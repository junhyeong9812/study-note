# issue2 — sync 파이프라인: push 한 번이 색인으로 바뀌기까지

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-backend
- 이슈 #3 · PR: https://github.com/junhyeong9812/study-note-deploy-system-backend/pull/4

## 1. 배경 (요구사항)

study-note에 push하면 "바뀐 문서만" 검색엔진에 반영돼야 한다. 요구는 세 겹:

1. **무엇이 바뀌었나**를 정확히 안다 — 전체를 매번 다시 훑지 않는다.
2. **같은 push가 두 번 와도 한 번만** 처리한다(멱등 — 배포 재시도·중복 호출 대비).
   사용자 결정: 요청에 `commit_sha`를 실어 보내고 이걸로 중복을 가른다.
3. **"에러 없이 돌았다"를 "다 됐다"로 착각하지 않는다** — 넣은 만큼 들어갔는지 센다.

## 2. 검토한 방식들

### 선택 — git이 정본: `git diff prev..HEAD --name-status`

- 마지막으로 처리한 커밋(prev)과 지금 HEAD 사이의 변경 파일 목록을 git에게 묻는다.
  추가(A)·수정(M)·삭제(D)·이름변경(R)이 그대로 나온다. 파일 시간(mtime)이나 전체
  해시 비교보다 정확하고 싸다.
- prev는 **처리가 끝난 뒤에만** 파일에 기록한다. 중간에 실패하면 prev가 안 움직여서
  다음 요청이 같은 범위를 다시 처리한다 = 실패 재시도가 곧 멱등 재처리.

### 대안 — 매번 전체 재색인 (탈락)

- 616파일 임베딩에 13분. push마다 13분은 안 된다. 단, **"처음 한 번"과 "복구용 수동
  경로"로는 필요**해서 남겨둔다(prev가 없을 때 자동 / `full:true` 플래그).

### 대안 — 파일 워처(inotify)로 변경 감지 (탈락)

- 컨테이너 볼륨에서 이벤트 신뢰성이 떨어지고, "어느 커밋까지 반영됐나"를 말할 수 없다.
  → 탈락.

## 3. 구현 워크플로우

```
POST /internal/sync {request_id, commit_sha}  + X-Sync-Secret
  ▼
[문지기 — 멱등·single-flight]
  commit_sha == 마지막 처리 SHA ─────▶ 200 {"skipped":"duplicate"}     (중복 무시)
  처리 중 & 같은 SHA ─────────────────▶ 200 {"skipped":"in_progress"}
  처리 중 & 다른 SHA ─────────────────▶ 409 {"code":"sync_in_progress"} (한 번에 하나만)
  아니면 ────────────────────────────▶ 202 {"started":"incremental"|"full_index"} + 백그라운드 시작
  ▼ (백그라운드 스레드)
① git fetch + reset → HEAD 확정
② prev 없음 → 전체 목록 / 있음 → diff prev..HEAD (md만)     ← 색인 입력의 정본
③ 파일마다:  기존 청크 전량 삭제(path 기준) → 
             청킹(h2 단위, 8KB 넘으면 h3→문단) → 
             BGE-M3 임베딩(청크 묶음 1회 호출) → 
             ES bulk 저장(_id = path#chunk_no — 같은 걸 다시 넣어도 덮어씀) →
             ★ count(path) == 청크 수 확인 (틀리면 실패 처리)
④ 전부 성공 → prev = HEAD 기록.  하나라도 실패 → prev 그대로(다음에 재처리)
```

**청크가 단위인 이유**: 58KB짜리 문서를 벡터 하나로 만들면 "그 문서 어딘가에 있다" 수준의
검색밖에 안 된다. 절(h2) 단위로 자르면 "이 절"을 찾아준다.

## 4. 코드 변경 (핵심)

```kotlin
// SyncService — 성공 후에만 전진. 이 한 줄이 "실패 재시도 = 멱등 재처리"를 만든다
val chunks = indexing.indexPaths(requestId, changes, headSha)
writeLastSha(headSha)      // ← 예외가 나면 여기 못 온다
```

```kotlin
// IndexingService — "돌았다"가 아니라 "들어갔다"를 센다
es.bulkUpsert(documents)
val count = es.countByPath(path)
check(count == doc.chunks.size.toLong()) { "count 불일치 $path" }
```

## 5. 구현 중 마주친 문제 (실기동에서 4건 — 단위 테스트론 하나도 못 잡는 것들)

### 문제 1 — 첫 시도: `/embed` 연결 거부
- **원인**: 배포하며 embedding 컨테이너도 재생성됐는데, BGE-M3 **모델 로딩(1~2분)이
  끝나기 전에** sync가 호출을 쳤다.
- **수정**: `depends_on: embedding: condition: service_healthy` + 클라이언트 타임아웃 명시.
- **배경**: "컨테이너가 떴다 ≠ 서비스가 준비됐다". 기동 순서는 헬스체크로 묶어야 한다.

### 문제 2 — 두 번째: ES가 `Invalid UTF-8 start byte 0xb7`
- **원인**: Spring `RestClient`에 문자열 본문을 주면 기본 문자셋이 **ISO-8859-1**이다.
  한글이 깨진 바이트로 전송돼 ES가 JSON 파싱에 실패.
- **수정**: 모든 ES 요청 본문을 `.toByteArray()`(UTF-8)로 보내고 `charset=utf-8` 명시.
- **배경**: "문자열 = UTF-8"이 아니다. 전송 계층의 문자셋 기본값은 프레임워크마다 다르다.
  한글 데이터를 다룬다면 첫 스모크에 한글을 반드시 넣어야 한다.

### 문제 3 — 세 번째: 파일을 못 찾음 (`"programmers/\352\267\270..."`)
- **원인**: git이 한글 경로를 **따옴표 + 8진수**로 이스케이프해 출력(`core.quotepath` 기본값).
- **수정**: `git -c core.quotepath=off ls-files/diff`.
- **배경**: 도구의 "사람용 출력"을 "기계용 입력"으로 쓸 때 늘 이 함정이 있다.

### 문제 4 — 앱 헬스체크가 계속 DOWN
- **원인**: Redis 라이브러리를 추가하자 Spring이 헬스체크에 Redis를 포함시켰는데, 접속
  주소를 안 줘서 기본값 **localhost:6379 = 컨테이너 자기 자신**을 두들겼다. 로그 전송도
  같은 이유로 조용히 실패 중이었다(예외를 삼키도록 설계했으니 티도 안 남).
- **수정**: `spring.data.redis.url`을 compose의 redis로 지정.
- **배경**: "실패 무해" 설계는 좋지만, 무해한 실패는 **관찰 수단이 없으면 영원히 모른다**.
  헬스체크가 DOWN을 띄워준 덕에 잡았다.

### (단위 테스트가 잡은 것) 청크 상한이 바이트가 아니라 글자 수
- 8KB 상한을 `String.length`로 쟀다. 한글은 글자당 3바이트라 24KB 청크가 나올 수 있었다.
  테스트가 먼저 빨간불을 켜서 실기동 전에 고침.

## 6. 결론

616파일 → 911청크, 13분, **ES count = 911 정확 일치**. 같은 SHA 재요청은 `duplicate`로
무시. 한국어 질의("정렬을 나중으로 미루는 구조")로 lsm-tree 문서가 톱히트 — nori가 일한다.
증분 경로는 다음 실제 push 때 검증(이 문서를 push하는 순간이 그 첫 테스트다). PR: #4
