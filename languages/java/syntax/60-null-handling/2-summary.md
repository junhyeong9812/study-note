# java/syntax/60 — `null` 다루기: `Objects.requireNonNull`·`Optional` 의 경계 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — JDK 21.0.5 표준 라이브러리 소스 `java.base/java/util/Objects.java` 의 **javadoc·`@since`·구현 원문**(`lib/src.zip` 에서 직접 인용) · `java.base/java/util/Optional.java` · [JEP 358 Helpful NullPointerExceptions](https://openjdk.org/jeps/358).
> **실행 검증** — 이 문서의 모든 출력·예외는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 실행 프로그램 셋(`Ex.java (60-a)`·`(60-b)`·`(60-c)`)을 **17.0.13 · 21.0.5 · 25.0.1** 세 곳에서 돌렸다.\
> ★ **`60-a`·`60-c` 는 출력이 같았고, `60-b` 는 한 줄이 달랐다** — 애너테이션의 `toString` 이 17에서는 `@Ex$NonNull()`,
> 21·25에서는 `@Ex.NonNull()` 이다(아래 「구현 세부사항 대 언어 보장」). **"세 곳에서 같았다"는 관찰이지 보장이 아니다.**
> **버전** — `Objects` 는 **Java 7**. `isNull`·`nonNull`·`requireNonNull(obj, Supplier)` 는 **8**,\
> `requireNonNullElse`·`requireNonNullElseGet`·`checkIndex`(`int` 판) 는 **9**, `checkIndex`(`long` 판) 는 **16**, `toIdentityString` 은 **19**(전부 `src.zip` 의 `@since` 확인).\
> helpful NullPointerException 은 **Java 14**(JEP 358), **15부터 기본 켜짐**.
> **범위** — `Optional` 이라는 **타입 하나**의 생성·소비·안티패턴은 [`../38-optional/`](../38-optional/) 가 정본이다.\
> 여기는 **"어느 계층에서 무엇으로 막을 것인가"** 라는 배치 문제만 다룬다.\
> NPE 메시지가 빌드 옵션·JVM 플래그에 갈린다는 실측은 [`../05-arrays/`](../05-arrays/) 가 정본이고, 여기서는 **결론만 받아 쓴다**((6)).
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**`null` 방어는 "어디에 검문소를 세우나" 문제다. 도구를 고르는 문제가 아니다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 건물에 들어오는 정문 | **경계** — 컨트롤러·파서·외부 API 응답을 받는 자리 |
| 정문의 검문소 | 경계 검증(형식·필수값 확인) |
| 사무실에 들어갈 때 신분증 확인 | **생성자**의 `Objects.requireNonNull` |
| 창고에서 물건을 찾아 없을 때 | **반환값**의 `Optional` |
| "없을 수도 있음" 이라고 적은 안내문 | `@Nullable` 애너테이션 — **안내일 뿐 문이 안 잠긴다** |
| 검문 없이 들여보냈다가 3층에서 사고 | 늦게 터지는 NPE — 원인과 멀다 |

- ★ **세 자리가 각각 다른 도구를 쓴다.** 하나로 전부 하려고 하면 반드시 어긋난다.
- **생성자에서 막으면** 잘못된 객체 자체가 안 만들어진다 — "즉시 실패".
- **반환값을 봉투에 담으면** 호출자가 "없을 수 있음"을 시그니처로 안다.
- **경계에서 거르면** 안쪽 코드가 `null` 을 아예 안 본다.
- 이 셋을 안 하면 NPE 는 **원인에서 멀리 떨어진 자리**에서 터진다. 그게 진짜 비용이다.

```text
   밖                        경계                 도메인                   저장소
  ----+---------------------+--------------------+-----------------------+------
   HTTP 요청               검증                  생성자                  조회
   JSON                   형식·필수값            requireNonNull          Optional 반환
   외부 API 응답            ↓                      ↓                       ↓
                      여기서 거르면          여기서 막으면            여기서 알리면
                      안쪽이 null 을        잘못된 객체가            호출자가 없음을
                      안 본다               안 만들어진다            타입으로 안다
```

**똑같은 구조로** Java 가 동작한다: 검문소 = 방어 코드, 신분증 확인 = `requireNonNull`, 없음 안내 = `Optional`.

실무에서 이게 터지는 자리는 **"NPE 나니까 앞에 `if (x != null)` 을 붙이자"는 코드**다.\
검문소가 건물 전체에 흩어지고, 정작 **`null` 이 어디서 들어왔는지는 아무도 모르게** 된다.

> **즉시 실패(fail fast)** — 잘못된 값이 들어온 **그 자리에서** 터뜨려, 원인과 증상을 붙여 놓는 것.\
> 예: 생성자에서 `Objects.requireNonNull(name)` 을 하면 스택 트레이스가 생성자를 가리킨다.

> **NPE(NullPointerException)** — `null` 인 참조로 필드를 읽거나 메서드를 부를 때 나는 런타임 예외.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `null` 을 **어느 계층에서** 막아야 하고, 그 자리마다 **어떤 도구**가 맞는가.
2. 방어 시점이 다르면 **관측되는 것이 무엇이 달라지는가** — 스택 트레이스·메시지·터지는 시점.
3. `@Nullable` 애너테이션은 **무엇을 해 주고 무엇을 안 해 주는가.**

## 동작 방식

### (1) ★ 방어 시점 셋 — 이 절이 이 주제의 전부다

**언제 쓰나** — `null` 이 들어올 수 있는 값을 다룰 때. **먼저 "어느 자리인가"를 정한다.**

