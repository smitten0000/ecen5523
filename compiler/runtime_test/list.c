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
    big_pyobj *list, *list2;
    int i;


    /**
     * test1: simple list creation
     * list = []
     * decref(list)
     */
    pymem_init();
    list = create_list(inject_int(0));
    incref(list);
    decref(list);
    pymem_print_stats();
    pymem_shutdown();

    /**
     * test2: list with primitive (int) elements
     * list = [99,88,77,66,55]
     * decref(list)
     */
    pymem_init();
    list = create_list(inject_int(5));
    incref(list);
    set_subscript(inject_big(list), inject_int(0), inject_int(99));
    set_subscript(inject_big(list), inject_int(1), inject_int(88));
    set_subscript(inject_big(list), inject_int(2), inject_int(77));
    set_subscript(inject_big(list), inject_int(3), inject_int(66));
    set_subscript(inject_big(list), inject_int(4), inject_int(55));
    decref(list);
    pymem_print_stats();
    pymem_shutdown();

    /**
     * test3: list with another list (int) element
     * list = [99]
     * list2 = [list]  // increments list's ref count by one...
     * decref(list2)   // decrements list's ref count by one (in addition to list2)
     *                 // list2 should be deallocated completely.
     * decref(list)    // list should be deallocated completely.
     */
    pymem_init();

    list = create_list(inject_int(1));
    incref(list);
    set_subscript(inject_big(list), inject_int(0), inject_int(99));

    list2 = create_list(inject_int(1));
    incref(list2);
    set_subscript(inject_big(list2), inject_int(0), inject_big(list));
    assert (list->ref_ctr == 2);

    decref(list2);
    assert (list->ref_ctr == 1);

    decref(list);
    pymem_print_stats();
    pymem_shutdown();
}
