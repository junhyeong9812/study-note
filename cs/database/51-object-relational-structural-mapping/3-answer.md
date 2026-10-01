# database/51-object-relational-structural-mapping — 정답

## 정답

### 1. 다섯 가지 차이와 패턴

| 객체 | 테이블 | 패턴(PoEAA 12장) |
|---|---|---|
| 메모리 정체성 | 기본 키 | Identity Field |
| 참조 | FK 값 | Foreign Key Mapping |
| 컬렉션(1NF 위반) | "여러" 쪽 FK / 연결 테이블 | Foreign Key Mapping(1:N), Association Table Mapping(N:M), Dependent Mapping(부모 수명 자식) |
| 작은 값 객체 | 컬럼뿐 | Embedded Value, 또는 그래프 통째로 Serialized LOB |
| 상속 | 없음(관계 모델 기준. PostgreSQL `INHERITS`는 별도 기능) | Single / Class / Concrete Table Inheritance |

### 2. 대리키 vs 자연키

- 대리키(시퀀스·UUID)
  - 뜻이 없어 바뀌지 않는다.
  - 위험: 자연키의 유일성을 DB가 더는 모른다. UNIQUE를 따로 걸지 않으면 같은 이메일·사업자번호가 두 행 생긴다.
- 자연키(이메일·ISBN)
  - 위험: 현실 값은 바뀐다(이메일 변경, 번호 체계 개편). 그러면 그 키를 FK로 든 모든 테이블을 고쳐야 한다.
  - 복합 자연키는 FK도 복합이 된다.
- 대리키를 써도 자연키 컬럼에는 **UNIQUE 제약**을 건다. Hibernate는 이를 `@NaturalId`로 표시한다(Hibernate 6.6 3.10).
- 키 생성 방식도 본다. Hibernate는 `IDENTITY`면 INSERT를 배치로 묶지 못한다(3.7.10).

### 3. Embedded Value

```text
  employment(id, person_id, start_on, end_on, salary_amount, salary_currency)
             값 객체 두 개가 컬럼 4개로 펼쳐졌다. 자기 테이블·자기 id 없음
```

- 별도 테이블로 빼고 주인 행이 그 id를 FK로 들면
  - 값 객체에 없던 식별자가 생긴다(주인 id를 PK로 쓰는 자식 테이블이면 아니다). 공유 여부·수명 관리 책임이 생긴다.
  - 값을 바꿀 때 새 행 + FK 교체를 하면 옛 행이 고아가 된다.
  - 로컬 재현(PostgreSQL 17.11): 주소 변경 + 고객 삭제 뒤, `NOT EXISTS` 고아 조회에 `서울`·`부산` 두 행이 남았다.
- 조회할 때 조인도 하나 는다.

### 4. 단방향 `@OneToMany`

- JPA 기본 매핑은 FK가 아니라 **조인 테이블**이다. 이름은 `Order_OrderLine`처럼 `A_B` 형태다. `OrderLine` 쪽 컬럼에는 유일 제약이 붙는다(Jakarta Persistence 3.1 2.11.5.1).
- 줄 하나를 빼면 Hibernate는 부모의 연결 행을 **전부 지우고**(`DELETE FROM … WHERE order_id = ?`) 남은 원소 수만큼 다시 INSERT한다. `orphanRemoval = true`면 빠진 자식 행도 DELETE한다(Hibernate 6.6 3.8.2).
- 고침
  - 자식에 `@ManyToOne @JoinColumn(name = "order_id")`를 둔다.
  - 부모는 `@OneToMany(mappedBy = "order")`로 바꾼다(양방향, 자식 FK가 관계 소유).
  - 또는 단방향에 `@JoinColumn`을 명시한다.

### 5. 상속 3종 비교

| | Single Table | Class Table (`JOINED`) | Concrete Table (`TABLE_PER_CLASS`) |
|---|---|---|---|
| 한 건 조회 | 행 하나 | 경로 테이블 조인 | 테이블 하나 |
| 다형 조회 | 한 테이블 | 자식 테이블 모두 LEFT JOIN | `UNION`(Hibernate `UNION ALL`) |
| 하위 컬럼 NOT NULL | 불가(조건부 CHECK로 보완) | 가능 | 가능 |
| 상위 타입 FK | 가능 | 가능 | 어렵다 |

