# api-design/04-error-format-problem-details — 에러 응답 표준 형식: RFC 9457 Problem Details — 정리 (힌트)

## 해결하는 문제

상태 코드(03)는 "어떤 종류의 실패인가"까지만 말한다. 클라이언트가 실제로 대처하려면 더 필요하다.

```text
  HTTP/1.1 403 Forbidden            ← 범용 소프트웨어(캐시·LB·SDK)는 여기까지만 본다
  Content-Type: ???

  { ??? }                           ← 앱이 알고 싶은 것
                                       - 정확히 무슨 문제? (잔액 부족 / 한도 초과 / 정지된 계정)
                                       - 어느 입력이? (age 필드, profile.color 필드)
                                       - 고칠 방법은? (충전 링크, 문서 링크)
                                       - 이 발생 건을 지원팀에 어떻게 알리지? (발생 id)
```

- 이 본문의 형식을 API마다, 엔드포인트마다 따로 정하면 두 가지가 깨진다.
  - **클라이언트 파싱**: 에러 처리 코드를 형식 수만큼 짜야 한다. 처음 보는 형식이 오면 파싱 자체가 실패한다.
  - **보안**: 형식이 없으니 개발 편의로 예외 메시지·스택 트레이스를 그대로 내보내기 쉽다.
- *Problem Details*(RFC 9457, 2023-07): HTTP API 에러 본문의 공통 JSON(·XML) 형식. RFC 7807(2016)을 대체한다.

쉬운 예: 병원 진단서 양식이다.
- 병원마다 진단서 양식이 다르면 보험사는 서류마다 사람을 붙여 읽어야 한다.
- 양식이 같으면 "질병 코드" 칸만 기계로 읽고, 나머지 칸은 사람이 참고한다.

똑같은 구조다.\
`type`이 질병 코드, `title`·`detail`이 사람이 읽는 설명, 확장 멤버가 보험사가 필요한 추가 칸이다.

실무 예:
- 한 서비스 안에서 도메인 오류는 `{"code":..,"msg":..}`, 프레임워크 오류는 `{"timestamp":..,"error":..}`, 게이트웨이 오류는 HTML 페이지로 나온다. 앱의 공통 에러 처리기가 JSON 파싱 예외로 죽는다.
- 운영 설정에 개발용 옵션이 남아, 500 응답 본문에 SQL 문과 제약 조건 이름, 클래스 경로가 담긴 스택 트레이스가 나간다.

## 동작·원리

### 1. Problem Details 객체 — 멤버 다섯 + 확장

```text
  HTTP/1.1 403 Forbidden
  Content-Type: application/problem+json          ← 미디어 타입으로 "이건 문제 상세다"를 알린다
  Content-Language: en

  {
   "type": "https://example.com/probs/out-of-credit",   ← 문제 유형의 식별자(URI). 기계는 이걸로 분기
   "title": "You do not have enough credit.",           ← 유형의 짧은 요약. 발생마다 바뀌지 않음
   "status": 403,                                       ← 참고용 사본. 실제 HTTP 상태와 같아야 함
   "detail": "Your current balance is 30, but that costs 50.",  ← 이번 발생 건 설명(사람용)
   "instance": "/account/12345/msgs/abc",               ← 이번 발생 건 식별자
   "balance": 30,                                       ← 확장 멤버(유형이 정의)
   "accounts": ["/account/12345", "/account/67890"]
  }
```

(RFC 9457 §3의 예시에 `"status": 403` 한 줄을 더했다 — 원문 예시에는 `status` 멤버가 없다)

| 멤버 | 뜻 | 소비자 규칙 |
|---|---|---|
| `type` | 문제 유형 URI. 없으면 `about:blank` | 문제 유형의 **주 식별자로 써야 한다**(MUST). 자동으로 역참조하지 않아야 한다(SHOULD NOT) |
| `status` | 서버가 만든 HTTP 상태 코드 사본 | 참고용(advisory). 생성자는 실제 응답과 같은 코드를 써야 한다(MUST) |
| `title` | 유형의 짧은 사람용 요약 | 발생마다 바뀌지 않아야 한다(SHOULD NOT, 현지화 제외) |
| `detail` | 이번 발생 건에 대한 사람용 설명 | **파싱해서 정보를 뽑지 않아야 한다**(SHOULD NOT). 필요한 정보는 확장 멤버로 |
| `instance` | 이번 발생 건을 식별하는 URI 참조 | 역참조 가능하면 상세를 가져올 수 있고, 아니면 불투명 식별자 |
| 확장 멤버 | 유형별 추가 정보 | 모르는 확장은 **무시해야 한다**(MUST) |

