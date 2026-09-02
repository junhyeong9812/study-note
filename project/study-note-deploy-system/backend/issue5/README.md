# issue5 — 듀얼 리뷰 반영: 두 모델이 본 구멍들을 하나씩 메우다

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-backend
- 이슈 #9 · PR: https://github.com/junhyeong9812/study-note-deploy-system-backend/pull/10

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                          [새 문서 — 지금 이것]
> 표로 "구멍|문제|조치" 압축      ──▶   지적마다: 무엇이 위험했나 → 무엇을
>                                       고민했나 → 그래서 이렇게 (서사)
> "chunk_no로 바꿈"만 서술        ──▶   실제 커밋 8ea60a4·f77b564 diff 그대로
> full 재색인 글 설명             ──▶   [기존 흐름]↔[변경 흐름] ASCII 나란히
> ```
> 표현도 순화: "안전벨트로 박아둠" → "안전벨트로 유지".

---

## 1. 배경 — 왜 두 명의 리뷰어인가

이슈 1~4를 머지한 뒤, 누적된 diff를 **서로 다른 두 모델**에게 같은 packet(명세 + 설계 문서
+ diff)으로 보내 리뷰시켰다.

> 용어 — 듀얼 리뷰(dual review): 같은 코드를 독립된 리뷰어 둘에게 각각 보는 것. 같은 모델
> 둘은 같은 맹점을 공유하므로, **다른 모델**이어야 서로 다른 신호가 나온다.

```
누적 diff (issue1~4)
   │  같은 packet(명세+설계+diff)을 두 모델에게
   ├──▶ 리뷰어 A(모델 1) : 11건
   └──▶ 리뷰어 B(모델 2) : 14건
        │  겹치는 핵심 5건 (양쪽이 독립으로 잡은 = 신뢰도 높음)
        ▼
   내가 각 지적을 채택/기각 판정
        ▼
   종합 감사 1회 (판정표를 또 다른 모델에게)  ──▶ "조치 강도 부족" 3건 반려
        ▼
   수정
        ▼
   타깃 재점검 1회 (수정 diff만)              ──▶ "수정이 만든 새 구멍" 3건
```

채택/기각의 기준을 먼저 정해뒀다.

- **채택**: 명세·설계와 어긋나고 + 실패 시나리오가 구체적이며 + 코드 위치가 있는 것.
- **기각(근거 기록)**: 설계 의도로 설명되는 것. 기각도 이유를 남긴다 — 나중에 같은 지적이
  또 오면 "그때 왜 안 했지"를 다시 고민하지 않게.
- **감사·재점검**: 리뷰어의 지적도 틀릴 수 있다 — 실행해보고 판정한다.

아래는 채택한 지적들을 **왜 그게 위험했는지**부터 하나씩 풀어 쓴 것이다.

---

## 2. 채택한 지적들

### B1 — RRF 병합 키가 서로 다른 청크를 하나로 접고 있었다

**무엇이 위험했나:** issue4의 RRF 병합은 "같은 청크"를 `path#heading`으로 식별했다. 그런데
issue2의 청킹 규칙상 **큰 절 하나를 여러 문단 청크로 쪼갤 때 그 청크들의 heading은 전부
같다.** 그러면 서로 다른 청크가 병합 단계에서 하나로 접혀, 등수 점수가 엉뚱하게 합산되고
순위가 왜곡된다.

**무엇을 고민했나:** 청크의 진짜 정체성이 무엇인가. 설계 문서(es-index D1)에는 이미
`path#chunk_no`가 청크의 식별자로 정의돼 있었다. 코드가 그 정의를 안 따르고 heading을 쓴 게
문제였다.

**그래서 이렇게 했다** (`.../search/SearchService.kt`, 커밋 8ea60a4) — 병합 키를 설계대로
`chunk_no` 기반으로 바꾸고, 결과에 `chunk_no`를 실어 보냈다:

```diff
- data class SearchHit(val path: String, val heading: String, ...)
+ data class SearchHit(val path: String, val chunkNo: Int, val heading: String, ...)

- /** 두 랭킹을 RRF로 병합 — 같은 청크(_id 기준)는 점수 합산 */
+ /** RRF 병합 — 청크 정체성은 path#chunk_no (es-index D1). 같은 청크는 점수 합산 (B1) */
-         val key = "${hit.path}#${hit.heading}"
+         val key = "${hit.path}#${hit.chunkNo}"
```

### B3 — ES가 멈추면 검색 스레드가 영원히 기다리고, sync는 영원히 "처리 중"

