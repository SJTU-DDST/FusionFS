import matplotlib.pyplot as plt
import numpy as np

# hat = ['|//','-\\\\','|\\\\','-//',"--","\\\\",'//',"xx"]
markers = ['H', '^', '>', 'D', 'o', 's', 'p', 'x']
c = np.array([[102, 194, 165], [252, 141, 98], [141, 160, 203], 
        [231, 138, 195], [166,216,84], [255, 217, 47],
        [229, 196, 148], [179, 179, 179]])
c  = c/255

# Define the log file names in the desired order
log_files = {
    "flush-all-data": "flush all data\n(PMFS)",
    "remove-all-flush": "+remove\nall flush",
    "flush-cold-data": "+adaptive\ndata update",
    "isolated-data-access": "+isolated\ndata access",
    "associativity-friendly-data-layout": "+associativity-\nfriendly\ndata layout",
    "DDIO-aware-way-allocation": "+DCA-aware\nway allocation",
}

# Initialize lists to store the data
x_values = []
y_values_1_uniform = []
y_values_2_uniform = []
# y_values_1_zipf = []
# y_values_2_zipf = []

# Read the data from the log files
for log_file, value in log_files.items():
    file_path_uniform = f"../data/breakdown/odinfs-breakdown-uniform-{log_file}.log"
    # file_path_zipf = f"../data/breakdown/odinfs-breakdown-zipf-{log_file}.log"
    
    with open(file_path_uniform, "r") as file_uniform: #, open(file_path_zipf, "r") as file_zipf:
        lines_uniform = file_uniform.readlines()
        # lines_zipf = file_zipf.readlines()
        
        # Extract the relevant data from the uniform log file
        data_line_uniform = lines_uniform[1].strip().split()
        x_values.append(value)

        thp = float(data_line_uniform[1])
        MiB = thp / 1024 * 10 # we run for 10 seconds
        amp = float(data_line_uniform[-1]) / MiB

        y_values_1_uniform.append(thp / 1024 / 1024)
        y_values_2_uniform.append(amp)
        
        # Extract the relevant data from the zipf log file
        # data_line_zipf = lines_zipf[1].strip().split()
        # y_values_1_zipf.append(float(data_line_zipf[1]))
        # y_values_2_zipf.append(float(data_line_zipf[-1]))

# Create a figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3), layout="constrained")

# Plot the first subplot
width = 0.35  # width of the bars
x = range(len(x_values))
ax1.set_axisbelow(True)
ax1.bar(x, y_values_1_uniform, width, label="uniform", color=c[0], edgecolor='black', lw=1.2)
# ax1.bar([i + width for i in x], [val/1000000 for val in y_values_1_zipf], width, label="zipf", alpha=0.5)
ax1.set_ylabel("Throughput (GiB/s)")
# ax1.set_xticks([i + width/2 for i in x])
ax1.set_xticks(x)
ax1.set_xticklabels(x_values, rotation=45, ha="right")
# ax1.legend()
ax1.grid(axis='y', linestyle='-.')

# Plot the second subplot
ax2.set_axisbelow(True)
ax2.bar(x, y_values_2_uniform, width, label="uniform", color=c[0], edgecolor='black', lw=1.2)
# ax2.bar([i + width for i in x], [val/1024 for val in y_values_2_zipf], width, label="zipf", alpha=0.5)
ax2.set_ylabel("I/O amplification")
# ax2.set_xticks([i + width/2 for i in x])
ax2.set_xticks(x)
ax2.set_xticklabels(x_values, rotation=45, ha="right")
ax2.grid(axis='y', linestyle='-.')

# Calculate the percentage increase in y_values_1_uniform
y_values_1_uniform_increase = [((y_values_1_uniform[i] - y_values_1_uniform[i-1]) / y_values_1_uniform[i-1]) * 100 for i in range(1, len(y_values_1_uniform))]

# Calculate the percentage increase in y_values_2_uniform
y_values_2_uniform_increase = [((y_values_2_uniform[i] - y_values_2_uniform[i-1]) / y_values_2_uniform[i-1]) * 100 for i in range(1, len(y_values_2_uniform))]

# Print the percentage increase in y_values_1_uniform
print("Percentage increase in y_values_1_uniform:")
for increase in y_values_1_uniform_increase:
    print(f"{increase:.2f}%")
print("Combined increase between last and first value:")
print(f"{((y_values_1_uniform[-1] - y_values_1_uniform[0]) / y_values_1_uniform[0]) * 100:.2f}%")

# Print the percentage increase in y_values_2_uniform
print("Percentage increase in y_values_2_uniform:")
for increase in y_values_2_uniform_increase:
    print(f"{increase:.2f}%")
print("Combined increase between last and first value:")
print(f"{((y_values_2_uniform[-1] - y_values_2_uniform[0]) / y_values_2_uniform[0]) * 100:.2f}%")

plt.savefig("breakdown.png", bbox_inches='tight')
plt.savefig("breakdown.pdf", bbox_inches='tight')