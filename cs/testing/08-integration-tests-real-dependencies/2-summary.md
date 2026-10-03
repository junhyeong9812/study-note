# testing/08-integration-tests-real-dependencies — 실제 DB·브로커로 하는 통합 테스트(Testcontainers) — 정리 (힌트)

## 해결하는 문제

단위 테스트는 DB·브로커를 테스트 더블이나 인메모리 대용품으로 바꿔 빠르게 돈다. 대가는 **충실도**다.

- *충실도(fidelity)*: 테스트가 실제 시스템의 동작을 얼마나 그대로 비추는가. SWE@G 14장의 정의는 "테스트가 SUT의 실제 동작을 반영하는 성질"이다.
  - *SUT(System Under Test)*: 테스트 대상 시스템.

```text
  빠름·안정 ◀──────────────────────────────────────────────▶ 충실
  mock 리포지토리   인메모리 Fake    H2(PostgreSQL 모드)    실제 PostgreSQL 17 컨테이너    운영
       │                │                 │                        │
       └ SQL을 안 탄다    └ SQL을 안 탄다     └ SQL은 타지만 다른 엔진     └ 운영과 같은 엔진·같은 판
```

쉬운 예: 운전 연습을 시뮬레이터로만 했다.

- 시뮬레이터에서는 브레이크가 늘 같은 거리에서 선다. 실제 도로는 노면·타이어에 따라 다르다.
- 시뮬레이터 합격은 "시뮬레이터에서 운전할 줄 안다"는 뜻이다.

똑같은 구조다.\
H2로 통과한 테스트는 "H2에서 동작한다"는 뜻이다. 운영 DB가 PostgreSQL이면 방언·락·트랜잭션 의미가 다른 곳에서 운영에서만 실패한다.

실무 예:

- 중복 키를 잡아 무시하는 코드가 H2 테스트에서는 초록인데, PostgreSQL에서는 그 뒤 문장들이 `ROLLBACK` 전까지 `25P02 current transaction is aborted`로 거부된다(아래 실험).
- `INSERT ... ON CONFLICT DO UPDATE`·`jsonb`·`->>`를 쓰는 쿼리는 H2 테스트 자체가 문법 오류로 막혀, 그 경로를 아예 테스트하지 못한다.
- 락 대기 실패의 SQLSTATE가 달라(H2 `HYT00` vs PostgreSQL `55P03`) 예외 변환·재시도 분기가 테스트에서 다른 길을 탄다.

## 동작·원리

### 1. 통합 테스트는 어디까지 진짜인가

```text
   [테스트 코드] ──▶ [리포지토리/DAO] ──JDBC──▶ [DB]
                    └── 여기까지 내 코드 ──┘     └ 진짜 엔진이면 "실제 의존 통합 테스트"

   해석: SWE@G 14장의 "하나 이상의 상호작용하는 바이너리 기능 테스트" 중 가장 작은 형태
```

- *통합 테스트*: 정의가 사람마다 다르다. Fowler "IntegrationTest"(2018)는 두 가지를 구분한다.
  - 좁은 통합 테스트: 내 서비스 중 외부 서비스와 대화하는 코드만 돌린다. 상대 서비스는 프로세스 안·밖의 테스트 더블로 둔다.
  - 넓은 통합 테스트: 모든 서비스의 실제 판을 띄우고 서비스 전체를 지나는 경로를 돌린다.
  - 이 노트의 테스트는 범위는 좁은 쪽처럼 "DB와 대화하는 코드"만이다. 다만 상대를 더블이 아니라 **실제 DB·브로커 엔진 하나**로 둔다(Fowler 정의를 그대로 옮긴 것은 아니다).
- SWE@G 14장이 꼽은 "단위 테스트가 놓치는 것" 중 이 노트가 겨냥하는 것
  - *충실하지 않은 더블(unfaithful doubles)*: 대체품과 원본이 다르게 동작한다. mock은 원본이 바뀌어도 그대로 남아 낡는다.
  - *설정 문제*: 바이너리와 설정의 호환은 단위 테스트로 못 본다.
