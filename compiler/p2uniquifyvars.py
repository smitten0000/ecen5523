from compiler.ast import *
from comp_util import *
from x86ir import *

class P2UniquifyVars:
    def __init__(self):
        self.vardict = {}

    def getNext(self, varname):
        if varname not in self.vardict:
            self.vardict[varname] = 0
        else:
            self.vardict[varname] = self.vardict[varname] + 1
        return varname + '/' + str(self.vardict[varname])

    def getCurrent(self, varname):
        if varname not in self.vardict:
            raise Exception("Reference to undefined variable: '%s'" % varname)
        return varname + '/' + str(self.vardict[varname])

    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        if not meth:
            raise Exception('Unknown node: %s method: %s' % (node.__class__, meth))
        return meth(node, *args, **kwargs)

    def visit_Module(self, node):
        return Module(None, self.visit(node.node), None)

    def visit_Stmt(self, node):
        # first pass, just change local assignments and references
        ast = Stmt([self.visit(x,True) for x in node.nodes], None)
        # second pass, move on to lambdas and functions
        return Stmt([self.visit(x,False) for x in ast.nodes],None)

    def visit_Printnl(self, node, local):
        return Printnl([self.visit(node.nodes[0], local)], node.dest)

    def visit_Assign(self, node, local):
        return Assign([self.visit(node.nodes[0], local)], self.visit(node.expr, local))

    def visit_Discard(self, node, local):
        return Discard(self.visit(node.expr, local))

    def visit_Add(self, node, local):
        return Add((self.visit(node.left, local), self.visit(node.right, local)))

    def visit_UnarySub(self, node, local):
        return UnarySub(self.visit(node.expr, local))

    def visit_CallFunc(self, node, local):
        args = [self.visit(x, local) for x in node.args]
        return CallFunc(self.visit(node.node,local), args) 

    def visit_Or(self, node, local):
        return Or([self.visit(node.nodes[0], local), self.visit(node.nodes[1], local)])

    def visit_And(self, node, local):
        return And([self.visit(node.nodes[0], local), self.visit(node.nodes[1], local)])

    def visit_IfExp(self, node, local):
        return IfExp(self.visit(node.test, local), self.visit(node.then, local), self.visit(node.else_, local))

    def visit_List(self, node, local):
        args = [self.visit(x, local) for x in node.nodes]
        return List(args)

    def visit_Dict(self, node, local):
        keys = [self.visit(x[0], local) for x in node.items]
        values = [self.visit(x[1], local) for x in node.items]
        items = map(lambda x: (keys[x],values[x]), range(0,len(keys)))
        return Dict(items)

    def visit_Compare(self, node, local):
        ops = [(node.ops[0][0], self.visit(node.ops[0][1], local))]
        return Compare(self.visit(node.expr, local), ops)

    def visit_Not(self, node, local):
        return Not(self.visit(node.expr, local))

    def visit_Subscript(self, node, local):
        subs = [self.visit(node.subs[0], local)]
        return Subscript(self.visit(node.expr, local), node.flags, subs)

    def visit_Return(self, node, local):
        return Return(self.visit(node.value, local))

    def visit_Function(self, node, local):
        if local: 
            # if we are on the local pass, uniquify the function name and leave
            # everything else alone.
            funcname = self.getNext(node.name)
            return Function(node.decorators, funcname, node.argnames, node.defaults, node.flags, node.doc, node.code)
        else:
            # uniquify the args
            args = [self.getNext(x) for x in node.argnames]
            # code is a Stmt; so this performs local assignments first, then handles any nested functions/lambdas
            code = self.visit(node.code)
            # all done
            return Function(node.decorators, node.name, args, node.defaults, node.flags, node.doc, code)

    def visit_Lambda(self, node, local):
        if local: 
            # if we are on the local pass, leave the Lambda node alone
            return node
        else:
            # uniquify the args
            args = [self.getNext(x) for x in node.argnames]
            # code is an expression
            code = self.visit(node.code, True)
            # all done
            return Lambda(args, node.defaults, node.flags, code)

    def visit_Const(self, node, local):
        return node

    def visit_Name(self, node, local):
        if not local:
            return node
        if node.name == 'True' or node.name == 'False':
            return node
        newname = self.getCurrent(node.name)
        return Name(newname)

    def visit_AssName(self, node, local):
        if not local:
            return node
        newname = self.getNext(node.name)
        return AssName(newname, node.flags)


if __name__ == "__main__":
    import sys, compiler
    from comp_util import *
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    debug = True
    for testcase in testcases:
        ast = compiler.parseFile(testcase)
        uniquify = P2UniquifyVars()
        ast = uniquify.visit(ast)
        print ast
        print prettyAST(ast)
