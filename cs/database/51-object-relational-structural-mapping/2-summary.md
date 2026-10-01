# database/51-object-relational-structural-mapping — 객체 구조를 테이블로: O-R 구조 매핑 패턴 — 정리 (힌트)

## 해결하는 문제

객체와 테이블은 모양이 다르다.

```text
  객체 세계                              관계형 세계
  ─────────────────────                  ─────────────────────
  메모리 주소가 곧 정체성                   기본 키가 정체성
  참조 (order.customer)                  외래 키 값 (orders.customer_id)
  컬렉션 (order.lines: List)             "여러 값" 컬럼이 없다 (1NF) → 다른 테이블의 FK
  작은 값 객체 (Money, DateRange)          컬럼만 있다 — 값 객체 "타입"이 없다
  상속 (Payment ← CardPayment)           상속이 없다 (관계 모델 기준)
```

- PostgreSQL에는 `INHERITS` 테이블 상속이 있다(PostgreSQL 17 5.11). 하지만 이것은 객체 상속을 담는 표준 방법이 아닌 별도 기능이다. JPA 상속 매핑도 이것을 쓰지 않는다.

- 이 차이를 흔히 *객체-관계 임피던스 불일치(object-relational impedance mismatch)*라고 부른다.
- 구조 매핑 패턴은 이 다섯 가지 차이 각각을 **어떤 테이블 모양으로 바꿀지**를 정한다. Fowler 『PoEAA』 12장 "Object-Relational Structural Patterns"의 패턴들이다.

쉬운 예: 이삿짐을 상자에 담는 일이다.
- 가구(엔티티)는 상자마다 번호표를 붙인다.
- 작은 소품(값 객체)은 가구 서랍에 같이 넣는다.
- "이 의자는 저 책상 세트"라는 관계는 번호표로 적는다.

똑같은 구조다.\
어떻게 담느냐에 따라 풀 때(조회) 비용과 망가질 위험(제약)이 달라진다.

실무 예:
- JPA `@Id`, `@Embedded`, `@ManyToOne`, `@ManyToMany`, `@ElementCollection`, `@Inheritance`는 모두 이 패턴의 구현이다.
- "누가 SQL을 아는가"(Data Mapper·Active Record)는 database `25-data-source-patterns`가 다룬다. 이 노트는 "어떤 **모양**으로 저장하나"만 다룬다.

## 동작·원리

### 1. Identity Field — 객체에 행의 키를 담는다

```text
  class Order { Long id; ... }        ←→      orders(id bigint PRIMARY KEY, ...)
            └── 이 필드가 "메모리 객체 ↔ DB 행"을 잇는 끈
```

- PoEAA 정의: 메모리 객체와 DB 행의 정체성을 유지하려고, 행의 기본 키를 객체 필드에 저장한다.
- 어떤 키를 쓸지가 설계 질문이다.

| | 대리키(surrogate) | 자연키(natural) |
|---|---|---|
| 예 | `bigint` 시퀀스, UUID | 주민번호, 이메일, ISBN, (주문번호, 줄번호) |
| 장점 | 뜻이 없어 바뀌지 않는다 | 따로 유일 제약이 필요 없다, 의미가 보인다 |
| 위험 | 자연키 중복을 막으려면 UNIQUE를 **따로** 걸어야 한다 | 현실 값이 바뀌면(이메일 변경) 모든 FK를 고쳐야 한다 |

- 대리키를 쓰더라도 자연키에는 UNIQUE를 건다. Hibernate는 이것을 `@NaturalId`로 표시하는 기능을 따로 둔다(Hibernate 6.6 3.10).
- 키 생성 방식도 매핑에 영향을 준다. Hibernate는 `IDENTITY` 생성 방식이면 INSERT를 배치로 묶지 못한다(Hibernate 6.6 3.7.10). 키 전략 자체는 [28-key-strategy-surrogate-natural-public-id](../28-key-strategy-surrogate-natural-public-id/2-summary.md)에서 다룬다.

### 2. Embedded Value — 값 객체를 주인 테이블의 컬럼으로 편다

