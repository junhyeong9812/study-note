# sql/41-JSON 타입과 함수 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · JSON Types](https://www.postgresql.org/docs/18/datatype-json.html) · [PostgreSQL 18 · JSON Functions and Operators](https://www.postgresql.org/docs/18/functions-json.html) · [MySQL 8.4 · The JSON Data Type](https://dev.mysql.com/doc/refman/8.4/en/json.html) · [MySQL 8.4 · JSON Functions](https://dev.mysql.com/doc/refman/8.4/en/json-functions.html) · [MySQL 8.4 · CREATE INDEX](https://dev.mysql.com/doc/refman/8.4/en/create-index.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러·경고는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> 표는 기존 `emp`·`dept` 만 썼고 **JSON 문서는 CTE 안에서 리터럴로 만들었다.** **새로 만든 표가 없다.**\
> ★ **딱 한 자리만 실행으로 확인하지 못했다** — **MySQL 의 인덱스 생성**(10번 절). 이 작업이 **표 생성 금지**라 `CREATE TABLE`·`ALTER TABLE` 을 던질 수 없었다. 그 자리는 **매뉴얼 인용으로만** 적었고 본문에 그렇게 밝혔다. PG 쪽 인덱스는 **카탈로그 조회로 실행 확인**했다.\
> **버전** — PG 의 SQL/JSON 경로 언어(`jsonpath`·`@?`·`@@`)는 **12 부터**, `JSON_TABLE` 은 **17 부터**(릴리스 노트 확인). MySQL 의 `JSON_TABLE` 은 **8.0.4 부터**, `JSON_VALUE` 는 **8.0.21 부터**(릴리스 노트 확인).\
> **선행** — [35 타입 체계와 캐스팅](../35-type-system-and-casting/). **이 주제는 그 편의 결론이 가장 크게 재현되는 자리다.**

## 한눈에 — 쉽게 말하면

**JSON 열은 「한 칸 안에 서류 한 장을 통째로 넣는 것」이다. 엔진은 그 서류를 읽어 주지만, 서류의 내용은 보증하지 않는다.**

```text
 보통의 열 (스키마가 있다)              JSON 열 (스키마가 없다)
+----------+--------+                  +----------------------------------+
| name     | salary |                  | doc                              |
+----------+--------+                  +----------------------------------+
| ann      |    300 |                  | {"name":"ann","salary":300}      |
| bob      | "삼백" |  <- 막힌다        | {"name":"bob","salary":"삼백"}   |  <- 안 막힌다
+----------+--------+                  +----------------------------------+
 타입·NOT NULL·외래키를 엔진이 지킨다    엔진은 "올바른 JSON 인가"만 본다
```

- **비유** — 서랍장과 상자다.\
  **서랍장**은 칸마다 이름표와 크기가 정해져 있다. 양말 칸에 신발을 못 넣는다.\
  **상자**는 뭐든 들어간다. 대신 **뭐가 들었는지는 열어 봐야** 알고, **잘못 든 것을 아무도 막아 주지 않는다.**
- **똑같은 구조다** — JSON 열에 `"salary": "삼백"` 을 넣어도 엔진은 통과시킨다.\
  문제는 그것을 **숫자로 쓰려는 날**에 터지고, ★ **PG 는 에러를 내고 MySQL 은 `0` 으로 읽고 경고만 남긴다.**\
  이것이 [35번](../35-type-system-and-casting/)이 찾은 두 엔진의 성격 차이 그대로다.

| 비유 | 실체 |
|---|---|
| 상자에 서류를 통째로 넣는다 | JSON 열 — PG `json`/`jsonb`, MySQL `JSON` |
| 넣을 때 "서류 형식인지"만 본다 | 유효한 JSON 텍스트인지만 검사한다 |
| 상자 안 쪽지를 꺼낸다 | `->`(꺼낸 것도 JSON) |
| 쪽지의 **글자만** 꺼낸다 | `->>`(따옴표를 벗겨 문자열로) |
| 서류를 복사해 정서한다 | PG `jsonb` · MySQL `JSON` — **키를 정렬하고 중복을 지운다** |
| 원본을 사진 찍어 둔다 | PG `json` — **텍스트 그대로** 보관 |
| 상자 안 내용으로 색인을 만든다 | PG GIN · MySQL 생성 열 인덱스 |
| 잘못 든 물건을 아무도 안 막는다 | 타입·`NOT NULL`·외래키가 **없다** |

> **JSON 열(JSON column)** — JSON 문서 한 장을 값으로 담는 열.\
> 예: `{"name":"ann","tags":["x","y"]}` 한 덩어리가 한 칸에 들어간다.

## 이 주제가 답하려는 질문

1. **`->` 와 `->>` 는 무엇이 다른가?** — 그리고 그 차이가 왜 사고를 만드나.
2. **두 엔진의 JSON 은 어디까지 같고 어디서 갈리나?** — 타입 이름·연산자·함수 이름·경로 문법.
3. **JSON 열에 인덱스를 걸 수 있나?** — 걸린다면 **어떤 연산자만** 그것을 타나.

## 예시 데이터 — 이 묶음이 공유하는 것

이 폴더의 SQL 주제들은 `emp`·`dept` 두 표를 쓴다. **그런데 두 표에는 JSON 열이 없다.**

**그래서 표를 만들지 않고 [32번](../32-cte-with-clause/)의 CTE 로 JSON 리터럴을 만든다.**

```sql
-- 이 주제의 예제 대부분이 이 한 줄을 머리에 달고 있다
WITH j AS (SELECT CAST('{"a":1,"boss":{"name":"ann"},"tags":["x","y"]}' AS jsonb) AS doc)
--                                                                        ^^^^^ MySQL 은 JSON
```

```text
 doc 한 장의 구조

 {
   "a"    : 1                     <- 스칼라 (숫자)
   "boss" : { "name": "ann" }     <- 중첩 객체   -> 경로가 두 칸 필요하다
   "tags" : [ "x", "y" ]          <- 배열        -> 첨자가 필요하다
 }
```

★ **절마다 문서가 미세하게 다르니 질의의 `WITH` 줄을 그대로 읽어라.** 위의 `j` 가 기본이지만,
**1번 절만 `tags` 가 3원소**(`["x","y","z"]`)이고, 정규화·타입 절은 그 절에만 쓰는 짧은 문서를 따로 만든다(`j2` 등).\
★ 실제로 **이 차이가 사고를 냈다** — 1번 절의 3원소 출력을 2번 절 이후의 2원소 블록에 옮겨 붙여
`len=3`·`x/y/z` 로 적힌 곳이 네 군데 있었고, 출력 재검증에서 잡혔다.
**「같은 이름이니 같은 값이겠지」가 정확히 옮겨 적기 사고의 모양이다.**

**왜 이 데이터가 이 주제에 맞나.**

