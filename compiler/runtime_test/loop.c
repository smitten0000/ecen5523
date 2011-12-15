#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "pymem.h"
#include "runtime.h"


/**
 * This test case is meant to verify that the incref/decref functions
 * work correctly to release allocated memory. Relies on the pymem
 * infrastructure.
 */

void incref (big_pyobj *obj) { inc_ref_ctr(inject_big(obj)); }
void decref (big_pyobj *obj) { dec_ref_ctr(inject_big(obj)); }


void make_list ()
{
    big_pyobj *list = create_list(inject_int(100));
    incref(list);
    // comment out the decref and you'll see how much more memory is used.
    // use "top", and 'O' then 'q'<Enter> to sort by RSS (resident set size)
    decref(list);
}

int main (int argc, char *argv[])
{
    char c;
    int i;

    /**
     * test1: make a list in a tight loop.
     */
    pymem_init();
    for (i=0; i < 100000; i++)
        make_list();
    pymem_print_stats();
    pymem_shutdown();

    printf("Go ahead, check the memory consumption now.\n");
    printf("Press any key to exit.\n");
    scanf("%c", &c);
}
