#!/bin/bash

echo "Remember run ./compile.sh after reboot"
echo "Build fio-3.37 with libnuma-dev"

source common.sh

cd ../../fs && ./compile.sh || exit 1
cd ../eval/scripts

echo "挂载resctrl文件系统"
sudo mount -t resctrl resctrl /sys/fs/resctrl # TODO: do this in kernel
sudo mkdir /sys/fs/resctrl/c1
sudo bash -c 'echo "L3:0=03f;1=03f">/sys/fs/resctrl/c1/schemata'
sudo bash -c 'echo "L3:0=fc0;1=fc0">/sys/fs/resctrl/schemata'

for i in 4 8 14 20 
do
    $FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_seq-read-4K$' \
    --ncore='*' --iotype='bufferedio' --dthread="$i" --dsocket='1' \
    --rcore='False' --delegate='False' --confirm='True' \
    --directory_name="fio-vd" --log_name="odinfs-read-$i-4k.log" --duration=1
    
    $FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_seq-read-2M$' \
    --ncore='*' --iotype='bufferedio' --dthread="$i" --dsocket='1' \
    --rcore='False' --delegate='True' --confirm='True' \
    --directory_name="fio-vd" --log_name="odinfs-read-$i-2m.log" --duration=1

    $FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_seq-write-4K$|^fio_global_seq-write-2M$' \
    --ncore='*' --iotype='bufferedio' --dthread="$i" --dsocket='1' \
    --rcore='False' --delegate='True' --confirm='True' \
    --directory_name="fio-vd" --log_name="odinfs-write-$i.log" --duration=1
done

echo "Parsing fio results for odinfs with varying delegation threads"
for i in `ls $FXMARK_LOG_PATH/fio-vd/`
do
    echo "On $i"
    threads=`echo $i | cut -d '-' -f 3 | tr -dc '0-9'`
    $FXMARK_PARSER_PATH/pdata.py --log="$FXMARK_LOG_PATH/fio-vd/$i" \
    --type='fio' --out="$DATA_PATH/odinfs-$threads-threads"
done
echo ""

echo "卸载resctrl文件系统"
sudo umount /sys/fs/resctrl/