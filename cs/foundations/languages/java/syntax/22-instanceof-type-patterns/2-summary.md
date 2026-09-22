# java/syntax/22 — `instanceof` 타입 패턴 (16+) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — 이 주제는 javadoc 이 아니라 **javac 자신**이 기준이다.\
> 규칙 전부를 `javac` 의 실제 에러 메시지와 `javap -c -p` 출력으로 접지했다.\
> JLS 본문은 열지 않았고, 인용한 JLS 절 번호도 없다.
> **실행 검증** — 이 문서의 모든 출력·에러 메시지는 Temurin JDK 에서 실제로 돌려 얻은 것이다.\
> 프로그램 4개 + 컴파일 에러용 10개. `javac` 28회 · `java` 14회 · `javap` 1회.\
> 도는 프로그램은 **17.0.13 · 21.0.5 · 25.0.1 셋 다**에서 돌렸다.\
> ★ **한 자리가 17 과 21 에서 갈렸다**(무조건 패턴) — 그 자리를 따로 표시했다.\
> 버전 갈림(`--release 15` / `16`)은 JDK 21 의 `javac --release` 로 찍었다.
> **버전** — `instanceof` 타입 패턴은 **Java 16** 정식(14·15 프리뷰).\
> ★ 다만 **같은 타입을 패턴으로 받는 것**(`String s0` 에 `s0 instanceof String s`)은 **21 부터** 허용된다.\
> 17 에서는 컴파일 에러다 — **돌려 확인했다.** "16부터"를 외울 때 이 예외를 같이 외운다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**타입 패턴은 「검사하면서 이름표를 붙이는 것」이다.**

옛 코드는 같은 타입을 **세 번** 적었다 — 검사에서 한 번, 캐스트에서 한 번, 선언에서 한 번.\
타입 패턴은 **한 번만** 적는다. 그리고 여기서 이 주제의 진짜 내용이 시작된다 —\
**그 이름표가 어디서부터 어디까지 보이느냐**가 `if` 의 **모양**에 따라 달라진다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 짐을 열어 "이건 책이다" 하고 확인 | `o instanceof String` — 타입 검사 |
| 확인하면서 **이름표를 붙임** | `o instanceof String s` — 패턴 변수 `s` |
| 이름표가 **읽히는 구역** | 패턴 변수의 스코프 |
| "책이라고 확인된 쪽" 통로 | 조건이 **참**인 경로 (`true` 구역) |
| "책이 아니라고 확인된 쪽" 통로 | 조건이 **거짓**인 경로 (`false` 구역) |
| 아니면 돌려보내고 나머지는 전부 책 | `if (!(o instanceof String s)) return;` |
| 이름표를 못 읽는 자리에서 부르면 | `cannot find symbol: variable s` |

```text
옛 코드 — 타입을 세 번 적는다             타입 패턴 — 한 번 적는다
+-------------------------------+       +-------------------------------+
| if (o instanceof String) {    |       | if (o instanceof String s) {  |
|     String s = (String) o;    |       |                               |
|     return s.length();        |       |     return s.length();        |
| }                             |       | }                             |
+-------------------------------+       +-------------------------------+
  String 이 3번                           String 이 1번
  캐스트가 검사와 따로 논다                검사와 캐스트가 한 덩어리다
```

**똑같은 구조로** Java 가 이렇게 동작한다 — 그런데 놀랍게도 **바이트코드는 한 글자도 같다.**\
타입 패턴은 **런타임 기능이 아니라 소스 표면의 규칙**이고, 그 규칙의 본체가 **스코프**다.

실무에서 이게 값을 내는 자리는 **`equals` 구현**과 **가드 절**(guard clause)이다.\
둘 다 "아니면 나가고 나머지는 전부 그 타입" 이라는 모양이고, 타입 패턴이 그 모양에 정확히 맞는다.

> **타입 패턴(type pattern)** — `String s` 처럼 **타입 하나와 변수 이름 하나**로 된 패턴.\
> 예: `o instanceof String s` 는 "`o` 가 `String` 이면 그 값을 `s` 라고 부른다"는 뜻이다.

> **패턴 변수(pattern variable)** — 패턴이 매칭됐을 때 만들어지는 변수. 위의 `s`.

> **흐름 스코프(flow scoping)** — 변수가 보이는 범위를 **중괄호가 아니라 프로그램의 흐름**으로 정하는 것.\
> 예: `if (!(o instanceof String s)) return;` 다음 줄에서 `s` 가 보인다 — 중괄호는 거기 없는데도.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 과녁으로 둔다.

1. 타입 패턴이 캐스트를 없앴다는 것은 **런타임에도 무언가 달라진 것**인가.
2. ★ 패턴 변수는 **어디서 보이고 어디서 안 보이는가** — `!`·`&&`·`||` 에서 각각 어떻게 갈리는가.
3. 못 쓰는 자리는 어디인가 — 제네릭·`var`·같은 타입에서 각각 무엇이 막히는가.

