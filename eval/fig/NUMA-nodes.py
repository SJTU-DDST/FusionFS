import os
import re
import numpy as np
import matplotlib.pyplot as plt

data_dir = '../data'
numa_pattern = re.compile(r'NUMA-nodes-(\d+)-sockets')
file_pattern = re.compile(r'pm-array:odinfs:rand-write-file-size-(\d+[KMG]):bufferedio.dat')

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

def collect_data():
    data = {}
    for root, _, files in os.walk(data_dir):
        match = numa_pattern.search(root)
        if match:
            sockets = int(match.group(1))
            if sockets not in data:
                data[sockets] = []
            for file in files:
                file_match = file_pattern.match(file)
                if file_match:
                    size_str = file_match.group(1)
                    file_size = get_file_size_in_mb(size_str)
                    filepath = os.path.join(root, file)
                    bandwidth = parse_file(filepath)
                    if bandwidth is not None:
                        data[sockets].append((file_size, bandwidth))
    return data

def plot_data(data):
    plt.figure(figsize=(4, 3), layout="constrained")
    
    # 排序sockets数量
    sorted_sockets = sorted(data.keys())
    
    for sockets in sorted_sockets:
        points = sorted(data[sockets], key=lambda x: x[0])  # 按文件大小排序
        x = [point[0] for point in points]  # 文件大小（MB）
        y = [point[1] / 1024 for point in points]  # PM 写带宽
        if sockets == 1:
            label = '1 socket'
        else:
            label = f'{sockets} sockets'
        plt.plot(x, y, label=label, marker='o')
    
    plt.xlabel('File Size (MB)')
    plt.ylabel('PM Writes (GB)')
    # plt.title('File Size vs PM Write Bandwidth for Different Sockets')
    plt.legend()
    plt.grid(True)
    
    # 设置xticks
    unique_file_sizes = sorted(set(x for points in data.values() for x, _ in points))
    plt.xticks(unique_file_sizes, [f'{int(size)}' for size in unique_file_sizes])
    
    # plt.show()
    plt.savefig("NUMA-nodes.png")

# 收集数据
data = collect_data()

# 绘制数据
plot_data(data)