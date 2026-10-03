# api-design/03-status-codes-for-apis — API 상태 코드 선택: 4xx vs 5xx, 409·422·429 — 정리 (힌트)

## 해결하는 문제

상태 코드는 본문을 읽지 않는 소프트웨어가 응답을 처리하는 유일한 근거다.

```text
                         응답 하나 ── 상태 코드 ──┬──> 재시도 계층: 다시 보낼까?
                                                 ├──> 모니터링: 에러율에 셀까? 누구 탓?
                                                 ├──> 로드 밸런서·헬스체크: 이 서버 빼야 하나?
                                                 ├──> 캐시: 저장해도 되나? (404는 휴리스틱 캐시 가능)
                                                 └──> 클라이언트 SDK: 어떤 예외로 던질까?
                                   본문(에러 상세) ──> 사람·앱 로직 (04에서)
```

- 상태 코드를 잘못 고르면 이 계층들이 **한꺼번에** 틀린 행동을 한다.
  - 실패를 200으로 주면 재시도도, 경보도 일어나지 않는다.
  - 클라이언트 잘못(입력 오류)을 500으로 주면 재시도 계층이 같은 잘못된 요청을 반복하고, 서버 팀에 경보가 울린다.

쉬운 예: 택배 반송 사유 도장이다.
- "주소 불명"(고쳐서 다시 보내라)과 "물류센터 일시 마비"(그대로 나중에 다시)는 처리가 다르다.
- 둘 다 "배송 완료" 도장을 찍고 상자 안에 쪽지로 사정을 적으면, 물류 시스템은 아무것도 못 한다.

똑같은 구조다.\
첫 자리 4·5가 "누가 고쳐야 하나"를, 세부 번호가 "어떻게 다시 시도하나"를 알려 준다.

실무 예:
- (예시) 외부 API가 모든 실패를 `200 {"success":false}`로 주면, 그 API가 장애일 때 우리 쪽 호출 에러율 대시보드는 0%로 보인다.
- (예시) 입력 검증 실패를 500으로 돌려주는 API 앞에 "5xx면 3번 재시도" 게이트웨이가 있으면, 잘못된 요청 하나가 서버에 4번 도착한다(아래 실험에서 재현).

## 동작·원리

### 1. 첫 자리가 분류, 클라이언트는 분류를 이해해야 한다(MUST)

```text
  2xx  성공          요청을 받아 이해하고 수락했다
  3xx  리다이렉트     완료하려면 추가 동작이 필요하다
  4xx  클라이언트 오류 요청에 잘못이 있거나 이행할 수 없다      ← 같은 요청을 그대로 다시 보내도 대개 같다
  5xx  서버 오류      서버가 유효해 보이는 요청을 처리 못 했다  ← 서버 사정이 바뀌면 다시 될 수 있다
```

- RFC 9110 §15: 클라이언트가 모든 코드를 알 필요는 없다. 하지만 첫 자리 분류는 이해해야 하고(MUST), 모르는 코드는 그 분류의 x00으로 다룬다. 예) 모르는 471은 400처럼.
- 4xx·5xx 응답에는 (HEAD가 아니면) 오류 설명과 그것이 일시적인지 영구적인지를 담은 표현을 보내야 한다(SHOULD, §15.5·§15.6).
- "같은 요청을 그대로 다시 보내면 되나"의 대략적 구분은 분류에서 나온다. 단, 예외가 있다.
  - 4xx인데 기다리면 되는 것: 429(속도 제한), 408(요청 시간 초과).
  - 5xx인데 다시 보내면 안 되는 것: 비멱등 요청이 서버에서 처리됐을 수 있는 경우(05의 멱등 키 없이는 위험).
- Google Cloud Storage 재시도 전략 문서(회사 문서): 408·429·5xx와 소켓 타임아웃·TCP 끊김을 "일시적이라 재시도할 만한 응답"으로 들고, **요청의 멱등성**을 재시도의 두 번째 조건으로 둔다.

### 2. 고르는 순서 — 결정 흐름

