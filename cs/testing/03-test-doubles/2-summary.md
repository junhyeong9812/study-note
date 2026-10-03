# testing/03-test-doubles — Dummy·Fake·Stub·Spy·Mock — 정리 (힌트)

## 해결하는 문제

시험하려는 코드가 다른 부품에 기대고 있으면, 그 부품 때문에 테스트를 못 쓰거나 못 믿게 된다.

```text
  주문 서비스(시험 대상)
      │ 계좌 잔액을 묻는다          → 실제 DB가 있어야 한다(느림, 데이터 준비)
      │ 결제를 요청한다            → 실제 PG사 호출(돈이 나간다, 실패 응답을 마음대로 못 만든다)
      │ 환영 메일을 보낸다          → 실제 SMTP(테스트마다 메일 발송)
      ▼
  "결제 실패면 주문을 취소한다"를 확인하고 싶은데, 결제 실패를 일부러 일으킬 방법이 없다
```

- 해법: 기대는 부품을 **테스트용 대역**으로 바꿔 끼운다.
  - *테스트 더블(Test Double)*: 테스트에서 실제 부품 대신 끼우는 객체. Meszaros가 영화의 스턴트 대역(stunt double)에 빗대 붙인 이름이다(xunitpatterns.com "Test Double").
  - *SUT(System Under Test)*: 지금 시험하는 코드.
  - *DOC(Depended-On Component)*: SUT가 기대는 부품. 더블은 DOC를 대신하지 SUT를 대신하지 않는다.

쉬운 예: 소방 훈련에서 진짜 불 대신 연기 발생기를 쓴다.
- 대피 절차(SUT)는 진짜로 돌린다. 불(DOC)만 가짜다.
- 연기 발생기가 진짜 불과 너무 다르면(연기가 위로 안 올라간다) 훈련은 통과해도 실제 화재에서 틀린다.

똑같은 구조다.\
더블은 SUT를 시험 가능하게 만든다. 대신 **더블이 실제 부품과 다르게 굴면 테스트는 초록인데 운영에서 깨진다.** 이 노트의 실험이 그 경우를 재현한다.

실무 예:
- 저장소(Repository)를 Mockito로 흉내 내 서비스 테스트는 전부 초록인데, 실제 DB 구현은 "없으면 예외"라 운영에서 500이 난다.
- 외부 결제 API의 실패 응답(타임아웃·거절)을 재현하려고 Stub을 쓴다.
- 메일 발송 여부는 결과 상태로 볼 수 없어 Spy·Mock으로 호출을 확인한다.

## 동작·원리

### 1. 간접 입력과 간접 출력 — 더블이 끼어드는 두 방향

```text
                  직접 입력(인자)            직접 출력(반환값)
   테스트 ──────────────────▶  SUT  ──────────────────▶ 테스트
                               │  ▲
            간접 출력(호출·인자) │  │ 간접 입력(DOC의 반환값·예외)
                               ▼  │
                               DOC  ◀── 여기를 더블로 바꾼다
```

- *간접 입력(indirect input)*: SUT가 DOC를 불러 **받아 오는** 값. 반환값·예외. 테스트가 인자로 직접 넣을 수 없다.
- *간접 출력(indirect output)*: SUT가 DOC에 **내보내는** 호출과 인자. SUT의 반환값에 나타나지 않는다.
- Meszaros의 분류는 이 두 방향으로 갈린다(xunitpatterns.com의 각 패턴 요약 문장).
  - Test Stub: "feeds the desired indirect inputs into the system under test" — 간접 입력을 조종한다.
  - Test Spy: "capture the indirect output calls ... for later verification by the test" — 간접 출력을 기록해 두고 테스트가 나중에 확인한다.
  - Mock Object: "verifies it is being used correctly by the SUT" — 간접 출력을 더블 자신이 기대와 대조한다.

### 2. 다섯 가지 더블 — Meszaros 분류(Fowler 정리)

