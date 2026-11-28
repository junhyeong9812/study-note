# java/java-jpa/02 — @OneToOne 매핑 — 정리 (힌트)

> 출처 — study-site 항목 `java/jpa-mapping-onetoone`(항목 데이터 `data/java/jpa-database.json`) · 정답 코드 study-practice `java/java-jpa/reference/jpa-mapping-onetoone.java`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**`@OneToOne` 은 「회원증에 적힌 사물함 번호」다.**
회원증(회원 행)에는 사물함 번호 칸이 있고, 그 번호로 사물함을 찾아간다.
사물함 쪽에는 주인 이름 칸이 없다.
「이 사물함을 누가 쓰나」를 알려면 회원증 묶음을 뒤져 그 번호가 적힌 카드를 찾아야 한다.
한 번호는 한 회원증에만 적을 수 있어서(중복 금지) 회원과 사물함은 하나 대 하나로 맞물린다.
JPA 의 `@OneToOne` 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 회원증 | `Member` 엔티티 / `members` 테이블의 한 행 |
| 사물함 | `Locker` 엔티티 / `Locker` 테이블의 한 행 |
| 회원증에 적힌 사물함 번호 | 외래키(FK) 컬럼 `locker_id` |
| 「한 번호는 한 카드에만」 규칙 | `@JoinColumn(unique = true)` |
| 사물함에서 주인을 찾으려고 회원증 묶음을 뒤지는 일 | `mappedBy` 쪽 필드를 채우려고 `members` 테이블을 조회하는 일 |

```text
 members 테이블                    Locker 테이블
┌────┬───────┬───────────┐        ┌────┬──────────┐
│ id │ name  │ locker_id │──FK──► │ id │ location │
├────┼───────┼───────────┤        ├────┼──────────┤
│ 1  │ 민수  │    7      │──────► │ 7  │ 2층 A-3  │
│ 2  │ 지영  │   NULL    │        └────┴──────────┘
└────┴───────┴───────────┘        (주인을 가리키는 칸이 없다)
```

> **엔티티** — 테이블의 한 행에 대응하도록 `@Entity` 를 붙인 자바 클래스.\
> 예: `Member` 객체 하나가 `members` 테이블의 행 하나다.

> **외래키(FK)** — 다른 테이블 행의 기본키 값을 담아 그 행을 가리키는 컬럼.\
> 예: `members.locker_id = 7` 은 `Locker` 테이블의 `id = 7` 행을 가리킨다.

> **기본키(PK)** — 한 테이블 안에서 행 하나를 콕 집어내는 고유한 값.\
> 예: `@Id private Long id;`

## 이 주제가 답하려는 질문

1. 일대일 관계에서 FK 컬럼은 어느 테이블에 두고, 그 위치가 무엇을 바꾸나?
2. 양쪽 엔티티가 서로를 참조(양방향)하면 FK 값은 어느 쪽 필드가 책임지나?
3. `fetch = FetchType.LAZY` 를 적었는데도 바로 조회되는 쪽은 어디이고 왜 그런가?
4. FK 컬럼을 따로 두지 않고 기본키 자체를 공유(`@MapsId`)하면 무엇이 달라지나?

## 동작 방식

### (1) 단방향 — FK 를 가진 쪽에서만 참조한다

**언제 쓰나** — 한쪽에서만 상대를 꺼내 보면 될 때 쓴다.
예제의 `User` 는 `getProfile()` 로 프로필을 꺼내지만, `UserProfile` 은 자기가 누구의 프로필인지 몰라도 된다.

```text
User.profile 필드
  @OneToOne(fetch = LAZY, cascade = ALL)
  @JoinColumn(name = "user_profile_id", unique = true)
        │
        ▼
User 테이블에 user_profile_id 컬럼이 생긴다 (FK + UNIQUE)
        │
        ▼
자바에서는 user.getProfile() 한 방향으로만 간다
UserProfile 클래스에는 User 필드가 없다
```

- `@OneToOne` 은 「이 필드는 상대 엔티티 하나를 가리킨다」고 알린다.
- `@JoinColumn(name = "user_profile_id")` 은 FK 컬럼 이름을 정하고, 그 컬럼이 이 엔티티(`User`)의 테이블에 생긴다는 뜻이다.
- `unique = true` 는 같은 프로필 id 가 두 사용자 행에 들어가지 못하게 막아 일대일을 DB 차원에서 지킨다.
- `UserProfile` 쪽에는 아무 매핑이 없으므로 프로필에서 사용자로 가는 길은 없다.

