# java/syntax/33 — `synchronized`·`volatile`: 문법과 그 보장이 끝나는 자리 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·바이트코드는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> ⚠️ **측정 조건** — JMH 가 아니다. 스레드를 직접 띄워 **같은 실험을 N회 반복**하고 「정답 횟수 / N」과 「관측 최소~최대」로 적는다.\
> 머신 **24코어**(Linux x86-64). 반복 수는 실험마다 본문에 적었다(경쟁 20회 또는 10회, 가시성 5회, 교착 20회).\
> **같은 명령을 두 번 돌리면 정답 횟수가 18/20 → 13/20 으로 바뀐다.** 수치는 "**0 인가 0 이 아닌가**"로만 읽는다.\
> `(33-a)` `(33-b)` `(33-c)` `(33-e)` 는 **17.0.13 · 21.0.5 · 25.0.1** 에서 각각 돌렸다.
> JLS·javadoc 인용은 링크된 명세와 `lib/src.zip` 원문이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 동기화 없이 카운터를 올리면 몇 번이나 맞나

**출력** (`Ex.java` — 33-a, 각 조건 20회 반복, JDK 21.0.5, 같은 명령을 연달아 2회)

```text
===== 실행 1
--- 스레드 2 x 100회 (기대 200) / 각 20회 반복
  int++            정답 20/20회   관측 200 ~ 200
--- 스레드 2 x 1000회 (기대 2000) / 각 20회 반복
  int++            정답 20/20회   관측 2000 ~ 2000
--- 스레드 2 x 100000회 (기대 200000) / 각 20회 반복
  int++            정답 18/20회   관측 105502 ~ 200000
--- 스레드 8 x 100000회 (기대 800000) / 각 20회 반복
  int++            정답 18/20회   관측 701456 ~ 800000
===== 실행 2
--- 스레드 2 x 100회 (기대 200) / 각 20회 반복
  int++            정답 20/20회   관측 200 ~ 200
--- 스레드 2 x 1000회 (기대 2000) / 각 20회 반복
  int++            정답 19/20회   관측 1300 ~ 2000
--- 스레드 2 x 100000회 (기대 200000) / 각 20회 반복
  int++            정답 15/20회   관측 100017 ~ 200000
--- 스레드 8 x 100000회 (기대 800000) / 각 20회 반복
  int++            정답 13/20회   관측 284119 ~ 800000
```

**왜 그런가**

- **(A) 20/20회 정답**이다. 스레드 둘이 100회씩 올리는 정도로는 **서로 겹칠 틈이 없다.**
- **(D) 는 13~18/20회 정답**이다. 실패가 **소수파**다 — 8스레드 × 10만 회로 키워도 그렇다.
- **틀릴 때는 항상 기대값보다 작다.** 관측 하한이 284,119(기대 800,000)까지 내려갔다.\
  "읽고-고치고-쓰기" 중 남의 결과를 덮어쓰기 때문이라 **잃기만 하고 얻지는 않는다.**
- **한 번만 돌려 보면 13/20 의 경우에도 65% 확률로 정답을 본다.**\
  놓치는 것은 이것이다 — **테스트 통과는 "경쟁이 없다"의 증거가 아니다.**

★ **이 문항의 수치를 외우지 마라.** 같은 명령의 1회차와 2회차가 18 → 13 으로 달랐다.\
외울 것은 "**작으면 항상 맞고, 크게 해도 절반 이상 맞는다**"는 모양이다.

### 2. `volatile` 을 붙이면 더 자주 맞을까

**출력** (`Ex.java` — 33-a, JDK 21.0.5)

```text
--- 스레드 8 x 100000회 (기대 800000) / 각 20회 반복
  int++            정답 18/20회   관측 701456 ~ 800000
  volatile int++   정답  0/20회   관측 211563 ~ 311445
  synchronized ++  정답 20/20회
```

**`-Xint`(JIT 끔) 로 같은 프로그램을 돌리면**

```text
--- 스레드 8 x 100000회 (기대 800000) / 각 20회 반복
  int++            정답  0/20회   관측 153910 ~ 304667
  volatile int++   정답  0/20회   관측 260404 ~ 358424
  synchronized ++  정답 20/20회
```

