# java/java-jpa/11 — JPA Auditing — 정리 (힌트)

> 출처 — study-site 항목 `java/jpa-auditing`(항목 데이터 `data/java/jpa-database.json`) · 정답 코드 study-practice `java/java-jpa/reference/jpa-auditing.java`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**JPA Auditing 은 「문서함에 붙은 자동 날인기」다.**
서류(엔티티)를 처음 문서함에 넣으면 날인기가 「접수 일시 · 접수자」 도장을 찍는다.
서류 내용을 고쳐서 다시 넣으면 「최종 수정 일시 · 수정자」 도장만 새로 찍는다.
접수 도장은 한 번 찍히면 다시 찍지 않는다.
JPA Auditing 도 똑같은 구조다.
엔티티가 처음 저장될 때 생성 시각과 생성자를 채우고, 변경이 감지되어 UPDATE 가 나갈 때 수정 시각과 수정자를 채운다.

| 비유 | 실체 |
|---|---|
| 서류 | 엔티티 객체(`Post` 등) |
| 문서함에 처음 넣기 | persist(최초 저장, INSERT) |
| 고쳐서 다시 넣기 | 변경 감지(dirty checking) 후 UPDATE |
| 자동 날인기 | `AuditingEntityListener` |
| 날인기의 전원 스위치 | `@EnableJpaAuditing` |
| 「지금 일하는 사람」 명찰 | `AuditorAware` 빈 |
| 도장 찍는 칸이 인쇄된 공용 양식 | `@MappedSuperclass` 로 만든 `BaseEntity` |

```text
  new Post(...)          save / persist              필드 변경 → 커밋
 ┌──────────────┐      ┌──────────────────┐       ┌──────────────────┐
 │ createdAt=∅  │ ───▶ │ createdAt = 지금  │ ───▶  │ createdAt  그대로 │
 │ createdBy=∅  │      │ createdBy = 사용자│       │ updatedAt = 지금  │
 │ updatedAt=∅  │      │                   │       │ updatedBy = 사용자│
 └──────────────┘      └──────────────────┘       └──────────────────┘
```

## 이 주제가 답하려는 질문

1. 엔티티마다 생성 · 수정 시각을 손으로 넣지 않고 어떻게 자동으로 채우나?
2. 「누가」 만들고 고쳤는지는 어디서 가져오나?
3. 모든 엔티티에 같은 감사 필드를 일관되게 붙이려면 어떻게 묶나?
4. Spring Data 없이 JPA 표준만으로는 같은 일을 어떻게 하나?

## 동작 방식

### (1) 기능을 켜기 — `@EnableJpaAuditing`

**언제 쓰나** — Auditing 어노테이션(`@CreatedDate` 등)을 하나라도 쓰려면 반드시 한 번 켠다.

```text
@Configuration
@EnableJpaAuditing          ──▶  Auditing 처리기 등록
class JpaAuditingConfig          (이것이 없으면 @CreatedDate 등은 그냥 표시일 뿐)
        │
        ▼
@CreatedDate · @LastModifiedDate ... 가 실제로 값을 받게 된다
```

- 설정 클래스에 `@EnableJpaAuditing` 을 붙이면 Auditing 기능이 활성화된다.
- 이 스위치가 없으면 필드에 어노테이션을 붙여도 아무도 값을 넣지 않아 `null` 로 남는다.

### (2) 리스너를 걸기 — `@EntityListeners(AuditingEntityListener.class)`

**언제 쓰나** — Auditing 필드를 가진 엔티티(또는 그 부모)마다 붙인다.

```text
엔티티 생명주기 이벤트            AuditingEntityListener 가 하는 일
──────────────────────          ────────────────────────────────
persist 직전          ─────▶    @CreatedDate · @CreatedBy 칸 채움
UPDATE 직전(변경 감지)  ─────▶    @LastModifiedDate · @LastModifiedBy 칸 채움
```

- `@EntityListeners` 는 엔티티 생명주기 이벤트를 받을 리스너를 등록한다.
- `AuditingEntityListener` 는 Spring Data JPA 가 제공하는 리스너로, 이벤트를 받아 감사 필드를 채운다.
- 원본 주석은 이 등록이 「Auditing 동작에 필수」라고 적는다.
- 스위치(1)와 리스너(2)는 둘 다 있어야 한다.

### (3) 시각 필드 — `@CreatedDate` 와 `@LastModifiedDate`

