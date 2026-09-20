# java/syntax/25 — 예외: checked/unchecked·전파·다중 `catch`·재던지기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력·에러·스택트레이스를 맞힐 수 있는지**를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 열 개 중 무엇이 checked 인가 (경계)

`IOException` · `FileNotFoundException` · `SQLException` · `RuntimeException` · `IllegalArgumentException` · `NullPointerException` · `Exception` · `Error` · `StackOverflowError` · `Throwable`

- 각각 checked 인가 unchecked 인가?
- 경계선을 한 문장으로 말하면 무엇인가?
- `Throwable` 은 어느 쪽인가, 그것을 어떻게 확인할 수 있는가?
- `catch (Exception e)` 는 `StackOverflowError` 를 잡는가?

### 2. 이 네 코드는 각각 어떤 컴파일 에러를 내는가 (예측)

```java
// (A)
static void risky() throws IOException { }
public static void main(String[] a) { risky(); }

// (B)
try { System.out.println("아무것도 안 던진다"); } catch (IOException e) { }

// (C)
try { mayThrowFnf(); }
catch (IOException e) { } catch (FileNotFoundException e) { }

// (D)
try { throw new IOException("a"); }
catch (IOException | RuntimeException e) { e = new RuntimeException("재대입"); }
```

- 넷의 에러 문구는 각각 무엇인가?
- (B)에서 `IOException` 대신 `RuntimeException` 을 잡으면 어떻게 되는가, 왜 다른가?
- (D)가 말해 주는 다중 `catch` 변수의 성질은 무엇인가?

### 3. 다중 `catch` 는 어느 절이 걸리는가 (예측)

```java
try { throwIt(kind); }                      // kind 별로 FNF / IOException / IAE / NPE 를 던진다
catch (FileNotFoundException e) { ... }
catch (IOException e) { ... }
catch (IllegalArgumentException | NullPointerException e) { ... }
```

- 네 가지 `kind` 에 대해 각각 어느 `catch` 가 걸리는가?
- 세 번째 절에서 `e` 의 **정적 타입**은 무엇인가?
- 첫 두 절의 순서를 바꾸면 무슨 일이 생기는가?

### 4. `finally` 가 있는 이 다섯 메서드의 결과는 (예측)

```java
static int overwrite()   { try { return 1; } finally { return 2; } }
static int swallow()     { try { throw new IllegalStateException("사라진다"); } finally { return 3; } }
static int mutateAfter() { int x = 1; try { return x; } finally { x = 99; } }
static StringBuilder mutateObject() { StringBuilder sb = new StringBuilder("a");
                                      try { return sb; } finally { sb.append("b"); } }
static void replace()    { try { throw new IllegalStateException("원래"); }
                           finally { throw new RuntimeException("나중"); } }
```

- 다섯의 결과(반환값 또는 밖으로 나오는 예외)는 각각 무엇인가?
- `mutateAfter` 와 `mutateObject` 의 결과가 갈리는 이유는 무엇인가?
- `replace()` 에서 원래 예외는 `getCause` 나 `getSuppressed` 에 남는가?
- 컴파일러는 이 중 어느 것을 경고하고, 그 경고를 보려면 무엇이 필요한가?

### 5. `try { return f(); } finally { g(); }` 의 실행 순서 (예측)

- `f()` 평가 · `g()` 실행 · 반환값 전달의 순서는 무엇인가?
- 그 순서를 실행 출력으로 어떻게 확인할 수 있는가?
- `finally` 가 있는 메서드의 바이트코드에서 `finally` 의 코드는 몇 번 나타나는가, 왜인가?

### 6. 원인 사슬을 이었을 때와 버렸을 때 스택트레이스 (예측)

```java
static void driver()     { throw new IllegalStateException("커넥션이 닫혔다"); }
static void repository() { try { driver(); }
                           catch (IllegalStateException e) {
                               throw new DataAccessException("회원 조회 실패(id=42)", e); } }
```

- `repository()` 를 잡아 `printStackTrace()` 하면 무엇이 찍히는가?
- 두 번째 인자를 `null` 로 바꾸면 출력이 어떻게 달라지는가?
- 출력의 `... 1 more` 는 무엇을 뜻하는가?
- `initCause` 를 두 번 부르면 무슨 일이 생기는가?

### 7. 예외를 삼키는 것이 왜 최악인가 (왜)

- 빈 `catch` 로 삼켰을 때 **관측 가능한 흔적**은 무엇이 남는가?
- 같은 상황에서 예외를 올렸을 때와 비교해 무엇이 달라지는가?
- `printStackTrace()` 는 삼키기보다 낫지만 운영에서 왜 부족한가?
- 삼키는 것이 정당한 경우가 있다면 어떤 경우이고 그때 무엇을 해야 하는가?

### 8. 정밀 재던지기는 무엇을 살려 주는가 (왜)

```java
static void precise() throws IOException, SQLException {
    try { mayThrow(); }                     // throws IOException, SQLException
    catch (Exception e) { log(e); throw e; }
}
```

- 이 코드가 `throws Exception` 이 아니어도 컴파일되는 이유는 무엇인가?
- 이 규칙은 어느 버전부터인가?
- `catch` 블록 안에서 `e = new Exception(...)` 을 하면 어떻게 되는가?

### 9. `throws` 는 오버라이드에서 어떻게 다뤄지는가 (경계)

- 하위 클래스가 상위보다 **넓은** `throws` 를 다는 것은 허용되는가?
- 좁히거나 아예 없애는 것은 허용되는가?
- `throws` 를 없앤 하위 타입의 인스턴스를 **상위 타입 변수**로 받아 호출하면, 호출부는 여전히 처리해야 하는가?
- unchecked 예외를 `throws` 에 적는 것은 의미가 있는가?

### 10. 새 예외를 만들 때 checked 와 unchecked 중 무엇을 고르나 (경계)

- 선택 기준을 한 문장으로 말하면 무엇인가?
- 프레임워크·라이브러리가 대개 unchecked 를 고르는 이유는 무엇인가?
- 람다나 스트림 안에서 던질 예외는 어느 쪽이어야 하는가, 왜인가?
- 직접 만든 예외 클래스에 어떤 생성자를 열어 둬야 하는가, 왜인가?

### 11. 다른 주제와 잇기 (연결)

- `finally` 에서 예외가 예외를 덮는 문제를 언어가 자동으로 막아 주는 문법은 무엇인가?
- 다중 `catch` 변수가 암묵적 `final` 인 것은 어느 주제와 이어지는가?
- 운영에서의 실패 처리 패턴(재시도·차단기)과 이 주제의 경계는 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
