# java/syntax/60 — `null` 다루기: `Objects.requireNonNull`·`Optional` 의 경계 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·예외는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> `60-a`·`60-c` 는 **17.0.13 · 25.0.1** 에서도 출력이 같았고, `60-b` 는 **한 줄이 달랐다**\
> (애너테이션의 `toString` — 아래 7번). **관찰이지 보장이 아니다.**\
> JDK 소스 인용은 `lib/src.zip` 의 `Objects.java`·`Collectors.java` 원문이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 방어 시점 셋은 어디이고 각각 무엇을 쓰는가

```text
  자리                   도구                          무엇을 얻나
  ---------------------------------------------------------------------------
  ① 경계                 형식·필수값 검증               안쪽이 null 을 안 본다
     (컨트롤러·파서·      + 정규화
      외부 API 응답)

  ② 생성자·팩토리         Objects.requireNonNull        잘못된 객체가 안 만들어진다
     (도메인 객체 생성)   (메시지를 반드시 준다)         스택이 생성 지점을 가리킨다 ★

  ③ 반환값               Optional<T>                   호출자가 "없음" 을
     (조회 메서드)        (null 을 절대 안 돌려준다)     시그니처로 안다
```

**막는 것과 알리는 것**

| | 하는 일 | 도구 |
|---|---|---|
| **막는다** | 잘못된 값이 더 못 가게 한다 | ① 경계 검증 · ② `requireNonNull`·예외 |
| **알린다** | "없을 수 있다"를 호출자에게 전한다 | ③ `Optional` |

- ★ **`Optional` 은 막지 않는다.** 봉투 자체가 `null` 일 수 있고, 호출자가 `orElse` 로 넘길 수도 있다([`../38-optional/`](../38-optional/)).

**하나로 합치려 하면**

```text
  전부 Optional 로                            전부 requireNonNull 로
  +-----------------------------------+      +-----------------------------------+
  | 필수값도 봉투에 담긴다             |      | "없어도 되는 조회" 까지 터진다     |
  | 호출자가 orElse(기본값) 로         |      | 정상 흐름이 예외가 된다            |
  |   조용히 넘긴다 ★                 |      | 호출자가 try/catch 로 흐름을 짠다  |
  | 필드·파라미터까지 번진다           |      |                                   |
  +-----------------------------------+      +-----------------------------------+
```

- ★ **②는 "있어야만 하는 값", ③은 "없어도 정상인 값"** 이다. 이 구분이 먼저다.
- 예외와 값의 경계는 [`../25-exceptions/`](../25-exceptions/) 가 정본이다.

### 2. ★ 이 두 클래스는 언제 터지고 스택이 어디를 가리키는가

**출력** (`Ex.java (60-a)`, JDK 21.0.5 — 17·25 동일)

```text
--- 1. 언제 터지나 — 방어 시점이 스택을 바꾼다 ---
new Lazy(null)  : 생성 성공. lazy.name = null
  lazy.len()    -> NPE: Cannot invoke "String.length()" because "this.name" is null
  터진 자리      : Ex$Lazy.len <- Ex.main
new Eager(null) -> NPE: name 은 null 일 수 없다
  터진 자리      : java.util.Objects.requireNonNull <- Ex$Eager.<init>
```

**`new Lazy(null)` 은 성공한다**

- ★ **이것이 문제의 전부다.** `null` 을 품은 객체가 만들어져 그대로 살아 나간다.
- `lazy.name` 이 `null` 인 채로 리스트에 들어가고, 캐시에 저장되고, 다른 스레드로 넘어갈 수 있다.

**NPE 시점과 스택 맨 위 두 프레임**

| | 터지는 시점 | 스택 맨 위 두 프레임 |
|---|---|---|
| `Lazy` | **`len()` 을 부를 때** — 생성과 무관한 나중 | `Ex$Lazy.len` <- `Ex.main` |
| `Eager` | **생성자 안에서 즉시** | `java.util.Objects.requireNonNull` <- **`Ex$Eager.<init>`** |

**두 메시지**

- `Lazy` : `Cannot invoke "String.length()" because "this.name" is null` — JVM 이 만든 helpful NPE
- `Eager` : `name 은 null 일 수 없다` — **내가 쓴 문장**

