import requests
import json
from datetime import datetime, timedelta
import re

BASE_URL = "https://login.questrade.com"
TOKEN_URI = BASE_URL + "/oauth2/token"
ACCOUNT_ACTIVITIES_REL_URI = "v1/accounts/{account_id}/activities?startTime={start_time}&endTime={end_time}&"
MARKET_SYMBOL_ID_REL_URI = "v1/symbols/{id}"
MARKET_SYMBOL_NAME_REL_URI = "v1/symbols?names={name}"
MARKET_QUOTES_REL_URI = "v1/markets/quotes/{id}"
ACCOUNTS_REL_URI = "v1/accounts"


CACHE_STORE_TOKEN = "qt_token"
CACHE_TTL_TOKEN = int(3600*24*90)
EXPIRY_DATE_FMT = r"%Y-%m-%d %H:%M:%S"

CACHE_STORE_SYMBOL_BY_ID = "qt_symbol_by_id"
CACHE_STORE_SYMBOL_BY_NAME = "qt_symbol_by_name"
CACHE_TTL_SYMBOL = 3600*24*7

CACHE_STORE_QUOTE = "qt_quote"
CACHE_TTL_QUOTE = int(60*60*2)

class QuestradeClient():
    def __init__(self, cache_client, user_id):
        self._cache_client = cache_client
        self._user_id = user_id
        self._token = {}    

    def get_account_activities(self, account_id, start_date, end_date):
        rel_url = ACCOUNT_ACTIVITIES_REL_URI.format(
            account_id = account_id,
            start_time = self.qt_time_format(start_date),
            end_time = self.qt_time_format(end_date)
        )
        r = self.qt_url_get(rel_url)
        return r['activities']

    def get_symbol_by_id_cached(self, id):
        r = self._cache_client.get(CACHE_STORE_SYMBOL_BY_ID, id)
        if r:
            return json.loads(r)
        else:
            s = self.get_symbol_by_id(id)
            self._cache_client.put(CACHE_STORE_SYMBOL_BY_ID, id, json.dumps(s), CACHE_TTL_SYMBOL)
            return s
    
    def get_symbol_by_id(self, id):
        rel_url = MARKET_SYMBOL_ID_REL_URI.format(id=id)
         # returns a dict, the dict first item (key = "symbols") is an array of one item ("symbol")
        r = self.qt_url_get(rel_url)
        return r['symbols'][0]

    def get_symbol_by_name_cached(self, name):
        r = self._cache_client.get(CACHE_STORE_SYMBOL_BY_NAME, name)
        if r:
            return json.loads(r)
        else:
            s = self.get_symbol_by_name(name)
            self._cache_client.put(CACHE_STORE_SYMBOL_BY_NAME, name, json.dumps(s), CACHE_TTL_SYMBOL)
            return s
    
    def get_symbol_by_name(self, name):
        rel_url = MARKET_SYMBOL_NAME_REL_URI.format(name=name)
         # returns a dict, the dict first item (key = "symbols") is an array of one item ("symbol")
        r = self.qt_url_get(rel_url)
        return r['symbols'][0]

    def get_quote_cached(self, symbol_id):
        r = self._cache_client.get(CACHE_STORE_QUOTE, str(symbol_id))
        if r:
            return json.loads(r)
        else:
            s = self.get_quote(symbol_id)
            self._cache_client.put(CACHE_STORE_QUOTE, str(symbol_id), json.dumps(s), CACHE_TTL_QUOTE)
            return s

    def get_quote(self, symbol_id):
        rel_url = MARKET_QUOTES_REL_URI.format(id=str(symbol_id))
        r = self.qt_url_get(rel_url)
        # returns a dict, the dict first item (key = "symbolsqutes") is an array of one item
        return r['quotes'][0]        

    def get_accounts(self):
        r = self.qt_url_get(ACCOUNTS_REL_URI)
        # returns a dict of one item (key = "accounts"). This item contains an array of accounts
        return r['accounts']

    @staticmethod
    def qt_time_format(date):
        dt = datetime.strptime(date, r"%Y-%m-%d")
        return dt.strftime(r"%Y-%m-%dT%H:%M:%S-05:00")

    def qt_url_get(self, rel_url, params=None, headers={}):
        headers["Authorization"] = "Bearer " + self.get_access_token()        
        url = self._token['api_server'] + rel_url
        print("Calling Questrade..., url=", url)
        r = requests.get(url, params=params, headers=headers)
        print("Response received")
        if r.ok:
            return r.json()
        else:
            r.raise_for_status()
 
    def get_access_token(self):
        # check if valid token in memory
        if self._token and datetime.now() < datetime.strptime(self._token['expiry_date'], r"%Y-%m-%d %H:%M:%S"):
            return self._token['access_token']

        # check if valid token in remote cache
        cached_token_info = self.get_token_info_from_cache()
        if cached_token_info:
            cached_dt = datetime.strptime(cached_token_info['expiry_date'], EXPIRY_DATE_FMT)
            if datetime.now() < cached_dt:
                self._token = cached_token_info
                return cached_token_info['access_token']
        else:
            raise Exception("Refresh token missing from cache. Cannot get new access_token")
        
        # if no valid token then request a new one from QT token endpoint
        new_token_info = self.get_fresh_token(cached_token_info['refresh_token'])
        # compute expiration date of the new token
        dt = datetime.now() + timedelta(seconds=new_token_info['expires_in'])
        new_token_info['expiry_date'] = dt.strftime(EXPIRY_DATE_FMT)
        # save token info in remote cache
        self._cache_client.put(CACHE_STORE_TOKEN, self._user_id, json.dumps(new_token_info), CACHE_TTL_TOKEN)
        # save token info in memory
        self._token = new_token_info

        return self._token['access_token']

    def get_token_info_from_cache(self):
        cached_value = self._cache_client.get(CACHE_STORE_TOKEN, self._user_id)
        if cached_value:
            return json.loads(cached_value)
        else:
            return None

    def get_fresh_token(self, refresh_token):
        # refresh_token = "9yc5eDQANmSEjqVRCIjW8RUyKDFe5vuk0"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        # print("Refresh token=", refresh_token)
        r = requests.post(TOKEN_URI, payload)
        if r.ok:
            return r.json()
        else:
            r.raise_for_status()

if __name__ == "__main__":
    import os
    from chalicelib.CacheClient import CacheClient
    os.environ['CACHE_DB_PASSWORD'] = "irondesk89"
    os.environ['CACHE_DB_NAME'] = "investornetwork"

    cache_client = CacheClient()
    qt_client = QuestradeClient(cache_client, "1")
    # r = qt_client.get_account_activities("26829536", "2018-08-01", "2018-08-25")
    # r = qt_client.get_symbol_by_id_cached(8049)
    # r = qt_client.get_accounts()
    # r = qt_client.get_symbol_by_name_cached("BNS.TO")
    r = qt_client.get_quote_cached(9339)
    print(str(r))
