from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

#config sqlite
SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
SECRET_KEY = os.getenv("SECRET_KEY")

#teste de conexão

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    connection = engine.connect()
    print("Banco conectado")
except Exception as e:
    print(f"Erro ao conectar ao bano de dados {e}")


Base = declarative_base()