> **단방향 연관관계** — 두 엔티티 중 한쪽만 상대를 필드로 들고 있는 관계.\
> 예: `User` 에는 `profile` 필드가 있고 `UserProfile` 에는 `user` 필드가 없다.

### (2) 양방향 — 주인과 거울

**언제 쓰나** — 양쪽에서 서로를 꺼내 봐야 할 때 쓴다.
예제의 `Member` 는 `getLocker()` 로, `Locker` 는 `getMember()` 로 상대를 꺼낸다.

```text
Member.locker   @OneToOne + @JoinColumn(name = "locker_id")   ← 주인 (FK 를 쓴다)
Locker.member   @OneToOne(mappedBy = "locker")                ← 거울 (읽기 전용)
        │
        ▼
DB 에 FK 컬럼은 members.locker_id 하나뿐이다
        │
        ▼
members.locker_id 값은 Member.locker 필드만 보고 정해진다
Locker.member 를 바꿔도 DB 에는 아무것도 쓰이지 않는다
```

- 양방향이어도 DB 에는 FK 컬럼이 하나뿐이라서, 그 컬럼을 책임질 필드를 한쪽으로 정해야 한다.
- `@JoinColumn` 을 단 `Member.locker` 가 그 책임자, 곧 연관관계의 주인이다.
- `mappedBy = "locker"` 는 「나는 상대 클래스의 `locker` 필드가 관리하는 관계를 비춰 볼 뿐이다」라는 뜻이다.
- 그래서 `Locker.member` 에만 값을 넣으면 객체 안에서는 연결된 듯 보여도 `locker_id` 는 채워지지 않는다.

> **양방향 연관관계** — 두 엔티티가 서로를 필드로 들고 있는 관계.\
> 예: `Member.locker` 와 `Locker.member`.

> **연관관계의 주인** — 양방향 관계에서 FK 값을 실제로 쓰고 바꾸는 쪽 필드.\
> 예: `Member.locker` 를 바꾸면 커밋 때 `members.locker_id` 가 바뀐다.

> **`mappedBy`** — 「이 관계의 주인은 상대 클래스의 이 필드다」라고 적는 속성. 붙은 쪽은 읽기 전용이 된다.\
> 예: `@OneToOne(mappedBy = "locker")`

**편의 메서드로 양쪽을 한 번에 맞춘다.**
DB 는 주인 쪽만 보지만, 같은 트랜잭션 안의 자바 객체는 양쪽 필드를 따로 들고 있다.
한쪽만 바꾸면 객체끼리 말이 어긋난다.
그래서 `Member.assignLocker()` 는 `this.locker = locker;` 와 `locker.setMember(this);` 를 함께 부른다.
`Locker.setMember()` 는 접근 제한자가 없는 패키지-프라이빗이라, 바깥 코드가 거울 쪽만 따로 바꾸는 일을 줄인다.

```text
member.assignLocker(locker)
   ├─ this.locker = locker        → 주인 쪽: 커밋 때 locker_id 가 쓰인다
   └─ locker.setMember(this)      → 거울 쪽: SQL 은 없지만 locker.getMember() 가 맞는 값을 돌려준다
```

> **편의 메서드** — 양방향 관계의 두 필드를 한 번에 맞춰 주는 메서드.\
> 예: `assignLocker(locker)` 가 `Member.locker` 와 `Locker.member` 를 함께 채운다.

### (3) cascade 와 orphanRemoval — 저장 · 삭제를 따라가게 하기

**언제 쓰나** — 대상 엔티티의 생애가 주 엔티티에 딸려 있을 때 쓴다.
사물함 배정은 회원에게 딸린 것이라, 회원을 통해 만들고 회원을 통해 지운다.

```text
MemberService.assignLocker(memberId, location)    (@Transactional 안)
   ├─ memberRepository.findById(memberId)  → 영속 상태 Member (없으면 orElseThrow 로 예외)
   ├─ Locker.create(location)              → 비영속 Locker (아직 DB 와 무관)
   └─ member.assignLocker(locker)          → 주인 필드에 비영속 Locker 를 연결
        │
        ▼
트랜잭션 커밋 → 플러시 → 변경 감지: Member.locker 가 바뀌었다
        │
        ▼
cascade = ALL 이 저장을 Locker 로 전파 → Locker INSERT
그리고 members.locker_id 에 새 Locker 의 id 가 들어간다
```

