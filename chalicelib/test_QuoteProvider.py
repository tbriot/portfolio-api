import unittest
from chalicelib.QuoteProvider import QuoteProvider
import pymysql
from datetime import datetime, timedelta

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

    def test_get_quote_from_cache(self):
            conn = self.get_db_conn()
            q_provider = QuoteProvider(60, conn)
            price, updated_on = q_provider.get_quote_from_cache('AAPL')
            self.assertEqual(price, 207.53)

    def test_set_quote_from_cache(self):
            conn = self.get_db_conn()
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
            conn = self.get_db_conn()
            q_provider = QuoteProvider(10, conn)    

            price = q_provider.get_quote('GOOG')
            self.assertEqual(type(price), float)

if __name__ == '__main__':
    unittest.main()