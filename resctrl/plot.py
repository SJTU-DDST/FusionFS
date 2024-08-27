import re
import csv
from pprint import pprint
import matplotlib.pyplot as plt
import scienceplots
import sys
import datetime
import numpy as np

# plt.style.use(['science','ieee'])#,'no-latex']) # apt install cm-super dvipng

hat = ['|//','-\\\\','|\\\\','-//',"--","\\\\",'//',"xx"]
markers = ['H', '^', '>', 'D', 'o', 's', 'p', 'x']
c = np.array([[102, 194, 165], [252, 141, 98], [141, 160, 203], 
        [231, 138, 195], [166,216,84], [255, 217, 47],
        [229, 196, 148], [179, 179, 179]])
c  = c/255

fields = ["MediaReads", "MediaWrites", "ReadRequests", "WriteRequests", "TotalMediaReads", "TotalMediaWrites", "TotalReadRequests", "TotalWriteRequests"]
cat_titles = ["Flushing Cold Data", # No CAT
              "Naive L3_CAT", #  - Fixed 6/12 Ways (24 MB) Allocated to Main Process
              "Reversed CAT - Interference Cores in CAT Group", 
              "All CAT - Main Process & Interference Cores in CAT Group",
              "Writer Bomb CAT - File Writer in CAT and has a DRAM bomb thread",
              "Cache Pseudo-Locking",
              "Delegate CAT",
              "L3_CAT with DEVDAX",
              "L3_CAT with DRAM", # DRAM_CAT
              "L3_CAT with DRAM Hugepages",
              "L3_CAT with Margin",
              "L3_CAT with Margin and DEVDAX",
              "L3_CAT with Shareable Ways",
              "L3_CAT with Flush"]
cat_types = range(len(cat_titles))
# cat_types = [0, 1] # [No CAT, Cache Pseudo-Locking, CAT - Fixed 6/12 Ways (24 MB) Allocated to Main Process]

def parse_hex(hex_str):
    return int(hex_str, 16)

data = [{} for _ in range(len(cat_titles))]
bw_data = [{} for _ in range(len(cat_titles))]
n_bombs_values = [[] for _ in range(len(cat_titles))]
allocated_cache_values = [[] for _ in range(len(cat_titles))]

