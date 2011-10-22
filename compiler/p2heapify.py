from compiler.ast import *
from comp_util import *
from x86ir import *

from p2explicate import P2Explicate
from p2uniquifyvars import P2UniquifyVars
from p2freevars import P2FreeVars

import logging


class P2Heapify(object):
    def __init__(self, explicate):
        self.log = logging.getLogger('compiler.heapify')
        self.explicate = P2Explicate(explicate.varalloc,False)
        self.freevars = P2FreeVars()
        self.heapvarset = set([])

    def getLambdaFreeVars(self, n):
        if isinstance(n, Module):
            return self.getLambdaFreeVars(n.node)
        elif isinstance(n, Stmt):
            fvars = [self.getLambdaFreeVars(x) for x in n.nodes]
            return squash(fvars)
        elif isinstance(n, Printnl):
            return self.getLambdaFreeVars(n.nodes[0])
        elif isinstance(n, Assign):
            return self.getLambdaFreeVars(n.expr)
        elif isinstance(n, (Discard,UnarySub,Not)):
            return self.getLambdaFreeVars(n.expr)
        elif isinstance(n, Add):
            return self.getLambdaFreeVars(n.left) | self.getLambdaFreeVars(n.right)
        elif isinstance(n, IfExp):
            return self.getLambdaFreeVars(n.test) | self.getLambdaFreeVars(n.then) | self.getLambdaFreeVars(n.else_)
        elif isinstance(n, (And,Or)):
            fvars = [self.getLambdaFreeVars(x) for x in n.nodes]
            return squash(fvars)
        elif isinstance(n, CallFunc):
            fvars = [self.getLambdaFreeVars(x) for x in n.args]
            return squash(fvars)
        elif isinstance(n, CallFuncIndirect):
            fvars = [self.getLambdaFreeVars(x) for x in n.args]
            return squash(fvars) | self.getLambdaFreeVars(n.node)
        elif isinstance(n, Compare):
            return self.getLambdaFreeVars(n.expr) | self.getLambdaFreeVars(n.ops[0][1])
