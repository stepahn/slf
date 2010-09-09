"""This file contains the bytecode-compiler.

An instruction can have one or no arguments. There are two different ways how
an argument is encoded:

    ARG4 encodes an argument in 4 bytes, in a little-endian manner

    SMALLARG encodes an integer i differently based on its size:
        if -127 <= i <= 127 the integers is encoded as one byte
        otherwise it is encoded as 5 bytes:
            1 marker byte equal to -128 to signify that the large form is used
            4 bytes to encode the integer as with ARG4

The instruction set contains the following instructions:

    INT_LITERAL <SMALLARG>
    Pushes an integer literal on the stack. The argument is the value of the
    integer.

    IMPLICIT_SELF
    Pushes the implicit self on the stack.

    POP
    Pops the top element from the stack.

    DUP
    Duplicates the top element of the stack.

    JUMP <ARG4>
    Unconditionally jump to a different point in the program. The offset of the
    program counter to the target is given by the argument.

    JUMP_IF_FALSE <ARG4>
    Pops an object from the stack and jump to a different point in the program
    if that object is false. The offset of the program counter to the target is
    given by the argument.

    ASSIGNMENT <SMALLARG>
    Assigns the first object on the stack to the second object on the stack.
    The objects are popped from the stack, and then the assigned object
    (i.e. the `expression') is pushed again.  The attribute name is given by
    the argument, which is an index into the symbols list of the bytecode
    object.

    PRIMITIVE_METHOD_CALL <SMALLARG>
    Call a primitive method. The argument is an index into a list of all
    primitives, which must be defined in the "primitive" module. The arguments
    are found on the stack and are popped by this bytecode; the result is
    pushed on the stack. To make the compiler work correctly for primitives,
    the "primitive" module needs to expose a global dictionary
    "primitives_by_name", which maps primitive name to a primitive number.

    METHOD_LOOKUP <SMALLARG>
    Looks up a method in the object at the top of the stack. The method name
    is given by the argument, which is an index into the symbols list of the
    bytecode object. The method is pushed on the stack (and the original
    object is not removed).

    METHOD_CALL <SMALLARG>
    Calls a method. The first n (where n is the argument of the bytecode) are
    the arguments to the method, in reverse order. The next object on the
    stack is the method. The final object is the receiver. All these objects
    are popped from the stack. The result of the method call is pushed.

    MAKE_FUNCTION <SMALLARG>
    Creates a new W_Method object and pushes it on the stack. The bytecode of
    the method can be found in the subbytecodes list of the current bytecode
    object; the index is given by the argument.

    MAKE_OBJECT <SMALLARG>
    Create a new (empty) object and pushes it on the stack. The argument (which
    can be ignored for now) is the index in symbols of the name of the object.

    ASSIGNMENT_APPEND_PARENT <SMALLARG>
    Adds a new parent to an object. This bytecode is only used during object
    creation. It works like the ASSIGNMENT bytecode, but (1) it also adds the
    name to the list of parent attributes of the object, and (2) it leaves
    on the stack the assigned-to object (the `lvalue'), not the assigned
    object (the `expression').

    MAKE_OBJECT_CALL <SMALLARG>
    Execute the body of a newly created object. The object is on the top of the
    stack and is left there. The bytecode of the body can be found in the
    subbytecodes list of the current bytecode object, the index is given by the
    argument.

    GET_LOCAL <SMALLARG>
    This is an optimization for the common case of sending a method without
    arguments to the implicit self. This bytecode is equivalent to:
        IMPLICIT_SELF
        METHOD_LOOKUP <SMALLARG>
        METHOD_CALL 0

    SET_LOCAL <SMALLARG>
    This is an optimization for the common case of writing a slot to the
    implicit self. This bytecode is equivalent to:
        IMPLICIT_SELF
        ASSIGNMENT <SMALLARG>

Note that there is no "return" bytecode. When the end of the bytecode is
reached, the top of the stack is returned (and the stack should have only one
element on it).
"""
import sys
from pypy.rlib.objectmodel import specialize

import simpleast

# ---------- bytecodes ----------

INT_LITERAL = 2               # integer value
ASSIGNMENT = 4                # index of attrname
METHOD_LOOKUP = 5             # index of method name
METHOD_CALL = 6               # number of arguments
PRIMITIVE_METHOD_CALL = 7     # number of the primitive
MAKE_FUNCTION = 8             # bytecode literal index
MAKE_OBJECT = 9               # index of object name
ASSIGNMENT_APPEND_PARENT = 10 # index of parentname
MAKE_OBJECT_CALL = 11         # bytecode literal index
JUMP_IF_FALSE = 12            # offset
JUMP = 13                     # offset
GET_LOCAL = 15                # index of attrname (optimization)
SET_LOCAL = 16                # index of attrname (optimization)

