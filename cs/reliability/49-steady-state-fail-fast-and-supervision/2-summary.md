# reliability/49-steady-state-fail-fast-and-supervision — Steady State·Fail Fast·Let It Crash와 감독 트리·Handshaking·Governor·Test Harness — 정리 (힌트)

## 해결하는 문제

시스템을 오래 안정적으로 돌리려면 "빨리 처리하는 법" 말고도 네 가지 습관이 필요하다.

```text
 쌓이는 것을 치운다      Steady State   ── 없으면: 몇 달 뒤 디스크 풀·테이블 비대로 서서히 느려짐
 안 될 일은 입구에서 거절  Fail Fast      ── 없으면: 끝까지 가서야 실패 → 이미 한 부분 작업을 되돌려야 함
 망가지면 죽고 새로 시작  Let It Crash   ── 없으면: 손상된 상태로 계속 돌며 틀린 결과를 퍼뜨림
 자동화에 브레이크        Governor       ── 없으면: 정리 스크립트·스케일인이 폭주해 전부 지움
```

- 이 이름들은 Nygard 『Release It!』 2판 5장 "Stability Patterns"의 항목이다(pragprog.com 목차: Timeouts, Circuit Breaker, Bulkheads, Steady State, Fail Fast, Let It Crash, Handshaking, Test Harnesses, Decoupling Middleware, Shed Load, Create Back Pressure, Governor).
  - 이 노트는 그중 앞 노트들이 다루지 않은 여섯을 다룬다. Timeouts·Circuit Breaker·Bulkheads·Shed Load·Back Pressure는 [05](../05-timeouts-and-deadline-propagation/2-summary.md)·[10](../10-circuit-breaker/2-summary.md)·[28](../28-bulkhead/2-summary.md)·[12](../12-backpressure-and-load-shedding/2-summary.md) 노트에 있다.
  - 5장 본문은 열어 보지 못했다. 각 패턴의 **정의 문장**은 이 노트가 풀어 쓴 것이고, 책의 원문 표현과 다를 수 있다 `[?]`.

쉬운 예: 공장 생산 라인이다.
- 쓰레기통을 비우지 않으면 몇 주 뒤 라인이 멈춘다(Steady State).
- 부품이 다 있는지 작업 **시작 전에** 확인한다. 반쯤 조립하고 나서 부품이 없다는 걸 알면 분해해야 한다(Fail Fast).
- 기계가 이상한 소리를 내면 계속 돌리지 않고 멈춘 뒤 정비 담당(감독자)이 교체한다(Let It Crash).
- 자동 폐기 장치가 한 번에 치울 수 있는 양에 상한을 둔다(Governor).

똑같은 구조다.\
실무 예: 로그·세션·임시 테이블 보존 정책, 요청 입구 검증과 자원 예약, Erlang/OTP·Akka의 감독 트리, 쿠버네티스의 재시작 정책과 CrashLoopBackOff, 자동화 스크립트의 삭제 상한.

## 동작·원리

### 1. Steady State — 늘기만 하는 것을 치운다

```text
 요청마다 남는 것            치우는 장치 없으면                     치우는 장치
 로그 파일                  디스크 100% → 쓰기 실패 → 장애            로테이션 + 보존 기간
 세션·캐시 항목             힙 증가 → GC 지옥 → OOM                  TTL, 크기 상한(LRU)
 감사·이력 테이블            인덱스·백업 커짐 → 서서히 느려짐           파티션 + 오래된 파티션 drop, 아카이브
 큐·DLQ·임시 파일            저장소 한도                             보존 기간, 크기 상한
```

- *Steady State(정상 상태)*: 사람이 손대지 않아도 시스템이 오래 같은 상태로 돌 수 있게, 쌓이는 자원마다 치우는 장치를 둔다는 원칙.
  - 판단 질문: "이 자원은 무엇이 줄여 주나?" 답이 없으면 언젠가 찬다.