- `findById` 로 가져온 `Member` 는 트랜잭션 안에서 영속 상태다.
- 영속 상태 엔티티의 필드 변경은 커밋 때 플러시되면서 변경 감지로 SQL 이 된다.
- 이때 새로 걸린 `Locker` 는 비영속이지만 `cascade = CascadeType.ALL` 이 저장을 전파하므로 따로 `save` 를 부르지 않아도 INSERT 된다.
- `User.setProfile()` 도 같은 원리라서, 비영속 `UserProfile` 을 넣어도 함께 INSERT 된다.

```text
member.removeLocker()
   ├─ this.locker.setMember(null)   → 거울 쪽을 먼저 끊는다
   └─ this.locker = null            → 주인 쪽을 끊는다
        │
        ▼
커밋 → members.locker_id 를 NULL 로 바꾼다
     → 부모를 잃은 Locker 는 orphanRemoval = true 때문에 DELETE
```

- `orphanRemoval = true` 는 「주인 필드에서 떨어져 나간 대상 엔티티는 지운다」는 뜻이다.
- `removeLocker()` 는 `null` 검사를 먼저 해서 사물함이 없는 회원에게 불러도 아무 일 없이 끝난다.

> **영속성 컨텍스트** — 트랜잭션 동안 엔티티를 담아 두고 변경을 지켜보는 JPA 의 보관소.\
> 예: `findById` 로 꺼낸 `Member` 는 여기에 담겨 있다.

> **영속 / 비영속** — 영속성 컨텍스트가 관리하는 상태 / 아직 관리 밖에 있는 막 만든 객체.\
> 예: `Locker.create(...)` 로 막 만든 `Locker` 는 비영속이다.

> **변경 감지** — 커밋(플러시) 때 영속 엔티티의 처음 값과 지금 값을 비교해 바뀐 만큼 UPDATE · INSERT 를 만드는 동작.\
> 예: `member.locker` 를 바꾸기만 해도 커밋 때 `locker_id` 가 갱신된다.

> **cascade** — 한 엔티티에 한 저장 · 삭제 같은 작업을 연관된 엔티티로 전파하는 설정.\
> 예: `cascade = CascadeType.ALL`

> **orphanRemoval** — 부모 엔티티의 참조에서 빠진 자식 엔티티를 자동으로 지우는 설정.\
> 예: `this.locker = null;` 뒤 커밋하면 그 `Locker` 행이 지워진다.

### (4) mappedBy 쪽에서 LAZY 가 깨지는 까닭

**언제 쓰나** — `fetch = FetchType.LAZY` 를 양방향 일대일의 어느 쪽에 기대할 수 있는지 판단할 때 쓴다.

```text
Member 를 읽는다 → 그 행에 locker_id 칸이 있다
   locker_id = 7     → "사물함이 있다" → id 7 짜리 Locker 프록시를 넣어 둔다 → 실제 SELECT 는 나중에
   locker_id = NULL  → "사물함이 없다" → null 을 넣는다

Locker 를 읽는다 → 그 행에 회원을 가리키는 칸이 없다
   member 가 있나? 없나? → members 테이블을 봐야만 안다
   → 프록시를 넣을지 null 을 넣을지 정하려면 결국 바로 조회해야 한다 → EAGER 처럼 된다
```

- 지연 로딩은 필드에 「나중에 채울 대리 객체(프록시)」를 넣어 두는 방식이다.
- 그런데 일대일에서는 상대가 없으면 필드가 `null` 이어야 하고, 있으면 프록시여야 한다.
- FK 를 가진 쪽(`Member`)은 자기 행의 `locker_id` 만 보고 둘 중 하나를 고를 수 있다.
- `mappedBy` 쪽(`Locker`)은 자기 행에 그런 칸이 없어 고를 근거가 없다.
- 그래서 `Locker.member` 에 `fetch = FetchType.LAZY` 를 적어도, 원본의 말대로 「항상 EAGER 로 조회될 수 있다」.
- 이 동작은 JPA 구현체가 프록시를 만드는 방식에서 나오는 것이다 — 「구현 세부사항 대 언어 보장」을 보라.

