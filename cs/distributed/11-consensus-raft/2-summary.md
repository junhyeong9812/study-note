# distributed/11-consensus-raft — Raft: 선출·로그 복제·안전성·멤버십 변경 — 정리 (힌트)

## 해결하는 문제

서버 한 대가 상태를 들고 있으면 그 한 대가 죽을 때 서비스가 멈춘다.\
여러 대에 복제하면 이번엔 **복제본들이 같은 순서로 같은 명령을 실행하게** 만들어야 한다.

```text
  복제 상태 기계(replicated state machine)
  클라이언트 ─ "x=3" ─> [합의 모듈] ─> 로그: 1:x=1  2:y=2  3:x=3 ─> 상태 기계(KV 저장소)
                          │  같은 로그를 다른 서버에도
                          ├──────────> 로그: 1:x=1  2:y=2  3:x=3 ─> 상태 기계
                          └──────────> 로그: 1:x=1  2:y=2  3:x=3 ─> 상태 기계
  같은 로그 + 결정적 상태 기계 = 같은 상태
```

- *합의(consensus)*: 여러 노드가 하나의 값(여기서는 "로그 i번 칸의 명령")에 동의하고, 한 번 정하면 바꾸지 않는 것.
- *복제 상태 기계*: 같은 시작 상태에서 같은 명령을 같은 순서로 실행하면 같은 결과가 나온다는 성질을 이용한 복제. 합의는 "같은 순서"를 만드는 부분이다.
- Raft는 이 일을 **리더 하나가 로그를 정하고 팔로워에게 복사**하는 방식으로 푼다. 이해하기 쉽게 만드는 것이 설계 목표였다(Ongaro–Ousterhout 2014 1절).

쉬운 예: 회의록이다.
- 서기(리더) 한 명이 안건 순서대로 회의록을 쓰고, 참석자(팔로워)는 받아 적는다.
- 과반이 받아 적었다고 확인한 안건만 "의결"이다.
- 서기가 쓰러지면 새 서기를 뽑는데, **의결된 안건을 다 가진 사람만** 서기가 될 수 있다.

똑같은 구조다.\
실무 예: etcd(Kubernetes의 저장소), Consul 서버, CockroachDB의 범위별 복제(Raft group), TiKV, Kafka KRaft 메타데이터 쿼럼(KIP-595 "A Raft Protocol for the Metadata Quorum")이 Raft나 그 변형을 쓴다고 각 문서가 밝힌다. 제품마다 변형이 있어 세부는 제품 문서로 확인한다. 이 노트의 실험은 etcd 3.6.5(go.etcd.io/raft v3.6.0)로 했다.

## 동작·원리

### 1. 세 역할과 term

```text
           타임아웃, 선거 시작              과반 득표
 ┌────────┐ ─────────────────> ┌─────────┐ ─────────> ┌────────┐
 │follower│                    │candidate│            │ leader │
 └────────┘ <───────────────── └─────────┘            └────────┘
      ^       리더 발견·더 큰 term       │ 타임아웃(표 갈림) → 새 선거     │
      └──────────────────────────────────────────────── 더 큰 term 발견 ┘

 term:  ──[ term 1: 리더 A ]──[ term 2: 리더 B ]──[ term 3: 표 갈림, 리더 없음 ]──[ term 4: 리더 C ]──>
```

- 시간은 term으로 나뉜다. term마다 선거가 있고, 리더가 많아야 하나다(Election Safety).
- 노드는 메시지에서 더 큰 term을 보면 자기 term을 올리고 follower가 된다. 작은 term의 요청은 거절한다(논문 그림 2 "Rules for Servers").
  - etcd raft(go.etcd.io/raft v3.6.0 `Step`)에는 예외가 있다: 높은 term의 PreVote에는 term을 올리지 않고, CheckQuorum으로 리더 소식을 최근에 들었으면 높은 term의 투표 요청을 무시한다.
