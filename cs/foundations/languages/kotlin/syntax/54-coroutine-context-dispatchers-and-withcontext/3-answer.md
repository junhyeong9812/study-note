# kotlin/syntax/54 — `CoroutineContext` 와 디스패처 · `withContext` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`, 그리고 **kotlinx-coroutines-core-jvm 1.11.0** 에서 실제로 얻었다(이 머신은 코어 24개).
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **6 / 8 이 줄을 섰다** — 겹친 것은 `IO`(`cores+1`)와 `Default → withContext(IO)` 둘뿐 · `Default` 는 **`cores`** 까지 · `IO` 도 **`ioLimit`** 에서 멈춘다 · 한 스레드짜리 넷은 **`1`** · `kotlinc` 는 **아무것도 안 찍는다**

**출력**

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar grid54.kt -d o54g =====
(exit 0)
===== java -cp o54g:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Grid54Kt 2>/dev/null =====
dispatcher	N	one thread	all on main	most at once	queued
runBlocking (no dispatcher)	cores+1	true	true	1	true
Dispatchers.Unconfined	cores+1	true	true	1	true
newSingleThreadContext	cores+1	true	false	1	true
Default.limitedParallelism(1)	cores+1	true	false	1	true
Dispatchers.Default	cores+1	false	false	cores	true
Default -> withContext(IO)	cores+1	false	false	all N	false
Dispatchers.IO	cores+1	false	false	all N	false
Dispatchers.IO	ioLimit+1	false	false	ioLimit	true
rows where blocking calls queued: 6 / 8
(exit 0)
```

**왜 그런가**

- ★★★ `Thread.sleep` 은 **스레드를 쥔 채** 잔다 — 그 스레드에서는 다른 코루틴이 못 돈다. 그래서 동시에 도는 수 = **디스패처의 스레드 수**다. `Default` 는 코어 수, `IO` 는 `max(64, cores)`(2-summary (5) KDoc).
- ★★★ `withContext(Dispatchers.IO)` 는 **블로킹 구간만** IO 풀로 보낸다 — 걸어 둔 곳이 `Default` 여도 겹친다.
- ★★ `runBlocking`·`Unconfined` 는 **main 하나**에서 차례로, `newSingleThreadContext`·`limitedParallelism(1)` 은 **main 이 아닌 스레드 하나**에서 차례로 잤다. `Unconfined` 는 `launch` 자리에서 바로 돌아 `launch` 호출 자체가 막혔다.
- ★★ 컴파일 줄이 `(exit 0)` 뿐인 것이 답의 일부다 — **`kotlinc` 는 블로킹 호출을 모른다.**

### 2. ★★★ 안쪽 `Job` 은 **바깥 `Job` 의 자식(다른 객체)** · 이름은 물려받고 디스패처만 `IO` · **`42` 를 돌려받고 main 으로 복귀** · `7` 은 **`DispatchedCoroutine` · `UndispatchedCoroutine` · `ScopeCoroutine`** · 예외는 **부른 자리에서 잡히고 바깥은 살아 있다** · 취소되면 **`9`·`11` 은 안 찍힌다**

**출력**

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar within54.kt -d o54w =====
(exit 0)
===== java -cp o54w:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Within54Kt 2>/dev/null =====
1 inner Job === outer Job: false
2 inner Job is a child of outer Job: true
3 CoroutineName inside: CoroutineName(outer54)
4 dispatcher inside: Dispatchers.IO
5 running on main: false
6 value returned: 42 · back on main: true
7 withContext(IO): Job class = DispatchedCoroutine · on main = false
7 withContext(CoroutineName only): Job class = UndispatchedCoroutine · on main = true
7 withContext(EmptyCoroutineContext): Job class = ScopeCoroutine · on main = true
8 caught at the withContext call: thrown inside · outer Job active: true
10 finally inside withContext · on main = false
12 caller caught JobCancellationException · on main = true
13 launched job isCancelled: true
(exit 0)
```

**왜 그런가**

