import compiler, sys, os
from compiler.ast import *

def pretty(node):
    """Given an AST node, print out a human readable form."""
    if isinstance(node, Printnl):
        if node.dest is not None:
            return 'print >> %s, %s' % (node.dest, pretty(node.nodes[0]))
        else:
            return 'print %s' % (pretty(node.nodes[0]))
    elif isinstance(node, Assign):
        return '%s = %s' % (pretty(node.nodes[0]), pretty(node.expr))
    elif isinstance(node, Discard):
        pass
    elif isinstance(node, CallFunc):
        if node.args is not None and len(node.args) > 0:
            return '%s(%s)' % (pretty(node.node), node.args)
        else:
            return '%s()' % (pretty(node.node))
    elif isinstance(node, Add):
        return '%s + %s' % (pretty(node.left), pretty(node.right))
    elif isinstance(node, UnarySub):
        return '- %s' % (pretty(node.expr))
    elif isinstance(node, Const):
        return node.value
    elif isinstance(node, Name):
        return node.name
    elif isinstance(node, AssName):
        return node.name
    else:
        print node
        raise Exception('Unknown node: %s' % node.__class__)


def flatten (node, stmtlist, discard=False):
    """Takes an AST as input, and then "flattens" the tree into a
list of statements.  These are stored in the StatementList
object, which is given as the 2nd argument."""
    # XXX: optimization.  If direct descendant in AST is also UnarySub, then
    # we should be able to optimize the two UnarySub nodes away.
    # X = UnarySub(UnarySub(X))  
    while isinstance(node, UnarySub) and isinstance(node.expr, UnarySub):
        node = node.expr.expr
    if isinstance(node, Module):
        flatten(node.node, stmtlist, discard)
    elif isinstance(node, Stmt):
        for node in node.nodes:
            if node is not None:
                flatten(node, stmtlist, discard)
    elif isinstance(node, Printnl):
        if len(node.nodes) > 0:
            stmtlist.append(Printnl([flatten(node.nodes[0], stmtlist, discard)], node.dest))
    elif isinstance(node, Assign):
        stmtlist.add_var(node.nodes[0].name)
        stmtlist.append(Assign(node.nodes, flatten(node.expr, stmtlist, discard)))
        return node.nodes[0]
    elif isinstance(node, Discard):
        # discard nodes should be ignored; except for function calls with side effects.
        # call flatten() with discard=True
        flatten(node.expr, stmtlist, True)
        return None
    elif isinstance(node, Add):
        left = flatten (node.left, stmtlist, discard)
        right = flatten (node.right, stmtlist, discard)
        if discard:
            return None
        varname = stmtlist.get_next_var()
        stmtlist.append(Assign([AssName(varname, 'OP_ASSIGN')], Add((left,right))))
        return Name(varname)
    elif isinstance(node, UnarySub):
        f = flatten(node.expr,stmtlist, discard)
        if discard:
            return None
        varname = stmtlist.get_next_var()
        stmtlist.append(Assign([AssName(varname, 'OP_ASSIGN')], UnarySub(f)))
        return Name(varname)
    elif isinstance(node, CallFunc):
        if discard:
            stmtlist.append(node)
            return None
        varname = stmtlist.get_next_var()
        stmtlist.append(Assign([AssName(varname, 'OP_ASSIGN')], node))
        return Name(varname)
    elif isinstance(node, Const):
        return node
    elif isinstance(node, Name):
        return node
    elif isinstance(node, AssName):
        stmtlist.add_var(node.assname)
        return node
    else:
        raise Exception('Unknown node: %s' % node.__class__)
    

def imm32_or_mem(arg, ctxt):
    if isinstance(arg,Const):
        return '$%s' % arg.value
    elif isinstance(arg,Name):
        if not ctxt.is_allocated(arg.name):
            raise Exception("Attempt to access an undefined variable '%s'" % arg.name)
        return '%s(%%ebp)' % ctxt.get_location(arg.name)
    else:
        raise Exception("Only constants or variables are supported: '%s'" % arg)    
