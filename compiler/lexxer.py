import lex as us

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
          'EOF',   # end of file
         ) + tuple(reserved.values())

# whitespace
t_ignore = ' \t\r'  # ignore space and horizontal tab

# newline handling
def t_newline(t):
    r'[\n\r]+'
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


def getLex():
    return us.lex()



        
        
    