```text
  방어 없음                                    생성자에서 requireNonNull
  +-----------------------------------+       +-----------------------------------+
  | new Lazy(null)   -> 성공 ★        |       | new Eager(null)  -> 즉시 NPE      |
  |                                   |       |                                   |
  | ... 리스트에 담기고 ...            |       | 스택 두 번째 프레임이             |
  | ... 캐시에 저장되고 ...            |       |   Ex$Eager.<init>  = 생성 지점 ★  |
  | ... 한참 뒤 ...                    |       |                                   |
  | lazy.len()       -> NPE           |       | 그 아래 한 칸을 더 보면           |
  |                                   |       |   누가 null 을 넘겼는지 나온다     |
  | 스택에 "누가 넣었나" 가 없다 ★     |       |                                   |
  +-----------------------------------+       +-----------------------------------+
```

**`Lazy` 쪽이 더 나쁜 이유 한 문장**

> **증상이 원인에서 떨어져 있어, 스택 트레이스에 `null` 을 넣은 코드가 한 줄도 없다.**

- 게다가 그 객체를 **직렬화·로그·다른 스레드**로 흘려보낸 뒤라면 원인 추적이 사실상 끝난다.

### 3. `requireNonNull` 의 세 형태는 메시지가 어떻게 다른가

**출력** (`Ex.java (60-a)`, JDK 21.0.5 — 17·25 동일)

```text
--- 3. requireNonNull 의 세 형태 ---
requireNonNull(null)              -> NPE 메시지 = null
requireNonNull(null, "...")       -> NPE 메시지 = 직접 쓴 메시지
requireNonNull(null, 공급자)       -> NPE 메시지 = 공급자가 만든 메시지
```

**세 `getMessage()`**

| 호출 | `getMessage()` |
|---|---|
| `requireNonNull(null)` | **`null`** (메시지 없음) |
| `requireNonNull(null, "직접 쓴 메시지")` | `직접 쓴 메시지` |
| `requireNonNull(null, () -> "...")` | `공급자가 만든 메시지` |

**첫째가 그런 이유 — 소스 그대로**

```java
// JDK 21.0.5  java.base/java/util/Objects.java  230~235행 — 실제 소스 그대로
@ForceInline
public static <T> T requireNonNull(T obj) {
    if (obj == null)
        throw new NullPointerException();
    return obj;
}
```

- `new NullPointerException()` — **인자가 없는 생성자**라 메시지가 `null` 이다.
- 그래서 스택 행 번호 말고는 단서가 없다.

**셋째(`Supplier`)를 쓸 자리**

- **메시지를 만드는 비용이 클 때**만이다 — 문자열 이어붙이기, 조회, 포맷팅.
- `"name"` 같은 리터럴이면 **둘째가 낫다.** `Supplier` 는 람다 객체를 하나 더 만든다.
- 판단 기준이 `orElse` 대 `orElseGet` 과 똑같다(5번).

**javadoc 이 든 예제**

> This method is designed primarily for doing parameter validation in methods
> and constructors with multiple parameters, as demonstrated below:
> ```
> public Foo(Bar bar, Baz baz) {
>     this.bar = Objects.requireNonNull(bar, "bar must not be null");
>     this.baz = Objects.requireNonNull(baz, "baz must not be null");
> }
> ```

- ★ **javadoc 자신이 "인자가 여럿인 생성자"에 "메시지를 붙인" 형태를 예로 들었다.** 이것이 표준 형태다.

### 4. ★ 이 세 호출의 NPE 메시지는 각각 무엇인가

**출력** (`Ex.java (60-a)`, JDK 21.0.5 — 17·25 동일)

```text
--- 4. requireNonNullElse 와 requireNonNullElseGet ---
Else("값", "기본")       : 값
Else(null, "기본")       : 기본
Else(null, null)         -> NPE 메시지 = defaultObj
ElseGet(null, ()->null)  -> NPE 메시지 = supplier.get()
ElseGet(null, null)      -> NPE 메시지 = supplier
```

**세 메시지**

| 호출 | 메시지 |
|---|---|
| `requireNonNullElse(null, null)` | **`defaultObj`** |
| `requireNonNullElseGet(null, () -> null)` | **`supplier.get()`** |
| `requireNonNullElseGet(null, null)` | **`supplier`** |

**어디서 오는가 — 소스 그대로**

```java
// JDK 21.0.5  java.base/java/util/Objects.java  313~315 · 332~335행 — 실제 소스 그대로
public static <T> T requireNonNullElse(T obj, T defaultObj) {
    return (obj != null) ? obj : requireNonNull(defaultObj, "defaultObj");
}

public static <T> T requireNonNullElseGet(T obj, Supplier<? extends T> supplier) {
    return (obj != null) ? obj
            : requireNonNull(requireNonNull(supplier, "supplier").get(), "supplier.get()");
}
```

