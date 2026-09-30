# Java 20 (2023년 3월)

> 원본: `~/project/java-history/java/java-20.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JEP 번호·클래스/API 이름·코드블록 4개(java 4)·「릴리스 정보」와 「그 외 변경」의 목록은 원문 그대로다.\
> 「한눈에」의 리허설 비유와 대응표, 「이 편에서 미리보기인가 정식인가」 표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다. 새 도식은 없다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> Java 21 LTS를 6개월 앞두고, 21에 담길 핵심 기능들(가상 스레드, 레코드 패턴, switch 패턴 매칭, FFM API, 구조적 동시성, scoped values)을 마지막으로 다듬은 "징검다리" 릴리스. 정식화된 새 기능은 없고, 전부 다음 단계의 프리뷰·인큐베이터로 진행되었다.

이 편을 읽는 비유는 **본 공연 전날의 리허설**이다.\
원문이 「시대적 배경」에서 그 성격을 이렇게 적는다 — "Java 20은 **다음 LTS(Java 21)를 위한 최종 점검 릴리스**의 성격이 강하다."

| 비유 | 실체 |
|---|---|
| 본 공연 | Java 21 — 원문 표현으로 "LTS에서 안정적으로 정식화하는 전략"의 그 자리다 |
| 리허설 | Java 20 — 원문 표현으로 "LTS 직전 비-LTS 릴리스에서 프리뷰 기능을 한 번 더 검증·정련해 피드백을 흡수한 뒤" |
| 이날 정식으로 올린 곡 | 없다 — 원문 표현으로 "정식화된 새 기능은 없고", "신규 정식 기능은 없었다" |
| 리허설에서 처음 맞춰 본 새 곡 | Scoped Values — 원문 표현으로 "Scoped Values라는 새 개념이 처음 등장해" (1차 인큐베이터다) |

### 이 편에서 미리보기인가 정식인가

**이 편은 7개 JEP 전부가 프리뷰 아니면 인큐베이터다.** 원문이 직접 그렇게 적는다 — "7개 JEP 모두가 기존 기능의 새로운 프리뷰 라운드이거나 인큐베이터 단계로, 신규 정식 기능은 없었다."\
원문이 절 제목·괄호에 적어 둔 상태를 한자리에 모으면 이렇다.

| 기능 | 이 편(20)에서의 상태 — 원문 절 제목 표기 | 정식이 된 편 |
|---|---|---|
| 가상 스레드 (JEP 436) | **Second Preview/2차 프리뷰** | 21 (JEP 444) — 원문이 "정식화는 Java 21(JEP 444)에서 이루어진다"고 직접 적는다 |
| 레코드 패턴 (JEP 432) | **Second Preview/2차 프리뷰** | 21 (JEP 440) — 원문이 "정식화는 Java 21(JEP 440)"이라고 직접 적는다 |
| Pattern Matching for switch (JEP 433) | **Fourth Preview/4차 프리뷰** | 21 (JEP 441) — 원문이 "정식화는 Java 21(JEP 441)"이라고 직접 적는다 |
| Foreign Function & Memory API (JEP 434) | **Second Preview/2차 프리뷰** | 22 (JEP 454) — 원문이 "정식화는 Java 22(JEP 454)에서 이루어진다(21에서는 3차 프리뷰)"라고 직접 적는다 |
| Scoped Values (JEP 429) | **Incubator/1차 인큐베이터** | 25 (JEP 506) — 출처: 원문 `java-25.md` |
| 구조적 동시성 (JEP 437) | **Second Incubator/2차 인큐베이터** | 이 편 뒤로도 정식이 되지 않는다 — 21에서 프리뷰(JEP 453)이고 25 시점에도 프리뷰다(출처: 원문 `java-21.md`·`java-25.md`) |
| Vector API (JEP 438) | **Fifth Incubator/5차 인큐베이터** | 이 편 뒤로도 인큐베이터가 이어진다 — 25 시점에 10차다(출처: 원문 `java-25.md`) |

> **프리뷰(preview) / 인큐베이터(incubator)** — 정식이 아닌 채로 먼저 실어 보내는 단계 표기. 원문은 이 편을 "모든 핵심 변경이 프리뷰·인큐베이터 단계 진전에 집중되었다"고 적는다.\
> 예: 이 편의 가상 스레드 코드 첫 줄에 원문이 단 주석이 "--enable-preview 필요 (JDK 20)"이고, Scoped Values 쪽 주석은 "인큐베이터 API (JDK 20)"다.

> **라운드(round) / 차수** — 같은 기능이 정식이 되기 전까지 프리뷰·인큐베이터를 되풀이하는 횟수. 원문은 이 편의 기능들을 "기존 기능의 새로운 프리뷰 라운드"라 적는다.\
> 예: 같은 switch 패턴 매칭이 이 편에서 4차 프리뷰이고, 원문이 그 앞 차수로 든 것이 "Java 19(JEP 427)의 3차 프리뷰"다.

## 릴리스 정보
- 정식 출시일: 2023년 3월 21일
- LTS 여부: 아니오 (단기 지원)
- 포함 JEP 수: 7개

## 시대적 배경
Java 20은 **다음 LTS(Java 21)를 위한 최종 점검 릴리스**의 성격이 강하다.\
7개 JEP 모두가 기존 기능의 새로운 프리뷰 라운드이거나 인큐베이터 단계로, 신규 정식 기능은 없었다.

이는 6개월 케이던스 모델의 의도된 작동 방식이다.\
LTS 직전 비-LTS 릴리스에서 프리뷰 기능을 한 번 더 검증·정련해 피드백을 흡수한 뒤, LTS에서 안정적으로 정식화하는 전략이다.\
실제로 Java 20에서 다듬어진 가상 스레드·레코드 패턴·switch 패턴 매칭이 모두 Java 21에서 정식이 된다.

> **케이던스(cadence) 모델** — 릴리스를 일정한 주기로 내보내는 방식. 원문은 이 편의 모습을 그 "의도된 작동 방식"이라 적는다.\
> 예: 원문이 든 그 전략의 두 단계가 "LTS 직전 비-LTS 릴리스에서 … 검증·정련"과 "LTS에서 안정적으로 정식화"다.

## 주요 추가 기능

### 가상 스레드 (JEP 436, Second Preview/2차 프리뷰) ⭐
- Java 19(JEP 425)의 1차 프리뷰에 이은 **두 번째 프리뷰**. 큰 API 변경 없이 안정화에 집중했다.
- 19(JEP 425) 대비 의미 있는 API 변경은 없고, 프리뷰 기간 피드백을 반영한 사소한 정련과 안정화가 중심이다. (`Thread.Builder`는 이미 19에 도입돼 있었고, 가상 스레드가 `ThreadLocal`을 항상 지원하도록 한 변경은 20이 아니라 21 정식화에서 이루어진다.)
- 정식화는 Java 21(JEP 444)에서 이루어진다.

> **가상 스레드** — 원문 `java-19.md`가 "OS 스레드에 1:1로 묶이지 않는 경량 스레드"라 정의한 것. 이 편은 그 정의를 다시 적지 않고, 19 대비 무엇이 달라졌는지를 적는다.\
> 예: 원문이 아래 코드 주석에 적어 둔 것이 "10만 개 작업이 적은 수의 OS 스레드 위에서 실행된다"이다.

> **`ThreadLocal`** — 스레드마다 따로 보관되는 값. 원문이 괄호에 분명히 적어 둔 대로, 가상 스레드가 이것을 항상 지원하게 된 변경은 **이 편이 아니라 21 정식화**에서 일어난다.\
> 예: 원문이 같은 괄호에서 마찬가지로 이 편의 것이 아니라고 적은 또 하나가 `Thread.Builder`다 — "이미 19에 도입돼 있었고".

```java
// --enable-preview 필요 (JDK 20)
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    var futures = IntStream.range(0, 100_000)
        .mapToObj(i -> executor.submit(() -> {
            Thread.sleep(Duration.ofMillis(100)); // 블로킹 I/O를 흉내
            return i;
        }))
        .toList();
    // 10만 개 작업이 적은 수의 OS 스레드 위에서 실행된다
}
```

### 레코드 패턴 (JEP 432, Second Preview/2차 프리뷰)
- Java 19(JEP 405)에 이은 **두 번째 프리뷰**. 주요 변경: 향상된 `for` 루프 헤더에서의 레코드 패턴 사용을 **추가**하고, 제네릭 레코드 패턴의 타입 추론을 다듬었으며, 명명된 레코드 패턴(named record patterns) 지원은 제거했다.
- 정식화는 Java 21(JEP 440).

원문이 이 편의 변경 셋을 각각 추가·다듬음·제거로 나눠 적었다는 점을 그대로 읽어 두면 된다 — 프리뷰 단계에서는 들어왔던 것이 도로 빠지기도 한다.

> **레코드 패턴** — 레코드 값을 꺼내 변수로 받는 패턴. 원문 `java-19.md`가 "레코드 값을 분해(deconstruct)"하는 것이라 적는다.\
> 예: 아래 코드의 `case Circle(double r)`가 그것으로, `Circle`의 값을 `r`로 받는다.

> **전체성 보장** — 분기가 가능한 경우를 모두 덮었음이 보장되는 것. 원문은 그 근거를 `sealed`로 든다.\
> 예: 아래 코드에서 `switch`를 닫는 줄에 원문이 단 주석이 "sealed 덕분에 default 불필요 (전체성 보장)"이고, 그 `sealed interface Shape permits Circle, Rectangle`이 코드 위쪽에 적혀 있다.

```java
// --enable-preview 필요
sealed interface Shape permits Circle, Rectangle {}
record Circle(double r) implements Shape {}
record Rectangle(double w, double h) implements Shape {}