```text
  자리                   도구                          무엇을 얻나
  ---------------------------------------------------------------------------
  ① 경계                 형식·필수값 검증               안쪽이 null 을 안 본다
     (컨트롤러·파서)      + 정규화(빈 문자열 -> null 등)

  ② 생성자·팩토리         Objects.requireNonNull        잘못된 객체가 안 만들어진다
     (도메인 객체 생성)   (메시지를 반드시 준다)         스택이 생성자를 가리킨다 ★

  ③ 반환값               Optional<T>                   호출자가 "없음" 을
     (조회 메서드)        (null 을 절대 안 돌려준다)     시그니처로 안다
```

그림 해설 (한 단계씩):

- ★ **셋은 대체재가 아니라 분업이다.** ①이 안 되면 ②가 터지고, ②가 안 되면 ③ 이후 아무 데서나 터진다.
- ②는 **막는 것**이고 ③은 **알리는 것**이다. 섞으면 안 된다 —
  "없으면 안 되는 값"을 `Optional` 로 감싸면 호출자가 `orElse(기본값)` 로 조용히 넘긴다.
- `@Nullable` 은 이 표에 없다. **문을 잠그지 않기 때문**이다((5)).

비용 — ②는 참조 비교 한 번. ③은 봉투 객체 하나. **둘 다 무시할 수 있다.**

### (2) 방어 시점이 스택 트레이스를 바꾼다

**언제 쓰나** — "NPE 는 났는데 어디서 들어온 `null` 인지 모르겠다" 를 겪을 때.

```java
static class Lazy {                              // 방어 없음
    final String name;
    Lazy(String name) { this.name = name; }
    int len() { return name.length(); }
}
static class Eager {                             // 생성자에서 즉시 실패
    final String name;
    Eager(String name) { this.name = Objects.requireNonNull(name, "name 은 null 일 수 없다"); }
    int len() { return name.length(); }
}
```

**출력** (`Ex.java (60-a)`, JDK 21.0.5 — 17·25 동일)

```text
--- 1. 언제 터지나 — 방어 시점이 스택을 바꾼다 ---
new Lazy(null)  : 생성 성공. lazy.name = null
  lazy.len()    -> NPE: Cannot invoke "String.length()" because "this.name" is null
  터진 자리      : Ex$Lazy.len <- Ex.main
new Eager(null) -> NPE: name 은 null 일 수 없다
  터진 자리      : java.util.Objects.requireNonNull <- Ex$Eager.<init>
```

```text
  방어 없음                                    생성자에서 requireNonNull
  +-----------------------------------+       +-----------------------------------+
  | new Lazy(null)   -> 성공 ★        |       | new Eager(null)  -> 즉시 NPE      |
  |   잘못된 객체가 살아서 돌아다닌다  |       |   객체가 아예 안 만들어진다        |
  |                                   |       |                                   |
  | ... 한참 뒤 ...                    |       | 스택 top:                         |
  | lazy.len()       -> NPE           |       |   Objects.requireNonNull          |
  |                                   |       |   <- Ex$Eager.<init>  ★ 생성 지점 |
  | 스택 top: Lazy.len                |       |                                   |
  |   "누가 null 을 넣었나" 는 없다 ★  |       | 메시지: 내가 쓴 문장               |
  +-----------------------------------+       +-----------------------------------+
```

그림 해설 (한 단계씩):

- ★ **`new Lazy(null)` 이 성공한다는 것이 문제의 전부다.** `null` 을 품은 객체가 그대로 살아 나간다.
- 그 객체가 리스트에 들어가고, 캐시에 저장되고, 다른 스레드로 넘어간 **뒤에** 터진다.\
  그때 스택 트레이스에는 **`null` 을 넣은 코드가 한 줄도 없다.**
- `Eager` 쪽은 스택의 두 번째 프레임이 **`Ex$Eager.<init>`** — 생성자다.\
  그 아래를 한 칸만 더 보면 **누가 `null` 을 넘겼는지**가 나온다.
- 메시지도 내가 쓴 문장이라 **어느 인자인지 바로 안다.**

비용 — `null` 비교 한 번. `requireNonNull` 은 `@ForceInline` 이 붙어 있어 JIT 이 인라인한다.

```java
// JDK 21.0.5  java.base/java/util/Objects.java  230~235행 — 실제 소스 그대로
@ForceInline
public static <T> T requireNonNull(T obj) {
    if (obj == null)
        throw new NullPointerException();
    return obj;
}
```

### (3) `requireNonNull` 의 세 형태 — 메시지가 다르다

**언제 쓰나** — 생성자·public 메서드의 인자 검증.

```java
Objects.requireNonNull(x);                          // 메시지 없음
Objects.requireNonNull(x, "직접 쓴 메시지");           // 문자열
Objects.requireNonNull(x, () -> "공급자가 만든 메시지"); // Supplier (8+)
```

**출력** (`Ex.java (60-a)`, JDK 21.0.5 — 17·25 동일)

```text
--- 3. requireNonNull 의 세 형태 ---
requireNonNull(null)              -> NPE 메시지 = null
requireNonNull(null, "...")       -> NPE 메시지 = 직접 쓴 메시지
requireNonNull(null, 공급자)       -> NPE 메시지 = 공급자가 만든 메시지
```

그림 해설 (한 단계씩):

