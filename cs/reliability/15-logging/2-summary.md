# reliability/15-logging — 구조화 로그·상관 ID·레벨·샘플링·비동기 appender — 정리 (힌트)

## 해결하는 문제

장애가 나면 "그 요청에 무슨 일이 있었나"를 묻게 된다.\
지표(16)는 "에러율이 올랐다"까지 알려 준다. **어떤 주문이, 어느 단계에서, 무슨 값으로** 실패했는지는 사건 하나하나를 적은 기록, 곧 로그가 있어야 안다.

```text
 로그가 없거나 쓸모없을 때                      로그가 제 역할을 할 때
 고객: "주문 1042 결제가 실패했어요"            고객: "주문 1042 결제가 실패했어요"
 서버 20대 × 파일 수십 개를 grep               검색: orderId=1042 → requestId=req-7f3a
 "결제 실패" 문자열이 하루 3만 줄               → 그 요청의 줄만 시간순: 입력 → PG 호출 → 타임아웃 3s
 어느 줄이 이 고객 것인지 모른다                → 원인 후보가 바로 좁혀진다
```

- *로그(log)*: 프로그램이 실행 중 일어난 사건을 시간순으로 적은 기록. 한 줄 = 사건 하나가 기본이다.
- 로그가 쓸모 있으려면 네 가지가 갖춰져야 한다.
  1. **구조화**: 기계가 필드로 검색할 수 있는 형식(JSON·key=value).
  2. **상관 ID**: 한 요청의 줄을 한데 묶는 번호.
  3. **레벨**: 중요도를 나눠 걸러 내고 비용을 조절한다.
  4. **샘플링·비동기 기록**: 로그가 서비스를 느리게 하거나 디스크를 채우지 않게 한다.

쉬운 예: 택배 송장 번호다. 물류 센터 여러 곳이 각자 기록을 남겨도, 송장 번호 하나로 한 상자의 경로를 이어 볼 수 있다.\
똑같은 구조다.\
실무 예: 게이트웨이가 만든 요청 ID를 서비스 A·B가 로그 줄마다 넣는다. 로그 수집기가 서버 20대의 줄을 모아도 ID 하나로 그 요청만 뽑힌다.

## 동작·원리

### 1. 로그 한 줄이 가는 길

```text
 애플리케이션 스레드
   log.info("order placed", orderId=1042)
        │ ① 레벨 검사: 로거 레벨보다 낮으면 여기서 버린다(비용 거의 0)
        ▼
   이벤트 객체(시각·레벨·스레드·MDC 사본·메시지·필드)
        │ ② appender: 동기면 이 스레드가 직접 쓴다 / 비동기면 큐에 넣고 바로 돌아온다
        ▼
   stdout / 파일
        │ ③ 수집기(Fluent Bit·Vector·OTel Collector 등)가 읽어 보낸다
        ▼
   저장·검색(Loki·Elasticsearch 등) ── 보존 기한이 지나면 지운다
```

- *appender*: 로그 이벤트를 실제 목적지(콘솔·파일·네트워크)에 쓰는 부품. Logback·Log4j의 용어다.
- 12-factor 앱 XI장 "Logs"는 앱이 로그 파일 위치·회전을 관리하지 말고 **stdout에 이벤트 스트림으로** 쓰라고 한다. 모으고 보내는 일은 실행 환경(컨테이너 런타임·수집기)의 몫이다.
  - 그러면 파일 회전 책임이 실행 환경으로 간다. Docker `json-file` 드라이버는 `max-size` 기본값이 -1(무제한)이다(Docker 문서, 2026-10-01 열람). 회전 설정을 하지 않으면 컨테이너 로그가 디스크를 채울 수 있다.

### 2. 구조화 로그 — 사람이 읽는 문장에서 기계가 고르는 필드로