- 멤버 값의 타입이 명세와 다르면 그 멤버는 무시해야 한다(MUST, §3.1). 처리는 그 멤버가 없는 것처럼 계속한다.
- `about:blank`: "상태 코드 이상의 의미가 없다"는 유형. 이때 `title`은 그 상태 코드의 표준 문구("Not Found" 등)와 같아야 한다(SHOULD, §4.2.1).
- `status`를 둔 이유: 중간자가 상태 코드를 바꿨거나, 본문만 따로 저장됐을 때 원래 코드를 알기 위해서다. 범용 HTTP 소프트웨어는 여전히 실제 HTTP 상태를 쓴다(§3.1.2·§5).

### 2. 새 문제 유형 정의 — 무엇을 문서화하나

- 새 문제 유형 정의는 반드시 세 가지를 문서화해야 한다(MUST, §4).
  1. `type` URI(보통 http·https)
  2. 적절한 `title`
  3. 함께 쓸 HTTP 상태 코드
- `type` URI는 문제 해결 방법을 설명하는 HTML 문서로 이어지는 것이 좋다(SHOULD).
- 확장 멤버 이름은 영문자로 시작하고 영문자·숫자·`_`로, 3자 이상이 좋다(SHOULD). JSON 밖의 형식(XML 등)으로도 직렬화할 수 있게 하려는 것이다(§4).
- 쓰지 말아야 할 곳(§4)
  - 진짜 범용 문제(어떤 자원에나 해당)는 상태 코드만으로 충분하다. 예: PUT에 대한 403 "쓰기 금지"는 따로 유형을 만들 필요가 없다.
  - Problem Details는 **구현 디버깅 도구가 아니다.** HTTP 인터페이스 자체의 세부를 드러내는 수단이다.
- 공용 유형 등록소: RFC 9457이 IANA "HTTP Problem Types" 등록소를 만들었다(§4.2). 회사·앱 전용 값은 등록할 수 없다.

### 3. 여러 오류를 한 번에 — 검증 오류

```text
  HTTP/1.1 422 Unprocessable Content
  Content-Type: application/problem+json

  {
   "type": "https://example.net/validation-error",
   "title": "Your request is not valid.",
   "errors": [
     {"detail": "must be a positive integer",       "pointer": "#/age"},
     {"detail": "must be 'green', 'red' or 'blue'", "pointer": "#/profile/color"}
   ]
  }
```

(RFC 9457 §3의 예시 그대로)

- 같은 유형의 여러 발생은 유형이 정의한 확장(`errors` 배열)으로 담는다. 각 항목의 `pointer`는 요청 본문 안 위치를 가리키는 JSON Pointer다.
- 서로 다른 유형의 문제가 여럿이면, 가장 관련 있거나 급한 문제 하나를 응답하는 것이 권장된다(RECOMMENDED, §3). 서로 다른 유형을 묶는 "배치" 문제 유형은 HTTP 의미와 잘 맞지 않는다고 적는다.

### 4. RFC 7807 → 9457에서 바뀐 것(부록 D)

- 공용 문제 유형 등록소(§4.2) 신설.
- 여러 문제를 다루는 방법 명확화(§3).
- 역참조할 수 없는 `type` URI(예: `tag:` 스킴) 사용 지침(§3.1.1). 단, 나중에 역참조가 필요해지면 URI를 바꿔야 하고 그것은 깨는 변경이 된다. 그래서 역참조 가능한 URI를 권한다.

### 5. 다른 회사들의 에러 형식 — 같은 역할, 다른 이름