- ★ **세 문자열이 전부 소스의 리터럴**이다. 지어낸 것이 아니라 JDK 가 심어 놓은 라벨이다.
- `requireNonNullElseGet` 은 `requireNonNull` 을 **두 번 중첩**해 부른다 — 안쪽이 `supplier`, 바깥이 `supplier.get()`.

**메시지만 보고 구분할 수 있는가**

```text
  메시지            무엇이 null 이었나                  고칠 자리
  -------------------------------------------------------------------------
  defaultObj        두 번째 인자(기본값) 자체가 null    기본값을 만드는 곳
  supplier          Supplier 를 null 로 넘겼다          호출 자리
  supplier.get()    Supplier 는 줬는데 null 을 돌려줬다  Supplier 의 본문
```

- ★ **된다.** 세 단계가 한 단어로 구분된다.
- 이것이 **메시지를 붙이는 관용구의 값어치**다 — JDK 도 자기 코드에 그렇게 한다.

### 5. ★ `requireNonNullElse` 의 두 번째 인자는 언제 평가되는가

**출력** (`Ex.java (60-a)`, JDK 21.0.5 — 17·25 동일)

```text
--- 5. Else 는 즉시 평가, ElseGet 은 필요할 때만 ---
Else("값", make())    = 값 / make() 호출 = 1
ElseGet("값", make)   = 값 / make() 호출 = 0
ElseGet(null, make)   = 만들어진 기본값 / make() 호출 = 1
```

**세 경우의 호출 횟수**

| | 호출 횟수 |
|---|---|
| (A) `requireNonNullElse("값", make())` | **1회** ★ 결과에 안 쓰였는데도 |
| (B) `requireNonNullElseGet("값", Ex::make)` | **0회** |
| (C) `requireNonNullElseGet(null, Ex::make)` | 1회 |

```text
  requireNonNullElse(x, make())              requireNonNullElseGet(x, Ex::make)
  +-----------------------------------+      +-----------------------------------+
  | 1. make() 를 먼저 부른다 ★        |      | 1. Supplier 만 만든다             |
  | 2. 그 반환값을 인자로 넘긴다       |      | 2. x 가 null 이 아니면            |
  | 3. x 가 null 이 아니면 x 를 반환   |      |    supplier.get() 을 안 부른다    |
  | -> 만든 것을 버렸다                |      |                                   |
  +-----------------------------------+      +-----------------------------------+
```

**원인은 `Objects` 의 구현인가**

- ★ **아니다. 자바의 인자 평가 규칙**이다. 메서드를 부르려면 **인자를 먼저 평가해야** 한다.
- 자바에는 지연 인자가 없으므로, 지연을 만들려면 **함수로 감싸는 수밖에** 없다.
  그래서 `Supplier` 를 받는 짝이 따로 존재한다.
- 인자 평가 규칙의 정본은 [`../03-variables-and-assignment/`](../03-variables-and-assignment/), `Supplier` 는 [`../31-functional-interfaces/`](../31-functional-interfaces/).

**같은 현상을 보이는 다른 API**

| 즉시 평가 | 지연 |
|---|---|
| `Optional.orElse(x)` | `Optional.orElseGet(sup)` |
| `Objects.requireNonNullElse(x, def)` | `Objects.requireNonNullElseGet(x, sup)` |
| `Objects.requireNonNull(x, "msg")` | `Objects.requireNonNull(x, sup)` |
| `Map.getOrDefault(k, v)` | `Map.computeIfAbsent(k, fn)` |
| `log.debug("x=" + heavy())` | `log.debug("x={}", heavy)` (플레이스홀더) |

- ★ **자바 전체에 같은 모양이 반복된다.** 하나를 이해하면 나머지가 따라온다.
- 판정 기준도 같다 — **리터럴·상수면 즉시형, 계산·조회·객체 생성이면 지연형.**

### 6. ★ NPE 메시지는 무엇에 갈리는가

**출력** (`Ex.java (60-c)`, JDK 21.0.5 — 17·25 동일)

```text
==== javac -g ====
[1] 그냥 역참조  : Cannot invoke "String.length()" because "s" is null
[2] requireNonNull: name
==== javac (기본, -g 없음) ====
[1] 그냥 역참조  : Cannot invoke "String.length()" because "<local1>" is null
[2] requireNonNull: name
==== java -XX:-ShowCodeDetailsInExceptionMessages ====
[1] 그냥 역참조  : null
[2] requireNonNull: name
```

**[1] 은 세 조건에서 전부 다르다**

