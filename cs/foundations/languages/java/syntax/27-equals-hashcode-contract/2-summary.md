# java/syntax/27 — `equals`/`hashCode`/`toString` 계약 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — JDK 21.0.5 표준 라이브러리 소스 `java.base/java/lang/Object.java` 의 `equals`·`hashCode`·`toString` **javadoc 원문**(`lib/src.zip` 에서 직접 인용) · `java.base/java/util/HashMap.java`
> **실행 검증** — 이 문서의 모든 출력은 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 같은 프로그램을 **17.0.13 · 25.0.1** 에서도 돌려 **출력이 한 글자도 다르지 않음**을 확인했다.
> **버전** — 세 메서드의 계약은 Java 1.0 이래 바뀌지 않았다. `record` 의 자동 구현은 **Java 16**부터.
> **범위** — 해시 테이블이 **어떻게 동작하는가**(버킷·충돌·리사이즈·트리화)는 이 문서가 다루지 않는다.\
> 그쪽은 [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) 과 [`29-open-addressing/`](../../../../../data-structure/29-open-addressing/) 이 정본이다.\
> 여기는 **「계약을 어기면 어디서 조용히 틀리나」**만 다룬다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**`hashCode` 는 우편번호, `equals` 는 정확한 주소 대조다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 우편번호 | `hashCode()` 가 돌려주는 정수 |
| 배달 구역(동네) | 버킷 — 그 해시가 떨어지는 칸 |
| 구역에 가서 문패를 하나씩 대조 | 그 칸 안에서 `equals` 로 확인 |
| 창고를 통째로 뒤지기 | 전체 순회 — `toString`·`size`·`containsValue`·`List.contains` |

- 우체부는 **우편번호로 동네를 먼저 고른다.**\
  그래야 온 도시를 뒤지지 않는다.
- 동네에 도착하면 **문패를 대조**해서 진짜 그 집인지 확인한다.\
  같은 동네에 다른 집도 많기 때문이다.
- 그래서 규칙은 **한 방향으로만** 성립한다.\
  **같은 집이면 우편번호도 반드시 같아야** 하지만, 우편번호가 같다고 같은 집은 아니다.
- 이 규칙을 어기면 어떻게 되나?\
  **같은 집인데 우편번호를 다르게 적는 것**이다 — 편지는 엉뚱한 동네로 가고, 그 동네에는 그 집이 없으니 **"수취인 없음"** 이 된다.
- 끔찍한 점: **편지가 사라진 게 아니다.** 창고에는 그대로 있다.\
  창고를 통째로 뒤지면(`toString`) 보인다. 주소로 찾을 때만 없다.

아래 숫자는 전부 **JDK 21.0.5 에서 실제로 찍어 본 값**이다(`Buckets2.java`, 칸 16개 기준).

```text
계약을 지킨 경우 (PB)                       hashCode 를 재정의 안 한 경우 (PA)

 put(PB(1,2))                               put(PA(1,2))
   hashCode = 994    -> 칸 2 에 저장           hashCode = 366712642 -> 칸 9 에 저장
                                               (객체 정체성 기반)
 get(PB(1,2))                               get(PA(1,2))  <- equals 로는 같은 값
   hashCode = 994    -> 칸 2 를 본다            hashCode = 640070680 -> 칸 14 를 본다
   equals 로 대조 -> 찾았다                      칸 14 는 비었다 -> null
                                               칸 9 는 쳐다보지도 않는다
```

**똑같은 구조로** Java 가 이렇게 동작한다: 우편번호 = `hashCode()`, 동네 = 버킷, 문패 대조 = `equals`.

실무에서 이게 터지는 자리는 **DTO·VO 를 `Set` 에 넣거나 `Map` 의 키로 쓰는 코드**다.\
`equals` 만 IDE 로 생성했거나, 필드를 하나 추가하면서 `equals` 만 고치면 그날부터 조용히 틀린다.

> **계약(contract)** — 언어가 컴파일로 강제하지 못하지만 **지키지 않으면 표준 라이브러리가 오동작하는 약속**.\
> 예: `equals` 를 재정의하면서 `hashCode` 를 안 고쳐도 컴파일은 되지만, 그 객체를 `HashSet` 에 넣으면 중복이 걸러지지 않는다.

