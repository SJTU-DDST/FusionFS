#!/bin/bash

echo "Remember run ./compile.sh after reboot"

source common.sh

cd ../../fs
./compile.sh
cd ../eval/scripts 

cd ../benchmark/fxmark
make
cd ../../scripts

# TODO: set duration to 30

# $FXMARK_BIN_PATH/run-fxmark.py --media='pmem-local' \
#     --fs='^ext4$|^pmfs$|^nova$|^winefs$' \
#     --workload='^DRBL$|^DRBM$|^DRBH$|^DWOL$|^DWOM$|^DWAL$|^MWCL$|^MWCM$' \
#     --ncore='*' --iotype='bufferedio' --dthread='0' --dsocket='1' \
#     --rcore='False' --delegate='False' --confirm='True' \
#     --directory_name="fxmark" --log_name="fs.log" --duration=1

# $FXMARK_BIN_PATH/run-fxmark.py --media='^dm-stripe$' --fs='^ext4$' \
#     --workload='^DRBL$|^DRBM$|^DRBH$|^DWOL$|^DWOM$|^DWAL$|^MWCL$|^MWCM$' \
#     --ncore='*' --iotype='bufferedio' --dthread='0' --dsocket='1' \
#     --rcore='False' --delegate='False' --confirm='True' \
#     --directory_name="fxmark" --log_name="ext-raid0.log" --duration=1

echo "挂载resctrl文件系统"
sudo mount -t resctrl resctrl /sys/fs/resctrl # TODO: do this in kernel
sudo mkdir /sys/fs/resctrl/c1
sudo bash -c 'echo "L3:0=03f;1=03f">/sys/fs/resctrl/c1/schemata'
sudo bash -c 'echo "L3:0=fc0;1=fc0">/sys/fs/resctrl/schemata'

$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^DRBL$|^DRBM$|^DRBH$' \
    --ncore='*' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='False' --confirm='True' \
    --directory_name="fxmark" --log_name="FusionFS-read.log" --duration=1

$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^DWOL$|^DWOM$|^DWAL$' \
    --ncore='*' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='True' --confirm='True' \
    --directory_name="fxmark" --log_name="FusionFS-write.log" --duration=1
    
$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^MWCL$|^MWCM$' \
    --ncore='*' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='True' --confirm='True' \
    --directory_name="fxmark" --log_name="FusionFS-dir.log" --duration=1

sudo bash -c 'echo "L3:0=fff;1=fff">/sys/fs/resctrl/c1/schemata' # DDIO-aware, not overlap with shareable ways
sudo bash -c 'echo "L3:0=fff;1=fff">/sys/fs/resctrl/schemata'
sed -i 's/#define PMFS_FUSIONFS 1/#define PMFS_FUSIONFS 0/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^DRBL$|^DRBM$|^DRBH$' \
    --ncore='*' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='False' --confirm='True' \
    --directory_name="fxmark" --log_name="odinfs-read.log" --duration=1

$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^DWOL$|^DWOM$|^DWAL$' \
    --ncore='*' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='True' --confirm='True' \
    --directory_name="fxmark" --log_name="odinfs-write.log" --duration=1
    
$FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^MWCL$|^MWCM$' \
    --ncore='*' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='True' --confirm='True' \
    --directory_name="fxmark" --log_name="odinfs-dir.log" --duration=1

sed -i 's/#define PMFS_FUSIONFS 0/#define PMFS_FUSIONFS 1/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

echo "Parsing fxmark results"
for i in `ls $FXMARK_LOG_PATH/fxmark/`
do
    echo "On $i"
    $FXMARK_PARSER_PATH/pdata.py --log="$FXMARK_LOG_PATH/fxmark/$i" \
    --type='fxmark' --out="$DATA_PATH/fxmark"
done
echo ""

# echo "卸载resctrl文件系统"
# sudo umount /sys/fs/resctrl/

# cd ../fig
# ./fig.sh
# cd ../scripts

cd ../../eval/benchmark/fxmark
bin/plotter.py --ty sc-matplotlib-plotter  --out ../../fig
cd ../../scripts