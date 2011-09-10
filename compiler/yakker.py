import yacc

from compiler.ast import Printnl, Add, Const, CallFunc, Assign, AssName, Stmt, Module, Discard, Name, UnarySub

from lexxer import tokens


precedence = (
    ('nonassoc', 'CONST', 'NEWLINE'),
    ('left','PLUS', 'UNARYSUB', 'PRINT')
    )

def p_module(t):
    '''module : statements'''
    t[0] = Module([],t[1])
def p_statements(t):
    '''statements : statement
                  | statements statement'''
    if len(t) == 3:
        l = t[1].nodes
        l.append(t[2])
        t[0] = Stmt(l)
    elif len(t)==2:
        t[0] = Stmt([t[1]])
    else:
        t[0] = Stmt([])
def p_empty(t):
    r'''statement : COMMENT NEWLINE
              | NEWLINE'''
    pass
       
def p_print_statement(t):
    '''statement  : PRINT expression NEWLINE
                  | PRINT expression'''
    if len(t) == 4:
        t[0] = Printnl([t[2]], [])
    else:
        t[0] = Printnl([], [])

def p_unarysub_expression(t):
    '''expression : UNARYSUB expression'''
    t[0] = UnarySub(t[2])
    
def p_plus_expression(t):
    '''expression : expression PLUS expression'''
    t[0] = Add([t[1], t[3]])

def p_paren(t):
    '''expression : LEFT_PAREN expression RIGHT_PAREN'''
    t[0] = t[2]

def p_equals_statement(t):
    '''statement : NAME EQUALS expression NEWLINE'''
    t[0] = Assign([AssName(t[1], 'OP_ASSIGN')], t[3])

def p_name_statement(t):
    '''expression : NAME'''
    t[0] = Name(t[1])
       
def p_const_expression(t):
    '''expression : CONST'''
    t[0] = Const(t[1])
    
def p_statement_expr(t):
    '''statement : expression NEWLINE'''
    t[0] = Discard(t[1])
    
def p_input_expression(t):
    '''expression : INPUT LEFT_PAREN RIGHT_PAREN'''
    t[0] = CallFunc(Name('input'),[])
    
def p_comment_expression(t):
    '''expression : expression COMMENT'''
    t[0] = t[1]

    
def p_error(t):
    print "Syntax error at '%s'" % t


def parse(source, lex):
    parser = yacc.yacc()
    return parser.parse(source, lexer=lex)
