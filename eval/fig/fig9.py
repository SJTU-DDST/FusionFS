import os
import numpy as np
import matplotlib.pyplot as plt

# 数据目录
data_dir = '../data'

# 图例和线型
labels = ['4', '8', '12', '16', '20']
linestyles = ['-', '--', '-.', ':', '-']
markers = ['o', '^', 's', 'D', 'x']

def load_data(file_path):
    """
    从文件中加载数据并转换吞吐量为 GiB/s
    """
    data = np.loadtxt(file_path, usecols=(0, 1))
    data[:, 1] = data[:, 1] / (1024 * 1024)  # 转换为 GiB/s
    return data

def plot_subplot(ax, title, files, xlabel=None, ylabel=None):
    """
    绘制子图
    """
    for i, file in enumerate(files):
        data = load_data(os.path.join(data_dir, file))
        ax.plot(data[:, 0], data[:, 1], label=labels[i]+" threads", linestyle=linestyles[i], marker=markers[i])
    
    # ax.title(title)
    if xlabel:
        ax.xlabel(xlabel)
    if ylabel:
        ax.ylabel(ylabel)
    ax.grid(True)
    ax.legend()

# 创建图形和子图
plt.figure(figsize=(4, 3), layout="constrained")

# 绘制 4K 写
plot_subplot(plt, '(b) 4K write', [
    'odinfs-4-threads/pm-array:odinfs:seq-write-4K-hot:bufferedio.dat',
    'odinfs-8-threads/pm-array:odinfs:seq-write-4K-hot:bufferedio.dat',
    'fio/pm-array:odinfs:seq-write-4K-hot:bufferedio.dat',
    'odinfs-16-threads/pm-array:odinfs:seq-write-4K-hot:bufferedio.dat',
    'odinfs-20-threads/pm-array:odinfs:seq-write-4K-hot:bufferedio.dat'
], xlabel="# threads", ylabel="Throughput (GiB/s)")

# 调整布局并保存图形
# plt.tight_layout()
plt.savefig("fig9.png")
# plt.show()