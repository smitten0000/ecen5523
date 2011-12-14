#include <assert.h>
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
    big_pyobj *dict, *dict2;
    int i;

    /**
     * test1: simple empty dictionary 
     */
    pymem_init();
    dict = create_dict();
    incref(dict);
    decref(dict);
    pymem_print_stats();
    pymem_shutdown();

    /**
     * test2: dictionary with one trivial entry (key/value pair)
     */
    pymem_init();
    dict = create_dict();
    incref(dict);
    set_subscript(inject_big(dict), inject_int(1), inject_int(2));
    decref(dict);
    pymem_print_stats();
    pymem_shutdown();

    /** 
     * test3: dictionary with one pyobj entry for the value
     */
    pymem_init();
    dict = create_dict(); incref(dict);
    dict2 = create_dict(); incref(dict2);

    set_subscript(inject_big(dict), inject_int(1), inject_big(dict2));

    // verify the ref count for dict2 is now 2
    assert (dict2->ref_ctr == 2);
    decref(dict);

    // at this point, dict should no longer exist, but dict2 should still exist
    assert (dict2->ref_ctr == 1);
    decref(dict2);

    pymem_print_stats();
    pymem_shutdown();

}

