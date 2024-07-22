import os
import re
import numpy as np
import matplotlib.pyplot as plt

markers = ['H', '^', '>', 'D', 'o', 's', 'p', 'x']
data_dir = '../data/threshold'

labels = {
    "active-flush": "active-flush",
    "non-temporal": "non-temporal",
    "place-hot": "in-place (hit)",
    "place-cold": "in-place (miss)",
    "dedicated-cache": "dedicated-cache"
}

def parse_filename(filename):
    """
    从文件名中提取更新方式和 I/O size。
    """
    match = re.match(r'.*-(\w+-\w+):threshold-\w+-(\d+[KMG]?)\.dat', filename)
    if match:
        update_mode = match.group(1)
        io_size_str = match.group(2)
        io_size = convert_size_to_bytes(io_size_str)
        return update_mode, io_size, io_size_str
    return None, None, None

def convert_size_to_bytes(size_str):
    """
    将 I/O size 字符串转换为字节数。
    """
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
    """
    从文件内容中提取吞吐量（第二列的第二行）。
    """
    with open(filepath, 'r') as file:
        lines = file.readlines()
        if len(lines) > 1:
            return float(lines[1].split()[1])
    return None

def plot_data(data):
    """
    绘制数据。
    """
    plt.figure(figsize=(5, 3), layout="constrained")
    
    i = 0
    for update_mode in labels.keys():
        if update_mode in data:
            points = sorted(data[update_mode], key=lambda x: x[0])  # 按 I/O size 排序
            x = [point[2] for point in points]  # 使用原始 I/O size 字符串作为标签
            y = [point[1] / 1024 / 1024 for point in points]
            plt.plot(x, y, label=labels[update_mode], marker=markers[i])
            i += 1
    
    plt.xlabel('I/O Size')
    plt.ylabel('Throughput (GiB/s)')
    plt.title('I/O Size vs Throughput for Different Update Modes')
    plt.legend()
    plt.grid(True)
    plt.savefig("threshold.png")

# 读取数据
data = {}

for root, _, files in os.walk(data_dir):
    for file in files:
        filepath = os.path.join(root, file)
        update_mode, io_size, io_size_str = parse_filename(file)
        if update_mode and io_size:
            throughput = get_throughput(filepath)
            if throughput is not None:
                if update_mode not in data:
                    data[update_mode] = []
                data[update_mode].append((io_size, throughput, io_size_str))

# 绘制数据
plot_data(data)