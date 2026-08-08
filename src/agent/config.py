from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    tavily_api_key: str = ""
    database_url: str = "postgresql://agent:agent@localhost:5432/agent_checkpoints"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
