# java/syntax/14 — `record` (16+): 컴팩트 생성자·불변 계약·못 하는 것 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러 메시지는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 바이트코드는 `javap -c -p` · `javap -v -p` 출력을 그대로 옮겼다.\
> 17.0.13 · 25.0.1 에서도 같은 프로그램을 돌려 **출력이 한 글자도 다르지 않음**을 확인했다\
> (배열 `toString` 의 `[I@77459877` 같은 identity 해시만 실행마다 다르다).
> 계약 인용은 JDK 21.0.5 `lib/src.zip` 의 `java/lang/Record.java` javadoc **원문**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 한 줄이 만드는 멤버를 전부 세어라

**출력** (`Ex.java (14-a)`, JDK 21.0.5 — 17·25 동일)

```text
toString()   = Point[x=1, y=2]
x()          = 1, y() = 2
equals       = true
== 는        = false
hashCode     = 33 / 33
상위 클래스   = java.lang.Record
final 인가    = true
isRecord()   = true
--- 무엇이 만들어졌나 ---
  method public final boolean Ex$Point.equals(java.lang.Object)
  method public final java.lang.String Ex$Point.toString()
  method public final int Ex$Point.hashCode()
  method public int Ex$Point.x()
  method public int Ex$Point.y()
  field  private final int Ex$Point.x
  field  private final int Ex$Point.y
  ctor   Ex$Point(int,int)
  component int x accessor=x
  component int y accessor=y
```

**왜 그런가**

**메서드는 다섯** — `equals`·`hashCode`·`toString` 셋에 컴포넌트 접근자 `x()`·`y()` 둘.

- 접근자 이름은 **`getX()` 가 아니라 `x()`** 다. 컴포넌트 이름을 그대로 쓴다.
- `equals`·`hashCode`·`toString` 은 **`public final`**, 접근자는 `public`(final 아님)이다.

**필드는 둘, 전부 `private final int`.**

- 그래서 밖에서 필드를 직접 못 보고, 안에서도 못 바꾼다.
- 이 `final` 이 「어디서 틀리나」의 출발점이다 — **`final` 인 것은 필드이지 그 필드가 가리키는 객체가 아니다.**

**생성자는 하나, 접근 제어자가 없다.**

- `ctor   Ex$Point(int,int)` — `public` 이 안 붙어 있다.
- 이 `record` 를 `class Ex` 안에 **제어자 없이**(package-private) 선언했기 때문이다.
- javadoc 의 규칙: 표준 생성자는 "must provide **at least as much access** as the record class".\
  `public record` 로 선언했으면 생성자도 `public` 이 된다.

**상위 클래스는 `java.lang.Record`**(`@since 16`).

- 상속 자리가 이미 찼으므로 `record` 는 다른 클래스를 상속할 수 없다.
- 그리고 클래스 자신이 `final` 이라 아무도 `record` 를 상속할 수 없다(`Modifier.isFinal` = true).

**`toString()` 은 `Point[x=1, y=2]`.**

- 중첩 record 인데도 `Ex$Point` 가 아니라 **단순 이름 `Point`** 가 찍혔다.
- 단 이 **형식은 보장이 아니다** — 10번 참조.

**직접 쓰면 사라지는 제어자는 `final` 이다.**

```text
Ex.java (14x-g) — A 는 전부 자동, B 는 표준 생성자만 직접, C 는 equals 를 직접

  A.equals final? true  -> public final boolean Ex$A.equals(java.lang.Object)
  B.equals final? true  -> public final boolean Ex$B.equals(java.lang.Object)
  C.equals final? false  -> public boolean Ex$C.equals(java.lang.Object)
```

- `final` 은 **"컴파일러가 만든 것"이라는 표시**이지 `record` 에 찍히는 도장이 아니다.
- 생성자를 직접 써도(`B`) `equals` 는 여전히 자동이라 `final` 이 남는다.

> **표준 생성자(canonical constructor)** — 컴포넌트와 같은 순서·타입의 파라미터를 받는 생성자. `record` 마다 정확히 하나 있다.\
> 예: `record Point(int x, int y)` 의 표준 생성자는 `Point(int, int)` 이고, 내가 안 쓰면 컴파일러가 만든다.

### 2. 컴팩트 생성자가 무엇으로 끝나는가

**출력** (`Ex.java (14-b)`)

```text
Range[lo=0, hi=10]
Money[currency=USD, amount=100]
검증 -> java.lang.IllegalArgumentException: lo > hi: 9 > 2
```

**왜 그런가**

**`new Range(-5, 10)` 이 `Range[lo=0, hi=10]` 이다.**

- `lo = Math.max(lo, 0)` 에서 고친 것은 **파라미터 변수**인데 필드에 반영됐다.

**필드 대입을 안 썼는데 반영되는 이유 — 컴파일러가 마지막에 넣는다.**

