# java/syntax/26 — `try`-with-resources: `AutoCloseable`·suppressed·`finally` 순서 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·스택트레이스·컴파일 에러·바이트코드는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 실행 프로그램 넷은 **17.0.13 · 25.0.1** 에서도 돌렸다. `Ex.java (26-h)` 만 결과가 갈렸고(`ExecutorService`) 나머지는 같았다.\
> 바이트코드는 `javap -c -p` 출력을, javadoc 은 `lib/src.zip` 의 실파일을 그대로 옮겼다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 블록의 출력 순서를 예측하라

**출력** (`Ex.java (26-a)`, JDK 21.0.5 — 17·25 에서도 동일)

```text
--- 1. 닫는 순서 — 연 순서의 역순
  열기: A
  열기: B
  열기: C
  사용: A
  사용: B
  사용: C
  닫기: C
  닫기: B
  닫기: A
```

**아홉 줄의 순서**

- 열기 **A -> B -> C** (선언 순서)
- 사용 **A -> B -> C** (본문에 쓴 순서)
- 닫기 **C -> B -> A** (선언의 **역순**)

```text
열기                                        닫기
  A  ─┐                                     ┌─ A   (마지막)
  B  ─┼─ 들여놓은 순서                        ├─ B
  C  ─┘                                     └─ C   (먼저)

  스택처럼: 마지막에 넣은 것을 먼저 뺀다
```

**닫는 순서가 그렇게 정해진 이유**

- **의존 방향 때문**이다. 나중에 연 자원이 먼저 연 자원에 기대고 있을 수 있다.
- `a` 를 먼저 닫으면 `b.close()` 가 "이미 닫힌 것 위에서" 돌게 된다.
- JLS §14.20.3 이 역순을 **명세로** 정한다 — 구현 재량이 아니다.

**JDBC 에서 왜 중요한가**

```java
try (Connection c = ds.getConnection();
     PreparedStatement ps = c.prepareStatement(sql);
     ResultSet rs = ps.executeQuery()) {
    ...
}
```

- 여는 순서가 `Connection` -> `Statement` -> `ResultSet` 이므로 **닫는 순서는 `ResultSet` -> `Statement` -> `Connection`** 이 된다.
- 반대로 닫으면 `Connection` 이 이미 닫힌 뒤 `Statement.close()` 가 불려 드라이버에 따라 예외가 난다.
- 한 `try` 에 세미콜론으로 나열하기만 하면 **언어가 이 순서를 보장한다.** 손으로 쓰면 중첩 `finally` 세 겹이다.

### 2. suppressed 는 언제 생기는가

**출력** (`Ex.java (26-a)`, 17·21·25 동일)

```text
--- 2. 본문이 정상이고 close 만 실패 -> close 예외가 밖으로
  열기: A
  사용: A
  닫기: A
  밖으로 나온 것 = java.lang.IllegalStateException: close 실패: A
  suppressed 개수 = 0

--- 3. 본문도 실패하고 close 도 실패 -> 본문이 주, close 가 suppressed
  열기: A
  사용: A
  닫기: A
  밖으로 나온 것 = java.lang.RuntimeException: 본문 예외
  suppressed 개수 = 1
  suppressed: java.lang.IllegalStateException: close 실패: A
```

**(가)와 (나)의 결과**

| | 밖으로 나오는 예외 | `getSuppressed().length` |
|---|---|---|
| (가) 본문 정상, `close` 실패 | `IllegalStateException: close 실패: A` | **0** |
| (나) 본문 실패, `close` 실패 | `RuntimeException: 본문 예외` | **1** |

```text
경우 나누기 — 네 가지뿐이다

  본문    close    밖으로 나오는 것          suppressed
  ----    -----    -----------------        -----------
  정상    정상     없음                      —
  정상    실패     close 예외                0개
  실패    정상     본문 예외                 0개
  실패    실패     본문 예외                 close 예외   <- 여기서만 생긴다
```

- **suppressed 는 둘 다 던졌을 때만 생긴다.** 하나만 던지면 그것이 그냥 주 예외로 나간다.

**어느 쪽이 주 예외가 되는가, 근거는 어디에**