## 동작 방식

### (1) ★ 바이트코드는 **한 글자도 같다**

**언제 쓰나** — "타입 패턴이 캐스트를 없앴다"가 성능 이야기인지 판단할 때.

`Ex.java (22-a)` — 같은 일을 옛 방식과 패턴으로 각각 쓴다.

```java
// 옛 형태 — 타입을 세 번 적는다
static String oldWay(Object o) {
    if (o instanceof String) {
        String s = (String) o;
        return "문자열 길이 " + s.length();
    }
    return "그 밖";
}

// 타입 패턴 — 한 번만 적는다
static String newWay(Object o) {
    if (o instanceof String s) {
        return "문자열 길이 " + s.length();
    }
    return "그 밖";
}
```

`javap -c -p Ex.class` (JDK 21.0.5) 로 두 메서드를 나란히 본다.

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
```

```text
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

그림 해설 (한 단계씩):

- ★ **오프셋부터 상수 풀 번호까지 완전히 같다.** 두 메서드는 구별할 수 없다.
- `instanceof` 로 검사하고(오프셋 1), `checkcast` 로 변환하고(8), 지역 변수에 넣는다(11).\
  **캐스트는 사라지지 않았다.** 소스에서 안 보일 뿐이다.
- 그러므로 **타입 패턴은 성능 기능이 아니다.** 소스에서 중복을 없애고,\
  그 대가로 **스코프 규칙 하나를 새로 배워야 하는** 기능이다.
- ★ 그리고 이 점이 [**23번 주제**](../23-switch-pattern-matching/)와 갈린다 —\
  거기서는 `invokedynamic typeSwitch` 라는 **새 런타임 장치**가 실제로 들어온다.

**비용** — 없다. 런타임 비용도 클래스 파일 크기도 같다.\
비용은 **읽는 사람이 흐름 스코프를 알아야 한다**는 것뿐이다.

### (2) ★ 스코프 — 이름표가 읽히는 구역

**언제 쓰나** — 이 주제의 본체다. `s` 를 어디서 쓸 수 있는지 판단할 때 매번.

규칙은 하나다.

> **패턴 변수는 「패턴이 확실히 매칭됐다」고 컴파일러가 아는 구역에서만 보인다.**

그 구역을 **`true` 구역**과 **`false` 구역**으로 나눠 읽으면 전부 설명된다.

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

이제 문장 모양별로 그 구역이 **어디에 놓이는지**만 보면 된다.

```text
[A] 그냥 if
    if (o instanceof String s) {
        ####################              <- true 구역: s 보임
    } else {
        ..................                <- false 구역: s 안 보임
    }
    ......................                <- 뒤: s 안 보임 (둘 중 어느 쪽인지 모른다)


[B] 부정 + 빠져나감  ★ 이것이 이 주제의 핵심 형태
    if (!(o instanceof String s)) return;
        ^^^^^^^^^^^^^^^^^^^^^^^^  true 구역 = "매칭 안 됨" -> 여기서 나간다
    ######################################  <- 나가지 않은 경로 = 매칭됨 -> s 보임
    ######################################     메서드 끝까지 보인다


[C] && 의 오른쪽
    if (o instanceof String s && s.length() > 3) { ###### }
                              ^^^^^^^^^^^^^^^^   왼쪽이 참이어야 평가된다
                              #### s 보임              -> true 구역


[D] || 의 오른쪽 — 부정했을 때만
    if (!(o instanceof String s) || s.isEmpty()) { ... }
                                    ^^^^^^^^^^  왼쪽이 거짓이어야 평가된다
                                    #### s 보임      = !(매칭 안 됨) = 매칭됨


[E] || 의 오른쪽 — 부정 안 했으면 안 보인다
    if (o instanceof String s || s.isEmpty()) { ... }
                                 ^^^^^^^^^^  왼쪽이 거짓이어야 평가된다
                                 XXXX 안 보임     = 매칭 안 됨
                                                 -> cannot find symbol


[F] while 의 조건에서 부정
    while (!(q.peek() instanceof String s)) { ... }
    ######################################  <- 루프를 빠져나오면 조건이 거짓
                                               = 매칭됨 -> s 보임
```

`Ex.java (22-a)` 로 [A]~[E] 를, `Ex.java (22-b)` 로 [F] 를 돌렸다.

```java
static String andScope(Object o) {
    if (o instanceof String s && s.length() > 3) return "긴 문자열 " + s;
    return "그 밖";
}

static String earlyReturn(Object o) {
    if (!(o instanceof String s)) return "문자열이 아니다";
    return "문자열 " + s.toUpperCase();   // 여기서 s 가 보인다
}

static String orScope(Object o) {
    if (!(o instanceof String s) || s.isEmpty()) return "문자열이 아니거나 비었다";
    return "내용 있는 문자열 " + s;
}
```

**실행 결과** (JDK 21.0.5 — 17.0.13 · 25.0.1 에서도 같았다)

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

