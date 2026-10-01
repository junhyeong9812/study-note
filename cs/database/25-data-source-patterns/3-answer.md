# database/25-data-source-patterns — 정답

## 정답

### 1. SQL이 흩어지면

- 규칙을 테스트하려면 DB가 필요해진다. 규칙과 SQL이 한 메서드에 엉켜 있기 때문이다.
- 스키마가 바뀌면 SQL이 있는 서비스 곳곳을 고쳐야 한다.
- DBA가 튜닝할 SQL을 찾기 어렵다. Fowler Table Data Gateway 설명: SQL에 익숙하지 않은 개발자도 많고, DBA는 SQL을 쉽게 찾아 튜닝할 수 있어야 한다.

### 2. 네 패턴 비교 (PoEAA 10장)

| 패턴 | SQL을 아는 자 | 인스턴스 하나 = | 도메인 로직 |
|---|---|---|---|
| Table Data Gateway | 게이트웨이 | 테이블(뷰) 전체 | 바깥(서비스·스크립트) |
| Row Data Gateway | 게이트웨이 | 행 하나 | 바깥 |
| Active Record | 도메인 객체 자신 | 행 하나 | 그 객체 안 |
| Data Mapper | 매퍼 층 | (매퍼는 도메인 객체와 분리) | 보통 도메인 객체 안(Domain Model과 짝), DB를 모름 — 패턴이 정하는 것은 분리이지 로직 위치는 아니다 |

### 3. Active Record와 테스트

- 규칙 메서드가 `find()`·`save()`를 부르면, 규칙만 테스트하려 해도 DB가 필요하다. 규칙(`cancel()`)과 저장(`save()`)을 나눠 두면 Active Record여도 규칙만 따로 테스트할 수 있다. 테스트가 느려지고, 데이터 준비가 필요하다.
- Fowler(Row Data Gateway 설명):
  - 인메모리 객체에 DB 조작 코드를 넣으면, 객체에 비즈니스 로직이 있을 때 복잡도가 커진다.
  - 객체가 DB에 묶이면 DB 접근 때문에 테스트가 느리고 불편하다.
- 대처: 규칙을 DB 접근 없는 메서드(값을 받고 결과를 돌려줌)로 먼저 뽑는다. 커진 부분부터 Data Mapper + Repository로 옮긴다.

### 4. JPA/Hibernate의 정체

- **Data Mapper**: 엔티티와 DB 사이의 매퍼 층이 Hibernate다.
- **Metadata Mapping**: `@Entity`·`@Column`·`@OneToMany`(또는 `orm.xml`)가 객체–관계 매핑 메타데이터다. `@Column`은 필드↔컬럼, `@OneToMany`는 연관↔외래 키(또는 조인 테이블)를 선언한다. 범용 코드가 이것을 읽어 SQL을 만든다.
- **Identity Map·Unit of Work·Lazy Load**(11장): 영속성 컨텍스트·flush·프록시([23](../23-orm-and-n-plus-one/2-summary.md)).
- **Query Object**: JPA Criteria API(명세 6장).

### 5. Repository vs Data Mapper

- Data Mapper: 객체↔테이블 **변환**을 맡는 층이다. SQL과 매핑을 안다.
- Repository: 그 앞에서 도메인이 보는 **컬렉션 모양 인터페이스**다. 쿼리 명세를 받아 결과를 돌려주고, 객체를 더하고 뺀다. 뒤에서 매퍼가 실제 일을 한다.
- 한 방향 의존: **매핑 층(Repository 구현) → 도메인** 방향만 있다. 매핑 층이 도메인을 알고, 도메인은 매핑 층을 모른다. 도메인이 보는 것은 자기 쪽에 둔 Repository 인터페이스뿐이다. 인터페이스는 도메인 쪽에 두고 구현은 인프라 쪽에 둔다.

### 6. Query Object 트리

```text
             AND
            /    \
  EQ(status,'PAID')  OR
                    /  \
       GT(amount,1000)  EQ(vip,true)
```

- 재귀 방문: 노드마다 왼쪽 → 연산자 → 오른쪽으로 SQL 조각을 잇는다. OR 노드는 괄호로 감싼다. 리프에서 값을 바인딩 목록에 넣는다.
- 결과: `status = ? AND (amount > ? OR vip = ?)`, 바인딩 `[PAID, 1000, true]`(로컬에서 Java 21로 실행해 확인).
- 컬럼 이름: 코드가 정한 값(엔티티 메타데이터·화이트리스트)만 쓴다.
- 값: 사용자 입력은 **바인딩(`?`)으로만** 넣는다. 문자열로 이어 붙이면 SQL 주입이 된다.

### 7. 비대한 리포지토리

- 원인: 조건 조합을 이름 파생 쿼리로 표현했다. 조합이 늘 때마다 메서드가 는다. Spring Data JPA 문서도 이름이 "불필요하게 흉해지는" 경우를 한계로 적고, `@Query`·이름 있는 쿼리를 권한다.
- 대처:
  - 조건은 Query Object(`Specification`·Criteria·QueryDSL)로 조립한다. 작은 조건 조각을 `and`/`or`로 조합한다.
  - 화면용 복잡 조회는 별도 조회 층(DTO 프로젝션·`JdbcClient`)으로 뺀다.
  - 리포지토리에는 애그리게이트 저장·로드와 몇 개의 핵심 조회만 남긴다.

### 8. 도메인이 ORM에 묶임

- 문제: Data Mapper의 약속("도메인 객체는 DB를 모른다")이 깨진다.
  - 도메인만 따로 빌드·테스트하기 어렵다.
  - 지연 로딩 프록시·더티 체킹 같은 ORM 런타임 동작이 규칙의 결과에 스며든다(`LazyInitializationException`, 프록시 때문에 틀리는 `equals`).
- 선택지:
  1. 어노테이션을 그대로 둔다. 가장 실용적이다. 대신 규칙 코드가 ORM 런타임 동작에 기대지 않도록 규율로 지킨다.
  2. `orm.xml`로 매핑을 클래스 밖에 둔다(Jakarta Persistence 3.1 12장). 도메인 클래스는 깨끗하다. 대신 XML 유지비와 리팩터링 도구 지원 약화를 치른다.
  3. 영속 모델(`OrderEntity`)과 도메인 모델(`Order`)을 분리하고 매퍼로 변환한다. 가장 순수하다. 대신 이중 모델과 변환 코드를 치른다. 도메인 객체의 변경은 Hibernate가 직접 추적하지 않으므로, 변경을 관리 상태의 `OrderEntity`에 옮겨 적어야 더티 체킹이 돈다.

### 9. 한 시스템, 두 모양

- 관리자 CRUD: 테이블과 화면이 거의 1:1이고 규칙이 적다. Active Record나 게이트웨이(또는 단순 리포지토리 + 엔티티)로 코드를 줄인다.
- 정산 도메인: 규칙이 크고 객체 구조가 테이블과 다르다(값 객체·상태 전이). DB 없이 규칙을 테스트해야 한다. Data Mapper + Repository를 쓰고, 조회는 별도 조회 층으로 둔다.
- 기준: **도메인 로직의 복잡도**와 **객체–스키마 불일치의 크기**, 그리고 **DB 없이 테스트해야 하는가**. 패턴의 우열이 아니다. 한 시스템 안에서 영역마다 달리 고를 수 있다.
