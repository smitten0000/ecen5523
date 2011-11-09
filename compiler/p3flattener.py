# vim: set ts=4 sw=4 expandtab:
from compiler.ast import *
from comp_util import *
from p2flattener import P2Flattener
from p3declassify import P3Declassify
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
            flatbody = self.flatten(node.body)
            #expression
            var, flattest = self.flatten(node.test) 
            return [While((var,Stmt(flattest)), flatbody, [], node.lineno)]   
        elif isinstance(node, If):
            # flatten the "test" expression
            vartes, test = self.flatten(node.tests[0][0])
            # flatten the "then" and "else" statements
            then = self.flatten(node.tests[0][1])
            else_ = self.flatten(node.else_)
            
            # NOTE: The If node has two attributes: "tests" and "else_".  The tests attribute is
            # a list of tuples, where the first element in the tuple is the test expression and the
            # second element in the tuple is a Stmt object.  Each tuple in the list corresponds to
            # an "if" or "elif" clause.  The else_ attribute is a Stmt object corresponding to the 
            # "else" clause.
            self.log.debug('then=%s' % then)
            self.log.debug('else_=%s' % then)
            return test + [If([(vartes, then)], else_)]

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
        varalloc = VariableAllocator()
        declassify = P3Declassify(varalloc)
        unique = P3UniquifyVars()
        explicator = P3Explicate(varalloc)
        heap = P3Heapify(explicator)
        closure = P3ClosureConversion(explicator, varalloc)
        flatten = P3Flattener(varalloc,True)

        ast = compiler.parseFile(testcase)
        ast = declassify.transform(ast)
        ast = unique.transform(ast)        
        ast = explicator.explicate(ast)
        ast = heap.transform(ast)
        astlist = closure.transform(ast)
        print astlist   
        for ast in astlist:
            print ast
            ast = flatten.flatten(ast)
            print prettyAST(ast)


