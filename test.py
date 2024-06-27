import re

# 步骤1: 打开并读取文件
with open('log.txt', 'r') as file:
    content = file.readlines()

# 步骤2: 使用正则表达式匹配
pattern = re.compile(r'phys=([0-9a-f]+)')

# 步骤3: 存储匹配到的数字
phys_addresses = set()
for line in content:
    match = pattern.search(line)
    if match:
        phys_addresses.add(int(match.group(1), 16))
        # convert hex string to int
        # print(int(match.group(1), 16))

# 步骤4: 转换为列表并排序
sorted_addresses = sorted(phys_addresses)

# 步骤5: 打印结果
print(sorted_addresses)

for i, addr in enumerate(sorted_addresses):
    # print(f'{i + 1}: {addr}')
    if i >= 1 and sorted_addresses[i] != sorted_addresses[i - 1] + 4096:
        # print(f'连续的物理地址中断于: {sorted_addresses[i - 1]}')
        # print(f'连续的物理地址开始于: {sorted_addresses[i]}')
        # break
        print(f'i={i}处不连续，addr={addr}，前一个是{sorted_addresses[i - 1]}，差值是{addr - sorted_addresses[i - 1]}')