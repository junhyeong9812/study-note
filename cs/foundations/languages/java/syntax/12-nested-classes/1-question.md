# java/syntax/12 — 중첩 클래스: static nested·inner·지역·익명 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **클래스 파일에 무엇이 생기는지**를 맞힐 수 있는지 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 종류를 한 파일에 넣으면 클래스 파일이 몇 개 생기는가 (예측)

```java
public class Ex {
    private String name = "바깥";
    static class Nested { String show() { return "Nested"; } }
    class Inner { String show() { return "Inner -> " + name; } }

    String localAndAnon(int seed) {
        int captured = seed * 10;
        class Local { String show() { return "Local -> " + name + " / captured=" + captured; } }
        Runnable anon = new Runnable() {
            public void run() { System.out.println("Anon  -> " + name + " / captured=" + captured); }
        };
        anon.run();
        return new Local().show();
    }
    // main: Nested · Inner · localAndAnon(4) 를 차례로 쓰고
    //       마지막에 main 안에서 익명 Runnable 하나와 람다 하나를 더 만든다
}
```

- `javac` 가 만드는 `.class` 파일은 몇 개이고 이름은 각각 무엇인가?
- 람다는 몇 개의 클래스 파일을 만드는가?
- 지역 클래스와 익명 클래스의 이름 규칙은 어떻게 다른가?
- `Inner` 를 `main` 에서 만들려면 어떤 문법을 써야 하는가?

### 2. `javap -p` 로 열면 어느 클래스에 무슨 필드가 있는가 (예측)

1번의 프로그램을 컴파일하고 `javap -p Ex$Nested Ex$Inner Ex$1Local Ex$1` 을 돌렸다.

- 네 클래스 중 **필드가 하나도 없는 것**은 무엇인가?
- `Ex$Inner` 에 있는 필드는 무엇이고 그 타입은 무엇인가?
- `Ex$1Local` 과 `Ex$1` 에는 필드가 **몇 개** 보이는가?
- `Ex$Inner` 의 생성자 시그니처는 무엇인가 — 소스에는 생성자를 안 썼는데?

### 3. `this$0` 는 생성자의 어디에서 대입되는가 (왜)

```text
  Ex$Inner(Ex);
    Code:
       0: aload_0
       1: aload_1
       2: putfield      #1     // Field this$0:LEx;
       5: aload_0
       6: invokespecial #7     // Method java/lang/Object."<init>":()V
       9: return
```

- 이 바이트코드에서 `super()` 호출은 몇 번 줄인가?
- `this$0` 대입이 `super()` **앞**에 있다 — 소스 규칙("생성자의 첫 문장은 `super()`")과 모순 아닌가?
- 왜 이 순서여야 하는가? (힌트: [**06번 주제**](../06-initialization-order/))
- `Ex.this.name` 이라고 쓴 것과 그냥 `name` 이라고 쓴 것의 바이트코드는 다른가?

### 4. 지역 변수를 캡처한 뒤 바꾸면 (경계)

```java
public class Ex {
    void run() {
        int count = 0;
        class Local { void show() { System.out.println(count); } }
        count = 1;
        new Local().show();
    }
}
```

- 이 코드는 컴파일되는가? 안 된다면 에러 메시지는 무엇인가?
- 에러가 가리키는 줄은 `count = 1;` 인가, `count` 를 읽는 줄인가 — 그리고 왜 그쪽인가?
- 어느 한 줄만 지우면 통과하는가?
- 같은 값을 **필드**에 담으면 왜 이 제약을 안 받는가?

### 5. `static` 메서드 안의 지역 클래스 (예측)

```java
public class Ex {
    private String field = "바깥 필드";
    static void inStatic()   { int n = 1; class L { void go() { /* n 만 쓴다 */ } } new L().go(); }
    void        inInstance() { int n = 2; class L { void go() { /* n 과 field 를 쓴다 */ } } new L().go(); }
}
```

- `javap -p` 로 두 지역 클래스를 열면 필드 구성이 어떻게 다른가?
- `inStatic` 안의 `L` 에서 `field` 를 읽으면 어떻게 되는가?
- 같은 규칙이 익명 클래스에도 적용되는가 — `main` 안에서 만든 익명 클래스는?
- 이 차이를 정하는 것은 "바깥을 썼는가"인가, "어디에 선언했는가"인가?

### 6. 익명 클래스의 `this` 와 람다의 `this` (예측)

```java
public class Ex {
    private String id = "Ex 인스턴스";
    public String toString() { return id; }
    void compare() {
        Runnable anon   = new Runnable() { public void run() { System.out.println(this.getClass().getName()); } };
        Runnable lambda = () -> System.out.println(this.getClass().getName());
        anon.run();
        lambda.run();
    }
}
```

