# Java 19 (2022년 9월)

> 원본: `~/project/java-history/java/java-19.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JEP 번호·클래스/API 이름·코드블록 4개(java 4)·「릴리스 정보」와 「그 외 변경」의 목록은 원문 그대로다.\
> ASCII 도식 1개와 「한눈에」의 좌석 비유와 대응표, 「이 편에서 미리보기인가 정식인가」 표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> Project Loom의 **가상 스레드(Virtual Threads)**가 마침내 프리뷰로 등장한, 동시성 역사에서 가장 중요한 전환점 중 하나가 된 릴리스. 구조적 동시성(인큐베이터), 레코드 패턴(프리뷰), Foreign Function & Memory API의 프리뷰 승격도 함께 이루어졌다.

이 편의 대표 변경을 읽는 비유는 **좌석은 적은데 손님은 아주 많은 식당**이다.\
원문이 「주요 추가 기능」에서 그 구조를 이렇게 적는다 — "JVM이 다수의 가상 스레드를 소수의 플랫폼(OS) 스레드(캐리어 스레드) 위에 다중화(M:N)한다."

| 비유 | 실체 |
|---|---|
| 좌석 | 플랫폼(OS) 스레드 = 캐리어 스레드 — 원문 표현으로 "소수의" 쪽이다 |
| 손님 | 가상 스레드 — 원문 표현으로 "다수의" 쪽이고, "수십만~수백만 개"까지 만들 수 있다 |
| 기다리는 동안 좌석을 비켜 주는 것 | 언마운트(unmount) — 원문 표현으로 "JVM이 해당 가상 스레드를 캐리어에서 언마운트(unmount)하고 다른 가상 스레드를 올린다" |
| 비켜 주지 못하고 좌석을 차지한 채 기다리는 손님 | 고정(pinning) — 원문 표현으로 "언마운트되지 못하고 캐리어에 고정(pinning)되어 OS 스레드를 점유할 수 있다" |

블로킹이 사라지는 것이 아니다 — 원문이 적은 것은 블로킹 작업에 **진입하면** 캐리어에서 언마운트된다는 것이고, 언마운트되지 못하는 자리를 원문이 같은 문단에서 함께 든다.

### 이 편에서 미리보기인가 정식인가

**이 편에서 흔한 오해가 "19부터 가상 스레드를 쓴다"이다. 이 편에서는 1차 프리뷰다.**\
원문은 이 편을 두고 "이 모든 것이 아직 프리뷰/인큐베이터였기에 운영 환경에 바로 쓰긴 어려웠지만"이라고 적는다.\
원문이 절 제목·괄호에 적어 둔 상태를 한자리에 모으면 이렇다.

| 기능 | 이 편(19)에서의 상태 — 원문 절 제목 표기(★는 원문 표기가 아니라 재서술자 추론이거나 다른 편 원문에서 온 것) | 정식이 된 편 |
|---|---|---|
| 가상 스레드 (JEP 425) | **Preview/1차 프리뷰** | 21 (JEP 444) — 원문이 "19·20에서 프리뷰를 거쳐 **Java 21(JEP 444)에서 정식**이 된다"고 직접 적는다 |
| 구조적 동시성 (JEP 428) | **Incubator/1차 인큐베이터** | 이 편 뒤로도 정식이 되지 않는다 — 20에서 2차 인큐베이터, 21에서 프리뷰(JEP 453)이고 25 시점에도 프리뷰다(출처: 원문 `java-20.md`·`java-21.md`·`java-25.md`) |
| 레코드 패턴 (JEP 405) | **Preview/1차 프리뷰** | 21 (JEP 440) — 원문이 "Java 21(JEP 440)에서 정식화된다"고 직접 적는다 |
| Foreign Function & Memory API (JEP 424) | **Preview/1차 프리뷰** (인큐베이터에서 승격) | 22 (JEP 454) — 출처: 원문 `java-20.md`·`java-22.md` |
| Pattern Matching for switch (JEP 427) | **Third Preview/3차 프리뷰** | 21 (JEP 441) — 원문이 "정식화는 Java 21(JEP 441)"이라고 직접 적는다 |
| Vector API (JEP 426) | **Fourth Incubator/4차 인큐베이터** | 이 편 뒤로도 인큐베이터가 이어진다 — 출처: 원문 `java-20.md`(5차) |
| Linux/RISC-V 포트 (JEP 422) | ★정식(그 외 변경) — 원문 「그 외 변경」 불릿에 상태 표기가 없다. 재서술자 추론이다 | 19 — 이 편이다 |

> **프리뷰(preview) / 인큐베이터(incubator)** — 정식이 아닌 채로 먼저 실어 보내는 단계 표기. 언어 문법·정식 패키지 쪽에 프리뷰를, 아직 `jdk.incubator.*`에 있는 API에 인큐베이터를 쓴다.\
> 예: 이 편의 가상 스레드 코드 첫 줄에 원문이 단 주석이 "--enable-preview 필요 (JDK 19)"이고, 구조적 동시성 쪽 주석은 "인큐베이터 API (JDK 19)"다.

## 릴리스 정보
- 정식 출시일: 2022년 9월 20일
- LTS 여부: 아니오 (단기 지원)
- 포함 JEP 수: 7개

## 시대적 배경
Java 19는 **세 거대 프로젝트(Loom, Panama, Amber)의 결실이 동시에 가시화된** 릴리스다.\
특히 2017년 말 시작되어 약 5년간 진행되어 온 Project Loom의 가상 스레드가 처음으로 프리뷰로 공개되면서, "스레드 하나에 OS 스레드 하나"라는 Java 동시성의 근본 제약을 깨뜨릴 길이 열렸다.

**왜 가상 스레드가 나왔나** — 원문이 같은 절에 적어 둔 그대로다: "당시 백엔드 생태계는 높은 동시성을 다루기 위해 리액티브 프로그래밍(WebFlux, RxJava, Reactor)에 크게 의존하고 있었다. 그러나 리액티브 스타일은 코드가 복잡하고 디버깅·스택트레이스가 어려웠다."\
가상 스레드는 **"익숙한 동기·블로킹 코드를 그대로 쓰면서 리액티브 수준의 확장성"**을 약속하며 이 흐름에 정면으로 도전했다.

> **리액티브 프로그래밍** — 원문이 이 편의 대비 상대로 든 스타일. 원문이 든 구현체가 WebFlux, RxJava, Reactor이고, 원문이 든 약점이 "코드가 복잡하고 디버깅·스택트레이스가 어려웠다"이다.\
> 예: 원문은 가상 스레드가 약속한 것을 "익숙한 동기·블로킹 코드를 그대로 쓰면서 리액티브 수준의 확장성"이라 적는다.

> **블로킹(blocking) / 동기** — 결과가 나올 때까지 그 자리에서 기다리는 방식. 원문이 블로킹 작업의 예로 든 것이 "소켓 I/O, `sleep` 등"이다.\
> 예: 원문이 아래 코드 주석에 적어 둔 것이 "블로킹해도 OS 스레드를 점유하지 않음"이고, 그 줄이 `Thread.sleep(Duration.ofSeconds(1));`이다.

## 주요 추가 기능

### 가상 스레드 (JEP 425, Preview/1차 프리뷰) ⭐
- **OS 스레드에 1:1로 묶이지 않는 경량 스레드**. JVM이 다수의 가상 스레드를 소수의 플랫폼(OS) 스레드(캐리어 스레드) 위에 다중화(M:N)한다.
- 가상 스레드가 **대부분의 JDK 블로킹 작업(소켓 I/O, `sleep` 등)**에 진입하면, JVM이 해당 가상 스레드를 캐리어에서 **언마운트(unmount)**하고 다른 가상 스레드를 올린다. 따라서 수십만~수백만 개의 가상 스레드를 만들어도 OS 스레드는 적게 유지된다. 단 `synchronized` 블록·`Object.wait()`·일부 파일시스템 작업·네이티브 호출에서는 언마운트되지 못하고 캐리어에 **고정(pinning)**되어 OS 스레드를 점유할 수 있다.
- 핵심 가치: 동기·블로킹 스타일의 단순한 코드를 그대로 쓰면서도 높은 처리량을 얻는다. 리액티브의 복잡성 없이 확장성을 확보한다.
- `Thread`/`ExecutorService` 등 기존 API와 호환된다. 가상 스레드는 항상 데몬이며 우선순위 설정이 무시되는 등 일부 의미 차이가 있다.

아래 그림은 위 둘째 불릿이 나눈 두 갈래를 두 칸에 놓은 것이다.

```text
[원문 둘째 불릿이 「단」으로 나눈 두 갈래]

