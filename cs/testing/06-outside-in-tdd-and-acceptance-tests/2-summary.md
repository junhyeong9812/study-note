# testing/06-outside-in-tdd-and-acceptance-tests — 이중 루프 TDD, Walking Skeleton, 인수 테스트의 추상화 수준 — 정리 (힌트)

## 해결하는 문제

단위 테스트를 아무리 잘 써도, 부품을 **조립한 결과**가 기능으로 동작하는지는 따로 확인해야 한다.

```text
  가입 기능
   [HTTP 어댑터] ─▶ [가입 유스케이스] ─▶ [저장소]
                └─▶ [조회 유스케이스] ─▶ [저장소]   ← 조립에서 저장소를 따로 만들었다

  단위 테스트: 어댑터 ✔  가입 ✔  조회 ✔  저장소 ✔   (각자 자기 테스트 안에서 올바르게 조립)
  실제 앱:     가입은 되는데, 방금 가입한 사용자가 조회되지 않는다
```

- 이 노트가 다루는 세 가지
  - *인수 테스트(acceptance test)*: 시스템을 바깥(HTTP·UI·메시지)에서 조작해 기능 하나가 사용자 관점에서 동작하는지 확인하는 테스트.
  - *이중 루프 TDD*: 바깥 루프에서 인수 테스트 하나를 빨강으로 두고, 안쪽 루프에서 단위 TDD로 부품을 채워 바깥 테스트를 초록으로 만든다.
  - *Walking Skeleton*: 기능을 넣기 전에, 빌드·배포·끝에서 끝까지의 테스트가 자동으로 도는 가장 얇은 실제 기능 한 조각을 먼저 만든다.

쉬운 예: 레고 설명서대로 부품 봉지를 하나씩 조립한다.
- 봉지마다 부품이 맞는지 확인해도, 마지막에 몸통과 날개를 이어 붙여야 비행기가 된다.
- 표지 그림(완성품)을 먼저 보고 시작하면 지금 만드는 부품이 어디에 붙는지 안다.

똑같은 구조다.\
표지 그림이 인수 테스트이고, 봉지별 확인이 단위 테스트다. 인수 테스트가 초록이 되는 순간이 "다 붙었다"는 증거다.

실무 예:
- 각 계층 단위 테스트는 초록인데 Spring 빈 설정·라우팅·직렬화 설정 누락으로 기능이 동작하지 않는다.
- 화면 버튼 위치를 바꿨더니 인수 테스트 수십 개가 한꺼번에 깨진다.
- 백엔드·프론트·배치를 계층별로 따로 완성하고 마지막 주에 붙였더니 필드 이름·형식이 대량으로 어긋난다.

## 동작·원리

### 1. 이중 루프

```text
   바깥 루프 (인수 테스트, 기능 단위 — 몇 시간~며칠 빨강)
   ┌──────────────────────────────────────────────────────────┐
   │  인수 테스트 작성 → 빨강                                  │
   │        │                                                  │
   │        ▼   안쪽 루프 (단위 테스트, 분 단위)               │
   │     ┌──────────────────────────────┐                      │
   │     │ 단위 테스트 빨강 → 초록 → 정리 │ ←─ 여러 번 돈다      │
   │     └──────────────────────────────┘                      │
   │        │ 부품이 다 차고 조립되면                          │
   │        ▼                                                  │
   │  인수 테스트 초록 → 다음 기능                             │
   └──────────────────────────────────────────────────────────┘
```

- GOOS(Freeman·Pryce 2009) 5장 "Start Each Feature with an Acceptance Test"가 이 순서를 권한다. 바깥·안쪽 두 피드백 루프 그림은 1장 "The Bigger Picture" 절에 있다 [?] — 그림 번호는 확인하지 못했다.
- 안쪽 루프 한 바퀴는 05번 노트의 Canon TDD 그대로다.
- 바깥 테스트는 오래 빨강이다. 그래서 GOOS 5장은 "진행을 재는 테스트"와 "회귀를 잡는 테스트"를 나눠 두라고 한다("Separate Tests That Measure Progress from Those That Catch Regressions"). 아직 구현 중인 인수 테스트가 CI를 계속 빨갛게 만들지 않게 하는 장치다.

### 2. Walking Skeleton — 가로로 쌓지 말고 세로로 한 줄 뚫기

