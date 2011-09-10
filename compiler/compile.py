#! /usr/bin/python
# vim: set ts=4 sw=4 expandtab:
# Brent Smith <brent.m.smith@colorado.edu>
# Robert Elsner <robert.elsner@colorado.edu>
# CSCI5525, Fall 2011
import lexxer
import yakker

from comp_util import *

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


# Concept borrowed from http://peter-hoffmann.com/2010/extrinsic-visitor-pattern-python-inheritance.html

class Visitor(object):
    def __init__(self, ctxt):
        self.ctxt = ctxt
        
    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)

        if not meth:
            meth = self.generic_visit
        return meth(node, *args, **kwargs)

    def generic_visit(self, node, *args, **kwargs):
        return ''
    def visit_Assign(self, node, *args, **kwargs):
        assname = node.nodes[0]
        expr = node.expr
        if not self.ctxt.is_allocated(assname.name):
            self.ctxt.allocate_var(assname.name)
        # here, we assume that the result of the expression is in %eax
        return '%s\tmovl %%eax, %s(%%ebp)\n' % (self.visit(expr), self.ctxt.get_location(assname.name))
        
    def visit_Printnl(self, node, *args, **kwargs):
        arg = node.nodes[0]
        return '%s\tpushl %%eax\n\tcall print_int_nl\n\taddl $4, %%esp\n' % (self.visit(arg))
    
    def visit_StatementList(self, node, *args, **kwargs):
        program = ""
        for stmt in node:
            program = '%s\n\t# %s\n%s' % (program, pretty(stmt), self.visit(stmt))
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
""" % (self.ctxt.get_stacksize(), program)
    
    def visit_Add(self, node, *args, **kwargs):
        return '%s\taddl %s,%%eax\n' % (self.visit(node.left), imm32_or_mem(node.right, self.ctxt))
    def visit_UnarySub(self, node, *args, **kwargs):
        # result of negation is in %eax
        return '%s\tnegl %%eax\n' % (self.visit(node.expr))
    def visit_CallFunc(self, node, *args, **kwargs):
        # result of function call is in %eax
        return '\tcall input\n'
    def visit_Const(self, node, *args, **kwargs):
        # constant has been moved into %eax
        return '\tmovl $%s, %%eax\n' % node.value
    def visit_Name(self, node, *args, **kwargs):
        if not self.ctxt.is_allocated(node.name):
            raise Exception("Attempt to access an undefined variable '%s' %s" % (node.name, node))
        # variable has been moved into %eax
        return '\tmovl %s(%%ebp), %%eax\n' % (self.ctxt.get_location(node.name))
   

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    testcases = sys.argv[1:]
    for testcase in testcases:
        f = open(testcase, 'r')
        source = f.read()
        ast = yakker.parse(source, lexxer.getLex())
        stmtlist = StatementList()
        flatten(ast, stmtlist)
        visitor = Visitor(CompilerContext())
        output = visitor.visit(stmtlist)
        outputfile = '%s.s' % testcase[:testcase.rfind('.')]
        f = open(outputfile, 'w')
        print >> f, output
        f.close()
