import requests
from datetime import datetime
import re
# from activities_sample import ACTIVITIES_SAMPLE

ACCOUNT_ID = "26829536"
QT_BASE_URL = "https://login.questrade.com"
QT_OAUTH2_EP = QT_BASE_URL + "/oauth2/token"

QT_ACCOUNT_CALLS_URI = "v1/accounts/{account_id}/"
QT_ACCOUNT_ACTIVITIES_URI = QT_ACCOUNT_CALLS_URI + "activities?startTime={start_time}&endTime={end_time}&"

qt_refresh_token = "XwCWOEuCvlSBv8UweSNqYGPTm4GcwOHH0"

start_date = "2018-07-20"
end_date = "2018-08-17"

def get_access_token(refresh_token):
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": qt_refresh_token
    }
    r = requests.post(QT_OAUTH2_EP, payload)
    if r.ok:
        r_json = r.json()
        return r_json['access_token'], r_json['api_server']
    else:
        r.raise_for_status()

def get_activities(access_token, api_server, account_id, start_date, end_date):
    headers = {"Authorization": "Bearer " + access_token}
    r = requests.get(
        api_server + QT_ACCOUNT_ACTIVITIES_URI.format(
            account_id=account_id,
            start_time=time_format(start_date),
            end_time=time_format(end_date)
        ),
        headers=headers)
    if r.ok:
        r_json = r.json()
        return r_json['activities']
    else:
        r.raise_for_status()

def build_insert_statement(activity):
    return (
        "INSERT INTO trade (portfolio_id, transaction_type, market, symbol, quantity, "
            " security_price, security_currency, fee, fee_currency, local_currency, traded_on) "
        "VALUES (1, '{transaction_type}', '{market}', '{symbol}', {quantity}, {security_price}, "
        "'{security_currency}', {fee}, '{fee_currency}', '{local_currency}', '{traded_on}');\n"
    ).format(
        transaction_type=map_transaction_type(activity['action']),
        market="",
        symbol=activity['symbol'],
        quantity=abs(activity['quantity']),
        security_price=activity['price'], 
        security_currency=activity['currency'],
        fee=abs(activity['commission']),
        fee_currency="CAD",
        local_currency="CAD",
        traded_on=convert_dt_from_qt(activity['tradeDate'])
    )

def build_insert_header():
    return "DELETE FROM trade WHERE portfolio_id=1;\n"

def build_insert_footer():
    return "COMMIT;\n"

def map_transaction_type(action):
    if action=="Buy":
        return "BUY"
    else:
        return "SELL"

def convert_dt_from_qt(date_time):
    date_time = re.sub(r'(?<=[+-][0-9]{2}):', '', date_time)
    dt = datetime.strptime(date_time, r"%Y-%m-%dT%H:%M:%S.%f%z")
    return dt.strftime(r"%Y-%m-%d %H:%M:%S")

def generate_sql_dump(activities):
    file = open("./qt_trades.sql", "a")
    file.write(build_insert_header())
    for a in activities:
        if a['type'] == "Trades":
            sql = build_insert_statement(a)            
            file.write(sql)
    file.write(build_insert_footer())
    file.close()
    return 0

def time_format(date):
    dt = datetime.strptime(date, r"%Y-%m-%d")
    return dt.strftime(r"%Y-%m-%dT%H:%M:%S-05:00")

if __name__ == "__main__":
    print("START extract tades from Questrade")
    access_token, api_server = get_access_token(qt_refresh_token)
    print("Access token retrieved: " + access_token)
    print("Questrade API server: " + api_server)
    activities = get_activities(access_token, api_server, ACCOUNT_ID, start_date, end_date)
    print("Retrieved {} activities successfully".format(len(activities)))
    generate_sql_dump(activities)
    print("SQL dump generated")
