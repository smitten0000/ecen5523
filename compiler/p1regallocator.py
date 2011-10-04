# vim: set ts=4 sw=4 expandtab:

import compiler

from comp_util import *
from x86ir import *
from p0regallocator import P0RegAllocator

class P1RegAllocator(P0RegAllocator):
    
    def __init__(self, program):
        P0RegAllocator.__init__(self, program)

    def build_interference_graph(self):
        instructions = self.program.instructions()
        for k in range(0,len(instructions)):
            instr = instructions[k]
            # get the list of variables live at this point
            live_after_k = list(self.liveness_after_k_dict[k])
            # rule #1
            if isinstance(instr,Movl):
                for live in live_after_k:
                    if instr.dst != live or (isinstance(instr.src,Var) and instr.src != live):
                        self._add_edge(instr.dst, live)
            # rule #2
            elif isinstance(instr,(Addl,Negl)):
                for live in live_after_k:
                    if isinstance(instr, Addl) and isinstance(instr.dst, Var):
                        self._add_edge(instr.dst, live)
                    elif isinstance(instr, Negl) and isinstance(instr.operand, Var):   
                        self._add_edge(instr.operand, live)
            # rule #3
            elif isinstance(instr,Call):
                for live in live_after_k:
                    for reg in P0RegAllocator.CALLER_SAVE:
                        self._add_edge(live, reg)


if __name__ == "__main__":
    import sys
    from comp_util import *
    from p0parser import P0Parser
    from p1flattener import P1Flattener
    from p1insselector import P1InstructionSelector
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    for testcase in testcases:
        #parser = P0Parser()
        #parser.build()
        #ast = parser.parseFile(testcase)
        ast = compiler.parseFile(testcase)
        varalloc = VariableAllocator()
        p0flattener = P1Flattener(varalloc)
        stmtlist = p0flattener.flatten(ast)
        instruction_selector = P1InstructionSelector(varalloc)
        program = instruction_selector.visit(stmtlist)
        regallocator = P0RegAllocator(program)
        regallocator.substitute()
        #import cProfile as profile
        #import pstats
        #output_file = 'profile.out'
        #profile.run('regallocator.substitute()', output_file)
        #p = pstats.Stats(output_file)
        #print "name: "
        #print p.sort_stats('name')
        #print "all stats: "
        #p.print_stats()
        #print "cumulative (top 10): "
        #p.sort_stats('cumulative').print_stats(10)
