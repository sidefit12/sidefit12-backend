## ✨ 백엔드 주요 기능 (Key Backend Features)

- **✅ 인증 및 사용자 관리**
  > 이메일 기반 회원가입·로그인 및 이메일 인증  
  > JWT Access Token·Refresh Token 기반 인증/인가  
  > 회원정보 조회·수정, 비밀번호 재설정, 로그아웃 및 회원 탈퇴

- **✅ 프로필 및 온보딩**
  > 관심 토픽, 보유·학습 기술 스택, 희망 역할 등록  
  > 참여 가능한 기간, 진행 방식 등 프로젝트 참여 조건 설정  
  > 자기소개와 포트폴리오 등록 및 프로필 완성도 관리

- **✅ 프로젝트 모집 관리**
  > 프로젝트 모집 글 작성·조회·수정·삭제  
  > 토픽, 기술 스택, 모집 역할, 역할별 인원과 모집 마감일 관리  
  > 모집 중·모집 완료 등 프로젝트 상태와 지원자 목록 관리

- **✅ 프로젝트 탐색 및 검색**
  > 키워드 기반 프로젝트 검색  
  > 토픽·기술 스택·역할·진행 방식·모집 상태를 조합한 필터링  
  > 페이지네이션을 적용한 프로젝트 목록 및 상세 조회

- **✅ 지원 및 팀 구성 관리**
  > 프로젝트 지원·취소 및 내 지원 내역 조회  
  > 모집자의 지원 승인·거절과 지원 상태 관리  
  > 중복 지원과 마감된 프로젝트에 대한 지원 방지  
  > 지원 승인 후 팀원 확정 및 프로젝트 진행 상태 관리

- **✅ 맞춤형 프로젝트 추천**
  > 관심 토픽, 기술 스택, 희망 역할의 일치도를 활용한 규칙 기반 추천  
  > 프로젝트 설명과 사용자 관심 정보의 의미적 유사도 분석  
  > 추천 점수와 함께 일치한 토픽·기술·역할 등 추천 이유 제공  
  > 프로필 정보가 부족한 신규 사용자를 위한 콜드 스타트 대응

- **✅ 관심 목록 및 활동 기록**
  > 관심 프로젝트 저장·해제 및 목록 조회  
  > 작성한 모집 글, 지원한 프로젝트와 받은 지원 현황 조회  
  > 완료한 프로젝트와 리뷰·후기 등 활동 이력 관리

- **✅ 알림·신고 및 운영 관리**
  > 지원 승인·거절, 모집 마감과 신규 메시지에 대한 알림  
  > 프로젝트 및 사용자 신고와 신고 처리 이력 관리  
  > 관리자 권한을 통한 신고 처리, 제재와 기준 데이터 관리

- **🔜 확장 기능**
  > 프로젝트 채팅·게시판과 일정 관리  
  > 프로젝트 파일 및 이미지 업로드  
  > FCM 기반 푸시 알림과 WebSocket 기반 실시간 통신  
  > OpenAI API를 활용한 모집 글 개선 및 추천 이유 보조 생성

---

## ⚙️ 기술 스택 (Tech Stack)

<div align="center">

### Backend
<p>
  <img src="https://img.shields.io/badge/Python_3-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img src="https://img.shields.io/badge/Uvicorn-499848?style=for-the-badge">
  <img src="https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white">
</p>

### Database & Persistence
<p>
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white">
  <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white">
  <img src="https://img.shields.io/badge/Alembic-6BA81E?style=for-the-badge">
  <img src="https://img.shields.io/badge/pgvector-336791?style=for-the-badge">
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white">
</p>

### Authentication & Recommendation
<p>
  <img src="https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white">
  <img src="https://img.shields.io/badge/Sentence_Transformers-FFD21E?style=for-the-badge">
  <img src="https://img.shields.io/badge/OpenAI_API-412991?style=for-the-badge&logo=openai&logoColor=white">
</p>

### Test & Infrastructure
<p>
  <img src="https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white">
  <img src="https://img.shields.io/badge/Ruff-D7FF64?style=for-the-badge&logo=ruff&logoColor=black">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white">
  <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white">
  <img src="https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white">
</p>

</div>

> `pgvector`, `Redis`, Sentence Transformers, OpenAI API 등은 해당 기능의 구현 단계에 맞춰 순차적으로 도입합니다.

