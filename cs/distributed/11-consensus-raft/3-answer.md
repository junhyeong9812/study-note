# distributed/11-consensus-raft — 정답

## 정답

### 1. 합의가 맡는 부분

- 합의는 **로그 i번 칸에 어떤 명령이 오는지**를 모든 복제본이 같게 정하는 일이다. 실행은 각 서버의 상태 기계가 한다.
- 결정적이어야 하는 이유: 같은 명령을 같은 순서로 넣어도, 상태 기계가 현재 시각·난수·스레드 순서에 따라 다르게 동작하면 결과가 갈라진다.
  - 그래서 "지금 시각"이나 난수는 리더가 정해 명령 안에 넣어 보낸다.

### 2. 일관성 검사로 c를 맞추기

```text
 index:   1   2   3   4   5
 리더    [1] [1] [2] [3] [3]
 c       [1] [1] [2] [2] [2]

 1차: prevLogIndex=5, prevLogTerm=3 → c의 5번은 term 2 → 거절
 2차: prevLogIndex=4, prevLogTerm=3 → c의 4번은 term 2 → 거절
 3차: prevLogIndex=3, prevLogTerm=2 → 일치 → entries [4:t3, 5:t3]로 4·5를 덮는다
 결과 c: [1][1][2][3][3]
```

- 리더는 팔로워별 `nextIndex`를 하나씩 줄여 일치하는 지점을 찾는다(논문은 term 단위로 건너뛰는 최적화도 소개한다).
- c의 4·5번(term 2)은 커밋되지 않은 항목이었다. 커밋된 항목이었다면 선거 제한 때문에 그것이 없는 리더는 당선될 수 없었다.

### 3. commitIndex 계산

- matchIndex를 정렬하면 7, 7, 6, 4, 3. 5대의 과반은 3대이므로 "3대 이상이 가진 가장 큰 index"는 6이다.
- log[6].term = 5(현재 term)이면 **commitIndex = 6**.
- log[6].term = 4이면 복제 수만으로는 6을 커밋하지 않는다. 현재 term 항목이 과반에 복제될 때까지 기다린다. 7번(term 5)은 2대에만 있어 아직 아니다.

### 4. 그림 8과 no-op

- 흐름(논문 그림 8)
  - (a) S1이 term 2 리더로 index 2 항목을 일부에만 복제한다.
  - (b) S1이 죽고 S5가 term 3 리더가 되어 index 2에 다른 항목을 받는다.
  - (c) S5가 죽고 S1이 다시 리더(term 4)가 되어 term 2 항목을 과반에 복제한다. 이 시점에 커밋됐다고 보면 안 된다.
  - (d) S1이 또 죽으면 S5(마지막 term 3)가 S2·S3·S4의 표로 당선될 수 있고, index 2를 자기 term 3 항목으로 덮는다.
- 그래서 현재 term 항목만 복제 수로 커밋한다. 현재 term 항목이 과반에 들어가면 (e)처럼 S5는 더 이상 당선될 수 없고, 앞 항목도 함께 커밋된다.
- no-op: 새 리더는 자기 term 항목이 하나도 없으면 이전 항목들을 커밋할 수 없다. 그래서 term 시작에 빈 항목을 기록한다. 이것으로 커밋 위치도 알게 되어 선형화 읽기를 할 수 있다(8절).

### 5. 과반 없는 노드에 보낸 요청

(실험, etcd 3.6.5, `--command-timeout=3s`)

| 요청 | 결과 |
|---|---|
| `put /w10/x v2` | `Error: context deadline exceeded` (3.075초) |
| 기본 `get` (선형화) | `Error: context deadline exceeded` |
| `get --consistency=s` (직렬화) | `v1` — 로컬 상태, 오래됐을 수 있다 |

- 상태는 `leader=0`이었다.
- 실패한 put을 "실패"로 단정하면 안 된다. 타임아웃은 결과를 모르는 상태다. 이번 실험에서는 watch 이력에 v2가 없어 적용되지 않았지만, 리더에 도달해 로그에 들어간 뒤 응답만 잃었다면 나중에 커밋될 수 있다. 재시도는 같은 요청 ID나 조건부 쓰기로 멱등하게 한다.

### 6. 멤버십 변경

