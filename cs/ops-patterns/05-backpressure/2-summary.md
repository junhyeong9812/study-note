# ops-patterns/05-backpressure — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 서머리(Claude 작성) — 원본 myway 코드·문서 기준.
> 2026-09-28: 통일 골격 양식으로 재배치 + 새 절 추가(Claude 작성 — 기존 본문은 이동만).

## 해결하는 문제

만드는 쪽이 처리하는 쪽보다 빠르면 그 차이는 어딘가에 쌓인다.\
쌓이는 곳(큐)에 상한이 없으면 아무 에러 없이 죽는다.

```text
생산 1000/s ──> [ 큐 ......................... ] ──> 소비 100/s
                     매초 900개씩 자란다
                     10초: 9,000개 / 최대 대기 10초   에러 0 · 버림 0 · 성공률 100%
                     30초: 27,000개 / 최대 대기 28초  지표는 초록, 사용자는 이미 떠남
```

쉬운 예: 식당의 웨이팅 마감 — 주방이 소화 못 하는 줄을 무한히 받으면 3시간 기다린 손님은 이미 딴 데 갔고, 주방은 아무도 안 먹을 음식을 만든다.\
똑같은 구조다: 소비자가 생산자에게 **"천천히"**라고 말하는 통로가 있어야 하고, 큐가 찼을 때 무엇을 잃을지를 미리 정해야 한다.\
실무 예: 인자 없는 `new LinkedBlockingQueue<>()`(정원 `Integer.MAX_VALUE`) 위에 얹은 작업 큐, 느린 구독자에게 무한히 버퍼링하는 웹소켓 서버, 컨슈머 랙이 자라기만 하는 Kafka 파이프라인.

  - *컨슈머 랙(consumer lag)*: 브로커에 쌓인 메시지 중 소비자가 아직 못 읽은 개수.

### 한눈에 — 쉽게 말하면
**백프레셔 = 식당의 웨이팅 마감.**\
주방이 소화 못 하는 줄을 무한히 받으면, 3시간 기다린 손님은 이미 딴 데 갔다.

> **백프레셔(backpressure)** — 소비자가 생산자에게 "천천히"라고 말하는 것.\
> 예: 밀려드는 압력을 거슬러 올라가는 신호다.

- 생산자가 초당 1000개를 넣고 소비자가 초당 100개를 처리한다.\
  큐에 제한이 없으면?

> **생산자(producer) / 소비자(consumer)** — 큐에 넣는 쪽 / 큐에서 빼서 처리하는 쪽.\
> 예: 생산 1000/s · 소비 100/s 면 매초 900개씩 밀린다.

- 서버의 요청 큐도 똑같은 구조다 — 큐는 자라기만 하고, **버린 것 0, 에러 0, 성공률 100%** — **지표가 전부 초록인 채로 죽는다.**\
  이 상자가 막으려는 것이 그 모양이다.
- 그래서 소비자가 생산자에게 **"천천히"라고 말한다.**\
  03은 이미 들어온 것을 나눴고, 04는 들어오는 속도를 막았고, 05는 못 받겠다고 말한다 — 셋이 같은 문제의 세 층이다.
- 핵심 선택: 큐가 **찼을 때 무엇을 할 것인가.**\
  재우기(BLOCK) / 새것 버리기(DROP_NEWEST) / 옛것 버리기(DROP_OLDEST) / 던지기(FAIL) — 넷 다 정답이고, 무엇을 잃을지가 다를 뿐이다.

> **오버플로 정책(overflow policy)** — 큐가 찼을 때의 행동 — BLOCK(재움) / DROP_NEWEST(새것 버림) / DROP_OLDEST(옛것 버림) / FAIL(던짐).\
> 예: 넷 다 정답이고, 무엇을 잃을지가 다를 뿐이다.

> **유한 큐(bounded) / 무한 큐(unbounded)** — 정원이 있는 큐 / 없는 큐.\
> 예: 무한 큐는 장애를 타임아웃(시간 손실)으로 바꿀 뿐이다.

```text
무한 큐:  경과 10초 → 큐 9,000 → 최대 대기 10초
          경과 30초 → 큐 27,000 → 최대 대기 28초   ← 에러 하나 없이 죽는 중
정원 100: 큐가 100에서 멈춤 → 최대 대기 1초, 대신 9,000개를 잃음(버리거나 거절)
```

