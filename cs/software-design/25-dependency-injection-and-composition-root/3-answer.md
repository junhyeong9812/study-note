# software-design/25-dependency-injection-and-composition-root — 정답

## 정답

### 1. 스스로 만들기의 비용

- 구체 클래스가 고정돼 바꾸려면 그 클래스를 고쳐야 한다(PG 교체 = 서비스 코드 수정).
- 시험할 때 진짜 DB·진짜 시계를 써야 한다. 시간 같은 숨은 입력은 테스트가 고를 수 없다.
- 테스트가 어렵다는 것은 코드가 변동 의존을 숨긴다는 뜻이라 설계 신호다. 주입하면 테스트가 그 의존을 고를 수 있다.

### 2. Composition Root

```text
 main() / 컨테이너 기동
 ┌──── Composition Root ────┐
 │ clock = Clock.systemDefaultZone() │
 │ repo  = new JdbcRepo(ds)  │
 │ svc   = new Svc(repo, clock) │   ← new는 여기
 └──────────────────────────┘
 애플리케이션 코드: 생성자로 받은 것만 쓴다
```

- Seemann 정의: 모듈을 함께 조립하는 (가급적) 유일한 위치, 진입점 가까이.
- 주입하지 않아도 되는 것: 값 객체·DTO·순수 계산 — 바꿔 끼울 일이 없고 환경에 묶이지 않는 것.

### 3. 생성 순서

(실험 A, Spring 6.2.11, 2026-10-02)

```text
  생성 C
  생성 B (C 받음)
  생성 A (B 받음)
```

- 등록 순서와 무관하게 C → B → A. 의존 그래프를 깊이 우선으로 따라가 주는 쪽을 먼저 만든 결과, 즉 위상 정렬 순서다.

### 4. 생성자 순환

- **기동 시점**(`refresh()`)에 실패한다. 바깥 예외 `UnsatisfiedDependencyException`, 원인 사슬 끝 `BeanCurrentlyInCreationException: … Requested bean is currently in creation: Is there an unresolvable circular reference …`(실험 A).
- Spring Boot 2.6부터 빈 순환 참조는 기본 금지다(2.6 릴리스 노트). 세터·필드 주입 순환을 허용하려면 `spring.main.allow-circular-references=true`(또는 `SpringApplication`의 setter)를 명시해야 한다. X(Y), Y(X) 같은 생성자 순환은 이 스위치를 켜도 같은 예외로 실패한다(실험 E).

### 5. Captive Dependency

(실험 B, 2026-10-02)

```text
  요청 alice: captive → ctx#1 user=alice | provider → ctx#2 user=alice
  요청 bob: captive → ctx#1 user=alice | provider → ctx#3 user=bob
  요청 alice: proxy → ctx#4 user=alice (주입된 클래스=Di$RequestCtx$$SpringCGLIB$$0)
  요청 bob: proxy → ctx#5 user=bob (주입된 클래스=Di$RequestCtx$$SpringCGLIB$$0)
```

- 붙잡은 판: bob의 요청에서 alice의 컨텍스트(ctx#1)가 보인다. 에러 없이 상태가 샌다.
- `ObjectProvider`: 호출마다 현재 범위의 새 객체. 범위 프록시: 싱글턴은 CGLIB 프록시를 붙잡고 프록시가 호출마다 현재 범위 객체에 위임한다.

### 6. 실패 시점

(실험 C)

- 생성자 주입: 기동 때 `UnsatisfiedDependencyException … No qualifying bean of type 'java.time.Clock'`.
- `getBean`: 기동 성공, 첫 `bill()` 호출 때 `NoSuchBeanDefinitionException`.
- 중요한 이유: 기동 실패는 배포 직후 헬스 체크·컨텍스트 로드 테스트에서 잡힌다. 첫 호출 실패는 그 기능이 처음 쓰일 때(월말 배치 등) 운영 중에 터진다. Seemann(2010)이 말한 "컴파일 시점 오류 대신 실행 시점 오류"의 실제 모습이다.

### 7. 안티패턴 넷과 평가 차이

- 5장: Control Freak · Service Locator · Ambient Context · Constrained Construction.
- `UUID.randomUUID()`·`LocalDate.now()` 직접 호출은 전역 정적 접근점에서 변동 의존(숨은 입력)을 가져온다. 해석하면 Ambient Context(책 5.3.1 "Accessing time through Ambient Context")와 구현을 직접 고정하는 Control Freak 양쪽에 걸친다. 책이 이것을 어느 항목으로 분류하는지는 본문 미확인 [?].
- Fowler(2004): Service Locator를 DI의 대안으로 소개, 둘 중 무엇이냐보다 설정과 사용의 분리가 중요하다고 결론. Seemann(2010): 의존을 숨겨 실행 시점 오류를 낳으므로 안티패턴.

### 8. 월말 청구 누락

- 원인: `LocalDate.now().getDayOfMonth() == billingDay`. 30일까지인 달에는 31일이 없다. 시간이 숨은 입력이라 테스트는 실행한 날짜만 봤다.
- 재현: `Clock`을 주입하고 `Clock.fixed`로 날짜를 고정해 훑는다.

```text
2026년 365일을 Clock.fixed로 훑음 — 청구일 31일 고객의 청구 횟수: 주입판(버그)=7회, 고친 판=12회
2026-04-30 고정: 버그판=false 고친 판=true
```

- 고친 판: `Math.min(billingDay, d.lengthOfMonth())` — 없는 날이면 말일.

### 9. `mockStatic`의 대가

- 가능했다: `mockStatic(LocalDate.class, CALLS_REAL_METHODS)` + `when(LocalDate::now).thenReturn(apr30)` → `isBillingDay(31) = false`.
- 대가 1: 인라인 목 메이커가 에이전트를 스스로 붙이며 "This will no longer work in future releases of the JDK" 경고를 냈다.
- 대가 2: 스터빙 안에서 `LocalDate.of(...)`를 부르자 `UnfinishedStubbingException`. 가로챈 클래스의 메서드를 스터빙 중에 쓰면 안 돼 값을 블록 밖에서 만들어야 했다.
- 결론: 정적 모킹은 숨은 의존을 고치지 않고 덮는다. 주입이 더 싸다.

### 10. 순환 주입 기동 실패

- 흔한 근본 원인: 한 클래스가 두 책임을 가져 서로의 일부를 필요로 한다(책 6.3.1 "SRP violation").
- 대처 순서: 순환에 걸린 빈을 메시지 사슬에서 확인 → 공통 부분을 세 번째 클래스로 추출하거나 한 방향을 이벤트로 바꾼다 → 세터(프로퍼티) 주입으로 끊기는 최후 수단(책 6.3.5 "Last resort: Breaking the cycle with Property Injection"). `@Lazy`·순환 허용 설정도 같은 부류로 본다(해석). 단 순환 허용 설정은 세터·필드 순환에만 듣고, 생성자 순환은 `@Lazy`(지연 프록시) 같은 코드 변경이 있어야 뜬다(실험 E).
