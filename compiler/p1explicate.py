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

compareTag = lambda x,y: Compare(GetTag(x),[('==',y)])
isIntOrBoolExp = lambda x: Or([compareTag(x,intTag),compareTag(x,boolTag)])

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

    def visit_IfExp(self, node):
        test  = self.visit(node.test)
        then  = self.visit(node.then)
        else_ = self.visit(node.else_)
        testvar = Name(self.varalloc.get_next_var())
        thenvar = Name(self.varalloc.get_next_var())
        elsevar = Name(self.varalloc.get_next_var())
        ifexp = IfExp(
                  isIntOrBoolExp(testvar),
                  IfExp(testvar, thenvar, elsevar),
                  IfExp(ProjectTo('bool',CallFunc(Name('is_true'),[testvar])), thenvar, elsevar)
                )
        return Let(testvar, test,
                   Let(thenvar, then,
                       Let(elsevar, else_, ifexp)))
        
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

    def visit_Dict(self, node):
        pyobj_dict = self.visit(InjectFrom('big',CallFunc(Name('create_dict'),[])))
        # allocate a temp var 
        varname = Name(self.varalloc.get_next_var())
        # we are going to create a tree of Let nodes to create a single expression
        # that executes all needed statements and returns the dictionary
        ret = Let(varname, pyobj_dict, None)
        let = ret
        # for each expression, we have to assign it to the next consecutive index
        for key, value in node.items:
            tmp = Name(self.varalloc.get_next_var())
            expr = self.visit(CallFunc(Name('set_subscript'),[varname, key, value]))
            let.body = Let(tmp, expr, None)
            let = let.body
        # We need a final reference to the variable corresponding to the dictionary
        let.body = varname
        # Use Let to return an expression that results in a pyobj
        return ret

    def visit_Name(self, node):
        if node.name == 'True':
            return InjectFrom('bool', Const(1))
        elif node.name == 'False':
            return InjectFrom('bool', Const(0))
        return node
    # All operands in p0 are expected to be pyobj
    # therefore, we have to convert Const -> pyobj
    def visit_Const(self, node):
        return InjectFrom('int', node)    
    
    def visit_Compare(self, node):
        # != and == should operate on booleans, is should operate on pointer address or raw value
        lhs = self.explicate(node.expr)
        rhs = self.explicate(node.ops[0][1])
        leftvar = Name(self.varalloc.get_next_var())
        rightvar = Name(self.varalloc.get_next_var())
        if node.ops[0][0] in ('==','!='):
            bigBehavior = CallFunc(Name('equal'),[leftvar,rightvar])
        elif node.ops[0][0] in ('is'):
            bigBehavior = InjectFrom('bool',Compare(ProjectTo('big',leftvar), [('==', ProjectTo('big',rightvar))]))
        else:
            raise Exception("unknown operator '%s'" % node.ops[0][0])
        ifexp = IfExp(
                  And([isIntOrBoolExp(leftvar),isIntOrBoolExp(rightvar)]),
                  Compare(ProjectTo('int',leftvar), [(node.ops[0][0], ProjectTo('int',rightvar))]),
                  IfExp(
                    And([compareTag(leftvar,bigTag),compareTag(rightvar,bigTag)]),
                    bigBehavior,
                    CallFunc(Name('exit'),[])
                  )
                )
        return Let(leftvar, lhs, Let(rightvar, rhs, ifexp))
        
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
        # the node.nodes[0] attribute may contain a subscript, so we have to 
        # handle this case now.  We can't delegate to visit_Subscript, since that
        # will result in a call to get_subscript, which is not what is intended.
        # instead we a conditional below to determine what to do
        if isinstance(node.nodes[0], AssName):
            # "normal" behavior
            # remember to mark this variable as allocated
            self.varalloc.add_var(node.nodes[0].name)
            return Assign([node.nodes[0]], self.visit(node.expr))
        elif isinstance(node.nodes[0], Subscript):
            subscript = node.nodes[0]
            # make the expression that the subscript operates on explicit
            expr = self.visit(subscript.expr)
            # make the subscript explicit (only support one subscript)
            subexpr = self.visit(subscript.subs[0])
            # make the value explicit
            valueexpr = self.visit(node.expr)
            # generate a temporary for the assignment statement (even though its
            # not going to be used by anyone since x = y = 2 is invalid in p1)
            retvar = Name(self.varalloc.get_next_var())
            return Assign([AssName(retvar,'OP_ASSIGN')], CallFunc(Name('set_subscript'),[expr,subexpr,valueexpr]))
    def visit_Not(self, node):
        expr1 = self.explicate(node.expr)
        var = Name(self.varalloc.get_next_var())
        ifexp = IfExp(compareTag(var,boolTag),
                      IfExp(Compare(ProjectTo('int',var), [('==',Const(0))]), 
                            InjectFrom('bool',Const(1)), 
                            InjectFrom('bool',Const(0))
                           ),
                      IfExp(compareTag(var,intTag),
                            IfExp(Compare(ProjectTo('int',var), [('==',Const(0))]), 
                                  InjectFrom('bool',Const(1)), 
                                  InjectFrom('bool',Const(0))
                                 ),
                            IfExp(Compare(ProjectTo('int',CallFunc(Name('is_true'),[var])), [('==',InjectFrom('int',Const(0)))]),
                                  InjectFrom('bool',Const(1)),
                                  InjectFrom('bool',Const(0))
                                 )
                      )
                            
              )
        return Let(var, expr1, ifexp)

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

        ifexp = IfExp(
                  And([isIntOrBoolExp(leftvar), isIntOrBoolExp(rightvar)]),
                  IfExp(Compare(ProjectTo('int',leftvar), [('==',Const(0))]), leftvar, rightvar),
                  IfExp(Compare(ProjectTo('int',CallFunc(Name('is_true'),[leftvar])), [('==',Const(0))]), leftvar, rightvar)
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

        ifexp = IfExp(
                  And([isIntOrBoolExp(leftvar), isIntOrBoolExp(rightvar)]),
                  IfExp(Compare(ProjectTo('int',leftvar), [('==',InjectFrom('int',Const(0)))]), rightvar, leftvar),
                  IfExp(Compare(ProjectTo('int',CallFunc(Name('is_true'),[leftvar])), [('==',Const(0))]), rightvar, leftvar)
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

    def visit_Subscript(self, node):
        # make the expression that the subscript operates on explicit
        expr = self.visit(node.expr)
        # make the subscript explicit (only support one subscript)
        subexpr = self.visit(node.subs[0])
        # generate a temporary var to refer to the expression by
        exprvar = Name(self.varalloc.get_next_var())
        # generate a temporary var to refer to the subscript expression by
        subvar = Name(self.varalloc.get_next_var())
        # Call the get_subscript function from the runtime
        return Let(exprvar, expr, Let(subvar, subexpr, CallFunc(Name('get_subscript'),[exprvar,subvar]))) 



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
