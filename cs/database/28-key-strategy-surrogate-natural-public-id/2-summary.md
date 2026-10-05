# database/28-key-strategy-surrogate-natural-public-id — 키 전략: 대리키·자연키, bigint·UUID, 내부 PK와 외부 ID — 정리 (힌트)

## 해결하는 문제

모든 행에는 "이 행"을 가리키는 이름(키)이 필요하다.\
그 이름은 FK로 다른 테이블에 복사되고, URL과 API 응답으로 밖에 나가고, 인덱스의 정렬 기준이 된다.\
그래서 키 하나를 고르는 일이 네 가지 질문에 동시에 답하는 일이 된다.

```text
  ① 바뀌나?           값이 바뀌면 그 값을 복사해 간 모든 FK를 고쳐야 한다
  ② 밖에서 보이나?     보이면 추측·열거·규모 추정의 재료가 된다
  ③ 어떤 순서로 생기나? B+Tree는 정렬 구조라 삽입 순서가 페이지 분할·캐시 효율을 정한다
  ④ 어떤 타입으로 나가나? 64비트 정수는 JSON·JavaScript에서 끝자리가 바뀔 수 있다
```

쉬운 예: 학생을 이름으로 부르는 학교다.
- 개명하면 출석부·성적표·도서 대출 기록을 전부 고쳐야 한다(①).
- 학번이 입학 순서라면 "올해 몇 명 들어왔나"를 학번만 보고 안다(②).

똑같은 구조다.\
그래서 실무의 기본형은 **안에서는 바뀌지 않는 짧은 대리키, 밖으로는 별도의 공개 ID**다.

실무 예:
- 회원 PK를 이메일로 했다가 이메일 변경 기능이 생기자 주문·포인트·쿠폰 테이블의 FK를 연쇄 수정한다.
- `/orders/10231` 다음 번호를 넣어 보니 남의 주문이 열린다.
- PK를 UUIDv4로 바꾼 뒤 같은 데이터인데 인덱스가 두 배 가까이 커졌다.
- 프런트에서 주문 ID `1234567890123456789`가 `1234567890123456800`으로 바뀌어 조회가 404다.

## 동작·원리

### 1. 자연키 vs 대리키

```text
  자연키 PK                                  대리키 PK
  users(email PK)                            users(id PK, email UNIQUE)
     ▲        ▲                                 ▲        ▲
  orders.user_email  points.user_email        orders.user_id  points.user_id
  email 변경 → 참조하는 모든 행 UPDATE         email 변경 → users 한 행만 UPDATE
```

  - *자연키*: 업무 세계에 이미 있는 값(이메일, 주민번호, 사업자번호, 상품 코드).
  - *대리키*: 식별만을 위해 DB가 만든, 뜻 없는 값(bigint 시퀀스, UUID).

- 자연키가 "절대 안 바뀐다"는 가정은 자주 깨진다. RFC 9562 §6.13도 우편번호·면허 번호처럼 "고유하고 불변해 보이던 값이 나중에 바뀌는" 사례를 들며, 이름 기반 UUID를 PK로 쓰지 말고 시간 기반 UUID 대리키를 쓰라고 권한다.
- 주민번호 같은 민감 정보를 PK로 쓰면 모든 FK 테이블·로그·인덱스로 복제된다.
- 자연키를 버리라는 뜻은 아니다. 업무 규칙상 유일해야 하면 **UNIQUE 제약**으로 둔다. PK와 유일성 규칙을 분리하는 것이다.

### 2. 내부 PK와 외부 ID를 나눈다

```text
  DB 안                                         API 밖
  orders.id          bigint  1024     ─╳─▶     (절대 안 나감)
  orders.public_id   text    ord_7Kp2Xq...  ─▶  GET /orders/ord_7Kp2Xq...
       │
       └ FK·조인·클러스터링은 id로, 외부 조회는 public_id UNIQUE 인덱스로
```

- 내부 PK: 짧고(8바이트), 증가 순서라 인덱스에 유리하다. 밖으로 안 내보내니 순서가 드러나도 된다.
- 외부 ID: 추측이 어렵고, 타입을 알 수 있게 **접두어**를 붙일 수 있다(예: Stripe `cus_`, `pi_`, `ch_`).
  - Stripe 블로그(2022-08-30, "Designing APIs for humans: Object IDs"): 접두어로 객체 종류를 사람이 바로 알고, 잘못된 종류의 ID를 넘긴 실수를 눈으로 잡는다. 2012년부터 써 왔다고 적는다.
