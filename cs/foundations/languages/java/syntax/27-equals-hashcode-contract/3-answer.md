# java/syntax/27 — `equals`/`hashCode`/`toString` 계약 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> javadoc 인용은 `lib/src.zip` 의 `java.base/java/lang/Object.java` 원문 그대로다.\
> 17.0.13 · 25.0.1 에서도 같은 프로그램을 돌려 확인했다(갈리는 것은 1번에 따로 적었다).
> 해시 테이블의 **원리**는 이 파일이 다루지 않는다 — [`data-structure/05-hashmap`](../../../../../data-structure/05-hashmap/) 이 정본이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `equals` 만 재정의한 클래스의 여섯 줄을 예측하라

**실행 결과** (`Lost.java`, JDK 21.0.5 — 17·25 동일)

```text
A) equals        : true
A) hashCode 같나 : false
A) get(a2)       : null
A) contains(a2)  : false
A) List.contains : true
A) HashSet size  : 2
B) hashCode 같나 : true  (994)
B) get(b2)       : 여기 있다
B) HashSet size  : 1
```

**여섯 줄**

| 호출 | 답 | 왜 |
|---|---|---|
| `a1.equals(a2)` | **`true`** | 내가 쓴 `equals` 가 x·y 를 비교한다 |
| `a1.hashCode() == a2.hashCode()` | **`false`** | `Object` 의 기본 구현이 남아 있다 — 객체마다 다른 값 |
| `map.get(a2)` | **`null`** | 칸을 다르게 고른다 |
| `List.of(a1).contains(a2)` | **`true`** | 리스트는 전부 훑으며 `equals` 만 쓴다 |
| `new HashSet<>(List.of(a1,a2)).size()` | **`2`** | 다른 칸에 들어가 중복 판정이 안 된다 |

**앞 두 줄과 마지막 줄이 갈리는 이유**

```text
Map / Set — 칸을 먼저 고른다              List — 칸이 없다

  hashCode() -> 칸 번호                     처음부터 끝까지
        |                                        |
        v                                        v
  그 칸만 본다  <-- ★ 여기서 갈린다          모든 원소와 equals
        |                                        |
        v                                        v
  그 칸 안에서만 equals                     하나라도 true 면 찾았다
```

- ★ **해시 컬렉션은 칸을 잘못 고르면 `equals` 를 부르지도 않는다.**\
  `equals` 를 아무리 정확히 써도 도달하지 못한다.
- `List` 는 칸이라는 개념이 없어 **`hashCode` 를 쓰지 않는다.**\
  그래서 계약 위반이 `List` 에서는 드러나지 않는다.
- 이 비대칭이 진단을 어렵게 만든다 — "리스트에서는 되는데 맵에서만 안 되네"가 이 버그의 전형적 증상이다.

**측정한 실제 값** (`Buckets2.java`, 칸 16개 기준)

```text
PA a1 hashCode=366712642  칸=9      <- put 은 여기에
PA a2 hashCode=640070680  칸=14     <- get 은 여기를 본다
PB b1 hashCode=994        칸=2
PB b2 hashCode=994        칸=2      <- 같은 칸
```

- `994` 는 결정적이다. `Objects.hash(1, 2)` 는 `31 * (31 * 1 + 1) + 2 = 994` 로 손계산과 맞는다.\
  근거는 JDK 소스다 — `Objects.hash` 는 `Arrays.hashCode(values)` 한 줄이고, 그 안이 `result = 31 * result + element.hashCode()` 이다.
- `366712642` 쪽은 **보장된 값이 아니다.** JDK 버전만 바꿔도 달라진다.

| JDK | 첫 객체 `hashCode` | 칸 |
|---|---|---|
| 17.0.13 | 622488023 | 13 |
| 21.0.5 | 366712642 | 9 |
| 25.0.1 | 498931366 | 11 |

