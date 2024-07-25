#!/bin/bash

# different I/O size
# dedicated-cache update (kthread)
# in-place (hot, file size=16M)
# in-place (cold, file size=1G)
# active-flush update
# non-temporal update

source common.sh

echo "挂载resctrl文件系统"
sudo mount -t resctrl resctrl /sys/fs/resctrl
sudo mkdir /sys/fs/resctrl/c1

# active-flush update
sed -i 's/#define PMFS_NT_STORE 1/#define PMFS_NT_STORE 0/' ../../fs/odinfs/pmfs_config.h
sed -i 's/#define PMFS_DELEGATION_ENABLE 1/#define PMFS_DELEGATION_ENABLE 0/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts
$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_threshold-cold-1K$|^fio_global_threshold-cold-2K$|^fio_global_threshold-cold-4K$|^fio_global_threshold-cold-8K$|^fio_global_threshold-cold-16K$|^fio_global_threshold-cold-32K$|^fio_global_threshold-cold-64K$|^fio_global_threshold-cold-2M$' \
    --ncore='1' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='False' --confirm='True' \
    --directory_name="threshold" --log_name="odinfs-threshold-active-flush.log" --duration=10

# non-temporal update
sed -i 's/#define PMFS_NT_STORE 0/#define PMFS_NT_STORE 1/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts
$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_threshold-cold-1K$|^fio_global_threshold-cold-2K$|^fio_global_threshold-cold-4K$|^fio_global_threshold-cold-8K$|^fio_global_threshold-cold-16K$|^fio_global_threshold-cold-32K$|^fio_global_threshold-cold-64K$|^fio_global_threshold-cold-2M$' \
    --ncore='1' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='False' --confirm='True' \
    --directory_name="threshold" --log_name="odinfs-threshold-non-temporal.log" --duration=10

# in-place (cold):
sed -i 's/#define PMFS_NO_FLUSH 0/#define PMFS_NO_FLUSH 1/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_threshold-cold-1K$|^fio_global_threshold-cold-2K$|^fio_global_threshold-cold-4K$|^fio_global_threshold-cold-8K$|^fio_global_threshold-cold-16K$|^fio_global_threshold-cold-32K$|^fio_global_threshold-cold-64K$|^fio_global_threshold-cold-2M$' \
    --ncore='1' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='False' --confirm='True' \
    --directory_name="threshold" --log_name="odinfs-threshold-in-place-cold.log" --duration=10

# in-place (hot)
$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_threshold-hot-1K$|^fio_global_threshold-hot-2K$|^fio_global_threshold-hot-4K$|^fio_global_threshold-hot-8K$|^fio_global_threshold-hot-16K$|^fio_global_threshold-hot-32K$|^fio_global_threshold-hot-64K$|^fio_global_threshold-hot-2M$' \
    --ncore='1' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='False' --confirm='True' \
    --directory_name="threshold" --log_name="odinfs-threshold-in-place-hot.log" --duration=10

# dedicated-cache update:
sed -i 's/#define PMFS_NO_FLUSH 1/#define PMFS_NO_FLUSH 0/' ../../fs/odinfs/pmfs_config.h
sed -i 's/#define PMFS_DELEGATION_ENABLE 0/#define PMFS_DELEGATION_ENABLE 1/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

sudo bash -c 'echo "L3:0=03f;1=03f">/sys/fs/resctrl/c1/schemata' # DDIO-aware, not overlap with shareable ways
sudo bash -c 'echo "L3:0=fc0;1=fc0">/sys/fs/resctrl/schemata'

$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_threshold-hot-1K$|^fio_global_threshold-hot-2K$|^fio_global_threshold-hot-4K$|^fio_global_threshold-hot-8K$|^fio_global_threshold-hot-16K$|^fio_global_threshold-hot-32K$|^fio_global_threshold-hot-64K$|^fio_global_threshold-hot-2M$' \
    --ncore='1' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='True' --confirm='True' \
    --directory_name="threshold" --log_name="odinfs-threshold-dedicated-cache.log" --duration=10

# echo "卸载resctrl文件系统"
# sudo umount /sys/fs/resctrl/
sudo bash -c 'echo "L3:0=fff;1=fff">/sys/fs/resctrl/c1/schemata' # DDIO-aware, not overlap with shareable ways
sudo bash -c 'echo "L3:0=fff;1=fff">/sys/fs/resctrl/schemata'

echo "Parsing fio results"
for i in `ls $FXMARK_LOG_PATH/threshold/`
do
    echo "On $i"
    $FXMARK_PARSER_PATH/pdata.py --log="$FXMARK_LOG_PATH/threshold/$i" \
    --type='fio' --out="$DATA_PATH/threshold"
done
echo ""

cd ../fig
python threshold.py
cd ../scripts