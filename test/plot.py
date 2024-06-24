import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Load data from CSV
data = pd.read_csv('data.csv')

# Function to plot latency with better distinction
def plot_latency(data):
    plt.figure(figsize=(12, 6))
    bars = plt.bar(data['Program'], data['TimeElapsed(s)'], color='blue')
    plt.xlabel('Program')
    plt.ylabel('Time Elapsed (s)')
    plt.title('Latency Comparison')
    plt.ylim(9.98, 10.03)  # Adjust y-axis for better visibility
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    # Add numbers on the bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 5), va='bottom')  # va: vertical alignment
    
    plt.show()

# Function to plot throughput
def plot_throughput(data):
    total_reads = data[['Reader0', 'Reader1', 'Reader2', 'Reader3', 'Reader4', 'Reader5', 'Reader6', 'Reader7', 'Reader8', 'Reader9']].sum(axis=1)
    total_writes = data[['Writer0', 'Writer1']].sum(axis=1)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    bar_width = 0.35
    index = np.arange(len(data['Program']))
    
    bars1 = ax.bar(index, total_reads, bar_width, label='Total Reads', color='green')
    bars2 = ax.bar(index + bar_width, total_writes, bar_width, label='Total Writes', color='red')
    
    ax.set_xlabel('Program')
    ax.set_ylabel('Count')
    ax.set_title('Throughput Comparison')
    ax.set_xticks(index + bar_width / 2)
    ax.set_xticklabels(data['Program'])
    ax.legend()
    
    # Add numbers on the bars
    for bars in [bars1, bars2]:
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval, int(yval), va='bottom')  # va: vertical alignment
    
    plt.show()

def plot_throughput_write(data):
    total_writes = data[['Writer0', 'Writer1']].sum(axis=1)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    bar_width = 0.35
    index = np.arange(len(data['Program']))
    
    bars = ax.bar(index + bar_width, total_writes, bar_width, label='Total Writes', color='red')
    
    ax.set_xlabel('Program')
    ax.set_ylabel('Count')
    ax.set_title('Writer Throughput Comparison')
    ax.set_xticks(index + bar_width / 2)
    ax.set_xticklabels(data['Program'])
    ax.legend()
    
    # Add numbers on the bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, int(yval), va='bottom')  # va: vertical alignment
    
    plt.show()

# Call functions to plot data
plot_latency(data)
plot_throughput(data)
plot_throughput_write(data)