- 반대 방향의 비용: 실제 의존을 붙이면 느려지고, 환경 문제로 불안정해질 수 있다. SWE@G 14장은 **밀폐성(hermeticity)** 과 충실도가 서로 당긴다고 적는다.
  - *밀폐성*: 테스트가 외부 환경(공유 DB·네트워크)에 기대지 않고 자기 안에서 완결되는 정도.
  - Testcontainers는 "테스트마다 새 컨테이너"로 실제 엔진을 쓰면서 밀폐성을 지키려는 도구다.

### 2. Testcontainers가 하는 일

```text
   JUnit 5 테스트 JVM
     │ ① Docker API 연결(/var/run/docker.sock)
     │ ② Ryuk(정리 담당 컨테이너) 기동 ── JVM이 끝나면 라벨 붙은 컨테이너를 지운다
     │ ③ postgres:17 컨테이너 기동, 무작위 호스트 포트에 5432 매핑
     │ ④ 준비될 때까지 대기(로그·포트 대기 전략)
     ▼ ⑤ getJdbcUrl() → jdbc:postgresql://<host>:<무작위 포트>/test
   테스트 본문 ──JDBC──▶ 진짜 PostgreSQL 17
     │ ⑥ stop() 또는 JVM 종료 → 컨테이너 제거
```

- *Ryuk*: Testcontainers의 "resource reaper". 문서 표현으로 "JVM 종료 시 컨테이너를 지우고 죽은 컨테이너를 정리"한다. 테스트가 비정상 종료해도 컨테이너가 남지 않게 한다.
  - moby-ryuk README: 연결한 클라이언트 수를 세다가, 마지막 연결이 끊기고 `RYUK_RECONNECTION_TIMEOUT`(기본 10s)이 지나면 등록된 라벨 필터에 맞는 자원을 지우고 스스로 끝난다.
- JUnit 5 수명(Testcontainers JUnit 5 문서)
  - `@Container`를 **static 필드**에 두면 클래스의 테스트 메서드들이 공유한다. 첫 테스트 전에 한 번 켜고 마지막 테스트 뒤에 끈다.
  - **인스턴스 필드**에 두면 테스트 메서드마다 켜고 끈다.
  - 문서는 이 확장을 순차 실행에서만 시험했고 병렬 실행은 "지원하지 않는다"고 적는다. 여러 클래스가 하나를 같이 쓰려면 싱글턴 컨테이너 패턴(수동 수명 관리)을 쓴다.
- 컨테이너 안에서 테스트를 돌릴 때(CI 러너가 컨테이너인 경우): Docker 소켓을 마운트하고, Testcontainers가 기본 게이트웨이 IP를 쓰거나 `TESTCONTAINERS_HOST_OVERRIDE`로 호스트 이름을 정한다(문서 "Patterns for running tests inside a Docker container").

### 3. 실험: 같은 SQL, H2(PostgreSQL 모드) vs PostgreSQL 17

H2는 PostgreSQL 호환 모드의 권장 URL로 띄웠다. H2 문서가 권하는 설정 그대로다.

```text
jdbc:h2:mem:probe;MODE=PostgreSQL;DATABASE_TO_LOWER=TRUE;DEFAULT_NULL_ORDERING=HIGH
```

프로브 코드(핵심) — 두 DB에 같은 함수를 돌려 결과나 SQLSTATE를 찍는다.

```java
both("tx-after-dup-key", (a, b) -> {
  Statement s = a.createStatement();
  s.execute("drop table if exists u; create table u(id int primary key)");
  a.setAutoCommit(false);
  s.execute("insert into u values (1)");
  try { s.execute("insert into u values (1)"); } catch (SQLException e) { /* 중복은 무시하고 계속 */ }
  s.execute("insert into u values (2)");
  a.commit();
  return "committed " + rows(s.executeQuery("select id from u order by id"));
});

both("skip-locked", (a, b) -> {          // a, b = 같은 DB의 두 커넥션(두 워커)
  ...
  String q = "select id from job where done = false order by id limit 1 for update skip locked";
  a.setAutoCommit(false); b.setAutoCommit(false);
  String w1 = rows(a.createStatement().executeQuery(q));
  String w2 = rows(b.createStatement().executeQuery(q));
  ...
});
```

