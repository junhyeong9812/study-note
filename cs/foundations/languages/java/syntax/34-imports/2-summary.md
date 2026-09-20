# java/syntax/34 — `import`·static import·(25) 모듈 import 선언 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §7.5 Import Declarations](https://docs.oracle.com/javase/specs/jls/se21/html/jls-7.html) · [§6.4.1 Shadowing](https://docs.oracle.com/javase/specs/jls/se21/html/jls-6.html) · [JEP 511: Module Import Declarations](https://openjdk.org/jeps/511).
> **실행 검증** — 이 문서의 모든 출력·에러는 실제로 돌려 얻은 것이다.\
> 일반 `import` 는 Temurin **JDK 21.0.5**, **모듈 import 선언은 JDK 25.0.1** 에서 돌렸다.\
> **21 에서 나는 에러와 25 에서 나는 결과를 둘 다 실었다**(「동작 방식 (5)」).\
> 프로그램 9개를 돌렸고, `javap -c`·`javap -l`·`javap -v`·`cmp` 로 클래스 파일을 대조했다.
> **버전** — 단일 타입/온디맨드 `import` 는 **1.0**, `static import` 는 **5**,
> **모듈 import 선언은 25 정식(JEP 511)** 이다. 23 에서 1차 preview(JEP 476), 24 에서 2차(JEP 494)를 거쳤다.\
> 정식인지 프리뷰인지는 기억이 아니라 **직접 확인했다** — JDK 25 에서 `--enable-preview` 없이 컴파일·실행이 됐고,
> `javac -Xlint:preview` 도 경고를 내지 않았다(「동작 방식 (5)」).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> 선행 없음. 이어지는 주제: [58 리플렉션](../58-reflection/)(`Class.forName` 은 `import` 와 무관하다).

## 한눈에 — 쉽게 말하면

**`import` 는 "이 파일 안에서만 쓰는 약칭 사전"이다.**\
그리고 **그 사전은 컴파일이 끝나면 버려진다** — 클래스 파일에는 전부 풀네임으로 적혀 있다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 약칭 사전 | `import` 선언들 — **한 파일(컴파일 단위)에만** 효력이 있다 |
| "`List` 는 `java.util.List` 를 뜻한다"는 한 줄 | **단일 타입 import**(`import java.util.List;`) |
| "`java.util` 패키지 말은 다 통한다"는 한 줄 | **온디맨드 import**(`import java.util.*;`) |
| 같은 약칭이 두 사전에 있어 못 고르는 상태 | **모호(ambiguous)** — 컴파일 에러 |
| 사전보다 우선하는 "이 동네 말" | 같은 패키지·같은 파일에 선언된 타입 |
| 사전을 안 봐도 통하는 기본 어휘 | `java.lang.*` — **자동으로 import 된다** |
| 컴파일이 끝나면 사전을 버리는 것 | 클래스 파일에는 `java/util/ArrayList` 처럼 **풀네임**만 남는다 |
| (25) "이 모듈이 내보내는 패키지 말은 다 통한다" | **모듈 import 선언**(`import module java.base;`) |

- `import` 는 **코드를 바꾸지 않는다.** 짧게 적게 해 줄 뿐이다.\
  그래서 `import` 를 지우고 전부 풀네임으로 고쳐도 **바이트코드가 똑같다**(「동작 방식 (4)」에서 `javap` 로 확인).
- 약칭이 겹치면 컴파일러가 **고르지 않고 멈춘다.** 이때 나는 말이 `reference to List is ambiguous` 다.
- **모호는 `import` 줄이 아니라 그 이름을 *쓴* 줄에서 난다** — 안 쓰면 에러도 안 난다.

```text
소스                                  컴파일러가 하는 일               클래스 파일

import java.util.List;        ─┐
import java.util.ArrayList;   ─┤  이름 -> 풀네임 변환에만 쓰고
                               │  선언 자체는 버린다
List<String> a =               │                                  new java/util/ArrayList
    new ArrayList<>();        ─┘                                  InterfaceMethod
                                                                    java/util/List.add
```