> **지연 로딩(LAZY)** — 연관 엔티티를 실제로 만질 때까지 조회를 미루는 방식.\
> 예: `member.getLocker().getLocation()` 을 부를 때 비로소 `Locker` 를 SELECT 한다.

> **즉시 로딩(EAGER)** — 엔티티를 읽을 때 연관 엔티티도 바로 함께 읽는 방식.\
> 예: `Locker` 를 읽자마자 그 사물함의 `Member` 까지 조회한다.

> **프록시** — 진짜 엔티티 대신 자리를 지키다가, 처음 쓰일 때 DB 에서 내용을 채우는 대리 객체.\
> 예: `Member` 를 읽은 직후 `locker` 필드에 들어 있는 `Locker` 껍데기.

**FK 위치에 따른 장단점**은 이 절에서 나온다.

| FK 를 두는 곳 | 좋은 점 | 아쉬운 점 |
|---|---|---|
| 주 테이블(자주 읽는 쪽, 예: `members.locker_id`) | 주 엔티티를 읽을 때 FK 값만 보고 대상 유무를 안다 → 주 엔티티 쪽 LAZY 가 정상 동작한다 | 양방향이면 대상 쪽(`Locker.member`)이 `mappedBy` 가 되어 그쪽 LAZY 는 깨질 수 있다 |
| 대상 테이블(예: `Locker` 테이블에 회원 FK) | 대상 엔티티 쪽에서 주인 노릇을 한다 | 주 엔티티 쪽 필드가 `mappedBy` 가 되어, 자주 읽는 주 엔티티를 읽을 때마다 대상까지 조회될 수 있다 |

원본 팁의 처방은 둘이다.
하나는 `@MapsId` 로 PK 를 공유하는 것(다음 절), 하나는 거울 쪽 필드를 없애 단방향으로 설계하는 것이다(1절의 `User` → `UserProfile`).

### (5) `@MapsId` — 기본키를 공유한다

**언제 쓰나** — 대상 엔티티가 주 엔티티 없이는 존재할 까닭이 없고, 둘을 같은 id 로 묶고 싶을 때 쓴다.
예제의 `UserDetail` 은 어떤 `User` 의 상세 정보이므로 그 `User` 의 id 를 그대로 쓴다.

```text
UserDetail
  @Id private Long id;                     ← @GeneratedValue 가 없다
  @OneToOne(fetch = LAZY) @MapsId
  @JoinColumn(name = "id") private User user;
        │
        ▼
UserDetail.create(user, phone) 로 user 를 넣는다
        │
        ▼
저장할 때 UserDetail.id ← user 의 id
UserDetail 테이블의 id 컬럼 = 기본키이면서 User 를 가리키는 FK
        │
        ▼
FK 컬럼을 따로 만들 필요가 없다
```

- `@MapsId` 는 「연관 엔티티(`User`)의 PK 를 내 PK 로 쓴다」는 뜻이다.
- 그래서 `id` 에 `@GeneratedValue` 를 달지 않는다 — 값은 스스로 만들지 않고 `User` 에게서 받는다.
- `@JoinColumn(name = "id")` 로 PK 컬럼 하나가 FK 노릇까지 한다.
- `UserDetail.create()` 가 `User` 를 인자로 받는 까닭도 여기 있다 — `User` 없이는 id 를 정할 수 없다.
- `UserDetail.user` 는 FK 를 가진 쪽이라 지연 로딩이 정상 동작한다.

> **`@MapsId`** — 연관된 엔티티의 기본키를 자기 기본키로 가져다 쓰게 하는 어노테이션.\
> 예: `UserDetail.id` 가 `User.id` 와 같은 값이 된다.

## 문법 — 형태와 규칙

```java
// 최소 예제: 자동차(주) — 엔진(대상), FK 는 Car 쪽
@Entity
public class Car {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;

    @OneToOne(fetch = FetchType.LAZY, cascade = CascadeType.ALL, orphanRemoval = true)
    @JoinColumn(name = "engine_id", unique = true)   // Car 테이블에 FK
    private Engine engine;                           // 연관관계의 주인
}

@Entity
public class Engine {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;

    @OneToOne(mappedBy = "engine", fetch = FetchType.LAZY)  // 거울 — LAZY 가 깨질 수 있다
    private Car car;
}
```

