# Java 23 (2024.09)

> 원본: `~/project/java-history/java/java-23.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JEP 번호·클래스/옵션 이름·자바 코드블록 4개와 셸 코드블록 1개·「릴리스 정보」의 JEP 목록·「참고 출처」는 원문 그대로다.\
> 도식은 넣지 않았다 — 원문에 도식이 없고, 원문이 절차로 서술한 메커니즘도 없다.\
> 「한눈에」의 시험 도로 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.\
> 「이 편의 기능은 지금 어디쯤인가」 표의 「그 앞」·「그 뒤」 칸은 같은 시리즈의 다른 편(`java-21.md`·`java-22.md`·`java-24.md`~`java-26.md`)에서 끌어온 보충이고, 출처 편을 칸마다 적었다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 마크다운 Javadoc과 세대별 ZGC 기본화를 정식화하고, 원시 타입 패턴 매칭·모듈 임포트 선언을 새로 프리뷰한 비-LTS 릴리스. 문자열 템플릿은 재설계를 위해 전면 보류되었다.

이 편에서 가장 오래 기억될 사건 하나를 비유로 읽으면 **임시로 깔아 두고 다녀 보게 한 시험 도로를, 다녀 본 사람들 반응이 나빠 아예 걷어낸 일**이다.\
**문자열 템플릿도 똑같은 구조다** — 원문 자신이 「시대적 배경」에서 그 전말을 이렇게 적는다: "21·22에서 프리뷰되었으나, 프로세서 중심 설계가 사용자에게 혼란을 주고 조합성이 떨어진다는 피드백에 따라 23에서는 프리뷰에서조차 제거되었다 — 5년 만에 처음으로 정식화에 이르지 못한 프리뷰 기능이 되었다."

본문 흐름에 쓰는 비유는 이 시험 도로 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 임시로 깔아 둔 시험 도로 | 프리뷰 단계의 기능 — 이 편에서 걷힌 것이 문자열 템플릿(JEP 459) |
| 다녀 본 사람들의 반응 | 원문 표현으로 "사용자에게 혼란을 주고 조합성이 떨어진다는 피드백" |
| 도로를 걷어냄 | 원문 표현으로 "프리뷰에서조차 제거되었다" |
| 정식으로 포장해 넘김 | 정식화 — 이 편에서 그렇게 된 것이 JEP 467과 JEP 474 둘이다 |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **프리뷰는 정식으로 가는 계단이 아니라 시험이다.** 원문이 「영향과 의의」에서 못 박은 그대로다 — "문자열 템플릿의 보류는 "프리뷰는 폐기될 수 있다"는 프리뷰 제도의 취지를 실증한 사례로 남았다."
- **모듈 임포트를 쓰려고 내 코드를 모듈로 만들 필요는 없다.** 원문이 그 절에 직접 적어 둔 한 문장이 "임포트하는 코드가 모듈일 필요는 없다"이다.

### 이 편의 기능은 지금 어디쯤인가

가운데 칸은 이 편 원문이 적은 것이고, 양옆 칸은 그 편들의 원문에서 확인한 보충이다.

| 기능 | 그 앞 | 이 편(23)에서의 상태 | 그 뒤 |
|---|---|---|---|
| Markdown Documentation Comments (JEP 467) | — | **정식** | — |
| ZGC: Generational Mode by Default (JEP 474) | `java-21.md` JEP 439로 세대 모드 추가(당시엔 비세대가 기본) | **정식**(기본값 전환) | `java-24.md` JEP 490에서 비-세대 모드 제거 |
| Primitive Types in Patterns, instanceof, and switch (JEP 455) | — (이 편이 1차) | 프리뷰 | `java-24.md` 2차 → `java-25.md` 3차 → `java-26.md` 4차 — **아직 정식이 아니다** |
| Module Import Declarations (JEP 476) | — (이 편이 1차) | 프리뷰 | `java-24.md` 2차(JEP 494) → `java-25.md` **정식**(JEP 511) |
| Stream Gatherers (JEP 473) | `java-22.md` 1차 프리뷰(JEP 461) | 2차 프리뷰 | `java-24.md` **정식**(JEP 485) |
| Flexible Constructor Bodies (JEP 482) | `java-22.md`에 "Statements before super(...)"라는 이름으로 1차 프리뷰(JEP 447) | 2차 프리뷰 | `java-24.md` 3차(JEP 492) → `java-25.md` **정식**(JEP 513) |
| Class-File API (JEP 466) | `java-22.md` 1차 프리뷰(JEP 457) | 2차 프리뷰 | `java-24.md` **정식**(JEP 484) |
| Implicitly Declared Classes and Instance Main Methods (JEP 477) | `java-21.md` 1차 프리뷰(JEP 445) | 3차 프리뷰 | `java-25.md`에서 "Compact Source Files and Instance Main Methods"로 **정식**(JEP 512) |
| Structured Concurrency (JEP 480) | `java-21.md` 1차 프리뷰(JEP 453) | 3차 프리뷰 | `java-26.md` 6차 프리뷰(JEP 525)까지도 **정식이 아니다** |
| Scoped Values (JEP 481) | `java-21.md` 1차 프리뷰(JEP 446) | 3차 프리뷰 | `java-25.md` **정식**(JEP 506) |
| Vector API (JEP 469) | `java-22.md` 7차 인큐베이터(JEP 460) | 8차 인큐베이터 | `java-26.md` 11차 인큐베이터(JEP 529)까지도 **정식이 아니다** |
| String Templates | `java-21.md` 1차 프리뷰(JEP 430) → `java-22.md` 2차 프리뷰(JEP 459) | **철회 — 목록에서 사라졌다** | 없음. **정식이 된 적이 없다** |

## 릴리스 정보
- 정식 출시일: 2024년 9월 17일
- LTS 여부: 아니오 (단기 지원 / Java 24로 대체)
- 포함 JEP 목록 (총 12개):
  - JEP 455: Primitive Types in Patterns, instanceof, and switch (프리뷰)
  - JEP 466: Class-File API (2차 프리뷰)
  - JEP 467: Markdown Documentation Comments (정식)
  - JEP 469: Vector API (8차 인큐베이터)
  - JEP 471: Deprecate the Memory-Access Methods in sun.misc.Unsafe for Removal
  - JEP 473: Stream Gatherers (2차 프리뷰)
  - JEP 474: ZGC: Generational Mode by Default (정식)
  - JEP 476: Module Import Declarations (프리뷰)
  - JEP 477: Implicitly Declared Classes and Instance Main Methods (3차 프리뷰)
  - JEP 480: Structured Concurrency (3차 프리뷰)
  - JEP 481: Scoped Values (3차 프리뷰)
  - JEP 482: Flexible Constructor Bodies (2차 프리뷰)

이 목록을 상태별로 세어 보면 "(정식)"이 붙은 것은 둘(JEP 467·474), 프리뷰라 적힌 것은 여덟, 인큐베이터가 하나(JEP 469)다.\
남은 하나 JEP 471에는 괄호가 아예 없는데, 그 제목 자체가 상태를 말한다 — `for Removal`, 즉 제거 예고다.\
원문이 「영향과 의의」에서 이 편을 ""정식화 2건 + 다수의 프리뷰 갱신"이라는 전형적인 비-LTS 릴리스 패턴"이라 부르는 근거가 이 셈이다.

## 시대적 배경

Java 22에 이은 두 번째 비-LTS 릴리스로, 1년 뒤 출시될 Java 25 LTS를 향한 기능 성숙의 중간 기점이다.\
가장 주목할 사건은 **문자열 템플릿(JEP 459)의 전면 보류**였다. 21·22에서 프리뷰되었으나, 프로세서 중심 설계가 사용자에게 혼란을 주고 조합성이 떨어진다는 피드백에 따라 23에서는 프리뷰에서조차 제거되었다 — 5년 만에 처음으로 정식화에 이르지 못한 프리뷰 기능이 되었다.\
한편 문서화(마크다운 Javadoc)와 GC(세대별 ZGC) 영역에서 의미 있는 정식 기능이 들어왔고, `sun.misc.Unsafe`의 메모리 접근 메서드 폐기 예고로 FFM/VarHandle로의 이전 신호를 명확히 했다.

> **프리뷰(preview)** — 정식으로 굳히기 전에 미리 내보내 피드백을 받는 단계. 같은 시리즈 `README.md`는 이것을 "정식 채택 전 단계"로 적는다.\
> 예: 이 편에서 프리뷰가 어느 쪽으로도 갈 수 있음이 한꺼번에 드러난다 — Stream Gatherers는 2차 프리뷰로 이어졌고, 문자열 템플릿은 목록에서 빠졌다.

## 주요 추가 기능

### Markdown Documentation Comments (JEP 467, 정식)
- Javadoc 주석을 HTML과 `@`-태그 혼합 대신 마크다운으로 작성할 수 있게 한다. 소스 형태에서 훨씬 읽기 쉽다. `///`로 시작하는 새 주석 형식을 사용한다.

