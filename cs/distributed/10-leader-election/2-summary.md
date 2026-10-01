# distributed/10-leader-election — 리더 선출: 장애 탐지·리스·임기(에포크), 분할 때의 리더 둘 — 정리 (힌트)

## 해결하는 문제

여러 대가 같은 일을 할 수 있어도, **순서를 정하는 일**과 **한 번만 해야 하는 일**은 한 대가 맡아야 한다.

```text
  리더 없이 둘이 동시에 쓰면              리더 하나가 순서를 정하면
  A: x=1 ─┐                               클라이언트 ─> 리더 ─> 1) x=1  2) x=2 ─> 모든 복제본에 같은 순서
  B: x=2 ─┴─> 복제본마다 도착 순서가 달라
              최종 x가 1인 곳과 2인 곳이 생긴다
```

- 그런데 리더는 죽는다. 사람이 손으로 바꾸면 새벽에 몇십 분이 멈춘다.
- 자동으로 바꾸려면 세 가지를 풀어야 한다.
  1. **죽었다고 언제 판단하나** — 장애 탐지.
  2. **누가 새 리더인가를 모두가 같게 보나** — 선출(합의).
  3. **옛 리더가 살아 돌아오면 어떻게 가려내나** — 임기 번호(에포크).
  - *리더 선출(leader election)*: 후보 여럿 중 한 대를 리더로 정하고, 그 리더가 죽거나 끊기면 다른 한 대로 바꾸는 절차.

쉬운 예: 반장 선거다.
- 반장이 결석하면 새로 뽑는다. 그런데 결석인지 지각인지 교실에서는 모른다.
- 지각한 옛 반장이 들어와 "내가 반장"이라고 하면 "몇 대 반장인가"로 가려낸다.

똑같은 구조다.\
"결석인지 지각인지 모른다"가 비동기 네트워크에서 **죽음과 느림을 구별할 수 없다**는 사실이다([02-system-and-failure-models](../02-system-and-failure-models/2-summary.md)).\
그래서 리더 선출의 목표는 "리더가 정확히 한 대"가 아니다. **리더라고 믿는 놈이 둘이어도 둘 다 결정을 내리지는 못하게** 하는 것이다.

실무 예:
- 데이터베이스 주 서버 자동 승격(페일오버) — [database/32-replication-leader-follower](../../database/32-replication-leader-follower/2-summary.md)
- etcd·ZooKeeper·Kafka KRaft 컨트롤러 같은 합의 그룹 안의 리더
- Kubernetes 컨트롤러 매니저처럼 "여러 대 띄우되 한 대만 일하는" 애플리케이션 — 합의 저장소(etcd)의 lease를 빌려 쓴다
- 기초 개념(락과 선출의 차이, 상태 기계 FOLLOWER·LEADER·STEPPING_DOWN)은 원본 [ops-patterns/12-leader-election](../../ops-patterns/12-leader-election/2-summary.md) 「동작·원리」에 있다.

## 동작·원리

### 1. 한 장 그림 — 탐지 → 선출 → 임기 증가

```text
 시간 ─────────────────────────────────────────────────────────────>
 리더 A(term 3)  ♥  ♥  ♥  ✕ 죽음
 B              ·  ·  ·  ·  ·  ·  [타임아웃] 후보(term 4) ─ 투표 요청 ─┐
 C              ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  찬성 ─┘ → B가 리더(term 4)
                ♥ = 하트비트          |<── 선거 타임아웃 ──>|
```

- 리더는 주기적으로 하트비트를 보낸다.
  - *하트비트(heartbeat)*: "나 살아 있다"는 주기 메시지. etcd 3.6 기본 간격은 100ms다(`etcd --help`, etcd v3.6 Tuning 문서).
- 팔로워는 **선거 타임아웃** 동안 하트비트를 못 받으면 리더가 죽었다고 본다.
  - *선거 타임아웃(election timeout)*: 리더 소식 없이 기다리는 상한. etcd 3.6 기본 1000ms.
