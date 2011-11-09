from compiler.ast import *
from comp_util import *
from x86ir import *

from p3explicate import P3Explicate
from p3uniquifyvars import P3UniquifyVars

import logging

from p2freevars import P2FreeVars

class P3FreeVars(P2FreeVars):
    '''Returns for each visited node return a set of variables not bound in that node'''
    def __init__(self):
        P2FreeVars.__init__(self)
        
    def getLocalAssigns(self,n):
        self.log.debug('getLocalAssigns %s'%n)

        if isinstance(n, (While, If)):
            # these are all expressions, so no assignments
            return set([])
        elif isinstance(n, (Let)):
            return set([n.var.name])
        else:
            return P2FreeVars.getLocalAssigns(self, n)
    
    def visit_While(self, node, *args, **kwargs):
        self.log.debug('visit_While %s'%node)
        test_b, test_f = self.visit(node.test)
        then_b, then_f = self.visit(node.body)
        return (set([]), test_f | then_f )

    def visit_If(self, node, *args, **kwargs):
        self.log.debug('visit_If %s'%node)
        test_b, test_f = self.visit(node.tests[0][0])
        then_b, then_f = self.visit(node.tests[0][1])
        else_b, else_f = self.visit(node.else_)
        return (set([]), test_f | then_f | else_f)

    
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
        p3unique = P3UniquifyVars()
        p3explicator = P3Explicate(VariableAllocator())
        p3free = P3FreeVars()

        ast = compiler.parseFile(testcase)
        unique = p3unique.visit(ast)        
        explicated = p3explicator.explicate(unique)
        print prettyAST(explicated)
        ast = p3free.visit(explicated)
        
        print ast            
