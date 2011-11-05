from compiler.ast import *
from comp_util import *
from x86ir import *
import logging

from p2uniquifyvars import P2UniquifyVars
from p2explicate import P2Explicate


class P3Explicate(P2Explicate):
    def __init__(self, varalloc, handleLambdas=True):
        P2Explicate.__init__(self, varalloc)
            


if __name__ == "__main__":
    import sys, compiler
    import logging.config
    from p0parser import P0Parser
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        #parser = P0Parser()
        #parser.build()
        ast = compiler.parseFile(testcase)
        #ast = parser.parseFile(testcase)
        p2unique = P2UniquifyVars()
        unique = p2unique.transform(ast)        
        p3explicator = P3Explicate(VariableAllocator())
        print prettyAST(p3explicator.transform(unique))
