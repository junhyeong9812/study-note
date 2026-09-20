# java/syntax/01 — 기본형과 래퍼: 값 의미론·오토박싱·`Integer` 캐시 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §5.1.7 Boxing Conversion](https://docs.oracle.com/javase/specs/jls/se21/html/jls-5.html) · [§15.25 Conditional Operator](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html) · JDK 21.0.5 표준 라이브러리 소스 `java.base/java/lang/Integer.java`(`lib/src.zip`).
> **실행 검증** — 이 문서의 모든 출력은 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 같은 프로그램을 **17.0.13 · 25.0.1** 에서도 돌려 **출력이 한 글자도 다르지 않음**을 확인했다.\
> 바이트코드는 `javap -c` 출력을 그대로 옮겼다.
> **버전** — 오토박싱/언박싱과 `Integer` 캐시는 **Java 5**부터. 17·21·25 에서 동작이 같다.\
> 단 `new Integer(int)` 의 **경고 문구**는 21과 25가 다르다(「어디서 틀리나」 4번).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**기본형은 종이에 적은 숫자, 래퍼는 그 숫자를 넣어 둔 사물함이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 종이에 적은 숫자 | 기본형 값 (`int` 값 그 자체) |
| 사물함 | 힙에 놓인 래퍼 객체 (`Integer` 인스턴스) |
| 사물함 열쇠 | 참조(reference) — 변수가 실제로 들고 있는 것 |
| 편의점이 미리 만들어 둔 공용 사물함 | `Integer` 캐시 (`-128`~`127`) |

- 종이에 적은 숫자를 친구에게 **베껴 주면** 종이가 둘이 된다.\
  내 종이를 고쳐 써도 친구 종이는 그대로다 — 이것이 **값 의미론**이다.
- 사물함은 다르다.\
  열쇠를 복사해 주면 **사물함은 하나**고 열쇠만 둘이다.
- 그런데 편의점이 **-128번부터 127번까지는 사물함을 미리 만들어 놓고** 있다.\
  "127 맡아 줘"라고 하면 새로 만들지 않고 **늘 그 127번 사물함**을 준다.\
  그래서 두 사람이 따로 맡겼는데 **열쇠가 같다.**
- 128부터는 미리 만들어 둔 게 없어서 **맡길 때마다 새 사물함**을 만든다.\
  두 사람의 열쇠가 다르다.

```text
Integer a = 127;  Integer b = 127;        Integer c = 128;  Integer d = 128;

  a --열쇠--+                               c --열쇠--> [사물함 #1: 128]
            +--> [공용 사물함 127]
  b --열쇠--+                               d --열쇠--> [사물함 #2: 128]

  a == b  -> true  (같은 사물함)            c == d  -> false (다른 사물함)
```

`==` 는 **"열쇠가 같은 사물함을 가리키나"** 를 묻고, `.equals` 는 **"사물함을 열어 안의 숫자가 같나"** 를 묻는다.\
**똑같은 구조로** Java 가 이렇게 동작한다: 종이 = `int`, 사물함 = `Integer` 객체, 공용 사물함 = `Integer.valueOf` 가 들고 있는 캐시 배열.

실무에서 이게 터지는 자리는 **`Map<String, Integer>` 에서 꺼낸 두 값을 `==` 로 비교하는 코드**다.\
테스트 데이터의 수량이 전부 127 이하면 통과하고, 운영에서 128을 넘는 순간 조용히 틀린다.

> **값 의미론(value semantics)** — 대입·전달할 때 값이 복사되어, 한쪽을 고쳐도 다른 쪽이 안 바뀌는 성질.\
> 예: `int b = a;` 뒤에 `b = 99` 를 해도 `a` 는 그대로다.

> **참조 의미론(reference semantics)** — 대입·전달할 때 "가리키는 곳"이 복사되어, 같은 대상을 둘이 함께 보는 성질.\
> 예: `int[] arr2 = arr1;` 뒤에 `arr2[0] = 99` 를 하면 `arr1[0]` 도 99가 된다.

> **박싱(boxing) / 언박싱(unboxing)** — `int` 를 `Integer` 객체로 감싸는 것 / 다시 꺼내는 것.\
> 예: `Integer x = 5;` 는 박싱, `int y = x;` 는 언박싱이다.

