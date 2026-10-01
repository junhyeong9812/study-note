# database/10-collation-and-text-comparison — collation: 문자열을 "같다"·"작다"고 판정하는 규칙 — 정리 (힌트)

## 해결하는 문제

정수 `3 < 7`은 누구에게 물어도 같다.\
문자열 `'a' < 'B'`는 그렇지 않다. 규칙에 따라 참도 되고 거짓도 된다.

```text
  같은 두 문자열, 규칙만 다르다 (로컬 재현, PostgreSQL 17.11)

  'a' < 'B'  COLLATE "C"      → false   (바이트 값: 'B'=0x42 < 'a'=0x61)
  'a' < 'B'  COLLATE "en_US"  → true    (사전 순서: a 다음 b)
```

- *collation(콜레이션, 정렬 규칙)*: 두 문자열을 비교해 "작다·같다·크다"를 정하는 규칙이다. `ORDER BY`, `=`, `<`, `UNIQUE`, 인덱스가 모두 이 규칙을 쓴다.

쉬운 예: 전화번호부다.
- "Kim"과 "kim"을 같은 사람으로 볼지 정해야 한다.
- "é"를 "e" 옆에 둘지, 알파벳 맨 뒤에 둘지 정해야 한다.

똑같은 구조다.\
DB는 문자열 비교가 필요할 때마다 collation에게 묻는다. 그런데 이 답은 **제품·설정·라이브러리 버전**마다 다르다.

실무 예:
- 회원 가입에서 `A@x.com`이 "이미 가입된 이메일"로 거절된다. MySQL 8.4 기본 collation `utf8mb4_0900_ai_ci`는 대소문자를 무시하기 때문이다.
- 같은 스키마를 PostgreSQL로 옮기자 `a@x.com`과 `A@x.com`이 둘 다 들어간다. 기본 collation이 대소문자를 구분하기 때문이다.
- OS를 올린 뒤 PostgreSQL에서 분명 있는 행이 `WHERE name = …`로 안 찾힌다. 인덱스가 옛 정렬 규칙으로 쌓여 있다.

## 동작·원리

### 1. collation이 쓰이는 자리

```text
  문자열 비교가 필요한 곳                   → collation에게 "a ? b" 를 묻는다
  ─────────────────────────────────────────
  WHERE s = 'x', s < 'x'                   비교 연산자
  ORDER BY s, MIN(s), DISTINCT, GROUP BY   정렬·같음 판정
  UNIQUE 제약, B+Tree 인덱스                키를 정렬해 디스크에 저장 ← 규칙이 바뀌면 저장된 순서가 틀어진다
  범위 파티션 경계                          어느 파티션에 넣을지
  lower()/upper(), LIKE, 정규식 (PG)        대소문자 변환·패턴 매칭
```

- PostgreSQL 17 문서(23.2)는 `ORDER BY`, `<` 같은 비교 외에 `lower`·`upper`·`initcap`, 패턴 매칭, `to_char`도 collation을 쓴다고 적는다.
- 가장 중요한 줄은 셋째 줄이다. 인덱스는 비교 결과로 **정렬된 상태를 디스크에 저장**한다. 비교 규칙이 나중에 바뀌면 저장된 순서가 틀린 것이 된다(시나리오 3).

### 2. 다단계 비교 — UCA의 가중치

