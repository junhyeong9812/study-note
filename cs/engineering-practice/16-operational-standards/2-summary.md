# engineering-practice/16-operational-standards — 운영 표준: 서비스마다 다른 로그·지표를 하나의 운영 계약으로 — 정리 (힌트)

## 해결하는 문제

운영 표준이 없으면 서비스마다 로그 모양과 지표 이름이 다르다. 평소에는 불편한 정도지만, 사고 때 한 요청을 여러 서비스에 걸쳐 따라가는 순간 막힌다.

- 주문 서비스는 `02:10:59.499 [main] INFO order -- ...`, 결제 서비스는 두 줄짜리 JUL 형식, 배송 서비스는 JSON을 쓴다.
- 한 서비스는 지연을 밀리초(`payment_latency_ms`)로, 다른 서비스는 초(`http_server_requests_seconds`)로 낸다. 대시보드에서 두 선을 겹치면 1000배 차이가 난다.
- 새 서비스는 "운영 준비가 됐나"를 판정할 기준 없이 출시된다. 경보·런북·대시보드가 없다는 사실을 첫 장애 때 안다.

쉬운 예: 집집마다 다른 콘센트다.

```text
  표준 없음                                 표준 있음
  방마다 플러그 모양이 다름                    KS 규격 콘센트 하나
  기기를 옮길 때마다 어댑터를 찾음              어느 방에 꽂아도 됨
  고장 나면 전기 기사가 방마다 구조를 새로 익힘   점검 절차가 하나
```

똑같은 구조다. 운영 표준은 "어느 서비스에 꽂아도 같은 도구(로그 검색·대시보드·경보·런북)가 동작하게 하는 규격"이다.

실무 예:
- 사고 타임라인을 만드는데, 한 서비스 로그의 시각은 날짜 없는 현지 시각이고 다른 서비스는 UTC다. 사건 순서가 뒤집힌 채 포스트모템이 작성된다(장애 2).
- 스택트레이스가 여러 줄로 찍혀 로그 수집기가 줄마다 별개 이벤트로 저장한다. "ERROR 한 건"이 검색에서는 13줄짜리 조각으로 흩어진다(장애 3).

기초 — ISO/IEC 20000-1 서비스 관리 체계(조항 8의 운영 프로세스), Google SRE의 SLI·SLO·에러 버짓·toil·포스트모템·골든 시그널 — 은 원본 [operational-standards](../../engineering/development-standards/operational-standards/2-summary.md) §1~§4에 있다. 이 노트는 그 위에서 **서비스가 지켜야 할 관측·운영 계약을 정하고 검사하는 법**을 다룬다.

참고: 원본 §6의 straggler 링크(`../../straggler/`)는 원본 위치에서 풀면 `cs/engineering/straggler`로, 저장소에 없는 경로다. 가리키던 노트는 재구조화 뒤 [systems/straggler](../../systems/straggler/2-summary.md)에 있고, 같은 주제는 [reliability/34-tail-latency-and-stragglers](../../reliability/34-tail-latency-and-stragglers/2-summary.md)에도 있다.

## 동작·원리

### 1. 운영 표준 = 서비스와 운영 도구 사이의 계약

```text
   서비스 A ─┐                                       ┌─ 로그 검색 (trace_id로 한 요청 따라가기)
   서비스 B ─┼──> [ 운영 표준(계약) ] ──> 공용 도구 ───┼─ 대시보드 (같은 이름·단위의 지표)
   서비스 C ─┘    · 로그 스키마                         ├─ 경보 → 런북 링크
                 · 지표 이름·단위·레이블 규칙            └─ 출시 전 점검(PRR)
                 · SLI/SLO 정의 방식
                 · 경보마다 런북
                 · 출시 전 운영 준비 점검
```

- *운영 표준(이 노트의 뜻)*: 서비스가 운영 도구와 사람에게 약속하는 형식·절차의 묶음. 20000-1이 요구하는 "관리 체계"를 엔지니어링 수준으로 내린 것이다(해석).
- *관측 가능성(observability)*: 시스템 바깥에서 로그·지표·추적만 보고 안의 상태를 추론할 수 있는 정도. 표준은 서비스마다 이 출력을 같은 모양으로 맞춘다.