- ★★★ `withContext` 는 **새 lexically scoped 자식 코루틴**을 만든다 — 바깥 `Job` 이 부모다(`2`). 코드는 한 흐름이다 — 부른 쪽은 블록이 끝날 때까지 멈추고 **결과를 받는다**(`6`).
- ★★★ 경로는 셋 — 디스패처가 다르면 `DispatchedCoroutine`(스레드가 바뀐다) · 디스패처가 같으면 `UndispatchedCoroutine`(**그 자리에서**, `on main = true`) · 문맥이 같으면 `ScopeCoroutine`. 이름은 내부 구현이다.
- ★★ 블록의 실패는 **부모를 취소하지 않고 부른 자리로 다시 던져진다**(`8`). 바깥 취소는 **안으로 번져** 안쪽 `delay` 가 끊기고, 안쪽 `finally` 가 IO 스레드에서 돈 뒤 부른 쪽이 main 에서 `JobCancellationException` 을 받았다.

### 3. ★★ 원소 **셋** · `+ CoroutineName(b54)` 뒤에도 **셋**(이름만 교체) · 디스패처 둘은 **하나(오른쪽 `IO`)** · `minusKey` 뒤 **둘 · `null`** · `runBlocking` 은 **`BlockingEventLoop`** · 자식은 **부모 이름을 물려받고 인자로 덮는다**

**출력**

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar compose54.kt -d o54c =====
(exit 0)
===== java -cp o54c:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Compose54Kt 2>/dev/null =====
1 elements: 3
2 [CoroutineName] = CoroutineName(a54)
3 [ContinuationInterceptor] = Dispatchers.IO
4 [Job] present: true
5 after + CoroutineName(b54): elements 3 · name CoroutineName(b54)
6 Default + IO: elements 1 · Dispatchers.IO
7 minusKey(CoroutineName): elements 2 · name null
8 runBlocking dispatcher class: BlockingEventLoop
9 child without name sees: CoroutineName(parent54)
10 child with + sees: CoroutineName(child54) · Dispatchers.IO
11 a running child is in parent.children: true
(exit 0)
```

**왜 그런가**

- ★★★ `CoroutineContext` 는 **키로 찾는 원소 집합**이다 — `+` 는 같은 키가 있으면 **오른쪽으로 덮어쓴다.** 디스패처의 키는 둘 다 `ContinuationInterceptor` 라 하나만 남는다.
- ★★ `launch` 는 부모 문맥 위에 **인자를 `+`** 한 문맥에서 돈다 — 인자에 없는 칸(`CoroutineName`)은 부모 것이다. 도는 동안 부모 `Job` 의 `children` 에 있다.
- ★ `BlockingEventLoop` 은 `runBlocking` 이 **부른 스레드 하나**로 돌리는 디스패처다 — [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/)가 잰 「스레드 id 1개」가 이것이다.

### 4. ★★ **`U1` → `M1`**(Unconfined 는 바로 돈다, main) · `U2` 는 **`kotlinx.coroutines.DefaultExecutor`** · `U3`·`U4` 는 **`DefaultDispatcher-worker-#`** · **`M2` → `C1`**(기본 `launch` 는 줄을 선다) · `C2`·`C4` 는 **main 으로 복귀**

