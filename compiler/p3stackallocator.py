# vim: set ts=4 sw=4 expandtab:

from p2stackallocator import *
from x86ir import *

class P3StackAllocator(P2StackAllocator):
    def __init__(self, program):
        P2StackAllocator.__init__(self, program)

    def visit_x86While(self, node, *args, **kwargs):
        test = [self.visit(x) for x in node.test[1]]
        test = [x for x in test if x is not None]
        body = [self.visit(x) for x in node.body]
        body = [x for x in body if x is not None]
        return x86While((self.visit(node.test[0]),test), body, [], node.lineno)


if __name__ == "__main__":
    import sys, compiler
    import logging, logging.config
    from comp_util import *
    from p3declassify import P3Declassify
    from p3uniquifyvars import P3UniquifyVars
    from p3explicate import P3Explicate
    from p3heapify import P3Heapify
    from p3closureconvert import P3ClosureConversion
    from p3flattener import P3Flattener
    from p3insselector import P3InstructionSelector
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
        flatten = P3Flattener(varalloc)
        insselector = P3InstructionSelector(varalloc)

        ast = compiler.parseFile(testcase)
        ast = declassify.transform(ast)
        unique = unique.transform(ast)        
        explicated = explicator.explicate(unique)
        heaped = heap.transform(explicated)
        astlist = closure.transform(heaped)
        for ast in astlist:
            ast = flatten.flatten(ast)
            program = insselector.transform(ast)
            allocator = P3StackAllocator(program)
            program = allocator.substitute()
            print '\nFunction\n================='
            print prettyAST(program)