- 후보는 임기 번호를 1 올리고 표를 모은다. **과반**이 찬성하면 리더다.
  - *임기(term, 에포크·세대 번호라고도 한다)*: 선출할 때마다 1씩 커지는 번호. 노드는 더 큰 term을 보면 자기 term을 따라 올린다.
  - *과반(majority)*: 전체 투표 멤버 수의 절반보다 많은 수. 3대면 2, 5대면 3.
- 한 term에서 노드는 한 표만 준다. 과반 둘은 한 대 이상 겹치므로, **한 term에 리더는 많아야 하나**다(Raft 논문 그림 3 Election Safety).

### 2. 실험: etcd 3노드에서 리더를 죽이면

전용 일회용 3노드 클러스터(`sn-dw-w10-e1~3`)에서 리더 컨테이너를 `docker kill`(SIGKILL)하고, 남은 노드의 raft 로그와 `etcdctl endpoint status`를 봤다.

(실험, etcd 3.6.5 3노드, 기본 설정 heartbeat 100ms·election 1000ms, 2026-10-01) — 2회차 출력

```text
--- 전
http://sn-dw-w10-e1:2379   member=bc22c2e06ef17fae leader=d12c53d5e01c4303 term=3 index=10
http://sn-dw-w10-e2:2379   member=d12c53d5e01c4303 leader=d12c53d5e01c4303 term=3 index=10
http://sn-dw-w10-e3:2379   member=73614ce759299fd2 leader=d12c53d5e01c4303 term=3 index=10
--- kill sn-dw-w10-e2 at 00:57:47.924
--- 남은 노드 로그(raft 이벤트)
e3 00:57:48.980 73614ce759299fd2 is starting a new election at term 3
e3 00:57:48.980 73614ce759299fd2 became pre-candidate at term 3
e3 00:57:48.981 73614ce759299fd2 has received 2 MsgPreVoteResp votes and 0 vote rejections
e3 00:57:48.981 73614ce759299fd2 became candidate at term 4
e3 00:57:48.987 73614ce759299fd2 received MsgVoteResp from bc22c2e06ef17fae at term 4
e3 00:57:48.987 73614ce759299fd2 became leader at term 4
--- 후
http://sn-dw-w10-e1:2379   member=bc22c2e06ef17fae leader=73614ce759299fd2 term=4 index=11
http://sn-dw-w10-e3:2379   member=73614ce759299fd2 leader=73614ce759299fd2 term=4 index=11
```

(로그는 원본에서 raft 이벤트 줄 일부만 골랐다. 전체는 실험 목록의 `out-A1-run2.txt`.)

- 관찰 1 — **term이 3 → 4**로 올랐다. 새 리더가 생길 때마다 term이 커진다.
- 관찰 2 — kill부터 새 리더까지 세 번 돌린 값: **1.526초, 1.063초, 1.583초.** 실행마다 다르다. 같은 조건의 다른 일회용 클러스터에서 다시 돌린 네 번은 1.551·1.756·1.350·1.371초였다.
  - 해석: etcd raft는 선거 타임아웃을 `[electionTimeout, 2×electionTimeout)` 틱에서 무작위로 고른다(go.etcd.io/raft v3.6.0 `resetRandomizedElectionTimeout`). 기본값이면 1~2초 구간이고, 세 값이 모두 그 안이다. 다만 이 구간은 타이머 설정 범위이지 복구 시간의 보장 범위는 아니다. 타이머는 kill 순간이 아니라 마지막 하트비트를 받은 때부터 돌고, 표가 갈리면 재선거로 더 걸린다(Raft 논문 §9.3).
