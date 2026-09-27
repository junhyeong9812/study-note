# java/syntax/22 — `instanceof` 타입 패턴 (16+) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★ **이 주제의 무게는 2·3번(스코프)에 있다.** 나머지는 그 규칙의 응용이거나 경계다.
> 문법이 한 줄짜리라 쉬워 보이지만, **실수는 전부 "어디서 보이나"에서 난다.**
> 기본은 Temurin **JDK 21.0.5** 이고, 판이 갈리는 문항(9번)에는 그 표시를 달았다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 캐스트는 정말 사라졌는가 (왜)

```java
static String oldWay(Object o) {
    if (o instanceof String) { String s = (String) o; return "문자열 길이 " + s.length(); }
    return "그 밖";
}
static String newWay(Object o) {
    if (o instanceof String s) { return "문자열 길이 " + s.length(); }
    return "그 밖";
}
```

- 두 메서드의 바이트코드는 같은가 다른가?
- `checkcast` 명령은 `newWay` 에 있는가 없는가?
- 타입 패턴은 성능 기능인가 — 얻는 것이 무엇이고 대가가 무엇인가?
- 이 점에서 [**23번 주제**](../23-switch-pattern-matching/)의 패턴 `switch` 와 어떻게 다른가?

### 2. ★ 이 여섯 자리에서 `s` 가 보이는가 (예측)

```java
// (A)
if (o instanceof String s) { /* 1 */ } else { /* 2 */ }
/* 3 */

// (B)
if (!(o instanceof String s)) return;
/* 4 */

// (C)
if (o instanceof String s && /* 5 */ ) { }

// (D)
if (!(o instanceof String s) || /* 6 */ ) { }
```

- 1~6 자리에서 `s` 는 각각 보이는가?
- 보이고 안 보이는 것을 **한 문장의 규칙**으로 정리하면 무엇인가?
- (B)에서 `else` 가 없는데도 `s` 가 보이는 것이 이상하지 않은가 — 이 스코프 방식의 이름은?
- `if (o instanceof String s || s.isEmpty())` 는 어떤가?

### 3. ★ 스코프를 어겼을 때의 에러 (예측)

```java
// (a)
if (o instanceof String s || s.isEmpty()) return "?";

// (b)
if (o instanceof String s) { }
return s.toUpperCase();

// (c)
String s = "바깥";
if (o instanceof String s) return s;
```

- (a)·(b)·(c)는 각각 어떤 에러 메시지를 내는가?
- (a)와 (b)의 메시지는 같은가 다른가 — 그것이 왜 함정인가?
- (c)의 메시지는 왜 다른가?
- (a)를 고치려면 무엇을 붙이는가 — 고치면 의미가 그대로인가?

### 4. `while` 조건의 패턴 (예측)

```java
static String loopScope(Deque<Object> q) {
    while (!(q.peek() instanceof String s)) {
        if (q.isEmpty()) return "문자열이 없다";
        q.poll();
    }
    return "첫 문자열 = " + s;
}
loopScope(new ArrayDeque<>(List.of(1, 2, "여기", 3)));
```

- 이것은 컴파일되는가? 된다면 출력은 무엇인가?
- 루프 **본문 안**에서 `s` 가 보이는가?
- `if (q.isEmpty()) return ...` 을 지우면 어떤 위험이 생기는가?
- 이 형태는 2번의 어느 항과 같은 구조인가?

### 5. 패턴 변수는 다시 대입할 수 있는가 (경계)

```java
if (o instanceof String s) { s = s + "!"; return s; }
if (o instanceof final String s) return "final 패턴 " + s;
```

- 첫 줄은 컴파일되는가 — 된다면 `"ab"` 를 넣었을 때 출력은?
- 패턴 변수에 `final` 을 붙일 수 있는가?
- 붙이면 무엇이 달라지는가?
- 대입하지 않는 것을 권하는 이유는 무엇인가?

### 6. 패턴 둘을 잇는 법 (예측)