> **버킷(bucket)** — 해시 테이블이 원소를 나눠 담는 칸.\
> 예: 칸이 16개면 해시를 16으로 나눈 나머지 근처의 값이 칸 번호가 된다. 상세는 `data-structure/05-hashmap`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. javadoc 이 요구하는 **조항이 정확히 몇 개**이고 각각 무엇인가.
2. 조항 하나를 어기면 **어느 API 가 어떻게 틀리는가** — 그리고 어느 API 는 멀쩡한가.
3. 왜 그 틀림이 **예외가 아니라 조용한 오답**으로 나타나는가.

## 동작 방식

### (1) `equals` 계약 — 다섯 조항

**언제 쓰나** — `equals` 를 손으로 쓰거나 리뷰할 때.

JDK 21.0.5 `java.base/java/lang/Object.java` 의 javadoc 원문이다. 다섯 개다.

> The `equals` method implements an equivalence relation on non-null object references:
> - It is *reflexive*: for any non-null reference value `x`, `x.equals(x)` should return `true`.
> - It is *symmetric*: for any non-null reference values `x` and `y`, `x.equals(y)` should return `true` if and only if `y.equals(x)` returns `true`.
> - It is *transitive*: for any non-null reference values `x`, `y`, and `z`, if `x.equals(y)` returns `true` and `y.equals(z)` returns `true`, then `x.equals(z)` should return `true`.
> - It is *consistent*: for any non-null reference values `x` and `y`, multiple invocations of `x.equals(y)` consistently return `true` or consistently return `false`, provided no information used in `equals` comparisons on the objects is modified.
> - For any non-null reference value `x`, `x.equals(null)` should return `false`.

```text
  반사성   x.equals(x)                          -> true
  대칭성   x.equals(y) <=> y.equals(x)          -> 한쪽만 true 면 위반
  추이성   x=y 이고 y=z 이면                     -> x=z 여야 한다
  일관성   비교에 쓰는 값이 안 바뀌면              -> 몇 번 불러도 같은 답
  null     x.equals(null)                       -> 항상 false
```

그림 해설 (한 단계씩):

- 앞의 셋(반사·대칭·추이)은 **동치 관계**의 정의다.\
  이걸 만족해야 "같음"이 객체들을 **겹치지 않는 묶음으로 쪼갤** 수 있다.
- 일관성 조항에는 **조건이 달려 있다** — "비교에 쓰는 정보가 바뀌지 않는 한".\
  가변 키가 위험한 이유가 여기 있다(「어디서 틀리나」 2번).
- `null` 조항이 따로 있는 이유: `null` 은 `equals` 를 못 부르니 **대칭성으로는 표현이 안 된다.**

비용 — 없음. 판단 규칙이다.

> **동치 관계(equivalence relation)** — 반사·대칭·추이를 만족하는 "같음" 관계.\
> 예: 사람을 생일로 묶으면 동치 관계다(같은 날 태어난 사람들끼리 묶음이 되고 묶음끼리 안 겹친다). "키가 5cm 이내로 비슷하다"는 추이성이 깨져 동치 관계가 아니다.

### (2) `hashCode` 계약 — 세 조항

**언제 쓰나** — `equals` 를 건드린 직후 언제나.

같은 파일의 javadoc 원문이다.

> The general contract of `hashCode` is:
> - Whenever it is invoked on the same object more than once during an execution of a Java application, the `hashCode` method must consistently return the same integer, provided no information used in `equals` comparisons on the object is modified. This integer need not remain consistent from one execution of an application to another execution of the same application.
> - If two objects are equal according to the `equals(Object)` method, then calling the `hashCode` method on each of the two objects must produce the same integer result.
> - It is *not* required that if two objects are unequal according to the `equals(Object)` method, then calling the `hashCode` method on each of the two objects must produce distinct integer results. However, the programmer should be aware that producing distinct integer results for unequal objects may improve the performance of hash tables.

```text
      equals 로 같다  ==================>  hashCode 도 같아야 한다   (강제)
                      <==================
                        이 방향은 아님       (같은 해시여도 다른 객체일 수 있다)
```

그림 해설 (한 단계씩):

- **한 방향만 강제**된다. 이 비대칭이 이 주제의 핵심이다.
- 첫 조항의 "같은 실행 안에서"에 주의 — **실행이 바뀌면 값이 달라도 된다.**\
  그래서 `hashCode` 를 파일이나 DB 에 저장하면 안 된다.
