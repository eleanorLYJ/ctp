import os
import re
import pandas as pd
import psutil
import matplotlib.pyplot as plt
from multiprocessing import Pool
import sys

# Global variables from command line arguments
num_readers_range = range(1, int(sys.argv[1]) + 1)
num_writers = int(sys.argv[2])
valid_cpus = sys.argv[3]
output_dir = sys.argv[4]

# Paths to C source files and executables
executables = ["./qsbr", "./bp", "./mb", "./memb", "./signal", "./slotpair", "./slotlist"]
urcu_names = ["qsbr", "qsbr-bp", "qsbr-mb", "qsbr-memb", "signal", "slotpair", "slotlist"]

# Directory to save CSV files
csv_dir = os.path.join(output_dir, "csv")
os.makedirs(csv_dir, exist_ok=True)

# Function to parse the output and save to CSV
def parse_and_save_output(output, executable, num_readers):
    with open(output, 'r') as file:
        output = file.read()
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

# # Function to generate comparison plots
def generate_plots():
    all_data = []

    for executable in executables:
        for num_readers in num_readers_range:
            csv_path = os.path.join(csv_dir, f"results_{executable[2:]}_{num_readers}_{num_writers}.csv")
            df = pd.read_csv(csv_path)
            all_data.append(df)

    combined_df = pd.concat(all_data)
    
    colors = plt.cm.get_cmap('tab10', len(executables))

    # Reader comparison plot
    plt.figure(figsize=(12, 8))
    for idx, exe in enumerate(combined_df["executable"].unique()):
        subset_df = combined_df[combined_df["executable"] == exe]
        plt.plot(subset_df["num_readers"], subset_df["total_reader_count"], label=f"{exe[2:]} readers", color=colors(idx))
        
        # for x, y in zip(subset_df["num_readers"], subset_df["total_reader_count"]):
        #     plt.text(x, y, str(y), fontsize=8)

    plt.xlabel("Number of Readers")
    plt.ylabel("Total Reader Counts")
    plt.title("Total Reader Counts by Number of Readers")
    plt.legend()
    plt.savefig(os.path.join(output_dir, "reader_comparison_plot.png"))
    plt.show()

    # Writer comparison plot
    plt.figure(figsize=(12, 8))
    for idx, exe in enumerate(combined_df["executable"].unique()):
        subset_df = combined_df[combined_df["executable"] == exe]
        plt.plot(subset_df["num_readers"], subset_df["total_writer_count"], label=f"{exe[2:]} writers", color=colors(idx))
        
        # for x, y in zip(subset_df["num_readers"], subset_df["total_writer_count"]):
        #     plt.text(x, y, str(y), fontsize=8)

    plt.xlabel("Number of Readers")
    plt.ylabel("Total Writer Counts")
    plt.title("Total Writer Counts by Number of Readers")
    plt.legend()
    plt.savefig(os.path.join(output_dir, "writer_comparison_plot.png"))
    plt.show()




# Main script execution
def main():
    # with Pool() as pool:
    #     pool.map(execute_for_readers, num_readers_range)
    for reader in num_readers_range:
       for exe in  executables:
           parse_and_save_output("./"+output_dir+'/csv/'+str(exe)[1:]+"_"+str(reader)+"_"+ str(num_writers) +".txt", exe, reader) # content is which printf output, that need to parse~
    
    # # Generate execution plots
    generate_plots()

if __name__ == "__main__":
    main()
