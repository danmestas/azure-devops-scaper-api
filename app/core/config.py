from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    AZURE_DEVOPS_ORG: str
    AZURE_DEVOPS_PROJECT: str
    AZURE_DEVOPS_PAT: str

    class Config:
        env_file = ".env"

settings = Settings() 