# java/syntax/33 — `synchronized`·`volatile`: 문법과 그 보장이 끝나는 자리 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — 없다. 스레드가 무엇인지는 [`../../../../process-thread/`](../../../../process-thread/) 가 정본이다.
> ⚠️ **이 주제의 답은 비결정적이다.** 수치를 묻는 문항은 **"항상 맞나 / 가끔 맞나 / 항상 틀리나"**만 맞히면 된다.
> 이 문서의 관측값은 **24코어 머신에서 N회 반복한 분포**이고, 다른 머신·다른 실행에서 그대로 재현되지 않는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 동기화 없이 카운터를 올리면 몇 번이나 맞나 (예측)

```java
static int plain = 0;
// 스레드 N개가 각자 M회: plain++
```

다음 네 조건을 **20회씩** 돌렸을 때 "정답이 나온 횟수"를 예측하라.

```text
(A) 스레드 2 x 100회   (기대 200)
(B) 스레드 2 x 1000회  (기대 2000)
(C) 스레드 2 x 100000회 (기대 200000)
(D) 스레드 8 x 100000회 (기대 800000)
```

- (A)는 20회 중 몇 회 정답인가?
- (D)는 20회 중 몇 회 정답인가 — 0회인가, 절반 이상인가?
- 틀릴 때 값은 기대값보다 큰가 작은가?
- 이 실험을 한 번만 돌려 보고 "안전하다"고 판단하면 무엇을 놓치는가?

### 2. `volatile` 을 붙이면 더 자주 맞을까 (예측)

같은 실험을 `volatile int` 로 바꿔 돌렸다.

- (D) 조건에서 `volatile int++` 의 정답 횟수는 일반 `int++` 보다 많은가 적은가?
- 그 결과가 "`volatile` 이 더 위험하다"는 뜻인가?
- 같은 프로그램을 `-Xint`(JIT 끔)로 돌리면 일반 `int++` 의 정답 횟수는 어떻게 되는가?
- 그래서 "관측된 정답률"은 무엇을 재고 있는가?

### 3. `n++` 은 바이트코드로 몇 개의 명령인가 (예측)

```java
synchronized void mSync() { n++; }
```

- `javap -c` 로 본 `n++` 은 어떤 명령들로 나오는가?
- 그중 "읽기"와 "쓰기"는 각각 어느 명령인가?
- `volatile` 을 붙이면 이 명령 개수가 줄어드는가?
- 이 사실에서 "`volatile` 로는 카운터를 못 지킨다"가 왜 따라 나오는가?

### 4. 플래그로 루프를 멈출 수 있나 (예측)

```java
static boolean running = true;              // (A)
static volatile boolean running2 = true;    // (B)
// 읽기 스레드: while (running) { }   / main: 200ms 뒤 running = false
```

- (A)를 5회 돌리면 몇 회나 멈추는가?
- (B)는 몇 회 멈추는가?
- `-Xint` 로 돌리면 (A)는 어떻게 되는가?
- 이 셋을 합치면 `volatile` 이 **하는 일**을 한 문장으로 무엇이라 할 수 있는가?

### 5. `synchronized` 를 붙였는데 왜 틀리나 (예측)

공유 `static` 필드를 8스레드가 5만 번씩 올린다. 각 경우 10회 중 정답 횟수를 예측하라.

```text
(A) 인스턴스 하나 + synchronized 인스턴스 메서드
(B) 인스턴스 둘   + synchronized 인스턴스 메서드
(C) 인스턴스 둘   + static synchronized
(D) 인스턴스 둘   + synchronized (Counter.class) 블록
(E) 인스턴스 하나인데 절반은 인스턴스 메서드, 절반은 static synchronized
```

- 다섯 중 10/10회 정답인 것은 어느 것인가?
- (E)가 틀리는 이유를 한 줄로 설명하라.
- 네 형태(`synchronized` 메서드 / `static synchronized` / `synchronized(this)` / `synchronized(X.class)`)의 **잠금 대상**을 각각 적어라.

### 6. 잠금 대상을 잘못 고르는 네 가지 (경계)

- 락 객체를 `private final` 로 두라고 하는 이유는?
- `synchronized (boxedInteger)` 가 위험한 이유 **둘**은 무엇인가?
- 문자열 리터럴 `"LOCK"` 을 락으로 쓰면 무엇이 문제인가?
- `synchronized (null)` 은 컴파일 에러인가 런타임 에러인가 — 메시지는?
- 블록 안에서 락 변수의 참조를 바꾸면, 나갈 때 풀리는 것은 어느 객체인가?