```text
   계층별로 완성 (수평)                 Walking Skeleton (수직)
   ┌──────────────────────┐            ┌──┐
   │ UI      ██████████   │            │██│ UI
   │ API     ██████████   │            │██│ API
   │ 도메인  ██████████   │            │██│ 도메인
   │ DB      ██████████   │            │██│ DB
   └──────────────────────┘            │██│ 빌드·배포·E2E 테스트 자동화
   마지막에 붙인다 → 어긋남이 한꺼번에    └──┘ 첫날부터 끝에서 끝까지 돈다
```

- GOOS 4장 "Kick-Starting the Test-Driven Cycle"의 "First, Test a Walking Skeleton": "the thinnest possible slice of real functionality that we can automatically build, deploy, and test end-to-end"(2차 출처에서 인용문을 확인했다. 책 본문은 열지 못했다).
- 10장 "The Walking Skeleton"은 예제(Auction Sniper)로 이것을 실제로 만든다(GOOS 목차).
- 용어는 Alistair Cockburn에서 왔다고 알려져 있다 [?].
- 효과(저자 주장): 배포·환경·조립 문제가 기능 개발 전에 드러난다. GOOS 4장 절 제목이 "Expose Uncertainty Early"다.

### 3. 바깥에서 안으로 — 협력 객체를 mock으로 발견하기

```text
   ① 인수 테스트: "가입하면 조회된다" → 빨강
   ② 가장 바깥 객체(HTTP 어댑터)의 단위 테스트
        "POST /users는 가입 유스케이스를 부르고 201을 준다"
        → 가입 유스케이스는 아직 없다 → 인터페이스만 정하고 mock으로 대신
   ③ 가입 유스케이스의 단위 테스트
        "가입하면 저장하고 환영 메일을 보낸다"
        → 저장소·메일러가 필요하다 → 역할(인터페이스)을 정하고 mock/Fake
   ④ 저장소·메일러 어댑터를 실제로 구현(통합 테스트)
   ⑤ Composition Root에서 조립 → 인수 테스트 초록
```

- 바깥 객체의 테스트를 쓰다 보면 "이 객체가 일을 맡길 상대"가 필요해진다. 그 상대의 **역할(인터페이스)**을 이때 정한다.
  - *역할(role)*: 객체가 협력 상대에게 기대하는 메시지 묶음. 구체 클래스가 아니라 인터페이스다.
- GOOS 2장 "Test-Driven Development with Objects"의 "Support for TDD with Mock Objects" 절이 이 쓰임을 다루고, 6장에 "Internals vs Peers"(무엇을 협력 상대로 볼지) 절이 있다(목차 기준 — 본문은 열지 못했다). 여기서 mock은 **설계 도구**다. 아직 없는 협력 객체의 인터페이스를 테스트가 요구하는 모양대로 정한다.
- 이 방식은 04번 노트의 런던파(mockist)와 같은 쪽이다. 과용하면 구현에 묶인 테스트가 되는 위험도 04번이 다룬다.
- mock은 "내가 가진 타입"에만 쓴다(GOOS 8장 "Only Mock Types That You Own", 03번 노트).

### 4. 인수 테스트의 추상화 수준 — 무엇을 할지 vs 어떻게 조작할지

```text
   테스트 본문      Given 가입한 사용자가 있다 / When 같은 이메일로 다시 가입 / Then 거절된다
        │         (도메인 언어 — 화면·URL이 안 보인다)
        ▼
   테스트 DSL       user.registers("a@x.test"); user.isRejectedAsDuplicate("a@x.test");
        │         (도메인 동사)
        ▼
   드라이버         POST /users, 상태 코드 201/409 확인
        │         (HTTP·UI 세부 — 여기에만 있다)
        ▼
   시스템
```

- Dan North "Introducing BDD"(Better Software 2006년 3월호 첫 게재)의 시나리오 틀: "Given some initial context (the givens), When an event occurs, Then ensure some outcomes."
  - 같은 글의 절 제목: "Acceptance criteria should be executable".
- *BDD(Behaviour-Driven Development)*: North가 TDD를 "행위" 어휘로 다시 설명한 방식. 인수 기준을 Given-When-Then 시나리오로 적고 자동화한다.
- 추상화 수준 오류: 테스트 본문에 "버튼 #submit 클릭", "`POST /users`"처럼 **조작 단계**를 쓰면, 화면·경로가 바뀔 때마다 모든 테스트가 바뀐다. 무엇을 하는지(도메인 동사)는 본문에, 어떻게 조작하는지는 드라이버 한 곳에 둔다.

