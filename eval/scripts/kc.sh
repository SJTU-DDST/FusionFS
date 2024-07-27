echo "挂载resctrl文件系统"
sudo mount -t resctrl resctrl /sys/fs/resctrl
sudo mkdir /sys/fs/resctrl/c1

sudo umount /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root
sudo parradm delete

sed -i 's/#define PMFS_FINE_GRAINED_LOCK 1/#define PMFS_FINE_GRAINED_LOCK 0/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts
sudo parradm create /dev/pmem0 
sudo mount -o init,dele_thrds=12 -t odinfs /dev/pmem_ar0 /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root

cd /home/congyong/Downloads/kyotocabinet-1.2.80
sudo -E python kc_test.py
cd /home/congyong/Odinfs/eval/scripts

sudo umount /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root
sudo parradm delete
sudo rmmod odinfs

sed -i 's/#define PMFS_FINE_GRAINED_LOCK 0/#define PMFS_FINE_GRAINED_LOCK 1/' ../../fs/odinfs/pmfs_config.h
cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts