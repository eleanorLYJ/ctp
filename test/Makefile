CC = gcc
CFLAGS = -Wall -g

# Source files
QSBR_SRC = qsbr.c
SIGNAL_SRC = signal.c
QSBR_MB_SRC = qsbr-mb.c
QSBR_MEMB_SRC = qsbr-memb.c
QSBR_BP_SRC = qsbr-bp.c
CTP_SRC = ctp.c

# Output binaries
QSBR_BIN = qsbr
SIGNAL_BIN = signal
QSBR_MB_BIN = mb
QSBR_MEMB_BIN = memb
QSBR_BP_BIN = bp
CTP_SLOT_PAIR_BIN = slotpair
CTP_SLOT_LIST_BIN = slotlist

# Libraries
QSBR_LIBS = -lurcu-qsbr -lpthread
SIGNAL_LIBS = -lurcu -lurcu-signal -lpthread
QSBR_MB_LIBS = -lurcu -lurcu-mb -lpthread
QSBR_MEMB_LIBS = -lurcu -lpthread
QSBR_BP_LIBS = -lurcu-bp -lpthread
CTP_LIBS = -L../ -ltsgv -lpthread

# Perf command
PERF_CMD = perf stat -e cycles,task-clock,instructions,context-switches,cpu-migrations,cache-references,cache-misses,L1-dcache-loads,L1-dcache-stores,LLC-load-misses,LLC-store-misses

NUM_READERS = 10
NUM_WRITERS = 1
VALID_CPUS = "0,2,4,6"

# Targets
all: $(QSBR_BIN) $(SIGNAL_BIN) $(QSBR_MB_BIN) $(QSBR_MEMB_BIN) $(QSBR_BP_BIN) $(CTP_SLOT_PAIR_BIN) $(CTP_SLOT_LIST_BIN) $(CTP_SLOT_LIST_BIN) $(CTP_SLOT_PAIR_BIN)

$(QSBR_BIN): $(QSBR_SRC)
	$(CC) $(CFLAGS) -o $@ -g $< $(QSBR_LIBS)

$(SIGNAL_BIN): $(SIGNAL_SRC)
	$(CC) $(CFLAGS) -o $@ -g $< $(SIGNAL_LIBS)

$(QSBR_MB_BIN): $(QSBR_MB_SRC)
	$(CC) $(CFLAGS) -o $@ -g $< $(QSBR_MB_LIBS)

$(QSBR_MEMB_BIN): $(QSBR_MEMB_SRC)
	$(CC) $(CFLAGS) -o $@ -g $< $(QSBR_MEMB_LIBS)

$(QSBR_BP_BIN): $(QSBR_BP_SRC)
	$(CC) $(CFLAGS) -o $@ -g $< $(QSBR_BP_LIBS)


$(CTP_SLOT_PAIR_BIN): $(CTP_SRC)
	$(CC) $(CFLAGS) -DUSE_SLOT_PAIR_DESIGN -o $@ -g $< $(CTP_LIBS) -Wl,-rpath,..

$(CTP_SLOT_LIST_BIN): $(CTP_SRC)
	$(CC) $(CFLAGS) -DUSE_SLOT_LIST_DESIGN -o $@ -g $< $(CTP_LIBS) -Wl,-rpath,..

clean:
	rm -f $(QSBR_BIN) $(SIGNAL_BIN) $(QSBR_MB_BIN) $(QSBR_MEMB_BIN) $(QSBR_BP_BIN) $(CTP_SLOT_PAIR_BIN) $(CTP_SLOT_LIST_BIN)
	rm -fr ./csv/* *.txt *.png ./output/* cachegrind.out.*

perf: all
	$(PERF_CMD) ./$(QSBR_BIN) $(NUM_READERS) $(NUM_WRITERS) $(VALID_CPUS)
	$(PERF_CMD) ./$(SIGNAL_BIN) $(NUM_READERS) $(NUM_WRITERS) $(VALID_CPUS)
	$(PERF_CMD) ./$(QSBR_MB_BIN) $(NUM_READERS) $(NUM_WRITERS) $(VALID_CPUS)
	$(PERF_CMD) ./$(QSBR_MEMB_BIN) $(NUM_READERS) $(NUM_WRITERS) $(VALID_CPUS)
	$(PERF_CMD) ./$(QSBR_BP_BIN) $(NUM_READERS) $(NUM_WRITERS) $(VALID_CPUS)
	$(PERF_CMD) ./$(CTP_SLOT_PAIR_BIN) $(NUM_READERS) $(NUM_WRITERS) $(VALID_CPUS)
	$(PERF_CMD) ./$(CTP_SLOT_LIST_BIN) $(NUM_READERS) $(NUM_WRITERS) $(VALID_CPUS)


