# software-design/05-connascence — 커너선스: 결합을 종류·강도·지역성·정도로 재기 — 정리 (힌트)

## 해결하는 문제

02의 결합도 단계(내용 → 자료)는 "얼마나 나쁜가"를 큰 칸으로만 나눈다.\
리뷰에서 "이거 결합이 강해요"라고 말해도 **무엇을 어떻게 고치라는지** 전해지지 않는다.\
커너선스는 "함께 바뀌어야 하는 이유"에 이름을 붙여, 고칠 방향(더 약한 종류로)까지 말하게 해 준다.

```text
 리뷰 코멘트 비교
 "결합이 강합니다"                    → 무엇을? 어떻게?
 "from/to 위치 커너선스예요.          → 타입이나 이름으로 바꾸면
  모듈 경계를 넘으니 타입으로 바꾸죠"    컴파일러가 순서 실수를 잡는다
```

- *커너선스(connascence)*: 두 요소 중 하나를 바꿨을 때 시스템이 올바르게 동작하려면 다른 하나도 바꿔야 하는 관계. 말 뜻은 "함께 태어남". Meilir Page-Jones가 컴퓨터 과학 맥락에서 처음 썼다(connascence.io About — CACM 35(9), 1992, "Comparing techniques by means of encapsulation and connascence").
- connascence.io의 설명: 결합의 **분류 체계이자 품질 지표**이고, 각 사례를 강도·정도·지역성 세 축으로 본다.

쉬운 예: 친구와 "3번 출구에서 만나자"고 정했다. 역이 출구 번호를 바꾸면 둘 다 약속을 고쳐야 한다(의미 커너선스). "서점 앞에서"로 정하면 번호가 바뀌어도 상관없다(이름 커너선스).\
똑같은 구조다.\
실무 예: 주문 상태 `3`이 "배송"이라는 뜻을 주문 서비스와 알림 서비스가 각자 안다. 포장 단계를 끼워 번호를 밀면, 알림이 엉뚱한 주문에 "배송 시작"을 보낸다(아래 실험).

## 동작·원리

### 1. 종류 — 정적 다섯, 동적 넷

```text
 정적 (소스만 보고 알 수 있다)                 동적 (실행해 봐야 안다)
 이름 Name       같은 이름에 합의               실행 순서 Execution  호출 순서에 합의
 타입 Type       같은 타입에 합의               타이밍 Timing        실행 시각·간격에 합의
 의미 Meaning    값의 뜻(매직 값)에 합의         값 Value             여러 값이 함께 바뀌어야
 위치 Position   값의 순서에 합의               동일성 Identity      같은 객체를 가리켜야
 알고리즘 Algorithm 같은 알고리즘에 합의
 약 ─────────────────────────────────────────────────────────────> 강
```

- 아래 정의는 connascence.io 각 페이지의 문장이다(2026-10-02 열람).
  - *이름(CoN)*: 여러 구성 요소가 한 개체의 이름에 합의해야 한다. 메서드 이름이 바뀌면 호출자도 바뀐다.
  - *타입(CoT)*: 한 개체의 타입에 합의해야 한다. 정적 타입 언어에서는 대개(항상은 아니다) 컴파일러가 잡는다.
  - *의미(CoM)*: 특정 값의 뜻에 합의해야 한다. 예: 테스트 카드 번호 `9999-…`, 권한을 정수 `2`로 표현.
  - *위치(CoP)*: 값의 순서에 합의해야 한다. 예: 리스트로 돌려준 사용자 정보의 `user[3]`.
  - *알고리즘(CoA)*: 특정 알고리즘에 합의해야 한다. 예: 송신·수신의 체크섬, 쓰기·읽기의 인코딩.
  - *실행 순서(CoE)*: 실행 순서가 중요하다. 예: 락 획득·해제 순서, `send()` 뒤에 `setSubject()` 금지.
  - *타이밍(CoTm)*: 실행 시점이 중요하다.
  - *값(CoV)*: 여러 값이 함께 바뀌어야 한다. 예: 클래스의 초기 상태와 그것을 가정한 테스트.
  - *동일성(CoI)*: 여러 구성 요소가 같은 개체를 참조해야 한다.
