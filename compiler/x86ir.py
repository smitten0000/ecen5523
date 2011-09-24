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
        return [self.dst]
    def reads(self):
        return [self.src]

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
        return [self.src]

class Addl(Instruction):
    def __init__(self, src, dst):
        self.src = src 
        self.dst = dst 
    def __str__(self):
        return "Addl(%s,%s)" % (self.src, self.dst)
    def __repr__(self):
        return self.__str__()
    def writes(self):
        return [self.dst]
    def reads(self):
        return [self.src, self.dst]

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
        return [self.operand]
    def reads(self):
        return [self.operand]

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
    def __init__(self, name):
        self.name = name
    def __str__(self):
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

class StackSlot(object):
    def __init__(self, slot):
        self.slot = slot
    def __str__(self):
        return "StackSlot(%s)" % (self.slot)
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return self.slot == other.slot
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return self.value.__hash__()
