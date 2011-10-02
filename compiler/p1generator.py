'''
Created on Oct 1, 2011

@author: relsner
'''
import compiler
from p0generator import P0Generator 


class LabelAllocator(object):
    def __init__(self):
        self.count = 0
        
    def get_next_label(self):
        label= '_label_%s' % self.count
        self.count= self.count+1
        return label
        

class P1Generator(P0Generator):
    '''
    Adds the necessary assembly instructions for type checking, if expressions, etc
    '''


    def __init__(self,params):
        '''
        Constructor
        '''
        P0Generator.__init__(self)
        self.labelalloc = LabelAllocator()
        
    def visit_GetTag(self, node, *args, **kwargs):
        return '\tand %s, $3' %  self.visit(node.arg)    
    
    def visit_If(self, node, *args, **kwargs):
        '''Generate a cmp/je/jmp set with 0 for the else case (true is anything not 0) of an if statement'''
        label = self.labelalloc.get_next_label()
        stmts = []
        # If([(vartes, Stmt(then))], else_
        stmts.append('\tcmpl %s, $0' % self.visit(node.tests[0]))
        stmts.append('\tje else%s' % label)
        stmts.append(self.visit(node.tests[1]))
        stmts.append('\tjmp end%s' % label)
        stmts.append('else%s' % label)
        stmts.append(self.visit(node.else_))
        stmts.append('end%s' % label)
        return '\n'.join(stmts)
    
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
        
        