---

## 🤖 백엔드 아키텍처 (Backend System Architecture)

SideFit 백엔드는 초기 운영 복잡도를 줄이기 위해 **모듈형 모놀리스** 구조로 구성합니다.  
각 도메인은 `router-service-repository` 계층으로 책임을 분리하고, 공통 설정과 인증 의존성은 `core` 영역에서 관리합니다.

```mermaid
flowchart TD
    Client[Vue Web / PWA Client] -->|HTTPS REST API| API[FastAPI Application]

    API --> Middleware[Middleware<br/>CORS · Logging · Request ID]
    Middleware --> Auth[JWT Authentication & Authorization]
    Auth --> Router[Domain Routers]
    Router --> Service[Business Services]
    Service --> Repository[Repositories]

    Repository --> PostgreSQL[(PostgreSQL)]
    Service --> Redis[(Redis<br/>Cache · Rate Limit · Notification)]
    Service --> Recommendation[Recommendation Module]
    Recommendation --> Vector[(pgvector)]
    Recommendation --> Embedding[Sentence Transformers]

    Service --> Email[Email Service]
    Service --> Storage[File Storage]
    Service --> FCM[Firebase Cloud Messaging]
    Service --> OpenAI[OpenAI API]

    API -->|JSON Response| Client
```

### 목표 패키지 구성

```text
📦 app
┣ 📜 main.py                    # FastAPI 애플리케이션 진입점
┣ 📂 core
┃ ┣ 📜 config.py               # 환경 변수 및 애플리케이션 설정
┃ ┣ 📜 database.py             # DB 엔진과 세션 관리
┃ ┣ 📜 security.py             # JWT, 비밀번호 해시, 인증 의존성
┃ ┣ 📜 exceptions.py           # 공통 예외와 오류 응답
┃ ┗ 📜 logging.py              # 구조화 로그 및 요청 식별자
┣ 📂 common
┃ ┣ 📜 responses.py            # 공통 응답 모델
┃ ┣ 📜 pagination.py           # 페이지네이션
┃ ┗ 📜 enums.py                # 공통 상태값
┣ 📂 domains
┃ ┣ 📂 auth                    # 회원가입·로그인, 이메일 인증, JWT·Refresh Token
┃ ┣ 📂 users                   # 계정 조회·수정, 회원 상태 관리와 탈퇴
┃ ┣ 📂 profiles                # 프로필·온보딩, 관심 토픽·기술 스택·희망 역할
┃ ┣ 📂 files                   # 프로필 이미지·공개 자료 파일 메타데이터와 열람 정책
┃ ┣ 📂 projects                # 모집 글·포지션·협업 채널, 프로젝트 상태와 소프트 삭제
┃ ┣ 📂 applications            # 프로젝트 지원·취소와 모집자의 승인·거절
┃ ┣ 📂 members                 # 확정 팀원과 합류·탈퇴·퇴출·복구 이력
┃ ┣ 📂 bookmarks               # 관심 프로젝트 저장·해제와 목록 조회
┃ ┣ 📂 reviews                 # 완료 프로젝트 리뷰·후기 관리
┃ ┣ 📂 recommendations         # 규칙·임베딩 기반 추천 결과와 추천 이유
┃ ┣ 📂 notifications           # 서비스 알림과 사용자별 알림 수신 설정
┃ ┣ 📂 reports                 # 사용자·프로젝트 신고와 관리자 처리
┃ ┗ 📂 reference_data          # 토픽, 기술 스택, 역할 기준 데이터
┣ 📂 integrations
┃ ┣ 📜 email.py                # 이메일 발송
┃ ┣ 📜 storage.py              # S3·Cloudinary 파일 저장 및 조회 연동
┃ ┣ 📜 firebase.py             # FCM 푸시 알림
┃ ┗ 📜 openai.py               # OpenAI API 연동
┗ 📂 tests
  ┣ 📂 unit                    # 서비스 및 추천 로직 단위 테스트
  ┗ 📂 integration             # API와 DB 통합 테스트
```

각 도메인은 필요에 따라 다음 파일을 포함합니다.

```text
router.py       # HTTP 요청·응답과 엔드포인트
service.py      # 비즈니스 규칙과 트랜잭션 흐름
repository.py   # 데이터 접근 로직
models.py       # SQLAlchemy ORM 모델
schemas.py      # Pydantic 요청·응답 스키마
dependencies.py # 도메인별 인증·권한 의존성
```

