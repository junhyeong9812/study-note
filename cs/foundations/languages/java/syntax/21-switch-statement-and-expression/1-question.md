# java/syntax/21 — `switch` 문과 `switch` 식 (14+): 화살표 · `yield` · 폴스루 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형**과 **「어기면 무엇이 출력되나」형**이 반반이다.
> ★ **버전 문항이 둘 있다**(4·10번) — 같은 소스가 17 과 21 에서 **다른 바이트코드**가 된다.
> 기본은 Temurin **JDK 21.0.5** 이고, 판이 갈리는 문항에는 그 표시를 달았다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `break` 를 빠뜨리면 (예측)

```java
static String colonBuggy(int day) {
    String s = "?";
    switch (day) {
        case 1: s = "월";
        case 2: s = "화";
        case 3: s = "수"; break;
        default: s = "그 밖";
    }
    return s;
}
```

- `colonBuggy(1)` · `colonBuggy(2)` · `colonBuggy(4)` 는 각각 무엇을 돌려주는가?
- 컴파일 경고가 나는가 — 안 난다면 **무엇을 켜야** 나는가?
- 켜면 경고는 **몇 개** 나오고 어느 줄을 가리키는가?
- 이것을 화살표로 바꾸면 무엇이 달라지는가?

### 2. 폴스루는 바이트코드에서 무엇인가 (왜)

```java
// (a) 콜론, break 누락
switch (day) { case 1: s = "월"; case 2: s = "화"; case 3: s = "수"; break; default: s = "그 밖"; }

// (b) 화살표 식
return switch (day) { case 1 -> "월"; case 2 -> "화"; case 3 -> "수"; default -> "그 밖"; };
```

- 두 메서드의 **분기 선택 명령**은 같은가 다른가?
- 두 메서드에서 **`goto` 의 개수**는 각각 몇인가?
- "화살표가 폴스루를 없앴다"를 바이트코드 수준으로 한 문장으로 말하면 무엇인가?
- 화살표로 바꾸면 분기가 더 빨라지는가?

### 3. `tableswitch` 와 `lookupswitch` (예측)

```java
static String dense(int code)  { return switch (code) { case 1 -> "하나"; case 2 -> "둘"; case 3 -> "셋"; default -> "?"; }; }
static String sparse(int code) { return switch (code) { case 1 -> "하나"; case 500 -> "오백"; case 9999 -> "구천구백구십구"; default -> "?"; }; }
```

- 두 메서드는 각각 어떤 JVM 분기 명령으로 컴파일되는가?
- 무엇이 그 선택을 가르는가 — 소스에서 고를 수 있는가?
- `javap` 출력의 `{ // 1 to 3 }` 과 `{ // 3 }` 은 각각 무슨 뜻인가?
- `switch (String)` 은 이 둘 중 무엇인가 — 아니면 또 다른가?

### 4. ★ 완결한 `enum` `switch` 식의 바이트코드 (예측 · 버전)

```java
enum Day { MON, TUE, SAT, SUN }
static String kindExpr(Day d) {
    return switch (d) {
        case MON, TUE -> "평일";
        case SAT, SUN -> "주말";
    };
}
```

- 소스에 `default` 가 없는데 바이트코드에도 `default:` 가 없는가?
- 있다면 그 가지는 **무엇을 하는가** — 어느 예외 클래스인가?
- 이 `switch` 에는 패턴이 하나도 없다. 그런데도 그 예외가 나오는 것이 이상하지 않은가?
- ★ 같은 소스를 **JDK 17 의 javac** 로 찍으면 바이트코드가 같은가 — 다르다면 두 군데가 어떻게 다른가?

### 5. 식이냐 문이냐로 갈리는 것 (예측)

```java
// (a) 식
static String kindExpr(Day d) { return switch (d) { case MON, TUE -> "평일"; case SAT, SUN -> "주말"; }; }

// (b) 문
static String kindStmt(Day d) {
    String s = "안 걸림";
    switch (d) { case MON -> s = "월"; case TUE -> s = "화"; }
    return s;
}
```

- (a)는 `default` 가 없는데 컴파일되는가?
- (b)는 상수를 둘만 적었는데 컴파일되는가?
- `kindStmt(Day.SAT)` 의 출력은 무엇인가?
- **왜 식에는 완결성이 요구되고 문에는 안 요구되는가**를 한 문장으로 말하면?
- 이 규칙이 **패턴을 쓰는 `switch` 문**에도 그대로인가?

### 6. `yield` 와 블록 가지 (예측)

```java
static int scored(int day) {
    return switch (day) {
        case 1, 2, 3, 4, 5 -> { int base = 10; yield base * day; }
        case 6, 7 -> 0;
        default   -> -1;
    };
}
```

