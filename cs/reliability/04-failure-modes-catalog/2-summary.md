# reliability/04-failure-modes-catalog — 실패 카탈로그 F-01~F-25: 증상·뿌리·막는 장치 — 정리 (힌트)

## 해결하는 문제

사고 회고를 모아 보면 같은 실패가 이름만 바꿔 다시 나온다.
"잔액이 가끔 틀린다", "포인트가 덜 쌓였다", "재고가 마이너스"는 모두 같은 뿌리(동시 갱신 유실)일 수 있다.
뿌리에 이름이 없으면 매번 처음 보는 사고처럼 조사하고, 매번 그 자리만 고친다.

쉬운 예: 병원의 진단명이다.
- "기침·열·근육통"을 증상 목록으로만 보면 매번 새로 고민한다. "독감"이라는 이름이 붙으면 검사·처방·예방(백신)이 한 묶음으로 따라온다.

똑같은 구조다.\
실무 예: 설계 리뷰에서 "이 경로에 F-01(lost update)·F-11(중복 소비)·F-16(타임아웃 역전)이 있나?"를 번호로 묻는다. 있으면 "무엇이 막나?"에 **장치 이름**(버전 컬럼·유니크 제약·데드라인 전파)으로 답해야 한다.

기초(25개 항목 각각의 증상·뿌리·실사건·막는 법, 세 묶음의 공통점)는 원본 [ops-patterns/failure-modes](../../ops-patterns/failure-modes/2-summary.md) 「A」「B」「C」 절에 있다. 이 노트는 카탈로그를 **쓰는 법**(색인·분류·판정)을 세우고, 대표 항목 둘(F-01·F-11)을 실제 DB에서 재현한다. 각 항목의 원리는 해당 영역 노트로 잇는다.

## 동작·원리

### 1. 한 항목을 읽는 네 칸과 판정

```text
 증상      겉으로 보이는 것   "에러 없음 · 간헐적 · 갈수록 느려짐"
   ↓
 뿌리      동작 원리          MVCC 스냅샷 · 두 장군 문제 · GC 멈춤 · 롤링 배포의 두 버전 공존
   ↓
 현장      같은 구조가 우리에게 있나   "load-modify-save를 하나?" "복제본에서 멱등 조회를 하나?"
   ↓
 막는 것   이름 붙은 장치인가 ──예──> 막힘 (버전 컬럼, 유니크 제약, fencing token, DLQ)
            └──아니오(문장뿐)──> 뚫림 ("순서를 지킨다", "멱등하다", "flush를 꼭 한다")
```

- 판정 규칙(원본의 핵심): **막는 것에 이름을 댈 수 있으면 막히고, 계약 문장뿐이면 뚫린다.** 문장은 사람의 주의력에 기대고, 부하가 걸리는 날 지켜지지 않는다.
- *이름 붙은 장치*: 지키지 않으면 **시스템이 거부**하는 것. 제약(유니크·외래 키·CHECK), 조건부 쓰기(버전·토큰 비교), 타입·모듈 경계, 자동 검사(아키텍처 테스트·대조 배치).
- 장치가 있어도 **그 장치가 실제로 도는지**를 다시 확인한다. 필드는 있는데 제약이 없거나(F-11), 대조 배치가 며칠째 안 도는 경우(F-21)가 흔하다.

### 2. 세 묶음과 공통점

| 묶음 | 범위 | 공통점(원본) |
|---|---|---|
| A. 동시성·DB (F-01~F-08) | 한 DB 안 | 부하가 걸릴 때만 틀린다, 에러 없이 조용히 틀린다, 늘려서 풀리지 않는다, "정상 동작"이 원인이다 |
| B. 분산·비동기 (F-09~F-19) | 프로세스·네트워크가 갈릴 때 | 두 장군 문제가 뿌리, 선언과 장치를 혼동하기 쉽다, 한 건이 전체를 막는다 |
| C. 결제 도메인 (F-20~F-25) | 돈·상대 기관이 걸릴 때 | 되돌리기가 비싸다, 조용히 틀리는 것이 많다, 그래서 "막기"만큼 "빨리 알기"에 투자한다 |

참고: 원본 B 묶음의 "두 장군 문제가 뿌리"는 메시지·응답 유실이 낀 항목(F-10·F-11·F-20 등)에 맞는다. 재시도 폭풍(F-09)·배포 스큐(F-17)·핫스팟(F-19)은 유실 없이도 생긴다(두 장군 문제는 메시지가 유실될 수 있을 때 양쪽이 합의할 수 없다는 한계다 — Lamport·Lynch, *Distributed Computing* §4.2.1).

