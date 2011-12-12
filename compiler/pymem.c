#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <time.h>
#include <sys/time.h>
#include <libgen.h>
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

static FILE *output_fd = NULL;
static char *cmdline = NULL;

/* functions */
void pymem_init()
{
    FILE *fp;
    struct timeval tv;
    char logfile[4096];
    char c;
    int i;

    /* This reads in the program name from the /proc filesystem on linux. */
    if (cmdline == NULL) {
        cmdline = (char *)malloc(4096);
        fp = fopen("/proc/self/cmdline", "r");
        i = 0;
        while (fread(&c, 1, 1, fp) && (i < 4095))
            cmdline[i++] = c;
        cmdline[i]='\0';
    }

    /* if previously initialized, shut it down */
    if (head_ptr != NULL)
        pymem_shutdown();

    /* open the log file */
    snprintf (logfile, 4096, "%s.pymem", basename(cmdline));
    if ((output_fd = fopen(logfile, "a")) == NULL) {
        perror("fopen");
        exit(-1);
    }

    /* print a message to the log that pymem_shutdown was called */
    int ret = gettimeofday(&tv, NULL);
    assert (ret > -1);
    fprintf (output_fd, "\n---> %s: pymem_init: %s\n", format_tv(&tv), cmdline);

    /* initialize the type array */
    for (i=0; i < MAX_TYPES; i++)
        bytype[i]=0;
}

void pymem_shutdown()
{
    struct timeval tv;
    node_t *ptr;
    node_t *next;
    int i, leak;

    /* free our linked list of facts, and free any user memory that
     * failed to be free()'d and emit a warning */
    leak = 0;
    if (head_ptr != NULL) {
        ptr = head_ptr;
        i = 0;
        while (ptr != NULL) {
            i++;
            if (!ptr->freed) {
                fprintf (output_fd, "WARNING: memory leak detected for allocation %d at %p\n", i, ptr->loc);
                free(ptr->loc);
                leak = 1;
            }
            next = ptr->next;
            free(ptr);
            ptr = next;
        }
    }
    if (leak)
        printf("Leak detected. See .pymem for details.\n");

    head_ptr = NULL;
    cur_ptr = NULL;

    /* print a message to the log that pymem_shutdown was called */
    int ret = gettimeofday(&tv, NULL);
    assert (ret > -1);
    fprintf (output_fd, "<--- %s: pymem_shutdown: %s\n", format_tv(&tv), cmdline);


    /* now we can close the output file */
    if (output_fd != NULL) {
        fclose(output_fd);
        output_fd = NULL;
    }
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

    fprintf (output_fd, "\nAllocations by type\n");
    fprintf (output_fd, "===========================================\n");
    for (i=0; i < MAX_TYPES; i++)
        if (bytype[i] > 0)
            fprintf (output_fd, "Type %s: %d\n", types[i], bytype[i]);

    fprintf (output_fd, "\nHistory of allocations (since pymem_init())\n");
    fprintf (output_fd, "===========================================\n");
    i = 0;
    while (p != NULL) {
        fprintf (output_fd, "Allocation %d: type=%s, size_req=%d, freed=%d, loc=%p, ",
                ++i, types[p->type], p->size_req, p->freed, p->loc);

        /* we have to print the times separately, since each call to format_tv
           overwrites the values from the previous call */
        fprintf (output_fd, "alloc_tv=%s, ", format_tv(&p->alloc_tv));
        fprintf (output_fd, "free_tv=%s\n", format_tv(&p->free_tv));
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
