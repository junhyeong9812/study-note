# Java 5 (J2SE 5.0, Tiger, 2004년 9월)

> 원본: `~/project/java-history/java/java-5.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JSR 번호·클래스/패키지 이름·코드블록 14개·「릴리스 정보」와 「그 외 변경 / API 추가」의 목록은 원문 그대로다.\
> ASCII 도식 1개(원문 mermaid 그림을 글자로 옮긴 것이다)와 「한눈에」의 라벨 비유·대응표, 용어 블록의 「예:」, 「용어 풀이」, 다른 편을 가리키는 교차 주 4개는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 제네릭, 어노테이션, enum, 향상된 for문 등을 한꺼번에 도입해 Java 언어 문법 자체를 가장 크게 바꾼 대변혁 릴리스.

이 편의 제네릭을 하나의 비유로 읽으면 **상자에 "사과만"이라고 라벨을 붙여 두고, 창고 문 앞의 검사원이 들여보내기 전에 라벨과 내용물을 맞춰 본 다음, 라벨을 떼고 들여보내는 일**이다.\
검사는 문 앞에서 끝나므로, 창고 안에 들어간 상자는 라벨 없이 다 같은 상자로 보인다.

**제네릭도 똑같은 구조다** — 원문 자신이 이렇게 적는다: "제네릭은 **컴파일 시점에만** 타입을 검사하고, 바이트코드에서는 타입 인자를 지운다(type erasure)".

본문 흐름에 쓰는 비유는 이 라벨 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 상자에 붙인 "사과만" 라벨 | 타입 인자 — 원문 코드의 `List<String>` |
| 문 앞의 검사원 | 원문 표현으로 "**컴파일 시점에만** 타입을 검사"하는 컴파일러 |
| 들여보내며 라벨을 떼는 것 | 원문 표현으로 "바이트코드에서는 타입 인자를 지운다(type erasure)" |
| 창고 안에서는 다 같은 상자로 보이는 것 | 원문 표현으로 "런타임에는 `List<String>`과 `List<Integer>`가 동일한 raw `List`로 보이며" |
| 라벨이 없어도 꺼낸 것의 종류가 맞는 이유 | 원문 표현으로 "타입 안정성은 컴파일러가 삽입한 캐스트로만 보장된다" |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **제네릭의 타입 인자는 런타임까지 남지 않는다.**\
  원문이 「제네릭 (Generics, JSR 14)」 절 끝에서 직접 적는다 — "런타임에는 `List<String>`과 `List<Integer>`가 동일한 raw `List`로 보이며, 타입 안정성은 컴파일러가 삽입한 캐스트로만 보장된다".
- **어노테이션은 그 자체로는 메타데이터다.**\
  어노테이션이 **무엇인가**에 대해 원문이 적는 것은 "클래스, 메서드, 필드 등 언어 구성요소에 메타데이터를 부착할 수 있게 되었다"이다.\
  *(교차 주: 그 메타데이터를 읽어 처리하는 쪽은 `java-6` 편이 적는다 — 그 편의 「플러그인 가능한 어노테이션 처리 (Pluggable Annotation Processing, JSR 269)」가 "컴파일 시점에 어노테이션을 처리하는 표준 API"를 든다.)*
- **버전 번호 5.0은 1.5 다음 번호가 아니다.**\
  원문이 「릴리스 정보」에 직접 적는다 — "J2SE 5.0 (내부 버전 1.5) — 마케팅상 버전 번호를 1.5에서 5.0으로 점프".

## 릴리스 정보
- 정식 출시일: 2004년 9월 30일
- 개발 주체: Sun Microsystems (JCP, Java Community Process를 통한 표준화)
- 공식 명칭: J2SE 5.0 (내부 버전 1.5) — 마케팅상 버전 번호를 1.5에서 5.0으로 점프
- 코드네임: Tiger
- 플랫폼 스펙: JSR 176 (J2SE 5.0 Release Contents)
- LTS 여부: 해당 시대엔 LTS 개념 자체가 없었음 (LTS는 Java 8 이후 도입)

*(교차 주: 여섯째 불릿의 괄호가 잡은 기준점은 편마다 조금씩 다르게 적힌다 — `java-8` 편은 자기 LTS 항목을 "현대적 LTS 모델(Java 11부터 시작) 이전 버전"으로 적고, 원문 repo의 `README`(`~/project/java-history/java/README.md`)는 LTS 목록에 "Java 8, 11, 17, 21, 25"를 함께 올린다. 셋 다 이 편(5.0) 당시에는 LTS가 없었다는 점에서는 어긋나지 않는다.)*

## 시대적 배경

J2SE 5.0 이전의 Java는 컬렉션을 다룰 때 모든 요소를 `Object`로 취급하고 꺼낼 때마다 캐스팅해야 했으며, 런타임에야 `ClassCastException`으로 타입 오류가 드러났다.\
상수 집합은 `int` 상수나 어색한 typesafe enum 패턴으로 흉내 내야 했고, 메타데이터는 XML 설정 파일이나 주석 규약(XDoclet 등)에 의존했다.

*(원문이 「시대적 배경」에서 불편·위험으로 적은 자리는 위 두 줄이다 — 이는 5.0이 치른 대가가 아니라 5.0이 나온 동기다.)*

당시 C#이 등장하며 언어 차원의 생산성을 강조하던 경쟁 환경에서, Sun은 "개발자가 더 적은 코드로 더 안전하게" 쓸 수 있도록 언어 문법을 대대적으로 손봤다.\
Tiger는 1.0 이후 Java 언어에 가해진 가장 큰 변화로 평가된다.

## 주요 추가 기능

### 제네릭 (Generics, JSR 14)

컴파일 타임 타입 안정성을 제공하고 대부분의 명시적 캐스팅을 제거한다.

도입 전:
```java
List list = new ArrayList();
list.add("hello");
// 잘못된 타입을 넣어도 컴파일러가 막지 못함
list.add(42);
String s = (String) list.get(0); // 매번 캐스팅 필요, 런타임 위험
```

도입 후:
```java
List<String> list = new ArrayList<String>();
list.add("hello");
// list.add(42); // 컴파일 에러 — 잘못된 타입을 컴파일 시점에 차단
String s = list.get(0); // 캐스팅 불필요
```

두 블록은 같은 일을 하는 코드를 도입 전후로 적은 것이다.\
위에서 `new ArrayList()`였던 것이 아래에서 `new ArrayList<String>()`이 되고, 위에서 `(String) list.get(0)`이었던 것이 아래에서 `list.get(0)`이 된다.\
`list.add(42)` 한 줄의 운명이 두 주석에 갈려 있다 — 위에서는 "잘못된 타입을 넣어도 컴파일러가 막지 못함", 아래에서는 "컴파일 에러".

> **제네릭(generics)** — 타입을 나중에 정할 수 있게 비워 두고, 쓰는 자리에서 채워 넣게 하는 문법.\
> 예: 원문 코드의 `List<String>`이 그 채움이고, 원문은 그 효과를 "컴파일 타임 타입 안정성을 제공하고 대부분의 명시적 캐스팅을 제거한다"고 적는다.

> **타입 인자(type argument)** — 비워 둔 자리에 실제로 채워 넣은 타입. `<>` 안에 적는다.\
> 예: `List<String>`의 `String`이 타입 인자다.

제네릭 메서드와 와일드카드도 함께 도입되었다:
```java
public static <T> T firstOf(List<T> list) {
    return list.get(0);
}

