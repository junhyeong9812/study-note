# database/10-collation-and-text-comparison — 정답

## 정답

### 1. collation의 역할과 가장 위험한 자리

- 두 문자열의 "작다·같다·크다"를 정하는 규칙이다.
- 쓰이는 자리
  - 비교 연산자(`=`, `<`)
  - `ORDER BY`·`MIN`·`DISTINCT`·`GROUP BY`
  - `UNIQUE` 제약과 B+Tree 인덱스
  - 범위 파티션 경계
  - PostgreSQL에서는 `lower`·`upper`, 패턴 매칭, `to_char`까지(PostgreSQL 17 23.2)
- 가장 위험한 자리는 **인덱스·범위 파티션**이다. 비교 결과로 정렬한 상태를 디스크에 **저장**하기 때문이다.
  - 규칙이 바뀌면 저장된 순서가 틀린 것이 된다.
  - 그러면 탐색이 틀린 가지로 가 행을 못 찾거나, 중복을 막지 못한다. 대개 오류도 없다(PostgreSQL wiki "Locale data changes").

### 2. UCA 다단계 비교

```text
  L1 기본 글자   role < roles < rule
  L2 악센트      role < rôle  < roles
  L3 대소문자    role < Role  < rôle
  L4 구두점      role < "role" < Role
  앞 단계에서 차이가 나면 뒤 단계는 보지 않는다 (UTS #10 표 2)
```

- 로컬 재현(MySQL 8.4.10)
  - `ai_ci`: `'a'` → `1C47`, `'A'` → `1C47`. L1만 남아 같다.
  - `as_cs`: `'a'` → `1C47 0000 0020 0000 0002`, `'A'` → `… 0000 0008`. L3만 다르다.
  - `'é'`는 L2에 `0024`가 더 붙는다. `ai_ci`는 L2를 버리므로 `'resume' = 'résumé'`다.
