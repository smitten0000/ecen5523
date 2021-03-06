# vim: set ts=4 sw=4 expandtab:
from compiler.ast import *
from comp_util import *

import logging, logging.config

from p2uniquifyvars import P2UniquifyVars

class P3UniquifyVars(P2UniquifyVars):
    def __init__(self):
        P2UniquifyVars.__init__(self)

    def visit_While(self, node):
        return While(self.visit(node.test), self.visit(node.body), None, node.lineno)

    def visit_If(self, node):
        tests = [self.visit(x[0]) for x in node.tests]
        thens = [self.visit(x[1]) for x in node.tests]
        return If(zip(tests, thens), self.visit(node.else_))

    def visit_CallFunc(self, node):
        args = [self.visit(x) for x in node.args]
        return CallFunc(node.node, args) 

    def visit_CallFuncIndirect(self, node):
        args = [self.visit(x) for x in node.args]
        return CallFuncIndirect(self.visit(node.node), args) 

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
        ast = compiler.parseFile(testcase)
        varalloc = VariableAllocator()
        declassify = P3Declassify(varalloc)
        uniquify = P3UniquifyVars()
        ast = declassify.transform(ast)
        ast = uniquify.transform(ast)
        print ast
        print prettyAST(ast)