```text
  요청 도착
   │
   ├─ 형식을 못 읽음(JSON 깨짐, 필수 헤더 없음) ................... 400
   ├─ 인증 정보 없음·틀림 .......................................... 401 (+ WWW-Authenticate, MUST)
   ├─ 누군지는 아는데 권한 없음 .................................... 403 (존재를 숨기려면 404 가능, MAY)
   ├─ 대상 자원 없음 ............................................... 404 (영구 삭제를 알면 410)
   ├─ 이 자원이 지원하지 않는 메서드 ............................... 405 (+ Allow, MUST)
   ├─ 본문 미디어 타입 미지원 ...................................... 415
   ├─ 문법은 맞는데 의미가 틀림(qty=-1, 존재하지 않는 상품 id) ....... 422 또는 400 (아래 표)
   ├─ 전제 조건(If-Match 등) 불일치 ................................ 412
   ├─ 현재 자원 상태와 충돌(이미 취소된 주문 취소, 버전 충돌) ......... 409
   ├─ 너무 많이 보냄 ............................................... 429 (+ Retry-After 가능)
   │
   └─ 처리 시도
       ├─ 성공: 조회 200 · 생성 201(+Location) · 비동기 접수 202 · 본문 없음 204
       ├─ 예상 못 한 서버 결함 ........................................ 500
       ├─ 일시 과부하·점검 ............................................ 503 (+ Retry-After 가능)
       └─ (게이트웨이가) 상류 응답 이상 / 시간 초과 ...................... 502 / 504
```

- 순서에도 의미가 있다. Google AIP-193: 권한이 없으면 자원이 있든 없든 403(PERMISSION_DENIED)이어야 하고, **권한 검사를 존재 확인보다 먼저** 해야 한다(회사 지침). 반대 순서면 404/403 차이로 "그 자원이 존재한다"는 정보가 샌다.
- RFC 9110 §15.5.4는 반대 방향을 허용한다. 존재를 숨기려는 서버는 403 대신 404를 줄 수 있다(MAY). 둘 다 "존재 여부를 권한 없는 사람에게 알리지 않는다"는 같은 목표다.

### 3. 자주 헷갈리는 쌍 — 표준과 회사 관례를 나눠 본다

| 상황 | RFC 9110 | Google(AIP-193 + `google.rpc.Code` 매핑) | Stripe(API 문서) |
|---|---|---|---|
| 필수 파라미터 누락 | 400 | INVALID_ARGUMENT → 400 | 400 |
| 문법은 맞고 의미가 틀림 | 422 (§15.5.21) | INVALID_ARGUMENT → 400 | 400("요청을 받아들일 수 없음") |
| 이미 있음(중복 생성) | 409 | ALREADY_EXISTS → 409 | 409(같은 멱등 키 충돌 등) |
| 동시성 충돌(test-and-set 실패) | 409 / 412(조건부 요청) | ABORTED → 409 | — |
| 시스템 상태가 맞지 않음(빈 디렉터리 아님) | 409 | FAILED_PRECONDITION → **400** | — |
| 매개변수는 맞는데 요청 실패(카드 거절) | (402는 "향후 사용 예약") | — | **402** "Request Failed" |
| 속도 제한 | 429 (RFC 6585) | RESOURCE_EXHAUSTED → 429 | 429 |
| 일시 불가 | 503 | UNAVAILABLE → 503 | 500·502·503·504 |

- 422: 원래 WebDAV(RFC 4918 §11.2)에 있던 코드다. RFC 9110이 범용성 때문에 핵심 명세로 가져왔다(부록 B.3). 이름도 "Unprocessable Entity" → "Unprocessable Content".
- 409(§15.5.10): 대상 자원의 현재 상태와 충돌. 사용자가 충돌을 풀고 다시 보낼 수 있는 상황에 쓴다. 충돌 원인을 알 수 있는 내용을 담아야 한다(SHOULD).
- 402: RFC 9110 §15.5.3은 "향후 사용을 위해 예약"이라고만 적는다. Stripe는 자기 API에서 "매개변수는 유효했지만 요청이 실패"의 뜻으로 쓴다(회사 관례). 범용 클라이언트는 402를 400처럼 다룰 것이다(§15의 x00 규칙).
- Google의 재시도 기준(`code.proto` 주석): 그 호출만 다시 하면 되면 UNAVAILABLE(503), 더 높은 단계(읽기-수정-쓰기 전체)부터 다시 해야 하면 ABORTED(409), 시스템 상태를 고치기 전엔 재시도하지 말아야 하면 FAILED_PRECONDITION(400).
- 결론: 정답 하나가 있는 게 아니다. **API 안에서 일관되게 하나를 고르고 문서에 적는 것**이 계약이다(01). 경계는 "4xx냐 5xx냐"와 "재시도 의미"를 틀리지 않는 것이다.

