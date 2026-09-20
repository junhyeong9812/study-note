# java/syntax/25 — 예외: checked/unchecked·전파·다중 `catch`·재던지기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §11 Exceptions](https://docs.oracle.com/javase/specs/jls/se21/html/jls-11.html) (§11.1.1 예외의 종류 · §11.2 컴파일 타임 검사 · §14.20 `try` 문) · [`java.lang.Throwable` API 문서](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Throwable.html) · JDK 21.0.5 표준 라이브러리 소스 `java.base/java/lang/Throwable.java`(`lib/src.zip`).
> **실행 검증** — 이 문서의 모든 출력·스택트레이스·컴파일 에러·바이트코드는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> `Ex.java (25-b)` `(25-c)` `(25-d)` `(25-e)` `(25-h)` 는 **17.0.13 · 21.0.5 · 25.0.1** 에서 돌렸고 **출력이 한 글자도 다르지 않았다.**\
> `finally` 경고 문구도 세 JDK 에서 같았다. **"세 곳에서 같았다"는 관찰이지 보장이 아니다** — 보장은 JLS·javadoc 인용으로만 적었다.
> **버전** — `try`/`catch`/`finally`·checked 예외는 **Java 1.0**. 다중 `catch` 와 **정밀 재던지기**는 **Java 7**. `addSuppressed`/`getSuppressed` 도 **7**(`src.zip` 의 `@since 1.7` 을 직접 읽었다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 JLS·javadoc 으로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**예외는 "호출 사슬을 거꾸로 거슬러 올라가는 비상 신호"다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 건물의 층 | 호출 스택의 프레임 하나(메서드 하나) |
| 비상 신호를 쏜다 | `throw` |
| 층마다 있는 "이 신호는 내가 받는다" 팻말 | `catch` 절 |
| 팻말이 없으면 한 층 올라간다 | 전파(propagation) |
| 옥상까지 올라가 아무도 안 받으면 | `Exception in thread "main" ...` 로 프로그램이 죽는다 |
| 층을 떠날 때 반드시 하는 마무리 | `finally` |
| "이 층을 지나려면 신고서를 내라"는 규정 | `throws` 선언 — **checked 예외에만 붙는 규정** |
| 규정이 없는 신호 | unchecked — `RuntimeException`·`Error` |

- 신호를 쏘면 **그 자리에서 실행이 멈추고** 층을 하나씩 거슬러 올라간다.
- 올라가면서 **팻말을 위에서 아래 순서로 본다.** 처음 맞는 팻말이 신호를 받는다.
- **팻말을 달아 놓고 아무 일도 안 하면**(빈 `catch`) 신호가 거기서 사라진다.\
  건물은 멀쩡해 보이는데 **아래층에서 일어난 사고는 아무도 모른다** — 이것이 "예외를 삼킨다"의 뜻이다.

```text
main 층  <- 여기서 잡았다
  ^
  |  전파
level1 층   throws IOException 만 달고 아무것도 안 한다
  ^
  |
level2 층   throws IOException
  ^
  |
level3 층   throw new IOException("맨 아래에서 발생")   <- 신호를 쏜 자리
```

이 그림이 그대로 스택트레이스다(`Ex.java (25-e)` 실행 결과).

```text
java.io.IOException: 맨 아래에서 발생
	at Ex.level3(Ex.java:21)
	at Ex.level2(Ex.java:22)
	at Ex.level1(Ex.java:23)
	at Ex.main(Ex.java:30)
```

**똑같은 구조로** 자바가 동작한다: 층 = 스택 프레임, 팻말 = `catch`, 신고서 = `throws`.

실무에서 이게 터지는 자리는 **`catch (Exception e) { }` 한 줄**이다.\
장애가 나도 로그가 없고, 상위는 정상 응답을 받고, 원인은 며칠 뒤 데이터 불일치로 발견된다.

> **checked 예외(검사 예외)** — 컴파일러가 "잡거나 `throws` 로 선언하라"고 **강제하는** 예외.\
> 예: `IOException`·`SQLException`. 처리하지 않으면 컴파일이 안 된다.

> **unchecked 예외(비검사 예외)** — 그 강제가 없는 예외. `RuntimeException` 과 `Error` 및 그 하위 전부다(JLS §11.1.1).\
> 예: `NullPointerException`·`IllegalArgumentException`. `throws` 에 안 적어도 던질 수 있다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. checked 와 unchecked 는 **컴파일러에게 무엇을 시키는가** — 그 경계선이 정확히 어디인가.
2. 예외가 올라가는 동안 **`catch` 와 `finally` 는 어떤 순서로 개입하고**, 그때 무엇이 사라질 수 있는가.
3. 예외를 **삼키거나 원인을 버리면** 정확히 어떤 정보가 없어지는가.

## 동작 방식

### (1) 계층 — 어디까지가 checked 인가

**언제 쓰나** — 새 예외 클래스를 만들 때, 또는 "이건 왜 `throws` 를 요구하지?"를 판단할 때.

**출력** (`Ex.java (25-b)`, JDK 21.0.5 — 17·25 에서도 동일)

```text
IOException                  부모=Exception                    checked (컴파일러가 강제)
FileNotFoundException        부모=IOException                  checked (컴파일러가 강제)
SQLException                 부모=Exception                    checked (컴파일러가 강제)
RuntimeException             부모=Exception                    unchecked (강제 안 함)
IllegalArgumentException     부모=RuntimeException             unchecked (강제 안 함)
NullPointerException         부모=RuntimeException             unchecked (강제 안 함)
Exception                    부모=Throwable                    checked (컴파일러가 강제)
Error                        부모=Throwable                    unchecked (강제 안 함)
StackOverflowError           부모=VirtualMachineError          unchecked (강제 안 함)
Throwable                    부모=Object                       checked (컴파일러가 강제)
```

```text
                         Object
                           |
                       Throwable          <- checked
                      /          \
                Exception         Error   <- unchecked (와 그 하위 전부)
               /         \
   RuntimeException    IOException 등      <- 왼쪽은 unchecked, 오른쪽은 checked
   (와 그 하위 전부)     SQLException 등
```

그림 해설 (한 단계씩):

- 경계선은 **딱 두 갈래**다: `RuntimeException` 의 하위, `Error` 의 하위. **이 둘만 unchecked** 다(JLS §11.1.1).
- 나머지는 전부 checked 다 — **`Throwable` 자신도 checked** 다.\
  자주 틀리는 자리라 컴파일로 확인했다(`Ex.java (25-a5)`).

```text
Ex.java:2: error: unreported exception Throwable; must be caught or declared to be thrown
    static void f() { throw new Throwable("checked 인가?"); }
                      ^
1 error
```

- `Error` 는 **잡으라고 만든 것이 아니다.** `OutOfMemoryError`·`StackOverflowError` 처럼 **JVM 수준의 사고**다.
- 그래서 `catch (Exception e)` 는 `Error` 를 **못 잡는다.** 실행으로 확인했다.

```text
catch(Exception) 이 잡은 것 = java.lang.NullPointerException
Error 는 따로 잡아야 한다 = java.lang.StackOverflowError
```

비용 — 없다. 분류 규칙이다.

### (2) checked 가 강제하는 것 — 컴파일러가 세 가지를 검사한다

**언제 쓰나** — checked 예외를 던지는 메서드를 부를 때마다.

전/후를 나란히 놓으면 이렇게 된다.

```text
아무것도 안 하면                            잡거나 선언하면
+-----------------------------------+      +-----------------------------------+
| static void risky()               |      | static void risky()               |
|        throws IOException { ... } |      |        throws IOException { ... } |
| void main() {                     |      | void main() throws IOException {  |
|     risky();                      |      |     risky();                      |
| }                                 |      | }                                 |
|                                   |      |                                   |
| error: unreported exception       |      | 컴파일된다                         |
|   IOException; must be caught or  |      | (또는 try/catch 로 감싼다)         |
|   declared to be thrown           |      |                                   |
+-----------------------------------+      +-----------------------------------+
```

**컴파일 에러** (`Ex.java (25-a1)`)

```text
Ex.java:5: error: unreported exception IOException; must be caught or declared to be thrown
        risky();
             ^
1 error
```

컴파일러는 **세 가지를 더** 본다.

```text
(1) 안 날아오는 예외를 잡으면                (Ex.java (25-a2))
    error: exception IOException is never thrown in body of corresponding try statement

(2) 넓은 것을 먼저 잡으면                    (Ex.java (25-a3))
    error: exception FileNotFoundException has already been caught

(3) 오버라이드가 throws 를 넓히면            (Ex.java (25-g))
    error: m() in Child cannot override m() in Parent
      overridden method does not throw Exception
```

그림 해설 (한 단계씩):

- (1)은 **checked 예외에만** 걸린다. `catch (RuntimeException e)` 는 아무것도 안 던지는 본문에서도 합법이다.\
  unchecked 는 어디서든 날아올 수 있다고 보기 때문이다.
- (2)는 **도달 불가능한 `catch`** 를 막는다 — 넓은 팻말이 위에 있으면 아래 좁은 팻말은 영원히 안 걸린다.
- (3)은 **리스코프 치환**을 예외에도 적용한 것이다. 하위 타입은 상위 타입보다 **더 많이 던질 수 없다.**\
  좁히거나 아예 없애는 것은 된다(`Ex.java (25-h)`).

비용 — 전부 컴파일 타임 검사. 런타임 비용 0.

### (3) 다중 `catch` — 위에서 아래로, 처음 맞는 것 하나

**언제 쓰나** — 한 `try` 에서 여러 종류의 실패를 다르게 처리할 때.

**출력** (`Ex.java (25-b)`)

```text
fnf -> catch(FileNotFoundException) FileNotFoundException
io -> catch(IOException) IOException
iae -> catch(IAE|NPE) IllegalArgumentException / 변수 정적 타입 = RuntimeException
npe -> catch(IAE|NPE) NullPointerException / 변수 정적 타입 = RuntimeException
```

```text
throw FileNotFoundException
        |
        v
   catch (FileNotFoundException e)   <- 맞는다. 여기서 멈춘다
   catch (IOException e)             <- 안 본다
   catch (IAE | NPE e)               <- 안 본다

throw IOException
        |
        v
   catch (FileNotFoundException e)   <- 안 맞는다 (IOException 은 FNF 가 아니다)
   catch (IOException e)             <- 맞는다
   catch (IAE | NPE e)               <- 안 본다
```

그림 해설 (한 단계씩):

- **위에서 아래로** 훑고 **처음 맞는 하나만** 실행한다. `switch` 의 fallthrough 같은 것이 없다.
- 그래서 **좁은 것을 위에, 넓은 것을 아래에** 둬야 한다. 반대로 두면 컴파일 에러다((2)의 사례).
- `catch (A | B e)` 형태(Java 7)는 **팻말 하나에 두 이름**을 적은 것이다.\
  이때 `e` 의 **정적 타입은 A 와 B 의 최소 상한**이다 — `IAE | NPE` 면 `RuntimeException` 이다.
- 다중 `catch` 의 변수는 **암묵적으로 `final`** 이다. 재대입하면 컴파일 에러다(`Ex.java (25-a4)`).

```text
Ex.java:7: error: multi-catch parameter e may not be assigned
            e = new RuntimeException("재대입");
            ^
1 error
```

비용 — 런타임 비용은 예외 테이블 조회 한 번. `catch` 절이 많아도 **예외가 안 나면 비용 0**이다.

### (4) `finally` — 어느 길로 나가든 지나는 문

**언제 쓰나** — 자원 해제·락 해제·로그처럼 "무슨 일이 있어도 해야 하는" 마무리.

**출력** (`Ex.java (25-c)`)

```text
order():
  try 본문
  return 식 평가
  finally
  결과 = 7
```

```text
try {                          정상 경로        예외 경로
    본문                        본문 실행        본문에서 throw
    return f();                f() 평가         |
} finally {                    |                |
    마무리                      마무리 실행       마무리 실행
}                              |                |
                               반환값 7 전달     예외를 위층으로
```

그림 해설 (한 단계씩):

- `return f();` 는 **`f()` 를 먼저 평가해 반환값을 확정하고**, 그다음 `finally` 를 돈다.
- 출력 순서가 그것을 보여 준다 — `return 식 평가` 가 `finally` 보다 **먼저** 나왔다.
- 그래서 `finally` 에서 지역 변수를 고쳐도 **이미 확정된 반환값은 안 바뀐다**((5)의 첫 사례).
- 예외 경로에서도 `finally` 는 돈다. 돈 뒤 예외가 계속 올라간다.

비용 — **`finally` 의 코드가 경로마다 복사된다.** `javap` 로 확인했다((6)).

### (5) `finally` 의 세 함정 — 전부 "덮어쓴다"

**언제 쓰나** — `finally` 안에 `return` 이나 `throw` 를 쓰려 할 때. **쓰지 말아야 할 이유를 아는 자리**다.

**출력** (`Ex.java (25-c)`, 17·21·25 동일)

```text
overwrite()          = 2
swallow()            = 3
mutateAfterReturn()  = 1
mutateObject()       = ab
replaceException() 에서 밖으로 나온 것 = java.lang.RuntimeException: finally 가 던진 예외
  원래 예외는? getCause = null / suppressed 개수 = 0
```

```text
함정 1 — return 을 덮어쓴다                 함정 2 — 예외를 삼킨다
+-----------------------------------+     +-----------------------------------+
| try { return 1; }                 |     | try { throw new ISE("사라진다"); }|
| finally { return 2; }             |     | finally { return 3; }             |
|                                   |     |                                   |
| -> 2                              |     | -> 3                             |
| 1 은 어디에도 안 남는다             |     | 예외가 통째로 없어진다             |
+-----------------------------------+     +-----------------------------------+

함정 3 — 예외를 다른 예외로 바꾼다
+---------------------------------------------------+
| try { throw new ISE("원래 예외"); }                 |
| finally { throw new RE("finally 가 던진 예외"); }   |
|                                                   |
| 밖으로 나오는 것 = RE("finally 가 던진 예외")        |
| getCause = null / suppressed 개수 = 0              |
| 원래 예외는 흔적도 없다                              |
+---------------------------------------------------+
```

그림 해설 (한 단계씩):

- `finally` 가 **정상적으로 끝나지 않으면**(`return`·`throw`·`break`) 진행 중이던 결과가 **버려진다.**
- 함정 2는 최악이다 — **예외가 통째로 사라지는데 컴파일도 되고 실행도 조용하다.**
- 함정 3도 원인이 날아간다. `getCause` 도 `getSuppressed` 도 비어 있다.\
  이 손실을 자동으로 막아 주는 것이 `try`-with-resources 의 suppressed 다([`../26-try-with-resources/`](../26-try-with-resources/)).

**컴파일러가 경고는 한다.** 다만 기본으로는 안 나오고 `-Xlint` 가 필요하다.

```text
$ javac -Xlint:all Ex.java
Ex.java:8: warning: [finally] finally clause cannot complete normally
        }
        ^
Ex.java:17: warning: [finally] finally clause cannot complete normally
        }
        ^
Ex.java:46: warning: [finally] finally clause cannot complete normally
        }
        ^
3 warnings
```

- 17·21·25 세 JDK 에서 **문구와 줄 번호가 같았다.**
- `-Xlint:finally` 만 켜도 나온다. **빌드에 `-Xlint:all -Werror` 를 걸면 이 버그가 빌드에서 막힌다.**

값이 아니라 **객체 내용**을 고치는 것은 반영된다.

```text
mutateAfterReturn()  = 1      // 지역 int 를 99 로 고쳐도 반환값은 이미 확정됐다
mutateObject()       = ab     // StringBuilder 에 append 는 반영된다 (같은 객체다)
```

- 이 차이는 값 전달 규칙 그대로다 — [`../03-variables-and-assignment/`](../03-variables-and-assignment/) 가 정본이다.

비용 — 없다. 전부 회피해야 할 패턴이다.

### (6) `finally` 는 바이트코드에서 복사된다

**언제 쓰나** — "`finally` 가 어떻게 모든 경로에서 도는가"를 이해할 때.

**`javap -c -p Ex.class` 출력 그대로** (`Ex.java (25-f)`, JDK 21.0.5)

```text
  static int f(int);
    Code:
       0: iload_0
       1: ifne          17
       4: bipush        10
       6: istore_1
       7: getstatic     #7    // Field java/lang/System.out:Ljava/io/PrintStream;
      10: ldc           #13   // String cleanup
      12: invokevirtual #15   // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      15: iload_1
      16: ireturn
      17: iload_0
      18: iconst_1
      19: if_icmpne     32
      22: new           #21   // class java/lang/IllegalStateException
      25: dup
      26: ldc           #23   // String x
      28: invokespecial #25   // Method java/lang/IllegalStateException."<init>":(Ljava/lang/String;)V
      31: athrow
      32: bipush        20
      34: istore_1
      35: getstatic     #7    // Field java/lang/System.out:Ljava/io/PrintStream;
      38: ldc           #13   // String cleanup
      40: invokevirtual #15   // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      43: iload_1
      44: ireturn
      45: astore_2
      46: getstatic     #7    // Field java/lang/System.out:Ljava/io/PrintStream;
      49: ldc           #13   // String cleanup
      51: invokevirtual #15   // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      54: aload_2
      55: athrow
    Exception table:
       from    to  target type
           0     7    45   any
          17    35    45   any
```

```text
소스는 한 번 썼다                          클래스 파일에는 세 벌 들어 있다

  finally {                                 오프셋 7  — return 10 경로용
      System.out.println("cleanup");        오프셋 35 — return 20 경로용
  }                                         오프셋 46 — 예외 경로용 (예외 테이블의 target)
```

그림 해설 (한 단계씩):

- `println("cleanup")` 세 명령 묶음이 **오프셋 7 · 35 · 46 에 세 번** 나온다.
- 나가는 길이 셋이라(두 `return` + 예외) **컴파일러가 각 길에 마무리 코드를 복사해 박았다.**
- 예외 경로는 예외 테이블의 `any` 핸들러다 — `astore_2` 로 예외를 잠시 저장하고, 마무리를 돌고, `athrow` 로 다시 던진다.
- 그래서 **`finally` 가 길면 메서드 크기가 경로 수만큼 부풀어 오른다.**\
  JIT 인라인 한계에 걸릴 수 있는 것도 이 때문이다(수치는 측정하지 않았다).

비용 — **코드 크기 × 나가는 경로 수.** 실행 비용은 경로당 한 벌이므로 늘지 않는다.

### (7) 원인 사슬 — `Caused by:` 가 생기는 조건

**언제 쓰나** — 하위 계층의 예외를 상위 계층의 예외로 바꿔 던질 때(예외 변환).

**출력** (`Ex.java (25-d)`, 17·21·25 동일)

```text
--- 1. 원인 사슬을 이었을 때 (e 를 두 번째 인자로)
Ex$DataAccessException: 회원 조회 실패(id=42)
	at Ex.repository(Ex.java:13)
	at Ex.main(Ex.java:35)
Caused by: java.lang.IllegalStateException: 커넥션이 닫혔다
	at Ex.driver(Ex.java:7)
	at Ex.repository(Ex.java:11)
	... 1 more
getCause() = java.lang.IllegalStateException: 커넥션이 닫혔다
가장 깊은 원인 = java.lang.IllegalStateException: 커넥션이 닫혔다

--- 2. 원인을 버렸을 때
Ex$DataAccessException: 회원 조회 실패(id=42)
	at Ex.repositoryLosing(Ex.java:21)
	at Ex.main(Ex.java:43)
getCause() = null
```

```text
원인을 이었을 때                             원인을 버렸을 때
+-----------------------------------+      +-----------------------------------+
| DataAccessException               |      | DataAccessException               |
|   at repository(Ex.java:13)       |      |   at repositoryLosing(Ex.java:21) |
|   at main(Ex.java:35)             |      |   at main(Ex.java:43)             |
| Caused by: IllegalStateException  |      |                                   |
|   : 커넥션이 닫혔다                |      | 끝. 여기까지다                     |
|   at driver(Ex.java:7)            |      |                                   |
|   ... 1 more                      |      | "왜 실패했나"가 사라졌다            |
+-----------------------------------+      +-----------------------------------+
  진짜 원인 줄(driver:7)이 남는다              고칠 지점을 못 찾는다
```

그림 해설 (한 단계씩):

- 생성자의 **두 번째 인자**로 원인을 넘기면 `Caused by:` 블록이 생긴다.
- `... 1 more` 는 **위쪽 트레이스와 겹치는 프레임 수**다. 중복을 안 찍는 것뿐이고 정보가 빠진 게 아니다.
- 원인을 안 넘기면 **`getCause()` 가 `null`** 이고, 어디서 시작됐는지 알 방법이 없다.
- 예외 변환 자체는 좋은 습관이다 — **계층 경계에서 하위 기술을 감춘다.**\
  다만 **원인을 반드시 같이 넘겨야** 한다.

생성자에 원인 인자가 없는 예외는 `initCause` 로 나중에 붙인다.

```text
--- 4. initCause — 생성자에 원인 인자가 없는 예외에 나중에 붙이기
getCause() = java.lang.IllegalStateException: 커넥션이 닫혔다
두 번 부르면 -> java.lang.IllegalStateException: Can't overwrite cause with java.lang.RuntimeException: 두 번째

--- 5. 생성자에서 cause 를 준 뒤 initCause 를 부르면
-> java.lang.IllegalStateException: Can't overwrite cause with java.lang.RuntimeException: 또
```

- **원인은 한 번만 설정할 수 있다.** 두 번째 호출은 `IllegalStateException` 이다.
- 생성자로 이미 준 경우도 마찬가지다 — 덮어쓸 수 없다.

비용 — 원인 사슬 길이만큼 스택트레이스가 길어진다. 예외 생성 시 스택 수집 비용이 사슬마다 한 번씩 든다.

### (8) 전파와 정밀 재던지기

**언제 쓰나** — 중간 계층이 예외를 처리할 수 없어 위로 넘길 때.

**출력** (`Ex.java (25-e)`)

```text
로그만 남기고 재던짐: 파일 없음
main 이 잡은 것 = java.io.FileNotFoundException
```

```java
static void precise() throws IOException, SQLException {   // Exception 이 아니다
    try {
        mayThrow();                       // throws IOException, SQLException
    } catch (Exception e) {
        System.out.println("로그만 남기고 재던짐: " + e.getMessage());
        throw e;
    }
}
```

```text
Java 6 까지                                 Java 7 이후 (정밀 재던지기)
+-----------------------------------+      +-----------------------------------+
| catch (Exception e) { throw e; }  |      | catch (Exception e) { throw e; }  |
|                                   |      |                                   |
| 컴파일러: e 의 타입은 Exception    |      | 컴파일러: try 본문이 실제로 던질 수 |
| -> throws Exception 을 요구       |      | 있는 것은 IOException, SQLException|
|                                   |      | -> 그 둘만 요구                    |
| 호출자가 잡아야 할 것이 뭉개진다   |      | 타입 정보가 살아 있다               |
+-----------------------------------+      +-----------------------------------+
```

그림 해설 (한 단계씩):

- `catch (Exception e)` 로 넓게 잡아도 **컴파일러가 본문을 분석해 실제 가능한 것만** 요구한다.
- 그래서 **로그만 찍고 그대로 올리는 코드**를 타입을 뭉개지 않고 쓸 수 있다.
- 조건이 하나 있다 — **`catch` 변수가 effectively final 이어야 한다.** 재대입하면 꺼진다.

```text
Ex.java:12: error: unreported exception Exception; must be caught or declared to be thrown
            throw e;
            ^
1 error
```

비용 — 컴파일 타임 분석. 런타임 비용 0.

`throws` 는 **좁히거나 없앨 수 있다**(`Ex.java (25-h)`).

```text
Child2.m (throws 없음)
정적 타입이 Parent 이므로 throws IOException 을 여전히 요구한다
Child2.m (throws 없음)
throws 없이 던진 unchecked = java.lang.IllegalStateException: throws 선언 없음
```

- 하위 클래스가 `throws` 를 없애도, **정적 타입이 상위 타입이면 호출부는 여전히 처리해야 한다.**\
  컴파일러는 정적 타입만 보기 때문이다.
- unchecked 는 `throws` 에 **안 적어도 던질 수 있다.** 적을 수는 있고 문서 효과만 있다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### `try` 문의 형태 넷

```java
try { }                catch (E e) { }                 // catch 만
try { }                finally { }                     // finally 만
try { } catch (E e) { } finally { }                    // 둘 다
try (Res r = open()) { } catch (E e) { } finally { }   // 자원 + 둘 다 (26번 주제)
```

- `try` 혼자는 안 된다 — `catch` 나 `finally` 중 하나는 있어야 한다.\
  단 `try`-with-resources 는 **자원이 있으면 혼자 있어도 된다.**

### `catch` 절의 형태

```java
catch (IOException e) { }                        // 하나
catch (IOException | SQLException e) { }         // 다중 catch (7+) — e 는 암묵적 final
catch (Exception e) { throw e; }                 // 정밀 재던지기 (7+)
```

- 다중 `catch` 의 타입들은 **서로 하위 타입 관계가 없어야** 한다.\
  `catch (IOException | FileNotFoundException e)` 는 컴파일 에러다.

### 예외를 만드는 형태

```java
throw new IllegalArgumentException("메시지");
throw new IllegalStateException("메시지", cause);      // 원인 사슬
throw new MyException("메시지");                        // 직접 만든 것

class MyChecked   extends Exception        { }          // checked
class MyUnchecked extends RuntimeException { }          // unchecked
```

- 직접 만드는 예외는 **생성자 넷을 다 열어 두는 것이 관례**다 — `()`, `(String)`, `(String, Throwable)`, `(Throwable)`.\
  원인을 못 넘기는 예외 클래스는 나중에 사슬을 끊는다.

### `throws` 선언

```java
void a() throws IOException { }                  // 하나
void b() throws IOException, SQLException { }    // 여럿
void c() throws RuntimeException { }             // 적어도 되지만 강제는 아니다 — 문서 효과
```

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 다섯 다 **컴파일이 통과하고 실행도 조용하다.**

### 1. 예외를 삼킨다 — 최악의 한 줄

```java
try {
    driver();
} catch (IllegalStateException e) {
    // 아무것도 안 한다
}
```

**출력** (`Ex.java (25-d)`)

```text
--- 3. 삼켰을 때 — 아무 일도 없었던 것처럼 보인다
정상 종료한 것처럼 보이지만 조회는 실패했다
```

```text
삼킨 경우                                    남긴 경우
+-----------------------------------+      +-----------------------------------+
| 로그: (없음)                       |      | 로그: ERROR 회원 조회 실패(id=42) |
| 모니터링 에러율: 0%                 |      |       Caused by: 커넥션이 닫혔다   |
| 상위 계층: 정상 응답                |      | 모니터링 에러율: 상승 -> 알림      |
|                                   |      |                                   |
| 며칠 뒤 데이터 불일치로 발견        |      | 즉시 발견                          |
+-----------------------------------+      +-----------------------------------+
```

왜 최악인가 — **지표가 전부 초록인 채로 틀린다.**\
실패한 요청이 성공으로 집계되고, 알림이 안 오고, 재현할 입력도 모른다.

삼키는 것이 **정당한 경우도 있다.** 그때는 **이유를 주석으로 남긴다.**

```java
try {
    Thread.sleep(10);
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();   // 인터럽트 상태를 복원하고 빠져나간다
}
```

- `InterruptedException` 을 그냥 삼키면 **인터럽트 신호가 사라진다.** 이것도 삼키기다.

### 2. `printStackTrace()` 로 끝낸다

```java
catch (DataAccessException e) {
    e.printStackTrace();
}
```

- 삼키기보다는 낫지만 **운영에서는 거의 쓸모가 없다.**

| | `printStackTrace()` | 로거 |
|---|---|---|
| 출력 대상 | `System.err` 고정 | 설정한 appender(파일·수집기) |
| 레벨 | 없다 | ERROR/WARN 등으로 필터 가능 |
| 컨텍스트 | 없다 | 요청 ID·사용자·MDC 를 붙일 수 있다 |
| 시각 | 없다 | 포맷에 포함 |
| 비동기·버퍼링 | 없다(느리다) | 가능 |
| 로그 수집 | 표준 출력과 섞여 파싱이 깨진다 | 구조화 가능 |

- 실무 형태는 `log.error("회원 조회 실패 id={}", id, e);` 다 — **마지막 인자로 예외를 넘기면** 스택트레이스가 함께 찍힌다.
- 그리고 **잡아서 로그만 찍고 정상인 척하면 그것도 삼키기**다. 로그를 남겼으면 **위로 올리거나 의미 있는 대체 동작을 해야** 한다.
- 실패 처리 패턴(재시도·차단기·대체값) 자체는 [`../../../../../ops-patterns/failure-modes/`](../../../../../ops-patterns/failure-modes/) 가 정본이다.

### 3. 예외를 바꿔 던지면서 원인을 버린다

```java
catch (IllegalStateException e) {
    throw new DataAccessException("회원 조회 실패(id=42)", null);   // e 를 버렸다
}
```

**출력** (`Ex.java (25-d)`)

```text
Ex$DataAccessException: 회원 조회 실패(id=42)
	at Ex.repositoryLosing(Ex.java:21)
	at Ex.main(Ex.java:43)
getCause() = null
```

- 스택트레이스가 **예외를 만든 줄부터** 시작한다. 진짜 원인이 있던 `driver(Ex.java:7)` 이 없다.
- 로그만 보면 "조회에 실패했다"는 것만 알고 **왜 실패했는지 모른다.**
- 고치는 법은 한 글자다 — `null` 대신 `e`.

### 4. 넓은 것을 먼저 잡는다

```java
catch (IOException e) { }
catch (FileNotFoundException e) { }     // 영원히 안 걸린다
```

**컴파일 에러** (`Ex.java (25-a3)`)

```text
Ex.java:10: error: exception FileNotFoundException has already been caught
        } catch (FileNotFoundException e) {   // 이미 잡혔다
          ^
1 error
```

- **이것은 컴파일러가 잡아 준다.** 운이 좋은 경우다.
- 그러나 `catch (Exception e)` 를 맨 위에 두고 **아래에 아무것도 안 두면** 에러가 안 난다 — 그냥 전부 한 덩어리로 처리된다.\
  그때는 **종류별 처리를 잃는 것**이고 컴파일러가 말해 주지 않는다.

### 5. `finally` 에 `return` 이나 `throw` 를 쓴다

(5)절에서 본 셋이다. 정리하면 이렇다.

| 코드 | 결과 |
|---|---|
| `try { return 1; } finally { return 2; }` | **2** — 1이 사라진다 |
| `try { throw ...; } finally { return 3; }` | **3** — 예외가 사라진다 |
| `try { throw A; } finally { throw B; }` | **B** — A 가 사라진다(`getCause`·`getSuppressed` 둘 다 비어 있다) |

- 셋 다 `-Xlint:finally` 가 **`finally clause cannot complete normally`** 로 경고한다.
- 셋째 경우를 자동으로 막아 주는 장치가 `try`-with-resources 다 — 거기서는 사라질 예외가 **suppressed 로 붙는다**([`../26-try-with-resources/`](../26-try-with-resources/)).

## 구현 세부사항 대 언어 보장

이 절은 **"어디까지 믿어도 되나"**를 가른다.

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| unchecked = `RuntimeException` ∪ `Error` 의 하위 | **JLS (언어 보장)** | JLS §11.1.1 |
| checked 는 잡거나 `throws` 로 선언해야 한다 | **JLS (언어 보장)** | JLS §11.2 |
| `catch` 를 위에서 아래로 보고 처음 맞는 하나만 실행 | **JLS (언어 보장)** | JLS §14.20 |
| `finally` 가 모든 경로에서 실행된다 | **JLS (언어 보장)** | JLS §14.20.2 |
| `finally` 의 급작스러운 종료가 이전 결과를 버린다 | **JLS (언어 보장)** | JLS §14.20.2 |
| 다중 `catch` 변수가 암묵적 `final` | **JLS (언어 보장)** | JLS §14.20 |
| 정밀 재던지기 | **JLS (언어 보장, 7+)** | JLS §11.2.2 |
| 원인은 한 번만 설정 가능 | **javadoc (API 계약)** | `Throwable.initCause` javadoc |
| `finally` 코드가 경로마다 **복사**되는 것 | **구현 세부** | `javap` 관찰. JVM 명세는 예외 테이블만 규정한다 |
| `-Xlint:finally` 의 경고 문구 | **구현 세부** | javac 의 메시지(17·21·25 동일하게 관찰) |
| `... N more` 의 생략 규칙 | **구현 세부** | `Throwable.printStackTrace` 의 구현. 형식은 javadoc 이 "may" 로만 적는다 |
| 컴파일 에러 문구 전문 | **구현 세부** | javac 의 메시지 |

**경계 한 줄** — **"어디서 무엇이 터지나"는 명세**이고, **"메시지가 어떻게 생겼나"는 구현**이다.\
로그 파싱이나 테스트를 메시지 문구에 걸면 JDK 를 올릴 때 깨진다.

## 언제 쓰고 언제 안 쓰나

| 상황 | checked | unchecked |
|---|---|---|
| 호출자가 **복구할 수 있고 복구해야 하는** 실패 | **쓴다** (파일 없음 -> 다른 경로 시도) | — |
| 프로그래밍 오류(계약 위반·`null`·범위 초과) | — | **쓴다** (`IllegalArgumentException` 등) |
| 프레임워크·라이브러리의 내부 실패 | 호출자가 할 일이 없으면 부담만 된다 | **쓴다** (`DataAccessException` 계열이 이 선택) |
| 람다·스트림 안에서 던질 것 | **못 쓴다** — 표준 함수형 인터페이스가 `throws` 를 안 단다 | **쓴다** |
| 정말로 복구 불가능한 것 | — | `Error` 는 **내가 만들지 않는다** |

판단 규칙 세 줄.

- **"호출자가 이걸 받아서 할 일이 있나"** — 없으면 unchecked.
- **잡았으면 셋 중 하나는 해라** — 복구하거나, 변환해 올리거나, 로그와 함께 올린다. **빈 `catch` 는 금지.**
- **변환할 때는 원인을 반드시 같이 넘긴다.**

## 핵심 문장

- unchecked 는 **`RuntimeException` 과 `Error` 의 하위뿐**이다. `Throwable` 자신을 포함해 나머지는 전부 checked 다.
- checked 가 강제하는 것은 **"잡거나 `throws` 로 선언하라"** 하나이고, 그 밖에 컴파일러는 **안 날아오는 예외를 잡는 `catch`·도달 불가 `catch`·오버라이드의 `throws` 확대**를 막는다.
- `catch` 는 **위에서 아래로 처음 맞는 하나**만 실행한다. 좁은 것을 위에 둔다.
- `finally` 는 모든 경로에서 돌고, **급작스럽게 끝나면 진행 중이던 반환값이나 예외를 버린다.** `-Xlint:finally` 가 경고한다.
- **삼킨 예외는 지표를 초록으로 만든 채 틀린다.** 원인을 버린 변환은 스택트레이스에서 진짜 원인 줄을 지운다.
- `finally` 의 코드는 **바이트코드에서 경로마다 복사된다** — `javap` 로 세 벌을 확인했다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 25번)
- [`../../../../../ops-patterns/failure-modes/`](../../../../../ops-patterns/failure-modes/) — **그쪽은 운영 관점의 실패 모드 분류와 대응 패턴(재시도·차단기·격벽)까지, 여기는 언어의 예외 문법(checked 규칙·전파·다중 `catch`)부터.**\
  "실패했을 때 무엇을 할까"는 그쪽, "그 실패가 언어에서 어떻게 표현되고 전달되나"는 여기다
