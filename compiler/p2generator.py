from x86ir import *
from p1generator import P1Generator 

class P2Generator(P1Generator):
    def __init__(self, allowMem2Mem=True):
        P1Generator.__init__(self, allowMem2Mem)
    
    def visit_CallAddress(self, node, *args, **kwargs):
        return '\tcall *%s' %  self.visit(node.address)    

    def visit_Ret(self, node, *args, **kwargs):
        return '''
\tpopl %%ebx\n
\tpopl %%edi\n
\tpopl %%esi\n
\tmovl %s,%%eax\n
\tleave\n\tret
''' %  self.visit(node.value)    

    def visit_x86Function(self, node, *args, **kwargs):
        function = "\n".join([self.visit(x) for x in node.statements])
        return """
%s:
\tpushl %%ebp
\tmovl %%esp, %%ebp
\tsubl $%s,%%esp # make stack space for variables
\tpushl %%esi
\tpushl %%edi
\tpushl %%ebx

%s
\tmovl $0, %%eax # put return value in eax
\tleave
\tret
""" % (node.name, self.get_stacksize(), function)

    def visit_StackSlot(self, node, *args, **kwargs):
        return '%s(%%ebp)' % (node.slot * -4)

    
if __name__ == "__main__":
    import sys, compiler
    import logging.config
    from comp_util import *
    from p2uniquifyvars import P2UniquifyVars
    from p2explicate import P2Explicate
    from p2heapify import P2Heapify
    from p2closureconvert import P2ClosureConversion
    from p2flattener import P2Flattener
    from p2insselector import P2InstructionSelector
    from p2regallocator import P2RegAllocator
    from p2ifinsselector import P2IfInstructionSelector
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        varalloc = VariableAllocator()
        p2unique = P2UniquifyVars()
        p2explicator = P2Explicate(varalloc)
        #p2heap = P2Heapify()
        p2closure = P2ClosureConversion(p2explicator, varalloc)
        p2flatten = P2Flattener(varalloc)
        p2insselector = P2InstructionSelector(varalloc)
        ifinsselector = P2IfInstructionSelector(varalloc,p2insselector.labelalloc)
        p2generator = P2Generator(False)

        ast = compiler.parseFile(testcase)
        unique = p2unique.transform(ast)        
        explicated = p2explicator.explicate(unique)
        #heaped = p2heap.transform(explicated)
        astlist = p2closure.transform(explicated)
        for ast in astlist:
            ast = p2flatten.flatten(ast)
            program = p2insselector.transform(ast)
            p2regallocator = P2RegAllocator(program, varalloc)
            program = p2regallocator.substitute()
            program = ifinsselector.visit(program)
            print p2generator.generate(program)
