# Java 12 (2019년 3월)

> 원본: `~/project/java-history/java/java-12.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JEP 번호·클래스/메서드 이름·코드블록 2개·「릴리스 정보」와 「그 외 변경 / API 추가」의 목록은 원문 그대로다.\
> 「한눈에」의 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.\
> 원문이 77줄로 짧고 도식이 없어, 새 도식은 그리지 않았다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> switch 표현식을 처음 선보이며(preview) 자바 언어 문법의 현대화를 시작한 버전.

이 편을 하나의 비유로 읽으면 **새 문법을 정식 규정집에 바로 싣지 않고, "시범 운영" 딱지를 붙여 먼저 써 보게 한 일**이다.\
딱지가 붙은 동안에는 쓰겠다고 따로 신청해야 하고, 규정은 다음 판에서 바뀔 수 있다.\
**Java 12의 preview도 똑같은 구조다** — 원문 자신이 「시대적 배경」에서 이렇게 적는다: "큰 언어 기능을 **preview(미리보기)** 형태로 먼저 출시해 커뮤니티 피드백을 받고, 이후 릴리스에서 다듬어 정식화하는 패턴".

본문 흐름에 쓰는 비유는 이 시범 운영 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| "시범 운영" 딱지 | preview(미리보기) — 원문 표현으로 "정식화 전에 실험하고 피드백받는" 절차 |
| 쓰겠다고 따로 하는 신청 | 원문 표현으로 컴파일 시 `javac --enable-preview --release 12 ...`, 실행 시 `java --enable-preview ...` |
| 다음 판에서 바뀐 규정 | 원문 표현으로 "이후 Java 13의 2차 preview에서 `yield`로 대체된다" |

초보자가 오해하기 쉬운 자리부터 짚어 두면 이렇다.

- **이 편의 switch 표현식은 정식 기능이 아니다.**\
  원문이 절 안에 적은 상태가 "**미리보기(Preview)**"이고, 쓰려면 컴파일·실행 양쪽에 옵션을 붙여야 한다.
- **`--release 12`와 `--enable-preview`는 붙는 자리가 다르다.**\
  원문이 괄호로 따로 적어 둔 그대로다 — "`--release 12`는 javac 컴파일 옵션이며 java 실행 옵션이 아니다".
- **이 편의 문법은 다음 편에서 한 번 더 바뀐다.**\
  원문이 코드 아래 「참고」로 적은 그대로다 — 이 시점의 값 반환 문법은 `break <값>;`이고, "이후 Java 13의 2차 preview에서 `yield`로 대체된다".

## 릴리스 정보
- 정식 출시일: 2019년 3월 19일
- 개발 주체: Oracle (OpenJDK)
- LTS 여부: 아니오 (단기 지원)
- 포함 JEP 수: 8개

## 시대적 배경

*(「한눈에」의 시범 운영 비유가 가리키는 자리다.)*

Java 11(LTS) 이후 첫 단기 릴리스다. 6개월 케이던스가 안정적으로 자리 잡으면서, 이제 Oracle은 큰 언어 기능을 **preview(미리보기)** 형태로 먼저 출시해 커뮤니티 피드백을 받고, 이후 릴리스에서 다듬어 정식화하는 패턴을 도입했다. Java 12의 switch 표현식이 그 첫 사례로, 이 "preview → 안정화 → 정식" 프로세스는 이후 텍스트 블록, records, sealed classes, pattern matching 등 자바 언어 진화의 표준 절차가 된다.

> **preview(미리보기) 기능** — 아직 정식이 아니어서 켜야만 쓸 수 있고, 다음 릴리스에서 바뀔 수 있는 기능.\
> 예: 원문이 이 절차를 "preview → 안정화 → 정식"이라 적고, 이 편의 첫 사례로 switch 표현식을 든다.

> **단기 릴리스(단기 지원)** — LTS로 지정되지 않아 다음 릴리스까지만 지원되는 버전.\
> 예: 원문이 이 버전의 LTS 칸에 적은 말이 "아니오 (단기 지원)"이고, 「시대적 배경」 첫 문장이 "Java 11(LTS) 이후 첫 단기 릴리스다"이다.

## 주요 추가 기능

### switch 표현식 (JEP 325)
- 상태: **미리보기(Preview)** — 컴파일 시 `javac --enable-preview --release 12 ...`, 실행 시 `java --enable-preview ...` 필요(`--release 12`는 javac 컴파일 옵션이며 java 실행 옵션이 아니다).
- 기존 `switch`는 문(statement)일 뿐이고 fall-through(break 누락 시 다음 case로 흘러내림) 버그가 잦았다. JEP 325는 switch를 **값을 돌려주는 표현식**으로도 쓸 수 있게 하고, 화살표(`->`) 문법을 도입해 fall-through를 없애고 여러 레이블을 콤마로 묶을 수 있게 했다.

**왜 이것이 나왔나** — 원문이 둘째 불릿 앞머리에 적은 그대로다. 기존 `switch`는 문일 뿐이었고, "fall-through(break 누락 시 다음 case로 흘러내림) 버그가 잦았다".

> **문(statement) / 표현식(expression)** — 한 동작을 시키기만 하는 것 / 값을 돌려주는 것.\
> 예: 아래 첫 블록의 `switch`는 `numLetters`에 값을 대입하는 동작을 할 뿐이고, 둘째 블록의 `switch`는 `int numLetters = switch (day) {...}`처럼 그 자체가 값이 된다.

> **fall-through** — 원문 표현으로 "break 누락 시 다음 case로 흘러내림".\
> 예: 아래 첫 코드에서 `numLetters = 6;` 뒤의 `break;`를 빠뜨리면 `case TUESDAY:`의 몸통으로 흘러내린다 — 원문이 그 코드 첫 줄 주석에 적은 말이 "fall-through 위험, break 필요"다.

```java
// 기존 switch 문 (fall-through 위험, break 필요)
int numLetters;
switch (day) {
    case MONDAY:
    case FRIDAY:
    case SUNDAY:
        numLetters = 6;
        break;
    case TUESDAY:
        numLetters = 7;
        break;
    default:
        throw new IllegalStateException();
}

