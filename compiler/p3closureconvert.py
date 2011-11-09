from compiler.ast import *
from comp_util import *
from x86ir import *

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

    def visit_If(self, node, *args, **kwargs):
        return If([(self.visit(node.test[0]),self.visit(node.test[1]))], self.visit(node.body), [], node.lineno)

    
if __name__ == "__main__":
    import sys, compiler
    import logging.config
    from p3declassify import P3Declassify
    from p3explicate import P3Explicate
    from p3uniquifyvars import P3UniquifyVars
    from p3heapify import P3Heapify
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        varalloc = VariableAllocator()
        declassify = P3Declassify(varalloc)
        unique = P3UniquifyVars()
        explicator = P3Explicate(varalloc)
        heap = P3Heapify(explicator)
        closure = P3ClosureConversion(explicator, varalloc)

        ast = compiler.parseFile(testcase)
        ast = declassify.transform(ast)
        ast = unique.transform(ast)        
        ast = explicator.explicate(ast)
        ast = heap.transform(ast)
        astlist = closure.transform(ast)
        for ast in astlist:
            print '\nFunction\n================='
            print prettyAST(ast)
