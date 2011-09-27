# vim: set ts=4 sw=4 expandtab:
from compiler.ast import *
from comp_util import *
from p0parser import P0Parser
from p0flattener import P0Flattener

class P1Flattener(P0Flattener):
    """Class to performing flattening of complex expressions."""
    def __init__ (self, varalloc):
        P0Flattener.__init__(self, varalloc)

    def flatten (self, node):
        """Takes an AST as input, and then "flattens" the tree into a list of statements."""

        if isinstance(node, Module):
            return Module(None, self.flatten(node.node), None)
        else:
            return P0Flattener.flatten(self, node)


if __name__ == "__main__":
    import compiler, sys
    if len(sys.argv) < 2:
        sys.exit(1)

    testcases = sys.argv[1:]
    for testcase in testcases:
        parser = P0Parser()
        parser.build()
        #ast = compiler.parseFile(testcase)
        ast = parser.parseFile(testcase)
        p0flattener = P0Flattener(VariableAllocator())
        stmtlist = p0flattener.flatten(ast)
        print stmtlist
