# vim: set ts=4 sw=4 expandtab:

from comp_util import *
from x86ir import *
from p0spillgenerator import P0SpillGenerator
import logging

logger = logging.getLogger(__name__)


class P1SpillGenerator(P0SpillGenerator):
    
    def __init__(self, varalloc):
        P0SpillGenerator.__init__(self, varalloc)

    def visit_x86If(self, node, *args, **kwargs):
        test = node.test
        spilled = False
        then_instr_list = []
        for x in node.then:
            spill, instrlist = self.visit(x)
            then_instr_list.extend(instrlist)
            if spill: spilled = True
        else_instr_list = []
        for x in node.else_:
            spill, instrlist = self.visit(x)
            # filter out no-ops
            else_instr_list.extend(instrlist)
            if spill: spilled = True
        return (False, [x86If(test, then_instr_list, else_instr_list)])

    def visit_Cmp(self, node, *args, **kwargs):
        src = node.rhs
        dst = node.lhs
        # do spill logic (see comment in Movl in p0spillgenerator)
        if isinstance(src,Var) and isinstance(dst, Var):
            assert(src.storage is not None)
            assert(dst.storage is not None)
            if isinstance(src.storage, StackSlot) and isinstance(dst.storage, StackSlot):
                logger.debug('Detected spill: %s' % node)
                var = Var(self.varalloc.get_next_var(),False) 
                logger.debug('Introducing variable: %s' % var)
                return (True, [Movl(dst, var), Cmp(src, var)])
        return (False, [Cmp(src, dst)])

    def visit_JumpEquals(self, node, *args, **kwargs):
        return (False, [node])

    def visit_Jump(self, node, *args, **kwargs):
        return (False, [node])

    def visit_Label(self, node, *args, **kwargs):
        return (False, [node])

    def visit_BitwiseNot(self, node, *args, **kwargs):
        return (False, [node])

    def visit_BitwiseAnd(self, node, *args, **kwargs):
        src = node.src
        dst = node.dst
        # do spill logic (see comment in Movl in p0spillgenerator)
        if isinstance(src,Var) and isinstance(dst, Var):
            assert(src.storage is not None)
            assert(dst.storage is not None)
            if isinstance(src.storage, StackSlot) and isinstance(dst.storage, StackSlot):
                logger.debug('Detected spill: %s' % node)
                var = Var(self.varalloc.get_next_var(),False) 
                logger.debug('Introducing variable: %s' % var)
                return (True, [Movl(dst, var), BitwiseAnd(src, var), Movl(var, dst)])
        return (False, [BitwiseAnd(src, dst)])

    def visit_BitwiseOr(self, node, *args, **kwargs):
        src = node.src
        dst = node.dst
        # do spill logic (see comment in Movl in p0spillgenerator)
        if isinstance(src,Var) and isinstance(dst, Var):
            assert(src.storage is not None)
            assert(dst.storage is not None)
            if isinstance(src.storage, StackSlot) and isinstance(dst.storage, StackSlot):
                logger.debug('Detected spill: %s' % node)
                var = Var(self.varalloc.get_next_var(),False) 
                logger.debug('Introducing variable: %s' % var)
                return (True, [Movl(dst, var), BitwiseOr(src, var), Movl(var, dst)])
        return (False, [BitwiseOr(src, dst)])

    def visit_BitShift(self, node, *args, **kwargs):
        src = node.src
        dst = node.dst
        # do spill logic (see comment in Movl in p0spillgenerator)
        if isinstance(src,Var) and isinstance(dst, Var):
            assert(src.storage is not None)
            assert(dst.storage is not None)
            if isinstance(src.storage, StackSlot) and isinstance(dst.storage, StackSlot):
                logger.debug('Detected spill: %s' % node)
                var = Var(self.varalloc.get_next_var(),False) 
                logger.debug('Introducing variable: %s' % var)
                return (True, [Movl(dst, var), BitShift(src, var), Movl(var, dst)])
        return (False, [BitShift(src, dst, node.dir)])


if __name__ == "__main__":
    import sys, compiler
    from comp_util import *
    from p0parser import P0Parser
    from p1flattener import P1Flattener
    from p1insselector import P1InstructionSelector
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    debug = True
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