- **본문 예외가 주 예외**다.
- 근거는 `Throwable.addSuppressed` 의 javadoc 이다(`lib/src.zip` 에서 읽은 원문).

> In these situations, only one of the thrown exceptions can be propagated. In the `try`-with-resources statement, when there are two such exceptions, the exception originating from the `try` block is propagated and the exception from the `finally` block is added to the list of exceptions suppressed by the exception from the `try` block. As an exception unwinds the stack, it can accumulate multiple suppressed exceptions.

- 같은 javadoc 이 **cause 와 suppressed 의 차이**도 설명한다 — cause 는 **인과**(A 때문에 B), suppressed 는 **형제 블록의 독립 사고**다.
- 이 선택이 맞는 이유: **본문 예외가 "왜 실패했나"를 담고 있고** `close` 실패는 대개 그 결과다.

**둘 다 정상이면**

- 예외가 아예 안 나오므로 **suppressed 를 물어볼 대상도 없다.**

### 3. 자원 셋이 전부 `close` 에서 실패하면

**출력** (`Ex.java (26-a)`)

```text
--- 4. 자원 셋이 전부 close 에서 실패하면 suppressed 가 둘
  열기: A
  열기: B
  열기: C
  사용: A
  닫기: C
  닫기: B
  닫기: A
  밖으로 나온 것 = java.lang.IllegalStateException: close 실패: C
  suppressed 개수 = 2
  suppressed: java.lang.IllegalStateException: close 실패: B
  suppressed: java.lang.IllegalStateException: close 실패: A
```

**닫기 출력 순서**

- **C -> B -> A.** 역순 규칙은 `close` 가 실패해도 그대로다.

**밖으로 나오는 예외**

- **C 의 것**이다. 본문이 정상이므로 **처음 던진 `close` 예외가 주 예외**가 된다.
- C 가 처음 닫히니까 C 의 예외가 주 예외다.

**`getSuppressed()` 의 내용과 순서**

- **B, A 순서로 둘**이 들어 있다.

```text
  닫기 순서       예외 처리
  ----------      ----------------------------------
  C  실패   ->    주 예외가 된다 (아직 아무것도 없었으므로)
  B  실패   ->    C 의 예외에 addSuppressed(B)
  A  실패   ->    C 의 예외에 addSuppressed(A)

  주 예외: C
  suppressed: [B, A]   <- 닫힌 순서대로 쌓인다
```

**하나가 실패하면 나머지는 안 닫히는가**

- **전부 닫힌다.** 출력에 `닫기: C`·`닫기: B`·`닫기: A` 가 다 나왔다.
- 이것이 손으로 쓴 코드와 결정적으로 다른 점이다 — 중첩 `finally` 를 잘못 쓰면 **첫 실패에서 멈춰 나머지가 샌다.**

자원 생성 중 실패하면 **이미 연 것만** 닫는다.

```text
--- 5. 자원 생성 도중 실패하면 이미 연 것만 닫는다
  열기: A
  닫기: A
  밖으로 나온 것 = java.lang.IllegalArgumentException: 자원 B 생성 실패
```

- `A` 는 열렸으니 닫고, `B` 는 안 만들어졌으니 닫을 것이 없고, `C` 는 시작도 안 했다.

### 4. 같은 상황을 손으로 쓰면 무엇을 잃는가

**출력** (`Ex.java (26-a)`)

```text
--- 6. 손으로 쓴 try-finally — 본문 예외가 사라진다
  열기: A
  사용: A
  닫기: A
  밖으로 나온 것 = java.lang.IllegalStateException: close 실패: A
  suppressed 개수 = 0
  본문 예외는 어디 갔나 = 사라졌다
```

**밖으로 나오는 예외**

- **`IllegalStateException: close 실패: A`** — `close` 예외다.

**`getSuppressed().length`**

- **0** 이다.

**본문 예외는 `getCause()` 에 남는가**

- **안 남는다.** 어디에도 없다.
- `finally` 가 `throw` 로 끝나면 진행 중이던 예외가 **버려진다**(JLS §14.20.2). 이것이 [`../25-exceptions/`](../25-exceptions/) 의 `finally` 함정 셋째다.

