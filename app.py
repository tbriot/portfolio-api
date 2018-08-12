from chalice import Chalice
from QuoteProvider import QuoteProvider

app = Chalice(app_name='portofolio-api')


@app.route('/portfolio/{port_id}/holdings')
def get_portfolio_holdings(port_id):
    # q_provider = QuoteProvider(60, conn)
    return {'portfolio_id': port_id}

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