(실험, JDK 21 temurin · JUnit 5.13.4 · Testcontainers 2.0.5 · postgres:17 이미지(PostgreSQL 17.11) · H2 2.5.252 · PostgreSQL JDBC 42.7.13, 2026-10-03)

```text
version                H2    [PostgreSQL 8.2.23 server protocol using H2 2.5.252 (2026-09-23)]
version                PG17  [PostgreSQL 17.11 (Debian 17.11-1.pgdg13+2) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit]
null-order             H2    asc=[3, 1, 2] desc=[2, 1, 3]
null-order             PG17  asc=[3, 1, 2] desc=[2, 1, 3]
upsert                 H2    SQLException 42000: Syntax error in SQL statement "insert into kv values ('a', 1) [*]on conflict (k) do update set n = kv.n + excluded.n"; SQL stateme…
upsert                 PG17  [2]
tx-after-dup-key       H2    committed [1, 2]
tx-after-dup-key       PG17  SQLException 25P02: ERROR: current transaction is aborted, commands ignored until end of transaction block
skip-locked            H2    worker1=[1] worker2=[2]
skip-locked            PG17  worker1=[1] worker2=[2]
nowait                 H2    SQLException HYT00: Timeout trying to lock table "acc"; SQL statement:
nowait                 PG17  SQLException 55P03: ERROR: could not obtain lock on row in relation "acc"
jsonb                  H2    SQLException 42000: Syntax error in SQL statement "select body-[*]>>'name' from doc"; SQL statement:
jsonb                  PG17  [kim]
text-vs-int-compare    H2    [10, 9]
text-vs-int-compare    PG17  SQLException 42883: ERROR: operator does not exist: character varying > integer
```

| 항목 | H2 2.5.252(PG 모드) | PostgreSQL 17.11 | 차이의 종류 |
|---|---|---|---|
| NULL 정렬(권장 URL) | 같음 | 기준 | 설정으로 맞춤 |
| `ON CONFLICT DO UPDATE` | 문법 오류 | 동작 | 방언 — 테스트가 그 경로를 못 탄다 |
| 오류 뒤 같은 트랜잭션 계속 | 커밋됨 `[1, 2]` | `25P02`로 거부 | **트랜잭션 의미** — 가장 위험 |
| `FOR UPDATE SKIP LOCKED` | 같음 | 기준 | 이 판에서는 같음 |
| `FOR UPDATE NOWAIT` 실패 | `HYT00`(타임아웃) | `55P03`(lock_not_available) | 예외 분류가 다르다 |
| `jsonb`·`->>` | 문법 오류 | 동작 | 방언 |
| `varchar > 5` | 암묵 변환, `[10, 9]` | `42883` 오류 | 타입 규칙 |

- NULL 정렬은 설정 의존이다. 같은 날 `DEFAULT_NULL_ORDERING=HIGH`를 빼고 돌리면 H2가 NULL을 앞에 둔다.

(실험, 같은 환경)

```text
jdbc:h2:mem:n1;MODE=PostgreSQL -> asc=[2, 3, 1]
jdbc:h2:mem:n2;MODE=PostgreSQL;DEFAULT_NULL_ORDERING=HIGH -> asc=[3, 1, 2]
```

- 해석: 차이에는 세 층이 있다.
  1. **문법 방언**(upsert·jsonb) — H2에서 바로 터진다. 시끄러워서 차라리 낫다.
  2. **설정으로 맞출 수 있는 것**(NULL 정렬) — URL 옵션을 빠뜨리면 조용히 다르다.
  3. **트랜잭션·락 의미**(오류 뒤 계속, 락 실패 코드) — H2에서는 **초록**이다. 운영에서만 실패한다. 커리큘럼 ⚠ 칸의 "락 동작 차이로 운영에서만 실패"가 이것이다.
- H2 문서는 호환 모드가 데이터베이스 사이 차이의 "작은 일부(a small subset)"만 흉내 낸다고 적는다. PostgreSQL 모드 항목에 `ON CONFLICT DO NOTHING`은 있지만 `DO UPDATE`는 없다 — 위 출력과 맞는다.

