#!/bin/bash

# % 有并行运行的8个进程，和RDMA I/O
# % 归一化IOPS：对比全部flush
# % Fio workload: 8线程倾斜访问64MB私有文件，大部分访问6 ways热数据，少部分访问其余的冷数据
# % Baseline: 无委托，no flush
# % +Adaptive Data Update: 冷数据flush
# % +Isolated Data Access: L3\_CAT保护的委托线程访问热数据，委托线程分配6 ways（和shareable ways重合）
# % +Associativity-Friendly Data Layout：只将5 ways作为热数据，热数据连续物理地址，缓解set contention
# % +DDIO-Aware Way Allocation：和shareable ways不重合，避免I/O争用

echo "Run bombs manually!!! cd ../../../resctrl/; ./bomb.sh"
echo "Build fio-3.37 with libnuma-dev"
source common.sh

echo "挂载resctrl文件系统"
sudo mount -t resctrl resctrl /sys/fs/resctrl
sudo mkdir /sys/fs/resctrl/c1
# sudo bash -c 'echo "L3:0=fc0;1=fc0">/sys/fs/resctrl/c1/schemata' # not DDIO-aware, overlap with shareable ways
# sudo bash -c 'echo "L3:0=03f;1=03f">/sys/fs/resctrl/schemata'

# I/O contention
sudo numactl --cpunodebind=0 --membind=0 ib_write_bw -a -F --force-link=IB --ib-dev=mlx5_0 > /dev/null 2>&1 &
pid1=$!
sleep 1
ssh 192.168.98.74 'sudo numactl --cpunodebind=0 --membind=0 ib_write_bw 192.168.98.73 -F --force-link=IB --ib-dev=mlx5_0 --size=7340032 --duration=180' > /dev/null 2>&1 &
pid2=$!

# interfering process contention
# cd ../../../resctrl/; nohup ./bomb.sh &
# cd ../Odinfs/eval/scripts

# flush all data
sed -i 's/#define PMFS_DELEGATION_ENABLE 1/#define PMFS_DELEGATION_ENABLE 0/' ../../fs/odinfs/pmfs_config.h
sed -i 's/#define FREQUENT_LIMIT (5 * 896 * 4096)/#define FREQUENT_LIMIT (6 * 896 * 4096)/' ../../fs/odinfs/cache.h # not associative-friendly
sed -i 's/#define RECENT_LIMIT (5 * 896 * 4096)/#define RECENT_LIMIT (6 * 896 * 4096)/' ../../fs/odinfs/cache.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts
$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_breakdown-zipf$' \
    --ncore='1' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='False' --confirm='True' \
    --directory_name="breakdown" --log_name="odinfs-breakdown-zipf-flush-all-data.log" --duration=10

# remove-all-flush:
# sed -i 's/#define PMFS_DELEGATION_ENABLE 1/#define PMFS_DELEGATION_ENABLE 0/' ../../fs/odinfs/pmfs_config.h
sed -i 's/#define PMFS_NO_FLUSH 0/#define PMFS_NO_FLUSH 1/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_breakdown-zipf$' \
    --ncore='1' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='False' --confirm='True' \
    --directory_name="breakdown" --log_name="odinfs-breakdown-zipf-remove-all-flush.log" --duration=10

# flush cold data:
sed -i 's/#define PMFS_NO_FLUSH 1/#define PMFS_NO_FLUSH 0/' ../../fs/odinfs/pmfs_config.h
sed -i 's/#define PMFS_HOT_NO_FLUSH 0/#define PMFS_HOT_NO_FLUSH 1/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_breakdown-zipf$' \
    --ncore='1' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='False' --confirm='True' \
    --directory_name="breakdown" --log_name="odinfs-breakdown-zipf-flush-cold-data.log" --duration=10

# isolated data access
sed -i 's/#define PMFS_DELEGATION_ENABLE 0/#define PMFS_DELEGATION_ENABLE 1/' ../../fs/odinfs/pmfs_config.h
sed -i 's/#define PMFS_HOT_NO_FLUSH 1/#define PMFS_HOT_NO_FLUSH 0/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

# echo "挂载resctrl文件系统"
# sudo mount -t resctrl resctrl /sys/fs/resctrl
# sudo mkdir /sys/fs/resctrl/c1
sudo bash -c 'echo "L3:0=fc0;1=fc0">/sys/fs/resctrl/c1/schemata' # not DDIO-aware, overlap with shareable ways
sudo bash -c 'echo "L3:0=03f;1=03f">/sys/fs/resctrl/schemata'

$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_breakdown-zipf$' \
    --ncore='1' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='True' --confirm='True' \
    --directory_name="breakdown" --log_name="odinfs-breakdown-zipf-isolated-data-access.log" --duration=10

# associativity-friendly data layout
sed -i 's/#define FREQUENT_LIMIT (6 * 896 * 4096)/#define FREQUENT_LIMIT (5 * 896 * 4096)/' ../../fs/odinfs/cache.h
sed -i 's/#define RECENT_LIMIT (6 * 896 * 4096)/#define RECENT_LIMIT (5 * 896 * 4096)/' ../../fs/odinfs/cache.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_breakdown-zipf$' \
    --ncore='1' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='True' --confirm='True' \
    --directory_name="breakdown" --log_name="odinfs-breakdown-zipf-associativity-friendly-data-layout.log" --duration=10

# DDIO-aware way allocation
sudo bash -c 'echo "L3:0=03f;1=03f">/sys/fs/resctrl/c1/schemata' # DDIO-aware, not overlap with shareable ways
sudo bash -c 'echo "L3:0=fc0;1=fc0">/sys/fs/resctrl/schemata'

$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_breakdown-zipf$' \
    --ncore='1' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='True' --confirm='True' \
    --directory_name="breakdown" --log_name="odinfs-breakdown-zipf-DDIO-aware-way-allocation.log" --duration=10

# reset
sed -i 's/#define FREQUENT_LIMIT (6 * 896 * 4096)/#define FREQUENT_LIMIT (5 * 896 * 4096)/' ../../fs/odinfs/cache.h
sed -i 's/#define RECENT_LIMIT (6 * 896 * 4096)/#define RECENT_LIMIT (5 * 896 * 4096)/' ../../fs/odinfs/cache.h

# echo "卸载resctrl文件系统"
# sudo umount /sys/fs/resctrl/
sudo bash -c 'echo "L3:0=fff;1=fff">/sys/fs/resctrl/c1/schemata' # DDIO-aware, not overlap with shareable ways
sudo bash -c 'echo "L3:0=fff;1=fff">/sys/fs/resctrl/schemata'

echo "Wait for I/O contention to finish"
wait $pid1 $pid2
echo "I/O contention finished"

echo "Parsing fio results"
for i in `ls $FXMARK_LOG_PATH/breakdown/`
do
    echo "On $i"
    $FXMARK_PARSER_PATH/pdata.py --log="$FXMARK_LOG_PATH/breakdown/$i" \
    --type='fio' --out="$DATA_PATH/breakdown"
done
echo ""

cd ../fig
python breakdown.py
cd ../scripts