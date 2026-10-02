# reliability/12-backpressure-and-load-shedding — 역압·큐 한도·우선순위 셰딩 — 정리 (힌트)

## 해결하는 문제

들어오는 요청이 처리 능력보다 많으면 남는 요청은 어딘가에 쌓인다.\
쌓이는 곳에 한도가 없으면 서버는 "모두를 받아서 모두를 늦게" 처리한다.\
그러다 처리한 응답이 전부 클라이언트의 기다림 한도를 넘기면, 일은 하는데 쓸모 있는 결과가 0이 된다.

```text
 도착 300/s ──> [ 큐 ............................... ] ──> 처리 200/s
                 매초 약 100개씩 자란다
 1초 뒤: 대기 0.5초     → 아직 응답이 쓸모 있다
 3초 뒤: 대기 1.5초     → 클라이언트는 0.3초에 이미 포기했다. 서버는 "버려진 요청"만 처리 중
 계속:   메모리 증가 → GC → 더 느려짐 → OOM
```

쉬운 예: 콜센터 대기열이다.
- 상담원 열 명이 1분에 열 통을 받는데 스무 통이 걸려 온다.
- 대기열에 한도가 없으면 대기 시간이 끝없이 늘어난다. 고객은 기다리다 끊고 다시 건다.
- 상담원이 받는 전화는 이미 끊긴 전화의 재통화뿐이다.
- 대처는 둘이다. "지금 통화량이 많으니 나중에 거세요"라고 바로 알리기(거절), 또는 급한 상담(분실 신고)만 받기(우선순위).

똑같은 구조다.\
실무 예: 스레드풀 앞의 무한 작업 큐, 컨슈머 랙이 계속 자라는 Kafka 파이프라인, 느린 구독자에게 버퍼를 무한히 쌓는 웹소켓 서버, 과부하 때 결제와 추천을 똑같이 대하는 API 서버.

- 기초(유계 큐의 네 가지 오버플로 정책, BLOCK·DROP_NEWEST·DROP_OLDEST·FAIL, wait/notify 구현의 함정)는 원본 [ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md) 「동작·원리」에 있다.
- 서버 설계 안에서의 자리(백프레셔 수단 표, 셰딩 기준 표)는 [systems/server-design/06-resilience.md](../../systems/server-design/06-resilience.md) §6에 있다.
- 이 노트는 **과부하가 왜 처리량 0으로 붕괴하는지**, **어디서 무엇을 버려야 하는지**를 실험으로 보인다.

## 동작·원리

### 1. 과부하의 시간축 — 처리량은 그대로인데 goodput이 0이 된다

```text
 요청 i의 도착 ──대기(큐)──> 처리 시작 ──10ms──> 응답      클라이언트 데드라인 300ms
 t=0s   대기   0ms  ✔ 쓸모 있음
 t=0.5s 대기 250ms  ✔ 아슬아슬
 t=1s   대기 500ms  ✘ 클라이언트는 이미 떠났다 → 서버는 계속 처리한다(헛일)
 t=3s   대기 1.5s   ✘
          처리량(throughput) ≈ 200/s 그대로 / goodput → 0
```

- *goodput(유효 처리량)*: **클라이언트가 아직 기다리고 있을 때** 끝난 요청의 수(단위 시간당). 처리량은 "끝낸 개수"라 헛일도 센다.
  - 아래 실험 출력의 괄호 속 %는 **제안한 요청 전체 대비** 제때 성공한 비율이다(예: 1028/1500 = 69%).
- SRE 책 22장은 이것을 "you don't get credit for late assignments with RPCs"라고 적는다. 데드라인이 지난 요청을 처리하는 데 자원을 쓰면 진전 없이 자원만 쓴다.
- 이 붕괴가 커리큘럼의 ⚠ "셰딩 없음 → 과부하 시 처리량 0으로 붕괴"다. 아래 실험의 FIFO_UNBOUNDED가 정확히 이 모양이다(초당 goodput `162 0 0 0 0 0 0 0`).

### 2. 리틀의 법칙 — 큐 길이를 정하는 것이 대기 시간을 정하는 것

```text
  L = λ × W
  L: 시스템(여기서는 큐) 안의 평균 개수
  λ: 들어오는 평균 비율(개/초)
  W: 한 개가 머무는 평균 시간(초)
```

