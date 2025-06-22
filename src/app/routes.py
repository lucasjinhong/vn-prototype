from flask import Blueprint, render_template, jsonify, request, session, send_from_directory, redirect, url_for, current_app
from .game_logic import get_node, process_node_for_player, perform_action, get_ui_text, get_available_locales
from .dynamic_question import generate_question
import os

main = Blueprint('main', __name__)

def new_game_session(locale):
    """Initializes session variables, now including the locale."""
    session['player_state'] = {}
    session['history'] = []
    session['locale'] = locale

def process_and_personalize(node_id, player_state, locale, player_name):
    """A new helper to centralize node processing and personalization."""
    processed_node = process_node_for_player(node_id, player_state, locale)
    return perform_name_replacement(processed_node, player_name)

def perform_name_replacement(node, player_name):
    """A helper function to replace 'Hero' with the player's name."""
    if not node or not player_name:
        return node
    
    if node.get('character') == "Hero":
        node['character'] = player_name
    
    if 'text' in node:
        node['text'] = node['text'].replace("Hero", player_name)

    return node

def get_full_processed_node(node_id):
    """
    This is the new, central function that does everything:
    1. Gets session data.
    2. Processes the node (adds asset URLs, filters choices).
    3. Personalizes the node (replaces 'Hero').
    4. Handles dynamic question generation.
    """
    locale = session.get('locale')
    player_name = session.get('player_name')
    player_state = session.get('player_state', {})
    
    processed_node = process_node_for_player(node_id, player_state, locale)
    personalized_node = perform_name_replacement(processed_node, player_name)

    if personalized_node and 'input_prompt' in personalized_node:
        prompt_data = personalized_node['input_prompt']

        if 'function' in prompt_data:
            function_name = prompt_data['function']
            generated_data = generate_question(function_name)

            if generated_data:
                session['correct_answer'] = generated_data['answer']
                personalized_node['text'] = personalized_node['text'].replace("{{question}}", generated_data['question'])
                session.modified = True

        elif 'answer' in prompt_data:
            session['correct_answer'] = prompt_data['answer']
            session.modified = True
            
    return personalized_node

@main.route('/')
def index_root():
    """Redirects the root URL to the default language."""
    return redirect(url_for('main.index', lang_code=current_app.config['DEFAULT_LOCALE']))

@main.route('/<lang_code>/')
def index(lang_code):
    """Serves the main HTML page with localized UI text."""
    session['locale'] = lang_code
    available_locales = get_available_locales()
    
    if lang_code not in available_locales:
        return redirect(url_for('main.index', lang_code=current_app.config['DEFAULT_LOCALE']))
    
    ui_text = get_ui_text(lang_code)
    
    return render_template(
        'index.html', 
        current_locale=lang_code, 
        locales=available_locales, # Pass the dynamic list to the template
        ui=ui_text
    )

@main.route('/api/node/<node_id>', methods=['GET'])
def get_node_data(node_id):
    """
    General purpose endpoint to get the data for any node by its ID.
    Used for starting the game and for jumping to nodes after text input.
    """
    if 'player_name' not in session:
        return jsonify({'error': 'Game session not initialized.'}), 403

    locale = session.get('locale')
    player_name = session.get('player_name')
    player_state = session.get('player_state', {})

    processed_node = process_node_for_player(node_id, player_state, locale)
    personalized_node = perform_name_replacement(processed_node, player_name)

    if not personalized_node:
        return jsonify({'error': f'Node "{node_id}" not found.'}), 404

    if session['history'][-1] != node_id:
        session['history'].append(node_id)
        session.modified = True

    return jsonify(personalized_node)

@main.route('/api/start', methods=['POST'])
def start_game():
    """Initializes the game session with the player's name and locale."""
    data = request.json
    player_name = data.get('name', 'Hero').strip() or "Hero"
    
    session['player_state'] = {}
    session['history'] = []
    session['player_name'] = player_name
    session['locale'] = data.get('locale', current_app.config['DEFAULT_LOCALE'])
    
    # Call our new central function
    start_node = get_full_processed_node('start')
    
    if not start_node:
        return jsonify({'error': 'Start node not found'}), 404
        
    session['history'] = ['start'] # Reset history after getting the node
    session.modified = True
    return jsonify(start_node)

@main.route('/api/choose', methods=['POST'])
def make_choice():
    """Handles a choice, gets the next node, and personalizes it."""
    data = request.json
    node_id = data.get('node_id')
    choice_index = data.get('choice_index')
    
    locale = session.get('locale')
    original_node = get_node(node_id, locale)
    if not original_node or choice_index >= len(original_node.get('choices', [])):
        return jsonify({'error': 'Invalid choice or node ID'}), 400

    selected_choice = original_node['choices'][choice_index]
    player_state = perform_action(selected_choice, session.get('player_state', {}))
    session['player_state'] = player_state

    next_node_id = selected_choice['next_node']
    session['history'].append(next_node_id)
    session.modified = True
    
    next_node_data = get_full_processed_node(next_node_id)
    
    return jsonify(next_node_data)

@main.route('/api/back', methods=['POST'])
def go_back():
    """Goes back one step and returns the personalized previous node."""
    history = session.get('history', [])
    if len(history) < 2:
        return jsonify({'error': 'No previous step to go back to.'}), 400

    history.pop()
    previous_node_id = history[-1]
    
    locale = session.get('locale')
    player_name = session.get('player_name')
    player_state = session.get('player_state', {})
    previous_node_processed = process_node_for_player(previous_node_id, player_state, locale)
    previous_node_personalized = perform_name_replacement(previous_node_processed, player_name)
    
    session['history'] = history
    session.modified = True
    
    return jsonify(previous_node_personalized)

@main.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    user_answer = data.get('answer', '').strip().lower()
    node_id = data.get('node_id')

    correct_answer = session.get('correct_answer')
    
    original_node = get_node(node_id, session.get('locale'))
    paths = original_node.get('input_prompt', {})

    if user_answer == correct_answer:
        next_node_id = paths.get('on_correct')
    else:
        next_node_id = paths.get('on_incorrect')
    
    next_node_data = get_full_processed_node(next_node_id)
    session['history'].append(next_node_id)
    session.modified = True

    return jsonify(next_node_data)

@main.route('/content/<version>/<locale>/<path:filename>')
def serve_content_asset(version, locale, filename):
    project_root = current_app.config['PROJECT_ROOT']
    content_path = os.path.join(project_root, 'content', 'vn-story', version, locale)
    return send_from_directory(content_path, filename)