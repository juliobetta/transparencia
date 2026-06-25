FROM python:3.12-slim
RUN apt-get update && apt-get install -y make curl git
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN /root/.cargo/bin/uv sync
COPY . .
EOF
