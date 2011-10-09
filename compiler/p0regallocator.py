# vim: set ts=4 sw=4 expandtab:

from comp_util import *
from x86ir import *
from SpillVisitor import SpillVisitor

UNSPILLABLE=1
SPILLABLE=20

class P0RegAllocator:
    ALL_REGS = [Register('eax'), Register('ebx'), Register('ecx'), Register('edx'), Register('edi'), Register('esi')]
    CALLER_SAVE = [Register('eax'), Register('ecx'), Register('edx')]
    ALL_SLOTS = set(range(0,500))
    def __init__(self, program, varalloc):
        self.program = program
        self.varalloc = varalloc
        self.liveness_after_k_dict={}
        self.interf_graph = {}
        self.register_assgnmnt = {}
        # all registers should start out with an assignment for their corresponding "index"
        for reg in P0RegAllocator.ALL_REGS:
            self.register_assgnmnt[reg] = P0RegAllocator.ALL_REGS.index(reg)

    def _add_vertex(self,a):
        self.interf_graph[a] = set()

    def _add_directed_edge(self, a, b):
        # add node to adjacency list if it doesn't exist
        if a not in self.interf_graph:
            self._add_vertex(a)
        # create the edge
        self.interf_graph[a].add(b)

    def _add_edge(self,a,b):
        # if a == b, then this is a loop and we don't allow loops in an
        # undirected graph, so simply return
        if a == b:
            return 
        # create the edges ; graph is undirected, so have to create edges 
        # for a -> b and b -> a since adjacency lists are directed by nature
        self._add_directed_edge(a,b)
        self._add_directed_edge(b,a)

    def liveness_analyze(self):
        instructions = self.program.instructions()
        num_instr = len(instructions)
        alive = set()
        k = num_instr
       
        for instr in reversed(instructions):
            k = k - 1
            self.liveness_after_k_dict[k] = alive
            if not isinstance(instr, Instruction):
                raise Exception("'%s' is not an Instruction" % instr)
            # get reads/writes performed by instruction, but only for variables
            writes = set(filter(lambda x: isinstance(x,Var), instr.writes()))
            reads = set(filter(lambda x: isinstance(x,Var), instr.reads()))
            # compute the live variables
            alive = (alive - writes) | reads
            # add all variables to the graph
            for x in writes: self._add_vertex(x)
            for x in reads: self._add_vertex(x)

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
                    if isinstance(instr, Addl) and isinstance(instr.dst, Var):
                        self._add_edge(instr.dst, live)
                    elif isinstance(instr, Negl) and isinstance(instr.operand, Var):   
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
        # get the list of vertices that need assignments
        # only include vertices of type 'Var' (ignore Registers)
        vertices = set(filter(lambda x: isinstance(x,Var), self.interf_graph.keys()))
        # compute the saturation for all the vertices up front
        # This gets a list of tuples of the form (sat(x),x)
        nodesat = map(lambda x:(x,self.saturation(x)), vertices)
        # create a priority queue (see comp_util module) and add all nodes
        # with their corresponding priority
        
        saturation_q = priorityq()
        for node, sat in nodesat:
            if node.spillable:
                # we negate the saturation to produce the same effect as a max-heap
                saturation_q.add_task(-sat, node, SPILLABLE)
            else:
                if debug:
                    print 'node %s is unspillable' % node
                saturation_q.add_task(-sat, node, UNSPILLABLE)
        while len(vertices) > 0:
            # find the entry in the list with the highest saturation
            # this corresponds to the "most-constrained" node; we tackle this first 
            sat, node = saturation_q.get_top_priority()
            #print "Node with highest saturation = %s (%s)" % (node, sat)
            registerset = set()
            for neighbor in self.interf_graph[node]:
                if neighbor in self.register_assgnmnt:
                    registerset.add(self.register_assgnmnt[neighbor])
            #print "Register set for node = %s" % (registerset)
            lowest_unused = min(P0RegAllocator.ALL_SLOTS-registerset)
            #print "Lowest unused register = %s" % (lowest_unused)
            self.register_assgnmnt[node] = lowest_unused
            #self.print_register_alloc()
            # finally, remove the node from the set of vertices that need colored
            vertices = vertices - set([node])
            # We have to re-compute the saturation for all the neighbors of the node, 
            # and update the priority queue.
            for neighbor in self.interf_graph[node]:
                # we should never need to know the saturation for a register, so don't
                # update registers' saturation value
                if isinstance(neighbor, Var):
                    # only update saturations for nodes that are still in our list
                    # of vertices, since the nodes that have already been colored have
                    # have been removed from the priority queue
                    if neighbor in vertices:
                        saturation_q.incr_priority(neighbor,inc=-1)

    def print_liveness(self):
        instructions = self.program.instructions()
        for k in range(0,len(instructions)):
            instr = instructions[k]
            print "%5s. %-40s : %s" % (k, instr, self.liveness_after_k_dict[k])
            k = k + 1

    def print_graph(self):
        print "\nGraph:"
        for k in sorted(self.interf_graph.iterkeys(),key=lambda x:x.name):
            print "%-20s : %s" % (k,self.interf_graph[k])

    def print_register_alloc(self):
        print "\nRegister allocation:"
        for k in sorted(self.register_assgnmnt.iterkeys(),key=lambda x:x.name):
            if isinstance(k,Var):
                print "%-20s : %s" % (k,self.get_assignment(k))

    def get_assignment(self,varname):
        if varname not in self.register_assgnmnt:
            raise Exception("Unable to find assignment for variable '%s'" % varname)
        assignment = self.register_assgnmnt[varname]
        if assignment > len(P0RegAllocator.ALL_REGS)-1:
            slot = (assignment - (len(P0RegAllocator.ALL_REGS)-1))
            return StackSlot(slot)
        else:
            return P0RegAllocator.ALL_REGS[assignment]

    def substitute(self):
        """ Substitutes the register assignments in for the corresponding variables"""
        is_safe = False
        retval = []
        while not is_safe:
            is_safe = True
            self.liveness_after_k_dict={}
            self.interf_graph = {}
            self.register_assgnmnt = {}
            # all registers should start out with an assignment for their corresponding "index"
            for reg in P0RegAllocator.ALL_REGS:
                self.register_assgnmnt[reg] = P0RegAllocator.ALL_REGS.index(reg)
            retval = self.internal_sub()
            spill = SpillVisitor()
            
            for statement in retval:
                for instruction in statement.instructions:
                    unsafe_op = spill.visit(instruction)
                    if unsafe_op != None:
                        is_safe = False
                        if debug:
                            print 'found unsafe op'
                        for prog_stmt in self.program.statements:
                            index = 0
                            for prog_instr in prog_stmt.instructions:
                                if prog_instr is unsafe_op.original:
                                    if debug:
                                        print prog_stmt
                                    
                                    varname = Var(self.varalloc.get_next_var(), spillable=False)
                                    tmpassign = Movl(unsafe_op.original.src, varname, unsafe_op)
                                    prog_stmt.instructions[index] = tmpassign
                                    
                                    tmpassign = Movl(varname,unsafe_op.original.dst, unsafe_op)
                                    prog_stmt.instructions.insert(index+1, tmpassign)
                                    if debug:
                                        print prog_stmt
                                    prog_instr.src = varname
                                    break
                                index = index + 1
        return retval
    def internal_sub(self):
        self.liveness_analyze()
        #self.print_liveness()
        self.build_interference_graph()
        #self.print_graph()
        self.color_graph()
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
        instructions = [self.visit(x) for x in node.instructions]
        # filter out any no-ops
        instructions = filter(lambda x: x is not None, instructions)
        return Statement(instructions,node.source)

    def visit_Movl(self, node, *args, **kwargs):
        src = node.src
        dst = node.dst
        if isinstance(src,Var):
            src = self.get_assignment(src)
        if isinstance(dst,Var):
            dst = self.get_assignment(dst)
        # if the source and destination are the same, then return None,
        # indicating a no-operation
        if src.__class__ == dst.__class__ and src == dst:
            return None
        return Movl(src,dst, node)
        
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
        return Addl(src,dst, node)

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
        regallocator = P0RegAllocator(program, varalloc)
        retval = regallocator.substitute()

        #print retval
        #import cProfile as profile
        #import pstats
        #output_file = 'profile.out'
        #profile.run('regallocator.substitute()', output_file)
        #p = pstats.Stats(output_file)
        #print "name: "
        #print p.sort_stats('name')
        #print "all stats: "
        #p.print_stats()
        #print "cumulative (top 10): "
        #p.sort_stats('cumulative').print_stats(10)
