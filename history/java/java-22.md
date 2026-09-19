# Java 22 (2024.03)

> 원본: `~/project/java-history/java/java-22.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JEP 번호·클래스/메서드 이름·자바 코드블록 5개와 셸 코드블록 1개·「릴리스 정보」의 JEP 목록·「참고 출처」는 원문 그대로다.\
> 도식은 넣지 않았다 — 원문에 도식이 없고, 원문이 절차로 서술한 메커니즘도 없다.\
> 「한눈에」의 창고 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.\
> 「이 편의 기능은 지금 어디쯤인가」 표의 「그 뒤」 칸은 같은 시리즈의 다른 편(`java-23.md`~`java-26.md`)에서 끌어온 보충이고, 출처 편을 칸마다 적었다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 외부 함수 & 메모리 API와 미명명 변수/패턴을 정식화하고, 스트림 Gatherers·생성자 본문 유연화 등 차세대 기능을 대거 프리뷰로 선보인 비-LTS 릴리스.

이 편의 주인공 하나를 비유로 읽으면 **집 밖 창고의 물건을 쓰려고 벽에 구멍을 뚫던 방식에서, 제대로 단 문으로 드나들게 된 일**이다.\
**FFM API도 똑같은 구조다** — 원문 자신이 이 절에서 그 자리를 이렇게 적는다: "자바 코드가 JVM 밖의 네이티브 메모리에 접근하고 네이티브 함수를 직접 호출할 수 있게 하는 API. … 깨지기 쉽고 위험한 JNI를 대체한다."

본문 흐름에 쓰는 비유는 이 창고 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 집 안 | JVM 안 — 원문이 바깥을 "JVM 밖의 네이티브 메모리"라 부르니 그 반대쪽이다 |
| 집 밖 창고 | 원문 표현으로 "네이티브 메모리"와 "네이티브 함수" |
| 벽에 뚫어 둔 구멍 | JNI — 원문 표현으로 "깨지기 쉽고 위험한 JNI" |
| 제대로 단 문 | FFM API — 원문 표현으로 "안전한 네이티브 상호운용 수단이 표준 라이브러리에 자리 잡았다" |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **이 편에 실렸다고 다 쓸 수 있는 기능이 아니다.** 원문의 JEP 목록 12개 가운데 "(정식)"이 붙은 것은 넷(JEP 423·454·456·458)뿐이고, 나머지는 프리뷰·인큐베이터다.
- **프리뷰는 반드시 정식이 되는 계단이 아니다.** 이 편의 String Templates가 그 반례이고, 원문이 그 자리에 직접 적어 둔 말이 "이 기능은 설계상의 문제로 Java 23에서 프리뷰에서도 제거되어 재설계에 들어갔다"이다.

### 이 편의 기능은 지금 어디쯤인가

왼쪽 두 칸은 이 편 원문이 적은 것이고, 오른쪽 칸은 그 편들의 원문에서 확인한 보충이다.

| 기능 | 이 편(22)에서의 상태 | 그 뒤 |
|---|---|---|
| Foreign Function & Memory API (JEP 454) | **정식** | — (이 편이 도착점. 원문 표현으로 "JDK 14부터 여러 차례 인큐베이터/프리뷰를 거쳐 이 버전에서 정식화되었다") |
| Unnamed Variables & Patterns (JEP 456) | **정식** | — (`java-21.md`의 JEP 443 1차 프리뷰가 앞자리다) |
| Launch Multi-File Source-Code Programs (JEP 458) | **정식** | — |
| Region Pinning for G1 (JEP 423) | **정식** | — |
| Stream Gatherers (JEP 461) | 프리뷰 | `java-23.md` 2차 프리뷰(JEP 473) → `java-24.md` **정식**(JEP 485) |
| Statements before super(...) (JEP 447) | 프리뷰 | `java-23.md`에서 이름이 "Flexible Constructor Bodies"로 바뀌어 2차 프리뷰(JEP 482) → `java-24.md` 3차(JEP 492) → `java-25.md` **정식**(JEP 513) |
| Class-File API (JEP 457) | 프리뷰 | `java-23.md` 2차 프리뷰(JEP 466) → `java-24.md` **정식**(JEP 484) |
| String Templates (JEP 459) | 2차 프리뷰 | `java-23.md`에서 **철회** — 정식이 된 적이 없다 |
| Structured Concurrency (JEP 462) | 2차 프리뷰 | `java-26.md`의 6차 프리뷰(JEP 525)까지도 **정식이 아니다** |
| Scoped Values (JEP 464) | 2차 프리뷰 | `java-25.md` **정식**(JEP 506) |
| Implicitly Declared Classes and Instance Main Methods (JEP 463) | 2차 프리뷰 | `java-25.md`에서 "Compact Source Files and Instance Main Methods"로 **정식**(JEP 512) |
| Vector API (JEP 460) | 7차 인큐베이터 | `java-26.md`의 11차 인큐베이터(JEP 529)까지도 **정식이 아니다** |

## 릴리스 정보
- 정식 출시일: 2024년 3월 19일
- LTS 여부: 아니오 (단기 지원, 6개월 주기 / Java 23으로 대체)
- 포함 JEP 목록 (총 12개):
  - JEP 423: Region Pinning for G1 (정식)
  - JEP 447: Statements before super(...) (프리뷰)
  - JEP 454: Foreign Function & Memory API (정식)
  - JEP 456: Unnamed Variables & Patterns (정식)
  - JEP 457: Class-File API (프리뷰)
  - JEP 458: Launch Multi-File Source-Code Programs (정식)
  - JEP 459: String Templates (2차 프리뷰)
  - JEP 460: Vector API (7차 인큐베이터)
  - JEP 461: Stream Gatherers (프리뷰)
  - JEP 462: Structured Concurrency (2차 프리뷰)
  - JEP 463: Implicitly Declared Classes and Instance Main Methods (2차 프리뷰)
  - JEP 464: Scoped Values (2차 프리뷰)

> **비-LTS(단기 지원)** — 다음 릴리스가 나오면 지원이 끝나는 버전. 원문이 괄호에 적은 그대로 "6개월 주기 / Java 23으로 대체"된다.\
> 예: 원문이 이 편을 "Java 21(2023.09, LTS) 직후의 첫 비-LTS 릴리스"로 자리매김한다.

## 시대적 배경

Java 21(2023.09, LTS) 직후의 첫 비-LTS 릴리스로, LTS에서 정식화된 기반 위에 차세대 프로젝트들의 결과물을 쏟아낸 버전이다.\
특히 **Project Panama**의 핵심 산출물인 외부 함수 & 메모리(FFM) API가 수년간의 인큐베이팅/프리뷰를 거쳐 마침내 정식화되어, JNI를 대체할 안전한 네이티브 상호운용 수단이 표준 라이브러리에 자리 잡았다.\
동시에 **Project Loom**(구조적 동시성, 스코프드 값), **Project Amber**(미명명 변수/패턴, 문자열 템플릿, 암시적 클래스) 등 여러 프로젝트가 병렬로 성숙해 가는 모습을 보여주었다.

> **네이티브(native) 함수·메모리** — JVM이 관리하는 영역 바깥, 운영체제와 C 같은 언어가 쓰는 쪽. 원문 표현으로 "JVM 밖의 네이티브 메모리"다.\
> 예: 아래 FFM 코드가 불러 쓰는 것이 원문 주석대로 "C 표준 라이브러리의 strlen 함수"다.

> **JNI** — FFM 이전에 네이티브 쪽을 부르던 수단. 원문이 붙인 평가가 "깨지기 쉽고 위험한"이다.\
> 예: 원문은 FFM 정식화가 "향후 JNI 사용 제한(JDK 24의 JEP 472)으로 이어지는 출발점"이 됐다고 적는다.

## 주요 추가 기능

### Foreign Function & Memory API (JEP 454, 정식)
- 자바 코드가 JVM 밖의 네이티브 메모리에 접근하고 네이티브 함수를 직접 호출할 수 있게 하는 API. JDK 14부터 여러 차례 인큐베이터/프리뷰를 거쳐 이 버전에서 정식화되었다. 깨지기 쉽고 위험한 JNI를 대체한다.
- `MemorySegment`, `Arena`, `Linker`, `FunctionDescriptor` 등으로 구성된다.

```java
import java.lang.foreign.*;
import java.lang.invoke.MethodHandle;

