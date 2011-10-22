# vim: set ts=4 sw=4 expandtab:

from comp_util import *
from x86ir import *
# to flatten nested lists into a flat list
from compiler.ast import flatten
from p1ifinsselector import P1IfInstructionSelector

# Concept borrowed from http://peter-hoffmann.com/2010/extrinsic-visitor-pattern-python-inheritance.html
class P2IfInstructionSelector(P1IfInstructionSelector):
    def __init__(self, varalloc, labelalloc):
        P1IfInstructionSelector.__init__(self, varalloc, labelalloc)

    # same as visit_Statement in P1IfInstructionSelector
    def visit_x86Function(self, node, *args, **kwargs):
        return x86Function(node.name, node.argnames, [self.visit(x) for x in node.statements], node.lineno)

if __name__ == "__main__":
    import sys, compiler
    from p2uniquifyvars import P2UniquifyVars
    from p2explicate import P2Explicate
    from p2heapify import P2Heapify
    from p2closureconvert import P2ClosureConversion
    from p2flattener import P2Flattener
    from p2insselector import P2InstructionSelector
    from p2regallocator import P2RegAllocator
    from p2ifinsselector import P2IfInstructionSelector
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    for testcase in testcases:
        varalloc = VariableAllocator()
        p2unique = P2UniquifyVars()
        p2explicator = P2Explicate(varalloc)
        p2heap = P2Heapify(p2explicator)
        p2closure = P2ClosureConversion(p2explicator, varalloc)
        p2flatten = P2Flattener(varalloc)
        p2insselector = P2InstructionSelector(varalloc)
        ifinsselector = P2IfInstructionSelector(varalloc,p2insselector.labelalloc)

        ast = compiler.parseFile(testcase)
        unique = p2unique.transform(ast)        
        explicated = p2explicator.explicate(unique)
        heaped = p2heap.transform(explicated)
        astlist = p2closure.transform(heaped)
        for ast in astlist:
            ast = p2flatten.flatten(ast)
            program = p2insselector.transform(ast)
            p2regallocator = P2RegAllocator(program, varalloc)
            program = p2regallocator.substitute()
            program = ifinsselector.visit(program)
            print '\nFunction\n================='
            print prettyAST(program)
