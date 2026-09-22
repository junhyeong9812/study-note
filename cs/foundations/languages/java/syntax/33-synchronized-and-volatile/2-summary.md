# java/syntax/33 — `synchronized`·`volatile`: 문법과 그 보장이 끝나는 자리 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §8.4.3.6 `synchronized` 메서드](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) · [§8.3.1.4 `volatile` 필드](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) · [§14.19 `synchronized` 문](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html) · [§17.7 `double`·`long` 의 비원자적 취급](https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html) · [`java.lang.Object#wait` API 문서](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Object.html) · 이 머신의 `javac`·`javap` 가 실제로 낸 출력.
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 프로그램 `(33-a)` `(33-b)` `(33-c)` `(33-e)` 는 **17.0.13 · 21.0.5 · 25.0.1** 세 JDK 에서 각각 돌렸다 — **세 곳에서 갈린 것이 둘 있다**(아래 「구현 세부사항 대 언어 보장」).
> ⚠️ **측정 조건 — 이 주제의 수치는 전부 비결정적이다.**\
> 도구: **JMH 가 아니다.** 스레드를 직접 띄워 같은 실험을 **N회 반복**하고 「정답이 나온 횟수 / N」과 「관측된 최솟값\~최댓값」으로 적는다.\
> 머신: **CPU 24코어**(`availableProcessors` = 24), Linux x86-64.\
> 반복: 경쟁 실험은 **각 20회 또는 10회**, 가시성 실험은 **5회**, 교착 실험은 **20회**.\
> 흔들림: 같은 프로그램을 두 번 돌리면 「정답 횟수」가 **18/20 → 13/20** 처럼 바뀐다. **자릿수와 방향만 읽는다.**\
> ★ **「안 터졌다」는 「안전하다」가 아니다.** 경쟁 조건은 **안 터지는 것이 기본값**이고, 터뜨리려면 스레드 수와 반복 수를 올려야 한다.\
> 이 문서가 그 사실 자체를 실측으로 보인다 — JDK 25 에서 8스레드 × 10만 회 `int++` 이 **20/20회 전부 정답**이 나왔다.
> **버전** — `synchronized`·`volatile` 은 **키워드**라 `src.zip` 에 `@since` 가 없다. JLS §3.9 의 키워드 목록에 Java 1.0 부터 들어 있고, 이 문서는 그 사실을 **실행으로 확인하지 않았다**(17 미만 JDK 가 이 머신에 없다).\
> `Thread.holdsLock` 은 `src.zip` 에서 **`@since 1.4`** 를 직접 읽었다.\
> **`Object.wait`·`notify`·`notifyAll` 에는 `@since` 태그가 아예 없다**(21 의 `Object.java` 를 직접 확인했다) — Java 1.0 부터 있었기 때문이다.
> **범위** — **메모리 모델(happens-before)·재배치·JIT·GC 는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §4\~9 가 정본이다.**\
> 그쪽은 **「동시성이 맞다」를 무엇으로 정의하나**까지, 여기는 「**그 정의를 만족시키려면 코드를 어떻게 쓰나**」부터다.\
> OS 스레드·스케줄링은 [`../../../../process-thread/`](../../../../process-thread/) 가 정본이다 — 그쪽은 **스레드가 무엇인가**까지, 여기는 **자바 키워드 둘의 문법과 사용 규칙**까지.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 JLS·javadoc 으로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**`synchronized` 는 "이 방에는 한 번에 한 사람"이고, `volatile` 은 "칠판에 바로 쓰고 바로 읽어라"다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 방 | 임계 구역 — `synchronized` 블록·메서드의 본문 |
| **방 열쇠** | **모니터(monitor) — 잠금 대상 객체** |
| 열쇠를 쥔 사람 | 락을 잡은 스레드 |
| 열쇠가 **두 개**인 방 | 잠금 대상을 둘로 나눈 것 — **배제가 안 된다** |
| 같은 사람이 방 안에서 또 들어감 | **재진입(reentrancy)** — 허용된다 |
| 칠판 | `volatile` 필드 |
| 각자 손에 든 메모지 | 일반 필드 — 다른 사람 메모지는 안 보인다 |
| 칠판에 적힌 숫자를 **보고 지우고 다시 적기** | `count++` — **세 동작이라 칠판으로도 못 막는다** |

- 열쇠가 **같아야** 배제가 된다.\
  방은 하나인데 열쇠를 두 개 만들면 두 사람이 동시에 들어온다.\
  실측에서 인스턴스를 둘로 나눠 `synchronized` 메서드를 부른 순간 **10회 전부 틀린 값**이 나왔다.
- 칠판은 **보이는 것**만 보장한다.\
  "보고 → 지우고 → 다시 적기"는 여전히 세 동작이라 그 사이에 남이 끼어든다.
- 그리고 **안 막아도 대개는 맞는 값이 나온다.**\
  그것이 이 주제가 위험한 이유다 — 테스트가 통과한다.

```text
열쇠가 하나 (인스턴스 하나)                  열쇠가 둘 (인스턴스 둘)

  +---------------------+                  +---------------------+
  | 방: shared++        |                  | 방: shared++        |
  |  열쇠 A 를 쥔 1명만 |                  |  열쇠 A 로 1명      |
  +---------------------+                  |  열쇠 B 로 또 1명   |
          |                                +---------------------+
          v                                          |
  10회 전부 400000 (정답)                            v
                                           10회 전부 틀림 (350993~379316)
```

**똑같은 구조로** 자바가 이렇게 동작한다: 방 = 임계 구역, 열쇠 = 모니터 객체.\
`synchronized` 인스턴스 메서드의 열쇠는 `this` 고, `static synchronized` 의 열쇠는 `그 클래스의 Class 객체`다.

실무에서 이게 사고를 내는 자리는 **"`synchronized` 를 붙였는데도 값이 틀린다"** 이다.\
붙이긴 붙였는데 **서로 다른 객체에 붙인 것**이다.

