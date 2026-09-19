# Java SE 8 (2014년 3월)

> 원본: `~/project/java-history/java/java-8.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JSR/JEP 번호·클래스/패키지/메서드 이름·자바 코드블록 13개·「릴리스 정보」와 「그 외 변경 / API 추가」의 목록은 원문 그대로다.\
> ASCII 도식 2개는 원문의 mermaid 그림 2개를 글자로 옮긴 것이고, 「한눈에」의 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」, 교차 주 2개는 원문에 없는 보충이다.\
> 원문에 없는 도식은 새로 그리지 않았다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 람다 표현식과 Stream API로 자바에 함수형 프로그래밍을 도입한, 자바 역사상 가장 혁명적인 릴리스.

이 편을 하나의 비유로 읽으면 **"무엇을 할지 적은 쪽지"를 남에게 건넬 수 있게 된 일**이다.\
그전에도 쪽지를 건넬 수는 있었지만, 쪽지 한 장을 건네려고 매번 봉투를 접고 주소를 쓰고 봉인을 해야 했다(익명 클래스).\
**Java 8의 람다도 똑같은 구조다** — 원문 자신이 「시대적 배경」에서 그 불편을 이렇게 적는다: "익명 클래스로 콜백 하나를 넘기는 데 5~6줄을 써야 하는 자바의 boilerplate".

본문 흐름에 쓰는 비유는 이 쪽지 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 건네는 쪽지 한 장 | 람다 표현식 — 원문 표현으로 "함수를 값처럼 전달할 수 있게 하는 익명 함수 문법" |
| 쪽지를 넣으려고 매번 접던 봉투 | 익명 클래스 — 원문 표현으로 "콜백 하나를 넘기는 데 5~6줄" |
| 쪽지가 맞춰야 하는 접수창구 양식 | 함수형 인터페이스(SAM) — 원문 표현으로 "람다의 타깃 타입" |
| 받은 쪽지대로 일을 처리하는 작업대 | Stream 파이프라인 — 원문 표현으로 "filter / map / reduce의 선언적 연산" |

초보자가 오해하기 쉬운 자리부터 짚어 두면 이렇다.

- **원문은 Stream을 "빠르다"로 설명하지 않는다.**\
  이 편의 원문이 Stream 절에서 쓰는 말은 "함수형 스타일"·"선언적"·"손쉬운 병렬 처리"·"데이터 구조 수준에서 추상화" 쪽이고, "빠르다"는 말은 이 편 어디에도 나오지 않는다.\
  (이 편에서 "고성능"이라는 말이 붙은 곳은 Stream이 아니라 Nashorn 절의 "고성능 JavaScript 런타임" 한 자리다.)
- **`Optional`은 원문 표현으로 NPE를 "줄이고"이지, 없앤다가 아니다.**\
  원문 문장 그대로는 "`NullPointerException`을 줄이고 의도를 명시하는 컨테이너"다.
- **람다가 익명 클래스와 어떤 구현 관계인지는 원문이 적지 않는다.**\
  원문이 적은 것은 "익명 클래스의 장황함을 제거했다"까지다.\
  같은 시리즈 `java-7.md`는 `invokedynamic`을 두고 "Java 8 람다 구현의 기반이 되었다"고 적는다 — 구현 방식 이야기는 이 편이 아니라 그쪽에 있다.

## 릴리스 정보
- 정식 출시일: 2014년 3월 18일 (JDK 8 General Availability)
- 개발 주체: Oracle (OpenJDK / JCP)
- 플랫폼 명세: JSR 337 (Java SE 8 Platform)
- 코드네임: 별도의 공식 마케팅 코드네임 없음 (개발 프로젝트명은 "JDK 8")
- LTS 여부: 현대적 LTS 모델(Java 11부터 시작) 이전 버전이지만, Oracle이 상용·확장 지원을 장기간 제공하여 사실상 가장 오래 살아남은 "장기 지원" 버전으로 취급됨

> **LTS(Long-Term Support)** — 한 버전을 오래 지원해 주기로 정해 두는 제도.\
> 예: 원문은 Java 8이 이 제도 이전 버전이라고 적으면서, 제도가 시작된 지점을 "Java 11부터"로 든다.

## 시대적 배경

Java 8은 자바 진영이 함수형 프로그래밍이라는 시대적 흐름에 응답한 결과물이다. 2000년대 후반부터 Scala, Clojure, Groovy 같은 JVM 기반 언어들이 함수형 스타일과 간결한 문법을 무기로 자바의 장황함(verbosity)을 정면으로 비판했다. 익명 클래스로 콜백 하나를 넘기는 데 5~6줄을 써야 하는 자바의 boilerplate는 멀티코어 시대의 병렬 처리 요구와도 맞지 않았다.

원래 람다(Project Lambda, JSR 335)는 Java 7에 포함될 예정이었으나, Sun의 경영난과 Oracle의 인수(2010) 과정에서 "Plan B"에 따라 Java 7에서는 작은 기능들만 내고 람다와 모듈 시스템은 다음 버전으로 미뤄졌다. 그 결과 람다는 Java 8로, 모듈 시스템은 Java 9로 넘어갔다. 약 2년 반의 준비 끝에 출시된 Java 8은 언어·라이브러리·JVM 전반을 동시에 바꾼 대형 릴리스가 되었다.

> **boilerplate(장황한 상용구)** — 하는 일에 비해 매번 똑같이 길게 적어야 하는 코드.\
> 예: 원문이 이 자리에서 든 것이 "익명 클래스로 콜백 하나를 넘기는 데 5~6줄"이고, 아래 람다 절의 "Before (Java 7)" 코드가 바로 그 모습이다.

> **콜백(callback)** — 지금 실행하지 않고 넘겨 두었다가 나중에 대신 불러 달라고 건네는 코드 조각.\
> 예: 아래 람다 절의 `Runnable`이 그런 것으로, `new Thread(r).start()`가 그것을 나중에 불러 준다.

> **멀티코어(multi-core)** — CPU 안에 계산하는 코어가 여럿 들어 있는 것. 일을 나눠 동시에 돌릴 수 있다.\
> 예: 원문은 자바의 boilerplate가 "멀티코어 시대의 병렬 처리 요구와도 맞지 않았다"고 적고, Stream 절에서 `parallelStream()`을 "멀티코어 활용을 데이터 구조 수준에서 추상화"한 것으로 든다.

## 주요 추가 기능

### 람다 표현식 (JSR 335, JEP 126)

*(「한눈에」의 "건네는 쪽지 한 장"에 해당하는 자리다.)*

- 함수를 값처럼 전달할 수 있게 하는 익명 함수 문법. 자바 8의 핵심이자 다른 모든 기능의 토대다.
- 동작 파라미터화(behavior parameterization)를 가능하게 하여, 익명 클래스의 장황함을 제거했다.

> **람다 표현식(lambda expression)** — 이름 없이 "받는 것 -> 하는 일"만 적어 둔 함수. 원문 표현으로 "익명 함수 문법"이다.\
> 예: 아래 "After" 코드의 `() -> System.out.println("Hello")`가 그것이고, 위 "Before" 코드에서 같은 일을 하던 것이 `new Runnable() { ... run() { ... } }` 전체다.

> **동작 파라미터화(behavior parameterization)** — 값이 아니라 *할 일 자체*를 인자로 넘기는 것.\
> 예: 아래 `Collections.sort(names, (a, b) -> a.compareTo(b))`에서 넘어가는 둘째 인자가 "어떻게 비교할지"라는 동작이다.

```java
// Before (Java 7): 익명 클래스로 Runnable 전달
Runnable r = new Runnable() {
    @Override
    public void run() {
        System.out.println("Hello");
    }
};
new Thread(r).start();

