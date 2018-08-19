import requests
import json
from datetime import datetime, timedelta
import re
from CacheClient import CacheClient

BASE_URL = "https://login.questrade.com"
TOKEN_URI = BASE_URL + "/oauth2/token"
ACCOUNT_ACTIVITIES_URI = BASE_URL + "/v1/accounts/{account_id}/activities?startTime={start_time}&endTime={end_time}&"

CACHE_STORE = "qt_token"
CACHE_ENTRIES_TTL = int(3600*24*90)
EXPIRY_DATE_FMT = r"%Y-%m-%d %H:%M:%S"

class QuestradeClient():
    def __init__(self, cache_client, user_id):
        self._cache_client = cache_client
        self._user_id = user_id
        self._token = {}

    def get_access_token(self):
        # check if valid token in memory
        if self._token and datetime.now() < self._token['expiry_date']:
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
        self._cache_client.put(CACHE_STORE, self._user_id, json.dumps(new_token_info), CACHE_ENTRIES_TTL)
        # save token info in memory
        self._token = new_token_info

        return self._token['access_token']

    def get_token_info_from_cache(self):
        cached_value = self._cache_client.get(CACHE_STORE, self._user_id)
        if cached_value:
            return json.loads(cached_value)
        else:
            return None

    def get_fresh_token(self, refresh_token):
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        r = requests.post(TOKEN_URI, payload)
        if r.ok:
            return r.json()
        else:
            r.raise_for_status()

if __name__ == "__main__":
    import os
    os.environ['CACHE_DB_PASSWORD'] = "irondesk89"
    os.environ['CACHE_DB_NAME'] = "investornetwork"
    from CacheClient import CacheClient
    cache_client = CacheClient()
    qt_client = QuestradeClient(cache_client, "1")
    print("QT access token=" + qt_client.get_access_token())