**왜 그런가**

- **`volatile` 쪽이 훨씬 적다** — 18/20 대 **0/20**.
- 그러나 **"`volatile` 이 더 위험하다"는 뜻이 아니다.**\
  `-Xint` 에서는 **일반 `int++` 도 0/20** 이다. 코드는 그대로인데 결과가 뒤집혔다.
- 즉 기본 모드의 18/20 은 **코드의 안전성이 아니라 최적화가 만든 것**이다.\
  `volatile` 은 그 최적화를 막아 **숨어 있던 경쟁을 보이게** 했을 뿐이다.
- **관측된 정답률은 "이 코드가 맞는가"가 아니라 "이번 실행에서 스레드들이 겹쳤는가"를 재고 있다.**\
  JIT 가 필드 접근에 무엇을 하는지는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §4~5 가 정본이다.

```text
JIT 켜짐 (기본)                            JIT 꺼짐 (-Xint)

  int++          18/20 정답               int++          0/20 정답
  volatile int++  0/20 정답               volatile int++ 0/20 정답
        |                                        |
        v                                        v
  안전해서가 아니다                          같은 코드가 항상 틀린다
```

### 3. `n++` 은 바이트코드로 몇 개의 명령인가

**출력** (`Ex.java` — 33-d, `javap -c -p`, JDK 21.0.5)

```text
  synchronized void mSync();
    Code:
       0: aload_0
       1: dup
       2: getfield      #7                  // Field n:I
       5: iconst_1
       6: iadd
       7: putfield      #7                  // Field n:I
      10: return
```

**왜 그런가**

- **읽기 = `getfield`, 더하기 = `iadd`, 쓰기 = `putfield`** 세 단계다.
- **`volatile` 을 붙여도 명령 개수는 그대로다.**\
  `readV()`(volatile 필드)와 `readPlain()`(일반 필드)의 바이트코드는 **둘 다 `getfield`** 로 같았다.

```text
  int readV();
    Code:
       0: aload_0
       1: getfield      #13                 // Field v:I
       4: ireturn

  int readPlain();
    Code:
       0: aload_0
       1: getfield      #7                  // Field n:I
       4: ireturn
```

- 다른 것은 **필드 선언의 플래그**뿐이다.

```text
  int n;
    flags: (0x0000)
  volatile int v;
    flags: (0x0040) ACC_VOLATILE
```

- 그래서 **`volatile` 은 세 명령을 하나로 묶지 못한다.** 각 명령이 최신 값을 보게 할 뿐이다.\
  둘이 동시에 `getfield` 로 `5` 를 읽으면 둘 다 `6` 을 쓴다.
- ★ **외울 것은 명령 이름이 아니라 「읽고-고치고-쓰기가 세 단계다**」이다.

### 4. 플래그로 루프를 멈출 수 있나

**출력** (`Ex.java` — 33-b, 각 5회, JDK 21.0.5)

```text
=== 기본(JIT)
--- 일반 boolean 플래그로 루프를 멈출 수 있나 (각 2초 기다림, 5회)
  0: 멈췄나 = false
  1: 멈췄나 = false
  2: 멈췄나 = false
  3: 멈췄나 = false
  4: 멈췄나 = false
--- volatile boolean 플래그 (각 2초 기다림, 5회)
  0: 멈췄나 = true
  1: 멈췄나 = true
  2: 멈췄나 = true
  3: 멈췄나 = true
  4: 멈췄나 = true
=== -Xint
--- 일반 boolean 플래그로 루프를 멈출 수 있나 (각 2초 기다림, 5회)
      (읽기 스레드 종료, 회전 40481260)
  0: 멈췄나 = true
      (읽기 스레드 종료, 회전 36626617)
  1: 멈췄나 = true
      (읽기 스레드 종료, 회전 45011312)
  2: 멈췄나 = true
      (읽기 스레드 종료, 회전 47528223)
  3: 멈췄나 = true
      (읽기 스레드 종료, 회전 47199983)
  4: 멈췄나 = true
```

**왜 그런가**

