# java/java-jpa/02 — @OneToOne 매핑 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `Member` 를 찾아 오기만 하면 (예측)

```java
// 질문용 발췌 — @Transactional 메서드 안
Member member = memberRepository.findById(1L).orElseThrow();
// 여기까지 실행된 시점 (members.id = 1 행의 locker_id = 7)
String where = member.getLocker().getLocation();
```

- 첫 줄이 끝난 시점에 `Locker` 테이블을 읽는 조회가 이미 일어났나, 그리고 `member.locker` 필드에는 무엇이 들어 있나?
- 둘째 줄에서는 무슨 일이 일어나나?

### 2. `Locker` 를 찾아 오기만 하면 (예측)

```java
// 질문용 발췌 — Locker.member 는 @OneToOne(mappedBy = "locker", fetch = FetchType.LAZY)
Locker locker = entityManager.find(Locker.class, 7L);
// 아직 locker.getMember() 를 부르지 않았다
```

- 이 시점까지 `members` 테이블을 읽는 조회가 일어날 수 있나, 그렇다면 왜인가?

### 3. `removeLocker()` 뒤 커밋하면 (예측)

```java
// 질문용 발췌 — @Transactional 메서드 안, member 는 영속 상태, locker_id = 7
Member member = memberRepository.findById(1L).orElseThrow();
member.removeLocker();
// 메서드가 끝나며 커밋
```

- 커밋 뒤 `members.locker_id` 와 `Locker` 테이블의 `id = 7` 행은 각각 어떻게 되나?

### 4. `mappedBy` 쪽은 프록시를 만들기 어렵다 (왜)

- `Member` 쪽은 지연 로딩이 되는데 `Locker` 쪽은 왜 프록시를 넣어 둘 수 없나?

### 5. 일대일인데 `@JoinColumn` 에 `unique = true` 를 붙인다 (왜)

- `@OneToOne` 을 이미 적었는데도 FK 컬럼에 `unique = true` 를 따로 주는 까닭은 무엇인가?

### 6. `@MapsId` 를 쓴 `UserDetail` 의 id (경계)

- `UserDetail` 의 id 값은 어디서 오며, `User` 없이 `UserDetail` 만 저장할 수 있나?

### 7. 편의 메서드의 한 줄을 빼면 (경계)

- `assignLocker()` 에서 `locker.setMember(this);` 를 빼면 DB 와 자바 객체 중 무엇은 맞고 무엇이 어긋나나?
- 반대로 `locker.setMember(member)` 만 부르고 `Member.locker` 를 비워 두면 `locker_id` 는 어떻게 되나?

### 8. `save` 없이 `Locker` 가 INSERT 되는 흐름 (연결)

- `MemberService.assignLocker()` 에는 `save` 호출이 없는데 `Locker` 가 저장되는 것은 영속성 컨텍스트의 어떤 동작과 cascade 가 맞물린 결과인가?

### 9. FK 위치를 고르는 기준과 LAZY 팁 (연결)

- 회원을 자주 읽고 사물함은 가끔 꺼내 보는 서비스라면, 원본 팁에 비추어 FK 를 어느 테이블에 두는 것이 유리한가?

## 실습

### 실습 1. 세 가지 `@OneToOne` 매핑과 사물함 배정 서비스 만들기

**만들 것** — 단방향(`User` → `UserProfile`), 양방향(`Member` ↔ `Locker`), PK 공유(`UserDetail` → `User`) 세 가지 일대일 매핑을 엔티티로 짜고, 회원에게 사물함을 배정하는 서비스 메서드를 만든다.

**준비물** — Jakarta Persistence(JPA) 와 Spring(`@Service` · `@Transactional`), Spring Data JPA 리포지토리가 필요하다. 정답 코드의 `memberRepository` 필드와 두 인자를 받는 `EntityNotFoundException` 은 정답 코드에 선언이 없으므로 직접 준비해야 한다.

**요구 조건**

1단계 — 단방향 `User` → `UserProfile`

1. `User` 는 IDENTITY 로 만드는 `id`, NOT NULL 인 `name`, `UserProfile` 을 가리키는 `profile` 을 가진다.
2. `profile` 은 일대일 · 지연 로딩 · 모든 작업 전파(cascade ALL)이고, FK 컬럼 `user_profile_id` 에 중복 금지를 건다.
3. `User` 에는 `protected` 기본 생성자, `setProfile()`, `getId()` · `getName()` · `getProfile()` 이 있다.
4. `UserProfile` 은 IDENTITY `id` 와 `bio` · `avatarUrl` · `website` 를 가지고, `create(bio, avatarUrl)` 정적 팩토리로 만든다. `User` 를 가리키는 필드는 없다.

2단계 — 양방향 `Member` ↔ `Locker`

