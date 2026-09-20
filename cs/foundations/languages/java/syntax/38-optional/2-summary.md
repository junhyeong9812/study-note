# java/syntax/38 — `Optional`: 생성·소비·안티패턴 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — JDK 21.0.5 표준 라이브러리 소스 `java.base/java/util/Optional.java` 의 **javadoc·`@since` 원문**(`lib/src.zip` 에서 직접 인용).
> **실행 검증** — 이 문서의 모든 출력·예외는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 실행 프로그램 셋(`Ex.java (38-a)`·`(38-b)`·`(38-c)`)을 **17.0.13 · 21.0.5 · 25.0.1** 세 곳에서 돌려 **출력이 한 글자도 다르지 않았다**.\
> 다만 **"세 곳에서 같았다"는 관찰이지 보장이 아니다** — 보장은 javadoc 인용으로만 적었다.
> **버전** — `Optional` 자체는 **Java 8**(`@since 1.8`). 메서드마다 버전이 갈린다 —\
> `ifPresentOrElse`·`or`·`stream` 은 **9**, `orElseThrow()`(인자 없는 것)는 **10**, `isEmpty` 는 **11**.\
> ★ 전부 `src.zip` 의 `@since` 를 직접 읽고, `javac --release` 를 8~11로 바꿔 가며 **컴파일로 재확인**했다(아래 표).
> **범위** — `null` 을 **어디서 어떻게 막을지**(생성자 검증·경계 방어·`Objects.requireNonNull`)는 이 문서가 다루지 않는다.\
> 그쪽은 [`../60-null-handling/`](../60-null-handling/) 가 정본이다. 여기는 **`Optional` 이라는 타입 하나**만 다룬다.\
> `findFirst`·`min`·`max` 가 왜 `Optional` 을 돌려주는지는 [`../46-terminal-operations/`](../46-terminal-operations/) 가 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**`Optional` 은 "내용물이 있을 수도 없을 수도 있는 봉투"다. 반환값에 씌우라고 만든 것이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 봉투 | `Optional<T>` 인스턴스 |
| 안에 서류가 든 봉투 | `Optional.of(v)` — 값이 있다 |
| 빈 봉투 | `Optional.empty()` — 값이 없다 |
| 봉투를 안 주고 아무것도 안 준 것 | `null` — **봉투 자체가 없다** |
| 봉투를 뜯어 꺼낸다 | `get()` · `orElseThrow()` |
| 비었으면 대신 넣을 것을 **미리 만들어 놓는다** | `orElse(x)` — **항상 만든다** ★ |
| 비었을 때만 만든다 | `orElseGet(() -> x)` |
| 봉투를 안 뜯고 내용에 도장만 찍는다 | `map` · `flatMap` · `filter` |

- `Optional` 을 만든 이유는 **"이 메서드는 값을 못 줄 수도 있다"를 타입으로 말하기 위해서**다.
- ★ javadoc 의 `@apiNote` 가 용도를 **직접 못 박았다** — **메서드 반환 타입**이라고.
- 그래서 **필드·파라미터·컬렉션 원소**에 쓰면 얻는 것보다 잃는 것이 많다.
- ★ 그리고 **봉투 자체가 `null` 일 수 있다.** `Optional<String> o = null;` 은 컴파일된다 — 이것이 가장 허무한 함정이다.

```text
   값이 있을 수도 없을 수도 있는 것을 돌려주는 방법 둘

   (A) null 을 돌려준다                      (B) Optional 을 돌려준다
   +----------------------------+            +----------------------------+
   | String find(String k)      |            | Optional<String> find(k)   |
   |                            |            |                            |
   | 호출자는 시그니처만 보고   |            | 호출자는 시그니처만 보고    |
   | "없을 수 있다"를 모른다    |            | "없을 수 있다"를 안다       |
   |                            |            |                            |
   | 안 막으면 나중에 NPE       |            | 꺼내려면 반드시 한 번 더    |
   | 그것도 아주 먼 곳에서      |            | 무언가를 호출해야 한다      |
   +----------------------------+            +----------------------------+
```

**똑같은 구조로** Java 가 동작한다: 봉투 = `Optional`, 뜯기 = `orElseThrow`, 도장 찍기 = `map`.

실무에서 이게 잘못 쓰이는 자리는 **`Optional` 을 "NPE 안 나게 하는 도구"로 오해한 코드**다.\
`if (opt.isPresent()) opt.get()` 은 `if (x != null) x` 를 길게 쓴 것일 뿐이고, 얻은 것이 없다.

> **`Optional`** — 값이 있을 수도 없을 수도 있음을 **타입으로 표현**한 컨테이너(Java 8).\
> 예: `Optional<User> findById(String id)` 는 "없을 수 있다"를 시그니처로 말한다.

> **안티패턴(anti-pattern)** — 흔히 쓰이지만 문제를 해결하기보다 더 만드는 방식.\
> 예: `Optional` 을 필드에 두는 것. 직렬화가 깨지고 상태가 셋이 된다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `Optional` 은 **무엇을 위해 만들어졌나** — javadoc 이 지정한 용도는 정확히 무엇인가.
2. **안티패턴이 왜 안티패턴인가** — `orElse` 의 평가 시점·직렬화·파라미터·컬렉션에서 실제로 무엇이 관측되는가.
3. `if` 없이 **엮어 쓰는 법**은 무엇이고, 어디까지 엮을 수 있나.

## 동작 방식

### (1) javadoc 이 용도를 직접 지정했다

**언제 쓰나** — "여기에 `Optional` 을 써도 되나?"를 판단할 때. **이 문단 하나가 기준이다.**

JDK 21.0.5 `java.base/java/util/Optional.java` 의 클래스 javadoc `@apiNote` 원문이다.