| 쓰는 것 | 붙는 자리 | 뜻 |
|---|---|---|
| `@OneToOne` | 상대 엔티티를 담는 필드 | 일대일 관계 |
| `fetch = FetchType.LAZY` | `@OneToOne` 속성 | 지연 로딩 요청 (FK 쪽에서만 믿을 수 있다) |
| `cascade = CascadeType.ALL` | `@OneToOne` 속성 | 저장 · 삭제 등을 상대에게 전파 |
| `orphanRemoval = true` | `@OneToOne` 속성 | 참조가 끊긴 상대를 삭제 |
| `mappedBy = "필드명"` | 거울 쪽 `@OneToOne` | 주인이 상대 클래스의 그 필드임을 밝힘 |
| `@JoinColumn(name = "...", unique = true)` | 주인 쪽 필드 | FK 컬럼 이름 · 중복 금지 |
| `@MapsId` | 상대를 담는 필드 | 상대의 PK 를 내 PK 로 공유 |
| `@GeneratedValue(strategy = GenerationType.IDENTITY)` | `@Id` 필드 | id 를 DB 의 자동 증가로 만든다 |
| `@Column(nullable = false)` | 일반 필드 | NOT NULL 컬럼 |
| `@Table(name = "members")` | 엔티티 클래스 | 테이블 이름 지정 |

- `@JoinColumn` 을 단 쪽이 FK 를 가진 쪽이고, 양방향이면 그쪽이 주인이다.
- `mappedBy` 의 값은 상대 클래스의 **필드 이름**이지 컬럼 이름이 아니다.
- `mappedBy` 와 `@JoinColumn` 을 한 필드에 함께 쓰지 않는다.
- 일대일을 DB 에서도 지키려면 FK 컬럼에 `unique = true` 를 준다.
- 엔티티에는 `protected` 기본 생성자를 두고, 객체는 정적 팩토리(`create(...)`)로 만든다 — 예제 전체가 이 꼴이다.
- `@MapsId` 를 쓰는 엔티티의 `@Id` 에는 `@GeneratedValue` 를 붙이지 않는다.

> **IDENTITY 전략** — 기본키 값을 DB 의 자동 증가 기능에 맡기는 생성 방식.\
> 예: `@GeneratedValue(strategy = GenerationType.IDENTITY)`

> **정적 팩토리** — 생성자 대신 객체를 만들어 돌려주는 `static` 메서드.\
> 예: `Locker.create("2층 A-3")`

## 어디서 틀리나

### 1. `mappedBy` 쪽에 `LAZY` 를 적고 안심한다

원본 팁 그대로, FK 를 가진 쪽만 지연 로딩이 정상 동작한다.
`Locker.member` 처럼 `mappedBy` 쪽은 프록시를 만들 근거가 없어 항상 즉시 조회될 수 있다.
`Locker` 를 목록으로 많이 읽으면 사물함마다 회원 조회가 붙을 수 있다.
피하는 길은 `@MapsId` 로 PK 를 공유하거나, 거울 쪽 필드를 없애 단방향으로 설계하는 것이다.

### 2. 거울 쪽에만 값을 넣는다

`locker.setMember(member)` 만 하고 `member.locker` 를 비워 두면 `locker_id` 는 채워지지 않는다.
DB 는 주인 쪽 필드만 본다.

### 3. 주인 쪽에만 값을 넣는다

`member.locker = locker` 만 하면 DB 는 맞게 바뀌지만, 같은 트랜잭션 안에서 `locker.getMember()` 는 `null` 이다.
객체 상태와 DB 상태가 어긋나므로 편의 메서드(`assignLocker`)로 양쪽을 함께 맞춘다.
끊을 때도 `removeLocker()` 처럼 양쪽을 함께 끊는다.

### 4. `unique = true` 를 빠뜨린다

빠지면 FK 컬럼에 같은 값이 여러 행에 들어갈 수 있어 DB 차원에서는 일대다가 된다.
자바 쪽 `@OneToOne` 만으로는 DB 가 막아 주지 않는다.

### 5. `@MapsId` 엔티티에 `@GeneratedValue` 를 붙인다

