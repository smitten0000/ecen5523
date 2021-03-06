# vim: set ts=4 sw=4 expandtab:
from compiler.ast import *
from comp_util import *
from p3declassify import P3Declassify
from p3wrapper import P3Wrapper
from p3uniquifyvars import P3UniquifyVars
from gcflattener import GCFlattener
import operator

def getLocals(n):
    """
    Returns the set of variables that are assigned to within the current scope,
    ignoring assignments in nested scopes (functions).
    """
    if isinstance(n, Module):
        return getLocals(n.node)
    elif isinstance(n, Stmt):
        assigns = [getLocals(x) for x in n.nodes]
        return reduce(lambda x,y: x|y, assigns, set([]))
    elif isinstance(n, Printnl):
        return set([])
    elif isinstance(n, Assign):
        if isinstance(n.nodes[0], (Subscript,AssAttr)):
             ##assigning to a subscript of a variable does not constitute
             ##assigning to the variable itself.  Return empty set.
             ##ditto for an object attribute
            return set([])
        elif isinstance(n.nodes[0], AssName):
            return set([n.nodes[0].name])
        else:
            raise Exception('Unhandled Assign case: %s' % n.nodes[0])
    elif isinstance(n, Discard):
        # there shouldn't ever be a case where there will be an assignment in a Discard
        # since a Discard is, by definition, a statement that produced no assignments
        return set([])
    elif isinstance(n, Return):
        return set([])
    elif isinstance(n, Function):
        # a function definition is equivalent to an assignment to a 
        # variable with the same name as the function
        # No need to recurse into the Function since the intent of the function
        # is to only find assigments for the local scope
        return set([n.name])
    elif isinstance(n, If):
        testset = getLocals(n.tests[0][0])
        thenset = getLocals(n.tests[0][1])
        elseset = getLocals(n.else_)
        return testset | thenset | elseset
    elif isinstance(n, While):
        testset = getLocals(n.test[1])
        bodyset = getLocals(n.body)
        elseset = getLocals(n.else_) if n.else_ is not None and n.else_ != [] else set()
        return testset | bodyset | elseset
    elif isinstance(n, (Add,UnarySub,CallFunc,Const,Name,Or,And,IfExp,List,Dict,Compare,Not,Subscript,Lambda,CallFuncIndirect)):
        # these are all expressions, so no assignments
        return set([])
    elif isinstance(n, Class):
        return set([n.name])
    else:
        raise Exception('Unhandled expression: "%s"' % repr(n))


