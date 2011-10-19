from compiler.ast import *
from comp_util import *
from x86ir import *
import logging

from p2uniquifyvars import P2UniquifyVars
from p1explicate import P1Explicate


class P2Explicate(P1Explicate):
    def __init__(self, varalloc):
        P1Explicate.__init__(self, varalloc)
            
    def visit_Function(self, node, *args, **kwargs):
        #Function: decorators, name, argnames, defaults, flags, doc, code
        #Lamba: argnames, defaults, flags, code
        #Assign([AssName(retvar,'OP_ASSIGN')], CallFunc(Name('set_subscript'),[expr,subexpr,valueexpr]))
        return Assign([AssName(node.name, 'OP_ASSIGN')], Lambda(node.argnames, node.defaults, node.flags, self.visit(node.code), node.name))
    def visit_CallFunc(self, node, *args, **kwargs):
        p1expl = P1Explicate.visit_CallFunc(self, node, *args, **kwargs)
        # convert the remaining CallFuncs to indirect since they are from a def or a lambda
        if node.node.name == 'input':
            return p1expl
        #CallFunc and CallFuncIndirect: node, args, star_args = None, dstar_args = None, lineno=None
        # def f(x): x
        # a[0] = f
        # 4 + a[0](4)
    
        # all arguments should already be explicated at this point.
        return CallFuncIndirect(p1expl.node, p1expl.args, p1expl.star_args, p1expl.dstar_args, p1expl.lineno)
        
        
    def visit_Lambda(self, node, *args, **kwargs):
        #Lamba: argnames, defaults, flags, code
        return Lambda(node.argnames, node.defaults, node.flags, Return(self.visit(node.code)), 'lambda')


if __name__ == "__main__":
    import sys, compiler
    import logging.config
    from p0parser import P0Parser
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        #parser = P0Parser()
        #parser.build()
        ast = compiler.parseFile(testcase)
        #ast = parser.parseFile(testcase)
        p2unique = P2UniquifyVars()
        unique = p2unique.transform(ast)        
        p2explicator = P2Explicate(VariableAllocator())
        print prettyAST(p2explicator.transform(unique))
