# java/syntax/53 — `BigDecimal`: 스케일·반올림·`equals` vs `compareTo` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> 선행: [02 수치 연산](../02-numeric-operations/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ `equals` 와 `compareTo` (예측)

```java
BigDecimal a = new BigDecimal("1.0");
BigDecimal b = new BigDecimal("1.00");

System.out.println(a.equals(b));
System.out.println(a.compareTo(b));
System.out.println(a.hashCode());
System.out.println(b.hashCode());
System.out.println(a.unscaledValue() + " / " + a.scale());
System.out.println(b.unscaledValue() + " / " + b.scale());
```

- 여섯 줄의 출력은 각각 무엇인가?
- `equals` 가 `false` 인 이유를 구현 코드 한 줄로 설명할 수 있는가?
- 해시가 다른 이유는 무엇인가?
- 이것은 `equals`/`hashCode` 계약 위반인가?

### 2. `HashSet` 과 `TreeSet` 에 같은 셋을 넣으면 (예측)

```java
var list = List.of(new BigDecimal("1"), new BigDecimal("1.0"), new BigDecimal("1.00"));
Set<BigDecimal> hash = new HashSet<>(list);
Set<BigDecimal> tree = new TreeSet<>(list);
System.out.println(hash.size());
System.out.println(tree.size());
System.out.println(hash.contains(new BigDecimal("1.000")));
System.out.println(tree.contains(new BigDecimal("1.000")));

Map<BigDecimal, String> m = new HashMap<>();
m.put(new BigDecimal("10.00"), "만원권");
System.out.println(m.get(new BigDecimal("10.0")));
```

- 다섯 줄의 출력은 각각 무엇인가?
- 마지막 줄이 예외인가 `null` 인가, 왜 그것이 더 나쁜가?
- 금액을 `HashMap` 키로 쓰려면 무엇을 해야 하는가?

### 3. `double` 로 만들면 무엇이 들어가는가 (예측)

```java
System.out.println(new BigDecimal(0.1));
System.out.println(new BigDecimal(0.1).scale());
System.out.println(new BigDecimal("0.1"));
System.out.println(BigDecimal.valueOf(0.1));
System.out.println(new BigDecimal(2.0));
System.out.println(BigDecimal.valueOf(1.0).scale());
```

- 여섯 줄의 출력은 각각 무엇인가?
- `new BigDecimal(0.1)` 의 값이 그렇게 나오는 것은 생성자의 버그인가?
- `valueOf(0.1)` 이 `"0.1"` 을 내는 이유는 무엇인가?
- `new BigDecimal(2.0)` 은 왜 깔끔한가, 그것이 왜 위험한가?

### 4. `divide` 와 `setScale` 이 던지는 네 가지 (예측)

```java
new BigDecimal("1").divide(new BigDecimal("3"));
new BigDecimal("1").divide(BigDecimal.ZERO);
BigDecimal.ZERO.divide(BigDecimal.ZERO);
new BigDecimal("1.5").setScale(0);
new BigDecimal("10").divide(new BigDecimal("4"));
```

- 다섯 줄 각각 — 값을 돌려주는가, 예외를 던지는가? 예외라면 **메시지**는 무엇인가?
- 같은 `ArithmeticException` 인데 메시지가 갈리는 이유는 무엇인가?
- 정수 `0 / 0` 의 메시지와 `BigDecimal.ZERO.divide(ZERO)` 의 메시지는 어떻게 다른가?
- `divide` 를 안전하게 쓰는 형태는 무엇인가?

### 5. 반올림 모드 (예측)

```java
// setScale(0, mode) 를 0.5 · 1.5 · 2.5 · -0.5 · -1.5 에 적용하면
// HALF_UP · HALF_DOWN · HALF_EVEN · UP · DOWN · CEILING · FLOOR
```

- `0.5`·`1.5`·`2.5` 에 대해 `HALF_UP` 과 `HALF_EVEN` 은 각각 무엇을 내는가?
- `-0.5` 에 대해 `HALF_UP` 과 `CEILING` 은 각각 무엇을 내는가?
- `HALF_EVEN` 을 회계에서 쓰는 이유는 무엇인가?
- `Math.round(-0.5)` 는 무엇이고, 그것은 어느 모드에 해당하는가?

### 6. 연산이 스케일을 어떻게 정하는가 (예측)

```java
new BigDecimal("1.0").add(new BigDecimal("2.00"))
new BigDecimal("1.5").multiply(new BigDecimal("2.00"))
new BigDecimal("2.50").stripTrailingZeros()
new BigDecimal("100").stripTrailingZeros()
new BigDecimal("100").stripTrailingZeros().toPlainString()
```

- 다섯 식의 **값과 스케일**은 각각 무엇인가?
- `multiply` 의 스케일 규칙은 무엇인가, 그것이 왜 위험한가?
- 네 번째 줄이 `100` 이 아닌 이유는 무엇인가?
- 그 값을 로그에 그대로 찍으면 무엇이 문제인가?

### 7. `0` 인지 판정하기 (경계)

- `BigDecimal.ZERO.equals(new BigDecimal("0.0"))` 는 무엇인가?
- `0` 판정에 쓸 수 있는 방법을 두 가지 들 수 있는가?
- `signum()` 이 돌려주는 값의 범위는 무엇인가?
- 금액이 음수인지 검사할 때 `compareTo` 와 `signum` 중 무엇을 쓰겠는가?

### 8. 되돌아갈 때 무엇이 조용히 틀리는가 (경계)

- `new BigDecimal("1.5").intValue()` 는 무엇인가?
- `new BigDecimal("1e20").intValue()` 는 무엇인가?
- `intValueExact()` 는 두 경우에 각각 어떤 메시지로 던지는가?
- 이 대비는 [02번 주제](../02-numeric-operations/)의 어떤 메서드와 같은 철학인가?

### 9. 계약인가 구현인가 (왜)

- `equals` 가 스케일을 본다는 사실은 어디에 적혀 있는가, 그 문장을 인용할 수 있는가?
- 자바가 스스로 "natural ordering that is inconsistent with equals"라고 적은 이유는 무엇인가?
- `2.0` 과 `2.00` 이 **대체 불가능**하다는 것을 javadoc은 어떤 예로 보여 주는가?
- `hashCode()` 가 돌려준 `311`·`3102` 라는 숫자를 코드가 의존해도 되는가?
- 예외 메시지를 테스트에서 단언해도 되는가?

### 10. 다른 주제와 잇기 (연결)

- `0.1` 을 열 번 더하면 `double` 과 `BigDecimal` 이 각각 무엇을 내는가?
- 그 `BigDecimal` 결과는 `BigDecimal.ONE` 과 `equals` 인가?
- `BigDecimal` 에는 오버플로가 없는데, 그 대신 무엇을 치르는가?
- 10000원을 3명이 나눌 때 `BigDecimal` 이 **정해 주지 않는 것**은 무엇인가?
- `0.1000000000000000055511...` 이라는 비트 패턴의 유래는 어느 문서가 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
