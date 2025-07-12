from flask import Flask, render_template, request, jsonify
import openai
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Store conversations in memory (per session)
conversations = {}

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Get form data
        goal = request.form.get('goal')
        deadline = request.form.get('deadline')
        free_time = float(request.form.get('free_time'))
        
        # Calculate time until deadline
        deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
        today = datetime.now()
        days_remaining = (deadline_date - today).days
        
        # Generate AI strategy
        prompt = f"""
        Create a detailed strategy to achieve the following goal:
        Goal: {goal}
        Deadline: {deadline} ({days_remaining} days from now)
        Available time per day: {free_time} hours
        
        Provide:
        1. A breakdown of milestones (weekly/monthly)
        2. Daily action items
        3. Potential obstacles and solutions
        4. Recommended resources
        
        Format the response with clear headings and bullet points.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            strategy = response.choices[0].message.content
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
    
    # Get or initialize conversation history
    if session_id not in conversations:
        conversations[session_id] = []
    
    # Add user message to conversation history
    conversations[session_id].append({"role": "user", "content": user_message})
    
    try:
        # Get AI response
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversations[session_id],
            temperature=0.7
        )
        ai_message = response.choices[0].message.content
        
        # Add AI response to conversation history
        conversations[session_id].append({"role": "assistant", "content": ai_message})
        
        return jsonify({'response': ai_message, 'session_id': session_id})
    except Exception as e:
        return jsonify({'response': f"Error: {str(e)}", 'session_id': session_id})

if __name__ == '__main__':
    app.run(debug=True)