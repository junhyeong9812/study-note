# java/syntax/10 — 접근 제어자: package-private·`protected` 의 실제 경계 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「어디까지 보이나」를 경계에서 묻는다** — 특히 **다른 패키지의 하위 클래스**에서.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 자리에서 각각 몇 개가 보이나 (예측)

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

읽는 쪽 넷: ① `Animal` 자신 ② `zoo.Neighbor` ③ `farm.Dog extends Animal` ④ `farm.Outsider`

- 넷이 각각 몇 개의 필드를 읽을 수 있는가?
- ②는 상속 관계가 없는데 `prot` 이 보이는가?
- ③은 상속했는데 `pkg` 가 보이는가?
- `javap -p zoo.Animal` 에서 package-private 필드는 어떻게 표시되는가?

### 2. 기본값은 무엇인가 (왜)

- 제어자를 안 쓰면 어느 수준인가?
- "안 쓰면 닫힘"이라는 직관이 왜 틀린가?
- 이 오해가 **테스트 코드에서 특히 안 드러나는** 이유는 무엇인가?

### 3. ★ `protected` 의 진짜 경계 (경계)

```java
package farm;
import zoo.Animal;
public class Dog extends Animal {
    public String readOwn()               { return prot; }          // (a)
    public String readOther(Animal other) { return other.prot; }    // (b)
    public String readDog(Dog other)      { return other.prot; }    // (c)
    public String readPup(Puppy other)    { return other.prot; }    // (d)
}
class Puppy extends Dog { }
```

- (a)~(d) 중 컴파일되는 것은 무엇이고 안 되는 것은 무엇인가?
- 안 되는 것의 에러 메시지는 무엇인가?
- JLS 가 정한 조건을 한 문장으로 말하면 무엇인가?
- `Cat extends Animal` 이 `Dog` 의 `prot` 을 읽으려 하면 어떻게 되는가?

### 4. 그 규칙이 막아 버리는 코드 (예측)

```java
package farm;
public class Dog extends zoo.Animal {
    public boolean sameAs(Object o) {
        Animal other = (Animal) o;
        return this.prot.equals(other.prot);
    }
}
```

- 컴파일되는가? 안 된다면 에러 캐럿은 **어느 토큰**을 가리키는가?
- `this.prot` 과 `other.prot` 중 무엇이 문제인가?
- 그래서 `equals`·복사 생성자·`compareTo` 에서 `protected` **필드**를 쓸 수 있는가?
- `Object.clone()` 이 `protected` 인데도 쓸 수 있게 되는 관용구는 무엇인가?

### 5. `private` 의 경계는 어디인가 (예측)

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

- 같은 파일인데 컴파일되는가?
- 중첩 클래스(`class Inner` 안에서 바깥의 `private` 필드)는 어떤가?
- 두 경우를 가르는 기준은 파일인가 클래스인가 nest 인가?
- `javap -v -p` 로 그 관계를 확인하려면 어느 속성을 보는가?

### 6. 어디에 붙일 수 있나 (경계)

- 최상위 클래스에 `private` 을 붙이면?
- 최상위 클래스에 `protected` 를 붙이면?
- 인터페이스 멤버에 `protected` 를 붙이면?
- 인터페이스 메서드를 구현하면서 제어자를 안 쓰면?

### 7. `public` 메서드가 감춰진 타입을 반환한다 (예측)

```java
// zoo/Secret.java   package-private 클래스
package zoo;
class Secret { public String value = "비밀"; }

// zoo/Gate.java
package zoo;
public class Gate { public static Secret open() { return new Secret(); } }
```

- 다른 패키지에서 `var s = Gate.open();` 이 컴파일되는가?
- `System.out.println("받기는 받았다: " + s);` 는?
- `s.value` 는?
- 이 상황을 한 줄로 요약하면, 그리고 방어는 무엇인가?

### 8. `protected` 와 `static` (경계)

- 다른 패키지의 하위 클래스에서 상위의 `protected static` 메서드를 부를 수 있는가?
- 3번의 수신자 타입 규칙이 왜 여기에는 적용되지 않는가?

### 9. `private` 은 보안인가 (왜)

- 리플렉션으로 `private` 필드를 읽을 수 있는가?
- 그렇다면 `private` 은 무엇을 위한 도구인가?
- Java 11 이전에는 중첩 클래스의 `private` 접근에 무엇이 끼어 있었는가?

### 10. 설계 순서 (연결)

- 새 멤버를 만들 때 어느 수준에서 시작하는가, 왜인가?
- `protected` **필드**와 `protected` **메서드** 중 무엇을 고르고 왜인가?
- "하위 클래스만 보게 하고 싶다"는 Java 로 표현되는가?

### 11. 정본 경계 (연결)

- 정보 은닉이 **왜** 필요한가는 어느 문서가 정본인가?
- 그 문서가 다루는 언어에서는 이 주제의 규칙들이 왜 성립하지 않는가?
- 재정의할 때 접근을 좁힐 수 없다는 규칙은 어느 주제가 정본인가?
- `setAccessible` 의 경계는 어디를 보는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