**언제 쓰나** — 언제 만들어지고 언제 마지막으로 바뀌었는지 기록할 때.

```text
Post post = Post.create("제목","본문");   createdAt = null  (아직 저장 전)
repository.save(post);                    → persist → createdAt = 지금
...트랜잭션 안에서...
post.update("새 제목","새 본문");           필드만 바뀜
커밋 → flush → 변경 감지 → UPDATE          → updatedAt = 지금
                                           created_at 은 UPDATE 문에서 빠짐
```

- `@CreatedDate` 는 엔티티를 최초로 persist 하는 시점에 현재 시각을 넣는다.
- `@LastModifiedDate` 는 변경 감지로 UPDATE 가 발생할 때 갱신된다.
- 그래서 `Post.create(...)` 가 객체를 막 만든 순간에는 시각 필드가 아직 비어 있다.
- `update(...)` 메서드는 제목과 본문만 바꾸고 시각은 건드리지 않는다 — 시각은 커밋 때 UPDATE 와 함께 채워진다.
- 변경 감지는 「바뀐 것이 있을 때」 UPDATE 를 만든다.
  바뀐 값이 없으면 UPDATE 도 없고, 그러면 `@LastModifiedDate` 를 갱신할 계기도 없다.
- `created_at` 컬럼에 `updatable = false` 를 주면 UPDATE 문에서 이 컬럼이 빠진다 — 생성 시각이 바뀌지 않게 막는 장치다.

> **변경 감지(dirty checking)** — 영속 상태 엔티티의 필드가 처음 읽었을 때와 달라졌는지 flush 시점에 비교해, 달라졌으면 UPDATE 를 자동으로 만드는 JPA 동작.\
> 예: 트랜잭션 안에서 `post.update(...)` 만 부르고 `save` 를 다시 부르지 않아도 커밋 때 UPDATE 가 나간다.

### (4) 사용자 필드 — `@CreatedBy` · `@LastModifiedBy` 와 `AuditorAware`

**언제 쓰나** — 「누가」 만들고 고쳤는지 기록할 때.

```text
@CreatedBy / @LastModifiedBy 칸을 채워야 함
        │  "지금 사용자 누구?"
        ▼
AuditorAware<String> 빈 (auditorProvider)
        │
        ├─ SecurityContextHolder.getContext().getAuthentication()
        │
        ├─ 인증 정보 없음 또는 인증 안 됨 ──▶ Optional.of("SYSTEM")
        └─ 인증됨                          ──▶ Optional.of(authentication.getName())
```

- `AuditorAware<T>` 는 「현재 작업자」를 돌려주는 인터페이스다.
- 원본은 이것을 `@Bean` 으로 등록하고 람다로 구현한다.
- `@CreatedBy` 는 persist 때, `@LastModifiedBy` 는 수정 때 이 빈이 돌려준 값을 기록한다.
- 원본 구현은 Spring Security 의 `SecurityContext` 에서 현재 요청 스레드의 인증 정보를 꺼낸다 — 팁이 말하듯 이것이 일반적인 방식이다.
- 인증 정보가 없거나 인증되지 않은 요청(배치 · 스케줄러 등)은 `"SYSTEM"` 으로 기록한다.
- `created_by` 도 `updatable = false` 로 한 번 기록한 뒤 바뀌지 않게 막는다.

### (5) 공통 부모로 묶기 — `@MappedSuperclass`

**언제 쓰나** — 여러 엔티티가 같은 감사 필드를 가져야 할 때.

```text
BaseTimeEntity  (@MappedSuperclass, 테이블 없음)
  createdAt, updatedAt
     ▲                         ▲
     │ extends                 │ extends
BaseEntity (@MappedSuperclass)  SystemLog (@Entity)
  + createdBy, updatedBy          테이블: id, action, detail,
     ▲                                    created_at, updated_at
     │ extends
Post (@Entity, 테이블 posts)
  테이블: id, title, content, created_at, updated_at, created_by, updated_by
```

- `@MappedSuperclass` 는 자기 테이블을 갖지 않고, 필드(매핑 정보)만 자식 엔티티의 테이블에 물려준다.
- 원본은 두 단계로 나눈다: 시간만 가진 `BaseTimeEntity`, 시간에 사용자를 더한 `BaseEntity`.
- 사용자 정보가 필요 없는 `SystemLog` 는 `BaseTimeEntity` 만 상속해 시간만 기록한다.
- `Post` 는 `BaseEntity` 를 상속해 네 필드가 모두 자동 관리된다.
- 팁: 모든 엔티티가 이 베이스를 상속하면 감사 필드 이름 · 컬럼 · 규칙이 일관되게 유지된다.