- **(A) 일반 플래그는 0/5회 멈췄다.** 2초를 다 기다려도 안 멈춘다.
- **(B) `volatile` 은 5/5회 멈췄다.** 다른 코드는 한 글자도 안 바뀌었다.
- **`-Xint` 에서는 (A)도 5/5회 멈춘다.** 회전 수까지 찍혔다(3,662만~4,753만 회).
- 한 문장으로: **`volatile` 이 하는 일은 "내가 쓴 값을 남이 보게 하는 것"이다.**
- 이 실험은 **17 · 21 · 25 세 JDK 에서 같았다**(일반 0/5, `volatile` 5/5).\
  ★ **세 곳에서 같았다는 것은 관찰이지 보장이 아니다.** 보장은 JLS §17.4 로만 적는다.

### 5. `synchronized` 를 붙였는데 왜 틀리나

**출력** (`Ex.java` — 33-c, 8스레드 × 5만 회, 각 10회 반복, JDK 21.0.5)

```text
--- 공유 static 필드를 8스레드 x 50000회 증가 (기대 400000) / 각 10회 반복
  인스턴스 하나 + synchronized 인스턴스 메서드              정답 10/10회  관측 400000 ~ 400000
  인스턴스 둘 + synchronized 인스턴스 메서드               정답  0/10회  관측 369377 ~ 379316
  인스턴스 둘 + synchronized(this) 블록               정답  0/10회  관측 369419 ~ 378437
  인스턴스 둘 + static synchronized                 정답 10/10회  관측 400000 ~ 400000
  인스턴스 둘 + synchronized(Counter.class) 블록      정답 10/10회  관측 400000 ~ 400000
  인스턴스 하나인데 절반은 static synchronized            정답  0/10회  관측 369019 ~ 380883
```

**왜 그런가**

- **10/10회 정답인 것은 (A)·(C)·(D)** 다. 셋 다 **열쇠가 하나**다.
- **(E)가 틀리는 이유** — 절반은 `this` 를, 절반은 `Counter.class` 를 잠근다. **둘은 서로를 배제하지 않는다.**
- 네 형태의 잠금 대상:

| 형태 | 잠금 대상 |
|---|---|
| `synchronized void m()` | **`this`** — 인스턴스마다 다르다 |
| `static synchronized void m()` | **`Counter.class`** — 클래스당 하나 |
| `synchronized (this) { }` | `this` — 위와 같다 |
| `synchronized (Counter.class) { }` | `Counter.class` — 위와 같다 |

- 이 패턴(어느 줄이 0/10 이고 어느 줄이 10/10 인지)은 **17 · 21 · 25 에서 같았다.** 관측된 수치만 달랐다.
- **규칙 한 줄** — `static` 데이터는 `static` 락으로, 인스턴스 데이터는 인스턴스 락으로.

### 6. 잠금 대상을 잘못 고르는 네 가지

**출력** (`Ex.java` — 33-f, 8스레드 × 5만 회, 각 10회, JDK 21.0.5)

```text
--- 잠금 대상을 잘못 고른 경우 (8스레드 x 50000, 기대 400000, 각 10회)
  고정된 private 객체 (정상)                      정답 10/10회  관측 400000 ~ 400000
  값이 바뀌는 필드에 락                             정답  0/10회  관측 346382 ~ 366357
  박싱된 Integer 에 락 (매번 새 객체)                정답  0/10회  관측 350248 ~ 369406
--- 왜 위험한가 — 잠금 대상의 정체
  Integer.valueOf(1) 둘이 같은 객체인가 : true   (캐시 범위 -128~127)
  Integer.valueOf(1000) 둘이 같은 객체인가 : false
  문자열 리터럴 "LOCK" 둘이 같은 객체인가  : true   (상수 풀 — JVM 전체가 공유)
  new String("LOCK") 과 리터럴          : false
  Boolean.TRUE 와 Boolean.valueOf(true)  : true
--- null 에 락을 걸면
  java.lang.NullPointerException: Cannot enter synchronized block because "<local10>" is null
--- 락을 잡은 채 필드를 바꾸면 나갈 때 무엇을 놓나
  블록 안에서 참조를 바꾼 뒤 holdsLock(처음 객체) : true
  블록 안에서 참조를 바꾼 뒤 holdsLock(새 객체)  : false
```

