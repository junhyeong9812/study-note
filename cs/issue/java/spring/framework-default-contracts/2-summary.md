# cs/issue/java/spring/framework-default-contracts — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
[기동]
  사용자 설정 파싱 (@Configuration, @Import 된 설정 포함)
     └─ @ConditionalOnBean 평가 ← 이 시점까지 등록된 빈만 본다     ✗ 자동구성 DataSource는 아직 없음
  자동구성 (AutoConfiguration.imports 목록)
     └─ @ConditionalOnMissingBean ← 조건이 붙은 설정/빈 단위로 back-off (예: 사용자 DataSource 1개 → 자동 DataSource 생성 안 함)
  빈 생성
     ├─ 생성자 여러 개 + 표시 없음 → no-arg 선택 → 의존성 null
     ├─ 같은 타입 후보 2+ → @Primary·@Priority·파라미터명=빈이름으로도 못 고르면 주입 실패 (Lombok 생성자엔 @Qualifier 안 복사)
     ├─ 컴포넌트 스캔 + @Bean 이중 선언 → 이름 다른 빈 2개
     └─ Filter 타입 빈 → 서블릿 컨테이너에 /* 자동 등록 (체인에도 넣으면 이중 등록 — 실행 횟수는 필터 종류·순서에 따라)

[요청]
  시큐리티: securityMatcher가 맞는 "첫 체인"만 적용 → 미매칭 경로는 정책 공백
  AOP 프록시 → 외부 호출만 가로챔 → this.method()는 @Cacheable/@Transactional 우회
  @PathVariable 이름 → -parameters 메타데이터 의존 (없으면 요청 시 실패)

[영속성]
  save(할당 ID 엔티티, @Version·Persistable 없음) → "기존"으로 보고 merge (SELECT→INSERT/UPDATE)
     → 선커밋 뒤 조회한 쪽은 UPDATE로 덮어씀(무음) / 동시 조회면 둘 다 INSERT → PK 위반
  @Query DELETE → 기본은 조회 실행 → @Modifying 없으면 예외 (조용한 무효가 아니라 명시적 실패)
  @CreatedDate → 감사 활성화 없으면 조용히 null
  네이밍 전략 → 따옴표 식별자까지 소문자화 → 대소문자 구분 DB에서 테이블 없음

교정 = 기본값에 맡기지 말고 명시
  @Primary/@Qualifier · 단일 생성자 · AutoConfiguration.imports · FilterRegistrationBean(disabled)
  catch-all denyAll 체인 · 별도 빈 분리(또는 자기 프록시 경유) · Persistable/persist · @Modifying · @EnableJpaAuditing
  이름 고정(@PathVariable("id")) · zone 명시 · 조건 평가 리포트/전체 컨텍스트 IT로 확인
```

## 핵심 문장

- 프레임워크의 기본값은 "아무것도 안 적었을 때의 선택"이다 — 그 선택이 의도와 다르면 **오류 없이** 다르게 동작한다.
- 프록시 기반 AOP는 **프록시를 통과한 호출만** 가로챈다. 자기 호출은 캐시·트랜잭션을 건너뛴다 — 1순위 교정은 별도 빈 분리, 자기 프록시 경유는 프레임워크 결합을 감수하는 차선.
- 같은 타입 빈 추가는 **무자격 주입의 결정성**(`@Primary`·이름 매칭 등 보조 규칙이 없으면 모호)과 **그 타입에 `@ConditionalOnMissingBean`이 붙은 자동설정** 두 전제를 동시에 바꿀 수 있다 — 기존 빈에 `@Primary`, 새 빈은 `@Qualifier`.
- 조건 어노테이션은 **평가 시점까지 등록된 빈만** 본다. `@Import`된 설정은 자동구성보다 먼저 평가되므로 자동구성으로 편입(`AutoConfiguration.imports`)하고, 의존 대상 뒤에 평가되도록 순서(`@AutoConfiguration(after = …)`)도 명시해야 한다 — 편입만으로 순서가 보장되지는 않는다.
- `save()`는 `@Version`·`Persistable`이 없으면 ID가 채워진 엔티티를 **기존 엔티티로 보고 merge**한다 — 할당 ID 엔티티의 신규 등록은 `persist`를 강제해야 중복이 제약 위반으로 드러난다.
- 이런 결함은 단위 테스트에 잘 안 잡힌다 — **조건 평가 리포트(`--debug`)·전체 컨텍스트·실 DB 통합 테스트**와 명시적 단언으로 드러낸다.