- **첫째는 메시지가 없다**(`getMessage()` 가 `null`). 소스가 `throw new NullPointerException()` 이기 때문이다.
- 그래서 **실무에서는 둘째를 쓴다.** 인자가 여럿인 생성자에서 **어느 인자인지** 알려면 메시지가 필요하다.
- 셋째(`Supplier`)는 **메시지를 만드는 비용이 클 때**만 의미가 있다 — 문자열 이어붙이기·조회가 들어갈 때.\
  `"name"` 같은 리터럴이면 둘째가 낫다([`../38-optional/`](../38-optional/) 의 `orElse` 대 `orElseGet` 과 같은 판단이다).

javadoc 이 용도를 예제로 못 박아 두었다.

> This method is designed primarily for doing parameter validation in methods
> and constructors with multiple parameters, as demonstrated below:
> ```
> public Foo(Bar bar, Baz baz) {
>     this.bar = Objects.requireNonNull(bar, "bar must not be null");
>     this.baz = Objects.requireNonNull(baz, "baz must not be null");
> }
> ```

비용 — 둘째는 문자열 리터럴이라 비용이 없다. 셋째는 람다 객체 하나.

### (4) `requireNonNullElse` 와 `requireNonNullElseGet` (9+)

**언제 쓰나** — `null` 이면 기본값을 쓰고 싶을 때. `Optional` 을 만들지 않고 한 줄로 끝낸다.

```java
Objects.requireNonNullElse(value, "기본");          // 9+
Objects.requireNonNullElseGet(value, () -> make()); // 9+
```

**출력** (`Ex.java (60-a)`, JDK 21.0.5 — 17·25 동일)

```text
--- 4. requireNonNullElse 와 requireNonNullElseGet ---
Else("값", "기본")       : 값
Else(null, "기본")       : 기본
Else(null, null)         -> NPE 메시지 = defaultObj
ElseGet(null, ()->null)  -> NPE 메시지 = supplier.get()
ElseGet(null, null)      -> NPE 메시지 = supplier
```

★ **세 NPE 메시지가 전부 다르고, 전부 소스에서 온다.**

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

```text
  메시지            무엇이 null 이었나
  ------------------------------------------------------------
  defaultObj        두 번째 인자(기본값) 자체가 null
  supplier          Supplier 를 안 줬다(null 을 줬다)
  supplier.get()    Supplier 는 줬는데 그게 null 을 돌려줬다
```

그림 해설 (한 단계씩):

- ★ **메시지 한 단어가 "어느 단계에서 null 이 나왔나"를 말한다.** 세 문자열이 전부 소스의 리터럴이다.
- **기본값도 `null` 이면 안 된다.** "기본값"이라는 개념 자체가 `null` 이면 성립하지 않기 때문이다.
- `Else` 와 `ElseGet` 의 차이는 **`orElse`/`orElseGet` 과 완전히 같다** — 다음 절에서 실측한다.

비용 — 참조 비교 한두 번.

### (5) ★ `Else` 도 인자가 항상 평가된다

**언제 쓰나** — `requireNonNullElse` 의 두 번째 인자에 **메서드 호출**을 넣을 때.

**출력** (`Ex.java (60-a)`, JDK 21.0.5 — 17·25 동일)

```text
--- 5. Else 는 즉시 평가, ElseGet 은 필요할 때만 ---
Else("값", make())    = 값 / make() 호출 = 1
ElseGet("값", make)   = 값 / make() 호출 = 0
ElseGet(null, make)   = 만들어진 기본값 / make() 호출 = 1
```

```text
  requireNonNullElse(x, make())              requireNonNullElseGet(x, Ex::make)
  +-----------------------------------+      +-----------------------------------+
  | 1. make() 를 먼저 부른다 ★        |      | 1. Supplier 만 만든다             |
  | 2. 그 값을 인자로 넘긴다           |      | 2. x 가 null 이 아니면            |
  | 3. x 가 null 이 아니면 x 를 반환   |      |    supplier.get() 을 안 부른다    |
  | -> 만든 것을 버렸다                |      |                                   |
  +-----------------------------------+      +-----------------------------------+
        호출 = 1                                    호출 = 0
```

그림 해설 (한 단계씩):

- ★ **`Optional.orElse` 와 완전히 같은 현상**이다. 자바에 지연 인자가 없기 때문이고, `Objects` 도 예외가 아니다.
- 판정 기준도 같다 — **리터럴·상수면 `Else`, 계산·조회·객체 생성이면 `ElseGet`.**
- 이 규칙은 `Optional`·`Objects`·`Map.getOrDefault`·로깅까지 **자바 전체에 같은 모양**으로 반복된다.

비용 — ★ `Else` 의 두 번째 인자는 **100% 평가된다.**

### (6) NPE 메시지 — 빌드 옵션·JVM 플래그에 갈린다

**언제 쓰나** — 운영 로그의 NPE 메시지를 근거로 삼으려 할 때. **삼으면 안 된다.**

`05-arrays` 가 같은 소스를 **세 JDK × 세 조건**으로 돌려 이미 실측했다.\
결론만 받는다 — [`../05-arrays/`](../05-arrays/) 가 정본이다.

| 조건 | 그냥 역참조했을 때의 메시지 |
|---|---|
| `javac -g` | `Cannot read the array length because "nil" is null` — **변수 이름이 나온다** |
| `javac`(기본, `-g` 없음) | `... because "<local1>" is null` — **슬롯 번호로 나온다** |
| `java -XX:-ShowCodeDetailsInExceptionMessages` | **`null`** — 메시지가 통째로 사라진다 |