# 从日志文件中提取数据
def parse_logs(log_files = ["log_miss_CacheContentionMitigation.txt", "log_bw_CacheContentionMitigation.txt"]):
    for log_file in log_files:
        with open(log_file, "r") as file:
            during_perf = False
            before_data = {}
            perf_data = {}

            for line in file:
                if "Perf Start" in line:
                    during_perf = True
                elif "Perf End" in line:
                    during_perf = False
                    if "Before" in line:
                        before_data = perf_data.copy()
                    else:
                        items = line.split(',')
                        cat_type = int(line.split(',')[0].split(':')[-1])
                        period = 1000000
                        allocated_cache = 0
                        n_bombs = 0

                        for item in items:
                            if 'allocated_cache' in item:
                                allocated_cache = int(item.split(':')[1]) / (1024 * 1024)
                                if allocated_cache not in bw_data[cat_type]:
                                    bw_data[cat_type][allocated_cache] = {"n_bombs": [], "MediaReads": [], "MediaWrites": [], "ReadRequests": [], "WriteRequests": [], "TotalMediaReads": [], "TotalMediaWrites": [], "TotalReadRequests": [], "TotalWriteRequests": []}
                            if 'n_bombs' in item:
                                n_bombs = int(item.split(':')[1])
                            if 'CPU time' in item:
                                period = float(item.split(':')[1])
                        assert period != 1000000

                        stats = {}

                        for dimm_id in perf_data:
                            for field in perf_data[dimm_id]:
                                delta = perf_data[dimm_id][field] - before_data[dimm_id][field]
                                bandwidth = delta #/ period
                                # Display MediaWrites without dividing by period? But it may be affected by the size of the buffer, maybe divide by the buffer size?
                                # When miss=0, there is still bandwidth, from mem_flush in each run?
                                if 'Reads' in field or 'Writes' in field:
                                    bandwidth = bandwidth * 64 / (1024 * 1024 * 1024) # GB/s 
                                if field not in stats:
                                    stats[field] = 0
                                stats[field] += bandwidth
                        # print(stats)
                        if stats != {}:
                            bw_data[cat_type][allocated_cache]["n_bombs"].append(n_bombs)
                            for field in fields:
                                bw_data[cat_type][allocated_cache][field].append(stats[field])

                elif during_perf:
                    line = line.strip()
                    if "DimmID" in line:
                        dimm_id = parse_hex(line.split('=')[1].replace('-', ''))
                        perf_data[dimm_id] = {}
                    elif '=' in line:
                        field, value = line.split('=')
                        value = parse_hex(value)
                        perf_data[dimm_id][field] = value


                elif line.startswith("# TEST"):
                    cat_type = int(line.split(',')[0].split(':')[-1])
                    allocated_cache = 0
                    miss_rate = 0
                    n_bombs = 0
                    
                    for item in line.split(','):
                        if "allocated cache" in item:
                            allocated_cache = int(re.findall(r"\d+", item)[0]) / (1024 * 1024)  # Convert bytes to MB
                            if allocated_cache not in allocated_cache_values[cat_type]:
                                allocated_cache_values[cat_type].append(allocated_cache)
                                data[cat_type][allocated_cache] = {"n_bombs": [], "miss_rate": []}
                        if "miss rate" in item:
                            find_res = re.findall(r"[-+]?(?:\d*\.*\d+)", item)
                            if len(find_res) > 0:
                                miss_rate = float(find_res[0])
                            else:
                                miss_rate = 0
                            # miss_rate = float(re.findall(r"[-+]?(?:\d*\.*\d+)", item)[0]) # miss rate: -nan%
                        if "n_bombs" in item:
                            n_bombs = int(re.findall(r"\d+", item)[0])
                    if "miss" in log_file:
                        data[cat_type][allocated_cache]["n_bombs"].append(n_bombs)
                        data[cat_type][allocated_cache]["miss_rate"].append(miss_rate)

def plot_CacheSize():
    print("Plotting CacheSize")
    old_fontsize = plt.rcParams['font.size']
    plt.rcParams['font.size'] = old_fontsize * 1.1
    # Define the data
    families = ['Intel Xeon Scalable', 'Intel Xeon Scalable', 'Intel Xeon Scalable', 'Intel Xeon Scalable', 'AMD EPYC', 'AMD EPYC']
    # code_names = ['Ice Lake', 'Sapphire Rapids', 'Emerald Rapids', 'Granite Rapids', 'Milan', 'Genoa']
    launch_times = [datetime.datetime(2021, 4, 1), datetime.datetime(2023, 1, 1), datetime.datetime(2023, 10, 1), datetime.datetime(2024, 7, 1), datetime.datetime(2022, 4, 1), datetime.datetime(2023, 4, 1)]
    cache_sizes = [60, 112.5, 320, 480, 768, 1152]

    # Create the plot
    plt.figure(figsize=(10, 3))
    for i, family in enumerate(set(families)):
        x = [launch_times[i] for i in range(len(families)) if families[i] == family]
        y = [cache_sizes[i] for i in range(len(families)) if families[i] == family]
        plt.plot(x, y, marker=markers[i], label=family, color=c[i], lw=3, mec='black', markersize=8, alpha=1)
        # for i in range(len(x)):
        #     plt.annotate(code_names[i], (x[i], y[i]), textcoords="offset points", xytext=(0, 5), ha='center')
    plt.annotate('Ice Lake', (launch_times[0], cache_sizes[0]), textcoords="offset points", xytext=(5, 10), ha='center')
    plt.annotate('Sapphire Rapids', (launch_times[1], cache_sizes[1]), textcoords="offset points", xytext=(-25, 10), ha='center')
    plt.annotate('Emerald Rapids', (launch_times[2], cache_sizes[2]), textcoords="offset points", xytext=(-25, 10), ha='center')
    plt.annotate('Granite Rapids', (launch_times[3], cache_sizes[3]), textcoords="offset points", xytext=(0, 10), ha='center')
    plt.annotate('Milan', (launch_times[4], cache_sizes[4]), textcoords="offset points", xytext=(-10, 10), ha='center')
    plt.annotate('Genoa', (launch_times[5], cache_sizes[5]), textcoords="offset points", xytext=(0, -20), ha='center')

    # Add title and labels
    # plt.title('L3 Cache Sizes in Recent Processor Generations')
    plt.xlabel('Launch Time')
    plt.ylabel('Maximum L3 (MB)')
    plt.grid(axis='y', linestyle='-.')
    # set xticks
    plt.xticks([datetime.datetime(2021, 1, 1), datetime.datetime(2022, 1, 1), datetime.datetime(2023, 1, 1), datetime.datetime(2024, 1, 1), datetime.datetime(2025, 1, 1)], ['2021', '2022', '2023', '2024', '2025'])

    # Add legend
    plt.legend()
    plt.tight_layout()
    plt.savefig("out/CacheSize.png", bbox_inches='tight')  # 保存图表为图片
    plt.savefig("out/CacheSize.pdf", bbox_inches='tight')  # 保存图表为图片
    plt.rcParams['font.size'] = old_fontsize