#        elif isinstance(n, Subscript):
#            return self.getLambdaFreeVars(n.expr) | self.getLambdaFreeVars(n.subs[0])
        elif isinstance(n, Return):
            return self.getLambdaFreeVars(n.value)
        elif isinstance(n, (Name,Const)):
            return set([])
        elif isinstance(n, Lambda):
            return n.free
        elif isinstance(n, (InjectFrom,ProjectTo,GetTag)):
            return self.getLambdaFreeVars(n.arg)
        elif isinstance(n, Let):
            return self.getLambdaFreeVars(n.rhs) | self.getLambdaFreeVars(n.body)
        else:
            raise Exception('Unhandled node: %s' % n)
        

    def transform(self, node):
        self.log.info('Starting heapify')
        # Do the freevars visitor on the whole tree. The ensures that
        # the free and bound attributes are set on all Lambdas.
        self.freevars.visit(node)
        ret = self.visit(node)
        self.log.info('Finished heapify')
        return ret
        
    def visit(self, node):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        # we cannot blindly return the node itself, if there is no visit 
        # function for that type.  This is because the children of that node may need
        # to be recursed upon: ex.  Printnl(CallFuncIndirect(...))
        self.log.debug('Visiting %s' % node.__class__)
        if not meth:
            raise Exception('Unknown node: %s method: %s' % (node.__class__, meth_name))
        return meth(node)

    def visit_Module(self, node):
        # Need to find the free variables on all immediate child Lambdas
        # These are the variables that need heapification
        vars_to_heapify = self.getLambdaFreeVars(node)
        self.heapvarset = self.heapvarset | vars_to_heapify
        self.log.debug('visit_Module: Variables to Heapify: %s', vars_to_heapify)
        heaplist = []
        for fvar in vars_to_heapify:
            listast = self.explicate.explicate(List([Const(-1)]))
            heaplist.append(Assign([AssName(fvar,'OP_APPLY')],listast))
        v = self.visit(node.node)
        return Module(None, Stmt(heaplist + v.nodes))

    def visit_Stmt(self, node):
        return Stmt([self.visit(x) for x in node.nodes])

    def visit_Printnl(self, node):
        return Printnl([self.visit(node.nodes[0])], node.dest)

    def visit_Assign(self, node):
        if isinstance(node.nodes[0], AssName) and node.nodes[0].name in self.heapvarset:
            # XXX: this is wrong; can't explicate node.expr, since its already been explicated.
            # end up getting nested InjectFrom(InjectFrom('int',Const(1))) for heapify.py test case
            #assign = Assign([Subscript(Name(node.nodes[0].name),'OP_APPLY',[Const(0)])], self.visit(node.expr))
            #assignexpl = self.explicate.explicate(assign)
            #self.log.debug('visit_Assign: %s', assignexpl)
            #return assignexpl
            # resort to duplicating the logic of explication here.
            expr = self.explicate.explicate(Name(node.nodes[0].name))
            subexpr = self.explicate.explicate(Const(0))
            valueexpr = self.visit(node.expr)
            return Discard(CallFunc(Name('set_subscript'),[expr,subexpr,valueexpr]))
        elif isinstance(node.nodes[0], Subscript):
            raise Exception('wtf')
        else:
            return Assign(node.nodes, self.visit(node.expr))

    def visit_Discard(self, node):
        return Discard(self.visit(node.expr))

    def visit_Add(self, node):
        return Add((self.visit(node.left), self.visit(node.right)))

    def visit_UnarySub(self, node):
        return UnarySub(self.visit(node.expr))

    def visit_CallFunc(self, node):
        self.log.debug('visit_CallFunc: %s', node)
        return CallFunc(self.visit(node.node), [self.visit(x) for x in node.args])

    def visit_Const(self, node):
        return node

    def visit_Name(self, node):
        self.log.debug('visit_Name: %s: stack: %s',node,self.heapvarset)
        if node.name in self.heapvarset:
            subscript = Subscript(node,'OP_APPLY',[Const(0)])
            return self.explicate.explicate(subscript)
        else:
            return node

    def visit_Or(self, node):
        return Or([self.visit(x) for x in node.nodes])

    def visit_And(self, node):
        return And([self.visit(x) for x in node.nodes])

    def visit_IfExp(self, node):
        return IfExp(self.visit(node.test), self.visit(node.then), self.visit(node.else_))

    # List/Dict/Function no longer exist after explicate
    def visit_List(self, node):
        raise Exception('Encountered List AST in heapify.  List should no longer exist after explicate')

    def visit_Dict(self, node):
        raise Exception('Encountered Dict AST in heapify.  Dict should no longer exist after explicate')

    def visit_Function(self, node):
        raise Exception('Encountered Function AST in heapify.  Function should no longer exist after explicate')

    def visit_Compare(self, node):
        return Compare(self.visit(node.expr), [(node.ops[0][0], self.visit(node.ops[0][1]))])

    def visit_Not(self, node):
        return Not(self.visit(node.expr))

    def visit_Subscript(self, node):
        return Subscript(self.visit(node.expr), node.flags, [self.visit(node.subs[0])])

    def visit_Return(self, node):
        return Return(self.visit(node.value))

    def visit_InjectFrom(self, node):
        return InjectFrom(node.typ, self.visit(node.arg))

    def visit_ProjectTo(self, node):
        return ProjectTo(node.typ, self.visit(node.arg))

    def visit_GetTag(self, node):
        return GetTag(self.visit(node.arg))

    def visit_Let(self, node):
        self.log.debug('visit_Let: %s',node)
        return Let(node.var, self.visit(node.rhs), self.visit(node.body))

    def visit_Lambda(self, node):
        # First, get the variables to heapify and add them to the global set
        vars_to_heapify = self.getLambdaFreeVars(node.code) - node.free
        self.log.debug('visit_Lambda: (%-10.10s) Variables to Heapify: %s', node.lineno, vars_to_heapify)
        self.heapvarset = self.heapvarset | vars_to_heapify
        # Next, rename arguments in this Lambda that need to be heapified to new, unique argument names
        args_to_heapify = [x for x in node.argnames if x in vars_to_heapify]
        self.log.debug('visit_Lambda: (%-10.10s) Arguments to Heapify: %s', node.lineno, args_to_heapify)
        argmap={}
        for arg in args_to_heapify:
            argmap[arg] = self.explicate.varalloc.get_next_var()
        argnames = [argmap[arg] if arg in argmap else arg for arg in node.argnames]
        self.log.debug('visit_Lambda: (%-10.10s) New Argument List: %s', node.lineno, argnames)
        # Then, create our list of statements, paramAllocs, to heapify arguments 
        paramAllocs = []
        for arg in args_to_heapify:
           listast = self.explicate.explicate(List([Const(-1)]))
           paramAllocs.append(Assign([AssName(arg,'OP_APPLY')],listast))
        # Now, create our list of statements, paramInits, which sets the first element of our heapified
        # argument, to the corresponding renamed variable
        paramInits = []
        for arg in args_to_heapify:
           paramInits.append(Discard(CallFunc(Name('set_subscript'),[Name(arg),InjectFrom('int',Const(0)),Name(argmap[arg])])))
        # Finally, create our list of statements, localAllocs, to heapify local variables (that are not arguments)
        locals_to_heapify = [x for x in vars_to_heapify if x not in node.argnames]
        localAllocs = []
        for local in locals_to_heapify:
           listast = self.explicate.explicate(List([Const(-1)]))
           paramAllocs.append(Assign([AssName(local,'OP_APPLY')],listast))
        # Visit all the darling little children
        v = self.visit(node.code)
        # Return our new lambda with the new set of argument names, and paramAllocs, paramInits, and localAllocs
        # prepended to the list of statements.
        return Lambda(argnames, node.defaults, node.flags, Stmt(paramAllocs + paramInits + localAllocs + v.nodes))

    def visit_CallFuncIndirect(self, node):
        return CallFuncIndirect(self.visit(node.node), [self.visit(x) for x in node.args])
    
if __name__ == "__main__":
    import sys, compiler
    import logging.config
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        p2unique = P2UniquifyVars()
        p2explicator = P2Explicate(VariableAllocator())
        p2heap = P2Heapify(p2explicator)

        ast = compiler.parseFile(testcase)
        unique = p2unique.transform(ast)        
        explicated = p2explicator.explicate(unique)
        ast = p2heap.transform(explicated)
        
        print prettyAST(ast)
        #print ast
