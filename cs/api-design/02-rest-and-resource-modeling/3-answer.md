# api-design/02-rest-and-resource-modeling — 정답

## 정답

### 1. RPC식 HTTP에서 중간자가 손을 못 쓰는 이유

- 중간자는 본문의 의미를 모르고 메서드·URI·헤더·상태 코드만 본다.
- 모든 요청이 `POST /api`면 조회인지 변경인지 겉에서 알 수 없다.
  - 캐시: POST라 저장하지 않는다.
  - 재시도: 비멱등일 수 있어 자동 재시도하지 않는다.
  - 모니터링: 경로 하나에 모든 동작이 섞인다.
- 해결 제약: **균일 인터페이스**, 특히 *자기 서술 메시지*(메서드·미디어 타입·캐시 지시로 처리 방법을 알 수 있음). 여기에 캐시 제약(응답에 캐시 가능 여부 표시)과 계층화 제약(중간자를 끼울 수 있음)이 함께 작동한다.

### 2. 제약 유도와 트레이드오프

```text
  Null → 클라이언트-서버 → 무상태 → 캐시 → 균일 인터페이스 → 계층화 → 주문형 코드(선택)
```

| 제약 | 얻는 것 | 잃는 것 |
|---|---|---|
| 무상태 | 가시성, 부분 실패 복구, 확장성 | 요청마다 반복 데이터 |
| 캐시 | 상호작용 일부 제거 → 지연·부하 감소 | 오래된 데이터 위험 |
| 균일 인터페이스 | 단순성, 가시성, 독립 진화 | 앱별 최적화보다 효율 낮음 |

- 근거: Fielding 2000, 5.1.2~5.1.7절(저자의 분석).

### 3. 자원과 표현

- 자원: 이름 붙일 수 있는 정보(문서, "오늘의 날씨", 다른 자원의 모음 등). 정확히는 시점마다 값 집합을 돌려주는 대응 MR(t). 고정할 것은 값이 아니라 대응의 의미다(5.2.1.1).
- 표현: 바이트 열 + 메타데이터(미디어 타입 등)(5.2.1.2). 같은 자원에 JSON·HTML 표현이 있을 수 있다.
- 두 논문: 지금 같은 값을 가리켜도 의미(대응 규칙)가 다르다. "저자가 선호하는 판"은 저자가 고칠 때마다 다른 값을 가리키고, "학회 X 게재판"은 고정이다(Fielding 5.2.1.1의 예). 그래서 따로 식별해야 한다.
- 함의: 자원은 저장 구조가 아니라 의미 단위다. Google AIP-121은 DB 스키마와 같은 API를 안티패턴이라 부른다. 테이블을 그대로 노출하면 스키마 변경이 API 파손이 된다.

### 4. RMM과 REST의 두 뜻

- Level 0: HTTP를 터널로, 한 엔드포인트에 POST.
- Level 1: 개별 자원에 요청.
- Level 2: HTTP 메서드(GET 안전 등)와 상태 코드(실패는 non-2xx, 생성은 201 + Location).
- Level 3: 하이퍼미디어 컨트롤(응답 안의 링크가 다음 행동을 안내).
- 업계의 "REST API"는 대체로 Level 2를 뜻하는 관용 표현이다. Fielding은 하이퍼텍스트로 구동되지 않으면 REST API가 아니라고 한다(2008 블로그). Fowler도 Level 3이 REST의 전제 조건이라는 Fielding의 입장을 소개한다.
- Fowler는 RMM을 REST의 정의나 평가 기준이 아니라 **개념을 단계적으로 이해하는 학습 도구**로 쓰라고 적는다.

### 5. GET vs POST 캐시 실험

(실험, nginx 1.31.6, 기본 `proxy_cache_methods`)

```text
GET  /products/1  #1  X-Cache-Status=MISS
GET  /products/1  #2  X-Cache-Status=HIT
GET  /products/1  #3  X-Cache-Status=HIT
POST /getProduct  #1~#3  X-Cache-Status=(빈 값)
백엔드 도착 수: {GET /products/1=1, POST /getProduct=3}
```

- nginx `proxy_cache_methods` 기본값은 `GET HEAD`다. POST는 캐시 경로를 타지 않아 상태 변수도 비었다. 서버가 캐시 헤더를 줘도 소용없다.

### 6. 끊긴 연결 위의 자동 재시도

(실험, JDK 21.0.12 `HttpClient`, HTTP/1.1)

