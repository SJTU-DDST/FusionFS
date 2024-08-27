import os
import re
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint

old_fontsize = plt.rcParams['font.size']
plt.rcParams['font.size'] = old_fontsize * 1.1

# Threshold 图的参数
c = np.array([[102, 194, 165], [252, 141, 98], [141, 160, 203], 
        [231, 138, 195], [166,216,84], [255, 217, 47],
        [229, 196, 148], [179, 179, 179]])
c  = c/255
threshold_markers = ['H', '^', '>', 'D', 'o', 's', 'p', 'x']
threshold_data_dir = '../data/threshold'
threshold_labels = {
    "active-flush": "active-flush",
    "non-temporal": "non-temporal",
    "place-hot": "in-place hit",
    "place-cold": "in-place miss",
    "dedicated-cache": "dedicated"
}

# Fig9 图的参数
fig9_data_dir = '../data'
fig9_labels = ['4', '8', '12', '16', '20']
# fig9_linestyles = ['-', '--', '-.', ':', '-']
# fig9_markers = ['o', '^', 's', 'D', 'x']

fig9_files = [
    'odinfs-4-threads/pm-array:odinfs:seq-write-4K-hot:bufferedio.dat',
    'odinfs-8-threads/pm-array:odinfs:seq-write-4K-hot:bufferedio.dat',
    'fio/pm-array:odinfs:seq-write-4K-hot:bufferedio.dat',
    'odinfs-16-threads/pm-array:odinfs:seq-write-4K-hot:bufferedio.dat',
    'odinfs-20-threads/pm-array:odinfs:seq-write-4K-hot:bufferedio.dat'
]

# NUMA-nodes 图的参数
numa_data_dir = '../data'
numa_pattern = re.compile(r'NUMA-nodes-(\d+)-sockets')
numa_file_pattern = re.compile(r'pm-array:odinfs:rand-write-file-size-(\d+[KMG]):bufferedio.dat')

def get_file_size_in_mb(size_str):
    size_str = size_str.upper()
    if size_str.endswith('K'):
        return int(size_str[:-1]) / 1024
    elif size_str.endswith('M'):
        return int(size_str[:-1])
    elif size_str.endswith('G'):
        return int(size_str[:-1]) * 1024
    else:
        return int(size_str) / (1024 * 1024)

def parse_file(filepath):
    with open(filepath, 'r') as file:
        lines = file.readlines()
        if len(lines) > 1:
            bandwidth = float(lines[1].split()[-1])
            return bandwidth
    return None

def collect_threshold_data():
    data = {}
    for root, _, files in os.walk(threshold_data_dir):
        for file in files:
            if "2M" in file:
                continue
            filepath = os.path.join(root, file)
            update_mode, io_size, io_size_str = parse_filename(file)
            if update_mode and io_size:
                throughput = get_throughput(filepath)
                if throughput is not None:
                    if update_mode not in data:
                        data[update_mode] = []
                    data[update_mode].append((io_size, throughput, io_size_str))
    return data

def collect_fig9_data():
    data = {}
    for i, file in enumerate(fig9_files):
        data[fig9_labels[i]] = np.loadtxt(os.path.join(fig9_data_dir, file), usecols=(0, 1))
        data[fig9_labels[i]][:, 1] = data[fig9_labels[i]][:, 1] / (1024 * 1024)
        # for root, _, files in os.walk(fig9_data_dir):
        #     for file in files:
        #         if f'{label}-threads' in root:
        #             filepath = os.path.join(root, file)
        #             throughput = parse_file(filepath)
        #             if throughput is not None:
        #                 threads = int(label)
        #                 data[label].append((threads, throughput))

    return data

def collect_numa_data():
    data = {}
    for root, _, files in os.walk(numa_data_dir):
        match = numa_pattern.search(root)
        if match:
            sockets = int(match.group(1))
            if sockets not in data:
                data[sockets] = []
            for file in files:
                file_match = numa_file_pattern.match(file)
                if file_match:
                    size_str = file_match.group(1)
                    file_size = get_file_size_in_mb(size_str)
                    filepath = os.path.join(root, file)
                    bandwidth = parse_file(filepath)
                    if bandwidth is not None:
                        data[sockets].append((file_size, bandwidth))
    return data

