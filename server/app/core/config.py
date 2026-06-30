from pydantic import BaseModel


class AppConfig(BaseModel):
    app_name: str = 'Goblin Black Office API'
    api_prefix: str = '/api/v1'