try (Arena arena = Arena.ofConfined()) {
    // C 표준 라이브러리의 strlen 함수에 대한 핸들 확보
    Linker linker = Linker.nativeLinker();
    MethodHandle strlen = linker.downcallHandle(
        linker.defaultLookup().find("strlen").orElseThrow(),
        FunctionDescriptor.of(ValueLayout.JAVA_LONG, ValueLayout.ADDRESS));

    MemorySegment str = arena.allocateUtf8String("Hello FFM");
    long len = (long) strlen.invoke(str);
    System.out.println(len); // 9
}
```

원문이 "구성된다"며 이름만 든 넷이 위 코드에 그대로 나온다 — `Arena`, `Linker`, `FunctionDescriptor`, `MemorySegment`다. 각각이 무엇을 맡는지는 원문이 적지 않으므로 여기서도 풀지 않는다.\
"JDK 14부터"라는 원문의 출발점도 같은 시리즈에서 확인된다 — `java-14.md`가 JEP 370을 "Foreign-Memory Access API … incubator로 시작"으로 적고, `java-17.md`가 JEP 412를 두 갈래를 합친 incubator로, `java-19.md`가 JEP 424를 "정식 패키지 `java.lang.foreign`의 프리뷰"로 적는다.

### Unnamed Variables & Patterns (JEP 456, 정식)
- 사용하지 않는 변수나 패턴 컴포넌트를 밑줄(`_`)로 표기해 의도를 명확히 한다. 예외 변수, 람다 파라미터, for 루프 변수, 패턴 매칭 등에서 사용한다.

> **미명명(unnamed) 변수·패턴** — 값은 받지만 이름을 붙이지 않겠다고 `_` 한 글자로 밝히는 것. 원문 표현으로 "의도를 명확히 한다".\
> 예: 아래 코드의 `catch (NumberFormatException _)`가 예외 변수 쪽이고, `Point(int x, _)`가 패턴 컴포넌트 쪽이다. 원문이 쓰이는 자리로 든 넷이 "예외 변수, 람다 파라미터, for 루프 변수, 패턴 매칭"이다.

```java
// 사용하지 않는 예외 변수
try {
    int n = Integer.parseInt(s);
} catch (NumberFormatException _) {
    System.out.println("숫자가 아님");
}

