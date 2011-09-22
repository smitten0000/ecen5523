#! /usr/bin/python
# vim: set ts=4 sw=4 expandtab:
# Brent Smith <brent.m.smith@colorado.edu>
# Robert Elsner <robert.elsner@colorado.edu>
# CSCI5525, Fall 2011
# HW1

import sys
from p0parser import P0Parser
from p0flattener import P0Flattener
from p0insselector import P0InstructionSelector
from p0generator import P0Generator
from comp_util import *

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    testcases = sys.argv[1:]
    for testcase in testcases:
        parser = P0Parser()
        parser.build()
        #ast = compiler.parseFile(testcase)
        ast = parser.parseFile(testcase)
        p0flattener = P0Flattener()
        stmtlist = p0flattener.flatten(ast)
        #code = '%s' % stmtlist
        #eval(compile(code,'test.txt','exec'))
        print stmtlist
        #visitor = Visitor(CompilerContext())
        #output = visitor.visit(stmtlist)
        instruction_selector = P0InstructionSelector()
        program = instruction_selector.visit(stmtlist)
        print program
        generator = P0Generator()
        print generator.generate(program)
        #outputfile = '%s.s' % testcase[:testcase.rfind('.')]
        #f = open(outputfile, 'w')
        #print >> f, output
        #f.close()
