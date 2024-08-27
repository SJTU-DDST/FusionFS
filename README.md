This repository contains the source code for FusionFS, which is implemented based on [ODINFS](https://rs3lab.github.io/Odinfs/). 

# Overview 

### Structure:

```
root
|---- fs                 (source code of the evaluated file systems)
    |---- odinfs         (odinfs/FusionFS kernel module) 
    |---- parradm        (odinfs user-level utility)
    |---- nova         
    |---- pmfs 
    |---- winefs
|---- linux              (5.13.13 Linux kernel)
|---- eval               (evaluation)
    |---- benchmark      (Filebench and Fxmark) 
    |---- scripts        (main evaluation scripts) 
    |---- fig            (figures) 
    |---- data           (raw data)
|---- dep.sh             (scripts to install dependency)    
|---- resctrl            (FusionFS's cache contention tests)
```

### Environment: 

Our artifact should run on any Linux distribution. The current scripts are developed for **Ubuntu 22.04.4 LTS**. Porting to other Linux distributions would require some scripts modifications , especially ```dep.sh```, which installs dependencies with package management tools. 

# Setup 

**Note**: For the below steps, our scripts will complain if it fails to compile or install the target. Check the end part of the scripts' output to ensure that the install is successful. Also, some scripts would prompt to ask the sudo permission at the beginning. 

### 1. Install the dependencies:
```
$ ./dep.sh 
```

### 2. Install the 5.13.13 Linux kernel (50GB space and 20 minutes)
```
$ cd linux
$ cp config-odinfs .config
$ make oldconfig             (update the config with the provided .config file)
```

Say N to KASAN if the config program prompts to ask about it. 

```
KASAN: runtime memory debugger (KASAN) [N/y/?] (NEW) N
```


Next, please use your favorite way to compile and install the kernel. The below step is just for reference. The installation requires 50GB space and takes around 20 minutes on our machines. 

For Ubuntu:
```
$ make -j8 deb-pkg           (generate the kernel installment package)
$ cd ..
$ sudo dpkg -i *.deb         (install the package) 
```

Otherwise, the classical ways will work as well:

```
$ make -j8              
$ make -j8 modules 
$ sudo make install
$ sudo make modules_install
```
Reboot the machine to the installed 5.13.13 kernel. 

### 3. Install and insmod file systems 

```
$ cd fs
$ ./compile.sh
```
The script will compile, install, and insert the following kernel modules:

* Odinfs/FusionFS 
* PMFS 
* NOVA 
* Winefs

### 4. Compile and install benchmarks 

**4.1 Fxmark**

```
$ cd eval/benchmark/fxmark
$ ./compile.sh
```

**4.2 Filebench**

```
$ cd eval/benchmark/filebench
$ ./compile.sh
```

### 5. Install tools 

Install ipmctl instead of pmwatch to monitor PM media writes: https://github.com/intel/ipmctl

# Running Experiments:

Main scripts are under ```eval/scripts/```

```
eval/scripts
|---- fio.sh                    (FIO-related experiments; fig1, fig2, fig6, fig7)
|---- fxmark.sh                 (Fxmark-related experiments; fig11)
|---- filebench.sh              (Filebench-related experiments; fig12)
|---- fio-odinfs-vd.sh          (Odinfs with varying number of delegation threads; fig1, fig9)   
|---- fio-odinfs-vn.sh          (Odinfs with varying number of NUMA nodes; fig10) 
|---- ampl.sh                   (I/O amplifcation rate of each file system; fig2, fig8)
|---- numa.sh                   (PM NUMA impact; fig3)
|---- run-all.sh                (running all the above scripts)
|---- run-test.sh               (quick run of fio, fxmark, and filbench with the evaluated file systems)
|---- odinfs.sh                 (rerun all the experiments related to odinfs)
|---- parse.sh                  (parse and output the results to directory: eval/data)
|---- fio-vary-zipf.sh           (FusionFS's FIO with varying zipf factor)   
|---- breakdown-uniform.sh      (FusionFS's breakdown analysis) 
|---- threshold.sh              (FusionFS's threshold sensitivity analysis)
|---- NUMA-nodes.sh             (FusionFS's NUMA nodes sensitivity analysis)
|---- KyotoCabinet.sh           (FusionFS's KyotoCabinet test)
|---- lmdb.sh                   (FusionFS's LMDB test)
```

# Authors of ODINFS

Diyu Zhou (EPFL)

Yuchen Qian (EPFL) 

Vishal Gupta (EPFL) 

Zhifei Yang (EPFL) 

Changwoo Min (Virginia Tech) 

Sanidhya Kashyap (EPFL) 