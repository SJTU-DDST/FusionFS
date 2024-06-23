cmd_/home/congyong/Odinfs/test/modules.order := {   echo /home/congyong/Odinfs/test/my_module.ko; :; } | awk '!x[$$0]++' - > /home/congyong/Odinfs/test/modules.order
