
import json
from fastapi import FastAPI, Request, HTTPException, status, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import mysql.connector
import jwt
from jwt.exceptions import InvalidSignatureError, ExpiredSignatureError
from datetime import datetime, timedelta, timezone
import hashlib
from multiprocessing import Process, Manager
import tomllib
import ast
import requests
import uvicorn
from time import sleep
from decimal import Decimal

 
manager = Manager()
conns = manager.list()

SECRET_KEY = "chavesupersecretaenadavulneravel"
ALGORITHM = "HS256"

# MySQL Connection comands

def create_connection():
    conexao = mysql.connector.connect(host='0.0.0.0',
                                     user='asset_hub_db_user',
                                     password='AssetHubDB2024',
                                     database='db_asset_hub')
    return conexao


def insert_host(data, addr):
    conexao = create_connection()
    cursor = conexao.cursor()

    if addr not in conns:
        conns.append(addr)
        update_conns()

    data_dict = json.loads(data)

    query = f"SELECT hostname FROM tb_host WHERE uuid = '{data_dict['uuid']}';"
    cursor.execute(query)
    regs = cursor.fetchall()

    if len(regs) == 0:
        # (uuid, hostname, data, last_report_date, os_name, os_pretty_name, kernel_release, os_type, architecture, boot_time, total_bytes_sent, total_bytes_recv, disk_total_read, disk_total_write)
        sql_host = f"""
            INSERT INTO tb_host (uuid, hostname, data, ipv4, last_report_date, os_name, os_pretty_name, os_release, kernel_release, os_type, architecture, boot_time, total_bytes_sent, total_bytes_recv, disk_total_read, disk_total_write)
            VALUES ('{data_dict['uuid']}', '{data_dict['systemInfo']['hostname']}', '{data}', '{data_dict['systemInfo']['ipv4']}', '{data_dict['date']}', '{data_dict['systemInfo']['OS_Name']}', '{data_dict['systemInfo']['OS_Pretty_Name']}', '{data_dict['systemInfo']['OS_Release']}', '{data_dict['systemInfo']['kernelRelease']}', '{data_dict['systemInfo']['OS_Type']}', '{data_dict['systemInfo']['arch']}', '{data_dict['bootTime']}', '{data_dict['networkInfo']['totalBytesSent']}', '{data_dict['networkInfo']['totalBytesRecv']}', '{data_dict['diskInfo']['totalRead']}', '{data_dict['diskInfo']['totalWrite']}')
            """
        print(sql_host)

        sql_cpu = f"""
            INSERT INTO tb_cpu (host_uuid, physical_cores, logical_cores, minFrequency, maxFrequency, current_frequency, total_cpu_usage_percent)
            VALUES ('{data_dict['uuid']}', {data_dict['cpuInfo']['physicalCores']}, {data_dict['cpuInfo']['logicalCores']}, '{data_dict['cpuInfo']['minFrequency']}', '{data_dict['cpuInfo']['maxFrequency']}', '{data_dict['cpuInfo']['currentFrequency']}', {data_dict['cpuInfo']['totalUsagePercent']})
        """

        sql_mem = f"""
            INSERT INTO tb_memory (host_uuid, total_memory, free_memory, used_memory, memory_usage_percent)
            VALUES ('{data_dict['uuid']}', '{data_dict['memoryInfo']['totalMem']}', '{data_dict['memoryInfo']['freeMem']}', '{data_dict['memoryInfo']['usedMem']}', {data_dict['memoryInfo']['usagePercent']})
        """

        sql_swap = f"""
            INSERT INTO tb_swap (host_uuid, total_swap, free_swap, used_swap, swap_usage_percent)
            VALUES ('{data_dict['uuid']}', '{data_dict['swapInfo']['totalSwap']}', '{data_dict['swapInfo']['freeSwap']}', '{data_dict['swapInfo']['usedSwap']}', {data_dict['swapInfo']['usagePercent']})
        """

        cursor.execute(sql_host) # tb_host INSERT
        cursor.execute(sql_cpu)  # tb_cpu INSERT
        cursor.execute(sql_mem)  # tb_memory INSERT
        cursor.execute(sql_swap) # tb_swap INSERT
        
        devices = data_dict["diskInfo"]["devices"]
        for device_name, device_info in devices.items():
            if data_dict['systemInfo']['OS_Type'] == "Windows":
                sql_disk = f"""
                    INSERT INTO tb_disk_partition (host_uuid, device, mountpoint, filesystem, disk_total_size, disk_used_size, disk_free_size, disk_usage_percent)
                    VALUES ('{data_dict['uuid']}', '{device_name}\\', '{device_info['mountpoint']}\\', '{device_info['filesystem']}', '{device_info['totalSize']}', '{device_info['usedSize']}','{device_info['freeSize']}', {device_info['usagePercent']})
                """
            elif data_dict['systemInfo']['OS_Type'] == "Linux":
                sql_disk = f"""
                    INSERT INTO tb_disk_partition (host_uuid, device, mountpoint, filesystem, disk_total_size, disk_used_size, disk_free_size, disk_usage_percent)
                    VALUES ('{data_dict['uuid']}', '{device_name}', '{device_info['mountpoint']}', '{device_info['filesystem']}', '{device_info['totalSize']}', '{device_info['usedSize']}','{device_info['freeSize']}', {device_info['usagePercent']})
                """
            cursor.execute(sql_disk)

        interfaces = data_dict["networkInfo"]["interfaces"]
        for interface_name, interface_data in interfaces.items():
            sql_interface = f"""
                INSERT INTO tb_network_interface (host_uuid, interface)
                VALUES ('{data_dict['uuid']}', '{interface_name}')
            """
            cursor.execute(sql_interface)
            conexao.commit()

            sql_select_interface = f"SELECT id_network_interface FROM tb_network_interface WHERE host_uuid = '{data_dict['uuid']}' AND interface = '{interface_name}'"
            cursor.execute(sql_select_interface)

            result = cursor.fetchall()
            interface_id = result[0][0]

            for data in interface_data:
                sql_addr = f"""
                    INSERT INTO tb_interface_data (family, address, netmask, broadcast, id_network_interface)
                    VALUES ({data['family']}, '{data['address']}', '{data['netmask']}', '{data['broadcast']}', '{interface_id}')
                """
                cursor.execute(sql_addr)
            conexao.commit()

    else:
        # TB_CPU UPDATE
        sql_select_cpu_percent = f"""
            SELECT total_cpu_usage_percent FROM tb_cpu WHERE host_uuid = '{data_dict['uuid']}'
        """
        cursor.execute(sql_select_cpu_percent)
        result = cursor.fetchall()
        cpu_percent = result[0][0]

        sql_select_cpu_history = f"""
            SELECT cpu_usage_percent_history FROM tb_cpu WHERE host_uuid = '{data_dict['uuid']}'
        """
        cursor.execute(sql_select_cpu_history)
        result = cursor.fetchall()
        cpu_history = result[0][0]
        
        if cpu_history == None:
            hist = [cpu_percent]
        else:
            hist = json.loads(cpu_history)
            hist.append(cpu_percent)
        

        hist = [float(x) if isinstance(x, Decimal) else x for x in hist]
        if len(hist) > 24:
            hist = hist[-24:]
        cpu_mean = sum(hist) / len(hist)
     
        updated_history_json = json.dumps(hist)
        query_update = f"""
            UPDATE `db_asset_hub`.`tb_cpu`
            SET 
                `physical_cores` = {data_dict['cpuInfo']['physicalCores']}, 
                `logical_cores` = {data_dict['cpuInfo']['logicalCores']}, 
                `minFrequency` = '{data_dict['cpuInfo']['minFrequency']}', 
                `maxFrequency` = '{data_dict['cpuInfo']['maxFrequency']}', 
                `current_frequency` = '{data_dict['cpuInfo']['currentFrequency']}', 
                `total_cpu_usage_percent` = {data_dict['cpuInfo']['totalUsagePercent']},
                `cpu_usage_percent_history` = '{updated_history_json}',
                `cpu_mean` = '{cpu_mean}'
            WHERE 
                `host_uuid` = '{data_dict['uuid']}';
            """
        cursor.execute(query_update)
        conexao.commit()

        #######
        # TB_MEMORY UPDATE
        sql_select_mem_percent = f"""
            SELECT memory_usage_percent FROM tb_memory WHERE host_uuid = '{data_dict['uuid']}'
        """
        cursor.execute(sql_select_mem_percent)
        result = cursor.fetchall()
        mem_percent = result[0][0]

        sql_select_mem_history = f"""
            SELECT memory_usage_percent_history FROM tb_memory WHERE host_uuid = '{data_dict['uuid']}'
        """
        cursor.execute(sql_select_mem_history)
        result = cursor.fetchall()
        mem_history = result[0][0]

        if mem_history == None:
            hist = [mem_percent]
        else:
            hist = json.loads(mem_history)
            hist.append(mem_percent)

        hist = [float(x) if isinstance(x, Decimal) else x for x in hist]
        if len(hist) > 24:
            hist = hist[-24:]
        memory_mean = sum(hist) / len(hist)
     
        updated_history_json = json.dumps(hist)
        query_update = f"""
            UPDATE tb_memory
            SET 
                total_memory = '{data_dict['memoryInfo']['totalMem']}',
                free_memory = '{data_dict['memoryInfo']['freeMem']}',
                used_memory = '{data_dict['memoryInfo']['usedMem']}',
                memory_usage_percent = {data_dict['memoryInfo']['usagePercent']},
                memory_usage_percent_history = '{hist}',
                memory_mean = '{memory_mean}'
            WHERE 
                `host_uuid` = '{data_dict['uuid']}';
            """
        cursor.execute(query_update)
        conexao.commit()

        #######
        # TB_SWAP UPDATE
        sql_update_swap = f"""
            UPDATE tb_swap
            SET 
                total_swap = '{data_dict['swapInfo']['totalSwap']}',
                free_swap = '{data_dict['swapInfo']['freeSwap']}',
                used_swap = '{data_dict['swapInfo']['usedSwap']}',
                swap_usage_percent = {data_dict['swapInfo']['usagePercent']}
            WHERE 
                `host_uuid` = '{data_dict['uuid']}';
        """
        cursor.execute(sql_update_swap)
        conexao.commit()

        #######
        # TB_DISK_PARTITION UPDATE (dado as complicações de tempo, farei um DELETE e um INSERT)
        sql_delete_disk_partition = f"""
            DELETE FROM tb_disk_partition
            WHERE host_uuid = '{data_dict['uuid']}';
        """
        cursor.execute(sql_delete_disk_partition)
        conexao.commit()

        devices = data_dict["diskInfo"]["devices"]
        for device_name, device_info in devices.items():
            if data_dict['systemInfo']['OS_Type'] == "Windows":
                sql_disk = f"""
                    INSERT INTO tb_disk_partition (host_uuid, device, mountpoint, filesystem, disk_total_size, disk_used_size, disk_free_size, disk_usage_percent)
                    VALUES ('{data_dict['uuid']}', '{device_name}\\', '{device_info['mountpoint']}\\', '{device_info['filesystem']}', '{device_info['totalSize']}', '{device_info['usedSize']}','{device_info['freeSize']}', {device_info['usagePercent']})
                """
            elif data_dict['systemInfo']['OS_Type'] == "Linux":
                sql_disk = f"""
                    INSERT INTO tb_disk_partition (host_uuid, device, mountpoint, filesystem, disk_total_size, disk_used_size, disk_free_size, disk_usage_percent)
                    VALUES ('{data_dict['uuid']}', '{device_name}', '{device_info['mountpoint']}', '{device_info['filesystem']}', '{device_info['totalSize']}', '{device_info['usedSize']}','{device_info['freeSize']}', {device_info['usagePercent']})
                """
                
            cursor.execute(sql_disk)
        conexao.commit()

        #######
        # TB_NETWORK_INTERACE and TB_INTERFACE_DATA UPDATE (dado as complicações de tempo, farei um DELETE e um INSERT)
        sql_delete_interface_data = f"""
            DELETE FROM tb_interface_data
            WHERE id_network_interface IN (
                SELECT id_network_interface FROM tb_network_interface WHERE host_uuid = '{data_dict['uuid']}'
            );
        """
        cursor.execute(sql_delete_interface_data)
        conexao.commit()

        sql_delete_interface = f"""
            DELETE FROM tb_network_interface
            WHERE host_uuid = '{data_dict['uuid']}';
        """

        cursor.execute(sql_delete_interface)
        conexao.commit()
        
        interfaces = data_dict["networkInfo"]["interfaces"]
        for interface_name, interface_data in interfaces.items():
            sql_interface = f"""
                INSERT INTO tb_network_interface (host_uuid, interface)
                VALUES ('{data_dict['uuid']}', '{interface_name}')
            """
            cursor.execute(sql_interface)
            conexao.commit()

            sql_select_interface = f"SELECT id_network_interface FROM tb_network_interface WHERE host_uuid = '{data_dict['uuid']}' AND interface = '{interface_name}'"
            cursor.execute(sql_select_interface)

            result = cursor.fetchall()
            interface_id = result[0][0]

            for data in interface_data:
                sql_addr = f"""
                    INSERT INTO tb_interface_data (family, address, netmask, broadcast, id_network_interface)
                    VALUES ({data['family']}, '{data['address']}', '{data['netmask']}', '{data['broadcast']}', {interface_id});
                """
                cursor.execute(sql_addr)
                
            conexao.commit()
        
            
        ########
        # TB_HOST UPDATE
        sql_select_read_write_send_recv = f"""
            SELECT total_bytes_sent, total_bytes_recv, disk_total_read, disk_total_write
            FROM tb_host
            WHERE uuid = '{data_dict['uuid']}';
        """
        cursor.execute(sql_select_read_write_send_recv)
        result = cursor.fetchone()
        total_bytes_sent, total_bytes_recv, disk_total_read, disk_total_write = result

        sql_select_hist = f"""
            SELECT network_history, disk_history
            FROM tb_host
            WHERE uuid = '{data_dict['uuid']}';
        """
        cursor.execute(sql_select_hist)
        result = cursor.fetchone()
        network_history, disk_history = result

        if network_history is None:
            network_history = [[total_bytes_sent, total_bytes_recv]]
        else:
            network_history = json.loads(network_history)
            network_history.append([total_bytes_sent, total_bytes_recv])
            if len(network_history) > 24:
                network_history = network_history[-24:]

        if disk_history is None:
            disk_history = [[disk_total_read, disk_total_write]]
        else:
            disk_history = json.loads(disk_history)
            disk_history.append([disk_total_read, disk_total_write])
            if len(disk_history) > 24:
                disk_history = disk_history[-24:]

        data = json.dumps(data)
        disk_history = json.dumps(disk_history)
        network_history = json.dumps(network_history)


        sql_update_host = f"""
            UPDATE tb_host
            SET 
                hostname = '{data_dict['systemInfo']['hostname']}',
                data = '{data}',
                ipv4 = '{data_dict['systemInfo']['ipv4']}',
                last_report_date = '{data_dict['date']}',
                os_name = '{data_dict['systemInfo']['OS_Name']}',
                os_pretty_name = '{data_dict['systemInfo']['OS_Pretty_Name']}',
                os_release = '{data_dict['systemInfo']['OS_Release']}',
                kernel_release = '{data_dict['systemInfo']['kernelRelease']}',
                os_type = '{data_dict['systemInfo']['OS_Type']}',
                architecture = '{data_dict['systemInfo']['arch']}',
                boot_time = '{data_dict['bootTime']}',
                total_bytes_sent = '{data_dict['networkInfo']['totalBytesSent']}',
                total_bytes_recv = '{data_dict['networkInfo']['totalBytesRecv']}',
                disk_total_read = '{data_dict['diskInfo']['totalRead']}',
                disk_total_write = '{data_dict['diskInfo']['totalWrite']}',
                network_history = '{network_history}',
                disk_history = '{disk_history}'
            WHERE uuid = '{data_dict['uuid']}';
        """
        cursor.execute(sql_update_host)

    conexao.commit()