- 셋째 조항은 **충돌을 허용**한다. 충돌은 성능 문제이지 정확성 문제가 아니다.

비용 — 계약을 지키면 조회 평균 O(1).\
셋째 조항을 극단적으로 쓰면(`return 1;`) 계약은 지키지만 모든 원소가 한 칸에 몰려 O(n)이 된다.

### (3) 두 메서드가 실제로 불리는 순서

**언제 쓰나** — "왜 못 찾는가"를 추적할 때.

```java
// JDK 21.0.5  java.base/java/util/HashMap.java  336~339행 — 실제 소스 그대로
static final int hash(Object key) {
    int h;
    return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
}
```

```text
map.get(key) 한 번에 일어나는 일

   key.hashCode()                    <- (1) 내 클래스의 메서드가 불린다
        |
        v
   섞기(spread) + 칸 번호 계산        <- (2) HashMap 의 몫. 원리는 data-structure/05-hashmap
        |
        v
   그 칸만 본다                       <- (3) 다른 칸은 쳐다보지 않는다  ★
        |
        v
   칸 안의 후보들과 equals            <- (4) 내 클래스의 메서드가 다시 불린다
        |
        v
   찾았다 / 못 찾았다(null)
```

그림 해설 (한 단계씩):

- (1)과 (4)만 **내가 쓴 코드**다. (2)(3)은 표준 라이브러리의 몫이다.
- ★ **(3)이 이 주제의 모든 함정을 만든다.**\
  칸을 잘못 고르면 **그 안에 값이 있어도 영원히 못 찾는다.** `equals` 는 불리지도 않는다.
- `hashCode` 가 틀리면 (4)에 도달조차 못 한다 — 그래서 `equals` 를 아무리 잘 써도 소용이 없다.

비용 — 계약을 지키면 `hashCode` 1회 + `equals` 몇 회.\
계약을 어기면 비용이 아니라 **답이 틀린다.**

### (4) `toString` — 계약이 아니라 권고다

**언제 쓰나** — 로그·디버거에 객체가 찍힐 때.

같은 파일의 javadoc 원문이다.

> In general, the `toString` method returns a string that "textually represents" this object. The result should be a concise but informative representation that is easy for a person to read. It is recommended that all subclasses override this method. **The string output is not necessarily stable over time or across JVM invocations.**

그리고 `Object` 의 기본 구현은 이렇게 명시돼 있다.

> returns a string equal to the value of: `getClass().getName() + '@' + Integer.toHexString(hashCode())`

**실행 결과** (`ToStr.java`)

```text
기본 toString 형태 : true
기본 toString 예   : Plain@776ec8df
```

- 첫 줄은 `p.toString()` 과 `getClass().getName() + "@" + Integer.toHexString(p.hashCode())` 를 **실제로 비교한 결과**다.\
  javadoc 의 `implSpec` 그대로였다.
- `776ec8df` 는 **실행마다 달라진다.** 기본 `hashCode` 가 객체마다 다른 값을 주기 때문이다.
- 그래서 `toString` 은 **동작의 근거로 쓰면 안 된다.**\
  파싱하거나, 비교하거나, 저장하지 않는다. 사람이 읽는 용도다.

비용 — 없음. 다만 `toString` 에서 무거운 일(지연 로딩 컬렉션 순회 등)을 하면 **디버거가 멈춘다.**

## 문법 — 형태와 규칙

직접 쓴 최소 예제다.

### 셋을 함께 재정의하는 표준 형태

```java
final class Point {
    private final int x, y;
    Point(int x, int y) { this.x = x; this.y = y; }

    @Override public boolean equals(Object o) {          // 매개변수는 반드시 Object
        return o instanceof Point p && p.x == x && p.y == y;
    }
    @Override public int hashCode() { return Objects.hash(x, y); }
    @Override public String toString() { return "Point[x=" + x + ", y=" + y + "]"; }
}
```

지켜야 할 것 네 가지.

