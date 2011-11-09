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
        var = Name(self.varalloc.get_next_var())
        # explicate the test so we can compare it to 0
        return  While(Let(var, test, Compare(ProjectTo('int',CallFunc(Name('is_true'),[var])), [('!=',Const(0))])),body, [], node.lineno)

    def visit_If(self, node, *args, **kwargs):
        if len(node.tests) > 1:
            raise Exception('P3 does not support more than one test/then')
        test  = self.visit(node.tests[0][0])
        then  = self.visit(node.tests[0][1])
        else_ = self.visit(node.else_)
        testvar = Name(self.varalloc.get_next_var())
        ifexp = IfExp(
                  isIntOrBoolExp(testvar),
                  IfExp(ProjectTo('bool',testvar), then, else_),
                  IfExp(ProjectTo('bool',CallFunc(Name('is_true'),[testvar])), then, else_)
                )
        return If(zip(tests, thens), self.visit(node.else_))


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
