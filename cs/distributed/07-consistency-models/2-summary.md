# distributed/07-consistency-models — 일관성 모델: 선형화·순차·인과·최종 일관성, 세션 보장 — 정리 (힌트)

## 해결하는 문제

복제·캐시가 생기면 "읽으면 무엇이 나와야 하나"가 더 이상 자명하지 않다(06번).\
이것을 정해 두지 않으면 앱이 무엇을 믿어도 되는지 모른다.

6.5840 L8의 예
```text
  생산자:  put("result", 27);  put("done", true)
  소비자:  while (get("done") == false) wait;   v = get("result")
  v는 27인가?
```
- 한 대짜리 서버라면 당연히 27이다.
- 복제본에서 읽으면 `done=true`는 보이는데 `result`는 아직 옛 값일 수 있다. 저장소가 무엇을 약속하는지에 달렸다.
  - *일관성 모델(consistency model)*: 여러 클라이언트가 동시에 읽고 쓸 때 **어떤 결과가 허용되는가**를 정한 명세. 저장소와 앱 사이의 계약이다(6.5840 L8).

쉬운 예: 게시판.
- 내가 글을 쓰고 새로고침했는데 내 글이 없다.
- 친구는 내 글을 봤는데 나는 못 본다.
- 댓글이 원글보다 먼저 보인다.
모두 "허용되느냐"가 일관성 모델의 질문이다.

실무 예
- 최종 일관성 저장소에 쓰고 바로 읽었더니 옛 값이 나온다.
- "남은 쿠폰 수"를 복제본에서 읽고 발급했더니 한도를 넘어 발급했다.
- etcd 3.6의 `--consistency=s` 읽기, ZooKeeper의 `sync()`가 왜 따로 있나.

## 동작·원리

### 1. 히스토리 — 클라이언트가 본 것만으로 판정한다

```text
  실시간 →
  C1: |--W(x,1)--|   |--W(x,2)--|
  C2:       |------R(x)→2------|
  C3:         |--R(x)→1--|
  |- : 요청 보낸 시각,  -| : 응답 받은 시각
```

- *히스토리(history)*: 연산마다 시작·끝 시각과 인자·결과를 적은 기록. 일관성 모델은 히스토리가 허용되는지로 정의한다(6.5840 L8).
- 서버 안에서 실제로 어떻게 실행했는지는 따지지 않는다. 밖에서 본 결과만 본다.

### 2. 선형화(linearizability) — "한 대처럼, 실시간 순서대로"

```text
  각 연산의 시작~끝 사이 어딘가에 점(•) 하나를 찍는다
  C1: |--W1-•-|   |-•-W2----|
  C2:       |-------------•-R2-|
  C3:         |--•R1--|
  점 순서: W1 → R1 → W2 → R2   — 한 대짜리 레지스터로 돌려도 같은 결과 → 선형화 가능
```

- 정의: 연산마다 시작과 끝 사이의 한 점을 골라, 그 점 순서로 한 대에서 차례로 실행한 결과와 같으면 선형화 가능하다(Herlihy–Wing 1990, 6.5840 L8).
  - Herlihy–Wing 원문: 연산이 호출과 응답 사이 어느 한 순간에 **즉시** 일어나는 것처럼 보이게 한다.
- 결과로 생기는 규칙
  - 쓰기가 **끝난 뒤** 시작한 읽기는 그 값이나 더 나중 값을 본다. 옛 값 금지.
  - 어떤 읽기가 새 값을 봤으면, 그 읽기가 끝난 뒤 시작한 읽기도 새 값 이상을 본다.
- 선형화는 객체 하나(키 하나)에 대한 성질이다. 여러 키를 묶는 트랜잭션은 다루지 않는다. 대신 *지역성(locality)*이 있다. 객체마다 선형화 가능하면 시스템 전체도 선형화 가능하다(Herlihy–Wing 1990).
  - *직렬 가능성(serializability)*: 트랜잭션들이 어떤 직렬 순서로 실행한 것과 같은 결과. **실시간 순서는 요구하지 않는다.** 둘을 합친 것이 *strict serializability*다. etcd 3.6 문서는 KV API가 strict serializability를 보장한다고 적는다. 단 이것은 기본(선형화) 요청 기준이다. 같은 문서는 읽기를 serializable로 바꾸면 옛 데이터를 볼 수 있다고 적는다(아래 실험의 v1).

### 3. 순차 일관성 — 순서는 하나, 실시간은 안 지켜도 됨

```text
  C1: |--W(x,1)--|
  C2:               |--R(x)→0--|        ← 쓰기가 끝난 "뒤"에 시작했는데 옛 값
  선형화: ✘ (R을 W 뒤에 둬야 하는데 그러면 1이어야 함)
  순차:   ✔ (직렬 순서 R→0, W(1)도 각 프로세스 순서를 어기지 않는다)
```

- 정의: 모든 연산이 어떤 **하나의 전체 순서**로 일어난 것처럼 보이고, 그 순서가 프로세스마다의 프로그램 순서를 지킨다(Lamport 1979, Jepsen "Sequential Consistency").
- 실시간 조건이 없다. 그래서 어떤 프로세스는 한참 옛 상태를 읽을 수 있다. 다만 한 번 본 것보다 뒤로 가지는 않는다(Jepsen).
- ZooKeeper 3.9 문서의 보장: 한 클라이언트의 갱신은 보낸 순서로 적용(Sequential Consistency), 서버를 바꿔도 더 옛날 상태를 보지 않음(Single System Image). 그리고 **두 클라이언트가 같은 순간 같은 값을 본다는 보장은 없다**고 따로 적는다. A가 `/a`를 1로 바꾼 뒤 B에게 읽으라고 알려도 B는 0을 읽을 수 있다. 같아야 하면 B가 읽기 전에 `sync()`를 부르는 것이 흔한 방법이다. 단 ZooKeeper 3.9.3 Internals 문서는 `sync`가 정족수 연산이 아니라서, 두 서버가 동시에 자기가 리더라고 믿는 드문 경우엔 `sync` 뒤 읽기도 옛 값일 수 있다고 적는다. 엄밀한 선형화가 필요하면 읽기 전에 쓰기 같은 실제 정족수 연산을 한다.

### 4. 인과 일관성 — 원인이 결과보다 먼저

```text
  A: "점심 먹을래?" ──▶ B: "응"     C: "아니"
  허용:  A가 보는 순서 [점심?, 응, 아니]   B가 보는 순서 [점심?, 아니, 응]   (응·아니는 동시 → 순서 자유)
  금지:  누구든 [응, 점심?]                (답이 질문보다 먼저)
```

- 정의: 인과 관계가 있는 연산은 모든 프로세스에서 같은 순서로 보인다. 인과 관계가 없는(동시) 연산은 프로세스마다 다른 순서로 보여도 된다(Jepsen "Causal Consistency").
  - *인과 관계*: 램포트의 happens-before. 같은 프로세스의 앞 연산, 또는 메시지로 결과를 볼 수 있었던 다른 프로세스의 연산(05번).
- 분할 중에도 같은 서버에 붙어 있는 클라이언트는 계속 진행할 수 있다(Jepsen의 *sticky available*). 그래서 "가용성을 지키며 얻을 수 있는 강한 쪽 모델"로 자주 거론된다.

### 5. 최종 일관성 — 쓰기가 멈추면 언젠가 같아진다

- 정의(약속의 전부): 새 쓰기가 멈추면 복제본들은 결국 같은 값으로 수렴한다.
- **그 사이 읽기에 대해서는 아무것도 약속하지 않는다.** 옛 값, 순서가 뒤바뀐 쓰기, 클라이언트마다 다른 값이 모두 허용된다(6.5840 L8의 eventual consistency 목록).
- 대신 가장 가까운 복제본 하나로 읽고 쓸 수 있어 빠르고 가용성이 높다. Dynamo, Cassandra가 이쪽이다(6.5840 L8).

### 6. 세션 보장 — 최종 일관성 위에 얹는 "내 눈에는 말이 되게"

```text
  read-your-writes     나: W(x,1) → R(x)  … 읽는 복제본에 W(x,1)이 반영돼 있음   (내가 쓴 것은 내가 본다)
  monotonic reads      나: R(x)→1 → R(x)  … 첫 읽기가 본 쓰기들이 반영돼 있음    (본 것보다 옛것으로 안 돌아감)
  writes-follow-reads  나: R(x)→1 → W(y)  … y를 보는 곳은 x=1도 봄
  monotonic writes     나: W(x,1) → W(x,2) … 모두가 1 다음 2 순서로 적용
```

