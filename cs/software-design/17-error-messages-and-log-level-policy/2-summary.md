# software-design/17-error-messages-and-log-level-policy — 에러 메시지와 로그 레벨 정책: 누구에게 무엇을 얼마나 — 정리 (힌트)

## 해결하는 문제

에러 하나에는 독자가 셋 있다. 사용자, 운영자(알람을 받는 사람), 개발자(원인을 찾는 사람). 한 문자열로 셋을 다 만족시키려 하면 셋 다 실패한다.

```text
                        ┌─> 사용자:   "주문 금액을 다시 확인해 주세요."  (무엇을 하면 되나)
 에러 하나 ── 분리 ──────┼─> 운영자:   ERROR 1건 → 알람                  (지금 사람이 움직여야 하나)
                        └─> 개발자:   incidentId·SQLState·스택 트레이스   (어디서 왜)
                              ↑ 셋을 잇는 열쇠: 에러 코드 + incidentId(요청 ID)
```

- *로그 레벨*: 로그 한 줄의 중요도 표시(ERROR·WARN·INFO·DEBUG 등). 알람·보존·샘플링의 기준이 된다.
- *조작적 정의(operational definition)*: "심각하면 ERROR"처럼 느낌으로 정하지 않고, **관찰 가능한 기준**(사람이 조치해야 하나, 자동 복구됐나)으로 정하는 것.
- *에러 코드*: 실패 종류에 붙인 안정된 식별자(`ORDER_INVALID_AMOUNT`). 메시지 문구가 바뀌어도 코드는 그대로라 검색·통계·클라이언트 분기에 쓴다.

쉬운 예: 병원에서 환자에게는 "검사 결과 다시 봐야 합니다, 내일 오세요", 당직 의사에게는 호출벨, 차트에는 수치 전부를 적는다. 셋을 같은 종이에 적어 환자에게 주지 않는다.\
똑같은 구조다.\
실무 예: 검증 실패(400) 수십 건이 ERROR로 찍혀 알람이 계속 울리자 당직자가 알람을 무시하기 시작했고, 그 사이 진짜 DB 장애 알람도 묻혔다. 한편 사용자 화면에는 SQL 에러 원문이 보였고, 다른 화면은 "오류가 발생했습니다"만 보여서 고객센터가 원인을 찾을 길이 없었다.

기초: 어디서 잡고 한 번 기록하나는 [15-error-handling-design](../15-error-handling-design/2-summary.md), 로그 파이프라인(구조화·상관 ID·비동기 appender·샘플링)은 [reliability/15-logging](../../reliability/15-logging/2-summary.md). 이 노트는 **레벨의 기준, 메시지의 분리, 에러 코드**를 다룬다.

## 동작·원리

### 1. 레벨의 조작적 정의

표준은 레벨 이름과 번호만 준다. RFC 5424 §6.2.1은 Severity 0~7(Emergency·Alert·Critical·Error·Warning·Notice·Informational·Debug)을 표로 두지만 "Facility and Severity values are not normative but often used"라고 적는다. 무엇을 ERROR로 찍을지는 **팀이 정할 일**이다.

이 노트가 권하는 정의(팀 규칙의 예 — 출처의 규정이 아니다):

```text
 레벨    질문                                   예                               뒤따르는 것
 ──────────────────────────────────────────────────────────────────────────────────────────────
 ERROR   지금 사람이 조치해야 하나?  예          DB 연결 실패로 요청 실패, 데이터 불일치   알람(페이지)
 WARN    자동으로 회복했지만 추세는 봐야 하나?    재시도 후 성공, 폴백 사용, 풀 90%       대시보드·일일 검토
 INFO    정상 흐름의 주요 사건인가?              요청 완료, 4xx(클라이언트 입력 오류)     검색용
 DEBUG   조사할 때만 켤 세부인가?                SQL 파라미터, 분기 결정                 평소 꺼 둠
```

- 4xx(검증 실패·없는 리소스)는 **서버가 정상 동작한 결과**다. 클라이언트의 몫이라 ERROR가 아니다. 다만 4xx가 갑자기 늘면 배포 버그(클라이언트·서버 계약 깨짐) 신호일 수 있으니 **지표**로 본다.
- OWASP Logging Cheat Sheet는 레벨 등 이벤트 분류(type·confidence·severity)를 조직이 일관되고 문서화된 방식으로 정하라고 적는다(Note B).
- OpenTelemetry 로그 데이터 모델의 SeverityNumber 범위와 흔한 관례 표는 [reliability/15-logging](../../reliability/15-logging/2-summary.md) 「레벨」 절에 있다.

