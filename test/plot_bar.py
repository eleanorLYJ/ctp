import os
import subprocess
import re
import pandas as pd
import matplotlib.pyplot as plt
from multiprocessing import Pool

# Paths to C source files and executables
executables = ["./qsbr", "./bp", "./mb", "./memb", "./signal", "./slotpair", "./slotlist"]
urcu_names = ["qsbr", "qsbr-bp", "qsbr-mb", "qsbr-memb", "signal", "slotpair", "slotlist"]

# Directory to save CSV files
csv_dir = "csv"
os.makedirs(csv_dir, exist_ok=True)

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
def execute_program(executable, num_readers, num_writers, cpus):
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "../"  # Ensure the path to libtsgv.so is included

    # Prepare the taskset command with the specified CPUs
    cpu_list = ','.join(map(str, cpus))
    taskset_command = ['taskset', '-c', cpu_list, executable, str(num_readers), str(num_writers)]
    
    result = subprocess.run(taskset_command, capture_output=True, text=True, env=env)
    return result.stdout

# Function to parse the output and save to CSV
def parse_and_save_output(output, executable, num_readers, num_writers):
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
        for num_readers in [10]:
            for num_writers in [2]:  # Assuming number of writers remains constant
                csv_path = os.path.join(csv_dir, f"results_{executable[2:]}_{num_readers}_{num_writers}.csv")
                df = pd.read_csv(csv_path)
                all_data.append(df)

    combined_df = pd.concat(all_data)
    colors = plt.cm.get_cmap('tab10', len(urcu_names))

    # Reader comparison plot (bar chart with numbers)
    plt.figure(figsize=(12, 8))
    bars = plt.bar(combined_df["executable"].unique(), combined_df.groupby('executable')['total_reader_count'].sum(), color=colors(range(len(urcu_names))))
    plt.xlabel("Executable")
    plt.ylabel("Total Reader Counts (Sum)")
    plt.title("Total Reader Counts (Sum) by Executable")
    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability

    # Add count values on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + yval * 0.05, int(yval), ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.savefig("reader_comparison_bar.png")
    plt.show()

    # Writer comparison plot (bar chart with numbers) - similar to reader plot
    plt.figure(figsize=(12, 8))
    bars = plt.bar(combined_df["executable"].unique(), combined_df.groupby('executable')['total_writer_count'].sum(), color=colors(range(len(urcu_names))))
    plt.xlabel("Executable")
    plt.ylabel("Total Writer Counts")
    plt.title("Total Writer Counts by Executable")
    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + yval * 0.05, int(yval), ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.savefig("writer_comparison_bar.png")
    plt.show()



# Function to compile and execute for given number of readers and writers
def compile_and_execute(num_readers):
    num_writers = 2  # Modify this if you want to change the number of writers

    # Compile all programs
    compile_programs()
    # Generate CPU list based on the number of readers and writers
    total_threads = num_readers + num_writers
    num_cores = os.cpu_count() // 2  # Assuming hyperthreading is disabled, and you have half the number of logical CPUs
    cpus = list(range(min(total_threads, num_cores)))

    # Execute each compiled program and collect results
    for exe in executables:
        output = execute_program(exe, num_readers, num_writers, cpus)
        parse_and_save_output(output, exe, num_readers, num_writers)

# Main script execution
def main():
    num_readers_list = [10]
    
    with Pool() as pool:
        pool.map(compile_and_execute, num_readers_list)
    
    # Generate plots
    generate_plots()

if __name__ == "__main__":
    main()
