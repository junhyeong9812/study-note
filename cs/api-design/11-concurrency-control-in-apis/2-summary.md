# api-design/11-concurrency-control-in-apis — ETag·If-Match·조건부 요청으로 lost update 막기 — 정리 (힌트)

## 해결하는 문제

두 클라이언트가 같은 자원을 읽고, 각자 고쳐서, 통째로 다시 쓴다. 나중에 쓴 쪽이 먼저 쓴 쪽의 변경을 **소리 없이** 지운다.

```text
 Alice                     서버 (doc d1)                      Bob
 GET  → {title:초안, tags:a}  ◀────────▶  GET  → {title:초안, tags:a}
 PUT  {title:새 제목, tags:a} ─▶ 저장
                                    ◀─ PUT  {title:초안, tags:a,b}
 결과: {title:초안, tags:a,b}   ← Alice의 제목 변경이 사라짐 (에러 없음)
```

- *lost update(갱신 손실)*: 동시에 읽고-고치고-쓴 두 요청 중 하나의 변경이 다른 쪽에 덮여 사라지는 이상 현상. 양쪽 다 200을 받았으니 아무도 모른다.

쉬운 예: 공유 문서를 각자 내려받아 고친 뒤 업로드한다.
- 나중에 올린 사람이 앞사람 수정본을 덮는다.
- 업로드할 때 "내가 받은 판이 아직 최신이면만 올려라"라고 하면, 늦게 올린 사람은 거절당하고 최신판을 다시 받아 자기 수정을 얹는다.

똑같은 구조다.
- "내가 받은 판" = `ETag`. "최신이면만" = `If-Match`. "거절" = `412 Precondition Failed`.

실무 예: 관리자 화면에서 두 운영자가 같은 상품 정보를 고친다. 설정 저장 API, 위키 문서, 장바구니, Kubernetes 매니페스트 적용. DB 트랜잭션은 요청 하나 안에서 끝나므로, **요청과 요청 사이**(사람이 화면을 보고 고치는 몇 분)는 DB 락으로 지킬 수 없다. 그 구간을 HTTP 계약으로 지킨다.

## 동작·원리

### 1. 조건부 요청 — 판 번호를 들고 쓰기

```text
 Alice                                서버                              Bob
 GET /docs/d1 ───────────────────▶  ETag: "1"  ◀──────────────── GET /docs/d1
 PUT If-Match: "1" ──────────────▶  "1" == 현재 "1" → 저장, ETag: "2"
                                    ◀──────────────────────── PUT If-Match: "1"
                                    "1" != 현재 "2" → 412 Precondition Failed
                                                          Bob: 다시 GET (ETag "2")
                                                               자기 변경을 얹는다
                                    ◀──────────────────────── PUT If-Match: "2"
                                    저장, ETag: "3"   → 두 변경 모두 남는다
```

- *ETag(entity tag)*: 자원의 현재 표현을 가리키는 불투명한 판 표시. 표현이 바뀌면 값이 바뀐다(RFC 9110 §8.8.3).
- *If-Match*: "현재 ETag가 이 목록 중 하나와 같을 때만 이 메서드를 실행하라"(§13.1.1). 거짓이면 서버는 메서드를 실행하지 않아야 한다(MUST NOT). 그 대신 412를 줄 수 있다.
- *412 Precondition Failed*: 요청 헤더의 조건이 서버에서 거짓으로 평가됐다(§15.5.13).
- *428 Precondition Required*: "이 요청은 조건부여야 한다"(RFC 6585 §3). lost update를 막으려고 `If-Match` 없는 쓰기를 거절할 때 쓴다. 응답에 다시 보내는 법을 설명하라고 권한다(SHOULD).

### 2. RFC 9110이 정한 세부

```text
 비교 함수 (§8.8.3.2)                강한 비교   약한 비교
   W/"1"  vs  W/"1"                  불일치      일치
   W/"1"  vs  "1"                    불일치      일치
   "1"    vs  "1"                    일치        일치

 If-Match      → 강한 비교(MUST)   "바뀐 게 하나라도 있으면 막겠다"
 If-None-Match → 약한 비교(MUST)   캐시 검증용
```

