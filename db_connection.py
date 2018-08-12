import pymysql
from sshtunnel import SSHTunnelForwarder
import os

DB_HOST = os.environ.get('DB_HOST') or 'investornetwork.co0pqf5yoscl.ca-central-1.rds.amazonaws.com'
DB_PORT = os.environ.get('DB_PORT') or 3306
DB_USERNAME = os.environ.get('DB_USERNAME') or 'admin'
DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'irondesk89'
DB_NAME = os.environ.get('DB_NAME') or 'investornetwork'
DB_CONN_TIMEOUT = os.environ.get('DB_CONN_TIMEOUT') or 10

SSH_HOST = 'ec2-35-183-37-105.ca-central-1.compute.amazonaws.com'
SSH_USERNAME = 'ec2-user'
SSH_KEY_FILE = r'C:\Users\Thomas\.ssh\tbriot-ca-central-1.pem'
LOCALHOST = '127.0.0.1'

def get_db_conn(tunnel):
    if tunnel:
        host = LOCALHOST
        port = tunnel.local_bind_port
    else:
        host = DB_HOST
        port = DB_PORT
    return pymysql.connect(
        host,
        port=port,
        db=DB_NAME,
        user=DB_USERNAME,
        passwd=DB_PASSWORD,
        connect_timeout=DB_CONN_TIMEOUT
    )


def get_ssh_tunnel():
    return SSHTunnelForwarder(
        (SSH_HOST, 22),
        ssh_username = SSH_USERNAME,
        ssh_private_key = SSH_KEY_FILE,
        remote_bind_address=(DB_HOST, 3306)
    )