- 치우는 장치의 두 종류:
  - **시간 기준**(TTL, 보존 기간): "30일 지난 것은 지운다".
  - **크기 기준**(상한, 링 버퍼, LRU): "최근 1000개만 둔다".
  - *링 버퍼(ring buffer)*: 크기가 고정된 배열을 원형으로 써서, 가득 차면 가장 오래된 것을 덮어쓰는 구조.
- 정리 작업 자체도 부하다. 한 번에 1억 행 DELETE는 락·복제 지연·bloat를 만든다. 청크로 나눠 치운다([database/34-large-backfill-and-batch-dml](../../database/34-large-backfill-and-batch-dml/2-summary.md) 「동작·원리」 6, [database/29-soft-delete-and-data-lifecycle](../../database/29-soft-delete-and-data-lifecycle/2-summary.md)).

### 2. Fail Fast — 실패할 일이면 시작 전에

```text
 늦은 실패                                        빠른 실패
 ① 재고 차감 ─ ② 포인트 차감 ─ ③ 결제 호출 ✗       입구: 결제사 서킷 열림? 재고 충분? 입력 유효? 남은 시간 충분?
     └ ①②를 되돌려야 함 (보상, 실패 가능)              └ 아니면 바로 거절 (아무것도 안 함)
```

- *Fail Fast(빨리 실패)*: 요청을 끝까지 처리할 수 없다는 것을 **미리** 알 수 있으면, 일을 시작하기 전에 거절한다는 원칙.
- 입구에서 볼 수 있는 것:
  - 입력 검증(형식, 범위, 권한).
  - 필요한 자원이 지금 있는가(커넥션 풀 여유, 의존성의 서킷 상태, 남은 데드라인 — [08-time-budget-allocation](../08-time-budget-allocation/2-summary.md)).
  - 자원을 미리 **예약**할 수 있는가(재고 홀드, 풀에서 커넥션 먼저 빌리기).
- 빨리 실패한 응답은 빨라야 의미가 있다. 느린 실패는 호출자의 자원을 오래 붙잡는다([48](../48-performance-and-stability-antipatterns-in-code/2-summary.md) Blocked Threads).

### 3. Let It Crash와 감독 트리

```text
                    [최상위 감독자]
                     /           \
          [주문 감독자]            [알림 감독자]
          one_for_one             one_for_all
          /     |     \            /        \
     [워커1] [워커2] [워커3]    [연결]    [발송기]   ← 연결이 죽으면 발송기도 함께 재시작
 워커2가 죽음 → 주문 감독자가 워커2만 새로 시작 (다른 워커는 그대로)
 5초 안에 재시작이 너무 많음 → 주문 감독자도 포기하고 죽음 → 최상위 감독자가 판단 (escalate)
```

- *Let It Crash*: 예상 못 한 오류가 나면 그 자리에서 고치려 애쓰지 않고 프로세스를 끝낸다. 다른 프로세스(감독자)가 깨끗한 상태로 다시 시작한다. Armstrong 박사 논문(2003) 4.4절 제목이 "Let it crash"이고, 그 앞 4.3절(Error handling philosophy)의 4.3.1절이 "Let some other process fix the error"다(4.3.2 "Workers and supervisors"가 그 사이에 있다).
- *감독자(supervisor)*: 자식 프로세스를 시작하고, 지켜보고, 죽으면 정해진 규칙대로 재시작하는 프로세스. 감독자들이 나무 모양으로 쌓인 것이 *감독 트리(supervision tree)*다.
- 왜 고치지 않고 죽이나:
  - 예상 못 한 오류 뒤의 상태는 믿을 수 없다. 이어서 돌면 틀린 결과를 밖으로 내보낸다.
  - 새로 시작한 프로세스의 상태는 알려진 초기 상태다.
  - 전제: 재시작해도 잃으면 안 되는 상태는 프로세스 **밖**(DB·로그)에 있어야 한다.