- 강도 순서: connascence.io "Strength"는 정적이 동적보다 약하다고 하고, 이름은 약하고 의미는 더 강하다고 예를 든다. 위 그림의 **정적 안·동적 안의 세부 순서**는 이 사이트의 나열 순서이고, 그것이 엄밀한 강도 서열인지는 확인하지 못했다 [?].

### 2. 세 축 — 강도·지역성·정도

```text
              가까움(같은 함수·클래스)        멀다(다른 모듈·서비스·저장소)
 약한 종류      괜찮다                          괜찮다
 (이름·타입)
 강한 종류      어느 정도 허용                   위험 — 약하게 바꾸거나 가깝게 옮긴다
 (의미·위치·실행 순서 …)

 정도(degree): 이 커너선스에 묶인 곳이 2곳인가 200곳인가
```

- *강도(strength)*: 그 종류의 결합을 찾고 리팩터링하기가 얼마나 어려운가. 이름은 바꾸기 쉬워 약하다. 의미는 코드베이스 전체에서 찾기 어려워 강하다(connascence.io "Strength").
- *지역성(locality)*: 묶인 요소가 얼마나 가까운가. 강한 커너선스는 한 모듈 **안**에서 더 받아들일 만하고, 멀리 떨어진 요소 사이에는 약한 것을 써야 한다(connascence.io "Locality").
- *정도(degree)*: 영향의 크기. 2개를 묶나 200개를 묶나(connascence.io "Degree").
- 실무 규칙 셋으로 줄이면: ① 강한 것을 약한 것으로 바꾼다 ② 멀리 떨어질수록 약한 것만 허용한다 ③ 정도를 줄인다. connascence.io About은 Jim Weirich를 커너선스의 "greatest proponent"로 소개하고 그의 강연 목록을 단다. 이 세 규칙이 그 강연에서 어떤 이름·문구로 나오는지는 확인하지 못했다 [?].

### 3. 약하게 바꾸는 방법

| 강한 종류 | 증상 | 더 약한 종류로 | Java 수단 |
|---|---|---|---|
| 위치 | 같은 타입 인자 여럿, `arr[3]` | 이름·타입 | 값 타입(record), 매개변수 객체, 빌더 |
| 의미 | 매직 값 `3`, `"Y"`, `-1` | 이름 | enum, 상수, `Optional` |
| 알고리즘 | 두 곳에서 같은 해시·인코딩 | 이름 | 그 알고리즘을 한 함수로 |
| 실행 순서 | `init()` 먼저 | 타입·이름 | 생성자에서 초기화, 상태별 타입 |
| 값 | 초기값을 테스트가 가정 | 이름 | `InitialState` 같은 이름 있는 상수 |

- connascence.io "Meaning"은 매직 값을 이름 있는 상수로 옮기면 의미 커너선스가 이름 커너선스로 바뀐다고 한다. 대신 상수를 둘 세 번째 위치가 생겨 **이름 커너선스의 양은 늘어난다**고 함께 적는다. 약하게 바꾸는 것은 공짜가 아니다.

### 실험 A: 강한 세 종류를 실행으로 — 위치·의미·실행 순서

```java
// 위치: 같은 타입 인자 둘
static void transfer(String from, String to, long amount) { ... }
transfer("bob", "alice", 300);                     // 의도는 alice → bob

// 의미: 포장(PACKED) 단계를 끼우며 번호를 밀었다. 주문 쪽: 3=PACKED, 4=SHIPPED
static class NotificationService {                 // 아직 옛 뜻 3=SHIPPED
    static String message(int status) { return status == 3 ? "배송이 시작됐습니다" : "(알림 없음)"; }
}

// 실행 순서: init() 전에 send() 금지
class Mailer { private StringBuilder conn; void init() { conn = new StringBuilder("smtp:"); } void send(String to) { conn.append(to); ... } }
new Mailer().send("bob");
```