- 두 줄의 출력은 각각 무엇인가?
- 익명 클래스 안에서 바깥 인스턴스를 가리키려면 무엇이라고 써야 하는가?
- 익명 클래스를 람다로 바꾸는 리팩토링이 조용히 깨뜨리는 코드는 어떤 모양인가?
- `getDeclaredFields()` 로 두 객체의 필드를 찍으면 무엇이 보이는가?

### 7. 바깥을 하나도 안 쓰는 익명 클래스는 바깥을 붙잡는가 (예측)

```java
public class Ex {
    private String id;
    Runnable anonTask()   { return new Runnable() { public void run() { } }; }  // 바깥 안 씀
    Runnable lambdaTask() { return () -> { }; }                                 // 바깥 안 씀
    Runnable lambdaUsingField() { return () -> System.out.println(id); }        // 필드 씀
}
```

- `anonTask()` 가 돌려준 객체의 `getDeclaredFields()` 에는 무엇이 보이는가 — JDK 17 과 21 에서 각각?
- `lambdaUsingField()` 가 돌려준 객체에는 어떤 필드가 보이는가?
- `lambdaTask()` 를 두 번 불러 `==` 로 비교하면 무엇이 나오는가? `anonTask()` 는?
- 이 결과 중 **언어가 보장하는 것**은 몇 개인가?

### 8. 오래 사는 목록에 태스크를 넣으면 바깥이 수거되는가 (예측)

```java
static final List<Runnable> REGISTRY = new ArrayList<>();            // 오래 사는 전역 목록
static class Owner {
    final byte[] payload = new byte[8 * 1024 * 1024];                // 8MB
    int size() { return payload.length; }
    class UsingTask  implements Runnable { public void run() { int n = size(); } }  // 바깥 씀
    class UnusedTask implements Runnable { public void run() { } }                  // 바깥 안 씀
    static class NestedTask implements Runnable { public void run() { } }
}
// 태스크 하나를 REGISTRY 에 넣고 Owner 지역 변수를 버린 뒤 System.gc()
// WeakReference<Owner>.get() == null 로 수거 여부를 본다
```

- 세 태스크 각각에 대해 `Owner` 가 수거되는가 — JDK 21 에서?
- JDK 17 에서 달라지는 줄은 어느 것인가?
- 붙잡히는 것은 태스크가 쓰는 `size()` 뿐인가, `Owner` 객체 전체인가?
- 이 표를 "수거된다/안 된다"로 단정해도 되는가?

### 9. inner 클래스 안에 `static` 멤버를 두면 (경계)

```java
public class Ex {
    class Inner {
        static int COUNT = 0;
        static void touch() { COUNT++; }
    }
}
```

- `--release 15` 로 컴파일하면 어떤 에러가 나는가?
- 에러 메시지의 "only allowed in constant variable declarations" 는 무엇을 허용한다는 뜻인가?
- 몇 번 릴리스부터 통과하는가, 그리고 그 완화는 어느 기능을 들여오면서 따라온 것인가?
- `static class Nested` 안에서는 원래부터 되는가?

### 10. `private` 을 넘나드는 접근을 컴파일러가 어떻게 처리하는가 (왜)

- inner 클래스가 바깥의 `private` 필드를 그냥 읽는데, JVM 의 `private` 은 클래스 단위다 — 어떻게 가능한가?
- `--release 8` 로 컴파일하면 `javap -p` 에 어떤 메서드가 추가로 보이는가?
- `--release 21` 에서는 왜 그 메서드가 안 생기는가 — 어느 JEP 가 무엇을 바꿨는가?
- 그 합성 메서드가 있던 시절, 무엇이 의도치 않게 새어 나갔는가?

### 11. 무엇이 언어 보장이고 무엇이 구현 세부인가 (연결)

- `this$0` 이라는 **이름**은 어느 쪽인가?
- "바깥을 안 쓰면 참조를 안 남긴다"는 어느 쪽인가 — 그 근거는?
- "inner 는 바깥 인스턴스를 필요로 한다"는 어느 쪽이고, 무엇이 그것을 정하는가?
- `System.gc()` 뒤에 수거된 것을 "수거된다"로 적으면 무엇이 틀린가?

### 12. 어디에 무엇을 쓰나 (연결)

- 리스너·콜백을 만들 때 기본값을 `static` nested 로 두는 이유는 무엇인가?
- 이터레이터는 왜 inner 로 두는 경우가 많은가?
- 추상 메서드가 둘인 인터페이스를 그 자리에서 구현해야 하면 무엇을 쓰는가?
- 이중 중괄호 초기화(`new HashMap<>() {{ put(...); }}`)가 만드는 문제 셋은 무엇인가?
- 이 주제가 다루지 않는 것(람다 문법 전체 · GC 알고리즘)은 어느 문서가 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