- Erlang/OTP `supervisor` 문서(OTP 29.1.1, stdlib 8.1)의 규칙:
  - 재시작 전략: `one_for_one`(죽은 자식만, **기본값**), `one_for_all`(하나가 죽으면 전부), `rest_for_one`(죽은 자식과 그보다 뒤에 시작한 자식들), `simple_one_for_one`(같은 코드의 동적 자식들).
  - 재시작 강도: `intensity`(MaxR)와 `period`(MaxT). **MaxT초 안에 MaxR번보다 많이** 재시작이 일어나면 감독자는 자식을 모두 끝내고 자기도 끝난다. 기본값은 intensity 1, period 5.
  - 자식의 restart 종류: `permanent`(항상 재시작, 기본값), `transient`(비정상 종료일 때만), `temporary`(재시작 안 함).
- 재시작 강도가 있는 이유: 같은 원인으로 계속 죽는 자식(예: 처리할 때마다 실패하는 메시지)을 무한히 재시작하면 아무것도 나아지지 않는다. 위로 올려 더 큰 단위를 재시작하거나 사람에게 알린다.

### 실험 1: Erlang/OTP 감독자의 재시작 강도와 전략

- 자식 `w`는 시작 200ms 뒤 항상 죽는다. 자식 `a`는 1초마다 죽고 `b`는 안 죽는다.
- 감독자 플래그를 바꿔 가며 자식이 시작될 때 시각과 pid를 찍는다.

```erlang
init({Flags, Children}) ->
    {ok, {Flags, [#{id => N, start => {?MODULE, start_child, [N, C]}} || {N, C} <- Children]}}.
%% A: #{strategy => one_for_one, intensity => 3, period => 5}, 자식 [{w, 200}]
%% B: #{}  (기본값), 자식 [{w, 200}]
%% C: one_for_one, D: one_for_all — 자식 [{a, 1000}, {b, infinity}]
```

(실험, erlang:27-alpine(OTP 27), `--cpus=2`, 2026-10-01 — 시각은 실행마다 몇 ms 다르다)

```text
== A: intensity 3 / period 5  flags=#{intensity => 3,period => 5,
                                      strategy => one_for_one}
t=    0ms start w <0.84.0>
t=  205ms start w <0.85.0>
t=  406ms start w <0.86.0>
t=  607ms start w <0.87.0>
t=  808ms supervisor exit: shutdown
== B: defaults (empty flags)  flags=#{}
t=    0ms start w <0.89.0>
t=  201ms start w <0.90.0>
t=  402ms supervisor exit: shutdown
== C: one_for_one  flags=#{intensity => 10,period => 5,
                           strategy => one_for_one}
t=    0ms start a <0.92.0>
t=    0ms start b <0.93.0>
t= 1001ms start a <0.94.0>
t= 2002ms start a <0.95.0>
t= 2502ms supervisor alive -> cleanup
== D: one_for_all  flags=#{intensity => 10,period => 5,
                           strategy => one_for_all}
t=    0ms start a <0.97.0>
t=    0ms start b <0.98.0>
t= 1001ms start a <0.99.0>
t= 1001ms start b <0.100.0>
t= 2002ms start a <0.101.0>
t= 2002ms start b <0.102.0>
t= 2501ms supervisor alive -> cleanup
```

- 관찰 1 — A: 처음 시작 + 재시작 3번(pid 84→87). 네 번째 죽음에서 "5초 안에 3번보다 많이"가 되어 감독자가 끝났다(종료 이유 `shutdown`). 같은 실험을 OTP 오류 보고를 켜고 돌리면 마지막 보고가 `errorContext: shutdown`, `reason: reached_max_restart_intensity`다.
- 관찰 2 — B: 기본값이면 재시작 **1번**만 하고 두 번째 죽음에서 포기한다(intensity 1, period 5).
- 관찰 3 — C·D: `one_for_one`에서는 `b`의 pid(0.93)가 그대로다. `one_for_all`에서는 `a`가 죽을 때마다 `b`도 새 pid로 다시 시작됐다.
- 해석: 재시작 강도는 "일시적 오류는 재시작으로 넘기고, 계속되는 오류는 위로 올린다"를 숫자로 정한 것이다.

### 4. Handshaking — 받기 전에 물어본다

```text
 클라이언트 ── "지금 받을 수 있나?" ──> 서버        서버: 여유 있음 → 200 / 바쁨 → 503 + Retry-After
 (또는 서버가 먼저 "지금 N개까지만" 을 알려 줌 — 크레딧, 윈도)
```

