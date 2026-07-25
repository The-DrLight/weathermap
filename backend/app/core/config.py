from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", protected_namespaces=())

    lat: float = 6.5244
    lon: float = 3.3792

    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    open_meteo_archive_url: str = "https://archive-api.open-meteo.com/v1/archive"
    nasa_power_base_url: str = "https://power.larc.nasa.gov/api/temporal/hourly/point"
    nasa_power_daily_url: str = "https://power.larc.nasa.gov/api/temporal/daily/point"

    frontend_origin: str = "http://localhost:5173"

    model_path: str = "models/rain_model.joblib"


settings = Settings()
