from objmodel import W_Integer, W_NormalObject, W_Method
import compile
import primitives
import struct
import disass

class BytecodeInterpreter(object):
    def __init__(self, code, context, interpreter, debug_level=1):
        self.code = code
        self.context = context
        self.interpreter = interpreter
        self.pc = 0
        self.stack = []
        self.debug = interpreter.debug
        self.debug_level = debug_level
        if self.debug:
            print '(%d) dbg: >>>>>>>>>>>>>>>>>>>>>>>>>>>>' % self.debug_level

    def run(self):
        while self.pc < len(self.code.code):
            op = self.next_instruction()

            arg = 0
            if compile.isjump(op):
                arg = self.read_arg4()
            elif compile.hasarg(op):
                arg = self.read_smallarg()

            if self.debug:
                print '(%d) pc:%d op: %d (%s) args %d' % (self.debug_level, self.pc, op, disass.opcode2name[op], arg)
                print disass.disassemble(self.code, '(%d)' % self.debug_level, pc = self.pc)

            if op == compile.INT_LITERAL:
                self.op_int_literal(arg)
            elif op == compile.SET_LOCAL:
                # TODO something is strange
                t = self.stack.pop()
                self.op_implicit_self()
                self.stack.append(t)
                self.op_assignment(arg)
            elif op == compile.PRIMITIVE_METHOD_CALL:
                self.op_primitive_method_call(arg)
            elif op == compile.POP:
                self.stack.pop()
            elif op == compile.GET_LOCAL:
                self.op_implicit_self()
                self.op_method_lookup(arg)
                self.op_method_call(0)
            elif op == compile.JUMP_IF_FALSE:
                self.op_jump_if_false(arg)
            elif op == compile.JUMP:
                self.op_jump(arg)
            elif op == compile.MAKE_OBJECT:
                self.op_make_object(arg)
            elif op == compile.MAKE_OBJECT_CALL:
                self.op_make_object_call(arg)
            elif op == compile.ASSIGNMENT_APPEND_PARENT:
                self.op_assignment_append_parrent(arg)
            elif op == compile.METHOD_LOOKUP:
                self.op_method_lookup(arg)
            elif op == compile.METHOD_CALL:
                self.op_method_call(arg)
            elif op == compile.DUP:
                self.op_dup()
            elif op == compile.ASSIGNMENT:
                self.op_assignment(arg)
            elif op == compile.MAKE_FUNCTION:
                self.op_make_function(arg)
            elif op == compile.IMPLICIT_SELF:
                self.op_implicit_self()
            else:
                raise NotImplementedError(compile.opcode_names[op])
        return self.context

    def op_assignment(self, arg):
        name = self.lookup_symbol(arg)
        value = self.stack.pop()
        target = self.stack.pop()
        target.setvalue(name, value)
        self.stack.append(value)

    def op_assignment_append_parrent(self, arg):
        name = self.lookup_symbol(arg)
        parent = self.stack.pop()
        target = self.stack.pop()
        target.setvalue(name, parent)
        target.parents.append(name)
        self.stack.append(target)

    def op_dup(self):
        self.stack.append(self.stack[-1])

    def op_implicit_self(self):
        self.stack.append(self.context)

    def op_int_literal(self, arg):
        i = W_Integer(arg)
        i.builtins = self.interpreter.builtins
        self.stack.append(i)

    def op_jump(self, arg):
        self.pc += arg

    def op_jump_if_false(self, arg):
        acc = self.stack.pop()
        if acc.istrue() is not True:
            self.op_jump(arg)

    def op_make_function(self, arg):
        method = W_Method({'__parent__':self.context})
        method.block = self.lookup_subcode(arg)

        self.stack.append(method)

    def op_make_object(self, arg):
        name = self.lookup_symbol(arg)
        obj = W_NormalObject({'__parent__':self.context})
        self.stack.append(obj)

    def op_make_object_call(self, arg):
        code = self.lookup_subcode(arg)
        context = self.stack[-1]
        self.eval(code, context, self.interpreter)

    def op_method_call(self, arg):
        args = []
        for i in xrange(arg):
            args.insert(0,self.stack.pop())
        method = self.stack.pop()
        receiver = self.stack.pop()
        if isinstance(method, W_Method):
            code = method.block
            context = W_NormalObject()
            i = 0
            for a in args:
                context.setvalue(code.symbols[i], a)
                i += 1
            context.setvalue('self', receiver)
            context.setvalue('__parent__', receiver)
            res = self.eval(code, context, self.interpreter)
        else:
            res = method
        self.stack.append(res)

    def op_method_lookup(self, arg):
        name = self.lookup_symbol(arg)
        self.stack.append(self.stack[-1].getvalue(name))

    def op_primitive_method_call(self, arg):
        primitive = primitives.primitives_by_name[arg]
        arity = primitives.all_primitives_arg_count[arg]
        arguments = []
        for i in xrange(arity):
            arguments.append(self.stack.pop())
        receiver = self.stack.pop()
        res = primitives.call(primitive, receiver, arguments, self.interpreter.builtins)
        self.stack.append(res)

    def eval(self, code, context, interpreter):
        b = BytecodeInterpreter(code, context, interpreter, self.debug_level + 1)
        b.run()
        if self.debug:
            print '(%d) dbg: <<<<<<<<<<<<<<<<<<<<<<<<<<<<' % self.debug_level
        return b.stack[0]

    def read(self, next=1):
        if next == 1:
            c = self.code.code[self.pc]
            self.pc += 1
            return c
        else:
            c = []
            for i in xrange(next):
                c.append(self.code.code[self.pc])
                self.pc += 1
            return ''.join(c)

    def lookup_subcode(self, index):
        return self.code.subbytecodes[index]

    def lookup_symbol(self, index):
        return self.code.symbols[index]

    def next_instruction(self):
        return self.read_arg()

    def read_arg(self):
        v = ord(self.read())
        if v >= 128:
            v -= 256
        return v

    def read_arg4(self):
        c = self.read(4)
        highval = ord(c[3])
        if highval >= 128:
            highval -= 256
        return (ord(c[0]) | (ord(c[1]) << 8) | (ord(c[2]) << 16) | (highval << 24))

    def read_smallarg(self):
        i = self.read_arg()
        if i == -128:
            return self.read_arg4()
        else:
            return i