// 정렬도 익명 Comparator로
List<String> names = Arrays.asList("Charlie", "Alice", "Bob");
Collections.sort(names, new Comparator<String>() {
    @Override
    public int compare(String a, String b) {
        return a.compareTo(b);
    }
});
```

```java
// After (Java 8): 람다로 간결하게
Runnable r = () -> System.out.println("Hello");
new Thread(r).start();

List<String> names = Arrays.asList("Charlie", "Alice", "Bob");
Collections.sort(names, (a, b) -> a.compareTo(b));
// 또는 메서드 참조 + Comparator 유틸
names.sort(Comparator.naturalOrder());
```

두 블록은 같은 일을 두 방식으로 적은 것이다.\
위 블록의 `new Runnable() { ... }` 여섯 줄이 아래 블록에서 `() -> System.out.println("Hello")` 한 줄이 되고, `new Comparator<String>() { ... }` 여섯 줄이 `(a, b) -> a.compareTo(b)` 한 줄이 된다.\
원문이 아래 블록의 주석으로 덧붙인 셋째 방법이 "메서드 참조 + Comparator 유틸"인 `names.sort(Comparator.naturalOrder())`다.

> **재서술자 주:** 위 두 블록만 보면 람다가 익명 클래스를 짧게 적은 것으로 읽히기 쉬운데, 이 편의 원문은 둘의 구현 관계를 적지 않는다. 구현 방식을 언급하는 것은 같은 시리즈 `java-7.md` 쪽으로, 거기서 `invokedynamic`을 "Java 8 람다 구현의 기반이 되었다"고 적는다.

### 함수형 인터페이스와 java.util.function

- 추상 메서드가 정확히 하나인 인터페이스(SAM, Single Abstract Method)를 함수형 인터페이스라 하며, 람다의 타깃 타입이 된다.
- `@FunctionalInterface` 어노테이션으로 의도를 명시하고 컴파일러 검증을 받는다.
- 표준 함수형 인터페이스 패키지 `java.util.function` 도입: `Function<T,R>`, `Supplier<T>`, `Consumer<T>`, `Predicate<T>`, `BiFunction<T,U,R>`, `UnaryOperator<T>` 등.

> **추상 메서드(abstract method)** — 이름과 모양만 정해 두고 몸통은 비워 둔 메서드.\
> 예: 아래 코드의 `int apply(int a, int b);`가 그것이고, 원문 표현으로 이런 것이 "정확히 하나"인 인터페이스가 함수형 인터페이스다.

> **타깃 타입(target type)** — 람다를 적은 자리가 요구하는 타입. 람다는 그 타입의 인스턴스로 변환된다.\
> 예: 아래 코드에서 `(a, b) -> a + b`가 놓인 자리의 타입이 `Calculator`이고, 그래서 그 람다가 `Calculator`가 된다.

```java
@FunctionalInterface
interface Calculator {
    int apply(int a, int b);
}