- **스칼라·중첩 객체·배열 셋이 한 문서에 다 있다.** 이 주제의 연산자는 전부 "**무엇을 꺼내나**"로 갈리므로, 세 종류가 다 있어야 **경로 문법의 차이**(`'{boss,name}'` 대 `'$.boss.name'`)와 **첨자 문법의 차이**가 한 문서에서 전부 드러난다.
- **`"ann"` 이라는 값이 `emp` 의 `ann` 과 같다.** 그래서 **JSON 에서 꺼낸 값과 열에서 읽은 값을 나란히 놓고 타입을 비교**할 수 있다 — `->` 가 내는 `"ann"` 과 `->>` 가 내는 `ann` 의 차이가 그것이다.
- **문서가 4줄짜리로 작다.** 이 주제의 출력은 문서 자체가 그대로 찍히는 경우가 많아, 길면 **키 정렬·중복 제거**(1번 절) 같은 미세한 변화가 안 보인다.
- **표를 만들지 않으므로** 다른 주제의 `emp`·`dept` 가 한 글자도 바뀌지 않는다.\
  ★ **대가는 인덱스다** — 실제 표가 없으니 **MySQL 쪽 인덱스 생성을 실행으로 확인하지 못했다**(10번 절에 그렇게 적었다).
- 집계로 JSON 을 **만드는** 예제(9번 절)에서는 `emp`·`dept` 의 실제 행을 쓴다.

## 동작 방식

### 1. 타입 — **MySQL 의 `JSON` 은 PG 의 `jsonb` 에 해당한다**

**언제 쓰나** — 열 타입을 고를 때. PG 에는 선택지가 둘이고 MySQL 에는 하나다.

```text
 PG json        원문 텍스트를 그대로 저장. 읽을 때마다 파싱한다
 PG jsonb       파싱해서 이진 구조로 저장. 키를 정렬하고 중복 키를 지운다
 MySQL JSON     파싱해서 이진 구조로 저장.  = jsonb 쪽이다. json 쪽에 해당하는 타입이 없다
```

같은 문자열을 셋에 넣어 본다. **키 순서가 뒤섞이고 중복 키(`"a"` 가 둘)가 든 것을 일부러 넣었다.**

```text
### SQL: SELECT CAST('{"b":2,"a":1,"a":9,"tags":["x","y","z"],"boss":{"name":"ann","id":1}}' AS <타입>);
--- PG 18.6 · jsonb ---
 {"a": 9, "b": 2, "boss": {"id": 1, "name": "ann"}, "tags": ["x", "y", "z"]}
--- PG 18.6 · json ---
 {"b":2,"a":1,"a":9,"tags":["x","y","z"],"boss":{"name":"ann","id":1}}
--- MySQL 8.4.10 · JSON ---
+-----------------------------------------------------------------------------+
| doc                                                                         |
+-----------------------------------------------------------------------------+
| {"a": 9, "b": 2, "boss": {"id": 1, "name": "ann"}, "tags": ["x", "y", "z"]} |
+-----------------------------------------------------------------------------+
```

그림 해설 — **PG `jsonb` 와 MySQL `JSON` 의 출력이 한 글자도 다르지 않다.**\
둘 다 키를 정렬하고(`a, b, boss, tags`), **중복 키 `"a":1` 을 버리고 마지막 `"a":9` 만 남겼으며**, 공백을 정규화했다.\
PG `json` 만 **입력 텍스트를 글자 그대로** 보관했다.

정렬 기준까지 같다 — **길이 먼저, 그다음 바이트순**이다.

```text
### SQL: SELECT CAST('{"b":1,"aa":2}' AS <타입>);
--- PG 18.6 · jsonb ---          --- MySQL 8.4.10 · JSON ---
 {"b": 1, "aa": 2}               +-------------------+
                                 | {"b": 1, "aa": 2} |
                                 +-------------------+
```

`b` 가 `aa` 보다 앞이다 — 사전순이면 `aa` 가 앞이어야 한다. **길이가 먼저다.**

비용 — `jsonb`/`JSON` 은 **넣을 때 비용을 치르고 꺼낼 때 싸다.** `json` 은 반대다.\
★ **`json` 은 인덱스를 못 건다**(10번 절). 실무에서 PG 를 쓰면 **거의 항상 `jsonb`** 다.

> **정규화(normalization)** — 같은 뜻의 여러 표기를 하나의 표준 표기로 바꾸는 것.\
> 예: `{"b":2,"a":1}` 과 `{ "a":1, "b":2 }` 가 둘 다 `{"a": 1, "b": 2}` 로 저장되는 것.

---

### 2. ★ `->` 와 `->>` — **반환 타입이 다르다**

**언제 쓰나** — 값을 꺼낼 때마다. **이 주제에서 가장 자주 틀리는 자리다.**

```text
 doc -> 'boss' -> 'name'          doc -> 'boss' ->> 'name'
        ↓                                ↓
      "ann"                              ann
   (JSON 문자열 — 따옴표가 있다)      (SQL 문자열 — 따옴표가 없다)
   -> 계속 파고들 수 있다             -> 더는 못 판다. 대신 SQL 함수에 넘길 수 있다
```

```text
### SQL: WITH j AS (SELECT CAST('{"a":1,"boss":{"name":"ann"},"tags":["x","y"]}' AS jsonb) AS doc)
         SELECT doc -> 'boss' AS arrow, pg_typeof(doc -> 'boss') AS arrow_type,
                doc ->> 'boss' AS darrow, pg_typeof(doc ->> 'boss') AS darrow_type FROM j;
--- PG 18.6 ---
      arrow      | arrow_type |     darrow      | darrow_type 
-----------------+------------+-----------------+-------------
 {"name": "ann"} | jsonb      | {"name": "ann"} | text
(1 row)
```

★ **보이는 글자는 똑같은데 타입이 다르다.** `pg_typeof` 없이는 구분이 안 된다 — 그래서 사고가 난다.

문자열 값에서는 **눈에도 보인다.**

```text
### SQL: SELECT doc -> 'boss' -> 'name' AS a, doc -> 'boss' ->> 'name' AS b FROM j;
--- PG 18.6 ---                  --- MySQL 8.4.10 (doc -> '$.boss.name' / ->>) ---
   a   |  b                      +-------+------+
-------+-----                    | a     | b    |
 "ann" | ann                     +-------+------+
(1 row)                          | "ann" | ann  |
                                 +-------+------+
```

**MySQL 쪽도 같은 규칙이다.** 매뉴얼상 `->>` 는 `JSON_UNQUOTE(JSON_EXTRACT(...))` 의 줄임이고, 실제로 셋이 같은 값을 낸다.

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

**MySQL 에서 타입을 어떻게 확인하나** — `JSON_TYPE()` 에 넣어 보면 된다. **JSON 이 아니면 거부한다.**

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

그림 해설 — **`ann` 은 유효한 JSON 텍스트가 아니다**(따옴표가 없으니까). 그래서 `JSON_TYPE` 이 거부했다.\
★ **이 에러가 곧 "`->>` 는 JSON 이 아니라 평범한 문자열을 돌려준다"의 증거다.**\
비용 — **문자열 비교·`LIKE`·조인 키로 쓸 값은 반드시 `->>`** 로 꺼낸다. `->` 로 꺼내면 따옴표가 붙어 다닌다.

---

### 3. 배열 — 첨자와 길이

**언제 쓰나** — JSON 배열에서 원소를 꺼내거나 행으로 펼 때.