★ **그런데 `requireNonNull` 의 메시지는 세 조건에서 전부 살아남는다.**
이 주제에서 직접 확인했다 — `Ex.java (60-c)` 를 **세 JDK × 세 조건(9회)** 으로 돌렸고 **아홉 결과가 조건별로 완전히 같았다.**

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

그림 해설 (한 단계씩):

- ★ **이것이 명시적 검증을 쓰는 실무적 이유**다. 운영 환경의 빌드 설정·JVM 옵션을 내가 못 정해도 메시지가 남는다.
- helpful NPE 는 **개발 중에는 고맙지만 운영 로그의 근거로 쓸 수 없다.**
- 그러므로 **NPE 메시지 문자열에 의존하는 코드·테스트를 쓰면 안 된다.** 어느 쪽이든.

비용 — 없다.

> **helpful NullPointerException** — NPE 메시지에 "어느 식이 `null` 이었는지"를 적어 주는 기능(JEP 358, Java 14. 15부터 기본 켜짐).\
> 예: `Cannot invoke "String.length()" because "s" is null`.

### (7) `Optional` 은 반환 자리에만 — 38번과의 경계

**언제 쓰나** — 조회 메서드를 설계할 때.

```java
static final Map<String, String> DB = Map.of("a", "값");
@Nullable static String       findNull(String k) { return DB.get(k); }                 // null 반환
static Optional<String>       findOpt (String k) { return Optional.ofNullable(DB.get(k)); }  // 봉투 반환
```

**출력** (`Ex.java (60-b)`, JDK 21.0.5 — 17·25 동일)

```text
--- 5. 반환값을 null 로 돌려주는 것과 Optional 로 돌려주는 것 ---
findNull("없음")           : null
findOpt("없음")            : Optional.empty
findOpt("없음").orElse(..) : 기본
findNull(..).length()      -> NPE: Cannot invoke "String.length()" because the return value of "Ex.findNull(String)" is null
```

```text
  String findNull(String k)                  Optional<String> findOpt(String k)
  +-----------------------------------+      +-----------------------------------+
  | 시그니처가 "없을 수 있음" 을      |      | 시그니처가 말해 준다              |
  | 말하지 않는다                     |      |                                   |
  | 호출자가 잊으면 NPE               |      | 꺼내려면 반드시 한 번 더          |
  |   그것도 먼 곳에서                |      | 무언가를 호출해야 한다            |
  +-----------------------------------+      +-----------------------------------+
```

그림 해설 (한 단계씩):

- ★ NPE 메시지가 `the return value of "Ex.findNull(String)" is null` 이라고 **어느 메서드가 `null` 을 줬는지** 짚어 준다.\
  helpful NPE 가 가장 쓸모 있는 자리다 — 다만 (6)의 조건에 걸린다.
- `Optional` 을 쓰면 그 사고가 **컴파일 단계에서 사라진다.** `Optional` 에는 `length()` 가 없다.
- ★ 단 **반환 자리에만** 쓴다. 필드·파라미터·컬렉션 원소는 안 된다 — 근거와 실측은 [`../38-optional/`](../38-optional/).

비용 — 봉투 객체 하나.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다.

### `Objects` 의 `null` 관련 API 지도 (버전은 `src.zip` 의 `@since`)

| 호출 | 하는 일 | `@since` |
|---|---|---|
| `requireNonNull(obj)` | `null` 이면 메시지 없는 NPE | 7 |
| `requireNonNull(obj, String)` | `null` 이면 그 메시지로 NPE | 7 |
| `requireNonNull(obj, Supplier<String>)` | 메시지를 지연 생성 | **8** |
| `isNull(obj)` / `nonNull(obj)` | `Predicate` 로 쓰려고 만든 것 | **8** |
| `requireNonNullElse(obj, def)` | `null` 이면 `def` (`def` 도 `null` 이면 NPE) | **9** |
| `requireNonNullElseGet(obj, sup)` | `null` 이면 `sup.get()` | **9** |
| `equals(a, b)` | 양쪽 `null` 안전 | 7 |
| `hashCode(o)` | `null` 이면 `0` | 7 |
| `toString(o, nullDefault)` | `null` 이면 기본 문자열 | 7 |
| `toIdentityString(o)` | `null` 이면 NPE. 정체성 문자열 | **19** |

`isNull`·`nonNull` 의 javadoc 이 용도를 못 박았다.

> This method exists to be used as a {@link java.util.function.Predicate}, `filter(Objects::isNull)`

- ★ **`if (Objects.isNull(x))` 로 쓰라고 만든 것이 아니다.** 그건 `x == null` 보다 길다.
- 메서드 참조로 스트림에 넘길 때 쓴다 — `stream().filter(Objects::nonNull)`.

**출력** (`Ex.java (60-a)`)

```text
--- 6. Objects 의 null 안전 유틸 ---
Objects.toString(null, "-")  : -
Objects.equals(null, null)    : true
Objects.hashCode(null)        : 0
Objects.isNull / nonNull      : true / false
Objects.requireNonNullElse(null, "-").length() : 1
```

### `record` 의 컴팩트 생성자에서 검증한다

```java
record Money(String currency, long amount) {
    Money {
        Objects.requireNonNull(currency, "currency");
        if (amount < 0) throw new IllegalArgumentException("amount 는 음수일 수 없다: " + amount);
    }
}
```

**출력** (`Ex.java (60-a)`)

```text
--- 2. record 컴팩트 생성자 ---
정상               : Money[currency=KRW, amount=1000]
new Money(null, ..) -> NullPointerException: currency
new Money(.., -1)   -> IllegalArgumentException: amount 는 음수일 수 없다: -1
```