- 안정 상태의 어떤 대기 시스템에도 성립한다(Little 1961). 분포 가정이 필요 없다.
- 처리율이 일정하면 "큐 한도 ÷ 처리율"이 가득 찬 큐의 대기 시간(큐를 비우는 데 걸리는 시간)이다. 그래서 큐 한도를 정하는 것이 대기 시간을 정하는 것이다.
  - 이것은 리틀의 법칙(평균끼리의 관계)이 아니라 처리율이 일정하다는 가정의 근사다. 처리 시간이 흔들리거나 작업자가 멈추면 유계 큐에서도 대기가 이보다 길어진다.
  - SRE 책 22장 예: 큐가 스레드 수의 10배이고 한 요청 처리에 100ms면, 큐가 가득 찼을 때 요청 하나는 1.1초가 걸리고 그 대부분이 큐 대기다.
  - 그래서 SRE 22장은 트래픽이 꾸준한 시스템이면 큐를 스레드풀 크기에 비해 작게(예: 50% 이하) 두라고 권한다. Gmail은 큐 없는 서버를 자주 쓴다고 적는다.
- 아래 실험의 모든 행에서 측정한 L과 λ×W가 같거나 0.1 차이였다(예: FIFO_BOUNDED `L=36.9 vs λ×W = 195.5/s × 0.189s = 36.9`, FIFO_BUDGET_DROP `76.4 vs 76.5`). 큐가 빈 상태로 시작해 빈 상태로 끝나는 구간이라 리틀의 법칙이 측정 구간 그대로 성립한다.

### 3. 두 가지 대응 — 역압과 셰딩

```text
 역압(backpressure): 소비자가 생산자를 늦춘다 — 아무것도 버리지 않는다
   생산자 ◀──"천천히"── 소비자          수단: 블로킹 put, Reactive Streams request(n),
                                              TCP 수신 창(rwnd)

 로드 셰딩(load shedding): 일부를 일부러 버려 나머지를 살린다
   요청 ──▶ [입장 판정] ──▶ [큐] ──▶ [꺼낼 때 판정] ──▶ 처리
              ✘ 503            ✘ 오래 머문 것 폐기
```

- *역압*: 처리하는 쪽이 감당할 수 있는 만큼만 받겠다는 신호를 위로 보내는 것. 신호가 맨 앞(사용자·외부 생산자)까지 전파돼야 의미가 있다. 중간에서 흡수하면 그 지점에 큐가 다시 생긴다.
- *로드 셰딩*: 과부하일 때 일부 요청을 빨리 거절하거나 버려서 나머지 요청이 제시간에 끝나게 하는 것. SRE 22장의 정의: 서버가 메모리 부족·헬스체크 실패·극단적 지연에 빠지지 않게 하면서 "할 수 있는 만큼 유용한 일을" 하는 것.
- 429/503 + `Retry-After`는 둘에 걸친다. 그 요청은 거절된다(셰딩). 헤더는 다음 시도를 언제 하라는 제안일 뿐이다(RFC 9110 §10.2.3). 클라이언트가 따를 때만 생산자를 늦추는 역압 신호가 된다.
- 역압을 걸 수 없는 생산자도 있다. 인터넷 사용자는 늦춰지지 않는다. 그래서 요청-응답 서버의 맨 앞은 결국 셰딩(거절)이다. 내부 파이프라인(큐·스트림)은 역압을 걸 수 있다.
- 신호의 계층: TCP 수신 창은 **전송 계층**의 역압이다([network/17-tcp-flow-control](../../network/17-tcp-flow-control/2-summary.md)). 애플리케이션이 큐를 무한히 두면 TCP 창은 0이 되지 않는다. 앱이 소켓에서 계속 읽어 자기 큐에 쌓아 두기 때문이다(메모리가 허락하는 동안).

### 4. 어디서 버리나 — 네 자리

```text
 ① 입장 거절      큐 길이·동시 실행 수가 한도면 즉시 503      [유계 큐, 세마포어]
 ② 체류 시간 폐기  꺼낼 때 "이미 오래 기다렸다"면 버린다        [CoDel 계열]
 ③ 순서 바꾸기    큐가 생기면 최신 것부터(LIFO)                [적응형 LIFO]
 ④ 예산 판정      남은 데드라인 < 예상 처리 시간이면 시작 안 함   [데드라인 전파]
```

- ② CoDel: 원래 네트워크 라우터의 큐 관리 알고리즘이다(RFC 8289).
  - *체류 시간(sojourn time)*: 항목이 큐에 머문 시간. CoDel은 큐 **길이**가 아니라 이것을 본다.
  - 규칙: 체류 시간이 TARGET(인터넷 기본 5ms)보다 INTERVAL(기본 100ms) 동안 계속 크면 버리기 시작한다. 버리는 동안 다음 버림 시각은 `t + INTERVAL / sqrt(count)`라 간격이 점점 줄어든다(값은 RFC 8289 §4.2·§4.3, 식은 §5.6 의사코드 `control_law`).
  - 짧은 버스트(100ms 안에 빠지는 큐)는 그대로 두고, 오래 서 있는 큐(standing queue)만 줄인다.