```text
javap -c -p Ex$Range  — 출력 그대로

  Ex$Range(int, int);
    Code:
       0: aload_0
       1: invokespecial #1                  // Method java/lang/Record."<init>":()V
       4: iload_1
       5: iload_2
       6: if_icmple     24
       9: new           #7                  // class java/lang/IllegalArgumentException
      12: dup
      13: iload_1
      14: iload_2
      20: invokespecial #13                 // Method java/lang/IllegalArgumentException."<init>":(Ljava/lang/String;)V
      23: athrow
      24: iload_1
      25: iconst_0
      26: invokestatic  #16                 // Method java/lang/Math.max:(II)I
      29: istore_1
      30: aload_0
      31: iload_1
      32: putfield      #22                 // Field lo:I
      35: aload_0
      36: iload_2
      37: putfield      #28                 // Field hi:I
      40: return
```

*(offset 15 의 문자열 결합 한 줄은 `javap -v` 출력에 제어문자가 섞여 나오므로 뺐다 — `"lo > hi: " + lo + " > " + hi` 를 만드는 줄이다.)*

- offset 4~23 = **내가 쓴 검증.**
- offset 24~29 = **내가 쓴 정규화.** `Math.max` 의 결과를 `istore_1`, 즉 **1번 파라미터 슬롯**에 되쓴다.
- offset 30~37 = **내가 안 쓴 두 줄.** `putfield lo`, `putfield hi`.
- **마지막 네 줄이 그 두 개의 `putfield` 다.** 이것이 "컴팩트 생성자는 대입으로 끝난다"의 실물이다.
- 그래서 **파라미터를 고치는 것이 곧 필드를 정하는 것**이고, 반대로 `this.lo = ...` 은 컴파일 에러다(8번).

**`new Range(9, 2)` — 객체가 아예 안 만들어진다.**

- `athrow` 로 가는 길에는 `putfield` 가 없다.
- 그래서 **잘못된 상태의 `record` 가 존재할 수 없다.** `record` 에서 검증의 자리가 여기인 이유다.
- `Money` 의 `currency = currency.toUpperCase()` 도 같은 구조다 — 정규화 역시 파라미터에 대입한다.

> **컴팩트 생성자(compact constructor)** — `record` 이름 뒤에 **괄호 없이** `{` 를 여는 생성자 표기.\
> 예: `Range { ... }` 는 `Range(int lo, int hi)` 의 앞부분만 쓴 것이고, 끝의 `this.lo = lo; this.hi = hi;` 는 컴파일러가 붙인다.

### 3. `record` 의 불변은 어디까지인가

**출력** (`Ex.java (14-c)`, 17·21·25 동일)

```text
만든 직후  : Order[id=#1, items=[a, b]]
밖에서 추가: Order[id=#1, items=[a, b, c]]
접근자로 추가: Order[id=#1, items=[a, b, c, d]]
```

**왜 그런가**

```text
  구멍 1 — 들어올 때                     구멍 2 — 나갈 때

  List src = ["a","b"]                     Order o
      |                                        |
      +--> new Order("#1", src)                +--> o.items()
      |    (참조를 그대로 붙잡는다)              |    (같은 참조를 그대로 준다)
      |                                        |
  src.add("c")                            o.items().add("d")
      |                                        |
      v                                        v
   record 의 내용이 바뀐다                  또 바뀐다
```

**구멍은 둘이다.**

1. **생성자로 받은 참조** — 밖에 `src` 를 들고 있던 코드가 계속 바꿀 수 있다.
2. **접근자가 주는 참조** — 받은 쪽이 그대로 바꿀 수 있다.

- `record` 가 보장하는 것은 **"`o.items` 가 다른 리스트를 가리키게 만들 수 없다"** 뿐이다.\
  `Record.java` 클래스 javadoc 의 표현이 정확히 그것이다 — "a **shallowly immutable**, transparent carrier".
- 한쪽만 막으면 다른 쪽으로 샌다.

**`HashMap` 키로 쓰고 있었다면 — 넣어 둔 키를 못 찾는다.**

- `items` 의 내용이 바뀌면 `List.hashCode` 가 바뀌고, 그러면 `record` 의 `hashCode` 도 바뀐다.
- 키는 **넣을 때의 해시로 정해진 칸**에 있는데 찾을 때는 새 해시로 다른 칸을 뒤진다.
- 증상(사라진 키·중복 삽입)의 정본은 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 「어디서 틀리나」 2번이다.

**한 줄로 두 구멍을 동시에 막는 법 — `List.copyOf`.**

```java
record Order(String id, List<String> items) {
    Order { items = List.copyOf(items); }
}
```

**출력** (`Ex.java (14-d)`)

```text
밖에서 추가해도 : Order[id=#1, items=[a, b]]
접근자로 추가  : java.lang.UnsupportedOperationException
```

- `List.copyOf` 는 **복사본**이면서 **수정 불가**다.\
  복사라서 구멍 1이 막히고, 수정 불가라서 접근자를 안 고쳐도 구멍 2가 막힌다.
- **배열에는 그런 게 없다.** `data = data.clone()` 으로 구멍 1만 막히고, 구멍 2는 접근자를 직접 고쳐야 한다.\
  그런데 접근자만 고치면 또 다른 것이 깨진다 — 6번.