- `record` 는 필드를 `final` 로 만들어 주지만 **`null` 은 막아 주지 않는다.** 검증은 직접 쓴다.
- ★ **컴팩트 생성자가 검증을 넣기 위한 자리**다. 정본은 [`../14-records/`](../14-records/).
- `null` 은 `NullPointerException`, 범위 위반은 `IllegalArgumentException` — **예외 타입을 나누면** 호출자가 구분할 수 있다.

### 컬렉션마다 `null` 정책이 다르다

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

| 컬렉션 | `null` 키 | `null` 값 / 원소 |
|---|---|---|
| `HashMap` | 허용 (1개) | 허용 |
| `ArrayList` · `Arrays.asList` | — | 허용 |
| **`Map.of` · `List.of` · `Set.of`** (불변 팩토리, 9+) | **거부(NPE)** | **거부(NPE)** |
| `TreeSet` · `TreeMap` | **거부(NPE)** — 비교할 수 없다 | 값은 허용 |

- ★ **같은 `Map` 인터페이스인데 구현체마다 다르다.** "컬렉션은 `null` 을 받는다"는 문장은 틀렸다.
- `HashMap` 에서는 **"키가 없다"와 "값이 `null` 이다"가 `get` 으로 구분되지 않는다.** `containsKey` 를 봐야 한다.
- `TreeSet` 이 거부하는 이유는 28번과 이어진다 — **`compareTo(null)` 이 NPE 여야** 하기 때문이다([`../28-comparable-comparator/`](../28-comparable-comparator/)).

### 스트림 수집기의 `null` 정책

**출력** (`Ex.java (60-b)`)

```text
--- 3. 스트림 수집기의 null 정책 ---
Collectors.toMap  -> java.lang.NullPointerException: null
collect(HashMap::new, ...) : {a=1, b=null}
groupingBy 는 키가 null 이면 :
  -> java.lang.NullPointerException: element cannot be mapped to a null key
```

- ★ **`Collectors.toMap` 은 값이 `null` 이면 NPE** 다. 누산기 소스에 그 한 줄이 있다.

```java
// JDK 21.0.5  java.base/java/util/stream/Collectors.java  178~183행 — 실제 소스 그대로
return (map, element) -> {
    K k = keyMapper.apply(element);
    V v = Objects.requireNonNull(valueMapper.apply(element));
    V u = map.putIfAbsent(k, v);
    if (u != null) throw duplicateKeyException(k, u, v);
};
```

  즉 **JDK 안에서도 (2)~(3)의 관용구를 그대로 쓴다.** 메시지가 없어서 `NPE: null` 로 나온다.
- `groupingBy` 는 **키가 `null`** 이면 NPE 이고, 메시지가 `element cannot be mapped to a null key` 로 원인을 직접 말한다.
- 우회하려면 3인자 `collect(HashMap::new, ...)` 를 쓴다 — 실행으로 `{a=1, b=null}` 이 나왔다.
- `toMap` 의 함정은 [`../47-collectors-basics/`](../47-collectors-basics/) 가 정본이다.

### 경계에서 거르는 두 관용구

**출력** (`Ex.java (60-b)`)

```text
--- 4. 경계에서 걸러 내기 ---
원본                      : [a, null, b, null]
filter(Objects::nonNull)  : [a, b]
map(ofNullable).flatMap   : [a, b]
[a, null, b, null]
```

```java
list.stream().filter(Objects::nonNull).toList();                          // 짧다
list.stream().map(Optional::ofNullable).flatMap(Optional::stream).toList(); // 9+, 길다
```

- **둘 다 결과가 같다.** 실무에서는 앞의 것을 쓴다.
- ★ 마지막 줄이 중요하다 — **`stream().toList()` 는 `null` 원소를 그대로 통과시킨다.**

넷을 나란히 돌려 확인했다(`Ex.java (60-d)`).

```text
stream().toList()                    : [x, null, y]
collect(Collectors.toList())         : [x, null, y]
collect(toUnmodifiableList())        -> java.lang.NullPointerException
List.copyOf(...)                     -> java.lang.NullPointerException
```

  **"스트림을 거쳤으니 `null` 이 없겠지"는 틀린다.** 수집기를 무엇으로 쓰느냐가 정한다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다.

### 1. ★ `@Nullable` 애너테이션이 런타임에 막아 줄 거라 믿는다

```java
@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.PARAMETER, ElementType.FIELD, ElementType.METHOD})
@interface NonNull {}

static int len(@NonNull String s) { return s.length(); }
len(null);   // 컴파일된다
```

**출력** (`Ex.java (60-b)`, JDK 21.0.5)

```text
--- 1. @NonNull 은 런타임에 아무것도 막지 않는다 ---
메서드 파라미터의 애너테이션 : [@Ex.NonNull()]
len(null) 은 컴파일된다 -> 실행하면 NPE: Cannot invoke "String.length()" because "s" is null
```

```text
  애너테이션이 하는 일                   애너테이션이 안 하는 일
  +-----------------------------------+  +-----------------------------------+
  | 클래스 파일에 정보를 남긴다        |  | 컴파일을 막는다                   |
  |   (RUNTIME 이면 리플렉션으로 읽힘) |  | 런타임에 검사한다                 |
  | 정적 분석 도구가 읽는다            |  | NPE 를 막는다                     |
  | IDE 가 경고를 띄운다               |  |                                   |
  +-----------------------------------+  +-----------------------------------+
     ★ 애너테이션은 "메타데이터" 일 뿐이다. 검사를 하는 것은 그것을 읽는 도구다
```