void printAll(List<? extends Number> nums) {
    for (Number n : nums) System.out.println(n);
}
```

> **제네릭 메서드** — 메서드 하나만을 위해 타입 자리를 비워 두는 문법.\
> 예: 위 코드의 `public static <T> T firstOf(List<T> list)`가 그것이고, 앞에 붙은 `<T>`가 비워 둔 자리다.

> **와일드카드** — 타입 인자 자리에 구체적인 타입 대신 `?`를 적어, 한 가지로 고정하지 않는 표기.\
> 예: 위 코드의 `List<? extends Number>`가 그것이다.

제네릭은 **컴파일 시점에만** 타입을 검사하고, 바이트코드에서는 타입 인자를 지운다(type erasure). 아래는 그 흐름이다.

```text
소스: List<String>
        ↓
컴파일러: 타입 검사
(컴파일 시점)
        ↓
타입 소거: raw List 로 변환
        ↓
바이트코드: List + 자동 캐스트 삽입
        ↓
런타임: 타입 인자 정보 없음
```

위 그림은 원문의 mermaid 그림(`flowchart LR`)을 글자로 옮긴 것이다 — 다섯 칸의 문구와 네 화살표의 방향 모두 원문의 것이고, 가로로 놓인 것을 세로로 내려 적었을 뿐이다.

런타임에는 `List<String>`과 `List<Integer>`가 동일한 raw `List`로 보이며, 타입 안정성은 컴파일러가 삽입한 캐스트로만 보장된다.

> **타입 소거(type erasure)** — 원문 표현 그대로 "바이트코드에서는 타입 인자를 지운다"는 것.\
> 예: 위 그림의 셋째 칸이 "타입 소거: raw List 로 변환"이고, 다섯째 칸이 "런타임: 타입 인자 정보 없음"이다.

> **raw `List`** — 타입 인자가 붙지 않은 `List`. 원문은 소거 뒤의 모습을 이 이름으로 적는다.\
> 예: 원문이 든 그대로, 런타임에는 `List<String>`과 `List<Integer>`가 둘 다 이 모습이다.

### 어노테이션 / 메타데이터 (Annotations, JSR 175)

클래스, 메서드, 필드 등 언어 구성요소에 메타데이터를 부착할 수 있게 되었다. 프레임워크 설정이 XML에서 코드 내 어노테이션으로 이동하는 흐름의 출발점이다.

> **메타데이터(metadata)** — 무언가에 대해 덧붙여 두는 정보. 그 자체가 일을 하는 것이 아니라, 읽는 쪽이 있어야 쓰인다.\
> 예: 원문은 어노테이션을 "언어 구성요소에 메타데이터를 부착"하는 수단으로 적고, 그 부착 대상으로 클래스·메서드·필드를 든다.

```java
@Override
public String toString() {
    return "tiger";
}

