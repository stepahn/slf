from objmodel import W_Integer, W_NormalObject, W_Method
from simpleparser import parse
import primitives
import compile
from bytecode_interpreter import BytecodeInterpreter

class Interpreter(object):
    def __init__(self, builtins = None, use_bytecode = True):
        self.use_bytecode = use_bytecode
        self.builtins = W_NormalObject()
        if not builtins:
            builtins = self.read_builtins('slflib/builtins.slf')
        self.eval(parse(builtins), self.builtins)

    def read_builtins(self, fname):
        from pypy.rlib.streamio import open_file_as_stream
        s = open_file_as_stream(fname, 'r', 1024)

        code =''
        while True:
            next_line = s.readline()
            if not next_line:
                break
            code += next_line

        return code

    def eval(self, ast, w_context):
        if self.use_bytecode:
            return BytecodeInterpreter(compile.compile(ast), w_context, self).run()
        else:
            method = getattr(self, "eval_" + ast.__class__.__name__)
            return method(ast, w_context)

    def eval_Program(self, ast, context):
        retr = None
        for s in ast.statements:
            retr = self.eval(s, context)
        return retr

    def eval_Assignment(self, ast, context):
        receiver = self.eval(ast.lvalue, context)
        val = self.eval(ast.expression, context)
        receiver.setvalue(ast.attrname, val)

    def eval_IntLiteral(self, ast, context):
        int = W_Integer(ast.value)
        int.builtins = self.builtins
        return int

    def eval_IfStatement(self, ast, context):
        condition = self.eval(ast.condition, context)
        if condition.istrue():
            return self.eval(ast.ifblock, context)
        elif(ast.elseblock):
            return self.eval(ast.elseblock, context)

    def eval_FunctionDefinition(self, ast, context):
        context.setvalue(ast.name, W_Method({'name':ast.name, 'arguments':ast.arguments, 'block':ast.block, '__parent__':context}))

    def eval_MethodCall(self, ast, context):
        receiver = self.eval(ast.receiver, context)
        if ast.methodname == 'self':
            subject = receiver.getparents()[0]
        else:
            subject = receiver.getvalue(ast.methodname)
        if(subject.callable()):
            block = subject.getvalue('block')
            arg_names = subject.getvalue('arguments')
            arg_values = map(lambda a: self.eval(a, context), ast.arguments)
            method_context = W_NormalObject(dict(zip(arg_names, arg_values)))
            method_context.setvalue('__parent__', receiver)
            return self.eval(block,method_context)
        else:
            return subject

    def eval_ExprStatement(self, ast, context):
        return self.eval(ast.expression, context)

    def eval_ObjectDefinition(self, ast, context):
        parent_names = ast.parentnames
        parent_values = map(lambda a: self.eval(a, context), ast.parentdefinitions)
        parents = dict(zip(parent_names, parent_values))
        parents['__parent__'] = context
        obj = W_NormalObject(parents)
        obj.parents = parent_names
        self.eval(ast.block, obj)
        context.setvalue(ast.name, obj)
        return obj

    def eval_ImplicitSelf(self, ast, context):
        return context

    def eval_PrimitiveMethodCall(self, ast, context):
        receiver = self.eval(ast.receiver, context)
        arguments = map(lambda a: self.eval(a, context), ast.arguments)
        return primitives.call(ast.methodname, receiver, arguments, self.builtins)

    def eval_WhileStatement(self, ast, context):
        while self.eval(ast.condition, context).istrue():
            self.eval(ast.whileblock, context)

    def make_module(self):
        if self.builtins:
            return W_NormalObject({'__parent__':self.builtins})
        else:
            return W_NormalObject()