- 선출 자체와 PreVote·CheckQuorum은 [10-leader-election](../10-leader-election/2-summary.md)에 실험과 함께 있다.

### 2. 로그 복제 — AppendEntries

```text
 index:    1    2    3    4    5
 리더     [1]  [1]  [2]  [3]  [3]      [t] = 그 항목을 만든 term
 팔로워 a [1]  [1]  [2]  [3]  [3]      ← 같다
 팔로워 b [1]  [1]  [2]                ← 뒤처짐: 4·5를 받아야 함
 팔로워 c [1]  [1]  [2]  [2]  [2]      ← 옛 리더에게서 받은, 커밋 안 된 항목이 남음

 리더 → c: AppendEntries(prevLogIndex=3, prevLogTerm=2, entries=[4:t3, 5:t3])
           c의 3번 칸 term이 2로 일치 → 4·5를 지우고 리더 것으로 덮는다
```

- 리더는 새 명령을 자기 로그 끝에 붙이고 `AppendEntries`로 팔로워에게 보낸다. 빈 `AppendEntries`가 하트비트다.
- **일관성 검사**: 요청에 "바로 앞 칸의 index와 term"을 싣는다. 팔로워 로그의 그 칸이 다르면 거절한다. 리더는 `nextIndex`를 하나씩 줄여 다시 보낸다.
- 그래서 **Log Matching**이 선다: 두 로그가 같은 index에 같은 term의 항목을 가지면, 그 칸까지 앞부분이 전부 같다(그림 3).
- 리더는 자기 로그를 지우거나 덮지 않는다(Leader Append-Only). 덮이는 쪽은 팔로워의 충돌 항목뿐이다.

### 3. 커밋 — 과반에 복제되면, 단 "자기 term의 항목"으로

```text
 commitIndex 계산 (5대, 리더 포함)
 matchIndex:   리더=7  a=7  b=6  c=4  d=3   → 정렬하면 7,7,6,4,3 → 과반(3대)이 가진 가장 큰 index = 6
 log[6].term == 현재 term 이면 commitIndex = 6
```

- 과반이 저장한 항목은 **커밋**된다 — 단 바로 아래 함정대로 리더 자신의 term 항목일 때다. 커밋된 항목만 상태 기계에 적용하고 클라이언트에 응답한다.
- 함정(그림 8): 리더는 **이전 term의 항목을 과반 복제 수만 세서 커밋하지 않는다.**
  - 이전 term 항목이 과반에 있어도, 더 최근 term 항목을 가진 노드가 리더가 되어 덮어쓸 수 있다.
  - 자기 term 항목이 과반에 복제되면 그 앞의 항목은 Log Matching 덕분에 함께 커밋된다(5.4.2절).
  - 새 리더가 term 시작에 빈 항목(no-op)을 기록하는 이유가 이것이다(8절). 10번 실험에서 리더가 바뀔 때 raft index가 하나씩 는 것이 그 흔적이다.

### 4. 안전성의 열쇠 — 선거 제한

- 투표자는 **후보의 로그가 자기 것만큼 최신이 아니면** 표를 주지 않는다(5.4.1절).
  - 최신 비교: 마지막 항목의 term이 크면 더 최신. term이 같으면 더 긴 쪽이 더 최신.
- 이 규칙과 "과반 둘은 겹친다"가 합쳐져 **Leader Completeness**가 선다: 커밋된 항목은 이후 모든 리더의 로그에 있다.

```text
  커밋한 과반  {S1, S2, S3}   ← 항목 X를 가짐
  당선한 과반      {S3, S4, S5}  ← 겹치는 S3가 투표자
  S3는 X를 가졌으므로, X가 없는(더 뒤처진) 후보에게는 표를 안 준다
```

### 5. 실험: 과반이 없으면 쓰기도, 선형화 읽기도 거부

3노드 중 2노드를 `docker kill`하고, 남은 e1에 쓰기·읽기를 보냈다. `etcdctl --command-timeout=3s`.

(실험, etcd 3.6.5 3노드 전용 클러스터, 2026-10-01 — 클라이언트 경고 줄은 뺐다)

```text
OK
v1
--- kill e2, e3 at 01:12:15.319
--- put (과반 없음)
Error: context deadline exceeded

real	0m3.075s
--- get 기본(선형화)
Error: context deadline exceeded
--- get --consistency=s(직렬화)
v1
--- e1 상태
http://sn-dw-w10-e1:2379   member=bc22c2e06ef17fae leader=0 term=7 index=440
--- e2 재시작(과반 회복)
OK
v3
--- /w10/x 변경 이력(watch --rev=1, 두 번 실행한 누적)
mod_revision=2 version=1 value=v1
mod_revision=3 version=2 value=v3
mod_revision=407 version=3 value=v1
mod_revision=408 version=4 value=v3
```

- 관찰 1 — 혼자 남은 e1은 리더가 없다(`leader=0`). 쓰기는 타임아웃(3초)까지 기다리다 실패했다. **과반이 없는 쪽은 진행하지 않는다** — 커리큘럼 ⚠ "가용성 저하"가 이것이다.
- 관찰 2 — 기본 읽기도 실패했다. etcd의 기본 읽기는 선형화 읽기라 리더가 과반에게 확인(ReadIndex)해야 한다. etcd는 raft `ReadOnlyOption`을 따로 주지 않아 기본값 `ReadOnlySafe`를 쓴다(go.etcd.io/raft: "communicating with the quorum. It is the default").
- 관찰 3 — `--consistency=s`(직렬화 읽기)는 응답했다. 로컬 상태를 그대로 읽기 때문이다. 이 값은 **오래됐을 수 있다**(etcd API guarantees 문서: "may access stale data with respect to quorum").
- 관찰 4 — 타임아웃 난 `put v2`는 변경 이력 어디에도 없다. 이번에는 적용되지 않았다.
  - 다만 일반적으로 타임아웃은 **결과를 모르는 상태**다. 리더에 도달해 로그에 들어간 뒤 응답만 잃었다면 나중에 커밋될 수 있다. 재시도는 멱등하게 짠다(논문 8절: 클라이언트 일련번호로 중복 제거).

### 6. 멤버십 변경 — 한 번에 바꾸면 과반이 둘 생긴다

```text
 3대 → 5대를 한 번에 바꾸면, 서버마다 새 설정을 보는 시각이 다르다
   옛 설정 {1,2,3}의 과반  = {1,2}       ← 1·2는 아직 옛 설정
   새 설정 {1,2,3,4,5}의 과반 = {3,4,5}  ← 3·4·5는 새 설정
   두 과반이 겹치지 않는다 → 같은 term에 리더 둘이 가능
```

- 논문(6절)의 해법: **joint consensus**. 중간 설정 C(old,new)에서는 결정에 옛 과반과 새 과반을 **둘 다** 요구한다. C(old,new)가 커밋된 뒤 C(new)로 간다.
- 한 번에 **한 대씩만** 바꾸면 옛 과반과 새 과반이 겹친다(3대의 과반 2 + 4대의 과반 3 > 4). etcd 3.6.5 서버의 member add·remove·promote는 `raftpb.ConfChange` 하나로 한 멤버씩 제안한다(`server/etcdserver/server.go`).
- 새 서버는 로그가 비어 있다. 바로 투표 멤버로 넣으면 따라잡는 동안 과반 계산을 흔든다. 논문은 먼저 **비투표 멤버**로 붙여 따라잡게 한다. etcd는 이것을 **learner**로 제공한다.
  - *learner*: 로그를 복제받지만 과반 계산·투표에 들어가지 않는 멤버.

(실험, etcd 3.6.5, 3노드 + e4, 2026-10-01)

