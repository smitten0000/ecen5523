from x86ir import *
from p2generator import P2Generator 

class P3Generator(P2Generator):
    def __init__(self, allowMem2Mem=True):
        P2Generator.__init__(self, allowMem2Mem)
        self.labelcnt = 1
        self.labelstrlist = []

    def get_next_str_label(self, string):
        label = '.str%s' % self.labelcnt
        self.labelstrlist.append((label,string))
        self.labelcnt = self.labelcnt + 1
        return label

    def get_string_decls(self):
        decls=[]
        for label, string in self.labelstrlist:
            decls.append('%s:\n\t.string "%s"' % (label, string))
        # this is kind of nasty to introduce a side effect like this,
        # but we don't want to print out duplicate strings if this
        # generator is used again (for example to print out top-level
        # function definitions)
        self.labelstrlist=[]
        return "\n".join(decls)

    # override to handle string constants
    def visit_Imm32(self, node, *args, **kwargs):
        if isinstance(node.value,str) and not node.value.startswith('glob_fun'):
            return '$%s' % self.get_next_str_label(node.value)
        else:
            return '$%s' % node.value

    # overridden to add string constants at beginning
    def visit_Program(self, node, *args, **kwargs):
        programbody = P2Generator.visit_Program(self,node)
        return self.get_string_decls() + programbody

    # overridden to add string constants at beginning
    def visit_x86Function(self, node, *args, **kwargs):
        funcbody = P2Generator.visit_x86Function(self,node)
        return self.get_string_decls() + funcbody
    

if __name__ == "__main__":
    import sys, compiler
    import logging.config
    from comp_util import *
    from p3declassify import P3Declassify
    from p3uniquifyvars import P3UniquifyVars
    from p3explicate import P3Explicate
    from p3heapify import P3Heapify
    from p3closureconvert import P3ClosureConversion
    from p3flattener import P3Flattener
    from p3insselector import P3InstructionSelector
    from p2stackallocator import P2StackAllocator
    from p3regallocator import P3RegAllocator
    from p3ifinsselector import P3IfInstructionSelector
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        varalloc = VariableAllocator()
        declassify = P3Declassify(varalloc)
        unique = P3UniquifyVars()
        explicator = P3Explicate(varalloc)
        heap = P3Heapify(explicator)
        closure = P3ClosureConversion(explicator, varalloc)
        flatten = P3Flattener(varalloc)
        insselector = P3InstructionSelector(varalloc)
        ifinsselector = P3IfInstructionSelector(varalloc,insselector.labelalloc)
        generator = P3Generator(True)

        ast = compiler.parseFile(testcase)
        ast = declassify.transform(ast)
        ast = unique.transform(ast)
        ast = explicator.explicate(ast)
        ast = heap.transform(ast)
        astlist = closure.transform(ast)
        for ast in astlist:
            ast = flatten.flatten(ast)
            program = insselector.transform(ast)
            allocator = P2StackAllocator(program)
#            allocator = P3RegAllocator(program, varalloc)
            program = allocator.substitute()
            program = ifinsselector.visit(program)
            print generator.generate(program)
