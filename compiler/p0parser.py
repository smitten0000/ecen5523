# vim: set ts=4 sw=4 expandtab:
# start of parser
from compiler.ast import *
from p0lexer import P0Lexer
import ply.yacc as yacc

class P0Parser:
    # precedence
    precedence = (
        ('nonassoc','PRINT'),
        ('left','PLUS'),
        ('left','MINUS')
    )

    def __init__(self):
        self.lexer = P0Lexer()
        self.lexer.build()
        self.tokens = self.lexer.tokens

    def p_module(self, p):
        r'module : statements'
        p[0] = Module(None,p[1])
    
    def p_empty(self, p):
        r'''empty : '''
    
    def p_statements(self, p):
        r'''statements : endofstmt
                       | statement endofstmt
                       | statements endofstmt
                       | statements statement endofstmt'''
        if len(p) == 4:
            p[0] = Stmt(p[1].nodes + [p[2]])
        elif len(p) == 3:
            if isinstance(p[1], Stmt):
                p[0] = p[1]
            else:
                p[0] = Stmt([p[1]])
        else:
            p[0] = Stmt([])
    
#    def p_subscription(self, p):
#        r'''subscription : expression LBRACE expression RBRACE'''
#        
#    def p_expression_subscription(self, p):
#        r'''expression : subscription'''
#        
    
    
            
    def p_dict(self, p):
        r'''expression : LBRACE key_datum_list RBRACE'''
        p[0] = Dict(p[2])
        
    def p_keydatum(self, p):
        r'''key_datum : expression COLON expression'''
        p[0] = (p[1], p[3]) 
    def p_keydatum_list(self, p):
        r'''key_datum_list : empty
                           | key_datum
                           | key_datum key_datum_list'''
        if len(p) == 2:
            p[0] = Dict([p[1]])
        else:
            p[0] = Dict([p[1]]+p[2].items)
        
    def p_endofstmt(self, p):
        r'''endofstmt : ENDMARKER
                      | NEWLINE
                      | NEWLINE ENDMARKER'''
        return None

    def p_expression_notequals(self, p):
        r'''expression : expression NOTEQUALS expression'''
        p[0] = Compare('!=', [p[1],p[3]])
        
    def p_expression_equality(self, p):
        r'''expression : expression EQUALITY expression'''
        p[0] = Compare('==', [p[1],p[3]])

    def p_expression_or(self, p):
        r'''expression : expression OR expression'''
        p[0] = Or(p[1], p[3])
    def p_expression_and(self, p):
        r'''expression : expression AND expression'''
        p[0] = And(p[1], p[3])

    def p_expression_if(self, p):
        r'''expression : expression IF expression ELSE expression'''
        p[0] = IfExp(p[3], p[1], p[5])

    def p_expression_is(self, p):
        r'''expression : expression IS expression'''
        p[0] = Compare('is', p[1], p[3])

    def p_expression_list(self, p):
        r'''expression : LBRACKET expr_list RBRACKET'''
        p[0] = List(p[2])
        
    def p_expr_list(self,p):
        r'''expr_list : empty
                      | expression
                      | expression COMMA expression'''
        if len(p) == 2:
            p[0] = [p[1]]
        elif len(p) == 4:
            p[0] = [p[1],p[3]].flatten()
            
    def p_expression_not(self, p):
        r'''expression : NOT expression'''
        p[0] = Not(p[2])

    def p_statement_print(self, p):
        r'''statement : PRINT expression'''
        p[0] = Printnl([p[2]], None)

    def p_statement_assign(self, p):
        r'''statement : NAME EQUALS expression'''
        p[0] = Assign([AssName(p[1],'OP_ASSIGN')],p[3])

    def p_statement_expr(self, p):
        r'''statement : expression'''
        p[0] = Discard(p[1])

    def p_expression_const(self, p):
        r'expression : CONST'
        p[0] = Const(p[1])

    def p_expression_name(self, p):
        r'expression : NAME'
        p[0] = Name(p[1])

    def p_expression_add(self, p):
        r'expression : expression PLUS expression'
        p[0] = Add((p[1],p[3]))

    def p_expression_unarysub(self, p):
        r'expression : MINUS expression'
        p[0] = UnarySub(p[2])

    def p_expression_input(self, p):
        r'expression : INPUT LPAREN RPAREN'
        p[0] = CallFunc(Name('input'),[])

    def p_expression_paren(self, p):
        r'expression : LPAREN expression RPAREN'
        p[0] = p[2]
    
    def p_expression_boolean_true(self, p):
        r'''expression : TRUE'''
        p[0] = Const(1)
        
    def p_expression_boolean_false(self, p):
        r'''expression : FALSE'''
        p[0] = Const(0)    
        
    def p_target(self,p):
        r'''target : NAME
                   | subscription'''
        p[0] = p[1]
        
    def p_target_statement(self, p):
        r'''statement : target EQUALS expression'''
        Assign([AssName(p[1],'OP_ASSIGN')],p[3])
        
    # Error rule for syntax errors
    def p_error(self, p):
        raise SyntaxError(p)

    def build(self, **kwargs):
        self.parser = yacc.yacc(module=self, **kwargs)

    def parse(self, data):
        return self.parser.parse(data, lexer=self.lexer, debug=0)

    def parseFile(self, filename):
        f = open(filename,'r')
        data = f.read()
        f.close()
        return self.parse(data)

# main function
if __name__ == "__main__":
    import sys, compiler

    if len(sys.argv) < 2:
        print "Usage: %s <input-file> [input-files...]" % sys.argv[0]
        sys.exit(1)

    # build the lexer and run
    pars = P0Parser()
    pars.build()

    for filename in sys.argv[1:]:
        f = open(filename, 'r')
        data = f.read()
        f.close()
        print str(pars.parse(data))