- 방어 복사 관용구 자체는 [**59번 주제**](../59-immutable-objects/)가 정본이다. 여기는 **`record` 의 어디에 넣나**만 본다.

> **얕은 불변(shallow immutability)** — 필드에 담긴 값은 고정이지만 그 값이 가리키는 객체의 내부는 막지 못하는 상태.\
> 예: `final List<String> items` 는 다른 리스트로 갈아끼울 수 없을 뿐 `items.add("c")` 는 그대로 된다.

### 4. 배열 컴포넌트 record 의 네 줄

**출력** (`Ex.java (14-c)`, 17·21·25 동일 — `[I@...` 뒤 숫자만 실행마다 다르다)

```text
b1 = Buf[name=x, data=[I@77459877]
내용이 같은 두 record 가 equals? false
hashCode 같나? false
HashSet 크기 = 2
```

**왜 그런가**

`Record.equals` 의 `@implSpec` 이 판정 규칙을 못박는다.

> If the component is of a **reference type**, the component is considered equal if and only if `Objects.equals(this.c, r.c)` would return `true`.

```text
  int[] data 는 참조 타입이다
        |
        v
  Objects.equals(this.data, r.data)
        |
        v
  배열은 equals 를 재정의하지 않는다 -> Object.equals -> ==
        |
        v
  참조가 다르면 false
```

- `toString` 도 `Arrays.toString` 이 아니라 배열의 기본 `toString` 을 쓰므로 `[I@77459877` 이 박힌다.
- `hashCode` 도 같은 이유로 identity 해시가 섞여 들어가 둘이 다르다.
- 그래서 `HashSet` 에 같은 내용이 **둘** 들어간다.

**이것은 계약 위반이 **아니다**.**

- "참조가 다르면 다른 객체"라는 판정은 반사·대칭·추이·일관성·`null` 다섯 조항을 **전부 지킨다.**
- 깨진 것은 계약이 아니라 **"내용이 같으면 같겠지"라는 내 기대**다.
- 다섯 조항과 위반의 증상은 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 가 정본이다.

**고치려면 셋 — `equals`·`hashCode`·`toString`.**

```java
@Override public boolean equals(Object o) {
    return o instanceof Buf b && name.equals(b.name) && Arrays.equals(data, b.data);
}
@Override public int hashCode() { return Objects.hash(name, Arrays.hashCode(data)); }
@Override public String toString() { return "Buf[name=" + name + ", data=" + Arrays.toString(data) + "]"; }
```

**출력** (`Ex.java (14-d)`)

```text
배열 record equals = true / Buf[name=x, data=[1, 2]]
HashSet 크기 = 1
```

- **잊기 쉬운 것은 `hashCode`** 다. `equals` 만 `Arrays.equals` 로 바꾸면 "같다는데 해시가 다른" 진짜 계약 위반이 된다.
- 자동 생성의 최대 장점(셋이 함께 갱신된다)이 **여기서만 사라진다.**

**`toString` 까지 고치는 근거는 `Record.toString` 의 javadoc 이다.**

> record classes must further participate in the invariant that any two records which are **equal must produce equal strings**.

- `equals` 만 고치고 `toString` 을 두면 **같다고 판정된 둘이 다른 문자열**(`[I@a`·`[I@b`)을 뱉는다.
- 더 나은 답은 애초에 **컴포넌트를 `List<Integer>`·`String` 으로 잡는 것**이다.

### 5. 부동소수 컴포넌트 — 네 줄 중 무엇이 뒤집히나

**출력** (`Ex.java (14-c)`, 17·21·25 동일)

```text
NaN  == NaN  (원시 비교)   : false
Temp(NaN).equals(Temp(NaN)): true
0.0  == -0.0 (원시 비교)   : true
Temp(0.0).equals(Temp(-0.0)): false
```

**왜 그런가**

**둘 다 뒤집힌다.** 우연이 아니라 규칙의 귀결이다.

`Record.equals` 의 `@implSpec` 원문이 근거다.

> If the component is of a **primitive type**, using the corresponding primitive wrapper class `PW` ..., the component is considered equal if and only if `PW.compare(this.c, r.c)` would return `0`.

```text
   double 을 그냥 == 로                 record 컴포넌트로
   +---------------------------+       +---------------------------------+
   | NaN == NaN      -> false  |       | Double.compare(NaN, NaN) == 0   |
   |                           |       |                 -> true         |
   | 0.0 == -0.0     -> true   |       | Double.compare(0.0, -0.0) == 0  |
   |                           |       |                 -> false        |
   +---------------------------+       +---------------------------------+
     IEEE 754 의 == 규칙                  @implSpec 이 정한 PW.compare 규칙
```

- `Double.compare` 는 **`NaN` 을 자기 자신과 같게**, **`-0.0` 을 `0.0` 보다 작게** 정렬한다.
- `record` 가 그 `compare` 를 쓰기로 정했으니 두 결과가 그대로 따라온다.

