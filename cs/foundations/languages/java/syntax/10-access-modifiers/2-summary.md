# java/syntax/10 — 접근 제어자: package-private·`protected` 의 실제 경계 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §6.6 Access Control](https://docs.oracle.com/javase/specs/jls/se21/html/jls-6.html) · [§6.6.2 Details on protected Access](https://docs.oracle.com/javase/specs/jls/se21/html/jls-6.html) · [§8.1.1 Class Modifiers](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) · [JEP 181: Nest-Based Access Control](https://openjdk.org/jeps/181)
> **실행 검증** — 이 문서의 모든 출력·에러 메시지는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 패키지 예제는 **17.0.13 · 21.0.5 · 25.0.1** 셋에서 다 돌려 **출력이 한 글자도 다르지 않음**을 확인했다.\
> 클래스 파일의 접근 플래그는 `javap -p` · `javap -v -p` 출력을 그대로 옮겼다.
> **버전** — 네 수준의 규칙은 Java 1.0 이래 같다. **nest 기반 접근 제어는 Java 11**(JEP 181)부터.\
> 모듈 시스템(JPMS, Java 9+)이 그 위에 한 층을 더 얹지만 **이 주제에서는 다루지 않는다**(목록에서 뺀 것이다).
> **범위** — **정보 은닉이 왜 필요한가**는 [`../../../../oop-basics/`](../../../../oop-basics/) §10~12 가 정본이다.\
> 여기는 **Java 의 네 수준이 각각 정확히 어디까지 열리나**만 다룬다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**접근 제어는 문 네 개짜리 집이 아니라, 동심원 네 겹이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 내 방 | `private` — 그 클래스(정확히는 nest) 안 |
| 우리 동네 | **package-private** — 같은 패키지 (기본값) |
| 우리 동네 + 내 자식이 이사 간 다른 동네 | `protected` |
| 온 세상 | `public` |
| 자식이 "아버지 물건"은 만져도 **남의 아버지 물건**은 못 만지는 규칙 | `protected` 의 실제 경계 |

- **제어자를 안 쓰면 `private` 이 아니라 "동네"다.**\
  이것이 가장 많이 틀리는 곳이다 — 기본값은 닫힘이 아니라 **동네 공개**다.
- `protected` 는 동네에 **자식 집 하나**를 더한 것이다.\
  다른 동네로 이사 간 자식도 **자기 것**은 볼 수 있다.
- ★ 그런데 그 자식은 **다른 집(다른 인스턴스)의 같은 물건은 못 본다.**\
  "내가 아버지에게 물려받은 내 것"만 볼 수 있다.

```text
네 겹의 동심원 — 안쪽이 좁다

  +-------------------------------------------------+
  |  public                                         |
  |  +-------------------------------------------+  |
  |  |  protected = 같은 패키지 + 하위 클래스      |  |
  |  |  +-------------------------------------+  |  |
  |  |  |  package-private (기본값)            |  |  |
  |  |  |  +-------------------------------+  |  |  |
  |  |  |  |  private (같은 nest 안)        |  |  |  |
  |  |  |  +-------------------------------+  |  |  |
  |  |  +-------------------------------------+  |  |
  |  +-------------------------------------------+  |
  +-------------------------------------------------+
```

**똑같은 구조로** Java 가 이렇게 동작한다: 동네 = 패키지, 집 = 클래스, 방 = nest.

실무에서 이게 물리는 자리는 **추상 클래스의 `protected` 메서드**다.\
"하위 클래스가 쓰라고 열어 뒀다"고 생각했는데, 다른 패키지의 하위 클래스가\
**같은 타입의 다른 객체**를 받아 그 메서드를 부르려 하면 컴파일이 안 된다.

> **패키지(package)** — 클래스들의 이름 공간. 디렉터리 구조와 `package` 선언으로 정해진다.\
> 예: `zoo.Animal` 과 `zoo.Neighbor` 는 같은 패키지, `farm.Dog` 는 다른 패키지다.

