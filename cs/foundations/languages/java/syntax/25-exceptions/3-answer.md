# java/syntax/25 — 예외: checked/unchecked·전파·다중 `catch`·재던지기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·스택트레이스·컴파일 에러·바이트코드는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 실행 프로그램 다섯은 **17.0.13 · 25.0.1** 에서도 돌려 **출력이 한 글자도 다르지 않았다**(관찰이다 — 보장은 JLS·javadoc 인용으로만 적었다).\
> 바이트코드는 `javap -c -p` 출력을, javadoc 은 `lib/src.zip` 의 실파일을 그대로 옮겼다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 열 개 중 무엇이 checked 인가

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

**경계선을 한 문장으로**

> **`RuntimeException` 의 하위이거나 `Error` 의 하위이면 unchecked, 나머지 `Throwable` 은 전부 checked** (JLS §11.1.1).

```text
                         Object
                           |
                       Throwable          <- checked
                      /          \
                Exception         Error   <- unchecked (와 그 하위 전부)
               /         \
   RuntimeException    IOException        <- 왼쪽 unchecked, 오른쪽 checked
   (와 그 하위 전부)     SQLException
```

- 흔한 오해는 **"`Exception` 은 checked, `RuntimeException` 은 unchecked"** 까지만 외우는 것이다.\
  그러면 `Throwable` 과 `Error` 를 어디에 넣을지 모른다.
- 정확한 규칙은 **"두 서브트리만 unchecked"** 다.

**`Throwable` 은 어느 쪽이고 어떻게 확인하나**

- **checked** 다. 컴파일로 확인했다(`Ex.java (25-a5)`).

```text
Ex.java:2: error: unreported exception Throwable; must be caught or declared to be thrown
    static void f() { throw new Throwable("checked 인가?"); }
                      ^
1 error
```

- `throws Throwable` 을 달거나 잡아야 컴파일된다. 즉 **`Throwable` 은 강제 대상**이다.

**`catch (Exception e)` 는 `StackOverflowError` 를 잡는가**

- **못 잡는다.** `Error` 는 `Exception` 의 하위가 아니다.

**출력** (`Ex.java (25-b)`)

```text
catch(Exception) 이 잡은 것 = java.lang.NullPointerException
Error 는 따로 잡아야 한다 = java.lang.StackOverflowError
```

- `catch (Exception e)` 는 checked 와 unchecked **예외**를 다 잡지만 **`Error` 는 안 잡는다.**
- 전부 잡으려면 `catch (Throwable t)` 여야 한다 — 그리고 그건 대개 하면 안 되는 일이다.

### 2. 이 네 코드는 각각 어떤 컴파일 에러를 내는가

**출력** (전부 `javac`, JDK 21.0.5)

**(A)** checked 미처리 (`Ex.java (25-a1)`)

```text
Ex.java:5: error: unreported exception IOException; must be caught or declared to be thrown
        risky();
             ^
1 error
```

**(B)** 안 날아오는 checked 예외를 잡음 (`Ex.java (25-a2)`)

```text
Ex.java:6: error: exception IOException is never thrown in body of corresponding try statement
        } catch (IOException e) {
          ^
1 error
```

**(C)** 넓은 것을 먼저 잡음 — 도달 불가 `catch` (`Ex.java (25-a3)`)

```text
Ex.java:10: error: exception FileNotFoundException has already been caught
        } catch (FileNotFoundException e) {   // 이미 잡혔다
          ^
1 error
```

**(D)** 다중 `catch` 변수 재대입 (`Ex.java (25-a4)`)

```text
Ex.java:7: error: multi-catch parameter e may not be assigned
            e = new RuntimeException("재대입");   // 다중 catch 의 변수는 암묵적 final
            ^
1 error
```

**(B)에서 `RuntimeException` 을 잡으면**

- **컴파일된다.** 에러가 안 난다.
- 이유: unchecked 예외는 **어디서든 날아올 수 있다**고 보기 때문이다.\
  `NullPointerException`·`ArithmeticException` 은 어떤 코드에서도 발생 가능하므로 "절대 안 날아온다"고 증명할 수 없다.
