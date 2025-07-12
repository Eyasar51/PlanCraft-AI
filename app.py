from flask import Flask, render_template, request, jsonify
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')  # If available
HF_TOKEN = os.getenv('HF_TOKEN')  # Hugging Face free token

def get_ai_response(messages, provider="huggingface"):
    """Unified AI response handler with fallback"""
    
    if provider == "deepseek" and DEEPSEEK_API_KEY:
        # Deepseek API call (if available)
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.7
        }
        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=payload
            ).json()
            return response['choices'][0]['message']['content']
        except:
            pass  # Fallthrough to Hugging Face

    # Hugging Face fallback (always available)
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": messages[-1]["content"],  # Use last message
        "parameters": {"max_length": 500}
    }
    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/deepseek-ai/deepseek-llm-7b",
            headers=headers,
            json=payload
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
        
        prompt = f"""Create a goal strategy:
        Goal: {goal}
        Deadline: {days_remaining} days
        Daily Time: {free_time} hours"""
        
        strategy = get_ai_response(
            [{"role": "user", "content": prompt}],
            provider="deepseek"  # Try Deepseek first
        )
        
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
    
    ai_message = get_ai_response(
        conversations[session_id],
        provider="deepseek"  # Try Deepseek first
    )
    
    conversations[session_id].append({"role": "assistant", "content": ai_message})
    return jsonify({'response': ai_message, 'session_id': session_id})

if __name__ == '__main__':
    app.run(debug=True)