| 역할 | RFC 9457 | Google(AIP-193, HTTP+JSON 표현) | Stripe(API 문서) |
|---|---|---|---|
| 상태 분류 | HTTP 상태 + `status` | `error.code`(HTTP 숫자) + `error.status`(`NOT_FOUND` 등) | HTTP 상태 + `type`(`card_error` 등 4종) |
| 기계용 식별자 | `type` URI | `details[]`의 `ErrorInfo`: `reason` + `domain` (+ `metadata`) | `code`(일부 오류), `decline_code` |
| 사람용 설명 | `title`, `detail` | `message`(영어 개발자용), `LocalizedMessage` | `message` |
| 어느 입력이 | 확장(`errors[].pointer` 등) | `BadRequest` 상세 | `param` |
| 더 읽을 곳 | `type` URI 문서 | `Help` 상세의 링크 | `doc_url` |

- 셋 다 "범용 분류는 상태 코드, 기계용 식별자는 따로, 사람용 문장은 파싱하지 않는다"는 구조가 같다.
- 회사 형식을 이미 쓰고 있으면 바꿀 필요는 없다. RFC 9457도 "이미 앱 전용 형식이 있으면 그것을 쓰는 게 낫다"고 적는다(§4.1). 새 API라면 직접 만들 이유가 적다.

### 6. 보안 — 에러 본문에 무엇을 넣지 않나

- RFC 9457 §5: 문제 유형을 정의할 때도, 실제로 생성할 때도 담는 정보를 검토해야 한다. 위험은 시스템 공격에 쓸 정보, 시스템 접근, 사용자 개인정보 노출이다.
- 발생 정보 링크를 줄 때 스택 덤프 같은 구현 세부를 HTTP 인터페이스로 내보내지 않도록 권한다.
- 그래서 나누는 원칙(software-design/17과 같은 축)
  - 응답: `type`·`title`·사용자에게 의미 있는 `detail`·`instance`(발생 id).
  - 로그: 예외 원문·스택 트레이스·SQL·내부 호스트. `instance` 값으로 응답과 로그를 잇는다.

### 실험: Spring Boot 4.1.1의 에러 응답 — 형식이 섞이고, 설정 하나로 내부가 샌다

앱 하나에 엔드포인트 셋을 둔다.

```java
@GetMapping("/orders/{id}")              // long id. 42 외에는 도메인 예외 OrderNotFound
@GetMapping("/boom")                     // 처리 안 된 예외, 메시지에 SQL·제약 조건 이름 포함
    throw new IllegalStateException("could not execute statement [ERROR: duplicate key value "
        + "violates unique constraint \"uk_member_email\"] [insert into member (email,password_hash) values (?,?)]");

@ExceptionHandler(App.OrderNotFound.class)   // 도메인 오류만 직접 ProblemDetail로
ProblemDetail notFound(App.OrderNotFound e) {
    ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, "주문 " + e.id + "이(가) 없습니다.");
    pd.setType(URI.create("https://api.example.com/problems/order-not-found"));
    pd.setTitle("Order not found");
    pd.setProperty("orderId", e.id);
    return pd;
}
```

설정 네 가지로 `/orders/7`(도메인 오류), `/orders/abc`(프레임워크의 형식 변환 오류), `/boom`(처리 안 된 예외)을 호출한다.

(실험, Spring Boot 4.1.1 · Spring Framework 7.0.9 · Tomcat 11.0.24 · JDK 21 temurin, maven 컨테이너 `--network none`, 2026-10-04)