- `earlyReturn` 이 [B] 다 — **`return` 뒤부터 메서드 끝까지** `s` 가 산다.
- ★ **`else` 가 없는데도** `s` 가 보인다. 중괄호가 스코프를 정하지 않는다는 뜻이다.
- `orScope` 가 [D] 다 — `!` 가 있어야 `||` 의 오른쪽에서 보인다.
- **`null` 은 어떤 타입 패턴에도 안 맞는다.** 마지막 행이 그것이다 — `oldWay` 와 같은 결과다.\
  `instanceof` 가 `null` 에 `false` 인 옛 규칙 그대로다.

**기억하는 법** — 문장 모양을 외우지 말고 **한 문장**만 붙든다.

> **"그 줄에 도달했다는 사실이 「매칭됐다」를 함의하면 보인다."**

**비용** — 없다. 다만 [E] 를 만나면 헤매기 쉽다 — 에러가 `cannot find symbol` 이라\
**스코프 문제가 아니라 오타처럼 보인다.**

### (3) 패턴 변수는 `final` 이 아니다 — 그리고 `final` 을 붙일 수도 있다

**언제 쓰나** — "패턴 변수를 다시 대입해도 되나"를 따질 때.

`Ex.java (22-b)`

```java
// 패턴 변수는 final 이 아니다 — 다시 대입할 수 있다
static String reassign(Object o) {
    if (o instanceof String s) {
        s = s + "!";
        return s;
    }
    return "그 밖";
}

// final 수식어를 붙일 수 있다
static String withFinal(Object o) {
    if (o instanceof final String s) return "final 패턴 " + s;
    return "그 밖";
}
```

**실행 결과** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
reassign("ab")   = ab!
withFinal("ab")  = final 패턴 ab
```

- 기본은 **`final` 이 아니다.** 보통의 지역 변수와 같다.
- `final` 을 붙이면 다시 대입할 수 없게 된다. 람다에서 캡처할 때도 안전해진다.
- ★ 실무 권고: **대입하지 마라.** `s` 는 "검사에 통과한 그 값"이라는 뜻인데,\
  다른 값을 넣으면 그 의미가 깨진다. 읽는 사람이 `s` 를 원본으로 믿는다.

**비용** — 없다. `final` 은 클래스 파일에 흔적도 남기지 않는다.

### (4) 패턴 둘을 잇는다 — `&&` 만 된다

**언제 쓰나** — 인자 둘을 동시에 좁힐 때.

`Ex.java (22-b)`

```java
static String twoPatterns(Object a, Object b) {
    if (a instanceof Integer x && b instanceof Integer y) return "합 " + (x + y);
    return "정수 둘이 아니다";
}

static String ternary(Object o) {
    return o instanceof String s ? "문자열(" + s.length() + ")" : "그 밖";
}
```

**실행 결과** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
twoPatterns(1,2) = 합 3
twoPatterns(1,"")= 정수 둘이 아니다
ternary("abc")   = 문자열(3)
ternary(42)      = 그 밖
```

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

- `&&` 는 **왼쪽이 참일 때만 오른쪽을 평가**한다. 그래서 오른쪽은 이미 `true` 구역이다.
- **조건 연산자(`? :`)** 에서도 같다 — 조건이 참인 쪽 가지가 `true` 구역이다.
- ★ `||` 로는 **패턴 둘을 이을 수 없다** — 돌려 확인했다(`Ex.java (22-e8)`).

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

  **둘 다 안 보인다** — 어느 쪽이 참이었는지 모르기 때문이다. 에러도 둘이다.

**비용** — 없다.

### (5) 가장 많이 쓰이는 자리 — `equals`

**언제 쓰나** — `equals` 를 손으로 구현할 때. 이 주제의 실무 용례 1위다.

`Ex.java (22-b)`

```java
record Point(int x, int y) {
    @Override public boolean equals(Object o) {
        return o instanceof Point p && p.x == x && p.y == y;
    }
    @Override public int hashCode() { return x * 31 + y; }
}
```

**실행 결과** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
Point equals     = true
```

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
    null 검사가 instanceof 에 숨어 있다      같다 (instanceof 는 null 에 false)
```

- `null` 이 들어와도 `instanceof` 가 `false` 이므로 **따로 검사할 필요가 없다.** 옛 형태도 같았다.
- `equals` 의 **계약** 자체(대칭성·추이성 등)는 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/)가 정본이다.\
  여기서는 **그 구현이 타입 패턴으로 짧아지는 자리**만 본다.
- `record` 는 `equals` 를 자동으로 만들어 준다([`../14-records/`](../14-records/)). 위 코드는 **형태를 보이려고** 직접 쓴 것이다.

**비용** — 없다. (1)에서 봤듯 바이트코드가 같다.

### (6) 반복문에서의 스코프 — 루프를 나온 뒤에 보인다

