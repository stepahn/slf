import py

from simpleparser import parse
from objmodel import W_NormalObject
from interpreter import Interpreter

empty_builtins = """
1
"""

def test_assignment():
    ast = parse("""
x = 1
""")
    interpreter = Interpreter(empty_builtins)
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("x").value == 1

def test_negative_intliteral():
    ast = parse("""
x = -1
""")
    interpreter = Interpreter(empty_builtins)
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("x").value == -1

def test_huge_intliteral():
    ast = parse("""
x = 10000
""")
    interpreter = Interpreter(empty_builtins)
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("x").value == 10000

def test_huge_negative_intliteral():
    ast = parse("""
x = -10000
""")
    interpreter = Interpreter(empty_builtins)
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("x").value == -10000

def test_primitive():
    ast = parse("""
x = 1 $int_add(2)
""")
    interpreter = Interpreter(empty_builtins)
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("x").value == 3

def test_pop():
    ast = parse("""
x = 1 # the result of this will be popped from the stack
x = 2
""")
    interpreter = Interpreter(empty_builtins)
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("x").value == 2


def test_condition():
    ast = parse("""
x = 1
if x:
    x = 2
else:
    x = 3
if 0:
    y = 3
else:
    y = 4
""")
    interpreter = Interpreter(empty_builtins)
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("x").value == 2
    assert w_module.getvalue("y").value == 4

def test_objectdefinition_simple():
    ast = parse("""
object x:
    a = 1
    b = 2
""")
    interpreter = Interpreter(empty_builtins)
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("x").getvalue("a").value == 1
    assert w_module.getvalue("x").getvalue("b").value == 2


def test_objectdefinition_parents():
    ast = parse("""
object x:
    a = 1
    b = 2
object y(parent=x):
    b = 3
a = y a
b = y b
""")
    interpreter = Interpreter(empty_builtins)
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("a").value == 1
    assert w_module.getvalue("b").value == 3

def test_objectdefinition___parent__():
    ast = parse("""
object x:
    a = 1
    b = 2
object y(__parent__=x):
    b = 3
a = y a
b = y b
""")
    interpreter = Interpreter(empty_builtins)
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("a").value == 1
    assert w_module.getvalue("b").value == 3


def test_functiondefinition_noargs():
    ast = parse("""
def f:
    if x:
        1
    else:
        2
x = 0
x = f
y = f
""")
    interpreter = Interpreter(empty_builtins)
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("x").value == 2
    assert w_module.getvalue("y").value == 1


def test_functiondefinition_args():
    ast = parse("""
def f(x):
    if x:
        1
    else:
        2
x = f(0)
y = f(1)
""")
    interpreter = Interpreter(empty_builtins)
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("x").value == 2
    assert w_module.getvalue("y").value == 1


def test_whileloop():
    ast = parse("""
def f(x):
    sum = 0
    while x:
        sum = sum $int_add(x)
        x = x $int_add(-1)
    sum
x = f(100)
""")
    interpreter = Interpreter(empty_builtins)
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("x").value == 5050

def test_method_cascade():
    ast = parse("""
object x:
    a = 1
object y:
    a = 2
x next = y
y next = x

a = x next next next next next next a
b = x next next next next next next next a
""")
    interpreter = Interpreter(empty_builtins)
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("a").value == 1
    assert w_module.getvalue("b").value == 2