```text
== 기본값
  GET /orders/7 -> 404 application/problem+json
    {"detail":"주문 7이(가) 없습니다.","instance":"/orders/7","status":404,"title":"Order not found","type":"https://api.example.com/problems/order-not-found","orderId":7}
    [키] [detail, instance, status, title, type, orderId]
  GET /orders/abc -> 400 application/json
    {"timestamp":"2026-10-03T19:40:53.918Z","status":400,"error":"Bad Request","path":"/orders/abc"}
    [키] [timestamp, status, error, path]
  GET /boom -> 500 application/json
    {"timestamp":"2026-10-03T19:40:53.973Z","status":500,"error":"Internal Server Error","path":"/boom"}
    [키] [timestamp, status, error, path]
== 옛 이름 server.error.* (3.x식)
  GET /orders/7 -> 404 application/problem+json
    {"detail":"주문 7이(가) 없습니다.","instance":"/orders/7","status":404,"title":"Order not found","type":"https://api.example.com/problems/order-not-found","orderId":7}
    [키] [detail, instance, status, title, type, orderId]
  GET /orders/abc -> 400 application/json
    {"timestamp":"2026-10-03T19:40:55.005Z","status":400,"error":"Bad Request","path":"/orders/abc"}
    [키] [timestamp, status, error, path]
  GET /boom -> 500 application/json
    {"timestamp":"2026-10-03T19:40:55.024Z","status":500,"error":"Internal Server Error","path":"/boom"}
    [키] [timestamp, status, error, path]
== 새 이름 spring.web.error.*
  GET /orders/7 -> 404 application/problem+json
    {"detail":"주문 7이(가) 없습니다.","instance":"/orders/7","status":404,"title":"Order not found","type":"https://api.example.com/problems/order-not-found","orderId":7}
    [키] [detail, instance, status, title, type, orderId]
  GET /orders/abc -> 400 application/json
    {"timestamp":"2026-10-03T19:40:55.872Z","status":400,"error":"Bad Request","trace":"org.springframework.web.method.annotation.MethodArgumentTypeMismatchException: Method parameter 'id': Failed to convert value of type 'java.lang.String' to required type 'l …(생략)
    [키] [timestamp, status, error, trace, message, path]
    [message] Method parameter 'id': Failed to convert value of type 'java.lang.String' to required type 'long'; For input string: \"abc\"
  GET /boom -> 500 application/json
    {"timestamp":"2026-10-03T19:40:55.894Z","status":500,"error":"Internal Server Error","trace":"java.lang.IllegalStateException: could not execute statement [ERROR: duplicate key value violates unique constraint \"uk_member_email\"] [insert into member (emai …(생략)
    [키] [timestamp, status, error, trace, message, path]
    [message] could not execute statement [ERROR: duplicate key value violates unique constraint \"uk_member_email\"] [insert into member (email,password_hash) values (?,?)]
== problemdetails 켬
  GET /orders/7 -> 404 application/problem+json
    {"detail":"주문 7이(가) 없습니다.","instance":"/orders/7","status":404,"title":"Order not found","type":"https://api.example.com/problems/order-not-found","orderId":7}
    [키] [detail, instance, status, title, type, orderId]
  GET /orders/abc -> 400 application/problem+json
    {"detail":"Failed to convert 'id' with value: 'abc'","instance":"/orders/abc","status":400,"title":"Bad Request"}
    [키] [detail, instance, status, title]
  GET /boom -> 500 application/json
    {"timestamp":"2026-10-03T19:40:56.610Z","status":500,"error":"Internal Server Error","path":"/boom"}
    [키] [timestamp, status, error, path]
```

(본문은 260자에서 잘랐다 — 원래 길이는 `/orders/abc` 6105자, `/boom` 4622자. `[키]`·`[message]` 줄은 실험 코드가 본문에서 뽑아 찍은 것. 타임스탬프는 실행마다 다르다)

관찰:
- **기본값에서 한 앱이 두 형식을 낸다.** 직접 만든 도메인 오류는 `application/problem+json`, 프레임워크 오류와 처리 안 된 예외는 Spring Boot 기본 형식(`timestamp·status·error·path`, `application/json`)이다. 클라이언트가 `type`·`detail`을 기대하면 두 번째 형식에서 값이 비어 있다.
- **`problemdetails`를 켜도 다 덮지 않는다.** 프레임워크 오류(`/orders/abc`)는 problem+json이 됐다. 처리 안 된 예외(`/boom`)는 여전히 기본 형식이다. Spring Framework 문서상 이 지원은 Spring MVC 예외와 `ErrorResponseException`을 처리하는 `ResponseEntityExceptionHandler` 기반이다.
- **기본값은 안전하다.** `trace`·`message`가 기본으로 나가지 않는다(메타데이터 기본값 `never`).
- **새 이름으로 켜면 내부가 그대로 나간다.** 500 본문에 예외 클래스, 제약 조건 이름(`uk_member_email`), 테이블·컬럼 이름, 소스 위치(`App.java:25`)가 담겼다. 400에서도 프레임워크 내부 클래스 경로가 나갔다.
- **설정 이름이 바뀌었다.** Spring Boot 4.0부터 `server.error.*`는 `spring.web.error.*`로 바뀌었다(`spring-boot-web-server-4.1.1.jar` 메타데이터: 옛 이름에 `deprecation level=error, replacement=spring.web.error.include-stacktrace, since=4.0.0`). 이 실험에서 옛 이름은 반영되지 않았다. 설정 파일만 보고 "켜져 있다/꺼져 있다"를 판단하면 틀린다 — 실제 응답으로 확인한다.