(가) 언마운트되는 쪽                        (나) 고정(pinning)되는 쪽

  어디서                                    어디서
    "대부분의 JDK 블로킹 작업               "synchronized 블록·Object.wait()
     (소켓 I/O, sleep 등)"                   ·일부 파일시스템 작업·네이티브 호출"

  무슨 일이                                 무슨 일이
    "JVM이 해당 가상 스레드를 캐리어에서    "언마운트되지 못하고 캐리어에
     언마운트(unmount)하고                    고정(pinning)되어
     다른 가상 스레드를 올린다"               OS 스레드를 점유할 수 있다"

  그래서
    "수십만~수백만 개의 가상 스레드를
     만들어도 OS 스레드는 적게 유지된다"
```

- 두 칸의 대립축은 원문이 둘째 불릿에서 "단"으로 갈라 세운 것 그대로다 — 왼쪽이 그 앞, 오른쪽이 "단" 뒤다.
- 따옴표 안의 글자는 전부 원문 문장이다. 「(가)」·「(나)」와 「어디서」·「무슨 일이」·「그래서」는 배치를 위해 재서술자가 붙인 이름표이고, 원문에는 없다. 왼쪽 아래 "그래서" 칸은 원문이 (가) 뒤에 "따라서"로 이어 적은 문장이다.
- 이 그림에 화살표가 없는 것은 두 갈래가 순서로 이어지는 것이 아니라, 원문이 "단"으로 갈라 병렬해 적은 둘이기 때문이다.

> **캐리어 스레드 / 다중화(M:N)** — 가상 스레드를 실제로 올려 돌리는 플랫폼(OS) 스레드 / 다수의 가상 스레드를 소수의 캐리어 위에 나눠 얹는 방식.\
> 예: 원문 표현으로 "JVM이 다수의 가상 스레드를 소수의 플랫폼(OS) 스레드(캐리어 스레드) 위에 다중화(M:N)한다".

> **언마운트(unmount) / 고정(pinning)** — 기다리는 동안 캐리어에서 내려오는 것 / 내려오지 못하고 캐리어를 붙든 채 있는 것. 원문은 둘째 불릿에서 어느 자리가 어느 쪽인지 나눠 적는다.\
> 예: 원문이 고정되는 자리로 든 넷이 `synchronized` 블록·`Object.wait()`·일부 파일시스템 작업·네이티브 호출이다.

```java
// --enable-preview 필요 (JDK 19)
// 1) 가상 스레드 하나 실행
Thread vt = Thread.ofVirtual().start(() ->
        System.out.println("Hello from " + Thread.currentThread()));
