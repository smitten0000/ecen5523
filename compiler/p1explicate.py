# vim: set ts=4 sw=4 expandtab:

from comp_util import *
from x86ir import *

class GetTag(Node):
    def __init__(self, arg):
        self.arg = arg
class InjectFrom(Node):
    def __init__(self, typ, arg):
        self.typ = typ
        self.arg = arg
class ProjectTo(Node):
    def __init__(self, typ, arg):
        self.typ = typ
        self.arg = arg
class Let(Node):
    def __init__(self, var, rhs, body):
        self.var = var
        self.rhs = rhs
        self.body = body


# Concept borrowed from http://peter-hoffmann.com/2010/extrinsic-visitor-pattern-python-inheritance.html
class P1Explicate(object):
    def __init__(self, varalloc):
        self.varalloc = varalloc

    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        # we return the node passed in by default so we do not have to handle
        # every case unless necessary
        if not meth:
            return node
        return meth(node, *args, **kwargs)


if __name__ == "__main__":
    import sys
    from p0parser import P0Parser
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    for testcase in testcases:
        parser = P0Parser()
        parser.build()
        #ast = compiler.parseFile(testcase)
        ast = parser.parseFile(testcase)
        varalloc = VariableAllocator()
        explc = P1Explicate()
        
        print explc.visit(ast) 
