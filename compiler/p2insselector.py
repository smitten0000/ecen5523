# vim: set ts=4 sw=4 expandtab:
import compiler
from comp_util import *
from x86ir import *
from p1insselector import P1InstructionSelector


# Concept borrowed from http://peter-hoffmann.com/2010/extrinsic-visitor-pattern-python-inheritance.html
class P2InstructionSelector(P1InstructionSelector):
    '''Instruction selection for dynamic types as well as if, also converts an If node to Labels and Jumps'''
    def __init__(self, varalloc):
        P1InstructionSelector.__init__(self, varalloc)
        
    

if __name__ == "__main__":
    import sys
    from p0parser import P0Parser
    from p2flattener import P2Flattener
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    for testcase in testcases:
        #parser = P0Parser()
        #parser.build()
        #ast = parser.parseFile(testcase)
        ast = compiler.parseFile(testcase)
        
        varalloc = VariableAllocator()
        explicator = P1Explicate(varalloc)
        ast = explicator.explicate(ast)
        flattener = P2Flattener(varalloc)
        stmtlist = flattener.flatten(ast)
        instruction_selector = P2InstructionSelector(varalloc)
        program = instruction_selector.visit(stmtlist)
        print program
        print prettyAST(program)
