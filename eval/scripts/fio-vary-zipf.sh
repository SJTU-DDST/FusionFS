#!/bin/bash

echo "Remember run ./compile.sh after reboot"
echo "Build fio-3.37 with libnuma-dev"

source common.sh

cd ../../fs
./compile.sh
cd ../eval/scripts 

# $FXMARK_BIN_PATH/run-fxmark.py --media='pmem-local' \
#     --fs='^ext4$|^pmfs$|^nova$|^winefs$' \
#     --workload='^fio_global_rand-write-4K$|^fio_global_rand-write-4K-zipf-90-10$|^fio_global_rand-write-4K-zipf-80-20$|^fio_global_rand-write-4K-zipf-70-30$|^fio_global_rand-write-4K-zipf-60-40$|^fio_global_rand-write-2M$|^fio_global_rand-write-2M-zipf-90-10$|^fio_global_rand-write-2M-zipf-80-20$|^fio_global_rand-write-2M-zipf-70-30$|^fio_global_rand-write-2M-zipf-60-40$' \
#     --ncore='*' --iotype='bufferedio' --dthread='0' --dsocket='0' \
#     --rcore='False' --delegate='False' --confirm='True' \
#     --directory_name="fio-vary-zipf" --log_name="fs-write.log" --duration=10

echo "挂载resctrl文件系统"
sudo mount -t resctrl resctrl /sys/fs/resctrl # TODO: do this in kernel
sudo mkdir /sys/fs/resctrl/c1
sudo bash -c 'echo "L3:0=03f;1=03f">/sys/fs/resctrl/c1/schemata'
sudo bash -c 'echo "L3:0=fc0;1=fc0">/sys/fs/resctrl/schemata'

$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_rand-write-4K$|^fio_global_rand-write-4K-zipf-90-10$|^fio_global_rand-write-4K-zipf-80-20$|^fio_global_rand-write-4K-zipf-70-30$|^fio_global_rand-write-4K-zipf-60-40$|^fio_global_rand-write-2M$|^fio_global_rand-write-2M-zipf-90-10$|^fio_global_rand-write-2M-zipf-80-20$|^fio_global_rand-write-2M-zipf-70-30$|^fio_global_rand-write-2M-zipf-60-40$' \
    --ncore='*' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='True' --confirm='True' \
    --directory_name="fio-vary-zipf" --log_name="FusionFS-write.log" --duration=10

sudo bash -c 'echo "L3:0=fff;1=fff">/sys/fs/resctrl/c1/schemata'
sudo bash -c 'echo "L3:0=fff;1=fff">/sys/fs/resctrl/schemata'

sed -i 's/#define PMFS_FUSIONFS 1/#define PMFS_FUSIONFS 0/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

# $FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
#     --workload='^fio_global_rand-write-4K$|^fio_global_rand-write-4K-zipf-90-10$|^fio_global_rand-write-4K-zipf-80-20$|^fio_global_rand-write-4K-zipf-70-30$|^fio_global_rand-write-4K-zipf-60-40$|^fio_global_rand-write-2M$|^fio_global_rand-write-2M-zipf-90-10$|^fio_global_rand-write-2M-zipf-80-20$|^fio_global_rand-write-2M-zipf-70-30$|^fio_global_rand-write-2M-zipf-60-40$' \
#     --ncore='*' --iotype='bufferedio' --dthread='12' --dsocket='1' \
#     --rcore='False' --delegate='True' --confirm='True' \
#     --directory_name="fio-vary-zipf" --log_name="odinfs-write.log" --duration=10

sed -i 's/#define PMFS_FUSIONFS 0/#define PMFS_FUSIONFS 1/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

echo "Parsing fio results"
for i in `ls $FXMARK_LOG_PATH/fio-vary-zipf/`
do
    echo "On $i"
    $FXMARK_PARSER_PATH/pdata.py --log="$FXMARK_LOG_PATH/fio-vary-zipf/$i" \
    --type='fio' --out="$DATA_PATH/fio-vary-zipf"
done
echo ""

# echo "卸载resctrl文件系统"
# sudo umount /sys/fs/resctrl/