> **identity hash code** — `Object.hashCode()` 의 기본 구현이 돌려주는 값. 객체를 구별하기 위한 것이고 값의 내용과 무관하다.\
> 예: 필드가 똑같은 두 객체라도 서로 다른 값이 나온다. 그래서 `equals` 를 재정의하면 반드시 같이 고쳐야 한다.

### 2. 계약의 조항을 세어 보라

**`equals` — 다섯 조항** (JDK 21.0.5 `Object.java` javadoc 원문)

> - It is *reflexive*: for any non-null reference value `x`, `x.equals(x)` should return `true`.
> - It is *symmetric*: ... `x.equals(y)` should return `true` if and only if `y.equals(x)` returns `true`.
> - It is *transitive*: if `x.equals(y)` returns `true` and `y.equals(z)` returns `true`, then `x.equals(z)` should return `true`.
> - It is *consistent*: multiple invocations of `x.equals(y)` consistently return `true` or consistently return `false`, **provided no information used in `equals` comparisons on the objects is modified**.
> - For any non-null reference value `x`, `x.equals(null)` should return `false`.

1. 반사성 · 2. 대칭성 · 3. 추이성 · 4. 일관성 · 5. `null` 은 항상 `false`

**`hashCode` — 세 조항** (같은 파일 javadoc 원문)

> - Whenever it is invoked on the same object more than once **during an execution** of a Java application, the `hashCode` method must consistently return the same integer, provided no information used in `equals` comparisons on the object is modified. **This integer need not remain consistent from one execution of an application to another execution of the same application.**
> - If two objects are equal according to the `equals(Object)` method, then calling the `hashCode` method on each of the two objects **must produce the same integer result**.
> - It is *not* required that if two objects are unequal ... must produce distinct integer results. However, ... producing distinct integer results for unequal objects may improve the performance of hash tables.

1. 같은 실행 안에서는 일관 (실행 간에는 보장 없음)
2. **`equals` 로 같으면 해시도 같다**
3. 다르다고 해시가 달라야 하는 것은 아니다

**두 계약을 잇는 조항의 방향**

```text
   equals 로 같다  ============>  hashCode 도 같다      (조항 2 — 강제)
                   <============
                      요구되지 않음
```

- **한 방향뿐**이다. 이 비대칭이 전부다.

**반대 방향이 요구되지 않는 이유**

- `hashCode` 는 `int` 다 — **2^32 가지**뿐이다.
- 표현 가능한 객체는 그보다 무한히 많다(`String` 하나만 해도 무한하다).
- **비둘기집 원리**로 충돌은 피할 수 없다 — 그래서 요구할 수가 없다.
- 충돌은 **정확성 문제가 아니라 성능 문제**다. 칸 안에서 `equals` 로 최종 확인하기 때문이다.

> **비둘기집 원리(pigeonhole principle)** — 넣을 것이 칸보다 많으면 한 칸에 둘 이상이 들어간다.\
> 예: 해시 값이 42억 가지인데 문자열은 그보다 많으니, 서로 다른 문자열인데 해시가 같은 쌍이 반드시 존재한다.

**`null` 조항이 따로 있는 이유**

- `null` 에는 `equals` 를 부를 수 없다 — `null.equals(x)` 는 NPE 다.
- 그래서 **대칭성으로는 `null` 을 다룰 수 없다.** 따로 못박아야 한다.
- 실무 함의: `equals` 안에서 `null` 검사를 따로 쓸 필요가 없다.\
  `o instanceof Point p` 는 `o` 가 `null` 이면 `false` 이므로 다섯째 조항이 공짜로 지켜진다.

### 3. 넣어 둔 키의 필드를 바꾸면

**실행 결과** (`Mutable.java`)

```text
넣은 직후 hashCode : 128
get(key)           : 값
바꾼 뒤 hashCode   : 129
get(key)           : null
get(new Tag("b")) : null
map 전체           : {Tag[b]=값}
map.size()         : 1
map.containsValue  : true
remove(key)        : null / size=1
```

**`hashCode` 는 각각 무엇인가**