- **매개변수는 `Object`** 다. `equals(Point)` 는 재정의가 아니라 오버로딩이다(「어디서 틀리나」 4번).
- **`@Override` 를 반드시 붙인다.** 그 오버로딩 사고를 컴파일 에러로 바꿔 준다.
- **`equals` 와 `hashCode` 는 같은 필드를 쓴다.** 하나만 고치면 그날 계약이 깨진다.
- **비교에 쓰는 필드는 `final`** 로. 가변이면 일관성 조항이 깨진다(「어디서 틀리나」 2번).

### `record` 는 셋을 자동으로 만들어 준다 (Java 16+)

```java
record Pt(int x, int y) {}
```

**실행 결과** (`ToStr.java`)

```text
record toString  : Pt[x=1, y=2]
record equals    : true
record hashCode  : 33 / 33
```

- 모든 컴포넌트를 쓰는 `equals`·`hashCode`·`toString` 이 자동 생성된다.
- 컴포넌트를 추가해도 **셋이 함께 갱신된다** — 손으로 쓸 때의 가장 흔한 사고가 원천적으로 막힌다.
- `record` 로 못 바꾸는 경우(상속이 필요하다, 가변이어야 한다)는 [**14번 주제**](../14-records/)가 정본이다.

### `Objects` 유틸

| 호출 | 하는 일 |
|---|---|
| `Objects.hash(a, b, c)` | 여러 필드를 합친 해시. 소스는 `return Arrays.hashCode(values);` 한 줄이고, 거기서 `result = 31 * result + element.hashCode()` 를 돌린다 |
| `Objects.hashCode(x)` | `x` 가 `null` 이면 `0`, 아니면 `x.hashCode()` |
| `Objects.equals(a, b)` | 양쪽 `null` 안전한 `equals` |
| `Objects.toString(x, "기본값")` | `null` 이면 기본값 |

`Objects.hash(1, 2)` 는 `994` 다 — `31 * (31 * 1 + 1) + 2 = 994`.\
실행으로도 `994` 가 나왔다(3-answer 1번). 손계산과 일치한다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 다섯 다 **예외가 아니라 조용한 오답**으로 나타난다.

### 1. `equals` 만 재정의하고 `hashCode` 를 안 한다

**실행 결과** (`Lost.java`)

```text
A) equals        : true          <- 같다고 한다
A) hashCode 같나 : false         <- 그런데 우편번호가 다르다
A) get(a2)       : null          <- 못 찾는다
A) contains(a2)  : false
A) List.contains : true          <- 리스트에서는 찾는다  ★
A) HashSet size  : 2             <- 중복이 안 걸러진다
B) hashCode 같나 : true  (994)
B) get(b2)       : 여기 있다
B) HashSet size  : 1
```

```text
같은 값인데 다른 우편번호가 찍힌다 (JDK 21.0.5 실측값, 칸 16개)

  put(PointA(1,2))                        get(PointA(1,2))
    hashCode = 366712642 -> 칸 9            hashCode = 640070680 -> 칸 14
          |                                       |
          v                                       v
    +-------+-------+-------+               +-------+-------+-------+
    | 칸 9  | 칸 14 |  ...  |               | 칸 9  | 칸 14 |  ...  |
    |PointA |       |       |               |PointA | 비었다 |       |
    +-------+-------+-------+               +-------+-------+-------+
                                              여기만 본다 -> null
                                              칸 9 는 쳐다보지도 않는다
                                              equals 는 불리지도 않는다
```

- ★ **`List.contains` 는 `true` 다.** 리스트는 **창고를 통째로 뒤지기** 때문이다.
- 그래서 같은 객체가 **`List` 에서는 찾아지고 `Map`/`Set` 에서만 사라진다.**\
  "equals 는 맞게 썼는데 왜?"라는 혼란이 여기서 온다.
- `994` 는 **결정적인 값**이다 — `Objects.hash(1, 2)` 의 결과이고 손계산으로도 나온다.
- 반면 `366712642`·`640070680` 은 **기본 `hashCode`** 라 보장된 값이 아니다.\
  실제로 같은 프로그램을 세 JDK 에서 돌리니 첫 객체의 값이 이렇게 갈렸다.

  | JDK | 첫 객체 `hashCode` | 칸 |
  |---|---|---|
  | 17.0.13 | 622488023 | 13 |
  | 21.0.5 | 366712642 | 9 |
  | 25.0.1 | 498931366 | 11 |

  javadoc 의 "This integer need not remain consistent from one execution of an application to another execution" 가 이 뜻이다.