### 7. 재진입 (예측)

```java
Object o = new Object();
synchronized (o) {
    synchronized (o) { /* 여기까지 오나? */ }
}
synchronized int depth(int n) { return n == 0 ? 0 : 1 + depth(n - 1); }
```

- 안쪽 블록에서 막히는가?
- `depth(5)` 는 무엇을 반환하는가, 아니면 멈추는가?
- 다른 스레드였다면 결과가 어떻게 달랐겠는가?
- `Thread.holdsLock(o)` 은 각 지점에서 무엇을 반환하는가?

### 8. `synchronized` 메서드와 블록은 컴파일 결과가 같은가 (예측)

- `synchronized` 메서드의 바이트코드에 `monitorenter` 가 있는가?
- 없다면 무엇으로 표시되는가?
- `synchronized` 블록에는 `monitorexit` 이 몇 개 나오는가 — 그리고 왜 그 개수인가?
- `volatile int` 를 읽는 바이트코드는 일반 `int` 를 읽는 것과 다른가?

### 9. `wait`/`notify` 를 잘못 부르면 (예측)

```java
static final Object LOCK = new Object();
LOCK.wait(10);                                  // (A) 락 없이
synchronized (other) { LOCK.wait(10); }         // (B) 다른 객체의 락을 쥐고
```

- (A)와 (B)는 각각 무엇을 던지는가 — 예외 이름과 메시지는?
- `wait` 는 락을 놓는가? `Thread.sleep` 은?
- 그 차이를 "남이 그 락을 잡는 데 걸린 시간"으로 어떻게 관측할 수 있는가?
- `wait` 를 `if` 가 아니라 `while` 로 감싸야 하는 이유는?

### 10. `InterruptedException` 을 삼키면 (예측)

```java
try { Thread.sleep(10_000); } catch (InterruptedException e) { }
```

- `catch` 에 들어온 **직후** `Thread.currentThread().isInterrupted()` 는 무엇인가?
- 아무것도 안 하고 넘어가면 위쪽 코드는 인터럽트가 있었다는 것을 어떻게 아는가?
- 올바른 처리 두 가지는 무엇인가?

### 11. 교착은 어떤 모습으로 나타나나 (예측)

```java
t1: synchronized (A) { sleep(20); synchronized (B) { } }
t2: synchronized (B) { sleep(20); synchronized (A) { } }
```

- 이 구조를 20회 돌리면 몇 회나 멈추는가?
- 멈췄을 때 어떤 예외가 던져지는가?
- 두 스레드의 `getState()` 는 무엇인가?
- 밖에서 이것을 확인하는 표준 수단은 무엇인가?
- `t2` 를 `synchronized (A) { ... synchronized (B) }` 로 바꾸면 20회 중 몇 회 멈추는가?

### 12. `long` 쓰기는 찢어지는가 (경계)

두 스레드가 `long` 필드에 `0x0000...0` 과 `0xFFFF...F` 를 번갈아 쓰고, 한 스레드가 읽는다.

- JLS 는 이 상황에서 무엇을 허용하는가?
- 이 머신에서 2,899만 회를 읽었을 때 "A도 B도 아닌 값"이 몇 번 나왔는가?
- 그 결과를 "안전하다"의 근거로 쓸 수 있는가?
- `volatile` 을 붙이면 무엇이 추가로 보장되는가?

### 13. 17 · 21 · 25 에서 무엇이 갈렸나 (경계)

- `IllegalMonitorStateException` 의 **스택 최상단 프레임**이 버전에 따라 달랐는가?
- 값 기반 클래스에 락을 걸 때 나오는 **`javac` 경고의 린트 이름**은 세 버전에서 같았는가?
- 경쟁 실험의 정답 횟수는 세 버전에서 같았는가?
- 세 버전에서 같았던 항목들은 "보장"이라고 적어도 되는가?

### 14. 이 코드를 어떻게 고칠 것인가 (연결)

각각 무엇으로 바꿀지 한 줄로 답하라.

```text
(A) volatile int requestCount;  ... requestCount++;
(B) static Map<String,Integer> CACHE; synchronized void put(..) { CACHE.put(..); }   // 인스턴스가 여럿이다
(C) synchronized (this) { httpClient.send(request); }                                 // 200ms 걸린다
(D) public final Object lock = new Object();
(E) synchronized (Integer.valueOf(userId)) { ... }
(F) if (!ready) lock.wait();
```

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
