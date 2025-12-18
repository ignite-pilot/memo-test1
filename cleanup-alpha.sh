#!/usr/bin/env bash
set -euo pipefail

# jq 설치 확인
if ! command -v jq &> /dev/null; then
  echo "오류: jq가 설치되어 있지 않습니다. JSON 파싱을 위해 jq가 필요합니다."
  echo ""
  echo "설치 방법:"
  echo "  macOS: brew install jq"
  echo "  Ubuntu/Debian: sudo apt-get install jq"
  echo "  CentOS/RHEL: sudo yum install jq"
  exit 1
fi

# GitHub token 확인
if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "오류: GITHUB_TOKEN 환경변수가 없습니다. 이 스크립트는 그 환경변수에 'repo' 및 'workflow' 권한이 있다고 가정합니다."
  echo ""
  echo "스크립트 실행:"
  echo "  GITHUB_TOKEN=<전달받은 Github Personal Token> ./cleanup-alpha.sh"
  exit 1
fi

# Repository 정보
OWNER="ignite-pilot"
REPO="memo-test1"
WORKFLOW_FILE="cleanup-alpha.yml"

# Custom 인자 처리
IMAGE_NAME="${1:-memo-test1}"
BRANCH="${2:-main}"

echo "=========================================="
echo "⚠️  Alpha 환경 리소스 정리"
echo "=========================================="
echo ""
echo "이 스크립트는 다음 AWS 리소스를 삭제합니다:"
echo "  - ECR Repository (모든 Docker 이미지 포함)"
echo "  - ECS Service 및 Task Definitions"
echo "  - Application Load Balancer 및 Target Group"
echo "  - Route 53 DNS 레코드"
echo "  - Security Groups (ALB, ECS)"
echo ""
echo "Repository       : ${OWNER}/${REPO}"
echo "Application      : ${IMAGE_NAME}"
echo "Branch           : ${BRANCH}"
echo ""

# 사용자 확인
read -p "정말로 삭제하시겠습니까? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "❌ 정리가 취소되었습니다."
  exit 0
fi

echo ""
echo "=================================="
echo "GitHub Workflow 실행"
echo "=================================="
echo ""

# GitHub API를 통해 workflow dispatch
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW_FILE}/dispatches" \
  -d "{
    \"ref\": \"${BRANCH}\",
    \"inputs\": {
      \"image_name\": \"${IMAGE_NAME}\",
      \"deployment_phase\": \"alpha\",
      \"delete_ecr_repository\": \"true\",
      \"delete_ecs_service\": \"true\",
      \"delete_ecs_cluster\": \"false\",
      \"delete_load_balancer\": \"true\",
      \"delete_dns_records\": \"true\",
      \"delete_security_groups\": \"true\",
      \"delete_logs\": \"false\",
      \"delete_iam_role\": \"false\",
      \"confirmation\": \"DELETE\"
    }
  }")

# HTTP 상태 코드 추출
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

# 결과 확인
if [ "$HTTP_CODE" -ne 204 ]; then
  echo "❌ Workflow 호출 실패 (HTTP ${HTTP_CODE})!!"
  if [ -n "$BODY" ]; then
    echo "${BODY}"
  fi
  echo "자세한 내용은 담당자에게 문의하세요."
  exit 1
fi

echo "✅ Cleanup Workflow를 시작했습니다."
echo ""

# Workflow run이 생성될 때까지 대기
echo "Workflow run이 생성될 때까지 대기 중..."
sleep 5

# 최근 workflow run ID 가져오기
RUNS_RESPONSE=$(curl -s \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW_FILE}/runs?per_page=1&branch=${BRANCH}")

RUN_ID=$(echo "$RUNS_RESPONSE" | jq -r '.workflow_runs[0].id')
RUN_URL=$(echo "$RUNS_RESPONSE" | jq -r '.workflow_runs[0].html_url')

if [ -z "$RUN_ID" ] || [ "$RUN_ID" = "null" ]; then
  echo "❌ Workflow run ID를 가져올 수 없습니다."
  echo "GitHub Actions 페이지에서 직접 확인해주세요: https://github.com/${OWNER}/${REPO}/actions"
  echo "자세한 내용은 담당자에게 문의하세요."
  exit 1
fi

echo "Workflow run ID: ${RUN_ID}"
echo "Workflow URL: ${RUN_URL}"
echo ""
echo "상태를 모니터링합니다..."
echo ""

# 스피너 문자 배열
SPINNER=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
SPINNER_IDX=0

# 상태 확인 루프
POLL_INTERVAL=15        # API 확인 간격 (15초)
SPINNER_INTERVAL=0.5    # 스피너 애니메이션 간격 (0.5초)

while true; do
  RUN_RESPONSE=$(curl -s \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/${OWNER}/${REPO}/actions/runs/${RUN_ID}")

  STATUS=$(echo "$RUN_RESPONSE" | jq -r '.status')
  CONCLUSION=$(echo "$RUN_RESPONSE" | jq -r '.conclusion')

  TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

  if [ "$STATUS" = "completed" ]; then
    # 스피너 라인 지우기
    echo -e "\r\033[K"
    echo "=========================================="
    if [ "$CONCLUSION" = "success" ]; then
      echo "✅ 리소스 정리가 성공적으로 완료되었습니다!"
      echo "완료 시간: ${TIMESTAMP}"
      echo "=========================================="
      exit 0
    else
      echo "❌ 리소스 정리가 실패했습니다."
      echo "Conclusion: ${CONCLUSION}"
      echo "완료 시간: ${TIMESTAMP}"
      echo ""
      echo "자세한 내용은 다음 URL에서 확인하세요:"
      echo "${RUN_URL}"
      echo "=========================================="
      exit 1
    fi
  fi

  # 스피너 애니메이션 (15초 동안 0.5초마다 업데이트)
  SPINNER_STEPS=$(awk "BEGIN {print int($POLL_INTERVAL / $SPINNER_INTERVAL)}")
  for ((i=0; i<SPINNER_STEPS; i++)); do
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    printf "\r%s 리소스 정리 중... [%s]" "${SPINNER[$SPINNER_IDX]}" "${TIMESTAMP}"
    SPINNER_IDX=$(( (SPINNER_IDX + 1) % ${#SPINNER[@]} ))
    sleep $SPINNER_INTERVAL
  done
done
