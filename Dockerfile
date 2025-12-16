# ============================================
# Multi-stage Dockerfile
# Frontend (React + Vite) + Backend (FastAPI)를 하나의 이미지로 패키징
# ============================================

# ============================================
# Stage 1: Frontend 빌드
# ============================================
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Frontend 의존성 파일 복사 및 설치
# package.json과 package-lock.json을 먼저 복사하여 Docker 캐시 활용
COPY frontend/package*.json ./
RUN npm ci

# Frontend 소스 코드 복사
COPY frontend/ ./

# Frontend 빌드 (Vite)
# 결과물은 /app/frontend/dist 에 생성됨
RUN npm run build

# 빌드 결과 확인
RUN ls -la /app/frontend/dist && \
    echo "✅ Frontend 빌드 완료"

# ============================================
# Stage 2: Backend + Frontend Static Files
# ============================================
FROM python:3.11-slim AS production

# 작업 디렉토리 설정
WORKDIR /app

# 메타데이터 설정
LABEL maintainer="ignite-pilot"
LABEL description="Memo Test1 Application - Backend + Frontend"
LABEL version="1.0.0"

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
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

# uv 설치 (Python 패키지 관리 도구)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Backend 코드 복사
COPY backend/ ./backend/
COPY config/ ./config/

# Frontend 빌드 결과 복사 (Stage 1에서)
# Backend가 frontend/dist 경로에서 static files를 서빙하도록 설정되어 있음
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Frontend 빌드 결과 확인
RUN ls -la /app/frontend/dist && \
    echo "✅ Frontend static files 복사 완료"

# Backend 작업 디렉토리로 이동
WORKDIR /app/backend

# Backend 의존성 설치
RUN if command -v uv &> /dev/null; then \
        echo "Using uv for package installation..."; \
        uv pip install --system -r requirements.txt; \
    else \
        echo "Using pip for package installation..."; \
        pip install --no-cache-dir -r requirements.txt; \
    fi

# 의존성 설치 확인
RUN python -c "import fastapi; import uvicorn; print('✅ Backend 의존성 설치 완료')"

# 포트 노출
# 8501: Backend API 및 Frontend Static Files 서빙
EXPOSE 8501

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8501
ENV PHASE=alpha

# AWS Secrets Manager 사용 여부 (기본값: false)
# - 로컬 개발: false (환경변수 fallback 사용)
# - ECS 배포: secrets.py가 자동으로 ECS 환경 감지하여 true로 변경
# - 또는 PHASE=alpha/beta/production이면 자동으로 AWS Secrets Manager 시도
# - 명시적 활성화: docker run 시 -e USE_AWS_SECRETS=true 전달
# - 명시적 비활성화: docker run 시 -e USE_AWS_SECRETS=false 전달
ENV USE_AWS_SECRETS=false

# 애플리케이션 실행
# uvicorn으로 FastAPI 서버 시작
# - Backend API는 /api/* 경로에서 서빙
# - Frontend는 / 및 기타 경로에서 서빙
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8501"]