### 실험 A: 단위 테스트는 초록, 인수 테스트만 조립 누락을 잡는다

조립 코드(Composition Root)에 실수를 넣었다.

```java
public App() {
    RegisterUser register = new RegisterUser(new InMemoryUserRepository(), mailer);
    FindUser find = new FindUser(new InMemoryUserRepository());   // 조립 실수: 저장소를 따로 만듦
    api = new HttpApi(register, find);
}
```

단위 테스트는 각자 테스트 안에서 올바르게 조립한다.

```java
@Test void routes() {
    UserRepository users = new InMemoryUserRepository();   // 테스트가 스스로 올바르게 조립
    HttpApi api = new HttpApi(new RegisterUser(users, new RecordingMailer()), new FindUser(users));
    assertThat(api.handle("POST", "/users", "a@x.test")).isEqualTo(201);
    assertThat(api.handle("GET", "/users/a@x.test", "")).isEqualTo(200);
}
```

(실험, maven:3.9-eclipse-temurin-21 이미지 — Maven 3.9.16 · JDK 21.0.11 · JUnit 5.13.4 · Mockito 5.24.0 · AssertJ 3.27.3 · JDK 내장 `com.sun.net.httpserver`·`java.net.http.HttpClient`, 2026-10-03)

```text
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.290 s -- in app.FindUserTest
[ERROR] Tests run: 3, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 1.566 s <<< FAILURE! -- in app.AcceptanceRawTest
expected: 200
 but was: 404
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.017 s -- in app.HttpApiTest
[ERROR] Tests run: 3, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 0.147 s <<< FAILURE! -- in app.AcceptanceDslTest
Expecting value to be true but was false
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 2.475 s -- in app.RegisterUserTest
...
[ERROR] Tests run: 10, Failures: 2, Errors: 0, Skipped: 0
```

- 관찰: 단위 테스트 4개(가입 2·조회 1·어댑터 1)는 모두 초록이다. 인수 테스트 두 묶음에서 "가입 후 조회" 시나리오만 빨강이다.
- 해석: 단위 테스트는 **자기 안에서 조립**하므로 실제 조립 코드를 한 줄도 실행하지 않는다. 조립 실수는 실제 `App`을 띄우는 테스트만 잡는다.
- 저장소 하나를 만들어 둘에 주입하도록 고치자 `Tests run: 10, Failures: 0`.
- DSL 판의 실패 메시지(`Expecting value to be true but was false`)는 무엇이 틀렸는지 말해 주지 않는다. 실험 B의 개선 드라이버가 이것을 고친다.

### 실험 B: 경로가 바뀌면 몇 군데를 고치나 — 그리고 드라이버가 실패를 삼키면

같은 인수 시나리오 3개를 두 방식으로 썼다. 서버 경로를 `/users` → `/v2/members`로 바꾸고 테스트는 그대로 돌렸다.

```text
(실험, 같은 환경 — 서버 경로만 변경)
[ERROR] Tests run: 3, Failures: 3, Errors: 0, Skipped: 0, Time elapsed: 1.433 s <<< FAILURE! -- in app.AcceptanceRawTest
[ERROR] Tests run: 1, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 0.008 s <<< FAILURE! -- in app.HttpApiTest
[ERROR] Tests run: 3, Failures: 2, Errors: 0, Skipped: 0, Time elapsed: 0.214 s <<< FAILURE! -- in app.AcceptanceDslTest
[ERROR] Tests run: 10, Failures: 6, Errors: 0, Skipped: 0

$ grep -c '"/users' AcceptanceRawTest.java AcceptanceDslTest.java UserDriver.java HttpApiTest.java
src/test/java/app/AcceptanceDslTest.java:0
src/test/java/app/UserDriver.java:2
src/test/java/app/AcceptanceRawTest.java:5
src/test/java/app/HttpApiTest.java:3
```

| 방식 | 경로 리터럴이 있는 곳 | 드라이버만 고친 뒤 |
|---|---|---|
| Raw(테스트 본문에 HTTP 세부) | 테스트 본문 5곳 | `Tests run: 3, Failures: 3` — 본문을 다 고쳐야 한다 |
| DSL(도메인 동사 + 드라이버) | 드라이버 2곳, 본문 0곳 | `Tests run: 3, Failures: 0` |

