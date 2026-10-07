# security/18-injection — SQL·명령·LDAP 인젝션과 파라미터 바인딩 — 정리 (힌트)

## 해결하는 문제

애플리케이션은 사용자 입력을 받아 **다른 해석기**(DB, 셸, LDAP 서버)에 넘긴다.
입력을 명령 문자열에 이어 붙이면, 해석기는 어디까지가 코드이고 어디부터가 데이터인지 모른다.

```text
  개발자가 의도한 것                       해석기가 실제로 본 것
  SELECT ... WHERE name = '[데이터]'       SELECT ... WHERE name = 'nobody' OR '1'='1'
                          └ 이름 한 개                              └ 데이터 ┘└── 코드(조건 추가) ──┘
```

- *인젝션(injection)*: 데이터로 넘긴 입력이 해석기에서 코드(문법 요소)로 해석되는 결함.
  - 흔한 오해: "특수 문자를 지우면 된다." OWASP는 입력 검증을 "완전한 방어가 아니다"라고 적는다. 정상 데이터에도 따옴표가 있다(`o'brien`).
- 분류: OWASP Top 10 2021의 A03 Injection(SQL·NoSQL·OS 명령·ORM·LDAP·EL/OGNL, XSS인 CWE-79 포함). Top 10 2025에서는 A05 Injection이다.
- 결과: 데이터 유출(조건이 무력화되어 전 행 반환), 데이터 변조, 셸 경유 실행이면 서버에서 임의 명령 실행.

쉬운 예: 은행 창구 신청서에 "금액: 1만 원. 그리고 창구 직원은 금고를 열 것"이라고 쓴다.
- 직원이 신청서 칸 안의 글을 **지시**로 읽으면 사고다.
- 칸 안의 글은 언제나 "금액 칸의 값"으로만 읽는 것이 해법이다.

실무 예:
- 검색 API가 `"... WHERE name = '" + q + "'"`로 쿼리를 만든다. 이름에 따옴표가 든 고객은 `500`을 받고, 공격자는 전 행을 받는다.
- 썸네일 서버가 `sh -c "convert " + fileName`을 호출한다. 파일 이름의 `;`가 명령 구분자가 된다.

## 동작·원리

### 1. 문맥이 섞이는 지점 — 해석기의 파서

```text
  [사용자 입력] ──▶ [앱: 문자열 연결] ──▶ "SELECT ... '"+q+"'" ──▶ [DB 파서] ──▶ 실행 계획
                                                   ▲
                                       여기서 데이터와 코드가 한 문자열로 섞인다

  [사용자 입력] ──▶ [앱: 바인딩] ──▶ 쿼리 틀 "SELECT ... = $1"  ──▶ [DB 파서] ──▶ 문법 트리(틀만 파싱)
                                    값 $1 = '...'(별도 필드)   ──▶ Bind ──▶ 계획(보통 이때)·값으로만 대입
```

- 해석기는 문자열을 토큰으로 자르고 문법 트리를 만든다(파싱, [language/03-parsing-grammars-ast](../../language/03-parsing-grammars-ast/2-summary.md)).
  - *토큰(token)*: 파서가 자른 최소 단위. 따옴표는 "문자열 리터럴 끝"이라는 토큰 경계다.
- 문자열 연결은 입력을 **파싱 전에** 섞는다. 입력의 따옴표가 리터럴을 닫고, 뒤따르는 글자가 새 문법 요소가 된다.
- 바인딩은 쿼리 틀만 파싱하고, 값은 **파싱이 끝난 뒤** 자리표시자(`?`, `$1`)에 들어간다. 값이 무엇이든 문법 트리는 바뀌지 않는다.
  - PostgreSQL 17 문서 53.2.3: 실행 계획은 보통 `Bind`를 처리할 때 만든다(값을 보고 계획할 수 있다). 문법 구조는 그 전에 `Parse`에서 확정된다.

### 2. 실제로 서버가 받은 것 — PostgreSQL 로그로 확인

(실험, PostgreSQL 17.11 + pgjdbc 42.7.7 + OpenJDK 21.0.12, 로컬 내부망 일회용 컨테이너, `log_statement=all`, 2026-10-07)

```text
LOG:  execute <unnamed>: SELECT id, name, note FROM member WHERE name = 'nobody' OR '1'='1'
LOG:  execute <unnamed>: SELECT id, name, note FROM member WHERE name = $1
DETAIL:  Parameters: $1 = 'nobody'' OR ''1''=''1'
```

