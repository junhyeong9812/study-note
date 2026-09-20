# java/syntax/11 — 인터페이스: `default`/`static`/`private` 메서드와 충돌 해소 (8+) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러 메시지는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 정상 실행되는 프로그램은 **17.0.13 · 21.0.5 · 25.0.1** 셋에서 다 돌려 출력이 같음을 확인했다.\
> 바이트코드와 멤버 목록은 `javap -c -p` · `javap -p` 출력을 그대로 옮겼다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `default` 는 무엇을 풀려고 들어왔나

**Java 7 까지** — 인터페이스에 메서드를 추가하면 **모든 구현체가 컴파일 에러**가 됐다.\
남이 만든 구현체까지 전부 깨지므로 **사실상 추가가 불가능**했다.

**`default` 가 푸는 방식** — 인터페이스가 **본문을 함께 준다.**\
구현체가 아무것도 안 해도 그 구현이 상속되므로, 추가해도 안 깨진다.

**`java.lang.Iterable` 의 증거** (`javap -p`, JDK 21.0.5)

```text
public interface java.lang.Iterable<T> {
  public abstract java.util.Iterator<T> iterator();
  public default void forEach(java.util.function.Consumer<? super T>);
  public default java.util.Spliterator<T> spliterator();
}
```

- 세 줄 중 **두 줄이 `default`** 다. 원래 계약은 `iterator()` 하나뿐이었다.

**Java 21 에서 `List` 에 얹힌 것들** (`javap -p java.util.List`)

```text
  public default void addFirst(E);
  public default void addLast(E);
  public default E getFirst();
  public default E getLast();
  public default E removeFirst();
  public default E removeLast();
  public default java.util.List<E> reversed();
```

- `SequencedCollection`(JEP 431, Java 21)이 `default` 로 얹힌 것이다.\
  **기존 `List` 구현체를 하나도 안 고치고** 새 API 를 추가했다 — 정확히 같은 수법이다.

### 2. 네 종류가 한 인터페이스에

**출력** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
g1.greet() = 안녕, 람다
g2.greet() = !!! 안녕, 자바 !!!
```

**왜 그런가**

```text
javap -c -p Greeter — 출력 그대로

interface Greeter {
  public abstract java.lang.String name();

  public default java.lang.String greet();
    Code:
       0: aload_0
       1: invokeinterface #1,  1            // InterfaceMethod prefix:()Ljava/lang/String;
       6: aload_0
       7: invokeinterface #7,  1            // InterfaceMethod name:()Ljava/lang/String;
      12: invokedynamic #10,  0             // InvokeDynamic #0:makeConcatWithConstants:(...)
      17: areturn

  public static Greeter of(java.lang.String);
  private java.lang.String prefix();
  private static java.lang.String lambda$of$0(java.lang.String);
}
```

- `String name();` 이라고만 썼는데 **`public abstract`** 가 붙어 있다 — 암묵적으로 붙는다.
- `greet()` 안의 호출은 **`invokeinterface`** 다. 수신자의 선언 타입이 인터페이스이기 때문이다.
- `g1` 은 람다로 만든 것이라 `Greeter.greet()` 의 기본 구현이 그대로 돈다.
- `g2` 는 `Loud` 가 재정의했고, 그 안에서 기본 구현을 다시 불렀다.

```text
javap -c -p Loud — 출력 그대로

  public java.lang.String greet();
    Code:
       0: aload_0
       1: invokespecial #9                  // InterfaceMethod Greeter.greet:()Ljava/lang/String;
```

- `Greeter.super.greet()` 는 **`invokespecial`** 이다 — 09 편의 `super.m()` 과 **같은 명령**이다.\
  다른 점은 대상이 `InterfaceMethod` 라는 것뿐이다.
- 클래스는 상위가 하나라 `super.` 로 충분하지만, 인터페이스는 여럿이라 **이름을 앞에 붙인다.**

### 3. 충돌 세 규칙

**출력** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
Resolved  : A+B
Specific  : B2(가장 구체적)
ClassWins : Base(클래스)
```

**`javap -p` 에는 `who()` 가 없다.**

```text
class ClassWins extends Base implements A {
  ClassWins();
}
```

```text
class Specific implements B,B2 {
  Specific();
}
```

- 둘 다 **생성자밖에 없다.** 브리지도 합성 메서드도 만들지 않는다.\
  컴파일러가 "어느 것이 이기는지"를 정해 두고, 호출은 런타임에 그쪽으로 간다.

**`class C implements A, B { }` 는 멈춘다.**

```text
Ex.java:3: error: types A and B are incompatible;
class C implements A, B { }                      // 둘 다 default 를 준다
^
  class C inherits unrelated defaults for who() from types A and B
1 error
```