@Deprecated
public void oldApi() { }

// 사용자 정의 어노테이션
@interface Author {
    String name();
}

@Author(name = "Duke")
class Sample { }
```
표준 내장 어노테이션으로 `@Override`, `@Deprecated`, `@SuppressWarnings`가 추가되었다.

위 코드에 원문이 든 표준 내장 셋 중 둘이 나온다 — `@Override`와 `@Deprecated`이고, `@SuppressWarnings`는 이 코드에 나오지 않는다.\
나머지 둘, `@interface Author { … }`와 `@Author(name = "Duke")`는 코드 주석이 말하는 "사용자 정의 어노테이션"을 선언하는 쪽과 쓰는 쪽이다.

### 열거형 (enum, JSR 201)

타입 안전한 상수 집합을 언어 차원에서 지원한다.

도입 전:
```java
public static final int SEASON_SPRING = 0;
public static final int SEASON_SUMMER = 1;
// 단순 int라 타입 안전성 없음, 잘못된 값 전달 가능
```

도입 후:
```java
public enum Season { SPRING, SUMMER, FALL, WINTER }

Season s = Season.SPRING;
switch (s) {
    case SPRING:
        break;
    default:
        break;
}

// enum은 필드와 메서드도 가질 수 있는 완전한 클래스
public enum Planet {
    EARTH(9.8), MARS(3.7);
    private final double gravity;
    Planet(double g) { this.gravity = g; }
    public double gravity() { return gravity; }
}
```

두 블록의 대비가 코드 주석에 그대로 적혀 있다 — 위는 "단순 int라 타입 안전성 없음, 잘못된 값 전달 가능"이고, 아래의 `Planet`에 붙은 주석은 "enum은 필드와 메서드도 가질 수 있는 완전한 클래스"다.

> **enum(열거형)** — 정해진 몇 개의 값만 가질 수 있는 타입. 원문 표현으로 "타입 안전한 상수 집합"이다.\
> 예: 원문 코드의 `public enum Season { SPRING, SUMMER, FALL, WINTER }`가 네 값만 갖는 타입을 선언한 것이다.

### 향상된 for문 (for-each, JSR 201)

컬렉션과 배열 순회를 간결하게 한다.

도입 전:
```java
for (Iterator it = list.iterator(); it.hasNext(); ) {
    String s = (String) it.next();
    System.out.println(s);
}
```

도입 후:
```java
for (String s : list) {
    System.out.println(s);
}
```

두 블록은 같은 순회를 도입 전후로 적은 것이다 — 위의 `for (Iterator it = list.iterator(); it.hasNext(); )`와 `String s = (String) it.next();` 두 줄이 아래에서는 `for (String s : list)` 한 줄이 된다.

*(교차 주: 위 "도입 전" 쪽 코드는 앞 편들의 코드와 같은 모습이다 — `jdk-1.1` 편과 `jdk-1.2` 편의 코드 주석이 각각 "for-each도 5.0부터", "제네릭·for-each·오토박싱은 모두 J2SE 5.0부터다(diamond `<>`는 Java SE 7)"라고 미리 적어 둔 그 제약이다.)*

### 오토박싱 / 언박싱 (Autoboxing/Unboxing, JSR 201)

기본형과 래퍼 타입 간 변환을 자동화한다.

도입 전:
```java
List<Integer> nums = new ArrayList<Integer>();
nums.add(Integer.valueOf(10));      // 수동 박싱
int x = nums.get(0).intValue();     // 수동 언박싱
```

도입 후:
```java
List<Integer> nums = new ArrayList<Integer>();
nums.add(10);          // 자동 박싱 (int -> Integer)
int x = nums.get(0);   // 자동 언박싱 (Integer -> int)
```

두 블록에서 달라진 것은 두 줄뿐이다 — `Integer.valueOf(10)`이 `10`이 되고, `nums.get(0).intValue()`가 `nums.get(0)`이 된다.

> **기본형과 래퍼 타입** — `int` 같은 값 자체의 타입과, 그것을 객체로 감싼 `Integer` 같은 타입.\
> 예: 원문 코드 주석이 두 방향을 각각 "자동 박싱 (int -> Integer)", "자동 언박싱 (Integer -> int)"로 적는다.

> **오토박싱 / 언박싱** — 원문 표현 그대로 "기본형과 래퍼 타입 간 변환을 자동화한다"는 것. 손으로 쓰던 변환 코드를 컴파일러가 대신 넣어 준다.\
> 예: 원문 코드에서 `Integer.valueOf(10)`이라 쓰던 자리에 `10`만 써도 되게 된 것이다.

### 가변인자 (Varargs, JSR 201)

개수가 정해지지 않은 인자를 배열처럼 받을 수 있다.

```java
static int sum(int... values) {
    int total = 0;
    for (int v : values) total += v;
    return total;
}
sum(1, 2, 3, 4); // 호출 시 개수 자유
```
`printf`/`String.format`도 이 기능 위에서 동작한다.

> **가변인자(varargs)** — 인자 개수를 고정하지 않고 받는 문법. 타입 뒤에 `...`을 붙인다.\
> 예: 위 코드의 `int... values`가 그것이고, 원문이 든 호출이 `sum(1, 2, 3, 4)`다.

위 코드 안에 앞 절의 기능도 함께 쓰였다 — `for (int v : values)`가 「향상된 for문 (for-each, JSR 201)」의 문법이다.

### 정적 임포트 (Static Import)

정적 멤버를 클래스명 없이 사용할 수 있다.

```java
import static java.lang.Math.*;

