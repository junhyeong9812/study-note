# NewSQL · 분산 SQL (2012~)

> 원본: `~/project/database-history/04-NewSQL-분산.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-18).\
> 연도·인명·논문명·표준번호·코드는 원문 그대로다.\
> 용어 블록의 「예:」, 「대가는 무엇인가」, 트레이드오프 표는 원문에 없는 보충 설명이다.

## 한눈에 — 쉽게 말하면

**NewSQL = 은행 지점을 전국에 늘리면서도, 통장 잔액은 전 지점이 똑같이 보게 만든 것.**

- 옛날 은행은 지점 하나에 장부 하나였다.\
  손님이 늘면 그 지점이 터진다 — 한 대의 데이터베이스가 한계에 부딪히는 것과 같다.
- 지점을 100개로 늘리면 손님은 감당되지만, 이번엔 "A지점에서 입금한 돈이 B지점 장부엔 아직 안 보이는" 일이 생긴다.\
  2000년대 NoSQL이 택한 길이 이쪽이었다 — 확장을 얻고 정확한 잔액을 포기.
- NewSQL은 셋째 길이다.\
  지점은 100개로 늘리되, 모든 지점이 **같은 순서로 같은 장부를 적게** 강제한다.\
  그래서 어느 지점에서 조회해도 잔액이 하나다.
- 대가는 속도다.\
  "모두가 동의할 때까지 기다리는" 시간이 한 건마다 붙는다.

```text
한 대 (관계형)          여러 대 · 느슨 (NoSQL)      여러 대 · 엄격 (NewSQL)
+-----------+           +-----+ +-----+ +-----+     +-----+ +-----+ +-----+
| 잔액 100  |           |100  | | 90  | |100  |     |100  | |100  | |100  |
+-----------+           +-----+ +-----+ +-----+     +-----+ +-----+ +-----+
 정확하다               빠르다                       정확 + 확장
 손님 100만 명에서       "90"을 읽은 손님은          한 건마다 합의를
 터진다                 틀린 값을 본다               기다리는 시간이 붙는다
```

이 세 칸이 **똑같은 구조로** 데이터베이스 역사의 세 단계다: 관계형 → NoSQL → NewSQL.\
오늘날 Google Cloud Spanner, CockroachDB, TiDB, YugabyteDB가 셋째 칸에 서 있다.

> **강한 일관성(strong consistency)** — 방금 쓴 값을, 어느 노드에 물어봐도 곧바로 최신으로 읽을 수 있다는 보장.\
> 예: 서울에서 입금한 1만 원이, 부산 지점에서 1초 뒤 조회해도 반드시 반영돼 있다.

> **결과적 일관성(eventual consistency)** — 지금은 노드마다 값이 다를 수 있지만, 시간이 지나면 결국 같아진다는 약한 보장.\
> 예: 입금 직후 다른 지점에서 조회하면 옛 잔액이 나올 수 있고, 몇 초 뒤엔 맞는 값이 된다.

## 시대적 배경

*(이 편의 「시대 배경」에 해당한다)*

2000년대 후반 NoSQL(Dynamo·BigTable·Cassandra·MongoDB)은 웹 스케일의 쓰기 부하를 감당하려고 관계형 모델과 ACID 트랜잭션을 과감히 버렸다.\
수평 확장(샤딩)과 고가용성을 얻는 대신 SQL의 표현력, 조인, 외래키, 그리고 무엇보다 **강한 일관성**을 포기한 것이다.

> **샤딩(sharding)** — 데이터를 여러 서버에 쪼개 나눠 담아서, 서버를 늘릴수록 담을 수 있는 양과 처리량이 같이 늘게 하는 것.\
> 예: 회원 번호가 짝수면 1번 서버, 홀수면 2번 서버에 저장한다.

많은 시스템이 CAP 정리를 근거로 "분산 환경에서는 일관성(C)을 포기하고 가용성(A)을 택해야 한다"는 결정론을 받아들였고, 그 결과가 결과적 일관성이었다.

문제는 그 뒤에 남는 일이었다.\
결과적 일관성은 "읽은 값이 최신이라는 보장이 없다"는 뜻이고, 그 보정 책임은 고스란히 애플리케이션 개발자에게 넘어갔다.

```text
 [ 데이터베이스가 해주던 일 ]  [ NoSQL 이후 앱이 떠안은 일 ]
+---------------------+        +------------------------+
| 트랜잭션 한 줄로 끝 |        | 충돌 해소 코드         |
|   BEGIN ... COMMIT  |  --->  | 읽은-후-쓰기 보장 코드 |
|                     |        | 멱등 처리 코드         |
|                     |        | 중복 제거 코드         |
+---------------------+        +------------------------+
 → 개발자는 비즈니스 로직만    → 같은 일을 앱마다 다시 구현한다