- ③ 적응형 LIFO: Facebook의 "Fail at Scale"(Maurer, ACM Queue 2015)이 소개한 서버 큐 관리다.
  - 평소에는 FIFO로 처리하다가 큐가 생기기 시작하면 LIFO로 바꾼다. 막 들어온 요청이 데드라인 안에 끝날 확률이 가장 높기 때문이다.
  - 같은 글의 CoDel 변형: 큐가 지난 N ms 동안 한 번도 비지 않았으면 큐 타임아웃을 M ms로, 아니면 N ms로 둔다. M=5ms, N=100ms가 넓은 경우에 잘 맞았다고 적는다(ACM 원문의 Internet Archive 사본으로 확인 — `onNewRequest` 의사코드와 "a value of 5 milliseconds for M and 100 ms for N tends to work well").
- ④ 예산 판정은 [05 데드라인 전파](../05-timeouts-and-deadline-propagation/2-summary.md)(원본 [ops-patterns/deadline-propagation](../../ops-patterns/deadline-propagation/2-summary.md))와 짝이다. SRE 22장도 단계마다 남은 데드라인을 확인하라고 적는다.

### 5. 무엇을 먼저 버리나 — 우선순위 셰딩

```text
 큐 사용률   0% ──────── 50% ──────────── 100%
 SHEDDABLE   받음      │ 거절
 CRITICAL    받음                         │ 거절
```

- SRE 21장의 요청 중요도는 네 단계다: `CRITICAL_PLUS`, `CRITICAL`(프로덕션 요청의 기본), `SHEDDABLE_PLUS`(배치의 기본), `SHEDDABLE`.
  - 과부하된 태스크는 **낮은 중요도부터 먼저** 거절한다. 중요도는 RPC로 하위 호출에 자동 전파된다.
  - 중요도는 지연 요구와 **직교**한다. 검색어 자동완성은 버려도 되지만(셰딩 가능) 지연 요구는 빡빡하다.
- 아래 실험의 PRIORITY_SHED: 같은 과부하에서 중요 요청 `302/302`가 성공했다(4회 실행 모두). 우선순위 없는 FIFO_BOUNDED에서는 `206/302`였다(실행마다 201~217).

### 6. 거절도 공짜가 아니다 — 클라이언트 측 적응형 스로틀링

- 거절 응답을 만드는 비용이 처리 비용과 비슷하면, 백엔드는 거절만 하다가 과부하된다(SRE 21장).
- SRE 21장의 적응형 스로틀링: 클라이언트가 지난 2분의 `requests`(보낸 시도)와 `accepts`(백엔드가 받아 준 수)를 센다.

```text
  로컬 거절 확률 = max(0, (requests − K × accepts) / (requests + 1))      K 기본 2 권장
```

- `requests`가 `K × accepts`를 넘기 시작하면 초과분만큼을 **네트워크에 보내지도 않고** 로컬에서 실패시킨다.
- K를 줄이면 공격적(1.1이면 받아 준 10개당 백엔드 거절 1개), 키우면 느슨하다. SRE는 2를 선호한다고 적는다. 백엔드 상태 변화가 클라이언트에 더 빨리 전해지기 때문이다.

### 실험: 같은 과부하, 큐 정책 6가지

- 서버: 작업자 스레드 2개, 요청 하나 10ms(`Thread.sleep` — 하류 I/O 대기 흉내) → 용량 약 200/s.
- 부하: **열린 부하** 300/s로 5초(요청 i의 도착 시각을 `t0 + i/300`으로 고정 — 서버가 느려도 도착을 늦추지 않는다). 지연은 이 예정 도착 시각부터 잰다(coordinated omission 회피).
  - *열린 부하(open loop)*: 응답을 기다리지 않고 정해진 비율로 요청을 보내는 부하. 사용자가 많은 실제 서비스가 이쪽에 가깝다.
- 클라이언트 데드라인 300ms. 20%는 중요 요청.
- 정책: FIFO 무한 / FIFO 유계 40 / 무한 + 꺼낼 때 데드라인 지난 것 폐기 / 무한 + 꺼낼 때 남은 예산 < 처리 시간이면 폐기 / 적응형 LIFO + CoDel 변형(M=5ms, N=100ms) / 우선순위 셰딩(유계 40, 일반 요청은 20부터 거절).

핵심 코드(전체: 실험 목록의 `Backpressure.java`):

