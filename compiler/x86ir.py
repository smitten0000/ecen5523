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

class Statement(Instruction):
    def __init__(self, instructions, source):
        self.instructions = instructions
        self.source = source
    def __str__(self):
        return "Statement([%s],'%s')" % (",".join([str(x) for x in self.instructions]), self.source)
    def __repr__(self):
        return self.__str__()
    def writes(self):
        return reduce(lambda x,y: x+y, [x.writes() for x in self.instructions])
    def reads(self):
        return reduce(lambda x,y: x+y, [x.reads() for x in self.instructions])

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

class Cmp(Instruction):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
    def __str__(self):
        return "Cmp(%s, %s)" % (self.lhs, self.rhs)
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return self.lhs == other.lhs and self.rhs == other.rhs
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return self.lhs.__hash__()+self.rhs.__hash__()
    def writes(self):
        return []
    def reads(self):
        return [self.lhs, self.rhs]

class CmpNe(Cmp):
    def __init__(self, lhs, rhs):
        Cmp.__init__(lhs,rhs)
    def __str__(self):
        return "CmpNe(%s, %s)" % (self.lhs, self.rhs)
    def __repr__(self):
        return self.__str__()
    
class BitwiseNot(Instruction):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "BitwiseNot(%s)" % (self.value)
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return self.value == other.value
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return self.value.__hash__()
    def writes(self):
        return [self.value]
    def reads(self):
        return [self.value]
    
class BitwiseAnd(Instruction):
    def __init__(self, src, dst):
        self.src = src 
        self.dst = dst 
    def __str__(self):
        return "BitwiseAnd(%s,%s)" % (self.src, self.dst)
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return self.src == other.src and self.dst == other.dst
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return self.value.__hash__()
    def writes(self):
        return [self.dst]
    def reads(self):
        return [self.src, self.dst]

class BitwiseOr(Instruction):
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst 
    def __str__(self):
        return "BitwiseOr(%s,%s)" % (self.src, self.dst)
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return self.src == other.src and self.dst == other.dst
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return self.value.__hash__()
    def writes(self):
        return [self.dst]
    def reads(self):
        return [self.src, self.dst]
    
class BitShift(Instruction):
    def __init__(self, value, places, direction):
        self.value = value
        self.places = places
        self.dir = direction
    def __str__(self):
        return "BitShift%s(%s,%s)" % (self.dir, self.value, self.places)
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return self.value == other.value and self.places == other.places and self.dir == other.dir
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return self.value.__hash__()
    def writes(self):
        return [self.value]
    def reads(self):
        return [self.value]
        
class Label(Instruction):
    def __init__(self, label):
        self.label = label
    def __str__(self):
        return "Label(%s)" % self.label
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return self.label == other.label
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return self.label.__hash__()
    def writes(self):
        return []
    def reads(self):
        return []
    
class Jump(Instruction):
    def __init__(self, label):
        self.label = label
    def __str__(self):
        return "Jump(%s)" % self.label
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return self.label == other.label
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return self.label.__hash__()
    def writes(self):
        return []
    def reads(self):
        return []
    
class JumpEquals(Jump):
    def __init__(self, label):
        Jump.__init__(self, label)
    def __str__(self):
        return "JumpEquals(%s)" % self.label