### 3. 색인 — 25개 한 줄씩과 장치, 자세히 볼 곳

| # | 이름 | 뿌리 한 줄 | 막는 장치 | 자세히 |
|---|---|---|---|---|
| F-01 | lost update | 읽고-고치고-절대값 저장, 사이 변경이 덮임 | 버전 조건부 UPDATE, 원자적 상대 UPDATE, 직렬화 오류 | [database/14](../../database/14-isolation-levels-and-anomalies/2-summary.md)·[18](../../database/18-app-level-concurrency-patterns/2-summary.md) |
| F-02 | 데드락 | 락 순서 불일치·중복 키 INSERT·갭 락 | 일관된 락 순서, 재시도 | [database/15](../../database/15-two-phase-locking-and-deadlock/2-summary.md) |
| F-03 | 커넥션 풀 고갈 | 인스턴스×풀 > DB 한도, 한 작업이 커넥션 둘 | 한 작업 한 커넥션, 풀 분리, 총량 검증 | [database/21](../../database/21-connection-pooling/2-summary.md) |
| F-04 | 복제 지연 | 쓰기는 주, 읽기는 복제본 | 돈·멱등 판단은 주 DB에서만 | [database/32](../../database/32-replication-leader-follower/2-summary.md) |
| F-05 | 롱 트랜잭션 | 오래 열린 스냅샷이 옛 버전 정리를 막음 | 짧은 트랜잭션, 실행 시간 상한 | [database/16](../../database/16-mvcc/2-summary.md) |
| F-06 | 온라인 DDL이 온라인이 아님 | 복제본 지연·컬럼 드롭이 구 코드를 깸 | expand-contract, 단계 사이 전체 배포 대기 | [database/26](../../database/26-schema-migration/2-summary.md) |
| F-07 | ORM flush 타이밍 | 직접 SQL이 아직 flush 안 된 변경을 못 봄 | 혼용을 모듈 경계로 금지 | [database/24](../../database/24-transaction-boundaries-in-app-code/2-summary.md) |
| F-08 | 채번 병목 | 한 행에 갱신 집중 | 블록 할당, Snowflake류 | [distributed/13](../../distributed/13-distributed-id-generation/2-summary.md) |
| F-09 | 재시도 폭풍 | 느림 → 재시도 → 더 느림 | 재시도 예산, 백오프+지터, 서킷 브레이커 | [03](../03-failure-at-scale/2-summary.md) |
| F-10 | 메시지 유실 | (XA 같은 분산 트랜잭션 없이) DB 커밋과 브로커 발행이 따로라 원자적이 아님 | 아웃박스 | [distributed/16](../../distributed/16-outbox-and-dual-write/2-summary.md) |
| F-11 | 메시지 중복 | 외부 DB 업무 변경과 브로커 완료 표시(ack·오프셋 커밋)가 원자적이 아님(Kafka 안의 읽기-처리-쓰기는 트랜잭션으로 묶을 수 있다) | 수신 측 유니크 제약(인박스) | [distributed/17](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md) |
| F-12 | 순서 역전 | 병렬 전달 | 키 파티션 + 파티션당 소비자 하나 | [distributed/21](../../distributed/21-kafka-internals/2-summary.md) |
| F-13 | 독약 메시지(HOL) | 영구 실패 한 건이 뒤를 막음 | 재시도 상한 + DLQ + 알림 | [distributed/18](../../distributed/18-consumer-failure-handling/2-summary.md) |
| F-14 | 좀비 소유자 | lease 만료 뒤 깨어난 옛 소유자의 쓰기 | fencing token | [distributed/12](../../distributed/12-coordination-and-fencing/2-summary.md) |
| F-15 | 배치 중복 실행 | 스케줄러 이중화·CronJob 중복 생성 | 멱등 작업, 파티션 할당, 실행 이력 유일 제약 | [30-scheduler-and-cron-ha](../30-scheduler-and-cron-ha/2-summary.md) |
| F-16 | 타임아웃 계층 역전 | 상위가 포기해도 하위가 계속 돎 | 안쪽일수록 짧게 + 취소 전파 | [distributed/03](../../distributed/03-partial-failure-and-timeouts/2-summary.md) |
| F-17 | 배포 스큐 | 롤링 중 구·신 버전 공존 | 기능 플래그, expand-contract | [23-deployment-strategies](../23-deployment-strategies/2-summary.md) |
| F-18 | split-brain | 분할 양쪽이 각자 리더 | 쿼럼 + fencing | [distributed/10](../../distributed/10-leader-election/2-summary.md) |
| F-19 | 핫스팟 | 한 키에 몰림 | 키 설계 변경 | [03](../03-failure-at-scale/2-summary.md) |
| F-20 | 이중 결제 | 응답 유실 → "모름" 상태 | 멱등 키 + 성공/실패/모름 3분류 | [13-idempotency](../13-idempotency/2-summary.md) |
| F-21 | 정산 불일치 탐지 지연 | 세 원장이 각자 정본 | 대사 + 대사가 도는지 감시 | [distributed/20](../../distributed/20-data-ownership-and-cross-service-queries/2-summary.md) |
| F-22 | 초과 승인 | 가용잔액이 아닌 잔액으로 판단 | 홀딩·한도·승인을 한 커밋 + 낙관적 락 | 원본 F-22 |
| F-23 | 전표 누락·중복 | 복식부기는 전표 하나의 균형만 보장 | 아웃박스 + 원천 이벤트 유일 제약 + 총량 불변식 | 원본 F-23 |
| F-24 | 문서·설정 잔재 | 같은 사실이 두 곳에 있고 한 곳만 고침 | 단일 출처, 자동 대조 | 원본 F-24 |
| F-25 | 조용한 실패 | 부분 실패를 완료로·무음 스킵·지표 없음 | 완료 조건 명시, 적재, 지표, 검증의 감시 | [01](../01-fault-error-failure-availability/2-summary.md) |

