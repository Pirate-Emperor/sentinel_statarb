FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY . /workspace
RUN python -m pip install --no-cache-dir --upgrade pip && python -m pip install --no-cache-dir -e ".[ipc,storage,dev]"
CMD ["bash", "scripts/run_checks.sh"]
