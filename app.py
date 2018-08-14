from chalice import Chalice
from QuoteProvider import QuoteProvider
from FXProvider import FXProvider
import db_connection
import traceback

app = Chalice(app_name='portofolio-api')

LOCAL_CURRENCY = 'CAD'

@app.route('/portfolio/{port_id}/holdings')
def get_portfolio_holdings(port_id):
    # TODO: add test of 'groupBy' query string param
    try:
        with db_connection.get_ssh_tunnel() as t:
            conn = db_connection.get_db_conn(t)
            with conn.cursor() as cur:
                print("cursor up")
                sql = (
                    "SELECT ticker, SUM(quantity) AS qty, "
                    "SUM(quantity * price) AS pos_cost, "
                    "SUM(quantity * price * exchange_rate) AS pos_cost_local, "
                    "SUM(fee / IF(price_currency_code!=fee_currency_code, exchange_rate, 1)) AS fee_cost, "
                    "MIN(local_currency_code), MIN(price_currency_code), MIN(fee_currency_code)"
                     "FROM investornetwork.trade "
                    "WHERE portfolio_id = {port_id} "
                    "GROUP BY ticker "
                    "ORDER BY ticker ASC"
                )
                cur.execute(sql.format(port_id=port_id))
                conn.commit()
                
                resp_holdings_list = []
                q_provider = QuoteProvider(60, conn)
                fx_provider = FXProvider()
                for row in cur:
                    resp_holdings_list.append(get_holding_item_dic(row, q_provider, fx_provider))

                return resp_holdings_list
    except Exception:
        return traceback.format_exc()


def get_holding_item_dic(row, quote_provider, fx_provider):
    
    qty = float(row[1])
    position_cost = float(row[2])
    position_cost_local = float(row[3])
    local_currency = row[5]
    share_currency = row[6]
    fee_currency = row[7]
    if local_currency != share_currency:
        diff_curr = True
        last_fx_rate = fx_provider.get_rate(share_currency, local_currency)

    fee_cost = float(row[4])
    if fee_currency != share_currency:
        if fee_currency == local_currency:
            fee_cost = fee_cost / last_fx_rate
        else:
            fee_cost = fee_cost * last_fx_rate
    
    position_cost = position_cost + fee_cost
    # position_cost_local = 

    avg_cost_per_share = (position_cost - fee_cost) / qty

    h = {
        'ticker': row[0],
        'quantity': qty,
        'avg_cost_per_share': fmt_share_price(avg_cost_per_share),
        'share_currency': share_currency,
        'position_cost': fmt_price(position_cost),
        'position_cost_local': fmt_price(position_cost_local),
        'market_value': {},
        'returns': {}
    }

    if diff_curr:
        h['avg_exchange_rate'] = fmt_price(position_cost_local / position_cost)

    h['market_value']['share_price'] = fmt_share_price(quote_provider.get_quote(h['ticker']))
    h['market_value']['position'] = fmt_price(h['quantity'] * h['market_value']['share_price'])
    if diff_curr:
        h['market_value']['position_local'] = fmt_price(h['market_value']['position'] * last_fx_rate)

    # Capital gains
    cap_gains = (h['market_value']['share_price'] - h['avg_cost_per_share']) * h['quantity']
    if diff_curr:
        cap_gains = cap_gains * last_fx_rate

    h['returns']['capital_gains'] = fmt_price(cap_gains)
    h['returns']['capital_gains_pct'] = fmt_pct(cap_gains / h['position_cost_local'])

    # Currency gains
    if diff_curr:
        curr_gains = (last_fx_rate - h['avg_exchange_rate']) * h['quantity'] * h['avg_cost_per_share']

    h['returns']['currency_gains'] = fmt_price(curr_gains)
    h['returns']['currency_gains_pct'] = fmt_pct(curr_gains / h['position_cost_local'])

    return h

def fmt_share_price(price):
    return float('%.3f' % price)

def fmt_price(price):
    return float('%.2f' % price)

def fmt_pct(pct):
    pct = pct * 100
    return float('%.2f' % pct)

# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to '/'.
#
# Here are a few more examples:
#
# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.
#
