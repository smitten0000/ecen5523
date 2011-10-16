from compiler.ast import *
from comp_util import *
from x86ir import *

from p2explicate import P2Explicate
from p2uniquifyvars import P2UniquifyVars
from p2heapify import P2Heapify

import logging

class P2ClosureConversion(object):
    def __init__(self, varalloc):
        P1Explicate.__init__(self, varalloc)
        self.log = logging.getLogger('closure')

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
    import sys, compiler
    from p0parser import P0Parser
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    debug = True
    for testcase in testcases:
        p2unique = P2UniquifyVars(ast)
        p2explicator = P2Explicate(VariableAllocator())
        p2heap = P2Heapify()
        p2closure = P2ClosureConversion()

        ast = compiler.parseFile(testcase)
        unique = p2unique.visit(ast)        
        explicated = p1explicator.explicate(unique)
        heaped = p2heap.visit(explicated)
        ast = p2closure.visit(heaped)
        
        print prettyAST(ast)
