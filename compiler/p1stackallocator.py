# vim: set ts=4 sw=4 expandtab:

from p0stackallocator import *
from x86ir import *

class P1StackAllocator(P0StackAllocator):
    """ Class whose sole purpose is to replace Var instances with
    instances of StackSlot"""
    def __init__(self, program):
        P0StackAllocator.__init__(self, program)

    def visit_Cmp(self, node):
        return Cmp(self.visit(node.lhs), self.visit(node.rhs))

    def visit_BitwiseNot(self, node):
        return BitwiseNot(self.visit(node.value))

    def visit_BitwiseAnd(self, node):
        return BitwiseAnd(self.visit(node.src), self.visit(node.dst))

    def visit_BitwiseOr(self, node):
        return BitwiseOr(self.visit(node.src), self.visit(node.dst))

    def visit_BitShift(self, node):
        return BitShift(self.visit(node.src), self.visit(node.dst), node.dir)

    def visit_Label(self, node):
        return node

    def visit_Jump(self, node):
        return node

    def visit_JumpEquals(self, node):
        return node

if __name__ == "__main__":
    import sys, compiler
    import logging, logging.config
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
        ast = compiler.parseFile(testcase)
        #ast = parser.parseFile(testcase)
        varalloc = VariableAllocator()
        p1explicator = P1Explicate(varalloc)
        ast = p1explicator.explicate(ast)
        p1flattener = P1Flattener(varalloc)
        stmtlist = p1flattener.flatten(ast)
        instruction_selector = P1InstructionSelector(varalloc)
        program = instruction_selector.visit(stmtlist)
        stackallocator = P1StackAllocator(program)
        print stackallocator.substitute()
