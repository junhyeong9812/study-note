# api-design/19-api-gateway-and-bff — API 게이트웨이와 BFF: 라우팅·집계·오프로딩·게이트키퍼·발렛 키 — 정리 (힌트)

## 해결하는 문제

서비스를 여러 개로 나누면 클라이언트가 그 구조를 그대로 떠안는다.

```text
  게이트웨이 없이
  모바일 앱 ──> profile.svc   (인증 검사·TLS 인증서·속도 제한을 서비스마다 각자)
           ──> orders.svc
           ──> recommend.svc
  → 앱이 서비스 주소·분할 구조를 안다. 서비스를 쪼개거나 합치면 앱을 다시 배포해야 한다.
  → 셀룰러망에서 왕복 3번. 인증·TLS·속도 제한을 서비스마다 중복 구현.
```

- 해법: 클라이언트와 서비스 사이에 **입구 하나**를 둔다.
  - *API 게이트웨이*: 모든 클라이언트 요청이 들어오는 단일 진입점. 요청을 알맞은 서비스로 보내거나(라우팅), 여러 서비스로 퍼뜨린 뒤 모으고(집계), 공통 관심사(인증·TLS·속도 제한)를 대신 처리한다(오프로딩). microservices.io "API Gateway" 패턴의 정의를 따른다.
  - *BFF(Backends for Frontends)*: 클라이언트 종류(웹·iOS·Android)마다 **따로 둔** 게이트웨이·백엔드. Sam Newman이 2015-11-18 글로 정리했다. 그 글은 이 이름을 SoundCloud 출신 Phil Calçado가 부른 이름("as (ex-SoundClouder) Phil Calçado called it")으로 소개한다.
- 쉬운 예: 큰 건물의 안내 데스크. 방문객은 데스크(게이트웨이)에만 가면 된다. 데스크는 출입증 검사(오프로딩)를 하고, 맞는 층으로 안내(라우팅)하고, 여러 부서 서류를 한 봉투에 모아 준다(집계). 어린이 방문객 전용 창구가 따로 있으면 그게 BFF다.
- 똑같은 구조다. 대신 **데스크에 모든 일을 몰면** 데스크가 병목·단일 장애점이 되고, 업무 규칙이 데스크에 쌓이면 부서를 바꿀 때마다 데스크도 고쳐야 한다(분산 모놀리스).

## 동작·원리

### 1. 게이트웨이 패턴 셋 + 관련 패턴 둘 (Azure 아키텍처 센터 패턴 카탈로그)

```text
                       ┌──────────────── API 게이트웨이 ────────────────┐
  클라이언트 ──TLS──>  │ 오프로딩: TLS 종료·인증·속도 제한·로깅            │
                       │ 라우팅  : /api/orders/* → orders,  /api/* → 기본 │──> 서비스들
                       │ 집계    : 1요청 → profile + orders + recommend   │
                       └────────────────────────────────────────────────┘
  게이트키퍼: 공개 쪽 파사드는 검증·정제만, 저장소 자격 증명은 뒤쪽 신뢰 호스트만 가진다
  발렛 키   : 큰 파일은 게이트웨이를 거치지 않고, 짧게 유효한 범위 제한 토큰으로 저장소에 직접
```

- *Gateway Routing*: 엔드포인트 하나 뒤에 여러 서비스·인스턴스·버전을 두고 L7(경로·헤더 등)로 나눈다. 서비스를 쪼개거나 합쳐도 라우팅만 바꾸면 된다. 버전별 라우팅으로 블루그린 배포에도 쓴다.
- *Gateway Aggregation*: 클라이언트 요청 하나를 여러 백엔드 요청으로 나눠 보내고 결과를 합친다. 셀룰러망처럼 지연이 큰 경우에 이득이 크다.
- *Gateway Offloading*: TLS 인증서 관리·인증·모니터링·프로토콜 변환·스로틀링을 게이트웨이로 옮긴다. 문서는 **비즈니스 로직은 절대 게이트웨이로 옮기지 말라**("Never offload business logic to the gateway")고 적는다.
- *Gatekeeper*: 공개 엔드포인트 코드와 실제 처리·저장소 접근 코드를 분리한다. 게이트키퍼는 낮은 권한으로 돌고, 저장소 자격 증명을 갖지 않으며, 요청 검증·정제만 한다. 뚫려도 데이터에 바로 닿지 못한다.
- *Valet Key*: 클라이언트에게 특정 자원·특정 동작·짧은 기간으로 제한된 토큰(Azure SAS 등)을 주고 저장소에 직접 올리거나 받게 한다. 앱 서버가 대용량 전송을 중계하지 않는다.
- 이름에 Gateway가 붙은 패턴은 Routing·Aggregation·Offloading 셋이다. Gatekeeper·Valet Key는 카탈로그에서 보안(Security) 쪽으로 분류된 별개 패턴이다 — 여기서는 "요청이 어디를 거쳐 가나"를 함께 정하는 이웃 패턴이라 같이 본다. 발렛 키는 오히려 게이트웨이를 **거치지 않게** 하는 패턴이다.

