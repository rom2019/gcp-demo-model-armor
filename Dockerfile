
FROM python:3.9-slim

WORKDIR /app

# 필요한 파일 복사
COPY requirements.txt .
COPY *.py .

# 필요한 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 포트 설정 (Cloud Run에서 사용할 포트)
EXPOSE 8080

# 환경 변수 설정 (배포시 반드시 설정해야 함)
ENV GCP_PROJECT_ID=""
ENV GCP_LOCATION=""
ENV MODEL_ARMOR_TEMPLATE_ID=""

# Streamlit이 Cloud Run에서 제대로 작동하도록 설정
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# 헬스체크를 위한 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# 애플리케이션 실행
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]