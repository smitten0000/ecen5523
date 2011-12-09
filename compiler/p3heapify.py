# vim: set ts=4 sw=4 expandtab:
from compiler.ast import *
from comp_util import *
from x86ir import *
import logging

from p3freevars import P3FreeVars
from gcflattener import GCFlattener
from gcrefcount import GCRefCount
from p3wrapper import P3Wrapper
from p3explicate import P3Explicate
from p2heapify import P2Heapify

class P3Heapify(P2Heapify):
    def __init__(self, explicate):
        self.log = logging.getLogger('compiler.heapify')
        self.explicate = P3Explicate(explicate.varalloc,False)
        self.freevars = P3FreeVars()
        self.heapvarset = set([])

    def getLambdaFreeVars(self, n):
        if isinstance(n, (While)):
            test_fv = self.getLambdaFreeVars(n.test[1])
            body_fv = self.getLambdaFreeVars(n.body)
            return test_fv | body_fv
        elif isinstance(n, If):
            test_fv = self.getLambdaFreeVars(n.tests[0][0])
            then_fv = self.getLambdaFreeVars(n.tests[0][1])
            else_fv = self.getLambdaFreeVars(n.else_)
            # ignore n.else_ for now
            return test_fv | then_fv | else_fv
        else:
            return P2Heapify.getLambdaFreeVars(self,n)
            #return super(P3Heapify, self).getLambdaFreeVars(n)
    
    def visit_While(self, node):
        return While((self.visit(node.test[0]),self.visit(node.test[1])), self.visit(node.body), [], node.lineno)

    def visit_If(self, node):
        return If([(self.visit(node.tests[0][0]), self.visit(node.tests[0][1]))], self.visit(node.else_))

if __name__ == "__main__":
    import sys, compiler
    import logging.config
    from p3declassify import P3Declassify
    from p3uniquifyvars import P3UniquifyVars
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        varalloc = VariableAllocator()
        declassify = P3Declassify(varalloc)
        wrapper = P3Wrapper()
        unique = P3UniquifyVars()
        gcflatten = GCFlattener(varalloc)
        gcrefcount = GCRefCount(varalloc)
        explicator = P3Explicate(varalloc, handleLambdas=False)
        heap = P3Heapify(explicator)

        ast = compiler.parseFile(testcase)
        ast = declassify.transform(ast)
        ast = wrapper.transform(ast)
        ast = unique.transform(ast)        
        ast = gcflatten.transform(ast)        
        ast = gcrefcount.transform(ast)        
        ast = explicator.explicate(ast)
        ast = heap.transform(ast)
        print prettyAST(ast)
        print ast
