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
                    "SELECT *, pos_cost/qty as cost_share FROM "
                    "(SELECT ticker, SUM(quantity) AS qty, SUM(quantity * price) AS pos_cost "
                    "FROM investornetwork.trade "
                    "WHERE portfolio_id = {port_id} "
                    "GROUP BY ticker) as t "
                    "ORDER BY ticker ASC"
                )
                cur.execute(sql.format(port_id=port_id))
                conn.commit()
                
                resp_holdings_list = []
                for row in cur:
                    resp_holdings_list.append(get_holding_item_dic(row))
                return resp_holdings_list
    except Exception:
        return traceback.format_exc()
    # q_provider = QuoteProvider(60, conn)


def get_holding_item_dic(row):
    json_row = {}
    json_row['ticker'] = row[0]
    json_row['quantity'] = row[1]
    json_row['avg_cost_per_share'] = row[3]
    json_row['position_cost'] = row[2]
    return json_row

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