- Terry 외 1994가 이름 붙인 네 가지다. 기준은 **세션(한 클라이언트)** 의 연산이다. 다른 클라이언트의 쓰기를 보라는 약속은 없다(Jepsen "Read Your Writes").
- 보장 대상은 값의 크기가 아니라 "앞서 쓰거나 본 쓰기가 반영됐나"다. 그 사이 남이 x=0을 썼다면 다음 읽기가 0이어도 위반이 아니다(Terry 외 §3.1).
- RYW·MR은 세션 자신의 읽기를 제약한다. WFR·MW는 세션이 만든 쓰기의 순서를 **모든 복제본에서** 제약하므로, 세션 밖 클라이언트가 보는 순서에도 영향을 준다(Terry 외 §3.3·§3.4).
- 구현 방법: 세션이 "내가 마지막으로 쓰거나 본 버전"을 들고 다니고, 그보다 옛 복제본에서는 읽지 않는다.

### 7. 강도 지도

```text
  강함  strict serializability (선형화 + 직렬 가능, 여러 키 트랜잭션)
          │
        선형화 ───────── 실시간 순서까지
          │
        순차 일관성 ──── 전체 순서 하나, 실시간 X
          │
        인과 일관성 ──── 인과 순서만
          │
        세션 보장(RYW, MR, WFR, MW) ── 한 클라이언트 시점
          │
  약함  최종 일관성 ──── 수렴만
```

- 아래로 갈수록 기다릴 일이 적어 빠르고, 분할 중에도 응답하기 쉽다. 위로 갈수록 앱이 생각하기 쉽다.
- 위쪽 둘(선형화·순차)은 네트워크 분할 중에 일부 노드가 진행하지 못한다(Jepsen, 08번).

### 실험: 히스토리 판정기 — 선형화와 순차 일관성의 차이

- 환경: Java 21, 연산 몇 개짜리 히스토리를 전수 탐색으로 판정. 선형화는 "실시간 순서 + 레지스터 규칙", 순차는 "프로세스 순서 + 레지스터 규칙"을 지키는 직렬 순서를 찾는다. 결정적이다.

```java
// LinCheck.java 핵심: 다음에 놓을 연산 c를 고를 때의 제약
for (Op o : 아직 안 놓은 연산들) {
    if (realTime && o.end() < c.start()) ok = false;                     // 먼저 끝난 연산을 건너뛸 수 없다(선형화만)
    if (o.proc().equals(c.proc()) && o.start() < c.start()) ok = false; // 같은 프로세스 순서(둘 다)
}
```

(실험, Java 21 판정기, 2026-10-01)

```text
L8 예1                              선형화 예   [C1:Wx1, C3:Rx1, C1:Wx2, C2:Rx2] | 순차 예   [C1:Wx1, C3:Rx1, C1:Wx2, C2:Rx2]
L8 예3                              선형화 아니오  | 순차 예   [C1:Wx1, C3:Rx1, C1:Wx2, C2:Rx2]
쓰기 끝난 뒤 다른 클라이언트가 옛 값              선형화 아니오  | 순차 예   [C2:Rx0, C1:Wx1]
자기 쓰기 뒤 옛 값                        선형화 아니오  | 순차 아니오 
1을 본 뒤 0을 봄(단조 읽기 위반)              선형화 아니오  | 순차 아니오
```

- "L8 예3"은 Rx2가 끝난 뒤 시작한 Rx1이 옛 값을 봤다. 실시간 순서를 지키면 불가능 → 선형화 아님. 실시간을 무시하면 가능 → 순차 일관.
- "다른 클라이언트가 옛 값"은 복제본 읽기에서 흔한 모습이다. 순차 일관성은 허용하고 선형화는 금지한다.
- "자기 쓰기 뒤 옛 값", "1을 본 뒤 0"은 순차 일관성조차 깬다. 각각 read-your-writes·monotonic reads 위반이다.

### 실험: etcd 3.6.5 — 선형화 읽기와 직렬화 읽기

- etcd 3.6 문서: 기본은 선형화다. 읽기의 consistency를 serializable로 바꾸면 Raft 합의를 거치지 않아 빠르지만 "정족수 기준으로 오래된 데이터"를 볼 수 있다(API guarantees).
- 환경: 일회용 etcd 3.6.5 3노드(`sn-dw-w06-etcd1·2·3`). 팔로워 etcd3을 Docker 네트워크에서 떼어 낸 뒤, 다수 쪽에 v2를 쓰고 etcd3에서 두 방식으로 읽었다.