### 2. 라우팅 — 가장 긴 접두사가 이긴다

```text
  location /api/         → backend /default/
  location /api/orders/  → backend /orders/      (+ API 키별 속도 제한)

  GET /api/users/1    → /api/ 만 일치                → /default/users/1
  GET /api/orders/3   → /api/ 와 /api/orders/ 둘 다 일치 → 더 긴 /api/orders/ 선택
```

- nginx `location` 문서: 접두사 location 중 **가장 길게 일치하는 것**을 골라 기억하고, 그다음 정규식 location을 설정 순서대로 검사한다. 정규식이 일치하지 않으면 기억해 둔 접두사 location을 쓴다. `=`는 정확 일치, `^~`는 정규식 검사를 건너뛴다.
- 설정 파일 안의 순서가 아니라 **길이**가 정한다는 점이 함정이다.

### 실험 1: 게이트웨이 오프로딩과 라우팅

(실험, nginx 1.31.6(`nginx:alpine`) 게이트웨이 + node 22.23.2 백엔드(경로별 도달 횟수 기록), 일회용 컨테이너·전용 네트워크, 2026-10-04)

```nginx
limit_req_zone $http_x_api_key zone=perkey:1m rate=60r/m;   # API 키별 분당 60건 = 초당 1건
server {
  listen 8082;
  if ($http_x_api_key = "") { return 401 '{"title":"missing api key"}'; }   # 오프로딩: 키 검사
  location /api/        { proxy_pass http://sn-ad-w17-backend:8080/default/; }
  location /api/orders/ { limit_req zone=perkey burst=2 nodelay; limit_req_status 429;
                          proxy_pass http://sn-ad-w17-backend:8080/orders/; }
}
```

```text
키 없음 /api/orders/1   -> 401
키 있음 /api/users/1    -> 200
키 있음 /api/orders/* 6회 연속 -> 200 200 200 429 429 429
백엔드 도달: {"GET /default/users/1":1,"GET /orders/0":1,"GET /orders/1":1,"GET /orders/2":1}
```

- 관찰
  - 키 없는 요청은 게이트웨이에서 끝났다. 백엔드 도달 기록의 `/orders/1`은 1번뿐이다 — 연속 6건 중 두 번째 요청이 남긴 것이고, 첫 줄의 키 없는 `/api/orders/1`은 닿지 않았다.
  - `/api/users/1`은 `/default/`로, `/api/orders/*`는 `/orders/`로 갔다 — 긴 접두사 우선.
  - 초당 1건 + `burst=2` + `nodelay`라 연속 6건 중 3건만 통과하고 나머지는 429였다. 거절된 3건은 백엔드에 닿지 않았다.
- 해석: 공통 관심사를 게이트웨이에서 끊으면 서비스는 그 코드를 갖지 않아도 된다. 이 설정은 429에 `Retry-After`를 붙이지 않는다 — 클라이언트 계약은 [14-rate-limit-and-quota-contracts](../14-rate-limit-and-quota-contracts/2-summary.md)에서 다룬다.
- nginx `limit_req` 문서: leaky bucket 방식, 기본 거절 상태 503(`limit_req_status`로 변경), **키가 빈 요청은 세지 않는다**. 키 없는 요청을 앞의 `if`로 먼저 끊은 이유다.

