from sqlalchemy import create_engine, MetaData

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata = MetaData()

def get_database_url():
    return DATABASE_URL