**출력**

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar unconf54.kt -d o54u =====
(exit 0)
===== java -cp o54u:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Unconf54Kt 2>/dev/null =====
U1 before delay: main
M1 line after launch(Unconfined): main
U2 after delay: kotlinx.coroutines.DefaultExecutor
U3 inside withContext(IO): DefaultDispatcher-worker-#
U4 after withContext(IO): DefaultDispatcher-worker-#
M2 line after launch: main
C1 before delay: main
C2 after delay: main
C3 inside withContext(IO): DefaultDispatcher-worker-#
C4 after withContext(IO): main
(exit 0)
```

**왜 그런가**

- ★★★ `Unconfined` 는 **첫 중단점까지 부른 자리(main)** 에서 돌고, 그 뒤로는 **깨운 쪽 스레드**에서 계속한다 — `delay` 를 깨우는 `DefaultExecutor`, `withContext(IO)` 를 끝낸 IO 워커. KDoc 「`resume in whatever thread that is used by the corresponding suspending function`」.
- ★★ 기본 `launch` 는 `runBlocking` 의 이벤트 루프(main)에 묶여 있어 `withContext` 결과가 **main 으로 다시 디스패치**된다(`C4`).
- ★ 순서 로그 셋은 세 판 되풀이 해시가 안 갈렸다(2-summary (4) 끝의 블록).

### 5. ★★ **안 된다** — 「`Operator '+' on two CoroutineDispatcher objects is meaningless`」 · 라이브러리가 `plus(CoroutineDispatcher)` 를 **`@Deprecated(level = ERROR)`** 로 막았고, **그것을 에러로 만드는 것은 컴파일러**다

**출력**

```kotlin
// dplus54.kt
import kotlinx.coroutines.*

val both54 = Dispatchers.Default + Dispatchers.IO
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar dplus54.kt -d o54p =====
dplus54.kt:3:34: error: 'fun plus(other: CoroutineDispatcher): CoroutineDispatcher' is deprecated. Operator '+' on two CoroutineDispatcher objects is meaningless. CoroutineDispatcher is a coroutine context element and `+` is a set-sum operator for coroutine contexts. The dispatcher to the right of `+` just replaces the dispatcher to the left.
val both54 = Dispatchers.Default + Dispatchers.IO
                                 ^
(exit 1)
```

```text
===== sed -n '155,160p' commonMain/CoroutineDispatcher.kt =====
     * Note that there is no guarantee that the underlying system thread will always be the same.
     *
     * #### It is not a mutex!
     *
     * **Pitfall**: [limitedParallelism] limits how many threads can execute some code in parallel,
     * but does not limit how many coroutines execute concurrently!
(exit 0)
===== sed -n '298,303p' commonMain/CoroutineDispatcher.kt =====
    @Deprecated(
        message = "Operator '+' on two CoroutineDispatcher objects is meaningless. " +
            "CoroutineDispatcher is a coroutine context element and `+` is a set-sum operator for coroutine contexts. " +
            "The dispatcher to the right of `+` just replaces the dispatcher to the left.",
        level = DeprecationLevel.ERROR
    )
(exit 0)
```

**왜 그런가**

- ★★★ 언어에는 디스패처끼리 `+` 를 금지하는 규칙이 **없다** — `CoroutineContext.plus` 로는 된다(3번의 `6` — `as CoroutineContext` 로 올려 더했다). 막은 것은 kotlinx-coroutines 가 디스패처 쪽에 둔 **더 구체적인 오버로드의 폐기 선언**이고, 컴파일러는 오버로드를 고른 뒤 **폐기 수준 `ERROR`** 를 에러로 낸다.
- ★★ 메시지가 말하는 그대로 — 「`` The dispatcher to the right of `+` just replaces the dispatcher to the left. ``」 문맥에 디스패처 칸은 **하나**다.

### 6. ★ **`[value-of-a, value-of-b, value-of-c]`** · **`CoroutineName(form54)`** · **`(55, CoroutineName(cpu54))`**

**출력**

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar form54.kt -d o54f =====
(exit 0)
===== java -cp o54f:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Form54Kt 2>/dev/null =====
[value-of-a, value-of-b, value-of-c]
CoroutineName(form54)
(55, CoroutineName(cpu54))
(exit 0)
```

**왜 그런가**

- ★★ `read54` 가 **스스로** `withContext(Dispatchers.IO)` 로 옮기므로 부르는 쪽(`async`)은 디스패처를 몰라도 된다. `withContext` 는 블록의 값(`Pair`)을 돌려주고, 안에서 준 이름 `cpu54` 는 **그 블록 안에서만** 보인다 — 바깥은 여전히 `form54` 다.

