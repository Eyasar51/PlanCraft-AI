from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Correct Gemini 1.0 Pro configuration
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.0-pro')  # Updated model name

conversations = {}

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        goal = request.form.get('goal')
        deadline = request.form.get('deadline')
        free_time = float(request.form.get('free_time'))
        
        deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
        today = datetime.now()
        days_remaining = (deadline_date - today).days
        
        prompt = f"""Create a step-by-step plan:
        Goal: {goal}
        Timeframe: {days_remaining} days
        Daily Time: {free_time} hours

        Include:
        1. Weekly targets
        2. Daily tasks
        3. Potential roadblocks
        4. Learning resources"""
        
        try:
            response = model.generate_content(prompt)
            strategy = response.text
        except Exception as e:
            strategy = f"Error: {str(e)}"
        
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
    
    try:
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(user_message)
        conversations[session_id].append({"role": "model", "content": response.text})
        return jsonify({'response': response.text, 'session_id': session_id})
    except Exception as e:
        return jsonify({'response': f"Error: {str(e)}", 'session_id': session_id})

if __name__ == '__main__':
    app.run(debug=True)