---

## 🔐 인증 구조 (Authentication)

SideFit 백엔드는 이메일 인증과 JWT 기반 인증 구조를 사용합니다.

```text
1. 사용자가 이메일, 비밀번호와 기본정보를 입력하여 회원가입을 요청합니다.
2. 서버는 중복 이메일을 확인하고 비밀번호를 단방향 해시로 저장합니다.
3. 이메일 인증을 완료한 사용자가 로그인을 요청합니다.
4. 인증에 성공하면 Access Token과 Refresh Token을 발급합니다.
5. 클라이언트는 보호된 API 요청의 Authorization Header에 Access Token을 포함합니다.
6. 서버는 JWT와 사용자 상태를 검증한 뒤 요청을 처리합니다.
7. 프로젝트 수정, 지원자 승인 등은 소유권과 역할을 추가로 검증합니다.
```

### 보안 원칙

- 비밀번호, 토큰과 같은 민감정보를 로그 및 API 응답에 포함하지 않습니다.
- 모집 글 수정·삭제와 지원 승인·거절은 객체 단위 소유권을 검증합니다.
- 입력 길이, 데이터 형식, 페이지 크기와 상태 전이 규칙을 검증합니다.
- 탈퇴 시 개인정보 삭제 또는 익명화 정책을 적용합니다.

---

## 🗄️ 데이터 처리 방식 (Database & Persistence)

| 구분 | 기술 | 역할 |
| --- | --- | --- |
| Main Database | PostgreSQL | 사용자, 프로필, 토픽, 기술 스택, 역할, 프로젝트, 지원과 관심 목록 저장 |
| ORM | SQLAlchemy 2 | 엔티티 매핑, 트랜잭션과 데이터 접근 |
| Migration | Alembic | DB 스키마 변경 이력과 배포 환경 마이그레이션 관리 |
| Vector Search | pgvector | 프로젝트 설명 임베딩 저장과 의미적 유사도 검색 |
| Cache | Redis | 조회 캐시, 요청 제한, 알림 처리 등에 선택적으로 활용 |
| File Storage | S3 또는 Cloudinary | 프로필 이미지와 프로젝트 첨부파일 저장 |
| Validation | Pydantic 2 | 외부 요청·응답 모델 검증과 내부 모델 분리 |

### 주요 데이터 규칙

- 사용자·프로젝트와 토픽·기술 스택·역할은 연결 테이블로 관계를 관리합니다.
- 동일 사용자가 하나의 프로젝트에 중복 지원하지 못하도록 유일성 제약조건을 적용합니다.
- 지원 상태는 `PENDING`, `ACCEPTED`, `REJECTED`, `CANCELED`로 관리합니다.
- 마감되거나 모집이 완료된 프로젝트에는 새로운 지원을 허용하지 않습니다.
- 목록 API에는 페이지네이션을 기본 적용하고 자주 조회되는 검색 조건에 인덱스를 적용합니다.

---

## 🧠 맞춤형 추천 구조 (Recommendation)

SideFit의 추천 기능은 사용자의 결정을 대신하지 않고,  
조건과 적합도가 높은 프로젝트를 먼저 탐색할 수 있도록 후보를 좁혀 주는 기능입니다.

```mermaid
flowchart TD
    UserProfile[사용자 프로필<br/>관심 토픽 · 기술 스택 · 희망 역할]
    RecruitingProjects[모집 중인 프로젝트]

    UserProfile --> CandidateFilter[후보 프로젝트 필터링]
    RecruitingProjects --> CandidateFilter

    CandidateFilter --> RuleScore[구조화 조건 점수<br/>역할 · 토픽 · 기술 · 진행 방식]
    CandidateFilter --> SemanticScore[의미 유사도 점수<br/>문장 임베딩 · 코사인 유사도]

    RuleScore --> Normalize[점수 정규화]
    SemanticScore --> Normalize

    Normalize --> HybridScore[하이브리드 추천 점수]
    HybridScore --> Reason[추천 이유 생성]
    Reason --> Result[추천 프로젝트 및 근거 반환]
```

### 추천 처리 원칙

