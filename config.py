import os
import sys

# Try loading .env, but system env vars take precedence
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional; env vars alone are fine

class Config:
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')

    _required = {
        'DB_USER': DB_USER,
        'DB_PASSWORD': DB_PASSWORD,
        'DB_HOST': DB_HOST,
        'DB_PORT': DB_PORT,
        'DB_NAME': DB_NAME,
    }

    @classmethod
    def validate(cls):
        """Validate all required config variables are set."""
        missing = [k for k, v in cls._required.items() if not v]
        if missing:
            print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
            print("Set them via environment variables or a .env file.")
            sys.exit(1)

    @property
    def DATABASE_URL(self):
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


config = Config()
