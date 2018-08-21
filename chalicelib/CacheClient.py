import pymysql
import os
from datetime import datetime
from time import sleep

class CacheClient():
    def __init__(self):
        db_params = self.get_db_params_from_env()
        self._conn = pymysql.connect(**db_params)   
    
    @staticmethod
    def get_db_params_from_env():
        return {
            'host': os.environ.get('CACHE_DB_HOST') or 'localhost',
            'port': os.environ.get('CACHE_DB_PORT') or 3306,
            'db': os.environ.get('CACHE_DB_NAME'),
            'user': os.environ.get('CACHE_DB_USERNAME') or 'admin',
            'passwd': os.environ.get('CACHE_DB_PASSWORD')
        }

    def put(self, store, key, value, ttl=300):
        sql = (
            "INSERT INTO cache (store, key_, value_, expiry_date) "
            "VALUES('{store}', '{key}', '{value}', (NOW() + INTERVAL {ttl} SECOND)) "
            "ON DUPLICATE KEY UPDATE value_='{value}', expiry_date=(NOW() + INTERVAL {ttl} SECOND)"
        )
        with self._conn.cursor() as cur:
            cur.execute(sql.format(
                store=store,
                key=key,
                value=value,
                ttl=ttl
                )
            )
            self._conn.commit()
        
    def get(self, store, key):
        sql = (
            "SELECT value_ FROM cache "
            "WHERE store='{store}' AND key_='{key}' "
            "AND NOW() < expiry_date"
        )
        with self._conn.cursor() as cur:
            cur.execute(sql.format(
                store=store,
                key=key
                )
            )
            self._conn.commit()
            first_row = cur.fetchone()
            if first_row:
                return first_row[0]
            else:
                return None