- *Handshaking*: 일을 보내기 전에, 받는 쪽이 지금 받을 수 있는지 서로 확인하는 것. 받는 쪽이 "지금은 안 된다"고 말할 수 있어야 한다.
- 예: 서버가 과부하일 때 빨리 503과 `Retry-After`를 주는 것, 헬스체크·readiness로 LB에 "나 지금 못 받는다"를 알리는 것([14-graceful-shutdown](../14-graceful-shutdown/2-summary.md)), TCP·HTTP/2의 흐름 제어 윈도, 리액티브 스트림의 `request(n)`([12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md)).

### 5. Governor — 자동화에 속도 상한

```text
 자동화가 "지워도 됨"이라고 판단한 대상: 10대 (버그로 전부)
 Governor 없음: 10대 즉시 삭제
 Governor:      창(예: 10분)마다 최대 2대, 남는 비율 70% 미만이면 멈춤 → 사람에게 확인 요청
```

- *Governor(조속기)*: 자동화가 한 번에, 또는 단위 시간에 할 수 있는 일의 양에 상한을 두는 장치. 특히 지우기·축소·재시작 같은 파괴적 동작에 둔다. 자동화가 틀렸을 때 피해를 사람이 알아챌 수 있는 속도로 늦춘다.
- 사고 사례 — Google SRE 책 7장 "The Evolution of Automation at Google"의 "Automation: Enabling Failure at Scale":
  - 랙 하나를 폐기하던 자동화가 디스크 지우기(Diskerase) 단계를 끝낸 뒤 실패했다. 디버깅하려고 폐기 과정을 처음부터 다시 돌렸다.
  - 아직 지울 기계 집합은 (정확히) **빈 집합**이었다. 그런데 빈 집합이 특별값으로 "전부"로 해석됐다. 거의 모든 콜로(colo)의 기계가 Diskerase로 보내졌다.
  - 몇 분 만에 CDN의 모든 기계 디스크가 지워졌다. 자체 데이터센터로 사용자를 받아 바깥에는 지연 증가 정도만 보였다. 재설치에 이틀 가까이 걸렸다.
  - 이후 몇 주 동안 감사하고 **속도 제한을 포함한 sanity check**를 자동화에 넣고 폐기 워크플로를 멱등하게 만들었다.
- 해석: 빈 집합 = 전부라는 해석 버그는 테스트로 막을 수도 있었다. Governor는 그런 버그가 **있을 때도** 피해를 한정하는 마지막 장치다.

### 6. Test Harness — 나쁜 상대를 흉내 낸다

- *Test Harness(시험 장치)*: 통합 지점의 상대를 대신하는 가짜 서버. 정상 응답이 아니라 **나쁜 행동**(응답 안 함, 아주 느림, 연결 거절, 연결 직후 끊기, 헤더만 주고 멈춤, 거대한 응답, 깨진 데이터)을 골라 낼 수 있게 만든다.
- 목 객체(mock)는 코드 안의 인터페이스를 바꾼다. Test Harness는 **네트워크 수준**에서 바꾼다. 그래서 소켓 타임아웃·커넥션 풀·파서 같은 실제 코드 경로를 시험한다.
- 이 영역의 실험 다수가 작은 Test Harness다. 예: [48](../48-performance-and-stability-antipatterns-in-code/2-summary.md) 실험 6의 "5초 멈추는 외부 서버", [50](../50-sidecar-ambassador-and-service-mesh/2-summary.md) 실험의 "항상 503인 백엔드".

### 실험 2: Steady State·상태 오염·Governor (Java 시뮬레이션)

- Steady State: 요청 30만 건마다 기록 한 줄. 무한 리스트 vs 최근 1000개 링 버퍼(`ArrayDeque` + 오래된 것 제거).
- 상태 오염: 잔액 워커가 메시지 10개(`+10` × 9, 4번째에 `BAD`)를 처리한다. `BAD`는 잔액을 −1,000,000으로 망가뜨리고 불변식 검사(잔액 ≥ 0)에서 예외가 난다.
  - `swallow`: 예외를 잡고 같은 객체로 계속.
  - `crash`: 감독자가 워커를 버리고 마지막 확정 상태(30)로 새 워커를 시작.
