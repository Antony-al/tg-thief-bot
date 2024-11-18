import sqlite3
db_path = 'data/botdb.db'

class MemeStealerDb():
    def __init__(self):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()

    def create_db(self):
            
                  