> **Javadoc 주석** — 소스에 달아 두면 API 문서로 뽑혀 나오는 주석. 원문은 이 편 이전의 형식을 "HTML과 `@`-태그 혼합"으로 적는다.\
> 예: 아래 코드에서 줄마다 앞에 붙은 `///`가 원문이 말한 "새 주석 형식"이고, 그 안의 `- `·`` ` ``·`[...]`가 마크다운 표기다.

```java
/// 두 수를 더한다.
///
/// - `a` 첫 번째 값
/// - `b` 두 번째 값
///
/// 자세한 내용은 [java.lang.Math]를 참고.
int add(int a, int b) {
    return a + b;
}
```

### ZGC: Generational Mode by Default (JEP 474, 정식)
- Z 가비지 컬렉터의 기본 모드를 **세대별(generational)** 로 전환한다. 대부분의 워크로드에서 비-세대 모드보다 성능이 크게 우수함이 확인되었다. (비-세대 모드는 이후 Java 24의 JEP 490에서 제거된다.)

**언제 쓸 수 있게 됐나** — 이 편이 만든 기능이 아니라 기본값을 바꾼 편이다. 같은 시리즈 `java-21.md`가 JEP 439로 "ZGC에 세대(generational) 모드"를 추가하며 "21에서는 `-XX:+UseZGC -XX:+ZGenerational`로 활성화(비세대 ZGC가 기본)"라고 적어 두었고, 그 기본값이 여기서 뒤집혔다.

> **기본 모드(기본값)** — 아무 옵션도 주지 않았을 때 자동으로 골라지는 쪽. 기능이 있는 것과 기본으로 켜지는 것은 다른 일이다.\
> 예: 원문이 아래 셸 주석에 적어 둔 그대로다 — "-XX:+UseZGC 만으로 세대별 ZGC가 활성화됨 (-XX:+ZGenerational 불필요)".

```bash
# -XX:+UseZGC 만으로 세대별 ZGC가 활성화됨 (-XX:+ZGenerational 불필요)
java -XX:+UseZGC -jar app.jar
```

### Primitive Types in Patterns, instanceof, and switch (JEP 455, 프리뷰)
- 패턴 매칭, `instanceof`, `switch`를 모든 원시 타입에 대해 사용할 수 있게 확장한다.

> **원시 타입(primitive type)** — `int`·`double`처럼 객체가 아닌 값 그 자체로 다뤄지는 타입. 패턴 매칭은 원래 객체 쪽의 문법이었다.\
> 예: 아래 코드의 `obj instanceof int i`와 `case int i when i > 0`이 원시 타입을 그 자리에 쓴 모습이고, 원문이 그 두 줄에 붙인 주석이 "원시 타입 패턴"과 "원시 타입에 대한 패턴 switch (switch 식)"다.

```java
Object obj = 42;
if (obj instanceof int i) {           // 원시 타입 패턴
    System.out.println(i + 1);
}