표준의 근거로 쓸 수 있는 공개 규격(제품 중립 규격과 커뮤니티 관례를 구분한다).

| 대상 | 근거 | 무엇을 정하나 |
|---|---|---|
| 로그 레코드 모양 | OpenTelemetry Logs Data Model(Stable) | 최상위 필드 12개: Timestamp·ObservedTimestamp·TraceId·SpanId·TraceFlags·SeverityText·SeverityNumber·Body·Resource·InstrumentationScope·Attributes·EventName |
| 심각도 | 같은 문서 | SeverityNumber 1~4 TRACE, 5~8 DEBUG, 9~12 INFO, 13~16 WARN, 17~20 ERROR, 21~24 FATAL |
| 추적 ID | W3C Trace Context | trace-id = 16바이트, 소문자 16진수 32자. 전부 0은 무효 |
| 지표 이름 | Prometheus 문서 "Metric and label naming"(커뮤니티 관례) | 단일 단위·기본 단위(seconds·bytes)·복수형 단위 접미사·누적 카운트는 `_total`·레이블에 고카디널리티 값 금지 |
| 출시 전 점검 | Google SRE Book 32장 PRR | 아키텍처·의존성, 계측·지표·모니터링, 비상 대응, 용량 계획, 변경 관리, 성능 |

- *SeverityNumber*: 로그 심각도를 숫자로 정규화한 값. 라이브러리마다 다른 레벨 이름(`WARNING`·`WARN`·`warn`)을 같은 축에 놓는다.
- *카디널리티(cardinality)*: 지표의 레이블 값 조합 수. 실제로 나타난 레이블 값 조합 하나가 시계열 하나를 만든다([reliability/16](../../reliability/16-metrics-and-golden-signals/2-summary.md) 실험).
- *PRR(Production Readiness Review)*: 서비스가 운영 기준을 충족하는지 확인하고, 운영 중 사고 수·심각도를 줄이려는 점검(SRE Book 32장의 두 목적).
  - 흔한 오해: "PRR = 출시 승인 절차". SRE Book 32장에서 PRR은 SRE 팀이 서비스의 운영 책임을 맡기 전의 전제 절차다("A PRR is considered a prerequisite for an SRE team to accept responsibility"). 이 노트처럼 출시 전 점검으로 쓰는 것은 그 점검 영역을 빌려 온 것이다(해석).

### 2. 실험 A: 같은 이벤트, 다섯 가지 로그 — 팀 표준으로 검사하면

서비스 네 개가 각자 로그를 낸다(서비스 A는 기본 패턴과 Logback 내장 JSON 두 가지).

```java
// 서비스 A: SLF4J + Logback 1.5.12, 설정 파일 없이 기본 설정
Logger log = LoggerFactory.getLogger("order");
log.info("order created id=1001 user=u-7");
log.warn("payment slow ms=2300");
try { Integer.parseInt("x"); } catch (Exception e) { log.error("payment failed id=1001", e); }

// 서비스 B: java.util.logging 기본 SimpleFormatter
Logger log = Logger.getLogger("payment");
log.info("approved order=1001 amount=12000");
log.warning("pg timeout order=1002");

// 서비스 C: 팀 운영 표준(예시)대로 JSON 한 줄 — timestamp(ISO-8601+오프셋)·level·service·trace_id·message
System.out.printf("{\"timestamp\":\"%s\",\"level\":\"%s\",\"service\":\"shipping\",\"trace_id\":\"%s\",\"message\":\"%s\"}%n",
    Instant.now(), level, trace, msg);

// 서비스 D: JSON이긴 한데 이름·형식을 따로 정했다 (ts=epoch ms, severity, traceId / 로컬 시각 문자열, "warning")
```

(실험, Logback 1.5.12 · SLF4J 2.0.16 · JDK 21.0.12 temurin, 컨테이너 TZ=Asia/Seoul, 2026-10-05)

