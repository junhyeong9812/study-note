# cs/kafka-why-fast — Kafka가 빠른 이유 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 원고는 내가 직접 쓴 `db-engine-lab/docs/study/kafka.md`에 zero-copy 데이터 경로 배경을 더해 한 골격으로 편집한 것이다(2026-08-20).
> SSD 내부 동작(FTL·매핑·RMW·GC·WAF) 부분은 [nand-flash](../nand-flash/)로 분리한다. 여기서는 결론만 연결한다.

## 전체 흐름

한 줄: **Kafka는 빠른 저장소 위에 세운 시스템이 아니라, 가진 저장소(디스크·페이지 캐시·NIC)가 가장 잘하는 패턴만 쓰도록 데이터 모델 자체를 설계한 시스템이다.**

```text
질문     디스크에 모든 메시지를 쓰는데 단일 브로커로 초당 100만 건이 어떻게 가능한가?
전제     "디스크는 느리다"는 random access 기준이다. sequential은 같은 디스크에서 수천 배 빠르다.
답       ① append-only 로그 → 디스크 접근을 100% 순차로 강제
         ② OS 페이지 캐시 → 자기 캐시를 얹지 않는다. lag이 작으면 읽기는 RAM에서 RAM으로
         ③ zero-copy(sendfile) → JVM이 데이터 경로에서 빠진다
         ④ 배치 + 압축 → 네트워크 왕복과 write 횟수를 줄여 "한 번의 큰 순차 write"로 만든다
뼈대     이 네 가지를 가능하게 하는 것은 트릭이 아니라 데이터 모델이다.
         파티션 = 로그 파일, offset = 컨슈머가 관리하는 파일 위치, 수정 API 없음.
대가     fsync 안 함(복제로 대체), lag 크면 캐시 미스로 급락, TLS 켜면 zero-copy 불가, NVMe 시대엔 전제가 약해짐.
```

## 1. 전제 — 디스크가 느리다는 건 어느 기준인가

```text
메모리 접근        ~100 ns
SSD random access  ~100 µs   (1,000배)
HDD random access  ~10 ms    (100,000배)

같은 HDD 기준
  random write     ~100 IOPS
  sequential write ~600 MB/s     → 같은 디스크인데 수천 배 차이
```

순차가 빠른 이유는 HDD에서는 헤드가 이미 그 자리에 있어 회전만 하면 되기 때문이고, SSD에서는 큰 블록을 한 번에 프로그램하고 컨트롤러가 여러 채널에 병렬 배치할 수 있기 때문이다. 랜덤이 느린 이유는 HDD는 매번 seek + 회전 대기(~10 ms), SSD는 FTL 매핑 조회 + read-modify-write + GC/write amplification이다(→ nand-flash).

대역폭 = IOPS × I/O 크기. 작은 I/O가 많으면(인덱스 조회, 4KB 랜덤) IOPS가 병목이고, 큰 I/O가 적으면(로그 순차 쓰기) 대역폭이 병목이다. Kafka는 후자 쪽으로만 일한다.

## 2. 데이터 경로 — 일반 애플리케이션 vs Kafka

### 먼저 알아야 할 것

- `write(fd, buf, len)`은 시스템 콜이다. 자바 객체가 아니라 바이트 주소와 길이를 커널에 넘긴다. 커널은 페이지 캐시에 복사하고 즉시 리턴하며, 디스크 flush는 나중에 flusher 스레드가 비동기로 한다.
- 커널 공간과 사용자 공간 사이의 복사(`copy_to_user` / `copy_from_user`)는 CPU가 한다. 디스크↔메모리, 메모리↔NIC 사이의 복사는 DMA가 하므로 CPU를 거의 안 쓴다.
- JVM 입장에서 힙에 올라온 바이트는 GC 대상이다. 데이터가 힙을 지나가면 GC 부담과 객체 오버헤드(대략 2배)가 따라온다.