# if any(bw_data[i] for i in range(len(bw_data))):
def plot_bw(preset = "default"):
    print("Plotting bandwidth data, note that LLC misses are not accurate with this option")
    count = 0
    for cat_type in cat_types:
        if allocated_cache_values[cat_type]:
            count += 1
    fig, axs = plt.subplots(1, count, figsize=(3 * count, 3))
    plot_id = 0
    max_bw = 0
    for cat_type in cat_types:
        if not allocated_cache_values[cat_type]:
            continue
        if count == 1:
            ax = axs
        else:
            ax = axs[plot_id]

        for i, allocated_cache in enumerate(allocated_cache_values[cat_type]):
            try:
                n_bombs = bw_data[cat_type][allocated_cache]["n_bombs"]
            except:
                print(cat_type, allocated_cache, "failed")
                n_bombs = []
                continue
            MediaWrites = bw_data[cat_type][allocated_cache]["MediaWrites"]
            max_bw = max(max_bw, max(MediaWrites))
            # print(allocated_cache, MediaWrites)
            ax.plot(n_bombs, MediaWrites, marker=markers[i], label=f"{allocated_cache} MB")
        ax.set_xlabel("Interference Cores")  # Update x-axis label
        ax.set_ylabel("PM Bandwidth (GB)")
        # ax.set_title("No CAT" if cat_type else "CAT - Fixed 6/12 Ways (24 MB) Allocated to Main Process")
        ax.set_title(cat_titles[cat_type])
        ax.grid(True)
        # ax.set_ylim(0, 1)
        # ax.set_xticks(n_bombs)  # Set x-axis tick values
        ax.legend()
        plot_id += 1
    plot_id = 0
    for cat_type in cat_types:
        if not allocated_cache_values[cat_type]:
            continue
        if count == 1:
            ax = axs
        else:
            ax = axs[plot_id]
        ax.set_ylim(0, max_bw * 1.1)
        plot_id += 1
    # {min(allocated_cache_values[0])} MB, {max(allocated_cache_values[0])} MB
    if preset == "default":
        plt.suptitle(f"Cache Contention: Main Process Writing [3.5 MB, 21 MB] PM Buffer, \nwith [0, 32] Interference Cores Writing 100 MB Private DRAM Buffers")  # Add title for the entire image
    # else:
    #     plt.suptitle(preset)

    plt.tight_layout()
    if preset == "default":
        plt.savefig("out/bandwidth.png")  # 保存图表为图片
        plt.savefig("out/bandwidth.pdf")
    else:
        plt.savefig(f"out/bw_{preset}.png")
        plt.savefig(f"out/bw_{preset}.pdf")

