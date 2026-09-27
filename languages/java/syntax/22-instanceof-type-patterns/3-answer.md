# java/syntax/22 — `instanceof` 타입 패턴 (16+) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러 메시지는 Temurin JDK 에서 **실제로 돌려 얻은 것**이다.\
> 기본은 **21.0.5**이고, 도는 프로그램은 **17.0.13 · 25.0.1** 에서도 돌렸다.\
> ★ **9번은 세 판에서 갈렸다** — 그 자리는 판을 명시했다.\
> 세 판에서 같았던 것은 "같았다"라고 **관찰로** 적었다 — 보장이 아니다.\
> 버전 갈림(`--release 15` / `16`)은 JDK 21 의 `javac --release` 로 찍었다.\
> 역어셈블은 `javap -c -p` 출력을 그대로 옮겼다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 캐스트는 정말 사라졌는가

**출력** — `javap -c -p Ex.class` (JDK 21.0.5)

```text
  static java.lang.String oldWay(java.lang.Object);
    Code:
       0: aload_0
       1: instanceof    #7                  // class java/lang/String
       4: ifeq          22
       7: aload_0
       8: checkcast     #7                  // class java/lang/String
      11: astore_1
      12: aload_1
      13: invokevirtual #9                  // Method java/lang/String.length:()I
      16: invokedynamic #13,  0             // InvokeDynamic #0:makeConcatWithConstants:(I)Ljava/lang/String;
      21: areturn
      22: ldc           #17                 // String 그 밖
      24: areturn

  static java.lang.String newWay(java.lang.Object);
    Code:
       0: aload_0
       1: instanceof    #7                  // class java/lang/String
       4: ifeq          22
       7: aload_0
       8: checkcast     #7                  // class java/lang/String
      11: astore_1
      12: aload_1
      13: invokevirtual #9                  // Method java/lang/String.length:()I
      16: invokedynamic #13,  0             // InvokeDynamic #0:makeConcatWithConstants:(I)Ljava/lang/String;
      21: areturn
      22: ldc           #17                 // String 그 밖
      24: areturn
```

**왜 그런가**

- ★ **완전히 같다.** 오프셋도 상수 풀 번호도 한 글자 안 다르다.
- **`checkcast` 는 `newWay` 에도 있다**(오프셋 8). 캐스트는 사라진 것이 아니라 **소스에서 안 보일 뿐**이다.
- **성능 기능이 아니다.** 얻는 것은 **타입을 한 번만 적는 것**과 **검사·캐스트가 어긋날 수 없는 것**이고,\
  대가는 **흐름 스코프라는 규칙을 새로 배워야 하는 것**이다.
- [**23번 주제**](../23-switch-pattern-matching/)와 갈리는 지점이 여기다 —\
  거기서는 `invokedynamic typeSwitch` 라는 **실제 런타임 장치**가 들어온다. 이쪽에는 없다.

### 2. ★ 이 여섯 자리에서 `s` 가 보이는가

**출력**

| 자리 | 보이나 |
|---|---|
| 1 — `if` 본문 | **보인다** |
| 2 — `else` 본문 | 안 보인다 |
| 3 — `if` 뒤 | 안 보인다 |
| 4 — `if (!(...)) return;` 뒤 | **보인다** |
| 5 — `... && ???` 의 `???` | **보인다** |
| 6 — `!(...) \|\| ???` 의 `???` | **보인다** |
| `... \|\| s.isEmpty()` | 안 보인다 |

**왜 그런가**

- ★ **한 문장의 규칙**: **"그 줄에 도달했다는 사실이 「매칭됐다」를 함의하면 보인다."**

```text
                    o instanceof String s
                             |
            +----------------+----------------+
            |                                 |
        참인 경로                          거짓인 경로
     (s 가 매칭됐다)                    (s 는 매칭 안 됐다)
            |                                 |
        s 가 보인다                        s 가 안 보인다
```

```text
[1] if 본문        = 참인 경로                    -> 보인다
[2] else 본문      = 거짓인 경로                  -> 안 보인다
[3] if 뒤          = 둘이 합쳐진 자리             -> 안 보인다
[4] !(...) return 뒤 = "거짓의 부정" = 참인 경로   -> 보인다
[5] && 의 오른쪽   = 왼쪽이 참일 때만 평가         -> 보인다
[6] !(...) || ??? 의 오른쪽 = 왼쪽(부정)이 거짓    -> 매칭됨 -> 보인다
    ... || ??? 의 오른쪽     = 왼쪽이 거짓         -> 매칭 안 됨 -> 안 보인다
```

