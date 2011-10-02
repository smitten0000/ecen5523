'''
Created on Oct 1, 2011

@author: relsner
'''
import compiler
from p0generator import P0Generator 

        

class P1Generator(P0Generator):
    '''
    Adds the necessary assembly instructions for type checking, if expressions, etc
    '''
    def __init__(self,params):
        '''
        Constructor
        '''
        P0Generator.__init__(self)

        
    def visit_GetTag(self, node, *args, **kwargs):
        return '\tand %s, $3' %  self.visit(node.arg)    
    
    
    def visit_Or(self, node, *args, **kwargs):
        return '\tOR %s, %s' % (self.visit(node.nodes[0]), self.visit(node.nodes[1]))
    def visit_And(self, node, *args, **kwargs):
        return '\tAND %s, %s' % (self.visit(node.nodes[0]), self.visit(node.nodes[1]))
    def visit_Not(self, node, *args, **kwargs):
        return '\tNOT %s' % self.visit(node.expr)
    def visit_InjectFrom(self, node, *args, **kwargs):
        
    
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
        ast = compiler.parseFile(testcase)
#        ast = parser.parseFile(testcase)
        varalloc = VariableAllocator()
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
        
        