1. 모집 중인 프로젝트만 추천 후보로 조회합니다.
2. 사용자가 작성했거나 이미 지원한 프로젝트는 후보에서 제외합니다.
3. 희망 역할, 관심 토픽, 기술 스택과 진행 방식의 일치도를 계산합니다.
4. 프로젝트 설명과 사용자 관심 정보의 임베딩 유사도를 계산합니다.
5. 구조화 점수와 의미 유사도 점수를 정규화하여 결합합니다.
6. 일치한 토픽·기술·역할을 추천 결과의 근거로 함께 제공합니다.
7. 프로필 정보가 부족하면 최신·마감 임박·인기 프로젝트를 혼합해 제공합니다.

---

## 🚀 배포 구조 (Deployment)

SideFit은 Docker 기반 실행 환경과 GitHub Actions를 활용한 CI/CD 구성을 목표로 합니다.

```mermaid
flowchart TD
    PR[Pull Request] --> CI[GitHub Actions CI]
    CI --> Ruff[Ruff Lint & Format Check]
    CI --> Test[pytest Unit & Integration Test]
    CI --> Build[Docker Image Build Check]

    Merge[main 브랜치 병합] --> CD[GitHub Actions CD]
    CD --> Image[Container Image Build]
    Image --> Registry[Container Registry]
    Registry --> Server[Application Server]
    Server --> Nginx[Nginx Reverse Proxy]
    Nginx --> FastAPI[FastAPI Container]
    FastAPI --> PostgreSQL[(Managed PostgreSQL)]
    FastAPI --> Redis[(Redis)]
```

---

## 💻 로컬 실행 방법 (Getting Started)

### 1. 저장소 복제

```bash
git clone https://github.com/sidefit12/sidefit12-backend.git
cd sidefit12-backend
```

### 2. 가상환경 생성 및 활성화

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

PowerShell에서 스크립트 실행이 차단되는 경우 현재 터미널에서만 실행 정책을 변경합니다.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 의존성 설치

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

설치된 패키지의 의존성 충돌 여부를 확인합니다.

```bash
python -m pip check
```

### 4. PostgreSQL 실행

로컬 데이터베이스는 프로젝트 루트의 `compose.yml`을 사용하여  
**PostgreSQL 17과 pgvector가 포함된 컨테이너**로 실행합니다.

먼저 Docker Desktop을 실행하고 Docker 엔진이 정상적으로 동작하는지 확인합니다.

```bash
docker info
```

컨테이너를 백그라운드에서 실행합니다.

```bash
docker compose up -d
```

실행 상태를 확인합니다.

```bash
docker compose ps
```

정상적으로 실행되면 `sidefit-postgres` 컨테이너가 `Up` 또는 `healthy` 상태로 표시됩니다.

> Windows에서 `dockerDesktopLinuxEngine` 또는  
> `The system cannot find the file specified` 오류가 발생하면 Docker Desktop이 실행되지 않은 상태입니다.  
> Docker Desktop을 실행한 뒤 엔진 구동이 완료되면 명령어를 다시 실행합니다.

### 5. pgvector 확장 활성화

PostgreSQL 컨테이너가 처음 생성된 경우 `sidefit` 데이터베이스에서  
`vector` 확장을 한 번 활성화합니다.

