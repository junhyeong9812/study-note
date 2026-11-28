# java/java-jpa/11 — JPA Auditing — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 저장 전이라 아직 비어 있다 — `null`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`null` 이 찍힌다.

**왜 그런가**
`Post.create` 는 `title` · `content` 만 채운다.
`@CreatedDate` 는 엔티티를 최초로 persist 하는 시점에 채워지므로, `save` 전에는 아무도 값을 넣지 않았다.
원본 주석 「createdAt, createdBy는 자동 설정됨」 은 저장될 때를 가리킨다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 2. `updatedAt` 과 `updatedBy` 만 바뀐다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`updatedAt` 은 커밋 무렵의 시각으로, `updatedBy` 는 수정한 사용자명(인증 정보가 없으면 `"SYSTEM"`)으로 바뀐다.
`createdAt` · `createdBy` 는 처음 저장 때 값 그대로다.

**왜 그런가**
트랜잭션 안에서 필드가 바뀌었으니 커밋 때 변경 감지가 UPDATE 를 만든다.
UPDATE 계기에 `AuditingEntityListener` 가 `@LastModifiedDate` · `@LastModifiedBy` 칸을 채운다.
`created_at` · `created_by` 는 `updatable = false` 라 UPDATE 문에서 빠진다.
근거: 2-summary 「동작 방식 (3) · (4)」.

### 3. 바뀐 값이 없으면 `updatedAt` 도 그대로다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`updatedAt` 은 이전 값 그대로 남는다.

**왜 그런가**
변경 감지는 처음 읽었을 때와 달라진 필드가 있을 때만 UPDATE 를 만든다.
같은 값을 다시 넣으면 달라진 것이 없어 UPDATE 가 없고, `@LastModifiedDate` 를 갱신할 계기도 없다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 4」. (원본에 근거 없음 — 추론: 원본은 「변경 감지 시 갱신」 만 말한다)

### 4. 스위치 `@EnableJpaAuditing` 과 리스너 `AuditingEntityListener` 둘 다 필요하다

- `@EnableJpaAuditing` — Auditing 기능 자체를 켠다. 없으면 `@CreatedDate` 는 표시일 뿐이다.
- `@EntityListeners(AuditingEntityListener.class)` — 엔티티의 생명주기 이벤트를 받아 감사 필드를 실제로 채우는 주체를 등록한다. 없으면 이벤트를 받을 리스너가 없다.

근거: 2-summary 「동작 방식 (1) · (2)」 · 「어디서 틀리나 1 · 2」.

### 5. 수정 때 생성 값이 덮이는 것을 막는다

`updatable = false` 면 그 컬럼이 UPDATE 문에서 빠진다.
그래서 한 번 기록된 생성 시각 · 생성자가 이후 수정으로 바뀌지 않는다 — 원본 주석의 「불변 보장」 이다.
근거: 2-summary 「동작 방식 (3) · (4)」 · 「어디서 틀리나 5」.

### 6. `"SYSTEM"` 을 넘긴다

`auditorProvider` 는 `SecurityContextHolder` 에서 인증 정보를 꺼내, `null` 이거나 `isAuthenticated()` 가 거짓이면 `Optional.of("SYSTEM")` 을 돌려준다.
배치 · 스케줄러처럼 로그인 없는 작업을 위한 약속이다.
다만 이 `"SYSTEM"` 은 프레임워크가 정한 값이 아니라 이 예제 코드의 약속이다.
근거: 2-summary 「동작 방식 (4)」 · 「구현 세부사항 대 언어 보장」.

### 7. 시각 두 개만 있고 사용자 필드는 없다

`SystemLog` 는 `BaseTimeEntity` 만 상속하므로 `created_at` · `updated_at` 만 자동 관리된다.
`created_by` · `updated_by` 는 `BaseEntity` 에 있으므로 `SystemLog` 테이블에는 아예 컬럼이 없다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 7」.

### 8. 상속한 자식 엔티티의 테이블에 컬럼으로 들어간다

`@MappedSuperclass` 는 자기 테이블 없이 매핑 정보만 물려준다.
그래서 `posts` 테이블에 `created_at` · `updated_at` · `created_by` · `updated_by` 가, `SystemLog` 의 테이블에 `created_at` · `updated_at` 이 생긴다.
근거: 2-summary 「동작 방식 (5)」 의 그림.

### 9. 콜백 방식은 JPA 표준만, `@CreatedDate` 방식은 Spring Data 에 기댄다

