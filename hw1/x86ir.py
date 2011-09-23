# vim: set ts=4 sw=4 expandtab:

class Instruction(object):
    def writes(self):
        raise NotImplementedError('writes() not implemented')
    def reads(self):
        raise NotImplementedError('reads() not implemented')

class Program(object):
    def __init__(self, statements):
        self.statements = statements
    def __str__(self):
        return "Program([%s])" % ",".join([str(x) for x in self.statements])
    def __repr__(self):
        return self.__str__()
    def instructions(self):
        instructions=[]
        for statement in self.statements:
            for instr in statement.instructions:
                instructions.append(instr)
        return instructions

class Statement(object):
    def __init__(self, instructions, source):
        self.instructions = instructions
        self.source = source
    def __str__(self):
        return "Statement([%s],'%s')" % (",".join([str(x) for x in self.instructions]), self.source)
    def __repr__(self):
        return self.__str__()

class Movl(Instruction):
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst
    def __str__(self):
        return "Movl(%s,%s)" % (self.src, self.dst)
    def __repr__(self):
        return self.__str__()
    def writes(self):
        if isinstance(self.dst, Var):
            return [self.dst]
        return []
    def reads(self):
        if isinstance(self.src, Var): return [self.src]
        return []

class Pushl(Instruction):
    def __init__(self, src):
        self.src = src 
    def __str__(self):
        return "Pushl(%s)" % (self.src)
    def __repr__(self):
        return self.__str__()
    def writes(self):
        return []
    def reads(self):
        if isinstance(self.src, Var): return [self.src]
        return []

class Addl(Instruction):
    def __init__(self, src, dst):
        self.src = src 
        self.dst = dst 
    def __str__(self):
        return "Addl(%s,%s)" % (self.src, self.dst)
    def __repr__(self):
        return self.__str__()
    def writes(self):
        if isinstance(self.dst, Var): return [self.dst]
        return []
    def reads(self):
        varreads = []
        if isinstance(self.src, Var): varreads.append(self.src)
        if isinstance(self.dst, Var): varreads.append(self.dst)
        return varreads

class Call(Instruction):
    def __init__(self, func):
        self.func = func
    def __str__(self):
        return "Call('%s')" % (self.func)
    def __repr__(self):
        return self.__str__()
    def writes(self):
        return []
    def reads(self):
        return []

class Negl(Instruction):
    def __init__(self, operand):
        self.operand = operand
    def __str__(self):
        return "Negl(%s)" % (self.operand)
    def __repr__(self):
        return self.__str__()
    def writes(self):
        if isinstance(self.operand, Var): return [self.operand]
        return []
    def reads(self):
        if isinstance(self.operand, Var): return [self.operand]
        return []

class Register(object):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return "Register('%s')" % (self.name)
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return self.name == other.name
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return self.name.__hash__()

class Var(object):
    def __init__(self, name, stackloc=None):
        self.name = name
        self.stackloc = stackloc
    def __str__(self):
        if self.stackloc is not None:
            return "Var('%s',%s)" % (self.name, self.stackloc)
        else:
            return "Var('%s')" % (self.name)
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return self.name == other.name
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return self.name.__hash__()

class Imm32(object):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "Imm32(%s)" % (self.value)
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return self.value == other.value
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return self.value.__hash__()