> **nest** — 같은 **최상위 클래스**에 속한 클래스들의 묶음(Java 11, JEP 181).\
> 예: `Ex` 와 `Ex.Inner` 는 같은 nest 라 서로의 `private` 멤버를 본다.\
> **같은 파일에 있는 두 최상위 클래스는 nest 가 다르다** — 파일이 아니라 최상위 클래스가 기준이다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 네 수준이 각각 **정확히 어디까지** 열리는가 — 다른 패키지의 하위 클래스까지 넣었을 때.
2. `protected` 가 **"하위 클래스면 다 된다"가 아니라면** 무엇인가.
3. `private` 의 경계는 클래스인가, 파일인가, nest 인가.

## 동작 방식

### (1) 네 수준을 네 자리에서 읽어 본다

**언제 쓰나** — "이 멤버를 저기서 볼 수 있나"를 판단할 때.

```java
// zoo/Animal.java
package zoo;
public class Animal {
    public    String pub  = "public";
    protected String prot = "protected";
              String pkg  = "package-private";
    private   String priv = "private";

    public String selfAll() { return pub + " / " + prot + " / " + pkg + " / " + priv; }
}
```

읽는 쪽 넷을 만든다 — 자기 자신 / 같은 패키지 / 다른 패키지의 하위 클래스 / 다른 패키지의 남.

```java
// zoo/Neighbor.java   (같은 패키지)
public static String read(Animal a) { return a.pub + " / " + a.prot + " / " + a.pkg; }

// farm/Dog.java       (다른 패키지, extends Animal)
public String readOwn() { return pub + " / " + prot; }

// farm/Outsider.java  (다른 패키지, 남)
public static String read(Animal a) { return a.pub; }
```

