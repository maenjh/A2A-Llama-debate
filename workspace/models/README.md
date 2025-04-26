# Llama-2 모델 설치 가이드

이 디렉토리에는 Llama-2-7b 모델 파일이 위치해야 합니다.

## 모델 다운로드 방법

1. Hugging Face에서 Llama-2-7b-hf 모델 접근 권한 획득
   - https://huggingface.co/meta-llama/Llama-2-7b-hf 페이지 방문
   - Meta의 라이선스 동의 및 접근 권한 요청

2. 모델 다운로드
```bash
# Hugging Face 토큰으로 로그인
huggingface-cli login

# 모델 다운로드
git lfs install
git clone https://huggingface.co/meta-llama/Llama-2-7b-hf
```

3. 다운로드한 모델 파일을 이 디렉토리에 복사
```bash
cp -r Llama-2-7b-hf/* .
```

## 주의사항
- 이 디렉토리에는 실제 모델 파일을 포함하지 마세요
- 모델 파일은 `.gitignore`에 포함되어 있습니다
- 라이선스 및 사용 조건을 반드시 확인하세요 