```

이 대비의 결론은 하나다 — 데이터베이스가 안 해주면, 그 일이 사라지는 게 아니라 **앱으로 옮겨갈 뿐**이다.

> **멱등(idempotent) 처리** — 같은 요청이 두 번 들어와도 결과가 한 번 들어온 것과 같게 만드는 것.\
> 예: 결제 요청이 네트워크 문제로 두 번 도착해도 실제 출금은 한 번만 되게 처리 번호를 두는 것.

금융·재고·결제처럼 "틀린 값을 잠깐도 보이면 안 되는" 도메인에서는 NoSQL이 근본적으로 부적합했다.\
동시에 SQL의 생산성과 성숙한 생태계(드라이버·BI 도구·ORM)를 버린 비용도 컸다.

여기서 던져진 질문이 출발점이다 — **"확장성과 강한 일관성, SQL을 모두 가질 수는 없는가?"**\
451 Research의 Matthew Aslett가 2011년 이 새로운 부류를 가리켜 **NewSQL**이라는 용어를 만들었다.\
NoSQL 수준의 확장성을 제공하면서도 SQL과 ACID를 유지하는 관계형 DBMS라는 뜻이다.\
2012년 Google이 발표한 Spanner 논문이 이 질문에 "가능하다"고 답한 결정적 사건이었다.

## 주요 시스템과 기능

*(이 편의 「무엇이 바뀌었나」에 해당한다)*

### Google Spanner (2012) — 분산 SQL의 원형

**무엇** — 전 지구에 데이터를 흩뿌리면서도 단일 데이터베이스처럼 강한 일관성과 분산 트랜잭션을 보장한 시스템.

- **언제**: 2012년 OSDI에서 "Spanner: Google's Globally-Distributed Database" 논문 발표.\
  SQL 인터페이스와 외부 공개(Cloud Spanner)는 2017년.
- **왜**: Google 내부의 광고 시스템(AdWords)을 받치던 샤딩된 MySQL이 운영·재샤딩 한계에 부딪혔다.
- **무엇을 풀었나**: 글로벌 분산·동기 복제 위에서 **외부 일관성**(external consistency = strict serializability)을 보장했다.\
  핵심 무기가 **TrueTime API**다.

> **외부 일관성(external consistency)** — 실제 시간으로 먼저 끝난 트랜잭션이, 시스템이 매긴 순서에서도 반드시 먼저 오는 성질.\
> 예: 서울에서 3시 정각에 커밋된 이체가, 3시 1초에 시작한 뉴욕 트랜잭션에는 반드시 보인다.

TrueTime은 기존 분산 시스템이 회피해온 문제를 정면으로 다룬다 — "분산된 노드들이 절대 시간에 합의할 수 없다".\
GPS와 원자시계를 데이터센터에 두고, 시간을 하나의 값이 아니라 **불확실성 구간**(`TTinterval = [earliest, latest]`)으로 노출한다.\
트랜잭션을 커밋할 때 이 구간이 지나갈 때까지 **의도적으로 대기**(commit-wait)함으로써, 전 지구에 흩어진 트랜잭션에 모순 없는 전역 타임스탬프 순서를 부여한다.

```text
TrueTime: 시간을 "점"이 아니라 "구간"으로

    TT.now() = [earliest ───── latest]   ← 불확실성 ε (보통 수 ms)

  트랜잭션 T1 commit 타임스탬프 = s
    │
    ├─ commit-wait: now().earliest > s 가 될 때까지 대기
    │   (ε 만큼 기다려 불확실성을 "소진")
    ▼
  이후 시작하는 T2 는 반드시 s 이후의 타임스탬프를 받음
    ⇒ 실제 시간 순서 = 트랜잭션 직렬화 순서  (외부 일관성)