```text
손으로 쓴 try-finally                        try-with-resources
+-----------------------------------+      +-----------------------------------+
| 밖: close 실패: A                  |      | 밖: 본문 예외                      |
| suppressed: 0                     |      | suppressed: 1 (close 실패: A)     |
| "본문 예외"는 흔적도 없다           |      | 둘 다 남는다                       |
+-----------------------------------+      +-----------------------------------+
  두 칸 모두 실제 실행 결과다 (26-a 의 6번과 3번)
```

**왜 특히 나쁜가 — 실무 상황으로**

- 쿼리가 **제약 위반**으로 실패해 트랜잭션이 깨졌다고 하자.
- 트랜잭션이 깨진 상태라 `connection.close()` 도 실패한다.
- 손으로 쓴 코드의 로그에는 **"커넥션을 닫을 수 없습니다"** 만 남는다.
- 진짜 원인인 **"어떤 제약을 어떤 값으로 위반했는지"** 는 사라진다.
- 즉 **`close` 실패는 대개 본문 실패의 결과인데, 결과가 원인을 덮어쓴다.**
- 그래서 자원 정리에 `finally` 를 쓰는 것은 **스타일 문제가 아니라 정보 손실 문제**다.

### 5. 스택트레이스에서 suppressed 는 어떻게 보이는가

**출력** (`Ex.java (26-b)`, `printStackTrace(System.out)` — 출력 그대로. 17·21·25 동일)

```text
--- printStackTrace() 가 찍는 것
java.lang.RuntimeException: 본문 예외
	at Ex.work(Ex.java:10)
	at Ex.main(Ex.java:16)
	Suppressed: java.lang.IllegalStateException: close 실패: B
		at Ex$Res.close(Ex.java:5)
		at Ex.work(Ex.java:9)
		... 1 more
	Suppressed: java.lang.IllegalStateException: close 실패: A
		at Ex$Res.close(Ex.java:5)
		at Ex.work(Ex.java:9)
		... 1 more
```

잡지 않으면(uncaught) 형태가 같고 첫 줄만 달라진다.

```text
--- 잡지 않으면 (uncaught)
Exception in thread "main" java.lang.RuntimeException: 본문 예외
	at Ex.work(Ex.java:10)
	at Ex.main(Ex.java:36)
	Suppressed: java.lang.IllegalStateException: close 실패: B
		at Ex$Res.close(Ex.java:5)
		at Ex.work(Ex.java:9)
		... 1 more
	Suppressed: java.lang.IllegalStateException: close 실패: A
		at Ex$Res.close(Ex.java:5)
		at Ex.work(Ex.java:9)
		... 1 more
```

**첫 줄**

- **`java.lang.RuntimeException: 본문 예외`** — 주 예외다.

**`Suppressed:` 줄의 개수와 순서**

- **둘**이다. **B 먼저, 그다음 A** — 닫힌 순서(역순)대로다.
- `Suppressed:` 블록은 **한 단계 더 들여쓰기** 되어 있고, 그 안의 `at` 줄은 **두 단계** 들여쓰기다.\
  로그를 볼 때 이 들여쓰기가 "주 예외의 부속"임을 표시한다.

**`... 1 more`**

- **위쪽 트레이스와 겹치는 프레임 수**다.
- `Suppressed` 블록의 실제 스택은 `Ex$Res.close(5)` -> `Ex.work(9)` -> `Ex.main(16)` 인데, `Ex.main(16)` 은 위에 이미 찍혔으므로 **생략하고 개수만 적었다.**
- 정보가 빠진 게 아니라 중복을 안 찍은 것이다.\
  *(이 생략 형식은 `Throwable.printStackTrace` 의 구현 세부다.)*

**`log.error(e.getMessage())` 로 찍으면**

```text
잘못된 로깅                                  올바른 로깅
+-----------------------------------+      +-----------------------------------+
| log.error(e.getMessage());        |      | log.error("작업 실패", e);         |
|                                   |      |                                   |
| 본문 예외                          |      | 위의 전체 트레이스가 찍힌다         |
| 끝.                               |      | Suppressed 둘 포함                |
+-----------------------------------+      +-----------------------------------+
```

