# api-design/02-rest-and-resource-modeling — REST와 자원 모델링: 자원·표현·균일 인터페이스·성숙도 모델 — 정리 (힌트)

## 해결하는 문제

HTTP를 "함수 호출을 실어 나르는 통로"로만 쓰면, 클라이언트와 서버 사이의 중간자들이 아무것도 도와주지 못한다.

```text
  RPC식 (모든 것을 POST 한 곳으로)               자원식 (메서드가 의미를 말함)
  POST /api  {"op":"getProduct","id":1}       GET    /products/1
  POST /api  {"op":"deleteProduct","id":1}    DELETE /products/1
  POST /api  {"op":"createOrder",...}         POST   /orders

  캐시:   본문을 열어 봐야 조회인지 앎 → 안 함      GET이면 캐시 가능, 나머지는 통과
  재시도:  전부 POST → 안전한지 모름 → 안 함        GET·PUT·DELETE는 멱등, 재시도 판단 가능
  크롤러:  -                                     GET은 안전 → 따라가도 됨
  모니터링: 엔드포인트 하나에 전부 섞임              경로·메서드별로 지표가 갈림
```

- *중간자*: 클라이언트와 서버 사이의 캐시·프록시·게이트웨이·로드 밸런서·HTTP 클라이언트 라이브러리. 메시지 본문의 의미는 모르고, 메서드·URI·헤더·상태 코드만 보고 판단한다.
- REST의 핵심은 이 중간자들이 판단할 수 있게 **메시지가 스스로를 설명하게 하는 것**이다.

쉬운 예: 우체국 봉투다.
- 봉투 겉면에 "등기", "반송 불가", "파손 주의"가 적혀 있으면, 우체국 직원은 내용물을 열지 않고도 처리 방법을 안다.
- 모든 편지를 "일반"으로 보내고 안에 "사실 등기로 해 주세요"라고 쓰면 아무도 그렇게 처리해 주지 않는다.

똑같은 구조다.\
HTTP 메서드·상태 코드·캐시 헤더가 봉투 겉면이다.

실무 예:
- (예시) 상품 조회를 `POST /getProduct`로 만들면 CDN·nginx 캐시가 기본 설정에서 적중하지 않아, 조회가 원 서버로 그대로 간다(아래 실험 A).
- (예시) 결제 승인을 `GET /approve?id=…`로 만들면, 메신저의 링크 미리보기가 URL을 GET으로 여는 순간 승인이 실행될 수 있다. RFC 9110 §9.2.1이 경고하는 상황이다.

## 동작·원리

### 1. Fielding의 REST — 제약을 하나씩 더해 만든 스타일

Fielding 박사논문(2000) 5장은 아무 제약 없는 상태("Null style")에서 제약을 차례로 더해 REST를 유도한다.

```text
  Null style
    + 클라이언트-서버   관심사 분리, 양쪽이 따로 진화
    + 무상태            요청 하나에 이해에 필요한 정보가 다 있다 (세션 상태는 클라이언트에)
    + 캐시              응답에 "캐시 가능/불가" 표시
    + 균일 인터페이스    ← REST를 다른 스타일과 가르는 중심 특징
    + 계층화 시스템      각 구성요소는 바로 옆 계층만 본다 (프록시·게이트웨이 끼울 수 있음)
    + 주문형 코드(선택)  스크립트를 내려받아 클라이언트 기능 확장
  = REST
```

제약마다 얻는 것과 잃는 것(5.1절, 저자의 분석):

| 제약 | 얻는 것 | 잃는 것 |
|---|---|---|
| 무상태 | 가시성(요청 하나만 보면 됨), 부분 실패 복구 쉬움, 확장성 | 요청마다 반복 데이터 → 네트워크 효율 저하 |
| 캐시 | 일부 상호작용 제거 → 지연·부하 감소 | 오래된 데이터로 신뢰성 저하 가능 |
| 균일 인터페이스 | 단순성, 상호작용 가시성, 구현과 서비스 분리 → 독립 진화 | 표준 형식이라 앱별 최적화보다 효율 낮음 |
| 계층화 | 복잡도 상한, 공유 캐시·부하 분산·보안 정책 삽입 | 처리 지연 증가 |

