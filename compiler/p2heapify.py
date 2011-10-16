from compiler.ast import *
from comp_util import *
from x86ir import *

from p2explicate import P2Explicate
from p2uniquifyvars import P2UniquifyVars

import logging

class P2Heapify(object):
    def __init__(self, varalloc):
        P1Explicate.__init__(self, varalloc)
        self.log = logging.getLogger('heapify')

    def visit(self, node, *args, **kwargs):
        meth = None
        
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        # we return the node passed in by default so we do not have to handle
        # every case unless necessary
        if not meth:
            return node
        return meth(node, *args, **kwargs)
    
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    debug = True
    for testcase in testcases:
        p2unique = P2UniquifyVars(ast)
        p2explicator = P2Explicate(VariableAllocator())
        p2heap = P2Heapify()

        ast = compiler.parseFile(testcase)
        unique = p2unique.visit(ast)        
        explicated = p1explicator.explicate(unique)
        ast = p2heap.visit(explicated)
        
        print prettyAST(ast)