- 요약: "대소문자 무시" = L3을 버림, "악센트 무시" = L2도 버림.
- 구두점이 L4로 가는 것은 *shifted* 설정일 때다. non-ignorable 설정에서는 구두점도 L1에서 비교된다(UTS #10 4절).

### 3. 이메일 UNIQUE — 두 제품

| | MySQL 8.4 기본 | PostgreSQL 17 기본 |
|---|---|---|
| 기본 collation | `utf8mb4_0900_ai_ci` | DB locale(예: libc `en_US.utf8`), deterministic |
| 결과 | 두 번째 INSERT가 `ERROR 1062 (23000): Duplicate entry 'A@x.com' for key 'users.email'` | 둘 다 들어간다(count 2) |

- MySQL에서 구분하게 하려면: 컬럼을 `COLLATE utf8mb4_0900_as_cs`나 `utf8mb4_bin`·`utf8mb4_0900_bin`으로 둔다. 로컬 재현에서 `as_cs`는 두 행을 받았다.
- PostgreSQL에서 무시하게 하려면
  - `CREATE UNIQUE INDEX … (lower(email))`
  - 또는 ICU `und-u-ks-level2`, `deterministic = false` collation
- 로컬 재현(PostgreSQL 17.11): ci collation에서 `duplicate key value violates unique constraint "users_email_key"`.

### 4. deterministic vs nondeterministic

- deterministic(기본): collation이 같다고 해도 **바이트로 동점을 깬다**. 그래서 `=`는 바이트가 같을 때만 참이다.
- nondeterministic: collation이 같다고 하면 같다. 대소문자·악센트·정규화 형태를 무시하는 `=`를 만들 수 있다.
- PostgreSQL 17 문서(23.2.2.4)가 드는 대가
  1. 성능 손해가 있다.
  2. B-tree 중복 제거(deduplication)를 쓸 수 없다.
  3. 패턴 매칭 등 일부 연산을 못 쓴다. 로컬 재현: `ERROR: nondeterministic collations are not supported for LIKE`.
- 표준·미리 정의된 collation은 모두 deterministic이다. 비결정적 collation은 ICU로 직접 만들어야 한다.

### 5. 제공자별 정렬 결과

```text
  PG "C" / MySQL utf8mb4_bin  1 | 10 | 9 | A | B | Z | _x | a | a b | ab | b | e | f | é
  PG "en_US" (glibc 2.41)     1 | 10 | 9 | a | A | a b | ab | b | B | e | é | f | _x | Z
  PG "en-x-icu"               _x | 1 | 10 | 9 | a | A | a b | ab | b | B | e | é | f | Z
```

- 바이트 순서에서 `_x`(0x5F)는 대문자와 소문자 사이, `é`(U+00E9)는 맨 뒤다.
- glibc `en_US`에서 `_x`는 `f`와 `Z` 사이다. 첫 단계에서 `_`를 무시하고 `x`로 비교한다.
- ICU는 `_x`를 맨 앞에 둔다. 두 사전 순서 모두 `é`는 `e` 바로 뒤다.
- 교훈: "영어 사전 순서"라는 같은 이름이어도 **제공자(libc/ICU)마다 결과가 다르다**. 주 서버와 복제본, 앱과 DB가 다른 제공자·버전을 쓰면 순서가 어긋난다.

### 6. 커서 페이지네이션 누락

- 로컬 재현(MySQL 8.4.10, `ai_ci`)

```text
  행: kim(1) Kim(2) KIM(3) lee(4) Kím(5)
  1쪽 ORDER BY name LIMIT 2           → kim, Kim
  2쪽 WHERE name > 'Kim'               → lee          (KIM, Kím 누락)
```

- 원인: `ai_ci`에서 `kim = Kim = KIM = Kím`이다. 정렬 키가 유일하지 않다. 그래서 `>`가 동점 무리 전체를 건너뛴다.
- 고친 쿼리

```sql
SELECT id, name FROM person
 WHERE (name, id) > (:last_name, :last_id)
 ORDER BY name, id LIMIT 20;       -- 재현: KIM, Kím, lee
```

- Java `String.compareTo`는 UTF-16 코드 단위 값으로 비교한다. 그래서 `'Z' < 'a'`, `'é'`는 맨 뒤다. DB `ai_ci`·`en_US` 순서와 다르다. 앱이 만든 커서나 앱 쪽 재정렬로 페이지를 이어 붙이면 누락·중복이 생긴다. 정렬과 커서 비교를 **같은 시스템, 같은 collation**에서 한다.

### 7. OS 업그레이드 뒤 조용한 인덱스 손상

- 원인
  - glibc locale 데이터가 바뀌었다(대표적으로 glibc 2.28, 2018-08-01).
  - 디스크의 B-tree는 옛 순서, 새 비교 함수는 새 순서다. 그래서 탐색이 행을 놓치고, UNIQUE 검사도 중복을 못 본다.
- 영향받는 경로
  - 같은 데이터 디렉터리로 OS 메이저 업그레이드
  - `pg_upgrade`
  - locale 데이터가 다른 스트리밍 복제본(복제본이 손상, 주 서버는 정상)
  - `pg_basebackup` 복원
- 받지 않는 경로: `pg_dump`, 논리 복제.
- 대상
  - 영향: text·varchar·char B-tree 인덱스, 텍스트 범위 파티션.
  - 무관: `C`·`POSIX` 컬럼, ICU collation 컬럼(glibc 변경과 무관)(PostgreSQL wiki).
- 확인 방법
  - PostgreSQL 15부터는 `datcollversion` 불일치 경고(`collation "…" has version mismatch`)가 나온다. 다만 glibc 버전을 대신 쓰므로, 백포트된 변경은 놓칠 수 있다.
  - `amcheck`의 `bt_index_check(idx)`로 순서 불변식을 검사한다(`heapallindexed => true`는 힙 행 누락까지 보는 선택 검사).
  - `( echo "1-1"; echo "11" ) | LC_COLLATE=en_US.UTF-8 sort`를 옛·새 OS에서 비교한다.
- 대처
  - 투입 전에 텍스트 인덱스를 `REINDEX`한 뒤 `ALTER DATABASE … REFRESH COLLATION VERSION`을 실행한다. REFRESH는 경고만 끈다.
  - 주·복제본의 OS를 맞춘다.
  - OS 교체는 논리 복제로 옮긴다.

### 8. B+Tree 불변식과 collation

- B+Tree는 비교 함수 하나로 "왼쪽 < 분리 키 ≤ 오른쪽"을 유지한다. 텍스트 키의 비교 함수가 collation이다. 인덱스는 **만들 때의 collation으로** 정렬되어 있다.
- 다른 collation의 비교에는 그 순서를 쓸 수 없다.
  - PG `WHERE name = 'abc' COLLATE "C"` → `Seq Scan`, `Filter: (name = 'abc'::text COLLATE "C")`(로컬 재현, 10만 행).
  - non-C DB의 `LIKE 'abc%'`도 기본 인덱스를 못 탔다. `text_pattern_ops` 인덱스를 따로 만들자 Index Scan으로 바뀌었다.
- MySQL에서 collation이 다른 두 컬럼을 `=`로 조인하면 `ERROR 1267 (HY000): Illegal mix of collations (utf8mb4_0900_ai_ci,IMPLICIT) and (utf8mb4_unicode_ci,IMPLICIT) for operation '='`가 나온다. `COLLATE`로 맞추면 실행은 되지만, 인덱스 lookup 대신 인덱스 전체 스캔이 되었다(로컬 재현).

### 9. 컬럼별 비교 규칙

| 컬럼 | 규칙 |
|---|---|
| 이메일 | 대소문자만 무시(악센트는 요구에 따라) |
| 이름 검색 | 대소문자·악센트 무시 collation 또는 검색 엔진 |
| API 토큰 | 바이트 비교(PG `"C"`, MySQL `utf8mb4_0900_bin` 또는 `VARBINARY`. `utf8mb4_bin`은 `PAD SPACE`라 끝 공백을 무시한다) |
| 표시 정렬 | 사용자 언어 ICU collation. 유일성에는 쓰지 않는다 |

- PostgreSQL의 두 방법
  - A. `CREATE UNIQUE INDEX … (lower(email))`
    - 조회도 `lower(email) = lower($1)`로 써야 인덱스를 탄다.
    - 기존 중복이 있으면 생성이 `could not create unique index … is duplicated`로 실패한다(로컬 재현).
    - `lower`도 collation을 따르므로 비ASCII 대소문자 처리는 collation에 의존한다.
  - B. ICU 비결정적 collation
    - `=`가 자연스럽게 대소문자를 무시한다.
    - 대가: LIKE 불가, 성능 손해, dedup 불가(4번).

### 10. NFC와 NFD 한글

- 같은 `'한'`이 완성형 U+D55C(NFC, 1글자)일 수도 있고, 조합형 U+1112 U+1161 U+11AB(NFD, 3글자)일 수도 있다. 바이트가 다르다.
- 로컬 재현

| 비교 | 결과 |
|---|---|
| PostgreSQL 17 기본(deterministic) `=` | false |
| PostgreSQL ICU `ks-level2` 비결정적 | true |
| PostgreSQL `normalize(nfd, NFC) = nfc` | true |
| MySQL 8.4 `utf8mb4_0900_ai_ci` | 1 |
| MySQL 8.4 `utf8mb4_bin` | 0 |

- 대처: 입력 경계에서 NFC로 정규화해 저장한다. 또는 비결정적 collation을 쓴다. PostgreSQL 문서는 두 방법에 각각 장단이 있다고 적는다(23.2.2.4).