```text
== a.log (Logback 기본)
02:10:59.499 [main] INFO order -- order created id=1001 user=u-7
02:10:59.504 [main] WARN order -- payment slow ms=2300
02:10:59.505 [main] ERROR order -- payment failed id=1001
java.lang.NumberFormatException: For input string: "x"
	at java.base/java.lang.NumberFormatException.forInputString(NumberFormatException.java:67)
	...
== a_json.log (Logback JsonEncoder)
{"sequenceNumber":0,"timestamp":1791134059348,"nanoseconds":348019313,"level":"INFO","threadName":"main","loggerName":"order",...,"message":"order created id=1001 user=u-7","throwable":null}
== b.log (JUL 기본)
Oct 05, 2026 2:11:01 AM SvcB main
INFO: approved order=1001 amount=12000
== c.log (팀 표준)
{"timestamp":"2026-10-04T17:11:04.411773918Z","level":"INFO","service":"shipping","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","message":"label printed order=1001"}
== d.log (제각각 JSON)
{"ts":1791133892166,"severity":"info","traceId":"4bf92f3577b34da6a3ce929d0e0e4736","msg":"stock reserved order=1001"}
{"timestamp":"2026-10-05 02:11:09","level":"warning","service":"inventory","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","message":"stock low sku=A1"}
```

검사기(핵심 부분):

```java
static final List<String> REQUIRED = List.of("timestamp", "level", "service", "trace_id", "message");
static final Set<String> LEVELS = Set.of("TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL");

static List<String> violations(String line) {
  List<String> v = new ArrayList<>();
  String t = line.strip();
  if (!(t.startsWith("{") && t.endsWith("}"))) { v.add("JSON 한 줄 아님"); return v; }
  Map<String, String> f = parseTopLevel(t);                      // "키":"문자열" 또는 "키":숫자
  for (String k : REQUIRED) if (!f.containsKey(k)) v.add("필드 없음:" + k);
  if (f.containsKey("timestamp")) {
    try { OffsetDateTime.parse(f.get("timestamp")); }             // 날짜+시각+오프셋(Z 포함) 필수
    catch (Exception e) { v.add("timestamp 형식(ISO-8601+오프셋) 아님"); }
  }
  if (f.containsKey("level") && !LEVELS.contains(f.get("level"))) v.add("level 어휘 밖:" + f.get("level"));
  if (f.containsKey("trace_id") && !f.get("trace_id").matches("[0-9a-f]{32}")) v.add("trace_id 형식 아님");
  else if (f.containsKey("trace_id") && f.get("trace_id").matches("0{32}")) v.add("trace_id 전부 0(무효)");  // W3C: all-zero 무효
  return v;
}
```

```text
$ java LogStandardCheck.java a.log a_json.log b.log c.log d.log z.log
a.log: 줄 13, 표준 준수 0 (0%) {JSON 한 줄 아님=13}
a_json.log: 줄 3, 표준 준수 0 (0%) {timestamp 형식(ISO-8601+오프셋) 아님=3, 필드 없음:service=3, 필드 없음:trace_id=3}
b.log: 줄 4, 표준 준수 0 (0%) {JSON 한 줄 아님=4}
c.log: 줄 2, 표준 준수 2 (100%) {}
d.log: 줄 2, 표준 준수 0 (0%) {level 어휘 밖:warning=1, timestamp 형식(ISO-8601+오프셋) 아님=1, 필드 없음:level=1, 필드 없음:message=1, 필드 없음:service=1, 필드 없음:timestamp=1, 필드 없음:trace_id=1}
z.log: 줄 1, 표준 준수 0 (0%) {trace_id 전부 0(무효)=1}

$ grep -c '4bf92f3577b34da6a3ce929d0e0e4736' a.log a_json.log b.log c.log d.log            # 글자로 찾기
a.log:0
a_json.log:0
b.log:0
c.log:2
d.log:2

$ grep -c '"trace_id":"4bf92f3577b34da6a3ce929d0e0e4736"' a.log a_json.log b.log c.log d.log  # 표준 필드로 찾기
a.log:0
a_json.log:0
b.log:0
c.log:2
d.log:1
```

