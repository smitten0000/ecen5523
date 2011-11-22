# vim: set ts=4 sw=4 expandtab:
from compiler.ast import *
from comp_util import *
import logging

class P3Wrapper:
    def __init__(self):
        self.log = logging.getLogger('compiler.wrapper')

    def transform(self, node):
        self.log.info ('Starting wrapper')
        ret = self.visit(node)
        self.log.info ('Finished wrapper')
        return ret

    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        # we cannot blindly return the node itself, if there is no visit 
        # function for that type.  This is because the children of that node may need
        # to be recursed upon: ex.  Printnl(CallFuncIndirect(...))
        if not meth:
            raise Exception('Unknown node: %s method: %s' % (node.__class__, meth_name))
        return meth(node, *args, **kwargs)

    # P0
    # ================================================================================
    def visit_Module(self, node):
        stmt = self.visit(node.node)
        prestmt = [Discard(CallFunc(Name('pymem_init'), []))]
        poststmt = [Discard(CallFunc(Name('pymem_print_stats'), [])), 
                    Discard(CallFunc(Name('pymem_shutdown'), []))]
        stmt.nodes = prestmt + stmt.nodes + poststmt
        return Module(None, stmt, None)

    def visit_Stmt(self, node):
        return Stmt([self.visit(x) for x in node.nodes],None)

    def visit_Printnl(self, node):
        return Printnl([self.visit(node.nodes[0])], node.dest)

    def visit_Assign(self, node):
        return Assign([self.visit(node.nodes[0])], self.visit(node.expr))

    def visit_Discard(self, node):
        return Discard(self.visit(node.expr))

    def visit_Add(self, node):
        return Add((self.visit(node.left), self.visit(node.right)))

    def visit_UnarySub(self, node):
        return UnarySub(self.visit(node.expr))

    def visit_CallFunc(self, node):
        expressions = [self.visit(x) for x in node.args]
        return CallFunc(self.visit(node.node), expressions, None, node.lineno)

    def visit_CallFuncIndirect(self, node):
        expressions = [self.visit(x) for x in node.args]
        return CallFuncIndirect(self.visit(node.node), expressions, None, node.lineno)

    def visit_Const(self, node):
        return node

    def visit_Name(self, node):
        return node

    def visit_AssName(self, node):
        return node

    # P1
    # ================================================================================
    def visit_Or(self, node):
        return Or([self.visit(node.nodes[0]), self.visit(node.nodes[1])])

    def visit_And(self, node):
        return And([self.visit(node.nodes[0]), self.visit(node.nodes[1])])

    def visit_IfExp(self, node):
        return IfExp(self.visit(node.test), self.visit(node.then), self.visit(node.else_))

    def visit_List(self, node):
        args = [self.visit(x) for x in node.nodes]
        return List(args)

    def visit_Dict(self, node):
        keys = [self.visit(x[0]) for x in node.items]
        values = [self.visit(x[1]) for x in node.items]
        items = map(lambda x: (keys[x],values[x]), range(0,len(keys)))
        return Dict(items)

    def visit_Compare(self, node):
        ops = [(node.ops[0][0], self.visit(node.ops[0][1]))]
        return Compare(self.visit(node.expr), ops)

    def visit_Not(self, node):
        return Not(self.visit(node.expr))

    def visit_Subscript(self, node):
        subs = [self.visit(node.subs[0])]
        return Subscript(self.visit(node.expr), node.flags, subs)

    # P2
    # ================================================================================
    def visit_Return(self, node):
        return Return(self.visit(node.value))

    def visit_Function(self, node):
        code = self.visit(node.code)
        return Function(node.decorators, node.name, node.argnames, node.defaults, node.flags, node.doc, code)

    def visit_Lambda(self, node):
        return Lambda(node.argnames, node.defaults, node.flags, code)

    # P3
    # ================================================================================
    def visit_While(self, node):
        return [While(self.visit(node.test), self.visit(node.body), None)]

    def visit_If(self, node):
        tests = [self.visit(x[0]) for x in node.tests]
        thens = [self.visit(x[1]) for x in node.tests]
        return If(zip(tests, thens), self.visit(node.else_))

    # We use InjectFrom in declassify, so we need to handle it in explicate now
    def visit_InjectFrom(self, node):
        return InjectFrom(node.typ, self.visit(node.arg))

    def visit_Getattr(self, node):
        return Getattr(self.visit(node.expr), node.attrname)

    def visit_AssAttr(self, node):
        return AssAttr(self.visit(node.expr), node.attrname, node.flags)


if __name__ == "__main__":
    import sys, compiler
    import logging.config
    from p3declassify import P3Declassify
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        varalloc = VariableAllocator()
        declassify = P3Declassify(varalloc)
        wrapper = P3Wrapper()
        ast = compiler.parseFile(testcase)
        ast = declassify.transform(ast)
        ast = wrapper.transform(ast)
        print ast
        print prettyAST(ast)
