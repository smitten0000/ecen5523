# vim: set ts=4 sw=4 expandtab:
import compiler
from comp_util import *
from x86ir import *
from p1insselector import P1InstructionSelector


# Concept borrowed from http://peter-hoffmann.com/2010/extrinsic-visitor-pattern-python-inheritance.html
class P2InstructionSelector(P1InstructionSelector):
    '''Instruction selection for dynamic types as well as if, also converts an If node to Labels and Jumps'''
    def __init__(self, varalloc):
        P1InstructionSelector.__init__(self, varalloc)

    def transform(self, node):
        self.log.info('Starting instruction selection')
        ret = self.visit(node)
        self.log.info('Finished instruction selection')
        return ret

    def visit(self, node, *args, **kwargs):
        self.log.debug(node)
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        # we cannot blindly return the node itself, if there is no visit 
        # function for that type.  This is because the children of that node may need
        # to be recursed upon: ex.  Printnl(CallFuncIndirect(...))
        if not meth:
            raise Exception('Unknown node: %s method: %s' % (node.__class__, meth_name))
        return meth(node, *args, **kwargs)

    def visit_Function(self, node, *args, **kwargs):
        return x86Function(node.name, node.argnames, self.visit(node.code), node.lineno)

    def visit_Return(self, node, *args, **kwargs):
        retvar, stmtlist = self.visit(node.value)
        return stmtlist + [Ret(retvar)]

    def visit_CallFuncIndirect(self, node, *args, **kwargs):
        # need to create a temporary variable here to store the result.
        varname = self.varalloc.get_next_var()
        instructions = []
        # We have to generate a Pushl for each argument, but in reverse order to
        # be consistent with the cdecl calling convention.
        for x in reversed(node.args):
            var, instrlist = self.visit(x)
            instructions.extend(instrlist + [Pushl(var)])
        # Convert the CallFuncIndirect to a CallAddress() node in our x86IR
        instructions.extend([CallAddress(node.node)])
        # Move the result from the eax register to the new temp var.
        instructions.extend([Movl(Register('eax'),Var(varname))])
        # Generate an Addl instruction to restore the stack pointer
        instructions.extend([Addl(Imm32(4*len(node.args)), Register('esp'))])
        return (Var(varname), instructions)
    

if __name__ == "__main__":
    import sys
    import logging.config
    from p0parser import P0Parser
    from p2explicate import P2Explicate
    from p2uniquifyvars import P2UniquifyVars
    from p2heapify import P2Heapify
    from p2closureconvert import P2ClosureConversion
    from p2freevars import P2FreeVars
    from p2flattener import P2Flattener
    if len(sys.argv) < 2:
        sys.exit(1)
    # configure logging 
    logging.config.fileConfig('logging.cfg')
    testcases = sys.argv[1:]
    for testcase in testcases:
        varalloc = VariableAllocator()
        p2unique = P2UniquifyVars()
        p2explicator = P2Explicate(varalloc)
        p2heap = P2Heapify()
        p2closure = P2ClosureConversion(p2explicator, varalloc)
        p2flatten = P2Flattener(varalloc)
        p2insselector = P2InstructionSelector(varalloc)

        ast = compiler.parseFile(testcase)
        unique = p2unique.transform(ast)        
        explicated = p2explicator.explicate(unique)
        #heaped = p2heap.transform(explicated)
        astlist = p2closure.transform(explicated)
        for ast in astlist:
            ast = p2flatten.flatten(ast)
            ast = p2insselector.transform(ast)
            print '\nFunction\n================='
            print prettyAST(ast)