(실험, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, `java strong/Conn.java`, 2026-10-02)

```text
[위치] transfer("alice","bob",300) 의도, 호출은 transfer("bob","alice",300)
  잔액 {alice=1300, bob=700}  ← 컴파일·실행 모두 통과, 반대 방향 송금
[의미] 포장 완료 주문(status=3)에 대한 알림: 배송이 시작됐습니다
       배송 시작 주문(status=4)에 대한 알림: (알림 없음)
[실행 순서] init() 없이 send()
  java.lang.NullPointerException: Cannot invoke "java.lang.StringBuilder.append(String)" because "this.conn" is null
```

- 위치: 컴파일러는 `String` 둘의 순서를 모른다. 돈이 반대로 갔다.
- 의미: 두 서비스가 숫자의 뜻에 합의했는데 한쪽만 바뀌었다. 포장만 된 주문에 "배송 시작"이 가고, 실제 배송 주문에는 알림이 없다. 예외도 없다.
- 실행 순서: 순서를 어기면 그제서야 NPE다. JDK의 도움말 NPE 메시지(JEP 358로 JDK 14에 들어왔고, JDK-8233014로 JDK 15부터 기본 켜짐)가 `this.conn`을 가리키지만, 원인이 "init 누락"이라는 것은 알려 주지 않는다.

### 실험 B: 약하게 바꾼 뒤 — 타입·이름·생성자

```java
record From(String id) {}  record To(String id) {}
static void transfer(From from, To to, long amount) { ... }
enum Status { CREATED, PACKED, SHIPPED }                  // 숫자 대신 이름
class Mailer { private final StringBuilder conn; Mailer() { conn = new StringBuilder("smtp:"); } ... }
```

(실험, 같은 환경, `java weak/Conn.java`, `javac weak/Swapped.java`)

```text
## weak
[타입] 잔액 {alice=700, bob=1300}
[이름] PACKED 알림: (알림 없음) / SHIPPED 알림: 배송이 시작됐습니다
[생성자]
  sent via smtp:bob
## weak/Swapped 컴파일
weak/Swapped.java:6: error: incompatible types: To cannot be converted to From
    public static void main(String[] a) { transfer(new To("bob"), new From("alice"), 300); }
                                                   ^
Note: Some messages have been simplified; recompile with -Xdiags:verbose to get full output
1 error
```

- 위치 → 타입: 같은 실수(인자 뒤바꿈)가 이제 **컴파일 오류**다.
- 의미 → 이름: enum 사이에 `PACKED`를 끼워도 `SHIPPED`의 뜻은 밀리지 않는다.
- 실행 순서 → 생성자: 초기화 안 된 `Mailer`를 만들 방법이 없다. 잘못된 순서가 **표현 불가능**해졌다.
- 대가: `From`·`To`·`Status` 타입이 늘었다. 이름 커너선스는 늘었다(위 3절).

### 실험 C: 강도 = 찾기 어려움 — 이름 vs 의미

두 질문을 같은 작은 코드베이스(4파일)에 던졌다. ① `Mailer.send`의 이름을 바꾸면 고칠 곳은? ② 상태 `3`(배송)의 뜻을 바꾸면 고칠 곳은?

(실험, 같은 환경, `sd/01/e05/rename`)

```text
## grep -rnw 3 src  (상태 3 '배송'의 뜻을 찾으려는 검색)
src/app/Api.java:3:    static String label(int code) { return switch (code) { case 1 -> "주문됨"; case 3 -> "배송중"; default -> "기타"; }; }
src/app/Api.java:4:    static void ping(String admin) { Mailer.send(admin, "top 3 errors"); }
src/app/Report.java:3:    static int shipped(int[] statuses) { int n = 0; for (int s : statuses) if (s == 3) n++; return n; }
src/app/Report.java:4:    static void mail(String to) { for (int i = 0; i < 3; i++) Mailer.send(to, "page " + (i + 1) + "/3"); }
src/app/Notifier.java:3:    static final int MAX_RETRIES = 3;
src/app/Notifier.java:4:    static void onStatus(String user, int status) { if (status == 3) Mailer.send(user, "배송 시작"); }
## 이 중 실제 '배송 상태'인 곳: Notifier status==3, Report s==3, Api case 3 → 3곳
src/app/Api.java:4: error: cannot find symbol
    static void ping(String admin) { Mailer.send(admin, "top 3 errors"); }
src/app/Notifier.java:4: error: cannot find symbol
src/app/Report.java:4: error: cannot find symbol
3 errors
```

