# distributed/27-chain-replication-and-striping — 체인 복제와 스트라이핑: 체인·앙상블/쓰기 정족수·라운드로빈 배치 — 정리 (힌트)

## 해결하는 문제

강한 일관성의 복제를 만드는 방법은 합의(Raft·Paxos, 11·28번)만 있는 것이 아니다.\
"설정 서버 + 단순한 데이터 복제"로 나누는 길이 있다(6.5840 L13).
- 설정 서버: 누가 헤드·테일·프라이머리인지 정한다. 분할 시 split brain을 막아야 하므로 보통 Raft·Paxos·ZooKeeper로 만든다.
- 데이터 복제: 프라이머리-백업, 체인 복제처럼 단순한 프로토콜. split brain 판단은 설정 서버에 맡긴다.

이 노트는 그 데이터 복제 쪽의 두 설계를 본다.
- **체인 복제**: 복제본을 한 줄로 세워 쓰기는 앞(헤드)으로, 읽기는 끝(테일)에서. 프라이머리의 부담을 헤드와 테일로 나눈다.
- **스트라이핑(BookKeeper)**: 한 로그의 엔트리를 여러 노드에 돌려 가며 나눠 쓰고, Qa개 응답이면 성공. E > Qw이면 쓰기 부하를 E대로 나누고, Qa < Qw이면 느린 한 대를 기다리지 않는다.

기초 — Kafka 파티션이 리더 한 대로 쓰기를 받는 구조, BookKeeper의 E·Qw·Qa 그림, 리더 없는 순서 보장, Journal/Ledger 디스크 분리, Kafka와의 비교표 — 는 원본 [systems/striping](../../systems/striping/2-summary.md) §1~§6에 있다. 여기서는 원본에 없던 체인 복제, 장애 양상, 정족수 규칙의 정확한 숫자, 실험을 더한다.

쉬운 예: 서류 결재.
- 체인: 담당 → 과장 → 부장 순서로 도장을 찍고, 부장이 최종 답을 준다. 과장이 자리를 비우면 전부 멈춘다.
- 스트라이핑: 서류마다 다섯 명 중 세 명에게 돌리고, 두 명 도장이면 통과. 한 명이 느려도 다른 둘로 끝난다.

똑같은 구조다. 순서대로 거치면 단순하지만 가장 느린 사람에게 묶이고, 정족수로 받으면 빠르지만 규칙이 늘어난다.

## 동작·원리

### 1. 프라이머리-백업 — 출발점

```text
  client ─write─▶ [P] ──병렬──▶ [B1]
                   │   └──────▶ [B2]
                   ◀── 전원 ack ──┘    → client에 OK      ("write all")
  client ─read──▶ [P]                                     ("read one")
```

- 프라이머리가 순서를 정해 모든 백업에 보내고, **전원** 응답을 받은 뒤 답한다. 읽기는 프라이머리가 혼자 답한다. ROWA(read one, write all)라고도 한다(6.5840 L13).
- 모든 복제본이 커밋된 값을 다 가지므로 N대 중 N−1대가 죽어도 견딘다. 과반 정족수(N/2 미만 장애)보다 많다(6.5840 L13).
- 대가: 백업 하나라도 느리면 쓰기가 느리다. 백업이 죽으면 설정 서버가 그 백업을 빼 줘야 쓰기가 다시 진행된다.

### 2. 체인 복제 — 헤드에 쓰고 테일에서 읽는다

```text
  쓰기:  client ─▶ [Head] ─▶ [Mid] ─▶ [Tail] ─OK─▶ client
  읽기:  client ─────────────────────▶ [Tail] ─값─▶ client
  ack:                [Head] ◀── [Mid] ◀── [Tail]   (테일이 받은 것까지 앞쪽이 보관분을 지움)
```

