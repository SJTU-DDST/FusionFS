import subprocess
import re
import time
import pprint
import matplotlib.pyplot as plt

def parse_hex(hex_str):
    return int(hex_str, 16)

def calculate_bandwidth(current, previous, period):
    diff = current - previous
    bytes_count = diff * 64  # Each count represents 64 bytes
    gb = bytes_count / (1024 * 1024 * 1024)
    bandwidth = gb / period
    return bandwidth

def monitor_performance(period):
    previous_media_reads = {}
    prev_data = None
    command = "sudo ipmctl show -dimm -performance"

    timestamps = []
    media_reads = []
    media_writes = []
    read_requests = []
    write_requests = []
    total_media_reads = []
    total_media_writes = []
    total_read_requests = []
    total_write_requests = []

    def plot():
        fig, axs = plt.subplots(1, 2, figsize=(12, 6))
        # 绘制 Reads/Writes (GB/s) 图
        ax = axs[0]
        ax.plot(timestamps, media_reads, label='Media Reads')
        ax.plot(timestamps, media_writes, label='Media Writes')
        ax.plot(timestamps, total_media_reads, label='Total Media Reads')
        ax.plot(timestamps, total_media_writes, label='Total Media Writes')
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Bandwidth (GB/s)')
        ax.set_title('Performance Monitoring - Reads/Writes')
        ax.legend()
        ax.grid(True)

        # 绘制 Requests (ops) 图
        ax = axs[1]
        ax.plot(timestamps, read_requests, label='Read Requests')
        ax.plot(timestamps, write_requests, label='Write Requests')
        ax.plot(timestamps, total_read_requests, label='Total Read Requests')
        ax.plot(timestamps, total_write_requests, label='Total Write Requests')
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Requests (ops)')
        ax.set_title('Performance Monitoring - Requests')
        ax.legend()
        ax.grid(True)

        plt.tight_layout()
        plt.savefig("performance.png")  # 保存图表为图片

    try:
        start_time = time.time()
        run_process = subprocess.Popen(["sudo", "bash", "run.sh"])
        while run_process.poll() is None: # True
            output = subprocess.check_output(command, shell=True, universal_newlines=True)
            lines = [elem.strip() for elem in output.splitlines()]

            data = {}
            dimm_id = 0

            for line in lines:
                if "DimmID" in line:
                    dimm_id = parse_hex(line.split('=')[1].replace('-', ''))
                    data[dimm_id] = {}
                else:
                    field, value = line.split('=')
                    value = parse_hex(value)
                    data[dimm_id][field] = value

            if prev_data is not None:
                stats = {}

                for dimm_id in data:
                    for field in data[dimm_id]:
                        delta = data[dimm_id][field] - prev_data[dimm_id][field]
                        bandwidth = delta / period

                        if 'Reads' in field or 'Writes' in field:
                            bandwidth = bandwidth * 64 / (1024 * 1024 * 1024) # GB/s 

                        if field not in stats:
                            stats[field] = 0
                        stats[field] += bandwidth

                timestamp = round(time.time() - start_time)
                timestamps.append(timestamp)
                media_reads.append(stats.get('MediaReads', 0))
                media_writes.append(stats.get('MediaWrites', 0))
                read_requests.append(stats.get('ReadRequests', 0))
                write_requests.append(stats.get('WriteRequests', 0))
                total_media_reads.append(stats.get('TotalMediaReads', 0))
                total_media_writes.append(stats.get('TotalMediaWrites', 0))
                total_read_requests.append(stats.get('TotalReadRequests', 0))
                total_write_requests.append(stats.get('TotalWriteRequests', 0))

                print(f"Time: {timestamp:.2f}")
                for field in stats:
                    if 'Reads' in field or 'Writes' in field:
                        print(f"{field}: {stats[field]:.2f} GB/s")
                    else:
                        print(f"{field}: {stats[field]:.2f}")

            prev_data = data.copy()
            time.sleep(period)

    except KeyboardInterrupt:
        fig, axs = plt.subplots(1, 2, figsize=(12, 6))
        # 绘制 Reads/Writes (GB/s) 图
        ax = axs[0]
        ax.plot(timestamps, media_reads, label='Media Reads')
        ax.plot(timestamps, media_writes, label='Media Writes')
        ax.plot(timestamps, total_media_reads, label='Total Media Reads')
        ax.plot(timestamps, total_media_writes, label='Total Media Writes')
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Bandwidth (GB/s)')
        ax.set_title('Performance Monitoring - Reads/Writes')
        ax.legend()
        ax.grid(True)

        # 绘制 Requests (ops) 图
        ax = axs[1]
        ax.plot(timestamps, read_requests, label='Read Requests')
        ax.plot(timestamps, write_requests, label='Write Requests')
        ax.plot(timestamps, total_read_requests, label='Total Read Requests')
        ax.plot(timestamps, total_write_requests, label='Total Write Requests')
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Requests (ops)')
        ax.set_title('Performance Monitoring - Requests')
        ax.legend()
        ax.grid(True)

        plt.tight_layout()
        plt.savefig("performance.png")  # 保存图表为图片
        
monitor_performance(1.0)  # Period in seconds