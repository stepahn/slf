builtincode = """
object inttrait:
    def add(i):
        self $int_add(i)
    def sub(i):
        self $int_sub(i)
    def mul(i):
        self $int_mul(i)
    def div(i):
        self $int_div(i)
    def mod(i):
        self $int_mod(i)
    def eq(i):
        bool eq(self, i)
    def neq(i):
        bool not(eq(i))

object bool:
    def and(a,b):
        nor(nor(a,a), nor(b,b))

    def eq(a,b):
        if a sub(b):
            0
        else:
            1

    def gz(a):
        a $bool_gz

    def not(a):
        if a:
            0
        else:
            1

    def nor(a,b):
        a $bool_nor(b)

object math:
    def sqrt(i):
        i $math_sqrt

    def isprime(i):
        prime = 0
        if bool and(i neq(0), i neq(1)):
            prime = 1
            if i neq(2):
                upto = math sqrt(i) add(1)
                testing = 2
                while testing:
                    prime = i mod(testing)
                    if prime:
                        if upto neq(testing):
                            testing = testing add(1)
                        else:
                            testing = 0
                    else:
                        testing = 0
        prime
"""