- checked 예외는 **던질 수 있는 지점이 `throws` 선언으로 전부 드러나 있으므로** 증명이 가능하다. 그래서 막는다.

```text
catch (IOException e)                       catch (RuntimeException e)
+-----------------------------------+      +-----------------------------------+
| 본문의 어느 호출도 IOException 을  |      | 어떤 코드든 unchecked 를 던질 수  |
| throws 하지 않는다                 |      | 있다고 본다                       |
| -> 절대 안 걸린다고 증명됨          |      | -> 증명 불가                      |
| -> 컴파일 에러                     |      | -> 통과                           |
+-----------------------------------+      +-----------------------------------+
```

**(D)가 말해 주는 성질**

- **다중 `catch` 의 예외 변수는 암묵적으로 `final`** 이다(JLS §14.20).
- 이유: 그 변수의 정적 타입이 **여러 타입의 최소 상한**이라, 재대입을 허용하면 정밀 재던지기(8번)의 타입 추론이 무너진다.
- 일반 `catch (IOException e)` 의 변수는 **`final` 이 아니다** — 재대입할 수 있다(권장하지는 않는다).
- 같은 암묵적 `final` 제약이 자원 변수에도 있다 — [`../03-variables-and-assignment/`](../03-variables-and-assignment/)·[`../26-try-with-resources/`](../26-try-with-resources/).

### 3. 다중 `catch` 는 어느 절이 걸리는가

**출력** (`Ex.java (25-b)`)

```text
fnf -> catch(FileNotFoundException) FileNotFoundException
io -> catch(IOException) IOException
iae -> catch(IAE|NPE) IllegalArgumentException / 변수 정적 타입 = RuntimeException
npe -> catch(IAE|NPE) NullPointerException / 변수 정적 타입 = RuntimeException
```

**네 가지 `kind` 의 결과**

| 던진 것 | 걸리는 `catch` |
|---|---|
| `FileNotFoundException` | 첫째 (`FileNotFoundException`) |
| `IOException` | 둘째 (`IOException`) |
| `IllegalArgumentException` | 셋째 (`IAE \| NPE`) |
| `NullPointerException` | 셋째 (`IAE \| NPE`) |

```text
throw FileNotFoundException             throw IOException
        |                                       |
        v                                       v
   catch (FNF)        <- 맞는다              catch (FNF)        <- 안 맞는다
   catch (IOException) <- 안 본다            catch (IOException) <- 맞는다
   catch (IAE|NPE)     <- 안 본다            catch (IAE|NPE)     <- 안 본다
```

- **위에서 아래로 훑고 처음 맞는 하나만** 실행한다(JLS §14.20). fallthrough 가 없다.
- `FileNotFoundException` 은 `IOException` 의 하위이므로 **둘째 절에도 맞지만**, 첫째가 먼저 잡아서 거기서 끝난다.

**셋째 절의 `e` 의 정적 타입**

- **`RuntimeException`** 이다.
- 다중 `catch` 변수의 타입은 나열한 타입들의 **최소 상한(least upper bound)** 이다.
- `IllegalArgumentException` 과 `NullPointerException` 의 공통 상위 중 가장 가까운 것이 `RuntimeException` 이다.
- 그래서 그 블록에서는 **`RuntimeException` 에 있는 메서드만** 부를 수 있다.\
  `IllegalArgumentException` 고유 메서드를 쓰려면 절을 나눠야 한다.

**첫 두 절의 순서를 바꾸면**

- **컴파일 에러**다 — 2번 (C)의 `exception FileNotFoundException has already been caught`.
- 넓은 팻말이 위에 있으면 아래 좁은 팻말은 **영원히 도달할 수 없으므로** 언어가 막는다.
- 규칙: **좁은 것을 위에, 넓은 것을 아래에.**

### 4. `finally` 가 있는 이 다섯 메서드의 결과는