### 일반 방식 — 파일을 읽어 소켓으로 보내면

```text
Kafka log file
    │  ① DMA (Disk → Page Cache)
    ▼
┌───────────────────────┐
│ Kernel Page Cache     │
└───────────────────────┘
    │  ② copy_to_user   (CPU 복사)
    ▼
┌───────────────────────┐
│ JVM / App Buffer      │  ← 여기서 역직렬화, 비즈니스 로직, 직렬화가 끼어든다
└───────────────────────┘
    │  ③ write() → copy_from_user   (CPU 복사)
    ▼
┌───────────────────────┐
│ Kernel Socket Buffer  │
└───────────────────────┘
    │  ④ DMA (Socket Buffer → NIC)
    ▼
   NIC ──→ Network ──→ Consumer
```

복사 4회(DMA 2 + CPU 2), 커널↔사용자 컨텍스트 스위치 4회. 일반 애플리케이션의 흐름이 `DB → Java Object → Deserialize → Business Logic → Serialize → HTTP Response`인 이상 이 두 번의 CPU 복사는 피할 수 없다. 데이터가 "객체"가 되는 순간 JVM을 지나야 하기 때문이다.

### Kafka 방식 — 페이지 캐시를 소켓에 바로 연결

```text
Kafka Log File
    │  DMA
    ▼
┌────────────────────────┐
│ Linux Page Cache       │
│ (Kafka message bytes)  │
└────────────────────────┘
    │  sendfile() / FileChannel.transferTo()
    │  JVM으로 복사하지 않는다 — 소켓 쪽에는 page를 가리키는 descriptor만 넘어간다
    ▼
┌────────────────────────┐
│ Kernel Network Stack   │
│ (skb가 page를 참조)     │
└────────────────────────┘
    │  DMA (NIC가 page memory를 직접 읽는다 — scatter/gather)
    ▼
   NIC ──→ Network ──→ Consumer
```

CPU 복사 0회(NIC가 scatter/gather DMA를 지원할 때), DMA 2회, 컨텍스트 스위치 2회. **JVM은 데이터 경로에서 빠진다.** Kafka가 이렇게 할 수 있는 이유는 브로커가 메시지를 "해석"하지 않기 때문이다. 프로듀서가 보낸 바이트를 그대로 로그에 붙이고, 컨슈머에게 그대로 내보낸다. 압축도 프로듀서가 배치 단위로 하고 브로커는 풀지 않는다.

### fetch 한 번의 실제 경로

```text
① Consumer         FETCH partition=0, offset=1000
② Kafka Broker     offset → 어느 segment 파일의 어느 위치인지 계산 (인덱스 파일)
③ Linux Kernel     해당 파일 page 확인
④ Page Cache       page가 있으면 디스크 접근 없음 / 없으면 Disk → Page Cache
⑤ sendfile()       page cache를 socket에 연결
⑥ TCP/IP Stack     TCP segment, IP header 구성 (page는 참조만)
⑦ NIC              DMA로 page memory 접근
⑧ Network
⑨ Consumer
```

그래서 이상적인 Kafka 데이터 흐름은 `SSD → RAM → Consumer`가 아니라 다음이다.

```text
Producer → Broker → Linux Page Cache ─(zero-copy)→ NIC → Consumer
```

프로듀서가 쓴 바이트가 페이지 캐시에 올라가고, 컨슈머가 바짝 따라붙어 있으면 그 바이트가 디스크를 거치지 않은 채 NIC로 나간다. 디스크 write는 나중에 flusher가 한다. 읽기 경로에서 디스크를 안 건드리는 것이 핵심이다.

정정 하나: "JVM을 아예 안 지난다"는 아니다. 프로듀서에게서 네트워크로 받은 바이트는 JVM을 거친다. Kafka는 DirectByteBuffer(힙 밖)와 FileChannel로 GC 대상 힙 영역을 최소로 통과시킨다. 정확한 표현은 **"메시지를 힙에 캐싱하지 않는다"**이다.

