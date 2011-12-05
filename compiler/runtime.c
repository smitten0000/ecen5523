#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <ctype.h>
#include <string.h>

#include "runtime.h"

int min(int x, int y) {
    return y < x ? y : x;
}

/* Some forward declarations */
static int equal_pyobj(pyobj a, pyobj b);
static void print_float(double in);
static void print_list(pyobj pyobj_list);
static void print_dict(pyobj dict);
static list list_add(list x, list y);

int tag(pyobj val) {
    return val & MASK;
}

int is_int(pyobj val) {
    return (val & MASK) == INT_TAG;
}

int is_bool(pyobj val) {
    return (val & MASK) == BOOL_TAG;
}

int is_float(pyobj val) {
    return (val & MASK) == FLOAT_TAG;
}

int is_big(pyobj val) {
    return (val & MASK) == BIG_TAG;
}

int is_function(pyobj val) {
    int ret;
    if (is_big(val)) {
        ret = project_big(val)->tag == FUN;
        return ret;
    } else
        return 0;
}
int is_object(pyobj val) {
    return is_big(val) && (project_big(val)->tag == OBJECT);
}
int is_class(pyobj val) {
    return is_big(val) && (project_big(val)->tag == CLASS);
}
int is_unbound_method(pyobj val) {
    return is_big(val) && (project_big(val)->tag == UBMETHOD);
}
int is_bound_method(pyobj val) {
    return is_big(val) && (project_big(val)->tag == BMETHOD);
}

/*
  Injecting into pyobj.
*/
pyobj inject_int(int i) {
    return (i << SHIFT) | INT_TAG;
}
pyobj inject_bool(int b) {
    return (b << SHIFT) | BOOL_TAG;
}
pyobj inject_float(int f) {
    /* Could accomplish this with a special mask */
    return ((f >> SHIFT) << SHIFT) | FLOAT_TAG;
}
pyobj inject_big(big_pyobj* p) {
    assert((((long)p) & MASK) == 0);
    return ((long)p) | BIG_TAG;
}
/*
  Projecting from pyobj.
*/
int project_int(pyobj val) {
    assert((val & MASK) == INT_TAG);
    return val >> SHIFT;
}
int project_bool(pyobj val) {
    assert((val & MASK) == BOOL_TAG);
    return val >> SHIFT;
}
float project_float(pyobj val) {
    assert((val & MASK) == FLOAT_TAG);
    return (val >> SHIFT) << SHIFT;
}
big_pyobj* project_big(pyobj val) {
    assert((val & MASK) == BIG_TAG);
    return (big_pyobj*)(val & ~MASK);
}

function project_function(pyobj val) {
    big_pyobj* p = project_big(val);
    assert(p->tag == FUN);
    return p->u.f;
}
class project_class(pyobj val) {
    big_pyobj* p = project_big(val);
    assert(p->tag == CLASS);
    return p->u.cl;
}
object project_object(pyobj val) {
    big_pyobj* p = project_big(val);
    assert(p->tag == OBJECT);
    return p->u.obj;
}
bound_method project_bound_method(pyobj val) {
    big_pyobj* p = project_big(val);
    assert(p->tag == BMETHOD);
    return p->u.bm;
}
unbound_method project_unbound_method(pyobj val) {
    big_pyobj* p = project_big(val);
    assert(p->tag == UBMETHOD);
    return p->u.ubm;
}


/* Not used? */
static int is_zero(pyobj val) {
    return (val >> SHIFT) == 0;
}

static void print_int(int x) {
    printf("%d", x);
}
void print_int_nl(int x) {
    printf("%d\n", x);
}
static void print_bool(int b) {
    if (b)
        printf ("True");
    else
        printf ("False");
}

static void print_pyobj(pyobj x) {
    switch (tag(x)) {
    case INT_TAG:
        print_int(project_int(x));
        break;
    case BOOL_TAG:
        print_bool(project_bool(x));
        break;
    case FLOAT_TAG:
        print_float(project_float(x));
        break;
    case BIG_TAG: {
        big_pyobj* b = project_big(x);
        switch (b->tag) {
        case DICT:
            print_dict(x);
            break;
        case LIST:
            print_list(x);
            break;
        default:
            assert(0);
        }
        break;
    }
    default:
        assert(0);
    }
}

int input() {
    int i;
    scanf("%d", &i);
    return i;
}

pyobj input_int() {
    int i;
    scanf("%d", &i);
    return inject_int(i);
}

/*
  Lists (needed for hashtables)
*/

