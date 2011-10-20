# vim: set ts=4 sw=4 expandtab:

from compiler.ast import *
import itertools,heapq
from p1explicate import *

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


class priorityq:
    """ Priority queue abstraction, with the ability to reprioritize
    a given task and invalidate a task.  Taken from the python
    documentation here: http://docs.python.org/library/heapq.html
    Modified slightly."""
    INVALID = -1            # special const to mark an entry as deleted
    def __init__(self):
        self.pq = []                      # the priority queue list
        self.counter = itertools.count(1) # unique sequence count
        self.task_finder = {}             # mapping of tasks to entries

    def add_task(self, priority, task, count=None):
        if count is None:
            count = next(self.counter)
        entry = [priority, count, task]
        self.task_finder[task] = entry
        heapq.heappush(self.pq, entry)

    def get_top_priority(self):
        while True:
            priority, count, task = heapq.heappop(self.pq)
            if count is not priorityq.INVALID:
                del self.task_finder[task]
                return priority, task

    def delete_task(self, task):
        entry = self.task_finder[task]
        entry[1] = priorityq.INVALID

    def reprioritize(self, priority, task):
        entry = self.task_finder[task]
        self.add_task(priority, task, entry[1])
        entry[1] = priorityq.INVALID

    def incr_priority(self, task, inc=1):
        entry = self.task_finder[task]
        self.reprioritize(entry[0]-inc, task)


def prettyIndent(node,depth=0,indent='  '):
    """Given an AST node, print out a human readable form."""
    space=indent*depth
    ret = space
    if isinstance(node, Printnl):
        if node.dest is not None:
            ret = ret + 'print >> %s, %s' % (node.dest, pretty(node.nodes[0]))
        else:
            ret = ret + 'print %s' % (pretty(node.nodes[0]))
    elif isinstance(node, Assign):
        ret = ret + '%s = %s' % (pretty(node.nodes[0]), pretty(node.expr))
    elif isinstance(node, Discard):
        pass
    elif isinstance(node, CallFunc):
        if node.args is not None and len(node.args) > 0:
            ret = ret + '%s(%s)' % (pretty(node.node), node.args)
        else:
            ret = ret + '%s()' % (node.node)
    elif isinstance(node, Add):
        ret = ret + '%s + %s' % (pretty(node.left), pretty(node.right))
    elif isinstance(node, UnarySub):
        ret = ret + '- %s' % (pretty(node.expr))
    elif isinstance(node, Const):
        ret = ret + str(node.value)
    elif isinstance(node, Name):
        ret = ret + node.name
    elif isinstance(node, AssName):
        ret = ret + str(node.name)
    elif isinstance(node, Not):
        ret = ret + 'Not(%s)' % node.expr
    elif isinstance(node, If):
        ret = ret +         'If(%s):\n%s\n' % (node.tests[0][0], 
                                               '\n'.join([pretty(x,depth+1) for x in node.tests[0][1]]))
        ret = ret + space + 'Else:\n%s'     % ('\n'.join([pretty(x,depth+1) for x in node.else_]))
    elif isinstance(node, ProjectTo):
        ret = ret + 'ProjectTo(%s,%s)' % (node.typ, pretty(node.arg))
    elif isinstance(node, InjectFrom):
        ret = ret + 'InjectFrom(%s,%s)' % (node.typ, pretty(node.arg))
    elif isinstance(node, GetTag):
        ret = ret + 'GetTag(%s)' % (pretty(node.arg))
    elif isinstance(node, Or):
        ret = ret + 'Or(%s,%s)' % (pretty(node.nodes[0]), pretty(node.nodes[1]))
    elif isinstance(node, And):
        ret = ret + 'And(%s,%s)' % (pretty(node.nodes[0]), pretty(node.nodes[1]))
    elif isinstance(node, Compare):
        return 'Compare(%s, %s, %s)' % (node.expr, node.ops[0][0], node.ops[0][1])
    else:
        raise Exception('Unknown node: %s' % node.__class__)
    return ret

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
    elif isinstance(node, (CallFunc,CallFuncIndirect)):
        if node.args is not None and len(node.args) > 0:
            return '%s(%s)' % (pretty(node.node), node.args)
        else:
            return '%s()' % (node.node)
    elif isinstance(node, Add):
        return '%s + %s' % (pretty(node.left), pretty(node.right))
    elif isinstance(node, UnarySub):
        return '- %s' % (pretty(node.expr))
    elif isinstance(node, Const):
        return str(node.value)
    elif isinstance(node, Name):
        return node.name
    elif isinstance(node, AssName):
        return str(node.name)
    elif isinstance(node, Not):
        return 'Not(%s)' % node.expr
    elif isinstance(node, If):
        return 'If(%s) %s Else %s' % (node.tests[0][0], node.tests[0][1], node.else_)
    elif isinstance(node, ProjectTo):
        return 'ProjectTo(%s,%s)' % (node.typ, pretty(node.arg))
    elif isinstance(node, InjectFrom):
        return 'InjectFrom(%s,%s)' % (node.typ, pretty(node.arg))
    elif isinstance(node, GetTag):
        return 'GetTag(%s)' % (pretty(node.arg))
    elif isinstance(node, Or):
        return 'Or(%s,%s)' % (pretty(node.nodes[0]), pretty(node.nodes[1]))
    elif isinstance(node, And):
        return 'And(%s,%s)' % (pretty(node.nodes[0]), pretty(node.nodes[1]))
    elif isinstance(node, Compare):
        return 'Compare(%s, %s, %s)' % (node.expr, node.ops[0][0], node.ops[0][1])
    elif isinstance(node, Function):
        return 'Function_%s(%s)' % (node.name, ",".join(x for x in node.argnames))
    elif isinstance(node, Return):
        return 'Return(%s)' % (node.value)
    else:
        raise Exception('Unknown node: %s: %s' % (node.__class__, node))

