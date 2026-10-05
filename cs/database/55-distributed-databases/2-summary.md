# database/55-distributed-databases — 분산 데이터베이스 개관: 분산 OLTP·OLAP과 NewSQL — 정리 (힌트)

## 해결하는 문제

샤딩(33번)은 데이터를 나눈다. 그러나 나누는 순간 DB가 해 주던 일이 앱으로 넘어온다.

```text
  단일 DB가 해 주던 것            직접 샤딩하면                         분산 DB가 다시 떠맡는 것
  여러 행의 원자적 커밋            샤드를 넘으면 앱이 saga·2PC            분산 트랜잭션(2PC + 합의)
  "지금" 일관된 스냅숏 읽기         샤드마다 시각이 달라 어긋남             전역 타임스탬프(TSO·TrueTime·HLC)
  조인·집계                       앱에서 scatter-gather                 분산 실행 계획(푸시다운·셔플)
  장애 시 자동 복구                샤드마다 따로 페일오버                  파티션마다 합의 그룹(Raft·Paxos)
  재샤딩                         운영 작업(33번 장애 3)                 자동 분할·이동
```

- *분산 DBMS*: 하나의 논리 DB를 여러 물리 자원에 나눠 둔다. 앱은 보통 데이터가 나뉜 것을 모른다(CMU 15-445 L22).
- *NewSQL*: "SQL과 ACID 트랜잭션을 유지하면서 수평 확장하는" 관계형 분산 DB를 묶어 부르는 말이다. Google Spanner, CockroachDB, TiDB 등이 흔히 이렇게 불린다. 표준 정의가 있는 용어는 아니다.

쉬운 예: 지점이 여러 개인 은행.
- 각 지점이 자기 고객 장부를 가진다(분할).
- 지점마다 장부 사본을 세 권 두고, 셋 중 둘이 동의해야 기록한다(합의 복제).
- A 지점 → B 지점 이체는 두 지점이 모두 "준비됐다"고 해야 확정한다(2PC).
- "오늘 마감 시점의 전체 잔액"을 내려면 모든 지점이 같은 "시점"에 동의해야 한다(전역 시계).

똑같은 구조다. 그리고 대가도 똑같다. **커밋마다 지점 사이 통신 왕복이 붙고, 시계의 불확실성이 대기(Spanner commit wait)나 재시도(CockroachDB)로 붙을 수 있다.**

## 동작·원리

### 1. 구조 — 무엇을 공유하나

```text
  shared-nothing                          shared-disk
  [CPU+메모리+디스크] [CPU+메모리+디스크]     [CPU+메모리] [CPU+메모리]   ← 계산 노드(무상태, 캐시)
        └─────── 네트워크 ───────┘               └──── 공유 저장소 ────┘   ← 저장 계층(상태)
  + 성능·효율                              + 계산과 저장을 따로 늘림
  − 노드 추가 = 데이터 물리 이동             − 노드끼리 캐시 무효화 메시지 필요
  예: 분산 OLTP 대부분                      예: 클라우드 네이티브 OLAP(Snowflake·BigQuery·Redshift)
```

- CMU L22·L24의 분류다. 클라우드 네이티브 DBMS는 대개 shared-disk 기반이다(L24).

### 2. 분산 OLTP의 뼈대 — 파티션 × 합의 × 원자적 커밋

```text
  키 공간:  [a──f)        [f──m)        [m──z]          ← 파티션(range·region·tablet)
             │              │              │
  복제:    Raft 그룹 1     Raft 그룹 2     Raft 그룹 3      ← 파티션마다 3~5 사본, 과반 합의로 쓰기
           L  F  F         F  L  F         F  F  L        (L = 리더/리스 보유자)
             └───────── 2PC ─────────┘                   ← 여러 파티션에 걸친 트랜잭션
```