- 첫 줄: 연결한 쿼리. 서버 파서는 `OR '1'='1'`을 조건으로 읽었다.
- 둘째 줄: `PreparedStatement`. 쿼리 틀(`$1`)과 값이 따로 왔다. 로그의 `''`는 로그가 값을 보여 주려고 붙인 표기다.
- 같은 입력의 결과: 연결은 3행 전부, 바인딩은 0행(그런 이름 없음).

### 3. 셸 인젝션 — 셸이라는 해석기를 끼우면 생긴다

```text
  sh -c "ls /tmp/files/" + input        input = "report.txt; echo INJECTED-$(whoami)"
        └ 셸 파서: ;  $( )  |  &  > 를 문법으로 해석 → 명령 2개 실행

  ProcessBuilder("ls", "/tmp/files/" + input)
        └ 셸 없음. execve에 인자 배열로 전달 → 파일 이름 1개("report.txt; echo ...")
```

- *셸 메타문자*: `;`·`|`·`&`·`$( )`·`` ` ``·`>` 등. 셸이 명령 구분·치환·리다이렉트로 해석한다.
- 셸을 거치지 않으면 메타문자를 해석할 주체가 없다.
- 남는 위험은 **인자 주입**이다. 셸이 없어도 `-`로 시작하는 값은 대상 프로그램이 옵션으로 읽는다. 관례상 `--`로 옵션 끝을 표시한다(POSIX 유틸리티 관례, 프로그램마다 지원 여부 다름).

### 4. LDAP 인젝션 — 필터 문법

```text
  "(&(uid=" + user + ")(userPassword=x))"     user = "*)(objectClass=*"
  → (&(uid=*)(objectClass=*)(userPassword=x))     uid=* 는 "uid가 있는 모든 항목", 조건 하나가 늘었다
```

- LDAP 검색 필터(RFC 4515)에서 `*`는 와일드카드, `(`·`)`는 필터 경계다.
- RFC 4515 §3: 값 안의 `*`·`(`·`)`·`\`·NUL은 `\2a`·`\28`·`\29`·`\5c`·`\00`으로 쓴다.
- JDK JNDI는 `DirContext.search(name, "(uid={0})", new Object[]{user}, ctls)`처럼 **필터 인자**를 받는다. 실험에서 내부 치환 결과가 `(uid=\2a\29\28objectClass=\2a)`였다(LDAP 판의 바인딩).

### 5. 바인딩으로 안 되는 곳

| 자리 | 바인딩 | 대처 |
|---|---|---|
| 값(`WHERE x = ?`, `VALUES (?)`) | 된다 | `PreparedStatement` |
| 식별자(테이블·열 이름, `ORDER BY` 열) | 안 된다 — 값으로 들어가 상수가 된다 | 허용 목록에서 고른다 |
| 키워드(`ASC`/`DESC`) | 안 된다 | 허용 목록(2택) |
| `LIKE` 패턴 | 값은 되지만 `%`·`_`는 여전히 패턴 문자 | `%`·`_`·`\` 이스케이프 |
| `IN (...)` 목록 | 개수만큼 `?` 생성 또는 배열 바인딩(`= ANY(?)`, PostgreSQL) | 자리표시자 개수는 코드가 정한다 |

- OWASP A03(2021): "테이블 이름, 열 이름 같은 SQL 구조는 이스케이프할 수 없다. 사용자가 고른 구조 이름은 위험하다."
- 실험: `ORDER BY ?`에 `"name DESC"`를 바인딩하면 서버 로그에 `ORDER BY $1`, 값 `'name DESC'`로 찍혔다. 상수로 정렬하니 정렬이 일어나지 않았다(오류도 없다 — 조용한 실패).

## 쓰이는 자료구조·알고리즘

- **파서 문맥 분리**: 해석기는 어휘 분석기(상태 기계)와 문법 분석기로 입력을 트리로 만든다. 바인딩은 "트리 모양을 먼저 확정하고 리프 값만 나중에 채우는" 구조다.
  - 같은 생각이 XSS의 문맥별 인코딩(19번)과 이어진다.
- **허용 목록 = 해시 집합·맵 조회**: 식별자 선택은 `Map<String, String>`에서 키로 찾는다. 키가 없으면 거부한다(O(1)).
- **프로그램 실행 인자 = 문자열 배열(argv)**: 셸 파싱 없이 운영체제 `execve`에 그대로 전달된다.
- 문자열 매칭(정적 분석 도구가 "연결된 문자열이 실행 메서드에 닿는 흐름"을 찾는 것)은 데이터 흐름 분석이다 — [engineering-practice/15-security-standards](../../engineering-practice/15-security-standards/2-summary.md)의 SAST 실험.

## 적용 — 풀어나가는 법

### 1. SQL — 연결 → 바인딩

```java
// (취약) 입력을 쿼리 문자열에 이어 붙인다
String sql = "SELECT id, name FROM member WHERE name = '" + q + "'";
try (Statement s = c.createStatement(); ResultSet r = s.executeQuery(sql)) { ... }