**세 규칙의 순서**

```text
  1) 클래스가 인터페이스를 이긴다
       Base.who() 가 있으면 A.who() 는 고려되지 않는다
              |
              v  (클래스 쪽에 없으면)
  2) 더 구체적인 인터페이스가 이긴다
       B2 extends B 이면 B2.who() 가 B.who() 를 덮는다
              |
              v  (우열이 없으면)
  3) 컴파일 에러 — 내가 직접 재정의해야 한다
```

**왜 순서로 자동 결정하지 않는가**

- C++ 의 가상 상속이나 파이썬의 MRO 는 **선언 순서**로 결정한다.\
  그러면 `implements A, B` 와 `implements B, A` 의 **의미가 달라진다** — 읽는 사람이 알 수 없다.
- Java 는 **모호한 것은 사람에게 되돌린다.** 우열이 명확한 경우(2)만 자동으로 정한다.
- 해소 수단은 **직접 재정의**뿐이고, 그 안에서 `A.super.who()` 로 골라 쓴다.

### 4. `default` 와 `abstract` 가 만나면

**출력** (`javac Ex.java`, JDK 21.0.5)

```text
Ex.java:3: error: C is not abstract and does not override abstract method who() in IsAbstract
class C implements HasDefault, IsAbstract { }     // 한쪽은 default, 한쪽은 abstract
^
1 error
```

**왜 그런가**

- **기본 구현이 있는데도 에러다.** 컴파일러는 "빈칸이 남아 있다"고 말한다.
- 규칙: 상속된 같은 시그니처 중 **하나라도 `abstract` 면** 그 클래스는 그것을 구현해야 한다.\
  `abstract` 가 `default` 를 **무효화**한다.

**설계 수단으로 쓰면**

```java
interface Base   { default String who() { return "기본"; } }
interface Strict extends Base { @Override String who(); }   // 다시 abstract 로
```

```text
$ javac Ex.java        (class Impl implements Strict { } 를 두고)
Ex.java:3: error: Impl is not abstract and does not override abstract method who() in Strict
class Impl implements Strict { }
^
1 error
```

- 하위 인터페이스에서 같은 이름을 **`abstract` 로 재선언**하면\
  **"이것만은 반드시 직접 구현하라"**를 강제할 수 있다. `Base` 의 기본 구현이 있어도 소용없다.
- 실제로 JDK 가 쓰는 기법이다 — `Comparator` 가 `equals(Object)` 를 재선언해 둔 것도 같은 계열이다\
  (그쪽은 목적이 다르다 — 9번 참조).

### 5. `static` 인터페이스 메서드는 상속되나

**`Greeter.of()` 는 되고 `Impl.of()` 는 안 된다.**

```text
Ex.java:6: error: cannot find symbol
        Impl.of();         // 구현 클래스 이름으로는?
            ^
  symbol:   method of()
  location: class Impl
1 error
```

**왜 그런가**

| | 클래스의 `static` (09 편) | 인터페이스의 `static` |
|---|---|---|
| 상속되나 | **그렇다** | **아니다** |
| 하위에서 같은 이름을 선언하면 | **숨김**(hiding) | 아무 관계 없음 |
| 어떻게 부르나 | 어느 이름으로든 | **인터페이스 이름으로만** |

- **왜 이렇게 설계했겠는가**: 상속하게 두면 인터페이스를 여럿 구현할 때\
  같은 이름의 `static` 이 여러 개 내려와 **또 충돌**이 난다.\
  `default` 는 「클래스가 이긴다」로 풀 수 있지만 `static` 에는 그 사다리가 없다.
- 결과적으로 읽기에도 낫다 — `Greeter.of(...)` 는 **어디 것인지가 이름에 박혀 있다.**

### 6. `Object` 의 메서드를 `default` 로

**에러가 셋이다.**

```text
Ex.java:2: error: default method toString in interface Bad overrides a member of java.lang.Object
    default String toString() { return "인터페이스가 준 toString"; }
                   ^
Ex.java:3: error: default method equals in interface Bad overrides a member of java.lang.Object
    default boolean equals(Object o) { return true; }
                    ^
Ex.java:4: error: default method hashCode in interface Bad overrides a member of java.lang.Object
    default int hashCode() { return 0; }
                ^
3 errors
```

**왜 막는가**

- **「클래스가 인터페이스를 이긴다」**(3번의 규칙 1)에서 따라 나온다.
- 모든 클래스는 `Object` 를 상속한다 → `Object.toString()` 이 **항상** 클래스 계층에 있다\
  → 인터페이스의 `default toString()` 은 **어떤 경우에도 불리지 않는다.**
