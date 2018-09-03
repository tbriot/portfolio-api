from chalicelib.QuestradeClient import QuestradeClient

class QuoteProvider:

    def __init__(self, cache_client):
        self._cache_client = cache_client
        self._qt_client = QuestradeClient(cache_client, 1)        
    
    def get_quote(self, market, ticker):
        if market == "TSX":
            qt_symbol = ticker + ".TO"
        else:
            qt_symbol = ticker
        # get QT internal symbol id from the security ticker symbol
        symb = self._qt_client.get_symbol_by_name_cached(qt_symbol)
        qt_symbol_id = symb["symbolId"]
        # get security quote from QT 
        q = self._qt_client.get_quote_cached(qt_symbol_id)
        if not q["lastTradePrice"]:
            raise Exception("Quote for ticker={} has no lastTradePrice attribute".format(qt_symbol))
        return float(q["lastTradePrice"])

if __name__ == "__main__":
    import os
    from chalicelib.CacheClient import CacheClient
    os.environ['CACHE_DB_PASSWORD'] = "irondesk89"
    os.environ['CACHE_DB_NAME'] = "investornetwork"

    cache_client = CacheClient()
    qp = QuoteProvider(cache_client)

    q = qp.get_quote("NYSE", "BNS")
    print(str(q))