> `Optional` is primarily intended for use as a method return type where
> there is a clear need to represent "no result," and where using `null`
> is likely to cause errors. A variable whose type is `Optional` should
> never itself be `null`; it should always point to an `Optional`
> instance.

```text
  이 한 문단이 말하는 것 셋

  ① primarily intended for use as a method return type
       -> 반환 타입. 필드도 파라미터도 아니다

  ② where there is a clear need to represent "no result"
       -> "결과 없음"이 정상적인 경우일 때만

  ③ A variable whose type is Optional should never itself be null
       -> 봉투 자체가 null 이면 안 된다 (그런데 언어가 막아 주지 않는다 ★)
```

그림 해설 (한 단계씩):

- ★ **"primarily intended for use as a method return type"** — 이 구절이 모든 안티패턴 판정의 근거다.
- ②는 "예외를 던질 상황"과 구분하라는 뜻이다. **조회했는데 없는 것은 정상**, 필수 설정이 없는 것은 예외다.
- ③은 **요구이지 보장이 아니다.** 컴파일러도 런타임도 막지 않는다((5) 4번에서 실측).

같은 파일에 `@jdk.internal.ValueBased` 애너테이션과 이 문단도 있다.

> This is a value-based class; programmers should treat instances that are
> equal as interchangeable and should not use instances for synchronization,
> or unpredictable behavior may occur.

- 그래서 `synchronized (optional)` 은 **컴파일 경고**가 난다((5) 6번).

비용 — 없다. 판단 규칙이다.

### (2) 생성 — 세 가지뿐이다

**언제 쓰나** — `Optional` 을 만들 때. 셋의 구분이 첫 번째 갈림길이다.

```java
Optional<String> some  = Optional.of("값");          // null 이면 NPE
Optional<String> maybe = Optional.ofNullable(null);  // null 이면 empty
Optional<String> none  = Optional.empty();
```

**출력** (`Ex.java (38-a)`, JDK 21.0.5 — 17·25 동일)

```text
--- 1. 생성 세 가지 ---
Optional.of("값")        : Optional[값]
Optional.ofNullable(null) : Optional.empty
Optional.empty()          : Optional.empty
Optional.of(null)         -> java.lang.NullPointerException: null
```

```text
   값                 of(v)                    ofNullable(v)
  +------+          +---------------+        +---------------+
  | "값" |  ----->  | Optional[값]  |        | Optional[값]  |
  +------+          +---------------+        +---------------+

  +------+          +---------------+        +---------------+
  | null |  ----->  | NPE 를 던진다  |        | Optional.empty|
  +------+          +---------------+        +---------------+
                      ★ 이것이 의도다           ★ 이것도 의도다
```

그림 해설 (한 단계씩):

- **`of` 는 "여긴 절대 `null` 이 아니다"를 주장하는 것**이다. 아니면 그 자리에서 터진다 — 좋은 일이다.
- **`ofNullable` 은 "`null` 일 수 있다"를 봉투로 바꾸는 것**이다. `null` 을 다루는 코드의 **경계**에 쓴다.
- 둘을 헷갈려 `of` 를 쓰면 NPE 가 나고, 전부 `ofNullable` 만 쓰면 **버그를 봉투에 담아 흘려보낸다.**
- `Optional.of(null)` 의 NPE 메시지는 **`null`**(메시지 없음)이다. 소스가 `Objects.requireNonNull(value)` 한 줄이기 때문이다.

비용 — `of`/`ofNullable` 은 객체 하나를 만든다. `empty()` 는 **공유 인스턴스**를 돌려준다.\
다만 javadoc 이 `empty()` 의 `@apiNote` 에서 이렇게 경고한다.

> avoid testing if an object is empty by comparing with `==` or `!=` against instances returned by
> `Optional.empty()`.  There is no guarantee that it is a singleton.

### (3) 소비 — 꺼내는 방법과 꺼내지 않는 방법

**언제 쓰나** — 봉투에서 답을 얻을 때. **꺼내지 않고 끝내는 쪽이 대개 낫다.**

```text
  꺼낸다 (T 가 나온다)                  안 꺼낸다 (Optional 이 나온다)
  +------------------------------+     +------------------------------+
  | get()            비면 예외    |     | map(f)      있으면 f 적용     |
  | orElseThrow()    비면 예외 10+|     | flatMap(f)  f 가 Optional     |
  | orElseThrow(공급자) 내 예외   |     | filter(p)   조건 불통과면 empty|
  | orElse(x)        ★ 항상 평가  |     | or(공급자)  비면 대체 9+      |
  | orElseGet(공급자) 필요할 때만 |     | stream()    0개 또는 1개 9+   |
  +------------------------------+     +------------------------------+

  꺼내지도 만들지도 않는다 (부수효과만)
  +--------------------------------------------------+
  | ifPresent(소비자)            있으면 실행          |
  | ifPresentOrElse(소비자, 실행) 없으면 다른 것 9+   |
  +--------------------------------------------------+
```

**출력** (`Ex.java (38-a)`)

```text
--- 3. 비어 있는 것에서 값을 꺼내려 하면 ---
get()          -> java.util.NoSuchElementException: No value present
orElseThrow()  -> java.util.NoSuchElementException: No value present
orElseThrow(공급자) -> java.lang.IllegalStateException: 사용자가 없다

--- 4. 소비 — ifPresent / ifPresentOrElse ---
ifPresent(있음)       : 값
ifPresentOrElse(있음) : 값
ifPresentOrElse(없음) : 없는 쪽이 돌았다

--- 5. 엮어 쓰기 — map / flatMap / filter / or / stream ---
map(String::length)          : Optional[1]
map 이 null 을 주면           : Optional.empty
filter(비통과)                : Optional.empty
or(대체 Optional)             : Optional[대체]
some.stream().toList()        : [값]
none.stream().toList()        : []
isPresent / isEmpty           : true / false
```

그림 해설 (한 단계씩):

