from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base


server = 'HARSHIT'
database = 'Harshit'

DB_URL = (
    f"mssql+pyodbc://{server}/{database}?"
    f"trusted_connection=yes&"
    f"driver=ODBC+Driver+17+for+SQL+Server" # Adjust driver name if necessary
)

engine = create_engine(DB_URL,pool_pre_ping=True,future=True)

SessionLocal = sessionmaker(autoflush=False,autocommit = False,bind=engine)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

     