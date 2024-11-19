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
            CREATE TABLE IF NOT EXISTS queue (
                channel_id TEXT,
                message_id INTEGER,
                media_path TEXT,
                caption TEXT,
                PRIMARY KEY (channel_id, message_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                usertgid INTEGER,
                api_id INTEGER DEFAULT 0,
                api_hash TEXT DEFAULT "",
                PRIMARY KEY (usertgid)
            )
        """)
        return self.conn.commit() 
    
    def user_exists(self, user_id):
        pass

    def add_user(self, user_id):
        pass


    def set_tg_client(self):
        pass

    def get_tg_client(self):
        pass
        