IMPLICIT_SELF = 32            # (no argument)
POP = 33                      # (no argument)
DUP = 34                      # (no argument)

opcode_names = [None] * 256
for key, value in globals().items():
    if key.strip("_").isupper():
        opcode_names[value] = key



def hasarg(opcode):
    """ Helper function to determine whether an opcode has an argument."""
    return opcode < 32

def isjump(opcode):
    """ Helper function to determine whether an opcode is a jump."""
    return opcode == JUMP_IF_FALSE or opcode == JUMP


class Bytecode(object):
    """ A class representing the bytecode of one piece of code.

    self.code is a string that encodes the bytecode itself.

    self.symbols is a list of strings containing the names that occur in the
    piece of code.

    self.subbytecodes is a list of further bytecodes that occur in the piece of
    code.
    """
    _immutable_ = True
    _immutable_fields_ = ["symbols[*]", "subbytecodes[*]"]

    def __init__(self, code, name, symbols,
                 subbytecodes, numargs, stackdepth):
        self.code = code
        if name is None:
            name = "?"
        self.name = name
        self.symbols = symbols
        self.subbytecodes = subbytecodes
        self.numargs = numargs
        self.stackdepth = stackdepth

    def dis(self, pc=-1):
        from disass import disassemble
        disassemble(self, pc=pc)


# ---------- compiler ----------

def compile(ast, argumentnames=[], name=None):
    """ Turns an AST into a Bytecode object."""
    assert isinstance(ast, simpleast.Program)
    comp = Compiler()
    for arg in argumentnames:
        comp.lookup_symbol(arg)
    comp.lookup_symbol("__parent__")
    comp.lookup_symbol("self")
    comp.compile(ast, True)
    return comp.make_bytecode(len(argumentnames), name)


stack_effects = {
    INT_LITERAL: 1,
    ASSIGNMENT: -1,
    METHOD_LOOKUP: 1,
    MAKE_FUNCTION: 1,
    MAKE_OBJECT: 1,
    ASSIGNMENT_APPEND_PARENT: -1,
    MAKE_OBJECT_CALL: 0,
    GET_LOCAL: 1,
    SET_LOCAL: 0,
    JUMP: 0,
    JUMP_IF_FALSE: -1,
    IMPLICIT_SELF: 1,
    POP: -1,
    DUP: 1,
}


