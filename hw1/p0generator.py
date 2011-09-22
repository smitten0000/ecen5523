# vim: set ts=4 sw=4 expandtab:

from x86ir import *

class P0Generator(object):
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

    def generate(self, stmtlist):
        return self.visit(stmtlist)

    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        if not meth:
            raise Exception('Unknown node: %s method: %s' % (node.__class__, meth))
        return meth(node, *args, **kwargs)

    def visit_Program(self, node, *args, **kwargs):
        program = "\n".join([self.visit(x) for x in node.statements])
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
""" % (self.get_stacksize(), program)

    def visit_Statement(self, node, *args, **kwargs):
        return ("\t# %s\n" %  node.source) + "\n".join([self.visit(x) for x in node.instructions]) + "\n"

    def visit_Movl(self, node, *args, **kwargs):
        if isinstance(node.dst, Var) and not self.is_allocated(node.dst.name):
            self.allocate_var(node.dst.name)
        stmtlist=[]
        # handle memory to memory moves
        if isinstance(node.src,Var) and isinstance(node.dst, Var):
            stmtlist.append('\tmovl %s, %s' % (self.visit(node.src), self.visit(Register('eax'))))
            node.src = Register('eax')
        stmtlist.append('\tmovl %s, %s' % (self.visit(node.src), self.visit(node.dst)))
        return "\n".join(stmtlist)
        
    def visit_Pushl(self, node, *args, **kwargs):
        return '\tpushl %s' % (self.visit(node.src))
    
    def visit_Addl(self, node, *args, **kwargs):
        return '\taddl %s,%s' % (self.visit(node.src), self.visit(node.dst))

    def visit_Negl(self, node, *args, **kwargs):
        return '\tnegl %s' % (self.visit(node.operand))

    def visit_Call(self, node, *args, **kwargs):
        return '\tcall %s' % node.func

    def visit_Imm32(self, node, *args, **kwargs):
        return '$%s' % node.value

    def visit_Register(self, node, *args, **kwargs):
        return '%%%s' % node.name

    def visit_Var(self, node, *args, **kwargs):
        if not self.is_allocated(node.name):
            raise Exception("Attempt to access an undefined variable '%s'" % node.name)
        return '%s(%%ebp)' % (self.get_location(node.name))


if __name__ == "__main__":
    import sys
    from comp_util import *
    from p0parser import P0Parser
    from p0flattener import P0Flattener
    from p0insselector import P0InstructionSelector
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
        generator = P0Generator()
        print generator.generate(program)
        