### 2. 가변 필드를 키로 쓴다 — 넣은 뒤에 바꾼다

**실행 결과** (`Mutable.java`)

```text
넣은 직후 hashCode : 128
get(key)           : 값
바꾼 뒤 hashCode   : 129
get(key)           : null
get(new Tag("b")) : null
map 전체           : {Tag[b]=값}      <- 보인다!
map.size()         : 1                <- 있다!
map.containsValue  : true             <- 있다!
remove(key)        : null / size=1    <- 지울 수도 없다
```

```text
put 할 때 (name="a")                       필드를 바꾼 뒤 (name="b")

  hash = 128 -> 칸 0 에 저장                 hash = 129 -> 칸 1 을 본다
  +------+------+                           +------+------+
  | 칸 0 | 칸 1 |                           | 칸 0 | 칸 1 |
  | Tag  |      |                           | Tag  | 비었다|
  +------+------+                           +------+------+
                                              엔트리는 칸 0 에 그대로 있다
                                              아무도 칸 0 을 안 본다
```

- `Objects.hash("a")` = `31 + 'a'.hashCode()` = `31 + 97` = **128**, `"b"` 는 **129**.\
  둘 다 손계산과 실행이 일치한다.
- 저장 위치는 **넣을 때의 해시로 정해진다.** 나중에 해시가 바뀌어도 **이사하지 않는다.**
- 그래서 엔트리는 **살아 있으면서 도달 불가능**해진다.\
  `size()` 는 1이고 `toString` 에도 보이는데 `get` 도 `remove` 도 실패한다.
- 이것이 **메모리 누수의 한 형태**다 — 지울 방법이 없으니 맵이 살아 있는 한 남는다.
- 방어: **키로 쓸 객체는 불변으로 만든다.** `equals`/`hashCode` 가 읽는 필드를 전부 `final` 로.

### 3. 대칭성을 깬다 — JDK 안에도 있는 사고

`java.util.Date` 와 `java.sql.Timestamp` 는 실제로 대칭성을 어긴다.

**실행 결과** (`JdkSym.java` / `JdkSym2.java`)

```text
d.equals(t) : true
t.equals(d) : false
d.hashCode()==t.hashCode() : true
[d].contains(t) : false
[t].contains(d) : true
add(Date) -> add(Timestamp) : size 2
add(Timestamp) -> add(Date) : size 1     <- 같은 두 객체, 넣는 순서만 다르다
```

```text
같은 두 객체를 같은 HashSet 에 넣는데

  add(d) 먼저                              add(t) 먼저
  +---------------------------+            +---------------------------+
  | d 저장                     |            | t 저장                     |
  | add(t): t.equals(d)=false  |            | add(d): d.equals(t)=true  |
  |   -> 다른 것으로 보고 추가   |            |   -> 같은 것으로 보고 무시  |
  | size = 2                   |            | size = 1                  |
  +---------------------------+            +---------------------------+
```

- **넣는 순서가 `size()` 를 바꾼다.** 컬렉션이 "같음"을 물을 때 **어느 쪽의 `equals` 를 부르느냐**가 갈리기 때문이다.
- `List.contains` 도 마찬가지다 — `[d].contains(t)` 와 `[t].contains(d)` 의 답이 반대다.
- 원인: 상위 타입이 `instanceof` 로 비교하면 **하위 타입도 통과**하는데, 하위 타입은 자기 필드까지 보므로 통과시키지 않는다.
- 방어 둘 중 하나.
  - **`getClass() != o.getClass()` 로 비교**한다 -> 대칭이 되지만 하위 타입이 상위와 절대 같아지지 않는다.
  - **상속 대신 조합을 쓰고 클래스를 `final` 로** 만든다 -> 문제 자체가 안 생긴다.

### 4. `equals(내타입)` 을 쓴다 — 재정의가 아니라 오버로딩

```java
class Id {
    final int v;
    public boolean equals(Id other) {      // Object 가 아니다!
        return other != null && other.v == v;
    }
    @Override public int hashCode() { return v; }
}
```

**실행 결과** (`Overload.java`)

```text
a.equals(b) 정적 타입 Id     : true      <- 내 메서드가 불렸다
a.equals((Object) b)         : false     <- Object.equals 가 불렸다
List.of(a).contains(b)       : false
new HashSet<>(List.of(a,b)).size() : 2
```

