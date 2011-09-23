'''
Created on Sep 22, 2011

@author: relsner
'''
from x86ir import *
# Concept borrowed from http://peter-hoffmann.com/2010/extrinsic-visitor-pattern-python-inheritance.html
class AssemblyVisitor(object):
    def __init__(self, nodes, ctxt):
        self.nodes = nodes
        self.ctxt = ctxt
        
    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        if not meth:
            meth = self.generic_visit
        return meth(node, *args, **kwargs)
    def get_reg_name(self, node):
        if isinstance(node, Var):
            if self.nodes[node.name].register is None:
                return '%s(%%ebp)'%self.ctxt.get_location(node.name)
            else:
                return self.nodes[node.name].register.x86name()
        elif isinstance(node, Const):
            return '$%d' % node.value
        elif isinstance(node, Pushl):
            return self.nodes[node.src.name].register.x86name()
        elif isinstance(node, Register):
            return node.x86name()
        elif isinstance(node, Negl):
            return self.get_reg_name(node.left)
        return '$%s' % type(node)
         
    def generic_visit(self, node, *args, **kwargs):
        return node
    def visit_Const(self, node, *args, **kwards):
        return '$%s' % node.value
    def visit_Move(self, node, *args, **kwargs):
        left = self.get_reg_name(node.left)
        right = self.get_reg_name(node.right)
        return '\tmovl %s, %s\n' % ( right, left ) #self.ctxt.get_location(assname))
    
    def visit_Addl(self, node, *args, **kwargs):
        left = ""
        right = ""
        left = self.get_reg_name(node.left) 
        right = self.get_reg_name(node.right)
            #imm32_or_mem(node.right, self.ctxt))
        return '\taddl %s, %s\n' % (left, right)
    def visit_Pushl(self, node, *args, **kwargs):
        return '\tpushl %s' % self.get_reg_name(node)
    def visit_Negl(self, node, *args, **kwargs):
        return '\tnegl %s' % self.get_reg_name(node)        
    #def visit_UnarySub(self, node, *args, **kwargs):
        # result of negation is in %eax
    #    return self.visit(node.expr).append(UnarySub(eax))
        
        #return '%s\tnegl %%eax\n' % (self.visit(node.expr))
    def visit_Call(self, node, *args, **kwargs):
        # result of function call is in %eax
        return '\tcall %s\n' % node.function
    #def visit_LoadRegister(self, node, *args, **kwargs):
        # constant has been moved into %eax
        #return [LoadRegister(node.value)]
        #return '\tmovl $%s, %%eax\n' % node.value
    #def visit_Name(self, node, *args, **kwargs):
    #    if not self.ctxt.is_allocated(node.name):
    #        raise Exception("Attempt to access an undefined variable '%s' %s" % (node.name, node))
        # variable has been moved into %eax
    #    return [LoadRegister(node.name)]
        #return '\tmovl %s(%%ebp), %%eax\n' % (self.ctxt.get_location(node.name))    