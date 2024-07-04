import os
import subprocess
import re
import pandas as pd
import psutil
import matplotlib.pyplot as plt
from multiprocessing import Pool

# Global variables
num_readers_range = range(1, 12) 
num_writers = 1

# Paths to C source files and executables
executables = ["./qsbr", "./bp", "./mb", "./memb", "./signal", "./slotpair", "./slotlist"]
urcu_names = ["qsbr", "qsbr-bp", "qsbr-mb", "qsbr-memb", "signal", "slotpair", "slotlist"]

# Directory to save CSV files
csv_dir = "csv"
os.makedirs(csv_dir, exist_ok=True)

# Directory to save cachegrind output
cachegrind_dir = "cachegrind"
os.makedirs(cachegrind_dir, exist_ok=True)

# Function to compile the C programs
def compile_programs():
    compile_commands = [
        "gcc -o qsbr qsbr.c -lurcu-qsbr -lpthread",
        "gcc -o bp qsbr-bp.c -lurcu-bp -lpthread",
        "gcc -o mb qsbr-mb.c -lurcu -lurcu-mb -lpthread",
        "gcc -o memb qsbr-memb.c -lurcu -lpthread",
        "gcc -o signal signal.c -lurcu -lurcu-signal -lpthread",
        "gcc -o slotpair ctp.c -DUSE_SLOT_PAIR_DESIGN -L../ -ltsgv -lpthread -Wl,-rpath,../",
        "gcc -o slotlist ctp.c -DUSE_SLOT_LIST_DESIGN -L../ -ltsgv -lpthread -Wl,-rpath,../"
    ]
    
    for command in compile_commands:
        subprocess.run(command, shell=True, check=True)

# Function to execute the programs and capture the output with CPU affinity
def execute_program(executable, num_readers, cpus, valid_cpus):
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "../"  # Ensure the path to libtsgv.so is included

    # Prepare the taskset command with the specified CPUs
    cpu_list = ','.join(map(str, cpus))
    taskset_command = ['taskset', '-c', cpu_list, executable, str(num_readers), str(num_writers), valid_cpus]

    process = subprocess.Popen(taskset_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)

    proc = psutil.Process(process.pid)
    cpu_usage = []
    memory_usage = []
    try:
        while True:
            cpu_percent = proc.cpu_percent(interval=1) / psutil.cpu_count()
            memory_info = proc.memory_info()
            cpu_usage.append(cpu_percent)
            memory_usage.append(memory_info.rss)

            if process.poll() is not None:
                break

        stdout, stderr = process.communicate()
    except Exception as e:
        process.kill()
        stdout, stderr = process.communicate()
        print(f"Error: {e}")

    # Write CPU and memory usage to memory.txt
    with open("memory.txt", "a") as f:
        f.write(f"Executable: {executable}\n")
        f.write(f"Num Readers: {num_readers}, Num Writers: {num_writers}, Valid CPUs: {valid_cpus}\n")
        f.write(f"CPU usage: {cpu_usage}\n")
        f.write(f"Memory usage: {memory_usage}\n")
        f.write("\n")

    return stdout

# Function to parse the output and save to CSV
def parse_and_save_output(output, executable, num_readers):
    reader_counts = re.findall(r"Reader \d+ read (\d+) times", output)
    writer_counts = re.findall(r"Writer \d+ wrote (\d+) times", output)

    total_reader_count = sum(map(int, reader_counts))
    total_writer_count = sum(map(int, writer_counts))

    data = {
        "num_readers": [num_readers],
        "num_writers": [num_writers],
        "total_reader_count": [total_reader_count],
        "total_writer_count": [total_writer_count],
        "executable": [executable]
    }

    df = pd.DataFrame(data)
    csv_path = os.path.join(csv_dir, f"results_{executable[2:]}_{num_readers}_{num_writers}.csv")
    df.to_csv(csv_path, index=False)

# Function to generate comparison plots
def generate_plots():
    all_data = []

    for executable in executables:
        for num_readers in num_readers_range:
            csv_path = os.path.join(csv_dir, f"results_{executable[2:]}_{num_readers}_{num_writers}.csv")
            df = pd.read_csv(csv_path)
            all_data.append(df)

    combined_df = pd.concat(all_data)
    
    colors = plt.cm.get_cmap('tab10', len(urcu_names))

    # Reader comparison plot
    plt.figure(figsize=(12, 8))
    for idx, exe in enumerate(combined_df["executable"].unique()):
        subset_df = combined_df[combined_df["executable"] == exe]
        plt.plot(subset_df["num_readers"], subset_df["total_reader_count"], label=f"{exe[2:]} readers", color=colors(idx))
        
        for x, y in zip(subset_df["num_readers"], subset_df["total_reader_count"]):
            plt.text(x, y, str(y), fontsize=8)

    plt.xlabel("Number of Readers")
    plt.ylabel("Total Reader Counts")
    plt.title("Total Reader Counts by Number of Readers")
    plt.legend()
    plt.savefig("reader_comparison_plot.png")
    plt.show()

    # Writer comparison plot
    plt.figure(figsize=(12, 8))
    for idx, exe in enumerate(combined_df["executable"].unique()):
        subset_df = combined_df[combined_df["executable"] == exe]
        plt.plot(subset_df["num_readers"], subset_df["total_writer_count"], label=f"{exe[2:]} writers", color=colors(idx))
        
        for x, y in zip(subset_df["num_readers"], subset_df["total_writer_count"]):
            plt.text(x, y, str(y), fontsize=8)

    plt.xlabel("Number of Readers")
    plt.ylabel("Total Writer Counts")
    plt.title("Total Writer Counts by Number of Readers")
    plt.legend()
    plt.savefig("writer_comparison_plot.png")
    plt.show()