def plot_miss(preset = "default", ylim_100 = True):
    print("Plotting cache miss rate data")
    count = 0
    for cat_type in cat_types:
        if allocated_cache_values[cat_type]:
            count += 1
    fig, axs = plt.subplots(1, count, figsize=(3 * count, 3))
    plot_id = 0
    max_miss = 0
    for cat_type in cat_types:
        if not allocated_cache_values[cat_type]:
            continue
        if count == 1:
            ax = axs
        else:
            ax = axs[plot_id]

        for i, allocated_cache in enumerate(allocated_cache_values[cat_type]):
            n_bombs = data[cat_type][allocated_cache]["n_bombs"]
            miss_rate = data[cat_type][allocated_cache]["miss_rate"]
            max_miss = max(max_miss, max(miss_rate))
            # print(allocated_cache, miss_rate)
            ax.plot(n_bombs, miss_rate, marker=markers[i], label=f"{allocated_cache} MB")
        ax.set_xlabel("Interference Cores")  # Update x-axis label
        ax.set_ylabel("L3 Miss Rate (\%)")
        ax.set_title(cat_titles[cat_type])
        ax.grid(True)
        if ylim_100:
            ax.set_ylim(0, 100)
        else:
            ax.set_ylim(0, max_miss * 1.1)
        # ax.set_xticks(n_bombs)  # Set x-axis tick values
        ax.legend()
        plot_id += 1
    # {min(allocated_cache_values[0])} MB, {max(allocated_cache_values[0])} MB
    if preset == "default":
        plt.suptitle(f"Cache Contention: Main Process Writing [3.5 MB, 21 MB] PM Buffer, \nwith [0, 32] Interference Cores Writing 100 MB Private DRAM Buffers")
    # else:
    #     plt.suptitle(preset)
    
    plt.tight_layout()
    if preset == "default":
        plt.savefig("out/miss.png")  # 保存图表为图片
        plt.savefig("out/miss.pdf")
    else:
        plt.savefig(f"out/miss_{preset}.png")
        plt.savefig(f"out/miss_{preset}.pdf")

def plot_CacheContentionMitigation(cat_types = [0, 5, 1, 13]): # [No CAT, Cache Pseudo-Locking, CAT - Fixed 6/12 Ways (24 MB) Allocated to Main Process]
    print("Plotting CacheContentionMitigation")

    old_fontsize = plt.rcParams['font.size']
    plt.rcParams['font.size'] = old_fontsize * 1.1

    # plt.rcParams.update({
    #     "font.family": "sans-serif",
    #     "font.serif": ["Times New Roman"]})
    
    # plt.rcParams["font.family"] = "Times New Roman"
    # plt.rcParams['font.family'] = 'Linux Libertine O' # install ttf; fc-cache; rm ~/.cache/matplotlib -rf

    # plt.rcParams.update({
    #     # "text.usetex": True,
    #     "font.family": "Linux Libertine O"
    # })
    
    fig, axs = plt.subplots(1, 2, figsize=(8, 2), layout='constrained')
    ax_miss = axs[0]
    ax_bw = axs[1]

    count = 0

    for i, cat_type in enumerate(cat_types):
        if not allocated_cache_values[cat_type]:
            continue
        if cat_type == 0:
            fixed_allocated_cache = 42.0
        else:
            fixed_allocated_cache = 38.5
        n_bombs = data[cat_type][fixed_allocated_cache]["n_bombs"]
        miss_rate = data[cat_type][fixed_allocated_cache]["miss_rate"]
        ax_miss.plot(n_bombs, miss_rate, marker=markers[i], label=cat_titles[cat_type], color=c[i], lw=3, mec='black', markersize=8, alpha=1)  # Use different marker for each cat_type
        n_bombs = bw_data[cat_type][fixed_allocated_cache]["n_bombs"]
        MediaWrites = bw_data[cat_type][fixed_allocated_cache]["MediaWrites"]

        # Here the buffer traversed with cat_type==0 is 42MB and the other cat type traversed is 38.5MB.
        # To make sure that the calculation of MediaWrites is fair, I put MediaWrites*(11/12) with cat_type=0.
        # if cat_type == 0:
        #     MediaWrites = [MediaWrites[i] * (11/12) for i in range(len(MediaWrites))] # IMPORTANT: NO SCALE!

        # we use L3_CAT with flush as the baseline
        GiB = bw_data[13][38.5]["MediaWrites"][0]
        if cat_type == 0:
            GiB = GiB / 11 * 12

        ax_bw.plot(n_bombs, [value / GiB for value in MediaWrites], marker=markers[i], label=cat_titles[cat_type], color=c[i], lw=3, mec='black', markersize=8, alpha=1)  # Use different marker for each cat_type
        count += 1
    
    ax_miss.set_xlabel("# interfering processes")  # Update x-axis label
    ax_miss.set_ylabel("Cache Misses (%)")
    ax_miss.set_ylim(bottom=0)
    ax_miss.set_xticks([i for i in n_bombs if i % 4 == 0])
    ax_miss.grid(axis='y', linestyle='-.')
    # ax_miss.grid(True)
    # ax_miss.set_ylim(0, 100)
    # ax_miss.legend()
    ax_bw.set_xlabel("# interfering processes")  # Update x-axis label
    ax_bw.set_ylabel("I/O amplification")
    ax_bw.set_ylim(bottom=0)
    ax_bw.set_xticks([i for i in n_bombs if i % 4 == 0])
    ax_bw.grid(axis='y', linestyle='-.')
    # ax_bw.grid(True)
    # ax_bw.legend()
    # {min(allocated_cache_values[0])} MB, {max(allocated_cache_values[0])} MB
    # plt.suptitle(f"Cache Contention: Main Process Writing {fixed_allocated_cache} MB PM Buffer, \nwith [0, 32] Interference Cores Writing 100 MB Private DRAM Buffers")  # Add title for the entire image
    handles, labels = ax_miss.get_legend_handles_labels()
    fig.legend(handles, labels, loc=9, bbox_to_anchor=(0.5, 1.15), ncol=count, frameon=False)
    # plt.tight_layout()
            
    plt.savefig("out/CacheContentionMitigation.png", bbox_inches='tight')  # 保存图表为图片
    plt.savefig("out/CacheContentionMitigation.pdf", bbox_inches='tight')  # 保存图表为图片

    plt.rcParams['font.size'] = old_fontsize

