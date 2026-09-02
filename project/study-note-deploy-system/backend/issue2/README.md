# issue2 — sync 파이프라인: push 한 번이 색인으로 바뀌기까지

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-backend
- 이슈 #3 · PR: https://github.com/junhyeong9812/study-note-deploy-system-backend/pull/4

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "선택 / 대안 탈락" 요약          ──▶     각 갈림길: 무엇이 문제였나
>                                          → 무엇을 고민했나 → 그래서 이렇게
> 파이프라인을 글로 서술          ──▶     문지기 판정 + 백그라운드 흐름 ASCII
> 함정 5건은 이미 로그 있음        ──▶     그대로 살리되 실제 커밋 diff로 보강
>                                          (3c66730·4c2ef2b·40b9eb9·8f91a96)
> 멱등·single-flight 용어 던짐      ──▶     그 자리에서 한 줄 풀이
> ```

---

## 1. 배경 — "바뀐 것만, 한 번만, 정말로 들어갔는지 세면서"

study-note 저장소에 push하면, **바뀐 문서만** 검색엔진에 반영돼야 한다. 요구는 세 겹이었다.

1. **무엇이 바뀌었나를 정확히 안다** — 매번 전체를 다시 훑지 않는다.
2. **같은 push가 두 번 와도 한 번만 처리한다** — 배포 재시도나 중복 호출에 대비.
   > 용어 — 멱등(idempotent): 같은 요청을 여러 번 보내도 결과가 한 번 보낸 것과 같은 성질.
   사용자 결정으로, 요청에 그 시점의 커밋 해시 `commit_sha`를 실어 보내 이걸로 중복을 가르기로 했다.
3. **"에러 없이 돌았다"를 "다 됐다"로 착각하지 않는다** — 넣으려던 만큼 실제로 들어갔는지 센다.

---

## 2. 갈림길마다의 판단

### 갈림길 (1) — 무엇이 바뀌었는지 어떻게 아는가

**무엇이 문제였나:** "바뀐 문서만" 처리하려면 먼저 "무엇이 바뀌었나"를 알아야 한다.
후보는 셋 — ① 파일 수정 시각(mtime) 비교 ② 파일 워처(inotify)로 실시간 감지 ③ git에게 직접 묻기.

**무엇을 고민했나:** mtime은 clone/pull 과정에서 전부 갱신돼버려 신뢰할 수 없다. inotify는
컨테이너 볼륨에서 이벤트가 유실되기 쉽고, 무엇보다 **"어느 커밋까지 반영됐다"를 말할 수 없다.**
git은 두 커밋 사이의 변경 목록(추가 A / 수정 M / 삭제 D / 이름변경 R)을 정확히, 싸게 알려준다.

**그래서 이렇게 했다:** **git을 정본으로 삼는다.** 마지막으로 처리한 커밋(prev)과 지금 HEAD 사이를
`git diff prev..HEAD --name-status`로 묻는다. 그리고 결정적으로 — prev는 **처리가 완전히 끝난
뒤에만** 파일에 기록한다. 중간에 실패하면 prev가 안 움직이므로, 다음 요청이 같은 범위를 다시
처리한다. 즉 **실패 후 재시도가 곧 멱등 재처리**가 된다.

### 갈림길 (2) — 그래도 전체 재색인은 필요하다

**무엇이 문제였나:** 증분(바뀐 것만) 처리만 있으면, 맨 처음 한 번(prev가 없을 때)이나 색인이
망가졌을 때 복구할 길이 없다.

**무엇을 고민했나:** 전체 재색인은 616파일 임베딩에 13분이 걸린다. push마다 13분은 안 된다.
하지만 "처음 한 번"과 "복구용 수동 경로"로는 반드시 있어야 한다.

**그래서 이렇게 했다:** prev가 없으면 자동으로 전체를, 있으면 증분을 돈다. 복구가 필요하면
`full:true` 플래그로 강제 전체 재색인을 부를 수 있게 남겨뒀다.

### 갈림길 (3) — 색인의 단위: 문서 통째 vs. 청크

**무엇이 문제였나:** 58KB짜리 문서를 벡터 하나로 만들면, 검색이 "그 문서 어딘가에 있다" 수준밖에
안 된다. 독자는 "그 문서의 이 절"을 찾고 싶어 한다.

**그래서 이렇게 했다:** 문서를 절(h2 헤딩) 단위 **청크**로 잘라 색인한다. 절이 8KB를 넘으면 h3으로,
그래도 넘으면 문단 경계로 더 쪼갠다. 청크마다 벡터를 만들어 "이 절"을 찾아준다.

> 용어 — 청크(chunk): 문서를 검색·임베딩 단위로 자른 조각. 여기선 대략 "절 하나".

---

## 3. 구현 워크플로우 — 문지기와 백그라운드

sync는 두 층으로 나뉜다. 앞단의 **문지기**(요청을 받자마자 중복·동시성만 판정하고 즉시 응답)와,
뒷단의 **백그라운드 파이프라인**(실제 pull→색인).

> 용어 — single-flight: "같은 종류의 작업은 한 번에 하나만 진행"시키는 것. sync가 돌고 있는데
> 또 다른 sync가 오면, 새로 시작하지 않고 거절하거나 흘려보낸다.

```
POST /internal/sync {request_id, commit_sha}  + X-Sync-Secret
  ▼