- 바꾸기 전 `name="a"` -> **128**.\
  `Objects.hash("a")` = `31 * 1 + "a".hashCode()` = `31 + 97` = 128.
- 바꾼 뒤 `name="b"` -> **129**.\
  `31 + 98` = 129.
- 손계산과 실행이 일치한다.

**`map.get(key)`**

- **`null`.**

```text
put 할 때 (name="a")                      필드를 바꾼 뒤 (name="b")

  hash 128 -> 칸 0                          hash 129 -> 칸 1 을 본다
  +------+------+                          +------+------+
  | 칸 0 | 칸 1 |                          | 칸 0 | 칸 1 |
  | Tag  |      |                          | Tag  | 비었다|
  +------+------+                          +------+------+
                                             엔트리는 칸 0 에 그대로
                                             아무도 칸 0 을 안 본다
```

- 저장 위치는 **넣을 때의 해시로 결정**된다. 나중에 해시가 바뀌어도 **이사하지 않는다.**
- 자기 자신을 키로 줘도 못 찾는다 — **넣은 그 객체인데도** 못 찾는다.

**`map.get(new Tag("b"))`**

- **`null`.**
- 새 `Tag("b")` 는 해시 129 -> 칸 1 을 본다. 거기는 비어 있다.
- 엔트리는 칸 0 에 있고, 그 엔트리의 키를 지금 물어보면 `"b"` 라고 답하는데도 못 찾는다.

**`size()` 와 `toString()`**

- `size()` -> **`1`**
- `toString()` -> **`{Tag[b]=값}`**
- **엔트리가 멀쩡히 보인다.** 사라진 게 아니다.
- `containsValue("값")` 도 `true` 다 — 값 검색은 **전체 순회**라 칸을 안 고르기 때문이다.

**`remove(key)` 는 성공하는가**

- **실패한다.** `null` 을 돌려주고 `size` 는 1 그대로다.
- `remove` 도 칸을 먼저 고르기 때문이다.

**이 상태의 이름과 왜 누수인가**

- **도달 불가능하지만 살아 있는 엔트리**다.
- `get` 도 `remove` 도 못 하니 **지울 방법이 없다.**\
  맵 전체를 순회하며 `Iterator.remove` 로 지우는 것 말고는 수단이 없다.
- 맵이 살아 있는 한 키와 값이 GC 되지 않는다 — **메모리 누수**다.
- 캐시·세션 저장소처럼 오래 사는 맵에서 이것이 쌓이면 OOM 으로 간다.
- 방어: **키로 쓸 객체는 불변으로.** `equals`/`hashCode` 가 읽는 필드를 전부 `final` 로 만든다.
- 특히 조심할 것: **JPA 엔티티의 자동 생성 ID**.\
  `null` 인 채로 `Set` 에 넣었다가 `flush` 후 ID 가 채워지면 해시가 바뀐다 — 정확히 이 함정이다.

### 4. `java.util.Date` 와 `java.sql.Timestamp`

**실행 결과** (`JdkSym.java`)

```text
d.equals(t) : true
t.equals(d) : false
d.hashCode()==t.hashCode() : true
[d].contains(t) : false
[t].contains(d) : true
HashSet{d,t}.size() : 2
```

**실행 결과** (`JdkSym2.java`)

```text
add(Date) -> add(Timestamp) : size 2
add(Timestamp) -> add(Date) : size 1
```

**`d.equals(t)` / `t.equals(d)`**

- `d.equals(t)` -> **`true`**
- `t.equals(d)` -> **`false`**
- **대칭성 위반**이다.

**`hashCode` 는 같은가**

- **`true`.** 같은 밀리초라 해시도 같다.
- 그래서 **둘은 같은 칸에 떨어진다** — 이번 사고는 칸 문제가 아니라 `equals` 문제다.

**`List.contains`**

- `[d].contains(t)` -> **`false`**
- `[t].contains(d)` -> **`true`**