- 관찰 1: 고칠 자리 수가 5 대 2였다. 단위 테스트 `HttpApiTest`(경로 리터럴 3곳)도 두 방식과 무관하게 실패했다 — 표는 인수 테스트만 센다. 테스트 시나리오가 늘수록 Raw 쪽 자리는 늘고, DSL 쪽은 드라이버에 머문다(시나리오 3개짜리 예시에서의 측정).
- 관찰 2: **DSL 판은 3개가 아니라 2개만 실패했다.** 중복 가입 시나리오가 경로가 틀렸는데도 통과했다.
  - 원인: 첫 드라이버는 `register()`가 `201`이면 `true`, 아니면 `false`를 돌려줬다. 404도 `false`라 "중복이라 거절됨(false)"과 구별되지 않았다.
  - 교훈: 드라이버가 실패를 값으로 삼키면 **거짓 통과**가 생긴다. 드라이버는 기대한 응답이 아니면 그 자리에서 실패해야 한다.

개선 드라이버(기대 상태 코드를 드라이버가 확인):

```java
private static void expect(int want, int got, String what) {
    if (got != want) throw new AssertionError(what + ": expected HTTP " + want + " but was " + got);
}
void registers(String email)             { expect(201, send("POST", "/v2/members", email), "register " + email); }
void isRejectedAsDuplicate(String email) { expect(409, send("POST", "/v2/members", email), "duplicate " + email); }
void isRegistered(String email)          { expect(200, send("GET", "/v2/members/" + email, ""), "lookup " + email); }
```

```text
(실험, 같은 환경 — 개선 드라이버, 서버 경로를 다시 /v3/accounts로 변경)
[ERROR] Tests run: 3, Failures: 3, Errors: 0, Skipped: 0, Time elapsed: 0.118 s <<< FAILURE! -- in app.AcceptanceDslTest
java.lang.AssertionError: register a@x.test: expected HTTP 201 but was 404
```

- 3개 모두 실패했고, 메시지가 어느 단계·어떤 응답인지 말해 준다.

## 쓰이는 자료구조·알고리즘

