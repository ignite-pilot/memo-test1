# 프로젝트 설정 가이드

## 초기 설정

### 1. 데이터베이스 초기화

```bash
cd backend
python init_db.py
```

또는 백엔드 서버를 실행하면 자동으로 초기화됩니다.

### 2. Backend 설정

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend 설정

```bash
cd frontend
npm install
```

## 실행

### Backend 실행
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8501
```

### Frontend 실행
```bash
cd frontend
npm run dev
```

## 테스트 실행

### Backend 테스트
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

### Frontend 테스트
```bash
cd frontend
npm test
```

## 코드 품질 체크

### Backend
```bash
cd backend
source venv/bin/activate
./run_checks.sh
```

또는 Makefile 사용:
```bash
cd backend
make lint      # 린팅
make format    # 포맷팅
make security  # 보안 스캔
make test      # 테스트
```

## Docker 실행

```bash
docker-compose up --build
```

## 환경 변수

프로젝트는 `config/config.local.env` 파일을 사용합니다.
필요시 다른 환경의 설정 파일을 사용할 수 있습니다.

