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

    def visit_x86If(self, node):
        then = [self.visit(x) for x in node.then if x is not None]
        else_ = [self.visit(x) for x in node.else_ if x is not None]
        return x86If(self.visit(node.test), then, else_)

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
        explicator = P1Explicate(varalloc)
        flattener = P1Flattener(varalloc)
        instruction_selector = P1InstructionSelector(varalloc)
        ast = explicator.explicate(ast)
        ast = flattener.flatten(ast)
        ast = instruction_selector.visit(ast)
        stackallocator = P1StackAllocator(ast)
        ast = stackallocator.substitute()
        print prettyAST(ast)
