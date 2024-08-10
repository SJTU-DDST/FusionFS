import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import re

old_fontsize = plt.rcParams['font.size']
plt.rcParams['font.size'] = old_fontsize * 1.1

# 定义颜色和柱子宽度
hat = ['|//','-\\\\','|\\\\','-//',"--","\\\\",'//',"xx"]
c = np.array([[102, 194, 165], [252, 141, 98], [141, 160, 203], 
              [231, 138, 195], [166, 216, 84], [255, 217, 47],
              [229, 196, 148], [179, 179, 179]])
c = c / 255
width = 0.15

# 文件系统和zipf分布
filesystems = ["ext4", "pmfs", "nova", "winefs", "odinfs", "FusionFS"]
labels = {
    "ext4": "ext4",
    "pmfs": "PMFS",
    "nova": "NOVA",
    "winefs": "WineFS",
    "odinfs": "ODINFS",
    "FusionFS": "FusionFS"
}
zipf_distributions = ["", "60-40", "70-30", "80-20", "90-10"]
data_dir = "../data/fio-vary-zipf"  # 修改为实际数据目录

# 初始化数据结构
throughput_data = {fs: {zipf: {} for zipf in zipf_distributions} for fs in filesystems}

iosizes = ["4K", "2M"]
rows = [0, 2]
cols = [1, 2, 5]

# 读取数据
for fs in filesystems:
    for zipf in zipf_distributions:
        for iosize in iosizes:
            for row in rows:
                for col in cols:
                    media = "pmem-local"
                    if fs == "FusionFS" or fs == "odinfs":
                        media = "pm-array"

                    if zipf == "":
                        pattern = re.compile(f"{media}:{fs}:rand-write-{iosize}:bufferedio.dat")
                    else:
                        pattern = re.compile(f"{media}:{fs}:rand-write-{iosize}-zipf-{zipf}:bufferedio.dat")
                    for root, _, files in os.walk(data_dir):
                        for file in files:
                            if pattern.search(file):
                                filepath = os.path.join(root, file)
                                data = pd.read_csv(filepath, sep='\s+', header=None, skiprows=1, on_bad_lines='skip')
                                data[0] = pd.to_numeric(data[0], errors='coerce')
                                data[col] = pd.to_numeric(data[col], errors='coerce')
                                data = data.dropna()

                                throughput = data[col][row] # / 1000000
                                if col == 1:
                                    throughput = throughput / 1024 / 1024 # GiB/s
                                if col == 5:
                                    MiB = data[1][row] / 1024 * 10 # we run for 10 seconds
                                    throughput = throughput / MiB
                                throughput_data[fs][zipf][(iosize, row, col)] = throughput

                                # print(fs, zipf, data[0][row], data[col][row])

# 绘制子图
fig, axs = plt.subplots(3, 4, figsize=(12, 7))
x = np.arange(len(filesystems))