PK 값은 `User` 에게서 받는 것이라 스스로 만들 값이 아니다.
`UserDetail` 을 `User` 없이 만들려 해도 id 를 정할 길이 없다.

### 6. cascade 를 믿고 영속 상태가 아닌 부모에 건다

`save` 없이 `Locker` 가 저장되는 것은 `Member` 가 트랜잭션 안의 영속 엔티티이고, 커밋 때 변경 감지가 일어나기 때문이다.
`@Transactional` 밖에서 같은 코드를 쓰면 이 흐름이 성립하지 않는다.

### 7. 원본 주석과 코드가 맞지 않는 곳

- 원본의 주장: 「users 테이블에 user_profile_id FK 컬럼 생성」 → 왜 의심스러운가: `User` 에는 `@Table(name = "users")` 가 없다. 테이블 이름은 엔티티 이름과 명명 전략으로 정해지므로 `users` 가 된다는 근거가 코드에 없다 (확인 필요).
- 원본의 주장: `new EntityNotFoundException("Member", memberId)` → 왜 의심스러운가: 표준 `jakarta.persistence.EntityNotFoundException` 은 메시지 문자열 하나를 받는 꼴로 알려져 있어, 두 인자 생성자는 직접 만든 예외 클래스를 전제한 것으로 보인다 (확인 필요).
- `MemberService` 의 `memberRepository` 는 선언 · 주입 코드가 없다.
- 한 파일에 `public class` 가 여럿이다 — 자바는 파일 하나에 `public` 최상위 클래스를 하나만 허용하므로 실제로는 파일을 나눠야 한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `mappedBy` 쪽 `@OneToOne` 은 `LAZY` 를 적어도 즉시 조회될 수 있다 | JPA 구현체(예: Hibernate)의 프록시 방식에서 나오는 동작 — JPA 표준이 「반드시 EAGER 가 된다」고 정한 것이 아니다 |
| FK 쪽 `LAZY` 는 프록시로 정상 동작한다 | 구현체의 동작 — 표준은 지연 로딩 방식을 프록시로 못 박지 않는다 |
| `cascade = ALL` 이면 비영속 대상도 함께 INSERT 된다 | JPA 표준의 cascade 규칙 |
| `orphanRemoval = true` 이면 끊긴 대상이 DELETE 된다 | JPA 표준 |
| `@MapsId` 로 PK 를 공유한다 | JPA 표준 |
| `IDENTITY` 는 DB 자동 증가로 id 를 만든다 | JPA 표준의 전략 이름 + 그것을 실제로 수행하는 DB 기능 |
| `@Transactional` 메서드 안에서 커밋 때 변경 감지가 일어난다 | `@Transactional` 은 Spring, 변경 감지는 JPA 영속성 컨텍스트 |
| 한 파일에 `public` 최상위 클래스는 하나 | 자바 언어 규칙 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 한쪽에서만 상대를 꺼내 보면 된다 | 단방향 `@OneToOne` + `@JoinColumn` | 습관적인 양방향 |
| 양쪽에서 서로를 꺼내야 한다 | 양방향 + 편의 메서드 | 한쪽 필드만 바꾸는 setter 호출 |
| 주 엔티티를 자주 읽고 대상은 가끔 쓴다 | FK 를 주 테이블에 두고 주 쪽 `LAZY` | FK 를 대상 테이블에 두기 (주 쪽이 `mappedBy` 가 된다) |
| 대상이 주 엔티티 없이 존재할 까닭이 없다 | `@MapsId` 로 PK 공유 | 별도 FK 컬럼 + 따로 만든 id |
| 대상의 생애가 주 엔티티에 딸려 있다 | `cascade = ALL` + `orphanRemoval = true` | 여러 주인이 함께 쓰는 대상에 `orphanRemoval` |
| 거울 쪽을 목록으로 많이 읽는다 | 단방향으로 바꾸거나 `@MapsId` | `mappedBy` 쪽 `LAZY` 에 기대기 |

## 핵심 문장