- 출력은 판정 단계 재실행(GNU grep 3.12, 같은 컨테이너 환경, 2026-10-05)이다. 첫 실행 기록의 grep 출력에는 `a_json.log` 행이 빠져 있었다(그 파일을 grep 뒤에 만든 것으로 보인다 — 해석). `z.log`는 trace_id가 전부 0인 한 줄을 검사기가 거르는지 보려고 더한 표본이다.

관찰과 해석.
- **이벤트 수 ≠ 줄 수.** 서비스 A는 이벤트 3건을 13줄로 냈다(스택트레이스 10줄). 줄 단위로 수집하면 ERROR 한 건이 11개 조각이 된다. 서비스 B도 이벤트 2건이 4줄이다.
- **시각이 서로 비교되지 않는다.** A는 날짜·오프셋 없는 현지 시각 `02:10:59`, B는 `Oct 05, 2026 2:11:01 AM`, C는 UTC `2026-10-04T17:11:04Z`다. 세 서비스는 몇 초 사이에 실행됐는데(KST 02:10:59~02:11:04), 적힌 날짜는 B가 10-05, C가 10-04로 하루가 다르고 A에는 날짜가 없다.
- **JSON이라고 표준은 아니다.** Logback 내장 `JsonEncoder`(1.3.8/1.4.8부터, JSON Lines)는 timestamp를 epoch 밀리초 숫자로 내고 service·trace_id 필드가 없다. D는 같은 trace_id를 한 줄에선 `traceId`, 다른 줄에선 `trace_id`로 썼다. 표준 필드로 검색하면 D의 이벤트 2건 중 1건이 빠진다.
- 표준을 따른 C만 검사·검색이 모두 된다. 표준의 가치는 형식 자체가 아니라 **공용 도구가 서비스를 가리지 않고 동작한다**는 데 있다.

### 3. 실험 B: 지표 이름 검사 — 단위·접미사·카디널리티

Prometheus 명명 문서의 권고를 팀 표준 규칙으로 옮겨 서비스들의 지표 이름을 검사했다.

```java
if (!name.matches("[a-z][a-z0-9_]*")) v.add("snake_case 아님");
if (type.equals("counter") && !name.endsWith("_total")) v.add("카운터는 _total로 끝나야");
if (name.matches(".*_(ms|millis|milliseconds|kb|mb)(_.*)?")) v.add("기본 단위(seconds·bytes) 아님");
if (type.equals("histogram") && !name.matches(".*_(seconds|bytes)")) v.add("히스토그램에 단위 접미사 없음");  // 팀 규칙: 히스토그램은 시간·크기만
if (name.matches(".*_\\d{3,}.*")) v.add("이름에 식별자 값(카디널리티) 포함 의심");
```

(실험, JDK 21.0.12 temurin, 2026-10-05 — 입력 이름 목록은 예시로 만든 것)

```text
order     http_requests_total                OK
order     http_server_requests_seconds       OK
payment   paymentRequestCount                [snake_case 아님, 카운터는 _total로 끝나야]
payment   payment_latency_ms                 [기본 단위(seconds·bytes) 아님, 히스토그램에 단위 접미사 없음]
shipping  shipping_queue_size                OK
shipping  shipping_label_user_10234_total    [이름에 식별자 값(카디널리티) 포함 의심]
inventory inventory_reserved                 [카운터는 _total로 끝나야]
위반 이름 4개
```

- `payment_latency_ms`와 `http_server_requests_seconds`를 한 대시보드에 그리면 단위가 1000배 다르다. Prometheus 문서는 한 지표가 단일 단위를 쓰고(MUST), 기본 단위를 쓰라고(SHOULD) 한다.
- `shipping_label_user_10234_total`은 사용자 ID를 이름에 넣었다. 사용자 수만큼 지표가 생긴다. 레이블로 옮겨도 고카디널리티 값은 레이블에 넣지 말라는 것이 같은 문서의 권고다.
- 히스토그램 규칙은 "우리 팀 히스토그램은 시간·크기만 잰다"는 **팀 규칙(예시)**이다. Prometheus 기본 단위에는 meters·grams·joules 등도 있으므로, 일반 검사기라면 그 단위 접미사도 받아야 한다.
- 검사기는 이름만 본다. 단위가 이름과 실제 값에서 일치하는지(이름은 seconds인데 값은 ms로 기록)는 계측 코드 리뷰나 값 범위 검사로 따로 봐야 한다.