```text
 텍스트:  2026-10-01 09:00:01 INFO order placed for 1042, amount 39000 (req-7f3a)
          → "1042"를 찾으려면 정규식. 문구가 바뀌면 검색이 깨진다
 구조화:  {"level":"INFO","mdc":{"requestId":"req-7f3a"},"kvpList":[{"orderId":"1042"}],"message":"order placed"}
          → 수집 단계에서 kvpList를 필드로 뽑아 두면 orderId = 1042 로 정확히 고른다. 집계(주문별 실패 수)도 된다
```

- 메시지 문장은 고정하고, 바뀌는 값은 **필드**로 뺀다. 같은 사건이 같은 문장이면 "order placed가 몇 번" 같은 집계가 쉬워진다.
- OpenTelemetry Logs 데이터 모델(상태 Stable)은 로그 레코드의 필드를 정한다: `Timestamp`·`ObservedTimestamp`·`TraceId`·`SpanId`·`TraceFlags`·`SeverityText`·`SeverityNumber`·`Body`·`Resource`·`InstrumentationScope`·`Attributes`·`EventName`.
  - `TraceId`·`SpanId` 칸이 따로 있다. 로그 줄을 트레이스(17)와 잇는 칸이다.
- Spring Boot는 3.4부터 `logging.structured.format.console`(ECS·GELF·Logstash 형식)로 구조화 로그를 켠다(3.4.0 문서. 3.3.0 문서에는 이 속성이 없다).
  - Spring Boot 기본 로깅 설정을 쓸 때 얘기다. 자체 `logback-spring.xml`이 있으면 그 encoder가 `CONSOLE_LOG_STRUCTURED_FORMAT`을 쓰도록 고쳐야 한다(3.4 문서).

### 3. 상관 ID — MDC와 그 함정

```text
 요청 스레드 http-nio-1          스레드풀 pool-1-thread-1
 MDC(ThreadLocal) = {requestId:req-7f3a}
 log.info(...) → ID 찍힘
 pool.submit(task) ──────────▶  MDC = {} (이 스레드의 ThreadLocal은 비어 있다)
                                 log.info(...) → ID 없음
```

- *상관 ID(correlation ID)*: 한 요청(또는 한 업무 흐름)에 속한 로그 줄을 묶는 식별자. 요청 ID·트레이스 ID가 그 역할을 한다.
- *MDC(Mapped Diagnostic Context)*: SLF4J·Logback의 "현재 스레드에 붙은 키-값 묶음". 로그 이벤트를 만들 때 사본이 들어간다.
  - Logback의 MDC는 스레드별 저장소(ThreadLocal) 위에 있다. 그래서 **다른 스레드로 넘어가면 따라가지 않는다.**
- 정리하지 않으면 반대 사고도 난다. 스레드풀의 스레드는 재사용되므로, 앞 작업이 넣은 MDC가 **다음 요청의 줄에 남는다.**

### 4. 실험: JSON 구조화 로그와 스레드풀 경계의 MDC

```java
MDC.put("requestId", "req-7f3a");
log.atInfo().addKeyValue("orderId", 1042).addKeyValue("amount", 39000).log("order placed");
pool.submit(() -> log.info("async step (MDC 복사 안 함)")).get();
Map<String, String> copy = MDC.getCopyOfContextMap();
pool.submit(() -> { MDC.setContextMap(copy); try { log.info("async step (MDC 복사함, 끝나면 clear)"); } finally { MDC.clear(); } }).get();
pool.submit(() -> { MDC.put("requestId", "req-AAAA"); log.info("요청 A 처리 (clear 안 함)"); }).get();
pool.submit(() -> log.info("요청 B 처리 — 누구의 ID가 찍히나?")).get();
```

(실험, JDK 21.0.12 temurin + Logback 1.5.18 `JsonEncoder`, 컨테이너 `--cpus=2`, 2026-10-01)