> **모니터(monitor)** — 자바의 모든 객체가 하나씩 갖고 있는 "열쇠".\
> 예: `synchronized (lock) { ... }` 는 `lock` 이라는 **객체 하나의** 열쇠를 잡는 것이지, 그 안의 코드를 잠그는 게 아니다.

> **임계 구역(critical section)** — 한 번에 한 스레드만 들어가야 하는 코드 구간.\
> 예: `잔액 = 잔액 - 출금액` 처럼 읽고 고쳐 쓰는 세 단계가 통째로 한 덩어리여야 하는 곳.

> **경쟁 조건(race condition)** — 두 스레드가 같은 데이터를 동시에 건드려 결과가 실행 순서에 좌우되는 것.\
> 예: 둘이 동시에 `count` 를 읽어 둘 다 `5` 를 보고 둘 다 `6` 을 쓰면, 두 번 올렸는데 1 만 올라간다.

> **가시성(visibility)** — 한 스레드가 쓴 값을 다른 스레드가 **볼 수 있는가**의 문제.\
> 예: `stop = true` 로 바꿨는데 상대 스레드의 `while (!stop)` 이 영원히 안 멈추는 일이 실제로 일어난다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 네 질문을 둔다.

1. 동기화를 **안 하면** 정확히 무슨 일이 나나 — 그리고 왜 그 일이 **테스트에서 안 잡히나**.
2. `synchronized` 의 **잠금 대상**은 무엇이며, 어떻게 하면 "붙였는데 안 막히는" 상태가 되나.
3. `volatile` 이 **보장하는 것**과 **보장하지 않는 것**의 경계는 어디인가.
4. 잘못 쓰면 어떤 **에러 메시지**가 나오고, 어떤 경우엔 **아무 메시지도 안 나오나**.

## 동작 방식

### (1) 동기화를 안 하면 무슨 일이 나나 — 한 번이 아니라 분포로 본다

**언제 쓰나** — 공유 변수를 여러 스레드가 고칠 때. 이 주제의 출발점이다.

동시성 실험은 **한 번 돌린 결과를 「이렇게 된다」로 적을 수 없다.**\
같은 프로그램이 돌 때마다 다른 값을 낸다. 그래서 **N회 반복해 분포**로 적는다.

**실행 결과** (`Ex.java` — 33-a, 24코어, 각 조건 20회 반복, JDK 21.0.5, **같은 명령을 연달아 2회**)

```text
===== 실행 1
--- 스레드 2 x 100회 (기대 200) / 각 20회 반복
  int++            정답 20/20회   관측 200 ~ 200
  volatile int++   정답 20/20회   관측 200 ~ 200
  synchronized ++  정답 20/20회
--- 스레드 2 x 1000회 (기대 2000) / 각 20회 반복
  int++            정답 20/20회   관측 2000 ~ 2000
  volatile int++   정답 18/20회   관측 1960 ~ 2000
  synchronized ++  정답 20/20회
--- 스레드 2 x 100000회 (기대 200000) / 각 20회 반복
  int++            정답 18/20회   관측 105502 ~ 200000
  volatile int++   정답  0/20회   관측 128996 ~ 185124
  synchronized ++  정답 20/20회
--- 스레드 8 x 100000회 (기대 800000) / 각 20회 반복
  int++            정답 18/20회   관측 701456 ~ 800000
  volatile int++   정답  0/20회   관측 211563 ~ 311445
  synchronized ++  정답 20/20회
===== 실행 2
--- 스레드 2 x 100회 (기대 200) / 각 20회 반복
  int++            정답 20/20회   관측 200 ~ 200
  volatile int++   정답 20/20회   관측 200 ~ 200
  synchronized ++  정답 20/20회
--- 스레드 2 x 1000회 (기대 2000) / 각 20회 반복
  int++            정답 19/20회   관측 1300 ~ 2000
  volatile int++   정답 17/20회   관측 1938 ~ 2000
  synchronized ++  정답 20/20회
--- 스레드 2 x 100000회 (기대 200000) / 각 20회 반복
  int++            정답 15/20회   관측 100017 ~ 200000
  volatile int++   정답  0/20회   관측 131405 ~ 193338
  synchronized ++  정답 20/20회
--- 스레드 8 x 100000회 (기대 800000) / 각 20회 반복
  int++            정답 13/20회   관측 284119 ~ 800000
  volatile int++   정답  0/20회   관측 251529 ~ 418672
  synchronized ++  정답 20/20회
```

```text
작은 실험 (2스레드 x 100회)                큰 실험 (8스레드 x 10만 회)

  +----------------------+                 +----------------------+
  | 20회 돌려 20회 정답   |                 | 20회 돌려 13~18회 정답|
  | 관측 200 ~ 200       |                 | 관측 284119 ~ 800000 |
  +----------------------+                 +----------------------+
   -> "동기화 없어도 되네"                    -> 절반 이상이 여전히 "정답"
      테스트가 통과한다                          그래서 더 안 잡힌다
```

그림 해설 (한 단계씩):

- **작은 실험은 20회 전부 정답이다.** 스레드 둘이 100번씩 올리는 정도로는 **겹칠 틈이 없다.**\
  여기서 "동기화 없어도 되는구나"라고 판단하면 그대로 운영에 나간다.
- **크게 키워도 13\~18/20회는 여전히 정답**이다. 실패가 **소수파**다.
- **실패할 때는 크게 실패한다** — 80만이 28만이 된다. 조금 틀리는 게 아니다.
- 그리고 **같은 명령을 두 번 돌리면 정답 횟수가 18 → 13 으로 바뀐다.**\
  그래서 이 표의 값은 "**몇 회"가 아니라 "0 인가 0 이 아닌가**"로만 읽는다.
- `synchronized` 만 **모든 조건에서 20/20** 이다.

비용 — 이 실험이 말하는 것은 하나다. **「테스트가 통과했다」는 「경쟁이 없다」의 증거가 아니다.**

#### 그런데 `int++` 이 `volatile int++` 보다 더 자주 맞았다