- 불릴 수 없는 코드를 쓰게 두면 사람이 착각한다. 그래서 **선언 자체를 막는다.**

**그래서 "인터페이스로 `toString` 을 공짜로 주기"는 불가능하다.**

- 대안은 둘 — **추상 클래스**를 쓰거나, 각 구현체가 직접 쓰거나(`record` 가 자동으로 만들어 준다).
- 인터페이스에 **`abstract` 로 재선언**하는 것은 된다(9번). 다만 구현을 주는 게 아니라 **강제하는** 것이다.
- 계약 자체는 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 가 정본이다.

### 7. 인터페이스 상수의 함정

**출력** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
Limits.MAX = 10
Impl.MAX   = 10
TABLE      = [99, 2, 3]
```

**왜 그런가**

- `Impl.MAX` 가 **읽힌다.** 상수는 구현 클래스 이름으로도 노출된다 — constant interface 의 실질적 해악이다.
- `TABLE[0] = 99` 가 막히지 않는 이유: **`final` 은 참조에 걸린 것**이다.\
  `TABLE` 변수에 다른 배열을 대입하는 것은 막히지만, **그 배열의 내용**은 아무나 바꾼다.

```text
javap -p -c Limits — 출력 그대로

interface Limits {
  public static final int MAX;

  public static final int[] TABLE;

  static {};
    Code:
       0: iconst_3
       1: newarray       int
       ...
      15: putstatic     #1                  // Field TABLE:[I
      18: return
}
```

- **`putstatic` 은 `TABLE` 에만 있다.**
- `MAX` 는 **컴파일 타임 상수**(`final` + 상수 식 + `int`)라 `<clinit>` 에 대입 코드가 없다.\
  `10` 이 호출부에 **박힌다**([06 편의 상수 접기](../06-initialization-order/)).
- 인터페이스에도 **`static {}` 이 있다** — 클래스 초기화가 똑같이 적용된다.
- `MAX` 와 `TABLE` 에 붙은 **`public static final`** 은 내가 안 썼는데 붙어 있다.

**상수는 어디에 두나**

- 관련된 값들의 묶음이면 **`enum`**.
- 단순 상수면 **`final class` 의 `static final`**(생성자를 `private` 으로).
- 인터페이스에는 두지 않는다 — 구현하면 상속돼 버린다.

### 8. 같은 이름의 상수를 둘에서

**출력** (`javac Ex.java`, JDK 21.0.5)

```text
Ex.java:4: error: reference to LIMIT is ambiguous
    int use() { return LIMIT; }     // 어느 LIMIT?
                       ^
  both variable LIMIT in X and variable LIMIT in Y match
1 error
```

**왜 그런가**

- **상수에는 「더 구체적인 것이 이긴다」가 없다.** `X` 와 `Y` 사이에 상속 관계가 없으면 그냥 모호하다.
- `default` 메서드와 다른 점이다 — 메서드에는 세 규칙이 있는데 필드에는 없다.\
  필드는 09 편에서 봤듯 **숨김(정적 결정)** 이라, "가장 구체적인 것" 이라는 개념 자체가 안 선다.
- 고치는 법: **이름을 붙인다.** `X.LIMIT` 또는 `Y.LIMIT`.
- 7번과 합쳐서 읽으면, **인터페이스에 상수를 두는 것이 왜 안티패턴인지**가 완성된다.

### 9. `@FunctionalInterface` 가 세는 것

**`F` 는 통과한다. `G` 만 거부된다.**

```text
Ex.java:8: error: Unexpected @FunctionalInterface annotation
@FunctionalInterface
^
  G is not a functional interface
    multiple non-overriding abstract methods found in interface G
1 error
```

**무엇을 세고 무엇을 안 세나**

| 세나 | 무엇 |
|---|---|
| **센다** | 추상 메서드 |
| 안 센다 | `default` 메서드 |
| 안 센다 | `static` 메서드 |
| 안 센다 | `private` 메서드 |
| 안 센다 | **`Object` 의 `public` 메서드를 재선언한 것** |

- `F` 는 `apply` 하나뿐이라 통과한다. `equals(Object)` 를 선언해 뒀는데도 세지 않는다.
- **JDK 안의 실물은 `java.util.Comparator`** 다.

  ```text
  $ javap java.util.Comparator | grep -i equals
    public abstract boolean equals(java.lang.Object);
  ```

  추상 메서드가 `compare` 와 `equals` 둘로 보이는데, `equals` 는 `Object` 의 것이라 세지 않아\
  **함수형 인터페이스로 성립한다.**
- `Comparator` 가 굳이 `equals` 를 재선언한 이유는 **javadoc 으로 계약을 덧붙이기 위해서**다.\
  JDK 21.0.5 의 `lib/src.zip` 에서 그 javadoc 을 열면 이렇게 적혀 있다.

  > Additionally, this method can return `true` *only* if the specified object is also\
  > a comparator and it imposes the same ordering as this comparator.

  4번의 "abstract 로 재선언"과 문법은 같고 목적이 다르다 — 이쪽은 강제가 아니라 **계약 문서**다.

### 10. `private` 인터페이스 메서드

**Java 9 부터다.** `--release 8` 로는 거부된다.

```text
Ex.java:1: error: private interface methods are not supported in -source 8
interface I { private void helper() { } private static void s() { } }
                                 ^
  (use -source 9 or higher to enable private interface methods)
