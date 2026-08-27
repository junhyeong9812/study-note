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

## 5. 구현 중 마주친 문제 (실기동 4건 + 테스트가 잡은 1건)

전체 색인을 처음 돌리는 데 **6번 시도**했다. 매 시도가 다른 지점에서 죽었고, 각각이
독립된 함정이었다. 아래는 각 시도의 실제 로그다.

### 시도 1 — 시작 0.8초 만에 죽음: 임베딩 서버 연결 거부

**증상** (`/internal/sync/status`와 앱 로그):

```
sync-full-1:backend:sync start FULL..d9d1db45 files=616
sync-full-1:backend:sync failed: I/O error on POST request for "http://embedding:8080/embed": null
```

**진단**: ① `docker ps` — 컨테이너 상태를 보니 전부 "Up About a minute" — 배포하며
**재생성된 지 1분**밖에 안 됐다. ② `docker logs backend-embedding`:

```
INFO:     Started server process [1]
INFO:     Waiting for application startup.      ← 여기서 멈춰 있음 (모델 로딩 중)
```

BGE-M3 모델 로딩은 1~2분 걸리는데, sync는 기동 10초 뒤에 `/embed`를 쳤다. 서버는
포트도 안 연 상태 → 연결 거부(메시지의 `null`이 이것).

**수정** (docker-compose.yml + EmbeddingClient):

```diff
     depends_on:
       elasticsearch:
         condition: service_healthy
+      embedding:
+        condition: service_healthy   # 모델 로딩(1~2분) 전에 /embed를 치면 연결 거부 (실측)
```
클라이언트에도 connect 5s / read 3분 타임아웃 명시(그전엔 무제한이라 행 걸릴 수 있었다).

**배경**: "컨테이너가 떴다 ≠ 서비스가 준비됐다." 준비 여부는 healthcheck가 판정하고,
기동 순서는 `depends_on: service_healthy`로 묶는다.

### 시도 4 — 이번엔 ES가 거부: 그런데 에러 메시지가 우리 버그로 가려져 있었다

**증상** (시도 3의 로그):

```
sync-full-3:backend:sync failed: bulk 색인 부분 실패: $response
```

`$response` — **리터럴 문자열**이다. 에러 상세를 넣으려던 Kotlin 문자열 템플릿을 잘못
써서(`${'$'}response`) 진짜 에러가 가려졌다. 먼저 이 에러 메시지 코드부터 고치고
재실행하니(시도 4) 진짜 원인이 나왔다:

```
sync-full-4:backend:sync failed: bulk 색인 부분 실패: {type=document_parsing_exception,
reason=[1:170] failed to parse field [content] of type [text] in document with id 'README.md#2'.
Preview of field's value: '', caused_by={type=json_parse_exception,
reason=Invalid UTF-8 start byte 0xb7
```

**진단**: `Invalid UTF-8 start byte 0xb7` — 0xb7은 UTF-8에서 시작 바이트가 될 수 없는
값이다. 우리가 만든 JSON은 정상인데 **전송 중에 바이트가 깨졌다**는 뜻. Spring
`RestClient`에 문자열 본문을 주면 `StringHttpMessageConverter`가 인코딩하는데, 이 기본
문자셋이 **ISO-8859-1**이다. 한글 "정"(UTF-8 3바이트)이 라틴 문자셋으로 다시 인코딩되며
깨진 바이트가 됐다. README.md#2 = 한글이 처음 등장하는 청크라 거기서 터진 것.

**수정** (EsClient — 모든 요청 본문):

```diff
-        client.post().uri("/_bulk?refresh=true").body(body)
-            .header("Content-Type", "application/x-ndjson")
+        client.post().uri("/_bulk?refresh=true").body(body.toByteArray())   // UTF-8 바이트로 직접
+            .header("Content-Type", "application/x-ndjson; charset=utf-8")
```

**배경**: 두 겹의 교훈. ① "문자열 = UTF-8"은 착각 — 전송 계층의 기본 문자셋은
프레임워크마다 다르다. 한글 데이터를 다루면 첫 스모크에 반드시 한글을 넣어라.
② 에러 메시지를 만드는 코드 자체도 틀릴 수 있다 — 가려진 에러는 디버깅 비용을 배로 만든다.

### 시도 5 — 10분 돌다 죽음: git이 한글 경로를 8진수로 이스케이프

**증상**:

