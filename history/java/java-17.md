# Java 17 (2021년 9월) — LTS

> 원본: `~/project/java-history/java/java-17.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JEP 번호·클래스/옵션 이름·코드블록 4개(java 4)·「릴리스 정보」와 「그 외 변경」·「지원 중단(deprecation)·제거」의 목록은 원문 그대로다.\
> ASCII 도식 2개(원문 mermaid 그림 2개를 글자로 옮긴 것이다)와 「한눈에」의 합류 비유와 대응표, 「이 편에서 미리보기인가 정식인가」 표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> Java 11 이후 3년 만의 LTS. 여러 버전에 걸쳐 다듬어 온 모던 문법(record·sealed·패턴 매칭)을 한데 모아 안정적으로 제공하는, 사실상 "모던 Java의 새 기준점" 릴리스.

이 편을 읽는 비유는 **여러 갈래로 흐르던 물줄기가 한 곳에서 합류하는 지점**이다.\
원문이 「시대적 배경」에서 그 합류를 이렇게 적는다 — "6개월 주기 릴리스(12~16)가 차곡차곡 쌓아 올린 언어 기능들이 17에서 정식 형태로 수렴했다는 점이 핵심이다."

| 비유 | 실체 |
|---|---|
| 합류해 들어온 물줄기들 | 원문이 괄호로 편을 적어 든 다섯 — "switch 표현식(14), 텍스트 블록(15), record(16), instanceof 패턴 매칭(16), sealed 클래스(17)" |
| 합류 지점 | Java 17 — 원문 표현으로 "모던 Java의 핵심 문법 대부분이 17 시점에 정식 기능으로 완비됐다" |
| 아직 합류하지 않고 옆으로 흐르는 물줄기 | switch 패턴 매칭 — 이 편에서는 preview이고, 원문 표현으로 "정식화는 Java 21의 JEP 441에서 이뤄진다" |

### 이 편에서 미리보기인가 정식인가

**이 편에서 흔한 오해는 "17은 LTS니까 여기 적힌 것이 전부 정식이다"이다.**\
sealed는 여기서 정식이 되지만 **switch 패턴 매칭은 이 편에서 preview**이고, FFM API와 Vector API는 incubator다.\
원문이 절 제목·불릿에 적어 둔 상태를 한자리에 모으면 이렇다.

| 기능 | 이 편(17)에서의 상태 — 원문 절 제목·불릿 표기(★는 원문 표기가 아니라 재서술자 추론이거나 다른 편 원문에서 온 것) | 정식이 된 편 |
|---|---|---|
| sealed 클래스 (JEP 409) | **정식화** | 17 — 이 편이다 (15 1차, 16 2차 preview를 거쳤다) |
| switch 패턴 매칭 (JEP 406) | **preview** ★(1차) — 차수 「1차」는 이 편 원문에 없다. 원문 `java-18.md`의 "Java 17의 1차 프리뷰(JEP 406)"에서 왔다 | 21 (JEP 441) — 원문이 "정식화는 Java 21의 JEP 441에서 이뤄진다"고 직접 적는다 |
| 새 의사난수 생성기 API (JEP 356) | **정식** | 17 — 이 편이다 |
| 강한 캡슐화의 완성 (JEP 403) | ★정식 정책 변경(원문 절 제목에 상태 표기가 없다 — 재서술자 추론) | 17 — 이 편이다 (16의 JEP 396에 이은 단계다) |
| macOS/AArch64 포트 (JEP 391) | ★정식(원문 절 제목에 상태 표기가 없다 — 재서술자 추론) | 17 — 이 편이다 |
| 새 macOS 렌더링 파이프라인 (JEP 382) | ★추가되되 **기본값 아님**(opt-in) — 원문 절 제목에 상태 표기가 없다. 재서술자가 본문에서 줄인 것이다 | 이 편에서는 원문 표현으로 "기본값은 여전히 OpenGL" |
| Foreign Function & Memory API (JEP 412) | **incubator** | 22 (JEP 454) — 원문이 "Java 22의 JEP 454에서 정식화"라고 직접 적는다 |
| Vector API (JEP 414) | **2차 incubator** | 이 편 뒤로도 incubator가 이어진다 — 출처: 원문 `java-19.md`(4차)·`java-20.md`(5차) |

> **preview(미리보기) / incubator(인큐베이터)** — 정식이 아닌 채로 먼저 실어 보내는 단계 표기. 원문은 이 편에서는 언어 문법 쪽에 preview를, API 쪽에 incubator를 쓴다.\
> 예: 이 편의 switch 패턴 매칭 코드에 원문이 단 주석이 "preview 기능 (--enable-preview 필요)"이다.

> **LTS(Long-Term Support)** — 원문 표현으로 "수년간 장기 지원·보안 패치를 제공하는 기준 버전".\
> 예: 원문이 이 편의 앞뒤로 든 LTS가 "직전 LTS는 Java 11(2018), 다음 LTS는 Java 21(2023)"이다.

## 릴리스 정보
- 정식 출시일: 2021년 9월 14일
- LTS 여부: **예 (Long-Term Support)**. 직전 LTS는 Java 11(2018), 다음 LTS는 Java 21(2023).
- 지원: Oracle 및 주요 벤더가 수년간 장기 지원·보안 패치를 제공하는 기준 버전.

## 시대적 배경

Java 17은 Java 11 이후 3년 만에 등장한 LTS다.\
6개월 주기 릴리스(12~16)가 차곡차곡 쌓아 올린 언어 기능들이 17에서 정식 형태로 수렴했다는 점이 핵심이다.\
switch 표현식(14), 텍스트 블록(15), record(16), instanceof 패턴 매칭(16), sealed 클래스(17)까지 — 모던 Java의 핵심 문법 대부분이 17 시점에 정식 기능으로 완비됐다.

그래서 많은 기업과 프레임워크가 Java 8/11에서 곧장 17로 점프하는 마이그레이션을 택했다.\
Spring Framework 6 / Spring Boot 3가 **Java 17을 최소 요구 버전**으로 채택하면서, 17은 새 시대 엔터프라이즈 Java의 기준선이 됐다.

이 버전은 LTS인 만큼, 새 기능의 양 자체는 많지 않지만 **장기 운영에 필요한 안정성·보안·정리 작업**에 무게를 둔 것이 특징이다.

## 주요 추가 기능

### sealed 클래스 정식화 (JEP 409)

*(「한눈에」의 비유 표에서 "합류 지점"에 해당하는 자리다.)*

15(1차)·16(2차) preview를 거쳐 **정식 기능**으로 확정됐다.\
클래스·인터페이스의 상속/구현 대상을 `permits`로 제한해, 타입 계층을 설계자가 닫힌 집합으로 통제할 수 있다.\
record·패턴 매칭과 결합하면 대수적 데이터 타입(ADT) 스타일을 표현할 수 있다.

상속을 **통째로** 금지하는 장치가 아니다 — **허용 목록 밖만** 막는다(원문이 아래 그림 해설에 적은 그대로다: "허용한 하위 타입(`Circle`·`Rectangle`)만 구현할 수 있어, 타입 집합이 닫혀 있음을 컴파일러가 보장한다"). 원문이 적은 것은 `permits`로 대상을 **제한**해 "닫힌 집합으로 통제"한다는 것이고, 아래 코드의 `Circle`·`Rectangle`은 실제로 `Shape`를 구현한다.

> **sealed / `permits` / 닫힌 집합** — 상속·구현 대상을 제한하겠다는 표시 / 허용 목록을 적는 절 / 그렇게 해서 더 늘지 않게 된 하위 타입의 모임.\
> 예: 아래 코드의 `permits Circle, Rectangle`이 허용 목록이고, 바로 그 둘이 `implements Shape`로 적혀 있다.

```java
public sealed interface Shape
        permits Circle, Rectangle { }