### 4. 실험: "H2에서 초록, PostgreSQL에서 빨강"인 테스트

```java
/** 운영 코드(단순화): 한 트랜잭션에서 태그들을 저장, 중복 키는 잡아서 무시 */
static void saveTags(Connection c, List<String> tags) throws SQLException {
  c.setAutoCommit(false);
  try (PreparedStatement ps = c.prepareStatement("insert into tag(name) values (?)")) {
    for (String t : tags) {
      ps.setString(1, t);
      try { ps.executeUpdate(); }
      catch (SQLException e) { if (!"23505".equals(e.getSQLState())) throw e; } // 중복이면 건너뜀
    }
    c.commit();
  } catch (SQLException e) { c.rollback(); throw e; }
}

@ParameterizedTest @ValueSource(strings = {"h2", "postgres17"})
void duplicateTagIsSkipped(String db) throws Exception {
  try (Connection c = open(db)) {
    c.createStatement().execute("drop table if exists tag; create table tag(name varchar(20) primary key)");
    saveTags(c, List.of("java", "java", "sql"));
    ResultSet rs = c.createStatement().executeQuery("select count(*) from tag");
    rs.next();
    assertEquals(2, rs.getInt(1));
  }
}
```

(실험, 같은 환경 — surefire 출력 발췌. 시간 값은 실행마다 다르다 — 점검 재실행에서는 3.920 s·0.084 s)

```text
[ERROR] Tests run: 3, Failures: 0, Errors: 1, Skipped: 0, Time elapsed: 9.617 s <<< FAILURE! -- in TagServiceTest
[ERROR] TagServiceTest.duplicateTagIsSkipped(String)[2] -- Time elapsed: 0.565 s <<< ERROR!
org.postgresql.util.PSQLException: ERROR: current transaction is aborted, commands ignored until end of transaction block
	at TagServiceTest.saveTags(TagServiceTest.java:27)
```

- `[1]`(h2)은 통과, `[2]`(postgres17)만 실패했다. 3개 중 나머지 하나는 NULL 정렬 출력 테스트다.
- 원인: PostgreSQL은 트랜잭션 안에서 문장 하나가 실패하면 트랜잭션 전체를 "중단(aborted)" 상태로 둔다. 이후 문장은 `ROLLBACK`까지 거부한다.
  - PostgreSQL 17 문서 3.4 Transactions: `ROLLBACK TO`(세이브포인트)가 오류로 중단된 트랜잭션 블록의 제어를 되찾는 유일한 방법이다(전체 롤백 제외).
  - SQLSTATE `25P02` = `in_failed_sql_transaction`(부록 A).
- 고친 판: 오류를 내지 않는 문장으로 바꾼다.

```java
"insert into tag(name) values (?) on conflict (name) do nothing"
```

(실험, 같은 환경, 2회) `@Testcontainers` + static `@Container`로 고친 판을 돌렸다. 통과했다.

```text
[main] INFO tc.testcontainers/ryuk:0.14.0 - Container testcontainers/ryuk:0.14.0 started in PT1.641587056S
[main] INFO tc.postgres:17 - Container postgres:17 started in PT3.472551658S
test body ms=511
wall=22.59s
...
[main] INFO tc.postgres:17 - Container postgres:17 started in PT3.494274007S
test body ms=512
wall=19.57s
```

- 비용: 컨테이너 기동이 약 3~3.5초, Ryuk 약 1.5~1.6초(이 머신·`--cpus=2` 제한, 이미지가 이미 있을 때 — 점검 재실행 2회는 postgres 3.02·3.32초, Ryuk 1.50·1.55초, wall 17.5·17.6초). `wall`은 maven 기동·컴파일을 포함한 전체 시간이다.
- 이미지를 처음 받는 CI에서는 내려받기 시간이 더해진다(이 실험은 내려받지 않았다).

## 쓰이는 자료구조·알고리즘

