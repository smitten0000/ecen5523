# vim: set ts=4 sw=4 expandtab:

from comp_util import *
from x86ir import *
# to flatten nested lists into a flat list
from compiler.ast import flatten
from p2ifinsselector import P2IfInstructionSelector

# Concept borrowed from http://peter-hoffmann.com/2010/extrinsic-visitor-pattern-python-inheritance.html
class P3IfInstructionSelector(P2IfInstructionSelector):
    def __init__(self, varalloc, labelalloc):
        P2IfInstructionSelector.__init__(self, varalloc, labelalloc)

    # same as visit_Statement in P1IfInstructionSelector
    def visit_x86While(self, node, *args, **kwargs):
        label = self.labelalloc.get_next_label()
        stmts = []
        stmts.append(Label('while_start%s' % label))
        stmts.extend(self.visit(node.test[1]))
        stmts.extend([Cmp(Imm32(0),node.test[0]),
                      JumpEquals('while_end%s' % label)])
        stmts.extend(self.visit(node.body))
        stmts.append(Jump('while_start%s' % label))
        stmts.append(Label('while_end%s' % label))
        return stmts
    

if __name__ == "__main__":
    import sys, compiler
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
            print '\nFunction\n================='
            print prettyAST(program)
