from compiler.ast import *
from comp_util import *
from x86ir import *
import logging

from p2explicate import P2Explicate

class P3Explicate(P2Explicate):
    def __init__(self, varalloc, handleLambdas=True):
        P2Explicate.__init__(self, varalloc, handleLambdas)
            
    # XXX: Had to change this after we added a flatten phase before explication.
    # Because of this change, we have a tuple for the "test" attribute, instead of
    # an expression.   The first element of the tuple is the variable associated 
    # with the test, while the second element in the tuple is the Stmt node. 
    # Below, we maintain the tuple for the "test" attribute, but since we have to
    # inject some IfExp logic, we change the first element of the tuple to a Let
    # node.   The second element remains the same, but is the explicated version
    # of the Stmt node.
    def visit_While(self, node, *args, **kwargs):
        test0  = self.visit(node.test[0])
        test1  = self.visit(node.test[1])
        self.log.info('visit_While: test0=%s' % test0)
        self.log.info('visit_While: test1=%s' % test1)
        body  = self.visit(node.body)
        var = Name(self.varalloc.get_next_var())
        # explicate the test so we can compare it to 0
        ifexp = IfExp(
                  isIntOrBoolExp(var), 
                  ProjectTo('bool',var),
                  ProjectTo('bool',CallFunc(Name('is_true'),[var]))
                )
        return  While((Let(var, test0, ifexp),test1), body, [], node.lineno)

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
        # explicate the arguments
        args = [self.visit(x) for x in node.args]
        # CallFunc should always return a pyobj.  This is the case for most of the
        # functions in runtime.c, but for 'input', this isn't the case.  
        # Instead, we need to call 'input_int' 
        if isinstance(node.node, Name) and node.node.name == 'input':
            node.node.name = 'input_int'
            return CallFunc(node.node, node.args, None, node.lineno)

        # explicate the node
        node = self.visit(node.node)
        # variable corresponding to node expression
        nodevar = Name(self.varalloc.get_next_var())

        # need to create variables for each of the arguments, and encapsulate each
        # argument in a Let() statement
        ret = Let(nodevar, node, None)
        let = ret
        argvars=[]
        for i in range(0,len(args)):
            argvars.append(Name(self.varalloc.get_next_var()))
            let.body = Let(argvars[i], args[i], None)
            let = let.body

        # variable corresponding to the returned object
        objvar = Name(self.varalloc.get_next_var())
        # variable corresponding to __init__ constructor, if it exists
        initvar = Name(self.varalloc.get_next_var())
        # dummy, to allow __init__ constructor to be called, but objvar to be returned
        dummyvar = Name(self.varalloc.get_next_var())

        ifexp = IfExp(
                  CallFunc(Name('is_class'),[nodevar]),
                  Let(
                    objvar,
                    InjectFrom('big',CallFunc(Name('create_object'),[nodevar])),
                    IfExp(
                      CallFunc(Name('has_attr'),[nodevar,Const('__init__')]),
                      Let(
                        initvar,
                        InjectFrom('big',CallFunc(Name('get_function'),[CallFunc(Name('get_attr'),[nodevar,Const('__init__')])])),
                        Let(
                          dummyvar,
                          CallFuncIndirect(initvar, [objvar] + argvars),
                          objvar
                        ),
                      ),
                      objvar
                    )
                  ),
                  IfExp(
                    CallFunc(Name('is_bound_method'),[nodevar]),
                    CallFuncIndirect(InjectFrom('big',CallFunc(Name('get_function'),[nodevar])), [InjectFrom('big',CallFunc(Name('get_receiver'),[nodevar]))]+argvars),
                    IfExp(
                      CallFunc(Name('is_unbound_method'),[nodevar]),
                      CallFuncIndirect(InjectFrom('big',CallFunc(Name('get_function'),[nodevar])), argvars),
                      CallFuncIndirect(nodevar, argvars)
                    )
                  )
                )
        let.body = ifexp
        return ret

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

    def visit_Getattr(self, node):
        # explicate the expression
        expr = self.visit(node.expr)
        return CallFunc(Name('get_attr'),[expr, Const(node.attrname)])

    # overridden from p1explicate
    def visit_Assign(self, node):
        if isinstance(node.nodes[0], AssAttr):
            # explicate the expression on the assign
            expr = self.visit(node.expr)
            # explicate the expression on assignment attribute
            attrexpr = self.visit(node.nodes[0].expr)
            return Discard(CallFunc(Name('set_attr'),[attrexpr, Const(node.nodes[0].attrname), expr]))
        else:
            return P2Explicate.visit_Assign(self, node)

if __name__ == "__main__":
    import sys, compiler
    import logging.config
    from p3declassify import P3Declassify
    from p3wrapper import P3Wrapper
    from p3uniquifyvars import P3UniquifyVars
    from gcflattener import GCFlattener
    from gcrefcount import GCRefCount
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        varalloc = VariableAllocator()
        declassify = P3Declassify(varalloc)
        wrapper = P3Wrapper()
        gcflatten = GCFlattener(varalloc)
        uniquify  = P3UniquifyVars()
        explicator = P3Explicate(varalloc, handleLambdas=False)
        gcrefcount = GCRefCount(varalloc)
        ast = compiler.parseFile(testcase)
        ast = declassify.transform(ast)
        ast = wrapper.transform(ast)
        ast = uniquify.transform(ast)
        ast = gcflatten.transform(ast)
        ast = gcrefcount.transform(ast)         
        print prettyAST(explicator.transform(ast))