### 3. 집계 — 하위 하나의 지연이 전체 지연이 된다

```text
  순차, 타임아웃 없음       profile 50ms ─> orders 80ms ─> recommend 3000ms        합 ≈ 3.1s
  병렬, 타임아웃 없음       profile ──┐
                           orders  ──┼── 가장 느린 것 기다림                         ≈ 3.0s
                           recommend ┘
  병렬, 호출별 예산 300ms    profile ──┐
                           orders  ──┼── 300ms에서 끊고 있는 것만 반환 + missing 표시  ≈ 0.3s
                           recommend ┘ (null)
```

- 병렬로 바꿔도 응답 시간은 **가장 느린 하위 호출**에 묶인다. 타임아웃과 부분 응답 정책이 있어야 끊을 수 있다.
- Azure "Gateway Aggregation" 문서: 하위 호출이 너무 오래 걸리면 타임아웃 후 **일부 데이터만 돌려주는 것이 허용될 수 있으니** 앱이 그 경우를 어떻게 다룰지 정하라고 한다. 예시 절은 누락이 허용되면 부분 응답, 완전하고 일관된 데이터가 필요하면 요청 전체 실패 — 이 결정을 정책에 명시하라고 한다.

### 실험 2: 집계의 타임아웃과 부분 응답

(실험, JDK 21.0.12 temurin, `java Agg.java` 단일 파일, JDK `HttpClient` + `com.sun.net.httpserver`, `--network none`, 2026-10-04)

하위 서비스 3개를 같은 JVM의 HTTP 서버로 흉내 냈다. profile 50ms, orders 80ms, recommendations 3000ms 지연.

```java
// C: 호출마다 예산을 걸고, 넘기면 실패 대신 null — 무엇을 비워도 되는지는 화면(BFF)이 정한다
static CompletableFuture<String> call(int port, Duration t) {
  return http.sendAsync(req(port, t), HttpResponse.BodyHandlers.ofString())
      .thenApply(HttpResponse::body)
      .exceptionally(e -> null);          // HttpTimeoutException → 부분 응답
}
Duration budget = Duration.ofMillis(300);
g.put("profile", call(9001, budget)); g.put("orders", call(9002, budget)); g.put("recommendations", call(9003, budget));
```

```text
A 순차, 타임아웃 없음     :  3159 ms  {"name":"kim"}["order-1"]["rec-1"]
B 병렬, 타임아웃 없음     :  3053 ms  {"name":"kim"}["order-1"]["rec-1"]
C 병렬, 호출별 300ms 예산 :   307 ms  {profile={"name":"kim"}, orders=["order-1"], recommendations=null} missing=[recommendations]
```

- 네 번 실행했다(집필 2회·사실 점검 2회). A 3156~3163ms, B 3051~3053ms, C 306~307ms.
- 관찰: 병렬화만으로는 3초가 그대로다(B). 예산을 걸어야 0.3초로 끊고 나머지로 화면을 그릴 수 있다(C).
- JDK 21 `HttpRequest.Builder.timeout()` Javadoc: 타임아웃을 설정하지 않으면 무한 `Duration`을 준 것과 같다("block forever"). A·B가 3초를 다 기다린 이유다. (`connectTimeout`은 연결 수립에만 걸린다.)

### 4. BFF — 클라이언트별 백엔드

```text
  공용 게이트웨이 하나                        BFF
  웹  ─┐                                    웹  ──> 웹 BFF  (웹 팀 소유) ──┐
  iOS ─┼──> 범용 API ──> 서비스들             iOS ──> 모바일 BFF (앱 팀 소유) ─┼──> 서비스들
  Andr ┘   (모든 화면 요구가 한곳에 충돌)       Andr ┘                         ┘
```

- Azure "Backends for Frontends" 문서: 하나의 백엔드가 여러 프론트엔드의 상충 요구를 받으면 갱신이 잦고 병목이 된다. 인터페이스마다 BFF를 두고 **프론트엔드 팀이 자기 BFF를 관리**한다.
  - 고려 사항: 코드 중복은 예상되는 결과다. BFF는 특정 사용자 경험에 관한 **클라이언트 전용 로직만** 다루고, 모니터링·인가 같은 공통 기능은 게이트키퍼·속도 제한·라우팅 패턴으로 따로 둔다.
  - 맞지 않는 경우: 인터페이스들이 같은 요청을 보낼 때, 인터페이스가 하나뿐일 때. 프론트엔드별 리졸버를 둔 GraphQL을 쓰면 BFF가 가치를 더하지 않을 수 있다([17](../17-graphql/2-summary.md)).
