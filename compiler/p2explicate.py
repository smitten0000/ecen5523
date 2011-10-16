from compiler.ast import *
from comp_util import *
from x86ir import *
import logging

from p1explicate import P1Explicate


class P2Explicate(P1Explicate):
    def __init__(self, varalloc):
        P1Explicate.__init__(self, varalloc)
        self.log = logging.getLogger('explicate')
            
    def visit_Function(self, node, *args, **kwargs):
        #Function: decorators, name, argnames, defaults, flags, doc, code
        #Lamba: argnames, defaults, flags, code
        #Assign([AssName(retvar,'OP_ASSIGN')], CallFunc(Name('set_subscript'),[expr,subexpr,valueexpr]))
        return Assign([AssName(node.name, 'OP_ASSIGN')], Lambda(node.argnames, node.defaults, node.flags, node.code))

    def visit_Lambda(self, node, *args, **kwargs):
        #Lamba: argnames, defaults, flags, code
        return Lambda(node.argnames, node.defaults, node.flags, Return(node.code))


if __name__ == "__main__":
    # create logger
    log = logging.getLogger('explicate')
    log.setLevel(logging.DEBUG)
    
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # add formatter to ch
    ch.setFormatter(formatter)
    
    # add ch to logger
    log.addHandler(ch)
    import sys, compiler
    from p0parser import P0Parser
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    for testcase in testcases:
        #parser = P0Parser()
        #parser.build()
        ast = compiler.parseFile(testcase)
        #ast = parser.parseFile(testcase)
        p2explicator = P2Explicate(VariableAllocator())
        print prettyAST(p2explicator.explicate(ast))
        