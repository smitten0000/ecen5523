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
    inc_ref_ctr(A_parents);

    A = create_class(inject_big(A_parents));
    inc_ref_ctr(A);
    assert (A_parents->ref_ctr == 2);

    a = create_object(inject_big(A));
    inc_ref_ctr(a);
    assert (A->ref_ctr == 2);

    dec_ref_ctr(A_parents);
    assert (A_parents->ref_ctr == 1);

    dec_ref_ctr(A);
    assert (A->ref_ctr == 1);

    pymem_print_stats();
    dec_ref_ctr(a);   // this should deallocate everything
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

    a = create_object(inject_big(A));
    inc_ref_ctr(a);
    assert (A->ref_ctr == 3);

    b = create_object(inject_big(B));
    inc_ref_ctr(b);
    assert (B->ref_ctr == 2);

    // now start releasing stuff.
    dec_ref_ctr(A_parents);
    assert (A_parents->ref_ctr == 1);

    dec_ref_ctr(A);
    assert (A->ref_ctr == 2);

    dec_ref_ctr(a);             // a becomes deallocated at this point
                                // but A should hang around since B_parents
                                // should still own a reference to it.
    assert (A->ref_ctr == 1);

    dec_ref_ctr(B_parents);
    assert (B_parents->ref_ctr == 1);

    dec_ref_ctr(B);
    assert (B->ref_ctr == 1);

    pymem_print_stats();
    dec_ref_ctr(b);  // everything should go away at this point.
    pymem_print_stats();
    pymem_shutdown();
}
