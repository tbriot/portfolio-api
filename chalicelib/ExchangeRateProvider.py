import pymysql
import os
from datetime import datetime

class ExchangeRateProvider:
    def __init__(self):
        db_params = self.get_db_params_from_env()
        self._conn = pymysql.connect(**db_params)   
    
    @staticmethod
    def get_db_params_from_env():
        return {
            'host': os.environ.get('CURCONVERTER_DB_HOST') or 'localhost',
            'port': os.environ.get('CURCONVERTER_DB_PORT') or 3306,
            'db': os.environ.get('CURCONVERTER_DB_NAME'),
            'user': os.environ.get('CURCONVERTER_DB_USERNAME') or 'admin',
            'passwd': os.environ.get('CURCONVERTER_DB_PASSWORD')
        }
    
    def get_rate(self, from_c, to_c, date=None):
        if not date:
            date = datetime.now().strftime(r"%Y-%m-%d")

        sql = (
            "SELECT rate FROM exchange_rate "
            "WHERE from_curr='{from_c}' AND to_curr='{to_c}' "
            "AND type='{type}' "
            "AND date='{date}'"
        )
        with self._conn.cursor() as cur:
            r = cur.execute(sql.format(
                    date=date,
                    from_c=from_c,
                    to_c=to_c,
                    type='Noon'
                )
            )
            self._conn.commit()
            first_row = cur.fetchone()
            if first_row:
                return first_row[0]
            else:
                raise Exception("Could not find rate for date={}, from={}, to={}".format(date, from_c, to_c))

if __name__ == "__main__":
    os.environ['CURCONVERTER_DB_NAME'] = "investornetwork"
    os.environ['CURCONVERTER_DB_PASSWORD'] = "irondesk89"
    p = ExchangeRateProvider()
    print("rate=" + str(p.get_rate('USD', 'CAD', '2017-02-16')))
        