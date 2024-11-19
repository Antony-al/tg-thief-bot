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
    
    def user_exists(self, usertgid):
        result = self.cursor.execute("SELECT `usertgid` FROM `users` WHERE `usertgid` = ?", (usertgid,))
        return bool(len(result.fetchall()))

    def add_user(self, usertgid):
        self.cursor.execute("INSERT INTO `users` (`usertgid`) VALUES (?)", (usertgid,))
        return self.conn.commit()


    def set_tg_client(self, usertgid, api_id, api_hash):
        self.cursor.execute("INSERT INTO users (usertgid, api_id, api_hash) VALUES (?, ?, ?)", (usertgid, api_id, api_hash,))

    def get_tg_client(self, usertgid):
        result = []
        self.cursor.execute("SELECT api_id, api_hash FROM users WHERE usertgid = ?", (usertgid,))
        result = self.cursor.fetchone()
        return result

                                    ###Проверить в дейтсвии надо будет###
                                    
    def add_channel(self, user_id, channel):
        self.cursor.execute("SELECT channels_to_monitor FROM users WHERE usertgid = ?", (user_id,))
        result = self.cursor.fetchone()
        if result:
            current_channels = result[0]
            if channel not in current_channels.split('|'):
                self.cursor.execute("UPDATE users SET channels_to_monitor = ? WHERE usertgid = ?", (channel, user_id))
                self.conn.commit()
            else:
                print(f"Канал {channel} уже существует для usertgid {user_id}.")