```text
--- (1) member add --learner
Member fc759b077d2a466a added as learner to cluster 6c763775e25c1509
--- member list (마지막 열 = IS LEARNER)
73614ce759299fd2, started, e3, http://sn-dw-w10-e3:2380, http://sn-dw-w10-e3:2379, false
bc22c2e06ef17fae, started, e1, http://sn-dw-w10-e1:2380, http://sn-dw-w10-e1:2379, false
d12c53d5e01c4303, started, e2, http://sn-dw-w10-e2:2380, http://sn-dw-w10-e2:2379, false
fc759b077d2a466a, started, e4, http://sn-dw-w10-e4:2380, http://sn-dw-w10-e4:2379, true
--- learner에서 선형화 읽기
Error: etcdserver: rpc not supported for learner
--- learner에서 직렬화 읽기
v200
--- promote
Member fc759b077d2a466a promoted in cluster 6c763775e25c1509
--- 제거
Member fc759b077d2a466a removed from cluster 6c763775e25c1509
--- (2) e3를 죽인 채 투표 멤버 e5 추가
Error: etcdserver: unhealthy cluster
```

(member list 두 번째 출력 등 일부 줄은 줄였다. 전체는 실험 목록의 `out-D.txt`.)

- 관찰 1 — learner는 `IS LEARNER=true`로 붙고, 선형화 읽기는 거부, 직렬화 읽기는 응답했다. 따라잡은 뒤 `promote`로 투표 멤버가 됐다.
- 관찰 2 — e4를 띄우기 전에 promote하면 `can only promote a learner member which is in sync with leader`로 거절된다(같은 날 첫 시도에서 나온 오류 문구).
- 관찰 3 — 한 대가 죽은 상태에서 투표 멤버를 추가하자 `unhealthy cluster`로 거부됐다. `--strict-reconfig-check` 기본 `true`("Reject reconfiguration requests that would cause quorum loss")다.
  - 해석: 추가가 받아들여지면 투표 멤버가 4대(과반 3)가 되는데 살아 있는 것은 2대뿐이라 즉시 과반을 잃는다.
- 관찰 4 — 같은 날 첫 시도에서는 세 대가 다 살아 있을 때 **아직 띄우지 않은** 투표 멤버 e5를 추가하자 받아들여졌다. 이 순간 투표 멤버 4대 중 1대가 unstarted라 **한 대만 더 죽어도 과반을 잃는 상태**였다. learner로 먼저 붙이는 이유다.

### 7. 실험: 선거 타임아웃의 무작위 폭 — 선거 폭풍

선거는 표가 갈리면(split vote) 실패하고 다음 term으로 넘어간다. 모두가 같은 순간에 후보가 되면 계속 갈린다.

이산 사건 시뮬레이션으로 5대 중 리더 1대가 죽은 뒤 새 리더까지의 시간을 쟀다. 메시지 편도 지연 3~7ms(예시), 구간별 1000회.

(실험, Java 21 시뮬레이션 `ElectionSim.java`, 시드 42, 2026-10-01)

```text
타임아웃(ms)   중앙값   p99     최대     평균 라운드  (1000회, 5노드 중 리더 1대 사망)
 150-150      60000    60000    60000   395.19
 150-151      13102    60000    60000   123.64
 150-155        776     3823     6396     6.80
 150-175        171      641      821     1.32
 150-300        192      412      460     1.03
  12-24          43      129      189     2.13
```

- 60000은 시뮬레이션 상한(60초)이다. 무작위 폭이 0이면 60초 안에 리더가 한 번도 서지 않았다.
- 폭 1ms는 아직 나쁘고, 5ms부터 급히 좋아지고, 150–300ms는 평균 1.03라운드로 거의 첫 선거에 끝났다.
- 12–24ms는 빠르지만(중앙값 43ms) 라운드가 2.13으로 늘었다. 왕복(6~14ms)이 타임아웃에 비해 길어 표가 더 자주 갈린다.
- 논문 9.3절 그림 16(5대, broadcast ≈15ms)도 같은 경향이다: 무작위 없으면 "consistently took longer than 10 seconds", 5ms 무작위로 중앙값 287ms, 12–24ms면 평균 35ms(최장 152ms)에 리더가 서지만, 이보다 더 낮추면 타이밍 요건을 어겨 불필요한 리더 교체가 생긴다고 적고, 보수적인 150–300ms를 권한다.
- 그래서 조건은 **broadcastTime ≪ electionTimeout ≪ MTBF**다(5.6절). etcd는 이를 "선거 타임아웃 ≥ 10 × RTT"로 권한다(Tuning 문서).

### 8. 로그 압축과 읽기 (짧게)

- 로그는 계속 자란다. 상태 기계의 스냅샷을 찍고 그 앞 로그를 버린다. 너무 뒤처진 팔로워에게는 `InstallSnapshot`으로 스냅샷을 보낸다(7절). etcd 3.6.5의 `--snapshot-count` 기본값은 10000(커밋 1만 건마다 스냅샷)이고, `etcd --help`는 이 플래그가 v3.6에서 deprecated라고 적는다.
- 선형화 읽기: 리더가 (1) 자기 term의 항목을 커밋해 커밋 위치를 알고 (2) 과반과 하트비트를 주고받아 자기가 아직 리더인지 확인한 뒤 응답한다(8절). 하트비트를 리스처럼 써서 (2)를 생략하는 방법은 시계 어긋남이 유한하다는 가정에 기댄다(같은 절). go.etcd.io/raft도 `ReadOnlyLeaseBased`는 "can be affected by clock drift"라고 적는다.

## 쓰이는 자료구조·알고리즘

- **복제 로그** — (index, term, 명령)의 배열. 디스크에 남기고 fsync한 뒤 응답해야 한다. 이 부분은 DB의 WAL과 같은 재료다 — [database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md), [os/24-fsync-and-durability](../../os/24-fsync-and-durability/2-summary.md).
- **영속 상태 셋** — `currentTerm`, `votedFor`, `log[]`(그림 2). 재시작 뒤 이 셋이 사라지면 한 term에 두 번 투표할 수 있다.
- **nextIndex·matchIndex 배열** — 리더가 팔로워별로 "다음에 보낼 칸"과 "복제 확인된 칸"을 든다. commitIndex = matchIndex 정렬의 중앙값(과반 위치) 중 현재 term 항목.
- **무작위 타이머** — 선거 타임아웃을 구간에서 무작위로 뽑는다(위 실험).
- **상태 기계** — follower·candidate·leader(+ etcd의 pre-candidate).
- **스냅샷** — 상태 기계의 시점 복사본 + 마지막 포함 index·term.
- **정족수 교집합** — 커밋한 과반과 당선한 과반이 겹친다. 28번 Paxos와 같은 뼈대다.

## 적용 — 풀어나가는 법

### 1. Raft를 직접 짜지 않는다

- 검증된 구현(etcd raft, hashicorp/raft 등)이나 그 위의 저장소(etcd·Consul)를 쓴다. MIT 6.5840 Lab 3이 Raft 구현 과제일 만큼, 맞게 짜기가 어렵다.
- 앱이 하는 일은 대부분 "Raft 저장소의 클라이언트"다. 그 클라이언트가 지킬 것을 아래에 둔다.

### 2. 클라이언트 쪽 규칙 (Java)

```java
/** 합의 저장소에 쓸 때: 타임아웃 = 결과 모름. 재시도는 같은 요청 ID로 */
String requestId = UUID.randomUUID().toString();
for (int attempt = 1; ; attempt++) {
    try {
        kv.putIfAbsentWithId("/orders/42", payload, requestId);   // 서버가 requestId로 중복을 걸러야 한다
        break;
    } catch (TimeoutException e) {          // 리더 교체·과반 상실 중
        if (attempt == 5) throw e;          // 끝내 모르면 위로 알린다 — "실패"라고 단정하지 않는다
        Thread.sleep(200L * attempt);
    }
}
```

