#! /usr/bin/python
# vim: set ts=4 sw=4 expandtab:
# Brent Smith <brent.m.smith@colorado.edu>
# Robert Elsner <robert.elsner@colorado.edu>
# CSCI5525, Fall 2011
import lexxer
import yakker

from comp_util import *
from types import *

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

class Register(object):
    def __init__(self, name):
        self.register_name = name
    def __str__(self):
        return "Register(%s)" % (self.register_name)
    def __repr__(self):
        return self.__str__()    
    def x86name(self):
        return '%%%s' % self.register_name

eax = Register('eax')
ebx = Register('ebx')
ecx = Register('ecx')
edx = Register('edx')
unk = Register('unk')

    
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
        return []
    def visit_Assign(self, node, *args, **kwargs):
        assname = node.nodes[0]
        expr = node.expr
        gen_code = []
        #if not self.ctxt.is_allocated(assname.name):
            #self.ctxt.allocate_var(assname.name)
        if isinstance(expr, Const) or isinstance(expr, Name):
            mvinst = Move(assname.name, expr)
        else:  
            mvinst = Move(assname.name, expr)
            #self.visit(expr)
            #mvinst = Move(assname.name, unk)
        gen_code.append(mvinst)
        return gen_code
        #return '%s\tmovl %%eax, %s(%%ebp)\n' % (, self.ctxt.get_location(assname.name))
        
    def visit_Printnl(self, node, *args, **kwargs):
        arg = node.nodes[0]
        return '%s\tpushl %%eax\n\tcall print_int_nl\n\taddl $4, %%esp\n' % (self.visit(arg))
    
    def visit_StatementList(self, node, *args, **kwargs):
        program = []
        for stmt in node:
            program.extend(self.visit(stmt))
         #'%s\n\t# %s\n%s' % (program, pretty(stmt), 
        return program
    
    def visit_Add(self, node, *args, **kwargs):
        print '*** %s '%node
        return Add(node.left, node.right)
        #return '%s\taddl %s,%%eax\n' % (self.visit(node.left), imm32_or_mem(node.right, self.ctxt))
    def visit_UnarySub(self, node, *args, **kwargs):
        # result of negation is in %eax
        return self.visit(node.expr).append(UnarySub(eax))
        
        #return '%s\tnegl %%eax\n' % (self.visit(node.expr))
    def visit_CallFunc(self, node, *args, **kwargs):
        # result of function call is in %eax
        return '\tcall input\n'
    def visit_Const(self, node, *args, **kwargs):
        # constant has been moved into %eax
        return LoadRegister(node.value)
        #return '\tmovl $%s, %%eax\n' % node.value
    def visit_Name(self, node, *args, **kwargs):
        if not self.ctxt.is_allocated(node.name):
            raise Exception("Attempt to access an undefined variable '%s' %s" % (node.name, node))
        
        # variable has been moved into %eax
        return LoadRegister(node.name)
        #return '\tmovl %s(%%ebp), %%eax\n' % (self.ctxt.get_location(node.name))

# Concept borrowed from http://peter-hoffmann.com/2010/extrinsic-visitor-pattern-python-inheritance.html
class AssemblyVisitor(object):
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
    def visit_Const(self, node, *args, **kwards):
        return '$%s' % node.value
    def visit_Move(self, node, *args, **kwargs):
        assname = node.lhs
        if not self.ctxt.is_allocated(assname):
            self.ctxt.allocate_var(assname)
        return '\tmovl %%eax, %s(%%ebp)\n' % ( self.ctxt.get_location(assname))
    
    def visit_Add(self, node, *args, **kwargs):
        return '\taddl %s, %%eax\n' % (imm32_or_mem(node.right, self.ctxt))
            
    #def visit_UnarySub(self, node, *args, **kwargs):
        # result of negation is in %eax
    #    return self.visit(node.expr).append(UnarySub(eax))
        
        #return '%s\tnegl %%eax\n' % (self.visit(node.expr))
    #def visit_CallFunc(self, node, *args, **kwargs):
        # result of function call is in %eax
    #    return '\tcall input\n'
    def visit_LoadRegister(self, node, *args, **kwargs):
        # constant has been moved into %eax
        #return [LoadRegister(node.value)]
        return '\tmovl $%s, %%eax\n' % node.value
    #def visit_Name(self, node, *args, **kwargs):
    #    if not self.ctxt.is_allocated(node.name):
    #        raise Exception("Attempt to access an undefined variable '%s' %s" % (node.name, node))
        # variable has been moved into %eax
    #    return [LoadRegister(node.name)]
        #return '\tmovl %s(%%ebp), %%eax\n' % (self.ctxt.get_location(node.name))        

class Move(object):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
    def __str__(self):
        return "movl %s %s" % (self.rhs, self.lhs)
    def __repr__(self):
        return self.__str__()
    
class Call(object):
    def __init__(self, func):
        self.function = func
    
class UnarySub(object):
    def __init__(self, expr):
        self.expression = expr
    def get_expression(self):
        return self.expression          