Calculator add = (a, b) -> a + b;
System.out.println(add.apply(3, 4)); // 7

Predicate<String> isEmpty = String::isEmpty;
Function<String, Integer> length = String::length;
```

하나의 람다는 추상 메서드가 하나뿐인 함수형 인터페이스(SAM)의 인스턴스로 변환된다. 아래는 대표 인터페이스와 람다 형태의 매핑이다.

```text
() -> T            -->  Supplier<T>           T get()
(T) -> void        -->  Consumer<T>           void accept(T)
(T) -> boolean     -->  Predicate<T>          boolean test(T)
(T) -> R           -->  Function<T,R>         R apply(T)
(T,U) -> R         -->  BiFunction<T,U,R>     R apply(T,U)
```

- 이 그림은 원문의 mermaid 그림을 글자로 옮긴 것이다 — 화살표 다섯으로 원문의 화살표 수와 같고, 방향도 왼쪽(람다 형태)에서 오른쪽(인터페이스)으로 같다.
- 왼쪽 칸과 오른쪽 칸의 글자는 원문 노드 라벨 그대로다(원문이 `&lt;`·`&gt;`로 적은 자리는 꺾쇠로 되돌렸다). 원문이 한 상자 안에 줄바꿈으로 적어 둔 인터페이스 이름과 메서드 시그니처를 여기서는 두 칸으로 나눠 적었다.
- 같은 줄에 놓인 왼쪽과 오른쪽은 원문이 화살표로 이어 둔 짝이다.

람다의 파라미터·반환 형태가 타깃 함수형 인터페이스의 단일 추상 메서드 시그니처와 일치할 때, 그 인터페이스 타입으로 추론된다.

### 메서드 참조 (Method References)

- 이미 존재하는 메서드를 람다 대신 가리키는 축약 문법. `::` 연산자 사용.
- 4가지 형태: 정적 메서드(`ClassName::staticMethod`), 특정 객체의 인스턴스 메서드(`instance::method`), 임의 객체의 인스턴스 메서드(`ClassName::instanceMethod`), 생성자(`ClassName::new`).

```java
// 람다 → 메서드 참조
list.forEach(s -> System.out.println(s));
list.forEach(System.out::println);          // 인스턴스 메서드 참조

names.stream().map(s -> s.toUpperCase());
names.stream().map(String::toUpperCase);    // 임의 객체 인스턴스 메서드

Supplier<ArrayList<String>> factory = ArrayList::new; // 생성자 참조
```

> **메서드 참조(`::`)** — 새로 적는 대신 이미 있는 메서드를 가리켜 람다 자리에 놓는 문법.\
> 예: 위 코드에서 `s -> System.out.println(s)`를 `System.out::println`으로 줄인 것이 그 짝이고, 원문이 이 줄에 단 주석이 "인스턴스 메서드 참조"다.

위 코드에 원문이 주석으로 붙인 이름은 셋이다 — "인스턴스 메서드 참조", "임의 객체 인스턴스 메서드", "생성자 참조". 원문이 4가지 형태 가운데 첫째로 든 정적 메서드(`ClassName::staticMethod`)는 이 코드에 나오지 않는다.

### Stream API (JEP 107)

*(「한눈에」의 "작업대"에 해당하는 자리다.)*

- `java.util.stream` 패키지. 컬렉션에 대해 함수형 스타일(filter / map / reduce)의 선언적 연산을 제공한다.
- 중간 연산(intermediate, lazy: `filter`, `map`, `sorted`, `distinct`)과 최종 연산(terminal: `collect`, `forEach`, `reduce`, `count`)으로 구성된 파이프라인.
- `parallelStream()`으로 손쉬운 병렬 처리. 멀티코어 활용을 데이터 구조 수준에서 추상화했다.

> **선언적(declarative)** — "어떻게 돌릴지"의 절차 대신 "무엇을 원하는지"를 적는 방식.\
> 예: 아래 "Before" 코드가 `for` 루프로 돌리는 절차를 적는 쪽이고, "After" 코드의 `.filter(...).map(...).sorted()`가 원하는 것을 적는 쪽이다.

> **중간 연산 / 최종 연산** — 파이프라인 도중에 걸리는 단계 / 파이프라인을 끝맺는 단계. 원문은 중간 연산에 lazy, 최종 연산에 terminal이라는 말을 붙인다.\
> 예: 원문이 중간 연산으로 든 것이 `filter`·`map`·`sorted`·`distinct`이고, 최종 연산으로 든 것이 `collect`·`forEach`·`reduce`·`count`다.

```java
// Before (Java 7): 명령형 루프
List<String> names = Arrays.asList("Charlie", "Alice", "Bob", "alex");
List<String> result = new ArrayList<>();
for (String name : names) {
    if (name.length() > 3) {
        result.add(name.toUpperCase());
    }
}
Collections.sort(result);
```

```java
// After (Java 8): 선언적 스트림 파이프라인
List<String> result = names.stream()
        .filter(name -> name.length() > 3)
        .map(String::toUpperCase)
        .sorted()
        .collect(Collectors.toList());