- Jakarta Persistence 3.1 2.13
  - 단일 테이블과 조인 전략은 구현이 **반드시** 지원한다.
  - 구체 테이블 전략은 **선택**이다. 쓰면 이식성이 없다.
- `@Inheritance`를 생략하면 `SINGLE_TABLE`, 구분 컬럼 기본은 `DTYPE`(STRING, 길이 31)이다.

### 6. 조건부 CHECK

```sql
CONSTRAINT card_needs_no CHECK (dtype <> 'CardPayment' OR card_no IS NOT NULL)
```

- PostgreSQL 17.11: `ERROR: new row for relation "payment" violates check constraint "card_needs_no"`, `DETAIL: Failing row contains (…)`.
- MySQL 8.4.10: `ERROR 3819 (HY000): Check constraint 'card_needs_no' is violated.`
- 둘 다 로컬 재현이다. JPA 스키마 생성은 이 제약을 만들지 않는다. 마이그레이션에 직접 쓴다.

### 7. JSON LOB 검색

- 로컬 재현(PostgreSQL 17.11, 20만 행)
  - 인덱스 전: `Parallel Seq Scan`, `Rows Removed by Filter: 99980`(워커당).
  - `CREATE INDEX ON orders ((extra->>'coupon'))` 뒤: `->>` 등호가 `Bitmap Index Scan`.
  - `extra @> '{"coupon":"C42"}'`는 여전히 `Seq Scan`이었다. GIN(`jsonb_path_ops`)을 만든 뒤 `Bitmap Index Scan`이 되었다.
- 질의 모양마다 인덱스가 다르다.
  - 특정 경로의 등호·범위: 표현식 B+Tree.
  - 포함 질의: GIN.
- MySQL 8.4: `CAST(extra->>'$.coupon' AS CHAR(20)) COLLATE utf8mb4_bin` 함수 인덱스를 만든 뒤 `Table scan`이 `Index lookup`으로 바뀌었다(로컬 재현).
- 장기 대처
  - 검색·조인·제약이 필요한 필드는 정식 컬럼(또는 생성 컬럼)으로 승격하고 백필한다.
  - JSON 경로에는 FK·NOT NULL을 직접 선언할 수 없다. 존재·타입은 CHECK(PG 식, MySQL `JSON_SCHEMA_VALID()`)로 검사할 수 있지만, FK가 필요하면 컬럼이어야 한다.

### 8. JOINED 다형 조회 지연

- 보이는 것: SQL 로그의 `from payment p left outer join card_payment … left outer join bank_transfer … left outer join …`. 하위 타입 수만큼 조인이 붙는다.
- 원인
  - 다형 조회는 행의 실제 타입을 모른다. 그래서 모든 자식 테이블을 조인한다.
  - JPA 명세도 깊은 계층에서 "받아들일 수 없는 성능"을 JOINED의 단점으로 든다(2.13.2).
- 대처
  - 목록은 부모 테이블만 읽는 DTO 프로젝션으로 한다.
  - 계층을 얕게(조합) 한다.
  - 다형 조회가 주 용도면 Single Table로 옮긴다.

### 9. 트리와 그래프

- Class Table에서 객체 하나 = 상속 트리의 루트에서 그 잎까지 **경로 위 테이블들을 PK로 조인**한 결과다.
  - 로컬 재현 계획: `Nested Loop Left Join` 안에 `pay_pkey`, `card_pay_pkey`, `bank_pay_pkey` Index Scan.
  - 타입을 모르면 모든 가지를 LEFT JOIN한다.
- N:M 연결 테이블 = **이분 그래프의 간선 목록**이다. `(student_id, course_id)` 복합 PK가 중복 간선을 막는다. 간선에 속성이 붙으면 그 간선을 엔티티로 올린다.
