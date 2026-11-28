# java/java-jpa/02 — @OneToOne 매핑 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `Member` 만 읽히고, `locker` 에는 프록시가 들어 있다 — 위치를 꺼낼 때 `Locker` 를 조회한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 첫 줄이 끝난 시점에는 `members` 행만 읽고, `Locker` 테이블은 아직 읽지 않는다.
- `member.locker` 에는 `id = 7` 을 가진 `Locker` 프록시가 들어 있다.
- 둘째 줄에서 `getLocation()` 으로 실제 값을 만질 때 `Locker` 를 조회해 프록시를 채운다.

**왜 그런가**
`Member.locker` 는 `@JoinColumn` 을 단 FK 쪽이라, 자기 행의 `locker_id` 값(7)만 보고 「사물함이 있다」를 안다.
그래서 `null` 대신 프록시를 넣어 두고 조회를 미룰 수 있다 — 지연 로딩이 정상 동작하는 쪽이다.
`locker_id` 가 `NULL` 이었다면 프록시 없이 `null` 이 들어갔을 것이다.
근거: 2-summary 「동작 방식 (4)」.

### 2. 조회가 일어날 수 있다 — `mappedBy` 쪽은 상대 유무를 몰라 바로 읽는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`LAZY` 를 적었어도 `Locker` 를 읽는 시점에 `members` 를 조회해 `member` 필드를 채울 수 있다 — 즉시 로딩처럼 된다.

**왜 그런가**
`Locker` 테이블 행에는 회원을 가리키는 칸이 없다.
이 사물함을 쓰는 회원이 있는지 없는지는 `members.locker_id` 를 뒤져 봐야만 안다.
필드에 `null` 을 넣을지 프록시를 넣을지 정할 근거가 없으므로 구현체는 그 자리에서 조회해 버릴 수 있다.
이것은 구현체의 프록시 방식에서 나오는 동작이라 「반드시」가 아니라 「될 수 있다」로 말한다.
근거: 2-summary 「동작 방식 (4)」, 「구현 세부사항 대 언어 보장」.

### 3. `locker_id` 는 `NULL` 로 바뀌고 `id = 7` 행은 지워진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `members.locker_id` 는 `NULL` 이 된다.
- `Locker` 테이블의 `id = 7` 행은 DELETE 된다.

**왜 그런가**
`removeLocker()` 는 `this.locker.setMember(null)` 로 거울 쪽을, `this.locker = null` 로 주인 쪽을 끊는다.
`member` 는 영속 상태라 커밋 때 변경 감지가 주인 필드의 변화를 `locker_id` 갱신으로 바꾼다.
`orphanRemoval = true` 때문에 부모에게서 떨어져 나간 `Locker` 는 삭제된다.
거울 쪽(`setMember(null)`)을 바꾼 것 자체는 SQL 을 만들지 않는다 — 객체 상태를 맞추려는 것이다.
두 SQL 이 나가는 차례는 이 문서가 정하지 않는다.
근거: 2-summary 「동작 방식 (3)」.

### 4. `Locker` 행에는 상대 유무를 알려 줄 FK 칸이 없기 때문이다

일대일 필드는 상대가 없으면 `null`, 있으면 프록시여야 한다.
`Member` 는 자기 행의 `locker_id` 가 `NULL` 인지 아닌지로 둘 중 하나를 고를 수 있다.
`Locker` 는 `mappedBy` 쪽이라 자기 행에 그런 칸이 없고, `members` 테이블을 조회해야만 알 수 있다.
그래서 프록시를 미리 넣어 둘 수 없고 결국 바로 조회하게 된다.
근거: 2-summary 「동작 방식 (4)」.

### 5. `@OneToOne` 은 자바 쪽 표시일 뿐이고, DB 에서 일대일을 막는 것은 `unique` 다

`unique = true` 가 없으면 FK 컬럼에 같은 값이 여러 행에 들어갈 수 있다.
그러면 DB 에서는 한 `Locker` 를 여러 회원이 가리키는 일대다가 되어 버린다.
`unique = true` 는 「한 번호는 한 회원증에만」 규칙을 DB 제약으로 건다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 4」.

### 6. id 는 연결한 `User` 의 PK 에서 오고, `User` 없이는 id 를 정할 수 없다