def plot_DRAMEnlargeWSS(cat_types = [1, 13]):
    print("Plotting DRAMEnlargeWSS")

    old_fontsize = plt.rcParams['font.size']
    plt.rcParams['font.size'] = old_fontsize * 1.1
    
    fig, axs = plt.subplots(1, 2, figsize=(8, 2), layout='constrained')
    ax_miss = axs[0]
    ax_bw = axs[1]

    count = 0

    for i, cat_type in enumerate(cat_types):
        if not allocated_cache_values[cat_type]:
            continue
        dram_buf_sizes = allocated_cache_values[cat_type]
        miss_rate = [data[cat_type][dram_buf_size]["miss_rate"] for dram_buf_size in dram_buf_sizes]
        MediaWrites = [bw_data[cat_type][dram_buf_size]["MediaWrites"] for dram_buf_size in dram_buf_sizes]

        ax_miss.plot(dram_buf_sizes, miss_rate, marker=markers[i], label=cat_titles[cat_type], color=c[i], lw=3, mec='black', markersize=8, alpha=1)  # Use different marker for each cat_type
        ax_bw.plot(dram_buf_sizes, [MediaWrites[i][0] / bw_data[13][size]["MediaWrites"][0] for i, size in enumerate(dram_buf_sizes)], marker=markers[i], label=cat_titles[cat_type], color=c[i], lw=3, mec='black', markersize=8, alpha=1)  # Use different marker for each cat_type
        count += 1
    
    ax_miss.set_xlabel("DRAM WSS (MB)")  # Update x-axis label
    ax_miss.set_xticks(dram_buf_sizes)
    ax_miss.set_ylabel("Cache Misses (%)")
    ax_miss.set_ylim(bottom=0)
    ax_miss.grid(axis='y', linestyle='-.')

    ax_bw.set_xlabel("DRAM WSS (MB)")  # Update x-axis label
    ax_bw.set_xticks(dram_buf_sizes)
    ax_bw.set_ylabel("I/O amplification")
    ax_bw.set_ylim(bottom=0)
    ax_bw.grid(axis='y', linestyle='-.')

    handles, labels = ax_miss.get_legend_handles_labels()
    fig.legend(handles, labels, loc=9, bbox_to_anchor=(0.5, 1.15), ncol=count, frameon=False)
    # plt.tight_layout()
            
    plt.savefig("out/DRAMEnlargeWSS.png", bbox_inches='tight')  # 保存图表为图片
    plt.savefig("out/DRAMEnlargeWSS.pdf", bbox_inches='tight')  # 保存图表为图片

    plt.rcParams['font.size'] = old_fontsize

