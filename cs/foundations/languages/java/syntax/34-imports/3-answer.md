# java/syntax/34 — `import`·static import·(25) 모듈 import 선언 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **실제로 돌려 얻은 것**이다 —
> 일반 `import` 는 Temurin **JDK 21.0.5**, **모듈 import 선언은 JDK 25.0.1**.\
> 바이트코드는 `javap -c -p`·`javap -l`·`javap -v` 출력을, 클래스 파일 비교는 `cmp` 를 썼다.\
> 실행 파일명은 전부 `Ex.java` 로 고정했고, 프로그램이 여럿이라 `Ex.java (34-a)` 처럼 라벨로 구분한다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 온디맨드 둘이 겹치면 어디서 터지나

**출력** (`Ex.java (34-a)`, JDK 21.0.5)

```text
Ex.java:6: error: reference to List is ambiguous
        List x = null;
        ^
  both class java.awt.List in java.awt and interface java.util.List in java.util match
1 error
```

**어디서 터지나**

- `import` 두 줄(2·3행)은 **아무 에러도 내지 않는다.**
- 에러는 `List` 를 **쓴 줄**(6행)에서 난다.

**메시지 첫 줄** — `error: reference to List is ambiguous`

- 그 아래 줄이 후보 둘을 **풀네임과 종류(class/interface)까지** 찍어 준다.\
  `java.awt.List` 는 클래스, `java.util.List` 는 인터페이스다.

**`List x = null;` 을 지우면**

- **컴파일된다.** 온디맨드 import 는 "이름을 쓸 때 찾아본다"는 뜻이라, 안 쓰면 찾을 일이 없다.
- 이것이 위험한 이유: 지금은 통과하고, **나중에 누가 `List` 를 한 줄 쓰는 순간** 그 사람 코드에서 터진다.

### 2. 단일 타입 import 둘이 겹치면

**출력** (`Ex.java (34-c)`, JDK 21.0.5)

```text
Ex.java:2: error: a type with the same simple name is already defined by the single-type-import of List
import java.awt.List;           // 같은 단순 이름 둘
^
1 error
```

**두 줄만으로 에러가 난다.** 본문에서 `List` 를 한 번도 안 써도 그렇다.

**1번과의 차이**

| | 온디맨드 충돌 | 단일 타입 충돌 |
|---|---|---|
| 에러 나는 줄 | 이름을 **쓰는** 줄 | **`import` 선언** 줄 |
| 문구 | `reference to List is ambiguous` | `a type with the same simple name is already defined by the single-type-import of List` |
| 안 쓰면 | 통과한다 | **그래도 에러다** |

**문구만 보고 구별할 수 있다.**

- `ambiguous` → 온디맨드(또는 모듈 import) 충돌. **쓰는 줄**을 본다.
- `already defined by the single-type-import` → 선언 충돌. **`import` 블록**을 본다.

### 3. 누가 이기나 — 우선순위

**출력** (`Ex.java (34-own)` · `(34-shadow)`, JDK 21.0.5)

```text
--- 같은 패키지의 타입이 on-demand import 를 가린다
  x = 내가 만든 List (List)
  y = [] (java.util.ArrayList)
--- 같은 패키지 타입이 java.lang 을 가린다
  내 Integer (Integer)
  java.lang.Integer.MAX_VALUE = 2147483647
```

**두 변수의 타입**

- `x` 는 **내가 만든 `List`** 다(`getClass().getName()` 이 `List`).
- `i` 는 **내가 만든 `Integer`** 다.

**`java.lang.Integer` 도 가려진다.** 자동 import 라고 특별 대우를 받지 않는다.

**진짜 `java.util.List` 를 쓰려면** — **풀네임을 적는다.**

```java
java.util.List<String> y = new ArrayList<>();
```

**우선순위 네 단계** (JLS §6.4.1 · §7.5)

```text
1. 같은 파일·같은 패키지에 선언된 타입
2. 단일 타입 import
3. 온디맨드 import · (25) 모듈 import       <- 여럿이면 ambiguous
4. java.lang.*  (자동)
```

- 실무 결론: **`List`·`Integer`·`Object`·`Type`·`Field` 같은 이름으로 클래스를 만들지 않는다.**

### 4. `import` 를 지우고 풀네임으로 바꾸면 클래스 파일이 같은가

**출력** (`Ex.java (34-jv1)` · `(34-jv2)`, JDK 21.0.5)

