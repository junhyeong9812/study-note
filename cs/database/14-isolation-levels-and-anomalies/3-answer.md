# database/14-isolation-levels-and-anomalies — 정답

## 정답

### 1. 갱신 손실 vs write skew

```text
  P4 갱신 손실:  r1[x] ... w2[x] ... w1[x] ... c1
    T1: 읽기 qty=10 ─────────────────── 쓰기 qty=9 ── 커밋
    T2:           읽기 qty=10 ── 쓰기 qty=9 ── 커밋
    → 두 번 팔았는데 9

  A5B write skew: r1[x] ... r2[y] ... w1[y] ... w2[x] ... (c1, c2)
    T1: count=2 ────────── Alice off ── 커밋
    T2:       count=2 ───────── Bob off ── 커밋
    → 당직 0명
```

- 결정적 차이: 갱신 손실은 **같은 행**을 둘 다 쓴다. write skew는 **다른 행**을 쓴다. 공통점은 "읽은 것에 근거해 판단한 뒤 쓴다"는 것이다.
- 같은 행을 쓰므로 갱신 손실은 행 락·"같은 행 동시 수정" 검사로 잡을 수 있다. write skew는 그것으로 안 잡힌다.

### 2. 금지 목록 방식의 결과

- 제품 차이: 표준은 최소한만 정하므로 더 강하게 구현해도 된다. PostgreSQL의 RR은 팬텀도 막는다. 같은 이름이 제품마다 다른 보장을 뜻하게 된다.
- Berenson 외 비판: 현상 정의(P1~P3)가 모호하고, 더티 쓰기(P0)·갱신 손실(P4)·읽기/쓰기 skew(A5A/A5B)를 빠뜨렸다. 스냅샷 격리 같은 실제 구현을 표준 표로 분류할 수 없다.
- 모든 수준에서 금지해야 할 것: **P0 더티 쓰기**(Remark 3). 막지 않으면 롤백을 올바르게 할 수 없다.

### 3. 읽고-계산하고-쓰기 (로컬 재현)

| 환경 | 결과 |
|---|---|
| PostgreSQL 17 RC | 둘 다 성공, 최종 9 — **갱신 손실** |
| PostgreSQL 17 RR | 나중 세션이 `ERROR: could not serialize access due to concurrent update`(40001), 최종 9 = 한 건만 반영, 실패한 쪽은 재시도해야 함 |
| MySQL 8.4 RR (기본) | 둘 다 성공, 최종 9 — **갱신 손실**. UPDATE는 최신 행을 잠그고 덮어쓴다 |
| MySQL 8.4 SERIALIZABLE | 두 SELECT가 공유 락 → 둘 다 쓰려다 교착 → 한쪽 `ERROR 1213`, 최종 9, 실패한 쪽 재시도 |

- `UPDATE … SET qty = qty - 1`로 쓰면 PG RC·MY RR 모두 최종 8(정답)이었다.

### 4. 당직 write skew

- PostgreSQL 17 RR: 둘 다 성공, **0명**. 서로 다른 행을 써서 SI의 같은 행 검사에 안 걸린다.
- PostgreSQL 17 SERIALIZABLE: 나중 세션이 `ERROR: could not serialize access due to read/write dependencies among transactions`, `DETAIL: Reason code: Canceled on identification as a pivot, during write.`, `HINT: The transaction might succeed if retried.` → 최종 1명.
- MySQL 8.4 SERIALIZABLE: `ERROR 1213 (40001): Deadlock found when trying to get lock; try restarting transaction` → 최종 1명.
  - 이유: 자동 커밋이 꺼진 트랜잭션의 일반 SELECT가 `FOR SHARE`로 바뀐다. 두 세션이 둘 다 공유 락을 쥔 채 상대가 공유 락을 쥔 행에 배타 락을 요청해 교착이 된다. InnoDB 교착 탐지가 한쪽을 롤백한다.

### 5. SI vs 락 기반 RR

| | 팬텀(A3) | write skew(A5B) |
|---|---|---|
| 스냅샷 격리(PostgreSQL RR) | 막는다 — 스냅샷이라 새 행이 안 보인다 | 허용 |
| 락 기반 RR(읽은 행에 락, 술어 락 없음) | 허용 — 읽은 행만 잠가 새 행 삽입을 못 막는다 | 막는다 — 읽은 행에 쥔 공유 락이 상대의 쓰기를 막는다(둘 다 쥐면 교착 → 한쪽 롤백, MySQL SERIALIZABLE 재현과 같은 모양) |

