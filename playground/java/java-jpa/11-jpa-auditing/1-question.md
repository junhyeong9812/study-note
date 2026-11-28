# java/java-jpa/11 — JPA Auditing — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 저장 전에 생성 시각을 읽으면 (예측)

```java
// 질문용 발췌
Post post = Post.create("안녕", "첫 글");
System.out.println(post.getCreatedAt());
```

- `repository.save(post)` 를 부르기 전인 이 시점에 무엇이 찍힌다고 보나?

### 2. 트랜잭션 안에서 `update` 를 부르고 커밋하면 (예측)

```java
// 질문용 발췌 — 이미 저장된 post 를 다른 사용자가 수정
@Transactional
public void edit(Long id) {
    Post post = postRepository.findById(id).orElseThrow();
    post.update("고친 제목", "고친 본문");
}   // 커밋
```

- 커밋 뒤 `createdAt` · `createdBy` · `updatedAt` · `updatedBy` 네 필드 가운데 값이 바뀌는 것은 어느 것인가?

### 3. 같은 값으로 `update` 를 부르면 (예측)

```java
// 질문용 발췌 — 저장된 제목·본문이 이미 "A", "B" 인 post
@Transactional
public void touch(Long id) {
    Post post = postRepository.findById(id).orElseThrow();
    post.update("A", "B");
}
```

- 커밋 뒤 `updatedAt` 은 어떻게 된다고 보나?

### 4. 어노테이션을 붙였는데 시각이 비어 있는 까닭 (왜)

- 필드에 `@CreatedDate` 를 붙였는데 값이 채워지지 않는다면, 원본 설정에서 빠졌을 수 있는 두 가지는 무엇이고 각각 왜 필요한가?

### 5. 생성 컬럼에 `updatable = false` 를 다는 까닭 (왜)

- `created_at` 과 `created_by` 에 `updatable = false` 를 주는 것은 무엇을 막기 위해서인가?

### 6. 로그인 없이 도는 배치 작업에서 `created_by` (경계)

- 스케줄러가 인증 정보 없이 `Post` 를 저장하면 원본의 `auditorProvider` 는 `created_by` 에 무엇을 넘기나?

### 7. `SystemLog` 가 기록하는 감사 필드의 범위 (경계)

- `SystemLog` 를 저장하면 감사 필드 가운데 어떤 것이 생기고 어떤 것은 아예 없는가?

### 8. `@MappedSuperclass` 와 테이블 (연결)

- `BaseTimeEntity` 와 `BaseEntity` 에는 테이블이 생기지 않는데, 그 필드들은 데이터베이스의 어디에 컬럼으로 나타나나?

### 9. `@PrePersist` / `@PreUpdate` 와 Spring Data Auditing (연결)

- `AuditManualEntity` 방식과 `@CreatedDate` 방식은 무엇을 기대어 동작하며, 「누가」 를 기록하는 면에서는 어떤 차이가 있나?

## 실습

### 실습 1. 감사 필드를 자동으로 채우는 엔티티 계층 만들기

**만들 것** — Spring Data JPA Auditing 을 켜고, 시간용 · 시간+사용자용 베이스 엔티티를 만들어 게시글과 시스템 로그가 상속하게 한다. 비교를 위해 JPA 콜백으로 시각을 직접 채우는 엔티티도 하나 만든다.

**준비물** — Spring Boot 프로젝트에 Spring Data JPA · Spring Security · 데이터베이스 드라이버(H2 등)가 필요하다.

**요구 조건**

1단계 — 설정
1. 설정 클래스 `JpaAuditingConfig` 에서 JPA Auditing 을 켠다.
2. `AuditorAware<String>` 빈 `auditorProvider` 를 등록한다 — `SecurityContextHolder` 에서 현재 인증 정보를 꺼내, 없거나 인증되지 않았으면 `"SYSTEM"`, 인증되었으면 사용자명을 `Optional` 로 돌려준다.