위 표에서 이상한 것이 있다. **일반 `int++` 이 18/20 인데 `volatile int++` 은 0/20 이다.**\
안전 장치를 붙였더니 **더 자주 틀린다.**

원인을 확인하려고 같은 프로그램을 **JIT 를 끄고**(`-Xint`) 다시 돌렸다.

**실행 결과** (`Ex.java` — 33-a, `-Xint`, JDK 21.0.5)

```text
--- 스레드 2 x 100000회 (기대 200000) / 각 20회 반복
  int++            정답  0/20회   관측 129413 ~ 169050
  volatile int++   정답  0/20회   관측 138905 ~ 171839
  synchronized ++  정답 20/20회
--- 스레드 8 x 100000회 (기대 800000) / 각 20회 반복
  int++            정답  0/20회   관측 153910 ~ 304667
  volatile int++   정답  0/20회   관측 260404 ~ 358424
  synchronized ++  정답 20/20회
```

```text
JIT 켜짐 (기본)                            JIT 꺼짐 (-Xint)

  int++          18/20 정답               int++          0/20 정답
  volatile int++  0/20 정답               volatile int++ 0/20 정답
        |                                        |
        v                                        v
  "일반 필드라서 안전하다"가 아니라        같은 코드가 항상 틀린다
  최적화가 경쟁을 감춘 것이다
```

- **`-Xint` 에서는 일반 `int++` 도 0/20** 이다. 코드는 그대로인데 결과가 뒤집혔다.
- 즉 기본 모드의 18/20 은 **코드가 안전해서가 아니라 최적화의 부작용**이다.
- **`volatile` 을 붙이면 그 최적화가 막혀** 경쟁이 그대로 드러난다.\
  「`volatile` 을 붙였더니 더 틀린다」가 아니라 「**`volatile` 이 숨어 있던 것을 보이게 했다**」이다.
- **JIT 가 필드 접근에 무엇을 하는지**는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §4\~5 가 정본이다.\
  여기서 쓸 결론은 하나다 — **관측되는 정답률은 코드의 안전성과 다른 것을 재고 있다.**

비용 — 없다. **이 실험은 "안 터졌다"를 근거로 쓰면 안 되는 이유의 전부다.**

### (2) `int++` 은 한 동작이 아니다 — 컴파일러가 한 일을 본다

**언제 쓰나** — "한 줄인데 왜 안 원자적이냐"가 안 믿길 때.

도식을 그리는 것보다 `javap -c` 가 낫다. **지어낼 수 없고 독자가 자기 머신에서 재현한다.**

**실행 결과** (`Ex.java` — 33-d, `javap -c -p`, JDK 21.0.5)

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

```text
n++ 한 줄이 실제로 하는 일

   getfield  n   ->  스택에 현재 값을 올린다      <- (A) 읽기
   iconst_1
   iadd          ->  1 을 더한다                 <- (B) 더하기
   putfield  n   ->  결과를 필드에 쓴다           <- (C) 쓰기

   A 와 C 사이에 다른 스레드가 A·C 를 통째로 끼워 넣을 수 있다
       -> 둘이 같은 값을 읽고 둘이 같은 값을 쓴다 -> 한 번만 올라간다
```

그림 해설 (한 단계씩):

- **`getfield` → `iadd` → `putfield`** 세 명령이다. 소스는 한 줄이지만 기계는 셋으로 나눠 한다.
- `volatile` 은 이 **세 명령을 하나로 묶어 주지 않는다.** 각 명령이 최신 값을 보게 할 뿐이다.
- 그래서 (1) 의 표에서 `volatile int++` 이 **0/20** 이 나온다.
- ★ **외울 것은 명령 이름이 아니라 「읽고-고치고-쓰기가 세 단계다」라는 성질**이다.

비용 — 세 단계를 하나로 묶으려면 **락**(`synchronized`) 이나 **CAS**([`../55-atomics-and-concurrent-collections/`](../55-atomics-and-concurrent-collections/))가 필요하다.

### (3) `volatile` 이 보장하는 것 — 쓴 값이 보인다

**언제 쓰나** — 플래그 하나로 다른 스레드를 멈추려 할 때. **`volatile` 이 값을 하는 거의 유일한 자리다.**

**실행 결과** (`Ex.java` — 33-b, 각 5회, 플래그를 바꾸고 2초 기다린다, JDK 21.0.5)

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
(데몬 스레드라 JVM 은 끝난다)
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
--- volatile boolean 플래그 (각 2초 기다림, 5회)
  0: 멈췄나 = true
  ... (5회 모두 true)
```

```text
일반 필드                                   volatile 필드

  읽기 스레드                                 읽기 스레드
    while (plainFlag) { ... }                 while (volFlag) { ... }
          ^                                         ^
          |                                         |
  main 이 plainFlag = false               main 이 volFlag = false
          |                                         |
          v                                         v
    5/5회 안 멈췄다 (2초를 다 기다림)          5/5회 즉시 멈췄다
```

그림 해설 (한 단계씩):

- **일반 `boolean` 플래그는 5회 전부 안 멈췄다.** 값을 바꿨는데 상대가 못 본다.
- **`volatile` 을 붙이면 5회 전부 멈춘다.** 코드의 다른 부분은 한 글자도 안 바뀌었다.
- `-Xint` 로 돌리면 **일반 플래그도 5회 전부 멈춘다** — 회전 수까지 찍힌다(4천만 회 돌다 멈췄다).\
  이것이 (1) 에서 본 것과 **같은 현상의 반대 방향**이다. 최적화가 켜지면 값이 안 보이고, 꺼지면 보인다.
- 이 실험은 **17 · 21 · 25 세 JDK 에서 같았다**(일반 0/5, `volatile` 5/5). **관찰이지 보장이 아니다.**

비용 — `volatile` 읽기·쓰기는 일반 필드보다 비싸다. **`volatile` 이 하는 일은 "보이게 하는 것"까지다.**\
보장의 정의(happens-before) 자체는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §9 가 정본이다.

### (4) `volatile` 이 보장하지 않는 것 — 원자성

**언제 쓰나** — "카운터에 `volatile` 붙이면 되는 거 아냐?" 를 판정할 때.

**실행 결과** (`Ex.java` — 33-h, 8스레드 × 10만 회, 10회 반복, JDK 21.0.5)

```text
--- volatile long 도 ++ 는 안전하지 않다 (8스레드 x 100000, 기대 800000, 10회)
  volatile long++  정답 0/10회  관측 260588 ~ 412227
