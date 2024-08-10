import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

c = np.array([[102, 194, 165], [252, 141, 98], [141, 160, 203], 
        [231, 138, 195], [166,216,84], [255, 217, 47],
        [229, 196, 148], [179, 179, 179]])
c  = c/255
markers = ['H', '^', '>', 'D', 'o', 's', 'p', 'x']

old_fontsize = plt.rcParams['font.size']
plt.rcParams['font.size'] = old_fontsize * 1.1

# 定义绘图函数
def plot_data(ax, file_paths, labels, title, ylabel=None, xlabel=None, data_col=2): # 2: 50, 3: 99
    i = 0
    fusionfs_data = None
    other_data = []
    for file_path, label in zip(file_paths, labels):
        try:
            data = pd.read_csv(file_path, sep='\s+', header=None, skiprows=1, on_bad_lines='skip')
            data[0] = pd.to_numeric(data[0], errors='coerce')
            data[1] = pd.to_numeric(data[1], errors='coerce')
            data = data.dropna()
            ax.plot(data[0], data[data_col], label=label, marker=markers[i], color=c[i], lw=3, mec='black', markersize=8, alpha=1)
            if label == 'FusionFS':
                fusionfs_data = data
            else:
                other_data.append(data)
            # print(file_path)
            # print(data)
            # print(data[data_col])
        except pd.errors.ParserError as e:
            print(f"Error parsing {file_path}: {e}")
        i += 1
    
    if fusionfs_data is not None:
        max_outperform = {}
        max_underperform = {}
        for thread_count in fusionfs_data[0]:
            fusionfs_value = fusionfs_data[fusionfs_data[0] == thread_count][data_col].values[0]
            max_ratio = 0
            max_percentage = 0
            for other in other_data:
                other_value = other[other[0] == thread_count][data_col].values[0]
                ratio = fusionfs_value / other_value
                if ratio > max_ratio:
                    max_ratio = ratio
                percentage = ((other_value - fusionfs_value) / other_value) * 100
                if percentage > max_percentage:
                    max_percentage = percentage
            max_outperform[thread_count] = max_ratio
            max_underperform[thread_count] = max_percentage
        
        print("FusionFS outperform ratios for", title)
        for thread_count, ratio in max_outperform.items():
            print(f"Thread count {thread_count}: {ratio:.2f} times")
        
        print("FusionFS underperform percentages for", title)
        for thread_count, percentage in max_underperform.items():
            print(f"Thread count {thread_count}: {percentage:.2f}%")
    
    ax.set_title(title)
    if ylabel:
        ax.set_ylabel(ylabel)
    if xlabel:
        ax.set_xlabel(xlabel)
    ax.set_xticks([1, 4, 8, 16, 28, 56]) # no 2
    ax.grid(axis='y', linestyle='-.')
    # ax.legend()

# 文件路径和标签
file_paths_4k_read = [
    "../data/fio/pmem-local:ext4:seq-read-4K:bufferedio.dat",
    "../data/fio/pmem-local:pmfs:seq-read-4K:bufferedio.dat",
    "../data/fio/pmem-local:nova:seq-read-4K:bufferedio.dat",
    "../data/fio/pmem-local:winefs:seq-read-4K:bufferedio.dat",
    # "../data/fio/dm-stripe:ext4:seq-read-4K:bufferedio.dat",
    "../data/fio/pm-array:odinfs:seq-read-4K:bufferedio.dat",
    # "../data/fio/pm-array:FusionFS:seq-read-4K:bufferedio.dat"
]
labels_4k_read = ['ext4', 'PMFS', 'NOVA', 'WineFS', 'ODINFS', 'FusionFS']

file_paths_4k_write = [
    "../data/fio/pmem-local:ext4:seq-write-4K:bufferedio.dat",
    "../data/fio/pmem-local:pmfs:seq-write-4K:bufferedio.dat",
    "../data/fio/pmem-local:nova:seq-write-4K:bufferedio.dat",
    "../data/fio/pmem-local:winefs:seq-write-4K:bufferedio.dat",
    # "../data/fio/dm-stripe:ext4:seq-write-4K:bufferedio.dat",
    "../data/fio/pm-array:odinfs:seq-write-4K:bufferedio.dat",
    "../data/fio/pm-array:FusionFS:seq-write-4K:bufferedio.dat"
]
labels_4k_write = ['ext4', 'PMFS', 'NOVA', 'WineFS', 'ODINFS', 'FusionFS']

file_paths_4k_mmap = [
    "../data/fio/pmem-local:ext4:seq-write-4K-mmap-zipf:bufferedio.dat",
    "../data/fio/pmem-local:pmfs:seq-write-4K-mmap-zipf:bufferedio.dat",
    "../data/fio/pmem-local:nova:seq-write-4K-mmap-zipf:bufferedio.dat",
    "../data/fio/pmem-local:winefs:seq-write-4K-mmap-zipf:bufferedio.dat",
    # "../data/fio/dm-stripe:ext4:seq-write-4K-mmap-zipf:bufferedio.dat",
    "../data/fio/pm-array:odinfs:seq-write-4K-mmap-zipf:bufferedio.dat",
    "../data/fio/pm-array:FusionFS:seq-write-4K-mmap-zipf:bufferedio.dat"
]
labels_4k_mmap = ['ext4', 'PMFS', 'NOVA', 'WineFS', 'ODINFS', 'FusionFS']

