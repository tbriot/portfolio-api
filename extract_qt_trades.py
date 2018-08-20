from QuestradeClient import QuestradeClient
from CacheClient import CacheClient
from datetime import datetime, timedelta
import re
# from activities_sample import ACTIVITIES_SAMPLE

def extract_qt_trades(start_date, end_date):
    cache = CacheClient() 
    qt_client = QuestradeClient(cache, 1)

    file = open("./qt_trades.sql", "a")
    file.write(build_insert_header())

    accounts = qt_client.get_accounts()
    for account in accounts:
        time_periods = split_time_period(start_date, end_date)
        for start, end in time_periods:
            activities = qt_client.get_account_activities(
                account['number'],
                start,
                end
            )
            for a in activities:
                if a['type'] == "Trades":
                    sql = build_insert_statement(a)            
                    file.write(sql)

    file.write(build_insert_footer())
    file.close()

def split_time_period(start_date, end_date):
    time_periods = []    

    start_dt = datetime.strptime(start_date, r"%Y-%m-%d")
    end_dt = datetime.strptime(end_date, r"%Y-%m-%d")

    current_period_start_dt = start_dt

    iterating = True
    while iterating:
        current_period_end_dt = min([current_period_start_dt + timedelta(days=30), end_dt])
        time_periods.append(
            [
                current_period_start_dt.strftime(r"%Y-%m-%d"),
                current_period_end_dt.strftime(r"%Y-%m-%d")
            ]
        )

        if current_period_end_dt == end_dt:
            iterating = False
        
        # next time period start date is current's time period end date + 1 day
        current_period_start_dt = current_period_end_dt + timedelta(days=1)

    return time_periods

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
    import os
    os.environ['CACHE_DB_NAME'] = "investornetwork"
    os.environ['CACHE_DB_PASSWORD'] = "irondesk89"
    os.environ['CURCONVERTER_DB_NAME'] = "investornetwork"
    os.environ['CURCONVERTER_DB_PASSWORD'] = "irondesk89"
    extract_qt_trades("2018-07-01", "2018-08-31")
    # print(str(split_time_period("2018-08-05", "2018-10-15")))