```

그림 해설 — 한 단계씩.

- 시계가 몇 ms 틀릴 수 있다면, 시간을 한 점으로 말하는 대신 "이 구간 어딘가"라고 말한다.\
  틀릴 수 있음을 숨기지 않고 값에 적어 넣는 것이다.
- 커밋한 뒤 그 구간이 다 지나갈 때까지 일부러 기다린다.\
  기다리고 나면 "지금 시각은 확실히 s 이후"라고 말할 수 있다.
- 그래서 나중에 시작한 트랜잭션은 반드시 더 큰 타임스탬프를 받는다.\
  실제 시간의 앞뒤가 곧 트랜잭션의 앞뒤가 된다.

**왜 이게 나은가** — 잠금 없는 스냅샷 읽기, 읽기 전용 트랜잭션의 글로벌 일관 읽기, 무중단 스키마 변경이 가능해진다.\
복제 그룹 내 합의는 **Paxos**로, 노드 간 분산 트랜잭션은 **2단계 커밋**(2PC)을 Paxos 그룹 위에 얹어 처리한다.\
초기 Spanner는 키-값에 가까웠으나, F1(광고 시스템용 분산 SQL 계층) 경험을 흡수하며 2017년 SIGMOD 논문 "Spanner: Becoming a SQL System"에서 본격적인 관계형 SQL 시스템으로 진화했다.

**대가는 무엇인가** — GPS 수신기와 원자시계라는 **특수 하드웨어**가 필요하고, 커밋마다 ε만큼 일부러 기다린다.\
Google이 아니면 따라 하기 어려운 조건이었고, 그 빈자리를 메우는 것이 뒤의 CockroachDB다.

> Spanner의 의의는 기술 그 자체보다 "**CAP의 일관성 포기는 필연이 아니다**"를 실증한 데 있다. 이후 거의 모든 분산 SQL이 Spanner를 직간접적 원형으로 삼는다.

### VoltDB / H-Store (2010~) — 인메모리 OLTP 계열의 NewSQL

**무엇** — 데이터를 통째로 메모리에 올리고, 잠금 자체를 없애 버린 초고속 트랜잭션 엔진.

- **언제**: 학술 프로토타입 H-Store(2007, Brown·MIT·CMU·Yale)에서 출발, 상용 VoltDB는 2010년 첫 공개.
- **왜**: Michael Stonebraker는 전통 디스크 기반 RDBMS의 오버헤드 — 버퍼 관리, 행 잠금(locking), 래치(latching), 다중 스레드 경합 — 가 실제 작업보다 CPU를 더 잡아먹는다고 진단했다.\
  "OLTP 트랜잭션의 대부분은 짧고 정형적인데, 왜 디스크 시대의 무거운 구조를 짊어지나?"

```text
 전통 RDBMS 한 건 처리               VoltDB 한 건 처리
+-----------------------------+      +--------------------------+
| 버퍼 관리                   |      | (메모리에 이미 있음)     |
| 행 잠금 획득/해제           |      | (파티션당 한 줄 실행이라 |
| 래치(짧은 내부 잠금)        |      |  잠금이 필요 없음)       |
| 스레드 경합 대기            |      |                          |
| 실제 작업  ← 아주 작은 조각 |      | 실제 작업  ← 거의 전부   |
+-----------------------------+      +--------------------------+
```

이 대비의 결론 — 느린 이유가 "일이 많아서"가 아니라 "일을 하기 위한 준비가 많아서"였다.

> **래치(latch)** — 데이터가 아니라 엔진 내부 자료구조를 잠깐 지키는 아주 짧은 잠금.\
> 예: 버퍼 목록을 고칠 때 0.001초 동안만 다른 스레드를 막는 것.

**무엇을 풀었나** — 데이터를 메모리에 올리고(in-memory), **shared-nothing**으로 파티셔닝한 뒤, 각 파티션에서 트랜잭션을 **단일 스레드로 직렬 실행**한다.\
잠금·래치가 아예 필요 없어지므로 경합 오버헤드가 사라진다.\
트랜잭션은 미리 컴파일된 Java 저장 프로시저로 실행된다.

**대가는 무엇인가** — 메모리 용량이 곧 데이터 한계이고, 한 파티션에서 오래 걸리는 트랜잭션 하나가 그 파티션 전체를 막는다.\
Spanner 계열이 "글로벌 분산 + 강한 일관성"에 집중했다면, VoltDB 계열은 "단일 데이터센터 초고속 OLTP"라는 다른 축의 NewSQL을 대표한다.

> **shared-nothing** — 노드끼리 디스크나 메모리를 공유하지 않고 각자 제 몫만 들고 있는 구조.\
> 예: 창고 10개가 서로 물건을 빌려주지 않고, 각 창고가 자기 구역 주문만 처리한다.

### CockroachDB (2015) — Spanner를 오픈소스로

**무엇** — 원자시계 없이 Spanner급 강한 일관성을 구현한 오픈소스 분산 SQL.

- **언제**: 2015년, 전 Google 엔지니어 Spencer Kimball·Peter Mattis·Ben Darnell이 Cockroach Labs 설립.
- **왜**: Spanner의 강력함을 본 이들이 "원자시계 없이도, 누구나 쓸 수 있는 오픈소스 Spanner"를 만들고자 했다.\
  바퀴벌레(cockroach)처럼 노드 일부가 죽어도 살아남는 회복력이 이름의 모티프다.

```text
 Spanner                         CockroachDB