1 error
```

**`private` 인스턴스 메서드는 `static` 메서드에서 부를 수 없다.**

```text
Ex.java:9: error: non-static method helper() cannot be referenced from a static context
    static String bad() { return helper(); }      // static 에서 private 인스턴스 메서드
                                 ^
1 error
```

- `private static` 은 `default` 에서도 `static` 에서도 부를 수 있다.

**무엇을 위해 쓰나** — `default` 메서드 여럿의 **공통부를 모으는 것**이다.

```java
interface Logger {
    void log(String m);
    default void info(String m)  { write("INFO", m); }
    default void error(String m) { write("ERROR", m); }
    private void write(String level, String m) { log("[" + level + "] " + m); }
    static Logger stdout() { return System.out::println; }
}
```

**출력** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
[INFO] 시작
[ERROR] 실패
```

- Java 8 에서는 이 공통부를 **`default` 로 빼야 했고**, 그러면 **공개 API 가 돼 버렸다.**\
  `protected` 를 쓸 수 없으니(10 편) 선택지가 없었다. Java 9 가 그것을 메웠다.

### 11. `default` 를 추가했는데 조용히 안 불린다

**출력** (`Ex.java`, JDK 21.0.5)

```text
x.describe() = Old 가 원래 갖고 있던 메서드
```

**왜 그런가**

- **경고도 에러도 없다.** 그냥 클래스 쪽이 불린다.
- 작동한 규칙은 **「클래스가 인터페이스를 이긴다」**(3번의 규칙 1)다.\
  `Old.describe()` 는 `Api.describe()` 를 **재정의한 것으로 취급**된다 — 시그니처가 같기 때문이다.
- `Old` 를 쓴 사람은 `describe()` 를 재정의할 의도가 전혀 없었다. 이름이 우연히 같았을 뿐이다.

**라이브러리 저자가 조심할 것**

- `default` 추가는 **이진 호환이고 소스 호환이지만, 의미 호환은 아닐 수 있다.**
- 흔한 이름(`get`·`size`·`close`·`describe`)을 `default` 로 추가하면\
  구현체 쪽에 이미 있던 동명 메서드가 **조용히 기본 구현을 가린다.**
- 방어: 이름을 구체적으로 짓고, 릴리스 노트에 **"이 이름을 이미 쓰고 있으면 그쪽이 이긴다"**를 명시한다.
- 또 하나 — **두 인터페이스가 같은 이름의 `default` 를 갖게 되면** 그 둘을 함께 구현하던 코드가\
  **재컴파일 시 깨진다**(3번의 규칙 3). `default` 추가가 남의 코드를 깨는 유일한 경로다.

### 12. 정본 경계

**`default` 가 왜 들어왔나**

- [`../../../../../../history/java/java-8.md`](../../../../../../history/java/java-8.md) 가 정본이다.\
  람다·스트림을 넣으려면 `Collection` 에 메서드를 추가해야 했다는 동기와 설계 논쟁이 그쪽이다.\
  여기는 **그래서 무엇을 쓰고 무엇이 막히나**만 다룬다.

**오버라이딩 규칙 자체**

- [`../09-inheritance-overriding/`](../09-inheritance-overriding/) 다.\
  `X.super.m()` 이 `invokespecial` 인 것도, 접근을 좁힐 수 없는 것도 그쪽 규칙의 적용이다.\
  11 이 더하는 것은 **인터페이스가 여럿일 때의 충돌 해소** 하나다.

**인터페이스 멤버의 암묵 `public` 과 `protected` 불가**

- [`../10-access-modifiers/`](../10-access-modifiers/) 다.\
  10 번 주제의 「인터페이스 멤버에는 `protected` 를 못 쓴다」가 없었다면\
  이 주제의 `private`(9+)이 왜 필요했는지 설명되지 않는다.