public record Circle(double radius)              implements Shape { }
public record Rectangle(double w, double h)      implements Shape { }
```

봉인 타입의 하위 타입은 다음 셋 중 하나여야 한다:
- `final` — 더 이상 확장 불가
- `sealed` — 다시 제한된 확장 허용
- `non-sealed` — 봉인을 풀어 자유 확장 허용

아래 클래스 다이어그램은 봉인 계층을 표현한다. `Shape`는 `permits`로 허용한 하위 타입(`Circle`·`Rectangle`)만 구현할 수 있어, 타입 집합이 닫혀 있음을 컴파일러가 보장한다.

```text
Shape
  <<sealed interface>>

Shape <|.. Circle     : permits
Shape <|.. Rectangle  : permits

Circle     +double radius
Rectangle  +double w
Rectangle  +double h
```

- 이 그림은 원문의 mermaid `classDiagram`을 글자로 옮긴 것이다 — 관계 줄 둘로 원문의 관계 수와 같고, `<|..`도 엣지 라벨 `permits`도 원문이 적은 글자 그대로다(화살촉은 `Shape` 쪽을 향한다).
- `<<sealed interface>>`와 `+double radius` 같은 칸 안의 글자도 원문 노드에 적힌 것 그대로다.
- 바로 위 문단이 이 그림을 읽는 법이고, 원문의 것이다.

### switch 패턴 매칭 (JEP 406, preview)

switch에서 **타입 패턴**으로 분기할 수 있게 하는 기능이 preview로 등장했다.\
sealed 타입과 결합하면, 컴파일러가 모든 경우를 다뤘는지(exhaustiveness) 검사해줘 안전한 분기를 작성할 수 있다. (정식화는 Java 21의 JEP 441에서 이뤄진다.)

> **타입 패턴 / 전체성(exhaustiveness)** — `case` 자리에 값이 아니라 타입을 적어 맞춰 보는 것 / 그 분기가 가능한 모든 경우를 다뤘는지를 따지는 성질.\
> 예: 아래 코드의 `case Circle c`가 타입 패턴이고, 원문이 주석에 적어 둔 것이 "Shape가 sealed이고 모든 하위 타입을 다뤘다면 default 불필요"다.

```java
// preview 기능 (--enable-preview 필요)
static double area(Shape shape) {
    return switch (shape) {
        case Circle c    -> Math.PI * c.radius() * c.radius();
        case Rectangle r -> r.w() * r.h();
        // Shape가 sealed이고 모든 하위 타입을 다뤘다면 default 불필요
    };
}
```

null 처리와 가드(guarded pattern)도 함께 실험됐다.\
단, 17 시대(JEP 406)의 가드 문법은 `when`이 아니라 `&&`였다.\
`when` 가드는 Java 19(JEP 427)에서 도입돼 Java 21(JEP 441)에서 정식화된다.

> **가드(guarded pattern)** — 타입이 맞은 뒤에 조건을 하나 더 걸어 거르는 것. 이 편의 표기는 `&&`다.\
> 예: 아래 코드의 `case Integer i && i > 10`에 원문이 단 주석이 "가드: 17 시대에는 &&"이다.

```java
static String describe(Object obj) {
    return switch (obj) {
        case null                -> "널";
        case Integer i && i > 10 -> "큰 정수 " + i; // 가드: 17 시대에는 &&
        case Integer i           -> "정수 " + i;
        case String s            -> "문자열 길이 " + s.length();
        default                  -> "기타";
    };
}
```

아래 흐름도는 switch 패턴 매칭이 입력 객체의 런타임 타입에 따라 분기하는 과정을 보여준다. `Shape`가 sealed이면 컴파일러가 모든 하위 타입 처리 여부(exhaustiveness)를 검사한다. 참고로 Java 17 시점(JEP 406)은 preview이며, 가드 조건 문법은 `when`이 아니라 `&&`다(`when` 가드는 Java 19+에서 도입).

```text
"입력 객체 (Shape)"  -->  {"타입 패턴 매칭"}

