import py

from interpreter import Interpreter

def test_int_add():
    w_module = do_the_twist("""
x = 0
x = x add(4)
x = x add(8)
x = x add(15)
x = x add(16)
x = x add(23)
x = x add(42)
""")
    assert w_module.getvalue("x").value == 108

def test_int_sub():
    w_module = do_the_twist("""
x = 0
x = x sub(4)
x = x sub(8)
x = x sub(15)
x = x sub(16)
x = x sub(23)
x = x sub(42)
""")
    assert w_module.getvalue("x").value == -108

def test_int_mult():
    w_module = do_the_twist("""
x = 1
x = x mul(4)
x = x mul(8)
x = x mul(15)
x = x mul(16)
x = x mul(23)
x = x mul(42)
""")
    assert w_module.getvalue("x").value == 7418880

def test_int_div():
    w_module = do_the_twist("""
x = 108 div(6)
y = 42 div(5)
z = 42 div(11)
""")
    assert w_module.getvalue("x").value == 18
    assert w_module.getvalue("y").value == 8
    assert w_module.getvalue("z").value == 3

def test_int_div():
    w_module = do_the_twist("""
x = 108 mod(6)
y = 42 mod(5)
z = 42 mod(11)
""")
    assert w_module.getvalue("x").value == 0
    assert w_module.getvalue("y").value == 2
    assert w_module.getvalue("z").value == 9

    assert w_module.getvalue("x").istrue() == False
    assert w_module.getvalue("y").istrue() == True

def test_bool_and():
    w_module = do_the_twist("""
a = bool and(1,1)
b = bool and(1,0)
c = bool and(0,1)
d = bool and(0,0)
""")

    assert w_module.getvalue("a").istrue() == True
    assert w_module.getvalue("b").istrue() == False
    assert w_module.getvalue("c").istrue() == False
    assert w_module.getvalue("d").istrue() == False

def test_bool_eq():
    w_module = do_the_twist("""
x = bool eq(1,2)
y = bool eq(1,1)
""")
    assert w_module.getvalue("x").istrue() == False
    assert w_module.getvalue("y").istrue() == True

def test_compare_int():
    w_module = do_the_twist("""
a = 1 eq(0)
b = 1 neq(0)
c = 1 eq(1)
d = 1 neq(1)
""")
    assert w_module.getvalue("a").istrue() == False
    assert w_module.getvalue("b").istrue() == True
    assert w_module.getvalue("c").istrue() == True
    assert w_module.getvalue("d").istrue() == False

def test_bool_nor():
    w_module = do_the_twist("""
a = bool nor(1,1)
b = bool nor(1,0)
c = bool nor(0,1)
d = bool nor(0,0)
""")
    assert w_module.getvalue("a").istrue() == False
    assert w_module.getvalue("b").istrue() == False
    assert w_module.getvalue("c").istrue() == False
    assert w_module.getvalue("d").istrue() == True

def test_bool_not():
    w_module = do_the_twist("""
x = bool not(0)
y = bool not(1)
""")
    assert w_module.getvalue("x").istrue() == True
    assert w_module.getvalue("y").istrue() == False

def test_bool_gz():
    w_module = do_the_twist("""
x = bool gz(-1)
y = bool gz(0)
z = bool gz(1)
""")
    assert w_module.getvalue("x").istrue() == False
    assert w_module.getvalue("y").istrue() == False
    assert w_module.getvalue("z").istrue() == True

def test_math_pow():
    w_module = do_the_twist("""
x = 2 pow(1)
y = 2 pow(2)
z = 2 pow(3)
""")
    assert w_module.getvalue("x").value == 2
    assert w_module.getvalue("y").value == 4
    assert w_module.getvalue("z").value == 8

def do_the_twist(code):
    from simpleparser import parse
    ast = parse(code)
    interpreter = Interpreter()
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    return w_module