class GCRefCount:
    """Class to insert reference counting for garbage collection phase"""
    def __init__ (self, varalloc):
        self.varalloc = varalloc
        self.varset = set()
        self.log = logging.getLogger('compiler.gcrefcounter')
        self.lambda_local_vars = []
    
    def transform(self, node, *args, **kwargs):
        self.log.info('Starting gcrefcounter')
        ret = self.visit(node, *args, **kwargs)
        self.log.info('Finished gcrefcounter')
        return ret
    
    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        self.log.debug('%s' % meth_name)
        if not meth:
            raise Exception('Unknown node: %s method: %s' % (node.__class__, meth_name))
        return meth(node, *args, **kwargs)
    
    def visit_Module(self, node, *args, **kwargs):
        self.log.debug('localAssigns = %s' % getLocals(node))
        decrefstmts = []
        initialassigns = []
        for localvar in getLocals(node):
            initialassigns.append(Assign([AssName(localvar, 'OP_ASSIGN')],Const(0)))
        for localvar in getLocals(node):
            decrefstmts.append(Discard(CallFunc(Name('dec_ref_ctr'),[Name(localvar)])))
        stmt = self.visit(node.node)
        stmt.nodes = initialassigns + stmt.nodes + decrefstmts
        return Module(None, stmt, None)

    def visit_Stmt(self, node, *args, **kwargs):
        stmts = [self.visit(x) for x in node.nodes]
        return Stmt(reduce(lambda x,y:x+y, stmts, []), None)

    def visit_Assign(self, node, *args, **kwargs):
        assnode = node.nodes[0]
        if isinstance(assnode,Subscript):
            # NOTE: the increment of the reference count for assignment to a subscript is taken
            # care of in the runtime; see subscript_assign in runtime.c
            # so we can just return the assignment here, since this will get explicated to a call
            # to subscript_assign in a later phase.
            return [Assign([assnode], self.visit(node.expr))]
        elif isinstance(assnode, AssAttr):
            # NOTE: see set_attr in runtime.c ; the runtime has been modified to take care of 
            # incrementing the reference count.
            return [Assign([assnode], self.visit(node.expr))]
        elif isinstance(assnode, AssName):
            stmtlist = []
            self.log.info('varset=%s' % self.varset)
            self.varset.add(assnode.name)
            stmtlist.append(Discard(CallFunc(Name('dec_ref_ctr'),[Name(assnode.name)])))
            stmtlist.append(Assign([AssName(assnode.name,'OP_ASSIGN')], self.visit(node.expr)))
            stmtlist.append(Discard(CallFunc(Name('inc_ref_ctr'),[Name(assnode.name)])))
            return stmtlist
        else:
            raise Exception('Unknown assignment node: %s' % assnode)

    def visit_Printnl(self, node, *args, **kwargs):
        return [node]

    def visit_Discard(self, node, *args, **kwargs):
        raise Exception('There should be no Discard AST nodes.')
        return [node]

    def visit_Add(self, node, *args, **kwargs):
        return node

    def visit_UnarySub(self, node, *args, **kwargs):
        return node

    def visit_CallFunc(self, node, *args, **kwargs):
        return node

    def visit_Const(self, node, *args, **kwargs):
        return node

    def visit_Name(self, node, *args, **kwargs):
        return node

    def visit_AssName(self, node, *args, **kwargs):
        return node

    def visit_And(self, node, *args, **kwargs):
        return node

    def visit_Or(self, node, *args, **kwargs):
        return node

    def visit_IfExp(self, node, *args, **kwargs):
        raise Exception('IfExp should not exist at this point')
        return node

    def visit_List(self, node, *args, **kwargs):
        return node

    def visit_Dict(self, node, *args, **kwargs):
        return node
    
    def visit_Not(self, node, *args, **kwargs):
        return node

    def visit_Subscript(self, node, *args, **kwargs):
        return node
    
    def visit_Return(self, node, *args, **kwargs):
        localAssigns, argset = self.lambda_local_vars[-1]
        self.log.debug('visit_Return: localAssigns=%s' % localAssigns)
        self.log.debug('visit_Return: node=%s' % node)
        decrefstmts=[]
        # call dec_ref on all local variables, unless the this value is being returned.
        for localvar in localAssigns | argset:
            if not isinstance(node.value, Name) or node.value.name != localvar:
                decrefstmts.append(Discard(CallFunc(Name('dec_ref_ctr'),[Name(localvar)])))
        # Call set_autorelease on the variable being returned from the function
        if isinstance(node.value,Name):
            decrefstmts.append(Discard(CallFunc(Name('autorelease'),[node.value])))
        return decrefstmts + [node]

    def visit_CallFuncIndirect(self, node, *args, **kwargs):
        return node

    def visit_While(self, node, *args, **kwargs):
        body = self.visit(node.body)
        test = self.visit(node.test[1])
        return [While((node.test[0],test), body, [], node.lineno)]

    def visit_If(self, node, *args, **kwargs):
        # recurse on the "then" and "else" statements
        then = self.visit(node.tests[0][1])
        else_ = self.visit(node.else_)
        # NOTE: The If node has two attributes: "tests" and "else_".  The tests attribute is
        # a list of tuples, where the first element in the tuple is the test expression and the
        # second element in the tuple is a Stmt object.  Each tuple in the list corresponds to
        # an "if" or "elif" clause.  The else_ attribute is a Stmt object corresponding to the 
        # "else" clause.
        return [If([(node.tests[0][0], then)], else_)]

    def visit_Getattr(self, node, *args, **kwargs):
        return node

    def visit_InjectFrom(self, node, *args, **kwargs):
        return node

    def visit_Lambda(self, node, *args, **kwargs):
        # Lambda argnames, defaults, flags, code, lineno=None):
        # code is normally an expression, but it has been turned into a Stmt object in the 
        # GCFlattener; recurse on that stmt object here to add ref counting.
        if not isinstance(node.code, Stmt):
            raise Exception('Expected Stmt object for Lambda.code')
        increfstmts = []
        decrefstmts = []
        initialassigns = []
        localAssigns = getLocals(node.code)
        self.log.info('visit_Lambda: localAssigns=%s' % localAssigns)
        # Assign every local variable the value zero, except for arguments to the function
        # This eliminates the need to know where a variable is first assigned, which may
        # not be able to be determined statically.  
        for argvar in node.argnames:
            increfstmts.append(Discard(CallFunc(Name('inc_ref_ctr'),[Name(argvar)])))
        for localvar in localAssigns:
            if localvar not in node.argnames:
                initialassigns.append(Assign([AssName(localvar, 'OP_ASSIGN')],Const(0)))
        allvars = localAssigns | set(node.argnames)
        for localvar in allvars:
            decrefstmts.append(Discard(CallFunc(Name('dec_ref_ctr'),[Name(localvar)])))
        self.lambda_local_vars.append((localAssigns,set(node.argnames)))
        code = self.visit(node.code)
        self.lambda_local_vars.pop()
        code.nodes = increfstmts + initialassigns + code.nodes + decrefstmts
        for x in node.argnames:
            self.varalloc.add_var(x)
        return Lambda(node.argnames, node.defaults, node.flags, code, node.lineno)

    def visit_Compare(self, node, *args, **kwargs):
        return node


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
        wrapper = P3Wrapper()
        unique = P3UniquifyVars()
        flatten = GCFlattener(varalloc,True)
        refcount = GCRefCount(varalloc)

        ast = compiler.parseFile(testcase)
        ast = declassify.transform(ast)
        ast = wrapper.transform(ast)
        ast = unique.transform(ast)        
        ast = flatten.transform(ast)
        ast = refcount.transform(ast)
        print ast
        print prettyAST(ast)
