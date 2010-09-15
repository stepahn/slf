from objmodel import W_Integer, W_NormalObject, W_Method

primitives = {}
primitives_by_name = []
all_primitives_arg_count = []

def register(argscount):
    def g(f):
        name = '$'+f.__name__

        primitives_by_name.append(name)
        all_primitives_arg_count.append(argscount)
        primitives[name] = f

        return f
    return g

def call(methodname, receiver, arguments, builtins):
    method = primitives[methodname]
    args = []

    args.append(receiver.getvalue('').intvalue())

    for a in arguments:
        if a:
            args.append(a.intvalue())
        else:
            args.append(0)

    my_int = W_Integer(method(args))
    my_int.builtins = builtins
    return my_int

@register(1)
def bool_nor(args):
    return int(not(args[0] or args[1]))

@register(0)
def bool_gz(args):
    return int(args[0] > 0)

@register(1)
def int_add(args):
    return args[0] + args[1]

@register(1)
def int_sub(args):
    return args[0] - args[1]

@register(1)
def int_mul(args):
    return args[0] * args[1]

@register(1)
def int_div(args):
    return args[0] / args[1]

@register(1)
def int_mod(args):
    return args[0] % args[1]

@register(0)
def math_sqrt(args):
    import math
    return int(math.sqrt(args[0]))

@register(1)
def math_pow(args):
    import math
    return int(math.pow(args[0], args[1]))

@register(0)
def puts(args):
    print args[0]
    return args[0]


