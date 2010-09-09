import py

from simpleparser import parse
from objmodel import W_NormalObject
from interpreter import Interpreter

def test_builtin_simple():
    builtincode = """
x = 1
object None:
    1
def pass:
    None
"""
    # construct the builtin module by running builtincode within the context of
    # a new empty module
    interpreter = Interpreter(builtincode)
    w_module = interpreter.make_module()
    # the parent of a normal module is the builtin module
    builtins = w_module.getparents()[0]
    assert builtins.getvalue('x').value == 1

    ast = parse("""
tx = x
object a:
    pass
ax = a x
""")
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("ax").value == 1
    assert w_module.getvalue("tx").value == 1

def test_inttrait():
    builtincode = """
object inttrait:
    x = 1
    def maybe_fortytwo:
        if self:
            42
        else:
            x
"""
    interpreter = Interpreter(builtincode)
    w_module = interpreter.make_module()
    # the parent of a normal module is the builtin module
    builtins = w_module.getparents()[0]
    inttrait = builtins.getvalue("inttrait")

    ast = parse("""
x = 5 x # this returns 1, because it looks in the inttrait defined above
m0 = 0 maybe_fortytwo
m1 = x maybe_fortytwo
inttrait x = 2
m2 = 0 maybe_fortytwo
tr = inttrait
""")
    interpreter.eval(ast, w_module)
    x = w_module.getvalue("x")
    assert w_module.getvalue("tr") is inttrait
    # the inttrait is defined in the builtin module, so its __parent__ is that
    # module
    assert inttrait.getparents() == [builtins]
    assert x.value == 1
    assert x.getparents() == [inttrait]
    assert w_module.getvalue("m0").value == 1
    assert w_module.getvalue("m1").value == 42
    assert w_module.getvalue("m2").value == 2

    
def test_builtin_default():
    ast = parse("""
def sumupto(x):
    r = 0
    while x:
        r = r add(x)
        x = x add(-1)
    r
x = sumupto(100)
""")
    # the constructor is called without arguments, so the default builtins are
    # used
    interpreter = Interpreter()
    # test that the default inttrait defines a method ``add``
    w_module = interpreter.make_module()
    interpreter.eval(ast, w_module)
    assert w_module.getvalue("x").value == 5050