| 조건 | 메시지 |
|---|---|
| `javac -g` | `... because "s" is null` — **변수 이름** |
| `javac`(기본) | `... because "<local1>" is null` — **슬롯 번호** |
| `-XX:-ShowCodeDetailsInExceptionMessages` | **`null`** — 통째로 사라진다 |

- 같은 성격의 실측을 배열로 한 것이 [`../05-arrays/`](../05-arrays/) 에 있다(세 JDK × 세 조건). 여기서는 **결론만 받았다.**

**[2] 는 세 조건에서 전부 같다**

- ★ **`name` 이 그대로 나온다.** 빌드 옵션도 JVM 플래그도 영향을 못 준다.

```text
  helpful NPE 메시지                        requireNonNull 메시지
  +-----------------------------------+    +-----------------------------------+
  | JVM 이 바이트코드를 읽어 만든다    |    | 내가 소스에 쓴 문자열이다          |
  | -g 없으면 <local1>                |    | 빌드 옵션과 무관                  |
  | 플래그 끄면 null                  |    | JVM 플래그와 무관                 |
  | 버전마다 문구가 바뀔 수 있다       |    | 내가 안 바꾸면 안 바뀐다           |
  +-----------------------------------+    +-----------------------------------+
        환경에 흔들린다                          ★ 흔들리지 않는다
```

**"명시적 검증을 쓰는 이유"가 되는 까닭**

- 운영 환경의 **빌드 설정과 JVM 옵션을 내가 못 정할 때가 많다.** 컨테이너 이미지·CI 설정·운영팀의 튜닝이 정한다.
- 그 상황에서 helpful NPE 는 `<local1>` 이나 `null` 로 줄어들 수 있다.
- `requireNonNull(x, "x")` 의 메시지는 **내 소스에 박혀 있어** 그 변동을 타지 않는다.

**하면 안 되는 것**

> **NPE 메시지 문자열에 의존하는 코드·테스트를 쓰지 않는다.** 어느 쪽이든.

- helpful NPE 는 환경에 갈리고, `requireNonNull` 메시지도 **내가 리팩토링하면 바뀐다.**
- 테스트는 **예외 타입**으로 하고, 메시지는 사람이 읽는 용도로만 둔다.

> **helpful NullPointerException** — NPE 메시지에 "어느 식이 `null` 이었는지"를 적어 주는 기능(JEP 358, Java 14. 15부터 기본 켜짐).\
> 예: `Cannot invoke "String.length()" because "s" is null`.

### 7. ★ `@NonNull` 애너테이션은 런타임에 무엇을 막는가

**출력** (`Ex.java (60-b)`, JDK 21.0.5)

```text
--- 1. @NonNull 은 런타임에 아무것도 막지 않는다 ---
메서드 파라미터의 애너테이션 : [@Ex.NonNull()]
len(null) 은 컴파일된다 -> 실행하면 NPE: Cannot invoke "String.length()" because "s" is null
```

**컴파일되는가**

- ★ **그냥 컴파일된다.** 경고도 없다.

**실행하면**

- `s.length()` 에서 **평범한 NPE** 가 난다. 애너테이션은 아무 역할도 안 했다.
- 애너테이션이 **런타임에 읽히기는 한다** — `@Retention(RUNTIME)` 이라 `getParameterAnnotations()` 가 `[@Ex.NonNull()]` 을 돌려줬다.\
  읽히기만 하고 **검사는 아무도 안 한다.**

```text
  애너테이션이 하는 일                   애너테이션이 안 하는 일
  +-----------------------------------+  +-----------------------------------+
  | 클래스 파일에 정보를 남긴다        |  | 컴파일을 막는다                   |
  |   RUNTIME 이면 리플렉션으로 읽힘   |  | 런타임에 검사한다                 |
  | 정적 분석 도구가 읽는다            |  | NPE 를 막는다                     |
  | IDE 가 경고를 띄운다               |  |                                   |
  +-----------------------------------+  +-----------------------------------+
     ★ 애너테이션은 메타데이터다. 검사를 하는 것은 그것을 읽는 도구다
```

**의미 있으려면 필요한 것**

1. **애너테이션을 읽는 도구가 빌드에 붙어 있어야 한다** — ErrorProne + NullAway, SpotBugs, IDE 인스펙션, 스프링의 `@Validated`.\
   그 도구가 없으면 **주석과 다를 바 없다.**
2. **팀이 하나를 골라야 한다.** `@Nullable`/`@NonNull` 은 **표준이 아니다** —
   `jakarta.annotation`·`org.jetbrains.annotations`·`javax.annotation`(JSR-305)·`org.springframework.lang` 등이 각자 있다.