{"타입 패턴 매칭"}  --|"case Circle c"|-->     "원 넓이: PI * r^2"
{"타입 패턴 매칭"}  --|"case Rectangle r"|-->  "직사각형 넓이: w * h"

"원 넓이: PI * r^2"      -->  "결과 반환"
"직사각형 넓이: w * h"   -->  "결과 반환"
```

- 이 그림은 원문의 mermaid `flowchart TD`를 글자로 옮긴 것이다 — 화살표 다섯으로 원문의 엣지 수와 같고, 방향도 원문과 같다(위에서 아래로).
- 칸 안의 글자와 화살표 위의 라벨(`"case Circle c"` 등)은 원문이 적은 것 그대로이며, `{ }`로 감싼 칸은 원문이 마름모로 그린 분기점이다.
- 바로 위 문단이 이 그림을 읽는 법이고, 원문의 것이다 — 마지막 괄호가 이 편의 가드가 `&&`인 이유를 적어 둔 자리다.

### 새 의사난수 생성기 API (JEP 356, 정식)

`RandomGenerator` 인터페이스를 새로 도입하고, 다양한 PRNG 알고리즘(예: Xoshiro, LXM 계열)을 통합된 API로 제공한다.\
기존 `Random`/`SplittableRandom`/`ThreadLocalRandom`을 이 인터페이스 아래로 통합해, 알고리즘을 이름으로 선택하고 일관되게 사용할 수 있다.\
스트림 기반 생성과 점프(jump)·분할(split) 기능도 표준화했다.

> **PRNG(의사난수 생성기)** — 진짜 무작위가 아니라 계산으로 난수처럼 보이는 값을 만들어 내는 장치. 원문이 알고리즘 예로 든 것이 Xoshiro, LXM 계열이다.\
> 예: 아래 코드가 알고리즘을 이름으로 고르는 모습이다 — `RandomGenerator.of("Xoshiro256PlusPlus")`.

```java
RandomGenerator gen = RandomGenerator.of("Xoshiro256PlusPlus");
int n = gen.nextInt(100);

