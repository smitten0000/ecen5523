# vim: set ts=4 sw=4 expandtab:
import compiler
from comp_util import *
from x86ir import *
from p0insselector import P0InstructionSelector

TAG_SIZE = 2
INT_TAG = 0
BOOL_TAG = 1
BIG_TAG = 3

class LabelAllocator(object):
    def __init__(self):
        self.count = 0
        
    def get_next_label(self):
        label= '_label_%s' % self.count
        self.count= self.count+1
        return label


# Concept borrowed from http://peter-hoffmann.com/2010/extrinsic-visitor-pattern-python-inheritance.html
class P1InstructionSelector(P0InstructionSelector):
    '''Instruction selection for dynamic types as well as if, also converts an If node to Labels and Jumps'''
    def __init__(self, varalloc):
        P0InstructionSelector.__init__(self, varalloc)
        self.labelalloc = LabelAllocator()
    def visit_Not(self, node, *args, **kwargs):
        (var, stmt) = self.visit(node.expr)
        return stmt+[BitwiseNot(var)]
    def visit_Compare(self, node, *args, **kwargs):
        stmts = []
        lhsvar, lhs = self.visit(node.expr)
        rhsvar, rhs = self.visit(node.ops[0][1])
        result = Var(self.varalloc.get_next_var())
        # take care of any necessary flattening for the statements
        # but there should be none at this point
        stmts = stmts + lhs + rhs
        label = self.labelalloc.get_next_label()
        # we have decided that explicate will convert a comparison between
        # a bool and an integer to a cast of the int to a bool (using an If
        # statement to check if the int value == 0 -> false, else true)
        # so we can blindly do a cmp
        # default case gets 2 out of 3 operations
        thenval = Imm32(0)
        elseval = Imm32(1)
        if node.ops[0][0] == '==':            
            None
        elif node.ops[0][0]== '!=':
            thenval = Imm32(1)
            elseval = Imm32(0)
        else: #is
            None
        stmts = stmts + [Cmp(lhsvar, rhsvar),JumpEquals('else%s'%label),Movl(thenval, result),Jump('end%s'%label),Label('else%s'%label), Movl(elseval,result),Label('end%s'%label)]
        return (result, stmts)
    def visit_If(self, node, *args, **kwargs):
        # test has type Name()
        # then has type Stmt()
        # else_ has type Stmt()
        test, then = node.tests[0]
        else_ = node.else_
        # perform instruction selection for statements in the "then" and "else" blocks
        # These are encapsulated in a Stmt AST node, and therefore there is no variable
        # returned in this case, just a list of Statement nodes 
        # (see visit_Stmt in p0insselector.py)
        elsestmts = self.visit(else_)
        thenstmts = self.visit(then)
        # get rid of the pesky Statement nodes
        elsestmts = reduce(lambda x,y: x+y, [x.instructions for x in elsestmts], [])
        thenstmts = reduce(lambda x,y: x+y, [x.instructions for x in thenstmts], [])
        # encapsulate the flattened code into an If again.
        return [x86If(Var(test.name), thenstmts, elsestmts)]
    def visit_InjectFrom(self, node, *args, **kwargs):
        loc, stmtlist = self.visit(node.arg)
        # convert a simple value to a pyobj
        # pyobj inject_int(int i) { return (i << SHIFT) | INT_TAG; }
        # pyobj inject_bool(int b) { return (b << SHIFT) | BOOL_TAG; }
        # pyobj inject_big(big_pyobj* p) { assert((((long)p) & MASK) == 0); return ((long)p) | BIG_TAG; }
        if node.typ == 'int': tag = INT_TAG
        elif node.typ == 'bool': tag = BOOL_TAG
        elif node.typ == 'big': tag = BIG_TAG
        else:
            raise Exception("Unknown tag type '%s'" % node.typ)
        # need to create a temporary variable to store the result of the shift
        varname = self.varalloc.get_next_var()
        stmts = [Movl(loc,Var(varname))]
        # only shift left if we are converting from an int or bool
        if node.typ == 'int' or node.typ == 'bool':
            stmts.extend([BitShift(Imm32(TAG_SIZE), Var(varname), 'left')])
        stmts.extend([BitwiseOr(Imm32(tag),Var(varname))])
        return (Var(varname), stmtlist + stmts)
    def visit_ProjectTo(self, node, *args, **kwargs):
        # int project_int(pyobj val) { assert((val & MASK) == INT_TAG); return val >> SHIFT; }
        # int project_bool(pyobj val) { assert((val & MASK) == BOOL_TAG); return val >> SHIFT; }
        # big_pyobj* project_big(pyobj val) { assert((val & MASK) == BIG_TAG); return (big_pyobj*)(val & ~MASK); }
        loc, stmtlist = self.visit(node.arg)
        # need to create a temporary variable to store the result of the shift
        varname = self.varalloc.get_next_var()
        # only shift to the right if we are converting to int or bool
        stmts = [Movl(loc,Var(varname))]
        if node.typ == 'int' or node.typ == 'bool':
            stmts.extend([BitShift(Imm32(TAG_SIZE), Var(varname), 'right')])
        else:
            stmts.extend([BitwiseAnd(Imm32(~3), Var(varname))])
        return (Var(varname), stmtlist + stmts)
    def visit_GetTag(self, node, *args, **kwargs):
        loc, stmtlist = self.visit(node.arg)
        # need to create a temporary variable to store the result of the shift
        varname = self.varalloc.get_next_var()
        # int tag(pyobj val) { return val & MASK; }
        return (Var(varname), stmtlist + [Movl(loc,Var(varname)), BitwiseAnd(Imm32(3), Var(varname))])
    def visit_Or(self, node, *args, **kwargs):
        left,  leftstmtlist  = self.visit(node.nodes[0])
        right, rightstmtlist = self.visit(node.nodes[1])
        # need to create a temporary variable to store the result
        varname = self.varalloc.get_next_var()
        return (Var(varname), leftstmtlist + rightstmtlist + [Movl(left, Var(varname)), BitwiseOr(right, Var(varname))])
    def visit_And(self, node, *args, **kwargs):
        left,  leftstmtlist  = self.visit(node.nodes[0])
        right, rightstmtlist = self.visit(node.nodes[1])
        # need to create a temporary variable to store the result
        varname = self.varalloc.get_next_var()
        return (Var(varname), leftstmtlist + rightstmtlist + [Movl(left, Var(varname)), BitwiseAnd(right, Var(varname))])
    # overridden from p0insselector.py to use print_any instead of print_int_nl
    def visit_Printnl(self, node, *args, **kwargs):
        loc, stmtlist = self.visit(node.nodes[0])
        return stmtlist + [Pushl(loc),
                           Call('print_any'),
                           Addl(Imm32(4), Register('esp'))]

    # overridden from p0insselector.py to allow for arguments to CallFunc
    def visit_CallFunc(self, node, *args, **kwargs):
        # need to create a temporary variable here to store the result.
        varname = self.varalloc.get_next_var()
        instructions = []
        # We have to generate a Pushl for each argument, but in reverse order to
        # be consistent with the cdecl calling convention.
        for x in reversed(node.args):
            var, instrlist = self.visit(x)
            instructions.extend(instrlist + [Pushl(var)])
        # Convert the CallFunc to a Call() node in our x86IR
        instructions.extend([Call(node.node.name)])
        # Move the result from the eax register to the new temp var.
        instructions.extend([Movl(Register('eax'),Var(varname))])
        # Generate an Addl instruction to restore the stack pointer
        instructions.extend([Addl(Imm32(4*len(node.args)), Register('esp'))])
        return (Var(varname), instructions)


if __name__ == "__main__":
    import sys
    from p0parser import P0Parser
    from p1flattener import P1Flattener
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    for testcase in testcases:
        #parser = P0Parser()
        #parser.build()
        #ast = parser.parseFile(testcase)
        ast = compiler.parseFile(testcase)
        
        varalloc = VariableAllocator()
        explicator = P1Explicate(varalloc)
        ast = explicator.explicate(ast)
        flattener = P1Flattener(varalloc)
        stmtlist = flattener.flatten(ast)
        instruction_selector = P1InstructionSelector(varalloc)
        program = instruction_selector.visit(stmtlist)
        print program
        print prettyAST(program)
