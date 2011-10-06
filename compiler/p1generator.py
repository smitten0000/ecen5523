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
    def __init__(self):
        '''
        Constructor
        '''
        P0Generator.__init__(self)
    
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
        return '\tCMP %s, %s' % (self.visit(node.lhs), self.visit(node.rhs))    
    def visit_Or(self, node, *args, **kwargs):
        return '\tOR %s, %s' % (self.visit(node.nodes[0]), self.visit(node.nodes[1]))
    def visit_And(self, node, *args, **kwargs):
        return '\tAND %s, %s' % (self.visit(node.nodes[0]), self.visit(node.nodes[1]))
    def visit_BitwiseNot(self, node, *args, **kwargs):
        return '\tNOT %s' % self.visit(node.value)
    def visit_JumpEquals(self, node, *args, **kwargs):
        return '\tJE %s' % node.label
    def visit_Jump(self, node, *args, **kwargs):
        return '\tJMP %s' % node.label
    def visit_Label(self, node, *args, **kwargs):
        return '%s:' % node.label
    def visit_BitShift(self, node, *args, **kwargs ):
        if node.dir == 'left':
            return '\tSHL %s, %s' % (self.visit(node.places), self.visit(node.value))
        elif node.dir == 'right':
            return '\tSHR %s, %s' % (self.visit(node.places), self.visit(node.value))
        else:
            raise Exception("Unknown direction '%s' for shift" % node.dir)
    def visit_BitwiseAnd(self, node, *args, **kwargs):
        return '\tandl %s, %s' % (self.visit(node.src), self.visit(node.dst))
    def visit_BitwiseOr(self, node, *args, **kwargs):
        return '\torl %s, %s' % (self.visit(node.src), self.visit(node.dst))
    
if __name__ == "__main__":
    import sys
    from comp_util import *
    
    from p1flattener import P1Flattener
    from p1insselector import P1InstructionSelector
    from p1regallocator import P1RegAllocator
    from p0stackallocator import P0StackAllocator
    if len(sys.argv) < 2:
        sys.exit(1)
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
        instruction_selector = P1InstructionSelector(varalloc)
        program = instruction_selector.visit(stmtlist)
        regallocator = P1RegAllocator(program)
        program = regallocator.substitute()
        #stackallocator = P0StackAllocator(program)
        #program = stackallocator.substitute()
        generator = P1Generator()
        print generator.generate(program)
