from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Kita-AIoT"
    APP_ENV: str = "dev"
    
    MQTT_HOST: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_TOPIC: str = "aiot/device/alarm"
    
    DIFY_API_BASE_URL: Optional[str] = None
    DIFY_API_KEY: Optional[str] = None
    BAILIAN_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