```text
   무엇을 하나                         이름
   ─────────────────────────────────────────────────
   자리만 채운다(호출되지 않는다)      Dummy
   동작하는 가벼운 구현으로 바꾼다     Fake      (예: HashMap 저장소, 인메모리 DB)
   정해 둔 답을 돌려준다(입력 조종)    Stub
   Stub + 받은 호출을 기록한다         Spy       → 테스트가 기록을 꺼내 단언
   기대 호출을 미리 프로그램한다       Mock      → 더블이 스스로 기대와 대조
```

Fowler "Mocks Aren't Stubs"(2004, 2007 개정)가 Meszaros의 정의를 이렇게 옮겼다.
- Dummy: "passed around but never actually used. Usually they are just used to fill parameter lists."
- Fake: "actually have working implementations, but usually take some shortcut which makes them not suitable for production."
- Stub: "provide canned answers to calls made during the test".
- Spy: "stubs that also record some information based on how they were called."
- Mock: "pre-programmed with expectations which form a specification of the calls they are expected to receive."

같은 글이 검증 방식도 둘로 나눈다.
- *상태 검증(state verification)*: 실행 뒤 SUT와 협력 객체의 **상태**를 본다.
- *행위 검증(behavior verification)*: SUT가 협력 객체를 **올바르게 불렀는지** 본다. Mock은 행위 검증을 위한 더블이다.

### 3. 출처마다 다른 말 — 섞지 않는다

| 출처 | 분류 | 핵심 주장 |
|---|---|---|
| Meszaros 『xUnit Test Patterns』(2007), Fowler | Dummy·Fake·Stub·Spy·Mock 다섯 | Stub = 입력, Spy·Mock = 출력 검증. Mock은 기대를 미리 프로그램한다 |
| Khorikov 『Unit Testing PPP』(2020) 5장 · 블로그 "When to Mock" | 크게 둘: **mock**(mock·spy)과 **stub**(stub·dummy·fake) | mock = 나가는 상호작용(상태를 바꾸는 호출) 흉내·검사, stub = 들어오는 상호작용(입력 데이터) 흉내. "never assert interactions with stubs". 관리형 의존(앱 전용 DB)은 실제로, 비관리형 의존(SMTP·메시지 버스)만 mock |
| SWE@G 13장 | 기법 셋: **faking·stubbing·interaction testing** + 실제 구현 | "Prefer Realism Over Isolation". 상태 검증을 상호작용 검증보다 선호. Fake는 실제 구현을 가진 팀이 만들고, 자기 테스트(계약 테스트)를 가져야 한다 |
| Mockito(라이브러리) | `mock()`이 만든 객체 하나가 stub(`when`)도 되고 mock(`verify`)도 된다(Mockito의 용어) | `verify`는 SUT 실행 **뒤에** 테스트가 호출 기록을 대조한다 — Meszaros 분류로는 Mock Object(더블이 미리 받은 기대와 스스로 대조)보다 Test Spy("for later verification by the test")에 가깝다. `spy(obj)`는 실제 객체의 **복사본**으로 부분 mock을 만든다. stub 안 한 메서드는 진짜 코드가 그 복사본 위에서 돈다. 원본에 호출을 넘기지 않는다 — Meszaros의 Spy와 뜻이 다르다(Mockito javadoc 13절 "Important gotcha on spying real objects!") |

- 결론: "mock"이라는 말은 문맥마다 뜻이 다르다. 대화에서는 "입력을 조종하는 더블인가, 출력을 검증하는 더블인가"로 물으면 엇갈림이 줄어든다.
- Khorikov의 정의와 관리형·비관리형 구분은 enterprisecraftsmanship.com "When to Mock"(2020-04-15)에서 확인했다. 책은 장 제목(5장 "Mocks and test fragility", 9장 "Mocking best practices")까지만 확인했다.

### 4. 더블은 "실제 부품에 대한 믿음"을 코드로 굳힌 것이다

```text
   실제 계약(구현이 지키는 것)          Mockito stub(테스트 작성자의 믿음)
   findBalance("없는 id") → 예외        when(findBalance("nope")).thenReturn(-1L)
   recentTransfers → 최신 것이 먼저      thenReturn(List.of(옛 것, 새 것))
          │                                     │
          └──────────── 둘이 다르면 ───────────┘
                     SUT 테스트는 초록, 운영은 실패
```