### 4. 표준을 어떻게 지키게 하나 — 검사보다 기본값

```text
  약한 강제                                   강한 강제
  위키 문서 ──> 리뷰에서 지적 ──> CI 검사기 ──> 공용 라이브러리·템플릿의 기본값(골든 패스)
  (잊힘)        (사람마다 다름)   (위반을 막음)   (따로 노력하지 않아도 표준대로 나옴)
```

- *골든 패스(golden path)*: 조직이 권장하는 표준 구성으로 새 서비스를 시작하게 하는 템플릿·라이브러리. 기본값이 표준이면 따로 노력하지 않아도 표준을 따른다(용어는 업계 관례, 특정 표준 문서의 정의는 아님).
- 검사기는 "벗어남"을 잡고, 기본값은 "벗어날 일"을 줄인다. 둘 다 둔다.

## 쓰이는 자료구조·알고리즘

- **스키마 검증 = 필드 집합 비교 + 값 형식 검사**: 필수 필드 집합과 레코드 키 집합의 차집합으로 누락을 찾고, 값마다 형식(ISO-8601 파서, 정규식 `[0-9a-f]{32}` + 전부 0 거부, 레벨 어휘 집합)을 검사한다(실험 A).
- **시계열 식별 = 이름 + 레이블 집합**: 지표 하나의 시계열 수는 실제로 나타난 고유 레이블 조합의 수다. 레이블별 값 개수의 곱은 그 상한(모든 조합이 나타날 때의 수)이다. 이름이나 레이블에 사용자 ID 같은 무한 집합이 들어가면 상한이 폭발하고, 실제 시계열도 사용자 수만큼 는다([reliability/16](../../reliability/16-metrics-and-golden-signals/2-summary.md)).
- **trace-id 128비트(16바이트) 값**: W3C Trace Context의 trace-id는 16바이트다. 무작위 생성은 권고(SHOULD, 비규범 8.2절)이고, 더 짧은 내부 ID를 쓰는 시스템을 위한 처리도 같은 절에 있다 — 길이가 128비트라고 128비트 난수인 것은 아니다. 서비스들이 이 값을 같은 필드 이름으로 남겨야 로그 검색이 "같은 키로 조인"이 된다(실험 A의 grep 대비).
- **멀티라인 묶기**: 줄 단위 수집에서 스택트레이스를 한 이벤트로 묶으려면 "새 이벤트 시작 줄" 패턴으로 상태 기계를 돌려야 한다. 처음부터 한 이벤트 = 한 줄(JSON Lines)이면 이 단계가 필요 없다.

## 적용 — 풀어나가는 법

### 1. 순서

1. **사고 하나를 다시 재생해 본다.** 최근 사고의 한 요청을 로그·지표로 끝까지 따라가 보고, 막힌 지점(시각 형식·ID 누락·단위)을 표준 후보로 적는다.
2. **로그 스키마를 정한다.** 필수 필드(시각·레벨·서비스·trace_id·메시지), 시각 형식(ISO-8601 + 오프셋, 권장 UTC), 레벨 어휘(OTel SeverityNumber 대응표), 한 이벤트 = 한 줄.
3. **지표 규칙을 정한다.** 이름 형식, 단위(기본 단위), 카운터 `_total`, 금지 레이블(사용자 ID·이메일·URL 원문), 서비스마다 골든 시그널 4종 또는 RED.
4. **SLO·경보·런북 연결 규칙.** 서비스마다 SLI 정의 방식([reliability/02](../../reliability/02-slo-sli-error-budget/2-summary.md)), 경보마다 런북 링크([reliability/44](../../reliability/44-runbooks-and-operational-readiness/2-summary.md)).
5. **골든 패스에 넣는다.** 공용 로깅 설정·지표 라이브러리 설정을 서비스 템플릿의 기본값으로.
6. **검사기를 CI와 출시 점검에 건다.** 로그 샘플 검사·지표 이름 검사를 CI에서, PRR 체크리스트를 출시 전에.
7. **표준을 버전 관리한다.** 필드를 바꾸면 기존 대시보드·경보가 깨진다. 표준 변경은 공지·이행 기간과 함께.