```java
// 입장 판정 — false면 즉시 503
switch (mode) {
    case FIFO_BOUNDED  -> { if (n >= 40) return false; }
    case PRIORITY_SHED -> { if (n >= 40 || (!r.critical() && n >= 20)) return false; }
    default -> {}
}
// 꺼낼 때 판정
boolean late     = now - r.arrival() > DEADLINE_NS;                         // 이미 늦었다
boolean noBudget = now - r.arrival() + SERVICE_MS * 1_000_000L > DEADLINE_NS; // 해 봐야 늦는다
if ((mode == FIFO_DEADLINE_DROP && late) || (mode == FIFO_BUDGET_DROP && noBudget) || (now - enq > timeout)) { expired++; continue; }
```

(실험, JDK 21.0.12 eclipse-temurin, 컨테이너 `--cpus=2`, 2026-10-01 — 지연·개수는 실행마다 조금 다르다. 집필 2회·점검 2회, 모두 4회 실행해 goodput 차이는 정책마다 8건 이내였다)

```text
작업자 2 · 처리 10ms → 용량 약 200/s, 도착 300/s x 5s, 데드라인 300ms, cores=2
== FIFO_UNBOUNDED
  제안 1500 · 입장거절 0 · 큐에서폐기 0 · 처리 1500 · 데드라인내 성공(goodput) 162 (11%)
  처리된 요청 지연 p50 1319ms · p99 2594ms · max 2618ms · 최대 큐 516
  리틀: 평균 큐 길이 L=256.3  vs  λ×W = 195.8/s × 1.309s = 256.3   (전체 7.7s)
  중요 요청 성공 32/302 · 일반 요청 성공 130/1198
  초당 goodput: 162 0 0 0 0 0 0 0
== FIFO_BOUNDED
  제안 1500 · 입장거절 472 · 큐에서폐기 0 · 처리 1028 · 데드라인내 성공(goodput) 1028 (69%)
  처리된 요청 지연 p50 210ms · p99 212ms · max 212ms · 최대 큐 40
  리틀: 평균 큐 길이 L=36.9  vs  λ×W = 195.5/s × 0.189s = 36.9   (전체 5.3s)
  중요 요청 성공 206/302 · 일반 요청 성공 822/1198
  초당 goodput: 196 198 197 197 198 42
== FIFO_DEADLINE_DROP
  제안 1500 · 입장거절 0 · 큐에서폐기 455 · 처리 1045 · 데드라인내 성공(goodput) 168 (11%)
  처리된 요청 지연 p50 308ms · p99 310ms · max 310ms · 최대 큐 92
  리틀: 평균 큐 길이 L=78.9  vs  λ×W = 280.1/s × 0.282s = 78.9   (전체 5.4s)
  중요 요청 성공 37/302 · 일반 요청 성공 131/1198
  초당 goodput: 168 0 0 0 0 0
== FIFO_BUDGET_DROP
  제안 1500 · 입장거절 0 · 큐에서폐기 456 · 처리 1044 · 데드라인내 성공(goodput) 1030 (69%)
  처리된 요청 지연 p50 296ms · p99 300ms · max 300ms · 최대 큐 89
  리틀: 평균 큐 길이 L=76.4  vs  λ×W = 280.8/s × 0.272s = 76.5   (전체 5.3s)
  중요 요청 성공 210/302 · 일반 요청 성공 820/1198
  초당 goodput: 196 191 196 195 195 57
== ADAPTIVE_LIFO_CODEL
  제안 1500 · 입장거절 0 · 큐에서폐기 516 · 처리 984 · 데드라인내 성공(goodput) 984 (66%)
  처리된 요청 지연 p50 12ms · p99 105ms · max 110ms · 최대 큐 296
  리틀: 평균 큐 길이 L=104.9  vs  λ×W = 296.5/s × 0.354s = 104.9   (전체 5.1s)
  중요 요청 성공 190/302 · 일반 요청 성공 794/1198
  초당 goodput: 193 197 198 197 197 2
== PRIORITY_SHED
  제안 1500 · 입장거절 494 · 큐에서폐기 0 · 처리 1006 · 데드라인내 성공(goodput) 1006 (67%)
  처리된 요청 지연 p50 109ms · p99 116ms · max 117ms · 최대 큐 22
  리틀: 평균 큐 길이 L=18.8  vs  λ×W = 195.3/s × 0.097s = 18.8   (전체 5.2s)
  중요 요청 성공 302/302 · 일반 요청 성공 704/1198
  초당 goodput: 196 197 197 198 197 21
```

