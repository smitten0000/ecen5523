#include <stdlib.h>

#ifndef __PYMEM_H_
#define __PYMEM_H_

#define MAX_TYPES 256

void  pymem_init();
void  pymem_shutdown();
void *pymem_new(int type, size_t size);
void  pymem_free(void *loc);
void  pymem_print_stats();

#endif