- 균일 인터페이스는 다시 네 제약으로 이뤄진다(5.1.5절).
  - *자원 식별*: 자원을 식별자(URI)로 가리킨다.
  - *표현을 통한 자원 조작*: 자원 자체가 아니라 그 표현(JSON 문서 등)을 주고받는다.
  - *자기 서술 메시지*: 메시지만 보고 처리 방법을 알 수 있다(메서드·미디어 타입·캐시 지시).
  - *애플리케이션 상태 엔진으로서의 하이퍼미디어(HATEOAS)*: 다음에 할 수 있는 일을 응답 안의 링크로 안내한다.

### 2. 자원과 표현

```text
  자원 "오늘의 서울 날씨"  ──(시점 t에)──>  값 {맑음, 23도}       ← 자원은 시간에 따라 바뀌는 대응
         │
         ├── 표현 1: application/json   {"sky":"clear","temp":23}
         └── 표현 2: text/html          <p>맑음, 23도</p>

  같은 순간 같은 값을 가리켜도 "저자가 선호하는 판 논문"과 "학회 X 게재판 논문"은 다른 자원이다
```

- *자원*: 이름 붙일 수 있는 정보면 무엇이든 자원이 된다. 문서·이미지·"오늘의 날씨" 같은 시간적 서비스·다른 자원의 모음까지(5.2.1.1절).
  - 정확히는 시점 t마다 값 집합을 돌려주는 대응 함수 MR(t)다. 고정돼야 하는 것은 값이 아니라 **대응의 의미**다.
- *표현*: 바이트 열 + 그것을 설명하는 메타데이터(미디어 타입 등)(5.2.1.2절).
- 설계 함의: 자원은 DB 테이블이 아니다. Google AIP-121은 "API가 DB 스키마와 똑같은 것은 안티패턴"이라고 적는다(회사 지침). 테이블을 그대로 노출하면 스키마 변경이 곧 API 변경이 된다(01의 계약 문제).

### 3. Richardson 성숙도 모델(RMM)

Fowler(2010, "Richardson Maturity Model")가 Leonard Richardson의 모델을 설명한 글이다.

```text
  Level 3  하이퍼미디어 컨트롤   응답에 "다음에 할 수 있는 일" 링크
  Level 2  HTTP 메서드·상태 코드  GET은 안전, 실패는 non-2xx, 생성은 201 + Location
  Level 1  자원                 /doctors/mjones, /slots/1234 처럼 개별 자원에 요청
  Level 0  HTTP를 터널로         POST /appointmentService 한 곳에 모든 요청
```

- Level 2에서 Fowler가 강조한 것(글의 주장)
  - GET이 안전하다는 정의 덕분에 경로상의 누구든 캐시를 쓸 수 있다.
  - "200을 주고 본문에 에러를 넣는" 대신 non-2xx를 쓴다(03).
  - 웹이 실제로 증명한 핵심은 "안전한 연산과 아닌 연산의 강한 분리 + 상태 코드로 에러 종류 전달"이라고 적는다.
- RMM은 REST의 정의가 아니다. Fowler 본인이 그렇게 적고, Fielding은 Level 3(하이퍼미디어)이 REST의 전제 조건이라고 분명히 했다고 덧붙인다.
  - Fielding 블로그(2008, "REST APIs must be hypertext-driven"): 하이퍼텍스트로 애플리케이션 상태가 구동되지 않으면 REST API라 부를 수 없다고 적는다.
- 그래서 용어를 나눠 쓴다.
  - **Fielding의 REST**: 하이퍼미디어까지 포함한 아키텍처 스타일.
  - **업계의 "REST API"**: 대체로 RMM Level 2(자원 + HTTP 메서드·상태 코드)를 뜻하는 관용 표현.
