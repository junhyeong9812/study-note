# database/14-isolation-levels-and-anomalies — 격리 수준과 이상 현상: dirty·non-repeatable·phantom·lost update·write skew — 정리 (힌트)

## 해결하는 문제

13번의 I(격리)는 "동시에 돌아도 어떤 직렬 순서와 같다(직렬화 가능)"가 기준이었다.\
그런데 직렬화 가능을 지키려면 비용이 든다. 더 많이 기다리거나(락), 더 자주 실패하고 재시도해야 한다.\
그래서 DB는 **격리 수준**이라는 다이얼을 준다. 약하게 돌리면 빠르지만, 정해진 종류의 이상 현상을 허용한다.

쉬운 예: 병원 당직표다(DDIA 7장의 예).

```text
  규칙: 당직 의사는 항상 1명 이상
  지금: Alice, Bob 둘 다 당직

  Alice: "당직이 2명이네, 나는 빠져도 되겠다"  → 자기 행을 off로
  Bob:   "당직이 2명이네, 나는 빠져도 되겠다"  → 자기 행을 off로   (동시에)

  결과: 당직 0명
```

둘 다 규칙을 확인했다. 둘 다 **서로 다른 행**만 고쳤다. 그런데 규칙이 깨졌다.\
이것이 *write skew*다. PostgreSQL 17의 REPEATABLE READ, MySQL 8.4 InnoDB의 REPEATABLE READ 모두 이것을 막지 못했다(로컬 재현).

똑같은 구조다.\
실무 예: 한 사람의 두 계좌 잔액 합이 0 이상이어야 한다. 두 요청이 각각 다른 계좌에서 출금하면서 "합이 충분하다"를 확인하면, 합이 음수가 된다.

이 노트의 목표는 세 가지다.

- 이상 현상 **이름과 모양**을 시간축 그림으로 구분한다.
- 격리 수준 **이름이 같아도 제품마다 동작이 다르다**는 것을 표로 본다.
- 내 코드의 패턴이 어느 이상 현상에 걸리는지 보고, 고치는 법을 고른다.

## 동작·원리

### 1. 이상 현상 카탈로그 — 시간축으로 본다

표기: `r1[x]` = T1이 x를 읽음, `w2[x]` = T2가 x를 씀, `c1` = T1 커밋, `a1` = T1 중단(Berenson 외 1995).

```text
  P0 더티 쓰기 (dirty write)       w1[x] ... w2[x] ... (c1 또는 a1)
     T1이 쓰고 끝나기 전에 T2가 덮어쓴다. T1이 롤백하면 무엇으로 되돌리나?

  P1 더티 읽기 (dirty read)        w1[x] ... r2[x] ... (c1 또는 a1)
     T2가 T1의 커밋 안 된 값을 읽는다. T1이 롤백하면 T2는 없던 값을 본 셈이다.

  P2 반복 불가능 읽기               r1[x] ... w2[x] ... (c1 또는 a1)
     (non-repeatable / fuzzy)      엄격 해석 A2: r1[x] ... w2[x] ... c2 ... r1[x] ... c1
                                   같은 행을 두 번 읽었는데 값이 다르다.

  P3 팬텀 (phantom)                r1[P] ... w2[y in P] ... (c1 또는 a1)
                                   엄격 해석 A3: r1[P] ... w2[y in P] ... c2 ... r1[P] ... c1
     같은 조건 P로 두 번 조회했는데 행 집합이 다르다(새 행이 끼었다).

  P4 갱신 손실 (lost update)        r1[x] ... w2[x] ... w1[x] ... c1
     T1이 읽은 뒤 T2가 쓴 것을, T1이 옛 값 기준으로 덮어써 없앤다.

  A5A 읽기 skew                    r1[x] ... w2[x] ... w2[y] ... c2 ... r1[y]
     x는 옛 값, y는 새 값을 읽어 둘의 관계(예: 합계)가 틀려 보인다.

  A5B 쓰기 skew (write skew)       r1[x] ... r2[y] ... w1[y] ... w2[x] ... (c1, c2)
     둘 다 x·y를 읽고 확인한 뒤 서로 다른 것을 써서, x·y 사이 규칙이 깨진다.
```