실무에서 이게 터지는 자리는 **`java.util.Date` 와 `java.sql.Date`**,\
**`java.util.List` 와 `java.awt.List`**, **`org.junit.Test` 와 `org.junit.jupiter.api.Test`** 처럼\
**같은 단순 이름이 두 패키지에 있는** 경우다.\
IDE 가 `import` 를 자동으로 넣어 주다가 엉뚱한 쪽을 골라 놓으면, 에러는 **한참 아래 사용 줄**에서 난다.

> **컴파일 단위(compilation unit)** — 소스 파일 하나. `import` 의 효력 범위가 정확히 이것이다.\
> 예: `A.java` 의 `import` 는 `B.java` 에 아무 영향이 없다.

> **단순 이름(simple name)** — 점이 없는 이름. `List`·`Map` 같은 것.\
> 예: `java.util.List` 의 단순 이름은 `List` 다.

> **모호(ambiguous)** — 같은 단순 이름의 후보가 둘 이상이어서 컴파일러가 하나를 못 고르는 상태.\
> 예: `java.util.*` 와 `java.awt.*` 를 둘 다 온디맨드로 들여오고 `List` 를 쓰면 이 상태가 된다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 같은 단순 이름의 후보가 여럿일 때 **누가 이기고, 언제 못 고르는가.**
2. `import` 는 **실행에 무엇을 남기는가** — 그것을 어떻게 확인하는가.
3. (25) **모듈 import 선언**은 무엇을 줄이고, 무엇을 새로 만드는가.

## 동작 방식

### (1) 네 가지 후보 — 이기는 순서가 있다

**언제 쓰나** — 같은 단순 이름이 여러 곳에 있을 때. `Date`·`List`·`Test` 가 대표다.

JLS §6.4.1(Shadowing)이 정한 우선순위를, 강한 쪽부터 놓으면 이렇다.

```text
강함
 ┌──────────────────────────────────────────────┐
 │ 1. 같은 파일·같은 패키지에 선언된 타입           │  <- 사전보다 "이 동네 말"이 먼저
 ├──────────────────────────────────────────────┤
 │ 2. 단일 타입 import  (import java.util.List;) │  <- 명시적으로 고른 것
 ├──────────────────────────────────────────────┤
 │ 3. 온디맨드 import   (import java.util.*;)    │  <- 여럿이면 모호
 │    (25) 모듈 import  (import module java.base;)│
 ├──────────────────────────────────────────────┤
 │ 4. java.lang.*  (자동)                        │
 └──────────────────────────────────────────────┘
약함
```

**1 이 2·4 를 이긴다** — 실행으로 확인했다(`Ex.java (34-own)` · `(34-shadow)`, JDK 21.0.5).

```text
--- 같은 패키지의 타입이 on-demand import 를 가린다
  x = 내가 만든 List (List)
  y = [] (java.util.ArrayList)
--- 같은 패키지 타입이 java.lang 을 가린다
  내 Integer (Integer)
  java.lang.Integer.MAX_VALUE = 2147483647
```

그림 해설 (한 단계씩):

- 같은 패키지에 `List` 클래스를 두고 `import java.util.*;` 를 쓰면 **내 `List` 가 이긴다.**\
  `java.util.List` 를 쓰려면 **풀네임으로 적어야** 한다(`y` 가 그것이다).
- `Integer` 도 마찬가지다. **`java.lang` 도 예외가 아니다** — 내가 만든 `Integer` 가 이긴다.\
  진짜 `Integer` 를 쓰려면 `java.lang.Integer` 라고 풀네임을 적는다.
- 그래서 **`List`·`Integer`·`Object` 같은 이름으로 클래스를 만들지 않는 것**이 실무 규칙이 된다.

비용 — 없다. 다만 **읽는 사람이 헷갈리는 비용**이 크다.

### (2) 모호 — `import` 줄이 아니라 *쓰는* 줄에서 터진다

**언제 쓰나** — `reference to X is ambiguous` 를 만났을 때.

```java
import java.util.*;
import java.awt.*;

public class Ex {
    public static void main(String[] args) {
        List x = null;          // <- 여기서 터진다
    }
}
```

