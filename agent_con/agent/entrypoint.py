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
        
        prompt = f"""[시스템] 당신은 주어진 주제에 대해 반대 입장을 가진 한국인 전문가입니다. 반드시 한국어로만 답변해야 합니다.

[주제] {topic}
[맥락] {context}

[지시사항]
다음 관점들을 고려하여 한국어로 논리적이고 설득력 있는 반대 논거를 제시해주세요:

1. 주제의 부정적 측면과 위험성을 구체적으로 설명
2. 예상되는 문제점과 한계를 데이터나 사례와 함께 제시
3. 유사한 상황의 반례나 실패 사례 분석
4. 현실적인 대안이나 개선방안 제안

[작성 규칙]
- 반드시 한국어로만 작성할 것
- 각 주장에 구체적인 예시와 근거 포함
- 감정적이지 않고 논리적인 관점 유지
- 찬성 측 주장에 대한 구체적인 반박 포함
- 단순 반복이나 모호한 표현 사용 금지

[한국어로 반대 논거를 작성해주세요]"""
        
        logger.info(f"Generating response for topic: {topic}")
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.8,
            do_sample=True,
            top_p=0.95,
            repetition_penalty=1.2,
            no_repeat_ngram_size=3,
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