## 3. 네 가지 트릭 — 각각 왜 필요하고 무엇을 치르는가

### ① Append-only 로그

파일 끝에만 덧붙이고 이미 쓴 데이터는 절대 수정하지 않는다. B-Tree 기반 DB는 "id=42의 status를 바꿔라"를 그 행이 있는 페이지를 찾아가 제자리 수정(in-place update)하므로 랜덤 I/O가 생긴다. Kafka에는 수정/삭제 API 자체가 없다. 삭제는 오래된 세그먼트 파일(기본 1GB 단위 롤오버)을 통째로 지우는 것이다.

```text
segment 파일
[msg0][msg1][msg2][msg3][          빈 공간 →
                        ↑ write pointer (여기서만 쓴다)
```

결과: 디스크 접근이 100% 순차 패턴이 되도록 **강제**된다. SSD에서도 유효한데, 블록이 순서대로 채워지고 세그먼트 단위로 통째 무효화되므로 GC가 복사할 유효 페이지가 거의 없어 WAF ≈ 1이 된다(→ nand-flash).

### ② OS 페이지 캐시에 맡긴다

Kafka는 자기만의 캐시 계층을 얹지 않는다. 일반 설계가 `JVM 힙에 메시지 객체 캐싱 → 필요할 때 직렬화 → write()`라면, Kafka는 `이미 직렬화된 바이트 → write() → 페이지 캐시`다. GC 부담이 없고 캐시 관리는 OS가 한다.

읽기 쪽 효과:

```text
t=0  프로듀서가 msg 쓰기 → 페이지 캐시에 올라감 (아직 디스크엔 없음)
t=1  컨슈머가 fetch → 커널: "이 파일 오프셋? 캐시에 있네" → HIT → 디스크 read 없음
t=2  (한참 뒤) flusher가 디스크에 write
```

대가 두 가지. (a) 페이지 캐시에만 있고 flush 전에 전원이 나가면 그 데이터는 날아간다 — Kafka는 이걸 fsync가 아니라 **복제**로 막는다. (b) 컨슈머가 한참 뒤처지면(예: 3시간 전 데이터) 캐시에서 밀려나 실제 디스크 read가 생기고 성능이 확 떨어진다. consumer lag을 모니터링하는 이유가 이것이다.

### ③ Zero-copy (sendfile)

2절 그대로. 조건이 하나 있다 — **TLS를 켜면 쓸 수 없다.** 암호화는 사용자 공간(JVM)에서 해야 하므로 데이터가 다시 JVM을 지난다. 보안과 zero-copy는 맞바꿈 관계다.

### ④ 배치 + 압축

메시지 1건마다 네트워크 왕복 + 디스크 write를 하면 순차 I/O의 이점이 사라진다. 프로듀서가 버퍼에 모았다가(`linger.ms`, `batch.size`) 수천 건을 하나의 큰 배치로 보내야 "한 번의 큰 순차 write"가 된다. 압축(gzip/snappy/lz4/zstd)도 배치 단위라 비슷한 메시지가 모일수록 압축률이 좋아진다. 큰 단위 쓰기는 SSD의 RMW도 피한다.

## 4. 용어 — 데이터 모델이 패턴을 강제한다

### 브로커 · 클러스터 · 컨트롤러

브로커 = Kafka 서버 프로세스 한 대. 프로듀서가 보낸 메시지를 로컬 디스크에 로그로 기록하고, 컨슈머의 fetch에 그 로그를 읽어 보내고, 파티션의 리더/팔로워 역할로 복제를 수행한다. 여러 브로커가 모여 클러스터를 이룬다("단일 브로커로 초당 100만 건" = 서버 한 대의 처리량).