**왜 그런가**

- **`private final` 인 이유 둘** — `private` 이라야 남이 같은 열쇠를 잡을 수 없고,\
  `final` 이라야 참조가 안 바뀐다. 참조가 바뀌면 **0/10회**가 된다.
- **박싱된 `Integer` 가 위험한 이유 둘**\
  ① 캐시 범위(-128~127) 안이면 **JVM 전체가 같은 객체를 공유**한다 — 남의 코드와 열쇠가 겹친다.\
  ② 범위를 벗어나면 `valueOf` 가 **매번 새 객체**를 준다 — 이번엔 배제가 안 된다(`1000` 이 `false`).
- **문자열 리터럴**은 상수 풀에 있어 **JVM 전체가 하나**를 공유한다. `"LOCK"` 둘이 `true` 다.
- **`synchronized (null)` 은 런타임 에러**다. 컴파일은 통과한다.\
  `NullPointerException: Cannot enter synchronized block because "<local10>" is null`
- **나갈 때 풀리는 것은 진입할 때 잡은 객체**다. 실측에서 `holdsLock(처음 객체)` 가 `true` 다.\
  `javap` 의 `astore_1`(잡은 객체 저장) / `aload_1`(그것을 꺼내 `monitorexit`)가 그 장치다.
- ★ **`javac` 가 이것을 경고한다.**

```text
f/Ex.java:28: warning: [synchronization] attempt to synchronize on an instance of a value-based class
        race("박싱된 Integer 에 락 (매번 새 객체)", threads, per, () -> { synchronized (boxedLock) { shared++; boxedLock = boxedLock + 1; } });
                                                                ^
1 warning
```

### 7. 재진입

**출력** (`Ex.java` — 33-c, JDK 21.0.5)

```text
--- 재진입과 holdsLock
  블록 밖            : holdsLock = false
  블록 안            : holdsLock = true
  같은 락 다시 잡음   : holdsLock = true  (막히지 않는다 = 재진입)
  안쪽 블록만 나옴    : holdsLock = true  (바깥이 아직 잡고 있다)
  둘 다 나옴         : holdsLock = false
--- 재귀 synchronized 메서드는 자기 자신을 막지 않는다
  depth(5) = 5
```

**왜 그런가**

- **안쪽 블록에서 막히지 않는다.** 같은 스레드는 자기가 쥔 락에 다시 들어간다.
- **`depth(5)` 는 `5` 를 반환한다.** 재진입이 없다면 이 재귀는 **자기 자신과 교착**한다.
- **다른 스레드였다면 첫 줄에서 막힌다** — 그 스레드는 락을 안 쥐고 있으니까.
- `Thread.holdsLock(o)` 은 각각 `false → true → true → true → false` 다.\
  **계수는 알려 주지 않는다** — 안쪽 블록을 나와도 아직 `true` 인 것이 그 증거다.

```text
재진입 계수 (같은 스레드 기준)

  synchronized (o) {        <- 계수 1   holdsLock = true
      synchronized (o) {    <- 계수 2   holdsLock = true (막히지 않는다)
      }                     <- 계수 1   holdsLock = true
  }                         <- 계수 0   holdsLock = false (이때 비로소 풀린다)
```

### 8. `synchronized` 메서드와 블록은 컴파일 결과가 같은가

**출력** (`Ex.java` — 33-d, `javap -c -p`, JDK 21.0.5)

```text
  synchronized void mSync();
    Code:
       0: aload_0
       1: dup
       2: getfield      #7                  // Field n:I
       5: iconst_1
       6: iadd
       7: putfield      #7                  // Field n:I
      10: return

  void mBlock();
    Code:
       0: aload_0
       1: dup
       2: astore_1
       3: monitorenter
       4: aload_0
       5: dup
       6: getfield      #7                  // Field n:I
       9: iconst_1
      10: iadd
      11: putfield      #7                  // Field n:I
      14: aload_1
      15: monitorexit
      16: goto          24
      19: astore_2
      20: aload_1
      21: monitorexit
      22: aload_2
      23: athrow
      24: return
    Exception table:
       from    to  target type
           4    16    19   any
          19    22    19   any
```

**왜 그런가**