// 팩토리로 알고리즘 탐색·생성
RandomGeneratorFactory.of("L64X128MixRandom")
        .create()
        .ints(5)
        .forEach(System.out::println);
```

### 강한 캡슐화의 완성 (JEP 403)

16에서 기본값으로 전환했던 JDK 내부 캡슐화를 한 단계 더 밀어붙여, `--illegal-access` 옵션으로 캡슐화를 **풀 수 있는 길 자체를 없앴다**(`sun.misc.Unsafe` 등 일부 중요한 내부 API는 여전히 접근 가능).\
내부 API에 의존하던 코드는 표준 대안으로의 이전이 사실상 강제됐다.

원문이 비용으로 적은 문장은 이 절의 "내부 API에 의존하던 코드는 표준 대안으로의 이전이 사실상 강제됐다"이다.

### macOS/AArch64 포트 (JEP 391)

Apple Silicon(M1 등 AArch64 기반 Mac)을 네이티브로 지원.\
Apple이 자체 칩으로 전환하던 시점에 맞춰 Java가 신속히 대응했다.

### 새 macOS 렌더링 파이프라인 (JEP 382)

Java 2D에 **Apple Metal API** 기반 렌더링 파이프라인을 새로 추가했다.\
다만 17 시점의 기본값은 여전히 OpenGL이며, Metal은 `-Dsun.java2d.metal=true` 옵션으로 켜는 opt-in 대안이다(OpenGL을 곧바로 대체한 것은 아니다).\
Apple OpenGL은 2018년부터 deprecated된 상태였다.

> **opt-in(옵트인)** — 기본으로는 꺼져 있고, 쓰겠다고 켜야 동작하는 방식. 이 절의 Metal 파이프라인이 그렇다.\
> 예: 원문이 켜는 방법으로 적은 것이 `-Dsun.java2d.metal=true` 옵션이다.

## 그 외 변경

- **Foreign Function & Memory API (JEP 412, incubator)**: 16의 외부 메모리(JEP 393)와 외부 링커(JEP 389) API를 하나로 통합한 incubator. 네이티브 코드 호출과 힙 밖 메모리 접근을 JNI보다 안전·간결하게 다룬다. (Java 22의 JEP 454에서 정식화.)
- **Vector API 2차 incubator (JEP 414)**: 16의 1차 incubator(JEP 338)를 개선.
- **항상 엄격한 부동소수점 (JEP 306)**: `strictfp` 의미를 기본으로 되돌려, 모든 플랫폼에서 동일한 부동소수점 결과를 보장.
- **컨텍스트별 역직렬화 필터 (JEP 415)**: 역직렬화 필터를 컨텍스트 단위로 동적 선택·구성해 보안을 강화.

> **JNI(Java Native Interface)** — Java에서 네이티브 코드를 부르는 기존 방식. 원문은 FFM API가 그 일을 "JNI보다 안전·간결하게 다룬다"고 적는다.\
> 예: 이 편에서 FFM API는 아직 incubator이고, 원문이 정식화 시점으로 적어 둔 것이 "Java 22의 JEP 454"다.

### 지원 중단(deprecation)·제거

- **Applet API 지원 중단(제거 예정) (JEP 398)**: 브라우저 플러그인 시대의 유물인 `java.applet.Applet`을 제거 예정으로 표시. 대부분의 브라우저가 이미 플러그인 지원을 끊은 상황을 반영.
- **Security Manager 지원 중단(제거 예정) (JEP 411)**: `SecurityManager`와 관련 API 전반을 제거 예정으로 표시. 25년 가까이 쓰였지만 실제 활용도가 낮고 유지 비용이 컸던 권한 기반 보안 모델을 단계적으로 퇴출하기로 했다.
- **실험적 AOT/JIT 컴파일러 제거 (JEP 410)**: GraalVM 기반 실험적 AOT·JIT 컴파일러(jaotc 등)를 JDK에서 제거. AOT 컴파일은 별도 GraalVM 프로젝트로 일원화.
- **RMI Activation 제거 (JEP 407)**: 15에서 지원 중단했던 RMI Activation 메커니즘을 완전히 제거.

> **지원 중단(제거 예정) / 제거** — 앞으로 없앨 것이라 표시만 해 둔 상태 / 실제로 빼 버린 상태. 이 절에 둘이 함께 들어 있다.\
> 예: Applet API와 Security Manager가 이 편에서는 표시까지이고, RMI Activation은 원문 표현으로 "15에서 지원 중단했던 … 완전히 제거"다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 넷은 원문의 것이다.)*

Java 17은 단순한 6개월 릴리스가 아니라 **모던 Java의 새 표준선**이다.

1. **문법의 완성**: switch 표현식·텍스트 블록·record·instanceof 패턴 매칭·sealed가 모두 정식 기능으로 모이면서, 12~16에 걸친 점진적 진화가 17에서 하나의 일관된 모습으로 수렴했다. 여기에 switch 패턴 매칭(preview)이 더해져, record + sealed + switch 패턴 매칭이라는 데이터 중심 프로그래밍의 큰 그림이 윤곽을 드러냈다.

2. **마이그레이션의 기준점**: 8/11에 머물던 수많은 프로젝트가 17로 이동했다. Spring Boot 3가 Java 17을 최소 버전으로 요구하면서, 17은 엔터프라이즈 생태계의 사실상 기본값이 됐다.

3. **장기 운영을 위한 정리**: Applet·Security Manager·RMI Activation·실험적 AOT 제거, 강한 캡슐화 완성 등 "오래된 짐을 덜어내는" 작업이 집중됐다. LTS답게, 향후 수년의 안정적 운영을 위한 토대를 다졌다.

4. **현대 하드웨어 대응**: Apple Silicon 네이티브 포트와 Metal 렌더링 파이프라인으로, 변화하는 하드웨어 환경에 발 빠르게 적응했다.

종합하면 Java 17은 "모던 Java를 한 번에 받아들이기 좋은 안정적 LTS"이며, 이후 Java 21 LTS로 이어지는 진화의 든든한 중간 거점이다.

## 용어 풀이

- **LTS(Long-Term Support)** — 원문 표현으로 "수년간 장기 지원·보안 패치를 제공하는 기준 버전". 원문이 든 앞뒤 LTS가 Java 11(2018)과 Java 21(2023)이다.
- **preview(미리보기) / incubator(인큐베이터)** — 정식이 아닌 채로 먼저 실어 보내는 단계 표기. 이 편에서는 switch 패턴 매칭이 preview, FFM·Vector API가 incubator다.
- **sealed / `permits` / 닫힌 집합** — 상속·구현 대상을 제한하겠다는 표시 / 허용 목록을 적는 절 / 그렇게 더 늘지 않게 된 하위 타입의 모임. 원문 표현으로 "타입 계층을 설계자가 닫힌 집합으로 통제"한다.
- **`final` / `sealed` / `non-sealed`** — 봉인 타입의 하위 타입이 가질 수 있는 셋. 원문 설명 그대로 각각 "더 이상 확장 불가" / "다시 제한된 확장 허용" / "봉인을 풀어 자유 확장 허용"이다.
- **대수적 데이터 타입(ADT)** — 원문이 sealed와 record·패턴 매칭을 결합하면 표현할 수 있다고 든 "스타일"의 이름. 이 편은 이름만 들고 뜻을 풀지 않는다.
- **타입 패턴** — `case` 자리에 값이 아니라 타입을 적어 맞춰 보는 것. 이 편에서는 preview다.
- **전체성(exhaustiveness)** — 분기가 가능한 모든 경우를 다뤘는지를 따지는 성질. 원문은 sealed와 결합하면 "컴파일러가 모든 경우를 다뤘는지(exhaustiveness) 검사해"준다고 적는다.
- **가드(guarded pattern)** — 타입이 맞은 뒤 조건을 하나 더 걸어 거르는 것. 원문 주석 표현으로 "17 시대에는 &&"이고, `when`은 19에서 도입된다.
- **PRNG(의사난수 생성기)** — 계산으로 난수처럼 보이는 값을 만드는 장치. 원문이 알고리즘 예로 든 것이 Xoshiro, LXM 계열이다.
- **강한 캡슐화** — JDK 내부 API를 바깥에서 건드리지 못하게 막는 정책. 원문 표현으로 이 편이 "풀 수 있는 길 자체를 없앴다".
- **opt-in(옵트인)** — 기본으로 꺼져 있고 켜야 동작하는 방식. 이 편의 Metal 렌더링 파이프라인이 그렇다.
- **JNI(Java Native Interface)** — Java에서 네이티브 코드를 부르는 기존 방식. 원문은 FFM API가 그 일을 "JNI보다 안전·간결하게" 한다고 적는다.
- **지원 중단(제거 예정) / 제거** — 앞으로 없앨 것이라 표시만 해 둔 상태 / 실제로 뺀 상태. 이 편에서 Applet API·Security Manager가 앞쪽, RMI Activation이 뒤쪽이다.

## 참고 출처
- [OpenJDK: JDK 17](https://openjdk.org/projects/jdk/17/)
- [JEPs in JDK 17 integrated since JDK 11](https://openjdk.org/projects/jdk/17/jeps-since-jdk-11)
- [JEP 409: Sealed Classes](https://openjdk.org/jeps/409)
- [JEP 406: Pattern Matching for switch (Preview)](https://openjdk.org/jeps/406)
- [JEP 356: Enhanced Pseudo-Random Number Generators](https://openjdk.org/jeps/356)
- [JEP 411: Deprecate the Security Manager for Removal](https://openjdk.org/jeps/411)
- [JEP 398: Deprecate the Applet API for Removal](https://openjdk.org/jeps/398)
- [JEP 412: Foreign Function & Memory API (Incubator)](https://openjdk.org/jeps/412)
- [New Features in Java 17 - Baeldung](https://www.baeldung.com/java-17-new-features)
- [Java version history - Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