- 이 노트의 설계 판단 대부분(캐시·재시도·모니터링)은 Level 2에서 이미 얻는다. Level 3의 이득(클라이언트가 URL 구조를 하드코딩하지 않음)은 클라이언트가 링크를 따라가도록 만들어졌을 때만 생긴다.

### 4. 자원 모델링 — 명사·계층·표준 메서드

Google AIP-121이 권하는 설계 순서(회사 지침): 자원(명사) → 관계·계층 → 각 자원의 스키마 → 메서드(가능한 한 표준 동사).

```text
  publishers/{publisher}                       ← 자원
  publishers/{publisher}/books                 ← 컬렉션 (같은 타입 자원의 모음)
  publishers/{publisher}/books/{book}          ← 하위 자원

  표준 메서드          HTTP 매핑 (AIP-131~135)
  Get     GET    /v1/publishers/p1/books/b1
  List    GET    /v1/publishers/p1/books
  Create  POST   /v1/publishers/p1/books
  Update  PATCH  /v1/publishers/p1/books/b1
  Delete  DELETE /v1/publishers/p1/books/b1

  커스텀 메서드 (AIP-136)
  Archive POST   /v1/publishers/p1/books/b1:archive
```

- AIP-121(회사 지침)
  - 자원은 최소 Get을 지원해야 한다. 변경 뒤 상태를 확인할 수 있어야 하기 때문이다.
  - 표준 메서드를 커스텀 메서드보다 우선한다.
  - 자원 관계는 방향 비순환 그래프로 표현할 수 있어야 하고, 부모는 하나다.
- AIP-122: 컬렉션 식별자는 복수형·camelCase 영어 단어.
- "동사형 URL 금지"는 단순화된 규칙이다. AIP-136은 표준 메서드로 표현하기 어려운 동작에 `POST …:archive` 같은 커스텀 메서드를 허용한다. 조건이 있다.
  - 데이터·자원 상태를 가져오는 메서드는 GET이어야 한다(must). 부작용이 있으면 POST여야 한다(must).
  - 조회라도 요청 내용이 URL 길이 한도를 넘을 수 있어 본문이 필요하면 POST를 쓸 수 있다(may).
- 동작을 자원으로 바꾸는 방법도 있다. "환불하다"를 `POST /payments/{id}/refunds`(환불 자원 생성)로 만들면 환불 이력 조회(`GET …/refunds`)가 자연스럽게 생긴다.

### 5. 무상태 — 세션 상태는 어디에

- Fielding 5.1.3: 요청마다 이해에 필요한 정보를 다 담고, 서버에 저장된 문맥을 쓰지 않는다. 세션 상태는 클라이언트가 가진다.
- AIP-121도 요청마다 다른 요청과 독립이어야 하고, 자원은 "특정 순서의 요청을 거쳐야 닿는" 방식이 아니라 직접 주소로 접근할 수 있어야 한다고 적는다.
- 무상태여도 서버에 **자원 상태**(주문·잔액)는 저장한다. 금지되는 것은 "이 연결·이 세션에서 전에 무엇을 했는가"에 기대는 **애플리케이션 상태**다.

### 실험 A: 같은 조회를 GET과 POST로 — 공유 캐시

같은 상품 조회를 두 경로로 만들고, 두 응답 모두 `Cache-Control: public, max-age=60`을 준다. 앞에 nginx `proxy_cache`를 둔다(`proxy_cache_methods`는 기본값).

```nginx
proxy_cache_path /tmp/cache keys_zone=api:1m;
location / {
    proxy_pass http://sn-ad-w01-backend:8080;
    proxy_cache api;            # proxy_cache_methods 기본값(GET HEAD) 그대로
    add_header X-Cache-Status $upstream_cache_status always;
}
```

(실험, nginx 1.31.6 alpine + JDK 21 `com.sun.net.httpserver` 백엔드, 일회용 docker 네트워크, 2026-10-04)