static big_pyobj* list_to_big(list l) {
    big_pyobj* v = (big_pyobj*)pymem_new(LIST, sizeof(big_pyobj));
    v->tag = LIST;
    v->u.l = l;
    v->ref_ctr = 0;
    return v;
}

big_pyobj* create_list(pyobj length) {
    list l;
    l.len = project_int(length); /* this should be checked */
    l.data = (pyobj*)pymem_new(LIST, sizeof(pyobj) * l.len);
    return list_to_big(l);
}

static pyobj make_list(pyobj length) {
    return inject_big(create_list(length));
}


static char is_in_list(list ls, pyobj b)
{
    int i;
    for(i = 0; i < ls.len; i++)
        if (ls.data[i] == b)
            return 1;
    return 0;
}

static int list_equal(list x, list y)
{
    char eq = 1;
    int i;
    for (i = 0; i != min(x.len, y.len); ++i)
        eq = eq && equal_pyobj(x.data[i], y.data[i]);
    if (x.len == y.len)
        return eq;
    else
        return 0;
}


/*
  Hashtable support
*/

static char inside;
static list printing_list;

static void print_dict(pyobj dict)
{
    big_pyobj* d;
    char inside_reset = 0;
    if(!inside) {
        inside = 1;
        inside_reset = 1;
        printing_list.len = 0;
        printing_list.data = 0;
    }
    d = project_big(dict);

    if(is_in_list(printing_list, dict)) {
        printf("{...}");
        return;
    }
    printf("{");
    int i = 0;
    int max = hashtable_count(d->u.d);

    struct hashtable_itr *itr = hashtable_iterator(d->u.d);
    if (max) {
        do {
            pyobj k = *(pyobj *)hashtable_iterator_key(itr);
            pyobj v = *(pyobj *)hashtable_iterator_value(itr);
            print_pyobj(k);
            printf(": ");
            if (is_in_list(printing_list, v)
                    || equal_pyobj(v,dict)) {
                printf("{...}");
            }
            else {
                /* tally this dictionary in our list of printing dicts */
                list a;
                a.len = 1;
                a.data = (pyobj*)pymem_new(LIST, sizeof(pyobj) * a.len);
                a.data[0] = dict;
                /* Yuk, concatenating (adding) lists is slow! */
                printing_list = list_add(printing_list, a);
                print_pyobj(v);
            }
            if(i != max - 1)
                printf(", ");
            i++;
        } while (hashtable_iterator_advance(itr));
    }
    printf("}");

    if(inside_reset) {
        inside = 0;
        printing_list.len = 0;
        printing_list.data = 0;
    }
}


/* This hash function was chosen more or less at random -Jeremy */
static int hash32shift(int key)
{
    key = ~key + (key << 15); /* key = (key << 15) - key - 1; */
    key = key ^ (key >> 12);
    key = key + (key << 2);
    key = key ^ (key >> 4);
    key = key * 2057; /* key = (key + (key << 3)) + (key << 11); */
    key = key ^ (key >> 16);
    return key;
}


static unsigned int hash_any(void* o)
{
    pyobj obj = *(pyobj*)o;
    switch (tag(obj)) {
    case INT_TAG:
        return hash32shift(project_int(obj));
    case FLOAT_TAG:
        return hash32shift(project_float(obj));
    case BOOL_TAG:
        return hash32shift(project_bool(obj));
    case BIG_TAG: {
        big_pyobj* b = project_big(obj);
        switch (b->tag) {
        case LIST: {
            int i;
            unsigned long h = 0;
            for (i = 0; i != b->u.l.len; ++i)
                h = 5*h + hash_any(&b->u.l.data[i]);
            return h;
        }
        case DICT: {
            struct hashtable_itr* i;
            unsigned long h = 0;
            if (hashtable_count(b->u.d) == 0)
                return h;
            i = hashtable_iterator(b->u.d);
            do {
                h = 5*h + hash_any(hashtable_iterator_value(i));
            } while (hashtable_iterator_advance(i));
            return h;
        }
        default:
            printf("unrecognized tag in hash_any\n");
            *(int*)0 = 42;
        }
        break;
    }
    default:
        printf("unrecognized tag in hash_any\n");
        *(int*)0 = 42;
    }
}


static struct hashtable *current_cmp_a;
static struct hashtable *current_cmp_b;