- Stub은 실제 구현을 한 줄도 실행하지 않는다. SWE@G 13장: "With stubbing, there is no way to ensure the function being stubbed behaves like the real implementation."
- Fake는 실제 구현처럼 동작하므로 이 틈이 작다. 대신 Fake 자체가 실제와 같은지 **계약 테스트**로 확인해야 한다.
  - *계약 테스트(contract test)*: 인터페이스의 공개 동작에 대한 같은 테스트 묶음을 실제 구현과 Fake 양쪽에 돌리는 것(SWE@G 13장 "Fakes Should Be Tested"). 서비스 간 소비자 주도 계약 테스트는 13번 노트에서 따로 다룬다.

### 실험: Stub은 초록, Fake·실제 구현은 빨강

계약: `findBalance`는 없는 계좌면 `NoSuchElementException`, `recentTransfers`는 최신 것이 먼저.\
서비스는 계약을 잘못 알고 있다(없으면 `-1`, 오래된 것이 먼저).

```java
// 잘못된 가정 두 개를 품은 서비스
public String balanceText(String id) {
    long b = repo.findBalance(id);
    if (b < 0) return "NOT_FOUND";              // 가정 (1): 없으면 -1
    return "balance=" + b;
}
public long lastTransferAmount(String id) {
    List<Transfer> ts = repo.recentTransfers(id, 10);
    if (ts.isEmpty()) return 0;
    return ts.get(ts.size() - 1).amount();      // 가정 (2): 오름차순
}
```

같은 시나리오 두 개를 더블 세 종류로 시험했다.

```java
// (가) Mockito Stub — 작성자의 믿음대로 답한다
when(repo.findBalance("nope")).thenReturn(-1L);
when(repo.recentTransfers("a", 10)).thenReturn(List.of(
    new Transfer("a", 100, 1), new Transfer("a", 300, 3)));

// (나) Fake — HashMap + 리스트로 계약대로 구현
public long findBalance(String id) {
    Long b = balances.get(id);
    if (b == null) throw new NoSuchElementException("account " + id);
    return b;
}
public List<Transfer> recentTransfers(String id, int limit) {
    return transfers.stream().filter(t -> t.accountId().equals(id))
        .sorted(Comparator.comparingLong(Transfer::createdAt).reversed())
        .limit(limit).toList();
}

// (다) 실제 구현 — H2 인메모리 DB, ... order by created_at desc limit ?

// 계약 테스트 — 같은 테스트를 (나)와 (다)에 돌린다
abstract class AccountRepositoryContract {
    abstract AccountRepository withData(String id, long balance, Transfer... ts) throws Exception;
    @Test void missingAccountThrows() throws Exception {
        AccountRepository r = withData("a", 10);
        assertThatThrownBy(() -> r.findBalance("nope")).isInstanceOf(NoSuchElementException.class);
    }
    @Test void recentTransfersNewestFirstAndLimited() throws Exception { /* 300, 200 순서 확인 */ }
}
```

(실험, maven:3.9-eclipse-temurin-21 이미지 — Maven 3.9.16 · JDK 21.0.11 · JUnit 5.13.4 · Mockito 5.24.0 · AssertJ 3.27.3 · H2 2.3.232, 2026-10-03)

```text
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.910 s -- in ex.JdbcRepositoryContractTest
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.209 s -- in ex.ServiceWithMockTest
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.061 s -- in ex.InMemoryRepositoryContractTest
[ERROR] Tests run: 2, Failures: 1, Errors: 1, Skipped: 0, Time elapsed: 0.221 s <<< FAILURE! -- in ex.ServiceWithH2Test
[ERROR] Tests run: 2, Failures: 1, Errors: 1, Skipped: 0, Time elapsed: 0.062 s <<< FAILURE! -- in ex.ServiceWithFakeTest
...
[ERROR] Failures: 
[ERROR]   ServiceWithFakeTest.lastTransfer:13 
expected: 300L
 but was: 100L
[ERROR]   ServiceWithH2Test.lastTransfer:19 
expected: 300L
 but was: 100L
[ERROR] Errors: 
[ERROR]   ServiceWithFakeTest.missingAccount:9 » NoSuchElement account nope
[ERROR]   ServiceWithH2Test.missingAccount:15 » NoSuchElement account nope
```

