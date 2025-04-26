from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch
import os
from loguru import logger
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

# Configure logging
logger.add("/app/agent.log", rotation="500 MB")

# Model configuration
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

# Device map for CPU offloading
device_map = {
    "model.embed_tokens": "cpu",
    "model.norm": "cpu",
    "lm_head": "cpu",
    "model.layers": "auto"
}

try:
    # Load model and tokenizer
    model_path = os.getenv('MODEL_PATH', '/app/models/Llama-2-7b-hf')
    logger.info(f"Loading model from {model_path}")
    
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True,
        local_files_only=True
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        quantization_config=quantization_config,
        torch_dtype=torch.float16,
        device_map="auto",
        low_cpu_mem_usage=True,
        trust_remote_code=True,
        local_files_only=True
    )
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Error loading model: {str(e)}")
    raise

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        topic = data.get('topic')
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
            
        context = data.get('context', '')
        
        prompt = f"""Topic: {topic}
Context: {context}
Generate a strong argument supporting the given topic. Focus on the benefits and advantages:"""
        
        logger.info(f"Generating response for topic: {topic}")
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)[len(prompt):]
        
        logger.info("Response generated successfully")
        
        return jsonify({
            'argument': response.strip(),
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Error in generate endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    if not model or not tokenizer:
        return jsonify({'status': 'unhealthy', 'error': 'Model not loaded'}), 500
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 