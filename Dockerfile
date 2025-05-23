
FROM python:3.9-slim

WORKDIR /app

# copy file
COPY requirements.txt .
COPY *.py .

# install package
RUN pip install --no-cache-dir -r requirements.txt

# port for cloud run
EXPOSE 8080

# env
ENV GCP_PROJECT_ID=""
ENV GCP_LOCATION=""
ENV MODEL_ARMOR_TEMPLATE_ID=""

# Streamlit cloud run 
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# run app
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]