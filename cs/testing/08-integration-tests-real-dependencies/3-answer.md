# testing/08-integration-tests-real-dependencies — 정답

## 정답

### 1. 대용품이 못 보는 것

- *충실도*: 테스트가 실제 SUT 동작을 얼마나 그대로 비추나(SWE@G 14장). mock·Fake는 SQL을 아예 타지 않고, H2는 SQL을 타지만 다른 엔진이다.
- 못 보는 것: 운영 DB의 방언(upsert·jsonb), 트랜잭션 의미(오류 뒤 계속 가능 여부), 락 실패 코드, 타입 규칙. SWE@G 14장은 이것을 "충실하지 않은 더블"·"설정 문제"로 분류한다.
- *밀폐성*: 테스트가 공유 환경에 기대지 않는 정도. 실제 엔진을 공유 DB로 붙이면 충실도는 오르지만 밀폐성이 떨어진다. Testcontainers는 테스트 전용 컨테이너로 둘을 함께 얻으려 한다.

### 2. 오류 뒤 같은 트랜잭션 계속

(실험, H2 2.5.252 · PostgreSQL 17.11, 2026-10-03)

```text
tx-after-dup-key       H2    committed [1, 2]
tx-after-dup-key       PG17  SQLException 25P02: ERROR: current transaction is aborted, commands ignored until end of transaction block
```

- H2는 중복 오류 뒤에도 트랜잭션을 계속해 1, 2를 커밋한다.
- PostgreSQL은 오류가 난 순간 트랜잭션을 중단 상태로 두고, `insert (2)`를 `25P02`(in_failed_sql_transaction)로 거부한다.

### 3. 방언 차이

| 문장 | H2(PG 모드) | PostgreSQL 17 |
|---|---|---|
| `ON CONFLICT (k) DO UPDATE` | `42000` 문법 오류 | 동작, 결과 `[2]` |
| `body->>'name'` (`jsonb`) | `42000` 문법 오류 | `[kim]` |
| `code > 5` (varchar) | 암묵 변환, `[10, 9]` | `42883` operator does not exist |

- H2 문서의 PG 모드 호환 항목에는 `ON CONFLICT DO NOTHING`만 있다.

### 4. 세 층

1. 문법 방언(upsert·jsonb) — H2에서 바로 오류가 난다. 테스트를 못 쓰게 되지만 적어도 시끄럽다.
2. 설정으로 맞추는 것(NULL 정렬) — `DEFAULT_NULL_ORDERING=HIGH`를 빼면 H2는 `asc=[2, 3, 1]`(NULL 먼저), 넣으면 `[3, 1, 2]`로 PostgreSQL과 같다.
3. 트랜잭션·락 의미(오류 뒤 계속, `HYT00` vs `55P03`) — H2에서는 **초록**이 나와 문제를 숨긴다. 운영에서만 실패하므로 가장 위험하다.

### 5. Testcontainers 흐름

```text
 Docker 소켓 연결 → Ryuk 기동 → postgres:17 기동(무작위 포트 매핑) → 준비 대기
   → getJdbcUrl()로 테스트 연결 → stop() 또는 JVM 종료 → 컨테이너 제거
```

- Ryuk = resource reaper. JVM이 끝나면 Testcontainers가 만든 컨테이너를 지운다. 실험에서 Ryuk 컨테이너는 테스트가 끝나고 수 초 뒤 스스로 사라졌고, 라벨 컨테이너 수는 실행 전후 4 → 4(기존 남의 것 4개)였다.

### 6. static vs 인스턴스 필드

- static: 클래스의 테스트들이 공유. 첫 테스트 전에 한 번 켜고 마지막 테스트 뒤에 끈다.
- 인스턴스: 테스트 메서드마다 켜고 끈다(이 환경에서 기동 약 3~3.5초씩).
- 공유의 위험: 앞 테스트가 남긴 데이터가 뒤 테스트에 보인다 → 순서 의존. 트랜잭션 롤백·테이블 비우기로 격리한다. 문서는 이 확장의 병렬 실행을 지원하지 않는다고 적는다.

### 7. Spring Boot에서 H2로 도는 경우

- Spring Boot 4.1.1 문서: `@DataJpaTest`는 임베디드 DB가 클래스패스에 있으면 그것을 구성한다.
- Spring Boot 3.3까지는 `@AutoConfigureTestDatabase`의 `replace` 기본값이 `ANY`라, H2가 테스트 의존성에 있으면 컨테이너 DataSource도 H2로 교체될 수 있었다.
- 3.4부터 기본값은 `NON_TEST`다. `@ServiceConnection`·`@DynamicPropertySource`·Testcontainers JDBC URL로 준 연결은 교체하지 않는다. 그래도 컨테이너를 다른 길(직접 만든 DataSource 빈 등)로 붙이면 H2로 바뀔 수 있다.
- 확인: 테스트 로그의 JDBC URL, `select version()`.
- 차단: `@AutoConfigureTestDatabase(replace = Replace.NONE)`, `@ServiceConnection`(또는 `@DynamicPropertySource`)으로 컨테이너 연결을 쓰게 하고, H2 의존성을 뺀다.

### 8. 락 실패 코드가 다르다

- 의심: 테스트 DB가 H2였다. 실험에서 `FOR UPDATE NOWAIT` 실패는 H2 `HYT00 Timeout trying to lock table`, PostgreSQL `55P03 could not obtain lock on row`였다.
- 재시도 분기가 특정 SQLSTATE·예외 타입에 묶여 있으면 테스트와 운영이 다른 길을 탄다.
- 고침: 재시도 경로를 실제 엔진(Testcontainers)으로 테스트하고, 예외 변환 계층을 거친 타입으로 판정한다.

### 9. 25P02 고치기

- 오류를 내지 않는 문장: `INSERT ... ON CONFLICT (name) DO NOTHING` — 실험의 고친 판(TagServiceFixedTest)이 PostgreSQL에서 통과했다.
- 세이브포인트: 위험한 문장 앞에 `SAVEPOINT`를 두고, 실패하면 `ROLLBACK TO SAVEPOINT`로 되돌린다. PostgreSQL 문서 3.4는 이것이 중단된 트랜잭션 블록의 제어를 되찾는 유일한 방법이라고 적는다(전체 롤백 제외).

### 10. 무엇을 실제 엔진으로

- 실제 엔진: SQL·운영 DB 고유 기능, 마이그레이션, 트랜잭션 경계·오류 처리, 락·재시도 경로.
- 단위 테스트: 순수 도메인 계산·매핑. 여기까지 컨테이너로 돌리면 느린 테스트만 늘어난다.
- 기준 질문: "이 테스트가 틀리면 원인이 DB 엔진의 동작에 있을 수 있나?" — 그렇다면 실제 엔진으로 올린다.
