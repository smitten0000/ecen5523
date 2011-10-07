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

intTag = Const(0)
boolTag = Const(1)
bigTag = Const(3)

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

    def visit_InjectFrom(self, node):
        return InjectFrom(node.typ, self.visit(node.arg))

    def visit_ProjectTo(self, node):
        return ProjectTo(node.typ, self.visit(node.arg))

    def visit_List(self, node):
        # the size of the list has to be known at creation time
        # this should be the same as the number of nodes in the List AST node
        pyobj_list = self.visit(InjectFrom('big',CallFunc(Name('create_list'),[Const(len(node.nodes))])))
        # allocate a temp var 
        varname = Name(self.varalloc.get_next_var())
        # we are going to create a tree of Let nodes to create a single expression
        # that executes all needed statements and returns the list
        # here is where we assign that return value.  In the case where we have
        # zero arguments, just return pyobj_list itself
        ret = Let(varname, pyobj_list, None)
        let = ret
        # for each expression, we have to assign it to the next consecutive index
        for i in range(0,len(node.nodes)):
            tmp = Name(self.varalloc.get_next_var())
            expr = self.visit(CallFunc(Name('set_subscript'),[varname, Const(i), node.nodes[i]]))
            let.body = Let(tmp, expr, None)
            let = let.body
        # We need a final reference to the variable corresponding to the list
        let.body = varname
        # Use Let to return an expression that results in a pyobj
        return ret
    def visit_Name(self, node):
        if node.name=='True' or node.name == 'False':
            return ProjectTo('bool', node)
        return node
    # All operands in p0 are expected to be pyobj
    # therefore, we have to convert Const -> pyobj
    def visit_Const(self, node):
        return InjectFrom('int', node)

    def visit_Printnl(self, node):
        return Printnl([self.visit(node.nodes[0])], node.dest)

    def visit_CallFunc(self, node):
        expressions = [self.visit(x) for x in node.args]
        # CallFunc should always return a pyobj.  This is the case for most of the
        # functions in runtime.c, but for 'input', this isn't the case.  
        # Instead, we need to call 'input_int' 
        if node.node.name == 'input':
            node.node.name = 'input_int'
        return CallFunc(node.node, expressions, None, None)

    def visit_UnarySub(self, node):
        return InjectFrom('int',UnarySub(ProjectTo('int',self.visit(node.expr))))

    def visit_Assign(self, node):
        # remember to mark this variable as allocated
        self.varalloc.add_var(node.nodes[0].name)
        return Assign(node.nodes, self.visit(node.expr))
    def visit_Not(self, node):
        expr1 = self.explicate(node.expr)
        var = Name(self.varalloc.get_next_var())
        return Let(var, expr1, ProjectTo('bool', var))

    def visit_And(self, node):
        if debug:
            print node
        expr1 = self.explicate(node.nodes[0])
        expr2 = self.explicate(node.nodes[1])
        if debug:
            print expr1
            print expr2
        # allocate new temporaries to hold the result of the subexpression
        leftvar = Name(self.varalloc.get_next_var())
        rightvar = Name(self.varalloc.get_next_var())
        
        compareTag = lambda x,y: Compare(GetTag(x),[('==',y)])
        isIntOrBoolExp = lambda x: Or([compareTag(x,intTag),compareTag(x,boolTag)])
        ifexp = IfExp(
                      And([isIntOrBoolExp(leftvar), isIntOrBoolExp(rightvar)]),
                        IfExp(Compare(ProjectTo('bool',leftvar), [('==',ProjectTo('bool',Name('False')))]), leftvar, rightvar),
                        IfExp(Compare(ProjectTo('bool',CallFunc(Name('is_true'),[leftvar])), [('==',Name('False'))])   , leftvar, rightvar)
                      )
        # Return a "Let" expression, which tells the flattener to flatten and
        # evaluate the RHS (2nd arg), assign it to the given variable (1st arg),
        # and then flatten and evaluate the body
        return Let(leftvar, expr1,
                   Let(rightvar, expr2, ifexp))

    def visit_Or(self, node):
        if debug:
            print node
        expr1 = self.explicate(node.nodes[0])
        expr2 = self.explicate(node.nodes[1])
        if debug:
            print expr1
            print expr2
        # allocate new temporaries to hold the result of the subexpression
        leftvar = Name(self.varalloc.get_next_var())
        rightvar = Name(self.varalloc.get_next_var())
        
        compareTag = lambda x,y: Compare(GetTag(x),[('==',y)])
        isIntOrBoolExp = lambda x: Or([compareTag(x,intTag),compareTag(x,boolTag)])
        ifexp = IfExp(
                      And([isIntOrBoolExp(leftvar), isIntOrBoolExp(rightvar)]),
                        IfExp(Compare(ProjectTo('bool',leftvar), [('==',ProjectTo('bool',Name('False')))]), rightvar, leftvar),
                        IfExp(Compare(ProjectTo('bool',CallFunc(Name('is_true'),[leftvar])), [('==',Name('False'))])   , rightvar, leftvar)
                      )
        # Return a "Let" expression, which tells the flattener to flatten and
        # evaluate the RHS (2nd arg), assign it to the given variable (1st arg),
        # and then flatten and evaluate the body
        return Let(leftvar, expr1,
                   Let(rightvar, expr2, ifexp))

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
                    CallFunc(Name('exit'),[])
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