(실험, etcd 3.6.5 3노드, 2026-10-01)

```text
분할 전 etcd3 직렬화 읽기: v1
--- etcd3 분리 ---
다수 쪽(etcd1) put v2 → 성공
다수 쪽(etcd1) 선형화 읽기: v2
소수 쪽(etcd3) 직렬화 읽기(--consistency=s): v1  [89ms]
소수 쪽(etcd3) 선형화 읽기(기본): Error: context deadline exceeded  [3097ms]
소수 쪽(etcd3) put v3: Error: context deadline exceeded  [3086ms]
--- 재연결 ---
재연결 5초 뒤 etcd3 선형화 읽기: v2
```

- 직렬화 읽기는 바로 답했지만 이미 덮어쓴 v1이었다. 선형화 읽기는 옛 값을 주느니 실패했다(`--command-timeout=3s`).
- 같은 구성의 첫 일회용 클러스터에서 네트워크를 잘못 바꿔 노드끼리 끊긴 적이 있다(다시 만들어 실험했다). 그때 etcd 로그에 `timed out waiting for read index response (local node might have slow network)`(caller `etcdserver/v3_server.go`)가 찍혔다. 선형화 읽기는 리더에게 "현재 커밋 위치(ReadIndex)"를 확인받은 뒤 답한다. 리더와 못 닿으면 답할 수 없다.

### 실험: Redis 7.4.9 비동기 복제 — 쓰고 바로 읽기, 그리고 쿠폰 과발급

- 06번 실험과 같은 실행이다(리더 1 + 복제본 1, 복제 링크 50ms 지연 프록시). 쓰고 바로 복제본에서 읽으면 300번 중 300번 옛 값이었다(06번).
- 여기에 쿠폰 한도 300을 두고 작업자 4개가 400번씩 시도했다. 남은 수량을 어디서 어떻게 읽느냐만 바꿨다.

```java
// follower-read / leader-read: 읽고 판단한 뒤 INCR
Object v = (mode.equals("follower-read") ? f : p).cmd("GET", "w06:issued");
long cur = v == null ? 0 : Long.parseLong((String) v);
if (cur < limit) { p.cmd("INCR", "w06:issued"); granted.incrementAndGet(); }
// leader-atomic: 리더에서 INCR 한 번으로 판단
long after = (Long) p.cmd("INCR", "w06:issued");
if (after <= limit) granted.incrementAndGet(); else p.cmd("DECR", "w06:issued");
```

(실험, Redis 7.4.9 리더 1 + 복제본 1, 2026-10-01)

```text
== 직결(지연 프록시 없음) ==
[4] follower-read  한도 300, 발급 302 (초과 2)
[4] leader-read    한도 300, 발급 302 (초과 2)
[4] leader-atomic  한도 300, 발급 300 (초과 0)
== 복제 링크 50ms 지연 프록시 ==
[4] follower-read  한도 300, 발급 1313 (초과 1013)
[4] leader-read    한도 300, 발급 301 (초과 1)
[4] leader-atomic  한도 300, 발급 300 (초과 0)
```

- 복제본 읽기 + 지연 50ms에서 1013장을 더 발급했다. 복제본은 50ms 전 숫자를 보여 주고, 그동안 작업자들은 계속 "아직 남았다"고 판단했다.
- 리더에서 읽어도 "읽고-판단-쓰기"가 원자적이지 않아 초과가 날 수 있었다(이 실행 1~2장, 재실행에서는 0~1장). 선형화된 저장소라도 **두 연산 사이**는 보호하지 않는다.
- 리더에서 `INCR` 결과로 판단하면 0장이었다. 발급 여부를 `INCR` 한 번의 반환값으로 정하기 때문이다.
  - 다만 초과분을 되돌리는 `DECR`은 별도 연산이다. 그 사이 카운터는 잠깐 한도를 넘고, `DECR` 전에 클라이언트가 죽으면 증가분이 남는다(과발급이 아니라 덜 발급하는 쪽). 카운터까지 정확히 하려면 확인과 갱신을 Lua 스크립트·함수 하나로 묶는다(Redis 스크립트는 원자 실행).