```text
  class Employment {                        employment
    Long id;                                ┌────┬──────────┬──────────┬─────────────┬──────────────┐
    Person person;                          │ id │ start_on │ end_on   │ salary_amt  │ salary_cur   │
    DateRange period;   ──┐                 └────┴──────────┴──────────┴─────────────┴──────────────┘
    Money salary;       ──┴── 컬럼으로 평탄화 (자기 테이블 없음, 자기 id 없음)
  }
```

- PoEAA: 돈·기간 같은 작은 값 객체를 테이블로 만들 사람은 없다. 주인 행의 필드로 펼친다.
- JPA: `@Embeddable` 클래스 + `@Embedded` 필드.
- 값 객체를 **별도 테이블**로 빼고 주인 행이 그 행의 id를 FK로 들면 무엇이 생기나(⚠)
  - 값 객체에 없던 **식별자**가 생긴다. (주인 id나 `(주인 id, 순번)`을 PK로 쓰는 자식 테이블이면 새 식별자는 없다.)
  - 값을 바꿀 때 "새 행 INSERT + FK 교체"를 하면 옛 행이 **고아**가 된다.
  - 로컬 재현(PostgreSQL 17.11): 주소를 새 행으로 바꾸고 고객 하나를 지우자 `address` 1·2번 행이 아무도 참조하지 않는 고아로 남았다.

### 3. Foreign Key Mapping / Association Table Mapping — 참조와 컬렉션

```text
  N:1 또는 1:N — Foreign Key Mapping           N:M — Association Table Mapping

  orders                customer                student      enrollment            course
  ┌────┬─────────────┐   ┌────┐                ┌────┐       ┌────────────┬───────────┐  ┌────┐
  │ id │ customer_id ├──>│ id │                │ id │<──────┤ student_id │ course_id ├─>│ id │
  └────┴─────────────┘   └────┘                └────┘       └────────────┴───────────┘  └────┘
  "여러" 쪽 행이 "하나" 쪽 키를 든다              양쪽 다 "여러"라 FK를 둘 곳이 없다 → 연결 테이블
```

- PoEAA: 객체 컬렉션은 1NF를 어긴다. 그래서 1:N은 "하나" 쪽이 아니라 **"여러" 쪽 테이블에 FK**를 둔다.
- N:M에는 단일 값 끝이 없다. 그래서 두 FK를 가진 연결 테이블을 만든다.
- JPA 기본값 함정: **단방향 `@OneToMany`**의 기본 매핑은 FK가 아니라 **조인 테이블**(`A_B`)이다(Jakarta Persistence 3.1 2.11.5.1). 연결 테이블이 원하지 않게 생긴다.
  - 원하면 `@JoinColumn`을 붙이거나 양방향(`mappedBy`)으로 만든다.
- 연결 테이블에 속성(수강 신청일, 성적)이 붙기 시작하면 그것은 연결이 아니라 **엔티티**다. 이때는 `Enrollment` 클래스로 올린다.

### 4. Dependent Mapping — 부모 매퍼가 자식까지 저장한다

```text
  Album ─┬─ Track 1          album(id, title)
         ├─ Track 2          track(album_id, seq, title)   ← 다른 곳에서 참조하지 않는다
         └─ Track 3          부모를 저장할 때 자식을 같이 저장·삭제한다
```

- PoEAA: 다른 테이블이 참조하지 않는 자식은, 부모 매퍼가 자식 매핑까지 맡는다.
- JPA에서는 `@ElementCollection`(값 컬렉션)이나 `@OneToMany(cascade = ALL, orphanRemoval = true)`가 이 역할을 한다.
- 자식에 개별 식별이 없으면 변경이 비싸다. Hibernate 문서: 단방향 bag(순서·유일성 없는 컬렉션)에서 원소 하나를 빼면, 부모의 연결 행을 **모두 지우고 남은 것을 다시 넣는다**(Hibernate 6.6 3.8.2·3.9.11). 값 컬렉션도 bag이면 같다(3.9.7 예). `Set`이면 빠진 원소만 지운다(Hibernate 6.6 `PersistentSet#getDeletes`). DB 호출 모양은 컬렉션 종류에 달렸다(3.9.7).

### 5. Serialized LOB — 객체 그래프를 한 컬럼에 통째로