| 더블 | 계약 테스트 | 서비스 테스트(2개) |
|---|---|---|
| Mockito Stub | 해당 없음(구현이 없다) | 2개 초록 |
| Fake(HashMap) | 2개 통과 | 1 실패 + 1 오류 |
| 실제 구현(H2) | 2개 통과 | 1 실패 + 1 오류 |

- 관찰: Stub 테스트만 서비스의 잘못된 가정을 통과시켰다. Fake와 H2는 같은 지점에서 같은 방식으로 깨졌다.
- 해석: Fake가 실제 구현과 **같은 계약 테스트를 통과**했기 때문에, Fake로 돌린 서비스 테스트의 실패를 믿을 수 있다.
- 서비스를 계약대로 고치면(예외를 잡아 `NOT_FOUND`, `get(0)`) 11개 모두 통과했다. 이때 Stub 테스트도 계약에 맞게 다시 써야 했다(`thenThrow`, 최신 것이 먼저). **Stub의 답은 테스트마다 흩어진 계약 사본**이라 계약이 바뀌면 그 사본을 전부 찾아 고쳐야 한다.

```text
(실험, 같은 환경 — 서비스와 Stub을 계약대로 고친 뒤)
[INFO] Tests run: 11, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

### 5. Mockito의 기본 응답과 엄격한 stub

- stub하지 않은 메서드를 부르면 Mockito는 기본 응답(`RETURNS_DEFAULTS`)을 돌려준다. Mockito 5.24.0 소스 `ReturnsEmptyValues` 주석 기준.
  - 숫자형 원시 타입과 그 래퍼는 0(`boolean`은 `false`), 컬렉션은 빈 컬렉션, `Optional`은 `Optional.empty()`, `Stream`은 빈 스트림, 그 밖의 참조 타입은 `null`.
- 위험: **아무것도 stub하지 않아도 테스트가 그럴듯하게 돈다.**

```text
(실험, 같은 환경 — mock(Repo.class)에 아무것도 stub하지 않고 호출)
DEFAULTS count=0 boxed=0 name=null list=[] opt=Optional.empty obj=null
DEFAULTS balanceText(missing)=balance=0
```

- 둘째 줄: 없는 계좌인데 `balance=0`이 나왔다. `findBalance`가 원시 `long`이라 기본값 0이 왔고, 서비스는 이를 정상 잔액으로 다뤘다. 예외도 실패도 없다.
- 반대 방향의 안전장치: `MockitoExtension`의 기본 엄격도는 `STRICT_STUBS`다(mockito-junit-jupiter 5.24.0 — `MockitoExtension` 기본 생성자가 `Strictness.STRICT_STUBS`를 쓰고, `@MockitoSettings`의 `strictness()` 기본값도 `STRICT_STUBS`). 쓰이지 않은 stub이 있으면 테스트가 실패한다.
  - 범위: 이 검사는 `MockitoExtension`(JUnit 4는 `MockitoJUnitRunner`·`MockitoRule`, 또는 `MockitoSession`)을 쓸 때만 돈다(`Strictness` javadoc). 확장 없이 `Mockito.mock()`만 쓴 테스트는 같은 쓰이지 않은 stub이 있어도 통과했다(사실 점검 재실행, 같은 환경).

```text
(실험, 같은 환경 — findBalance를 stub했지만 SUT가 부르지 않음)
org.mockito.exceptions.misusing.UnnecessaryStubbingException: 

Unnecessary stubbings detected.
Clean & maintainable test code requires zero unnecessary code.
Following stubbings are unnecessary (click to navigate to relevant line of code):
  1. -> at ex.StrictStubsDemoTest.unusedStubbing(StrictStubsDemoTest.java:14)