- **스택트레이스와 suppressed 가 통째로 사라진다.** 메시지 한 줄만 남는다.
- **예외 객체를 인자로 넘겨야** 한다 — `log.error("...", e)`.
- 이것은 [`../25-exceptions/`](../25-exceptions/) 의 "`printStackTrace` 대 로깅" 과 같은 계열의 실수다.

`Suppressed:` 와 `Caused by:` 는 **한 트레이스에 같이 나올 수 있다.**

```text
--- suppressed 안에 cause 까지 있을 때
java.lang.RuntimeException: 본문 예외
	at Ex.main(Ex.java:22)
	Suppressed: java.lang.IllegalStateException: close 실패: A
		at Ex$Res.close(Ex.java:5)
		at Ex.main(Ex.java:21)
Caused by: java.lang.IllegalArgumentException: 본문의 원인
	... 1 more
```

- **`Suppressed:` 가 먼저, `Caused by:` 가 나중**이다.
- 주 예외에 바로 붙은 것이 suppressed 이고, 원인은 그 아래 층이기 때문이다.

### 6. 이 문법은 무엇으로 펼쳐지는가

**`javap -c -p Ex.class` 출력 그대로** (`Ex.java (26-f)`, JDK 21.0.5)

```text
  static void twr();
    Code:
       0: new           #7                  // class Ex$R
       3: dup
       4: invokespecial #9                  // Method Ex$R."<init>":()V
       7: astore_0
       8: getstatic     #10                 // Field java/lang/System.out:Ljava/io/PrintStream;
      11: ldc           #16                 // String 본문
      13: invokevirtual #18                 // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      16: aload_0
      17: invokevirtual #24                 // Method Ex$R.close:()V
      20: goto          39
      23: astore_1
      24: aload_0
      25: invokevirtual #24                 // Method Ex$R.close:()V
      28: goto          37
      31: astore_2
      32: aload_1
      33: aload_2
      34: invokevirtual #29                 // Method java/lang/Throwable.addSuppressed:(Ljava/lang/Throwable;)V
      37: aload_1
      38: athrow
      39: return
    Exception table:
       from    to  target type
           8    16    23   Class java/lang/Throwable
          24    28    31   Class java/lang/Throwable
```

**소스에 없는 어떤 호출이 나타나는가**

- **`java/lang/Throwable.addSuppressed:(Ljava/lang/Throwable;)V`** (오프셋 34).
- 소스에는 `addSuppressed` 라는 글자가 없다. **컴파일러가 넣었다.**

**예외 테이블의 행과 각각이 감싸는 것**

| 행 | 구간 | 무엇을 감싸나 |
|---|---|---|
| `8 ~ 16 -> 23` | 본문 | 본문이 던진 예외를 잡아 `astore_1` 에 저장 |
| `24 ~ 28 -> 31` | 예외 경로의 `close()` | **`close()` 자체가 던진 예외**를 잡아 `astore_2` 에 저장 |

- 둘째 행이 이 문법의 핵심이다 — **`close()` 를 또 한 겹 감싸고 있으므로** 거기서 난 예외를 붙잡아 `addSuppressed` 로 넘길 수 있다.

**`close()` 호출은 몇 번 나타나는가**

- **두 번** — 오프셋 **17**(정상 경로)과 **25**(예외 경로).
- 이유: 나가는 길이 둘(정상 종료, 예외 전파)이고 **각 길에 마무리 코드를 복사해 박아야** 하기 때문이다.
- `finally` 의 코드 복사와 같은 성질이다([`../25-exceptions/`](../25-exceptions/) 5번에서 셋으로 복사된 것을 봤다).

```text
소스 다섯 줄                               클래스 파일이 하는 일

try (R r = new R()) {                      1. r 을 만든다               (0~7)
    본문                                    2. 본문을 돈다                (8~13)
}                                          3-a. 정상이면 close()         (17)
                                           3-b. 예외면 저장하고          (23)
                                                close()                 (25)
                                                close 도 던지면
                                                addSuppressed           (34)
                                                본문 예외를 athrow        (38)
```

