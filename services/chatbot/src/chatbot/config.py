import os

from dotenv import load_dotenv

from .dbconnections import CHROMA_HOST, CHROMA_PORT, MONGO_CONNECTION_URI

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret")
    MONGO_URI = MONGO_CONNECTION_URI
    DEFAULT_MODEL_NAME = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 50000))
    CHROMA_HOST = CHROMA_HOST
    CHROMA_PORT = CHROMA_PORT
