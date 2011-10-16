from compiler.ast import *
from comp_util import *
from x86ir import *

from p2explicate import P2Explicate
from p2uniquifyvars import P2UniquifyVars
from p2heapify import P2Heapify

import logging

class P2FreeVars(object):
    def __init__(self):
        self.log = logging.getLogger('freevars')

    def visit(self, node, *args, **kwargs):
        self.log.debug(node)
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        # we return the node passed in by default so we do not have to handle
        # every case unless necessary
        if not meth:
            return set([])
        self.log.debug('Visiting %s'%node)
        return meth(node, *args, **kwargs)
    def visit_Module(self,node, *args, **kwargs):
        return self.visit(node.node)
    def visit_Stmt(self,node, *args, **kwargs):
        st_args = [self.visit(x) for x in node.nodes]
        free_vars = reduce(lambda a,b : a|b, st_args, set([]))
        self.log.debug('Statement freeVars: %s'%free_vars)
        return free_vars
    def visit_Const(self,node, *args, **kwargs):
        return set([])
    def visit_Name(self,node, *args, **kwargs):
        return set([node.name])
    def visit_Assign(self, node, *args, **kwargs):
        rhs_fvar = [self.visit(x) for x in node.expr]
        self.log.debug('Assign rhs free vars %s'%rhs_fvar)
        fvars = set([node.nodes[0].name]) | reduce(lambda a,b : a | b, rhs_fvar, set([]))
        self.log.debug('Assign: free_vars %s'%fvars)
        return fvars
    def visit_Discard(self, node, *args, **kwargs):
        return self.visit(node.expr)
    def visit_Add(self,node, *args, **kwargs):
        return self.visit(node.left) | self.visit(node.right)
    def visit_CallFunc(self,node, *args, **kwargs):
        fv_args = [self.visit(e) for e in node.args]
        free_in_args = reduce(lambda a,b : a | b, fv_args, set([]))
        return self.visit(node.node) | free_in_args 
    def visit_Lambda(self,node, *args, **kwargs):
        fv_args = [self.visit(e) for e in node.args]
        free_in_args = reduce(lambda a,b : a | b, fv_args, set([]))
        return self.visit(node.code ) | free_in_args
    def visit_Printnl(self, node, *args, **kwargs):
        fv_args = [self.visit(e) for e in node.nodes]
        free_in_args = reduce(lambda a,b : a | b, fv_args, set([]))
        return free_in_args
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
        p2heap = P2Heapify()
        p2free = P2FreeVars()

        ast = compiler.parseFile(testcase)
        unique = p2unique.visit(ast)        
        explicated = p2explicator.explicate(unique)
        heaped = p2heap.visit(explicated)
        ast = p2free.visit(heaped)
        
        print ast            