# vim: set ts=4 sw=4 expandtab:
from compiler.ast import *
from comp_util import *
import logging

class P3ClassTransform(object):
    def __init__(self, classtmpvar, localassigns, freevars):
        self.classtmpvar = classtmpvar
        self.localassigns = localassigns
        self.freevars = freevars
        
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
        return Module(None, self.visit(node.node), None)

    def visit_Stmt(self, node):
        stmts = reduce(lambda x,y: x+y, [self.visit(x) for x in node.nodes], [])
        return Stmt(stmts,None)

    def visit_Printnl(self, node):
        return [Printnl([self.visit(node.nodes[0])], node.dest)]

    def visit_Assign(self, node):
        # check to see if this is a typical assignment
        if isinstance(node.nodes[0], AssName):
            # if this is an assignment to a local variable, convert it to an
            # assignment to a class attribute
            self.freevars = self.freevars - set([node.nodes[0].name])
            return [Assign([AssAttr(Name(self.classtmpvar), node.nodes[0].name, 'OP_ASSIGN')],node.expr)]
        elif isinstance(node.nodes[0], Subscript):
            sub = node.nodes[0]
            return [Assign([Subscript(self.visit(sub.expr), sub.flags, [self.visit(sub.subs[0])])],node.expr)]
        else:
            raise Exception('Need to handle this case: %s' % node.nodes[0])

    def visit_Discard(self, node):
        return [Discard(self.visit(node.expr))]

    def visit_Add(self, node):
        return Add((self.visit(node.left), self.visit(node.right)))

    def visit_UnarySub(self, node):
        return UnarySub(self.visit(node.expr))

    def visit_CallFunc(self, node):
        expressions = [self.visit(x) for x in node.args]
        # CallFunc should always return a pyobj.  This is the case for most of the
        # functions in runtime.c, but for 'input', this isn't the case.  
        # Instead, we need to call 'input_int' 
        if isinstance(node.node, Name) and node.node.name == 'input':
            node.node.name = 'input_int'
            return node
        return CallFuncIndirect(self.visit(node.node), expressions, None, node.lineno)

    def visit_Const(self, node):
        return node

    def visit_Name(self, node):
        if node.name in self.localassigns:
            # XXX: We need a way to figure out if this variable is available in the outside
            # scope as well.
            if node.name in self.freevars:
                return node
                #return IfExp(InjectFrom('int',CallFunc(Name('has_attr'),[Name(self.classtmpvar),Const(node.name)])), Getattr(Name(self.classtmpvar), node.name), Name(node.name))
            else:
                return Getattr(Name(self.classtmpvar), node.name)
        else:
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
        return [Return(self.visit(node.value))]

    def visit_Function(self, node):
        # Do not recurse into the function as we don't need to transform its contents.
        # Generate a new function name
        tmpname = '__' + node.name
        return [Function(node.decorators, tmpname, node.argnames, node.defaults, node.flags, node.doc, node.code),
                Assign([AssAttr(Name(self.classtmpvar), node.name, 'OP_ASSIGN')], Name(tmpname))]

    def visit_Lambda(self, node):
        # Do not recurse into the function as we don't need to transform its contents.
        return Lambda(node.argnames, node.defaults, node.flags, node.code)

    # P3
    # ================================================================================
    def visit_While(self, node):
        return [While(self.visit(node.test), self.visit(node.body), None)]

    def visit_If(self, node):
        tests = [self.visit(x[0]) for x in node.tests]
        thens = [self.visit(x[1]) for x in node.tests]
        return [If(zip(tests, thens), self.visit(node.else_))]

    # do not handle visit_Class, as all class definitions
    # should have been removed by declassify
    def visit_Class(self, node):
        raise Exception('All class definitions should have been removed by declassify!')

    def visit_Getattr(self, node):
        return Getattr(self.visit(node.expr), node.attrname)

    def visit_AssAttr(self, node):
        return AssAttr(self.visit(node.expr), node.attrname, node.flags)

