from compiler.ast import *
from comp_util import *
from x86ir import *
import logging

from p2explicate import P2Explicate

class P3Explicate(P2Explicate):
    def __init__(self, varalloc, handleLambdas=True):
        P2Explicate.__init__(self, varalloc)
            
    def visit_While(self, node, *args, **kwargs):
        test  = self.visit(node.test)
        body  = self.visit(node.body)
        var = Name(self.varalloc.get_next_var())
        # explicate the test so we can compare it to 0
        ifexp = IfExp(
                  isIntOrBoolExp(var), 
                  ProjectTo('bool',var),
                  ProjectTo('bool',CallFunc(Name('is_true'),[var]))
                )
        return  While(Let(var, test, ifexp), body, [], node.lineno)

    def visit_If(self, node, *args, **kwargs):
        if len(node.tests) > 1:
            raise Exception('P3 does not support more than one test/then')
        test  = self.visit(node.tests[0][0])
        then  = self.visit(node.tests[0][1])
        else_ = self.visit(node.else_)
        testvar = Name(self.varalloc.get_next_var())
        ifexp = IfExp(
                  isIntOrBoolExp(testvar), 
                  ProjectTo('bool',testvar),
                  ProjectTo('bool',CallFunc(Name('is_true'),[testvar]))
                )
        return If([(Let(testvar, test, ifexp),then)],else_)

    # override visit_Const to handle string constants (don't need inject)
    def visit_Const(self, node):
        if isinstance(node.value,str):
            return node
        else:
            return InjectFrom('int', node)    

    # New for p3
    def visit_CallFuncIndirect(self, node):
        elsecase = P2Explicate.visit_CallFunc(self, node)
        var1 = Name(self.varalloc.get_next_var())
        var2 = Name(self.varalloc.get_next_var())
        ifexp = Let(
                  var1,
                  self.visit(node.node),
                  IfExp(
                    CallFunc(Name('is_class'),[var1]),
                    Let(
                      var2,
                      CallFunc(Name('create_object'),[var1]),
                      var2
                    ),
                    elsecase
                  )
                )
        return ifexp
               

    def visit_CallFunc(self, node):
        expressions = [self.visit(x) for x in node.args]
        # CallFunc should always return a pyobj.  This is the case for most of the
        # functions in runtime.c, but for 'input', this isn't the case.  
        # Instead, we need to call 'input_int' 
        if isinstance(node.node, Name) and node.node.name == 'input':
            node.node.name = 'input_int'
        return CallFunc(node.node, expressions, None, node.lineno)

    # We use InjectFrom in declassify, so we need to handle it in explicate now
    def visit_InjectFrom(self, node):
        return InjectFrom(node.typ, self.visit(node.arg))


if __name__ == "__main__":
    import sys, compiler
    import logging.config
    from p3declassify import P3Declassify
    from p3uniquifyvars import P3UniquifyVars
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        ast = compiler.parseFile(testcase)
        varalloc = VariableAllocator()
        declassify = P3Declassify(varalloc)
        ast = declassify.transform(ast)
        uniquify  = P3UniquifyVars()
        ast = uniquify.transform(ast)        
        explicator = P3Explicate(VariableAllocator())
        print prettyAST(explicator.transform(ast))
