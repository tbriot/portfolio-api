from chalice import Chalice, Response
from chalicelib import CacheClient, QuoteProvider, FXProvider, get_db_conn
import traceback

app = Chalice(app_name='portfolio-api')
app.debug = True
LOCAL_CURRENCY = 'CAD'

@app.route('/portfolio/{port_id}/holdings')
def get_portfolio_holdings(port_id):
    # TODO: add test of 'groupBy' query string param
    try:
        cache_client = CacheClient()
        conn = get_db_conn()
        with conn.cursor() as cur:
            sql = (
                "SELECT symbol, market, "
                "SUM(quantity) AS qty, "
                "SUM(IF(transaction_type='SELL', -1, 1) * quantity * security_price "
                    "+ fee * (IFNULL(fee_currency_xr,1) / IFNULL(security_currency_xr,1))) AS position_cost, "
                "SUM(IF(transaction_type='SELL', -1, 1) * quantity * security_price * IFNULL(security_currency_xr,1) "
                    "+ fee * IFNULL(fee_currency_xr,1)) AS position_cost_local, "
                "MIN(local_currency), MIN(security_currency) "
                "FROM investornetwork.trade "
                "WHERE portfolio_id = {port_id} "
                "GROUP BY symbol, market "
                "ORDER BY symbol, market ASC"
            )
            conn.commit()
            cur.execute(sql.format(port_id=port_id))
            
            print("query successful")
            resp_holdings_list = []
            q_provider = QuoteProvider(cache_client)
            fx_provider = FXProvider(300, conn)
            for row in cur:
                resp_holdings_list.append(get_holding_item_dic(row, q_provider, fx_provider))
            
            return Response(
                body=get_holdings_render_html(resp_holdings_list),
                status_code=200,
                headers={'Content-Type': 'text/html'}
            )
    except Exception:
        return traceback.format_exc()


def get_holding_item_dic(row, quote_provider, fx_provider):
    diff_curr=False 

    symbol = row[0]
    market = row[1]
    qty = float(row[2])
    position_cost = float(row[3])
    position_cost_local = float(row[4])
    local_currency = row[5]
    security_currency = row[6]
    if local_currency != security_currency:
        diff_curr = True
        last_fx_rate = fx_provider.get_rate(security_currency, local_currency)
    
    avg_cost_per_share = position_cost / qty
    avg_exchange_rate = position_cost_local / position_cost
    last_share_price = quote_provider.get_quote(market, symbol)

    if not last_share_price:
        print("Unable to fetch current price of symbol=" + symbol)

    h = {
        'symbol': symbol,
        'market': market,
        'security_currency': security_currency,
        'quantity': qty,
        'position' : {},
        'market_value': {},
        'returns': {}
    }

    h['position']['avg_cost_per_share'] = fmt_share_price(avg_cost_per_share)
    h['position']['position_cost'] = fmt_price(position_cost)
    if diff_curr:
        h['position']['avg_exchange_rate'] = fmt_price(avg_exchange_rate)
        h['position']['position_cost_local'] = fmt_price(position_cost_local)

    h['market_value']['share_price'] = fmt_share_price(last_share_price)
    h['market_value']['position'] = fmt_price(qty * last_share_price)
    
    if diff_curr:
        h['market_value']['position_local'] = fmt_price(h['market_value']['position'] * last_fx_rate)

    # Capital gains
    cap_gains = (last_share_price - avg_cost_per_share) * qty
    if diff_curr:
        cap_gains = cap_gains * last_fx_rate

    h['returns']['capital_gains'] = fmt_price(cap_gains)
    h['returns']['capital_gains_pct'] = fmt_pct(cap_gains / position_cost_local)

    # Currency gains
    if diff_curr:
        curr_gains = (last_fx_rate - avg_exchange_rate) * qty * avg_cost_per_share
        h['returns']['currency_gains'] = fmt_price(curr_gains)
        h['returns']['currency_gains_pct'] = fmt_pct(curr_gains / position_cost_local)

    return h

def fmt_share_price(price):
    return float('%.3f' % price)

def fmt_price(price):
    return float('%.2f' % price)

def fmt_pct(pct):
    pct = pct * 100
    return float('%.2f' % pct)

def get_holdings_render_html(holdings):
    html = """
        <html>
            <head>
                <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous">
            </head>
            <body>
                <table class="table table-striped table-hover">
                    <thead class="thead-light">
                        <tr> 
                            <th>symbol</th>
                            <th>market</th>
                            <th>currency</th>
                            <th>qty</th>
                            <th>avg_cost_per_share</th>
                            <th>share_price</th>
                            <th>position cost</th>
                            <th>capital gains</th>
                            <th>capital gains %</th>
                            <th>currency gains</th>
                            <th>currency gains %</th>
                        </tr>
                    </thead>
    """

    for h in holdings:
        html += """
            <tr> 
                <td>{symbol}</td>
                <td>{market}</td>
                <td>{currency}</td>
                <td>{qty}</td>
                <td>{avg_cost_per_share}</td>
                <td>{share_price}</td>
                <td>{position}</td>
                <td>{cap_gains}</td>
                <td>{cap_gains_pct}</td>
                <td>{curr_gains}</td>
                <td>{curr_gains_pct}</td>
            </tr>
    """.format(
        symbol=h["symbol"],
        market=h["market"],
        currency=h["security_currency"],
        qty=h["quantity"],
        avg_cost_per_share=h["position"]["avg_cost_per_share"],
        share_price=h["market_value"]["share_price"],
        position=h["market_value"]["position"],
        cap_gains=h['returns']['capital_gains'],
        cap_gains_pct=h['returns']['capital_gains_pct'],
        curr_gains=h.get('returns').get('currency_gains') or "",
        curr_gains_pct=h.get('returns').get('currency_gains_pct') or ""
    )

    html += """
                </table>
            </body>
        </html>
    """
    return html
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

if __name__ == "__main__":
    import os
    from chalicelib.CacheClient import CacheClient
    os.environ['CACHE_DB_PASSWORD'] = "irondesk89"
    os.environ['CACHE_DB_NAME'] = "investornetwork"
    os.environ['DB_PASSWORD'] = "irondesk89"
    os.environ['DB_NAME'] = "investornetwork"
    r = get_portfolio_holdings("1")
    print(str(r))