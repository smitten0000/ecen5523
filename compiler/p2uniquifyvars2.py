
class P2UniquifyVars:
    def __init__(self):
        self.vardict = {}
        self.varcounter = {}

    def getLocalAssigns(self, n):
        """
        Returns the set of variables that are assigned to within the current scope,
        ignoring assignments in nested scopes (functions).
        """
        if isinstance(n, Module):
            return self.getLocalAssigns(n.node)
        elif isinstance(n, Stmt):
            assigns = [self.getLocalAssigns(x) for x in n.nodes]
            return reduce(lambda x,y: x|y, assigns, set([]))
        elif isinstance(n, Printnl):
            return set([])
        elif isinstance(n, Assign):
            if isinstance(n.nodes[0], Subscript):
                # assigning to a subscript of a variable does not constitute
                # assigning to the variable itself.  Return empty set.
                return set([])
            elif isinstance(n.nodes[0], AssName):
                return set([n.nodes[0].name])
            else:
                raise Exception('Unhandled Assign case: %s' % n.nodes[0])
        elif isinstance(n, Discard):
            # there shouldn't ever be a case where there will be an assignment in a Discard
            # since a Discard is, by definition, a statement that produced no assignments
            return set([])
        elif isinstance(n, Return):
            return set([])
        elif isinstance(n, Function):
            # a function definition is equivalent to an assignment to a 
            # variable with the same name as the function
            # No need to recurse into the Function since the intent of the function
            # is to only find assigments for the local scope
            return set([n.name])
        elif isinstance(n, (Add,UnarySub,CallFunc,Const,Name,Or,And,IfExp,List,Dict,Compare,Not,Subscript,Lambda)):
            # these are all expressions, so no assignments
            return set([])
        else:
            raise Exception('Unhandled expression: "%s"' % n)


    def assignVar(self, varname):
        if varname not in self.vardict:
            self.vardict[varname] = []
            self.varcounter[varname] = 0
        ret = varname + '/' + str(self.varcounter[varname])
        self.varcounter[varname] = self.varcounter[varname] + 1
        self.vardict[varname].append(ret)
        return ret

    def popVars(self, varlist):
        for var in varlist:
            self.vardict[var].pop()

    def isAllocated(self, varname):
        return varname in self.vardict

    def getCurrent(self, varname):
        if varname not in self.vardict:
            raise Exception("Reference to undefined variable: '%s'" % varname)
        # return top of "stack", which is last element in list
        return self.vardict[varname][-1]

    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        if not meth:
            raise Exception('Unknown node: %s method: %s' % (node.__class__, meth))
        return meth(node, *args, **kwargs)

    def visit_Module(self, node):
        # figure out the set of variables that are assigned to in this scope.
        localvars = self.getLocalAssigns(node)
        # Create an assignment for each of these variables
        for var in localvars:
            self.assignVar(var)
        # Now go ahead and process the AST.
        return Module(None, self.visit(node.node), None)

    def visit_Stmt(self, node):
        return Stmt([self.visit(x) for x in node.nodes],None)

    def visit_Printnl(self, node):
        return Printnl([self.visit(node.nodes[0])], node.dest)

    def visit_Assign(self, node):
        return Assign([self.visit(node.nodes[0])], self.visit(node.expr))

    def visit_Discard(self, node):
        return Discard(self.visit(node.expr))

    def visit_Add(self, node):
        return Add((self.visit(node.left), self.visit(node.right)))

    def visit_UnarySub(self, node):
        return UnarySub(self.visit(node.expr))

    def visit_CallFunc(self, node):
        args = [self.visit(x) for x in node.args]
        return CallFunc(self.visit(node.node), args) 

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

    def visit_Return(self, node):
        return Return(self.visit(node.value))

    def visit_Function(self, node):
        # get function name
        # do this first since the function name is technically a variable that
        # is outside the scope of the function.  Otherwise, if there is a variable
        # in the statements of the function with the same name as the function,
        # the function name gets this value, which is incorrect.
        funcname = self.getCurrent(node.name)
        # figure out the set of variables that are assigned to in this scope.
        localvars = self.getLocalAssigns(node.code)
        # add the parameters to the Function to this set
        localvars = localvars | set(node.argnames)
        # Create an assignment for each of these variables
        for var in localvars:
            self.assignVar(var)
        # uniquify the parameters to the Function
        args = [self.getCurrent(x) for x in node.argnames]
        # Now go ahead and process the AST.
        code = self.visit(node.code)
        # pop all vars
        self.popVars(localvars)
        # all done
        return Function(node.decorators, funcname, args, node.defaults, node.flags, node.doc, code)

    def visit_Lambda(self, node):
        # figure out the set of variables that are assigned to in this scope.
        localvars = self.getLocalAssigns(node.code)
        # add the parameters to the Lambda to this set
        localvars = localvars | set(node.argnames)
        # Create an assignment for each of these variables
        for var in localvars:
            self.assignVar(var)
        # uniquify the parameters to the lambda
        args = [self.getCurrent(x) for x in node.argnames]
        # code is an expression
        code = self.visit(node.code)
        # pop all vars
        self.popVars(node.argnames)
        # all done
        return Lambda(args, node.defaults, node.flags, code)

    def visit_Const(self, node):
        return node

    def visit_Name(self, node):
        if node.name == 'True' or node.name == 'False':
            return node
        newname = self.getCurrent(node.name)
        return Name(newname)

    def visit_AssName(self, node):
        if not self.isAllocated(node.name):
            raise Exception("This shouldn't happen since we pre-allocate variables at the beginning of a Module/Function/Lambda node.")
        newname = self.getCurrent(node.name)
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