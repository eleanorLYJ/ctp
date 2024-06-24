#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <err.h>
#include <errno.h>
#include <stdatomic.h>
#include <assert.h>
#include <time.h>
#include <unistd.h>
#include <stdarg.h>
#include <stdbool.h>
#include <string.h>

#include <urcu.h>
#define RCU_SIGNAL

// Define global variables and macros
static int *shared_var;

#define NR_READERS 10
#define NR_WRITERS 2
#define VERBOSE 1  // Set verbosity level

atomic_bool stop_flag = false;

void printf_verbose(const char *format, ...) {
    if (VERBOSE) {
        va_list args;
        va_start(args, format);
        vprintf(format, args);
        va_end(args);
    }
}

void *thr_writer(void *_count) {
    unsigned long long *count = _count;
    unsigned long long nr_writes = 0;
    int *new, *old;
    while (!atomic_load(&stop_flag)) {
        new = malloc(sizeof(int));
        assert(new);
        *new = 8;
        old = rcu_xchg_pointer(&shared_var, new);

        synchronize_rcu();  // Wait for all readers to finish
        if (old)
            *old = 0;
        free(old);
        nr_writes++;
    }
    *count = nr_writes;
    printf_verbose("thread_end %s, tid %lu\n", "writer", pthread_self());
    return ((void*)2);
}

void *thr_reader(void *_count) {
    unsigned long long *count = _count;
    unsigned long long nr_reads = 0;
    int *local_ptr;
    
    rcu_register_thread();  // Register the thread with RCU
    
    while (!atomic_load(&stop_flag)) {
        rcu_read_lock();  // Start an RCU read-side critical section
        local_ptr = rcu_dereference(shared_var);
        if (local_ptr)
            assert(*local_ptr == 8);
        rcu_read_unlock();  // End the RCU read-side critical section
        nr_reads++;
    }

    rcu_unregister_thread();  // Unregister the thread from RCU

    *count = nr_reads;
    printf_verbose("thread_end %s, tid %lu\n", "reader", pthread_self());
    return ((void*)1);
}

int main() {
    pthread_t readers[NR_READERS], writers[NR_WRITERS];
    unsigned long long count_readers[NR_READERS], count_writers[NR_WRITERS];
    int i;
    memset(readers, 0, sizeof(readers));
    memset(writers, 0, sizeof(writers));
    printf("Will use %ju reader threads and %ju writer threads\n",
           (uintmax_t)NR_READERS, (uintmax_t)NR_WRITERS);

    // Initialize RCU
    rcu_init();

    // Create reader threads
    for (i = 0; i < NR_READERS; i++) {
        if (pthread_create(&readers[i], NULL, thr_reader, &count_readers[i])) {
            // perror("pthread_create");
            // exit(EXIT_FAILURE);
            err(1, "Failed to create reader thread no. %ju", (uintmax_t)i);

        }
    }

    // Create writer threads
    for (i = 0; i < NR_WRITERS; i++) {
        if (pthread_create(&writers[i], NULL, thr_writer, &count_writers[i])) {
            err(1, "Failed to create writer thread no. %ju", (uintmax_t)i);
        }
    }

    // Let the threads run for a while
    sleep(10);
    atomic_store(&stop_flag, true);

    // Join reader threads
    for (i = 0; i < NR_READERS; i++) {
        pthread_join(readers[i], NULL);
    }

    // Join writer threads
    for (i = 0; i < NR_WRITERS; i++) {
        pthread_join(writers[i], NULL);
    }

    // Print counts
    for (i = 0; i < NR_READERS; i++) {
        printf("Reader %d read %llu times\n", i, count_readers[i]);
    }
    for (i = 0; i < NR_WRITERS; i++) {
        printf("Writer %d wrote %llu times\n", i, count_writers[i]);
    }

    return 0;
}