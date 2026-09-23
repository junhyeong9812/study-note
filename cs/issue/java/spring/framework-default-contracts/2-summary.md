# cs/issue/java/spring/framework-default-contracts — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
[기동]
  사용자 설정 파싱 (@Configuration, @Import 된 설정 포함)
     └─ @ConditionalOnBean 평가 ← 이 시점까지 등록된 빈만 본다     ✗ 자동구성 DataSource는 아직 없음
  자동구성 (AutoConfiguration.imports 목록)
     └─ @ConditionalOnMissingBean ← 같은 타입 빈 1개라도 있으면 통째로 back-off
  빈 생성
     ├─ 생성자 여러 개 + 표시 없음 → no-arg 선택 → 의존성 null
     ├─ 같은 타입 후보 2+ → 무자격 주입 실패 (Lombok 생성자엔 @Qualifier 안 복사)
     ├─ 컴포넌트 스캔 + @Bean 이중 선언 → 이름 다른 빈 2개
     └─ Filter 타입 빈 → 서블릿 컨테이너에 /* 자동 등록

[요청]
  시큐리티: securityMatcher가 맞는 "첫 체인"만 적용 → 미매칭 경로는 정책 공백
  AOP 프록시 → 외부 호출만 가로챔 → this.method()는 @Cacheable/@Transactional 우회
  @PathVariable 이름 → -parameters 메타데이터 의존 (없으면 요청 시 실패)

[영속성]
  save(할당 ID 엔티티) → "기존"으로 보고 merge (SELECT→UPDATE) → 동시 insert 충돌 미감지
  @Query DELETE → 기본은 조회 실행 → @Modifying 없으면 예외
  @CreatedDate → 감사 활성화 없으면 조용히 null
  네이밍 전략 → 따옴표 식별자까지 소문자화 → 대소문자 구분 DB에서 테이블 없음

교정 = 기본값에 맡기지 말고 명시
  @Primary/@Qualifier · 단일 생성자 · AutoConfiguration.imports · FilterRegistrationBean(disabled)
  catch-all denyAll 체인 · 자기 프록시 경유 · Persistable/persist · @Modifying · @EnableJpaAuditing
  이름 고정(@PathVariable("id")) · zone 명시 · 조건 평가 리포트/전체 컨텍스트 IT로 확인
```

## 핵심 문장

- 프레임워크의 기본값은 "아무것도 안 적었을 때의 선택"이다 — 그 선택이 의도와 다르면 **오류 없이** 다르게 동작한다.
- 프록시 기반 AOP는 **프록시를 통과한 호출만** 가로챈다. 자기 호출은 캐시·트랜잭션을 건너뛴다.
- 같은 타입 빈 추가는 **무자격 주입의 결정성**과 **`@ConditionalOnMissingBean` 자동설정** 두 전제를 동시에 바꾼다 — 기존 빈에 `@Primary`, 새 빈은 `@Qualifier`.
- 조건 어노테이션은 **평가 시점까지 등록된 빈만** 본다. `@Import`된 설정은 자동구성보다 먼저 평가되므로 자동구성 순서에 편입(`AutoConfiguration.imports`)해야 한다.
- `save()`는 ID가 채워진 엔티티를 **기존 엔티티로 보고 merge**한다 — 할당 ID 엔티티의 신규 등록은 `persist`를 강제한다.
- 이런 결함은 단위 테스트에 잘 안 잡힌다 — **조건 평가 리포트(`--debug`)·전체 컨텍스트·실 DB 통합 테스트**와 명시적 단언으로 드러낸다.