- 각 파티션은 스스로 **합의 그룹**이다. 과반이 살아 있으면 리더가 죽어도 새 리더를 뽑고 계속한다. 32번의 비동기 페일오버 유실이 구조적으로 없다(과반 확인 뒤 커밋).
- 여러 파티션을 건드리는 트랜잭션은 **2PC**(또는 그 변형)로 묶는다. 2PC의 약점(코디네이터가 죽으면 참가자가 막힘)은 코디네이터 상태를 합의 그룹에 두어 줄인다. Spanner 논문: "2PC를 Paxos 위에서 돌리면 가용성 문제가 완화된다."
- 제품별 이름(각 제품 문서)
  - CockroachDB: 데이터를 *range*로 나누고 range마다 Raft 그룹. range가 설정 크기에 닿으면 둘로 쪼갠다(동적 분할, 33번). 여러 range에 걸친 커밋은 고전 2PC 대신 *Parallel Commits*를 쓴다. 합의 두 번을 한 번으로 줄인 원자적 커밋 프로토콜이다(Transaction Layer 문서).
  - TiDB: 저장 계층 TiKV의 *Region*마다 Raft. PD(Placement Driver)가 메타데이터와 배치를 관리하고 타임스탬프를 발급한다(기본 구성. 실험 기능인 PD 마이크로서비스 모드에서는 별도 `tso` 서비스가 발급).
  - Spanner: 데이터를 Paxos 그룹에 두고, 여러 그룹에 걸친 쓰기는 2PC. 부하에 따라 디렉터리 단위로 그룹 사이를 옮긴다.

### 3. 2PC — 왕복 두 번, 그리고 막힘

```text
  코디네이터                참가자 A            참가자 B
     │── PREPARE ──────────▶│                   │
     │── PREPARE ──────────────────────────────▶│
     │◀─ OK(준비·로그 기록) ──│                   │
     │◀─ OK ────────────────────────────────────│
     │── COMMIT ───────────▶│ ──▶ 커밋·락 해제     │
     │── COMMIT ──────────────────────────────▶│ ──▶ 커밋·락 해제
```

- 1단계에서 모두 OK면 2단계에서 커밋, 하나라도 거절하면 모두 중단(CMU L23).
- **준비(PREPARE)한 참가자는 결과를 스스로 정할 수 없다.** 코디네이터가 준비 뒤 죽으면 참가자는 락을 쥔 채 기다린다(*in-doubt*). Paxos는 과반이 살아 있으면 막히지 않는다(CMU L23).

로컬 재현(예시, MySQL 8.4.10): 한 세션에서 `XA START → UPDATE acct … id=1 → XA END → XA PREPARE` 후 **연결을 끊었다**.

```text
  XA RECOVER;                      → formatID 1, data w20x   (준비된 채 남아 있다)
  performance_schema.data_locks    → acct PRIMARY X,REC_NOT_GAP GRANTED lock_data 1
  다른 세션 UPDATE acct … id=1     → ERROR 1205 (HY000): Lock wait timeout exceeded
  XA ROLLBACK 'w20x';              → 정리(결정을 내려 줘야 풀린다)
```

- 연결이 끊겨도 준비된 트랜잭션은 사라지지 않고 **행 락을 계속 쥔다**. 누군가 커밋·롤백을 결정해 줄 때까지다.
- 로컬 재현(예시, PostgreSQL 17.11): `PREPARE TRANSACTION 'w20_t1'` → `ERROR: prepared transactions are disabled` / `HINT: Set "max_prepared_transactions" to a nonzero value.` 기본값 0이라 2PC 참가자가 되려면 설정을 바꿔야 한다.

### 4. 시계 — "전역 순서"를 어떻게 얻나

분산 스냅숏 읽기와 직렬화 순서에는 **모든 노드가 동의하는 타임스탬프**가 필요하다. 벽시계는 노드마다 어긋난다(distributed 04 physical-clocks). 세 가지 답이 있다.

