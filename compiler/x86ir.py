
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
    def __init__(self, lhs, rhs):
        self.left = lhs
        self.right = rhs
    def __str__(self):
        return "movl %s %s" % (self.right, self.left)
    def __repr__(self):
        return self.__str__()
    
class Call(object):
    def __init__(self, func):
        self.function = func
    
class UnarySub(object):
    def __init__(self, expr):
        self.expression = expr
    def get_expression(self):
        return self.expression
class Negl(object):
    def __init__(self, left):
        self.left = left
    def __str__(self):
        return "Negl(%s)" % (self.left)
    def __repr__(self):
        return self.__str__()          
class Addl(object):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __str__(self):
        return "Add(%s,%s)" % (self.left, self.right)
    def __repr__(self):
        return self.__str__()
class Var(object):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return "Var(%s)" % (self.name)
    def __repr__(self):
        return self.__str__()
class Const(object):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "$%s" % (self.value)
    def __repr__(self):
        return self.__str__()