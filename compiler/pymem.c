#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <time.h>
#include <sys/time.h>
#include "pymem.h"


/* linked list */
struct node {
    int             type;
    size_t          size_req;
    int             freed;
    void           *loc;
    struct timeval  alloc_tv;
    struct timeval  free_tv;
    struct node    *next;
};
typedef struct node node_t;

/* wrapper type for every allocation */
typedef struct {
    node_t         *node;
    void           *user_mem;
} alloc_t;

static node_t *head_ptr = NULL;
static node_t *cur_ptr = NULL;

static int bytype[MAX_TYPES];

static char *types[8] = { "LIST", "DICT", "FUN", "CLASS", "OBJECT", "UBMETHOD", "BMETHOD", };

/* forward declarations for static functions */
static char *format_tv (const struct timeval *tv);

/* functions */
void pymem_init()
{
    int i;

    if (head_ptr != NULL)
        pymem_shutdown();

    for (i=0; i < MAX_TYPES; i++)
        bytype[i]=0;
}

void pymem_shutdown()
{
    node_t *ptr;
    node_t *next;
    int i;

    /* free our linked list of facts, and free any user memory that 
     * failed to be free()'d and emit a warning */
    if (head_ptr != NULL) {
        ptr = head_ptr;
        i = 0;
        while (ptr != NULL) {
            i++;
            if (!ptr->freed) {
                printf ("WARNING: memory leak detected for allocation %d at %p\n", i, ptr->loc);
                free(ptr->loc);
            }
            next = ptr->next;
            free(ptr);
            ptr = next;
        }
    }

    head_ptr = NULL;
    cur_ptr = NULL;
}


void *pymem_new(int type, size_t size)
{
    struct timeval tv;
    alloc_t *alloc;

    assert (type < MAX_TYPES);
    bytype[type]++;

    /* allocate memory for user request, plus a little more to maintain
     * a pointer to linked list node */
    alloc = malloc(sizeof(alloc_t) + size);

    /* on first call, initialize our head_ptr and cur_ptr */
    if (head_ptr == NULL) {
        head_ptr = malloc(sizeof(node_t));
        cur_ptr = head_ptr;
    } else {
        assert (cur_ptr != NULL);
        /* allocate a new node_t and advance the cur_ptr */
        cur_ptr->next = malloc(sizeof(node_t));
        cur_ptr = cur_ptr->next;
    }

    /* get allocation time */
    int ret = gettimeofday(&tv, NULL);
    assert (ret > -1);

    /* set facts on the cur_ptr */
    cur_ptr->type = type;
    cur_ptr->size_req = size;
    cur_ptr->freed = 0;
    cur_ptr->loc = alloc;
    cur_ptr->alloc_tv.tv_sec = tv.tv_sec;
    cur_ptr->alloc_tv.tv_usec = tv.tv_usec;
    cur_ptr->free_tv.tv_sec = 0;
    cur_ptr->free_tv.tv_usec = 0;
    cur_ptr->next = NULL;

    /* maintain a link back to our facts */
    alloc->node = cur_ptr;

    /* return a pointer to the user memory */
    return &alloc->user_mem;
}

void pymem_free(void *loc)
{
    struct timeval tv;
    alloc_t *alloc;

    /* get the pointer back to our alloc_t structure */
    alloc = (alloc_t *)(loc - sizeof(node_t *));

    /* get free time */
    int ret = gettimeofday(&tv, NULL);
    assert (ret > -1);

    /* set additional facts on the linked list node */
    node_t *node = alloc->node;
    node->freed = 1;
    node->free_tv.tv_sec = tv.tv_sec;
    node->free_tv.tv_usec = tv.tv_usec;

    /* finally, free the memory */
    free (alloc);
}

void pymem_print_stats()
{
    node_t *p = head_ptr;
    int i;
    
    printf ("\nAllocations by type\n");
    printf ("===========================================\n");
    for (i=0; i < MAX_TYPES; i++)
        if (bytype[i] > 0)
            printf ("Type %s: %d\n", types[i], bytype[i]);
    
    printf ("\nHistory of allocations (since pymem_init())\n");
    printf ("===========================================\n");
    i = 0;
    while (p != NULL) {
        printf ("Allocation %d: type=%s, size_req=%d, freed=%d, loc=%p, "
                "alloc_tv=%s, free_tv=%s\n", 
                ++i, types[p->type], p->size_req, p->freed, p->loc, 
                format_tv(&p->alloc_tv), format_tv(&p->free_tv));
        p = p->next;
    }
}

/* helper function to format struct timeval */
static char *format_tv (const struct timeval *tv)
{
    static char buf[4096];
    static char timestr[4096];
    const struct tm *tm;

    tm = localtime(&tv->tv_sec);
    strftime(buf, 4096, "%Y-%m-%d %H:%M:%S", tm);
    snprintf(timestr, 4096, "%s.%03ld", buf, tv->tv_usec);
    
    return timestr;
}