- ★ **`get()` 과 `orElseThrow()` 는 같은 예외·같은 메시지**다 — `NoSuchElementException: No value present`.\
  소스가 둘 다 `throw new NoSuchElementException("No value present")` 한 줄이다.
- ★ **javadoc 이 `get()` 을 쓰지 말라고 적어 두었다.** `get()` 의 `@apiNote` 원문이다.

> The preferred alternative to this method is {@link #orElseThrow()}.

  즉 `orElseThrow()` 는 **"여기서 터질 수 있다"가 이름에 드러난 `get()`** 이다. Java 10부터 이쪽을 쓴다.
- ★ **`map` 에 넘긴 함수가 `null` 을 돌려주면 `Optional.empty` 가 된다.** 소스가 그렇게 되어 있다.

```java
// JDK 21.0.5  java.base/java/util/Optional.java  255~262행 — 실제 소스 그대로
public <U> Optional<U> map(Function<? super T, ? extends U> mapper) {
    Objects.requireNonNull(mapper);
    if (isEmpty()) {
        return empty();
    } else {
        return Optional.ofNullable(mapper.apply(value));
    }
}
```

  그래서 `null` 을 돌려주는 옛 API 를 `map` 으로 이어도 봉투가 깨지지 않는다.
- `stream()` 은 **0개 또는 1개짜리 스트림**이다. 스트림에서 `Optional` 을 펼칠 때 쓴다((6)).

비용 — 소비 메서드 자체는 상수 시간. **`orElse` 의 인자는 호출 전에 평가된다** — 그것이 (4)다.

> **`NoSuchElementException`** — "가져올 원소가 없다"를 뜻하는 `java.util` 의 런타임 예외.\
> 예: 빈 `Optional` 에 `get()`·`orElseThrow()`, 빈 `Iterator` 에 `next()`.

### (4) ★ `orElse` 는 항상 평가된다 — 실측으로 못 박는다

**언제 쓰나** — `orElse` 인자에 **메서드 호출**을 넣을 때. 상수면 문제가 없다.

부작용이 눈에 보이는 메서드로 확인했다(`Ex.java (38-a)`).

```java
static int calls = 0;
static String expensive() {
    calls++;
    System.out.println("      [expensive() 가 실제로 불렸다]");
    return "기본값";
}
```

**출력** (JDK 21.0.5 — 17·25 동일)

```text
--- 2. orElse 는 항상 평가된다 / orElseGet 은 필요할 때만 ---
  (A) 값이 있는 Optional 에 orElse(expensive())
      [expensive() 가 실제로 불렸다]
      결과 = 값 / expensive() 호출 횟수 = 1
  (B) 값이 있는 Optional 에 orElseGet(Ex::expensive)
      결과 = 값 / expensive() 호출 횟수 = 0
  (C) 비어 있는 Optional 에 orElse(expensive())
      [expensive() 가 실제로 불렸다]
      결과 = 기본값 / expensive() 호출 횟수 = 1
  (D) 비어 있는 Optional 에 orElseGet(Ex::expensive)
      [expensive() 가 실제로 불렸다]
      결과 = 기본값 / expensive() 호출 횟수 = 1
```

```text
  some.orElse(expensive())                    some.orElseGet(Ex::expensive)
  +-----------------------------------+       +-----------------------------------+
  | 1. expensive() 를 부른다 ★        |       | 1. 람다 객체만 만든다             |
  |    -> 출력이 찍힌다                |       |                                   |
  | 2. 그 값을 인자로 orElse 에 넘긴다 |       | 2. orElse Get 에 넘긴다            |
  | 3. orElse 가 "값이 있네" 하고      |       | 3. "값이 있네" 하고 원래 값 반환  |
  |    원래 값을 돌려준다              |       |    -> expensive() 는 안 불린다     |
  | -> 만든 것을 버렸다                |       |                                   |
  +-----------------------------------+       +-----------------------------------+
        호출 횟수 = 1                                 호출 횟수 = 0
```

그림 해설 (한 단계씩):

- ★ **`orElse(expensive())` 는 자바의 평범한 인자 평가 규칙일 뿐이다.** `Optional` 이 특별해서가 아니다.\
  메서드를 부르려면 **인자를 먼저 평가**해야 한다 — 자바에는 지연 인자가 없다([`../03-variables-and-assignment/`](../03-variables-and-assignment/)).
- (A)와 (C)를 비교하면 **값이 있든 없든 똑같이 한 번 불렸다.** 값이 있을 때는 **만든 것을 그냥 버린다.**
- (B)와 (D)를 비교하면 `orElseGet` 은 **필요할 때만** 불렀다.
- 그래서 판정 기준은 하나다 — **인자가 상수면 `orElse`, 계산·조회·객체 생성이면 `orElseGet`.**

```java
opt.orElse("기본값")                    // O — 리터럴. 만드는 비용이 없다
opt.orElse(DEFAULT)                      // O — 이미 있는 상수
opt.orElse(new ArrayList<>())            // 주의 — 매번 새 리스트를 만들어 버린다
opt.orElse(repository.findDefault())     // X — 값이 있어도 DB 를 친다 ★
opt.orElseGet(repository::findDefault)   // O
```

비용 — ★ **`orElse` 의 인자는 100% 평가된다.** 그것이 DB 조회라면 매번 조회가 나간다.\
반대로 `orElseGet` 은 **람다 객체 하나**를 만드는 비용이 있다(캡처가 없으면 JVM 이 재사용할 수 있다).

### (5) 안티패턴 — 왜 안티패턴인지 실측으로

**언제 쓰나** — 리뷰에서 `Optional` 을 봤을 때. **다섯 가지를 순서대로 본다.**

#### 1. `Optional` 을 필드로 — 직렬화가 깨진다

```java
static class BadUser implements Serializable {
    String name = "김";
    Optional<String> nickname = Optional.of("닉");   // 필드
}
```

**출력** (`Ex.java (38-b)`, JDK 21.0.5 — 17·25 동일)

```text
--- 1. Optional 은 직렬화되지 않는다 ---
Optional 이 Serializable 인가 : false
BadUser  직렬화 -> java.io.NotSerializableException: java.util.Optional
GoodUser 직렬화 : 성공 (88 바이트)
```

★ **컴파일러도 이것을 안다.** `instanceof Serializable` 조차 막힌다(`Ex.java (38-b2)`).

```text
Ex.java:5: error: incompatible types: Optional<String> cannot be converted to Serializable
        System.out.println(Optional.of("x") instanceof Serializable);
                                      ^
1 error
```

- `Optional` 은 `final` 이고 `Serializable` 을 구현하지 않는다. 그래서 javac 이 **"그 `instanceof` 는 절대 참이 될 수 없다"**고 컴파일에서 막는다.
- 대안은 **필드는 `null` 허용, 접근자가 봉투를 만드는 것**이다.

```java
static class GoodUser implements Serializable {
    String nickname = "닉";                                    // 필드는 평범한 타입
    Optional<String> nickname() { return Optional.ofNullable(nickname); }   // 반환 타입이 봉투
}
```

- 이 형태가 javadoc 의 `@apiNote`(반환 타입)와 정확히 맞는다.

#### 2. `Optional` 을 파라미터로 — 호출자가 셋을 넘길 수 있다

**출력** (`Ex.java (38-b)`)

```text
--- 2. Optional 파라미터 — 호출자가 셋을 넘길 수 있다 ---
greetBad(Optional.of("철")) : 안녕 철
greetBad(Optional.empty())   : 안녕 손님
greetBad(null)               -> java.lang.NullPointerException: Cannot invoke "java.util.Optional.orElse(Object)" because "nick" is null
greetGood("철") / greetGood(null) : 안녕 철 / 안녕 손님
```

```text
  void f(Optional<String> nick)              void f(String nick)
  +--------------------------------+         +--------------------------------+
  | 호출자가 넘길 수 있는 것 셋     |         | 호출자가 넘길 수 있는 것 둘     |
  |   Optional.of("철")            |         |   "철"                         |
  |   Optional.empty()             |         |   null                         |
  |   null            ★ 여전히 있다 |         |                                |
  +--------------------------------+         +--------------------------------+
    "없음"의 표현이 둘로 늘었다                 원래대로 둘이다
    그리고 호출자가 매번 감싸야 한다
```

- ★ **`null` 을 없애려고 넣었는데 `null` 이 그대로 남고, 상태만 하나 늘었다.**
- 게다가 호출하는 쪽이 **매번 `Optional.of(...)` 로 감싸야** 한다 — 호출부가 더 지저분해진다.
- 선택 인자가 필요하면 **오버로드**를 쓴다. 인자가 많으면 파라미터 객체나 빌더로 간다.

#### 3. 컬렉션 원소로 — 상태가 셋이 된다

**출력** (`Ex.java (38-b)`)

```text
--- 3. 컬렉션 원소로 쓰면 — 상태가 셋이 된다 ---
map            : {a=Optional[값], b=Optional.empty}
m.get("b")     : Optional.empty   (키는 있는데 값이 비었다)
m.get("없는키") : null   (키 자체가 없다)
셋을 구분하려면 containsKey 까지 봐야 한다 : true / false
```

```text
  Map<String, Optional<String>> 의 상태 셋

  1. 키가 없다              get -> null            ★ 봉투가 아니다
  2. 키가 있고 값이 비었다   get -> Optional.empty
  3. 키가 있고 값이 있다     get -> Optional[값]
```

- **`Map` 은 이미 "없음"을 표현할 수 있다.** 그 위에 봉투를 얹으면 상태가 둘에서 셋으로 는다.
- 그리고 **1번은 여전히 `null` 이다.** `Optional` 이 아무것도 안 막았다.
- 원소마다 봉투 객체가 하나씩 더 생기는 비용도 있다.

#### 4. ★ 봉투 자체가 `null` 일 수 있다

**출력** (`Ex.java (38-b)`)

```text
--- 5. Optional 자체가 null 일 수 있다 ---
null 인 Optional 에 isPresent() -> java.lang.NullPointerException: Cannot invoke "java.util.Optional.isPresent()" because "nullOpt" is null
```

- javadoc 이 "A variable whose type is `Optional` should never itself be `null`" 이라고 **요구**했지만,
  언어는 **아무것도 강제하지 않는다.**
- 그래서 `Optional` 을 돌려주는 메서드는 **절대 `null` 을 돌려주면 안 된다.**\
  값이 없으면 `Optional.empty()` 다 — 이것이 이 타입을 쓰는 최소 규율이다.

#### 5. `isPresent()` + `get()` — 길어진 `if`

**출력** (`Ex.java (38-b)`)

```text
--- 4. isPresent() + get() 대 map/orElse ---
isPresent+get : HELLO
map+orElse    : HELLO
```

```java
// 얻은 것이 없다 — null 검사를 길게 쓴 것일 뿐
String bad;
if (o.isPresent()) bad = o.get().toUpperCase(); else bad = "없음";

// 엮어 쓴다
String good = o.map(String::toUpperCase).orElse("없음");
```

- 결과는 같다. 다른 것은 **`get()` 을 쓰는 곳이 남는가**다.
- `isPresent()` 를 쓸 자리는 **부수효과만 필요할 때**이고, 그때도 `ifPresent`/`ifPresentOrElse` 가 낫다.

#### 6. 값 기반 클래스에 `synchronized`

**출력** (`Ex.java (38-d)`, `javac -Xlint:all`)

```text
Ex.java:5: warning: [synchronization] attempt to synchronize on an instance of a value-based class
        synchronized (o) { System.out.println("동기화 블록 안 : " + o); }
        ^
1 warning
동기화 블록 안 : Optional[x]
```

- **경고만 나고 실행은 된다.** 지금은 동작하지만 javadoc 이 "in a future release, synchronization may fail" 이라고 적었다.
- 같은 이유로 `==` 로 비교하지 않는다. `Optional.empty()` 가 싱글턴이라는 보장이 없다((2)).

비용 — 없다. 판단 규칙이다.

### (6) 엮어 쓰기 — 스트림과 만나는 자리

**언제 쓰나** — 여러 단계를 지나 값이 하나 나오는 흐름. `if` 를 안 쓴다.

```java
String domain = find(id)                       // Optional<User>
        .map(User::email)                      // Optional<String>  (email 이 null 이면 empty)
        .filter(e -> e.contains("@"))          // 조건 불통과면 empty
        .map(e -> e.substring(e.indexOf('@') + 1))
        .orElse("(알 수 없음)");                // 마지막에 한 번만 꺼낸다
```

**출력** (`Ex.java (38-c)`, JDK 21.0.5 — 17·25 동일)

```text
--- 2. 사슬로 잇기 — 아이디에서 이메일 도메인까지 ---
  u1           -> x.com
  u2           -> (알 수 없음)
  없는아이디        -> (알 수 없음)
  u3           -> x.com
```

```text
  find("u2")  ->  Optional[User[u2, null]]
       |
   .map(User::email)      email 이 null 이다
       |                  -> map 이 자동으로 empty 로 바꾼다  ★
       v
   Optional.empty
       |
   .filter / .map          빈 봉투에는 아무것도 안 한다
       |
       v
   Optional.empty
       |
   .orElse("(알 수 없음)")
       |
       v
   "(알 수 없음)"
```

- ★ **`u2` 와 "없는아이디" 가 같은 답으로 합류한다.** "사용자가 없다"와 "이메일이 없다"를 한 흐름으로 처리했다.
- 빈 봉투는 이후 단계를 **전부 건너뛴다.** `if (x != null)` 을 네 번 쓰지 않아도 된다.

★ **스트림에서 `Optional` 을 펼치는 두 방법**이 있다(같은 프로그램).

```text
--- 1. 스트림에서 Optional 을 펼치는 두 방법 ---
filter(isPresent).map(get) : [User[id=u1, email=a@x.com], User[id=u2, email=null], User[id=u3, email=c@x.com]]
flatMap(Optional::stream)  : [User[id=u1, email=a@x.com], User[id=u2, email=null], User[id=u3, email=c@x.com]]
두 결과가 같은가            : true
```

```java
ids.stream().map(this::find).filter(Optional::isPresent).map(Optional::get).toList();  // 8 부터. get 이 남는다
ids.stream().map(this::find).flatMap(Optional::stream).toList();                        // 9 부터. get 이 없다 ★
```

- **결과는 같다.** 다른 것은 `get()` 이 코드에 남는가다.
- `Optional.stream()` 은 **Java 9**(`@since 9`, src.zip 확인)에 이것을 위해 추가됐다.

최종 연산이 `Optional` 을 돌려주는 자리들이다.

```text
--- 3. 최종 연산이 돌려주는 Optional ---
findFirst()                : Optional[1]
빈 스트림의 findFirst()     : Optional.empty
max(naturalOrder())        : Optional[3]
reduce(Integer::sum)       : Optional[6]
IntStream.average()        : OptionalDouble[2.0]
빈 IntStream 의 average()   : OptionalDouble.empty
```

- 기본형 스트림은 **`OptionalInt`·`OptionalLong`·`OptionalDouble`** 이라는 별도 타입을 쓴다(박싱을 피하려고).\
  API 가 비슷하지만 **`map`·`flatMap`·`filter` 가 없다.**
- 왜 이 자리들이 `Optional` 인지는 [`../46-terminal-operations/`](../46-terminal-operations/) 가 정본이다.

`or` 로 대체 경로를 잇는 것도 된다(Java 9).

```text
--- 4. or 로 대체 경로 잇기 ---
find(없는아이디).or(find(u1)) : u1
```

비용 — 단계마다 `Optional` 객체가 하나씩 생긴다. 핫 루프에서는 의미가 있을 수 있으나,\
**이 문서에서 측정하지 않았다** — 측정 없이 "느리다"고 적지 않는다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다.

### ★ 메서드별 버전 — `@since` 를 직접 읽고 컴파일로 재확인

`src.zip` 의 `Optional.java` 에서 읽은 `@since` 다.

| 메서드 | `@since` | 비고 |
|---|---|---|
| `empty` · `of` · `ofNullable` | 1.8 | (클래스 자체가 `@since 1.8`) |
| `get` · `isPresent` · `ifPresent` | 1.8 | |
| `filter` · `map` · `flatMap` | 1.8 | |
| `orElse` · `orElseGet` · `orElseThrow(Supplier)` | 1.8 | |
| **`ifPresentOrElse`** | **9** | |
| **`or`** | **9** | |
| **`stream`** | **9** | |
| **`orElseThrow()`** (인자 없음) | **10** | |
| **`isEmpty`** | **11** | |

★ 같은 소스를 `--release` 만 바꿔 컴파일해 **재확인**했다(`Ex.java (38-e)`, JDK 21.0.5 의 javac).

```text
$ javac --release 8 Ex.java
Ex.java:5: error: cannot find symbol
        o.ifPresentOrElse(v -> {}, () -> {});   // 9
         ^
  symbol:   method ifPresentOrElse((v)->{ },()->{ })
Ex.java:6: error: cannot find symbol
        o.or(() -> Optional.of("y"));           // 9
Ex.java:7: error: cannot find symbol
        o.stream().count();                     // 9
Ex.java:8: error: method orElseThrow in class Optional<T> cannot be applied to given types;
        o.orElseThrow();                        // 10
  required: Supplier<? extends X>
  found:    no arguments
Ex.java:9: error: cannot find symbol
        System.out.println(o.isEmpty());        // 11
5 errors

$ javac --release 9  -> 2 errors (orElseThrow() 와 isEmpty)
$ javac --release 10 -> 1 error  (isEmpty)
$ javac --release 11 -> 성공
```

- ★ **`orElseThrow()` 만 에러 모양이 다르다.** 8에도 `orElseThrow(Supplier)` 가 있어서 `cannot find symbol` 이 아니라
  **"cannot be applied to given types"** 가 나온다. 오버로드가 추가된 것이기 때문이다.
- 기억으로 쓰면 틀린다. **`@since` 를 읽고, 의심되면 `--release` 로 컴파일한다.**

### 전체 API 지도

| 하는 일 | 메서드 | 돌려주는 것 |
|---|---|---|
| 만들기 | `of` · `ofNullable` · `empty` | `Optional<T>` |
| 있나 보기 | `isPresent` · `isEmpty`(11) | `boolean` |
| 부수효과 | `ifPresent` · `ifPresentOrElse`(9) | `void` |
| 변환 | `map` · `flatMap` · `filter` | `Optional<U>` |
| 대체 봉투 | `or`(9) | `Optional<T>` |
| 스트림으로 | `stream`(9) | `Stream<T>` |
| 꺼내기(기본값) | `orElse` ★ · `orElseGet` | `T` |
| 꺼내기(예외) | `get` · `orElseThrow`(10) · `orElseThrow(Supplier)` | `T` |

### `map` 과 `flatMap` 의 구분

```java
Optional<String> src = Optional.of("씨앗");
src.map(v -> Optional.of(v.length()));      // Optional[Optional[2]]   ★ 봉투가 두 겹
src.flatMap(v -> Optional.of(v.length()));  // Optional[2]
```

**출력** (`Ex.java (38-b)`)

```text
--- 6. Optional<Optional<T>> 은 map 이 만든다 ---
map(v -> Optional.of(..))     : Optional[Optional[2]]
flatMap(v -> Optional.of(..)) : Optional[2]
```

- **함수가 `Optional` 을 돌려주면 `flatMap`**, 평범한 값을 돌려주면 `map`.
- 스트림의 `map`/`flatMap` 과 정확히 같은 구분이다([`../45-intermediate-operations/`](../45-intermediate-operations/)).

### `equals`·`hashCode`·`toString`

**출력** (`Ex.java (38-a)`)

```text
--- 6. equals / hashCode / toString ---
Optional.of("값").equals(Optional.of("값")) : true
Optional.empty() == Optional.empty()        : true
Optional.of("값").hashCode()                : 44050  / "값".hashCode() = 44050
Optional.empty().hashCode()                 : 0
```

- `equals` 는 **안의 값을 비교**한다. 봉투끼리 비교해도 된다.
- `hashCode` 는 **안의 값의 것을 그대로** 돌려준다(빈 봉투는 `0`).
- `==` 가 `true` 로 나왔지만 **이것에 의존하면 안 된다** — javadoc 이 싱글턴 보장이 없다고 명시했다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 「동작 방식」 (5)에서 안티패턴 여섯을 실측으로 보였고, 여기서는 **판단**을 정리한다.

### 1. ★ `orElse` 에 메서드 호출을 넣는다

```java
return findUser(id).orElse(userRepository.createGuest());   // 사용자가 있어도 게스트를 만든다
```

- (4)에서 실측한 그대로다 — **값이 있어도 인자는 평가된다.**
- 증상이 **성능 저하나 유령 데이터**로 나타난다. 예외가 아니라 조용한 낭비다.
- 판정: **인자가 리터럴·상수면 `orElse`, 그 밖에는 `orElseGet`.**

### 2. `Optional` 을 "NPE 방지 장치"로 오해한다

- `Optional` 은 **NPE 를 못 막는다.** 봉투 자체가 `null` 일 수 있고((5) 4번), `get()` 을 부르면 다른 예외가 난다.
- `Optional` 이 하는 일은 **"없을 수 있음"을 시그니처에 적는 것**뿐이다. 그다음은 사람이 처리한다.
- `null` 을 막는 장치는 다른 것이다 — `Objects.requireNonNull`·경계 검증([`../60-null-handling/`](../60-null-handling/)).

### 3. `get()` 을 그냥 쓴다

```java
Optional<User> u = find(id);
return u.get();     // 비면 NoSuchElementException: No value present
```

- `null` 검사를 안 한 것과 **같은 수준**이다. 봉투를 씌운 보람이 없다.
- 대안 셋 — `orElseThrow(() -> new UserNotFound(id))` / `orElse(기본값)` / `map(...).orElse(...)`.
- `orElseThrow()`(인자 없음, 10+)는 `get()` 과 완전히 같지만 **이름이 위험을 말한다.**

### 4. 필드·파라미터·컬렉션 원소로 쓴다

- (5) 1~3번의 실측이 근거다 — **직렬화 실패 · 상태 증가 · 호출부 오염.**
- 판정 한 줄: **javadoc 이 "method return type" 이라고 적었다.** 그 밖의 자리는 이유를 대야 한다.

### 5. 빈 `Optional` 을 예외 상황에 쓴다

```java
Optional<Config> loadRequiredConfig();   // 이건 없으면 예외여야 한다
```

- javadoc 의 조건은 **"a clear need to represent 'no result'"** — **결과 없음이 정상인 경우**다.
- 필수 설정이 없다, 권한이 없다 같은 것은 **예외**다. 봉투로 감싸면 호출자가 조용히 넘겨 버린다.
- 예외와 값의 경계는 [`../25-exceptions/`](../25-exceptions/) 가 정본이다.

### 6. 기본형 `Optional` 을 모르고 박싱한다

```java
IntStream.of(1, 2, 3).average();      // OptionalDouble  — Optional<Double> 이 아니다
```

- `OptionalInt`·`OptionalLong`·`OptionalDouble` 은 **별도 클래스**이고 `map`/`flatMap`/`filter` 가 없다.
- 변환이 필요하면 `stream().boxed()` 로 먼저 박싱하거나, `getAsDouble()`·`orElse(0.0)` 로 꺼낸다.
- 기본형 스트림의 정본은 [`../44-stream-creation/`](../44-stream-creation/).

## 구현 세부사항 대 언어 보장

이 절은 **"어디까지 믿어도 되나"**를 가른다.

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| `Optional` 의 용도는 **메서드 반환 타입** | **javadoc (`@apiNote`)** | "primarily intended for use as a method return type" |
| `Optional` 변수 자체가 `null` 이면 안 된다 | **javadoc 의 요구** — 강제는 **없다** | "should never itself be `null`". 언어는 막지 않는다(실측) |
| `of(null)` 이 NPE | **javadoc (계약)** | `@throws NullPointerException if value is null` |
| 빈 봉투에 `get()`/`orElseThrow()` 가 `NoSuchElementException` | **javadoc (계약)** | 두 메서드의 `@throws` |
| `orElse` 의 인자가 항상 평가됨 | **언어 규칙 (JLS)** | 메서드 호출의 인자 평가 규칙. `Optional` 과 무관 |
| `map` 이 `null` 을 `empty` 로 바꿈 | **구현 (소스 그대로)** | `Optional.java` 261행 `return Optional.ofNullable(mapper.apply(value));` |
| `get()` 보다 `orElseThrow()` 를 쓰라는 것 | **javadoc (`@apiNote`)** | "The preferred alternative to this method is `orElseThrow()`" |
| `Optional` 이 `Serializable` 이 아님 | **API 정의** | 클래스 선언에 `implements Serializable` 이 없다 |
| `Optional.empty()` 가 싱글턴 | **아니다 — 보장 없음** | javadoc: "There is no guarantee that it is a singleton" |
| `==` 비교가 `true` 로 나온 것 | **구현 세부(관찰)** | 21.0.5 에서 `EMPTY` 상수를 공유한다. 보장이 아니다 |
| 예외 메시지 `No value present` | **구현 세부** | 소스의 문자열 리터럴. 17·21·25 에서 같았다 |
| `NotSerializableException: java.util.Optional` 문구 | **구현 세부** | 17·21·25 에서 같았다 |
| `synchronized` 경고 | **구현 세부 + 컴파일 옵션** | `-Xlint:synchronization`. 값 기반 클래스라는 사실은 javadoc |

**경계 한 줄** — `Optional[값]`·`Optional.empty` 같은 `toString` 형태와 예외 메시지는 **관찰**이고,
"반환 타입에 쓰라"·"`of(null)` 은 NPE"·"`map` 이 `null` 을 `empty` 로 바꾼다"는 **javadoc 의 계약**이다.\
외울 것은 메시지가 아니라 **"봉투는 반환 자리에 씌운다"** 는 성질이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 판단 |
|---|---|
| 조회 메서드의 반환 타입 — 없을 수 있다 | **쓴다.** `Optional<User> findById(id)` |
| 스트림의 `findFirst`·`min`·`max`·`reduce` | 이미 `Optional` 이다. 그대로 이어 쓴다 |
| 값이 없으면 **예외**여야 한다 | **안 쓴다.** 예외를 던진다 |
| 필드 | **안 쓴다.** 필드는 `null` 허용, 접근자가 봉투를 만든다 |
| 파라미터 | **안 쓴다.** 오버로드나 파라미터 객체 |
| 컬렉션 원소·`Map` 값 | **안 쓴다.** 컬렉션이 이미 "없음"을 표현한다 |
| 기본값이 리터럴·상수 | `orElse` |
| 기본값이 계산·조회·객체 생성 | **`orElseGet`** |
| 여러 단계 변환 | `map`/`flatMap`/`filter` 로 엮고 **마지막에 한 번만** 꺼낸다 |
| 스트림에서 `Optional` 펼치기 | `flatMap(Optional::stream)` (9+) |
| 값을 반드시 꺼내야 한다 | `orElseThrow(() -> 내예외)`. `get()` 은 쓰지 않는다 |
| DTO·엔티티에 넣어 직렬화 | **못 쓴다.** `NotSerializableException` |

판단 규칙 세 줄.

- **봉투는 반환 자리에만 씌운다.** javadoc 이 그렇게 적었고, 다른 자리는 전부 잃는 것이 있다.
- **`orElse` 의 인자는 반드시 평가된다.** 계산이면 `orElseGet`.
- **`get()` 이 코드에 남으면 아직 안 엮은 것이다.** `map`/`orElse`/`orElseThrow` 로 끝낸다.

## 핵심 문장

- `Optional` 은 **"결과 없음"을 반환 타입으로 표현**하려고 만들어졌다 — javadoc 의 `@apiNote` 가 "primarily intended for use as a method return type" 이라고 직접 못 박았다.
- ★ **`orElse` 의 인자는 값이 있어도 항상 평가된다.** 부작용 있는 메서드를 넣으면 실행으로 바로 보인다(호출 횟수 1 대 0).
- **`get()` 과 `orElseThrow()` 는 같은 예외·같은 메시지**(`NoSuchElementException: No value present`)다. 10부터는 이름이 위험을 말하는 쪽을 쓴다.
- **`map` 에 넘긴 함수가 `null` 을 돌려주면 자동으로 빈 봉투가 된다.** 그래서 `null` 을 돌려주는 옛 API 와 이어 붙일 수 있다.
- ★ **`Optional` 은 `Serializable` 이 아니다.** 필드에 두면 `NotSerializableException: java.util.Optional` 이고, `instanceof Serializable` 은 **컴파일 에러**다.
- ★ **봉투 자체가 `null` 일 수 있다.** javadoc 이 금지했지만 언어는 막지 않는다 — `Optional` 을 돌려주는 메서드는 절대 `null` 을 돌려주지 않는다.
- 메서드마다 **버전이 갈린다** — `ifPresentOrElse`·`or`·`stream` 은 9, `orElseThrow()` 는 10, `isEmpty` 는 11. 기억이 아니라 `@since` 와 `--release` 로 확인한다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 38번)
- [`../60-null-handling/`](../60-null-handling/) — **그쪽은 `null` 을 어느 계층에서 막을지(생성자 검증·`Objects.requireNonNull`·경계)까지, 여기는 `Optional` 이라는 타입 하나의 생성·소비·안티패턴부터.**\
  "반환값에는 `Optional`"이라는 판단 자체는 그쪽의 세 방어 시점 중 하나로 다뤄진다
