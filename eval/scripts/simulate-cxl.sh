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

echo "用另一个NUMA节点模拟CXL设备的延迟"
sed -i 's|PMEMDEV = "/dev/pmem0"|PMEMDEV = "/dev/pmem1"|' ../../eval/benchmark/fxmark/bin/run-fxmark.py

sed -i 's/#define SIMULATE_BAS_WRITE_VOLUME 0/#define SIMULATE_BAS_WRITE_VOLUME 1/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

for granularity in 16384 4096 256 64
do
    sed -i "s/#define PMFS_BAS_GRANULARITY .*/#define PMFS_BAS_GRANULARITY $granularity/" ../../fs/odinfs/pmfs_config.h
    cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

    $FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_breakdown-uniform$' \
    --ncore='1' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='True' --confirm='True' \
    --directory_name="simulate-cxl" --log_name="FusionFS-simulate-granularity-$granularity.log" --duration=10
done

sed -i 's/#define PMFS_FUSIONFS 1/#define PMFS_FUSIONFS 0/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

# odinfs
for granularity in 16384 4096 256 64
do
    sed -i "s/#define PMFS_BAS_GRANULARITY .*/#define PMFS_BAS_GRANULARITY $granularity/" ../../fs/odinfs/pmfs_config.h
    cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

    $FXMARK_BIN_PATH/run-fxmark.py --media='pm-array' --fs='odinfs' \
    --workload='^fio_global_breakdown-uniform$' \
    --ncore='1' --iotype='bufferedio' --dthread='12' --dsocket='1' \
    --rcore='False' --delegate='True' --confirm='True' \
    --directory_name="simulate-cxl" --log_name="odinfs-simulate-granularity-$granularity.log" --duration=10
done

sed -i 's/#define PMFS_FUSIONFS 0/#define PMFS_FUSIONFS 1/' ../../fs/odinfs/pmfs_config.h
sed -i 's/#define SIMULATE_BAS_WRITE_VOLUME 1/#define SIMULATE_BAS_WRITE_VOLUME 0/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

echo "Parsing fio results for odinfs with simulate-cxl"
for i in `ls $FXMARK_LOG_PATH/simulate-cxl/`
do
    echo "On $i"
    granularity=`echo $i | cut -d '-' -f 4 | tr -dc '0-9'`
    $FXMARK_PARSER_PATH/pdata.py --log="$FXMARK_LOG_PATH/simulate-cxl/$i" \
    --type='fio' --out="$DATA_PATH/odinfs-granularity-$granularity"
done

echo "卸载resctrl文件系统"
sudo umount /sys/fs/resctrl/

sed -i 's|PMEMDEV = "/dev/pmem1"|PMEMDEV = "/dev/pmem0"|' ../../eval/benchmark/fxmark/bin/run-fxmark.py