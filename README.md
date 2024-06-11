# AssetHub

## Controller Dependencies
RHEL 8
  Dependências:
  - Python >= 3.11
  - dnf install gcc python3.11-devel python3.11-pip mysql-server
  - pip install fastapi mysql-connector-python PyJWT uvicorn python-multipart

## Agent Dependencies
RHEL 9
  Dependências:
  - Python >= 3.11
  - dnf install gcc python3.11-devel python3.11-pip 
  - pip install psutil requests tomllib