- [`../46-terminal-operations/`](../46-terminal-operations/) — **`findFirst`·`min`·`max`·인자 없는 `reduce` 가 왜 `Optional` 을 돌려주는지의 정본.**\
  여기서는 그 결과를 받아 어떻게 쓰는지만 다룬다
- [`../45-intermediate-operations/`](../45-intermediate-operations/) — `map`/`flatMap` 의 구분이 정본. `Optional` 의 둘도 같은 규칙이다
- [`../44-stream-creation/`](../44-stream-creation/) — `OptionalInt`/`OptionalDouble` 이 나오는 기본형 스트림
- [`../25-exceptions/`](../25-exceptions/) — **"없음"을 빈 봉투로 표현할지 예외로 표현할지**의 경계. 예외 설계는 그쪽이 정본
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — `Optional.equals` 가 안의 값을 비교한다는 것의 배경
- [`../03-variables-and-assignment/`](../03-variables-and-assignment/) — `orElse` 인자가 왜 항상 평가되는지(자바의 인자 평가 규칙)
- [`../31-functional-interfaces/`](../31-functional-interfaces/) — `orElseGet`·`or`·`orElseThrow` 가 받는 `Supplier`
- [`../14-records/`](../14-records/) — `Optional` 필드 대신 `record` 로 "없음"을 표현하는 다른 방법(`sealed` + 결과 타입)
- 목록의 **41번 주제**(`Map` API) — `Map` 이 이미 "없음"을 표현한다는 것(`getOrDefault`·`containsKey`)