- `putIfAbsentWithId`는 설명용 이름이다. etcd라면 `Txn`의 `If(CreateRevision(key) == 0)` 같은 조건부 쓰기가 그 자리다.
- 읽기는 용도에 따라 고른다. 결정에 쓰는 읽기는 선형화(etcd 기본). 대시보드처럼 오래돼도 되면 직렬화(`--consistency=s`)로 리더 부담과 지연을 줄인다.

### 3. 운영 순서

1. 투표 멤버는 홀수(3·5)로. 5대면 2대 장애까지 견딘다(2f+1). 4대는 3대와 같은 1대만 견딘다.
2. 멤버를 바꿀 때는 한 대씩. 새 노드는 learner로 붙이고 따라잡은 뒤 promote.
3. 타임아웃은 RTT 기준으로(하트비트 0.5~1.5×RTT, 선거 ≥10×RTT), 모든 멤버에 같은 값.
4. 디스크 fsync 지연을 감시한다.

### 4. 진단 명령

```bash
etcdctl --endpoints=$EP endpoint status -w table   # IS LEADER, RAFT TERM, RAFT INDEX, RAFT APPLIED INDEX
etcdctl --endpoints=$EP member list -w table       # IS LEARNER 열
etcdctl --endpoints=$EP endpoint health            # 과반 커밋이 되는지 (took = ...)
curl -s http://<etcd>:2379/metrics | grep -E '^etcd_server_(has_leader|leader_changes_seen_total|proposals_failed_total) |etcd_disk_wal_fsync_duration'
```

- `RAFT INDEX`와 `RAFT APPLIED INDEX` 차이가 계속 벌어지면 적용(apply)이 밀린다.
- 한 멤버의 `RAFT INDEX`만 뒤처지면 그 멤버의 네트워크·디스크를 본다.

## 장애 시나리오와 대처

### 1. 과반 상실 → 쓰기 전면 거부 (가용성 저하)

- 현상: 3대 중 2대가 죽거나 분할되자 쓰기가 전부 실패한다. 읽기도 기본값이면 실패한다.
- 보이는 형태: 클라이언트 `context deadline exceeded`·`etcdserver: request timed out`, `etcd_server_has_leader 0`, `endpoint status`의 leader 0. 위 실험 그대로다.
- 원인: Raft는 과반 없이 결정하지 않는다. 안전성을 위해 가용성을 내준 것이다.
- 대처: 홀수 대수와 장애 도메인 분산(랙·존). 오래돼도 되는 읽기는 직렬화 읽기로 돌린다. 과반을 영구히 잃었다면 etcd 재해 복구 절차(스냅샷 복원)를 따른다 — 강제로 한 대를 리더로 만드는 것은 커밋된 데이터를 잃을 수 있다.

### 2. 선거 타임아웃 튜닝 실패 → 선거 폭풍

- 현상: 리더가 계속 바뀌고 그 사이 쓰기가 실패한다. 아무도 리더가 못 되는 구간도 있다.
- 보이는 형태: `leader_changes_seen_total` 급증, 로그의 `is starting a new election`·`became candidate` 반복, term이 빠르게 오른다.
- 원인
  - 타임아웃 무작위 폭이 너무 좁아 표가 계속 갈린다(위 실험: 폭 0이면 60초 안에 실패).
  - 타임아웃이 RTT·fsync 지연에 비해 너무 짧다(12–24ms 줄: 라운드 2.13).
  - 멤버마다 다른 타이밍 값.
- 대처: RTT를 재고 etcd Tuning 기준으로 다시 잡는다. 디스크를 분리한다. PreVote를 켜 둔다(etcd 3.6 기본).

### 3. 이전 term 항목을 과반 복제만으로 커밋 (구현 버그)

