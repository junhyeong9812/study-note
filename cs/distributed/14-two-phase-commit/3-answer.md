# distributed/14-two-phase-commit — 정답

## 정답

### 1. 로컬 트랜잭션만으로는 안 되는 이유

- 서버 1이 먼저 커밋한 뒤 서버 2가 실패하면, 서버 1은 이미 확정한 변경을 혼자 되돌릴 수 없다. 반대로 서버 2가 먼저여도 같다.
- 각 서버는 "다른 서버도 커밋할 것인가"를 모른 채 자기 결정을 내린다.
- 2PC가 추가하는 것
  - **prepare 단계**: 커밋 직전 상태를 디스크에 남기고 "할 수 있다(YES)"를 약속하게 한다. 약속한 뒤에는 혼자 결정하지 못한다.
  - **코디네이터의 단일 결정**: 전원 YES일 때만 커밋을 결정하고, 그 결정을 모두에게 따르게 한다.

### 2. 정상 흐름과 디스크 쓰기 두 곳

```text
  TC            A                    B
  │─PREPARE────>│ [디스크: prepared]   │
  │─PREPARE──────────────────────────>│ [디스크: prepared]
  │<──YES───────│                     │
  │<──YES─────────────────────────────│
  │ [디스크: COMMIT 결정]  ← 커밋 지점
  │─COMMIT─────>│ 확정·락 해제 → ACK  │
  │─COMMIT───────────────────────────>│ 확정·락 해제 → ACK
```

- 참가자의 prepared 기록: YES를 보낸 뒤 크래시해도 커밋할 수 있어야 한다. 다른 참가자가 이미 커밋했을 수 있기 때문이다(6.5840 L11).
- TC의 결정 기록: COMMIT을 일부에게만 보내고 죽었다면, 재시작 후 같은 결정을 다시 보내야 한다. 그래서 COMMIT을 보내기 **전에** 디스크에 쓴다.

### 3. 참가자가 혼자 중단해도 되는 때

| 시점 | 혼자 중단? | 이유 |
|---|---|---|
| (a) PREPARE 전 | 된다 | 아직 YES를 안 보냈으니 TC가 커밋을 결정했을 리 없다. 이후 PREPARE에는 NO로 답한다 |
| (b) YES 뒤 결정 미도착 | 안 된다 | TC가 이미 COMMIT을 정해 A에 보냈을 수 있다. 혼자 커밋해도 안 된다(A가 NO였을 수 있다). 기다린다 = 블로킹 |
| (c) COMMIT 받은 뒤 | 해당 없음 | 결정이 확정됐다. 커밋을 끝내고 ACK한다. 같은 COMMIT이 또 오면 TID로 걸러 ACK만 다시 보낸다 |

### 4. prepare 뒤 코디네이터가 죽었을 때 (실험 결과)

- (a) `SELECT`: 막히지 않는다. MVCC로 이체 전 값(900)을 읽었다.
- (b) 같은 행 `UPDATE`: 3.113초 뒤 `ERROR: canceling statement due to lock timeout`. prepared 트랜잭션이 행 락을 쥐고 있다. `pg_locks`의 그 트랜잭션 항목은 pid가 비어 있었다.
- (c) 재시작 뒤: `pg_prepared_xacts`에 `tx-2`가 그대로 남았고, 같은 행 쓰기도 다시 lock timeout이었다. prepared 상태는 크래시·재시작을 견딘다.
- 근거: 실험(전용 PostgreSQL 17.11 2대 + Java 21, 2026-10-01).

### 5. 결정 로그로 복구하기

- `COMMIT tx-2`가 없다 → `ROLLBACK PREPARED 'tx-2'`. TC가 커밋을 결정한 적이 없으니 어느 참가자도 커밋하지 않았다. 중단이 안전하다.
- `COMMIT tx-3`이 있다 → `COMMIT PREPARED 'tx-3'`을 모든 참가자에게. 일부가 이미 커밋했을 수 있으니 결정을 끝까지 관철한다.
- 실험 출력: tx-2는 두 참가자 모두 `ROLLBACK PREPARED`(A 900·B 1100 유지), tx-3은 두 참가자 모두 `COMMIT PREPARED`(A 800·B 1200).
- 이름: *presumed abort* — 결정 기록이 없으면 중단으로 간주한다(R*, Mohan 외 1986).