**자원이 `null` 일 수 있으면**

**`javap -c -p Ex.class` 출력** (`Ex.java (26-g)` — 자원을 `maybeNull()` 로 받았다)

```text
      12: aload_0
      13: ifnull        43
      16: aload_0
      17: invokevirtual #27                 // Method Ex$R.close:()V
      20: goto          43
      23: astore_1
      24: aload_0
      25: ifnull        41
      28: aload_0
      29: invokevirtual #27                 // Method Ex$R.close:()V
```

- **`ifnull` 검사가 두 경로 모두에 들어간다.**
- 런타임 동작: 자원이 `null` 이면 **`close()` 를 건너뛴다.** NPE 가 안 난다.

```text
본문 (자원이 null)
NPE 없이 지나갔다
```

- 이것도 명세다(JLS §14.20.3) — 구현 재량이 아니다.

### 7. `AutoCloseable` 과 `Closeable` 의 계약 차이

**출력** (`Ex.java (26-c)`, 17·21·25 동일)

```text
AutoCloseable.close 의 throws = [class java.lang.Exception]
Closeable.close 의 throws     = [class java.io.IOException]
Closeable 은 AutoCloseable 의 하위 = true
```

**각각 무엇을 던질 수 있는가**

- `AutoCloseable.close()` -> **`Exception`** (checked 전부)
- `Closeable.close()` -> **`IOException`** 만

**멱등성을 요구하는 쪽과 그 근거**

- **`Closeable`** 이다. javadoc 원문이다.

> Closes this stream and releases any system resources associated with it. **If the stream is already closed then invoking this method has no effect.**

- `AutoCloseable` 은 **명시적으로 요구하지 않는다.** 역시 javadoc 원문이다.

> Note that unlike the `close` method of `Closeable`, this `close` method is **not** required to be idempotent. In other words, calling this `close` method more than once may have some visible side effect, unlike `Closeable.close` which is required to have no effect if called more than once.
>
> However, implementers of this interface are strongly encouraged to make their `close` methods idempotent.

```text
      AutoCloseable  (java.lang, @since 1.7)
        close() throws Exception
        멱등 요구 없음 (권장만)
              |
        상속
              |
      Closeable      (java.io, @since 1.5)
        close() throws IOException
        멱등 요구 있음
```

**왜 checked 예외 처리가 강제되는가, 그 에러 문구**

**컴파일 에러** (`Ex.java (26-d4)`)

```text
Ex.java:4: error: unreported exception Exception; must be caught or declared to be thrown
        try (AC a = new AC()) { }
                ^
  exception thrown from implicit call to close() on resource variable 'a'
1 error
```

- **컴파일러가 `close()` 를 불러 준다.** 그 호출은 `throws Exception` 이므로 **checked 예외 처리 규칙이 그대로 걸린다**([`../25-exceptions/`](../25-exceptions/) 2번).
- 에러 문구가 친절하다 — **`exception thrown from implicit call to close()`** 라고 "내가 안 쓴 호출"임을 밝힌다.

**강제를 없애려면**

- **구현에서 `throws` 를 좁히거나 아예 없앤다.**

```java
static class Quiet implements AutoCloseable {
    @Override public void close() { ... }     // throws 없음
}
```

- 실행으로 확인했다 — `throws` 가 없으면 `try`-with-resources 에서 **아무 처리도 요구하지 않는다.**

```text
본문
Quiet.close (throws 없음)
```

- `AutoCloseable` javadoc 도 그렇게 권한다.

> While this interface method is declared to throw `Exception`, implementers are *strongly* encouraged to declare concrete implementations of the `close` method to throw more specific exceptions, or to throw no exception at all if the close operation cannot fail.

### 8. `close()` 를 만들 때 지켜야 할 것

**자원 해제와 예외 던지기 중 무엇을 먼저**

- **자원을 먼저 놓고 나서 던진다.** `AutoCloseable.close` javadoc 원문이다.

> Cases where the close operation may fail require careful attention by implementers. It is strongly advised to relinquish the underlying resources and to internally *mark* the resource as closed, prior to throwing the exception. The `close` method is unlikely to be invoked more than once and so this ensures that the resources are released in a timely manner.

