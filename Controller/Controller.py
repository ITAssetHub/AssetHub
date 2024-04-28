# uvicorn main:app --reload
# http://127.0.0.1:6969/docs
#mysql -h {hostname} -u username -p {databasename}

import json
from fastapi import FastAPI, Request, HTTPException
import mysql.connector

# MySQL Connection comands

def create_connection():
    conexao = mysql.connector.connect(host='0.0.0.0',
                                     user='asset_hub_db_user',
                                     password='AssetHubDB2024',
                                     database='db_asset_hub')
    return conexao


def insert_host(data):
    conexao = create_connection()
    cursor = conexao.cursor()
    data_dict = json.loads(data)

    query = f"SELECT hostname FROM tb_host WHERE hostname = '{data_dict['systemInfo']['hostname']}';"
    cursor.execute(query)
    regs = cursor.fetchall()
    print(len(regs))

    if len(regs) >= 1:
        print("máquina já existente, atualizando dados")
        sql = f"UPDATE tb_host SET data = '{data}' WHERE hostname = '{data_dict['systemInfo']['hostname']}';"
        cursor.execute(sql)
        conexao.commit()
    else:
        print("máquina não existente, criando registro")
        sql = f"INSERT INTO tb_host (hostname, data) values ('{data_dict['systemInfo']['hostname']}', '{data}');"
        cursor.execute(sql)
        conexao.commit()

def select_all_hosts():
    conexao = create_connection()
    cursor = conexao.cursor()
    sql = "SELECT * FROM tb_host;"
    cursor.execute(sql)
    regs = cursor.fetchall()
    return regs

def select_host(hostname):
    conexao = create_connection()
    cursor = conexao.cursor()
    sql = f"SELECT * FROM tb_host WHERE hostname = '{hostname}';"
    cursor.execute(sql)
    regs = cursor.fetchall()

    if len(regs) == 0:
        return None
    
    return regs[0]

###############
#  Controller #




###############
##### API #####

app = FastAPI()


# External API!
@app.post("/hosts/post_host")
async def post_host(request: Request):
    data = await request.json()
    print(data)
    insert_host(data)
    
    return {"message": "Dados da máquinas recebidos com sucesso"}

#######

# Internal API
    ## User requests:



    ## Servers requests:

@app.get("/hosts/get_host/{hostname}")
async def get_host(hostname: str):
    host = select_host(hostname)
    if host == None:
        raise HTTPException(status_code=404, detail="Host não encontrado")
    return {"message": host}

@app.get("/hosts/get_host/all_hosts")
async def all_hosts():
    hosts = select_all_hosts()
    if len(hosts) == 0:
        raise HTTPException(status_code=404, detail="Hosts não encontrados")
    return {"message": hosts}
    
    ## Orgs requests:
    ## Hardware requests:
    ## Ambiente requests: 
    ## Site/Datacenter requests:



#Enpoints
#   # Servers
#       POST Hosts --- Feito  (External)
#       GET Host   --- Feito
#       GET Hosts  --- Feito
#       PUT Host/Site
#       PUT Host/Org
#       PUT Host/Hardware
#       PUT Host/Ambiente
#       DELETE                 (DÍFICIL!!!)
#   # Organizations:
#       POST Orgs
#       GET  Orgs
#       GET  Org/Hosts
#       DELETE
#   # Hardware:
#       POST Hardware
#       GET  Hardwares
#       GET  Hardware/Hosts
#       DELETE
#   # Ambiente:
#       POST Ambiente
#       GET  Ambientes
#       GET  Ambiente/Hosts
#       DELETE
#   # Site/Datacenter:
#       POST Site
#       GET  Sites
#       GET  Site/Hosts
#       DELETE
#   # Users
#       POST User
#       PUT  User
#           - Change username
#           - Change password
#           - Change name
#           - Change enabled
#       GET    Users
#       DELETE User
#

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6969)
    
