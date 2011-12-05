# Cool, our Makefile!
OBJS = \
	runtime.o \
	hashtable.o \
	hashtable_itr.o \
	hashtable_utility.o

all: libruntime.a

libruntime.a: $(OBJS)
	ar rcs $@ $(OBJS)

%.o: %.c
	gcc -c $<

clean:
	rm -f $(OBJS) libruntime.a *.pyc parser.out parsetab.py *.pymem
	for i in test alltests our_tests our_hw5_tests hw5_test our_hw6_tests ; do \
		rm -f $$i/*.c $$i/*.s $$i/*.expected $$i/*.out $$i/*.warn $$i/*.pymem ; \
		find $$i -type f -perm 0755 -exec rm -f {} \; ; \
	done
