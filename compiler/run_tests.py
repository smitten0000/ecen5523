#! /usr/bin/python

import sys
import os
import subprocess
import difflib
from os.path import splitext
import colors
import string
from string import split
from colors import *

python_prog = "/usr/bin/python"

# we'll need a garbage collection library later
if False:
  gc_inc = "-I/Users/siek/gc6.8/include"
  gc_lib = "/Users/siek/gc6.8/.libs/libgc.a"
else:
  gc_inc = ""
  gc_lib = ""

default_prog = "./compile.py"
default_tests_dir = "./test"

# default to using compiler.py and tests dir
if len(sys.argv) < 2:
  prog = default_prog
else:
  prog = sys.argv[1]

if not os.path.exists(prog):
    print "Compiler not found: " + prog
    sys.exit(1)

if len(sys.argv) < 3:
  testsdir = default_tests_dir
else:
  testsdir = sys.argv[2]

(homedir,progname) = os.path.split(prog)

gcc_params = ['-g', '-lm', '-m32','-I' + homedir, '-I' + homedir + '/test', '-I' + homedir + '/tests',gc_inc]


runtime_files = filter(lambda f: splitext(f)[1] == '.c', os.listdir(homedir))
for f in runtime_files:
    gcc_cmd = ["gcc", homedir + '/' + f, "-c", "-g", "-m32", gc_inc, "-lm"]
    gcc_cmd = [arg for arg in gcc_cmd if arg]
    compile_proc = subprocess.Popen(gcc_cmd)
    warn = compile_proc.communicate()[1]
    retcode = compile_proc.poll()
    if retcode != 0:
      print 'failed to compile ' + f
    mvproc = subprocess.Popen(["mv", splitext(f)[0] + '.o', homedir + '/' + splitext(f)[0] + '.o'])
    retcode = mvproc.poll()    

object_files = map(lambda f: homedir + '/' + splitext(f)[0] + '.o', runtime_files)

tests = os.listdir(testsdir)


tests = filter(lambda t: splitext(t)[1] == '.py', tests)
tests = map(lambda t: testsdir + '/' + t, tests)

success = 0
fail = 0

successes = []
failures = []

COMPILE_SUCCESS=0
COMPILE_WARN=1
COMPILE_FAIL=2

RUN_SUCCESS=0
RUN_FAIL=1


def show_test_result(test_name, compile, run):
    terminal_width = 50
    t_name = split(test_name,'.py')[0]
    t_name = split(t_name,testsdir + os.sep)[1]
    test_output = blue + t_name + normal
    if compile == COMPILE_SUCCESS:
        compile_result_str = '[ ' + green + 'OK' + normal + ' ]'
    elif compile == COMPILE_WARN:
        compile_result_str = '[' + yellow + 'WARN' + normal + ']'
    else:
        compile_result_str = '[' + red + 'FAIL' + normal + ']'

    if run == RUN_SUCCESS:
        run_result_str = '[ ' + green + 'OK' + normal + ' ]'
    else:
        run_result_str = '[' + red + 'FAIL' + normal + ']'

    spaces = terminal_width - len(t_name) - 2 * len('[    ]') + len(' ')
    for i in range(spaces):
        test_output += ' '
    test_output += compile_result_str + ' ' + run_result_str
    print test_output

print 'Test Name                              [Comp] [Run!]'

for t in tests:
    test_name = t
    base = splitext(t)[0]
    cfilename = base+'.s'
    cfile = open(cfilename, 'w')
    wfile = open(base+'.warn', 'w')
#    print 'compiling Python to C'
    retcode = subprocess.call([python_prog,prog,t], stdout=cfile)
#    print 'about to indent'
#    retcode = subprocess.call(['indent',cfilename])
    gcc_cmd = ["gcc", cfilename] + object_files + [gc_lib] + ["-o", base] + gcc_params
    gcc_cmd = [arg for arg in gcc_cmd if arg]
    
#    print 'invoking gcc'
#    print ' '.join(gcc_cmd)
#    compile_proc = subprocess.Popen(gcc_cmd, stderr=subprocess.PIPE)
    compile_proc = subprocess.Popen(gcc_cmd)
    warn = compile_proc.communicate()[1]
    retcode = compile_proc.poll()

    compile_result = COMPILE_SUCCESS
    if retcode != 0:
        compile_result = COMPILE_FAIL
        fail = fail + 1
    elif warn:
        compile_result = COMPILE_WARN
    run_result = RUN_FAIL

    if retcode == 0:
        outfilename = base + '.out'
        infilename = base + '.in'
#        print 'running the program'
        outfile = open(outfilename, 'w')
        if os.path.split(infilename)[1] in os.listdir(testsdir):
          infile = open(infilename, 'r')
          retcode = subprocess.call([base], stdin=infile, stdout=outfile)
        else:
          retcode = subprocess.call([base], stdout=outfile)

        expfilename = base+'.expected'
        expected = open(expfilename, 'w')
        
        if os.path.split(infilename)[1] in os.listdir(testsdir):
          infile = open(infilename, 'r')
          retcode = subprocess.call([python_prog,t], stdin=infile, stdout=expected)
        else:
          retcode = subprocess.call([python_prog,t], stdout=expected)

        retcode = subprocess.call(["diff","-w","-B",expfilename, outfilename],stdout=subprocess.PIPE)
        if retcode == 0:
            success = success + 1
            successes.append(base)
            run_result = RUN_SUCCESS
        else:
            fail = fail + 1
            failures.append(base)
    show_test_result(test_name, compile_result, run_result)

def hr():
    print '===================================================='


hr()
print '                tests passed: ' + green + str(success) + normal + \
        ', tests failed: ' + red + str(fail) + normal

if False and fail > 0:
    print '\nfailures:'
    for f in failures:
        print red + f + normal
        print blue + 'test program:\n' + normal + open(f + '.py', 'r').read()
        print blue + 'output:\n' + normal + open(f + '.out','r').read()
        print blue + 'expected:\n' + normal + open(f + '.expected','r').read()
