from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
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
        
        prompt = f"""Create a step-by-step plan to achieve this goal:
        Goal: {goal}
        Deadline: {days_remaining} days from now
        Available time: {free_time} hours/day

        Include:
        1. Weekly milestones
        2. Daily action items
        3. Potential obstacles
        4. Recommended resources"""
        
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
        chat_session = model.start_chat(history=conversations[session_id])
        response = chat_session.send_message(user_message)
        ai_message = response.text
        conversations[session_id].append({"role": "model", "content": ai_message})
        return jsonify({'response': ai_message, 'session_id': session_id})
    except Exception as e:
        return jsonify({'response': f"Error: {str(e)}", 'session_id': session_id})

if __name__ == '__main__':
    app.run(debug=True)
