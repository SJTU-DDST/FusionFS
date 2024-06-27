#!/bin/bash

source common.sh

cd ../../fs/odinfs
sudo rmmod odinfs; sudo make && sudo insmod build/odinfs.ko
cd ../../eval/scripts

cd ../benchmark/fxmark
make
cd ../../scripts

echo "挂载resctrl文件系统"
sudo mount -t resctrl resctrl /sys/fs/resctrl # TODO: do this in kernel
sudo mkdir /sys/fs/resctrl/c1
sudo bash -c 'echo "L3:0=03f;1=03f">/sys/fs/resctrl/c1/schemata'
sudo bash -c 'echo "L3:0=fc0;1=fc0">/sys/fs/resctrl/schemata'

# $FXMARK_BIN_PATH/run-fxmark.py --media='pmem-local' \
#     --fs='^ext4$|^pmfs$|^nova$|^winefs$' \
#     --workload='^DRBL$|^DRBM$|^DRBH$|^DWOL$|^DWOM$|^DWAL$' \
#     --ncore='*' --iotype='bufferedio' --dthread='0' --dsocket='2' \
#     --rcore='False' --delegate='False' --confirm='True' \
#     --directory_name="fxmark" --log_name="fs.log" --duration=3

# $FXMARK_BIN_PATH/run-fxmark.py --media='^dm-stripe$' --fs='^ext4$' \
#     --workload='^DRBL$|^DRBM$|^DRBH$|^DWOL$|^DWOM$ |^DWAL$' \
#     --ncore='*' --iotype='bufferedio' --dthread='0' --dsocket='2' \
#     --rcore='False' --delegate='False' --confirm='True' \
#     --directory_name="fxmark" --log_name="ext-raid0.log" --duration=3

# $FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
#     --workload='^DRBL$|^DRBM$|^DRBH$' \
#     --ncore='*' --iotype='bufferedio' --dthread='12' --dsocket='2' \
#     --rcore='False' --delegate='False' --confirm='True' \
#     --directory_name="fxmark" --log_name="odinfs-read.log" --duration=3

$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^DWOL$' \
    --ncore='*' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='True' --confirm='True' \
    --directory_name="fxmark" --log_name="odinfs-write.log" --duration=1


echo "Parsing fxmark results"
for i in `ls $FXMARK_LOG_PATH/fxmark/`
do
    echo "On $i"
    $FXMARK_PARSER_PATH/pdata.py --log="$FXMARK_LOG_PATH/fxmark/$i" \
    --type='fxmark' --out="$DATA_PATH/fxmark"
    $FXMARK_PARSER_PATH/pdata.py --log="$FXMARK_LOG_PATH/fxmark/$i" \
    --type='fxmark' --out="/home/congyong/fxmark-plain/out"
done
echo ""

echo "卸载resctrl文件系统"
sudo umount /sys/fs/resctrl/