실무 예: `new LinkedBlockingQueue<>()`(인자 없으면 정원이 Integer.MAX_VALUE — 위 사고 그대로), Kafka 컨슈머 랙, Reactive Streams의 request(n), TCP 흐름 제어.

## 동작·원리

### 전체 흐름
```text
Channel<T> 계약: offer(막히거나·버리거나·던진다) / poll / size / accepted / dropped
   │
   ├─ UnboundedChannel  기준선 — 제한 없음. 사고가 어떻게 자라는지 보여준다
   │                    (요점: 항목마다 들어온 시각을 담는다 — 대기 시간을 재려고)
   └─ BoundedChannel    정원 + OverflowPolicy 넷 + wait/notify 가 본체
```

### 설계 — 큐 길이를 고르는 것 = 대기 시간을 고르는 것
**리틀의 법칙**: `대기 시간 = 큐 길이 / 처리율`.

  > **리틀의 법칙(Little's law)** — 줄의 길이와 빠져나가는 속도만 알면 기다리는 시간이 정해진다는 대기 이론의 기본 법칙.\
  > 예: 큐에 9,000개가 있고 초당 100개를 처리하면 지금 들어간 항목은 90초 뒤에 처리된다.

처리율은 소비자가 정한다.\
우리가 고를 수 있는 것은 큐 길이뿐이고, 그러므로 **큐 길이를 고르는 것이 곧 대기 시간을 고르는 것**이다.\
측정(생산 1000/s, 소비 100/s, 10초):

> **처리율(throughput)** — 소비자가 단위 시간에 빼는 개수.\
> 예: 큐로는 못 바꾸는, 소비자가 정하는 값이다.

> **정원(capacity)** — 큐가 담을 수 있는 최대 개수.\
> 예: 이것을 고르는 것이 곧 대기 시간을 고르는 것이다.

```text
정원      50      100     200      400      800
버림    9,500   9,000   8,900    8,700    8,300
최대대기 1,000ms 1,000ms 2,000ms  4,000ms  8,000ms
         └──같다──┘   ← 정원에 비례하지 않는다!
```

- 50과 100의 대기가 같다 — 대기는 정원이 아니라 **소비자가 한 주기에 못 빼고 남긴 양**에 비례한다.\
  그 양이 0이면 정원을 키워도 안 자란다.\
  (원본 저자가 "지연이 정원에 비례한다"고 쓰려다 이 측정에 반박당해 주장을 고쳤다.)
- **큐를 크게 잡는 것은 안전이 아니라 지연을 사는 것이다.**\
  10초 기다려 처리한 요청은 이미 아무도 안 받는다 — 일은 했는데 쓸모가 없다.

### 동작 — 네 가지 OverflowPolicy (찼을 때 무엇을 할 것인가)
**언제 쓰나**: 정원을 두는 순간 반드시 무언가를 잃는다 — 무엇을 잃을지는 **데이터가 정한다.**

전 상태 — 정원 4가 꽉 찬 큐에 새 항목 E가 도착:

```text
        큐(정원 4): [ A | B | C | D ] ← E 도착
```

단계 (정책별 한 문장):

```text
BLOCK       : E의 생산자를 재운다(wait) → 소비자가 빼면 깨어나 넣는다. 아무것도 안 잃고 생산자가 느려진다
DROP_NEWEST : E를 안 넣는다(offer=false). [A|B|C|D] 그대로 — 이미 받은 것을 지킨다
DROP_OLDEST : A를 버리고 E를 넣는다(offer=true!). [B|C|D|E] — 최신을 지킨다
FAIL        : ChannelFullException 을 던진다 — 생산자가 알고, 재시도할지 포기할지 고를 수 있다
```

후 상태 — 같은 부하(정원 100, 생산 1000/s, 소비 100/s, 10초)의 측정:

```text
            받음      버림     거절     최대 대기
DROP_NEWEST  1,000    9,000       0     1,000ms
DROP_OLDEST 10,000    9,000       0     1,000ms
FAIL         1,000        0   9,000     1,000ms
무한 큐      10,000        0       0    10,000ms   ← 시간을 잃는 중
```

**잃는 양은 같다. 잃는 것이 무엇이냐가 다르다.**\
무한 큐만 안 잃는 것처럼 보이는데 시간을 잃고 있다.

- DROP_NEWEST: 순서가 중요한 데이터(로그, 이벤트 소싱)에 맞다 — 대신 제일 최신 정보를 잃는다.
- DROP_OLDEST: 최신만 의미 있는 데이터(센서 값, 시세, 대시보드)에 맞다 — 오래된 값은 아무도 안 본다.
- FAIL: 03번 `BulkheadFullException`과 같은 모양 — 선택권이 값이다.\
  다만 알면 재시도하게 되고 재시도는 부하를 늘린다(01번).\
  **고를 수 있게 하는 것과 잘 고르는 것은 다르다.**

> **ChannelFullException** — "큐가 찼다"를 생산자에게 알리는 예외.\
> 예: 버림과 달리 생산자에게 선택권을 준다.

- BLOCK이 진짜 백프레셔다 — 느려짐이 생산자의 생산자에게 **전파**되어야 의미가 있다.

### 동작 — BoundedChannel 구현의 함정들
**언제 쓰나**: 위 정책을 실제 스레드 사이에서 구현할 때.\
wait/notify가 본체다.

```text
생산자 offer ──┐                          ┌── 소비자 poll
               v                          v
         [synchronized 큐]  ── poll 이 notifyAll() ──> 자던 BLOCK 생산자가 깨어남
```

- **`wait`는 `if`가 아니라 `while`이다** — 깨어났을 때 자리가 있다는 보장이 없다(다른 생산자가 먼저 가져갔거나, 이유 없이 깨어났거나(spurious wakeup)).

> **wait / notifyAll** — 자바에서 스레드를 재우고 깨우는 기본 도구.\
> 예: wait 는 잠금을 놓고 자므로 소비자가 그동안 poll 할 수 있다.

> **가짜 깨어남(spurious wakeup)** — 아무 이유 없이 wait 에서 깨어나는 현상.\
> 예: 그래서 wait 는 if 가 아니라 while 로 감싼다.

- **`poll`이 `notifyAll`을 빼먹으면 BLOCK 생산자가 영원히 안 깨어난다** — 그런데 **네 정책 중 셋은 그대로 통과한다.**\
  나머지 셋에서는 아무 일도 안 일어나기 때문에 테스트 세 개가 초록이다.
- **DROP_OLDEST의 offer는 true를 반환한다** — 새 항목은 들어갔으니까.\
  예외도 없고 반환값도 정상인데 **다른 항목이 사라졌다.**\
  dropped 카운터를 같이 봐야 안다.\
  이 상자에서 제일 조용한 사고다.
- **항목마다 자기 시각을 들고 있어야 한다**(`Stamped(item, enqueuedAt)`) — 큐 전체에 시각 하나만 두면 먼저 온 것과 나중 온 것의 대기가 같은 값으로 나온다.

> **타임스탬프(enqueuedAt)** — 항목마다 들고 있는 "들어온 시각".\
> 예: 대기 시간 측정의 근거 — 큐 전체에 하나만 두면 틀린다.

- 담는 그릇(ArrayDeque)은 직접 만들지 않는다 — 주제는 큐가 아니라 **찼을 때 무엇을 하느냐** 하나다.

**한계**:

- **큐는 완충재지 속도를 바꾸는 물건이 아니다.**\
  정원을 1로 줄이면 대기는 짧아지는데 9,990개를 버린다.\
  생산이 소비보다 계속 빠르면 어떤 큐 길이로도 못 고친다 — 잃는 것이 달라질 뿐이다.
- **백프레셔는 위로 전파되어야 의미가 있다.**\
  BLOCK은 호출 스레드를 묶는다 — 중간에서 흡수하면 그 지점이 새 병목이 된다(03번이 막으려던 사고가 여기서 다시 난다).

## 쓰이는 자료구조·알고리즘

- **유계 큐(bounded queue)** — `ArrayDeque` + 정원. 자바의 `ArrayBlockingQueue`·`LinkedBlockingQueue(capacity)`가 그것이다. 원형 배열은 [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md).
- **모니터(wait/notifyAll)** — BLOCK 정책의 재우기·깨우기. 조건 변수의 원리는 [systems/semaphore](../../systems/semaphore/2-summary.md)의 이웃이다. `while`로 감싸는 이유는 가짜 깨어남.
- **리틀의 법칙(Little's law)** — `대기 시간 = 큐 길이 / 처리율`. 대기 이론의 기본 항등식이고, 정원을 대기 시간으로 번역하는 도구다.
- **항목별 타임스탬프(`Stamped`)** — 대기 시간과 "가장 오래된 항목의 나이"를 재는 근거. 큐 전체에 하나만 두면 틀린다.
- **TCP 흐름 제어** — 수신 창(rwnd)이 0이면 송신자가 멈춘다. 네트워크 계층의 BLOCK 정책이다.
- **Reactive Streams `request(n)`** — 소비자가 "n개만 더"를 말한다. 백프레셔를 위로 전파하는 표준 인터페이스. 스레드를 재우는 BLOCK과 달리 논블로킹으로 요청량을 주고받는다.
- **CoDel** — 큐 길이가 아니라 **큐 안에서 머문 시간**이 목표를 넘으면 버리는 큐 관리 알고리즘(Nichols·Jacobson, "Controlling Queue Delay", ACM Queue 2012 — 머문 시간 목표 기본 5ms). "대기 시간을 지표로" 삼는 발상의 원형.
- 실제 시스템 — Kafka 컨슈머 랙([systems/kafka-consumer-failure](../../systems/kafka-consumer-failure/2-summary.md)), Netty의 `writability`·고수위 표시, 03의 `BulkheadFullException`과 같은 모양의 FAIL.

## 적용 — 풀어나가는 법

### 문제 — 이 챕터가 시키는 것
생산자가 초당 1000개를 넣고 소비자가 초당 100개를 처리하는데 큐에 제한이 없다.\
30초면 큐가 27,000이고 최대 대기가 28초인데 **버린 것 0개, 에러 0건, 성공률 100%** — 지표가 전부 초록인 채로 죽는다.\
**제한 없는 큐가 어떻게 자라는지 기준선으로 재보고, 정원과 네 가지 오버플로 정책을 가진 채널을 구현해 "정원을 두면 무엇을 잃는가"를 숫자로 확인하라**는 챕터다.

과제(원본 README "하는 방법"):

1. `ChannelContractTest.java` 를 따라친다.
2. `UnboundedChannel` 의 **TODO 1~2** — 기준선.\
   그냥 넣고(판단하지 않는다) 꺼낼 때 대기 시간을 기록한다.\
   요점은 **항목마다 들어온 시각을 담는 것**이다(`Stamped(item, enqueuedAt)`).
3. `BoundedChannel` 의 **TODO 3~4** — 본체.\
   `offer` 는 자리가 있으면 넣고 없으면 정책대로(DROP_NEWEST는 false, DROP_OLDEST는 머리를 버리고 true, FAIL은 `ChannelFullException`, BLOCK은 `while` + `wait`), `poll` 은 꺼내고 대기 시간을 기록하고 **자리가 났다고 알린다**(`notifyAll`).

시작점: `cd ~/project/myway/ops-patterns && ./run.sh 05` — 84개 중 73개가 실패하는 상태에서 출발한다.

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

실제 시스템에 붙일 때의 순서: ① 소비자의 **처리율**을 잰다(큐로는 못 바꾸는 값) → ② 허용할 **최대 대기 시간**을 정한다(사용자·호출자 타임아웃에서 역산) → ③ 정원 = 대기 시간 × 처리율 → ④ 찼을 때의 정책(데이터가 정한다 — 순서가 중요하면 DROP_NEWEST, 최신만 의미 있으면 DROP_OLDEST, 선택권을 주려면 FAIL, 전파하려면 BLOCK) → ⑤ 그 신호가 생산자의 생산자까지 올라가는 경로.\
위 「문제」절의 TODO는 기준선(무한)으로 사고를 먼저 재고 정원과 네 정책을 만든다.

## 장애 시나리오와 대처

위 「동작 — 구현의 함정들」절이 다루는 것(if/while·notifyAll 누락·DROP_OLDEST의 조용함·전파) 말고, 운영에서 따로 보이는 장애들이다.

**1. 처리량은 있는데 유효 처리량이 0이다**

- 현상: 소비자 CPU는 100%인데 성공 응답은 0에 가깝다. 클라이언트는 전부 타임아웃 뒤 재시도한다.
- 보이는 형태: 큐에서 꺼낸 항목의 나이(`now - enqueuedAt`)가 호출자 타임아웃보다 크다. 처리 완료 로그는 찍히는데 받는 사람이 없다.
- 원인: 정원은 있지만 큐가 늘 가득 차 있어 꺼낸 항목마다 이미 늦었다. 일은 했는데 쓸모가 없고, 재시도가 다시 큐를 채운다.
- 대처: 꺼낼 때 나이를 보고 **이미 늦은 항목은 처리하지 않고 버린다**(load shedding). 기준은 호출자의 데드라인 — [deadline-propagation](../deadline-propagation/2-summary.md).\
  큐 길이 대신 머문 시간으로 버리는 것이 CoDel의 발상이다.
  - *load shedding(부하 셰딩)*: 과부하일 때 일부 요청을 일부러 버려 나머지를 살리는 것.

**2. 큐 길이 알람은 조용한데 대기 시간이 폭증한다**

- 현상: 큐 길이는 정원 100에서 안 움직이는데 사용자 지연이 10배가 됐다.
- 보이는 형태: 큐 길이 그래프는 평평, 응답 시간 그래프만 계단으로 오른다.
- 원인: 처리율이 떨어졌다(소비자가 부르는 DB가 느려짐). 리틀의 법칙에서 같은 길이라도 처리율이 1/10이면 대기는 10배다. 길이만 보면 안 보인다.
- 대처: 지표를 **가장 오래된 항목의 나이**(`enqueuedAt` 기준)로 바꾼다. 항목마다 시각을 들고 있어야 하는 이유가 측정에서도 반복된다.

**3. 느린 소비자 하나가 전체를 멈춘다**

- 현상: 웹소켓 구독자 1,000명 중 한 명의 네트워크가 느린데 서버 메모리가 선형으로 늘거나, 나머지 999명도 같이 늦는다.
- 보이는 형태: 특정 연결의 송신 버퍼만 계속 자란다. 또는 BLOCK 정책의 방송 스레드가 그 한 연결의 `offer`에서 잠들어 있다.
- 원인: 소비자별 큐가 없이 공유 큐 하나거나, 소비자별 큐가 무한이다. 한 소비자의 느림이 생산자를 잠재우거나 메모리를 먹는다.
- 대처: 소비자마다 유계 큐를 두고, 최신만 의미 있는 데이터면 DROP_OLDEST로 그 소비자만 값을 잃게 한다. 상한을 계속 넘는 소비자는 연결을 끊는다 — 느린 하나를 위해 전체를 세우지 않는다.

## 핵심 문장

- 무한 큐의 사고는 **지표가 전부 초록인 채로** 온다 — 버림 0, 에러 0, 성공률 100%인데 대기 시간만 무한히 자란다.
- **큐 길이를 고르는 것이 곧 대기 시간을 고르는 것이다**(리틀의 법칙) — 큐를 크게 잡는 것은 안전이 아니라 지연을 사는 것이다.
- 정원을 두면 반드시 무언가를 잃는다 — **잃는 양은 같고 잃는 것(최신/옛것/선택권/시간)이 다를 뿐이며**, 무엇을 잃을지는 데이터가 정한다.
- 버리는 것과 던지는 것은 다르다 — 버리면 생산자는 성공한 줄 알고, 던지면 생산자가 고를 수 있다.\
  그 선택권이 값이다.
- DROP_OLDEST는 반환값 true로 다른 항목을 지운다, poll의 notifyAll 누락은 정책 셋에서 안 드러난다 — 이 상자의 사고는 전부 조용하다.

## 관련 주제·근거

- 선행 — [03-bulkhead](../03-bulkhead/2-summary.md) · [04-rate-limiter](../04-rate-limiter/2-summary.md): 나누기·막기. 05는 말하기. 누출 버킷의 큐가 무제한이면 여기의 사고다.
- 선행 — [01-retry-backoff](../01-retry-backoff/2-summary.md): FAIL 정책이 준 선택권으로 생산자가 재시도하면 부하가 는다.
- 후속 — [06-idempotency-store](../06-idempotency-store/2-summary.md): 여기까지가 부하의 세 층, 다음부터 "한 번만 실행되게".
- 곁 — [deadline-propagation](../deadline-propagation/2-summary.md): 늦은 항목을 버리는 기준.
- 곁 — [systems/kafka-consumer-failure](../../systems/kafka-consumer-failure/2-summary.md): 컨슈머 랙이 자라는 파이프라인의 실패.
- 곁 — [systems/server-design/06-resilience.md](../../systems/server-design/06-resilience.md): 백프레셔·로드 셰딩을 서버 설계 안에서.
- 영역 표 — [reliability/README.md](../../reliability/README.md) `12-backpressure-and-load-shedding`.
- 교재 — Google SRE 책 21장 "Handling Overload" · Little, J. D. C. (1961) "A Proof for the Queuing Formula L = λW".
- myway 원본 — `/home/jun/project/myway/ops-patterns/05-backpressure/` (README.md · impl/UnboundedChannel.java · impl/BoundedChannel.java · src/test/.../PolicyTest.java · LatencyTest.java).

### 관련 자료
- 챕터 안내: `/home/jun/project/myway/ops-patterns/05-backpressure/README.md`
- 계약(TODO 없음): `.../src/main/java/com/ops/backpressure/Channel.java`, `OverflowPolicy.java`, `ChannelFullException.java`, `Ticker.java`
- 내 구현(TODO 껍데기): `.../src/main/java/com/ops/backpressure/UnboundedChannel.java`, `BoundedChannel.java`
- 정답 기준 소스: `/home/jun/project/myway/ops-patterns/05-backpressure/impl/UnboundedChannel.java`, `impl/BoundedChannel.java`
- 테스트: `.../src/test/java/com/ops/backpressure/ChannelContractTest.java`, `PolicyTest.java`(네 정책 대차대조), `LatencyTest.java`(정원-대기 측정), `BoundedBlockTest.java`, `BoundedDropNewestTest.java`, `BoundedDropOldestTest.java`, `BoundedFailTest.java`, `UnboundedChannelTest.java`
- 다음 챕터로의 다리: `06-idempotency-store`부터는 "한 번만 실행되게" — 여기까지가 부하를 다루는 세 층(03 나누기, 04 막기, 05 말하기)이었다.

### 용어 풀이
- **백프레셔(backpressure)**: 소비자가 생산자에게 "천천히"라고 말하는 것.\
  밀려드는 압력을 거슬러 올라가는 신호.
- **생산자(producer) / 소비자(consumer)**: 큐에 넣는 쪽 / 큐에서 빼서 처리하는 쪽.
- **유한 큐(bounded) / 무한 큐(unbounded)**: 정원이 있는 큐 / 없는 큐.\
  무한 큐는 장애를 타임아웃(시간 손실)으로 바꿀 뿐이다.
- **정원(capacity)**: 큐가 담을 수 있는 최대 개수.\
  이것을 고르는 것이 곧 대기 시간을 고르는 것.
- **리틀의 법칙(Little's law)**: 대기 시간 = 큐 길이 / 처리율.\
  대기 이론의 기본 공식.
- **오버플로 정책(overflow policy)**: 큐가 찼을 때의 행동 — BLOCK(재움) / DROP_NEWEST(새것 버림) / DROP_OLDEST(옛것 버림) / FAIL(던짐).
- **wait / notifyAll**: 자바에서 스레드를 재우고 깨우는 기본 도구.\
  wait는 잠금을 놓고 자므로 소비자가 그동안 poll 할 수 있다.
- **가짜 깨어남(spurious wakeup)**: 아무 이유 없이 wait에서 깨어나는 현상.\
  그래서 wait는 if가 아니라 while로 감싼다.
- **ChannelFullException**: "큐가 찼다"를 생산자에게 알리는 예외.\
  버림과 달리 생산자에게 선택권을 준다.
- **타임스탬프(enqueuedAt)**: 항목마다 들고 있는 "들어온 시각".\
  대기 시간 측정의 근거 — 큐 전체에 하나만 두면 틀린다.
- **처리율(throughput)**: 소비자가 단위 시간에 빼는 개수.\
  큐로는 못 바꾸는, 소비자가 정하는 값.
