import kyotocabinet as kc # sudo apt-get install -y python3-kyotocabinet
import time
import argparse
import csv
from tqdm import tqdm

def set_operation(db_path, duration=30):
    # 打开数据库
    db = kc.DB()
    if not db.open(db_path, kc.DB.OWRITER | kc.DB.OCREATE | kc.DB.OAUTOSYNC):
        print("open error: " + str(db.error()))
        return

    # 开始计时
    start_time = time.time()
    end_time = start_time + duration
    num_records = 0

    # 进行SET操作
    while time.time() < end_time:
        i = 0
        for i in range(100):
            key = str(num_records).zfill(8)
            value = "x" * 1024
            if not db.set(key, value):
                print("set error: " + str(db.error()))
                break
            num_records += 1

    # 结束计时
    elapsed_time = time.time() - start_time

    # 关闭数据库
    if not db.close():
        print("close error: " + str(db.error()))

    # 计算并打印性能指标
    ops_per_sec = num_records / elapsed_time
    # print(f"Total records: {num_records}")
    # print(f"Elapsed time: {elapsed_time:.2f} seconds")
    # print(f"Operations per second: {ops_per_sec:.2f} ops/sec")

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

    # 修改这里的路径以运行不同文件系统上的测试
    # db_path = "./test.kch"
    # db_path = "/tmp/test.kch"
    db_path = "/home/congyong/Odinfs/eval/benchmark/fxmark/bin/root/test.kch"
    ops_per_sec = set_operation(db_path)

    if ops_per_sec is not None:
        update_csv(args.fs_name, ops_per_sec, '/home/congyong/Odinfs/eval/data/KyotoCabinet/KyotoCabinet.csv')
        print(f"File system: {args.fs_name}")
        print(f"Operations per second: {ops_per_sec:.2f} ops/sec")