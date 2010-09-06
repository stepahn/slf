import py

from simpleparser import parse
from objmodel import W_NormalObject
from interpreter import Interpreter

def test_args_order():
    ast = parse("""
def f(a, b, c):
    if a:
        4
    else:
        if b:
            8
        else:
            if c:
                15
            else:
                16
w = f(1, 1, 1)
x = f(0, 1, 1)
y = f(0, 0, 1)
z = f(0, 0, 0)
""")

    interpreter = Interpreter()
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("w").value == 4
    assert w_module.getvalue("x").value == 8
    assert w_module.getvalue("y").value == 15
    assert w_module.getvalue("z").value == 16
