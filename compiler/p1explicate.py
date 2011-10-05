# vim: set ts=4 sw=4 expandtab:

debug = False # set to True when module is this

from compiler.ast import *
from comp_util import *
from x86ir import *

class GetTag(Node):
    def __init__(self, arg):
        self.arg = arg
    def __str__(self):
        return 'GetTag(%s)' % self.arg
    def __repr__(self):
        return self.__str__()
    def getChildren(self):
        return [self.arg]

class InjectFrom(Node):
    def __init__(self, typ, arg):
        self.typ = typ
        self.arg = arg
    def __str__(self):
        return "InjectFrom('%s',%s)" % (self.typ, self.arg)
    def __repr__(self):
        return self.__str__()
    def getChildren(self):
        return [self.typ, self.arg]

class ProjectTo(Node):
    def __init__(self, typ, arg):
        self.typ = typ
        self.arg = arg
    def __str__(self):
        return "ProjectTo('%s',%s)" % (self.typ, self.arg)
    def __repr__(self):
        return self.__str__()
    def getChildren(self):
        return [self.typ, self.arg]

class Let(Node):
    def __init__(self, var, rhs, body):
        self.var = var
        self.rhs = rhs
        self.body = body
    def __str__(self):
        return "Let('%s',%s,%s)" % (self.var, self.rhs, self.body)
    def __repr__(self):
        return self.__str__()
    def getChildren(self):
        return [self.var, self.rhs, self.body]


# Concept borrowed from http://peter-hoffmann.com/2010/extrinsic-visitor-pattern-python-inheritance.html
class P1Explicate(object):
    def __init__(self, varalloc):
        self.varalloc = varalloc

    def explicate(self, node):
        return self.visit(node)

    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        # we return the node passed in by default so we do not have to handle
        # every case unless necessary
        if not meth:
            return node
        return meth(node, *args, **kwargs)

    def visit_Module(self, node):
        return Module(None, self.visit(node.node), None)

    def visit_Stmt(self, node):
        return Stmt([self.visit(x) for x in node.nodes], None)

    def visit_Discard(self, node):
        return Discard(self.visit(node.expr))

    # All operands in p0 are expected to be pyobj
    # therefore, we have to convert Const -> pyobj
    def visit_Const(self, node):
        return InjectFrom('int', node)

    def visit_And(self, node):
        if debug:
            print node
        expr1 = self.explicate(node.left)
        expr2 = self.explicate(node.right)
        if debug:
            print expr1
            print expr2
        # allocate new temporaries to hold the result of the subexpression
        leftvar = Name(self.varalloc.get_next_var())
        rightvar = Name(self.varalloc.get_next_var())
        # Below, we create an AST tree that represents the logic executed at run-time 
        # to describe the behavior of the Add operation (e.g., check the type
        # of a variable and either perform an integer Add, or call the runtime
        # to perform list concatenation, or error...)
        # some variables to help make the code more readable when referring to tags
        intTag = Const(0)
        boolTag = Const(1)
        bigTag = Const(3)
        # helper functions to help generate the AST
        compareTag = lambda x,y: Compare(GetTag(x),[('==',y)])
        isIntOrBoolExp = lambda x: Or([compareTag(x,intTag),compareTag(x,boolTag)])
        # Here is the "runtime" logic for doing an Add in P1.
        ifexp = IfExp(
                  # no need to explicate this And, because the operands should always booleans
                  And([isIntOrBoolExp(leftvar),isIntOrBoolExp(rightvar)]),
                  InjectFrom('int',Add((ProjectTo('int',leftvar),ProjectTo('int',rightvar)))),
                  IfExp(
                    # ditto for this And
                    And([compareTag(leftvar,bigTag),compareTag(rightvar,bigTag)]),
                    InjectFrom('big',Add((ProjectTo('big',leftvar),ProjectTo('big',rightvar)))),
                    CallFunc('exit',[])
                  )
                )
        # Return a "Let" expression, which tells the flattener to flatten and
        # evaluate the RHS (2nd arg), assign it to the given variable (1st arg),
        # and then flatten and evaluate the body
        return Let(leftvar, expr1,
                   Let(rightvar, expr2, ifexp))

    def visit_Or(self, node):
        raise NotImplementedError('TODO: Implement me!')

    def visit_Add(self, node):
        if debug:
            print node
        expr1 = self.explicate(node.left)
        expr2 = self.explicate(node.right)
        if debug:
            print expr1
            print expr2
        # allocate new temporaries to hold the result of the subexpression
        leftvar = Name(self.varalloc.get_next_var())
        rightvar = Name(self.varalloc.get_next_var())
        # Below, we create an AST tree that represents the logic executed at run-time 
        # to describe the behavior of the Add operation (e.g., check the type
        # of a variable and either perform an integer Add, or call the runtime
        # to perform list concatenation, or error...)
        # some variables to help make the code more readable when referring to tags
        intTag = Const(0)
        boolTag = Const(1)
        bigTag = Const(3)
        # helper functions to help generate the AST
        compareTag = lambda x,y: Compare(GetTag(x),[('==',y)])
        isIntOrBoolExp = lambda x: Or([compareTag(x,intTag),compareTag(x,boolTag)])
        # Here is the "runtime" logic for doing an Add in P1.
        ifexp = IfExp(
                  # no need to explicate this And, because the operands should always booleans
                  And([isIntOrBoolExp(leftvar),isIntOrBoolExp(rightvar)]),
                  InjectFrom('int',Add((ProjectTo('int',leftvar),ProjectTo('int',rightvar)))),
                  IfExp(
                    # ditto for this And
                    And([compareTag(leftvar,bigTag),compareTag(rightvar,bigTag)]),
                    InjectFrom('big',Add((ProjectTo('big',leftvar),ProjectTo('big',rightvar)))),
                    CallFunc('exit',[])
                  )
                )
        # Return a "Let" expression, which tells the flattener to flatten and
        # evaluate the RHS (2nd arg), assign it to the given variable (1st arg),
        # and then flatten and evaluate the body
        return Let(leftvar, expr1,
                   Let(rightvar, expr2, ifexp))


if __name__ == "__main__":
    import sys, compiler
    from p0parser import P0Parser
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    debug = True
    for testcase in testcases:
        #parser = P0Parser()
        #parser.build()
        ast = compiler.parseFile(testcase)
        #ast = parser.parseFile(testcase)
        p1explicator = P1Explicate(VariableAllocator())
        print prettyAST(p1explicator.explicate(ast))
