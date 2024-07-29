import pandas as pd
import matplotlib.pyplot as plt

# 读取CSV文件
file_path = '/home/congyong/Odinfs/eval/data/KyotoCabinet/KyotoCabinet.csv'
data = pd.read_csv(file_path, header=None, names=['FileSystem', 'Performance'])

# 创建柱状图
plt.figure(figsize=(4, 3), layout='constrained')
plt.bar(data['FileSystem'], data['Performance'], color='skyblue')
plt.xlabel('File System')
plt.ylabel('Throughput (ops/sec)')
plt.title('KyotoCabinet Performance')
plt.xticks(rotation=45)
# plt.tight_layout()

# 显示图表
# plt.show()
plt.savefig('KyotoCabinet.png')

# 如果需要保存图表，可以使用以下代码
# plt.savefig('/path/to/save/kyotocabinet_performance.png')

# IMPORTANT: 注意NOVA没打开atomic-mmap