> **오토박싱(autoboxing)** — 그 감싸고 꺼내는 코드를 **내가 안 썼는데 컴파일러가 대신 넣어 주는 것**.\
> 예: 소스에는 `Integer x = 5;` 한 줄뿐인데 클래스 파일에는 `Integer.valueOf(5)` 호출이 들어 있다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 소스에 `Integer a = 127;` 한 줄만 썼는데 **컴파일러는 무엇으로 바꾸는가.**
2. `==` 는 언제 참조를 비교하고 언제 값을 비교하는가 — **그 선택을 누가 언제 하는가.**
3. 캐시는 어디서 끼어들고, **어디까지가 명세의 보장이고 어디부터가 구현의 재량인가.**

## 동작 방식

### (1) 오토박싱 — 컴파일러가 `Integer.valueOf` 를 끼워 넣는다

**언제 쓰나** — `Integer x = 5;` 처럼 기본형 자리에 래퍼를, 또는 그 반대를 쓸 때마다.\
소스에는 아무 호출도 없지만 클래스 파일에는 호출이 들어간다.

```text
내가 쓴 소스                        javac 가 만든 바이트코드 (javap -c)

static boolean sameRef(int n) {     iload_0
    Integer a = n;                  invokestatic Integer.valueOf:(I)LInteger;   <- 끼워 넣은 것
    Integer b = n;                  astore_1
    return a == b;                  iload_0
}                                   invokestatic Integer.valueOf:(I)LInteger;   <- 끼워 넣은 것
                                    astore_2
                                    aload_1
                                    aload_2
                                    if_acmpne  19       <- 참조 비교 명령
```

그림 해설 (한 단계씩):

- `Integer a = n;` 은 `Integer a = Integer.valueOf(n);` 으로 바뀐다.\
  `valueOf` 는 **내가 부르지 않은 메서드**인데 여기서 캐시가 끼어든다.
- 마지막 `a == b` 는 `if_acmpne` 로 컴파일된다.\
  `a`(address) `cmp`(compare) — **참조를 비교하는 명령**이다.
- 즉 `==` 가 값을 비교할지 참조를 비교할지는 **런타임이 아니라 컴파일 타임에** 두 피연산자의 **정적 타입**으로 이미 정해진다.

비용 — 박싱 한 번마다 `valueOf` 호출 1회.\
캐시 범위 밖이면 그때마다 **객체 하나가 힙에 새로 생긴다.**

> **정적 타입(static type)** — 컴파일러가 소스만 보고 정한 변수·식의 타입.\
> 예: `Object o = "x";` 에서 `o` 의 정적 타입은 `Object` 이고, 실제 들어 있는 것의 타입(`String`)은 런타임 타입이다.

### (2) 언박싱 — 한쪽이 기본형이면 `intValue()` 가 끼어든다

**언제 쓰나** — `Integer` 와 `int` 를 섞어 쓰는 모든 자리. `==`, 사칙연산, `if` 조건.

```text
static boolean mixed(Integer a, int b) {     aload_0
    return a == b;                           invokevirtual Integer.intValue:()I   <- 끼워 넣은 것
}                                            iload_1
                                             if_icmpne  12      <- 정수 비교 명령
```

그림 해설 (한 단계씩):

- 한쪽이 `int` 라서 `Integer` 쪽을 `intValue()` 로 **풀어 내린다.**
- 비교 명령이 `if_acmpne`(참조)가 아니라 `if_icmpne`(int compare)로 **바뀐다.**
- 그래서 캐시 범위와 무관하게 **값 비교**가 되고 항상 기대대로 동작한다.

비용 — 메서드 호출 1회.\
다만 `Integer` 쪽이 `null` 이면 **여기서 `NullPointerException`** 이 난다.

### (3) 캐시 — `Integer.valueOf` 안에서 갈린다

**언제 쓰나** — 박싱이 일어나는 모든 순간. 내가 부르지 않아도 (1)에서 이미 불린다.

```java
// JDK 21.0.5  java.base/java/lang/Integer.java  1070~1074행 — 실제 소스 그대로
public static Integer valueOf(int i) {
    if (i >= IntegerCache.low && i <= IntegerCache.high)
        return IntegerCache.cache[i + (-IntegerCache.low)];
    return new Integer(i);
}
```