```text
ArrayList.contains(o) 는 o.equals(원소) 를 부른다

  [d].contains(t)   ->  t.equals(d)  ->  false
  [t].contains(d)   ->  d.equals(t)  ->  true

  같은 두 객체인데 "누가 묻느냐"로 답이 뒤집힌다
```

**`HashSet` 의 `size()`**

- `d` 먼저, `t` 나중 -> **`2`**
- `t` 먼저, `d` 나중 -> **`1`**

```text
  add(d) 먼저                             add(t) 먼저
  +----------------------------+          +----------------------------+
  | d 저장                      |          | t 저장                      |
  | add(t): 같은 칸을 본다        |          | add(d): 같은 칸을 본다        |
  |   t.equals(d) = false       |          |   d.equals(t) = true        |
  |   -> 새것으로 보고 추가       |          |   -> 이미 있다고 보고 무시    |
  | size = 2                    |          | size = 1                   |
  +----------------------------+          +----------------------------+
```

- **같은 두 객체, 같은 컬렉션, 넣는 순서만 다른데 크기가 다르다.**
- 이런 동작은 리스트 정렬·중복 제거 파이프라인에서 **입력 순서에 따라 결과가 달라지는** 버그로 나타난다.

**어느 조항이 깨졌으며, 원인 패턴은**

- **대칭성**(조항 2)이 깨졌다.
- 원인: 상위 타입이 **`instanceof` 로 비교**하면 하위 타입 인스턴스도 통과한다.\
  하위 타입은 자기 필드(`nanos`)까지 보므로 통과시키지 않는다.

```text
  Date.equals(Object o)                   Timestamp.equals(Object o)
    o 가 Date 계열이면 시각만 비교           o 가 Timestamp 여야 하고 nanos 까지 비교
         |                                        |
    Timestamp 도 Date 다 -> 통과              Date 는 Timestamp 가 아니다 -> 거부
```

**피하는 방법 두 가지**

1. **`getClass() != o.getClass()` 로 비교한다.**\
   대칭이 된다. 대신 하위 타입이 상위 타입과 **절대** 같아지지 않는다(리스코프 치환 원칙과 충돌한다는 비판이 있다).
2. **상속 대신 조합을 쓰고 클래스를 `final` 로 만든다.**\
   하위 타입이 존재할 수 없으니 문제가 생기지 않는다. `record` 가 이 길을 택한 것이다(7번).

- 세 번째 선택지: 값 타입 계층을 만들지 않는다.\
  "시각"이라는 값에 하위 타입을 두려는 설계 자체가 무리였다 — 그래서 `java.time` 은 계층 없이 별개 타입들로 갔다([**51번 주제**](../51-java-time-types/)).

### 5. 매개변수 타입을 잘못 쓰면

**실행 결과** (`Overload.java`)

```text
a.equals(b) 정적 타입 Id     : true
a.equals((Object) b)         : false
List.of(a).contains(b)       : false
new HashSet<>(List.of(a,b)).size() : 2
```

**`a.equals(b)`**

- **`true`.** 내가 쓴 `equals(Id)` 가 뽑혔다.

**`Object bo = b; a.equals(bo)`**

- **`false`.** `Object.equals(Object)` 가 뽑혀 참조 비교를 했다.

**두 답이 갈리는 이유**

```text
  클래스 Id 가 실제로 갖는 equals 는 둘이다

    Object.equals(Object)   <- 상속받은 것. 참조 비교
    Id.equals(Id)           <- 내가 쓴 것. 재정의가 아니라 새 메서드

  어느 쪽이 불리느냐는 인자의 정적 타입으로 컴파일 타임에 정해진다

    a.equals(b)          b 의 정적 타입 Id     -> equals(Id)      -> true
    a.equals((Object) b) 정적 타입 Object      -> equals(Object)  -> false
```

- **오버로딩 해소**는 컴파일 타임에 **정적 타입**으로 이뤄진다.\
  런타임 타입으로 고르는 동적 디스패치와 다르다.
