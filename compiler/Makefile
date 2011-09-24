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
	rm -f $(OBJS) libruntime.a *.pyc parser.out parsetab.py test/*.s test/*.c test/*.warn test/*.expected test/*.out
	find test -type f -perm 0755 -exec rm -f {} \;
