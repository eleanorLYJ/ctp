
#define _POSIX_C_SOURCE 200809L
#define _BSD_SOURCE 600
#define _DEFAULT_SOURCE

#include <sys/types.h>
#include <sys/stat.h>
#include <assert.h>
#include <err.h>
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <pthread.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "thread_safe_global.h"
#include "atomics.h"

#include <stdbool.h>
#include <stdatomic.h>



#if !defined(USE_TSV_SLOT_PAIR_DESIGN) && !defined(USE_TSV_SUBSCRIPTION_SLOTS_DESIGN)
#define USE_TSV_SLOT_PAIR_DESIGN
#endif
#ifdef USE_TSV_SLOT_PAIR_DESIGN
#define TSV_TYPE "slotpair"
#endif
#ifdef USE_TSV_SUBSCRIPTION_SLOTS_DESIGN
#define TSV_TYPE "slotlist"
#endif

static void *reader(void *data);
// static void *idle_reader(void *);
static void *writer(void *data);
static void dtor(void *);

atomic_bool stop_flag = false;
__thread unsigned long long nr_reads = 0;
__thread unsigned long long nr_writes = 0;

static pthread_t *readers;
static pthread_t *writers;
static size_t nreaders;
static size_t nwriters;
#define MY_NTHREADS (nreaders + nwriters)

static pthread_mutex_t exit_cv_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t exit_cv = PTHREAD_COND_INITIALIZER;
// static uint32_t nthreads;
// static uint32_t *random_bytes;
// static uint32_t *idleruns;
// static uint64_t **runs;

enum magic {
    MAGIC_FREED = 0xABADCAFEEFACDABAUL,
    MAGIC_INITED = 0xA600DA12DA1FFFFFUL,
    MAGIC_EXIT = 0xAABBCCDDFFEEDDCCUL,
};

thread_safe_var var;

int
main()
{
    size_t i;

    uint64_t *magic_exit;

    nreaders = 10;
    nwriters = 2;
    unsigned long long count_readers[nreaders], count_writers[nwriters];

    // memset(count_readers, 0, sizeof(count_readers));
    // memset(count_writers, 0, sizeof(count_writers));


    printf("Will use %ju reader threads and %ju writer threads\n",
           (uintmax_t)nreaders, (uintmax_t)nwriters);

#define MY_CALLOC1(v, n) (((v) = calloc((n), sizeof((v)[0]))) == NULL)

    if (MY_CALLOC1(readers, nreaders) ||
        MY_CALLOC1(writers, nwriters))
        err(1, "calloc failed");

    if ((magic_exit = malloc(sizeof(*magic_exit))) == NULL)
        err(1, "malloc failed");
    *magic_exit = MAGIC_EXIT;
    

    if ((errno = thread_safe_var_init(&var, dtor)) != 0)
        err(1, "thread_safe_var_init() failed");


    if ((errno = pthread_mutex_lock(&exit_cv_lock)) != 0)
        err(1, "Failed to acquire exit lock");

    for (i = 0; i < nreaders; i++) {
        if ((errno = pthread_create(&readers[i], NULL, reader, &count_readers[i])) != 0)
            err(1, "Failed to create reader thread no. %ju", (uintmax_t)i);
        if ((errno = pthread_detach(readers[i])) != 0)
            err(1, "Failed to detach reader thread no. %ju", (uintmax_t)i);
    }

    for (i = 0; i < nwriters; i++) {
        if ((errno = pthread_create(&writers[i], NULL, writer, &count_writers[i])) != 0)
            err(1, "Failed to create writer thread no. %ju", (uintmax_t)i);
        if ((errno = pthread_detach(writers[i])) != 0)
            err(1, "Failed to detach writer thread no. %ju", (uintmax_t)i);
    }
    
    // Let the threads run for a while
    sleep(10);
    atomic_store(&stop_flag, true);


    // Print counts
    for (i = 0; i < nreaders; i++) {
        printf("Reader %zu read %llu times\n", i, count_readers[i]);
    }
    for (i = 0; i < nwriters; i++) {
        printf("Writer %zu wrote %llu times\n", i, count_writers[i]);
    }


// free something??
    free(readers);
    free(writers);
    free(magic_exit);
    return 0;
}

// last_version ?????
static void *
reader(void *_count)
{
    unsigned long long *count = _count;
    uint64_t version;
    uint64_t last_version = 0;
    int first = 1;
    void *p;

    printf("Enter reader function\n");
    if ((errno = thread_safe_var_wait(var)) != 0)
        err(1, "thread_safe_var_wait() failed");

    while (!atomic_load(&stop_flag)) {
        if ((errno = thread_safe_var_get(var, &p, &version)) != 0)
            err(1, "thread_safe_var_get() failed");

        if (version < last_version)
            err(1, "version went backwards for this reader! "
                "new version is %jd, previous is %jd",
                version, last_version);
        last_version = version;

        if (*(uint64_t *)p == MAGIC_EXIT)
            break;
        if (*(uint64_t *)p == MAGIC_FREED)
            err(1, "data is no longer live here!");
        if (*(uint64_t *)p != MAGIC_INITED)
            err(1, "data not valid here!");

        nr_reads++;

        if (first) {
            fflush(stdout);
            first = 0;
        }
    }
    printf("reader %llu!!\n", nr_reads);

    if ((errno = pthread_mutex_lock(&exit_cv_lock)) != 0)
        err(1, "Failed to acquire exit lock");
    if ((errno = pthread_cond_signal(&exit_cv)) != 0)
        err(1, "Failed to signal exit cv");
    if ((errno = pthread_mutex_unlock(&exit_cv_lock)) != 0)
        err(1, "Failed to release exit lock");

    *count = nr_reads;
    return NULL;
}

static void *
writer(void *_count)
{
    unsigned long long *count = _count;
    uint64_t version;
    uint64_t last_version = 0;
    uint64_t *p;


    while (!atomic_load(&stop_flag)) {
        if ((p = malloc(sizeof(*p))) == NULL)
            err(1, "malloc() failed");
        *p = MAGIC_INITED;
        if ((errno = thread_safe_var_set(var, p, &version)) != 0)
            err(1, "thread_safe_var_set() failed");
        if (version < last_version)
            err(1, "version went backwards for this writer! "
                "new version is %jd, previous is %jd",
                version, last_version);
        last_version = version;
        nr_writes++;
    }

    if ((errno = pthread_mutex_lock(&exit_cv_lock)) != 0)
        err(1, "Failed to acquire exit lock");
    if ((errno = pthread_cond_signal(&exit_cv)) != 0)
        err(1, "Failed to signal exit cv");
    if ((errno = pthread_mutex_unlock(&exit_cv_lock)) != 0)
        err(1, "Failed to release exit lock");
    
    *count = nr_writes;
    return NULL;
}

static void
dtor(void *data)
{
    if (data == (void *)0x08UL)
        return;
    *(uint64_t *)data = MAGIC_FREED;
    free(data);
}