- 관찰 1 — 무한 FIFO는 1500개를 **전부 처리했다**(처리량 정상). 그런데 goodput은 첫 1초의 162개뿐이고 그 뒤 0이다. 에러 응답은 하나도 없었다.
- 관찰 2 — 유계 큐(40)는 472개를 즉시 거절하고, 받은 1028개를 **전부** 데드라인 안에 끝냈다. 버린 쪽이 오히려 성공 수가 6배다.
- 관찰 3 — "데드라인이 **지난** 것만 버리기"는 무한 FIFO와 거의 같았다(goodput 168). 큐는 데드라인 경계에 서 있게 되고, 꺼낸 요청은 처리 10ms를 더하면 늦는다. "**남은 예산이 처리 시간보다 짧으면** 버리기"로 바꾸자 1030으로 올랐다. 판정 기준은 "늦었나"가 아니라 "제때 끝낼 수 있나"다.
- 관찰 4 — 적응형 LIFO + CoDel 변형은 처리한 요청의 p50이 12ms였다. 대신 최대 큐 길이는 265~356이었다(4회 실행, 곧 버릴 항목이 쌓여 있다). 큐 길이만 보는 경보는 이 정책에서 오탐을 낸다.
- 관찰 5 — 모든 정책에서 goodput 상한은 처리 용량(약 200/s)이다. 셰딩은 용량을 늘리지 않는다. 용량이 **헛일로 새는 것**을 막을 뿐이다.

### 실험: 무한 큐 → OOM

- 항목 4KB, 생산 약 5000/s, 소비 약 500/s(`sleep(2)`), 힙 상한 `-Xmx64m`.

(실험, JDK 21.0.12, `--cpus=2`, 2026-10-01)

```text
## unbounded
t= 1.1s 큐   4463 · 거절      0 · 힙 사용  31MB / 최대 64MB
t= 2.3s 큐   8920 · 거절      0 · 힙 사용  44MB / 최대 64MB
t= 3.5s 큐  13383 · 거절      0 · 힙 사용  63MB / 최대 64MB

Exception: java.lang.OutOfMemoryError thrown from the UncaughtExceptionHandler in thread "main"
## bounded
t= 1.1s 큐    999 · 거절   3460 · 힙 사용  31MB / 최대 64MB
t= 2.3s 큐    999 · 거절   7909 · 힙 사용  29MB / 최대 64MB
...
t=12.4s 큐    999 · 거절  48148 · 힙 사용  36MB / 최대 64MB
12초 경과 — 종료
```

- 관찰: 무한 큐는 3.5초 동안 거절 0으로 자라다 OOM으로 죽었다. 마지막 메시지조차 메모리가 없어 정상 출력되지 못했다(`thrown from the UncaughtExceptionHandler`). 유계 큐(1000)는 같은 부하에서 12초 동안 힙이 18~48MB 사이에서 머물렀다(중략 줄은 같은 모양의 반복).

## 쓰이는 자료구조·알고리즘