- 이유는 javadoc 이 직접 적는다 — **`close` 는 두 번 불릴 가능성이 낮다.**\
  던지고 나면 아무도 다시 안 부르므로, 먼저 놓지 않으면 **자원이 샌다.**
- 순서: (1) 내부 자원 해제 (2) 닫혔다고 표시 (3) 그다음 예외.

**`InterruptedException` 을 던지면 안 되는 이유**

- javadoc 원문이다.

> *Implementers of this interface are also strongly advised to not have the `close` method throw `InterruptedException`.*\
> This exception interacts with a thread's interrupted status, and runtime misbehavior is likely to occur if an `InterruptedException` is suppressed.

- **suppressed 로 밀려나면 인터럽트 신호가 조용히 사라진다.**
- 주 예외만 보고 처리하는 상위 코드는 **스레드가 인터럽트됐다는 사실을 모른다.**
- 일반화하면 javadoc 의 다음 문장이 된다 — "if it would cause problems for an exception to be suppressed, the `AutoCloseable.close` method should not throw it."

**멱등하게 만드는 것이 권장되는 이유**

- `AutoCloseable` 은 요구하지 않지만 **javadoc 이 강하게 권한다**(7번의 인용 마지막 문장).
- 실무 이유: **정리 경로가 겹칠 수 있다.**\
  `try`-with-resources 가 닫았는데 종료 훅이나 풀 반납 코드가 또 닫는 일이 흔하다.
- 멱등이 아니면 두 번째 호출에서 엉뚱한 예외가 나거나 남의 자원을 닫는다.
- 구현은 보통 `private boolean closed;` 플래그 하나다.

### 9. 자원 변수의 제약

**컴파일 에러** (전부 `javac`, JDK 21.0.5)

**(A)** 자원 변수 재대입 (`Ex.java (26-d1)`)

```text
Ex.java:5: error: auto-closeable resource r may not be assigned
            r = new R();
            ^
1 error
```

**(B)** effectively final 이 아닌 변수를 자원으로 (`Ex.java (26-d3)`)

```text
Ex.java:6: error: variable r used as a try-with-resources resource neither final nor effectively final
        try (r) { }
             ^
1 error
```

**(C)** `AutoCloseable` 이 아닌 타입 (`Ex.java (26-d2)`)

```text
Ex.java:4: error: incompatible types: try-with-resources not applicable to variable type
        try (NotRes r = new NotRes()) { }
                    ^
    (NotRes cannot be converted to AutoCloseable)
1 error
```

**(A)(B)의 공통 이유**

- **닫을 대상이 흔들리면 안 된다.**
- 본문에서 변수가 다른 객체를 가리키게 되면 **무엇을 닫아야 하는지 정해지지 않는다.**\
  연 것을 닫을지, 지금 가리키는 것을 닫을지 답이 없다.
- 그래서 `try` 안에서 선언한 자원은 **암묵적 `final`**, 밖에서 가져온 변수는 **effectively final** 이어야 한다.
- effectively final 개념은 [`../03-variables-and-assignment/`](../03-variables-and-assignment/) 가 정본이다.

**`try (r)` 형태는 어느 버전부터인가, 어떻게 확인하나**

**`javac --release` 로 확인** (`Ex.java (26-e)`, JDK 21.0.5 의 javac)

```text
=== --release 8 ===
Ex.java:5: error: variables in try-with-resources are not supported in -source 8
        try (outside) { System.out.println("본문"); }
                    ^
  (use -source 9 or higher to enable variables in try-with-resources)
1 error
=== --release 9 ===
OK
=== 기본(21) ===
OK
```

- **Java 9 부터**다. 에러 메시지가 직접 알려 준다 — `use -source 9 or higher`.
- 이렇게 `--release` 를 바꿔 찍으면 **"몇 부터인가"를 기억이 아니라 도구로** 확인할 수 있다.
- 7~8 에서는 `try (Quiet ref = outside2) { }` 처럼 **새 변수로 한 번 더 받아야** 했다.

**(C)가 말해 주는 조건**

