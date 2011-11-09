'''
Created on Oct 1, 2011

@author: relsner
'''
from compiler import parseFile
from x86ir import *
from p0generator import P0Generator 

class P1Generator(P0Generator):
    '''
    Adds the necessary assembly instructions for type checking, if expressions, etc
    '''
    def __init__(self, allowMem2Mem=True):
        '''
        Constructor
        '''
        P0Generator.__init__(self, allowMem2Mem)
    
    def visit_Imm32(self, node, *args, **kwargs):
        # This is most likely wrong, we will need to change some logic in the
        # If statement because x = 2; True if x else False ==> True
        if node.value == 'True':
            return '$1'
        elif node.value =='False':
            return '$0'
        return P0Generator.visit_Imm32(self, node)
    def visit_GetTag(self, node, *args, **kwargs):
        return '\tand %s, $3' %  self.visit(node.arg)    
    def visit_Cmp(self, node, *args, **kwargs):
        stmtlist=[]
        if isinstance(node.lhs,Var) and isinstance(node.rhs, Var):
            # handle memory to memory "cmp" (this is just here to work with the stack allocator)
            if isinstance(node.lhs.storage,StackSlot) and isinstance(node.rhs.storage, StackSlot):
                if self.allowMem2Mem:
                    stmtlist.append('\tmovl %s, %s' % (self.visit(node.lhs), self.visit(Register('eax'))))
                    node.lhs = Register('eax')
                else:
                    raise Exception ('Detected memory to memory during %s"' % node.__class__.__name__)
                # handle imm32 to memory "cmp" (this is just here to work with the stack allocator)
            elif isinstance(node.lhs.storage,StackSlot) and isinstance(node.rhs, Imm32):
                if self.allowMem2Mem:
                    stmtlist.append('\tmovl %s, %s' % (self.visit(node.rhs), self.visit(Register('eax'))))
                    node.rhs = Register('eax')
                else:
                    raise Exception ('Detected memory to imm32 during %s"' % node.__class__.__name__)
        stmtlist.append('\tcmpl %s, %s' % (self.visit(node.lhs), self.visit(node.rhs)))
        return "\n".join(stmtlist)
    def visit_BitwiseNot(self, node, *args, **kwargs):
        return '\tNOTL %s' % self.visit(node.value)
    def visit_JumpEquals(self, node, *args, **kwargs):
        return '\tJE %s' % node.label
    def visit_Jump(self, node, *args, **kwargs):
        return '\tJMP %s' % node.label
    def visit_Label(self, node, *args, **kwargs):
        return '%s:' % node.label
    def visit_BitShift(self, node, *args, **kwargs ):
        if node.dir == 'left':
            return '\tsall %s, %s' % (self.visit(node.src), self.visit(node.dst))
        elif node.dir == 'right':
            return '\tsarl %s, %s' % (self.visit(node.src), self.visit(node.dst))
        else:
            raise Exception("Unknown direction '%s' for shift" % node.dir)
    def visit_BitwiseAnd(self, node, *args, **kwargs):
        stmtlist=[]
        # handle memory to memory "and" (this is just here to work with the stack allocator)
        if isinstance(node.src,Var) and isinstance(node.dst, Var):
            if isinstance(node.src.storage,StackSlot) and isinstance(node.dst.storage, StackSlot):
                if self.allowMem2Mem:
                    stmtlist.append('\tmovl %s, %s' % (self.visit(node.src), self.visit(Register('eax'))))
                    node.src = Register('eax')
                else:
                    raise Exception ('Detected memory to memory during %s"' % node.__class__.__name__)
        stmtlist.append('\tandl %s, %s' % (self.visit(node.src), self.visit(node.dst)))
        return "\n".join(stmtlist)
    def visit_BitwiseOr(self, node, *args, **kwargs):
        stmtlist=[]
        # handle memory to memory "or" (this is just here to work with the stack allocator)
        if isinstance(node.src,Var) and isinstance(node.dst, Var):
            if isinstance(node.src.storage,StackSlot) and isinstance(node.dst.storage, StackSlot):
                if self.allowMem2Mem:
                    stmtlist.append('\tmovl %s, %s' % (self.visit(node.src), self.visit(Register('eax'))))
                    node.src = Register('eax')
                else:
                    raise Exception ('Detected memory to memory during %s"' % node.__class__.__name__)
        stmtlist.append('\torl %s, %s' % (self.visit(node.src), self.visit(node.dst)))
        return "\n".join(stmtlist)

    
if __name__ == "__main__":
    import sys
    import logging.config
    from comp_util import *
    
    from p1flattener import P1Flattener
    from p1insselector import P1InstructionSelector
    from p1regallocator import P1RegAllocator
    from p0stackallocator import P0StackAllocator
    from p1ifinsselector import P1IfInstructionSelector
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
#        parser = P1parser()
#        parser.build()
        ast = parseFile(testcase)
#        ast = parser.parseFile(testcase)
        varalloc = VariableAllocator()
        p1explicate = P1Explicate(varalloc)
        ast = p1explicate.explicate(ast)
        p1flattener = P1Flattener(varalloc)
        stmtlist = p1flattener.flatten(ast)
        insselector = P1InstructionSelector(varalloc)
        program = insselector.visit(stmtlist)
        regallocator = P1RegAllocator(program)
        program = regallocator.substitute()
        #stackallocator = P0StackAllocator(program)
        #program = stackallocator.substitute()
        ifinsselector = P1IfInstructionSelector(varalloc,insselector.labelalloc)
        program = ifinsselector.visit(program)
        generator = P1Generator()
        print generator.generate(program)