```text
GET  /products/1  #1  X-Cache-Status=MISS
GET  /products/1  #2  X-Cache-Status=HIT
GET  /products/1  #3  X-Cache-Status=HIT
POST /getProduct  #1  X-Cache-Status=
POST /getProduct  #2  X-Cache-Status=
POST /getProduct  #3  X-Cache-Status=
백엔드 도착 수: {GET /products/1=1, POST /getProduct=3}
```

- GET은 첫 요청만 백엔드에 갔다. POST는 세 번 다 갔다. 캐시 상태 변수도 비었다 — 캐시 경로를 아예 타지 않았다.
- 서버가 캐시 헤더를 똑같이 줘도 소용없다. nginx 문서상 `proxy_cache_methods` 기본값은 `GET HEAD`다.
- RFC 9110 기준으로 POST 응답은 명시적 신선도 + 같은 `Content-Location`이 있을 때만 캐시할 수 있고, 그것도 이후 GET·HEAD에 쓰는 용도다(세부는 network/33·34).

### 실험 B: 끊긴 keep-alive 연결 위의 자동 재시도 — GET vs POST

서버는 연결마다 첫 요청에만 응답하고, 두 번째 요청은 읽은 뒤 응답 없이 연결을 닫는다. 서버가 막 닫은 keep-alive 연결을 클라이언트가 재사용하는 상황이다.

(실험, JDK 21.0.12 temurin `java.net.http.HttpClient`, HTTP/1.1, 기본 설정, 2026-10-04)

```text
== GET /products/1  => 클라이언트: 성공 200
   서버 도착: conn1 #1 GET /warmup HTTP/1.1
   서버 도착: conn1 #2 GET /products/1 HTTP/1.1  -> 응답 없이 닫음
   서버 도착: conn2 #1 GET /products/1 HTTP/1.1
   /products/1 도착 횟수 = 2
== POST /getProduct  => 클라이언트: 실패 IOException: HTTP/1.1 header parser received no bytes
   서버 도착: conn3 #1 GET /warmup HTTP/1.1
   서버 도착: conn3 #2 POST /getProduct HTTP/1.1  -> 응답 없이 닫음
   /getProduct 도착 횟수 = 1
== POST /orders  => 클라이언트: 실패 IOException: HTTP/1.1 header parser received no bytes
   서버 도착: conn4 #1 GET /warmup HTTP/1.1
   서버 도착: conn4 #2 POST /orders HTTP/1.1  -> 응답 없이 닫음
   /orders 도착 횟수 = 1
```

같은 코드를 `-Djdk.httpclient.enableAllMethodRetry=true`로 돌리면(발췌 — GET 결과는 위와 같고, `/warmup` 줄은 뺐다):

```text
== POST /getProduct  => 클라이언트: 성공 200
   서버 도착: conn3 #2 POST /getProduct HTTP/1.1  -> 응답 없이 닫음
   서버 도착: conn4 #1 POST /getProduct HTTP/1.1
   /getProduct 도착 횟수 = 2
== POST /orders  => 클라이언트: 성공 200
   서버 도착: conn5 #2 POST /orders HTTP/1.1  -> 응답 없이 닫음
   서버 도착: conn6 #1 POST /orders HTTP/1.1
   /orders 도착 횟수 = 2
```