### 4. 429·503과 Retry-After

- 429(RFC 6585 §4): 주어진 시간에 너무 많은 요청. 응답에 설명을 담아야 하고(SHOULD), `Retry-After`를 줄 수 있다(MAY). 429 응답은 캐시에 저장하면 안 된다(MUST NOT).
- RFC 6585는 서버가 사용자를 어떻게 식별하고 요청을 어떻게 세는지 정하지 않는다. 그 선택은 14(rate-limit 계약)의 몫이다.
- 503(§15.6.4): 일시 과부하·점검. `Retry-After`로 기다릴 시간을 줄 수 있다(MAY). 과부하일 때 503을 꼭 써야 하는 것은 아니며 연결을 거부하는 서버도 있다고 RFC가 적는다.
- `Retry-After` 값은 HTTP 날짜 또는 초 단위 정수다(§10.2.3).

### 5. 502·504는 게이트웨이의 말

- 502·504는 게이트웨이·프록시가 상류 문제를 대신 알리는 코드다. 앱 서버가 직접 만들 일은 드물다. 앱이 하류 서비스 실패를 502로 감싸는 설계도 있지만, 그 경우 모니터링에서 "LB가 만든 502"와 섞인다 — 세부는 [network/33-http-semantics](../../network/33-http-semantics/2-summary.md) 5절.

### 실험: 같은 실패, 세 가지 상태 코드 스타일

요청 10건 중 id 4·8은 입력 오류(qty < 0), id 3·6·9는 첫 시도에서 DB 일시 장애(두 번째 시도에 회복)다. 서버 스타일만 바꾼다.

```text
  CORRECT             입력 오류 422, 일시 장애 503, 성공 201
  OK_WITH_ERROR_BODY  전부 200, 실패는 본문 {"ok":false,"error":...}
  ALL_500             입력 오류·일시 장애 모두 500, 성공 201
```

클라이언트는 범용 HTTP 계층의 흔한 정책 하나로 고정한다.

```java
// 5xx·429면 최대 3번 더 시도, 4xx는 재시도 안 함, 2xx는 성공
for (int attempt = 0; attempt < 4; attempt++) {
    r = c.send(req, HttpResponse.BodyHandlers.ofString());
    if (!(r.statusCode() >= 500 || r.statusCode() == 429)) break;
}
```

서버는 응답마다 상태 코드 분류를 센다(대시보드가 보는 값).

(실험, JDK 21.0.12 temurin, `com.sun.net.httpserver` + JDK `HttpClient`, 일회용 컨테이너 `--network none`, 2026-10-04)

```text
== CORRECT             서버 도착=13  서버 집계={2xx=8, 4xx=2, 5xx=3}
   HTTP 계층 판정: 성공=8(그중 본문은 실패=0) 4xx 거절=2 재시도 소진=0
== OK_WITH_ERROR_BODY  서버 도착=10  서버 집계={2xx=10}
   HTTP 계층 판정: 성공=10(그중 본문은 실패=5) 4xx 거절=0 재시도 소진=0
== ALL_500             서버 도착=19  서버 집계={2xx=8, 5xx=11}
   HTTP 계층 판정: 성공=8(그중 본문은 실패=0) 4xx 거절=0 재시도 소진=2
```

관찰:
- **CORRECT**: 일시 장애 3건은 재시도로 회복했다(도착 10 + 재시도 3 = 13). 입력 오류 2건은 한 번에 끝났다. 대시보드에 5xx 3건이 잡혀 DB 문제를 볼 수 있다.
- **OK_WITH_ERROR_BODY**: 대시보드는 2xx 100%다. HTTP 계층은 10건 모두 성공으로 판정했지만 그중 5건은 실패였다. 일시 장애 3건은 재시도 한 번이면 회복했을 텐데 재시도되지 않았다.
- **ALL_500**: 입력 오류 2건이 각각 4번씩 도착했다(10 + 3 + 2×3 = 19). 5xx가 11건으로 부풀어, 서버 탓이 아닌 오류로 서버 팀 경보가 울린다. 클라이언트는 "재시도 소진"이라 입력을 고치라는 신호를 받지 못했다.
- 주의: 이 실험 클라이언트는 POST를 5xx에서 재시도했다. 실제로 그렇게 하려면 서버가 멱등 키(05)로 중복을 막아야 한다. 503이 "처리 안 했음"을 뜻한다는 보장은 HTTP에 없다.

