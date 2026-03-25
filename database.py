import psycopg

class Database:
    def __init__(self, config):
        self.config = config
        self.conn = None
        self.cur = None

    def execute_and_fetch_all(self, query, params=None):
        self.conn = psycopg.connect(**self.config)
        self.cur = self.conn.cursor()
        try:
            self.cur.execute(query, params)
            return self.cur.fetchall()
        finally:
            self.close()
    
    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()