- **약한 ETag(`W/"…"`)로는 If-Match가 성립하지 않는다.** 강한 비교에서 `W/`가 붙은 쪽은 무엇과도 일치하지 않는다. 서버가 GET에 약한 ETag만 준다면 그 값으로 조건부 쓰기를 할 수 없다.
- `If-Match: *` — 현재 표현이 하나라도 있으면 참. "있는 것만 고쳐라". 없으면 거짓인데, 응답은 요청에 따라 다르다. 조건 없이 보냈다면 새로 만들었을 PUT은 412로 막힌다(생성 말고 수정만). 원래 404가 될 요청(DELETE·PATCH 등)은 아래 §13.2.1 규칙대로 조건을 무시하고 404가 된다.
- `If-None-Match: *` — 현재 표현이 없을 때만 참. **"없을 때만 생성"**이다. `PUT /docs/new`를 두 클라이언트가 동시에 해도 하나만 만든다.
- 평가 시점(§13.2.1): 일반 요청 검사(인증·존재 여부 등)를 마친 뒤, 본문 처리·메서드 실행 직전. 조건 없이도 2xx·412 이외의 응답(예: 404, 리다이렉트)이 될 요청이면 조건을 무시한다.
- 평가 순서(§13.2.2): `If-Match` → (없으면) `If-Unmodified-Since` → `If-None-Match` → `If-Modified-Since` → `If-Range`.
- 예외 허용(§13.1.1): 조건이 거짓이어도 "요청한 변경이 이미 적용된 것으로 보이면" 2xx를 줄 수 있다(MAY). 응답을 잃고 재시도한 경우를 위한 것이다. 같은 값으로 수렴하지 않는 동작(비원자적 증가)에는 위험하다고 RFC가 적는다.
- `Last-Modified` + `If-Unmodified-Since`도 같은 일을 하지만 시각이 초 단위라 1초 안의 두 변경을 구분하지 못한다. 쓰기 경합에는 ETag가 맞다.
- 조건 헤더는 **원 서버**가 평가한다. 캐시도 원 서버도 아닌 중간 서버는 평가하지 말고 그대로 넘겨야 한다(MUST NOT/MUST, §13.2.1).

### 3. 다른 관례 — 같은 생각, 다른 숫자

| 출처 | 판 표시 | 불일치 응답 |
|---|---|---|
| RFC 9110 | `ETag` 응답 헤더, `If-Match` 요청 헤더 | 412 |
| Google AIP-154 | 자원 본문의 `etag` 필드(문자열, 출력에 서버가 채움). 요청에 담아 보냄 | gRPC `ABORTED`(must). `google.rpc.Code`의 HTTP 대응은 409 |
| Kubernetes API | `metadata.resourceVersion` | 409 Conflict |

- AIP-154는 클라이언트가 etag를 **안 보내면 허용**하라고 한다(should). 다만 강한 일관성이 필요한 서비스는 etag를 늘 요구하고 없으면 `INVALID_ARGUMENT`로 거절해도 된다고 적는다(may). RFC 6585의 428처럼 필수로 만들지는 API마다 다르다.
- `google.rpc.Code` 주석은 `ABORTED`를 "클라이언트가 더 높은 수준에서 재시도해야 할 때 — 예: 클라이언트가 지정한 test-and-set이 실패해 read-modify-write를 처음부터 다시 해야 할 때"로 설명한다. HTTP 412 vs 409의 숫자는 다르지만 클라이언트가 할 일(다시 읽고 다시 적용)은 같다.

### 4. 서버 쪽: 조건 검사와 쓰기는 한 덩어리

```text
 잘못: 검사와 쓰기가 따로                 맞음: 한 문장
  SELECT version → 1 == If-Match 1 ✔        UPDATE doc SET body=?, version=version+1
  (처리 중 … 다른 요청도 1 == 1 ✔)            WHERE id=? AND version=?   ← 1행이면 성공, 0행이면 412
  UPDATE doc SET body=?                      
  → 둘 다 성공 = lost update 재발
```

- ETag 검사를 애플리케이션에서 "읽고 비교한 뒤 쓰기"로 하면, 비교와 쓰기 사이에 다른 요청이 같은 판으로 통과한다. HTTP 계층에서 막은 lost update가 서버 안에서 다시 생긴다.
- 조건부 UPDATE(버전 컬럼)나 `SELECT … FOR UPDATE`로 검사와 쓰기를 원자적으로 한다. 버전 컬럼과 OCC는 [database/17-occ-and-timestamp-ordering](../../database/17-occ-and-timestamp-ordering/2-summary.md), 조건부 UPDATE 패턴은 [database/18-app-level-concurrency-patterns](../../database/18-app-level-concurrency-patterns/2-summary.md)에 있다.

