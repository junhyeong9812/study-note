# java/syntax/01 — 기본형과 래퍼: 값 의미론·오토박싱·`Integer` 캐시 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 바이트코드는 `javap -c` 출력을, JDK 소스는 `lib/src.zip` 의 실파일을 그대로 옮겼다.\
> 17.0.13 · 25.0.1 에서도 같은 프로그램을 돌려 출력이 동일함을 확인했다(다른 점은 6번에 따로 적었다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 네 줄의 출력을 예측하라

**실행 결과** (`Box1.java`, JDK 21.0.5)

```text
127 == 127 : true
128 == 128 : false
128.equals  : true
Integer==int : true
```

**네 줄의 출력은 각각 무엇인가**

- `a == b` (둘 다 127) -> **`true`**
- `c == d` (둘 다 128) -> **`false`**
- `c.equals(d)` -> **`true`**
- `e == f` (`Integer` 와 `int`) -> **`true`**

**두 번째 줄과 네 번째 줄의 결과가 갈리는 이유**

```text
c == d  : 둘 다 Integer                    e == f  : Integer 와 int
+---------------------------+              +---------------------------+
| c -> [객체 #1 : 128]       |              | e -> [객체 #3 : 128]       |
| d -> [객체 #2 : 128]       |              | f    128 (값 그 자체)      |
|                           |              |                           |
| 두 참조를 비교한다          |              | e.intValue() 로 풀어 내려   |
| if_acmpne -> 다르다 -> false|              | 128 == 128 -> true         |
+---------------------------+              +---------------------------+
```

- 128은 캐시 범위(`-128`~`127`) **밖**이라 `Integer.valueOf(128)` 이 매번 `new Integer(128)` 을 만든다.\
  그래서 `c` 와 `d` 는 다른 객체다.
- `c == d` 는 **둘 다 참조 타입**이라 참조 비교가 된다 -> `false`.
- `e == f` 는 **한쪽이 `int`** 라서 컴파일러가 `e.intValue()` 를 끼워 넣는다.\
  값 비교가 되므로 캐시와 무관하게 `true`.
- `equals` 는 애초에 값을 비교하는 메서드이므로 캐시와 무관하게 `true`.

> **캐시 범위(Integer cache)** — `Integer.valueOf` 가 새 객체를 만들지 않고 미리 만들어 둔 배열에서 꺼내 주는 값의 구간.\
> 예: JDK 21 기본값은 `-128`~`127` 이고, 이 안의 값은 몇 번을 박싱해도 같은 객체다.

### 2. 컴파일러가 무엇을 끼워 넣는가

**실행 결과** (`javap -c Box2`, JDK 21.0.5 — 출력 그대로)

```text
  static boolean sameRef(int);
    Code:
       0: iload_0
       1: invokestatic  #7    // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
       4: astore_1
       5: iload_0
       6: invokestatic  #7    // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
       9: astore_2
      10: aload_1
      11: aload_2
      12: if_acmpne     19
      15: iconst_1
      16: goto          20
      19: iconst_0
      20: ireturn
```

**소스에 없는 어떤 호출이 들어 있는가**

- `Integer.valueOf(int)` 호출이 **두 번** 들어 있다(오프셋 1, 6).
- 소스에는 `Integer a = n;` 이라고만 썼다.\
  `valueOf` 라는 글자는 소스 어디에도 없다.

```text
소스 한 줄                       클래스 파일 두 명령

Integer a = n;      ---->        iload_0                       (n 을 스택에)
                                 invokestatic Integer.valueOf  (컴파일러가 넣음)
                                 astore_1                      (a 에 저장)
```

**`a == b` 는 어떤 바이트코드 명령으로 컴파일되는가**

- `if_acmpne` — **a**ddress **c**o**mp**are, **n**ot **e**qual.\
  참조 두 개를 비교하는 명령이다.
- 값 비교였다면 `if_icmpne` 가 나왔을 것이다(3번 참조).
- 즉 `==` 의 의미는 **클래스 파일에 이미 박혀 있다.** 런타임이 판단하는 게 아니다.

**`n` 이 500이면 무엇을 반환하는가**

**실행 결과** (`BoxQ.java`)

```text
sameRef(100) = true
sameRef(500) = false
```

- 500은 캐시 범위 밖이라 `valueOf(500)` 이 두 번 다 새 객체를 만든다.
- 두 참조가 다르므로 `if_acmpne` 가 갈라져 **`false`**.
- 같은 메서드가 **인자 값에 따라 다른 답을 낸다** — 이것이 이 주제가 위험한 이유다.

> **`invokestatic`** — 클래스 메서드(정적 메서드)를 부르는 JVM 명령.\
> 예: `Integer.valueOf(5)` 는 인스턴스가 필요 없으므로 `invokestatic` 으로 불린다.

### 3. `==` 의 의미는 누가 언제 정하는가

**무엇을 보고 결정되는가**

- **두 피연산자의 정적 타입**이다.
- 규칙은 한 줄로 요약된다: **한쪽이라도 기본형이면 값 비교, 둘 다 참조 타입이면 참조 비교.**

| 왼쪽 정적 타입 | 오른쪽 정적 타입 | 컴파일된 명령 | 의미 |
|---|---|---|---|
| `int` | `int` | `if_icmpne` | 값 비교 |
| `Integer` | `int` | `intValue()` -> `if_icmpne` | 값 비교 |
| `int` | `Integer` | `intValue()` -> `if_icmpne` | 값 비교 |
| `Integer` | `Integer` | `if_acmpne` | **참조 비교** |

**컴파일 타임인가 런타임인가**

- **컴파일 타임**이다.
- 근거는 2번의 `javap` 출력이다 — 클래스 파일에 `if_acmpne` 라는 **하나의 명령**만 들어 있다.\
  런타임에 "이번엔 값 비교로 할까" 같은 분기가 없다.
- 그래서 변수의 **선언 타입만 바꿔도** 같은 코드의 의미가 뒤집힌다.

**`Integer x` 와 `int y` 를 `==` 로 비교하면**

**실행 결과** (`javap -c Box3`, 출력 그대로)

```text
  static boolean mixed(java.lang.Integer, int);
    Code:
       0: aload_0
       1: invokevirtual #7    // Method java/lang/Integer.intValue:()I
       4: iload_1
       5: if_icmpne     12
       8: iconst_1
       9: goto          13
      12: iconst_0
      13: ireturn
```

- **`Integer` 쪽이 `intValue()` 로 언박싱된다.** `int` 쪽이 박싱되는 게 아니다.
- 방향이 중요하다 — 언박싱이므로 `Integer` 가 `null` 이면 여기서 NPE 가 난다.
- 비교 명령도 `if_acmpne` 가 아니라 `if_icmpne` 로 **바뀌어 있다.**

> **`invokevirtual`** — 인스턴스 메서드를 부르는 JVM 명령. 대상 객체가 스택에 있어야 한다.\
> 예: `x.intValue()` 는 `x` 가 `null` 이면 이 명령에서 NPE 가 난다.

### 4. 캐시의 보장 범위

**JLS 가 `==` 를 `true` 로 강제하는 범위**

JLS SE 21 §5.1.7 원문:

> ... a character in the range `'\u0000'` to `'\u007f'` inclusive, or an integer in the range `-128` to `127` inclusive, then let `a` and `b` be the results of any two boxing conversions of `p`. It is always the case that `a` `==` `b`.

- 정수는 **`-128` 이상 `127` 이하**.
- `char` 는 `'\u0000'`~`'\u007f'`(= 0~127).
- `boolean` 은 `true`·`false` 둘 다.

**값 말고 붙는 조건 하나**

- **상수 식(constant expression)이어야 한다.** 원문은 "the result of evaluating a constant expression (§15.29)" 라고 못박는다.
- 즉 `Integer a = 127;` 은 보장 대상이고, `Integer a = readFromFile();` 이 127을 돌려준 경우는 **JLS 의 보장 대상이 아니다.**
- 다만 `Integer.valueOf` 의 javadoc 이 "This method will always cache values in the range -128 to 127, inclusive" 라고 적어 두었으므로, **이 구현에서는** 상수 식이 아니어도 같은 객체가 나온다.\
  두 근거의 층이 다르다 — JLS 는 언어 보장, javadoc 은 API 보장이다.

**범위 밖에 대해 명세는 무엇을 말하는가**

> For other values, the rule disallows any assumptions about the identity of the boxed values on the programmer's part. This allows (but does not require) sharing of some or all of these references.

- **"프로그래머의 어떤 가정도 허용하지 않는다."**
- 공유해도 되고 안 해도 된다 — 어느 쪽도 틀린 구현이 아니다.

**`Integer a = 1000, b = 1000; a == b` 를 `true` 로 만들 수 있는가**

**있다.** 실행 결과 (`Box6.java` / `Box9.java`):

```text
$ java Box6                                             1000 == 1000 : false
$ java -XX:AutoBoxCacheMax=2000 Box6                    1000 == 1000 : true
$ java -Djava.lang.Integer.IntegerCache.high=2000 Box9  1000 : true
```

- 두 방법 다 **캐시의 위쪽 한계(`high`)를 넓히는 것**이다.
- JDK 21 소스의 `IntegerCache` static 블록이 이 프로퍼티를 읽는다.

```java
// JDK 21.0.5  java.base/java/lang/Integer.java — 실제 소스 그대로
int h = 127;
String integerCacheHighPropValue =
    VM.getSavedProperty("java.lang.Integer.IntegerCache.high");
if (integerCacheHighPropValue != null) {
    try {
        h = Math.max(parseInt(integerCacheHighPropValue), 127);
        h = Math.min(h, Integer.MAX_VALUE - (-low) -1);
    } catch( NumberFormatException nfe) { }
}
high = h;
```

- `Math.max(..., 127)` 이 있으므로 **127보다 작게는 못 줄인다.**
- 같은 클래스 파일이 **JVM 옵션 하나로 결과가 뒤집히는** 것이 이 사실의 실무적 함의다.

**`Integer a = -129, b = -129; a == b` 를 `true` 로 만들 수 있는가**

**없다.** 실행 결과 (`Box9.java`, 옵션 유무 둘 다):

```text
-128 : true
-129 : false
```

- 아래쪽 한계는 소스에 **상수로 박혀 있다.**

```java
private static final class IntegerCache {
    static final int low = -128;      // 고정
    static final int high;            // 프로퍼티로 조절 가능
```

- `low` 를 읽는 프로퍼티가 없으므로 **아래쪽은 어떤 옵션으로도 못 넓힌다.**
- 그래서 캐시는 **위쪽만 열려 있는 비대칭 구간**이다.

```text
      못 넓힘                          넓힐 수 있음
   <-------------|                |------------------->
                -128 ........... 127
                 |<-- 늘 캐시됨 -->|
```

### 5. 이 메서드가 끝난 뒤 세 값은 무엇인가

**실행 결과** (`Box7.java`)

```text
n=1 boxed=1 arr[0]=99
```

**세 값**

- `n` = **1** (안 바뀜)
- `boxed` = **1** (안 바뀜)
- `arr[0]` = **99** (바뀜)

```text
호출 직후 (값이 복사되어 들어간 상태)        메서드 안에서 세 줄을 실행한 뒤

  호출자 n     1                              호출자 n     1        <- 그대로
  파라미터 n   1                              파라미터 n   99       <- 복사본만 바뀜

  호출자 boxed --> [Integer 1]                호출자 boxed --> [Integer 1]   <- 그대로
  파라미터 boxed -/                           파라미터 boxed --> [Integer 99] <- 가리키는 곳만 바뀜

  호출자 arr   --> [ 1 ]                      호출자 arr   --> [ 99 ]  <- 같은 배열의 안이 바뀜
  파라미터 arr -/                             파라미터 arr -/
```

그림 해설 (한 단계씩):

- `n = 99` 는 **복사본에** 99를 썼다. 호출자의 `n` 은 그 복사본을 안 본다.
- `boxed = 99` 는 **복사된 열쇠가 다른 사물함을 가리키게** 했다.\
  호출자의 열쇠는 여전히 옛 사물함을 가리킨다.
- `arr[0] = 99` 만 다르다 — 열쇠는 복사됐지만 **그 열쇠로 연 사물함 안을 고쳤다.**

**`boxed` 는 참조 타입인데 왜 `arr` 처럼 바뀌지 않는가**

- `arr[0] = 99` 는 **가리키는 대상의 내용**을 바꾼 것이고,\
  `boxed = 99` 는 **가리키는 대상을 바꾼 것**이다.
- 전자는 호출자와 공유하는 객체를 건드리므로 보이고, 후자는 지역 변수 하나만 건드리므로 안 보인다.
- 즉 Java 의 전달은 **언제나 값 전달**이고, 참조 타입은 "참조라는 값"을 복사해 넘긴다.

**`Integer` 가 불변이 아니었다면**

- `boxed.setValue(99)` 같은 메서드가 있었다면 **호출자의 `boxed` 에도 보였을 것이다.**
- 그리고 그 순간 캐시가 치명적이 된다 — `Integer` 5를 고치면 **프로그램 전체의 5가 바뀐다.**\
  캐시로 객체를 공유하는 설계는 **불변이라는 전제 위에서만** 성립한다.

> **불변 객체(immutable object)** — 만들어진 뒤 내부 상태가 절대 바뀌지 않는 객체.\
> 예: `Integer` 의 필드는 `private final int value` 하나이고 세터가 없다. 그래서 여러 곳이 같은 객체를 나눠 써도 안전하다.

### 6. 이 메서드는 언제 터지는가

**실행 결과** (`BoxQ.java`)

```text
pick(true, null)  = 0
pick(false, null) -> NPE: Cannot invoke "java.lang.Integer.intValue()" because "<parameter2>" is null
```

**`pick(true, null)`**

- **`0` 을 반환한다.** 안 터진다.
- 삼항 연산자는 **고른 쪽만 평가**한다. `flag` 가 참이면 `box` 를 아예 건드리지 않는다.

**`pick(false, null)`**

- **`NullPointerException` 을 던진다.**

```text
javap -c 로 본 pick 의 실제 경로 (flag = false 일 때)

  0: iload_0                       flag 를 읽는다
  1: ifeq 8                        false 이면 8번으로
  ...
  8: aload_1                       box 를 스택에 (null)
  9: invokevirtual Integer.intValue()   <- 여기서 NPE
 12: invokestatic  Integer.valueOf      (도달 못 함)
 15: areturn
```

- `flag ? 0 : box` 는 **숫자 조건식**이다 — 한쪽(`0`)이 `int` 라서.
- 숫자 조건식은 이항 승격을 적용하므로 **`box` 를 `intValue()` 로 풀어 내린다.**
- `box` 가 `null` 이니 그 호출에서 터진다.
- 그리고 결과를 다시 `Integer` 로 반환해야 하므로 **`valueOf` 로 되박는다** — 풀었다가 다시 싸는 왕복이 소스에는 안 보인다.

**스택트레이스에 나오는 메서드 이름**

- **`java.lang.Integer.intValue()`**.
- 내가 쓴 적 없는 메서드다.\
  helpful NullPointerException 이 켜져 있어 `because "<parameter2>" is null` 까지 알려 준다.
- `box` 가 파라미터가 아니라 지역 변수면 같은 자리가 `"<local2>"` 로 나온다(`Box4.java` 로 확인).

**한 글자 수준으로 고치려면**

```java
return flag ? Integer.valueOf(0) : box;    // 또는 (Integer) 0
```

**실행 결과** (`javap -c Box5`, `pickSafe`)

```text
  0: iload_0
  1: ifeq 11
  4: iconst_0
  5: invokestatic Integer.valueOf    <- 여기서 박싱
  8: goto 12
 11: aload_1                         <- box 를 그대로
 12: areturn
```

- 양쪽이 다 `Integer` 가 되어 **참조 조건식**이 된다.
- `intValue()` 가 사라졌다 -> NPE 도 사라진다.
- **무엇이 달라지는가**: 이제 `pick(false, null)` 이 `null` 을 **반환한다.**\
  예외가 사라진 게 아니라 **예외 대신 `null` 이 흘러가는 것**이다 — 호출자가 그걸 감당하게 된다.\
  터지는 자리를 여기서 저기로 옮긴 것이므로, 진짜 고치려면 `null` 을 어디서 막을지를 정해야 한다(목록의 **60번 주제**).

### 7. 이 두 줄이 NPE 를 내는지 예측하라

**실행 결과** (`Box4.java` / `BoxQ.java`)

```text
1) NPE: Cannot invoke "java.lang.Integer.intValue()" because the return value of "java.util.Map.get(Object)" is null
Integer w = m.get -> null
```

**어느 쪽이 터지는가**

- **(A) 가 터진다.** `int v = m.get("missing");`
- (B) 는 안 터진다 — `w` 에 `null` 이 들어갈 뿐이다.

```text
(A)  int v = m.get("missing");                (B)  Integer w = m.get("missing");

  m.get(...)  -> null                           m.get(...)  -> null
       |                                             |
       v  왼쪽이 int 라 언박싱 강제                    v  왼쪽도 Integer — 변환 없음
  null.intValue()   -> NPE                      w = null      -> 통과
```

**예외 메시지에 등장하는 메서드**

- **`java.lang.Integer.intValue()`**.
- 소스에는 없다 — **컴파일러가 대입문의 왼쪽 타입을 보고 끼워 넣은 것**이다.
- 메시지의 뒷부분이 `because the return value of "java.util.Map.get(Object)" is null` 이라 **어느 식이 null 이었는지**까지 알려 준다.

**`getOrDefault` 는 (A)를 고치는가**

**실행 결과**

```text
getOrDefault      = 0
int v = getOrDefault -> 0
```

- **고친다.** 키가 없으면 `0` 을 돌려주므로 언박싱할 대상이 `null` 이 아니다.
- 다만 **의미가 바뀐다** — "없음"과 "0"이 구분되지 않는다.\
  재고가 없는 상품과 재고가 0인 상품을 같게 취급해도 되는지는 도메인이 답할 문제다.
- 값 자체가 `null` 로 저장돼 있으면 `getOrDefault` 도 `null` 을 돌려준다(기본값은 **키가 없을 때만** 쓰인다).

> **조용한 실패(silent failure)** — 에러 없이 정상처럼 끝나는데 결과만 틀린 것.\
> 예: `getOrDefault(key, 0)` 로 NPE 를 없앴는데 "재고 없음"이 "재고 0"으로 둔갑해 흘러가는 것.

### 8. 어느 래퍼에 캐시가 있는가

**실행 결과** (`Box4.java`, JDK 21.0.5 — 17·25 동일)

```text
3) Long 127: true / Long 128: false
3) Char 127: true / Char 128: false
3) Boolean: true
3) Double 1.0: false
```

**`Long l1 = 127L, l2 = 127L; l1 == l2`**

- **`true`.** `Long` 도 `-128`~`127` 캐시를 갖는다.
- `128L` 은 `false` — 경계가 `Integer` 와 같다.
- 단 `-XX:AutoBoxCacheMax` 는 **`Integer` 전용 옵션**이라 `Long` 의 범위는 못 넓힌다.

**`Double d1 = 1.0, d2 = 1.0; d1 == d2`**

- **`false`.**

**`Double` 에 캐시가 없는 이유**

```text
Integer 의 캐시                              Double 이라면

  -128 .. 127  = 256개                        1.0 과 1.0 사이에도
  전부 미리 만들어 배열에 담을 수 있다          표현 가능한 값이 무수히 많다
  인덱스 = i + 128  (산수 한 번)               "자주 쓰는 256개"를 고를 기준이 없다
```

- 정수는 **작은 연속 구간을 통째로** 미리 만들 수 있고, 인덱스 계산이 뺄셈 한 번이다.
- 부동소수는 그런 구간을 정의할 수 없다 — `0.1`·`1e-300`·`3.14` 중 무엇을 캐시할지 정할 근거가 없다.
- JLS §5.1.7 도 캐시 보장 대상에 `float`·`double` 을 넣지 않았다(1번 인용의 타입 목록에 없다).
- 실무 함의: **`Double` 은 `==` 가 거의 항상 `false`** 라 오히려 버그가 빨리 드러난다.\
  값 비교는 `Double.compare` 또는 허용 오차 비교를 쓴다(부동소수 비교 자체는 [`../../../../data-representation/`](../../../../data-representation/) 가 정본).

**`Boolean b1 = true, b2 = true; b1 == b2`**

- **`true`.**
- `Boolean` 의 값은 `true`/`false` 둘뿐이라 **전 범위가 캐시된다.**\
  `Boolean.valueOf` 는 `Boolean.TRUE`/`Boolean.FALSE` 두 상수 중 하나를 돌려준다.
- 그래도 `==` 로 비교하는 습관은 들이지 않는다 — `new Boolean(true)` 나 다른 경로로 만든 객체면 깨진다.

### 9. 다른 주제와 잇기

**`IntStream.boxed()` 는 내부에서 무엇을 부르는가**

```java
// JDK 21.0.5  java.base/java/util/stream/IntPipeline.java  232~234행 — 실제 소스 그대로
public final Stream<Integer> boxed() {
    return mapToObj(Integer::valueOf, 0);
}
```

- **`Integer::valueOf`** 를 부른다 — 이 주제의 그 `valueOf` 다.
- 그래서 `IntStream.range(0, 200).boxed()` 가 만드는 `Integer` 중 **`-128`~`127` 구간은 캐시에서 나오고 그 위는 새 객체**다.
- 이어지는 함의: `IntStream` 으로 있을 동안은 객체가 하나도 안 생기고, `boxed()` 를 부르는 순간 원소 수만큼 박싱이 일어난다.\
  자세한 것은 [`../44-stream-creation/`](../44-stream-creation/).

**기본형 대신 래퍼를 골라야만 하는 상황 두 가지**

1. **컬렉션·제네릭의 타입 인자로 쓸 때.**\
   `List<int>` 는 컴파일되지 않는다 — 제네릭 타입 인자는 참조 타입만 된다.\
   이유(타입 소거)는 목록의 **19번 주제**가 정본이다.
2. **"값이 없음"을 표현해야 할 때.**\
   nullable 한 DB 컬럼, 아직 안 들어온 응답 필드.\
   `int` 로 받으면 0과 "없음"이 같은 값이 되어 **구분 자체가 사라진다.**

**래퍼를 골랐을 때 리뷰에서 반드시 확인할 한 가지**

- **그 변수에 `==` 나 `!=` 가 붙은 자리가 있는가.**
- 있으면 양쪽 정적 타입을 본다 — 둘 다 래퍼면 거의 항상 버그다.
- 부수적으로 확인할 것 하나 더: **언박싱되는 자리에 `null` 이 올 수 있는가.**\
  `int x = someInteger;`·`if (someBoolean)`·산술 연산이 전부 언박싱 지점이다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Box1` | 127/128 의 `==`, `equals`, `Integer==int` | 17 · 21 · 25 (동일) |
| `Box2` `javap -c` | 오토박싱이 `Integer.valueOf` 로, `==` 가 `if_acmpne` 로 컴파일됨 | 21 |
| `Box3` `javap -c` | `Integer==int` 가 `intValue()` + `if_icmpne` 로 컴파일됨 | 21 |
| `Box4` | `null` 언박싱 NPE, 삼항 NPE, `Long`/`Char`/`Boolean`/`Double` 캐시 | 17 · 21 · 25 (동일) |
| `Box5` `javap -c` | 숫자 조건식 vs 참조 조건식의 바이트코드 차이 | 21 |
| `Box6` | `-XX:AutoBoxCacheMax=2000` 로 1000의 `==` 가 뒤집힘 | 21 |
| `Box7` | 값 전달 — `int`·`Integer`·`int[]` 의 결과 차이 | 21 |
| `Box8` `javac` | `new Integer(int)` 경고 문구가 21과 25에서 다름 | 21 · 25 (**다름**) |
| `Box9` | `-128`/`-129` 경계, `IntegerCache.high` 프로퍼티 | 21 |
| `BoxQ` | `sameRef(500)`, `pick(true,null)`, `getOrDefault` | 21 |
| `src.zip` 열람 | `Integer.valueOf`·`IntegerCache`·`IntPipeline.boxed` 실소스 | 21 · 25 |
