from flask import Flask, request, jsonify
import requests
import os
import json

app = Flask(__name__)

# Configure JSON encoder for Korean
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return json.JSONEncoder.default(self, obj)
        except TypeError:
            return str(obj)

app.json_encoder = CustomJSONEncoder

AGENT_PRO_URL = "http://agent_pro:5000"
AGENT_CON_URL = "http://agent_con:5000"

@app.route('/debate/start', methods=['POST'])
def start_debate():
    data = request.json
    topic = data.get('topic')
    context = data.get('context', '')
    rounds = data.get('rounds', 1)
    
    debate_history = []
    current_context = context
    
    for round in range(rounds):
        # Get Pro argument
        pro_response = requests.post(f"{AGENT_PRO_URL}/generate", 
                                   json={'topic': topic, 'context': current_context})
        pro_argument = pro_response.json()['argument']
        
        # Update context with pro argument
        current_context = f"{current_context}\n찬성 측 주장: {pro_argument}"
        
        # Get Con argument
        con_response = requests.post(f"{AGENT_CON_URL}/generate", 
                                   json={'topic': topic, 'context': current_context})
        con_argument = con_response.json()['argument']
        
        # Update context with con argument
        current_context = f"{current_context}\n반대 측 주장: {con_argument}"
        
        # Save this round's arguments
        debate_history.append({
            'round': round + 1,
            'pro_argument': pro_argument,
            'con_argument': con_argument
        })
    
    return jsonify({
        'topic': topic,
        'context': context,
        'rounds': rounds,
        'debate_history': debate_history,
        'status': 'completed'
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 