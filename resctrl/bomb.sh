sudo make clean;
sudo make && sudo numactl --cpunodebind=0 --membind=0 ./resctrl_tests -j