- **트랜잭션 상태 기계** — PostgreSQL 세션: `idle → in transaction → (오류) failed transaction → ROLLBACK/ROLLBACK TO → ...`. 실험의 25P02는 `failed` 상태에서 들어온 문장이다. 상태 전이 테스트 설계는 [07-test-design-techniques](../07-test-design-techniques/2-summary.md)에서 다룬다.
- **행 락 + 대기 큐** — `FOR UPDATE`는 행 락을 잡고, 다른 트랜잭션은 큐에서 기다린다. `NOWAIT`는 기다리지 않고 실패, `SKIP LOCKED`는 잠긴 행을 건너뛴다. [database/15-two-phase-locking-and-deadlock](../../database/15-two-phase-locking-and-deadlock/2-summary.md), [database/18-app-level-concurrency-patterns](../../database/18-app-level-concurrency-patterns/2-summary.md).
- **유일 인덱스 조회** — `ON CONFLICT`는 충돌 대상 열의 유일 인덱스(PostgreSQL 기본 B-Tree)로 충돌을 판정한다. [database/08-btree-indexes](../../database/08-btree-indexes/2-summary.md).
- **참조 카운트식 정리(Ryuk)** — 컨테이너에 세션 라벨을 붙이고, 연결 수가 0이 된 뒤 재연결 대기(기본 10s)가 지나면 그 라벨을 가진 자원을 지운다. 테스트 쪽은 "만든 것을 기록 → 끝에 일괄 회수"라는 단순한 소유권 관리다.

## 적용 — 풀어나가는 법

### 1. 어떤 테스트를 실제 의존으로 올리나

```text
  운영 DB 고유 기능을 쓰나? ── 예 ──▶ 실제 엔진 통합 테스트(Testcontainers)
        │ 아니오
  트랜잭션·락·오류 처리 경로인가? ── 예 ──▶ 실제 엔진
        │ 아니오
  순수 매핑·도메인 계산인가? ── 예 ──▶ 단위 테스트 + Fake(03번)
```

- 실제 엔진으로 올릴 대상: 리포지토리의 SQL, 마이그레이션 스크립트([database/26-schema-migration](../../database/26-schema-migration/2-summary.md)), 트랜잭션 경계·재시도, 락 경합 경로.
- 도메인 규칙까지 전부 컨테이너로 돌리면 느린 테스트가 쌓인다. 피라미드 균형은 [01-why-test-and-pyramid](../01-why-test-and-pyramid/2-summary.md).

### 2. JUnit 5 + Testcontainers 2.x 골격 (Java)

```java
@Testcontainers
class TagRepositoryIT {
  @Container static PostgreSQLContainer pg = new PostgreSQLContainer("postgres:17"); // 운영과 같은 메이저 판으로 고정

  @Test void duplicateTagIsSkipped() throws Exception {
    try (Connection c = DriverManager.getConnection(pg.getJdbcUrl(), pg.getUsername(), pg.getPassword())) {
      // 스키마는 운영과 같은 마이그레이션 도구(Flyway·Liquibase)로 올리는 편이 충실하다
      ...
    }
  }
}
```

- Testcontainers 2.0에서는 모듈 클래스가 `org.testcontainers.postgresql.PostgreSQLContainer`, 의존성은 `testcontainers-postgresql`이다(1.x의 `org.testcontainers:postgresql`·`org.testcontainers.containers.PostgreSQLContainer`에서 바뀜 — 2.0.5는 실험 컴파일, 1.21.4는 jar 목록으로 확인).
- 이미지 태그는 운영 판에 맞춰 고정한다. `latest`는 어느 날 메이저가 바뀌어 테스트 결과가 달라질 수 있다.
- 브로커도 같은 방식이다. Kafka 모듈 문서의 예: `new KafkaContainer("apache/kafka-native:3.8.0")` → `kafka.getBootstrapServers()`. (이 노트는 DB만 실험했다.)

### 3. Spring Boot에서 (문서 기준)