def plot_SetContention(cat_types = [1, 7, 13]):
    global data, bw_data, n_bombs_values, allocated_cache_values
    parse_logs(["out/log_miss_SetContention_35MB.txt", "out/log_bw_SetContention_35MB.txt"])
    print("Plotting SetContention")

    old_fontsize = plt.rcParams['font.size']
    plt.rcParams['font.size'] = old_fontsize * 1.1
    
    fig = plt.figure(layout='constrained', figsize=(10, 2))
    subfigs = fig.subfigures(1, 2)

    subfig_35MB = subfigs[0]
    axs = subfig_35MB.subplots(1, 2)
    ax_miss_35MB = axs[0]
    ax_bw_35MB = axs[1]

    count = 0

    for i, cat_type in enumerate(cat_types):
        if not allocated_cache_values[cat_type]:
            continue
        pm_buf_sizes = allocated_cache_values[cat_type]
        miss_rate = [data[cat_type][pm_buf_size]["miss_rate"] for pm_buf_size in pm_buf_sizes]
        MediaWrites = [bw_data[cat_type][pm_buf_size]["MediaWrites"] for pm_buf_size in pm_buf_sizes]

        ax_miss_35MB.plot(pm_buf_sizes, miss_rate, marker=markers[i], label=cat_titles[cat_type], color=c[i], lw=3, mec='black', markersize=8, alpha=1)  # Use different marker for each cat_type
        ax_bw_35MB.plot(pm_buf_sizes, [MediaWrites[i][0] / bw_data[13][size]["MediaWrites"][0] for i, size in enumerate(pm_buf_sizes)], marker=markers[i], label=cat_titles[cat_type], color=c[i], lw=3, mec='black', markersize=8, alpha=1)  # Use different marker for each cat_type
        count += 1
    
    ax_miss_35MB.set_xlabel("PM WSS (MB)")  # Update x-axis label
    ax_miss_35MB.set_xticks(pm_buf_sizes[::2])
    ax_miss_35MB.set_xticklabels(pm_buf_sizes[::2], rotation=45, ha='right')  # Rotate x-axis labels
    ax_miss_35MB.set_ylabel("Cache Misses (\%)")
    ax_miss_35MB.set_ylim(bottom=0)
    ax_miss_35MB.grid(axis='y', linestyle='-.')

    ax_bw_35MB.set_xlabel("PM WSS (MB)")  # Update x-axis label
    ax_bw_35MB.set_xticks(pm_buf_sizes[::2])
    ax_bw_35MB.set_xticklabels(pm_buf_sizes[::2], rotation=45, ha='right')  # Rotate x-axis labels
    ax_bw_35MB.set_ylabel("I/O amplification")
    ax_bw_35MB.set_ylim(bottom=0)
    ax_bw_35MB.grid(axis='y', linestyle='-.')
    
    subfigs[0].suptitle("(a) 10 Cache Ways Allocated to Main Process")

    data = [{} for _ in range(len(cat_titles))]
    bw_data = [{} for _ in range(len(cat_titles))]
    n_bombs_values = [[] for _ in range(len(cat_titles))]
    allocated_cache_values = [[] for _ in range(len(cat_titles))]
    parse_logs(["out/log_miss_SetContention_7MB.txt", "out/log_bw_SetContention_7MB.txt"])

    subfig_7MB = subfigs[1]
    axs = subfig_7MB.subplots(1, 2)
    ax_miss_7MB = axs[0]
    ax_bw_7MB = axs[1]

    for i, cat_type in enumerate(cat_types):
        if not allocated_cache_values[cat_type]:
            continue
        pm_buf_sizes = allocated_cache_values[cat_type]
        miss_rate = [data[cat_type][pm_buf_size]["miss_rate"] for pm_buf_size in pm_buf_sizes]
        MediaWrites = [bw_data[cat_type][pm_buf_size]["MediaWrites"] for pm_buf_size in pm_buf_sizes]

        ax_miss_7MB.plot(pm_buf_sizes, miss_rate, marker=markers[i], label=cat_titles[cat_type], color=c[i], lw=3, mec='black', markersize=8, alpha=1)
        ax_bw_7MB.plot(pm_buf_sizes, [MediaWrites[i][0] / bw_data[13][size]["MediaWrites"][0] for i, size in enumerate(pm_buf_sizes)], marker=markers[i], label=cat_titles[cat_type], color=c[i], lw=3, mec='black', markersize=8, alpha=1)
        count += 1

    ax_miss_7MB.set_xlabel("PM WSS (MB)")  # Update x-axis label
    ax_miss_7MB.set_xticks(pm_buf_sizes)
    ax_miss_7MB.set_xticklabels(pm_buf_sizes, rotation=45, ha='right')  # Rotate x-axis labels
    ax_miss_7MB.set_ylabel("Cache Misses (\%)")
    ax_miss_7MB.set_ylim(bottom=0)
    ax_miss_7MB.grid(axis='y', linestyle='-.')

    ax_bw_7MB.set_xlabel("PM WSS (MB)")  # Update x-axis label
    ax_bw_7MB.set_xticks(pm_buf_sizes)
    ax_bw_7MB.set_xticklabels(pm_buf_sizes, rotation=45, ha='right')  # Rotate x-axis labels
    ax_bw_7MB.set_ylabel("I/O amplification")
    ax_bw_7MB.set_ylim(bottom=0)
    ax_bw_7MB.grid(axis='y', linestyle='-.')

    subfigs[1].suptitle("(b) 2 Cache Ways Allocated to Main Process")

    handles, labels = ax_miss_35MB.get_legend_handles_labels()
    fig.legend(handles, labels, loc=9, bbox_to_anchor=(0.5, 1.15), ncol=count, frameon=False)
    # plt.tight_layout()
            
    plt.savefig("out/SetContention.png", bbox_inches='tight')  # 保存图表为图片
    plt.savefig("out/SetContention.pdf", bbox_inches='tight')  # 保存图表为图片

    plt.rcParams['font.size'] = old_fontsize