- `AuditManualEntity` 는 JPA 표준 콜백 `@PrePersist` · `@PreUpdate` 에서 `LocalDateTime.now()` 를 직접 넣는다 — `@EnableJpaAuditing` 도 리스너도 필요 없다.
- `@CreatedDate` 방식은 Spring Data JPA 의 `@EnableJpaAuditing` 과 `AuditingEntityListener` 가 값을 채운다.
- 「누가」 는 Spring Data 쪽이 `AuditorAware` 빈으로 공급받아 `@CreatedBy` · `@LastModifiedBy` 에 채워 주지만, 콜백 방식에는 그런 장치가 없어 직접 구해야 한다.

근거: 2-summary 「동작 방식 (4) · (6)」 · 「구현 세부사항 대 언어 보장」.

## 실습 정답

### 실습 1. 감사 필드를 자동으로 채우는 엔티티 계층 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. Auditing 켜기 | `JpaAuditingConfig` 의 `@Configuration` + `@EnableJpaAuditing` |
| 2. 현재 사용자 공급 | `@Bean auditorProvider()` 람다 — `SecurityContextHolder.getContext().getAuthentication()`, `Optional.of("SYSTEM")` / `Optional.of(authentication.getName())` |
| 3. 테이블 없는 베이스 + 리스너 | `BaseTimeEntity` 의 `@MappedSuperclass` · `@EntityListeners(AuditingEntityListener.class)` · `abstract` |
| 4. 생성 시각, 수정 불가 | `@CreatedDate` + `@Column(name = "created_at", nullable = false, updatable = false)` |
| 5. 수정 시각 | `@LastModifiedDate` + `@Column(name = "updated_at")` |
| 6. 시간+사용자 베이스 | `BaseEntity extends BaseTimeEntity` — `@CreatedBy` (`updatable = false`), `@LastModifiedBy` |
| 7. getter | `getCreatedAt()` · `getUpdatedAt()` · `getCreatedBy()` · `getUpdatedBy()` |
| 8. 게시글 엔티티 | `@Entity @Table(name = "posts") class Post extends BaseEntity` — `id` · `title` · `content` |
| 9. 생성자 · 팩토리 · 수정 | `protected Post()` · `static create(...)` · `update(...)` · `getId()` · `getTitle()` |
| 10. 시간만 쓰는 엔티티 | `SystemLog extends BaseTimeEntity` |
| 11. 콜백 직접 구현 | `AuditManualEntity` 의 `@PrePersist onCreate()` · `@PreUpdate onUpdate()` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-jpa/reference/jpa-auditing.java`

```java
// [JPA & 데이터베이스] JPA Auditing
// 설명: @CreatedDate, @LastModifiedDate, @EnableJpaAuditing을 사용한 엔티티 생성/수정 시간 자동 관리
// 팁: @MappedSuperclass로 BaseEntity를 만들고, 모든 엔티티가 상속받도록 하면 일관된 감사 필드를 유지할 수 있다. @CreatedDate는 엔티티 최초 저장 시, @LastModifiedDate는 변경 감지(dirty checking) 시 자동 갱신된다. AuditorAware는 Spring Security의 SecurityContext에서 현재 사용자 정보를 가져오는 것이 일반적이다.

// JPA 표준 어노테이션
import jakarta.persistence.*;
// Spring 빈 등록용 어노테이션
import org.springframework.context.annotation.Bean;
// 설정 클래스 어노테이션
import org.springframework.context.annotation.Configuration;
// 생성자 자동 기록 어노테이션 (Spring Data 제공)
import org.springframework.data.annotation.CreatedBy;
// 생성 시각 자동 기록 어노테이션
import org.springframework.data.annotation.CreatedDate;
// 마지막 수정자 기록
import org.springframework.data.annotation.LastModifiedBy;
// 마지막 수정 시각 기록
import org.springframework.data.annotation.LastModifiedDate;
// 현재 작업자(Auditor)를 제공하는 인터페이스
import org.springframework.data.domain.AuditorAware;
// Auditing 이벤트를 처리하는 리스너
import org.springframework.data.jpa.domain.support.AuditingEntityListener;
// JPA Auditing 활성화 어노테이션
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
// 인증 정보 객체
import org.springframework.security.core.Authentication;
// SecurityContext 접근
import org.springframework.security.core.context.SecurityContextHolder;

// 시간 타입
import java.time.LocalDateTime;
// 빈 값 처리용 Optional
import java.util.Optional;

// === 1. JPA Auditing 활성화 ===
// @Configuration: Spring 설정 클래스
@Configuration
// @EnableJpaAuditing: Auditing 기능 활성화 - @CreatedDate 등이 동작하도록 만듦
@EnableJpaAuditing
public class JpaAuditingConfig {

