# java/syntax/26 — `try`-with-resources: `AutoCloseable`·suppressed·`finally` 순서 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §14.20.3 try-with-resources](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html) · [`java.lang.AutoCloseable` API 문서](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/AutoCloseable.html) · [`java.lang.Throwable#addSuppressed`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Throwable.html) · JDK 21.0.5 표준 라이브러리 소스 `java.base/java/lang/AutoCloseable.java`·`Throwable.java`·`java/io/Closeable.java`(`lib/src.zip`).
> **실행 검증** — 이 문서의 모든 출력·스택트레이스·컴파일 에러·바이트코드는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> `Ex.java (26-a)` `(26-b)` `(26-c)` 는 **17.0.13 · 21.0.5 · 25.0.1** 에서 돌렸고 **출력이 한 글자도 다르지 않았다.**\
> **"세 곳에서 같았다"는 관찰이지 보장이 아니다** — 보장은 JLS·javadoc 인용으로만 적었다.
> **버전** — `try`-with-resources 와 `AutoCloseable`·`addSuppressed`/`getSuppressed` 는 **Java 7**(`src.zip` 의 `@since 1.7` 을 직접 읽었다).\
> **effectively final 변수를 자원 자리에 직접 쓰는 형태는 Java 9** 부터다 — `javac --release 8` 로 거부되는 것을 확인했다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 JLS·javadoc 으로, 출력은 실행으로 접지했다.
> **선행** — [`../25-exceptions/`](../25-exceptions/) 의 `finally` 함정(특히 「예외가 예외를 덮는다」)을 먼저 본다. 이 주제는 그 함정의 해결책이다.

## 한눈에 — 쉽게 말하면

**`try`-with-resources 는 "나갈 때 불을 끄고 문을 잠그는 것을 계약으로 만든 방"이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 방 | `try` 블록 |
| 방에 들여놓은 장비 | 자원(`AutoCloseable` 구현체) |
| 장비마다 붙은 "끄는 법" 설명서 | `close()` 메서드 |
| 나갈 때 자동으로 실행되는 소등 절차 | 컴파일러가 만들어 넣은 `finally` |
| **나중에 들여놓은 것부터 끈다** | 역순 close |
| 방 안에서 난 사고 | 본문 예외 |
| 끄다가 난 사고 | `close()` 가 던진 예외 |
| 본 사고 보고서에 **첨부**되는 부수 사고 | suppressed 예외 |

- 방에 장비를 셋 들여놓으면 **나갈 때 셋 다 꺼 준다.** 내가 안 써도 된다.
- 끄는 순서는 **들여놓은 역순**이다. 나중 장비가 앞 장비에 기대고 있을 수 있기 때문이다.\
  (`Connection` -> `Statement` -> `ResultSet` 순으로 열었으면 반대로 닫아야 한다.)
- **방 안에서 사고가 났는데 끄다가 또 사고가 나면**, 자바는 **방 안 사고를 본 보고서로 올리고 소등 사고를 첨부**한다.\
  손으로 `finally` 를 쓰면 **나중 사고가 본 사고를 덮어써서 원래 사고가 사라진다.**

```text
손으로 쓴 try-finally                        try-with-resources
+-----------------------------------+      +-----------------------------------+
| 본문 예외: "본문 예외"             |      | 본문 예외: "본문 예외"             |
| close 예외: "close 실패: A"        |      | close 예외: "close 실패: A"        |
|                                   |      |                                   |
| 밖으로 나온 것                     |      | 밖으로 나온 것                     |
|   = close 실패: A                 |      |   = 본문 예외                      |
| suppressed 개수 = 0               |      | suppressed 개수 = 1               |
|                                   |      |   suppressed: close 실패: A       |
| 본문 예외는 사라졌다               |      | 둘 다 남는다                       |
+-----------------------------------+      +-----------------------------------+
```

두 칸 모두 **실제 실행 결과**다(`Ex.java (26-a)` 의 3번과 6번).

**똑같은 구조로** 자바가 동작한다: 방 = `try` 블록, 소등 절차 = 컴파일러가 만든 `finally`, 첨부 = `Throwable.addSuppressed`.

실무에서 이게 터지는 자리는 **DB 커넥션을 손으로 닫는 옛 코드**다.\
쿼리가 실패한 진짜 이유(제약 위반·타임아웃)가 `close()` 의 "이미 닫힌 커넥션" 예외에 덮여 사라진다.