- 추측이 어렵다고 **권한 검사를 생략하지 않는다.** RFC 9562 §8: UUID가 추측하기 어렵다고 가정하면 안 되며(SHOULD NOT), 보유만으로 접근을 주는 보안 수단으로 쓰면 안 된다(MUST NOT).

### 3. 삽입 순서와 B+Tree — 순차 키 vs 랜덤 키

```text
  순차 키(bigint 시퀀스, UUIDv7)            랜덤 키(UUIDv4)
  [1..90][91..180][181..270][271.. ▶        [ab..][03..][f1..][5c..]
                              새 키는 항상     새 키가 아무 페이지에나 떨어짐
                              오른쪽 끝          → 가득 찬 중간 페이지를 반으로 분할
  → 오른쪽 끝 페이지만 뜨겁다(버퍼 풀에 상주)    → 모든 리프가 번갈아 필요(버퍼 풀 경쟁)
  → 페이지를 꽉 채우고 다음 페이지로            → 분할 후 반쯤 빈 페이지가 남는다
```

로컬 재현(예시, PostgreSQL 17.11, 20만 행 삽입 후 `pgstatindex`):

| PK | 인덱스 크기 | 리프 페이지 | 평균 리프 채움 | 리프 단편화 |
|---|---|---|---|---|
| bigint identity | 4408 kB | 547 | 90% | 0 |
| UUIDv4 (`gen_random_uuid()`) | 8456 kB | 1049 | 65.9% | 50.2 |
| UUIDv7 (SQL로 생성, 밀리초 미만 비트 포함) | 6184 kB | 767 | 90.0% | 0 |

- bigint와 v7의 90%는 B-tree 기본 fillfactor 90과 일치한다. 문서: 오른쪽 끝에 새 최대 키를 붙일 때 이 비율로 채운다.
- v4는 무작위 위치 분할 때문에 페이지가 약 2/3만 찼다. v7은 순차라 v4보다 작다. 다만 키가 16바이트라 bigint보다는 크다.
- PostgreSQL 17에는 `uuidv7()` 함수가 없다(로컬에서 `function uuidv7() does not exist`). 재현은 RFC 9562 배치대로 SQL 함수로 만들었다.
- 주의(재현 조건): 처음에는 밀리초 안에서 랜덤 비트만 쓴 v7을 만들었다. 한 번의 `INSERT`가 1ms에 수백 행을 넣으니 밀리초 안 순서가 섞여 단편화가 45%까지 났다. RFC 9562 §6.2의 밀리초 미만 비트(rand_a 12비트)를 채운 판으로 바꾸자 위 표처럼 0이 됐다.

MySQL 8.4 InnoDB는 **PK가 곧 테이블(클러스터드 인덱스)**이라 영향이 더 크다.

| PK(20만 행, 로컬 재현 MySQL 8.4.10) | `data_length` | 16KB 페이지 |
|---|---|---|
| `bigint AUTO_INCREMENT` | 6.8 MB | 417 |
| `BINARY(16)` 랜덤(`RANDOM_BYTES(16)`) | 14.2 MB | 867 |
| `BINARY(16)` `UUID_TO_BIN(UUID(), 1)` | 8.9 MB | 545 |

- 문서(17.6.2.2): 순차 삽입이면 페이지가 약 15/16 차고, 랜덤 삽입이면 1/2~15/16 찬다.
- 문서(17.6.2.1): 보조 인덱스의 모든 레코드는 PK 값을 함께 담는다. PK가 길면 **모든 보조 인덱스가 커진다.**
- MySQL `UUID()`는 버전 1(시간 기반)이다. `UUID_TO_BIN(u, 1)`은 시간 부분의 앞뒤를 바꿔 앞쪽 바이트가 천천히 변하게 한다(문서 14.23 swap_flag).

### 4. UUIDv4와 v7의 비트 배치 (RFC 9562)

```text
  v4:  [ 랜덤 48 ][ver 4][ 랜덤 12 ][var 2][ 랜덤 62 ]           랜덤 122비트
  v7:  [ unix_ts_ms 48 ][ver 4][ rand_a 12 ][var 2][ rand_b 62 ]   앞 48비트 = 밀리초 시각
        └ 앞에서부터 바이트 비교하면 밀리초 단위로 시간순
```

- v7은 바이트 순 정렬이 곧 밀리초 시각 순이다(§6.11). 인덱스 지역성이 좋다.
  - 같은 밀리초 안의 순서까지 생성 순서와 맞추려면 §6.2의 단조 증가 방식(rand_a를 카운터·밀리초 미만 비트로 채움)을 써야 한다. 랜덤만 채우면 같은 밀리초 안에서는 섞인다(위 재현의 45% 단편화).
