import requests
from datetime import datetime, timedelta

API_KEY = 'JVI5ZU3MASJ5J5MS'

RESP_TOP_LVL_KEY = 'Realtime Currency Exchange Rate'

RESP_KEYS={
    'from_curr': '1. From_Currency Code',
    'rate': '5. Exchange Rate'
}

class FXProvider:
    def __init__(self, cache_ttl, conn):
        self.cache_ttl = cache_ttl
        self._conn = conn
    
    def get_rate(self, from_curr, to_curr):
        rate_cached, updated_on = self.get_rate_from_cache(from_curr, to_curr)
        if rate_cached and datetime.utcnow() < updated_on + timedelta(seconds=self.cache_ttl):
            print('Cache hit for currency conversion={}/{}'.format(from_curr, to_curr))
            return rate_cached
        else:
            try:
                rate = self.get_rate_from_provider(from_curr, to_curr)
            except Exception as e:            
               print("Error while calling FX rate provider error=" + str(e))
               return rate_cached
            if rate:
                self.set_rate_in_cache(from_curr, to_curr, rate)
                print("Cache refreshed for currency conversion={}/{}".format(from_curr, to_curr))
                return rate
            else:
                print("Provider cannot provide any rate for conversion={}/{}".format(from_curr, to_curr))
                return None
    
    def get_rate_from_provider(self, from_curr, to_curr):
        url_template = 'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={from_curr}&to_currency={to_curr}&apikey={key}'
        url = url_template.format(from_curr=from_curr, to_curr=to_curr, key=API_KEY)
        headers = {'Accept': 'application/json'}
        print("calling alphavantage.co...")
        r = requests.get(url, headers=headers)
        print("call complete")
        if r.ok:   
            r_json = r.json()
            rate_s = r_json.get(RESP_TOP_LVL_KEY).get(RESP_KEYS['rate'])
            return float(rate_s)
        else:
            return None

    def get_rate_from_cache(self, from_curr, to_curr):
        with self._conn.cursor() as cur:
            sql = "SELECT exchange_rate, updated_on FROM last_exchange_rate WHERE from_currency='{from_curr}' and to_currency='{to_curr}'"
            cur.execute(sql.format(from_curr=from_curr, to_curr=to_curr))
            self._conn.commit()
            first_row = cur.fetchone()
            if first_row:
                return float(first_row[0]), first_row[1]
            else:
                return None, None

    def set_rate_in_cache(self, from_curr, to_curr, rate):
        with self._conn.cursor() as cur:
            sql = "INSERT INTO last_exchange_rate (from_currency, to_currency, exchange_rate) VALUES('{from_curr}', '{to_curr}', {rate}) " \
                "ON DUPLICATE KEY UPDATE exchange_rate={rate}, updated_on=NOW(3)"
            cur.execute(sql.format(from_curr=from_curr, to_curr=to_curr, rate=rate))
            self._conn.commit()
