from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Kita-AIoT"
    APP_ENV: str = "dev"

    DATABASE_URL: str = "sqlite:///./kita_aiot.db"

    MQTT_HOST: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_TOPIC: str = "aiot/device/alarm"
    MQTT_ENABLED: bool = False
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None

    MINIO_ENABLED: bool = False
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "device-documents"

    DIFY_API_BASE_URL: Optional[str] = None
    DIFY_API_KEY: Optional[str] = None
    DIFY_WORKFLOW_ENABLED: bool = False
    DIFY_TIMEOUT_SECONDS: int = 180
    DIFY_SERIALIZE_COMPLEX_INPUTS: bool = False

    BAILIAN_API_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    BAILIAN_API_KEY: Optional[str] = None
    BAILIAN_MODEL: str = "qwen-plus"
    BAILIAN_TIMEOUT_SECONDS: int = 120

    AGENT_PLATFORM: str = "auto"
    RAG_TOP_K: int = 3
    KNOWLEDGE_BASE_DIR: str = "docs/knowledge_base"

    N8N_WEBHOOK_URL: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