**언제 쓰나** — "조건에 맞는 첫 원소를 찾을 때까지 버린다" 형태를 쓸 때.

`Ex.java (22-b)`

```java
static String loopScope(Deque<Object> q) {
    while (!(q.peek() instanceof String s)) {
        if (q.isEmpty()) return "문자열이 없다";
        q.poll();
    }
    return "첫 문자열 = " + s;            // 루프를 빠져나오면 s 가 보인다
}
```

**실행 결과** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
loopScope        = 첫 문자열 = 여기
```

```text
  while (!(q.peek() instanceof String s)) {
      ....................                  <- 루프 본문: 조건이 참 = 매칭 안 됨 -> s 안 보임
  }
  ########################                  <- 루프 탈출: 조건이 거짓 = 매칭됨 -> s 보임
```

- [B] 와 같은 구조다 — **"빠져나왔다는 사실이 매칭을 함의한다."**
- 루프 **안**에서는 `s` 가 안 보인다. 안에서는 매칭이 안 된 상태이기 때문이다.
- ★ 이 형태는 **무한 루프를 조심해야 한다.** 위 코드의 `if (q.isEmpty()) return` 이 그 방어다.\
  조건이 계속 참이면 루프가 안 끝난다.

**비용** — 없다. 다만 읽기 어려운 편이므로 **간단한 경우에만** 쓴다.\
대부분은 [B] 형태(메서드 앞머리의 가드)가 더 읽기 쉽다.

## 문법 — 형태와 규칙

### 선언 형태

```java
// 기본
if (o instanceof String s) { ... }

// final 을 붙일 수 있다
if (o instanceof final String s) { ... }

// 부정 + 빠져나감 (가드 절)
if (!(o instanceof String s)) return;
// 여기서부터 s

// && 로 조건을 더 붙인다
if (o instanceof String s && !s.isBlank()) { ... }

// 조건 연산자
String r = o instanceof String s ? s.strip() : "";
```

### 규칙 불릿

- **`null` 은 어떤 타입 패턴에도 안 맞는다.** `null instanceof String s` 는 `false` 다.
- 패턴 변수는 **`final` 이 아니다.** `final` 을 명시할 수는 있다.
- 패턴 변수의 이름은 **그 스코프에 이미 있는 지역 변수와 겹칠 수 없다.**
- **제네릭 타입 인자를 쓸 수 없다** — `o instanceof List<String> l` 은 에러다.\
  **`o instanceof List<?> l` 은 된다** — 돌려 확인했다(`Ex.java (22-c)`, 17 · 21 · 25 동일).

```text
wildcard(List.of("a","b")) = 리스트 크기 2 첫 원소 = a
wildcard(42)                = 그 밖
```

- **`var` 를 쓸 수 없다** — `o instanceof var v` 는 에러다.
- **애초에 불가능한 변환은 컴파일 에러**다 — `String` 을 `Integer` 패턴으로 받을 수 없다.
- ★ **같은 타입(또는 상위 타입)을 패턴으로 받는 것**은 **21 부터** 허용된다. 17 에서는 에러다.

### 스코프 판정표 — 이 표 하나로 전부 결정된다

| 자리 | `s` 가 보이나 | 왜 |
|---|---|---|
| `if (o instanceof String s)` 의 **본문** | **보인다** | 도달 = 매칭됨 |
| 그 `if` 의 **`else`** | 안 보인다 | 도달 = 매칭 안 됨 |
| 그 `if` **뒤** | 안 보인다 | 둘 중 어느 쪽인지 모른다 |
| `if (!(o instanceof String s)) return;` **뒤** | **보인다** | 안 나갔다 = 매칭됨 |
| `if (!(o instanceof String s)) { ... }` 의 **본문** | 안 보인다 | 도달 = 매칭 안 됨 |
| `o instanceof String s && ???` 의 **`???`** | **보인다** | `&&` 의 오른쪽 = 왼쪽이 참 |
| `o instanceof String s \|\| ???` 의 **`???`** | 안 보인다 | `\|\|` 의 오른쪽 = 왼쪽이 거짓 |
| `!(o instanceof String s) \|\| ???` 의 **`???`** | **보인다** | 왼쪽이 거짓 = 매칭됨 |
| `while (!(... instanceof String s))` **뒤** | **보인다** | 탈출 = 조건 거짓 = 매칭됨 |
| 그 `while` 의 **본문** | 안 보인다 | 도달 = 매칭 안 됨 |
| `cond ? A : B` 의 **`A`** (cond 에 패턴) | **보인다** | 조건이 참인 가지 |

## 어디서 틀리나

★ 이 주제의 값은 대부분 여기 있다. **아래 에러 메시지는 전부 JDK 21.0.5 의 javac 실출력이다.**

### 1. `||` 의 오른쪽에서 패턴 변수를 썼다

`Ex.java (22-e1)`

```java
static String f(Object o) {
    if (o instanceof String s || s.isEmpty()) return "?";
    return "그 밖";
}
```

```text
Ex.java:3: error: cannot find symbol
        if (o instanceof String s || s.isEmpty()) return "?";
                                     ^
  symbol:   variable s
  location: class Ex
