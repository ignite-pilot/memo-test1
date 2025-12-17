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
  echo "  GITHUB_TOKEN=<전달받은 Github Personal Token> ./deploy-alpha.sh"
  exit 1
fi

# Repository 정보
OWNER="ignite-pilot"
REPO="memo-test1"
WORKFLOW_FILE="deploy-alpha.yml"

# Custom 인자 처리
BRANCH="${1:-main}"
HEALTH_CHECK_PATH="${2:-/api/health}"

echo "Alpha 배포를 시작합니다."
echo "Repository       : ${OWNER}/${REPO}"
echo "Branch           : ${BRANCH}"
echo "Health Check Path: ${HEALTH_CHECK_PATH}"
echo ""

# Step 1: 로컬에서 Docker 이미지 빌드 및 검증
echo "=================================="
echo "Step 1: Docker 이미지 빌드"
echo "=================================="
echo ""

if [ -f "./build-alpha.sh" ]; then
  ./build-alpha.sh "${REPO}"
else
  echo "❌ 오류: build-alpha.sh 파일을 찾을 수 없습니다"
  exit 1
fi

echo ""
echo "=================================="
echo "Step 2: GitHub Workflow 실행"
echo "=================================="
echo ""

# GitHub API를 통해 workflow dispatch
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW_FILE}/dispatches" \
  -d "{\"ref\":\"${BRANCH}\", \"inputs\":{\"health_check_path\":\"${HEALTH_CHECK_PATH}\"}}")

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

echo "✅ Workflow를 시작했습니다."
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
      echo "✅ Workflow가 성공적으로 완료되었습니다!"
      echo "완료 시간: ${TIMESTAMP}"
      echo "=========================================="
      exit 0
    else
      echo "❌ Workflow가 실패했습니다."
      echo "Conclusion: ${CONCLUSION}"
      echo "완료 시간: ${TIMESTAMP}"
      echo ""

      # 실패한 jobs 정보 가져오기
      echo "실패 원인을 분석하고 있습니다..."
      JOBS_RESPONSE=$(curl -s \
        -H "Accept: application/vnd.github+json" \
        -H "Authorization: Bearer ${GITHUB_TOKEN}" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        "https://api.github.com/repos/${OWNER}/${REPO}/actions/runs/${RUN_ID}/jobs")

      # 실패한 jobs 찾기
      FAILED_JOBS=$(echo "$JOBS_RESPONSE" | jq -r '.jobs[] | select(.conclusion == "failure" or .conclusion == "cancelled") | "\(.name)|\(.id)"')

      if [ -n "$FAILED_JOBS" ]; then
        echo ""
        echo "=== 실패한 Jobs ==="
        echo ""

        while IFS='|' read -r job_name job_id; do
          echo "▶ Job: ${job_name}"

          # 실패한 steps 찾기
          FAILED_STEPS=$(echo "$JOBS_RESPONSE" | jq -r --arg job_id "$job_id" \
            '.jobs[] | select(.id == ($job_id | tonumber)) | .steps[] | select(.conclusion == "failure" or .conclusion == "cancelled") | "  ✗ \(.name) (\(.conclusion))"')

          if [ -n "$FAILED_STEPS" ]; then
            echo ""
            echo "  실패한 Steps:"
            echo "$FAILED_STEPS"
            echo ""
          fi

          # 로그 가져오기
          echo "  로그 (마지막 100줄):"
          echo "  ----------------------------------------"

          LOG_RESPONSE=$(curl -s -w "\n%{http_code}" \
            -L \
            -H "Authorization: Bearer ${GITHUB_TOKEN}" \
            "https://api.github.com/repos/${OWNER}/${REPO}/actions/jobs/${job_id}/logs" 2>/dev/null)

          LOG_HTTP_CODE=$(echo "$LOG_RESPONSE" | tail -n1)
          LOG_BODY=$(echo "$LOG_RESPONSE" | sed '$d')

          if [ "$LOG_HTTP_CODE" -eq 200 ]; then
            if [ -n "$LOG_BODY" ]; then
              echo "$LOG_BODY" | tail -n 100 | sed 's/^/  /'
            else
              echo "  (로그가 비어있습니다)"
            fi
          else
            echo "  (로그를 가져올 수 없습니다 - HTTP ${LOG_HTTP_CODE})"
            if [ "$LOG_HTTP_CODE" -eq 403 ]; then
              echo "  권한 오류: GITHUB_TOKEN에 'actions:read' 권한이 필요합니다."
            elif [ "$LOG_HTTP_CODE" -eq 404 ]; then
              echo "  로그를 찾을 수 없습니다. 로그가 아직 생성되지 않았거나 만료되었을 수 있습니다."
            fi
          fi

          echo "  ----------------------------------------"
          echo ""
        done <<< "$FAILED_JOBS"
      fi

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
    printf "\r%s Workflow 실행 중... [%s]" "${SPINNER[$SPINNER_IDX]}" "${TIMESTAMP}"
    SPINNER_IDX=$(( (SPINNER_IDX + 1) % ${#SPINNER[@]} ))
    sleep $SPINNER_INTERVAL
  done
done
