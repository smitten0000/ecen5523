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
    incref(A_parents);

    A = create_class(inject_big(A_parents));
    incref(A);
    assert (A_parents->ref_ctr == 2);

    decref(A);
    assert (A_parents->ref_ctr == 1);

    decref(A_parents);

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
    incref(A_parents);

    A = create_class(inject_big(A_parents));
    incref(A);
    assert (A_parents->ref_ctr == 2);

    B_parents = create_list(inject_int(1));
    incref(B_parents);
    set_subscript(inject_big(B_parents), inject_int(0), inject_big(A));
    assert (A->ref_ctr == 2);

    B = create_class(inject_big(B_parents));
    incref(B);
    assert (B_parents->ref_ctr == 2);

    decref(A_parents);
    assert (A_parents->ref_ctr == 1);

    decref(A);
    assert (A->ref_ctr == 1);

    decref(B_parents);
    assert (B_parents->ref_ctr == 1);

    pymem_print_stats();
    decref(B);  // everything should go away at this point.
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
    incref(list);

    A_parents = create_list(inject_int(0));
    incref(A_parents);

    A = create_class(inject_big(A_parents));
    incref(A);
    assert (A_parents->ref_ctr == 2);

    set_attr(inject_big(A), "a", inject_big(list));
    decref(list);                   // the list should not go away here.
    assert (list->ref_ctr == 1);

    decref(A_parents);
    assert (A_parents->ref_ctr == 1);

    pymem_print_stats();
    decref(A);                      // now everything should be de-allocated.
    pymem_print_stats();
    pymem_shutdown();
}
