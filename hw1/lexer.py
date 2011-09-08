# Brent Smith
# CSCI5225
# HW2
# Lexer implementation

# reserved words.
# this is suggested by the PLY documentation instead of having
# separate tokens for each reserved word
reserved = {
    'print' : 'PRINT',
    'input' : 'INPUT',
}

tokens = ('CONST',       # constant integer
          'NAME',        # identifier (variable or function name)
          'PLUS',        # addition operator (+)
          'EQUALS',      # assignment operator (=)
          'MINUS',       # negation operator (-)
          'LPAREN',      # (
          'RPAREN',      # )
          'NEWLINE',     # a new line to separate statements.
         ) + tuple(reserved.values())

# whitespace
t_ignore = ' \t'  # ignore space and horizontal tab

# newline handling
def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")
    t.type = 'NEWLINE'
    return t

# error handling
def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

# basic tokens
t_PLUS    = r'\+'
t_EQUALS  = r'='
t_MINUS   = r'-'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_ignore_COMMENT = r'\#.*'

# advanced tokens (defined as functions)

# identifiers (names)
def t_NAME(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    # assign the type attribute the value 'ID', unless the identifier is
    # in the list of reserved words, in which case we lookup the type in
    # the dictionary.
    t.type = reserved.get(t.value,'NAME')
    return t

# constants (numeric)
def t_CONST(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except:
        print "Integer value too large: ", t.value
        t.value = 0
    return t

# start of parser
from compiler.ast import *

# precedence
precedence = (
    ('nonassoc','PRINT'),
    ('left','PLUS'),
    ('left','MINUS')
)

def p_module(p):
    r'module : statements'
    p[0] = Module(None,p[1])

def p_empty(p):
    r'empty : '

def p_statements(p):
    r'''statements : empty
                   | NEWLINE
                   | statement 
                   | statements statement'''
    if len(p) > 2:
        p[0] = Stmt(p[1].nodes + [p[2]])
    else:
        if p[1] is None:
            p[0] = Stmt([])
        elif p[1] == '\n':
            p[0] = Stmt([])
        else:
            p[0] = Stmt([p[1]])

def p_statement_print(p):
    r'statement : PRINT expression NEWLINE'
    p[0] = Printnl([p[2]], None)

def p_statement_assign(p):
    r'statement : NAME EQUALS expression NEWLINE'
    p[0] = Assign([AssName(p[1],'OP_ASSIGN')],p[3])

def p_statement_expr(p):
    r'statement : expression NEWLINE'
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
    raise SyntaxError("Syntax error in input!")


# main function
if __name__ == "__main__":
    import sys
    import ply.lex as lex
    import ply.yacc as yacc
    import compiler

    red = "\033[31m"
    green = "\033[32m"
    reset = "\033[0m"

    # build the lexer and run
    lexer = lex.lex()
    parser = yacc.yacc()
    #lex.runmain()

    if len(sys.argv) < 2:
        print "Usage: %s <input-file> [input-files...]" % sys.argv[0]
        sys.exit(1)

    for filename in sys.argv[1:]:
        f = open(filename, 'r')
        data = f.read()
        f.close()
        #lexer.input(data)
        #for token in lexer:
        #    print token
        try:
            result1 = str(parser.parse(data))
        except:
            result1 = 'failed parse'
        try:
            result2 = str(compiler.parse(data))
        except:
            result2 = 'failed parse'
        if result1 == result2:
            print "%-30s [%s%s%s]" % (filename, green, 'OK', reset)
        else:
            print "%-30s [%s%s%s]" % (filename, red, 'FAIL', reset)
            print result1 
            print result2