```text
  중앙 발급(TSO)                    TrueTime + commit wait            HLC + 불확실성 구간
  TiDB PD가 번호를 나눠 줌            [earliest, latest] 구간을 받음        물리 시각 + 논리 카운터
  64비트 = 물리 ms 46비트             커밋 ts = latest로 잡고              읽기가 "내 시각 + 최대 오프셋" 안의
          + 논리 18비트               earliest > ts 될 때까지 기다림         쓰기를 만나면 → 재시작
  − 발급자와 왕복 1회                  − 커밋마다 약 2ε 대기                 − 재시도(40001)가 늘 수 있음
  − 발급자가 병목·단일 지점(HA로 보완)  − 특수 시계 인프라(GPS·원자시계)      − 오프셋 한도 넘으면 정합성 위험
```

- TiDB TSO: 기본 구성에서는 PD가 발급한다. 앞 46비트는 밀리초 단위 UNIX 시각, 뒤 18비트는 같은 밀리초 안의 순번이다. Percolator 트랜잭션 모델에 쓴다(TiDB TSO 문서).
- Spanner TrueTime: `TT.now()`가 구간을 돌려준다. 구간 반폭 ε은 폴링 주기마다 약 1~7 ms로 톱니처럼 움직이고 평균 약 4 ms다. 코디네이터는 커밋 타임스탬프를 `TT.now().latest` 이상으로 잡고, 그 시각이 확실히 과거가 될 때까지(`TT.after(s)`) 결과를 보이지 않는다(**commit wait**). 기대 대기는 최소 2ε이고 Paxos 통신과 겹쳐 진행된다. 이것으로 *외부 일관성*(T1이 T2 시작 전에 커밋하면 T1의 타임스탬프가 더 작다)을 얻는다(Spanner OSDI 2012 §3, §4.1.2, §4.2.1).
  - 논문의 1-복제본 실험에서 commit wait는 약 5 ms, Paxos 지연은 약 9 ms였다.
- CockroachDB HLC: 물리 성분(벽시계에 가까움) + 논리 성분. 읽기가 자기 시각보다 **조금 미래**의 쓰기를 만나면, 그 쓰기가 실제로 먼저였을 수 있으므로 불확실성 구간 안이면 타임스탬프를 올려 재시도한다(`ReadWithinUncertaintyIntervalError`, SQLSTATE `40001`). 노드는 클러스터 절반 이상과의 시계 차이가 최대 오프셋의 80%를 넘으면 **스스로 종료한다**(CockroachDB Transaction Layer 문서).

### 5. 분산 OLAP — 데이터를 옮길까, 쿼리를 옮길까

```text
  쿼리를 데이터로(push)                  데이터를 쿼리로(pull)
  각 노드에서 필터·부분 집계 → 결과만 전송     저장소에서 페이지를 가져와 계산 노드가 처리
  shared-nothing에 흔함                   shared-disk에 흔함
```

```text
  분산 조인 네 경우 (R ⋈ S)
  ① S가 모든 노드에 복제됨           → 각 노드 로컬 조인
  ② R·S가 조인 키로 같이 분할됨       → 각 노드 로컬 조인
  ③ 다른 키로 분할, S가 작음         → S를 모든 노드에 방송(broadcast join)
  ④ 둘 다 조인 키로 분할 안 됨        → 둘 다 조인 키로 재분배(shuffle join) — 최악
```

- 조인 알고리즘 자체는 단일 노드와 같다([11-join-algorithms](../11-join-algorithms/2-summary.md)). 분산에서는 **튜플을 같은 노드에 모으는 비용**이 지배한다(CMU L24).
- 대부분의 shared-nothing 분산 OLAP은 실행 중 노드 장애를 가정하지 않는다. 노드 하나가 죽으면 **쿼리 전체가 실패**하고 처음부터 다시 돈다(CMU L24).

### 6. CAP과 PACELC — 선택의 말

- CAP: 네트워크 분할(P) 중에는 일관성(C, 선형화)과 가용성(A) 중 하나를 포기한다. 분산 OLTP·NewSQL은 대개 C를 택한다. 과반과 연결이 끊긴 쪽은 쓰기를 받지 않는다(CMU L23).
- PACELC: 분할이 없을 때(E)도 지연(L)과 일관성(C) 사이를 고른다. commit wait·합의 왕복은 "평시에 C를 위해 L을 내는" 비용이다(distributed 08 cap-and-pacelc).