static char dict_equal(struct hashtable* x, struct hashtable* y)
{
    if(hashtable_count(x) != hashtable_count(y))
        return 0;

    if(current_cmp_a)
    {
        if(current_cmp_a == x)
        {
            return current_cmp_a == y;
        }
        else if(current_cmp_a == y)
        {
            return current_cmp_a == x;
        }
    }


    if(current_cmp_b)
    {
        if(current_cmp_b == y)
        {
            return current_cmp_b == x;
        }
        else if(current_cmp_b == x)
        {
            return current_cmp_b == y;
        }
    }

    char will_reset = 0;
    char same = 1;
    if(!current_cmp_a)
    {
        current_cmp_a = x;
        current_cmp_b = y;
        will_reset = 1;
    }

    int max = hashtable_count(x);

    struct hashtable_itr *itr_a = hashtable_iterator(x);
    struct hashtable_itr *itr_b = hashtable_iterator(y);
    if (max)
    {
        do {
            pyobj k_a = *(pyobj *)hashtable_iterator_key(itr_a);
            pyobj v_a = *(pyobj *)hashtable_iterator_value(itr_a);
            pyobj k_b = *(pyobj *)hashtable_iterator_key(itr_b);
            pyobj v_b = *(pyobj *)hashtable_iterator_value(itr_b);

            if(!equal_pyobj(k_a,k_b) || !equal_pyobj(v_a,v_b))
                same = 0;

        } while (hashtable_iterator_advance(itr_a) && hashtable_iterator_advance(itr_b));
    }

    if(will_reset)
    {
        current_cmp_a = NULL;
        current_cmp_b = NULL;
    }

    return same;
}

static int equal_pyobj(pyobj a, pyobj b)
{
    switch (tag(a)) {
    case INT_TAG: {
        switch (tag(b)) {
        case INT_TAG:
            return project_int(a) == project_int(b);
        case BOOL_TAG:
            return project_int(a) == project_bool(b);
        case FLOAT_TAG:
            return project_int(a) == project_bool(b);
        default:
            return 0;
        }
        break;
    }
    case FLOAT_TAG: {
        switch (tag(b)) {
        case INT_TAG:
            return project_float(a) == project_int(b);
        case BOOL_TAG:
            return project_float(a) == project_bool(b);
        case FLOAT_TAG:
            return project_float(a) == project_bool(b);
        default:
            return 0;
        }
        break;
    }
    case BOOL_TAG: {
        switch (tag(b)) {
        case INT_TAG:
            return project_bool(a) == project_int(b);
        case BOOL_TAG:
            return project_bool(a) == project_bool(b);
        case FLOAT_TAG:
            return project_bool(a) == project_bool(b);
        default:
            return 0;
        }
        break;
    }
    case BIG_TAG: {
        if (tag(b) != BIG_TAG)
            return 0;
        big_pyobj* x = project_big(a);
        big_pyobj* y = project_big(b);
        if (x->tag != y->tag)
            return 0;
        switch (x->tag) {
        case LIST:
            return list_equal(x->u.l, y->u.l);
        case DICT:
            return dict_equal(x->u.d, y->u.d);
        case CLASS:
            return x == y;
        default:
            return 0;
        }
        break;
    }
    }
    return 0;
}


static int equal_any(void* a, void* b)
{
    return equal_pyobj(*(pyobj*)a, *(pyobj*)b);
}

big_pyobj* create_dict()
{
    big_pyobj* v = (big_pyobj*)pymem_new(DICT, sizeof(big_pyobj));
    v->tag = DICT;
    v->u.d = create_hashtable(4, hash_any, equal_any, DICT);
    v->ref_ctr = 0;
    return v;
}

static pyobj make_dict() {
    return inject_big(create_dict());
}

static pyobj* dict_subscript(dict d, pyobj key)
{
    void* p = hashtable_search(d, &key);
    if (p)
        return (pyobj*)p;
    else {
        pyobj* k = (pyobj*) pymem_new(DICT, sizeof(pyobj));
        *k = key;
        pyobj* v = (pyobj*) pymem_new(DICT, sizeof(pyobj));
        *v = inject_int(444);
        hashtable_insert(d, k, v, DICT);
        return v;
    }
}

static pyobj* list_subscript(list ls, pyobj n)
{
    switch (tag(n)) {
    case INT_TAG: {
        int i = project_int(n);
        if (0 <= i && i < ls.len)
            return &(ls.data[i]);
        else if (0 <= ls.len + i && ls.len + i < ls.len)
            return &(ls.data[ls.len + i]);
        else {
            printf("ERROR: list_nth index larger than list");
            exit(1);
        }
    }
    case BOOL_TAG: {
        int b = project_bool(n);
        if (b < ls.len)
            return &(ls.data[b]);
        else {
            printf("ERROR: list_nth index larger than list");
            exit(1);
        }
    }
    default:
        printf("ERROR: list_nth expected integer index");
        exit(1);
    }
}


