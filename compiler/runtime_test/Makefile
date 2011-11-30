
TESTS=pymem_test list dict
RUNTIME_DIR=..
RUNTIME_SOURCE= \
	$(RUNTIME_DIR)/hashtable.c \
	$(RUNTIME_DIR)/hashtable_itr.c \
	$(RUNTIME_DIR)/hashtable_utility.c \
	$(RUNTIME_DIR)/pymem.c \
	$(RUNTIME_DIR)/runtime.c

CC=gcc
CFLAGS=-I$(RUNTIME_DIR) -g
LDFLAGS=-lm

all: $(TESTS)

pymem_test: pymem_test.c $(RUNTIME_SOURCE)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

list: list.c $(RUNTIME_SOURCE)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

dict: dict.c $(RUNTIME_SOURCE)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

clean:
	rm -f $(TESTS) *.pymem
