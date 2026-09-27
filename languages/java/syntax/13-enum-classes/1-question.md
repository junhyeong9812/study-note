# java/syntax/13 — `enum` 클래스: 상수별 본문·`EnumSet`/`EnumMap` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제는 **예측형 위주**다 — 아는지가 아니라 **출력·컴파일 결과를 맞힐 수 있는지**를 묻는다.
> 선행은 [06번](../06-initialization-order/)이다. `<clinit>` 이 **딱 한 번** 돈다는 규칙이 이 주제의 절반을 설명한다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. enum 상수 셋을 쓰면 클래스 파일에 무엇이 생기는가 (예측)

```java
enum Planet {
    MERCURY(3.303e+23, 2.4397e6),
    VENUS  (4.869e+24, 6.0518e6),
    EARTH  (5.976e+24, 6.37814e6);
    private final double mass, radius;
    Planet(double mass, double radius) { this.mass = mass; this.radius = radius; }
    double surfaceGravity() { return 6.67300E-11 * mass / (radius * radius); }
}
```

- `javap -p` 로 열면 내가 쓰지 않은 멤버가 무엇 무엇 보이는가?
- 이 클래스의 상위 클래스는 무엇이고, 클래스 선언에 붙는 수식어는 무엇인가?
- `<clinit>` 안에서는 상수 하나당 무슨 명령이 몇 번 일어나는가?
- 소스의 생성자는 `(double, double)` 인데 클래스 파일의 descriptor 는 무엇인가, 그 차이는 무엇을 뜻하는가?

### 2. `values()` 로 받은 배열을 망가뜨리면 (예측)

```java
System.out.println("values() == values() ? " + (Planet.values() == Planet.values()));
Planet[] stolen = Planet.values();
stolen[0] = null;
System.out.println("망가뜨린 뒤 values()[0] = " + Planet.values()[0]);
System.out.println("내가 들고 있던 배열[0] = " + stolen[0]);
```

- 네 줄의 출력은 각각 무엇인가?
- `javap -c` 로 `values()` 를 열면 몇 개의 명령이 보이고, 그중 결정적인 것은 무엇인가?
- 이 설계가 치르는 대가는 무엇이며, 루프 안에서 `values()` 를 부르면 어떻게 되는가?
- 방어책 두 가지는 무엇인가?

### 3. 상수별 본문을 쓰면 `getClass()` 가 무엇을 돌려주는가 (예측)

```java
enum Op {
    PLUS("+")  { int apply(int a, int b) { return a + b; } },
    MINUS("-") { int apply(int a, int b) { return a - b; } },
    TIMES("*") { int apply(int a, int b) { return a * b; } };
    private final String symbol;
    Op(String symbol) { this.symbol = symbol; }
    abstract int apply(int a, int b);
}
enum Plain { A, B }
```

- `Op.PLUS.getClass()` 와 `Op.PLUS.getDeclaringClass()` 는 각각 무엇인가?
- `Op.class` 와 `Plain.class` 에 붙는 수식어는 각각 무엇이고 왜 다른가?
- 컴파일하면 클래스 파일이 몇 개 생기는가?
- `javap -v Op` 에만 나타나는 속성은 무엇이며, 그것이 어느 주제와 이어지는가?

### 4. `EnumSet`·`EnumMap` 과 `HashSet`·`HashMap` 의 출력이 갈린다 (예측)

```java
enum Day { MON, TUE, WED, THU, FRI, SAT, SUN }
System.out.println(EnumSet.of(Day.SUN, Day.SAT));
System.out.println(new HashSet<>(List.of(Day.SUN, Day.SAT)));

EnumMap<Day,Integer> em = new EnumMap<>(Day.class);
em.put(Day.SUN, 1); em.put(Day.MON, 2); em.put(Day.FRI, 3);
System.out.println(em);
em.put(null, 9);
```

- 앞의 세 출력은 각각 무엇인가?
- 마지막 줄은 어떻게 되는가, `HashMap` 이었다면 어떻게 되는가?
- 그 순서가 **우연히 그런 것**인가 **보장된 것**인가 — 근거는 어디 있는가?
- `EnumMap` 이 `HashMap` 보다 나은 구조적 이유는 무엇이고, **말하면 안 되는 것**은 무엇인가?

### 5. `ordinal()` 로 저장한 값이 조용히 바뀐다 (예측)

```java
// 어제
enum Status { NEW, PAID, SHIPPED }
int stored = Status.SHIPPED.ordinal();      // 이 값을 DB 에 넣었다

// 오늘 — 누가 가운데에 하나를 끼워 넣었다
enum Status { NEW, CANCELLED, PAID, SHIPPED }
System.out.println(Status.values()[stored]);
System.out.println(Status.valueOf("SHIPPED"));
```

