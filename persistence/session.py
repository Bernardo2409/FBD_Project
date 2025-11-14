import configparser
import functools
from pathlib import Path
import pyodbc


@functools.cache
def conn_string() -> str:
    config_file = Path("conf.ini")
    assert config_file.exists(), "conf.ini file not found"

    config = configparser.ConfigParser()
    config.read(config_file)

    server = config["database"]["server"]
    db_name = config["database"]["name"]
    username = config["database"]["username"]
    password = config["database"]["password"]

    return f"DRIVER={{/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.10.so.6.1}};SERVER={server};DATABASE={db_name};UID={username};PWD={password};ThrustCertificate=yes;"


def create_connection():
    """Cria uma conexão com o banco de dados SQL Server."""
    conn_string_val = conn_string()
    return pyodbc.connect(conn_string_val)
