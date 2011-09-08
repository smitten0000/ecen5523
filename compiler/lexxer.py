
import lex as us
import yacc

tokens = ( 'PLUS', 'CONST', 'NAME', 'UNARYSUB', 'PRINT', 'EQUALS', 'LEFT_PAREN', 'RIGHT_PAREN', 'COMMENT', 'CALL')

t_PLUS = r'\+'

def t_CONST(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print "integer overflow", t.value
        t.value = 0
    return t

t_NAME = r'[a-zA-Z][a-zA-Z0-9]{0,}'

t_UNARYSUB = r'-'

t_PRINT = r'print'

t_EQUALS = r'='

t_LEFT_PAREN = r'\('

t_RIGHT_PAREN = r'\)'

t_ignore = ' \t'

t_COMMENT = r'\#.*$'

def t_CALL(t):
    r'[a-zA-Z][a-zA-Z0-9_]{0,}([ \t]+\([\t ,]*\))'
    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    
def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

us.lex()

us.input("print ()+5")
while True:
    tok = us.token()
    if not tok: break
    print tok

