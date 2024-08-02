import subprocess
import argparse
import csv


def run_mobibench():
    # 运行命令并捕获输出
    result = subprocess.run(['sudo', '/home/congyong/Mobibench/shell/mobibench', '-p', '/home/congyong/Odinfs/eval/benchmark/fxmark/bin/root/', '-n', '10000', '-d', '1', '-a', '0', '-y', '1'], 
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # 检查命令是否成功执行
    if result.returncode != 0:
        print("命令执行失败:", result.stderr)
        return None

    for line in result.stdout.split('\n'):
        if line.startswith('[TIME]'):
            return float(line.split()[5])
    return 0

def update_csv(fs_name, ops_per_sec, csv_path):
    rows = []
    updated = False

    # 读取现有的CSV内容
    try:
        with open(csv_path, mode='r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == fs_name:
                    row[1] = ops_per_sec
                    updated = True
                rows.append(row)
    except FileNotFoundError:
        pass

    # 如果没有找到相同的文件系统名字，则追加新的记录
    if not updated:
        rows.append([fs_name, ops_per_sec])

    # 写回CSV文件
    with open(csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run SQLite benchmark.')
    parser.add_argument('fs_name', type=str, help='File system name')
    args = parser.parse_args()

    transactions_per_sec = run_mobibench()
    if transactions_per_sec:
        update_csv(args.fs_name, transactions_per_sec, '/home/congyong/Odinfs/eval/data/lmdb/lmdb.csv')
        print(f"File system: {args.fs_name}")
        print("Transactions/sec:", transactions_per_sec)