1 error
```

- ★ **에러 메시지가 스코프를 말해 주지 않는다.** `cannot find symbol` 은 오타일 때와 똑같은 문구다.
- 실제 이유는 **`||` 의 오른쪽은 왼쪽이 거짓일 때 평가되고, 그때 `s` 는 안 만들어졌기** 때문이다.
- 고치는 법: `!(o instanceof String s) || s.isEmpty()` — 부정하면 통한다.\
  단 **의미가 뒤집히므로** 정말 그 뜻이 맞는지 확인한다.

### 2. `if` 밖에서 패턴 변수를 썼다

`Ex.java (22-e2)`

```java
static String f(Object o) {
    if (o instanceof String s) { }
    return s.toUpperCase();
}
```

```text
Ex.java:4: error: cannot find symbol
        return s.toUpperCase();
               ^
  symbol:   variable s
  location: class Ex
1 error
```

- `if` 를 빠져나오면 **매칭됐는지 아닌지 모른다.** 그래서 `s` 가 없다.
- ★ **`!` 를 붙이고 `return` 하면 반대가 된다** — 「동작 방식」 (2) 의 [B].\
  `if (!(o instanceof String s)) return "?";` 뒤에서는 `s` 가 보인다.
- 1번과 **에러 문구가 같다.** 이 문구를 보면 먼저 **스코프 판정표**를 떠올린다.

### 3. 이미 있는 이름을 패턴 변수로 썼다

`Ex.java (22-e3)`

```java
static String f(Object o) {
    String s = "바깥";
    if (o instanceof String s) return s;
    return "그 밖";
}
```

```text
Ex.java:4: error: variable s is already defined in method f(Object)
        if (o instanceof String s) return s;
                                ^
1 error
```

- 패턴 변수는 **지역 변수와 같은 이름 공간**을 쓴다. 안쪽 블록이라고 가려 주지 않는다.
- 메시지가 다르다는 점이 중요하다 — 1·2번의 `cannot find symbol` 과 달리 **`already defined`** 다.

### 4. 제네릭 타입 인자를 썼다

`Ex.java (22-e4)`

```java
static String f(Object o) {
    if (o instanceof List<String> l) return "문자열 리스트 " + l.size();
    return "그 밖";
}
```

```text
Ex.java:4: error: Object cannot be safely cast to List<String>
        if (o instanceof List<String> l) return "문자열 리스트 " + l.size();
            ^
1 error
```

- 타입 인자는 **런타임에 없다**(타입 소거). 검사할 수가 없다.
- 메시지의 `cannot be safely cast` 가 그 이유를 말한다 — 안전하게 검사할 방법이 없다는 뜻이다.
- **`List<?> l` 은 된다.** 와일드카드는 검사할 것이 없기 때문이다.
- 타입 소거의 정본은 [**19번 주제**](../19-type-erasure/)다.

### 5. 애초에 불가능한 타입을 썼다

`Ex.java (22-e5)`

```java
static String f(String s) {
    if (s instanceof Integer i) return "정수 " + i;
    return "그 밖";
}
```

```text
Ex.java:3: error: incompatible types: String cannot be converted to Integer
        if (s instanceof Integer i) return "정수 " + i;
            ^
1 error
```

- `String` 과 `Integer` 는 **서로 상속 관계가 아니다.** 어떤 값도 둘 다일 수 없다.
- 이것은 패턴 때문이 아니라 **`instanceof` 의 옛 규칙**이다. 패턴 없이 써도 같은 에러가 난다 — 돌려 확인했다(`Ex.java (22-e9)`).

```text
Ex.java:3: error: incompatible types: String cannot be converted to Integer
        return s instanceof Integer;      // 패턴 없이 같은 조합
               ^
1 error
```

- 그래서 `instanceof` 는 **항상 거짓인 검사**를 컴파일 시점에 잡아 준다.

### 6. `var` 를 썼다

`Ex.java (22-e6)`

```java
if (o instanceof var v) return "" + v;
```

```text
Ex.java:3: error: 'var' is not allowed here
        if (o instanceof var v) return "" + v;
                         ^
1 error
```

- 타입 패턴의 **본질은 타입 검사**다. `var` 를 쓰면 무엇을 검사할지가 없다.
- ★ 다만 **`record` 패턴의 컴포넌트에는 `var` 를 쓸 수 있다** — 거기서는 컴포넌트 선언이 타입을 알려 주기 때문이다.\
  그쪽은 [**24번 주제**](../24-record-patterns/)가 정본이다.

### 7. ★ 같은 타입을 패턴으로 받았다 — **17 과 21 이 갈린다**

`Ex.java (22-e7)`

```java
static int sameType(String s0) {
    if (s0 instanceof String s) return s.length();   // 이미 String 인데 String 패턴
    return -1;
}
```

**JDK 17.0.13**

```text
Ex.java:3: error: expression type String is a subtype of pattern type String
        if (s0 instanceof String s) return s.length();   // 이미 String 인데 String 패턴
               ^
