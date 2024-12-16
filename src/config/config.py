from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    # BOt

    BOT_TOKEN: str

    # DB

    DB_PASS: str
    DB_USER: str
    DB_NAME: str 
    DB_HOST: str
    DB_PORT: int 

    # redis

    RD_HOST: str
    RD_PASS: str
    RD_PORT: int
    
    # Debug mode

    DEBUG: bool = False

    @property
    def database_link(self):
         return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def get_debug_settings(self):
        return self.DEBUG
    
    
settings = Settings()