**`equals` 계약을 구해 주는 쪽은 `NaN` 쪽이다.**

- `x.equals(x)` 가 `true` 여야 한다(반사성).
- `double` 필드를 `==` 로 비교하는 손수 쓴 `equals` 는 필드가 `NaN` 일 때 **자기 자신과도 같지 않게 되어 계약을 깬다.**
- `record` 는 `Double.compare` 를 쓰므로 그 사고를 원천적으로 막는다.

**`-0.0` 은 리터럴 없이도 생긴다.**

- `-1.0 * 0.0`, `0.0 / -1.0`, `Math.round` 이전의 중간 계산, 뺄셈 결과.
- 그래서 `Map<Temp, ...>` 에 넣어 둔 값을 **같은 계산을 다시 해도 못 찾는** 일이 생긴다.
- 방어: 컴팩트 생성자에서 정규화한다 — `celsius = celsius == 0.0 ? 0.0 : celsius;`\
  (`==` 는 `-0.0` 도 `0.0` 과 같다고 보므로 이 한 줄이 `-0.0` 을 `0.0` 으로 접는다.)
- 금액은 `double` 이 아니라 `BigDecimal`·`long`(최소 단위) — [**53번 주제**](../53-bigdecimal/).

### 6. 접근자만 방어 복사하면

**출력** (`Ex.java (14x-h)`, JDK 21.0.5 — 17·25 동일)

```text
Buf  (자동 그대로)   : r.equals(copy) = true
   같은 내용의 새 배열로 만들면 = false
Safe (접근자만 복사) : r.equals(copy) = false
```

**왜 그런가**

`Record.java` 의 클래스 javadoc 이 요구하는 불변식은 이것이다.

> For all record classes, the following **invariant must hold**: if a record R's components are `c1, c2, ... cn`, then if a record instance is copied as follows:
> ```
>     R copy = new R(r.c1(), r.c2(), ..., r.cn());
> ```
> then it must be the case that `r.equals(copy)`.

```text
  자동 그대로 (Buf)                        접근자만 복사 (Safe)
  +-------------------------------+       +-------------------------------+
  | data() 가 원본 배열을 준다      |       | data() 가 clone 을 준다        |
  |   -> copy 의 배열 == 원본 배열  |       |   -> copy 의 배열 != 원본 배열  |
  |   -> Objects.equals -> true    |       |   -> Objects.equals -> false   |
  | 불변식 **성립**                 |       | 불변식 **위반**                |
  +-------------------------------+       +-------------------------------+
```

**불변식을 깨는 쪽은 `Safe` — 방어 복사를 넣은 쪽이다.**

- 자동 그대로인 `Buf` 는 접근자가 **같은 참조**를 주므로 복사본의 `equals` 가 `true` 다.\
  (같은 내용의 **다른** 배열로 만들면 `false` 지만, 그건 불변식이 요구하는 비교가 아니다.)
- `Safe` 는 접근자가 **새 배열**을 주므로 `Objects.equals` 가 `false` 가 된다.
- 즉 `record` 가 요구하는 유일한 불변식을, **좋은 일을 하려던 쪽이** 깬다.

**규칙: 방어 복사와 `equals` 재정의는 한 묶음이다.**

- 접근자만 고친 **중간 상태가 가장 나쁘다** — 불변도 아니고 불변식도 안 지킨다.
- 14-d 처럼 `equals` 를 `Arrays.equals` 로 함께 고치면 다시 성립한다(접근자가 준 clone 도 내용이 같으므로).
- `List.copyOf` 방식은 접근자를 안 건드리므로 애초에 이 문제가 없다 — 3번에서 `List` 쪽이 더 쉬운 이유다.

**이 불변식이 깨지면 같이 깨지는 것**

- **역직렬화** — javadoc 이 적은 대로 `record` 의 역직렬화는 **표준 생성자를 거친다.**\
  "읽어서 다시 만든 것이 원본과 같다"가 이 불변식에 기댄다.
- **`record` 패턴 분해** — `case Buf(String n, int[] d)` 로 꺼내 다시 조립한 것이 같지 않게 된다([**24번 주제**](../24-record-patterns/)).
- **`Map` 키** — 꺼내서 다시 만든 키로 조회가 안 된다.

### 7. `record` 가 대신 지켜 주는 계약을 세어 보라

**`invariant must hold` 로 적힌 조항은 둘이다.**

| # | 어디에 | 내용 |
|---|---|---|
| 1 | `Record` 클래스 javadoc | `R copy = new R(r.c1(), ..., r.cn())` 이면 `r.equals(copy)` 여야 한다 — **복사 불변식** |
| 2 | `Record.toString` javadoc | `equals` 로 같은 두 record 는 **같은 문자열**을 내야 한다 ("necessarily relaxed in the rare case where corresponding equal component values might fail to produce equal strings for themselves") |

- 1번은 **"must hold"** 라고 강하게 적혀 있다. 6번이 그것을 깨는 실례다.
- 2번은 완화 조건이 붙어 있다 — 컴포넌트 자신이 같은데 다른 문자열을 내는 경우(예: 배열).