`@MapsId` 는 `user` 필드가 가리키는 `User` 의 PK 를 `UserDetail.id` 로 쓴다.
그래서 `id` 에 `@GeneratedValue` 가 없고, 컬럼 `id` 가 PK 이자 `User` 를 가리키는 FK 다.
`User` 를 넣지 않은 `UserDetail` 은 PK 값을 얻을 곳이 없으므로 그대로는 저장할 수 없다.
`UserDetail.create(user, phoneNumber)` 가 `User` 를 반드시 받는 까닭도 이것이다.
근거: 2-summary 「동작 방식 (5)」, 「어디서 틀리나 5」.

### 7. 주인 쪽만 바꾸면 DB 는 맞고 객체가 어긋나며, 거울 쪽만 바꾸면 FK 가 비어 있다

- `locker.setMember(this)` 를 빼면: 주인 필드 `Member.locker` 는 채워졌으니 커밋 때 `locker_id` 는 맞게 들어간다. 그러나 같은 트랜잭션 안에서 `locker.getMember()` 는 `null` 이라 자바 객체끼리 어긋난다.
- `locker.setMember(member)` 만 부르면: 거울 쪽은 DB 에 아무것도 쓰지 않으므로 `locker_id` 는 채워지지 않는다.

그래서 양쪽을 한 번에 맞추는 편의 메서드를 둔다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 2 · 3」.

### 8. 영속 `Member` 의 변경 감지와 cascade 의 저장 전파가 맞물린다

`findById` 로 가져온 `Member` 는 `@Transactional` 안에서 영속 상태다.
`member.assignLocker(locker)` 로 주인 필드에 비영속 `Locker` 가 걸린다.
트랜잭션 커밋 때 플러시되면서 변경 감지가 `Member.locker` 의 변화를 찾는다.
`cascade = CascadeType.ALL` 이 이 저장을 `Locker` 로 전파해 `Locker` 가 INSERT 되고, `locker_id` 에 그 id 가 들어간다.
근거: 2-summary 「동작 방식 (3)」.

### 9. 자주 읽는 `members` 테이블에 FK 를 두는 것이 유리하다

FK 를 가진 쪽만 지연 로딩이 정상 동작한다.
FK 를 `members` 에 두면 자주 읽는 `Member` 쪽 `locker` 가 프록시로 미뤄져, 회원을 읽을 때마다 사물함까지 조회하지 않는다.
FK 를 사물함 테이블에 두면 `Member` 쪽 필드가 `mappedBy` 가 되어 회원을 읽을 때마다 사물함 조회가 붙을 수 있다.
근거: 2-summary 「동작 방식 (4)」의 FK 위치 장단점 표, 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 세 가지 `@OneToOne` 매핑과 사물함 배정 서비스 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `User` 의 `id` · NOT NULL `name` · `profile` | `@Id @GeneratedValue(strategy = GenerationType.IDENTITY)`, `@Column(nullable = false) private String name;`, `private UserProfile profile;` |
| 2. `profile` 일대일 · LAZY · cascade ALL · `user_profile_id` 중복 금지 | `@OneToOne(fetch = FetchType.LAZY, cascade = CascadeType.ALL)` + `@JoinColumn(name = "user_profile_id", unique = true)` |
| 3. `protected` 생성자 · `setProfile()` · 게터 | `protected User() {}`, `setProfile(UserProfile profile)`, `getId()` · `getName()` · `getProfile()` |
| 4. `UserProfile` 필드 · `create(bio, avatarUrl)` · 역참조 없음 | `bio` · `avatarUrl` · `website`, `public static UserProfile create(...)` |
| 5. `members` 테이블 · 주인 `locker` 매핑 | `@Table(name = "members")`, `@OneToOne(fetch = FetchType.LAZY, cascade = CascadeType.ALL, orphanRemoval = true)` + `@JoinColumn(name = "locker_id", unique = true)` |
| 6. 양쪽을 함께 채우는 배정 | `Member.assignLocker()` 의 `this.locker = locker;` + `locker.setMember(this);` |
| 7. 있을 때만 양쪽을 끊는 해제 | `Member.removeLocker()` 의 `if (this.locker != null)` + `setMember(null)` + `this.locker = null;` |
| 8. `Locker` 필드 · 읽기 전용 `member` | `@Column(nullable = false) private String location;`, `@OneToOne(mappedBy = "locker", fetch = FetchType.LAZY)` |
| 9. `create(location)` · 패키지-프라이빗 setter | `public static Locker create(String location)`, `void setMember(Member member)` |
| 10. PK 를 생성하지 않고 공유 | `UserDetail` 의 `@Id private Long id;` (`@GeneratedValue` 없음) |
| 11. `user` 일대일 · LAZY · PK 이자 FK `id` | `@OneToOne(fetch = FetchType.LAZY)` + `@MapsId` + `@JoinColumn(name = "id")` |
| 12. `create(user, phoneNumber)` · `address` | `public static UserDetail create(User user, String phoneNumber)`, `private String address;` |
| 13. 서비스 빈 · 트랜잭션 | `@Service` + `@Transactional` on `MemberService` |
| 14. 찾고 · 만들고 · 배정 (`save` 없음) | `memberRepository.findById(memberId).orElseThrow(...)`, `Locker.create(location)`, `member.assignLocker(locker)` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-jpa/reference/jpa-mapping-onetoone.java`

```java
// [JPA & 데이터베이스] @OneToOne 매핑
// 설명: @OneToOne 단방향/양방향 관계 매핑과 외래키(FK) 위치에 따른 장단점
// 팁: @OneToOne에서 mappedBy가 아닌 쪽(FK를 가진 쪽)만 LAZY 로딩이 정상 동작한다. mappedBy 쪽은 프록시를 생성할 수 없어 항상 EAGER로 조회될 수 있다. 이를 피하려면 @MapsId로 PK를 공유하거나, 단방향으로 설계하는 것이 좋다.