### 실험: lost update → 412·428, 약한 ETag, 검사 방식의 경쟁

- 환경: JDK 21.0.12 `com.sun.net.httpserver` + PostgreSQL 17.11(전용 컨테이너, `--cpus=2`), JDBC 42.7.7.
- 자원: `doc(id, body, version)`. GET은 `ETag: "<version>"`. PUT 모드: `none`(조건 무시) / `check-then-write`(SELECT로 비교 → 300ms(예시) 처리 → UPDATE) / `atomic`(`UPDATE … WHERE id=? AND version=?`).

```java
// Etag11.java 핵심 — atomic 모드
if (im == null) → 428 "If-Match required"
if (im.startsWith("W/") || !im.matches("\"\\d+\"")) → 412      // 강한 비교: 약한 태그는 불일치
UPDATE doc SET body=?, version=version+1 WHERE id=? AND version=? RETURNING version
  → 행이 있으면 200 + 새 ETag, 없으면 412
// If-None-Match: * → INSERT … ON CONFLICT DO NOTHING, 0행이면 412
```

(실험, JDK 21.0.12 + PostgreSQL 17.11, 2026-10-04 — L1·L2·L3·L5는 전체 실행 4회 모두 같은 결과)

```text
[L1] If-Match 없이 읽고-고치고-통째로 PUT
  둘 다 GET: {"title":"초안","tags":"a"} ETag "1"
  Alice PUT(title 변경): 200
  Bob   PUT(tags 변경):  200
  최종: {"title":"초안","tags":"a,b"}   ← Alice의 제목 변경이 사라짐

[L2] If-Match 필수(서버가 조건을 원자적으로 검사)
  Alice PUT If-Match "1": 200 새 ETag "2"
  Bob   PUT If-Match "1": 412 {"title":"precondition failed","detail":"resource changed; GET again"}
  Bob   PUT (If-Match 없음): 428 {"title":"If-Match required","detail":"GET the resource and send its ETag in If-Match"}
  Bob 다시 GET → 자기 변경을 얹어 PUT If-Match "2": 200
  최종: {"title":"새 제목","tags":"a,b"}

[L3] 약한 ETag를 If-Match에 (강한 비교)
  현재 ETag "3", 보낸 If-Match W/"3" → 412

[L5] If-None-Match: * — 없을 때만 생성
  1차 PUT /docs/new: 201
  2차 PUT /docs/new: 412
```

같은 `If-Match: "1"`을 든 PUT 20개를 동시에 보냈다(L4). 검사 방식만 다르다.

(실험, 같은 환경, check-then-write 처리 시간 300ms 설정으로 7회 실행 중 3회 발췌 — 200 개수는 실행마다 다르다)

```text
[L4] 같은 If-Match "1"로 동시 PUT 20개, 서버 검사 방식 check-then-write → {200=2, 412=18}, 최종 version "3"
[L4] 같은 If-Match "1"로 동시 PUT 20개, 서버 검사 방식 atomic           → {200=1, 412=19}, 최종 version "2"
[L4] 같은 If-Match "1"로 동시 PUT 20개, 서버 검사 방식 check-then-write → {200=14, 412=6}, 최종 version "15"
[L4] 같은 If-Match "1"로 동시 PUT 20개, 서버 검사 방식 atomic           → {200=1, 412=19}, 최종 version "2"
[L4] 같은 If-Match "1"로 동시 PUT 20개, 서버 검사 방식 check-then-write → {200=9, 412=11}, 최종 version "10"
[L4] 같은 If-Match "1"로 동시 PUT 20개, 서버 검사 방식 atomic           → {200=1, 412=19}, 최종 version "2"
```

