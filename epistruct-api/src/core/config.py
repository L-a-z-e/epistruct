from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = "development"
    secret_key: str = "change-me"
    allowed_origins: list[str] = ["http://localhost:8081"]

    database_url: str
    postgres_user: str = "epistruct"
    postgres_password: str = "epistruct"
    postgres_db: str = "epistruct"

    supabase_url: str = ""
    supabase_jwt_secret: str = ""
    supabase_webhook_secret: str = ""

    anthropic_api_key: str = ""

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    glitchtip_dsn: str = ""

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    discord_webhook_url: str = ""


settings = Settings()
