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

    def transform(self, node, *args, **kwargs):
        self.log.info('Starting heapify')
        ret = self.visit(node, *args, **kwargs)
        self.log.info('Finished heapify')
        return ret
        
    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        # we return the node passed in by default so we do not have to handle
        # every case unless necessary
        if not meth:
            return node
        return meth(node, *args, **kwargs)

    def visit_Module(self,node, *args, **kwargs):
        return Module(None, self.visit(node.node))

    def visit_Stmt(self,node, *args, **kwargs):
        visited = [self.visit(x) for x in node.nodes]
        self.log.debug('Visited and produced %s'%visited)
        return Stmt(visited)

    def visit_Assign(self, node, *args, **kwargs):
        self.log.debug('Visiting rhs of assign %s'%node.expr)
        return Assign(node.nodes, self.visit(node.expr))

    def visit_Lambda(self, node, *args, **kwargs):
        fvars = self.freevars.visit(node)
        self.log.debug(fvars)
    
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
