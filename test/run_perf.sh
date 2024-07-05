#!/bin/bash

# Variables
RUN_MODE=$1
NUM_READERS=$2
NUM_WRITERS=$3
VALID_CPUS=$4
OUTPUT_DIR=$5

# Executable binaries
EXECUTABLES=(
    "qsbr"
    "bp"
    "mb"
    "memb"
    "signal"
    "slotpair"
    "slotlist"
)


# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/csv"


# Loop over the number of readers and executables
for EXECUTABLE in "${EXECUTABLES[@]}"; do
    if [ "$RUN_MODE" -eq 0 ]; then
        # Use NUM_READERS directly if RUN_MODE is 0
        OUTPUT_FILE="${OUTPUT_DIR}/perf_output_${EXECUTABLE}_${NUM_READERS}_readers.txt"
        OUTPUT_TXT="${OUTPUT_DIR}/csv/${EXECUTABLE}_${NUM_READERS}_${NUM_WRITERS}.txt"
        taskset -c $VALID_CPUS perf stat -e cycles,instructions,context-switches,cpu-migrations,L1-dcache-loads,L1-dcache-stores,cache-references,cache-misses,L1-dcache-load-misses,L1-dcache-store-misses,LLC-load-misses,LLC-store-misses \
                -o $OUTPUT_FILE -- ./$EXECUTABLE $NUM_READERS $NUM_WRITERS $VALID_CPUS > $OUTPUT_TXT 2>&1
    else
        # Run for each reader count from 1 to NUM_READERS
        for ((NUM_READER=1; NUM_READER<=NUM_READERS; NUM_READER++)); do
            OUTPUT_FILE="${OUTPUT_DIR}/perf_output_${EXECUTABLE}_${NUM_READER}_readers.txt"
            OUTPUT_TXT="${OUTPUT_DIR}/csv/${EXECUTABLE}_${NUM_READER}_${NUM_WRITERS}.txt"
            taskset -c $VALID_CPUS perf stat -e cycles,instructions,context-switches,cpu-migrations,L1-dcache-loads,L1-dcache-stores,cache-references,cache-misses,L1-dcache-load-misses,L1-dcache-store-misses,LLC-load-misses,LLC-store-misses \
                    -o $OUTPUT_FILE -- ./$EXECUTABLE $NUM_READER $NUM_WRITERS $VALID_CPUS > $OUTPUT_TXT 2>&1
        done
    fi
done

if [ "$RUN_MODE" -eq 0 ]; then
    python3 plot_memory_bar.py
    python3 plot_throughput_bar.py $NUM_READERS $NUM_WRITERS $VALID_CPUS $OUTPUT_DIR
else
    python3 plot_memory_line.py
    python3 plot_throughput_line.py $NUM_READERS $NUM_WRITERS $VALID_CPUS $OUTPUT_DIR
fi