```text
{"timestamp":1790834459352,"level":"INFO","threadName":"main","loggerName":"order","mdc": {"requestId":"req-7f3a"},"kvpList": [{"orderId":"1042"},{"amount":"39000"}],"message":"order placed","throwable":null}
== B. 스레드풀 경계: MDC는 ThreadLocal이라 따라가지 않는다
{"timestamp":1790834459362,"level":"INFO","threadName":"pool-1-thread-1","loggerName":"order","mdc": {},"message":"async step (MDC 복사 안 함)","throwable":null}
{"timestamp":1790834459366,"level":"INFO","threadName":"pool-1-thread-1","loggerName":"order","mdc": {"requestId":"req-7f3a"},"message":"async step (MDC 복사함, 끝나면 clear)","throwable":null}
{"timestamp":1790834459368,"level":"INFO","threadName":"pool-1-thread-1","loggerName":"order","mdc": {"requestId":"req-AAAA"},"message":"요청 A 처리 (clear 안 함)","throwable":null}
{"timestamp":1790834459369,"level":"INFO","threadName":"pool-1-thread-1","loggerName":"order","mdc": {"requestId":"req-AAAA"},"message":"요청 B 처리 — 누구의 ID가 찍히나?","throwable":null}
```

- 관찰 1: 복사하지 않은 작업의 줄은 `mdc: {}`다. 이 줄은 요청 ID로 검색해도 나오지 않는다.
- 관찰 2: 요청 B의 줄에 **요청 A의 ID**가 찍혔다. 끊김보다 나쁘다. 엉뚱한 요청의 기록으로 보여 조사를 잘못된 방향으로 끈다.
- 관찰 3: Logback 1.5.18 `JsonEncoder`는 key-value 값을 문자열로 적는다(`"1042"`). 숫자 범위 검색이 필요하면 수집 단계에서 형 변환을 정한다.

### 5. 레벨 — 중요도와 비용의 손잡이

| OTel SeverityNumber | 범위 이름 | 쓰는 곳(관례 예) |
|---|---|---|
| 1–4 | TRACE | 아주 세밀한 디버깅. 운영에서는 보통 끈다 |
| 5–8 | DEBUG | 개발·장애 조사 때 잠깐 켠다 |
| 9–12 | INFO | 정상 흐름의 주요 사건(요청 완료, 잡 시작·끝) |
| 13–16 | WARN | 자동으로 회복됐지만 알아 둘 일(재시도 성공, 폴백 사용) |
| 17–20 | ERROR | 요청이 실패했다. 사람이 볼 필요가 있다 |
| 21–24 | FATAL | 프로세스가 계속 못 간다 |

- 범위와 이름은 OpenTelemetry Logs 데이터 모델의 표다. 오른쪽 칸은 흔한 운영 관례이고 표준이 정한 것이 아니다.
- 레벨 검사는 이벤트를 만들기 **전에** 한다. 그래서 꺼진 DEBUG는 비용이 거의 없다. 단, 인자를 미리 문자열로 이어 붙이면(`"x=" + big.toString()`) 그 비용은 레벨과 상관없이 든다. `{}` 자리표시자나 `atDebug()`를 쓴다.
  - 다만 인자로 부른 메서드(`expensive()`)는 둘 다 레벨 검사 전에 실행된다. 계산 자체를 피하려면 `isDebugEnabled()` 검사나 `Supplier`를 받는 `addArgument(() -> …)`·`addKeyValue("x", () -> …)`(SLF4J 2.x `LoggingEventBuilder`)를 쓴다.

### 6. 동기 vs 비동기 appender

```text
 동기:   요청 스레드 ──[직렬화 + 쓰기(디스크·네트워크)]──▶ 다음 코드
                       목적지가 느리면 요청이 그만큼 느려진다

 비동기: 요청 스레드 ──[큐에 넣기]──▶ 다음 코드
                         │
                     [ 크기 256 큐 ]  ← Logback AsyncAppender 기본
                         │  워커 스레드가 꺼내 실제 appender에 쓴다
                     큐가 차면? → 버리거나(INFO 이하) 기다린다(WARN 이상)
```