    // @Bean: AuditorAware 빈 등록 - @CreatedBy/@LastModifiedBy가 이 빈을 통해 사용자 식별자를 얻음
    @Bean
    public AuditorAware<String> auditorProvider() {
        // 현재 로그인한 사용자 정보 반환
        // 람다로 AuditorAware 구현 - Spring Security의 SecurityContext에서 사용자명 추출
        return () -> {
            // 현재 요청 스레드의 인증 정보 조회
            Authentication authentication =
                SecurityContextHolder.getContext().getAuthentication();

            // 인증되지 않은 요청은 SYSTEM으로 기록 (배치/스케줄러 등)
            if (authentication == null || !authentication.isAuthenticated()) {
                return Optional.of("SYSTEM");
            }
            // 인증된 사용자명 반환
            return Optional.of(authentication.getName());
        };
    }
}

// === 2. BaseEntity (시간만) ===
// @MappedSuperclass: 자체 테이블이 없는 부모 클래스 - 자식 엔티티 테이블에 필드만 상속
@MappedSuperclass  // 테이블 매핑 없이 필드만 상속
// @EntityListeners: 엔티티 생명주기 이벤트 처리 리스너 등록 (Auditing 동작에 필수)
@EntityListeners(AuditingEntityListener.class)  // Auditing 이벤트 리스너
public abstract class BaseTimeEntity {

    // @CreatedDate: 엔티티 최초 persist 시점에 자동으로 현재 시각 기록
    @CreatedDate
    // updatable=false로 UPDATE 시 created_at 컬럼 제외 (불변 보장)
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    // @LastModifiedDate: 변경 감지(dirty checking)로 UPDATE 발생 시 자동 갱신
    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
}

// === 3. BaseEntity (시간 + 사용자) ===
// 시간 필드를 상속하면서 사용자 필드까지 추가하는 베이스
@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
public abstract class BaseEntity extends BaseTimeEntity {

    // @CreatedBy: persist 시 AuditorAware의 사용자명을 자동 기록
    @CreatedBy
    // 생성자 컬럼 - 한 번 기록 후 변경되지 않도록 updatable=false
    @Column(name = "created_by", updatable = false, length = 100)
    private String createdBy;

    // @LastModifiedBy: 수정 시 현재 사용자명을 자동 갱신
    @LastModifiedBy
    @Column(name = "updated_by", length = 100)
    private String updatedBy;

    public String getCreatedBy() { return createdBy; }
    public String getUpdatedBy() { return updatedBy; }
}

// === 4. 엔티티에서 상속하여 사용 ===
// 게시글 엔티티 - BaseEntity 상속으로 감사 필드 자동 적용
@Entity
@Table(name = "posts")
public class Post extends BaseEntity {
    // createdAt, updatedAt, createdBy, updatedBy 자동 관리

    // PK
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // 제목 - NOT NULL
    @Column(nullable = false)
    private String title;

    // 본문 - TEXT
    @Column(columnDefinition = "TEXT")
    private String content;

    // JPA 기본 생성자
    protected Post() {}

    // 게시글 생성 정적 팩토리
    public static Post create(String title, String content) {
        Post post = new Post();
        post.title = title;
        post.content = content;
        // createdAt, createdBy는 자동 설정됨
        return post;
    }

    // 제목/본문 변경 - dirty checking으로 트랜잭션 커밋 시 UPDATE 발생
    public void update(String title, String content) {
        this.title = title;
        this.content = content;
        // updatedAt, updatedBy는 자동 갱신됨
    }

    public Long getId() { return id; }
    public String getTitle() { return title; }
}

// 시간만 필요한 엔티티
// 시스템 로그 - 사용자 정보 없이 시간만 기록
@Entity
public class SystemLog extends BaseTimeEntity {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // 액션 종류
    private String action;
    // 상세 내용
    private String detail;

    protected SystemLog() {}
}

// === 5. @PrePersist / @PreUpdate (Auditing 없이 직접 구현) ===
// Spring Data Auditing 없이 라이프사이클 콜백으로 감사 필드를 직접 관리
@Entity
public class AuditManualEntity {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;
    // 직접 채울 시간 필드들
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    // @PrePersist: persist 호출 직전 콜백 - INSERT 직전에 시간 기록
    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    // @PreUpdate: UPDATE 직전 콜백 - dirty checking 발생 시 호출
    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }

    protected AuditManualEntity() {}
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**
- 스위치(`@EnableJpaAuditing`)와 리스너(`AuditingEntityListener`)가 둘 다 있어야 감사 어노테이션이 값을 받는다.
- `Post` 의 `create` · `update` 는 감사 필드를 전혀 건드리지 않는다 — 그것이 자동 관리의 핵심이다.
- 생성 쪽 컬럼은 `updatable = false` 로 UPDATE 에서 빼 불변을 지킨다.
- 시간용과 시간+사용자용 베이스를 나눠, 엔티티가 필요한 만큼만 상속한다.
- 원본은 public 클래스가 한 덩어리로 있으니, 실제로 컴파일하려면 클래스마다 파일을 나눈다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