**출력** (`Ex.java (25-c)`, 17·21·25 동일)

```text
overwrite()          = 2
swallow()            = 3
mutateAfterReturn()  = 1
mutateObject()       = ab
replaceException() 에서 밖으로 나온 것 = java.lang.RuntimeException: finally 가 던진 예외
  원래 예외는? getCause = null / suppressed 개수 = 0
```

**다섯의 결과**

| 메서드 | 결과 | 사라진 것 |
|---|---|---|
| `overwrite()` | **2** | `return 1` 의 1 |
| `swallow()` | **3** | `IllegalStateException` 전체 |
| `mutateAfter()` | **1** | 없다 (99 는 반영 안 됨) |
| `mutateObject()` | **`ab`** | 없다 (append 가 반영됨) |
| `replace()` | **`RuntimeException: 나중`** | `IllegalStateException: 원래` 전체 |

```text
함정 1 — return 을 덮어쓴다                 함정 2 — 예외를 삼킨다
+-----------------------------------+     +-----------------------------------+
| try { return 1; }                 |     | try { throw ISE; }                |
| finally { return 2; }             |     | finally { return 3; }             |
| -> 2                              |     | -> 3                             |
| 1 은 어디에도 안 남는다             |     | 예외가 통째로 없어진다             |
+-----------------------------------+     +-----------------------------------+
```

- 공통 규칙: **`finally` 가 정상적으로 끝나지 않으면**(`return`·`throw`·`break`·`continue`) **진행 중이던 결과가 버려진다**(JLS §14.20.2).

**`mutateAfter` 와 `mutateObject` 가 갈리는 이유**

```text
mutateAfter — 값을 복사했다                 mutateObject — 같은 객체를 본다
+-----------------------------------+     +-----------------------------------+
| int x = 1;                        |     | StringBuilder sb = new SB("a");   |
| return x;  -> 반환값 1 로 확정     |     | return sb; -> 반환값 = 참조 #7     |
| finally { x = 99; }               |     | finally { sb.append("b"); }       |
|   x 라는 쪽지만 고쳤다              |     |   #7 창고 안을 고쳤다              |
| -> 1                              |     | -> "ab"                           |
+-----------------------------------+     +-----------------------------------+
```