```text
valueOf(127) 일 때                          valueOf(128) 일 때

  low=-128  high=127                          low=-128  high=127
  127 은 범위 안                               128 은 범위 밖
        |                                            |
        v                                            v
  cache[127 + 128] = cache[255]               new Integer(128)
        |                                            |
        v                                            v
  +---------------------+                     +---------------------+
  | 미리 만들어 둔 객체  |  <- 늘 같은 것       | 방금 만든 새 객체    |  <- 부를 때마다 새것
  +---------------------+                     +---------------------+
```

캐시 배열은 클래스 초기화 때 한 번 채워진다.\
`IntegerCache` 의 `static` 블록이 `low`(소스에 `-128` 로 고정)부터 `high` 까지를 미리 `new Integer` 로 만들어 배열에 담는다.

그림 해설 (한 단계씩):

- 범위 안이면 **배열에서 꺼내 온다** — 두 번 불러도 같은 객체다.
- 범위 밖이면 `new Integer(i)` — **부를 때마다 다른 객체**다.
- 그래서 `==` 의 결과가 **값의 크기에 따라 갈린다.**

비용 — 캐시 적중이면 배열 인덱싱 한 번, 객체 할당 0.\
미적중이면 객체 할당 1회.

### (4) 명세의 보장과 구현의 재량 — 경계가 어디인가

**언제 쓰나** — "그러면 -128~127 은 믿어도 되나?"를 판단할 때.

JLS SE 21 §5.1.7 은 이렇게 못박는다(원문 인용).

> If the value `p` being boxed is the result of evaluating a constant expression (§15.29) of type `boolean`, `byte`, `char`, `short`, `int`, or `long`, and the result is `true`, `false`, a character in the range `'\u0000'` to `'\u007f'` inclusive, or an integer in the range `-128` to `127` inclusive, then let `a` and `b` be the results of any two boxing conversions of `p`. It is always the case that `a` `==` `b`.

그리고 그 밖의 범위에 대해서는 이렇게 쓴다.

> For other values, the rule disallows any assumptions about the identity of the boxed values on the programmer's part. This allows (but does not require) sharing of some or all of these references.

```text
     -129          -128 .......... 127          128
      |              |<------------>|            |
      |              | 명세가 강제   |            |
      |              | == 가 true   |            |
      +--------------+              +------------+
       구현 재량 — 같을 수도 다를 수도 있다. 가정 금지
```

그림 해설 (한 단계씩):

- 가운데 구간만 **명세가 `==` 를 true 로 강제**한다.
- 바깥은 **"같을 수도 있다"**일 뿐 보장이 아니다 — 실제로 JVM 옵션 하나로 뒤집힌다(「어디서 틀리나」 3번).
- 그래서 **"127까지는 `==` 가 된다"를 코드가 의존하면 안 된다** — 되는 게 아니라 **우연히 명세와 겹친 것**이고, 128부터는 바로 깨진다.

비용 — 없음. 판단 규칙이다.

> **상수 식(constant expression)** — 컴파일 타임에 값이 정해지는 식(JLS §15.29).\
> 예: `127`, `120 + 7`, `static final int X = 127` 은 상수 식이고, 메서드 인자로 받은 `int n` 은 아니다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### 기본형 8개와 짝이 되는 래퍼

| 기본형 | 래퍼 | 캐시 (JDK 21 구현) | 실행으로 확인한 것 |
|---|---|---|---|
| `boolean` | `Boolean` | `true`/`false` 둘 다 | `Boolean b1=true, b2=true; b1==b2` -> `true` |
| `char` | `Character` | `0`~`127` | `127` -> `true` / `128` -> `false` |
| `byte` | `Byte` | 전 범위 | 안 돌려 봄 |
| `short` | `Short` | `-128`~`127` | 안 돌려 봄 |
| `int` | `Integer` | `-128`~`high`(기본 `127`) | `127` -> `true` / `128` -> `false` |
| `long` | `Long` | `-128`~`127` | `127L` -> `true` / `128L` -> `false` |
| `float` | `Float` | 없음 | 안 돌려 봄 |
| `double` | `Double` | 없음 | `1.0` vs `1.0` -> `false` |

「실행으로 확인한 것」 칸은 이 주제의 실험 프로그램에서 실제로 나온 출력이다(3-answer 2번).\
"안 돌려 봄"은 지어내지 않고 비워 둔 것이다.

### 값 의미론 — 무엇이 복사되는가

```java
static void tryChange(int n, Integer boxed, int[] arr) {
    n = 99;
    boxed = 99;
    arr[0] = 99;
}
// 호출: n=1, boxed=1, arr={1}
// 실행 결과: n=1 boxed=1 arr[0]=99
```

