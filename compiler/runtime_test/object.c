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


int main (int argc, char *argv[])
{
    big_pyobj *A, *B, *C;
    big_pyobj *A_parents, *B_parents, *C_parents;
    big_pyobj *a, *b, *c;
    int i;

    /**
     * test1: simple class with no superclasses + 1 object
     * dependencies: a -> A -> A_parents
     * class A:
     * a = A()
     */
    pymem_init();
    A_parents = create_list(inject_int(0));
    incref(A_parents);

    A = create_class(inject_big(A_parents));
    incref(A);
    assert (A_parents->ref_ctr == 2);

    a = create_object(inject_big(A));
    incref(a);
    assert (A->ref_ctr == 2);

    decref(A_parents);
    assert (A_parents->ref_ctr == 1);

    decref(A);
    assert (A->ref_ctr == 1);

    pymem_print_stats();
    decref(a);   // this should deallocate everything
    pymem_print_stats();
    pymem_shutdown();

    /**
     * test2: class with one superclass + 1 object for each class.
     * class A:
     * class B(A):
     * a = A()
     * b = B()
     *
     * dependency graph:
     * A -> A_parents
     * B_parents -> A
     * B -> B_parents
     * a -> A 
     * b -> B
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

    a = create_object(inject_big(A));
    incref(a);
    assert (A->ref_ctr == 3);

    b = create_object(inject_big(B));
    incref(b);
    assert (B->ref_ctr == 2);

    // now start releasing stuff.
    decref(A_parents);
    assert (A_parents->ref_ctr == 1);

    decref(A);
    assert (A->ref_ctr == 2);

    decref(a);             // a becomes deallocated at this point
                                // but A should hang around since B_parents
                                // should still own a reference to it.
    assert (A->ref_ctr == 1);

    decref(B_parents);
    assert (B_parents->ref_ctr == 1);

    decref(B);
    assert (B->ref_ctr == 1);

    pymem_print_stats();
    decref(b);  // everything should go away at this point.
    pymem_print_stats();
    pymem_shutdown();
}