- [`../26-try-with-resources/`](../26-try-with-resources/) — 이 주제의 `finally` 함정 셋째(예외가 예외를 덮는 것)를 언어가 자동으로 막아 주는 장치
- [`../03-variables-and-assignment/`](../03-variables-and-assignment/) — 다중 `catch` 변수가 암묵적 `final` 인 것, `finally` 가 값은 못 바꾸고 객체 내용은 바꾸는 이유
- [`../06-initialization-order/`](../06-initialization-order/) — `static` 초기화 중 예외가 `ExceptionInInitializerError` 로 감싸지는 것
- [**38번 주제**](../38-optional/)(`Optional`) — "값이 없음"을 예외 대신 표현하는 수단. 예외를 흐름 제어에 쓰지 않기 위한 도구
- 목록의 **54번 주제**(`java.util.concurrent`) — `Future.get` 이 던지는 `ExecutionException` 의 원인 사슬. 다른 스레드의 예외가 어떻게 넘어오는가
- [**60번 주제**](../60-null-handling/)(`null` 다루기) — `Objects.requireNonNull` 로 계약 위반을 일찍 `NullPointerException` 으로 만드는 법

## 용어 풀이

- **예외(exception)** — 정상 흐름을 중단하고 호출 스택을 거슬러 올라가는 신호 객체. 최상위 타입은 `Throwable` 이다.
- **checked 예외(검사 예외)** — 컴파일러가 처리를 강제하는 예외. `RuntimeException`·`Error` 의 하위가 아닌 모든 `Throwable`.
- **unchecked 예외(비검사 예외)** — 강제가 없는 예외. `RuntimeException` 과 `Error` 및 그 하위.
- **`Error`** — JVM 수준의 회복 불가 사고를 나타내는 타입. 잡으라고 만든 것이 아니다.
- **전파(propagation)** — 잡히지 않은 예외가 호출자에게 그대로 넘어가는 것. 스택트레이스가 그 경로다.
- **다중 `catch`(multi-catch)** — `catch (A | B e)` 형태. Java 7 부터. 변수는 암묵적 `final` 이다.
- **정밀 재던지기(precise rethrow)** — 넓게 잡고 그대로 던졌을 때, 컴파일러가 실제로 가능한 예외만 요구하는 규칙. Java 7 부터.
- **원인 사슬(cause chain)** — 예외가 다른 예외를 원인으로 품는 구조. 출력에서 `Caused by:` 로 나타난다.
- **예외 변환(exception translation)** — 하위 계층 예외를 상위 계층의 의미 있는 예외로 바꿔 던지는 것. 원인을 같이 넘겨야 한다.
- **삼키기(swallowing)** — `catch` 에서 아무것도 하지 않아 예외를 없애 버리는 것.
- **예외 테이블(exception table)** — 클래스 파일에서 "어느 구간의 어떤 예외를 어느 오프셋이 처리하는지" 적어 둔 표. `javap -c` 가 보여 준다.
- **`athrow`** — 스택 맨 위의 예외 객체를 던지는 JVM 명령.