# Função para converter objetos não serializáveis (como datetime) em strings
def custom_json_handler(obj):
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')  # Converte datetime para string no formato desejado
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def select_all_hosts():
    try:
        conexao = create_connection()
        cursor = conexao.cursor()
        sql = "SELECT uuid, hostname, os_pretty_name, ambiente, hardware, last_report_date, description FROM tb_host;"
        cursor.execute(sql)

        # Formats to JSON
        column_names = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        result = [dict(zip(column_names, row)) for row in rows]
        
        print(result)

        return result
    finally:
        cursor.close()
        conexao.close()

def convert_decimals_to_floats(input_dict):
    output_dict = {}
    for key, value in input_dict.items():
        if isinstance(value, Decimal):
            output_dict[key] = float(value)
        elif isinstance(value, str) and value.startswith('[') and value.endswith(']'):
            # Converte a string que representa uma lista para uma lista real
            output_dict[key] = ast.literal_eval(value)
        else:
            output_dict[key] = value
    return output_dict

def select_host(uuid):
    try:
        conexao = create_connection()
        cursor = conexao.cursor()

        sql = f"SELECT uuid, hostname, ipv4, last_report_date, os_pretty_name, architecture, boot_time, description FROM tb_host WHERE uuid = '{uuid}';"
        cursor.execute(sql)
        column_names = [column[0] for column in cursor.description]
        regs = cursor.fetchall()
        result = [dict(zip(column_names, row)) for row in regs]
        info = result[0]

        sql = f"SELECT logical_cores, total_cpu_usage_percent, cpu_usage_percent_history FROM tb_cpu WHERE host_uuid = '{uuid}';"
        cursor.execute(sql)
        column_names = [column[0] for column in cursor.description]
        regs = cursor.fetchall()
        result = [dict(zip(column_names, row)) for row in regs]
        cpu = convert_decimals_to_floats(result[0])

        sql = f"SELECT total_memory, memory_usage_percent, memory_usage_percent_history FROM tb_memory WHERE host_uuid = '{uuid}';"
        cursor.execute(sql)
        column_names = [column[0] for column in cursor.description]
        regs = cursor.fetchall()
        result = [dict(zip(column_names, row)) for row in regs]
        memory = convert_decimals_to_floats(result[0])
        
        sql = f"SELECT total_bytes_sent, total_bytes_recv FROM tb_host WHERE uuid = '{uuid}';"
        cursor.execute(sql)
        column_names = [column[0] for column in cursor.description]
        regs = cursor.fetchall()
        result = [dict(zip(column_names, row)) for row in regs]
        network_usage = result[0]

        sql = f"SELECT disk_total_read, disk_total_write FROM tb_host WHERE uuid = '{uuid}';"
        cursor.execute(sql)
        column_names = [column[0] for column in cursor.description]
        regs = cursor.fetchall()
        result = [dict(zip(column_names, row)) for row in regs]
        disk_usage = result[0]

        sql = f"SELECT device, mountpoint, filesystem, disk_total_size, disk_used_size, disk_free_size, disk_usage_percent FROM tb_disk_partition WHERE host_uuid = '{uuid}';"
        cursor.execute(sql)
        column_names = [column[0] for column in cursor.description]
        regs = cursor.fetchall()
        result = [dict(zip(column_names, row)) for row in regs]
        temp = []
        for entry in result:
            entry = convert_decimals_to_floats(entry)
            temp.append(entry)
        disks = temp

        sql = f"SELECT id_network_interface, interface FROM tb_network_interface WHERE host_uuid = '{uuid}';"
        cursor.execute(sql)
        regs = cursor.fetchall()
        interfaces = regs
        temp = []
        for interface in interfaces:
            print(interface)
            sql_interface_data = f"SELECT family, address, netmask FROM tb_interface_data WHERE id_network_interface = {interface[0]};"
            cursor.execute(sql_interface_data)
            column_names = [column[0] for column in cursor.description]
            data = cursor.fetchall()
            data = [dict(zip(column_names, row)) for row in data]
            temp.append({"Interface": interface[1], "Interface_Data": data})
        
        net_interfaces = temp

        final_result = {
            "INFO": info,
            "CPU_DATA": cpu,
            "MEMORY_DATA": memory,
            "NETWORK_USAGE": network_usage,
            "DISK_USAGE":disk_usage,
            "DISKS": disks,
            "NETWORK_INTERFACES": net_interfaces,
            }

        json_result = final_result
        
        print(json_result)
        if len(regs) == 0:
            return None
        
        return json_result
    finally:
        cursor.close()
        conexao.close()