### 2. 운영 표준 문서 골격 (예시)

```text
운영 표준 v1 (예시 — 조직마다 정한다)
1. 로그
   - 형식: JSON Lines(한 이벤트 = 한 줄), UTF-8, 표준 출력
   - 필수 필드: timestamp(ISO-8601+오프셋), level(TRACE|DEBUG|INFO|WARN|ERROR|FATAL),
               service, trace_id(소문자 16진 32자, 요청 처리 중일 때), message
   - 금지: 비밀번호·토큰·주민등록번호 원문 (→ 17-legal-standards, reliability/15 장애 5)
2. 지표
   - 이름: snake_case, 기본 단위 접미사(_seconds, _bytes), 카운터 _total
   - 레이블 금지 목록: user_id, email, 원본 URL 경로
   - 서비스마다: 요청 수·오류 수·지연 히스토그램·포화도
3. SLO·경보: 사용자 여정 단위 SLI, 경보마다 런북 URL 주석
4. 출시 전 점검(PRR): 대시보드·경보·런북·용량 시험·롤백 절차·온콜 지정
```

### 3. 로그 설정을 골든 패스에 (Logback, Java)

```java
// MDC에 trace_id를 넣는 필터 — 들어온 traceparent 헤더(W3C)가 유효하면 그 trace-id 부분을 쓴다
public class TraceIdFilter implements Filter {
    // 버전 00 형식만 받는 단순화(더 높은 버전 처리는 W3C 4.3절)
    private static final Pattern TP = Pattern.compile("00-([0-9a-f]{32})-([0-9a-f]{16})-[0-9a-f]{2}");
    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)
            throws IOException, ServletException {
        String tp = ((HttpServletRequest) req).getHeader("traceparent");   // 00-<trace-id>-<parent-id>-<flags>
        Matcher m = (tp == null) ? null : TP.matcher(tp.strip());
        boolean valid = m != null && m.matches()
                && !m.group(1).equals("0".repeat(32)) && !m.group(2).equals("0".repeat(16));
        String traceId = valid ? m.group(1) : newTraceId();   // 무효하면 무시하고 새 추적(W3C: MUST ignore)
        MDC.put("trace_id", traceId);
        try { chain.doFilter(req, res); } finally { MDC.remove("trace_id"); }
    }
    private static String newTraceId() {
        byte[] b = new byte[16];
        ThreadLocalRandom.current().nextBytes(b);
        return HexFormat.of().formatHex(b);
    }
}
```

- 표준 필드 이름(timestamp ISO-8601·service·trace_id)으로 내려면 인코더 출력 모양을 맞춰야 한다. 실험 A처럼 Logback 내장 `JsonEncoder`는 timestamp를 epoch 밀리초로 내므로 그대로는 이 예시 표준과 다르다. 어떤 인코더·어떤 설정으로 맞출지는 조직이 골라 템플릿에 고정한다.
- 스레드풀 경계에서 MDC가 사라지는 함정은 [reliability/15-logging](../../reliability/15-logging/2-summary.md) §3.

### 4. 진단 — 표준이 지켜지는지

- 로그 샘플 N줄을 검사기로 돌려 준수율을 서비스별로 본다(실험 A의 출력 형태).
- `trace_id` 하나로 검색했을 때 요청이 거친 서비스 수와, 실제 호출 경로의 서비스 수가 같은가.
- 지표 이름 검사 위반 수, 시계열 수 상위 지표.
- 경보 중 런북 링크가 없는 것의 수.

## 장애 시나리오와 대처

### 1. 서비스마다 다른 로그·지표 → 사고 때 한 요청을 따라갈 수 없다 (⚠ 커리큘럼)

- 현상: 결제 실패 문의 하나를 추적하는 데 서비스마다 다른 검색어·다른 대시보드를 써야 한다.
- 보이는 형태: 실험 A처럼 표준 필드로 검색하면 일부 서비스의 이벤트가 빠진다(`traceId` vs `trace_id`, 아예 ID 없음). 지표는 서비스마다 이름·단위가 달라 한 그래프에 겹칠 수 없다.
- 원인: 운영 형식을 서비스 팀이 각자 정했다. 기준이 문서로도, 기본값으로도 없다.
- 대처: 로그 스키마·지표 규칙을 운영 표준으로 정하고, 골든 패스의 기본값으로 넣고, CI 검사기로 벗어남을 막는다.