- 관찰 3 — `pre-candidate`를 먼저 거쳤다. etcd 3.6은 `--pre-vote` 기본값이 `true`다.
  - *PreVote*: term을 올리기 전에 "내가 이길 수 있나"를 먼저 물어보는 단계. 끊겼다 돌아온 노드가 쓸데없이 term을 올려 멀쩡한 리더를 끌어내리는 일을 막는다.
- 관찰 4 — raft index가 10 → 11로 하나 늘었다. 새 리더는 자기 term의 빈 항목을 하나 기록한다(go.etcd.io/raft `becomeLeader`의 `emptyEnt`, Raft 논문 8절의 no-op).

### 3. 분할 — "리더 둘"은 실제로 생긴다

죽이는 대신 리더를 네트워크에서 떼어 냈다(`docker network disconnect`).

```text
        분할 전                                  분할 후
   ┌────────────────┐               ┌──────────┐ ║ ┌──────────────────┐
   │ e1(리더,term6) │               │ e1       │ ║ │ e2   e3          │
   │ e2   e3        │               │ 나 혼자   │ ║ │ 과반(2/3) → 선출 │
   └────────────────┘               │ (1/3)    │ ║ │ e2 리더, term 7  │
                                    └──────────┘ ║ └──────────────────┘
```

(실험, etcd 3.6.5 3노드, 2026-10-01) — 세 노드 로그를 시각순으로 합친 것

```text
00:59:03.559 e2 d12c53d5e01c4303 became pre-candidate at term 6
00:59:03.568 e2 d12c53d5e01c4303 became candidate at term 7
00:59:03.574 e2 d12c53d5e01c4303 became leader at term 7
00:59:03.574 e3 raft.node: 73614ce759299fd2 elected leader d12c53d5e01c4303 at term 7
00:59:03.936 e1 bc22c2e06ef17fae stepped down to follower since quorum is not active
```

분할 시각은 00:59:02.415, 떼어 낸 옛 리더 e1에 보낸 `put`은 `Error: context deadline exceeded`였다.

- 관찰 1 — 새 리더 e2가 03.574에 섰고, 옛 리더 e1은 03.936에야 물러났다. **약 0.36초 동안 리더라고 믿는 노드가 둘**이었다(e1은 term 6, e2는 term 7).
  - 겹침 길이는 실행마다 다르다. 다시 돌린 두 번에서는 한 번은 약 0.30초 겹쳤고, 한 번은 옛 리더가 새 리더보다 약 0.22초 **먼저** 물러나 겹침이 없었다. 둘 다 각자의 무작위 타이머(옛 리더의 CheckQuorum 판정, 과반 쪽의 선거 타임아웃)에 달렸기 때문이다.
- 관찰 2 — 그래도 e1은 아무것도 확정하지 못했다. 쓰기를 확정하려면 과반의 확인이 필요한데, e1 쪽에는 자기 하나뿐이다.
- 관찰 3 — e1은 스스로 물러났다. etcd 3.6은 raft의 `CheckQuorum`을 켜 둔다(`server/etcdserver/bootstrap.go`의 `CheckQuorum: true`).
  - *CheckQuorum*: 리더가 선거 타임아웃 동안 과반과 연락이 안 되면 스스로 팔로워가 되는 규칙.
- 관찰 4 — 떨어져 있는 동안 e1은 `became pre-candidate at term 6`을 일정 간격으로 되풀이했고(이 실행은 1.2초, 다시 돌린 두 번은 1.7초·1.9초 — 무작위 선거 타임아웃 구간 안), **term은 6에 머물렀다.** PreVote가 과반 찬성을 못 받아 term을 올리지 않은 것이다. 재연결 뒤 e1은 `received a MsgAppResp message with higher term ... [term: 7]`을 보고 term 7 팔로워가 됐다.

정리하면 리더 선출의 안전성은 "리더가 하나"가 아니라 이렇게 선다.