- 한 번에 바꾸면: 서버마다 새 설정을 보는 시각이 달라, 옛 설정의 과반 {1,2}와 새 설정의 과반 {3,4,5}가 겹치지 않을 수 있다. 같은 term에 리더 둘이 가능하다.
- joint consensus: 중간 설정 C(old,new)에서 결정에 옛 과반과 새 과반을 **둘 다** 요구한다. C(old,new)가 커밋된 뒤 C(new)로 간다. 어느 순간에도 옛 설정과 새 설정이 따로 결정할 수 없다(논문 6절, 그림 11).
- 한 대씩: 대수가 하나만 다르면 옛 과반과 새 과반의 합이 새 대수보다 커서 겹친다(예: 3대 과반 2 + 4대 과반 3 = 5 > 4). etcd 3.6.5의 member add·remove·promote는 한 멤버씩 `ConfChange`로 제안한다.

### 7. learner와 strict-reconfig-check

(실험, etcd 3.6.5)

- learner에서 선형화 읽기: `Error: etcdserver: rpc not supported for learner`.
- learner에서 직렬화 읽기: `v200` — 복제받은 값을 로컬에서 읽는다.
- 따라잡은 뒤 `member promote` → 투표 멤버. 따라잡기 전이면 `can only promote a learner member which is in sync with leader`.
- 한 대가 죽은 상태에서 투표 멤버 추가: `Error: etcdserver: unhealthy cluster`. 추가되면 투표 멤버 4대(과반 3) 중 살아 있는 것이 2대라 즉시 과반을 잃기 때문이다(`--strict-reconfig-check` 기본 true).

### 8. 선거 타임아웃의 무작위 폭

(실험, Java 시뮬레이션, 5대 중 리더 사망, 편도 지연 3~7ms, 1000회)

| 구간(ms) | 중앙값 | p99 | 평균 라운드 |
|---|---|---|---|
| 150–150 | 60000(상한 — 선출 실패) | 60000 | 395.19 |
| 150–155 | 776 | 3823 | 6.80 |
| 150–300 | 192 | 412 | 1.03 |
| 12–24 | 43 | 129 | 2.13 |

- 경향: 무작위 폭이 없으면 모두가 같이 후보가 되어 표가 계속 갈린다. 폭을 조금만 줘도 급히 좋아지고, 넓을수록 꼬리가 짧아진다. 논문 그림 16도 같은 경향이다(무작위 없음 → 10초 넘게, 5ms → 중앙값 287ms).
- 12–24ms를 권하지 않는 이유: 이 모델에서는 왕복 시간(6~14ms)이 타임아웃의 절반 수준이라 broadcastTime ≪ electionTimeout(5.6절)이 성립하지 않고, 라운드가 2.13으로 늘었다. 논문(9.3절)은 12–24ms에서 평균 35ms로 리더가 섰다고 보고하면서, **그보다 더 낮추면** 하트비트가 다른 서버의 선거 시작 전에 닿지 못해 불필요한 리더 교체가 생긴다고 적고 여유 있는 150–300ms를 권한다.

### 9. 잦은 리더 교체·빠른 term 증가

- 볼 것: `etcd_server_leader_changes_seen_total`, `etcd_disk_wal_fsync_duration_seconds` 꼬리, 멤버 간 RTT, 로그의 `is starting a new election`·`became candidate`, 멤버별 `--heartbeat-interval`·`--election-timeout`.
- 고칠 것: 선거 타임아웃 ≥ 10×RTT, 하트비트 0.5~1.5×RTT, 모든 멤버 같은 값(etcd Tuning). 디스크 분리·`ionice`. PreVote 유지.

### 10. 영속 상태를 잃은 노드

- 위험: Raft의 안전성은 `currentTerm`·`votedFor`·로그가 재시작 뒤에도 남는다고 가정한다. 이것을 잃으면 이미 투표한 term에 또 투표해 한 term에 두 리더가 생길 수 있다. 커밋에 참여했던 로그를 잃으면 과반의 일부가 사라져 커밋된 항목을 잃을 수도 있다.
- 절차: 그 멤버를 `member remove`하고, 빈 데이터 디렉터리로 **새 멤버**로 추가한다(learner → 따라잡기 → promote).
