from compiler.ast import *
from comp_util import *
from x86ir import *

from p3explicate import P3Explicate
from p3uniquifyvars import P3UniquifyVars
from p3freevars import P3FreeVars

import logging

from p2heapify import P2Heapify

class P3Heapify(P2Heapify):
    def __init__(self, explicate):
        P2Heapify.__init__(self, explicate)

        
if __name__ == "__main__":
    import sys, compiler
    import logging.config
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        p3unique = P3UniquifyVars()
        p3explicator = P3Explicate(VariableAllocator())
        p3heap = P3Heapify(p3explicator)

        ast = compiler.parseFile(testcase)
        unique = p3unique.transform(ast)        
        explicated = p3explicator.explicate(unique)
        ast = p3heap.transform(explicated)
        
        print prettyAST(ast)
        #print ast