class Addl(object):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __str__(self):
        return "Add(%s,%s)" % (self.left, self.right)
    def __repr__(self):
        return self.__str__()
class Variable(object):
    def __init__(self, name, register):
        self.name = name
        self.register = register
    def __str__(self):
        return "Var(%s = %s)" % (self.register, self.name)
    def __repr__(self):
        return self.__str__()        
class LoadRegister(object):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "loooooad %s reg ?" % (self.value)
    def __repr__(self):
        return self.__str__()
        
        
class LiveNode(object):
    def __init__(self, node):
        self.node = node
        self.edges = []
        self.register = None
    def add_edge(self, other):
        self.edges.append(other)
    def assign_reg(self, reg):
        self.register = reg
    def __str__(self):
        return "connected to %s" % (str([x for x in self.edges]))
    def __repr__(self):
        return self.__str__()
                                  
                
        
def gen_live(statements):
    vars = []
    live_vars = set([])
    write_vars = set([])
    lafter = set([])
    for stmt in reversed(statements):
        read = set([])
        write = set([])
        if isinstance(stmt, Move):
            # write variable is the left hand side of a move statement
            write = set([stmt.lhs])
            
            # now decide if we have an add (to avoid inserting another temp var)
            if isinstance(stmt.rhs, Add):
                st = set([])
                # of any read variables
                if isinstance(stmt.rhs.right, Name):
                    st = st | set([stmt.rhs.right.name])
                if isinstance(stmt.rhs.left, Name):
                    st = st | set([stmt.rhs.left.name]) 
                read = read | st
        elif isinstance(stmt, LoadRegister):
            read = read | set([stmt.value])

        if len(vars)>0:
            lafter = vars.pop()
        else:
            lafter = set([])
        vars.append(lafter)
        lbefore = []
        lbefore = (lafter-write)|read
        vars.append(lbefore)
    #vars.pop()
    
#1 If instruction Ik is a move: movl s, t (and t 2 Lafter(k)), then
#  add the edge (t; v) for every v 2 Lafter(k) unless v = t or
#  v = s.
#2 If instruction Ik is not a move but some other arithmetic instruction such as addl s, t (and t 2 Lafter(k)), then add the
#  edge (t; v) for every v 2 Lafter(k).
#3 If instruction Ik is of the form call label, then add an edge
#  (r; v) for every caller-save register r and every variable v 2
#  Lafter(k). (The caller-save registers are eax, ecx, and edx.)
    
    nodes = {}
    found_nodes = []
    registers = set([eax,ebx,ecx, edx])
    instr_ctr = 0
    
    print 'vars %d statements %d' % (len(vars), len(statements))
    vars.pop()
    vars.reverse()
    
    for varset in vars:
        for var in varset:
            nodes[var] = LiveNode(var)
    print nodes
    for varset in vars:
        if isinstance(statements[instr_ctr], Move):
            mv = statements[instr_ctr]
            print 'checking %s with %s for statement %s' %(varset, mv.lhs, statements[instr_ctr])
            if mv.lhs not in varset:
                continue
            for var in varset:
                if mv.lhs != var:
                    if mv.lhs in nodes:
                        nodes[mv.lhs].add_edge(var)
                        nodes[var].add_edge(mv.lhs)
                    else:
                        nodes[mv.lhs] = LiveNode(mv.lhs)
                        nodes[mv.lhs].add_edge(var)
                        nodes[var].add_edge(mv.lhs)
                                                
                    print 'rule 1 applies statement %s variable %s statement %s' % (mv.lhs, var, statements[instr_ctr])
        if isinstance(statements[instr_ctr], Addl):
            print 'rule 2 applies %s' % statements[instr_ctr]

        instr_ctr = instr_ctr+1
    print nodes        
       
    for tuple in zip(statements, vars):
        print tuple
        
    
#http://www.cs.ucla.edu/~palsberg/paper/aplas05.pdf
if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    testcases = sys.argv[1:]
    for testcase in testcases:
        #f = open(testcase, 'r')
        #source = f.read()
        #f.close()
        #ast = yakker.parse(source, lexxer.getLex())
        ast = compiler.parseFile(testcase)
        stmtlist = StatementList()
        flatten(ast, stmtlist)

        visitor = Visitor(CompilerContext())
        output = visitor.visit(stmtlist)
        gen_live(output)
        
 #       assvis = AssemblyVisitor(visitor.ctxt)
 #       for stmt in output:
 #           print(assvis.visit(stmt))
        #outputfile = '%s.s' % testcase[:testcase.rfind('.')]
        #f = open(outputfile, 'w')
#        for stmt in output:
#            print stmt
        

#"""
#.globl main
#main:
#\tpushl %%ebp
#\tmovl %%esp, %%ebp
#\tsubl $%s,%%esp # make stack space for variables
#%s
#\tmovl $0, %%eax # put return value in eax
#\tleave
#\tret
#""" % (self.ctxt.get_stacksize(), program)