1 error
```

**JDK 21.0.5 · 25.0.1**

```text
sameType("abcd") = 4
null 이면          = -1
```

- ★ **같은 소스가 17 에서는 에러이고 21 에서는 통과한다.** 세 판에서 돌려 확인했다.
- 17 은 "항상 참인 패턴은 쓸 이유가 없다"며 막았다. 21 에서 그 제한이 풀렸다.
- 21 에서 통과해도 **`null` 이면 여전히 안 맞는다** — 위 실행의 둘째 줄(`-1`)이 그것이다.\
  "항상 참"이 아니라 **"`null` 만 빼고 항상 참"** 이다. 이 구별이 [**23번 주제**](../23-switch-pattern-matching/)의 `null` 규칙과 이어진다.
- 실무 함의: **21 로 쓴 코드를 17 로 되돌리면 이 자리가 깨진다.** 반대 방향은 안전하다.

### 8. 16 미만에서 쓰려 했다

JDK 21 의 `javac --release 15` (같은 `Ex.java (22-a)`)

```text
Ex.java:13: error: pattern matching in instanceof is not supported in -source 15
        if (o instanceof String s) {
                                ^
  (use -source 16 or higher to enable pattern matching in instanceof)
1 error
```

`--release 16` 은 통과했다.

- 메시지가 **정확한 버전**을 알려 준다 — `use -source 16 or higher`.
- 그래서 "타입 패턴은 16부터"는 **이 에러 메시지에 근거한 사실**이다.
- 단 7번의 예외(같은 타입 패턴은 21부터)를 같이 기억한다.

### 9. `null` 을 특별 취급할 줄 알았다

```text
null    oldWay=그 밖            newWay=그 밖            andScope=그 밖
        earlyReturn=문자열이 아니다           orScope=문자열이 아니거나 비었다
```

- `null` 은 **어떤 타입 패턴에도 안 맞는다.** `oldWay` 와 결과가 같다.
- 그래서 `if (!(o instanceof String s)) return "?";` 는 **`null` 도 같이 걸러 준다.**\
  이것이 `equals` 에서 `null` 검사를 따로 안 써도 되는 이유다.
- ★ **`switch` 에서는 이야기가 달라진다.** `case null` 이 생기면서 규칙이 갈린다 —\
  [**23번 주제**](../23-switch-pattern-matching/)가 정본이다. 여기서는 **"타입 패턴은 `null` 에 안 맞는다"** 만 외운다.

## 구현 세부사항 대 언어 보장

이 주제는 **런타임에 새로 생긴 것이 없어서** 경계가 단순하다. 대신 **버전 경계**가 둘이다.

| 무엇 | 어디에 속하나 | 근거 |
|---|---|---|
| 타입 패턴이 Java 16 부터 | **언어 보장** | `--release 15` 에러 `(use -source 16 or higher)` |
| ★ 같은 타입 패턴이 21 부터 | **언어 보장** | 17 에서 `expression type String is a subtype of pattern type String` |
| `null` 이 타입 패턴에 안 맞는 것 | **언어 보장** | `instanceof` 의 옛 규칙. 실행으로 확인 |
| 흐름 스코프 규칙(`true`/`false` 구역) | **언어 보장** | javac 가 `cannot find symbol` 로 거부 |
| 패턴 변수가 `final` 이 아닌 것 | **언어 보장** | 재대입이 컴파일된다 |
| 제네릭 타입 인자 금지 | **언어 보장** | `Object cannot be safely cast to List<String>` |
| `var` 금지 | **언어 보장** | `'var' is not allowed here` |
| 같은 이름 금지 | **언어 보장** | `variable s is already defined` |
| ★ **바이트코드가 옛 형태와 같다** | **구현 세부** | javac 21 의 코드 생성. 명세가 요구하는 것이 아니다 |
| `checkcast` 가 쓰인다는 것 | **구현 세부** | 같은 이유 |
| 에러 메시지의 **문구 자체** | **구현 세부** | javac 의 것이다 |

### "설탕"이라는 말의 정확한 뜻

```text
  소스 표면                                런타임
  +-----------------------------+         +-----------------------------+
  | 타입을 1번만 적는다          |         | instanceof + checkcast      |
  | 스코프 규칙이 새로 생겼다     |   ->    | (옛 형태와 완전히 같다)      |
  | 컴파일 에러가 새로 생겼다     |         |                             |
  +-----------------------------+         +-----------------------------+
    여기에 전부 있다                        여기에는 아무것도 없다
```

- **"문법 설탕"이라 부르는 것은 런타임 쪽에서만 맞다.** 소스 쪽에서는 **새 규칙이 하나 늘었다.**
- 그래서 이 주제의 학습 비용은 **문법이 아니라 스코프**에 있다. 실수도 거기서만 난다.

## 언제 쓰고 언제 안 쓰나

**쓴다**

- **`equals` 구현** — `o instanceof Point p && ...` 한 문장으로 끝난다. 1위 용례다.
- **가드 절** — `if (!(o instanceof X x)) return;` 뒤로 본문이 평평해진다.\
  들여쓰기가 한 단계 줄고, 나머지 코드가 전부 "`X` 인 경우"가 된다.
- **`Object` 를 받는 메서드**(직렬화·리플렉션 경계·프레임워크 콜백)에서 타입을 좁힐 때.
- **`&&` 로 조건을 이어 붙일 때** — 타입 검사와 값 검사를 한 줄로 쓴다.

**안 쓴다**

- **`instanceof` 사슬이 셋을 넘을 때** — 그것은 `switch` 패턴 매칭의 자리다([**23번 주제**](../23-switch-pattern-matching/)).\
  사슬은 **빠뜨려도 컴파일러가 모른다**는 약점이 있다.
- **타입으로 분기하는 설계 자체가 냄새일 때** — 다형성으로 풀리는지 먼저 본다.\
  `sealed` 계층이면 `switch` 가, 열린 계층이면 메서드 재정의가 맞다.
- **컴포넌트를 꺼내야 할 때** — `record` 면 [**24번 주제**](../24-record-patterns/)의 `record` 패턴이 더 짧다.

**중간 지대**

- 패턴 변수 이름은 **짧게**(`s`·`p`·`x`) 쓰는 관례가 자리잡았다.\
  스코프가 좁고, 타입이 바로 옆에 적혀 있기 때문이다. 길게 쓰면 오히려 읽기 나빠진다.

## 핵심 문장

1. 타입 패턴은 **소스에서 타입을 세 번 적던 것을 한 번으로** 줄인다.
2. ★ **바이트코드는 옛 형태와 한 글자도 같다** — 성능 기능이 아니다. 얻는 것은 정확성과 짧음이다.
3. 이 주제의 본체는 **흐름 스코프**다. 중괄호가 아니라 **흐름**이 변수의 수명을 정한다.
4. 규칙 한 문장: **"그 줄에 도달했다는 사실이 「매칭됐다」를 함의하면 보인다."**
5. `&&` 의 오른쪽에서는 보이고, `||` 의 오른쪽에서는 **부정했을 때만** 보인다.
6. ★ `if (!(o instanceof X x)) return;` 뒤로 `x` 가 **메서드 끝까지** 산다 — `else` 없이.
7. 스코프를 어기면 에러가 **`cannot find symbol`** 이다 — 오타와 구별이 안 되니 판정표를 먼저 떠올린다.
8. `null` 은 어떤 타입 패턴에도 안 맞는다. 그래서 `equals` 에서 `null` 검사가 따로 필요 없다.
9. 타입 패턴은 **16** 부터. ★ 단 **같은 타입을 패턴으로 받는 것은 21** 부터다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 22번)
- [`../../../../../../history/java/java-16.md`](../../../../../../history/java/java-16.md) — **언제·왜 들어왔나**(JEP 394 확정, 두 번의 프리뷰).\
  여기는 **어떻게 쓰고 무엇을 못 하나**만 다룬다
- [`../../../../../../history/java/java-21.md`](../../../../../../history/java/java-21.md) — 같은 타입 패턴 제한이 풀린 판. **연혁은 거기**
- [`../09-inheritance-overriding/`](../09-inheritance-overriding/) — **이 주제의 선행.**\
  거기는 **"메서드는 재정의되고 필드는 숨겨진다"는 디스패치 규칙**이 정본.\
  여기는 **디스패치를 쓰지 않고 타입을 직접 묻는 쪽**이다 — 둘은 같은 문제의 반대 해법이다
- [**20번 주제**](../20-control-flow-statements/)(제어문) — `if`·`while` 의 흐름 자체. **여기는 그 조건이 변수를 만드는 것**부터
- [**21번 주제**](../21-switch-statement-and-expression/)(`switch` 문과 식) — 값으로 분기하는 것. **타입으로 분기하는 것은 여기**
- [**23번 주제**](../23-switch-pattern-matching/)(`switch` 패턴 매칭, 21) — **`instanceof` 사슬이 셋을 넘을 때의 자리.**\
  `case null`·`when` 가드·지배 관계·완결성이 전부 거기다. 여기는 **`if` 하나짜리**까지
- [**24번 주제**](../24-record-patterns/)(`record` 패턴, 21) — 타입 패턴 안에서 컴포넌트를 꺼내는 것.\
  **`var` 가 쓰이는 유일한 패턴 자리**도 거기다
- [`../14-records/`](../14-records/) — `record` 가 `equals` 를 만들어 주는 것. **계약 구현은 거기**
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — **`equals` 계약이 정본.**\
  여기는 **그 구현이 타입 패턴으로 짧아지는 자리**만
- [**19번 주제**](../19-type-erasure/)(타입 소거) — **제네릭 타입 인자를 `instanceof` 에 못 쓰는 이유가 정본.**\
  여기는 **그 에러 메시지**까지
- [**04번 주제**](../04-var-type-inference/)(`var`) — `var` 의 규칙. **여기는 "패턴에는 못 쓴다"까지**
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — JIT·GC·메모리 모델. **이 주제와 겹치지 않는다**

## 용어 풀이

- **타입 패턴(type pattern)** — `String s` 처럼 타입 하나와 변수 이름 하나로 된 패턴. Java 16.
- **패턴 변수(pattern variable)** — 패턴이 매칭됐을 때 만들어지는 변수.
- **흐름 스코프(flow scoping)** — 변수가 보이는 범위를 중괄호가 아니라 **프로그램 흐름**으로 정하는 것.
- **`true` 구역 / `false` 구역** — 조건이 참/거짓으로 확정된 경로. 패턴 변수는 `true` 구역에서만 산다.
- **가드 절(guard clause)** — 메서드 앞머리에서 예외 경우를 먼저 `return` 으로 걸러 내는 형태.
- **`instanceof`** — 참조가 그 타입인지 묻는 연산자. **`null` 에는 항상 `false`.** Java 1.0.
- **`checkcast`** — 참조를 그 타입으로 변환하는 JVM 명령. 아니면 `ClassCastException`.
- **무조건 패턴(unconditional pattern)** — 그 타입의 모든 값에 맞는 패턴(`String` 에 대한 `String s`).\
  ★ `instanceof` 에서는 **21 부터** 허용된다. `null` 에는 여전히 안 맞는다.
- **타입 소거(type erasure)** — 제네릭 타입 인자가 런타임에 사라지는 것. 정본은 [**19번 주제**](../19-type-erasure/).
- **문법 설탕(syntactic sugar)** — 새 런타임 기능 없이 소스만 짧아지는 문법.\
  이 주제는 **런타임 쪽에서만** 그렇다 — 소스 쪽에는 새 스코프 규칙이 생겼다.

## 더 들어가면

- **흐름 스코프는 `definite assignment` 분석의 확장이다.**\
  javac 는 원래 "이 변수가 이 지점에서 확실히 대입됐나"를 추적하고 있었다.\
  패턴 변수는 그 기계 장치에 **"이 지점에서 확실히 매칭됐나"** 를 하나 더 얹은 것이다.\
  그래서 `&&`·`||`·`!` 의 단락 평가 규칙이 그대로 따라온다 — **새로 만든 규칙이 아니다.**
- **`if (!(o instanceof X x)) return;` 형태가 읽기 좋은 이유는 들여쓰기 때문만이 아니다.**\
  이 형태는 **"이 메서드의 나머지 전부는 `X` 를 다룬다"** 를 첫 줄에서 선언한다.\
  본문 어디서도 "지금 타입이 뭐였지"를 되짚을 필요가 없다.
- **`instanceof` 사슬의 약점은 "빠뜨려도 조용하다"는 것이다.**\
  `Ex.java (23-a)` 에서 실제로 확인했다 — 세 갈래 중 둘만 적은 `if` 사슬은 아무 말 없이 잘못된 값을 냈다.

  ```text
  Rect[w=2.0, h=3.0]   name=직사각형   ifElse=빠뜨린 것이 여기로 온다
  ```

  같은 분기를 `sealed` + `switch` 로 쓰면 **컴파일이 멈춘다.** 그 거래가 [**23번 주제**](../23-switch-pattern-matching/)의 내용이다.
- **패턴 변수를 `final` 로 쓰는 습관**을 들이면 람다·익명 클래스에서 캡처할 때 고민이 없다.\
  다만 코드가 길어지므로, **대입하지 않는다는 관례**로 대신하는 팀이 더 많다.
- **`o instanceof List<?> l` 은 되지만 `List<String>` 은 안 된다**는 비대칭은\
  "런타임에 무엇이 남아 있나"로 갈린다. `List` 라는 사실은 남고 `String` 이라는 사실은 사라진다.\
  그래서 `List<?>` 로 받은 뒤 원소를 꺼내면 **`String` 에 바로 못 넣는다** — 돌려 확인했다(`Ex.java (22-e10)`).

  ```text
  Ex.java:6: error: incompatible types: CAP#1 cannot be converted to String
              String first = l.get(0);      // Object 를 String 에 바로 넣어 본다
                                  ^
    where CAP#1 is a fresh type-variable:
      CAP#1 extends Object from capture of ?
  1 error
  ```

  타입이 `Object` 라고 적히지도 않는다 — **`?` 를 포착한 익명 타입 변수(`CAP#1`)** 다.\
  그 메커니즘의 정본은 [**19번 주제**](../19-type-erasure/)다 — 여기서는 **에러 메시지가 그 경계를 가리킨다**는 것까지만.
