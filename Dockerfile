FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    libmupdf-dev curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY pipeline/ ./pipeline/
COPY demo/ ./demo/
ENV GEMINI_API_KEY=""
ENV MINIMAX_API_KEY=""
EXPOSE 5050
HEALTHCHECK --interval=30s --timeout=10s \
  CMD curl -f http://localhost:5050/health || exit 1
CMD ["python", "pipeline/app.py"]