- 대가: 앞 48비트에서 **생성 시각이 드러난다.** §8은 이를 "매우 작은 공격 표면"이라 부르고, 보안 목적이 조금이라도 있으면 v4를 쓰라고(SHOULD) 권한다.
- 저장은 문자열(36자, 288비트)이 아니라 128비트 이진이 권장이다(§6.13 SHOULD). PG `uuid` 타입, MySQL `BINARY(16)`.

### 5. 64비트 ID와 JavaScript 숫자

```text
  JavaScript Number = IEEE 754 배정밀도 → 정확한 정수는 2^53 − 1 = 9007199254740991 까지
  (예시, Node 18.19) JSON.parse('{"id":9007199254740993}').id   → 9007199254740992   ✘ 끝자리 변형
                     JSON.parse('{"id":"9007199254740993"}').id → "9007199254740993" ✔ 문자열
                     JSON.stringify({id: 1n})                    → TypeError: Do not know how to serialize a BigInt
```

- bigint 시퀀스는 처음엔 작아서 문제가 안 보인다. 스노플레이크류 ID(시간 비트가 앞에 오는 64비트)는 처음부터 2^53을 넘는다.
- 대처: 64비트 ID는 **JSON 문자열**로 내보낸다. 외부 ID를 처음부터 문자열(접두어 ID)로 두면 이 문제가 생기지 않는다.

### 6. 시퀀스는 빈틈을 만든다

```text
  (예시, PostgreSQL 17.11)  INSERT → id 1 / BEGIN; INSERT → id 2; ROLLBACK / INSERT → id 3
  결과: 1, 3   — 롤백된 번호는 재사용되지 않는다
```

- 대리키 시퀀스는 "연속"을 보장하지 않는다.
- 시퀀스는 보통 겹치지 않는 값을 내지만, 재설정하거나 값을 수동으로 넣으면 겹칠 수 있다. 테이블 안 유일성은 **PK·UNIQUE 제약**이 보장한다(PG 17 문서 5.3 Identity Columns). 송장 번호처럼 빈틈이 없어야 하는 업무 번호는 별도로 설계한다.

## 쓰이는 자료구조·알고리즘

- **B+Tree 삽입 지역성**: 오른쪽 끝 삽입은 한 페이지만 뜨겁고 분할이 꽉 찬 페이지 뒤에서 일어난다. 랜덤 삽입은 중간 분할로 반쯤 빈 페이지를 남긴다. [08-btree-indexes](../08-btree-indexes/2-summary.md), [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md).
- **버퍼 풀**: 랜덤 키는 삽입마다 다른 리프가 필요해 버퍼 풀 적중률이 떨어진다. [07-buffer-pool](../07-buffer-pool/2-summary.md).
- **비트 필드(시간 + 랜덤/카운터)**: UUIDv7, 스노플레이크 ID는 상위 비트에 시각을 둬 정렬 가능하게 하고 하위 비트로 유일성을 채운다. [ops-patterns/13-snowflake](../../ops-patterns/13-snowflake/2-summary.md).
- **접두어 + 인코딩**: 외부 ID는 `타입 접두어 + 랜덤 바이트의 base62/base32 인코딩` 형태가 흔하다. 접두어로 라우팅(어느 테이블을 볼지)도 할 수 있다(Stripe 블로그).

## 적용 — 풀어나가는 법

**1) 기본형 스키마**

```sql
-- PostgreSQL 17
CREATE TABLE customer (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,   -- 내부 PK
  public_id  text   NOT NULL UNIQUE,                            -- 외부 ID, 예: cus_...
  email      text   NOT NULL UNIQUE                             -- 자연키는 UNIQUE로
);

-- MySQL 8.4
CREATE TABLE customer (
  id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  public_id  VARCHAR(32)  NOT NULL UNIQUE,
  email      VARCHAR(255) NOT NULL UNIQUE
);
```

**2) 외부 ID 생성 (Java)**

```java
private static final SecureRandom RND = new SecureRandom();
private static final char[] B62 =
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz".toCharArray();

static String publicId(String prefix) {          // 예: publicId("cus")
    StringBuilder sb = new StringBuilder(prefix).append('_');
    for (int i = 0; i < 22; i++) sb.append(B62[RND.nextInt(62)]);   // 약 131비트
    return sb.toString();
}
```

