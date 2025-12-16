#!/usr/bin/env bash
# Docker 이미지 빌드 및 검증 스크립트
# GitHub workflow의 build-docker-image job과 동일한 작업 수행

set -euo pipefail

echo "=================================="
echo "Docker Image 빌드 및 검증"
echo "=================================="
echo ""

# Repository 정보
REPO_NAME="${1:-memo-test1}"
IMAGE_TAG="${2:-$(git rev-parse --short HEAD)}"

echo "📦 Docker 이미지 정보"
echo "  이미지 이름: ${REPO_NAME}"
echo "  이미지 태그: ${IMAGE_TAG}"
echo ""

# Docker 이미지 빌드
echo "🔨 Docker 이미지 빌드 시작..."
docker build \
  --tag "${REPO_NAME}:${IMAGE_TAG}" \
  --tag "${REPO_NAME}:latest" \
  --file Dockerfile \
  .

echo "✅ Docker 이미지 빌드 완료"
echo ""

# 이미지 존재 확인
echo "🔍 Docker 이미지 검증 중..."

if ! docker images "${REPO_NAME}:${IMAGE_TAG}" --format "{{.Repository}}:{{.Tag}}" | grep -q "${REPO_NAME}:${IMAGE_TAG}"; then
  echo "❌ 오류: Docker 이미지를 찾을 수 없습니다 (${REPO_NAME}:${IMAGE_TAG})"
  echo ""
  echo "사용 가능한 이미지 목록:"
  docker images "${REPO_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" || true
  exit 1
fi

echo "✓ 이미지 존재 확인 완료"
echo ""

# 이미지 상세 정보 출력
echo "=== Docker 이미지 정보 ==="
docker images "${REPO_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
echo ""

# 이미지 메타데이터 검증
echo "=== 이미지 메타데이터 ==="
docker inspect "${REPO_NAME}:${IMAGE_TAG}" --format='
- Repository: {{.RepoTags}}
- 생성 시간: {{.Created}}
- 아키텍처: {{.Architecture}}
- OS: {{.Os}}
- 크기: {{.Size}} bytes
- Exposed Ports: {{.Config.ExposedPorts}}
- Cmd: {{.Config.Cmd}}'
echo ""

echo "✅ Docker 이미지 검증 완료"
echo ""
echo "빌드된 이미지:"
echo "  - ${REPO_NAME}:${IMAGE_TAG}"
echo "  - ${REPO_NAME}:latest"
echo ""

# ============================================
# 컨테이너 실행 테스트
# ============================================
echo "=================================="
echo "컨테이너 실행 테스트"
echo "=================================="
echo ""

# 기존 테스트 컨테이너 정리 (포트 충돌 방지)
echo "기존 테스트 컨테이너 정리 중..."
EXISTING_CONTAINERS=$(docker ps -a --filter "ancestor=${REPO_NAME}" --format "{{.ID}}" || true)
if [ -n "$EXISTING_CONTAINERS" ]; then
  echo "발견된 컨테이너: ${EXISTING_CONTAINERS}"
  docker rm -f $EXISTING_CONTAINERS > /dev/null 2>&1 || true
  echo "✓ 정리 완료"
else
  echo "✓ 정리할 컨테이너 없음"
fi
echo ""

echo "컨테이너를 실행하고 애플리케이션 응답을 확인합니다..."

# 컨테이너 실행 (백그라운드)
CONTAINER_ID=$(docker run -d \
  -p 8501:8501 \
  -e DATABASE_URL="postgresql://test:test@localhost:5432/test" \
  "${REPO_NAME}:${IMAGE_TAG}")

echo "컨테이너 ID: ${CONTAINER_ID}"
echo ""

# 애플리케이션 시작 대기 및 Health Check (최대 30초)
# 우선순위: 1) environment variable, 2) default
HEALTH_CHECK_PATH="${HEALTH_CHECK_PATH:-/api/health}"
echo "애플리케이션 시작 대기 중 (health check 확인: ${HEALTH_CHECK_PATH})..."
APP_READY=false

for i in {1..30}; do
  # Health check endpoint에 요청
  if curl -f -s "http://localhost:8501${HEALTH_CHECK_PATH}" > /dev/null 2>&1; then
    echo "✓ 애플리케이션이 응답합니다 (${i}초 경과)"
    APP_READY=true
    break
  fi

  # 컨테이너가 종료되었는지 확인 (조기 실패 감지)
  # docker ps --quiet는 짧은 ID(12자)를 반환하므로, 출력 존재 여부로 확인
  PS_OUTPUT=$(docker ps --quiet --filter "id=${CONTAINER_ID}")
  if [ -z "$PS_OUTPUT" ]; then
    echo "⚠️  컨테이너가 종료되었습니다. 로그를 확인합니다..."
    break
  fi

  sleep 1
done

# 결과 출력
echo ""
echo "=== 검증 결과 ==="

if [ "$APP_READY" = true ]; then
  # 성공: 애플리케이션이 응답함
  echo "✓ Health check 성공"
  HEALTH_RESPONSE=$(curl -s "http://localhost:8501${HEALTH_CHECK_PATH}")
  echo "응답: ${HEALTH_RESPONSE}"

  echo ""
  echo "=== 컨테이너 로그 ==="
  docker logs "${CONTAINER_ID}" 2>&1 | tail -n 20

  # 컨테이너 정리
  echo ""
  echo "컨테이너 중지 및 삭제 중..."
  docker stop "${CONTAINER_ID}" >/dev/null 2>&1 || true
  docker rm "${CONTAINER_ID}" >/dev/null 2>&1 || true

  echo ""
  echo "✅ Docker 이미지 검증 완료 - 애플리케이션이 정상적으로 응답합니다"
else
  # 실패: 애플리케이션이 응답하지 않음
  echo "❌ 오류: 애플리케이션이 30초 내에 응답하지 않았습니다"
  echo ""

  # 컨테이너 상태 확인
  if docker ps --quiet --filter "id=${CONTAINER_ID}" | grep -q "${CONTAINER_ID}"; then
    echo "컨테이너는 실행 중이지만 HTTP 요청에 응답하지 않습니다"
  else
    echo "컨테이너가 종료되었습니다"
    EXIT_CODE=$(docker inspect "${CONTAINER_ID}" --format='{{.State.ExitCode}}' 2>/dev/null || echo "unknown")
    echo "Exit code: ${EXIT_CODE}"
  fi

  echo ""
  echo "=== 컨테이너 로그 ==="
  docker logs "${CONTAINER_ID}" 2>&1

  # 컨테이너 정리
  docker rm -f "${CONTAINER_ID}" 2>/dev/null || true

  exit 1
fi