### 4. 고장 모양으로 다시 묶기

[01](../01-fault-error-failure-availability/2-summary.md)의 고장 분류(신호 있음/없음)로 보면 우선순위가 보인다.

```text
 신호 없는 고장(에러 없이 값이 틀림)        F-01 F-04 F-07 F-11 F-12 F-14 F-17 F-18 F-21 F-22 F-23 F-24 F-25
 신호 있는 고장(에러·지연이 보임)           F-02 F-03 F-05 F-06 F-09 F-13 F-16 F-19
 둘 다 가능(상황에 따라)                    F-08 F-10 F-15 F-20
```

- 신호 없는 쪽이 더 많고 더 비싸다. 비용 = 건수 × 발견까지의 기간이기 때문이다(원본 F-25).
- 그래서 신호 없는 항목에는 "막는 장치"와 함께 **"아는 장치"**(대조·불변식 검사·지표)를 붙인다.
- 이 분류는 이 노트의 판단이다. 같은 항목도 구현에 따라 신호가 생기기도 한다(예: F-01을 직렬화 오류로 막으면 신호 있는 고장이 된다 — 아래 실험).

### 5. "정상 동작이 원인"인 계열

- F-02(데드락 탐지로 한쪽 중단), F-05(MVCC 옛 버전 보존), F-06(DDL 알고리즘의 제약), F-14(GC 멈춤), F-15(스케줄러 이중화), F-17(롤링 배포)는 **기능이 설계대로 동작한 결과**다. 코드 리뷰에서 버그를 찾아도 안 나온다. 원리를 알아야 보인다(원본 [Claude 추가] 절).

### 실험: F-01 lost update와 F-11 중복 소비를 실제 DB에서

- 환경: 전용 일회용 컨테이너 `sn-rl-w01-pg`(PostgreSQL 17.11, `--cpus=2`), psql 두 세션을 `pg_sleep`으로 엇갈리게 실행.
- F-01: T1(+30)·T2(+50)가 같은 행을 읽고(`\gset`), 앱 쪽에서 더해 **절대값**으로 저장. 기대값 80.

```bash
# 핵심 부분 (전체: scratchpad/rel/01/e04/lost.sh)
BEGIN ISOLATION LEVEL $ISO;
SELECT held, version FROM acct WHERE id = 1 \gset
SELECT pg_sleep($WAIT);
UPDATE acct SET held = :held + $AMT WHERE id = 1;                                          -- plain
UPDATE acct SET held = :held + $AMT, version = version + 1 WHERE id = 1 AND version = :version; -- optimistic
UPDATE acct SET held = held + $AMT WHERE id = 1;                                           -- atomic
COMMIT;
```

