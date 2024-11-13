import re

api_id = None
api_hash = None
bot_token = None
review_chat_id = None
channels_to_monitor = None
my_channel = None
my_channel_id = None
db_name = 'meme_bot.db'
ad_keywords = ["реклама", "спонсор", "поддержи", "подписывайся", "партнёрская", "промо"]
link_pattern = re.compile(r"(t\.me/|@|https?://)")