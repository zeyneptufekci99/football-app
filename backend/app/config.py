from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_football_key: str = ""
    api_football_base_url: str = "https://v3.football.api-sports.io"
    database_url: str = ""
    # Ücretsiz plan: dakikada 10 istek -> istekler arası en az 6.5 sn
    min_request_interval: float = 6.5


settings = Settings()