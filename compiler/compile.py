#! /usr/bin/python
# vim: set ts=4 sw=4 expandtab:
# Brent Smith <brent.m.smith@colorado.edu>
# Robert Elsner <robert.elsner@colorado.edu>
# CSCI5525, Fall 2011
# HW1

import sys, logging
from p0parser import P0Parser
from p0flattener import P0Flattener
from p0insselector import P0InstructionSelector
from p0regallocator import P0RegAllocator
from p0stackallocator import P0StackAllocator
from p0generator import P0Generator
from comp_util import *
import time

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    logging.basicConfig(level=logging.WARN)

    testcases = sys.argv[1:]
    for testcase in testcases:
        parser = P0Parser()
        parser.build()
        #ast = compiler.parseFile(testcase)
        ast = parser.parseFile(testcase)
        varalloc = VariableAllocator()
        p0flattener = P0Flattener(varalloc)
        stmtlist = p0flattener.flatten(ast)
        #code = '%s' % stmtlist
        #eval(compile(code,'test.txt','exec'))
        instruction_selector = P0InstructionSelector(varalloc)
        program = instruction_selector.visit(stmtlist)
        regallocator = P0RegAllocator(program)
        start = time.time()
        program = regallocator.substitute()
        end = time.time()
        logger.debug("P0RegAllocator.substitute() took %.02fs" % (end - start))
        #stackallocator = P0StackAllocator(program)
        #program = stackallocator.substitute()
        generator = P0Generator()
        output = generator.generate(program)
        outputfile = '%s.s' % testcase[:testcase.rfind('.')]
        f = open(outputfile, 'w')
        print >> f, output
        f.close()