5. `Member` 는 테이블 이름이 `members` 이고, `Locker` 를 가리키는 `locker` 필드가 연관관계의 주인이다 — 일대일 · 지연 로딩 · cascade ALL · `orphanRemoval`, FK 컬럼 `locker_id` 에 중복 금지.
6. `Member.assignLocker(locker)` 는 자기 필드와 `Locker` 쪽 필드를 함께 채운다.
7. `Member.removeLocker()` 는 사물함이 있을 때만 `Locker` 쪽 참조를 먼저 끊고 자기 필드를 `null` 로 만든다.
8. `Locker` 는 IDENTITY `id`, NOT NULL `location`, 그리고 `Member.locker` 가 주인임을 밝힌 읽기 전용 `member` 필드(지연 로딩 요청)를 가진다.
9. `Locker` 는 `create(location)` 정적 팩토리와, 바깥 패키지에서 부를 수 없는 `setMember()` 를 가진다.

3단계 — PK 공유 `UserDetail`

10. `UserDetail` 의 `id` 는 스스로 생성하지 않고 `User` 의 PK 를 공유한다.
11. `user` 필드는 일대일 · 지연 로딩이고, 컬럼 `id` 가 PK 이자 FK 가 된다.
12. `UserDetail.create(user, phoneNumber)` 가 `User` 를 받아 객체를 만든다. `address` 필드도 둔다.

4단계 — 서비스

13. `MemberService` 는 서비스 빈이며 클래스 전체가 트랜잭션 안에서 돈다.
14. `assignLocker(memberId, location)` 은 회원을 찾고(없으면 예외), 새 `Locker` 를 만들어 편의 메서드로 배정한다 — `save` 는 부르지 않는다.

**시작 코드**

```java
import jakarta.persistence.*;

// === 1. 단방향 ===
@Entity
public class User {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // TODO: NOT NULL 컬럼
    private String name;

    // TODO: 일대일 · 지연 로딩 · cascade ALL
    // TODO: FK 컬럼 user_profile_id, 중복 금지
    private UserProfile profile;

    protected User() {}

    // TODO: setProfile(UserProfile profile)

    public Long getId() { return id; }
    public String getName() { return name; }
    public UserProfile getProfile() { return profile; }
}

@Entity
public class UserProfile {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String bio;
    private String avatarUrl;
    private String website;

    protected UserProfile() {}

    // TODO: static UserProfile create(String bio, String avatarUrl)

    public Long getId() { return id; }
    public String getBio() { return bio; }
}

// === 2. 양방향 ===
@Entity
// TODO: 테이블 이름 members
public class Member {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;

    // TODO: 일대일 · 지연 로딩 · cascade ALL · orphanRemoval
    // TODO: FK 컬럼 locker_id, 중복 금지
    private Locker locker;

    protected Member() {}

    public void assignLocker(Locker locker) {
        // TODO: 양쪽 필드를 함께 채운다
    }

    public void removeLocker() {
        // TODO: 사물함이 있을 때만 양쪽 참조를 끊는다
    }

    public Long getId() { return id; }
    public String getName() { return name; }
    public Locker getLocker() { return locker; }
}

@Entity
public class Locker {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // TODO: NOT NULL 컬럼
    private String location;

    // TODO: 주인은 Member.locker — 읽기 전용, 지연 로딩 요청
    private Member member;

    protected Locker() {}

    // TODO: static Locker create(String location)

    // TODO: 패키지-프라이빗 setMember(Member member)

    public Long getId() { return id; }
    public String getLocation() { return location; }
    public Member getMember() { return member; }
}

// === 3. PK 공유 ===
@Entity
public class UserDetail {
    // TODO: 기본키 — 스스로 생성하지 않는다
    private Long id;

    private String phoneNumber;
    private String address;

    // TODO: 일대일 · 지연 로딩
    // TODO: User 의 PK 를 내 PK 로 공유
    // TODO: PK 이자 FK 인 컬럼 id
    private User user;

    protected UserDetail() {}

    // TODO: static UserDetail create(User user, String phoneNumber)

    public Long getId() { return id; }
    public String getPhoneNumber() { return phoneNumber; }
}

// === 4. 서비스 ===
// TODO: 서비스 빈 · 트랜잭션
public class MemberService {

    public void assignLocker(Long memberId, String location) {
        // TODO: memberRepository 로 회원 찾기 (없으면 EntityNotFoundException)
        // TODO: Locker 를 만들어 편의 메서드로 배정 (save 는 부르지 않는다)
    }
}
```

**확인 방법** — 클래스를 파일별로 나눠 Spring Boot + JPA 프로젝트에 넣고 SQL 로그(예: `spring.jpa.show-sql=true`)를 켠 채 띄운다. 생성된 테이블 정의에서 `user_profile_id` · `locker_id` 가 중복 금지 FK 인지, `UserDetail` 테이블의 `id` 가 PK 이자 `User` 를 가리키는 FK 인지 본다. 이어 `assignLocker()` 를 불러 `save` 없이 `Locker` 의 INSERT 와 `locker_id` 갱신이 SQL 로그에 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
