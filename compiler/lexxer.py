
import lex as us
reserved = {
   'print' : 'PRINT',
   'input' : 'INPUT'
}

tokens = [ 'NEWLINE', 'PLUS', 'CONST', 'NAME', 'UNARYSUB',  'EQUALS', 'LEFT_PAREN', 'RIGHT_PAREN', 'COMMENT']+list(reserved.values())
#'NAME',
t_PLUS = r'\+'

def t_CONST(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print "integer overflow", t.value
        t.value = 0
    return t

#def t_CALL(t):
#    r'[a-zA-Z][a-zA-Z0-9_]{0,}([ \t]+\([\t ,]*\))'
#    return t

def t_NAME(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value,'NAME')    # Check for reserved words
    return t

t_UNARYSUB = r'-'

t_EQUALS = r'='

t_LEFT_PAREN = r'\('

t_RIGHT_PAREN = r'\)'

t_ignore = ' \t'

t_COMMENT = r'\#.*'

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.type = 'NEWLINE'
    return t
    
def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

def getLex():
    return us.lex()


