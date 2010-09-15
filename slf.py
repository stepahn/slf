#/usr/bin/env python

from slflib.simpleparser import parse
from slflib.interpreter import Interpreter

from pypy.rlib.streamio import open_file_as_stream

def target(*args):
    return main, None

def main(args):
    try:
        fname = args[1]
    except:
        print 'usage: ', args[0], ' file.slf'
        sys.exit(1)

    interpreter = Interpreter()
    w_module = interpreter.make_module()

    code = open_file_as_stream(fname, 'r', 1024).readall()
    ast = parse(code)
    interpreter.eval(ast, w_module)

    return 0

if __name__ == '__main__':
    import sys
    main(sys.argv)