| 요청 | 기본 | `enableAllMethodRetry=true` |
|---|---|---|
| `GET /products/1` | 새 연결로 재시도 → 200, 서버 도착 2 | 같음 |
| `POST /getProduct` | `IOException: HTTP/1.1 header parser received no bytes`, 도착 1 | 재시도 → 200, 도착 2 |
| `POST /orders` | 같은 `IOException`, 도착 1 | 재시도 → 200, **도착 2**(주문 중복 위험) |

- 근거: jdk21u `MultiExchange.java`의 `isIdempotentRequest`(`"GET", "HEAD"`만 true), `canRetryRequest`(`RETRY_ALWAYS`면 무조건), `retryPostValue`(`jdk.httpclient.enableAllMethodRetry`), 재시도는 `retriedOnce`로 한 번.
- RFC 9110은 PUT·DELETE도 멱등으로 정의하지만, JDK 21 기본값은 끊긴 연결 위의 실패에서 GET·HEAD만 재시도해 더 좁다. 프로토콜 정의와 라이브러리 기본값은 다른 계층이다.
- 단, 연결 수립 실패(`ConnectException`)와 서버가 처리하지 않았다고 알린 요청(HTTP/2 GOAWAY·REFUSED_STREAM)은 메서드와 무관하게 한 번 재시도한다(`MultiExchange.getExceptionalCF`의 `retryOnFailure`·`isUnprocessedByPeer`).

### 7. 동사형 URL 규칙의 범위

- 단순화된 규칙이다. AIP-136은 표준 메서드로 표현하기 어려운 동작에 `POST /v1/…/books/b1:archive` 같은 커스텀 메서드를 허용한다.
- 조건(AIP-136): 데이터·상태 조회는 GET(must). 부작용이 있으면 POST(must). 조회라도 요청 내용이 URL 길이 한도를 넘을 수 있어 본문이 필요하면 POST를 쓸 수 있다(may).
- 지켜야 할 핵심은 "URL에 동사가 없다"가 아니라 **메서드 의미와 동작이 일치**하는 것이다.
- 동작을 자원으로: "환불하다" → `POST /orders/{id}/refunds`(환불 자원 생성). 환불 이력 조회 `GET …/refunds`가 따라 생긴다(사례 27). "취소하다" → `POST /orders/{id}/cancellations`.

### 8. 본문이 필요한 조회

- POST로 조회하면 공유 캐시를 못 쓰고(실험 A), 자동 재시도도 안 된다(실험 B). 클라이언트가 조회와 생성을 구별할 수 없다.
- RFC 10008(2026-06) QUERY: 본문을 가진 안전하고 멱등인 메서드다. 캐시할 수 있고, 캐시 키에 요청 본문을 포함해야 한다(MUST, §2.7).
- 확인할 것: 프록시·CDN·게이트웨이·클라이언트 라이브러리가 QUERY를 통과·캐시·재시도하는지 제품·버전별로. 예로 jdk21u `MultiExchange`의 자동 재시도 목록에는 QUERY가 없다.
- 대안: 검색을 자원으로 저장(`POST /savedSearches` → `GET …/results`).

### 9. GET 링크로 생긴 승인

- 호출자 가설: 메일·메신저의 링크 미리보기 봇, 보안 스캐너, 프리페치. 승인 로그의 User-Agent·시각(발송 직후)으로 확인한다.
- RFC 9110 §9.2.1: 안전 메서드 구분은 자동화된 프로세스(링크 점검·프리페치·검색 색인)가 해를 걱정하지 않고 GET을 호출하게 하려는 것이다. URI 파라미터로 위험한 동작을 고르는 자원이면, 안전 메서드로 접근할 때 그 동작을 막아야 한다(MUST).
- 수정: 링크는 확인 화면(GET)으로 보내고, 실제 승인은 그 화면에서 POST로 보낸다.

### 10. 단계형 흐름과 무상태

- 어긴 제약: **무상태**(Fielding 5.1.3). 중간 단계 상태를 서버 메모리 세션에 뒀다. 다른 인스턴스로 가면 그 문맥이 없다.
- 보이는 형태: 세션 없음 400, 고정 세션(sticky)을 켜야만 동작.
- 바꾸는 법: 흐름 자체를 자원으로 만든다. `POST /checkouts`(생성) → `PATCH /checkouts/{id}`(단계 진행) → `POST /checkouts/{id}/confirmations`. 상태는 서버 저장소의 **자원 상태**가 되고, 어느 인스턴스든 처리할 수 있다. AIP-121도 자원이 "특정 순서의 요청을 거쳐야 닿는" 방식이 아니라 직접 주소로 접근 가능해야 한다고 적는다.
