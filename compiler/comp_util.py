# vim: set ts=4 sw=4 expandtab:

from compiler.ast import *

class VariableAllocator:
    """Provides context allocating variables by storing a set
    of currently used variables and the next variable number"""
    def __init__(self, varnum=0, varset=set()):
        self.varnum = varnum
        self.varset = varset

    def add_var(self, varname):
        self.varset.add(varname)

    def get_next_var(self):
        done = False
        while not done:
            varname = 'tmp%d' % self.varnum
            self.varnum = self.varnum + 1
            if varname not in self.varset:
                done = True
        self.add_var(varname)
        return varname

    def is_allocated(self, varname):
        return varname in self.varset

    def __str__(self):
        return 'VariableAllocator(%s,%s)' % (self.varnum, self.varset)


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
