import yaml
import os
from flask import current_app, url_for

STORY_DATA = {}
IMAGE_KEYS = ['background', 'character_sprite', 'item_image']

def get_content_path(locale=None):
    """Constructs the base path to the content for a given version and locale."""
    config = current_app.config
    if locale is None:
        locale = config['DEFAULT_LOCALE']
    version = config['CONTENT_VERSION']
    return os.path.join('content', 'vn-story', version, locale)

def load_story(app):
    """Loads the story from the manifest for the configured version and locale."""
    global STORY_DATA
    STORY_DATA = {}
    with app.app_context():
        base_path = get_content_path()
        manifest_path = os.path.join(base_path, '_manifest.yaml')
        print(f"Attempting to load story from: {manifest_path}")

        try:
            with open(manifest_path, 'r') as f:
                manifest = yaml.safe_load(f)
            
            for story_filename in manifest.get('story_files', []):
                file_path = os.path.join(base_path, story_filename)
                with open(file_path, 'r') as f:
                    nodes_from_file = yaml.safe_load(f)
                    for node in nodes_from_file:
                        STORY_DATA[node['id']] = node
            print(f"Story loading complete. Total nodes: {len(STORY_DATA)}")
        except FileNotFoundError:
            raise RuntimeError(f"FATAL: Could not find story manifest or its files at '{base_path}'")

def get_node(node_id):
    """Retrieves a single, unprocessed node from the loaded story data."""
    return STORY_DATA.get(node_id)

def process_node_for_player(node_id, player_state):
    """Gets a node, filters choices, and converts asset paths to full URLs."""
    node = get_node(node_id)
    if not node:
        return None

    processed_node = node.copy()

    config = current_app.config
    for key in IMAGE_KEYS:
        if key in processed_node and processed_node[key]:
            relative_path = processed_node[key]
            processed_node[key] = url_for('main.serve_content_asset', 
                                          version=config['CONTENT_VERSION'],
                                          locale=config['DEFAULT_LOCALE'],
                                          filename=relative_path)

    if 'choices' in processed_node:
        available_choices = [
            choice for choice in processed_node.get('choices', [])
            if 'requires' not in choice or player_state.get(choice['requires']['state']) == choice['requires']['value']
        ]
        processed_node['choices'] = available_choices

    return processed_node

def perform_action(choice, player_state):
    """Updates the player's state based on a choice's action."""
    if 'action' in choice:
        action = choice['action']
        if 'set_state' in action:
            state_key = action['set_state']
            value = action.get('value', True)
            player_state[state_key] = value
    return player_state