- ★ **`len(null)` 이 그냥 컴파일되고 실행된다.** 애너테이션은 **읽히기만** 하고 아무 일도 안 한다.
- 검사를 하는 것은 **애너테이션을 읽는 도구**다 — IDE 인스펙션, ErrorProne, NullAway, SpotBugs, 스프링의 `@Validated`.\
  그 도구가 빌드 파이프라인에 없으면 **아무 효과가 없다.**
- 게다가 `@Nullable`/`@NonNull` 은 **표준이 아니다.** `jakarta.annotation`·`org.jetbrains`·`javax.annotation`·`org.springframework.lang` 등이 각자 있다.\
  팀에서 하나를 고르고 도구를 붙여야 의미가 생긴다.
- 따라서 **런타임 보장이 필요하면 `Objects.requireNonNull` 을 쓴다.** 애너테이션은 그 위에 얹는 문서다.
- 애너테이션 선언·`@Retention`·`@Target` 자체는 [**16번 주제**](../16-annotations/)가 정본이다.

### 2. `if (x != null)` 을 만나는 곳마다 붙인다

- 검문소가 **건물 전체에 흩어진다.** 그러면 `null` 이 어디서 들어왔는지 아무도 모른다.
- 코드가 길어지는데 **버그는 그대로** 있다 — 한 곳만 빠뜨려도 터지고, 그 자리는 원인과 멀다.
- 대신 (1)의 세 자리로 모은다. **안쪽 코드는 `null` 을 안 본다**는 규약을 만든다.

### 3. `requireNonNull` 에 메시지를 안 준다

```java
Foo(Bar bar, Baz baz) {
    this.bar = Objects.requireNonNull(bar);    // 메시지 없음
    this.baz = Objects.requireNonNull(baz);    // 메시지 없음
}
```

- 둘 중 무엇이 `null` 이었는지 **스택의 행 번호로만** 구분된다. 리팩토링하면 그마저 어긋난다.
- javadoc 의 예제가 메시지를 준 형태인 이유다((3)).
- 인자 이름 하나면 충분하다 — `requireNonNull(bar, "bar")`.

### 4. `requireNonNullElse` 의 기본값이 `null` 일 수 있다

```java
Objects.requireNonNullElse(value, config.getDefault());   // getDefault() 가 null 을 주면?
```

- `NullPointerException: defaultObj` 가 난다((4)에서 실측).
- 메시지가 `defaultObj` 라 **"기본값 쪽이 문제"** 라는 것은 알 수 있지만, 그 기본값을 누가 줬는지는 안 나온다.
- 기본값을 만드는 자리에서 먼저 보증하거나, `Optional` 로 표현을 바꾼다.

### 5. 빈 문자열·빈 컬렉션과 `null` 을 같이 취급한다

- `""` 와 `null` 은 다르다. `List.of()` 와 `null` 도 다르다.
- **경계에서 한쪽으로 정규화**한다 — 대개 "빈 것"으로 모은다.\
  `Objects.requireNonNullElse(list, List.of())` 한 줄이면 안쪽에서 `null` 검사가 사라진다.
- 컬렉션을 돌려주는 메서드는 **`null` 대신 빈 컬렉션**을 돌려준다. `Optional<List<T>>` 는 거의 항상 과하다.

### 6. `Optional` 을 `null` 방어 장치로 쓴다

- `Optional` 은 **알리는 도구**이지 막는 도구가 아니다. 봉투 자체가 `null` 일 수 있다([`../38-optional/`](../38-optional/)).
- "없으면 안 되는 값"을 봉투에 담으면 호출자가 `orElse(기본값)` 로 **조용히 넘어간다.**
- 막아야 하면 `requireNonNull` 또는 예외다([`../25-exceptions/`](../25-exceptions/)).

## 구현 세부사항 대 언어 보장

이 절은 "**어디까지 믿어도 되나**"를 가른다.

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| `requireNonNull(obj)` 가 `null` 이면 NPE | **javadoc (계약)** | `@throws NullPointerException if obj is null` |
| 메시지 있는 형태가 그 메시지를 쓴다 | **javadoc (계약)** | `@param message detail message ...` |
| `requireNonNullElse` 의 기본값도 `null` 이면 NPE | **javadoc (계약)** | `@throws NullPointerException if both obj and defaultObj are null` |
| 메시지가 `defaultObj`·`supplier`·`supplier.get()` | **구현 세부** | 소스의 문자열 리터럴(`Objects.java` 313·332행) |
| `Else` 의 인자가 항상 평가됨 | **언어 규칙 (JLS)** | 메서드 호출의 인자 평가 규칙. `Objects` 와 무관 |
| `Map.of`/`List.of` 가 `null` 을 거부 | **javadoc (계약)** | `@throws NullPointerException if ... is null` |
| `HashMap` 이 `null` 키를 허용 | **javadoc (계약)** | `HashMap` 은 `null` 키 하나와 `null` 값을 허용한다고 명시 |
| helpful NPE 메시지의 문구 | **구현 세부 + 컴파일 옵션 + JVM 플래그** | `-g` 유무·`-XX:-ShowCodeDetailsInExceptionMessages` ([`../05-arrays/`](../05-arrays/) 실측) |
| `requireNonNull` 메시지가 플래그에 안 흔들림 | **구현 (소스 그대로)** | 내가 준 문자열이 그대로 `NullPointerException` 생성자로 간다 |
| 애너테이션의 `toString` 형태 | **구현 세부 — JDK 마다 달랐다 ★** | 아래 |
| `@Retention(RUNTIME)` 애너테이션이 런타임 검사를 하지 않음 | **언어 보장** | 애너테이션은 메타데이터다. 검사는 도구의 몫 |

