# java/syntax/38 — `Optional`: 생성·소비·안티패턴 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력과 예외를 맞힐 수 있는지**를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `Optional` 은 무엇을 위해 만들어졌는가 (왜)

- javadoc 의 `@apiNote` 가 지정한 **용도 하나**는 무엇인가?
- 같은 문단이 요구하는 나머지 둘은 무엇인가?
- 그 요구 중 **언어가 강제하지 않는 것**은 무엇인가?

### 2. 이 네 줄의 출력은 무엇인가 (예측)

```java
System.out.println(Optional.of("값"));
System.out.println(Optional.ofNullable(null));
System.out.println(Optional.empty());
Optional.of(null);
```

- 앞 세 줄은 각각 무엇을 찍는가?
- 마지막 줄은 어떻게 되는가 — 예외 타입과 **메시지**는 무엇인가?
- `of` 와 `ofNullable` 을 각각 언제 쓰는가?

### 3. ★ 이 네 경우에 `expensive()` 는 몇 번 불리는가 (예측)

```java
static String expensive() { System.out.println("불렸다"); return "기본값"; }

Optional<String> some = Optional.of("값");
Optional<String> none = Optional.empty();

some.orElse(expensive());        // (A)
some.orElseGet(Ex::expensive);   // (B)
none.orElse(expensive());        // (C)
none.orElseGet(Ex::expensive);   // (D)
```

- 네 경우의 호출 횟수는 각각 몇 번인가?
- (A)가 그렇게 되는 이유는 `Optional` 의 특별한 동작인가, 자바의 일반 규칙인가?
- `orElse` 와 `orElseGet` 중 무엇을 쓸지 판정하는 기준 한 줄은 무엇인가?

### 4. 빈 `Optional` 에서 값을 꺼내려 하면 (예측)

```java
Optional<String> none = Optional.empty();
none.get();
none.orElseThrow();
none.orElseThrow(() -> new IllegalStateException("사용자가 없다"));
```

- 세 호출의 예외 타입과 메시지는 각각 무엇인가?
- `get()` 과 `orElseThrow()` 는 무엇이 같고 무엇이 다른가?
- javadoc 은 둘 중 어느 것을 쓰라고 적었는가?

### 5. ★ `Optional` 을 필드에 두면 무엇이 깨지는가 (예측)

```java
class BadUser implements Serializable {
    String name = "김";
    Optional<String> nickname = Optional.of("닉");
}
new ObjectOutputStream(out).writeObject(new BadUser());

System.out.println(Optional.of("x") instanceof Serializable);
```

- 직렬화하면 무슨 일이 일어나는가 — 예외 타입과 메시지는?
- 마지막 줄은 무엇을 찍는가?
- 대안은 어떤 형태인가?

### 6. `Optional` 을 파라미터로 두면 무엇이 늘어나는가 (경계)

```java
static String greet(Optional<String> nick) { return "안녕 " + nick.orElse("손님"); }
```

- 호출자가 넘길 수 있는 값은 몇 가지인가?
- `greet(null)` 은 어떻게 되는가?
- `null` 을 없애려고 넣은 것인데 무엇이 남았는가?
- 선택 인자가 필요하면 무엇을 쓰는가?

### 7. `Map<String, Optional<String>>` 의 상태는 몇 가지인가 (예측)

```java
Map<String, Optional<String>> m = new HashMap<>();
m.put("a", Optional.of("값"));
m.put("b", Optional.empty());

m.get("b");
m.get("없는키");
```

- 두 `get` 의 결과는 각각 무엇인가?
- 이 맵에서 구분해야 하는 상태는 몇 가지인가?
- 그중 몇 가지가 `Optional` 로 표현되고 몇 가지가 `null` 로 표현되는가?

### 8. `map` 과 `flatMap` 은 어디서 갈리는가 (예측)

```java
Optional<String> src = Optional.of("씨앗");
src.map(v -> Optional.of(v.length()));
src.flatMap(v -> Optional.of(v.length()));

Optional.of(new User("u2", null)).map(User::email);
```

- 앞 두 줄의 결과는 각각 무엇인가?
- 마지막 줄에서 `email` 이 `null` 일 때 결과는 무엇인가? 그 이유를 소스로 설명할 수 있는가?
- 둘을 고르는 기준은 무엇인가?

### 9. 스트림에서 `Optional` 을 펼치는 두 방법 (연결)

```java
ids.stream().map(Ex::find).filter(Optional::isPresent).map(Optional::get).toList();
ids.stream().map(Ex::find).flatMap(Optional::stream).toList();
```

- 두 결과는 같은가?
- 뒤의 것은 몇 버전부터 되는가?
- 뒤의 것이 더 나은 이유는 무엇인가?
- 최종 연산 중 `Optional` 을 돌려주는 것들은 무엇이고, 기본형 스트림에서는 무엇이 나오는가?

### 10. 메서드마다 버전이 어떻게 갈리는가 (경계)

- `ifPresentOrElse`·`or`·`stream`·`orElseThrow()`·`isEmpty` 는 각각 몇 버전부터인가?
- 그것을 기억이 아니라 도구로 확인하는 방법 둘은 무엇인가?
- `--release 8` 로 컴파일했을 때 `orElseThrow()` 만 에러 모양이 다른 이유는 무엇인가?

### 11. `Optional` 변수 자체가 `null` 이면 (경계)

- `Optional<String> o = null; o.isPresent();` 는 어떻게 되는가?
- javadoc 은 이것을 무엇이라고 적었는가? 강제되는가?
- 그래서 `Optional` 을 돌려주는 메서드가 지켜야 할 규율은 무엇인가?

### 12. 어디에 쓰고 어디에 안 쓰나 (왜)

- `Optional` 을 반환 타입으로 쓰는 것이 맞는 경우와, 예외를 던져야 하는 경우는 어떻게 가르는가?
- `if (opt.isPresent()) opt.get()` 이 얻은 것이 없는 이유는 무엇인가?
- `synchronized (opt)` 와 `opt == Optional.empty()` 는 왜 하면 안 되는가?

### 13. 다른 주제와 잇기 (연결)

- `Optional` 이 `null` 을 없애 주는가? 아니라면 `null` 을 막는 장치는 무엇인가?
- `Optional` 필드가 필요해 보일 때 대신 고려할 설계는 무엇인가?
- `OptionalInt`/`OptionalDouble` 에 `map` 이 없는 이유는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