```text
Ex.java:6: error: reference to List is ambiguous
        List x = null;
        ^
  both class java.awt.List in java.awt and interface java.util.List in java.util match
1 error
```

- **`import` 두 줄은 아무 에러도 내지 않는다.** `List` 를 안 쓰면 컴파일이 통과한다.
- 에러 메시지가 **후보 둘을 이름까지 찍어 준다** — 고치는 데 필요한 정보가 다 있다.

반면 **단일 타입 import 두 개가 겹치면 `import` 줄에서 바로 터진다.**

```java
import java.util.List;
import java.awt.List;
```

```text
Ex.java:2: error: a type with the same simple name is already defined by the single-type-import of List
import java.awt.List;           // 같은 단순 이름 둘
^
1 error
```

```text
온디맨드 둘이 겹침                     단일 타입 둘이 겹침
+-------------------------------+     +-------------------------------+
| import 줄  : 통과              |     | import 줄  : 에러             |
| 쓰는 줄    : ambiguous 에러    |     | 쓰는 줄    : 거기까지 못 간다  |
+-------------------------------+     +-------------------------------+
  -> "안 쓰면 괜찮다"                    -> "선언 자체가 모순이다"
```

- 두 경우의 **에러 문구가 다르다.** 어느 쪽인지 문구로 바로 판별할 수 있다.

**해소법은 둘 중 하나다.**

```java
import java.util.*;
import java.awt.*;
import java.util.List;          // 단일 타입 import 로 승부를 낸다
```

```text
--- 단일 타입 import 우선 : [hi] / java.util.ArrayList
```

- 또는 그냥 **쓰는 자리에 풀네임**을 적는다(`java.awt.List` 를 몇 번만 쓴다면 이쪽이 낫다).

비용 — 없다. 단 "단일 타입 import 로 눌렀다"는 사실이 **파일 맨 위에만 적혀 있어** 아래쪽을 읽는 사람은 모른다.

### (3) `static import` — 타입이 아니라 멤버를 들여온다

**언제 쓰나** — `Math.max`·`Assertions.assertEquals`·`Collectors.toList` 를 이름만으로 쓰고 싶을 때.

```text
import static java.lang.Math.max;   단일 static import  -> max 만
import static java.lang.Math.*;     온디맨드 static     -> Math 의 static 멤버 전부
```

실행 결과 (`Ex.java (34-si1)`, JDK 21.0.5):

```text
--- static import
  asList(1,2,3) = [1, 2, 3]
  of(1,2,3)     = [1, 2, 3]
  max(3,7)      = 7
  abs(-5)       = 5   (on-demand static import)
  PI            = 3.141592653589793
```

- **메서드도 필드도** 들여온다(`PI` 가 필드다).
- 인터페이스의 static 메서드도 된다(`java.util.List.of`).

**겹치면 여기서도 모호해진다** (`Ex.java (34-si2)`).

```java
import static java.lang.Math.*;
import static pkg.Tools.*;      // Tools 에도 max(int,int) 가 있다
...
System.out.println(max(3, 7));
```

```text
Ex.java:6: error: reference to max is ambiguous
        System.out.println(max(3, 7));
                           ^
  both method max(int,int) in Math and method max(int,int) in Tools match
1 error
```

- 타입 모호와 **같은 구조**다 — 선언은 통과하고, 쓰는 줄에서 터진다.
- 다만 **시그니처가 다르면 오버로딩으로 합쳐진다.** 완전히 같은 시그니처일 때만 모호다.

**남용 경계** — 이 셋이 실무의 선이다.

| 쓴다 | 안 쓴다 |
|---|---|
| 테스트의 `assertEquals`·`assertThat` — 한 파일에서 수십 번 나온다 | 도메인 코드의 일반 유틸 — `Tools.max` 가 어디서 왔는지 안 보인다 |
| `Collectors.*` 를 스트림 파이프라인에서 | 이름이 **짧고 흔한 것**(`of`·`get`·`max`) — 모호와 오해를 동시에 부른다 |
| 상수 묶음(`Math.PI`·`TimeUnit.SECONDS`) | **온디맨드 static import 를 여러 개** — 충돌 가능성이 곱으로 는다 |