# def parse_cachegrind_output(cachegrind_file):
#     cache_info = {
#         "Ir": 0,
#         "I1mr": 0,
#         "ILmr": 0,
#         "Dr": 0,
#         "D1mr": 0,
#         "DLmr": 0,
#         "Dw": 0,
#         "D1mw": 0,
#         "DLmw": 0
#     }

#     with open(cachegrind_file, "r") as f:
#         lines = f.readlines()
#         last_line = lines[-1]
#         cleaned_line = last_line.replace("summary: ", "").strip()
#         integers = cleaned_line.split()
#         array = [int(i) for i in integers]
#         cache_info["Ir"] += int(integers[0])
#         cache_info["I1mr"] += int(integers[1])
#         cache_info["ILmr"] += int(integers[2])
#         cache_info["Dr"] += int(integers[3])
#         cache_info["D1mr"] += int(integers[4])
#         cache_info["DLmr"] += int(integers[5])
#         cache_info["Dw"] += int(integers[6])
#         cache_info["D1mw"] += int(integers[7])
#         cache_info["DLmw"] += int(integers[8])
    
#     return cache_info


def profile_with_cachegrind(executable, num_readers, valid_cpus):
    command = f"valgrind --tool=cachegrind --cachegrind-out-file={cachegrind_dir}/cachegrind.out.{num_readers}_{executable[2:]} {executable} {num_readers} {num_writers} {valid_cpus}"
    subprocess.run(command, shell=True, check=True)

# Function to compile and execute for given number of readers and writers
def compile_and_execute(num_readers):
    total_threads = num_readers + num_writers
    valid_cpus = "0,2,4,6"  # Modify this based on your valid CPUs
    # Compile all programs
    compile_programs()
    # Execute each compiled program and collect results
    # Assuming hyperthreading is disabled, and you have half the number of logical CPUs
    cpus = list(range(min(total_threads, os.cpu_count() // 2)))
    print("start executing")
    for exe in executables:
        output = execute_program(exe, num_readers, cpus, valid_cpus)
        parse_and_save_output(output, exe, num_readers)
        profile_with_cachegrind(exe, num_readers, valid_cpus)
    print("finish")
# Generate cachegrind plots
# def generate_cachegrind_plots():
#     all_cache_data = []

#     for executable in executables:
#         for num_readers in num_readers_range:
#             cachegrind_file = f"{cachegrind_dir}/cachegrind.out.{num_readers}_{executable[2:]}"
#             cache_info = parse_cachegrind_output(cachegrind_file)
#             cache_info["num_readers"] = num_readers
#             cache_info["executable"] = executable
#             all_cache_data.append(cache_info)

#     cache_df = pd.DataFrame(all_cache_data)

#     colors = plt.cm.get_cmap('tab10', len(urcu_names))

#     metrics = ["Ir", "I1mr", "ILmr", "Dr", "D1mr", "DLmr", "Dw", "D1mw", "DLmw"]

#     for metric in metrics:
#         plt.figure(figsize=(12, 8))
#         for idx, exe in enumerate(cache_df["executable"].unique()):
#             subset_df = cache_df[cache_df["executable"] == exe]
#             plt.plot(subset_df["num_readers"], subset_df[metric], label=f"{exe[2:]} {metric}", color=colors(idx))

#             for x, y in zip(subset_df["num_readers"], subset_df[metric]):
#                 plt.text(x, y, str(y), fontsize=8)

#         plt.xlabel("Number of Readers")
#         plt.ylabel(metric)
#         plt.title(f"{metric} by Number of Readers")
#         plt.legend()
#         plt.savefig(f"cachegrind_plot_{metric}.png")
#         plt.show()

# Main script execution
def main():
    with Pool() as pool:
        pool.map(compile_and_execute, num_readers_range)
    
    # Generate execution plots
    generate_plots()
    # Generate cachegrind plots
    # generate_cachegrind_plots()

if __name__ == "__main__":
    main()