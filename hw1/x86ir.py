# vim: set ts=4 sw=4 expandtab:

class Program(object):
    def __init__(self, statements):
        self.statements = statements
    def __str__(self):
        return "Program([%s])" % ",".join([str(x) for x in self.statements])

class Statement(object):
    def __init__(self, instructions, source):
        self.instructions = instructions
        self.source = source
    def __str__(self):
        return "Statement([%s],'%s')" % (",".join([str(x) for x in self.instructions]), self.source)

class Register(object):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return "Register('%s')" % (self.name)

class Movl(object):
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst
    def __str__(self):
        return "Movl(%s,%s)" % (self.src, self.dst)

class Pushl(object):
    def __init__(self, src):
        self.src = src 
    def __str__(self):
        return "Pushl(%s)" % (self.src)

class Addl(object):
    def __init__(self, src, dst):
        self.src = src 
        self.dst = dst 
    def __str__(self):
        return "Add(%s,%s)" % (self.src, self.dst)

class Call(object):
    def __init__(self, func):
        self.func = func
    def __str__(self):
        return "Call('%s')" % (self.func)

class Negl(object):
    def __init__(self, operand):
        self.operand = operand
    def __str__(self):
        return "Negl(%s)" % (self.operand)

class Var(object):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return "Var('%s')" % (self.name)

class Imm32(object):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "Imm32(%s)" % (self.value)