- Newman 2015(저자 주장): "한 경험당 BFF 하나"(Stewart Gleadow 인용), UI 팀이 BFF를 소유. 범용 API 백엔드는 배포 병목이 되고 비대해지기 쉽다. 하위 호출 팬아웃은 전부-아니면-전무가 아닌 **저하 전략**이 필요하다.

## 쓰이는 자료구조·알고리즘

- **경로 → 백엔드 라우팅 테이블 = 접두사 일치**: 요청 경로와 가장 길게 일치하는 접두사를 고른다. 트라이로 만들면 경로 길이에 비례해 찾을 수 있다 → [data-structure/09-trie](../../data-structure/09-trie/2-summary.md), [data-structure/20-radix-trie](../../data-structure/20-radix-trie/2-summary.md). IP 라우팅의 최장 접두사 일치와 같은 생각이다 → [network/08](../../network/08-routing-and-longest-prefix-match/2-summary.md).
- **병렬 팬아웃 + 데드라인**: 호출을 동시에 띄우고 공통 마감 시각에서 끊는다. 응답 시간 = min(가장 느린 호출, 예산). `CompletableFuture`·`allOf`·호출별 timeout → [reliability/05](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md).
- **토큰 버킷 / leaky bucket**: 키별 카운터 해시 + 시간에 따른 보충. nginx `limit_req`는 leaky bucket → [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md).
- **서명된 토큰(발렛 키)**: 자원·권한·만료 시각을 문자열로 만들고 서버 키로 서명(HMAC). 저장소는 서명만 검증하면 된다.

## 적용 — 풀어나가는 법

### 1. 무엇을 어디에 둘까

| 일 | 게이트웨이 | BFF | 서비스 |
|---|---|---|---|
| TLS 종료·인증 토큰 검증·키별 속도 제한 | ○ | | |
| 경로·버전 라우팅 | ○ | | |
| 화면 하나를 위한 호출 조합·필드 잘라내기 | | ○ | |
| 부분 응답 허용 여부(어느 위젯을 비워도 되나) | | ○ | |
| 주문 가능 여부·가격 계산 같은 업무 규칙 | ✗ | ✗ | ○ |
| 대용량 업로드·다운로드 | ✗ — 발렛 키로 직접 | | 토큰 발급 |

- 게이트웨이 설정에 `if (user.tier == ...)` 같은 업무 분기가 보이기 시작하면 경고 신호다.

### 2. 집계 구현 체크리스트

1. 하위 호출마다 타임아웃(또는 남은 데드라인)을 건다. JDK `HttpClient`는 `HttpRequest.Builder.timeout()`을 직접 넣어야 한다.
2. 필수 필드와 선택 필드를 나눈다. 필수가 실패하면 전체 실패(5xx 또는 504), 선택이 실패하면 null + 누락 목록.
3. 클라이언트가 부분 응답을 알 수 있게 응답에 표시한다(예: `"missing": ["recommendations"]`).
4. 상관 ID를 하위 호출에 전파하고, 하위 호출별 지연을 지표로 낸다.
5. 게이트웨이·BFF 인스턴스를 여러 개 두고 LB 뒤에 둔다(단일 장애점 제거).

### 3. 우회 차단

- Azure "Gateway Offloading": 백엔드가 게이트웨이 경로로만 요청을 받게 하라. 그렇지 않으면 클라이언트가 백엔드에 직접 붙어 인증·스로틀링·로깅을 건너뛴다. 전달된 헤더(`X-Forwarded-*`, 사용자 ID 헤더)를 검증 없이 신원 증명으로 믿지 말라.

### 4. 진단