Logback 1.5.18 `AsyncAppenderBase`·`AsyncAppender` 소스에서 확인한 동작이다.
- 큐는 `ArrayBlockingQueue`, 기본 크기 `DEFAULT_QUEUE_SIZE = 256`.
- `discardingThreshold`를 정하지 않으면 `queueSize / 5`(=51). **남은 칸이 51보다 적으면** TRACE·DEBUG·INFO(`isDiscardable`: 레벨 ≤ INFO)를 조용히 버린다.
- WARN·ERROR는 `put`으로 넣는다. 큐가 꽉 차면 **호출 스레드가 기다린다.** `neverBlock=true`면 `offer`로 넣고, 꽉 찼으면 레벨과 상관없이 버린다.
- 워커는 `take()`로 하나를 꺼낸 뒤 `drainTo`로 **큐를 통째로 비워** 묶음으로 쓴다.
- `stop()`은 남은 이벤트를 `maxFlushTime`(기본 1000ms)까지 기다려 쓴다. 그 안에 못 쓴 것은 버린다.

### 7. 실험: 느린 목적지에 2000건 — 동기·비동기 기본·neverBlock

- 목적지: 이벤트마다 2ms 자는 appender(느린 디스크·원격 수집기 흉내).
- 부하: 2000건을 쉬지 않고 기록, 10건마다 WARN 1건(WARN 200, INFO 1800).

(실험, JDK 21.0.12 temurin + Logback 1.5.18, 컨테이너 `--cpus=2`, 세 번 실행(점검에서 세 번 더), 2026-10-01)

```text
sync              호출 지연 p50=  2.109ms p99=  2.267ms max=  3.199ms(1602번째 호출) 1ms초과 2000건 | 전달 INFO 1800/1800 WARN 200/200
async-default     호출 지연 p50=  0.005ms p99=  0.078ms max=532.936ms(1500번째 호출) 1ms초과    3건 | 전달 INFO  626/1800 WARN 200/200
async-neverBlock  호출 지연 p50=  0.001ms p99=  0.016ms max=  0.655ms(0번째 호출) 1ms초과    0건 | 전달 INFO  372/1800 WARN 107/200
```

- 관찰 1 — 동기: 호출마다 약 2.1ms. 목적지의 느림이 **요청 지연에 그대로 더해진다.** 대신 하나도 잃지 않았다.
- 관찰 2 — 비동기 기본: p50 5µs. 하지만 INFO가 1800건 중 626건만 남았다(집필·점검 여섯 번 실행에서 558~743건). 버린 줄에 대한 경고는 없다.
- 관찰 3 — 비동기 기본에서 1ms를 넘은 호출은 실행마다 3건이었고, 최대값은 약 530ms였다(여섯 번 실행 모두 529~534ms). 큐가 꽉 찬 때 온 WARN이 `put`에서 기다렸다.
  - 해석: 워커가 `drainTo`로 256개를 한꺼번에 가져가 2ms씩 쓰는 동안(약 512ms) 큐가 다시 찬다. 그 묶음이 끝나야 자리가 난다.
- 관찰 4 — neverBlock: 멈춤은 없다. 대신 **WARN도 버렸다**(전달 수는 실행마다 다르다 — 집필·점검 여섯 번 실행에서 73~141/200).
- 정리: 비동기 appender는 지연을 목적지에서 떼어 내는 대신, **유실 또는 드문 긴 멈춤**을 고르게 한다. 목적지의 지속 처리량이 기록 속도보다 낮으면 어느 쪽이든 따라잡지 못한다(Log4j 2 문서 "Asynchronous loggers"의 Trade-offs 절도 같은 점을 적는다).

### 8. 샘플링 — 줄 단위 vs 요청 단위

로그가 너무 많으면 일부만 남긴다. 무엇을 기준으로 고르느냐가 중요하다.

(실험, 같은 환경, 요청 1000개 × 줄 5개, 10% 샘플)

```text
줄마다 무작위: 남은 줄 452, 5줄 다 남은 요청 0, 일부만 남은 요청 373
요청 ID 해시: 남은 줄 480, 5줄 다 남은 요청 96, 일부만 남은 요청 0
```