**3) UUID를 PK로 써야 한다면** (분산 생성·오프라인 생성 등)
- v7(시간순)을 쓰고, 이진으로 저장한다. PostgreSQL 17은 앱에서 생성하거나 함수를 둔다. MySQL은 `BINARY(16)`.
- 외부에 v7을 노출하면 생성 시각이 드러난다는 점을 받아들일 수 있는지 판단한다.

**4) 64비트 ID를 JSON으로 내보낼 때 (Java·TS)**

```java
// Jackson: long 필드를 문자열로 직렬화
@JsonSerialize(using = ToStringSerializer.class)
private long id;
```

```ts
// TS 쪽은 ID를 string 타입으로 받는다 — 숫자로 파싱하지 않는다
type Order = { id: string; amount: number };
```

**5) 진단**

```sql
-- PostgreSQL: PK 인덱스 채움·단편화
CREATE EXTENSION IF NOT EXISTS pgstattuple;
SELECT * FROM pgstatindex('orders_pkey');   -- avg_leaf_density, leaf_fragmentation
-- MySQL: 테이블·인덱스 크기
SELECT table_name, data_length, index_length FROM information_schema.tables
WHERE table_schema = DATABASE();
```

## 장애 시나리오와 대처

**① 자연키가 바뀌어 FK 연쇄 수정 (커리큘럼 ⚠)**
- 현상: 이메일 변경 기능 배포 후 변경 요청 한 건에 수 초가 걸리고, 가끔 교착이 난다.
- 보이는 형태: `ON UPDATE CASCADE`가 여러 테이블의 행을 잠근다. PG `40P01 deadlock detected`, MySQL `ERROR 1213`. CASCADE 없이 기본 동작(`NO ACTION`/`RESTRICT`)이면, 참조하는 행이 있을 때 FK 위반(PG 23503, MySQL 1451/1452)으로 실패한다.
- 원인: 바뀔 수 있는 값이 PK였고, FK로 여러 테이블에 복제돼 있었다.
- 대처: 대리키 컬럼을 추가하고 FK를 대리키로 옮긴다(26번 expand/contract). 자연키는 UNIQUE 제약으로 남긴다.

**② 순차 PK 노출 → 열거·규모 노출 (커리큘럼 ⚠)**
- 현상: 누군가 `/orders/{id}`를 1씩 올리며 조회한다. 또는 경쟁사가 월초·월말 주문 번호 차이로 월 주문량을 추정한다.
- 보이는 형태: 접근 로그에 연속 ID 요청이 몰린다. 권한 검사가 빠진 엔드포인트면 404가 아니라 200이 섞인다.
- 원인: 내부 순서가 그대로 외부 식별자였다. 권한 검사가 ID의 "추측 어려움"에 기대고 있었다면 더 심각하다.
- 대처: 1순위는 **객체 단위 권한 검사**다. 그다음 외부 ID를 랜덤 공개 ID로 분리한다. RFC 9562 §8대로 UUID도 권한 수단이 아니다.

**③ UUIDv4 PK → 페이지 분할·버퍼 풀 적중률 하락 (커리큘럼 ⚠)**
- 현상: 테이블이 커질수록 삽입 지연과 디스크 읽기가 늘어난다. 같은 행 수에서 인덱스가 bigint의 약 2배다(재현 표 — 키 크기 8→16바이트 몫 포함).
- 보이는 형태: PG `pgstatindex`의 `avg_leaf_density` 약 66%, `leaf_fragmentation` 약 50%(재현 표). MySQL `data_length`가 순차 키의 2배 가까이(재현 417 → 867페이지, 키 크기 몫 포함. 같은 랜덤 키를 재구성 전후로 비교한 무작위 삽입 몫만은 약 1.4배 — [08번](../08-btree-indexes/2-summary.md)). 버퍼 풀 적중률 하락, 쓰기 I/O 증가.
- 원인: 랜덤 키는 삽입 위치가 무작위라 중간 분할이 잦고, 모든 리프가 번갈아 메모리에 있어야 한다. InnoDB는 PK가 클러스터드라 테이블 자체와 모든 보조 인덱스가 영향을 받는다.
- 대처: 내부 PK는 bigint 시퀀스로, 외부 ID는 따로. UUID가 꼭 필요하면 v7(시간순) + 이진 저장. 이미 v4인 대형 테이블은 PK 교체가 큰 마이그레이션이므로 26번 절차로 한다.