**`oop-basics` 의 추상 클래스와 어디서 갈리나**

- [`../../../../oop-basics/`](../../../../oop-basics/) §17 은 **`abc` 로 구현을 강제하는 것**까지 다룬다 — 개념이다.
- 여기서 갈린다.

| | `oop-basics` §17 | 이 주제 |
|---|---|---|
| 다루는 것 | 추상 메서드로 **구현을 강제**한다 | 인터페이스가 **구현을 제공**할 수도 있게 된 뒤의 규칙 |
| 언어 | 파이썬 | Java |
| 다중 상속 | 파이썬은 MRO 로 **자동 결정** | Java 는 우열이 없으면 **컴파일 에러** |
| `static` 상속 | 파이썬은 상속된다 | 인터페이스의 `static` 은 **안 된다** |

- 즉 그쪽은 **「추상화가 무엇인가」**, 여기는 **「Java 8 이 인터페이스에 본문을 허용하면서 생긴 규칙들」**이다.\
  ★ 이 주제의 값어치는 대부분 **다중 상속 충돌**에 있고, 그것은 파이썬과 해법이 정반대라 그 문서에 없다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `11/a/Ex` + `javap -c -p Greeter`·`Loud` | 네 종류 멤버 · 암묵 `public abstract` · `invokeinterface` · `X.super` = `invokespecial` | 17 · 21 · 25 (출력 동일) |
| `11/b/Ex` + `javap -p ClassWins`·`Specific` | 충돌 세 규칙 · 이긴 쪽에 메서드가 생기지 않음 | 17 · 21 · 25 (출력 동일) |
| `11/e2/Ex` | `inherits unrelated defaults for who()` | 21 |
| `11/e5/Ex` | `default` + `abstract` → `does not override abstract method` | 21 |
| `11/e1/Ex` | `static` 은 상속 안 됨 — `cannot find symbol` | 21 |
| `11/e3/Ex` | `Object` 메서드를 `default` 로 → 에러 3개 | 21 |
| `11/c/Ex` + `javap -p -c Limits` | 상수 함정 · `TABLE[0]=99` 통과 · `MAX` 에 `putstatic` 없음 | 17 · 21 · 25 (출력 동일) |
| `11/e4/Ex` | 같은 이름 상수 둘 — `reference to LIMIT is ambiguous` | 21 |
| `11/e6/Ex` | `@FunctionalInterface` 가 세는 것 · `G` 거부 | 21 |
| `11/e7/Ex` | `private` 인터페이스 메서드 — 21 통과 / `--release 8` 거부 | 21 |
| `11/e8/Ex` | `static` 에서 `private` 인스턴스 메서드 호출 불가 | 21 |
| `11/d/Ex` | `private` 로 `default` 둘의 공통부 뽑기 | 17 · 21 · 25 (출력 동일) |
| `11/f/Ex` | 기존 동명 메서드가 새 `default` 를 조용히 가림 | 21 |
| `11/g/Ex` | `abstract` 재선언으로 `default` 무효화 | 21 |
| `src.zip` 의 `Comparator.java` | `equals` 재선언의 javadoc 계약 | 21 |
| `javap -p java.lang.Iterable` | `forEach`·`spliterator` 가 `default` | 21 |
| `javap -p java.util.List` | `SequencedCollection` 메서드 7개가 `default` | 21 |
| `javap java.util.Comparator` | `equals(Object)` 를 선언해도 함수형 인터페이스 | 21 |

**안 돌려 본 것**

- **Java 7 이하에서 `default` 가 거부되는 것** — **안 돌려 봄**.\
  JDK 21 의 `javac` 가 `--release 7` 자체를 거부한다(`error: release version 7 not supported`).\
  확인한 버전 게이트는 **9(`private` 메서드)** 하나뿐이다.
- **`invokeinterface` 와 `invokevirtual` 의 실행 비용 차이** — **안 돌려 봄**. 명령이 다르다는 것만 확인했다.

**구현 의존 항목**

- 람다가 `invokedynamic` + `lambda$of$0` 로 컴파일되는 것은 **구현 세부**다(목록의 29번 주제).
- `javap` 의 오프셋·상수 풀 번호(`#n`)는 컴파일러 버전에 따라 달라질 수 있다.
- **암묵 제어자**(`public abstract`·`public static final`)와 **충돌 해소 세 규칙**은 언어 보장이라 바뀌지 않는다.

**버전이 오르면 다시 돌릴 것** — `javap -p java.util.List` 의 `default` 목록.\
새 릴리스가 인터페이스에 `default` 를 더 얹으면 1번의 근거가 늘어난다.