- 현상: 리더 교체 뒤, 커밋됐다고 응답한 쓰기가 사라진다.
- 보이는 형태: 클라이언트는 성공을 받았는데 나중 읽기에 없다. 리더 교체가 두 번 이어진 직후에 생긴다.
- 원인: 논문 그림 8의 상황. 이전 term 항목이 과반에 있어도 더 최신 term 항목을 가진 노드가 리더가 되어 덮을 수 있다.
- 대처: 현재 term 항목으로만 커밋을 센다. 새 리더는 term 시작에 no-op을 기록한다. 직접 구현했다면 이 시나리오를 테스트로 재현한다(6.5840 Lab 3 안내문의 예시 출력에 `TestFigure83C`가 있다).

### 4. 멤버를 한 번에 여럿 바꾸거나, 띄우지 않은 멤버를 추가

- 현상: 확장 작업 중 클러스터가 갑자기 쓰기를 못 한다.
- 보이는 형태: `member list`에 `unstarted` 투표 멤버가 있다. 이 상태에서 한 대가 더 죽으면 `has_leader 0`.
- 원인: 투표 멤버 수가 늘어 과반 기준이 올랐는데 새 멤버는 아직 투표를 못 한다(위 실험 관찰 4).
- 대처: learner로 추가 → 기동·따라잡기 → promote. 한 번에 한 멤버. etcd의 `--strict-reconfig-check`(기본 켜짐)를 끄지 않는다.

### 5. 영속 상태를 잃은 노드가 다시 투표

- 현상: 디스크를 갈아 끼운(또는 데이터 디렉터리를 지운) 노드를 같은 ID로 다시 넣었더니 이상한 선거 결과가 난다.
- 보이는 형태: 같은 term에 두 후보가 둘 다 과반을 주장하거나, 커밋된 항목이 사라진다.
- 원인: `votedFor`·`currentTerm`·로그를 잃으면 이미 투표한 term에 다시 투표할 수 있다. Raft의 안전성 증명은 이 셋이 남는다고 가정한다.
- 대처: 데이터를 잃은 멤버는 `member remove` 후 새 멤버로 다시 추가한다(learner부터).

## 핵심 문장

- Raft는 리더 하나가 로그 순서를 정하고, 과반에 복제된 현재 term 항목(과 그 앞 항목)을 커밋하는 합의 알고리즘이다.
- AppendEntries의 (앞 칸 index, term) 검사가 Log Matching을 만들고, 투표의 "최신 로그만" 규칙이 커밋된 항목을 다음 리더에게 넘긴다.
- 리더는 이전 term 항목을 복제 수로 커밋하지 않는다. 자기 term 항목을 커밋하면 앞 항목이 함께 커밋된다.
- 과반이 없는 쪽은 쓰기를 못 하고, etcd 기본(`ReadOnlySafe`) 선형화 읽기도 못 한다(리스 기반 읽기는 시계 가정에 기대 예외). etcd 실험에서 혼자 남은 노드는 3초 타임아웃으로 실패했고, 직렬화 읽기만 옛 값을 돌려줬다.
- 선거 타임아웃의 무작위 폭은 표 갈림을 줄여 빨리 수렴하게 한다. 시뮬레이션에서 폭 0은 60초 안에 리더가 안 섰고, 150–300ms는 평균 1.03라운드였다.
- 멤버십은 한 번에 한 대씩, 새 멤버는 learner로 먼저 붙인다. 한꺼번에 바꾸면 겹치지 않는 과반 둘이 생길 수 있다.

## 관련 주제·근거

- 선행
  - [10-leader-election](../10-leader-election/2-summary.md) — 선출·term·PreVote·CheckQuorum(etcd 실험)
  - [07-consistency-models](../07-consistency-models/2-summary.md)(선형화 vs 직렬화 읽기), [09-quorums](../09-quorums/2-summary.md)