- 관찰 1 (L1) — 두 PUT 모두 200. 에러 없이 Alice의 제목이 사라졌다.
- 관찰 2 (L2) — 늦은 Bob은 412, 조건 없이 보내면 428. 다시 GET해 자기 변경을 얹자 두 변경이 다 남았다.
- 관찰 3 (L3) — 현재 판과 같은 번호라도 `W/`를 붙이면 412. RFC 9110의 강한 비교 규칙대로다.
- 관찰 4 (L4) — check-then-write는 7회 실행에서 200이 1~14개 나왔다(사실 점검 재실행 4회: 1·4·15·3개 — 1개만 나온 실행도 있어 매번 새는 것은 아니다). 같은 판을 든 요청 여럿이 "검사 통과"한 뒤 차례로 덮어썼다. 처리 시간 50ms 설정에서는 3회 중 1~2개였다. 창이 넓을수록 많이 샌다. atomic은 7회(점검 4회 포함 11회) 모두 정확히 1개.
- 관찰 5 (L5) — `If-None-Match: *` 생성은 두 번째가 412. 클라이언트가 ID를 정하는 생성 API의 중복 방지에 쓴다([05-idempotency-keys](../05-idempotency-keys/2-summary.md) §4).

## 쓰이는 자료구조·알고리즘

- **버전 비교 = compare-and-swap(CAS)** — "현재 값이 기대값이면 새 값으로 바꾼다"를 원자적으로. DB의 `UPDATE … WHERE version = ?`가 그 CAS다. 실패하면 다시 읽고 다시 시도하는 낙관적 동시성 제어(OCC) 루프가 된다. [database/17-occ-and-timestamp-ordering](../../database/17-occ-and-timestamp-ordering/2-summary.md).
- **ETag 생성 방식 둘**
  - 버전 카운터: 쓰기마다 +1. 싸고 확실하다. 같은 내용으로 되돌려도 번호는 오른다.
  - 내용 해시: 표현 바이트의 해시(SHA-256 등). 같은 내용이면 같은 값. 표현이 압축·필드 순서·서버마다 다른 값에 따라 달라지면 쓸데없는 412가 난다.
- **단조 증가 카운터** — 버전은 되돌아가면 안 된다. 되돌아가면 옛 ETag가 다시 "최신"이 된다.

## 적용 — 풀어나가는 법

### 1. 순서

1. **경합 가능한 쓰기를 고른다** — 사람이 화면을 보고 고치는 자원(설정·문서·상품), 여러 시스템이 고치는 자원.
2. **GET·생성·수정 응답에 강한 ETag를 준다** — 버전 컬럼에서 만든다(`"<version>"`). 숫자로 의존하지 않게 문서에는 "불투명 문자열"이라고 쓴다.
3. **PUT·PATCH·DELETE에 `If-Match`를 받는다** — 불일치 412. 필수로 할지 정한다(필수면 없을 때 428, AIP-154는 기본은 허용·필수로 하면 `INVALID_ARGUMENT`).
4. **서버에서 원자적으로 검사한다** — 조건부 UPDATE. 앱에서 읽고 비교하지 않는다.
5. **412 응답을 클라이언트가 처리할 수 있게** — 문제 상세(problem+json)에 "다시 GET하라"를 쓰고, 최신 ETag나 최신 표현을 줄지 정한다.
6. **생성은 `If-None-Match: *`** — 클라이언트가 ID를 정하는 PUT 생성에서 중복을 막는다.

### 2. 클라이언트 코드 모양 (JDK HttpClient)

```java
// 읽고-고치고-쓰기를 412면 처음부터 다시. 자동으로 다시 할 수 없는 충돌은 사용자에게 보인다
for (int attempt = 1; attempt <= 3; attempt++) {
    HttpResponse<String> cur = http.send(GET(uri), ofString());
    String etag = cur.headers().firstValue("ETag").orElseThrow();
    Doc doc = mapper.readValue(cur.body(), Doc.class);
    Doc changed = doc.withTags(doc.tags().plus("b"));          // 내 변경을 "최신 판 위에" 얹는다
    HttpResponse<String> r = http.send(HttpRequest.newBuilder(uri)
            .header("If-Match", etag)
            .PUT(BodyPublishers.ofString(mapper.writeValueAsString(changed))).build(), ofString());
    if (r.statusCode() != 412) return r;                       // 200·4xx는 끝
}
throw new ConflictException("다른 사람이 계속 고치고 있습니다. 새로 고친 뒤 다시 시도하세요");
```

- 자동 재적용은 "내 변경이 최신 판 위에서도 의미가 같을 때"만 한다(태그 추가처럼). 같은 필드를 둘이 다르게 고쳤다면 사용자에게 충돌을 보여 준다.
- `PATCH`(부분 수정)를 써도 필드 단위 덮어쓰기는 막아 주지 않는다. 같은 필드를 고치는 경합이 있으면 `If-Match`를 함께 쓴다.