- `n` 은 값이 복사됐으니 안 바뀐다.
- `boxed` 도 **안 바뀐다** — 복사된 건 열쇠고, `boxed = 99` 는 그 복사된 열쇠가 **다른 사물함을 가리키게** 했을 뿐이다.
- `arr` 만 바뀐다 — 열쇠는 복사됐지만 **사물함 안을 고쳤다.**
- `Integer` 는 불변이라 "사물함 안을 고치는" 수단 자체가 없다.\
  그래서 래퍼는 참조 타입인데도 값처럼만 쓸 수 있다.

Java 에서 **전달은 언제나 값 전달**이다 — 참조 타입은 "참조라는 값"을 전달한다.\
이 규칙 자체는 [**03번 주제**](../03-variables-and-assignment/)(변수와 대입)가 정본이다.

### `==` 와 `equals` 가 갈리는 표

| 식 | 컴파일된 비교 | 결과 | 왜 |
|---|---|---|---|
| `int == int` | `if_icmpne` | 값 비교 | 둘 다 기본형 |
| `Integer == int` | `intValue()` 후 `if_icmpne` | 값 비교 | 한쪽이 기본형이라 언박싱 |
| `Integer == Integer` | `if_acmpne` | **참조 비교** | 둘 다 참조 타입 |
| `a.equals(b)` | `Integer.equals` 호출 | 값 비교 | 타입과 값을 둘 다 본다 |

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 다섯 다 **에러 없이, 또는 엉뚱한 줄에서 터진다.**

### 1. `Integer == Integer` 를 값 비교로 읽는다

```text
왼쪽 — 테스트 데이터가 127 이하            오른쪽 — 운영 데이터가 128 이상
+---------------------------------+      +---------------------------------+
| Integer a = order.getQty();     |      | Integer a = order.getQty();     |
| Integer b = stock.getQty();     |      | Integer b = stock.getQty();     |
| if (a == b) { ... }             |      | if (a == b) { ... }             |
|                                 |      |                                 |
| 둘 다 100 -> 같은 캐시 객체      |      | 둘 다 1000 -> 서로 다른 객체     |
| -> true. 분기를 탄다             |      | -> false. 분기를 안 탄다         |
| 테스트 초록                      |      | 에러 없음. 로그도 없음           |
+---------------------------------+      +---------------------------------+
```

왼쪽은 우연히 맞은 것이고 오른쪽이 이 코드의 진짜 동작이다 — **테스트가 초록인 채로 틀린다.**

한쪽이라도 `int` 면 언박싱되어 값 비교가 되므로 **`if (a == 100)` 은 멀쩡하다.**\
깨지는 것은 **양쪽 다 래퍼인 경우**뿐이다. 이 구분이 이 주제에서 가장 자주 헷갈리는 자리다.

### 2. 삼항 연산자가 몰래 언박싱한다

```java
static Integer pick(boolean flag, Integer box) {
    return flag ? 0 : box;                     // box 가 null 이면 여기서 NPE
}
static Integer pickSafe(boolean flag, Integer box) {
    return flag ? Integer.valueOf(0) : box;    // NPE 안 남
}
```

두 메서드의 바이트코드가 갈린 자리 (`javap -c` 출력 그대로):

```text
pick — 숫자 조건식 -> 이항 승격 -> 언박싱     pickSafe — 참조 조건식 -> 언박싱 없음

  ifeq 8                                       ifeq 11
  iconst_0                                     iconst_0
  goto 12                                      invokestatic Integer.valueOf   <- 여기서 박싱
  aload_1                                      goto 12
  invokevirtual Integer.intValue()  <- NPE     aload_1                        <- 그대로 반환
  invokestatic  Integer.valueOf                areturn
  areturn
```

- `flag ? 0 : box` 는 **숫자 조건식**이다(JLS §15.25.2) — `0` 이 `int` 라서.\
  숫자 조건식은 이항 승격을 적용하고, 이항 승격은 **양쪽을 언박싱**한다.
- 그래서 `flag` 가 `false` 여서 `box` 쪽을 고르면 `box.intValue()` 가 불리고, `box` 가 `null` 이면 그 자리에서 NPE.
- `Integer.valueOf(0)` 으로 바꾸면 **참조 조건식**이 되어 언박싱이 사라진다.
- 실제 출력: `NPE: Cannot invoke "java.lang.Integer.intValue()" because "<parameter2>" is null`\
  (같은 코드라도 `box` 가 지역 변수면 `"<local2>"` 로 나온다 — 둘 다 실행해 확인했다.)

