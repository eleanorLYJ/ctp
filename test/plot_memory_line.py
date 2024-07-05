import os
import re
import pandas as pd
import matplotlib.pyplot as plt

method_order = ["qsbr", "bp", "mb", "memb", "signal", "slotpair", "slotlist"]

def parse_perf_output(file_path):
    metrics = {
        'cycles': 0,
        'instructions': 0,
        'context-switches': 0,
        'cpu-migrations': 0,
        'cache-references': 0,
        'cache-misses': 0,
        'L1-dcache-stores':0,
        'L1-dcache-loads':0,
        'L1-dcache-store-misses':0,
        'L1-dcache-load-misses':0,
        'LLC-load-misses': 0,
        'LLC-store-misses':0
    }

    with open(file_path, 'r') as f:
        for line in f:
            for key in metrics:
                if key in line:
                    value = re.search(r'(\d[\d,]*)', line.replace(',', '')).group().replace(',', '')
                    metrics[key] += int(value)
    
    return metrics

def collect_data(output_dir):
    data = []

    for file_name in os.listdir(output_dir):
        if file_name.startswith('perf_output'):
            parts = re.search(r'perf_output_(\w+)_([\d]+)_readers', file_name)
            executable = parts.group(1)
            num_readers = int(parts.group(2))
            file_path = os.path.join(output_dir, file_name)
            metrics = parse_perf_output(file_path)
            metrics['num_readers'] = num_readers
            metrics['executable'] = executable
            data.append(metrics)
    
    df = pd.DataFrame(data)
    df['executable'] = pd.Categorical(df['executable'], categories=method_order, ordered=True)
    return df.sort_values(by=['num_readers', 'executable'])

def plot_data(df):
    df = df.sort_values(by=['executable', 'num_readers'])

    # Plot memory usage (cache misses) for each executable
    plt.figure(figsize=(12, 8))
    for exe in df['executable'].unique():
        subset_df = df[df['executable'] == exe]
        plt.plot(subset_df['num_readers'], subset_df['cache-misses'], marker='o', label=f'{exe} Cache Misses')
        # for x, y in zip(subset_df["num_readers"], subset_df["cache-misses"]):
            # plt.text(x, y, str(y), fontsize=8)
    plt.xlabel('Number of Readers')
    plt.ylabel('Cache Misses')
    plt.title('Cache Misses vs. Number of Readers')
    plt.legend()
    plt.grid(True)
    plt.savefig('Cache_Misses.png')
    plt.show()

    # Plot L1-dcache-store-misses for each executable
    plt.figure(figsize=(12, 8))
    for exe in df['executable'].unique():
        subset_df = df[df['executable'] == exe]
        plt.plot(subset_df['num_readers'], subset_df['L1-dcache-store-misses'], marker='o', label=f'{exe} L1 Dcache Store Misses')
        # for x, y in zip(subset_df["num_readers"], subset_df["L1-dcache-store-misses"]):
            # plt.text(x, y, str(y), fontsize=8)
    plt.xlabel('Number of Readers')
    plt.ylabel('L1 Dcache Store Misses')
    plt.title('L1 Dcache Store Misses vs. Number of Readers')
    plt.legend()
    plt.grid(True)
    plt.savefig('L1_dcache_store_misses_plot.png')
    plt.show()


    # 'L1-dcache-load-misses':0,
    plt.figure(figsize=(12, 8))
    for exe in df['executable'].unique():
        subset_df = df[df['executable'] == exe]
        plt.plot(subset_df['num_readers'], subset_df['L1-dcache-load-misses'], marker='o', label=f'{exe} L1 Dcache Load Misses')
        # for x, y in zip(subset_df["num_readers"], subset_df["L1-dcache-load-misses"]):
            # plt.text(x, y, str(y), fontsize=8)
    plt.xlabel('Number of Readers')
    plt.ylabel('L1 Dcache Load Misses')
    plt.title('L1 Dcache Load Misses vs. Number of Readers')
    plt.legend()
    plt.grid(True)
    plt.savefig('L1_dcache_load_misses_plot.png')
    plt.show()

    plt.figure(figsize=(12, 8))
    for exe in df['executable'].unique():
        subset_df = df[df['executable'] == exe]
        plt.plot(subset_df['num_readers'], subset_df['L1-dcache-stores'], marker='o', label=f'{exe} L1 Dcache Store')
        # for x, y in zip(subset_df["num_readers"], subset_df["L1-dcache-stores"]):
            # plt.text(x, y, str(y), fontsize=8)
    plt.xlabel('Number of Readers')
    plt.ylabel('L1 Dcache Stores')
    plt.title('L1 Dcache Stores vs. Number of Readers')
    plt.legend()
    plt.grid(True)
    plt.savefig('L1-dcache-stores_plot.png')
    plt.show()

    plt.figure(figsize=(12, 8))
    for exe in df['executable'].unique():
        subset_df = df[df['executable'] == exe]
        plt.plot(subset_df['num_readers'], subset_df['L1-dcache-loads'], marker='o', label=f'{exe} L1 Dcache Load')
        # for x, y in zip(subset_df["num_readers"], subset_df["L1-dcache-loads"]):
            # plt.text(x, y, str(y), fontsize=8)
    plt.xlabel('Number of Readers')
    plt.ylabel('L1 Dcache Loads')
    plt.title('L1 Dcache Loads vs. Number of Readers')
    plt.legend()
    plt.grid(True)
    plt.savefig('L1-dcache-loads_plot.png')
    plt.show()

    plt.figure(figsize=(12, 8))
    for exe in df['executable'].unique():
        subset_df = df[df['executable'] == exe]
        plt.plot(subset_df['num_readers'], subset_df['LLC-load-misses'], marker='o', label=f'{exe} LLC load misses')
        # for x, y in zip(subset_df["num_readers"], subset_df["LLC-load-misses"]):
            # plt.text(x, y, str(y), fontsize=8)
    plt.xlabel('Number of Readers')
    plt.ylabel('LL Load Misses')
    plt.title('LL Load Misses vs. Number of Readers')
    plt.legend()
    plt.grid(True)
    plt.savefig('L1-dcache-loads_plot.png')
    plt.show()

    plt.figure(figsize=(12, 8))
    for exe in df['executable'].unique():
        subset_df = df[df['executable'] == exe]
        plt.plot(subset_df['num_readers'], subset_df['LLC-store-misses'], marker='o', label=f'{exe} LLC Store misses')
        # for x, y in zip(subset_df["num_readers"], subset_df["LLC-store-misses"]):
            # plt.text(x, y, str(y), fontsize=8)
    plt.xlabel('Number of Readers')
    plt.ylabel('LL Store Misses')
    plt.title('LL Store Misses vs. Number of Readers')
    plt.legend()
    plt.grid(True)
    plt.savefig('L1-dcache-stores_plot.png')
    plt.show()
def main():
    output_dir = 'output'
    df = collect_data(output_dir)
    plot_data(df)

if __name__ == "__main__":
    main()