int x = 42;
String r = switch (x) {                // 원시 타입에 대한 패턴 switch (switch 식)
    case 0 -> "zero";
    case int i when i > 0 -> "양수";
    default -> "음수";
};
```

이 기능은 이 편에서 정식이 되지 않고, 같은 시리즈의 마지막 편까지도 프리뷰로 남는다 — `java-24.md` 2차(JEP 488), `java-25.md` 3차(JEP 507), `java-26.md` 4차(JEP 530)다.

### Module Import Declarations (JEP 476, 프리뷰)
- 한 모듈이 export하는 모든 패키지를 한 줄로 임포트한다. 임포트하는 코드가 모듈일 필요는 없다.

> **모듈 / export** — 패키지들을 묶어 이름을 붙인 단위 / 그 묶음이 바깥에 내놓는 패키지. 원문은 임포트 대상이 "한 모듈이 export하는 모든 패키지"라고 적는다.\
> 예: 아래 코드의 `import module java.base;`가 그 한 줄이고, 원문 주석이 그 효과를 "java.base 모듈의 모든 export 패키지를 임포트"라 적는다.

```java
import module java.base;   // java.base 모듈의 모든 export 패키지를 임포트

void main() {
    List<String> list = List.of("a", "b");   // java.util 등 별도 import 불필요
}
```

### Stream Gatherers (JEP 473, 2차 프리뷰)
- Java 22에서 프리뷰된 사용자 정의 중간 연산 API를 큰 변경 없이 2차 프리뷰로 이어간다. (Java 24에서 정식화됨.)

### Flexible Constructor Bodies (JEP 482, 2차 프리뷰)
- "Statements before super(...)"(JEP 447)에서 이름이 바뀐 기능의 2차 프리뷰. 명시적 생성자 호출 이전에 문장을 둘 수 있다.

> **명시적 생성자 호출** — 생성자 안에서 부모나 자기 자신의 다른 생성자를 직접 부르는 `super(...)`·`this(...)` 호출.\
> 예: 아래 코드가 그 둘 중 `this(...)` 쪽을 보여 준다 — 원문 주석대로 "명시적 this(...) 호출 전에 검증 문장 배치"가 먼저 오고, 그다음 줄이 "검증 뒤에 오는 명시적 생성자 호출"이다.

```java
class Range {
    final int lo, hi;
    Range(int lo, int hi) {
        this.lo = lo;
        this.hi = hi;
    }
    Range(int[] bounds) {
        if (bounds.length != 2)                   // 명시적 this(...) 호출 전에 검증 문장 배치
            throw new IllegalArgumentException();
        this(bounds[0], bounds[1]);               // 검증 뒤에 오는 명시적 생성자 호출
    }
}
```

## 그 외 변경
- **Deprecate Memory-Access Methods in sun.misc.Unsafe (JEP 471)**: `sun.misc.Unsafe`의 메모리 접근 메서드를 향후 제거 대상으로 폐기 예고. 대체 수단은 VarHandle(JDK 9)과 FFM API(JDK 22)다.
- **Class-File API (JEP 466, 2차 프리뷰)**: 클래스 파일 처리 표준 API의 2차 프리뷰.
- **Implicitly Declared Classes and Instance Main Methods (JEP 477, 3차 프리뷰)**: 초보자 친화적 진입점 계속 다듬기.
- **Structured Concurrency (JEP 480, 3차 프리뷰)** / **Scoped Values (JEP 481, 3차 프리뷰)**: Project Loom 동시성 기능 지속.
- **Vector API (JEP 469, 8차 인큐베이터)**: SIMD 벡터 API 계속 인큐베이팅.

> **폐기 예고(deprecate for removal)** — 아직 동작하지만 앞으로 없앨 것이라고 미리 표시해 두는 일. 쓰는 쪽에 옮길 시간을 준다.\
> 예: 원문이 이 자리에서 대체 수단으로 지목한 둘이 "VarHandle(JDK 9)과 FFM API(JDK 22)"이고, 실제 경고는 `java-24.md`의 JEP 498에서 붙는다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 문장은 원문의 것이다.)*

Java 23은 "정식화 2건 + 다수의 프리뷰 갱신"이라는 전형적인 비-LTS 릴리스 패턴을 보여준다.\
마크다운 Javadoc은 라이브러리 문서화 경험을 즉각 개선했고, 세대별 ZGC 기본화는 대용량 힙·저지연 서비스의 운영 기본값을 바꾸었다.\
무엇보다 문자열 템플릿의 보류는 "프리뷰는 폐기될 수 있다"는 프리뷰 제도의 취지를 실증한 사례로 남았다.

## 용어 풀이

- **프리뷰(preview)** — 정식으로 굳히기 전에 미리 내보내 피드백을 받는 단계. 같은 시리즈 `README.md`는 "정식 채택 전 단계"로 적고, 이 편은 그 단계가 폐기로도 끝날 수 있음을 보여 준 편이다.
- **Javadoc 주석** — 소스에 달아 두면 API 문서로 뽑혀 나오는 주석. 이 편 이전의 형식을 원문은 "HTML과 `@`-태그 혼합"으로 적고, 이 편이 더한 형식이 `///`로 시작하는 마크다운이다.
- **기본 모드(기본값)** — 아무 옵션도 주지 않았을 때 자동으로 골라지는 쪽. 이 편에서 ZGC의 기본값이 세대별로 바뀌었다.
- **세대별(generational) 모드** — 객체를 젊은 쪽과 오래된 쪽으로 나눠 관리하는 방식. 그 정의는 같은 시리즈 `java-21.md`의 JEP 439 절에 있다 — "객체를 젊은 세대와 오래된 세대로 나눠 관리한다".
- **원시 타입(primitive type)** — `int`·`double`처럼 객체가 아닌 값 그 자체로 다뤄지는 타입. 이 편에서 패턴 매칭·`instanceof`·`switch`로 확장되었으나 프리뷰다.
- **모듈 / export** — 패키지들을 묶어 이름을 붙인 단위 / 그 묶음이 바깥에 내놓는 패키지. 원문은 "임포트하는 코드가 모듈일 필요는 없다"고 못 박는다.
- **명시적 생성자 호출** — 생성자 안에서 `super(...)`·`this(...)`로 다른 생성자를 직접 부르는 것. 이 편의 JEP 482가 그 호출 "이전에 문장을 둘 수 있다"고 적는다.
- **폐기 예고(deprecate for removal)** — 아직 동작하지만 앞으로 없앨 것이라고 미리 표시해 두는 일. 이 편의 대상이 `sun.misc.Unsafe`의 메모리 접근 메서드다.

## 참고 출처
- [JDK 23 - OpenJDK 프로젝트 페이지](https://openjdk.org/projects/jdk/23/)
- [Oracle Releases Java 23](https://www.oracle.com/news/announcement/oracle-releases-java-23-2024-09-17/)
- [Java 23 Delivers Markdown Documentation, ZGC Generational Mode, Deprecate sun.misc.Unsafe - InfoQ](https://www.infoq.com/news/2024/09/java23-released/)
- [Update on String Templates (JEP 459) - OpenJDK amber-spec-experts](https://mail.openjdk.org/pipermail/amber-spec-experts/2024-April/004106.html)
- [Java version history - Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