static char printed_0;
static char printed_0_neg;
static void print_float(double in)
{
    char outstr[128];

    snprintf(outstr, 128, "%.12g", in);

    char *p = outstr;

    if(in == 0.0)
    {
        if(printed_0 == 0)
        {
            printed_0 = 1;
            printed_0_neg = *p == '-'; /*see if we incremented for negative*/
        }
        else
        {
            printf(printed_0_neg ? "-0.0" : "0.0");
            return;
        }
    }

    if(*p == '-')
        p++;


    while(*p && isdigit(*p))
        p++;

    printf( ( (*p)  ? "%s" : "%s.0" ), outstr);
}

static pyobj *current_list;
static void print_list(pyobj ls)
{
    big_pyobj* pyobj_list = project_big(ls);
    if(current_list && current_list == pyobj_list->u.l.data) {
        printf("[...]");
        return;
    }

    int will_reset = 0;
    if(!current_list) {
        current_list = pyobj_list->u.l.data;
        will_reset = 1;
    }

    list l = pyobj_list->u.l;
    printf("[");
    int i;
    for(i = 0; i < l.len; i++) {
        if (tag(l.data[i]) == BIG_TAG && project_big((l.data[i]))->tag == LIST
                && project_big((l.data[i]))->u.l.data == l.data)
            printf("[...]");
        else
            print_pyobj(l.data[i]);
        if(i != l.len - 1)
            printf(", ");
    }
    printf("]");

    if(will_reset)
        current_list = NULL;
}

static list list_add(list a, list b)
{
    list c;
    c.len = a.len + b.len;
    c.data = (pyobj*)pymem_new(LIST, sizeof(pyobj) * c.len);
    int i;
    for (i = 0; i != a.len; ++i)
        c.data[i] = a.data[i];
    for (i = 0; i != b.len; ++i)
        c.data[a.len + i] = b.data[i];
    return c;
}

big_pyobj* add(big_pyobj* a, big_pyobj* b) {
    switch (a->tag) {
    case LIST:
        switch (b->tag) {
        case LIST:
            return list_to_big(list_add(a->u.l, b->u.l));
        default:
            printf("error in add, expected a list\n");
            exit(-1);
        }
    default:
        printf("error in add, expected a list\n");
        exit(-1);
    }
}

int equal(big_pyobj* a, big_pyobj* b) {
    switch (a->tag) {
    case LIST:
        switch (b->tag) {
        case LIST:
            return list_equal(a->u.l, b->u.l);
        default:
            return 0;
        }
    case DICT:
        switch (b->tag) {
        case DICT:
            return dict_equal(a->u.d, b->u.d);
        default:
            return 0;
        }
    case CLASS:
        switch (b->tag) {
        case CLASS:
            return a == b;
        default:
            return 0;
        }
    default:
        return 0;
    }
}

int not_equal(big_pyobj* x, big_pyobj* y) {
    return !equal(x, y);
}

static pyobj subscript_assign(big_pyobj* c, pyobj key, pyobj val)
{
    switch (c->tag) {
    case LIST:
        // XXX: inc ref count (for val only)
        inc_ref_ctr(val);
        return *list_subscript(c->u.l, key) = val;
    case DICT:
        // XXX: inc ref count (for key and val)
        inc_ref_ctr(key);
        inc_ref_ctr(val);
        return *dict_subscript(c->u.d, key) = val;
    default:
        printf("error in set subscript, not a list or dictionary\n");
        assert(0);
    }
}

pyobj set_subscript(pyobj c, pyobj key, pyobj val)
{
    switch (tag(c)) {
    case BIG_TAG: {
        big_pyobj* b = project_big(c);
        return subscript_assign(b, key, val);
    }
    default:
        printf("error in set subscript, not a list or dictionary\n");
        assert(0);
    }
    assert(0);
}

static pyobj subscript(big_pyobj* c, pyobj key)
{
    switch (c->tag) {
    case LIST:
        return *list_subscript(c->u.l, key);
    case DICT:
        return *dict_subscript(c->u.d, key);
    default:
        printf("error in set subscript, not a list or dictionary\n");
        assert(0);
    }
}

