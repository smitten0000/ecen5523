from compiler.ast import *
from comp_util import *
from x86ir import *

from p2explicate import P2Explicate
from p2uniquifyvars import P2UniquifyVars

import logging

squash = lambda fv_args: reduce(lambda a,b : a | b, fv_args, set([]))

class P2FreeVars(object):
    '''Returns for each visited node return a set of variables not bound in that node'''
    def __init__(self):
        self.log = logging.getLogger('freevars')

    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        # we return the node passed in by default so we do not have to handle
        # every case unless necessary
        if not meth:
            return (set([]),set([]))
        return meth(node, *args, **kwargs)
    
    def visit_Module(self,node, *args, **kwargs):
        return (set([]),self.visit(node.node))
    
    def visit_Stmt(self,node, *args, **kwargs):
        st_args = [self.visit(x) for x in node.nodes]
        
        fvar = [free for (bounds, free) in st_args]
        bvar = [bounds for (bounds, free) in st_args]
        print "**********"
        print (fvar)
        print squash(fvar)
        free_vars = (fvar)
        bound_vars = (bvar)  
        self.log.debug('Statement %s freeVars: %s'%(node, free_vars))
        return (bound_vars, fvar)
    
    def visit_Const(self,node, *args, **kwargs):
        return (set([]),set([]))
    def visit_Name(self,node, *args, **kwargs):
        return (set([]),set([node.name]))
    
    def visit_Assign(self, node, *args, **kwargs):        
        
        rhs_vars = [self.visit(x) for x in node.expr]
        
        self.log.debug('Assign rhs free vars %s'%rhs_vars)
        rhs_fvar = [freez for (bounds, freez) in rhs_vars]
        rhs_bvar = [bounds for (bounds, freez) in rhs_vars]
        rhs_bvar = rhs_bvar+[set([node.nodes[0].name])]
        
        self.log.debug('Free vars: %s, vars bound %s'%(rhs_fvar, rhs_bvar))
        
        all_free = squash(rhs_fvar)
        rhs_bvar = squash(rhs_bvar)
 
        fvars = all_free - rhs_bvar
        self.log.debug('Assign: bound %s, free_vars %s'%(rhs_bvar, fvars)) 
        return (rhs_bvar,fvars)
    
    def visit_Discard(self, node, *args, **kwargs):
        return (set([]),self.visit(node.expr))
    
    def visit_Add(self,node, *args, **kwargs):
        # get the variables which are bound in this scope and referenced in this scope
        # we shouldn't ever see a case where we an bind a variable in scope, since (a=3)+4 is non-sensical for our syntax
        (left_b, left_f) = self.visit(node.left)
        (right_b, right_f) = self.visit(node.right)
        bound = (left_b|right_b) # this should always be an empty set since p2 does not support assignments in an add
        free = (right_f|left_f)
        self.log.debug('Add bound vars %s free vars %s'%(bound,free))        
        return (bound  ,  free)
    
    def visit_CallFunc(self,node, *args, **kwargs):
        fv_args = [self.visit(e) for e in node.args]
        free_in_args = squash(fv_args)       
        return (set([]),self.visit(node.node) | free_in_args) 
    
    def visit_Lambda(self,node, *args, **kwargs):
        self.log.debug('Lambda args: %s' %node.argnames)
        fv_args = [set([e]) for e in node.argnames]
        bound_vars = reduce(lambda a,b : a | b, fv_args, set([]))
        
        self.log.debug('Bound in lambda %s'%bound_vars)
        
        bound_vars, free_vars = self.visit(node.code)
        
        self.log.debug("Variables bound: %s, and free: %s"%(bound_vars, free_vars))
        free_vars = free_vars - bound_vars        
        self.log.debug('Lambda free vars: %s' %free_vars)
        return (set([]),free_vars)
    def visit_Printnl(self, node, *args, **kwargs):
        fv_args = [self.visit(e) for e in node.nodes]
        free_in_args = reduce(lambda a,b : a | b, fv_args, set([]))
        return (set([]),free_in_args)
    def visit_Return(self, node, *args, **kwargs):
        return (set([]),self.visit(node.value))
    #def visit_Statement(self,node, *args, **kwargs):


    

    
if __name__ == "__main__":
    # create logger
    log = logging.getLogger('freevars')
    log.setLevel(logging.DEBUG)
    
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # add formatter to ch
    ch.setFormatter(formatter)
    
    # add ch to logger
    log.addHandler(ch)

    import sys, compiler
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    debug = True
    for testcase in testcases:
        p2unique = P2UniquifyVars()
        p2explicator = P2Explicate(VariableAllocator())
        p2free = P2FreeVars()

        ast = compiler.parseFile(testcase)
        unique = p2unique.visit(ast)        
        explicated = p2explicator.explicate(unique)
        print prettyAST(explicated)
        ast = p2free.visit(explicated)
        
        print ast            