import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    ## Running with PostgreSQL
    # SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')

    ## Running with SQLite
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "instance/data.db")}'