## 쓰이는 자료구조·알고리즘

- **JSON Pointer**(RFC 6901): `#/profile/color`처럼 `/`로 이은 경로로 JSON 트리를 루트부터 내려간다. 검증 오류가 요청 본문의 어느 노드인지 가리킨다. 트리 경로 탐색이다.
- **문제 유형 카탈로그 = `type` URI → (title, status, 문서)의 맵**: 서버는 예외 타입 → 문제 유형으로, 클라이언트는 `type` → 처리기로 분기한다. 둘 다 해시 맵 조회다.
- **발생 id(상관 id)**: `instance`나 확장 멤버에 요청·추적 id를 담아, 응답 하나와 로그·트레이스를 잇는다 — [reliability/17-distributed-tracing](../../reliability/17-distributed-tracing/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. **문제 유형 카탈로그를 만든다.** 유형마다 `type` URI, `title`, 상태 코드, 확장 멤버, 클라이언트 대처를 적는다(§4의 MUST 세 가지 포함).
2. **경계 한 곳에서, 처리 안 된 예외까지 문제 상세로 바꾼다.** 도메인 예외 → 해당 유형, 프레임워크 예외 → 프레임워크 기본 처리기, 나머지 → 500 `about:blank` + 발생 id.
3. **내부 정보는 로그로만.** 응답에는 발생 id만. 운영 설정에서 트레이스·메시지 노출 옵션이 꺼졌는지 **실제 응답으로** 확인한다.
4. **게이트웨이·LB가 만드는 오류도 맞춘다.** 502·504 등 앞단 오류 페이지를 problem+json으로 바꾸거나, 클라이언트가 `Content-Type`을 보고 형식을 가르게 한다.
5. **클라이언트는 `type`(+상태 코드)으로 분기하고 `detail`은 표시만** 한다. 모르는 확장 멤버·모르는 `type`은 무시하고 상태 코드 분류로 처리한다.

### 2. 서버 코드 (Spring Framework 7 / Spring Boot 4)

```java
@RestControllerAdvice
class ApiProblems extends ResponseEntityExceptionHandler {   // Spring MVC 예외 → problem+json
    private static final Logger log = LoggerFactory.getLogger(ApiProblems.class);

    @ExceptionHandler(InsufficientBalance.class)
    ProblemDetail balance(InsufficientBalance e) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.UNPROCESSABLE_CONTENT,
                "잔액이 부족합니다.");
        pd.setType(URI.create("https://api.example.com/problems/insufficient-balance"));
        pd.setTitle("Insufficient balance");
        pd.setProperty("balance", e.balance());       // 클라이언트가 쓸 값은 확장 멤버로
        pd.setProperty("required", e.required());
        return pd;
    }

    @ExceptionHandler(Exception.class)                 // 마지막 그물: 내부 정보는 로그로만
    ProblemDetail unexpected(Exception e, HttpServletRequest req) {
        String id = UUID.randomUUID().toString();
        log.error("unhandled id={} path={}", id, req.getRequestURI(), e);
        ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.INTERNAL_SERVER_ERROR);   // type = about:blank
        pd.setProperty("errorId", id);
        return pd;
    }
}
```

- `HttpStatus.UNPROCESSABLE_CONTENT`는 Spring Framework 7.0의 상수다. 6.x(v6.0.0·v6.1.0·v6.2.12 태그 소스)에는 `UNPROCESSABLE_ENTITY`만 있고, 7.0에서 그 이름은 폐기 예정(`@Deprecated(since = "7.0")`)이 됐다. 6.x에서는 `UNPROCESSABLE_ENTITY`를 쓴다.
- Spring 문서: `ProblemDetail`의 `instance`는 비어 있으면 현재 URL 경로로 채워진다. 실험 출력의 `"instance":"/orders/7"`이 그것이다.

### 3. 클라이언트 코드 (Java, Jackson 2.x)

```java
record Problem(URI type, String title, Integer status, String detail, String instance,
               @JsonAnySetter Map<String, Object> ext) {}       // 확장 멤버는 맵으로 모은다

static Optional<Problem> parseProblem(HttpResponse<String> r, ObjectMapper m) {
    boolean isProblem = r.headers().firstValue("Content-Type")
            .map(ct -> ct.startsWith("application/problem+json")).orElse(false);
    if (!isProblem) return Optional.empty();                    // HTML 오류 페이지 등은 상태 코드로만 처리
    try {
        return Optional.of(m.readerFor(Problem.class)
                .without(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
                .readValue(r.body()));
    } catch (IOException e) { return Optional.empty(); }
}
// 분기: problem.type() 기준. detail은 화면 표시용.
```

- 이 코드를 Jackson 2.19.2로 실험 출력의 실제 본문 두 개에 돌린 결과(레코드 생성자 매개변수의 `@JsonAnySetter`가 동작했다. 더 낮은 버전은 따로 확인한다):

(실험, JDK 21 temurin + Jackson 2.19.2, 2026-10-04)

```text
Problem[type=https://api.example.com/problems/order-not-found, title=Order not found, status=404, detail=주문 7이(가) 없습니다., instance=/orders/7, ext={orderId=7}]
Problem[type=null, title=null, status=500, detail=null, instance=null, ext={path=/boom, error=Internal Server Error, timestamp=2026-10-03T19:28:51.397Z}]
```

- 두 번째는 Spring Boot 기본 형식 본문이다. 예외 없이 읽혔지만 `type`·`title`이 null이다. `type`으로 분기하는 클라이언트는 이 응답을 "알 수 없는 문제"로 처리하게 된다. 그래서 위 코드는 `Content-Type`부터 확인한다.

### 4. 진단

```bash
# 오류 응답의 Content-Type이 일관된가 — 경로별로 형식이 다른지 확인
for p in /v1/orders/7 /v1/orders/abc /v1/unknown; do
  curl -s -o /dev/null -w "%{http_code} %{content_type} $p\n" https://api.example.com$p; done
# 오류 응답에 내부 정보가 새는가 (스테이징에서 일부러 실패시킨 응답 검사)
curl -s https://staging.example.com/v1/boom | grep -E -o '"trace"|Exception|\.java:[0-9]+|insert into|constraint' | sort | uniq -c
```

## 장애 시나리오와 대처

### 1. 에러 형식이 제각각 → 클라이언트 파싱 실패 (⚠ 커리큘럼)

- **현상**: 앱의 공통 에러 처리기가 일부 오류에서 "알 수 없는 오류"만 보여 주거나, 파싱 예외로 화면이 멈춘다.
- **보이는 형태**: 클라이언트 크래시 리포트에 JSON 파싱 예외(`Unexpected character '<'` — HTML 오류 페이지), 또는 `type`·`code`가 null.
- **원인**: 도메인 오류·프레임워크 오류·처리 안 된 예외·게이트웨이 오류가 서로 다른 형식이다. 실험의 기본값 설정에서 한 앱이 두 형식을 냈고, `problemdetails`를 켜도 처리 안 된 예외는 기본 형식으로 남았다.
- **대처**: 서버는 마지막 그물(`@ExceptionHandler(Exception.class)`)까지 problem+json으로 통일하고, 앞단 오류 페이지도 맞춘다. 클라이언트는 `Content-Type`으로 먼저 가르고, 문제 상세가 아니면 상태 코드 분류로만 처리한다.

### 2. 스택 트레이스·내부 메시지 노출 (⚠ 커리큘럼)

- **현상**: 보안 점검에서 500 응답에 SQL 문, 제약 조건 이름, 내부 클래스 경로가 담겨 있다는 지적을 받는다.
- **보이는 형태**: 응답 본문에 `trace`, `Exception`, `.java:25`, `insert into`. 실험에서 500 본문이 4622자였다.
- **원인**: 개발용 노출 옵션(`spring.web.error.include-stacktrace=always`·`include-message=always`)이 운영 설정에 남았다. 또는 직접 만든 처리기가 `e.getMessage()`를 `detail`에 넣었다. RFC 9457 §5가 경고하는 구현 세부 노출이다.
- **대처**: 운영에서는 트레이스·예외 메시지를 응답에 넣지 않는다. 처리기는 정해진 문구 + 발생 id만 응답하고 원문은 로그로. 배포 파이프라인에 "일부러 실패시킨 응답에 내부 정보 패턴이 없는지" 검사를 둔다.
- 함정: Spring Boot 4에서 설정 이름이 `server.error.*` → `spring.web.error.*`로 바뀌었다. 설정 파일 검토만으로는 실제 동작을 알 수 없다. 응답으로 확인한다.

### 3. `detail` 문구를 파싱 → 문구 개선에 깨짐

- **현상**: 서버가 `detail` 문구를 다듬은 뒤 클라이언트의 특정 분기(예: "잔액 부족" 처리)가 동작하지 않는다.
- **보이는 형태**: 같은 `type`의 응답인데 클라이언트 동작이 배포 시점부터 달라진다.
- **원인**: 클라이언트가 `detail`에서 숫자·키워드를 뽑았다. RFC 9457 §3.1.4가 하지 말라는(SHOULD NOT) 일이다(01의 Hyrum).
- **대처**: 필요한 값은 확장 멤버(`balance`, `required`)로 준다. 클라이언트는 `type`과 확장 멤버만 쓴다.

### 4. `status` 멤버와 실제 상태 코드가 다르다

- **현상**: 모니터링은 200으로 세는데 본문에는 `"status": 500`이 있다. 또는 그 반대.
- **보이는 형태**: 같은 응답에서 HTTP 상태와 `status` 값이 불일치.
- **원인**: 서버가 problem 본문은 만들었지만 HTTP 상태를 설정하지 않았거나(200 + 에러 바디, 03의 장애 1), 중간자가 상태를 바꿨다.
- **대처**: 생성자는 실제 응답과 같은 코드를 써야 한다(MUST, §3.1.2). 범용 소프트웨어(프록시·LB·모니터링)는 HTTP 상태를 따른다. 앱 소비자는 `status`로 생성자의 원래 코드를 알 수 있다(중간자가 바꿨거나 본문만 저장된 경우, §3.1.2). 둘의 우선순위는 RFC 9457이 정하지 않는다(§5). 어느 쪽을 믿을지는 팀이 정하고, 불일치 자체를 지표로 센다(생성자 버그나 중간자 변경의 신호).

### 5. 검증 오류를 하나씩만 돌려준다 → 왕복이 늘어난다

- **현상**: 폼 제출 때 필드 오류가 하나 고치면 다음 하나가 나오는 식으로 반복된다.
- **보이는 형태**: 같은 사용자의 422(또는 400)가 짧은 간격으로 여러 번.
- **원인**: 첫 검증 실패에서 바로 응답했다.
- **대처**: 같은 유형의 검증 오류는 `errors[]` 확장 + JSON Pointer로 한 번에 돌려준다(RFC 9457 §3 예시). 서로 다른 유형이 섞이면 가장 급한 하나만 응답하는 것이 RFC 권장이다.

## 핵심 문장

- 상태 코드는 분류만 말하고, Problem Details(RFC 9457)는 기계가 분기할 `type`과 사람이 읽을 `title`·`detail`, 유형별 확장 멤버를 같은 틀로 담는다.
- 소비자는 `type`으로 분기하고(MUST), `detail`은 파싱하지 않으며(SHOULD NOT), 모르는 확장 멤버는 무시한다(MUST).
- 실험에서 Spring Boot 4.1.1 기본값의 한 앱이 두 에러 형식을 냈고, `problemdetails`를 켜도 처리 안 된 예외는 기본 형식으로 남았다 — 마지막 그물까지 직접 통일해야 한다.
- 에러 본문은 디버깅 도구가 아니다. 트레이스 노출 옵션 하나로 SQL·제약 조건 이름·소스 위치가 나갔다. 응답에는 발생 id만, 원문은 로그로.
- 설정 이름도 바뀐다(Boot 4: `server.error.*` → `spring.web.error.*`). 노출 여부는 설정이 아니라 실제 응답으로 확인한다.

## 관련 주제·근거

- 선행
  - [03-status-codes-for-apis](../03-status-codes-for-apis/2-summary.md) — 상태 코드 선택
  - [01-api-as-contract](../01-api-as-contract/2-summary.md) — 에러 문구 파싱과 Hyrum의 법칙
- 후속(api-design)
  - [05-idempotency-keys](../05-idempotency-keys/2-summary.md)(같은 키 다른 본문 422) · [14-rate-limit-and-quota-contracts](../14-rate-limit-and-quota-contracts/2-summary.md)(429 + Retry-After) · [21-api-documentation-openapi](../21-api-documentation-openapi/2-summary.md)(명세 문서화)
  - 사례: [22-case-order-point](../22-case-order-point/2-summary.md) · [27-case-refund](../27-case-refund/2-summary.md)
- 연결
  - [software-design/17-error-messages-and-log-level-policy](../../software-design/17-error-messages-and-log-level-policy/2-summary.md) — 사용자용·개발자용 메시지 분리, SQL 에러 원문 노출 실험
  - [software-design/15-error-handling-design](../../software-design/15-error-handling-design/2-summary.md) — 예외 경계 한 곳에서 번역
  - [reliability/17-distributed-tracing](../../reliability/17-distributed-tracing/2-summary.md) — 발생 id와 트레이스 연결
  - security 영역 — 미작성, [security/README](../../security/README.md)
- 근거
  - RFC 9457 Problem Details for HTTP APIs(2023-07, RFC 7807 대체) — §3(예시·여러 문제), §3.1.1~§3.1.5(멤버와 소비자 규칙), §3.2(확장 무시 MUST), §4(정의 시 MUST 세 가지, 디버깅 도구 아님), §4.2(등록소, `about:blank`), §5(보안), 부록 D(7807 대비 변경) <https://www.rfc-editor.org/rfc/rfc9457>
  - RFC 6901 JSON Pointer
  - Google AIP-193 Errors — HTTP/1.1+JSON 표현(`error.code`·`status`·`details`), `ErrorInfo`·`LocalizedMessage`·`Help` <https://google.aip.dev/193>
  - Stripe API Reference "Errors" — `type`(api_error·card_error·idempotency_error·invalid_request_error)·`code`·`message`·`param`·`doc_url` <https://docs.stripe.com/api/errors>
  - Spring Framework 7.0.9 Reference "Error Responses"(`ProblemDetail`·`ErrorResponse`·`ResponseEntityExceptionHandler`, `instance` 자동 채움, problem+json 우선) <https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-rest-exceptions.html>
  - Spring Boot 4.1.1 설정 메타데이터 — `spring-boot-webmvc`의 `spring.mvc.problemdetails.enabled`(기본 false), `spring-boot-autoconfigure`의 `spring.web.error.include-stacktrace`·`include-message`(기본 never), `spring-boot-web-server`의 `server.error.*` 폐기(level error, since 4.0.0)
- 실험 목록
  - Spring Boot 4.1.1 앱(도메인 ProblemDetail 처리기 1개)에 설정 4종(기본값 · 옛 이름 `server.error.*` · 새 이름 `spring.web.error.*` · `spring.mvc.problemdetails.enabled=true`)을 주고 `/orders/7`·`/orders/abc`·`/boom` 응답의 상태·Content-Type·본문 키·길이 비교 — JUnit 5 테스트 안에서 `SpringApplication.run` + JDK `HttpClient`, maven 3.9 + JDK 21 컨테이너 `--network none`
