# vim: set ts=4 sw=4 expandtab:
from compiler.ast import *
from comp_util import *
from p0parser import P0Parser
from p0flattener import P0Flattener
import operator

class P1Flattener(P0Flattener):
    """Class to performing flattening of complex expressions."""
    def __init__ (self, varalloc, validate=False):
        P0Flattener.__init__(self, varalloc)
        self.validate = validate
    
    def flatten (self, node):
        """Takes an AST as input, and then "flattens" the tree into a list of statements."""

        if isinstance(node, (Or,And)):
            # we only need to handle two operands to the "or" operator
            if self.validate and len(node.nodes) > 2:
                raise Exception("Only two operands supported in P1 for 'or' operator")
            lhsvar, lhsstmtlist = self.flatten(node.nodes[0])
            rhsvar, rhsstmtlist = self.flatten(node.nodes[1])
            varname = self.varalloc.get_next_var()
            result = Or([lhsvar,rhsvar]) if isinstance(node,Or) else And([lhsvar,rhsvar])
            return (Name(varname), lhsstmtlist + rhsstmtlist + [Assign([AssName(varname, 'OP_ASSIGN')], result)])
        elif isinstance(node, List):
            stmts = [self.flatten(x) for x in node.nodes]
            varlist = [x for x,y in stmts]
            # convert the list of lists into a single list of statements
            stmtlist = reduce(lambda x,y: x+y, [y for x,y in stmts if y != []], [])
            varname = self.varalloc.get_next_var()
            return (Name(varname), stmtlist + [Assign([AssName(varname, 'OP_ASSIGN')], List(varlist))])
        elif isinstance(node, Dict):
            keys = [self.flatten(x[0]) for x in node.items]
            keyvarlist = [x for x,y in keys]
            keystmtlist = reduce(lambda x,y: x+y, [y for x,y in keys if y != []], [])
            values = [self.flatten(x[1]) for x in node.items]
            valuevarlist = [x for x,y in values]
            valuestmtlist = reduce(lambda x,y: x+y, [y for x,y in values if y != []], [])
            # keyvaluelist becomes a list of tuples, where each tuple is a key,value corresponding to the 
            # temp variables for the key/value
            keyvaluelist = map(lambda x: (keyvarlist[x],valuevarlist[x]), range(0,len(keyvarlist)))
            varname = self.varalloc.get_next_var()
            return (Name(varname), keystmtlist + valuestmtlist + [Assign([AssName(varname, 'OP_ASSIGN')], Dict(keyvaluelist))])
        # not sure why we are handling tuple? Ah, this was probably because Dict.items is a tuple.
        # I think its cleaner to separate into keys/values as done above.
        #elif isinstance(node, tuple):
        #    return (node,[])
        elif isinstance(node, IfExp):
            # XXX: B.S., need to look at this more.  I think that the flattened statements/expressions
            # should be encapsulated in the IfExp node, so that the statements are not unconditionally
            # executed.  This may require a new node type to store the statements...
            vart, then = self.flatten(node.then)
            vare, else_ = self.flatten(node.else_)
            vartes, test = self.flatten(node.test)
            # The return value should be the new If node itself?  I think...
            varname = self.varalloc.get_next_var()
            return (Name(varname), NewIfExp(vartes, vart, vare, then, else_, test))
        elif isinstance(node, Not):
            var, stmtlist = self.flatten(node.expr)
            varname = self.varalloc.get_next_var()
            return (Name(varname), stmtlist + [Assign([AssName(varname,'OP_ASSIGN')], Not(varname))])
        elif isinstance(node, Compare):
            # Only need to handle binary comparison operators.  So if len(node.ops) > 1, its a syntax error.
            # For example, a == b == c is valid python, but invalid P1
            if self.validate and len(node.ops) > 1:
                raise Exception('Only two operands supported in P1 for comparison operators')
            if self.validate and node.ops[0][0] not in ['==','!=','is']:
                raise Exception("'%s' is not a valid comparison operator in P1" % node.ops[0][0])
            lhsvar, lhsstmtlist = self.flatten(node.expr)
            oper, rhs = node.ops[0]
            rhsvar, rhsstmtlist = self.flatten(rhs)
            varname = self.varalloc.get_next_var()
            return (Name(varname), lhsstmtlist + rhtstmtlist + [Assign([AssName(varname,'OP_ASSIGN')], Compare(lhsvar, [(oper, rhsvar)]))])
        elif isinstance(node, Subscript):
            # We only need to handle one subscript per the grammar, e.g, a[1,2] is invalid P1
            # (a[1,2] is the only case where you get len(node.subs) > 1)
            if self.validate and len(node.subs) > 1:
                raise Exception('Only one subscript index supported in P1')
            exprvar, exprstmtlist = self.flatten(node.expr)
            subvar, substmtlist = self.flatten(node.subs[0])
            varname = self.varalloc.get_next_var()
            return (Name(varname), exprstmtlist + substmtlist + [Assign([AssName(varname,'OP_ASSIGN')], Subscript(exprvar, node.flags, subvar))])
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
        
        p1flattener = P1Flattener(VariableAllocator(),True)
        stmtlist = p1flattener.flatten(ast)
        print stmtlist
