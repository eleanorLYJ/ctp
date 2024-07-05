**Required:** `libtsgv.so`, you can get it by `make` in the parent directory.

**Instructions:**
**Bar chart (memory usage and throughput)**
    1. Use `make` to generate executable files.
    2. Run the following command to generate performance results:
       ```shell
       ./run_perf.sh {RUN_MODE(0)} {NUM_READERS} {NUM_WRITERS} {VALID_CPUS} {OUTPUT_DIR}
       ```
       Example:
       ```shell
       ./run_perf.sh 0 7 1 0,2,4,6 perf_output
       ```
       This generates performance results for 1 writer and 7 readers using different methods (urcu + ctp).

**Bar chart (memory usage and throughput)**
    1. Use `make` to generate executable files.
    2. Run the following command to generate performance results:
       ```sh
       ./run_perf.sh {RUN_MODE(1)} {NUM_READERS} {NUM_WRITERS} {VALID_CPUS} {OUTPUT_DIR}
       ```
       Example:
       ```sh
       ./run_perf.sh 1 11 1 0,2,4,6 perf_output
       ```
       This generates different combinations of 1 writer and multiple readers (1~11) using different methods (5 urcu + 2 ctp).