- van Renesse–Schneider 2004
  - 갱신은 헤드에서 처리하고 상태 변경을 신뢰할 수 있는 FIFO 링크로 다음 노드에 넘긴다. 테일까지 가면 테일이 답한다.
  - 조회는 테일이 처리한다. 갱신과 조회가 모두 **테일 한 곳**에서 직렬로 결정되므로 강한 일관성이 나온다.
  - 서버는 fail-stop이라고 가정한다. 고장 나면 멈추고, 멈춘 것을 환경이 감지할 수 있다.
  - 서버 t대로 복제하면 t−1대가 죽어도 객체를 쓸 수 있다.
- 왜 테일에서 답하나: 테일이 본 갱신은 체인의 모든 노드가 이미 갖고 있다. 그래서 테일이 보여 준 값은 허용된 장애 뒤에도 사라지지 않는다(6.5840 L13).
  - 헤드가 다음 노드의 "받았다"만 보고 답하면 선형화가 깨진다. 클라이언트가 OK를 받은 뒤 테일에서 읽어도 아직 옛 값일 수 있다(6.5840 L13의 질문).
- 장애 처리는 설정 서버(논문의 master)가 한다(6.5840 L13)
  - 헤드 장애: 두 번째 노드가 새 헤드. 옛 헤드만 알던 갱신은 사라지고, 클라이언트가 응답을 못 받아 다시 보낸다.
  - 테일 장애: 끝에서 두 번째가 새 테일. 그 노드는 옛 테일만큼 최신이거나 더 최신이다.
  - 중간 장애: 앞뒤 노드를 직접 잇는다. 앞 노드가 이미 보낸 갱신 일부를 다시 보낸다.
  - 복제본 추가: 새 노드를 테일 뒤에 붙인다. 상태를 미리 복사해 두고 마지막 몇 갱신만 잠깐 멈춰 보낸다.
- 분할: 체인 중간 링크가 끊기면 갱신은 테일에 못 닿아 완료되지 않는다. 테일과 닿는 클라이언트의 읽기는 계속된다. 안전(선형화)하지만 쓰기는 멈춘다(6.5840 CR FAQ). 옛 테일이 살아 있는데 설정 서버가 새 테일을 정하면 옛 테일이 옛 값을 줄 수 있다. 논문은 이 split brain 방지를 다루지 않는다. 테일에 리스를 주고 리스가 끝난 뒤에야 새 테일을 정하는 방법이 제안된다(같은 FAQ).

### 3. 세 방식의 지연 — 누구를 기다리나

```text
  체인:            처리(Head) + 처리(Mid) + 처리(Tail)       ← 합
  프라이머리-백업:   처리(P) + max(처리(B1), 처리(B2))        ← 가장 느린 백업
  정족수(Qw=3,Qa=2): 세 곳 중 2번째로 빠른 처리               ← 느린 소수를 건너뜀
```

- 6.5840 L13의 비교: 프라이머리-백업(체인 포함)은 서버 하나만 느려도 느리다. 정족수는 일시적으로 느린 소수를 견딘다. 대신 정족수는 N/2 미만 장애만 견디고, 체인은 N−1까지 견딘다.
- 체인의 장점: 헤드는 다음 노드 한 곳에만 보낸다. 프라이머리는 모든 백업에 보낸다. 데이터가 클 때 헤드의 네트워크 부담이 작다. 읽기는 테일, 쓰기는 헤드라 일이 나뉜다.

#### 실험: 체인·프라이머리-백업·정족수의 쓰기 지연, 가운데 노드가 느릴 때

- 환경: Java 21 단일 프로세스. 노드 3개를 단일 스레드 실행기로 만들고(노드마다 한 번에 하나씩 처리), 처리 시간은 `Thread.sleep`(예시 값). 쓰기 200건을 하나씩(앞 응답 뒤 다음) 보내 실제 경과 시간을 쟀다. 네트워크 비용은 넣지 않았다.