> **자원(resource)** — 다 쓰면 명시적으로 놓아 줘야 하는 것. 파일 핸들·소켓·DB 커넥션·락.\
> 예: `InputStream` 을 안 닫으면 프로세스의 파일 디스크립터가 계속 쌓인다.

> **suppressed 예외(억제된 예외)** — 주 예외를 밖으로 내보내면서 함께 매달아 두는 부수 예외.\
> 예: 본문이 실패하고 `close()` 도 실패하면 본문 예외가 나가고 `close()` 예외가 suppressed 로 붙는다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 이 문법이 **무엇으로 펼쳐지는가** — 컴파일러가 소스에 없는 어떤 코드를 만들어 넣는가.
2. **suppressed 가 생기는 조건**은 정확히 무엇이고, 그것이 없으면 무엇을 잃는가.
3. `AutoCloseable` 과 `Closeable` 은 **계약이 어떻게 다른가** — 그리고 그 차이가 코드에서 무엇을 바꾸는가.

## 동작 방식

### (1) 닫는 순서 — 연 역순

**언제 쓰나** — 자원을 둘 이상 열 때. 자원이 서로에 기대고 있으면 순서가 정확성을 좌우한다.

```java
try (Res a = new Res("A", false);
     Res b = new Res("B", false);
     Res c = new Res("C", false)) {
    a.use(); b.use(); c.use();
}
```

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

```text
열기                                        닫기
  A  ─┐                                     ┌─ A   (마지막)
  B  ─┼─ 들여놓은 순서                        ├─ B
  C  ─┘                                     └─ C   (먼저)

  스택처럼: 마지막에 넣은 것을 먼저 뺀다
```

그림 해설 (한 단계씩):

- 선언 순서대로 열고 **반대로 닫는다**(JLS §14.20.3).
- 이유는 **의존 방향**이다. `c` 가 `b` 를 쓰고 `b` 가 `a` 를 쓴다면, `a` 를 먼저 닫으면 `b.close()` 가 터진다.
- 실제 예: `Connection` -> `PreparedStatement` -> `ResultSet` 순으로 열었으면 역순으로 닫아야 한다.
- 이것이 **손으로 쓰면 틀리기 쉬운 자리**다. 중첩 `try-finally` 를 순서 맞춰 쓰면 들여쓰기가 세 겹이 된다.

비용 — 자원 수만큼 `close()` 호출 한 번씩.

### (2) 무엇으로 펼쳐지나 — `javap` 가 보여 준다

**언제 쓰나** — "컴파일러가 뭘 해 주는 거지?"를 판단할 때. 이 문법의 값어치가 전부 여기 있다.

```java
static void twr() {
    try (R r = new R()) {
        System.out.println("본문");
    }
}
```

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
      17: invokevirtual #24                 // Method Ex$R.close:()V        <- 정상 경로의 close
      20: goto          39
      23: astore_1                                                          <- 본문 예외를 잡았다
      24: aload_0
      25: invokevirtual #24                 // Method Ex$R.close:()V        <- 예외 경로의 close
      28: goto          37
      31: astore_2                                                          <- close 도 던졌다
      32: aload_1
      33: aload_2
      34: invokevirtual #29                 // Method java/lang/Throwable.addSuppressed:(Ljava/lang/Throwable;)V
      37: aload_1
      38: athrow                                                            <- 본문 예외를 다시 던진다
      39: return
    Exception table:
       from    to  target type
           8    16    23   Class java/lang/Throwable
          24    28    31   Class java/lang/Throwable
```

```text
소스 다섯 줄                               클래스 파일이 하는 일

try (R r = new R()) {                      1. r 을 만든다
    본문                                    2. 본문을 돈다
}                                          3-a. 정상이면 close()         (오프셋 17)
                                           3-b. 예외면 예외를 저장하고     (오프셋 23)
                                                close()                (오프셋 25)
                                                close 도 던지면
                                                addSuppressed(close예외)(오프셋 34)
                                                저장한 본문 예외를 athrow (오프셋 38)