## 용어 풀이

- **`Optional<T>`** — 값이 있을 수도 없을 수도 있음을 타입으로 표현하는 컨테이너(Java 8, `java.util`).
- **`of`** — 값이 `null` 이 아님을 주장하며 만드는 팩토리. `null` 이면 NPE.
- **`ofNullable`** — `null` 이면 빈 `Optional` 을 만드는 팩토리. `null` 을 다루는 경계에서 쓴다.
- **`empty`** — 빈 `Optional`. 싱글턴이라는 보장은 없다.
- **`orElse`** — 비었을 때 돌려줄 값을 **인자로** 받는다. 인자는 항상 평가된다.
- **`orElseGet`** — 비었을 때 돌려줄 값을 **`Supplier` 로** 받는다. 필요할 때만 평가된다.
- **`orElseThrow()`** — 비었으면 `NoSuchElementException`. `get()` 과 같지만 이름이 위험을 말한다(Java 10).
- **`NoSuchElementException`** — 가져올 원소가 없다는 런타임 예외. 메시지는 `No value present`.
- **`flatMap`** — 함수가 `Optional` 을 돌려줄 때 겹치는 봉투를 한 겹으로 펴 주는 변환.
- **값 기반 클래스(value-based class)** — 동등한 인스턴스를 서로 바꿔 써도 되는 클래스. 동기화·정체성 비교를 하면 안 된다.
- **`NotSerializableException`** — 직렬화할 수 없는 객체가 객체 그래프에 있을 때 나는 예외.
- **안티패턴(anti-pattern)** — 흔히 쓰이지만 문제를 해결하기보다 더 만드는 방식.