```java
// ChainSim.java 핵심
static CompletableFuture<Void> chain(int i) {            // 0 → 1 → 2, 테일이 끝나면 완료
    return CompletableFuture.runAsync(() -> work(i), nodes[i])
            .thenCompose(v -> i == nodes.length - 1 ? CompletableFuture.completedFuture(null) : chain(i + 1));
}
static CompletableFuture<Void> quorum(int qa) {          // 세 곳에 병렬, qa개 끝나면 완료
    CompletableFuture<Void> done = new CompletableFuture<>();
    AtomicInteger acks = new AtomicInteger();
    for (int i = 0; i < 3; i++) { int n = i;
        CompletableFuture.runAsync(() -> work(n), nodes[n])
            .thenRun(() -> { if (acks.incrementAndGet() == qa) done.complete(null); }); }
    return done;
}
```

(실험, Java 21 스레드 시뮬레이션, 2026-10-01)

```text
[A] 세 노드 모두 처리 2ms
  chain           p50   6.5ms  p99   7.1ms  (응답 뒤 남은 일 처리 1ms)
  primary-backup  p50   4.3ms  p99   4.6ms  (응답 뒤 남은 일 처리 0ms)
  quorum Qa=2     p50   2.1ms  p99   2.3ms  (응답 뒤 남은 일 처리 0ms)
[B] 가운데 노드(1번)만 처리 20ms — GC·디스크 지연 흉내
  chain           p50  24.5ms  p99  25.6ms  (응답 뒤 남은 일 처리 0ms)
  primary-backup  p50  22.3ms  p99  22.7ms  (응답 뒤 남은 일 처리 0ms)
  quorum Qa=2     p50   2.1ms  p99   2.4ms  (응답 뒤 남은 일 처리 3593ms)
```

- 체인 지연은 처리 시간의 **합**(2+2+2 → 6.5ms, 2+20+2 → 24.5ms)이었다. 가운데 한 대가 느리면 모든 쓰기가 그만큼 늦다.
- 프라이머리-백업은 **가장 느린 백업**(20ms)에 묶였다.
- 정족수(Qa=2)는 느린 노드를 기다리지 않아 2.1ms 그대로였다. 대신 느린 노드에 일이 쌓였다. 200건을 다 응답한 뒤에도 그 노드가 밀린 일을 끝내는 데 3593ms가 더 걸렸다. 응답이 빠르다고 그 노드가 따라오고 있다는 뜻은 아니다.
- 수치는 sleep 값과 스레드 스케줄에 따라 실행마다 조금 다르다. 순서(체인 > 프라이머리-백업 > 정족수)와 합·최댓값·2번째 값이라는 구조가 요점이다.

### 4. 스트라이핑 — BookKeeper의 정확한 규칙 (Apache BookKeeper 4.17 프로토콜 문서)

```text
  E=4, Qw=3, Qa=2, 앙상블 [B1 B2 B3 B4]
  entry 0 → B1 B2 B3        write quorum = 앙상블에서 (entryId % E) 위치부터 Qw개
  entry 1 → B2 B3 B4
  entry 2 → B3 B4 B1
  entry 3 → B4 B1 B2
  entry 4 → B1 B2 B3        서로 다른 write quorum은 E개뿐. Qw=E면 하나(스트라이핑 없음)
  ack quorum = write quorum 중 아무 Qa개
```

- 메타데이터(ZooKeeper에 저장, CAS로 갱신): E(앙상블 크기), Qw(쓰기 정족수 = 엔트리당 최대 복제 수), Qa(ack 정족수 = 최소 복제 수), 상태(OPEN·CLOSED·IN_RECOVERY), fragment 목록. 원장 생성 시 E ≥ Qw ≥ Qa가 아니면 생성이 실패한다.
- 쓰기: Qa개 bookie가 확인하면 클라이언트에 성공. 단, **더 작은 엔트리가 모두 성공한 뒤에만**. bookie는 디스크에 영속화한 뒤 확인한다.
- **견디는 장애 수는 Qa − 1이다.** 문서 문장: "The system can tolerate Qa – 1 failures without data loss."
  - 참고: 원본 §3의 "각 entry는 3벌 → 2대까지 죽어도 안전"은 Qw 기준이라 틀리다. 성공 응답은 Qa벌만 보장하므로 E=5·Qw=3·Qa=2에서 보장은 1대다(BookKeeper 프로토콜 문서 "Guarantees").