- Spring Boot 4.1.1 문서: `@DataJpaTest`는 "임베디드 DB가 클래스패스에 있으면 그것도 구성한다". 실제 DB로 돌리려면 `@AutoConfigureTestDatabase(replace = Replace.NONE)`을 붙인다.
  - 판에 따라 다르다. `@AutoConfigureTestDatabase`의 `replace` 기본값은 Spring Boot 3.3까지 `ANY`(어떤 DataSource든 임베디드로 교체), 3.4부터 `NON_TEST`다(소스 확인).
  - `NON_TEST`는 `@ServiceConnection` 컨테이너·`@DynamicPropertySource`로 준 URL·Testcontainers JDBC URL을 "테스트 DB"로 보고 교체하지 않는다.
  - 그래서 H2로 조용히 바뀌는 경우는 3.3 이하이거나, 컨테이너를 위 방식이 아닌 길(직접 만든 DataSource 빈 등)로 연결했을 때다. 로그의 JDBC URL을 확인한다.
- `@ServiceConnection`: 컨테이너 필드에 붙이면 연결 정보 빈을 만들어 연결 관련 설정 속성보다 우선 적용한다. 더 유연한 대안은 `@DynamicPropertySource`.
- 문서 경고: static 컨테이너는 테스트 클래스가 끝나면 멈추는데, Spring 테스트 컨텍스트 캐시는 그 뒤에도 컨텍스트를 재사용할 수 있다. 컨텍스트가 캐시되는 동안 컨테이너를 살려 두려면 컨테이너를 Spring 빈으로 관리하라고 권한다.

### 4. 진단 순서 — "운영에서만 실패"

1. 실패 SQLSTATE를 본다. `25P02`면 앞선 문장의 오류를 찾는다(로그에서 같은 트랜잭션의 첫 오류).
2. 테스트가 실제로 어느 DB로 돌았는지 확인한다 — 테스트 로그의 JDBC URL, `select version()`.
3. 같은 테스트를 Testcontainers 판으로 돌려 재현한다(운영과 같은 메이저 판 이미지).
4. 재현되면 고치고, 그 테스트를 실제 엔진 테스트 묶음에 남긴다.

### 5. CI에서 돌리는 법 (이 실험의 방식)

```bash
docker run --rm -u "$(id -u):$(id -g)" --group-add "$(stat -c %g /var/run/docker.sock)" -e HOME=/tmp \
  -v /var/run/docker.sock:/var/run/docker.sock -v "$PWD":/w -w /w \
  -e TESTCONTAINERS_RYUK_CONTAINER_IMAGE=testcontainers/ryuk:0.14.0 \
  --add-host=host.docker.internal:host-gateway -e TESTCONTAINERS_HOST_OVERRIDE=host.docker.internal \
  maven:3.9-eclipse-temurin-21 mvn -q test
docker ps -a --filter label=org.testcontainers=true   # 끝난 뒤 내 실행이 남긴 것이 없어야 한다
```

- 이 실험에서 실행 전후 라벨 컨테이너 수는 4 → 4였다. 남은 4개는 이 실험 전부터 있던 다른 작업의 것이다. Ryuk는 테스트 JVM이 끝나고 수 초 뒤 스스로 사라졌다(관찰).

## 장애 시나리오와 대처

### 1. ⚠ H2로는 초록, 운영 PostgreSQL에서만 실패

- 현상: 배포 뒤 특정 요청만 500. 같은 기능의 테스트는 통과했다.
- 보이는 형태: `PSQLException: ERROR: current transaction is aborted, commands ignored until end of transaction block`(25P02), 또는 `operator does not exist: character varying > integer`(42883).
- 원인: 테스트 DB가 H2였다. H2는 오류 뒤 트랜잭션을 계속 허용하고, 타입을 암묵 변환한다(실험).
- 대처: 리포지토리·트랜잭션 테스트를 운영과 같은 엔진(Testcontainers)으로 옮긴다. 오류를 삼키고 계속하는 코드는 `ON CONFLICT`·세이브포인트로 바꾼다.

### 2. ⚠ 락 실패 처리가 테스트와 운영에서 다른 길을 탄다

- 현상: 운영에서 락 경합 때 재시도가 안 되고 바로 500.
- 보이는 형태: 운영 로그 `55P03 could not obtain lock on row`. 테스트에서는 `HYT00 Timeout trying to lock table`이었다.
- 원인: 재시도 분기를 SQLSTATE나 예외 타입으로 나눴는데, 테스트 DB의 코드가 달랐다.
- 대처: 재시도 분기는 실제 엔진으로 테스트한다. 예외 변환 계층(예: Spring의 SQLSTATE 변환)을 거친 뒤의 타입으로 판정한다.

