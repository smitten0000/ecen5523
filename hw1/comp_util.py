# vim: set ts=4 sw=4 expandtab:

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