```text
  orders(id, extra jsonb)
  extra = {"coupon": "C42", "memo": "...", "gift": {"wrap": true}}
          └── DB는 이 안의 구조를 컬럼으로 모른다 (컬럼 제약 없음, 기본 인덱스 없음)
```

- PoEAA: 작은 객체들의 복잡한 그래프를 직렬화해 큰 객체(LOB) 하나로 한 필드에 저장한다.
- 오늘날에는 PostgreSQL `jsonb`, MySQL `JSON`이 흔한 형태다. Hibernate 6.6은 `@JdbcTypeCode(SqlTypes.JSON)`을 명시해야 JSON 타입을 쓴다(3.2.40).
- 대가: 안의 필드로 **검색·조인·제약**을 걸기 어렵다(시나리오 4).

### 6. 상속 매핑 3종

```text
  Payment(id, amount) ← CardPayment(card_no), BankTransfer(bank_code)

  (a) Single Table                (b) Class Table                   (c) Concrete Table
  payment                         payment(id, amount)               card_payment(id, amount, card_no)
  ┌─────┬──────┬──────┬───────┐   card_payment(id→payment, card_no) bank_transfer(id, amount, bank_code)
  │dtype│amount│card_no│bank_  │   bank_transfer(id→payment, ...)
  │     │      │(null?)│(null?)│   클래스마다 테이블, 조회 = 조인      구체 클래스마다 테이블, 공통 컬럼 반복
  └─────┴──────┴──────┴───────┘
  한 테이블 + 구분 컬럼
```

| | Single Table | Class Table (JPA `JOINED`) | Concrete Table (JPA `TABLE_PER_CLASS`) |
|---|---|---|---|
| 한 건 조회 | 행 하나 | 부모 + 자식 테이블 조인 | 테이블 하나 |
| 다형 조회 ("모든 결제") | 한 테이블 스캔 | 조인 N개 | `UNION` (Hibernate: `UNION ALL`) |
| 하위 클래스 전용 컬럼 NOT NULL | **불가**(다른 타입 행에서 null) | 가능 | 가능 |
| 상위 타입을 가리키는 FK | 가능 | 가능 | 어렵다(테이블이 여럿) |
| 계층 변경 비용 | 컬럼 추가 | 테이블 추가 | 공통 컬럼 변경이 모든 테이블에 |

- Jakarta Persistence 3.1 2.13
  - 구현은 단일 테이블과 조인 전략을 **반드시** 지원해야 하고, 구체 테이블 전략 지원은 **선택**이다. 쓰면 이식성이 없다.
  - 단일 테이블은 하위 클래스 상태 컬럼이 nullable이어야 한다는 단점이 있다.
  - 조인 전략은 깊은 계층에서 성능이 받아들일 수 없을 만큼 나빠질 수 있다.
  - 구체 테이블은 다형 관계 지원이 약하고, 계층 전체 질의에 `UNION`이나 하위 클래스별 질의가 필요하다.
- JPA 기본값
  - `@Inheritance`를 생략하면 `SINGLE_TABLE`이다.
  - 구분 컬럼 기본은 이름 `DTYPE`, 타입 `STRING`, 길이 31이다(`@DiscriminatorColumn`).

## 쓰이는 자료구조·알고리즘