- Governor: "유휴 판정" 버그로 10대 모두 유휴로 보인다. 상한 없음 vs 창당 2대·남는 비율 70% 상한.

```java
for (String m : msgs) {
    try { w.handle(m); }
    catch (IllegalStateException e) {
        if (swallow) { /* 로그만 찍고 같은 객체로 계속 */ }
        else { restarts++; w = new Worker(); w.balance = 30; }   // 새 워커 + 마지막 확정 상태
    }
    if (w.balance < 0) wrongOutputs++;                            // 밖으로 나간 잘못된 잔액 수
}
```

(실험, eclipse-temurin:21-jdk, `--cpus=2`, `-Xmx256m`, 2026-10-01 — 집필 2회 + 점검 2회. 힙 증가만 22~23MB로 조금 달랐고 나머지는 같았다)

```text
steady unbounded 요청 300000건 뒤 남은 기록 300000건, 힙 증가 약 23 MB
steady ring1000  요청 300000건 뒤 남은 기록 1000건, 힙 증가 약 0 MB
swallow 최종 잔액=-999940, 잘못된 잔액을 내보낸 횟수=7, 재시작=0
crash  최종 잔액=90, 잘못된 잔액을 내보낸 횟수=0, 재시작=1
governor off 삭제 10대, 남은 0대
  governor: 이번 창 삭제 2건 도달 → 멈추고 사람에게 확인 요청
governor on  삭제 2대, 남은 8대
```

- 관찰 1 — Steady State: 무한 리스트는 요청 수에 비례해 자랐다(30만 건에 약 22~23MB). 링 버퍼는 1000건에서 멈췄다. 하루 수천만 요청이면 무한 리스트는 며칠 안에 힙을 채운다(계산, 같은 비율 가정).
- 관찰 2 — 상태 오염: `swallow`는 망가진 잔액을 **7번**(BAD 처리 직후 + 그 뒤 6번) 밖으로 내보냈다. `crash`는 0번이다. 대신 `BAD` 메시지 자체는 처리되지 않고 버려졌다(최종 90 = 30 + 6×10). 그 메시지는 DLQ 같은 곳에 따로 남겨야 한다.
- 관찰 3 — Governor: 같은 버그에서 피해가 10대 → 2대로 줄고, 사람이 확인할 기회가 생겼다.
- 범위: 감독자·Governor는 직접 만든 축약 모델이다. 실제 감독자 동작은 실험 1(Erlang)이 근거다.

## 쓰이는 자료구조·알고리즘

- **감독 트리** — 감독자를 내부 노드, 워커를 잎으로 둔 나무. 재시작 전략(one_for_one·one_for_all·rest_for_one)은 "어느 부분 트리를 다시 시작하나"의 규칙이다.
- **재시작 강도 = 슬라이딩 윈도 카운터** — 최근 `period`초 안의 재시작 시각을 큐에 두고, 오래된 것을 빼고, 개수가 `intensity`를 넘으면 포기([11-rate-limiter](../11-rate-limiter/2-summary.md)의 슬라이딩 윈도와 같은 모양).
- **보존 정책** — TTL(시간), 크기 상한(링 버퍼, LRU), 파티션 단위 drop(시간 범위 파티션을 통째로 지우기).
- **Governor = 토큰 버킷/윈도 한도** — 파괴적 동작마다 토큰 하나. 토큰이 없으면 멈추고 사람에게 묻는다. 남는 비율 하한(예: 70%)을 함께 둔다.
- **불변식 검사** — 상태가 망가졌는지 아는 방법. 검사가 없으면 "죽어야 할 때"를 모른다.

## 적용 — 풀어나가는 법

### 1. Steady State 점검표

