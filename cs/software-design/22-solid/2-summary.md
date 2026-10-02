# software-design/22-solid — SRP·OCP·LSP·ISP·DIP — 정리 (힌트)

## 해결하는 문제

요구는 바뀐다. 바뀔 때 **고칠 곳이 몇 곳이고, 그 변경이 어디까지 번지나**가 설계의 비용이다. SOLID는 그 번짐을 줄이는 다섯 가지 관점이다.

```text
 변경 요청 하나 ──> 고쳐야 할 곳
 ┌────────────────────────────────────────────────────────────────┐
 │ SRP  서로 다른 사람의 요구가 한 클래스에 섞였나?   → 한 요구가 남의 기능을 깨뜨린다 │
 │ OCP  새 종류를 추가할 때 기존 파일을 여나?        → switch N곳 수정·누락          │
 │ LSP  하위 타입을 넣으면 상위 타입 호출자가 깨지나? → 런타임 예외·instanceof 분기   │
 │ ISP  안 쓰는 메서드에 묶였나?                    → 무관한 변경에 재컴파일·가짜 구현 │
 │ DIP  정책이 세부(DB·SMTP)를 직접 아나?            → 세부 교체·테스트가 정책을 흔든다 │
 └────────────────────────────────────────────────────────────────┘
```

쉬운 예: 멀티탭이다. 플러그 모양(인터페이스)만 맞으면 어떤 기기든 꽂힌다(OCP·DIP). 전기를 주겠다고 해 놓고 가끔 안 주는 멀티탭은 못 쓴다(LSP).\
똑같은 구조다.\
실무 예: 결제 수단 추가(OCP), 정산 완료 거래의 취소(LSP), 메일 발송 서비스 단위 테스트(DIP).

다섯 원칙의 정의·나쁜 예·좋은 예·위반 신호·원칙 간 충돌은 원본 [engineering/solid-principles](../../engineering/solid-principles/2-summary.md)에 길게 있다.\
이 노트는 **원칙마다 출처별 정의를 구분하고**, 원칙이 줄여 준다는 비용과 **반대로 늘리는 비용**을 실험으로 재고, 장애 시나리오와 진단을 채운다.

## 동작·원리

### 0. 출처별 정의 — 저자 주장으로 읽는다

| 원칙 | 원 출처 | Martin의 정리 |
|---|---|---|
| SRP | Parnas 1972(바뀔 결정으로 모듈을 나눔)를 Martin이 근거로 든다 | 2014 블로그: "each software module should have one and only one reason to change", 그리고 "the reasons for change are people". 『Clean Architecture』(2017) 7장 — 절: "Symptom 1: Accidental Duplication", "Symptom 2: Merges" |
| OCP | Meyer 『Object-Oriented Software Construction』 1판(1988): 모듈은 "both open and closed" | 2014 블로그: "You should be able to extend the behavior of a system without having to modify that system." 8장 |
| LSP | Liskov 1987 OOPSLA 기조연설 "Data Abstraction and Hierarchy"의 치환 성질, Liskov·Wing 1994 "A behavioral notion of subtyping" | 9장 — 절: "The Square/Rectangle Problem", "LSP and Architecture" |
| ISP | — | 10장 — 절: "ISP and Language", "ISP and Architecture" |
| DIP | — | 11장 — 절: "Stable Abstractions", "Factories", "Concrete Components" |

- Martin 블로그 문장은 직접 열어 확인했다. 『Clean Architecture』는 출판사 목차(장·절 제목)만 확인했고 본문 문장은 열지 못했다.
- 원본 노트의 "하나의 모듈은 오직 하나의 액터에 대해서만 책임져야 한다"는 『Clean Architecture』 7장 정의로 널리 인용되지만, 이 작업에서 본문 대조는 못 했다 [?]. 같은 생각(변경 이유 = 사람·그룹)은 2014 블로그에서 확인된다.
- Liskov 1987의 치환 성질(원문): "If for each object o1 of type S there is an object o2 of type T such that for all programs P defined in terms of T, the behavior of P is unchanged when o1 is substituted for o2, then S is a subtype of T."
  - *행동적 하위 타입(behavioral subtyping)*: 시그니처가 맞는 것으로는 부족하고, 상위 타입의 명세(사전·사후조건·불변식)를 하위 타입이 지켜야 하위 타입이라는 관점. 계약 규칙은 [23-design-by-contract](../23-design-by-contract/2-summary.md).