컨트롤러는 클러스터의 조율자다 — 어느 브로커가 어느 파티션의 리더인지 관리, 브로커 사망 감지와 새 리더 선출, 파티션 재할당. 예전엔 이 메타데이터를 ZooKeeper에 뒀지만 Kafka 3.x부터 KRaft 모드로 Kafka 자체가 Raft로 관리한다. 이 메타데이터도 내부 토픽의 append-only 로그로 저장한다 — 자기 설계 철학을 메타데이터에도 적용한 것이다.

디스크의 "클러스터"(섹터 묶음)와 직접 관계는 없지만 발상은 같다: 물리적으로 여럿을 논리적으로 하나로 다룬다.

### 토픽 · 파티션 · offset · 세그먼트

파티션은 토픽을 물리적으로 쪼갠 단위이자 **append-only 로그 파일의 실체**다.

```text
Topic: orders
├── Partition 0 : [0][1][2][3][4]        ← 각각 독립된 로그 파일
├── Partition 1 : [0][1][2]
└── Partition 2 : [0][1][2][3][4][5][6]
```

파티션이 존재하는 이유 세 가지:

1. **병렬성** — 파티션마다 다른 브로커에 배치되므로 쓰기·읽기가 여러 서버로 분산된다. 토픽 처리량 = 파티션 수 × 파티션당 처리량.
2. **순서 보장의 단위** — Kafka는 토픽 전체가 아니라 파티션 안에서만 순서를 보장한다. 프로듀서가 key를 주면 `hash(key) % 파티션 수`로 배정되어 같은 key는 항상 같은 파티션으로 간다(user_id를 key로 쓰면 한 사용자의 이벤트는 순서 보장).
3. **확장 단위** — 브로커를 늘렸을 때 옮길 수 있는 최소 단위.

주의: 파티션은 늘릴 수는 있어도 줄일 수 없고, 늘리면 `hash % N`의 N이 바뀌어 기존 key의 배정이 깨진다. 순서가 중요한 시스템에서 파티션 수 증가는 위험한 작업이다.

offset은 파티션 안에서 메시지마다 부여되는 단조 증가 정수다. **파티션 안에서만 유효하다** — P0의 offset 3과 P1의 offset 3은 아무 관계가 없다.

```text
partition-0:  [0][1][2][3][4][5][6][7][8]
                          ↑        ↑
                    consumer A   consumer B
```

브로커는 컨슈머가 어디까지 읽었는지 신경 쓰지 않는다. 읽은 위치는 컨슈머가 관리하고 "5번부터 주세요"라고 요청만 한다. 그래서 (a) 읽었다고 지우지 않아도 되고 → append-only가 성립하고, (b) 여러 컨슈머가 같은 데이터를 각자 속도로 읽을 수 있고, (c) replay는 offset을 뒤로 돌리는 것뿐이고, (d) 브로커는 상태 없이 파일 오프셋만 읽으면 되므로 sendfile이 가능하다. offset이 순서대로 증가한다 = 읽기도 파일을 앞에서 뒤로 훑는 순차 읽기다.

### 프로듀서

메시지를 브로커에 보내는 클라이언트. 직렬화(객체 → 바이트), 파티셔닝(어느 파티션으로), 배칭, 압축, 재시도/ack 대기를 한다. 배칭이 성능의 핵심이다(3-④).

`acks`가 내구성과 속도의 트레이드오프를 결정한다:

```text
acks=0    보내고 잊는다          가장 빠름, 유실 가능
acks=1    리더가 받으면 OK       중간, 리더가 죽으면 유실 가능
acks=all  ISR 전체가 받아야 OK   가장 안전, 느림
```

### 컨슈머 · 컨슈머 그룹

브로커에서 메시지를 읽어가는 클라이언트. push가 아니라 **pull**이다 — "offset 500부터 최대 1MB 주세요"라고 당겨온다. pull을 택한 이유: 컨슈머가 감당 가능한 속도로만 가져가므로 backpressure가 자동이고, 배치 fetch가 자연스럽고, 브로커가 컨슈머 상태를 몰라도 되어 단순해진다.