- 줄마다 무작위로 고르면 남은 양은 비슷하다. 그러나 **처음부터 끝까지 이어 볼 수 있는 요청이 0개**다.
- 요청 ID의 해시로 고르면 한 요청의 줄이 함께 남거나 함께 버려진다. 트레이스의 head 샘플링(17)과 같은 생각이다.
- ERROR·감사 사건은 샘플링 대상에서 뺀다. 감사·업무 기록을 운영 로그와 따로 다루는 기준은 18.

## 쓰이는 자료구조·알고리즘

- **원형 배열 큐(링 버퍼)** — Logback `AsyncAppender`의 `ArrayBlockingQueue`는 고정 크기 배열을 원형으로 돈다. Log4j 2의 비동기 로거는 LMAX Disruptor의 링 버퍼를 쓴다(기본 `256 × 1024`칸, GC-free 모드는 `4 × 1024`칸, Log4j 2 문서). 큐 일반은 [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md).
- **유계(bounded) 큐 + 넘침 정책** — 버림·대기·호출자 실행 중 하나를 고른다. 역압 일반은 [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md).
- **ThreadLocal 맵** — MDC의 저장소. 스레드 경계에서 복사·정리가 필요하다.
- **해시 기반 결정적 샘플링** — `hash(요청 ID) mod 100 < 10`. 같은 ID는 어디서나 같은 결정을 받는다.
- **로그 회전(크기·시간 기준 파일 교체)** — 오래된 파일부터 지운다. 보존 기한 개념은 18.

## 적용 — 풀어나가는 법

### 1. 순서

1. 형식을 정한다: JSON 한 줄 = 사건 하나. 공통 필드(시각·레벨·서비스·요청 ID·트레이스 ID)를 문서로 고정한다.
2. 입구에서 요청 ID를 받거나 만든다. 응답 헤더로 돌려주고, 하류 호출 헤더에 싣는다.
3. 스레드 경계마다 MDC를 복사하고, 끝나면 지운다.
4. 레벨 기준을 정한다(예: 예상된 4xx는 WARN 이하, 요청 실패는 ERROR).
5. appender를 고른다: 지연이 중요하면 비동기 + 버린 수 지표. 잃으면 안 되는 기록은 이 경로에 두지 않는다(18).
6. 보존·회전·용량 경보를 정한다(디스크 사용률은 16의 포화 지표).

### 2. 요청 ID 필터와 스레드풀 래퍼 (Java, Servlet + SLF4J)

```java
public class RequestIdFilter implements Filter {
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain) throws IOException, ServletException {
        HttpServletRequest r = (HttpServletRequest) req;
        String id = Optional.ofNullable(r.getHeader("X-Request-Id"))
                .filter(s -> s.matches("[A-Za-z0-9-]{8,64}"))       // 밖에서 온 값은 형식을 검사한다(로그 주입 방지)
                .orElse(UUID.randomUUID().toString());
        MDC.put("requestId", id);
        ((HttpServletResponse) res).setHeader("X-Request-Id", id);
        try { chain.doFilter(req, res); }
        finally { MDC.remove("requestId"); }                          // 스레드가 재사용되므로 정리한다
    }
}

/** 작업을 제출한 스레드의 MDC를 실행 스레드로 옮기고, 끝나면 원래대로 돌린다 */
static Runnable withMdc(Runnable task) {
    Map<String, String> captured = MDC.getCopyOfContextMap();
    return () -> {
        Map<String, String> before = MDC.getCopyOfContextMap();
        if (captured == null) MDC.clear(); else MDC.setContextMap(captured);
        try { task.run(); }
        finally { if (before == null) MDC.clear(); else MDC.setContextMap(before); }
    };
}
```

