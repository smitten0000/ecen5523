# vim: set ts=4 sw=4 expandtab:
from compiler.ast import *
from comp_util import *
from p1flattener import P1Flattener
from p2explicate import *
import operator

class P2Flattener(P1Flattener):
    """Class to performing flattening of complex expressions."""
    def __init__ (self, varalloc, validate=False):
        P1Flattener.__init__(self, varalloc)
        self.validate = validate
    
    def flatten (self, node):
        """Takes an AST as input, and then "flattens" the tree into a list of statements."""

        if False:
            pass
        else:
            return P1Flattener.flatten(self, node)


if __name__ == "__main__":
    import compiler, sys
    from p0parser import P0Parser
    from p1explicate import P1Explicate
    if len(sys.argv) < 2:
        sys.exit(1)

    testcases = sys.argv[1:]
    for testcase in testcases:
        #parser = P0Parser()
        #parser.build()
        #ast = parser.parseFile(testcase)
        ast = compiler.parseFile(testcase)
        varalloc = VariableAllocator()
        p1explicator = P2Explicate(varalloc)
        ast = p2explicator.explicate(ast)
        p1flattener = P1Flattener(varalloc,True)
        stmtlist = p1flattener.flatten(ast)
        print stmtlist
        print prettyAST(stmtlist)
        print '\n'.join([pretty(x) for x in stmtlist.node.nodes])