- 기본 설정에서 JDK 클라이언트는 GET만 새 연결로 한 번 더 보냈다. 사용자는 실패를 못 봤다.
- 조회인데 POST로 만든 `/getProduct`는 재시도되지 않아 사용자에게 오류가 났다. 클라이언트는 `/getProduct`가 조회인지 `/orders`(주문 생성)인지 구별할 방법이 없다.
- 전부 재시도하도록 켜면 이번엔 `/orders`도 서버에 **두 번 도착**했다. 서버가 첫 요청을 처리했다면 주문이 두 건 생긴다.
- 근거(소스): jdk21u `MultiExchange.java` — `isIdempotentRequest`는 `"GET", "HEAD"`만 참이다. `enableAllMethodRetry` 속성이 켜지면 메서드와 무관하게 재시도한다. 재시도는 한 번(`retriedOnce`)이다.
- 계층을 나눠 보면
  - 프로토콜(RFC 9110 §9.2.2): PUT·DELETE·안전 메서드는 멱등이다. 클라이언트는 비멱등 요청을 자동 재시도하지 않아야 한다(SHOULD NOT).
  - 라이브러리 기본값(JDK 21): 이미 보냈을 수 있는 요청이 끊긴 연결에서 실패하면 RFC보다 좁게 GET·HEAD만 자동 재시도한다. PUT·DELETE도 이 경우 재시도하지 않는다.
    - 예외 두 가지는 메서드와 무관하게 한 번 다시 보낸다. 연결 수립 실패(`ConnectException`, `jdk.httpclient.disableRetryConnect`로 끔)와, 서버가 "처리하지 않았다"고 알린 요청(HTTP/2 GOAWAY·REFUSED_STREAM, `isUnprocessedByPeer`)이다(jdk21u `MultiExchange.getExceptionalCF`). 둘 다 서버가 요청을 처리하지 않은 경우라 RFC와 충돌하지 않는다.
  - 애플리케이션: POST를 안전하게 재시도하려면 멱등 키(05)를 서버가 처리해야 한다.

### 본문이 필요한 조회 — QUERY 메서드

- 검색 조건이 길어 URL에 담기 어려우면 POST로 조회하고 싶어진다. 그러면 위 두 실험의 손해를 그대로 본다.
- RFC 10008(2026-06, "The HTTP QUERY Method")은 본문을 가진 **안전하고 멱등인** 조회 메서드를 정의한다. 캐시 키에 요청 본문을 포함해야 한다(MUST, §2.7).
- 새 표준이라 프록시·CDN·클라이언트 라이브러리 지원은 제품·버전별로 확인해야 한다. 예로 위 jdk21u 소스의 자동 재시도 목록에는 QUERY가 없다.
- 또 다른 대안(일반적인 설계 기법 — AIP-136의 규정은 아니다): 자주 쓰는 검색을 자원으로 저장(`POST /savedSearches` → `GET /savedSearches/{id}/results`)하면 결과 조회는 GET이 된다.

## 쓰이는 자료구조·알고리즘

- **자원 계층 = 트리**: `publishers/p1/books/b1`처럼 부모가 하나인 계층이다. AIP-121은 관계를 방향 비순환 그래프로, 부모-자식은 하나의 정식 부모로 제한한다. 순환이 있으면 생성·삭제 순서가 꼬인다(AIP-121의 A↔B 예).
- **경로 라우팅 = 트라이**: 서버 프레임워크는 경로 세그먼트를 트라이(또는 정렬된 패턴 목록)로 매칭해 핸들러를 찾는다. `{id}` 같은 변수 세그먼트는 와일드카드 간선이다 — [data-structure/09-trie](../../data-structure/09-trie/2-summary.md).
- **캐시 = (메서드, URI) 키의 해시 맵 + 만료 시각**: RFC 9111이 정한 최소 캐시 키가 메서드와 대상 URI다. POST 조회는 본문이 키에 없어 그대로는 캐시할 수 없다 — [network/34-http-caching](../../network/34-http-caching/2-summary.md).
- **재시도 판정 = 메서드 화이트리스트**: JDK 클라이언트의 `switch (method) { case "GET", "HEAD" -> true; }`. 메서드 의미가 맞아야 이 단순한 표가 올바르게 동작한다.

## 적용 — 풀어나가는 법

### 1. 순서