```

- `int` 든 `long` 든 같다. **`volatile` + `++` 는 10회 중 0회 정답**이다.
- (2) 에서 본 세 단계 때문이다.

그리고 `volatile` 이 **추가로** 보장하는 것이 하나 있다 — **`long`·`double` 의 쓰기가 쪼개지지 않는 것**(JLS §17.7).\
이것을 관측하려고 시도했다.

**실행 결과** (`Ex.java` — 33-h, 두 스레드가 `0x0000...0` 과 `0xFFFF...F` 를 번갈아 쓰고 한 스레드가 읽는다, 각 10회 × 200ms)

```text
--- long 쓰기가 찢어지는가 (JLS 17.7: volatile 아닌 long/double 쓰기는 두 번에 나뉠 수 있다)
  plain long     읽기 28,993,390회 중 A도 B도 아닌 값 0회
  volatile long  읽기 24,788,720회 중 A도 B도 아닌 값 0회
  → 이 머신(x86-64)에서는 찢어진 값을 한 번도 못 봤다. 관측 실패는 보장이 아니다.
```

- **2,899만 번 읽어 한 번도 못 봤다.** 그래도 **"안전하다"고 쓸 수 없다.**
- JLS 가 허용한 동작이고, 이 머신이 64비트라 안 나타난 것뿐이다.
- ★ **관찰은 관찰로 적고, 보장은 명세로만 적는다.** 여기는 그 규칙이 정확히 적용되는 자리다.

비용 — `volatile` 로 얻는 것은 **가시성 + `long`/`double` 쓰기의 비분할**까지다. **원자성은 없다.**

### (5) 잠금 대상 — 열쇠가 같아야 막힌다

**언제 쓰나** — `synchronized` 를 어디에 붙일지 정할 때. **이 주제의 대표 사고다.**

**실행 결과** (`Ex.java` — 33-c, 공유 `static` 필드를 8스레드 × 5만 회, 각 10회 반복, JDK 21.0.5)

```text
--- 공유 static 필드를 8스레드 x 50000회 증가 (기대 400000) / 각 10회 반복
  인스턴스 하나 + synchronized 인스턴스 메서드              정답 10/10회  관측 400000 ~ 400000
  인스턴스 둘 + synchronized 인스턴스 메서드               정답  0/10회  관측 369377 ~ 379316
  인스턴스 둘 + synchronized(this) 블록               정답  0/10회  관측 369419 ~ 378437
  인스턴스 둘 + static synchronized                 정답 10/10회  관측 400000 ~ 400000
  인스턴스 둘 + synchronized(Counter.class) 블록      정답 10/10회  관측 400000 ~ 400000
  인스턴스 하나인데 절반은 static synchronized            정답  0/10회  관측 369019 ~ 380883
```

```text
잠금 대상이 무엇인가

  synchronized void m()            ->  this            (인스턴스마다 다른 열쇠)
  static synchronized void m()     ->  Counter.class   (클래스당 하나)
  synchronized (this) { }          ->  this            (위와 같다)
  synchronized (Counter.class) { } ->  Counter.class   (위와 같다)
  synchronized (LOCK) { }          ->  LOCK 이 가리키는 객체
```

그림 해설 (한 단계씩):

- **`synchronized` 인스턴스 메서드의 열쇠는 `this` 다.** 인스턴스가 둘이면 열쇠가 둘이다.
- 그래서 **공유 `static` 필드를 인스턴스 메서드로 지키면 안 된다** — 0/10회.
- **`static synchronized` 는 클래스당 하나**라 10/10회 정답이다.
- 마지막 줄이 가장 조용한 사고다 — **한쪽은 인스턴스 락, 한쪽은 클래스 락**을 썼다.\
  둘 다 `synchronized` 가 붙어 있는데 **서로를 배제하지 않는다.**
- 이 표는 **17 · 21 · 25 에서 정답/오답 패턴이 같았다**(관측된 수치만 다르다).

비용 — `synchronized` 는 "코드를 잠그는 것"이 아니라 "**객체를 잠그는 것**"이다.\
**지켜야 할 데이터마다 그 데이터를 소유한 객체 하나를 정하고, 모든 접근이 그 하나를 통과하게 한다.**

### (6) 재진입 — 같은 스레드는 자기 락에 다시 들어간다

**언제 쓰나** — `synchronized` 메서드가 다른 `synchronized` 메서드를 부를 때.

**실행 결과** (`Ex.java` — 33-c, JDK 21.0.5)

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

```text
재진입 계수 (같은 스레드 기준)

  synchronized (o) {        <- 계수 1
      synchronized (o) {    <- 계수 2 (막히지 않는다)
      }                     <- 계수 1
  }                         <- 계수 0, 이때 비로소 풀린다
```

- **같은 스레드**는 자기가 쥔 락에 몇 번이든 다시 들어간다. 그래서 `synchronized` 재귀 메서드가 돈다.
- **다른 스레드**였다면 첫 줄에서 막힌다.
- `Thread.holdsLock(o)` 은 **지금 이 스레드가 그 락을 쥐고 있나**만 답한다. 계수는 안 알려 준다.

비용 — 재진입이 없다면 `synchronized` 메서드끼리 호출만 해도 자기 자신과 교착한다. **재진입은 안전장치다.**

### (7) `synchronized` 의 두 형태 — 바이트코드가 다르다

**언제 쓰나** — 메서드 전체에 걸지, 블록에만 걸지 고를 때.

**실행 결과** (`Ex.java` — 33-d, `javap -c -p`, JDK 21.0.5)

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

**실행 결과** (`Ex.java` — 33-d, `javap -v -p` 의 플래그 줄만, JDK 21.0.5)

```text
  int n;
    descriptor: I
    flags: (0x0000)
  volatile int v;
    descriptor: I
    flags: (0x0040) ACC_VOLATILE
  synchronized void mSync();
    descriptor: ()V
    flags: (0x0020) ACC_SYNCHRONIZED
  void mBlock();
    descriptor: ()V
    flags: (0x0000)
  static synchronized void sSync();
    descriptor: ()V
    flags: (0x0028) ACC_STATIC, ACC_SYNCHRONIZED