1. **FK 를 가진 쪽이 관계를 쓴다** — 양방향이면 `@JoinColumn` 쪽이 주인, `mappedBy` 쪽은 읽기 전용 거울이다.
2. **일대일 `LAZY` 는 FK 쪽에서만 믿을 수 있다** — `mappedBy` 쪽은 상대 유무를 몰라 프록시를 못 만들고 즉시 조회될 수 있다.
3. **FK 는 자주 읽는 주 테이블에 두는 것이 지연 로딩에 유리하다.**
4. **양방향은 편의 메서드로 양쪽을 함께 맞추고 함께 끊는다.**
5. **`@MapsId` 는 상대의 PK 를 내 PK 로 써서 FK 컬럼 없이 일대일을 만든다.**

## 관련 자료

- `jpa-entity` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `jpa-mapping-onetomany` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `jpa-cascade` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/java/jpa-database.json` 의 `jpa-mapping-onetoone`

## 용어 풀이

- **엔티티** — `@Entity` 를 붙여 테이블 행에 대응시킨 자바 클래스.
- **기본키(PK)** — 테이블 안에서 행 하나를 고유하게 가리키는 값.
- **외래키(FK)** — 다른 테이블 행의 PK 값을 담아 그 행을 가리키는 컬럼.
- **연관관계** — 엔티티가 다른 엔티티를 필드로 참조하는 관계.
- **단방향 연관관계** — 한쪽만 상대를 필드로 가진 관계.
- **양방향 연관관계** — 두 엔티티가 서로를 필드로 가진 관계.
- **연관관계의 주인** — 양방향에서 FK 값을 쓰고 바꾸는 쪽 필드.
- **`mappedBy`** — 관계의 주인이 상대 클래스의 어느 필드인지 밝히는 속성, 붙은 쪽은 읽기 전용.
- **편의 메서드** — 양방향의 두 필드를 한 번에 맞추는 메서드.
- **영속성 컨텍스트** — 트랜잭션 동안 엔티티를 담고 변경을 지켜보는 보관소.
- **영속 / 비영속** — 영속성 컨텍스트가 관리하는 상태 / 막 만들어 관리 밖에 있는 상태.
- **변경 감지** — 커밋 때 영속 엔티티의 바뀐 값을 찾아 SQL 로 만드는 동작.
- **cascade** — 저장 · 삭제 같은 작업을 연관 엔티티로 전파하는 설정.
- **orphanRemoval** — 부모의 참조에서 빠진 자식을 자동 삭제하는 설정.
- **지연 로딩(LAZY)** — 연관 엔티티를 실제로 쓸 때까지 조회를 미루는 방식.
- **즉시 로딩(EAGER)** — 엔티티를 읽을 때 연관 엔티티도 바로 읽는 방식.
- **프록시** — 진짜 엔티티 자리를 지키다 처음 쓰일 때 내용을 채우는 대리 객체.
- **`@MapsId`** — 연관 엔티티의 PK 를 자기 PK 로 공유하게 하는 어노테이션.
- **IDENTITY 전략** — PK 값을 DB 자동 증가에 맡기는 생성 방식.
- **정적 팩토리** — 생성자 대신 객체를 만들어 주는 `static` 메서드.

## 더 들어가면

- JPA 명세는 `FetchType.LAZY` 를 구현체에 주는 「힌트」로, `EAGER` 를 「요구」로 다룬다고 알려져 있다 — 그래서 `LAZY` 가 지켜지지 않아도 명세 위반이 아니다 (확인 필요).
- Hibernate 는 바이트코드 향상(bytecode enhancement)을 켜면 `mappedBy` 쪽 일대일도 지연 로딩할 수 있다고 알려져 있다 (확인 필요).
- FK 를 대상 테이블에 두면, 나중에 관계가 일대다로 바뀔 때 테이블 구조를 그대로 둘 수 있다는 장점이 흔히 꼽힌다 (확인 필요).
- `user` 는 일부 DB 에서 예약어라 엔티티 이름이 `User` 이면 테이블 이름을 `@Table` 로 따로 주는 경우가 많다 (확인 필요).
- `removeLocker()` 뒤 커밋할 때 FK 를 `NULL` 로 바꾸는 UPDATE 와 `Locker` 의 DELETE 가 어떤 차례로 나가는지는 구현체의 플러시 순서에 달려 있다 (확인 필요).
- `optional = false` 를 주면 구현체가 「상대가 반드시 있다」고 보고 프록시를 쓸 수 있다는 설명이 있지만, `mappedBy` 쪽에서 통하는지는 구현체마다 다르다 (확인 필요).
