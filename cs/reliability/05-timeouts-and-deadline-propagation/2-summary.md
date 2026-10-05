# reliability/05-timeouts-and-deadline-propagation — 타임아웃 계층 정렬과 데드라인 전파 — 정리 (힌트)

## 해결하는 문제

원격 호출에 타임아웃이 없으면, 응답이 오지 않는 호출 하나가 스레드 하나를 무한히 잡는다.\
타임아웃이 있어도 계층마다 따로 정하면, 바깥이 이미 포기한 요청을 안쪽이 계속 처리한다.

```text
 타임아웃 없음                         계층 역전(안쪽이 더 김)
 클라 ──> 서버 ──> 하류(응답 없음)       클라(1s) ──> A(5s) ──> B(5s) ──> C(3초짜리 일)
          스레드가 영원히 묶인다          1초에 클라가 떠났는데 C는 3초까지 일한다 → 헛일
          → 스레드 풀이 바닥난다          결과를 받을 사람이 없다
```

- *타임아웃(timeout)*: 이 호출의 응답을 **얼마나 오래** 기다릴지 정한 상대 시간. 내 인내심이다.
- *데드라인(deadline)*: 이 요청이 **언제까지** 끝나야 하는지 정한 절대 시각. 요청의 수명이다.
- *데드라인 전파(deadline propagation)*: 요청을 받은 서버가 하류를 부를 때, 자기가 받은 데드라인에서 이미 쓴 시간을 뺀 나머지를 넘기는 것.

쉬운 예: 심부름이다.
- 엄마가 "6시까지 두부 사 와"라고 했다. 형이 동생에게 다시 시키면서 "천천히 해, 한 시간 줘"라고 말한다.
- 6시에 엄마는 다른 반찬을 만들기로 했는데, 동생은 6시 반까지 두부를 찾아 헤맨다.
- 형이 "엄마가 6시까지래. 나 여기까지 10분 썼으니 너는 50분 남았어"라고 넘겼으면 헛걸음이 없다.

똑같은 구조다.\
실무 예: gRPC의 데드라인(`grpc-timeout` 헤더로 자동 전파), Go `context.WithDeadline`, 게이트웨이 → 서비스 → DB 경로의 타임아웃 정렬.

기초(타임아웃 ≠ 데드라인, 고아 작업, 진입점·스레드·DB·외부·큐 계층별 전파, 취소가 닿지 않는 곳)는 원본 [ops-patterns/deadline-propagation](../../ops-patterns/deadline-propagation/2-summary.md) §1~§4에 자세하다.\
층별 예산 그림은 [systems/server-design/06-resilience.md](../../systems/server-design/06-resilience.md) §2 「타임아웃 — 모든 것의 출발점」에 있다.\
이 노트는 (1) 정렬 규칙 (2) gRPC가 데드라인을 **선로에 싣는 방식** (3) 서버가 질 책임을 1차 출처로 확인하고, 세 가지 전파 방식을 실험으로 비교한다.\
예산을 단계에 나누는 설계는 [08-time-budget-allocation](../08-time-budget-allocation/2-summary.md), 작업을 실제로 멈추는 법은 [09-cancellation-propagation](../09-cancellation-propagation/2-summary.md)에서 깊게 다룬다.

## 동작·원리

### 1. 정렬 규칙 — 바깥이 길고 안쪽이 짧다

```text
 사용자 ── 게이트웨이 ── 서비스 A ── 서비스 B ── DB
          3.0 s        2.5 s       2.0 s       1.5 s     (예시)
          ─────────────────────────────────────────>
          바깥이 길다                          안쪽이 짧다
```

- 안쪽이 먼저 터져야 바깥이 그 실패를 받아 처리(폴백·에러 응답)할 시간이 있다.
- 반대면 바깥이 먼저 떠난다. 안쪽은 끝까지 일하지만 결과를 받을 사람이 없다.
- 그런데 고정값으로 정렬해도 빈틈이 남는다.
  - A가 B를 부르기 전에 이미 1.8초를 썼다면, B에게 2.0초를 주는 것은 거짓말이다. 남은 것은 0.7초다.
  - 그래서 고정 정렬만으로 부족하고 **남은 시간을 실어 보내는** 전파가 필요하다.

### 2. 전파 — 절대 시각을 기억하고, 선로에는 남은 시간을 싣는다