// 집계와 그룹핑도 한 줄로
Map<Integer, List<String>> byLength = names.stream()
        .collect(Collectors.groupingBy(String::length));

int totalLength = names.stream().mapToInt(String::length).sum();

// 병렬 처리
long count = names.parallelStream().filter(n -> n.length() > 3).count();
```

두 블록을 맞대어 보면 짝이 보인다.\
위 블록의 `if (name.length() > 3)`가 아래 블록의 `.filter(name -> name.length() > 3)`이고, `result.add(name.toUpperCase())`가 `.map(String::toUpperCase)`이며, 마지막 줄 `Collections.sort(result)`가 `.sorted()`다.\
원문이 두 블록 첫 줄 주석에 붙인 이름이 각각 "명령형 루프"와 "선언적 스트림 파이프라인"이다.

Stream은 소스 → 중간 연산 → 최종 연산으로 이어지는 파이프라인이며, 중간 연산은 **지연(lazy)** 평가된다.

```text
      소스                Collection.stream()
      |
      v
  +-> 중간 연산           filter (lazy)
  |   |
  |   v
  |   중간 연산           map (lazy)
  |   |
  |   v
  |   중간 연산           sorted (lazy)
  |   |
  |   v
  |   최종 연산           collect / forEach (eager)
  |   |
  +---+   실행 트리거
```

- 이 그림은 원문의 mermaid 그림을 글자로 옮긴 것이다 — 아래로 내려가는 화살표 넷과 되돌아가는 화살표 하나로, 원문의 화살표 다섯(실선 넷 + 점선 하나)과 같다.
- 각 칸의 두 줄(「중간 연산」과 「filter (lazy)」 같은 짝)은 원문이 한 상자 안에 줄바꿈으로 적어 둔 글자 그대로이고, 여기서는 왼쪽·오른쪽 두 칸으로 나눠 적었다.
- 왼쪽 세로줄이 원문의 점선 화살표다. 최종 연산 칸에서 출발해 `filter` 칸으로 되돌아가며, 원문이 그 화살표에 붙인 라벨이 "실행 트리거"다.

`collect`·`forEach` 같은 최종 연산이 호출되기 전까지는 중간 연산이 실제로 실행되지 않는다(지연 평가). 최종 연산이 파이프라인 전체를 한 번에 흐르게 한다.

> **지연(lazy) 평가** — 적어 둔 계산을 그 자리에서 바로 하지 않고, 결과가 필요해질 때까지 미뤄 두는 것.\
> 예: 원문이 바로 위 문단에 적은 그대로다 — `collect`·`forEach` 같은 최종 연산이 호출되기 전까지는 중간 연산이 실제로 실행되지 않는다.

### 인터페이스의 default 메서드와 static 메서드 (JSR 335)

- 인터페이스에 구현(body)을 가진 `default` 메서드와 `static` 메서드를 추가할 수 있게 됨.
- 기존 인터페이스(`Collection`, `List` 등)에 `forEach`, `stream`, `removeIf` 같은 새 메서드를 기존 구현체를 깨뜨리지 않고 추가하기 위한 "인터페이스 진화(interface evolution)" 메커니즘. Stream API 도입의 전제 조건이기도 했다.

**왜 이것이 나왔나** — 원문이 둘째 불릿에서 적은 그대로다. 기존 인터페이스에 새 메서드를 넣으면 그 인터페이스를 구현하던 코드가 깨지는데, `default` 메서드는 "기존 구현체를 깨뜨리지 않고" 넣을 수 있게 한다. 원문은 이것이 "Stream API 도입의 전제 조건이기도 했다"고 적는다.

> **`default` 메서드** — 인터페이스 안에 몸통까지 적어 둔 메서드. 구현 클래스가 따로 적지 않아도 이것이 쓰인다.\
> 예: 아래 코드의 `honk()`에 원문이 단 주석이 "구현체가 오버라이드하지 않아도 됨"이다.

> **인터페이스 진화(interface evolution)** — 이미 쓰이고 있는 인터페이스에 새 메서드를 넣어도 기존 구현체가 깨지지 않게 하는 방식.\
> 예: 원문이 이 방식으로 실제 추가됐다고 든 메서드가 `forEach`·`stream`·`removeIf`이고, 그 인터페이스로 든 것이 `Collection`·`List`다.

```java
interface Vehicle {
    void start();