- bookie가 쓰기를 확인하지 못하면 writer가 그 bookie를 바꾼 새 앙상블로 **새 fragment**를 만든다. 시작점은 클라이언트에 아직 확인되지 않은 첫 엔트리다. 메타데이터 CAS가 실패하면 다시 읽고, 상태가 OPEN이 아니면 쓰기를 실패시킨다.
- 펜싱(새 writer가 옛 writer를 막기): 상태를 IN_RECOVERY로 바꾸고 마지막 fragment의 bookie들에 fence를 보낸다. **write quorum마다 (Qw − Qa) + 1개**가 응답하면 펜싱 완료다. 그러면 옛 writer는 어느 write quorum에서도 Qa개 확인을 모을 수 없다. 옛 writer는 `LedgerFenced`를 받는데, 이것은 "안 쓰였다"가 아니라 "모른다"다(타임아웃처럼 다룬다).
  - 참고: 원본 「[Claude 추가]」 B의 "Qa가 Qw의 과반이어야 하는지 (확인 필요)"는 프로토콜 문서에 과반 조건이 없다. 복구·펜싱이 기다리는 수가 write quorum마다 (Qw − Qa) + 1개다.
- 읽기: 다른 클라이언트는 LAC(last add confirmed)까지 읽을 수 있다. LAC까지는 Qa벌 복제가 보장된다.
- 순서 보장의 범위는 원장(ledger) 하나다. 여러 원장을 이어 로그를 만드는 것과 리더 선출은 BookKeeper 밖(ZooKeeper 등)이다.

#### 실험: 스트라이핑 배치와 편중

- 환경: 위 Java 프로그램의 [C] 부분. 프로토콜 문서의 `(entryId % E)` 규칙으로 bookie별 저장 수를 셌다. 이어서 E=Qw=3(스트라이핑 없음)인 원장 20개를 bookie 5대에 놓는 세 방법을 비교했다. 원장마다 엔트리 1000개, 원장 0만 9000개(핫 원장).

```java
for (int e = 0; e < 10_000; e++) for (int k = 0; k < Qw; k++) cnt[(e % E + k) % E]++;   // 원장 하나 안
List<Integer> ens = switch (how) {                                                         // 원장 배치
    case "항상 앞 3대" -> List.of(0, 1, 2);
    case "무작위 3대" -> { List<Integer> all = new ArrayList<>(List.of(0, 1, 2, 3, 4)); Collections.shuffle(all, r); yield all.subList(0, 3); }
    default -> List.of(l % 5, (l + 1) % 5, (l + 2) % 5);                                    // 시작 위치 순환
};
```

(실험, Java 21, 2026-10-01)

```text
[C] ledger 1개, E=5 Qw=3, entry 10000개 → Bookie별 저장 수 [6000, 6000, 6000, 6000, 6000]
    항상 앞 3대    Bookie별 entry [28000, 28000, 28000, 0, 0]  최대/평균 1.67
    무작위 3대     Bookie별 entry [21000, 17000, 12000, 23000, 11000]  최대/평균 1.37
    시작 위치 순환   Bookie별 entry [20000, 20000, 20000, 12000, 12000]  최대/평균 1.19
```

- 원장 하나 안에서는 라운드로빈이 완벽히 고르다(5대 × 6000 = 10000 × Qw 3).
- 원장을 bookie에 놓는 방법이 나쁘면 편중된다. "항상 앞 3대"는 2대가 놀았다.
- 순환 배치도 1.19였다. 핫 원장 0이 놓인 bookie 0·1·2에 9000씩 더 얹혔다. 스트라이핑은 **원장 안의** 부하를 나눌 뿐, 원장 간 쏠림은 배치 정책과 원장 크기가 정한다.
- 무작위 배치는 표본이 작으면(원장 20개) 운에 따라 편중된다. 6.5840 L13·논문 §5.4도 무작위 배치(rndpar)가 복구는 빠르지만 임의의 서버 3대가 동시에 죽으면 어떤 체인의 복제본이 모두 사라질 확률이 커진다고 짚는다.

