#define _GNU_SOURCE
#include <sched.h>
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
#include <stdarg.h>

#include <urcu.h>
#define RCU_SIGNAL

// Define global variables and macros
static struct rcu_data {
    int value;
    long long version;
} *shared_ptr = NULL;

#define VERBOSE 1  // Set verbosity level

atomic_bool stop_flag = false;
FILE *writer_log, *reader_log;
int *valid_cpus;
int num_valid_cpus;

struct thread_info {
    int core_id;
    unsigned long long count;
};


// void printf_verbose(const char *format, ...) {
//     if (VERBOSE) {
//         va_list args;
//         va_start(args, format);
//         vprintf(format, args);
//         va_end(args);
//     }
// }

void set_affinity(int cpu) {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(cpu, &cpuset);

    pthread_t current_thread = pthread_self();
    int ret = pthread_setaffinity_np(current_thread, sizeof(cpu_set_t), &cpuset);
    if (ret != 0) {
        fprintf(stderr, "Error setting CPU affinity for thread %lu to CPU %d: %s\n", current_thread, cpu, strerror(ret));
    }
}

void check_affinity() {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    pthread_t current_thread = pthread_self();
    pthread_getaffinity_np(current_thread, sizeof(cpu_set_t), &cpuset);
    // for (int i = 0; i < CPU_SETSIZE; i++) {
    //     if (CPU_ISSET(i, &cpuset)) {
    //         printf("Thread %lu is running on CPU %d\n", current_thread, i);
    //     }
    // }
}
int get_valid_cpu(int core_id) {
    // if (core_id >= num_valid_cpus) {
    //     return -1;
    // }
    // return valid_cpus[core_id];
    return valid_cpus[core_id % num_valid_cpus];
}

void parse_cpu_list(const char *cpu_list) {
    char *token;
    char *cpu_list_copy = strdup(cpu_list);
    int count = 0;

    token = strtok(cpu_list_copy, ",");
    while (token != NULL) {
        count++;
        token = strtok(NULL, ",");
    }

    free(cpu_list_copy);
    valid_cpus = malloc(count * sizeof(int));
    if (!valid_cpus) {
        perror("Failed to allocate memory for valid_cpus");
        exit(EXIT_FAILURE);
    }

    cpu_list_copy = strdup(cpu_list);
    count = 0;

    token = strtok(cpu_list_copy, ",");
    while (token != NULL) {
        valid_cpus[count++] = atoi(token);
        token = strtok(NULL, ",");
    }

    num_valid_cpus = count;
    free(cpu_list_copy);
}

void *thr_writer(void *arg) 
{
    struct thread_info *info = (struct thread_info *)arg;
    int core_id = get_valid_cpu(info->core_id);
    if (core_id >= 0) {
        set_affinity(core_id);
    } else {
        fprintf(stderr, "Invalid core ID: %d\n", core_id);
        fflush(stderr);
    }

    check_affinity();

    unsigned long long nr_writes = 0;
    struct rcu_data *new, *old;
    static atomic_llong global_version = 0; // Global version counter to avoid conflicts between writers

    while (!atomic_load(&stop_flag)) {
        new = malloc(sizeof(int));
        assert(new);
        new->value = rand();  // Assign a random value
        new->version = atomic_fetch_add(&global_version, 1);
        old = rcu_xchg_pointer(&shared_ptr, new);

        fprintf(writer_log, "Writer: value=%d, version=%lld\n", new->value, new->version);
        fflush(writer_log);

        synchronize_rcu();  // Wait for all readers to finish

        free(old);
        old = NULL;
        nr_writes++;
    }
    // printf_verbose("thread_end %s, tid %lu\n", "writer", pthread_self());
    info->count = nr_writes;
    return ((void*)2);
}

void *thr_reader(void *arg) {
    struct thread_info *info = (struct thread_info *)arg;
    int core_id = get_valid_cpu(info->core_id);

    if (core_id >= 0) {
        set_affinity(core_id);
    } else {
        fprintf(stderr, "Invalid core ID: %d\n", core_id);
        fflush(stderr);
    }
    check_affinity();

    unsigned long long nr_reads = 0;
    struct rcu_data *local_ptr;

    
    rcu_register_thread();  // Register the thread with RCU
    
    while (!atomic_load(&stop_flag)) {
        rcu_read_lock();  // Start an RCU read-side critical section
        local_ptr = rcu_dereference(shared_ptr);
        if (local_ptr){
            fprintf(reader_log, "Reader: value=%d, version=%lld\n", local_ptr->value, local_ptr->version);
            fflush(reader_log);
        }
        rcu_read_unlock();  // End the RCU read-side critical section
        nr_reads++;
    }

    rcu_unregister_thread();  // Unregister the thread from RCU

    info->count = nr_reads;
    // printf_verbose("thread_end %s, tid %lu\n", "reader", pthread_self());
    return ((void*)1);
}


int main(int argc, char *argv[]) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <num_readers> <num_writers> <valid_cpus>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    int num_readers = atoi(argv[1]);
    int num_writers = atoi(argv[2]);
    parse_cpu_list(argv[3]);
    
    pthread_t readers[num_readers], writers[num_writers];
    struct thread_info reader_info[num_readers], writer_info[num_writers];
    int i;
    memset(readers, 0, sizeof(readers));
    memset(writers, 0, sizeof(writers));
    printf("Will use %ju reader threads and %ju writer threads\n",
           (uintmax_t)num_readers, (uintmax_t)num_writers);

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

    // Initialize RCU
    rcu_init();

    // Create reader threads
    for (i = 0; i < num_readers; i++) {
        reader_info[i].core_id = i;
        reader_info[i].count = 0;
        if (pthread_create(&readers[i], NULL, thr_reader, &reader_info[i])) {
            err(1, "Failed to create reader thread no. %ju", (uintmax_t)i);

        }
    }

    // Create writer threads
    for (i = 0; i < num_writers; i++) {
        writer_info[i].core_id = i + num_readers;
        writer_info[i].count = 0;
        if (pthread_create(&writers[i], NULL, thr_writer, &writer_info[i])) {
            err(1, "Failed to create writer thread no. %ju", (uintmax_t)i);
        }
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
        printf("Reader %d read %llu times\n", i, reader_info[i].count);
    for (i = 0; i < num_writers; i++) 
        printf("Writer %d wrote %llu times\n", i, writer_info[i].count);

    // Free the initial shared_ptr
    free(shared_ptr);
    shared_ptr = NULL;

    return 0;
}