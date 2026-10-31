import os
from sqlalchemy.engine import URL

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'local-development-only-secret')
    SQLALCHEMY_DATABASE_URI = URL.create(
        'mysql+pymysql', username=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', '#RootPassword123'),
        host=os.getenv('MYSQL_HOST', 'localhost'), port=3306,
        database='campus_lab_booking')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
