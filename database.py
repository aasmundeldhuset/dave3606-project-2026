import psycopg


class Database:
    def __init__(self, config):
        self.config = config
        self.conn = None
        self.cur = None

    def execute_and_fetch_all(self, query):
        # Ensure previous cursor/connection are closed before opening new ones.
        self.close()
        self.conn = psycopg.connect(**self.config)
        self.cur = self.conn.cursor()
        self.cur.execute(query)
        return self.cur.fetchall()

    def close(self):
        if self.cur is not None:
            self.cur.close()
            self.cur = None
        if self.conn is not None:
            self.conn.close()
            self.conn = None