gRPC Deadlines 가이드의 예를 그대로 그리면 이렇다.

```text
 13:00:00.0  클라이언트: 2초 안에 끝나야 한다 → 데드라인 13:00:02
     │  GetUserProfile (deadline 13:00:02)
     v
 User 서버:  0.5초 일하고 Billing을 부른다
     │  GetTransactionHistory (timeout 1.5s)   ← 절대 시각이 아니라 "남은 1.5초"
     v
 Billing 서버: 받은 순간 + 1.5초 = 자기 시계로 데드라인을 다시 만든다
 13:00:02    시간 끝 → 클라이언트 DEADLINE_EXCEEDED, 서버 쪽 호출은 취소(Cancel)
```

- gRPC는 데드라인을 그대로 보내지 않는다. 이미 흐른 시간을 뺀 **타임아웃으로 바꿔** 보낸다(gRPC Deadlines 가이드 "Deadline Propagation").
  - 이유: 두 서버의 시계가 맞지 않을 수 있다. 상대 시간으로 보내면 시계 어긋남(clock skew)의 영향을 받지 않는다.
  - *시계 어긋남(clock skew)*: 서로 다른 기계의 벽시계가 같은 순간에 다른 값을 가리키는 것. [distributed/04-physical-clocks-and-ntp](../../distributed/04-physical-clocks-and-ntp/2-summary.md).
- 선로 형식: HTTP/2 헤더 `grpc-timeout`. 값은 8자리 이하 양의 정수 + 단위(H·M·S·m·u·n)다. 예: `grpc-timeout: 1S`(gRPC PROTOCOL-HTTP2.md).
  - 헤더가 없으면 서버는 무한 타임아웃으로 가정한다(같은 문서). 클라이언트 기본도 데드라인 없음이다(gRPC Deadlines 가이드).
- 자동 전파는 구현마다 다르다. 가이드는 Java·Go는 기본으로 켜져 있고, C++은 명시적으로 켜야 한다고 적는다.
- 남는 오차: 선로를 건너는 시간(전송 지연)은 빠지지 않는다. 받는 쪽은 "받은 순간"부터 센다.
  - SRE 22장은 그래서 나가는 데드라인을 수백 ms쯤 줄이는 것을 고려하라고 적는다(전송 시간·클라이언트 후처리 몫).

### 3. 서버의 책임 — 취소를 알아채고 스스로 멈춘다

```text
 데드라인 지남
   │
   ├─ gRPC 라이브러리: 그 호출을 CANCELLED로 끝낸다(응답을 더 받지 않는다)
   │
   └─ 애플리케이션 코드: ??? ← 여기가 비면 일은 계속 돈다
        필요한 것: 단계마다 "남은 시간 > 0 ?"을 확인 → 아니면 멈추고 하류 호출도 취소
```

- gRPC Deadlines 가이드: 서버는 데드라인이 지나면 호출을 자동으로 취소(`CANCELLED`)하지만, **그 RPC를 위해 시작한 활동을 멈추는 것은 서버 애플리케이션의 책임**이다. 오래 걸리는 처리는 주기적으로 취소 여부를 확인해야 한다.
- SRE 22장 "Missing deadlines": 여러 단계로 처리하는 요청은 **각 단계 전에** 남은 시간을 확인하라. 마감이 지난 요청을 처리해도 "늦은 과제에는 점수가 없다(you don't get credit for late assignments)".
- 예외도 있다. SRE 22장은 체크포인트를 남기며 진행하는 비싼 따라잡기 작업은 데드라인 뒤에도 계속할 가치가 있을 수 있다고 적는다(배치는 [32-batch-and-job-time-bounds](../32-batch-and-job-time-bounds/2-summary.md)).

### 4. 타임아웃이 아예 없을 때 — 스레드 고갈 계산

SRE 22장 "Bimodal latency"의 계산을 옮긴다.

```text
 프런트엔드 10대 × 워커 100 = 스레드 1,000
 평소: 1,000 QPS × 0.1 s = 스레드 100개 사용
 사고: 요청의 5%가 끝나지 않음, 데드라인 100 s
       5% = 50 QPS × 100 s = 스레드 5,000개 필요  (가진 것은 1,000)
 결과: 처리 가능 비율 = 1,000 / (5,000 + 95) = 19.6%  → 에러율 80.4%
```