```

```text
synchronized 메서드                        synchronized 블록

  본문에 monitorenter 가 없다               monitorenter / monitorexit 가 보인다
  대신 메서드에 ACC_SYNCHRONIZED 플래그       예외 테이블이 하나 더 붙는다
       |                                          |
       v                                          v
  JVM 이 호출·반환 때 알아서 잠그고 푼다        컴파일러가 astore_1 로 잠금 대상을
                                            보관해 두고, 어떤 경로로 나가든 그걸 푼다
```

그림 해설 (한 단계씩):

- **`synchronized` 메서드의 바이트코드에는 `monitorenter` 가 없다.** 메서드 플래그 `ACC_SYNCHRONIZED` 뿐이다.
- **블록은 `monitorenter`/`monitorexit` 명령**으로 나온다. 그리고 **`monitorexit` 이 두 개**다 — 정상 경로용과 예외 경로용.
- `astore_1` 로 **진입 시점의 객체를 지역 변수에 저장**해 둔다. 그래서 블록 안에서 그 필드를 다른 객체로 바꿔도 **나갈 때 푸는 것은 처음 잡은 객체**다((아래 「어디서 틀리나」 7번).
- **`volatile` 읽기에는 전용 명령이 없다.** `readV()` 와 `readPlain()` 의 바이트코드가 **둘 다 `getfield`** 로 똑같다 — 다른 것은 **필드의 `ACC_VOLATILE` 플래그**뿐이다.

비용 — 블록이 **범위를 좁힐 수 있어** 대개 낫다. 메서드 전체에 걸면 **락을 쥔 채 I/O 를 하는** 코드가 쉽게 생긴다.

### (8) `wait`/`notify` — 락을 쥐고 불러야 한다

**언제 쓰나** — 조건이 갖춰질 때까지 기다려야 할 때. **잘못 부르면 바로 예외가 난다.**

**실행 결과** (`Ex.java` — 33-e, JDK 21.0.5)

```text
--- 락을 안 잡고 wait() 를 부르면
  java.lang.IllegalMonitorStateException: current thread is not owner
  at java.base/java.lang.Object.wait0(Native Method)
--- 락을 안 잡고 notify() 를 부르면
  java.lang.IllegalMonitorStateException: current thread is not owner
--- 다른 객체의 락을 잡고 wait() 를 부르면
  java.lang.IllegalMonitorStateException: current thread is not owner
--- 제대로 잡고 wait/notify
  대기 스레드: 깨어났고 ready=true
--- wait 는 락을 놓는다 (sleep 은 안 놓는다)
  wait 중인 락을 잡는 데 0 ms
  sleep 중인 락을 잡는 데 250 ms
--- InterruptedException 을 삼키면 플래그가 지워진다
  잡은 직후 isInterrupted = false
  삼킨 뒤 isInterrupted   = false
  복구한 뒤 isInterrupted = true
```

```text
wait 중                                    sleep 중

  synchronized (LOCK) {                     synchronized (LOCK) {
      LOCK.wait();   <- 락을 놓는다              Thread.sleep(300); <- 락을 쥔 채 잔다
  }                                         }
        |                                         |
        v                                         v
  남이 그 락을 0 ms 만에 잡았다               남이 250 ms 를 기다려야 했다
```

그림 해설 (한 단계씩):

- **`wait`·`notify`·`notifyAll` 은 그 객체의 락을 쥔 상태에서만 부를 수 있다.**\
  아니면 `IllegalMonitorStateException: current thread is not owner` 다.
- **다른 객체의 락을 쥐고 있어도 소용없다** — 세 번째 줄이 그 경우다.
- **`wait` 는 락을 놓고, `sleep` 은 안 놓는다.** 실측에서 0 ms 대 250 ms 로 갈렸다.
- `InterruptedException` 을 **잡기만 하고 넘어가면 인터럽트 플래그가 지워진다.**\
  `catch` 안에서 `Thread.currentThread().interrupt()` 로 되살려야 위쪽이 안다.

비용 — `wait`/`notify` 는 저수준이다. 실무에서는 `java.util.concurrent` 의 `CountDownLatch`·`BlockingQueue` 로 대체한다([`../54-executorservice-and-future/`](../54-executorservice-and-future/)).

### (9) 교착 — 예외를 안 던진다

**언제 쓰나** — 락을 둘 이상 잡는 코드를 쓸 때.

**실행 결과** (`Ex.java` — 33-g, JDK 21.0.5, 각 20회 반복)

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

```text
순서를 뒤집으면 (20/20 멈춤)               순서를 맞추면 (0/20 멈춤)

  t1: A -> B                                t1: A -> B
  t2: B -> A                                t2: A -> B
       |                                         |
       v                                         v
  서로 상대가 쥔 것을 기다린다                 뒤에 온 쪽이 A 에서 기다렸다가
  영원히 BLOCKED                             앞의 것이 끝나면 통째로 진행