3. **런타임 보장이 필요하면 `Objects.requireNonNull` 을 쓴다.** 애너테이션은 그 위에 얹는 문서다.

★ **이 한 줄만 JDK 마다 출력이 달랐다.**

```text
JDK 17.0.13 : 메서드 파라미터의 애너테이션 : [@Ex$NonNull()]
JDK 21.0.5  : 메서드 파라미터의 애너테이션 : [@Ex.NonNull()]
JDK 25.0.1  : 메서드 파라미터의 애너테이션 : [@Ex.NonNull()]
```

- 중첩 애너테이션 타입의 이름이 **이진 이름(`Ex$NonNull`)에서 정규 이름(`Ex.NonNull`)으로** 바뀌었다.
- `Annotation.toString()` 의 형식은 명세가 고정하지 않았으므로 이런 변화가 허용된다.
- **애너테이션의 `toString` 을 파싱·비교하는 코드를 쓰면 안 된다.**
- 애너테이션 선언·`@Retention`·`@Target` 자체는 [**16번 주제**](../16-annotations/)가 정본이다.

### 8. 컬렉션마다 `null` 정책이 어떻게 다른가

**출력** (`Ex.java (60-b)`, JDK 21.0.5 — 17·25 동일)

```text
--- 2. 컬렉션마다 null 정책이 다르다 ---
HashMap.put(null, null)        : {null=null}  size=1
HashMap.get("없는키")          : null  (없는 것과 null 값이 같은 모양)
containsKey 로만 구분된다       : true / false
Map.of("a", null)              -> java.lang.NullPointerException: null
List.of("a", null)             -> java.lang.NullPointerException: null
Arrays.asList("a", null)       : [a, null]
new ArrayList<>(...)           : [a, null]  contains(null)=true
TreeSet 에 null                 -> java.lang.NullPointerException: null
```

**성공하는 것과 NPE**

| 호출 | 결과 |
|---|---|
| `new HashMap<>().put(null, null)` | **성공** — `{null=null}`, `size=1` |
| `Map.of("a", null)` | **NPE** |
| `List.of("a", null)` | **NPE** |
| `Arrays.asList("a", null)` | **성공** — `[a, null]` |
| `new TreeSet<>(Arrays.asList("a", null))` | **NPE** |

```text
  null 을 받는다                             null 을 거부한다
  +-----------------------------------+      +-----------------------------------+
  | HashMap (키 1개 · 값 무제한)      |      | Map.of / List.of / Set.of         |
  | ArrayList · Arrays.asList         |      |   -> 불변 팩토리는 전부 거부       |
  | LinkedList · HashSet              |      | TreeSet / TreeMap (키)            |
  +-----------------------------------+      +-----------------------------------+
        옛 컬렉션                                 9 이후의 불변 팩토리 + 정렬 컬렉션
```

**`HashMap` 에서 둘을 구분하는 법**

- `get` 으로는 **구분 안 된다.** "키가 없다"도 `null`, "값이 `null` 이다"도 `null` 이다.
- **`containsKey(k)`** 를 봐야 한다 — 실측에서 `true` / `false` 로 갈렸다.
- 아니면 **`getOrDefault(k, 기본값)`** 로 둘을 한 답으로 합친다([**41번 주제**](../41-map-api-merge-compute/)).

**`TreeSet` 이 거부하는 이유**

- ★ **`compareTo(null)` 이 NPE 여야 하기 때문**이다. `TreeSet` 은 원소를 넣을 때 반드시 비교하는데, `null` 은 비교할 수가 없다.
- `Comparable` javadoc 원문: "`e.compareTo(null)` should throw a `NullPointerException`".
- 정렬에 `null` 을 넣어야 하면 **`Comparator.nullsFirst`/`nullsLast`** 로 감싼 비교자를 준다.
- 정본은 [`../28-comparable-comparator/`](../28-comparable-comparator/).

### 9. 스트림 수집기의 `null` 정책은 어떻게 갈리는가

**출력** (`Ex.java (60-b)`·`Ex.java (60-d)`, JDK 21.0.5 — 17·25 동일)

```text
--- 3. 스트림 수집기의 null 정책 ---
Collectors.toMap  -> java.lang.NullPointerException: null
collect(HashMap::new, ...) : {a=1, b=null}
groupingBy 는 키가 null 이면 :
  -> java.lang.NullPointerException: element cannot be mapped to a null key

--- 4. 경계에서 걸러 내기 ---
원본                      : [a, null, b, null]
filter(Objects::nonNull)  : [a, b]
map(ofNullable).flatMap   : [a, b]
[a, null, b, null]
```