| | 도구 | 걸린 줄 | 실제로 고칠 곳 | 놓침 |
|---|---|---|---|---|
| 의미(`3`) | `grep -w 3` | 6줄 | 3곳 | 0, 대신 거짓 양성 3줄(재시도 횟수·페이지 수·문구) |
| 이름(`send` → `deliver`) | `javac` | 3건 | 3곳 | 0, 거짓 양성 0 |

- 이름 커너선스는 컴파일러가 **정확히** 찾아 준다. 그래서 약하다.
- 의미 커너선스는 사람이 grep 결과를 하나씩 판정해야 한다. 이 작은 코드에서도 걸린 줄의 절반이 다른 뜻의 `3`이었다. 다른 모양(`case 3`, `s == 3`)으로 쓰여 정규식을 잘못 짜면 놓친다(01의 unknown unknowns).

## 쓰이는 자료구조·알고리즘

- **심볼 테이블·이름 해석** — 이름 커너선스가 약한 이유. 컴파일러는 심볼 테이블로 소스의 정적 참조를 빠짐없이 찾아(리플렉션·문자열로 부르는 곳은 제외) 이름 불일치를 오류로 낸다(실험 C). 언어 영역 [language](../../language/README.md).
- **타입 검사** — 위치 커너선스를 타입 커너선스로 바꾸면 타입 검사기가 순서 실수를 잡는다(실험 B). 24 types-as-invariants에서 깊게.
- **유한 상태 기계** — 실행 순서 커너선스는 객체가 숨긴 상태 기계다. 상태별로 다른 타입을 두거나 생성자에서 초기 상태를 끝내면 잘못된 전이를 표현할 수 없다.
- **텍스트 검색(grep)** — 의미 커너선스를 찾는 유일한 일반 도구지만 정밀도가 낮다(실험 C). 문자열 탐색은 [algorithm/25-string-matching](../../algorithm/25-string-matching/2-summary.md).
- **동일성 vs 동등성** — 동일성 커너선스는 "같은 객체"(`==`)에 대한 합의다. 캐시·세션에서 다른 인스턴스를 받으면 깨진다.

## 적용 — 풀어나가는 법

### 1. 리뷰에서 쓰는 순서

1. 바뀐 줄마다 "이걸 바꾸면 함께 바꿔야 하는 곳"을 찾는다.
2. 그 관계에 **종류**를 붙인다(이름·위치·의미·실행 순서 …).
3. **지역성**을 본다. 같은 메서드 안인가, 다른 모듈·서비스인가.
4. **정도**를 센다. 몇 곳이 묶였나.
5. 멀리 떨어졌는데 강하면 약하게 바꾼다(위 3절 표). 가깝고 정도가 작으면 그냥 둔다.

### 2. 코드 (Java)

```java
// 위치 → 이름·타입: 같은 타입 인자가 셋 이상이면 의심
void transfer(AccountId from, AccountId to, Money amount)      // 여전히 from/to 같은 타입 — 위치 커너선스 남음
void transfer(Transfer t)                                       // record Transfer(AccountId from, AccountId to, Money amount)
                                                                // 호출: new Transfer(from, to, amount) — 생성자 인자에도 순서가 있다
                                                                // 이름으로: Transfer.from(a).to(b).amount(m) 빌더

// 의미 → 이름
if (status == 3)                         →  if (status == Status.SHIPPED)

// 실행 순서 → 생성자
m.init(); m.send(x);                     →  new Mailer(config).send(x)
```

