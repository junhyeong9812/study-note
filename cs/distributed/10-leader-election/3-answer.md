# distributed/10-leader-election — 정답

## 정답

### 1. 세 부품이 다 필요한 이유

| 부품 | 하는 일 | 빼면 |
|---|---|---|
| 장애 탐지(하트비트 + 타임아웃) | 리더가 죽었다고 판단하는 시점 | 리더가 죽어도 아무도 모른다. 서비스가 조용히 멈춘다 |
| 과반 투표 | 한 term에 리더가 둘 선출되지 않게 함(노드마다 리더·term을 잠깐 다르게 볼 수는 있다 — 정답 3) | 분할된 양쪽이 각자 리더를 뽑아 둘 다 결정한다 |
| 임기 번호 | 누가 더 최근 리더인지 | 옛 리더의 늦은 명령과 새 리더의 명령을 구별할 근거가 없다 |

- 비동기 네트워크에서는 죽음과 느림을 구별할 수 없다. 그래서 탐지는 틀릴 수 있고, 틀렸을 때를 과반과 임기 번호가 수습한다.

### 2. 리더 kill → 1~2초, term +1

- 실험(etcd 3.6.5 3노드) 세 번: kill부터 새 리더까지 **1.526초, 1.063초, 1.583초**(재실행 네 번: 1.551·1.756·1.350·1.371초). term은 3 → 4처럼 하나 올랐다.
- 이유: etcd raft는 선거 타임아웃을 `[electionTimeout, 2×electionTimeout)` 틱 구간에서 무작위로 뽑는다(go.etcd.io/raft v3.6.0 `resetRandomizedElectionTimeout`). 기본 1000ms면 1~2초다. 투표 왕복은 몇 ms라 거의 더해지지 않는다(로그상 candidate → leader 6ms). 다만 이 구간은 타이머 설정 범위이지 복구 시간의 보장 범위가 아니다. 타이머는 마지막 하트비트부터 돌고, 표가 갈리면 재선거로 더 걸린다.
- 덤: PreVote가 기본으로 켜져 있어 `pre-candidate` 단계를 먼저 거친다. raft index도 하나 는다(새 리더의 빈 항목).

### 3. 분할 — 리더라고 믿는 노드가 잠깐 둘

- 실험: 분할 00:59:02.415 → 과반 쪽 e2가 03.574에 term 7 리더 → 옛 리더 e1은 03.936에 `stepped down to follower since quorum is not active`.
- 약 0.36초 동안 e1(term 6)과 e2(term 7)가 둘 다 자기가 리더라고 믿었다. 이 길이는 실행마다 다르다(재실행: 0.30초, 그리고 옛 리더가 먼저 물러나 겹침이 없던 실행). "잠깐 둘일 수 있다"가 답이고, 정확한 길이는 보장되지 않는다.
- 데이터가 안 갈라지는 이유: 쓰기를 확정하려면 과반의 확인이 필요하다. e1 쪽은 1/3이라 확정할 수 없다. 실제로 e1에 보낸 `put`은 `context deadline exceeded`였다.
- e1이 스스로 물러난 것은 etcd가 raft `CheckQuorum`을 켜 두었기 때문이다(`bootstrap.go`).

### 4. Election Safety ≠ 순간 리더 하나

- Election Safety는 **같은 term 안에서** 리더가 많아야 하나라는 말이다. 한 term에 노드는 한 표만 주고, 과반 둘은 겹치기 때문이다.
- 서로 **다른 term**의 리더는 동시에 존재할 수 있다. 3번 실험의 e1(term 6)과 e2(term 7)가 그렇다.
- 그래서 안전성은 "결정은 과반 쪽만", "낮은 term의 명령은 거절"로 지킨다.

### 5. lease 선출 실험의 시간표

(실험 출력, etcd 3.6.5, Java 21)

```text
t=  158ms 리더 = A(create_revision=6)
t= 1019ms A 멈춤 시작(keepalive 중단) — A는 여전히 자기가 리더라고 믿는다
t= 3114ms 리더 = B(create_revision=7)
t= 6433ms A 깨어남: 믿음=나는 리더, A lease TTL=-1 (−1 = 만료), 실제 리더 = B(create_revision=7)
```