- **유계 큐(원형 배열)** — 정원이 있는 FIFO. Java의 `ArrayBlockingQueue`. 원리는 [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md).
- **덱(deque)** — 적응형 LIFO는 같은 덱의 앞(FIFO)과 뒤(LIFO)에서 꺼낸다.
- **CoDel 상태 기계** — 상태 둘(버리지 않음 / 버리는 중). 구간(INTERVAL) 동안의 **최소** 체류 시간이 TARGET을 넘으면 버리는 상태로 간다. 다음 버림 시각 = `t + INTERVAL / sqrt(count)`(RFC 8289 §5 의사코드). 최소값을 보는 이유는 짧은 버스트에 흔들리지 않기 위해서다.
- **다중 우선순위 큐** — 중요도별 큐 또는 중요도별 입장 한도. 힙 기반 우선순위 큐는 [data-structure/07-heap](../../data-structure/07-heap/2-summary.md). 셰딩에서는 "꺼내는 순서"보다 "어느 등급부터 거절하나"가 핵심이라 등급별 임계치로 충분한 경우가 많다.
- **지수 감쇠 평균(EWMA)** — SRE 21장은 실행 중·실행 대기 스레드 수를 지수 감쇠로 평활해, 프로세서 수를 넘으면 거절을 시작한다. 짧은 팬아웃 스파이크는 평활이 삼킨다.
- **슬라이딩 윈도 카운터** — 적응형 스로틀링의 2분 `requests`·`accepts`. 토큰 버킷·창 카운터는 [11-rate-limiter](../11-rate-limiter/2-summary.md).
- **세마포어** — 동시 실행 수 한도(큐 없는 입장 거절). [os/18-semaphores](../../os/18-semaphores/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. **처리 용량을 잰다** — 요청 하나 처리 시간 × 동시 처리 수. 부하 테스트로 "어느 부하에서 무너지나"를 먼저 본다(SRE 22장: 용량 한계와 과부하 실패 모드를 테스트하라).
2. **허용 대기 시간을 정한다** — 호출자 데드라인에서 처리 시간을 뺀 값.
3. **큐 한도 = 허용 대기 × 처리율**(리틀의 법칙). 꾸준한 트래픽이면 작게, 버스트가 크면 버스트 크기에 맞춘다.
4. **입장에서 거절한다** — 한도를 넘으면 503(또는 429)을 **빨리** 돌려준다. 거절은 처리보다 훨씬 싸야 한다.
5. **꺼낼 때 예산을 본다** — 남은 데드라인이 예상 처리 시간보다 짧으면 시작하지 않는다.
6. **중요도를 붙인다** — 결제·로그인 > 조회 > 추천·프리페치. 하위 호출에 전파한다.
7. **클라이언트를 맞춘다** — 거절 응답에 재시도 백오프·재시도 예산([06](../06-retry-backoff-jitter/2-summary.md)), 거절률이 높으면 로컬 스로틀링.
8. **지표를 단다** — 큐 길이만이 아니라 **큐 체류 시간**(가장 오래된 항목의 나이), 거절 수, goodput.

### 2. 유계 풀 + 빠른 거절 (Java, JDK 21)

```java
// Executors.newFixedThreadPool(n)은 무한 LinkedBlockingQueue를 쓴다(JDK 문서: "shared unbounded queue").
// 과부하 서버라면 큐를 직접 고른다.
ThreadPoolExecutor pool = new ThreadPoolExecutor(
        16, 16, 0, TimeUnit.MILLISECONDS,
        new ArrayBlockingQueue<>(8),                 // 큐 = 스레드의 50% (SRE 22장 권고 범위)
        new ThreadPoolExecutor.AbortPolicy());       // 꽉 차면 RejectedExecutionException

void handle(Request req, Response res) {
    try {
        pool.execute(() -> serve(req, res));
    } catch (RejectedExecutionException e) {
        metrics.counter("shed_total", "reason", "queue_full").increment();
        res.status(503).header("Retry-After", "1").end(); // 거절은 싸게, 빨리
    }
}
```

- `CallerRunsPolicy`는 거절 대신 **제출한 스레드가 직접 실행**한다(실행기가 이미 종료됐으면 작업을 조용히 버린다 — JDK 21 API 문서). 제출자가 느려지므로 역압처럼 동작한다. 단 제출자가 이벤트 루프·수락 스레드라면 그 스레드가 막혀 서버 전체가 멈춘다.

### 3. 꺼낼 때 예산 판정 + 중요도

```java
record Task(Runnable work, long deadlineNanos, Criticality crit) {}

void workerLoop(BlockingQueue<Task> q, long expectedServiceNanos) throws InterruptedException {
    while (true) {
        Task t = q.take();
        long remaining = t.deadlineNanos() - System.nanoTime();
        if (remaining < expectedServiceNanos) {           // 실험의 FIFO_BUDGET_DROP
            metrics.counter("shed_total", "reason", "no_budget").increment();
            continue;                                      // 남은 시간으로는 제때 못 끝낸다 → 실행 안 함
        }
        t.work().run();
    }
}

boolean admit(Task t, int queued, int capacity) {          // 실험의 PRIORITY_SHED
    return switch (t.crit()) {
        case CRITICAL -> queued < capacity;
        case SHEDDABLE -> queued < capacity / 2;
    };
}
```

### 4. 진단

```bash
# 큐 체류 시간·거절률(PromQL 개념 예 — 지표 이름은 예시)
histogram_quantile(0.99, sum by (le) (rate(queue_wait_seconds_bucket[5m])))
sum(rate(shed_total[5m])) by (reason) / sum(rate(requests_total[5m]))
# goodput 비율: 받은 요청 중 데드라인 안에 끝난 응답의 비율
sum(rate(requests_completed_within_deadline_total[5m])) / sum(rate(requests_total[5m]))

# 커널 수락 큐가 차는지(LISTEN 소켓의 Recv-Q = 수락 대기 연결 수, Send-Q = backlog 한도)
ss -lnt 'sport = :8080'
# JVM 스레드가 어디서 기다리나
jcmd <pid> Thread.print | grep -A3 'pool-'
```

- 수락 큐(backlog)는 애플리케이션 큐 앞에 있는 커널 큐다. [network/15-tcp-handshake-and-backlog](../../network/15-tcp-handshake-and-backlog/2-summary.md).

## 장애 시나리오와 대처

### 1. 무한 큐 → 지연 폭증 후 OOM (⚠)

- 현상: 트래픽이 용량을 조금 넘은 뒤 몇 분 동안 에러 없이 응답만 느려지다가, 인스턴스가 하나씩 재시작된다.
- 보이는 형태: 에러율 0%인데 p99가 계단처럼 오른다. 힙 사용량이 톱니 없이 우상향하고 GC 시간이 늘다 `java.lang.OutOfMemoryError: Java heap space`. 위 OOM 실험처럼 마지막 로그조차 깨질 수 있다.
- 원인: `Executors.newFixedThreadPool`·`new LinkedBlockingQueue<>()` 같은 무한 큐. 넘치는 요청을 거절하지 않고 메모리에 쌓았다.
- 대처: 큐에 한도를 두고 넘치면 503. 한도는 리틀의 법칙으로 "허용 대기 × 처리율". 큐 체류 시간 지표와 경보를 단다.

### 2. 셰딩 없음 → 처리량 0으로 붕괴 (⚠)

- 현상: 과부하 동안 서버 CPU는 바쁜데 성공 응답이 거의 없다. 부하가 조금만 줄어도 회복되지 않는다.
- 보이는 형태: 서버 쪽 "처리 완료" 수는 정상, 클라이언트 쪽은 전부 타임아웃. 위 실험 FIFO_UNBOUNDED의 `초당 goodput: 162 0 0 0 0 0 0 0`. 클라이언트 재시도로 요청 수가 더 늘어난다.
- 원인: 모든 요청을 받아 FIFO로 처리하니 큐 대기가 데드라인을 넘었다. 헛일이 용량을 다 먹는다. SRE 22장: 11,000 QPS에서 무너진 서비스는 9,000 QPS로 줄여도 회복되지 않을 수 있다(살아 있는 서버 비율이 줄어 있으므로).
- 대처: 입장 거절(유계 큐), 예산 판정, 적응형 LIFO·CoDel. 회복할 때는 부하를 용량 **훨씬 아래**로 일시적으로 줄인다(트래픽 차단 후 점진 복귀).

### 3. "데드라인 지난 것만 버리기"를 넣었는데 효과가 없다

- 현상: 큐에서 늦은 요청을 버리도록 고쳤는데도 타임아웃률이 거의 그대로다.
- 보이는 형태: 폐기 카운터는 오르는데 성공 응답 지연이 데드라인 바로 위에 몰려 있다(실험 FIFO_DEADLINE_DROP: p50 308ms, 데드라인 300ms).
- 원인: 큐 대기가 데드라인 경계에 서 있다. 꺼낼 때는 아직 안 늦었지만 처리 시간을 더하면 늦는다.
- 대처: "남은 예산 < 예상 처리 시간"이면 버린다(실험 FIFO_BUDGET_DROP: goodput 168 → 1030). 예상 처리 시간은 p50~p90 같은 분위수로 잡는다. 더 근본적으로는 큐 자체를 짧게 둔다.

### 4. 셰딩이 헬스체크까지 버려 연쇄 장애

- 현상: 한 인스턴스가 과부하로 셰딩을 시작하자 로드 밸런서가 그 인스턴스를 빼고, 남은 인스턴스가 차례로 과부하된다.
- 보이는 형태: 헬스체크 실패 → 대상 제외 이벤트가 인스턴스마다 연달아 찍힌다. 살아 있는 대상 수가 줄수록 각 대상의 QPS가 오른다.
- 원인: 헬스체크 요청도 같은 큐·같은 입장 판정을 탔다. SRE 22장: 헬스체크에 실패하는 서버는 크래시와 비슷한 효과를 내고, 남은 서버 부하를 늘려 눈덩이가 된다.
- 대처: 헬스체크·관리 요청은 별도 경로(별도 포트·스레드, 최고 중요도)로 처리한다. "과부하"와 "죽음"을 구분해 보고한다(준비 상태 해제는 신중하게).

### 5. 거절 응답이 재시도 폭풍을 부른다

- 현상: 503을 늘렸더니 요청 수가 오히려 2~3배가 됐다.
- 보이는 형태: 같은 요청 ID가 짧은 간격으로 반복된다. 거절 처리에 CPU가 쓰인다.
- 원인: 클라이언트가 거절을 즉시 재시도한다. SRE 21장 예: 재시도로 요청이 약 3X까지 늘 수 있고, 클라이언트당 재시도 예산 10%를 걸면 1.1X로 줄어든다.
- 대처: 재시도 예산·지수 백오프·지터([06](../06-retry-backoff-jitter/2-summary.md)), 클라이언트 측 적응형 스로틀링(`max(0, (requests − K·accepts)/(requests+1))`), `Retry-After` 존중.

## 핵심 문장

- 과부하에서 처리량은 유지되는데 goodput이 0이 될 수 있다. 실험에서 무한 FIFO는 1500개를 전부 처리했지만 데드라인 안의 것은 첫 1초의 162개뿐이었다.
- 큐 한도를 정하는 것이 대기 시간을 정하는 것이다(처리율이 일정할 때 가득 찬 큐의 대기 ≈ 한도 ÷ 처리율). 평균끼리는 리틀의 법칙 L = λW가 묶는다. 실험의 모든 정책에서 측정한 L과 λ×W가 거의 같았다(차이 0.1 이하).
- 일부를 빨리 버리면 나머지가 산다. 유계 큐는 472개를 거절하고 받은 1028개를 모두 제때 끝냈다.
- 꺼낼 때의 판정 기준은 "이미 늦었나"가 아니라 "제때 끝낼 수 있나"다.
- 무엇을 먼저 버릴지는 중요도가 정한다. 중요도는 요청 경로를 따라 전파해야 깊은 곳의 셰딩도 같은 판단을 한다.
- 셰딩은 용량을 늘리지 않는다. 용량이 헛일로 새는 것을 막을 뿐이다.

## 관련 주제·근거

- 선행
  - [11-rate-limiter](../11-rate-limiter/2-summary.md) — 들어오는 속도 막기(토큰 버킷). 셰딩은 "지금 내 상태"로, 레이트 리미터는 "약속한 몫"으로 판단한다.
  - math/10-queueing-and-littles-law — 미작성([../../math/README.md](../../math/README.md) 영역 표). 원고: [systems/server-design/01-scaling-principles.md](../../systems/server-design/01-scaling-principles.md).
  - 원본 [ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md) — 오버플로 정책 네 가지와 구현 함정. 원본의 "정원 50과 100의 최대 대기가 같다" 측정은 원본 시뮬레이션이 소비를 주기 단위로 돌린 데서 나온 결과다. 큐가 늘 차 있는 연속 처리 서버라면 리틀의 법칙대로 대기 ≈ 정원 / 처리율이다(이 노트 실험의 유계 40: 40 / 195.5/s ≈ 205ms, 측정 p99 212ms에는 처리 10ms가 더해져 있다).
  - 원본 [systems/server-design/06-resilience.md](../../systems/server-design/06-resilience.md) §6
- 후속·연결
  - [05-timeouts-and-deadline-propagation](../05-timeouts-and-deadline-propagation/2-summary.md) — 남은 예산 판정의 짝. 원본 [ops-patterns/deadline-propagation](../../ops-patterns/deadline-propagation/2-summary.md)
  - [06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md) — 거절 뒤 재시도
  - [28-bulkhead](../28-bulkhead/2-summary.md) — 자원 나누기
  - [41-autoscaling](../41-autoscaling/2-summary.md) · [49-steady-state-fail-fast-and-supervision](../49-steady-state-fail-fast-and-supervision/2-summary.md)
  - [distributed/17-queues-logs-and-delivery-semantics](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md) · [distributed/18-consumer-failure-handling](../../distributed/18-consumer-failure-handling/2-summary.md) — 메시지 큐의 컨슈머 랙
  - [network/17-tcp-flow-control](../../network/17-tcp-flow-control/2-summary.md) · [network/40-chunked-and-streaming-responses](../../network/40-chunked-and-streaming-responses/2-summary.md) — 전송 계층·스트리밍의 역압
  - [database/21-connection-pooling](../../database/21-connection-pooling/2-summary.md) — 풀 대기 큐
- 근거
  - Google SRE 책 21장 "Handling Overload"(고객별 한도, 클라이언트 측 적응형 스로틀링 공식, 중요도 4단계, 실행자 부하 평균) <https://sre.google/sre-book/handling-overload/>
  - Google SRE 책 22장 "Addressing Cascading Failures"(Queue Management, Load Shedding and Graceful Degradation, 데드라인 전파, 11,000→9,000 QPS 예) <https://sre.google/sre-book/addressing-cascading-failures/>
  - RFC 8289 "Controlled Delay Active Queue Management"(TARGET 5ms, INTERVAL 100ms, `INTERVAL / sqrt(count)`) <https://www.rfc-editor.org/rfc/rfc8289>
  - Maurer, "Fail at Scale", ACM Queue 13(8), 2015 — 적응형 LIFO, CoDel 변형(M=5ms, N=100ms) <https://queue.acm.org/detail.cfm?id=2839461>(직접 접속이 막혀 Internet Archive 사본으로 확인)
  - Little, J. D. C., "A Proof for the Queuing Formula: L = λW", Operations Research, 1961
  - JDK 21 API — `Executors.newFixedThreadPool`(무한 큐), `ThreadPoolExecutor.AbortPolicy`·`CallerRunsPolicy`
- 실험 목록
  - E1 과부하 큐 정책 6가지(goodput·지연·리틀의 법칙·중요도별 성공) — `Backpressure.java`, JDK 21 temurin, `--cpus=2`, 집필 2회 + 점검 2회 실행
  - E2 무한 큐 vs 유계 큐 OOM — `OomQueue.java`, `-Xmx64m`, JDK 21 temurin, `--cpus=2`