**무엇이 위험했나:** Elasticsearch 접근에 타임아웃이 없었다. ES가 멈추면 검색 스레드가 무한
대기하고, sync도 영원히 "처리 중"이 되어 이후 요청마다 409(single-flight 거절)를 쏟아낸다.
게다가 ES 접근 코드가 검색·색인 두 곳으로 갈라져 있어 정책(타임아웃·인덱스명)을 한 곳에서
못 걸었다.

**그래서 이렇게 했다** (`.../indexing/EsClient.kt`, 커밋 8ea60a4) — ES 접근을 단일 창구로
모으고, 경로별로 다른 타임아웃을 명시했다. 사용자 경로(검색)는 짧게, 색인 경로(bulk)는 길게:

```kotlin
/** ES 접근 단일 창구 — 색인·검색 공용 (B3: 타임아웃·인덱스명 정책을 한 곳에). 쓰기·읽기 모두 alias 경유. */
    private fun clientWith(readTimeout: Duration): RestClient = RestClient.builder()
        .requestFactory(SimpleClientHttpRequestFactory().apply {
            setConnectTimeout(Duration.ofSeconds(3))
            setReadTimeout(readTimeout)
        }) ...
    private val queryClient = clientWith(Duration.ofSeconds(5))    // 검색·count — 사용자 경로
    private val bulkClient  = clientWith(Duration.ofSeconds(60))   // bulk·delete_by_query — 색인 경로
```

> 용어 — alias(별칭): 실제 인덱스에 붙이는 가명. 재색인 때 새 인덱스로 무중단 전환하려면
> 코드가 실제 인덱스명이 아니라 별칭을 바라봐야 한다. 여기서 "인덱스만 있고 alias가 빠진
> 상태"도 자동 복구하도록 했다.

### B4 — 의미 검색 장애가 검색 전체를 죽이고 있었다

**무엇이 위험했나:** llm 재작성에는 폴백이 있었는데(issue4), 임베딩 서버가 예외를 던지면
검색 전체가 503으로 죽었다. 불변식("뭐가 죽어도 응답")이 절반만 지켜진 상태였다.

**그래서 이렇게 했다** — kNN 호출을 try/catch로 감싸 실패 시 BM25 단독으로 강등하고,
`dense_used=false`를 응답에 실었다(코드 diff는 issue4 문서 6장에 상세). 이로써 llm·임베딩
두 부가 기능이 모두 검색을 인질로 잡지 못하게 됐다.

### B7 — diff가 한번 실패하면 색인이 영구히 멈추고, 복구할 길도 없었다

**무엇이 위험했나:** sync는 "이전 SHA와 현재 SHA 사이 diff"로 바뀐 파일만 색인한다. 그런데
처리해둔 SHA가 shallow clone(얕은 복제 — 최근 커밋 몇 개만 받아온 저장소)의 경계를 벗어나면
diff 계산이 실패한다. 그러면 그 자리에서 끝 — 이전 SHA가 안 움직이니 다음 sync도 같은
지점에서 실패한다(영구 스톨). 게다가 전체를 다시 색인할 수동 경로도 없었다.

**무엇을 고민했나:** "diff 실패"를 에러로 던지고 사람이 개입하게 할 것인가, 아니면 자동으로
전체 색인으로 강등할 것인가. 노트 저장소는 크지 않아 전체 색인 비용이 감당 가능하므로,
**조용히 멈추느니 시끄럽게 강등**하는 쪽을 골랐다.

```
[기존] prev 있음 → diff → 실패하면 끝 (prev 안 움직임 → 다음도 실패 → 영구 스톨)

[변경] prev 있음 → diff ──실패(shallow 경계 밖)──▶ 전체 목록으로 강등(warning 로그)
       전체 색인 후 → commit_sha != 이번 SHA 인 문서 삭제  ← 저장소에서 사라진 문서 청소(고아 정리)
       + POST /internal/sync {"full": true} 수동 재색인 경로도 신설
```

**그래서 이렇게 했다** (`.../indexing/IndexingService.kt`, 커밋 8ea60a4) — 전체 색인 뒤
"이번 SHA로 안 찍힌 문서"를 지워 고아를 정리한다:

```kotlin
    /** full 색인 후 고아 정리 — 이번 SHA로 안 찍힌 문서 = 저장소에 더 없는 문서 (B7) */
    fun deleteStale(requestId: String, commitSha: String) {
        val deleted = es.deleteWhereShaNot(commitSha)
        if (deleted > 0) requestLog.log(requestId, "index stale cleanup: $deleted docs (sha!=$commitSha)")
    }
```

### B8 — git 프로세스가 멈추면 출력을 읽다가 영원히 블록됐다