**`Record.equals` 의 `@implSpec` 판정 규칙은 두 갈래다.**

```text
  컴포넌트 c 하나를 볼 때
        |
        +-- 참조 타입이면  ->  Objects.equals(this.c, r.c) 가 true 인가
        |
        +-- 원시 타입이면  ->  PW.compare(this.c, r.c) 가 0 인가
                               (int -> Integer, double -> Double ...)
```

- 앞에 조건이 하나 더 붙는다 — **"the argument is an instance of the same record class as this record"**.
- 그리고 뒤에 면책이 붙는다 — 구체적 알고리즘·호출 메서드·**비교 순서**는 보장이 아니다(10번).

**`record` 가 문제 자체를 없앤 조항은 대칭성이다.**

```text
  일반 클래스                                 record
  class Money { ... }                         record Money(int amount) {}
       ^ extends                                   ^
  class TaggedMoney extends Money             (상속 불가 — 암묵적 final)
       |                                           |
  상위가 하위를 통과시키면 비대칭이 생긴다        비대칭이 생길 자리가 없다
```

- 대칭성 위반의 전형은 **상위 타입의 `equals` 가 `instanceof` 로 하위 타입을 통과시키는 것**이다.
- `record` 는 `final` 이라 **하위 타입이 존재할 수 없다.**\
  문제를 푼 게 아니라 **문제가 생길 조건을 없앤 것**이다. 이 서술의 정본은 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 7번이다.

**`record` 라도 깨질 수 있는 것**

- **일관성** — 가변 컴포넌트의 내용이 바뀌면 `equals`·`hashCode` 의 답이 바뀐다.\
  조항에 "provided no information used in `equals` comparisons ... is modified" 라는 단서가 붙어 있어 **형식적 위반은 아니지만**, `HashMap` 에서의 증상은 똑같이 난다(3번).
- **내가 직접 재정의하면 전부 내 책임**으로 돌아온다.\
  자동 생성분에 붙던 `final` 이 사라지는 것이 그 신호다(1번).
- **복사 불변식**은 접근자를 고치는 것만으로 깨진다(6번).

### 8. 어기면 무엇이 출력되나 — 여섯 가지

**출력** (전부 `javac` 21.0.5 의 실제 출력, `14-err e1~e6`)

```text
(1) 인스턴스 필드 추가
e1/Ex.java:3: error: field declaration must be static
        private int cached;
                    ^
  (consider replacing field with record component)

(2) 다른 클래스 상속
e2/Ex.java:3: error: '{' expected
    record Point(int x) extends Base { }
                       ^

(3) record 를 상속
e3/Ex.java:3: error: cannot inherit from final Point
    static class Sub extends Point { Sub(int x) { super(x); } }
                             ^

(4) 컴팩트 생성자에서 this.x 에 대입
e4/Ex.java:3: error: cannot assign a value to final variable x
        Point { this.x = Math.abs(x); }
                    ^

(5) 컴팩트 + 표준 생성자 둘 다
e5/Ex.java:4: error: constructor Point(int) is already defined in record Point
        Point(int x) { this.x = x; }
        ^

(6) 컴포넌트 이름을 hashCode 로
e6/Ex.java:2: error: illegal record component name hashCode
    record Bad(int hashCode) { }
                   ^
```

**왜 그런가 — 여섯 다 컴파일 에러다.**

- **(1)** `record` 의 상태는 **컴포넌트가 전부**여야 한다. 그래야 자동 생성된 `equals`/`hashCode`/`toString` 이 상태 전체를 덮는다.\
  `javac` 가 친절하게 **"(consider replacing field with record component)"** 까지 알려 준다.\
  `static` 필드는 인스턴스 상태가 아니므로 허용된다(`static final User ANONYMOUS = ...`).
- **(2)** 상위 자리가 `java.lang.Record` 로 이미 찼다.
- **(3)** 클래스가 `final` 이다. `Sub` 쪽에서 막힌다.
- **(4)** 컴팩트 생성자 안의 `x` 는 **필드가 아니라 파라미터**다. `x = ...` 는 되고 `this.x = ...` 는 안 된다.\
  보통 자바와 정반대의 감각이라 가장 많이 걸린다. 필드는 `final` 이고 대입은 컴파일러의 몫이다(2번).
- **(5)** 컴팩트와 표준은 **같은 생성자의 두 표기**다. 둘 다 쓰면 중복 선언이다.
- **(6)** 금지어는 `Object` 의 메서드 이름들이다 — `hashCode`·`toString`·`equals`·`getClass`·`wait`·`notify`·`clone`·`finalize`.\
  컴포넌트 `hashCode` 는 접근자 `hashCode()` 를 만들어야 하는데 그 시그니처가 이미 있다.

**문법 에러는 (2)뿐이다.**

- 나머지 다섯은 **의미 검사**에서 걸린 에러(`error: cannot ...`)인데, (2)만 **`'{' expected`** 다.
- 뜻하는 바: **`record` 선언에는 `extends` 를 쓰는 자리 자체가 없다.**\
  "상속을 금지한다"가 규칙으로 막히는 것이 아니라 **문법에 존재하지 않는다.**
