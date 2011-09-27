# vim: set ts=4 sw=4 expandtab:
from compiler.ast import *
from comp_util import *
from p0parser import P0Parser
from p0flattener import P0Flattener
import operator

class P1Flattener(P0Flattener):
    """Class to performing flattening of complex expressions."""
    def __init__ (self, varalloc):
        P0Flattener.__init__(self, varalloc)
    
    def flatten (self, node):
        """Takes an AST as input, and then "flattens" the tree into a list of statements."""

        if isinstance(node, Or):
            stmts = [self.flatten(x) for x in node.nodes]
            simple = [x for (x,y) in stmts]
            other = [y for (x,y) in stmts if y != []]
            other = reduce(lambda x,y: x+y, [x for x in other], [])
            return (Or(simple),[])
        elif isinstance(node, List):
            stmts = [self.flatten(x) for x in node.nodes]
            simple = [x for (x,y) in stmts]
            other = [y for (x,y) in stmts if y != []]
            other = reduce(lambda x,y: x+y, [x for x in other])
            return (List(simple),[other])
        
        elif isinstance(node, Dict):
            stmts = [self.flatten(x) for x in node.items]
            simple = [x for (x,y) in stmts]
            other = [y for (x,y) in stmts if y != []]
            other = reduce(lambda x,y: x+y, [x for x in other], [])
            return (Dict(simple),[other])
        elif isinstance(node, tuple):
            return (node,[])
        elif isinstance(node, IfExp):
            vart, then = self.flatten(node.then)
            vare, else_ = self.flatten(node.else_)
            vartes, test = self.flatten(node.test)
            return (IfExp(vart, vare, vartes),then+else_+test)
        elif isinstance(node, Not):
            var, stmtlist = self.flatten(node.expr)
            return (node, stmtlist)
        else:
            return P0Flattener.flatten(self, node)


if __name__ == "__main__":
    import compiler, sys
    if len(sys.argv) < 2:
        sys.exit(1)

    testcases = sys.argv[1:]
    for testcase in testcases:
        #parser = P0Parser()
        #parser.build()
        #ast = parser.parseFile(testcase)
        ast = compiler.parseFile(testcase)
        
        p1flattener = P1Flattener(VariableAllocator())
        stmtlist = p1flattener.flatten(ast)
        print stmtlist