```text
stream().toList()                    : [x, null, y]
collect(Collectors.toList())         : [x, null, y]
collect(toUnmodifiableList())        -> java.lang.NullPointerException
List.copyOf(...)                     -> java.lang.NullPointerException
```

**NPE 가 나는 것**

| 호출 | 결과 |
|---|---|
| `Collectors.toMap(key, value)` — 값이 `null` | **NPE** (메시지 없음) |
| `Collectors.groupingBy(...)` — 키가 `null` | **NPE** |
| `stream().toList()` | **성공** — `null` 을 그대로 통과 |
| `collect(Collectors.toUnmodifiableList())` | **NPE** |
| `List.copyOf(...)` | **NPE** |

**`toMap` 이 터지는 이유 — 소스 그대로**

```java
// JDK 21.0.5  java.base/java/util/stream/Collectors.java  178~183행 — 실제 소스 그대로
return (map, element) -> {
    K k = keyMapper.apply(element);
    V v = Objects.requireNonNull(valueMapper.apply(element));
    V u = map.putIfAbsent(k, v);
    if (u != null) throw duplicateKeyException(k, u, v);
};
```

- ★ **JDK 자신이 이 주제의 관용구를 쓴다.** 다만 **메시지를 안 줬다** — 그래서 `NPE: null` 로 나온다.
- 우회하려면 3인자 `collect` 를 쓴다 — 실행으로 `{a=1, b=null}` 이 나왔다.

```java
rows.stream().collect(HashMap::new, (m, r) -> m.put(r.key(), r.value()), HashMap::putAll);
```

**`groupingBy` 의 메시지**

```text
java.lang.NullPointerException: element cannot be mapped to a null key
```

- ★ **`toMap` 과 달리 메시지가 있다.** 원인을 직접 말한다 — 키 쪽이 문제라는 것까지 알려 준다.
- `toMap` 의 다른 함정(키 충돌)은 [`../47-collectors-basics/`](../47-collectors-basics/) 가 정본이다.

**`toList()` 계열이 갈리는 기준**

> **불변 컬렉션을 만드는 쪽이 `null` 을 거부한다.**

| 만드는 것 | `null` |
|---|---|
| `Stream.toList()`(16+) · `Collectors.toList()` | **허용** |
| `Collectors.toUnmodifiableList()` · `List.copyOf` | **거부(NPE)** |

- `List.of`/`Map.of`/`Set.of` 와 같은 정책이다 — **9 이후의 불변 팩토리는 전부 `null` 을 거부한다.**
- ★ **"스트림을 거쳤으니 `null` 이 없겠지"는 틀린다.** 수집기를 무엇으로 쓰느냐가 정한다.
- 걸러야 하면 **`filter(Objects::nonNull)`** 한 줄이 가장 짧다.

### 10. 반환값을 `null` 로 줄 때와 `Optional` 로 줄 때

**출력** (`Ex.java (60-b)`, JDK 21.0.5 — 17·25 동일)

```text
--- 5. 반환값을 null 로 돌려주는 것과 Optional 로 돌려주는 것 ---
findNull("없음")           : null
findOpt("없음")            : Optional.empty
findOpt("없음").orElse(..) : 기본
findNull(..).length()      -> NPE: Cannot invoke "String.length()" because the return value of "Ex.findNull(String)" is null
```

**두 호출의 결과**

- `findNull("없음").length()` -> **NPE**
- `findOpt("없음").orElse("기본")` -> **`"기본"`**

**첫째의 NPE 메시지가 담은 정보**

```text
Cannot invoke "String.length()" because the return value of "Ex.findNull(String)" is null
                                                            ^^^^^^^^^^^^^^^^^^^^^^
                                                  ★ 어느 메서드가 null 을 줬는지
```

- ★ **helpful NPE 가 가장 쓸모 있는 자리**다 — "누가 `null` 을 줬나"를 메서드 시그니처까지 짚는다.
- 다만 **6번의 조건에 걸린다.** `-g` 없이 빌드하거나 플래그를 끄면 이 정보가 줄거나 사라진다.

**둘째에서 같은 사고가 없는 이유**

```text
  String findNull(String k)                  Optional<String> findOpt(String k)
  +-----------------------------------+      +-----------------------------------+
  | 반환값에 .length() 를 바로 쓸 수   |      | Optional 에는 length() 가 없다     |
  | 있다 -> 컴파일된다                 |      | -> 컴파일 에러                     |
  |                                   |      |                                   |
  | 호출자가 null 검사를 잊으면 NPE    |      | 꺼내려면 반드시 한 번 더           |
  |                                   |      |   orElse / map / orElseThrow      |
  +-----------------------------------+      +-----------------------------------+
        런타임 사고                                ★ 컴파일 단계에서 사라진다
```

