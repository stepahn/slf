from objmodel import W_Integer, W_NormalObject, W_Method
import primitives

registered_primitives = {
    '$int_add': 1,
    '$int_sub': 1,
    '$int_mul': 1,
    '$int_div': 1,
    '$int_mod': 1,
    '$bool_gz': 0,
    '$bool_nor': 1,
    '$math_sqrt': 0}
primitives_by_name = registered_primitives.keys()
all_primitives_arg_count = registered_primitives.values()

def call(methodname, receiver, argumments, builtins):
    method = getattr(primitives, methodname[1:])
    args = map(lambda i: i.getvalue(), [receiver] + argumments )
    int = W_Integer(method(args))
    int.builtins = builtins
    return int

def bool_nor(args):
    return int(not(args[0] or args[1]))

def bool_gz(args):
    return int(args[0] > 0)

def int_add(args):
    return args[0] + args[1]

def int_sub(args):
    return args[0] - args[1]

def int_mul(args):
    return args[0] * args[1]

def int_div(args):
    return args[0] / args[1]

def int_mod(args):
    return args[0] % args[1]

def math_sqrt(args):
    import math
    return int(math.sqrt(args[0]))

def debug(args):
    print "dbg: "+repr(args)