- 오늘의 두 줄은 각각 무엇을 출력하는가?
- 예외·경고·로그 중 무엇이라도 나는가?
- `Enum.ordinal()` 의 javadoc 은 이 메서드에 대해 무엇이라고 쓰는가?
- 그런데도 `EnumSet`/`EnumMap` 이 `ordinal` 을 쓰는 것은 왜 안전한가?

### 6. 같은 파일이냐 다른 파일이냐로 `switch` 의 컴파일 결과가 갈린다 (왜)

```java
// (A) Ex.java 하나에 enum Day 와 kind() 가 같이 있다
// (B) Day.java 와 Ex.java 로 나뉘어 있다
static String kind(Day d) {
    switch (d) {
        case SAT: case SUN: return "쉬는 날";
        default:            return "일하는 날";
    }
}
```

- (A) 와 (B) 의 `javap -c Ex` 는 각각 어떻게 다른가?
- (B) 에서 더 생기는 클래스는 무엇이고 그 안에 무엇이 들어 있는가?
- 그 클래스의 `<clinit>` 에 **예외 테이블**이 있는 이유는 무엇인가?
- `Day` 의 상수 **순서만** 바꿔 `Day` 만 다시 컴파일하면 (A)(B) 는 각각 어떻게 되는가?

### 7. enum 이 싱글턴인 것을 무엇이 보장하는가 (왜)

- 인스턴스를 더 만들려는 길이 **몇 개**이고 각각을 무엇이 막는가?
- 그중 **컴파일러가** 막는 것과 **런타임이** 막는 것은 어떻게 갈리는가?
- 리플렉션으로 생성자를 불러 보면 어떤 예외 메시지가 나오는가?
- 이 보장이 [**06번 주제**](../06-initialization-order/)의 어느 규칙에 기대고 있는가?

### 8. enum 생성자에서 그 enum 의 `static` 필드를 건드리면 (경계)

- `Code(String tag) { BY_TAG.put(tag, this); }` 는 컴파일되는가, 안 되면 어떤 에러인가?
- 만약 컴파일이 됐다면 실행 시 무슨 일이 났겠는가 — 그 이유는 무엇인가?
- 이 제약의 **예외**(허용되는 경우)는 무엇인가?
- 같은 목적을 달성하는 올바른 형태는 무엇인가?

### 9. `case Day.SAT:` 는 되는가 (경계)

- `--release 17` · `--release 20` · `--release 21` · JDK 25 에서 각각 어떻게 되는가?
- 안 될 때의 에러 메시지는 무엇인가?
- 바뀐 계기는 무엇이고, JLS SE 21 §14.11.1 의 문장은 무엇이라고 쓰는가?
- 21 로 올린 코드를 17 로 되돌리면 이 자리는 어떻게 되는가?

### 10. `switch` 문에 `null` 을 넣으면 (경계)

- `default:` 가 있는 옛 `switch` **문**에 `null` 을 넣으면 어떻게 되는가?
- 예외 메시지는 **어느 메서드**를 지목하는가, 그것이 무엇을 말해 주는가?
- 21 부터는 무엇을 쓸 수 있는가?

### 11. `toString()` 을 바꿔 놓고 `valueOf()` 로 되읽으면 (경계)

- `@Override public String toString() { return symbol; }` 를 둔 enum 에서 `name()` 과 `toString()` 은 각각 무엇을 돌려주는가?
- `valueOf(PLUS.toString())` 은 어떻게 되는가?
- 둘 중 오버라이드할 수 있는 것은 무엇이고, 그 사실이 직렬화에 주는 규칙은 무엇인가?

### 12. 어디까지가 언어 보장인가 (연결)

- `$VALUES` · `$values()` · `$SwitchMap$Day` · `Ex$Op$1` 중 JLS 에 나오는 것은 무엇인가?
- `values()` 가 "매번 새 배열"이라는 것은 JLS 의 어느 문장으로 뒷받침되는가 — 없다면 무엇을 외워야 하는가?
- 생성자 descriptor 의 `String`·`int` 파라미터에 대해 JLS 가 **직접 쓴 말**은 무엇인가?
- `EnumSet`/`EnumMap` 이 "더 빠르다"는 것은 보장인가, javadoc 원문은 무엇이라 쓰는가?
- enum 을 늘려야 할 때 이 주제 대신 어느 주제로 가야 하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
