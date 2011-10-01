# vim: set ts=4 sw=4 expandtab:

from comp_util import *
from x86ir import *

class GetTag(Node):
    def __init__(self, arg):
        self.arg = arg
class InjectFrom(Node):
    def __init__(self, typ, arg):
        self.typ = typ
        self.arg = arg
class ProjectTo(Node):
    def __init__(self, typ, arg):
        self.typ = typ
        self.arg = arg
class Let(Node):
    def __init__(self, var, rhs, body):
        self.var = var
        self.rhs = rhs
        self.body = body


# Concept borrowed from http://peter-hoffmann.com/2010/extrinsic-visitor-pattern-python-inheritance.html
class P1Explicate(object):
    def __init__(self, varalloc):
        self.varalloc = varalloc

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
        if not self.varalloc.is_allocated(assname.name):
            raise Exception('Attempt to assign to previously unseen variable: %s' % assname.name)
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
        # need to create a temporary variable here to store the result.
        varname = self.varalloc.get_next_var()
        return (Var(varname), leftstmt + rightstmt + [Movl(right, Var(varname)), Addl(left, Var(varname))])

    def visit_UnarySub(self, node, *args, **kwargs):
        loc, stmtlist = self.visit(node.expr)
        # need to create a temporary variable here to store the result.
        varname = self.varalloc.get_next_var()
        tmpvar = Var(varname)
        return (tmpvar, stmtlist + [Movl(loc, tmpvar), Negl(tmpvar)])

    def visit_CallFunc(self, node, *args, **kwargs):
        # need to create a temporary variable here to store the result.
        varname = self.varalloc.get_next_var()
        return (Var(varname), [Call('input'), Movl(Register('eax'),Var(varname))])

    def visit_Const(self, node, *args, **kwargs):
        return (Imm32(node.value), [])

    def visit_Name(self, node, *args, **kwargs):
        if not self.varalloc.is_allocated(node.name):
            raise Exception("Attempt to access an undefined variable '%s'" % node.name)
        return (Var(node.name), [])


if __name__ == "__main__":
    import sys
    from p0parser import P0Parser
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    for testcase in testcases:
        parser = P0Parser()
        parser.build()
        #ast = compiler.parseFile(testcase)
        ast = parser.parseFile(testcase)
        varalloc = VariableAllocator()
        explc = P1Explicate()
        
        print explc.visit(ast) 