1. **명사를 뽑는다.** 화면·유스케이스에서 "다루는 대상"을 적는다(주문, 주문 항목, 결제, 환불).
2. **계층을 정한다.** 소유 관계(부모 하나)만 경로에 넣는다. 참조 관계는 필드(`customerId`)로 둔다.
3. **표현 스키마를 정한다.** DB 테이블을 그대로 옮기지 않는다. 클라이언트가 필요한 의미 단위로 묶는다.
4. **메서드 매핑 표를 만든다.** 조회 = GET(안전), 전체 교체 = PUT, 부분 수정 = PATCH, 생성 = POST(201 + `Location`), 삭제 = DELETE.
5. **표준 메서드로 안 되는 동작만 커스텀 메서드로.** 부작용이 있으면 POST, 순수 조회면 GET. 반복 조회될 동작이면 자원으로 바꾸는 쪽을 먼저 검토한다.
6. **중간자 동작을 확인한다.** 캐시(`curl -i`로 `Cache-Control`·캐시 상태 헤더), 클라이언트·게이트웨이의 재시도 메서드 목록.

### 2. 코드 (Spring MVC)

```java
@RestController
@RequestMapping("/v1/orders")
class OrderController {
    @GetMapping("/{id}")                          // 안전·멱등 → 캐시·자동 재시도 가능
    ResponseEntity<OrderDto> get(@PathVariable String id) {
        return ResponseEntity.ok()
            .cacheControl(CacheControl.maxAge(Duration.ofSeconds(30)).cachePrivate())
            .body(service.get(id));
    }

    @PostMapping                                  // 생성: 201 + Location (RFC 9110 §15.3.2)
    ResponseEntity<OrderDto> create(@RequestBody CreateOrder req) {
        OrderDto o = service.create(req);
        return ResponseEntity.created(URI.create("/v1/orders/" + o.id())).body(o);
    }

    @PostMapping("/{id}/cancellations")           // 동작을 자원으로: 취소 이력이 생긴다
    ResponseEntity<CancellationDto> cancel(@PathVariable String id) { ... }
}
```

- 주문 조회는 사용자별 데이터라 `private`로 둔다. 공유 캐시에 남으면 다른 사용자에게 나갈 수 있다(network/34 장애 1).

### 3. 진단

```bash
# 메서드·경로별 요청 분포 — POST 비율이 비정상적으로 높으면 조회가 POST로 숨어 있을 수 있다
awk '{print $6, $7}' access.log | sed 's/?.*//' | sort | uniq -c | sort -rn | head
# 캐시 적중 여부 확인
curl -s -o /dev/null -D - https://api.example.com/v1/products/1 | grep -i -E 'cache-control|x-cache|age'
```

## 장애 시나리오와 대처

### 1. 동사형 URL·모든 것을 POST로 → 캐시·재시도 의미 상실 (⚠ 커리큘럼)

- **현상**: 트래픽이 늘자 원 서버 CPU가 포화된다. CDN·nginx 캐시 적중률이 0에 가깝다. 네트워크가 흔들릴 때 조회 화면이 자주 실패한다.
- **보이는 형태**: 캐시 상태 헤더가 비어 있거나 `MISS`만 있다. 접근 로그에 `POST /getXxx`가 대부분이다. 클라이언트 로그에 `IOException`(연결 끊김)이 재시도 없이 바로 남는다.
- **원인**: 조회를 POST로 만들었다. 중간자는 POST를 캐시하지 않고(nginx 기본 `proxy_cache_methods GET HEAD`), 라이브러리는 끊긴 연결 위의 POST를 자동 재시도하지 않는다(JDK 21: 이 경우 GET·HEAD만). 실험 A·B와 같다.
- **대처**: 조회는 GET으로 옮긴다. URL이 너무 길면 저장된 검색 자원이나 QUERY 메서드(RFC 10008, 지원 여부 확인)를 쓴다. 이전 기간에는 두 경로를 함께 두고 사용량을 보며 폐기한다(07).

### 2. GET에 부작용 → 링크 미리보기·크롤러가 동작을 실행