- ★ **타입이 다르기 때문**이다. `Optional<String>` 에는 `length()` 가 없어서 그 사고를 **쓸 수가 없다.**
- 봉투를 열려면 `orElse`·`map`·`orElseThrow` 중 하나를 반드시 거쳐야 하고, 그때 "없을 때 무엇을 할지"를 적게 된다.

**반환 자리 밖에 쓰면 안 되는 이유**

- javadoc 이 용도를 **"primarily intended for use as a method return type"** 으로 지정했다.
- 필드에 두면 `NotSerializableException`, 파라미터로 두면 상태가 셋이 되고, 컬렉션 원소로 두면 `null` 이 그대로 남는다.
- **셋 다 실측이 [`../38-optional/`](../38-optional/) 에 있다.** 이 문서는 그 결론을 배치 판단으로만 쓴다.

### 11. 어디에 무엇을 쓰나

**세 자리의 도구**

| 상황 | 도구 |
|---|---|
| 필수 인자 검증(생성자·public 메서드) | **`Objects.requireNonNull(x, "x")`** — 메시지를 반드시 준다 |
| 선택 기본값 — 기본값이 상수 | `Objects.requireNonNullElse(x, DEFAULT)` |
| 선택 기본값 — 기본값을 만들어야 함 | **`Objects.requireNonNullElseGet(x, () -> ...)`** |
| 없을 수 있는 조회의 반환 | **`Optional<T>`** (반환 자리에만) |
| 없으면 계속 진행하면 안 됨 | **예외를 던진다** |
| 외부 입력(HTTP·JSON·DB) | **경계에서 검증·정규화** |

**컬렉션을 돌려주는 메서드**

> **빈 컬렉션을 돌려준다.** `null` 도 `Optional<List<T>>` 도 아니다.

- `List.of()` · `Collections.emptyList()` — 호출자가 그대로 `for` 를 돌 수 있다.
- `Optional<List<T>>` 는 상태가 셋(`null` 봉투 / 빈 봉투 / 빈 리스트)이 되어 **거의 항상 과하다.**
- 방어가 필요하면 받는 쪽에서 `Objects.requireNonNullElse(list, List.of())` 한 줄.

**`if (x != null)` 을 만나는 곳마다 붙이면**

```text
  검문소가 세 자리에 있을 때                검문소가 전체에 흩어질 때
  +-----------------------------------+    +-----------------------------------+
  | null 이 어디서 들어왔는지 안다     |    | 아무도 모른다                     |
  | 안쪽 코드는 null 을 안 본다        |    | 모든 줄이 null 을 의심한다         |
  | 한 곳만 고치면 된다                |    | 한 곳만 빠뜨려도 터진다 ★         |
  +-----------------------------------+    +-----------------------------------+
```

- 코드는 길어지는데 **버그는 그대로**다. 게다가 터지는 자리가 원인과 멀다.
- 게다가 `if (x != null) return;` 같은 조용한 무시가 섞이면 **`null` 이 결과에 스며든다.**

**`requireNonNull` 에 메시지를 안 주면**

- 인자가 여럿인 생성자에서 **무엇이 `null` 이었는지 스택 행 번호로만** 구분된다.
- 리팩토링하면 그 행 번호도 어긋난다.
- 인자 이름 하나면 충분하다 — `requireNonNull(bar, "bar")`.

### 12. 다른 주제와 잇기

**`Optional` 과 `requireNonNull` 의 차이**

```text
  Objects.requireNonNull                    Optional
  +-----------------------------------+     +-----------------------------------+
  | 막는다                            |     | 알린다                            |
  | "이 값은 있어야 한다"              |     | "이 값은 없을 수 있다"             |
  | 없으면 그 자리에서 예외            |     | 없으면 빈 봉투                    |
  | 쓰는 자리: 생성자·인자 검증        |     | 쓰는 자리: 반환 타입              |
  +-----------------------------------+     +-----------------------------------+
```

- ★ **둘은 반대 방향의 도구다.** 같은 값에 둘 다 쓸 일은 거의 없다.
- `Optional` 자체의 정본은 [`../38-optional/`](../38-optional/).

**`record` 에서 검증은 어디에**

**출력** (`Ex.java (60-a)`)

```text
--- 2. record 컴팩트 생성자 ---
정상               : Money[currency=KRW, amount=1000]
new Money(null, ..) -> NullPointerException: currency
new Money(.., -1)   -> IllegalArgumentException: amount 는 음수일 수 없다: -1
```

