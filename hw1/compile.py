#/usr/bin/python
# vim: set ts=4 sw=4 expandtab:
# Brent Smith <brent.m.smith@colorado.edu>
# Robert Elsner <robert.elsner@colorado.edu>
# CSCI5525, Fall 2011
# HW1
import compiler, sys, os
from compiler.ast import *

class StatementList(list):
    """Class to encapsulate a list of statements and the next unused 
variable number"""
    def __init__(self, varnum=0):
        self.varnum = 0
        self.vardict = {}
    def __repr__(self):
        return "\n".join([str(x) for x in self])
        #return "\n".join([pretty(x) for x in self])
    def add_var(self, varname):
        self.vardict[varname] = True
    def get_next_var(self):
        done = False
        while not done:
            varname = 'tmp%d' % self.varnum
            self.varnum = self.varnum + 1
            if varname not in self.vardict or not self.vardict[varname]:
                done = True
        self.vardict[varname] = True
        return varname

class CompilerContext:
    def __init__(self):
        self.numvars = 0
        self.varmap = {}
    def allocate_var(self, varname):
        if self.is_allocated(varname):
            raise Exception("Variable '%s' already allocated" % varname)
        self.numvars = self.numvars + 1
        self.varmap[varname] = -4 * self.numvars
    def is_allocated(self, varname):
        if varname in self.varmap:
            return True
        return False
    def get_location(self, varname):
        if not self.is_allocated(varname):
            raise Exception("Variable '%s' is not allocated" % varname)
        return self.varmap[varname]
    def get_stacksize(self):
        return self.numvars*4


def imm32_or_mem(arg, ctxt):
    if isinstance(arg,Const):
        return '$%s' % arg.value
    elif isinstance(arg,Name):
        if not ctxt.is_allocated(arg.name):
            raise Exception("Attempt to access an undefined variable '%s'" % arg.name)
        return '%s(%%ebp)' % ctxt.get_location(arg.name)
    else:
        raise Exception("Only constants or variables are supported: '%s'" % arg)


def generate_assembly(node, ctxt):
    if isinstance(node, StatementList):
        program = ""
        for stmt in node:
            program = '%s\n\t# %s\n%s' % (program, pretty(stmt), generate_assembly(stmt, ctxt))
        return """
.globl main
main:
\tpushl %%ebp
\tmovl %%esp, %%ebp
\tsubl $%s,%%esp # make stack space for variables
%s
\tmovl $0, %%eax # put return value in eax
\tleave
\tret
""" % (ctxt.get_stacksize(), program)
    elif isinstance(node, Printnl):
        arg = node.nodes[0]
        return '%s\tpushl %%eax\n\tcall print_int_nl\n\taddl $4, %%esp\n' % (generate_assembly(arg,ctxt))
    elif isinstance(node, Assign):
        assname = node.nodes[0]
        expr = node.expr
        if not ctxt.is_allocated(assname.name):
            ctxt.allocate_var(assname.name)
        # here, we assume that the result of the expression is in %eax
        return '%s\tmovl %%eax, %s(%%ebp)\n' % (generate_assembly(expr, ctxt), ctxt.get_location(assname.name))
    elif isinstance(node, Add):
        # result of addition is in %eax
        return '%s\taddl %s,%%eax\n' % (generate_assembly(node.left,ctxt), imm32_or_mem(node.right,ctxt))
    elif isinstance(node, UnarySub):
        # result of negation is in %eax
        return '%s\tnegl %%eax\n' % (generate_assembly(node.expr,ctxt))
    elif isinstance(node, CallFunc):
        # result of function call is in %eax
        return '\tcall input\n'
    elif isinstance(node, Const):
        # constant has been moved into %eax
        return '\tmovl $%s, %%eax\n' % node.value
    elif isinstance(node, Name):
        if not ctxt.is_allocated(node.name):
            raise Exception("Attempt to access an undefined variable '%s'" % node.name)
        # variable has been moved into %eax
        return '\tmovl %s(%%ebp), %%eax\n' % (ctxt.get_location(node.name))
    else:
        print node
        raise Exception('Unknown node: %s' % node.__class__)


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
        print node
        raise Exception('Unknown node: %s' % node.__class__)
    

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: %s <testcase> [testcases...]"
        sys.exit(1)

    testcases = sys.argv[1:]
    for testcase in testcases:
        ast = compiler.parseFile(testcase)
        stmtlist = StatementList()
        flatten(ast, stmtlist)
        #code = '%s' % stmtlist
        #eval(compile(code,'test.txt','exec'))
        output = generate_assembly(stmtlist, CompilerContext())
        outputfile = '%s.s' % testcase[:testcase.rfind('.')]
        f = open(outputfile, 'w')
        print >> f, output
        f.close()