+-------------------------+      +----------------------------+
| 합의: Paxos             |      | 합의: Raft                 |
| 시계: TrueTime          |      | 시계: HLC(하이브리드 논리) |
|   (GPS + 원자시계 필요) |      |   (특수 하드웨어 불필요)   |
+-------------------------+      +----------------------------+
 특수 하드웨어가 전제              범용 하드웨어에서 돌아간다
```

**무엇을 풀었나** — TrueTime이라는 특수 하드웨어 없이도 분산 트랜잭션의 강한 일관성을 구현했다.\
Spanner의 Paxos 대신 **Raft**로 복제 그룹의 합의를 이루고, TrueTime의 빈자리는 **하이브리드 논리 시계**(HLC, Hybrid Logical Clock)로 메운다.\
데이터를 자동으로 **range** 단위로 분할·복제하되, 사용자에게는 PostgreSQL 호환 SQL의 단일 논리 DB처럼 보인다.\
기본 격리 수준이 SQL 표준 최강인 **SERIALIZABLE**이라는 점이 특징으로, MVCC와 타임스탬프 순서화로 잠금 없이 직렬성을 보장한다.\
스토리지는 RocksDB 계열(이후 자체 엔진 Pebble)을 사용한다.

> **직렬성(serializability) / SERIALIZABLE** — 동시에 돌린 트랜잭션들의 결과가, 하나씩 차례로 돌린 어떤 순서의 결과와 같다는 성질.\
> 예: 두 이체를 동시에 처리해도 "먼저 하나, 다음 하나"로 한 것과 잔액이 똑같다.

> **MVCC(다중 버전 동시성 제어)** — 값을 덮어쓰지 않고 새 버전을 쌓아, 읽는 쪽은 과거 버전을 보게 해서 읽기와 쓰기가 서로 안 막게 하는 기법.\
> 예: 잔액을 고치는 중에도 조회는 "고치기 직전 값"을 잠금 없이 읽는다.

**대가는 무엇인가** — HLC는 TrueTime의 외부 일관성에는 약간 못 미친다.\
그 대신 범용 하드웨어에서 돌아간다는 것이 이 선택의 값어치다.

### TiDB (2015) — MySQL 호환 + HTAP

**무엇** — MySQL로 보이면서 수평 확장하고, 같은 데이터로 실시간 분석까지 돌리는 시스템.

- **언제**: 2015년 PingCAP이 개발 시작, 오픈소스.
- **왜**: 중국 인터넷 기업들이 MySQL 샤딩의 운영 지옥(수동 재샤딩, 교차 샤드 트랜잭션 불가, 분석 쿼리 불가)에 시달렸다.\
  "MySQL을 그대로 쓰면서 수평 확장하고, 거기에 실시간 분석까지"라는 요구가 있었다.

```text
애플리케이션 (MySQL 드라이버 그대로)
        ↓
TiDB 서버 (무상태 SQL 계층, MySQL 프로토콜 호환)   각각 따로 늘린다
        ↓
   ┌────┴─────────────────┐
   ↓                      ↓
TiKV (행 기반)      TiFlash (열 기반)
Raft 복제            Multi-Raft Learner 로 실시간 복제
OLTP 트랜잭션 담당    OLAP 분석 질의 담당
   ↑