**무엇이 위험했나:** git 명령의 출력을 `readText()`로 전부 읽은 **뒤에** 타임아웃을 거는
순서였다. 그런데 git 프로세스가 멈추면 `readText()`가 waitFor에 닿기도 전에 무한 블록한다 —
타임아웃 자체가 무의미해진다.

**그래서 이렇게 했다** (`.../sync/GitRepository.kt`, 커밋 8ea60a4) — 출력 소비를 별도
스레드로 돌리고, 메인은 `waitFor(120s)`를 먼저 건다:

```diff
- val output = process.inputStream.bufferedReader().readText()
- if (!process.waitFor(120, TimeUnit.SECONDS)) { process.destroyForcibly(); error("git timeout ...") }
+ // 출력 소비를 별도 스레드로 — 프로세스 행 시 readText가 waitFor 이전에 무한 블록하는 것 방지 (B8)
+ val reader = Thread { process.inputStream.bufferedReader().forEachLine { outputBuffer.appendLine(it) } }
+ ...
+ if (!process.waitFor(120, TimeUnit.SECONDS)) { process.destroyForcibly(); error("git timeout ...") }
```

### 그 밖에 채택한 지적들 (짧게)

- **전역 봉투 구멍:** 파라미터 누락·타입 오류·예상 못 한 예외가 Spring 기본 JSON으로 새어
  나갔다 → `@RestControllerAdvice`(모든 컨트롤러 예외를 한 곳에서 잡는 Spring 장치)로 전부
  우리 봉투(`{success, ...}`)로 감쌌다.
- **diff 파싱 무테스트:** 여기가 틀리면 문서가 조용히 인덱스에서 사라진다. 파싱을 순수 함수로
  분리하고 rename·한글 경로·탭 케이스 테스트를 붙였다.
- **단일 거대 문단:** 문단 하나가 8KB를 넘으면(개행 없는 코드블록) 청크 상한이 안 지켜졌다 →
  줄·코드포인트 경계로 강제 분할(surrogate 안전 — 아래 5장).
- **LAN 바인딩(B14):** 앱 포트가 `0.0.0.0`(모든 인터페이스) 기본값이라, 인터페이스가 늘면
  외부에 노출된다 → 5장에서 fail-closed로 강화.

---

## 3. 기각한 지적 — 왜 안 받아들였나 (이것도 기록으로)

### 기각 (1) "요청 SHA를 checkout해서 그 SHA를 색인하라"

리뷰어는 "요청에 담긴 SHA로 checkout한 뒤 색인해야 정확하다"고 봤다. 하지만 우리 설계는
다르다 — **SHA는 중복 판별 힌트일 뿐, 색인 대상은 항상 원격 HEAD**다(수렴 모델). 빠르게 두
번 push가 오면 뒤처진 SHA 요청은 no-op이 되고, 최신 HEAD 한 번만 색인된다. checkout 방식은
오히려 오래된 상태를 색인할 위험이 있어 기각하고, 설계 의도를 문서에 명문화했다.

### 기각 (2) "평면 목록 반환은 계약 위반, 트리를 서버가 줘야 한다"

리뷰어는 "폴더 구조(트리)를 API가 줘야 한다"고 봤다. 당시 설계는 **front가 평면 목록으로
트리를 구성**하는 것이 계약이었다 — 그래서 기각하고 문서에 명문화했다. (다만 이 결정은 이후
issue7에서 "트리는 sync 때만 변한다"는 새 근거로 뒤집혀 서버가 /api/tree를 주게 된다 —
기각을 기록해둔 덕에 번복의 맥락이 남았다.)

---

## 4. 감사가 "조치가 결함을 해소하지 못한다"고 반려한 3건

채택/기각표를 다시 또 다른 모델에게 감사시켰더니, 조치의 **강도**를 지적했다. 대표적으로
임베딩 절단 건 — 내 조치는 "절단 시 warning 로그"였는데 감사가 말하길:

> "warning만 추가해도 청크 뒷부분이 dense 검색에서 제외되는 문제는 그대로다. 모델 토큰
> 한도에 맞춘 추가 청킹 또는 전체 청크 임베딩이 필요하다."

맞는 말이다 — 로그는 문제를 **알려줄** 뿐 **없애지** 못한다. 그래서 재조치했다: 절단 상한을
6000자 → 9000자로 올렸다. 청크 자체가 8KB(≈ASCII 8192자·한글 ~2700자) 이하로 잘리므로
9000자 상한이면 **절단이 구조적으로 발생하지 않는다**(warning은 안전벨트로 유지).

같은 논리로 BIND 건도 강화했다. 기본값 `0.0.0.0`은 "설정을 깜빡하면 그대로 외부 노출"이다.
감사 지적을 받아 **fail-closed**(설정을 안 하면 아예 기동을 거부)로 바꿨다.