같은 `group.id`를 공유하는 컨슈머들은 하나의 논리적 소비자가 된다.

```text
Topic: orders (파티션 3개)
  P0 ──┐
  P1 ──┼── Consumer Group "billing"     ├─ A → P0, B → P1, C → P2  (병렬)
  P2 ──┘
  같은 P0~P2 ── Consumer Group "analytics"  (독립적으로 전체를 또 읽음)
```

규칙: 하나의 파티션은 그룹 내에서 단 하나의 컨슈머에게만 할당된다(그래서 파티션 순서가 유지된다). 따라서 그룹의 병렬성 상한 = 파티션 수 — 파티션 3개에 컨슈머 5개면 2개는 논다. 컨슈머가 죽거나 추가되면 리밸런싱으로 재분배한다. 그룹이 다르면 서로 완전히 독립이다.

### 리더 · 팔로워 · ISR

파티션은 장애 대비로 여러 브로커에 복제된다(replica). 하나가 리더, 나머지가 팔로워다.

```text
replication.factor = 3
           Broker 1        Broker 2        Broker 3
P0        [Leader]        (Follower)      (Follower)
P1       (Follower)        [Leader]       (Follower)
P2       (Follower)       (Follower)       [Leader]
```

리더가 해당 파티션의 모든 읽기/쓰기를 단독 처리하고, 프로듀서와 컨슈머는 리더하고만 통신한다(KIP-392로 가까운 팔로워에서 읽는 옵션은 생겼지만 기본은 리더 전용). 팔로워는 클라이언트 요청을 받지 않고 리더의 로그를 복사만 하는데, **컨슈머처럼 리더에게 fetch 요청을 보내 당겨온다** — 복제 로직과 소비 로직이 같은 메커니즘이다. 리더가 파티션마다 다른 브로커에 흩어져 있어야 모든 브로커가 골고루 일한다.

ISR(In-Sync Replicas) = 리더를 충분히 따라잡고 있는 replica 집합. 팔로워가 `replica.lag.time.max.ms`보다 뒤처지면 ISR에서 빠진다.

- `acks=all`은 "전체 replica"가 아니라 "ISR 전원이 받았을 때 OK"다.
- 새 리더는 ISR 안에서만 뽑는다. 뒤처진 replica를 리더로 만들면 데이터가 유실되기 때문이다.
- `min.insync.replicas`로 "ISR이 이 수보다 적으면 쓰기를 거부"하게 만들 수 있다.

이 복제가 fsync를 대신한다 — 페이지 캐시에만 있는 데이터도 다른 브로커에 복사본이 있으니 한 대는 죽어도 괜찮다는 논리다.

### 전체 그림

```text
Producer ──(key로 파티션 결정, 배치+압축)──> Leader Partition
                                                │
                                    ┌───────────┴───────────┐
                                    ↓                       ↓
                              Follower(fetch)        Follower(fetch)
                                    │
Consumer Group <──(offset 지정 fetch, sendfile)──────┘
```

```text
파티션 = append-only 로그 파일   → 순차 I/O 강제
offset = 컨슈머가 위치 관리      → 브로커는 상태 없이 파일 오프셋만 읽음 → sendfile 가능
배치 전송                        → 큰 단위 순차 write, 압축 효율
복제                             → fsync 없이 내구성 → 페이지 캐시에 맡기고 빠르게 응답
```

"빠르다"의 비결은 어느 한 트릭이 아니라, 데이터 모델(파티션·offset·append) 자체가 디스크가 잘하는 패턴을 강제하도록 설계된 것이다.

## 5. 전제가 흔들리는 곳 — 저장 매체가 바뀌면 답도 바뀐다

Kafka의 설계는 "sequential은 random보다 압도적으로 빠르다"는 HDD 시대 가정 위에 서 있다. NVMe에서는 random read ~10 µs, 1M+ IOPS로 격차가 좁혀진다. 그래서 다른 답들이 나왔다.