- 3초 무렵: A의 lease가 마지막 갱신 약 2초 뒤 만료되어 A 키가 지워졌고, B가 리더다.
- 6초: 리더는 B. 깨어난 A는 저장소에 다시 묻기 전까지 "나는 리더"라고 믿는다.
- B의 create_revision(7) > A의 것(6). 이 번호가 B의 임기·fencing token 구실을 한다.

### 6. 리스가 시계에 기대는 지점

- 문제는 시각이 아니라 **흐른 양**이다. 보유자가 "TTL이 아직 안 지났다"고 판단하는 시간 측정이 저장소의 측정과 비슷해야 한다.
- 깨지는 경우
  - 보유자 시계가 느리게 간다(속도 차이, drift).
  - 보유자가 GC·VM 정지로 멈춰 자기 시계를 보지 못한다.
- 벽시계로 재면 NTP 조정·수동 변경으로 시각이 뛸 수 있으니 단조 시계로 잰다. 그래도 위 두 경우는 남는다.
- client-go `leaderelection` 주석: fencing을 보장하지 않는다. 임의의 시계 어긋남(skew)에는 견디지만 임의의 skew rate에는 견디지 못하고, 견딜 수 있는 속도 비율은 `LeaseDuration`/`RenewDeadline` 비로 설정한다.

### 7. 리더 교체가 잦아졌을 때

- 볼 것: `etcd_server_leader_changes_seen_total` 증가 시각, 로그의 `lost leader`·`is starting a new election`, `etcd_disk_wal_fsync_duration_seconds`의 꼬리, 멤버 간 RTT.
- 의심할 것: 디스크 fsync 지연으로 하트비트를 놓침(etcd Tuning 문서의 "temporary leader loss"), RTT 대비 너무 짧은 선거 타임아웃, 멤버마다 다른 타이밍 설정.
- 바꿀 것: 디스크 격리·`ionice`, 선거 타임아웃을 RTT의 10배 이상으로, 하트비트는 RTT의 0.5~1.5배, 모든 멤버에 같은 값.

### 8. 돌아온 노드가 리더를 끌어내림

- 원인: 고립된 노드가 혼자 선거를 반복하며 term을 올린다. 돌아와서 큰 term을 보이면 리더가 더 큰 term을 보고 follower가 된다.
- 막는 장치: PreVote. term을 올리기 전에 과반에게 "이길 수 있나"를 먼저 묻는다. etcd 3.6은 `--pre-vote` 기본 `true`다. 덧붙여 Raft 논문 6절과 etcd raft는 "최근에 리더 소식을 들은 노드는 투표 요청을 무시"하는 규칙도 둔다. etcd raft에서는 이 `inLease` 검사가 `CheckQuorum`이 켜져 있을 때만 동작한다(go.etcd.io/raft v3.6.0 `raft.go`, etcd 3.6은 켜 둔다).
- 실험: 고립된 e1은 `became pre-candidate at term 6`만 되풀이하고 term 6에 머물렀다. 재연결 뒤 더 큰 term(7)을 보고 조용히 follower가 됐다.

### 9. 짧은 기한 vs epoch 싣기

- 짧은 기한(TTL보다 짧게, 단조 시계): 보유자가 **깨어 있는 동안** 시계 속도 차이·지연 때문에 기한을 넘겨 일하는 것을 줄인다.
- epoch 싣기: 보유자가 **멈춰 있다가** 기한을 넘긴 뒤 보내는 쓰기를 받는 쪽에서 거절한다.
- 하나만으로 부족한 이유
  - 짧은 기한만: GC 멈춤은 확인과 쓰기 사이에서도 일어난다. 멈춘 동안은 기한을 볼 수 없다.
  - epoch만: 받는 쪽이 검사할 수 있는 쓰기만 막는다. 외부 API 호출·이메일 발송처럼 검사할 수 없는 부수 효과는 못 막는다. 그래서 스스로 물러나는 규칙도 같이 둔다.