```

그림 해설 (한 단계씩):

- **소스에 없는 `Throwable.addSuppressed` 호출이 클래스 파일에 들어 있다.** 이것이 이 문법의 핵심이다.
- 예외 테이블이 **두 행**이다. 첫 행은 본문을, 둘째 행은 **예외 경로의 `close()` 자체**를 감싼다.
- `close()` 코드가 **정상 경로(17)와 예외 경로(25)에 두 번** 나온다 — `finally` 의 코드 복사와 같은 성질이다([`../25-exceptions/`](../25-exceptions/) 5번).
- 즉 이 문법은 **"`finally` + suppressed 처리"로 펼쳐진다.** 새로운 런타임 기능이 아니라 컴파일러가 써 주는 코드다.

자원이 `null` 일 수 있으면 **널 검사까지 넣어 준다**(`Ex.java (26-g)`).

```text
      12: aload_0
      13: ifnull        43            <- null 이면 close 를 건너뛴다
      16: aload_0
      17: invokevirtual #27           // Method Ex$R.close:()V
      ...
      24: aload_0
      25: ifnull        41            <- 예외 경로에도 같은 검사
```

- 실행으로도 확인했다 — 자원이 `null` 이면 **NPE 없이 그냥 지나간다.**

```text
본문 (자원이 null)
NPE 없이 지나갔다
```

비용 — 코드 크기가 늘어난다(`close` 가 경로마다 복사). 실행 비용은 정상 경로에서 `close()` 한 번.

### (3) suppressed 가 생기는 조건 — 둘 다 던져야 한다

**언제 쓰나** — 로그에 `Suppressed:` 가 보일 때, 또는 안 보일 때 왜인지 판단할 때.

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

```text
경우 나누기 — 네 가지뿐이다

  본문    close    밖으로 나오는 것          suppressed
  ----    -----    -----------------        -----------
  정상    정상     없음                      —
  정상    실패     close 예외                0개        <- suppressed 가 안 생긴다
  실패    정상     본문 예외                 0개        <- suppressed 가 안 생긴다
  실패    실패     본문 예외                 close 예외  <- 여기서만 생긴다
```

그림 해설 (한 단계씩):

- **suppressed 는 "둘 다 던졌을 때"만 생긴다.** 하나만 던지면 그것이 그냥 나간다.
- **본문 예외가 항상 이긴다** — 주 예외로 나가고 `close` 예외가 첨부된다.\
  근거는 `Throwable.addSuppressed` 의 javadoc 이다(원문 인용).

> In the `try`-with-resources statement, when there are two such exceptions, the exception originating from the `try` block is propagated and the exception from the `finally` block is added to the list of exceptions suppressed by the exception from the `try` block.

- 이유는 **본문 예외가 "왜 실패했나"를 담고 있기** 때문이다. `close` 실패는 대개 그 결과다.

자원이 여럿이면 suppressed 가 쌓인다.

```text
--- 4. 자원 셋이 전부 close 에서 실패하면 suppressed 가 둘
  닫기: C
  닫기: B
  닫기: A
  밖으로 나온 것 = java.lang.IllegalStateException: close 실패: C
  suppressed 개수 = 2
  suppressed: java.lang.IllegalStateException: close 실패: B
  suppressed: java.lang.IllegalStateException: close 실패: A
```

- 본문이 정상이므로 **처음 던진 `close`(= 마지막에 연 C)가 주 예외**가 된다.
- 그다음 B, A 의 예외가 **닫는 순서대로 첨부**된다.
- 즉 **자원 하나가 close 에 실패해도 나머지는 계속 닫는다.** 누수가 안 생긴다.

자원 생성 중 실패하면 **이미 연 것만** 닫는다.

```text
--- 5. 자원 생성 도중 실패하면 이미 연 것만 닫는다
  열기: A
  닫기: A
  밖으로 나온 것 = java.lang.IllegalArgumentException: 자원 B 생성 실패
