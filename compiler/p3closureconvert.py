from compiler.ast import *
from comp_util import *
from x86ir import *

from p3explicate import P3Explicate
from p3uniquifyvars import P3UniquifyVars
from p3heapify import P3Heapify
from p3freevars import P3FreeVars
from p2closureconvert import P2ClosureConversion

import logging
    
class P3ClosureConversion(P2ClosureConversion):
    def __init__(self, explicate, varalloc):
        self.log = logging.getLogger('compiler.closure')
        self.varalloc = varalloc
        self.name_alloc = {}
        self.functions = []
        self.freevars = P3FreeVars()
        self.explicate = explicate
        
    def visit_While(self, node, *args, **kwargs):
        return While(node.test, self.visit(node.body), [], node.lineno)

    
if __name__ == "__main__":
    import sys, compiler
    import logging.config
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        varalloc = VariableAllocator()
        p3unique = P3UniquifyVars()
        p3explicator = P3Explicate(varalloc)
        p3heap = P3Heapify(p3explicator)
        p3closure = P3ClosureConversion(p3explicator, varalloc)

        ast = compiler.parseFile(testcase)
        unique = p3unique.transform(ast)        
        explicated = p3explicator.explicate(unique)
        heaped = p3heap.transform(explicated)
        astlist = p3closure.transform(heaped)
        for ast in astlist:
            print '\nFunction\n================='
            print prettyAST(ast)