vt.join();

// 2) 가상 스레드 기반 ExecutorService — 요청마다 스레드 하나
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 10_000).forEach(i ->
        executor.submit(() -> {
            Thread.sleep(Duration.ofSeconds(1)); // 블로킹해도 OS 스레드를 점유하지 않음
            return i;
        }));
} // close()가 모든 작업 완료를 대기
```

> 가상 스레드는 19·20에서 프리뷰를 거쳐 **Java 21(JEP 444)에서 정식**이 된다. 이것이 Java 21을 "현대 Java의 분기점"으로 만든 핵심 기능이다.

### 구조적 동시성 (JEP 428, Incubator/1차 인큐베이터)
- 여러 스레드에서 실행되는 연관 작업들을 **하나의 작업 단위로 묶어** 다루는 API다(`jdk.incubator.concurrent`의 `StructuredTaskScope`).
- 부모-자식 작업의 생명주기가 코드 블록 구조와 일치하도록 강제하여, 오류 전파·취소·관찰성을 단순화한다. "한 작업이 실패하면 형제 작업을 자동 취소", "모두 끝날 때까지 대기" 같은 패턴을 안전하게 표현한다.
- 가상 스레드와 결합할 때 진가를 발휘한다 (작업마다 가상 스레드를 자유롭게 생성 가능).

> **`StructuredTaskScope`** — 원문 표현으로 연관 작업들을 "하나의 작업 단위로 묶어" 다루는 인큐베이터 API의 클래스. 이 편에서는 `jdk.incubator.concurrent`에 있다.\
> 예: 아래 코드에서 원문이 두 호출에 단 주석이 "두 작업 완료 대기"(`scope.join()`)와 "하나라도 실패하면 예외 전파"(`scope.throwIfFailed()`)다.

```java
// 인큐베이터 API (JDK 19)
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Future<String> user  = scope.fork(() -> findUser());
    Future<Integer> order = scope.fork(() -> fetchOrder());

    scope.join();            // 두 작업 완료 대기
    scope.throwIfFailed();   // 하나라도 실패하면 예외 전파

    return new Response(user.resultNow(), order.resultNow());
}
```

### 레코드 패턴 (JEP 405, Preview/1차 프리뷰)
- 패턴 매칭에서 **레코드 값을 분해(deconstruct)**할 수 있게 한다. `instanceof`와 `switch` 모두에서 사용 가능하다.
- **중첩(nesting)**이 가능해, 복잡한 객체 구조를 한 번에 풀어낼 수 있다.
- Java 21(JEP 440)에서 정식화된다.

> **분해(deconstruct) / 중첩(nesting)** — 레코드 안의 값들을 꺼내 변수로 받는 것 / 그 패턴 안에 또 패턴을 넣는 것.\
> 예: 아래 코드의 `Line(Point(var x1, var y1), Point(var x2, var y2))`가 그것이고, 원문이 단 주석이 "중첩 레코드 패턴으로 한 번에 분해"다.

```java
record Point(int x, int y) {}
record Line(Point from, Point to) {}

