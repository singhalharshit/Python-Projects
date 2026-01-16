from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker



server = 'HARSHIT'
database = 'AUTH'

SQLALCHEMY_DATABASE =(
    f"mssql+pyodbc://{server}/{database}?"
    f"trusted_connection=yes&"
    f"driver=ODBC+Driver+17+for+SQL+Server" # Adjust driver name if necessary
)

engine = create_engine(SQLALCHEMY_DATABASE)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