    // default 메서드: 구현체가 오버라이드하지 않아도 됨
    default void honk() {
        System.out.println("Beep!");
    }

    // static 메서드
    static Vehicle create() {
        return () -> System.out.println("started");
    }
}
```

### 새 날짜·시간 API: java.time (JSR 310, JEP 150)

- 기존 `java.util.Date`/`Calendar`의 고질적 문제(가변성, 0부터 시작하는 month, 스레드 안전성 부재, 빈약한 API)를 해결한 불변(immutable)·스레드 안전 API.
- Joda-Time에서 영감을 받았으며, 핵심 타입: `LocalDate`, `LocalTime`, `LocalDateTime`, `ZonedDateTime`, `Instant`, `Duration`, `Period`, `DateTimeFormatter`.

**왜 이것이 나왔나** — 원문이 첫 불릿 괄호 안에 넷으로 나열한 것이 그 이유다: 가변성, 0부터 시작하는 month, 스레드 안전성 부재, 빈약한 API.

> **불변(immutable)** — 한 번 만들어지면 내용이 바뀌지 않는 것. 바꾸려면 새 객체를 받는다.\
> 예: 아래 "After" 코드의 `date.plusWeeks(1)`에 원문이 단 주석이 "새 객체 반환 (불변)"이다.

> **스레드 안전(thread-safe)** — 여러 갈래가 동시에 같은 객체를 써도 어긋나지 않는 성질.\
> 예: 원문이 "Before" 코드의 `SimpleDateFormat`에 단 주석이 "스레드 안전하지 않음"이고, 새 API를 "불변(immutable)·스레드 안전 API"라 적는다.

```java
// Before (Java 7): Date/Calendar - 가변, month는 0부터
Calendar cal = Calendar.getInstance();
cal.set(2014, Calendar.MARCH, 18); // 2(=March)... 헷갈림
Date date = cal.getTime();
SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd"); // 스레드 안전하지 않음
String s = sdf.format(date);
```

```java
// After (Java 8): java.time - 불변, 직관적
LocalDate date = LocalDate.of(2014, 3, 18);  // month 그대로 3
LocalDate nextWeek = date.plusWeeks(1);       // 새 객체 반환 (불변)
String s = date.format(DateTimeFormatter.ISO_LOCAL_DATE);