- 주의: record 생성자도 인자 순서가 있다. 같은 타입 필드 둘을 record로 묶으면 위치 커너선스가 **생성자로 옮겨갈 뿐**이다. 실험 B처럼 서로 다른 타입(`From`·`To`)이거나 이름 붙인 빌더여야 컴파일러가 잡는다.

### 3. 경계를 넘는 커너선스

- 서비스 사이의 상태 코드·필드 순서(CSV 열 순서)·직렬화 형식은 강한 커너선스가 **가장 먼 거리**에 걸린 경우다.
- 약하게 바꾸는 수단: 숫자 대신 이름(`"SHIPPED"`), 위치 대신 이름 있는 필드(CSV 열 순서 대신 JSON 키), 스키마 레지스트리로 합의를 한 곳에. 메시지 형식 진화는 distributed 영역 [distributed/19-message-types-channels-and-endpoints](../../distributed/19-message-types-channels-and-endpoints/2-summary.md).

## 장애 시나리오와 대처

### 1. 인자 순서 결합 → 반대 송금 (⚠ 커리큘럼)

- 현상: `transfer(from, to, amount)` 호출부에서 from/to가 뒤바뀌었다. 컴파일·테스트 통과 후 운영에서 반대 방향 이체.
- 보이는 형태: 예외 없음. 잔액 대사에서 두 계좌가 정반대로 어긋난다(실험 A: `alice=1300, bob=700`).
- 원인: 같은 타입 인자 둘 사이의 위치 커너선스가 호출부(먼 곳)까지 뻗어 있다.
- 대처: `From`/`To` 같은 서로 다른 타입이나 이름 붙인 빌더로 바꾼다. 같은 실수가 컴파일 오류가 된다(실험 B).

### 2. 매직 값 결합 → 한쪽만 수정 (⚠ 커리큘럼)

- 현상: 상태 `3`의 뜻이 서비스 두 곳에 따로 하드코딩돼 있다. 한쪽만 바꿔 알림이 엉뚱한 주문에 나간다.
- 보이는 형태: 예외 없음. 고객 문의("포장만 됐는데 배송 시작 알림이 왔어요"), 알림 발송 수 지표가 단계 수와 맞지 않음(실험 A).
- 원인: 의미 커너선스가 모듈 경계를 넘었다.
- 대처: enum·이름 있는 상수로 바꾼다. 서비스 경계라면 숫자 대신 이름으로 직렬화하고, 모르는 값은 실패로 드러내게 한다.

### 3. 호출 순서 결합 → `init()` 전 `send()` NPE (⚠ 커리큘럼)

- 현상: 새 호출자가 초기화를 빠뜨려 NPE.
- 보이는 형태: `NullPointerException: Cannot invoke "java.lang.StringBuilder.append(String)" because "this.conn" is null`. 스택은 `send` 안을 가리키고, 원인(초기화 누락)은 호출자 쪽에 있다.
- 원인: 실행 순서 커너선스가 API 사용자에게 노출됐다.
- 대처: 생성자에서 초기화를 끝내거나, 초기화 전/후를 다른 타입으로 나눈다(`MailerConfig.connect()`가 `Mailer`를 돌려줌). 잘못된 순서를 표현할 수 없게 만든다.

### 4. 알고리즘 결합 → 한쪽만 바꾼 인코딩·해시

- 현상: 쓰기 쪽이 저장 형식을 암호화·압축으로 바꿨는데 읽기 쪽이 옛 방식으로 읽는다.
- 보이는 형태: 디코딩 오류, 깨진 문자, 체크섬 불일치 로그.
- 원인: 두 곳이 같은 알고리즘에 각자 합의(connascence.io "Algorithm"의 캐시 파일 예와 같은 구조).
- 대처: 쓰기·읽기를 한 모듈(한 쌍의 함수)로 묶고, 형식 버전을 데이터에 적는다.

## 핵심 문장

