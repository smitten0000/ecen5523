# vim: set ts=4 sw=4 expandtab:
from compiler.ast import *
from comp_util import *
from p3declassify import P3Declassify
from p3wrapper import P3Wrapper
from p3uniquifyvars import P3UniquifyVars
from gcflattener import GCFlattener
import operator

class GCRefCount:
    """Class to insert reference counting for garbage collection phase"""
    def __init__ (self, varalloc):
        self.varalloc = varalloc
        self.varset = set()
        self.log = logging.getLogger('compiler.gcrefcounter')
    
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
        self.log.debug('localAssigns = %s' % getLocalAssigns(node))
        decrefstmts = []
        for localvar in getLocalAssigns(node):
            decrefstmts.append(Discard(CallFunc(Name('dec_ref_ctr'),[Name(localvar)])))
        stmt = self.visit(node.node)
        stmt.nodes = stmt.nodes + decrefstmts
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
            return [node]
        elif isinstance(assnode, AssAttr):
            # NOTE: see set_attr in runtime.c ; the runtime has been modified to take care of 
            # incrementing the reference count.
            return [node]
        elif isinstance(assnode, AssName):
            stmtlist = []
            if assnode.name in self.varset:
                stmtlist.append(Discard(CallFunc(Name('dec_ref_ctr'),[Name(assnode.name)])))
            self.varset.add(assnode.name)
            stmtlist.append(node)
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
        return [node]

    def visit_CallFuncIndirect(self, node, *args, **kwargs):
        return node

    def visit_Function(self, node, *args, **kwargs):
        # This should be a Stmt AST node; recurse on it to handle assignments within function
        code = self.visit(node.code)
        #for x in node.argnames:
        #    self.varalloc.add_var(x)
        return [Function(node.decorators, node.name, node.argnames, node.defaults, node.flags, node.doc, code, node.lineno)]

    def visit_While(self, node, *args, **kwargs):
        return [node]

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
        code = self.visit(node.code)
        #for x in node.argnames:
        #    self.varalloc.add_var(x)
        return [Lambda(node.argnames, node.defaults, node.flags, code, node.lineno)]

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