(실험, PostgreSQL 17.11, 2026-10-01)

```text
== READ COMMITTED / plain (T1 +30, T2 +50, 기대값 80)
  T1: 읽음 held=0 version=0
  T1: UPDATE 1
  T2: 읽음 held=0 version=0
  T2: UPDATE 1
  최종 held = 50
== READ COMMITTED / optimistic (T1 +30, T2 +50, 기대값 80)
  T1: 읽음 held=0 version=0
  T1: UPDATE 1
  T2: 읽음 held=0 version=0
  T2: UPDATE 0
  최종 held = 30
== READ COMMITTED / atomic (T1 +30, T2 +50, 기대값 80)
  T1: 읽음 held=0 version=0
  T1: UPDATE 1
  T2: 읽음 held=0 version=0
  T2: UPDATE 1
  최종 held = 80
== REPEATABLE READ / plain (T1 +30, T2 +50, 기대값 80)
  T1: 읽음 held=0 version=0
  T1: UPDATE 1
  T2: 읽음 held=0 version=0
  T2: ERROR:  could not serialize access due to concurrent update
  최종 held = 30
```

- 관찰 1 — plain: 두 UPDATE가 모두 `UPDATE 1`로 성공했고 최종 50. **T1의 +30이 에러 없이 사라졌다.** 신호 없는 고장이다.
- 관찰 2 — optimistic: T2가 `UPDATE 0`을 받았다. 앱이 이 0을 보고 다시 읽어 재시도해야 80이 된다. 0을 무시하면 이번엔 T2의 +50이 사라진다 — 장치는 "0행"이라는 신호까지만 준다.
- 관찰 3 — atomic: `held = held + 50`은 최신 값을 읽어 더해 80. 단 "가용잔액이 충분한가"처럼 **읽은 값으로 판단**해야 하면 이 꼴만으로는 안 된다(판단을 `WHERE held + 50 <= limit`처럼 같은 문장에 넣어야 한다).
- 관찰 4 — PostgreSQL REPEATABLE READ는 같은 경합에서 T2를 **직렬화 오류로 거부**했다. 유실이 신호 있는 실패로 바뀌었다. 앱은 이 오류에 트랜잭션 전체를 재시도해야 한다.
  - 참고: 원본 F-01은 "RR의 끝까지 같은 사진은 쓰기에 위험하다"고 MySQL InnoDB 기준으로 적는다. Jepsen(MySQL 8.0.34)은 MySQL RR이 lost update를 허용함을 확인했다. PostgreSQL 17 RR은 위 실험처럼 거부한다 — **격리 수준 이름이 같아도 제품마다 동작이 다르다.**
  - 참고: 원본은 Jepsen을 "load-modify-save 패턴에서 커밋된 변경을 조용히 버린다 — 9,048 트랜잭션 중 198건"으로 인용한다. Jepsen 원문(2023-12)의 수치는 "9,048개 성공 트랜잭션 중 446개 트랜잭션이 198건의 lost update에 관여"이고, 시험은 list-append(키에 원소 덧붙이기) 워크로드다. "load-modify-save"라는 문구는 원문에서 찾지 못했다.

- F-11: 같은 이벤트가 두 소비자에게 거의 동시에 도착. "조회해서 없으면 넣기" vs 유니크 제약.

(실험, 같은 컨테이너 — 코드 `scratchpad/rel/01/e04/dup.sh`)

```text
== 제약 없음: 같은 이벤트가 두 소비자에게 거의 동시에 도착
  C1: 조회 결과 0 건
  C1: 처리함
  C2: 조회 결과 0 건
  C2: 처리함
  inbox의 evt-42 행 수 = 2
== 유니크 제약: 같은 이벤트가 두 소비자에게 거의 동시에 도착
  C1: 조회 결과 0 건
  C1: 처리함
  C2: 조회 결과 0 건
  C2: ERROR:  duplicate key value violates unique constraint "inbox_event_id_key"
  C2: DETAIL:  Key (event_id)=(evt-42) already exists.
  C2: 삽입 거부 → 이미 있음으로 판단
  inbox의 evt-42 행 수 = 1
```

- 관찰: 두 소비자 모두 "0건"을 봤다. 조회는 막지 못한다. 유니크 제약이 있을 때만 DB가 두 번째를 거부했다. "본다"가 아니라 "못 넣는다"가 장치다(원본 F-11).