pyobj get_subscript(pyobj c, pyobj key)
{
    switch (tag(c)) {
    case BIG_TAG: {
        big_pyobj* b = project_big(c);
        return subscript(b, key);
    }
    default:
        printf("error in get_subscript, not a list or dictionary\n");
        assert(0);
    }
}

void print_any(pyobj p) {
    print_pyobj(p);
    printf("\n");
}

int is_true(pyobj v)
{
    switch (tag(v)) {
    case INT_TAG:
        return project_int(v) != 0;
    case FLOAT_TAG:
        return project_float(v) != 0;
    case BOOL_TAG:
        return project_bool(v) != 0;
    case BIG_TAG: {
        big_pyobj* b = project_big(v);
        switch (b->tag) {
        case LIST:
            return b->u.l.len != 0;
        case DICT:
            return hashtable_count(b->u.d) > 0;
        case FUN:
            return 1;
        case CLASS:
            return 1;
        case OBJECT:
            return 1;
        default:
            printf("error, unhandled case in is_true\n");
            assert(0);
        }
    }
    }
    assert(0);
}

/* Support for Functions */

static big_pyobj* closure_to_big(function f) {
    big_pyobj* v = (big_pyobj*)pymem_new(FUN, sizeof(big_pyobj));
    v->tag = FUN;
    v->u.f = f;
    v->ref_ctr = 0;
    return v;
}

big_pyobj* create_closure(void* fun_ptr, pyobj free_vars) {
    function f;
    f.function_ptr = fun_ptr;
    f.free_vars = free_vars;
    // XXX: increment ref counter to free_vars list
    // Shouldn't we assert that free_vars is of type LIST?
    assert(is_big(free_vars));
    inc_ref_ctr(free_vars);
    return closure_to_big(f);
}



void* get_fun_ptr(pyobj p) {
    big_pyobj* b = project_big(p);
    assert(b->tag == FUN);
    return b->u.f.function_ptr;
}

pyobj get_free_vars(pyobj p) {
    big_pyobj* b = project_big(p);
    assert(b->tag == FUN);
    return b->u.f.free_vars;
}

big_pyobj* set_free_vars(big_pyobj* b, pyobj free_vars) {
    assert(b->tag == FUN);
    b->u.f.free_vars = free_vars;
    return b;
}

/* Support for Objects and Classes */

static unsigned int attrname_hash(void *ptr)
{
    unsigned char *str = (unsigned char *)ptr;
    unsigned long hash = 5381;
    int c;
    while(c=*str++)
        hash = ((hash << 5) + hash) ^ c;
    return hash;
}

static int attrname_equal(void *a, void *b)
{
    return !strcmp( (char*)a, (char*)b );
}

// XXX: design change.
// The original design used the code below to copy the parent classes
// from the list pyobj passed in by the user, to the newly allocated
// class pyobj.  The problem with this approach is that when we go
// to deallocate this class pyobj, we no longer have a reference to
// the original list pyobj, or the class pyobj(s) corresponding to the
// base classes, therefore we cannot decrement the reference counts on
// them.  We changed the design by changing the struct class_struct
// definition in runtime.h to contain a single pyobj reference to the
// list we are passed in (instead of struct class_struct *parents).  This
// allows us to call decref on the list when this class is de-allocated,
// and at the same time, simplifies our reference counting logic, since
// we only have to manage the reference count for the list pyobj (we
// don't have to manage the reference counts for each base class itself,
// since the list owns these references).  The downside of this change
// is that it requires some small changes to get_attr, and inherits_rec,
// and attrsearch_rec...
// We need to just test this well and make sure it doesn't break anything.
// I think this design is more consistent with the rest of the runtime
// design, so I believe its an improvement.
/*
big_pyobj* create_class(pyobj bases)
{
    big_pyobj* ret = (big_pyobj*)pymem_new(CLASS, sizeof(big_pyobj));
    ret->tag = CLASS;
    ret->u.cl.attrs = create_hashtable(2, attrname_hash, attrname_equal, CLASS);
    ret->ref_ctr = 0;

    big_pyobj* basesp = project_big(bases);
    switch (basesp->tag) {
    case LIST: {
        int i;
        ret->u.cl.nparents = basesp->u.l.len;
        ret->u.cl.parents = (class*)pymem_new(CLASS, sizeof(class) * ret->u.cl.nparents);
        for (i = 0; i != ret->u.cl.nparents; ++i) {
            pyobj* parent = &basesp->u.l.data[i];
            if (tag(*parent) == BIG_TAG && project_big(*parent)->tag == CLASS) {
                ret->u.cl.parents[i] = project_big(*parent)->u.cl;
                //XXX: when we figure out how to track references properly for
                // a class_struct type
                //inc_ref_ptr(project_big(*parent));
            }
            else
                exit(-1);
        }
        break;
    }
    default:
        exit(-1);
    }
    return ret;
}
*/
big_pyobj* create_class(pyobj bases)
{
    big_pyobj* ret;
    big_pyobj* basesp = project_big(bases);
    pyobj parent;

    // Do validation first to check that we were passed in a list of classes
    // and not anything else.
    switch (basesp->tag) {
    case LIST: {
        int i;
        for (i = 0; i != basesp->u.l.len; ++i) {
            parent = basesp->u.l.data[i];
            if (tag(parent) != BIG_TAG || project_big(parent)->tag != CLASS) {
                fprintf(stderr, "create_class: list must contain only classes");
                exit(-1);
            }
        }
        break;
    }
    default:
        fprintf(stderr, "create_class: must pass list");
        exit(-1);
    }

    // Create the class pyobj to return
    ret = (big_pyobj*)pymem_new(CLASS, sizeof(big_pyobj));
    ret->tag = CLASS;
    ret->ref_ctr = 0;
    ret->u.cl.attrs = create_hashtable(2, attrname_hash, attrname_equal, CLASS);
    ret->u.cl.parents = bases;
    // remember to increment the reference count on the list pyobj of base classes!
    inc_ref_ctr(bases);
    return ret;
}

