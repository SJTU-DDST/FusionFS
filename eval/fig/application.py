import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import re

order = ['ext4', 'pmfs', 'nova', 'winefs', 'odinfs', 'FusionFS']

# 创建子图
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10, 3), layout='constrained')

data_dir = '../data/filebench'

filesystems = {
    "pmem-local:ext4": "ext4",
    "pmfs": "pmfs",
    "nova": "nova",
    "winefs": "winefs",
    "dm-stripe:ext4": "ext4(RAID0)",
    "pm-array:odinfs": "odinfs",
    "FusionFS": "FusionFS"
}

markers = ['H', '^', '>', 'D', 'o', 's', 'p', 'x']

i = 0
for fs, label in filesystems.items():
    if fs == "dm-stripe:ext4":
        continue
    pattern = re.compile(f"{fs}:filebench_oltp:bufferedio.dat")
    for root, _, files in os.walk(data_dir):
        for file in files:
            if pattern.search(file):
                filepath = os.path.join(root, file)
                data = np.loadtxt(filepath, usecols=(0, 1))
                ax1.plot(data[:, 0], data[:, 1] / 1000000, label=label, marker=markers[i])
    i = i + 1
ax1.set_xlabel('# threads')
ax1.set_ylabel('Throughput (M ops/sec)')
ax1.set_title('OLTP')
ax1.grid(True)
ax1.legend()


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
for i, fs in enumerate(order):
    ax2.bar(x1 + i * width1 - (len(order) / 2 - 0.5) * width1, [tpcc_performance[i]], width1, label=fs)

ax2.set_xlabel('File System')
ax2.set_ylabel('Throughput (ops/sec)')
ax2.set_title('TPCC Performance')
# ax2.set_xticks(x)
# ax2.set_xticklabels(order)
ax2.set_xticks(x1)
ax2.set_xticklabels(['TPCC'])
ax2.legend()

# 右子图：KyotoCabinet 和 LMDB
x2 = np.arange(2)  # x 轴的位置，2个负载
width2 = 0.1  # 柱状图的宽度

for i, fs in enumerate(order):
    ax3.bar(x2 + i * width2 - (len(order) / 2 - 0.5) * width2, [kyoto_performance[i], lmdb_performance[i]], width2, label=fs)

ax3.set_xlabel('Workload')
ax3.set_ylabel('Throughput (ops/sec)')
ax3.set_title('KyotoCabinet and LMDB Performance')
ax3.set_xticks(x2)
ax3.set_xticklabels(['KyotoCabinet', 'LMDB'])
ax3.legend(title='File System')

# 调整布局
# plt.tight_layout()

# 显示图表
plt.savefig('application.png')
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