```text
  게이트웨이 지연 분해: (게이트웨이 총 지연) − (하위 호출 중 최댓값) = 게이트웨이 자체 오버헤드
  집계 엔드포인트: 하위 호출별 p99, 부분 응답 비율(missing 비어 있지 않은 응답 수 / 전체)
  우회 탐지: 서비스 접근 로그에서 게이트웨이 IP가 아닌 출처
```

## 장애 시나리오와 대처

### 1. 게이트웨이가 분산 모놀리스가 된다 (⚠)

- **현상**: 서비스 하나의 기능을 바꾸는데 게이트웨이 설정·스크립트도 같이 바꿔야 하고, 게이트웨이 팀 배포 일정에 묶인다.
- **보이는 형태**: 게이트웨이 저장소의 변경 빈도가 서비스보다 높다. 게이트웨이 배포가 여러 팀 기능 출시의 선행 조건이 된다.
- **원인**: 업무 규칙·응답 가공을 게이트웨이에 쌓았다. Azure 문서가 금지한 "비즈니스 로직 오프로딩"이다.
- **대처**: 게이트웨이는 라우팅·공통 관심사만. 조합·가공은 BFF나 게이트웨이 뒤 별도 집계 서비스로 옮긴다(Azure Aggregation 문서도 집계를 게이트웨이 안이 아니라 뒤에 두는 것을 고려하라고 한다).

### 2. 공용 게이트웨이 하나로 모바일·웹 요구가 충돌한다 (⚠)

- **현상**: 모바일 응답에 웹 화면용 필드가 잔뜩 붙어 페이로드가 크다. 한 팀의 요구가 다른 팀 승인을 기다린다.
- **보이는 형태**: 모바일 응답 크기 증가, 앱의 데이터 사용량 불만, API 변경 요청 대기열.
- **원인**: 범용 API 하나가 모든 화면을 만족시키려 한다.
- **대처**: 경험이 다른 클라이언트마다 BFF를 두고 그 클라이언트 팀이 소유한다. 중복은 감수하되 공통 로직은 서비스로 내린다. 인터페이스들이 같은 요청을 보낸다면 BFF를 나누지 않는다.

### 3. 추천 서비스 하나가 느려지자 홈 화면 전체가 느려진다 (⚠)

- **현상**: 홈 API p99가 하위 서비스 하나의 지연과 같이 움직인다.
- **보이는 형태**: 실험 A·B처럼 집계 응답 시간 ≈ 가장 느린 하위 호출. 게이트웨이 스레드·연결이 쌓인다.
- **원인**: 집계에 타임아웃·부분 응답 정책이 없다.
- **대처**: 호출별 예산 + 선택 필드 부분 응답(실험 C: 3053ms → 307ms). 반복되면 서킷 브레이커로 빨리 실패하고 캐시된 값을 대체로 쓴다([reliability/10](../../reliability/10-circuit-breaker/2-summary.md), [reliability/28](../../reliability/28-bulkhead/2-summary.md)).

### 4. 게이트웨이가 죽자 모든 API가 죽는다 — 단일 장애점 (⚠)

- **현상**: 게이트웨이 인스턴스 하나의 장애·배포 실수로 전체 서비스가 응답하지 않는다.
- **원인**: 모든 트래픽이 지나는 지점을 하나만 뒀다. 설정 변경 하나가 모든 경로에 영향을 준다.
- **대처**: 여러 인스턴스 + LB, 연결 드레이닝·graceful shutdown으로 재시작 시 진행 중 요청 보호(여기까지 Azure Offloading 문서). 설정 변경도 카나리로 배포한다(일반 관행). 셀 단위로 게이트웨이를 나누면 영향 범위가 줄어든다([reliability/51](../../reliability/51-cells-stamps-and-blast-radius/2-summary.md)).

### 5. 대용량 업로드가 앱 서버를 잡아먹는다

- **현상**: 파일 업로드가 몰릴 때 API 서버 메모리·대역폭이 포화되고 일반 API까지 느려진다.
- **원인**: 앱 서버가 업로드를 받아 저장소로 중계한다.
- **대처**: 발렛 키 — 앱은 짧은 유효 기간·특정 경로·쓰기(생성) 전용 토큰만 발급하고, 클라이언트가 저장소에 직접 올린다. Azure 문서 주의점: 키가 새면 유효 기간 동안 악용 가능, 업로드 크기는 키로 제한하기 어렵다, 올라온 데이터는 사용 전에 검증, URL에 담긴 키가 로그에 남을 수 있다.

