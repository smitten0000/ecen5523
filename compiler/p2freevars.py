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

    def getLocalAssigns(self,n):
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
            raise Exception('Functions should have been removed in explicate.')
        elif isinstance(n, Lambda):
            # a function definition is equivalent to an assignment to a 
            # variable with the same name as the function
            # No need to recurse into the Function since the intent of the function
            # is to only find assigments for the local scope
            return set([n.name])
        elif isinstance(n, (Add,UnarySub,CallFunc,Const,Name,Or,And,IfExp,List,Dict,Compare,Not,Subscript)):
            # these are all expressions, so no assignments
            return set([])
        else:
            raise Exception('Unhandled expression: "%s"' % n)

    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        # we return the node passed in by default so we do not have to handle
        # every case unless necessary
        if not meth:
            raise Exception('Unknown node: %s method: %s' % (node.__class__, meth_name))
        self.log.debug('Visiting %s', node)
        return meth(node, *args, **kwargs)
    
    def visit_Module(self,node, *args, **kwargs):
        localassigns = self.getLocalAssigns(node.node)
        bound, free = self.visit(node.node)
        bound = localassigns.intersection(free)
        free = free - bound
        self.log.info('visit_Module: Module:          %s', node)
        self.log.info('visit_Module: Free Variables:  %s', free)
        self.log.info('visit_Module: Bound Variables: %s', bound)
        return (bound,free)
    
    def visit_Stmt(self,node, *args, **kwargs):
        # list of tuples
        st_args = [self.visit(x) for x in node.nodes]
        # list of sets
        f = [free for (bounds, free) in st_args]
        b = [bounds for (bounds, free) in st_args]
        f = squash(f)
        b = squash(b)  
        return (b, f)

    def visit_IfExp(self, node, *args, **kwargs):
        test_b, test_f = self.visit(node.test)
        then_b, then_f = self.visit(node.then)
        else_b, else_f = self.visit(node.else_)
        return (set([]), test_f | then_f | else_f)

    def visit_List(self, node, *args, **kwargs):
        # list of tuples
        fv_args = [self.visit(e) for e in node.nodes]
        # list of sets
        free = [x for (x,y) in fv_args]
        return (set([]), squash(free))

    def visit_Dict(self, node, *args, **kwargs):
        # list of tuples
        fv_key_args = [self.visit(e[0]) for e in node.items]
        fv_val_args = [self.visit(e[1]) for e in node.items]
        # list of sets
        free_key = [free for (bound,free) in fv_key_args]
        free_val = [free for (bound,free) in fv_val_args]
        return (set([]), squash(free_key) | squash(free_val))

    def visit_Compare(self, node, *args, **kwargs):
        (left_b, left_f) = self.visit(node.expr)
        (right_b, right_f) = self.visit(node.ops[0][1])
        free = (right_f|left_f)
        return (set([]), free)

    def visit_Subscript(self, node, *args, **kwargs):
        (left_b, left_f) = self.visit(node.expr)
        (right_b, right_f) = self.visit(node.subs[0])
        free = (right_f|left_f)
        return (set([]), free)

    def visit_Const(self,node, *args, **kwargs):
        return (set([]),set([]))

    def visit_Name(self,node, *args, **kwargs):
        return (set([]),set([node.name]))
    
    def visit_Assign(self, node, *args, **kwargs):        
        b, f = self.visit(node.expr)
        # we don't care about LHS in Assign, since our visit_Lambda calls getLocalAssigns
        # so return an empty set for "bound"
        return (set([]),f)
    
    def visit_Discard(self, node, *args, **kwargs):
        b, f = self.visit(node.expr)
        return (set([]),f)
    
    def visit_Add(self,node, *args, **kwargs):
        # get the variables which are bound in this scope and referenced in this scope
        # we shouldn't ever see a case where we an bind a variable in scope, since (a=3)+4 is non-sensical for our syntax
        (left_b, left_f) = self.visit(node.left)
        (right_b, right_f) = self.visit(node.right)
        free = (right_f|left_f)
        self.log.debug('visit_Add: free vars %s'%(free))        
        return (set([]), free)

    def visit_UnarySub(self, node, *args, **kwargs):
        bound, free = self.visit(node.expr)
        return (set([]), free)

    def visit_GetTag(self, node, *args, **kwargs):
        bound, free = self.visit(node.arg)
        return (set([]), free)

    def visit_InjectFrom(self, node, *args, **kwargs):
        bound, free = self.visit(node.arg)
        return (set([]), free)

    def visit_ProjectTo(self, node, *args, **kwargs):
        bound, free = self.visit(node.arg)
        return (set([]), free)

    def visit_Or(self, node, *args, **kwargs):
        left_b, left_f = self.visit(node.nodes[0])
        right_b, right_f = self.visit(node.nodes[0])
        return (set([]), left_f | right_f)

    def visit_And(self, node, *args, **kwargs):
        left_b, left_f = self.visit(node.nodes[0])
        right_b, right_f = self.visit(node.nodes[0])
        return (set([]), left_f | right_f)

    def visit_Not(self, node, *args, **kwargs):
        bound, free = self.visit(node.expr)
        return (set([]), free)

    def visit_CallFunc(self, node, *args, **kwargs):
        # list of tuples
        fv_args = [self.visit(e) for e in node.args]
        # list of sets
        free = [f for (b,f) in fv_args]
        return (set([]),squash(free)) 
    
    def visit_CallFuncIndirect(self,node, *args, **kwargs):
        # list of tuples
        fv_args = [self.visit(e) for e in node.args]
        # list of sets
        free = [f for (b,f) in fv_args]
        expr_b, expr_f = self.visit(node.node)
        self.log.info('visit_CallFuncIndirect: Free variables: %s', expr_f | squash(free))
        return (set([]),expr_f | squash(free)) 
    
    def visit_Lambda(self, node, *args, **kwargs):
        # this is the set of local assignments and parameters
        localassigns = self.getLocalAssigns(node.code) | set(node.argnames)
        # bound, free variables in the children
        bound, free = self.visit(node.code)
        # We say that a variable reference is bound with respect to a given expression
        # or statement, let's call it P, if there is an function or lambda inside P
        # that encloses the variable reference and that function or lambda has
        # that variable as a parameter or local 
        # translated --> bound is equivalent to the intersection between localassigns and free
        bound = localassigns.intersection(free)
        # We say that a variable is free with respect to an expression or 
        # statement P if there is a reference to the variable inside P that 
        # is not bound in P 
        # translated --> free in P is equivalent to free in P's children minus (set difference)
        #                the bound variables in P
        free = free - bound
        self.log.info('visit_Lambda: Module:          %s', node)
        self.log.info('visit_Lambda: Free Variables:  %s', free)
        self.log.info('visit_Lambda: Bound Variables: %s', bound)
        # set some attributes on the node
        node.free = free
        node.bound = bound
        return (bound, free)

    def visit_Printnl(self, node, *args, **kwargs):
        # list of sets
        bound, free = self.visit(node.nodes[0])
        return (set([]), free)

    def visit_Return(self, node, *args, **kwargs):
        bound, free = self.visit(node.value)
        return (set([]), free)

    def visit_Let(self, node, *args, **kwargs):
        rhs_b, rhs_f = self.visit(node.rhs)
        body_b, body_f = self.visit(node.body)
        return (set([node.var.name]), (body_f | rhs_f) - set([node.var.name]))

    
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
