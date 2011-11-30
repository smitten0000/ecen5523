#include <string.h>
#include "pymem.h"
#include "runtime.h"


/**
 * This test case is meant to verify that the incref/decref functions
 * work correctly to release allocated memory. Relies on the pymem
 * infrastructure.
 */

int main (int argc, char *argv[])
{
    big_pyobj *list;
    int i;

    pymem_init();

    list = create_list(inject_int(0));
    inc_ref_ctr(list);
    dec_ref_ctr(list);

    pymem_print_stats();
    pymem_shutdown();
}