- 즉 `Id` 에는 `equals` 가 **두 개** 공존하고, 부르는 자리마다 다른 것이 뽑힌다.

**컬렉션에서는 어느 쪽이 불리는가**

- **항상 `Object` 쪽**이다.
- `List.contains(Object o)`·`HashMap.get(Object key)` 의 시그니처가 `Object` 이므로, 그 안에서 `equals` 를 부를 때의 정적 타입도 `Object` 다.
- 그래서 **내가 쓴 `equals(Id)` 는 컬렉션에서 한 번도 안 불린다.**
- 가장 나쁜 점: **내 단위 테스트는 통과한다.** 테스트에서는 정적 타입이 `Id` 이기 때문이다.

**컴파일 에러로 바꾸는 방법**

- **`@Override` 를 붙인다.**

```text
$ javac OverrideCatch.java
OverrideCatch.java:4: error: method does not override or implement a method from a supertype
    @Override public boolean equals(Id2 other) { return other.v == v; }
    ^
1 error
```

- `@Override` 는 주석이 아니라 **컴파일러에게 시키는 검사**다.
- 이 한 글자로 "테스트는 통과하는데 운영에서만 틀리는" 버그가 **컴파일 에러**가 된다.
- 같은 이유로 `hashCode` 에도 붙인다 — `hashcode()` 오타를 잡아 준다.

> **오버로딩 해소(overload resolution)** — 이름이 같은 메서드 여럿 중 어느 것을 부를지 **인자의 정적 타입**으로 고르는 컴파일 타임 절차.\
> 예: `println(char)` 와 `println(int)` 중 무엇이 불릴지는 인자의 선언 타입으로 정해진다.\
> 규칙 자체는 [**08번 주제**](../08-method-declaration-overloading/)가 정본이다.

### 6. `toString` 은 무엇을 보장하는가

**기본 구현이 돌려주는 것**

javadoc 의 `implSpec` 원문이다.

> The `toString` method for class `Object` returns a string consisting of the name of the class of which the object is an instance, the at-sign character `@`, and the unsigned hexadecimal representation of the hash code of the object. In other words, this method returns a string equal to the value of:
> `getClass().getName() + '@' + Integer.toHexString(hashCode())`

**실행 결과** (`ToStr.java`)

```text
기본 toString 형태 : true
기본 toString 예   : Plain@776ec8df
```

- 첫 줄은 `p.toString()` 과 `p.getClass().getName() + "@" + Integer.toHexString(p.hashCode())` 를 **실제로 비교한 결과**다.\
  javadoc 의 서술이 그대로였다.

**javadoc 이 명시적으로 부정하는 보장**

> **The string output is not necessarily stable over time or across JVM invocations.**

- **시간이 지나도, JVM 을 다시 띄워도 같다는 보장이 없다.**
- 이것을 명시적으로 적어 뒀다는 것이 중요하다 — "우연히 안정적"인 것과 "보장된" 것은 다르다.

**`776ec8df` 는 무엇인가**

- **그 객체의 `hashCode()` 를 16진수로 적은 것**이다.
- `Plain` 은 `hashCode` 를 재정의하지 않았으므로 identity hash code 다.
- 그래서 **실행마다 달라질 수 있다** — 1번의 표에서 JDK 버전만 바꿔도 값이 갈렸다.

**파싱하거나 비교에 쓰면 안 되는 이유**

- 형식이 **계약이 아니다.** 라이브러리 버전이 올라가면 바뀔 수 있다.
- 기본 구현이라면 값 자체가 **실행마다 다르다.**
- `record` 의 `Pt[x=1, y=2]` 형식도 편의이지 **파싱 대상이 아니다.**
- 직렬화가 필요하면 JSON 등 **형식이 계약인 수단**을 쓴다.

**계약인가 권고인가**

