import py

from simpleparser import parse
from objmodel import W_NormalObject
from interpreter import Interpreter

def test_integer_asignment():
    ast = parse("""
x = 42
y = x
x = 4
""")

    interpreter = Interpreter()
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)

    assert w_module.getvalue("x").value == 4
    assert w_module.getvalue("y").value == 42

def test_object_asignment():
    ast = parse("""
object foo:
    x = 42
x = foo x
y = x
foo x = 4
z = foo x
""")

    interpreter = Interpreter()
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)

    assert w_module.getvalue("x").value == 42
    assert w_module.getvalue("y").value == 42
    assert w_module.getvalue("z").value == 4