- 판단 기준 한 줄: **"이 이름만 보고 어디서 왔는지 알 수 있나."**\
  `assertEquals` 는 안다. `max` 는 모른다.

비용 — 없다. 대가는 **읽는 사람이 정의로 점프하기 전까지 출처를 모른다**는 것이다.

### (4) `import` 는 런타임에 아무것도 아니다 — `javap` 가 증거다

**언제 쓰나** — "`import` 가 많으면 무거워지나", "쓰지 않는 `import` 가 성능에 영향이 있나"를 물을 때.

같은 코드를 **`import` 로** 쓴 것과 **풀네임으로** 쓴 것, 두 파일을 만들었다 (`Ex.java (34-jv1)` · `(34-jv2)`).

```java
// jv1                                    // jv2
import java.util.ArrayList;               public class Ex {
import java.util.List;                        public static void main(String[] args) {
import static java.lang.Math.max;                 java.util.List<String> a =
                                                      new java.util.ArrayList<>();
public class Ex {                                 a.add("x");
    public static void main(String[] args) {      System.out.println(
        List<String> a = new ArrayList<>();           a + " " + java.lang.Math.max(1, 2));
        a.add("x");                               }
        System.out.println(a + " " + max(1, 2));  }
    }
}
```

`javap -c -p Ex.class` 를 두 쪽에서 뽑아 `diff` 했다 (JDK 21.0.5).

```text
두 클래스 파일의 javap -c 출력이 완전히 동일
```

```text
  public static void main(java.lang.String[]);
    Code:
       0: new           #7                  // class java/util/ArrayList
       3: dup
       4: invokespecial #9                  // Method java/util/ArrayList."<init>":()V
       7: astore_1
       8: aload_1
       9: ldc           #10                 // String x
      11: invokeinterface #12,  2           // InterfaceMethod java/util/List.add:(Ljava/lang/Object;)Z
      16: pop
      17: getstatic     #18                 // Field java/lang/System.out:Ljava/io/PrintStream;
      20: aload_1
      21: invokestatic  #24                 // Method java/lang/String.valueOf:(Ljava/lang/Object;)Ljava/lang/String;
      24: iconst_1
      25: iconst_2
      26: invokestatic  #30                 // Method java/lang/Math.max:(II)I
      29: invokedynamic #36,  0             // InvokeDynamic #0:makeConcatWithConstants:(Ljava/lang/String;I)Ljava/lang/String;
      34: invokevirtual #40                 // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      37: return
```

그림 해설 (한 단계씩):

- 바이트코드에 **`java/util/ArrayList`·`java/util/List`·`java/lang/Math` 가 풀네임으로** 박혀 있다.\
  `import` 가 남긴 흔적은 하나도 없다.
- 상수 풀 항목 수도 **양쪽 69개로 같았다**(`javap -v | grep -c` 로 확인).
- `static import` 도 마찬가지다 — `max(1,2)` 가 `invokestatic java/lang/Math.max` 다.

**그런데 클래스 파일 바이트는 달랐다.**

```text
jv1/Ex.class jv2/Ex.class 다름: 975바이트, 8행
```

이유를 `javap -l` 로 찾았다.

```text
< line 7: 0        (jv1 — import 3줄 때문에 코드가 7행에서 시작)
< line 8: 8
< line 9: 17
< line 10: 37
---
> line 3: 0        (jv2)
> line 4: 8
> line 5: 17
> line 6: 37
```

- 다른 것은 **`LineNumberTable`**(디버거가 쓰는 소스 줄 번호)뿐이다.
- 즉 `import` 가 클래스 파일에 남기는 것은 **"코드가 소스 몇 번째 줄인가"라는 부수 정보**가 전부다.

비용 — **런타임 비용 0.** 쓰지 않는 `import` 는 컴파일 시간 외에 아무 대가가 없다.\
그래도 지우는 이유는 **읽는 사람과 의존성 추적** 때문이지 성능이 아니다.

### (5) (25) 모듈 import 선언 — 온디맨드 import 를 모듈 단위로

**언제 쓰나** — JDK 25 이상에서, 짧은 프로그램·스크립트의 `import` 더미를 줄이고 싶을 때.