### 실험 A: 같은 트래픽, 두 레벨 정책

요청 1000건(고정 시드로 만든 예시 구성)을 두 정책으로 기록했다. A는 "실패는 전부 ERROR", B는 위 표의 조작적 정의다.

```java
static String levelA(Outcome o) { return switch (o) { case OK -> "INFO"; default -> "ERROR"; }; }
static String levelB(Outcome o) {
    return switch (o) {
        case OK, VALIDATION_400, NOT_FOUND_404 -> "INFO";
        case RETRIED_THEN_OK -> "WARN";
        case DB_DOWN_500 -> "ERROR";
    };
}
```

(실험, JDK 21.0.12 eclipse-temurin `--cpus=2`, `scratchpad/sd/15/e17/LogPolicy.java`, 2026-10-01)

```text
요청 구성: {OK=952, VALIDATION_400=39, NOT_FOUND_404=3, RETRIED_THEN_OK=4, DB_DOWN_500=2}
정책 A(실패=ERROR)    레벨별={ERROR=48, INFO=952}  ERROR 중 사람이 조치할 것=2/48
정책 B(조작적 정의)      레벨별={ERROR=2, INFO=994, WARN=4}  ERROR 중 사람이 조치할 것=2/2
```

- 정책 A에서 ERROR 48건 중 사람이 움직여야 할 것은 2건(4%)이었다. "ERROR 1건 = 알람"이면 알람 48번 중 46번이 헛걸음이다.
- 정책 B는 ERROR 2건이 전부 조치 대상이다. 재시도로 회복한 4건은 WARN으로 남아 추세를 볼 수 있다.
- 구성 비율은 예시다. 실제 서비스에서 4xx 비율은 더 높을 수도 낮을 수도 있다.

### 2. 메시지 분리 — 사용자용 · 개발자용

```text
 예외(SQLException: Table "ORDERS_V2" not found … SQL statement: select …)
        │
        ├── 경계 처리기 ──> 에러 코드 표 조회: INTERNAL → (500, "일시적인 오류입니다…")
        │                       │
        │                       └──> 응답: problem+json { status, detail(사용자용), code, incidentId }
        │
        └── 서버 로그(한 번): ERROR incidentId=… code=INTERNAL sqlState=… msg=… (+ 스택 트레이스)
```

### 실험 B: SQL 에러 원문 노출 vs 분리

H2 메모리 DB에 없는 표를 조회해 실제 `SQLException`을 만들었다.

(실험, 같은 환경 + H2 2.3.232)

```text
[나쁨] 응답 본문에 원문 노출:
  {"status":500,"message":"Table \"ORDERS_V2\" not found (this database is empty); SQL statement: select amount from orders_v2 where customer_id = 1001 [42104-232]"}
[좋음] 응답(problem+json):
  {"type":"about:blank","title":"Internal Server Error","status":500,"detail":"일시적인 오류입니다. 잠시 후 다시 시도해 주세요.","code":"INTERNAL","incidentId":"inc-bb1ad573"}
[좋음] 서버 로그(개발자용, 한 번):
  ERROR incidentId=inc-bb1ad573 code=INTERNAL sqlState=42S04 vendorCode=42104 msg=Table "ORDERS_V2" not found (this database is empty); SQL statement:
```

- 원문 노출은 표 이름·SQL 문·DB 제품 버전 단서(`[42104-232]`)를 공격자에게 준다. OWASP Error Handling Cheat Sheet는 예상치 못한 에러에 일반 응답을 주고 상세는 서버 쪽에 기록하라고 적는다.
- RFC 9457 §3.1.4: `detail`은 클라이언트가 문제를 고치는 데 초점을 두고 디버깅 정보를 담지 않는다. §5는 스택 덤프 같은 구현 세부를 HTTP 인터페이스로 노출하지 말라고 권한다.
- `incidentId`가 사용자 화면·고객 문의와 서버 로그를 잇는다. "오류가 발생했습니다"만 보여 주면 이 연결이 없다.
- 서버 로그 줄은 메시지의 첫 줄만 담았다(이 실험 코드가 `lines().findFirst()`로 잘랐다). 실제로는 스택 트레이스를 함께 남긴다.
- 같은 위험의 다른 예: JDK 15부터 helpful NPE 메시지가 기본으로 켜졌다. Oracle JDK 15 릴리스 노트는 이 메시지가 애플리케이션 에러 메시지에 포함되면 원격 공격자에게 단서가 될 수 있다고 경고한다.

### 3. 에러 코드 체계

