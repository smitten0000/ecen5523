from compiler.ast import *
from comp_util import *
from x86ir import *

from p3explicate import P3Explicate
from p3uniquifyvars import P3UniquifyVars

import logging

from p2freevars import P2FreeVars

class P3FreeVars(P2FreeVars):
    '''Returns for each visited node return a set of variables not bound in that node'''
    def __init__(self):
        P2FreeVars.__init__()

    
if __name__ == "__main__":
    # create logger
    log = logging.getLogger('freevars')
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
        p3unique = P3UniquifyVars()
        p3explicator = P3Explicate(VariableAllocator())
        p3free = P3FreeVars()

        ast = compiler.parseFile(testcase)
        unique = p3unique.visit(ast)        
        explicated = p3explicator.explicate(unique)
        print prettyAST(explicated)
        ast = p3free.visit(explicated)
        
        print ast            