for i, (iosize, row, col) in enumerate([("4K", rows[0], cols[0]), ("2M", rows[0], cols[0]), ("4K", rows[1], cols[0]), ("2M", rows[1], cols[0]),
                                        ("4K", rows[0], cols[1]), ("2M", rows[0], cols[1]), ("4K", rows[1], cols[1]), ("2M", rows[1], cols[1]),
                                        ("4K", rows[0], cols[2]), ("2M", rows[0], cols[2]), ("4K", rows[1], cols[2]), ("2M", rows[1], cols[2])]):
    ax = axs[i // 4, i % 4]
    for j, zipf in enumerate(zipf_distributions):
        y = [throughput_data[fs][zipf].get((iosize, row, col), 0) for fs in filesystems]
        ax.bar(x + j * width, y, width, label="50-50" if zipf == "" else zipf, color=c[j], edgecolor='black', lw=1.2, hatch=hat[j])
    if i // 4 == 0:
        ax.set_title(f'{iosize}, {"Single-thread" if row == 0 else "8 threads"}')
    if i // 4 == 2:
        ax.set_xticks(x + width * (len(zipf_distributions) - 1) / 2)
        ax.set_xticklabels(labels.values(), rotation=45)
    else: # no x-axis labels
        ax.set_xticks([])
    if i % 4 == 0:
        ax.set_ylabel('Throughput (GiB/s)' if col == 1 else 'Latency (μs)' if col == 2 else 'I/O amplification')
    # if i // 4 == 2:
    #     ax.set_xlabel('File System')
    # ax.legend()
    ax.grid(axis='y', linestyle='-.')

handles, labels = axs[0][0].get_legend_handles_labels()
fig.legend(handles, labels, loc=9, ncol=len(zipf_distributions), frameon=False)

# 调整布局
plt.tight_layout()
fig.subplots_adjust(top=0.9)
plt.savefig("fio-vary-zipf.pdf", bbox_inches='tight')
plt.show()

# import matplotlib.pyplot as plt
# import numpy as np
# import pandas as pd
# import os
# import re

# # 定义颜色和柱子宽度
# hat = ['|//','-\\\\','|\\\\','-//',"--","\\\\",'//',"xx"]
# c = np.array([[102, 194, 165], [252, 141, 98], [141, 160, 203], 
#               [231, 138, 195], [166, 216, 84], [255, 217, 47],
#               [229, 196, 148], [179, 179, 179]])
# c = c / 255
# width = 0.15

# # 文件系统和zipf分布
# filesystems = ["ext4", "pmfs", "nova", "winefs", "odinfs", "FusionFS"]
# zipf_distributions = ["", "60-40", "70-30", "80-20", "90-10"]
# data_dir = "../data/fio-vary-zipf"  # 修改为实际数据目录
# # data_dir_fio = "../data/fio"

# # 初始化数据结构
# throughput_data = {fs: [] for fs in filesystems}

# # 读取数据
# for fs in filesystems:
#     for zipf in zipf_distributions:
#         media = "pmem-local"
#         if fs == "FusionFS" or fs == "odinfs":
#             media = "pm-array"

#         iosize = "4K" # "2M"

#         if zipf == "":
#             pattern = re.compile(f"{media}:{fs}:rand-write-{iosize}:bufferedio.dat")
#         else:
#             pattern = re.compile(f"{media}:{fs}:rand-write-{iosize}-zipf-{zipf}:bufferedio.dat")
#         for root, _, files in os.walk(data_dir):
#             for file in files:
#                 if pattern.search(file):
#                     filepath = os.path.join(root, file)
#                     data = pd.read_csv(filepath, sep='\s+', header=None, skiprows=1, on_bad_lines='skip')
#                     data[0] = pd.to_numeric(data[0], errors='coerce')
#                     data[1] = pd.to_numeric(data[1], errors='coerce')
#                     data = data.dropna()

#                     row = 0 # 0=single thread, 3=8 threads
#                     col = 1 # 1=thrp, 2=lat, 5=pm writes # TODO: pm writes->amp rate

#                     print(fs, zipf, data[0][row], data[col][row])
#                     # throughput = np.mean(data[1]) / 1000000  # 转换为M ops/sec
#                     throughput = data[col][row] / 1000000
#                     throughput_data[fs].append(throughput)

# # 绘制柱状图
# fig, ax = plt.subplots(figsize=(10, 6))
# x = np.arange(len(filesystems))

# for i, zipf in enumerate(zipf_distributions):
#     y = [throughput_data[fs][i] for fs in filesystems]
#     ax.bar(x + i * width, y, width, label=f'zipf-{zipf}', color=c[i], edgecolor='black', lw=1.2, hatch=hat[i])

# # 设置标签和标题
# ax.set_xlabel('File System')
# ax.set_ylabel('Throughput (M ops/sec)')
# ax.set_title('Single-threaded 4K Write Throughput with Different Zipf Distributions')
# ax.set_xticks(x + width * (len(zipf_distributions) - 1) / 2)
# ax.set_xticklabels(filesystems)
# ax.legend()

# # 显示网格
# ax.grid(axis='y', linestyle='-.')

# # 显示图形
# plt.tight_layout()
# plt.savefig("fio-vary-zipf.pdf", bbox_inches='tight')
# plt.show()