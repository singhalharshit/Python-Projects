from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "super-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DB_URL: str = (
        "mssql+pyodbc://username:password@localhost:1433/ingestion_db"
        "?driver=ODBC+Driver+17+for+SQL+Server"
    )

settings = Settings()
