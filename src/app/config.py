# app/config.py
import os

class Config:
    """Base configuration for the application."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-dev-secret-key-for-the-session'

    CONTENT_VERSION = 'v1'
    DEFAULT_LOCALE = 'en-US'