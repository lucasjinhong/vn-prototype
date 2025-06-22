# app/__init__.py
from flask import Flask, g
import os
from .config import Config
from .game_logic import load_story

def create_app(config_class=Config):
    """Application factory function."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    project_root = os.path.dirname(app.root_path)
    app.config['PROJECT_ROOT'] = project_root
    
    with app.app_context():
        load_story(app)

    # Register blueprints
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    return app