```

그림 해설 (한 단계씩):

- **교착은 예외를 안 던진다.** 스택트레이스도, 로그도 없다. 그냥 **멈춰 있다.**
- 밖에서 보려면 `ThreadMXBean.findDeadlockedThreads()` 나 스레드 덤프를 쓴다.\
  `getLockName()`·`getLockOwnerName()` 이 **누가 무엇을 쥐고 누구를 기다리는지** 알려 준다.
- **고치는 법은 순서 고정 하나다** — 모든 스레드가 같은 순서로 잡으면 20/20 → 0/20 이 된다.
- 이 실험은 **비결정적이 아니다** — 20/20, 0/20 으로 갈렸다. 락 둘을 뒤집는 구조는 거의 확실히 걸린다.

비용 — 락 둘 이상을 잡아야 하면 **락에 순서를 매기고 문서화한다.** 그게 안 되면 `tryLock`(타임아웃) 으로 간다.

## 문법 — 형태와 규칙

### `synchronized` 의 네 형태

```java
class Counter {
    private int n;
    private static int total;
    private final Object lock = new Object();

    synchronized void a() { n++; }                         // 잠금 대상 = this
    static synchronized void b() { total++; }              // 잠금 대상 = Counter.class
    void c() { synchronized (this) { n++; } }              // a() 와 같다
    void d() { synchronized (lock) { n++; } }              // 잠금 대상 = lock
}
```

- **메서드에 붙는 `synchronized` 는 선언의 수식어**다. 추상 메서드·인터페이스 메서드에는 못 붙인다.
- **블록의 괄호 안은 참조 타입 식**이어야 한다. 기본형은 컴파일 에러, `null` 은 런타임 `NullPointerException`.
- `synchronized` 는 **오버라이딩에 상속되지 않는다** — 재정의한 메서드에 다시 붙여야 한다.

### `volatile` 의 형태

```java
class Flags {
    volatile boolean running = true;   // 필드에만 붙는다
    // volatile int local;             // 지역 변수에는 못 붙인다
    // volatile final int x = 1;       // final 과 함께 못 쓴다
}
```

- **`volatile` 은 필드 수식어다.** 지역 변수·파라미터에는 못 쓴다.
- **`final` 과 같이 못 쓴다**(JLS §8.3.1.4).
- 배열에 붙이면 **배열 참조**가 `volatile` 이지 **원소**가 아니다.

### 컴파일 에러로 확인한 것

**실행 결과** (`Ex.java` — 33-f, `javac`, JDK 21.0.5)

```text
f/Ex.java:28: warning: [synchronization] attempt to synchronize on an instance of a value-based class
        race("박싱된 Integer 에 락 (매번 새 객체)", threads, per, () -> { synchronized (boxedLock) { shared++; boxedLock = boxedLock + 1; } });
                                                                ^
1 warning
```

- `Integer`·`Long`·`Boolean` 같은 **값 기반 클래스에 락을 걸면 `javac` 가 경고**한다.
- ★ **이 경고의 이름이 버전에 따라 다르다** — 17·21 은 `[synchronization]`, **25 는 `[identity]`** 다(아래 「구현 세부사항」).

## 어디서 틀리나

### 1. 잠금 대상을 나눠 놓고 "동기화했다"고 생각한다

```java
class Registry {
    private static Map<String, String> CACHE = new HashMap<>();
    synchronized void put(String k, String v) { CACHE.put(k, v); }   // 인스턴스마다 열쇠가 다르다
}
```

- `Registry` 인스턴스가 둘 이상이면 **배제가 안 된다** — (5) 에서 0/10회.
- **`static` 데이터는 `static` 락으로, 인스턴스 데이터는 인스턴스 락으로.**

### 2. `volatile` 로 카운터를 지킨다

- `volatile int count; count++` 은 **10회 중 0회 정답**이다((4)).
- 카운터에는 `AtomicInteger`([`../55-atomics-and-concurrent-collections/`](../55-atomics-and-concurrent-collections/)) 나 락을 쓴다.

### 3. 락 객체를 `public` 으로 둔다

```java
public class Service {
    public final Object lock = new Object();   // 남이 이 열쇠로 잠글 수 있다
}
```

- 남의 코드가 `synchronized (service.lock)` 을 하면 **내 임계 구역이 남의 사정으로 막힌다.**
- **`private final` 객체**를 락으로 둔다. `this` 도 사실상 공개된 열쇠다.

### 4. 값 기반 클래스·문자열 리터럴에 락을 건다

**실행 결과** (`Ex.java` — 33-f, JDK 21.0.5)

```text
--- 왜 위험한가 — 잠금 대상의 정체
  Integer.valueOf(1) 둘이 같은 객체인가 : true   (캐시 범위 -128~127)
  Integer.valueOf(1000) 둘이 같은 객체인가 : false
  문자열 리터럴 "LOCK" 둘이 같은 객체인가  : true   (상수 풀 — JVM 전체가 공유)
  new String("LOCK") 과 리터럴          : false
  Boolean.TRUE 와 Boolean.valueOf(true)  : true
```

- `Integer` 1 이나 `"LOCK"` 리터럴은 **JVM 전체가 공유하는 객체**다.\
  전혀 상관없는 라이브러리가 같은 열쇠를 잡고 있을 수 있다.
- 값이 캐시 범위를 벗어나면 **매번 다른 객체**가 되어 이번엔 배제가 안 된다(`1000` 은 `false`).
- 객체 정체성은 [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) 와 [`../35-string/`](../35-string/) 이 정본이다.

### 5. 락 필드를 블록 안에서 갈아 끼운다

**실행 결과** (`Ex.java` — 33-f, 8스레드 × 5만 회, 각 10회, JDK 21.0.5)

```text
--- 잠금 대상을 잘못 고른 경우 (8스레드 x 50000, 기대 400000, 각 10회)
  고정된 private 객체 (정상)                      정답 10/10회  관측 400000 ~ 400000
  값이 바뀌는 필드에 락                             정답  0/10회  관측 346382 ~ 366357
  박싱된 Integer 에 락 (매번 새 객체)                정답  0/10회  관측 350248 ~ 369406
```

- **락 객체는 `final` 이어야 한다.** 참조가 바뀌면 다음 스레드는 다른 열쇠를 잡는다.

### 6. `null` 에 락을 건다

```text
--- null 에 락을 걸면
  java.lang.NullPointerException: Cannot enter synchronized block because "<local10>" is null
