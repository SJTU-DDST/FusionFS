echo "挂载resctrl文件系统"
sudo mount -t resctrl resctrl /sys/fs/resctrl
sudo mkdir /sys/fs/resctrl/c1

sudo umount /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root
sudo parradm delete

sed -i 's/#define PMFS_FINE_GRAINED_LOCK 1/#define PMFS_FINE_GRAINED_LOCK 0/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts
sudo parradm create /dev/pmem0 
sudo mount -o init,dele_thrds=12 -t odinfs /dev/pmem_ar0 /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root
sudo -E python sqlite_test.py FusionFS
sudo umount /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root

sed -i 's/#define PMFS_FUSIONFS 1/#define PMFS_FUSIONFS 0/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts
sudo parradm create /dev/pmem0 
sudo mount -o init,dele_thrds=12 -t odinfs /dev/pmem_ar0 /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root
sudo -E python sqlite_test.py odinfs
sudo umount /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root
sudo parradm delete

# sed -i 's/#define PMFS_FINE_GRAINED_LOCK 0/#define PMFS_FINE_GRAINED_LOCK 1/' ../../fs/odinfs/pmfs_config.h
sed -i 's/#define PMFS_FUSIONFS 0/#define PMFS_FUSIONFS 1/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts

sudo mkfs.ext4 -b 4096 /dev/pmem0
sudo mount -t ext4 -o dax /dev/pmem0 /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root
sudo -E python sqlite_test.py ext4
sudo umount /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root

sudo mount -o init -t winefs /dev/pmem0 /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root
sudo -E python sqlite_test.py winefs
sudo umount /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root

sudo mount -o init -t pmfs /dev/pmem0 /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root
sudo -E python sqlite_test.py pmfs
sudo umount /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root

sudo mount -o init -t NOVA /dev/pmem0 /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root
sudo -E python sqlite_test.py nova
sudo umount /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root