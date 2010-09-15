class W_SimpleObject(object):
    def get_mro(self):
        import c3computation
        return c3computation.compute_C3_mro(self)

    def getvalue(self, key = None):
        for parent in self.get_mro():
            try:
                return parent.getval(key)
            except KeyError:
                pass
        return None

    def callable(self):
        self.get_mro()
        return False

    def clone(self):
        pass

class W_Integer(W_SimpleObject):
    def __init__(self, value):
        self.value = value
        self.builtins = None

    def __repr__(self):
        return '<W_Integer@%(id)x(%(value)d)>' % {'value':self.value, 'id':id(self)}

    def getparents(self):
        if self.builtins:
            inttrait = self.builtins.getvalue('inttrait')
            if inttrait:
                return [inttrait]
        return []

    def getval(self, key):
        if key:
            raise KeyError
        return self.value

    def istrue(self):
        return self.value != 0

class W_NormalObject(W_SimpleObject):
    def __init__(self, values=None):
        if values is None:
            values = {}
        self.values = values
        self.parents = []
    def __repr__(self):
        return '<W_NormalObject@%(id)x(%(values)s)>' % {'values':self.values, 'id':id(self)}

    def clone(self):
        return self.__class__(dict(self.values))

    def getname(self):
        return self['name']

    def getparents(self):
        parents = [self.values[p] for p in self.parents]
        try:
            parents.append(self.values['__parent__'])
        except KeyError:
            pass
        return parents

    def getval(self, key):
        return self.values[key]

    def istrue(self):
        return True

    def setvalue(self, key, value):
        self.values[key] = value

class W_Method(W_NormalObject):
    block = None

    def callable(self):
        self.get_mro()
        return True

    def __repr__(self):
        return '<W_Method@%(id)x(%(values)s)>' % {'values':self.values, 'id':id(self)}