// Java 12 switch 표현식 (preview): 화살표 문법, 값 반환
int numLetters = switch (day) {
    case MONDAY, FRIDAY, SUNDAY -> 6;
    case TUESDAY                -> 7;
    case THURSDAY, SATURDAY     -> 8;
    case WEDNESDAY              -> 9;
};
```
> 참고: 이 시점에는 블록에서 값을 반환할 때 `break <값>;` 문법을 썼다. 이후 Java 13의 2차 preview에서 `yield`로 대체되고, Java 14(JEP 361)에서 정식화된다.

위 한 블록 안의 두 코드는 같은 일을 두 방식으로 적은 것이다.\
앞쪽에서 세 줄에 걸쳐 나란히 놓여 있던 `case MONDAY:` / `case FRIDAY:` / `case SUNDAY:`가 뒤쪽에서는 `case MONDAY, FRIDAY, SUNDAY -> 6;` 한 줄이 되고, `break;`가 사라진다.\
원문이 두 코드 첫 줄 주석에 붙인 이름이 각각 "기존 switch 문 (fall-through 위험, break 필요)"과 "Java 12 switch 표현식 (preview): 화살표 문법, 값 반환"이다.

### Shenandoah GC (JEP 189)
- 상태: **실험적(Experimental)** — Red Hat이 주도한 저지연 GC.
- 힙 크기와 무관하게 짧고 일정한 일시정지를 목표로, 애플리케이션 스레드와 **동시에(concurrent)** 객체를 정리(compaction 포함)한다. ZGC와 함께 자바 저지연 GC 시대를 여는 또 다른 축이다.

> **저지연(low-latency) GC** — 애플리케이션을 멈춰 세우는 시간을 짧게 유지하는 것을 목표로 삼는 가비지 컬렉터.\
> 예: 원문이 Shenandoah의 목표로 적은 것이 "힙 크기와 무관하게 짧고 일정한 일시정지"이고, 같은 축으로 든 다른 하나가 ZGC다.

> **동시에(concurrent) 정리** — 애플리케이션 스레드를 멈춰 두지 않고, 그것이 도는 동안 함께 메모리를 정리하는 것.\
> 예: 원문이 이 방식으로 한다고 적은 일이 객체를 정리하는 것이고, 괄호로 덧붙인 것이 "compaction 포함"이다.

### 마이크로벤치마크 스위트 (JEP 230)
- 상태: 정식(빌드/툴링)
- JMH(Java Microbenchmark Harness) 기반의 마이크로벤치마크 모음을 JDK 소스에 포함시켜, JDK 자체 성능 회귀를 쉽게 측정하고 새 벤치마크를 추가할 수 있게 했다.

> **마이크로벤치마크(microbenchmark)** — 프로그램 전체가 아니라 아주 작은 코드 조각의 속도를 재는 측정.\
> 예: 원문이 이 모음의 기반으로 든 도구가 JMH이고, 재는 대상으로 든 것이 "JDK 자체 성능 회귀"다.

## 그 외 변경 / API 추가
- **컴팩트 숫자 포맷(Compact Number Formatting)** — API 추가: `NumberFormat.getCompactNumberInstance()`로 큰 숫자를 "1K", "1M", "1만", "1000만" 같은 짧은 로케일 인지 형식으로 표현.
  ```java
  NumberFormat fmt = NumberFormat.getCompactNumberInstance(Locale.US, NumberFormat.Style.SHORT);
  fmt.format(1_000);      // "1K"
  fmt.format(1_000_000);  // "1M"
  ```
- **JEP 341 — 기본 CDS 아카이브**: JDK 빌드 시 기본 클래스 리스트로 CDS 아카이브를 미리 생성해 기본 제공. 시작 시간 개선.
- **JEP 344 — G1의 중단 가능한 혼합 컬렉션(Abortable Mixed Collections)**: 일시정지 목표를 초과할 것 같으면 혼합 GC를 중단해 지연 목표를 더 잘 지킴.
- **JEP 346 — G1의 미사용 메모리 즉시 반환**: 유휴 시점에 커밋된 힙 메모리를 OS에 더 신속히 돌려줌.
- **JEP 334 — JVM Constants API**: `java.lang.constant` 패키지 도입. class-file/런타임 아티팩트(상수 풀에 로드 가능한 상수)를 명목상으로 기술하는 API.
- **JEP 340 — 하나의 AArch64 포트만 유지**: 중복된 64비트 ARM 포트 중 하나를 제거.
- **API**: `String.indent(int)`, `String.transform(Function)`, `Collectors.teeing(...)`(두 컬렉터 결과를 합치는 다운스트림), `Files.mismatch(Path, Path)` 등 추가.

> **로케일 인지(locale-aware) 형식** — 나라·언어에 따라 표기를 달리하는 형식.\
> 예: 원문이 같은 줄에 나란히 든 것이 "1K", "1M"과 "1만", "1000만"이고, 위 코드가 `Locale.US`를 주었을 때의 결과로 적어 둔 주석이 `"1K"`와 `"1M"`이다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 불릿은 원문 한 문단을 나눠 적은 것이다.)*

- Java 12는 기능 수는 적지만 **언어 진화의 방법론을 확립한** 릴리스다.
- switch 표현식을 preview로 내놓아 "정식화 전에 실험하고 피드백받는" 절차를 처음 적용했고, 이는 이후 자바가 안전하게 빠른 문법 혁신을 이어가는 틀이 되었다.
- GC 측면에서는 Shenandoah가 합류하면서 ZGC와 함께 저지연 GC 선택지가 넓어졌다.
- 컴팩트 숫자 포맷, `Collectors.teeing` 같은 작지만 실용적인 API도 더해졌다.

## 용어 풀이

- **preview(미리보기) 기능** — 아직 정식이 아니어서 켜야만 쓸 수 있고, 다음 릴리스에서 바뀔 수 있는 기능. 원문이 적은 절차가 "preview → 안정화 → 정식"이다.
- **`--enable-preview`** — preview 기능을 켜는 옵션. 원문에 따르면 컴파일(`javac`)과 실행(`java`) 양쪽에 필요하고, `--release 12`는 javac 쪽에만 붙는다.
- **단기 릴리스(단기 지원)** — LTS로 지정되지 않아 다음 릴리스까지만 지원되는 버전. 원문은 Java 12를 "Java 11(LTS) 이후 첫 단기 릴리스"로 적는다.
- **문(statement) / 표현식(expression)** — 동작을 시키기만 하는 것 / 값을 돌려주는 것. 이 편의 JEP 325가 `switch`를 후자로도 쓸 수 있게 했다.
- **fall-through** — 원문 표현으로 "break 누락 시 다음 case로 흘러내림". 화살표(`->`) 문법이 이것을 없앤다.
- **저지연(low-latency) GC** — 멈춰 세우는 시간을 짧게 유지하는 것을 목표로 삼는 가비지 컬렉터. 원문이 이 축으로 든 둘이 Shenandoah와 ZGC다.
- **동시에(concurrent) 정리** — 애플리케이션 스레드를 멈추지 않고 함께 메모리를 정리하는 것. 원문이 괄호로 덧붙인 범위가 "compaction 포함"이다.
- **마이크로벤치마크(microbenchmark)** — 아주 작은 코드 조각의 속도를 재는 측정. 원문이 든 기반 도구가 JMH다.
- **로케일 인지(locale-aware) 형식** — 나라·언어에 따라 표기를 달리하는 형식. 컴팩트 숫자 포맷이 그렇게 동작한다.

## 참고 출처
- [JDK 12 — OpenJDK Project](https://openjdk.org/projects/jdk/12/)
- [JEP 325: Switch Expressions (Preview)](https://openjdk.org/jeps/325)
- [JEP 230: Microbenchmark Suite](https://openjdk.org/jeps/230)
- [Java 12 Released with Experimental Switch Expressions and Shenandoah GC — InfoQ](https://www.infoq.com/news/2019/03/java12-released/)
- [Java 12 Features — DigitalOcean](https://www.digitalocean.com/community/tutorials/java-12-features)
- [Java version history — Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