```text
 PG                                  MySQL
 doc -> 'tags' -> 0     첫째 (JSON)  doc -> '$.tags[0]'      첫째 (JSON)
 doc -> 'tags' ->> 0    첫째 (text)  doc ->> '$.tags[0]'     첫째 (문자열)
 doc -> 'tags' -> -1    마지막       doc ->> '$.tags[last]'  마지막
 jsonb_array_length(...)  길이       JSON_LENGTH(doc,'$.tags')  길이
```

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

그림 해설 — **마지막 원소를 가리키는 법이 다르다.** PG 는 **음수 첨자 `-1`**, MySQL 은 **`last` 라는 낱말**이다.

**배열을 행으로 펴는 것**은 도구가 다르다.

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
```

**그리고 `JSON_TABLE` 은 두 엔진에 다 있다** — 이 주제에서 드문 공통 지대다.

```text
### SQL: (PG 18.6) SELECT t.* FROM j, JSON_TABLE(doc, '$.tags[*]' COLUMNS (ord FOR ORDINALITY, val text PATH '$')) AS t;
--- PG 18.6 ---
 ord | val 
-----+-----
   1 | x
   2 | y
(2 rows)
```

비용 — **PG 의 `JSON_TABLE` 은 17 부터**이고 **MySQL 은 8.0.4 부터**다(릴리스 노트).\
이식이 필요하면 `JSON_TABLE` 이 현재 가장 공통에 가깝고, PG 16 이하를 지원해야 하면 `jsonb_array_elements` 쪽을 쓴다.\
`LATERAL` 이 왜 필요한지는 [20번](../20-lateral-join/)이 정본이다.

---

### 4. 경로 문법 — **PG 는 두 벌, MySQL 은 한 벌**

**언제 쓰나** — 중첩된 값을 한 번에 꺼낼 때.

```text
 PG 의 "경로 배열"            PG 의 "SQL/JSON 경로"(12+)    MySQL 의 경로
 doc #>  '{boss,name}'        jsonb_path_query(doc,'$.boss.name')   doc -> '$.boss.name'
 doc #>> '{boss,name}'        doc @? '$.tags[*] ? (@ == "y")'       JSON_EXTRACT(doc,'$.boss.name')
 (배열 리터럴로 칸을 나열)     (MySQL 과 비슷한 $.a.b 모양)          ($.a.b 한 가지뿐)
```

```text
### SQL: (PG) SELECT doc #> '{boss,name}' AS path_json, doc #>> '{boss,name}' AS path_text,
                     doc #>> '{tags,1}' AS t1 FROM j;
--- PG 18.6 ---
 path_json | path_text | t1 
-----------+-----------+----
 "ann"     | ann       | y
(1 row)
```

그림 해설 — `#>` 와 `#>>` 의 관계는 `->` 와 `->>` 와 **같다** — 두 번째 `>` 가 "따옴표를 벗긴다"는 뜻이다.\
배열 첨자도 같은 자리에 숫자로 쓴다(`{tags,1}`).

**PG 는 `$.a.b` 모양도 알아듣는다 — 단 `jsonpath` 자리에서만.**

```text
### SQL: (PG) SELECT jsonb_path_query_first(doc, '$.tags[1]') AS pathq,
                     doc @? '$.tags[*] ? (@ == "y")' AS pathtest FROM j;
--- PG 18.6 ---
 pathq | pathtest 
-------+----------
 "y"   | t
(1 row)
```

★ **그런데 같은 문자열을 `->` 에 주면 조용히 실패한다** — 6번 절이 그 사고다.

비용 — PG 의 SQL/JSON 경로 언어는 **12 부터**다.

