import requests
from datetime import datetime, timedelta

class QuoteProvider:

    def __init__(self, cache_ttl, conn):
        self.cache_ttl = cache_ttl
        self._conn = conn
    
    def get_quote(self, ticker):
        price_cached, updated_on = self.get_quote_from_cache(ticker)
        if price_cached and datetime.utcnow() < updated_on + timedelta(seconds=self.cache_ttl):
            print('Cache hit for ticker=' + ticker)
            return price_cached
        else:
            try:
                price = self.get_quote_from_provider(ticker)
            except Exception as e:            
               print("Error while calling quote provider error=" + str(e))
               return price_cached
            if price:
                self.set_quote_in_cache(ticker, price)
                print("Cache refreshed for ticker=" + ticker)
                return price
            else:
                print("Provider cannot provide any quote for ticker=" + ticker)
                return None

    def get_quote_from_provider(self, ticker):
        headers = {
            'Authorization': 'Bearer WAAr38EPoAbgOC8cIbQvVzPthXZj',
            'Accept': 'application/json'
        }
        url = 'https://sandbox.tradier.com/v1/markets/quotes?symbols=' + ticker
        r = requests.get(url, headers=headers)
        if r.ok:   
            quote_entry = r.json()['quotes'].get('quote')
            if quote_entry:
                return quote_entry['last']            
        return None

    def get_quote_from_cache(self, ticker):
        with self._conn.cursor() as cur:
            sql = "SELECT price, updated_on FROM last_price where ticker='{ticker}'"
            cur.execute(sql.format(ticker=ticker))
            self._conn.commit()
            first_row = cur.fetchone()
            if first_row:
                return float(first_row[0]), first_row[1]
            else:
                return None, None

    def set_quote_in_cache(self, ticker, price):
        with self._conn.cursor() as cur:
            sql = "INSERT INTO last_price (ticker, price) VALUES('{ticker}', {price}) " \
                "ON DUPLICATE KEY UPDATE price={price}, updated_on=NOW(3)"
            cur.execute(sql.format(ticker=ticker, price=price))
            self._conn.commit()
