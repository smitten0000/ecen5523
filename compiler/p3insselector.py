# vim: set ts=4 sw=4 expandtab:
import compiler
from comp_util import *
from x86ir import *
from p2insselector import P2InstructionSelector


# Concept borrowed from http://peter-hoffmann.com/2010/extrinsic-visitor-pattern-python-inheritance.html
class P3InstructionSelector(P2InstructionSelector):
    '''Instruction selection for dynamic types as well as if, also converts an If node to Labels and Jumps'''
    def __init__(self, varalloc):
        P2InstructionSelector.__init__(self, varalloc)

    def visit_While(self, node, *args, **kwargs):
        # need to create a temporary variable here to store the result.
        # test[0] has type Name()
        # test[1] has type Stmt()
        # body has type Stmt()
        testvar, dummy = self.visit(node.test[0])
        teststmts = self.visit(node.test[1])
        bodystmts = self.visit(node.body)
        teststmts = reduce(lambda x,y: x+y, [x.instructions for x in teststmts], [])
        bodystmts = reduce(lambda x,y: x+y, [x.instructions for x in bodystmts], [])
        return [x86While((testvar,teststmts),bodystmts,[],node.lineno)]


if __name__ == "__main__":
    import sys
    import logging.config
    
    from p3declassify import P3Declassify
    from p3wrapper import P3Wrapper
    from p3uniquifyvars import P3UniquifyVars
    from gcflattener import GCFlattener
    from gcrefcount import GCRefCount
    from p3explicate import P3Explicate
    from p3heapify import P3Heapify
    from p3closureconvert import P3ClosureConversion
    from p3freevars import P3FreeVars
    from p3flattener import P3Flattener
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        varalloc = VariableAllocator()
        declassify = P3Declassify(varalloc)
        unique = P3UniquifyVars()
        wrapper = P3Wrapper()
        gcflatten = GCFlattener(varalloc, True)
        gcrefcount = GCRefCount(varalloc)
        explicator = P3Explicate(varalloc, handleLambdas=False)
        heap = P3Heapify(explicator)
        closure = P3ClosureConversion(explicator, varalloc)
        flatten = P3Flattener(varalloc)
        insselector = P3InstructionSelector(varalloc)

        ast = compiler.parseFile(testcase)
        ast = declassify.transform(ast)
        ast = wrapper.transform(ast)
        ast = unique.transform(ast)        
        ast = gcflatten.transform(ast)        
        ast = gcrefcount.transform(ast)        
        ast = explicator.explicate(ast)
        ast = heap.transform(ast)
        astlist = closure.transform(ast)
        for ast in astlist:
            ast = flatten.flatten(ast)
            ast = insselector.transform(ast)
            print '\nFunction\n================='
            print prettyAST(ast)
