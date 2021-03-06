# Brent Smith
# CSCI5225
# HW2
# Lexer implementation
import ply.lex as lex

class P0Lexer:
    # reserved words.
    # this is suggested by the PLY documentation instead of having
    # separate tokens for each reserved word
    reserved = {
        'print' : 'PRINT',
        'input' : 'INPUT',
        'True' : 'TRUE',
        'False' : 'FALSE',
        'and' : 'AND',
        'or' : 'OR',
        'is' : 'IS',
        'if' : 'IF',        
        'else':'ELSE'
    }

    tokens = (
              'NOT',
              'LBRACKET',
              'RBRACKET',
              'LBRACE',
              'RBRACE',
              'EQUALITY',
              'NOTEQUALS',
              'COMMA',
              'COLON',
              'CONST',       # constant integer
              'NAME',        # identifier (variable or function name)
              'PLUS',        # addition operator (+)
              'EQUALS',      # assignment operator (=)
              'MINUS',       # negation operator (-)
              'LPAREN',      # (
              'RPAREN',      # )
              'NEWLINE',     # a new line to separate statements.
              'ENDMARKER',   # end of file
             ) + tuple(reserved.values())

    # whitespace
    t_ignore = ' \t'  # ignore space and horizontal tab

    # newline handling
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")
        t.type = 'NEWLINE'
        return t

    # error handling
    def t_error(self, t):
        print "Illegal character '%s'" % t.value[0]
        t.lexer.skip(1)

    # basic tokens
    t_PLUS    = r'\+'
    t_EQUALS  = r'='
    t_MINUS   = r'-'
    t_LPAREN  = r'\('
    t_RPAREN  = r'\)'
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'
    t_LBRACE = r'{'
    t_RBRACE = r'}'
    t_COLON = r':'
    t_EQUALITY = r'=='
    t_AND = r'and'
    t_OR = r'or'
    t_NOTEQUALS = r'!='
    t_IF = r'if'
    t_ELSE = r'else'
    t_COMMA = r','
    t_ignore_COMMENT = r'\#.*'
    t_TRUE = r'True'
    t_FALSE = r'False'
    t_NOT = r'not'
    # advanced tokens (defined as functions)

    # identifiers (names)
    def t_NAME(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        # assign the type attribute the value 'ID', unless the identifier is
        # in the list of reserved words, in which case we lookup the type in
        # the dictionary.
        t.type = self.reserved.get(t.value,'NAME')
        return t

    # constants (numeric)
    def t_CONST(self, t):
        r'\d+'
        try:
            t.value = int(t.value)
        except:
            print "Integer value too large: ", t.value
            t.value = 0
        return t

    # Build the lexer
    def build(self,**kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    # add an ENDMARKER at the very end of the token stream
    # this marks the end of the file
    def filter(self, add_endmarker=True):
        tokens = iter(self.lexer.token,None)
        for token in tokens:
            yield token

        if add_endmarker:
            token = lex.LexToken()
            token.type = 'ENDMARKER'
            token.value = None
            token.lineno = 0 
            token.lexpos = 0 
            yield token

    def input(self, data, add_endmarker=True):
        self.lexer.input(data)
        self.token_stream = self.filter(add_endmarker)

    # implement the token interface
    def token(self):
        try:
            return self.token_stream.next()
        except StopIteration:
            return None

    def __iter__(self):
        return self.token_stream

# main function
if __name__ == "__main__":
    import sys, compiler

    if len(sys.argv) < 2:
        print "Usage: %s <input-file> [input-files...]" % sys.argv[0]
        sys.exit(1)

    # build the lexer and run
    lexer = P0Lexer()
    lexer.build()

    for filename in sys.argv[1:]:
        f = open(filename, 'r')
        data = f.read()
        f.close()
        lexer.input(data)
        for token in lexer:
            print token
