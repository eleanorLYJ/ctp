#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <stdatomic.h>
#include <assert.h>
#include <time.h>
#include <unistd.h>
#include <stdarg.h>

#include <urcu-qsbr.h>

// Define global variables and macros
static int *test_rcu_pointer;

#define NR_READERS 10
#define NR_WRITERS 2
#define VERBOSE 1  // Set verbosity level

atomic_bool stop_flag = false;

__thread unsigned long long nr_reads = 0;
__thread unsigned long long nr_writes = 0;

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
    int *new, *old;
    while (!atomic_load(&stop_flag)) {
        new = malloc(sizeof(int));
        assert(new);
        *new = 8;
        old = rcu_xchg_pointer(&test_rcu_pointer, new);

        urcu_qsbr_synchronize_rcu();
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
    int *local_ptr;
    
    urcu_qsbr_register_thread();
    // mark long periods for which the threads are not active. 
    rcu_thread_offline();
    rcu_thread_online();
    
    while (!atomic_load(&stop_flag)) {
        urcu_qsbr_read_lock();
        local_ptr = rcu_dereference(test_rcu_pointer);
        if (local_ptr)
            assert(*local_ptr == 8);
        urcu_qsbr_read_unlock();
        nr_reads++;
        /* Every 1024 readings, enter a quiescent state */
        if (caa_unlikely((nr_reads & ((1 << 10) - 1)) == 0))
            rcu_quiescent_state();
    }

    urcu_qsbr_unregister_thread();

    *count = nr_reads;
    printf_verbose("thread_end %s, tid %lu\n", "reader", pthread_self());
    return ((void*)1);
}

int main() {
    pthread_t readers[NR_READERS], writers[NR_WRITERS];
    unsigned long long count_readers[NR_READERS], count_writers[NR_WRITERS];
    int i;

    // Create reader threads
    for (i = 0; i < NR_READERS; i++) {
        if (pthread_create(&readers[i], NULL, thr_reader, &count_readers[i])) {
            perror("pthread_create");
            exit(EXIT_FAILURE);
        }
    }

    // Create writer threads
    for (i = 0; i < NR_WRITERS; i++) {
        if (pthread_create(&writers[i], NULL, thr_writer, &count_writers[i])) {
            perror("pthread_create");
            exit(EXIT_FAILURE);
        }
    }

    // Let the threads run for a while
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

    // Print counts
    for (i = 0; i < NR_READERS; i++) {
        printf("Reader %d read %llu times\n", i, count_readers[i]);
    }
    for (i = 0; i < NR_WRITERS; i++) {
        printf("Writer %d wrote %llu times\n", i, count_writers[i]);
    }

    return 0;
}
