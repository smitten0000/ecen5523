# vim: set ts=4 sw=4 expandtab:

from x86ir import *

class P0Generator(object):
    def __init__(self, allowMem2Mem=True):
        self.maxslot = 0
        self.allowMem2Mem = allowMem2Mem

    def get_stacksize(self):
        return self.maxslot * 4

    def generate(self, stmtlist):
        return self.visit(stmtlist)

    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        if not meth:
            raise Exception('Unknown node: %s method: %s' % (node.__class__, meth))
        return meth(node, *args, **kwargs)

    def visit_Program(self, node, *args, **kwargs):
        program = "\n".join([self.visit(x) for x in node.statements])
        return """
.globl main
main:
\tpushl %%ebp
\tmovl %%esp, %%ebp
\tsubl $%s,%%esp # make stack space for variables

%s
\tmovl $0, %%eax # put return value in eax
\tleave
\tret
""" % (self.get_stacksize(), program)

    def visit_Statement(self, node, *args, **kwargs):
        return ("\t# %s\n" %  node.source) + "\n".join([self.visit(x) for x in node.instructions]) + "\n"

    def visit_Movl(self, node, *args, **kwargs):
        stmtlist=[]
        # if the source and destination are the same, then this is a no-op, return nothing
        #if node.src.__class__ == node.dst.__class__ and node.src == node.dst:
        #    return ""
        # handle memory to memory moves
        if isinstance(node.src,StackSlot) and isinstance(node.dst, StackSlot):
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
        if isinstance(node.src,StackSlot) and isinstance(node.dst, StackSlot):
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
    from comp_util import *
    from p0parser import P0Parser
    from p0flattener import P0Flattener
    from p0insselector import P0InstructionSelector
    from p0regallocator import P0RegAllocator
    from p0stackallocator import P0StackAllocator
    if len(sys.argv) < 2:
        sys.exit(1)
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
        
