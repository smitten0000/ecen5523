# vim: set ts=4 sw=4 expandtab:

class P0RegAllocator:
    def __init__(self):
        self.liveness_after_k_dict={}

    def liveness_analyze(self, program):
        num_instr = reduce(lambda x,y: x + y, [len(x.instructions) for x in program.statements], 0)
        print "num_instr = ", num_instr
        alive = set()
        i = num_instr
        for instr in reversed(program.instructions()):
            i = i - 1
            self.liveness_after_k_dict[i] = alive
            alive = (alive - set(instr.writes())) | set(instr.reads())
        i = 0
        for instr in program.instructions():
            print "%5s. %-40s : %s" % (i, instr, self.liveness_after_k_dict[i])
            i = i + 1


if __name__ == "__main__":
    import sys
    from p0parser import P0Parser
    from p0flattener import P0Flattener
    from p0insselector import P0InstructionSelector
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    for testcase in testcases:
        parser = P0Parser()
        parser.build()
        #ast = compiler.parseFile(testcase)
        ast = parser.parseFile(testcase)
        p0flattener = P0Flattener()
        stmtlist = p0flattener.flatten(ast)
        instruction_selector = P0InstructionSelector()
        program = instruction_selector.visit(stmtlist)
        regallocator = P0RegAllocator()
        regallocator.liveness_analyze(program)
