import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import re

order = ['ext4', 'pmfs', 'nova', 'winefs', 'odinfs', 'FusionFS']

old_fontsize = plt.rcParams['font.size']
plt.rcParams['font.size'] = old_fontsize * 1.1

c = np.array([[102, 194, 165], [252, 141, 98], [141, 160, 203], 
        [231, 138, 195], [166,216,84], [255, 217, 47],
        [229, 196, 148], [179, 179, 179]])
c  = c/255

# 创建子图
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10, 3))

data_dir = '../data/filebench'

filesystems = {
    "pmem-local:ext4": "ext4",
    "pmfs": "PMFS",
    "nova": "NOVA",
    "winefs": "WineFS",
    "dm-stripe:ext4": "ext4(RAID0)",
    "pm-array:odinfs": "ODINFS",
    "FusionFS": "FusionFS"
}

labels = {
    "ext4": "ext4",
    "pmfs": "PMFS",
    "nova": "NOVA",
    "winefs": "WineFS",
    "odinfs": "ODINFS",
    "FusionFS": "FusionFS"
}

# hat = ['|//','-\\\\','|\\\\','-//',"--","\\\\",'//',"xx"]
markers = ['H', '^', '>', 'D', 'o', 's', 'p', 'x']

i = 0
fusionfs_data = None
other_data = []
for fs, label in filesystems.items():
    if fs == "dm-stripe:ext4":
        continue
    pattern = re.compile(f"{fs}:filebench_oltp:bufferedio.dat")
    for root, _, files in os.walk(data_dir):
        for file in files:
            if pattern.search(file):
                filepath = os.path.join(root, file)
                data = np.loadtxt(filepath, usecols=(0, 1))
                ax1.plot(data[:, 0], data[:, 1] / 1000000, label=label, marker=markers[i], color=c[i], lw=3, mec='black', markersize=8, alpha=1)
                if label == "FusionFS":
                    fusionfs_data = data
                else:
                    other_data.append((label, data))
    i = i + 1

if fusionfs_data is not None:
    max_outperform = {}
    sum_outperform = {}
    for thread_count in fusionfs_data[:, 0]:
        fusionfs_value = fusionfs_data[fusionfs_data[:, 0] == thread_count][0, 1]
        max_ratio = 0
        for label, other in other_data:
            other_value = other[other[:, 0] == thread_count][0, 1]
            ratio = fusionfs_value / other_value
            if ratio > max_ratio:
                max_ratio = ratio
            # print(f"FusionFS vs {label} at thread count {thread_count}: {ratio:.2f}x")
            sum_outperform[label] = sum_outperform.get(label, 0) + ratio
        max_outperform[thread_count] = max_ratio
    
    for label, other in other_data:
        avg_ratio = sum_outperform[label] / len(fusionfs_data[:, 0])
        print(f"Average FusionFS vs {label}: {avg_ratio:.2f}x")
    
    print("FusionFS outperform ratios for OLTP:")
    for thread_count, ratio in max_outperform.items():
        print(f"Thread count {thread_count}: {ratio:.2f} times")

ax1.set_xlabel('# threads')
ax1.set_ylabel('Throughput (M ops/sec)')
ax1.set_title('(a) Filebench OLTP')
ax1.grid(axis='y', linestyle='-.')
ax1.set_xticks([1, 4, 8, 16, 28, 56])
ax1.legend(loc='upper center', bbox_to_anchor=(0.5, 1.6), ncol=2)


# 读取CSV文件
tpcc_data = pd.read_csv('/home/congyong/Odinfs/eval/data/tpcc/tpcc.csv', header=None, names=['FileSystem', 'Performance'])
kyoto_data = pd.read_csv('/home/congyong/Odinfs/eval/data/KyotoCabinet/KyotoCabinet.csv', header=None, names=['FileSystem', 'Performance'])
lmdb_data = pd.read_csv('/home/congyong/Odinfs/eval/data/lmdb/lmdb.csv', header=None, names=['FileSystem', 'Performance'])

# 获取性能数据
tpcc_performance = [tpcc_data[tpcc_data['FileSystem'] == fs]['Performance'].values[0] if fs in tpcc_data['FileSystem'].values else 0 for fs in order]
kyoto_performance = [kyoto_data[kyoto_data['FileSystem'] == fs]['Performance'].values[0] if fs in kyoto_data['FileSystem'].values else 0 for fs in order]
lmdb_performance = [lmdb_data[lmdb_data['FileSystem'] == fs]['Performance'].values[0] if fs in lmdb_data['FileSystem'].values else 0 for fs in order]



# x = np.arange(len(order))  # x 轴的位置
x1 = np.arange(1)  # x 轴的位置，1个负载
# width = 0.35  # 柱状图的宽度
width1 = 0.1  # 柱状图的宽度

# 左子图：TPCC
# ax2.bar(x, tpcc_performance, width, label='TPCC')
fusionfs_performance = None
other_performances = []

