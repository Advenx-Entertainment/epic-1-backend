"""
config.py — Centralised configuration via environment variables.

Defaults work out of the box for local development.
Override via a .env file or shell exports.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MQTT broker
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