- 초과 수는 실행마다 크게 다르다(같은 조건 다른 실행 1166장, 사실 점검 재실행 410·416장). "복제본 읽기 ≫ 리더 읽기 > 원자 연산(0)"이라는 경향은 같았다.

## 쓰이는 자료구조·알고리즘

- **히스토리 + 선형화 검사(탐색)** — 연산들의 가능한 직렬 순서를 백트래킹으로 찾는다. 경우의 수가 연산 수에 따라 지수적으로 늘어 이 판정기는 연산 몇 개짜리만 다룬다. [algorithm/13-backtracking](../../algorithm/13-backtracking/2-summary.md)
- **ReadIndex** — etcd 선형화 읽기의 길. 리더가 아직 리더인지 확인하고 그 시점 커밋 위치까지 적용한 뒤 답한다(로그 메시지로 존재 확인, 상세는 11번 consensus-raft).
- **벡터 시계·버전 토큰** — 인과 일관성과 세션 보장의 재료. "내가 본 마지막 버전"을 들고 다닌다. [05-logical-clocks](../05-logical-clocks/2-summary.md)
- **단일 연산 원자 갱신(fetch-and-add, CAS)** — 카운터를 "읽고 쓰기" 두 연산이 아니라 하나로 만든다. Redis `INCR`, etcd `Txn`의 compare.

## 적용 — 풀어나가는 법

### 1. 연산마다 필요한 모델을 적는다

| 연산 | 필요한 보장 | 이유 |
|---|---|---|
| 재고·쿠폰 차감, 유일 아이디 등록 | 확인과 갱신을 묶은 조건부 원자 연산(CAS 등). 선형화된 읽기+쓰기 두 번으로는 부족 | 옛 값이나 끼어든 요청으로 판단하면 초과·중복 |
| 리더 선출·락 | 선형화 | 두 명이 리더가 되면 안 된다(DDIA 9장 "Relying on Linearizability") |
| 내 프로필 수정 후 보기 | read-your-writes | 남의 수정은 조금 늦어도 된다 |
| 피드·댓글 | 인과(최소한 consistent prefix) | 답이 질문보다 먼저 보이면 안 된다 |
| 조회수·추천 목록 | 최종 일관성 | 조금 틀려도 된다 |

### 2. 제품의 기본값과 선택지를 확인한다

```bash
# etcd 3.6: 기본 선형화 읽기, -consistency=s 는 직렬화(로컬) 읽기
etcdctl get /config/flag                    # 선형화
etcdctl get /config/flag --consistency=s    # 빠르지만 옛 값 가능
# ZooKeeper 3.9: 다른 클라이언트의 최신 쓰기를 봐야 하면 읽기 전에 sync (엄밀한 선형화는 아님)
#   zk.sync("/a", cb, ctx);  이어서 zk.getData("/a", ...)
```

### 3. 세션 보장을 버전 토큰으로 구현한다

```java
// 쓰기 응답의 버전(예: etcd revision, DB LSN)을 세션에 저장하고,
// 읽기는 그 버전 이상 반영한 복제본에서만 한다 → read-your-writes + monotonic reads
public final class Session {
    private volatile long minVersion = 0;
    public void afterWrite(long version) { minVersion = Math.max(minVersion, version); }
    public Replica pickReplica(List<Replica> rs) {
        return rs.stream().filter(r -> r.appliedVersion() >= minVersion)
                 .findAny().orElse(leader);                 // 없으면 리더로
    }
    public void afterRead(long seenVersion) { minVersion = Math.max(minVersion, seenVersion); }
}
```

- etcd 3.6은 기본 읽기가 선형화라 이런 토큰이 필요 없다. 직렬화 읽기를 섞을 때만 응답 헤더의 `revision`(그 멤버가 반영한 저장소 revision)을 세션의 최소 버전과 비교해 뒤처진 응답을 거른다.

### 4. 카운터는 한 연산으로 판단한다

