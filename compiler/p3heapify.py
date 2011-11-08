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
        self.log = logging.getLogger('compiler.heapify')
        self.explicate = P3Explicate(explicate.varalloc,False)
        self.freevars = P3FreeVars()
        self.heapvarset = set([])

    def getLambdaFreeVars(self, n):
        if isinstance(n, (While)):
            return super(P3Heapify, self).getLambdaFreeVars(n.body)
        else:
            return super(P3Heapify, self).getLambdaFreeVars(n)
    
    def visit_While(self, node):
        return While(self.visit(node.test), self.visit(node.body), [], node.lineno)

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