### 6. 3PC를 안 쓰는 이유와 실무 해법

- DDIA 9장: 3PC는 지연 상한이 있는 네트워크와 응답 시간 상한이 있는 노드를 가정한다. 실제 네트워크는 지연 상한이 없어서 그 가정이 깨지면 원자성을 보장하지 못한다.
- 실무 해법: 코디네이터(와 참가자)를 Raft·Paxos로 복제한다. 코디네이터 한 대가 죽어도 복제본이 결정을 이어받아 참가자가 무기한 기다리지 않는다(6.5840 L11).

### 7. 2PC와 Raft

- 2PC: 참가자마다 **다른 일**을 하고, **모두** 자기 몫을 해야 할 때(샤드 A는 출금, 샤드 B는 입금). 전원이 살아 있어야 진행한다. 가용성을 높이지 않는다.
- Raft: 모든 서버가 **같은 일**을 하고, **과반**만 살아 있으면 진행한다. 가용성을 높이지만 "모두가 했다"는 보장은 없다.
- Spanner: 각 샤드(와 코디네이터)를 Paxos로 복제한 그룹으로 만들고, 그룹들 사이에서 2PC를 돈다(6.5840 L11·L12).

### 8. 방치된 prepared 트랜잭션 진단

- 조회
  - `SELECT gid, prepared, owner, database, age(transaction) FROM pg_prepared_xacts;` — 며칠 된 항목이 있나.
  - `VACUUM (VERBOSE) <테이블>` — `dead but not yet removable`이 크면 cutoff를 누가 붙잡나 본다.
  - `pg_locks`에서 pid 없는 락.
- 확인: 그 gid를 만든 트랜잭션 관리자의 결정 로그. 다른 참가자의 같은 gid 상태(이미 커밋됐나).
- 정리: 결정 로그대로 `COMMIT PREPARED` 또는 `ROLLBACK PREPARED`. 실험에서는 `ROLLBACK PREPARED` 직후 VACUUM이 dead tuple 1,000개를 제거했다.
- 재발 방지: 쓰지 않으면 `max_prepared_transactions = 0`(PostgreSQL 17 기본값이자 문서 권고). 쓰면 `pg_prepared_xacts`의 건수·나이에 알람.

### 9. 휴리스틱 롤백의 위험

- 다른 참가자가 이미 `COMMIT PREPARED`를 했다면, 이쪽만 롤백되어 원자성이 깨진다(돈이 생기거나 사라진다).
- DDIA 9장은 이런 휴리스틱 결정을 2PC의 약속을 깨는 비상구라고 부른다. JTA에서는 `HeuristicMixedException` 같은 결과로 드러난다.
- 먼저 확인할 것: 코디네이터 결정 로그, 다른 모든 참가자의 같은 트랜잭션 상태. 하나라도 커밋됐다면 나머지도 커밋해야 한다.

### 10. DB + Kafka와 2PC

- Kafka 4.1 프로듀서 트랜잭션은 Kafka 안(파티션 쓰기·컨슈머 오프셋)의 원자성이다. DB와 함께 XA 2PC에 참가하지 않는다.
  - Kafka가 외부 2PC에 참가하게 하는 KIP-939는 "Accepted" 상태다. kafka-clients 4.1.0에는 관련 설정과 `PreparedTxnState` 클래스는 있지만, 공개 `KafkaProducer`에 `prepareTransaction()`·`completeTransaction()`이 없다(4.1.0 소스). 4.1.0 클라이언트로는 2PC 참가자로 쓸 수 없다.
- 실무 대안: transactional outbox — 이벤트를 비즈니스 데이터와 같은 DB 트랜잭션에 쓰고, 릴레이가 나중에 발행한다(16번).