### 1. SRP — 변경을 요구하는 사람이 기준

```text
 Employee                         CFO 요구: 초과근무 계산 변경
  calculatePay() ──┐                         │
                   ├──> regularHours()  <────┘ 고침
  reportHours()  ──┘        │
                            └──> COO의 근무시간 보고가 조용히 바뀜 (Accidental Duplication)
```

- 기초 예제(Employee·Payment)는 원본 「S」. 원본이 다루지 않은 신호: 7장 절 제목의 두 번째 증상 **Merges** — 서로 다른 팀이 같은 파일을 동시에 고쳐 병합 충돌이 잦다. `git log`로 잰다(아래 적용).

### 2. OCP — 어느 축으로 닫혀 있나

```text
              새 "종류" 추가 (결제수단)        새 "연산" 추가 (환불 수수료)
 switch 설계   기존 파일 N곳 수정 (+누락 위험)    새 파일 1개
 다형 설계     새 파일 1개 + 등록 1줄             인터페이스 + 구현 전부 수정
```

- OCP는 "모든 변경에 닫힘"이 아니다. **한 축에 닫으면 다른 축에는 열린다.** 이 맞교환을 표현 문제(expression problem)라고도 부른다.

### 실험 B: 같은 두 변경을 switch 설계와 다형 설계에 적용

설계: 결제수단(CARD·BANK)별 수수료·한도·라벨. switch 설계는 `Fee`·`Limit`·`Label` 세 파일에 `switch` 문(default 있음), 다형 설계는 `PaymentMethod` 인터페이스 + 구현 클래스 + 등록 목록.