- 반면 `implements` 는 문법에 있다 — `record User(...) implements Named { }` 는 통과한다(9번).

**참고 — 표준 생성자를 직접 쓸 때의 추가 함정** (`14x-g2`)

```text
g2/Ex.java:3: error: variable y might not have been initialized
        B(int x, int y) { this.x = x; }
                                      ^
```

- 표준 생성자를 직접 쓰기로 했으면 **모든 컴포넌트를 내가 대입**해야 한다. 컴파일러가 안 채워 준다.
- 컴팩트 생성자는 본문이 **비어 있어도 된다**(`record B(int x) { B { } }` 는 `B[x=7]` 로 정상 동작).

### 9. 만들어 주는 것과 안 만들어 주는 것

**출력** (`Ex.java (14x-f)`, JDK 21.0.5 — 17·25 동일)

```text
Comparable 인가   = false
Serializable 인가 = false
구현한 인터페이스 = []
TreeSet -> java.lang.ClassCastException
   메시지: class Ex$Point cannot be cast to class java.lang.Comparable (Ex$Point is in unnamed module of loader 'app'; java.lang.Comparable is in module java.base of loader 'bootstrap')
HashMap 조회      = a
```

**왜 그런가**

**자동으로 구현하는 인터페이스는 없다.** `getInterfaces()` 가 **빈 배열**이다.

```text
   만들어 준다                          안 만들어 준다
  +-----------------------------+     +------------------------------------+
  | 표준 생성자                  |     | 세터                                |
  | 접근자 x()                   |     | 빌더                               |
  | equals / hashCode / toString |     | withX 류 복사 메서드                |
  | java.lang.Record 상속        |     | Comparable  -> TreeSet 이 던진다    |
  | final (상속 불가)            |     | Serializable                       |
  | Record 속성 (컴포넌트 이름)   |     | **깊은 불변**                      |
  +-----------------------------+     +------------------------------------+
```

**`HashSet`/`HashMap` 은 되고 `TreeSet`/`TreeMap` 은 터진다.**

- `HashMap` 은 `hashCode` 와 `equals` 만 쓴다 — `record` 가 둘 다 만들어 주므로 **그냥 된다**(위 출력의 `HashMap 조회 = a`).
- `TreeSet` 은 `compareTo` 로 같음과 순서를 판정한다 — `Comparable` 이 없으니 **첫 `add` 부터 `ClassCastException`** 이다.
- 두 컬렉션이 "같음"을 다르게 판정한다는 사실 자체는 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 「더 알면 좋은 것」이 정본이다.
- 고치려면 `implements Comparable<Point>` 를 직접 쓰거나 `Comparator` 를 넘긴다.\
  14-e 에서 `Comparator.comparing(User::name)` 으로 정렬하는 것은 **그래서 잘 된다** — `Comparable` 없이 비교자를 주는 길이다.

**`withX` 도 안 만들어 준다.**

- 필드 하나만 바꾼 복사본이 필요하면 직접 쓴다 — `Point withX(int x) { return new Point(x, y); }`.
- 컴포넌트가 많아지면 이게 곧 boilerplate 가 된다. **`record` 가 지우지 못한 boilerplate** 가 여기다.

**빌더·세터·깊은 불변 중 `record` 가 주는 것은 **없다**.**

- 세터는 `final` 필드라 애초에 불가능하고, 빌더는 아무것도 안 생기며, 깊은 불변은 내 책임이다(3번).

**직렬화 — 붙지는 않지만, 붙이면 표준 생성자를 거친다.**

`Record.java` 의 `@apiNote` 원문이다.

> During deserialization the record's canonical constructor is invoked to construct the record object. Certain serialization-related methods, such as `readObject` and `writeObject`, **are ignored** for serializable records.

- 일반 클래스의 역직렬화는 생성자를 **건너뛰므로** 생성자에 쓴 검증이 통째로 우회된다.
- `record` 는 그러지 않는다 — **컴팩트 생성자의 검증이 역직렬화에도 걸린다.**
- 대신 `readObject`/`writeObject` 로 하던 커스터마이즈는 못 한다.
- **실행으로 확인했다** (`Ex.java (14-ser)`, JDK 21.0.5) — 같은 값을 직렬화했다 되읽으면서 생성자에 출력 한 줄을 심었다.

```text
--- 만들 때 ---
    [record 컴팩트 생성자 실행] x=5
    [일반 클래스 생성자 실행] x=5
--- 역직렬화할 때 ---
    [record 컴팩트 생성자 실행] x=5
record  -> RecPoint[x=5]
일반 클래스 -> ClsPoint[x=5]
```

- 되읽을 때 **record 쪽만 생성자 줄이 한 번 더** 찍혔다. 일반 클래스는 건너뛰었다.\
  javadoc 의 `@apiNote` 가 말한 그대로다.

### 10. 무엇이 언어 보장이고 무엇이 구현 세부인가