- *이상 현상(anomaly/phenomenon)*: 직렬 실행에서는 나올 수 없는 결과다.
- Berenson 외(1995)는 SQL 표준의 정의(P1~P3)가 모호하고 부족하다고 비판했다. 그리고 P0·P4·A5A·A5B를 추가해 격리 수준을 다시 구분했다.
  - *넓은 해석(broad, P)과 엄격 해석(strict, A)*: P는 "이런 순서가 시작되기만 해도" 금지하는 넓은 정의다. A는 실제로 이상한 결과가 난 경우(예: 다시 읽었더니 달랐다)만 가리키는 좁은 정의다. 논문은 넓은 해석이 필요하다고 본다.
  - "P0(더티 쓰기)는 모든 격리 수준에서 막아야 한다"(Remark 3). 롤백을 할 수 없게 되기 때문이다.

### 2. SQL 표준의 표 — "무엇을 금지하나"로 정의한다

| 격리 수준 | 더티 읽기 | 반복 불가능 읽기 | 팬텀 | 직렬화 이상 |
|---|---|---|---|---|
| READ UNCOMMITTED | 허용 | 가능 | 가능 | 가능 |
| READ COMMITTED | 금지 | 가능 | 가능 | 가능 |
| REPEATABLE READ | 금지 | 금지 | 가능 | 가능 |
| SERIALIZABLE | 금지 | 금지 | 금지 | 금지 |

- 표준 표는 앞의 세 현상(더티·반복 불가능·팬텀)만 다룬다. "직렬화 이상" 열은 PostgreSQL 문서 표 13.1이 덧붙인 것이다. SERIALIZABLE은 현상 목록이 아니라 "어떤 직렬 순서와 같은 효과"로 정의된다(13.2).
- 표준은 **각 수준에서 일어나면 안 되는 것**만 정한다. 더 강하게 막는 것은 허용된다(PostgreSQL 13.2).
- 그래서 같은 이름이라도 제품마다 실제로 막는 범위가 다르다.
- *스냅샷 격리(SI, Snapshot Isolation)*는 표준 표에 없다. 트랜잭션이 시작 시점의 스냅샷을 읽고, 같은 행을 동시에 쓰면 먼저 커밋한 쪽이 이긴다(first-committer-wins). Berenson 외는 SI가 READ COMMITTED보다 강하지만 **락 기반 REPEATABLE READ와는 비교 불가**라고 보였다(Remark 9).
  - SI는 팬텀(A3)을 막지만 write skew(A5B)를 허용한다.
  - 락 기반 REPEATABLE READ는 write skew를 막지만 팬텀을 허용한다.

### 3. 제품별 실제 동작

```text
                    PostgreSQL 17                          MySQL 8.4 InnoDB
  READ UNCOMMITTED  READ COMMITTED와 똑같이 동작              더티 읽기 허용
  READ COMMITTED    ★기본. 문장마다 새 스냅샷                  문장(일관 읽기)마다 새 스냅샷
                    UPDATE는 최신 커밋 버전을 기다렸다 다시 평가   갭 락 거의 없음 → 팬텀 가능
  REPEATABLE READ   = 스냅샷 격리                             ★기본. 첫 읽기 때 스냅샷
                    첫 문장 시점 스냅샷, 팬텀도 안 보임            잠금 읽기·UPDATE는 "최신" 버전 + 갭·next-key 락
                    같은 행 동시 수정 → 40001로 실패             같은 행 동시 수정 → 기다린 뒤 최신 값에 덮어씀
  SERIALIZABLE      = SSI (스냅샷 + 위험 구조 감시)               RR + 자동 커밋이 꺼져 있으면
                    rw 의존 두 개 연속 → 한쪽 40001               일반 SELECT를 SELECT … FOR SHARE로 바꿈
```

- PostgreSQL의 REPEATABLE READ는 문서가 직접 "학계에서 스냅샷 격리라고 부르는 기법"이라고 쓴다(13.2.2).
- PostgreSQL의 SERIALIZABLE은 *SSI(Serializable Snapshot Isolation)*다. 읽은 범위를 `SIRead` 술어 락으로 기록한다. 이 락은 **아무도 막지 않는다**. 의존 관계만 표시한다(13.2.3).
  - SSI의 관찰: SI의 모든 이상은 의존 그래프의 사이클이고, 그 사이클에는 **rw 충돌 간선 두 개가 연달아 있는 위험 구조**가 있다(`README-SSI`).

