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

    def p_endofstmt(self, p):
        r'''endofstmt : ENDMARKER
                      | NEWLINE
                      | NEWLINE ENDMARKER'''
        return None

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
