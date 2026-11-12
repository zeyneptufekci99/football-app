from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_football_key: str = ""
    api_football_base_url: str = "https://v3.football.api-sports.io"
    database_url: str = ""
    # Ücretsiz plan: dakikada 10 istek -> istekler arası en az 6.5 sn
    min_request_interval: float = 6.5
    daily_request_limit: int = 100
    auto_sync_budget: int = 70        
    scheduler_tick_seconds: int = 900  
    min_sync_interval_minutes: int = 15 
    full_sync_every_days: int = 7
    app_timezone: str = "Europe/Istanbul" 


settings = Settings()