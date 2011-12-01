#include <assert.h>
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
    big_pyobj *A, *B, *C;
    big_pyobj *A_parents, *B_parents, *C_parents;
    big_pyobj *list;
    int i;

    /**
     * test1: simple class with no superclasses
     * class A:
     */
    pymem_init();
    A_parents = create_list(inject_int(0));
    inc_ref_ctr(A_parents);

    A = create_class(inject_big(A_parents));
    inc_ref_ctr(A);
    assert (A_parents->ref_ctr == 2);

    dec_ref_ctr(A);
    assert (A_parents->ref_ctr == 1);

    dec_ref_ctr(A_parents);

    pymem_print_stats();
    pymem_shutdown();

    /**
     * test2: class with one superclass
     * class A:
     * class B(A):
     * B -> B_parents -> A -> A_parents
     */
    pymem_init();
    A_parents = create_list(inject_int(0));
    inc_ref_ctr(A_parents);

    A = create_class(inject_big(A_parents));
    inc_ref_ctr(A);
    assert (A_parents->ref_ctr == 2);

    B_parents = create_list(inject_int(1));
    inc_ref_ctr(B_parents);
    set_subscript(inject_big(B_parents), inject_int(0), inject_big(A));
    assert (A->ref_ctr == 2);

    B = create_class(inject_big(B_parents));
    inc_ref_ctr(B);
    assert (B_parents->ref_ctr == 2);

    dec_ref_ctr(A_parents);
    assert (A_parents->ref_ctr == 1);

    dec_ref_ctr(A);
    assert (A->ref_ctr == 1);

    dec_ref_ctr(B_parents);
    assert (B_parents->ref_ctr == 1);

    pymem_print_stats();
    dec_ref_ctr(B);  // everything should go away at this point.
    pymem_print_stats();
    pymem_shutdown();

    /**
     * test3: simple class with attribute.
     * list = []
     * class A:
     *     a = list
     */
    pymem_init();
    list = create_list(inject_int(0));
    inc_ref_ctr(list);

    A_parents = create_list(inject_int(0));
    inc_ref_ctr(A_parents);

    A = create_class(inject_big(A_parents));
    inc_ref_ctr(A);
    assert (A_parents->ref_ctr == 2);

    set_attr(inject_big(A), "a", inject_big(list));
    dec_ref_ctr(list);                   // the list should not go away here.
    assert (list->ref_ctr == 1);

    dec_ref_ctr(A_parents);
    assert (A_parents->ref_ctr == 1);

    pymem_print_stats();
    dec_ref_ctr(A);                      // now everything should be de-allocated.
    pymem_print_stats();
    pymem_shutdown();
}
