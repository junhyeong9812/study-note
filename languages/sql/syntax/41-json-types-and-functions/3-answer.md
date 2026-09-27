# sql/41-JSON 타입과 함수 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러·경고는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 표는 기존 `emp`·`dept` 만 썼고 JSON 문서는 CTE 안의 리터럴이다 — **새로 만든 표가 없다.**\
> ★ **13번 한 문항만 실행으로 확인하지 못했다**(표 생성 금지). 그 자리에 그렇게 적었다.\
> 문서 근거는 [PG 18 JSON Types](https://www.postgresql.org/docs/18/datatype-json.html) · [PG 18 JSON Functions](https://www.postgresql.org/docs/18/functions-json.html) · [MySQL 8.4 JSON](https://dev.mysql.com/doc/refman/8.4/en/json.html) · [MySQL 8.4 CREATE INDEX](https://dev.mysql.com/doc/refman/8.4/en/create-index.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 세 타입에 같은 문자열을 넣으면

**PG `jsonb` 와 MySQL `JSON` 이 한 글자도 다르지 않고, PG `json` 만 원문 그대로다.**

```text
### SQL: SELECT CAST('{"b":2,"a":1,"a":9,"tags":["x","y","z"],"boss":{"name":"ann","id":1}}' AS jsonb);
--- PG 18.6 ---
                                     doc                                     
-----------------------------------------------------------------------------
 {"a": 9, "b": 2, "boss": {"id": 1, "name": "ann"}, "tags": ["x", "y", "z"]}
(1 row)

### SQL: SELECT CAST('...같은 문자열...' AS json);
--- PG 18.6 ---
                                  doc                                  
-----------------------------------------------------------------------
 {"b":2,"a":1,"a":9,"tags":["x","y","z"],"boss":{"name":"ann","id":1}}
(1 row)

### SQL: SELECT CAST('...같은 문자열...' AS JSON);
--- MySQL 8.4.10 ---
+-----------------------------------------------------------------------------+
| doc                                                                         |
+-----------------------------------------------------------------------------+
| {"a": 9, "b": 2, "boss": {"id": 1, "name": "ann"}, "tags": ["x", "y", "z"]} |
+-----------------------------------------------------------------------------+
```

**무엇이 일어났나** — 세 가지가 동시에 일어났다.

```text
 입력  {"b":2, "a":1, "a":9, "tags":[...], "boss":{"name":...,"id":...}}
         ↓ (jsonb · MySQL JSON)
  (1) 키를 정렬한다        b,a,a,tags,boss  ->  a, b, boss, tags
  (2) 중복 키를 지운다     "a":1 과 "a":9   ->  마지막 것(9)만 남는다  ★
  (3) 공백을 정규화한다    "a":9            ->  "a": 9
      중첩 객체 안에서도 같은 일이 일어난다  {"name":..,"id":..} -> {"id":.., "name":..}
```

★ **`"a":1` 이 사라졌다.** 중복 키는 **마지막 것이 이긴다** — 두 엔진 다 그랬다.

**결론** — **MySQL 의 `JSON` 은 PG 의 `jsonb` 에 해당한다.** PG 의 `json`(원문 보존)에 해당하는 타입은 **MySQL 에 없다.**

---

### 2. 키 정렬 기준

**사전순이 아니다. 「길이 먼저, 그다음 바이트순」이다.**

```text
### SQL: SELECT CAST('{"b":1,"aa":2}' AS jsonb);  /  ... AS JSON);
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 {"b": 1, "aa": 2}               +-------------------+
                                 | {"b": 1, "aa": 2} |
                                 +-------------------+
```

```text
 사전순이라면       aa, b
 실제 출력          b, aa      <- 길이 1 이 길이 2 보다 앞이다
```

**두 엔진이 같았다.** 단 이것은 **관찰이지 보장이 아니다** — 저장 형식의 귀결이지 JSON 명세의 요구가 아니다.\
★ **어느 쪽이든 「넣은 순서」는 아니다.** **`jsonb`/`JSON` 의 키 순서에 의미를 담지 마라.** 순서가 필요하면 **배열**을 쓴다.

---

### 3. `->` 와 `->>`

**값은 똑같이 보이고 타입이 다르다. 눈으로는 구분할 수 없다.**

```text
### SQL: SELECT doc -> 'boss' AS arrow, pg_typeof(doc -> 'boss') AS arrow_type,
                doc ->> 'boss' AS darrow, pg_typeof(doc ->> 'boss') AS darrow_type FROM j;
--- PG 18.6 ---
      arrow      | arrow_type |     darrow      | darrow_type 
-----------------+------------+-----------------+-------------
 {"name": "ann"} | jsonb      | {"name": "ann"} | text
(1 row)
```

★ **`arrow` 와 `darrow` 의 글자가 한 글자도 다르지 않다.** `pg_typeof` 가 없으면 못 알아챈다.

**문자열 값에서는 눈에도 보인다.**

```text
### SQL: SELECT doc -> 'boss' -> 'name' AS a, doc -> 'boss' ->> 'name' AS b FROM j;
--- PG 18.6 ---                  --- MySQL 8.4.10 ('$.boss.name') ---
   a   |  b                      +-------+------+
-------+-----                    | a     | b    |
 "ann" | ann                     +-------+------+
(1 row)                          | "ann" | ann  |
                                 +-------+------+
```

```text
 doc -> 'boss' -> 'name'   ->  "ann"   JSON 문자열. 따옴표가 값의 일부다
 doc -> 'boss' ->> 'name'  ->  ann     SQL 문자열. 비교·조인에 쓸 수 있다

 doc -> 'name' = 'ann'   ->  "ann" = 'ann'  ->  안 맞는다  ★ 흔한 사고
 doc ->> 'name' = 'ann'  ->  ann   = 'ann'  ->  맞는다
```

**규칙** — **계속 파고들 거면 `->`, 값을 꺼내 쓸 거면 `->>`.**

---

### 4. MySQL 에서 `->>` 의 반환 타입 확인하기

**`ERROR 3141` 이 나온다. 그 에러가 곧 「JSON 이 아니다」의 증거다.**

```text
### SQL: SELECT JSON_TYPE(doc -> '$.boss.name') FROM j;    -- -> 쪽
--- MySQL 8.4.10 ---
+--------+
| STRING |
+--------+

### SQL: SELECT JSON_TYPE(doc ->> '$.boss.name') FROM j;   -- ->> 쪽
--- MySQL 8.4.10 ---
ERROR 3141 (22032) at line 1: Invalid JSON text in argument 1 to function json_type: "Invalid value." at position 0.
```

**왜 증거가 되는가** — `JSON_TYPE()` 은 **유효한 JSON 텍스트**만 받는다.

```text
 -> 가 낸 것   "ann"   따옴표가 있다  -> 유효한 JSON 문자열  -> STRING
 ->> 가 낸 것   ann    따옴표가 없다  -> JSON 으로는 못 읽는다 -> ERROR 3141
                                        ^^^^^^^^^^^^^^^^^^^^
                                        곧 "평범한 SQL 문자열"이라는 뜻이다
```

★ **에러를 증거로 쓴 자리다.** MySQL 에는 `pg_typeof` 같은 도구가 없으므로, **거부당하는 것 자체**로 타입을 알아낸다.

세 표기가 같은 값을 내는 것도 같이 확인된다.

```text
### SQL: SELECT JSON_EXTRACT(doc,'$.boss.name') AS ex,
                JSON_UNQUOTE(JSON_EXTRACT(doc,'$.boss.name')) AS unq,
                JSON_VALUE(doc,'$.boss.name') AS val FROM j;
--- MySQL 8.4.10 ---
+-------+------+------+
| ex    | unq  | val  |
+-------+------+------+
| "ann" | ann  | ann  |
+-------+------+------+
```

`->` = `JSON_EXTRACT`, `->>` = `JSON_UNQUOTE(JSON_EXTRACT(...))` 다.

---

### 5. 배열의 마지막 원소

**PG 는 음수 첨자 `-1`, MySQL 은 `last` 라는 낱말이다.**

```text
### SQL: (PG) SELECT doc -> 'tags' -> 0 AS first_json, doc -> 'tags' ->> 0 AS first_text,
                     doc -> 'tags' -> -1 AS last FROM j;
--- PG 18.6 ---
 first_json | first_text | last 
------------+------------+------
 "x"        | x          | "y"
(1 row)

### SQL: (MySQL) SELECT doc -> '$.tags[0]' AS first_json, doc ->> '$.tags[0]' AS first_text,
                        doc ->> '$.tags[last]' AS last_text FROM j;
--- MySQL 8.4.10 ---
+------------+------------+-----------+
| first_json | first_text | last_text |
+------------+------------+-----------+
| "x"        | x          | y         |
+------------+------------+-----------+
```

```text
 PG      doc -> 'tags' -> -1        첨자가 연산자의 오른쪽 피연산자다
 MySQL   doc ->> '$.tags[last]'     첨자가 경로 문자열 안에 들어간다
```

**첨자가 0 부터인 것은 두 엔진이 같다.** `->`/`->>` 의 구분도 배열에서 똑같이 적용된다.

---

### 6. 배열을 행으로 펴기

**PG 는 `jsonb_array_elements(_text)`, MySQL 은 `JSON_TABLE`. 그리고 `JSON_TABLE` 은 두 엔진에 다 있다.**

```text
### SQL: (PG) SELECT jsonb_array_length(doc -> 'tags') AS len, t.ord, t.val
              FROM j, LATERAL jsonb_array_elements_text(doc -> 'tags') WITH ORDINALITY AS t(val, ord);
--- PG 18.6 ---
 len | ord | val 
-----+-----+-----
   2 |   1 | x
   2 |   2 | y
(2 rows)

### SQL: (MySQL) SELECT JSON_LENGTH(doc, '$.tags') AS len, t.ord, t.val
                 FROM j, JSON_TABLE(doc, '$.tags[*]' COLUMNS (ord FOR ORDINALITY, val VARCHAR(10) PATH '$')) AS t;
--- MySQL 8.4.10 ---
+------+------+------+
| len  | ord  | val  |
+------+------+------+
|    2 |    1 | x    |
|    2 |    2 | y    |
+------+------+------+

### SQL: (PG 18.6 에도 JSON_TABLE 이 있다)
         SELECT t.* FROM j, JSON_TABLE(doc, '$.tags[*]' COLUMNS (ord FOR ORDINALITY, val text PATH '$')) AS t;
--- PG 18.6 ---
 ord | val 
-----+-----
   1 | x
   2 | y
(2 rows)
```

★ **`JSON_TABLE` 이 이 주제에서 가장 넓은 공통 지대다.** 문법이 거의 같다 — 열 타입 이름(`text`/`VARCHAR(10)`)만 갈린다.

**버전 주의** — PG 는 **17 부터**, MySQL 은 **8.0.4 부터**다(릴리스 노트).

> "Add function `JSON_TABLE()` to convert `JSON` data to a table representation"\
> — [PostgreSQL 17 릴리스 노트](https://www.postgresql.org/docs/release/17.0/)

PG 16 이하를 지원해야 하면 `jsonb_array_elements` 쪽을 쓴다. `LATERAL` 이 왜 필요한지는 [20번](../20-lateral-join/)이 정본이다.

---

### 7. 서로의 경로 문법을 던지면

**(A) PG 는 조용히 `NULL` · (B) MySQL 은 `ERROR 3143`. ★ PG 쪽이 훨씬 위험하다.**

```text
### SQL: WITH j AS (SELECT CAST('{"a":1}' AS jsonb) AS doc)
         SELECT doc -> 'a' AS ok, doc -> '$.a' AS mysql_style, (doc -> '$.a') IS NULL AS is_null FROM j;
--- PG 18.6 ---
 ok | mysql_style | is_null 
----+-------------+---------
 1  |             | t
(1 row)

### SQL: WITH j AS (SELECT CAST('{"a":1}' AS JSON) AS doc) SELECT doc -> 'a' FROM j;
--- MySQL 8.4.10 ---
ERROR 3143 (42000) at line 1: Invalid JSON path expression. The error is around character position 1.
```

**왜 그런가** — **`->` 의 오른쪽이 무엇인지가 두 엔진에서 다르다.**

```text
 PG 의 ->        오른쪽은 "키 이름" 이다
                 '$.a' 라는 이름의 키를 찾는다 -> 그런 키는 없다 -> NULL   ★ 조용하다

 MySQL 의 ->     오른쪽은 "경로 표현" 이다
                 'a' 를 경로로 파싱하려 한다 -> $ 로 시작하지 않는다 -> ERROR 3143
```

```text
 PG 로 이식했을 때                     MySQL 로 이식했을 때
 에러 없음 · 경고 없음                 즉시 ERROR
 모든 행이 NULL                        배포 전에 잡힌다
   -> 바깥 조건이 전부 UNKNOWN (04번)
   -> "데이터가 없네" 로 읽힌다
   -> 통계가 비고 나서야 안다  ★
```

★ **"에러가 안 났으니 잘 옮겼다"가 가장 위험한 판단이다.** 이식 뒤에는 **행 수와 `NULL` 비율**을 먼저 센다.

**나머지 연산자·함수는 서로 확실히 거부한다.**

```text
### SQL: (PG 에 MySQL 함수) SELECT JSON_EXTRACT(doc, '$.a') FROM j;
--- PG 18.6 ---
ERROR:  function json_extract(jsonb, unknown) does not exist
HINT:  No function matches the given name and argument types. You might need to add explicit type casts.

### SQL: (MySQL 에 PG 함수) SELECT jsonb_extract_path_text(doc, 'boss', 'name') FROM j;
--- MySQL 8.4.10 ---
ERROR 1305 (42000) at line 1: FUNCTION study.jsonb_extract_path_text does not exist

### SQL: (MySQL 에 PG 연산자) SELECT doc @> '{"a":1}' FROM j;   /   SELECT doc ? 'a' FROM j;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: ... near '@> '{"a":1}' FROM j' at line 1
ERROR 1064 (42000) at line 1: ... near '? 'a' FROM j' at line 1
```

---

### 8. `#>` 를 MySQL 에

**`#` 이 MySQL 에서 주석 시작이라, `doc` 뒤가 통째로 사라졌기 때문이다.**

```text
### SQL: WITH j AS (SELECT CAST('{"boss":{"name":"ann"}}' AS JSON) AS doc) SELECT doc #> '{boss,name}' FROM j;
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'doc' in 'field list'
```

**증명 — `#` 뒤가 사라지는지 직접 본다.**

```text
### SQL: SELECT 1 #> 2;               ### SQL: SELECT 1 AS a #> 2;
--- MySQL 8.4.10 ---                  --- MySQL 8.4.10 ---
+---+                                 +---+
| 1 |                                 | a |
+---+                                 +---+
| 1 |                                 | 1 |
+---+                                 +---+
```

`#> 2` 가 통째로 없어졌고, 두 번째 문에서는 `AS a` 까지는 살아 있다. **`#` 부터 줄 끝까지가 주석이다.**

```text
 내가 쓴 것     SELECT doc #> '{boss,name}' FROM j
 MySQL 이 본 것 SELECT doc                                <- # 뒤가 주석
                       ^^^ 별칭도 없는 맨 doc
                       -> 그런 열이 없다 -> ERROR 1054
```

★ **에러 메시지가 원인을 전혀 가리키지 않는다.** "열이 없다"는데 열은 있다.\
**MySQL 에서 설명 안 되는 `Unknown column` 을 만나면 `#` 을 먼저 찾아라.**

---

### 9. 키를 오타 내면

**두 엔진 다 조용히 `NULL` 이다. 열 이름 오타였다면 에러였다.**

```text
### SQL: (PG) SELECT doc ->> 'salary' AS kept, doc ->> 'salery' AS typo, jsonb_typeof(doc->'salary') AS t FROM j;
--- PG 18.6 ---
 kept | typo |   t    
------+------+--------
 삼백 |      | string
(1 row)

### SQL: (MySQL) SELECT doc ->> '$.salary' AS kept, doc ->> '$.salery' AS typo, JSON_TYPE(doc->'$.salary') AS t FROM j;
--- MySQL 8.4.10 ---
+--------+------+--------+
| kept   | typo | t      |
+--------+------+--------+
| 삼백   | NULL | STRING |
+--------+------+--------+
```

**열 이름 오타와의 차이.**

```text
 SELECT salery FROM emp              doc ->> 'salery'
   -> ERROR: column "salery" does     -> NULL
      not exist                       -> 에러도 경고도 없다
   -> 배포 전에 잡힌다                -> 배포되고 통계가 빈 뒤에 안다  ★
```

**왜 이렇게 되나** — 엔진은 **문서에 어떤 키가 있어야 하는지 모른다.** 스키마가 없으니 "없는 키"와 "오타"를 구분할 수단이 없다.

**방어선** — 키 존재 여부를 **따로 확인**한다.

```text
 PG      doc ? 'salary'                            -> t / f
 MySQL   JSON_CONTAINS_PATH(doc,'one','$.salary')  -> 1 / 0
```

이것이 11번 문항의 "JSON 을 쓰면 안 되는 자리" 논거의 절반이다.

---

### 10. 타입이 틀린 값을 계산하면

**PG 는 에러, MySQL 은 `1` 을 돌려주고 경고만 남긴다. `SHOW WARNINGS` 를 물어야 보인다.**

```text
### SQL: (PG) SELECT (doc ->> 'salary')::int + 1 AS boom FROM j;      -- doc = {"salary":"삼백"}
--- PG 18.6 ---
ERROR:  invalid input syntax for type integer: "삼백"

### SQL: (MySQL) SELECT CAST(doc ->> '$.salary' AS SIGNED) + 1 AS boom FROM j;
                 SHOW WARNINGS;
--- MySQL 8.4.10 ---
+------+
| boom |
+------+
|    1 |
+------+
+---------+------+---------------------------------------------+
| Level   | Code | Message                                     |
+---------+------+---------------------------------------------+
| Warning | 1292 | Truncated incorrect INTEGER value: '삼백'   |
+---------+------+---------------------------------------------+
```

**왜 `1` 인가** — MySQL 은 `'삼백'` 을 **읽을 수 있는 데까지 읽는다.** 읽을 수 있는 숫자가 없으니 `0` 이고, `0 + 1 = 1` 이다.

```text
 PG                              MySQL
 못 읽겠다 -> 문을 죽인다         읽을 수 있는 데까지 읽는다 -> 0
   -> 트랜잭션이 롤백된다           -> 계산이 계속된다
   -> 즉시 안다                     -> 보고서에 1 이 찍힌다
                                    -> 경고 1292 는 SHOW WARNINGS 로만 보인다  ★
```

★ **이것이 [35번](../35-type-system-and-casting/)의 한 줄 그대로다** — **"PG 는 못 읽으면 문을 죽이고, MySQL 은 읽을 수 있는 데까지 읽고 경고만 남긴다."**\
JSON 에서 더 위험한 이유는 **스키마가 그 값을 막아 주지 않아, 애초에 잘못된 타입이 들어와 있기 때문**이다.

**엔진이 막아 주는 것은 JSON 문법뿐이다.**

```text
### SQL: SELECT CAST('{"a":1,}' AS jsonb);   /   SELECT CAST('{"a":1,}' AS JSON);
--- PG 18.6 ---
ERROR:  invalid input syntax for type json
DETAIL:  Expected string, but found "}".
CONTEXT:  JSON data, line 1: {"a":1,}
--- MySQL 8.4.10 ---
ERROR 3141 (22032) at line 1: Invalid JSON text in argument 1 to function cast_as_json: "Missing a name for object member." at position 7.
```

**"올바른 JSON 인가"까지만 본다. 값의 타입은 보지 않는다.**

---

### 11. 인덱스가 걸리는 타입

**`jsonb` 만 걸린다. `json` 에는 연산자 클래스가 0개다 — 카탈로그가 답해 준다.**

```text
### SQL: SELECT am.amname AS index_method, opc.opcname AS opclass, opc.opcdefault AS is_default
         FROM pg_opclass opc JOIN pg_am am ON am.oid = opc.opcmethod
         WHERE opc.opcintype = 'jsonb'::regtype ORDER BY am.amname, opc.opcname;
--- PG 18.6 ---
 index_method |    opclass     | is_default 
--------------+----------------+------------
 btree        | jsonb_ops      | t
 gin          | jsonb_ops      | t
 gin          | jsonb_path_ops | f
 hash         | jsonb_ops      | t
(4 rows)

### SQL: SELECT count(*) AS json_opclasses FROM pg_opclass WHERE opcintype = 'json'::regtype;
--- PG 18.6 ---
 json_opclasses 
----------------
              0
(1 row)
```

**왜 카탈로그인가** — 실행 계획은 통계에 따라 흔들리지만([32번](../32-cte-with-clause/)), **`pg_opclass` 는 그 빌드의 정의**라 흔들리지 않는다.\
`0` 이라는 숫자는 "**문서에 없다"가 아니라 "서버가 없다고 대답했다**"이다 — 부재를 증명할 수 있는 드문 형태다.

```text
 jsonb  btree · hash · gin(둘)     -> 인덱스를 건다
 json   0 개                        -> 못 건다. 어떤 인덱스도 안 받는다
```

**그래서 PG 에서는 이유가 없으면 `jsonb`** 다. `json` 은 **원문을 글자 그대로 보존해야 할 때**만 고른다.

---

### 12. GIN 이 타는 연산자

**안 탄다. GIN `jsonb_ops` 가 받는 연산자 목록에 `->>` 가 없다.**

```text
### SQL: SELECT amopopr::regoperator AS indexable_operator FROM pg_amop
         WHERE amopfamily = (SELECT opcfamily FROM pg_opclass
                             WHERE opcname='jsonb_ops' AND opcmethod=(SELECT oid FROM pg_am WHERE amname='gin'))
         ORDER BY 1;
--- PG 18.6 ---
 indexable_operator 
--------------------
 @>(jsonb,jsonb)
 ?(jsonb,text)
 ?|(jsonb,text[])
 ?&(jsonb,text[])
 @?(jsonb,jsonpath)
 @@(jsonb,jsonpath)
(6 rows)
```

★ **여섯 개뿐이고 `->`·`->>`·`#>` 는 하나도 없다.**

```text
 GIN 이 답할 수 있는 질문              GIN 이 못 답하는 질문
 "이 문서가 {"a":1} 을 품고 있나"       "이 문서의 a 가 5 보다 큰가"
 "이 문서에 tags 키가 있나"             "name 이 'a' 로 시작하나"
   ↓                                      ↓
 역색인이 조각을 찾아 주면 된다          값을 꺼내 비교해야 한다
 -> @> · ? · @? · @@                     -> 표현식 인덱스가 따로 필요하다
```

**값 비교로 인덱스를 타려면** 표현식 인덱스를 따로 만든다 — `CREATE INDEX … ((doc->>'name'))`.\
그러면 **`doc->>'name' = 'ann'`** 은 타지만 **`doc @> …` 는 못 탄다.** 둘은 다른 인덱스다.

인덱스 정의는 [46번 주제](../46-index-definition-composite-partial-expression/), "언제 타고 언제 안 타나"는 [목록의 **47번 주제**](../47-when-indexes-are-used/)가 정본이다.

---

### 13. MySQL 의 인덱스 전략

**함수 키(생성 열)와 다중값 인덱스다. ★ 이 문항은 실행으로 확인하지 못했다.**

> ★ **이 작업은 표 생성이 금지돼 있어 `CREATE TABLE`·`ALTER TABLE` 을 던질 수 없었다.**\
> 아래 문장은 **MySQL 매뉴얼 인용**이고, 실행 출력이 아니다. 이 주제에서 **유일하게 안 돌려 본 자리**다.

> "Functional key parts enable indexing of values that cannot be indexed otherwise, such as `JSON` values. However, this must be done correctly to achieve the desired effect."\
> "A multi-valued index is a secondary index defined on a column that stores an array of values… Multi-valued indexes are intended for indexing `JSON` arrays."\
> — [MySQL 8.4 · CREATE INDEX](https://dev.mysql.com/doc/refman/8.4/en/create-index.html)

같은 페이지가 **`CAST` 를 감싸라**고 적는다.

```sql
-- 매뉴얼이 "이렇게 하면 원하는 효과가 안 난다"고 든 예
CREATE TABLE employees (data JSON, INDEX ((data->>'$.name')));
-- 매뉴얼이 권하는 형태
CREATE TABLE employees (data JSON, INDEX ((CAST(data->>'$.name' AS CHAR(30)))));
```

그리고 8.0.21 릴리스 노트가 `JSON_VALUE()` 를 **"simplifies creating indexes on `JSON` columns"** 라고 소개한다.

**인덱스에 들어갈 「표현식」 자체는 돌려 봤다** — 거기까지가 실행 확인의 범위다.

```text
### SQL: SELECT CAST(JSON_EXTRACT(CAST('{"a":1}' AS JSON), '$.a') AS UNSIGNED) AS casted;
         SELECT JSON_VALUE(CAST('{"a":1}' AS JSON), '$.a' RETURNING UNSIGNED) AS returning_typed;
--- MySQL 8.4.10 ---
+--------+                       +-----------------+
| casted |                       | returning_typed |
+--------+                       +-----------------+
|      1 |                       |               1 |
+--------+                       +-----------------+
```

**두 엔진의 전략 차이.**

```text
 PostgreSQL                          MySQL
 jsonb + GIN                         함수 키 / 생성 열 + 보통 인덱스
 문서 통째로 역색인                   미리 정한 키 하나만 색인
 -> 어떤 키로 찾을지 몰라도 된다      -> 키마다 인덱스를 따로 만든다
 -> 인덱스가 크다                     -> 인덱스가 작고 B-tree 라 범위 검색도 된다
 배열: jsonb_path_ops                배열: 다중값 인덱스
```

★ **PG 쪽이 "무엇으로 찾을지 모를 때" 강하고, MySQL 쪽이 "찾을 키가 정해졌을 때" 강하다.**\
바꿔 말하면 **MySQL 에서 JSON 을 쓰려면 검색 패턴을 먼저 정해야 한다.**

---

### 14. JSON 을 만드는 쪽

**PG 는 `jsonb_build_object`/`jsonb_agg`, MySQL 은 `JSON_OBJECT`/`JSON_ARRAYAGG`. 결과는 같다.**

```text
### SQL: (PG) SELECT jsonb_build_object('dept', d.name, 'members', jsonb_agg(e.name ORDER BY e.id)) AS doc
              FROM dept d JOIN emp e ON e.dept_id = d.id GROUP BY d.id, d.name ORDER BY d.id;
--- PG 18.6 ---
                     doc                      
----------------------------------------------
 {"dept": "sales", "members": ["ann", "bob"]}
 {"dept": "dev", "members": ["cho"]}
(2 rows)

### SQL: (MySQL) SELECT JSON_OBJECT('dept', d.name, 'members', JSON_ARRAYAGG(e.name)) AS doc
                 FROM dept d JOIN emp e ON e.dept_id = d.id GROUP BY d.id, d.name ORDER BY d.id;
--- MySQL 8.4.10 ---
+----------------------------------------------+
| doc                                          |
+----------------------------------------------+
| {"dept": "sales", "members": ["ann", "bob"]} |
| {"dept": "dev", "members": ["cho"]}          |
+----------------------------------------------+
```

**한 글자도 다르지 않다.** 이 주제에서 두 엔진이 가장 잘 맞는 자리다.

**두 가지 주의.**

1. **`hr` 부서가 없다.** 내부 조인이라 사원이 없는 부서가 빠졌다([13번](../13-inner-join/)). 빈 배열로라도 넣으려면 `LEFT JOIN` 이다([14번](../14-left-right-outer-join/)).
2. ★ **배열 안의 순서가 다르게 보장된다.** PG 는 `jsonb_agg(e.name ORDER BY e.id)` 로 **지정했고**, MySQL 의 `JSON_ARRAYAGG` 에는 **그 문법이 없다.**\
   위 MySQL 출력이 `["ann","bob"]` 로 나온 것은 **이 데이터에서 그랬을 뿐** 보장이 아니다.

**그리고 이 방향이 JSON 의 가장 안전한 사용법이다** — **저장은 관계형으로, 출력만 JSON 으로.**\
타입·`NOT NULL`·외래키·인덱스를 전부 지키면서 응답 모양만 JSON 으로 만든다.

---

### 15. 쓰면 안 되는 자리

**타입·필수·참조·오타 검출·인덱스를 한꺼번에 잃는다.**

```text
 열로 뒀을 때                        JSON 안에 뒀을 때
 +-------------------------------+   +--------------------------------+
 | 타입    salary int            |   | 아무 타입이나 들어간다 (10번)  |
 | 필수    NOT NULL              |   | 없으면 그냥 NULL (9번)         |
 | 참조    FK -> dept(id)        |   | 없는 부서를 가리켜도 통과      |
 | 오타    ERROR column ...      |   | NULL — 조용하다 (9번)          |
 | 인덱스  아무 열이나 바로       |   | GIN 은 포함만 · 값 비교는 별도 |
 | 변경    ALTER TABLE 로 추적    |   | 코드 안에만 있다               |
 +-------------------------------+   +--------------------------------+
```

**판정 기준 한 줄.**

> **"이 값으로 `WHERE` 하거나 `JOIN` 하거나 `SUM` 할 일이 있나?" — 있으면 열로 뺀다.**

| | 쓴다 | 안 쓴다 |
|---|---|---|
| 외부 API 원문·웹훅 페이로드 | **O** 형태를 모른다 | |
| 희소한 속성(종류마다 다른) | **O** 열로 만들면 대부분 `NULL` | |
| 읽기 전용 스냅샷(주문 시점 주소) | **O** 더는 안 바뀐다 | |
| 응답 모양 만들기 | **O** 14번의 방향 | |
| 질의 조건·조인 키(`status`·`dept_id`) | | **X** 인덱스와 제약이 필요하다 |
| 금액·수량 | | **X** 10번의 사고가 언제든 난다 |
| 다른 표를 가리키는 값 | | **X** 외래키를 못 건다 |
| 집계·정렬 대상 | | **X** 매번 캐스팅해야 하고 인덱스를 못 탄다 |

**타협안** — JSON 에 원문을 두되 **자주 쓰는 키만 열로 승격**한다.\
PG 는 생성 열이나 표현식 인덱스로, MySQL 은 생성 열로(13번). 그러면 **원문은 남고 질의는 인덱스를 탄다.**

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 세 타입의 정규화 (1번) | PG 18.6 × 2 · MySQL 8.4.10 | 3회 | `jsonb`·`json`·`JSON` |
| 키 정렬 기준 (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 길이 먼저 — **두 엔진 같았다** |
| `->` 대 `->>` (3번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `pg_typeof` 가 근거다 |
| MySQL 의 타입 확인 (4번) | MySQL 8.4.10 | 3회 | **`ERROR 3141` 이 근거다** |
| 배열 첨자 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 음수 대 `last` |
| 배열 펴기 (6번) | PG 18.6 × 2 · MySQL 8.4.10 | 3회 | `jsonb_array_elements` · `JSON_TABLE` 양쪽 |
| 경로 문법 교차 (7번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **PG 의 `NULL` 과 MySQL 의 `ERROR 3143` 이 각각 근거다** |
| `#` 주석 (8번) | MySQL 8.4.10 | 3회 | **`ERROR 1054` + `#` 실증 2회** |
| 키 오타 (9번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러 없이 `NULL`** — 무음 실패 |
| 타입 불일치 (10번) | PG 18.6 · MySQL 8.4.10 | 각 2회 + `SHOW WARNINGS` | ★ **경고 1292 가 근거다** |
| 인덱스 가능 타입 (11번) | PG 18.6 | 2회 | **카탈로그 조회** — `pg_opclass` |
| GIN 연산자 목록 (12번) | PG 18.6 | 1회 | **`pg_amop` 조회 — 6개** |
| MySQL 인덱스 (13번) | — | **0회** | ★ **안 돌려 봄 — 표 생성 금지.** 매뉴얼 인용 + 표현식만 2회 실행 |
| JSON 만들기 (14번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 결과가 한 글자도 안 달랐다 |
| 설계 판정 (15번) | — | — | 9·10·12번의 출력에서 따라 나온다 |

**구현 의존 항목** — 1·2번의 정규화와 11·12번의 카탈로그 내용이다.\
키 정렬이 「길이 먼저」인 것은 **저장 형식의 귀결**이지 JSON 명세의 요구가 아니다 — **두 엔진에서 같았다는 것은 관찰이지 보장이 아니다.**\
`pg_opclass`/`pg_amop` 는 **그 빌드의 정의**라 통계처럼 흔들리지는 않지만, **PG 버전이 오르면 목록이 늘 수 있다.**

★ **한쪽에서만 결론이 서는 실험** — **7번이 그렇다.**\
PG 의 `NULL` 은 **"PG 의 `->` 오른쪽은 키 이름이다"의 근거**이고, MySQL 의 `ERROR 3143` 은 **"MySQL 의 `->` 오른쪽은 경로다"의 근거**다.\
**두 출력은 서로를 증명하지 않는다** — "경로 문법이 다르다"는 결론은 **각각의 출력에서 따로** 나온다.\
같은 성격이 4번(MySQL 만)·8번(MySQL 만)·11·12번(PG 만)에도 있다 — **이 주제는 한쪽에서만 서는 실험이 유난히 많다.** 두 엔진의 JSON 이 문법 표면부터 다르기 때문이다.

★ **경고도 출력이다** — 10번의 MySQL 결과는 `boom = 1` 만 보면 **"잘 돌았다"로 읽힌다.**\
`SHOW WARNINGS` 를 따로 묻지 않으면 경고 1292 가 **보이지 않는다.** 애플리케이션은 대개 묻지 않는다.

★ **안 돌려 본 자리는 13번 하나다** — 이유는 **이 작업의 제약**(표 생성 금지)이고, 환경이 없어서가 아니다.\
그 자리는 **매뉴얼 인용**으로 적었고 본문·머리말에도 밝혔다. **인덱스에 들어갈 표현식 자체는 돌려 봤다.**

**언어 보장 항목** — 3·9번. `->`/`->>` 의 반환 타입 구분과 "없는 키는 `NULL`" 은 두 엔진에서 같았다.\
**방언이 갈리는 항목** — 1(타입 이름·`json` 의 부재) · 4(타입 확인 수단) · 5(마지막 원소) · 6(펴는 도구, 단 `JSON_TABLE` 은 공통) · 7(경로 문법) · 8(`#` 주석) · 10(틀린 타입의 처리) · 11~13(인덱스 전략) · 14(배열 순서 지정 가능 여부).\
**두 엔진이 같았던 것** — 정규화 결과(1·2), `->`/`->>` 의 의미(3), 없는 키(9), JSON 문법 검사(10), 만들기 함수의 결과(14).

**순서 보장** — 없다. 14번의 `ORDER BY d.id` 는 그래서 붙였고, **배열 안의 순서**는 PG 만 `jsonb_agg(… ORDER BY …)` 로 지정할 수 있다.