- 후속·연결
  - [12-coordination-and-fencing](../12-coordination-and-fencing/2-summary.md) — Raft 저장소(etcd) 위의 락과 fencing
  - [28-consensus-paxos](../28-consensus-paxos/2-summary.md) — 같은 정족수 교집합, 다른 설명 방식
  - [31-byzantine-and-blockchain](../31-byzantine-and-blockchain/2-summary.md) — 거짓말하는 노드까지 견디려면 3f+1
  - [25-impossibility-results](../25-impossibility-results/2-summary.md)(FLP — Raft가 안전성은 시간과 무관하게, 진행은 시간에 기대는 이유)
  - [database/55-distributed-databases](../../database/55-distributed-databases/2-summary.md) — 파티션 × 합의 × 원자적 커밋
  - [database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md) · [os/24-fsync-and-durability](../../os/24-fsync-and-durability/2-summary.md) — 로그를 디스크에 남기는 비용
- 논문·강의
  - Ongaro & Ousterhout, "In Search of an Understandable Consensus Algorithm (Extended Version)", 2014 — 그림 2(상태·RPC·규칙), 그림 3(다섯 성질), 5.3 로그 복제, 5.4.1 선거 제한, 5.4.2·그림 8, 5.6 타이밍, 6 멤버십(joint consensus·비투표 멤버·제거된 서버의 방해), 7 스냅샷, 8 클라이언트·읽기, 9.3·그림 16 <https://raft.github.io/raft.pdf>
  - MIT 6.5840 Spring 2026 Lab 3 Raft 안내(하트비트 초당 10회 이하, TestFigure83C) <https://pdos.csail.mit.edu/6.824/labs/lab-raft1.html>
  - MIT 6.5840 Spring 2026 L6–L7 Raft(1)(2) 노트 <https://pdos.csail.mit.edu/6.824/notes/l-raft.txt> · <https://pdos.csail.mit.edu/6.824/notes/l-raft2.txt>, 일정 <https://pdos.csail.mit.edu/6.824/schedule.html>
  - Kleppmann 『DDIA』 1판 9장 "Consistency and Consensus"("Fault-Tolerant Consensus")
- 제품 문서·소스
  - Raft 사용 문서: Consul Consensus <https://developer.hashicorp.com/consul/docs/architecture/consensus>, CockroachDB Replication Layer <https://www.cockroachlabs.com/docs/stable/architecture/replication-layer>, TiKV Deep Dive Raft <https://tikv.org/deep-dive/consensus-algorithm/raft/>, Kafka KIP-595 <https://cwiki.apache.org/confluence/display/KAFKA/KIP-595%3A+A+Raft+Protocol+for+the+Metadata+Quorum>
  - etcd v3.6 Tuning <https://etcd.io/docs/v3.6/tuning/> · API guarantees(strict serializability, serializable 읽기) <https://etcd.io/docs/v3.6/learning/api_guarantees/>
  - etcd v3.6.5 `etcd --help`(`--pre-vote`, `--strict-reconfig-check`, `--max-learners` 기본 1), `server/etcdserver/bootstrap.go`(raftConfig), `server/etcdserver/server.go`(ConfChange)
  - go.etcd.io/raft v3.6.0 `raft.go` — `ReadOnlySafe`(기본)·`ReadOnlyLeaseBased`, `resetRandomizedElectionTimeout`, `becomeLeader`의 빈 항목
- 실험 목록
  - A3 3노드 중 2노드 kill → put·선형화 get 실패(3초), 직렬화 get은 옛 값, 실패한 put의 미적용 확인(watch 이력) — 전용 etcd 3.6.5 클러스터
  - D learner 추가·읽기 제한·promote·제거, 한 대 장애 중 투표 멤버 추가 거부(strict-reconfig-check)
  - E 선거 타임아웃 무작위 폭별 재선출 시간 이산 사건 시뮬레이션(Java 21, 1000회 × 6구간) — 사실 점검에서 독립 구현한 시뮬레이션(같은 지연·구간·1000회)도 같은 경향(폭 0은 60초 안에 실패, 150–300ms 중앙값 186ms, 12–24ms 중앙값 39ms)
