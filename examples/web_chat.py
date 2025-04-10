import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from flask import Flask, render_template, request, jsonify
from core.pipeline import TCAPipeline
from memory.langraph_adapter import LangGraphMemoryAdapter
from memory.memory_store import (
    get_user_id, 
    load_user_memory, 
    save_user_memory, 
    get_user_profile,
    update_user_profile
)
from dotenv import load_dotenv

load_dotenv()

# Initialize Flask app with the correct template folder
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
app = Flask(__name__, template_folder=template_dir)

# Get user ID from environment variable or use default
user_id = get_user_id()
mode = "therapist"

# Initialize pipeline with user profile data
user_profile = get_user_profile(user_id)
prior_state = LangGraphMemoryAdapter.load_checkpoint(user_id)

# If no prior state exists, create a new one with user profile data
if not prior_state:
    prior_state = {
        "session_memory": {
            "user_profile": user_profile,
            "last_interaction": None
        },
        "turns": [],
        "components": {}
    }

pipeline = TCAPipeline(mode)
pipeline.load(prior_state)

@app.route('/')
def home():
    return render_template('chat.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    user_input = request.json.get('message', '')
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400

    # Process the message through the pipeline
    result = pipeline.process(user_input)
    
    # Save updated memory
    LangGraphMemoryAdapter.save_checkpoint(user_id, pipeline.to_dict())
    
    return jsonify({
        'response': result['response'],
        'timestamp': result.get('timestamp', '')
    })

@app.route('/update_profile', methods=['POST'])
def update_profile():
    profile_data = request.json.get('profile', {})
    if not profile_data:
        return jsonify({'error': 'No profile data provided'}), 400
        
    try:
        # Update the user profile in MongoDB
        update_user_profile(user_id, profile_data)
        
        # Also update the pipeline's user profile
        pipeline.user_profile.update(profile_data)
        
        # Save the updated state
        LangGraphMemoryAdapter.save_checkpoint(user_id, pipeline.to_dict())
        
        return jsonify({'status': 'success', 'message': 'Profile updated successfully'})
    except Exception as e:
        return jsonify({'error': f'Failed to update profile: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True) 