Please remove unnecessary stubbings or use 'lenient' strictness. More info: javadoc for UnnecessaryStubbingException class.
```

- 이 오류는 "테스트가 SUT의 호출 경로를 잘못 알고 있다"는 신호다. `lenient()`로 덮기 전에 왜 안 불렸는지 먼저 본다.
- `spy(obj)`는 원본을 감싸지 않고 **복사본**을 만든다(Mockito 5.24.0 javadoc 13절: "Mockito *does not* delegate calls to the passed real instance, instead it actually creates a copy of it"). 그래서 spy를 만든 뒤 원본과 spy의 상태가 따로 간다.

```text
(실험, 같은 환경 — Counter real; spied = spy(real); real.inc(); spied.inc() 두 번)
after real.inc():  real=1 spied=0
after spied.inc()x2: real=1 spied=2
```

  - 주의: 복사는 필드 값을 옮기는 데 그친다. `ArrayList`처럼 내부 배열을 필드로 든 객체는 그 배열을 원본과 함께 쓸 수 있다. 같은 실험에서 `real=[a]`를 spy한 뒤 `real.add("b")`, `spied.add("c")`를 하자 둘 다 `[a, c]`를 출력했다(원본이 넣은 `b`를 spy가 덮었다). spy를 만든 뒤에는 원본을 건드리지 않는 편이 안전하다.

## 쓰이는 자료구조·알고리즘

- **Fake = 인메모리 자료구조로 다시 짠 구현**
  - 키 조회 저장소 → [해시맵](../../data-structure/05-hashmap/2-summary.md). 없는 키 처리(예외냐 `Optional`이냐)가 계약의 핵심이다.
  - 정렬·페이지 조회 → 리스트 + 정렬 + `limit`. 실제 DB의 `ORDER BY`·동순위 처리와 같아야 한다.
  - 큐·메시지 브로커 Fake → 리스트(FIFO). 실제 브로커의 재전달·순서 보장 차이는 Fake가 흉내 내지 못하는 경우가 많다.
- **Spy = 호출 기록 리스트**: 받은 인자를 `List`에 쌓고 테스트가 꺼내 본다. Mockito의 `verify`도 내부적으로 호출 기록을 대조한다.
- **계약 테스트 = 같은 테스트 묶음 × 여러 구현**: 추상 테스트 클래스(구현 생성만 하위 클래스가 결정)나 매개변수화 테스트로 만든다.

## 적용 — 풀어나가는 법

### 1. 더블을 고르는 순서

```text
   실제 구현이 빠르고 결정적인가? ── 예 ──▶ 실제 구현 (SWE@G "Prefer Realism Over Isolation")
          │ 아니오
   믿을 만한 Fake가 있나? ── 예 ──▶ Fake (계약 테스트를 통과한 것)
          │ 아니오
   SUT가 값을 받아 오기만 하나(간접 입력)? ── 예 ──▶ Stub
          │ 아니오(밖으로 상태를 바꾸는 호출)
   그 호출이 앱 밖에서 관찰되나(메일·외부 API·메시지)? ── 예 ──▶ Mock/Spy로 호출 검증
          │ 아니오(앱 전용 DB 등)
   실제 구현으로 통합 테스트 (Khorikov: 관리형 의존은 실제로)
```

- 이 순서는 SWE@G 13장과 Khorikov "When to Mock"의 권고를 합친 것이다. 저자들의 주장이지 측정 결과가 아니다.
- 실행 시간·결정성·생성 비용 때문에 실제 구현을 못 쓰는 경우가 있다(SWE@G 13장 "How to Decide When to Use a Real Implementation"의 세 기준).

### 2. 손으로 짠 Fake와 Spy

```java
// Spy: Stub처럼 답하고, 받은 호출을 기록한다
class RecordingMailer implements Mailer {
    final List<String> sent = new ArrayList<>();
    public void sendWelcome(String email) { sent.add(email); }
}