```

- `A` 는 열렸으므로 닫고, `B` 는 안 만들어졌으므로 닫을 것이 없고, `C` 는 시작도 안 했다.

비용 — suppressed 하나당 리스트 원소 하나.

### (4) 손으로 쓰면 무엇을 잃나

**언제 쓰나** — 옛 코드를 볼 때, 또는 "그냥 `finally` 쓰면 되는 거 아냐"를 판단할 때.

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

```text
손으로 쓴 try-finally                        try-with-resources
+-----------------------------------+      +-----------------------------------+
| Res a = new Res("A", true);       |      | try (Res a = new Res("A", true)) {|
| try {                             |      |     a.use();                      |
|     a.use();                      |      |     throw new RE("본문 예외");     |
|     throw new RE("본문 예외");     |      | }                                 |
| } finally {                       |      |                                   |
|     a.close();                    |      |                                   |
| }                                 |      |                                   |
|                                   |      |                                   |
| 밖: close 실패: A                  |      | 밖: 본문 예외                      |
| suppressed: 0                     |      | suppressed: 1 (close 실패: A)     |
| "본문 예외"는 흔적도 없다           |      | 둘 다 남는다                       |
+-----------------------------------+      +-----------------------------------+
```

그림 해설 (한 단계씩):

- 왼쪽은 [`../25-exceptions/`](../25-exceptions/) 의 `finally` 함정 셋째와 **완전히 같은 현상**이다.\
  `finally` 가 예외를 던지면 진행 중이던 예외가 버려진다(JLS §14.20.2).
- 잃는 것은 **"왜 실패했나"** 다. 남는 것은 "닫다가도 실패했다"뿐이다.
- 이 손실이 특히 나쁜 이유: **`close()` 실패는 본문 실패의 결과인 경우가 많다.**\
  트랜잭션이 깨져서 커넥션이 못 닫히는 것인데, 로그에는 "커넥션을 못 닫았다"만 남는다.
- 그래서 **자원을 닫는 코드는 `try`-with-resources 로만 쓴다** — 스타일 문제가 아니라 정보 손실 문제다.

비용 — 없다. 오히려 코드가 짧아진다.

### (5) `AutoCloseable` 대 `Closeable` — 계약이 둘 다르다

**언제 쓰나** — 내가 만드는 클래스를 어느 쪽으로 구현할지 고를 때.

**출력** (`Ex.java (26-c)`, 17·21·25 동일)

```text
AutoCloseable.close 의 throws = [class java.lang.Exception]
Closeable.close 의 throws     = [class java.io.IOException]
Closeable 은 AutoCloseable 의 하위 = true
```

```text
      AutoCloseable  (java.lang, 7+)
        close() throws Exception
        멱등성 요구 없음
              |
        상속
              |
      Closeable      (java.io, 5+)
        close() throws IOException
        멱등성 요구 있음
```

두 계약의 차이는 **javadoc 에 명시돼 있다.** 원문 인용이다.

`AutoCloseable.close` javadoc:

> Note that unlike the `close` method of `Closeable`, this `close` method is **not** required to be idempotent. In other words, calling this `close` method more than once may have some visible side effect, unlike `Closeable.close` which is required to have no effect if called more than once.

`Closeable.close` javadoc:

> Closes this stream and releases any system resources associated with it. **If the stream is already closed then invoking this method has no effect.**

그림 해설 (한 단계씩):

- **`Closeable` 은 여러 번 불러도 안전해야 한다**(멱등). `AutoCloseable` 은 그 요구가 없다.
- **`throws` 가 다르다.** `Closeable` 은 `IOException` 만, `AutoCloseable` 은 `Exception` 전체다.
- 그래서 `AutoCloseable` 구현을 `try`-with-resources 에 쓰면 **checked 예외 처리가 강제된다.**

```text
Ex.java:4: error: unreported exception Exception; must be caught or declared to be thrown
        try (AC a = new AC()) { }
                ^
  exception thrown from implicit call to close() on resource variable 'a'
1 error
```

- 에러 문구가 **`implicit call to close()`** 라고 명시한다 — 내가 안 쓴 호출에서 난 것임을 알려 준다.
- 실무 해법은 **구현에서 `throws` 를 좁히거나 없애는 것**이다.

```java
static class Quiet implements AutoCloseable {
    @Override public void close() { ... }     // throws 없음 -> 호출부가 아무것도 안 해도 된다
}
```

- 실행으로 확인했다 — `throws` 가 없는 구현은 `try`-with-resources 에서 아무 처리도 요구하지 않는다.
- `AutoCloseable.close` 의 javadoc 도 그렇게 권한다(원문 인용).

> While this interface method is declared to throw `Exception`, implementers are *strongly* encouraged to declare concrete implementations of the `close` method to throw more specific exceptions, or to throw no exception at all if the close operation cannot fail.

비용 — 없다. 설계 선택이다.

> **멱등(idempotent)** — 여러 번 해도 결과가 한 번 한 것과 같은 성질.\
> 예: `Closeable.close()` 를 두 번 불러도 두 번째는 아무 일도 안 일어나야 한다.

### (6) Java 9 — 이미 있는 변수를 자원 자리에 쓸 수 있게 됐다

**언제 쓰나** — 자원을 밖에서 받아 오거나 조건부로 만들 때.

**출력** (`Ex.java (26-c)`)

```text
본문 (9+ 형태)
Quiet.close (throws 없음)
본문 (7~8 형태)
Quiet.close (throws 없음)
```

```text
Java 7~8 — 새 변수를 만들어야 했다           Java 9+ — 그대로 쓴다
+-----------------------------------+      +-----------------------------------+
| Quiet outside2 = new Quiet();     |      | Quiet outside = new Quiet();      |
| try (Quiet ref = outside2) {      |      | try (outside) {                   |
|     본문                           |      |     본문                           |
| }                                 |      | }                                 |
|                                   |      |                                   |
| ref 라는 의미 없는 변수가 하나 생긴다|      | 변수가 하나뿐이다                   |
+-----------------------------------+      +-----------------------------------+
```

**`javac --release` 로 확인한 경계** (`Ex.java (26-e)`, JDK 21.0.5 의 javac)

```text
=== --release 8 ===
Ex.java:5: error: variables in try-with-resources are not supported in -source 8
        try (outside) { System.out.println("본문"); }
                    ^
  (use -source 9 or higher to enable variables in try-with-resources)
