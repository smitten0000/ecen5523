# vim: set ts=4 sw=4 expandtab:

import compiler

from comp_util import *
from x86ir import *
from p0regallocator import P0RegAllocator
from p1spillgenerator import P1SpillGenerator

class P2RegAllocator(P1RegAllocator):
    
    def __init__(self, program, varalloc):
        P1RegAllocator.__init__(self, program, varalloc)
        self.spillgenerator = P1SpillGenerator(varalloc)


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
            elif isinstance(instr,(Call,CallAddress)):
                for live in live_after_k:
                    for reg in P0RegAllocator.CALLER_SAVE:
                        self._add_edge(live, reg)

    def visit_CallAddress(self, node, *args, **kwargs):
        return CallAddress(self.visit(node.address))

    def visit_Ret(self, node, *args, **kwargs):
        return Ret(self.visit(node.value))

    def visit_x86Function(self, node, *args, **kwargs):
        return x86Function(node.name, node.argnames, self.visit(node.code), node.lineno)


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
        varalloc = VariableAllocator()
        p2unique = P2UniquifyVars()
        p2explicator = P2Explicate(varalloc)
        p2heap = P2Heapify()
        p2closure = P2ClosureConversion(p2explicator, varalloc)
        p2flatten = P2Flattener(varalloc)
        p2insselector = P2InstructionSelector(varalloc)

        ast = compiler.parseFile(testcase)
        unique = p2unique.transform(ast)        
        explicated = p2explicator.explicate(unique)
        #heaped = p2heap.transform(explicated)
        astlist = p2closure.transform(explicated)
        for ast in astlist:
            ast = p2flatten.flatten(ast)
            program = p2insselector.transform(ast)
            p2regallocator = P2RegAllocator(program, varalloc)
            program = p2regallocator.substitute()
            print '\nFunction\n================='
            print prettyAST(program)
