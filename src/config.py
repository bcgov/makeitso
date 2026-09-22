import os
import urllib.parse

class Config:
    DB_USER = os.environ.get("DB_USER", "postgres")
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{urllib.parse.quote(str(os.environ.get('DB_PASSWORD')))}@{os.environ.get('DB_HOST', '127.0.0.1')}:{os.environ.get('DB_PORT', '5432')}/{os.environ.get('DB_NAME', 'mis')}"