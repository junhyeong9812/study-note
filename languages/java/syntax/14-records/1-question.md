# java/syntax/14 — `record` (16+): 컴팩트 생성자·불변 계약·못 하는 것 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제는 **예측형과 계약형이 섞여 있다** — 출력을 맞히는 문항(1~6)과
> **「javadoc 이 요구하는 조항을 세는」** 문항(7), **「어기면 어떤 에러가 나오나」** 문항(8)이 따로 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 한 줄이 만드는 멤버를 전부 세어라 (예측)

```java
public class Ex {
    record Point(int x, int y) { }
    // 리플렉션으로 getDeclaredMethods / getDeclaredFields / getDeclaredConstructors 를 전부 찍는다
}
```

- 메서드는 몇 개이고 각각 무엇인가?
- 필드는 몇 개이고 어떤 제어자가 붙는가?
- 생성자는 몇 개이고 접근 제어자는 무엇인가?
- `Point.class.getSuperclass()` 는 무엇을 돌려주는가?
- `toString()` 의 출력은 무엇인가?
- 자동 생성된 `equals` 에 붙는 제어자 중 **내가 직접 쓰면 사라지는 것**은 무엇인가?

### 2. 컴팩트 생성자가 무엇으로 끝나는가 (예측)

```java
record Range(int lo, int hi) {
    Range {
        if (lo > hi) throw new IllegalArgumentException("lo > hi: " + lo + " > " + hi);
        lo = Math.max(lo, 0);
    }
}
// System.out.println(new Range(-5, 10));
// new Range(9, 2);
```

- `new Range(-5, 10)` 의 출력은 무엇인가?
- 필드에 대입하는 문장을 하나도 안 썼는데 `lo` 가 왜 반영되는가?
- `new Range(9, 2)` 는 어떻게 되는가?
- `javap -c -p` 로 이 생성자를 열면 **마지막 네 줄**에 무엇이 있는가?

### 3. `record` 의 불변은 어디까지인가 (예측)

```java
record Order(String id, List<String> items) { }

List<String> src = new ArrayList<>(List.of("a", "b"));
Order o = new Order("#1", src);
System.out.println(o);
src.add("c");
System.out.println(o);
o.items().add("d");
System.out.println(o);
```

- 세 줄의 출력은 각각 무엇인가?
- 구멍은 몇 개이고 각각 어디인가?
- 이 record 를 `HashMap` 키로 쓰고 있었다면 무슨 일이 생기는가?
- 한 줄로 두 구멍을 동시에 막는 방법은 무엇인가?

### 4. 배열 컴포넌트 record 의 네 줄 (예측)

```java
record Buf(String name, int[] data) { }

Buf b1 = new Buf("x", new int[]{1, 2});
Buf b2 = new Buf("x", new int[]{1, 2});
System.out.println(b1);
System.out.println(b1.equals(b2));
System.out.println(b1.hashCode() == b2.hashCode());
Set<Buf> set = new HashSet<>(); set.add(b1); set.add(b2);
System.out.println(set.size());
```

- 네 줄의 출력은 각각 무엇인가?
- 이것은 `equals` **계약 위반인가**, 아닌가?
- 고치려면 몇 개의 메서드를 재정의해야 하며, 그중 잊기 쉬운 것은 무엇인가?
- `toString` 까지 고쳐야 하는 이유를 javadoc 의 어느 요구로 설명할 수 있는가?

### 5. 부동소수 컴포넌트 — 네 줄 중 무엇이 뒤집히나 (예측)

```java
record Temp(double celsius) { }

System.out.println(Double.NaN == Double.NaN);
System.out.println(new Temp(Double.NaN).equals(new Temp(Double.NaN)));
System.out.println(0.0 == -0.0);
System.out.println(new Temp(0.0).equals(new Temp(-0.0)));
```

- 네 줄의 출력은 각각 무엇인가?
- 원시 비교와 record 의 `equals` 가 갈리는 근거는 javadoc 의 어느 문장인가?
- 이 둘 중 **`equals` 계약을 구해 주는 쪽**은 어느 것인가?
- `-0.0` 이 코드에 리터럴로 없는데도 생기는 경로는 무엇인가?

### 6. 접근자만 방어 복사하면 (예측)