### 3. 진단

```bash
curl -si https://api.example.com/docs/d1 | grep -i etag          # ETag: "7"
curl -si -X PUT https://api.example.com/docs/d1 \
     -H 'If-Match: "6"' -H 'Content-Type: application/json' -d '{...}'
# HTTP/1.1 412 Precondition Failed
```

- 지표: 412 비율(경합 정도), 428 비율(구 클라이언트), 같은 자원 연속 412(재시도 루프 폭주).
- 로그: 412 응답에 기대 ETag와 현재 ETag를 함께 남긴다.

## 장애 시나리오와 대처

### 1. 동시 편집 → lost update (⚠)

- **현상**: "분명 저장했는데 내 수정이 없어졌다"는 문의. 재현이 어렵다.
- **보이는 형태**: 같은 자원에 짧은 간격으로 PUT 두 건, 둘 다 200. 감사 로그를 보면 앞 변경이 뒤 변경에 덮였다(실험 L1).
- **원인**: 전체 교체 PUT에 조건이 없다. 또는 ETag를 주지만 서버가 `If-Match`를 무시한다.
- **대처**: `If-Match` 필수 + 412(실험 L2), 구 클라이언트는 428로 안내. 감사 로그에 판 번호를 남긴다.

### 2. 412 처리 누락 (⚠)

- **현상**: 저장 버튼을 누르면 "알 수 없는 오류". 또는 앱이 412에 같은 요청을 무한 재시도한다.
- **보이는 형태**: 클라이언트 에러 로그에 412. 같은 자원·같은 ETag의 PUT이 초당 여러 번.
- **원인**: 클라이언트가 412를 일반 4xx로 처리하거나, 다시 GET 하지 않고 같은 ETag로 재시도한다. 같은 ETag로는 영원히 412다.
- **대처**: 412 → 다시 GET → 재적용 또는 사용자에게 충돌 화면. 재시도 상한. 서버는 412 본문에 "다시 GET하라"를 쓴다.

### 3. 약한 ETag로 조건부 쓰기 → 412만 나온다

- **현상**: 조건부 쓰기를 붙였더니 PUT이 전부 412다.
- **보이는 형태**: GET 응답 `ETag: W/"…"`, PUT `If-Match: W/"…"` → 412(실험 L3).
- **원인**: If-Match는 강한 비교라 약한 ETag는 무엇과도 일치하지 않는다(RFC 9110 §8.8.3.2·§13.1.1). 앞단 프록시가 응답을 압축하면서 ETag를 약하게 바꾸기도 한다. nginx는 1.7.3부터 응답을 변형할 때 강한 ETag를 약한 것으로 바꾼다(nginx CHANGES 1.7.3).
- **대처**: 쓰기용 자원에는 버전 기반 강한 ETag를 준다. 프록시가 ETag를 바꾸는지 `curl -i`로 원 서버와 앞단 응답을 비교한다.

### 4. If-Match를 받는데도 덮어쓰기가 생긴다

- **현상**: 412가 잘 나오는데도 가끔 동시 저장에서 변경이 사라진다.
- **보이는 형태**: 같은 If-Match 값을 든 PUT 둘이 모두 200(실험 L4 check-then-write: 집필 7회 중 200이 1~14개, 점검 4회 1~15개).
- **원인**: 서버가 ETag를 읽어 비교한 뒤 따로 UPDATE한다. 그 사이에 다른 요청이 통과한다.
- **대처**: `UPDATE … WHERE version = ?` 한 문장으로(실험 atomic: 7회 모두 1개). JPA라면 `@Version`([database/17](../../database/17-occ-and-timestamp-ordering/2-summary.md)).

### 5. 서버마다 다른 ETag → 쓸데없는 412

- **현상**: 로드 밸런서 뒤 여러 인스턴스 중 어떤 곳을 거치면 412가 난다.
- **보이는 형태**: 같은 자원의 GET ETag가 요청마다 다르다.
- **원인**: ETag를 인스턴스별 값(메모리 해시, 직렬화 순서, 서버 시각)으로 만들었다. 캐시 검증 쪽 같은 문제는 [network/34-http-caching](../../network/34-http-caching/2-summary.md) 장애 5에 있다.
- **대처**: DB의 버전 컬럼처럼 공유 저장소의 값으로 만든다.

## 핵심 문장

