# vim: set ts=4 sw=4 expandtab:
from compiler.ast import *
from comp_util import *
from p2flattener import P2Flattener
from p3explicate import P3Explicate
from p3uniquifyvars import P3UniquifyVars
from p3heapify import P3Heapify
from p3freevars import P3FreeVars
from p3closureconvert import P3ClosureConversion
import operator

class P3Flattener(P2Flattener):
    """Class to performing flattening of complex expressions."""
    def __init__ (self, varalloc, validate=False):
        P2Flattener.__init__(self, varalloc)
        self.validate = validate
    
    def flatten (self, node):
        """Takes an AST as input, and then "flattens" the tree into a list of statements."""

        if isinstance(node, While):
            #statement
            print
            print
            print
            print self.flatten(node.body)   
            print
            flatbody = self.flatten(node.body)
            #expression
            var, flattest = self.flatten(node.test) 
             
            return [x86While((var,flattest) , flatbody, [], node.lineno)]   
        else:
            return P2Flattener.flatten(self, node)


if __name__ == "__main__":
    import compiler, sys
    import logging.config
    
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')

    testcases = sys.argv[1:]
    for testcase in testcases:
        p3unique = P3UniquifyVars()
        varalloc = VariableAllocator()
        p3explicator = P3Explicate(varalloc)
        p3heap = P3Heapify(p3explicator)
        p3closure = P3ClosureConversion(p3explicator, varalloc)
        p3flatten = P3Flattener(varalloc,True)

        ast = compiler.parseFile(testcase)
        unique = p3unique.transform(ast)        
        explicated = p3explicator.explicate(unique)
        heaped = p3heap.transform(explicated)
        astlist = p3closure.transform(heaped)
        print astlist   
        for ast in astlist:
            print ast
            ast = p3flatten.flatten(ast)
            print prettyAST(ast)