static double area(Shape shape) {
    return switch (shape) {
        case Circle(double r)             -> Math.PI * r * r;
        case Rectangle(double w, double h) -> w * h;
    }; // sealed 덕분에 default 불필요 (전체성 보장)
}
```

### Pattern Matching for switch (JEP 433, Fourth Preview/4차 프리뷰)
- Java 19(JEP 427)의 3차 프리뷰에 이은 **네 번째 프리뷰**. 레코드 패턴(JEP 432)과의 공진화를 위해 한 라운드 더 프리뷰로 유지되었다.
- 전체성(exhaustiveness) 검사 방식과 패턴이 적용되는 타입 처리 등이 정련되었다. 정식화는 Java 21(JEP 441).

> **`when` 가드 / `null` 케이스** — 타입이 맞은 뒤 조건을 하나 더 거는 것 / `null`을 `case`로 직접 받는 것. 원문은 이 편의 코드를 "when 가드 + null 케이스 (4차 프리뷰)"라 적는다.\
> 예: 아래 코드의 `case Integer i when i<0`이 가드이고, `case null`이 널 케이스다.

```java
// when 가드 + null 케이스 (4차 프리뷰)
static String describe(Object obj) {
    return switch (obj) {
        case null               -> "널";
        case Integer i when i<0 -> "음수";
        case Integer i          -> "정수";
        case String s           -> "문자열(길이 " + s.length() + ")";
        default                 -> "기타";
    };
}
```

### Foreign Function & Memory API (JEP 434, Second Preview/2차 프리뷰)
- Java 19(JEP 424)에 이은 **두 번째 프리뷰**. 의미 있는 API 정리가 이루어졌다.
- `MemorySegment`와 `MemoryAddress` 추상화를 **하나로 통합**, `MemoryLayout` 계층을 sealed로 만들어 패턴 매칭과 잘 어울리게 했고, `MemorySession`을 `Arena`와 `SegmentScope`로 분리했다.
- 정식화는 Java 22(JEP 454)에서 이루어진다(21에서는 3차 프리뷰).

> **`MemorySegment` / `MemorySession`** — 원문이 이 편의 API 정리 대상으로 든 두 이름이다. **원문은 이 둘의 뜻을 풀지 않는다** — 이 편에서 무엇이 달라졌는지만 적는다.\
> 예: 원문 표현으로 앞엣것은 "`MemorySegment`와 `MemoryAddress` 추상화를 **하나로 통합**"이고, 뒤엣것은 "`MemorySession`을 `Arena`와 `SegmentScope`로 분리했다"이다.

### Scoped Values (JEP 429, Incubator/1차 인큐베이터)
- 스레드(특히 가상 스레드) 내부와 자식 스레드로 **불변 데이터를 안전하게 공유**하는 메커니즘. `ThreadLocal`의 단점을 개선하는 것이 목표다.

**왜 Scoped Values가 나왔나** — 원문이 같은 절에 적어 둔 그대로다: "`ThreadLocal`은 가변·상속 비용·생명주기 관리가 문제인데, 가상 스레드가 수천~수만 개 존재하는 환경에서 특히 부담이 크다."

그 해법을 원문은 같은 문단 다음 문장에서 이렇게 적는다 — "Scoped Value는 정해진 동적 범위(바운드 영역) 안에서만 값이 유효하고 불변이라 가볍고 안전하다."

> **동적 범위(바운드 영역)** — 값이 유효한 구간. 아래 코드에서는 `run(...)` 이 도는 동안 **그 안에서 불린 코드 전부**이고(호출된 `handleRequest()` 안에서도 `get()`이 된다), 적어 둔 블록 안쪽으로만 한정되는 것이 아니다. 원문 표현으로 "정해진 동적 범위(바운드 영역) 안에서만 값이 유효하고 불변"이다.\
> 예: 아래 코드에서 원문이 `.run(() -> handleRequest())` 줄에 단 주석이 "이 범위 안에서만 CURRENT_USER.get() 유효"이고, 그 안의 `handleRequest()`에 단 주석이 "명시적 인자 전달 없이 접근"이다.

```java
// 인큐베이터 API (JDK 20)
final static ScopedValue<User> CURRENT_USER = ScopedValue.newInstance();