### ★ 세 JDK 에서 유일하게 달랐던 한 줄

`Ex.java (60-b)` 의 첫 절만 JDK 마다 출력이 달랐다.

```text
JDK 17.0.13 : 메서드 파라미터의 애너테이션 : [@Ex$NonNull()]
JDK 21.0.5  : 메서드 파라미터의 애너테이션 : [@Ex.NonNull()]
JDK 25.0.1  : 메서드 파라미터의 애너테이션 : [@Ex.NonNull()]
```

- 중첩 애너테이션 타입의 이름이 **`Ex$NonNull`(이진 이름)에서 `Ex.NonNull`(정규 이름)로** 바뀌었다.
- ★ **`Annotation.toString()` 의 형식은 명세가 고정하지 않았다.** 그래서 이런 변화가 허용된다.
- **애너테이션의 `toString` 을 파싱하거나 비교하는 코드를 쓰면 안 된다.**
- 나머지 모든 출력(`60-a`·`60-c` 전부, `60-b` 의 2~5절)은 세 JDK 에서 같았다 — **관찰이다.**

**경계 한 줄** — 메시지 문자열(`defaultObj`·`supplier.get()`·helpful NPE 문구·애너테이션 `toString`)은 **관찰**이고,
"`null` 이면 NPE 를 던진다"·"`Map.of` 는 `null` 을 거부한다"는 **javadoc 의 계약**이다.\
외울 것은 메시지가 아니라 **"어느 자리에서 막을 것인가"** 라는 배치다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 도구 |
|---|---|
| 생성자·팩토리의 필수 인자 | **`Objects.requireNonNull(x, "x")`** — 메시지를 반드시 준다 |
| `record` 의 컴포넌트 | 컴팩트 생성자에서 `requireNonNull` |
| public 메서드의 필수 인자 | `requireNonNull`. private 내부 메서드는 대개 불필요 |
| 조회 메서드의 반환값 — 없을 수 있다 | **`Optional<T>`** (반환 자리에만) |
| 컬렉션을 돌려주는 메서드 | **빈 컬렉션**을 돌려준다. `null` 도 `Optional` 도 아니다 |
| `null` 이면 기본값 — 기본값이 상수 | `requireNonNullElse(x, DEFAULT)` |
| `null` 이면 기본값 — 기본값을 만들어야 함 | **`requireNonNullElseGet(x, () -> ...)`** |
| 스트림에서 `null` 걸러 내기 | `filter(Objects::nonNull)` |
| 외부 입력(HTTP·JSON·DB) | **경계에서 검증·정규화.** 안쪽으로는 `null` 을 안 보낸다 |
| 팀에 정적 분석 도구가 있다 | `@Nullable`/`@NonNull` 을 **함께** 쓴다. 단독으로는 효과 없다 |
| 값이 없으면 계속 진행하면 안 된다 | **예외를 던진다.** `Optional` 로 감싸지 않는다 |
| `Optional` 을 필드·파라미터·컬렉션 원소로 | **안 쓴다** ([`../38-optional/`](../38-optional/)) |

판단 규칙 세 줄.

- **막을 것인가, 알릴 것인가를 먼저 정한다.** 막는 것은 `requireNonNull`·예외, 알리는 것은 `Optional`.
- **검문소는 세 자리에만 세운다** — 경계·생성자·반환값. 그 사이에는 `null` 이 없다고 가정한다.
- **애너테이션은 도구가 있어야 일한다.** 런타임 보장이 필요하면 코드를 쓴다.

## 핵심 문장

- `null` 방어는 **도구 고르기가 아니라 배치 문제**다 — ① 경계 검증 ② 생성자 `requireNonNull` ③ 반환값 `Optional`, 셋은 분업이다.
- ★ **생성자에서 막으면 스택 트레이스가 생성 지점을 가리킨다.** 안 막으면 `null` 을 품은 객체가 살아 나가 **원인과 먼 자리**에서 터진다.
- `requireNonNull` 은 **메시지를 주고 쓴다.** javadoc 의 예제 자체가 인자가 여럿인 생성자에 메시지를 붙인 형태다.
- `requireNonNullElse` 의 NPE 메시지 셋(`defaultObj`·`supplier`·`supplier.get()`)은 **어느 단계에서 `null` 이 나왔는지**를 말한다.
- ★ **`requireNonNullElse` 의 두 번째 인자도 항상 평가된다.** `Optional.orElse` 와 완전히 같은 현상이고, 원인은 자바의 인자 평가 규칙이다.
- ★ **helpful NPE 메시지는 `-g` 와 JVM 플래그에 갈리지만, `requireNonNull` 의 메시지는 세 조건에서 모두 살아남았다.** 이것이 명시적 검증의 실무적 이유다.
- ★ **`@Nullable`/`@NonNull` 은 런타임에 아무것도 막지 않는다.** `len(null)` 이 그냥 컴파일되고 실행된다 — 검사는 그것을 읽는 도구의 몫이다.
- **컬렉션마다 `null` 정책이 다르다.** `HashMap` 은 받고, `Map.of`/`List.of`/`TreeSet` 은 NPE 로 거부한다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 60번)
- [`../38-optional/`](../38-optional/) — **그쪽은 `Optional` 이라는 타입 하나(생성·소비·안티패턴·버전)까지, 여기는 그것을 세 방어 시점 중 하나로 배치하는 판단부터.**\
  "`Optional` 을 필드에 두면 안 되는 이유"의 실측은 전부 그쪽에 있다