### 3. 통합 테스트가 느려 아무도 안 돌린다

- 현상: 테스트 단계가 수십 분. 개발자가 로컬에서 건너뛴다.
- 보이는 형태: 클래스마다(또는 테스트 메서드마다) 컨테이너 기동 로그(`started in PT3.4S`)가 반복된다.
- 원인: 인스턴스 필드 `@Container`(메서드마다 기동)나 클래스마다 새 컨테이너.
- 대처: static 필드 또는 싱글턴 컨테이너로 공유하고, 테스트 사이 격리는 트랜잭션 롤백·테이블 비우기로 한다. 공유하면 테스트 사이 데이터 오염이 생길 수 있다 — [09-flaky-tests](../09-flaky-tests/2-summary.md)·[11-test-data-and-fixtures](../11-test-data-and-fixtures/2-summary.md).

### 4. CI에서 Testcontainers가 Docker를 못 찾는다·포트에 못 붙는다

- 현상: `Could not find a valid Docker environment`, 또는 컨테이너는 떴는데 JDBC 연결 시간 초과.
- 원인: 러너 컨테이너에 Docker 소켓이 없거나 권한(그룹)이 없다. 컨테이너 안에서 `localhost`로 형제 컨테이너 포트를 찾는다.
- 대처: 소켓 마운트 + 그룹 추가, 호스트 이름은 문서 방식(`TESTCONTAINERS_HOST_OVERRIDE` 등)으로 정한다.

### 5. 컨테이너가 남아 쌓인다

- 현상: CI 머신 디스크·메모리 고갈, `docker ps -a`에 테스트 컨테이너가 수백 개.
- 원인: Ryuk를 끄고(`TESTCONTAINERS_RYUK_DISABLED=true`) 비정상 종료한 실행이 정리되지 않았다.
- 대처: Ryuk를 켜 두거나, 끌 수밖에 없는 환경이면 파이프라인 끝에서 자기 실행의 라벨로만 지운다. 남의 컨테이너까지 지우는 일괄 정리(`prune`)는 공유 머신에서 피한다.

## 핵심 문장

- 통합 테스트의 가치는 충실도다. H2 같은 대용품에서 통과했다는 것은 "그 대용품에서 동작한다"는 뜻이다.
- 실험에서 H2(PostgreSQL 모드)와 PostgreSQL 17은 upsert·jsonb 문법, 오류 뒤 트랜잭션 계속, 락 실패 코드, 문자열–정수 비교에서 달랐다.
- 가장 위험한 차이는 문법이 아니라 트랜잭션 의미다 — H2에서 초록인 테스트가 PostgreSQL에서 25P02로 실패했다.
- Testcontainers는 테스트마다 운영과 같은 엔진을 띄우고 Ryuk로 정리해, 충실도와 밀폐성을 함께 얻으려 한다. 대가는 기동 시간(이 환경에서 약 3~3.5초)이다.
- 실제 엔진으로 올릴 대상은 SQL·마이그레이션·트랜잭션·락 경로이고, 순수 도메인 계산은 단위 테스트에 둔다.

## 관련 주제·근거

- 선행
  - [03-test-doubles](../03-test-doubles/2-summary.md). Fake·mock이 실제와 다른 계약을 흉내 낼 때.
  - [01-why-test-and-pyramid](../01-why-test-and-pyramid/2-summary.md). 크기·범위와 피라미드.
- 후속·연결
  - [13-contract-testing](../13-contract-testing/2-summary.md) — 서비스 사이 의존은 계약 테스트로.
  - [18-e2e-and-ui-testing](../18-e2e-and-ui-testing/2-summary.md) — 더 넓은 범위의 테스트.
  - [09-flaky-tests](../09-flaky-tests/2-summary.md). 공유 컨테이너·네트워크가 만드는 불안정.
  - database [13-transactions-acid](../../database/13-transactions-acid/2-summary.md), [15-two-phase-locking-and-deadlock](../../database/15-two-phase-locking-and-deadlock/2-summary.md), [18-app-level-concurrency-patterns](../../database/18-app-level-concurrency-patterns/2-summary.md)(SKIP LOCKED 작업 큐), [26-schema-migration](../../database/26-schema-migration/2-summary.md), [24-transaction-boundaries-in-app-code](../../database/24-transaction-boundaries-in-app-code/2-summary.md)