```java
enum ErrorCode {
    ORDER_INVALID_AMOUNT(400, "주문 금액을 다시 확인해 주세요."),
    ORDER_NOT_FOUND(404, "주문을 찾을 수 없습니다."),
    INTERNAL(500, "일시적인 오류입니다. 잠시 후 다시 시도해 주세요.");
    final int status; final String userMessage;
    ErrorCode(int s, String m) { status = s; userMessage = m; }
}
```

- 코드 = 안정된 키. 문구 = 바뀔 수 있는 값. 클라이언트는 코드로 분기하고 문구를 파싱하지 않는다(RFC 9457 §3.1.4: "Consumers SHOULD NOT parse the "detail" member").
- 규칙 예(팀 규칙): 영역 접두사(`ORDER_`·`PAY_`), 한 번 공개한 코드는 의미를 바꾸지 않는다, 코드마다 HTTP 상태·로그 레벨·재시도 가능 여부를 함께 정한다.
- 다국어는 코드를 메시지 번들 키로 쓴다(Spring `MessageSource` 등).

### 4. 한 번만 로깅

계층마다 기록하면 장애 하나가 여러 건이 된다. [15](../15-error-handling-design/2-summary.md)의 실험에서 3계층 catch-log-rethrow는 SEVERE 4건·62줄, 경계 한 번은 1건·16줄이었다. 레벨 정책이 아무리 좋아도 같은 사건이 네 번 찍히면 ERROR 수가 네 배가 된다.

### 실험 C: 로그 주입

사용자 입력에 개행이 들어 있으면 가짜 로그 줄이 생긴다.

(실험, 같은 환경)

```text
[로그 주입] 그대로 기록:
2026-10-01T09:59:59Z WARN login failed user=mallory
2026-10-01T10:00:00Z INFO login success user=admin
[로그 주입] CR/LF 이스케이프 후:
2026-10-01T09:59:59Z WARN login failed user=mallory\n2026-10-01T10:00:00Z INFO login success user=admin
```

- 둘째 줄은 기록된 적 없는 "admin 로그인 성공"이다. OWASP Logging Cheat Sheet는 CR·LF·구분자를 정리해 로그 주입을 막으라고 적는다(CWE-117).
- JSON 같은 구조화 로그는 인코더가 개행을 이스케이프하므로 이 형태의 위조가 어렵다. 평문 패턴 로그일 때 특히 조심한다.

## 쓰이는 자료구조·알고리즘