### 7. ★★★ `Default` 의 스레드 수가 **코어 수**라서 — KDoc 「`equal to the number of CPU cores, but is at least two`」 · `delay` 였다면 **중단점**이라 스레드를 놓아 줄을 서지 않는다([52번 주제](../52-coroutine-basics-suspend-scope-launch-async/))

- ★★★ `Thread.sleep` 은 스레드를 쥐고 자므로 `cores + 1` 번째 코루틴은 **스레드가 빌 때까지** 못 시작한다 — `most at once = cores`.
- ★★ `delay` 는 `suspend` 함수라 코루틴만 멈추고 스레드를 풀에 돌려준다 — 한 스레드에서도 끼어든다는 것은 [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/)가 `delay(10)` 대 `Thread.sleep(10)` 로 쟀다. ★ 이 문서는 `Default` 에서 `delay` N 개를 **따로 돌리지 않았다.**

### 8. ★★★ 맞는 곳 — **부른 쪽이 멈추고 결과를 받는 한 흐름**이다 · 어긋나는 곳 — 안쪽 `Job` 은 **다른 객체이고 바깥의 자식**이다 · KDoc 은 「**`a new *lexically scoped child coroutine*`**」

- ★★★ `1 … false` · `2 … true` 가 「새 자식 `Job`」의 증거다. 디스패처가 같으면(`7` 의 둘째 줄) **스레드도 안 바뀌고 디스패치도 없지만** 그래도 `UndispatchedCoroutine` 이라는 **자식이 생긴다.**
- ★★ 「같은 코루틴」이라 부를 만한 것은 **흐름**이다 — `launch` 와 달리 동시에 돌지 않고, 예외도 부른 자리로 온다. 「새 코루틴」이라 부를 만한 것은 **`Job`** 이다 — 취소·자식 대기를 자기 `Job` 으로 한다.

### 9. ★★ **관찰이다** — KDoc 「`no guarantee that the underlying system thread will always be the same`」 · 보장하는 것은 **동시에 하나만 돈다(`most at once = 1`)** · 보장하지 않는 것은 **같은 스레드**와 **중단점 사이의 배타성(mutex 가 아니다)**

- ★★★ 격자가 `true` 를 낸 것은 이 판·이 부하에서 **본 것**이다 — `Default` 풀의 어느 워커가 그 뷰의 일을 집을지는 약속되지 않는다.
- ★★ KDoc 의 「`It is not a mutex!`」 — 중단점에서 다른 코루틴이 들어온다. 공유 상태의 보호는 [56번 주제](../56-channel-mutex-and-shared-mutable-state/)다.

### 10. ★★ 둘 다 **블로킹 호출을 따로 둔 스레드 풀로 떠넘기고, 부른 쪽은 기다리는 동안 이벤트 루프·디스패처 스레드를 놓는다** · 가상 스레드는 같은 문제를 **JDK 런타임 층**에서 푼다 — 블로킹 호출이 캐리어 스레드를 놓게 만들어 **코드를 안 바꾼다**

- ★★ Python 은 `to_thread` 가 **기본 스레드 풀 하나**로 보내고, Kotlin 은 **보낼 풀을 디스패처로 고른다**(`IO` · `limitedParallelism(n)` · 직접 만든 풀).
- ★★ 가상 스레드 쪽은 [`../../언어-특성/README.md`](../../언어-특성/README.md) §6 이 「같은 문제, 반대 해법」으로 정리한다 — Kotlin 은 라이브러리가 **스레드를 골라 옮기는** 해법이다. ★ 이 문서는 가상 스레드를 **돌리지 않았다.**

## 실행 검증

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

```text
===== java -version =====
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
(exit 0)
```

```text
===== unzip -p kotlinx-coroutines-core-jvm-1.11.0.jar META-INF/MANIFEST.MF | grep -E '^Implementation-(Title|Version)' =====
Implementation-Title: kotlinx-coroutines-core
Implementation-Version: 1.11.0
(exit 0)
===== javap -v -cp kotlinx-coroutines-core-jvm-1.11.0.jar kotlinx.coroutines.Job | grep -E '^ +mv=' =====
      mv=[2,2,0]
(exit 0)
```

