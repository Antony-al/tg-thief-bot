from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    bot_token: SecretStr
    my_channel: str
    my_channel_id: str
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


config = Settings()