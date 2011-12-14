#include <assert.h>
#include <string.h>
#include "pymem.h"
#include "runtime.h"


/**
 * This test case is meant to verify that the incref/decref functions
 * work correctly to release allocated memory. Relies on the pymem
 * infrastructure.
 */

void incref (big_pyobj *obj) { inc_ref_ctr(inject_big(obj)); }
void decref (big_pyobj *obj) { dec_ref_ctr(inject_big(obj)); }

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
    incref(freevars);

    f = create_closure(dummy_function, inject_big(freevars));
    incref(f);
    assert (freevars->ref_ctr == 2);

    decref(f);
    assert (freevars->ref_ctr == 1);

    decref(freevars);

    pymem_print_stats();
    pymem_shutdown();
}
