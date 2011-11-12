# vim: set ts=4 sw=4 expandtab:

from comp_util import *
from x86ir import *
from p0regallocator import P0RegAllocator
from p2regallocator import P2RegAllocator
from p3spillgenerator import P3SpillGenerator

class P3RegAllocator(P2RegAllocator):
    def __init__(self, program, varalloc):
        P2RegAllocator.__init__(self, program, varalloc)
        self.spillgenerator = P3SpillGenerator(varalloc)

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
        if isinstance(instr, x86While):
            if isinstance(instr.test[0], Var):
                self._add_vertex(instr.test[0])
            return (set(instr.test[0]) | self.Lbefore(instr.test[1],instr.liveafter) | self.Lbefore(instr.body,instr.liveafter))
        elif isinstance(instr, x86If):
            if isinstance(instr.test, Var):
                self._add_vertex(instr.test)
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

    def build_interference_graph_instr(self, instructions):
        for instr in instructions:
            # get the list of variables live at this point
            live_after_k = instr.liveafter
            # rule #0 (added in p1)
            # Need to recurse on x86If nodes.
            if isinstance(instr,x86If):
                for live in live_after_k:
                    if isinstance(instr.test,Var) and live != instr.test:
                        self._add_edge(live, instr.test)
                self.log.debug('build_interf_graph: x86If.then = %s' % instr.then)
                self.log.debug('build_interf_graph: x86If.else_ = %s' % instr.else_)
                self.build_interference_graph_instr(instr.then)
                self.build_interference_graph_instr(instr.else_)
            elif isinstance(instr,x86While):
                for live in live_after_k:
                    if isinstance(instr.test[0],Var) and live != instr.test[0]:
                        self._add_edge(live, instr.test[0])
                self.log.debug('build_interf_graph: x86While.test[1] = %s' % instr.test[1])
                self.log.debug('build_interf_graph: x86While.body = %s' % instr.body)
                self.build_interference_graph_instr(instr.test[1])
                self.build_interference_graph_instr(instr.body)
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
            elif isinstance(instr,(Call,CallAddress)):
                for live in live_after_k:
                    for reg in P0RegAllocator.CALLER_SAVE:
                        self._add_edge(live, reg)

    def visit_x86While(self, node, *args, **kwargs):
        test = [self.visit(x) for x in node.test[1]]
        test = [x for x in test if x is not None]
        body = [self.visit(x) for x in node.body]
        body = [x for x in body if x is not None]
        self.log.debug('x86While=%s'%node)
        return x86While((self.visit(node.test[0]),test), body, [], node.lineno)


if __name__ == "__main__":
    import sys, compiler
    import logging.config
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
        ast = unique.transform(ast)        
        ast = explicator.explicate(ast)
        ast = heap.transform(ast)
        astlist = closure.transform(ast)
        for ast in astlist:
            ast = flatten.flatten(ast)
            program = insselector.transform(ast)
            regallocator = P3RegAllocator(program, varalloc)
            program = regallocator.substitute()
            print '\nFunction\n================='
            print program
            print prettyAST(program)
