# vim: set ts=4 sw=4 expandtab:

from comp_util import *
from x86ir import *
from p1spillgenerator import P1SpillGenerator
import logging

class P2SpillGenerator(P1SpillGenerator):
    
    def __init__(self, varalloc):
        P1SpillGenerator.__init__(self, varalloc)

    def visit_CallAddress(self, node, *args, **kwargs):
        return (False, [node])

    def visit_Ret(self, node, *args, **kwargs):
        return (False, [node])

    # very similar to visit_Program in p0spillgenerator
    # (content is the same, just changed from visit_Program to visit_x86Function)
    def visit_x86Function(self, node, *args, **kwargs):
        stmts = []
        spilled = False
        for x in node.statements:
            spill, stmt = self.visit(x)
            stmts.append(stmt)
            if spill: spilled = True
        return (spilled, Program(stmts))


if __name__ == "__main__":
    import sys, compiler
    from comp_util import *
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    for testcase in testcases:
        ast = compiler.parseFile(testcase)
        varalloc = VariableAllocator()
        explicate = P1Explicate(varalloc)
        ast = explicate.explicate(ast)
        flattener = P1Flattener(varalloc)
        stmtlist = flattener.flatten(ast)
        instruction_selector = P1InstructionSelector(varalloc)
        program = instruction_selector.visit(stmtlist)
        print prettyAST(program)
        regallocator = P1RegAllocator(program, varalloc)
        print prettyAST(regallocator.substitute())