사전 순서를 정하는 국제 표준은 Unicode Collation Algorithm(UCA, UTS #10)이다.

```text
  UTS #10 표 2 — 비교 단계 (앞 단계에서 차이가 나면 뒤 단계는 보지 않는다)

  L1  기본 글자        role < roles < rule
  L2  악센트           role < rôle  < roles
  L3  대소문자·변형     role < Role  < rôle
  L4  구두점           role < "role" < Role
  Ln  동일(코드 포인트)  마지막 동점 처리
```

- 문자열마다 단계별 *가중치(weight)*를 이어 붙인 *정렬 키(sort key)*를 만든다. 정렬 키를 바이트로 비교하면 결과가 사전 순서가 된다.
  - *가중치*: 글자에 매긴 숫자. 같은 L1 가중치 = 같은 기본 글자다.
- 구두점이 L4로 가는 것은 *shifted*(변수 가중치를 L4로 미루는) 설정일 때다. *non-ignorable* 설정에서는 구두점도 L1 가중치를 가진다(UTS #10 4절 Variable Weighting). 로컬 재현에서 ICU·MySQL이 `_x`를 맨 앞에 둔 것(3절)이 이 동작과 맞는다.
- "대소문자 무시"는 **L3을 안 본다**는 뜻이다. "악센트 무시"는 **L2도 안 본다**는 뜻이다.

MySQL은 이 가중치를 직접 보여 준다(`WEIGHT_STRING`).

```text
  로컬 재현 (예시, MySQL 8.4.10)          L1        L2        L3
  'a' COLLATE utf8mb4_0900_ai_ci    →    1C47                          (L1만)
  'A' COLLATE utf8mb4_0900_ai_ci    →    1C47                          → 'a' = 'A'
  'a' COLLATE utf8mb4_0900_as_cs    →    1C47 0000 0020 0000 0002
  'A' COLLATE utf8mb4_0900_as_cs    →    1C47 0000 0020 0000 0008      L3만 다르다 → 'a' < 'A'
  'e' COLLATE utf8mb4_0900_as_cs    →    1CAA 0000 0020      0000 0002
  'é' COLLATE utf8mb4_0900_as_cs    →    1CAA 0000 0020 0024 0000 0002 0002  L2에 악센트 가중치 0024가 붙는다
```

- `0000`은 단계 사이 구분자다.
- `é`는 `e` + 악센트 두 요소로 펼쳐진다. 그래서 L2에 `0020 0024`, L3에 `0002 0002`로 가중치가 둘씩 붙는다.
- `_ai_ci`는 L1만 남긴다. 그래서 `'a' = 'A'`이고 `'resume' = 'résumé'`이다(로컬 재현 둘 다 1).

### 3. 제품마다 기본값이 다르다

```text
  같은 14개 문자열의 ORDER BY 결과 (로컬 재현)

  PG "C" / ucs_basic       1 | 10 | 9 | A | B | Z | _x | a | a b | ab | b | e | f | é
  MySQL utf8mb4_bin        1 | 10 | 9 | A | B | Z | _x | a | a b | ab | b | e | f | é
  PG "en_US" (glibc 2.41)  1 | 10 | 9 | a | A | a b | ab | b | B | e | é | f | _x | Z
  PG "en-x-icu" (ICU)      _x | 1 | 10 | 9 | a | A | a b | ab | b | B | e | é | f | Z
  MySQL 0900_as_cs         _x | 1 | 10 | 9 | a | A | a b | ab | b | B | e | é | f | Z
  MySQL 0900_ai_ci         _x | 1 | 10 | 9 | (a,A) | a b | ab | (b,B) | (e,é) | f | Z   ← 괄호 안은 같은 값
```

- 바이트 순서(`C`, `_bin`)는 대문자 전체가 소문자 전체보다 앞이고, `é`(U+00E9)는 맨 뒤다.
- glibc `en_US`는 `_x`를 `f`와 `Z` 사이에 둔다. 첫 단계에서 구두점 `_`를 무시하고 `x`로 비교하기 때문이다. ICU와 MySQL UCA는 `_x`를 맨 앞에 둔다.
- **ICU vs libc**: 같은 "영어 정렬"이어도 결과가 다르다. 제공자가 다르기 때문이다.
  - *제공자(provider)*: 정렬 규칙을 실제로 계산하는 라이브러리. PostgreSQL 17은 `libc`(OS의 glibc), `icu`(ICU 라이브러리), `builtin`(PG 내장, `C`·`pg_c_utf8`) 세 가지다.
- `ai_ci`에서 `a`와 `A`, `b`와 `B`, `e`와 `é`는 **같은 값**이다. 그래서 괄호 안의 순서는 정해지지 않는다(로컬 재현 한 번은 `a | A`, `é | e`로 나왔다).

| | PostgreSQL 17 | MySQL 8.4 InnoDB |
|---|---|---|
| 기본 collation | DB 생성 시 locale을 따른다(이 컨테이너: libc `en_US.utf8`) | `utf8mb4_0900_ai_ci`(`default_collation_for_utf8mb4`, 로컬 확인) |
| 대소문자 | 기본은 구분(표준·사전 collation 모두 deterministic) | 기본은 **무시**(`_ci`) |
| 무시 비교 만들기 | ICU로 `deterministic = false` collation 생성 | `_ci`, `_ai` 붙은 collation 선택 |
| 끝 공백 | 구분(`text`) | `0900` 계열 `NO PAD`는 구분, `_general_ci`·`_unicode_ci`·`_bin`은 `PAD SPACE`로 무시 |

### 4. deterministic vs nondeterministic (PostgreSQL)

```text
  deterministic = true (기본)                  deterministic = false
  collation이 "같다"고 해도                     collation이 "같다"면 끝
  바이트가 다르면 바이트로 동점을 깬다            'a' = 'A'  (level2 기준)
  → '=' 는 사실상 바이트 동일                    → '=' 가 대소문자·악센트를 무시할 수 있다
```

- PostgreSQL 17 문서(23.2.2.4): deterministic 플래그는 "동점을 바이트 비교로 깰지"만 정한다.
- 비결정적 collation의 대가(같은 절):
  - 성능 손해가 있다.
  - B-tree가 *중복 제거(deduplication)*를 못 쓴다.
  - 패턴 매칭 같은 일부 연산이 안 된다. 로컬 재현: `LIKE`가 `ERROR: nondeterministic collations are not supported for LIKE`로 실패했다(PostgreSQL 17.11).

```sql
-- PostgreSQL 17 — 대소문자 무시 이메일 (ICU)
CREATE COLLATION ci (provider = icu, locale = 'und-u-ks-level2', deterministic = false);
CREATE TABLE users (email text COLLATE ci UNIQUE);
INSERT INTO users VALUES ('a@x.com');
INSERT INTO users VALUES ('A@x.com');
-- ERROR:  duplicate key value violates unique constraint "users_email_key"
-- DETAIL:  Key (email)=(A@x.com) already exists.        (로컬 재현, PostgreSQL 17.11)
```

- `ks-level2`는 "L2까지 본다"는 뜻이다. 그래서 대소문자는 무시하고 악센트는 구분한다(`'resume' = 'résumé'`는 false). `ks-level1`이면 악센트도 무시한다(로컬 재현).

### 5. 유니코드 정규화 — 눈에 같은 한글도 바이트가 다르다

```text
  '한'  NFC(완성형)  U+D55C                1글자
  '한'  NFD(조합형)  U+1112 U+1161 U+11AB  3글자  (macOS 파일 이름 등에서 들어온다)
```

- 로컬 재현(PostgreSQL 17.11): 기본 collation에서 둘은 `=`가 false, 위 `ci` collation에서는 true, `normalize(…, NFC)` 뒤에는 true.
- 로컬 재현(MySQL 8.4.10): `utf8mb4_0900_ai_ci`에서 1, `utf8mb4_bin`에서 0.
- PostgreSQL 문서는 정규화 차이를 다루는 방법으로 비결정적 collation과 `normalize()` 전처리 둘을 들고, 각자 장단이 있다고 적는다(23.2.2.4). 문자 인코딩 기초는 [foundations/data-representation](../../foundations/data-representation/README.md) §3.

## 쓰이는 자료구조·알고리즘

- **정렬 키 생성(UCA 다단계 가중치)**: 문자열 → 단계별 가중치 배열 → 이어 붙인 바이트열. 비교는 이 바이트열의 사전식 비교다. "무시"는 뒤 단계를 잘라 내는 것이다. MySQL `WEIGHT_STRING()`이 그 결과를 보여 준다.
- **B+Tree의 비교 함수**: B+Tree는 "키 a < 키 b"를 판정하는 함수 하나만 믿고 키를 정렬해 둔다. 탐색은 그 순서를 전제로 가지를 고른다. collation은 텍스트 키의 비교 함수다. [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md)
  - 비교 함수가 바뀌면 트리의 불변식("왼쪽 < 분리 키 ≤ 오른쪽")이 깨진다. 트리는 에러를 내지 않고 **틀린 가지로 내려간다**.
- **인덱스와 collation의 결합**: 인덱스는 만들 때의 collation으로 정렬된다. 쿼리의 비교가 다른 collation이면 그 인덱스를 쓸 수 없다(로컬 재현: PG `WHERE name = 'abc' COLLATE "C"` → Seq Scan, MySQL `COLLATE utf8mb4_bin` → Covering index **scan**, 즉 인덱스 전체 훑기).
- **표현식 인덱스**: `lower(email)`처럼 정규화한 값을 키로 쓰면 deterministic collation 위에서 대소문자 무시 유일성을 만든다.

## 적용 — 풀어나가는 법

### 1. 먼저 "무엇을 같다고 볼지"를 컬럼마다 정한다

```text
  컬럼            같다고 볼 것                         권장
  이메일 로그인 ID  대소문자만 무시                       lower() 저장 + 표현식 UNIQUE, 또는 ci collation
  사람 이름 검색    대소문자·악센트 무시                   ci/ai collation 또는 검색 엔진
  토큰·해시·코드    바이트가 같아야 같다                   PG "C", MySQL utf8mb4_0900_bin(NO PAD) 또는 VARBINARY
                                                          (utf8mb4_bin은 PAD SPACE라 끝 공백을 무시한다)
  표시용 정렬      사용자 언어 사전 순서                   ICU 언어 collation (정렬 전용)
```

### 2. 확인 명령

```sql
-- PostgreSQL 17
SELECT datname, datlocprovider, datcollate, datcollversion FROM pg_database;   -- DB 기본 collation과 기록된 버전
SELECT collname, collprovider, collisdeterministic, collversion,
       pg_collation_actual_version(oid) FROM pg_collation WHERE collname = 'en_US';
\d users                                    -- 컬럼별 Collation 열
EXPLAIN SELECT id FROM member WHERE name = 'abc' COLLATE "C";   -- 인덱스를 쓰나

-- MySQL 8.4
SHOW CREATE TABLE users\G                   -- 테이블·컬럼 COLLATE
SELECT @@collation_server, @@collation_connection, @@default_collation_for_utf8mb4;
SELECT COLLATION_NAME, PAD_ATTRIBUTE FROM information_schema.COLLATIONS WHERE CHARACTER_SET_NAME = 'utf8mb4';
SELECT HEX(WEIGHT_STRING('A' COLLATE utf8mb4_0900_as_cs));
```

- 클라이언트 문자셋도 본다. 로컬 재현에서 `mysql` 클라이언트가 `latin1`로 접속하자 `'résumé'`가 깨진 바이트로 들어가 비교 결과가 달라졌다. `--default-character-set=utf8mb4`로 바로잡았다. MySQL Connector/J에서는 `characterEncoding`(문자셋)과 `connectionCollation`(세션 `collation_connection`) 속성이 이 값을 정한다(Connector/J 문서 Session 속성).

### 3. 대소문자 무시 유일성 — 두 제품의 방법

```sql
-- PostgreSQL 17: 방법 A — 표현식 UNIQUE (collation은 그대로)
CREATE UNIQUE INDEX users_email_lower ON users (lower(email));
SELECT * FROM users WHERE lower(email) = lower($1);   -- 조회도 같은 식으로 써야 인덱스를 탄다

-- PostgreSQL 17: 방법 B — 비결정적 ICU collation (위 동작·원리 4)

-- MySQL 8.4: 기본 utf8mb4_0900_ai_ci가 이미 대소문자·악센트 무시
-- 오히려 "구분"이 필요하면 명시한다
CREATE TABLE api_key (k varchar(64) COLLATE utf8mb4_0900_bin UNIQUE);
```

- 방법 A의 주의: 이미 `a@x.com`과 `A@x.com`이 둘 다 있으면 인덱스 생성이 `could not create unique index … is duplicated`로 실패한다(로컬 재현). 먼저 중복을 정리한다.

### 4. 커서 페이지네이션 — 정렬과 비교를 같은 곳, 같은 규칙으로

```sql
-- 동점이 생길 수 있는 키에는 반드시 유일한 보조 키를 붙인다
SELECT id, name FROM person
 WHERE (name, id) > (:last_name, :last_id)
 ORDER BY name, id
 LIMIT 20;
```

- 다음 페이지 조건(`>`)과 `ORDER BY`가 **같은 DB 안에서, 같은 collation으로** 계산되면 collation 때문에 생기는 누락·중복은 없다.
  - 별개 조건: 정렬 키에 NULL이 있으면 `(name, id) > (…)`가 NULL이 되어 그 행이 빠진다(NULL을 막거나 따로 처리). 페이지 사이에 행이 바뀌는 것도 따로 다룬다.
- 앱에서 다시 정렬하거나 커서를 앱 쪽 비교로 만들면 규칙이 달라진다. Java `String.compareTo`는 UTF-16 코드 단위 값으로 비교한다(Java SE `String` 문서). 이는 DB `C`에 가깝고 `en_US`·`ai_ci`와 다르다.

```java
// 앱에서 사람에게 보여 줄 정렬이 필요하면 Collator를 쓴다 — 단, DB 정렬과 같다는 보장은 없다
Collator c = Collator.getInstance(Locale.KOREAN);
c.setStrength(Collator.SECONDARY);   // 대소문자(L3) 차이를 무시
names.sort(c);
```

## 장애 시나리오와 대처

### 1. `_ci` collation에서 이메일이 UNIQUE 위반 (또는 반대로 중복 허용)

- **현상**: 가입이 "이미 있는 이메일"로 실패한다. 또는 DB를 옮긴 뒤 같은 사람이 두 계정을 만든다.
- **보이는 형태**
  - MySQL 8.4: `ERROR 1062 (23000): Duplicate entry 'A@x.com' for key 'users.email'`. `á@x.com`도 같은 오류였다(악센트 무시, 로컬 재현).
  - Spring `JdbcTemplate`(JDBC 예외 번역)이면 `DuplicateKeyException`(`DataIntegrityViolationException`의 하위). `sql-error-codes.xml`의 MySQL `duplicateKeyCodes`에 1062가 있다.
  - JPA/Hibernate 경로는 기본 `HibernateJpaDialect`가 Hibernate `ConstraintViolationException`을 `DataIntegrityViolationException`으로 번역한다(Spring 6.2 소스). 하위 타입까지 기대하지 말고 상위 타입으로 잡는다.
  - PostgreSQL 기본 collation: 오류 없음. `SELECT count(*)`가 2.
- **원인**: "같다"의 정의가 collation마다 다르다. MySQL 8.4 기본 `utf8mb4_0900_ai_ci`는 대소문자·악센트를 무시하고, PostgreSQL 기본은 구분한다.
- **대처**
  - 요구사항을 먼저 정한다(동작·원리 적용 1의 표).
  - PG: `lower()` 표현식 UNIQUE 또는 ICU ci collation.
  - MySQL: 구분이 필요한 컬럼은 `_0900_bin`·`_as_cs`로 명시(`utf8mb4_bin`은 끝 공백을 무시).
  - 이관 전에 `GROUP BY lower(email) HAVING count(*) > 1`로 충돌 후보를 찾는다.

### 2. 커서 페이지네이션에서 행 누락·중복

- **현상**: 목록을 끝까지 넘겼는데 몇 명이 안 보인다. 또는 두 페이지에 같은 사람이 나온다.
- **보이는 형태** (로컬 재현, MySQL 8.4.10, `ai_ci`)

```text
  행: kim(1) Kim(2) KIM(3) lee(4) Kím(5)
  1쪽: ORDER BY name LIMIT 2            → kim, Kim
  2쪽: WHERE name > 'Kim' ORDER BY name → lee          ← KIM, Kím 누락 (ai_ci에서 셋 다 'kim'과 같다)
  고침: WHERE (name,id) > ('Kim',2) ORDER BY name,id → KIM, Kím, lee
```

- **원인**
  - `ci`·`ai` collation은 서로 다른 문자열을 **같은 값**으로 본다. 유일하지 않은 정렬 키로 커서를 만들면 동점 무리가 통째로 건너뛰어진다.
  - 앱 정렬(`String.compareTo`)과 DB `ORDER BY`의 규칙이 다르면, 앱이 만든 커서가 DB의 순서와 어긋난다.
  - 정렬은 검색 엔진, 커서 비교는 DB처럼 **두 시스템**에 나뉘어도 같은 일이 난다.
- **대처**: 유일한 보조 키(`id`)를 정렬과 커서에 넣는다. 정렬·비교는 한 시스템, 한 collation에서 한다. 페이지네이션 기초는 api-design `06-pagination` — 미작성, [api-design/curriculum](../../api-design/curriculum.md).

### 3. glibc 업그레이드 뒤 PostgreSQL 인덱스가 조용히 손상

- **현상**
  - 분명 있는 행이 `WHERE name = 'x'`로 안 찾힌다.
  - UNIQUE 컬럼에 중복이 들어간다.
  - 복제본에서만 결과가 다르다.
  - 대개 오류 메시지는 없다.
- **보이는 형태**
  - PostgreSQL 15부터 DB 기본 collation 버전을 `pg_database.datcollversion`에 기록하고, 쓸 때 대조해 경고한다(15·17 카탈로그 문서, 14 문서에는 이 열이 없다). 로컬 재현(사용자 collation의 기록 버전을 일부러 바꿈):

```text
  WARNING:  collation "ci" has version mismatch
  DETAIL:  The collation in the database was created using version 0.0, but the operating system provides version 153.128.
  HINT:  Rebuild all objects affected by this collation and run ALTER COLLATION public.ci REFRESH VERSION, ...
```

  - glibc collation의 "버전"은 glibc 버전으로 대신한다. 배포판이 새 정렬 데이터를 옛 glibc에 백포트하면 경고 없이 바뀔 수 있다(ALTER COLLATION 문서 Note).
  - `amcheck`의 `bt_index_check(…)`가 순서 불일치를 오류로 보고할 수 있다(`heapallindexed => true`는 힙 행이 인덱스에 다 있는지까지 더 보는 선택 검사). 문서는 OS collation 변경과 주·복제본 OS 불일치를 원인으로 든다(F.1).
- **원인**
  - glibc 2.28(2018-08-01)은 locale 데이터를 크게 바꿨다(PostgreSQL wiki "Locale data changes").
  - 디스크의 B-tree는 옛 순서, 비교 함수는 새 순서다. 그래서 탐색이 틀린 가지로 간다.
  - 영향받는 경로: OS 메이저 업그레이드 후 같은 데이터 디렉터리, `pg_upgrade`, **locale 데이터가 다른 스트리밍 복제본**, `pg_basebackup` 복원.
  - 영향 없는 경로: `pg_dump`, 논리 복제(wiki).
  - 대상은 text·varchar·char 컬럼의 B-tree 인덱스와 텍스트 범위 파티션이다. `C`·`POSIX` 컬럼과 ICU collation 컬럼은 glibc 변경의 영향을 받지 않는다(wiki).
  - 확인 방법: `( echo "1-1"; echo "11" ) | LC_COLLATE=en_US.UTF-8 sort`의 결과가 옛·새 OS에서 다르면 바뀐 것이다. 로컬 재현(glibc 2.41)은 `1-1`, `11` 순이었다.
- **대처**
  - 업그레이드 뒤 서비스 투입 **전에** 텍스트 인덱스를 `REINDEX`하고 `ALTER DATABASE … REFRESH COLLATION VERSION`을 실행한다. REFRESH는 경고만 끈다. 재구축 여부는 검사하지 않는다(문서).
  - 주·복제본의 OS·glibc 버전을 맞춘다.
  - OS를 바꾸는 이전은 논리 복제·`pg_dump`로 한다.
  - ICU도 버전이 바뀌면 같은 일이 생긴다. ICU는 버전을 모든 플랫폼에서 제공해 경고가 더 믿을 만할 뿐이다.

### 4. collation이 달라 인덱스를 못 탄다 / 조인이 실패한다

- **현상**: 특정 쿼리만 갑자기 느리다. 또는 조인이 오류로 실패한다.
- **보이는 형태**
  - PG: `Filter: (name = 'abc'::text COLLATE "C")`와 함께 `Seq Scan`. `LIKE 'abc%'`도 non-C DB에서는 기본 인덱스를 못 탔다(로컬 재현, 10만 행).
  - MySQL: `ERROR 1267 (HY000): Illegal mix of collations (utf8mb4_0900_ai_ci,IMPLICIT) and (utf8mb4_unicode_ci,IMPLICIT) for operation '='`(로컬 재현). 명시 `COLLATE`로 맞추면 인덱스 lookup 대신 인덱스 전체 스캔이 된다.
- **원인**: 인덱스는 만들 때의 collation으로 정렬되어 있다. 다른 규칙의 비교에는 그 순서가 쓸모없다. 테이블마다 만든 시기가 달라 기본 collation이 다른 경우가 흔하다.
- **대처**
  - 조인 키 컬럼의 collation을 통일한다(`ALTER TABLE … MODIFY … COLLATE`, 재구축 필요).
  - PG 접두 `LIKE`에는 `text_pattern_ops` 인덱스를 따로 만든다. 로컬 재현에서 `Index Cond: ((name ~>=~ 'abc') AND (name ~<~ 'abd'))`로 바뀌었다.
  - 쿼리 안의 `COLLATE`는 인덱스를 버리는 비용을 치르고 쓴다.

## 핵심 문장

- collation은 문자열의 "같다·작다"를 정하는 규칙이고, `=`·`ORDER BY`·`UNIQUE`·인덱스가 모두 이것을 쓴다.
- UCA는 기본 글자 → 악센트 → 대소문자 (→ shifted 설정이면 구두점) 순의 다단계 가중치로 비교한다. "대소문자 무시"는 L3을 버린다는 뜻이다.
- MySQL 8.4 기본 `utf8mb4_0900_ai_ci`는 대소문자·악센트를 무시하고, PostgreSQL 17 기본 collation은 구분한다. 같은 UNIQUE 제약이 두 제품에서 다른 행을 거부한다.
- 비결정적(ci) collation은 서로 다른 문자열을 같게 만든다. 커서 페이지네이션에는 유일한 보조 키가 필요하다.
- B+Tree는 비교 함수를 믿고 순서를 디스크에 저장한다. glibc·ICU가 바뀌면 인덱스가 오류 없이 틀린 답을 낼 수 있으니 업그레이드·복제 때 REINDEX와 버전 일치를 챙긴다.

## 관련 주제·근거

- 선행
  - [09-index-design](../09-index-design/2-summary.md) — 인덱스 설계
  - architecture `04-character-encoding-unicode` — 원고: [foundations/data-representation](../../foundations/data-representation/README.md)
- 연결
  - api-design `06-pagination` — 커서 페이지네이션. 미작성, [api-design/curriculum](../../api-design/curriculum.md)
  - [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md) — B-tree 불변식
  - [08-btree-indexes](../08-btree-indexes/2-summary.md) · [20-backup-and-pitr](../20-backup-and-pitr/2-summary.md) — B+Tree 인덱스, 물리 백업 복원에서의 collation 문제
  - database `32-replication-leader-follower` — 복제본의 locale 불일치. 원고: [systems/server-design/03-data-layer.md](../../systems/server-design/03-data-layer.md)
- 표준·문서
  - Unicode UTS #10 Unicode Collation Algorithm(Version 18.0.0, 2026-08-31) — 1.1 Multi-Level Comparison, 표 2 비교 단계 <https://www.unicode.org/reports/tr10/>
  - PostgreSQL 17 문서 23.2 Collation Support(collation 적용 자리, `ucs_basic`·`unicode`·`pg_c_utf8`·`C`, 23.2.2.4 Nondeterministic Collations, ICU `ks-level`) <https://www.postgresql.org/docs/17/collation.html>
  - PostgreSQL 17 ALTER COLLATION(REFRESH VERSION, 버전 불일치 경고, glibc 버전을 대용으로 쓰는 한계) <https://www.postgresql.org/docs/17/sql-altercollation.html> · ALTER DATABASE … REFRESH COLLATION VERSION <https://www.postgresql.org/docs/17/sql-alterdatabase.html>
  - PostgreSQL 17 F.1 amcheck(`bt_index_check`, collation 변경·주/복제 불일치로 인한 순서 불일치) <https://www.postgresql.org/docs/17/amcheck.html>
  - PostgreSQL wiki "Locale data changes"(glibc 2.28, 영향 경로·데이터형, `sort` 테스트, 영향 인덱스 조회) <https://wiki.postgresql.org/wiki/Locale_data_changes>
  - MySQL 8.4 Reference Manual 12.3.1 Collation Naming Conventions(`_ai`·`_as`·`_ci`·`_cs`·`_bin`) <https://dev.mysql.com/doc/refman/8.4/en/charset-collation-names.html> · 12.10.1 Unicode Character Sets(UCA 9.0.0 기반 `0900`, NO PAD vs PAD SPACE) <https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-sets.html> · 12.8.5 binary collation과 `_bin` <https://dev.mysql.com/doc/refman/8.4/en/charset-binary-collations.html>
  - Java SE `String.compareTo`(UTF-16 문자 값 사전식 비교), `java.text.Collator`(strength)
  - MySQL Connector/J 문서 Configuration Properties — Session(`characterEncoding`, `connectionCollation`) <https://dev.mysql.com/doc/connector-j/en/connector-j-connp-props-session.html>
  - PostgreSQL 17 문서 51.15 `pg_database`(`datcollversion`) <https://www.postgresql.org/docs/17/catalog-pg-database.html>
  - Spring Framework `sql-error-codes.xml`(MySQL `duplicateKeyCodes` 1062), `DuplicateKeyException extends DataIntegrityViolationException`
  - Spring Framework 6.2.12 `spring-orm/.../HibernateJpaDialect.java`(Hibernate `ConstraintViolationException` → `DataIntegrityViolationException`) · UTS #10 4절 Variable Weighting(non-ignorable / shifted)
- 로컬 재현(PostgreSQL 17.11 + glibc 2.41 + ICU collator 153.128, MySQL 8.4.10): 네 collation의 `ORDER BY` 결과, `WEIGHT_STRING` 단계별 가중치, ci collation UNIQUE 위반과 `LIKE` 오류, `lower()` UNIQUE 생성 실패, NFC/NFD 한글 비교, `ai_ci` 커서 누락, collation 불일치 Seq Scan·`text_pattern_ops`, MySQL 1267·1062, collation 버전 불일치 경고