```text
두 클래스 파일의 javap -c 출력이 완전히 동일
--- cmp 바이트 비교
jv1/Ex.class jv2/Ex.class 다름: 975바이트, 8행
```

**`javap -c` 출력은 같다.**

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

- 전부 **풀네임**(`java/util/ArrayList`, `java/lang/Math`)이다. `import` 흔적이 없다.
- `static import` 로 쓴 `max(1,2)` 도 `invokestatic java/lang/Math.max` 다.
- 상수 풀 항목 수도 **양쪽 69 로 같았다**(`javap -v Ex.class | grep -c '^ *#'`).

**바이트는 다르다.** 어느 속성인지 `javap -l` 로 찾았다.

```text
<       line 7: 0        (import 3줄이 있는 쪽 — 코드가 7행에서 시작)
<       line 8: 8
<       line 9: 17
<       line 10: 37
---
>       line 3: 0        (import 0줄인 쪽)
>       line 4: 8
>       line 5: 17
>       line 6: 37
```

- 다른 것은 **`LineNumberTable`** 뿐이다 — 바이트코드 위치 ↔ 소스 줄 번호 표.
- 즉 `import` 가 남기는 것은 **"코드가 소스 몇 행인가"라는 디버그 정보**가 전부다.

**결론이 말하는 것**

- 쓰지 않는 `import` 를 지우는 이유는 **성능이 아니다.** 런타임 비용이 0 이다.
- 지우는 진짜 이유는 **의존성이 보이게 하는 것**과 **읽는 사람**이다.\
  "`import` 가 많으면 느리다"는 설명은 이 출력 앞에서 유지될 수 없다.

### 5. `import module java.base;` 를 21 과 25 에서 각각

**출력** (`Ex.java (34-mod)`)

```text
##### JDK 21
Ex.java:1: error: '.' expected
import module java.base;
             ^
1 error

##### JDK 25 (플래그 없이)
--- import module java.base
  List      = [a, b, c]
  Map       = {a=1, b=1, c=1}
  Collectors= a,b,c
  Path      = /tmp  (java.nio.file)
  Function  = 42
```

**JDK 21 의 에러 첫 줄** — `error: '.' expected`

- 캐럿이 `module` 과 `java` 사이를 가리킨다. 파서는 `import module.java.base` 처럼 **패키지 이름**을 기대한 것이다.
- **JDK 17 에서도 같은 메시지**였다(돌려 확인).

**JDK 25 에서 `--enable-preview` 는 필요 없다.**

**정식인가 프리뷰인가 — 정식이다.** 세 가지로 확인했다.

1. `javac Ex.java` 가 **플래그 없이** 컴파일됐다.
2. `javac -Xlint:preview Ex.java` 가 **아무 경고도 내지 않았다**(exit 0).\
   프리뷰 기능을 쓰면 `uses preview features` 경고나 에러가 난다.
3. 이 기능은 **JEP 511**(23 = JEP 476 1차 preview, 24 = JEP 494 2차)이다.

**`java.base` 가 export 하는 패키지 수** — 프로그램으로 셌다(`Ex.java (34-cnt)`).

```java
ModuleDescriptor d = ModuleLayer.boot().findModule("java.base").orElseThrow().getDescriptor();
long unqualified = d.exports().stream().filter(e -> !e.isQualified()).count();
```

```text
(JDK 21.0.5)                (JDK 25.0.1)
--- java.base               --- java.base
  무조건 export 하는 패키지 수 = 54    무조건 export 하는 패키지 수 = 58
--- java.desktop            --- java.desktop
  무조건 export 하는 패키지 수 = 50    무조건 export 하는 패키지 수 = 51
```

- **버전마다 다르다.** 숫자를 외우지 말고 **세는 코드**를 외운다.
- `import module java.base;` 한 줄이 JDK 25 에서 **온디맨드 import 58 줄** 몫을 한다.

### 6. 모듈 import 두 개를 겹치면

**출력** (`Ex.java (34-mod2)` · `(34-mod3)`, JDK 25.0.1)

```text
Ex.java:6: error: reference to List is ambiguous
        List<String> x = List.of("a");
        ^
  both class java.awt.List in java.awt and interface java.util.List in java.util match
Ex.java:6: error: reference to List is ambiguous
        List<String> x = List.of("a");
                         ^
  both class java.awt.List in java.awt and interface java.util.List in java.util match
2 errors
```

**컴파일 안 된다.**

**1번과 같은 종류의 에러다** — 문구가 한 글자도 다르지 않다.\
모듈 import 는 결국 **온디맨드 import 의 묶음**이기 때문이다.

