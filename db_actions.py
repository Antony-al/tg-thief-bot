import sqlite3
db_path = 'data/botdb.db'

class MemeStealerDb():
    def __init__(self):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()

    def create_db(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                channel_id TEXT,
                message_id INTEGER,
                PRIMARY KEY (channel_id, message_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                channel_id TEXT,
                message_id INTEGER,
                PRIMARY KEY (channel_id, message_id)
            )
        """)
        return self.conn.commit() 

    def set_tg_client(self):
        pass        