- Spring에서는 `ThreadPoolTaskExecutor.setTaskDecorator(...)`에 같은 일을 하는 `TaskDecorator`를 건다. Spring Framework에는 Micrometer Context Propagation을 쓰는 `ContextPropagatingTaskDecorator`도 있다(Spring Framework javadoc).
- 트레이싱을 켜면 트레이스 ID가 상관 ID 역할을 한다. Spring Boot는 트레이싱이 켜져 있으면 로그에 상관 ID를 넣는다(Spring Boot 3.4 logging 문서 "Correlation ID").

### 3. Logback 비동기 설정 (선택을 드러내기)

```xml
<appender name="ASYNC" class="ch.qos.logback.classic.AsyncAppender">
  <queueSize>8192</queueSize>               <!-- 버스트를 흡수할 만큼 (예시 값) -->
  <discardingThreshold>0</discardingThreshold> <!-- 0 = INFO도 버리지 않는다(대신 꽉 차면 기다린다) -->
  <neverBlock>false</neverBlock>            <!-- true면 멈추지 않는 대신 레벨과 상관없이 버린다 -->
  <appender-ref ref="JSON_STDOUT"/>
</appender>
```

- 어느 쪽을 고르든 "버렸다"가 보이게 한다.
  - Logback 1.5.18 `AsyncAppenderBase`는 버린 수를 세지 않는다. 문턱 아래 버림은 그냥 `return`이고, `neverBlock`의 `offer` 결과도 버린다(소스). Logback 단계의 유실 수가 필요하면 그 경로를 따로 계측한다(예: appender를 감싸 센다).
  - 수집기·에이전트의 드롭 카운터는 수집기 **이후**의 유실만 센다. 큐 남은 칸(`getRemainingCapacity()`)은 지금 얼마나 찼는지일 뿐 지난 유실 수가 아니다. 둘 다 "버릴 위험"의 신호로 함께 본다.

### 4. 진단 명령

```bash
# 한 요청의 줄만 시간순으로 (JSON 로그 + jq)
#  deploy/order는 Pod 하나의 로그만 준다 → 레이블로 모든 Pod를 고른다(선택자를 쓰면 --tail 기본이 10줄이라 -1로)
#  여러 서비스를 거친 요청은 중앙 로그 저장소에서 요청 ID + 시각으로 찾는 것이 정석
kubectl logs -l app=order --tail=-1 --since=30m \
  | jq -cR 'fromjson? | select(.mdc.requestId=="req-7f3a")' | jq -sc 'sort_by(.timestamp)[]'
# 상관 ID가 빠진 줄의 비율 — 요청 처리 로그인데 높으면 스레드 경계에서 끊기고 있다
#  (시작·종료 로그처럼 요청 밖에서 찍힌 줄도 ID가 없으니 로거로 범위를 좁혀 해석한다)
kubectl logs -l app=order --tail=-1 --since=10m \
  | jq -cR -s '[split("\n")[] | fromjson?] | {total: length, missing: (map(select(.mdc.requestId == null)) | length)}
              | .ratio = (if .total > 0 then .missing / .total else null end)'
# 로그가 디스크를 채우는지
df -h /var/lib/docker && du -sh /var/lib/docker/containers/*/*-json.log | sort -h | tail -3
```

## 장애 시나리오와 대처

### 1. 로그 폭증 → 디스크 풀·비용 폭증

- 현상: 노드 디스크가 100%가 되고, 같은 노드의 다른 서비스까지 쓰기에 실패한다. 로그 저장소 청구액이 갑자기 몇 배가 된다.
- 보이는 형태: `No space left on device`(ENOSPC). 로그 줄 수 지표가 장애 시각에 수십 배. 같은 스택 트레이스가 초당 수천 줄.
- 원인: 실패 경로에서 요청마다 스택 트레이스를 찍는다. 재시도 루프 안의 로그. 회전·보존 설정이 없다(Docker `json-file` 기본 `max-size=-1`).
- 대처: 회전·보존 기한을 건다. 같은 메시지 반복은 비율 제한(초당 N줄 + "M줄 생략")한다. 스택 트레이스는 경계에서 한 번만 찍는다. 로그 양을 지표로 보고 경보한다.

