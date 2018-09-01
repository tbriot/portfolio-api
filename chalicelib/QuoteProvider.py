import requests
from chalicelib.QuestradeClient import QuestradeClient
from datetime import datetime, timedelta

CACHE_STORE_QUOTES = "stock_quotes"
CACHE_ENTRIES_TTL = 1800

CACHE_STORE_QT_SYMBOL = "qt_symbol_id"
CACHE_QT_SYMBOL_ID_TTL = 3600*24*7 # one week

class QuoteProvider:

    def __init__(self, cache_client):
        self._cache_client = cache_client
        self._qt_client = QuestradeClient(cache_client, 1)        
    
    def get_quote(self, market, ticker):
        key = '{}:{}'.format(market, ticker)
        price_cached = self._cache_client.get(CACHE_STORE_QUOTES, key)
        if price_cached:
            print('Cache hit for ticker=' + ticker)
            return float(price_cached)
        
        try:
            price = self.get_quote_from_provider(market, ticker)
        except Exception as e:            
           print("Error while calling quote provider error=" + str(e))
           return None

        if price:
            self._cache_client.put(CACHE_STORE_QUOTES, key, price, CACHE_ENTRIES_TTL)
            print("Cache refreshed for stock=" + key)
            return price
        else:
            print("Provider cannot provide any quote for stock=" + key)
            return None

    def get_quote_from_provider(self, market, ticker):
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
    
    def get_symbol_id(self, symbol):
        s_id_cached = self._cache_client.get(CACHE_STORE_QT_SYMBOL, symbol)
        if s_id_cached:
            print("Cache hit for symbol=", symbol)
            return int(s_id_cached)
        
        try:
            s_id = self.get_symbol_id_from_qt(symbol)
        except Exception as e:
            print("Error while retrieving symbol id from QT, error=", str(e))
            return None
        
        if s_id:
            self._cache_client.put(CACHE_STORE_QT_SYMBOL, symbol, s_id, CACHE_QT_SYMBOL_ID_TTL)
            print("Cache refreshed for symbol=", symbol)
            return s_id
        else:
            print("Unable to fetch QT's symbol id, symbol=", symbol)
            return None
    
    def get_symbol_id_from_qt(self, symbol):
        pass