[문지기 — 멱등·single-flight]
  commit_sha == 마지막 처리 SHA ─────▶ 200 {"skipped":"duplicate"}      (중복 무시)
  처리 중 & 같은 SHA ─────────────────▶ 200 {"skipped":"in_progress"}
  처리 중 & 다른 SHA ─────────────────▶ 409 {"code":"sync_in_progress"}  (한 번에 하나만)
  아니면 ────────────────────────────▶ 202 {"started":"incremental"|"full_index"} + 백그라운드 시작
  ▼ (백그라운드 스레드)
① git fetch + reset → HEAD 확정
② prev 없음 → 전체 목록 / 있음 → diff prev..HEAD (md만)      ← 색인 입력의 정본
③ 파일마다:  기존 청크 전량 삭제(path 기준) →
             청킹(h2 단위, 8KB 넘으면 h3→문단) →
             BGE-M3 임베딩(청크 묶음 1회 호출) →
             ES bulk 저장(_id = path#chunk_no — 같은 걸 다시 넣어도 덮어씀) →
             ★ count(path) == 청크 수 확인 (틀리면 실패 처리)
④ 전부 성공 → prev = HEAD 기록.  하나라도 실패 → prev 그대로(다음에 재처리)
```

> 용어 — 202 / 409: HTTP 응답 코드. 202 = "요청을 접수했고 뒤에서 처리 중". 409 = "지금은
> 충돌 상태라 못 받는다"(여기선 "이미 sync 진행 중").

---

## 4. 코드 변경 (핵심)

### 문지기 — commit_sha로 중복·동시성을 가른다

`src/main/kotlin/xyz/junproject/backend/sync/SyncService.kt` (커밋 3c66730):
```kotlin
fun requestSync(requestId: String, commitSha: String?): Decision {
    val lastSha = readLastSha()
    if (commitSha != null && commitSha == lastSha) return Decision.Skip("duplicate")
    val current = inFlightSha.get()
    if (current != null) {
        return if (commitSha != null && commitSha == current) Decision.Skip("in_progress")
        else Decision.Busy
    }
    if (!inFlightSha.compareAndSet(null, commitSha ?: "unknown")) return Decision.Busy
    thread(name = "sync-worker") { runPipeline(requestId, lastSha) }
    return Decision.Started(if (lastSha == null) "full_index" else "incremental")
}
```
`inFlightSha`는 "지금 처리 중인 SHA"를 담는 원자적(atomic) 참조다. `compareAndSet(null, …)`은
"비어 있을 때만 채운다"를 한 번의 원자 연산으로 해서, 두 요청이 동시에 들어와도 하나만 이긴다.

### 성공 후에만 전진 — 이 한 줄이 "실패 재시도 = 멱등 재처리"를 만든다

`SyncService.kt` runPipeline (커밋 3c66730):
```kotlin
val changes = if (prevSha == null) git.allMarkdown().map { 'A' to it }
              else git.changedMarkdown(prevSha, headSha)
val chunks = indexing.indexPaths(requestId, changes, headSha)
writeLastSha(headSha)      // 전량 성공 후에만 전진 (D5-3). 예외가 나면 여기 못 온다
```

### "돌았다"가 아니라 "들어갔다"를 센다 — record-level 검증

`src/main/kotlin/xyz/junproject/backend/indexing/IndexingService.kt` (커밋 3c66730):
```kotlin
es.bulkUpsert(documents)
// record-level 검증 — "에러 없이 돌았다 ≠ 완료" (silent failure 차단)
val count = es.countByPath(path)
check(count == chunks.size.toLong()) { "count 불일치 $path: es=$count chunks=${chunks.size}" }
```
`bulkUpsert`가 예외 없이 끝나도, ES가 실제로 그 path에 청크 몇 개를 갖고 있는지 되물어
**청킹한 개수와 일치하는지** 확인한다. 하나라도 조용히 빠졌으면 여기서 실패로 잡힌다.

---

## 5. 구현 중 마주친 문제 (실기동 4건 + 테스트가 잡은 1건)

전체 색인을 처음 돌리는 데 **6번 시도**했다. 매 시도가 다른 지점에서 죽었고, 각각이 독립된
함정이었다. 아래는 각 시도의 실제 로그다.

### 시도 1 — 시작 0.8초 만에 죽음: 임베딩 서버 연결 거부

**증상** (`/internal/sync/status`와 앱 로그):
```
sync-full-1:backend:sync start FULL..d9d1db45 files=616
sync-full-1:backend:sync failed: I/O error on POST request for "http://embedding:8080/embed": null
```

**진단:** ① `docker ps` — 컨테이너가 전부 "Up About a minute", **재생성된 지 1분**밖에 안 됐다.
② `docker logs backend-embedding`:
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.      ← 여기서 멈춤 (모델 로딩 중)
```
BGE-M3 모델 로딩은 1~2분 걸리는데 sync는 기동 10초 뒤에 `/embed`를 쳤다. 서버가 아직 포트를
안 연 상태라 연결이 거부됐다(메시지 끝의 `null`이 그 거부다).

**어떻게 고쳤나:** app을 embedding이 healthy가 될 때까지 기다리게 묶었다.

`docker-compose.yml` (커밋 4c2ef2b):
```diff
     depends_on:
       elasticsearch:
         condition: service_healthy
       redis:
         condition: service_started
+      embedding:
+        condition: service_healthy   # BGE-M3 모델 로딩(1~2분) 전에 /embed를 치면 연결 거부 (실측)
```
클라이언트에도 connect 5초 / read 3분 타임아웃을 명시했다(그전엔 무제한이라 응답 없이 매달릴 수
있었다). **교훈: "컨테이너가 떴다 ≠ 서비스가 준비됐다."** 준비 여부는 healthcheck가 판정하고,
기동 순서는 `depends_on: service_healthy`로 묶는다.

### 시도 4 — 이번엔 ES가 거부: 그런데 진짜 에러가 우리 버그에 가려져 있었다

**증상** (시도 3의 로그):
```
sync-full-3:backend:sync failed: bulk 색인 부분 실패: $response
```
`$response` — 값이 아니라 **리터럴 문자열**이 그대로 찍혔다. 에러 상세를 넣으려던 Kotlin 문자열
템플릿을 잘못 써서(`${'$'}response`) 진짜 에러가 가려진 것이다. 먼저 이 에러 메시지 코드를 고쳐
재실행하니(시도 4) 진짜 원인이 나왔다:
```
sync-full-4:backend:sync failed: bulk 색인 부분 실패: {type=document_parsing_exception,
reason=[1:170] failed to parse field [content] ... caused_by={type=json_parse_exception,
reason=Invalid UTF-8 start byte 0xb7
```

**진단:** `Invalid UTF-8 start byte 0xb7` — 0xb7은 UTF-8에서 첫 바이트가 될 수 없는 값이다.
우리가 만든 JSON은 정상인데 **전송 중에 바이트가 깨졌다**는 뜻. Spring `RestClient`에 문자열
본문을 주면 `StringHttpMessageConverter`가 인코딩하는데, 그 기본 문자셋이 **ISO-8859-1**(라틴)이다.
한글 "정"(UTF-8 3바이트)이 라틴 문자셋으로 다시 인코딩되며 깨진 바이트가 됐다.

**어떻게 고쳤나:** 문자열을 넘기지 말고 **직접 UTF-8 바이트로 인코딩**해서 보낸다. 겸사겸사
가려졌던 에러 메시지도 첫 실패 항목을 뽑아 찍도록 바꿨다.

`src/main/kotlin/xyz/junproject/backend/indexing/EsClient.kt` (커밋 40b9eb9):
```diff
-        val response = client.post().uri("/_bulk?refresh=true").body(body)
-            .header("Content-Type", "application/x-ndjson").retrieve().body(Map::class.java)
-        if (response?.get("errors") == true) error("bulk 색인 부분 실패: ${'$'}response")
+        val response = client.post().uri("/_bulk?refresh=true").body(body.toByteArray())   // UTF-8 바이트로 직접
+            .header("Content-Type", "application/x-ndjson; charset=utf-8").retrieve().body(Map::class.java)
+        if (response?.get("errors") == true) {
+            val firstError = (response["items"] as? List<Map<String, Map<String, Any?>>>)
+                ?.firstNotNullOfOrNull { it["index"]?.get("error") }
+            error("bulk 색인 부분 실패: $firstError")
+        }
```
**교훈 둘:** ① "문자열 = UTF-8"은 착각이다 — 전송 계층의 기본 문자셋은 프레임워크마다 다르다.
한글 데이터는 첫 스모크에 반드시 한글을 넣어라. ② 에러 메시지를 만드는 코드도 틀릴 수 있다 —
가려진 에러는 디버깅 비용을 배로 만든다.

### 시도 5 — 10분 돌다 죽음: git이 한글 경로를 8진수로 이스케이프

**증상:**
```
sync-full-5 ... failed:
/data/study-note/repo/"programmers/\352\267\270\353\236\230\355\224\204/01-...1-question.md"
  (No such file or directory)
```

**진단:** 경로가 **따옴표로 감싸이고 한글이 `\352\267\270…`(8진수)로 바뀌어** 있다. 이건 우리가
만든 문자열이 아니라 `git ls-files`의 출력 그대로다. git은 기본 설정(`core.quotepath=true`)에서
비ASCII 경로를 사람이 보기 "안전하게" 이스케이프해 출력한다. 그 출력을 파일 경로로 그대로 썼으니
존재하지 않는 파일이 됐다.

**어떻게 고쳤나:** git을 부를 때 `core.quotepath=off`를 붙여 이스케이프를 끈다.

`src/main/kotlin/xyz/junproject/backend/sync/GitRepository.kt` (커밋 40b9eb9):
```diff
-        val output = run("git", "diff", "--name-status", "-M", "$prevSha..$headSha", "--", "*.md")
+        // core.quotepath=off — 한글 경로를 8진수 이스케이프로 감싸는 git 기본 동작 차단 (실측: 파일 못 찾음)
+        val output = run("git", "-c", "core.quotepath=off", "diff", "--name-status", "-M", "$prevSha..$headSha", "--", "*.md")
...
-        run("git", "ls-files", "*.md")
+        run("git", "-c", "core.quotepath=off", "ls-files", "*.md")
```
**교훈:** 도구의 "사람용 출력"을 "기계용 입력"으로 쓸 때의 고전 함정. 기계가 읽을 거면 출력
이스케이프를 끄는 옵션부터 찾아라.

### (별개) 앱 헬스체크가 계속 DOWN — Redis가 자기 자신을 두들기고 있었다

**증상:** 배포 후 `app-ready` 대기 루프가 안 끝난다.
```
$ curl -s .../actuator/health
{"groups":["liveness","readiness"],"status":"DOWN"}
...
WARN ... DataRedisReactiveHealthIndicator : Redis health check failed
```

**진단:** Redis 컨테이너 자체는 `redis-cli ping → PONG` 정상이었다. 원인은 접속 주소였다 —
이슈②에서 `spring-boot-starter-data-redis` 의존성을 추가하자 Spring이 ① 헬스체크에 Redis 항목을
자동 편입하고 ② 접속 주소를 안 줬으니 **기본값 `localhost:6379`**로 접속을 시도했다. 컨테이너
안에서 localhost는 **자기 자신(app 컨테이너)**인데, 거기엔 Redis가 없다. 더 위험한 건, 로그
전송(XADD)도 같은 주소로 조용히 실패 중이었다는 것 — 우리 logger는 "전송 실패는 무해" 설계라
예외를 삼키니 **아무 티도 안 났다.**

**어떻게 고쳤나:** 접속 주소를 compose의 redis로 명시했다.

`src/main/resources/application.yml` (커밋 8f91a96):
```diff
 spring:
   application:
     name: backend
+  data:
+    redis:
+      url: ${LOG_REDIS_URL:redis://redis:6379}   # 미지정 시 Spring 기본 localhost = 컨테이너 자신 (함정)
```
**교훈:** "실패해도 무해"로 설계한 경로는 **실패를 알려줄 다른 채널**이 필요하다. 여기선 뜻밖에도
헬스체크가 그 채널이 돼줬다 — DOWN이 아니었으면 로그 유실을 며칠 뒤에야 알았을 것이다.

### (실기동 전에 테스트가 잡은 것) 청크 상한이 바이트가 아니라 글자 수

**증상** (단위 테스트, 커밋 전 개발 중):
```
ChunkerTest > h3도 넘치면 문단 경계 분할 - 청크당 8KB 상한 유지() FAILED
    expected: <true> but was: <false>     ← 청크 하나가 상한을 초과
```

**진단:** `splitByParagraph`가 `buffer.length + paragraph.length > 8192`로 판단했는데,
`String.length`는 **글자 수**다. 한글은 UTF-8로 글자당 3바이트라, 8192자 버퍼는 실제 약 24KB.
상한의 단위(바이트)와 측정의 단위(글자)가 어긋나 있었다.

**어떻게 고쳤나:** 측정도 바이트로 통일했다. 커밋된 최종 코드(3c66730)는 이미 바이트 기준이다
— 아래 char 기준 버전은 커밋 전에 테스트가 잡아낸 작업본 상태다.

`src/main/kotlin/xyz/junproject/backend/indexing/Chunker.kt`:
```diff
-            if (buffer.isNotEmpty() && (buffer.length + paragraph.length) > SPLIT_THRESHOLD_BYTES) {
+            val paragraphBytes = paragraph.toByteArray().size
+            if (bufferBytes > 0 && bufferBytes + paragraphBytes > SPLIT_THRESHOLD_BYTES) {
```
**교훈:** 한글 처리에서 글자수/바이트 혼동은 반드시 한 번은 밟는 함정. 상한의 단위를 정했으면
측정도 같은 단위로. 그리고 테스트 데이터에 한글을 쓰면 이런 게 잡힌다(ASCII 데이터였으면 통과했을 것).

---

## 6. 결론

616파일 → 911청크, 13분, **ES count = 911 정확 일치**. 같은 SHA 재요청은 `duplicate`로 무시.
한국어 질의("정렬을 나중으로 미루는 구조")로 lsm-tree 문서가 톱히트 — nori가 일한다. 증분 경로는
다음 실제 push 때 검증된다(이 문서를 push하는 순간이 그 첫 테스트다). PR: #4