static String describe(Object obj) {
    // 중첩 레코드 패턴으로 한 번에 분해
    if (obj instanceof Line(Point(var x1, var y1), Point(var x2, var y2))) {
        return "(%d,%d) -> (%d,%d)".formatted(x1, y1, x2, y2);
    }
    return "unknown";
}
```

### Foreign Function & Memory API (JEP 424, Preview/1차 프리뷰)
- 18까지 인큐베이터(`jdk.incubator.foreign`)였던 API가 **정식 패키지 `java.lang.foreign`의 프리뷰**로 승격되었다.
- JNI 없이 네이티브 함수를 호출하고(다운콜/업콜), JVM 힙 밖 메모리를 안전하게 다룬다. `Linker`, `MethodHandle`, `MemorySegment`, `MemorySession` 등을 제공한다.

> **다운콜 / 업콜** — 원문이 "JNI 없이 네이티브 함수를 호출하고(다운콜/업콜)"이라며 괄호로 이름만 든 둘이다. **그 뜻은 원문에 없다** — 이 편에서는 이름만 기억해 두면 된다.\
> 예: 패키지 이름이 이 편에서 `jdk.incubator.foreign`에서 `java.lang.foreign`으로 옮겨 갔다 — 다만 상태는 아직 프리뷰다.

### Pattern Matching for switch (JEP 427, Third Preview/3차 프리뷰)
- 18의 2차 프리뷰(JEP 420)에 이은 **3차 프리뷰**. 가장 눈에 띄는 변화는 가드 조건을 `&&`가 아니라 **`when` 키워드**로 표현하게 바뀐 점이다.
- `null` 케이스 처리와 패턴 지배 규칙도 더 정련되었다. 정식화는 Java 21(JEP 441).

> **가드(guard) / `when`** — 타입이 맞은 뒤 조건을 하나 더 걸어 거르는 것 / 이 편에서 그 조건을 적게 된 키워드. 17·18 시대의 표기는 `&&`였다(출처: 원문 `java-17.md`·`java-18.md`).\
> 예: 아래 코드의 `case Integer i when i > 100`이고, 원문이 코드 첫 줄 주석에 적어 둔 것이 "3차 프리뷰: when 절 도입"이다.

```java
// 3차 프리뷰: when 절 도입
static String classify(Object obj) {
    return switch (obj) {
        case Integer i when i > 100 -> "큰 수";
        case Integer i              -> "정수 " + i;
        case String s               -> "문자열 " + s;
        default                     -> "기타";
    };
}
```

### Vector API (JEP 426, Fourth Incubator/4차 인큐베이터)
- SIMD 벡터 연산 API의 **네 번째 인큐베이터**. Project Panama의 다른 기능들과 보조를 맞춰 계속 다듬어졌다.

## 그 외 변경
- **JEP 422: Linux/RISC-V 포트** — JDK를 RISC-V(RV64GV) 아키텍처의 Linux로 포팅했다. 벡터 명령을 포함한 범용 64비트 ISA 지원으로, 오픈 하드웨어 생태계로의 확장을 의미한다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 불릿은 원문의 것이다.)*

Java 19는 **"Loom의 시대"를 연 릴리스**로 기억된다.
- 가상 스레드(JEP 425)는 Java가 고동시성 워크로드를 다루는 방식을 근본적으로 바꿀 잠재력을 처음으로 손에 잡히게 보여줬다. 이후 21에서 정식화되며 Spring Boot 등 주요 프레임워크가 빠르게 채택했다.
- 구조적 동시성과 레코드 패턴은 각각 "동시성 코드의 구조화"와 "데이터 중심 프로그래밍"이라는 방향을 명확히 했다.
- FFM API의 프리뷰 승격은 JNI 시대의 종말을 예고했다.

이 모든 것이 아직 프리뷰/인큐베이터였기에 운영 환경에 바로 쓰긴 어려웠지만, Java 19는 Java 21 LTS가 담을 청사진을 거의 그대로 드러낸 릴리스였다.

## 용어 풀이

- **프리뷰(preview) / 인큐베이터(incubator)** — 정식이 아닌 채로 먼저 실어 보내는 단계 표기. 이 편의 기능은 원문 표현으로 "이 모든 것이 아직 프리뷰/인큐베이터였"다.
- **리액티브 프로그래밍** — 원문이 이 편의 대비 상대로 든 스타일. 원문이 든 구현체가 WebFlux·RxJava·Reactor이고, 약점으로 든 것이 "코드가 복잡하고 디버깅·스택트레이스가 어려웠다"이다.
- **블로킹(blocking) / 동기** — 결과가 나올 때까지 그 자리에서 기다리는 방식. 원문이 블로킹 작업의 예로 든 것이 "소켓 I/O, `sleep` 등"이다.
- **가상 스레드** — 원문 표현으로 "OS 스레드에 1:1로 묶이지 않는 경량 스레드". 이 편에서는 1차 프리뷰이고, 정식은 21(JEP 444)이다.
- **캐리어 스레드 / 다중화(M:N)** — 가상 스레드를 실제로 올려 돌리는 플랫폼(OS) 스레드 / 다수의 가상 스레드를 소수의 캐리어 위에 나눠 얹는 방식.
- **언마운트(unmount) / 고정(pinning)** — 기다리는 동안 캐리어에서 내려오는 것 / 내려오지 못하고 캐리어를 붙든 채 있는 것. 원문이 고정되는 자리로 든 넷이 `synchronized` 블록·`Object.wait()`·일부 파일시스템 작업·네이티브 호출이다.
- **`StructuredTaskScope`** — 연관 작업들을 원문 표현으로 "하나의 작업 단위로 묶어" 다루는 API의 클래스. 이 편에서는 `jdk.incubator.concurrent`에 있는 인큐베이터 API다.
- **분해(deconstruct) / 중첩(nesting)** — 레코드 안의 값들을 꺼내 변수로 받는 것 / 그 패턴 안에 또 패턴을 넣는 것. 원문 주석으로 "중첩 레코드 패턴으로 한 번에 분해"다.
- **다운콜 / 업콜** — 원문이 괄호로 이름만 든 둘이다. 그 뜻은 원문에 없다.
- **JNI** — 원문이 FFM API의 대비 상대로 드는 기존 방식. 원문 표현으로 "JNI 없이 네이티브 함수를 호출하고".
- **가드(guard) / `when`** — 타입이 맞은 뒤 조건을 하나 더 걸어 거르는 것 / 이 편에서 그 조건을 적게 된 키워드. 원문은 이 변화를 "`&&`가 아니라 **`when` 키워드**로 표현하게 바뀐 점"이라 적는다.
- **SIMD** — 하나의 명령으로 여러 값을 한꺼번에 처리하는 CPU 기능. Vector API가 이 편에서 4차 인큐베이터다.

## 참고 출처
- [JEP 425: Virtual Threads (Preview)](https://openjdk.org/jeps/425)
- [JEP 428: Structured Concurrency (Incubator)](https://openjdk.org/jeps/428)
- [JEP 405: Record Patterns (Preview)](https://openjdk.org/jeps/405)
- [JEP 424: Foreign Function & Memory API (Preview)](https://openjdk.org/jeps/424)
- [JEP 427: Pattern Matching for switch (Third Preview)](https://openjdk.org/jeps/427)
- [JEP 426: Vector API (Fourth Incubator)](https://openjdk.org/jeps/426)
- [JEP 422: Linux/RISC-V Port](https://openjdk.org/jeps/422)
- [OpenJDK JDK 19 프로젝트 페이지](https://openjdk.org/projects/jdk/19/)
- [InfoQ: Java 19 Delivers Features for Projects Loom, Panama and Amber](https://www.infoq.com/news/2022/09/java19-released/)
