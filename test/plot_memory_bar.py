import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

num_methods = 7
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
        'L1-dcache-store-misses': 0,
        'L1-dcache-load-misses': 0,
        'LLC-load-misses': 0,
        'LLC-store-misses': 0
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
    print("dir: ", output_dir)
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
    df = df.sort_values(by=['num_readers', 'executable'])
    bar_width = 0.2
    gap = bar_width * len(df['num_readers'].unique())
    positions = np.arange(len(df['executable'].unique())) * gap * 1.5
    colors = plt.cm.get_cmap('tab10', num_methods)
    
    def add_labels(bars):
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, yval + yval * 0.01, int(yval), ha='center', va='bottom', fontsize=8)
    

    # Plot memory usage (cache misses) for each executable
    plt.figure(figsize=(14, 8))
    for i, num_readers in enumerate(df['num_readers'].unique()):
        subset_df = df[df['num_readers'] == num_readers]
        bars = plt.bar(positions + bar_width*i, subset_df['cache-misses'], width=bar_width, label=f'{num_readers} Readers',color=colors(range(num_methods)))
        add_labels(bars)
        
    plt.xlabel('Methods')
    plt.ylabel('Cache Misses')
    plt.title('Cache Misses vs. Methods')
    plt.xticks(positions + bar_width*(len(df['num_readers'].unique())/2), df['executable'].unique())
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('cache_misses_bar.png')
    plt.show()

    # Plot L1-dcache-store-misses for each executable
    plt.figure(figsize=(14, 8))
    for i, num_readers in enumerate(df['num_readers'].unique()):
        subset_df = df[df['num_readers'] == num_readers]
        bars = plt.bar(positions + bar_width*i, subset_df['L1-dcache-store-misses'], width=bar_width, label=f'{num_readers} Readers',color=colors(range(num_methods)))
        add_labels(bars)
        
    plt.xlabel('Methods')
    plt.ylabel('L1 Dcache Store Misses')
    plt.title('L1 Dcache Store Misses vs. Methods')
    plt.xticks(positions + bar_width*(len(df['num_readers'].unique())/2), df['executable'].unique())
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('l1_dcache_store_misses_bar.png')
    plt.show()

    # Plot L1-dcache-load-misses for each executable
    plt.figure(figsize=(14, 8))
    for i, num_readers in enumerate(df['num_readers'].unique()):
        subset_df = df[df['num_readers'] == num_readers]
        bars = plt.bar(positions + bar_width*i, subset_df['L1-dcache-load-misses'], width=bar_width, label=f'{num_readers} Readers',color=colors(range(num_methods)))
        add_labels(bars)
        
    plt.xlabel('Methods')
    plt.ylabel('L1 Dcache Load Misses')
    plt.title('L1 Dcache Load Misses vs. Methods')
    plt.xticks(positions + bar_width*(len(df['num_readers'].unique())/2), df['executable'].unique())
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('l1_dcache_load_misses_bar.png')
    plt.show()

    # Plot LLC load misses for each executable
    plt.figure(figsize=(14, 8))
    for i, num_readers in enumerate(df['num_readers'].unique()):
        subset_df = df[df['num_readers'] == num_readers]
        bars = plt.bar(positions + bar_width*i, subset_df['LLC-load-misses'], width=bar_width, label=f'{num_readers} Readers',color=colors(range(num_methods)))
        add_labels(bars)
        
    plt.xlabel('Methods')
    plt.ylabel('LLC Load Misses')
    plt.title('LLC Load Misses vs. Methods')
    plt.xticks(positions + bar_width*(len(df['num_readers'].unique())/2), df['executable'].unique())
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('llc_load_misses_bar.png')
    plt.show()

    # Plot LLC store misses for each executable
    plt.figure(figsize=(14, 8))
    for i, num_readers in enumerate(df['num_readers'].unique()):
        subset_df = df[df['num_readers'] == num_readers]
        bars = plt.bar(positions + bar_width*i, subset_df['LLC-store-misses'], width=bar_width, label=f'{num_readers} Readers',color=colors(range(num_methods)))
        add_labels(bars)
        
    plt.xlabel('Methods')
    plt.ylabel('LLC Store Misses')
    plt.title('LLC Store Misses vs. Methods')
    plt.xticks(positions + bar_width*(len(df['num_readers'].unique())/2), df['executable'].unique())
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('llc_store_misses_bar.png')
    plt.show()

    plt.figure(figsize=(14, 8))
    for i, num_readers in enumerate(df['num_readers'].unique()):
        subset_df = df[df['num_readers'] == num_readers]
        bars = plt.bar(positions + bar_width*i, subset_df['L1-dcache-stores'], width=bar_width, label=f'{num_readers} Readers',color=colors(range(num_methods)))
        add_labels(bars)
        
    plt.xlabel('Methods')
    plt.ylabel('L1-dcache-stores')
    plt.title('L1 Dcache  Stores vs. Methods')
    plt.xticks(positions + bar_width*(len(df['num_readers'].unique())/2), df['executable'].unique())
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('L1-dcache-stores.png')
    plt.show()

    plt.figure(figsize=(14, 8))
    for i, num_readers in enumerate(df['num_readers'].unique()):
        subset_df = df[df['num_readers'] == num_readers]
        bars = plt.bar(positions + bar_width*i, subset_df['L1-dcache-loads'], width=bar_width, label=f'{num_readers} Readers',color=colors(range(num_methods)))
        add_labels(bars)
        
    plt.xlabel('Methods')
    plt.ylabel('L1-dcache-loads')
    plt.title('L1 Dcache  Loads vs. Methods')
    plt.xticks(positions + bar_width*(len(df['num_readers'].unique())/2), df['executable'].unique())
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('L1-dcache-loads.png')
    plt.show()

def main():
    output_dir = 'output'
    df = collect_data(output_dir)
    plot_data(df)

if __name__ == "__main__":
    main()
