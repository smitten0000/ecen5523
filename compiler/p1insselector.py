# vim: set ts=4 sw=4 expandtab:
import compiler
from comp_util import *
from x86ir import *
from p0insselector import P0InstructionSelector


class LabelAllocator(object):
    def __init__(self):
        self.count = 0
        
    def get_next_label(self):
        label= '_label_%s' % self.count
        self.count= self.count+1
        return label


# Concept borrowed from http://peter-hoffmann.com/2010/extrinsic-visitor-pattern-python-inheritance.html
class P1InstructionSelector(P0InstructionSelector):
    '''Instruction selection for dynamic types as well as if, also converts an If node to Labels and Jumps'''
    def __init__(self, varalloc):
        P0InstructionSelector.__init__(self, varalloc)
        self.labelalloc = LabelAllocator()
    def visit_Not(self, node, *args, **kwargs):
        (var, stmt) = self.visit(node.expr)
        print var
        
        return stmt+[BitwiseNot(var)]        
    def visit_If(self, node, *args, **kwargs):
        '''Generate a cmp/je/jmp set with 0 for the else case (true is anything not 0) of an if statement'''
        label = self.labelalloc.get_next_label()
        (test, then) = node.tests[0]
        #then = [self.visit(x) for x in then]
        t2 = []
        for thenexpr in then:
            t2 = [x for x in self.visit(thenexpr)]
        then = t2
        cmpvarname = self.varalloc.get_next_var()  
        stmts = [Movl(Imm32(0), Var(cmpvarname)), Cmp(Var(test.name), Var(cmpvarname)), JumpEquals('else%s' % label )]
        stmts.extend(then)
        stmts.append(Jump('end%s'%label))
        stmts.append(Label('else%s'%label))
        e2 = []
        for ex in node.else_:
            e2 = [x for x in self.visit(ex)]
        else_ = e2
        stmts.extend(else_)
        stmts.append(Label('end%s' % label ))
        return stmts
        

if __name__ == "__main__":
    import sys
    from p0parser import P0Parser
    from p1flattener import P1Flattener
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    for testcase in testcases:
        #parser = P0Parser()
        #parser.build()
        #ast = parser.parseFile(testcase)
        ast = compiler.parseFile(testcase)
        
        varalloc = VariableAllocator()
        flattener = P1Flattener(varalloc)
        stmtlist = flattener.flatten(ast)
        print stmtlist
        instruction_selector = P1InstructionSelector(varalloc)
        program = instruction_selector.visit(stmtlist)
