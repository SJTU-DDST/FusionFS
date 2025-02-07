import matplotlib.pyplot as plt
import numpy as np

old_fontsize = plt.rcParams['font.size']
plt.rcParams['font.size'] = old_fontsize * 1.1

hat = ['//', '\\\\', 'xx', '||', '--', '++']
markers = ['H', '^', '>', 'D', 'o', 's', 'p', 'x']
c = np.array([[102, 194, 165], [252, 141, 98], [141, 160, 203], 
        [231, 138, 195], [166,216,84], [255, 217, 47],
        [229, 196, 148], [179, 179, 179]])
c  = c/255

# Define the log file names in the desired order
log_files = {
    "64": {
        "odinfs": "../data/odinfs-granularity-64/pm-array:odinfs:breakdown-uniform:bufferedio.dat",
        "FusionFS": "../data/odinfs-granularity-64/pm-array:FusionFS:breakdown-uniform:bufferedio.dat"
    },
    "256": {
        "odinfs": "../data/odinfs-granularity-256/pm-array:odinfs:breakdown-uniform:bufferedio.dat",
        "FusionFS": "../data/odinfs-granularity-256/pm-array:FusionFS:breakdown-uniform:bufferedio.dat"
    },
    "4096": {
        "odinfs": "../data/odinfs-granularity-4096/pm-array:odinfs:breakdown-uniform:bufferedio.dat",
        "FusionFS": "../data/odinfs-granularity-4096/pm-array:FusionFS:breakdown-uniform:bufferedio.dat"
    },
    "16384": {
        "odinfs": "../data/odinfs-granularity-16384/pm-array:odinfs:breakdown-uniform:bufferedio.dat",
        "FusionFS": "../data/odinfs-granularity-16384/pm-array:FusionFS:breakdown-uniform:bufferedio.dat"
    }
}

# Initialize lists to store the data
x_values = []
y_values_1_odinfs = []
y_values_1_FusionFS = []
y_values_2_odinfs = []
y_values_2_FusionFS = []
y_values_3_odinfs = []
y_values_3_FusionFS = []

# Read the data from the log files
for granularity, paths in log_files.items():
    for fs, file_path in paths.items():
        with open(file_path, "r") as file:
            lines = file.readlines()
            
            # Extract the relevant data from the log file
            data_line = lines[1].strip().split()
            if fs == "odinfs":
                if granularity not in x_values:
                    x_values.append(granularity)
                thp = float(data_line[1])
                latency = float(data_line[2])
                MiB = thp / 1024 * 10 # we run for 10 seconds
                amp = float(data_line[-1]) / MiB

                y_values_1_odinfs.append(thp / 1024 / 1024)
                y_values_2_odinfs.append(amp)
                y_values_3_odinfs.append(latency)
            elif fs == "FusionFS":
                thp = float(data_line[1])
                latency = float(data_line[2])
                MiB = thp / 1024 * 10 # we run for 10 seconds
                amp = float(data_line[-1]) / MiB

                y_values_1_FusionFS.append(thp / 1024 / 1024)
                y_values_2_FusionFS.append(amp)
                y_values_3_FusionFS.append(latency)

# Create a figure with three subplots
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10, 3)) #, layout="constrained")

# Plot the first subplot
width = 0.35  # width of the bars
x = np.arange(len(x_values))
ax1.set_axisbelow(True)
ax1.bar(x - width/2, y_values_1_odinfs, width, label="ODINFS", color=c[0], edgecolor='black', lw=1.2, hatch=hat[0])
ax1.bar(x + width/2, y_values_1_FusionFS, width, label="FusionFS", color=c[1], edgecolor='black', lw=1.2, hatch=hat[1])
ax1.set_ylabel("Throughput (GiB/s)")
ax1.set_xlabel("Access granularity (B)")
ax1.set_xticks(x)
ax1.set_xticklabels(x_values)
ax1.grid(axis='y', linestyle='-.')

# Plot the second subplot
ax2.set_axisbelow(True)
ax2.bar(x - width/2, y_values_3_odinfs, width, label="ODINFS", color=c[0], edgecolor='black', lw=1.2, hatch=hat[0])
ax2.bar(x + width/2, y_values_3_FusionFS, width, label="FusionFS", color=c[1], edgecolor='black', lw=1.2, hatch=hat[1])
ax2.set_ylabel("Latency (μs)")
ax2.set_xlabel("Access granularity (B)")
ax2.set_xticks(x)
ax2.set_xticklabels(x_values)
ax2.grid(axis='y', linestyle='-.')

# Plot the third subplot
ax3.set_axisbelow(True)
ax3.bar(x - width/2, y_values_2_odinfs, width, label="ODINFS", color=c[0], edgecolor='black', lw=1.2, hatch=hat[0])
ax3.bar(x + width/2, y_values_2_FusionFS, width, label="FusionFS", color=c[1], edgecolor='black', lw=1.2, hatch=hat[1])
ax3.set_ylabel("I/O amplification")
ax3.set_xlabel("Access granularity (B)")
ax3.set_xticks(x)
ax3.set_xticklabels(x_values)
ax3.grid(axis='y', linestyle='-.')

# Create a shared legend
handles, labels = ax1.get_legend_handles_labels()
fig.legend(handles, labels, loc=9, ncol=2, frameon=False)

# Calculate the percentage increase in y_values_1_odinfs
y_values_1_odinfs_increase = [((y_values_1_odinfs[i] - y_values_1_odinfs[i-1]) / y_values_1_odinfs[i-1]) * 100 for i in range(1, len(y_values_1_odinfs))]

# Calculate the percentage increase in y_values_2_odinfs
y_values_2_odinfs_increase = [((y_values_2_odinfs[i] - y_values_2_odinfs[i-1]) / y_values_2_odinfs[i-1]) * 100 for i in range(1, len(y_values_2_odinfs))]

# Print the percentage increase in y_values_1_odinfs
print("Percentage increase in y_values_1_odinfs:")
for increase in y_values_1_odinfs_increase:
    print(f"{increase:.2f}%")
print("Combined increase between last and first value:")
print(f"{((y_values_1_odinfs[-1] - y_values_1_odinfs[0]) / y_values_1_odinfs[0]) * 100:.2f}%")

# Print the percentage increase in y_values_2_odinfs
print("Percentage increase in y_values_2_odinfs:")
for increase in y_values_2_odinfs_increase:
    print(f"{increase:.2f}%")
print("Combined increase between last and first value:")
print(f"{((y_values_2_odinfs[-1] - y_values_2_odinfs[0]) / y_values_2_odinfs[0]) * 100:.2f}%")

plt.tight_layout()
fig.subplots_adjust(top=0.9)
plt.savefig("simulate-cxl.png", bbox_inches='tight')
plt.savefig("simulate-cxl.pdf", bbox_inches='tight')