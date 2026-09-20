# java/syntax/29 — 람다: 문법·변수 캡처·`this` 의 의미 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [**11번 주제**](../11-interfaces-default-methods/)(인터페이스 `default`/`static` 메서드). 람다가 들어갈 타입이 무엇인지 먼저 본다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **무엇이 출력되고 무엇이 컴파일 에러인지**를 맞힐 수 있는지를 묻는다.
> 5·6번은 「무엇이 에러인가」를 묻는다. 에러 메시지의 **첫 줄**까지 말해 보라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 컴파일하면 클래스 파일이 몇 개 나오나 (예측)

```java
public class Ex {
    public static void main(String[] args) {
        int captured = 42;
        Supplier<String> noCapture  = () -> "상수";
        Supplier<String> yesCapture = () -> "값 " + captured;
        Supplier<String> anon = new Supplier<String>() {
            public String get() { return "값 " + captured; }
        };
    }
}
```

- `javac Ex.java` 뒤 `ls *.class` 의 출력은 무엇인가?
- 람다 둘은 각각 어떤 클래스 파일이 되는가?
- 람다 자리에 `new` 가 아니라 무엇이 컴파일되는가?
- 그 명령이 첫 실행에서 부르는 메서드는 무엇인가?

### 2. 캡처 유무에 따라 합성 메서드가 어떻게 달라지나 (예측)

```java
// 위와 같은 프로그램. javap -c -p Ex.class 의 끝부분
```

- 컴파일러가 만든 합성 메서드는 몇 개이며 이름은 무엇인가?
- 캡처 **없는** 람다의 합성 메서드 시그니처는 무엇인가?
- 캡처 **있는** 람다의 합성 메서드 시그니처는 무엇인가?
- 그 차이가 「캡처는 값 복사」에 대해 무엇을 말해 주는가?
- 같은 값을 익명 클래스는 어디에 담는가?

### 3. `this` 는 각각 무엇인가 (예측)

```java
public class Ex {
    private String name = "바깥 Ex 인스턴스";
    public String toString() { return name; }
    void run() {
        Runnable lam  = () -> System.out.println(this + " / " + this.getClass().getName());
        Runnable anon = new Runnable() {
            private String name = "익명 클래스 자기 자신";
            public String toString() { return name; }
            public void run() { System.out.println(this + " / " + this.getClass().getName()); }
        };
        lam.run(); anon.run();
    }
}
```

- 람다 쪽 출력은 무엇인가?
- 익명 클래스 쪽 출력은 무엇인가?
- 익명 클래스 안에서 바깥 `name` 에 닿으려면 어떻게 쓰는가?
- 람다 안에서 바깥 `name` 을 가리는 방법이 있는가?
- 람다 객체 자신의 클래스 이름과 람다 안의 `this.getClass()` 는 같은가?

### 4. 캡처 뒤에 바꿀 수 있는 것은 무엇인가 (예측)

```java
int local = 10;  int[] box = {1000};   // field 는 인스턴스 필드, staticField 는 static
Supplier<String> s = () -> "지역 " + local + " / 필드 " + field
                         + " / static " + staticField + " / 배열칸 " + box[0];
System.out.println(s.get());
field = 2;  staticField = 200;  box[0] = 2000;
System.out.println(s.get());
```

- 두 줄의 출력은 각각 무엇인가?
- 넷 중 무엇이 바뀌고 무엇이 안 바뀌는가?
- 필드가 바뀌는 이유는 무엇인가 — 람다가 필드의 무엇을 캡처했는가?
- `StringBuilder sb` 를 캡처한 뒤 `sb.append(...)` 하면 람다가 보는 값은 바뀌는가?

### 5. 어느 줄이 컴파일 에러인가 (경계)

```java
// (A) int count = 0; Supplier<Integer> s = () -> count; count = 1;
// (B) int count = 0; Supplier<Integer> s = () -> { count++; return count; };
// (C) static void main(...) { Supplier<String> s = () -> this.toString(); }
// (D) String msg = "바깥"; Supplier<String> s = () -> { String msg = "람다 안"; return msg; };
// (E) (D) 를 익명 클래스로 바꾼 것
```

- 다섯 중 컴파일되는 것은 무엇인가?
- (A)의 에러 메시지는 무엇이며, **어느 줄**을 가리키는가?
- (B)에서 에러는 몇 개인가?
- (D)의 에러 메시지는 무엇이며, 그것이 람다의 스코프에 대해 무엇을 말하는가?
- (E)가 되는 이유는 무엇인가?

### 6. 루프 변수를 캡처하면 (예측)

```java
for (String s : List.of("가", "나", "다")) subs.add(() -> s);          // (A)
for (int i = 0; i < 3; i++)               subs.add(() -> "" + i);      // (B)
for (int i = 0; i < 3; i++) { int c = i;  subs.add(() -> "" + c); }    // (C)
```

- (A)·(B)·(C) 중 컴파일되는 것은 무엇인가?
- (A)가 되는 이유는 무엇인가?
- (C)가 되는 이유는 무엇인가?
- 세 개 다 컴파일된다면 출력은 각각 무엇인가?

### 7. 스택트레이스에 무엇이 뜨나 (연결)

- 람다 안에서 예외가 나면 스택트레이스에 어떤 이름이 뜨는가?
- 같은 코드를 익명 클래스로 쓰면 어떤 이름이 뜨는가? 그 이름이 두 줄 나오는 이유는 무엇인가?
- 메서드 참조로 쓰면 어떤 이름이 뜨는가?
- 람다 객체 자신의 클래스(`Ex$$Lambda/0x...`)는 스택트레이스에 나오는가?
- 셋 중 디버깅에 가장 유리한 것은 무엇이며 그 이유는 무엇인가?

### 8. 람다를 `==` 로 비교하면 (경계)

- 캡처 없는 람다식을 두 번 평가해 얻은 두 객체는 `==` 가 참인가?
- 캡처 있는 람다식을 **같은 값으로** 두 번 평가하면 `==` 는 어떤가? `equals` 는?
- 그 결과는 **보장**인가 구현 세부인가 — 근거 문서는 무엇인가?
- 리스너를 `remove(x -> ...)` 로 해제하려 하면 무슨 일이 일어나는가?
- 람다 객체로 `synchronized` 를 걸어도 되는가?

### 9. 람다를 직렬화하면 (경계)

- `Supplier<String> s = () -> "안녕";` 을 `writeObject` 하면 무슨 예외가 나는가?
- 직렬화하려면 타깃 타입에 무엇이 필요한가?
- 직렬화된 바이트 안에 들어가는 클래스와 그 필드 이름들은 무엇인가?
- 직렬화 가능 람다의 합성 메서드 이름은 보통 람다와 어떻게 다른가?
- 그래서 무엇이 깨지는가?

### 10. `this` 를 캡처한 람다의 합성 메서드 (왜)

- 필드를 쓰는 람다의 합성 메서드에는 `static` 이 붙는가?
- 그 본문의 `aload_0` 은 무엇인가?
- 호출 자리의 `invokedynamic` 서술자는 캡처 없는 쪽과 어떻게 다른가?
- 그 람다를 오래 사는 자료구조에 넣으면 무엇이 같이 사는가?

### 11. 언제 익명 클래스로 돌아가야 하나 (연결)

- 람다로 쓸 수 없는 경우를 세 가지 대라.
- 익명 클래스를 람다로 기계적으로 바꾸면 안 되는 이유는 무엇인가?
- 본문이 길어질 때 권하는 것은 무엇인가?
- 세 JDK(17·21·25)에서 **달랐던** 것은 무엇이며, 그래서 무엇에 기대지 말아야 하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