LocalDateTime now = LocalDateTime.now();
Duration d = Duration.between(now, now.plusHours(2)); // PT2H
ZonedDateTime seoul = ZonedDateTime.now(ZoneId.of("Asia/Seoul"));
```

두 블록은 같은 날짜(2014년 3월 18일)를 두 API로 적은 것이다.\
위쪽 `cal.set(2014, Calendar.MARCH, 18)`에 원문이 단 주석이 "2(=March)... 헷갈림"이고, 아래쪽 `LocalDate.of(2014, 3, 18)`에 단 주석이 "month 그대로 3"이다.

### Optional<T> (별도 JEP 아님, JSR 335 / Java SE 8 라이브러리 API, java.util.Optional @since 1.8)

- 값이 있을 수도/없을 수도 있음을 타입으로 표현하여 `NullPointerException`을 줄이고 의도를 명시하는 컨테이너.
- `map`, `filter`, `flatMap`, `orElse`, `orElseGet`, `orElseThrow`, `ifPresent`로 함수형 처리.

> **`Optional<T>`** — 값이 들어 있을 수도, 비어 있을 수도 있다는 사실 자체를 타입으로 드러낸 그릇. 원문 표현으로 `NullPointerException`을 "줄이고 의도를 명시하는 컨테이너"다.\
> 예: 아래 "After" 코드의 `Optional.ofNullable(user)`가 "`user`는 없을 수도 있다"를 타입으로 적은 것이고, 없을 때 내놓을 값을 `orElse("Unknown")`으로 적는다.

> **`NullPointerException`(NPE)** — 값이 없는 자리(`null`)에 대고 무언가를 하려 할 때 나는 예외.\
> 예: 원문이 "Before" 코드로 보여 주는 `if (user != null)` 같은 검사 세 겹이 그것을 피하려는 코드이고, 원문은 이 절을 "수동 null 체크"라 부른다.

```java
// Before (Java 7): 수동 null 체크
public String getCityName(User user) {
    if (user != null) {
        Address addr = user.getAddress();
        if (addr != null) {
            City city = addr.getCity();
            if (city != null) {
                return city.getName();
            }
        }
    }
    return "Unknown";
}
```

```java
// After (Java 8): Optional 체이닝
public String getCityName(User user) {
    return Optional.ofNullable(user)
            .map(User::getAddress)
            .map(Address::getCity)
            .map(City::getName)
            .orElse("Unknown");
}
```

두 블록은 같은 메서드를 두 방식으로 적은 것이다.\
위 블록의 `if` 세 겹(`user`·`addr`·`city`)이 아래 블록의 `.map` 세 번(`User::getAddress`·`Address::getCity`·`City::getName`)과 짝을 이루고, 위 블록 마지막 줄의 `return "Unknown";`이 아래 블록의 `.orElse("Unknown")`이 된다.\
원문이 두 블록 첫 줄 주석에 붙인 이름이 각각 "수동 null 체크"와 "Optional 체이닝"이다.

### Nashorn JavaScript 엔진 (JEP 174)

- 기존 Rhino 엔진을 대체하는 고성능 JavaScript 런타임. `invokedynamic` 기반으로 JVM 위에서 ECMAScript를 실행.
- 명령행 도구 `jjs` 제공, `javax.script` API를 통해 자바와 상호 운용. (이후 Java 11에서 deprecated, Java 15에서 제거됨.)

**언제까지 쓸 수 있었나** — 원문이 둘째 불릿 괄호 안에 적은 그대로다: 이후 Java 11에서 deprecated, Java 15에서 제거됨.

> **재서술자 주:** 이 괄호는 같은 시리즈의 뒤 편들과 그대로 맞는다. `java-11.md`가 "JEP 335 — Nashorn 자바스크립트 엔진 deprecate"를 적고, `java-15.md`가 "Nashorn JavaScript 엔진 제거 (JEP 372)"를 적는다.

> **deprecated(사용 중단 예고)** — 아직 동작하지만 앞으로 없앨 예정이니 쓰지 말라고 표시해 둔 상태.\
> 예: 원문에 따르면 Nashorn이 나중에(Java 11) 이 표시를 받고, Java 15에서 제거된다.

### PermGen 제거 → Metaspace (JEP 122)

- 클래스 메타데이터를 보관하던 힙 내부 영역 PermGen(Permanent Generation)을 완전히 제거.
- 클래스 메타데이터를 네이티브 메모리 영역인 **Metaspace**로 이동. 크기를 튜닝하기 어렵고 `OutOfMemoryError: PermGen space`를 자주 유발하던 문제를 완화했고, 기본적으로 가용 네이티브 메모리까지 자동 확장(`-XX:MaxMetaspaceSize`로 상한 지정 가능).

**왜 이것이 나왔나** — 원문이 둘째 불릿에서 PermGen의 문제로 든 둘이다: 크기를 튜닝하기 어렵다는 것, 그리고 `OutOfMemoryError: PermGen space`를 자주 유발한다는 것.

> **클래스 메타데이터(class metadata)** — 클래스 자체에 대한 정보(어떤 메서드·필드가 있는지 등)를 JVM이 따로 보관해 둔 것.\
> 예: 원문에 따르면 이것을 Java 8 이전에는 힙 안의 PermGen에 두었고, Java 8부터는 네이티브 메모리의 Metaspace에 둔다.

> **네이티브 메모리(native memory)** — 자바 힙 바깥, 운영체제가 직접 내주는 메모리.\
> 예: 원문이 Metaspace를 이 영역이라 적고, 크기에 대해 "가용 네이티브 메모리까지 자동 확장"된다고 적는다(상한은 `-XX:MaxMetaspaceSize`로 지정).

### 타입 어노테이션 (JSR 308, JEP 104)

- 어노테이션을 선언 위치뿐 아니라 타입이 사용되는 모든 곳(제네릭 타입 인자, 캐스트, `throws`, `new` 등)에 붙일 수 있게 확장.
- `ElementType.TYPE_USE`, `TYPE_PARAMETER` 추가. Checker Framework 같은 정적 분석 도구의 토대가 되었다.

> **어노테이션(annotation)** — 코드에 붙여 두는 표시. 컴파일러나 도구가 그 표시를 읽고 쓴다.\
> 예: 아래 코드의 `@NonNull`·`@Readonly`가 그것이고, 원문이 이 표시를 읽는 도구로 든 것이 Checker Framework다.

> **정적 분석(static analysis)** — 프로그램을 돌려 보지 않고 코드만 읽어서 문제를 찾아내는 것.\
> 예: 원문은 타입 어노테이션이 "Checker Framework 같은 정적 분석 도구의 토대가 되었다"고 적는다.

```java
List<@NonNull String> strings;        // 제네릭 타입 인자에 어노테이션
@Readonly Document doc = ...;
String s = (@NonNull String) obj;     // 캐스트에 어노테이션
```

위 코드에는 원문이 첫 불릿에 넷으로 나열한 자리 가운데 둘이 주석으로 이름 붙어 있다 — "제네릭 타입 인자에 어노테이션", "캐스트에 어노테이션". 나머지 둘(`throws`, `new`)은 목록에만 있고 이 코드에는 나오지 않는다.

### CompletableFuture (java.util.concurrent)

- 기존 `Future`의 한계(블로킹 `get()`, 조합 불가)를 극복한 비동기 프로그래밍 API.
- 콜백 체이닝(`thenApply`, `thenAccept`, `thenCompose`), 조합(`thenCombine`, `allOf`, `anyOf`), 예외 처리(`exceptionally`, `handle`)를 선언적으로 표현.

**왜 이것이 나왔나** — 원문이 첫 불릿 괄호 안에 둘로 적은 기존 `Future`의 한계다: 블로킹 `get()`, 그리고 조합 불가.

> **비동기(asynchronous)** — 결과가 나올 때까지 그 자리에서 기다리지 않고, 결과가 준비되면 이어서 할 일을 미리 적어 두는 방식.\
> 예: 아래 코드에서 `supplyAsync(...)`가 결과를 기다리지 않고 돌아오고, 그 뒤에 할 일을 `.thenApply(...)`·`.thenAccept(...)`로 적어 둔다.

> **콜백 체이닝(callback chaining)** — 다음에 할 일을 점(`.`)으로 이어 붙여 적는 것.\
> 예: 원문이 이 이름으로 든 메서드가 `thenApply`·`thenAccept`·`thenCompose`이고, 아래 코드에 앞의 둘이 실제로 이어져 있다.

```java
CompletableFuture.supplyAsync(() -> fetchUser(id))
        .thenApply(User::getName)
        .thenAccept(System.out::println)
        .exceptionally(ex -> { ex.printStackTrace(); return null; });