```java
record Buf (String name, int[] data) { }                              // 전부 자동
record Safe(String name, int[] data) {
    public int[] data() { return data.clone(); }                      // 접근자만 고쳤다
}
// 각각에 대해 r.equals(new R(r.name(), r.data())) 를 찍는다
```

- 두 줄의 출력은 각각 무엇인가?
- 둘 중 **javadoc 이 "must hold" 라고 못박은 불변식을 깨는 쪽**은 어느 것인가?
- "좋은 일을 한 쪽이 계약을 깬다"는 결과가 말하는 규칙은 무엇인가?
- 이 불변식이 깨지면 무엇이 같이 깨지는가?

### 7. `record` 가 대신 지켜 주는 계약을 세어 보라 (경계)

- `Record` 의 javadoc 이 **반드시 성립한다(invariant must hold)** 고 적은 조항은 몇 개이고 무엇인가?
- `Record.equals` 의 `@implSpec` 이 컴포넌트 동치를 판정하는 규칙은 **몇 갈래**이고 각각 무엇인가?
- `Record.toString` 이 일반 계약에 **더해서** 요구하는 것은 무엇인가?
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 의 `equals` 다섯 조항 중, `record` 가 **문제 자체를 없애 버린** 조항은 무엇이며 그 이유는 무엇인가?
- `record` 라도 **깨질 수 있는** 조항은 무엇인가?

### 8. 어기면 무엇이 출력되나 — 여섯 가지 (경계)

각각 컴파일이 되는가? 안 된다면 `javac` 가 뭐라고 하는가?

- `record` 본문에 `private int cached;` 라고 인스턴스 필드를 추가한다.
- `record Point(int x) extends Base { }` 라고 다른 클래스를 상속한다.
- `class Sub extends Point { }` 라고 `record` 를 상속한다.
- 컴팩트 생성자에 `this.x = Math.abs(x);` 라고 쓴다.
- 컴팩트 생성자와 표준 생성자 `Point(int x) { this.x = x; }` 를 **둘 다** 선언한다.
- `record Bad(int hashCode) { }` 라고 컴포넌트 이름을 짓는다.
- 여섯 중 **문법 에러**(다른 다섯과 성격이 다른 것)는 어느 것이며 그게 뜻하는 바는 무엇인가?

### 9. 만들어 주는 것과 안 만들어 주는 것 (연결)

- `record` 가 자동으로 구현하는 **인터페이스**는 무엇인가?
- `record` 를 `HashSet` 에 넣으면 되는데 `TreeSet` 에 넣으면 무슨 예외가 나는가, 그 이유는?
- 필드 하나만 바꾼 복사본(`withX`)을 만들어 주는가?
- 빌더·세터·깊은 불변 중 `record` 가 주는 것은 무엇인가?
- `record` 를 `implements Serializable` 하면 역직렬화가 **표준 생성자를 거치는가**, 건너뛰는가 — 그게 왜 중요한가?

### 10. 무엇이 언어 보장이고 무엇이 구현 세부인가 (경계)

- `new Point(1,2).hashCode()` 가 17·21·25 에서 전부 `33` 이었다 — 이 값에 기대도 되는가, 그 근거는?
- `toString` 이 `Point[x=1, y=2]` 형식이라는 것은 보장인가? 이 문자열을 파싱해도 되는가?
- `equals`/`hashCode`/`toString` 이 `invokedynamic` 한 줄로 컴파일된다는 것은 보장인가?
- **컴포넌트를 선언 순서대로 비교한다**는 것은 보장인가?
- 그렇다면 `record` 에서 **보장으로 적어도 되는 것**은 무엇인가?

### 11. 어디까지가 이 주제이고 어디부터가 다른 주제인가 (연결)

- `record` 가 **언제·왜** 들어왔나(JEP 395·preview 단계)는 어느 문서가 정본인가?
- `equals`/`hashCode` **계약 다섯 조항과 위반 증상**은 어느 문서가 정본인가?
- **방어적 복사 관용구 자체**는 어느 주제가 정본이고, 이 주제가 맡는 부분은 무엇인가?
- `record` 를 **분해하는 문법**(`if (o instanceof Point(int x, int y))`)은 어느 주제인가?
- `record` 와 짝을 이뤄 패턴 매칭의 완결성을 만드는 문법은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
