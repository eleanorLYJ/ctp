import os
import subprocess
import re
import pandas as pd
import matplotlib.pyplot as plt
from multiprocessing import Pool

# Paths to C source files and executable
# source_files = ["qsbr.c", "qsbr-bp.c", "qsbr-mb.c", "qsbr-memb.c", "signal.c", "ctp.c"]
executables = ["./qsbr", "./bp", "./mb", "./memb", "./signal", "./ctp_slotpair", "./ctp_slotlist"]
urcu_names = ["qsbr", "qsbr-bp", "qsbr-mb", "qsbr-memb", "signal", "ctp_slotpair", "ctp_slotlist"]

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
        "gcc -o ctp_slotpair ctp.c -DUSE_SLOT_PAIR_DESIGN -L../ -ltsgv -lpthread -Wl,-rpath,../",
        "gcc -o ctp_slotlist ctp.c -DUSE_SLOT_LIST_DESIGN -L../ -ltsgv -lpthread -Wl,-rpath,../"
    ]
    
    for command in compile_commands:
        subprocess.run(command, shell=True, check=True)

# Function to execute the programs and capture the output
def execute_program(executable, num_readers, num_writers):
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "../"  # Ensure the path to libtsgv.so is included
    result = subprocess.run([executable, str(num_readers), str(num_writers)], capture_output=True, text=True, env=env)
    return result.stdout

# Function to parse the output and save to CSV
def parse_and_save_output(output, executable, num_readers, num_writers):
    reader_counts = re.findall(r"Reader \d+ read (\d+) times", output)
    writer_counts = re.findall(r"Writer \d+ wrote (\d+) times", output)

    # Ensure the lengths of reader_counts and writer_counts are the same
    min_length = min(len(reader_counts), len(writer_counts))
    reader_counts = reader_counts[:min_length]
    writer_counts = writer_counts[:min_length]

    data = {
        "num_readers": [num_readers] * min_length,
        "num_writers": [num_writers] * min_length,
        "reader_counts": list(map(int, reader_counts)),
        "writer_counts": list(map(int, writer_counts)),
        "executable": [executable] * min_length
    }

    df = pd.DataFrame(data)
    csv_path = os.path.join(csv_dir, f"results_{executable[2:]}_{num_readers}_{num_writers}.csv")
    df.to_csv(csv_path, index=False)

# Function to generate comparison plots
def generate_plots():
    all_data = []

    for executable in executables:
        for num_readers in range(1, 11):
            for num_writers in [2]:  # Assuming number of writers remains constant
                csv_path = os.path.join(csv_dir, f"results_{executable[2:]}_{num_readers}_{num_writers}.csv")
                df = pd.read_csv(csv_path)
                all_data.append(df)

    combined_df = pd.concat(all_data)
    
    colors = plt.cm.get_cmap('tab10', len(urcu_names))

    # Reader comparison plot
    plt.figure(figsize=(12, 8))
    for idx, exe in enumerate(combined_df["executable"].unique()):
        subset_df = combined_df[combined_df["executable"] == exe]
        plt.plot(subset_df["num_readers"], subset_df["reader_counts"], label=f"{exe[2:]} readers", color=colors(idx))
        
        for x, y in zip(subset_df["num_readers"], subset_df["reader_counts"]):
            plt.text(x, y, str(y), fontsize=8)

    plt.xlabel("Number of Readers")
    plt.ylabel("Reader Counts")
    plt.title("Reader Counts by Number of Readers")
    plt.legend()
    plt.savefig("reader_comparison_plot.png")
    plt.show()

    # Writer comparison plot
    plt.figure(figsize=(12, 8))
    for idx, exe in enumerate(combined_df["executable"].unique()):
        subset_df = combined_df[combined_df["executable"] == exe]
        plt.plot(subset_df["num_readers"], subset_df["writer_counts"], label=f"{exe[2:]} writers", color=colors(idx))
        
        for x, y in zip(subset_df["num_readers"], subset_df["writer_counts"]):
            plt.text(x, y, str(y), fontsize=8)

    plt.xlabel("Number of Readers")
    plt.ylabel("Writer Counts")
    plt.title("Writer Counts by Number of Readers")
    plt.legend()
    plt.savefig("writer_comparison_plot.png")
    plt.show()

# Function to compile and execute for given number of readers and writers
def compile_and_execute(num_readers):
    num_writers = 2  # Modify this if you want to change the number of writers

    # Compile all programs
    compile_programs()
    
    # Execute each compiled program and collect results
    for exe in executables:
        output = execute_program(exe, num_readers, num_writers)
        parse_and_save_output(output, exe, num_readers, num_writers)

# Main script execution
def main():
    num_readers_list = range(1, 11)
    
    with Pool() as pool:
        pool.map(compile_and_execute, num_readers_list)
    
    # Generate plots
    generate_plots()

if __name__ == "__main__":
    main()
