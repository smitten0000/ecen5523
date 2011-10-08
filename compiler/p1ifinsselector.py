# vim: set ts=4 sw=4 expandtab:

from comp_util import *
from x86ir import *
# to flatten nested lists into a flat list
from compiler.ast import flatten

# Concept borrowed from http://peter-hoffmann.com/2010/extrinsic-visitor-pattern-python-inheritance.html
class P1IfInstructionSelector(object):
    def __init__(self, varalloc, labelalloc):
        self.varalloc = varalloc
        self.labelalloc = labelalloc

    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        # return the node if there is no visit method
        if not meth: return node
        return meth(node, *args, **kwargs)

    def visit_Program(self, node):
        return Program([self.visit(x) for x in node.statements])

    def visit_Statement(self, node, *args, **kwargs):
        # flattened the returned list since it may be nested, due to nested x86If instructions
        instructions = flatten([self.visit(x) for x in node.instructions])
        # filter out any no-ops
        instructions = filter(lambda x: x is not None, instructions)
        return Statement(instructions,node.source)

    def visit_x86If(self, node):
        '''Generate a cmp/je/jmp set with 0 for the else case (true is anything not 0) of an if statement'''
        testvar = node.test
        # filter out any no-ops
        then  = [self.visit(x) for x in node.then if x is not None]
        else_ = [self.visit(x) for x in node.else_ if x is not None]
        # Don't have to worry about the test statements; they
        # were already put ahead of this node during flattening (see p1flattener.py)
        # Now, generate the branches and jumps
        label = self.labelalloc.get_next_label()
        #cmpvarname = self.varalloc.get_next_var()  
        stmts = []
        stmts.extend([Cmp(Imm32(0),testvar), 
                      JumpEquals('else%s' % label)])
#        stmts.extend([Movl(Imm32(0), Var(cmpvarname)), 
#                      Cmp(testvar, Var(cmpvarname)), 
#                      JumpEquals('else%s' % label)])
        stmts.extend(then)
        stmts.append(Jump('end%s' % label))
        stmts.append(Label('else%s' % label))
        stmts.extend(else_)
        stmts.append(Label('end%s' % label ))
        return stmts

if __name__ == "__main__":
    import sys, compiler
    from p0parser import P0Parser
    from p1explicate import P1Explicate
    from p1flattener import P1Flattener
    from p1insselector import P1InstructionSelector
    from p1regallocator import P1RegAllocator
    from p1ifinsselector import P1IfInstructionSelector
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    for testcase in testcases:
        #parser = P0Parser()
        #parser.build()
        ast = compiler.parseFile(testcase)
        #ast = parser.parseFile(testcase)
        ast = compiler.parseFile(testcase)
        varalloc = VariableAllocator()
        explicate = P1Explicate(varalloc)
        ast = explicate.explicate(ast)
        flattener = P1Flattener(varalloc)
        stmtlist = flattener.flatten(ast)
        insselector = P1InstructionSelector(varalloc)
        program = insselector.visit(stmtlist)
        regallocator = P1RegAllocator(program)
        program = regallocator.substitute()
        ifinsselector = P1IfInstructionSelector(varalloc,insselector.labelalloc)
        program = ifinsselector.visit(program)
        print program
        print prettyAST(program)