- **`synchronized` 메서드에는 `monitorenter` 가 없다.** 본문은 `n++` 그대로다.
- 대신 **메서드 플래그 `ACC_SYNCHRONIZED`(0x0020)** 로 표시된다. JVM 이 호출·반환 때 알아서 처리한다.

```text
  synchronized void mSync();
    flags: (0x0020) ACC_SYNCHRONIZED
  void mBlock();
    flags: (0x0000)
  static synchronized void sSync();
    flags: (0x0028) ACC_STATIC, ACC_SYNCHRONIZED
```

- **블록에는 `monitorexit` 이 두 개**다 — **정상 경로용(15번)과 예외 경로용(21번)**.\
  예외 테이블이 `4~16` 구간의 `any` 예외를 `19` 로 보낸다. **어떤 경로로 나가든 락이 풀린다.**
- **`volatile` 읽기의 바이트코드는 일반 읽기와 같다**(둘 다 `getfield`). 3번 답 참조.

### 9. `wait`/`notify` 를 잘못 부르면

**출력** (`Ex.java` — 33-e, JDK 21.0.5)

```text
--- 락을 안 잡고 wait() 를 부르면
  java.lang.IllegalMonitorStateException: current thread is not owner
  at java.base/java.lang.Object.wait0(Native Method)
--- 락을 안 잡고 notify() 를 부르면
  java.lang.IllegalMonitorStateException: current thread is not owner
--- 다른 객체의 락을 잡고 wait() 를 부르면
  java.lang.IllegalMonitorStateException: current thread is not owner
--- wait 는 락을 놓는다 (sleep 은 안 놓는다)
  wait 중인 락을 잡는 데 0 ms
  sleep 중인 락을 잡는 데 250 ms
```

**왜 그런가**

- **(A)와 (B) 둘 다 `IllegalMonitorStateException: current thread is not owner`** 다.\
  **다른 객체의 락을 쥐고 있어도 소용없다** — 그 객체의 락이어야 한다.
- **`wait` 는 락을 놓고 `sleep` 은 안 놓는다.**\
  관측 방법이 실측 그대로다 — 상대가 300ms 동안 `wait`/`sleep` 하는 사이에 같은 락을 잡아 보고 **걸린 시간을 잰다.**\
  `wait` 는 **0 ms**, `sleep` 은 **250 ms** 였다.
- **`while` 로 감싸야 하는 이유** — `wait` 는 **왜 깨어났는지 알려 주지 않는다.**\
  `notifyAll` 로 여럿이 함께 깨거나, 조건과 무관한 이유로 깰 수 있다.\
  깨어난 뒤 **조건을 다시 확인**해야 하므로 `if` 가 아니라 `while` 이다.

```text
wait 중                                    sleep 중

  synchronized (LOCK) {                     synchronized (LOCK) {
      LOCK.wait();   <- 락을 놓는다              Thread.sleep(300); <- 쥔 채로 잔다
  }                                         }
        |                                         |
        v                                         v
  남이 0 ms 만에 잡았다                       남이 250 ms 를 기다렸다
```

★ **버전 차이** — 스택 최상단 프레임이 **17 은 `Object.wait`, 21·25 는 `Object.wait0`** 이다(13번).

### 10. `InterruptedException` 을 삼키면

**출력** (`Ex.java` — 33-e, JDK 21.0.5)

```text
--- InterruptedException 을 삼키면 플래그가 지워진다
  잡은 직후 isInterrupted = false
  삼킨 뒤 isInterrupted   = false
  복구한 뒤 isInterrupted = true
```

**왜 그런가**

- **`catch` 에 들어온 직후 이미 `false`** 다. `InterruptedException` 을 던질 때 플래그가 지워진다.
- 아무것도 안 하면 **위쪽은 알 방법이 없다.** 인터럽트 요청이 조용히 사라진다.\
  그래서 `ExecutorService.shutdownNow()` 로 보낸 중단 신호가 무시된다([`../54-executorservice-and-future/`](../54-executorservice-and-future/)).
- **올바른 처리 둘**\
  ① 그대로 던진다 — `throws InterruptedException` 을 시그니처에 남긴다.\
  ② 잡아야 한다면 **`Thread.currentThread().interrupt()` 로 플래그를 복구**하고 빠져나온다.