### 3. 캐시 범위는 고정이 아니다

같은 클래스 파일, 같은 JVM, 옵션만 다르게 돌린 결과다.

```text
$ java Box6                                             1000 == 1000 : false
$ java -XX:AutoBoxCacheMax=2000 Box6                    1000 == 1000 : true
$ java -Djava.lang.Integer.IntegerCache.high=2000 Box9  1000 : true
```

- **실행 옵션 하나로 결과가 뒤집힌다.**
- `low` 는 소스에 `static final int low = -128;` 로 박혀 있어 못 바꾸고, `high` 만 움직인다.\
  그래서 `-128` 쪽 경계는 어떤 옵션으로도 넓힐 수 없다(`-129` 는 항상 `false`).
- 결론: `==` 로 래퍼를 비교하는 코드는 **내 소스만 봐서는 맞는지 알 수 없다.**

### 4. `new Integer(...)` 는 캐시를 통과하지 않는다 — 경고가 버전마다 다르다

```text
Integer p = new Integer(127);
Integer q = 127;
p == q       -> false      (new 는 늘 새 객체)
p.equals(q)  -> true
```

컴파일 경고가 21과 25에서 갈린다 — 실제 `javac` 출력이다.

```text
JDK 21.0.5  javac -Xlint:removal
  warning: [removal] Integer(int) in Integer has been deprecated and marked for removal

JDK 25.0.1  javac -Xlint:deprecation
  warning: [deprecation] Integer(int) in Integer has been deprecated
```

`lib/src.zip` 의 `Integer.java` 를 직접 열어 보면 애너테이션 자체가 다르다.

| JDK | `Integer(int)` 에 붙은 애너테이션 |
|---|---|
| 21.0.5 | `@Deprecated(since="9", forRemoval = true)` |
| 25.0.1 | `@Deprecated(since="9")` |

25에서 `forRemoval` 이 빠졌다 — **제거 예고가 취소된 것**이다.\
여전히 deprecated 이므로 새 코드에서는 쓰지 않는다.\
*(두 애너테이션이 다르다는 사실만 확인했다. 왜 바뀌었는지는 이 문서의 기준 소스로 확인하지 않았다 — 확인 필요.)*

### 5. `null` 언박싱은 내가 쓰지 않은 호출에서 터진다

```java
Map<String, Integer> m = new HashMap<>();
int v = m.get("missing");     // NPE
```

```text
NPE: Cannot invoke "java.lang.Integer.intValue()"
     because the return value of "java.util.Map.get(Object)" is null
```

- 소스 어디에도 `.intValue()` 가 없다.\
  **컴파일러가 넣은 호출에서** NPE 가 난다.
- 대입하는 왼쪽이 `int` 인 순간 언박싱이 강제된다.\
  `Integer v = m.get(...)` 였으면 `null` 이 들어갔을 뿐 안 터진다.
- 이 메시지 형태(helpful NullPointerException)는 17·21·25 에서 모두 같았다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 기본형 | 래퍼 |
|---|---|---|
| 지역 변수·계산 | 쓴다 | 박싱 비용만 붙는다 |
| 컬렉션 원소 (`List<Integer>`) | 못 쓴다 | 써야 한다 (제네릭은 참조 타입만) |
| "값이 없음"을 표현해야 할 때 | 못 쓴다 | 써야 한다 (`null`) |
| DB 컬럼이 nullable 일 때의 필드 | 0과 NULL 을 못 가른다 | 써야 한다 |
| 성능이 걸린 대량 루프 | 쓴다 | 박싱마다 객체 — `IntStream` 을 쓴다 |

판단 규칙 두 줄.

- **"없음"을 표현해야 하면 래퍼, 아니면 기본형.**
- **래퍼를 골랐으면 `==` 를 쓰지 않는다** — `equals` 또는 한쪽을 `int` 로 내려서 비교한다.

## 핵심 문장