```java
// (a)
if (a instanceof Integer x && b instanceof Integer y) return "합 " + (x + y);

// (b)
if (a instanceof Integer x || b instanceof Integer y) return "합? " + x + y;
```

- (a)는 컴파일되는가 — `a=1, b=2` 면 무엇이 나오는가?
- (b)는 컴파일되는가 — 안 된다면 에러는 **몇 개** 나오는가?
- (a)의 오른쪽에서 `x` 가 이미 보이는가?
- 조건 연산자(`? :`)에서는 어떤가?

### 7. `null` 을 넣으면 (예측)

```java
newWay(null);
earlyReturn(null);       // if (!(o instanceof String s)) return "문자열이 아니다";
orScope(null);           // if (!(o instanceof String s) || s.isEmpty()) return "...";
```

- 세 호출은 각각 무엇을 돌려주는가?
- `null` 은 타입 패턴에 맞는가?
- 그래서 `equals` 구현에서 무엇을 생략할 수 있는가?
- `switch` 에서는 이 규칙이 그대로인가?

### 8. 못 쓰는 자리 셋 (경계)

```java
// (a)
if (o instanceof List<String> l) return "문자열 리스트 " + l.size();

// (b)
if (o instanceof var v) return "" + v;

// (c)
static String f(String s) { if (s instanceof Integer i) return "정수 " + i; return "그 밖"; }
```

- (a)·(b)·(c)는 각각 어떤 에러를 내는가?
- (a)를 `List<?> l` 로 바꾸면 통과하는가 — 통과하면 `l.get(0)` 의 타입은 무엇인가?
- (c)의 에러는 패턴 때문인가, 아니면 패턴 없이 써도 같은가?
- `record` 패턴의 컴포넌트에는 `var` 를 쓸 수 있는가?

### 9. ★ 몇 부터인가 — 예외가 하나 있다 (경계 · 버전)

```java
// (a)
static int sameType(String s0) { if (s0 instanceof String s) return s.length(); return -1; }

// (b)
if (o instanceof String s) { ... }      // --release 15 로 컴파일
```

- (a)는 JDK 21 에서 컴파일되는가? JDK **17** 에서는?
- 다르다면 17 의 에러 메시지는 무엇인가?
- (a)가 21 에서 통과할 때 `sameType(null)` 은 무엇을 돌려주는가?
- (b)는 무엇을 출력하는가 — 메시지가 알려 주는 최소 버전은 몇인가?

### 10. `equals` 를 어떻게 쓰는가 (연결)

```java
record Point(int x, int y) {
    @Override public boolean equals(Object o) { return o instanceof Point p && p.x == x && p.y == y; }
    @Override public int hashCode() { return x * 31 + y; }
}
```

- 이 구현에서 `null` 검사는 어디에 있는가?
- 옛 형태(5줄)와 비교해 줄어든 것은 무엇이고 줄지 않은 것은 무엇인가?
- `equals` 의 **계약** 자체는 어느 주제가 정본인가?
- `record` 인데 `equals` 를 직접 쓴 것은 무엇을 보이려는 것인가?

### 11. 언제 `instanceof` 를 쓰고 언제 안 쓰나 (연결)

- `instanceof` 사슬이 셋을 넘으면 무엇으로 옮기는가 — 그 이득은 무엇인가?
- `if` 사슬이 가지를 빠뜨렸을 때 컴파일러는 무엇을 해 주는가?
- 컴포넌트를 꺼내야 할 때는 어느 주제로 가는가?
- 타입으로 분기하는 설계 자체를 의심해야 하는 경우는 언제인가?

### 12. 무엇이 보장이고 무엇이 구현 세부인가 (경계)

- "타입 패턴은 문법 설탕이다"라는 말은 어디까지 맞는가?
- 바이트코드가 옛 형태와 같다는 것은 보장인가 구현 세부인가?
- 흐름 스코프 규칙은 보장인가?
- 이 주제에서 **17 과 21 이 달랐던 자리**는 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