- 5%만 문제가 있었는데 80%가 실패한다. 끝나지 않는 요청이 스레드를 다 먹기 때문이다.
- SRE는 평균 지연보다 몇 자릿수 긴 데드라인은 대개 나쁘다고 적는다. 이 예는 평균의 1,000배였다.
- 타임아웃이 "없음"인 것과 "지나치게 긴 것"은 이 계산에서 거의 같다.

### 5. 실험: 전파 없음 vs 절대 시각 전파 vs 남은 시간 전파

- 구성: 클라이언트 → A → B → C. 한 JVM 안의 HTTP 서버 셋(JDK `HttpServer` + `HttpClient`).
  - 클라이언트는 1초 타임아웃으로 부른다. A·B는 각자 50ms 일한 뒤 하류를 부른다.
  - C는 100ms짜리 단계를 30번(3초) 한다. 예산을 받으면 단계마다 데드라인을 확인한다.
- 세 방식
  - none: 각 홉이 고정 5초 타임아웃(안쪽이 바깥 1초보다 긺 = 역전). 전파 없음.
  - absolute: 클라이언트의 절대 만료 시각(epoch ms)을 헤더로 그대로 전파. **C의 시계만 2초 늦게** 흉내 냈다.
  - relative: 남은 ms를 헤더로 전파(gRPC 방식). 각 홉이 받은 순간 + 남은 ms로 자기 시계의 만료 시각을 다시 만들고, 하류에는 그 시각 - 지금을 넘긴다.

핵심 코드(Java):

```java
// B가 C를 부를 때 — relative 방식
long deadline = arrived + Long.parseLong(req.header("X-Remaining-Ms")); // 내 시계로 다시 만든 만료 시각
long remaining = deadline - now();                                        // 내가 쓴 시간을 뺀다
if (remaining <= 0) return reply(504, "예산 소진, 하위 호출 안 함");
downstream.header("X-Remaining-Ms", String.valueOf(remaining))
          .timeout(Duration.ofMillis(remaining));                          // 내 기다림도 남은 예산으로

// C — 단계마다 확인(협조적 취소)
for (int i = 0; i < 30; i++) {
    if (now() >= deadline) { log("데드라인 확인 → " + i + "단계에서 중단"); break; }
    doStep();   // 100ms
}
```

(실험, JDK 21.0.12 Temurin, 컨테이너 `--cpus=2`, 2026-10-01 — t는 클라이언트가 요청을 시작한 시각 기준)

```text
== mode=none
t=    0ms client: 요청 시작, 타임아웃 1000ms
t=   66ms A: 고정 타임아웃 5초로 하위 호출
t=  124ms B: 고정 타임아웃 5초로 하위 호출
t=  129ms C: 시작, 내 시계 기준 남은 예산 없음
t= 1012ms client: 1초 타임아웃 — 포기
t= 3134ms C: 30단계 모두 완료 — 응답을 쓰지만 받을 사람이 없다
t= 3141ms 응답 쓰기 실패(상대가 이미 끊음): Broken pipe
t= 5017ms 결과: C가 한 단계 30개 중 클라이언트 포기 뒤 단계 22개 (헛일)
== mode=absolute
t=    0ms client: 요청 시작, 타임아웃 1000ms
t=   89ms A: 절대 만료 시각 그대로 전달(내 시계로 남은 919ms)
t=  145ms B: 절대 만료 시각 그대로 전달(내 시계로 남은 855ms)
t=  149ms C: 시작, 내 시계 기준 남은 예산 2851ms
t= 1005ms B: 하위 타임아웃 → 하위 호출 포기
t= 1008ms client: 1초 타임아웃 — 포기
t= 3055ms C: 데드라인 확인 → 29단계에서 중단
t= 5014ms 결과: C가 한 단계 29개 중 클라이언트 포기 뒤 단계 21개 (헛일)
== mode=relative
t=    0ms client: 요청 시작, 타임아웃 1000ms
t=   72ms A: 남은 예산 949ms를 하위에 전달
t=  128ms B: 남은 예산 898ms를 하위에 전달
t=  133ms C: 시작, 내 시계 기준 남은 예산 898ms
t= 1010ms client: 1초 타임아웃 — 포기
t= 1023ms A: 하위 타임아웃 → 하위 호출 포기
t= 1027ms B: 하위 타임아웃 → 하위 호출 포기
t= 1035ms C: 데드라인 확인 → 9단계에서 중단
t= 5017ms 결과: C가 한 단계 9개 중 클라이언트 포기 뒤 단계 1개 (헛일)
```