## 핵심 문장

- API 게이트웨이는 단일 진입점에서 라우팅·집계·공통 관심사 오프로딩을 맡는다. 업무 규칙은 게이트웨이에 두지 않는다.
- 라우팅은 설정 순서가 아니라 가장 긴 접두사 일치로 정해진다(nginx 접두사 location 기준).
- 집계 응답 시간은 병렬로 해도 가장 느린 하위 호출에 묶인다. 호출별 예산과 부분 응답 정책이 있어야 끊을 수 있다(실험: 3053ms → 307ms).
- BFF는 경험이 다른 클라이언트마다 따로 두고 그 프론트엔드 팀이 소유한다. 중복은 대가로 받아들인다.
- 게이트키퍼는 공개 쪽을 낮은 권한의 검증 전용으로 분리하고, 발렛 키는 대용량 전송을 범위·기간 제한 토큰으로 저장소에 직접 넘긴다.

## 관련 주제·근거

- 선행
  - [18-api-style-selection](../18-api-style-selection/2-summary.md) — 스타일별 경계
  - network 46-load-balancers-and-proxies — 미작성, [network README](../../network/README.md)에서 상태 확인
- 후속·연결
  - [14-rate-limit-and-quota-contracts](../14-rate-limit-and-quota-contracts/2-summary.md) · [17-graphql](../17-graphql/2-summary.md) — 영역 표: [curriculum](../curriculum.md)
  - reliability [05-timeouts-and-deadline-propagation](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md) · [10-circuit-breaker](../../reliability/10-circuit-breaker/2-summary.md) · [11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md) · [28-bulkhead](../../reliability/28-bulkhead/2-summary.md) · [50-sidecar-ambassador-and-service-mesh](../../reliability/50-sidecar-ambassador-and-service-mesh/2-summary.md) · [51-cells-stamps-and-blast-radius](../../reliability/51-cells-stamps-and-blast-radius/2-summary.md)
  - software-design [45-monolith-vs-microservices](../../software-design/45-monolith-vs-microservices/2-summary.md)
  - security — 인증·토큰 노트는 미작성, [security README](../../security/README.md)
- 문서
  - Azure Architecture Center — Gateway Routing <https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-routing> · Gateway Aggregation(타임아웃·부분 응답, 집계를 게이트웨이 뒤에) <https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-aggregation> · Gateway Offloading("Never offload business logic to the gateway", 우회 차단) <https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading> · Gatekeeper <https://learn.microsoft.com/en-us/azure/architecture/patterns/gatekeeper> · Backends for Frontends <https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends> · Valet Key <https://learn.microsoft.com/en-us/azure/architecture/patterns/valet-key>
  - JDK 21 `java.net.http.HttpRequest.Builder.timeout` Javadoc <https://docs.oracle.com/en/java/javase/21/docs/api/java.net.http/java/net/http/HttpRequest.Builder.html>
  - Sam Newman, "Backends For Frontends", 2015-11-18 <https://samnewman.io/patterns/architectural/bff/>
  - Chris Richardson, microservices.io "API Gateway / Backends for Frontends" <https://microservices.io/patterns/apigateway.html>
  - nginx `location`(최장 접두사 → 정규식 순서) <https://nginx.org/en/docs/http/ngx_http_core_module.html#location> · `ngx_http_limit_req_module`(leaky bucket, 기본 503, 빈 키 미집계) <https://nginx.org/en/docs/http/ngx_http_limit_req_module.html>
- 실험 목록
  - nginx 게이트웨이의 키 검사(401)·최장 접두사 라우팅·키별 `limit_req`(burst=2 nodelay → 3건 통과 후 429)와 백엔드 도달 횟수 — nginx 1.31.6(`nginx:alpine`), node 22.23.2. 사실 점검에서 두 `location` 순서를 바꾼 설정으로도 돌려 같은 출력
  - 집계: 순차·병렬·호출별 300ms 예산의 응답 시간과 부분 응답 — JDK 21.0.12 temurin 단일 파일(`HttpClient`, `com.sun.net.httpserver`)