// JPA 표준 어노테이션
import jakarta.persistence.*;

// === 1. @OneToOne 단방향 (FK를 가진 쪽에서 참조) ===
// User 엔티티 - UserProfile에 대한 FK 보유
@Entity
public class User {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // 회원 이름 - NOT NULL
    @Column(nullable = false)
    private String name;

    // 단방향: User -> UserProfile
    // users 테이블에 user_profile_id FK 컬럼 생성
    // @OneToOne: 1:1 관계, FK를 가진 쪽이 LAZY 로딩 정상 동작
    @OneToOne(fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    // FK 컬럼명, unique=true로 1:1 보장
    @JoinColumn(name = "user_profile_id", unique = true)
    private UserProfile profile;

    protected User() {}

    // 프로필 설정 (cascade.ALL이라 비영속이어도 함께 INSERT)
    public void setProfile(UserProfile profile) {
        this.profile = profile;
    }

    public Long getId() { return id; }
    public String getName() { return name; }
    public UserProfile getProfile() { return profile; }
}

// 사용자 프로필 - 부가 정보
@Entity
public class UserProfile {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // 자기소개
    private String bio;
    // 아바타 이미지 URL
    private String avatarUrl;
    // 개인 사이트 URL
    private String website;

    protected UserProfile() {}

    // 프로필 정적 팩토리
    public static UserProfile create(String bio, String avatarUrl) {
        UserProfile profile = new UserProfile();
        profile.bio = bio;
        profile.avatarUrl = avatarUrl;
        return profile;
    }

    public Long getId() { return id; }
    public String getBio() { return bio; }
}

// === 2. @OneToOne 양방향 ===
// Member 엔티티 - Locker에 대한 FK 보유 (주 테이블)
@Entity
@Table(name = "members")
public class Member {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // 회원 이름
    private String name;

    // 주 테이블(Member)에 FK
    // FK가 Member 쪽에 있으므로 이쪽이 연관관계의 주인 (LAZY 정상 동작)
    @OneToOne(fetch = FetchType.LAZY, cascade = CascadeType.ALL,
              orphanRemoval = true)
    // 사물함 FK - unique 보장
    @JoinColumn(name = "locker_id", unique = true)
    private Locker locker;

    protected Member() {}

    // 편의 메서드: 양방향 관계 설정
    // 양쪽 모두 동기화하여 영속성 컨텍스트와 DB 상태 일치 유지
    public void assignLocker(Locker locker) {
        this.locker = locker;
        // 반대 쪽(Locker)에도 자기 자신 등록
        locker.setMember(this);  // 양방향 동기화
    }