- **현상**: 아무도 누르지 않은 "승인" 처리가 생긴다. 시각은 메일·메신저 발송 직후다.
- **보이는 형태**: 승인 로그의 User-Agent가 링크 미리보기 봇·보안 스캐너다.
- **원인**: `GET /approve?id=…`처럼 안전 메서드에 상태 변경을 걸었다. RFC 9110 §9.2.1은 자동화된 프로세스(링크 점검·프리페치·검색 색인)가 GET을 마음대로 호출할 수 있게 하려고 안전 메서드를 구분한다. URI 파라미터로 위험한 동작을 고르는 자원이라면 안전 메서드 요청에서는 그 동작을 막아야 한다(MUST).
- **대처**: 상태 변경은 POST(또는 PUT·PATCH·DELETE)로 옮긴다. 메일 링크는 확인 화면(GET)으로 보내고, 그 화면에서 POST를 보낸다.

### 3. 비멱등 요청 자동 재시도 → 주문 중복

- **현상**: 네트워크가 불안정한 날 같은 주문이 몇 초 간격으로 두 건 생긴다.
- **보이는 형태**: 서버 로그에 같은 본문의 POST가 두 번, 첫 번째는 응답 기록이 없거나 연결 종료로 끝났다.
- **원인**: 클라이언트·게이트웨이가 모든 메서드를 재시도하도록 설정됐다(JDK `enableAllMethodRetry`, 실험 B의 두 번째 결과). 서버는 첫 요청을 이미 처리했다.
- **대처**: 비멱등 메서드 자동 재시도를 끈다. 재시도가 필요한 생성 요청은 멱등 키(05, [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md))로 서버가 중복을 걸러낸다.

### 4. DB 스키마를 그대로 노출 → 테이블 변경이 API 파손

- **현상**: 컬럼 이름 정리(마이그레이션) 뒤 외부 클라이언트가 깨진다.
- **보이는 형태**: 응답 필드 이름이 바뀐 배포 직후 클라이언트 오류 급증.
- **원인**: 자원 표현을 엔티티 직렬화로 만들었다. AIP-121이 안티패턴이라 부르는 "DB 스키마와 같은 API"다.
- **대처**: API 표현용 DTO를 따로 둔다. 테이블 변경과 API 변경의 수명을 분리한다(01의 계약).

### 5. 서버 세션에 기대는 흐름 → 확장·복구가 어렵다

- **현상**: 인스턴스를 늘렸더니 "다음 단계" 요청이 간헐적으로 실패한다.
- **보이는 형태**: 같은 사용자의 요청이 다른 인스턴스로 가면 400·세션 없음 오류. 로드 밸런서에 고정 세션(sticky session)을 켜야 동작한다.
- **원인**: 단계형 흐름의 중간 상태를 서버 메모리 세션에 뒀다. 무상태 제약(Fielding 5.1.3)을 어겼다.
- **대처**: 중간 상태를 자원으로 만든다(`POST /checkouts` → `PATCH /checkouts/{id}`). 그러면 어느 인스턴스든 처리할 수 있고, 중간 실패 뒤 이어서 진행할 수 있다.

## 핵심 문장

- REST의 이득은 메시지가 스스로를 설명해, 본문을 모르는 중간자(캐시·프록시·라이브러리)가 메서드만 보고 캐시·재시도를 판단하게 하는 데서 나온다.
- 조회를 POST로 만들면 실험에서 캐시 적중이 0이 됐고(nginx 기본 `GET HEAD`만 캐시), 끊긴 연결에서 자동 재시도도 일어나지 않았다(JDK 21: 이 경우 GET·HEAD만 — 연결 수립 실패·서버가 처리 안 했다고 알린 요청은 예외).
- 자원은 DB 테이블이 아니라 이름 붙일 수 있는 개념의 시간에 따른 대응이며, 고정할 것은 값이 아니라 의미다(Fielding 5.2.1.1).
- 업계의 "REST API"는 대체로 RMM Level 2를 뜻하고, Fielding의 REST는 하이퍼미디어(Level 3)까지 요구한다 — 둘을 구분해 말한다.
- "동사형 URL 금지"는 단순화다. AIP-136처럼 커스텀 메서드를 허용하되, 조회면 GET·부작용이면 POST라는 메서드 의미는 지킨다.