### 2. 상관 ID 없음 → 요청 하나를 따라갈 수 없음

- 현상: 고객 문의 한 건을 조사하는 데 몇 시간이 걸린다. 같은 시각의 비슷한 줄이 수백 개라 누구 것인지 모른다.
- 보이는 형태: 비동기 단계 이후의 줄에 요청 ID가 비어 있다(위 실험의 `mdc: {}`). 또는 남의 ID가 찍혀 있다(`req-AAAA`).
- 원인: MDC는 스레드에 붙어 있어 스레드풀·`CompletableFuture`·메시지 소비 스레드로 넘어가지 않는다. 정리하지 않으면 재사용 스레드에 남는다.
- 대처: 입구 필터 + 실행기 래퍼(`TaskDecorator`)로 복사·정리를 한 곳에 모은다. 큐를 건너면 메시지 헤더에 ID를 싣는다(트레이스 컨텍스트 전파는 17). "ID 없는 줄 비율"을 정기적으로 본다.

### 3. 동기 로깅이 지연을 만든다

- 현상: 로그 수집기(또는 NFS 디스크)가 느려진 시각에 API p99가 같이 오른다. CPU는 한가하다.
- 보이는 형태: 스레드 덤프에 `FileOutputStream.write`·소켓 쓰기에서 멈춘 요청 스레드가 많다. 위 실험의 sync처럼 호출마다 목적지 지연만큼 늘어난다.
- 원인: 요청 스레드가 직접 I/O를 한다. 목적지의 꼬리 지연이 요청 경로에 들어온다.
- 대처: 비동기 appender로 떼어 내되 유실·멈춤 정책을 정한다. stdout으로 쓰고 전송은 수집기에 맡긴다(12-factor XI). 로그 양을 줄인다.

### 4. 비동기 큐 포화 → INFO가 조용히 사라지거나 WARN에서 수백 ms 멈춤

- 현상: 장애 조사 중 "그 시각 INFO가 듬성듬성 비어" 있다. 또는 평소 몇 ms인 API가 가끔 500ms 넘게 멈춘다.
- 보이는 형태: 위 실험의 async-default — INFO 1800건 중 558~743건만 전달, WARN 기록 호출이 약 530ms 대기. neverBlock이면 WARN·ERROR도 빠진다.
- 원인: 기록 속도 > 목적지 처리량. Logback 기본 설정은 남은 칸이 20% 미만이면 INFO 이하를 버리고, 꽉 차면 WARN 이상에서 기다린다.
- 대처: 목적지 처리량을 늘리거나 로그를 줄인다. 큐 크기·`discardingThreshold`·`neverBlock`을 의도에 맞게 명시한다. 버린 수를 지표로 낸다. 잃으면 안 되는 사건은 별도 경로로 보낸다(18).

### 5. 비밀번호·토큰·개인정보가 로그에 남는다

- 현상: 보안 점검에서 로그 저장소에 액세스 토큰·주민번호가 발견된다. 삭제 요청을 처리하려니 로그까지 뒤져야 한다.
- 보이는 형태: 요청 본문·헤더 전체를 찍는 디버그 로그. `Authorization: Bearer ...`가 그대로 남은 줄.
- 원인: "일단 다 찍자". 객체 `toString()`에 민감 필드가 들어 있다.
- 대처: OWASP Logging Cheat Sheet "Data to exclude"(세션 ID·액세스 토큰·비밀번호·연결 문자열·카드 정보 등)를 기준으로 마스킹 규칙을 둔다. 허용 목록 방식으로 필드를 고른다. 밖에서 온 값은 개행·제어 문자를 정리해 로그 주입을 막는다.

## 핵심 문장

