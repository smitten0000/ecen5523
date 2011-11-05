from compiler.ast import *
from comp_util import *
from x86ir import *
import logging

from p3uniquifyvars import P3UniquifyVars
from p2explicate import P2Explicate


class P3Explicate(P2Explicate):
    def __init__(self, varalloc, handleLambdas=True):
        P2Explicate.__init__(self, varalloc)
            

    def visit_While(self, node, *args, **kwargs):
        test  = self.visit(node.test)
        body  = self.visit(node.body)
        testvar = Name(self.varalloc.get_next_var())
        exp = While(CallFunc(Name('is_true'),[testvar]), body, [], node.lineno) 
#        ifexp = IfExp(isIntOrBoolExp(testvar),
#                      IfExp(Compare(ProjectTo('int',testvar), [('==',Const(0))]), 
#                            else_,
#                            then
#                           ),
#                      IfExp(Compare(ProjectTo('int',CallFunc(Name('is_true'),[testvar])), [('==',InjectFrom('int',Const(0)))]),
#                            else_,
#                            then
#                           )
#                     )
        return Let(testvar, test, exp)

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
        p3unique = P3UniquifyVars()
        unique = p3unique.transform(ast)        
        p3explicator = P3Explicate(VariableAllocator())
        print prettyAST(p3explicator.transform(unique))
