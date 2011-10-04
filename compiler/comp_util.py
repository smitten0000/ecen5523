# vim: set ts=4 sw=4 expandtab:

from compiler.ast import *
import itertools,heapq

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
            count = next(counter)
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
    elif isinstance(node, Not):
        return 'Not(%s)' % node.expr
    elif isinstance(node, If):
        return 'If(%s) then %s else %s' % (node.tests[0][0], node.tests[0][1].nodes[0:-1], node.else_)
    else:
        print node
        raise Exception('Unknown node: %s' % node.__class__)
