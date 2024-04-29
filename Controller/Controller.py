# uvicorn main:app --reload
# http://127.0.0.1:6969/docs
#mysql -h {hostname} -u username -p {databasename}

import json
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import mysql.connector
import jwt
from jwt.exceptions import InvalidSignatureError
from datetime import datetime, timedelta, timezone
import hashlib


SECRET_KEY = "chavesupersecretaenadavulneravel"
ALGORITHM = "HS256"

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
    try:
        conexao = create_connection()
        cursor = conexao.cursor()
        sql = "SELECT * FROM tb_host;"
        print("SQL:", sql)  # Debug
        cursor.execute(sql)
        regs = cursor.fetchall()
        print("Número de registros encontrados:", len(regs))  # Debug
        return regs
    finally:
        cursor.close()
        conexao.close()


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

@app.get("/hosts/get_host/{hostname}")
async def get_host(hostname: str, token: str = Depends(verify_token)):
    host = select_host(hostname)
    if host == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host não encontrado")
    return {"message": host}

@app.get("/hosts/get_all_hosts")
async def all_hosts(token: str = Depends(verify_token)):
    hosts = select_all_hosts()
    if len(hosts) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hosts não encontrados")
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
#
#
#Enpoints:
#   /token
#   /hosts/get_host/{hostname}
#   /hosts/get_all_hosts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6969)
