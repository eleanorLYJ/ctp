#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <urcu-qsbr.h>
#include <urcu/rculist.h>
#include <stdatomic.h>
#include <assert.h>
#include <time.h>
#include <unistd.h>
#include <stdarg.h>
#include <string.h>
#include <err.h>


// Define global variables and macros
static struct rcu_data {
    int value;
    long long version;
} *shared_ptr = NULL;

#define NR_READERS 10
#define NR_WRITERS 2
#define VERBOSE 1  // Set verbosity level

atomic_bool stop_flag = false;
FILE *writer_log, *reader_log;

void printf_verbose(const char *format, ...) 
{
    if (VERBOSE) {
        va_list args;
        va_start(args, format);
        vprintf(format, args);
        va_end(args);
    }
}

void *thr_writer(void *_count) 
{
    unsigned long long *count = _count;
    unsigned long long nr_writes = 0;
    struct rcu_data *new, *old;
    static atomic_llong global_version = 0; // Global version counter to avoid conflicts between writers

    while (!atomic_load(&stop_flag)) {
        new = malloc(sizeof(struct rcu_data));
        assert(new);
        new->value = rand();  // Assign a random value
        new->version = atomic_fetch_add(&global_version, 1);
        old = rcu_xchg_pointer(&shared_ptr, new);

        fprintf(writer_log, "Writer: value=%d, version=%lld\n", new->value, new->version);
        fflush(writer_log);

        synchronize_rcu();
        free(old);
        old = NULL;
        nr_writes++;
    }
    printf_verbose("thread_end %s, tid %lu\n", "writer", pthread_self());
    *count = nr_writes;
    return ((void*)2);
}

void *thr_reader(void *_count) 
{
    unsigned long long *count = _count;
    unsigned long long nr_reads = 0;
    struct rcu_data *local_ptr;
    
    rcu_register_thread();
    rcu_thread_offline();
    rcu_thread_online();
    
    while (!atomic_load(&stop_flag)) {
        rcu_read_lock();
        local_ptr = rcu_dereference(shared_ptr);
        if (local_ptr) {
            fprintf(reader_log, "Reader: value=%d, version=%lld\n", local_ptr->value, local_ptr->version);
            fflush(reader_log);
        }
        rcu_read_unlock();
        nr_reads++;
        /* Every 1024 readings, enter a quiescent state */
        if (caa_unlikely((nr_reads & ((1 << 10) - 1)) == 0))
            rcu_quiescent_state();
    }

    rcu_unregister_thread();

    *count = nr_reads;
    printf_verbose("thread_end %s, tid %lu\n", "reader", pthread_self());
    return ((void*)1);
}

int main() 
{
    pthread_t readers[NR_READERS], writers[NR_WRITERS];
    unsigned long long count_readers[NR_READERS], count_writers[NR_WRITERS];
    int i;
    memset(readers, 0, sizeof(readers));
    memset(writers, 0, sizeof(writers));

    // Initialize random number generator
    srand(time(NULL));

    // Allocate memory for shared_ptr and initialize
    shared_ptr = malloc(sizeof(struct rcu_data));
    assert(shared_ptr);
    shared_ptr->version = -1;
    shared_ptr->value = 0;

    // Open log files
    writer_log = fopen("writer_log.txt", "w");
    reader_log = fopen("reader_log.txt", "w");

    // Create reader threads
    for (i = 0; i < NR_READERS; i++) {
        if (pthread_create(&readers[i], NULL, thr_reader, &count_readers[i])) {
            err(1, "Failed to create reader thread no. %ju", (uintmax_t)i);
        }
    }

    // Create writer threads
    for (i = 0; i < NR_WRITERS; i++) {
        if (pthread_create(&writers[i], NULL, thr_writer, &count_writers[i])) {
            err(1, "Failed to create writer thread no. %ju", (uintmax_t)i);


        }
    }

    // Let the threads run for a while (e.g., 10 seconds)
    sleep(10);
    
    // Signal the threads to stop
    atomic_store(&stop_flag, true);

    // Join reader threads
    for (i = 0; i < NR_READERS; i++) {
        pthread_join(readers[i], NULL);
    }

    // Join writer threads
    for (i = 0; i < NR_WRITERS; i++) {
        pthread_join(writers[i], NULL);
    }

    // Close log files
    fclose(writer_log);
    fclose(reader_log);

    // Print counts
    for (i = 0; i < NR_READERS; i++) {
        printf("Reader %d read %llu times\n", i, count_readers[i]);
    }
    for (i = 0; i < NR_WRITERS; i++) {
        printf("Writer %d wrote %llu times\n", i, count_writers[i]);
    }

    // Free the initial shared_ptr
    free(shared_ptr);
    shared_ptr = NULL;

    return 0;
}