PD (Placement Driver) — 메타데이터·스케줄러
```

**무엇을 풀었나** — **컴퓨트와 스토리지를 분리**한 계층 구조로 각각을 독립 확장한다.\
무상태 SQL 계층(TiDB 서버, MySQL 프로토콜 호환), 분산 KV 스토리지(**TiKV**, Raft 복제), 메타데이터·스케줄러(**PD, Placement Driver**)의 셋이다.\
결정적 차별점은 **HTAP**다.\
행 기반 엔진 TiKV에 더해 **열 기반 엔진 TiFlash**를 두고, **Multi-Raft Learner** 프로토콜로 두 엔진 간 데이터를 실시간 일관 복제한다.\
같은 데이터에 대해 OLTP(트랜잭션)는 TiKV가, OLAP(분석)는 TiFlash가 처리하므로, ETL로 데이터를 분석 DB에 따로 옮기지 않고도 **트랜잭션과 분석을 한 시스템에서** 수행한다.

> **행 기반 / 열 기반 저장** — 행 기반은 한 건의 모든 칼럼을 붙여 두고, 열 기반은 같은 칼럼의 값들을 붙여 둔다.\
> 예: "주문 한 건 전체 조회"는 행 기반이, "전체 주문 금액 합계"는 열 기반이 훨씬 빠르다.

**대가는 무엇인가** — 같은 데이터를 두 형태로 중복 보관하므로 저장 공간과 복제 부하가 늘어난다.\
여기서 뒤의 HTAP 절이 말하는 "데이터 이중화 없이"는 별도 분석 DB 사본을 따로 두지 않는다는 뜻으로, 한 시스템 안에 행·열 두 벌을 두는 것과는 층위가 다르다.

### YugabyteDB (2016) — PostgreSQL 호환 분산 SQL

**무엇** — PostgreSQL의 질의 계층을 통째로 재사용해, 익숙한 Postgres를 분산으로 돌리는 시스템.

- **언제**: 2016년, 전 Facebook 엔지니어들이 설립한 Yugabyte가 개발(2019년 핵심 전체 오픈소스화).
- **왜**: Spanner의 아키텍처를 따르되, 폐쇄적인 Cloud Spanner나 새 SQL 방언이 아니라 **개발자에게 익숙한 PostgreSQL 그대로**를 분산으로 제공하려 했다.
- **무엇을 풀었나**: SQL 계층(**YSQL**)이 **PostgreSQL의 쿼리 레이어 코드를 그대로 재사용**한다(Amazon Aurora PostgreSQL과 유사한 전략).\
  따라서 데이터 타입·함수·저장 프로시저·트리거·확장(extension)까지 PostgreSQL 기능을 광범위하게 물려받는다.\
  그 아래 분산 스토리지는 Spanner를 본떠 **Raft 합의 + HLC 기반 분산 ACID 트랜잭션**으로 강한 일관성을 보장한다.
- **왜 Raft인가**: Paxos가 아니라 Raft를 택한 이유는 명시적이다 — "Paxos보다 이해하기 쉽고, 동적 멤버십 변경 같은 운영 필수 기능을 제공하기 때문."

### Vitess (2011~) — 미들웨어 방식의 MySQL 수평 확장

**무엇** — 새 데이터베이스를 만드는 대신, 이미 돌고 있는 MySQL 무리 앞에 라우팅 계층을 세운 방식.

- **언제**: 2010년 YouTube에서 시작, 2011년부터 YouTube의 모든 DB 트래픽을 처리.\
  2018년 CNCF 인큐베이션, 2019년 졸업.
- **왜**: 처음부터 분산 DB를 새로 만드는 대신, **이미 운영 중인 거대한 MySQL 자산을 그대로 둔 채** 수평 확장하려는 현실적 요구.\
  YouTube는 읽기 복제 → 더 많은 복제 → 수동 샤딩의 진화 끝에 Vitess에 도달했다.

```text
 [ 손으로 샤딩 ]                    [ Vitess ]
 앱 코드가 샤드를 안다              앱은 MySQL 한 대로 본다
+----------------------------+      +-----------------------------+
| if id % 4 == 0: shard0     |      | 그냥 SELECT ... FROM ...    |
| 교차 샤드 조회는 앱이 합침 |      |         ↓                   |
| 재샤딩은 서비스 중단       |      | Vitess (라우팅·풀링·재샤딩) |
|                            |      |         ↓                   |
|                            |      | MySQL 수만 노드             |
+----------------------------+      +-----------------------------+
 → 샤딩 지식이 앱 코드에 박힌다     → 무중단 재샤딩이 뒤에서 일어난다
```

이 대비의 결론 — 샤딩 지식이 앱에서 미들웨어로 내려가면, 앱 코드를 안 고치고도 뒤를 바꿀 수 있다.

**무엇을 풀었나** — Pavlo·Aslett의 NewSQL 분류에서 **"투명 샤딩 미들웨어"** 부류를 대표한다.\
애플리케이션과 MySQL 사이에 **투명한 샤딩 계층**을 두어 쿼리 라우팅, 연결 풀링, **무중단 온라인 재샤딩**(resharding)을 처리한다.\
애플리케이션은 단일 MySQL처럼 보고 코드를 거의 바꾸지 않으면서, 그 뒤에서는 수만 개 MySQL 노드로 확장된다.\
Google의 Borg에서 시작한 태생 덕분에 Go와 Kubernetes를 일찍 받아들여, 클라우드 네이티브 환경의 MySQL 확장 표준이 됐다(Slack·Square·JD.com 등 채택).\
PlanetScale의 기반이기도 하다.

## 분산 SQL을 떠받치는 핵심 기술

### 합의 알고리즘 (Paxos · Raft)

**언제 나오나** — 여러 복제본이 "같은 순서로 같은 쓰기를 적용한다"를 보장해야 할 때.

분산 SQL의 강한 일관성은 결국 이 합의 위에 선다.\
한 데이터 조각은 보통 3~5개 복제본의 그룹으로 보관되고, 각 그룹은 합의 알고리즘으로 리더를 뽑아 쓰기를 직렬화한다.

- **Paxos**: Leslie Lamport가 정립한 합의의 고전.\
  이론적으로 완전하지만 이해·구현이 어렵기로 악명 높다. Spanner가 채택.
- **Raft**: 2014년 Diego Ongaro·John Ousterhout가 "이해 가능성(understandability)"을 명시적 설계 목표로 만든 합의 알고리즘.\
  리더 선출·로그 복제·멤버십 변경을 분리해 명료하게 정의했다.\
  CockroachDB·TiDB(TiKV)·YugabyteDB가 모두 Raft를 택한 이유가 여기 있다 — Paxos와 등가의 보장을 주면서 운영(동적 멤버십 변경)이 쉽다.

```text
하나의 거대한 트랜잭션이 아니라, 작은 합의 그룹의 집합

  전체 데이터를 range 로 쪼갠다
  ┌──────────┬──────────┬──────────┬──────────┐
  │ range A  │ range B  │ range C  │ range D  │
  └────┬─────┴────┬─────┴────┬─────┴────┬─────┘
       │          │          │          │
   Raft 그룹  Raft 그룹  Raft 그룹  Raft 그룹   ← 각각 독립적으로 합의
   (복제 3)   (복제 3)   (복제 3)   (복제 3)

  노드를 늘리면 → range 가 늘고 → 합의 그룹이 늘고 → 처리량이 선형 확장