class Compiler(object):

    def __init__(self):
        self.code = []
        self.symbols = {}
        self.subbytecodes = []
        self.stackdepth = 0
        self.max_stackdepth = 0

    def make_bytecode(self, numargs, funcname):
        symbols = [None] * len(self.symbols)
        for name, index in self.symbols.items():
            symbols[index] = name
        result = Bytecode(''.join(self.code),
                        funcname,
                        symbols,
                        self.subbytecodes,
                        numargs, self.max_stackdepth)
        assert self.stackdepth == 1
        return result

    def stack_effect(self, num):
        self.stackdepth += num
        self.max_stackdepth = max(self.stackdepth, self.max_stackdepth)

    @specialize.argtype(2)
    def emit(self, opcode, arg=None, stackeffect=sys.maxint):
        self.code.append(chr(opcode))
        if isjump(opcode):
            assert arg is None
            for c in self.encode4(0):
                self.code.append(c)
        elif hasarg(opcode):
            assert isinstance(arg, int)
            if -127 <= arg <= 127:
                self.code.append(chr(arg & 0xFF))
            else:
                self.code.append(chr(128))
                for c in self.encode4(arg):
                    self.code.append(c)
        else:
            assert arg is None

        if opcode in stack_effects:
            stackeffect = stack_effects[opcode]
        else:
            assert stackeffect != sys.maxint
        self.stack_effect(stackeffect)

    def get_position(self):
        return len(self.code)

    def set_target_position(self, oldposition, newtarget):
        offset = newtarget - (oldposition+5)
        i = 0
        for c in self.encode4(offset):
            self.code[oldposition+1+i] = c
            i += 1

    def encode4(self, value):
        return [chr(value & 0xFF),
                chr((value >> 8) & 0xFF),
                chr((value >> 16) & 0xFF),
                chr((value >> 24) & 0xFF)]

    def lookup_symbol(self, symbol):
        if symbol not in self.symbols:
            self.symbols[symbol] = len(self.symbols)
        return self.symbols[symbol]


    def compile(self, ast, needsresult=True):
        return ast.dispatch(self, needsresult)

    def compile_IntLiteral(self, astnode, needsresult):
        self.emit(INT_LITERAL, astnode.value)

    def compile_ImplicitSelf(self, astnode, needsresult):
        self.emit(IMPLICIT_SELF)

    def compile_Assignment(self, astnode, needsresult):
        if isinstance(astnode.lvalue, simpleast.ImplicitSelf):
            self.compile(astnode.expression)
            self.emit(SET_LOCAL, self.lookup_symbol(astnode.attrname))
        else:
            self.compile(astnode.lvalue)
            self.compile(astnode.expression)
            self.emit(ASSIGNMENT, self.lookup_symbol(astnode.attrname))
        if not needsresult:
            self.emit(POP)

    def compile_ExprStatement(self, astnode, needsresult):
        self.compile(astnode.expression)
        if not needsresult:
            self.emit(POP)

    def compile_MethodCall(self, astnode, needsresult):
        numargs = len(astnode.arguments)
        if (isinstance(astnode.receiver, simpleast.ImplicitSelf) and
                numargs == 0):
            self.emit(GET_LOCAL, self.lookup_symbol(astnode.methodname))
        else:
            self.compile(astnode.receiver)
            self.emit(METHOD_LOOKUP, self.lookup_symbol(astnode.methodname))
            for arg in astnode.arguments:
                self.compile(arg)
            self.emit(METHOD_CALL, numargs, -numargs - 1)

    def compile_PrimitiveMethodCall(self, astnode, needsresult):
        import primitives
        try:
            index = primitives.primitives_by_name.index(astnode.methodname)
        except ValueError:
            raise KeyError('primitive not registered', astnode.methodname)

        assert (len(astnode.arguments) ==
                primitives.all_primitives_arg_count[index])
        self.compile(astnode.receiver)
        for arg in astnode.arguments:
            self.compile(arg)
        self.emit(PRIMITIVE_METHOD_CALL, index, -len(astnode.arguments))

    def compile_ObjectDefinition(self, astnode, needsresult):
        self.emit(MAKE_OBJECT, self.lookup_symbol(astnode.name))
        #
        for i in range(len(astnode.parentdefinitions)):
            name = astnode.parentnames[i]
            if name == "__parent__":
                self.emit(DUP)
                self.compile(astnode.parentdefinitions[i])
                self.emit(ASSIGNMENT, self.lookup_symbol(name))
                self.emit(POP)
            else:
                self.compile(astnode.parentdefinitions[i])
                self.emit(ASSIGNMENT_APPEND_PARENT, self.lookup_symbol(name))
        #
        bytecode = compile(astnode.block, name=astnode.name)
        index = len(self.subbytecodes)
        self.subbytecodes.append(bytecode)
        self.emit(MAKE_OBJECT_CALL, index)
        self.emit(SET_LOCAL, self.lookup_symbol(astnode.name))
        if not needsresult:
            self.emit(POP)

    def compile_Program(self, astnode, needsresult):
        for statement in astnode.statements[:-1]:
            self.compile(statement, needsresult=False)
        laststatement = astnode.statements[-1]
        self.compile(laststatement, needsresult)

    def compile_FunctionDefinition(self, astnode, needsresult):
        bytecode = compile(astnode.block, astnode.arguments, astnode.name)
        index = len(self.subbytecodes)
        self.subbytecodes.append(bytecode)
        self.emit(MAKE_FUNCTION, index)
        self.emit(SET_LOCAL, self.lookup_symbol(astnode.name))
        if not needsresult:
            self.emit(POP)

    def compile_IfStatement(self, astnode, needsresult):
        # XXX this can compute the needed stack by one too much
        self.compile(astnode.condition)
        position1 = self.get_position()
        self.emit(JUMP_IF_FALSE)
        #
        self.compile(astnode.ifblock, needsresult)
        position2 = self.get_position()
        self.emit(JUMP)
        #
        self.set_target_position(position1, self.get_position())
        if astnode.elseblock:
            self.compile(astnode.elseblock, needsresult)
        else:
            if needsresult:
                self.emit(IMPLICIT_SELF)
        if needsresult:
            self.stack_effect(-1)
        #
        self.set_target_position(position2, self.get_position())

    def compile_WhileStatement(self, astnode, needsresult):
        if needsresult:
            self.emit(IMPLICIT_SELF)
        #
        position1 = self.get_position()
        self.compile(astnode.condition)
        position2 = self.get_position()
        self.emit(JUMP_IF_FALSE)
        #
        if needsresult:
            self.emit(POP)
        self.compile(astnode.whileblock, needsresult)
        position3 = self.get_position()
        self.emit(JUMP)
        self.set_target_position(position3, position1)
        #
        self.set_target_position(position2, self.get_position())
