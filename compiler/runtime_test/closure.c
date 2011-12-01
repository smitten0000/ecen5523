#include <assert.h>
#include <string.h>
#include "pymem.h"
#include "runtime.h"


/**
 * This test case is meant to verify that the incref/decref functions
 * work correctly to release allocated memory. Relies on the pymem
 * infrastructure.
 */

int dummy_function (int x)
{
    return x;
}

int main (int argc, char *argv[])
{
    big_pyobj *f, *freevars;
    int i;


    /**
     * test1: simple closure with no free vars
     * f = lambda x: x
     * decref(list)
     */
    pymem_init();
    freevars = create_list(inject_int(0));
    inc_ref_ctr(freevars);

    f = create_closure(dummy_function, inject_big(freevars));
    inc_ref_ctr(f);
    assert (freevars->ref_ctr == 2);

    dec_ref_ctr(f);
    assert (freevars->ref_ctr == 1);

    dec_ref_ctr(freevars);

    pymem_print_stats();
    pymem_shutdown();
}