- **조인 = 상속 계층 트리의 경로**: Class Table에서 한 객체를 복원하는 것은 루트 테이블에서 잎 테이블까지 **트리 경로의 테이블을 PK로 조인**하는 것이다. 로컬 재현(PostgreSQL 17.11) 계획: `Nested Loop Left Join` 두 단 아래에 `pay_pkey`·`card_pay_pkey`·`bank_pay_pkey` Index Scan 세 개. 하위 타입을 모르고 다형 조회하면 모든 자식 테이블을 LEFT JOIN한다. 조인 알고리즘은 [11-join-algorithms](../11-join-algorithms/2-summary.md).
- **임베디드 값 = 컬럼 평탄화**: 중첩 구조(객체 트리)를 접두어 붙은 컬럼 목록으로 펼친다(`salary.amount` → `salary_amount`). 역변환은 컬럼 묶음을 다시 객체로 조립한다.
- **연결 테이블 = 이분 그래프의 간선 목록**: N:M 관계는 두 노드 집합 사이의 간선 목록이다. `(student_id, course_id)` 복합 PK가 중복 간선을 막는다. [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
- **JSON 인덱스**: 표현식 B+Tree(`(extra->>'coupon')`)는 특정 경로 하나의 등호·범위에, GIN 역색인(`jsonb_path_ops`)은 포함(`@>`) 질의에 쓴다. [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 결정 순서

```text
  이 개념에 정체성이 있나? (따로 조회·참조·수명)  ── 예 ─> 엔티티: Identity Field + 자기 테이블
         │ 아니오
         v
  값 객체다 ── 개수가 1개 ──> Embedded Value (주인 테이블 컬럼)
         └── 여러 개 ──> Dependent Mapping (@ElementCollection / 자식 테이블, 부모와 수명 같이)
  안의 필드로 검색·제약이 필요 없다, 구조가 자주 바뀐다 ──> Serialized LOB (json/jsonb) 후보
  상속 ──> 다형 조회가 많고 하위 컬럼이 적다: Single Table
          하위 컬럼 NOT NULL·FK가 중요하다: Class Table
          하위 타입을 따로만 조회한다: Concrete Table (또는 상속 매핑을 포기)
```

### 2. 단일 테이블의 NOT NULL 빈자리 메우기 — CHECK 제약

```sql
-- PostgreSQL 17 / MySQL 8.4 공통 (MySQL 8.4 15.1.20.6 CHECK Constraints)
CREATE TABLE payment(
  id bigint PRIMARY KEY,
  dtype varchar(31) NOT NULL,
  amount numeric(12,2) NOT NULL,
  card_no text,
  bank_code text,
  CONSTRAINT card_needs_no   CHECK (dtype <> 'CardPayment'  OR card_no   IS NOT NULL),
  CONSTRAINT bank_needs_code CHECK (dtype <> 'BankTransfer' OR bank_code IS NOT NULL)
);
INSERT INTO payment VALUES (2,'CardPayment',1000,NULL,NULL);
-- ERROR:  new row for relation "payment" violates check constraint "card_needs_no"   (로컬 재현, PostgreSQL 17.11)
-- MySQL 8.4.10: ERROR 3819 (HY000): Check constraint 'card_needs_no' is violated.       (로컬 재현)
```

- "타입이 X면 이 컬럼은 NOT NULL"을 조건부 CHECK로 건다. JPA는 이 제약을 자동으로 만들지 않는다. 마이그레이션에 직접 쓴다.

### 3. JPA 매핑 예

```java
@Embeddable
public record Money(BigDecimal amount, String currency) {}

@Entity
@Inheritance(strategy = InheritanceType.JOINED)          // Class Table
public abstract class Payment {
    @Id @GeneratedValue(strategy = GenerationType.SEQUENCE) Long id;   // Identity Field
    @Embedded Money money;                                             // Embedded Value
    @ManyToOne(fetch = FetchType.LAZY) @JoinColumn(name = "order_id") Order order;  // FK Mapping
}

@Entity
public class Order {
    @Id @GeneratedValue Long id;
    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)  // 양방향: 조인 테이블 없음
    List<OrderLine> lines = new ArrayList<>();
    @JdbcTypeCode(SqlTypes.JSON) Map<String, Object> extra;                         // Serialized LOB
}
```

- Hibernate 6.6 문서는 3.3.11 Aggregate embeddable mapping에서 embeddable을 Java `record`로 정의하는 예를 든다. 3.3.8은 Jakarta Persistence가 embeddable에 Java Bean 규약(인자 없는 생성자)을 요구하고 record는 이를 따르지 않는다고 적는다. 그래서 record embeddable은 Hibernate 기능이며, 다른 JPA 구현·버전에서는 따로 확인한다.

### 4. 진단

```sql
-- 고아 행 찾기 (값 객체를 별도 테이블로 뺀 경우)
SELECT a.* FROM address a WHERE NOT EXISTS (SELECT 1 FROM customer c WHERE c.address_id = a.id);

-- 단일 테이블 상속의 null 비율 — 하위 타입이 늘면 이 목록이 길어진다
SELECT dtype, count(*), count(card_no) AS card_no_filled, count(bank_code) AS bank_code_filled
  FROM payment GROUP BY dtype;

-- JSON 필드 검색의 계획 확인
EXPLAIN (ANALYZE, BUFFERS) SELECT id FROM orders WHERE extra->>'coupon' = 'C42';       -- PostgreSQL
EXPLAIN FORMAT=TREE SELECT id FROM orders WHERE extra->>'$.coupon' = 'C42';           -- MySQL
```

- Hibernate가 실제로 내보내는 SQL을 로그로 확인한다(`org.hibernate.SQL` 로거). 조인 수와 UNION 여부가 여기서 보인다.

## 장애 시나리오와 대처

### 1. 단일 테이블 상속 → nullable 컬럼 폭증, NOT NULL 제약 불가

- **현상**: 하위 타입이 10개를 넘자 `payment` 테이블 컬럼이 60개가 된다. 행마다 대부분 null이다. 카드 결제에 카드 번호가 빠진 행이 섞인다.
- **보이는 형태**: 오류는 없다. 데이터 품질 검사에서 `count(card_no) < count(*) WHERE dtype='CardPayment'`. 조회 코드에 `if (cardNo == null)` 방어가 늘어난다.
- **원인**
  - 한 테이블이 모든 하위 타입을 담는다. 그래서 하위 타입 전용 컬럼은 다른 타입 행에서 null이어야 한다.
  - 그래서 컬럼 단위 `NOT NULL`을 걸 수 없다(Jakarta Persistence 3.1 2.13.1).
- **대처**
  - 조건부 `CHECK (dtype <> 'X' OR col IS NOT NULL)`를 건다(로컬 재현에서 위반 INSERT 거부).
  - 하위 타입 전용 필드가 많아지면 Class Table로 옮긴다.
  - 공통 필드 + 타입별 JSON(Serialized LOB)도 선택지다. 대신 시나리오 4의 대가를 치른다.

### 2. 클래스 테이블 상속 → 조회마다 조인 N개

- **현상**: 결제 목록 API가 하위 타입이 늘 때마다 느려진다.
- **보이는 형태**: Hibernate SQL 로그에 부모 테이블과 **모든 자식 테이블**의 `left outer join`이 붙는다. `EXPLAIN`에 조인 노드가 하위 타입 수만큼 쌓인다.
- **원인**
  - 다형 조회("모든 Payment")는 행마다 어떤 하위 타입인지 모른다. 그래서 모든 자식 테이블을 LEFT JOIN한다.
  - 깊은 계층이면 한 건 조회에도 경로의 테이블 수만큼 조인한다. JPA 명세도 "깊은 계층에서 받아들일 수 없는 성능"을 단점으로 든다(2.13.2).
- **대처**
  - 목록은 부모 테이블만 읽는 전용 조회(프로젝션 DTO)로 만든다.
  - 계층을 얕게 한다(상속보다 조합).
  - 다형 조회가 대부분이면 Single Table로 되돌린다.

### 3. 값 객체를 별도 테이블로 → 불필요한 식별자와 고아 행

- **현상**: `address` 테이블이 고객 수보다 훨씬 빠르게 커진다. 아무도 참조하지 않는 행이 쌓인다.
- **보이는 형태** (로컬 재현, PostgreSQL 17.11): 주소 변경을 "새 행 INSERT + FK 교체"로 하고, 고객 하나를 지웠다. 그러자 `NOT EXISTS` 고아 조회에 `1 | 서울`, `2 | 부산` 두 행이 나왔다.
- **원인**
  - 값 객체는 정체성이 없다. 그런데 테이블로 만들며 id를 붙였다.
  - 그러자 공유·수명 관리가 필요해졌다. 주인이 사라지거나 값이 바뀌어도 옛 행을 지울 책임자가 없다.
- **대처**
  - 1개면 Embedded Value로 주인 테이블에 편다.
  - 여러 개면 부모와 수명을 같이하는 Dependent Mapping(`@ElementCollection` 또는 `orphanRemoval = true`)으로 한다.
  - 이미 쌓인 고아는 위 쿼리로 정리한다. 이때 FK 방향(주인 → 값)을 바꿔 값 행이 주인 id를 들게 하면, 주인 삭제 시 `ON DELETE CASCADE`로 같이 지울 수 있다.

### 4. JSON LOB에 넣은 필드로 검색 요구 발생 → 풀스캔

- **현상**: "쿠폰 C42를 쓴 주문"을 찾는 관리자 화면이 수 초 걸린다.
- **보이는 형태** (로컬 재현, PostgreSQL 17.11, 20만 행)

```text
  WHERE extra->>'coupon' = 'C42'
    Parallel Seq Scan on orders ... Rows Removed by Filter: 99980          ← 인덱스 전
    Bitmap Index Scan on orders_coupon                                    ← CREATE INDEX ON orders ((extra->>'coupon'))
  WHERE extra @> '{"coupon":"C42"}'
    Seq Scan (표현식 인덱스로는 안 된다) → GIN (jsonb_path_ops) 만들자 Bitmap Index Scan
```

  - MySQL 8.4.10: `extra->>'$.coupon' = 'C42'`가 `Table scan`이다. `((CAST(extra->>'$.coupon' AS CHAR(20)) COLLATE utf8mb4_bin))` 함수 인덱스를 만든 뒤 `Index lookup`으로 바뀌었다(로컬 재현).
- **원인**
  - Serialized LOB 안은 DB에게 컬럼이 아니다. 인덱스·통계·제약이 없다.
  - 인덱스는 **질의 모양마다** 따로 필요하다. PG 표현식 인덱스는 `->>` 등호에만, GIN은 `@>`에만 맞았다.
- **대처**
  - 검색·조인·제약이 필요한 필드는 **컬럼으로 승격**한다(생성 컬럼 또는 정식 컬럼 + 백필).
  - 당장은 질의 모양에 맞는 표현식·함수·GIN 인덱스를 둔다.
  - JSON 안의 값에는 컬럼처럼 FK·NOT NULL을 직접 선언할 수 없다. 존재·타입 검사는 CHECK로 걸 수 있다. PG 17은 `CHECK (extra ? 'coupon')` 같은 식(로컬 재현에서 위반 거부), MySQL 8.4는 `CHECK (JSON_SCHEMA_VALID(…))`(MySQL 8.4 14.17.7)다. FK가 필요한 값은 컬럼으로 꺼낸다.

### 5. 단방향 `@OneToMany`가 조인 테이블을 만들고 전부 지웠다 다시 넣는다

- **현상**: 주문 줄 하나를 지웠을 뿐인데 SQL 로그에 DELETE 한 번과 INSERT 여러 번이 찍힌다. 스키마에 `order_lines` 같은 생각지 않은 연결 테이블이 있다.
- **보이는 형태**: `DELETE FROM Person_Phone WHERE Person_id = 1` 뒤에 남은 원소 수만큼 `INSERT INTO Person_Phone`(Hibernate 6.6 문서의 예).
- **원인**
  - JPA는 단방향 `@OneToMany`의 기본 매핑으로 조인 테이블을 쓴다(Jakarta Persistence 3.1 2.11.5.1).
  - 부모 쪽은 개별 연결 행을 식별하지 못한다. 그래서 Hibernate는 연결 행을 모두 지우고 다시 넣는다(Hibernate 6.6 3.8.2).
- **대처**
  - 자식 쪽 `@ManyToOne` + 부모 쪽 `mappedBy`의 양방향으로 바꾼다. 자식 테이블의 FK가 관계를 소유한다.
  - 단방향을 유지하려면 `@JoinColumn`으로 FK 매핑을 명시한다.

## 핵심 문장

- O-R 구조 매핑은 정체성·참조·컬렉션·값 객체·상속이라는 다섯 가지 모양 차이를 테이블 모양으로 바꾸는 패턴 모음이다(PoEAA 12장).
- 1:N은 "여러" 쪽 테이블에 FK, N:M은 연결 테이블이다. JPA 단방향 `@OneToMany`는 기본으로 연결 테이블을 만든다.
- 값 객체는 주인 테이블 컬럼으로 편다(Embedded Value). 별도 테이블로 빼고 주인이 그 id를 FK로 들면 식별자와 고아 행이 생긴다.
- 단일 테이블 상속은 조회가 싸지만 하위 컬럼 NOT NULL을 못 건다(조건부 CHECK로 보완). 클래스 테이블은 제약이 살지만 조인이 늘고, 구체 테이블은 다형 조회에 UNION이 든다.
- Serialized LOB(JSON)는 스키마 유연성과 맞바꿔 검색·제약을 잃는다. 검색 요구가 생기면 인덱스로 버티거나 컬럼으로 승격한다.

## 관련 주제·근거

- 선행
  - database [25-data-source-patterns](../25-data-source-patterns/2-summary.md) — 누가 SQL을 아는가.
  - [03-normalization](../03-normalization/2-summary.md) — 1NF와 반정규화
- 연결
  - [28-key-strategy-surrogate-natural-public-id](../28-key-strategy-surrogate-natural-public-id/2-summary.md) — 대리키·자연키·UUID
  - database `23-orm-and-n-plus-one` — 원고: [engineering/data-access](../../engineering/data-access/)
  - [52-offline-concurrency-patterns](../52-offline-concurrency-patterns/2-summary.md) — aggregate 단위 버전
  - [data-structure/08-graph](../../data-structure/08-graph/2-summary.md) · [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)
- 책·명세·문서
  - Martin Fowler, 『Patterns of Enterprise Application Architecture』(2002), 12장 Object-Relational Structural Patterns — Identity Field, Foreign Key Mapping, Association Table Mapping, Dependent Mapping, Embedded Value, Serialized LOB, Single/Class/Concrete Table Inheritance. 온라인 카탈로그 요약 <https://martinfowler.com/eaaCatalog/> (본문 12장은 카탈로그 요약 경유로만 확인)
  - Jakarta Persistence 3.1(2022-03-04) — 2.11.5.1 단방향 OneToMany 기본 조인 테이블, 2.13 상속 전략 3종과 단점·지원 의무, `@Inheritance` 기본 `SINGLE_TABLE`, `@DiscriminatorColumn` 기본 `DTYPE`·STRING·31 <https://jakarta.ee/specifications/persistence/3.1/jakarta-persistence-spec-3.1.html>
  - Hibernate ORM 6.6 User Guide — 3.2.40 JSON mapping(`@JdbcTypeCode(SqlTypes.JSON)`), 3.3 Embeddable, 3.7.10 IDENTITY 컬럼(INSERT 배치 불가), 3.8.2 단방향 `@OneToMany`의 전부 삭제 후 재삽입, 3.10 Natural Id, 3.14 상속(Table per class의 `UNION ALL`) <https://docs.jboss.org/hibernate/orm/6.6/userguide/html_single/Hibernate_User_Guide.html>
  - PostgreSQL 17 문서 11.7 Indexes on Expressions, 8.14.4 jsonb Indexing(`jsonb_path_ops`) <https://www.postgresql.org/docs/17/datatype-json.html>
  - PostgreSQL 17 5.11 Inheritance <https://www.postgresql.org/docs/17/ddl-inherit.html>
  - MySQL 8.4 14.17.7 JSON Schema Validation Functions(`JSON_SCHEMA_VALID()`와 CHECK) <https://dev.mysql.com/doc/refman/8.4/en/json-validation-functions.html>
  - Hibernate ORM 6.6 소스 `hibernate-core/src/main/java/org/hibernate/collection/spi/PersistentSet.java` `getDeletes` — 빠진 원소만 삭제 대상
  - MySQL 8.4 Reference Manual 15.1.15 CREATE INDEX — Functional Key Parts(JSON 값 CAST와 collation) <https://dev.mysql.com/doc/refman/8.4/en/create-index.html>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): 단일 테이블 조건부 CHECK 위반 거부, 값 객체 별도 테이블의 고아 행 2개, 20만 행 JSON 필드 검색의 Seq Scan → 표현식 인덱스 → `@>`에는 GIN 필요, Class Table 조인 계획, MySQL JSON 함수 인덱스 전후 `Table scan` → `Index lookup`
