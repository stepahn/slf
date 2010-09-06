import py

from simpleparser import Parser, ParseError
from simplelexer import lex
from simpleast import *

def raisesparserror(source, what):
    p = Parser(source)
    excinfo = py.test.raises(ParseError, getattr(p, what))
    print excinfo.value.nice_error_message()


def test_expression():
    ast = Parser("a b c").expression()
    ast1 = MethodCall(MethodCall(MethodCall(ImplicitSelf(), "a"), "b"), "c")
    assert ast == ast1
    ast = Parser("a f(1, a b c, 3,)").expression()
    assert ast == MethodCall(MethodCall(ImplicitSelf(), "a"), "f", [
                      IntLiteral(1), ast1, IntLiteral(3)])

def test_expression2():
    ast = Parser("$a $b $c").expression()
    ast1 = PrimitiveMethodCall(PrimitiveMethodCall(
        PrimitiveMethodCall(ImplicitSelf(), "$a"), "$b"), "$c")
    assert ast == ast1
    ast = Parser("$a $f(1, $a $b $c, 3,)").expression()
    assert ast == PrimitiveMethodCall(
            PrimitiveMethodCall(ImplicitSelf(), "$a"), "$f", [
                      IntLiteral(1), ast1, IntLiteral(3)])


def test_simplestatement():
    ast = Parser("a\n").statement()
    ast1 = ExprStatement(MethodCall(ImplicitSelf(), "a"))
    assert ast == ast1
    ast = Parser("a = 4 b\n").statement()
    ast1 = Assignment(ImplicitSelf(), "a", MethodCall(IntLiteral(4), "b"))
    assert ast == ast1
    ast = raisesparserror("a(1) = 4 b\n", "statement")
    ast = raisesparserror("1 = 4 b\n", "statement")

def test_error():
    ast = raisesparserror("a add 2\n", "statement")



def test_if():
    ast = Parser("""if a and(b):
    a b
""").statement()
    ast1 = IfStatement(MethodCall(MethodCall(ImplicitSelf(), "a"), "and",
                                  [MethodCall(ImplicitSelf(), "b")]),
                       Program([ExprStatement(
                           MethodCall(MethodCall(ImplicitSelf(), "a"),
                                "b"))]))
    assert ast1 == ast

    ast = Parser("""if a and(b):
    a b
else:
    b
""").statement()
    ast1 = IfStatement(MethodCall(MethodCall(ImplicitSelf(), "a"), "and",
                                  [MethodCall(ImplicitSelf(), "b")]),
                       Program([ExprStatement(
                           MethodCall(MethodCall(ImplicitSelf(), "a"),
                                "b"))]),
                       Program([ExprStatement(
                           MethodCall(ImplicitSelf(), "b"))]))
    assert ast1 == ast

def test_while():
    ast = Parser("""
while i:
    i = i sub(1)
""").statement()
    ast1 = WhileStatement(MethodCall(ImplicitSelf(), "i"),
                          Program([Assignment(ImplicitSelf(), "i",
                                      MethodCall(MethodCall(ImplicitSelf(), "i"),
                                                 "sub",
                                                 [IntLiteral(1)]))]))
    assert ast1 == ast

def test_object():
    ast = Parser("""
object a:
    i = 1
    if i:
        j = 2
""").statement()
    ast1 = ObjectDefinition("a", Program([
        Assignment(ImplicitSelf(), "i", IntLiteral(1)),
        IfStatement(MethodCall(ImplicitSelf(), "i"), Program([
            Assignment(ImplicitSelf(), "j", IntLiteral(2)),
            ]))
        ]))
    assert ast1 == ast

    ast = Parser("""
object a(parent=1):
    i = 1
    if i:
        j = 2
""").statement()
    ast1 = ObjectDefinition("a", Program([
        Assignment(ImplicitSelf(), "i", IntLiteral(1)),
        IfStatement(MethodCall(ImplicitSelf(), "i"), Program([
            Assignment(ImplicitSelf(), "j", IntLiteral(2)),
            ]))
        ]),
        ["parent"],
        [IntLiteral(1)])
    assert ast1 == ast


def test_def():
    ast = Parser("""
def f(x, y, z):
    i = 1
    if i:
        j = 2
""").program()
    ast1 = Program([FunctionDefinition("f", ["x", "y", "z"], Program([
        Assignment(ImplicitSelf(), "i", IntLiteral(1)),
        IfStatement(MethodCall(ImplicitSelf(), "i"), Program([
            Assignment(ImplicitSelf(), "j", IntLiteral(2)),
            ]))
        ]))])
    assert ast1 == ast