- `scored(3)` 과 `scored(6)` 은 각각 무엇인가?
- 블록 가지에서 `yield` 대신 `return` 을 쓰면 무엇이 나오는가?
- 블록 가지가 값도 안 내고 `throw` 도 안 하면 무엇이 나오는가 — 메시지의 괄호 설명은?
- 콜론 문법으로도 `switch` **식**을 쓸 수 있는가?

### 7. `switch` 식이 안 덮었을 때 (경계)

```java
static String f(int n) {
    return switch (n) {
        case 1 -> "하나";
        case 2 -> "둘";
    };
}
```

- 이것은 컴파일되는가? 안 된다면 정확히 무엇이 출력되는가?
- `default -> "?"` 를 넣으면 통과하는가?
- `int` 를 selector 로 쓸 때 `default` 없이 완결할 수 있는 방법이 있는가?
- 같은 본문을 `switch` **문**으로 바꾸면 컴파일되는가?

### 8. 섞으면 안 되는 것 셋 (경계)

```java
// (a)
return switch (n) { case 1 -> "하나"; case 2: yield "둘"; default -> "?"; };

// (b)
return switch (n) { case 1 -> { return "하나"; } default -> "?"; };

// (c)
int limit = 3;
switch (n) { case limit -> System.out.println("?"); default -> System.out.println("?"); }
```

- (a)·(b)·(c)는 각각 어떤 에러를 내는가?
- (c)에서 `limit` 을 `static final int LIMIT = 3;` 으로 바꾸면 통과하는가?
- `case` 레이블이 상수여야 하는 이유를 3번의 답과 이어서 말하면 무엇인가?
- 중복 `case` 와 중복 `default` 는 각각 어떤 메시지인가?

### 9. `yield` 는 예약어인가 (경계)

```java
// (a)
static int f(int n) { if (n > 0) yield n; return 0; }

// (b)
static int yield(int x) { return x * 2; }
...
int yield = 5;
System.out.println(yield + " / " + yield(3));
```

- (a)는 어떤 에러를 내는가?
- (b)에서 **변수** `yield` 는 선언할 수 있는가?
- (b)의 `yield(3)` 호출은 통과하는가 — 안 된다면 메시지가 알려 주는 고치는 법은 무엇인가?
- `yield` 와 `goto` 는 이 점에서 어떻게 다른가?

### 10. ★ `enum` 에 상수를 추가하고 `switch` 를 안 고쳤다 (예측 · 버전)

```text
1차:  Day.java   public enum Day { MON, TUE, SAT, SUN }
      Ex.java    switch (d) { case MON, TUE -> "평일"; case SAT, SUN -> "주말"; }   // default 없음
      -> javac -d out Day.java Ex.java   (성공)

2차:  Day 에 HOLIDAY 를 넣고 Day.java 만 다시 컴파일 (Ex 는 그대로)
```

- 2차 컴파일은 성공하는가?
- `java Ex SAT` 는 무엇을 출력하는가?
- `java Ex HOLIDAY` 는 무엇을 출력하는가 — 예외라면 **정확한 클래스 이름**은?
- ★ 같은 시나리오를 **JDK 17** 에서 돌리면 예외 이름이 같은가?
- javac 가 이것을 컴파일 시점에 막아 주지 못하는 이유는 무엇인가?

### 11. 옛 `switch` 에 `null` 을 넣으면 (경계)

```java
enum Day { MON, SAT }
static String oldEnumSwitch(Day d) {
    switch (d) { case MON: return "월"; case SAT: return "토"; default: return "?"; }
}
oldEnumSwitch(null);
```

- 무엇이 나오는가 — 메시지에는 **어느 메서드 이름**이 박히는가?
- `default` 가 있는데도 `default` 로 안 가는 이유는 무엇인가?
- `switch (String)` 에 `null` 을 넣으면 메시지가 어떻게 다른가?
- `case null` 은 언제부터 쓸 수 있고, 그것은 어느 주제인가?

### 12. 무엇이 보장이고 무엇이 판마다 다른가 (연결)

- 이 주제에서 **17 · 21 · 25 사이에 달랐던 것 둘**은 무엇인가?
- 세 판에서 **실행 출력이 같았다**는 것으로 무엇을 주장할 수 있고 무엇을 주장할 수 없는가?
- `MatchException` 은 몇 부터이며 근거는 어디에 있는가?
- `tableswitch`/`lookupswitch` 선택은 보장인가 구현 세부인가?

### 13. 정본 경계와 선택 (연결)

- 이 주제와 **13번**(`enum`)·**23번**(패턴 `switch`)·**35번**(`String`)의 경계는 각각 어디인가?
- `default` 를 넣을지 말지의 판단 기준을 한 문장으로 말하면 무엇인가?
- 가지에 블록이 셋 이상 생기면 그것은 무엇의 신호인가?
- `case 1, 2, 3 ->` 와 옛 `case 1: case 2: case 3:` 는 같은 것인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