- 예외를 삼켰을 때 무엇이 사라지는지는 [`../25-exceptions/`](../25-exceptions/) 가 정본이다.

### 11. 교착은 어떤 모습으로 나타나나

**출력** (`Ex.java` — 33-g, 각 20회 반복, JDK 21.0.5)

```text
--- 교착은 예외를 던지지 않는다. 밖에서 보는 방법
  두 스레드 상태 : BLOCKED / BLOCKED
  findDeadlockedThreads() = 2개
  deadlock-1 상태=BLOCKED
      기다리는 락 : java.lang.Object@b4c966a
      그 락 주인  : deadlock-2
  deadlock-2 상태=BLOCKED
      기다리는 락 : java.lang.Object@6f496d9f
      그 락 주인  : deadlock-1
  (JVM 은 교착을 스스로 풀지 않는다 — 두 스레드는 영원히 BLOCKED 다)
--- 락 순서를 뒤집으면 (독립된 락 쌍으로 20회, 각 1초 안에 끝나나)
  1초 안에 안 끝난 횟수 : 20/20
--- 두 스레드가 같은 순서로 잡으면 (20회)
  1초 안에 안 끝난 횟수 : 0/20
```

**왜 그런가**

- **20회 중 20회 멈췄다.** 이 문항은 **비결정적이 아니다** — 락 둘을 뒤집는 구조는 거의 확실히 걸린다.\
  (`sleep(20)` 으로 겹치는 창을 벌려 놓았기 때문이다.)
- **아무 예외도 던지지 않는다.** 로그도, 스택트레이스도 없다. **멈춰 있는 것이 증상의 전부다.**
- 두 스레드의 상태는 **`BLOCKED`** 다.
- 밖에서 보는 표준 수단은 **스레드 덤프**(`jstack`)와 **`ThreadMXBean.findDeadlockedThreads()`** 다.\
  `getLockName()`·`getLockOwnerName()` 이 **누가 무엇을 쥐고 누구를 기다리는지** 짝지어 준다.
- **순서를 맞추면 20/20 → 0/20** 이다. 고치는 법은 **락 순서 고정** 하나다.

```text
순서를 뒤집으면 (20/20 멈춤)               순서를 맞추면 (0/20 멈춤)

  t1: A -> B                                t1: A -> B
  t2: B -> A                                t2: A -> B
       |                                         |
       v                                         v
  서로 상대가 쥔 것을 기다린다                 뒤에 온 쪽이 A 에서 기다린다
  영원히 BLOCKED                             앞의 것이 끝나면 통째로 진행
```

### 12. `long` 쓰기는 찢어지는가

**출력** (`Ex.java` — 33-h, 각 10회 × 200ms, JDK 21.0.5)

```text
--- long 쓰기가 찢어지는가 (JLS 17.7: volatile 아닌 long/double 쓰기는 두 번에 나뉠 수 있다)
  plain long     읽기 28,993,390회 중 A도 B도 아닌 값 0회
  volatile long  읽기 24,788,720회 중 A도 B도 아닌 값 0회
  → 이 머신(x86-64)에서는 찢어진 값을 한 번도 못 봤다. 관측 실패는 보장이 아니다.
```

**왜 그런가**

- **JLS §17.7 은 `volatile` 아닌 64비트 값의 쓰기를 32비트 둘로 나누는 것을 허용한다.**\
  그러면 읽는 쪽이 **위 절반은 새 값, 아래 절반은 옛 값**인 값을 볼 수 있다.
- **이 머신에서는 2,899만 회 중 0회**였다. 64비트 CPU 에서는 사실상 안 나타난다.
- ★ **그 결과를 "안전하다"의 근거로 쓸 수 없다.** 명세가 허용한 동작이고 다른 플랫폼에서는 다를 수 있다.\
  **관찰은 관찰로, 보장은 명세로만 적는다.**
- **`volatile` 이 추가로 보장하는 것**은 바로 이 **쓰기·읽기의 비분할**이다.\
  그래도 **`++` 는 여전히 안전하지 않다** — 같은 프로그램에서 `volatile long++` 이 **0/10회 정답**이었다.

