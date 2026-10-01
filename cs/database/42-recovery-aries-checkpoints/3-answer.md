# database/42-recovery-aries-checkpoints — 정답

## 정답

### 1. STEAL·NO-FORCE

| 정책 | 뜻 | 복구에 필요해지는 것 |
|---|---|---|
| STEAL | 커밋 안 된 트랜잭션의 dirty 페이지도 디스크로 내보낼 수 있다 | **취소(undo)** — 디스크에 올라간 미커밋 변경을 되돌려야 한다 |
| NO-FORCE | 커밋할 때 페이지를 디스크에 강제로 쓰지 않는다 | **재실행(redo)** — 커밋됐지만 디스크에 없는 변경을 다시 해야 한다 |

- 이유: STEAL은 버퍼 풀이 트랜잭션에 묶이지 않게 한다(큰 트랜잭션도 메모리에 안 갇힌다). NO-FORCE는 커밋을 "로그 순차 쓰기 한 번"으로 끝내 빠르게 한다. 런타임 성능을 사고 복구 복잡도를 치른다.

### 2. 네 LSN

| 이름 | 위치 | 쓰임 |
|---|---|---|
| pageLSN | 각 페이지 헤더 | 이 페이지를 마지막으로 바꾼 로그. 재실행 때 "이미 반영됐나" 판정 |
| prevLSN | 각 로그 레코드 | 같은 트랜잭션의 앞 레코드. 취소 때 거꾸로 걷는 사슬 |
| recLSN | DPT(메모리, 체크포인트에 기록) | 페이지를 처음 더럽힌 로그. 재실행 시작점 계산 |
| flushedLSN | 메모리 | 로그가 디스크에 여기까지 내려갔다 |

- 부등식: 페이지 P를 쓰기 전 `pageLSN(P) ≤ flushedLSN`. 페이지 변경을 설명하는 로그가 먼저 디스크에 있어야 한다(WAL 규칙).

### 3. 예제 풀이

- 분석(LSN 40부터)
  - ATT: T1(UNDO, lastLSN 80). T2는 70에서 COMMIT → 재실행 끝에 TXN-END를 쓰고 빠진다.
  - DPT: P1(rec 20), P2(rec 30), P3(rec 60).
- 재실행 시작: min(recLSN) = **20**. 20·30·60·80을 차례로 검사해 필요한 것만 다시 적용한다.
- 취소: T1만. lastLSN 80부터 prevLSN 사슬로.

```text
  90   CLR undo 80 (P1)   undoNextLSN = 60
  100  CLR undo 60 (P3)   undoNextLSN = 20
  110  CLR undo 20 (P1)   undoNextLSN = 10   (10은 BEGIN — 되돌릴 갱신 없음)
  120  T1 TXN-END
```

### 4. 역사 반복과 건너뛰기

- 크래시 직전의 **정확한 페이지 상태**를 먼저 만들어야 그 위에서 취소가 올바르게 동작한다. 또 재실행 단계는 "이 레코드가 누구 것인가"를 따지지 않아 단순하다. 취소는 CLR로 기록되므로 그 자체도 재실행 대상이 된다.
- 건너뛰는 조건(CMU L21)
  1. 레코드가 바꾼 페이지가 DPT에 없다 → 이미 디스크에 있다.
  2. 페이지는 DPT에 있지만 레코드 LSN < 그 페이지의 recLSN → 그 변경은 이미 디스크에 있다.
  3. 디스크에서 읽은 pageLSN ≥ 레코드 LSN → 이미 반영됐다.
- 다시 적용하면 pageLSN을 그 LSN으로 올린다. 이 판정 때문에 재실행은 몇 번 해도 결과가 같다.

### 5. 취소 도중 재크래시

- 재시작 → 분석이 CLR 90·100을 보고 T1의 lastLSN을 100으로 잡는다.
- 재실행이 CLR 90·100까지 다시 적용한다(CLR도 재실행 대상).
- 취소는 CLR 100의 `undoNextLSN = 20`에서 **이어서** 한다. LSN 80·60은 다시 되돌리지 않는다.
- CLR 자체는 되돌리지 않는다. 그래서 "되돌림을 되돌리는" 일이 없고, 반복 크래시에도 취소 작업이 유한하다.

### 6. PostgreSQL과 InnoDB의 차이

