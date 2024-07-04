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
    "signal"
    "mb"
    "memb"
    "bp"
    "slotpair"
    "slotlist"
)

# Create output directory if it doesn't exist
mkdir -p $OUTPUT_DIR

# Loop over the number of readers and executables
for EXECUTABLE in "${EXECUTABLES[@]}"; do
    if [ "$RUN_MODE" -eq 0 ]; then
        # Use NUM_READERS directly if EXTERNAL_PARAM is 0
        OUTPUT_FILE="${OUTPUT_DIR}/perf_output_${EXECUTABLE}_${NUM_READERS}_readers.txt"
        perf stat -e cycles,instructions,context-switches,cpu-migrations,L1-dcache-loads,L1-dcache-stores,cache-references,cache-misses,L1-dcache-load-misses,L1-dcache-store-misses,LLC-load-misses,LLC-store-misses\
                -o $OUTPUT_FILE -- ./$EXECUTABLE $NUM_READERS $NUM_WRITERS $VALID_CPUS
    else
        # Run for each reader count from 1 to NUM_READERS
        for ((NUM_READER=1; NUM_READER<=NUM_READERS; NUM_READER++)); do
            OUTPUT_FILE="${OUTPUT_DIR}/perf_output_${EXECUTABLE}_${NUM_READER}_readers.txt"
            perf stat -e cycles,instructions,context-switches,cpu-migrations,L1-dcache-loads,L1-dcache-stores,cache-references,cache-misses,L1-dcache-load-misses,L1-dcache-store-misses,LLC-load-misses,LLC-store-misses\
                    -o $OUTPUT_FILE -- ./$EXECUTABLE $NUM_READER $NUM_WRITERS $VALID_CPUS
        done
    fi
done
