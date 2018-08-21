import pymysql
import os

def get_db_conn():
    return pymysql.connect(
        os.environ.get('DB_HOST') or "localhost",
        port=os.environ.get('DB_PORT') or 3306,
        db= os.environ.get('DB_NAME') or 'investornetwork',
        user=os.environ.get('DB_USERNAME') or 'admin',
        passwd=os.environ.get('DB_PASSWORD'),
        connect_timeout=os.environ.get('DB_CONN_TIMEOUT') or 10
    )