- 커너선스는 "하나를 바꾸면 다른 것도 바꿔야 하는" 관계에 종류 이름을 붙인 어휘다(Page-Jones 1992).
- 종류는 정적(이름·타입·의미·위치·알고리즘)과 동적(실행 순서·타이밍·값·동일성)이고, 정적이 동적보다 약하다.
- 강한 것은 약하게 바꾸고, 멀리 떨어질수록 약한 것만 허용하고, 묶인 곳의 수를 줄인다.
- 실험에서 같은 인자 뒤바꿈이 `String` 둘이면 반대 송금으로 실행됐고, `From`/`To` 타입이면 컴파일 오류였다.
- 이름 커너선스는 컴파일러가 정확히 찾고(3건 = 3곳), 의미 커너선스는 grep이 거짓 양성과 함께 찾는다(6줄 중 3곳). 그 차이가 강도다.

## 관련 주제·근거

- 선행
  - [02-modularity-coupling-cohesion](../02-modularity-coupling-cohesion/2-summary.md) — 결합도 단계
- 함께
  - [01-complexity](../01-complexity/2-summary.md) — 같은 지식이 다른 모양으로 적힌 암묵적 의존
  - [04-decompose-by-change](../04-decompose-by-change/2-summary.md) — 함께 바뀌는 것을 한 모듈로
- 후속
  - [23-design-by-contract](../23-design-by-contract/2-summary.md) · [24-types-as-invariants](../24-types-as-invariants/2-summary.md)
  - [10 code-smells](../10-code-smells/2-summary.md)(Primitive Obsession·Data Clumps)
- 다른 영역
  - [distributed/19-message-types-channels-and-endpoints](../../distributed/19-message-types-channels-and-endpoints/2-summary.md) — 서비스 경계를 넘는 형식 합의
  - [algorithm/25-string-matching](../../algorithm/25-string-matching/2-summary.md)
- 글·문서
  - Meilir Page-Jones, "Comparing techniques by means of encapsulation and connascence", CACM 35(9):147–151, 1992-09 — 서지는 Crossref(DOI 10.1145/130994.131004)로 확인, 본문 미열람
  - Meilir Page-Jones, 『What Every Programmer Should Know About Object-Oriented Design』(Dorset House) — 커리큘럼 출처, 열람하지 못했다. 출판 연도는 커리큘럼 1995, connascence.io About 1996으로 출처마다 다르다 [?]
  - connascence.io — 홈(세 축), Strength·Locality·Degree, 종류 9개 페이지, About(Page-Jones·Weirich 강연 목록) <https://connascence.io/> (2026-10-02 열람)
  - Jim Weirich, "Grand Unified Theory of Software Design"(Aloha on Rails, 같은 제목의 앞선 강연은 2009)·"Connascence Examined"(2012, YOW) — connascence.io About <https://connascence.io/pages/about.html>에 목록만 확인, 강연 내용은 확인하지 못했다 [?]
  - Wikipedia "Connascence" — 결합도와 커너선스의 관계 개관 <https://en.wikipedia.org/wiki/Connascence>
  - JEP 358 "Helpful NullPointerExceptions"(Release 14) <https://openjdk.org/jeps/358> · JDK-8233014 "Enable ShowCodeDetailsInExceptionMessages by default"(Fix Version 15) <https://bugs.openjdk.org/browse/JDK-8233014>
- 실험 목록 (코드: scratchpad `sd/01/e05/`, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, 2026-10-02)
  - A `strong/Conn.java`(`java strong/Conn.java`): 위치 → 반대 송금, 의미 → 엉뚱한 알림, 실행 순서 → NPE
  - B `weak/Conn.java`·`weak/Swapped.java`: 타입·enum·생성자로 바꾼 뒤 정상 실행, 인자 뒤바꿈은 `incompatible types` 컴파일 오류
  - C `rename/src/app/*.java`: `grep -rnw 3` 6줄 중 실제 3곳, `send` 이름 변경 시 `javac` 오류 3건 = 3곳