1 error
=== --release 9 ===
OK
```

그림 해설 (한 단계씩):

- 에러 메시지가 **어느 버전부터인지를 직접 알려 준다** — `use -source 9 or higher`.
- 조건이 하나 있다: **그 변수가 `final` 이거나 effectively final 이어야 한다.**

```text
Ex.java:6: error: variable r used as a try-with-resources resource neither final nor effectively final
        try (r) { }
             ^
1 error
```

- 이유는 **닫을 대상이 흔들리면 안 되기** 때문이다. 본문에서 변수가 다른 객체를 가리키게 되면 무엇을 닫아야 할지 정해지지 않는다.
- 같은 이유로 **`try` 안에서 선언한 자원 변수도 암묵적 `final`** 이다.

```text
Ex.java:5: error: auto-closeable resource r may not be assigned
            r = new R();
            ^
1 error
```

- effectively final 개념 자체는 [`../03-variables-and-assignment/`](../03-variables-and-assignment/) 가 정본이다.

비용 — 없다. 문법 편의다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### 형태 넷

```java
try (Res r = open()) { }                          // 하나
try (Res a = open(); Res b = open()) { }          // 여럿 — 세미콜론으로 구분
try (Res a = open(); Res b = open();) { }         // 마지막 세미콜론은 있어도 된다
try (existingVar) { }                             // 9+ — effectively final 변수
```

- `catch`·`finally` 를 붙일 수 있다. **안 붙여도 된다** — 일반 `try` 와 다른 점이다.
- 붙이면 순서는 **자원 close -> `catch` -> `finally`** 다.\
  `catch` 블록이 돌 때는 자원이 **이미 닫혀 있다.**

### 자원이 되기 위한 조건

```java
class Ok   implements AutoCloseable { public void close() { } }        // 된다
class Ok2  implements java.io.Closeable { public void close() { } }    // 된다 (하위 인터페이스)
class NotOk                            { public void close() { } }     // 안 된다
```

**컴파일 에러** (`Ex.java (26-d2)`)

```text
Ex.java:4: error: incompatible types: try-with-resources not applicable to variable type
        try (NotRes r = new NotRes()) { }
                    ^
    (NotRes cannot be converted to AutoCloseable)