**실행 결과** (`app/Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
자기 자신에서      : public / protected / package-private / private
같은 패키지에서    : public / protected / package-private
다른 패키지 하위클래스: public / protected
다른 패키지 남      : public
```

```text
네 줄이 정확히 한 칸씩 줄어든다

  자기 자신        [ public ][ protected ][ package-private ][ private ]
  같은 패키지      [ public ][ protected ][ package-private ]
  다른 패키지 자식  [ public ][ protected ]
  다른 패키지 남    [ public ]
```

그림 해설 (한 단계씩):

- 위에서 아래로 **한 칸씩 줄어든다.** 동심원 그림이 그대로 출력에 나온다.
- **같은 패키지에서는 `protected` 도 보인다.** `protected` 는 package-private 을 **포함**한다.
- 다른 패키지의 하위 클래스는 `package-private` 을 **못 본다** — 상속했는데도 안 보인다.
- `private` 은 자기 자신에서만 보인다.

비용 — 없다. 전부 컴파일 타임 검사다. 클래스 파일에는 플래그만 남는다.

```text
javap -p zoo.Animal — 출력 그대로. 선언한 그대로가 남는다

public class zoo.Animal {
  public java.lang.String pub;
  protected java.lang.String prot;
  java.lang.String pkg;            <- 제어자가 없는 것이 package-private 이다
  private java.lang.String priv;
  public zoo.Animal();
  public java.lang.String selfAll();
}
```

### (2) `protected` 의 진짜 규칙 — "내 것"만이다

**언제 쓰나** — 다른 패키지에서 상속받은 클래스 안에서 `protected` 멤버를 건드릴 때.

같은 `Dog extends zoo.Animal` 안에서 **네 가지 표기**를 시험한다.

```java
package farm;
import zoo.Animal;
public class Dog extends Animal {
    public String readOwn()               { return prot; }          // (a) 내 것
    public String readOther(Animal other) { return other.prot; }    // (b) Animal 타입의 남
    public String readDog(Dog other)      { return other.prot; }    // (c) Dog 타입
    public String readPup(Puppy other)    { return other.prot; }    // (d) Dog 의 하위 타입
}
class Puppy extends Dog { }
```

**결과**

| 표기 | 컴파일 | 왜 |
|---|---|---|
| (a) `prot` (= `this.prot`) | **된다** | 수신자가 `this` — 당연히 `Dog` 다 |
| (b) `other.prot` where `other : Animal` | **안 된다** | 수신자 타입이 `Dog` 나 그 하위가 아니다 |
| (c) `other.prot` where `other : Dog` | **된다** | 수신자 타입이 `Dog` 다 |
| (d) `other.prot` where `other : Puppy` | **된다** | `Puppy` 는 `Dog` 의 하위다 |

(b) 의 에러는 이것이다.

```text
$ javac -d out zoo/*.java farm/*.java
farm/Dog.java:5: error: prot has protected access in Animal
        return other.prot;      // 하위 클래스인데 "다른 인스턴스"의 protected 를 본다
                    ^
1 error
```

```text
같은 Dog 클래스 안에서 갈린다

  Animal other  -->  other.prot    X    "남의 아버지 물건"
  Dog    other  -->  other.prot    O    "내 형제 것 = 내 종류의 것"
  Puppy  other  -->  other.prot    O    "내 자식 것도 내 종류"
  this          -->  prot          O
```

그림 해설 (한 단계씩):

- JLS §6.6.2.1 의 규칙: 다른 패키지에서 `protected` 인스턴스 멤버에 접근하려면\
  **접근식의 수신자 타입이 접근하는 클래스(또는 그 하위)여야 한다.**
- 그래서 **"하위 클래스면 다 된다"가 아니다.** "하위 클래스가 **자기 종류의 객체**에 대해서만" 이다.
- 형제 하위 클래스도 막힌다.

  ```text
  farm/Dog.java:5: error: prot has protected access in Animal
      public String peek(Dog d) { return d.prot; }   // 형제 하위 클래스의 protected
                                          ^
  1 error
  ```

  `Cat extends Animal` 이 `Dog` 의 `prot` 을 보려 한 것이다 — `Dog` 는 `Cat` 의 하위가 아니다.

비용 — 없다. 다만 **설계 비용**이 있다: `protected` 는 `equals`·복사 생성자처럼\
**같은 타입의 다른 인스턴스를 다루는 코드**에서 쓸 수 없다.

### (3) `private` 의 경계는 파일이 아니라 nest 다

**언제 쓰나** — 한 파일에 클래스를 여럿 둘 때, 또는 중첩 클래스를 쓸 때.

같은 파일의 **다른 최상위 클래스**는 못 본다.

```java
class Vault {
    private String secret = "비밀";
    private String reveal() { return secret; }
}
public class Ex {
    public static void main(String[] a) {
        Vault v = new Vault();
        System.out.println(v.secret + " / " + v.reveal());
    }
}
```

```text
$ javac Ex.java
Ex.java:8: error: secret has private access in Vault
        System.out.println("같은 파일의 다른 클래스에서 private 접근: " + v.secret + " / " + v.reveal());
                                                             ^
Ex.java:8: error: reveal() has private access in Vault
        System.out.println("같은 파일의 다른 클래스에서 private 접근: " + v.secret + " / " + v.reveal());
                                                                                ^
2 errors
```

**중첩 클래스는 본다.**

```java
public class Ex {
    private int x = 1;
    class Inner { int peek() { return x; } }
    // main: new Ex().new Inner().peek()
}
```

**실행 결과** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
중첩 클래스가 본 private x = 1
```

```text
javap -v -p 로 본 nest 관계 — 출력 그대로

  (Ex 쪽)        NestMembers:
                   Ex$Inner
  (Ex$Inner 쪽)  NestHost: class Ex
```

그림 해설 (한 단계씩):

- 경계는 **파일이 아니라 nest** — 같은 **최상위 클래스**에 속하느냐다.
- `Vault` 와 `Ex` 는 같은 파일이지만 **각각 최상위 클래스**라 nest 가 다르다.
- `Ex` 와 `Ex$Inner` 는 `NestHost`/`NestMembers` 속성으로 묶여 있어 서로의 `private` 을 **직접** 본다.
- Java 11 이전에는 컴파일러가 `access$000` 같은 **합성 접근자 메서드**를 끼워 넣었다.\
  JEP 181 이 그 우회를 없앴다 — **소스 의미는 그때나 지금이나 같다.**

비용 — Java 11+ 에서는 없다(직접 접근). 그 이전에는 접근자 메서드 하나씩.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다.

### 네 수준 표

| 제어자 | 같은 클래스(nest) | 같은 패키지 | 다른 패키지 하위 클래스 | 그 외 |
|---|---|---|---|---|
| `private` | O | X | X | X |
| (없음) = package-private | O | O | X | X |
| `protected` | O | O | **O (조건부)** | X |
| `public` | O | O | O | O |

- ★ "조건부"가 이 표의 핵심이다 — 동작 방식 (2)의 수신자 타입 규칙.

### 어디에 붙일 수 있나

```java
private class Hidden { }        // 최상위에 private
protected class Half { }        // 최상위에 protected
```

```text
$ javac Ex.java
Ex.java:1: error: modifier private not allowed here
private class Hidden { }        // 최상위에 private
        ^
Ex.java:2: error: modifier protected not allowed here
protected class Half { }        // 최상위에 protected
          ^
2 errors
```

| 자리 | 쓸 수 있는 것 |
|---|---|
| 최상위 클래스·인터페이스 | `public` 또는 **(없음)** 둘뿐 |
| 멤버(필드·메서드·중첩 클래스) | 넷 다 |
| 인터페이스 멤버 | `public`(암묵)·`private`(9+). **`protected` 는 불가** |
| 지역 변수·파라미터 | 아무것도 못 붙인다 |

인터페이스에 `protected` 를 붙이면 막힌다.

```text
Ex.java:3: error: modifier protected not allowed here
    protected void bad();              // 인터페이스에 protected
                   ^
1 error
```

### 오버라이딩과 접근 수준

- 재정의할 때 **좁힐 수 없다**(09 편). 인터페이스 구현도 같다.

```text
Ex.java:3: error: run() in Impl cannot implement run() in Contract
    void run() { }                               // 기본값으로 줄였다
         ^
  attempting to assign weaker access privileges; was public
1 error
```

- 인터페이스 메서드는 **암묵적으로 `public`** 이므로, 구현은 반드시 `public` 이어야 한다.

## 어디서 틀리나

### 1. "아무것도 안 쓰면 `private`" 이라고 믿는다

- 기본값은 **package-private** 이다. 같은 패키지의 아무 클래스나 볼 수 있다.
- 동작 방식 (1)의 둘째 줄이 그 증거다 — `Neighbor` 가 `a.pkg` 를 읽었다.
- 특히 **테스트 코드가 같은 패키지**라 통과하고, 다른 패키지에서 쓰려는 순간 깨진다.

```text
farm/Bad.java:4: error: pkg is not public in Animal; cannot be accessed from outside package
    public static String read(Animal a) { return a.pkg; }   // 다른 패키지에서 기본값을
                                                  ^
1 error
```

- 방어: **의도한 것이면 주석으로 밝힌다.** 실수로 비워 둔 것과 구분이 안 된다.

### 2. `protected` 를 "하위 클래스 전용"으로 읽는다

- `protected` 는 **같은 패키지에도 열려 있다.** 이름과 달리 `package-private` 보다 **넓다.**
- 동작 방식 (1)의 둘째 줄 — `Neighbor` 가 `a.prot` 을 읽는다. 상속 관계가 없는데도.
- 그래서 "하위 클래스만 보게 하고 싶다"는 **Java 에 없는 수준**이다.\
  `sealed`(목록의 15번)나 패키지 분리로 우회해야 한다.

### 3. `protected` 멤버로 `equals`·복사를 쓰려 한다

동작 방식 (2)의 (b) 가 그것이다. 실제로 써 보면 이렇게 된다.

```java
// farm/Dog.java  —  다른 패키지의 하위 클래스
public class Dog extends Animal {
    public boolean sameAs(Object o) {
        Animal other = (Animal) o;
        return this.prot.equals(other.prot);     // equals 를 쓰려면 여기가 필요하다
    }
}
```

```text
$ javac -d out zoo/*.java farm/*.java
farm/Dog.java:7: error: prot has protected access in Animal
        return this.prot.equals(other.prot);     // equals 를 쓰려면 여기가 필요하다
                                     ^
1 error
```

- `this.prot` 은 통과하는데 **`other.prot` 에서만** 멈춘다. 에러 캐럿이 정확히 그 자리를 가리킨다.
- `equals`·복사 생성자·`compareTo` 는 전부 **같은 타입의 다른 인스턴스**를 다룬다.
- `protected` 필드는 그 자리에서 **못 쓴다**(수신자 타입이 `Dog` 가 아니라 `Animal`·`Object` 라서).
- 그래서 JDK 자신도 `Object.clone()` 이 `protected` 인데, 하위 클래스에서 **`public` 으로 넓혀** 공개한다.
- 방어: `protected` **필드**를 만들지 않는다. `protected` **메서드**로 열고, 필드는 `private` 으로 둔다.

### 4. `private` 이 파일 단위라고 믿는다

- 동작 방식 (3)의 `Vault` 예제가 그것이다 — **같은 파일인데 에러**다.
- 반대로 중첩 클래스는 **파일이 아무리 커도** 본다.
- 기준은 **최상위 클래스(nest)** 하나다.

### 5. `public` 메서드가 package-private 타입을 반환한다

```java
// zoo/Secret.java
package zoo;
class Secret { public String value = "비밀"; }     // package-private 클래스

// zoo/Gate.java
package zoo;
public class Gate { public static Secret open() { return new Secret(); } }
```

**컴파일은 된다.** 다른 패키지에서 받는 것도 된다.

```text
실행 결과 (farm/Use.java, JDK 21.0.5)
받기는 받았다: zoo.Secret@6d06d69c
```

그런데 **멤버를 건드리는 순간** 막힌다.

```text
farm/Use.java:6: error: Secret.value is defined in an inaccessible class or interface
        System.out.println(s.value);
                            ^
1 error
```

- `var s = Gate.open()` 은 되고 `s.value` 는 안 된다.\
  `toString()` 이 되는 이유는 그것이 **`Object` 의 `public` 메서드**라서다.
- 객체는 손에 들어왔는데 **아무것도 못 하는** 상태다. API 설계 실수의 전형이다.
- 방어: **`public` API 의 시그니처에 나오는 타입은 전부 `public`** 이어야 한다.\
  반환형·파라미터·던지는 예외 전부.

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 |
|---|---|
| 네 수준의 가시성 범위 | **언어 보장** — JLS §6.6 |
| `protected` 의 수신자 타입 조건 | **언어 보장** — JLS §6.6.2.1 |
| 기본값이 package-private 인 것 | **언어 보장** |
| 최상위 클래스에 `private`/`protected` 불가 | **언어 보장** — JLS §8.1.1 |
| `private` 접근에 **합성 접근자**(`access$000`)가 끼는지 | **구현 세부** — Java 11 이전에는 끼었고, nest 이후엔 안 낀다 |
| `NestHost`/`NestMembers` 속성 | **구현 세부**(클래스 파일 포맷) — 소스 의미는 그대로다 |

★ 중요한 구분: **접근 제어는 컴파일 타임 검사이고, JVM 의 검증도 별도로 한다.**\
그러나 **리플렉션은 그 검사를 우회할 수 있다**(`setAccessible(true)`).\
그래서 `private` 은 **안전 장치가 아니라 설계 도구**다 — 보안 경계가 아니다.\
리플렉션의 경계는 [**58번 주제**](../58-reflection/)가 정본이다.

## 언제 쓰고 언제 안 쓰나

| 쓸 것 | 안 쓸 것 |
|---|---|
| 기본은 **`private`**, 필요할 때만 넓힌다 | 일단 `public` 으로 열고 나중에 좁히기(깨진다) |
| 같은 패키지 협력 클래스 -> package-private | 제어자를 **실수로** 비워 두기 |
| 하위 클래스 확장점 -> `protected` **메서드** | `protected` **필드**(필드 숨김·`equals` 문제로 이어진다) |
| `public` API 시그니처의 타입은 전부 `public` | `public` 메서드가 package-private 타입을 반환 |

판단 규칙 세 줄.

- **넓히는 것은 언제든 되고 좁히는 것은 안 된다.** 그러니 좁게 시작한다.
- **`protected` 는 "하위 클래스 전용"이 아니다.** 패키지에도 열린다는 것을 잊지 않는다.
- **`private` 은 보안이 아니다.** 리플렉션이 뚫는다. 설계 의도를 적는 도구로 쓴다.

## 핵심 문장

- 수준은 **넷**이고 **기본값은 package-private** — "아무것도 안 쓰면 닫힘"이 아니다.
- `protected` = **같은 패키지 + 하위 클래스**. 이름과 달리 package-private 보다 **넓다.**
- ★ 다른 패키지의 하위 클래스는 `protected` 멤버를 **자기 종류의 객체에 대해서만** 쓸 수 있다(JLS §6.6.2.1).\
  그래서 `equals`·복사에서 `protected` 필드를 못 쓴다.
- `private` 의 경계는 파일이 아니라 **nest**(같은 최상위 클래스) 다.
- 최상위 클래스에는 `public` 과 **(없음)** 둘뿐이고, 인터페이스 멤버에는 `protected` 를 못 쓴다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 10번)
- [`../../../../oop-basics/`](../../../../oop-basics/) — **정보 은닉이 왜 필요한가는 거기**(§10 C++ 접근 제어, §11 파이썬 네임 맹글링, §12 프로퍼티).\
  ★ 그쪽은 「감추는 이유」와 「파이썬은 사실상 못 막는다」까지, 여기는 **「Java 는 네 수준으로 실제로 막고, 그 경계가 정확히 어디인가」**부터다
- [`../09-inheritance-overriding/`](../09-inheritance-overriding/) — **재정의할 때 접근을 좁힐 수 없다**는 규칙이 그쪽에 있다.\
  `protected` 필드가 필드 숨김 사고의 전제 조건이라는 것도
- [`../06-initialization-order/`](../06-initialization-order/) — package-private 클래스의 기본 생성자도 package-private 이다
- [**11번 주제**](../11-interfaces-default-methods/)(인터페이스) — 인터페이스 멤버의 암묵적 `public` 과 `private` 메서드(9+)
- [**12번 주제**](../12-nested-classes/)(중첩 클래스) — nest 의 구성원이 어떻게 정해지나
- [**15번 주제**](../15-sealed-classes/)(`sealed`) — "하위 클래스를 내가 정한 것만" 이라는, 접근 제어로는 안 되는 제약
- [**58번 주제**](../58-reflection/)(리플렉션) — **`setAccessible` 이 이 경계를 어디까지 뚫나**가 그쪽 정본

## 용어 풀이

- **접근 제어자(access modifier)** — `public`·`protected`·`private` 과 **아무것도 안 쓴 상태**(package-private).
- **package-private** — 제어자를 안 썼을 때의 **기본값**. 같은 패키지에서만 보인다. `default` 라고도 부르지만 키워드가 아니다.
- **패키지(package)** — 클래스의 이름 공간. 하위 패키지는 **다른 패키지**다(`zoo` 와 `zoo.birds` 는 남남).
- **nest / NestHost / NestMembers** — 같은 최상위 클래스에 속한 클래스 묶음과 그것을 기록한 클래스 파일 속성(Java 11).
- **합성 접근자(synthetic accessor)** — Java 11 이전에 중첩 클래스의 `private` 접근을 위해 컴파일러가 만들던 메서드.
- **수신자 타입(qualifying type)** — `x.m()` 에서 `x` 의 **선언 타입**. `protected` 규칙이 이것을 본다.
- **리스코프 치환 원칙** — 재정의할 때 접근을 좁히지 못하게 하는 근거.
- **`setAccessible(true)`** — 리플렉션으로 접근 검사를 끄는 호출. `private` 이 보안 경계가 아닌 이유.

## 더 들어가면

- **모듈 시스템(JPMS, Java 9+)이 다섯 번째 층을 얹는다.**\
  `module-info.java` 가 `exports` 하지 않은 패키지는 `public` 이어도 밖에서 못 쓴다.\
  이 목록은 모듈을 뺐으므로 다루지 않지만, "`public` 인데 안 보인다"의 원인이 이것일 수 있다.
- **`protected` 의 수신자 타입 규칙은 `static` 멤버에는 적용되지 않는다.**\
  `static` 은 수신자가 없기 때문이다. 다른 패키지의 하위 클래스에서 `Animal.shared()` 로도, 그냥 `shared()` 로도 쓸 수 있다\
  (`10/e9b`, JDK 21.0.5 에서 컴파일 통과 확인).
- **`Object.clone()` 이 `protected` 인 이유**가 이 규칙의 실물 사례다.\
  아무나 복제하지 못하게 막되 하위 클래스가 `public` 으로 넓혀 공개하도록 설계한 것이다.
- **package-private 클래스는 라이브러리 내부 구현을 감추는 표준 수단**이다.\
  `java.util` 의 `Collections$UnmodifiableList` 가 그렇다 — `javap -p` 로 열어 보면 `public` 이 없는 package-private 클래스이고,\
  밖에서는 `List` 인터페이스로만 보인다.
