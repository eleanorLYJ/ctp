import os
import re
import pandas as pd
import matplotlib.pyplot as plt
from multiprocessing import Pool
import sys

# Global variables from command line arguments
num_readers = int(sys.argv[1])
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
def parse_and_save_output(output, executable):
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

 # Function to generate comparison plots
def generate_plots():
    all_data = []

    for executable in executables:
        csv_path = os.path.join(csv_dir, f"results_{executable[2:]}_{num_readers}_{num_writers}.csv")
        df = pd.read_csv(csv_path)
        all_data.append(df)

    combined_df = pd.concat(all_data)
    colors = plt.cm.get_cmap('tab10', len(urcu_names))

    # Reader comparison plot (bar chart with numbers)
    plt.figure(figsize=(12, 8))
    bars = plt.bar(combined_df["executable"].unique(), combined_df.groupby('executable')['total_reader_count'].sum(), color=colors(range(len(urcu_names))))
    plt.xlabel("Executable")
    plt.ylabel("Total Reader Counts")
    plt.title("Total Reader Counts by Executable")
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

# Main script execution
def main():
    
    for exe in  executables:
        parse_and_save_output("./"+output_dir+'/csv/'+str(exe)[2:]+"_"+str(num_readers)+"_"+ str(num_writers) +".txt", exe) # content is which printf output, that need to parse~
    
    # Generate plots
    generate_plots()

if __name__ == "__main__":
    main()