```

핵심 통찰: NewSQL은 "**하나의 거대한 분산 트랜잭션"이 아니라 "수많은 작은 합의 그룹(range/region)의 집합**"으로 확장성을 얻는다.

> **합의(consensus)** — 메시지가 늦거나 유실되고 노드가 죽을 수 있는 환경에서, 여러 노드가 하나의 값·하나의 순서에 동의하는 것.\
> 예: 복제본 3개 중 2개가 "이 쓰기가 5번째다"에 동의하면 그것이 확정된 순서가 된다.

### 분산 트랜잭션 (2PC + MVCC + 논리 시계)

**언제 나오나** — 한 트랜잭션이 여러 range/노드에 걸칠 때.

시스템은 **2단계 커밋**(2PC)으로 원자성을 보장한다.\
단, 전통적 2PC의 약점(코디네이터 장애 시 블로킹)은 코디네이터 자체를 합의 그룹으로 복제해 보완한다.\
격리는 **MVCC**(다중 버전 동시성 제어)로 한다 — 각 쓰기에 타임스탬프를 붙여 버전을 쌓고, 읽기는 잠금 없이 특정 시점의 스냅샷을 본다.

> **2단계 커밋(2PC)** — 여러 참가자에게 먼저 "준비됐나" 묻고, 전원이 예라고 답해야 "커밋해" 하고 알리는 2단계 절차.\
> 예: 세 창고에서 동시에 재고를 빼야 할 때, 셋 다 준비되지 않으면 아무도 빼지 않는다.

트랜잭션 순서를 정하는 시계가 관건인데, 여기서 두 갈래가 갈린다.

- **TrueTime(Spanner)**: 특수 하드웨어로 실제 시간의 불확실성을 좁히고 commit-wait로 외부 일관성 달성.
- **HLC(CockroachDB·YugabyteDB)**: 물리 시계 + 논리 카운터를 결합한 하이브리드 논리 시계.\
  특수 하드웨어 없이 인과 순서를 보존하며, TrueTime의 외부 일관성에는 약간 못 미치지만 범용 하드웨어에서 직렬성을 제공한다.

### HTAP (Hybrid Transactional/Analytical Processing)

**언제 나오나** — "방금 들어온 거래"를 곧바로 분석해야 할 때.

전통적으로 OLTP(거래 처리)와 OLAP(분석)는 분리된 시스템이었고, 그 사이를 ETL 파이프라인이 밤마다 데이터를 퍼 날랐다.

```text
[ 전통: ETL 분리 ]                    [ HTAP ]
OLTP DB ──밤마다 ETL──> OLAP DB       하나의 클러스터
  낮 거래                분석용         TiKV(행) ←Raft→ TiFlash(열)
                                         ↑              ↑
  분석 결과 = "어제까지의 데이터"        거래 즉시      즉시 분석 가능