```java
// Redis: 리더에서 INCR 결과로 판단 (실험의 leader-atomic)
long n = redis.incr("coupon:issued");
if (n > LIMIT) { redis.decr("coupon:issued"); throw new SoldOut(); }

// etcd 3.6 + jetcd(Java 클라이언트): compare-and-swap. 읽은 mod_revision이 그대로일 때만 쓴다
var key = ByteSequence.from("/coupon/issued", UTF_8);
var cur = kv.get(key).get();                       // 선형화 읽기
long modRev = cur.getKvs().isEmpty() ? 0 : cur.getKvs().get(0).getModRevision();
long count  = cur.getKvs().isEmpty() ? 0 : Long.parseLong(cur.getKvs().get(0).getValue().toString(UTF_8));
if (count >= LIMIT) throw new SoldOut();
var ok = kv.txn().If(new Cmp(key, Cmp.Op.EQUAL, CmpTarget.modRevision(modRev)))
          .Then(Op.put(key, ByteSequence.from(Long.toString(count + 1), UTF_8), PutOption.DEFAULT))
          .commit().get().isSucceeded();           // false면 다른 누가 먼저 바꿈 → 다시 읽고 재시도
```

## 장애 시나리오와 대처

### 1. 최종 일관성 저장소에서 쓰고 바로 읽기 → 옛 값

- **현상**: 설정을 바꾸고 바로 조회했더니 옛 설정이다. 잠시 뒤에는 새 값이다.
- **보이는 형태**: 복제본(또는 캐시) 읽기 경로에서만 생긴다. 지연이 클 때 빈도가 오른다. 실험에서 지연 50ms면 300번 중 300번.
- **원인**: 저장소는 최종 일관성만 약속했다. "쓰기가 끝났다"가 "어디서 읽어도 보인다"는 뜻이 아니다.
- **대처**: read-your-writes를 구현한다(쓰기 직후 리더 읽기, 버전 토큰). 다른 클라이언트도 바로 봐야 하는 데이터면 선형화 읽기(etcd 기본 읽기)를 쓴다. ZooKeeper `sync` + 읽기는 실무에서 흔히 충분하지만 엄밀한 선형화는 아니다(Internals 문서).

### 2. 선형화를 가정한 분산 카운터 → 과발급

- **현상**: 한도 300장인 쿠폰이 1000장 넘게 나갔다. 재고가 음수가 됐다.
- **보이는 형태**: 에러 없이 성공 응답이 한도보다 많다. 부하가 크거나 복제 지연이 클 때 몰려서 생긴다.
- **원인**: 남은 수량을 복제본·캐시에서 읽었다(옛 값). 리더에서 읽어도 "읽기 → 판단 → 쓰기" 사이에 다른 요청이 끼어든다. 실험에서 복제본 읽기 1013장(실행에 따라 400~1100장대), 리더 읽기 0~2장 초과.
- **대처**: 판단을 쓰기 연산 하나에 넣는다(`INCR` 결과 확인, DB 조건부 `UPDATE ... WHERE remaining > 0`, etcd `Txn` compare). 실험의 leader-atomic은 0장 초과.

### 3. 요청마다 다른 복제본 → 시간이 거꾸로 간다

- **현상**: 새로고침할 때마다 댓글 수가 3 → 2 → 3으로 오락가락한다.
- **보이는 형태**: 로드밸런서가 복제본을 번갈아 고를 때만 생긴다. 판정기 실험의 "1을 본 뒤 0" 히스토리다.
- **원인**: 복제본마다 지연이 다르다. monotonic reads 위반.
- **대처**: 세션을 같은 복제본에 고정하거나, 세션이 본 최소 버전 이상인 복제본만 고른다.

### 4. 다른 채널로 알렸더니 아직 없다

- **현상**: 이미지 업로드 후 큐에 "썸네일 만들어"를 넣었는데, 작업자가 이미지를 읽으니 없다.
- **보이는 형태**: 작업자 쪽 `not found`가 간헐적으로 난다. 재시도하면 된다.
- **원인**: 저장소 복제와 큐 전달이 다른 경로다. 큐 메시지가 복제보다 먼저 도착했다. 선형화가 아니면 "쓰기가 끝난 뒤"가 다른 경로의 읽기를 보장하지 않는다(DDIA 9장 "Cross-channel timing dependencies").
- **대처**: 메시지에 버전을 담아 그 버전 이상을 읽을 때까지 기다리게 하거나, 그 읽기만 선형화 경로(리더)로 한다.

## 핵심 문장

