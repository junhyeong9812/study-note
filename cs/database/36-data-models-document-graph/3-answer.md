# database/36-data-models-document-graph — 정답

## 정답

### 1. 이력서와 지역성

- 관계: `users`, `positions`, `education`, `contact_info` 테이블로 나누고 `user_id`로 잇는다. 한 사람의 이력서를 보려면 여러 번 조회하거나 여러 테이블을 조인한다.
- 문서: 한 사람 = JSON 문서 하나. 경력·학력은 배열, 연락처는 중첩 객체다. 일 대 다 관계가 트리로 드러난다.
- 지역성: 문서 DB에서 문서는 보통 하나의 연속된 값으로 저장되므로 전체를 읽는 화면은 조회 한 번이면 된다(DDIA 2장).
- 이득이 사라지는 조건: 문서의 일부만 자주 읽거나 쓸 때. 보통 문서 전체를 읽어야 하고, 크기가 바뀌는 갱신은 전체를 다시 쓴다. 그래서 문서를 작게 두라고 권한다.

### 2. 복사 vs 참조

- 복사: 읽기는 문서 하나로 끝난다. 대신 회사 이름이 바뀌면 **앱이** 모든 복사본을 고쳐야 하고, 하나라도 빠지면 불일치다(쓰기 비용·일관성 위험).
- 참조: 문서에 회사 id만 둔다. 한 곳만 고치면 된다. 대신 읽을 때 조인이 필요하다. 문서 DB의 조인 지원이 약하면 **앱이** 여러 번 조회해 조인을 흉내 내고, 보통 DB 안 조인보다 느리다(DDIA 2장).
- IMS 이야기: 1960~70년대 계층형 DB도 일 대 다에 강하고 다대다에 약해, 개발자가 복제할지 참조를 손으로 풀지 골라야 했다. 문서 DB가 같은 문제를 다시 만난다는 것을 보여 준다.

### 3. 스키마 온 리드

- 읽는 코드는 필드 이름·타입을 가정한다. 즉 암묵적 스키마가 있다. DB가 쓰기 때 강제하지 않을 뿐이다. 그래서 더 정확한 말은 "스키마 온 리드"다(DDIA 2장).
- 스키마 온 라이트 ≈ 정적 타입 검사, 스키마 온 리드 ≈ 동적 타입 검사.
- 스키마 온 리드가 나은 경우(DDIA)
  1. 객체 종류가 많아 종류마다 테이블을 두기 어렵다.
  2. 구조를 통제할 수 없는 외부 시스템이 정하고, 언제든 바뀔 수 있다.

### 4. JSON 타입이 검사하는 것

- PostgreSQL `jsonb`: `"age":"unknown"` 문서는 **들어간다**(로컬 재현).
- MySQL `JSON`: `'{bad json'`은 `ERROR 3140 (22032): Invalid JSON text`로 **거부된다**(로컬 재현).
- 두 DB 모두 **JSON 문법**은 쓰기 때 검사한다. **필드 존재·타입(문서의 모양)**은 검사하지 않는다. 모양 검사는 CHECK 제약 등을 따로 걸어야 한다.

### 5. 평균 나이

- PostgreSQL 17.11: `ERROR 22P02: invalid input syntax for type integer: "unknown"`. 쿼리 전체가 실패한다.
- MySQL 8.4.10: `23.666666666666668`과 경고 1건(`3156 Invalid JSON value for CAST to DOUBLE`). "unknown"이 0으로 계산됐다: (31 + 0 + 40) / 3.
- 교훈: 같은 데이터 오류가 한 제품에선 오류로, 다른 제품에선 경고 + 틀린 숫자로 드러난다. 타입을 먼저 거르면(`jsonb_typeof(…) = 'number'`) PostgreSQL 평균은 35.5였다.

### 6. 그래프를 관계 DB에

```text
  vertices(vertex_id PK, properties)
  edges(edge_id PK, tail_vertex FK, head_vertex FK, label, properties)
  INDEX(tail_vertex), INDEX(head_vertex)       -- 나가는·들어오는 간선을 빨리 찾기
```

