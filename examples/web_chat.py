import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from flask import Flask, render_template, request, jsonify
from core.pipeline import TCAPipeline
from memory.langraph_adapter import LangGraphMemoryAdapter
from dotenv import load_dotenv

load_dotenv()

# Initialize Flask app with the correct template folder
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
app = Flask(__name__, template_folder=template_dir)

user_id = "web_user"
mode = "therapist"

# Initialize pipeline
prior_state = LangGraphMemoryAdapter.load_checkpoint(user_id)
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

    result = pipeline.process(user_input)
    
    # Save updated memory
    LangGraphMemoryAdapter.save_checkpoint(user_id, pipeline.to_dict())
    
    return jsonify({
        'response': result['response'],
        'timestamp': result.get('timestamp', '')
    })

if __name__ == '__main__':
    app.run(debug=True) 