# ACBS RAG Agent — HF Spaces compatible Docker image
FROM python:3.12-slim

# System deps (build-essential cho sentence-transformers, git cho HF model download)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# HF Spaces chạy với user `user` (uid 1000) cho permission an toàn
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python deps trước (Docker layer cache)
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download embedding model vào HF cache lúc build (~1.4GB)
# Tránh runtime download chậm + fail nếu HF rate-limit
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('AITeamVN/Vietnamese_Embedding', trust_remote_code=True)"

# Copy app code + data (chunks.jsonl + chromadb folder)
COPY --chown=user:user app.py .
COPY --chown=user:user data/ /app/data/

# HF Spaces required port
EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