ScopedValue.where(CURRENT_USER, loggedInUser)
           .run(() -> handleRequest()); // 이 범위 안에서만 CURRENT_USER.get() 유효

void handleRequest() {
    User u = CURRENT_USER.get(); // 명시적 인자 전달 없이 접근
}
```

### 구조적 동시성 (JEP 437, Second Incubator/2차 인큐베이터)
- Java 19(JEP 428)에 이은 **두 번째 인큐베이터**. API는 거의 그대로 유지하되, `StructuredTaskScope`가 scoped values를 상속·전파하도록 업데이트했다.

### Vector API (JEP 438, Fifth Incubator/5차 인큐베이터)
- SIMD 벡터 연산 API의 **다섯 번째 인큐베이터**. 19 대비 API 변경은 없고, 버그 수정·성능 개선과 향후 Project Valhalla 값 타입과의 정렬에 초점을 맞췄다.

> **Project Valhalla** — 원문이 Vector API가 앞으로 맞춰 갈 대상으로 이름만 든 OpenJDK 작업 갈래. 원문은 이 편에서 그 내용을 풀지 않는다.\
> 예: 원문 표현으로 이 편의 초점 가운데 하나가 "향후 Project Valhalla 값 타입과의 정렬"이다.

## 그 외 변경
- Java 20에는 정식화된 신규 언어/플랫폼 기능이 없다. 모든 핵심 변경이 프리뷰·인큐베이터 단계 진전에 집중되었다.
- 다수의 성능·안정성·버그 수정과 JDK 내부 정리 작업이 병행되었다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 불릿은 원문의 것이다.)*

Java 20은 단독으로 보면 화려하지 않지만, **Java 21 LTS의 품질을 떠받친 핵심 릴리스**다.
- 가상 스레드·레코드 패턴·switch 패턴 매칭이 여기서 마지막 프리뷰 라운드를 거치며 다듬어졌고, 그 결과 21에서 안심하고 정식화될 수 있었다.
- Scoped Values라는 새 개념이 처음 등장해, 가상 스레드 시대에 맞는 컨텍스트 전달 방식을 제시했다.
- 6개월 케이던스 + 프리뷰 제도가 "큰 기능을 점진적으로, 그러나 LTS에서는 안정적으로" 내보내는 데 어떻게 기여하는지를 보여준 모범 사례다.

## 용어 풀이

- **프리뷰(preview) / 인큐베이터(incubator)** — 정식이 아닌 채로 먼저 실어 보내는 단계 표기. 원문 표현으로 이 편은 "모든 핵심 변경이 프리뷰·인큐베이터 단계 진전에 집중되었다".
- **라운드(round) / 차수** — 같은 기능이 정식이 되기 전까지 프리뷰·인큐베이터를 되풀이하는 횟수. 이 편의 switch 패턴 매칭이 4차, Vector API가 5차다.
- **케이던스(cadence) 모델** — 릴리스를 일정한 주기로 내보내는 방식. 원문은 이 편의 모습을 그 "의도된 작동 방식"이라 적는다.
- **가상 스레드** — 원문 `java-19.md`의 정의로 "OS 스레드에 1:1로 묶이지 않는 경량 스레드". 이 편에서는 2차 프리뷰다.
- **`ThreadLocal`** — 스레드마다 따로 보관되는 값. 가상 스레드가 이것을 항상 지원하게 된 변경은 원문이 분명히 적은 대로 이 편이 아니라 21 정식화의 것이다.
- **레코드 패턴** — 레코드 값을 꺼내 변수로 받는 패턴. 이 편에서는 2차 프리뷰이고, 정식은 21(JEP 440)이다.
- **전체성(exhaustiveness) 보장** — 분기가 가능한 경우를 모두 덮었음이 보장되는 것. 원문 주석 표현으로 "sealed 덕분에 default 불필요 (전체성 보장)"이다.
- **`when` 가드 / `null` 케이스** — 타입이 맞은 뒤 조건을 하나 더 거는 것 / `null`을 `case`로 직접 받는 것. 원문이 이 편 코드에 붙인 제목이 "when 가드 + null 케이스 (4차 프리뷰)"다.
- **`MemorySegment` / `MemorySession`** — 원문이 이 편의 API 정리 대상으로 든 두 이름. 원문은 뜻을 풀지 않고, 앞엣것이 `MemoryAddress`와 통합되고 뒤엣것이 `Arena`와 `SegmentScope`로 갈렸다고만 적는다.
- **Scoped Value / 동적 범위(바운드 영역)** — 원문 표현으로 "불변 데이터를 안전하게 공유"하는 메커니즘 / 그 값이 유효한 구간. 이 편에서는 1차 인큐베이터다.
- **`StructuredTaskScope`** — 구조적 동시성의 클래스. 이 편에서 scoped values를 "상속·전파하도록 업데이트"됐다.
- **SIMD / Project Valhalla** — 하나의 명령으로 여러 값을 한꺼번에 처리하는 CPU 기능 / 원문이 Vector API가 앞으로 맞춰 갈 대상으로 이름만 든 작업 갈래.

## 참고 출처
- [JEP 436: Virtual Threads (Second Preview)](https://openjdk.org/jeps/436)
- [JEP 432: Record Patterns (Second Preview)](https://openjdk.org/jeps/432)
- [JEP 433: Pattern Matching for switch (Fourth Preview)](https://openjdk.org/jeps/433)
- [JEP 434: Foreign Function & Memory API (Second Preview)](https://openjdk.org/jeps/434)
- [JEP 429: Scoped Values (Incubator)](https://openjdk.org/jeps/429)
- [JEP 437: Structured Concurrency (Second Incubator)](https://openjdk.org/jeps/437)
- [JEP 438: Vector API (Fifth Incubator)](https://openjdk.org/jeps/438)
- [OpenJDK JDK 20 프로젝트 페이지](https://openjdk.org/projects/jdk/20/)
- [InfoQ: Java 20 Delivers Features for Projects Amber, Loom and Panama](https://www.infoq.com/news/2023/03/java20-released/)
