# vim: set ts=4 sw=4 expandtab:

from comp_util import *
from x86ir import *

# Concept borrowed from http://peter-hoffmann.com/2010/extrinsic-visitor-pattern-python-inheritance.html
class P0InstructionSelector(object):
    def __init__(self):
        self.varset = set()

    def allocate_var(self, varname):
        if self.is_allocated(varname):
            raise Exception("Variable '%s' already allocated" % varname)
        self.varset.add(varname)

    def is_allocated(self, varname):
        if varname in self.varset:
            return True
        return False

    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        if not meth:
            raise Exception('Unknown node: %s method: %s' % (node.__class__, meth))
        return meth(node, *args, **kwargs)

    def visit_Module(self, node, *args, **kwargs):
        return self.visit(node.node)

    def visit_Stmt(self, node, *args, **kwargs):
        return Program([Statement(self.visit(x),pretty(x)) for x in node.nodes])

    def visit_Assign(self, node, *args, **kwargs):
        assname = node.nodes[0]
        if not self.is_allocated(assname.name):
            self.allocate_var(assname.name)
        loc, stmtlist = self.visit(node.expr)
        return stmtlist + [Movl(loc, Var(assname.name))]
        
    def visit_Printnl(self, node, *args, **kwargs):
        loc, stmtlist = self.visit(node.nodes[0])
        return stmtlist + [Pushl(loc), 
                           Call('print_int_nl'),
                           Addl(Imm32(4), Register('esp'))]

    def visit_Add(self, node, *args, **kwargs):
        left, leftstmt = self.visit(node.left)
        right, rightstmt = self.visit(node.right)
        return (Register('eax'), leftstmt + rightstmt + [Movl(right, Register('eax')), Addl(left, Register('eax'))])

    def visit_UnarySub(self, node, *args, **kwargs):
        loc, stmtlist = self.visit(node.expr)
        return (Register('eax'), stmtlist + [Movl(loc, Register('eax')), Negl(Register('eax'))])

    def visit_CallFunc(self, node, *args, **kwargs):
        return (Register('eax'), [Call('print_int_nl')])

    def visit_Const(self, node, *args, **kwargs):
        return (Imm32(node.value), [])

    def visit_Name(self, node, *args, **kwargs):
        if not self.is_allocated(node.name):
            raise Exception("Attempt to access an undefined variable '%s'" % node.name)
        return (Var(node.name), [])


if __name__ == "__main__":
    import sys
    from p0parser import P0Parser
    from p0flattener import P0Flattener
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    for testcase in testcases:
        parser = P0Parser()
        parser.build()
        #ast = compiler.parseFile(testcase)
        ast = parser.parseFile(testcase)
        p0flattener = P0Flattener()
        stmtlist = p0flattener.flatten(ast)
        instruction_selector = P0InstructionSelector()
        program = instruction_selector.visit(stmtlist)
        print program