- 요청과 요청 사이(사람이 화면을 보는 시간)는 DB 트랜잭션으로 못 지킨다. 그 구간의 lost update는 `ETag` + `If-Match` 계약으로 막는다.
- If-Match가 거짓이면 서버는 실행하지 않고 412를 준다. 조건 없는 쓰기를 거절하려면 428이다.
- If-Match는 강한 비교다. 약한 ETag(`W/`)로는 조건부 쓰기가 성립하지 않는다.
- 서버 안에서 검사와 쓰기를 따로 하면 같은 판을 든 요청 여럿이 통과한다. 실험에서 check-then-write는 20개 중 1~15개가 성공했고(실행마다 다르다) 조건부 UPDATE는 매번 1개였다.
- RFC 9110은 412, AIP-154는 `ABORTED`(HTTP 409), Kubernetes는 409를 쓴다. 숫자는 달라도 클라이언트 할 일은 "다시 읽고 다시 적용"이다.

## 관련 주제·근거

- 선행
  - [07-versioning-and-compatibility](../07-versioning-and-compatibility/2-summary.md) — 커리큘럼 선행
  - [database/17-occ-and-timestamp-ordering](../../database/17-occ-and-timestamp-ordering/2-summary.md) — 버전 컬럼·OCC·`@Version`
  - [network/34-http-caching](../../network/34-http-caching/2-summary.md) — ETag·`If-None-Match`·304(읽기 쪽 검증)
- 후속·연결
  - [database/18-app-level-concurrency-patterns](../../database/18-app-level-concurrency-patterns/2-summary.md) — 조건부 UPDATE·`FOR UPDATE`
  - [database/52-offline-concurrency-patterns](../../database/52-offline-concurrency-patterns/2-summary.md) — 요청 사이의 낙관적·비관적 오프라인 락
  - [05-idempotency-keys](../05-idempotency-keys/2-summary.md) — `If-None-Match: *`로 없을 때만 생성, 재시도 안전
  - [03-status-codes-for-apis](../03-status-codes-for-apis/2-summary.md) · [04-error-format-problem-details](../04-error-format-problem-details/2-summary.md) — 412·428·409 선택과 응답 본문
  - 사례 [22-case-order-point](../22-case-order-point/2-summary.md)(읽고-계산해서-쓰지 마라) · [24-case-stock-deduct](../24-case-stock-deduct/2-summary.md)
- 근거
  - RFC 9110 §8.8.3 ETag, §8.8.3.2 강한·약한 비교(표 3), §13.1.1 If-Match(강한 비교 MUST, 거짓이면 실행 MUST NOT, 412 또는 이미 적용 시 2xx MAY, lost update), §13.1.2 If-None-Match(약한 비교, `*`), §13.2.1 평가 시점, §13.2.2 평가 순서, §15.5.13 412 <https://www.rfc-editor.org/rfc/rfc9110#section-13>
  - RFC 6585 §3 428 Precondition Required <https://www.rfc-editor.org/rfc/rfc6585#section-3>
  - Google AIP-154 Resource freshness validation(`etag` 필드, 강한·약한, 불일치 `ABORTED`, 미전송 시 허용(should)·필수로 하면 `INVALID_ARGUMENT`(may)) <https://google.aip.dev/154>
  - googleapis `google/rpc/code.proto` — `ABORTED` HTTP 409, `FAILED_PRECONDITION` 400, test-and-set 실패 시 ABORTED 지침 <https://github.com/googleapis/googleapis/blob/master/google/rpc/code.proto>
  - Kubernetes "API Concepts" — resourceVersion이 오래되면 409 Conflict <https://kubernetes.io/docs/reference/using-api/api-concepts/>
  - nginx CHANGES 1.7.3(2014-07-08) — 응답 변형 시 강한 ETag를 약하게 <https://nginx.org/en/CHANGES>
- 실험 목록
  - L1~L5: If-Match 없음 lost update / 412·428·재적용 / 약한 ETag 412 / 동시 20 PUT check-then-write vs atomic / `If-None-Match: *` — `Etag11.java`, JDK 21.0.12 + PostgreSQL 17.11 전용 컨테이너, L4는 7회(처리 시간 300ms) + 3회(50ms), 나머지는 4회 / 사실 점검 재실행 4회(300ms): L1·L2·L3·L5 같음, L4 check-then-write 200=1·4·15·3, atomic 매번 1
