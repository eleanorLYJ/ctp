#define _POSIX_C_SOURCE 200809L
#define _BSD_SOURCE 600
#define _DEFAULT_SOURCE

#define _GNU_SOURCE
#include <sched.h>
#include <sys/types.h>
#include <sys/stat.h>
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
#include "../thread_safe_global.h"
#include "../atomics.h"
#include <stdarg.h>
#include <assert.h>
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

#define VERBOSE 1  // Set verbosity level
#define MY_CALLOC(v, n) (((v) = calloc((n), sizeof((v)[0]))) == NULL)

static void *reader(void *data);
static void *writer(void *core_id);
static void dtor(void *);

atomic_bool stop_flag = false;
FILE *writer_log, *reader_log;
thread_safe_var shared_ptr;
int num_cores;

struct thread_info {
    int core_id;
    unsigned long long count;
};

enum magic {
    MAGIC_FREED = 0xABADCAFEEFACDABAUL,
    MAGIC_INITED = 0xA600DA12DA1FFFFFUL,
    MAGIC_EXIT = 0xAABBCCDDFFEEDDCCUL,
};

void printf_verbose(const char *format, ...) {
    if (VERBOSE) {
        va_list args;
        va_start(args, format);
        vprintf(format, args);
        va_end(args);
    }
}

void set_affinity(int cpu) {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(cpu, &cpuset);

    pthread_t current_thread = pthread_self();
    int ret = pthread_setaffinity_np(current_thread, sizeof(cpu_set_t), &cpuset);
    if (ret != 0) {
        fprintf(stderr, "Error setting CPU affinity for thread %lu to CPU %d: %s\n", current_thread, cpu, strerror(ret));
        fflush(stderr);
    }
}

void check_affinity() {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    pthread_t current_thread = pthread_self();
    int ret = pthread_getaffinity_np(current_thread, sizeof(cpu_set_t), &cpuset);
    if (ret != 0) {
        fprintf(stderr, "Error getting CPU affinity for thread %lu: %s\n", current_thread, strerror(ret));
        fflush(stderr);
        return;
    }
    
    for (int i = 0; i < CPU_SETSIZE; i++) {
        if (CPU_ISSET(i, &cpuset)) {
            printf("Thread %lu is running on CPU %d\n", current_thread, i);
            fflush(stdout);
        }
    }
}


int main(int argc, char *argv[]) 
{
    num_cores = sysconf(_SC_NPROCESSORS_ONLN); 

    if (argc != 3) {
        fprintf(stderr, "Usage: %s <num_readers> <num_writers>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    size_t num_readers = atoi(argv[1]);
    size_t num_writers = atoi(argv[2]);

    pthread_t readers[num_readers], writers[num_writers];
    struct thread_info reader_info[num_readers], writer_info[num_writers];


    size_t i;
    uint64_t *magic_exit;
    // Open log files before creating threads
    writer_log = fopen("writer_log.txt", "w");
    if (writer_log == NULL) {
        perror("Failed to open writer log file");
        exit(EXIT_FAILURE);
    }

    reader_log = fopen("reader_log.txt", "w");
    if (reader_log == NULL) {
        perror("Failed to open reader log file");
        fclose(writer_log);
        exit(EXIT_FAILURE);
    }
    memset(readers, 0, sizeof(readers));
    memset(writers, 0, sizeof(writers));


    printf("Will use %ju reader threads and %ju writer threads\n",
           (uintmax_t)num_readers, (uintmax_t)num_writers);

    if ((errno = thread_safe_var_init(&shared_ptr, dtor)) != 0)
        err(1, "thread_safe_var_init() failed");

    if ((magic_exit = malloc(sizeof(*magic_exit))) == NULL)
        err(1, "malloc failed");
    *magic_exit = MAGIC_EXIT;

    for (i = 0; i < num_readers; i++) {
        reader_info[i].core_id = i;
        reader_info[i].count = 0;
        if ((errno = pthread_create(&readers[i], NULL, reader, &reader_info[i])) != 0)
            err(1, "Failed to create reader thread no. %ju", (uintmax_t)i);
    }

    for (i = 0; i < num_writers; i++) {
        writer_info[i].core_id = i + num_readers;
        writer_info[i].count = 0;
        if ((errno = pthread_create(&writers[i], NULL, writer, &writer_info[i])) != 0)
            err(1, "Failed to create writer thread no. %ju", (uintmax_t)i);
    }
    
    // Let the threads run for a while
    sleep(1);
    atomic_store(&stop_flag, true);

    // Join reader threads
    for (i = 0; i < num_readers; i++) {
        pthread_join(readers[i], NULL);
    }

    // Join writer threads
    for (i = 0; i < num_writers; i++) {
        pthread_join(writers[i], NULL);
    }

    // Close log files
    fclose(writer_log);
    fclose(reader_log);

    // Print counts
    for (i = 0; i < num_readers; i++) 
        printf("Reader %ld read %llu times\n", i, reader_info[i].count);
    for (i = 0; i < num_writers; i++) 
        printf("Writer %ld wrote %llu times\n", i, writer_info[i].count);

    return 0;
}

static void *
reader(void *arg)
{
    struct thread_info *info = (struct thread_info *)arg;
    int core_id = info->core_id;

    if (core_id >= 0 && core_id < num_cores) {
        set_affinity(core_id);
    } else {
        fprintf(stderr, "Invalid core ID: %d\n", core_id);
        fflush(stderr);
    }
    check_affinity();

    unsigned long long nr_reads = 0;
    uint64_t version;
    uint64_t last_version = 0;
    int first = 1;
    void *p;

    if ((errno = thread_safe_var_wait((shared_ptr))) != 0)
        err(1, "thread_safe_var_wait() failed");

    while (!atomic_load(&stop_flag)) {
        if ((errno = thread_safe_var_get((shared_ptr), &p, &version)) != 0)
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
        fprintf(reader_log, "Reader: value=%lu, version=%lu\n", *(uint64_t *)p, version);
        fflush(reader_log);
        if (first) {
            fflush(stdout);
            first = 0;
        }
    }
    info->count = nr_reads;
    printf_verbose("thread_end %s, tid %lu\n", "reader", pthread_self());
    return NULL;
}


static void *
writer(void *arg)
{
    struct thread_info *info = (struct thread_info *)arg;
    int core_id = info->core_id;
    // Validate core_id
    if (core_id >= 0 && core_id < num_cores) {
        set_affinity(core_id);
    } else {
        fprintf(stderr, "Invalid core ID: %d\n", core_id);
        fflush(stderr);
    }
    check_affinity();
    unsigned long long nr_writes = 0;
    uint64_t version;
    uint64_t last_version = 0;
    uint64_t *new;
    while (!atomic_load(&stop_flag)) {
        new = malloc(sizeof(uint64_t));
        assert(new);
        *new = MAGIC_INITED;
        if ((errno = thread_safe_var_set((shared_ptr), new, &version)) != 0)
            err(1, "thread_safe_var_set() failed");
        if (version < last_version)
            err(1, "version went backwards for this writer! "
                "new version is %jd, previous is %jd",
                version, last_version);
        fprintf(writer_log, "Writer: value=%lu, version=%lu\n", *new, version);
        fflush(writer_log);
        last_version = version;
        nr_writes++;
    }

    printf_verbose("thread_end %s, tid %lu\n", "writer", pthread_self());
    info->count = nr_writes;
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
