# vim: set ts=4 sw=4 expandtab:

from compiler.ast import Node, flatten

class Instruction(Node):
    def writes(self):
        raise NotImplementedError('writes() not implemented')
    def reads(self):
        raise NotImplementedError('reads() not implemented')

class Program(Node):
    def __init__(self, statements):
        self.statements = statements
    def __str__(self):
        return "Program([%s])" % ",".join([str(x) for x in self.statements])
    def __repr__(self):
        return self.__str__()
    def getChildren(self):
        return tuple(flatten(self.statements))
    def instructions(self):
        instructions=[]
        for statement in self.statements:
            for instr in statement.instructions:
                instructions.append(instr)
        return instructions

class Statement(Node):
    def __init__(self, instructions, source):
        self.instructions = instructions
        self.source = source
    def __str__(self):
        #return "Statement([%s],'%s')" % (",".join([str(x) for x in self.instructions]), self.source)
        return "Statement([%s])" % (",".join([str(x) for x in self.instructions]))
    def __repr__(self):
        return self.__str__()
    def getChildren(self):
        l=[]
        l.extend(flatten(self.instructions))
#        l.append(self.source)
        return tuple(l)
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

class Register(Node):
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

class Var(Node):
    def __init__(self, name, spillable=True, storage=None):
        self.name = name
        self.spillable = spillable
        self.storage = None   # one of Register() or StackSlot()
    def __str__(self):
        if self.storage is not None:
            if isinstance(self.storage, (Register,StackSlot)):
                return str(self.storage)
            else:
                assert(False)
        return "Var('%s')" % (self.name)
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return self.name == other.name
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return self.name.__hash__()
    # need this for set operations b/c Node overrides __iter__ to
    # call getChildren().  Nasty.
    def getChildren(self):
        return tuple()

class Imm32(Node):
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

class StackSlot(Node):
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
    def __init__(self, src, dst, direction):
        self.src = src 
        self.dst = dst 
        self.dir = direction
    def __str__(self):
        return "BitShift%s(%s,%s)" % (self.dir, self.src, self.dst)
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return self.src == other.src and self.dst == other.dst and self.dir == other.dir
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return self.value.__hash__()
    def writes(self):
        return [self.dst]
    def reads(self):
        return [self.src, self.dst]
        
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

class x86If(Node):
    def __init__(self, test, then, else_):
        self.test = test
        self.then = then
        self.else_ = else_
    def __str__(self):
        return "x86If(%s,%s,%s)" % (self.test, self.then, self.else_)
    def __repr__(self):
        return self.__str__()
    def getChildren(self):
        return (self.test, self.then, self.else_)

class x86Function(Node):
    def __init__(self, name, argnames, statements, lineno=None):
        self.name = name
        self.argnames = argnames
        self.statements = statements
        self.lineno = lineno
    def __str__(self):
        return "x86Function(%s, [%s])" % (self.name,",".join([str(x) for x in self.argnames]))
    def __repr__(self):
        return self.__str__()
    def getChildren(self):
        l=[self.name]
        l.extend(self.argnames)
        l.extend(flatten(self.statements))
        return tuple(l)
    def instructions(self):
        instructions=[]
        for statement in self.statements:
            for instr in statement.instructions:
                instructions.append(instr)
        return instructions

class x86While(Node):
    def __init__(self, test, body, else_, lineno=None):
        self.test = test
        self.body = body
        self.else_ = else_
        self.lineno = lineno

    def getChildren(self):
        children = []
        children.append(self.test)
        children.append(self.body)
        children.append(self.else_)
        return tuple(children)

    def getChildNodes(self):
        nodelist = []
        nodelist.append(self.test)
        nodelist.append(self.body)
        if self.else_ is not None:
            nodelist.append(self.else_)
        return tuple(nodelist)

    def __str__(self):
        return "x86While(%s, %s, %s)" % (self.test, self.body, self.else_)
    def __repr__(self):
        return self.__str__()

class CallAddress(Instruction):
    def __init__(self, address):
        self.address = address
    def __str__(self):
        return "CallAddress(%s)" % (self.address)
    def __repr__(self):
        return self.__str__()
    def writes(self):
        return []
    def reads(self):
        return [self.address]

class Ret(Instruction):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "Ret(%s)" % (self.value)
    def __repr__(self):
        return self.__str__()
    def writes(self):
        return [Register('eax')]
    def reads(self):
        return [self.value]
