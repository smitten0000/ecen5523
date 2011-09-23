#! /usr/bin/python
# vim: set ts=4 sw=4 expandtab:
# Brent Smith <brent.m.smith@colorado.edu>
# Robert Elsner <robert.elsner@colorado.edu>
# CSCI5525, Fall 2011
import lexxer
import yakker

debug = True    

from Assembler import AssemblyVisitor

from comp_util import *
from x86ir import *

eax = Register('eax')
ebx = Register('ebx')
ecx = Register('ecx')
edx = Register('edx')
unk = Register('unk')
esp = Register('esp')
edi = Register('edi')
esi = Register('esi')
ALL_REGS = [eax, ebx, ecx, edx, edi, esi]
CALLER_SAVE = [eax, ecx, edx]

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
    def next_var(self):
        var = 'tmp%d' % self.numvars
        self.numvars = self.numvars+1
        self.varmap[var] = -4 * self.numvars        
        return var
    def allocate_var(self, varname):
        if isinstance(varname, Register):
            return
        if self.is_allocated(varname):
            raise Exception("Variable '%s' already allocated" % varname)
        self.numvars = self.numvars + 1
        self.varmap[varname] = -4 * self.numvars
        if debug:
            print 'Stored vars: %s'%self.varmap
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
        return []
    def visit_Assign(self, node, *args, **kwargs):
        assname = node.nodes[0].name
        expr = node.expr
        gen_code = []
        #if not self.ctxt.is_allocated(assname.name):
            #self.ctxt.allocate_var(assname.name)
        loc, stmt = self.visit(expr)
        gen_code.append(stmt)
        return stmt + [Move(Var(assname), loc)]
        #return '%s\tmovl %%eax, %s(%%ebp)\n' % (, self.ctxt.get_location(assname.name))
        
    def visit_Printnl(self, node, *args, **kwargs):
        arg = node.nodes[0]
        var, stmt = self.visit(arg)
        return stmt + [Pushl(var), Call('print_int_nl'), Addl(Const(4), esp)]
        #return '%s\tpushl %%eax\n\tcall print_int_nl\n\taddl $4, %%esp\n' % (self.visit(arg))
    
    def visit_StatementList(self, node, *args, **kwargs):
        program = []
        for stmt in node:
            program.extend(self.visit(stmt))
         #'%s\n\t# %s\n%s' % (program, pretty(stmt), 
        return program
    
    def visit_Add(self, node, *args, **kwargs):
        varname = self.ctxt.next_var()
        left, leftstmt = self.visit(node.left)
        right, rightstmt = self.visit(node.right)
        return (Var(varname), leftstmt + rightstmt + [Move(Var(varname), right), Addl(left, Var(varname))])
        #return '%s\taddl %s,%%eax\n' % (self.visit(node.left), imm32_or_mem(node.right, self.ctxt))
    def visit_UnarySub(self, node, *args, **kwargs):
        loc, stmtlist = self.visit(node.expr)
        # need to create a temporary variable here to store the result.
        varname = self.ctxt.next_var()
        tmpvar = Var(varname)
        return (tmpvar, stmtlist + [Move(loc, tmpvar), Negl(tmpvar)])
    def visit_CallFunc(self, node, *args, **kwargs):
        varname = self.ctxt.next_var()
        return (Var(varname), [Call('input'), Move(eax,Var(varname))])
    def visit_Const(self, node, *args, **kwargs):
        return (Const(node.value), [])
    def visit_Name(self, node, *args, **kwargs):
        if not self.ctxt.is_allocated(node.name):
            self.ctxt.allocate_var(node.name)
        
        return (Var(node.name), [])

        
class LiveNode(object):
    def __init__(self, node):
        self.node = node
        self.edges = set([])
        self.register = None
        self.color = None
    def add_edge(self, other):
        if self.node == other:
            return
        self.edges = self.edges | set([other])
    def assign_reg(self, reg):
        self.register = reg
    def __str__(self):
        return "connected to %s, on reg %s" % (str([x.node for x in self.edges]), self.register)
    def __repr__(self):
        return self.__str__()
                                  

        
