import psutil
import platform
from datetime import datetime
from time import sleep
import json
import requests
import tomllib

def get_configs():     # Coleta dados de configuração do agente (sujeito a mudanças)
    with open("config.toml", "rb") as f:
        data = tomllib.load(f)
    return data

#### HTTP POST #####
def send_data(json_object, controller_url):
    try:
        response = requests.post(controller_url, json=json_object)
        return response.status_code
    except Exception as e:
        return e
    
#### DATA COLLECTION ######

def get_size(bytes, suffix="B"):  # byte scale formatter
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def disk_info():   # disk processing
    devices = {}
    partitions = psutil.disk_partitions()  # get all disk partitions
    for partition in partitions:
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
        except PermissionError:
            # this can be catched due to the disk that
            # isn't ready
            continue

        dict_device = {
            partition.device: {
                "mountpoint": partition.mountpoint,
                "filesystem": partition.fstype,
                "totalSize": get_size(partition_usage.total),
                "usedSize": get_size(partition_usage.used),
                "freeSize": get_size(partition_usage.free),
                "usagePercent": partition_usage.percent
            }
        }
        devices.update(dict_device)
    return devices

def network_info(): # network data gatherer
    net_interfaces = {}
    if_addrs = psutil.net_if_addrs()
    for interface in if_addrs:
        if interface == "lo":  # ignore loopback interface
            continue
        interface_ips = if_addrs[interface]

        ips = []
        for ip in interface_ips:
            ip_data = {
                "family": ip.family,
                "address": ip.address,
                "netmask": ip.netmask,
                "broadcast": ip.broadcast
            }
            ips.append(ip_data)

        dict_interface = {interface: ips}
        net_interfaces.update(dict_interface)
    return net_interfaces

def collect_data():
    uname = platform.uname()                          # system info
    info = platform.freedesktop_os_release()          # linux only!!! (more system info)
    boot_time_timestamp = psutil.boot_time()          # uptime (boot time)
    bt = datetime.fromtimestamp(boot_time_timestamp)  # uptime (boot time)
    cpufreq = psutil.cpu_freq()                       # cpu info
    svmem = psutil.virtual_memory()                   # get the memory details
    swap = psutil.swap_memory()                       # swap details
    devices = disk_info()                             # disk data
    disk_io = psutil.disk_io_counters()               # disk IO statistics since boot
    net_interfaces = network_info()                   # network interfaces
    net_io = psutil.net_io_counters()                 # network IO statistics since boot

    x = {
        "systemInfo": {
            "hostname": uname.node,
            "OS_Name": info["NAME"],
            "OS_Pretty_Name": info["PRETTY_NAME"],
            "OS_Release": info["VERSION_ID"],
            "kernelRelease": uname.release,
            "OS_Type": uname.system,
            "arch": uname.machine
        },
        "date": {
            "day": datetime.now().day,
            "month": datetime.now().month,
            "year": datetime.now().year,
            "hour": datetime.now().hour,
            "minutes": datetime.now().minute,
            "seconds": datetime.now().second,
        },
        "bootTime": f"{bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}",
        "cpuInfo": {
            "physicalCores": psutil.cpu_count(logical=False),
            "logicalCores": psutil.cpu_count(logical=True),
            "minFrequency": f"{cpufreq.min:.2f}",            #MHz
            "maxFrequency": f"{cpufreq.max:.2f}",            #MHz
            "currentFrequency": f"{cpufreq.current:.2f}",    #MHz
            "totalUsagePercent": psutil.cpu_percent()
        },
        "memoryInfo": {
            "totalMem": get_size(svmem.total),
            "freeMem": get_size(svmem.available),
            "usedMem": get_size(svmem.used),
            "usagePercent": svmem.percent
        },
        "swapInfo": {
            "totalSwap": get_size(swap.total),
            "freeSwap": get_size(swap.free),
            "usedSwap": get_size(swap.used),
            "usagePercent": swap.percent
        },
        "diskInfo": {
            "devices" : devices,
            "totalRead": get_size(disk_io.read_bytes),
            "totalWrite": get_size(disk_io.write_bytes),
        },
        "networkInfo": {
            "interfaces": net_interfaces,
            "totalBytesSent": get_size(net_io.bytes_sent),
            "totalBytesRecv":get_size(net_io.bytes_recv)
        }
    }

    json_object = json.dumps(x)
    #with open("sample1.json", "w") as outfile:
    #    outfile.write(json_object)
    return json_object


if __name__ == "__main__":
    while(True):
        configs = get_configs()
        data_json = collect_data()
        sent = send_data(controller_url=configs["controller_url"], json_object=data_json)
        
        sleep(configs["sleep_time"])