def parse_filename(filename):
    match = re.match(r'.*-(\w+-\w+):threshold-\w+-(\d+[KMG]?)\.dat', filename)
    if match:
        update_mode = match.group(1)
        io_size_str = match.group(2)
        io_size = convert_size_to_bytes(io_size_str)
        return update_mode, io_size, io_size_str
    return None, None, None

def convert_size_to_bytes(size_str):
    size_str = size_str.upper()
    if size_str.endswith('K'):
        return int(size_str[:-1]) * 1024
    elif size_str.endswith('M'):
        return int(size_str[:-1]) * 1024 * 1024
    elif size_str.endswith('G'):
        return int(size_str[:-1]) * 1024 * 1024 * 1024
    else:
        return int(size_str)

def get_throughput(filepath):
    with open(filepath, 'r') as file:
        lines = file.readlines()
        if len(lines) > 1:
            return float(lines[1].split()[1])
    return None

def plot_threshold(ax, data):
    i = 0
    for update_mode in threshold_labels.keys():
        if update_mode in data:
            points = sorted(data[update_mode], key=lambda x: x[0])
            x = [point[2].replace('K', '') for point in points]
            y = [point[1] / 1024 / 1024 for point in points]
            ax.plot(x, y, label=threshold_labels[update_mode], marker=threshold_markers[i], color=c[i], lw=3, mec='black', markersize=8, alpha=1)
            i += 1
    ax.set_xlabel('I/O size (KB)')
    ax.set_ylabel('Throughput (GiB/s)')
    # ax.legend()
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.6), ncol=2)
    ax.grid(axis='y', linestyle='-.')
    ax.set_title('(a) 4K uniform rand write')

def plot_fig9(ax, data):
    for label in fig9_labels:
        if label in data:
            points = sorted(data[label], key=lambda x: x[0])
            x = [point[0] for point in points]
            y = [point[1] for point in points]
            ax.plot(x, y, label=label + " threads", marker=threshold_markers[fig9_labels.index(label)], color=c[fig9_labels.index(label)], lw=3, mec='black', markersize=8, alpha=1)
    ax.set_xlabel('# threads')
    ax.set_ylabel('Throughput (GiB/s)')
    # ax.legend(ncol=2)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.6), ncol=2)
    ax.grid(axis='y', linestyle='-.')
    ax.set_xticks([1, 4, 8, 16, 28, 56])
    ax.set_title('(b) 4K hot write')

def plot_numa(ax, data):
    sorted_sockets = sorted(data.keys())
    for sockets in sorted_sockets:
        points = sorted(data[sockets], key=lambda x: x[0])
        x = [point[0] for point in points]
        # ax.set_xticks(x)
        y = [point[1] / 1024 for point in points]
        label = '1 socket' if sockets == 1 else f'{sockets} sockets'
        ax.plot(x, y, label=label, marker=threshold_markers[sorted_sockets.index(sockets)], color=c[sorted_sockets.index(sockets)], lw=3, mec='black', markersize=8, alpha=1)
    ax.set_xlabel('File size (MB)')
    ax.set_ylabel('PM writes (GB)')
    # ax.legend()
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.35), ncol=2)
    ax.grid(axis='y', linestyle='-.')
    ax.set_xticks([8, 16, 24, 32, 40])
    ax.set_title('(c) 4K uniform rand write')

# 收集数据
threshold_data = collect_threshold_data()
fig9_data = collect_fig9_data()
numa_data = collect_numa_data()

# 创建图形和子图
fig, axs = plt.subplots(1, 3, figsize=(10, 3))

# 绘制每个子图
plot_threshold(axs[0], threshold_data)
plot_fig9(axs[1], fig9_data)
plot_numa(axs[2], numa_data)

# 调整布局并保存图形
plt.tight_layout()
fig.subplots_adjust(top=0.8)
plt.savefig("sensitivity.png", bbox_inches='tight')
plt.savefig("sensitivity.pdf", bbox_inches='tight')
plt.show()