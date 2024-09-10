FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN python -m venv /app/venv

RUN /app/venv/bin/pip install --upgrade pip && \
    /app/venv/bin/pip install --no-cache-dir -r requirements.txt

COPY /path/to/local/llama_model /app/llama_model

EXPOSE 8000

CMD ["/app/venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