**④ 64비트 ID를 JSON 숫자로 → 끝자리 변형 (커리큘럼 ⚠)**
- 현상: 웹에서 상세 조회가 404다. 모바일 앱과 서버 로그로는 정상이다.
- 보이는 형태: 서버가 보낸 `1234567890123456789`가 브라우저에서 `1234567890123456800`이 된다(재현: Node 18.19 `JSON.parse`).
- 원인: JavaScript Number는 2^53 − 1까지만 정수를 정확히 담는다.
- 대처: ID는 JSON 문자열로 내보낸다(Jackson `ToStringSerializer`, 응답 스키마에서 `string`). 이미 숫자로 나간 API는 문자열 필드를 추가하고 클라이언트를 옮긴 뒤 숫자 필드를 폐기한다(API 버전 관리).

## 핵심 문장

- 바뀔 수 있는 값은 PK로 쓰지 않는다. 업무상 유일성은 UNIQUE 제약으로 지킨다.
- 안에서는 짧고 순차적인 대리키로 조인·클러스터링하고, 밖으로는 별도의 공개 ID를 내보낸다.
- B+Tree에는 삽입 순서가 중요하다. 랜덤 키(UUIDv4)는 중간 분할로 페이지를 반쯤 비우고 버퍼 풀을 넓게 쓴다. 재현에서 인덱스가 bigint의 약 2배였다(키 크기 차이 포함. 무작위 삽입 몫만은 약 1.4배 — 08번).
- UUIDv7은 앞 48비트가 밀리초 시각이라 정렬이 곧 밀리초 단위 시간순이다(같은 밀리초 안은 단조 생성 방식일 때만). 대신 생성 시각이 드러난다.
- 추측하기 어려운 ID도 권한 검사를 대신하지 못한다.
- 64비트 ID는 JSON 문자열로 내보낸다. JavaScript 정수는 2^53 − 1까지만 정확하다.

## 관련 주제·근거

- 선행
  - [08-btree-indexes](../08-btree-indexes/2-summary.md) — B+Tree 분할, 클러스터드 vs 보조
  - `security/16-identifiers-and-enumeration` — 미작성, [security/README](../../security/README.md)
  - [distributed/13-distributed-id-generation](../../distributed/13-distributed-id-generation/2-summary.md)
- 연결
  - [02-keys-and-constraints](../02-keys-and-constraints/2-summary.md) — PK·FK·UNIQUE
  - [07-buffer-pool](../07-buffer-pool/2-summary.md) — 적중률
  - [26-schema-migration](../26-schema-migration/2-summary.md) — PK 교체 마이그레이션
  - [51-object-relational-structural-mapping](../51-object-relational-structural-mapping/2-summary.md) — Identity Field
  - [ops-patterns/13-snowflake](../../ops-patterns/13-snowflake/2-summary.md) — 64비트 시간순 ID
  - [api-design/08-schema-and-serialization](../../api-design/08-schema-and-serialization/2-summary.md)
- 표준·문서
  - RFC 9562 "Universally Unique IDentifiers (UUIDs)" — §2.1(v4의 인덱스 지역성 문제), §5.4 v4, §5.7 v7 비트 배치, §6.2 단조성, §6.11 정렬, §6.13 DBMS 고려(이진 저장, 이름 기반 UUID PK 비권장), §8 보안 <https://www.rfc-editor.org/rfc/rfc9562>
  - PostgreSQL 17 5.3 Identity Columns(identity 열은 유일성을 보장하지 않음 — PK·UNIQUE로) <https://www.postgresql.org/docs/17/ddl-identity-columns.html>
  - PostgreSQL 17 CREATE INDEX — B-tree fillfactor 기본 90 <https://www.postgresql.org/docs/17/sql-createindex.html> · F.31 pgstattuple(`pgstatindex`) <https://www.postgresql.org/docs/17/pgstattuple.html>
  - MySQL 8.4 Reference Manual 17.6.2.1 Clustered and Secondary Indexes <https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html> · 17.6.2.2 The Physical Structure of an InnoDB Index(15/16, 1/2~15/16) <https://dev.mysql.com/doc/refman/8.4/en/innodb-physical-structure.html> · 14.23 Miscellaneous Functions(`UUID()` 버전 1, `UUID_TO_BIN` swap_flag) <https://dev.mysql.com/doc/refman/8.4/en/miscellaneous-functions.html>
  - Paul Asjes, "Designing APIs for humans: Object IDs", Stripe, dev.to 2022-08-30 <https://dev.to/stripe/designing-apis-for-humans-object-ids-3o5a>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10, Node 18.19): 20만 행 PK별 인덱스 크기·채움·단편화(`pgstatindex`), InnoDB `data_length`, `uuidv7()` 부재, 시퀀스 롤백 빈틈, `JSON.parse` 정밀도·BigInt 직렬화 에러