## 쓰이는 자료구조·알고리즘

- **합의 로그(Raft·Paxos)** — 파티션 사본들이 같은 순서의 로그에 동의한다. 32번 복제 로그에 "과반 확인"을 더한 것이다([distributed/11-consensus-raft](../../distributed/11-consensus-raft/2-summary.md)).
- **2PC** — 준비·커밋 두 단계의 원자적 커밋 프로토콜([distributed/14-two-phase-commit](../../distributed/14-two-phase-commit/2-summary.md)).
- **MVCC + 타임스탬프** — 버전마다 커밋 타임스탬프. "ts T 시점 스냅숏 읽기" = T 이하에서 가장 최신 버전([16-mvcc](../16-mvcc/2-summary.md)).
- **하이브리드 논리 시계(HLC)·TSO** — 물리 시각과 논리 카운터를 합친 단조 타임스탬프([ops-patterns/14-logical-clock](../../ops-patterns/14-logical-clock/2-summary.md)).
- **범위 맵(메타 range)** — 키 → range → 노드를 찾는 정렬된 경계 목록. CockroachDB는 이를 meta range로 둔다(Distribution Layer 문서).
- **해시 재분배(shuffle)·방송** — 분산 조인·집계의 데이터 이동 방식.

## 적용 — 풀어나가는 법

### 1. 정말 필요한가 — 먼저 묻는 것

```text
  데이터가 한 서버에 들어가나?           예 → 단일 DB + 복제(32) + 분할(33)로 충분할 가능성이 크다
  쓰기가 한 서버를 넘나?                 아니오 → 위와 같다
  여러 리전에서 쓰기 + 강한 일관성?        예 → 분산 OLTP의 영역. 대신 커밋마다 리전 간 왕복을 낸다
  분석 쿼리가 운영 DB를 괴롭히나?          예 → 분산 OLAP(데이터 웨어하우스)으로 복제해 분리
```

### 2. 지역성을 설계한다

- 한 트랜잭션이 건드리는 행을 **같은 파티션**에 두도록 키를 잡는다(33번 co-location). 단일 파티션 트랜잭션은 2PC를 생략할 수 있다(제품의 1PC 최적화. 예: TiDB `tidb_enable_1pc`, 기본 ON). CMU L22도 분할의 목표를 "단일 노드 트랜잭션을 최대화"로 적는다.
- 리전이 여럿이면 사용자와 가까운 리전에 그 사용자의 리더·사본을 둔다. 리전을 넘는 트랜잭션은 커밋마다 리전 간 왕복이 붙는다.

### 3. 재시도를 앱에 넣는다

분산 DB는 충돌·시계 불확실성 때문에 SQLSTATE `40001`로 "다시 하라"를 자주 돌려준다. 트랜잭션 **전체**를 재시도한다.

```java
// 40001이면 트랜잭션 전체를 지수 백오프로 재시도 (JDBC)
interface TxWork<T> { T apply(Connection c) throws SQLException; }  // Function은 SQLException을 못 던진다

<T> T inTx(DataSource ds, TxWork<T> work) throws SQLException {
    for (int attempt = 1; ; attempt++) {
        try (Connection c = ds.getConnection()) {
            c.setAutoCommit(false);
            try {
                T r = work.apply(c);
                c.commit();
                return r;
            } catch (SQLException e) {
                c.rollback();
                if (!"40001".equals(e.getSQLState()) || attempt >= 5) throw e;
                Thread.sleep((long) (Math.pow(2, attempt) * 10 + Math.random() * 10));  // 예시 값
            }
        } catch (InterruptedException ie) { Thread.currentThread().interrupt(); throw new SQLException(ie); }
    }
}
```

