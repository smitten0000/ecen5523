# vim: set ts=4 sw=4 expandtab:

from comp_util import *
from x86ir import *
import logging

logger = logging.getLogger(__name__)

class P0SpillGenerator:
    def __init__(self, varalloc):
        self.varalloc = varalloc

    def generate_spill(self, program):
        """ Returns a tuple; the first element is a boolean indicating whether or not a
        spill occurred;  The second element is the new representation of the program,
        with additional instructions added to replace memory to memory operations,
        which are not allowed in x86"""
        spilled, program = self.visit(program)
        return (spilled, program)

    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        if not meth:
            raise Exception('Unknown node: %s method: %s' % (node.__class__, meth_name))
        return meth(node, *args, **kwargs)

    def visit_Program(self, node, *args, **kwargs):
        stmts = []
        spilled = False
        for x in node.statements:
            spill, stmt = self.visit(x)
            stmts.append(stmt)
            if spill: spilled = True
        return (spilled, Program(stmts))

    def visit_Statement(self, node, *args, **kwargs):
        instructions = []
        spilled = False
        for x in node.instructions:
            spill, instrlist = self.visit(x)
            instructions.extend(instrlist)
            if spill: spilled = True
        return (spilled, Statement(instructions,node.source))

    def visit_Movl(self, node, *args, **kwargs):
        src = node.src
        dst = node.dst
        # if source and destination are both memory references (StackSlot),
        # then we have to generate an additional Movl instruction to copy the
        # contents of the src to a register, and then from the register to the
        # dst.  This "register" is actually a variable marked as unspillable.
        if isinstance(src,Var) and isinstance(dst, Var):
            assert(src.storage is not None)
            assert(dst.storage is not None)
            if isinstance(src.storage, StackSlot) and isinstance(dst.storage, StackSlot):
                logger.debug('Detected spill: %s' % node)
                var = Var(self.varalloc.get_next_var(),False)  # 2nd arg False = unspillable
                logger.debug('Introducing variable: %s' % var)
                # return true for 1st element in tuple, to indicate a spill has happened.
                return (True, [Movl(src, var), Movl(var, dst)])
        return (False, [Movl(src,dst)])
        
    def visit_Pushl(self, node, *args, **kwargs):
        return (False, [node])

    def visit_Addl(self, node, *args, **kwargs):
        src = node.src
        dst = node.dst
        # do spill logic (see comment in Movl)
        if isinstance(src,Var) and isinstance(dst, Var):
            assert(src.storage is not None)
            assert(dst.storage is not None)
            if isinstance(src.storage, StackSlot) and isinstance(dst.storage, StackSlot):
                logger.debug('Detected spill: %s' % node)
                var = Var(self.varalloc.get_next_var(),False) 
                logger.debug('Introducing variable: %s' % var)
                return (True, [Movl(dst, var), Addl(src, var), Movl(var, dst)])
        return (False, [Addl(src,dst)])

    def visit_Negl(self, node, *args, **kwargs):
        return (False, [node])

    def visit_Call(self, node, *args, **kwargs):
        return (False, [node])



if __name__ == "__main__":
    import sys, compiler
    from comp_util import *
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
        varalloc = VariableAllocator()
        flattener = P0Flattener(varalloc)
        stmtlist = p0flattener.flatten(ast)
        insselector = P0InstructionSelector(varalloc)
        program = insselector.visit(stmtlist)
        regallocator = P0RegAllocator(program, varalloc)
        print regallocator.substitute()
