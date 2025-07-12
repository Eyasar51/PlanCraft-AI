from flask import Flask, render_template, request, jsonify
import requests  # For API calls (no heavy ML libs needed)
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialize conversations in memory
conversations = {}

# Hugging Face API settings
HF_API_URL = "https://api-inference.huggingface.co/models/deepseek-ai/deepseek-llm-7b"
HF_TOKEN = os.getenv("HF_TOKEN")  # Get from https://huggingface.co/settings/tokens

def query_huggingface(prompt):
    """Get AI response from Hugging Face API"""
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    try:
        response = requests.post(
            HF_API_URL,
            headers=headers,
            json={"inputs": prompt}
        ).json()
        return response[0]['generated_text']
    except Exception as e:
        return f"AI Error: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        goal = request.form.get('goal')
        deadline = request.form.get('deadline')
        free_time = float(request.form.get('free_time'))
        
        deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
        days_remaining = (deadline_date - datetime.now()).days
        
        prompt = f"""Create a step-by-step plan to achieve:
        Goal: {goal}
        Timeframe: {days_remaining} days
        Daily Time: {free_time} hours
        
        Include:
        1. Weekly milestones
        2. Daily tasks
        3. Potential obstacles"""
        
        strategy = query_huggingface(prompt)
        return render_template('index.html', 
                            goal=goal,
                            deadline=deadline,
                            free_time=free_time,
                            strategy=strategy)
    
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data['message']
    session_id = data.get('session_id', 'default')
    
    if session_id not in conversations:
        conversations[session_id] = []
    
    conversations[session_id].append({"role": "user", "content": user_message})
    ai_response = query_huggingface(user_message)
    conversations[session_id].append({"role": "assistant", "content": ai_response})
    
    return jsonify({'response': ai_response, 'session_id': session_id})

if __name__ == '__main__':
    app.run(debug=True)
