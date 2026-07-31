# Commit & Branch Convention

SideFit은 변경 이력을 명확하게 관리하기 위해 아래 커밋 및 브랜치 규칙을 사용합니다.

---

## 📌 Commit Message Format

커밋 메시지는 다음 형식으로 작성합니다.

```text
<Emoji> <Type>: <Subject>

<Body> (Optional)

<Footer> (Optional)
```

### Type

커밋의 성격에 따라 아래 타입 중 하나를 사용합니다.  
터미널에서 이모지가 깨지는 경우 실제 이모지 대신 Emoji Code를 사용할 수 있습니다.

| Type | Emoji | Emoji Code | 사용 범위 |
| --- | --- | --- | --- |
| `Feat` | ✨ | `:sparkles:` | 새로운 기능 추가 또는 기존 기능 개선 |
| `Bug` | 🐛 | `:bug:` | 버그, 오류, 데이터 불일치 수정 |
| `Docs` | 📚 | `:books:` | README, API 문서 등 문서 변경 |
| `Style` | 🎨 | `:art:` | 포맷팅 등 동작에 영향을 주지 않는 변경 |
| `Refactor` | 🔨 | `:hammer:` | 기능 변경 없는 코드·아키텍처 개선 |
| `Test` | 🧪 | `:test_tube:` | 단위·통합 테스트 추가 및 수정 |
| `Chore` | ⚙️ | `:gear:` | 의존성, 설정, 개발 환경 관련 작업 |
| `Devops` | 🐳 | `:whale:` | Docker, 배포, CI/CD 자동화 |
| `Security` | 🔒 | `:lock:` | 인증, 인가와 보안 관련 작업 |

---

## ✍️ Subject

- 제목은 **50자 이내**로 작성합니다.
- 무엇을 변경했는지 명확하게 요약합니다.
- 제목 끝에 마침표를 작성하지 않습니다.
- `구현`, `추가`, `수정`, `분리`처럼 작업 내용을 명확히 드러내는 표현을 사용합니다.

```text
✨ Feat: 프로젝트 모집 글 작성 기능 구현
🐞 Fix: 마감된 프로젝트에 지원되는 오류 수정
🔨 Refactor: 인증 토큰 검증 로직을 의존성으로 분리
```

---

## 📝 Body (Optional)

제목만으로 변경 내용을 설명하기 부족할 때 작성합니다.

- **어떻게** 변경했는지 작성합니다.
- **왜** 변경했는지 작성합니다.
- 주요 비즈니스 규칙이나 설계 결정이 있다면 함께 기록합니다.
- 한 줄은 가급적 72자 이내로 작성합니다.

```text
✨ Feat: 프로젝트 지원 기능 구현

- 프로젝트 모집 상태와 마감일을 검증하도록 처리
- 동일 사용자의 중복 지원을 차단하는 유일성 제약조건 추가
- 지원 생성과 지원자 수 갱신을 하나의 트랜잭션으로 처리
```

---

## 🔗 Footer (Optional)

관련 이슈를 연결하거나 자동으로 종료할 때 사용합니다.

| 키워드 | 사용 기준 | 예시 |
| --- | --- | --- |
| `Closes` | 기능 구현 등 일반 작업을 완료한 경우 | `Closes #10` |
| `Fixes` | 버그를 수정하여 이슈를 해결한 경우 | `Fixes #25` |
| `Resolves` | 논의·설계 이슈를 해결한 경우 | `Resolves #40` |

이슈를 종료하지 않고 참조만 할 경우 키워드 없이 이슈 번호를 작성합니다.

```text
관련 이슈: #75
```

---

## ✅ Commit Message Examples

### 기능 구현

```text
✨ Feat: 사용자 관심 토픽 등록 기능 구현

- 사용자와 토픽 사이의 다대다 관계를 연결 테이블로 구성
- 중복 토픽 등록을 차단하도록 유일성 제약조건 적용

Closes #12
```

### 버그 수정

```text
🐛 Bug: 모집 마감 후 지원 가능한 오류 수정

- 프로젝트 상태와 모집 마감일을 함께 검증하도록 수정
- 마감된 프로젝트 지원 예외 테스트 추가

Fixes #27
```

### 리팩터링

```text
🔨 Refactor: 추천 점수 계산 로직을 전략 객체로 분리

- 규칙 기반 점수와 임베딩 점수 계산 책임 분리
- 추천 가중치를 설정으로 주입할 수 있도록 구조 개선

Resolves #41
```

### 문서 수정

```text
📚 Docs: 백엔드 실행 방법과 아키텍처 문서 추가

- 로컬 가상환경 설정 방법 추가
- 목표 패키지 구조와 추천 처리 흐름 문서화
```

### 개발 환경 설정

```text
⚙️ Chore: FastAPI 개발 환경 초기 설정

- FastAPI와 Uvicorn 의존성 추가
- 환경 변수 파일과 가상환경을 Git 추적에서 제외
```

---

## 🌿 Branch Strategy

SideFit은 `main` 브랜치를 항상 실행 가능한 안정 상태로 유지하는  
**GitHub Flow** 방식으로 작업합니다.

1. 모든 작업은 GitHub Issue로 정의합니다.
2. 최신 `main` 브랜치에서 작업 브랜치를 생성합니다.
3. 작업 완료 후 Pull Request를 생성합니다.
4. 테스트와 리뷰가 완료되면 `main`에 병합합니다.
5. 병합된 작업 브랜치는 삭제합니다.

```bash
git switch main
git pull origin main
git switch -c feature/12-project-create
```

---

## 🏷️ Branch Naming Convention

```text
{label}/{issue-number}-{summary}
```

> 브랜치 이름에는 `#` 문자를 포함하지 않습니다.  
> `summary`는 영문 소문자와 하이픈을 사용해 간결하게 작성합니다.

| Label | 브랜치 예시 | 설명 |
| --- | --- | --- |
| `feature` | `feature/12-project-create` | 새로운 기능 개발 |
| `bug` | `bug/25-application-deadline` | 버그 수정 |
| `refactor` | `refactor/30-auth-dependency` | 코드·아키텍처 리팩터링 |
| `docs` | `docs/7-readme` | 문서 추가 및 수정 |
| `test` | `test/18-project-service` | 테스트 코드 추가 및 수정 |
| `chore` | `chore/3-project-config` | 설정, 의존성, 개발 환경 작업 |
| `devops` | `devops/40-backend-ci` | 배포와 CI/CD 작업 |
| `security` | `security/45-token-validation` | 인증·인가와 보안 작업 |

---

## 🔀 Pull Request Convention

### PR 제목

커밋 제목과 동일한 형식을 사용하며 이슈 이름과 동일하게 작성합니다.

```text
✨ Feat: 프로젝트 모집 글 작성 기능 구현
```

### PR 본문 필수 항목

```markdown
## 작업 내용
- 구현하거나 수정한 내용을 작성합니다.

## 상세 내용
- 주요 처리 흐름과 설계 결정을 작성합니다.

## 테스트
- [ ] 단위 테스트
- [ ] 통합 테스트
- [ ] 로컬 API 확인

## 변경 사항
- [ ] API 명세 변경
- [ ] DB 스키마 변경
- [ ] 환경 변수 변경
- [ ] 의존성 변경

## 관련 이슈

- Closes: `#이슈번호`
- Fixes: `#이슈번호`
- Resolves: `#이슈번호`
- Progress: `#이슈번호`
```
