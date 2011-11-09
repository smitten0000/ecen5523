# vim: set ts=4 sw=4 expandtab:

from p1stackallocator import *
from x86ir import *

class P2StackAllocator(P1StackAllocator):
    def __init__(self, program):
        P1StackAllocator.__init__(self, program)

    def visit_CallAddress(self, node, *args, **kwargs):
        return CallAddress(self.visit(node.address))

    def visit_Ret(self, node, *args, **kwargs):
        return Ret(self.visit(node.value))

    def visit_x86Function(self, node, *args, **kwargs):
        return x86Function(node.name, node.argnames, [self.visit(x) for x in node.statements], node.lineno)

    def visit_StackSlot(self, node, *args, **kwargs):
        return node


if __name__ == "__main__":
    import sys, compiler
    import logging, logging.config
    from comp_util import *
    from p2uniquifyvars import P2UniquifyVars
    from p2explicate import P2Explicate
    from p2heapify import P2Heapify
    from p2closureconvert import P2ClosureConversion
    from p2flattener import P2Flattener
    from p2insselector import P2InstructionSelector
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        varalloc = VariableAllocator()
        unique = P2UniquifyVars()
        explicator = P2Explicate(varalloc)
        heap = P2Heapify(explicator)
        closure = P2ClosureConversion(explicator, varalloc)
        flatten = P2Flattener(varalloc)
        insselector = P2InstructionSelector(varalloc)

        ast = compiler.parseFile(testcase)
        unique = unique.transform(ast)        
        explicated = explicator.explicate(unique)
        heaped = heap.transform(explicated)
        astlist = closure.transform(heaped)
        for ast in astlist:
            ast = flatten.flatten(ast)
            program = insselector.transform(ast)
            allocator = P2StackAllocator(program)
            program = allocator.substitute()
            print '\nFunction\n================='
            print prettyAST(program)
