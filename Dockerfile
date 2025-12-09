# 루트 디렉토리용 Dockerfile
# 전체 프로젝트를 포함하여 빌드

FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    git \
    curl \
    jq \
    unzip \
    bash \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# AWS CLI 설치
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf aws awscliv2.zip

# uv 설치
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# 전체 프로젝트 복사
COPY . .

# Backend 디렉토리로 이동하여 의존성 설치
WORKDIR /app/backend

# uv를 사용하여 의존성 설치 (requirements.txt 기반)
# uv가 없을 경우를 대비해 pip도 사용 가능하도록 설정
RUN if command -v uv &> /dev/null; then \
        uv pip install --system -r requirements.txt; \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi

# 작업 디렉토리를 backend로 설정
WORKDIR /app/backend

# 포트 노출 (프로젝트에서 사용하는 포트)
EXPOSE 8501

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8501
ENV PHASE=alpha

# 헬스 체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/api/health || exit 1

# 서버 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8501"]
