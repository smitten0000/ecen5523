'''
Created on Oct 8, 2011

@author: relsner
'''
from comp_util import *
from x86ir import *

class SpillVisitor(object):

    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        if not meth:
            return None
        return meth(node, *args, **kwargs)
    
    def visit_Movl(self, node, *args, **kwargs):
        src = node.src
        dst = node.dst
        if isinstance(src,StackSlot) and isinstance(dst,StackSlot):
            return node
        
    def visit_Addl(self, node, *args, **kwargs):
        src = node.src
        dst = node.dst
        if isinstance(src,StackSlot) and isinstance(dst,StackSlot):
            return None

