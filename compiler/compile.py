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
from p2uniquifyvars import P2UniquifyVars
from p2explicate import P2Explicate
from p2heapify import P2Heapify
from p2closureconvert import P2ClosureConversion
from p2flattener import P2Flattener
from p2insselector import P2InstructionSelector
from p2regallocator import P2RegAllocator
from p2ifinsselector import P2IfInstructionSelector
from p2generator import P2Generator
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
        uniquify = P2UniquifyVars()
        explicator = P2Explicate(varalloc)
        heap = P2Heapify(explicator)
        closer = P2ClosureConversion(explicator, varalloc)
        flattener = P2Flattener(varalloc)
        instruction_selector = P2InstructionSelector(varalloc)
        ifinsselector = P2IfInstructionSelector(varalloc,instruction_selector.labelalloc)
        generator = P2Generator(False)

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
            allocator = P2RegAllocator(program, varalloc)
            program = allocator.substitute()
            program = ifinsselector.visit(program)
            output = output + generator.generate(program)
        outputfile = '%s.s' % testcase[:testcase.rfind('.')]
        f = open(outputfile, 'w')
        print >> f, output
        f.close()
        logging.shutdown()