- 어려운 이유: 출생지가 도시일 수도 주일 수도 있어 `WITHIN` 간선을 **몇 번** 따라가야 할지 미리 모른다. 고정 개수의 조인으로 쓸 수 없다.
- Cypher: `(person) -[:BORN_IN]-> () -[:WITHIN*0..]-> (us:Location {name:'United States'})`. `*0..`가 "0번 이상 반복"이다.
- SQL: 재귀 CTE로 USA에서 `within` 간선을 거꾸로 따라가 도달 가능한 장소 집합을 구하고, 유럽도 같이 구한 뒤 `born_in`·`lives_in`과 교차한다. DDIA는 같은 질의가 Cypher 4줄, SQL 29줄이라고 비교한다. 로컬 재현(PostgreSQL 17.11)에서 `Lucy`를 얻었다.

### 7. 혼합 설계

- 열: 모든 상품에 공통이고 조회·조인·제약에 쓰는 것(id, name, price, company_id). 공유되는 회사는 FK 참조.
- jsonb: 종류마다 다른 속성(색상, 사이즈, 소재 등).
- 제약·인덱스
  - `CHECK (jsonb_typeof(attrs) = 'object')` 같은 최소 모양 검사. 꼭 필요한 필드는 `CHECK (attrs ? 'weight' AND jsonb_typeof(attrs->'weight') = 'number')`처럼 개별로. 존재 검사(`?`)를 빼면 키가 없을 때 NULL이 되어 CHECK를 통과한다.
  - `CREATE INDEX … USING gin (attrs)`로 `@>`·`?` 검색(PostgreSQL 8.14.4). MySQL은 추출용 생성 열에 인덱스를 건다(13.5).
- 위반 데이터가 있을 때: 그냥 추가하면 `check constraint … is violated by some row`로 실패한다(로컬 재현). PostgreSQL은 `ADD CONSTRAINT … NOT VALID`로 새 행부터 검사하고, 위반 행을 정리한 뒤 `VALIDATE CONSTRAINT`한다(02번).

### 8. 복사본 불일치

- 원인: 여러 사용자가 공유하는 회사(다대일)를 문서마다 복사했다. 이름 변경 시 일부 문서만 갱신됐다. 로컬 재현: `1 | Acme Corp | Acme Corp`, `2 | Acme | Acme Corp`.
- 확인: 원본과 복사본을 비교한다.

```sql
SELECT u.id, u.doc #>> '{company,name}' AS embedded, c.name AS source
FROM users_doc u JOIN company c ON c.id = (u.doc #>> '{company,id}')::int
WHERE u.doc #>> '{company,name}' IS DISTINCT FROM c.name;
```

- 근본 대처: 공유되는 것은 id로 참조하고 읽을 때 해석한다. 복사를 유지해야 하면 원본 변경을 한 경로(이벤트·배치)로만 전파하고, 위 점검 쿼리를 주기적으로 돌린다.

### 9. 큰 문서의 작은 갱신

- PostgreSQL 17 8.14.2: 테이블에 저장된 JSON도 다른 타입과 같은 동시성 제어를 받는다. 갱신은 **행 전체에** 행 수준 락을 건다. 문서를 다룰 만한 크기로 제한하라고 권한다.
- DDIA 2장: 문서 갱신은 보통 문서 전체를 다시 쓴다. 크기를 바꾸지 않는 수정만 제자리에서 쉽게 된다.
- 그래서 필드 하나를 바꾸는 요청끼리도 같은 행 락을 두고 경합하고, 매번 큰 쓰기가 생긴다. 로컬 재현(예시, PostgreSQL 17.11): 약 384KB `jsonb` 문서의 필드 하나를 `jsonb_set`으로 바꾸자 WAL이 약 422KB 생겼다.
- 대처: 독립적으로 자주 바뀌는 부분은 별도 행·테이블로 떼고, 문서는 작게 유지한다.
