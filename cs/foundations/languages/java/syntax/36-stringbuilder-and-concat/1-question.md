# java/syntax/36 — `StringBuilder` 와 문자열 연결이 컴파일되는 방식 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> 선행: [35 `String`](../35-string/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 세 메서드의 바이트코드를 예측하라 (예측)

```java
static String constFold() { return "he" + "l" + "lo"; }
static String twoVars(String a, String b) { return a + b; }
static String loopBuilder(String[] parts) {
    StringBuilder sb = new StringBuilder();
    for (String p : parts) sb.append(p);
    return sb.toString();
}
```

- `javap -c` 를 뜨면 세 메서드에 각각 어떤 명령이 나오는가?
- `constFold` 에 `+` 의 흔적이 남는가?
- `twoVars` 에 `StringBuilder` 가 나오는가?
- `twoVars` 의 호출 대상은 무엇이고, 그것을 어떤 명령으로 확인하는가?

### 2. ★ 루프 안 `+=` 는 무엇으로 컴파일되는가 (예측)

```java
static String loopConcat(String[] parts) {
    String s = "";
    for (String p : parts) {
        s += p;
    }
    return s;
}
```

- 루프 몸통 안에 `new StringBuilder` 가 **몇 번** 나오는가?
- JDK 21에서 실제로 나오는 명령은 무엇인가?
- 그렇다면 이 코드가 느린 **진짜 이유**는 무엇인가?
- Java 8 시절의 바이트코드를 지금 JDK에서 재현하는 방법이 있는가?
- 17·21·25에서 이 바이트코드가 같은가?

### 3. n 을 2배로 늘리면 시간은 몇 배가 되는가 (예측)

- `s += "x"` 를 n번 도는 루프에서, n 을 2배로 하면 시간은 대략 몇 배가 되는가?
- `StringBuilder` 쪽은 몇 배가 되는가?
- 그 답을 **복잡도 기호**로 쓰면 각각 무엇인가?
- 이 문서의 측정에서 "`+=` 가 `StringBuilder` 보다 1836배 느리다"는 문장은 왜 불완전한가?
- 측정할 때 워밍업을 안 하면 무엇이 잘못되는가?

### 4. `StringBuilder` 의 용량 (예측)

```java
StringBuilder sb = new StringBuilder();
System.out.println(sb.capacity());
// 17글자를 append 한 뒤
System.out.println(sb.capacity());
System.out.println(new StringBuilder("abc").capacity());
// 한글 20자를 넣은 StringBuilder 의 capacity 는?
```

- 기본 용량은 얼마인가?
- 용량이 늘어나는 규칙을 식으로 쓸 수 있는가?
- `new StringBuilder("abc")` 의 용량이 3이 아닌 이유는 무엇인가?
- `capacity()` 가 돌려주는 것은 바이트 수인가 글자 수인가, 한글로 어떻게 확인하는가?

### 5. `null` 이 섞이면 (예측)

```java
String s = null;
System.out.println("x" + s);
StringBuilder sb = new StringBuilder();
sb.append((String) null);
System.out.println(sb.length());
System.out.println(String.join(",", listWithNull));   // ["a", null]
System.out.println(String.valueOf((Object) null));
System.out.println(String.valueOf((char[]) null));
```

- 다섯 줄의 출력(또는 예외)은 각각 무엇인가?
- 왜 마지막 줄만 다른가?
- 이 동작이 **조용한 실패**인 이유는 무엇인가?

### 6. 반복과 서식의 경계 (예측)

```java
"ab".repeat(0)
"ab".repeat(0) == ""
"ab".repeat(-1)
String.format("%d", "문자열")
String.format("%,d", 1234567)
```

- 다섯 식의 결과(또는 예외 클래스와 메시지)는 각각 무엇인가?
- `repeat(0) == ""` 가 참인 것을 코드가 의존해도 되는가, 왜인가?
- `String.format` 의 타입 오류는 컴파일 타임에 잡히는가?

### 7. 잇는 세 가지 방법 (경계)

- `String.join`, `Collectors.joining`, `StringBuilder` 는 각각 언제 쓰는가?
- `String.join(",", List.of())` 는 예외인가 빈 문자열인가?
- `Collectors.joining` 의 내부는 실제로 무엇인가?
- 그것이 `StringBuilder` 와 어떻게 다른가?

### 8. 명세는 무엇을 보장하는가 (왜)

- JLS는 `+` 가 `StringBuilder` 로 컴파일된다고 말하는가?
- 명세가 실제로 쓰는 낱말은 무엇인가, 그 문장을 인용할 수 있는가?
- 그래서 "`+` 는 `StringBuilder` 가 된다"는 설명은 무엇이었나?
- 이 문서의 측정 수치 중 다른 기계에서 재현되는 것은 무엇이고 안 되는 것은 무엇인가?

### 9. 어디를 고치고 어디를 두나 (경계)

- 다음 셋 중 고쳐야 할 것은 무엇인가 — 루프 안 `+=` / 한 줄 `a + b + c` / `new StringBuilder().append().append().toString()` 한 줄?
- 한 줄 연결을 `StringBuilder` 로 바꾸면 무엇이 나빠지는가?
- 용량을 미리 잡는 최적화는 `+=` 를 고치는 것보다 먼저인가 나중인가, 왜인가?

### 10. 다른 주제와 잇기 (연결)

- 루프 안 `+=` 가 O(n²)인 근본 원인은 이 주제의 성질인가, [35번](../35-string/)의 성질인가?
- `StringBuilder` 의 "2배 + 2" 증가 규칙과 동적 배열의 증폭 전략은 어떻게 이어지는가?
- `1 + 2 + "x"` 가 `"3x"` 인 것은 어느 주제의 규칙인가?
- `StringBuffer` 와 `StringBuilder` 의 유일한 차이는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