```

- 컴파일은 된다. **런타임에 터진다.** 메시지가 원인을 정확히 말해 준다(헬프풀 NPE).

### 7. 블록 안에서 참조를 바꾸면 무엇이 풀리나

```text
--- 락을 잡은 채 필드를 바꾸면 나갈 때 무엇을 놓나
  블록 안에서 참조를 바꾼 뒤 holdsLock(처음 객체) : true
  블록 안에서 참조를 바꾼 뒤 holdsLock(새 객체)  : false
  (monitorexit 은 블록 진입 때 저장해 둔 객체를 푼다 — javap 의 astore_1/aload_1)
```

- **진입할 때 잡은 객체가 나갈 때 풀린다.** (7) 의 `astore_1` 이 그 장치다.

### 8. `wait` 를 `if` 로 감싼다

```java
synchronized (lock) {
    if (!ready) lock.wait();     // 틀림
    while (!ready) lock.wait();  // 맞음
}
```

- `wait` 는 **깨어난 이유를 알려 주지 않는다.** 깨어났을 때 조건이 아직 거짓일 수 있다.
- **항상 `while` 루프 안에서 기다린다.**

### 9. `InterruptedException` 을 삼킨다

```java
try { Thread.sleep(100); } catch (InterruptedException e) { }   // 플래그가 지워진 채 사라진다
```

- (8) 의 실측 — **잡은 직후 `isInterrupted` 가 이미 `false`** 다.
- 다시 던지거나 `Thread.currentThread().interrupt()` 로 복구한다.\
  예외를 삼켰을 때 무엇이 사라지는지는 [`../25-exceptions/`](../25-exceptions/) 가 정본이다.

### 10. 락을 쥔 채 오래 기다린다

- (8) 의 실측 — `sleep` 중인 락을 잡으려면 **250 ms** 를 기다린다.
- **I/O·네트워크 호출·다른 락 획득을 `synchronized` 안에서 하지 않는다.**

### 11. 테스트가 통과했다고 안전하다고 판단한다

- (1) 의 전부다. **작은 실험은 20/20 정답이고, 큰 실험도 13\~18/20 이 정답이다.**
- 동시성 코드는 **실행으로 안전을 증명할 수 없다.** 잠금 대상이 하나인지 **읽어서** 확인한다.

## 구현 세부사항 대 언어 보장

| 관측한 것 | 누가 보장하나 | 버전에 갈리나 |
|---|---|---|
| `synchronized` 메서드가 `ACC_SYNCHRONIZED` 로, 블록이 `monitorenter`/`monitorexit` 로 컴파일되는 것 | **JVMS 가 정한 것**이지만 이 문서의 근거는 `javap` 관측이다 | 17·21·25 에서 확인 안 함(21만 찍었다) |
| 일반 `int++` 이 8스레드에서도 **자주 정답**인 것 | **아무도 보장 안 한다.** JIT 최적화의 부작용이다 | ★ **갈린다** — 25 에서 20/20 정답이 나왔다 |
| `volatile` 플래그가 루프를 멈추게 하는 것 | **JLS §17.4 가 보장**(가시성) | 17·21·25 동일(5/5) |
| 일반 플래그가 루프를 **안** 멈추는 것 | 보장이 아니라 **관측**이다. `-Xint` 에서는 멈춘다 | 17·21·25 동일(0/5) |
| `long` 쓰기가 안 찢어지는 것 | **보장 아님.** JLS §17.7 이 쪼개질 수 있다고 적는다 | 이 머신에서 2,899만 회 중 0회 |
| `IllegalMonitorStateException` 의 메시지 `current thread is not owner` | javadoc 이 예외 종류만 정한다. **문구는 구현 세부** | 17·21·25 문구 동일 |
| 그 예외의 스택 최상단 프레임 | 구현 세부 | ★ **갈린다** — 17 은 `Object.wait`, **21·25 는 `Object.wait0`** |
| 값 기반 클래스 락 경고의 **린트 이름** | `javac` 의 구현 | ★ **갈린다** — 17·21 `[synchronization]`, **25 `[identity]`** |
| 교착이 20/20 재현되는 것 | 보장 아님. 다만 이 구조는 거의 확실히 걸린다 | 21 에서만 확인 |

**세 버전에서 갈린 것 둘** (실제로 돌려 확인했다)

```text
17.0.13                     21.0.5                      25.0.1
--------------------------  --------------------------  --------------------------
at java.lang.Object.wait    at java.lang.Object.wait0   at java.lang.Object.wait0
[synchronization] 경고      [synchronization] 경고      [identity] 경고
```

★ **"세 곳에서 같았다"는 보장이 아니다.** 이 문서에서 세 버전이 같았던 것(가시성 5/5·잠금 대상 패턴)도 **관찰**로만 적었다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 플래그 하나로 루프를 멈춘다 | **`volatile`** | 가시성만 필요하고 읽고-고치고-쓰기가 없다 |
| 한 번 만들고 참조만 바꿔 게시한다 | **`volatile`** 참조 | 위와 같다 |
| 카운터를 올린다 | **`AtomicInteger`·`LongAdder`** | 읽고-고치고-쓰기다. [55번 주제](../55-atomics-and-concurrent-collections/) |
| 필드 둘 이상을 함께 바꾼다 | **`synchronized`** 또는 `ReentrantLock` | 원자성이 여러 변수에 걸린다 |
| 맵에 카운트를 쌓는다 | **`ConcurrentHashMap.merge`** | 락을 직접 안 잡는다. [55번 주제](../55-atomics-and-concurrent-collections/) |
| 조건이 갖춰질 때까지 기다린다 | `CountDownLatch`·`BlockingQueue` | `wait`/`notify` 보다 안전하다 |
| 타임아웃·시도-실패가 필요하다 | `ReentrantLock.tryLock` | `synchronized` 에는 타임아웃이 없다 |
| 읽기가 압도적으로 많다 | `ReadWriteLock`·불변 객체 | `synchronized` 는 읽기끼리도 막는다 |
| 가상 스레드 안에서 블로킹한다 | ★ **JDK 판을 본다** | 21 에서는 `synchronized` 가 캐리어를 붙잡는다. [`../56-virtual-threads/`](../56-virtual-threads/) |

**가장 싼 답은 공유하지 않는 것이다.** 불변 객체·스레드 로컬·메시지 전달로 공유를 없애면 이 장 전체가 필요 없다.

## 핵심 문장

- **`synchronized` 는 코드가 아니라 객체를 잠근다.** 같은 객체여야 배제가 성립한다.
- **`volatile` 은 가시성을 주고 원자성은 안 준다.** `count++` 는 세 동작이다.
- **동기화를 빼도 대개 맞는 값이 나온다.** 실측에서 8스레드 × 10만 회가 20회 중 13\~20회 정답이었다.
- **"안 터졌다"는 "안전하다"가 아니다.** JIT 를 끄면 같은 코드가 0/20 으로 뒤집힌다.
- **교착은 예외를 안 던진다.** 멈춰 있는 것이 증상의 전부다.

## 관련 자료

- [`../../언어-특성/README.md`](../../언어-특성/README.md) §9 — **메모리 모델이 정본이다.**\
  그쪽은 **happens-before 가 무엇을 정의하나**까지, 여기는 **그 정의를 코드로 어떻게 만족시키나**부터.\
  §4\~5(JIT)·§7\~8(GC) 도 그쪽이다 — 이 문서의 `-Xint` 실험은 **관측만** 싣고 원인 설명은 하지 않는다.
- [`../../../../process-thread/`](../../../../process-thread/) — OS 스레드·컨텍스트 스위칭.\
  그쪽은 **스레드가 무엇인가**까지, 여기는 **자바 키워드의 문법**부터.
- [`../55-atomics-and-concurrent-collections/`](../55-atomics-and-concurrent-collections/) — 락 없이 같은 일을 하는 도구.\
  이 주제가 **락으로 막는 법**이면 그쪽은 **CAS 로 막는 법**이다.
- [`../54-executorservice-and-future/`](../54-executorservice-and-future/) — 스레드를 직접 만들지 않는 법.\
  이 문서의 예제는 전부 `new Thread` 를 쓴다. **실무에서는 그쪽을 쓴다.**
- [`../56-virtual-threads/`](../56-virtual-threads/) — `synchronized` 가 **가상 스레드에서 무엇을 막는가**.\
  ★ 이 주제의 키워드가 그쪽에서 **버전에 따라 다르게 동작한다.**
- [`../49-parallel-streams/`](../49-parallel-streams/) — 공유 상태가 병렬 스트림에서 깨지는 모습.\
  그쪽이 **공용 ForkJoinPool 과 `ArrayList` 경쟁을 이미 실측했다.** 여기서 다시 재지 않는다.
- [`../25-exceptions/`](../25-exceptions/) — `InterruptedException` 을 삼켰을 때 무엇이 사라지나.
- [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) · [`../35-string/`](../35-string/) — `Integer` 캐시와 문자열 상수 풀. **락 객체의 정체성 문제의 근거.**

## 용어 풀이

- **모니터(monitor)** — 모든 자바 객체가 하나씩 가진 잠금 장치. `synchronized` 가 잡고 푸는 것이 이것이다.
- **임계 구역(critical section)** — 한 번에 한 스레드만 들어가야 하는 코드 구간.
- **경쟁 조건(race condition)** — 결과가 스레드 실행 순서에 좌우되는 상태.
- **가시성(visibility)** — 한 스레드가 쓴 값을 다른 스레드가 볼 수 있는지의 문제.
- **원자성(atomicity)** — 여러 단계가 쪼개지지 않고 통째로 일어나는 성질.
- **재진입(reentrancy)** — 이미 락을 쥔 스레드가 같은 락에 다시 들어갈 수 있는 성질.
- **읽고-고치고-쓰기(read-modify-write)** — `n++` 처럼 현재 값을 읽어 계산하고 다시 쓰는 연산.
- **교착(deadlock)** — 두 스레드가 서로가 쥔 락을 기다려 둘 다 영원히 못 나아가는 상태.
- **`ACC_SYNCHRONIZED`** — `synchronized` 메서드에 붙는 클래스 파일의 메서드 플래그. `javap -v` 로 보인다.
- **`monitorenter`/`monitorexit`** — `synchronized` **블록**이 컴파일되는 두 바이트코드 명령.
- **값 기반 클래스(value-based class)** — `Integer`·`Boolean` 처럼 **정체성을 약속하지 않는** 클래스. 락 대상으로 쓰면 안 된다.
- **인터럽트 플래그** — 스레드마다 있는 불리언. `InterruptedException` 을 잡으면 지워진다.
- **스레드 덤프** — 모든 스레드의 스택과 락 상태를 찍은 것. 교착을 보는 표준 수단.

## 더 들어가면

- **`ReentrantLock`** — `synchronized` 가 못 하는 것을 한다: `tryLock(타임아웃)`, `lockInterruptibly`, 공정성 옵션, 여러 개의 `Condition`.\
  대신 `finally` 에서 반드시 `unlock` 해야 한다 — **`synchronized` 는 그 실수가 불가능하다.**
- **`StampedLock`**(8+) — 낙관적 읽기. 읽기가 압도적으로 많을 때. 재진입이 **안 된다.**
- **`VarHandle`**(9+) — `volatile`·`acquire/release`·`opaque` 접근 모드를 **호출 단위로** 고른다.\
  `volatile` 필드가 "항상 가장 센 모드"라면 이쪽은 **필요한 만큼만** 고르는 도구다.
- **이중 검사 잠금(double-checked locking)** — `volatile` 없이 쓰면 깨진다는 고전적 예. 요즘은 **홀더 클래스 관용구**나 `enum` 싱글턴을 쓴다.
- **`synchronized` 의 비용** — [`../../언어-특성/README.md`](../../언어-특성/README.md) §9 가 LMAX 측정을 인용한다. **그쪽이 정본이라 여기서 다시 재지 않았다.**