```

이 대비의 결론 — ETL 지연과 데이터 이중화 없이 "방금 들어온 거래를 곧바로 분석"하는 것이 HTAP의 가치다.

TiDB가 행 엔진(TiKV)과 열 엔진(TiFlash)을 Raft로 일관 복제해 두 워크로드를 한 클러스터에서 받는 것이 대표 사례다.

> **HTAP(Hybrid Transactional/Analytical Processing)** — 같은 데이터에 대해 트랜잭션 처리와 분석 질의를 한 시스템에서 함께 하는 것.\
> 예: 쇼핑몰이 주문을 받으면서, 같은 DB에서 "오늘 지금까지의 매출"을 실시간으로 뽑는다.

> **ETL** — 한 시스템에서 데이터를 뽑아(Extract) 변형하고(Transform) 다른 시스템에 싣는(Load) 일괄 작업.\
> 예: 매일 새벽 2시에 거래 DB의 하루치를 분석 DB로 복사하는 배치.

## 왜 그렇게 갔나 — 남은 선택지와 트레이드오프

같은 "분산 + SQL"이라는 목표를 두고도 갈림길마다 선택이 갈렸다.

```text
갈림길 1: 시간을 어떻게 맞출 것인가
   ├─ 특수 하드웨어로 실제 시간을 좁힌다 ... TrueTime  (Spanner)
   │     얻는 것: 외부 일관성 / 잃는 것: GPS·원자시계가 있어야 함
   └─ 논리 카운터로 인과만 보존한다 ....... HLC       (CockroachDB·Yugabyte)
         얻는 것: 범용 하드웨어 / 잃는 것: 외부 일관성에 약간 못 미침

갈림길 2: 합의를 무엇으로 할 것인가
   ├─ Paxos ... 이론적으로 완전 / 이해·구현이 어렵다
   └─ Raft .... 등가의 보장 + 동적 멤버십 변경이 쉽다

갈림길 3: SQL 표면을 어디서 가져올 것인가
   ├─ 새로 만든다 ................. Spanner
   ├─ PostgreSQL 호환으로 .......... CockroachDB
   ├─ PostgreSQL 코드 재사용 ....... YugabyteDB(YSQL)
   └─ MySQL 호환 ................... TiDB

갈림길 4: 아예 새로 만들 것인가
   ├─ 새 분산 DB를 만든다 .......... Spanner·CockroachDB·TiDB·Yugabyte
   └─ 기존 MySQL 앞에 계층만 둔다 ... Vitess (투명 샤딩 미들웨어)
         얻는 것: 기존 자산 보존 / 잃는 것: MySQL의 한계는 그대로 남음
```

읽는 법 — 오른쪽으로 갈수록 "이미 있는 것을 살린다", 왼쪽으로 갈수록 "처음부터 제대로 만든다"다.\
어느 쪽도 공짜가 아니라는 것이 이 갈림길들의 공통점이다.

VoltDB 계열은 아예 다른 축을 골랐다.\
"글로벌 분산 + 강한 일관성"이 아니라 "단일 데이터센터 초고속 OLTP"라는 축에서, 잠금 자체를 없애 극한의 처리량을 얻는 길이다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다)*

NewSQL·분산 SQL이 바꾼 것은 **"확장하려면 일관성을 포기해야 한다"는 2000년대의 통념**이다.\
Spanner는 그것이 공학적으로 가능함을 증명했고, CockroachDB·TiDB·YugabyteDB는 그 능력을 특수 하드웨어 없는 오픈소스로 민주화했다.\
그 결과 개발자는 다시 SQL과 ACID라는 익숙하고 강력한 추상 위에서, 결과적 일관성을 손으로 보정하는 코드를 걷어내고 비즈니스 로직에 집중할 수 있게 됐다.

흥미로운 것은 용어의 운명이다.\
451 Research가 만든 "NewSQL"은 2010년대 후반 들어 "**분산 SQL(Distributed SQL)**"이라는 명칭에 자리를 내줬다.\
한 시대를 정의했던 마케팅 용어가 기술이 주류로 정착하면서 더 직접적인 이름으로 흡수된 것이다.\
오늘날 Cloud Spanner·CockroachDB·TiDB·YugabyteDB·Vitess는 글로벌 규모의 미션 크리티컬 시스템을 받치고 있으며, "관계형이냐 분산이냐"를 더 이상 양자택일로 묻지 않게 만든 것이 이 세대의 가장 큰 유산이다.

```text
관계형 (SQL·ACID)
      ↓  웹 스케일 압박
NoSQL (확장성을 위해 SQL·ACID 포기)
      ↓  "보정 책임이 앱으로 넘어왔다"는 피로
NewSQL (둘의 종합 — 분산 위에서 SQL·ACID 복원)
      ↓  기술이 주류가 되자