```text
  a.equals(b)          정적 타입이 Id  -> 내가 쓴 equals(Id) 가 뽑힌다   -> true
  a.equals((Object) b) 정적 타입 Object -> Object.equals(Object) 가 뽑힌다 -> false

  컬렉션 내부는 언제나 Object 로 받는다 -> 내 메서드는 영원히 안 불린다
```

- **내 테스트만 통과한다.** 테스트에서는 정적 타입이 구체 타입이라 내 메서드가 불리기 때문이다.
- 컬렉션·프레임워크는 전부 `Object` 로 받으므로 내 메서드를 **한 번도 부르지 않는다.**
- `@Override` 를 붙이면 컴파일이 막힌다.

```text
$ javac OverrideCatch.java
OverrideCatch.java:4: error: method does not override or implement a method from a supertype
    @Override public boolean equals(Id2 other) { return other.v == v; }
    ^
1 error
```

- 그래서 **`@Override` 는 취향이 아니라 계약 검사 장치**다.

### 5. `hashCode` 를 저장하거나 비교의 근거로 쓴다

- javadoc 첫 조항이 **"This integer need not remain consistent from one execution of an application to another execution"** 이라고 못박았다.
- 그래서 `hashCode` 를 DB·파일·캐시 키로 저장하면 **다음 실행에서 안 맞을 수 있다.**
- `Object` 의 기본 `hashCode` 는 객체 정체성 기반이라 **보장이 없다** — 1번의 표에서 JDK 버전만 바꿔도 값이 달라졌다.
- `String.hashCode` 처럼 값 기반이면 실행 간에도 같지만, **그것은 그 클래스의 구현 세부**이지 `Object` 계약의 보장이 아니다.
- 그리고 **`hashCode` 가 같다고 같은 객체가 아니다**(셋째 조항). `if (a.hashCode() == b.hashCode())` 는 `equals` 의 대체가 아니다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 어떻게 |
|---|---|
| 값을 나타내는 타입(좌표·금액·ID) | **`record`** 를 먼저 고려. 셋이 자동으로 같이 간다 |
| `record` 가 안 되는 값 타입 | 셋을 손으로. `final` 클래스 + `final` 필드 + `@Override` |
| 식별자(ID)가 있는 엔티티 | ID만으로 `equals`/`hashCode`. 단 **ID 가 나중에 생기면**(DB 채번) 넣은 뒤 해시가 바뀐다 — 2번 함정 |
| 상속 계층이 있는 타입 | `getClass()` 비교로 대칭성을 지키거나, 아예 `final` 로 막는다 |
| `equals` 를 쓸 일이 없는 타입(서비스·컨트롤러) | **재정의하지 않는다.** 기본 동일성 비교가 맞다 |
| `toString` | 거의 모든 값 타입에 쓴다. 단 **동작의 근거로는 쓰지 않는다** |

판단 규칙 세 줄.

- **`equals` 를 건드렸으면 같은 커밋에서 `hashCode` 를 건드린다.**
- **키로 쓸 객체는 불변으로.** 불변이 아니면 키로 쓰지 않는다.
- **`@Override` 를 반드시 붙인다.** 오버로딩 사고를 컴파일러가 잡게 한다.

## 핵심 문장

- 계약은 **`equals` 다섯 조항 + `hashCode` 세 조항**이고, 둘 사이의 다리는 **"equals 로 같으면 hashCode 도 같다"** 한 방향뿐이다.
- 해시 컬렉션은 **칸을 먼저 고르고 그 칸만 본다.** 칸이 틀리면 `equals` 는 불리지도 않는다.
- 그래서 계약 위반은 **예외가 아니라 조용한 오답**으로 나타난다 — `size()` 와 `toString` 에는 보이는데 `get` 만 실패한다.
- **`List` 는 멀쩡하고 `Map`/`Set` 만 틀린다.** 리스트는 해시를 안 쓰기 때문이다. 이 비대칭이 진단을 어렵게 만든다.
- `toString` 은 계약이 아니라 권고이며, javadoc 이 **"실행 간에 안정적이지 않다"**고 명시했다 — 파싱·저장 금지.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 27번)
- [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) — **해시 테이블의 원리가 정본이다.**\
  버킷·충돌·체이닝·리사이즈·로드 팩터는 거기서 본다. 이 문서는 그 위에서 **"계약을 어기면 어디가 틀리나"**만 다룬다