```text
 자원                       무엇이 줄여 주나            확인 명령·지표
 앱 로그 파일               logrotate / 로깅 드라이버 상한   df -h, du -sh /var/log/*
 컨테이너 로그(json-file)   --log-opt max-size,max-file     docker inspect -f '{{.HostConfig.LogConfig}}'
 세션·캐시                  TTL, maxmemory + 축출 정책      redis-cli INFO memory, 캐시 항목 수 지표
 이력·감사 테이블            파티션 + 보존 기간              pg_total_relation_size, 행 수 추이
 메시지 큐·DLQ              보존 기간·크기                  토픽 크기, DLQ 적체
```

- 각 자원에 "줄여 주는 장치"와 "그 장치가 동작하는지 보는 지표"를 짝으로 적는다. 정리 잡이 몰래 실패하면 Steady State가 깨진다 — 정리 잡에도 경보를 단다.

### 2. Fail Fast — 입구 검사 (Java)

```java
public Order place(OrderRequest req, Deadline dl) {
    validate(req);                                                        // 형식·범위·권한 — 400
    if (dl.remaining().compareTo(Duration.ofMillis(300)) < 0) throw new TooLate();   // 남은 시간 부족 — 504
    if (paymentBreaker.getState() == CircuitBreaker.State.OPEN) throw new Unavailable(); // 의존성 차단 — 503
    try (Connection c = pool.getConnection()) {                           // 자원 먼저 확보 (풀 대기 타임아웃 짧게)
        reserveStock(c, req);                                             // 재고 홀드 (예약)
        ...
    }
}
```

### 3. Let It Crash를 JVM에서

