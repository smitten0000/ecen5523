# vim: set ts=4 sw=4 expandtab:

from x86ir import *
import logging


class P0Generator(object):
    def __init__(self, allowMem2Mem=True):
        self.log = logging.getLogger('compiler.generator')
        self.maxslot = 0
        self.allowMem2Mem = allowMem2Mem

    def get_stacksize(self):
        return self.maxslot * 4

    def generate(self, stmtlist):
        self.log.info ('Starting assembly generate')
        ret = self.visit(stmtlist)
        self.log.info ('Finished assembly generate')
        return ret

    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        if not meth:
            raise Exception('Unknown node: %s method: %s' % (node.__class__, meth_name))
        return meth(node, *args, **kwargs)

    def visit_Program(self, node, *args, **kwargs):
        program = "\n".join([self.visit(x) for x in node.statements])
        return """
.globl main
main:
\tpushl %%ebp
\tmovl %%esp, %%ebp
\tsubl $%s,%%esp # make stack space for variables
\tcall pymem_init
\tcall runtime_init

%s
\tcall runtime_shutdown
\tcall pymem_print_stats
\tcall pymem_shutdown
\tmovl $0, %%eax # put return value in eax
\tleave
\tret
""" % (self.get_stacksize(), program)

    def visit_Statement(self, node, *args, **kwargs):
        instructions = [self.visit(x) for x in node.instructions]
        # filter out removed instructions
        instructions = [x for x in instructions if x is not None]
        return ("\t# %s\n" %  node.source) + "\n".join(instructions) + "\n"

    def visit_Movl(self, node, *args, **kwargs):
        stmtlist=[]
        # if the source and destination are the same, then this is a no-op, return nothing
        if isinstance(node.src,Var) and isinstance(node.dst,Var):
            if node.src.storage.__class__ == node.dst.storage.__class__ and node.src.storage == node.dst.storage:
                self.log.debug('Removing unnecessary assignment: %s (%s)' % (Movl(node.src,node.dst), Movl(node.src.storage, node.dst.storage)))
                return None
            # handle memory to memory moves
            if isinstance(node.src.storage,StackSlot) and isinstance(node.dst.storage, StackSlot):
                if self.allowMem2Mem:
                    stmtlist.append('\tmovl %s, %s' % (self.visit(node.src), self.visit(Register('eax'))))
                    node.src = Register('eax')
                else:
                    raise Exception ('Detected memory to memory during %s"' % node.__class__.__name__)
        if isinstance(node.src,Var) and isinstance(node.src.storage, StackSlot) and isinstance(node.dst, StackSlot):
            if self.allowMem2Mem:
                stmtlist.append('\tmovl %s, %s' % (self.visit(node.src), self.visit(Register('eax'))))
                node.src = Register('eax')
            else:
                raise Exception ('Detected memory to memory during %s"' % node.__class__.__name__)
        if isinstance(node.src,StackSlot) and isinstance(node.dst, Var) and isinstance(node.dst.storage, StackSlot):
            if self.allowMem2Mem:
                stmtlist.append('\tmovl %s, %s' % (self.visit(node.src), self.visit(Register('eax'))))
                node.src = Register('eax')
            else:
                raise Exception ('Detected memory to memory during %s"' % node.__class__.__name__)
        stmtlist.append('\tmovl %s, %s' % (self.visit(node.src), self.visit(node.dst)))
        return "\n".join(stmtlist)
        
    def visit_Pushl(self, node, *args, **kwargs):
        return '\tpushl %s' % (self.visit(node.src))
    
    def visit_Addl(self, node, *args, **kwargs):
        stmtlist=[]
        # handle memory to memory moves
        if isinstance(node.src,Var) and isinstance (node.dst,Var):
            if isinstance(node.src.storage,StackSlot) and isinstance(node.dst.storage, StackSlot):
                if self.allowMem2Mem:
                    stmtlist.append('\tmovl %s, %s' % (self.visit(node.src), self.visit(Register('eax'))))
                    node.src = Register('eax')
                else:
                    raise Exception ('Detected memory to memory during %s"' % node.__class__.__name__)
        stmtlist.append('\taddl %s, %s' % (self.visit(node.src), self.visit(node.dst)))
        return "\n".join(stmtlist)

    def visit_Negl(self, node, *args, **kwargs):
        return '\tnegl %s' % (self.visit(node.operand))

    def visit_Call(self, node, *args, **kwargs):
        return '\tcall %s' % node.func

    def visit_Imm32(self, node, *args, **kwargs):
        return '$%s' % node.value

    def visit_Register(self, node, *args, **kwargs):
        return '%%%s' % node.name

    def visit_Var(self, node, *args, **kwargs):
        if node.storage is None:
            raise Exception ("Variable '%s' has not been assigned a storage location (either Register or StackSlot)" % node.name)
        if isinstance(node.storage, Register):
            return '%%%s' % node.storage.name
        elif isinstance(node.storage, StackSlot):
            if node.storage.slot > self.maxslot:
                self.maxslot = node.storage.slot
            return '%s(%%ebp)' % (node.storage.slot * -4)
        else:
            raise Exception("Unknown storage class '%s' for Variable '%s'" % (node.storage.__class__.__name__, node.name))
            

if __name__ == "__main__":
    import sys
    import logging.config
    from comp_util import *
    from p0parser import P0Parser
    from p0flattener import P0Flattener
    from p0insselector import P0InstructionSelector
    from p0regallocator import P0RegAllocator
    from p0stackallocator import P0StackAllocator
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        parser = P0Parser()
        parser.build()
        #ast = compiler.parseFile(testcase)
        ast = parser.parseFile(testcase)
        varalloc = VariableAllocator()
        p0flattener = P0Flattener(varalloc)
        stmtlist = p0flattener.flatten(ast)
        instruction_selector = P0InstructionSelector(varalloc)
        program = instruction_selector.visit(stmtlist)
        regallocator = P0RegAllocator(program)
        program = regallocator.substitute()
        #stackallocator = P0StackAllocator(program)
        #program = stackallocator.substitute()
        generator = P0Generator()
        print generator.generate(program)
        
