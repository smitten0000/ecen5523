from compiler.ast import *
from comp_util import *
from x86ir import *

from p2explicate import P2Explicate
from p2uniquifyvars import P2UniquifyVars
from p2freevars import P2FreeVars

import logging


class P2Heapify(object):
    def __init__(self):
        self.log = logging.getLogger('compiler.heapify')
        self.freevars = P2FreeVars()
        self.heap_vars = {}

    def getLambdaFreeVars(self):
        pass

    def transform(self, node):
        self.log.info('Starting heapify')
        # Do the freevars visitor on the whole tree. The ensures that
        # the free and bound attributes are set on all Lambdas.
        self.freevars.visit(node)
        ret = self.visit(node)
        self.log.info('Finished heapify')
        return ret
        
    def visit(self, node):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        # we cannot blindly return the node itself, if there is no visit 
        # function for that type.  This is because the children of that node may need
        # to be recursed upon: ex.  Printnl(CallFuncIndirect(...))
        if not meth:
            raise Exception('Unknown node: %s method: %s' % (node.__class__, meth_name))
        return meth(node)

    def visit_Module(self, node):
        # Need to find the free variables on all immediate child Lambdas
        # These are the variables that need heapification
        vars_to_heapify = self.visit(node.node,False)
        #return Module(None, self.visit(node.node))

    def visit_Stmt(self, node):
        return Stmt([self.visit(x) for x in node.nodes])

    def visit_Printnl(self, node):
        return Printnl([self.visit(node.nodes[0])], node.dest)

    def visit_Assign(self, node):
        return Assign(node.nodes, self.visit(node.expr))

    def visit_Discard(self, node):
        return Discard(self.visit(node.expr))

    def visit_Add(self, node):
        return Add((self.visit(node.left), self.visit(node.right)))

    def visit_UnarySub(self, node):
        return UnarySub(self.visit(node.expr))

    def visit_CallFunc(self, node):
        return CallFunc(self.visit(node.node), [self.visit(x) for x in node.args])

    def visit_Const(self, node):
        return node

    def visit_Name(self, node):
        return node

    def visit_Or(self, node):
        return Or([self.visit(x) for x in node.nodes])

    def visit_And(self, node):
        return And([self.visit(x) for x in node.nodes])

    def visit_IfExp(self, node):
        return IfExp(self.visit(node.test), self.visit(node.then), self.visit(node.else_))

    # List/Dict/Function no longer exist after explicate
    def visit_List(self, node):
        raise Exception('Encountered List AST in heapify.  List should no longer exist after explicate')

    def visit_Dict(self, node):
        raise Exception('Encountered Dict AST in heapify.  Dict should no longer exist after explicate')

    def visit_Function(self, node):
        raise Exception('Encountered Function AST in heapify.  Function should no longer exist after explicate')

    def visit_Compare(self, node):
        return Compare(self.visit(node.expr), [(node.ops[0][0], self.visit(node.ops[0][1]))])

    def visit_Not(self, node):
        return Not(self.visit(node.expr))

    def visit_Subscript(self, node):
        return Subscript(self.visit(node.expr), node.flags, [self.visit(node.subs[0])])

    def visit_Return(self, node):
        return Return(self.visit(node.value))

    def visit_InjectFrom(self, node):
        return InjectFrom(node.typ, self.visit(node.arg))

    def visit_ProjectTo(self, node):
        return ProjectTo(node.typ, self.visit(node.arg))

    def visit_GetTag(self, node):
        return GetTag(self.visit(node.arg))

    def visit_Let(self, node):
        return Let(node.var, self.visit(node.rhs), self.visit(node.body))

    def visit_Lambda(self, node):
        fvars = self.freevars.visit(node)
        self.log.debug(fvars)

    def visit_CallFuncIndirect(self, node):
        pass
    
if __name__ == "__main__":
    import sys, compiler
    import logging.config
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        p2unique = P2UniquifyVars()
        p2explicator = P2Explicate(VariableAllocator())
        p2heap = P2Heapify()

        ast = compiler.parseFile(testcase)
        unique = p2unique.transform(ast)        
        explicated = p2explicator.explicate(unique)
        ast = p2heap.transform(explicated)
        
        print prettyAST(ast)
