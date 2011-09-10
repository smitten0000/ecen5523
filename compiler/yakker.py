from compiler.ast import *
from lexxer import tokens
import yacc

# precedence
precedence = (
    ('nonassoc','PRINT'),
    ('left','PLUS'),
    ('left','MINUS')
)

def p_module(p):
    r'module : statements'
    p[0] = Module(None,p[1])

def p_statements(p):
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

def p_endofstmt(p):
    r'''endofstmt : EOF
                  | NEWLINE
                  | NEWLINE EOF'''
    return None

def p_statement_print(p):
    r'''statement : PRINT expression'''
    p[0] = Printnl([p[2]], None)

def p_statement_assign(p):
    r'''statement : NAME EQUALS expression'''
    p[0] = Assign([AssName(p[1],'OP_ASSIGN')],p[3])

def p_statement_expr(p):
    r'''statement : expression'''
    p[0] = Discard(p[1])

def p_expression_const(p):
    r'expression : CONST'
    p[0] = Const(p[1])

def p_expression_name(p):
    r'expression : NAME'
    p[0] = Name(p[1])

def p_expression_add(p):
    r'expression : expression PLUS expression'
    p[0] = Add((p[1],p[3]))

def p_expression_unarysub(p):
    r'expression : MINUS expression'
    p[0] = UnarySub(p[2])

def p_expression_input(p):
    r'expression : INPUT LPAREN RPAREN'
    p[0] = CallFunc(Name('input'),[])

def p_expression_paren(p):
    r'expression : LPAREN expression RPAREN'
    p[0] = p[2]

# Error rule for syntax errors
def p_error(p):
    raise SyntaxError(p)
    


def parse(source, lex):
    parser = yacc.yacc()
    
    return parser.parse(source, lexer=lex, debug=0)