### 2. 시각 표기 혼재 → 타임라인 순서가 뒤집힌다

- 현상: 포스트모템 타임라인에서 원인 이벤트가 결과 이벤트보다 늦게 적힌다.
- 보이는 형태: `02:10:59`(날짜·오프셋 없음), `Oct 05, 2026 2:11:01 AM`(현지), `2026-10-04T17:11:04Z`(UTC)가 섞인다(실험 A). 글자 정렬로는 순서가 맞지 않는다.
- 원인: 시각 형식이 표준에 없다. 라이브러리 기본 패턴을 그대로 썼다.
- 대처: ISO-8601 + 오프셋을 필수로, 저장은 UTC로 통일한다. 수집기가 "받은 시각"(OTel ObservedTimestamp에 해당)과 "발생 시각"(Timestamp)을 구분해 남기게 한다.

### 3. 멀티라인 스택트레이스 → 이벤트가 조각난다

- 현상: ERROR 건수가 실제보다 많거나 적게 집계된다. 스택트레이스 일부만 검색된다.
- 보이는 형태: 이벤트 3건이 13줄(실험 A). 줄 단위 수집기에서는 `\tat java.base/...` 줄이 레벨 없는 별개 이벤트가 된다.
- 원인: 한 이벤트 = 한 줄 규칙이 없다.
- 대처: JSON Lines로 내고 스택트레이스는 한 필드 안에 넣는다(줄바꿈은 이스케이프). 당장 바꿀 수 없으면 수집기에 멀티라인 묶기 규칙을 둔다.

### 4. 지표 단위·이름 혼재 → 대시보드 오판, 카디널리티 폭발

- 현상: 지연 그래프에서 한 서비스만 1000배 느려 보인다. 지표 저장소 메모리가 갑자기 는다.
- 보이는 형태: `payment_latency_ms`와 `..._seconds`가 한 패널에 있다. 이름이나 레이블에 사용자 ID가 들어간 지표의 시계열 수가 사용자 수만큼 늘어난다(실험 B).
- 원인: 지표 이름·단위·레이블 규칙이 없다.
- 대처: 기본 단위·단위 접미사·`_total`·레이블 금지 목록을 표준으로, CI에서 이름 검사. 기존 지표는 이름을 바꾸면 대시보드·경보가 깨지므로 새 이름을 병행 발행한 뒤 옮긴다.

### 5. 표준이 문서에만 있다 → 새 서비스가 따르지 않는다

- 현상: 표준 문서는 있는데 최근 만든 서비스 세 개 중 두 개가 따르지 않는다. 첫 장애 때 경보·런북이 없다는 것을 안다.
- 보이는 형태: 출시 체크리스트에 운영 항목이 없다. 경보 규칙에 런북 주석이 없다.
- 원인: 강제가 "문서를 읽고 따르기"뿐이다.
- 대처: 표준을 서비스 템플릿 기본값으로 넣고, 출시 전 PRR(SRE Book 32장 범위: 아키텍처·의존성, 계측·모니터링, 비상 대응, 용량, 변경 관리, 성능)을 통과 조건으로 둔다([reliability/44](../../reliability/44-runbooks-and-operational-readiness/2-summary.md)).

## 핵심 문장

- 운영 표준은 서비스와 공용 운영 도구 사이의 계약이다 — 같은 규격이면 로그 검색·대시보드·경보·런북이 서비스를 가리지 않고 동작한다.
- "JSON으로 낸다"는 표준이 아니다. 필드 이름·시각 형식·레벨 어휘·추적 ID까지 정해야 서비스 사이에서 조인이 된다(실험: 표준 필드 검색에서 D의 이벤트 1건이 빠짐).
- 시각은 ISO-8601 + 오프셋, 이벤트는 한 줄, 지표는 기본 단위와 `_total` — 사고 때 타임라인과 그래프를 믿을 수 있게 하는 최소 규칙이다.
- 표준을 지키게 하는 가장 강한 방법은 검사기보다 골든 패스의 기본값이다. 검사기는 벗어남을 잡는다.
- 20000-1은 관리 체계를, SRE는 SLO·포스트모템 같은 실천을, 운영 표준은 그 실천이 서비스마다 같은 모양으로 나오게 하는 규격을 맡는다.

