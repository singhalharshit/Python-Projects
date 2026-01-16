from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE = 'postgres://user:password@localhost:5432/postgres'

engine= create_engine(SQLALCHEMY_DATABASE)

session = sessionmaker(autocommit = False,autoflush=False,bind=engine)