# file_paths_2m_read = [
#     "../data/fio/pmem-local:ext4:seq-read-2M:bufferedio.dat",
#     "../data/fio/pmem-local:pmfs:seq-read-2M:bufferedio.dat",
#     "../data/fio/pmem-local:nova:seq-read-2M:bufferedio.dat",
#     "../data/fio/pmem-local:winefs:seq-read-2M:bufferedio.dat",
#     # "../data/fio/dm-stripe:ext4:seq-read-2M:bufferedio.dat",
#     "../data/fio/pm-array:odinfs:seq-read-2M:bufferedio.dat",
#     "../data/fio/pm-array:FusionFS:seq-read-2M:bufferedio.dat"
# ]
# labels_2m_read = ['ext4', 'PMFS', 'NOVA', 'WineFS', 'ODINFS', 'FusionFS']

file_paths_4k_zipf_write = [
    "../data/fio/pmem-local:ext4:seq-write-4K-zipf:bufferedio.dat",
    "../data/fio/pmem-local:pmfs:seq-write-4K-zipf:bufferedio.dat",
    "../data/fio/pmem-local:nova:seq-write-4K-zipf:bufferedio.dat",
    "../data/fio/pmem-local:winefs:seq-write-4K-zipf:bufferedio.dat",
    # "../data/fio/dm-stripe:ext4:seq-write-4K-zipf:bufferedio.dat",
    "../data/fio/pm-array:odinfs:seq-write-4K-zipf:bufferedio.dat",
    "../data/fio/pm-array:FusionFS:seq-write-4K-zipf:bufferedio.dat"
]
labels_4k_zipf_write = ['ext4', 'PMFS', 'NOVA', 'WineFS', 'ODINFS', 'FusionFS']

file_paths_2m_write = [
    "../data/fio/pmem-local:ext4:seq-write-2M:bufferedio.dat",
    "../data/fio/pmem-local:pmfs:seq-write-2M:bufferedio.dat",
    "../data/fio/pmem-local:nova:seq-write-2M:bufferedio.dat",
    "../data/fio/pmem-local:winefs:seq-write-2M:bufferedio.dat",
    # "../data/fio/dm-stripe:ext4:seq-write-2M:bufferedio.dat",
    "../data/fio/pm-array:odinfs:seq-write-2M:bufferedio.dat",
    "../data/fio/pm-array:FusionFS:seq-write-2M:bufferedio.dat"
]
labels_2m_write = ['ext4', 'PMFS', 'NOVA', 'WineFS', 'ODINFS', 'FusionFS']

file_paths_2m_zipf_write = [
    "../data/fio/pmem-local:ext4:seq-write-2M-zipf:bufferedio.dat",
    "../data/fio/pmem-local:pmfs:seq-write-2M-zipf:bufferedio.dat",
    "../data/fio/pmem-local:nova:seq-write-2M-zipf:bufferedio.dat",
    "../data/fio/pmem-local:winefs:seq-write-2M-zipf:bufferedio.dat",
    # "../data/fio/dm-stripe:ext4:seq-write-2M-zipf:bufferedio.dat",
    "../data/fio/pm-array:odinfs:seq-write-2M-zipf:bufferedio.dat",
    "../data/fio/pm-array:FusionFS:seq-write-2M-zipf:bufferedio.dat"
]

labels_2m_zipf_write = ['ext4', 'PMFS', 'NOVA', 'WineFS', 'ODINFS', 'FusionFS']

# 创建子图
fig, axs = plt.subplots(1, 4, figsize=(10, 3))

# 绘制4K写数据
plot_data(axs[0], file_paths_4k_write, labels_4k_write, '(a) 4K write-50%', ylabel='Latency (μs)', xlabel='# threads')
plot_data(axs[1], file_paths_4k_zipf_write, labels_4k_zipf_write, '(b) 4K zipf write-50%', xlabel='# threads')
plot_data(axs[2], file_paths_4k_write, labels_4k_write, '(c) 4K write-99%', xlabel='# threads', data_col=3)
plot_data(axs[3], file_paths_4k_zipf_write, labels_4k_zipf_write, '(d) 4K zipf write-99%', xlabel='# threads', data_col=3)

# plot_data(axs[2], file_paths_2m_write, labels_2m_write, '(c) 2M write', xlabel='# threads')

# plot_data(axs[3], file_paths_2m_zipf_write, labels_2m_zipf_write, '(d) 2M zipf write', xlabel='# threads')

handles, labels = axs[3].get_legend_handles_labels()
fig.legend(handles, labels, loc=9, ncol=len(labels_2m_zipf_write), frameon=False)


# 调整布局
plt.tight_layout()
fig.subplots_adjust(top=0.8)
plt.savefig("fio-latency.pdf", bbox_inches='tight')
plt.show()