- 로그는 사건 하나하나의 기록이다. 기계가 고를 수 있게 필드로 남기고(구조화), 요청 단위로 묶을 수 있게 상관 ID를 넣는다.
- MDC는 스레드에 붙어 있어 스레드풀을 건너지 않는다. 정리하지 않으면 다음 요청의 줄에 이전 요청의 ID가 찍힌다(실험).
- 동기 appender는 목적지의 느림을 요청 지연에 더하고, 비동기 appender는 그 대가로 유실이나 드문 긴 멈춤을 고르게 한다(실험: INFO 1800건 중 558~743건 전달, WARN 대기 약 530ms).
- 샘플링은 줄이 아니라 요청 ID로 고른다. 그래야 남은 요청을 처음부터 끝까지 볼 수 있다.
- 로그는 버려질 수 있는 기록으로 설계한다. 잃으면 안 되는 사건은 운영 로그 경로 밖에 둔다.

## 관련 주제·근거

- 선행
  - [01-fault-error-failure-availability](../01-fault-error-failure-availability/2-summary.md)
- 후속·연결
  - [16-metrics-and-golden-signals](../16-metrics-and-golden-signals/2-summary.md) — 로그 양·버린 수·디스크 사용률은 지표로 본다
  - [17-distributed-tracing](../17-distributed-tracing/2-summary.md) — 트레이스 ID를 상관 ID로, 스레드·큐 경계의 컨텍스트 전파
  - [18-logs-traces-audit-roles](../18-logs-traces-audit-roles/2-summary.md) — 버려도 되는 로그와 버리면 안 되는 감사·업무 기록
  - [43-alerting-and-on-call](../43-alerting-and-on-call/2-summary.md) — ERROR 줄 수가 아니라 증상으로 경보
  - [distributed/03-partial-failure-and-timeouts](../../distributed/03-partial-failure-and-timeouts/2-summary.md) — 타임아웃 로그가 말해 주지 않는 것
  - [network/50-network-diagnostics](../../network/50-network-diagnostics/2-summary.md)
  - [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md) — 유계 큐와 넘침 정책 일반
  - [52-reliability-symptom-index](../52-reliability-symptom-index/2-summary.md)
- 문서·명세
  - The Twelve-Factor App, XI. Logs <https://12factor.net/logs>
  - OpenTelemetry Logs Data Model (Status: Stable — 필드 목록, SeverityNumber 범위) <https://opentelemetry.io/docs/specs/otel/logs/data-model/>
  - Logback 1.5.18 소스 `logback-core/.../AsyncAppenderBase.java`(DEFAULT_QUEUE_SIZE 256, discardingThreshold = queueSize/5, neverBlock, drainTo, maxFlushTime 1000), `logback-classic/.../AsyncAppender.java`(isDiscardable: 레벨 ≤ INFO), `JsonEncoder.java` <https://github.com/qos-ch/logback/tree/v_1.5.18>
  - Apache Log4j 2 "Asynchronous loggers"(LMAX Disruptor, Trade-offs, `log4j2.asyncLoggerRingBufferSize` 기본 256 × 1024) <https://logging.apache.org/log4j/2.x/manual/async.html>
  - Spring Boot 3.4 Logging — Structured logging(ECS·GELF·Logstash), Correlation ID <https://docs.spring.io/spring-boot/reference/features/logging.html>
  - Spring Framework `TaskDecorator`·`ContextPropagatingTaskDecorator` javadoc
  - Docker "JSON File logging driver"(`max-size` 기본 -1) <https://docs.docker.com/engine/logging/drivers/json-file/>
  - OWASP Logging Cheat Sheet — Data to exclude <https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html>
- 실험 목록
  - A·B: Logback `JsonEncoder` + MDC, 고정 스레드풀(1)에서 MDC 미복사·복사·미정리 — JDK 21.0.12 temurin, Logback 1.5.18, `--cpus=2`
  - C: 2ms 지연 appender에 2000건(WARN 10%) — 동기 / AsyncAppender 기본 / neverBlock, 호출 지연 분위수와 전달 수, 3회 실행
  - D: 요청 1000 × 5줄, 10% 샘플링 — 줄 단위 무작위 vs 요청 ID 해시