## 쓰이는 자료구조·알고리즘

- **버전 번호 + 비교 후 교환(CAS)** — `WHERE version = ?` 조건부 UPDATE. F-01·F-22. 낙관적 동시성 일반은 [database/17-occ-and-timestamp-ordering](../../database/17-occ-and-timestamp-ordering/2-summary.md).
- **유니크 인덱스(B+Tree)** — 같은 키의 두 번째 삽입을 인덱스가 거부한다. F-11·F-20·F-23. [database/08-btree-indexes](../../database/08-btree-indexes/2-summary.md).
- **단조 증가 토큰** — fencing. F-14·F-18.
- **해시 파티셔닝** — 같은 키는 같은 파티션·같은 소비자. F-12. 편중은 F-19.
- **DLQ(별도 큐)** — 실패한 항목을 옆 큐로 옮겨 본 큐가 진행되게 한다. F-13.
- **상태 기계** — 결제를 성공·실패·**모름** 세 상태로 두고, 모름은 조회·대사로, 또는 상대가 멱등 키를 지원하면 같은 키로 재시도해 저장된 결과를 받아 빠져나간다(Stripe 멱등 요청 문서). F-20.
- **대사(reconciliation) = 집합 비교** — 두 원장의 키 집합 차집합·값 비교(정렬 병합 조인이나 해시 조인). F-21·F-23.

## 적용 — 풀어나가는 법

### 1. 설계 리뷰에서 카탈로그를 쓰는 순서

1. 변경이 닿는 경로를 그린다(요청 → DB → 이벤트 → 소비자 → 외부).
2. 경로의 각 칸에 해당 F 번호를 붙인다. 읽고-쓰기 = F-01, 복제본 읽기 = F-04, 이벤트 발행 = F-10·F-11·F-12, 외부 호출 = F-16·F-20.
3. 번호마다 "막는 것" 칸을 **장치 이름**으로 채운다. 문장이면 빈칸으로 본다.
4. 신호 없는 항목에는 "아는 것"(대조·지표·불변식 검사)을 하나 더 붙인다.
5. 장치가 실제로 있는지 코드·스키마에서 확인한다(제약이 마이그레이션에 있나, 버전 컬럼이 엔티티에 있나).
6. 남긴 빈칸은 "이런 이유로 열어 둠"으로 기록한다 → [27-failure-point-checklist](../27-failure-point-checklist/2-summary.md).

### 2. 장치를 코드로 — 버전 조건부 저장 (Java, JDBC)

```java
/** F-01 장치: 읽은 버전 그대로일 때만 저장. 0행이면 다시 읽고 재시도(상한 있음). */
boolean holdAmount(Connection c, long id, long amount, int maxRetries) throws SQLException {
    for (int i = 0; i <= maxRetries; i++) {
        long held, available; int version;
        try (PreparedStatement ps = c.prepareStatement("SELECT held, balance, version FROM acct WHERE id = ?")) {
            ps.setLong(1, id);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) throw new IllegalStateException("no account " + id);
                held = rs.getLong(1); available = rs.getLong(2) - held; version = rs.getInt(3);
            }
        }
        if (available < amount) return false;                      // 읽은 값으로 판단
        try (PreparedStatement up = c.prepareStatement(
                "UPDATE acct SET held = ?, version = version + 1 WHERE id = ? AND version = ?")) {
            up.setLong(1, held + amount); up.setLong(2, id); up.setInt(3, version);
            if (up.executeUpdate() == 1) return true;              // 아무도 끼어들지 않았다
        }
        // 0행: 그 사이 다른 트랜잭션이 바꿨다 → 다시 읽는다 (조용히 넘어가지 않는다)
    }
    throw new ConcurrentModificationException("hold retry exhausted: " + id);
}
```

- JPA라면 엔티티에 `@Version` 필드를 두면 같은 조건부 UPDATE가 생성되고, 0행이면 `OptimisticLockException`이 난다. 필드를 빠뜨려도 컴파일·단위 테스트는 통과한다(원본 F-01). 그래서 "돈을 다루는 엔티티는 버전 필드가 있다"를 테스트(리플렉션으로 필드 검사 등)로 강제한다.

### 3. 진단 명령