def plot_IOContention(cat_types = [1, 12, 13]):
    print("Plotting IOContention")

    old_fontsize = plt.rcParams['font.size']
    plt.rcParams['font.size'] = old_fontsize * 1.1

    fig, axs = plt.subplots(1, 2, figsize=(5, 2), layout='constrained')
    ax_miss = axs[0]
    ax_bw = axs[1]

    plot_cache = 3.5

    if data[1]:
        miss_rate_CAT = data[1][plot_cache]["miss_rate"]
        MediaWrites_CAT = bw_data[1][plot_cache]["MediaWrites"]
    else:
        miss_rate_CAT = [0]
        MediaWrites_CAT = [0]
    if data[12]:
        miss_rate_Shareable_CAT = data[12][plot_cache]["miss_rate"]
        MediaWrites_Shareable_CAT = bw_data[12][plot_cache]["MediaWrites"]
    else:
        miss_rate_Shareable_CAT = [0]
        MediaWrites_Shareable_CAT = [0]
    if data[13]:
        miss_rate_CAT_FLUSH = data[13][plot_cache]["miss_rate"]
        MediaWrites_CAT_FLUSH = bw_data[13][plot_cache]["MediaWrites"]
    else:
        miss_rate_CAT_FLUSH = [0]
        MediaWrites_CAT_FLUSH = [0]

    # Set grid lines to be below the bars
    ax_miss.set_axisbelow(True)
    ax_bw.set_axisbelow(True)
        
    ax_miss.bar(0, miss_rate_CAT[0], label=cat_titles[1], color=c[0], edgecolor='black', lw=1.2)
    ax_miss.bar(1, miss_rate_Shareable_CAT[0], label=cat_titles[12], color=c[1], edgecolor='black', lw=1.2)
    ax_miss.bar(2, miss_rate_CAT_FLUSH[0], label=cat_titles[13], color=c[2], edgecolor='black', lw=1.2)
    ax_bw.bar(0, MediaWrites_CAT[0] / MediaWrites_CAT_FLUSH[0], label=cat_titles[1], color=c[0], edgecolor='black', lw=1.2)
    ax_bw.bar(1, MediaWrites_Shareable_CAT[0] / MediaWrites_CAT_FLUSH[0], label=cat_titles[12], color=c[1], edgecolor='black', lw=1.2)
    ax_bw.bar(2, MediaWrites_CAT_FLUSH[0] / MediaWrites_CAT_FLUSH[0], label=cat_titles[13], color=c[2], edgecolor='black', lw=1.2)

    # ax_miss.set_xticks([0, 1, 2])
    # ax_miss.set_xticklabels(["", "", ""])
    ax_miss.set_xticks([])
    ax_miss.set_xlim(-1, 3)
    ax_miss.set_ylabel("Cache Misses (\%)")
    ax_miss.set_ylim(bottom=0)
    ax_miss.grid(axis='y', linestyle='-.')

    # ax_bw.set_xticks([0, 1, 2])
    # ax_bw.set_xticklabels(["", "", ""])
    ax_bw.set_xticks([])
    ax_bw.set_xlim(-1, 3)
    ax_bw.set_ylabel("I/O amplification")
    ax_bw.set_ylim(bottom=0)
    ax_bw.grid(axis='y', linestyle='-.')

    handles, labels = ax_miss.get_legend_handles_labels()
    fig.legend(handles, labels, loc=9, bbox_to_anchor=(0.5, 1.15), ncol=3, frameon=False)
    # plt.tight_layout()

    plt.savefig("out/IOContention.png", bbox_inches='tight')  # 保存图表为图片
    plt.savefig("out/IOContention.pdf", bbox_inches='tight')  # 保存图表为图片

    # plt.rcParams['font.size'] = old_fontsize

