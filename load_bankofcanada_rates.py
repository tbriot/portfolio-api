import json
import pymysql
import os
from datetime import datetime

USD_CAD_RATE_KEY = "FXUSDCAD"

def get_db_params_from_env():
    return {
        'host': os.environ.get('DB_HOST') or 'localhost',
        'port': os.environ.get('DB_PORT') or 3306,
        'db': os.environ.get('DB_NAME'),
        'user': os.environ.get('DB_USERNAME') or 'admin',
        'passwd': os.environ.get('DB_PASSWORD')
    }

def get_db_conn():
    db_params = get_db_params_from_env()
    return pymysql.connect(**db_params)  

def load_file(filepath, conn):
    file = open(filepath, "r")
    p = file.read()
    j = json.loads(p)
    with conn.cursor() as cur:
        for o in j['observations']:
            insert_obs_in_db(cur, o)
            conn.commit()


def insert_obs_in_db(cur, obs):
    date = obs['d']
    rate = obs[USD_CAD_RATE_KEY]["v"]
    sql = (
        "INSERT INTO exchange_rate (date, from_curr, to_curr, type, rate) "
        "VALUES ('{date}', 'USD', 'CAD', 'Noon', {rate})"
    )
    cur.execute(sql.format(
        date=date,
        rate=rate
        )
    )
    

if __name__ == "__main__":
    os.environ['DB_NAME'] = "investornetwork"
    os.environ['DB_PASSWORD'] = "irondesk89"
    conn = get_db_conn()
    load_file("./FX_RATES_DAILY-sd-2017-01-03.json", conn)