- `return x;` 는 **`x` 의 값을 읽어 반환값으로 확정한 뒤** `finally` 를 돈다.
- `mutateObject` 도 반환값(참조 #7)은 확정됐다. 다만 **그 참조가 가리키는 객체 안을 고쳤으므로** 호출자가 본다.
- 값 전달 규칙 그대로다 — [`../03-variables-and-assignment/`](../03-variables-and-assignment/) 가 정본이다.

**`replace()` 에서 원래 예외는 남는가**

- **안 남는다.** 출력이 직접 말한다.

```text
  원래 예외는? getCause = null / suppressed 개수 = 0
```

- `getCause()` 도 `null` 이고 `getSuppressed()` 도 비어 있다. **흔적이 전혀 없다.**
- 이 손실을 자동으로 막아 주는 것이 `try`-with-resources 의 suppressed 다 — [`../26-try-with-resources/`](../26-try-with-resources/).

**컴파일러는 무엇을 경고하고, 보려면 무엇이 필요한가**

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

- `overwrite`(8행) · `swallow`(17행) · `replace`(46행) **셋을 경고한다.**
- `mutateAfter`·`mutateObject` 는 `finally` 가 정상적으로 끝나므로 경고가 없다.
- **기본 컴파일에서는 안 나온다.** `-Xlint:finally`(또는 `-Xlint:all`)가 필요하다.
- 17·21·25 세 JDK 에서 **문구·줄 번호·개수가 모두 같았다.**
- 빌드에 `-Xlint:all -Werror` 를 걸면 **이 부류의 버그가 빌드에서 막힌다.**

### 5. `try { return f(); } finally { g(); }` 의 실행 순서

**출력** (`Ex.java (25-c)`)

```text
order():
  try 본문
  return 식 평가
  finally
  결과 = 7
```

**순서**

1. `try` 본문 실행
2. **`f()` 평가** — 반환값이 여기서 확정된다
3. **`g()` 실행** (`finally`)
4. 확정된 반환값을 호출자에게 전달

- 출력이 그대로 그 순서다 — `return 식 평가` 가 `finally` 보다 **먼저** 나왔다.
- 이것이 4번의 `mutateAfter()` 가 1을 돌려주는 이유다. 반환값은 이미 2단계에서 확정됐다.

**바이트코드에서 `finally` 의 코드는 몇 번 나타나는가**

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

- **세 번** 나타난다 — 오프셋 **7 · 35 · 46**.

```text
소스는 한 번                                클래스 파일에는 세 벌

  finally {                                 오프셋 7  — return 10 경로용
      System.out.println("cleanup");        오프셋 35 — return 20 경로용
  }                                         오프셋 46 — 예외 경로용
```

**왜인가**

- 메서드를 **나가는 길이 셋**이기 때문이다: `return 10`, `return 20`, 예외 전파.
- 각 길에 마무리 코드를 **복사해 박아야** "어느 길로 나가든 실행된다"가 성립한다.
- 예외 경로는 예외 테이블의 `any` 핸들러다 — `astore_2` 로 예외를 저장하고, 마무리를 돌고, `athrow` 로 다시 던진다.
- 함의: **`finally` 가 길면 메서드 크기가 경로 수만큼 부풀어 오른다.**\
  *(그것이 JIT 인라인에 미치는 영향은 이 문서에서 측정하지 않았다.)*
- **정상 경로에는 예외 관련 검사 명령이 하나도 없다** — `catch` 가 많아도 예외가 안 나면 비용이 0인 이유다.

### 6. 원인 사슬을 이었을 때와 버렸을 때 스택트레이스

**출력** (`Ex.java (25-d)`, 17·21·25 동일 — `printStackTrace(System.out)` 출력 그대로)

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
```

**두 번째 인자를 `null` 로 바꾸면**

```text
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
|   : 커넥션이 닫혔다                |      | 끝                                |
|   at driver(Ex.java:7)   <- 진짜   |      |                                   |
|   ... 1 more                      |      | driver:7 이 사라졌다               |
+-----------------------------------+      +-----------------------------------+
```

- 왼쪽은 **`driver(Ex.java:7)` 이라는 실제 발생 지점**이 남는다. 오른쪽은 없다.
- 오른쪽 로그만 보면 "조회가 실패했다"는 것만 알고 **왜 실패했는지 모른다.**
- 고치는 법은 한 글자 — `null` 을 `e` 로 바꾼다.

**`... 1 more` 는 무엇인가**

- **위쪽 트레이스와 겹치는 프레임 수**다.
- `Caused by:` 블록의 프레임은 `driver(7)` -> `repository(11)` -> `main(35)` 인데, `main(35)` 는 위 블록에 이미 찍혔으므로 **생략하고 개수만 적었다.**
- 정보가 빠진 것이 아니다. 중복을 안 찍은 것뿐이다.\
  *(이 생략 형식은 `Throwable.printStackTrace` 의 구현 세부다.)*

**`initCause` 를 두 번 부르면**

**출력** (`Ex.java (25-d)`)

```text
--- 4. initCause — 생성자에 원인 인자가 없는 예외에 나중에 붙이기
getCause() = java.lang.IllegalStateException: 커넥션이 닫혔다
두 번 부르면 -> java.lang.IllegalStateException: Can't overwrite cause with java.lang.RuntimeException: 두 번째

--- 5. 생성자에서 cause 를 준 뒤 initCause 를 부르면
-> java.lang.IllegalStateException: Can't overwrite cause with java.lang.RuntimeException: 또

--- 6. cause 없이 만든 예외에는 나중에 붙일 수 있다
getCause() = java.lang.RuntimeException: 나중에 붙인 원인
```

- **`IllegalStateException: Can't overwrite cause with ...`** 가 난다.
- **원인은 한 번만 설정할 수 있다.** 생성자로 이미 준 경우도 덮어쓸 수 없다.
- `initCause` 는 **생성자에 원인 인자가 없는 레거시 예외**에 원인을 붙일 때 쓰는 수단이다.\
  새로 만드는 예외라면 `(String, Throwable)` 생성자를 열어 두는 편이 낫다.

### 7. 예외를 삼키는 것이 왜 최악인가

**출력** (`Ex.java (25-d)`)

```text
--- 3. 삼켰을 때 — 아무 일도 없었던 것처럼 보인다
정상 종료한 것처럼 보이지만 조회는 실패했다
```

**관측 가능한 흔적**

- **없다.** 로그도, 스택트레이스도, 종료 코드도, 지표도 전부 정상이다.

```text
삼킨 경우                                    올린 경우
+-----------------------------------+      +-----------------------------------+
| 로그: (없음)                       |      | 로그: ERROR 회원 조회 실패(id=42) |
| 모니터링 에러율: 0%                 |      |       Caused by: 커넥션이 닫혔다   |
| 상위 계층: 정상 응답 (빈 결과)      |      | 모니터링 에러율: 상승 -> 알림      |
| 알림: 없음                         |      | 알림: 즉시                        |
|                                   |      |                                   |
| 며칠 뒤 데이터 불일치로 발견        |      | 발생 즉시 발견                     |
+-----------------------------------+      +-----------------------------------+
```

- **지표가 전부 초록인 채로 틀린다.** 실패한 요청이 성공으로 집계된다.
- 재현할 입력도, 발생 시각도, 원인도 남지 않는다.
- 다른 버그는 "어디서 터졌나"를 찾는 문제지만, 삼킨 예외는 **"터졌다는 사실 자체"를 찾는 문제**다.

**`printStackTrace()` 가 운영에서 부족한 이유**

| | `printStackTrace()` | 로거 |
|---|---|---|
| 출력 대상 | `System.err` 고정 | 설정한 appender(파일·수집기) |
| 레벨 | 없다 | ERROR/WARN 등으로 필터·알림 연동 |
| 컨텍스트 | 없다 | 요청 ID·사용자·MDC |
| 시각 | 없다 | 포맷에 포함 |
| 구조화 | 안 된다 | JSON 등으로 수집 가능 |
| 성능 | 동기·비버퍼 | 비동기·버퍼링 가능 |

- 실무 형태: `log.error("회원 조회 실패 id={}", id, e);`\
  마지막 인자로 예외를 넘기면 **스택트레이스가 함께 찍힌다**(SLF4J 계열의 관례).
- 그리고 **잡아서 로그만 찍고 정상인 척하면 그것도 삼키기다.**\
  로그를 남겼으면 **올리거나** 의미 있는 대체 동작을 해야 한다.

**삼키는 것이 정당한 경우**

- **정말로 무시해도 되는 실패**이고, 그 판단 근거를 **주석으로 남기는** 경우.
- 대표 사례는 `InterruptedException` 이다 — 그냥 삼키면 **인터럽트 신호가 사라진다.**

```java
try {
    Thread.sleep(10);
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();   // 상태를 복원하고 빠져나간다
}
```

- "무시한다"와 "상태를 복원하고 빠져나간다"는 다르다. 앞은 버그이고 뒤는 정당한 처리다.
- 운영 관점의 실패 처리 판단(재시도할까·대체값을 줄까·차단할까)은 [`../../../../../ops-patterns/failure-modes/`](../../../../../ops-patterns/failure-modes/) 가 정본이다.

### 8. 정밀 재던지기는 무엇을 살려 주는가

**출력** (`Ex.java (25-e)`)

```text
로그만 남기고 재던짐: 파일 없음
main 이 잡은 것 = java.io.FileNotFoundException
```

**`throws Exception` 이 아니어도 컴파일되는 이유**

- 컴파일러가 **`try` 본문이 실제로 던질 수 있는 checked 예외**를 분석해, `throw e;` 가 그 집합만 던진다고 본다.
- 본문의 `mayThrow()` 가 `throws IOException, SQLException` 이므로 **그 둘만** 요구된다.

```text
Java 6 까지                                 Java 7 이후 (정밀 재던지기)
+-----------------------------------+      +-----------------------------------+
| catch (Exception e) { throw e; }  |      | catch (Exception e) { throw e; }  |
| 컴파일러: e 의 타입은 Exception    |      | 컴파일러: 본문이 던질 수 있는 것은  |
| -> throws Exception 을 요구       |      |   IOException, SQLException 뿐    |
| 호출자가 잡아야 할 것이 뭉개진다   |      | -> 그 둘만 요구                    |
+-----------------------------------+      +-----------------------------------+
```

- 그래서 **"로그만 찍고 그대로 올린다"**는 흔한 패턴을 **타입 정보를 잃지 않고** 쓸 수 있다.
- 호출자는 여전히 `IOException` 과 `SQLException` 을 따로 처리할 수 있다.

**어느 버전부터인가**

- **Java 7** 부터다(JLS §11.2.2). 다중 `catch` 와 같은 릴리스에 들어왔다.

**`catch` 블록 안에서 `e = new Exception(...)` 을 하면**

**컴파일 에러** (`Ex.java (25-a6)`)

```text
Ex.java:12: error: unreported exception Exception; must be caught or declared to be thrown
            throw e;
            ^
1 error
```

- **정밀 재던지기가 꺼진다.** `e` 가 effectively final 이 아니게 되면 컴파일러가 선언된 타입(`Exception`)으로만 본다.
- 그러면 `throws Exception` 이 필요해진다.
- 즉 **이 기능은 effectively final 조건 위에 서 있다** — [`../03-variables-and-assignment/`](../03-variables-and-assignment/) 와 직접 이어진다.

### 9. `throws` 는 오버라이드에서 어떻게 다뤄지는가

**넓히는 것**

**컴파일 에러** (`Ex.java (25-g)`)

```text
Ex.java:5: error: m() in Child cannot override m() in Parent
        @Override void m() throws Exception {}    // 넓히기 시도
                       ^
  overridden method does not throw Exception
1 error
```

- **허용되지 않는다.** 하위 타입은 상위 타입보다 **더 많이 던질 수 없다.**
- 이유는 리스코프 치환이다 — 상위 타입으로 받아 쓰는 코드는 상위의 `throws` 만 처리하고 있다.\
  하위가 더 던지면 그 코드가 못 잡는 예외가 날아간다.

**좁히거나 없애는 것**

**출력** (`Ex.java (25-h)`)

```text
Child2.m (throws 없음)
정적 타입이 Parent 이므로 throws IOException 을 여전히 요구한다
Child2.m (throws 없음)
throws 없이 던진 unchecked = java.lang.IllegalStateException: throws 선언 없음
```

- **둘 다 허용된다.** `FileNotFoundException` 으로 좁히는 것도, 아예 `throws` 를 없애는 것도 컴파일된다.

**상위 타입 변수로 받아 호출하면**

```text
Parent p = new Child2();       Child2 c = new Child2();
p.m();                          c.m();
  |                               |
  정적 타입 = Parent              정적 타입 = Child2
  Parent.m 은 throws IOException  Child2.m 은 throws 없음
  -> 호출부가 처리해야 한다        -> 처리 불필요
```

- **여전히 처리해야 한다.** 컴파일러는 **정적 타입만** 본다.
- 실제 객체가 아무것도 안 던지더라도 상관없다 — 런타임 타입을 컴파일러는 모른다.
- 이 비대칭은 오버라이딩 일반 규칙과 같다([**09번 주제**](../09-inheritance-overriding/)).

**unchecked 를 `throws` 에 적는 것**

- **의미는 있다. 다만 강제는 아니다.**
- 실행으로 확인했다 — `throws` 선언 없이 `IllegalStateException` 을 던져도 컴파일되고 실행된다.
- 적는 이유는 **문서 효과**다. javadoc 의 `@throws` 와 함께 "이 메서드가 어떤 조건에서 실패하는지"를 알린다.
- 호출자에게 처리를 강제하지는 않는다.

### 10. 새 예외를 만들 때 checked 와 unchecked 중 무엇을 고르나

**선택 기준 한 문장**

> **호출자가 그 예외를 받아서 할 수 있고 해야 하는 복구 동작이 있으면 checked, 없으면 unchecked.**

| 상황 | 선택 |
|---|---|
| 파일이 없으면 기본 설정으로 진행한다 | checked — 호출자가 분기해야 한다 |
| 인자가 `null` 이다 (프로그래밍 오류) | unchecked (`NullPointerException`·`IllegalArgumentException`) |
| 상태가 맞지 않는다 (호출 순서 오류) | unchecked (`IllegalStateException`) |
| DB 연결이 끊겼다 | 대개 unchecked — 호출자가 할 수 있는 일이 없다 |

**프레임워크·라이브러리가 unchecked 를 고르는 이유**

- **호출자가 할 일이 없는 실패를 checked 로 만들면 `throws` 선언이 전파되며 온 코드를 오염시킨다.**
- 결국 `catch (SQLException e) { throw new RuntimeException(e); }` 같은 껍데기가 계층마다 생긴다 — 얻는 것 없이 코드만 는다.
- 그래서 스프링의 `DataAccessException` 계열, 하이버네이트, 다수의 현대 라이브러리가 unchecked 를 쓴다.

**람다·스트림 안에서**

- **unchecked 여야 한다.**
- `Function`·`Supplier`·`Consumer` 등 **표준 함수형 인터페이스가 `throws` 를 선언하지 않기** 때문이다.\
  checked 예외를 던지면 람다 본문에서 컴파일 에러가 난다.
- 우회는 셋: (1) 람다 안에서 잡아 unchecked 로 감싼다, (2) `throws` 를 단 커스텀 함수형 인터페이스를 만든다, (3) 애초에 unchecked 로 설계한다.
- 함수형 인터페이스의 시그니처 문제는 [`../31-functional-interfaces/`](../31-functional-interfaces/) 가 정본이다.

**직접 만든 예외 클래스에 열어 둘 생성자**

```java
public class MyException extends RuntimeException {
    public MyException() { super(); }
    public MyException(String message) { super(message); }
    public MyException(String message, Throwable cause) { super(message, cause); }
    public MyException(Throwable cause) { super(cause); }
}
```

- **넷을 다 여는 것이 관례**다. 특히 **`(String, Throwable)`** 은 반드시 있어야 한다.
- 없으면 예외 변환 시 **원인을 넘길 방법이 없어** 사슬이 끊긴다(6번의 오른쪽 칸이 된다).
- `initCause` 로 우회할 수는 있지만, 생성자로 넘기는 편이 짧고 한 번만 설정된다는 제약도 안 걸린다.

### 11. 다른 주제와 잇기

**`finally` 에서 예외가 예외를 덮는 문제를 막아 주는 문법**

- **`try`-with-resources** 다(Java 7).
- 자원의 `close()` 가 던진 예외가 본문 예외를 덮지 않고 **suppressed 로 붙는다.**
- 4번의 `replace()` 와 대비해 보면 차이가 분명하다.

```text
손으로 쓴 try-finally                        try-with-resources
+-----------------------------------+      +-----------------------------------+
| 본문 예외 -> 사라진다              |      | 본문 예외 -> 밖으로 나온다         |
| close 예외 -> 밖으로 나온다        |      | close 예외 -> suppressed 로 붙는다 |
| getSuppressed().length == 0       |      | getSuppressed().length == 1       |
+-----------------------------------+      +-----------------------------------+
```

- 정본은 [`../26-try-with-resources/`](../26-try-with-resources/).

**다중 `catch` 변수가 암묵적 `final` 인 것**

- [`../03-variables-and-assignment/`](../03-variables-and-assignment/) 의 `final`·effectively final 과 같은 뿌리다.
- 그리고 **정밀 재던지기(8번)가 그 조건 위에 서 있다** — 재대입하면 기능이 꺼진다.
- 자원 변수(`try (Res r = ...)`)도 같은 제약이다.

**운영 패턴과 이 주제의 경계**

- **여기는 "언어가 실패를 어떻게 표현하고 전달하는가"** — checked 규칙, `catch` 순서, 전파, 원인 사슬, `finally` 의미.
- **저쪽은 "그 실패를 만났을 때 시스템이 무엇을 하는가"** — 재시도·백오프·차단기·격벽·대체값.
- 예: "`IOException` 을 어떻게 잡나"는 여기, "재시도를 몇 번 어떤 간격으로 하나"는 [`../../../../../ops-patterns/failure-modes/`](../../../../../ops-patterns/failure-modes/) 와 [`../../../../../ops-patterns/01-retry-backoff/`](../../../../../ops-patterns/01-retry-backoff/).

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java (25-a1)` `javac` | checked 미처리 -> `unreported exception IOException` | 21 |
| `Ex.java (25-a2)` `javac` | 안 날아오는 checked 를 잡음 -> `is never thrown in body` | 21 |
| `Ex.java (25-a3)` `javac` | 넓은 것 먼저 -> `has already been caught` | 21 |
| `Ex.java (25-a4)` `javac` | 다중 `catch` 변수 재대입 -> `multi-catch parameter e may not be assigned` | 21 |
| `Ex.java (25-a5)` `javac` | `Throwable` 이 checked 임 -> `unreported exception Throwable` | 21 |
| `Ex.java (25-a6)` `javac` | `catch` 변수 재대입이 정밀 재던지기를 끔 | 21 |
| `Ex.java (25-b)` | 계층 10종의 checked 여부, 다중 `catch` 4경로, `catch(Exception)` 이 `Error` 를 못 잡음 | 17 · 21 · 25 (동일) |
| `Ex.java (25-c)` | `finally` 함정 다섯, 실행 순서 | 17 · 21 · 25 (동일) |
| `Ex.java (25-c)` `javac -Xlint:all` | `finally clause cannot complete normally` 경고 3건 | 17 · 21 · 25 (문구·줄 동일) |
| `Ex.java (25-d)` | 원인 사슬 `Caused by:`·`... 1 more`, 원인 버리기, 삼키기, `initCause` 3경우 | 17 · 21 · 25 (동일) |
| `Ex.java (25-e)` | 정밀 재던지기, 전파 스택트레이스(잡은 것·uncaught), `writableStackTrace=false` | 17 · 21 · 25 (동일) |
| `Ex.java (25-f)` `javap -c -p` | `finally` 코드가 오프셋 7·35·46 에 세 번 복사됨, 예외 테이블 | 21 |
| `Ex.java (25-g)` `javac` | 오버라이드에서 `throws` 넓히기 -> 컴파일 에러 | 21 |
| `Ex.java (25-h)` | `throws` 좁히기·없애기, 정적 타입 기준 요구, unchecked 는 선언 없이 던짐 | 17 · 21 · 25 (동일) |
| `src.zip` 열람 | `Throwable.addSuppressed`/`getSuppressed` 의 `@since 1.7` 과 javadoc | 21 |

**구현 의존 항목** — 컴파일 에러·경고의 **문구 전문**, `... N more` 의 생략 형식, `finally` 코드가 세 벌 복사되는 것은 **javac/JDK 의 구현 세부**다.\
버전이 올랐을 때 다시 돌려 볼 것은 **`(25-a*)` 의 에러 문구와 `(25-f)` 의 `javap`** 다.\
반면 checked 분류·`catch` 순서·`finally` 의 의미·정밀 재던지기는 JLS 가 보장한다.
