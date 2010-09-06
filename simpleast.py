import py

class MetaNode(type):
    def __init__(cls, name, bases, dict):
        compile_name = "compile_" + name
        abstract = not hasattr(cls, "attrs")
        def dispatch(self, compiler):
            if not abstract:
                getattr(compiler, compile_name)(self)
        cls.dispatch = dispatch

class AstNode(object):
    __metaclass__ = MetaNode

    """ Base class for all ast nodes. Provides generic functionality."""
    tokens = None
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__,
                ", ".join([repr(getattr(self, a)) for a in self.attrs]))

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return False
        for key in self.attrs:
            if getattr(self, key) != getattr(other, key):
                return False
        return True

    def __ne__(self, other):
        return not (self == other)

    def dot(self, result=None):
        def uid(x):
            result = id(x)
            if result < 0:
                result = 'm%d' % (-result,)
            return result
        if result is None:
            result = []
        body = [self.__class__.__name__]
        children = []
        for key in self.attrs:
            obj = getattr(self, key)
            if isinstance(obj, list):
                if obj and isinstance(obj[0], AstNode):
                    children.extend(obj)
                    for i, elt in enumerate(obj):
                        result.append("o%s -> o%s [label=\"%s[%s]\"]" % (
                            uid(self), uid(elt), key, i))
                else:
                    body.append("%s = %s" % (key, obj))
            elif isinstance(obj, AstNode):
                children.append(obj)
                result.append("o%s -> o%s [label=\"%s\"]" % (
                    uid(self), uid(obj), key))
            else:
                body.append("%s = %s" % (key, obj))
        result.append("o%s [label=\"%s\", shape=box]" % (uid(self), repr("\n".join(body))[1:-1]))
        for child in children:
            child.dot(result)
        return result

    def view(self):
        """ Calling this method gives a graphical representation of the ast
        graph.  Needs a checkout of
        http://codespeak.net/svn/pypy/trunk/dotviewer in the current directory
        as well as graphviz (http://graphviz.org) installed. """
        from dotviewer import graphclient
        content = ["digraph G{"]
        content.extend(self.dot())
        content.append("}")
        p = py.test.ensuretemp("simpleparser").join("temp.dot")
        p.write("\n".join(content))
        graphclient.display_dot_file(str(p))

class Expression(AstNode):
    """ Abstract Base class for all expression AST nodes"""

class IntLiteral(Expression):
    """ An integer literal (like "1") """

    attrs = ["value"]
    def __init__(self, value):
        self.value = value

class MethodCall(Expression):
    """ A call to a method with name 'methodname' on 'receiver' with
    'arguments' (which is a list of expression ASTs).

    Example:
        f(1, 2, 3)
        (receiver is ImplicitSelf(), methodname is 'f' and
        args is [IntLiteral(1), IntLiteral(2), IntLiteral(3)])

        5 f
        (receiver is IntLiteral(5), methodname is 'f' and args is [])
    """

    attrs = ["receiver", "methodname", "arguments"]
    def __init__(self, receiver, methodname, arguments=None):
        self.receiver = receiver
        self.methodname = methodname
        if arguments is None:
            arguments = []
        self.arguments = arguments

class PrimitiveMethodCall(MethodCall):
    """
    # ----------------------------------------
    # this can be ignored until Blatt 9

    A method call to a primitive method. Primitive method names start with
    '$'.The attributes are like those in MethodCall.

    Example:

        5 $int_add(6)
        (receiver is IntLiteral(5), methodname is '$int_add' and args
        is [IntLiteral(6)])
    """

class ImplicitSelf(Expression):
    """ The receiver that is used when none is specified.

    Example:
    f
    this is a method call "f" on the implicit self."""

    attrs = []

class Statement(AstNode):
    """ Base class of all statement nodes. """

class Assignment(Statement):
    """ An assignement: lvalue attrname = expression.

    Example:
    x = 7
    this is an assignement on the implicit self."""

    attrs = ["lvalue", "attrname", "expression"]
    def __init__(self, lvalue, attrname, expression):
        self.lvalue = lvalue
        self.attrname = attrname
        self.expression = expression

class ExprStatement(Statement):
    """ A statement that is just an expression evaluation."""

    attrs = ["expression"]
    def __init__(self, expr):
        self.expression = expr

class IfStatement(Statement):
    """ An if statement. The syntax looks like this:

    if condition:
        ... ifblock ...
    else:
        ... elseblock ...

    The elseblock is optional."""

    attrs = ["condition", "ifblock", "elseblock"]
    def __init__(self, condition, ifblock, elseblock=None):
        self.condition = condition
        self.ifblock = ifblock
        self.elseblock = elseblock

class WhileStatement(Statement):
    """ A while loop. The syntax looks like this:

    while condition:
        ... whileblock ...
    """

    attrs = ["condition", "whileblock"]
    def __init__(self, condition, whileblock):
        self.condition = condition
        self.whileblock = whileblock

class FunctionDefinition(Statement):
    """ A function definition.  Corresponds to def name(arguments): block.

    The 'name' is a string, the 'arguments' is a list of strings, and the
    'block' is a Program (see below).  Executing a FunctionDefinition creates
    a new W_Method and assigns it to the 'name' on the implicit self.

    Example:
        def f:              FunctionDefinition('f', [], Program([...]))
            41

        def g(a, b, c):     FunctionDefinition('g', ['a', 'b', 'c'], ...)
            43
    """
    attrs = ["name", "arguments", "block"]
    def __init__(self, name, arguments, block):
        self.name = name
        self.arguments = arguments
        self.block = block

class ObjectDefinition(Statement):
    """ Makes a new normal object.

    The block is immediately executed with the new object as the
    implicit self.  The 'name' is bound to the new object in the
    outer scope's implicit self.

    Example:
        object x:
            def f(y):
                y

    # --------------------------------------------------
    # the following can be ignored until Blatt 8
    The 'parentnames' attribute is a list of strings giving the parent
    attributes of the new object. The 'parentdefinitions' attribute is a list
    of expression-asts giving the initial value of those parent attributes.

    Example:
        object x(p1=a, p2=b):
            ...

    gives parentnames = ["p1", "p2"]
    and parentdefinitions = [MethodCall(ImplicitSelf, "a", []),
                             MethodCall(ImplicitSelf, "b", [])]

    """
    attrs = ["name", "block", "parentnames", "parentdefinitions"]
    def __init__(self, name, block, parentnames=None, parentdefinitions=None):
        self.name = name
        self.block = block
        if parentnames is None:
            parentnames = []
            parentdefinitions = []
        self.parentnames = parentnames
        self.parentdefinitions = parentdefinitions

class Program(AstNode):
    """ A list of statements. """
    attrs = ["statements"]
    def __init__(self, statements):
        self.statements = statements