### 5. 여러 체인·원장을 서버에 펼치기

```text
  나쁜 배치: 샤드 A = S1 S2 S3, 샤드 B = S4 S5 S6
    → 헤드·테일에 일이 몰리고 중간은 덜 바쁘다(중간도 모든 쓰기를 적용·전달하지만 클라이언트 요청은 안 받는다). S1이 죽으면 새 서버 한 대가 디스크 전체를 한 곳에서 복사(수 시간)
  좋은 배치(샤드 ≫ 서버): A = S1 S2 S3, B = S2 S3 S1, C = S3 S1 S2 …
    → 서버마다 어떤 체인에선 헤드, 어떤 체인에선 테일. 한 대가 죽으면 그 서버의 샤드 M개를 서로 다른 M대가 병렬로 복구
```

- 6.5840 L13: 1TB를 1Gbit/s로 옮기면 두 시간쯤 걸린다. 그동안 남은 복제본이 또 죽을 위험이 있다. 그래서 샤드를 서버보다 훨씬 많이 만들어 복구를 병렬화한다.
- BookKeeper도 같은 결이다. ensemble change는 새 엔트리부터 새 bookie를 쓰고, 빠진 복제는 백그라운드에서 fragment 단위로 채운다(원본 「[Claude 추가]」 C의 auditor·replication worker 설명).

## 쓰이는 자료구조·알고리즘

