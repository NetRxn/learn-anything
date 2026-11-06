# app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = ""
    state_backend: str = "json"  # "postgres" or "json"
    json_state_dir: str = "data/state"
    encryption_key_path: str = "data/encryption.key"
    secret_key: str = "change-me-on-first-run"
    session_max_age: int = 7 * 24 * 3600  # 7 days
    single_user: bool = False
    log_level: str = "INFO"
    allowed_origins: str = ""
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    setup_complete: bool = False

    model_config = {"env_prefix": "LA_", "env_file": ".env"}


settings = Settings()
