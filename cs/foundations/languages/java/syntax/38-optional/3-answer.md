# java/syntax/38 — `Optional`: 생성·소비·안티패턴 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·예외·컴파일 에러는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 실행 프로그램 셋을 **17.0.13 · 25.0.1** 에서도 돌려 **출력이 한 글자도 다르지 않았다**\
> (관찰이다 — 보장은 javadoc 인용으로만 적었다).\
> 버전 정보는 `lib/src.zip` 의 `@since` 를 직접 읽고 `javac --release` 로 재확인했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `Optional` 은 무엇을 위해 만들어졌는가

**javadoc `@apiNote` 원문** (`java.base/java/util/Optional.java`, JDK 21.0.5)

> `Optional` is primarily intended for use as a method return type where
> there is a clear need to represent "no result," and where using `null`
> is likely to cause errors. A variable whose type is `Optional` should
> never itself be `null`; it should always point to an `Optional`
> instance.

**지정된 용도 하나**

> **메서드 반환 타입**(method return type)이다.

- "primarily intended for use as a **method return type**" — 필드도 파라미터도 컬렉션 원소도 아니다.
- 이 한 구절이 **모든 안티패턴 판정의 근거**다.

**같은 문단의 나머지 둘**

| 요구 | 뜻 |
|---|---|
| "a clear need to represent 'no result'" | **결과 없음이 정상인 경우**여야 한다. 예외 상황이면 예외를 던진다 |
| "A variable whose type is `Optional` should never itself be `null`" | **봉투 자체가 `null` 이면 안 된다** |

**언어가 강제하지 않는 것**

- ★ **세 번째다.** `Optional<String> o = null;` 은 그냥 컴파일되고, 쓰면 평범한 NPE 가 난다(11번에서 실측).
- 첫째·둘째도 **강제가 아니다.** 필드에 써도 컴파일은 된다 — 다만 직렬화에서 터진다(5번).
- 즉 `Optional` 의 규율은 **전부 사람이 지키는 것**이다. 컴파일러는 도와주지 않는다.

### 2. 이 네 줄의 출력은 무엇인가

**출력** (`Ex.java (38-a)`, JDK 21.0.5 — 17·25 동일)

```text
--- 1. 생성 세 가지 ---
Optional.of("값")        : Optional[값]
Optional.ofNullable(null) : Optional.empty
Optional.empty()          : Optional.empty
Optional.of(null)         -> java.lang.NullPointerException: null
```

> 마지막 줄의 `null` 은 **예외 메시지가 없다**는 뜻이다.
> 프로그램이 `e.getMessage()` 를 이어 붙였고 그 값이 `null` 이라 `"null"` 로 찍혔다.

**앞 세 줄**

| 식 | 출력 |
|---|---|
| `Optional.of("값")` | `Optional[값]` |
| `Optional.ofNullable(null)` | `Optional.empty` |
| `Optional.empty()` | `Optional.empty` |

- `toString` 형태가 **`Optional[값]` / `Optional.empty`** 로 갈린다. 대괄호 유무로 눈에 보인다.

**마지막 줄**

- **`NullPointerException`** 이고 **메시지가 없다**(`getMessage()` 가 `null`).
- 소스가 한 줄이기 때문이다.

```java
// JDK 21.0.5  java.base/java/util/Optional.java  112~114행 — 실제 소스 그대로
public static <T> Optional<T> of(T value) {
    return new Optional<>(Objects.requireNonNull(value));
}
```

- `Objects.requireNonNull(obj)`(메시지 없는 오버로드)가 `new NullPointerException()` 을 던지므로 메시지가 없다.\
  메시지 있는 형태는 [**60번 주제**](../60-null-handling/)가 다룬다.
- javadoc 에도 `@throws NullPointerException if value is null` 로 명시돼 있다 — **계약**이다.

**`of` 와 `ofNullable` 을 각각 언제**

```text
   of(v)                                     ofNullable(v)
  +-----------------------------------+     +-----------------------------------+
  | "여긴 절대 null 이 아니다" 를 주장 |     | "null 일 수 있다" 를 봉투로 바꾼다 |
  | 틀리면 그 자리에서 NPE            |     | null 이면 empty                   |
  | -> 버그가 즉시 드러난다 ★         |     | -> null 을 다루는 경계에서 쓴다    |
  +-----------------------------------+     +-----------------------------------+
```

