import compile

def disassemble(bytecode, indent='', pc=-1):
    """ disassemble a bytecode object and print a readabable version of it"""
    assert isinstance(bytecode, compile.Bytecode)
    findlabeltargets = FindLabelTargets()
    findlabeltargets.disassemble(bytecode)
    disass = Disassembler(indent, findlabeltargets.targets)
    disass.disassemble(bytecode, pc)


opcode2name = {}
for name, value in compile.__dict__.items():
    if name == name.upper() and isinstance(value, int):
        opcode2name[value] = name


class AbstractDisassembler(object):

    def read4(self, code, pc):
        highval = ord(code[pc+3])
        if highval >= 128:
            highval -= 256
        return (ord(code[pc]) |
                (ord(code[pc+1]) << 8) |
                (ord(code[pc+2]) << 16) |
                (highval << 24))

    def disassemble(self, bytecode, currpc=-1):
        self.currpc = currpc
        self.bytecode = bytecode
        code = bytecode.code
        pc = 0
        while pc < len(code):
            self.start(pc)
            opcode = ord(code[pc])
            pc += 1
            if compile.isjump(opcode):
                oparg = self.read4(code, pc)
                pc += 4
            elif compile.hasarg(opcode):
                oparg = ord(code[pc])
                pc += 1
                if oparg >= 128:
                    if oparg > 128:
                        oparg -= 256
                    else:
                        oparg = self.read4(code, pc)
                        pc += 4
            else:
                oparg = None
            self.pc = pc
            self.end(opcode, oparg)
            name = opcode2name[opcode]
            method = getattr(self, name, self.dummy)
            method(opcode, oparg)

    def start(self, pc):
        pass

    def end(self, opcode, oparg):
        pass

    def dummy(self, opcode, oparg):
        pass


class FindLabelTargets(AbstractDisassembler):

    def __init__(self):
        self.targets = {}

    def JUMP_IF_FALSE(self, opcode, oparg):
        self.targets[self.pc + oparg] = True

    JUMP = JUMP_IF_FALSE


class Disassembler(AbstractDisassembler):

    def __init__(self, indent, targets):
        self.indent = indent
        self.targets = targets

    def start(self, pc):
        if pc in self.targets:
            print self.indent, '>>', pc
        if pc == self.currpc:
            print self.indent, '->', pc

    def end(self, opcode, oparg):
        print self.indent, '\t', opcode2name[opcode],

    def JUMP_IF_FALSE(self, opcode, oparg):
        print '\t', '-->', self.pc + oparg

    JUMP = JUMP_IF_FALSE

    def ASSIGNMENT(self, opcode, oparg):
        print '\t', repr(self.bytecode.symbols[oparg])

    METHOD_LOOKUP = ASSIGNMENT
    ASSIGNMENT_APPEND_PARENT = ASSIGNMENT
    GET_LOCAL = ASSIGNMENT
    SET_LOCAL = ASSIGNMENT

    def PRIMITIVE_METHOD_CALL(self, opcode, oparg):
        import primitive
        func = primitive.all_primitives[oparg]
        print '\t', repr('$' + func.func_name)

    def dummy(self, opcode, oparg):
        if oparg is None:
            print
        else:
            print '\t', oparg