// 레코드 패턴에서 일부 컴포넌트 무시
record Point(int x, int y) {}
if (obj instanceof Point(int x, _)) {
    System.out.println(x);
}
```

### Launch Multi-File Source-Code Programs (JEP 458, 정식)
- 단일 파일 소스 실행(JDK 11)을 확장하여, 컴파일 없이 여러 소스 파일로 구성된 프로그램을 `java` 명령으로 바로 실행할 수 있다.

```bash
# Main.java가 같은 디렉터리의 Helper.java를 참조해도 바로 실행 가능
java Main.java
```

> **단일 파일 소스 실행** — `.java` 파일을 따로 컴파일하지 않고 `java` 명령에 바로 넘겨 돌리는 기능. 원문은 그 출발점을 JDK 11로 적고, 이 편이 그것을 여러 파일로 "확장"했다고 적는다.\
> 예: 원문 주석이 든 상황이 "Main.java가 같은 디렉터리의 Helper.java를 참조"하는 경우다.

### Stream Gatherers (JEP 461, 프리뷰)
- Stream API에 사용자 정의 **중간 연산**을 만들 수 있는 `Stream.gather(Gatherer)`를 추가한다. 기존에 부족했던 윈도잉, 폴드, 커스텀 변환 등을 표현할 수 있다.

> **중간 연산** — 스트림을 받아 스트림을 돌려주는, 결과를 내기 전 단계의 연산. 이 편이 더한 것은 그런 연산을 **직접 만들 수 있게** 하는 길이다.\
> 예: 아래 코드의 `.gather(Gatherers.windowFixed(2))`가 그 자리이고, 원문이 그 예에 붙인 주석이 "고정 크기 윈도우로 묶기 (built-in gatherer)"다.

```java
// 고정 크기 윈도우로 묶기 (built-in gatherer)
List<List<Integer>> windows = Stream.of(1, 2, 3, 4, 5)
    .gather(Gatherers.windowFixed(2))
    .toList(); // [[1, 2], [3, 4], [5]]
