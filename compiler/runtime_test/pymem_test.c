#include "pymem.h"

int main (int argc, char *argv[])
{
    int i;

    pymem_init();
    void *ptr1 = pymem_new(1, 8);
    void *ptr2 = pymem_new(2, 16);
    void *ptr3 = pymem_new(3, 24);
    void *ptr4 = pymem_new(4, 32);
    void *ptr5 = pymem_new(5, 40);
    pymem_free(ptr1);
    pymem_free(ptr3);
    pymem_free(ptr5);
    pymem_print_stats();
    pymem_shutdown();

    pymem_init();
    ptr1 = pymem_new(1, 4);
    ptr2 = pymem_new(2, 4);
    for (i=0; i < 100000; i++) ;
    ptr3 = pymem_new(1, 4);
    ptr4 = pymem_new(3, 4);
    ptr5 = pymem_new(1, 4);
    pymem_print_stats();
    pymem_shutdown();
}

