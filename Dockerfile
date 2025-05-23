FROM python:3.9-slim

WORKDIR /app

# 필요한 파일 복사
COPY requirements.txt .
COPY *.py .

# 필요한 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 포트 설정 (Streamlit 기본 포트)
EXPOSE 8080

# 환경 변수 설정
ENV GCP_PROJECT_ID="releng-project"
ENV GCP_LOCATION="us-central1"
ENV MODEL_ARMOR_TEMPLATE_ID="test"

# Streamlit이 Cloud Run에서 제대로 작동하도록 설정
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# 애플리케이션 실행
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.enableCORS=false"]