- **에러 코드 → 메시지 맵** — enum 또는 해시 맵. 키는 안정, 값은 교체 가능. 다국어면 (코드, 로캘) → 문구, 없으면 기본 로캘로 내려가는 **대체 체인(fallback chain)**.
- **예외 타입 → 에러 코드 디스패치** — 경계 처리기가 예외 클래스로 코드·상태·레벨을 고른다([16](../16-error-strategy-exceptions-vs-results/2-summary.md)의 전수 `switch`를 쓰면 누락이 컴파일 오류가 된다).
- **레벨 = 순서 있는 열거형 + 임계 비교** — 로거는 `이벤트 레벨 ≥ 설정 레벨`일 때만 기록한다. 알람 규칙은 같은 비교를 한 번 더 한다(ERROR 이상이면 페이지).
- **카운터** — 4xx는 줄 로그보다 코드별 카운터 지표가 싸고 추세를 보기 좋다. 지표 쪽은 [reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. **레벨 정의를 문서로.** ERROR·WARN·INFO·DEBUG마다 "질문 한 줄 + 예 셋". 팀 위키나 코드 저장소에 둔다.
2. **에러 코드 표를 만든다.** 코드 → HTTP 상태, 사용자 문구, 로그 레벨, 재시도 가능 여부.
3. **경계 처리기 하나에서** 코드 조회 → 응답(problem+json) → 로그 한 번. 안쪽은 기록하지 않는다.
4. **incidentId(요청 ID)를 응답과 로그에 같이** 넣는다. 사용자 화면에도 보이게 해서 문의 때 받는다.
5. **로그에 남기지 않을 것**을 정한다. OWASP Logging Cheat Sheet "Data to exclude": 세션 식별자, 접근 토큰, 비밀번호, DB 연결 문자열, 암호 키, 결제 카드 정보 등.
6. **알람은 ERROR 줄 수가 아니라 비율·SLO로.** 레벨 정의가 좋아도 순간적인 ERROR 1건마다 페이지를 보내면 피로가 쌓인다. 알람 설계는 [reliability/43-alerting-and-on-call](../../reliability/43-alerting-and-on-call/2-summary.md).

### 2. 코드 (Spring Framework 6.x)

```java
@RestControllerAdvice
class ApiErrors {
    private static final Logger log = LoggerFactory.getLogger(ApiErrors.class);

    @ExceptionHandler(DomainException.class)            // 4xx: 사람이 조치할 일이 아니다
    ProblemDetail domain(DomainException e) {
        log.info("domain rejected code={} incidentId={}", e.code(), MDC.get("requestId"));
        return problem(e.code(), MDC.get("requestId"));
    }

    @ExceptionHandler(Exception.class)                   // 5xx: 사람이 봐야 한다, 한 번만
    ProblemDetail unexpected(Exception e) {
        String id = MDC.get("requestId");
        log.error("unexpected incidentId={}", id, e);    // 스택 트레이스는 로그에만
        return problem(ErrorCode.INTERNAL, id);
    }

    private ProblemDetail problem(ErrorCode c, String id) {
        ProblemDetail p = ProblemDetail.forStatusAndDetail(HttpStatus.valueOf(c.status), c.userMessage);
        p.setProperty("code", c.name());
        p.setProperty("incidentId", id);
        return p;
    }
}
```

- `ProblemDetail`은 Spring Framework 6.x의 RFC 9457 표현이다(Spring 문서 "Error Responses"). `setProperty`는 확장 필드로 직렬화된다.

### 3. 진단

```bash
# 레벨별 줄 수와 ERROR 중 4xx 비율 (JSON 로그 예시 — 필드 이름은 팀 형식에 맞춘다)
jq -r '.level' app.log | sort | uniq -c
jq -r 'select(.level=="ERROR") | .status' app.log | sort | uniq -c

# 같은 요청 ID로 ERROR가 2건 이상 = 어딘가에서 중복 기록
jq -r 'select(.level=="ERROR") | .requestId' app.log | sort | uniq -c | awk '$1>1' | head

# 응답에 내부 정보가 새는지 (스테이징에서 일부러 실패시킨 응답 본문 검사)
curl -s "$HOST/orders/does-not-exist" | grep -Ei 'sql|exception|stack|at [a-z]+\.'
```

## 장애 시나리오와 대처

### 1. 예상된 4xx를 ERROR로 → 알람 피로로 진짜 장애 무시 (⚠ 커리큘럼)

- 현상: 알람이 하루 수십 번 울리고, 당직자가 습관적으로 확인 없이 닫는다. 그 사이 DB 장애 알람이 묻힌다.
- 보이는 형태: ERROR의 대부분이 `status=400·404`. 실험 A에서는 ERROR 48건 중 조치 대상 2건.
- 원인: "실패 = ERROR"라는 느낌 기반 정의.
- 대처: 조작적 정의로 레벨을 다시 매긴다. 4xx는 INFO + 코드별 카운터. 알람은 5xx 비율·SLO 소진율로.

### 2. catch-log-rethrow 계층마다 반복 → 스택 트레이스 다중 기록 (⚠ 커리큘럼)

- 현상: 장애 한 번에 스택 트레이스가 여러 벌, 로그 비용·검색 노이즈 증가.
- 보이는 형태: 같은 요청 ID로 ERROR 여러 건, 같은 근본 원인 문장이 반복(15의 실험: SEVERE 4건, `connection reset` 4번).
- 원인: 기록 책임이 경계에 모이지 않았다.
- 대처: 경계에서 한 번. 안쪽은 원인을 붙여 번역만. Sonar S2139 같은 정적 규칙으로 막는다([15](../15-error-handling-design/2-summary.md)).

### 3. 사용자에게 SQL 에러 원문 노출 → 정보 누출 (⚠ 커리큘럼)

- 현상: 에러 화면·API 응답에 표 이름·SQL 문·라이브러리 버전이 보인다.
- 보이는 형태: 실험 B의 `[나쁨]` 응답. OWASP Error Handling Cheat Sheet는 에러 처리에서 새는 정보가 기술 스택을 드러내고 주입(injection) 지점을 찾는 데 쓰일 수 있다고 적는다(그 문서의 예는 Struts2·Tomcat 버전 노출).
- 원인: 경계에서 `e.getMessage()`를 그대로 응답에 넣었다. 프레임워크 기본 에러 페이지가 상세를 보여 주는 설정일 수도 있다.
- 대처: 응답은 에러 코드 표의 사용자 문구만. 상세는 서버 로그로. 스테이징에서 일부러 실패시켜 응답 본문을 검사한다(적용 3).

### 4. "오류가 발생했습니다"만 표시 → 원인 역추적 불가 (⚠ 커리큘럼)

- 현상: 고객 문의가 "오류가 났어요"뿐이라 어느 요청인지 찾지 못한다.
- 보이는 형태: 응답에 코드·식별자가 없다. 서버 로그는 시간대로만 뒤져야 한다.
- 원인: 정보 누출을 막으려다 연결 고리까지 지웠다.
- 대처: 응답에 에러 코드 + incidentId(요청 ID)를 넣고 화면에 보여 준다. 이 값은 내부 정보를 드러내지 않으면서 로그를 찾는 열쇠다(실험 B의 `[좋음]`).

### 5. 로그 주입·민감 정보 기록

- 현상: 감사 로그에 일어나지 않은 "admin 로그인 성공"이 있다. 또는 로그에 비밀번호·토큰이 평문으로 있다.
- 보이는 형태: 실험 C의 둘째 줄. 로그 검색에서 `password=`·`Bearer ` 발견.
- 원인: 사용자 입력을 이스케이프 없이 평문 로그에 넣었다. 요청 객체 전체를 `toString()`으로 기록했다.
- 대처: CR·LF 이스케이프 또는 구조화(JSON) 로그. 기록 제외 목록과 마스킹 필터. OWASP Logging Cheat Sheet "Data to exclude".

## 핵심 문장

- 표준(RFC 5424)은 레벨 이름만 주고 규범으로 정하지 않는다. ERROR의 뜻은 팀이 조작적으로 정해야 한다.
- ERROR는 "지금 사람이 조치해야 함", WARN은 "자동 회복했지만 추세를 볼 것"으로 정의하면 알람이 조치와 일치한다. 실험에서 ERROR가 48건에서 2건으로 줄었다.
- 사용자 메시지와 개발자 메시지를 나누고, 에러 코드와 incidentId로 둘을 잇는다.
- 응답에 SQL 원문·스택 트레이스를 넣지 않는다. RFC 9457의 `detail`은 클라이언트가 고칠 수 있게 돕는 문구다.
- 기록은 경계에서 한 번 한다. 사용자 입력은 개행을 이스케이프해 로그 위조를 막는다.

## 관련 주제·근거

- 선행
  - [15-error-handling-design](../15-error-handling-design/2-summary.md) — 경계에서 한 번 기록
  - [reliability/15-logging](../../reliability/15-logging/2-summary.md) — 구조화 로그·상관 ID·레벨 비용
  - api-design 04 error-format-problem-details — 미작성([api-design 커리큘럼](../../api-design/curriculum.md))
- 후속·연결
  - [16-error-strategy-exceptions-vs-results](../16-error-strategy-exceptions-vs-results/2-summary.md) — 실패 종류 → HTTP 상태
  - [reliability/43-alerting-and-on-call](../../reliability/43-alerting-and-on-call/2-summary.md) — 알람 피로
  - [reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md) — 4xx를 지표로
- 글·문서
  - RFC 5424 "The Syslog Protocol"(2009) §6.2.1 Table 2 Severity, "not normative but often used" <https://www.rfc-editor.org/rfc/rfc5424>
  - RFC 9457 "Problem Details for HTTP APIs"(2023) §3.1.4 detail, §5 Security Considerations <https://www.rfc-editor.org/rfc/rfc9457>
  - OWASP Error Handling Cheat Sheet(일반 응답 + 서버 쪽 상세 기록, 스택 노출 예) <https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html>
  - OWASP Logging Cheat Sheet(Note B 분류 일관성, Data to exclude, 로그 주입 정리, CWE-117) <https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html>
  - Oracle JDK 15 릴리스 노트 "Enable ShowCodeDetailsInExceptionMessages by default"(JDK-8233014) <https://www.oracle.com/java/technologies/javase/15-relnote-issues.html>
  - Spring Framework 문서 "Error Responses"(`ProblemDetail`) <https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-rest-exceptions.html>
- 실험 목록 (코드: scratchpad `sd/15/e17/LogPolicy.java`, JDK 21.0.12 eclipse-temurin `--cpus=2`, H2 2.3.232 jar, `java -cp h2-2.3.232.jar LogPolicy.java`)
  - A 레벨 정책 두 가지 — ERROR 48(조치 2) vs 2(조치 2)
  - B 실제 `SQLException` 원문 노출 vs problem+json + incidentId
  - C CR/LF 로그 주입과 이스케이프
  - (연결) 한 번만 로깅 — [15](../15-error-handling-design/2-summary.md)의 실험 1