```java
import module java.base;        // java.base 가 export 하는 모든 패키지를 온디맨드로
```

**JDK 21 에서는 문법이 없다** (`Ex.java (34-mod)`).

```text
##### JDK 21
Ex.java:1: error: '.' expected
import module java.base;
             ^
1 error
```

- 파서가 `import` 다음에 **타입 이름**을 기대하고 있다. `module` 을 패키지 이름으로 읽다가 `.` 을 찾는다.
- JDK 17 에서도 **같은 메시지**였다(돌려 확인).

**JDK 25 에서는 플래그 없이 된다.**

```text
##### JDK 25 (플래그 없이)
--- import module java.base
  List      = [a, b, c]
  Map       = {a=1, b=1, c=1}
  Collectors= a,b,c
  Path      = /tmp  (java.nio.file)
  Function  = 42
```

- `java.util`·`java.util.stream`·`java.nio.file`·`java.util.function` 이 **한 줄로 다 들어왔다.**
- `--enable-preview` 를 **안 붙였고**, `javac -Xlint:preview` 도 경고를 내지 않았다 → **정식 기능**이다(JEP 511).

**무엇을 줄이나** — 숫자로 재 봤다(`Ex.java (34-cnt)`).

```text
--- java.base
  무조건 export 하는 패키지 수 = 58      (JDK 25.0.1)
--- java.desktop
  무조건 export 하는 패키지 수 = 51
```

```text
import module java.base;              import java.util.*;
                                      import java.util.stream.*;
   =  온디맨드 import 58줄에 해당      import java.nio.file.*;
                                      import java.util.function.*;
                                      ... (필요한 만큼)
```

- (JDK 21 에서 같은 프로그램을 돌리면 `java.base` 가 **54**, `java.desktop` 이 **50** 이었다.\
  버전이 오르며 패키지가 는다 — 그래서 **숫자를 외우지 말고 세는 법을 외운다.**)

**새로 만드는 것 — 모호가 더 쉬워진다.**

```java
import module java.base;
import module java.desktop;
...
List<String> x = List.of("a");
```

```text
Ex.java:6: error: reference to List is ambiguous
        List<String> x = List.of("a");
        ^
  both class java.awt.List in java.awt and interface java.util.List in java.util match
2 errors
```

- (2) 의 온디맨드 충돌과 **완전히 같은 구조**다. 모듈 import 는 결국 온디맨드 import 의 묶음이다.
- 해소도 같다 — **단일 타입 import 로 누른다.**

```text
--- 모듈 import 둘 + 단일 타입 import : [a]
```

비용 — 없다(런타임은 (4) 와 같다). 대가는 **이름의 출처가 더 흐려진다**는 것이다.\
그래서 JEP 511 의 자리는 **짧은 프로그램·학습용 코드**이지 큰 애플리케이션이 아니다.

## 문법 — 형태와 규칙

```java
package com.example;            // 있다면 맨 위 하나

import java.util.List;                     // 단일 타입
import java.util.*;                        // 온디맨드(타입)
import static java.lang.Math.max;          // 단일 static
import static java.lang.Math.*;            // 온디맨드 static
import module java.base;                   // (25) 모듈
```

- 순서는 `package` → `import`(전부) → 타입 선언. `import` 들 사이의 순서는 **의미가 없다.**
- **`import` 는 한 파일에만 효력이 있다.** 다른 파일이 같은 패키지여도 각자 써야 한다.
- **`import java.util.*;` 는 하위 패키지를 포함하지 않는다.**

```text
Ex.java:4: error: cannot find symbol
        ConcurrentHashMap<String,String> m = new ConcurrentHashMap<>();
        ^
  symbol:   class ConcurrentHashMap
  location: class Ex
```

- `java.util.concurrent` 는 `java.util` 의 "하위"처럼 보이지만 **완전히 다른 패키지**다.\
  패키지 이름의 점은 **계층이 아니라 그냥 이름의 일부**다.
- **중첩 타입은 점으로 들여온다** — `import java.util.Map.Entry;`\
  그리고 **`import java.util.*;` 만으로는 `Entry` 가 단순 이름이 되지 않는다.**

