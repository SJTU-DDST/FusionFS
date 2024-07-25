import os
import re
import numpy as np
import matplotlib.pyplot as plt

# 数据目录
data_dir = '../data/filebench'

# 定义文件系统和对应的颜色/线型/标记
filesystems = {
    "pmem-local:ext4": "ext",
    "pmfs": "pmfs",
    "nova": "nova",
    "winefs": "winefs",
    "dm-stripe:ext4": "ext4(RAID0)",
    "pm-array:odinfs": "odinfs",
    "FusionFS": "FusionFS"
}

markers = ['H', '^', '>', 'D', 'o', 's', 'p', 'x']

# 定义子图的名称
# subplots = ['fileserver', 'webserver', 'oltp', 'varmail']

# 初始化子图
# fig, axs = plt.subplots(2, 2, figsize=(8, 6))
# axs = axs.flatten()

# # 解析数据文件并绘制子图
# for i, subplot in enumerate(subplots):
#     # print(i, subplots[i])
#     ax = axs[i]

#     i = 0
#     for fs, label in filesystems.items():
#         pattern = re.compile(f"{fs}:filebench_{subplot}:bufferedio.dat")
#         for root, _, files in os.walk(data_dir):
#             for file in files:
#                 if pattern.search(file):
#                     filepath = os.path.join(root, file)
#                     data = np.loadtxt(filepath, usecols=(0, 1))
#                     ax.plot(data[:, 0], data[:, 1], label=label, marker=markers[i])
#         i = i + 1

#     ax.set_title(f'({chr(97 + i)}) {subplot.capitalize()}')
#     if i % 2 == 0:
#         ax.set_ylabel('Throughput (ops/sec)')
#     if i >= 2:
#         ax.set_xlabel('# threads')
#     ax.grid(True)
#     ax.legend()

plt.figure(figsize=(4, 3), layout="constrained")
i = 0
for fs, label in filesystems.items():
    pattern = re.compile(f"{fs}:filebench_oltp:bufferedio.dat")
    for root, _, files in os.walk(data_dir):
        for file in files:
            if pattern.search(file):
                filepath = os.path.join(root, file)
                data = np.loadtxt(filepath, usecols=(0, 1))
                plt.plot(data[:, 0], data[:, 1] / 1000000, label=label, marker=markers[i])
    i = i + 1
plt.xlabel('# threads')
plt.ylabel('Throughput (M ops/sec)')
plt.legend()
plt.grid(True)

# 调整布局并保存图形
# fig.tight_layout()
plt.savefig("fig12.png")
plt.savefig("fig12.pdf")
# plt.show()