`docker-compose.yml` (커밋 8ea60a4):

```diff
-      - "8090:8090"          # LAN — front가 호출
+      # 전제: 호스트는 사설 LAN 단일 인터페이스(공유기 뒤). 공인 인터페이스가 생기면 BIND_ADDR로 제한 (리뷰 B14)
+      - "${BIND_ADDR:?set-in-env}:8090:8090"   # fail-closed — 배포 .env가 LAN 주소 지정 (감사 반영)
+      - "${BIND_ADDR:?set-in-env}:6379:6379"   # LAN — llm 등 타 호스트가 XADD
```

> 용어 — `${BIND_ADDR:?...}`: 셸/compose 문법. 변수가 비어 있으면 뒤 메시지를 내며 **기동을
> 중단**한다. "설정 안 하면 그냥 뜨는" 게 아니라 "설정 안 하면 못 뜨는" 것 — fail-closed.

이 fail-closed 바인딩은 이후 issue9에서 헬스체크와 한 번 충돌하는데, 그건 그 문서에서 다룬다.

---

## 5. 재점검이 잡은 "수정이 방금 만든 새 구멍" 3건

수정 diff만 다시 보게 했더니(전체 재리뷰가 아니라 좁게) 셋 다 **내 수정이 방금 만든** 결함
이었다:

```
- GlobalErrorHandler · 포괄 Exception 처리로 size=abc 같은 클라이언트 입력 예외까지
  500으로 변환. 기존 Spring 4xx 응답을 서버 장애로 회귀시켰다.
- ContentController · readFile()의 모든 예외를 404로 처리해 I/O·권한 장애도 "문서 없음"으로 오인.
- Chunker · String.chunked()는 UTF-16 단위로 자르므로 surrogate pair(이모지 등 4바이트 문자)를 찢는다.
```

각각 이렇게 고쳤다 (커밋 f77b564):

**입력 오류는 4xx로 되돌린다** (`.../common/GlobalErrorHandler.kt`) — 타입 불일치·본문 파싱
실패를 422 계열로 분리:

```diff
- @ExceptionHandler(MissingServletRequestParameterException::class, MissingRequestHeaderException::class)
+ @ExceptionHandler(
+     MissingServletRequestParameterException::class, MissingRequestHeaderException::class,
+     MethodArgumentTypeMismatchException::class, HttpMessageNotReadableException::class,   // size=abc·깨진 본문
+ )
```

**404는 파일 부재만** (`.../content/ContentController.kt`) — 부재만 404, 그 외 I/O 장애는
전역 500 봉투로:

```diff
- } catch (_: Exception) {
+ } catch (_: java.io.FileNotFoundException) {   // 부재만 404 — I/O 장애는 전역 500 봉투로
      requestLog.log(requestId, "doc not found: $path", "warning")
      return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Envelope.fail("not_found"))
+ } catch (_: java.nio.file.NoSuchFileException) { ...
```

**surrogate pair를 안 찢는 분할** (`.../indexing/Chunker.kt`):

> 용어 — surrogate pair: 이모지처럼 코드포인트가 큰 문자는 UTF-16에서 2칸(high+low
> surrogate)으로 표현된다. 그 사이를 자르면 깨진 반쪽 글자가 생긴다.

```kotlin
    /** 코드포인트 경계 분할 — String.chunked는 UTF-16 단위라 surrogate pair를 찢을 수 있다 (재점검 반영) */
    private fun chunkedByCodePoints(text: String, sizeInUnits: Int): List<String> {
        ...
        var end = minOf(start + sizeInUnits, text.length)
        if (end < text.length && Character.isHighSurrogate(text[end - 1])) end -= 1   // 끝이 반쪽이면 한 칸 당김
        ...
    }
```

**왜 마지막 재점검이 "수정 diff 한정"인가:** 여기서 그 이유가 드러난다 — 수정은 급하게
이뤄지는 코드라 새 결함 밀도가 높고, 좁게 보니 깊게 본다. 전체 재리뷰보다 이 좁은 재점검이
방금 만든 구멍을 더 잘 잡는다.

---

## 6. 결론

리뷰 25건 중 다수 채택 · 2건 근거 있는 기각 · 일부는 [구현 검증] 대장으로 이연. 수정 뒤
`full:true`로 전체 재색인(630파일 → 950청크, 고아 정리 동작 확인)하고 검색·봉투를
재검증했다. 테스트 22건 green. 이 이슈의 핵심 교훈은 두 가지 — **다른 모델이라야 다른 구멍을
본다**(B1·B4는 한쪽만 잡음), 그리고 **채택한 조치도 실측·감사로 강도를 재본다**(warning은
문제를 없애지 못한다). PR #10
