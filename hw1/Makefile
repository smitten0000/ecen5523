OBJS = \
	runtime/runtime.o \
	runtime/hashtable.o \
	runtime/hashtable_itr.o \
	runtime/hashtable_utility.o

TESTCASES = \
    book-ex \
    ex1.1_tc1 \
    ex1.1_tc2 \
    ex1.1_tc3 \
    ex1.1_tc4 \
    ex1.1_tc5 \
    ex1.1_tc6 \
    ex1.1_tc7 \
    ex1.1_tc8 \
    ex1.1_tc9 \
    ex1.1_tc10 \
    ex1.1_tc11 \
    ex1.1_tc12 \
    ex1.1_tc13

all: libruntime.a $(TESTCASES)

libruntime.a: $(OBJS)
	ar rcs $@ $(OBJS)

%.o: %.c
	gcc -c $< -o $@

%.S: %.p0
	python p0compiler.py $<

%: %.S
	#gcc -static -o $@ $< -L. -lruntime -lm
	gcc -o $@ $< $(OBJS) -lm

clean:
	rm -f $(TESTCASES) $(OBJS) libruntime.a
