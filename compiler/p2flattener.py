# vim: set ts=4 sw=4 expandtab:
from compiler.ast import *
from comp_util import *
from p1flattener import P1Flattener
from p2explicate import P2Explicate
from p2uniquifyvars import P2UniquifyVars
from p2heapify import P2Heapify
from p2freevars import P2FreeVars
from p2closureconvert import P2ClosureConversion
import operator

class P2Flattener(P1Flattener):
    """Class to performing flattening of complex expressions."""
    def __init__ (self, varalloc, validate=False):
        P1Flattener.__init__(self, varalloc)
        self.validate = validate
    
    def flatten (self, node):
        """Takes an AST as input, and then "flattens" the tree into a list of statements."""

        if isinstance(node, Function):
            # This is not a Function returned from the parse stage, but a top-level function
            # that is created in the closure-conversion pass.
            # We just need to flatten the "code" attribute, which is a Stmt.
            # Function(decorators, name, argnames, defaults, flags, doc, code, lineno=None)
            self.log.debug('in visit_Function, node.code = %s',node.code)
            code = self.flatten(node.code)
            for x in node.argnames:
                self.varalloc.add_var(x)
            return Function(node.decorators, node.name, node.argnames, node.defaults, node.flags, node.doc, code, node.lineno)
        elif isinstance(node, Return):
            retvar, retstmtlist = self.flatten(node.value)
            return retstmtlist + [Return(retvar)]
        elif isinstance(node, CallFuncIndirect):
            self.log.debug('CallFuncIndirect: args: %s', node.args)
            nodevar, nodestmtlist = self.flatten(node.node)
            tuplelist = [self.flatten(x) for x in node.args]
            varargs = [x[0] for x in tuplelist]
            varstmts = [x[1] for x in tuplelist]
            varname = self.varalloc.get_next_var()
            stmts = nodestmtlist + reduce(lambda x,y: x+y, varstmts, []) + [Assign([AssName(varname, 'OP_ASSIGN')], CallFuncIndirect(nodevar, varargs))]
            return (Name(varname), stmts)
        else:
            return P1Flattener.flatten(self, node)


if __name__ == "__main__":
    import compiler, sys
    import logging.config
    from p0parser import P0Parser
    from p1explicate import P1Explicate
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')

    testcases = sys.argv[1:]
    for testcase in testcases:
        p2unique = P2UniquifyVars()
        varalloc = VariableAllocator()
        p2explicator = P2Explicate(varalloc)
        p2heap = P2Heapify()
        p2closure = P2ClosureConversion(p2explicator, varalloc)
        p2flatten = P2Flattener(varalloc,True)

        ast = compiler.parseFile(testcase)
        unique = p2unique.transform(ast)        
        explicated = p2explicator.explicate(unique)
        #heaped = p2heap.transform(explicated)
        astlist = p2closure.transform(explicated)
        for ast in astlist:
            ast = p2flatten.flatten(ast)
            print ast
            print prettyAST(ast)
