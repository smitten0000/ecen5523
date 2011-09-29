# vim: set ts=4 sw=4 expandtab:
from compiler.ast import *
from comp_util import *
from p0parser import P0Parser

class P0Flattener:
    """Class to performing flattening of complex expressions."""
    def __init__ (self, varalloc):
        self.varalloc = varalloc

    def flatten (self, node):
        """Takes an AST as input, and then "flattens" the tree into a list of statements."""
        # XXX: optimization.  If direct descendant in AST is also UnarySub, then
        # we should be able to optimize the two UnarySub nodes away.
        # X = UnarySub(UnarySub(X))  
        while isinstance(node, UnarySub) and isinstance(node.expr, UnarySub):
            node = node.expr.expr
        if isinstance(node, Module):
            return Module(None, self.flatten(node.node), None)
        elif isinstance(node, Stmt):
            return Stmt(reduce(lambda x,y: x+y, [self.flatten(x) for x in node.nodes]), None)
        elif isinstance(node, Printnl):
            if len(node.nodes) > 0:
                var, stmtlist = self.flatten(node.nodes[0])
                return stmtlist + [Printnl([var], node.dest)]
        elif isinstance(node, Assign):
            if isinstance(node.nodes[0],Subscript):
                self.varalloc.add_var(node.nodes[0].expr.name)
            else:
                self.varalloc.add_var(node.nodes[0].name)
            var, stmtlist = self.flatten(node.expr)
            return stmtlist + [Assign(node.nodes, var)]
        elif isinstance(node, Discard):
            # discard nodes should be ignored; except for function calls with side effects.
            var, stmtlist = self.flatten(node.expr)
            return stmtlist
        elif isinstance(node, Add):
            left, stmtleft = self.flatten(node.left)
            right, stmtright = self.flatten(node.right)
            varname = self.varalloc.get_next_var()
            return (Name(varname), stmtleft + stmtright + [Assign([AssName(varname, 'OP_ASSIGN')], Add((left,right)))] )
        elif isinstance(node, UnarySub):
            f, stmtlist = self.flatten(node.expr)
            varname = self.varalloc.get_next_var()
            return (Name(varname), stmtlist + [Assign([AssName(varname, 'OP_ASSIGN')], UnarySub(f))])
        elif isinstance(node, CallFunc):
            varname = self.varalloc.get_next_var()
            return (Name(varname), [Assign([AssName(varname, 'OP_ASSIGN')], node)])
        elif isinstance(node, Const):
            return (node, [])
        elif isinstance(node, Name):
            return (node, [])
        elif isinstance(node, AssName):
            stmtlist.varalloc.add_var(node.assname)
            return (node, [])
        else:
            raise Exception('Unknown node: %s: %s' % (node.__class__, node))


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