> **`@MappedSuperclass`** — 엔티티가 아니라 매핑 정보만 물려주는 부모 클래스 표시.\
> 예: `BaseTimeEntity` 는 테이블이 없고, `posts` 테이블에 `created_at` 컬럼이 생긴다.

### (6) Spring Data 없이 — `@PrePersist` / `@PreUpdate`

**언제 쓰나** — Spring Data Auditing 을 쓰지 않고 JPA 표준 생명주기 콜백만으로 시각을 관리할 때.

```text
persist 호출  ──▶ @PrePersist onCreate()  ──▶ createdAt = now, updatedAt = now ──▶ INSERT
변경 감지     ──▶ @PreUpdate  onUpdate()  ──▶ updatedAt = now                  ──▶ UPDATE
```

- `@PrePersist` 메서드는 persist 직전(INSERT 직전)에 불린다.
- `@PreUpdate` 메서드는 변경 감지로 UPDATE 가 나가기 직전에 불린다.
- 원본의 `AuditManualEntity` 는 `LocalDateTime.now()` 로 직접 값을 넣는다.
- 이 방식은 `@EnableJpaAuditing` · `AuditingEntityListener` 가 필요 없다.
- 대신 「누가」 를 채우는 `AuditorAware` 같은 장치가 없으니, 사용자 기록이 필요하면 직접 구해야 한다.

## 문법 — 형태와 규칙

```java
@Configuration
@EnableJpaAuditing
class AuditConfig {
    @Bean
    AuditorAware<String> auditor() { return () -> Optional.of("tester"); }
}

@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
abstract class Base {
    @CreatedDate
    @Column(updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    private LocalDateTime updatedAt;
}
```

- `@EnableJpaAuditing` — 설정 클래스(`@Configuration`)에 붙인다.
- `@EntityListeners(AuditingEntityListener.class)` — 감사 필드를 가진 엔티티나 `@MappedSuperclass` 에 붙인다.
- `@CreatedDate` · `@LastModifiedDate` · `@CreatedBy` · `@LastModifiedBy` 는 `org.springframework.data.annotation` 패키지다 — JPA 표준(`jakarta.persistence`)이 아니라 Spring Data 가 제공한다.
- `AuditorAware<T>` 의 메서드는 `Optional<T>` 를 돌려준다 — 원본은 `Optional<String>` 을 쓴다.
- `@CreatedBy` 를 쓰려면 `AuditorAware` 빈이 있어야 한다.
- 시각 필드 타입은 원본에서 `LocalDateTime` 이다.
- 생성 시각 · 생성자 컬럼은 `@Column(updatable = false)` 로 UPDATE 에서 제외한다.
- `@PrePersist` · `@PreUpdate` 는 `jakarta.persistence` 의 표준 콜백 어노테이션이다.

## 어디서 틀리나

### 1. `@EnableJpaAuditing` 을 빠뜨린다

필드에 `@CreatedDate` 를 붙였는데 값이 `null` 로 남는다.
기능 스위치가 꺼져 있으면 어노테이션은 표시일 뿐이다.
원본처럼 `created_at` 이 `nullable = false` 면, 값이 비어 저장 자체가 실패할 수 있다.

### 2. `@EntityListeners(AuditingEntityListener.class)` 를 빠뜨린다

스위치를 켜도 엔티티(또는 부모)에 리스너가 걸려 있지 않으면 이벤트를 받을 주체가 없다.
베이스 클래스에 붙여 두면 자식마다 따로 붙이지 않아도 된다.

### 3. 저장 전에 `createdAt` 을 읽는다

`Post.create(...)` 직후에는 아직 persist 전이라 시각이 비어 있다.
원본 주석 「createdAt, createdBy는 자동 설정됨」 은 「저장될 때」 채워진다는 뜻이다.

### 4. `@LastModifiedDate` 가 아무 때나 갱신된다고 생각한다

팁대로 갱신 계기는 변경 감지다.
트랜잭션 밖에서 필드를 바꾸면(준영속 상태) 변경 감지가 일어나지 않는다.
바뀐 값이 없으면 UPDATE 도 없다.