## 더 들어가면

- **예외 생성 비용의 대부분은 스택트레이스 수집이다.**\
  `Throwable` 의 4인자 생성자로 `writableStackTrace=false` 를 주면 수집을 끌 수 있다. 실행으로 확인했다(`Ex.java (25-e)`).

```text
writableStackTrace=false 일 때 깊이 = 0
```

  제어 흐름에 예외를 쓰는 라이브러리(파서 등)가 이 수단을 쓴다.\
  **다만 그것이 얼마나 빨라지는지는 이 문서에서 측정하지 않았다.**

- **`... 1 more` 는 정보 손실이 아니다.**\
  `Caused by:` 블록에서 위쪽 트레이스와 **겹치는 프레임 수**를 줄여 적은 것이다. 겹치지 않는 프레임은 전부 찍힌다.
- **`catch` 절이 많아도 예외가 안 나면 비용이 0이다.**\
  `catch` 는 예외 테이블의 행일 뿐이고, 정상 경로의 바이트코드에는 아무것도 추가되지 않는다((6)의 `javap` 에서 정상 경로에 검사 명령이 없다).
- **`Error` 를 잡아야 하는 예외적인 경우가 있다.**\
  서버 최상위 루프에서 `Throwable` 을 잡아 로그를 남기고 스레드를 재시작하는 패턴이 그것이다.\
  그때도 `OutOfMemoryError` 는 **잡아도 대개 할 수 있는 일이 없다** — 로그를 남기려다 또 터질 수 있다.
