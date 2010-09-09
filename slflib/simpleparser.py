"""
A 'simple' parser.  Don't look into this file :-)
"""
import py
import simpleast
from simplelexer import lex

from pypy.rlib.objectmodel import specialize

def parse(s):
    result = Parser(s).program()
    return result

# ____________________________________________________________

class ParseError(Exception):
    def __init__(self, source_pos, errorinformation, source=""):
        self.source_pos = source_pos
        self.errorinformation = errorinformation
        self.args = (source_pos, errorinformation)
        self.source = source

    def nice_error_message(self, filename="<unknown>"):
        result = ["  File %s, line %s" % (filename, self.source_pos.lineno + 1)]
        source = self.source
        if source:
            result.append(source.split("\n")[self.source_pos.lineno])
            result.append(" " * self.source_pos.columnno + "^")
        else:
            result.append("<couldn't get source>")
        result.append("ParseError")
        if self.errorinformation:
            failure_reasons = self.errorinformation.expected
            if failure_reasons:
                expected = ''
                if len(failure_reasons) > 1:
                    all_but_one = failure_reasons[:-1]
                    last = failure_reasons[-1]
                    expected = "%s or '%s'" % (
                        ", ".join(["'%s'" % e for e in all_but_one]), last)
                elif len(failure_reasons) == 1:
                    expected = failure_reasons[0]
                if expected:
                    result.append("expected %s" % (expected, ))
            if self.errorinformation.customerror:
                result.append(self.errorinformation.customerror)
        return "\n".join(result)

    def __str__(self):
        return self.nice_error_message()


class ErrorInformation(object):
    def __init__(self, pos, expected=None, customerror=None):
        if expected is None:
            expected = []
        self.expected = expected
        self.pos = pos
        self.customerror = customerror

def combine_errors(self, other):
    if self is None:
        return other
    if (other is None or self.pos > other.pos or
        len(other.expected) == 0):
        return self
    elif other.pos > self.pos or len(self.expected) == 0:
        return other
    failure_reasons = []
    already_there = {}
    for fr in [self.expected, other.expected]:
        for reason in fr:
            if reason not in already_there:
                already_there[reason] = True
                failure_reasons.append(reason)
    return ErrorInformation(self.pos, failure_reasons,
                            self.customerror or other.customerror)

def make_arglist(methodname):
    def arglist(self):
        self.match("OpenBracket", "(")
        method = getattr(self, methodname)
        result = [method()]
        result.extend(self.repeat(self.comma, method))
        self.maybe(self.comma)
        self.match("CloseBracket", ")")
        return result
    return arglist

def make_choice(*methodnames):
    from pypy.rlib.unroll import unrolling_iterable
    unrolling_methodnames = unrolling_iterable(methodnames)
    def choice(self):
        c = self.i, self.last_i
        last = None
        for func in unrolling_methodnames:
            try:
                return getattr(self, func)()
            except ParseError, e:
                last = combine_errors(last, e.errorinformation)
                self.i, self.last_i = c
        raise ParseError(self.tokens[self.i].source_pos, last, self.source)
    return choice