## 더 들어가면

- **`Optional` 은 처음부터 "스트림의 반환 타입"으로 설계됐다.**\
  Java 8 에서 `findFirst`·`min`·`max`·`reduce` 가 "결과가 없을 수 있다"를 표현할 방법이 필요했다.\
  그래서 `java.util` 에 있고 `java.lang` 에 없다 — **범용 `null` 대체재가 아니다.**
- **`Optional.stream()`(9)이 생기기 전에는 `filter(Optional::isPresent).map(Optional::get)` 가 관용구였다.**\
  결과가 같다는 것을 실행으로 확인했다(`Ex.java (38-c)`). 지금은 `flatMap(Optional::stream)` 한 줄이다.
- **`OptionalInt`/`OptionalLong`/`OptionalDouble` 에는 `map`·`flatMap`·`filter` 가 없다.**\
  박싱을 피하려고 만든 타입인데 변환 메서드를 주면 다시 박싱이 생기기 때문이다.\
  변환이 필요하면 `stream().boxed()` 로 먼저 박싱한다.
- **`Optional` 필드가 필요해 보이면 대개 타입 설계가 덜 된 것이다.**\
  "상태가 둘 이상"이라는 뜻이므로 `sealed` 인터페이스 + `record` 로 상태를 나누는 편이 낫다.\
  [`../15-sealed-classes/`](../15-sealed-classes/)·[`../14-records/`](../14-records/).
- **`Optional` 은 `@jdk.internal.ValueBased` 다.**\
  `synchronized (opt)` 는 `-Xlint:synchronization` 에서 경고가 나고, javadoc 은 "in a future release, synchronization may fail" 이라고 적었다.\
  `==` 비교도 같은 이유로 금지다 — 실측에서 `Optional.empty() == Optional.empty()` 가 `true` 였지만 **보장이 아니다.**