## 쓰이는 자료구조·알고리즘

- **분류 = 정수 나눗셈**: `status / 100`. 모르는 코드도 분류로 처리할 수 있게 RFC가 첫 자리에만 의미를 줬다(§15). 실험의 집계(`status / 100 + "xx"`)가 그대로 이것이다.
- **재시도 판정표**: (상태 코드 분류, 메서드 멱등성, 재시도 횟수·예산)의 조회 표. 재시도 간격은 지수 백오프 + 지터 — [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md).
- **레이블별 카운터**: `http_requests_total{status="5xx"}`처럼 상태 분류를 레이블로 세는 카운터. 에러율 = 5xx 카운터 증가율 / 전체 증가율. 상태 코드를 잘못 주면 이 식의 분자가 틀린다 — [reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md).
- **예외 → 상태 코드 매핑 표**: 도메인 예외 타입을 키로 하는 맵. 한 곳(경계)에 모아 두면 API 전체가 일관된다 — [software-design/15-error-handling-design](../../software-design/15-error-handling-design/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. **팀의 매핑 표를 정한다.** 위 결정 흐름을 기준으로, 400 vs 422, 409 vs 412의 사용 규칙을 하나씩 고른다. 문서에 적는다.
2. **예외를 경계 한 곳에서 매핑한다.** 컨트롤러마다 `ResponseEntity.status(...)`를 흩뿌리지 않는다.
3. **4xx·5xx 응답 본문에 기계용 식별자를 넣는다**(04).
4. **클라이언트 재시도 정책을 상태 코드와 맞춘다.** 408·429·5xx + 멱등 요청만. `Retry-After`가 있으면 따른다.
5. **대시보드를 분류별로 나눈다.** 4xx 급증(클라이언트 배포 문제)과 5xx 급증(서버 문제)은 대응하는 팀이 다르다.

### 2. 코드 — 경계 한 곳에서 매핑 (Spring MVC)

```java
@RestControllerAdvice
class ApiErrors {
    @ExceptionHandler(InvalidQuantity.class)          // 의미 오류
    ResponseEntity<?> invalid(InvalidQuantity e)      { return status(422, "INVALID_QTY", e); }

    @ExceptionHandler(OrderAlreadyCancelled.class)    // 현재 상태와 충돌
    ResponseEntity<?> conflict(OrderAlreadyCancelled e) { return status(409, "ORDER_ALREADY_CANCELLED", e); }

    @ExceptionHandler({TransientDataAccessException.class,       // 쿼리 타임아웃·락 실패 등
                       CannotGetJdbcConnectionException.class})  // 커넥션 획득 실패(NonTransient 계열이라 따로)
    ResponseEntity<?> unavailable(Exception e) {
        return ResponseEntity.status(503).header("Retry-After", "1").body(Map.of("code", "DB_UNAVAILABLE"));
    }
    // 나머지는 500 — 세부 내용은 로그로만 (04)
}
```

- Spring 예외 계층 주의: 커넥션 획득 실패 `CannotGetJdbcConnectionException`은 `DataAccessResourceFailureException` → `NonTransientDataAccessResourceException` 아래다(spring-framework `spring-jdbc`·`spring-tx` 소스). `TransientDataAccessException`만 잡으면 연결 풀 고갈이 503으로 안 간다. 실제로 어떤 예외가 오는지는 JDBC/JPA 경로와 예외 번역 설정에 따라 다르니 로그로 확인한다.

### 3. 클라이언트 재시도 정책 (Java)

```java
static boolean retryable(HttpRequest req, HttpResponse<?> r) {
    int s = r.statusCode();
    boolean transientStatus = s == 408 || s == 429 || s >= 500;
    boolean idempotent = Set.of("GET", "HEAD", "PUT", "DELETE").contains(req.method())
                      || req.headers().firstValue("Idempotency-Key").isPresent();
    return transientStatus && idempotent;
}
// 대기: Retry-After(초)가 있으면 그 값, 없으면 지수 백오프 + 지터
```

### 4. 진단

```bash
# 상태 코드 분포 — 200만 있고 4xx·5xx가 0이면 오히려 의심한다
awk '{print $9}' access.log | sort | uniq -c | sort -rn
# 200 응답 본문에 에러 표시가 섞여 있나 (예시 패턴)
curl -s -w '\n%{http_code}\n' -X POST https://api.example.com/v1/orders -d '{"qty":-1}'
# 같은 요청이 짧은 간격으로 반복되나 — 재시도 폭풍의 흔적
awk '$9 ~ /^5/ {print $7}' access.log | sort | uniq -c | sort -rn | head
```

## 장애 시나리오와 대처

### 1. 200에 에러 바디 → 모니터링·재시도 무력화 (⚠ 커리큘럼)

- **현상**: 하류 DB 장애 동안 사용자 불만이 쏟아지는데 에러율 대시보드는 0%다. 경보가 울리지 않는다.
- **보이는 형태**: 접근 로그가 전부 200. 응답 본문에 `"ok":false`·`"error":...`. 클라이언트 SDK는 성공으로 처리하고 화면에서 빈 값을 보여 준다.
- **원인**: 실패를 2xx로 응답했다. 상태 코드를 보는 계층(재시도·지표·LB·캐시)이 모두 성공으로 판단했다. 실험의 OK_WITH_ERROR_BODY: 대시보드 2xx 100%, 실제 실패 5/10, 회복 가능한 3건도 재시도 안 됨.
- **대처**: 실패는 4xx·5xx로 바꾼다. 이전 클라이언트가 200 본문에 기대고 있다면(01의 Hyrum) 새 버전 경로에서 바꾸고, 그동안 본문의 에러 표시를 지표로 따로 센다.

### 2. 4xx를 5xx로 → 불필요한 재시도 폭풍 (⚠ 커리큘럼)

- **현상**: 특정 클라이언트 배포 뒤 서버 5xx가 급증하고 서버 팀이 호출된다. 서버에는 문제가 없다.
- **보이는 형태**: 같은 경로·같은 본문의 요청이 3~4번씩 연달아 도착한다. 5xx 대부분이 검증 예외 스택 트레이스와 함께 기록된다.
- **원인**: 검증 실패가 처리되지 않은 예외로 빠져 500이 됐다. 게이트웨이·클라이언트가 5xx를 재시도했다. 실험의 ALL_500: 잘못된 요청 1건이 4번 도착, 5xx 3건 → 11건.
- **대처**: 검증 예외를 경계에서 400/422로 매핑한다. 재시도 계층에 재시도 예산(전체 중 재시도 비율 상한)을 둔다(reliability/06).

### 3. 5xx를 4xx로 → 일시 장애가 "사용자 잘못"이 된다

- **현상**: DB 연결 풀 고갈 동안 사용자 화면에 "입력값을 확인하세요"가 뜬다.
- **보이는 형태**: 400 급증, 5xx는 평소대로. 서버 로그에는 커넥션 타임아웃.
- **원인**: 모든 예외를 400으로 매핑하는 catch-all 처리. 재시도 계층은 4xx라 재시도하지 않고, 서버 경보도 울리지 않는다.
- **대처**: catch-all은 500으로 둔다. 일시적 인프라 예외(커넥션 획득 실패·타임아웃)는 503으로 따로 매핑한다.

### 4. 403/404 차이로 자원 존재가 샌다

- **현상**: 남의 주문 번호를 넣으면 403, 없는 번호를 넣으면 404가 나온다. 번호를 훑어 "존재하는 주문"을 셀 수 있다.
- **보이는 형태**: 한 클라이언트가 연속된 id로 짧은 시간에 많은 404·403을 받는다.
- **원인**: 존재 확인을 권한 확인보다 먼저 했다.
- **대처**: AIP-193처럼 권한을 먼저 검사해 권한 없으면 존재와 무관하게 403, 또는 RFC 9110 §15.5.4처럼 숨기려면 둘 다 404로 통일한다. 팀 규칙으로 하나를 고른다.

### 5. `Retry-After` 없는 429·503 → 클라이언트 즉시 재시도로 폭주

- **현상**: 속도 제한에 걸린 클라이언트들이 곧바로 다시 보내 제한이 풀리지 않는다.
- **보이는 형태**: 429가 초당 수천 건, 같은 클라이언트의 재요청 간격이 수 ms.
- **원인**: 서버가 기다릴 시간을 알려 주지 않았고, 클라이언트 재시도에 백오프가 없었다.
- **대처**: 429·503에 `Retry-After`를 준다. 클라이언트는 그 값을 따른다. 세부 계약(제한 키·`RateLimit` 헤더)은 [14-rate-limit-and-quota-contracts](../14-rate-limit-and-quota-contracts/2-summary.md).

## 핵심 문장

- 상태 코드는 본문을 읽지 않는 계층(재시도·지표·LB·캐시)이 판단하는 유일한 근거라, 잘못 고르면 그 계층들이 한꺼번에 틀린다.
- 첫 자리는 "누가 고쳐야 하나"다. 4xx는 같은 요청을 그대로 다시 보내도 대개 같고, 5xx는 서버 사정이 바뀌면 될 수 있다 — 429·408과 비멱등 요청이 예외다.
- 실험에서 200+에러 바디는 대시보드를 2xx 100%로 만들어 실패 5건을 숨겼고, 전부 500은 잘못된 요청 2건을 4번씩 도착시켜 5xx를 3건에서 11건으로 부풀렸다.
- 400 vs 422, 409 vs 400(FAILED_PRECONDITION)은 RFC·Google·Stripe의 선택이 다르다. 하나를 골라 API 안에서 일관되게 문서화하는 것이 계약이다.
- 재시도는 상태 코드(408·429·5xx)와 멱등성 두 조건이 함께 맞을 때만 안전하다.

## 관련 주제·근거

- 선행
  - [02-rest-and-resource-modeling](../02-rest-and-resource-modeling/2-summary.md) — RMM Level 2: 메서드 + 상태 코드
  - [network/33-http-semantics](../../network/33-http-semantics/2-summary.md) — 상태 코드 분류, 502·503·504
- 후속(api-design)
  - [04-error-format-problem-details](../04-error-format-problem-details/2-summary.md) — 상태 코드가 못 담는 세부를 본문으로
  - [05-idempotency-keys](../05-idempotency-keys/2-summary.md) · [11-concurrency-control-in-apis](../11-concurrency-control-in-apis/2-summary.md)(412·428) · [13-long-running-operations](../13-long-running-operations/2-summary.md)(202) · [14-rate-limit-and-quota-contracts](../14-rate-limit-and-quota-contracts/2-summary.md)(429)
- 연결
  - [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md) — 재시도 예산·지터
  - [reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md) — 에러율 지표
  - [software-design/15-error-handling-design](../../software-design/15-error-handling-design/2-summary.md) · [software-design/17-error-messages-and-log-level-policy](../../software-design/17-error-messages-and-log-level-policy/2-summary.md) — 예외 경계, 4xx를 ERROR로 찍지 않기
- 근거
  - RFC 9110 §15(분류·x00 규칙), §15.5(4xx 설명 SHOULD), §15.5.2~§15.5.6(401·402 예약·403·404·405), §15.5.10(409), §15.5.13(412), §15.5.21(422), §15.6.1~§15.6.5(500·502·503·504), §10.2.3(Retry-After), 부록 B.3(422를 WebDAV에서 가져옴) <https://www.rfc-editor.org/rfc/rfc9110>
  - RFC 6585 §4 429 Too Many Requests(Retry-After MAY, 캐시 저장 MUST NOT) · RFC 4918 §11.2(422 원 정의)
  - Google AIP-193 Errors("Permission Denied" 순서) <https://google.aip.dev/193> · googleapis `google/rpc/code.proto`(HTTP 매핑, UNAVAILABLE·ABORTED·FAILED_PRECONDITION 구분 지침) <https://github.com/googleapis/googleapis/blob/master/google/rpc/code.proto>
  - Stripe API Reference "Errors" — HTTP Status Code Summary(400·401·402·403·404·409·424·429·5xx) <https://docs.stripe.com/api/errors>
  - Google Cloud Storage "Retry strategy" — 408·429·5xx + 멱등성 <https://cloud.google.com/storage/docs/retry-strategy>
  - Martin Fowler, "Richardson Maturity Model"(2010) — Level 2: "200 + 에러 대신 non-2xx"
- 실험 목록
  - 요청 10건(입력 오류 2, 일시 장애 3)을 세 스타일(CORRECT·OK_WITH_ERROR_BODY·ALL_500) 서버에 보내고, "5xx·429 최대 3회 재시도" 클라이언트로 서버 도착 수·상태 분류 집계·클라이언트 판정 비교 — JDK 21.0.12 temurin, `com.sun.net.httpserver` + `HttpClient`