(응답 쓰기 실패 줄 일부는 생략했다. 같은 실험을 두 번 더 돌린 결과 줄은 none 30/22, absolute 29/21, relative 9/1로 같았다.)

- 관찰 1 — none: 클라이언트는 1초에 떠났는데 C는 3.1초까지 30단계를 다 했다. 그중 22단계가 헛일이다. 응답은 `Broken pipe`로 버려졌다.
- 관찰 2 — absolute: 같은 만료 시각을 넘겼는데도 C는 "2851ms 남았다"고 믿었다. C의 시계가 2초 늦기 때문이다. 헛일 21단계로 전파 없음과 거의 같다.
- 관찰 3 — relative: C는 자기 시계로 898ms를 받았고, 클라이언트 포기 25ms 뒤에 멈췄다. 헛일은 1단계다.
- 관찰 4 — relative에서도 C가 클라이언트보다 약 25ms 늦게 멈췄다(재실행에서 24~29ms — 실행마다 다르다). A가 받은 예산(1000)에서 클라이언트 → A 전송·연결 시간이 빠지지 않았다(A는 t=72ms에 949ms를 넘겼다 = 자기가 받은 뒤 쓴 약 51ms만 뺐고, 요청 시작부터 A 도착까지의 약 20ms는 빠지지 않았다). SRE가 말한 "전송 시간만큼 줄여 보내라"가 이 틈이다. C가 100ms 단계 사이에서만 확인하므로 단계 크기만큼 더 늦을 수도 있다.
- 해석: 데드라인을 전파해도 **받는 쪽이 확인하지 않으면** 아무 일도 일어나지 않는다. C의 단계별 확인이 멈춤을 만든 것이다(3절).

## 쓰이는 자료구조·알고리즘