```text
Pulsar + BookKeeper   서빙(stateless Broker)과 저장(Bookie)을 분리. 하나의 ledger를 여러 Bookie에
                      stripe해 디스크 여러 대의 대역폭을 합산. Journal(쓰기) / Ledger(읽기) 디스크 분리로
                      뒤처진 컨슈머의 읽기가 쓰기를 방해하지 않음. 대가 = Broker+BookKeeper+ZooKeeper 운영 복잡도. (→ striping)
Redpanda              Kafka API 호환, C++ 재작성, 페이지 캐시를 버리고 Direct I/O + thread-per-core.
                      "OS에 맡기지 말고 NVMe에 맞춰 직접 스케줄링하자" — 정반대 철학
Kafka Tiered Storage  최근 데이터는 로컬, 오래된 데이터는 S3로 자동 이관. Kafka 자체의 진화 방향
WarpStream / AutoMQ   로컬 디스크 없이 S3에 직접. 지연시간을 포기하고 비용·운영 편의를 극한으로
LSM-Tree              랜덤 쓰기를 메모리에 모아 순차 쓰기로 변환. 목표(순차화)는 같고 방법이 다름 (→ lsm-tree)
Chronicle Queue       mmap 기반, syscall 자체를 제거. 나노초 단위 지연 목표
```

- HDD 시대 → "무조건 순차로 만들어라" (Kafka)
- NVMe 시대 → "랜덤도 빠르니 병렬성과 코어 활용을 최적화하라" (Redpanda)
- 클라우드 시대 → "지연시간보다 비용이 중요하니 오브젝트 스토리지로" (WarpStream)

원칙은 같고("가진 저장소가 가장 잘하는 패턴 위에 세운다"), 저장소가 달라서 답이 다르게 나온 것이다.

세 설계의 교훈을 한 줄씩: LSM-Tree는 디스크가 싫어하는 랜덤 쓰기를 메모리에서 모아 순차로 **변환**하고, Striping은 디스크 한 대의 한계를 여러 대로 **분산**해 넘고, Kafka는 변환도 분산도 필요 없는 데이터 모델(append-only 로그)을 **설계**해 디스크가 잘하는 패턴만 쓰게 한다.

## 핵심 문장

- 디스크가 느리다는 건 random access 기준이다. Kafka는 디스크가 못하는 걸 강요하지 않았기 때문에 디스크 기반인데도 빠르다.
- 일반 앱은 Page Cache → JVM → Socket Buffer로 CPU 복사 2회를 치르고, Kafka는 sendfile로 페이지 캐시를 소켓에 연결해 JVM을 데이터 경로에서 뺀다. 브로커가 메시지를 해석하지 않기 때문에 가능하다.
- 컨슈머가 따라붙으면 읽기는 페이지 캐시 히트라 디스크를 안 탄다. lag이 커지면 이 전제가 깨진다.
- 빠름의 비결은 트릭이 아니라 데이터 모델이다 — 파티션 = 로그 파일, offset = 컨슈머 소유의 파일 위치, 수정 API 없음.
- 내구성은 fsync가 아니라 복제(ISR, acks=all)로 산다. zero-copy는 TLS와 맞바꿈이다.
- 저장 매체가 바뀌면 최적 패턴도 바뀐다. 원칙은 같고 답이 다르다.

## 관련 자료

- 따라 친 원본 노트(직접 작성): `/home/jun/project/db-engine-lab/docs/study/kafka.md`
- zero-copy 경로 다이어그램: 2026-08-20 대화에서 추가한 원고
- 분리한 내용: SSD 내부(FTL·매핑 granularity·RMW·GC·WAF) → [nand-flash](../nand-flash/) · BookKeeper striping → [striping](../striping/) · LSM → [lsm-tree](../lsm-tree/)