2단계 — 베이스 클래스
3. `BaseTimeEntity` 는 테이블 없이 필드만 물려주는 추상 클래스이고, Auditing 리스너가 걸려 있다.
4. `BaseTimeEntity.createdAt` 은 최초 저장 시각을 자동으로 받고 수정 때 바뀌지 않는다.
5. `BaseTimeEntity.updatedAt` 은 변경 감지로 수정될 때 시각을 자동으로 받는다.
6. `BaseEntity` 는 `BaseTimeEntity` 를 상속한 같은 성격의 추상 클래스이고, `createdBy`(최초 저장자, 수정 불가)와 `updatedBy`(마지막 수정자)를 자동으로 받는다.
7. 두 베이스에 각 필드의 getter 를 둔다.

3단계 — 엔티티
8. `Post` 는 `posts` 테이블에 매핑되고 `BaseEntity` 를 상속한다 — 자동 증가 `id`, 필수 `title`, `TEXT` 형 `content` 를 가진다.
9. `Post` 는 `protected` 기본 생성자, 정적 팩토리 `create(title, content)`, 제목 · 본문만 바꾸는 `update(title, content)`, `getId()` · `getTitle()` 을 가진다 — 감사 필드는 어디서도 손으로 넣지 않는다.
10. `SystemLog` 는 `BaseTimeEntity` 만 상속하고 `id` · `action` · `detail` 을 가진다.

4단계 — 직접 구현 비교
11. `AuditManualEntity` 는 Auditing 없이 `createdAt` · `updatedAt` 을 갖고, persist 직전에 둘 다 현재 시각으로, UPDATE 직전에 `updatedAt` 만 현재 시각으로 채운다.

**시작 코드**

```java
import jakarta.persistence.*;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.annotation.CreatedBy;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedBy;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.domain.AuditorAware;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

import java.time.LocalDateTime;
import java.util.Optional;

@Configuration
// TODO: Auditing 기능 켜기
public class JpaAuditingConfig {

    @Bean
    public AuditorAware<String> auditorProvider() {
        // TODO: SecurityContext 에서 인증 정보를 꺼내
        //       없거나 인증 안 됐으면 "SYSTEM", 아니면 사용자명
        return null;
    }
}

// TODO: 테이블 없이 필드만 물려주기 + Auditing 리스너 등록
public abstract class BaseTimeEntity {

    // TODO: 최초 저장 시각 자동 기록
    @Column(name = "created_at", nullable = false /* TODO: 수정 때 제외 */)
    private LocalDateTime createdAt;

    // TODO: 수정 시각 자동 기록
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    // TODO: getter 두 개
}

// TODO: BaseTimeEntity 와 같은 두 어노테이션
public abstract class BaseEntity /* TODO: 상속 */ {

    // TODO: 최초 저장자 자동 기록
    @Column(name = "created_by", length = 100 /* TODO: 수정 때 제외 */)
    private String createdBy;

    // TODO: 마지막 수정자 자동 기록
    @Column(name = "updated_by", length = 100)
    private String updatedBy;

    // TODO: getter 두 개
}

@Entity
@Table(name = "posts")
public class Post /* TODO: 상속 */ {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String title;

    @Column(columnDefinition = "TEXT")
    private String content;

    protected Post() {}

    public static Post create(String title, String content) {
        // TODO: 제목·본문만 채운 새 Post
        return null;
    }

    public void update(String title, String content) {
        // TODO: 제목·본문만 바꾸기
    }

    public Long getId() { return id; }
    public String getTitle() { return title; }
}

@Entity
public class SystemLog /* TODO: 시간만 상속 */ {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String action;
    private String detail;

    protected SystemLog() {}
}

@Entity
public class AuditManualEntity {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    // TODO: persist 직전 콜백 — 두 시각 채우기

    // TODO: UPDATE 직전 콜백 — updatedAt 채우기

    protected AuditManualEntity() {}
}
```

**확인 방법** — 클래스마다 파일을 나눠 넣고, `@SpringBootTest` 테스트에서 `Post` 를 `save` 한 뒤 네 감사 필드를 찍어 본다. 이어 트랜잭션 안에서 `update` 를 부르고 커밋한 뒤 다시 조회해 `createdAt` 은 그대로이고 `updatedAt` 만 달라졌는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