1 error
```

- **`close()` 메서드가 있는 것만으로는 안 된다.** `AutoCloseable` 을 구현해야 한다.
- 자바는 구조적 타이핑을 안 한다 — 이름이 같아도 인터페이스를 선언해야 한다.

### 표준 라이브러리에서 자원인 것

리플렉션으로 직접 확인한 결과다(`Ex.java (26-h)`, 17·21·25 에서 돌렸다).

```text
java.io.InputStream                        AutoCloseable=true  Closeable=true
java.io.Reader                             AutoCloseable=true  Closeable=true
java.net.Socket                            AutoCloseable=true  Closeable=true
java.util.Scanner                          AutoCloseable=true  Closeable=true
java.sql.Connection                        AutoCloseable=true  Closeable=false
java.sql.Statement                         AutoCloseable=true  Closeable=false
java.sql.ResultSet                         AutoCloseable=true  Closeable=false
java.util.stream.Stream                    AutoCloseable=true  Closeable=false
java.util.concurrent.ExecutorService       AutoCloseable=true  Closeable=false
java.util.concurrent.locks.ReentrantLock   AutoCloseable=false Closeable=false
java.util.zip.ZipFile                      AutoCloseable=true  Closeable=true
```

| 타입 | 비고 |
|---|---|
| `InputStream`·`Reader` 계열 | 대부분의 I/O. `Closeable` 이라 멱등 계약이 붙는다 |
| `Socket`·`ZipFile` | 같음 |
| `Connection`·`Statement`·`ResultSet` | JDBC. `Closeable` 이 **아니다**. 역순 close 가 중요하다 |
| `Stream`·`IntStream` 등 | **대부분 닫을 필요가 없다** — `Files.lines` 같은 I/O 기반만 닫는다 |
| `Scanner` | `System.in` 을 감싼 것은 닫으면 안 된다(표준 입력이 닫힌다) |
| `ExecutorService` | **17 에서는 `AutoCloseable` 이 아니었고 21·25 에서는 맞다** — 위 출력이 그 증거다 |
| `ReentrantLock` | **자원이 아니다.** `lock()`/`unlock()` 을 손으로 써야 한다 |

- `Stream` 이 `AutoCloseable` 인데도 대개 안 닫는 이유는 `AutoCloseable` 의 javadoc 이 직접 설명한다(원문 인용).

> However, when using facilities such as `java.util.stream.Stream` that support both I/O-based and non-I/O-based forms, `try`-with-resources blocks are in general unnecessary when using non-I/O-based forms.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 다섯 다 **컴파일이 통과하거나, 에러가 원인을 바로 안 알려 준다.**

### 1. 아직 `finally` 로 자원을 닫는다

(4)절의 왼쪽 칸이다. **본문 예외가 사라진다.**\
옛 코드에서 이 패턴을 보면 **원인 손실이 이미 일어나고 있다**고 봐야 한다.

### 2. suppressed 를 로그에서 안 본다

`e.getMessage()` 만 찍는 로거는 **suppressed 를 통째로 버린다.**

```text
잘못된 로깅                                  올바른 로깅
+-----------------------------------+      +-----------------------------------+
| log.error(e.getMessage());        |      | log.error("작업 실패", e);         |
|                                   |      |                                   |
| 본문 예외                          |      | java.lang.RuntimeException: 본문..|
|                                   |      |   at Ex.work(Ex.java:10)          |
| 끝.                               |      |   Suppressed: java.lang.IllegalS..|
| close 실패는 어디에도 없다          |      |     at Ex$Res.close(Ex.java:5)    |
+-----------------------------------+      +-----------------------------------+
```

- 오른쪽은 실제 `printStackTrace()` 출력이다(`Ex.java (26-b)`, 아래 전문).
- **예외 객체를 통째로 넘겨야** suppressed 가 찍힌다.

### 3. `close()` 를 멱등하지 않게 만든다

- `AutoCloseable` 은 멱등을 요구하지 않지만, **멱등하게 만들어 두는 것이 안전하다.**
- javadoc 도 그렇게 권한다 — "implementers of this interface are strongly encouraged to make their `close` methods idempotent."
- 멱등하지 않으면 `try`-with-resources 와 다른 정리 경로가 겹칠 때 두 번 닫히며 이상한 일이 난다.

### 4. `close()` 안에서 자원을 안 놓고 예외부터 던진다

`AutoCloseable.close` javadoc 이 직접 경고한다(원문 인용).

> Cases where the close operation may fail require careful attention by implementers. It is strongly advised to relinquish the underlying resources and to internally *mark* the resource as closed, prior to throwing the exception.

- **먼저 놓고 나서 던져라.** 던지고 나면 아무도 다시 안 부른다 — 자원이 샌다.

같은 javadoc 이 `InterruptedException` 을 `close()` 에서 던지지 말라고도 한다.

> *Implementers of this interface are also strongly advised to not have the `close` method throw `InterruptedException`.*\
> This exception interacts with a thread's interrupted status, and runtime misbehavior is likely to occur if an `InterruptedException` is suppressed.

- **suppressed 로 밀려나면 인터럽트 신호가 조용히 사라지기** 때문이다.

### 5. 자원 변수를 재대입하려 한다

```text
Ex.java:5: error: auto-closeable resource r may not be assigned
            r = new R();
            ^
1 error
```

- **컴파일러가 막아 준다.** 다행인 경우다.
- 9+ 형태에서 밖의 변수를 쓸 때도 effectively final 이어야 한다.

```text
Ex.java:6: error: variable r used as a try-with-resources resource neither final nor effectively final
        try (r) { }
             ^