// (고친 예) 틀과 값을 분리한다
try (PreparedStatement p = c.prepareStatement("SELECT id, name FROM member WHERE name = ?")) {
    p.setString(1, q);
    try (ResultSet r = p.executeQuery()) { ... }
}
```

- 실험 결과(위 2절): 입력 `nobody' OR '1'='1`에 연결은 `rows=3`, 바인딩은 `rows=0`.
- 따옴표가 든 정상 입력 `o'brien`: 연결은 `SQLState=42601 Unterminated string literal ...`. 이 오류는 서버가 아니라 **pgjdbc 드라이버의 SQL 파서**가 냈다(서버 로그에 그 문장이 없었다). 바인딩은 정상 실행(0행).
- JPA·Spring Data도 같다. JPQL·네이티브 쿼리에 `+`로 이어 붙이면 똑같이 뚫린다. JPQL은 `:name` 파라미터, 네이티브 쿼리는 위치 파라미터(`?1`)를 쓴다(Jakarta Persistence 3.2 §3.11.11.4: 네이티브 쿼리의 이름 붙은 파라미터는 정의되지 않음, 이식 가능한 것은 위치 파라미터뿐).

```java
// Spring Data JPA — (취약) 문자열 연결 네이티브 쿼리 대신
@Query(value = "SELECT * FROM member WHERE name = ?1", nativeQuery = true)
List<Member> findByName(String name);
```

### 2. 정렬 열 — 허용 목록

```java
private static final Map<String, String> SORT = Map.of("name", "name", "joined", "created_at");

String col = SORT.get(req.sort());            // 없으면 null
if (col == null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "unknown sort");
String dir = "desc".equalsIgnoreCase(req.dir()) ? "DESC" : "ASC";
String sql = "SELECT id, name FROM member ORDER BY " + col + " " + dir;   // 연결하는 것은 코드가 고른 상수뿐
```

- 실험: 허용 목록에 `"name; DROP TABLE member"`를 넣으면 `null` → 거부.

### 3. `LIKE` 검색

```java
String pattern = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%";
p.setString(1, pattern);   // WHERE name LIKE ?   (PostgreSQL 기본 이스케이프 문자 = \)
```

- 실험: 바인딩한 `'%'`는 `count=3`(전부 일치), 이스케이프한 `'\%'`는 `count=0`. 바인딩은 인젝션을 막지만 **패턴 의미**는 막지 않는다. 막지 않으면 비싼 전체 스캔 검색을 누구나 유도할 수 있다.

### 4. 외부 명령 — 셸을 빼고, 인자는 배열로

```java
// (취약) 셸 경유
new ProcessBuilder("sh", "-c", "ls /tmp/files/" + input).start();
// (고친 예) 셸 없이, 옵션 끝 표시, 입력은 허용 문자로 먼저 검증
if (!input.matches("[A-Za-z0-9._-]{1,64}")) throw new IllegalArgumentException("bad name");
new ProcessBuilder("ls", "--", "/tmp/files/" + input).start();
```

(실험, OpenJDK 21.0.12, `--network none` 컨테이너, 이미지의 `ls` = uutils coreutils 0.8.0, 2026-10-07)

```text
[sh -c] exit=0 out=/tmp/files/report.txt | INJECTED-ubuntu
[argv]  exit=2 out=ls: cannot access '/tmp/files/report.txt; echo INJECTED-$(whoami)': No such file or directory
[argv opt]   exit=0 out=ls (uutils coreutils) 0.8.0
[argv -- opt] exit=2 out=ls: cannot access '--version': No such file or directory
```