```text
  리더라고 믿는 놈       ─ 둘일 수 있다(시간 차)
  결정(커밋)할 수 있는 놈 ─ 과반을 가진 쪽 하나뿐   ← 정족수가 지키는 것
  옛 리더의 늦은 명령    ─ 더 큰 term을 이미 본 쪽은 거절한다  ← 임기 번호가 지키는 것
```

### 4. 리스 — 시계에 기대는 부분

합의 그룹 바깥의 애플리케이션은 보통 **합의 저장소의 lease**로 리더를 정한다.

- *리스(lease)*: 기한이 붙은 권리. 갱신(keepalive)하지 않으면 기한 뒤 저절로 사라진다.

```text
 저장소의 시계   |── lease 10초 ─────────────────|만료 → B에게 줌
 A의 시계(느림)  |── A가 생각하는 10초 ────────────────|   ← A는 아직 리더라고 믿는다
                                               ^^^^^ 겹침: 리더 둘
 A의 GC 멈춤     |──|█████████ 멈춤 █████████|──>  깨어나 "나 리더" 하고 쓴다
```

- 리스는 **시간이 흐른 양**을 양쪽이 비슷하게 잰다고 가정한다.
  - 시각이 아니라 흐른 양이다. 그래서 벽시계가 아니라 단조 시계로 재야 한다([04-physical-clocks-and-ntp](../04-physical-clocks-and-ntp/2-summary.md)).
  - 그래도 시계 속도 차이(drift)와 프로세스 멈춤(GC·스왑)은 남는다.
- Kubernetes client-go `leaderelection` 패키지 문서 주석이 이것을 그대로 적는다.
  - "This implementation does not guarantee that only one client is acting as a leader (a.k.a. fencing)."
  - 임의의 시계 어긋남(skew)에는 견디지만 임의의 시계 **속도** 차이(skew rate)에는 견디지 못한다("tolerant to arbitrary clock skew, but is not tolerant to arbitrary clock skew rate"). 견딜 수 있는 속도 비율은 `LeaseDuration` 대 `RenewDeadline` 비로 정한다고 적는다.
- 그래서 리스만으로는 리더 둘을 못 막는다. 남는 겹침은 **임기 번호를 쓰기에 실어 받는 쪽이 검사**해서 막는다(12번 fencing).

### 5. 실험: etcd lease로 하는 애플리케이션 선출

etcd 클라이언트의 `concurrency.Election.Campaign`과 같은 규칙으로 직접 짰다.
1. lease를 받는다.
2. 접두사 아래에 `접두사/<leaseID>` 키를 그 lease로 만든다(키가 없을 때만 — txn).
3. 접두사 아래 **create_revision이 가장 작은 키의 주인**이 리더다.

- *create_revision*: etcd가 키를 만든 순간의 전역 리비전 번호. 클러스터 전체에서 커지기만 한다.

(실험, etcd 3.6.5 3노드 공용 클러스터 `sn-dw-etcd*`, Java 21 HttpClient → etcd gRPC-gateway, lease TTL 2초, 2026-10-01)

```text
t=  135ms A 입후보 create_revision=6, B 입후보 create_revision=7
t=  158ms 리더 = A(create_revision=6)
t= 1019ms A 멈춤 시작(keepalive 중단) — A는 여전히 자기가 리더라고 믿는다
t= 3114ms 리더 = B(create_revision=7)
t= 6433ms A 깨어남: 믿음=나는 리더, A lease TTL=-1 (−1 = 만료), 실제 리더 = B(create_revision=7)
t= 6458ms B 사임(lease revoke) → 리더 = (없음)
```