> "Add support for the SQL/JSON path language (…) This allows execution of complex queries on `JSON` values using an SQL-standard language."\
> — [PostgreSQL 12 릴리스 노트](https://www.postgresql.org/docs/release/12.0/)

---

### 5. 함수 이름 — **같은 일을 하는데 이름이 전부 다르다**

**언제 쓰나** — 한쪽에서 쓰던 질의를 다른 쪽으로 옮길 때.

| 하는 일 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 키로 꺼내기(JSON) | `doc -> 'a'` | `doc -> '$.a'` |
| 키로 꺼내기(문자열) | `doc ->> 'a'` | `doc ->> '$.a'` |
| 경로로 꺼내기 | `doc #> '{a,b}'` · `jsonb_extract_path(doc,'a','b')` | `JSON_EXTRACT(doc,'$.a.b')` |
| 따옴표 벗기기 | `#>>` · `jsonb_extract_path_text` | `JSON_UNQUOTE(...)` · `JSON_VALUE(...)` |
| 값의 종류 | `jsonb_typeof(...)` → `number`·`string`·`array` | `JSON_TYPE(...)` → `INTEGER`·`STRING`·`ARRAY` |
| 포함 여부 | `doc @> '{"a":1}'` | `JSON_CONTAINS(doc,'1','$.a')` |
| 키 존재 여부 | `doc ? 'tags'` | `JSON_CONTAINS_PATH(doc,'one','$.tags')` |
| 길이 | `jsonb_array_length(...)` | `JSON_LENGTH(doc,'$.tags')` |
| 값 찾기 | `jsonb_path_query(...)` | `JSON_SEARCH(doc,'one','y')` |
| 키 지우기 | `doc - 'a'` | `JSON_REMOVE(doc,'$.a')` |
| 합치기 | `doc \|\| '{"c":3}'` | `JSON_MERGE_PATCH(doc,'{"c":3}')` |
| 값 바꾸기 | `jsonb_set(doc,'{a}','9')` | `JSON_SET(doc,'$.a',9)` |
| 만들기 | `jsonb_build_object(...)` · `jsonb_agg(...)` | `JSON_OBJECT(...)` · `JSON_ARRAYAGG(...)` |

```text
### SQL: (PG) SELECT doc @> '{"a":1}' AS contains, doc ? 'tags' AS has_key, doc ? 'nope' AS has_nope,
                     jsonb_typeof(doc -> 'a') AS t_a, jsonb_typeof(doc -> 'tags') AS t_tags FROM j;
--- PG 18.6 ---
 contains | has_key | has_nope |  t_a   | t_tags 
----------+---------+----------+--------+--------
 t        | t       | f        | number | array
(1 row)

### SQL: (MySQL) SELECT JSON_CONTAINS(doc,'1','$.a') AS contains, JSON_CONTAINS_PATH(doc,'one','$.tags') AS has_key,
                        JSON_CONTAINS_PATH(doc,'one','$.nope') AS has_nope,
                        JSON_TYPE(doc->'$.a') AS t_a, JSON_TYPE(doc->'$.tags') AS t_tags,
                        JSON_SEARCH(doc,'one','y') AS found FROM j;
--- MySQL 8.4.10 ---
+----------+---------+----------+---------+--------+-------------+
| contains | has_key | has_nope | t_a     | t_tags | found       |
+----------+---------+----------+---------+--------+-------------+
|        1 |       1 |        0 | INTEGER | ARRAY  | "$.tags[1]" |
+----------+---------+----------+---------+--------+-------------+
```

그림 해설 — **값의 종류 이름조차 다르다.** PG 는 `number`(소문자, 정수/실수 구분 없음), MySQL 은 `INTEGER`(대문자, 구분 있음).\
★ **`JSON_SEARCH` 는 값이 아니라 「경로」를 돌려준다** — `"$.tags[1]"`. PG 에 대응물이 마땅치 않다.\
비용 — **이식은 문자열 치환으로 안 된다.** 연산자·함수·경로 문법이 전부 갈리므로 **질의를 다시 쓴다.**

**고치는 함수들은 결과가 같다.**

```text
### SQL: (PG) WITH j2 AS (SELECT CAST('{"a":1,"b":2}' AS jsonb) AS doc)
             SELECT doc - 'a' AS removed, doc || '{"c":3}' AS merged, jsonb_set(doc,'{a}','9') AS setted FROM j2;
--- PG 18.6 ---
 removed  |          merged          |      setted      
----------+--------------------------+------------------
 {"b": 2} | {"a": 1, "b": 2, "c": 3} | {"a": 9, "b": 2}
(1 row)

### SQL: (MySQL) WITH j2 AS (SELECT CAST('{"a":1,"b":2}' AS JSON) AS doc)
                 SELECT JSON_REMOVE(doc,'$.a') AS removed, JSON_MERGE_PATCH(doc,'{"c":3}') AS merged,
                        JSON_SET(doc,'$.a',9) AS setted FROM j2;
--- MySQL 8.4.10 ---
+----------+--------------------------+------------------+
| removed  | merged                   | setted           |
+----------+--------------------------+------------------+
| {"b": 2} | {"a": 1, "b": 2, "c": 3} | {"a": 9, "b": 2} |
+----------+--------------------------+------------------+
```

**세 결과가 한 글자도 안 다르다.** 갈리는 것은 **이름뿐**이다.

---

### 6. ★ 서로의 문법을 던져 보면 — **한쪽만 조용히 실패한다**

**언제 쓰나** — 절대 일부러 쓰지 않는다. **이식할 때 사고로 일어난다.**

```text
### SQL: (PG 에 MySQL 식 경로) WITH j AS (SELECT CAST('{"a":1}' AS jsonb) AS doc)
         SELECT doc -> 'a' AS ok, doc -> '$.a' AS mysql_style, (doc -> '$.a') IS NULL AS is_null FROM j;
--- PG 18.6 ---
 ok | mysql_style | is_null 
----+-------------+---------
 1  |             | t
(1 row)

### SQL: (MySQL 에 PG 식 키) WITH j AS (SELECT CAST('{"a":1}' AS JSON) AS doc) SELECT doc -> 'a' FROM j;
--- MySQL 8.4.10 ---
ERROR 3143 (42000) at line 1: Invalid JSON path expression. The error is around character position 1.
```

```text
 PG 에 '$.a' 를 주면                     MySQL 에 'a' 를 주면
 "$.a" 라는 이름의 키를 찾는다            경로 표현으로 파싱하려다 실패한다
   -> 그런 키가 없다                        -> ERROR 3143
   -> NULL     ★ 에러가 아니다              -> 곧바로 안다
```

★ **PG 쪽이 위험하다.** `->` 의 오른쪽은 **경로가 아니라 키 이름**이므로, `'$.a'` 는 그냥 **없는 키**다.\
에러도 경고도 없이 **`NULL` 이 나오고, 그 `NULL` 이 바깥 조건을 전부 `UNKNOWN` 으로 만든다**([04번](../04-null-three-valued-logic/)).

나머지 연산자·함수도 서로 거부한다.

```text
### SQL: (PG 에 MySQL 함수) SELECT JSON_EXTRACT(doc, '$.a') FROM j;
--- PG 18.6 ---
ERROR:  function json_extract(jsonb, unknown) does not exist
LINE 1: ...S (SELECT CAST('{"a":1}' AS jsonb) AS doc) SELECT JSON_EXTRA...
                                                             ^
HINT:  No function matches the given name and argument types. You might need to add explicit type casts.

### SQL: (MySQL 에 PG 함수) SELECT jsonb_extract_path_text(doc, 'boss', 'name') FROM j;
--- MySQL 8.4.10 ---
ERROR 1305 (42000) at line 1: FUNCTION study.jsonb_extract_path_text does not exist

### SQL: (MySQL 에 PG 연산자) SELECT doc @> '{"a":1}' FROM j;   /   SELECT doc ? 'a' FROM j;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: ... near '@> '{"a":1}' FROM j' at line 1
ERROR 1064 (42000) at line 1: ... near '? 'a' FROM j' at line 1
```

★ **그리고 `#>` 에는 더 고약한 함정이 있다.**

```text
### SQL: (MySQL 에 PG 의 #>) SELECT doc #> '{boss,name}' FROM j;
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'doc' in 'field list'
```

"모르는 열 `doc`"? 문서에는 `doc` 이 분명히 있다. **`#` 이 MySQL 에서 주석 시작이기 때문이다.**

```text
### SQL: SELECT 1 #> 2;               ### SQL: SELECT 1 AS a #> 2;
--- MySQL 8.4.10 ---                  --- MySQL 8.4.10 ---
+---+                                 +---+
| 1 |                                 | a |
+---+                                 +---+
| 1 |                                 | 1 |
+---+                                 +---+
```

`#` 뒤가 통째로 사라졌다. 그래서 `doc #> '{boss,name}'` 은 **`doc` 만 남고**, 별칭 없는 그 `doc` 이 "모르는 열"이 된 것이다.\
비용 — **에러 메시지가 원인을 가리키지 않는 드문 경우다.** MySQL 에서 `#` 을 만나면 **주석을 먼저 의심한다.**

---

### 7. **없는 키는 조용히 `NULL`** 이다

**언제 쓰나** — 키 이름을 오타 냈을 때. **엔진은 오타인지 "값이 없는 것"인지 구분할 수 없다.**

```text
### SQL: (PG) WITH j AS (SELECT CAST('{"salary":"삼백","dept_id":10}' AS jsonb) AS doc)
              SELECT doc ->> 'salary' AS kept, doc ->> 'salery' AS typo, jsonb_typeof(doc->'salary') AS t FROM j;
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

그림 해설 — **`salery` 라는 오타가 `NULL` 이 됐다.** 두 엔진 다 조용하다.

```text
 열 이름을 오타 내면                 JSON 키를 오타 내면
 SELECT salery FROM emp              doc ->> 'salery'
   -> ERROR: column does not exist     -> NULL
   -> 즉시 안다                        -> 통계가 비고 나서야 안다  ★
```

★ **스키마가 있는 열에서는 오타가 에러이고, JSON 키에서는 `NULL` 이다.** 이것이 10번 절의 "JSON 을 쓰면 안 되는 자리" 논거의 절반이다.\
비용 — JSON 키를 다루는 코드에는 **`JSON_CONTAINS_PATH` / `?` 로 존재 여부를 따로 확인**하는 방어선이 필요하다.

---

### 8. ★ 타입 보증이 없다 — **그리고 두 엔진이 다르게 망가진다**

**언제 쓰나** — JSON 안의 값을 숫자로 계산할 때.

문서에 `"salary": "삼백"` 이 들어 있다. **넣을 때는 두 엔진 다 아무 말도 안 했다**(위 7번 절의 `t` 가 `string`/`STRING`).

```text
### SQL: (PG) WITH j AS (SELECT CAST('{"salary":"삼백"}' AS jsonb) AS doc)
              SELECT (doc ->> 'salary')::int + 1 AS boom FROM j;
--- PG 18.6 ---
ERROR:  invalid input syntax for type integer: "삼백"

### SQL: (MySQL) WITH j AS (SELECT CAST('{"salary":"삼백"}' AS JSON) AS doc)
                 SELECT CAST(doc ->> '$.salary' AS SIGNED) + 1 AS boom FROM j;
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

그림 해설 — ★ **MySQL 은 `1` 을 돌려줬다.** `'삼백'` 을 `0` 으로 읽고 `0 + 1 = 1` 이다.\
**에러가 아니라 경고**이고, **`SHOW WARNINGS` 를 따로 물어야 보인다.** 애플리케이션은 대개 안 묻는다.

★ **이것이 [35번](../35-type-system-and-casting/)의 한 줄이 그대로 재현된 것이다** — **"PG 는 못 읽으면 문을 죽이고, MySQL 은 읽을 수 있는 데까지 읽고 경고만 남긴다."**\
JSON 은 **그 성격 차이가 가장 위험하게 드러나는 자리**다. 스키마가 막아 주지 않으니 **잘못된 타입이 처음부터 들어와 있기 때문**이다.

**JSON 문법 자체는 두 엔진 다 막는다.**

```text
### SQL: SELECT CAST('{"a":1,}' AS jsonb);   /   SELECT CAST('{"a":1,}' AS JSON);
--- PG 18.6 ---
ERROR:  invalid input syntax for type json
LINE 1: SELECT CAST('{"a":1,}' AS jsonb);
                    ^
DETAIL:  Expected string, but found "}".
CONTEXT:  JSON data, line 1: {"a":1,}
--- MySQL 8.4.10 ---
ERROR 3141 (22032) at line 1: Invalid JSON text in argument 1 to function cast_as_json: "Missing a name for object member." at position 7.
```

비용 — **엔진이 보증하는 것은 딱 여기까지다** — "올바른 JSON 텍스트인가". **값의 타입은 보증하지 않는다.**

---

### 9. JSON 을 **만드는** 쪽 — 여기는 오히려 편하다

**언제 쓰나** — 관계형 결과를 API 응답 모양으로 내보낼 때.

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

그림 해설 — **결과가 한 글자도 다르지 않다.** 이름만 `jsonb_build_object`/`jsonb_agg` 와 `JSON_OBJECT`/`JSON_ARRAYAGG` 로 갈린다.\
`hr` 부서가 없는 것은 내부 조인이라 그렇다([13번](../13-inner-join/)).\
★ **PG 쪽은 `jsonb_agg(… ORDER BY e.id)` 로 배열 순서를 지정했다.** MySQL 의 `JSON_ARRAYAGG` 에는 그 문법이 없어 **배열 안 순서가 보장되지 않는다.**\
비용 — **저장은 관계형으로, 출력만 JSON 으로** — 이것이 이 주제에서 가장 안전한 사용법이다.

---

### 10. 인덱스 — **`jsonb` 에는 걸리고 `json` 에는 안 걸린다**

**언제 쓰나** — JSON 안의 값으로 자주 검색할 때. **여기가 JSON 설계의 갈림길이다.**

**PG 에서 어떤 인덱스가 `jsonb` 를 지원하는지는 카탈로그가 답한다.**

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

그림 해설 — ★ **`json` 타입에는 연산자 클래스가 하나도 없다. 인덱스를 못 건다.**\
`jsonb` 에는 btree·hash·gin 셋이 있고, **GIN 이 둘**(`jsonb_ops` 기본 · `jsonb_path_ops`)이다.

**그런데 GIN 이 모든 연산자를 받아 주는 것이 아니다.** 어느 연산자를 타는지도 카탈로그에 있다.

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

★ **목록에 `->` 도 `->>` 도 `#>` 도 없다.**

```text
 GIN 인덱스가 타는 것          GIN 인덱스가 못 타는 것
 doc @> '{"a":1}'   포함       doc ->> 'a' = '1'      값 비교
 doc ? 'a'          키 존재    doc -> 'a' > '5'
 doc @? '$.a'       경로       doc ->> 'name' LIKE 'a%'
        ↓                              ↓
 "문서 안에 이게 있나"를 묻는다  "이 칸의 값이 얼마인가"를 묻는다
 -> 역색인이 답할 수 있다        -> 표현식 인덱스를 따로 만들어야 한다
```

**값 비교로 인덱스를 타려면 표현식 인덱스를 따로 만든다** — `CREATE INDEX … ((doc->>'name'))`.\
그것은 [46번 주제](../46-index-definition-composite-partial-expression/)(인덱스 정의)와 [목록의 **47번 주제**](../47-when-indexes-are-used/)(언제 타나)가 정본이다.

**MySQL 쪽.** ★ **이 한 자리만 실행으로 확인하지 못했다** — 이 작업이 **표 생성 금지**라 `CREATE TABLE`/`ALTER TABLE` 을 던질 수 없었다. **아래는 매뉴얼 인용이다.**

> "Functional key parts enable indexing of values that cannot be indexed otherwise, such as `JSON` values. However, this must be done correctly to achieve the desired effect."\
> "A multi-valued index is a secondary index defined on a column that stores an array of values… Multi-valued indexes are intended for indexing `JSON` arrays."\
> — [MySQL 8.4 · CREATE INDEX](https://dev.mysql.com/doc/refman/8.4/en/create-index.html)

같은 페이지가 **`CAST` 를 쓰라**고 적는다 — `INDEX ((data->>'$.name'))` 이 아니라 `INDEX ((CAST(data->>'$.name' AS CHAR(30))))` 다.\
그리고 8.0.21 릴리스 노트가 `JSON_VALUE()` 를 **"simplifies creating indexes on `JSON` columns"** 라고 소개한다.

**인덱스에 쓰는 「표현식」 자체는 돌려 봤다** — 값이 제대로 나오는 것까지가 실행 확인의 범위다.

```text
### SQL: (MySQL) SELECT CAST(JSON_EXTRACT(CAST('{"a":1}' AS JSON), '$.a') AS UNSIGNED) AS casted;
                        SELECT JSON_VALUE(CAST('{"a":1}' AS JSON), '$.a' RETURNING UNSIGNED) AS returning_typed;
--- MySQL 8.4.10 ---
+--------+                       +-----------------+
| casted |                       | returning_typed |
+--------+                       +-----------------+
|      1 |                       |               1 |
+--------+                       +-----------------+
```

비용 — **두 엔진의 전략이 다르다.**

```text
 PostgreSQL                          MySQL
 jsonb + GIN                         생성 열(또는 함수 키) + 보통 인덱스
 -> 문서 통째로 역색인                -> 미리 정한 키 하나만 색인
 -> 어떤 키로 찾을지 몰라도 된다      -> 키마다 인덱스를 따로 만들어야 한다
 -> 인덱스가 크다                     -> 인덱스가 작다
 (배열은 jsonb_path_ops 가 더 작다)   (배열은 multi-valued index)
```

---

### 11. ★ JSON 을 쓰면 **안 되는** 자리

**언제 쓰나** — 설계할 때. **이 절이 이 주제에서 가장 값비싼 절이다.**

```text
 스키마가 있는 것을 JSON 에 넣으면 잃는 것

 열로 뒀을 때                        JSON 안에 뒀을 때
 +-------------------------------+   +-------------------------------+
 | 타입    : salary int          |   | 아무 타입이나 들어간다 (8번)  |
 | 필수    : NOT NULL            |   | 없으면 그냥 NULL (7번)        |
 | 참조    : FK -> dept(id)      |   | 없는 부서를 가리켜도 통과     |
 | 오타    : ERROR column ...    |   | NULL — 조용하다 (7번)         |
 | 인덱스  : 아무 열이나 바로     |   | GIN 은 포함만 · 값 비교는 별도 |
 | 변경    : ALTER TABLE 로 추적  |   | 코드 안에만 있다              |
 +-------------------------------+   +-------------------------------+
```

- **X 질의 조건·조인 키로 자주 쓰는 값** — `dept_id`·`status`·`created_at` 같은 것. 인덱스와 제약이 붙어야 한다.
- **X 타입이 정해진 수치** — 금액·수량. 8번 절에서 MySQL 이 `1` 을 돌려준 그 사고가 언제든 난다.
- **X 다른 표를 가리키는 값** — 외래키를 못 건다. 참조 무결성은 [44번 주제](../44-foreign-key-referential-actions/)다.
- **X 집계·정렬의 대상** — 매번 꺼내 캐스팅해야 하고 인덱스를 못 탄다.
- **O 스키마가 정말 없는 것** — 외부 API 원문, 웹훅 페이로드, 감사 로그의 "그때 상태".
- **O 희소한 속성** — 상품 종류마다 다른 속성처럼, 열로 만들면 대부분 `NULL` 인 것.
- **O 읽기 전용 스냅샷** — 주문 시점의 배송지처럼 **더는 안 바뀌는** 덩어리.
- **O 출력 모양** — 저장은 관계형으로, **응답만 JSON 으로**(9번 절).

판정은 한 줄로 된다.

> **"이 값으로 `WHERE` 하거나 `JOIN` 하거나 `SUM` 할 일이 있나?" — 있으면 열로 뺀다.**

**타협안** — JSON 에 그대로 두되 **자주 쓰는 키만 뽑아 열로 승격**한다. PG 는 생성 열이나 표현식 인덱스로, MySQL 은 생성 열로.\
그러면 원문은 남고 질의는 인덱스를 탄다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
-- PostgreSQL
CAST('{"a":1}' AS jsonb)     -- 또는 '{"a":1}'::jsonb
doc -> 'a'        doc -> 0        -- JSON 을 돌려준다 (키 이름 / 배열 첨자)
doc ->> 'a'       doc ->> 0       -- text 를 돌려준다
doc #> '{a,b}'    doc #>> '{a,b}' -- 경로 배열
doc['a']                          -- 첨자 문법 (14+)
doc @> '{"a":1}'  doc ? 'a'       -- 포함 · 키 존재   (GIN 이 탄다)
doc @? '$.a'      doc @@ '$.a > 1'-- SQL/JSON 경로    (GIN 이 탄다, 12+)
jsonb_typeof · jsonb_array_length · jsonb_array_elements(_text) · jsonb_set · jsonb_build_object · jsonb_agg

-- MySQL
CAST('{"a":1}' AS JSON)
doc -> '$.a'      doc -> '$.t[0]'   -- JSON_EXTRACT 의 줄임
doc ->> '$.a'                       -- JSON_UNQUOTE(JSON_EXTRACT(...)) 의 줄임
JSON_EXTRACT · JSON_UNQUOTE · JSON_VALUE(… RETURNING 타입)
JSON_TYPE · JSON_LENGTH · JSON_CONTAINS · JSON_CONTAINS_PATH · JSON_SEARCH
JSON_SET · JSON_REMOVE · JSON_MERGE_PATCH · JSON_OBJECT · JSON_ARRAYAGG · JSON_TABLE
```

금지 사례 — **서로에게 던지면 안 되는 것들**(6번 절).

```sql
-- PG 에서: 경로 문자열을 -> 에 준다   -> 에러가 아니라 NULL  ★ 가장 위험
doc -> '$.a'
-- MySQL 에서: 키 이름만 준다          -> ERROR 3143
doc -> 'a'
-- MySQL 에서: PG 연산자              -> ERROR 1064 (@> · ?)
doc @> '{"a":1}'
-- MySQL 에서: #> 는 주석이 된다       -> ERROR 1054 Unknown column 'doc'
doc #> '{a,b}'
-- PG 에서: MySQL 함수                -> function json_extract(jsonb, unknown) does not exist
JSON_EXTRACT(doc, '$.a')
```

규칙 여덟.

1. **MySQL 의 `JSON` 은 PG 의 `jsonb` 다.** PG 의 `json`(원문 보존)에 해당하는 타입이 MySQL 에는 없다.
2. **`jsonb`/`JSON` 은 키를 정렬하고 중복 키를 지운다** — 길이 먼저, 그다음 바이트순.
3. **`->` 는 JSON 을, `->>` 는 문자열을 돌려준다.** 보이는 글자가 같아도 타입이 다르다.
4. **경로 문법이 다르다** — PG 는 키 이름·`#>` 경로 배열·`jsonpath`, MySQL 은 `$.a.b` 한 가지.
5. **없는 키는 두 엔진 다 조용히 `NULL`** 이다. 오타가 에러가 아니다.
6. **타입 보증이 없다.** 틀린 타입에 PG 는 에러, **MySQL 은 `0` + 경고**다.
7. **`json` 은 인덱스를 못 건다.** `jsonb` 는 GIN 이 되지만 **`@>`·`?`·`@?`·`@@` 계열만** 탄다.
8. **`WHERE`/`JOIN`/`SUM` 할 값이면 열로 뺀다.**

읽을 때 붙잡을 것은 **"이 값은 스키마가 있나 없나"** 하나다.

```text
 값에 스키마가 있나?
   ├─ 있다 (타입·필수·참조가 정해져 있다)   -> 열로 뺀다. JSON 에 두면 전부 잃는다
   └─ 없다 (형태를 모르거나 희소하다)       -> JSON. 대신 꺼낼 때마다 NULL·타입을 방어한다
```

## 어디서 틀리나

- ★ **PG 에 MySQL 식 경로를 준다.** `doc -> '$.a'` 가 **에러가 아니라 `NULL`** 이다. 이식 중 가장 조용한 사고다.
- **MySQL 에서 `#>` 를 쓴다.** `#` 이 주석이라 `Unknown column 'doc'` 이라는 **엉뚱한 에러**가 난다.
- **`->` 와 `->>` 를 섞어 쓴다.**\
  `doc -> 'name' = 'ann'` 은 `"ann" = 'ann'` 이라 안 맞는다. **비교·조인에는 `->>`** 다.
- **없는 키의 `NULL` 을 "값이 없다"로만 읽는다.** **오타일 수도 있다.** 존재 여부를 따로 확인한다(`?` / `JSON_CONTAINS_PATH`).
- **MySQL 에서 JSON 값을 숫자로 계산한다.** `'삼백'` 이 `0` 이 되고 **경고만** 남는다. `SHOW WARNINGS` 를 안 보면 모른다.
- **PG 에서 `json` 을 고른다.** 인덱스를 못 건다(연산자 클래스 0개). 이유가 없으면 **`jsonb`** 다.
- **GIN 을 걸어 놓고 `->>` 로 검색한다.** GIN 이 타는 연산자 목록에 `->>` 가 **없다.** 값 비교는 표현식 인덱스다.
- **`jsonb` 의 키 순서를 믿는다.** 넣은 순서가 아니라 **정렬된 순서**로 나온다. 순서에 의미를 담지 마라.
- **중복 키를 넣고 앞의 것이 남을 거라 기대한다.** **마지막 것이 남는다**(`"a":1,"a":9` → `9`).
- **MySQL 의 `JSON_ARRAYAGG` 순서를 믿는다.** `ORDER BY` 를 받는 문법이 없다. PG 의 `jsonb_agg(… ORDER BY …)` 와 다르다.
- **스키마가 있는 것을 JSON 에 넣는다.** 타입·필수·외래키·오타 검출·인덱스를 **한꺼번에** 잃는다.

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| 유효하지 않은 JSON 텍스트를 거부하는 것 | **타입의 정의** | 언어 — 두 엔진 같다 |
| `->` 가 JSON 을, `->>` 가 문자열을 내는 것 | **연산자의 정의** | 언어 — 두 엔진 같다 |
| 없는 키가 `NULL` 인 것 | **연산자의 정의** | 언어 — 두 엔진 같다 |
| 중복 키에서 **마지막 것**이 남는 것 | 그 타입의 정규화 규칙 | PG `jsonb`·MySQL `JSON` — **PG `json` 은 둘 다 보존한다** |
| **키가 정렬되는 것** | 그 타입의 저장 방식 | PG `jsonb`·MySQL `JSON` — **저장 형식의 귀결**이지 JSON 의 성질이 아니다 |
| **정렬 기준이 「길이 먼저」인 것** | 그 엔진의 구현 | 두 엔진이 **같았다.** 관찰이지 보장이 아니다 |
| **타입이 안 맞을 때의 처리** | **엔진의 정책** | 갈린다 — PG 는 에러, MySQL 은 `0` + 경고 1292 |
| `jsonb_typeof` 가 `number`, `JSON_TYPE` 이 `INTEGER` | **그 엔진의 표기** | 각 엔진 |
| `json` 에 인덱스를 못 거는 것 | **PG 의 구현** | PG — 카탈로그에 연산자 클래스가 0개다 |
| GIN 이 타는 연산자 6개 | **PG 의 연산자 클래스 정의** | PG — `pg_amop` 가 정본이다 |
| MySQL 의 함수 키·다중값 인덱스 | **MySQL 의 문법** | MySQL 매뉴얼. ★ **이 항목은 실행 확인을 못 했다**(표 생성 금지) |
| `JSON_ARRAYAGG` 의 배열 순서 | 아무것도 아니다 | **아무도** — MySQL 에는 순서 지정 문법이 없다 |

- ★ **한쪽에서만 결론이 서는 실험이 있다** — 6번 절의 **`doc -> '$.a'`** 가 그렇다.\
  PG 의 `NULL` 은 **"PG 는 이것을 키 이름으로 읽는다"의 근거**이고, MySQL 의 `ERROR 3143` 은 **"MySQL 은 경로로만 읽는다"의 근거**다.\
  **두 출력은 서로를 증명하지 않는다.** "경로 문법이 다르다"를 양쪽 출력으로 함께 증명할 수는 없고, **각각 따로** 근거가 된다.
- ★ **8번 절의 MySQL 출력은 `SHOW WARNINGS` 없이는 반쪽이다.** `boom = 1` 만 보면 "잘 돌았다"로 읽힌다.\
  **경고도 출력이다** — 따로 묻지 않으면 안 보이는 출력이 있다는 것 자체가 이 절의 교훈이다.
- **10번 절의 PG 쪽은 계획이 아니라 카탈로그 조회다.** 계획은 통계에 따라 흔들리지만(32번) **`pg_opclass`/`pg_amop` 는 그 빌드의 정의**라 흔들리지 않는다.\
  대신 **"인덱스를 실제로 타느냐"는 안 보여 준다** — 그것은 [목록의 **47번 주제**](../47-when-indexes-are-used/)다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 형태를 모르는 외부 데이터.** 웹훅 페이로드·외부 API 원문을 **그대로** 보관할 때.
- **쓴다 — 희소한 속성.** 열로 만들면 대부분 `NULL` 이 되는 종류별 속성.
- **쓴다 — 스냅샷.** 주문 시점의 배송지처럼 **더는 안 바뀌는** 덩어리.
- **쓴다 — 출력 모양 만들기.** 저장은 관계형, 응답만 `jsonb_build_object`/`JSON_OBJECT`(9번 절).
- **안 쓴다 — `WHERE`/`JOIN`/`SUM` 할 값.** 열로 뺀다.
- **안 쓴다 — 타입이 정해진 수치.** 8번 절의 사고가 언제든 난다.
- **안 쓴다 — 다른 표를 가리키는 값.** 외래키를 못 건다.
- **주의 — PG 에서는 `jsonb`.** `json` 은 원문 보존이 목적일 때만.
- **주의 — 검색 패턴을 먼저 정하고 인덱스를 고른다.** "문서에 이게 있나"면 GIN, "이 값이 얼마인가"면 표현식·생성 열이다.

## 핵심 문장

- **MySQL 의 `JSON` 은 PG 의 `jsonb`** 다. `json`(원문 보존)에 해당하는 타입은 MySQL 에 없다.
- **`jsonb`/`JSON` 은 키를 정렬하고 중복 키의 마지막 것만 남긴다** — 두 엔진이 한 글자도 다르지 않았다.
- **`->` 는 JSON, `->>` 는 문자열**이다. 보이는 글자가 같아도 타입이 다르다.
- **경로 문법이 방언의 핵심이다** — PG 는 키 이름·`#>`·`jsonpath`, MySQL 은 `$.a.b` 하나.
- ★ **PG 에 `'$.a'` 를 주면 에러가 아니라 `NULL`** 이다. MySQL 에 `'a'` 를 주면 `ERROR 3143` 이다 — **한쪽만 조용하다.**
- **없는 키는 두 엔진 다 조용히 `NULL`** — 스키마가 있는 열이라면 에러였을 오타가 여기서는 안 잡힌다.
- **타입 보증이 없고, 틀린 타입에 PG 는 에러·MySQL 은 `0` + 경고 1292** 다([35번](../35-type-system-and-casting/)의 성격 차이 그대로).
- **`json` 은 인덱스를 못 걸고, `jsonb` 의 GIN 은 `@>`·`?`·`@?`·`@@` 계열만 탄다** — `->>` 는 못 탄다.
- **`WHERE`/`JOIN`/`SUM` 할 값이면 열로 뺀다.**

## 관련 자료

- [PostgreSQL 18 · JSON Types](https://www.postgresql.org/docs/18/datatype-json.html) — `json` 과 `jsonb` 의 차이, 정규화, 인덱싱이 한 페이지에 있다.
- [PostgreSQL 18 · JSON Functions and Operators](https://www.postgresql.org/docs/18/functions-json.html) — 연산자표와 SQL/JSON 경로 언어.
- [PostgreSQL 12 릴리스 노트](https://www.postgresql.org/docs/release/12.0/) · [PostgreSQL 17 릴리스 노트](https://www.postgresql.org/docs/release/17.0/) — `jsonpath` 12, `JSON_TABLE` 17.
- [MySQL 8.4 · The JSON Data Type](https://dev.mysql.com/doc/refman/8.4/en/json.html) — 정규화와 경로 문법.
- [MySQL 8.4 · JSON Functions](https://dev.mysql.com/doc/refman/8.4/en/json-functions.html) — 함수 전체 목록.
- [MySQL 8.4 · CREATE INDEX](https://dev.mysql.com/doc/refman/8.4/en/create-index.html) — 함수 키·다중값 인덱스. **10번 절의 MySQL 인덱스 문장은 여기서만 왔다(실행 확인 못 함).**
- [MySQL 8.0.21 릴리스 노트](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-21.html) — `JSON_VALUE()` 도입.
- [35 타입 체계와 캐스팅](../35-type-system-and-casting/) — **경계: 그쪽은 SQL 타입끼리의 변환 규칙과 「변환이 실패할 때 두 엔진이 어떻게 다른가」까지, 여기는 그 규칙이 스키마 없는 문서 안의 값에 적용될 때부터.** 8번 절이 그 편 결론의 재현이다.
- [32 CTE(`WITH`)](../32-cte-with-clause/) — 이 주제의 예시 문서를 만드는 도구.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — 없는 키의 `NULL` 이 바깥 조건을 무너뜨리는 경로.
- [20 LATERAL 조인](../20-lateral-join/) — `jsonb_array_elements` 를 `FROM` 에 놓을 때 필요한 문법.
- [13 INNER JOIN](../13-inner-join/) — 9번 절에서 `hr` 부서가 빠진 이유.
- **인덱스 정의**는 [46번 주제](../46-index-definition-composite-partial-expression/), **언제 타고 언제 안 타나**는 [목록의 **47번 주제**](../47-when-indexes-are-used/), **생성 열**은 [45번 주제](../45-check-not-null-default-generated-columns/), **외래키**는 [44번 주제](../44-foreign-key-referential-actions/)가 정본이다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **JSON 열(JSON column)** — JSON 문서 한 장을 값으로 담는 열.\
  예: `{"name":"ann","tags":["x","y"]}` 한 덩어리가 한 칸에 들어간다.
- **`jsonb`** — PostgreSQL 의 이진 JSON 타입. 파싱해서 저장하고 키를 정렬한다.\
  예: `'{"b":2,"a":1}'::jsonb` → `{"a": 1, "b": 2}`.
- **`json`(PG)** — 입력 텍스트를 **그대로** 보관하는 PostgreSQL 타입. 인덱스를 못 건다.\
  예: `'{"b":2,"a":1}'::json` → `{"b":2,"a":1}` 그대로.
- **정규화(normalization)** — 같은 뜻의 여러 표기를 하나의 표준 표기로 바꾸는 것.\
  예: 키 정렬·중복 키 제거·공백 제거.
- **`->` (화살표)** — 키나 첨자로 꺼내고 **결과도 JSON** 인 연산자.\
  예: `doc -> 'name'` → `"ann"`(따옴표가 남는다).
- **`->>` (이중 화살표)** — 꺼낸 뒤 **따옴표를 벗겨 문자열**로 주는 연산자.\
  예: `doc ->> 'name'` → `ann`. 비교·조인에는 이쪽을 쓴다.
- **경로 표현(path expression)** — 중첩된 값의 위치를 적는 문자열.\
  예: MySQL `'$.boss.name'`, PG `'{boss,name}'`(`#>` 용) 또는 `'$.boss.name'`(`jsonpath` 용).
- **`@>` (포함 연산자, PG)** — 왼쪽 문서가 오른쪽 문서를 **품고 있나**를 묻는다. GIN 이 탄다.\
  예: `doc @> '{"a":1}'` → `a` 가 1 이면 참.
- **`?` (키 존재 연산자, PG)** — 그 키가 있나를 묻는다. GIN 이 탄다.\
  예: `doc ? 'tags'` → 참.
- **GIN(Generalized Inverted Index)** — 한 값 안의 **여러 조각**을 색인하는 PostgreSQL 인덱스.\
  예: 문서 하나의 모든 키·값을 색인해 `@>` 검색을 받아 준다.
- **연산자 클래스(operator class)** — 어떤 인덱스가 어떤 타입의 어떤 연산자를 받아 주는지 정의한 것.\
  예: `gin/jsonb_ops` 가 `@>`·`?`·`@?` 등 6개를 받는다.
- **생성 열(generated column)** — 다른 열에서 계산되는 열. MySQL 에서 JSON 값을 인덱스에 올리는 통로다.\
  예: `name_gc VARCHAR(30) AS (JSON_VALUE(doc,'$.name'))`. [목록의 **45번 주제**](../45-check-not-null-default-generated-columns/).
- **`JSON_TABLE`** — JSON 을 **행과 열의 표로 펴는** 함수. PG 17+ · MySQL 8.0.4+.\
  예: `JSON_TABLE(doc, '$.tags[*]' COLUMNS (val text PATH '$'))`.
- **경고 1292(Truncated incorrect … value)** — MySQL 이 값을 읽다 말았을 때 남기는 경고.\
  예: `'삼백'` 을 정수로 읽어 `0` 으로 쓰고 이 경고를 남긴다. `SHOW WARNINGS` 로만 보인다.

## 더 들어가면

- **PG 의 `jsonb_path_ops` GIN 은 `jsonb_ops` 보다 작다.** 대신 `@>` 계열만 받는다 — 검색이 포함 질의뿐이면 이쪽이 낫다.
- **PG 14 부터 첨자 문법이 생겼다** — `doc['a']` 가 `doc -> 'a'` 와 같고, 대입(`doc['a'] = '1'`)도 된다.
- **MySQL 의 다중값 인덱스(multi-valued index)** 는 JSON **배열 한 칸에 인덱스 레코드 여러 개**를 만든다 — 태그 검색에 쓴다. 이 주제에서는 표를 못 만들어 실행 확인하지 못했다.
- **PG 의 `jsonb` 부분 갱신은 문서 전체를 다시 쓴다.** 큰 문서에서 잦은 갱신은 비싸다 — 자주 바뀌는 값일수록 열로 빼는 이유가 하나 더 있다.
- **JSON 을 키로 조인하면 팬아웃이 보이지 않는다** — 배열을 펴면 행이 불어난다([25번](../25-join-fan-out/)). 펴기 전후의 행 수를 세어 두라.
- **`JSON_TABLE` 이 두 엔진에 다 있다는 것**이 이 주제에서 가장 쓸 만한 공통 지대다. 새 질의를 쓴다면 **여기서 출발**하는 편이 이식에 유리하다.
