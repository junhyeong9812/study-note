# issue3 — 콘텐츠 API: 문서 목록과 원문만 준다 (그리는 건 front)

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-backend
- 이슈 #5 · PR: https://github.com/junhyeong9812/study-note-deploy-system-backend/pull/6

## 1. 배경 (요구사항)

위키 화면이 필요로 하는 건 두 가지 — "무슨 문서가 있나"(네비게이션)와 "이 문서 내용"(본문).
설계 결정(front가 Next.js SSR로 렌더)에 따라 backend는 **HTML을 만들지 않고** md 원문과
메타(주제·문서종류)만 JSON으로 준다. 파일을 서버 간에 옮기는 문제가 통째로 사라진다.

## 2. 검토한 방식들

### 선택 — 평면 목록 + 원문 API 2개

- `GET /api/docs` — 전 문서의 메타 목록(경로·주제·종류). front가 이걸로 트리를 만든다.
  트리를 backend가 만들면 화면 구조가 바뀔 때마다 backend를 고쳐야 해서 평면으로 준다.
- `GET /api/doc?path=` — md 원문 + 메타.

### 대안 — backend가 트리 JSON까지 (탈락) / HTML 생성 (탈락)

- 둘 다 "화면 관심사"가 backend로 넘어온다. 화면 관심사는 front 한 곳에.

## 3. 구현 워크플로우

```
GET /api/doc?path=cs/lsm-tree/2-summary.md
  ▼
[경로 검사] .md 인가? 절대경로/..(상위 이동)/.git 이 없나?  → 아니면 422 invalid_request
  ▼
git 볼륨에서 파일 읽기 → 없으면 404 not_found (I/O 장애는 500 봉투 — 리뷰 후 구분)
  ▼
{"success":true,"data":{"path","topic","subject","doc_kind","form","markdown":"# ..."}}
```

경로 검사가 핵심 보안 장치다 — `path=../../etc/passwd.md` 같은 **경로 트래버설**(폴더
밖으로 기어 올라가기)을 막는다. LAN 전용이라도 backend는 이후 front를 통해 외부 요청을
받게 되므로 처음부터 닫는다.

## 4. 코드 변경 (핵심)

```kotlin
internal fun isSafe(path: String): Boolean =
    path.endsWith(".md") && !path.startsWith("/") && !path.startsWith("~") &&
    !path.split("/").any { it == ".." || it == ".git" } && path.isNotBlank()
```

## 5. 구현 중 마주친 문제

### 문제 — 한글 경로 문서의 본문이 빈 문자열
- **원인 조사**: 클론 볼륨의 파일이 0바이트 → 로컬 원본도 0바이트 → git 이력으로
  rename 이전(problem.md 시절)까지 확인 → **원래부터 빈 파일**. programmers 94개는
  아직 안 쓴 플레이스홀더였다.
- **수정**: 없음(결함 아님). 색인 쪽은 빈 파일을 청크 0개로 건너뛰어 이미 정상.
- **배경**: "버그처럼 보이는 것"의 절반은 데이터 실태다. 원본→이력 순으로 거슬러 확인해야
  엉뚱한 코드를 고치지 않는다.

## 6. 결론

616건 목록·한글 경로 조회·트래버설 422·실문서 6037자 서빙 확인. PR: #6
