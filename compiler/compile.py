#! /usr/bin/python
# vim: set ts=4 sw=4 expandtab:
# Brent Smith <brent.m.smith@colorado.edu>
# Robert Elsner <robert.elsner@colorado.edu>
# CSCI5525, Fall 2011
# HW1

import sys, logging
import logging.config
import compiler

from p0parser import P0Parser
from p3uniquifyvars import P3UniquifyVars
from p3explicate import P3Explicate
from p3heapify import P3Heapify
from p3closureconvert import P3ClosureConversion
from p3flattener import P3Flattener
from p3insselector import P3InstructionSelector
from p3regallocator import P3RegAllocator
from p3ifinsselector import P3IfInstructionSelector
from p3generator import P3Generator
from comp_util import *
import time

logger = logging.getLogger('compiler.main')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

#    # configure logging 
#    logging.config.fileConfig('logging.cfg')
    logging.basicConfig(level=logging.ERROR)
    sys.setrecursionlimit(10000)

    testcases = sys.argv[1:]
    for testcase in testcases:
        logger.info("Working on test case '%s'" % testcase)

        # instantiate all classes needed for our pipeline
        varalloc = VariableAllocator()
        uniquify = P3UniquifyVars()
        explicator = P3Explicate(varalloc)
        heap = P3Heapify(explicator)
        closer = P3ClosureConversion(explicator, varalloc)
        flattener = P3Flattener(varalloc)
        instruction_selector = P3InstructionSelector(varalloc)
        ifinsselector = P3IfInstructionSelector(varalloc,instruction_selector.labelalloc)
        generator = P3Generator(False)

        # send the AST through the pipeline
        ast = compiler.parseFile(testcase)
        ast = uniquify.transform(ast)
        ast = explicator.explicate(ast)
        ast  = heap.transform(ast)
        astlist = closer.transform(ast)
        output = ''
        for ast in astlist:
            flatast = flattener.flatten(ast)
            program = instruction_selector.visit(flatast)
            #allocator = P1StackAllocator(program)
            allocator = P3RegAllocator(program, varalloc)
            program = allocator.substitute()
            program = ifinsselector.visit(program)
            output = output + generator.generate(program)
        outputfile = '%s.s' % testcase[:testcase.rfind('.')]
        f = open(outputfile, 'w')
        print >> f, output
        f.close()
        logging.shutdown()