- 교재
  - Winters·Manshreck·Wright 『Software Engineering at Google』 14장 "Larger Testing"(Joseph Graves) — Fidelity, Common Gaps in Unit Tests(Unfaithful doubles·Configuration issues·…), The System Under Test(hermetic SUT), Functional Testing of One or More Interacting Binaries <https://abseil.io/resources/swe-book/html/ch14.html>
  - Fowler "IntegrationTest"(2018) — 좁은 통합 테스트(상대 서비스는 테스트 더블)·넓은 통합 테스트(모든 서비스 실제 판) <https://martinfowler.com/bliki/IntegrationTest.html>
- 제품 문서
  - Testcontainers for Java — JUnit 5(static 공유·인스턴스 필드, 병렬 미지원) <https://java.testcontainers.org/test_framework_integration/junit_5/>, 컨테이너 안에서 실행(소켓 마운트·`TESTCONTAINERS_HOST_OVERRIDE`) <https://java.testcontainers.org/supported_docker_environment/continuous_integration/dind_patterns/>, 설정(Ryuk·`TESTCONTAINERS_RYUK_DISABLED`) <https://java.testcontainers.org/features/configuration/>, moby-ryuk README(`RYUK_RECONNECTION_TIMEOUT` 기본 10s) <https://github.com/testcontainers/moby-ryuk>, Kafka 모듈 <https://java.testcontainers.org/modules/kafka/>
  - H2 Features — Compatibility Modes("only a small subset of the differences"), PostgreSQL Compatibility Mode(권장 URL, `ON CONFLICT DO NOTHING`) <https://www.h2database.com/html/features.html>
  - PostgreSQL 17 — 3.4 Transactions(`ROLLBACK TO`) <https://www.postgresql.org/docs/17/tutorial-transactions.html>, 부록 A 오류 코드(23505·25P02·42883·55P03) <https://www.postgresql.org/docs/17/errcodes-appendix.html>
  - Spring Boot 4.1.1 — `AutoConfigureTestDatabase.Replace` 기본값(v3.3.0 `ANY`, v3.4.0·v4.1.1 `NON_TEST`) <https://github.com/spring-projects/spring-boot/blob/v4.1.1/module/spring-boot-jdbc-test/src/main/java/org/springframework/boot/jdbc/test/autoconfigure/AutoConfigureTestDatabase.java>, Testcontainers(`@ServiceConnection`·`@DynamicPropertySource`·컨텍스트 캐시 경고) <https://docs.spring.io/spring-boot/reference/testing/testcontainers.html>, Testing Spring Boot Applications(`@DataJpaTest`·`@AutoConfigureTestDatabase(replace = Replace.NONE)`) <https://docs.spring.io/spring-boot/reference/testing/spring-boot-applications.html>
- 실험 목록
  - DialectProbeTest — H2 2.5.252(PG 모드 권장 URL) vs PostgreSQL 17.11(Testcontainers 2.0.5, postgres:17 이미지, Ryuk 0.14.0)에서 NULL 정렬·upsert·오류 뒤 계속·SKIP LOCKED·NOWAIT·jsonb·문자열–정수 비교. maven:3.9-eclipse-temurin-21 컨테이너(Docker 소켓 마운트, `--cpus=2`), JUnit 5.13.4, 2026-10-03.
  - TagServiceTest — 같은 `@ParameterizedTest`가 H2 통과·PostgreSQL 25P02 실패, H2 `DEFAULT_NULL_ORDERING` 유무에 따른 NULL 위치.
  - TagServiceFixedTest — `ON CONFLICT DO NOTHING` 판이 PostgreSQL에서 통과, 컨테이너 기동 시간 2회.