- PostgreSQL 17: 변경을 제자리에 덮지 않고 새 튜플 버전을 쓴다(MVCC). 트랜잭션이 커밋됐는지는 커밋 로그(`pg_xact`)가 정한다. 커밋 기록이 없는 트랜잭션은 크래시 뒤 **중단으로 간주**되고(`transam/README`, `PREPARE TRANSACTION`을 마친 준비 상태 트랜잭션은 예외), 그 튜플은 보이지 않다가 나중에 vacuum이 치운다. 그래서 재실행만 한다.
- `ROLLBACK`의 WAL: 로컬 재현에서 `HOT_UPDATE`·`LOCK`·`UPDATE` 뒤에 `Transaction … ABORT` 레코드 하나였다. CLR 같은 되돌림 레코드는 없다.
- InnoDB(MySQL 8.4): redo 적용 뒤 undo 로그로 미완료 트랜잭션을 **롤백한다**(`XA PREPARE` 상태의 XA 트랜잭션은 예외 — 준비 상태로 남는다). 이 롤백은 백그라운드 스레드가 새 연결과 병렬로 한다(17.18.2). ARIES의 취소 단계에 해당한다.

### 7. 퍼지 체크포인트

- 블로킹: 새 트랜잭션을 막고 실행 중인 것을 멈추거나 끝나길 기다린 뒤 dirty 페이지를 다 쓴다. 복구는 단순하지만 서비스가 멈춘다.
- 퍼지: 멈추지 않는다. 시작 순간의 ATT·DPT(또는 redo 시작 위치)를 기록하고, 복구가 그 이후를 계산한다.
- PostgreSQL: 체크포인트는 시작 시점의 WAL 위치를 **redo 위치**로 잡고, dirty 버퍼를 `checkpoint_completion_target`에 맞춰 퍼뜨려 쓴 뒤 끝에 `CHECKPOINT_ONLINE`을 쓴다. 쓰는 동안에도 다른 트랜잭션의 WAL이 쌓이므로 레코드가 자기보다 앞의 redo 위치를 가리킨다. 로컬 `pg_controldata`에서는 두 위치가 약 65 MB 떨어져 있었다.

### 8. 20분째 recovery mode

- 원인 후보: 마지막 체크포인트 뒤 WAL이 매우 많다. `max_wal_size`·`checkpoint_timeout`이 크거나, 체크포인트가 오래 못 끝났다(I/O 포화). 느린 스토리지라 재생 중 랜덤 읽기가 많다.
- 평소 지표: `pg_wal_lsn_diff(pg_current_wal_lsn(), redo_lsn)`(지금 죽으면 재생할 양)의 최댓값, `log_checkpoints` 로그의 `distance`, 시험 환경에서 잰 재생 속도.
- 조정: `max_wal_size`·`checkpoint_timeout`을 줄여 최악 재생량을 RTO 안으로. `recovery_prefetch`로 I/O 대기 완화.
- 대가: 체크포인트가 잦아져 평소 쓰기 I/O가 늘고, 체크포인트마다 첫 수정이 전체 페이지(FPW)라 WAL도 는다.
- 대안: 복구를 기다리지 말고 대기 복제본으로 넘긴다.

### 9. 너무 잦은 체크포인트

- 체크포인트가 `checkpoint_timeout`이 아니라 `max_wal_size` 도달로 계속 불린다. 이 경고 자체가 WAL 양으로 불린 체크포인트에만 나온다(`checkpointer.c`). `pg_stat_checkpointer.num_requested` ≫ `num_timed`도 보이지만, 이 카운터엔 수동 `CHECKPOINT`도 섞인다.
- WAL이 늘어나는 이유: `full_page_writes`가 켜져 있으면 체크포인트 뒤 각 페이지의 첫 수정이 페이지 전체(로컬 재현 8185 B vs 평소 71 B)를 기록한다. 체크포인트가 잦을수록 "첫 수정"이 잦아져 WAL이 더 빨리 차고, 그래서 체크포인트가 또 불린다.
- 대처: `max_wal_size`를 키운다(복구 시간과 저울질).
- MySQL 대응 증상: redo 용량이 작아 체크포인트가 못 따라오면 `Threads are unable to reserve space in redo log … Consider increasing innodb_redo_log_capacity.` 경고와 쓰기 스톨.

### 10. 재시작 뒤 긴 롤백

- InnoDB는 redo를 적용한 뒤 연결을 받기 시작하고, 1시간짜리 미완료 `UPDATE`는 백그라운드에서 undo로 **롤백한다**. 그 행들의 락은 롤백이 끝날 때까지 남아 새 갱신이 막힌다.
- 시간: 문서는 중단 전 실행 시간의 **3~4배**가 걸릴 수 있다고 적는다(부하에 따라). 1시간이면 수 시간일 수 있다. 롤백 중인 트랜잭션은 취소할 수 없다.
- 예방: 대량 변경을 keyset 청크의 작은 트랜잭션으로 쪼갠다. 극단적 상황의 `innodb_force_recovery ≥ 3`은 롤백을 건너뛰는 비상 수단이고 정합성 위험이 있다.