/* we leave calling the __init__ function for a separate step. */
big_pyobj* create_object(pyobj cl) {
    big_pyobj* ret = (big_pyobj*)pymem_new(OBJECT, sizeof(big_pyobj));
    ret->tag = OBJECT;
    ret->ref_ctr = 0;
    big_pyobj* clp = project_big(cl);
    if (clp->tag == CLASS) {
        ret->u.obj.clazz = cl;
        inc_ref_ctr(cl);
    } else {
        printf("in make object, expected a class\n");
        exit(-1);
    }
    ret->u.obj.attrs = create_hashtable(2, attrname_hash, attrname_equal, OBJECT);
    return ret;
}

static pyobj* attrsearch_rec(class cl, char* attr) {
    big_pyobj* parents;
    big_pyobj* parent;
    pyobj* ptr;
    int i;
    ptr = hashtable_search(cl.attrs, attr);

    if(ptr == NULL) {
        parents = project_big(cl.parents);
        for(i=0; i != parents->u.l.len; ++i) {
            parent = project_big(parents->u.l.data[i]);
            ptr = attrsearch_rec(parent->u.cl, attr);
            if (ptr != NULL)
                return ptr;
        }
        return NULL;
    } else
        return ptr;
}

static pyobj* attrsearch(class cl, char* attr) {
    pyobj* ret = attrsearch_rec(cl, attr);
    if (ret == NULL) {
        printf("attribute %s not found\n", attr);
        exit(-1);
    }
    return ret;
}

static big_pyobj* create_bound_method(pyobj receiver, pyobj f) {
    big_pyobj* ret = (big_pyobj*)pymem_new(BMETHOD, sizeof(big_pyobj));
    ret->tag = BMETHOD;
    ret->ref_ctr = 0;
    ret->u.bm.fun = f;
    inc_ref_ctr(f);
    ret->u.bm.receiver = receiver;
    inc_ref_ctr(receiver);
    return ret;
}

static big_pyobj* create_unbound_method(pyobj clazz, pyobj fun) {
    big_pyobj* ret = (big_pyobj*)pymem_new(UBMETHOD, sizeof(big_pyobj));
    ret->tag = UBMETHOD;
    ret->ref_ctr = 0;
    ret->u.ubm.fun = fun;
    inc_ref_ctr(fun);
    ret->u.ubm.clazz = clazz;
    inc_ref_ctr(clazz);
    return ret;
}

int has_attr(pyobj o, char* attr)
{
    if (tag(o) == BIG_TAG) {
        big_pyobj* b = project_big(o);
        switch (b->tag) {
        case CLASS: {
            pyobj* attribute = attrsearch_rec(b->u.cl, attr);
            return attribute != NULL;
        }
        case OBJECT: {
            pyobj* attribute = hashtable_search(b->u.obj.attrs, attr);
            if (attribute == NULL) {
                attribute = attrsearch_rec(b->u.cl, attr);
                return attribute != NULL;
            } else {
                return 1;
            }
        }
        default:
            return 0;
        }
    } else
        return 0;
}

