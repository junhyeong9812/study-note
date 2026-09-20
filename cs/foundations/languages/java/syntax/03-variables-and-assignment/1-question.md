# java/syntax/03 — 변수와 대입: 전부 값 전달·`final`·effectively final — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 세 호출이 끝난 뒤 값은 무엇인가 (예측)

```java
static class Point { int x; Point(int x) { this.x = x; } public String toString() { return "Point(" + x + ")"; } }

static void mutateField(Point p)   { p.x = 99; }
static void reassign(Point p)      { p = new Point(99); }
static void changePrimitive(int n) { n = 99; }

int n = 1;                 changePrimitive(n);
Point p1 = new Point(1);   mutateField(p1);
Point p2 = new Point(1);   reassign(p2);
```

- `n`, `p1`, `p2` 는 각각 무엇인가?
- `mutateField` 와 `reassign` 은 둘 다 `Point` 를 받았는데 왜 결과가 갈리는가?
- 이 셋 중 **복사된 것**은 각각 무엇인가?

### 2. 한 메서드가 둘을 다 하면 (예측)

```java
static void both(Point p) {
    p.x = 50;
    p = new Point(77);
    p.x = 88;
}
// 호출 전: p3 = new Point(1)
```

- 호출이 끝난 뒤 `p3` 는 무엇인가?
- 50, 77, 88 중 어느 것이 호출자에게 보이고 어느 것이 안 보이는가?
- 88 을 적은 객체는 그 뒤 어떻게 되는가?

### 3. `swap` 은 왜 불가능한가 (왜)

```java
static void swap(Point a, Point b) { Point t = a; a = b; b = t; }
```

- 호출 후 호출자의 `a`, `b` 는 어떻게 되는가?
- 이것을 "자바에 참조 전달이 없다"의 증명으로 쓸 수 있는 이유는 무엇인가?
- 자바에서 두 값을 실제로 바꾸려면 어떤 수단이 남는가?

### 4. `final` 이 막는 것과 안 막는 것 (경계)

```java
static final int[]        NUMS  = {1, 2, 3};
static final List<String> NAMES = new ArrayList<>();

NUMS[0] = 99;
NAMES.add("추가됨");
NUMS = new int[]{9};
```

- 세 줄 중 컴파일되는 것은 무엇이고 안 되는 것은 무엇인가?
- `final` 이 거는 제약을 한 문장으로 말하면 무엇인가?
- `public static final int[] PRIMES = {2, 3, 5};` 를 상수로 공개하면 무엇이 위험한가?

### 5. 이 코드가 컴파일되지 않는 이유와 에러가 가리키는 줄 (예측)

```java
int counter = 0;
Runnable r = () -> System.out.println(counter);
counter = 1;
r.run();
```

- 컴파일 에러 문구는 무엇인가?
- 에러가 표시되는 줄과 **실제 원인이 되는 줄**은 같은가?
- `counter = 1;` 을 지우면 무엇이 달라지는가?

### 6. 어느 반복문의 변수가 캡처되는가 (예측)

```java
List<Runnable> rs = new ArrayList<>();
for (int i = 0; i < 3; i++)            rs.add(() -> System.out.print(i));      // (A)
for (String s : List.of("a","b","c"))  rs.add(() -> System.out.print(s));      // (B)
```

- (A)와 (B) 중 컴파일되는 것은 어느 쪽인가?
- 안 되는 쪽의 에러 문구는 무엇인가?
- 둘의 차이를 만드는 것은 무엇인가?

### 7. effectively final 은 왜 생겼는가 (왜)

- 익명 클래스가 바깥 지역 변수 `int n` 을 캡처하면 클래스 파일에 무엇이 생기는가?
- 그 필드의 제어자는 무엇인가?
- 만약 바깥 변수의 재대입을 허용한다면 어떤 모순이 생기는가?
- 람다는 익명 클래스와 다르게 컴파일되는데, 캡처한 값은 어디로 들어가는가?

### 8. 이 두 메서드의 바이트코드는 몇 줄인가 (예측)

```java
static int withFinal()    { final int x = 1; return x + 1; }
static int withoutFinal() { int x = 1; return x + 1; }
```

- `javap -c` 로 찍었을 때 두 메서드의 명령 수는 같은가 다른가?
- 다르다면 어느 쪽이 짧고 그 이유는 무엇인가?
- 이 결과에서 "`final` 의 런타임 비용"에 대해 무엇을 말할 수 있는가?

### 9. 지역 변수와 필드의 초기화 규칙 차이 (경계)

- `int x;` 를 선언만 하고 읽으면 무슨 일이 생기는가?
- 같은 선언을 **필드**로 하면 무슨 일이 생기는가?
- `final int y;` 를 선언하고 `if/else` 두 갈래에서 각각 한 번씩 대입하는 것은 허용되는가?
- 한쪽 갈래에서만 대입하면 어떻게 되는가?

### 10. 자바에서 참조 전달이 없다는 것을 어떻게 한 문장으로 말하나 (왜)

- "자바는 객체를 참조로 넘긴다"는 문장은 어디까지 맞고 어디서부터 틀리는가?
- 이 주제를 정확히 담는 한 문장은 무엇인가?
- 그 문장으로 1번의 세 결과가 전부 설명되는지 확인할 수 있는가?

### 11. 다른 주제와 잇기 (연결)

- `Integer` 는 참조 타입인데 왜 메서드에 넘겨 "내용을 고치는" 일이 불가능한가?
- 다중 `catch` 의 예외 변수와 `try`-with-resources 의 자원 변수는 이 주제와 어떻게 이어지는가?
- 팀 상수로 `List` 를 공개할 때 `final` 만으로 부족한 이유와 대안은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