@Test void registeredUserGetsWelcomeMail() {
    var mailer = new RecordingMailer();
    new RegisterUser(new InMemoryUserRepository(), mailer).register("a@x.test");
    assertThat(mailer.sent).containsExactly("a@x.test");     // 기록을 꺼내 단언
}
```

- Mockito로 같은 것을 쓰면 `verify(mailer).sendWelcome("a@x.test")`이다. 이 `mailer`를 부르는 이름은 출처마다 다르다.
  - Mockito·Khorikov의 말로는 mock이다(나가는 호출을 검사한다).
  - Meszaros 분류로는 Test Spy에 가깝다. 기대를 미리 프로그램하지 않고, 실행 뒤에 테스트가 기록을 대조하기 때문이다(xunitpatterns.com "Test Spy"·"Mock Object" 요약 문장 비교).

### 3. Stub 단언 금지·과잉 명세 피하기

```java
// 나쁜 예: Stub(입력)에 대한 호출을 검증한다 — 구현 세부에 묶인다
when(repo.findBalance("a")).thenReturn(500L);
service.balanceText("a");
verify(repo).findBalance("a");          // Khorikov: stub과의 상호작용은 단언하지 않는다

// 나은 예: 결과만 본다
assertThat(service.balanceText("a")).isEqualTo("balance=500");
```

- SWE@G 13장 "Avoid overspecification": 검증하려는 동작과 무관한 호출까지 단언하면, 무관한 변경에도 테스트가 깨진다. 이 경우의 상세는 02·04번 노트 몫이다.

### 4. 진단 — 더블이 실제와 어긋났는지 찾기

```bash
# 테스트 코드에서 실제 구현이 하지 않는 답을 stub한 곳 찾기 (예: null·-1을 돌려주는 stub)
grep -rnE 'thenReturn\((null|-1L?)\)' src/test/java
# 한 인터페이스에 대한 stub 위치 수 — 계약 사본이 몇 군데 흩어져 있나
grep -rn 'when(repo\.' src/test/java | wc -l
```

- 점검 질문: 이 stub의 답을 **실제 구현이 실제로 낼 수 있나**? 없는 값, 실제와 다른 순서, 실제가 던지는 예외를 빼먹은 경우를 찾는다.
- 인터페이스마다 계약 테스트가 있으면, 새 Fake·새 구현이 생길 때 하위 클래스 하나로 같은 검증을 받는다.

## 장애 시나리오와 대처

### 1. 과도한 mock → 테스트는 초록인데 실제 통합에서 실패 (⚠ 커리큘럼)

- 현상: 서비스 단위 테스트 수백 개가 초록인데, 배포 직후 특정 경로에서 500.
- 보이는 형태: `NoSuchElementException`, `NullPointerException`, 잘못된 값으로 계산된 응답. 단위 테스트에는 이 경로를 실제 저장소와 붙여 본 테스트가 없다.
- 원인: 의존을 전부 Mockito stub으로 바꿔 **실제 구현이 한 번도 실행되지 않았다.** stub의 답은 테스트 작성자의 믿음이다.
- 대처
  - 관리형 의존(앱 전용 DB)은 실제 구현이나 계약 테스트를 통과한 Fake로 시험한다. 실제 DB 통합 테스트는 08번 노트.
  - 서비스 테스트 중 핵심 시나리오 몇 개는 실제 조립으로 한 번 더 돌린다(06번 노트의 인수 테스트).

### 2. mock이 실제와 다른 계약을 흉내 냄 (⚠ 커리큘럼)

- 현상: 위 실험 그대로. 없는 계좌에 `-1`, 최신 순 대신 오래된 순을 stub했다.
- 보이는 형태: Stub 테스트 초록, Fake·H2 테스트는 `expected: 300L but was: 100L`와 `NoSuchElementException`.
- 원인: 인터페이스의 계약(없을 때·정렬·예외·`null` 허용 여부)이 문서나 테스트로 고정되지 않았다. 각 테스트가 계약을 제멋대로 다시 적었다.
- 대처
  - 계약을 인터페이스 주석과 **계약 테스트**로 고정한다. Fake와 실제 구현이 같은 계약 테스트를 통과하게 한다.
  - stub 대신 그 Fake를 쓴다. 실험에서 Fake는 실제 구현과 같은 지점에서 깨졌다.
  - 반환 타입으로 "없음"을 드러낸다(`Optional`). 그러면 Mockito 기본 응답도 `Optional.empty()`가 되어, 원시 `long` 기본값 0이 정상 잔액처럼 보이던 문제가 줄어든다.

### 3. Fake가 실제 구현을 따라가지 못함(fake drift)

- 현상: 실제 저장소에 "삭제된 계좌는 조회 안 됨" 규칙을 넣었는데 Fake는 그대로라, Fake 기반 테스트가 옛 동작을 계속 통과시킨다.
- 보이는 형태: 운영에서만 삭제된 계좌가 조회된다는 버그 보고. Fake 기반 테스트는 초록.
- 원인: Fake를 실제 구현과 다른 팀·다른 시점에 고쳤다. 계약 테스트가 없거나 실제 구현 쪽만 돌렸다.
- 대처: 계약 테스트를 실제 구현과 Fake **양쪽에** CI에서 돌린다. SWE@G 13장은 실제 구현을 가진 팀이 Fake도 만들고 유지하라고 권한다.

### 4. stub이 쓰이지 않음 → `UnnecessaryStubbingException`

- 현상: 리팩터링 뒤 테스트 여러 개가 `UnnecessaryStubbingException`으로 실패한다.
- 보이는 형태: 위 실험의 메시지. 실패 위치는 `when(...)` 줄이다.
- 원인: SUT의 호출 경로가 바뀌어 일부 stub이 더 이상 불리지 않는다. 또는 처음부터 테스트가 호출 경로를 잘못 알았다.
- 대처: 불필요한 stub을 지운다. 여러 테스트가 공유하는 `@BeforeEach` stub 때문이면 그 stub을 필요한 테스트로 옮긴다. `lenient()`는 이유를 확인한 뒤에만 쓴다.

### 5. 내 것이 아닌 타입을 mock함

- 현상: `JdbcTemplate`·HTTP 클라이언트 같은 라이브러리 타입을 직접 stub했다. 라이브러리를 올렸더니 운영에서 동작이 달라졌는데 테스트는 그대로 초록.
- 원인: 라이브러리의 실제 동작(예외 종류·빈 결과 처리)을 테스트 작성자가 추측해 stub했다.
- 대처: GOOS 8장 "Only Mock Types That You Own" — 라이브러리 위에 내 인터페이스(어댑터)를 두고 그 인터페이스를 더블로 바꾼다. 어댑터 자체는 실제 라이브러리와 붙여 통합 테스트한다.

## 핵심 문장

- 테스트 더블은 SUT가 기대는 부품(DOC)을 대신한다. Stub은 간접 입력을 조종하고, Spy·Mock은 간접 출력을 확인한다.
- Fake는 동작하는 가벼운 구현이고, 흔히 해시맵·리스트 같은 인메모리 자료구조로 짠다.
- "mock"의 뜻은 출처마다 다르다. Meszaros·Fowler는 다섯 분류, Khorikov는 mock(나가는 호출)·stub(들어오는 입력) 둘, Mockito의 `mock()`은 둘 다 한다.
- Stub의 답은 실제 구현을 실행하지 않은 **믿음**이다. 실험에서 Stub 테스트는 초록, 계약을 지킨 Fake와 H2 구현은 같은 지점에서 빨강이었다.
- Fake는 실제 구현과 같은 계약 테스트를 통과할 때만 믿을 수 있다.
- Mockito는 stub하지 않은 호출에 0·빈 컬렉션·`null`을 돌려주므로, 아무것도 stub하지 않은 테스트도 그럴듯하게 돈다.

## 관련 주제·근거

- 선행
  - [02-good-unit-tests](../02-good-unit-tests/2-summary.md) — 회귀 방지·리팩터링 내성, 구현 세부 검증의 비용
- 후속·연결
  - [04-classical-vs-london](../04-classical-vs-london/2-summary.md) — 상태 검증 vs 상호작용 검증, 학파별 더블 사용
  - [06-outside-in-tdd-and-acceptance-tests](../06-outside-in-tdd-and-acceptance-tests/2-summary.md) — 협력 객체를 발견하려고 mock을 쓰는 이중 루프 TDD
  - [08-integration-tests-real-dependencies](../08-integration-tests-real-dependencies/2-summary.md) — 실제 DB·브로커로 시험하기
  - [11-test-data-and-fixtures](../11-test-data-and-fixtures/2-summary.md) — 픽스처와 테스트 데이터
  - [13-contract-testing](../13-contract-testing/2-summary.md) — 서비스 간 소비자 주도 계약
  - software-design [25-dependency-injection-and-composition-root](../../software-design/25-dependency-injection-and-composition-root/2-summary.md) — 더블을 끼울 이음새(생성자 주입), 숨은 입력
  - software-design [23-design-by-contract](../../software-design/23-design-by-contract/2-summary.md) — 계약(사전·사후 조건)
  - domain-modeling [10-repositories-and-factories](../../domain-modeling/10-repositories-and-factories/2-summary.md) — 저장소 인터페이스
  - data-structure [05-hashmap](../../data-structure/05-hashmap/2-summary.md) — Fake 저장소의 자료구조
- 문헌
  - Meszaros, 『xUnit Test Patterns』(2007) · xunitpatterns.com "Test Double"(책 522쪽), "Test Stub"(529쪽), "Test Spy"(538쪽), "Mock Object"(544쪽), "Fake Object"(551쪽), "Dummy Object"(728쪽) <http://xunitpatterns.com/Test%20Double.html>
  - Fowler, "Mocks Aren't Stubs"(2004-07-08, 2007-01-02 개정) — 다섯 더블 정의, 상태 검증 vs 행위 검증, 고전파 vs mockist <https://martinfowler.com/articles/mocksArentStubs.html>
  - Winters·Manshreck·Wright, 『Software Engineering at Google』 13장 "Test Doubles" — Seams, Prefer Realism Over Isolation, The Fidelity of Fakes, Fakes Should Be Tested(계약 테스트), The Dangers of Overusing Stubbing, Prefer State Testing Over Interaction Testing, Avoid overspecification <https://abseil.io/resources/swe-book/html/ch13.html>
  - Khorikov, 『Unit Testing: Principles, Practices, and Patterns』(Manning 2020) 5장 "Mocks and test fragility", 9장 "Mocking best practices" · "When to Mock"(2020-04-15) <https://enterprisecraftsmanship.com/posts/when-to-mock/>
  - Freeman·Pryce, 『Growing Object-Oriented Software, Guided by Tests』(2009) 8장 "Building on Third-Party Code" — Only Mock Types That You Own <https://growing-object-oriented-software.com/toc.html>
- 제품 문서·소스
  - Mockito 5.24.0 소스 — `org.mockito.internal.stubbing.defaultanswers.ReturnsEmptyValues`(기본 응답), `org.mockito.Mockito` javadoc 13절 "Spying on real objects", `org.mockito.quality.Strictness`
  - mockito-junit-jupiter 5.24.0 — `MockitoSettings.strictness()` 기본 `STRICT_STUBS`, `MockitoExtension`
- 실험 목록(코드는 scratchpad `ts/03/doubles`, 고친 판은 `ts/03/doubles-fixed`)
  - `maven:3.9-eclipse-temurin-21` 이미지(Maven 3.9.16, JDK 21.0.11), `--cpus=2 -m 1g`, JUnit 5.13.4 · Mockito 5.24.0 · AssertJ 3.27.3 · H2 2.3.232
  - A: 같은 서비스 시나리오 2개를 Mockito Stub·Fake·H2 구현으로 — Stub 2 초록, Fake·H2 각 1 실패 + 1 오류, 계약 테스트는 Fake·H2 모두 통과
  - B: 서비스와 Stub을 계약대로 고친 뒤 11개 전부 통과
  - C: stub 없는 mock의 기본 응답 출력, `UnnecessaryStubbingException` 메시지
  - D(사실 점검 재실행): 같은 쓰이지 않은 stub을 확장 없이 `Mockito.mock()`으로 만들면 통과, `MockitoExtension`이면 `UnnecessaryStubbingException`. stub 없는 `boolean` 메서드는 `false`
  - E(2차 리뷰 판정 재현, scratchpad `ts/adj-03/spy`): `spy()` 뒤 원본·spy 상태 분리 — `Counter`는 real=1·spied=2로 갈라짐, `ArrayList`는 내부 배열을 같이 써 둘 다 `[a, c]`