    // 사물함 해제 - orphanRemoval로 DELETE
    public void removeLocker() {
        if (this.locker != null) {
            // 반대 쪽 참조 끊기
            this.locker.setMember(null);
            this.locker = null;  // orphanRemoval로 삭제됨
        }
    }

    public Long getId() { return id; }
    public String getName() { return name; }
    public Locker getLocker() { return locker; }
}

// Locker 엔티티 - 양방향의 mappedBy 쪽 (읽기 전용)
@Entity
public class Locker {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // 사물함 위치 - NOT NULL
    @Column(nullable = false)
    private String location;

    // 양방향: Locker -> Member (읽기 전용, mappedBy)
    // 주의: @OneToOne mappedBy 쪽은 LAZY가 동작하지 않을 수 있음
    // (mappedBy 쪽은 FK가 없어 NULL 여부를 모르므로 프록시 생성이 어려움)
    @OneToOne(mappedBy = "locker", fetch = FetchType.LAZY)
    private Member member;

    protected Locker() {}

    // 사물함 정적 팩토리
    public static Locker create(String location) {
        Locker locker = new Locker();
        locker.location = location;
        return locker;
    }

    // 패키지-프라이빗 setter - 편의 메서드 내에서만 사용
    void setMember(Member member) {
        this.member = member;
    }

    public Long getId() { return id; }
    public String getLocation() { return location; }
    public Member getMember() { return member; }
}

// === 3. @OneToOne with @MapsId (PK 공유) ===
// 대상 테이블의 PK가 주 테이블의 PK와 동일 (FK이자 PK)
// User-UserDetail이 같은 PK를 공유하여 별도 FK 컬럼 불필요
@Entity
public class UserDetail {
    @Id  // @GeneratedValue 없음 - User의 PK를 공유
    private Long id;

    // 전화번호
    private String phoneNumber;
    // 주소
    private String address;

    // @MapsId: 연관 엔티티(User)의 PK를 자신의 PK로 매핑 - PK이자 FK
    @OneToOne(fetch = FetchType.LAZY)
    @MapsId  // UserDetail.id = User.id
    // PK이자 FK 컬럼
    @JoinColumn(name = "id")
    private User user;

    protected UserDetail() {}

    // 정적 팩토리 - User를 받아 PK 공유
    public static UserDetail create(User user, String phoneNumber) {
        UserDetail detail = new UserDetail();
        detail.user = user;
        detail.phoneNumber = phoneNumber;
        return detail;
    }

    public Long getId() { return id; }
    public String getPhoneNumber() { return phoneNumber; }
}

// === 4. 사용 예제 ===
// 회원 서비스 - 사물함 할당
@Service
@Transactional
public class MemberService {

    // 사물함 할당 - cascade로 Locker도 함께 INSERT
    public void assignLocker(Long memberId, String location) {
        Member member = memberRepository.findById(memberId)
            .orElseThrow(() -> new EntityNotFoundException("Member", memberId));

        // 비영속 Locker 생성
        Locker locker = Locker.create(location);
        // 양방향 동기화 + cascade.ALL로 함께 영속화
        member.assignLocker(locker);  // cascade로 locker도 자동 저장
    }
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**

- `@JoinColumn` 을 단 필드가 FK 를 가진 쪽이고, 양방향에서는 그 필드가 연관관계의 주인이다 — `Member.locker` 가 주인, `Locker.member` 는 `mappedBy` 거울이다.
- `unique = true` 가 DB 에서 일대일을 지킨다.
- 편의 메서드 `assignLocker()` · `removeLocker()` 가 양쪽 필드를 함께 맞추고 끊어 객체와 DB 가 어긋나지 않게 한다.
- `MemberService.assignLocker()` 에 `save` 가 없어도 영속 `Member` 의 변경 감지와 `cascade = ALL` 로 `Locker` 가 INSERT 된다.
- `UserDetail` 은 `@MapsId` 로 `User` 의 PK 를 공유하므로 `@GeneratedValue` 가 없고, FK 쪽이라 지연 로딩이 정상 동작한다.
- 정답 코드는 한 파일에 `public class` 를 여럿 모아 두었으므로 실제로는 파일을 나누고, `memberRepository` 와 두 인자 예외 클래스를 따로 준비해야 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
