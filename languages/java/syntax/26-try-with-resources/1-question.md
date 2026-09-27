# java/syntax/26 — `try`-with-resources: `AutoCloseable`·suppressed·`finally` 순서 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력·스택트레이스를 맞힐 수 있는지**를 묻는다.
> 선행: [`../25-exceptions/`](../25-exceptions/) 의 `finally` 함정.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 블록의 출력 순서를 예측하라 (예측)

```java
static class Res implements AutoCloseable {
    final String name;
    Res(String name) { this.name = name; System.out.println("  열기: " + name); }
    void use() { System.out.println("  사용: " + name); }
    public void close() { System.out.println("  닫기: " + name); }
}

try (Res a = new Res("A"); Res b = new Res("B"); Res c = new Res("C")) {
    a.use(); b.use(); c.use();
}
```

- 아홉 줄의 출력 순서는 무엇인가?
- 닫는 순서가 그렇게 정해진 이유는 무엇인가?
- JDBC 에서 이 순서가 왜 중요한가?

### 2. suppressed 는 언제 생기는가 (예측)

```java
// close 가 항상 IllegalStateException("close 실패: A") 를 던지는 자원 A 가 있다
// (가) try (Res a = A) { a.use(); }
// (나) try (Res a = A) { a.use(); throw new RuntimeException("본문 예외"); }
```

- (가)와 (나) 각각에서 **밖으로 나오는 예외**와 **`getSuppressed().length`** 는 무엇인가?
- 본문과 `close` 중 어느 쪽이 주 예외가 되는가, 그 근거는 어디에 적혀 있는가?
- 본문도 정상이고 `close` 도 정상이면 suppressed 는 몇 개인가?

### 3. 자원 셋이 전부 `close` 에서 실패하면 (예측)

```java
try (Res a = new Res("A", true);      // true = close 에서 던진다
     Res b = new Res("B", true);
     Res c = new Res("C", true)) {
    a.use();
}
```

- 닫기 출력 순서는 무엇인가?
- 밖으로 나오는 예외는 어느 자원의 것인가?
- `getSuppressed()` 에는 무엇이 몇 개 들어 있고 순서는 어떻게 되는가?
- 하나가 실패하면 나머지는 안 닫히는가?

### 4. 같은 상황을 손으로 쓰면 무엇을 잃는가 (예측)

```java
Res a = new Res("A", true);          // close 가 던진다
try {
    a.use();
    throw new RuntimeException("본문 예외");
} finally {
    a.close();
}
```

- 밖으로 나오는 예외는 무엇인가?
- `getSuppressed().length` 는 무엇인가?
- 본문 예외는 `getCause()` 에 남는가?
- 이 손실이 특히 나쁜 이유를 실무 상황으로 설명할 수 있는가?

### 5. 스택트레이스에서 suppressed 는 어떻게 보이는가 (예측)

```java
static void work() {
    try (Res a = new Res("A"); Res b = new Res("B")) {   // 둘 다 close 에서 던진다
        throw new RuntimeException("본문 예외");
    }
}
// work() 를 잡아 printStackTrace() 한다
```

- 출력의 첫 줄은 무엇인가?
- `Suppressed:` 줄은 몇 개이고 어떤 순서로 나오는가?
- `Suppressed:` 블록 안의 `... 1 more` 는 무엇을 뜻하는가?
- `log.error(e.getMessage())` 로 찍으면 무엇이 사라지는가?

### 6. 이 문법은 무엇으로 펼쳐지는가 (왜)

- `javap -c` 로 찍으면 소스에 없는 어떤 메서드 호출이 나타나는가?
- 예외 테이블의 행은 몇 개이고 각각 무엇을 감싸는가?
- `close()` 호출은 바이트코드에 몇 번 나타나는가, 왜인가?
- 자원이 `null` 일 수 있으면 컴파일러가 무엇을 더 넣는가, 그때 런타임 동작은?

### 7. `AutoCloseable` 과 `Closeable` 의 계약 차이 (경계)

- 두 인터페이스의 `close()` 는 각각 무엇을 던질 수 있는가?
- 둘 중 **멱등성을 요구하는 쪽**은 어디이고, 그것은 어디에 적혀 있는가?
- `AutoCloseable` 구현을 `try`-with-resources 에 쓰면 왜 checked 예외 처리가 강제되는가, 그 컴파일 에러 문구는?
- 그 강제를 없애려면 구현에서 무엇을 하는가?

### 8. `close()` 를 만들 때 지켜야 할 것 (경계)

- `close()` 가 실패할 수 있을 때 **자원 해제와 예외 던지기 중 무엇을 먼저** 해야 하는가, 왜인가?
- `close()` 에서 `InterruptedException` 을 던지면 안 되는 이유는 무엇인가?
- `close()` 를 멱등하게 만드는 것이 권장되는 이유는 무엇인가?

### 9. 자원 변수의 제약 (예측)

```java
// (A) try (R r = new R()) { r = new R(); }
// (B) R r = new R(); r = new R(); try (r) { }
// (C) class NotRes { public void close() {} }  ... try (NotRes r = new NotRes()) { }
```

- 셋의 컴파일 에러 문구는 각각 무엇인가?
- (B)의 `try (r)` 형태는 어느 버전부터인가, 그것을 어떻게 확인할 수 있는가?
- (C)가 말해 주는 "자원이 되기 위한 조건"은 무엇인가?

### 10. 언제 이 문법을 쓰면 안 되는가 (경계)

- 메서드 파라미터로 받은 `InputStream` 을 `try`-with-resources 에 넣어도 되는가?
- `new Scanner(System.in)` 은 닫아야 하는가?
- 컬렉션에서 만든 `Stream` 과 `Files.lines` 가 준 `Stream` 중 닫아야 하는 것은 어느 쪽인가?
- `ReentrantLock` 에는 왜 이 문법을 못 쓰는가?

### 11. 다른 주제와 잇기 (연결)

- 이 문법이 해결하는 `finally` 의 함정은 정확히 무엇이었나?
- 자원 변수의 암묵적 `final` 과 9+ 형태의 effectively final 조건은 어느 주제와 이어지는가?
- `ExecutorService` 를 `try`-with-resources 로 닫을 수 있는 JDK 는 어디부터인가, 그것을 어떻게 확인했는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
