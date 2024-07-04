Required libtsgv.so in privoud folder (?)
* plot_memory_bar.py 
    1. require  use `make` to generate executable files.
    2. require to `./run_perf.sh {RUN_MODE(0)} {NUM_READERS} {NUM_WRITERS} {VALIID_CPUS} {OUTPUT_DIR}` e.g. `./run_perf.sh 0 7 1 0,2,4,6 perf_output` : it would generate perf result of 1 writer and 7 readers with differnet methods. (uruc+ctp)
    3. `python plot_memory_bar.py`
* plot_memory_line.py :
    1. `make`
    2. require to `./run_perf.sh {RUN_MODE(1)} {NUM_READERS} {NUM_WRITERS} {VALIID_CPUS} {OUTPUT_DIR}` e.g. `./run_perf.sh 1 11 1 0,2,4,6 perf_output` : it would generate differnet combination of 1 writer and multiple readers (1~11) with differnet methods. (5 uruc + 2ctp).
    3. `python plot_memory_line.py`
* plot_throughput_bar.py  
  * (modify num_readers_list,  num_writers, valid_cpus)
* verify.py  == plot_thoughput_line.py