- 1행: 셸이 `;` 뒤를 두 번째 명령으로 실행했다.
- 2행: 같은 입력이 파일 이름 한 개로 취급되었다.
- 3·4행: 셸이 없어도 `--version`은 옵션이 되었다. `--`를 넣자 파일 이름이 되었다.
- 더 좋은 길은 외부 명령 자체를 없애는 것이다. 파일 목록은 `Files.list`, 이미지 변환은 라이브러리로.

### 5. 계층별 책임

| 계층 | 하는 일 |
|---|---|
| 드라이버·프로토콜 | 확장 질의 프로토콜로 틀과 값을 분리 전송(PostgreSQL `Parse`/`Bind`, pgjdbc 기본 `preferQueryMode=extended`) |
| 라이브러리 | `PreparedStatement`·JPA 파라미터·JNDI 필터 인자 제공 |
| 애플리케이션 | 연결하지 않기, 식별자는 허용 목록, 셸 쓰지 않기, 최소 권한 DB 계정 |
| 심층 방어 | DB 계정 권한 축소(읽기 API는 `SELECT`만), WAF·SAST는 보조 |

## 장애 시나리오와 대처

### 1. 검색 한 번에 전 회원 정보가 응답에 실린다

- **현상**: 특정 검색어로 결과 수가 전체 행 수와 같다.
- **보이는 형태**: 접근 로그에 `'`·`OR`·`--`가 든 쿼리스트링, 응답 크기 급증. DB 로그에 조건이 늘어난 SQL.
- **원인**: 문자열 연결 쿼리. 입력의 따옴표가 리터럴을 닫았다.
- **대처**: `PreparedStatement`로 교체, 같은 패턴을 SAST로 전수 검색. 유출 범위는 DB 감사 로그·접근 로그로 산정([26-security-logging-and-audit](../26-security-logging-and-audit/2-summary.md)).

### 2. 이름에 따옴표가 든 고객만 `500`

- **현상**: `O'Neil` 같은 고객만 조회·가입이 실패한다.
- **보이는 형태**: `SQLState=42601`(PostgreSQL 문법 오류 계열). pgjdbc면 `Unterminated string literal`이 드라이버에서 난다.
- **원인**: 장애 1과 같은 연결 쿼리. 기능 버그로 보이지만 같은 구멍이다.
- **대처**: 따옴표를 지우거나 두 번 쓰는 "땜질"이 아니라 바인딩으로 고친다. 이 오류 로그는 인젝션 결함의 단서로 분류한다.

### 3. 썸네일 생성 요청 뒤 서버에 모르는 프로세스

- **현상**: 업로드 처리 서버의 CPU가 오르고 낯선 자식 프로세스가 보인다.
- **보이는 형태**: 프로세스 목록에 `sh -c ...`, 업로드 파일 이름에 `;`·`$(`.
- **원인**: 파일 이름을 셸 명령 문자열에 이어 붙였다. 셸 경유 → 원격 명령 실행.
- **대처**: 셸 제거, 인자 배열, 저장 파일 이름은 서버가 생성(UUID). 실행 계정 권한 최소화, 컨테이너 격리. 침해가 의심되면 사고 대응 절차([reliability/26](../../reliability/26-incident-response-and-postmortem/2-summary.md)).

### 4. 정렬 파라미터를 바인딩으로 "고쳤더니" 정렬이 안 된다

- **현상**: `?sort=name`을 줘도 순서가 그대로다. 오류는 없다.
- **보이는 형태**: DB 로그 `ORDER BY $1`, `Parameters: $1 = 'name'`.
- **원인**: 식별자는 바인딩할 수 없다. 값으로 들어가 상수 정렬이 되었다.
- **대처**: 허용 목록 맵에서 열 이름을 고른다(적용 2).

### 5. ⚠ "ORM을 쓰니까 안전하다"

- **현상**: 코드 리뷰에서 넘어간 `@Query(nativeQuery=true)` 문자열 연결이 침투 테스트에서 걸린다.
- **원인**: ORM은 바인딩 **도구**를 줄 뿐이다. 문자열을 연결하면 ORM 안에서도 인젝션이다(OWASP A03이 ORM 인젝션을 따로 적는다).
- **대처**: 쿼리 문자열에 `+`·`String.format`·템플릿 보간이 닿는 지점을 SAST 규칙으로 막는다.

## 핵심 문장