- 서로 상대가 허용하는 것을 막으므로 어느 쪽도 다른 쪽보다 강하지 않다 → **비교 불가**(Remark 9).

### 6. SSI가 찾는 것

- 의존 그래프에서 **rw 충돌 간선 두 개가 연달아 있는 "위험 구조"** `Tin → Tpivot → Tout`를 찾는다. PostgreSQL은 여기에 Tout이 Tpivot·Tin보다 먼저 커밋했다는 조건까지 맞을 때 취소한다(`README-SSI`). SI의 모든 이상은 이런 구조를 포함한 사이클이라는 관찰에 기댄다(`README-SSI`).
- 대가: **거짓 양성**. 위험 구조가 실제 사이클의 일부가 아니어도 취소할 수 있다. 문서도 "진짜 직렬 실행이라면 나지 않았을 오류"가 날 수 있다고 한다.
- `SIReadLock`은 아무도 막지 않는다. 의존을 표시하는 용도라 교착의 원인이 되지도 않는다(13.2.3).

### 7. MySQL: 센 것과 바꾼 것이 다르다

- 일반 `SELECT`는 트랜잭션의 **첫 읽기 때 만든 스냅샷**을 본다(`START TRANSACTION WITH CONSISTENT SNAPSHOT`이면 시작 때). 그 뒤 다른 트랜잭션이 `id = 3`을 넣고 커밋했다.
- `UPDATE`(그리고 `SELECT … FOR UPDATE`)는 **최신 커밋 상태**를 읽고 잠근다. 그래서 새 행까지 2행을 바꿨다. 로컬 재현에서도 일반 SELECT 1, `FOR UPDATE` 2였다.
- 고치는 법: 판단에 쓰는 읽기를 처음부터 `SELECT … FOR UPDATE`로 한다(next-key 락이 범위 삽입도 막는다). 한 트랜잭션에서 잠금·비잠금 읽기를 섞지 않는다. UPDATE의 영향 행 수를 검사한다.

### 8. 두 계좌 합

- 격리 수준을 안 올리는 방법
  1. 두 계좌 행을 **id 순서로** `SELECT … FOR UPDATE`로 잠근 뒤 합을 확인하고 출금한다. 같은 행을 잠그므로 두 요청이 줄을 선다. 순서를 지키면 이 두 행을 역순으로 잡는 교착은 피한다(다른 락까지 얽힌 교착은 별개다).
  2. 충돌 구체화: 고객 단위 행(예: `customer`의 합계·잠금용 행)을 두고 그것을 잠근다. 또는 합계를 그 행에 두고 `CHECK`로 선언한다.
- SERIALIZABLE로 고치면: **트랜잭션 전체 재시도**(판단 로직 포함, 백오프)를 반드시 함께 둔다. PostgreSQL은 40001, MySQL은 1213으로 한쪽이 실패하기 때문이다.

### 9. SERIALIZABLE 실패 폭증

- SQLSTATE `40001`(serialization_failure).
- 원인 후보
  - 재시도 로직이 없어 실패가 그대로 사용자 오류가 된다.
  - 트랜잭션이 길고 많이 읽는다 → 겹치는 rw 의존이 많다.
  - 순차 스캔은 테이블 전체 술어 락을 잡는다. 술어 락 메모리가 모자라 페이지 락이 테이블 락으로 합쳐지면 실패율이 오른다.
- 줄이는 법(13.2.3 권고)
  - 트랜잭션 전체 재시도 + 백오프.
  - 읽기 전용은 `READ ONLY`로 선언. 긴 보고서는 `SERIALIZABLE READ ONLY DEFERRABLE`.
  - 트랜잭션을 짧게, 커넥션 수를 풀로 제한, `idle in transaction`을 오래 두지 않기.
  - 인덱스를 쓰게 해 술어 락 범위를 좁힌다. 필요하면 `max_pred_locks_per_transaction` 등을 늘린다.
  - SERIALIZABLE 덕분에 필요 없어진 `FOR UPDATE`·명시적 락을 걷어 낸다.