- [`../05-arrays/`](../05-arrays/) — **helpful NPE 메시지가 `-g` 와 `-XX:-ShowCodeDetailsInExceptionMessages` 에 갈린다는 실측의 정본.**\
  여기서는 그 결론만 받아 "그래서 `requireNonNull` 을 쓴다"까지만 적는다
- [`../25-exceptions/`](../25-exceptions/) — **"없음"을 값으로 돌려줄지 예외로 던질지**의 경계. 예외 설계는 그쪽이 정본
- [`../14-records/`](../14-records/) — 컴팩트 생성자에서 검증하는 자리의 정본
- [`../28-comparable-comparator/`](../28-comparable-comparator/) — `compareTo(null)` 이 NPE 여야 하는 이유. `TreeSet` 이 `null` 을 거부하는 근거
- [`../47-collectors-basics/`](../47-collectors-basics/) — `Collectors.toMap` 이 `null` 값에서 터지는 조건의 정본
- [`../45-intermediate-operations/`](../45-intermediate-operations/) — `filter(Objects::nonNull)` 로 거르는 자리
- [`../31-functional-interfaces/`](../31-functional-interfaces/) — `requireNonNullElseGet`·`requireNonNull(obj, Supplier)` 가 받는 `Supplier`
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — `Objects.equals`/`Objects.hashCode` 가 `null` 안전한 이유
- [**16번 주제**](../16-annotations/)(애너테이션) — `@Retention`·`@Target` 과 "런타임에 읽히는 것과 사라지는 것"의 정본
- [**41번 주제**](../41-map-api-merge-compute/)(`Map` API) — `getOrDefault`·`containsKey` 로 "없음"과 "`null` 값"을 가르는 법
- [**59번 주제**](../59-immutable-objects/)(불변 객체 만들기) — 생성자 검증과 방어적 복사가 한 자리에서 만나는 곳

## 용어 풀이

- **NPE(`NullPointerException`)** — `null` 인 참조로 필드를 읽거나 메서드를 부를 때 나는 런타임 예외.
- **즉시 실패(fail fast)** — 잘못된 값이 들어온 그 자리에서 터뜨려 원인과 증상을 붙여 놓는 것.
- **`Objects.requireNonNull`** — `null` 이면 NPE 를 던지고 아니면 그대로 돌려주는 정적 메서드(Java 7).
- **`requireNonNullElse` / `requireNonNullElseGet`** — `null` 이면 기본값 / `Supplier` 의 결과를 돌려준다(Java 9).
- **helpful NullPointerException** — NPE 메시지에 어느 식이 `null` 이었는지 적어 주는 기능(JEP 358, Java 14. 15부터 기본).
- **`@Nullable` / `@NonNull`** — "이 자리에 `null` 이 올 수 있다/없다"를 적는 애너테이션. **표준이 아니고 런타임 강제도 없다.**
- **정적 분석(static analysis)** — 코드를 실행하지 않고 읽어 문제를 찾는 것. 애너테이션은 이 도구가 읽는다.
- **경계(boundary)** — 내 코드와 밖(HTTP·DB·외부 API)이 만나는 자리. 검증을 여기 모은다.
- **정규화(normalization)** — 여러 표현을 한 가지로 모으는 것. 예: 빈 문자열과 `null` 을 `null` 하나로.
- **컴팩트 생성자(compact constructor)** — `record` 에서 파라미터 목록을 생략하고 검증·정규화만 쓰는 생성자 형태.

## 더 들어가면

- **`requireNonNull` 에는 `@ForceInline` 이 붙어 있다.**\
  `Objects.java` 의 소스에 그대로 있다 — JIT 이 반드시 인라인하라는 내부 지시다.\
  그래서 뜨거운 경로에 넣어도 비용 논쟁이 성립하지 않는다.
- **`requireNonNull` 은 반환값이 있어서 대입식에 그대로 쓸 수 있다.**\
  `this.name = Objects.requireNonNull(name, "name");` 한 줄이 검증과 대입을 동시에 한다.\
  `if (name == null) throw ...` 두 줄보다 짧아서 **빠뜨릴 확률이 줄어든다.**
- **JDK 자신도 이 관용구를 쓴다.**\
  `Optional.of` 는 `return new Optional<>(Objects.requireNonNull(value));` 한 줄이고,
  `Optional.map` 은 `Objects.requireNonNull(mapper);` 로 시작한다([`../38-optional/`](../38-optional/)).
- **불변 컬렉션 계열만 `null` 을 거부한다.**\
  `Stream.toList()`(16+)와 `Collectors.toList()` 는 `null` 원소를 그대로 통과시키고,
  `Collectors.toUnmodifiableList()` 와 `List.copyOf` 는 NPE 다(`Ex.java (60-d)` 실측).\
  `List.of`/`Map.of`/`Set.of` 와 같은 정책이다 — **불변 팩토리는 전부 `null` 을 거부한다.**
- **`Objects.requireNonNullElse` 는 `Optional.ofNullable(x).orElse(def)` 와 결과가 같지만 봉투를 안 만든다.**\
  한 번 쓰고 버릴 기본값 처리라면 `Objects` 쪽이 짧고 객체도 덜 만든다.\
  `Optional` 은 **여러 단계를 엮을 때**(map/filter/flatMap) 값어치가 나온다.