## 관련 주제·근거

- 원본(기초): [engineering/development-standards/operational-standards](../../engineering/development-standards/operational-standards/2-summary.md) — ISO/IEC 20000-1:2018 조항 구조와 조항 8 운영 프로세스, SRE의 SLI·SLO·SLA·에러 버짓·toil·포스트모템·골든 시그널
- 선행: [reliability/15-logging](../../reliability/15-logging/2-summary.md) — 구조화 로그·상관 ID·레벨·샘플링
- 후속·연결
  - [reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md) — 지표 형·카디널리티
  - [reliability/17-distributed-tracing](../../reliability/17-distributed-tracing/2-summary.md) · [reliability/18-logs-traces-audit-roles](../../reliability/18-logs-traces-audit-roles/2-summary.md)
  - [reliability/02-slo-sli-error-budget](../../reliability/02-slo-sli-error-budget/2-summary.md) · [reliability/43-alerting-and-on-call](../../reliability/43-alerting-and-on-call/2-summary.md) · [reliability/44-runbooks-and-operational-readiness](../../reliability/44-runbooks-and-operational-readiness/2-summary.md) · [reliability/26-incident-response-and-postmortem](../../reliability/26-incident-response-and-postmortem/2-summary.md)
  - [systems/straggler](../../systems/straggler/2-summary.md) — 원본 §6 링크가 가리키던 노트(재구조화 뒤 경로) · [reliability/34-tail-latency-and-stragglers](../../reliability/34-tail-latency-and-stragglers/2-summary.md) — 같은 주제
  - [14-quality-standards](../14-quality-standards/2-summary.md) · [15-security-standards](../15-security-standards/2-summary.md) · [17-legal-standards](../17-legal-standards/2-summary.md)(접속기록 보관·로그 속 개인정보)
- 근거
  - OpenTelemetry Logs Data Model(Stable) — 최상위 필드 12개, SeverityNumber 범위 <https://opentelemetry.io/docs/specs/otel/logs/data-model/>
  - W3C Trace Context — trace-id 16바이트·소문자 16진수, 전부 0 무효 <https://www.w3.org/TR/trace-context/>
  - Prometheus, "Metric and label naming" <https://prometheus.io/docs/practices/naming/>
  - Google SRE Book 32장 "The Evolving SRE Engagement Model" — PRR의 두 목적과 점검 영역 <https://sre.google/sre-book/evolving-sre-engagement-model/>
  - Logback 매뉴얼 "Encoders" — JsonEncoder(1.3.8/1.4.8부터, JSON Lines) <https://logback.qos.ch/manual/encoders.html>
  - ISO/IEC 20000-1:2018 <https://www.iso.org/standard/70636.html> (원문 유료 — 조항 구조는 원본 노트 범위. 2026-10 현재 개정 여부 `[?]`)
- 실험 목록
  - A. 로그 표준 검사: Logback 1.5.12(기본 패턴·JsonEncoder)·SLF4J 2.0.16·JUL 기본·직접 만든 JSON 2종, temurin 21.0.12 컨테이너(TZ=Asia/Seoul). 준수율 a 0/13, a_json 0/3, b 0/4, c 2/2, d 0/2. trace_id 글자 검색 c 2·d 2 vs 표준 필드 검색 c 2·d 1. 판정 단계 재실행(GNU grep 3.12): 검사기에 전부 0 trace_id 거부를 더하고 z.log 표본 1줄 추가 — 원래 5개 파일 결과는 같고 z.log 0/1, grep 출력에 a_json.log:0 행 보강.
  - B. 지표 이름 검사: 예시 이름 7개 중 위반 4개(snake_case·`_total`·기본 단위·단위 접미사·식별자 값).
