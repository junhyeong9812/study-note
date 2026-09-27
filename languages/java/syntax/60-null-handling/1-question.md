# java/syntax/60 — `null` 다루기: `Objects.requireNonNull`·`Optional` 의 경계 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제는 **관용구**라 "어디에 무엇을 쓰나"라는 **판단형**이 섞인다 —
> 그래도 판단의 근거는 전부 출력·예외로 둔다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 방어 시점 셋은 어디이고 각각 무엇을 쓰는가 (경계)

- `null` 을 막을 자리 셋은 어디인가?
- 각 자리에 맞는 도구는 무엇인가?
- 그중 **막는 것**과 **알리는 것**은 각각 어느 것인가?
- 셋을 하나로 합치려 하면 무엇이 어긋나는가?

### 2. ★ 이 두 클래스는 언제 터지고 스택이 어디를 가리키는가 (예측)

```java
static class Lazy  { final String name; Lazy(String n)  { this.name = n; } int len() { return name.length(); } }
static class Eager { final String name; Eager(String n) { this.name = Objects.requireNonNull(n, "name 은 null 일 수 없다"); } }

new Lazy(null);
new Eager(null);
```

- `new Lazy(null)` 은 성공하는가 실패하는가?
- 각각 NPE 가 나는 시점과 **스택 트레이스의 맨 위 두 프레임**은 무엇인가?
- 두 메시지는 각각 무엇인가?
- 운영에서 `Lazy` 쪽이 더 나쁜 이유를 한 문장으로 말하면 무엇인가?

### 3. `requireNonNull` 의 세 형태는 메시지가 어떻게 다른가 (예측)

```java
Objects.requireNonNull(null);
Objects.requireNonNull(null, "직접 쓴 메시지");
Objects.requireNonNull(null, () -> "공급자가 만든 메시지");
```

- 세 NPE 의 `getMessage()` 는 각각 무엇인가?
- 첫째가 그런 이유를 소스로 설명할 수 있는가?
- 셋째(`Supplier`)를 쓸 자리는 어디인가?
- javadoc 이 든 예제는 어떤 형태인가?

### 4. ★ 이 세 호출의 NPE 메시지는 각각 무엇인가 (예측)

```java
Objects.requireNonNullElse(null, null);
Objects.requireNonNullElseGet(null, () -> null);
Objects.requireNonNullElseGet(null, null);
```

- 세 메시지는 각각 무엇인가?
- 그 문자열들이 어디서 오는가?
- 메시지만 보고 무엇이 `null` 이었는지 구분할 수 있는가?

### 5. ★ `requireNonNullElse` 의 두 번째 인자는 언제 평가되는가 (예측)

```java
static int calls = 0;
static String make() { calls++; return "만들어진 기본값"; }

Objects.requireNonNullElse("값", make());      // (A)
Objects.requireNonNullElseGet("값", Ex::make); // (B)
Objects.requireNonNullElseGet(null, Ex::make); // (C)
```

- 세 경우의 `make()` 호출 횟수는 각각 몇 번인가?
- 이 현상의 원인은 `Objects` 의 구현인가, 자바의 일반 규칙인가?
- 같은 현상을 보이는 다른 API 는 무엇인가?

### 6. ★ NPE 메시지는 무엇에 갈리는가 (경계)

```java
String s = null;
s.length();                                    // [1]
new U(null);   // U 의 생성자가 requireNonNull(n, "name") 을 한다   // [2]
```

- `javac -g` / `javac`(기본) / `java -XX:-ShowCodeDetailsInExceptionMessages` 세 조건에서 [1]의 메시지는 어떻게 달라지는가?
- 같은 세 조건에서 [2]의 메시지는 어떻게 되는가?
- 이 차이가 "명시적 검증을 쓰는 이유"가 되는 까닭은 무엇인가?
- 그래서 NPE 메시지에 대해 하면 안 되는 것은 무엇인가?

### 7. ★ `@NonNull` 애너테이션은 런타임에 무엇을 막는가 (예측)

```java
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.PARAMETER)
@interface NonNull {}

static int len(@NonNull String s) { return s.length(); }
len(null);
```

- 이 코드는 컴파일되는가?
- 실행하면 무슨 일이 일어나는가?
- 애너테이션이 실제로 하는 일과 안 하는 일은 각각 무엇인가?
- 그럼에도 애너테이션을 쓰는 것이 의미 있으려면 무엇이 필요한가?

### 8. 컬렉션마다 `null` 정책이 어떻게 다른가 (경계)

```java
new HashMap<>().put(null, null);
Map.of("a", null);
List.of("a", null);
Arrays.asList("a", null);
new TreeSet<>(Arrays.asList("a", null));
```

- 다섯 중 성공하는 것과 NPE 가 나는 것은 각각 무엇인가?
- `HashMap` 에서 "키가 없다"와 "값이 `null` 이다"를 어떻게 구분하는가?
- `TreeSet` 이 `null` 을 거부하는 이유는 어느 주제와 이어지는가?

### 9. 스트림 수집기의 `null` 정책은 어떻게 갈리는가 (예측)

```java
rows.stream().collect(Collectors.toMap(Row::key, Row::value));   // value 에 null 이 있다
rows.stream().collect(Collectors.groupingBy(Row::value));        // value 에 null 이 있다
dirty.stream().toList();                                          // dirty 에 null 원소가 있다
dirty.stream().collect(Collectors.toUnmodifiableList());
List.copyOf(dirty);
```

- 다섯 중 NPE 가 나는 것은 무엇인가?
- `groupingBy` 의 NPE 메시지는 무엇인가?
- `toList()` 계열이 갈리는 기준은 무엇인가?

### 10. 반환값을 `null` 로 줄 때와 `Optional` 로 줄 때 (예측)

```java
@Nullable static String       findNull(String k) { return DB.get(k); }
static Optional<String>       findOpt (String k) { return Optional.ofNullable(DB.get(k)); }

findNull("없음").length();
findOpt("없음").orElse("기본");
```

- 두 호출의 결과는 각각 무엇인가?
- 첫째의 NPE 메시지는 어느 정보를 담고 있는가?
- 둘째에서 같은 사고가 일어날 수 없는 이유는 무엇인가?
- `Optional` 을 반환 자리 **밖**에 쓰면 안 되는 이유는 어디에 있는가?

### 11. 어디에 무엇을 쓰나 (왜)

- 필수 인자 검증·선택 기본값·"없을 수 있는 조회"에 각각 무엇을 쓰는가?
- 컬렉션을 돌려주는 메서드는 없을 때 무엇을 돌려주는가?
- `if (x != null)` 을 만나는 곳마다 붙이면 무엇이 나빠지는가?
- `requireNonNull` 에 메시지를 안 주면 무엇을 잃는가?

### 12. 다른 주제와 잇기 (연결)

- `Optional` 과 `requireNonNull` 은 무엇이 다른 일을 하는가?
- `record` 에서 검증은 어디에 쓰는가?
- JDK 자신이 이 관용구를 쓰는 자리를 둘 이상 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
