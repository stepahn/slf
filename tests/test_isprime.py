import py
def test_sqrt():
    w_module = do_the_twist("""
a = math sqrt(0)
b = math sqrt(1)
c = math sqrt(2)
d = math sqrt(3)
e = math sqrt(4)
f = math sqrt(5)
g = math sqrt(6)
h = math sqrt(7)
i = math sqrt(8)
j = math sqrt(9)
""")
    assert w_module.getvalue("a").value == 0
    assert w_module.getvalue("b").value == 1
    assert w_module.getvalue("c").value == 1
    assert w_module.getvalue("d").value == 1
    assert w_module.getvalue("e").value == 2
    assert w_module.getvalue("f").value == 2
    assert w_module.getvalue("g").value == 2
    assert w_module.getvalue("h").value == 2
    assert w_module.getvalue("i").value == 2
    assert w_module.getvalue("j").value == 3

def test_isprime():
    w_module = do_the_twist("""
a = math isprime(0)
b = math isprime(1)
c = math isprime(2)
d = math isprime(3)
e = math isprime(4)
f = math isprime(5)
g = math isprime(6)
h = math isprime(7)
i = math isprime(8)
j = math isprime(9)
""")
    assert w_module.getvalue("a").istrue() == False
    assert w_module.getvalue("b").istrue() == False
    assert w_module.getvalue("c").istrue() == True
    assert w_module.getvalue("d").istrue() == True
    assert w_module.getvalue("e").istrue() == False
    assert w_module.getvalue("f").istrue() == True
    assert w_module.getvalue("g").istrue() == False
    assert w_module.getvalue("h").istrue() == True
    assert w_module.getvalue("i").istrue() == False
    assert w_module.getvalue("j").istrue() == False

def do_the_twist(code):
    from interpreter import Interpreter
    from simpleparser import parse
    ast = parse(code)
    interpreter = Interpreter()
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    return w_module