- 전부 `ofNullable` 로만 쓰면 **버그를 봉투에 담아 흘려보낸다.** "여기선 `null` 이 아니어야 한다"는 자리에는 `of` 를 쓴다.

### 3. ★ 이 네 경우에 `expensive()` 는 몇 번 불리는가

**출력** (`Ex.java (38-a)`, JDK 21.0.5 — 17·25 동일)

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

**호출 횟수**

| | `orElse` | `orElseGet` |
|---|---|---|
| 값이 **있는** 봉투 | **1회** ★ (결과에 안 쓰임) | **0회** |
| 값이 **없는** 봉투 | 1회 | 1회 |

- ★ **(A)가 핵심이다.** 값이 있어서 결과에 쓰이지도 않는데 **만들어 놓고 버렸다.**

```text
  some.orElse(expensive())                    some.orElseGet(Ex::expensive)
  +-----------------------------------+       +-----------------------------------+
  | 1. expensive() 를 부른다 ★        |       | 1. 람다 객체만 만든다              |
  |    -> "불렸다" 가 찍힌다           |       |                                   |
  | 2. 그 반환값을 인자로 넘긴다       |       | 2. Supplier 를 인자로 넘긴다       |
  | 3. orElse 가 "값이 있네" 하고      |       | 3. "값이 있네" 하고 원래 값 반환   |
  |    원래 값을 돌려준다              |       |    -> supplier.get() 은 안 불린다  |
  +-----------------------------------+       +-----------------------------------+
```

**`Optional` 의 특별한 동작인가**

- ★ **아니다. 자바의 평범한 인자 평가 규칙**이다.
- 메서드를 부르려면 **인자를 먼저 평가해야** 한다. 자바에는 지연 인자(lazy argument)가 없다.
- `orElse(x)` 는 **`x` 라는 값**을 받고, `orElseGet(s)` 는 **`s` 라는 "값을 만드는 방법"** 을 받는다.\
  지연을 만들려면 **함수로 감싸는 수밖에 없고**, 그래서 `Supplier` 오버로드가 따로 있다.
- 이 규칙의 정본은 [`../03-variables-and-assignment/`](../03-variables-and-assignment/), `Supplier` 는 [`../31-functional-interfaces/`](../31-functional-interfaces/).

**판정 기준 한 줄**

> **인자가 리터럴·이미 있는 상수면 `orElse`, 계산·조회·객체 생성이면 `orElseGet`.**

```java
opt.orElse("기본값")                    // O — 리터럴
opt.orElse(DEFAULT)                      // O — 이미 있는 상수
opt.orElse(new ArrayList<>())            // 주의 — 매번 새 리스트를 만들어 버린다
opt.orElse(repository.findDefault())     // X — 값이 있어도 DB 를 친다 ★
opt.orElseGet(repository::findDefault)   // O
```

### 4. 빈 `Optional` 에서 값을 꺼내려 하면

**출력** (`Ex.java (38-a)`, JDK 21.0.5 — 17·25 동일)

```text
--- 3. 비어 있는 것에서 값을 꺼내려 하면 ---
get()          -> java.util.NoSuchElementException: No value present
orElseThrow()  -> java.util.NoSuchElementException: No value present
orElseThrow(공급자) -> java.lang.IllegalStateException: 사용자가 없다
```

**세 예외**

| 호출 | 예외 | 메시지 |
|---|---|---|
| `get()` | `java.util.NoSuchElementException` | `No value present` |
| `orElseThrow()` | `java.util.NoSuchElementException` | `No value present` |
| `orElseThrow(공급자)` | **내가 만든 예외** | 내가 쓴 메시지 |

**`get()` 과 `orElseThrow()` 의 차이**

- **동작은 완전히 같다.** 같은 예외 타입, 같은 메시지다. 소스도 둘 다 같은 한 줄을 던진다.
- **다른 것은 이름뿐**이다 — `get()` 은 "가져온다"라 안전해 보이고, `orElseThrow()` 는 **"아니면 던진다"가 이름에 있다.**
- `orElseThrow()`(인자 없음)는 **Java 10** 부터다. 8~9 에는 `orElseThrow(Supplier)` 만 있었다.

