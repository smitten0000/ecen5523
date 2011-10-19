# vim: set ts=4 sw=4 expandtab:

import compiler

from comp_util import *
from x86ir import *
from p0regallocator import P0RegAllocator
from p1spillgenerator import P1SpillGenerator

class P1RegAllocator(P0RegAllocator):
    
    def __init__(self, program, varalloc):
        P0RegAllocator.__init__(self, program, varalloc)
        self.spillgenerator = P1SpillGenerator(varalloc)

    def Lbefore(self, instructionlist, Lafter=set()):
        """Computes liveness recursively.  Liveness is stored as an attribute on
        the instruction itself, to be used later during construction of the
        interference graph."""
        # our base case
        if len(instructionlist) < 1:
            return Lafter
        instr = instructionlist[0]
        # compute Lafter (haha, laughter, get it?)
        laughter = self.Lbefore(instructionlist[1:], Lafter)
        # just store the liveness set in the instruction node itself.
        instr.liveafter = laughter
        # Now, return the liveness before. How this is computed depends on whether 
        # we have an x86If or a real Instruction.
        if isinstance(instr, x86If):
            return (set(instr.test) | self.Lbefore(instr.then,instr.liveafter) | self.Lbefore(instr.else_,instr.liveafter))
        elif isinstance(instr, Instruction):
            # get reads/writes performed by instruction, but only for variables
            writes = set(filter(lambda x: isinstance(x,Var), instr.writes()))
            reads = set(filter(lambda x: isinstance(x,Var), instr.reads()))
            # add all variables to the graph
            for x in writes: self._add_vertex(x)
            for x in reads: self._add_vertex(x)
            # For all x86 instructions, Lbefore(instr,Lafter) = Lafter - writes | reads
            return (instr.liveafter - writes) | reads
        else:
            raise Exception("Unknown instruction: '%s'" % instr)

    # overridden from p0regallocator.py since we are changing our strategy
    # to handle structured control flow (If)
    def liveness_analyze(self):
        instructions = self.program.instructions()
        # compute liveness recursively
        self.Lbefore(instructions)

    def build_interference_graph_instr(self, instructions):
        for instr in instructions:
            # get the list of variables live at this point
            live_after_k = instr.liveafter
            # rule #0 (added in p1)
            # Need to recurse on x86If nodes.
            if isinstance(instr,x86If):
                self.build_interference_graph_instr(instr.then)
                self.build_interference_graph_instr(instr.else_)
            # rule #1
            elif isinstance(instr,Movl):
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

    # overridden from p0regallocator.py 
    def build_interference_graph(self):
        self.build_interference_graph_instr(self.program.instructions())

    def print_liveness_instr(self, instructions):
        for instr in instructions:
            print "%5s. %-40s : %s" % (self.instrcnt, instr, instr.liveafter)
            if isinstance(instr,x86If):
                self.print_liveness_instr(instr.then)
                self.print_liveness_instr(instr.else_)

    # override from p0regallocator.py
    def print_liveness(self):
        self.print_liveness_instr(self.program.instructions())

    def visit_x86If(self, node, *args, **kwargs):
        then = [self.visit(x) for x in node.then]
        then = [x for x in then if x is not None]
        else_ = [self.visit(x) for x in node.else_]
        else_ = [x for x in else_ if x is not None]
        return x86If(self.visit(node.test), then, else_)

    def visit_Cmp(self, node, *args, **kwargs):
        return Cmp(self.visit(node.lhs), self.visit(node.rhs))

    def visit_JumpEquals(self, node, *args, **kwargs):
        return node

    def visit_Jump(self, node, *args, **kwargs):
        return node

    def visit_Label(self, node, *args, **kwargs):
        return node

    def visit_BitwiseNot(self, node, *args, **kwargs):
        return BitwiseNot(self.visit(node.value))

    def visit_BitwiseAnd(self, node, *args, **kwargs):
        return BitwiseAnd(self.visit(node.src), self.visit(node.dst))

    def visit_BitwiseOr(self, node, *args, **kwargs):
        return BitwiseOr(self.visit(node.src), self.visit(node.dst))

    def visit_BitShift(self, node, *args, **kwargs):
        return BitShift(self.visit(node.src), self.visit(node.dst), node.dir)


if __name__ == "__main__":
    import sys
    import logging.config
    from comp_util import *
    from p0parser import P0Parser
    from p1flattener import P1Flattener
    from p1insselector import P1InstructionSelector
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        #parser = P0Parser()
        #parser.build()
        #ast = parser.parseFile(testcase)
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
