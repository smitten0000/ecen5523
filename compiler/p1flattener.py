# vim: set ts=4 sw=4 expandtab:
from compiler.ast import *
from comp_util import *
from p0flattener import P0Flattener
from p1explicate import *
import operator

class P1Flattener(P0Flattener):
    """Class to performing flattening of complex expressions."""
    def __init__ (self, varalloc, validate=False):
        P0Flattener.__init__(self, varalloc)
        self.validate = validate
    
    def flatten (self, node):
        """Takes an AST as input, and then "flattens" the tree into a list of statements."""

        if isinstance(node, (Or,And)):
            # we only need to handle two operands to the "or" operator
            if self.validate and len(node.nodes) > 2:
                raise Exception("Only two operands supported in P1 for 'or' operator")
            lhsvar, lhsstmtlist = self.flatten(node.nodes[0])
            rhsvar, rhsstmtlist = self.flatten(node.nodes[1])
            varname = self.varalloc.get_next_var()
            result = Or([lhsvar,rhsvar]) if isinstance(node,Or) else And([lhsvar,rhsvar])
            return (Name(varname), lhsstmtlist + rhsstmtlist + [Assign([AssName(varname, 'OP_ASSIGN')], result)])
        elif isinstance(node, Let):
            # first, flatten rhs
            (rhsvar, rhsstmtlist) = self.flatten(node.rhs)
            # now make sure that the variable specified by Let is assigned the result
            letassignstmt = [Assign([AssName(node.var.name, 'OP_ASSIGN')], rhsvar)]
            # now flatten the body and return
            # NOTE: there should not be ANY Let nodes after a flatten
            (bodyvar, bodystmtlist) = self.flatten(node.body)
            return (bodyvar, rhsstmtlist + letassignstmt + bodystmtlist)
        elif isinstance(node, (ProjectTo,InjectFrom)):
            (var, stmtlist) = self.flatten(node.arg)
            varname = self.varalloc.get_next_var()
            result = ProjectTo(node.typ, var) if isinstance(node,ProjectTo) else InjectFrom(node.typ, var)
            return (Name(varname), stmtlist + [Assign([AssName(varname,'OP_ASSIGN')], result)])
        elif isinstance(node, GetTag):
            (var, stmtlist) = self.flatten(node.arg)
            varname = self.varalloc.get_next_var()
            return (Name(varname), stmtlist + [Assign([AssName(varname,'OP_ASSIGN')], GetTag(var))])
        elif isinstance(node, List):
            stmts = [self.flatten(x) for x in node.nodes]
            varlist = [x for x,y in stmts]
            # convert the list of lists into a single list of statements
            stmtlist = reduce(lambda x,y: x+y, [y for x,y in stmts if y != []], [])
            varname = self.varalloc.get_next_var()
            return (Name(varname), stmtlist + [Assign([AssName(varname, 'OP_ASSIGN')], List(varlist))])
        elif isinstance(node, Dict):
            keys = [self.flatten(x[0]) for x in node.items]
            keyvarlist = [x for x,y in keys]
            keystmtlist = reduce(lambda x,y: x+y, [y for x,y in keys if y != []], [])
            values = [self.flatten(x[1]) for x in node.items]
            valuevarlist = [x for x,y in values]
            valuestmtlist = reduce(lambda x,y: x+y, [y for x,y in values if y != []], [])
            # keyvaluelist becomes a list of tuples, where each tuple is a key,value corresponding to the 
            # temp variables for the key/value
            keyvaluelist = map(lambda x: (keyvarlist[x],valuevarlist[x]), range(0,len(keyvarlist)))
            varname = self.varalloc.get_next_var()
            return (Name(varname), keystmtlist + valuestmtlist + [Assign([AssName(varname, 'OP_ASSIGN')], Dict(keyvaluelist))])
        # not sure why we are handling tuple? Ah, this was probably because Dict.items is a tuple.
        # I think its cleaner to separate into keys/values as done above.
        #elif isinstance(node, tuple):
        #    return (node,[])
        elif isinstance(node, IfExp):
            # Go ahead and flatten all expressions, including the test expression, as well as the 
            # "then" and "else" expressions.
            vartes, test = self.flatten(node.test)
            vart, then = self.flatten(node.then)
            vare, else_ = self.flatten(node.else_)
            
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
            return (Name(varname), test + [If([(vartes, Stmt([then]))], Stmt([else_]))])
        elif isinstance(node, Not):
            var, stmtlist = self.flatten(node.expr)
            return (var, stmtlist + [Not(var)])
        elif isinstance(node, Compare):
            # Only need to handle binary comparison operators.  So if len(node.ops) > 1, its a syntax error.
            # For example, a == b == c is valid python, but invalid P1
            if self.validate and len(node.ops) > 1:
                raise Exception('Only two operands supported in P1 for comparison operators')
            if self.validate and node.ops[0][0] not in ['==','!=','is']:
                raise Exception("'%s' is not a valid comparison operator in P1" % node.ops[0][0])
            lhsvar, lhsstmtlist = self.flatten(node.expr)
            oper, rhs = node.ops[0]
            rhsvar, rhsstmtlist = self.flatten(rhs)
            varname = self.varalloc.get_next_var()
            return (Name(varname), lhsstmtlist + rhsstmtlist + [Assign([AssName(varname,'OP_ASSIGN')], Compare(lhsvar, [(oper, rhsvar)]))])
        elif isinstance(node, Subscript):
            # We only need to handle one subscript per the grammar, e.g, a[1,2] is invalid P1
            # (a[1,2] is the only case where you get len(node.subs) > 1)
            if self.validate and len(node.subs) > 1:
                raise Exception('Only one subscript index supported in P1')
            exprvar, exprstmtlist = self.flatten(node.expr)
            subvar, substmtlist = self.flatten(node.subs[0])
            varname = self.varalloc.get_next_var()
            return (Name(varname), exprstmtlist + substmtlist + [Assign([AssName(varname,'OP_ASSIGN')], Subscript(exprvar, node.flags, subvar))])
        else:
            return P0Flattener.flatten(self, node)


if __name__ == "__main__":
    import compiler, sys
    from p0parser import P0Parser
    from p1explicate import P1Explicate
    if len(sys.argv) < 2:
        sys.exit(1)

    testcases = sys.argv[1:]
    for testcase in testcases:
        #parser = P0Parser()
        #parser.build()
        #ast = parser.parseFile(testcase)
        ast = compiler.parseFile(testcase)
        varalloc = VariableAllocator()
        p1explicator = P1Explicate(varalloc)
        ast = p1explicator.explicate(ast)
        p1flattener = P1Flattener(varalloc,True)
        stmtlist = p1flattener.flatten(ast)
        #print stmtlist
        print prettyAST(stmtlist)
        print '\n'.join([pretty(x) for x in stmtlist.node.nodes])
