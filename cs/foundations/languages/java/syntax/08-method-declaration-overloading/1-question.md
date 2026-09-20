# java/syntax/08 — 메서드 선언: 오버로딩 해소·가변 인자 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **어느 메서드가 뽑히는지**를 맞힐 수 있는지 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 후보가 넷일 때 무엇이 뽑히나 (예측)

```java
static void f(long x)      { System.out.println("f(long)"); }
static void f(Integer x)   { System.out.println("f(Integer)"); }
static void f(Object x)    { System.out.println("f(Object)"); }
static void f(int... x)    { System.out.println("f(int...)"); }
// main: int i = 1;  f(i);
```

- 무엇이 출력되는가?
- `Integer` 가 `int` 에 "더 가까워 보이는데" 왜 안 뽑히는가?
- `javap -c` 로 `main` 을 열면 호출 직전에 어떤 명령이 하나 붙어 있는가?

### 2. 3단계를 하나씩 벗겨 보라 (예측)

```java
static void p1(long x)    { }   static void p1(Integer x) { }   static void p1(int... x) { }
static void p2(Integer x) { }                                   static void p2(int... x) { }
static void p3(int... x)  { }
static void q(Object x)   { }
// main: int i = 1;  p1(i); p2(i); p3(i); q(i);
```

- 네 호출이 각각 어느 후보로 가는가?
- 바이트코드에서 각 단계의 흔적은 무엇인가 — 세 단계가 서로 다른 명령을 남긴다.
- `q(Object)` 가 뽑히는 것은 몇 단계인가, 그 안에서 무슨 변환이 두 번 일어나는가?

### 3. 가변 인자와 배열의 관계 (예측)

```java
static void v(String... s) {
    System.out.println("len=" + (s == null ? "null 배열" : s.length));
}
// main: v(null);  v();  v("a","b");  v(new String[]{"a"});
```

- 네 줄의 출력은 각각 무엇인가?
- 넷 중 하나는 컴파일 경고가 난다 — 어느 것이고 경고는 무엇을 말하는가?
- `javap -c` 에서 네 호출의 **대상 시그니처**는 같은가 다른가?
- `v()` 와 `v(null)` 의 차이는 무엇인가?

### 4. 런타임 타입은 보지 않는다 (예측)

```java
static void t(Object o) { System.out.println("t(Object)"); }
static void t(String s) { System.out.println("t(String)"); }
// main:
Object o = "나는 런타임에는 String 이다";
t(o);
```

- 무엇이 출력되는가?
- 클래스 파일에는 어느 시그니처가 박히는가?
- 이 사실 때문에 "오버로딩은 다형성이 아니다"라고 말하는 이유는 무엇인가?

### 5. `null` 을 넘기면 (예측)

```java
static void g(Object o) { }   static void g(String s) { }
static void h(String s) { }   static void h(StringBuilder b) { }
// g(null);  g((Object) null);  h(null);
```

- `g(null)` 은 어느 것으로 가는가, 그 근거는 무엇인가?
- `h(null)` 은 어떻게 되는가, 에러 문구는 무엇인가?
- 둘의 차이를 만드는 조건을 한 문장으로 말하면 무엇인가?
- 고치려면 호출부를 어떻게 바꾸는가?

### 6. `List<Integer>.remove` (예측)

```java
List<Integer> list = new ArrayList<>(List.of(10, 20, 30));
list.remove(1);

List<Integer> list2 = new ArrayList<>(List.of(10, 20, 30));
list2.remove(Integer.valueOf(10));
```

- 두 리스트는 각각 무엇이 되는가?
- 왜 `remove(1)` 이 `remove(Object)` 로 안 가는가 — 몇 단계 규칙인가?
- `javap` 로 보면 두 호출의 대상 시그니처는 무엇인가?
- 반환형까지 보면 둘이 어떻게 다른가?

### 7. 모호해지는 조건 (경계)

```java
static void f(int x, long y) { }
static void f(long x, int y) { }
// f(1, 2);
```

- 컴파일되는가? 안 된다면 에러 문구는 무엇인가?
- "더 구체적"이라는 판정이 왜 여기서 안 서는가?
- 호출부를 어떻게 바꾸면 통과하는가?

### 8. 오버로딩이 아예 안 되는 조합 (경계)

- `void f(int[] x)` 와 `void f(int... x)` 를 같이 둘 수 있는가?
- `int f(int x)` 와 `String f(int x)` 는?
- 파라미터 **이름**만 다르면?
- `throws` 절만 다르면?

### 9. 가변 인자의 비용 (왜)

- 가변 인자 메서드를 루프 안에서 100만 번 부르면 무엇이 100만 개 생기는가?
- 그 근거를 바이트코드의 어느 명령에서 볼 수 있는가?
- `v()` 처럼 인자가 없어도 비용이 드는가?

### 10. API 를 바꿀 때 (연결)

- 이미 컴파일된 코드는 오버로딩이 추가돼도 안전한 이유는 무엇인가?
- 그런데도 **재컴파일하면** 깨질 수 있는 경우는 무엇인가?
- 그래서 오버로딩 대신 무엇을 고려하는가?

### 11. 정본 경계 (연결)

- 박싱 자체와 `Integer` 캐시는 어느 주제가 정본인가?
- 오버로딩과 **오버라이딩**의 대비는 어느 주제에서 완성되는가?
- `oop-basics` 가 말하는 "다형성"에 오버로딩이 포함되는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