```text
      Tin ──rw──> Tpivot ──rw──> Tout         이 모양 + Tout이 먼저 커밋 → 하나를 취소한다
      (거짓 양성 가능: 위험 구조가 실제 사이클의 일부가 아닐 때도 취소)
```

- MySQL 8.4 InnoDB RR의 스냅샷은 보통 첫 일관 읽기 때 만든다. `START TRANSACTION WITH CONSISTENT SNAPSHOT`이면 시작할 때 만든다(15.3.1).
- MySQL 8.4 InnoDB REPEATABLE READ의 함정: 일반 `SELECT`는 스냅샷을 보고, `SELECT … FOR UPDATE`·`UPDATE`는 **최신 상태**를 본다. 문서도 한 트랜잭션에서 둘을 섞지 말라고 권한다(17.7.2.1).

### 4. 로컬 재현 결과 (예시, PostgreSQL 17.11 · MySQL 8.4.10)

두 세션 A·B를 0.3초 간격으로 겹쳐 실행했다.

- 갱신 손실: 재고 10 → 둘 다 읽고 → 둘 다 `UPDATE … SET qty = 9`(애플리케이션이 계산한 값)
- write skew: 당직 2명 → 둘 다 `count(*)` → 각자 자기 행을 off

| 이상 현상 | PG RC | PG RR | PG SER | MY RC | MY RR | MY SER |
|---|---|---|---|---|---|---|
| 더티 읽기 (RU에서) | 안 보임(RU=RC) | — | — | **보임**(RU) | — | — |
| 반복 불가능 읽기 | **보임** 100→0 | 안 보임 | — | **보임** | 안 보임 | — |
| 팬텀 (일반 SELECT) | **보임** 1→2 | 안 보임 | — | **보임** | 안 보임 | — |
| 일반 SELECT 뒤 `FOR UPDATE`(읽기 섞기) | — | — | — | — | **다름** 1→2 | — |
| 갱신 손실 (qty=9) | **발생** 최종 9 | B: 40001 | B: 40001 | **발생** 9 | **발생** 9 | B: 1213 |
| write skew | **발생** 0명 | **발생** 0명 | B: 40001 → 1명 | **발생** 0명 | **발생** 0명 | B: 1213 → 1명 |

- "—"는 이번에 재현하지 않은 칸이다.
- PG RR의 갱신 손실 실패 메시지: `could not serialize access due to concurrent update`.
- PG SER의 write skew 실패 메시지: `could not serialize access due to read/write dependencies among transactions`, `Reason code: Canceled on identification as a pivot, during write.`
- MY SER은 두 세션의 `SELECT`가 공유 락을 잡고, 둘 다 쓰려다 교착이 나서 한쪽이 `ERROR 1213 (40001): Deadlock found when trying to get lock; try restarting transaction`으로 롤백됐다.
- 같은 갱신 손실 시나리오라도 `UPDATE … SET qty = qty - 1`(원자적 갱신)로 쓰면 PG RC와 MY RR 모두 최종 8로 **정확**했다. 갱신 손실은 "읽은 값을 애플리케이션에서 계산해 다시 쓸 때" 생긴다.

### 5. 무엇이 무엇을 막나 — 고치는 도구

```text
  문제                        도구 (가벼운 것부터)
  갱신 손실                    ① 원자적 UPDATE: SET qty = qty - 1 WHERE qty >= 1
                             ② 조건부 UPDATE: ... WHERE id = ? AND version = ?  (낙관적, 17번)
                             ③ SELECT ... FOR UPDATE 로 읽을 때 잠금 (비관적, 15번)
                             ④ PG REPEATABLE READ 이상: 자동으로 40001 → 재시도
  write skew                  ① 제약으로 선언할 수 있으면 선언 (UNIQUE, EXCLUDE, CHECK)
                             ② 확인에 쓴 행들을 FOR UPDATE로 잠금 (충돌을 같은 행으로 모은다)
                             ③ (PG) 행이 없으면 잠글 게 없다 → 잠글 행을 만들어 둔다 (충돌 구체화)
                             ④ SERIALIZABLE + 재시도
  읽기 skew (보고서 불일치)     긴 읽기를 하나의 스냅샷으로 (PG RR, READ ONLY)
```

