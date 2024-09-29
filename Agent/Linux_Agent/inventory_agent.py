import psutil
import platform
from datetime import datetime
from time import sleep
import json
import requests
import tomllib
import logging
from logging.handlers import RotatingFileHandler
from multiprocessing import Process
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import socket
from random import randint
import uuid
import os


# tamanho máximo de log = 5 MB
rfh = RotatingFileHandler(filename='inventory_agent.log', mode='a',maxBytes=5242880, backupCount=1, encoding=None, delay=0)
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] - %(message)s", handlers=[rfh])

def get_configs():     # Coleta dados de configuração do agente (sujeito a mudanças)
    with open("config.toml", "rb") as f:
        data = tomllib.load(f)
    logging.info(f"config.toml lido com sucesso! configs={data}")
    return data

def get_or_create_uuid():
    # Verifica se o UUID já foi gerado e salvo
    filename = "uuid.txt"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return f.read().strip()
    
    # Gera um novo UUID e salva no arquivo
    unique_id = str(uuid.uuid4())
    with open(filename, 'w') as f:
        f.write(unique_id)
    
    return unique_id


#### HTTP POST #####
def send_data(json_object, controller_url):
    try:
        response = requests.post(url=f"{controller_url}/hosts/post_host", json=json_object)
        logging.info(response)
        return response.status_code
    except Exception as e:
        logging.error(e)
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
    agent_uuid = get_or_create_uuid()
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
        "uuid": agent_uuid,
        "systemInfo": {
            "hostname": uname.node,
            "OS_Name": info["NAME"],
            "OS_Pretty_Name": info["PRETTY_NAME"],
            "OS_Release": info["VERSION_ID"],
            "kernelRelease": uname.release,
            "OS_Type": uname.system,
            "arch": uname.machine
        },
        "date": f"{datetime.now().year}-{datetime.now().month:02d}-{datetime.now().day:02d} {datetime.now().hour:02d}:{datetime.now().minute:02d}:{datetime.now().second:02d}",
        "bootTime": f"{bt.year}-{bt.month}-{bt.day} {bt.hour}:{bt.minute}:{bt.second}",
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

    json_object = json.dumps(x, indent=4)
    logging.debug(f"Dados coletados={json_object}")
    return json_object

# Essa função é engraçada... não estou fazendo conexão alguma, só estou usando o protocolo UDP
# para simular uma conexão e pegar o "IP principal" da máquina agente, ou seja, o IP
# que consegue se conectar ao controlador.
def get_main_ip(controller_ip):
    # Conecta-se ao IP da máquina controladora para determinar o IP da interface ativa
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Se conecta ao IP da máquina controladora, SEM ENVIAR PACOTES
        s.connect((controller_ip, 80))
        ip_address = s.getsockname()[0]
    finally:
        s.close()
        return ip_address
    

### API PARA RECEBER COMANDOS ###

api = FastAPI()


@api.get("/update")
def update():
    configs = get_configs()
    data_json = collect_data()
    send_data(controller_url=configs["api_url"], json_object=data_json)

# Isso aqui é uma medida para caso o Controller caia, demora para ser executado
# irá rodar em outra Thread
#def failsafe():
#    while(True):
#        # Evita com que sejam enviadas muitas requisições simultâneas.
#        sleep(randint(1200, 2100)) #20 - 35 min
#        update()


if __name__ == "__main__":
    logging.info("Starting inventory_agent.py...")
    configs = get_configs()

    # Primeiro envio de dados e cadastro no Controller
    data_json = collect_data()
    send_data(controller_url=configs["api_url"], json_object=data_json)
    
    # Pega endereço da interface principal da máquina e sobe api
    main_ip = get_main_ip(controller_ip=configs['controller_ip'])
    uvicorn.run(api, host=main_ip, port=8888)