- 재시도 안의 부수 효과(메일 발송·외부 API)는 커밋 뒤로 뺀다. 재시도가 곧 중복 실행이다([24-transaction-boundaries-in-app-code](../24-transaction-boundaries-in-app-code/2-summary.md)).
- CockroachDB 문서도 클라이언트 쪽 재시도 처리를 요구하고, 모든 트랜잭션 재시도 에러가 40001을 쓴다고 적는다.

### 4. 2PC를 직접 쓴다면 — in-doubt를 관리한다

```sql
-- MySQL 8.4: 준비된 채 남은 XA 트랜잭션 찾기와 결정
XA RECOVER;
XA COMMIT 'gtrid';   -- 또는 XA ROLLBACK 'gtrid'  (코디네이터 로그로 결정)

-- PostgreSQL 17 (max_prepared_transactions > 0 필요)
SELECT gid, prepared, owner, database FROM pg_prepared_xacts;
COMMIT PREPARED 'gid';   -- 또는 ROLLBACK PREPARED 'gid'
```

- 준비된 트랜잭션은 연결이 끊겨도 락을 쥔다(위 재현). 오래된 항목을 경보로 잡는다.

## 장애 시나리오와 대처

### 1. 분산 트랜잭션 지연 → 커밋이 단일 DB보다 수십 배 느리다

- **현상**: 같은 이체 API가 단일 PostgreSQL에서 수 ms였는데 분산 DB에서 수십~수백 ms다. 리전을 넘으면 더 크다.
- **보이는 형태**: 커밋 단계 지연이 리전 간 RTT의 몇 배로 계단처럼 나온다. 여러 파티션을 건드리는 트랜잭션만 느리다.
- **원인**: 커밋 경로 = 파티션별 합의(과반 왕복) + 파티션 간 2PC(준비·커밋 왕복) + (Spanner라면) commit wait. 단일 노드의 "로그 fsync 한 번"(PostgreSQL 기본 `synchronous_commit = on`, 동기 복제 없음)과 차원이 다르다.
- **대처**
  - 키 설계로 단일 파티션 트랜잭션을 늘린다. 한 트랜잭션이 건드리는 파티션 수를 지표로 본다.
  - 리더·사본을 사용자 가까이 두는 지역 배치.
  - 강한 일관성이 필요 없는 읽기는 약간 과거 시점의 스냅숏 읽기로 돌린다. Spanner 논문은 TrueTime 덕분에 "과거 시점의 비차단 읽기"와 락 없는 읽기 전용 트랜잭션이 가능하다고 적는다. 다른 제품의 문법은 각 문서를 확인한다.

### 2. 시계 의존 → 재시도 폭증 또는 노드 종료

- **현상**: 특정 시간대에 `40001` 재시도가 급증한다. 또는 노드 하나가 갑자기 스스로 내려간다.
- **보이는 형태**: CockroachDB `ReadWithinUncertaintyIntervalError`(40001, "restart transaction"). 노드 로그에 시계 오프셋 관련 치명 오류 후 종료. Spanner라면 ε이 커져 commit wait가 길어진다(TrueTime ε은 시계 마스터와의 통신 지연에도 의존).
- **원인**: NTP 동기가 흔들려 노드 간 시계 차이가 커졌다. HLC 계열은 불확실성 구간 안의 쓰기를 만날 때마다 재시작한다. 최대 오프셋을 넘으면 정합성을 지킬 수 없으니 노드를 내린다.
- **대처**: 모든 노드에 NTP(또는 클라우드 시간 서비스)를 두고 오프셋을 지표로 경보한다. 앱은 40001 재시도를 백오프와 횟수 제한으로 갖춘다. 가상화 환경의 시계 점프(마이그레이션·일시 정지)를 조심한다.

### 3. 2PC 코디네이터 장애 → in-doubt 트랜잭션이 락을 쥔 채 남는다

