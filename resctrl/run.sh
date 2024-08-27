# sudo bash -c 'echo 1024 > /proc/sys/vm/nr_hugepages'
# sudo sh -c "echo 2 > /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages"
sudo make clean && sudo make || exit 1;

lsblk;
echo "Please check if EXT4-DAX is mounted at /home/congyong/fxmark-plain/bin/root";

# echo "Default"
# echo "Monitoring miss rate...";
# sudo ./resctrl_tests > out/log_miss.txt; # miss rate

# echo "Monitoring bandwidth...";
# sudo ./resctrl_tests -m > out/log_bw.txt; # monitor ipmctl
# python plot.py default;

# echo "Figure 1 - CacheContentionMitigation"
# echo "Monitoring miss rate...";
# sudo ./resctrl_tests -s 1 > out/log_miss_CacheContentionMitigation.txt; # miss rate

# echo "Monitoring bandwidth...";
# sudo ./resctrl_tests -s 1 -m > out/log_bw_CacheContentionMitigation.txt; # monitor ipmctl
# python plot.py CacheContentionMitigation;

# echo "Figure 2 - DRAMEnlargeWSS" # also test FileWrite here to prove FS runs on writer's CAT group
# echo "Monitoring miss rate...";
# sudo ./resctrl_tests -s 2 > out/log_miss_DRAMEnlargeWSS.txt; # miss rate

# echo "Monitoring bandwidth...";
# sudo ./resctrl_tests -s 2 -m > out/log_bw_DRAMEnlargeWSS.txt; # monitor ipmctl
# python plot.py DRAMEnlargeWSS;

# echo "Figure 3 - SetContention"
# echo "Please check if dev1.0 exists";
# echo "Monitoring miss rate...";
# sudo ./resctrl_tests -s 31 > out/log_miss_SetContention_35MB.txt; # miss rate

# echo "Monitoring bandwidth...";
# sudo ./resctrl_tests -s 31 -m > out/log_bw_SetContention_35MB.txt; # monitor ipmctl

# echo "Monitoring miss rate...";
# sudo ./resctrl_tests -s 32 > out/log_miss_SetContention_7MB.txt; # miss rate

# echo "Monitoring bandwidth...";
# sudo ./resctrl_tests -s 32 -m > out/log_bw_SetContention_7MB.txt; # monitor ipmctl

# python plot.py SetContention;

echo "Figure 4 - IOContention"



sudo numactl --cpunodebind=0 --membind=0 ib_write_bw -a -F --force-link=IB --ib-dev=mlx5_0 &
pid1=$!
sleep 1
ssh 192.168.98.74 'sudo numactl --cpunodebind=0 --membind=0 ib_write_bw 192.168.98.73 -F --force-link=IB --ib-dev=mlx5_0 --size=7340032 --duration=20' &
pid2=$!

echo "Monitoring miss rate...";
sudo numactl --cpunodebind=0 --membind=0 ./resctrl_tests -s 4 > out/log_miss_IOContention.txt; # miss rate

echo "Monitoring bandwidth...";
sudo numactl --cpunodebind=0 --membind=0 ./resctrl_tests -s 4 -m > out/log_bw_IOContention.txt; # monitor ipmctl

wait $pid1 $pid2
python plot.py IOContention;


# sudo mkfs.ext4 -b 4096 /dev/pmem0
# sudo mount -t ext4 -o dax /dev/pmem0 /home/congyong/fxmark-plain/bin/root;
# ls /home/congyong/fxmark-plain/bin/root;