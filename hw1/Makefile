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
	rm -f $(OBJS) libruntime.a *.pyc parser.out parsetab.py tests/*.s
