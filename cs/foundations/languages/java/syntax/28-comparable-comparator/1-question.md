# java/syntax/28 — `Comparable`/`Comparator`: 전순서 계약과 조합 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제는 **계약형**이라 예측형이 그대로 서지 않는다 —
> **「조항 세기」 한 문 + 「어기면 무엇이 출력되나」 여러 문**으로 돌린다(작성 규칙 §2-1 규칙 6).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 계약의 조항은 몇 개이고 각각 무엇인가 (경계)

- `compareTo` 의 javadoc 이 "must ensure" 로 요구하는 조항은 몇 개이고 각각 무엇인가?
- 그 밖에 하나 더 있는 조항은 무엇이고, 앞의 것들과 **강제 수준이 어떻게 다른가**?
- `Comparator.compare` 의 계약은 `compareTo` 와 무엇이 같고 무엇이 다른가?
- 반사성(`x.compareTo(x) == 0`)은 왜 조항으로 따로 안 적혀 있는가?

### 2. 이 비교자는 계약의 어느 조항을 어기는가 (예측)

```java
Comparator<Integer> FUZZY = (x, y) -> Math.abs(x - y) <= 10 ? 0 : Integer.compare(x, y);

FUZZY.compare(0, 10);
FUZZY.compare(10, 20);
FUZZY.compare(0, 20);
```

- 세 호출의 결과는 각각 무엇인가?
- 그 결과가 어느 조항을 어기는가?
- 이 자를 만든 사람이 원했던 것은 무엇이고, 그것을 계약을 지키면서 하려면 무엇을 써야 하는가?

### 3. ★ 이 비교자로 정렬하면 무슨 일이 일어나는가 — 원소 수별로 (예측)

```java
List<Integer> l = /* 0~999 난수 n개, 씨앗 42 */;
l.sort(FUZZY);
```

- `n` 이 4·16·1000·2000 일 때 각각 어떻게 되는가 — 예외인가, 정상 종료인가?
- 정상 종료한 경우 **결과는 오름차순인가**?
- 예외가 난다면 예외 타입과 메시지는 무엇인가?
- 이 셋(정상+정답 / 정상+오답 / 예외) 중 **가장 위험한 것**은 어느 것이고 왜인가?

### 4. ★ 왜 원소가 적으면 안 터지는가 (왜)

- `TimSort` 소스의 어느 상수가 이 경계를 정하는가? 값은 얼마인가?
- 그 아래에서는 어떤 정렬이 돌고, 그 경로에 `throw` 가 있는가?
- 원소 2~31개로 6만 번 돌렸을 때 예외는 몇 번 났고, 오름차순이 아닌 결과는 몇 번 났는가?
- 32~61개에서는 그 둘이 어떻게 바뀌는가?
- 그래서 "예외가 안 났으니 계약을 지켰다"는 결론이 왜 틀리는가?

### 5. ★ `compareTo` 와 `equals` 가 어긋나면 무엇이 달라지는가 (예측)

```java
record Emp(String name, String dept) implements Comparable<Emp> {
    public int compareTo(Emp o) { return name.compareTo(o.name); }
}
Emp a = new Emp("김", "영업");
Emp b = new Emp("김", "개발");

new HashSet<>(List.of(a, b)).size();
new TreeSet<>(List.of(a, b)).size();
new TreeSet<>(List.of(a, b)).contains(b);
```

- 세 결과는 각각 무엇인가?
- `TreeSet` 에 남은 것은 `a` 인가 `b` 인가?
- `contains(b)` 의 답이 이상한 이유는 무엇인가?
- 같은 상황을 `TreeMap` 으로 만들면 키와 값이 어떻게 되는가?

### 6. JDK 안에서 이 계약을 깨 놓은 대표 클래스는 무엇인가 (연결)

- `new BigDecimal("1.0")` 과 `new BigDecimal("1.00")` 의 `equals` 와 `compareTo` 는 각각 무엇을 돌려주는가?
- 그 둘을 `HashSet` 과 `TreeSet` 에 넣으면 `size()` 는 각각 얼마인가?
- 이 클래스가 계약을 깨면서도 문제가 안 되는 이유는 무엇인가 — javadoc 이 무엇을 요구했나?

### 7. 뺄셈으로 비교하면 무엇이 틀리는가 (예측)

```java
Comparator<Integer> minus = (a, b) -> a - b;
List<Integer> l = new ArrayList<>(List.of(Integer.MAX_VALUE, -10, 0));
l.sort(minus);
```

- `Integer.MAX_VALUE - (-10)` 의 값은 무엇인가?
- 정렬 결과는 무엇인가?
- 이 버그가 오래 살아남는 이유는 무엇인가?
- 무엇으로 바꿔야 하는가?

### 8. `compareTo(null)` 은 어떻게 되어야 하는가 (경계)

- `e.compareTo(null)` 과 `e.equals(null)` 은 각각 무엇을 해야 하는가?
- 둘이 정반대인 이유는 무엇인가?
- `Comparator` 는 `null` 을 어떻게 다뤄야 하는가?

### 9. `reversed()` 를 붙이는 자리가 결과를 바꾸는가 (예측)

```java
list.sort(comparing(P::dept).thenComparing(P::name).reversed());   // (A)
list.sort(comparing(P::dept).reversed().thenComparing(P::name));   // (B)
```

- (A)와 (B)의 결과는 같은가 다른가?
- 다르다면 각각 어떤 순서가 되는가?
- 한 키만 내림차순으로 하려면 어떻게 써야 하는가?

### 10. `null` 이 섞인 정렬은 어떻게 다루는가 (경계)

- 키 추출 함수가 `null` 을 돌려줄 때와 원소 자체가 `null` 일 때, 각각 어떤 NPE 메시지가 나오는가?
- `nullsFirst`/`nullsLast` 는 어느 층에 감싸야 하는가?
- `list.sort(null)` 은 어떤 뜻인가?

### 11. 이 체인은 왜 컴파일되지 않는가 (예측)

```java
l.sort(comparing(p -> p.dept()).thenComparing(p -> p.name()));
```

- 에러 문구는 무엇이고 어디를 가리키는가?
- 원인은 무엇인가?
- 고치는 방법 두 가지는 무엇인가?

### 12. `Comparable` 과 `Comparator` 중 무엇을 고르나 (왜)

- 둘을 가르는 실제 기준은 무엇인가?
- 여러 키로 정렬할 때 `if` 를 쌓는 대신 무엇을 쓰는가?
- 기본형 키에 `comparing` 대신 `comparingInt` 를 쓰는 이유는 무엇인가?

### 13. 다른 주제와 잇기 (연결)

- 27번의 `equals` 계약과 이 주제의 계약은 어디서 만나고 어디서 갈라지는가?
- `HashSet` 에서 원소가 사라지는 것과 `TreeSet` 에서 원소가 사라지는 것은 원인이 어떻게 다른가?
- `Arrays.sort(int[])` 에서도 이 예외가 날 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