분산 SQL (Distributed SQL) — 이름만 남고 "New" 는 떨어져 나감
```

NewSQL은 또한 데이터베이스 역사가 **순환**한다는 점을 보여준다.\
버려졌던 것이 더 높은 차원에서 복원되는 변증법적 진보의 전형이다.

## 용어 풀이

- **강한 일관성(strong consistency)** — 어느 노드에 물어도 최신 값을 읽는다는 보장.
- **결과적 일관성(eventual consistency)** — 지금은 달라도 언젠가 같아진다는 약한 보장.
- **외부 일관성(external consistency, strict serializability)** — 실제 시간의 앞뒤가 트랜잭션 순서의 앞뒤와 일치하는 성질.
- **직렬성(serializability)** — 동시 실행 결과가 하나씩 차례로 실행한 어떤 순서와 같은 성질. SQL 표준의 최강 격리 수준이 SERIALIZABLE.
- **샤딩(sharding) / 재샤딩(resharding)** — 데이터를 여러 서버로 쪼개 담는 것, 그리고 그 경계를 다시 나누는 것.
- **range** — 데이터를 쪼개는 단위. CockroachDB는 range, TiKV는 region이라 부른다. 각각이 자기 복제 그룹을 갖는다.
- **합의(consensus) · Paxos · Raft** — 불신뢰 네트워크에서 여러 노드가 하나의 순서에 동의하는 문제와 그 알고리즘들.
- **TrueTime** — 시간을 점이 아니라 불확실성 구간으로 노출하는 Google의 시계 API.
- **commit-wait** — 불확실성 구간이 지나갈 때까지 커밋 후 일부러 기다리는 것.
- **HLC(Hybrid Logical Clock)** — 물리 시계와 논리 카운터를 결합해 인과 순서를 보존하는 시계.
- **MVCC** — 값을 덮어쓰지 않고 버전을 쌓아 읽기와 쓰기가 서로 안 막게 하는 기법.
- **2단계 커밋(2PC)** — 전원 준비 확인 후 커밋을 알리는 분산 원자성 절차.
- **shared-nothing** — 노드끼리 저장소를 공유하지 않는 구조.
- **래치(latch)** — 엔진 내부 자료구조를 지키는 아주 짧은 잠금.
- **OLTP / OLAP** — 짧은 거래 처리 / 대량 스캔 분석.
- **HTAP** — OLTP와 OLAP을 한 시스템에서 처리하는 것.
- **ETL** — 추출·변형·적재의 일괄 데이터 이동 작업.
- **행 기반 / 열 기반 저장** — 한 건의 칼럼들을 붙여 두느냐, 같은 칼럼의 값들을 붙여 두느냐.
- **멱등(idempotent)** — 같은 요청이 여러 번 와도 결과가 한 번과 같게 만드는 성질.
- **투명 샤딩 미들웨어** — 앱은 단일 DB로 보게 하고 뒤에서 샤드로 라우팅하는 계층(Vitess).

## 참고 출처

- [Spanner: Google's Globally-Distributed Database (OSDI 2012, PDF)](https://research.google.com/archive/spanner-osdi2012.pdf)
- [Spanner: Google's Globally-Distributed Database (Google Research)](https://research.google/pubs/spanner-googles-globally-distributed-database-2/)
- [From NoSQL to New SQL: how Spanner became a global, mission-critical database (Google Cloud Blog, 2017)](https://cloudplatform.googleblog.com/2017/06/from-NoSQL-to-New-SQL-how-Spanner-became-a-global-mission-critical-database.html)
- [Spanner (database) — Wikipedia](https://en.wikipedia.org/wiki/Spanner_(database))
- [NewSQL — Wikipedia](https://en.wikipedia.org/wiki/NewSQL)
- [Andrew Pavlo & Matthew Aslett, "What's Really New with NewSQL?" (SIGMOD Record 2016, PDF)](https://db.cs.cmu.edu/papers/2016/pavlo-newsql-sigmodrec2016.pdf)
- [A Decade in Review: Distributed SQL Takes the Stage as NewSQL Exits (451 Alliance)](https://blog.451alliance.com/a-decade-in-review-distributed-sql-takes-the-stage-as-newsql-exits/)
- [CockroachDB: The Resilient Geo-Distributed SQL Database (SIGMOD 2020, PDF)](https://rcs.uwaterloo.ca/~ali/cs854-f23/papers/cockroachdb.pdf)
- [CockroachDB — Database of Databases](https://dbdb.io/db/cockroachdb)
- [TiDB — Wikipedia](https://en.wikipedia.org/wiki/TiDB)
- [TiDB Architecture FAQs (PingCAP Docs)](https://docs.pingcap.com/tidb/stable/tidb-faq/)
- [YugabyteDB — GitHub](https://github.com/yugabyte/yugabyte-db)
- [Distributed PostgreSQL on a Google Spanner Architecture (Yugabyte Blog)](https://www.yugabyte.com/blog/distributed-postgresql-on-a-google-spanner-architecture-storage-layer/)
- [VoltDB — Wikipedia](https://en.wikipedia.org/wiki/VoltDB)
- [The Vitess Docs — History](https://vitess.io/docs/20.0/overview/history/)
- [CNCF to host Vitess (CNCF Blog, 2018)](https://www.cncf.io/blog/2018/02/05/cncf-host-vitess/)
