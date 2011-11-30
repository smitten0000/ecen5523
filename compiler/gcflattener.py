# vim: set ts=4 sw=4 expandtab:
from compiler.ast import *
from comp_util import *
from p3declassify import P3Declassify
from p3explicate import P3Explicate
from p3uniquifyvars import P3UniquifyVars
from p3closureconvert import P3ClosureConversion
import operator

class GCFlattener:
    """Class to performing flattening of complex expressions for the garbage collection phase (pre-explicate)"""
    def __init__ (self, varalloc, validate=False):
        self.validate = validate
        self.varalloc = varalloc
        self.log = logging.getLogger('compiler.gcflatten')        
    
    def transform(self, node, *args, **kwargs):
        self.log.info('Starting gcflattener')
        ret = self.visit(node, *args, **kwargs)
        self.log.info('Finished gcflattener')
        return ret
    
    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        if not meth:
            raise Exception('Unknown node: %s method: %s' % (node.__class__, meth_name))
        return meth(node, *args, **kwargs)
    
    def visit_Module(self, node, *args, **kwargs):
        return Module(None, self.visit(node.node), None)
    def visit_Stmt(self, node, *args, **kwargs):
        flat = [self.visit(x) for x in node.nodes]
        return Stmt(reduce(lambda x,y:x+y, flat, []), None)
    def visit_Printnl(self, node, *args, **kwargs):
        if len(node.nodes) > 0:
            var, stmtlist = self.visit(node.nodes[0])
            return stmtlist + [Printnl([var], node.dest)]
    def visit_Assign(self, node, *args, **kwargs):
        if isinstance(node.nodes[0],Subscript):
            self.varalloc.add_var(node.nodes[0].expr.name)
        else:
            self.varalloc.add_var(node.nodes[0].name)
        var, stmtlist = self.visit(node.expr)
        return stmtlist + [Assign(node.nodes, var)]
    def visit_Discard(self, node, *args, **kwargs):
        var, stmtlist = self.visit(node.expr)
        varname = self.varalloc.get_next_var()
        return stmtlist + [Assign([AssName(varname, 'OP_ASSIGN')], var)]
    def visit_Add(self, node, *args, **kwargs):
        left, stmtleft = self.visit(node.left)
        right, stmtright = self.visit(node.right)
        varname = self.varalloc.get_next_var()
        return (Name(varname), stmtleft + stmtright + [Assign([AssName(varname, 'OP_ASSIGN')], Add((left,right)))] )
    def visit_UnarySub(self, node, *args, **kwargs):
        f, stmtlist = self.visit(node.expr)
        varname = self.varalloc.get_next_var()
        return (Name(varname), stmtlist + [Assign([AssName(varname, 'OP_ASSIGN')], UnarySub(f))])
    def visit_CallFunc(self, node, *args, **kwargs):
        # arguments can be arbitrary expressions, so we need to flatten those too.
        # this is a list of tuples: [(var1,stmtlist1), (var2,stmtlist2), ...]
        varstmtlist = [self.visit(x) for x in node.args]
        #print varstmtlist
        # generate a temporary to store the result
        varname = self.varalloc.get_next_var()
        # convert the list of tuples to just a list of the variables; ditto for statements
        varlist =  [x[0] for x in varstmtlist]
        #print varlist
        stmtlist = reduce(lambda x,y: x+y, [x[1] for x in varstmtlist], [])
        #print stmtlist
        # return a CallFunc with the variables substituted in
        return (Name(varname), stmtlist + [Assign([AssName(varname, 'OP_ASSIGN')], CallFunc(node.node, varlist))])
    def visit_Const(self, node, *args, **kwargs):
        return (node, [])
    def visit_Name(self, node, *args, **kwargs):
        return (node, [])
    def visit_AssName(self, node, *args, **kwargs):
        self.varalloc.add_var(node.assname)
        return (node, [])
    def visit_And(self, node, *args, **kwargs):
        # we only need to handle two operands to the "or" operator
        if self.validate and len(node.nodes) > 2:
            raise Exception("Only two operands supported in P1 for 'or' operator")
        lhsvar, lhsstmtlist = self.visit(node.nodes[0])
        rhsvar, rhsstmtlist = self.visit(node.nodes[1])
        varname = self.varalloc.get_next_var()
        result = And([lhsvar,rhsvar])
        return (Name(varname), lhsstmtlist + rhsstmtlist + [Assign([AssName(varname, 'OP_ASSIGN')], result)])
    def visit_Or(self, node, *args, **kwargs):
        # we only need to handle two operands to the "or" operator
        if self.validate and len(node.nodes) > 2:
            raise Exception("Only two operands supported in P1 for 'or' operator")
        lhsvar, lhsstmtlist = self.visit(node.nodes[0])
        rhsvar, rhsstmtlist = self.visit(node.nodes[1])
        varname = self.varalloc.get_next_var()
        result = Or([lhsvar,rhsvar])
        return (Name(varname), lhsstmtlist + rhsstmtlist + [Assign([AssName(varname, 'OP_ASSIGN')], result)])
    def visit_IfExp(self, node, *args, **kwargs):
        # Go ahead and flatten all expressions, including the test expression, as well as the 
        # "then" and "else" expressions.
        vartes, test = self.visit(node.test)
        vart, then = self.visit(node.then)
        vare, else_ = self.visit(node.else_)
        
        # Allocate a variable name, which will hold the result of the IfExp
        varname = self.varalloc.get_next_var()
        #test = [Assign([AssName(vartes, 'OP_ASSIGN')], varname)]+test1
        # update the "then" and "else_" set of statements to include an 
        # assignment to the allocated variable
        then  = then  + [Assign([AssName(varname, 'OP_ASSIGN')], vart)]
        else_ = else_ + [Assign([AssName(varname, 'OP_ASSIGN')], vare)]
        # We don't want to blindly execute both branches of the if, so instead we
        # encapsulate the flattened statements for the "then" and "else_" clauses in an If node.
        # The If node is then returned as a statement.  This is expanded later into labels and
        # jumps.  The test expression is always evaluated, so we have to include the corresponding
        # flattened statements.
        # NOTE: The If node has two attributes: "tests" and "else_".  The tests attribute is
        # a list of tuples, where the first element in the tuple is the test expression and the
        # second element in the tuple is a Stmt object.  Each tuple in the list corresponds to
        # an "if" or "elif" clause.  The else_ attribute is a Stmt object corresponding to the 
        # "else" clause.
        return (Name(varname), test + [If([(vartes, Stmt(then))], Stmt(else_))])
    def visit_List(self, node, *args, **kwargs):
        stmts = [self.visit(x) for x in node.nodes]
        varlist = [x for x,y in stmts]
        # convert the list of lists into a single list of statements
        stmtlist = reduce(lambda x,y: x+y, [y for x,y in stmts if y != []], [])
        varname = self.varalloc.get_next_var()
        return (Name(varname), stmtlist + [Assign([AssName(varname, 'OP_ASSIGN')], List(varlist))])
    def visit_Dict(self, node, *args, **kwargs):
        keys = [self.visit(x[0]) for x in node.items]
        keyvarlist = [x for x,y in keys]
        keystmtlist = reduce(lambda x,y: x+y, [y for x,y in keys if y != []], [])
        values = [self.visit(x[1]) for x in node.items]
        valuevarlist = [x for x,y in values]
        valuestmtlist = reduce(lambda x,y: x+y, [y for x,y in values if y != []], [])
        # keyvaluelist becomes a list of tuples, where each tuple is a key,value corresponding to the 
        # temp variables for the key/value
        keyvaluelist = map(lambda x: (keyvarlist[x],valuevarlist[x]), range(0,len(keyvarlist)))
        varname = self.varalloc.get_next_var()
        return (Name(varname), keystmtlist + valuestmtlist + [Assign([AssName(varname, 'OP_ASSIGN')], Dict(keyvaluelist))])
    
    def visit_Not(self, node, *args, **kwargs):
        var, stmtlist = self.visit(node.expr)
        tempvar = self.varalloc.get_next_var()            
        return (Name(tempvar), stmtlist + [Assign([AssName(tempvar,'OP_ASSIGN')], Not(var))])
    def visit_Subscript(self, node, *args, **kwargs):
        # We only need to handle one subscript per the grammar, e.g, a[1,2] is invalid P1
            # (a[1,2] is the only case where you get len(node.subs) > 1)
        if self.validate and len(node.subs) > 1:
            raise Exception('Only one subscript index supported in P1')
        exprvar, exprstmtlist = self.visit(node.expr)
        subvar, substmtlist = self.visit(node.subs[0])
        varname = self.varalloc.get_next_var()
        return (Name(varname), exprstmtlist + substmtlist + [Assign([AssName(varname,'OP_ASSIGN')], Subscript(exprvar, node.flags, subvar))])
    
    def visit_Return(self, node, *args, **kwargs):
        x = self.visit(node.value)
        retvar, retstmtlist = self.visit(node.value)
        return retstmtlist + [Return(retvar)]
    def visit_CallFuncIndirect(self, node, *args, **kwargs):
        self.log.debug('CallFuncIndirect: args: %s', node.args)
        nodevar, nodestmtlist = self.visit(node.node)
        tuplelist = [self.visit(x) for x in node.args]
        varargs = [x[0] for x in tuplelist]
        varstmts = [x[1] for x in tuplelist]
        varname = self.varalloc.get_next_var()
        stmts = nodestmtlist + reduce(lambda x,y: x+y, varstmts, []) + [Assign([AssName(varname, 'OP_ASSIGN')], CallFuncIndirect(nodevar, varargs))]
        return (Name(varname), stmts)
    def visit_Function(self, node, *args, **kwargs):
        # This is not a Function returned from the parse stage, but a top-level function
        # that is created in the closure-conversion pass.
        # We just need to flatten the "code" attribute, which is a Stmt.
        # Function(decorators, name, argnames, defaults, flags, doc, code, lineno=None)
        self.log.debug('in visit_Function, node.code = %s',node.code)
        code = self.visit(node.code)
        for x in node.argnames:
            self.varalloc.add_var(x)
        return Function(node.decorators, node.name, node.argnames, node.defaults, node.flags, node.doc, code, node.lineno)
    def visit_While(self, node, *args, **kwargs):
        #statement
        flatbody = self.visit(node.body)
        #expression
        var, flattest = self.visit(node.test) 
        return [While((var,Stmt(flattest)), flatbody, [], node.lineno)] 
    def visit_If(self, node, *args, **kwargs):
        # flatten the "test" expression
        vartes, test = self.flatten(node.tests[0][0])
        # flatten the "then" and "else" statements
        then = self.visit(node.tests[0][1])
        else_ = self.visit(node.else_)
        
        # NOTE: The If node has two attributes: "tests" and "else_".  The tests attribute is
        # a list of tuples, where the first element in the tuple is the test expression and the
        # second element in the tuple is a Stmt object.  Each tuple in the list corresponds to
        # an "if" or "elif" clause.  The else_ attribute is a Stmt object corresponding to the 
        # "else" clause.
        self.log.debug('then=%s' % then)
        self.log.debug('else_=%s' % then)
        return test + [If([(vartes, then)], else_)]
    def visit_GetAttr(self, node, *args, **kwargs):
        return node
    def visit_AssAttr(self, node, *args, **kwargs):
        return node
    def visit_Lambda(self, node, *args, **kwargs):
        # Lambda argnames, defaults, flags, code, lineno=None):
        self.log.debug('in visit_Lambda, node.code = %s',node.code)
        code = self.visit(node.code)
        for x in node.argnames:
            self.varalloc.add_var(x)
        return Lambda(node.argnames, node.defaults, node.flags, code, node.lineno)
    def visit_Compare(self, node, *args, **kwargs):
        # Only need to handle binary comparison operators.  So if len(node.ops) > 1, its a syntax error.
        # For example, a == b == c is valid python, but invalid P1
        if self.validate and len(node.ops) > 1:
            raise Exception('Only two operands supported in P1 for comparison operators')
        if self.validate and node.ops[0][0] not in ['==','!=','is']:
            raise Exception("'%s' is not a valid comparison operator in P1" % node.ops[0][0])
        lhsvar, lhsstmtlist = self.visit(node.expr)
        oper, rhs = node.ops[0]
        rhsvar, rhsstmtlist = self.visit(rhs)
        varname = self.varalloc.get_next_var()
        return (Name(varname), lhsstmtlist + rhsstmtlist + [Assign([AssName(varname,'OP_ASSIGN')], Compare(lhsvar, [(oper, rhsvar)]))])


if __name__ == "__main__":
    import compiler, sys
    import logging.config
    
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')

    testcases = sys.argv[1:]
    for testcase in testcases:
        varalloc = VariableAllocator()
        declassify = P3Declassify(varalloc)
        unique = P3UniquifyVars()
        explicator = P3Explicate(varalloc)
        flatten = GCFlattener(varalloc,True)

        ast = compiler.parseFile(testcase)
        ast = declassify.transform(ast)
        ast = unique.transform(ast)        
        ast = flatten.transform(ast)
        print ast