static int inherits_rec(class c1, class c2) {
    big_pyobj *parents;
    big_pyobj *parent;
    int ret = 0;
    if (c1.attrs == c2.attrs) {
        ret = 1;
    } else {
        int i;
        parents = project_big(c1.parents);
        for(i=0; i != parents->u.l.len; ++i) {
            parent = project_big(parents->u.l.data[i]);
            ret = inherits_rec(parent->u.cl, c2);
            if (ret)
                break;
        }
    }
    return ret;
}

int inherits(pyobj c1, pyobj c2) {
    return inherits_rec(project_class(c1), project_class(c2));
}

big_pyobj* get_class(pyobj o)
{
    // XXX: caller is expected to incref on the return value
    big_pyobj* b = project_big(o);
    switch (b->tag) {
    case OBJECT:
        return project_big(b->u.obj.clazz);
        break;
    case UBMETHOD:
        return project_big(b->u.ubm.clazz);
        break;
    default:
        printf("get_class expected object or unbound method\n");
        exit(-1);
    }
}

big_pyobj* get_receiver(pyobj o)
{
    // XXX: caller is expected to incref the return value.
    big_pyobj* b = project_big(o);
    switch (b->tag) {
    case BMETHOD:
        return project_big(b->u.bm.receiver);
        break;
    default:
        printf("get_receiver expected bound method\n");
        exit(-1);
    }
}

big_pyobj* get_function(pyobj o)
{
    // XXX: caller is expected to incref the return value.
    big_pyobj* b = project_big(o);
    switch (b->tag) {
    case BMETHOD:
        return project_big(b->u.bm.fun);
        break;
    case UBMETHOD:
        return project_big(b->u.ubm.fun);
        break;
    default:
        printf("get_function expected a method\n");
        exit(-1);
    }
}

pyobj get_attr(pyobj c, char* attr)
{
    big_pyobj* b = project_big(c);
    switch (b->tag) {
    case CLASS: {
        pyobj* attribute = attrsearch(b->u.cl, attr);
        if (is_function(*attribute)) {
            return inject_big(create_unbound_method(c, *attribute));
        } else {
            return *attribute;
        }
    }
    case OBJECT: {
        pyobj* attribute = hashtable_search(b->u.obj.attrs, attr);
        big_pyobj* clazz = project_big(b->u.obj.clazz);
        if (attribute == NULL) {
            attribute = attrsearch(clazz->u.cl, attr);
            if (is_function(*attribute)) {
                return inject_big(create_bound_method(c, *attribute));
            } else {
                return *attribute;
            }
        } else {
            return *attribute;
        }
    }
    default:
        printf("error in get attribute, not a class or object\n");
        exit(-1);
    }
}

pyobj set_attr(pyobj obj, char* attr, pyobj val)
{
    char* k;
    pyobj* v;
    big_pyobj* b = project_big(obj);
    k = (char *)pymem_new(b->tag, strlen(attr)+1);
    v = (pyobj *)pymem_new(b->tag, sizeof(pyobj));
    strcpy(k, attr);
    // XXX: increment reference count here for the referenced object
    if (is_big(val))
        inc_ref_ctr(val);
    *v = val;

    struct hashtable* attrs;

    switch (b->tag) {
    case CLASS:
        attrs = b->u.cl.attrs;
        break;
    case OBJECT:
        attrs = b->u.obj.attrs;
        break;
    default:
        printf("error, expected object or class in set attribute\n");
        exit(-1);
    }

    if(!hashtable_change(attrs, k, v))
        if(!hashtable_insert(attrs, k, v, b->tag)) {
            printf("out of memory");
            exit(-1);
        }
    return val;
}

pyobj error_pyobj(char* string) {
    printf("%s\n", string);
    exit(-1);
}

void iterate_and_release_table(struct hashtable* h, int dec_keys) {
    struct hashtable_itr *itr;

    // if there are no entries in the hash table, then there is
    // nothing to do.
    if (hashtable_count(h) == 0)
        return;

    itr = hashtable_iterator(h);
    do {
        pyobj k = *(pyobj *)hashtable_iterator_key(itr);
        pyobj v = *(pyobj *)hashtable_iterator_value(itr);

        if ( dec_keys ) {
            dec_ref_ctr(k);
        }

        dec_ref_ctr(v);
    } while (hashtable_iterator_advance(itr));
    // none of the above functions which use iterators clean this up...
    free(itr);
}

/**
 * Free a class by first decrementing references on its parent classes (if any)
 * and then decrementing references to all keys and values in its attribute hashtable
 * then free the memory allocated for the class
 */