### 5. 생성 시각이 수정 때 덮인다

`updatable = false` 를 빼면 UPDATE 문에 `created_at` 이 들어가 값이 흔들릴 수 있다.
원본은 `created_at` · `created_by` 둘 다 `updatable = false` 로 막는다.

### 6. `@MappedSuperclass` 대신 `@Entity` 를 베이스에 붙인다

그러면 베이스가 엔티티 상속 매핑이 되어 테이블 설계가 달라진다.
감사 필드만 물려주려는 목적이면 `@MappedSuperclass` 다.

### 7. 사용자 정보가 필요 없는 엔티티에 `BaseEntity` 를 상속시킨다

`SystemLog` 처럼 「누가」 가 의미 없는 엔티티는 `BaseTimeEntity` 만 상속한다.
안 그러면 언제나 `"SYSTEM"` 만 들어가는 쓸모없는 컬럼이 생긴다.

### 8. 익명 사용자가 `"SYSTEM"` 으로 걸러진다고 믿는다

원본의 주장 → 인증되지 않은 요청은 `authentication == null || !isAuthenticated()` 로 걸러 `"SYSTEM"` 으로 기록한다.
왜 의심스러운가 → Spring Security 의 익명 인증이 켜져 있으면 로그인 안 한 요청에도 익명 인증 객체가 들어가고, 그 객체의 `isAuthenticated()` 가 `true` 일 수 있다 — 그러면 `"SYSTEM"` 이 아니라 익명 사용자 이름이 기록된다 (확인 필요).

### 9. 원본 예제를 한 파일에 그대로 넣는다

원본은 `public` 최상위 클래스 여러 개(`JpaAuditingConfig` · `BaseTimeEntity` · `Post` …)를 한 덩어리로 보인다.
Java 는 `public` 최상위 클래스를 파일 하나에 하나만 허용하므로, 실제로는 클래스마다 파일을 나눠야 컴파일된다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `@PrePersist` 는 persist 직전, `@PreUpdate` 는 UPDATE 직전에 불린다 | JPA 명세(Jakarta Persistence) |
| `@MappedSuperclass` 는 테이블 없이 매핑만 물려준다 | JPA 명세 |
| 변경 감지로 커밋 · flush 때 UPDATE 가 나간다 | JPA 영속성 컨텍스트 동작 — 실제 SQL 시점은 구현체(Hibernate 등)의 flush 정책 |
| `@CreatedDate` 등이 값을 받는다 | Spring Data JPA (`@EnableJpaAuditing` + `AuditingEntityListener`) — JPA 표준 아님 |
| 현재 사용자를 `SecurityContextHolder` 에서 꺼낸다 | Spring Security — 팁이 말하는 「일반적」 관례이지 필수 아님 |
| 인증 없으면 `"SYSTEM"` | 이 예제 코드의 약속 — 어떤 프레임워크도 정한 값 아님 |
| `LocalDateTime.now()` 가 주는 시각 | JDK — 시스템 기본 시간대를 따른다 |
| `public` 최상위 클래스는 파일당 하나 | Java 언어 규칙 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| Spring Data JPA 프로젝트에서 모든 엔티티에 생성 · 수정 시각 | `@EnableJpaAuditing` + `BaseTimeEntity` 상속 | 엔티티마다 `LocalDateTime.now()` 를 손으로 대입 |
| 작성자 · 수정자까지 기록 | `BaseEntity` + `AuditorAware` 빈 | 서비스 코드마다 사용자명 수동 세팅 |
| 사용자 개념이 없는 로그성 엔티티 | `BaseTimeEntity` 만 상속 | `BaseEntity` 상속 |
| Spring Data 없이 순수 JPA | `@PrePersist` / `@PreUpdate` 콜백 | `@CreatedDate` (처리해 줄 주체가 없다) |
| 생성 값이 절대 바뀌면 안 됨 | `@Column(updatable = false)` | 제약 없는 컬럼 |

## 핵심 문장

