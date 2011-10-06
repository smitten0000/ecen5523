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
        '''Generate a cmp/je/jmp set with 0 for the else case (true is anything not 0) of an if statement'''
        test, then = node.tests[0]
        else_ = node.else_
        # perform instruction selection on the collection of statements in the "test" block
        testvar, teststmts = self.visit(test)
        # do the same for the statements in the "then" and "else" blocks
        # The difference for these is that they are encapsulated in a Stmt AST node, and therefore
        # there is no variable returned in this case, just a list of Statement nodes 
        # (see visit_Stmt in p0insselector.py)
        elsestmts = self.visit(else_)
        thenstmts = self.visit(then)
        # Now, generate the branches and jumps
        label = self.labelalloc.get_next_label()
        cmpvarname = self.varalloc.get_next_var()  
        stmts = []
        stmts.extend(teststmts)
        stmts.extend([Movl(Imm32(0), Var(cmpvarname)), 
                      Cmp(testvar, Var(cmpvarname)), 
                      JumpEquals('else%s' % label)])
        stmts.extend(thenstmts)
        stmts.append(Jump('end%s' % label))
        stmts.append(Label('else%s' % label))
        stmts.extend(elsestmts)
        stmts.append(Label('end%s' % label ))
        return stmts
    def visit_InjectFrom(self, node, *args, **kwargs):
        loc, stmtlist = self.visit(node.arg)
        # convert a simple value to a pyobj
        # pyobj inject_int(int i) { return (i << SHIFT) | INT_TAG; }
        # pyobj inject_bool(int b) { return (b << SHIFT) | BOOL_TAG; }
        if node.typ == 'int': tag = INT_TAG
        elif node.typ == 'bool': tag = BOOL_TAG
        elif node.typ == 'big': tag = BIG_TAG
        else:
            raise Exception("Unknown tag type '%s'" % node.typ)
        # need to create a temporary variable to store the result of the shift
        varname = self.varalloc.get_next_var()
        stmts = [Movl(loc,Var(varname)), 
                 BitShift(Var(varname), Imm32(TAG_SIZE), 'left'),
                 BitwiseOr(Var(varname), Imm32(tag))]
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
            stmts.extend([BitShift(Var(varname), Imm32(TAG_SIZE), 'right')])
        return (Var(varname), stmtlist + stmts)
    def visit_GetTag(self, node, *args, **kwargs):
        loc, stmtlist = self.visit(node.arg)
        # need to create a temporary variable to store the result of the shift
        varname = self.varalloc.get_next_var()
        # int tag(pyobj val) { return val & MASK; }
        return (Var(varname), stmtlist + [BitwiseAnd(loc, Imm32(3))])
    def visit_Or(self, node, *args, **kwargs):
        left,  leftstmtlist  = self.visit(node.nodes[0])
        right, rightstmtlist = self.visit(node.nodes[1])
        # need to create a temporary variable to store the result
        varname = self.varalloc.get_next_var()
        return (Var(varname), leftstmtlist + rightstmtlist + [BitwiseOr(left, right)])
    def visit_And(self, node, *args, **kwargs):
        left,  leftstmtlist  = self.visit(node.nodes[0])
        right, rightstmtlist = self.visit(node.nodes[1])
        # need to create a temporary variable to store the result
        varname = self.varalloc.get_next_var()
        return (Var(varname), leftstmtlist + rightstmtlist + [BitwiseAnd(left, right)])
    def visit_Printnl(self, node, *args, **kwargs):
        loc, stmtlist = self.visit(node.nodes[0])
        return stmtlist + [Pushl(loc),
                           Call('print_any'),
                           Addl(Imm32(4), Register('esp'))]


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
        for stmt in program.statements:
            print stmt