- **권고**다. javadoc 이 "It is *recommended* that all subclasses override this method" 라고 쓴다.
- 지키지 않아도 표준 라이브러리가 오동작하지 않는다 — 로그가 읽기 나빠질 뿐이다.
- `equals`/`hashCode` 와 결정적으로 다른 점이 이것이다.\
  그 둘은 어기면 **`HashMap` 이 틀린 답을 낸다.**

### 7. `record` 는 무엇을 해결하는가

**실행 결과** (`ToStr.java`)

```text
record toString  : Pt[x=1, y=2]
record equals    : true
record hashCode  : 33 / 33
```

**자동으로 만드는 메서드**

- `equals(Object)` — 모든 컴포넌트를 비교
- `hashCode()` — 모든 컴포넌트를 조합
- `toString()` — `타입이름[컴포넌트=값, ...]`
- 그 밖에 컴포넌트 접근자(`x()`·`y()`)와 정규 생성자.

**`toString` 의 형태**

- **`Pt[x=1, y=2]`**
- 타입 이름 + 대괄호 + `이름=값` 을 쉼표로.

**`instanceof` 를 쓰는데 왜 대칭성 문제가 없는가**

```text
일반 클래스                                record

  class Money { ... }                       record Money(int amount) {}
       ^                                         ^
       |  extends                                |  (불가능)
  class TaggedMoney extends Money           record 는 암묵적으로 final
       |                                    하위 타입이 존재할 수 없다
  비대칭이 생길 수 있다                       -> 비대칭이 생길 자리가 없다
```

- **`record` 는 암묵적으로 `final`** 이다. 상속할 수 없다.
- 4번의 사고(상위 타입이 하위 타입을 통과시킴)는 **하위 타입이 있어야** 일어난다.
- 그래서 `record` 는 `instanceof` 를 써도 안전하다 — **문제를 푼 게 아니라 문제가 생길 조건을 없앤 것**이다.

**컴포넌트를 하나 추가했을 때**

```text
손으로 쓴 클래스                           record

  필드 추가                                 컴포넌트 추가
  equals 에 추가  <- 잊기 쉽다               (끝)
  hashCode 에 추가 <- 더 잊기 쉽다
  toString 에 추가 <- 가장 잊기 쉽다
       |                                        |
  셋 중 하나만 빠져도 조용히 틀린다            셋이 함께 다시 생성된다
```

- 손으로 쓸 때의 **가장 흔한 사고**가 원천적으로 막힌다.
- IDE 로 재생성하면 되지만, **재생성을 잊는 것**이 바로 그 사고다.
- `record` 로 못 바꾸는 경우(상속이 필요·가변이어야 함·필드를 일부만 비교)는 [**14번 주제**](../14-records/)가 정본이다.

### 8. 어디까지가 이 주제이고 어디부터가 다른 주제인가

**버킷·충돌 처리의 정본**

- [`data-structure/05-hashmap`](../../../../../data-structure/05-hashmap/) — 체이닝, 리사이즈, 로드 팩터.
- [`data-structure/29-open-addressing`](../../../../../data-structure/29-open-addressing/) — 개방 주소법.
- 이 주제는 그 위에서 **"계약을 어기면 어디가 틀리나"**만 다룬다.\
  이 문서에 나온 `hash(key)` 소스와 칸 번호도 **증상을 그리기 위한 최소한**이고, 왜 그렇게 섞는지는 거기서 본다.

**`TreeMap`/`TreeSet` 은 무엇으로 같음을 판정하는가**

**실행 결과** (`TreeVsHash.java` — `compareTo` 는 `major` 만 보고 `equals` 는 둘 다 보는 클래스)

```text
두 원소            : [1.0, 1.5]
equals 로 같나     : false
compareTo 가 0 인가: true
HashSet size       : 2 [1.0, 1.5]
TreeSet size       : 1 [1.0]
```

- **`TreeSet`/`TreeMap` 은 `compareTo`(또는 `Comparator`)의 결과가 `0` 인지로 판정**한다.\
  `equals` 를 부르지 않는다.
