echo "挂载resctrl文件系统"
sudo mount -t resctrl resctrl /sys/fs/resctrl
sudo mkdir /sys/fs/resctrl/c1

cd ../../fs && ./compile.sh > /dev/null 2>&1 && cd ../eval/scripts
sudo parradm create /dev/pmem0 
sudo mount -o init,dele_thrds=12 -t odinfs /dev/pmem_ar0 /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root
sudo touch /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root/test.txt
sudo bash -c 'base64 /dev/urandom | head -c 16384 >> /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root/test.txt'


gcc mmap.c -o mmap
sudo cat /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root/test.txt
sudo ./mmap /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root/test.txt
sudo cat /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root/test.txt

sudo umount /home/congyong/Odinfs/eval/benchmark/fxmark/bin/root