- ③의 "잠글 게 없다"는 PostgreSQL 행 잠금 기준이다. MySQL 8.4 InnoDB RR에서는 범위 잠금 읽기가 **빈 범위의 갭**도 잠근다(17.7.1 Gap Locks). 그래서 잠금용 행은 한 방법일 뿐 필수는 아니다.
- *충돌 구체화(materializing conflicts)*: 잠글 행이 없는 조건("그 시간대 예약이 없으면 INSERT")에, 잠금 대상으로 쓸 행(시간대 행)을 미리 만들어 두는 기법이다(DDIA 7장).

## 쓰이는 자료구조·알고리즘

- **이상 현상 분류 = 연산 순서 패턴** — `r1[x] … w2[x] … w1[x]`처럼 읽기·쓰기 순서의 문법으로 정의한다(Berenson).
- **의존 그래프와 사이클** — wr·ww·rw 의존을 간선으로 두고 사이클이면 직렬화 불가다. PostgreSQL SSI는 사이클 전체 대신 "rw 두 개 연속" 구조만 찾는다(`README-SSI`). [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
- **스냅샷** — "이 트랜잭션에 보이는 트랜잭션 id 집합". 버전마다 만든 트랜잭션 id를 비교해 보일지 정한다(16번).
- **술어 락(SIRead)** — 읽은 튜플·페이지·테이블 단위로 "여기를 읽었다"를 기록한다. 메모리가 모자라면 더 굵은 단위로 합친다(PostgreSQL 13.2.3).
- **갭·next-key 락** — InnoDB가 인덱스 레코드 사이 **틈**을 잠가 삽입을 막는다(15번).

## 적용 — 풀어나가는 법

### 1. 격리 수준 설정

```sql
-- PostgreSQL 17
BEGIN ISOLATION LEVEL REPEATABLE READ;           -- 트랜잭션 단위
SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL SERIALIZABLE;
SHOW default_transaction_isolation;              -- read committed

-- MySQL 8.4
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;  -- 다음 트랜잭션 하나에만
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
SELECT @@transaction_isolation;                  -- REPEATABLE-READ
```

- MySQL의 `SET TRANSACTION`(`SESSION`·`GLOBAL` 없이)은 **다음 트랜잭션 하나**에만 적용된다(15.3.7).

### 2. 판단 순서

1. 코드에서 "읽고 → 판단하고 → 쓰는" 트랜잭션을 찾는다.
2. 쓰는 대상이 **읽은 행과 같은가?**
   - 같다 → 갱신 손실 후보. 원자적 UPDATE나 버전 컬럼으로 바꾼다.
   - 다르다(읽은 것은 집합, 쓰는 것은 다른 행) → write skew 후보. 제약 선언, `FOR UPDATE`, SERIALIZABLE 중 고른다.
3. 판단에 쓴 조건이 **행이 없음**("아직 예약이 없으면")이면 잠글 행이 없다. 제약(UNIQUE·EXCLUDE)이나 충돌 구체화, SERIALIZABLE이 필요하다.

### 3. SERIALIZABLE을 쓰면 재시도는 필수다

```java
// PostgreSQL: 40001(serialization_failure), 40P01(deadlock_detected)은 트랜잭션 전체를 재시도
<T> T inTx(Supplier<T> work) {
    for (int attempt = 1; ; attempt++) {
        try {
            return tx.execute(status -> work.get());      // 매번 새 트랜잭션, 판단 로직까지 다시
        } catch (PessimisticLockingFailureException e) {    // Spring: 40001·40P01·1213 계열의 부모
            if (attempt >= 5) throw e;
            sleep(backoffWithJitter(attempt));
        }
    }
}
```

- PostgreSQL 문서: 재시도는 "어떤 SQL을 낼지, 어떤 값을 쓸지 정하는 로직까지 포함해" 트랜잭션 전체를 다시 해야 한다. 그래서 DB가 자동 재시도를 제공하지 않는다(13.5).
- Spring 6.x 기본 번역 경로(사용자 `sql-error-codes.xml`이 없을 때): `SQLExceptionSubclassTranslator` → `SQLStateSQLExceptionTranslator`. `40001`은 `CannotAcquireLockException`, 그 밖의 `40`(PostgreSQL `40P01` 등)은 `PessimisticLockingFailureException`이 된다. MySQL `1213`은 Connector/J가 SQLSTATE `40001`로 주므로 `CannotAcquireLockException`이다(56번 §2).
  - 사용자 `sql-error-codes.xml`을 두면 구형 `SQLErrorCodeSQLExceptionTranslator`가 쓰여 `40001` → `CannotSerializeTransactionException`, `40P01`·`1213` → `DeadlockLoserDataAccessException`이 된다. 이 두 클래스는 6.0.3부터 deprecated다.
  - 어느 경로든 부모인 `PessimisticLockingFailureException`으로 잡으면 된다.
- 읽기만 하는 트랜잭션은 `READ ONLY`로 선언한다. PostgreSQL SSI가 술어 락을 일찍 풀 수 있다(13.2.3). `SERIALIZABLE READ ONLY DEFERRABLE`은 안전한 스냅샷을 기다렸다가 시작해 직렬화 실패가 나지 않는다.

### 4. 관찰

```sql
-- PostgreSQL: SSI가 잡은 술어 락
SELECT locktype, relation::regclass, page, tuple, mode FROM pg_locks WHERE mode = 'SIReadLock';

-- MySQL: 현재 잡힌 레코드·갭 락
SELECT ENGINE_TRANSACTION_ID, OBJECT_NAME, INDEX_NAME, LOCK_TYPE, LOCK_MODE, LOCK_DATA
FROM performance_schema.data_locks;
```

## 장애 시나리오와 대처

### 1. 당직이 0명이 됐다 (⚠ SI에서 write skew)

- **현상**: "최소 1명" 규칙을 코드가 확인했는데 당직자가 0명이 됐다.
- **보이는 형태**: 오류가 없다. 두 요청 모두 성공 응답. 데이터만 규칙을 어긴다. 로컬 재현에서 PG RC·RR, MY RC·RR 모두 최종 0명.
- **원인**: 두 트랜잭션이 같은 집합을 읽고(`count(*) = 2`) 서로 다른 행을 고쳤다. 같은 행을 쓰지 않으므로 스냅샷 격리의 "같은 행 동시 수정" 검사에 걸리지 않는다.
- **대처**
  - 확인한 행들을 잠근다: `SELECT … WHERE on_call FOR UPDATE`. 로컬 재현(PG RC)에서 B가 A의 커밋을 기다린 뒤 다시 평가해 1명을 보고 멈췄다. 최종 1명.
  - 또는 SERIALIZABLE + 재시도. PG는 40001, MySQL은 1213으로 한쪽이 실패했다.
  - 테스트: 두 세션을 겹쳐 돌리는 동시성 테스트를 만든다. 단일 스레드 테스트로는 절대 재현되지 않는다.

### 2. 잔액 합이 음수가 됐다 (⚠ write skew, 여러 계좌)

- **현상**: "두 계좌 합 ≥ 0"을 확인하고 출금했는데 합이 음수다.
- **보이는 형태**: 오류 없음. 감사 쿼리에서 발견된다.
- **원인**: T1은 계좌 X에서, T2는 계좌 Y에서 출금했다. 둘 다 X+Y를 읽어 충분하다고 판단했다. 쓰는 행이 달라 SI는 통과시킨다.
- **대처**: 두 계좌 행을 **id 순서로** `FOR UPDATE` 잠근 뒤 확인한다(교착 방지는 15번). 또는 합계를 담는 상위 행(고객 행)을 두고 그것을 잠근다(충돌 구체화). SERIALIZABLE도 된다.

### 3. 재고가 두 번 팔렸는데 한 번만 줄었다 (⚠ RC에서 lost update)

- **현상**: 판매 2건, 재고 감소 1.
- **보이는 형태**: 오류 없음. 로컬 재현 PG RC·MY RC·**MY RR** 모두 최종 9(정답 8).
- **원인**: 애플리케이션이 `SELECT qty`로 읽고 `qty - 1`을 계산해 `UPDATE … SET qty = 9`로 썼다. 두 번째 쓰기가 첫 번째를 덮었다.
  - MySQL 8.4 InnoDB의 REPEATABLE READ(기본)도 이것을 막지 않는다. UPDATE는 최신 행을 잠그고 덮어쓴다.
  - PostgreSQL REPEATABLE READ는 두 번째 쓰기를 40001로 실패시킨다.
- **대처**: `UPDATE item SET qty = qty - 1 WHERE id = ? AND qty >= 1`로 바꾸고 영향 행 수를 확인한다(재현에서 최종 8). JPA면 `@Version` 낙관적 락(17번).

### 4. SERIALIZABLE로 올렸더니 실패가 폭증한다

- **현상**: 정합성 문제를 막으려고 SERIALIZABLE로 올렸더니 오류율이 오른다.
- **보이는 형태**: PG `ERROR: could not serialize access due to read/write dependencies among transactions`(40001). MySQL은 `ERROR 1213`이 늘고, 읽기 쿼리도 락 대기(`SHOW ENGINE INNODB STATUS`의 대기 목록)가 생긴다.
- **원인**
  - 재시도 로직이 없거나 불완전하다.
  - PG: 순차 스캔은 **테이블 전체** 술어 락을 잡는다. 락 메모리가 모자라 페이지 락이 테이블 락으로 합쳐지면 실패가 는다(13.2.3).
  - MySQL: 일반 SELECT가 공유 락이 되어 쓰기와 서로 막는다.
- **대처**: 트랜잭션 전체 재시도(백오프+지터). 트랜잭션을 짧게, 읽기 전용은 `READ ONLY`. PG는 인덱스를 쓰게 해 술어 락을 좁히고, 필요하면 `max_pred_locks_per_transaction`을 늘린다. 전체를 올리지 말고 **문제 트랜잭션만** SERIALIZABLE로 두는 것도 방법이다. 단 PostgreSQL SSI는 모든 참여 트랜잭션이 SERIALIZABLE일 때만 보장한다(13.2.3 "consistent use").

### 5. MySQL: 방금 센 행 수와 UPDATE된 행 수가 다르다

- **현상**: REPEATABLE READ 트랜잭션에서 `SELECT count(*)`는 1인데, 이어서 `UPDATE … WHERE …`가 2행을 바꿨다.
- **보이는 형태**: 로컬 재현(MY RR): 같은 조건으로 일반 `SELECT`는 1, `SELECT … FOR UPDATE`는 2.
- **원인**: 일반 SELECT는 트랜잭션 첫 읽기 때 만든 스냅샷을 본다. 잠금 읽기·UPDATE·DELETE는 최신 커밋 상태를 본다. 그 사이에 다른 트랜잭션이 행을 넣고 커밋했다.
- **대처**: 판단에 쓸 읽기는 처음부터 `FOR UPDATE`/`FOR SHARE`로 한다. 한 트랜잭션에서 두 종류를 섞지 않는다(문서 권고). 영향 행 수를 검사한다.

## 핵심 문장

- 격리 수준은 "직렬화 가능"에서 얼마나 물러설지 고르는 다이얼이다. 표준은 수준별로 **금지할 현상**만 정하므로 더 강한 구현도 허용된다.
- 이상 현상은 연산 순서 패턴이다. 갱신 손실은 같은 행을 읽고-계산하고-쓸 때, write skew는 집합을 읽고 다른 행을 쓸 때 생긴다.
- PostgreSQL 17의 RR은 스냅샷 격리라 팬텀과 갱신 손실은 막지만 write skew는 허용한다. SERIALIZABLE(SSI)은 rw 의존 두 개 연속 구조를 찾아 40001로 취소한다.
- MySQL 8.4 InnoDB의 기본 RR은 일반 SELECT는 스냅샷, 잠금 읽기·UPDATE는 최신 상태를 본다. 읽고-계산하고-쓰는 갱신 손실을 막지 않는다.
- 고치는 도구는 원자적 UPDATE → 버전 컬럼 → `FOR UPDATE` → 제약 선언 → SERIALIZABLE + 재시도 순으로 고른다. 재시도는 판단 로직까지 포함한 트랜잭션 전체다.

## 관련 주제·근거

- 선행: database `13-transactions-acid` — 직렬화 가능성과 충돌 그래프 → [../13-transactions-acid/2-summary.md](../13-transactions-acid/2-summary.md)
- 후속·연결
  - database `15-two-phase-locking-and-deadlock` → [../15-two-phase-locking-and-deadlock/2-summary.md](../15-two-phase-locking-and-deadlock/2-summary.md)
  - database `16-mvcc` → [../16-mvcc/2-summary.md](../16-mvcc/2-summary.md)
  - database `17-occ-and-timestamp-ordering` → [../17-occ-and-timestamp-ordering/2-summary.md](../17-occ-and-timestamp-ordering/2-summary.md)
  - database `18-app-level-concurrency-patterns` → [../18-app-level-concurrency-patterns/2-summary.md](../18-app-level-concurrency-patterns/2-summary.md)
  - [engineering/engineering-axes/concurrency.md](../../engineering/engineering-axes/concurrency.md) — 동시성 도구 선택의 개념 정리
  - 문법 쪽: [sql/56 격리 수준·읽기 이상·MVCC](../../../languages/sql/syntax/56-isolation-levels-read-phenomena-mvcc/2-summary.md) · [sql/57 명시적 락·교착](../../../languages/sql/syntax/57-explicit-locking-and-deadlock/2-summary.md)
  - [api-design/03-stock-deduct](../../api-design/03-stock-deduct/2-summary.md) — 재고 차감의 갱신 손실
- 논문·교재
  - H. Berenson, P. Bernstein, J. Gray, J. Melton, E. O'Neil, P. O'Neil, "A Critique of ANSI SQL Isolation Levels", SIGMOD 1995 — P0~P4, A5A 읽기 skew, A5B 쓰기 skew, Remark 3(P0는 모든 수준에서 금지), Remark 8·9(RC ≪ SI, RR »« SI)
  - M. Kleppmann, 『Designing Data-Intensive Applications』 1판 7장 "Weak Isolation Levels" — 당직 의사 예, 충돌 구체화
  - M. J. Cahill 외, "Serializable Isolation for Snapshot Databases", SIGMOD 2008 (PostgreSQL `README-SSI` 경유, 원문 미열람)
- PostgreSQL 17 문서·소스
  - 13.2 Transaction Isolation(표 13.1, RU=RC, RR=SI, SSI·SIReadLock, 성능 권고) <https://www.postgresql.org/docs/17/transaction-iso.html>
  - 13.5 Serialization Failure Handling(40001·40P01 재시도, 트랜잭션 전체) <https://www.postgresql.org/docs/17/mvcc-serialization-failure-handling.html>
  - SET TRANSACTION <https://www.postgresql.org/docs/17/sql-set-transaction.html> · 13.4 Data Consistency Checks at the Application Level <https://www.postgresql.org/docs/17/applevel-consistency.html>
  - `src/backend/storage/lmgr/README-SSI`(rw-conflict, dangerous structure, pivot, 거짓 양성) <https://github.com/postgres/postgres/blob/REL_17_STABLE/src/backend/storage/lmgr/README-SSI>
- MySQL 8.4 Reference Manual
  - 17.7.2.1 Transaction Isolation Levels(RR 기본, 잠금·비잠금 읽기 혼용 비권장, SERIALIZABLE은 SELECT → FOR SHARE) <https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html>
  - 17.7.2.3 Consistent Nonlocking Reads · 17.7.2.4 Locking Reads · 17.7.4 Phantom Rows · 15.3.7 SET TRANSACTION
- Spring Framework 6.2.x `spring-jdbc` 소스: `JdbcAccessor`(사용자 `sql-error-codes.xml`이 없으면 `SQLExceptionSubclassTranslator`), `SQLStateSQLExceptionTranslator`(`40001` → `CannotAcquireLockException`, 그 밖의 `40` → `PessimisticLockingFailureException`) <https://github.com/spring-projects/spring-framework/tree/6.2.x/spring-jdbc/src/main/java/org/springframework/jdbc/support> · 구형 `sql-error-codes.xml`(PostgreSQL 40001·40P01, MySQL 1213), `CannotSerializeTransactionException`(6.0.3 deprecated) <https://github.com/spring-projects/spring-framework/blob/main/spring-jdbc/src/main/resources/org/springframework/jdbc/support/sql-error-codes.xml>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10, 전용 DB `w12`, 두 세션 0.3초 간격): 수준별 더티·반복 불가능·팬텀 읽기, 읽고-계산-쓰기 갱신 손실, 당직 write skew, `FOR UPDATE`로 write skew 방지, 원자적 UPDATE