(실험, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/20/e22/b/` git 저장소, 2026-10-02 — 변경1은 EASY_PAY 추가, 실행 출력은 EASY_PAY 줄만 발췌)

```text
== 변경1 switch 쪽
 sw/Fee.java         | 1 +
 sw/Limit.java       | 1 +
 sw/PaymentType.java | 2 +-
 3 files changed, 3 insertions(+), 1 deletion(-)
== 변경1 poly 쪽
 poly/EasyPay.java | 6 ++++++
 poly/Main.java    | 2 +-
 2 files changed, 7 insertions(+), 1 deletion(-)
[switch] EASY_PAY fee(100000)=1500 limit=2000000 label=기타
[poly]   EASY_PAY fee(100000)=1500 limit=2000000 label=간편결제
```

- switch 쪽은 `Label.java`를 **의도적으로 빠뜨려** 재현했다. 컴파일·실행 모두 통과했고 라벨만 `default` 분기의 "기타"가 됐다. 기존 파일 3개를 열었다.
- 다형 쪽은 새 파일 1개와 등록 1줄. 라벨을 빠뜨리면 `EasyPay`가 인터페이스를 다 구현하지 않아 컴파일이 안 된다.

변경2는 `refundFee` 연산 추가:

```text
== 변경2 switch 쪽
 sw/RefundFee.java | 9 +++++++++
 1 file changed, 9 insertions(+)
== 변경2 poly 쪽
 poly/Bank.java          | 1 +
 poly/Card.java          | 1 +
 poly/EasyPay.java       | 1 +
 poly/PaymentMethod.java | 1 +
 4 files changed, 4 insertions(+)
```

- 새 연산은 switch 쪽이 새 파일 하나로 끝났고, 다형 쪽은 인터페이스와 구현 3개를 모두 열었다. **다형 설계가 손해인 변경**이다.
- 같은 저장소에서 enum에 `POINT`를 하나 더 넣고 컴파일하면:

```text
RefundFee.java:3: error: the switch expression does not cover all possible input values
        return switch (t) {               // switch 식: default 없이 enum 전부를 다뤄야 컴파일된다
               ^
1 error
```

- default 없는 switch **식**(JDK 14+)은 누락을 컴파일 오류로 잡았다. default 있는 switch **문**(`Fee`·`Limit`·`Label`)은 오류 없이 컴파일됐다. switch를 쓸 거라면 default 없는 switch 식으로 누락을 컴파일러에 맡길 수 있다(조건 분기 도구 선택은 28).

### 3. LSP — 컴파일은 되는데 약속이 깨진다

상위 타입만 아는 호출자에게 하위 타입을 넣어 본다. 기초 예제(정사각형·펭귄·정산 완료 거래)와 계약 규칙 네 가지는 원본 「L」에 있다.

### 실험 A: Square와 JDK 컬렉션

```java
static String resize(Rectangle r) {                 // Rectangle의 약속만 믿은 호출자
    r.setWidth(5); r.setHeight(4);
    return r.getClass().getSimpleName() + " area=" + r.area() + (r.area() == 20 ? " (기대대로)" : " (기대 20과 다름)");
}
static String appendAudit(List<String> l) {          // List의 약속만 믿은 호출자
    try { l.add("audit"); return "add OK size=" + l.size(); }
    catch (UnsupportedOperationException e) { return "add -> UnsupportedOperationException"; }
}
```

(실험, JDK 21.0.12, `scratchpad/sd/20/e22/a/Lsp.java`, 2026-10-02)

```text
Rectangle area=20 (기대대로)
Square area=16 (기대 20과 다름)
ArrayList                 : add OK size=2
List.of                   : add -> UnsupportedOperationException
Arrays.asList             : add -> UnsupportedOperationException
Collections.unmodifiable  : add -> UnsupportedOperationException
Arrays.asList set(0,z)    : [z, y]
```

- 넷 다 `List` 타입이라 컴파일러는 차이를 모른다. 호출자는 실행해 봐야 안다.
- JDK는 이것을 **계약에 적어 둔 선택**으로 처리한다. `Collection` javadoc(JDK 21 소스): "Certain methods are specified to be *optional*. If a collection implementation doesn't implement a particular operation, it should define the corresponding method to throw `UnsupportedOperationException`." `List.add`도 "(optional operation)"이다.
- 해석: 상위 타입의 계약이 "던질 수도 있다"를 허용하면 그 하위 타입은 계약 위반이 아니다. 대신 호출자가 타입만 보고 `add`가 되는지 알 수 없다 — 약속이 약해진 만큼 호출자가 부담을 진다. 우리 도메인 타입(`Transaction.cancel()`)에는 이 방식보다 능력별 타입 분리(원본 「L」의 `Cancellable`)가 낫다는 것이 원본의 주장이다.

### 4. ISP — 클라이언트 기준으로 자른다

- 원본 「I」(복합기·`UserRepository` 8메서드 → `UserReader`/`UserWriter`/`UserSearcher`) 참고.
- 비용 쪽 측정: 다형 설계 변경2에서 인터페이스에 메서드가 하나 늘자 구현 3개가 함께 열렸다. 인터페이스가 클수록 이 전파가 커진다. 클라이언트별로 좁힌 인터페이스는 이 전파 범위를 그 클라이언트로 줄인다.

### 5. DIP — 소스 의존 방향을 정책 쪽으로

```text
 DIP 없음                                  DIP
 SignupService ──new──> SmtpMailer         SignupService ──> WelcomeSender (정책 쪽 패키지가 소유)
   (정책)                (세부: 소켓)          (정책)               ▲ implements
                                                              SmtpSender (세부)   FakeSender (테스트)
 호출 흐름 = 소스 의존 방향                  호출 흐름: 정책 → 세부 / 소스 의존: 세부 → 정책 (역전)
```

### 실험 C: 같은 테스트("가입하면 환영 메일 1통")를 두 설계에

```java
static class SignupServiceV1 {                       // DIP 없음
    private final SmtpMailer mailer = new SmtpMailer();  // 127.0.0.1:2525로 소켓 연결
    String signup(String email) throws IOException { mailer.send(email, "환영합니다"); return "OK"; }
}
interface WelcomeSender { void send(String to, String body) throws IOException; }
static class SignupServiceV2 {                       // DIP
    private final WelcomeSender sender;
    SignupServiceV2(WelcomeSender sender) { this.sender = sender; }
    String signup(String email) throws IOException { sender.send(email, "환영합니다"); return "OK"; }
}
// 테스트: List<String> sent = new ArrayList<>(); WelcomeSender fake = (to, body) -> sent.add(to);
```

(실험, JDK 21.0.12, `--network none` 컨테이너, `scratchpad/sd/20/e22/c/Dip.java`, 2026-10-02)

```text
[V1] 테스트 실패: ConnectException: Connection refused
[V2] OK sent=[a@example.com]
```

- V1은 메일 서버가 없으면 테스트 자체가 돌지 않는다. 검증하려면 SMTP 서버를 띄우거나 바이트코드 조작형 목 도구가 필요하다.
- V2는 가짜 구현이 람다 한 줄이다. 정책(가입 규칙)을 세부(SMTP) 없이 검증한다.
- 비용: 인터페이스 1개와 생성자 주입이 늘었다. 경계를 넘지 않는 내부 협력 객체에까지 이렇게 하면 간접 계층만 늘어난다(원본 「원칙 간의 관계와 충돌」의 DIP ↔ 생산성).

## 쓰이는 자료구조·알고리즘

- **의존 그래프(방향 그래프)**: 노드 = 모듈·클래스, 간선 = "A가 B를 import한다". DIP는 경계를 넘는 간선의 방향을 정책 쪽으로 돌리는 것이고, 순환이 생기면 강연결요소(SCC)로 찾는다. 계층 위반 검사는 이 그래프에 대한 규칙 검사다(ArchUnit).
- **디스패치 테이블**: OCP의 다형 설계에서 `List<PaymentMethod>`나 `Map<Code, PaymentMethod>`가 switch를 대신한다 — 조회는 해시 맵 O(1)(평균), 목록 탐색은 O(n).
- **부분 순서(타입 계층)**: 하위 타입 관계는 반사·추이적이다. LSP는 이 순서가 **행동**에 대해서도 성립해야 한다는 요구다.
- **변경 결합 행렬**: `git log`로 "같은 커밋에 함께 바뀐 파일 쌍"을 세면 SRP·OCP 위반 후보(함께 바뀌는데 흩어진 것, 따로 바뀌는데 묶인 것)가 보인다.

## 적용 — 풀어나가는 법

1. **변경 이력에서 축을 찾는다.** 원칙을 미리 다 적용하지 않는다. 실제로 반복된 변경 종류(새 결제수단? 새 연산?)를 보고 그 축에만 닫는다(원본 「OCP — 대가」의 "두 번째 케이스가 생겼을 때").
2. **새 종류가 반복되면 다형/테이블, 새 연산이 반복되면 switch 식**(실험 B). 둘 다 반복되면 어느 쪽 비용이 큰지 이력으로 비교한다.
3. **LSP는 호출자 테스트로 확인한다.** 상위 타입에 대한 계약 테스트를 하위 타입마다 돌린다.
4. **경계를 넘는 의존(DB·외부 API·메일·시계)에만 DIP.** 포트 인터페이스는 정책 쪽 패키지에 두고, 시그니처에 인프라 타입을 넣지 않는다.
5. **규칙을 기계로 지킨다**(ArchUnit 1.x).

```java
// LSP 계약 테스트: 상위 타입의 약속을 하위 타입마다 같은 테스트로 (JUnit 5)
abstract class RectangleContract {
    abstract Rectangle create();
    @Test void widthAndHeightAreIndependent() {
        Rectangle r = create();
        r.setWidth(5); r.setHeight(4);
        assertEquals(20, r.area());            // Square용 하위 테스트 클래스에서 실패한다
    }
}
// DIP 규칙: 도메인·애플리케이션은 인프라를 모른다 (ArchUnit 1.x, 사용자 가이드의 규칙 API)
noClasses().that().resideInAPackage("..application..")
    .should().dependOnClassesThat().resideInAPackage("..infrastructure..");
```

진단 — 변경 이력으로 SRP(Merges)·OCP(Shotgun) 후보 찾기:

```bash
# 커밋 수 상위 파일 = 여러 이유로 자주 바뀌는 후보
git log --since=6.months --name-only --format= -- src/main/java | sort | uniq -c | sort -rn | head
# 같은 switch 대상이 흩어진 곳 (새 종류 추가 때 N곳 수정 후보)
grep -rn 'case CARD' src/main/java | cut -d: -f1 | sort -u
```

## 장애 시나리오와 대처

### 1. LSP 위반 → 하위 타입에서 `UnsupportedOperationException`

- 현상: 정산 완료 거래를 취소 배치가 집어 `cancel()`을 부르자 배치가 중단된다. 또는 `List.of(...)`로 만든 목록을 받은 공통 함수가 `add`에서 터진다.
- 보이는 형태: 실험 A의 출력. `List.of("x").add("y")`의 스택 트레이스(JDK 21.0.12, `scratchpad/sd/20/e22/a/Uoe.java`):

```text
Exception in thread "main" java.lang.UnsupportedOperationException
	at java.base/java.util.ImmutableCollections.uoe(ImmutableCollections.java:142)
	at java.base/java.util.ImmutableCollections$AbstractImmutableCollection.add(ImmutableCollections.java:147)
```

- 원인: 상위 타입이 약속한 연산을 하위 타입이 못 한다. 컴파일러는 시그니처만 본다.
- 대처: 능력을 타입으로 나눈다(`Cancellable`). 컬렉션은 수정할 쪽이 자기 사본(`new ArrayList<>(input)`)을 만든다. 상위 타입 계약 테스트를 하위 타입마다 돌린다.

### 2. DIP 부재 → 테스트 불가

- 현상: 서비스 단위 테스트가 CI에서만 실패하거나, 테스트를 아예 못 쓴다.
- 보이는 형태: `ConnectException: Connection refused`(실험 C), 외부 서버 타임아웃, 테스트에 실제 DB·SMTP 기동 스크립트가 붙는다.
- 원인: 정책 클래스가 세부 구현을 `new`로 직접 만들었다. 시계(`LocalDate.now()`)·난수도 같은 숨은 의존이다.
- 대처: 정책 쪽에 포트 인터페이스를 두고 생성자로 주입받는다. 조립은 한 곳에서([25-dependency-injection-and-composition-root](../25-dependency-injection-and-composition-root/2-summary.md)).

### 3. OCP 부재 → 새 종류 추가 때 한 곳 누락, default로 조용히 처리

- 현상: 새 결제수단의 영수증 라벨이 "기타"로 나간다. 수수료는 맞다.
- 보이는 형태: 실험 B의 `label=기타`. 에러 없음. CS 문의로 발견.
- 원인: 같은 `switch(type)`이 여러 파일에 있고, default 분기가 누락을 삼켰다.
- 대처: 반복되는 축이면 다형/테이블로 한 곳에 모은다. switch를 유지하면 default 없는 switch 식으로 바꿔 누락을 컴파일 오류로 만든다.

### 4. SRP 위반 → 한 팀의 수정이 다른 팀 기능을 깨고, 병합 충돌이 잦다

- 현상: 급여 계산을 고친 배포 뒤 근무시간 리포트 수치가 바뀌었다. 같은 파일에 대한 PR 충돌이 반복된다.
- 보이는 형태: 리포트 회귀 버그, `git log` 상위에 같은 파일이 여러 팀 커밋으로 올라온다.
- 원인: 서로 다른 액터가 요구하는 코드가 공유 헬퍼(`regularHours`)를 통해 한 클래스에 묶였다(Accidental Duplication·Merges).
- 대처: 액터별로 클래스를 나누고, 우연히 같았던 헬퍼는 복제해서라도 분리한다. 진짜 같은 규칙이면 공유를 유지하되 소유자를 정한다.

### 5. 원칙 과적용 → 간접 계층만 늘고 한 연산 추가에 파일 N개

- 현상: 메서드 하나 추가에 인터페이스·구현·팩토리·설정을 모두 연다. 새 사람이 흐름을 못 따라간다.
- 보이는 형태: 실험 B 변경2의 다형 쪽(4파일). 구현이 하나뿐인 인터페이스가 많다.
- 원인: 실제로 늘지 않는 축에 확장점을 미리 열었다(추측성 일반화).
- 대처: 구현이 하나뿐이고 경계도 아닌 인터페이스는 걷어 낸다(Inline). 확장점은 두 번째 사례가 생길 때 연다.

참고: 원본 「L — 좋은 instanceof와 나쁜 instanceof」 표의 "빠트리면 → 컴파일 시점에 드러난다"(좋은 instanceof 쪽)는 조건이 붙는다. `if (tx instanceof Cancellable c)`는 새 거래 타입이 `Cancellable`을 구현하지 않으면 **컴파일 오류 없이** 취소를 건너뛴다. 컴파일 시점에 잡히는 것은 원본 「instanceof를 아예 없애는 방법」처럼 메서드가 `Cancellable`을 매개변수 타입으로 받을 때다.

## 핵심 문장

- SOLID는 "변경이 어디까지 번지나"를 다섯 방향에서 보는 관점이다. 정의는 출처마다 다르다(SRP: Martin 2014 "reasons for change are people", OCP: Meyer 1988, LSP: Liskov 1987·Liskov–Wing 1994).
- OCP는 한 축에 닫으면 다른 축에 열린다. 새 종류 추가는 다형 설계가 싸고(새 파일 1), 새 연산 추가는 switch가 쌌다(새 파일 1 vs 4파일 수정).
- LSP 위반은 컴파일을 통과하고 실행에서 드러난다(`Square` 넓이 16, `List.of().add` → UOE). 상위 타입 계약 테스트로 잡는다.
- DIP는 소스 의존 방향을 정책 쪽으로 돌려, 세부 없이 정책을 테스트할 수 있게 한다(V1 `ConnectException` vs V2 람다 한 줄). 경계를 넘는 의존에만 적용한다.

## 관련 주제·근거

- 선행
  - [20-oop-fundamentals](../20-oop-fundamentals/2-summary.md) — 다형성·IS-A
- 원본
  - [engineering/solid-principles](../../engineering/solid-principles/2-summary.md) — 원칙별 정의·나쁜 예·좋은 예·위반 신호·현장 상황, 원칙 간 관계와 충돌
- 후속·연결
  - [21-composition-over-inheritance](../21-composition-over-inheritance/2-summary.md) — 상속 비용(LSP와 함께 상속 판단)
  - [23-design-by-contract](../23-design-by-contract/2-summary.md) — LSP의 계약 규칙(사전조건 강화 금지·사후조건 약화 금지)
  - [25-dependency-injection-and-composition-root](../25-dependency-injection-and-composition-root/2-summary.md) — DI는 DIP의 구현 수단
  - [04-decompose-by-change](../04-decompose-by-change/2-summary.md) — 변경 축으로 나누기(SRP·OCP의 근거)
  - [28-taming-conditionals](../28-taming-conditionals/2-summary.md) — switch·테이블·다형성 중 무엇을 고르나
- 글·문서
  - Robert C. Martin, "The Single Responsibility Principle", 2014-05-08 <https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html>
  - Robert C. Martin, "The Open Closed Principle", 2014-05-12 (Meyer 1988 인용) <https://blog.cleancoder.com/uncle-bob/2014/05/12/TheOpenClosedPrinciple.html>
  - Robert C. Martin, 『Clean Architecture』(Pearson, 2017) 3부 7~11장 — 출판사 목차 <https://www.informit.com/store/clean-architecture-a-craftsmans-guide-to-software-structure-9780134494166>
  - Barbara Liskov, "Data Abstraction and Hierarchy", OOPSLA '87 기조연설(SIGPLAN Notices 23(5)). doi:10.1145/62139.62141 · 원문 PDF <https://www.cs.tufts.edu/~nr/cs257/archive/barbara-liskov/data-abstraction-and-hierarchy.pdf>
  - B. Liskov, J. Wing, "A behavioral notion of subtyping", ACM TOPLAS 16(6):1811–1841, 1994. doi:10.1145/197320.197383
  - Bertrand Meyer, 『Object-Oriented Software Construction』 1판(Prentice Hall, 1988) — Martin 블로그의 인용으로만 확인
  - OpenJDK jdk21u `java/util/Collection.java`(optional operations), `List.java` <https://github.com/openjdk/jdk21u>
  - ArchUnit User Guide(1.5.1) — `noClasses().that().resideInAPackage(..).should().dependOnClassesThat().resideInAPackage(..)` <https://www.archunit.org/userguide/html/000_Index.html>
- 실험 목록 (JDK 21.0.12 temurin 컨테이너 `--cpus=2 --network none`, 2026-10-02)
  - A `scratchpad/sd/20/e22/a/Lsp.java` — Square 넓이, JDK 불변 리스트의 `add`
  - B `scratchpad/sd/20/e22/b/` git 저장소 — 새 종류·새 연산 두 변경의 `git diff --stat`, default 누락, switch 식 망라성 오류
  - C `scratchpad/sd/20/e22/c/Dip.java` — DIP 없음/있음의 테스트 실행 결과