- 다만 에러가 **둘** 나왔다 — 타입으로 쓴 자리와 `List.of` 로 쓴 자리 둘 다 걸렸다.

**해소** — 단일 타입 import 로 누른다.

```java
import module java.base;
import module java.desktop;
import java.util.List;          // 이 한 줄이 승부를 낸다
```

```text
--- 모듈 import 둘 + 단일 타입 import : [a]
```

- 3번의 우선순위대로 **단일 타입 import 가 온디맨드/모듈 import 를 이긴다.**

### 7. `import java.util.*;` 로 `ConcurrentHashMap` 이 들어오나

**출력** (`Ex.java (34-sub)`, JDK 21.0.5)

```text
Ex.java:4: error: cannot find symbol
        ConcurrentHashMap<String,String> m = new ConcurrentHashMap<>();   // java.util.concurrent
        ^
  symbol:   class ConcurrentHashMap
  location: class Ex
2 errors
```

**안 들어온다.**

**이유 한 문장** — `java.util.concurrent` 는 `java.util` 과 **완전히 다른 패키지**이고,\
온디맨드 import 는 **그 패키지 하나의 타입**만 들여오기 때문이다.

**패키지 이름의 점**

- **계층이 아니라 그냥 이름의 일부**다. `java.util` 과 `java.util.concurrent` 는 형제도 부모자식도 아니고 **남**이다.
- (접근 제어에서도 마찬가지다 — package-private 은 `java.util.concurrent` 에서 `java.util` 을 못 본다.\
  그쪽은 [10 접근 제어자](../10-access-modifiers/) 가 정본이다.)

### 8. `static import` 의 경계

**출력** (`Ex.java (34-si1)` · `(34-si2)`, JDK 21.0.5)

```text
--- static import
  asList(1,2,3) = [1, 2, 3]
  of(1,2,3)     = [1, 2, 3]
  max(3,7)      = 7
  abs(-5)       = 5   (on-demand static import)
  PI            = 3.141592653589793
```

**메서드뿐이 아니다.** `PI` 는 **필드**다 — static 멤버 전부(메서드·필드·중첩 타입)가 대상이다.

**인터페이스의 static 메서드도 된다** — `import static java.util.List.of;` 로 `of(1,2,3)` 을 썼다.

**같은 이름을 두 타입에서 온디맨드로 들여오면**

```text
Ex.java:6: error: reference to max is ambiguous
        System.out.println(max(3, 7));
                           ^
  both method max(int,int) in Math and method max(int,int) in Tools match
1 error
```

- 타입 모호와 **같은 구조**다 — 선언은 통과하고, 쓰는 줄에서 터진다.

**시그니처가 다르면**

- 모호가 아니라 **오버로딩으로 합쳐진다.** 완전히 같은 시그니처(`max(int,int)`)일 때만 에러다.
- 어느 후보가 뽑히는지는 오버로딩 해소 규칙이 정한다 — [08 메서드 선언·오버로딩 해소](../08-method-declaration-overloading/) 가 정본이다.

### 9. 남용 경계

**한 줄 기준**

- **"이 이름만 보고 어디서 왔는지 알 수 있나."**\
  `assertEquals` 는 안다(테스트 프레임워크). `max` 는 모른다(`Math`? 내 유틸? 상속받은 것?).

**테스트 코드에서 널리 쓰이는 이유**

- 한 파일에서 **수십·수백 번** 나오는 이름이라 반복 비용이 크다.
- 그 이름이 **그 파일의 주제 자체**라 출처를 의심할 여지가 없다.
- `assertThat(x).isEqualTo(y)` 처럼 **문장처럼 읽히게** 만드는 것이 목적이다.

**모듈 import 선언의 자리**

| 권장 | 비권장 |
|---|---|
| 한 파일짜리 프로그램, 학습·실습 코드 | 팀이 오래 유지하는 애플리케이션 코드 |
| `jshell`·단일 파일 소스 실행 | 모듈 둘 이상을 동시에 import (충돌 확률이 곱으로 는다) |
| 예제·문서에 붙이는 스니펫 | 이름의 출처가 리뷰 대상인 코드베이스 |

### 10. 왜 이런 규칙인가

**온디맨드 충돌을 쓰는 줄에서 터뜨리는 설계의 이득**