```text
===== kotlinc cores54.kt -d o54n =====
(exit 0)
===== java -cp o54n:kotlin-stdlib.jar Cores54Kt =====
availableProcessors = 24
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| ★ **코어 수**(`availableProcessors = 24`) — 머신에 매인다. 격자는 이 수를 칸에 안 쓴다 | ★★ 격자 8행 · 줄을 선 칸 수(탐침 여덟 판 · 캡처 두 벌 동일) |
| 걸린 시간 · 스레드 이름의 숫자 — **칸으로 안 만들었다**(겹침 수 · `#`) | 순서 로그 셋 — 세 판 되풀이 해시가 안 갈렸다 |
| ★ **라이브러리 판** — 1.11.0 이 아니면 다시 돌려라 | 소스 발췌(줄 번호째) · 진단 문구 · 모든 **종료 코드** |
| ★ `limitedParallelism(1)` 의 `one thread` — **관찰**(KDoc 이 보장하지 않는다) | |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-re` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 — **블록 109개 · 동일 109 · 흔들린 칸 0 · ★고칠 것 0**(54\~58 다섯 주제를 한 캡처로 받았다 — 이 주제 몫은 출력 12 · 소스 7 · 환경 5). 추가한 정규화 규칙은 없다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `cores54.kt` | 코어 수(흔들리는 칸) | `kotlinc` → `java` |
| `grid54.kt` | ★★★ 디스패처 8행 × 블로킹 N — 이름 집합 · 겹침 수 · 줄 섬 | `kotlinc` → `java`(표준 출력만 · 칸 수 검사와 줄 선 행 수는 프로그램이 센다) |
| `within54.kt` | ★★★ `withContext` 의 자식 `Job` · 결과 · 경로 셋 · 예외 · 취소 | `kotlinc` → `java` + 세 판 되풀이 해시 |
| `compose54.kt` | ★★ 문맥 합성 · 상속 | `kotlinc` → `java` + 세 판 되풀이 해시 |
| `dplus54.kt` | ★★ 디스패처 `+` 의 폐기 에러 | `kotlinc`(에러 전문) |
| `unconf54.kt` | ★★ `Unconfined` 의 재개 스레드 | `kotlinc` → `java` + 세 판 되풀이 해시 |
| `form54.kt` | 형태 한 벌 | `kotlinc` → `java` |
| 코루틴 소스 jar | 디스패처 KDoc · `limitedParallelism` · 폐기 선언 · `withContext` KDoc 과 경로 셋 | `unzip` → `sed -n` |

**구현 의존 항목** — `DispatchedCoroutine`·`UndispatchedCoroutine`·`ScopeCoroutine`·`BlockingEventLoop` · 스레드 이름(`kotlinx.coroutines.DefaultExecutor`·`DefaultDispatcher-worker-#`) · `limitedParallelism(1)` 이 한 스레드에 머문 것 — 이 판(1.11.0)의 산출물이다.\
반면 **`Default`·`IO` 의 상한 · `Unconfined` 의 재개 규칙 · `withContext` 가 lexically scoped 자식이고 예외를 부른 자리로 던진다**는 **라이브러리 계약(KDoc)**, `CoroutineContext` 의 키·`+` 는 **stdlib(언어)** 다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **`withContext` 는 「새 코루틴이 아니다」가 아니었다** — 안쪽 `Job` 은 바깥의 **자식인 다른 객체**였고, KDoc 도 「`new *lexically scoped child coroutine*`」라 적는다. 디스패처가 같아도 `UndispatchedCoroutine` 이 생긴다.
2. ★★ **디스패처 둘을 `+` 하면 경고가 아니라 에러였다** — 라이브러리의 `@Deprecated(level = ERROR)` 오버로드 때문이다.
3. ★★ **`IO` 에도 줄이 섰다** — `ioLimit + 1` 개를 걸자 `most at once = ioLimit`. 「IO 로 옮기면 겹친다」는 **상한 안에서만** 맞다.