```text
===== import java.util.Map.Entry; 를 쓴 쪽
--- 중첩 타입 import
  Entry 로 선언 = a=1 (java.util.KeyValueHolder)
  a=1
  b=2

===== import java.util.*; 만 쓴 쪽
Ex.java:4: error: cannot find symbol
        Entry<String,Integer> e = null;
        ^
  symbol:   class Entry
  location: class Ex
1 error
```

  온디맨드 import 는 **그 패키지의 최상위 타입**만 준다. `Entry` 는 `Map` 의 **멤버**라 따로 들여와야 한다.\
  (`import static java.util.Map.entry;` 로 **인터페이스의 static 메서드**도 함께 쓸 수 있다 — 위 실행이 그것이다.\
  반환된 구현체 이름 `java.util.KeyValueHolder` 는 **구현 세부**라 기대면 안 된다.)
- `java.lang.*` 은 **자동**이다. 적어도 되지만 의미가 없다.

| 형태 | 들여오는 것 | 충돌하면 | `@since` |
|---|---|---|---|
| `import p.T;` | 타입 하나 | **선언 줄에서** 에러 | 1.0 |
| `import p.*;` | 그 패키지의 타입 전부 | **쓰는 줄에서** ambiguous | 1.0 |
| `import static p.T.m;` | static 멤버 하나 | 선언 줄에서 에러 | 5 |
| `import static p.T.*;` | 그 타입의 static 멤버 전부 | 쓰는 줄에서 ambiguous | 5 |
| `import module M;` | 그 모듈이 export 하는 **모든 패키지**를 온디맨드로 | 쓰는 줄에서 ambiguous | **25** |

## 어디서 틀리나

### 1. IDE 가 넣어 준 `import` 를 안 본다

- `Date`·`List`·`Test`·`Assert`·`Timer`·`Observer` — 전부 두 곳 이상에 있다.
- 증상: **컴파일은 되는데 동작이 이상하다**(다른 쪽 `Date` 를 쓰고 있다).
- 방어: 애매한 이름은 **`import` 줄을 눈으로 확인**한다. 리뷰에서도 `import` 블록을 읽는다.

### 2. 온디맨드 두 개를 겹쳐 놓고 "괜찮은데?" 한다

- `java.util.*` 와 `java.awt.*` 를 같이 써도 **`List` 를 안 쓰면 에러가 없다.**
- 나중에 누가 `List` 를 한 줄 쓰는 순간 **그 사람 탓처럼** 에러가 난다.
- 방어: 온디맨드는 **패키지 하나**까지. 둘 이상이면 단일 타입으로 바꾼다.

### 3. `java.util.*` 로 `java.util.concurrent` 가 들어올 거라 믿는다

- 위 「문법」의 `cannot find symbol` 이 그 결과다.
- 방어: **점은 계층이 아니다**를 기억한다.

### 4. `import` 가 성능에 영향이 있다고 믿는다

- (4) 에서 본 대로 **바이트코드가 같다.** 쓰지 않는 `import` 는 런타임에 0 이다.
- 그래도 지운다 — 이유는 **의존성 추적과 가독성**이다. "성능 때문"이라는 설명은 틀렸다.

### 5. `static import` 를 남용해 출처를 지운다

```java
// 이 파일 어딘가에서
int r = max(a, b);      // Math.max? Tools.max? 내 static 메서드?
```

- 방어: 「동작 방식 (3)」의 판단 기준 — **"이름만 보고 어디서 왔는지 아는가."**

### 6. ★ 내가 만든 클래스 이름이 표준 타입을 가린다

이 문서를 쓰다가 **실제로 겪은 일**이다. 리플렉션 예제(58번)에서 클래스 이름을 `Target` 으로 지었더니:

```text
Ex.java:5: error: incompatible types: Target cannot be converted to Annotation
@Retention(RetentionPolicy.RUNTIME) @Target({ElementType.TYPE, ElementType.FIELD}) @interface Keep { ... }
                                     ^
```