- **`AutoCloseable` 을 구현해야 한다.** `close()` 라는 메서드가 있는 것만으로는 안 된다.
- 자바는 구조적 타이핑을 하지 않는다 — **이름이 같아도 인터페이스를 선언해야** 한다.
- `Closeable` 은 `AutoCloseable` 의 하위이므로 당연히 된다.

### 10. 언제 이 문법을 쓰면 안 되는가

**파라미터로 받은 `InputStream`**

- **넣으면 안 된다.**
- **"내가 연 것만 내가 닫는다."** 받아 온 자원을 닫으면 **준 쪽이 계속 쓰려다 깨진다.**
- 호출자가 같은 스트림으로 뒤이어 무언가를 하려던 것이라면 그 코드가 `IOException: Stream closed` 로 터진다.

**`new Scanner(System.in)`**

- **닫지 않는다.**
- `Scanner.close()` 는 **감싼 소스도 닫는다.** javadoc 원문이다(`lib/src.zip` 의 `Scanner.java`).

> If this scanner has not yet been closed then if its underlying `readable` also implements the `Closeable` interface then the readable's `close` method will be invoked.

- `System.in` 이 닫히면 그 뒤 어떤 입력도 못 읽는다.
- `Scanner` 자체는 `Closeable` 이다(리플렉션으로 확인했다) — **닫을 수 있다는 것과 닫아야 한다는 것은 다르다.**

**두 종류의 `Stream`**

```text
컬렉션에서 만든 Stream                       Files.lines 가 준 Stream
+-----------------------------------+      +-----------------------------------+
| list.stream()                     |      | Files.lines(path)                 |
| 닫을 필요 없다                     |      | **닫아야 한다**                    |
| 붙잡고 있는 OS 자원이 없다          |      | 파일 핸들을 쥐고 있다              |
+-----------------------------------+      +-----------------------------------+
```

- `Stream` 은 둘 다 `AutoCloseable` 이다(리플렉션으로 확인했다). 차이는 **무엇을 붙잡고 있느냐**다.
- `AutoCloseable` javadoc 이 이 구분을 직접 적는다.

> However, when using facilities such as `java.util.stream.Stream` that support both I/O-based and non-I/O-based forms, `try`-with-resources blocks are in general unnecessary when using non-I/O-based forms.

- `Files.lines`·`Files.walk`·`Files.list` 는 I/O 기반이므로 **반드시 닫는다.** 안 닫으면 파일 디스크립터가 샌다.\
  자세한 것은 목록의 **57번 주제**.

**`ReentrantLock` 에 못 쓰는 이유**

- **`AutoCloseable` 을 구현하지 않기 때문이다.** 리플렉션으로 확인했다(`Ex.java (26-h)`).

```text
java.util.concurrent.locks.ReentrantLock   AutoCloseable=false Closeable=false
```

- 그래서 락은 여전히 `finally` 로 쓴다.

```java
lock.lock();
try { ... } finally { lock.unlock(); }
```

- `lock()` 을 `try` **밖에** 두는 것이 관례다 — `lock()` 자체가 실패하면 `unlock()` 을 부르면 안 되기 때문이다.

### 11. 다른 주제와 잇기

**이 문법이 해결하는 `finally` 의 함정**

- [`../25-exceptions/`](../25-exceptions/) 의 셋째 함정 — **`finally` 가 예외를 던지면 진행 중이던 예외가 버려진다**(JLS §14.20.2).
- 25번에서 측정한 결과가 이것이다.

```text
replaceException() 에서 밖으로 나온 것 = java.lang.RuntimeException: finally 가 던진 예외
  원래 예외는? getCause = null / suppressed 개수 = 0
```

- 26번은 같은 상황에서 suppressed 를 만들어 **둘 다 남긴다.**
- 즉 이 문법은 **짧게 쓰려고 있는 게 아니라 정보를 잃지 않으려고 있다.**

**암묵적 `final` 과 effectively final**

