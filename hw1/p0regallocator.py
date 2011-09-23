# vim: set ts=4 sw=4 expandtab:

from x86ir import *

class P0RegAllocator:
    ALL_REGS = [Register('eax'), Register('ebx'), Register('ecx'), Register('edx'), Register('edi'), Register('esi')]
    CALLER_SAVE = [Register('eax'), Register('ecx'), Register('edx')]
    def __init__(self, program):
        self.program = program
        self.liveness_after_k_dict={}
        self.interf_graph = {}
        self.register_assgnmnt = {}

    def _add_vertex(self,a):
        self.interf_graph[a] = set()

    def _add_edge(self,a,b):
        # if a == b, then this is a loop and we don't allow loops in an
        # undirected graph, so simply return
        if a == b:
            return 
        # add nodes to adjacency list if they don't exist
        if a not in self.interf_graph:
            self._add_vertex(a)
        if b not in self.interf_graph:
            self._add_vertex(b)
        # create the edges ; graph is undirected, so have to create edges 
        # for a -> b and b -> a since adjacency lists are directed by nature
        self.interf_graph[a].add(b)
        self.interf_graph[b].add(a)

    def liveness_analyze(self):
        instructions = self.program.instructions()
        num_instr = len(instructions)
        print "num_instr = ", num_instr
        alive = set()
        k = num_instr
        for instr in reversed(instructions):
            k = k - 1
            self.liveness_after_k_dict[k] = alive
            # get reads/writes performed by instruction
            writes = set(instr.writes())
            reads = set(instr.reads())
            # compute the live variables
            alive = (alive - writes) | reads
            # add all variables to the graph
            for x in writes: self._add_vertex(x)
            for x in reads: self._add_vertex(x)
        for k in range(0,len(instructions)):
            instr = instructions[k]
            print "%5s. %-40s : %s" % (k, instr, self.liveness_after_k_dict[k])
            k = k + 1

    def build_interference_graph(self):
        instructions = self.program.instructions()
        for k in range(0,len(instructions)):
            instr = instructions[k]
            # get the list of variables live at this point
            live_after_k = list(self.liveness_after_k_dict[k])
            # rule #1
            if isinstance(instr,Movl):
                for live in live_after_k:
                    if instr.dst != live or (isinstance(instr.src,Var) and instr.src != live):
                        self._add_edge(instr.dst, live)
            # rule #2
            elif isinstance(instr,(Addl,Negl)):
                for live in live_after_k:
                    if isinstance(instr, Addl):
                        self._add_edge(instr.dst, live)
                    elif isinstance(instr, Negl):   
                        self._add_edge(instr.operand, live)
            # rule #3
            elif isinstance(instr,Call):
                for live in live_after_k:
                    for reg in P0RegAllocator.CALLER_SAVE:
                        self._add_edge(live, reg)

    def saturation(self,node):
        """ Returns the saturation for a given vertex; the saturation is
        the size of the set of registers allocated for each neighbor"""
        registerset = set()
        for neighbor in self.interf_graph[node]:
            if neighbor in self.register_assgnmnt:
                registerset.add(self.register_assgnmnt[neighbor])
        return len(registerset)

    def color_graph(self):
        vertices = set(self.interf_graph.keys())
        while len(vertices) > 0:
            # don't you love python?
            nodesat = map(lambda x:(x,self.saturation(x)), vertices)
            node, sat = reduce(lambda x,y: max(x,y,key=lambda x:x[0]), nodesat)
            print "Node with highest saturation = %s (%s)" % (node, sat)
            registerset = set()
            for neighbor in self.interf_graph[node]:
                if neighbor in self.register_assgnmnt:
                    registerset.add(self.register_assgnmnt[neighbor])
            print "Register set for node = %s" % (registerset)
            lowest_unused = min(set(range(0,100))-registerset)
            #if len(registerset) > 0:
            #    lowest_unused = max(registerset)+1
            #else:
            #    lowest_unused = 0
            print "Lowest unused register = %s" % (lowest_unused)
            self.register_assgnmnt[node] = lowest_unused
            self.print_register_alloc()
            vertices = vertices - set([node])

    def print_graph(self):
        print "\nGraph:"
        for k in sorted(self.interf_graph.iterkeys(),key=lambda x:x.name):
            print "%-20s : %s" % (k,self.interf_graph[k])

    def print_register_alloc(self):
        print "\nRegister allocation:"
        for k in sorted(self.register_assgnmnt.iterkeys(),key=lambda x:x.name):
            print "%-20s : %s" % (k,self.register_assgnmnt[k])

    def get_assignment(self,varname):
        if varname not in self.register_assgnmnt:
            raise Exception("Unable to find assignment for variable '%s'" % varname)
        assignment = self.register_assgnmnt[varname]
        if assignment > len(P0RegAllocator.ALL_REGS)-1:
            stack_location = (assignment - len(P0RegAllocator.ALL_REGS)) * -4
            return Var(varname,stack_location)
        else:
            return P0RegAllocator.ALL_REGS[assignment]

    def substitute(self):
        """ Substitutes the register assignments in for the corresponding variables"""
        self.liveness_analyze()
        self.build_interference_graph()
        self.print_graph()
        self.color_graph()
        self.print_register_alloc()
        return self.visit(self.program)

    def visit(self, node, *args, **kwargs):
        meth = None
        meth_name = 'visit_'+node.__class__.__name__
        meth = getattr(self, meth_name, None)
        if not meth:
            raise Exception('Unknown node: %s method: %s' % (node.__class__, meth))
        return meth(node, *args, **kwargs)

    def visit_Program(self, node, *args, **kwargs):
        return Program([self.visit(x) for x in node.statements])

    def visit_Statement(self, node, *args, **kwargs):
        return Statement([self.visit(x) for x in node.instructions],node.source)

    def visit_Movl(self, node, *args, **kwargs):
        src = node.src
        dst = node.dst
        if isinstance(src,Var):
            src = self.get_assignment(src)
        if isinstance(dst,Var):
            dst = self.get_assignment(dst)
        return Movl(src,dst)
        
    def visit_Pushl(self, node, *args, **kwargs):
        src = node.src
        if isinstance(src,Var):
            src = self.get_assignment(src)
        return Pushl(src)
    
    def visit_Addl(self, node, *args, **kwargs):
        src = node.src
        dst = node.dst
        if isinstance(src,Var):
            src = self.get_assignment(src)
        if isinstance(dst,Var):
            dst = self.get_assignment(dst)
        return Addl(src,dst)

    def visit_Negl(self, node, *args, **kwargs):
        operand = node.operand
        if isinstance(operand,Var):
            operand = self.get_assignment(operand)
        return Negl(operand)

    def visit_Call(self, node, *args, **kwargs):
        return Call(node.func)



if __name__ == "__main__":
    import sys
    from comp_util import *
    from p0parser import P0Parser
    from p0flattener import P0Flattener
    from p0insselector import P0InstructionSelector
    if len(sys.argv) < 2:
        sys.exit(1)
    testcases = sys.argv[1:]
    for testcase in testcases:
        parser = P0Parser()
        parser.build()
        #ast = compiler.parseFile(testcase)
        ast = parser.parseFile(testcase)
        varalloc = VariableAllocator()
        p0flattener = P0Flattener(varalloc)
        stmtlist = p0flattener.flatten(ast)
        instruction_selector = P0InstructionSelector(varalloc)
        program = instruction_selector.visit(stmtlist)
        regallocator = P0RegAllocator(program)
        print regallocator.substitute()