ax2.set_axisbelow(True)
for i, fs in enumerate(order):
    performance = tpcc_performance[i] / 1000
    ax2.bar(x1 + i * width1 - (len(order) / 2 - 0.5) * width1, [performance], width1, label=labels[fs], color=c[i], edgecolor='black', lw=1.2)
    if labels[fs] == 'FusionFS':
        fusionfs_performance = performance
    else:
        other_performances.append((labels[fs], performance))

# 计算 FusionFS 的 TPC-C 性能是其他文件系统多少倍
if fusionfs_performance is not None:
    outperform_ratios = {}
    for label, performance in other_performances:
        ratio = fusionfs_performance / performance
        outperform_ratios[label] = ratio
    
    print("FusionFS outperform ratios for TPC-C:")
    for label, ratio in outperform_ratios.items():
        print(f"{label}: {ratio:.2f} times")

# ax2.set_xlabel('File system')
ax2.set_ylabel('K transactions/sec')
ax2.set_title('(b) TPC-C on SQLite')
# ax2.set_xticks(x)
# ax2.set_xticklabels(order)
ax2.set_xticks(x1)
ax2.set_xticklabels(['TPC-C'])
ax2.grid(axis='y', linestyle='-.')
ax2.set_xlim(-0.8, 0.8)
# ax2.legend()
ax2.legend(loc='upper center', bbox_to_anchor=(0.5, 1.6), ncol=2)

# 右子图：KyotoCabinet 和 LMDB
x2 = np.arange(2)  # x 轴的位置，2个负载
width2 = 0.1  # 柱状图的宽度

ax3.set_axisbelow(True)
for i, fs in enumerate(order):
    ax3.bar(x2 + i * width2 - (len(order) / 2 - 0.5) * width2, [kyoto_performance[i] / 1000, lmdb_performance[i] / 1000], width2, label=labels[fs], color=c[i], edgecolor='black', lw=1.2)

# ax3.set_xlabel('Workload')
ax3.set_ylabel('Throughput (K ops/sec)')
ax3.set_title('(c) mmap applications')
ax3.set_xticks(x2)
ax3.set_xticklabels(['Kyoto Cabinet', 'LMDB'])
ax3.grid(axis='y', linestyle='-.')
# ax3.legend(title='File System')
ax3.legend(loc='upper center', bbox_to_anchor=(0.5, 1.6), ncol=2)

# 调整布局
plt.tight_layout()

# 显示图表
fig.subplots_adjust(top=0.8)
plt.savefig('application.png', bbox_inches='tight')
plt.savefig('application.pdf', bbox_inches='tight')
# plt.show()

# import pandas as pd
# import matplotlib.pyplot as plt

# order = ['ext4', 'pmfs', 'nova', 'winefs', 'odinfs', 'FusionFS']

# # 读取CSV文件
# tpcc_data = pd.read_csv('/home/congyong/Odinfs/eval/data/tpcc/tpcc.csv', header=None, names=['FileSystem', 'Performance'])
# kyoto_data = pd.read_csv('/home/congyong/Odinfs/eval/data/KyotoCabinet/KyotoCabinet.csv', header=None, names=['FileSystem', 'Performance'])
# lmdb_data = pd.read_csv('/home/congyong/Odinfs/eval/data/lmdb/lmdb.csv', header=None, names=['FileSystem', 'Performance'])
# # 创建柱状图
# fig, axs = plt.subplots(1, 3, figsize=(10, 3), layout='constrained')

# tpcc_performance = [tpcc_data[tpcc_data['FileSystem'] == fs]['Performance'].values[0] if fs in tpcc_data['FileSystem'].values else 0 for fs in order]
# axs[0].bar(order, tpcc_performance)
# axs[0].set_xlabel('File System')
# axs[0].set_ylabel('Throughput (ops/sec)')
# axs[0].set_title('TPCC Performance')
# axs[0].set_xticks(order)

# kyoto_performance = [kyoto_data[kyoto_data['FileSystem'] == fs]['Performance'].values[0] if fs in kyoto_data['FileSystem'].values else 0 for fs in order]
# axs[1].bar(order, kyoto_performance)
# axs[1].set_xlabel('File System')
# axs[1].set_ylabel('Throughput (ops/sec)')
# axs[1].set_title('KyotoCabinet Performance')
# axs[1].set_xticks(order)
# # plt.tight_layout()

# lmdb_performance = [lmdb_data[lmdb_data['FileSystem'] == fs]['Performance'].values[0] if fs in lmdb_data['FileSystem'].values else 0 for fs in order]
# axs[2].bar(order, lmdb_performance)
# axs[2].set_xlabel('File System')
# axs[2].set_ylabel('Throughput (ops/sec)')
# axs[2].set_title('LMDB Performance')
# axs[2].set_xticks(order)


# # 显示图表
# # plt.show()
# plt.savefig('application.png')

# # 如果需要保存图表，可以使用以下代码
# # plt.savefig('/path/to/save/kyotocabinet_performance.png')

# # IMPORTANT: 注意NOVA没打开atomic-mmap