- 자원 변수는 **암묵적 `final`**, 9+ 의 외부 변수 형태는 **effectively final** 을 요구한다.
- 같은 제약이 다중 `catch` 변수에도 있다([`../25-exceptions/`](../25-exceptions/) 2번).
- 개념의 정본은 [`../03-variables-and-assignment/`](../03-variables-and-assignment/) 다 — 거기서 "캡처는 값 복사다"를 본 것과 같은 계열의 이유(**대상이 흔들리면 안 된다**)다.

**`ExecutorService` 는 어느 JDK 부터인가, 어떻게 확인했나**

**출력** (`Ex.java (26-h)` — 리플렉션으로 인터페이스 구현 여부를 찍었다)

```text
=== JDK 17.0.13 ===
java.util.concurrent.ExecutorService       AutoCloseable=false Closeable=false
=== JDK 21.0.5 ===
java.util.concurrent.ExecutorService       AutoCloseable=true  Closeable=false
=== JDK 25.0.1 ===
java.util.concurrent.ExecutorService       AutoCloseable=true  Closeable=false
```

- **21 부터**다. 17 에서는 `false`, 21·25 에서 `true` 다.
- 같은 소스를 세 JDK 에서 돌려 **차이가 난 유일한 항목**이었다.
- 그래서 21부터 이렇게 쓸 수 있다.

```java
try (var ex = Executors.newFixedThreadPool(4)) {
    ex.submit(task);
}   // close() 가 shutdown 후 종료를 기다린다
```

- **닫으면 종료를 기다린다**는 점이 중요하다 — 그 의미와 주의점은 목록의 **54번 주제**가 정본이다.

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java (26-a)` | 역순 close, suppressed 네 경우, 자원 셋 전부 실패, 생성 중 실패, 손으로 쓴 `try-finally` 의 손실 | 17 · 21 · 25 (동일) |
| `Ex.java (26-b)` | `Suppressed:` 스택트레이스(잡은 것·uncaught), `Suppressed`+`Caused by` 동시 출력, 손으로 부른 `addSuppressed` | 17 · 21 · 25 (동일) |
| `Ex.java (26-c)` | `AutoCloseable`/`Closeable` 의 `throws`, 9+ 형태와 7~8 형태, 자원이 `null` 일 때 | 17 · 21 · 25 (동일) |
| `Ex.java (26-d1)` `javac` | 자원 변수 재대입 -> `auto-closeable resource r may not be assigned` | 21 |
| `Ex.java (26-d2)` `javac` | `AutoCloseable` 아닌 타입 -> `not applicable to variable type` | 21 |
| `Ex.java (26-d3)` `javac` | effectively final 아닌 변수 -> `neither final nor effectively final` | 21 |
| `Ex.java (26-d4)` `javac` | `AutoCloseable` 의 checked 예외 -> `exception thrown from implicit call to close()` | 21 |
| `Ex.java (26-e)` `javac --release` | `try (변수)` 형태가 `--release 8` 에서 거부, 9 에서 통과 | 21 의 javac |
| `Ex.java (26-f)` `javap -c -p` | `Throwable.addSuppressed` 삽입, 예외 테이블 2행, `close()` 2회 복사 | 21 |
| `Ex.java (26-g)` `javap -c -p` + 실행 | 자원이 `null` 일 때 `ifnull` 검사 삽입, NPE 없이 통과 | 21 |
| `Ex.java (26-h)` | 표준 타입 11종의 `AutoCloseable`/`Closeable` 여부 | 17 · 21 · 25 (**`ExecutorService` 만 다름**) |
| `src.zip` 열람 | `AutoCloseable`·`Closeable`·`Throwable.addSuppressed` 의 javadoc 과 `@since` | 21 |

**구현 의존 항목** — 펼쳐진 바이트코드의 오프셋·명령 순서, `Suppressed:` 출력의 들여쓰기와 `... N more`, 컴파일 에러 문구 전문은 **구현 세부**다.\
버전이 올랐을 때 다시 돌려 볼 것은 **`(26-f)`·`(26-g)` 의 `javap` 와 `(26-h)` 의 인터페이스 표**다 — 표준 타입이 `AutoCloseable` 로 바뀌는 일이 실제로 있었다(`ExecutorService`).\
반면 역순 close·suppressed 규칙·`null` 자원 처리·자원 변수의 `final` 성은 JLS 가 보장한다.