- `import java.lang.annotation.*;` 로 들여온 `@Target` 을, **같은 파일에 선언한 `class Target` 이 가렸다.**
- 에러 메시지가 `Target cannot be converted to Annotation` 이라 **원인이 `import` 라는 것이 안 보인다.**
- 방어: `Target`·`List`·`Entry`·`Type`·`Field`·`Method` 처럼 **표준 라이브러리에 흔한 이름을 피한다.**

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| 같은 파일·패키지 타입이 import 를 가린다 | **언어**(JLS §6.4.1) | (1) 의 실행 결과는 그 관찰 |
| 단일 타입 import 가 온디맨드를 이긴다 | **언어**(JLS §7.5.1~7.5.2) | (2) 의 해소 |
| `import` 가 클래스 파일에 남지 않는다 | **언어**(클래스 파일은 항상 풀네임으로 참조한다) | (4) 의 `javap` |
| 클래스 파일 바이트가 `LineNumberTable` 만 다른 것 | **컴파일러 구현** | 디버그 정보는 `-g` 옵션에 달렸다 |
| 상수 풀 항목 수가 69 로 같은 것 | **컴파일러 구현** | 값이 아니라 **"같다"는 사실**만 의미가 있다 |
| 에러 메시지 문구 | **컴파일러 구현** | 17·21·25 에서 같았지만 보장이 아니다 |
| `java.base` 가 export 하는 패키지 수 | **그 JDK 버전** | 21 = 54, 25 = 58 (직접 셈) |

## 언제 쓰고 언제 안 쓰나

| | 쓴다 | 안 쓴다 |
|---|---|---|
| 단일 타입 | **기본값.** 출처가 보인다 | — |
| 온디맨드 | 같은 패키지에서 대여섯 개 이상 쓸 때 | 패키지 둘 이상을 동시에 |
| static import | 테스트 단언, `Collectors`, 상수 묶음 | 도메인 유틸, 짧고 흔한 이름 |
| 모듈 import (25) | 한 파일짜리 프로그램·학습 코드·스크립트 | 팀이 오래 유지하는 애플리케이션 코드 |
| 풀네임 | 충돌이 났고 쓰는 곳이 한두 군데일 때 | 같은 타입을 수십 번 쓸 때 |

## 핵심 문장

- `import` 는 **한 파일 안의 약칭 사전**이고, 컴파일이 끝나면 **바이트코드에 아무것도 남기지 않는다**(`javap` 로 확인).
- 우선순위는 **같은 파일·패키지 > 단일 타입 import > 온디맨드/모듈 import > `java.lang`** 이다.
- **온디맨드 충돌은 `import` 줄이 아니라 이름을 쓰는 줄에서** 터지고, **단일 타입 충돌은 선언 줄에서** 터진다.
- `java.util.*` 은 **`java.util.concurrent` 를 포함하지 않는다** — 패키지 이름의 점은 계층이 아니다.
- **모듈 import 선언은 25 정식**(JEP 511)이고, 21 에서는 `'.' expected` 로 파싱조차 안 된다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 34번)
- [`../../../../../../history/java/java-25.md`](../../../../../../history/java/java-25.md) — **모듈 import 선언(JEP 511)이 언제·왜 정식이 됐나가 정본.**\
  **경계: 그쪽은 「23·24 프리뷰를 거쳐 25 정식」이라는 연혁까지, 여기는 「그래서 21 과 25 에서 각각 어떻게 되나」부터다.**
- [`../../../../../../history/java/java-9.md`](../../../../../../history/java/java-9.md) — **모듈 시스템(JPMS) 자체가 정본이다.**\
  **경계: 「모듈이 무엇이고 왜 만들었나」는 그쪽, 여기는 「`import module` 이라는 문법 표면」만.**\
  `module-info.java`·`requires`·`exports` 의 설계는 이 문서가 다루지 않는다(목록의 「뺀 것과 이유」 참고).
- [`../58-reflection/`](../58-reflection/) — **경계: `Class.forName("java.util.List")` 은 `import` 와 무관하다.**\
  `import` 는 컴파일 타임 약칭이고 리플렉션은 런타임 문자열이다 — 둘을 같은 것으로 배우지 않게 이 경계를 둔다.\
  모듈 경계가 **런타임에** 무엇을 막는지는 58번이 정본이다.
