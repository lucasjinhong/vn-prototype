import yaml
import os
from flask import current_app, url_for

# STORY_DATA will now be a dictionary of dictionaries, e.g., {'en-US': {...}, 'zh-TW': {...}}
STORY_DATA = {}
UI_DATA = {}
IMAGE_KEYS = ['background', 'character_sprite', 'item_image', 'illustration']
AVAILABLE_LOCALES = []

def get_content_base_path():
    """Gets the base path to the versioned content, e.g., 'content/vn-story/v1'"""
    config = current_app.config
    project_root = config['PROJECT_ROOT']
    version = config['CONTENT_VERSION']
    return os.path.join(project_root, 'content', 'vn-story', version)

def load_story(app):
    """Loads all available languages from the content directory."""
    global STORY_DATA, UI_DATA, AVAILABLE_LOCALES
    STORY_DATA = {}
    UI_DATA = {}
    AVAILABLE_LOCALES = []

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    with app.app_context():
        content_base_path = os.path.join(project_root, 'content', 'vn-story', app.config['CONTENT_VERSION'])
        
        if not os.path.isdir(content_base_path):
            raise RuntimeError(f"Content directory not found at: {content_base_path}")

        locales_on_disk = [d for d in os.listdir(content_base_path) if os.path.isdir(os.path.join(content_base_path, d))]

        for locale in locales_on_disk:
            locale_path = os.path.join(content_base_path, locale)
            manifest_path = os.path.join(locale_path, '_manifest.yaml')

            if os.path.exists(manifest_path):
                print(f"Loading story for locale: {locale}")
                STORY_DATA[locale] = {}

                with open(manifest_path, 'r') as f:
                    manifest = yaml.safe_load(f)

                for story_filename in manifest.get('story_files', []):
                    file_path = os.path.join(locale_path, story_filename)
                    with open(file_path, 'r') as f:
                        nodes_from_file = yaml.safe_load(f)
                        for node in nodes_from_file:
                            STORY_DATA[locale][node['id']] = node
            
            ui_path = os.path.join(locale_path, 'ui.yaml')
            if os.path.exists(ui_path):
                print(f"Loading UI text for locale: {locale}")

                with open(ui_path, 'r') as f:
                    UI_DATA[locale] = yaml.safe_load(f)

        AVAILABLE_LOCALES = sorted(list(UI_DATA.keys()))
        print(f"Loading complete. Detected and loaded locales: {AVAILABLE_LOCALES}")

def get_available_locales():
    """Returns the list of locales that were successfully detected at startup."""
    return AVAILABLE_LOCALES

def get_ui_text(locale):
    """Returns the UI dictionary for a given locale, or a default."""
    default_locale = current_app.config['DEFAULT_LOCALE']
    return UI_DATA.get(locale, UI_DATA.get(default_locale, {}))

def get_node(node_id, locale):
    """Retrieves a single, unprocessed node for a specific locale."""
    return STORY_DATA.get(locale, {}).get(node_id)

def process_node_for_player(node_id, player_state, locale):
    """Gets a node, filters choices, and converts asset paths for a specific locale."""
    node = get_node(node_id, locale)
    if not node:
        return None

    processed_node = node.copy()

    config = current_app.config
    for key in IMAGE_KEYS:
        if key in processed_node and processed_node[key]:
            relative_path = processed_node[key]
            processed_node[key] = url_for('main.serve_content_asset', 
                                          version=config['CONTENT_VERSION'],
                                          locale=locale,
                                          filename=relative_path)
    
    if 'choices' in processed_node:
        available_choices = [
            choice for choice in processed_node.get('choices', [])
            if 'requires' not in choice or player_state.get(choice['requires']['state']) == choice['requires']['value']
        ]
        processed_node['choices'] = available_choices

    return processed_node

def perform_action(choice, player_state):
    """This function is language-agnostic and does not need to change."""
    if 'action' in choice:
        action = choice['action']
        if 'set_state' in action:
            state_key = action['set_state']
            value = action.get('value', True)
            player_state[state_key] = value
    return player_state