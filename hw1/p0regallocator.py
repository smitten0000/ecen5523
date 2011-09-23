# vim: set ts=4 sw=4 expandtab:

from x86ir import *

class P0RegAllocator:
    ALL_REGS = [Register('eax'), Register('ebx'), Register('ecx'), Register('edx'), Register('edi'), Register('esi')]
    CALLER_SAVE = [Register('eax'), Register('ecx'), Register('edx')]
    def __init__(self, program):
        self.liveness_after_k_dict={}
        self.program = program
        self.interf_graph = {}
        self.register_assgnmnt = {}

    def _add_edge(self,a,b):
        # if a == b, then this is a loop and we don't allow loops in an
        # undirected graph, so simply return
        if a == b:
            return 
        # add nodes to adjacency list if they don't exist
        if a not in self.interf_graph:
            self.interf_graph[a] = set()
        if b not in self.interf_graph:
            self.interf_graph[b] = set()
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
            alive = (alive - set(instr.writes())) | set(instr.reads())
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
            #print "Node with highest saturation = %s (%s)" % (node, sat)
            registerset = set()
            for neighbor in self.interf_graph[node]:
                if neighbor in self.register_assgnmnt:
                    registerset.add(self.register_assgnmnt[neighbor])
            #registerset = map(lamdba x: self.register_assgnmnt(x), self.interf_graph[node]))
            #print "Register set for node = %s" % (registerset)
            lowest_unused = min(set(P0RegAllocator.ALL_REGS) - registerset, key=lambda x:x.name)
            #print "Lowest unused register = %s" % (lowest_unused)
            self.register_assgnmnt[node] = lowest_unused
            #self.print_register_alloc()
            vertices = vertices - set([node])

    def print_graph(self):
        print "\nGraph:"
        for k,v in self.interf_graph.iteritems():
            print "%-20s : %s" % (k,v)

    def print_register_alloc(self):
        print "\nRegister allocation:"
        for k,v in self.register_assgnmnt.iteritems():
            print "%-20s : %s" % (k,v)


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
        regallocator.liveness_analyze()
        regallocator.build_interference_graph()
        regallocator.print_graph()
        regallocator.color_graph()
        regallocator.print_register_alloc()