```text
--- volatile long 도 ++ 는 안전하지 않다 (8스레드 x 100000, 기대 800000, 10회)
  volatile long++  정답 0/10회  관측 260588 ~ 412227
```

### 13. 17 · 21 · 25 에서 무엇이 갈렸나

**출력** (`Ex.java` — 33-e, 세 JDK)

```text
===== 17.0.13-tem
--- 락을 안 잡고 wait() 를 부르면
  java.lang.IllegalMonitorStateException: current thread is not owner
  at java.base/java.lang.Object.wait(Native Method)
===== 25.0.1-tem
--- 락을 안 잡고 wait() 를 부르면
  java.lang.IllegalMonitorStateException: current thread is not owner
  at java.base/java.lang.Object.wait0(Native Method)
```

**출력** (`Ex.java` — 33-f, `javac` 경고, 세 JDK)

```text
===== 17.0.13-tem javac 경고
f/Ex.java:28: warning: [synchronization] attempt to synchronize on an instance of a value-based class
===== 25.0.1-tem javac 경고
f/Ex.java:28: warning: [identity] attempt to synchronize on an instance of a value-based class
```

**왜 그런가**

- **스택 최상단 프레임이 갈렸다** — 17 은 `Object.wait`, **21·25 는 `Object.wait0`**.\
  예외 이름과 메시지(`current thread is not owner`)는 셋 다 같았다.
- **`javac` 린트 이름이 갈렸다** — 17·21 은 `[synchronization]`, **25 는 `[identity]`**.\
  `-Xlint:synchronization` 을 CI 에 박아 뒀다면 25 에서 이름이 달라진다.
- **경쟁 실험의 정답 횟수는 세 버전에서 달랐다.** 예를 들어 8스레드 × 10만 회의 `int++` 이\
  17 에서 14/20, 21 에서 13~18/20, **25 에서 20/20** 이었다.\
  ★ **25 에서는 가장 센 조건이 한 번도 안 틀렸다** — 「안 터졌다」가 안전의 증거가 아닌 이유의 결정판이다.
- **세 버전에서 같았던 것도 "보장"으로 적으면 안 된다.**\
  가시성 5/5, 잠금 대상 패턴, 예외 메시지 문구 — 전부 **관찰**이다.\
  보장으로 적을 수 있는 것은 JLS·javadoc 에 문장이 있는 것뿐이다.

### 14. 이 코드를 어떻게 고칠 것인가

**(A) `volatile int requestCount; requestCount++`**

- **`AtomicInteger` 나 `LongAdder`** 로 바꾼다([`../55-atomics-and-concurrent-collections/`](../55-atomics-and-concurrent-collections/)).
- 근거: 3번 — `++` 는 세 명령이고 `volatile` 은 그것을 묶지 않는다. 실측 0/20회 정답.

**(B) `static` 맵을 `synchronized` 인스턴스 메서드로 지킨다**

- **`static synchronized` 로 바꾸거나**, 더 나은 답은 **필드 자체를 `ConcurrentHashMap` 으로** 바꾸는 것이다.
- 근거: 5번 — 인스턴스가 둘이면 열쇠가 둘이라 0/10회 정답.

**(C) `synchronized (this) { httpClient.send(request); }`**

- **락 밖으로 I/O 를 뺀다.** 락 안에서는 **메모리 상태만** 건드린다.
- 근거: 9번 — 락을 쥔 채 자면 남이 250 ms 를 기다린다. 네트워크는 그보다 훨씬 오래 걸린다.
- 가상 스레드에서는 **더 나쁘다** — 21 에서는 캐리어까지 붙잡는다([`../56-virtual-threads/`](../56-virtual-threads/)).

**(D) `public final Object lock = new Object();`**

- **`private final`** 로 바꾼다.
- 근거: 6번 — 공개된 열쇠는 남이 잠글 수 있다. 내 임계 구역이 남의 사정으로 막힌다.

**(E) `synchronized (Integer.valueOf(userId)) { ... }`**

