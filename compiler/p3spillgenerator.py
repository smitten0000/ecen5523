# vim: set ts=4 sw=4 expandtab:

from comp_util import *
from x86ir import *
from p2spillgenerator import P2SpillGenerator
import logging

class P3SpillGenerator(P2SpillGenerator):
    
    def __init__(self, varalloc):
        P2SpillGenerator.__init__(self, varalloc)

    # very similar to visit_Program in p0spillgenerator
    # (content is the same, just changed from visit_Program to visit_x86Function)
    def visit_x86While(self, node, *args, **kwargs):
        test = node.test[1]
        spilled = False
        test_instr_list = []
        for x in node.test[1]:
            spill, instrlist = self.visit(x)
            test_instr_list.extend(instrlist)
            if spill: spilled = True
        body_instr_list = []
        for x in node.body:
            spill, instrlist = self.visit(x)
            body_instr_list.extend(instrlist)
            if spill: spilled = True
        return (spilled, [x86While((node.test[0], test_instr_list), node.body, [], node.lineno)])


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
