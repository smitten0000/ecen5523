# vim: set ts=4 sw=4 expandtab:
import compiler
from comp_util import *
from x86ir import *
from p0insselector import P0InstructionSelector

# Concept borrowed from http://peter-hoffmann.com/2010/extrinsic-visitor-pattern-python-inheritance.html
class P1InstructionSelector(P0InstructionSelector):
    def __init__(self, varalloc):
        P0InstructionSelector.__init__(self, varalloc)


if __name__ == "__main__":
    import sys
    from p0parser import P0Parser
    from p1flattener import P1Flattener
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    for testcase in testcases:
        #parser = P0Parser()
        #parser.build()
        #ast = parser.parseFile(testcase)
        ast = compile.parseFile(testcase)
        
        varalloc = VariableAllocator()
        p0flattener = P1Flattener(varalloc)
        stmtlist = p0flattener.flatten(ast)
        instruction_selector = P1InstructionSelector(varalloc)
        program = instruction_selector.visit(stmtlist)
        print program
