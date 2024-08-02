import lmdb
import time
import argparse
import csv

def run_lmdb_test(env_path, duration=30):
    env = lmdb.open(env_path, map_size=10**9, writemap=True, sync=True, metasync=True)
    
    start_time = time.time()
    end_time = start_time + duration
    num_records = 0
    while time.time() < end_time:
        for i in range(100):
            key = str(num_records % 100000).zfill(8)
            value = "x" * 1024
            txn = env.begin(write=True)
            # txn.put(f'key{num_records}'.encode(), f'value{num_records}'.encode())
            txn.put(key.encode(), value.encode())
            txn.commit()
            num_records += 1
    elapsed_time = time.time() - start_time
    env.close()
    ops_per_sec = num_records / elapsed_time
    return ops_per_sec

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
    parser = argparse.ArgumentParser(description='Run KyotoCabinet benchmark.')
    parser.add_argument('fs_name', type=str, help='File system name')
    args = parser.parse_args()
    # db_path = "/tmp/lmdb_test"
    db_path = "/home/congyong/Odinfs/eval/benchmark/fxmark/bin/root/lmdb_test"
    ops_per_sec = run_lmdb_test(db_path)
# 在不同文件系统上运行测试

# print(f"Running test on file system")
# run_lmdb_test(f'/tmp/lmdb_test')

    if ops_per_sec is not None:
        update_csv(args.fs_name, ops_per_sec, '/home/congyong/Odinfs/eval/data/lmdb/lmdb.csv')
        print(f"File system: {args.fs_name}")
        print(f"Operations per second: {ops_per_sec:.2f} ops/sec")