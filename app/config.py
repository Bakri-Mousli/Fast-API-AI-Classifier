from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    openai_base_url: str = "https://openrouter.ai/api/v1"
    model_name: str = "deepseek/deepseek-r1:free"
    
    class Config:
        env_file = ".env"

settings = Settings()


