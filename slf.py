#/usr/bin/env python

from slflib.simpleparser import parse, ParseError
from slflib.interpreter import Interpreter

from pypy.rlib.streamio import open_file_as_stream
import sys

def target(*args):
    return main, None

def main(args):
    fname = ''
    try:
        fname = args[1]
    except:
        print 'usage: %s file.slf' % args[0]
        return 1

    interpreter = Interpreter()
    w_module = interpreter.make_module()

    code = ''
    try:
        code = open_file_as_stream(fname, 'r', 1024).readall()
    except Exception, e:
        print 'ERROR: reading file'
        print e
        return 1

    ast = ''
    try:
        ast = parse(code)
    except Exception, e:
        print 'ERROR: parser', e
        return 1

    try:
        interpreter.eval(ast, w_module)
    except Exception, e:
        print 'ERROR: interpreter', e
        return 1

    return 0

if __name__ == '__main__':
    main(sys.argv)
