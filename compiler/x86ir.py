
class Register(object):
    def __init__(self, name):
        self.register_name = name
    def __str__(self):
        return "Register(%s)" % (self.register_name)
    def __repr__(self):
        return self.__str__()    
    def x86name(self):
        return '%%%s' % self.register_name
class Pushl(object):
    def __init__(self, src):
        self.src = src
    def __str__(self):
        return "Pushl(%s)" % (self.src)
    def __repr__(self):
        return self.__str__()    
               
class Move(object):
    def __init__(self, src, dest):
        self.dest = dest
        self.src = src
    def __str__(self):
        return "movl %s, %s" % (self.src, self.dest)
    def __repr__(self):
        return self.__str__()
    
class Callf(object):
    def __init__(self, func):
        self.function = func
    def __str__(self):
        return "call %s" % self.function
    def __repr__(self):
        return self.__str__()
class UnarySub(object):
    def __init__(self, expr):
        self.expression = expr
    def get_expression(self):
        return self.expression
    def __str__(self):
        return "negl %s" % self.expression
    def __repr__(self):
        return self.__str__()
class Negl(object):
    def __init__(self, dest):
        self.dest = dest
    def __str__(self):
        return "Negl(%s)" % (self.dest)
    def __repr__(self):
        return self.__str__()          
class Addl(object):
    def __init__(self, src, dest):
        self.src = src
        self.dest = dest
    def __str__(self):
        return "Add(%s,%s)" % (self.src, self.dest)
    def __repr__(self):
        return self.__str__()
class Var(object):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return "Var(%s)" % (self.name)
    def __repr__(self):
        return self.__str__()
class Constant(object):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "$%s" % (self.value)
    def __repr__(self):
        return self.__str__()