- JVM에는 Erlang 같은 가벼운 프로세스 감독자가 기본으로 없다. 비슷한 효과를 내는 층:
  - 작업 단위: 워커 객체를 버리고 새로 만든다(실험 2 `crash`). Akka의 액터 감독(재시작 전략)이 이 모양이다.
  - 프로세스 단위: 불변식이 깨지면 프로세스를 끝내고 오케스트레이터가 재시작한다. 쿠버네티스 `restartPolicy: Always`에서는 재시작이 반복되면 kubelet이 재시작 **간격**을 지수적으로 늘린다(10s, 20s, 40s … 최대 300s, 10분 문제없이 돌면 초기화 — 이 상태가 CrashLoopBackOff). 재시작 속도는 늦추지만 OTP 재시작 강도처럼 포기하고 위로 올리지는 않고 계속 재시작한다. 그래서 반복 재시작은 경보(재시작 횟수·CrashLoopBackOff 상태)로 사람에게 올려야 한다([Pod Lifecycle — Container restart policy](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#restart-policy)).
- 조건: 재시작해도 되는 설계여야 한다. 상태는 밖에, 처리는 멱등하게, 종료는 우아하게([14-graceful-shutdown](../14-graceful-shutdown/2-summary.md)).
- 처리할 때마다 죽게 만드는 메시지(poison pill)는 재시작으로 안 낫는다. 몇 번 실패하면 DLQ로 빼야 한다([distributed/18-consumer-failure-handling](../../distributed/18-consumer-failure-handling/2-summary.md)).

### 4. Governor (Java)

```java
final class Governor {
    private final int maxPerWindow; private final Duration window; private final double minKeepRatio;
    private final Deque<Instant> actions = new ArrayDeque<>();

    synchronized void permit(int baseline, int fleetAfter) {   // baseline: 작업 시작 때(정상 상태) 대수 — 고정
        Instant now = Instant.now();
        while (!actions.isEmpty() && actions.peekFirst().isBefore(now.minus(window))) actions.pollFirst();
        if (actions.size() >= maxPerWindow) throw new NeedsHuman("창당 상한 " + maxPerWindow + " 도달");
        if (fleetAfter < baseline * minKeepRatio) throw new NeedsHuman("남는 비율 하한 미만");
        actions.addLast(now);
    }
}
// 사용: int baseline = fleet.size();   // 루프 밖에서 한 번
//       governor.permit(baseline, fleet.size() - 1); deleteInstance(id);
// (현재 대수를 baseline으로 넘기면 "한 번에 1대"만 보게 되어 10대 중 3대까지 내려간다)
```

- 대상 집합이 비었거나 "전부"면 멈추는 sanity check를 함께 둔다(SRE 7장 사례의 빈 집합 버그).

### 5. 진단 명령

```bash
df -h; du -sh /var/log/* | sort -h | tail       # Steady State: 디스크
kubectl get pods -o wide | grep -i crashloop      # 재시작 반복
kubectl describe pod <p> | grep -A5 'Last State'  # 직전 종료 이유·종료 코드
```

```sql
-- 이력 테이블이 얼마나 자랐나 (PostgreSQL)
SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC LIMIT 10;
```

## 장애 시나리오와 대처

### 1. 정리 작업 없음 → 수개월 뒤 디스크 풀·테이블 비대

- 현상: 몇 달간 조금씩 느려지다가 어느 날 쓰기가 실패한다.
- 보이는 형태: `No space left on device`, 로그 디렉터리·이력 테이블이 디스크 대부분. 쿼리 계획은 같은데 인덱스가 커져 느려짐. 실험 2처럼 무한 컬렉션이 요청 수에 비례해 자람.
- 원인: 쌓이는 자원에 줄여 주는 장치가 없다. 또는 정리 잡이 조용히 실패하고 있었다.
- 대처: 자원마다 TTL·크기 상한·파티션 보존. 정리 잡의 성공·처리량을 지표로 보고 실패에 경보. 큰 정리는 청크로.

### 2. 자원 부족을 끝까지 가서야 발견 → 부분 처리 롤백

- 현상: 주문 처리 마지막 단계(결제)에서 실패해, 앞 단계의 재고·포인트 차감을 되돌리는 보상 작업이 자주 돈다. 보상도 가끔 실패한다.
- 보이는 형태: 보상 트랜잭션 로그가 많다. 결제 의존성의 서킷이 열려 있는 시간대와 겹친다.
- 원인: 실패를 미리 알 수 있었는데(서킷 열림, 남은 시간 부족) 입구에서 보지 않았다.
- 대처: 입구에서 서킷 상태·남은 데드라인·자원 여유를 보고 빨리 거절. 필요한 자원은 먼저 예약. 보상 경로는 여전히 둔다.

### 3. 손상된 상태로 계속 실행 → 오염 전파

- 현상: 한 인스턴스가 틀린 값을 계속 내보낸다. 재시작하니 멀쩡해졌다.
- 보이는 형태: 로그에 잡힌 예외 뒤에도 같은 인스턴스의 응답이 이상하다(실험 2 `swallow`: 잘못된 잔액 7번). 다른 인스턴스는 정상.
- 원인: 예상 못 한 예외를 `catch`하고 같은 상태로 계속 돌았다. 불변식 검사가 없거나, 위반해도 멈추지 않았다.
- 대처: 불변식 위반은 그 작업 단위(액터·워커·프로세스)를 버린다. 상태는 밖에서 다시 읽는다. 감독자가 재시작하고, 같은 원인이 반복되면 재시작 강도로 위로 올린다(실험 1).

### 4. 재시작이 무한 반복되며 아무것도 처리 못 함

- 현상: 프로세스가 몇 초마다 재시작된다. 처리량 0.
- 보이는 형태: CrashLoopBackOff, 같은 메시지 오프셋에서 계속 실패, Erlang이면 `reached_max_restart_intensity`.
- 원인: 재시작으로 안 낫는 원인(poison pill, 잘못된 설정, 없는 의존성). 재시작 강도·DLQ가 없으면 무한 반복이다.
- 대처: 재시작 강도를 두어 위로 올리고 경보. 메시지 단위 실패는 횟수 제한 뒤 DLQ로. 설정 오류는 기동 시 검증(Fail Fast)으로 바로 실패.

### 5. 자동 스케일인·정리 스크립트 폭주 → 전 인스턴스 삭제

- 현상: 몇 분 만에 서비스 인스턴스·데이터·디스크가 대부분 사라진다.
- 보이는 형태: 자동화 로그에 삭제 요청이 짧은 시간에 수십~수천. 대상 목록이 비었거나 "전부".
- 원인: 대상 판정 버그(지표 수집 실패 → 모두 유휴, 빈 집합 = 전부 — SRE 7장 Diskerase 사례) + 속도 상한 없음.
- 대처: Governor(창당 상한, 남는 비율 하한, 상한 도달 시 사람 확인), 빈 집합·전체 대상 거절, dry-run 기본, 워크플로 멱등화. SRE 7장 사례의 사후 조치도 속도 제한과 멱등화였다.

## 핵심 문장

- 늘기만 하는 자원에는 줄여 주는 장치가 있어야 한다. 실험에서 무한 리스트는 요청 수에 비례해 자랐고 링 버퍼는 1000건에서 멈췄다.
- 끝까지 가서 실패할 일이면 입구에서 거절한다. 늦은 실패는 이미 한 일을 되돌리는 비용을 남긴다.
- 예상 못 한 오류 뒤의 상태는 믿지 않는다. 실험에서 예외를 삼킨 워커는 망가진 잔액을 7번 내보냈고, 버리고 새로 시작한 워커는 0번이었다.
- 감독자는 일시적 오류는 재시작으로 넘기고 반복되는 오류는 위로 올린다. OTP 기본값은 5초 안에 재시작 1번보다 많으면 포기다(실험 B).
- 자동화가 틀릴 때를 대비해 속도 상한을 둔다. Google의 Diskerase 사고 뒤 조치도 속도 제한과 멱등화였다.

## 관련 주제·근거

- 선행
  - [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md) — Shed Load·Back Pressure(같은 장의 다른 패턴)
  - [14-graceful-shutdown](../14-graceful-shutdown/2-summary.md) — 재시작이 안전하려면 종료가 우아해야 한다
- 연결
  - [48-performance-and-stability-antipatterns-in-code](../48-performance-and-stability-antipatterns-in-code/2-summary.md) — 4장 안티패턴(이 노트는 5장 패턴)
  - [10-circuit-breaker](../10-circuit-breaker/2-summary.md) · [28-bulkhead](../28-bulkhead/2-summary.md) · [05-timeouts-and-deadline-propagation](../05-timeouts-and-deadline-propagation/2-summary.md) · [08-time-budget-allocation](../08-time-budget-allocation/2-summary.md) · [11-rate-limiter](../11-rate-limiter/2-summary.md)
  - [distributed/18-consumer-failure-handling](../../distributed/18-consumer-failure-handling/2-summary.md) — poison pill, DLQ
  - [database/29-soft-delete-and-data-lifecycle](../../database/29-soft-delete-and-data-lifecycle/2-summary.md) — 보존·삭제
  - language/14-concurrency-models(액터) — 영역 표 [../../language/README.md](../../language/README.md)(미작성)
- 책·논문·문서
  - Nygard, 『Release It!』 2판(2018) 5장 "Stability Patterns" — 항목 목록은 pragprog.com 목차로 확인, 본문 미열람 `[?]` <https://pragprog.com/titles/mnee2/release-it-second-edition/>
  - Armstrong, "Making reliable distributed systems in the presence of software errors", 박사 논문, KTH, 2003 — 4.3.1 "Let some other process fix the error", 4.4 "Let it crash", 감독 트리 <https://erlang.org/download/armstrong_thesis_2003.pdf>
  - Erlang/OTP `supervisor` 문서(OTP 29.1.1, stdlib 8.1 — 전략·intensity 1/period 5 기본값·restart 종류), "Supervisor Behaviour" 설계 원칙 <https://www.erlang.org/doc/apps/stdlib/supervisor.html>
  - Google SRE 책 7장 "The Evolution of Automation at Google" — "Automation: Enabling Failure at Scale"(Diskerase) <https://sre.google/sre-book/automation-at-google/>
- 실험 목록
  - E49a Erlang/OTP 27 감독자 — intensity 3/period 5, 기본값, one_for_one vs one_for_all — erlang:27-alpine(받은 뒤 삭제), 코드 `demo.erl`
  - E49b Java 시뮬레이션 — 무한 리스트 vs 링 버퍼, 상태 오염 swallow vs crash, Governor — JDK 21, 코드 `Supervise.java`