- 소스에 `Integer x = 5;` 라고 썼으면 클래스 파일에는 `Integer.valueOf(5)` 가 들어 있다 — **캐시는 그 안에서 끼어든다.**
- `==` 가 값 비교인지 참조 비교인지는 **두 피연산자의 정적 타입으로 컴파일 타임에 결정**된다. 한쪽이라도 기본형이면 언박싱되어 값 비교다.
- `-128`~`127` 의 `==` 는 JLS 가 **상수 식에 한해** 보장하고, 그 밖은 구현 재량이라 JVM 옵션으로 뒤집힌다.
- 언박싱은 `null` 에서 NPE 를 던지고, 그 호출은 **내가 쓰지 않은 호출**이라 스택트레이스가 직관과 어긋난다.
- 삼항 연산자는 양쪽 중 한쪽이라도 기본형이면 **숫자 조건식**이 되어 반대쪽을 언박싱한다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 01번)
- [`../../../../data-representation/`](../../../../data-representation/) — 2의 보수·IEEE 754. **비트 표현 자체는 거기가 정본**이고, 여기는 Java 가 그 위에 얹은 규칙만 다룬다
- [`../../../../variables-and-memory/`](../../../../variables-and-memory/) — 스택·힙과 변수가 무엇을 들고 있는가
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — JVM·GC·JIT. **객체 할당 비용이 실제로 얼마인가는 거기**
- [**02번 주제**](../02-numeric-operations/)(수치 연산 — 이항 승격·정수 오버플로) — 이 문서의 「이항 승격」이 정본으로 다뤄지는 곳
- [**03번 주제**](../03-variables-and-assignment/)(변수와 대입 — 전부 값 전달) — 「무엇이 복사되는가」의 정본
- [`../44-stream-creation/`](../44-stream-creation/) — `IntStream` 과 `Stream<Integer>` 의 갈림. `IntStream.boxed()` 는 내부에서 `Integer::valueOf` 를 부른다

## 용어 풀이

- **기본형(primitive type)** — `boolean byte short char int long float double` 여덟 개. 객체가 아니고 값 자체다.
- **래퍼 클래스(wrapper class)** — 기본형 하나를 필드로 담은 불변 객체. `Integer` 는 `private final int value` 하나를 갖는다.
- **값 의미론** — 대입·전달 시 값이 복사되어 서로 영향을 주지 않는 성질.
- **참조 의미론** — 대입·전달 시 "가리키는 곳"이 복사되어 같은 대상을 공유하는 성질.
- **박싱 / 언박싱** — 기본형을 래퍼로 감싸기 / 래퍼에서 기본형을 꺼내기.
- **오토박싱** — 그 감싸기·꺼내기를 컴파일러가 소스에 없는 호출로 대신 넣어 주는 것.
- **정적 타입** — 컴파일러가 소스만 보고 정한 타입. `==` 의 의미를 고르는 기준.
- **상수 식(constant expression)** — 컴파일 타임에 값이 확정되는 식. JLS 의 `==` 보장이 걸리는 조건.
- **이항 승격(binary numeric promotion)** — 이항 연산의 두 피연산자를 공통 수치 타입으로 맞추는 변환. 래퍼가 섞여 있으면 **언박싱을 포함**한다.
- **`if_acmpne` / `if_icmpne`** — JVM 바이트코드 명령. 앞은 참조 비교, 뒤는 `int` 비교. `==` 가 어느 쪽으로 컴파일됐는지가 여기서 드러난다.
- **helpful NullPointerException** — NPE 메시지에 "어느 식이 null 이었는지"를 적어 주는 기능. 이 문서의 출력이 그 형태다.

---

## [Claude 추가] 더 알면 좋은 것

- `IntegerCache` 배열은 **CDS(Class Data Sharing) 아카이브에 저장**되어 JVM 기동 시 복원된다.\
  JDK 21 소스의 주석이 이를 명시하고 `CDS.initializeFromArchive(IntegerCache.class)` 를 호출한다.
- `Integer.valueOf` 의 javadoc 은 캐시 범위를 **API 계약으로도** 적어 둔다 — "This method will always cache values in the range -128 to 127, inclusive, and may cache other values outside of this range."\
  즉 `-128`~`127` 은 JLS(상수 식 한정)와 javadoc(모든 호출) 양쪽에서 보장된다.
- `-XX:AutoBoxCacheMax` 는 `Integer` 전용이다.\
  `Long.valueOf` 캐시도 `-128`~`127` 이지만 이 옵션으로는 안 늘어난다.
- `==` 를 쓰지 않아도 되는 형태: `Objects.equals(a, b)` 는 양쪽 `null` 도 안전하게 처리한다.