- **패키지에 타입이 새로 추가돼도 기존 코드가 안 깨진다.**\
  만약 `import` 줄에서 미리 검사한다면, 라이브러리가 새 클래스 하나를 추가한 것만으로\
  그 패키지를 온디맨드로 쓰던 코드가 전부 컴파일 에러가 날 수 있다.
- 실제로 **안 쓰는 이름의 충돌은 아무 해가 없다** — 해가 없는 것을 에러로 만들지 않는 설계다.

**단일 타입 import 가 온디맨드를 이기게 한 이유**

- **충돌을 푸는 수단이 필요하기 때문**이다. 둘이 동급이면 모호를 해소할 방법이 풀네임밖에 없다.
- "명시적으로 하나를 고른 쪽이 이긴다"는 것은 **덜 구체적인 것보다 더 구체적인 것이 이긴다**는 일반 원칙이다.

**같은 패키지 타입이 `java.lang` 까지 가리는 것의 대가**

- 내가 만든 `Integer`·`String` 이 **표준 타입을 조용히 덮는다.** 에러가 엉뚱한 자리에서 난다.
- 실제로 이 배치에서 겪었다 — 58번 예제의 `class Target` 이 `@Target` 을 가려\
  `incompatible types: Target cannot be converted to Annotation` 이 나왔다(「어디서 틀리나」 6번).
- 이득은 **사용자 코드가 언제나 우선**이라 플랫폼이 새 클래스를 추가해도 내 코드가 안 깨진다는 것이다.

### 11. 다른 주제와 잇기

**`import` 와 접근 제어**

| | 정하는 것 |
|---|---|
| `import` | **짧게 부를 수 있느냐**(이름 해소) |
| 접근 제어자 | **보이느냐**(가시성) |

- `import` 를 해도 `private` 멤버는 안 보인다. 반대로 `import` 없이 풀네임을 쓰면 `public` 은 다 보인다.
- 두 축은 독립이다 — 정본은 [10 접근 제어자](../10-access-modifiers/).

**`Class.forName("java.util.List")`**

- **`import` 의 영향을 전혀 안 받는다.** 리플렉션은 **런타임 문자열**로 클래스를 찾고,\
  `import` 는 **컴파일 타임 약칭**이다. 둘은 같은 층이 아니다.
- 그래서 `import` 를 아무리 넣어도 `Class.forName("List")` 는 실패한다 — 풀네임을 줘야 한다.
- 런타임에 무엇이 막히는지(모듈 경계)는 [58 리플렉션](../58-reflection/) 이 정본이다.

**`import` 가 통과했는데 실행에서 터질 수 있나**

- **있다.** 클래스 파일에는 풀네임 참조만 남으므로, 실행 클래스패스에 그 클래스가 없으면\
  **`NoClassDefFoundError`**(또는 `ClassNotFoundException`)가 난다.
- 즉 `import` 의 성공은 **컴파일 클래스패스**에 대한 보증이지 실행에 대한 보증이 아니다.

**클래스 이름을 `Target`·`Type`·`Field` 로 지으면**

- 같은 파일·패키지의 타입이 **import 를 이기므로**(3번) 표준 타입이 가려진다.
- 에러가 **`import` 줄이 아니라 그 타입을 쓰는 엉뚱한 자리**에서 나서 원인 찾기가 오래 걸린다.
- 관련 애너테이션 이야기는 [16 애너테이션](../16-annotations/) 이 정본이다.

### 12. 중첩 타입과 static 멤버 import

**출력** (`Ex.java (34-nest)` · `(34-nest2)`, JDK 21.0.5)

```text
===== import java.util.*; 만 쓴 쪽
Ex.java:4: error: cannot find symbol
        Entry<String,Integer> e = null;
        ^
  symbol:   class Entry
  location: class Ex
1 error

===== import java.util.Map.Entry; 를 쓴 쪽
--- 중첩 타입 import
  Entry 로 선언 = a=1 (java.util.KeyValueHolder)
  a=1
  b=2
```

**(가) 는 컴파일되지 않는다** — `cannot find symbol / symbol: class Entry`.

**온디맨드가 중첩 타입을 주지 않는 이유**

- `import p.*;` 는 **그 패키지의 최상위 타입**을 대상으로 한다.
- `Entry` 는 패키지 `java.util` 의 타입이 아니라 **`Map` 이라는 타입의 멤버**다.\
  7번에서 본 "패키지의 점은 계층이 아니다"와 같은 결의 이야기다 — **패키지 멤버와 타입 멤버는 다른 층**이다.

**구현 클래스 이름 — `java.util.KeyValueHolder`.**

