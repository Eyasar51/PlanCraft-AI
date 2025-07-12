from flask import Flask, render_template, request, jsonify
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Load Gemma 3B
model_name = "google/gemma-3b-it"  # Instruction-tuned version
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")

def generate_response(prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    outputs = model.generate(**inputs, max_length=500)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

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
        
        prompt = f"""<<SYS>>You are a goal-planning assistant. Provide:
        1. Weekly milestones
        2. Daily action items
        3. Potential obstacles
        <</SYS>>

        Goal: {goal}
        Deadline: {days_remaining} days
        Daily Time: {free_time} hours"""
        
        try:
            strategy = generate_response(prompt)
        except Exception as e:
            strategy = f"Error: {str(e)}"
        
        return render_template('index.html', 
                           goal=goal,
                           deadline=deadline,
                           free_time=free_time,
                           strategy=strategy)
    
    return render_template('index.html')

# ... (keep existing /chat endpoint logic)