- 관찰 1 — A가 keepalive를 멈추고 약 2초 뒤 A의 키가 사라졌고, B가 리더가 됐다.
- 관찰 2 — 6.4초에 깨어난 A의 지역 변수는 여전히 "나는 리더"다. **A는 저장소에 다시 물어보기 전까지 자기가 밀려난 것을 모른다.**
- 관찰 3 — B의 create_revision(7)은 A의 것(6)보다 크다. 이 값이 그대로 **임기 번호 겸 fencing token**이 된다.
- 덧붙임: TTL 1초로 lease를 요청하면 etcd 3.6.5 기본 설정은 `granted with TTL(2s)`로 올려 준다(실험). 소스 `server/etcdserver/server.go`의 `minTTL = (3*ElectionTicks)/2 × heartbeat` = 1.5초를 올림한 값이다.

## 쓰이는 자료구조·알고리즘

- **단조 증가 카운터(term·epoch)** — 더 큰 번호가 더 최근 리더다. 저장할 때 디스크에 남겨야 재시작 뒤에도 되돌아가지 않는다(Raft 그림 2의 영속 상태 `currentTerm`·`votedFor`).
- **정족수(과반)** — 두 과반은 한 대 이상 겹친다. "한 term에 리더 하나"와 "과반 없는 쪽은 결정 못 함"이 여기서 나온다. 계산은 28번 Paxos의 정족수 교집합 실험.
- **상태 기계** — follower → (pre-candidate) → candidate → leader. 더 큰 term을 보면 어느 상태에서든 follower로.
- **무작위 타이머** — 모두 같은 순간에 후보가 되면 표가 갈린다. 타임아웃을 무작위로 흩어 놓는다(11번 실험).
- **lease(기한 + 갱신)** — 시간으로 권리를 끊는 장치. 원본 [ops-patterns/11-distributed-lock](../../ops-patterns/11-distributed-lock/2-summary.md)의 `LeaseLock`과 같은 구조다.
- **순서 대기열(create_revision·sequential znode)** — etcd는 create_revision, ZooKeeper는 `EPHEMERAL|SEQUENTIAL` znode의 순번으로 후보를 줄 세운다. 앞사람 키만 지켜보면 리더가 바뀔 때 모두가 한꺼번에 깨어나지 않는다(Hunt 외 2010, "Simple Locks without Herd Effect").
- **장애 탐지기** — 하트비트 + 타임아웃. φ accrual 같은 적응형 탐지기는 [02-system-and-failure-models](../02-system-and-failure-models/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 정말 리더가 필요한가부터

- 일을 키 단위로 나눌 수 있으면(파티션별 소유) 리더 하나보다 낫다.
- 멱등하게 만들 수 있으면 "두 번 돌아도 괜찮다"로 리더가 필요 없어질 수 있다.
- 그래도 필요하면 **선출을 직접 만들지 않는다.** 합의 저장소(etcd·ZooKeeper)나 플랫폼(Kubernetes `Lease`)을 빌린다.

### 2. 애플리케이션 리더 루프의 뼈대 (Java)

아래 `ElectionStore`는 이 노트의 설명용 인터페이스다. etcd라면 `concurrency.Election`, ZooKeeper라면 Curator `LeaderLatch` 같은 것이 그 자리다.

```java
interface ElectionStore {
    /** 입후보 후 리더가 될 때까지 기다린다. 반환값 = 내 임기(etcd라면 내 키의 create_revision) */
    long campaign(String name, Duration ttl) throws InterruptedException;
    /** lease 갱신. 이미 만료됐으면 false — 되살리지 않는다 */
    boolean keepAlive();
    void resign();
}

void leaderLoop(ElectionStore store, Work work) throws InterruptedException {
    while (true) {
        long epoch = store.campaign("relay", Duration.ofSeconds(10));
        // 저장소보다 짧게 잡은 내 기한 — 단조 시계로 잰다(벽시계는 NTP가 되돌릴 수 있다)
        long myDeadline = System.nanoTime() + Duration.ofSeconds(6).toNanos();
        try {
            while (System.nanoTime() < myDeadline) {
                work.doOneBatch(epoch);                 // ★ 모든 쓰기에 epoch를 싣는다 → 받는 쪽이 검사(12번)
                if (store.keepAlive()) {
                    myDeadline = System.nanoTime() + Duration.ofSeconds(6).toNanos();
                } else {
                    break;                              // 잃었다 — 스스로 물러난다
                }
            }
        } finally {
            work.stopAndCleanUp();                      // STEPPING_DOWN: 하던 일을 정리
        }
    }
}
```

- 요점 셋
  - 기한을 저장소 TTL(10초)보다 짧게(6초) 잡는다. 시계 속도 차이와 지연을 여유로 흡수한다.
  - 갱신이 실패하면 남이 뺏기 전에 먼저 멈춘다.
  - 그래도 GC 멈춤은 이 루프 안에서 못 막는다. `doOneBatch` 도중에 멈출 수 있기 때문이다. 그래서 ★ 줄이 필요하다.

### 3. 진단 명령

```bash
# 누가 리더이고 term은 얼마인가 (IS LEADER, RAFT TERM 열)
etcdctl --endpoints=$EP endpoint status -w table
# 리더 교체 횟수 — 갑자기 늘면 디스크 fsync 지연·네트워크 문제를 의심
curl -s http://<etcd>:2379/metrics | grep -E '^etcd_server_(has_leader|is_leader|leader_changes_seen_total) '
# 애플리케이션 선출 지켜보기
etcdctl elect --listen <election-name>
# Kubernetes 컨트롤러의 리더 lease
kubectl -n kube-system get lease
```

(실험, etcd 3.6.5) 리더를 두 번 바꾼 뒤 e2의 `/metrics`:

```text
etcd_server_has_leader 1
etcd_server_is_leader 1
etcd_server_leader_changes_seen_total 2
etcd_server_proposals_committed_total 439
etcd_server_proposals_failed_total 0
```

### 4. 타임아웃 고르기

- etcd v3.6 Tuning 문서: 하트비트 간격은 멤버 간 RTT의 0.5~1.5배, 선거 타임아웃은 RTT의 **10배 이상**. 상한은 50초.
- 짧으면 멀쩡한 리더가 자꾸 바뀐다. 길면 진짜 장애에서 오래 멈춘다. 교체 횟수 지표가 그 선택의 자다(원본 측정: 하트비트 1초에 리스 0.5초면 교체 19회).

## 장애 시나리오와 대처

### 1. 네트워크 분할 → 리더 둘(split-brain)

- 현상: 분할 직후 옛 리더와 새 리더가 둘 다 자기가 리더라고 응답한다.
- 보이는 형태
  - 합의 그룹 안(etcd): 옛 리더 쪽 쓰기가 `context deadline exceeded`로 실패한다. 위 실험에서 겹친 시간은 0.36초였다(실행마다 다르고, 겹치지 않은 실행도 있었다).
  - 정족수 없이 만든 선출(두 대짜리 주·대기 + 하트비트만): 양쪽이 쓰기를 받아 데이터가 갈라진다. [database/32](../../database/32-replication-leader-follower/2-summary.md)의 split brain.
- 원인: 끊긴 쪽은 상대가 죽었는지 끊겼는지 구별하지 못한다.
- 대처
  - 결정에 **과반**을 요구한다. 그러면 많아야 한쪽만 진행한다. 두 대짜리는 증인(세 번째 투표자)을 둔다.
  - 리더의 쓰기에 **임기 번호**를 싣고 받는 쪽이 낮은 번호를 거절한다(12번).
  - 옛 리더가 스스로 물러나게 한다(etcd의 CheckQuorum, 위 Java 루프의 짧은 기한).

### 2. 리스가 시계에 기댄다 — 멈춤·시계 속도 차이

- 현상: 리스가 끝난 옛 리더가 몇 초 뒤 깨어나 리더로서 작업을 이어 간다.
- 보이는 형태: 같은 배치가 두 번 돈 흔적. 그 노드 로그에 긴 GC 멈춤(`Pause Full`)이나 VM 일시 정지가 같은 시각에 있다. 위 실험에서 A는 lease TTL이 -1인데도 "나는 리더"였다.
- 원인: 리스는 "보유자가 기한을 넘기기 전에 스스로 멈춘다"를 가정한다. 멈춰 있는 프로세스는 자기 시계를 볼 수 없다.
- 대처
  - 리더의 기한을 저장소 TTL보다 짧게 잡는다. 시간은 단조 시계로 잰다.
  - 그래도 남는 겹침은 fencing으로 막는다. client-go도 fencing은 보장하지 않는다고 적는다.

### 3. 리더가 너무 자주 바뀐다 (선거 폭풍의 전 단계)

- 현상: 평소 0이던 리더 교체가 분당 여러 번으로 늘고, 그때마다 요청이 잠깐 실패한다.
- 보이는 형태: `etcd_server_leader_changes_seen_total` 증가, 로그의 `lost leader`·`is starting a new election`. 같은 시각에 `etcd_disk_wal_fsync_duration_seconds` 꼬리가 길다.
- 원인: 하트비트가 선거 타임아웃 안에 도착하지 못한다. etcd Tuning 문서는 느린 디스크가 하트비트를 놓치게 해 "temporary leader loss"를 만든다고 적는다. 네트워크 RTT 대비 선거 타임아웃이 너무 짧아도 같다.
- 대처: 디스크 격리·우선순위(`ionice`), 선거 타임아웃을 RTT의 10배 이상으로. 모든 멤버에 같은 값을 준다(같은 문서).

### 4. 끊겼다 돌아온 노드가 멀쩡한 리더를 끌어내린다

- 현상: 잠깐 고립됐던 노드가 돌아오자마자 리더가 바뀌고 짧게 쓰기가 멈춘다.
- 보이는 형태: 돌아온 노드의 term이 클러스터보다 크다. 리더 로그에 더 큰 term을 보고 follower가 됐다는 줄이 나온다.
- 원인: PreVote가 없으면 고립된 노드는 혼자 선거를 반복하며 term만 올린다. 돌아와서 큰 term을 보이면 리더가 물러난다.
- 대처: PreVote를 켠다(etcd 3.6 기본 `--pre-vote=true`). 위 실험에서 고립된 e1은 term 6에 머물렀고, 돌아와서는 조용히 term 7 팔로워가 됐다.

## 핵심 문장

- 리더 선출은 장애 탐지·선출(과반 투표)·임기 번호 세 부품이다. 죽음과 느림을 구별할 수 없어서 셋 다 필요하다.
- "리더라고 믿는 놈"은 분할 때 둘일 수 있다. etcd 실험에서도 0.36초 겹친 실행이 있었다(겹침 길이는 실행마다 다르다). 정족수는 그중 **결정할 수 있는 쪽을 하나**로 만든다.
- 임기(에포크)는 선출마다 커지는 번호다. 받는 쪽이 더 큰 번호를 이미 봤다면, 옛 리더의 늦은 명령을 거절하는 근거가 된다. 아직 못 봤다면 번호만으로는 거절할 수 없다(12번).
- 리스는 시간의 흐름을 양쪽이 비슷하게 잰다는 가정 위에 있다. GC 멈춤과 시계 속도 차이 앞에서는 fencing 없이 안전하지 않다.
- etcd 3.6 기본값에서 리더를 죽이면 이번 실험에서는 모두 1~2초 안에 새 리더가 섰다. 무작위 선거 타임아웃 [1초, 2초)이 주요 요인이지만, 이 구간이 복구 시간의 하한·상한을 보장하지는 않는다.

## 관련 주제·근거

- 선행
  - [02-system-and-failure-models](../02-system-and-failure-models/2-summary.md)(장애 탐지기·죽음과 느림), [04-physical-clocks-and-ntp](../04-physical-clocks-and-ntp/2-summary.md)(단조 시계·드리프트)
  - 원본 [ops-patterns/12-leader-election](../../ops-patterns/12-leader-election/2-summary.md) — 기초(임기·하트비트·STEPPING_DOWN). 참고: 원본은 "임기 500ms → 교체 19회"처럼 "임기"를 **리스 길이** 뜻으로도 쓴다. 이 노트는 임기(term)=번호, 리스=기간으로 나눈다(Raft 논문 5.1절의 term은 번호다).
- 후속
  - 11 `consensus-raft` — 이 선출이 들어 있는 합의 알고리즘 전체(로그 복제·안전성) — [11-consensus-raft](../11-consensus-raft/2-summary.md)
  - 12 `coordination-and-fencing` — 임기 번호를 쓰기에 실어 막기 — [12-coordination-and-fencing](../12-coordination-and-fencing/2-summary.md)
  - 28 `consensus-paxos` — 제안 번호와 정족수 교집합 — [28-consensus-paxos](../28-consensus-paxos/2-summary.md)
  - [database/32-replication-leader-follower](../../database/32-replication-leader-follower/2-summary.md) — DB 페일오버와 split brain
- 교재·강의
  - Kleppmann, 『Designing Data-Intensive Applications』 1판 8장("The leader and the lock", "Fencing tokens")·9장("Epoch numbering and quorums", "Membership and Coordination Services")
  - MIT 6.5840 Spring 2026 L4 노트(split brain, 과반의 교집합) <https://pdos.csail.mit.edu/6.824/notes/l-paxos.txt>, L6 Raft <https://pdos.csail.mit.edu/6.824/notes/l-raft.txt>
- 논문·문서·소스
  - Ongaro & Ousterhout, "In Search of an Understandable Consensus Algorithm (Extended Version)" 2014 — 5.2 선출, 그림 3 Election Safety, 5.6 broadcastTime ≪ electionTimeout ≪ MTBF, 8절 no-op·읽기 <https://raft.github.io/raft.pdf>
  - Hunt 외, "ZooKeeper: Wait-free coordination for Internet-scale systems", USENIX ATC 2010 — ephemeral·sequential znode, herd effect 없는 락 <https://www.usenix.org/legacy/event/atc10/tech/full_papers/Hunt.pdf>
  - etcd v3.6 Tuning(하트비트 100ms·선거 1000ms·10×RTT·50초 상한·디스크) <https://etcd.io/docs/v3.6/tuning/>
  - etcd v3.6.5 소스: `server/etcdserver/bootstrap.go`(CheckQuorum: true, PreVote: cfg.PreVote), `server/etcdserver/server.go`(minTTL), `client/v3/concurrency/election.go`(Campaign), `etcdctl/README.md`(ELECT)
  - go.etcd.io/raft v3.6.0 `raft.go` — `resetRandomizedElectionTimeout`, `MsgCheckQuorum` 처리("stepped down to follower since quorum is not active"), `becomeLeader`의 빈 항목
  - Kubernetes client-go `tools/leaderelection/leaderelection.go` 패키지 주석(fencing 미보장, skew rate) <https://github.com/kubernetes/client-go/blob/master/tools/leaderelection/leaderelection.go>
- 실험 목록
  - A1 리더 kill → 재선출 시간·term(전용 etcd 3.6.5 3노드, 3회: 1.526·1.063·1.583초, 사실 점검 재실행 4회: 1.551·1.756·1.350·1.371초)
  - B 리더 분할 → 새 리더 선출 vs 옛 리더 자진 사퇴 시각(겹침 약 0.36초, 재실행 2회는 0.30초와 겹침 없음), 고립 중 term 유지(PreVote)
  - A2 etcd lease 기반 애플리케이션 선출(Java 21, 공용 3노드, `/w10/` 접두사), lease 최소 TTL 2초
  - etcd `/metrics`의 리더 지표