```java
record Money(String currency, long amount) {
    Money {                                                  // 컴팩트 생성자
        Objects.requireNonNull(currency, "currency");
        if (amount < 0) throw new IllegalArgumentException("amount 는 음수일 수 없다: " + amount);
    }
}
```

- ★ **컴팩트 생성자가 검증을 넣기 위한 자리**다. `record` 는 `final` 은 만들어 주지만 `null` 은 막아 주지 않는다.
- **예외 타입을 나눈다** — `null` 은 `NullPointerException`, 범위 위반은 `IllegalArgumentException`.\
  호출자가 둘을 구분해 처리할 수 있다.
- 정본은 [`../14-records/`](../14-records/).

**JDK 자신이 이 관용구를 쓰는 자리**

| 자리 | 소스 |
|---|---|
| `Optional.of` | `return new Optional<>(Objects.requireNonNull(value));` |
| `Optional.map` | `Objects.requireNonNull(mapper);` 로 시작 |
| `Objects.requireNonNullElse` | `requireNonNull(defaultObj, "defaultObj")` |
| `Objects.requireNonNullElseGet` | `requireNonNull(..., "supplier")` + `"supplier.get()"` |
| `Collectors.toMap` 의 누산기 | `V v = Objects.requireNonNull(valueMapper.apply(element));` |

- ★ **넷 중 셋은 메시지를 줬고, `Optional.of` 와 `Collectors.toMap` 은 안 줬다.**\
  그래서 `Optional.of(null)` 과 `toMap` 의 NPE 는 메시지가 `null` 이다 — 실측으로 확인된다.
- **JDK 안에서도 이 규율이 균일하지 않다**는 것이 오히려 교훈이다. 내 코드에서는 메시지를 준다.

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java (60-a)` | 방어 시점별 NPE 시점·스택 두 프레임·메시지, `record` 컴팩트 생성자, `requireNonNull` 세 형태, `Else`/`ElseGet` 의 세 NPE 메시지, `Else` 의 즉시 평가, `Objects` 유틸 | 17 · 21 · 25 (출력 동일) |
| `Ex.java (60-b)` | `@NonNull` 이 런타임에 아무것도 안 막음, 컬렉션별 `null` 정책, `toMap`/`groupingBy` 의 NPE, 경계에서 거르기, `null` 반환 대 `Optional` 반환 | 21 · 25 (동일) / **17은 첫 줄만 다름** ★ |
| `Ex.java (60-c)` `javac -g` / `javac` / `java -XX:-...` | helpful NPE 는 세 조건에서 전부 다르고, `requireNonNull` 메시지는 전부 같음 | **세 JDK × 세 조건 9회** — 조건별로 출력 동일 |
| `Ex.java (60-d)` | `stream().toList()`·`Collectors.toList()` 는 `null` 통과, `toUnmodifiableList()`·`List.copyOf` 는 NPE | 21 |
| `src.zip` 의 `Objects.java` | `@since`, `requireNonNull`·`requireNonNullElse(Get)` 의 실제 소스, javadoc 예제 원문 | 21.0.5 |
| `src.zip` 의 `Collectors.java` | `uniqKeysMapAccumulator` 의 `Objects.requireNonNull` 한 줄(178~183행) | 21.0.5 |

**★ 세 JDK 에서 유일하게 달랐던 한 줄** — `60-b` 의 애너테이션 `toString` 이다.

```text
JDK 17.0.13 : [@Ex$NonNull()]
JDK 21.0.5  : [@Ex.NonNull()]
JDK 25.0.1  : [@Ex.NonNull()]
```

**구현 의존 항목** — helpful NPE 의 문구, `requireNonNullElse(Get)` 의 메시지 문자열(`defaultObj`·`supplier`·`supplier.get()`),
`groupingBy` 의 `element cannot be mapped to a null key`, 애너테이션의 `toString` 형태, `Objects.java`·`Collectors.java` 의 행 번호 —
전부 **구현 세부**다. 버전이 올라 달라질 수 있으므로 그때 다시 돌린다.\
반면 "`requireNonNull` 은 `null` 이면 NPE"·"`requireNonNullElse` 는 기본값이 `null` 이어도 NPE"·
"`Map.of`/`List.of` 는 `null` 을 거부"·"`HashMap` 은 `null` 키 하나를 허용"은 **javadoc 의 계약**이고,
"`Else` 의 인자가 항상 평가되는 것"은 **JLS 의 인자 평가 규칙**이라 버전과 무관하다.