```

위 코드의 결과가 원문 주석대로 `[[1, 2], [3, 4], [5]]`인 점을 눈여겨볼 만하다 — 다섯 개를 둘씩 묶으니 마지막 묶음은 하나뿐이다.

### Statements before super(...) (JEP 447, 프리뷰)
- 생성자에서 `super(...)`/`this(...)` 호출 **이전에** 인자 검증·준비 등의 문장을 작성할 수 있게 한다(단, 생성 중인 인스턴스 참조는 불가).

```java
class PositiveBigInteger extends BigInteger {
    PositiveBigInteger(long value) {
        if (value <= 0)                         // super() 호출 전 검증
            throw new IllegalArgumentException("양수여야 함");
        super(Long.toString(value));
    }
}
```

위 코드에서 원문이 말한 "이전에"가 눈에 보인다 — `super(Long.toString(value));`보다 위에 `if (value <= 0)` 검증이 놓여 있고, 원문이 그 줄에 붙인 주석이 "super() 호출 전 검증"이다.\
원문이 괄호로 달아 둔 제한도 함께 읽어야 한다 — "단, 생성 중인 인스턴스 참조는 불가".

### Class-File API (JEP 457, 프리뷰)
- 클래스 파일을 파싱·생성·변환하기 위한 표준 API를 도입한다. 기존에 JDK 내부적으로 의존하던 ASM 같은 외부 라이브러리를 대체할 표준 수단을 제공한다.

> **클래스 파일 / ASM** — 자바 소스를 컴파일한 결과물(`.class`) / 그 파일을 다루려고 JDK가 내부적으로 써 오던 외부 라이브러리. 원문 표현으로 "JDK 내부적으로 의존하던 ASM 같은 외부 라이브러리"다.\
> 예: 원문이 이 API로 할 수 있다고 든 세 가지가 "파싱·생성·변환"이다.

### String Templates (JEP 459, 2차 프리뷰)
- 문자열 보간을 안전하게 수행하는 기능의 2차 프리뷰. (참고: 이 기능은 설계상의 문제로 Java 23에서 프리뷰에서도 제거되어 재설계에 들어갔다.)

```java
// 2차 프리뷰 당시 문법 (이후 폐기됨)
String name = "Java";
String msg = STR."Hello \{name}, version \{22}";
```

원문이 코드 첫 줄 주석에 "이후 폐기됨"이라 못 박아 둔 그대로다.\
1차 프리뷰가 어느 편이었는지도 같은 시리즈에서 확인된다 — `java-21.md`의 JEP 430이다. 즉 이 기능은 21·22 두 편에만 프리뷰로 존재했고 **정식이 된 적이 없다.**

## 그 외 변경
- **Structured Concurrency (JEP 462, 2차 프리뷰)** / **Scoped Values (JEP 464, 2차 프리뷰)**: Project Loom의 동시성 모델을 계속 다듬는다.
- **Implicitly Declared Classes and Instance Main Methods (JEP 463, 2차 프리뷰)**: 초보자 친화적인 간소화된 `main` 진입점.
- **Vector API (JEP 460, 7차 인큐베이터)**: SIMD 벡터 연산 API 계속 인큐베이팅.
- **Region Pinning for G1 (JEP 423, 정식)**: JNI 임계 영역(critical region) 동안에도 G1 GC가 멈추지 않도록 영역 단위 고정을 도입해 지연을 줄인다.

> **임계 영역(critical region)** — 그 구간이 도는 동안에는 건드리면 안 되는 자리. 원문은 이것을 JNI 쪽에 딸린 것으로 적는다.\
> 예: 원문이 이 JEP의 효과로 적은 것이 "동안에도 G1 GC가 멈추지 않도록 영역 단위 고정을 도입해 지연을 줄인다"이다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 두 문단은 원문의 것이다.)*

FFM API의 정식화는 자바 생태계에서 오랜 숙원이던 안전한 네이티브 상호운용의 표준화를 의미하며, 향후 JNI 사용 제한(JDK 24의 JEP 472)으로 이어지는 출발점이 되었다.

또한 Stream Gatherers(Java 24에서 정식화), 생성자 본문 유연화(Java 25에서 정식화) 등 이후 정식화될 기능들이 본격적으로 모습을 드러낸 릴리스로, "Java 25 LTS로 가는 길목"의 성격이 강하다.

## 용어 풀이

- **비-LTS(단기 지원)** — 다음 릴리스가 나오면 지원이 끝나는 버전. 원문은 이 편을 "6개월 주기 / Java 23으로 대체"된다고 적는다.
- **네이티브(native) 함수·메모리** — JVM이 관리하는 영역 바깥, 운영체제와 C 같은 언어가 쓰는 쪽. 원문 표현으로 "JVM 밖의 네이티브 메모리"다.
- **JNI** — FFM 이전에 네이티브 쪽을 부르던 수단. 원문이 붙인 평가가 "깨지기 쉽고 위험한"이고, 원문은 이 편을 "JNI 사용 제한(JDK 24의 JEP 472)으로 이어지는 출발점"으로 적는다.
- **미명명(unnamed) 변수·패턴** — 값은 받되 이름을 붙이지 않겠다고 `_` 한 글자로 밝히는 것. 원문이 쓰이는 자리로 든 넷이 "예외 변수, 람다 파라미터, for 루프 변수, 패턴 매칭"이다.
- **단일 파일 소스 실행** — `.java` 파일을 따로 컴파일하지 않고 `java` 명령에 바로 넘겨 돌리는 기능. 원문은 출발점을 JDK 11로 적는다.
- **중간 연산** — 스트림을 받아 스트림을 돌려주는, 결과를 내기 전 단계의 연산. 이 편이 더한 것은 그것을 직접 만들 수 있게 하는 `Stream.gather(Gatherer)`다.
- **클래스 파일 / ASM** — 자바 소스를 컴파일한 결과물 / 그 파일을 다루려고 JDK가 내부적으로 써 오던 외부 라이브러리.
- **임계 영역(critical region)** — 그 구간이 도는 동안에는 건드리면 안 되는 자리. 원문은 JNI 쪽에 딸린 것으로 적는다.
- **보간(interpolation)** — 문자열 안에 값이 들어갈 자리를 뚫어 두고 실행할 때 채우는 것. 이 편의 String Templates는 2차 프리뷰였고 이후 철회됐다.

## 참고 출처
- [JDK 22 - OpenJDK 프로젝트 페이지](https://openjdk.org/projects/jdk/22/)
- [Oracle Releases Java 22](https://www.oracle.com/news/announcement/oracle-releases-java-22-2024-03-19/)
- [The Arrival of Java 22! – Inside.java](https://inside.java/2024/03/19/the-arrival-of-java-22/)
- [Consolidated JDK 22 Release Notes](https://www.oracle.com/java/technologies/javase/22all-relnotes.html)
- [Java version history - Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