```
sync-full-5 ... failed:
/data/study-note/repo/"programmers/\352\267\270\353\236\230\355\224\204/01-\352\260\200\354\236\245 \353\250\274 \353\205\270\353\223\234/1-question.md" (No such file or directory)
```

**진단**: 경로가 **따옴표로 감싸이고 한글이 `\352\267\270…`(8진수)로 바뀌어** 있다.
이건 우리가 만든 문자열이 아니라 `git ls-files`의 출력 그대로다 — git은 기본 설정
(`core.quotepath=true`)에서 비ASCII 경로를 사람 눈에 "안전하게" 이스케이프해 출력한다.
그 출력을 파일 경로로 그대로 썼으니 존재하지 않는 파일이 됐다.

**수정** (GitRepository):

```diff
-        run("git", "ls-files", "*.md")
+        run("git", "-c", "core.quotepath=off", "ls-files", "*.md")
```
(diff 명령에도 동일 적용)

**배경**: 도구의 "사람용 출력"을 "기계용 입력"으로 쓸 때의 고전 함정. 기계가 읽을 거면
출력 이스케이프를 끄는 옵션부터 찾아라.

### (별개) 앱 헬스체크가 계속 DOWN — Redis가 자기 자신을 두들기고 있었다

**증상**: 배포 후 `app-ready` 대기 루프가 끝나지 않음. 직접 확인:

```
$ curl -s .../actuator/health
{"groups":["liveness","readiness"],"status":"DOWN"}
```

앱 로그에는 주기적으로:

```
WARN ... DataRedisReactiveHealthIndicator : Redis health check failed
```

**진단**: Redis 컨테이너는 `redis-cli ping → PONG` 정상. 그런데 왜? — 이슈②에서
`spring-boot-starter-data-redis` 의존성을 추가하자 Spring이 ①헬스체크에 Redis 항목을
자동 편입시키고 ②접속 주소를 안 줬으니 기본값 **localhost:6379**로 접속을 시도했다.
컨테이너 안에서 localhost는 **자기 자신**이다 — 앱 컨테이너엔 Redis가 없다.
더 무서운 건: 로그 전송(XADD)도 같은 주소로 조용히 실패 중이었다. 우리 logger는
"전송 실패 무해" 설계라 예외를 삼키니 **아무 티도 안 났다.**

**수정** (application.yml):

```diff
 spring:
   application:
     name: backend
+  data:
+    redis:
+      url: ${LOG_REDIS_URL:redis://redis:6379}   # 기본 localhost = 컨테이너 자신 (함정)
```

**배경**: "실패해도 무해"로 설계한 경로는 **실패를 알려줄 다른 채널**이 필요하다. 여기선
의도치 않게 헬스체크가 그 채널이 돼줬다 — DOWN이 아니었으면 로그 유실을 며칠 뒤에야
알았을 것.

### (실기동 전에 테스트가 잡은 것) 청크 상한이 바이트가 아니라 글자 수

**증상** (단위 테스트):

```
ChunkerTest > h3도 넘치면 문단 경계 분할 - 청크당 8KB 상한 유지() FAILED
    expected: <true> but was: <false>     ← 청크 하나가 9KB 검증을 초과
```

**진단·원인**: `splitByParagraph`가 `buffer.length + paragraph.length > 8192`로 판단 —
`String.length`는 **글자 수**다. 한글은 UTF-8로 글자당 3바이트라, 8192자 버퍼는
실제 ~24KB. 상한의 단위(바이트)와 측정의 단위(글자)가 달랐다.

**수정**:

```diff
-            if (buffer.isNotEmpty() && (buffer.length + paragraph.length) > SPLIT_THRESHOLD_BYTES) {
+            val paragraphBytes = paragraph.toByteArray().size
+            if (bufferBytes > 0 && bufferBytes + paragraphBytes > SPLIT_THRESHOLD_BYTES) {
```

**배경**: 한글 텍스트 처리에서 글자수/바이트 혼동은 반드시 한 번은 밟는 함정. 상한의
단위를 정했으면 측정도 같은 단위로 — 그리고 테스트 데이터에 한글을 쓰면 이런 게 잡힌다
(ASCII 테스트였으면 통과했을 것).

## 6. 결론

616파일 → 911청크, 13분, **ES count = 911 정확 일치**. 같은 SHA 재요청은 `duplicate`로
무시. 한국어 질의("정렬을 나중으로 미루는 구조")로 lsm-tree 문서가 톱히트 — nori가 일한다.
증분 경로는 다음 실제 push 때 검증(이 문서를 push하는 순간이 그 첫 테스트다). PR: #4