1 error
```

## 구현 세부사항 대 언어 보장

이 절은 **"어디까지 믿어도 되나"**를 가른다.

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| 자원을 **선언 역순**으로 닫는다 | **JLS (언어 보장)** | JLS §14.20.3 |
| 본문 예외가 주 예외, `close` 예외가 suppressed | **JLS + javadoc** | JLS §14.20.3 · `Throwable.addSuppressed` javadoc |
| 자원이 `null` 이면 `close()` 를 안 부른다 | **JLS (언어 보장)** | JLS §14.20.3 |
| 생성 중 실패하면 이미 연 것만 닫는다 | **JLS (언어 보장)** | JLS §14.20.3 |
| 자원 변수가 암묵적 `final` | **JLS (언어 보장)** | JLS §14.20.3 |
| 9+ 의 effectively final 변수 형태 | **JLS (언어 보장, 9+)** | `--release 8` 거부로 확인 |
| `Closeable.close` 가 멱등이어야 함 | **javadoc (API 계약)** | `Closeable.close` javadoc |
| `AutoCloseable.close` 는 멱등 요구 없음 | **javadoc (API 계약)** | `AutoCloseable.close` javadoc |
| 펼쳐진 바이트코드의 **모양**(오프셋·명령 순서) | **구현 세부** | `javap` 관찰. 명세는 의미만 규정한다 |
| `Suppressed:` 출력의 들여쓰기·`... N more` | **구현 세부** | `Throwable.printStackTrace` 의 구현 |
| 컴파일 에러 문구 전문 | **구현 세부** | javac 의 메시지(17·21·25 에서 동일하게 관찰) |

**경계 한 줄** — **"어떤 예외가 남고 어떤 것이 suppressed 로 붙나"는 명세**이고, **"그것이 로그에 어떻게 찍히나"는 구현**이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 판단 |
|---|---|
| `AutoCloseable` 인 것을 만들어 쓴다 | **무조건 `try`-with-resources.** 예외 없다 |
| 자원을 메서드 밖에서 받아 왔다 | **닫지 않는다.** 준 쪽이 닫는다 — 이 문법을 쓰면 안 되는 자리다 |
| `System.in` 을 감싼 `Scanner` | 닫지 않는다. 닫으면 표준 입력이 닫힌다 |
| 컬렉션 기반 `Stream` | 닫을 필요 없다(javadoc 이 그렇게 적는다) |
| `Files.lines`·`Files.walk` 가 준 `Stream` | **닫는다.** 파일 핸들을 쥐고 있다 |
| 락(`ReentrantLock`) | 이 문법을 못 쓴다 — `try { lock.lock(); ... } finally { lock.unlock(); }` |
| 자원을 여럿 여는데 순서가 중요하다 | **한 `try` 에 세미콜론으로 나열한다.** 역순 close 를 언어가 보장한다 |

판단 규칙 두 줄.

- **"내가 연 것만 내가 닫는다."** 받아 온 자원을 닫으면 준 쪽이 깨진다.
- **자원 닫기에 `finally` 를 쓰지 않는다** — 원인 예외가 사라진다.

## 핵심 문장

- `try`-with-resources 는 **"`finally` + `Throwable.addSuppressed`"로 펼쳐진다.** `javap` 에 그 호출이 그대로 찍힌다.
- 자원은 **선언 역순으로 닫히고**, 하나가 실패해도 **나머지는 계속 닫힌다.**
- **suppressed 는 본문과 `close` 가 둘 다 던졌을 때만 생긴다.** 그때 **본문 예외가 주 예외**로 나간다.
- 손으로 쓴 `try-finally` 는 그 상황에서 **본문 예외를 잃는다** — 잃는 것이 바로 "왜 실패했나"다.
- `Closeable` 은 **멱등을 요구**하고 `IOException` 만 던진다. `AutoCloseable` 은 둘 다 아니다 — 구현에서 `throws` 를 좁히는 것이 권장된다.
- **9부터 effectively final 인 바깥 변수를 자원 자리에 직접 쓸 수 있다.** `--release 8` 은 거부한다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 26번)
- [`../25-exceptions/`](../25-exceptions/) — **그쪽은 예외의 문법 전반(checked 규칙·전파·다중 `catch`·`finally` 의미)까지, 여기는 자원 정리 구문과 suppressed 부터.**\
  "`finally` 가 예외를 덮는다"는 그쪽의 함정이고, "그것을 언어가 어떻게 막아 주나"가 여기다
- [`../03-variables-and-assignment/`](../03-variables-and-assignment/) — 자원 변수의 암묵적 `final` 과 9+ 형태가 요구하는 effectively final 의 정본
- [`../../../../../ops-patterns/19-graceful-shutdown/`](../../../../../ops-patterns/19-graceful-shutdown/) — 프로세스 수준의 자원 정리. **이 문법은 한 블록 안의 정리까지**이고, 종료 시 커넥션 풀·스레드 풀을 어떻게 비우나는 그쪽이다
- [**46번 주제**](../46-terminal-operations/)(최종 연산과 지연 평가) — `Stream` 이 `AutoCloseable` 인데도 대개 안 닫는 이유
- 목록의 **57번 주제**(`Files`·`Path`) — `Files.lines`·`Files.walk` 처럼 **반드시 닫아야 하는 스트림**
- 목록의 **54번 주제**(`java.util.concurrent`) — `ExecutorService` 의 종료. 21부터 `AutoCloseable` 이 됐다
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — GC 는 자원을 안 닫아 준다. 왜 finalizer 가 대안이 못 되는지의 배경

## 용어 풀이

- **자원(resource)** — 다 쓰면 명시적으로 놓아 줘야 하는 것. 파일 핸들·소켓·DB 커넥션 등.
- **`AutoCloseable`** — `close() throws Exception` 하나를 가진 인터페이스(Java 7). `try`-with-resources 의 자격 조건이다.
- **`Closeable`** — `java.io` 의 인터페이스(Java 5). `AutoCloseable` 의 하위이며 `IOException` 만 던지고 **멱등을 요구**한다.
- **suppressed 예외** — 주 예외에 첨부되는 부수 예외. `getSuppressed()` 로 꺼내고 스택트레이스에 `Suppressed:` 로 찍힌다.
- **주 예외** — 밖으로 전파되는 예외. `try`-with-resources 에서는 본문 예외가 우선한다.
- **멱등(idempotent)** — 여러 번 실행해도 한 번 실행한 것과 결과가 같은 성질.
- **암묵적 `final`** — 소스에 `final` 이라고 안 썼는데 언어가 `final` 로 취급하는 것. 자원 변수와 다중 `catch` 변수가 그렇다.
- **effectively final** — 재대입이 없어 `final` 을 붙여도 되는 변수. 9+ 의 자원 변수 형태가 요구하는 조건이다.
- **원인 사슬(cause chain)** — `Caused by:` 로 이어지는 관계. suppressed 와는 **다른 축**이다(하나는 인과, 하나는 병렬 사고).

## 더 들어가면

- **`Suppressed:` 와 `Caused by:` 는 한 트레이스에 같이 나올 수 있다.** 실행으로 확인했다(`Ex.java (26-b)`).

```text
java.lang.RuntimeException: 본문 예외
	at Ex.main(Ex.java:22)
	Suppressed: java.lang.IllegalStateException: close 실패: A
		at Ex$Res.close(Ex.java:5)
		at Ex.main(Ex.java:21)