```sql
-- PostgreSQL: 오래 열린 트랜잭션 (F-05)
SELECT pid, now() - xact_start AS age, state, left(query, 60)
  FROM pg_stat_activity WHERE xact_start IS NOT NULL ORDER BY age DESC LIMIT 5;
-- 데드락 누적 (F-02의 신호). 직렬화 실패(SQLSTATE 40001, F-01을 RR로 막을 때)는 앱 쪽 지표로 센다
SELECT datname, deadlocks FROM pg_stat_database WHERE datname = current_database();
-- 유니크 제약이 실제로 있는가 (F-11)
SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'inbox'::regclass;
```

## 장애 시나리오와 대처

카탈로그 자체가 ⚠ 모음이다(커리큘럼). 여기서는 묶음마다 대표를 하나씩, 그리고 카탈로그를 쓸 때의 실패를 둔다.

### 1. F-01 — 동시 요청에서 금액이 조용히 덜 쌓인다

- 현상: 포인트·재고·홀딩 금액이 가끔 기대보다 작다. 재현이 안 된다.
- 보이는 형태: 에러·예외 없음. 두 요청의 로그가 같은 이전 값을 읽었다. 실험의 plain처럼 `UPDATE 1`이 둘 다 성공하고 하나의 변경이 사라진다.
- 원인: 읽고-고치고-절대값 저장. 격리 수준과 제품에 따라 허용된다(PostgreSQL RC 허용, MySQL RR 허용 — Jepsen).
- 대처: 버전 조건부 UPDATE + 0행 재시도, 판단이 필요 없으면 원자적 상대 UPDATE, 또는 직렬화 오류를 내는 격리 수준 + 트랜잭션 재시도. 엔티티 버전 필드를 테스트로 강제.

### 2. F-11 — 같은 이벤트가 두 번 반영된다

- 현상: 쿠폰이 두 번 지급됐다. 소비자 재시작·리밸런스 시각과 겹친다.
- 보이는 형태: 같은 `event_id` 처리 로그가 두 번. 코드에는 "이미 처리했는지 조회" 로직이 있다.
- 원인: at-least-once 전달 + 조회 기반 중복 검사. 동시 도착이면 둘 다 "없음"을 본다(실험).
- 대처: 처리 기록 테이블에 `event_id` `NOT NULL` + 유니크 제약을 두고(PostgreSQL 기본 UNIQUE는 NULL끼리를 중복으로 보지 않는다) **업무 변경과 같은 트랜잭션**에서 삽입한다. 제약 위반 = 이미 처리됨.

### 3. F-13 — 이벤트 하나 때문에 파티션 전체가 멈췄다

- 현상: 특정 파티션의 지연(lag)만 계속 증가한다. 다른 파티션은 정상.
- 보이는 형태: 같은 오프셋에서 같은 예외가 무한 반복. 대사에서는 유실이 아니라 "아직 안 옴"으로 보인다.
- 원인: 영구 실패 한 건 + 순서대로 처리하는 소비자.
- 대처: 재시도 상한 + DLQ로 옮기고 알림. DLQ 없이 상한만 두면 유실이다. 자세히는 [distributed/18](../../distributed/18-consumer-failure-handling/2-summary.md).

### 4. F-17 — 배포 중에만 일부 요청이 다르게 처리된다

- 현상: 배포 시간대에 판정이 엇갈린 거래가 나온다.
- 보이는 형태: 같은 시각 같은 입력인데 인스턴스(버전)마다 결과가 다르다.
- 원인: 구·신 버전 공존 — 롤링 도중의 일시 공존, 또는 배포 누락으로 남은 공존. Knight Capital(2012-08-01)은 뒤쪽이다(7월 27일부터 며칠에 걸친 단계 배포에서 한 대가 빠졌다 — SEC 명령서 15항): 기술자가 SMARS 서버 8대 중 1대에 새 코드를 복사하지 않았고, 재사용된 플래그가 그 서버에서 옛 기능(Power Peg)을 깨웠다. 약 45분 동안 주문이 시장에 나갔고, 그때 쌓인 포지션에서 결국 4억 6천만 달러 넘게 손실을 봤다(SEC 명령서 34-70694 1항·17항). 이후 다른 7대에서 새 코드를 되돌리자 그 서버들에서도 옛 코드가 돌았다(같은 문서).
- 대처: 판단이 바뀌는 변경은 기능 플래그 뒤에, 플래그 이름은 재사용하지 않는다, 스키마는 expand-contract, 배포 완료(전 인스턴스 버전 일치)를 확인하는 장치.

### 5. 카탈로그가 "안다"로 끝나고 장치가 없다 (F-24·F-25의 문서판)