- **기대면 안 된다.** `Map.entry(k, v)` 의 계약은 "불변 `Map.Entry` 를 돌려준다"까지이고,\
  어떤 클래스인지는 구현의 자유다. `instanceof KeyValueHolder` 같은 코드는 쓰지 않는다.

**중첩 타입을 쓰는 다른 방법**

| 방법 | 형태 |
|---|---|
| 단일 타입 import | `import java.util.Map.Entry;` → `Entry<K,V>` |
| 바깥 타입만 import | `import java.util.Map;` → **`Map.Entry<K,V>`** (점으로 접근) |
| 풀네임 | `java.util.Map.Entry<K,V>` |

- 실무에서는 **두 번째(`Map.Entry`)가 가장 흔하다** — `Entry` 라는 단순 이름이 너무 흔해서다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex`(34-a) `javac` | 온디맨드 둘 충돌 → 쓰는 줄에서 `ambiguous` | 21 |
| `Ex`(34-b) | 단일 타입 import 가 온디맨드를 이긴다 | 21 |
| `Ex`(34-c) `javac` | 단일 타입 둘 충돌 → 선언 줄에서 에러 | 21 |
| `Ex`(34-si1) | static import(단일·온디맨드), 메서드·필드·인터페이스 static | 21 |
| `Ex`(34-si2) `javac` | static import 충돌 → `reference to max is ambiguous` | 21 |
| `Ex`(34-own) | 같은 패키지 타입이 온디맨드를 가린다 + `javap -c` | 21 |
| `Ex`(34-shadow) | 같은 패키지 타입이 **`java.lang`** 을 가린다 | 21 |
| `Ex`(34-sub) `javac` | `java.util.*` 로 `java.util.concurrent` 가 안 들어온다 | 21 |
| `Ex`(34-jv1/jv2) `javap -c` `javap -l` `javap -v` `cmp` | import 유무로 바이트코드 동일, `LineNumberTable` 만 차이, 상수 풀 69 로 동일 | 21 |
| `Ex`(34-mod) `javac` | 모듈 import — **21·17 에서 `'.' expected`**, **25 에서 플래그 없이 동작** | 17 · 21 · 25 |
| `Ex`(34-mod) `javac -Xlint:preview` | **프리뷰 경고 없음** → 정식 확인 | 25 |
| `Ex`(34-mod2/mod3) `javac` | 모듈 import 둘 충돌 → `ambiguous`, 단일 타입 import 로 해소 | 25 |
| `Ex`(34-nest) · `(34-nest2)` `javac` | 중첩 타입 import 와 `import static` 의 인터페이스 static 메서드, 온디맨드가 중첩 타입을 안 주는 것 | 21 |
| `Ex`(34-cnt) | `java.base`·`java.desktop` 의 unqualified export 패키지 수 | 21 (54/50) · 25 (58/51) |

- 프로그램 **15개**, 컴파일·실행 왕복 **22회**, `javap` **5회**(`-c` 3 · `-l` 1 · `-v` 1), `cmp` 1회.

**구현에 의존하는 항목**

| 항목 | 무엇에 의존하나 |
|---|---|
| 에러 메시지 문구 | javac 버전 |
| `LineNumberTable` 이 유일한 차이인 것 | `-g` 디버그 옵션 (기본값 기준) |
| 상수 풀 항목 수 69 | javac 구현 — **"두 쪽이 같다"만 의미가 있다** |
| export 패키지 수 54 / 58 | **JDK 버전** — 21 과 25 가 실제로 달랐다 |
| `unnamed module @...` 같은 해시 | 실행마다 다르다 |

**버전이 오르면 다시 돌려야 할 것**

- `java.base` 의 export 패키지 수(21→25 에서 이미 4 늘었다).
- 모듈 import 선언이 더 많은 곳(예: `import module` 의 전이 규칙)에 적용되는지.
- 에러 메시지 문구.

## 안 돌려 본 것

- **모듈 경로(`--module-path`)로 실행**했을 때 모듈 import 의 동작 — 이번 실행은 전부 클래스패스다.
- `module-info.java` 를 둔 **진짜 모듈 프로젝트** — 목록의 「뺀 것과 이유」대로 JPMS 자체는 이 주제 밖이다.
- **컴파일 시간**에 온디맨드 import 가 주는 영향 — 재지 않았다(주장도 하지 않았다).
- JDK 23 · 24 의 **프리뷰 시절** 모듈 import — 그 JDK 가 이 머신에 없다.