- 일관성 모델은 "동시에 읽고 쓸 때 어떤 결과가 허용되나"를 정한 저장소와 앱 사이의 계약이다.
- 선형화는 한 대처럼, 실시간 순서까지 지킨다. 쓰기가 끝난 뒤 시작한 읽기는 옛 값을 볼 수 없다.
- 순차 일관성은 전체 순서는 하나지만 실시간을 안 지킨다. 그래서 다른 클라이언트의 끝난 쓰기를 못 볼 수 있다.
- 최종 일관성은 수렴만 약속한다. 세션 보장(RYW·단조 읽기 등)을 위에 얹어 한 사용자의 눈에는 말이 되게 한다.
- 선형화된 저장소도 두 연산 사이는 보호하지 않는다. 판단은 원자 연산 하나 안에 넣는다.

## 관련 주제·근거

- 선행
  - [06-replication-strategies](../06-replication-strategies/2-summary.md) — 복제 지연이 이 노트의 이상 현상을 만든다
  - [database/32-replication-leader-follower](../../database/32-replication-leader-follower/2-summary.md) §4 — 복제 지연의 세 이상 현상(RYW·단조 읽기·consistent prefix)
- 후속·연결
  - [08-cap-and-pacelc](../08-cap-and-pacelc/2-summary.md) — CAP의 C = 선형화, 분할 시의 선택
  - [09-quorums](../09-quorums/2-summary.md) — R+W>N이어도 선형화가 아닌 이유
  - [05-logical-clocks](../05-logical-clocks/2-summary.md) — happens-before, 벡터 시계
  - [11-consensus-raft](../11-consensus-raft/2-summary.md) — 선형화를 구현하는 합의 · [12-coordination-and-fencing](../12-coordination-and-fencing/2-summary.md)
  - [database/14-isolation-levels-and-anomalies](../../database/14-isolation-levels-and-anomalies/2-summary.md) — 트랜잭션 격리(직렬 가능성)와의 구분
- 강의·교재·논문
  - MIT 6.5840 Spring 2026 L8 "Consistency and Linearizability" 노트 — 히스토리, 선형화 정의와 예 1~6, 최종 일관성의 이상 목록 <https://pdos.csail.mit.edu/6.824/notes/l-linearizability.txt>
  - Herlihy, Wing, "Linearizability: A Correctness Condition for Concurrent Objects", TOPLAS 1990 — 정의, 지역성·비차단 성질 <https://cs.brown.edu/~mph/HerlihyW90/p463-herlihy.pdf>
  - Terry 외, "Session Guarantees for Weakly Consistent Replicated Data", PDIS 1994 — RYW·MR·WFR·MW(§3.1~3.4, WFR·MW는 세션 밖에도 영향)
  - DDIA 1판 9장 Consistency and Consensus — Linearizability, Relying on Linearizability(락·유일성 제약·cross-channel), Ordering Guarantees · 5장 Problems with Replication Lag
  - Jepsen Consistency Models — Linearizable, Sequential(Lamport 1979 정의 인용), Causal(sticky available), Read Your Writes <https://jepsen.io/consistency>
- 제품 문서
  - etcd v3.6 API guarantees — strict serializability, 기본 선형화, serializable 읽기는 옛 데이터 가능 <https://etcd.io/docs/v3.6/learning/api_guarantees/>
  - ZooKeeper 3.9 Programmer's Guide "Consistency Guarantees" — Sequential Consistency, Single System Image, 동시 교차 클라이언트 뷰 미보장, `sync()` <https://zookeeper.apache.org/doc/r3.9.3/zookeeperProgrammers.html> · Internals "Consistency Guarantees" — `sync`는 정족수 연산이 아님, 읽기 전 쓰기로 선형화 <https://zookeeper.apache.org/doc/r3.9.3/zookeeperInternals.html>
  - Kleppmann, "Please stop calling databases CP or AP"(2015) — CAP의 C = 선형화, ZooKeeper 기본 읽기는 선형화 아님
- 실험 목록
  - Java 21 히스토리 판정기: 6.5840 L8 예1·예3, 옛 값 읽기 세 가지의 선형화·순차 판정
  - etcd 3.6.5 일회용 3노드: 팔로워 하나 분리 후 직렬화 읽기(옛 값 v1, 89ms) vs 선형화 읽기·쓰기(3초 타임아웃 실패), 재연결 후 v2
  - Redis 7.4.9 리더 1 + 복제본 1(06번과 같은 실행): 쿠폰 한도 300, 작업자 4 × 400회, 복제본 읽기·리더 읽기·리더 원자 INCR별 발급 수(직결 / 50ms 지연)
