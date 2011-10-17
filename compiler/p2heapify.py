from compiler.ast import *
from comp_util import *
from x86ir import *

from p2explicate import P2Explicate
from p2uniquifyvars import P2UniquifyVars
from p2freevars import P2FreeVars

import logging

class P2Heapify(object):
    def __init__(self):
        self.log = logging.getLogger('heapify')
        self.freevars = P2FreeVars()
        self.heap_vars = {}
        
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
        return self.visit(node.node)
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
    # create logger
    log = logging.getLogger('heapify')
    log.setLevel(logging.DEBUG)    
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)    
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')    
    # add formatter to ch
    ch.setFormatter(formatter)    
    # add ch to logger
    log.addHandler(ch)

    import sys, compiler
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    debug = True
    for testcase in testcases:
        p2unique = P2UniquifyVars()
        p2explicator = P2Explicate(VariableAllocator())
        p2heap = P2Heapify()

        ast = compiler.parseFile(testcase)
        unique = p2unique.visit(ast)        
        explicated = p2explicator.explicate(unique)
        ast = p2heap.visit(explicated)
        
        print prettyAST(ast)
