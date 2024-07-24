#!/bin/bash

echo "Remember run ./compile.sh after reboot"
echo "Build fio-3.37 with libnuma-dev"

source common.sh

cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

echo "挂载resctrl文件系统"
sudo mount -t resctrl resctrl /sys/fs/resctrl # TODO: do this in kernel
sudo mkdir /sys/fs/resctrl/c1
sudo bash -c 'echo "L3:0=03f;1=03f">/sys/fs/resctrl/c1/schemata'
sudo bash -c 'echo "L3:0=fc0;1=fc0">/sys/fs/resctrl/schemata'

for i in 1 2
do
    $FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_rand-write-file-size-4M$|^fio_global_rand-write-file-size-8M$|^fio_global_rand-write-file-size-12M$|^fio_global_rand-write-file-size-16M$|^fio_global_rand-write-file-size-20M$|^fio_global_rand-write-file-size-24M$|^fio_global_rand-write-file-size-28M$|^fio_global_rand-write-file-size-32M$|^fio_global_rand-write-file-size-36M$|^fio_global_rand-write-file-size-40M$|^fio_global_rand-write-file-size-44M$' \
    --ncore='1' --iotype='bufferedio' --dthread='12' --dsocket=$i \
    --rcore='False' --delegate='True' --confirm='True' \
    --directory_name="NUMA-nodes" --log_name="odinfs-NUMA-nodes-$i.log" --duration=1
done

echo "Parsing fio results for FusionFS with varying NUMA nodes"
for i in `ls $FXMARK_LOG_PATH/NUMA-nodes/`
do
    echo "On $i"
    sockets=`echo $i | cut -d '-' -f 4 | tr -dc '0-9'`
    $FXMARK_PARSER_PATH/pdata.py --log="$FXMARK_LOG_PATH/NUMA-nodes/$i" \
    --type='fio' --out="$DATA_PATH/NUMA-nodes-$sockets-sockets"
done
echo ""

echo "卸载resctrl文件系统"
sudo umount /sys/fs/resctrl/

cd ../fig
python NUMA-nodes.py
cd ../scripts