**`33` 에 기대면 안 된다.**

`Record.hashCode` 의 `@implSpec` 원문이 못박는다.

> The precise algorithm used in the implicitly provided implementation is **unspecified and is subject to change** within the above limits. The resulting integer **need not remain consistent from one execution** of an application to another execution of the same application. ... Also, a component of primitive type **may contribute its bits to the hash code differently** than the `hashCode` of its primitive wrapper class.

- 17·21·25 에서 전부 `33` 이 나온 것은 **관찰**이다. 세 버전이 같았다는 사실이 오히려 위험하다.
- 파일·DB·캐시 키에 `hashCode` 를 저장하면 안 된다(그 규칙의 정본은 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 「어디서 틀리나」 5번).

**`Point[x=1, y=2]` 형식도 보장이 아니고, 파싱하면 안 된다.**

`Record.toString` 의 `@implSpec` 원문이다.

> The precise format produced by this implicitly provided implementation is **subject to change**, so the present syntax **should not be parsed by applications to recover record component values**.

- 값을 되찾고 싶으면 **접근자를 쓴다.** 로그 문자열을 파싱하지 않는다.
- 보장되는 것은 형식이 아니라 **"equal 한 두 record 는 equal 한 문자열"** 이라는 관계뿐이다(7번).

**`invokedynamic` 은 보장이 아니다.**

- `javap` 가 보여 준 `invokedynamic` + `ObjectMethods.bootstrap` 은 **javac 의 구현 전략**이다.
- 외울 것은 명령 이름이 아니라 **"세 메서드가 컴포넌트 목록 하나에서 함께 파생된다"** 는 성질이다.

**비교 순서도 보장이 아니다.**

`Record.equals` 의 `@implSpec` 마지막 문단이다.

> The implementation **may or may not** use calls to the particular methods listed, and **may or may not** perform comparisons in the order of component declaration.

- 그래서 컴포넌트의 `equals` 에 **부작용(로깅·카운팅)을 넣으면 안 된다.** 몇 번 불릴지, 어떤 순서일지 정해져 있지 않다.

**그렇다면 보장으로 적어도 되는 것**

| 보장 | 근거 |
|---|---|
| 컴포넌트마다 참조는 `Objects.equals`, 원시는 `PW.compare == 0` | `Record.equals` `@implSpec` |
| `r.equals(new R(r.c1(), ..., r.cn()))` | `Record` 클래스 javadoc — "invariant must hold" |
| `equals` 로 같은 둘은 같은 문자열 | `Record.toString` javadoc |
| `record` 는 `final`, 상위는 `java.lang.Record` | JLS §8.10 · 실행 확인 |
| 표준 생성자·접근자·필드가 컴포넌트마다 존재한다 | `Record` 클래스 javadoc — "mandated members" |
| `Class.isRecord()`·`getRecordComponents()` 로 컴포넌트를 런타임에 읽는다 | `src.zip` `@since 16` |

### 11. 어디까지가 이 주제이고 어디부터가 다른 주제인가

**`record` 의 연혁**

- [`../../../../../../history/java/java-16.md`](../../../../../../history/java/java-16.md) 가 정본이다 — JEP 395, 14(1차)·15(2차) preview 를 거쳐 16에서 정식.
- 거기는 **언제·왜 들어왔나**(설계 논쟁·동시에 정식화된 `instanceof` 패턴), 여기는 **어떻게 쓰고 무엇을 못 하나**.
- 1차 preview 는 [`../../../../../../history/java/java-14.md`](../../../../../../history/java/java-14.md), `record` 패턴 정식화는 [`../../../../../../history/java/java-21.md`](../../../../../../history/java/java-21.md).

**`equals`/`hashCode` 계약**

- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 가 정본이다 — 다섯 조항·세 조항과 위반의 증상.
- 여기는 그 위에서 **`record` 가 대신 지켜 주는 범위**(컴포넌트 단위 비교, `final` 이라 대칭성 문제 없음)와 **배열에서 뚫리는 구멍**만 다룬다.

**방어적 복사**

- [**59번 주제**](../59-immutable-objects/)(불변 객체 만들기)가 **관용구 자체의 정본**이다 — 무엇을 복사하고 무엇은 안 해도 되나.
- 여기가 맡는 부분은 **`record` 의 어디에 그 관용구를 넣나** — 컴팩트 생성자(들어올 때)와 접근자(나갈 때), 그리고 **접근자만 고치면 복사 불변식이 깨진다**는 것(6번).
- 개념으로서의 캡슐화·불변은 [`../../../../oop-basics/`](../../../../oop-basics/) 가 정본이고, 여기는 **자바 문법이 그것을 어디까지 강제하나**를 본다(필드의 `final` 까지, 가리켜진 객체는 아님).

**`record` 를 분해하는 문법**

- `if (o instanceof Point(int x, int y))` 같은 **record 패턴**은 [**24번 주제**](../24-record-patterns/)(Java 21, JEP 440).
- 그 앞 단계인 `instanceof` 타입 패턴은 [**22번 주제**](../22-instanceof-type-patterns/).
- 이 주제는 **만드는 쪽**만 다룬다.