double r = sqrt(PI * 2); // Math.sqrt, Math.PI 대신
```

위 코드 주석이 대비를 그대로 적는다 — `sqrt`와 `PI`가 "Math.sqrt, Math.PI 대신" 쓰인 것이다.

### 동시성 유틸리티 (java.util.concurrent, JSR 166)

Doug Lea가 주도한 고수준 동시성 라이브러리가 표준에 편입되었다. `ExecutorService`, `ConcurrentHashMap`, `CountDownLatch`, `BlockingQueue`, 원자적 변수(`AtomicInteger` 등)를 제공한다.

원문은 이 자리에서 제공되는 것들의 이름을 들 뿐, 각각이 무엇을 하는지는 적지 않는다.

```java
ExecutorService pool = Executors.newFixedThreadPool(4);
Future<Integer> f = pool.submit(new Callable<Integer>() {
    public Integer call() { return 1 + 1; }
});
Integer result = f.get();
pool.shutdown();
```

위 코드에 원문이 든 이름 중 나오는 것은 `ExecutorService` 하나다 — `Executors.newFixedThreadPool(4)`로 만들어 `pool`에 담고, 마지막에 `pool.shutdown()`으로 닫는다.\
`new Callable<Integer>() { … }`는 `jdk-1.1` 편이 도입한 익명 클래스 문법이고, 그 안의 `Callable<Integer>`·`Future<Integer>`는 이 편의 제네릭 문법이다.

### Scanner (java.util.Scanner)

콘솔/스트림 입력을 간단히 파싱한다.

```java
Scanner sc = new Scanner(System.in);
int n = sc.nextInt();
String line = sc.next();
```

## 그 외 변경 / API 추가
- `printf` / `format` 스타일 포매팅 (`java.util.Formatter`)
- `StringBuilder` 추가 (`StringBuffer`의 동기화하지 않는(non-synchronized) 버전으로 단일 스레드에서 더 빠름)
- `java.lang.instrument` 패키지 (자바 에이전트 기반 계측)
- JVM Tool Interface(JVMTI), JPDA 개선
- 공유 클래스 데이터(Class Data Sharing)로 시작 시간 단축

*(교차 주: 넷째 불릿의 JVMTI는 앞 편이 예고한 것이다 — `jdk-1.3` 편이 JPDA 절 괄호에 "저수준 JVMDI는 이후 J2SE 5.0에서 JVMTI로 대체된다"고 적어 두었다.)*

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 불릿은 원문 한 문단을 문장 단위로 끊은 것이다.)*

- J2SE 5.0은 Java를 "장황하지만 안전한" 언어에서 "현대적 타입 시스템을 갖춘" 언어로 끌어올렸다.
- 제네릭과 어노테이션은 이후 Spring, Hibernate, JUnit 4 같은 어노테이션 기반 프레임워크 생태계의 토대가 되었고, `java.util.concurrent`는 멀티코어 시대의 표준 동시성 모델을 제시했다.
- 오늘날 우리가 쓰는 Java 문법의 상당 부분이 이때 형태를 갖췄으며, Tiger는 Java 역사상 가장 영향력 큰 단일 릴리스로 꼽힌다.

## 용어 풀이

- **제네릭(generics)** — 타입을 나중에 정할 수 있게 비워 두고, 쓰는 자리에서 채워 넣게 하는 문법. 원문이 든 효과가 "컴파일 타임 타입 안정성을 제공하고 대부분의 명시적 캐스팅을 제거한다"이다.
- **타입 인자(type argument)** — 비워 둔 자리에 실제로 채워 넣은 타입. `List<String>`의 `String`이 그것이다.
- **제네릭 메서드** — 메서드 하나만을 위해 타입 자리를 비워 두는 문법. 원문 코드의 `<T> T firstOf(List<T> list)`가 그 예다.
- **와일드카드** — 타입 인자 자리에 구체적인 타입 대신 `?`를 적어 한 가지로 고정하지 않는 표기. 원문 코드의 `List<? extends Number>`가 그 예다.
- **타입 소거(type erasure)** — 원문 표현 그대로 "바이트코드에서는 타입 인자를 지운다"는 것. 원문은 그 결과로 "런타임에는 `List<String>`과 `List<Integer>`가 동일한 raw `List`로 보이며, 타입 안정성은 컴파일러가 삽입한 캐스트로만 보장된다"고 적는다.
- **raw `List`** — 타입 인자가 붙지 않은 `List`. 원문이 소거 뒤의 모습에 붙인 이름이다.
- **메타데이터(metadata)** — 무언가에 대해 덧붙여 두는 정보. 그 자체가 일을 하는 것이 아니라 읽는 쪽이 있어야 쓰인다. 원문은 어노테이션을 이것을 "부착"하는 수단으로 적는다.
- **어노테이션(annotation)** — 클래스·메서드·필드 등에 메타데이터를 붙이는 표시. 원문이 든 표준 내장 셋이 `@Override`, `@Deprecated`, `@SuppressWarnings`다.
- **enum(열거형)** — 정해진 몇 개의 값만 가질 수 있는 타입. 원문 표현으로 "타입 안전한 상수 집합"이며, 원문 코드 주석은 "enum은 필드와 메서드도 가질 수 있는 완전한 클래스"라고 덧붙인다.
- **향상된 for문(for-each)** — 컬렉션과 배열을 `for (타입 변수 : 대상)` 한 줄로 순회하는 문법. 원문이 든 효과가 "컬렉션과 배열 순회를 간결하게 한다"이다.
- **기본형과 래퍼 타입** — `int` 같은 값 자체의 타입과, 그것을 객체로 감싼 `Integer` 같은 타입. 원문 코드 주석이 두 방향을 "int -> Integer", "Integer -> int"로 적는다.
- **오토박싱 / 언박싱** — 원문 표현 그대로 "기본형과 래퍼 타입 간 변환을 자동화한다"는 것.
- **가변인자(varargs)** — 인자 개수를 고정하지 않고 받는 문법. 타입 뒤에 `...`을 붙인다. 원문은 `printf`/`String.format`도 이 기능 위에서 동작한다고 적는다.
- **정적 임포트(static import)** — 원문 표현 그대로 "정적 멤버를 클래스명 없이 사용"하게 해 주는 문법.
- **`StringBuilder`** — 원문 표현 그대로 "`StringBuffer`의 동기화하지 않는(non-synchronized) 버전으로 단일 스레드에서 더 빠름". 빠르다는 범위를 원문이 "단일 스레드에서"로 한정해 적는다.
- **JSR** — JCP에서 다루는 건마다 붙는 번호. 이 편에 나온 것이 JSR 176(플랫폼 스펙)·14(제네릭)·175(어노테이션)·201(enum·for-each·오토박싱·가변인자)·166(동시성 유틸리티)이다.

## 참고 출처
- [Java version history — Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
- [J2SE 5.0 — Oracle](https://www.oracle.com/java/technologies/javase/j2se-1-5.html)
- [JSR 176: J2SE 5.0 Release Contents — JCP](https://jcp.org/en/jsr/detail?id=176)
- [J2SE 5.0 (September 30, 2004) — Liquisearch](https://www.liquisearch.com/java_version_history/j2se_50_september_30_2004)