- **남은 예산 계산** — `remaining = deadline - now()`. 차감만 하고 늘리지 않는다. Go `context.WithDeadline`은 부모보다 늦은 데드라인을 주면 부모와 같게 본다(Go `context` 문서). 자식이 부모보다 오래 살 수 없다.
- **단조 시계** — 경과 시간은 벽시계가 아니라 단조 시계로 잰다. Java `System.nanoTime()`은 경과 시간 측정용이고 벽시계와 관계가 없다(Java SE API). 벽시계는 NTP 조정으로 뒤로 갈 수 있다([distributed/04-physical-clocks-and-ntp](../../distributed/04-physical-clocks-and-ntp/2-summary.md)). 이 노트의 실험은 출력 편의로 `currentTimeMillis`를 썼다.
- **호출 트리** — 요청 하나가 만드는 RPC는 트리다. SRE 22장: 트리의 모든 RPC가 **같은 절대 데드라인**을 갖는다. 각 간선에는 그 시점의 남은 시간이 실린다.
- **타이머** — 타임아웃마다 타이머가 하나 걸린다. 많은 타이머를 싸게 관리하는 구조(타이머 힙·계층형 타이머 휠)는 [data-structure/26-timer-structures](../../data-structure/26-timer-structures/2-summary.md). 힙은 [data-structure/07-heap](../../data-structure/07-heap/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. 호출 경로를 바깥부터 적는다(게이트웨이 → 서비스 → 하류·DB·외부).
2. 맨 바깥 데드라인을 정한다(SLO에서 — [08](../08-time-budget-allocation/2-summary.md)).
3. 고정 타임아웃은 바깥 > 안쪽으로 정렬한다. 데드라인 전파가 없는 구간의 마지막 방어선이다.
4. 전파 수단을 하나로 정한다. gRPC면 내장 데드라인, HTTP면 팀이 정한 헤더(남은 ms) 하나.
5. 서버 진입점에서 받은 값을 **자기 시계의 절대 시각**으로 바꿔 요청 문맥에 넣는다. 헤더가 없으면 서버 기본 데드라인을 만든다.
6. 하류 호출마다 `min(내 기본 타임아웃, 남은 예산 - 여유)`를 쓴다. 남은 예산이 0 이하면 부르지 않는다.
7. 긴 처리는 단계마다 남은 시간을 확인한다. 실제 중단 방법은 [09](../09-cancellation-propagation/2-summary.md).
8. 지표: "데드라인이 지난 뒤 끝난 작업 수"를 센다. 0이 아니면 전파가 끊겼을 수 있다는 조사 신호다. 일부러 끝까지 하는 작업(위 체크포인트 예외)인지 함께 본다.

### 2. 코드 — Java, 요청 문맥의 데드라인

```java
/** 요청 하나의 데드라인. 단조 시계 기준. */
public record Deadline(long expiresAtNanos) {
    public static Deadline after(Duration d) { return new Deadline(System.nanoTime() + d.toNanos()); }
    public static Deadline fromHeader(String remainingMs, Duration serverDefault) {
        return remainingMs == null ? after(serverDefault) : after(Duration.ofMillis(Long.parseLong(remainingMs)));
    }
    public Duration remaining() { return Duration.ofNanos(Math.max(0, expiresAtNanos - System.nanoTime())); }
    public boolean expired() { return System.nanoTime() >= expiresAtNanos; }
    /** 하류로 넘길 값: 남은 시간에서 전송·후처리 몫(margin)을 뺀다 */
    public Duration forDownstream(Duration margin, Duration cap) {
        Duration r = remaining().minus(margin);
        return r.compareTo(cap) > 0 ? cap : r;
    }
}

// 하류 호출
Duration t = deadline.forDownstream(Duration.ofMillis(50), Duration.ofSeconds(2));
if (t.isNegative() || t.isZero()) throw new DeadlineExceededException("하류 호출 전 예산 소진");
HttpRequest req = HttpRequest.newBuilder(uri)
        .header("X-Remaining-Ms", String.valueOf(t.toMillis()))
        .timeout(t)
        .build();
```

- 헤더 이름 `X-Remaining-Ms`는 예시다. HTTP에는 표준 헤더가 없다(원본 §3-1). 모든 서비스가 같은 이름을 읽어야 한다.
- gRPC Java는 `stub.withDeadlineAfter(2, TimeUnit.SECONDS)`로 데드라인을 걸고, 서버 안에서 하류 stub을 같은 `Context`에서 부르면 데드라인이 따라간다(gRPC Deadlines 가이드 "Language Support"의 Java 예).

### 3. 프록시가 붙이는 헤더는 "남은 시간"이 아닐 수 있다

- Envoy는 상류로 `x-envoy-expected-rq-timeout-ms`를 붙인다(라우터의 `suppress_envoy_headers`가 꺼져 있고, 계산된 timeout이 0(무한)이 아닐 때). 문서는 값이 `x-envoy-upstream-rq-timeout-ms` 헤더나 **라우트 timeout**에서 온다고 적는다(Envoy router filter 문서).
  - Envoy 1.39.1 소스(`source/common/router/router.cc` `setTimeoutHeaders`)로 보면 더 정확히는 이렇다. per-try timeout이 있으면 그 값, 없으면 전체(route) timeout을 쓴다. 단 `hedge_on_per_try_timeout`이 켜져 있거나 per-try가 전체 timeout 이상이면(무시됨) 전체 timeout을 쓴다. 재시도 때는 `min(그 값, 전체 timeout - 이 Envoy가 하류 요청을 다 받은 뒤 흐른 시간)`으로 줄인다.
  - 즉 줄어드는 것은 **이 Envoy 자신의** 전체 timeout 안에서뿐이다. 게이트웨이까지 오는 데 쓴 시간(클라이언트·앞 홉)은 빠지지 않는다.
- 35번 실험에서는 `per_try_timeout: 1s`를 둔 라우트(route timeout 3.5s)에서 이 헤더가 `1000`으로 왔다(Envoy 1.39.1). [35-timeout-design-worksheet](../35-timeout-design-worksheet/2-summary.md).

### 4. 진단

```bash
# 시작부터 각 단계 끝까지의 누적 시간(초): DNS·연결·TLS·첫 바이트·전체
curl -s -o /dev/null -w 'dns=%{time_namelookup} connect=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total}\n' https://api.example.com/x
# gRPC: 실제 전송된 grpc-timeout은 받는 서버 쪽 헤더 로그로 확인한다.
# grpcurl -v의 "Request metadata to send"는 사용자가 준 메타데이터만 보이고, -max-time이 만드는 grpc-timeout은 안 보인다(grpcurl format.go·invoke.go).
grpcurl -v -max-time 2 -d '{}' host:443 pkg.Svc/Method
```

- PromQL 예(지표 이름은 예시): 데드라인이 지난 뒤 끝난 작업 비율

```text
sum(rate(work_completed_after_deadline_total[5m])) / sum(rate(work_completed_total[5m]))
```

## 장애 시나리오와 대처

### 1. 하류 타임아웃 > 상류 — 이미 포기한 요청을 계속 처리 (⚠ 커리큘럼)

- 현상: 과부하 때 하류 CPU·DB 부하가 요청량보다 훨씬 크다. 사용자는 타임아웃을 보는데 하류는 바쁘다.
- 보이는 형태: 하류 로그에 `Broken pipe`·`connection reset`이 응답 쓰기 시점에 몰린다(5절 실험 none). 하류 처리 시간 분포가 상류 타임아웃보다 긴 쪽에 몰려 있다.
- 원인: 타임아웃이 역전돼 있거나, 정렬돼 있어도 남은 시간을 전파하지 않는다.
- 대처: 바깥 > 안쪽 정렬, 남은 시간 전파, 하류의 단계별 확인. 측정 지표 "데드라인 뒤 완료 수".

### 2. 타임아웃 없음 → 스레드 고갈 (⚠ 커리큘럼)

- 현상: 의존 서비스 하나가 응답하지 않자 전체 서비스가 거의 모든 요청에 실패한다.
- 보이는 형태: 스레드 덤프(`jcmd <pid> Thread.print`)에 같은 소켓 읽기·connect에서 멈춘 스레드가 풀 크기만큼 있다. 요청 큐 길이·대기 시간이 치솟는다. 평균 지연만 보면 원인이 안 보인다(SRE "Bimodal latency").
- 원인: 클라이언트 기본값이 무한이다. JDK `HttpClient`는 요청 timeout을 안 걸면 무한히 기다린다(JDK 21 API 문서). gRPC 클라이언트도 기본 데드라인이 없다.
- 대처: 모든 원격 호출에 타임아웃(4절 계산: 문제 요청 5%가 에러율 80%로 번진다). 끝날 수 없는 요청은 빨리 실패(fail fast). 의존 서비스별 격벽([28-bulkhead](../28-bulkhead/2-summary.md)).

### 3. 절대 시각을 그대로 전파 — 시계 어긋남으로 예산이 늘거나 준다

- 현상: 특정 서버만 데드라인 초과를 거의 안 내거나, 반대로 받자마자 초과로 거절한다.
- 보이는 형태: 그 서버의 NTP 오프셋이 크다(`chronyc tracking`의 System time). 5절 absolute처럼 "남은 2851ms"를 믿고 계속 일한다.
- 원인: epoch 시각을 선로에 실었다. 받는 쪽 시계가 늦으면 예산이 늘고, 빠르면 준다.
- 대처: 선로에는 남은 시간(상대값)을 싣고, 받는 쪽이 자기 단조 시계로 만료 시각을 만든다(gRPC 방식).

### 4. 전파가 중간에서 끊긴다 — 스레드 풀·큐·비동기 경계

- 현상: 진입점은 데드라인을 받는데, 비동기로 넘긴 작업이나 큐 소비자는 끝까지 돈다.
- 보이는 형태: 트레이스에서 상위 스팬은 끝났는데 자식 스팬이 한참 뒤에 끝난다([17-distributed-tracing](../17-distributed-tracing/2-summary.md)).
- 원인: 새 스레드·메시지는 부모의 데드라인을 모른다(원본 §3-2·§3-5).
- 대처: 작업 객체·메시지에 만료 시각을 담는다. 꺼낼 때 만료면 버리고 센다.

### 5. 데드라인이 너무 짧다 — 비싼 요청이 늘 실패한다

- 현상: 특정 요청 유형(큰 페이로드, 계산량이 많은 조회)만 꾸준히 실패한다.
- 보이는 형태: 실패가 요청 유형별로 몰린다. 서버 자원은 한가하다.
- 원인: SRE 22장 "Picking a deadline": 짧은 데드라인은 더 비싼 요청을 일관되게 실패시킬 수 있다. 트래픽 구성을 모르고 상한을 걸었다.
- 대처: 요청 유형별 데드라인, 분포를 보고 정한다([08](../08-time-budget-allocation/2-summary.md)).

## 핵심 문장

- 타임아웃은 바깥이 길고 안쪽이 짧게 정렬한다. 그러나 고정값 정렬은 이미 쓴 시간을 모르므로, 남은 시간을 실어 보내는 데드라인 전파가 필요하다.
- gRPC는 절대 데드라인을 기억하되 선로(`grpc-timeout`)에는 이미 흐른 시간을 뺀 타임아웃을 싣는다. 받는 쪽이 자기 시계로 다시 만들어 시계 어긋남을 피한다.
- 데드라인이 지나면 gRPC는 호출을 취소하지만, 시작한 일을 멈추는 것은 서버 코드의 책임이다. 단계마다 남은 시간을 확인해야 한다.
- 실험에서 전파 없음은 클라이언트 포기 뒤 22단계, 절대 시각 전파(시계 2초 어긋남)는 21단계, 남은 시간 전파는 1단계의 헛일을 했다.
- 타임아웃이 없으면 일부 요청의 멈춤이 스레드를 다 먹는다. SRE 예에서 5%의 멈춤이 80.4% 에러가 됐다.

## 관련 주제·근거

- 선행
  - [distributed/03-partial-failure-and-timeouts](../../distributed/03-partial-failure-and-timeouts/2-summary.md) — 타임아웃은 "모름"을 만든다, 값 고르기
  - 원본 [ops-patterns/deadline-propagation](../../ops-patterns/deadline-propagation/2-summary.md) — 계층별 전파·고아 작업·보상
  - 원본 [systems/server-design/06-resilience.md](../../systems/server-design/06-resilience.md) §2 — 타임아웃 예산 그림. 참고: 원본 §2의 "p99 응답 시간의 2~3배로 시작"은 출발점 휴리스틱이다. AWS Builders' Library는 허용 오탐률(예: 0.1%)을 고르고 그에 맞는 하류 백분위(예: p99.9)에서 시작한다고 적는다 — 근거 있는 방법은 [08](../08-time-budget-allocation/2-summary.md)에서 다룬다.
- 후속
  - [07-timeout-taxonomy-by-layer](../07-timeout-taxonomy-by-layer/2-summary.md) — 호출 하나에 달린 타임아웃의 종류
  - [08-time-budget-allocation](../08-time-budget-allocation/2-summary.md) — 예산을 단계에 나누기
  - [09-cancellation-propagation](../09-cancellation-propagation/2-summary.md) — 실제로 멈추기
  - [06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md) — 재시도와 데드라인
  - [database/22-database-side-timeouts](../../database/22-database-side-timeouts/2-summary.md) — DB 쪽 한도
- 문서·글
  - gRPC "Deadlines" 가이드 — 클라이언트 기본 데드라인 없음, 서버 자동 취소 + 애플리케이션 책임, 경과 시간을 뺀 타임아웃으로 전파(시계 어긋남), Java·Go 기본 자동 전파 <https://grpc.io/docs/guides/deadlines/>
  - gRPC PROTOCOL-HTTP2.md — `grpc-timeout` = TimeoutValue(8자리 이하) + TimeoutUnit, 생략 시 무한 <https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md>
  - Google SRE 책 22장 "Addressing Cascading Failures" — Picking a deadline, Missing deadlines, Deadline propagation(30초 → 23초 → 19초 예, 수백 ms 줄이기), Cancellation propagation, Bimodal latency(19.6%·80.4%) <https://sre.google/sre-book/addressing-cascading-failures/>
  - Go `context` 패키지 문서 `WithDeadline`
  - Envoy router filter 문서 `x-envoy-expected-rq-timeout-ms`
  - JDK 21 API `HttpRequest.Builder.timeout`(설정 안 하면 무한), `System.nanoTime`
- 실험 목록
  - Chain.java — 클라이언트(1s) → A → B → C(3초 작업), 전파 none / absolute(C 시계 -2초) / relative 비교, 각 3회. JDK 21.0.12 Temurin 컨테이너 `--cpus=2`, 한 JVM 안 HTTP 서버 3개(127.0.0.1)