- 그래서 `equals` 와 `compareTo` 가 어긋나면 **같은 두 객체가 `HashSet` 에서는 둘, `TreeSet` 에서는 하나**가 된다.
- `1.5` 가 **조용히 사라졌다.** 예외도 경고도 없다.
- `SortedSet` javadoc 이 이 상황을 "consistent with equals" 라는 용어로 다룬다.\
  자세한 것은 [**28번 주제**](../28-comparable-comparator/)(`Comparable`/`Comparator`).

**`hashCode` 를 `return 1;` 로 쓰면**

**실행 결과** (`ConstHash.java`)

```text
계약은 지켜지나 (같으면 해시 같다): true
중복이 걸러지나 : size = 5
찾아지나        : true
```

- **계약을 어기지 않는다.** 조항 2("같으면 해시도 같다")를 만족하고, 조항 3은 "달라야 한다"를 요구하지 않는다.
- **정확성은 그대로다** — 중복도 걸러지고 조회도 된다.
- 나빠지는 것은 **성능**뿐이다.

```text
좋은 해시                                   return 1

  +----+----+----+----+                      +------------------+----+----+
  | A  | B  | C  | D  |                      | A -> B -> C -> D |    |    |
  +----+----+----+----+                      +------------------+----+----+
   조회 = 칸 하나 보기 -> 평균 O(1)            조회 = 사슬 전체 훑기 -> O(n)
```

- 원소 n 개가 한 칸에 몰려 사슬(또는 트리)이 되고, 조회가 **O(n)**(트리화되면 O(log n))이 된다.
- **정확성은 살고 성능만 죽는** 위반이다 — 계약 위반과 성질이 다르다.\
  1번의 사고는 답이 틀리고, 이것은 느려질 뿐이다.

**서비스 클래스·컨트롤러에 재정의해야 하는가**

- **아니다.** 재정의하지 않는 것이 맞다.
- 그런 객체는 **값이 아니라 정체성**으로 구별된다 — 같은 설정의 서비스 두 개는 "같은" 것이 아니라 "둘"이다.
- `Object` 의 기본 구현(참조 비교 + identity hash)이 정확히 그 의미다.
- 재정의하지 않으면 **계약은 자동으로 지켜진다.**\
  `Object` 의 두 메서드는 이미 일관되게 짝이 맞아 있다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Lost` | `equals` 만 재정의 -> `Map`/`Set` 실패, `List` 는 성공 | 17 · 21 · 25 (동일) |
| `Buckets2` | 실제 `hashCode` 와 칸 번호. JDK 버전별로 identity hash 가 다름 | 17 · 21 · 25 (**값 다름**) |
| `Mutable` | 가변 키 — 도달 불가 엔트리, `size`/`toString` 에는 보임 | 17 · 21 · 25 (동일) |
| `JdkSym` / `JdkSym2` | `Date`/`Timestamp` 대칭성 위반, 넣는 순서가 `size` 를 바꿈 | 17 · 21 · 25 (동일) |
| `Overload` | `equals(Id)` 오버로딩 — 정적 타입에 따라 다른 답 | 17 · 21 · 25 (동일) |
| `OverrideCatch` `javac` | `@Override` 가 오버로딩을 컴파일 에러로 잡음 | 21 |
| `ToStr` | 기본 `toString` 형태, `record` 의 세 메서드 | 17 · 21 · 25 (`Plain@...` 의 16진수만 다름: 17 `1f32e575` / 21 `776ec8df` / 25 `5c647e05`) |
| `TreeVsHash` | `equals` 와 `compareTo` 불일치 -> `TreeSet` 에서 원소가 사라짐 | 21 |
| `ConstHash` | `return 1` — 계약은 지켜지고 성능만 나빠짐 | 21 |
| `src.zip` 열람 | `Object` 의 세 javadoc, `HashMap.hash`, `Objects.hash`, `Arrays.hashCode` | 21 |
