#! /usr/bin/python
# vim: set ts=4 sw=4 expandtab:
# Brent Smith <brent.m.smith@colorado.edu>
# Robert Elsner <robert.elsner@colorado.edu>
# CSCI5525, Fall 2011
# HW1

import sys, logging
import compiler

from p0parser import P0Parser
from p0stackallocator import P0StackAllocator
from p1stackallocator import P1StackAllocator
from p1flattener import P1Flattener
from p1insselector import P1InstructionSelector
from p1regallocator import P1RegAllocator
from p1generator import P1Generator
from comp_util import *
import time

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    logging.basicConfig(level=logging.WARN)

    testcases = sys.argv[1:]
    for testcase in testcases:
        #parser = P0Parser()
        #parser.build()
        #ast = parser.parseFile(testcase)
        
        ast = compiler.parseFile(testcase)
        
        varalloc = VariableAllocator()
        explicator = P1Explicate(varalloc)
        ast = explicator.explicate(ast)
        flattener = P1Flattener(varalloc)
        stmtlist = flattener.flatten(ast)
        #code = '%s' % stmtlist
        #eval(compile(code,'test.txt','exec'))
        instruction_selector = P1InstructionSelector(varalloc)
        program = instruction_selector.visit(stmtlist)
        #regallocator = P1RegAllocator(program)
        #start = time.time()
        #program = regallocator.substitute()
        #end = time.time()
        #logger.debug("P0RegAllocator.substitute() took %.02fs" % (end - start))
        #stackallocator = P0StackAllocator(program)
        #program = stackallocator.substitute()
        stackallocator = P1StackAllocator(program)
        program = stackallocator.substitute()
        generator = P1Generator()
        output = generator.generate(program)
        outputfile = '%s.s' % testcase[:testcase.rfind('.')]
        f = open(outputfile, 'w')
        print >> f, output
        f.close()
