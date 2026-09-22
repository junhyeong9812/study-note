# java/syntax/10 — 접근 제어자: package-private·`protected` 의 실제 경계 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러 메시지는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 패키지 예제는 **17.0.13 · 21.0.5 · 25.0.1** 셋에서 다 돌려 출력이 같음을 확인했다.\
> 클래스 파일 정보는 `javap -p` · `javap -v -p` 출력을 그대로 옮겼다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 네 자리에서 각각 몇 개가 보이나

**출력** (`app/Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
자기 자신에서      : public / protected / package-private / private
같은 패키지에서    : public / protected / package-private
다른 패키지 하위클래스: public / protected
다른 패키지 남      : public
```

**왜 그런가**

| 읽는 쪽 | 개수 | 보이는 것 |
|---|---|---|
| ① `Animal` 자신 | **4** | 전부 |
| ② `zoo.Neighbor`(같은 패키지) | **3** | `private` 만 빼고 |
| ③ `farm.Dog extends Animal` | **2** | `public`·`protected` |
| ④ `farm.Outsider` | **1** | `public` |

- **②는 상속 관계가 없는데 `prot` 이 보인다.** `protected` 는 package-private 을 **포함**하기 때문이다.\
  이름 때문에 "하위 클래스 전용"으로 읽기 쉬운데, 실제로는 package-private 보다 **넓다.**
- **③은 상속했는데 `pkg` 가 안 보인다.** 상속은 패키지 경계를 넘지 못한다.
- 네 줄이 **정확히 한 칸씩** 줄어드는 것이 동심원 구조의 실물이다.

```text
javap -p zoo.Animal — 출력 그대로

public class zoo.Animal {
  public java.lang.String pub;
  protected java.lang.String prot;
  java.lang.String pkg;            <- 제어자가 아예 없다. 이것이 package-private 이다
  private java.lang.String priv;
  public zoo.Animal();
  public java.lang.String selfAll();
}
```

- package-private 은 **키워드가 없다.** `javap` 에서도 빈칸으로 나타난다.

### 2. 기본값은 무엇인가

- 제어자를 안 쓰면 **package-private** 이다. 같은 패키지의 **아무 클래스나** 볼 수 있다.
- "안 쓰면 닫힘"이 틀린 이유: Java 의 기본값은 **닫힘이 아니라 동네 공개**다.\
  `private` 은 **명시적으로 써야** 얻는다.
- **테스트 코드에서 안 드러나는 이유**: 관례상 테스트는 **대상과 같은 패키지**에 둔다(`src/test/java` 의 같은 경로).\
  그래서 package-private 멤버가 테스트에서 전부 보이고, 테스트는 초록이다.\
  다른 패키지(또는 다른 모듈)에서 쓰려는 순간에야 깨진다.

```text
farm/Bad.java:4: error: pkg is not public in Animal; cannot be accessed from outside package
    public static String read(Animal a) { return a.pkg; }   // 다른 패키지에서 기본값을
                                                  ^
1 error
```

- 방어: **의도해서 비워 둔 것이면 주석으로 밝힌다.** 실수로 빠뜨린 것과 구분이 안 된다.

### 3. ★ `protected` 의 진짜 경계

**결과** (JDK 21.0.5)

| 표기 | 컴파일 | 왜 |
|---|---|---|
| (a) `prot` (= `this.prot`) | **된다** | 수신자가 `this` — `Dog` 다 |
| (b) `other.prot` where `other : Animal` | **안 된다** | 수신자 타입이 `Dog` 나 그 하위가 아니다 |
| (c) `other.prot` where `other : Dog` | **된다** | 수신자 타입이 `Dog` 다 |
| (d) `other.prot` where `other : Puppy` | **된다** | `Puppy` 는 `Dog` 의 하위다 |

(b) 의 에러.

```text
farm/Dog.java:5: error: prot has protected access in Animal
        return other.prot;      // 하위 클래스인데 "다른 인스턴스"의 protected 를 본다
                    ^
1 error
```

**한 문장 규칙** (JLS §6.6.2.1)

> 다른 패키지에서 `protected` **인스턴스** 멤버에 접근하려면,\
> 접근식의 **수신자 타입이 접근하는 클래스 자신(또는 그 하위 타입)** 이어야 한다.

- 그래서 **"하위 클래스면 다 된다"가 아니라 "하위 클래스가 자기 종류의 객체에 대해서만"** 이다.

**형제 하위 클래스도 막힌다.**

```text
farm/Dog.java:5: error: prot has protected access in Animal
    public String peek(Dog d) { return d.prot; }   // 형제 하위 클래스의 protected
                                        ^
1 error
```

- `Cat extends Animal` 안에서 `Dog` 의 `prot` 을 보려 한 것이다.\
  `Dog` 는 `Cat` 의 하위가 **아니므로** 규칙에 걸린다. 둘 다 `Animal` 의 자식이라는 것은 무관하다.

### 4. 그 규칙이 막아 버리는 코드

**출력** (`javac -d out zoo/*.java farm/*.java`, JDK 21.0.5)

```text
farm/Dog.java:7: error: prot has protected access in Animal
        return this.prot.equals(other.prot);     // equals 를 쓰려면 여기가 필요하다
                                     ^
1 error
```

**왜 그런가**

- 컴파일되지 **않는다.** 캐럿은 **`other.prot` 의 `prot`** 을 가리킨다.
- **`this.prot` 은 통과한다.** 수신자가 `this` 라 타입이 `Dog` 이기 때문이다.\
  같은 줄 안에서 하나는 되고 하나는 안 되는 것이다.
- 그래서 `equals`·복사 생성자·`compareTo` 처럼 **같은 타입의 다른 인스턴스**를 다루는 코드에서는\
  `protected` **필드**를 쓸 수 없다(다른 패키지의 하위 클래스인 경우).
- 우회는 셋이다.
  1. `protected` **접근자 메서드**를 만든다 — 메서드도 같은 규칙이지만, 상위 클래스에 `public` 게터를 두면 된다.
  2. 같은 패키지에 둔다.
  3. 애초에 `protected` 필드를 만들지 않는다.

**`Object.clone()` 관용구**

```text
$ javap -p java.lang.Object | grep clone
  protected native java.lang.Object clone() throws java.lang.CloneNotSupportedException;

$ javap java.util.ArrayList | grep clone
  public java.lang.Object clone();
```

- `Object.clone()` 은 `protected` 라 아무나 못 부른다.
- 복제를 지원하는 클래스는 **`public` 으로 넓혀 재정의**한다(09 편 — 넓히는 것은 허용된다).
- `ArrayList` 가 그렇게 한 실물이다. **설계 의도가 "하위 클래스가 열지 말지 정하라"** 인 것이다.

### 5. `private` 의 경계는 어디인가

**같은 파일인데 컴파일되지 않는다.**

```text
Ex.java:8: error: secret has private access in Vault
        System.out.println("같은 파일의 다른 클래스에서 private 접근: " + v.secret + " / " + v.reveal());
                                                             ^
Ex.java:8: error: reveal() has private access in Vault
        System.out.println("같은 파일의 다른 클래스에서 private 접근: " + v.secret + " / " + v.reveal());
                                                                                ^
2 errors
```

**중첩 클래스는 본다.**

```text
실행 결과 (Ex.java, JDK 21.0.5 — 17·25 동일)
중첩 클래스가 본 private x = 1
```

**왜 그런가**

- 기준은 **파일도 클래스도 아닌 nest** — 같은 **최상위 클래스**에 속하느냐다.
- `Vault` 와 `Ex` 는 같은 파일이지만 **각각 최상위 클래스**라 nest 가 다르다.
- `Ex` 와 `Ex$Inner` 는 같은 nest 다.

```text
javap -v -p 로 확인 — 출력 그대로

  (Ex 쪽)        NestMembers:
                   Ex$Inner

  (Ex$Inner 쪽)  NestHost: class Ex
```

- 봐야 할 속성은 **`NestHost`** 와 **`NestMembers`** 다(Java 11, JEP 181).

### 6. 어디에 붙일 수 있나

**최상위 클래스에 `private`·`protected`**

```text
Ex.java:1: error: modifier private not allowed here
private class Hidden { }        // 최상위에 private
        ^
Ex.java:2: error: modifier protected not allowed here
protected class Half { }        // 최상위에 protected
          ^
2 errors
```

- 최상위에는 **`public` 또는 (없음)** 둘뿐이다(JLS §8.1.1).\
  `private` 최상위 클래스는 아무도 못 쓰므로 의미가 없고, `protected` 는 기준이 될 "상위 클래스"가 없다.

**인터페이스 멤버에 `protected`**

```text
Ex.java:3: error: modifier protected not allowed here
    protected void bad();              // 인터페이스에 protected
                   ^
1 error
```

- 인터페이스 멤버는 `public`(암묵)이거나 `private`(Java 9+) 이다. 중간이 없다.

**인터페이스 메서드를 구현하면서 제어자를 안 쓰면**

```text
Ex.java:3: error: run() in Impl cannot implement run() in Contract
    void run() { }                               // 기본값으로 줄였다
         ^
  attempting to assign weaker access privileges; was public
1 error
```

- 인터페이스 메서드는 **암묵적으로 `public`** 이므로, 구현은 반드시 `public` 이어야 한다.\
  09 편의 "접근을 좁힐 수 없다"가 그대로 적용된다.

### 7. `public` 메서드가 감춰진 타입을 반환한다

**`var s = Gate.open();` 은 컴파일된다. 출력도 된다.**

```text
실행 결과 (farm/Use.java, JDK 21.0.5)
받기는 받았다: zoo.Secret@6d06d69c
```

**`s.value` 는 안 된다.**

```text
farm/Use.java:6: error: Secret.value is defined in an inaccessible class or interface
        System.out.println(s.value);
                            ^
1 error
```

**왜 그런가**

- `var` 는 타입 이름을 쓰지 않으므로 **받는 것까지는 된다.**
- `toString()` 이 되는 이유는 그것이 **`Object` 의 `public` 메서드**라서다. `Secret` 자신의 것이 아니다.
- 한 줄 요약: **객체는 손에 들어왔는데 아무것도 못 한다.**
- 방어: **`public` API 의 시그니처에 나오는 타입은 전부 `public`** 이어야 한다.\
  반환형·파라미터·`throws` 의 예외 타입·제네릭 인자까지 전부.
- 이 규칙의 반대편 활용이 **package-private 구현 클래스 + `public` 인터페이스**다.\
  `java.util.Collections$UnmodifiableList` 가 그렇게 돼 있다 — 타입은 감추고 `List` 로만 내보낸다.

### 8. `protected` 와 `static`

**부를 수 있다.** (`10/e9b`, JDK 21.0.5 — 컴파일 통과)

```java
package farm;
import zoo.Animal;
public class Dog extends Animal {
    public String useStatic() { return Animal.shared() + " / " + shared(); }
}
```

- `Animal.shared()` 로도, 상속받은 이름으로 `shared()` 로도 된다.
- **3번의 수신자 타입 규칙이 적용되지 않는 이유**: `static` 멤버에는 **수신자가 없다.**\
  JLS §6.6.2.1 의 조건 자체가 "인스턴스 멤버 접근식의 수신자 타입"에 대한 것이라 성립하지 않는다.
- 그래서 `protected static` 은 **"같은 패키지 + 모든 하위 클래스"** 로 단순하게 열린다.

### 9. `private` 은 보안인가

**리플렉션으로 읽고 쓸 수 있다.** (`10/d/Ex.java`, JDK 21.0.5)

```text
리플렉션으로 읽은 값: 비밀
리플렉션으로 바꾼 값: 바꿔치기
```

```java
Field f = Vault.class.getDeclaredField("secret");
f.setAccessible(true);
System.out.println("리플렉션으로 읽은 값: " + f.get(v));
```

**왜 그런가**

- 접근 제어는 **컴파일 타임 검사 + JVM 의 링크 시 검증**이고, 리플렉션은 그것을 **명시적으로 끄는** 경로다.
- 그러므로 `private` 은 **보안 경계가 아니다.** 설계 의도를 적는 도구다 —\
  "이것은 내부 구현이니 기대지 마라"를 컴파일러가 대신 말해 주는 것.
- **Java 11 이전**에는 중첩 클래스의 `private` 접근에 **합성 접근자 메서드**(`access$000` 같은 것)가 끼어 있었다.\
  JEP 181 의 nest 기반 접근 제어가 그 우회를 없애고 JVM 이 직접 허용하게 했다.\
  **소스 의미는 그때나 지금이나 같다** — 구현 세부만 바뀌었다.
- 무엇까지 뚫리는지(모듈이 막는 것 포함)는 [**58번 주제**](../58-reflection/)가 정본이다.

### 10. 설계 순서

**어느 수준에서 시작하는가**

- **`private` 에서 시작한다.**
- 이유는 비대칭이다 — **넓히는 것은 언제든 되고, 좁히는 것은 남의 코드를 깬다.**\
  09 편의 "재정의할 때 좁힐 수 없다"도 같은 방향이다.

**`protected` 필드 대 `protected` 메서드**

- **메서드를 고른다.** 필드를 `protected` 로 열면 셋이 따라온다.
  1. **필드 숨김** 사고 — 하위 클래스가 같은 이름을 다시 선언해도 경고가 없다(09 편).
  2. **`equals`·복사에서 못 쓴다** — 4번의 수신자 타입 규칙.
  3. **불변식을 지킬 수 없다** — 하위 클래스가 직접 쓰면 검증을 못 건다.

**"하위 클래스만"은 표현되는가**

- **Java 에 그런 수준은 없다.** `protected` 는 항상 패키지를 포함한다.
- 우회는 둘이다 — 패키지를 분리하거나(같은 패키지에 남을 안 둔다),\
  `sealed`([**15번 주제**](../15-sealed-classes/))로 **누가 하위 클래스가 될 수 있는지**를 제한한다.\
  다만 `sealed` 는 가시성이 아니라 **확장 가능성**을 막는 것이라 목적이 다르다.

### 11. 정본 경계

**정보 은닉이 왜 필요한가**

- [`../../../../oop-basics/`](../../../../oop-basics/) 가 정본이다 — §10 C++ 의 접근 제어, §11 파이썬 네임 맹글링, §12 프로퍼티 기법.

**그 언어에서는 왜 성립하지 않는가**

- 그 문서는 **파이썬**으로 쓰였고, 파이썬에는 **강제되는 접근 제어가 없다.**\
  `__balance` 는 `_Account__balance` 로 이름이 바뀔 뿐이라 "**원천적으로 막을 수 없다**"고 그 문서 자신이 적고 있다(§12).
- 그래서 이 주제의 규칙들 — 네 수준, `protected` 의 수신자 타입 조건, nest, 최상위 클래스 제약 — 은\
  **전부 Java 의 정적 검사에서만 나오는 것**이라 그쪽에 없다.
- 정리: **그쪽은 「왜 감추나」, 여기는 「Java 가 실제로 어디까지 막나」.**

**재정의할 때 접근을 좁힐 수 없다**

- [`../09-inheritance-overriding/`](../09-inheritance-overriding/) 가 정본이다. 6번의 인터페이스 구현 에러가 그 규칙의 적용이다.

**`setAccessible` 의 경계**

- [**58번 주제**](../58-reflection/)(리플렉션)다. 여기서는 **"뚫린다"는 사실**까지만 확인했다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `10/a` (`zoo`+`farm`+`app`, 5파일) | 네 자리에서 보이는 개수 4/3/2/1 | 17 · 21 · 25 (출력 동일) |
| `10/a` + `javap -p zoo.Animal` | package-private 은 제어자 없이 표시됨 | 21 |
| `10/e1` | 다른 패키지의 남이 `protected` — `has protected access` | 21 |
| `10/e2` | 다른 패키지에서 package-private — `is not public ... outside package` | 21 |
| `10/e3` | ★ 하위 클래스가 `Animal` 타입 인스턴스의 `protected` — 에러 | 21 |
| `10/e4` | `Dog`·`Puppy` 타입으로는 통과 | 21 |
| `10/e5` | 형제 하위 클래스(`Cat` → `Dog`) — 에러 | 21 |
| `10/e9` | `equals` 패턴에서 `other.prot` 만 에러 | 21 |
| `10/e9b` | `protected static` 은 다른 패키지 하위 클래스에서 통과 | 21 |
| `10/e6/Ex` | 최상위 `private`/`protected` — `modifier not allowed here` | 21 |
| `10/b/Ex` | 같은 파일의 다른 최상위 클래스에서 `private` — 에러 | 17 · 21 · 25 (동일) |
| `10/c/Ex` + `javap -v -p` | 중첩 클래스는 통과 · `NestHost`/`NestMembers` | 17 · 21 · 25 (출력 동일) |
| `10/e7/Ex` | 인터페이스에 `protected` — `modifier not allowed here` | 21 |
| `10/d(문법절)/Ex` | 인터페이스 구현에서 접근 좁히기 — `weaker access privileges` | 21 |
| `10/e8` (`zoo`+`farm`) | `public` 메서드가 package-private 타입 반환 — 받기는 됨, 멤버는 에러 | 21 |
| `10/d/Ex` (리플렉션) | `setAccessible(true)` 로 `private` 읽기·쓰기 | 21 |
| `javap -p java.lang.Object` / `javap java.util.ArrayList` | `clone()` 이 `protected` → `public` 으로 넓혀짐 | 21 |
| `javap -p java.util.Collections$UnmodifiableList` | package-private 구현 클래스의 실물 | 21 |

**안 돌려 본 것**

- **모듈 시스템(JPMS)이 얹는 층** — **안 돌려 봄**. 이 목록에서 모듈을 뺐으므로 다루지 않는다.
- **`setAccessible` 이 모듈 경계에서 막히는 경우** — **안 돌려 봄**. 58번 주제의 영역이다.

**구현 의존 항목**

- `NestHost`/`NestMembers` 속성은 **Java 11 이후**의 클래스 파일에만 있다.\
  그 이전 컴파일 결과에는 합성 접근자 메서드가 대신 들어간다. **소스 의미는 같다.**
- `zoo.Secret@6d06d69c` 의 해시 부분은 실행마다 달라진다.
- `javap` 의 출력 형식은 컴파일러 버전에 따라 달라질 수 있다. **접근 제어자 표기 자체**는 언어 규칙이다.