class Parser(object):
    def __init__(self, source):
        self.source = source
        self.tokens = lex(source)
        self.i = 0
        self.last_i = 0

    def match(self, name, value=None):
        if self.i < len(self.tokens):
            result = self.tokens[self.i]
            if result.name == name:
                if value is None or result.source == value:
                    self.i += 1
                    return result
        else:
            result = self.tokens[-1]
        raise ParseError(result.source_pos,
                         ErrorInformation(result.source_pos.i, [value or name]),
                         self.source)

    @specialize.arg(1)
    def call(self, c, *call):
        call = (c, ) + call
        result = None
        for subcall in call:
            result = subcall()
        return result

    @specialize.arg(1, 2)
    def repeat(self, c1, c2=None):
        if c2 is None:
            c2 = c1
            c1 = None
        result = []
        while True:
            c = self.i, self.last_i
            try:
                if c1:
                    c1()
                subresult = c2()
                result.append(subresult)
            except ParseError, e:
                self.i, self.last_i = c
                return result

    @specialize.arg(1)
    def maybe(self, callable):
        c = self.i, self.last_i
        try:
            return callable()
        except ParseError, e:
            self.i, self.last_i = c
            return None

    basic_expression = make_choice("intliteral", "implicitselfmethodcall")

    # Expressions
    def expression(self):
        first = self.basic_expression()
        while True:
            following = self.maybe(self.methodcall)
            if not following:
                break
            following.receiver = first
            first = following
        return first

    def intliteral(self):
        token = self.match("Number")
        return simpleast.IntLiteral(int(token.source))

    def name(self):
        return self.match("Name").source

    def newline(self):
        return self.match("Newline")

    def implicitselfmethodcall(self):
        result = self.methodcall()
        result.receiver = simpleast.ImplicitSelf()
        return result

    methodcall = make_choice("normalmethodcall", "primitivemethodcall")

    def normalmethodcall(self):
        name = self.name()
        args = self.maybe(self.callarguments)
        if args is None:
            args = []
        return simpleast.MethodCall(None, name, args)

    def primitivemethodcall(self):
        token = self.match("PrimitiveName")
        args = self.maybe(self.callarguments)
        if args is None:
            args = []
        return simpleast.PrimitiveMethodCall(None, token.source, args)

    
    callarguments = make_arglist("expression")

    def comma(self):
        return self.match('Special', ',')

    # Statements
    def statement(self):
        self.repeat(self.newline)
        return self._statement()

    _statement = make_choice("simplestatement", "ifstatement", "whilestatement",
                             "defstatement", "objectstatement")

    def statements(self):
        return simpleast.Program(self.repeat(self.statement))

    def program(self):
        result = self.statements()
        self.repeat(self.newline)
        self.match("EOF")
        return result

    @specialize.arg(2)
    def block(self, header, beforeblock=None):
        self.match("Name", header)
        if beforeblock:
            result = self.call(beforeblock)
        else:
            result = None
        self.match("Special", ":")
        self.newline()
        self.match("Indent")
        block = self.statements()
        self.match("Dedent")
        return result, block


    def ifstatement(self):
        (expression, block) = self.block("if", self.expression)
        elseblock = self.maybe(self.elseblock)
        return simpleast.IfStatement(expression, block, elseblock)

    def elseblock(self):
        return self.block("else")[1]

    def whilestatement(self):
        (expression, block) = self.block("while", self.expression)
        return simpleast.WhileStatement(expression, block)

    def defstatement(self):
        (name_args, block) = self.block("def", self.functionheader)
        name = name_args[0]
        args = name_args[1:]
        return simpleast.FunctionDefinition(name, args, block)

    def functionheader(self):
        result = [self.name()]
        args = self.maybe(self._arglist_name)
        if args is not None:
            result.extend(args)
        return result

    _arglist_name = make_arglist("name")
        
    def objectstatement(self):
        (ast, block) = self.block(
            "object", self.objectheader)
        ast.block = block
        return ast

    def objectheader(self):
        name = self.name()
        args = self.maybe(self._arglist_parentdefinition)
        if args is None:
            args = []
        names = [arg.attrname for arg in args]
        expressions = [arg.expression for arg in args]
        return simpleast.ObjectDefinition(name, None, names, expressions)

    _arglist_parentdefinition = make_arglist("parentdefinition")

    def parentdefinition(self):
        name = self.name()
        self.match("Special", "=")
        result = self.expression()
        # XXX hack: use an Assignment node because it fits a bit
        return simpleast.Assignment(None, name, result)

    def simplestatement(self):
        result = self.expression()
        assigntoken = self.tokens[self.i]
        assign = self.maybe(self.assignment)
        self.newline()
        if assign:
            if (isinstance(result, simpleast.MethodCall) and
                    result.arguments == []):
                return simpleast.Assignment(
                        result.receiver, result.methodname, assign)
            else:
                source_pos = assigntoken.source_pos
                raise ParseError(source_pos,
                                 ErrorInformation(source_pos.i,
                                     customerror="can only assign to attribute"),
                                 self.source)
        return simpleast.ExprStatement(result)

    def assignment(self):
        self.match("Special", "=")
        return self.expression()