**패턴 매칭의 완결성을 만드는 짝**

- [`../15-sealed-classes/`](../15-sealed-classes/) — `sealed` 인터페이스 + `record` 구현체.
- `sealed` 로 하위 타입 집합을 닫고 각 대안을 `record` 로 두면 `switch` 가 `default` 없이 완결된다.
- `record` 가 `final` 이라는 것이 그 완결성 판정의 전제가 된다.

**이 주제가 다루지 않는 것**

- GC·JIT·클래스로더·메모리 모델은 [`../../언어-특성/README.md`](../../언어-특성/README.md) 가 정본이다.
- 해시 테이블의 원리(버킷·충돌·리사이즈)는 [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/).
- Value Object·빌더 패턴의 배경은 [`../../../../../engineering/design-patterns-gof/`](../../../../../engineering/design-patterns-gof/).
- 지역 `record` 가 지역 클래스와 다른 점(암묵적 `static`·캡처 없음)의 정본은 [`../12-nested-classes/`](../12-nested-classes/).

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex (14-a)` | record 한 줄이 만드는 멤버 전수(메서드 5·필드 2·생성자 1·컴포넌트 2), 상위 = `java.lang.Record`, `final`, `isRecord()` | 17 · 21 · 25 (동일) |
| `Ex (14-a)` + `javap -c -p` | `equals`/`hashCode`/`toString` 이 `invokedynamic` 한 줄, 접근자는 `getfield` | 21 |
| `Ex (14-a)` + `javap -v -p` | 클래스 파일의 `Record:` 속성, `BootstrapMethods` = `ObjectMethods.bootstrap` + `x;y` + `REF_getField` 둘 | 21 |
| `Ex (14-b)` | 컴팩트 생성자의 검증·정규화가 필드에 반영됨 | 21 |
| `Ex (14-b)` + `javap -c -p` | 컴팩트 생성자가 `putfield lo` / `putfield hi` 로 끝남 (offset 30~37) | 21 |
| `Ex (14-c)` | 얕은 불변 두 구멍, 배열 컴포넌트의 `equals`/`hashCode`/`HashSet`, `NaN`·`-0.0` 뒤집힘 | 17 · 21 · 25 (동일) |
| `Ex (14-d)` | `List.copyOf`·`clone()` 방어 복사 + `Arrays.*` 재정의로 전부 해소 | 21 |
| `javac --release 15 / 16` | `records are not supported in -source 15` → 16부터 통과 | 21 의 javac |
| `Ex (14-e)` | 되는 것 — 인터페이스 구현·`static` 멤버·보조 생성자·메서드 추가·`toString` 재정의·제네릭·지역 record(`static`) | 21 |
| `javac (14-err e1~e6)` | 안 되는 것 여섯의 실제 에러 메시지 | 21 |
| `Ex (14x-f)` | `Comparable`·`Serializable` 미구현, `getInterfaces()` = `[]`, `TreeSet` → `ClassCastException`, `HashMap` 은 정상 | 17 · 21 · 25 (동일) |
| `Ex (14x-g)` + `javap -c -p` | 자동 생성분만 `final`(직접 쓴 `equals` 는 `final` 아님), 직접 쓴 `equals` 는 `invokedynamic` 이 아님 | 17 · 21 · 25 (동일) |
| `javac (14x-g2)` | 표준 생성자를 직접 쓰고 컴포넌트를 빠뜨리면 `variable y might not have been initialized` | 21 |
| `Ex (14x-h)` | 복사 불변식 — 자동 그대로는 `true`, 접근자만 복사하면 `false` | 17 · 21 · 25 (동일) |
| `Ex (14-ser)` | 역직렬화가 record 의 컴팩트 생성자는 부르고 일반 클래스 생성자는 건너뜀 | 21 |
| `Ex (14-ann)` | 컴포넌트 애너테이션이 `@Target` 이 허용하는 자리로만 퍼짐(필드·접근자·파라미터·컴포넌트) | 21 |
| `src.zip` (JDK 21.0.5 `lib/src.zip`) | `Record` `@since 16` · `RecordComponent` `@since 16` · `equals`/`hashCode`/`toString` 의 `@implSpec` · 복사 불변식 · 직렬화 `@apiNote` | — (소스 직접 확인) |

**구현 의존 항목** — 버전이 오르면 다시 봐야 하는 것.

- `hashCode` 값 `33` — `@implSpec` 이 "unspecified and subject to change". **값에 기대는 서술은 이 문서에 없다.**
- `toString` 형식 `Point[x=1, y=2]` — 같은 이유로 보장 아님.
- `invokedynamic` + `ObjectMethods.bootstrap` — javac 구현 전략.
- 컴포넌트 비교 순서 — `@implSpec` 이 명시적으로 보장하지 않는다.
- 배열 `toString` 의 `[I@77459877` — identity 해시라 **실행마다 다르다**(버전 문제가 아니다).