- **체인(단일 연결 리스트) + FIFO 링크** — 갱신이 헤드에서 테일로 한 방향으로 흐른다. 앞 노드의 이력은 뒤 노드의 이력을 접두사로 포함한다(논문 §3 Update Propagation Invariant). [data-structure/02-linked-list](../../data-structure/02-linked-list/2-summary.md)
- **보낸 갱신 버퍼(큐)** — 각 노드는 다음 노드로 보냈지만 테일이 확인하지 않은 갱신을 들고 있다가, 테일의 ack가 거꾸로 올라오면 지운다. 중간 노드 장애 때 재전송에 쓴다. [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **라운드로빈 배치(모듈러)** — `(entryId % E)`부터 Qw개. 원장 안의 부하를 E대에 고르게 나눈다.
- **정족수 교집합** — 펜싱이 write quorum마다 (Qw − Qa) + 1개를 모으면, 남은 bookie가 Qa개보다 적어 옛 writer가 정족수를 못 만든다. [09-quorums](../09-quorums/2-summary.md)
- **CAS 메타데이터** — fragment 추가·원장 닫기가 ZooKeeper의 compare-and-swap으로 직렬화된다.

## 적용 — 풀어나가는 법

### 1. 언제 무엇을 고르나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 큰 객체·블록을 강하게 복제, 설정 서버가 이미 있음 | 체인 복제 | 헤드 네트워크 부담 작음, 읽기를 테일로 분산, 재동기화 단순 |
| 일시적으로 느린 복제본이 흔함(GC·디스크) | 정족수(Qa < Qw) | 느린 소수를 기다리지 않음 |
| 한 로그의 쓰기 처리량을 노드 한 대 넘게 | 스트라이핑(E > Qw) | 엔트리를 E대에 나눔 |
| 단순함이 우선, 파티션을 늘릴 수 있음 | Kafka식 리더 + ISR | 운영 구성요소가 적음(원본 §6) |

### 2. BookKeeper 설정을 숫자로 읽는다

- E=5, Qw=3, Qa=2라면
  - 엔트리당 3벌 쓰기를 시도하고 2벌 확인으로 성공한다.
  - 데이터 손실 없이 견디는 장애: Qa − 1 = 1대.
  - 펜싱·복구는 write quorum마다 (3 − 2) + 1 = 2개 응답이 필요하다.
- bookie의 `journalSyncData`(기본 true)는 저널을 fsync한 뒤 확인한다. 끄면 쓰기는 빨라지지만 전원 장애 때 확인된 엔트리를 잃을 수 있다(BookKeeper 설정 문서). 저널과 원장 디렉터리는 "이상적으로는" 다른 장치에 둔다(BookKeeper "BookKeeper administration"). [os/24-fsync-and-durability](../../os/24-fsync-and-durability/2-summary.md)

### 3. 체인을 운영할 때 보는 것

```java
// 체인 노드: 받은 갱신을 적용하고 다음 노드로 넘긴 뒤, 테일 ack가 올 때까지 보관
final class ChainNode {
    private final Deque<Update> sentButUnacked = new ArrayDeque<>();
    private ChainNode next;                       // 테일이면 null
    void onUpdate(Update u) {
        store.apply(u);                            // 로컬 적용
        if (next == null) { client(u).reply(u.id()); ackUpstream(u.seq()); return; }   // 테일이 답한다
        sentButUnacked.addLast(u);
        next.send(u);                              // FIFO 링크
    }
    void onAck(long seq) {                         // 테일 쪽에서 거꾸로 올라오는 ack
        while (!sentButUnacked.isEmpty() && sentButUnacked.peekFirst().seq() <= seq) sentButUnacked.pollFirst();
        ackUpstream(seq);
    }
    void onNewSuccessor(ChainNode s, long successorLastSeq) {   // 중간 노드 장애 뒤 재연결
        next = s;
        for (Update u : sentButUnacked) if (u.seq() > successorLastSeq) s.send(u);   // 빠진 것만 재전송
    }
}
```

- `sentButUnacked` 길이가 계속 늘면 뒤쪽 노드가 느리거나 끊긴 것이다. 체인 지연 = 노드 처리의 합이므로 노드별 처리 시간 p99를 따로 본다.

### 4. Kafka와 비교할 때의 진단 명령

```bash
# Kafka 4.1: 파티션 리더와 ISR (acks=all은 현재 ISR 전원을 기다린다)
kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic orders
# 팔로워가 replica.lag.time.max.ms(4.1 기본 30000ms) 안에 못 따라오면 ISR에서 빠진다
```

- Kafka 4.1 설계 문서: `acks=all`의 확인은 **현재 ISR 전원**이 받은 시점이다. 느린 팔로워는 ISR에서 빠지기 전까지 쓰기 지연을 붙잡는다. 이 점에서 프라이머리-백업(전원 대기)과 같은 성질이다. 다만 ISR을 줄여 진행한다.

## 장애 시나리오와 대처

### 1. 체인 중간 노드가 느림 → 전체 쓰기 지연

- **현상**: 쓰기 p50이 갑자기 몇 배로 뛴다. 읽기(테일)는 멀쩡하다.
- **보이는 형태**: 쓰기 지연 = 노드 처리 시간의 합. 실험에서 가운데 노드만 2ms → 20ms가 되자 체인 쓰기가 6.5ms → 24.5ms. 앞쪽 노드의 "보냈지만 미확인" 버퍼가 늘어난다.
- **원인**: 체인은 모든 노드를 순서대로 거친다. 느린 한 대를 건너뛸 수 없다. 6.5840 L13: 프라이머리-백업·체인은 서버 하나만 느려도 느리다.
- **대처**: 노드별 처리 시간을 따로 감시한다. 오래 느린 노드는 설정 서버가 체인에서 뺀다(장애 탐지 타임아웃 조정 — 너무 빠르면 불필요한 복제본 재구성, 너무 느리면 오래 멈춤, 6.5840 L13). 느린 소수가 흔한 환경이면 정족수 방식을 검토한다.

### 2. 정족수로 지연은 숨겼는데 느린 bookie가 계속 밀림

- **현상**: 쓰기 지연은 정상인데 특정 bookie의 디스크·메모리 사용이 계속 오르고, 결국 그 bookie가 응답을 못 하며 앙상블 교체가 몰린다.
- **보이는 형태**: 실험에서 Qa=2 응답은 2.1ms였지만 느린 노드는 응답 뒤에도 3593ms 동안 밀린 일을 처리했다.
- **원인**: Qa < Qw면 느린 복제본을 기다리지 않을 뿐, 그 복제본에도 계속 보낸다. 따라오지 못하면 큐가 쌓인다. 그동안 그 엔트리들의 실제 복제 수는 Qw보다 적다.
- **대처**: bookie별 지연·큐 지표를 본다. 확인하지 못하는 bookie는 프로토콜대로 새 fragment로 교체된다. 느림이 일시적인지 장애인지 판단할 타임아웃을 정한다.

### 3. 스트라이프 배치 편중 → 일부 bookie만 과부하

- **현상**: bookie 다섯 대 중 세 대만 디스크가 차고 두 대는 한가하다.
- **보이는 형태**: bookie별 저장량·쓰기량 지표가 고르지 않다. 실험에서 "항상 앞 3대" 배치는 28000·28000·28000·0·0, 순환 배치도 핫 원장 때문에 최대/평균 1.19.
- **원인**: 원장 안의 라운드로빈은 고르지만, 원장을 어느 bookie 집합에 놓느냐는 배치 정책이 정한다. 랙 인식 배치 정책(설정 문서의 AutoRecovery 배치 기본값이 `RackawareEnsemblePlacementPolicy`)에서 랙마다 bookie 수가 다르면 적은 랙의 bookie가 더 자주 뽑힐 수 있다 [?]. 원장 하나가 유난히 크면 그 E대가 뜨겁다.
- **대처**: E > Qw로 원장 안 분산을 키운다. 원장을 주기적으로 롤오버해 큰 원장을 쪼갠다(원본 「[Claude 추가]」 C의 Pulsar rollover). 배치 정책과 랙 구성을 맞춘다.

### 4. 옛 writer의 늦은 쓰기 → `LedgerFenced`

- **현상**: writer를 교체한 뒤 옛 writer 쪽 클라이언트가 `LedgerFenced` 에러를 받는다.
- **보이는 형태**: 옛 writer는 개별 bookie 몇 곳에 쓰기를 보냈지만 Qa개 확인을 모으지 못한다.
- **원인**: 새 writer가 원장을 복구하며 write quorum마다 (Qw − Qa) + 1개 bookie를 펜싱했다.
- **대처**: `LedgerFenced`는 타임아웃처럼 다룬다. 그 엔트리가 쓰였는지는 복구가 끝나 원장이 닫힌 뒤 읽어 봐야 안다(프로토콜 문서). 멱등 키로 다시 쓴다.

### 5. 체인 테일 교체 중 옛 테일이 옛 값을 준다

- **현상**: 설정 서버가 새 테일을 정한 뒤에도 일부 클라이언트가 옛 값을 읽는다.
- **보이는 형태**: 옛 테일과 아직 연결된 클라이언트에서만 생긴다.
- **원인**: 옛 테일은 살아 있는데 설정 서버와 끊겼다. 더 이상 갱신을 못 받지만 읽기에는 답한다. split brain이다(6.5840 CR FAQ).
- **대처**: 테일에 리스를 주고, 리스가 끝난 뒤에만 새 테일을 정한다. 클라이언트는 설정 서버의 세대 번호를 확인한다(12번 펜싱).

## 핵심 문장

- 체인 복제는 헤드에서 쓰고 테일에서 읽는다. 갱신과 조회가 테일 한 곳에서 결정되어 강한 일관성이 나오고, t대 중 t−1대 장애를 견딘다.
- 체인 쓰기 지연은 노드 처리 시간의 합이다. 가운데 한 대가 느리면 모든 쓰기가 느리다.
- 정족수(Qa < Qw)는 느린 소수를 건너뛰지만, 그 소수에 일이 쌓이는 것까지 막지는 않는다.
- BookKeeper는 엔트리를 (entryId % E)부터 Qw대에 쓰고 Qa개 확인이면 성공한다. 데이터 손실 없이 견디는 장애는 Qw − 1이 아니라 Qa − 1이다.
- 스트라이핑은 원장 안의 부하를 나눈다. 원장 간 쏠림은 배치 정책과 원장 크기가 정한다.

## 관련 주제·근거

- 선행
  - [09-quorums](../09-quorums/2-summary.md) — 정족수 교집합, 쓰기·읽기 정족수
  - 원본 [systems/striping](../../systems/striping/2-summary.md) — Kafka 파티션 한계, E·Qw·Qa 그림, 리더 없는 순서, Journal/Ledger 분리, Kafka 비교
- 후속·연결
  - [06-replication-strategies](../06-replication-strategies/2-summary.md) — 단일 리더 복제와의 비교
  - [systems/straggler](../../systems/straggler/2-summary.md) — 느린 한 대가 전체를 붙잡는 문제
  - [systems/kafka-why-fast](../../systems/kafka-why-fast/2-summary.md) — Kafka 쪽 전제
  - [11-consensus-raft](../11-consensus-raft/2-summary.md) · [12-coordination-and-fencing](../12-coordination-and-fencing/2-summary.md) · [21-kafka-internals](../21-kafka-internals/2-summary.md)(ISR)
  - [os/32-raid](../../os/32-raid/2-summary.md) — RAID 0 스트라이핑과의 비교 · [os/24-fsync-and-durability](../../os/24-fsync-and-durability/2-summary.md)
  - 참고: 원본 정답 3의 "응답 시간은 6ms 수준을 유지"는 근거가 없는 수치다. 이 노트의 실험처럼 처리 시간을 정해 두면 정족수 응답은 "2번째로 빠른 노드"가 정한다.
- 논문·강의
  - van Renesse, Schneider, "Chain Replication for Supporting High Throughput and Availability", OSDI 2004 — §3 fail-stop 가정, t−1 장애, 갱신은 헤드·조회는 테일, Update Propagation Invariant, 장애 처리, §5 체인 배치(§5.4 rndpar) <https://www.cs.cornell.edu/home/rvr/papers/OSDI04.pdf>
  - MIT 6.5840 Spring 2026 L13 "Chain Replication" 노트와 FAQ — 설정 서버 + 데이터 복제 분리, ROWA, 장애 처리, p/b vs 체인 vs 정족수, 샤드 배치·병렬 복구 <https://pdos.csail.mit.edu/6.824/notes/l-cr.txt> · <https://pdos.csail.mit.edu/6.824/papers/cr-faq.txt>
- 제품 문서
  - Apache BookKeeper 4.17 "The BookKeeper protocol" — E≥Qw≥Qa, write quorum = (entryId % E)부터 Qw개, Qa−1 장애 허용, ensemble change·fragment, 펜싱 (Qw−Qa)+1, LAC, `LedgerFenced` <https://bookkeeper.apache.org/docs/development/protocol>
  - Apache BookKeeper "BookKeeper concepts and architecture"(striping, journal·entry log), 설정 참조(`journalSyncData` 기본 true, AutoRecovery의 `ensemblePlacementPolicy` 기본 Rackaware), "BookKeeper administration"(journal과 ledger 디렉터리는 이상적으로 다른 장치) <https://bookkeeper.apache.org/docs/getting-started/concepts>
  - Apache Kafka 4.1 Design "Replication"(ISR, `acks=all`), Broker configs(`replica.lag.time.max.ms` 30000) <https://kafka.apache.org/41/design/design/>
- 실험 목록
  - Java 21 스레드 시뮬레이션(노드 3개, 처리 2ms / 가운데만 20ms, 쓰기 200건): 체인·프라이머리-백업·정족수 Qa=2의 p50·p99와 남은 일 처리 시간
  - Java 21: `(entryId % E)` 배치의 bookie별 저장 수, 원장 20개(핫 원장 1개)를 bookie 5대에 놓는 세 방법의 편중
