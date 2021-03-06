# vim: set ts=4 sw=4 expandtab:

from x86ir import *
import logging

class P0StackAllocator(object):
    """ Class whose sole purpose is to replace Var instances with
    instances of StackSlot"""
    def __init__(self, program):
        self.program = program
        self.numvars = 0
        self.varmap = {}
        self.log = logging.getLogger('compiler.stackalloc')

    def allocate_var(self, varname):
        if self.is_allocated(varname):
            raise Exception("Variable '%s' already allocated" % varname)
        self.numvars = self.numvars + 1
        self.varmap[varname] = self.numvars

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

    def substitute(self):
        return self.visit(self.program)

    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        if not meth:
            raise Exception('Unknown node: %s method: %s' % (node.__class__, meth_name))
        self.log.debug(node)
        return meth(node, *args, **kwargs)

    def visit_Program(self, node, *args, **kwargs):
        return Program([self.visit(x) for x in node.statements])

    def visit_Statement(self, node, *args, **kwargs):
        return Statement([self.visit(x) for x in node.instructions],node.source)

    def visit_Movl(self, node, *args, **kwargs):
        if isinstance(node.dst, Var) and not self.is_allocated(node.dst.name):
            self.allocate_var(node.dst.name)
        return Movl(self.visit(node.src),self.visit(node.dst))
        
    def visit_Pushl(self, node, *args, **kwargs):
        return Pushl(self.visit(node.src))
    
    def visit_Addl(self, node, *args, **kwargs):
        return Addl(self.visit(node.src), self.visit(node.dst))

    def visit_Negl(self, node, *args, **kwargs):
        return Negl(self.visit(node.operand))

    def visit_Call(self, node, *args, **kwargs):
        return node

    def visit_Imm32(self, node, *args, **kwargs):
        return node

    def visit_Register(self, node, *args, **kwargs):
        return node

    def visit_Var(self, node, *args, **kwargs):
        if not self.is_allocated(node.name):
            raise Exception("Attempt to access an undefined variable '%s'" % node.name)
        # it's possible for a Variable to appear twice in the list of instructions:
        # E.g., 
        # 1. Movl(Var('tmp1'),...)
        # 2. Movl(...,Var('tmp1'))
        # So if the storage location is already assigned, do nothing.
        # If we wanted to be extra careful, we could just make sure the storage location
        # is the same as what is returned from get_location()
        if node.storage is None:
            node.storage = StackSlot(self.get_location(node.name))
        elif isinstance(node.storage, StackSlot):
            assert (node.storage == StackSlot(self.get_location(node.name)))
        else:
            raise Exception('Variable %s has unknown storage: %s ' % (node,node.storage))
        return node


if __name__ == "__main__":
    import sys
    from comp_util import *
    from p0parser import P0Parser
    from p0flattener import P0Flattener
    from p0insselector import P0InstructionSelector
    from p0regallocator import P0RegAllocator
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    for testcase in testcases:
        parser = P0Parser()
        parser.build()
        #ast = compiler.parseFile(testcase)
        ast = parser.parseFile(testcase)
        varalloc = VariableAllocator()
        p0flattener = P0Flattener(varalloc)
        stmtlist = p0flattener.flatten(ast)
        instruction_selector = P0InstructionSelector(varalloc)
        program = instruction_selector.visit(stmtlist)
        stackallocator = P0StackAllocator(program)
        print stackallocator.substitute()
