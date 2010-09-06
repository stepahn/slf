import py

from simpleparser import parse
from objmodel import W_NormalObject
from interpreter import Interpreter

def test_method_simple():
    ast = parse("""
object a:
    x = 11
    def f:
        self x
object b:
    __parent__ = a
    x = 22
af = a f # a is the receiver, therefore self is a in the method
bf = b f # b is the receiver, therefore self is b in the method

""")
    interpreter = Interpreter()
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("af").value == 11
    assert w_module.getvalue("bf").value == 22


def test_method_complex():
    ast = parse("""
k = 10
object a:
    x = 11
    y = 22
    def f(a, b):
        if a:
            if b:
                a
            else:
                k
        else:
            if b:
                self x
            else:
                self y
object b:
    __parent__ = a
    y = 55
af11 = a f(1, 1)
af10 = a f(1, 0)
af01 = a f(0, 1)
af00 = a f(0, 0)
k = 908
bf11 = b f(1, 1)
bf10 = b f(1, 0)
bf01 = b f(0, 1)
bf00 = b f(0, 0)
""")
    interpreter = Interpreter()
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("af11").value == 1
    assert w_module.getvalue("af10").value == 10
    assert w_module.getvalue("af01").value == 11
    assert w_module.getvalue("af00").value == 22
    assert w_module.getvalue("bf11").value == 1
    assert w_module.getvalue("bf10").value == 908
    assert w_module.getvalue("bf01").value == 11
    assert w_module.getvalue("bf00").value == 55
