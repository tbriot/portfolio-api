import unittest
from QuoteProvider import QuoteProvider
from sshtunnel import SSHTunnelForwarder
import pymysql
from datetime import datetime, timedelta

SSH_HOST = 'ec2-35-183-37-105.ca-central-1.compute.amazonaws.com'
SSH_USERNAME = 'ec2-user'
SSH_KEY_FILE = r'C:\Users\Thomas\.ssh\tbriot-ca-central-1.pem'

DB_HOST = 'investornetwork.co0pqf5yoscl.ca-central-1.rds.amazonaws.com'
DB_USERNAME = 'admin'
DB_PASSWORD = 'irondesk89'
DB_NAME = 'investornetwork'

LOCALHOST = '127.0.0.1'

class TestQuoteProvider(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def get_ssh_tunnel(self):
        return SSHTunnelForwarder(
            (SSH_HOST, 22),
            ssh_username = SSH_USERNAME,
            ssh_private_key = SSH_KEY_FILE,
            remote_bind_address=(DB_HOST, 3306)
        )
    
    def get_db_conn(self, tunnel):
        return pymysql.connect(
                LOCALHOST, user=DB_USERNAME,
                port=tunnel.local_bind_port,
                passwd=DB_PASSWORD, db=DB_NAME, connect_timeout=5
        )

    def test_get_quote_from_cache(self):
        with self.get_ssh_tunnel() as tunnel:
            conn = self.get_db_conn(tunnel)
            q_provider = QuoteProvider(60, conn)
            price, updated_on = q_provider.get_quote_from_cache('AAPL')
            self.assertEqual(price, 207.53)

    def test_set_quote_from_cache(self):
        with self.get_ssh_tunnel() as tunnel:
            conn = self.get_db_conn(tunnel)
            q_provider = QuoteProvider(60, conn)

            q_provider.set_quote_in_cache('BNS', 76.33)
            price, updated_on_1 = q_provider.get_quote_from_cache('BNS')
            self.assertEqual(price, 76.33)

            q_provider.set_quote_in_cache('BNS', 76.50)
            price, updated_on_2 = q_provider.get_quote_from_cache('BNS')
            self.assertEqual(price, 76.50)
            self.assertNotEqual(updated_on_1, updated_on_2)        

    def test_get_quote_from_provider(self):
        q_provider = QuoteProvider(60, None)
        price = q_provider.get_quote_from_provider('AAPL')
        self.assertEqual(type(price), float)

    def test_get_quote(self):
        with self.get_ssh_tunnel() as tunnel:
            conn = self.get_db_conn(tunnel)
            q_provider = QuoteProvider(10, conn)    

            price = q_provider.get_quote('GOOG')
            self.assertEqual(type(price), float)

if __name__ == '__main__':
    unittest.main()