Caused by: java.lang.IllegalArgumentException: 본문의 원인
	... 1 more
```

  **`Suppressed:` 가 `Caused by:` 보다 먼저 찍힌다** — 주 예외에 바로 붙은 것이 suppressed 이고, 원인은 그 아래 층이기 때문이다.

- **`addSuppressed` 는 손으로도 부를 수 있다.** `try`-with-resources 전용이 아니다.

```text
getSuppressed().length = 2
java.lang.RuntimeException: 주 예외
	at Ex.main(Ex.java:28)
	Suppressed: java.lang.IllegalStateException: 붙인 것 1
		at Ex.main(Ex.java:29)
	Suppressed: java.lang.IllegalStateException: 붙인 것 2
		at Ex.main(Ex.java:30)
```

  여러 작업을 돌리며 실패를 모아 한 번에 던질 때 쓴다(배치 처리·병렬 정리).

- **suppression 을 끌 수 있다.** `Throwable` 의 4인자 생성자에서 `enableSuppression=false` 를 주면 `addSuppressed` 가 아무 일도 안 한다.\
  `addSuppressed` javadoc 이 그렇게 적는다 — "When suppression is disabled, this method does nothing other than to validate its argument."
- **`ExecutorService` 가 21에서 `AutoCloseable` 이 됐다.** 위 리플렉션 출력이 17과 21의 차이를 그대로 보여 준다.\
  그래서 `try (var ex = Executors.newFixedThreadPool(4)) { ... }` 형태를 21부터 쓸 수 있다.\
  닫으면 `shutdown()` 후 **종료를 기다린다** — 그 의미와 주의점은 목록의 **54번 주제**가 정본이다.
