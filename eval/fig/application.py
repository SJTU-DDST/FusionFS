import pandas as pd
import matplotlib.pyplot as plt

order = ['ext', 'pmfs', 'nova', 'winefs', 'odinfs', 'FusionFS']

# 读取CSV文件
kyoto_data = pd.read_csv('/home/congyong/Odinfs/eval/data/KyotoCabinet/KyotoCabinet.csv', header=None, names=['FileSystem', 'Performance'])
lmdb_data = pd.read_csv('/home/congyong/Odinfs/eval/data/lmdb/lmdb.csv', header=None, names=['FileSystem', 'Performance'])
# 创建柱状图
fig, axs = plt.subplots(1, 2, figsize=(8, 3), layout='constrained')

kyoto_performance = [kyoto_data[kyoto_data['FileSystem'] == fs]['Performance'].values[0] if fs in kyoto_data['FileSystem'].values else 0 for fs in order]
axs[0].bar(order, kyoto_performance)
axs[0].set_xlabel('File System')
axs[0].set_ylabel('Throughput (ops/sec)')
axs[0].set_title('KyotoCabinet Performance')
axs[0].set_xticks(order)
# plt.tight_layout()

lmdb_performance = [lmdb_data[lmdb_data['FileSystem'] == fs]['Performance'].values[0] if fs in lmdb_data['FileSystem'].values else 0 for fs in order]
axs[1].bar(order, lmdb_performance)
axs[1].set_xlabel('File System')
axs[1].set_ylabel('Throughput (ops/sec)')
axs[1].set_title('LMDB Performance')
axs[1].set_xticks(order)


# 显示图表
# plt.show()
plt.savefig('application.png')

# 如果需要保存图表，可以使用以下代码
# plt.savefig('/path/to/save/kyotocabinet_performance.png')

# IMPORTANT: 注意NOVA没打开atomic-mmap