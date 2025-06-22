import sys
import os

# Add the 'src' directory to the path so Gunicorn can find the 'app' module.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app

app = create_app()