if len(sys.argv) > 1:
    preset = sys.argv[1]
    if preset == "default":
        parse_logs(log_files=["out/log_miss.txt", "out/log_bw.txt"])
        plot_bw()
        plot_miss()
    elif preset == "CacheSize":
        # parse_logs(["out/log_miss_CacheContentionMitigation.txt", "out/log_bw_CacheContentionMitigation.txt"])
        plot_CacheSize()
    elif preset == "CacheContentionMitigation":
        parse_logs(["out/log_miss_CacheContentionMitigation.txt", "out/log_bw_CacheContentionMitigation.txt"])
        plot_CacheContentionMitigation()
    elif preset == "DRAMEnlargeWSS":
        parse_logs(["out/log_miss_DRAMEnlargeWSS.txt", "out/log_bw_DRAMEnlargeWSS.txt"])
        # plot_bw(preset)
        # plot_miss(preset)
        plot_DRAMEnlargeWSS()
        # print(data)
    elif preset == "SetContention":
        # parse_logs(["out/log_miss_SetContention_35MB.txt", "out/log_bw_SetContention_35MB.txt"])
        # pprint(data)
        # pprint(bw_data)
        # plot_bw(preset)
        # plot_miss(preset, ylim_100=False)
        plot_SetContention()
    elif preset == "IOContention":
        parse_logs(["out/log_miss_IOContention.txt", "out/log_bw_IOContention.txt"])
        # pprint(bw_data)
        plot_bw(preset)
        plot_miss(preset, ylim_100=False)
        plot_IOContention()
    else:
        print("Invalid preset argument")
else:
    parse_logs(log_files=["out/log_miss.txt", "out/log_bw.txt"])
    plot_bw()
    plot_miss()

# csv_names = ["data_cat.csv", "data_cat_type.csv"]
# for cat_type in range(len(n_bombs_values)):
#     with open(csv_names[cat_type], "w", newline="") as file:
#         writer = csv.writer(file)
#         writer.writerow(["n_bombs", *data[cat_type][list(data[cat_type].keys())[0]]["n_bombs"]])
#         for allocated_cache, values in data[cat_type].items():
#             miss_rate = values["miss_rate"]
#             writer.writerow([allocated_cache, *miss_rate])