def select_all_hardware():
    try:
        conexao = create_connection()
        cursor = conexao.cursor()
        sql = "SELECT * FROM tb_hardware;"
        cursor.execute(sql)
        regs = cursor.fetchall()
        return regs
    finally:
        cursor.close()
        conexao.close()

def select_all_hosts_by_os(os_type):
    try:
        conexao = create_connection()
        cursor = conexao.cursor()
        sql = f"SELECT * FROM tb_host WHERE os_type = '{os_type}';"
        cursor.execute(sql)
        regs = cursor.fetchall()
        return regs
    finally:
        cursor.close()
        conexao.close()


######################
##### Controller #####

def broadcast_command(command):
    print(f"BROADCASTING COMMAND: {command}")
    print(conns)
    for agent in conns:
        try:
            if command == "UPDATE":   # Podemos paralelizar esse processo?
                response = requests.get(url=f"http://{agent}:8888/update", timeout=5)
                print(f"{agent} {command} {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"Timeout Error {agent}")
        except Exception as e:
            print(e)

def unicast_command(addr, command): 
    print(f"UNICASTING COMMAND: {command} TO: {addr}")
    try:
        if command == "UPDATE":
            response = requests.get(url=f"http://{addr}:8888/update")
            print(f"{addr} {command} {response.status_code}")
    except Exception as e:
        print(e)

###############
##### API #####

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir qualquer origem
    #allow_credentials=True,
    allow_methods=["*"],  # Permitir todos os métodos HTTP (GET, POST, etc.)
    allow_headers=["*"],  # Permitir todos os cabeçalhos
)

