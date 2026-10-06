# security/18-injection — 정답

## 정답

### 1. 섞이는 시점

- 문자열 연결은 입력을 쿼리 문자열에 넣은 **뒤에** DB 파서가 파싱한다. 입력의 따옴표가 리터럴을 닫고, 뒤의 글자가 새 문법 요소가 된다.
- 바인딩은 쿼리 틀(`... = $1`)을 **먼저** 파싱해 문법 트리를 확정한다. 값은 그 뒤에 자리표시자에 대입된다. 값이 무엇이든 트리는 바뀌지 않는다.
- PostgreSQL에서는 확장 질의 프로토콜의 `Parse`(틀)와 `Bind`(값)가 이 분리를 맡는다(문서 53.2.3, 실행 계획은 보통 `Bind` 때). pgjdbc 기본값 `preferQueryMode=extended` 기준이다. `simple`로 바꾸면 Parse·Bind 없이 단순 질의(`Q`)로 보낸다(pgjdbc 연결 설정 문서).

### 2. 같은 입력, 두 결과

| | 결과 | 서버 로그 |
|---|---|---|
| (a) 연결 | 3행 전부 | `... WHERE name = 'nobody' OR '1'='1'` |
| (b) 바인딩 | 0행 | `... WHERE name = $1` + `DETAIL: Parameters: $1 = 'nobody'' OR ''1''=''1'` |

- 로컬 실험(PostgreSQL 17.11, pgjdbc 42.7.7)에서 이렇게 나왔다. (a)는 `OR '1'='1'`이 조건이 되었고, (b)는 그 글자 전체가 이름 한 개였다.

### 3. 바인딩이 안 되는 자리

- `WHERE` 값: 된다.
- `ORDER BY` 열 이름: 안 된다. 허용 목록 맵에서 열 이름을 고른다.
- `ASC/DESC`: 안 된다. 두 값 중 하나를 코드가 고른다.
- `LIKE` 검색어: 바인딩은 되지만 `%`·`_`가 패턴 문자로 남는다. `\`·`%`·`_`를 이스케이프한다(PostgreSQL 기본 이스케이프 문자 `\`).
- OWASP A03(2021): 테이블·열 이름 같은 구조는 이스케이프할 수 없다.

### 4. `ORDER BY ?`

- 오류는 나지 않는다. 값 `'name DESC'`는 문자열 **상수**로 들어간다.
- 모든 행의 정렬 키가 같은 상수이므로 정렬이 일어나지 않는다(순서 보장 없음).
- 실험 로그: `ORDER BY $1`, `Parameters: $1 = 'name DESC'`. 조용한 실패라 테스트가 정렬 결과를 확인하지 않으면 놓친다.

### 5. 셸 없는 실행

- 막히는 것: 셸 메타문자(`;`·`|`·`$( )` 등). 해석할 셸이 없으니 입력은 인자 한 개다. 실험에서 `report.txt; echo ...`는 "그런 파일 없음"이 되었다.
- 남는 것: **인자 주입**. `-`로 시작하는 값은 대상 프로그램이 옵션으로 읽는다(실험: `ls --version`이 버전을 출력).
- 대처: 옵션 끝 표시 `--`(실험: `ls -- --version` → 파일 없음), 허용 문자 검증, 서버가 만든 파일 이름(UUID), 가능하면 외부 명령 대신 라이브러리.

### 6. LDAP

- `(uid=*)`는 "uid 속성이 있는 모든 항목"이다. 입력에 `)(`가 있으면 필터 조건이 늘어난다(실험: `(&(uid=*)(objectClass=*)(userPassword=x))`).
- RFC 4515 §3 이스케이프(`*`→`\2a`, `(`→`\28`, `)`→`\29`, `\`→`\5c`, NUL→`\00`)는 SQL의 "해석기 전용 이스케이프"에 해당한다.
- JNDI의 `search(name, "(uid={0})", args, ctls)`는 SQL의 **바인딩**에 해당한다. 실험에서 치환 결과가 `(uid=\2a\29\28objectClass=\2a)`였다.

### 7. 따옴표 고객의 `42601`

- 입력의 따옴표가 SQL 문법을 깨뜨렸다는 뜻이다. 즉 입력이 문법에 영향을 줄 수 있다 = 인젝션 가능 지점이다.
- pgjdbc에서는 드라이버 SQL 파서가 `Unterminated string literal`을 낸다(실험에서 서버 로그에는 그 문장이 없었다).
- 수정: 따옴표 제거·두 번 쓰기 같은 땜질이 아니라 `PreparedStatement`. 같은 패턴을 SAST로 전수 검색한다.

### 8. ORM 안의 인젝션

```java
// 취약: 네이티브 쿼리에 문자열 연결
em.createNativeQuery("SELECT * FROM member WHERE name = '" + name + "'").getResultList();
// 고친 예
em.createNativeQuery("SELECT * FROM member WHERE name = ?1").setParameter(1, name).getResultList();
// 네이티브 쿼리의 이식 가능한 바인딩은 위치 파라미터(Jakarta Persistence 3.2 §3.11.11.4)
```

- ORM은 바인딩 도구를 줄 뿐이다. OWASP A03(2021)은 ORM 인젝션을 따로 적는다.
- 탐지: SAST(예: FindSecBugs의 `SQL_INJECTION_JPA`·`SQL_INJECTION_JDBC` 규칙류)로 "연결 문자열이 실행 메서드에 닿는 흐름"을 찾는다([engineering-practice/15](../../engineering-practice/15-security-standards/2-summary.md) 실험). 예방: 리뷰 규칙(쿼리 문자열에 `+`·`format` 금지), 최소 권한 DB 계정.

### 9. 검증·이스케이프가 보조인 이유

- OWASP A03(2021): 양성(허용 목록) 서버 측 입력 검증은 "완전한 방어가 아니다". 많은 애플리케이션이 특수 문자를 정상 데이터로 받아야 하기 때문이다(`o'brien`).
- 이스케이프는 "남은 동적 쿼리"에만, 그 해석기 전용 문법으로 한다. 해석기·문자 집합마다 규칙이 달라 누락되기 쉽다.
- 1차 방어는 해석기 API의 문맥 분리(안전한 API·파라미터화된 인터페이스)다.
