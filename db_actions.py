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
                channels_to_monitor TEXT DEFAULT "t.me/eternalclassic|t.me/itvbia|",           
                PRIMARY KEY (usertgid)
            )
        """)
        return self.conn.commit() 
    
    def user_exists(self, user_id):
        result = self.cursor.execute("SELECT `usertgid` FROM `users` WHERE `usertgid` = ?", (user_id,))
        return bool(len(result.fetchall()))

    def add_user(self, user_id):
        self.cursor.execute("INSERT INTO `users` (`usertgid`) VALUES (?)", (user_id,))
        return self.conn.commit()


    def set_tg_client(self):
        pass

    def get_tg_client(self):
        pass

    def add_channel(self, user_id, channel):
        pass    