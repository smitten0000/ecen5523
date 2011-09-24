# vim: set ts=4 sw=4 expandtab:

# main function
if __name__ == "__main__":
    import sys, compiler
    from p0parser import P0Parser

    if len(sys.argv) < 2:
        print "Usage: %s <input-file> [input-files...]" % sys.argv[0]
        sys.exit(1)

    red = "\033[31m"
    green = "\033[32m"
    reset = "\033[0m"

    # build the lexer and run
    pars = P0Parser()
    pars.build()

    for filename in sys.argv[1:]:
        f = open(filename, 'r')
        data = f.read()
        f.close()
        try:
            result1 = str(pars.parse(data))
        except:
            raise
            result1 = 'failed parse'
        try:
            result2 = str(compiler.parse(data))
        except:
            raise
            result2 = 'failed parse'
        if result1 == result2:
            print "%-30s [%s%s%s]" % (filename, green, 'OK', reset)
        else:
            print "%-30s [%s%s%s]" % (filename, red, 'FAIL', reset)
            print result1 
            print result2
