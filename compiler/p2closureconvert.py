from compiler.ast import *
from comp_util import *
from x86ir import *

from p2explicate import P2Explicate
from p2uniquifyvars import P2UniquifyVars
from p2heapify import P2Heapify
from p2freevars import P2FreeVars


import logging
    
class P2ClosureConversion(object):
    def __init__(self):
        self.log = logging.getLogger('compiler.closure')
        self.name_alloc = {}
        self.globals = []
        self.freevars = P2FreeVars()
        
    def get_next_name(self, name):
        if name in self.name_alloc:
            self.name_alloc[name] =self.name_alloc[name]+1
        else:
            self.name_alloc[name] = 0
        return 'glob_fun_%s_%d' % (name, self.name_alloc[name])             

    def transform(self, node, *args, **kwargs):
        self.log.info ('Starting closure conversion')
        ret = self.visit(node)
        self.log.info ('Finished closure conversion')
        return ret

    def visit(self, node, *args, **kwargs):
        self.log.debug(node)
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        # we return the node passed in by default so we do not have to handle
        # every case unless necessary
        if not meth:
            return node
        return meth(node, *args, **kwargs)
    
    def visit_Module(self,node, *args, **kwargs):
        return self.visit(node.node)
    def visit_Stmt(self,node, *args, **kwargs):
        visited = [self.visit(x) for x in node.nodes]
        self.log.debug('Visited and produced %s'%visited)
        return Stmt(visited)
    def visit_Assign(self, node, *args, **kwargs):
        self.log.debug('Visiting rhs of assign %s'%node.expr)
        return Assign(node.nodes, self.visit(node.expr)) 
    def visit_Lambda(self, node, *args, **kwargs):
        # allocate a new function name
        name = self.get_next_name(node.lineno)
        
        # walk the body to perform closure conversion on any sub-lambdas
        # this could generate new closures as well, which get put in to the
        # global definition area
        newbody = self.visit(node.body)

        fvs = self.freevars.visit(node) - node.argnames
        self.log.debug('Computed free_vars as %s'%fvs)
        code = []
        #ssign([AssName(retvar,'OP_ASSIGN')], CallFunc(Name('set_subscript'),[expr,subexpr,valueexpr]))
        ctr = 0
        for var in fvs:
            code.append( Assign([AssName(Name(var), 'OP_ASSIGN')], Subscript))
        
        self.log.debug(node)
    

    
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
        p2heap = P2Heapify()
        p2closure = P2ClosureConversion()

        ast = compiler.parseFile(testcase)
        unique = p2unique.transform(ast)        
        explicated = p2explicator.explicate(unique)
        heaped = p2heap.transform(explicated)
        ast = p2closure.transform(heaped)
        
        #print prettyAST(ast)
