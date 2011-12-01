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
    big_pyobj *A_parents;
    big_pyobj *A;
    big_pyobj *freevars;
    big_pyobj *f;
    big_pyobj *ubmethod;
    int i;

    /**
     * test1: retrieve unbound method from simple class
     * class A:
     *    f = lambda x: x
     * dependencies:
     * f -> freevars
     * A -> A_parents
     * A -> f  (via A.f)
     * ubmethod -> f
     * ubmethod -> A
     */
    pymem_init();

    freevars = create_list(inject_int(0));
    inc_ref_ctr(freevars);

    f = create_closure(dummy_function, inject_big(freevars));
    inc_ref_ctr(f);

    A_parents = create_list(inject_int(0));
    inc_ref_ctr(A_parents);

    A = create_class(inject_big(A_parents));
    inc_ref_ctr(A);
    assert (A_parents->ref_ctr == 2);

    set_attr(inject_big(A), "f", inject_big(f));
    assert (f->ref_ctr == 2);

    ubmethod = project_big(get_attr(inject_big(A), "f"));
    inc_ref_ctr(ubmethod);
    assert (A->ref_ctr == 2);
    assert (f->ref_ctr == 3);

    dec_ref_ctr(freevars);
    assert (freevars->ref_ctr == 1);
    
    dec_ref_ctr(f);
    assert (f->ref_ctr == 2);

    dec_ref_ctr(A_parents);
    assert(A_parents->ref_ctr == 1);

    dec_ref_ctr(A);
    assert(A->ref_ctr == 1);

    // at this point only the unbound method is keeping stuff alive.
    pymem_print_stats();
    dec_ref_ctr(ubmethod);
    pymem_print_stats();
    pymem_shutdown();
}