- **현상**: 코디네이터(앱 서버·트랜잭션 매니저)가 죽은 뒤, 특정 행 갱신이 계속 타임아웃난다.
- **보이는 형태**: MySQL `XA RECOVER`에 오래된 항목, `performance_schema.data_locks`에 그 트랜잭션의 `X` 락, 다른 세션은 `ERROR 1205`(로컬 재현). PostgreSQL은 `pg_prepared_xacts`에 오래된 `prepared`.
- **원인**: 준비를 마친 참가자는 코디네이터의 결정 없이 커밋도 롤백도 못 한다(2PC의 막힘).
- **대처**: 코디네이터의 결정 로그로 커밋·롤백을 수동 결정한다. 준비 상태의 나이를 경보한다. 가능하면 합의 기반 코디네이터(분산 DB 내장)나 saga([ops-patterns/08-saga](../../ops-patterns/08-saga/2-summary.md))로 설계를 바꾼다.

### 4. 핫 키 경합 → 재시도가 재시도를 부른다

- **현상**: 재고·카운터 같은 한 행에 쓰기가 몰리자 처리량이 떨어지고 지연이 폭증한다.
- **보이는 형태**: 같은 키에서 40001이 반복된다. 재시도 트래픽이 원래 트래픽을 넘는다.
- **원인**: 분산 DB의 직렬화 가능 격리에서 같은 키의 동시 쓰기는 한쪽을 재시작시킨다. 재시작 비용에 합의 왕복까지 붙어 단일 노드보다 경합에 약하다.
- **대처**: 키를 쪼갠다(카운터 샤딩: 여러 행에 나눠 쓰고 합산). 백오프에 지터를 넣는다. 경합 행 갱신을 큐로 직렬화한다.

### 5. 분산 OLAP 쿼리 중 노드 장애·셔플 폭발 → 몇 시간짜리 쿼리가 처음부터

- **현상**: 긴 분석 쿼리가 막바지에 실패하고 재실행된다. 또는 디스크 부족으로 실패한다.
- **원인**: shared-nothing OLAP은 대개 실행 중 노드 장애를 가정하지 않아 쿼리 전체가 실패한다. 조인 키로 분할되지 않은 두 큰 테이블은 셔플 조인이 되어 대량 데이터가 네트워크·디스크로 쏟아진다(CMU L24).
- **대처**: 자주 조인하는 테이블을 같은 키로 분할하거나 작은 차원 테이블을 복제한다. 중간 결과를 나눠 저장하는 단계형 파이프라인으로 쪼갠다.

## 핵심 문장

- 분산 DB는 샤딩이 앱으로 넘긴 일(분산 커밋·전역 스냅숏·분산 조인·자동 재조정)을 다시 DB 안으로 가져온다. 대가는 커밋마다 붙는 왕복과, 대기·재시도로 나타나는 시계 불확실성이다.
- 분산 OLTP의 뼈대는 "파티션마다 합의 그룹 + 파티션 사이 2PC"다. 합의가 페일오버 유실을 없애고, 2PC를 합의 위에 올려 코디네이터 막힘을 완화한다.
- 전역 순서는 중앙 발급(TSO), TrueTime + commit wait, HLC + 불확실성 재시도 중 하나로 얻는다. 셋 다 시계나 발급자에 의존한다.
- 준비된 2PC 참가자는 결정 없이는 락을 놓지 못한다. 연결이 끊겨도 in-doubt로 남는다.
- 분산 OLAP의 비용은 데이터 이동이다. 조인 키 분할·작은 테이블 복제로 셔플을 피한다. 성능의 첫 단추는 "한 트랜잭션·한 조인이 한 노드에서 끝나게" 하는 키 설계다.

## 관련 주제·근거

- 선행
  - [33-partitioning-and-sharding](../33-partitioning-and-sharding/2-summary.md) — 분할·재조정·보조 인덱스
  - [distributed/14-two-phase-commit](../../distributed/14-two-phase-commit/2-summary.md)