- [`../10-access-modifiers/`](../10-access-modifiers/) — **경계: 그쪽은 「보이느냐」(접근 제어), 여기는 「짧게 부를 수 있느냐」(이름 해소).**\
  `import` 를 해도 `private` 은 여전히 안 보인다 — 둘은 다른 축이다.
- [`../12-nested-classes/`](../12-nested-classes/) — 중첩 타입을 `import p.Outer.Inner;` 로 들여오는 형태
- [`../16-annotations/`](../16-annotations/) — 「어디서 틀리나」 6번에서 실제로 충돌한 `@Target` 이 거기 있다
- [`../31-functional-interfaces/`](../31-functional-interfaces/) · [`../47-collectors-basics/`](../47-collectors-basics/) — `static import` 를 실제로 쓰는 자리
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — **경계: 클래스로더·모듈 런타임 내부는 거기.**

## 용어 풀이

- **컴파일 단위(compilation unit)** — 소스 파일 하나. `import` 의 효력 범위.
- **단일 타입 import(single-type-import)** — `import p.T;` — 타입 하나를 단순 이름으로 쓰게 한다.
- **온디맨드 import(type-import-on-demand)** — `import p.*;` — 그 패키지의 타입을 필요할 때 찾게 한다.
- **static import** — `import static p.T.m;` — 타입이 아니라 **static 멤버**를 단순 이름으로 쓰게 한다(5+).
- **모듈 import 선언(module import declaration)** — `import module M;` — 그 모듈이 export 하는 모든 패키지를 온디맨드로 들여온다(25 정식, JEP 511).
- **단순 이름 / 정규화된 이름** — 점 없는 이름 / 패키지까지 붙인 풀네임.
- **가림(shadowing)** — 더 강한 선언이 약한 선언을 덮는 것. JLS §6.4.1.
- **모호(ambiguous)** — 후보가 둘 이상이라 고를 수 없는 상태. 컴파일 에러.
- **`LineNumberTable`** — 클래스 파일에 들어가는, 바이트코드 위치 ↔ 소스 줄 번호 표. 디버거·스택트레이스가 쓴다.
- **export** — 모듈이 자기 패키지를 밖에서 쓸 수 있게 여는 것. 모듈 import 가 가져오는 대상이 이것이다.

## 더 들어가면

- **`import` 에 쓴 타입이 실제로 존재하는지는 컴파일 타임에만 확인된다.**\
  클래스 파일에는 풀네임 참조만 남으므로, **런타임에 그 클래스가 없으면** `NoClassDefFoundError` 가 난다.\
  즉 `import` 가 통과했다고 실행이 보장되지 않는다 — 컴파일 클래스패스와 실행 클래스패스가 다르면 그렇다.

- **온디맨드 import 가 컴파일을 느리게 한다는 말은 요즘 근거가 약하다.**\
  다만 **이름 후보가 늘어 모호가 날 확률이 오른다**는 것은 (2)·(5) 에서 본 대로 사실이다.\
  (컴파일 시간 자체는 이 배치에서 재지 않았다.)

- **모듈 import 는 "모듈을 의존한다"는 뜻이 아니다.**\
  `import module java.base;` 는 **이름 해소**만 바꾼다. 실제로 그 모듈을 읽을 수 있는지는\
  모듈 그래프(`requires`)나 클래스패스가 정한다 — 그래서 클래스패스 프로그램에서도 그냥 동작한다((5) 의 실행이 그렇다).

- **`java.desktop` 도 모듈 import 가 된다**(51개 패키지). 그래서 `java.base` 와 같이 쓰면\
  `List` 가 바로 모호해진다 — (5) 의 두 번째 실행이 그것이다.\
  **한 줄로 58개 패키지를 여는 편리함과 충돌 확률은 같은 동전의 양면**이다.

- **`javap -v` 로 상수 풀을 세는 법**: `javap -v Ex.class | grep -c '^ *#'`.\
  (4) 에서 두 파일이 **69 로 같았다**. 절대값보다 "같다"가 근거다 — 컴파일러가 바뀌면 값은 변한다.