def gen_live(statements):
    vars = []
    live_vars = set([])
    write_vars = set([])
    lafter = set([])
    if debug:
        print statements
    for stmt in reversed(statements):
        read = set([])
        write = set([])
        if isinstance(stmt, Move):
            if not isinstance(stmt.left, Const):
                # write variable is the left hand side of a move statement
                if isinstance(stmt.left, Register):
                    write = set([stmt.left])
                else:
                    write = set([stmt.left.name])
            st = set([])
            # of any read variables
            if not isinstance(stmt.left, Const):
                if isinstance(stmt.right, Var):
                    st = st | set([stmt.right.name])
                    read = read | st
        elif isinstance(stmt, Var):
            read = read | set([stmt.value])
        elif isinstance(stmt, Addl):
            if isinstance(stmt.left, Var):
                read = read | set([stmt.left.name])
            if isinstance(stmt.right, Var):
                read = read | set([stmt.right.name])
        elif isinstance(stmt, Pushl):
            read = read | set([stmt.src.name])
  
        if len(vars)>0:
            lafter = vars.pop()
        else:
            lafter = set([])
        vars.append(lafter)
        lbefore = []
        lbefore = (lafter-write)|read
        vars.append(lbefore)
    
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
    if debug:
        print 'vars %d statements %d' % (len(vars), len(statements))
    vars.pop()
    vars.reverse()
    if debug:
        print vars
    for varset in vars:
        for var in varset:
            nodes[var] = LiveNode(var)
            
    for reg in ALL_REGS:
        nodes[reg] = LiveNode(reg)
        
    
    for varset in vars:
        if debug:
            print varset
        if isinstance(statements[instr_ctr], Move):
            mv = statements[instr_ctr]
            varname = None
            if isinstance(mv.left, Var):
                varname = mv.left.name
            if varname not in varset:
                continue
            for var in varset:
                nodes[mv.left.name].add_edge(nodes[var])
                nodes[var].add_edge(nodes[mv.left.name])
        if isinstance(statements[instr_ctr], (Addl, Negl)):
            mv = statements[instr_ctr]
            for var in varset:
                nodes[mv.left.name].add_edge(nodes[var])
                nodes[var].add_edge(nodes[mv.left.name])
        if isinstance(statements[instr_ctr], Call):
            for var in varset:
                for reg in CALLER_SAVE:
                    nodes[var].add_edge(nodes[reg])
                    nodes[reg].add_edge(nodes[var])
                            
        instr_ctr = instr_ctr+1
    return nodes
    
def assign_registers(nodes, ctxt):
#http://arman.boyaci.ca/a-matlab-implementation-of-greedy-dsatur-coloring-algorithm/
#http://www.math.tu-clausthal.de/Arbeitsgruppen/Diskrete-Optimierung/publications/2002/gca.pdf
#http://www.ic.unicamp.br/~rberga/papers/p251-brelaz.pdf
    high_deg = None
    high_cnt = -999
    for key in nodes.keys():
        node = nodes[key]
        if len(node.edges) > high_cnt:
            high_cnt = len(node.edges)
            high_deg = node
    copy = nodes.copy()
    
    registers = [x for x in ALL_REGS]
    
    while len(copy):
        maxsat_node = max_sat(copy)
        if len(registers) > 0:
            if not isinstance(maxsat_node.node, Register):
                maxsat_node.register = registers.pop()
        copy.pop(maxsat_node.node)
    for val in nodes.values():
        if val.register is None:
            if not isinstance(maxsat_node.node, Register):
                if not ctxt.is_allocated(val.node):
                    ctxt.allocate_var(val.node)
    if debug:            
        for val in nodes.values():
            print 'node %s register %s' % (val.node, val.register)

def max_sat(nodes):
    max_sat = -999
    max_node = None
    for key in nodes.keys():
        sat = saturation(nodes[key])
        if sat > max_sat:
            max_sat = sat
            max_node = nodes[key]
    return max_node 
        
        
def saturation(node):
    sat = set([])
    for onode in node.edges:
        if isinstance(onode, Register):
            sat = sat | set([onode])
        elif onode.register is not None: # this node is "colored" or assigned a register
            sat = sat | set([onode])
    return len(sat)
    
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
        ctxt = CompilerContext()
        visitor = Visitor(ctxt)
        output = visitor.visit(stmtlist)
        nodes = gen_live(output)
        assign_registers(nodes, ctxt)
        if debug:
            print nodes
        assemblyVis = AssemblyVisitor(nodes, ctxt)
        outputfile = '%s.s' % testcase[:testcase.rfind('.')]
        f = open(outputfile, 'w')
       
        print >> f,"""
.globl main
main:
\tpushl %%ebp
\tmovl %%esp, %%ebp
\tsubl $%s,%%esp # make stack space for variables
""" % (ctxt.get_stacksize())
        for stmt in output:
            print >> f, assemblyVis.visit(stmt)
        print >> f,"""
\tmovl $0, %eax # put return value in eax
\tleave
\tret        
"""
        f.close()   
 #       assvis = AssemblyVisitor(visitor.ctxt)
 #       for stmt in output:
 #           print(assvis.visit(stmt))
        #outputfile = '%s.s' % testcase[:testcase.rfind('.')]
        #f = open(outputfile, 'w')
#        for stmt in output:
#            print stmt
        
#""" % (self.ctxt.get_stacksize(), program)