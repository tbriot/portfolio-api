from chalice import Chalice
from QuoteProvider import QuoteProvider
import db_connection
import traceback

app = Chalice(app_name='portofolio-api')


@app.route('/portfolio/{port_id}/holdings')
def get_portfolio_holdings(port_id):
    # TODO: add test of 'groupBy' query string param
    try:
        with db_connection.get_ssh_tunnel() as t:
            conn = db_connection.get_db_conn(t)
            with conn.cursor() as cur:
                print("cursor up")
                sql = (
                    "SELECT ticker, SUM(quantity) AS qty, SUM(quantity * price) AS pos_cost "
                    "FROM investornetwork.trade "
                    "WHERE portfolio_id = {port_id} "
                    "GROUP BY ticker "
                    "ORDER BY ticker ASC"
                )
                cur.execute(sql.format(port_id=port_id))
                conn.commit()
                
                resp_holdings_list = []
                q_provider = QuoteProvider(60, conn)
                for row in cur:
                    resp_holdings_list.append(get_holding_item_dic(row, q_provider))

                return resp_holdings_list
    except Exception:
        return traceback.format_exc()


def get_holding_item_dic(row, quote_provider):
    h = {
        'ticker': row[0],
        'quantity': float(row[1]),
        'avg_cost_per_share': fmt_share_price(float(row[2]) / float(row[1])),
        'position_cost': fmt_price(float(row[2])),
        'market_value': {},
        'returns': {}
    }

    h['market_value']['share_price'] = fmt_share_price(quote_provider.get_quote(h['ticker']))
    h['market_value']['position'] = fmt_price(h['quantity'] * h['market_value']['share_price'])

    h['returns']['capital_gains'] = fmt_price(h['market_value']['position'] - h['position_cost'])
    h['returns']['capital_gains_pct'] = fmt_pct(h['returns']['capital_gains'] / h['market_value']['position'])

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