## 관련 주제·근거

- 선행
  - [01-api-as-contract](../01-api-as-contract/2-summary.md) — 계약과 관찰 가능한 동작
  - [network/33-http-semantics](../../network/33-http-semantics/2-summary.md) — 안전·멱등·캐시 가능 메서드 표, 재시도 규칙
- 후속(api-design)
  - [03-status-codes-for-apis](../03-status-codes-for-apis/2-summary.md) — Level 2의 나머지 절반: 상태 코드
  - [05-idempotency-keys](../05-idempotency-keys/2-summary.md) · [06-pagination](../06-pagination/2-summary.md) · [11-concurrency-control-in-apis](../11-concurrency-control-in-apis/2-summary.md) · [12-filtering-sorting-search](../12-filtering-sorting-search/2-summary.md) · [18-api-style-selection](../18-api-style-selection/2-summary.md)
  - 사례: [22-case-order-point](../22-case-order-point/2-summary.md)(주문 자원·포인트 차감), [27-case-refund](../27-case-refund/2-summary.md)(`POST /orders/{order_id}/refunds` — 환불을 하위 자원으로)
- 연결
  - [network/34-http-caching](../../network/34-http-caching/2-summary.md) — 캐시 키·신선도·`private`
  - [network/35-http-connection-management](../../network/35-http-connection-management/2-summary.md) — keep-alive 연결 재사용과 끊김
  - [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md) · [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md)
  - [data-structure/09-trie](../../data-structure/09-trie/2-summary.md) — 경로 라우팅
- 근거
  - Roy T. Fielding, *Architectural Styles and the Design of Network-based Software Architectures*, 박사논문, UC Irvine, 2000, 5장 "Representational State Transfer (REST)" — 5.1(제약 유도·트레이드오프), 5.2.1.1(자원 정의 MR(t)), 5.2.1.2(표현) <https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm>
  - Roy T. Fielding, "REST APIs must be hypertext-driven", 2008 <https://roy.gbiv.com/untangled/2008/rest-apis-must-be-hypertext-driven>
  - Martin Fowler, "Richardson Maturity Model", 2010-03-18 <https://martinfowler.com/articles/richardsonMaturityModel.html>
  - RFC 9110 §9.2.1(안전, 크롤러·프리페치, MUST), §9.2.2(멱등·재시도), §9.3.3(POST), §15.3.2(201) · RFC 9111(캐시 키) · RFC 10008 The HTTP QUERY Method(2026-06) §1·§2.7
  - Google AIP-121 Resource-oriented design, AIP-122 Resource names, AIP-131~135 표준 메서드, AIP-136 Custom methods <https://google.aip.dev/121> · <https://google.aip.dev/136>
  - nginx `ngx_http_proxy_module` 문서 — `proxy_cache_methods` 기본값 `GET HEAD`, `$upstream_cache_status` <https://nginx.org/en/docs/http/ngx_http_proxy_module.html>
  - OpenJDK jdk21u `src/java.net.http/share/classes/jdk/internal/net/http/MultiExchange.java` — `isIdempotentRequest`, `canRetryRequest`, `jdk.httpclient.enableAllMethodRetry`, `retriedOnce`
- 실험 목록
  - A: 같은 조회 `GET /products/1` vs `POST /getProduct`, nginx 1.31.6 `proxy_cache` 기본 메서드 — 3회씩, 백엔드 도착 1 vs 3
  - B: 서버가 닫은 keep-alive 연결 재사용 시 JDK 21.0.12 `HttpClient` 자동 재시도 — 기본(GET만 재시도) vs `enableAllMethodRetry=true`(POST도 재시도, 주문 2회 도착)