```bash
docker exec -it sidefit-postgres psql -U sidefit -d sidefit -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

활성화 여부를 확인합니다.

```bash
docker exec -it sidefit-postgres psql -U sidefit -d sidefit -c "\dx"
```

출력 목록에 `vector`가 표시되면 정상적으로 적용된 상태입니다.

### 6. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 만들고 데이터베이스 연결 정보를 설정합니다.

```env
DATABASE_URL=postgresql+psycopg://sidefit:sidefit1234@localhost:5432/sidefit
```

| 구분 | 값 |
| --- | --- |
| Host | `localhost` |
| Port | `5432` |
| Database | `sidefit` |
| Username | `sidefit` |
| Password | `sidefit1234` |

> `.env`에는 비밀번호와 토큰 등 민감정보가 포함될 수 있으므로 Git에 커밋하지 않습니다.

### 7. 데이터베이스 테이블 생성

SQLAlchemy의 `models.py`는 테이블 구조를 정의할 뿐이며,  
개발 서버를 실행하는 것만으로 PostgreSQL에 테이블이 자동 생성되지는 않습니다.

현재 개발 초기 단계에서는 다음 명령어로 `Base.metadata`에 등록된 테이블을 생성합니다.

Windows PowerShell:

```powershell
python -c "from app.core.database import Base, engine; import app.domains.users.models; Base.metadata.create_all(bind=engine); print('테이블 생성 완료')"
```

macOS/Linux:

```bash
python -c "from app.core.database import Base, engine; import app.domains.users.models; Base.metadata.create_all(bind=engine); print('테이블 생성 완료')"
```

> `import app.domains.users.models`가 있어야 `User` 모델이 SQLAlchemy의 `Base.metadata`에 등록됩니다.  
> 새로운 도메인의 모델을 추가한 경우 해당 `models.py`도 함께 import해야 합니다.

생성된 테이블 목록을 확인합니다.

```bash
docker exec -it sidefit-postgres psql -U sidefit -d sidefit -c "\dt"
```

`users` 테이블의 컬럼과 제약조건을 확인합니다.

```bash
docker exec -it sidefit-postgres psql -U sidefit -d sidefit -c "\d+ users"
```

> `Base.metadata.create_all()`은 존재하지 않는 테이블만 생성하며, 이미 생성된 테이블의 컬럼이나 제약조건을 변경하지 않습니다.  
> 실제 스키마 변경 이력은 이후 Alembic 마이그레이션으로 관리합니다.

### 8. 개발 서버 실행

```bash
fastapi dev app/main.py
```

또는 Uvicorn을 직접 실행할 수 있습니다.

```bash
uvicorn app.main:app --reload
```

### 9. API 문서 확인

| 구분 | 주소 |
| --- | --- |
| API 서버 | `http://127.0.0.1:8000` |
| Swagger UI | `http://127.0.0.1:8000/docs` |
| ReDoc | `http://127.0.0.1:8000/redoc` |
| Health Check | `http://127.0.0.1:8000/health` |

### 10. PostgreSQL 종료 및 재실행

컨테이너를 종료합니다.

```bash
docker compose down
```

데이터를 유지한 상태로 다시 실행합니다.

```bash
docker compose up -d
```

PostgreSQL 데이터 볼륨까지 모두 삭제하려면 다음 명령어를 사용합니다.

```bash
docker compose down -v
```

> `-v` 옵션을 사용하면 로컬 PostgreSQL 데이터가 모두 삭제되므로 주의합니다.

---

## 🧪 테스트 및 품질 관리 (Test & Quality)

- 서비스 계층의 비즈니스 규칙과 권한 검증을 단위 테스트로 확인합니다.
- 회원가입 → 프로젝트 작성 → 지원 → 승인 → 추천 조회의 핵심 흐름을 통합 테스트로 검증합니다.
- 중복 이메일, 중복 지원, 마감된 프로젝트 지원과 소유권 위반을 예외 시나리오로 관리합니다.
- GitHub Actions에서 Ruff 검사, pytest와 Docker 이미지 빌드를 자동으로 수행합니다.
- API 오류는 공통 응답 형식으로 반환하고 주요 처리 결과를 구조화된 로그로 기록합니다.

---

## 🤝 Conventions

SideFit은 일관된 형상 관리와 작업 이력 관리를 위해 아래 규칙을 사용합니다.

- **[Commit & Branch Convention](./.github/COMMIT_CONVENTION.md)**
- 모든 작업은 GitHub Issue로 정의합니다.
- 작업 브랜치에서 구현한 뒤 Pull Request를 통해 `main` 브랜치에 병합합니다.
- Pull Request에는 구현 내용, 테스트 결과, API·DB 변경 여부를 기록합니다.

---

## 📚 참고자료 (References)

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 공식 문서](https://docs.sqlalchemy.org/en/20/)
- [Pydantic 공식 문서](https://docs.pydantic.dev/)
- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
- [pgvector](https://github.com/pgvector/pgvector)
- [Sentence Transformers 공식 문서](https://www.sbert.net/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [GitHub Actions 공식 문서](https://docs.github.com/actions)

---

## 💁‍♂️ 개발자 소개 (Developer)

<table align="center">
  <tr>
    <td align="center">
      <a href="https://github.com/WhiteBin-bin">
        <img src="https://github.com/WhiteBin-bin.png"
             alt="백현빈 프로필"
             width="150"
             height="150"><br>
        <b>백현빈</b>
      </a>
      <br>
      Backend · AI Recommendation · Infrastructure
    </td>
  </tr>
</table>