- (B)에서 `else` 가 없는데도 보이는 이유: **스코프를 정하는 것이 중괄호가 아니라 흐름**이기 때문이다.\
  이 방식의 이름이 **흐름 스코프(flow scoping)** 다.
- `if (o instanceof String s || s.isEmpty())` 는 **안 보인다.**\
  `||` 의 오른쪽은 왼쪽이 **거짓**일 때 평가되고, 그때 `s` 는 만들어지지 않았다.

**실행으로 확인한 것** (`Ex.java (22-a)`, JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
"abcd"  oldWay=문자열 길이 4       newWay=문자열 길이 4       andScope=긴 문자열 abcd
        earlyReturn=문자열 ABCD           orScope=내용 있는 문자열 abcd
"ab"    oldWay=문자열 길이 2       newWay=문자열 길이 2       andScope=그 밖
        earlyReturn=문자열 AB             orScope=내용 있는 문자열 ab
""      oldWay=문자열 길이 0       newWay=문자열 길이 0       andScope=그 밖
        earlyReturn=문자열                orScope=문자열이 아니거나 비었다
"42"    oldWay=그 밖            newWay=그 밖            andScope=그 밖
        earlyReturn=문자열이 아니다           orScope=문자열이 아니거나 비었다
null    oldWay=그 밖            newWay=그 밖            andScope=그 밖
        earlyReturn=문자열이 아니다           orScope=문자열이 아니거나 비었다
```

### 3. ★ 스코프를 어겼을 때의 에러

**출력** — (a) `||` 의 오른쪽

```text
Ex.java:3: error: cannot find symbol
        if (o instanceof String s || s.isEmpty()) return "?";
                                     ^
  symbol:   variable s
  location: class Ex
1 error
```

**출력** — (b) `if` 밖

```text
Ex.java:4: error: cannot find symbol
        return s.toUpperCase();
               ^
  symbol:   variable s
  location: class Ex
1 error
```

**출력** — (c) 이름 충돌

```text
Ex.java:4: error: variable s is already defined in method f(Object)
        if (o instanceof String s) return s;
                                ^
1 error
```

**왜 그런가**

- ★ (a)와 (b)의 메시지는 **완전히 같다** — `cannot find symbol` + `symbol: variable s`.
- **그것이 함정이다.** 이 문구는 **오타를 냈을 때와 똑같다.**\
  그래서 "변수 이름을 잘못 썼나" 하고 이름부터 확인하게 되는데, 실제 원인은 **스코프**다.\
  이 문구를 보면 먼저 **스코프 판정표**를 떠올리는 습관을 들인다.
- (c)만 메시지가 다르다 — `already defined`. 패턴 변수는 **지역 변수와 같은 이름 공간**을 쓴다.\
  안쪽이라고 바깥을 가려 주지 않는다.
- (a)를 고치려면 **`!` 를 붙인다** — `!(o instanceof String s) || s.isEmpty()`.\
  ★ **의미가 뒤집힌다.** 원래는 "문자열이거나 비었으면", 고친 뒤는 "문자열이 아니거나 비었으면"이다.\
  컴파일이 통과한다고 원하던 뜻이 되는 것이 아니다.

### 4. `while` 조건의 패턴

**출력** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
loopScope        = 첫 문자열 = 여기
```

**왜 그런가**

```text
  while (!(q.peek() instanceof String s)) {
      ....................                  <- 본문: 조건이 참 = 매칭 안 됨 -> s 안 보임
  }
  ########################                  <- 탈출: 조건이 거짓 = 매칭됨 -> s 보임
```

- **루프 본문 안에서는 `s` 가 안 보인다.** 본문에 도달했다는 것은 "아직 매칭 안 됨"을 뜻한다.
- 2번의 **[4] 와 같은 구조**다 — "빠져나왔다는 사실이 매칭을 함의한다."
- `if (q.isEmpty()) return ...` 을 지우면 **무한 루프**가 된다 — 돌려 확인했다(`Ex.java (22-d)`).

```text
5회를 넘겼다 — 빈 덱의 peek() = null
덱이 비었나 = true / peek() = null / (null instanceof String) = false
```

- 덱이 비면 `peek()` 이 **`null`** 을 준다. 그리고 **`null instanceof String` 은 `false`** 다.\
  그래서 `!(...)` 는 **영원히 참**이고, 조건이 스스로 끝나지 않는다.
- 위 실행은 5회 카운터로 강제로 끊은 것이다. 실제 `loopScope` 는 `isEmpty()` 검사로 막는다.

### 5. 패턴 변수는 다시 대입할 수 있는가

**출력** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
reassign("ab")   = ab!
withFinal("ab")  = final 패턴 ab
```

**왜 그런가**

- **컴파일된다.** 패턴 변수는 기본적으로 **`final` 이 아니다** — 보통의 지역 변수와 같다.
- **`final` 을 붙일 수 있다** — `o instanceof final String s`. 붙이면 재대입이 컴파일 에러가 되고,\
  람다·익명 클래스에서 캡처할 때 "effectively final 인가"를 고민할 필요가 없어진다.
- **대입하지 않는 것을 권하는 이유**: `s` 는 "검사에 통과한 그 값"이라는 뜻을 갖는다.\
  다른 값을 넣으면 그 뜻이 깨지고, 읽는 사람이 `s` 를 원본으로 믿고 읽다가 틀린다.

### 6. 패턴 둘을 잇는 법

**출력** — (a)

```text
twoPatterns(1,2) = 합 3
twoPatterns(1,"")= 정수 둘이 아니다
ternary("abc")   = 문자열(3)
ternary(42)      = 그 밖
```

**출력** — (b)

```text
Ex.java:3: error: cannot find symbol
        if (a instanceof Integer x || b instanceof Integer y) return "합? " + x + y;
                                                                             ^
  symbol:   variable x
  location: class Ex
Ex.java:3: error: cannot find symbol
        if (a instanceof Integer x || b instanceof Integer y) return "합? " + x + y;
                                                                                 ^
  symbol:   variable y
  location: class Ex
2 errors
```

**왜 그런가**

- (a)는 **컴파일되고** `a=1, b=2` 면 `합 3` 이다.
- (b)는 **에러가 2개** 다 — `x` 와 `y` 각각.\
  `||` 의 오른쪽은 왼쪽이 거짓일 때 평가되므로 `x` 는 없고, 본문에서는 **어느 쪽이 참이었는지 몰라** 둘 다 없다.
- (a)의 오른쪽(`b instanceof Integer y`)에서 **`x` 는 이미 보인다.** 거기까지 왔다는 것은 왼쪽이 참이었다는 뜻이다.
- **조건 연산자에서도 같다** — `o instanceof String s ? ... : ...` 에서 **참인 가지**에만 `s` 가 보인다.

```text
  a instanceof Integer x  &&  b instanceof Integer y
  +----------------------+    +----------------------+
  | 참이면 x 가 생긴다    |--->| 여기서 x 가 이미 보인다|
  +----------------------+    | 참이면 y 도 생긴다     |
                              +----------------------+
                                       |
                                       v
                               둘 다 보이는 본문
```

### 7. `null` 을 넣으면

**출력** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
null    oldWay=그 밖            newWay=그 밖            andScope=그 밖
        earlyReturn=문자열이 아니다           orScope=문자열이 아니거나 비었다
```

**왜 그런가**

- `newWay(null)` = `"그 밖"`, `earlyReturn(null)` = `"문자열이 아니다"`, `orScope(null)` = `"문자열이 아니거나 비었다"`.
- **`null` 은 어떤 타입 패턴에도 안 맞는다.** `instanceof` 가 `null` 에 `false` 인 옛 규칙 그대로다.
- 그래서 `equals` 에서 **`null` 검사를 생략**할 수 있다 — `o instanceof Point p` 하나가 둘을 다 한다.
- ★ **`switch` 에서는 그대로가 아니다.** Java 21 의 패턴 `switch` 는 `case null` 을 쓸 수 있고,\
  `default` 는 `null` 을 **안 받는다.** 그쪽은 [**23번 주제**](../23-switch-pattern-matching/)가 정본이다.

### 8. 못 쓰는 자리 셋

**출력** — (a) 제네릭 타입 인자

```text
Ex.java:4: error: Object cannot be safely cast to List<String>
        if (o instanceof List<String> l) return "문자열 리스트 " + l.size();
            ^
1 error
```

**출력** — (b) `var`

```text
Ex.java:3: error: 'var' is not allowed here
        if (o instanceof var v) return "" + v;
                         ^
1 error
```

**출력** — (c) 불가능한 타입

```text
Ex.java:3: error: incompatible types: String cannot be converted to Integer
        if (s instanceof Integer i) return "정수 " + i;
            ^
1 error
```

**왜 그런가**

- (a) 타입 인자는 **런타임에 없다**(타입 소거). 검사할 것이 없다. 정본은 [**19번 주제**](../19-type-erasure/).
- **`List<?> l` 로 바꾸면 통과한다** — 돌려 확인했다(`Ex.java (22-c)`, 17 · 21 · 25 동일).

```text
wildcard(List.of("a","b")) = 리스트 크기 2 첫 원소 = a
wildcard(42)                = 그 밖
```

- 다만 `l.get(0)` 의 타입은 **`Object` 라고 적히지도 않는다** — 돌려 확인했다(`Ex.java (22-e10)`).

```text
Ex.java:6: error: incompatible types: CAP#1 cannot be converted to String
            String first = l.get(0);      // Object 를 String 에 바로 넣어 본다
                                ^
  where CAP#1 is a fresh type-variable:
    CAP#1 extends Object from capture of ?
1 error
```

- **`?` 를 포착한 익명 타입 변수(`CAP#1`)** 다. `String` 으로 쓰려면 다시 캐스트하거나 패턴을 한 번 더 써야 한다.
- (c)는 **패턴 때문이 아니다.** 패턴 없이 써도 같은 에러다 — 돌려 확인했다(`Ex.java (22-e9)`).

```text
Ex.java:3: error: incompatible types: String cannot be converted to Integer
        return s instanceof Integer;      // 패턴 없이 같은 조합
               ^
1 error
```

- (b) 타입 패턴의 본질은 **타입 검사**다. `var` 면 무엇을 검사할지가 없다.\
  ★ **`record` 패턴의 컴포넌트에는 `var` 를 쓸 수 있다** — 컴포넌트 선언이 타입을 알려 주기 때문이다.\
  그쪽은 [**24번 주제**](../24-record-patterns/)가 정본이다.

### 9. ★ 몇 부터인가 — 예외가 하나 있다

**출력** — (a) JDK 17.0.13

```text
Ex.java:3: error: expression type String is a subtype of pattern type String
        if (s0 instanceof String s) return s.length();   // 이미 String 인데 String 패턴
               ^
1 error
```

**출력** — (a) JDK 21.0.5 · 25.0.1

```text
sameType("abcd") = 4
null 이면          = -1
```

**출력** — (b) JDK 21 의 `javac --release 15`

```text
Ex.java:13: error: pattern matching in instanceof is not supported in -source 15
        if (o instanceof String s) {
                                ^
  (use -source 16 or higher to enable pattern matching in instanceof)
1 error
```

`--release 16` 은 통과했다.

**왜 그런가**

- ★ (a)는 **17 에서 컴파일 에러, 21·25 에서 통과**다. 같은 소스, 다른 판.
- 17 은 "항상 참인 패턴은 쓸 이유가 없다"며 막았다. 21 에서 그 제한이 풀렸다.
- **21 에서 통과해도 `sameType(null)` 은 `-1`** 이다 — 위 실행의 둘째 줄.\
  즉 "항상 참"이 아니라 **"`null` 만 빼고 항상 참"** 이다.\
  이 구별이 [**23번 주제**](../23-switch-pattern-matching/)에서 "무조건 패턴이 `null` 을 받나"로 이어진다.
- (b)의 메시지가 **최소 버전을 직접 알려 준다** — `use -source 16 or higher`.\
  그래서 "타입 패턴은 16부터"는 이 에러 메시지에 근거한 사실이다.

```text
  버전 경계가 둘이다
  +--------------------------------------------------+
  | 16  타입 패턴 자체                                |
  | 21  같은(또는 상위) 타입을 패턴으로 받는 것        |
  +--------------------------------------------------+
    21 로 쓴 코드를 17 로 되돌리면 두 번째가 깨진다
```

### 10. `equals` 를 어떻게 쓰는가

**출력** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
Point equals     = true
```

**왜 그런가**

- **`null` 검사는 `instanceof` 안에 있다.** `null instanceof Point` 가 `false` 이므로 따로 안 써도 된다.\
  옛 형태도 같았다 — 타입 패턴이 새로 준 이점이 아니다.

```text
  옛 형태                                 타입 패턴
  +-----------------------------+        +-----------------------------+
  | if (this == o) return true; |        | return o instanceof Point p |
  | if (!(o instanceof Point))  |        |     && p.x == x             |
  |     return false;           |        |     && p.y == y;            |
  | Point p = (Point) o;        |        |                             |
  | return p.x == x && p.y == y;|        |                             |
  +-----------------------------+        +-----------------------------+
    5줄                                    1문장
```

- **줄어든 것**: 캐스트 줄과 별도 선언 줄, 그리고 `instanceof` 와 캐스트가 어긋날 여지.
- **줄지 않은 것**: `equals` 의 **계약**이다. 대칭성·추이성·일관성은 그대로 지켜야 한다.\
  정본은 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/)다.
- `record` 는 `equals` 를 자동으로 만들어 준다([`../14-records/`](../14-records/)).\
  위 코드를 직접 쓴 것은 **타입 패턴이 쓰이는 형태를 보이려는 것**이지 권장 형태라서가 아니다.

### 11. 언제 `instanceof` 를 쓰고 언제 안 쓰나

**왜 그런가**

- **사슬이 셋을 넘으면 `switch` 패턴 매칭으로 옮긴다**([**23번 주제**](../23-switch-pattern-matching/)).\
  이득은 **완결성 검사**다 — `sealed` 계층이면 가지를 빠뜨렸을 때 컴파일이 멈춘다.
- ★ **`if` 사슬은 빠뜨려도 컴파일러가 아무것도 안 해 준다** — 돌려 확인했다(`Ex.java (23-a)`).

```java
static String nameByIfElse(Shape s) {
    if (s instanceof Circle c) return "원";
    if (s instanceof Square q) return "정사각형";
    return "빠뜨린 것이 여기로 온다";
}
```

```text
Rect[w=2.0, h=3.0]   name=직사각형   ifElse=빠뜨린 것이 여기로 온다
```

- 같은 입력에 `switch` 쪽은 `직사각형`, `if` 사슬 쪽은 **엉뚱한 값**이다. 경고도 에러도 없다.
- **컴포넌트를 꺼내야 할 때**는 [**24번 주제**](../24-record-patterns/)의 `record` 패턴으로 간다.
- **타입 분기 자체를 의심해야 하는 때**: 그 타입들이 **내가 설계한 계층**일 때다.\
  그러면 다형성(메서드 재정의)으로 풀린다 — [`../09-inheritance-overriding/`](../09-inheritance-overriding/).\
  `instanceof` 가 맞는 자리는 **계층을 내가 못 고치거나**(`Object` 를 받는 경계),\
  **연산을 타입 쪽에 넣으면 안 될 때**(직렬화·표시 형식 같은 바깥 관심사)다.

### 12. 무엇이 보장이고 무엇이 구현 세부인가

**왜 그런가**

- **"문법 설탕이다"는 런타임 쪽에서만 맞다.** 소스 쪽에는 **새 규칙이 하나 늘었다**(흐름 스코프).

```text
  소스 표면                                런타임
  +-----------------------------+         +-----------------------------+
  | 타입을 1번만 적는다          |         | instanceof + checkcast      |
  | 스코프 규칙이 새로 생겼다     |   ->    | (옛 형태와 완전히 같다)      |
  | 컴파일 에러가 새로 생겼다     |         |                             |
  +-----------------------------+         +-----------------------------+
    여기에 전부 있다                        여기에는 아무것도 없다
```

- **바이트코드가 같다는 것은 구현 세부다.** javac 21 이 그렇게 만들 뿐이고,\
  명세가 "같은 바이트코드를 내라"고 요구하지는 않는다.
- **흐름 스코프 규칙은 언어 보장이다.** javac 가 `cannot find symbol` 로 거부하는 것이 근거다.

| 보장으로 적어도 되는 것 | 구현 세부 |
|---|---|
| 타입 패턴은 16부터 | 바이트코드가 옛 형태와 같다 |
| 같은 타입 패턴은 21부터 | `checkcast` 가 쓰인다 |
| `null` 은 안 맞는다 | 에러 메시지의 문구 |
| 흐름 스코프 규칙 전부 | 오프셋·상수 풀 번호 |
| 제네릭 인자·`var` 금지 | |

- ★ **17 과 21 이 달랐던 자리는 하나** — **같은(또는 상위) 타입을 패턴으로 받는 것**이다.\
  17 은 `expression type String is a subtype of pattern type String` 으로 막고, 21·25 는 통과시킨다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex (22-a)` | 옛 형태/패턴의 실행 결과 동일 · `&&`·`!`·`\|\|` 스코프 · `null` 은 안 맞음 | 17 · 21 · 25 (출력 동일) |
| `Ex (22-a)` + `javap -c -p` | ★ `oldWay` 와 `newWay` 의 바이트코드가 **한 글자도 같다** | 21 |
| `Ex (22-a)` `--release 15` | `pattern matching in instanceof is not supported in -source 15` | 21 의 javac |
| `Ex (22-a)` `--release 16` | 통과 | 21 의 javac |
| `Ex (22-b)` | 재대입 가능 · `final` 패턴 · 패턴 둘 `&&` · 조건 연산자 · `while` 스코프 · `equals` | 17 · 21 · 25 (출력 동일) |
| `Ex (22-c)` | `o instanceof List<?> l` 은 통과한다 | 17 · 21 · 25 (출력 동일) |
| `Ex (22-d)` | 빈 덱의 `peek()` 이 `null` · `null instanceof String` 이 `false` -> 무한 루프 위험 | 17 · 21 · 25 (출력 동일) |
| `Ex (22-e1)` | `\|\|` 오른쪽의 패턴 변수 -> `cannot find symbol` | 21 |
| `Ex (22-e2)` | `if` 밖의 패턴 변수 -> **같은** `cannot find symbol` | 21 |
| `Ex (22-e3)` | 이름 충돌 -> `variable s is already defined` | 21 |
| `Ex (22-e4)` | `List<String>` 패턴 -> `Object cannot be safely cast to List<String>` | 21 |
| `Ex (22-e5)` | `String` 을 `Integer` 패턴으로 -> `incompatible types` | 21 |
| `Ex (22-e6)` | `var` 패턴 -> `'var' is not allowed here` | 21 |
| `Ex (22-e7)` | ★ 같은 타입 패턴 — **17 은 에러, 21·25 는 통과**(`null` 이면 여전히 `-1`) | 17 · 21 · 25 (**갈림**) |
| `Ex (22-e8)` | `\|\|` 로 패턴 둘 -> `cannot find symbol` **2개** | 21 |
| `Ex (22-e9)` | 패턴 없는 `instanceof` 도 같은 `incompatible types` | 21 |
| `Ex (22-e10)` | `List<?>` 의 원소를 `String` 에 -> `CAP#1 cannot be converted to String` | 21 |
| `Ex (23-a)` | `if` 사슬이 가지를 빠뜨려도 **아무 말이 없다** | 21 |

**합계** — 프로그램 14개 · `javac` 28회 · `java` 14회 · `javap` 1회(메서드 2개 덤프).

**구현 의존 항목** — 버전이 오르면 다시 돌려야 하는 것

- **바이트코드가 옛 형태와 같다는 것**은 javac 21 의 코드 생성 방식이다.\
  외울 것은 명령 이름이 아니라 **"런타임에 새로 생긴 것이 없다"** 는 성질이다.
- ★ **같은 타입 패턴의 허용 여부**는 17 과 21 에서 달랐다. 버전을 낮춰 빌드하는 프로젝트라면 여기를 본다.
- **에러 메시지의 문구 자체**는 javac 의 것이다. 특히 `CAP#1` 같은 이름은 javac 가 붙이는 임시 이름이다.
- 세 판에서 출력이 같았던 것은 **관찰**이다. 보장은 에러 메시지가 명시한 버전 경계 쪽에만 있다.