- 현상: 회고에서 "이건 카탈로그의 F-11이다"라고 이름을 붙였는데 몇 달 뒤 같은 사고가 다시 난다.
- 보이는 형태: 설계 문서 "막는 것" 칸에 "멱등하게 처리한다"라는 문장만 있다. 스키마에는 유니크 제약이 없다.
- 원인: 문장을 장치로 착각했다. 판정 규칙을 적용하지 않았다.
- 대처: 리뷰에서 "막는 것" 칸은 장치 이름 + 위치(파일·마이그레이션·설정)로만 받는다. 장치가 도는지 확인하는 테스트·지표를 함께 둔다.

## 핵심 문장

- 카탈로그의 쓸모는 이름이다. 이름이 붙으면 같은 뿌리의 사고를 처음부터 다시 조사하지 않는다.
- 막는 것에 이름(제약·조건부 쓰기·토큰·DLQ)을 댈 수 있으면 막히고, 계약 문장뿐이면 뚫린다.
- 신호 없는 고장이 더 많고 더 비싸다. 막는 장치에 아는 장치(대조·불변식·지표)를 붙인다.
- 실험: 읽고-고치고-저장은 PostgreSQL RC에서 +30을 에러 없이 잃었다(최종 50). 버전 조건부 UPDATE는 0행으로, PostgreSQL RR은 직렬화 오류로 신호를 냈다.
- "조회 후 없으면 넣기"는 동시 도착을 못 막는다(행 2개). 유니크 제약만 두 번째를 거부했다.

## 관련 주제·근거

- 선행
  - [03-failure-at-scale](../03-failure-at-scale/2-summary.md) — 규모가 바꾸는 실패 양상(F-09·F-19의 일반형)
  - 원본 [ops-patterns/failure-modes](../../ops-patterns/failure-modes/2-summary.md) — 25개 항목의 증상·뿌리·실사건·막는 법
- 후속
  - [27-failure-point-checklist](../27-failure-point-checklist/2-summary.md) — 카탈로그를 설계 시 점검 절차로
  - [database/56-db-symptom-index](../../database/56-db-symptom-index/2-summary.md), [distributed/35-distributed-symptom-index](../../distributed/35-distributed-symptom-index/2-summary.md) — 증상에서 거꾸로 찾기
  - [52-reliability-symptom-index](../52-reliability-symptom-index/2-summary.md)
- 문서·사고 보고서
  - Jepsen, "MySQL 8.0.34", 2023-12 — RR에서 lost update, 9,048 트랜잭션 중 446개가 198건에 관여 <https://jepsen.io/analyses/mysql-8.0.34>
  - SEC Administrative Proceeding 34-70694 (Knight Capital, 2013) — 8대 중 1대 미배포, Power Peg, 약 45분간 주문 송출, 그 포지션에서 결국 4억 6천만 달러 초과 손실(1항·17항) <https://www.sec.gov/litigation/admin/2013/34-70694.pdf>
  - GitHub, "October 21 post-incident analysis", 2018 — 연결 43초 단절 → 24시간 11분 저하, "data integrity over site usability". 참고: 원본 F-18의 "954건 미복제"는 원문에서 "가장 바쁜 클러스터 하나에서 954건"이다 <https://github.blog/news-insights/company-news/oct21-post-incident-analysis/>
  - Kubernetes 문서 "CronJob" — 실행 시점마다 Job을 "대략 한 번" 만들며 둘이 만들어지거나 하나도 안 만들어질 수 있으므로 Job은 멱등해야 한다(F-15) <https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/>
  - 원본의 다른 실사건(우아한형제들·Airbnb·Percona·PlanetScale·Toss·Santander·카카오페이·Revolut·Bank of Ireland·Chase·Citi/Revlon·Deutsche Bank·삼성증권·Stripe·Twilio)은 이 노트에서 다시 확인하지 않았다. 원본도 F-15·F-25의 연도에 "확인 필요"를 달았다 `[?]`
- 실험 목록
  - e04-F01 lost update 4모드(RC plain·RC optimistic·RC atomic·RR plain) — PostgreSQL 17.11 일회용 컨테이너 `sn-rl-w01-pg`, `scratchpad/rel/01/e04/lost.sh`
  - e04-F11 조회 후 삽입 vs 유니크 제약 — 같은 컨테이너, `scratchpad/rel/01/e04/dup.sh`