- 인젝션은 데이터가 해석기의 파서에서 코드로 읽히는 결함이다. 원인은 파싱 **전에** 입력을 섞는 문자열 연결이다.
- 파라미터 바인딩은 쿼리 틀을 먼저 파싱하고 값은 나중에 대입한다. 그래서 값이 문법을 바꾸지 못한다.
- 식별자·키워드·`LIKE` 패턴은 바인딩만으로 해결되지 않는다. 허용 목록과 패턴 이스케이프가 필요하다.
- 셸을 거치지 않으면 셸 메타문자를 해석할 주체가 없다. 남는 인자 주입은 `--`와 입력 검증으로 막는다.
- 입력 검증·이스케이프는 보조다. 1차 방어는 해석기 API가 제공하는 문맥 분리(바인딩·인자 배열·필터 인자)다.

## 관련 주제·근거

- 선행
  - [01-security-principles](../01-security-principles/2-summary.md) — 최소 권한·심층 방어
  - [language/03-parsing-grammars-ast](../../language/03-parsing-grammars-ast/2-summary.md)
- 후속·연결
  - [19-xss-and-csp](../19-xss-and-csp/2-summary.md) — 같은 문제의 HTML·JS 판(문맥별 인코딩)
  - [23-deserialization-and-parser-attacks](../23-deserialization-and-parser-attacks/2-summary.md) — 문자열 lookup 기능(Log4Shell)
  - [engineering-practice/15-security-standards](../../engineering-practice/15-security-standards/2-summary.md) — SAST로 `SQL_INJECTION_JDBC` 검출 실험
  - [database/24-transaction-boundaries-in-app-code](../../database/24-transaction-boundaries-in-app-code/2-summary.md) — JDBC·JPA 쓰는 자리
- 1차 출처
  - OWASP Top 10 2021 A03 Injection — 포함 CWE(79·89·77/78·90), 예방(안전한 API, 양성 입력 검증은 완전한 방어 아님, 구조 이름 이스케이프 불가) <https://top10.owasp.org/2021/A03_2021-Injection/>
  - OWASP Top 10 2025 — A05 Injection <https://top10.owasp.org/2025>
  - OWASP SQL Injection Prevention Cheat Sheet <https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html> · OS Command Injection Defense Cheat Sheet <https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html> · LDAP Injection Prevention Cheat Sheet <https://cheatsheetseries.owasp.org/cheatsheets/LDAP_Injection_Prevention_Cheat_Sheet.html>
  - RFC 4515 §3 — LDAP 검색 필터 문자열 표현과 값 이스케이프 <https://www.rfc-editor.org/rfc/rfc4515#section-3>
  - PostgreSQL 17 문서 53.2.3 Extended Query(Parse·Bind·Execute) <https://www.postgresql.org/docs/17/protocol-flow.html> · 9.7.1 LIKE(기본 이스케이프 `\`) <https://www.postgresql.org/docs/17/functions-matching.html>
  - pgjdbc 연결 설정 `preferQueryMode`(기본 `extended`) <https://jdbc.postgresql.org/documentation/use/> · Jakarta Persistence 3.2 §3.11.11.4(네이티브 쿼리 파라미터) <https://jakarta.ee/specifications/persistence/3.2/jakarta-persistence-spec-3.2>
  - CWE-89 <https://cwe.mitre.org/data/definitions/89.html> · CWE-78 <https://cwe.mitre.org/data/definitions/78.html> · CWE-90 <https://cwe.mitre.org/data/definitions/90.html>
- 실험 목록(2026-10-07, 로컬 일회용 컨테이너만)
  - A. 문자열 연결 vs `PreparedStatement` — PostgreSQL 17.11 + pgjdbc 42.7.7 + temurin 21.0.12, 내부 전용 네트워크, `log_statement=all`: 연결 `rows=3`·바인딩 `rows=0`, 서버 로그의 `$1`·`Parameters`, `o'brien` 연결 시 드라이버 `42601`, `ORDER BY $1` 상수 정렬, `LIKE '%'` 3건 vs `'\%'` 0건
  - B. `sh -c` vs 인자 배열 vs `--` — temurin 21.0.12, `--network none`
  - C. LDAP 필터 연결 vs RFC 4515 이스케이프 vs JNDI 필터 인자 치환(`com.sun.jndi.toolkit.dir.SearchFilter.format`, `--add-exports`로 호출) — 서버 없이 필터 문자열만 비교