1. **`@EnableJpaAuditing` (스위치)와 `AuditingEntityListener` (리스너)가 둘 다 있어야 감사 필드가 채워진다.**
2. **`@CreatedDate` · `@CreatedBy` 는 최초 persist 때, `@LastModifiedDate` · `@LastModifiedBy` 는 변경 감지로 UPDATE 가 날 때 채워진다.**
3. **「누가」 는 `AuditorAware` 빈이 공급하고, 보통 Spring Security 의 `SecurityContext` 에서 꺼낸다.**
4. **`@MappedSuperclass` 베이스를 상속시키면 모든 엔티티의 감사 필드가 일관된다 — 필요에 따라 시간용 · 시간+사용자용으로 나눈다.**
5. **Spring Data 없이도 JPA 표준 `@PrePersist` / `@PreUpdate` 로 시각은 직접 채울 수 있다.**

## 관련 자료

- `jpa-entity` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `jpa-soft-delete` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `spring-security-basics` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/java/jpa-database.json` 의 `jpa-auditing`

## 용어 풀이

- **Auditing(감사)** — 데이터를 언제 · 누가 만들고 고쳤는지 자동으로 기록하는 일.
- **`@EnableJpaAuditing`** — Spring Data JPA 의 Auditing 기능을 켜는 설정 어노테이션.
- **`AuditingEntityListener`** — 생명주기 이벤트를 받아 감사 필드를 채우는 Spring Data JPA 리스너.
- **`@EntityListeners`** — 엔티티에 생명주기 이벤트 리스너 클래스를 등록하는 JPA 어노테이션.
- **`@CreatedDate`** — 최초 저장 시각을 받을 필드 표시.
- **`@LastModifiedDate`** — 마지막 수정 시각을 받을 필드 표시.
- **`@CreatedBy`** — 최초 저장한 사용자를 받을 필드 표시.
- **`@LastModifiedBy`** — 마지막 수정한 사용자를 받을 필드 표시.
- **`AuditorAware<T>`** — 현재 작업자를 `Optional<T>` 로 돌려주는 인터페이스.
- **`SecurityContextHolder`** — 현재 요청 스레드의 인증 정보(`SecurityContext`)에 접근하는 Spring Security 진입점.
- **`Authentication`** — 인증 정보 객체. `getName()` 으로 사용자명, `isAuthenticated()` 로 인증 여부를 본다.
- **persist** — 새 엔티티를 영속성 컨텍스트에 넣어 INSERT 대상으로 만드는 일.
- **변경 감지(dirty checking)** — flush 때 엔티티의 바뀐 필드를 찾아 UPDATE 를 자동으로 만드는 동작.
- **`@MappedSuperclass`** — 테이블 없이 매핑 정보만 자식 엔티티에 물려주는 부모 클래스 표시.
- **`@PrePersist` / `@PreUpdate`** — INSERT · UPDATE 직전에 불리는 JPA 표준 생명주기 콜백.
- **`updatable = false`** — 그 컬럼을 UPDATE 문에서 빼라는 `@Column` 속성.
- **BaseEntity** — 공통 감사 필드를 모아 둔 베이스 클래스를 부르는 관례 이름.

## 더 들어가면

- Spring Data 의 기본 설정에서는 최초 저장 때 `@LastModifiedDate` · `@LastModifiedBy` 도 생성 값과 같이 채워진다고 알려져 있다. `@EnableJpaAuditing(modifyOnCreate = false)` 로 끌 수 있다 (확인 필요).
- 시각을 어디서 얻을지 바꾸려면 `@EnableJpaAuditing(dateTimeProviderRef = "...")` 로 `DateTimeProvider` 빈을 지정할 수 있다 — 테스트에서 시각을 고정할 때 쓴다 (확인 필요).
- 원본은 `BaseTimeEntity` 와 그 자식 `BaseEntity` 양쪽에 같은 리스너를 붙였다. 부모에 붙인 리스너는 자식에게도 적용되므로 한쪽은 중복일 수 있다 — 구현체가 같은 리스너를 두 번 부르는지는 따로 확인해야 한다 (확인 필요).
- `@CreatedDate` 는 `LocalDateTime` 외에 `Instant` · `Long` 등 다른 시각 타입도 받는다고 알려져 있다 (확인 필요).
- `SecurityContextHolder` 의 기본 저장 전략은 스레드 로컬이라, 비동기 스레드에서는 인증 정보가 없어 `"SYSTEM"` 쪽으로 빠질 수 있다 (확인 필요).
- 벌크 UPDATE(JPQL `update ... set ...`)는 엔티티를 거치지 않아 생명주기 콜백이 불리지 않고, 그래서 감사 필드도 갱신되지 않는다 (확인 필요).