- [`../../../../../data-structure/29-open-addressing/`](../../../../../data-structure/29-open-addressing/) — 개방 주소법. 충돌 처리의 다른 갈래
- [`../../../../oop-basics/`](../../../../oop-basics/) — 동일성(identity)과 동등성(equality)의 개념 구분
- [`../06-initialization-order/`](../06-initialization-order/) — 「어디서 틀리나」 4번의 `@Override` 가 계약 위반을 컴파일 에러로 바꾸는 또 다른 사례
- [**09번 주제**](../09-inheritance-overriding/)(상속과 오버라이딩) — 오버로딩 해소와 동적 디스패치가 정본
- [**14번 주제**](../14-records/)(`record`) — 셋을 자동 생성하는 조건과 못 하는 것
- [**28번 주제**](../28-comparable-comparator/)(`Comparable`/`Comparator`) — **`equals` 와 `compareTo` 가 어긋날 때** 무엇이 깨지나. `TreeMap` 은 `equals` 가 아니라 `compareTo` 로 같음을 판정한다

## 용어 풀이

- **계약(contract)** — 컴파일러가 강제하지 못하지만 어기면 표준 라이브러리가 오동작하는 약속.
- **동치 관계** — 반사·대칭·추이를 만족하는 "같음". 이걸 만족해야 객체들이 겹치지 않는 묶음으로 나뉜다.
- **반사성** — 자기 자신과는 항상 같다.
- **대칭성** — `x.equals(y)` 와 `y.equals(x)` 의 답이 같아야 한다.
- **추이성** — `x=y`, `y=z` 면 `x=z` 여야 한다.
- **일관성** — 비교에 쓰는 값이 안 바뀌면 몇 번 불러도 같은 답.
- **버킷(bucket)** — 해시 테이블이 원소를 나눠 담는 칸. 상세는 `data-structure/05-hashmap`.
- **identity hash code** — `Object.hashCode()` 의 기본 구현이 주는 값. 객체마다 다르고 실행마다 달라진다.
- **오버로딩(overloading) / 오버라이딩(overriding)** — 같은 이름에 다른 매개변수 / 상위 타입의 같은 시그니처를 다시 구현. `equals(Id)` 는 전자다.
- **조용한 실패(silent failure)** — 에러 없이 정상처럼 끝나는데 결과만 틀린 것.
- **`@Override`** — 상위 타입의 메서드를 재정의한다는 선언. 아니면 컴파일 에러가 난다.

---

## 더 들어가면

- **`Objects.hash(...)` 는 배열을 하나 만든다.**\
  가변 인자라 호출마다 `Object[]` 가 생기고 기본형은 박싱된다. 뜨거운 경로에서는 `31 * x + y` 를 손으로 쓰는 게 낫다.\
  `int` 하나뿐이면 `Integer.hashCode(x)` 가 할당 없이 끝난다.
- **`hashCode` 를 `return 1;` 로 쓰면 계약은 지켜진다.**\
  "다르면 달라야 한다"는 조항이 없기 때문이다. 대신 모든 원소가 한 칸에 몰려 조회가 O(n)이 된다 — **정확성은 살고 성능만 죽는** 위반이다.
- **`TreeMap`/`TreeSet` 은 `equals` 를 안 쓴다.**\
  `compareTo`(또는 `Comparator`)의 결과가 `0` 인지로 같음을 판정한다. 그래서 `equals` 와 `compareTo` 가 어긋나면 **같은 객체가 `HashSet` 에서는 하나, `TreeSet` 에서는 둘**이 된다. 목록의 28번 주제.
- **`record` 의 `equals` 도 `instanceof` 로 쓰였지만 대칭성 문제가 없다.**\
  `record` 는 암묵적으로 `final` 이라 하위 타입이 존재할 수 없기 때문이다.
- **IDE 가 생성한 `equals` 는 보통 `getClass()` 비교를 쓴다.**\
  대칭성은 안전해지지만 프록시(하이버네이트·스프링 AOP)가 만든 하위 클래스와는 절대 같아지지 않는다. JPA 엔티티에서 자주 문제가 된다.
