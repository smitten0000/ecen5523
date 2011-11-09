from x86ir import *
from p2generator import P2Generator 

class P3Generator(P2Generator):
    def __init__(self, allowMem2Mem=True):
        P2Generator.__init__(self, allowMem2Mem)
    
if __name__ == "__main__":
    import sys, compiler
    import logging.config
    from comp_util import *
    from p3uniquifyvars import P3UniquifyVars
    from p3explicate import P3Explicate
    from p3heapify import P3Heapify
    from p3closureconvert import P3ClosureConversion
    from p3flattener import P3Flattener
    from p3insselector import P3InstructionSelector
    from p3regallocator import P3RegAllocator
    from p3ifinsselector import P3IfInstructionSelector
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        varalloc = VariableAllocator()
        unique = P3UniquifyVars()
        explicator = P3Explicate(varalloc)
        heap = P3Heapify(explicator)
        closure = P3ClosureConversion(explicator, varalloc)
        flatten = P3Flattener(varalloc)
        insselector = P3InstructionSelector(varalloc)
        ifinsselector = P3IfInstructionSelector(varalloc,insselector.labelalloc)
        generator = P3Generator(False)

        ast = compiler.parseFile(testcase)
        unique = unique.transform(ast)
        explicated = explicator.explicate(unique)
        heaped = heap.transform(explicated)
        astlist = closure.transform(heaped)
        for ast in astlist:
            ast = flatten.flatten(ast)
            program = insselector.transform(ast)
            regallocator = P3RegAllocator(program, varalloc)
            program = regallocator.substitute()
            program = ifinsselector.visit(program)
            print generator.generate(program)