- **객체 그래프와 공유 노드**: 조립은 의존 그래프를 만드는 일이다. 실험 A의 버그는 "저장소 노드 하나를 두 유스케이스가 공유"해야 할 그래프를 "노드 두 개"로 만든 것이다. 그래프 모양을 확인하는 것은 실제 조립을 띄우는 테스트뿐이다. 조립 원칙은 software-design [25-dependency-injection-and-composition-root](../../software-design/25-dependency-injection-and-composition-root/2-summary.md).
- **테스트 DSL = 계층 구조**: 시나리오(도메인 언어) → DSL(도메인 동사) → 드라이버(프로토콜·UI). 바뀌는 이유가 다른 것을 다른 계층에 둔다. 경로·선택자 변경은 드라이버 계층에서 끝난다.
- **포트와 어댑터**: 바깥에서 안으로 발견한 역할(인터페이스)이 포트가 되고, 실제 구현이 어댑터가 된다. software-design [38-layered-hexagonal-clean](../../software-design/38-layered-hexagonal-clean/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 실무 순서

1. **Walking Skeleton**: 아무 기능 없는 앱이라도 빌드 → 배포(또는 테스트 환경 기동) → 인수 테스트 한 개가 끝에서 끝까지 자동으로 도는 파이프라인을 먼저 만든다.
2. 기능마다 인수 테스트를 **도메인 언어로** 하나 쓴다. 빨강을 확인한다. 아직 구현 중인 것은 "진행" 묶음에 둔다.
3. 가장 바깥 객체부터 단위 TDD를 한다. 필요한 협력 객체는 인터페이스를 정하고 mock/Fake로 대신한다.
4. 안쪽으로 내려가며 각 역할을 구현한다. 외부 시스템에 닿는 어댑터는 실제 의존과 통합 테스트한다(08번).
5. Composition Root에서 조립한다. 인수 테스트가 초록이 되면 "회귀" 묶음으로 옮긴다.

### 2. Given-When-Then을 JUnit으로

```java
@Test void duplicateRegistrationIsRejected() {
    // Given 가입한 사용자가 있다
    user.registers("a@x.test");
    // When 같은 이메일로 다시 가입하면 / Then 거절된다
    user.isRejectedAsDuplicate("a@x.test");
}
```

- 도구(Cucumber 등 Gherkin 파일)가 없어도 같은 구조를 쓸 수 있다. 중요한 것은 본문에 조작 단계가 아니라 도메인 동사가 오는 것이다.
- 도메인 동사는 업무 쪽이 쓰는 말과 맞춘다. domain-modeling [03-ubiquitous-language](../../domain-modeling/03-ubiquitous-language/2-summary.md).

### 3. 진단

```bash
# 인수 테스트 본문에 프로토콜·UI 세부가 새어 있나(드라이버 밖의 경로·선택자 리터럴 수)
grep -rnE '"/(api|users|v[0-9])|By\.(id|css|xpath)|#[a-z-]+"' src/test/java --include='*Acceptance*' | wc -l
# 드라이버가 실패를 값으로 삼키나 — boolean을 돌려주는 드라이버 메서드 찾기
grep -rnE 'boolean [a-zA-Z]+\(' src/test/java --include='*Driver.java'
```

- 점검 질문
  - 단위 테스트 묶음에 실제 Composition Root를 실행하는 테스트가 하나라도 있나?
  - 화면·경로를 하나 바꾸면 테스트 몇 개를 고쳐야 하나?
  - 인수 테스트가 실패했을 때 메시지만 보고 어느 단계에서 무엇을 받았는지 알 수 있나?

## 장애 시나리오와 대처

### 1. 단위 테스트만 초록 → 기능 전체는 동작 안 함(조립 누락) (⚠ 커리큘럼)

- 현상: 배포 뒤 "가입은 되는데 조회가 안 된다".
- 보이는 형태: 조회 API가 404. 단위 테스트는 전부 초록(실험 A: 4개 초록). 인수 테스트가 있었다면 `expected: 200 but was: 404`.
- 원인: 단위 테스트는 각자 올바르게 조립하므로 실제 조립 코드(빈 설정·Composition Root·라우팅)가 실행되지 않는다.
- 대처
  - 실제 앱을 띄우는 인수 테스트를 기능마다 최소 하나 둔다.
  - 조립을 한 곳(Composition Root)에 모아, 그 한 곳을 실행하는 테스트가 모든 연결을 지나가게 한다.

### 2. UI 조작 단계로 쓴 인수 테스트 → 화면 변경마다 전부 파손 (⚠ 커리큘럼)

- 현상: 버튼 문구·경로·필드 이름을 바꾼 PR마다 인수 테스트 수십 개를 고친다. 결국 인수 테스트를 끄거나 무시한다.
- 보이는 형태: 같은 선택자·URL 리터럴이 테스트 본문 수십 곳에 있다. 실험 B에서 경로 변경 하나에 Raw 본문 5곳.
- 원인: 추상화 수준 오류. 무엇을 하는지(가입한다)와 어떻게 조작하는지(`POST /users`, `#submit` 클릭)를 같은 층에 썼다.
- 대처: 테스트 DSL(도메인 동사)과 드라이버를 나눈다. 조작 세부는 드라이버 한 곳에만 둔다. UI 선택자 고르는 법은 18번 노트.

### 3. 골격 없이 계층별로 완성 → 통합 시점에 대량 불일치 (⚠ 커리큘럼)

- 현상: 계층별로 두 달 개발 후 붙이는 주에 필드 이름·날짜 형식·인증 흐름 불일치가 수십 건 나온다. 배포 스크립트도 처음 돌려 본다.
- 보이는 형태: 통합 첫 주의 버그 목록이 기능 버그보다 연결 버그로 가득하다.
- 원인: 끝에서 끝까지 도는 경로가 마지막에야 생겼다. 불확실성이 마지막까지 숨어 있었다.
- 대처: Walking Skeleton을 첫 기능보다 먼저 만든다. 이후 기능은 그 골격에 세로로 한 조각씩 붙인다.

### 4. 드라이버가 실패를 삼킴 → 거짓 통과

- 현상: 서버 경로가 잘못됐는데 "중복 가입 거절" 인수 테스트가 초록이다.
- 보이는 형태: 실험 B — DSL 판 3개 중 2개만 실패. 남은 하나는 404를 "거절(false)"로 해석했다.
- 원인: 드라이버가 응답을 `boolean`으로 줄여, 서로 다른 실패(404·409·500)가 같은 값이 됐다.
- 대처: 드라이버는 기대한 응답을 직접 확인하고 아니면 예외를 던진다. 실패 메시지에 단계와 받은 응답을 넣는다(개선 드라이버: `register a@x.test: expected HTTP 201 but was 404`).

### 5. 바깥에서 안으로 쓴 mock이 실제 구현과 어긋남

- 현상: 협력 객체를 mock으로 발견해 인터페이스를 정했는데, 나중에 만든 실제 구현이 그 인터페이스의 기대(예외·순서)와 다르게 동작한다.
- 원인: mock은 발견 단계의 설계 도구였는데, 실제 구현이 생긴 뒤에도 계약을 확인하는 테스트가 없다.
- 대처: 실제 구현이 생기면 계약 테스트를 붙이고(03번), 인수 테스트가 그 경로를 실제로 지나가게 한다.

## 핵심 문장

- 이중 루프 TDD는 인수 테스트(바깥, 기능 단위)를 빨강으로 두고 단위 TDD(안쪽)로 부품을 채워 바깥을 초록으로 만든다.
- 단위 테스트는 각자 조립하므로 실제 조립 코드를 실행하지 않는다. 실험에서 조립 실수를 잡은 것은 인수 테스트뿐이었다.
- Walking Skeleton은 빌드·배포·끝에서 끝까지의 테스트가 자동으로 도는 가장 얇은 실제 기능 조각이다. 연결 문제를 첫날 드러낸다.
- 바깥에서 안으로 갈 때 mock은 아직 없는 협력 객체의 역할(인터페이스)을 정하는 설계 도구다.
- 인수 테스트 본문에는 도메인 동사를, 조작 세부는 드라이버 한 곳에 둔다. 드라이버는 실패를 값으로 삼키지 말고 그 자리에서 실패해야 한다.

## 관련 주제·근거

- 선행
  - [05-tdd](../05-tdd/2-summary.md) — 안쪽 루프의 사이클
  - [04-classical-vs-london](../04-classical-vs-london/2-summary.md) — 런던파(mockist)와 그 위험
- 후속·연결
  - [03-test-doubles](../03-test-doubles/2-summary.md) — mock·Fake와 계약 테스트
  - [08-integration-tests-real-dependencies](../08-integration-tests-real-dependencies/2-summary.md) — 어댑터를 실제 의존과 시험
  - [18-e2e-and-ui-testing](../18-e2e-and-ui-testing/2-summary.md) — UI 선택자와 E2E 비용
  - software-design [25-dependency-injection-and-composition-root](../../software-design/25-dependency-injection-and-composition-root/2-summary.md) — 조립은 한 곳에서
  - software-design [38-layered-hexagonal-clean](../../software-design/38-layered-hexagonal-clean/2-summary.md) — 포트와 어댑터
  - domain-modeling [03-ubiquitous-language](../../domain-modeling/03-ubiquitous-language/2-summary.md) — 시나리오의 도메인 언어
- 문헌
  - Freeman·Pryce, 『Growing Object-Oriented Software, Guided by Tests』(Addison-Wesley 2009) — 1장 "The Bigger Picture"·"Levels of Testing", 2장 "Test-Driven Development with Objects"(Support for TDD with Mock Objects 절), 4장 "Kick-Starting the Test-Driven Cycle"(First, Test a Walking Skeleton · Expose Uncertainty Early), 5장 "Maintaining the Test-Driven Cycle"(Start Each Feature with an Acceptance Test · Separate Tests That Measure Progress from Those That Catch Regressions), 6장 "Internals vs Peers", 8장 "Only Mock Types That You Own", 10장 "The Walking Skeleton" — 목차 <https://growing-object-oriented-software.com/toc.html>
  - Dan North, "Introducing BDD" — Better Software 2006년 3월호 첫 게재(블로그 게시 2006-09-20), Given-When-Then 틀, "Acceptance criteria should be executable" <https://dannorth.net/blog/introducing-bdd/>
- 실험 목록(코드는 scratchpad `ts/03/outside`, 개선 드라이버는 `ts/03/outside2`, 조립 실수 원본은 `outside/App.java.buggy.txt`)
  - `maven:3.9-eclipse-temurin-21` 이미지(Maven 3.9.16, JDK 21.0.11), `--cpus=2 -m 1g`, JUnit 5.13.4 · Mockito 5.24.0 · AssertJ 3.27.3, HTTP 서버는 127.0.0.1 임의 포트(컨테이너 안)
  - A: Composition Root에서 저장소를 두 개 만든 조립 실수 — 단위 4개 초록, 인수 테스트(Raw·DSL) 각 1개 실패, 고친 뒤 10개 통과
  - B: 서버 경로 변경 — 경로 리터럴 Raw 본문 5곳 vs 드라이버 2곳, 첫 DSL 드라이버의 거짓 통과(3개 중 2개만 실패), 개선 드라이버는 3개 모두 실패하며 단계·응답을 보고
