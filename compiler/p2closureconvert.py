from compiler.ast import *
from comp_util import *
from x86ir import *

from p2explicate import P2Explicate
from p2uniquifyvars import P2UniquifyVars
from p2heapify import P2Heapify
from p2freevars import P2FreeVars


import logging
    
class P2ClosureConversion(object):
    def __init__(self, explicate, varalloc):
        self.log = logging.getLogger('compiler.closure')
        self.varalloc = varalloc
        self.name_alloc = {}
        self.functions = []
        self.freevars = P2FreeVars()
        self.explicate = explicate
        
    def get_next_name(self, name):
        if name in self.name_alloc:
            self.name_alloc[name] =self.name_alloc[name]+1
        else:
            self.name_alloc[name] = 0
        return 'glob_fun_%s_%d' % (name, self.name_alloc[name])             

    def transform(self, node, *args, **kwargs):
        self.log.info ('Starting closure conversion')
        main = self.visit(node)
        self.log.info ('Finished closure conversion')
        return [main] + self.functions

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
    
    def visit_Module(self,node, *args, **kwargs):
        return Module(None, self.visit(node.node), None)
    def visit_Stmt(self,node, *args, **kwargs):
        visited = [self.visit(x) for x in node.nodes]
        self.log.debug('Visited and produced %s'%visited)
        return Stmt(visited)
    def visit_Printnl(self, node, *args, **kwargs):
        return Printnl([self.visit(node.nodes[0])], node.dest)
    def visit_Assign(self, node, *args, **kwargs):
        self.log.debug('Visiting rhs of assign %s'%node.expr)
        return Assign(node.nodes, self.visit(node.expr)) 
    def visit_Discard(self, node, *args, **kwargs):
        return Discard(self.visit(node.expr))
    def visit_Add(self, node, *args, **kwargs):
        return Add((self.visit(node.left), self.visit(node.right)))
    def visit_UnarySub(self, node, *args, **kwargs):
        return UnarySub(self.visit(node.expr))
    def visit_CallFunc(self, node, *args, **kwargs):
        return CallFunc(self.visit(node.node), [self.visit(x) for x in node.args])
    def visit_Const(self, node, *args, **kwargs):
        return node
    def visit_Name(self, node, *args, **kwargs):
        return node
    def visit_Or(self, node, *args, **kwargs):
        return Or([self.visit(x) for x in node.nodes])
    def visit_And(self, node, *args, **kwargs):
        return And([self.visit(x) for x in node.nodes])
    def visit_IfExp(self, node, *args, **kwargs):
        return IfExp(self.visit(node.test), self.visit(node.then), self.visit(node.else_))
    # List/Dict/Function no longer exist after explicate
    def visit_List(self, node, *args, **kwargs):
        raise Exception('Encountered List AST in closure conversion.  List should no longer exist after explicate')
    def visit_Dict(self, node, *args, **kwargs):
        raise Exception('Encountered Dict AST in closure conversion.  Dict should no longer exist after explicate')
    def visit_Function(self, node, *args, **kwargs):
        raise Exception('Encountered Function AST in closure conversion.  Function should no longer exist after explicate')
    def visit_Compare(self, node, *args, **kwargs):
        return Compare(self.visit(node.expr), [(node.ops[0][0], self.visit(node.ops[0][1]))])
    def visit_Not(self, node, *args, **kwargs):
        return Not(self.visit(node.expr))
    def visit_Subscript(self, node, *args, **kwargs):
        return Subscript(self.visit(node.expr), node.flags, [self.visit(node.subs[0])])
    def visit_Return(self, node, *args, **kwargs):
        return Return(self.visit(node.value))
    def visit_InjectFrom(self, node, *args, **kwargs):
        return InjectFrom(node.typ, self.visit(node.arg))
    def visit_ProjectTo(self, node, *args, **kwargs):
        return ProjectTo(node.typ, self.visit(node.arg))
    def visit_GetTag(self, node, *args, **kwargs):
        return GetTag(self.visit(node.arg))
    def visit_Let(self, node, *args, **kwargs):
        return Let(node.var, self.visit(node.rhs), self.visit(node.body))
    def visit_Lambda(self, node, *args, **kwargs):
        # allocate a new function name
        name = self.get_next_name(node.lineno)
        self.log.debug('Creating function definition for %s' % name)
        
        # Add the function definition to the functions
        # Function(decorators, name, argnames, defaults, flags, doc, code, lineno=None)

        # get free variables in Lambda; returns a set
        bound, free = self.freevars.visit(node)
        fvars = list(free)

        # add assignments
        i = 0
        assigns=[]
        for fvar in fvars:
            subscript = self.explicate.explicate(Subscript(Name('fvs'),'OP_APPLY',[Const(i)]))
            self.log.debug('visit_Lambda: Subscript = %s' % subscript)
            assigns.append(Assign([AssName(fvar,'OP_ASSIGN')],subscript))
            i = i + 1

        # walk the body to perform closure conversion on any sub-lambdas
        # this could generate new closures as well, which get put in to the
        # global definition area
        newcode = self.visit(Stmt(assigns + node.code.nodes))

        func = Function(None, name, ['fvs'] + node.argnames, [], 0, None, newcode, None)
        self.functions.append(func)
        var_refs = []
        
        # remember to each free variable into our list
        fvs = self.explicate.explicate(List([Name(fvar) for fvar in fvars]))
        return InjectFrom('big', CallFunc(Name('create_closure'), [Const(name), fvs], None, None))

        #self.log.debug(node)
        #fvs = self.freevars.visit(node) - node.argnames
        #self.log.debug('Computed free_vars as %s'%fvs)
        #code = []
        #ssign([AssName(retvar,'OP_ASSIGN')], CallFunc(Name('set_subscript'),[expr,subexpr,valueexpr]))
        #ctr = 0
        #for var in fvs:
        #    code.append( Assign([AssName(Name(var), 'OP_ASSIGN')], Subscript))

    def visit_CallFuncIndirect(self, node, *args, **kwargs):
        # First, get a new temporary variable to refer to the expression "node.node", which
        # should evaluate to a closure
        closurevar = Name(self.varalloc.get_next_var())
        ret = Let(
                closurevar, 
                self.visit(node.node),
                CallFuncIndirect(
                  CallFunc(Name('get_fun_ptr'),[closurevar]),
                  [CallFunc(Name('get_free_vars'),[closurevar])] + [self.visit(x) for x in node.args]
                )
              )
        return ret

    
if __name__ == "__main__":
    import sys, compiler
    import logging.config
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        varalloc = VariableAllocator()
        p2unique = P2UniquifyVars()
        p2explicator = P2Explicate(varalloc)
        p2heap = P2Heapify()
        p2closure = P2ClosureConversion(p2explicator, varalloc)

        ast = compiler.parseFile(testcase)
        unique = p2unique.transform(ast)        
        explicated = p2explicator.explicate(unique)
        #heaped = p2heap.transform(explicated)
        astlist = p2closure.transform(explicated)
        for ast in astlist:
            print '\nFunction\n================='
            print prettyAST(ast)