def prettyAST(node, depth=0, indent='  '):
    if node is None:
        ret = '%sNone' % (indent*depth)
    # handle the "leaf" nodes as special cases to make the output easier to read
    elif isinstance(node, (Const,Name,Var,Register,Instruction)):
        ret = '%s%s' % (indent*depth, node)
    # somewhat hackish; ideally these nodes would be defined in a p1ast.py file
    # and we could include that at the top...  Better yet, define a visitor for
    # each language definition and extend it.  But this works for now.
    elif node.__class__.__name__ in ('GetTag','ProjectTo'):
        ret = '%s%s' % (indent*depth, node)
    elif isinstance(node,(str,int,list,tuple)):
        ret = "%s%s" % (indent*depth, node)
    elif isinstance(node, Node):
        ret = '%s%s(\n' % (indent*depth, node.__class__.__name__)
        children = node.getChildren()
        if children is not None:
            ret = ret + ',\n'.join([prettyAST(x,depth+1) for x in children])
        ret = ret + '\n%s)' % (indent*depth)
    else:
        raise Exception('Encountered unhandled AST Node (%s)', node.__class__.__name__)
    return ret

def free_vars(n):
    if isinstance(n, Add):
        return free_vars(n.left) | free_vars(n.right)
    elif isinstance(n, UnarySub):
        return free_vars(n.expr)
    elif isinstance(n, CallFunc):
        # the name of the function being called should be considered "free" (n.node)
        return free_vars(n.node) | reduce(lambda x,y: x+y, [free_vars(x) for x in n.args], set([]))
    elif isinstance(n, Const):
        return set([])
    elif isinstance(n, Name):
        if n.name == 'True' or n.name == 'False':
            return set([])
        return set([n.name])
    elif isinstance(n, (Or,And)):
        return free_vars(n.nodes[0]) + free_vars(n.nodes[1])
    elif isinstance(n, IfExp):
        return free_vars(n.test) | free_vars(n.then) | free_vars(n.else_)
    elif isinstance(n, List):
        return reduce(lambda x,y: x|y, [free_vars(x) for x in n.nodes], set([]))
    elif isinstance(n, Dict):
        keys = reduce(lambda x,y: x|y, [free_vars(x[0]) for x in n.items], set([]))
        values = reduce(lambda x,y: x|y, [free_vars(x[1]) for x in n.items], set([])) 
        return keys | values
    elif isinstance(n, Compare):
        return free_vars(n.ops[0][1]) | free_vars(n.expr)
    elif isinstance(n, Not):
        return free_vars(n.expr)
    elif isinstance(n, Subscript):
        return free_vars(n.expr) | free_vars(n.subs[0])
    elif isinstance(n, Lambda):
        return free_vars(n.code) - set(n.argnames)
    else:
        raise Exception('Unhandled expression: "%s"' % n)

class CallFuncIndirect(Node):
    def __init__(self, node, args, star_args = None, dstar_args = None, lineno=None):
        self.node = node
        self.args = args
        self.star_args = star_args
        self.dstar_args = dstar_args
        self.lineno = lineno

    def getChildren(self):
        children = []
        children.append(self.node)
        children.extend(flatten(self.args))
        children.append(self.star_args)
        children.append(self.dstar_args)
        return tuple(children)

    def getChildNodes(self):
        nodelist = []
        nodelist.append(self.node)
        nodelist.extend(flatten_nodes(self.args))
        if self.star_args is not None:
            nodelist.append(self.star_args)
        if self.dstar_args is not None:
            nodelist.append(self.dstar_args)
        return tuple(nodelist)

    def __repr__(self):
        return "CallFuncIndirect(%s, %s, %s, %s)" % (repr(self.node), repr(self.args), repr(self.star_args), repr(self.dstar_args))