# External API!
@app.post("/hosts/post_host")
async def post_host(request: Request):
    data = await request.json()
    addr = request.client.host
    print(data)
    print(request.client.host)
    insert_host(data, addr)
    
    return {"message": "Dados da máquinas recebidos com sucesso"}

#######
# Internal API     (DEPOIS kkkkkkk)
## User requests:

async def authenticate_user(username: str, password: str):

    password = password.encode("utf-8")
    user_hash = hashlib.sha256(password)
    user_hash = user_hash.hexdigest()

    conexao = create_connection()
    cursor = conexao.cursor()
    sql = f"SELECT * FROM tb_passwd WHERE username = '{username}';"
    cursor.execute(sql)
    regs = cursor.fetchall()
    print(regs[0][2])

    if regs[0][2] == user_hash:
        return True
    return False

def verify_token(token: str = Depends(OAuth2PasswordBearer(tokenUrl="token"))):
    try:
        # Verifica se o token é válido e decodifica suas informações
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Retorna as informações decodificadas do token
        return payload
    except InvalidSignatureError:
        # Se ocorrer um erro ao verificar o token, levanta uma exceção HTTP 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password
    if not await authenticate_user(username, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Gera a data de expiração do token
    expires_delta = timedelta(hours=2)
    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = {"sub": username, "exp": expire}
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": encoded_jwt}


    ## Servers requests:


#####################
## Server requests ##
# token: str = Depends(verify_token)

@app.get("/conns")
async def connects():
    array = []
    for conn in conns:
        array.append(conn)

    return {"Conns": array}

@app.get("/dashboard/cpu_info")
async def cpu_info():   # IMPLEMENTAR APÓS ATUALIZAÇÃO DO BANCO!!!!
    from random import randint
    
    # PLACEHOLDER
    cpu_means = []
    for i in range(0, 24):
        cpu_means.append(float(randint(1, 97)))

    critical_hosts = {
        f"fakehost0{randint(1, 20)}": {
            "cpu_usage": randint(90, 99),
            "uuid": "fake-uuid-124313-12341234"
            },
        f"fakehost0{randint(1, 20)}": {
            "cpu_usage": randint(90, 99),
            "uuid": "fake-uuid-1243124-1243441"
            }
    }
        
    warning_hosts = {
        f"fakehost0{randint(20, 40)}": {
            "cpu_usage": randint(60, 89),
            "uuid": "fake-uuid-12s313-123g1234"
            },
        f"fakehost0{randint(20, 40)}": {
            "cpu_usage": randint(60, 89),
            "uuid": "fake-uuid-1240124-124t441"
            }
    }

    data = {
        "CPU_MEAN": cpu_means,
        "HOSTS":{
            "CRITICAL HOSTS": critical_hosts,
            "WARNING HOSTS": warning_hosts
        }
    }

    return data

@app.get("/hosts/update")
async def update():
    broadcast_command(command="UPDATE")

@app.get("/hosts/get_host/{uuid}")
async def get_host(uuid: str):
    host = select_host(uuid)
    if host == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host não encontrado")
    return {"Host": host}

@app.put("/hosts/update_host_description/{uuid}")
async def update_description(uuid: str, new_description: str):  # isso aqui passa vibes de SQL injection...
    try: 
        conexao = create_connection()
        cursor = conexao.cursor()
        sql_update_descrip = f"""
            UPDATE tb_host
            SET
                description = '{new_description}'
            WHERE
                `uuid` = '{uuid}';
        """
        cursor.execute(sql_update_descrip)
        conexao.commit()
        return Response(status_code=200)
    except Exception as e:
        print(e)
        return {"ERROR": "Failed to update host description"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        cursor.close()
        conexao.close()

@app.delete("/hosts/delete_host/{hostname}") # TERMINE ISSO!!!!!
async def delete_host(hostname: str):
    pass

@app.get("/hosts/get_hosts")
async def all_hosts():
    hosts = select_all_hosts()
    if len(hosts) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hosts não encontrados")
    return {"Hosts": hosts}

@app.get("/hosts/get_hosts_count")
async def get_hosts_count():
    hosts = select_all_hosts()
    return {"Host_Count": len(hosts)}

@app.get('/hosts/get_host_ostype_count')
async def get_host_ostype_count():
    hosts_linux = select_all_hosts_by_os(os_type='Linux')
    hosts_windows = select_all_hosts_by_os(os_type='Windows')
    return {"Linux_Hosts": len(hosts_linux), "Windows_Hosts": len(hosts_windows)}

@app.get('/hosts/os_types_count/')
async def os_types_count():  #TERMINE ISSO !!!!!
    pass 

## Orgs requests:
## Hardware requests:
@app.get("/hardware/get_hardware_count")
async def get_hardware_count():
    hardwares = select_all_hardware()
    return {"Hardware_Count": len(hardwares)}

## Ambiente requests: 
## Site/Datacenter requests:


def update_thread():
    cicle = 300 # Ciclo de update 

    current_cicle = 0
    while(True):
        sleep(cicle)
        if current_cicle == 12: # Após 12 ciclos, carregar médias do ambiente para dashboard
            conexao = create_connection()
            cursor = conexao.cursor()

            hist_cpu_query = "SELECT cpu_mean_history FROM tb_dashboard WHERE id = 1"
            cursor.execute(hist_cpu_query)
            result = cursor.fetchall()
            hist_cpu = result[0][0]

            hist_memory_query = "SELECT memory_mean_history FROM tb_dashboard WHERE id = 1"
            cursor.execute(hist_memory_query)
            result = cursor.fetchall()
            hist_memory = result[0][0]

            cpu_mean_query = "SELECT SUM(cpu_mean) / COUNT(*) AS media FROM tb_cpu"
            cursor.execute(cpu_mean_query)
            result = cursor.fetchall()
            cpu_mean = result[0][0]

            memory_mean_query = "SELECT SUM(memory_mean) / COUNT(*) AS media FROM tb_memory"
            cursor.execute(memory_mean_query)
            result = cursor.fetchall()
            memory_mean = result[0][0]

            if hist_cpu == None:
                hist_cpu = [cpu_mean]
            else:
                hist_cpu = json.loads(hist_cpu)
                hist_cpu.append(cpu_mean)
                hist_cpu = [float(x) if isinstance(x, Decimal) else x for x in hist_cpu]

            if hist_memory == None:
                hist_memory = [memory_mean]
            else:
                hist_memory = json.loads(hist_memory)
                hist_memory.append(memory_mean)
                hist_memory = [float(x) if isinstance(x, Decimal) else x for x in hist_memory]

            update_dashboard = f"""
                UPDATE tb_dashboard
                SET 
                    `cpu_mean_history` = '{hist_cpu}',
                    `memory_mean_history` = '{hist_memory}'
                WHERE
                    id = 1
            """
            cursor.execute(update_dashboard)
            conexao.commit()
            cursor.close()
            conexao.close()
            current_cicle = 0 # RESET CICLE COUNTER

        response = requests.get(url="http://127.0.0.1:6969/hosts/update")
        print(response.status_code)

        current_cicle += 1

def update_conns():
    conexao = create_connection()
    cursor = conexao.cursor()
    temp = []
    for conn in conns:
        temp.append(conn)
    temp = json.dumps(temp)

    sql_update = f"UPDATE tb_host_list SET hosts = '{temp}' WHERE id = 1"
    
    cursor.execute(sql_update)
    conexao.commit()
    cursor.close()
    conexao.close()
    get_conns()


def get_conns():
    conexao = create_connection()
    cursor = conexao.cursor()

    sql = "SELECT hosts FROM tb_host_list WHERE id = 1"
    cursor.execute(sql)
    hosts = cursor.fetchall()
    if len(hosts) > 0:
        hosts = json.loads(hosts[0][0])
        for i in range(len(conns)):
            conns.pop(0)
        for host in hosts:
            conns.append(host)


if __name__ == "__main__": 

    get_conns()

    upd = Process(target=update_thread)
    upd.start()
    
    uvicorn.run(app, host="0.0.0.0", port=6969)
    upd.join()
    