- 연결
  - [32-replication-leader-follower](../32-replication-leader-follower/2-summary.md) — 비동기 복제와 합의 복제의 차이
  - [11-join-algorithms](../11-join-algorithms/2-summary.md) · [16-mvcc](../16-mvcc/2-summary.md) · [24-transaction-boundaries-in-app-code](../24-transaction-boundaries-in-app-code/2-summary.md) · [37-row-vs-column-storage](../37-row-vs-column-storage/2-summary.md)
  - [distributed/04-physical-clocks-and-ntp](../../distributed/04-physical-clocks-and-ntp/2-summary.md)·[distributed/08-cap-and-pacelc](../../distributed/08-cap-and-pacelc/2-summary.md)·[distributed/11-consensus-raft](../../distributed/11-consensus-raft/2-summary.md)·[distributed/26-hybrid-clocks-and-truetime](../../distributed/26-hybrid-clocks-and-truetime/2-summary.md)
  - [ops-patterns/14-logical-clock](../../ops-patterns/14-logical-clock/2-summary.md) · [ops-patterns/08-saga](../../ops-patterns/08-saga/2-summary.md)
- 강의
  - CMU 15-445 Fall 2024 L22 Introduction to Distributed Databases(shared-nothing·shared-disk, 분할 목표, 일관 해싱, 중앙·분산 코디네이터) <https://15445.courses.cs.cmu.edu/fall2024/notes/22-distributed.pdf>
  - L23 Distributed OLTP(복제 구성·전파, 2PC와 막힘, Paxos 비막힘, CAP·PACELC) <https://15445.courses.cs.cmu.edu/fall2024/notes/23-distributedoltp.pdf>
  - L24 Distributed OLAP(push vs pull, 쿼리 장애 시 전체 재실행, 분산 조인 4경우·broadcast·shuffle, 클라우드 네이티브 shared-disk) <https://15445.courses.cs.cmu.edu/fall2024/notes/24-distributedolap.pdf>
- 논문: J. C. Corbett 외, "Spanner: Google's Globally-Distributed Database", OSDI 2012 — TrueTime ε(1~7 ms, 평균 약 4 ms), commit wait(기대 2ε 이상), 외부 일관성, 2PC over Paxos, 1-복제본 실험 commit wait 약 5 ms <https://static.googleusercontent.com/media/research.google.com/en//archive/spanner-osdi2012.pdf>
- 제품 문서
  - CockroachDB Architecture — Transaction Layer(Parallel Commits, HLC, 불확실성, 최대 오프셋 80% 초과 시 종료) · Distribution Layer(range 분할, meta range) · Transaction Retry Error Reference(40001, `ReadWithinUncertaintyIntervalError`) <https://www.cockroachlabs.com/docs/stable/architecture/transaction-layer>
  - TiDB — TSO(46비트 물리 ms + 18비트 논리, PD 발급, Percolator) <https://docs.pingcap.com/tidb/stable/tso> · TiDB Architecture(PD 역할) · PD Microservices(실험 기능, `tso` 마이크로서비스) <https://docs.pingcap.com/tidb/stable/pd-microservices/> · System Variables `tidb_enable_1pc`(기본 ON, 한 Region만 건드리는 트랜잭션의 1PC) <https://docs.pingcap.com/tidb/stable/system-variables/>
- MySQL 8.4 15.3.8 XA Transactions(`XA RECOVER`) <https://dev.mysql.com/doc/refman/8.4/en/xa.html> · PostgreSQL 17 19.4 Resource Consumption(`max_prepared_transactions` 기본 0 = 준비 트랜잭션 기능 꺼짐) · `PREPARE TRANSACTION` · 19.5 Write Ahead Log(`synchronous_commit` 기본 on, off·동기 복제 시 동작) <https://www.postgresql.org/docs/17/runtime-config-wal.html>
- 로컬 재현(MySQL 8.4.10, PostgreSQL 17.11): XA 준비 후 연결 끊기 → `XA RECOVER`·`data_locks`의 X 락·다른 세션 `ERROR 1205` → `XA ROLLBACK`, PostgreSQL `PREPARE TRANSACTION`의 기본 거부 메시지
