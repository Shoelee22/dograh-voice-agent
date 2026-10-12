FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY lead_server.py .
EXPOSE 8090
CMD ["uvicorn", "lead_server:app", "--host", "0.0.0.0", "--port", "8090"]
