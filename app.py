from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

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
        
        prompt = f"""Create a detailed strategy to achieve:
        Goal: {goal}
        Deadline: {deadline} ({days_remaining} days remaining)
        Daily Time Available: {free_time} hours

        Provide:
        1. Weekly/Monthly milestones
        2. Concrete daily actions
        3. Potential obstacles and solutions
        4. Recommended learning resources"""
        
        try:
            response = model.generate_content(prompt)
            strategy = response.text
        except Exception as e:
            strategy = f"Error generating strategy: {str(e)}"
        
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
    
    conversations[session_id].append({"role": "user", "parts": [user_message]})
    
    try:
        response = model.generate_content(conversations[session_id])
        ai_message = response.text
        conversations[session_id].append({"role": "model", "parts": [ai_message]})
        return jsonify({'response': ai_message, 'session_id': session_id})
    except Exception as e:
        return jsonify({'response': f"Error: {str(e)}", 'session_id': session_id})

if __name__ == '__main__':
    app.run(debug=True)