**javadoc 이 어느 것을 쓰라고 했나**

★ `get()` 의 `@apiNote` 가 직접 적어 두었다.

> The preferred alternative to this method is {@link #orElseThrow()}.

- **`orElseThrow()` 를 쓰라**는 것이다. 실무에서는 대개 `orElseThrow(() -> new 내예외(id))` 로 **원인을 담는다.**

> **`NoSuchElementException`** — "가져올 원소가 없다"를 뜻하는 `java.util` 의 런타임 예외.\
> 예: 빈 `Optional` 에 `get()`, 빈 `Iterator` 에 `next()`.

### 5. ★ `Optional` 을 필드에 두면 무엇이 깨지는가

**출력** (`Ex.java (38-b)`, JDK 21.0.5 — 17·25 동일)

```text
--- 1. Optional 은 직렬화되지 않는다 ---
Optional 이 Serializable 인가 : false
BadUser  직렬화 -> java.io.NotSerializableException: java.util.Optional
GoodUser 직렬화 : 성공 (88 바이트)
```

**직렬화하면**

- **`java.io.NotSerializableException: java.util.Optional`** 이 난다.
- `BadUser` 자신은 `Serializable` 인데, **필드 하나가 아니라서** 객체 그래프를 쓰다가 터진다.
- 증상이 **저장할 때가 아니라 캐시·세션·RPC 경계에서** 나타나기 때문에 늦게 발견된다.

**마지막 줄** — 찍히지 않는다. **컴파일 에러**다(`Ex.java (38-b2)`).

```text
Ex.java:5: error: incompatible types: Optional<String> cannot be converted to Serializable
        System.out.println(Optional.of("x") instanceof Serializable);
                                      ^
1 error
```

- ★ **컴파일러가 이미 안다.** `Optional` 은 `final` 이고 `Serializable` 을 구현하지 않으므로,
  javac 이 **"그 `instanceof` 는 절대 참이 될 수 없다"** 고 판단해 컴파일에서 막는다.
- 런타임에 확인하려면 `Serializable.class.isAssignableFrom(Optional.class)` 를 쓴다 — 결과는 `false`.

**대안**

```java
class GoodUser implements Serializable {
    String nickname = "닉";                                          // 필드는 평범한 타입
    Optional<String> nickname() { return Optional.ofNullable(nickname); }   // 반환 타입이 봉투
}
```

```text
  Optional 을 필드로                         필드는 null 허용, 접근자가 봉투
  +-----------------------------------+     +-----------------------------------+
  | NotSerializableException          |     | 직렬화 성공 (88 바이트)            |
  | 상태가 셋 (null / empty / 값)      |     | 상태가 둘 (null / 값)             |
  | javadoc 의 용도와 어긋난다         |     | javadoc 의 용도와 정확히 맞는다 ★ |
  +-----------------------------------+     +-----------------------------------+
```

- 이 형태가 `@apiNote` 의 **"method return type"** 과 정확히 맞는다.

### 6. `Optional` 을 파라미터로 두면 무엇이 늘어나는가

**출력** (`Ex.java (38-b)`, JDK 21.0.5 — 17·25 동일)

```text
--- 2. Optional 파라미터 — 호출자가 셋을 넘길 수 있다 ---
greetBad(Optional.of("철")) : 안녕 철
greetBad(Optional.empty())   : 안녕 손님
greetBad(null)               -> java.lang.NullPointerException: Cannot invoke "java.util.Optional.orElse(Object)" because "nick" is null
greetGood("철") / greetGood(null) : 안녕 철 / 안녕 손님
```

**호출자가 넘길 수 있는 값**

- **세 가지**다 — `Optional.of(v)` · `Optional.empty()` · **`null`**.

**`greet(null)` 은**

- **`NullPointerException`** 이다. 메시지가 `because "nick" is null` 이라 원인을 짚어 준다(helpful NPE).

**무엇이 남았나**

```text
  void f(Optional<String> nick)              void f(String nick)
  +--------------------------------+         +--------------------------------+
  | "없음" 의 표현이 둘            |         | "없음" 의 표현이 하나          |
  |   Optional.empty()             |         |   null                         |
  |   null            ★ 안 없어졌다 |         |                                |
  | 호출자가 매번 감싸야 한다       |         | 그냥 넘긴다                    |
  +--------------------------------+         +--------------------------------+
     상태가 3 으로 늘었다                        상태가 2 그대로다
```

- ★ **`null` 을 없애려고 넣었는데 `null` 은 그대로 있고 상태만 하나 늘었다.**
- 게다가 **호출부가 오염된다** — 모든 호출자가 `Optional.of(...)` / `Optional.empty()` 를 써야 한다.

**선택 인자가 필요하면**

| 방법 | 언제 |
|---|---|
| **오버로드** | 선택 인자가 한둘 — `greet(String nick)` 과 `greet()` |
| **파라미터 객체 / 빌더** | 선택 인자가 많다 |
| `@Nullable` 애너테이션 + 문서 | 넘기는 쪽에 `null` 허용을 알린다(런타임 강제는 없다 — [**60번 주제**](../60-null-handling/)) |

### 7. `Map<String, Optional<String>>` 의 상태는 몇 가지인가

**출력** (`Ex.java (38-b)`, JDK 21.0.5 — 17·25 동일)

```text
--- 3. 컬렉션 원소로 쓰면 — 상태가 셋이 된다 ---
map            : {a=Optional[값], b=Optional.empty}
m.get("b")     : Optional.empty   (키는 있는데 값이 비었다)
m.get("없는키") : null   (키 자체가 없다)
셋을 구분하려면 containsKey 까지 봐야 한다 : true / false
```

**두 `get` 의 결과**

- `m.get("b")` -> **`Optional.empty`**
- `m.get("없는키")` -> **`null`** ★ 봉투가 아니다

**상태는 셋이다**

```text
  1. 키가 없다              get -> null             ★ Optional 이 아니다
  2. 키가 있고 값이 비었다   get -> Optional.empty
  3. 키가 있고 값이 있다     get -> Optional[값]
```

**`Optional` 로 표현되는 것과 `null` 로 표현되는 것**

- **2·3 만 `Optional`** 이고, **1은 여전히 `null`** 이다.
- 즉 `Optional` 을 값에 씌워도 **`null` 검사는 사라지지 않는다.** 오히려 검사할 것이 하나 늘었다.
- `Map` 은 이미 "없음"을 표현할 수 있다 — `containsKey`·`getOrDefault`.\
  `Map` API 의 정본은 목록의 **41번 주제**.

```java
// 봉투를 씌우지 않는다
String v = m.getOrDefault(key, "기본값");
// 반환 자리에서만 봉투로 바꾼다
Optional<String> find(String key) { return Optional.ofNullable(m.get(key)); }
```

### 8. `map` 과 `flatMap` 은 어디서 갈리는가

**출력** (`Ex.java (38-b)`, JDK 21.0.5 — 17·25 동일)

```text
--- 6. Optional<Optional<T>> 은 map 이 만든다 ---
map(v -> Optional.of(..))     : Optional[Optional[2]]
flatMap(v -> Optional.of(..)) : Optional[2]
```

**앞 두 줄**

| 식 | 결과 |
|---|---|
| `src.map(v -> Optional.of(v.length()))` | **`Optional[Optional[2]]`** — 봉투가 두 겹 |
| `src.flatMap(v -> Optional.of(v.length()))` | **`Optional[2]`** |

**`email` 이 `null` 일 때**

```text
--- 2. 사슬로 잇기 — 아이디에서 이메일 도메인까지 ---
  u1           -> x.com
  u2           -> (알 수 없음)
  없는아이디        -> (알 수 없음)
  u3           -> x.com
```

- `Optional.of(user).map(User::email)` 은 **`Optional.empty`** 가 된다.
- ★ 소스가 그렇게 되어 있다 — 함수의 결과를 `ofNullable` 로 감싼다.

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

- 그래서 `u2`(사용자는 있는데 이메일이 `null`)와 "없는아이디"(사용자가 없음)가 **같은 답으로 합류**한다.
- `null` 을 돌려주는 옛 API 를 `map` 으로 이어도 봉투가 깨지지 않는 이유가 이것이다.

**둘을 고르는 기준**

> **함수가 `Optional` 을 돌려주면 `flatMap`, 평범한 값을 돌려주면 `map`.**

- 스트림의 `map`/`flatMap` 과 **정확히 같은 구분**이다([`../45-intermediate-operations/`](../45-intermediate-operations/)).
- `Optional<Optional<T>>` 가 보이면 **`map` 을 쓸 자리에 `flatMap` 을 안 쓴 것**이다.

### 9. 스트림에서 `Optional` 을 펼치는 두 방법

**출력** (`Ex.java (38-c)`, JDK 21.0.5 — 17·25 동일)

```text
--- 1. 스트림에서 Optional 을 펼치는 두 방법 ---
filter(isPresent).map(get) : [User[id=u1, email=a@x.com], User[id=u2, email=null], User[id=u3, email=c@x.com]]
flatMap(Optional::stream)  : [User[id=u1, email=a@x.com], User[id=u2, email=null], User[id=u3, email=c@x.com]]
두 결과가 같은가            : true
```

**두 결과는 같다.**

**몇 버전부터**

- `Optional.stream()` 은 **Java 9**(`@since 9`, src.zip 확인).
- `--release 8` 로 컴파일하면 `cannot find symbol ... method stream()` 이 난다(10번).

**뒤의 것이 나은 이유**

```text
  filter(Optional::isPresent).map(Optional::get)     flatMap(Optional::stream)
  +--------------------------------------+           +--------------------------------+
  | 두 단계                              |           | 한 단계                        |
  | get() 이 코드에 남는다 ★             |           | get() 이 없다                  |
  | 순서를 바꾸면 터진다                 |           | 바꿀 것이 없다                 |
  +--------------------------------------+           +--------------------------------+
```

- ★ **`get()` 이 코드에서 사라진다.** `filter` 와 `map` 의 순서 의존이 없어져 리팩토링에 안전하다.
- `Optional.stream()` 은 **0개 또는 1개짜리 스트림**이므로 `flatMap` 이 자연스럽게 빈 것을 걸러 낸다.

**최종 연산이 돌려주는 `Optional` 들**

```text
--- 3. 최종 연산이 돌려주는 Optional ---
findFirst()                : Optional[1]
빈 스트림의 findFirst()     : Optional.empty
max(naturalOrder())        : Optional[3]
reduce(Integer::sum)       : Optional[6]
IntStream.average()        : OptionalDouble[2.0]
빈 IntStream 의 average()   : OptionalDouble.empty
```

| 최종 연산 | 객체 스트림 | 기본형 스트림 |
|---|---|---|
| `findFirst`/`findAny` | `Optional<T>` | `OptionalInt`/`OptionalLong`/`OptionalDouble` |
| `min`/`max` | `Optional<T>` | 〃 |
| 인자 없는 `reduce` | `Optional<T>` | 〃 |
| `average` | 없다 | **`OptionalDouble`** |

- 기본형 쪽은 **박싱을 피하려고 만든 별도 클래스**라 `map`·`flatMap`·`filter` 가 없다.
- 왜 이 자리들이 `Optional` 인지는 [`../46-terminal-operations/`](../46-terminal-operations/) 가 정본이다.

### 10. 메서드마다 버전이 어떻게 갈리는가

**`src.zip` 의 `@since`**

| 메서드 | `@since` |
|---|---|
| `ifPresentOrElse` | **9** |
| `or` | **9** |
| `stream` | **9** |
| `orElseThrow()` (인자 없음) | **10** |
| `isEmpty` | **11** |

**도구로 확인하는 방법 둘**

1. **`src.zip` 을 풀어 `@since` 를 읽는다.**

```text
unzip -o ~/.sdkman/candidates/java/21.0.5-tem/lib/src.zip 'java.base/java/util/Optional.java'
grep -n '@since' java.base/java/util/Optional.java
```

2. **`javac --release N` 으로 컴파일해 본다.** 되는 최저 버전이 답이다.

**출력** (`Ex.java (38-e)`, JDK 21.0.5 의 javac)

```text
$ javac --release 8 Ex.java
Ex.java:5: error: cannot find symbol
        o.ifPresentOrElse(v -> {}, () -> {});   // 9
         ^
  symbol:   method ifPresentOrElse((v)->{ },()->{ })
  location: variable o of type Optional<String>
Ex.java:6: error: cannot find symbol
        o.or(() -> Optional.of("y"));           // 9
         ^
  symbol:   method or(()->Option[...]("y"))
  location: variable o of type Optional<String>
Ex.java:7: error: cannot find symbol
        o.stream().count();                     // 9
         ^
  symbol:   method stream()
  location: variable o of type Optional<String>
Ex.java:8: error: method orElseThrow in class Optional<T> cannot be applied to given types;
        o.orElseThrow();                        // 10
         ^
  required: Supplier<? extends X>
  found:    no arguments
  reason: cannot infer type-variable(s) X
    (actual and formal argument lists differ in length)
  where X,T are type-variables:
    X extends Throwable declared in method <X>orElseThrow(Supplier<? extends X>)
    T extends Object declared in class Optional
Ex.java:9: error: cannot find symbol
        System.out.println(o.isEmpty());        // 11
                            ^
  symbol:   method isEmpty()
  location: variable o of type Optional<String>
5 errors
```

`--release` 를 올리면 하나씩 사라진다.

| `--release` | 남는 에러 |
|---|---|
| 8 | 5건 (전부) |
| 9 | 2건 — `orElseThrow()`, `isEmpty` |
| 10 | 1건 — `isEmpty` |
| 11 | **없음** |

**`orElseThrow()` 만 에러 모양이 다른 이유**

- ★ **8에도 `orElseThrow(Supplier)` 가 이미 있었기 때문**이다.
- 그래서 javac 이 **"그런 이름이 없다"(`cannot find symbol`)가 아니라 "그 인자로는 못 부른다"(`cannot be applied to given types`)** 라고 말한다.
- 나머지 넷은 **이름 자체가 없던 것**이라 `cannot find symbol` 이다.
- 즉 **새 메서드가 추가된 것과 오버로드가 추가된 것이 에러 문구로 구분된다.**

### 11. `Optional` 변수 자체가 `null` 이면

**출력** (`Ex.java (38-b)`, JDK 21.0.5 — 17·25 동일)

```text
--- 5. Optional 자체가 null 일 수 있다 ---
null 인 Optional 에 isPresent() -> java.lang.NullPointerException: Cannot invoke "java.util.Optional.isPresent()" because "nullOpt" is null
```

- **그냥 `NullPointerException`** 이다. `Optional` 이라고 특별할 것이 하나도 없다.

**javadoc 은 무엇이라고 적었나**

> A variable whose type is `Optional` should
> never itself be `null`; it should always point to an `Optional`
> instance.

- **"should never"** — 요구다. 그리고 ★ **강제되지 않는다.**
- `Optional<String> o = null;` 은 컴파일 경고조차 없다.

```text
   Optional 이 막아 주는 것               Optional 이 안 막아 주는 것
  +-----------------------------+        +-----------------------------------+
  | 반환값이 "없을 수 있다" 를   |        | 봉투 변수 자체가 null 인 것       |
  | 시그니처로 알린다            |        | get() 을 그냥 부르는 것           |
  |                             |        | 필드·파라미터에 쓰는 것           |
  +-----------------------------+        +-----------------------------------+
        이것 하나뿐이다                      전부 사람이 지켜야 한다
```

**지켜야 할 규율**

> **`Optional` 을 돌려주는 메서드는 절대 `null` 을 돌려주지 않는다.** 값이 없으면 `Optional.empty()` 다.

- 이 규율 하나가 지켜져야 호출자가 **`isPresent()` 를 안전하게 부를 수 있다.**
- 규율을 강제하고 싶으면 반환 직전에 `Objects.requireNonNull(result)` 를 건다([**60번 주제**](../60-null-handling/)).

### 12. 어디에 쓰고 어디에 안 쓰나

**반환 타입으로 맞는 경우 vs 예외를 던져야 하는 경우**

```text
   "없음" 이 정상인가?
          |
    +-----+-----+
    |           |
   그렇다      아니다
    |           |
    v           v
  Optional    예외를 던진다
    |           |
  findById    loadRequiredConfig
  findByEmail requireAdminRole
  최고가 조회  결제 승인
```

- javadoc 의 조건은 **"a clear need to represent 'no result'"** — **결과 없음이 정상인 경우**다.
- 필수 설정이 없다, 권한이 없다, 계약 위반이다 — 전부 **예외**다.\
  봉투로 감싸면 호출자가 `orElse(기본값)` 로 **조용히 넘겨 버린다.**
- 예외와 값의 경계는 [`../25-exceptions/`](../25-exceptions/) 가 정본이다.

**`if (opt.isPresent()) opt.get()` 이 얻은 것이 없는 이유**

**출력** (`Ex.java (38-b)`)

```text
--- 4. isPresent() + get() 대 map/orElse ---
isPresent+get : HELLO
map+orElse    : HELLO
```

```java
String bad;
if (o.isPresent()) bad = o.get().toUpperCase(); else bad = "없음";   // if (x != null) 과 같다
String good = o.map(String::toUpperCase).orElse("없음");              // 한 식
```

- **결과가 같다.** 다른 것은 **`get()` 이 코드에 남는가**다.
- `isPresent()` + `get()` 은 `null` 검사를 **더 길게 쓴 것**이고, `Optional` 의 조합 메서드를 하나도 안 쓴 것이다.
- 부수효과만 필요하면 `ifPresent`/`ifPresentOrElse` 를 쓴다.

**`synchronized (opt)` 와 `opt == Optional.empty()`**

`Optional` 은 **값 기반 클래스**다. 클래스 javadoc 원문:

> This is a value-based class; programmers should treat instances that are
> equal as interchangeable and should not use instances for synchronization,
> or unpredictable behavior may occur. For example, in a future release, synchronization may fail.

**출력** (`Ex.java (38-d)`, `javac -Xlint:all`)

```text
Ex.java:5: warning: [synchronization] attempt to synchronize on an instance of a value-based class
        synchronized (o) { System.out.println("동기화 블록 안 : " + o); }
        ^
1 warning
동기화 블록 안 : Optional[x]
```

- **경고가 나고 실행은 된다.** 지금은 되지만 javadoc 이 "may fail" 이라고 예고했다.
- `==` 비교도 같은 이유로 금지다. `empty()` 의 `@apiNote` 가 직접 막는다.

> avoid testing if an object is empty by comparing with `==` or `!=` against instances returned by
> `Optional.empty()`.  There is no guarantee that it is a singleton.

- 실측에서는 `Optional.<String>empty() == Optional.<String>empty()` 가 **`true`** 였지만 **보장이 아니다.**\
  `isEmpty()`/`isPresent()` 를 쓴다.

> **값 기반 클래스(value-based class)** — 동등한 인스턴스를 서로 바꿔 써도 되는 클래스. 정체성(identity)에 의존하면 안 된다.\
> 예: `Optional`·`LocalDate`. 동기화·`==` 비교를 하면 안 된다.

### 13. 다른 주제와 잇기

**`Optional` 이 `null` 을 없애 주는가**

- ★ **아니다.** 실측으로 셋을 보였다.
  - 봉투 변수 자체가 `null` 일 수 있다(11번).
  - `Map` 값에 씌워도 `get("없는키")` 는 여전히 `null` 이다(7번).
  - 파라미터로 쓰면 `null` 이 그대로 남고 상태만 는다(6번).
- `Optional` 이 하는 일은 **"없을 수 있음"을 시그니처에 적는 것** 하나뿐이다.
- `null` 을 실제로 막는 장치는 다른 것이다.

| 장치 | 하는 일 |
|---|---|
| `Objects.requireNonNull(x, "msg")` | 그 자리에서 즉시 실패시킨다 |
| 생성자·컴팩트 생성자 검증 | 잘못된 객체가 만들어지는 것을 막는다 |
| 경계에서 검증 | 밖에서 들어온 것을 안쪽으로 보내기 전에 거른다 |
| `Optional` 반환 | **없음을 타입으로 알린다**(막지는 않는다) |

- 넷을 어디에 배치할지는 [`../60-null-handling/`](../60-null-handling/) 가 정본이다.

**`Optional` 필드가 필요해 보일 때**

- 대개 **"상태가 둘 이상"** 이라는 뜻이다. 필드에 봉투를 씌우는 대신 **타입을 나눈다.**

```java
sealed interface Result permits Found, NotFound {}
record Found(User user) implements Result {}
record NotFound(String reason) implements Result {}
```

- `switch` 패턴 매칭으로 분기하면 **컴파일러가 빠진 경우를 잡아 준다.**
- [`../15-sealed-classes/`](../15-sealed-classes/)·[`../14-records/`](../14-records/).
- 더 단순한 경우라면 **필드는 `null` 허용, 접근자가 `Optional.ofNullable`** 로 충분하다(5번).

**`OptionalInt`/`OptionalDouble` 에 `map` 이 없는 이유**

- 이 타입들은 **박싱을 피하려고** 만들어졌다.
- `map(IntUnaryOperator)` 를 주면 괜찮지만, `map(Function<Integer, U>)` 를 주는 순간 **다시 박싱이 생긴다.**\
  그래서 변환 계열을 아예 안 넣었다.
- 변환이 필요하면 `IntStream.of(...).boxed()` 로 먼저 박싱하거나, `getAsInt()`·`orElse(0)` 로 꺼낸 뒤 처리한다.
- 기본형 스트림의 정본은 [`../44-stream-creation/`](../44-stream-creation/), 박싱은 [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/).

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java (38-a)` | 생성 셋·`of(null)` NPE·`orElse` 대 `orElseGet` 호출 횟수·`get`/`orElseThrow` 예외·`ifPresent(OrElse)`·`map`/`filter`/`or`/`stream`·`equals`/`hashCode` | 17 · 21 · 25 (출력 동일) |
| `Ex.java (38-b)` | 직렬화 실패·`Optional` 파라미터 셋·`Map` 값의 상태 셋·`isPresent`+`get`·봉투가 `null`·`map` 대 `flatMap` | 17 · 21 · 25 (출력 동일) |
| `Ex.java (38-b2)` `javac` | `Optional.of("x") instanceof Serializable` -> **컴파일 에러** | 21 |
| `Ex.java (38-c)` | 스트림에서 `Optional` 펼치기 두 방법·사슬 잇기·최종 연산의 `Optional`/`OptionalDouble`·`or` | 17 · 21 · 25 (출력 동일) |
| `Ex.java (38-d)` `javac -Xlint:all` | 값 기반 클래스에 `synchronized` -> 경고 + 실행은 됨 | 21 |
| `Ex.java (38-e)` `javac --release 8/9/10/11` | `ifPresentOrElse`·`or`·`stream` = 9, `orElseThrow()` = 10, `isEmpty` = 11 | 21 의 javac |
| `src.zip` 의 `Optional.java` | `@since` 원문, `of`·`get`·`map` 의 실제 소스, `@apiNote` 원문 | 21.0.5 |

**구현 의존 항목** — `toString` 형태(`Optional[값]`·`Optional.empty`), 예외 메시지(`No value present`),
`NotSerializableException` 의 문구, `Optional.empty() == Optional.empty()` 가 `true` 인 것,
`GoodUser` 직렬화 바이트 수(88), javac 의 에러·경고 문구 — 전부 **구현 세부**다. 17·21·25 에서 같았지만 **관찰이다.**\
반면 "반환 타입에 쓰라"·"`of(null)` 은 NPE"·"빈 봉투에 `get()` 은 `NoSuchElementException`"·
"`empty()` 가 싱글턴이라는 보장은 없다"·"`get()` 대신 `orElseThrow()` 를 쓰라"는 **javadoc 의 계약·권고**다.

★ **`orElse` 의 인자가 항상 평가되는 것은 JLS 의 인자 평가 규칙**이지 `Optional` 의 구현 세부가 아니다. 버전이 올라도 바뀌지 않는다.
