import requests

API_KEY = 'JVI5ZU3MASJ5J5MS'

RESP_TOP_LVL_KEY = 'Realtime Currency Exchange Rate'

RESP_KEYS={
    'from_curr': '1. From_Currency Code',
    'rate': '5. Exchange Rate'
}

class FXProvider:
    def __init__(self):
        pass
    
    def get_rate(self, from_curr, to_curr):
        url_template = 'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={from_curr}&to_currency={to_curr}&apikey={key}'
        url = url_template.format(from_curr=from_curr, to_curr=to_curr, key=API_KEY)
        headers = {'Accept': 'application/json'}
        r = requests.get(url, headers=headers)
        if r.ok:   
            r_json = r.json()
            rate_s = r_json.get(RESP_TOP_LVL_KEY).get(RESP_KEYS['rate'])
            return float(rate_s)
        else:
            return None

if __name__ == '__main__':
    prov = FXProvider()
    print(prov.get_rate('USD', 'CAD'))