void free_class(big_pyobj* o) {
    /* o->u.cl.attrs is a hashtable which should be freed
       o.cl.parents is a list of parent classes
       -> should calling free here call dec_ref on the parent class reference? 
          B.S. just the _list_ of parent classes (after design change).
       -> that means create_class needs to call inc_ref on the parent class? 
          B.S. yes, but just the list; the list owns the references to the parent
               classes themselves.  By incrementing the reference count for the list,
               we guarantee that the reference counts for the elements in the list
               will never reach zero, since the list will always own a reference to
               its elements.
     */
    unsigned int i=0;
    // decrement reference count for list of parent classes
    dec_ref_ctr(o->u.cl.parents);
    // decrement reference counts for all values in the attribute hash table  
    // (but not keys since the keys are just strings that are not managed
    //  by the runtime)
    iterate_and_release_table(o->u.cl.attrs, 0);

    // release the hash table memory
    // If you look at set_attr, it always allocates new memory for both the 
    // keys and values, so we need to make sure to free it by passing a
    // non-zero (true) value for the free_values argument
    // (hashtable_destroy will always free the keys)
    hashtable_destroy(o->u.cl.attrs, 1);
    // finally release the memory for the class
    pymem_free(o);
}

/**
 * create_object sets a reference to the class
 * creates a hasttable for u.obj.attrs
 * and allocates the sizeof(big_pyobj)
 * so we simply undo each step
 */
void free_object(big_pyobj* o) {
    // decrement the class reference
    dec_ref_ctr(o->u.obj.clazz);

    // iterate the attr hashtable and release values (but not keys, since
    // they are not pyobj)
    iterate_and_release_table(o->u.obj.attrs, 0);

    // release the hash table memory, including keys and values
    hashtable_destroy(o->u.obj.attrs, 1);
    // release the object
    pymem_free(o);
}

/**
 * clean up a function
 * free_vars is set as a list so we need to walk the list and dec_ref on all elements, and then
 * dec_ref on the list reference itself
 */
 
void free_function(big_pyobj* o) {
    dec_ref_ctr(o->u.f.free_vars);
    // The only other portion of a function is the pointer itself
    pymem_free(o);
}
 
void free_bound_method(big_pyobj* o) {
    // decrement references to function (closure) and object (receiver).
    dec_ref_ctr(o->u.bm.fun);
    dec_ref_ctr(o->u.bm.receiver);
    
    pymem_free(o);
}

void free_unbound_method(big_pyobj* o) {
    // decrement references to function (closure) and class.
    dec_ref_ctr(o->u.ubm.fun);
    dec_ref_ctr(o->u.ubm.clazz);
    
    pymem_free(o);
}

void free_list(big_pyobj* o) {

    unsigned int i=0;
    
    for(i=0; i < o->u.l.len; i++) {
        dec_ref_ctr(o->u.l.data[i]);
    }
    pymem_free(o->u.l.data);
    pymem_free(o);
}

void free_dict(big_pyobj* o) {

    // iterate the hashtable and release both keys AND values
    // (in contrast to the attribute hashtable on classes/objects,
    //  this is because a pyobj dict can keys of type pyobj, whereas
    //  the attribute dictionary on classes/objects can only have 
    //  C strings as the key)
    iterate_and_release_table(o->u.d, 1);
    hashtable_destroy(o->u.d, 1);
    pymem_free(o);
}

void release(big_pyobj* o) {
    switch(o->tag) {
    case CLASS:
        free_class(o);
        break;
    case OBJECT:
        free_object(o);
        break;
    case BMETHOD:
        free_bound_method(o);
        break;
    case UBMETHOD:
        free_unbound_method(o);
        break;
    case LIST:
        free_list(o);
        break;
    case DICT:
        free_dict(o);
        break;
    case FUN:
        free_function(o);
        break;
    default:
        printf("Unhandled release for tag %d\n", o->tag);
    }
}

void inc_ref_ctr(pyobj v) {
    if (is_big(v)) {
        big_pyobj *val = project_big(v);
        val->ref_ctr ++;
    }
}

void dec_ref_ctr(pyobj v) {
    if (is_big(v)) {
        big_pyobj *val = project_big(v);
        val->ref_ctr --;
        if ( val->ref_ctr < 0 ) {
            fprintf(stderr,"too many dec_ref on big_pyobj\n");
            print_any(v);
            val->ref_ctr = 0;
        }
        if ( val->ref_ctr == 0 ) {
            release(val);
        }
    }
}
