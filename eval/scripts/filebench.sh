#!/bin/bash

source common.sh

cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

echo "挂载resctrl文件系统"
sudo mount -t resctrl resctrl /sys/fs/resctrl
sudo mkdir /sys/fs/resctrl/c1
sudo bash -c 'echo "L3:0=03f;1=03f">/sys/fs/resctrl/c1/schemata'
sudo bash -c 'echo "L3:0=fc0;1=fc0">/sys/fs/resctrl/schemata'

$FXMARK_BIN_PATH/run-fxmark.py --media='pmem-local' \
    --fs='^ext4$|^pmfs$|^nova$|^winefs$' \
    --workload='filebench_*' \
    --ncore='*' --iotype='bufferedio' --dthread='0' --dsocket='0' \
    --rcore='False' --delegate='False' --confirm='True' \
    --directory_name="filebench" --log_name="fs.log" --duration=3

$FXMARK_BIN_PATH/run-fxmark.py --media='^dm-stripe$' --fs='^ext4$' \
    --workload='filebench_*' \
    --ncore='*' --iotype='bufferedio' --dthread='0' --dsocket='1' \
    --rcore='False' --delegate='False' --confirm='True' \
    --directory_name="filebench" --log_name="ext4-raid0.log" --duration=3

$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='filebench_*' \
    --ncore='*' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='True' --confirm='True' \
    --directory_name="filebench" --log_name="FusionFS.log" --duration=3

sed -i 's/#define PMFS_FUSIONFS 1/#define PMFS_FUSIONFS 0/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='filebench_*' \
    --ncore='*' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='True' --confirm='True' \
    --directory_name="filebench" --log_name="odinfs.log" --duration=3

sed -i 's/#define PMFS_FUSIONFS 0/#define PMFS_FUSIONFS 1/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

sudo bash -c 'echo "L3:0=fff;1=fff">/sys/fs/resctrl/c1/schemata' # DDIO-aware, not overlap with shareable ways
sudo bash -c 'echo "L3:0=fff;1=fff">/sys/fs/resctrl/schemata'

echo "Parsing filebench results"
for i in `ls $FXMARK_LOG_PATH/filebench/`
do
    echo "On $i"
    $FXMARK_PARSER_PATH/pdata.py --log="$FXMARK_LOG_PATH/filebench/$i" \
    --type='filebench' --out="$DATA_PATH/filebench"
done
echo ""

cd ../fig
python fig12.py
cd ../scripts