- **키별 락이 필요하면 `ConcurrentHashMap<Long, Object>` 에 락 객체를 담아 `computeIfAbsent` 로 꺼낸다.**
- 근거: 6번 — 캐시 범위 안이면 JVM 전체와 열쇠가 겹치고, 밖이면 매번 다른 객체가 된다.\
  `javac` 도 이것을 경고한다.

**(F) `if (!ready) lock.wait();`**

- **`while (!ready) lock.wait();`** 로 바꾼다.
- 근거: 9번 — `wait` 는 깨어난 이유를 알려 주지 않는다. 깨어난 뒤 조건을 다시 봐야 한다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 반복 | 돌린 JDK |
|---|---|---|---|
| `Ex.java` (33-a) | 네 조건의 경쟁 분포(`int`·`volatile int`·`synchronized`), `-Xint` 대조 | 조건당 20회 × 명령 2회 | **17 · 21 · 25** (정답 횟수가 버전마다 다름 — 25 는 8×10만에서 20/20) |
| `Ex.java` (33-b) | 일반 플래그 대 `volatile` 플래그의 루프 종료, `-Xint` 대조 | 각 5회 | **17 · 21 · 25** (세 곳 모두 일반 0/5, `volatile` 5/5) |
| `Ex.java` (33-c) | 잠금 대상 6가지의 정답률, 재진입, `holdsLock`, 재귀 `synchronized` | 각 10회 | **17 · 21 · 25** (패턴 동일, 수치만 다름) |
| `Ex.java` (33-d) | `javap -c -p` 로 `synchronized` 메서드/블록/`volatile` 읽기, `javap -v` 의 플래그 | 1회 | 21 |
| `Ex.java` (33-e) | `IllegalMonitorStateException` 3경로, `wait`/`notify` 정상 경로, `wait` 대 `sleep` 의 락 보유, 인터럽트 플래그 | 1회 | **17 · 21 · 25** (`wait` → `wait0` 로 **갈림**) |
| `Ex.java` (33-f) | 락 객체 3종의 정답률, 값 기반 클래스·리터럴의 정체성, `null` 락, 블록 안 참조 교체 | 각 10회 | 21 (+ `javac` 경고는 **17 · 21 · 25** — 린트 이름이 **갈림**) |
| `Ex.java` (33-g) | 교착 검출(`ThreadMXBean`), 순서 뒤집기 대 순서 맞추기 | 각 20회 | 21 |
| `Ex.java` (33-h) | `long` 찢어짐 관측 시도(2,899만 회), `volatile long++` | 각 10회 | 21 |
| `src.zip` 열람 | `Thread.holdsLock` 의 `@since 1.4`, `Object.wait` 의 `@since` | — | 21 |

**측정 방법의 한계 (반드시 같이 읽을 것)**

- **JMH 가 아니다.** 스레드를 직접 띄워 반복한 것이다. 워밍업·DCE 통제가 없다.
- **머신 의존**이다 — 24코어 x86-64 Linux. 코어가 적으면 경쟁이 덜 드러난다.
- **실행마다 흔들린다** — 같은 명령 1회차와 2회차가 `18/20 → 13/20` 이었다.
- 이 문서의 정답률은 "**0 인가 아닌가**"의 근거이지 "**몇 %인가**"의 근거가 아니다.
- ★ **「안 터졌다」를 안전의 근거로 쓰지 마라.** 25 에서 가장 센 조건이 20/20 정답이었다.

**구현 의존 항목** (버전이 오르면 다시 돌려야 하는 것)

- 일반 `int++` 의 정답률 — **JIT 최적화에 좌우된다. 버전마다 달랐다.**
- `IllegalMonitorStateException` 의 스택 최상단 프레임 — **17 과 21·25 가 달랐다.**
- 값 기반 클래스 락 경고의 린트 이름 — **17·21 과 25 가 달랐다.**
- 일반 플래그가 안 멈추는 것 — `-Xint` 에서는 멈춘다. **최적화 수준에 좌우된다.**
- `long` 쓰기가 안 찢어지는 것 — **x86-64 관측일 뿐 보장이 아니다.**
- `synchronized` 메서드/블록의 바이트코드 형태 — **21 에서만 찍었다.** 17·25 는 안 돌려 봄.
- **Java 8 이하의 동작은 안 돌려 봄** — 이 머신에 8이 없다.