```

위 코드의 마지막 줄 `.exceptionally(...)`가 원문이 셋째 묶음으로 든 "예외 처리(`exceptionally`, `handle`)" 가운데 하나다. 둘째 묶음인 조합(`thenCombine`, `allOf`, `anyOf`)은 목록에만 있고 이 코드에는 나오지 않는다.

## 그 외 변경 / API 추가
- **Collectors / Collections 강화**: `Collectors.groupingBy`, `partitioningBy`, `joining`, `toMap`; `Map.getOrDefault`, `computeIfAbsent`, `merge`, `forEach`; `Iterable.forEach`, `Collection.removeIf`.
- **Compact Profiles (JEP 161)**: `compact1/2/3` 프로파일로 임베디드 환경용 축소 런타임 제공.
- **StringJoiner / String.join**: 구분자 기반 문자열 결합.
- **Arrays.parallelSort**: 병렬 정렬.
- **Base64**: 표준 `java.util.Base64` 인코더/디코더 추가.
- **Concurrent 개선**: `ConcurrentHashMap` 재설계, `LongAdder`, `StampedLock`.
- **JVM/도구**: `jdeps` 의존성 분석 도구 추가, `invokedynamic` 활용 확대.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 불릿은 원문 두 문단을 나눠 적은 것이다.)*

- Java 8은 "현대 자바의 시작점"으로 평가된다.
- 람다와 Stream API는 자바 코드의 작성 방식 자체를 명령형에서 선언형·함수형으로 이동시켰고, 동작 파라미터화·지연 평가·병렬화 같은 개념을 주류 엔터프라이즈 개발에 정착시켰다.
- `java.time`은 날짜/시간 처리의 사실상 표준이 되었고, `Optional`은 null 안전성 문화를 확산시켰다.
- 엔터프라이즈 생태계에서 Java 8은 가장 광범위하고 오래 사용된 버전이 되었다.
- 안정성과 풍부한 지원, 그리고 이후 도입된 모듈 시스템(Java 9)으로의 마이그레이션 부담 때문에, 수많은 조직이 오랫동안 Java 8에 머물렀다. 이 "Java 8 고착" 현상은 역설적으로 이 릴리스의 완성도와 영향력을 방증한다.
- Spring, Hadoop, Android(일부) 등 거의 모든 주요 프레임워크가 람다·스트림을 전제로 API를 재설계하면서, Java 8은 자바 역사의 분기점으로 남았다.

## 용어 풀이

- **LTS(Long-Term Support)** — 한 버전을 오래 지원해 주기로 정해 두는 제도. 원문은 현대적 LTS 모델의 시작을 "Java 11부터"로 적고, Java 8은 그 이전이지만 상용·확장 지원으로 "사실상" 장기 지원으로 취급된다고 적는다.
- **boilerplate(장황한 상용구)** — 하는 일에 비해 매번 똑같이 길게 적어야 하는 코드. 원문이 든 예가 "익명 클래스로 콜백 하나를 넘기는 데 5~6줄".
- **콜백(callback)** — 지금 실행하지 않고 넘겨 두었다가 나중에 대신 불러 달라고 건네는 코드 조각.
- **멀티코어(multi-core)** — CPU 안에 계산하는 코어가 여럿 있는 것. 원문은 `parallelStream()`을 "멀티코어 활용을 데이터 구조 수준에서 추상화"한 것으로 적는다.
- **람다 표현식(lambda expression)** — 이름 없이 "받는 것 -> 하는 일"만 적어 둔 함수. 원문 표현으로 "함수를 값처럼 전달할 수 있게 하는 익명 함수 문법".
- **동작 파라미터화(behavior parameterization)** — 값이 아니라 할 일 자체를 인자로 넘기는 것. 원문은 이것이 "익명 클래스의 장황함을 제거했다"고 적는다.
- **함수형 인터페이스 / SAM(Single Abstract Method)** — 추상 메서드가 정확히 하나인 인터페이스. 원문 표현으로 "람다의 타깃 타입이 된다".
- **추상 메서드(abstract method)** — 이름과 모양만 정하고 몸통은 비워 둔 메서드.
- **타깃 타입(target type)** — 람다를 적은 자리가 요구하는 타입. 람다는 그 타입의 인스턴스로 변환된다.
- **`@FunctionalInterface`** — 함수형 인터페이스로 쓰겠다는 의도를 적어 두는 어노테이션. 원문 표현으로 "컴파일러 검증을 받는다".
- **메서드 참조(`::`)** — 이미 있는 메서드를 가리켜 람다 자리에 놓는 축약 문법. 원문이 든 형태가 4가지다.
- **선언적(declarative)** — "어떻게"의 절차 대신 "무엇을"을 적는 방식. 원문은 스트림 파이프라인을 이 말로 부르고, 그 반대쪽 코드를 "명령형 루프"라 부른다.
- **중간 연산 / 최종 연산** — 파이프라인 도중 단계(원문 표현 intermediate, lazy) / 파이프라인을 끝맺는 단계(원문 표현 terminal).
- **지연(lazy) 평가** — 결과가 필요해질 때까지 계산을 미뤄 두는 것. 원문 표현으로 최종 연산 호출 전까지 중간 연산은 "실제로 실행되지 않는다".
- **`default` 메서드** — 인터페이스 안에 몸통까지 적어 둔 메서드. 원문 주석으로 "구현체가 오버라이드하지 않아도 됨".
- **인터페이스 진화(interface evolution)** — 기존 인터페이스에 새 메서드를 "기존 구현체를 깨뜨리지 않고" 넣는 방식. 원문은 이것을 Stream API 도입의 전제 조건으로 든다.
- **불변(immutable)** — 한 번 만들어지면 내용이 바뀌지 않는 것. 원문 주석으로 `plusWeeks(1)`은 "새 객체 반환 (불변)"이다.
- **스레드 안전(thread-safe)** — 여러 갈래가 동시에 써도 어긋나지 않는 성질. 원문은 `SimpleDateFormat`을 "스레드 안전하지 않음"으로 적는다.
- **`Optional<T>`** — 값이 있을 수도/없을 수도 있음을 타입으로 표현한 컨테이너. 원문 표현으로 NPE를 "줄이고" 의도를 명시한다.
- **`NullPointerException`(NPE)** — 값이 없는 자리에 대고 무언가를 하려 할 때 나는 예외.
- **deprecated(사용 중단 예고)** — 아직 동작하지만 앞으로 없앨 예정이라 표시해 둔 상태. 원문은 Nashorn이 Java 11에서 이렇게 되고 Java 15에서 제거된다고 적는다.
- **클래스 메타데이터(class metadata)** — 클래스 자체에 대한 정보를 JVM이 따로 보관해 둔 것. PermGen에서 Metaspace로 옮겨 간 것이 이것이다.
- **네이티브 메모리(native memory)** — 자바 힙 바깥, 운영체제가 직접 내주는 메모리. Metaspace가 놓인 영역이다.
- **어노테이션(annotation)** — 코드에 붙여 두는 표시. 이 편에서 붙일 수 있는 자리가 "타입이 사용되는 모든 곳"으로 넓어졌다.
- **정적 분석(static analysis)** — 돌려 보지 않고 코드만 읽어 문제를 찾는 것. 원문이 든 도구가 Checker Framework다.
- **비동기(asynchronous)** — 결과를 그 자리에서 기다리지 않고, 준비되면 이어서 할 일을 미리 적어 두는 방식.
- **콜백 체이닝(callback chaining)** — 다음에 할 일을 점으로 이어 붙여 적는 것. 원문이 든 메서드가 `thenApply`·`thenAccept`·`thenCompose`다.

## 참고 출처
- [JSR 337: Java SE 8 (JCP)](https://jcp.org/en/jsr/detail?id=337)
- [JSR 337 Specification (OpenJDK)](https://cr.openjdk.org/~mr/se/8/java-se-8-pr-spec/)
- [JDK 8 Project (OpenJDK)](https://openjdk.org/projects/jdk8/)
- [Java SE 8 is Now Available (Oracle Blog)](https://blogs.oracle.com/java/post/java-se-8-is-now-available)
- [Java 8 Arrives (ADTmag, 2014-03-18)](https://adtmag.com/articles/2014/03/18/java-8-arrives.aspx)
- [Where Has the Java PermGen Gone? (InfoQ)](https://www.infoq.com/articles/Java-PERMGEN-Removed/)
- [JSR 308: Annotations on Java Types (JCP)](https://jcp.org/en/jsr/detail?id=308)
- [Java version history (Wikipedia)](https://en.wikipedia.org/wiki/Java_version_history)
