CC = gcc
CFLAGS = -Wall -Wextra -ggdb3

# Source files
QSBR_SRC = qsbr.c
SIGNAL_SRC = signal.c
QSBR_MB_SRC = qsbr-mb.c
QSBR_MEMB_SRC = qsbr-memb.c
QSBR_BP_SRC = qsbr-bp.c

# Output binaries
QSBR_BIN = qsbr
SIGNAL_BIN = signal
QSBR_MB_BIN = mb
QSBR_MEMB_BIN = memb
QSBR_BP_BIN = bp

# Libraries
QSBR_LIBS = -lurcu-qsbr -lpthread
SIGNAL_LIBS = -lurcu -lurcu-signal -lpthread
QSBR_MB_LIBS = -lurcu -lurcu-mb -lpthread
QSBR_MEMB_LIBS = -lurcu -lpthread
QSBR_BP_LIBS = -lurcu-bp -lpthread

# Perf command
PERF_CMD = perf stat -e cycles,instructions,cache-references,cache-misses

# Targets
all: $(QSBR_BIN) $(SIGNAL_BIN) $(QSBR_MB_BIN) $(QSBR_MEMB_BIN) $(QSBR_BP_BIN)

$(QSBR_BIN): $(QSBR_SRC)
	$(CC) $(CFLAGS) -o $@ $< $(QSBR_LIBS)

$(SIGNAL_BIN): $(SIGNAL_SRC)
	$(CC) $(CFLAGS) -o $@ $< $(SIGNAL_LIBS)

$(QSBR_MB_BIN): $(QSBR_MB_SRC)
	$(CC) $(CFLAGS) -o $@ $< $(QSBR_MB_LIBS)

$(QSBR_MEMB_BIN): $(QSBR_MEMB_SRC)
	$(CC) $(CFLAGS) -o $@ $< $(QSBR_MEMB_LIBS)

$(QSBR_BP_BIN): $(QSBR_BP_SRC)
	$(CC) $(CFLAGS) -o $@ $< $(QSBR_BP_LIBS)

clean:
	rm -f $(QSBR_BIN) $(SIGNAL_BIN) $(QSBR_MB_BIN) $(QSBR_MEMB_BIN) $(QSBR_BP_BIN)

perf: all
	$(PERF_CMD) ./$(QSBR_BIN)
	$(PERF_CMD) ./$(SIGNAL_BIN)
	$(PERF_CMD) ./$(QSBR_MB_BIN)
	$(PERF_CMD) ./$(QSBR_MEMB_BIN)
	$(PERF_CMD) ./$(QSBR_BP_BIN)
