# kotlin/syntax/52 — 코루틴 기초 — `suspend`·`CoroutineScope`·`launch`/`async`/`await` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — **이 판의 stdlib 소스 jar**(`kotlin-stdlib-sources.jar` 2.4.20)의 `kotlin.coroutines.intrinsics`(`COROUTINE_SUSPENDED`) · **`kotlinx-coroutines-core-jvm` 1.11.0 의 소스 jar**(같은 판 — 53번 주제에서 발췌). ★ 공식 문서 페이지와 KEEP 문서는 **이 작업에서 열지 못했다**(외부 네트워크를 쓰지 않았다) — 설계 논거는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §6 이 원고째 인용한다.
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 9회(호출 규칙 격자 스크립트 안의 1회 포함) · `java` 6회 + 순서 로그 셋을 다섯 판씩 되풀이한 15회 · `javap` 3회 · stdlib 소스 jar 발췌 2곳.\
> ★★★ **라이브러리 판 — `kotlinx-coroutines-core-jvm` 1.11.0**(이 머신의 gradle 캐시에 있던 판 중 가장 새 것 · 매니페스트 `Implementation-Version: 1.11.0` · 클래스 메타데이터 `mv=[2,2,0]` 이라 kotlinc 2.4.20 이 **그대로 읽는다** — `-Xskip-metadata-version-check` 불필요). `launch`·`async`·`runBlocking`·`delay`·`yield` 는 **이 라이브러리의 것**이다. 라이브러리 판이 결과를 바꿀 수 있어 **흔들리는 칸 표에 판을 선언**한다.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「막힌 탐침 N / M」은 스크립트가 스스로 센 것**이다.
> **버전** — `COROUTINE_SUSPENDED` 는 stdlib 소스에 **`@SinceKotlin("1.3")`**(코루틴이 Stable 이 된 판)((5)).
> **경계** — ★★★ 「**코루틴 = 스레드가 아니라 컴파일러 변환**」이라는 **논지**와 가상 스레드와의 대비는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §6 이 정본이다. **스레드·프로세스 개념**은 [`cs/foundations/process-thread/`](../../../../process-thread/) 가 정본이다 — 여기는 **`suspend` 함수의 호출 규칙과 JVM 에서의 모양**만 본다. 람다가 JVM 에서 무엇이 되나는 [10번 주제](../10-lambdas-and-higher-order-functions/), `coroutineScope { }` 의 `this` 가 수신자 람다라는 것은 [37번 주제](../37-lambdas-with-receiver-and-type-safe-builders/)가 정본이다. **취소·예외가 형제와 부모로 번지는 규칙**은 [53번 주제](../53-structured-concurrency-job-cancellation-exceptions/)다. 디스패처와 `withContext` 는 [목록의 **54번 주제**](../54-coroutine-context-dispatchers-and-withcontext/)다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**`javap` — `suspend fun f(x: Int): Int` 가 JVM 에서 `f(int, Continuation): Object` 가 되고 상태 기계 클래스가 생기는 것**」. 둘째 본체는 **호출 규칙 격자**(어디서 부르면 막히나)다. 「스레드가 아니다」는 **스레드 수를 세는** 로그로만 말한다 — 가볍다·빠르다는 재지 않았다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장** | 컴파일러가 하는 것 | ★★★ **`suspend` 는 코루틴이나 다른 `suspend` 함수 안에서만 부른다**(진단) · `suspend` 함수는 JVM 에서 **`Continuation` 인자를 하나 더** 받는다 · stdlib `COROUTINE_SUSPENDED` KDoc |
| **라이브러리 계약(kotlinx-coroutines)** | 라이브러리 문서가 약속한 것 | `launch` 는 `Job` · `async` 는 `Deferred` · `runBlocking` 은 스레드를 막는다 · `delay` 는 스레드를 안 막는다 — ★ **언어가 아니다** |
| **이 판의 관찰** | kotlinc 2.4.20 + kotlinx-coroutines 1.11.0 에서 이번에 본 것 | `javap` 이름(`Cps52Kt$twice$1` · `I$0` · `label`) · 로그 순서 · 스레드 수 |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
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
===== javap -v -cp kotlinx-coroutines-core-jvm-1.10.2.jar kotlinx.coroutines.Job | grep -E '^ +mv=' =====
      mv=[2,1,0]
(exit 0)
```

- ★ `mv=` 는 클래스에 박힌 **Kotlin 메타데이터 판**이다 — 1.11.0 은 `2.2.0`, 대조용으로 둔 1.10.2 는 `2.1.0`. 둘 다 2.4.20 이 읽는 범위다(53번 주제가 1.10.2 로도 한 번 돌린다).

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다 — 칸으로 안 만들었다** | ★ 걸린 시간 | `form52` 의 시간은 **「190ms 미만인가」·「200ms 이상인가」** 참/거짓으로만 찍었다 |
| 안 흔들린다 | ★★ 로그 순서(`interleave52` · `order52` · `await52` · `block52`) | **단일 스레드**(`runBlocking` 의 이벤트 루프) 위에서 `yield()`·같은 길이의 `delay` 로 걸음을 맞췄다 — 캡처 두 벌과 **다섯 판 되풀이**((4) 끝의 블록)가 전부 같았다 |
| 안 흔들린다 | 스레드 수(`distinct thread ids = 1` · `activeCount`) | `runBlocking` 은 **자기 스레드 하나**에서 돈다 · 플랫폼 스레드 100개는 500ms 잠들어 있어 세는 순간 살아 있다 |
| 안 흔들린다 | `javap` 출력 · 호출 규칙 격자 · 진단 문구 | 같은 판이면 같다 |
| ★ **판에 매인다** | 라이브러리 **1.11.0** 의 동작 전부 | 판이 바뀌면 다시 돌려라 — 53번 주제에서 1.10.2 로 한 격자를 대조했다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**`suspend` 함수는 「책갈피를 끼울 수 있는 책」이다.** 읽다가(`delay` 같은 중단점에서) 책갈피를 끼우고 책을 덮으면, 그 사람(스레드)은 **다른 책을 읽으러 간다.** 나중에 누군가 책갈피 자리부터 **이어 읽는다.** 책갈피 = 「몇 쪽까지 읽었나(`label`) + 그때 머릿속에 있던 것(지역 변수 → 필드 `I$0`)」을 담은 **작은 객체**다 — 컴파일러가 만들어 준다.
★ 그래서 코루틴은 **스레드가 아니다** — 스레드 한 명이 책 10만 권을 번갈아 읽을 수 있다. 다만 **책갈피 없이 잠드는 사람**(`Thread.sleep`)은 그동안 **아무 책도 못 읽는다.**

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 책갈피를 끼울 수 있는 책 | `suspend fun` — JVM 에서 **`(…, Continuation): Object`** | (1) ★★★ |
| 책갈피 객체 | 상태 기계 클래스 `Cps52Kt$twice$1` — `label` · `I$0` · `I$1` | (1) ★★★ |
| 「덮었다」 표지 | 반환값 **`COROUTINE_SUSPENDED`** — 그래서 반환 타입이 `Object` | (1)(5) |
| 책갈피 없는 사람은 못 읽는다 | 일반 함수에서 `suspend` 호출 → **컴파일 에러** | (2) ★★★ |
| 한 사람이 10만 권 | `launch` 10만 개 · **스레드 id 1개** | (3) ★★ |
| 책갈피 없이 잠든다 | `Thread.sleep` — 같은 스레드의 다른 코루틴이 **못 돈다** | (3) ★★ |

```text
   suspend fun twice(x: Int): Int              JVM 에서 (javap)
   ──────────────────────────────              ─────────────────────────────────────────────────
   {                                           static Object twice(int x, Continuation c)
       delay(1)          ← 중단점 ①              상태 기계 객체 = Cps52Kt$twice$1 { label, I$0, I$1 }
       val y = x * 2                             tableswitch label  0 → 처음부터
       delay(1)          ← 중단점 ②                                 1 → ① 다음부터
       return y                                                     2 → ② 다음부터
   }                                             delay 가 COROUTINE_SUSPENDED 를 돌려주면
                                                 → 그대로 그 표지를 돌려주고 빠진다(스레드를 놓는다)
```

## 이 주제가 답하려는 질문

1. `suspend` 는 JVM 에서 **무엇이 되나** — 인자·반환 타입·생기는 클래스. 중단점이 없는 `suspend` 함수는 어떻게 되나.
2. `suspend` 함수는 **어디서 부를 수 있나** — 일반 함수 · 람다 종류(inline · 일반 · `suspend`) · `runBlocking` · `Thread { }` 에서.
3. 코루틴이 스레드가 아니라는 것을 **무엇으로 보나** — 스레드 수 · `delay` 대 `Thread.sleep` · 부른 순간 무엇이 도나 · `launch` 대 `async` 의 예외 위치.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **`javap -p` · `javap -c`(발췌)** | CPS 서명 · 상태 기계 클래스 · `label` · `tableswitch` · `COROUTINE_SUSPENDED`((1)) | ★ **본체 창** — 지어낼 수 없는 컴파일러의 일 |
| ★★★ **호출 규칙 격자(컴파일)** | 어디서 부르면 막히나 · 진단 두 종((2)) | 49편의 격자와 같은 꼴 |
| ★★ **계수 로그** | 스레드 id 집합 크기 · `Thread.activeCount()`((3)) | 성능이 아니라 **개수**만 |
| ★★ **순서 로그(단일 스레드)** | 끼어들기 · 부른 순간 무엇이 도나 · 예외가 어디서 나오나((3)(4)) | 흔들림 없이 결정적으로 만들었다 |
| ★ **다른 스레드에서 본 상태** | `runBlocking` 중 main 스레드의 `Thread.State`((4)) | ★ **제5의 상태** — 「막혔나」를 main 스스로는 못 묻는다(막혀 있으니까). **감시 스레드**가 대신 물었다 |
| ★★ **stdlib 소스 발췌** | `COROUTINE_SUSPENDED` · `CancellationException` 의 정체((5)) | — |
| **인용 — 다시 안 잰다** | 「스레드가 아니라 컴파일러 변환」의 논지 · 가상 스레드 대비 | [`../../언어-특성/README.md`](../../언어-특성/README.md) §6 |
| **부적용 — 성능** | 「코루틴은 가볍다」·「빠르다」는 **재지 않았다** — (3)은 **스레드 수**만 센다 | — |

### (1) ★★★ `suspend` 는 컴파일러 변환이다 — `javap` 로 본 CPS

```kotlin
// cps52.kt
import kotlinx.coroutines.delay

suspend fun twice(x: Int): Int {
    delay(1)
    val y = x * 2
    delay(1)
    return y
}

suspend fun plain(x: Int): Int = x + 1

fun normal(x: Int): Int = x + 1
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar cps52.kt -d o52c =====
(exit 0)
===== ls o52c =====
Cps52Kt$twice$1.class
Cps52Kt.class
META-INF
(exit 0)
===== javap -p o52c/Cps52Kt.class =====
Compiled from "cps52.kt"
public final class Cps52Kt {
  public static final java.lang.Object twice(int, kotlin.coroutines.Continuation<? super java.lang.Integer>);
  public static final java.lang.Object plain(int, kotlin.coroutines.Continuation<? super java.lang.Integer>);
  public static final int normal(int);
}
(exit 0)
===== javap -p 'o52c/Cps52Kt$twice$1.class' =====
Compiled from "cps52.kt"
final class Cps52Kt$twice$1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
  int I$0;
  int I$1;
  java.lang.Object result;
  int label;
  Cps52Kt$twice$1(kotlin.coroutines.Continuation<? super Cps52Kt$twice$1>);
  public final java.lang.Object invokeSuspend(java.lang.Object);
}
(exit 0)
===== javap -c -p o52c/Cps52Kt.class | grep -E 'public static final|COROUTINE_SUSPENDED|tableswitch|Field Cps52Kt\$twice\$1\.(label|I\$[0-9])' =====
  public static final java.lang.Object twice(int, kotlin.coroutines.Continuation<? super java.lang.Integer>);
      15: getfield      #15                 // Field Cps52Kt$twice$1.label:I
      27: getfield      #15                 // Field Cps52Kt$twice$1.label:I
      33: putfield      #15                 // Field Cps52Kt$twice$1.label:I
      55: invokestatic  #30                 // Method kotlin/coroutines/intrinsics/IntrinsicsKt.getCOROUTINE_SUSPENDED:()Ljava/lang/Object;
      62: getfield      #15                 // Field Cps52Kt$twice$1.label:I
      65: tableswitch   { // 0 to 2
     102: putfield      #39                 // Field Cps52Kt$twice$1.I$0:I
     108: putfield      #15                 // Field Cps52Kt$twice$1.label:I
     125: getfield      #39                 // Field Cps52Kt$twice$1.I$0:I
     145: putfield      #39                 // Field Cps52Kt$twice$1.I$0:I
     151: putfield      #48                 // Field Cps52Kt$twice$1.I$1:I
     157: putfield      #15                 // Field Cps52Kt$twice$1.label:I
     174: getfield      #48                 // Field Cps52Kt$twice$1.I$1:I
     180: getfield      #39                 // Field Cps52Kt$twice$1.I$0:I
  public static final java.lang.Object plain(int, kotlin.coroutines.Continuation<? super java.lang.Integer>);
  public static final int normal(int);
(exit 0)
```

- ★★★ **`twice(int, kotlin.coroutines.Continuation<? super java.lang.Integer>): java.lang.Object`** — 소스의 `(x: Int): Int` 에 **`Continuation` 인자가 하나 붙고**, 반환은 **`Int` 가 아니라 `Object`** 다. 이것이 CPS(continuation-passing style — 「이어서 할 일」을 인자로 넘기는 꼴)다.
- ★★★ **상태 기계 클래스가 하나 생겼다** — `Cps52Kt$twice$1 extends ContinuationImpl` 에 **`int label`**(어디까지 왔나) · **`int I$0` · `int I$1`**(지역 변수 `x`·`y` 를 필드로 옮겨 놓은 것) · `Object result` · `invokeSuspend`.
- ★★★ **`tableswitch { // 0 to 2`** — 중단점 **둘**이면 이어 들어올 자리가 **셋**(처음 · ① 뒤 · ② 뒤)이다. `label` 을 읽고·쓰는 줄과 `I$0`·`I$1` 에 넣고 빼는 줄이 그 사이사이에 있다.
- ★★ **`getCOROUTINE_SUSPENDED`** 를 부르는 줄이 있다 — 부른 `delay` 가 이 표지를 돌려주면 `twice` 도 **그 표지를 그대로 돌려주고 빠진다.** 반환 타입이 `Object` 인 까닭이 이것이다 — 진짜 값(`Integer`)이거나 **「중단됐다」 표지**다((5)).
- ★★ **`plain(x: Int) = x + 1` 도 `(int, Continuation): Object`** 다 — 중단점이 없어도 **서명은 똑같이 바뀐다.** 그러나 **상태 기계 클래스는 안 생겼다**(`ls` 에 `$plain$` 이 없다).
- ★ `normal(int): int` 은 그대로 — `suspend` 가 아닌 함수는 손대지 않는다.

### (2) ★★★ 호출 규칙 — 어디서 부르면 막히나

```kotlin
// call52.kt
import kotlinx.coroutines.runBlocking

suspend fun f(x: Int): Int = x

fun p1() { f(1) }                                                        // plain-function
suspend fun p2() { f(1) }                                                // suspend-function
suspend fun p3() { listOf(1).forEach { f(it) } }                         // inline-lambda
suspend fun p4() { val g: () -> Unit = { f(1) } }                        // plain-lambda-type
suspend fun p5() { val g: suspend () -> Unit = { f(1) } }                // suspend-lambda-type
fun p6() { runBlocking { f(1) } }                                        // runBlocking-block
fun p7() { Thread { f(1) } }                                             // Thread-lambda
suspend fun p8() { listOf(1).asSequence().map { f(it) }.toList() }       // Sequence-map-lambda
fun p9() { p2() }                                                        // plain-calls-suspend-fun
```

```python
# grid52.py
import os
import re
import subprocess

SRC = "call52.kt"
CP = os.environ["CP52"]

probes = {}
for n, line in enumerate(open(SRC, encoding="utf-8"), 1):
    m = re.search(r"// (\S+)$", line.rstrip("\n"))
    if m:
        probes[n] = m.group(1)

run = subprocess.run(["kotlinc", "-cp", CP, SRC, "-d", "o52g"], capture_output=True, text=True)
first = {}
for line in (run.stdout + run.stderr).splitlines():
    m = re.match(r"call52\.kt:(\d+):\d+: error: (.*)$", line)
    if m:
        first.setdefault(int(m.group(1)), m.group(2))

print("\t".join(["probe", "compile"]))
blocked = 0
for n, name in probes.items():
    cell = "ok" if n not in first else "error: " + first[n]
    blocked += n in first
    print("\t".join([name, cell]))
print("exit %d" % run.returncode)
print("blocked probes: %d / %d" % (blocked, len(probes)))
```

```text
===== CP52=kotlinx-coroutines-core-jvm-1.11.0.jar python3 grid52.py =====
probe	compile
plain-function	error: suspend function 'suspend fun f(x: Int): Int' can only be called from a coroutine or another suspend function.
suspend-function	ok
inline-lambda	ok
plain-lambda-type	error: suspension functions can only be called within coroutine body.
suspend-lambda-type	ok
runBlocking-block	ok
Thread-lambda	error: suspend function 'suspend fun f(x: Int): Int' can only be called from a coroutine or another suspend function.
Sequence-map-lambda	error: suspension functions can only be called within coroutine body.
plain-calls-suspend-fun	error: suspend function 'suspend fun p2(): Unit' can only be called from a coroutine or another suspend function.
exit 1
blocked probes: 5 / 9
(exit 0)
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar call52.kt -d o52e =====
call52.kt:5:12: error: suspend function 'suspend fun f(x: Int): Int' can only be called from a coroutine or another suspend function.
fun p1() { f(1) }                                                        // plain-function
           ^
call52.kt:8:42: error: suspension functions can only be called within coroutine body.
suspend fun p4() { val g: () -> Unit = { f(1) } }                        // plain-lambda-type
                                         ^
call52.kt:11:21: error: suspend function 'suspend fun f(x: Int): Int' can only be called from a coroutine or another suspend function.
fun p7() { Thread { f(1) } }                                             // Thread-lambda
                    ^
call52.kt:12:49: error: suspension functions can only be called within coroutine body.
suspend fun p8() { listOf(1).asSequence().map { f(it) }.toList() }       // Sequence-map-lambda
                                                ^
call52.kt:13:12: error: suspend function 'suspend fun p2(): Unit' can only be called from a coroutine or another suspend function.
fun p9() { p2() }                                                        // plain-calls-suspend-fun
           ^^
(exit 1)
```

- ★★★ **막힌 탐침 5 / 9 · 진단이 두 종이다** —
  일반 함수 몸통에서 부르면 「`suspend function 'suspend fun f(x: Int): Int' can only be called from a coroutine or another suspend function.`」 ·
  `suspend` 함수 **안의 일반 람다**에서 부르면 「`suspension functions can only be called within coroutine body.`」.
- ★★★ **같은 `suspend` 함수 안이라도 람다의 종류가 가른다** — `forEach { }` 는 **`inline`** 이라 람다 몸통이 바깥 `suspend` 함수에 펼쳐져 **된다.** `val g: () -> Unit = { }` 와 `Sequence.map { }`(인라인이 아니다)는 **막힌다.** `val g: suspend () -> Unit = { }` 는 **된다** — 람다 자체가 `suspend` 다.
- ★★ **`runBlocking { }` 안은 된다** — 그 람다의 타입이 `suspend CoroutineScope.() -> T` 이기 때문이다(**라이브러리가 코루틴을 만들어 주는 다리**). `Thread { }` 안은 일반 함수 몸통과 같은 진단이다.
- ★★ **전염된다** — `p2` 가 `suspend` 이니 그것을 부르는 `p9` 도 막힌다. `suspend` 는 **부르는 쪽도 `suspend` 여야 하는** 표지다.

### (3) ★★ 스레드가 아니다 — 세어 보면

```kotlin
// threads52.kt
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.yield
import java.util.concurrent.ConcurrentHashMap
import kotlin.concurrent.thread

fun main() {
    val before = Thread.activeCount()
    val ids = ConcurrentHashMap.newKeySet<Long>()
    var during = 0
    runBlocking {
        repeat(100_000) {
            launch {
                ids.add(Thread.currentThread().threadId())
                delay(100)
                ids.add(Thread.currentThread().threadId())
            }
        }
        yield()
        during = Thread.activeCount()
    }
    println("coroutines: 100000 launched and finished")
    println("coroutines: distinct thread ids seen = ${ids.size}")
    println("coroutines: activeCount before=$before during=$during after=${Thread.activeCount()}")

    val threads = List(100) { thread { Thread.sleep(500) } }
    val duringThreads = Thread.activeCount()
    threads.forEach { it.join() }
    println("threads: 100 started, activeCount during=$duringThreads after=${Thread.activeCount()}")
}
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar threads52.kt -d o52t =====
(exit 0)
===== java -cp o52t:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Threads52Kt =====
coroutines: 100000 launched and finished
coroutines: distinct thread ids seen = 1
coroutines: activeCount before=1 during=1 after=1
threads: 100 started, activeCount during=101 after=1
(exit 0)
```

- ★★★ **코루틴 10만 개가 스레드 id 1개 위에서 돌았다** — `runBlocking` 은 **자기를 부른 스레드(main)** 하나로 이벤트 루프를 돌리고, 모든 `launch` 가 그 위에서 `delay` 마다 스레드를 놓았다. `Thread.activeCount()` 도 전·중·후 **1** 이다.
- ★★ **플랫폼 스레드 100개는 `activeCount` 가 101** 이다(main + 100) — 스레드는 만들 때마다 **하나씩 는다.**
- ★★ **이것은 개수다** — 시간·메모리는 재지 않았다. 「그래서 가볍다」는 이 블록이 말하지 않는다.

```kotlin
// interleave52.kt
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.yield

fun trace(pause: suspend () -> Unit): String {
    val log = mutableListOf<String>()
    runBlocking {
        for (name in listOf("A", "B")) {
            launch {
                repeat(3) { i ->
                    log += "$name$i"
                    pause()
                }
            }
        }
    }
    return log.joinToString(" ")
}

fun main() {
    println("delay(10)        " + trace { delay(10) })
    println("Thread.sleep(10) " + trace { Thread.sleep(10) })
    println("yield()          " + trace { yield() })
}
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar interleave52.kt -d o52i =====
(exit 0)
===== java -cp o52i:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Interleave52Kt =====
delay(10)        A0 B0 A1 B1 A2 B2
Thread.sleep(10) A0 A1 A2 B0 B1 B2
yield()          A0 B0 A1 B1 A2 B2
(exit 0)
```

- ★★★ **`delay(10)` 은 끼어든다(`A0 B0 A1 B1 A2 B2`)**, **`Thread.sleep(10)` 은 안 끼어든다(`A0 A1 A2 B0 B1 B2`)** — 같은 스레드 하나에서, `delay` 는 **중단점**이라 스레드를 놓아 B 가 돌고, `Thread.sleep` 은 **스레드째 재워** B 가 A 가 끝날 때까지 못 돈다.
- ★ `yield()` 는 시간 없이 **순서만 넘긴다** — `delay` 와 같은 모양이다.

### (4) ★★ 부른 순간 무엇이 도나 · `runBlocking` · `async` 의 예외

```kotlin
// order52.kt
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.delay
import kotlinx.coroutines.joinAll
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

val log = mutableListOf<String>()

suspend fun work(tag: String): Int {
    log += "$tag: body starts"
    delay(1)
    log += "$tag: after delay"
    return 1
}

fun main() {
    runBlocking {
        log += "1 before the call"
        work("call")
        log += "2 after the call"
        val j = launch { work("launch") }
        log += "3 after launch { }"
        val u = launch(start = CoroutineStart.UNDISPATCHED) { work("undispatched") }
        log += "4 after launch(UNDISPATCHED) { }"
        joinAll(j, u)
        log += "5 after joinAll"
    }
    log.forEach(::println)
}
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar order52.kt -d o52o =====
(exit 0)
===== java -cp o52o:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Order52Kt =====
1 before the call
call: body starts
call: after delay
2 after the call
3 after launch { }
undispatched: body starts
4 after launch(UNDISPATCHED) { }
launch: body starts
undispatched: after delay
launch: after delay
5 after joinAll
(exit 0)
```

- ★★★ **`suspend` 함수를 그냥 부르는 것은 보통의 호출이다** — `work("call")` 은 몸통을 시작하고, `delay` 에서 멈췄다가 **다 끝난 뒤에야** 다음 줄(`2`)로 온다. 동시에 도는 것이 아니다 — **부른 쪽이 같이 멈춘다.**
- ★★★ **`launch { }` 는 몸통을 바로 안 돌린다** — `3 after launch { }` 가 먼저 찍히고, `launch: body starts` 는 부모가 **멈춘 뒤**(`joinAll`)에야 나온다. 기본 시작(`CoroutineStart.DEFAULT`)은 **디스패처에 줄을 세운다.**
- ★★ **`launch(start = CoroutineStart.UNDISPATCHED)`** 는 **첫 중단점까지 그 자리에서** 돌린다 — `undispatched: body starts` 가 `4` 보다 먼저다.

**세 언어 대비 — 「부른 순간 무엇이 도나」**

| 언어 | 부르기만 하면 | 근거 |
|---|---|---|
| **Kotlin `suspend`** | 몸통이 **끝까지** 돈다(중단점에서는 부른 쪽이 같이 멈춘다) — 따로 돌리려면 `launch`/`async`(라이브러리) · `launch { }` 는 **0줄**, `UNDISPATCHED` 는 **첫 중단점까지** | 위 블록 |
| **Python `async def`** | 코루틴 객체만 나오고 **몸통 0줄** — `await`·`asyncio.run` 이 돌린다 | [Python 51번](../../../python/syntax/51-asyncio-coroutine-basics/) |
| **C# `async`** | ★ **이 문서는 재지 않았다** — C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **40번**이 서면 이 칸을 채운다 | — |

★★ **가장 크게 갈리는 자리** — Python 과 C# 은 **부르는 쪽이 일반 함수여도** 부를 수는 있다(객체·작업이 나온다). Kotlin 은 **부르는 쪽이 `suspend` 가 아니면 컴파일이 안 된다**((2)).

```kotlin
// block52.kt
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlin.concurrent.thread

fun main() {
    val main = Thread.currentThread()
    var seen: Thread.State? = null
    val watcher = thread { Thread.sleep(150); seen = main.state }
    println("1 before runBlocking on ${Thread.currentThread().name}")
    runBlocking {
        launch { delay(300); println("3 child done on ${Thread.currentThread().name}") }
        println("2 inside runBlocking on ${Thread.currentThread().name}")
    }
    println("4 after runBlocking")
    watcher.join()
    println("5 main thread state seen by another thread at 150ms: $seen")
}
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar block52.kt -d o52b =====
(exit 0)
===== java -cp o52b:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Block52Kt =====
1 before runBlocking on main
2 inside runBlocking on main
3 child done on main
4 after runBlocking
5 main thread state seen by another thread at 150ms: TIMED_WAITING
(exit 0)
```

- ★★★ **`runBlocking` 은 부른 스레드를 막는다** — 자식의 `delay(300)` 이 끝날 때까지 `4 after runBlocking` 이 안 나온다. 그동안 **다른 스레드가 본 main 의 상태는 `TIMED_WAITING`** 이다. 그리고 `runBlocking` 안의 코루틴은 **main 스레드 위에서** 돈다(`on main`).
- ★ 그래서 `runBlocking` 은 **`main` 함수·테스트처럼 「막아도 되는」 경계**에 둔다 — 이미 코루틴 안이라면 막을 이유가 없다([목록의 **54번 주제**](../54-coroutine-context-dispatchers-and-withcontext/)에서 디스패처와 함께 본다).

```kotlin
// await52.kt
import kotlinx.coroutines.Deferred
import kotlinx.coroutines.Job
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.yield

fun main() = runBlocking {
    val log = mutableListOf<String>()
    try {
        coroutineScope {
            val other: Job = launch {
                repeat(3) { yield(); log += "other step $it" }
            }
            val d: Deferred<Int> = async {
                yield()
                throw IllegalStateException("boom")
            }
            try {
                d.await()
            } catch (e: IllegalStateException) {
                log += "caught at await: ${e.message}"
            }
            log += "after await: isActive=$isActive, other.isCancelled=${other.isCancelled}"
            yield()
            log += "after yield"
        }
    } catch (e: Exception) {
        log += "outside the scope: ${e::class.simpleName}: ${e.message}"
    }
    log.forEach(::println)
}
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar await52.kt -d o52a =====
(exit 0)
===== java -cp o52a:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Await52Kt =====
other step 0
caught at await: boom
after await: isActive=false, other.isCancelled=true
outside the scope: IllegalStateException: boom
(exit 0)
```

- ★★★ **`async` 의 예외는 `await()` 에서 나온다** — `caught at await: boom`. **그런데 끝이 아니다** — 그 직후 `isActive=false`, 형제 `other` 는 `isCancelled=true`, 다음 `yield()` 에서 블록이 멈춰 `after yield` 는 **안 찍히고**, `coroutineScope` 밖으로 **같은 `IllegalStateException` 이 다시** 나온다.
```text
===== for i in 1 2 3 4 5; do java -cp o52i:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Interleave52Kt | md5sum; java -cp o52o:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Order52Kt | md5sum; java -cp o52a:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Await52Kt | md5sum; done | sort | uniq -c =====
      5 46faf74adab9b9ba1f1b7076d0b2c8eb  -
      5 bf1dfe503ce4c52d261de86189c00c35  -
      5 e98a75e77bd305b1c7ba80f26b487496  -
(exit 0)
```

- ★ **순서 로그 셋(`interleave52` · `order52` · `await52`)을 다섯 판씩 돌려 출력 전체의 해시를 센 것**이다 — 서로 다른 해시가 **셋**이고 각각 **`5`** 번이다. 한 판이라도 줄 순서가 달랐으면 해시가 넷 이상으로 갈린다(규칙 11 — 「가짓수」를 찍는다).
- ★★ 까닭(`await52`) — `async` 자식이 실패한 순간 **부모 scope 가 이미 취소됐다.** `await` 에서 잡은 것은 **값 쪽 통로**일 뿐이고, **구조 쪽 통로**(부모에게 실패 알리기)는 따로 돈다. 이것이 [53번 주제](../53-structured-concurrency-job-cancellation-exceptions/)의 본론이다.

### (5) ★★ stdlib 소스 — 「중단됐다」 표지와 취소 예외의 정체

```text
===== unzip -o -q kotlin-stdlib-sources.jar 'commonMain/kotlin/time/*' 'jvmMain/kotlin/time/*' 'jvmMain/jdk8/kotlin/time/*' commonMain/kotlin/util/Preconditions.kt commonMain/kotlin/util/Standard.kt jvmMain/kotlin/util/AssertionsJVM.kt commonMain/kotlin/contracts/ContractBuilder.kt commonMain/kotlin/coroutines/intrinsics/Intrinsics.kt jvmMain/kotlin/coroutines/cancellation/CancellationException.kt =====
(exit 0)
===== unzip -o -q kotlinx-coroutines-core-jvm-1.11.0-sources.jar commonMain/CoroutineScope.kt commonMain/Supervisor.kt commonMain/Guidance.kt commonMain/CoroutineExceptionHandler.kt commonMain/Yield.kt commonMain/NonCancellable.kt -d kxs =====
(exit 0)
```

```text
===== sed -n '19,22p;57p' commonMain/kotlin/coroutines/intrinsics/Intrinsics.kt =====
 * If the [block] returns the special [COROUTINE_SUSPENDED] value, it means that suspend function did suspend the execution and will
 * not return any result immediately. In this case, the [Continuation] provided to the [block] shall be
 * resumed by invoking [Continuation.resumeWith] at some moment in the
 * future when the result becomes available to resume the computation.
public val COROUTINE_SUSPENDED: Any get() = CoroutineSingletons.COROUTINE_SUSPENDED
(exit 0)
===== sed -n '11p' jvmMain/kotlin/coroutines/cancellation/CancellationException.kt =====
public actual typealias CancellationException = java.util.concurrent.CancellationException
(exit 0)
```

- ★★★ **`COROUTINE_SUSPENDED`** — KDoc 「`If the [block] returns the special [COROUTINE_SUSPENDED] value, it means that suspend function did suspend the execution and will not return any result immediately.`」 (1)의 반환 타입 `Object` 가 이 **특별한 값**을 담을 자리다.
- ★★ **`CancellationException` 은 `java.util.concurrent.CancellationException` 의 타입 별칭**이다 — JVM 에서 **`Exception`** 의 자손이라 `catch (e: Exception)` 에 걸린다([49번 주제](../49-result-and-runcatching/) (4)) — 그것이 왜 문제인지는 [53번 주제](../53-structured-concurrency-job-cancellation-exceptions/)다.

## 문법 — 형태와 규칙

**형태** — 두 값을 `async` 로 동시에 받고, 직접 부르면 차례대로 받는다.

```kotlin
// form52.kt
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.measureTime

suspend fun fetchPrice(item: String): Int {
    delay(100)
    return item.length * 10
}

fun main() = runBlocking {
    val together = measureTime {
        val a = async { fetchPrice("apple") }
        val b = async { fetchPrice("kiwi") }
        println("async sum ${a.await() + b.await()}")
    }
    println("two 100ms fetches with async finished under 190ms: ${together < 190.milliseconds}")
    val oneByOne = measureTime {
        println("direct sum ${fetchPrice("apple") + fetchPrice("kiwi")}")
    }
    println("two direct calls took at least 200ms: ${oneByOne >= 200.milliseconds}")
}
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar form52.kt -d o52f =====
(exit 0)
===== java -cp o52f:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Form52Kt =====
async sum 90
two 100ms fetches with async finished under 190ms: true
direct sum 90
two direct calls took at least 200ms: true
(exit 0)
```

**규칙 불릿**

- **`suspend fun`** — 중단점(`delay`·`await`·다른 `suspend` 호출)을 가질 수 있는 함수. **코루틴이나 다른 `suspend` 함수 안에서만** 부른다((2)).
- **코루틴을 여는 다리** — `runBlocking { }`(스레드를 막는다 · `main`·테스트용) · `CoroutineScope.launch { }`(→ `Job`) · `CoroutineScope.async { }`(→ `Deferred<T>` · `await()`) — **전부 kotlinx-coroutines**((2)(4)).
- **`coroutineScope { }`** — `suspend` 함수 안에서 **자식들을 기다리는 영역**을 연다. 람다의 `this` 가 `CoroutineScope` 다([37번 주제](../37-lambdas-with-receiver-and-type-safe-builders/)의 수신자 람다).
- **`suspend` 함수를 그냥 부르면 차례대로** — 동시에 하려면 `async`/`launch`((4) · 형태 블록).
- **람다 안에서 부르려면** 그 람다가 `inline` 이거나 `suspend` 여야 한다((2)).

## 어디서 틀리나

1. ★★★ **`suspend` 를 「다른 스레드에서 돈다」로 읽는다.** 변환일 뿐이다 — 10만 개가 스레드 1개에서 돌았다((1)(3)).
2. ★★★ **`suspend` 함수를 부르면 동시에 돈다고 본다.** 그냥 부르면 **부른 쪽이 같이 멈추는 보통 호출**이다((4) · 형태 블록 — 직접 호출 둘은 200ms 이상).
3. ★★ **코루틴 안에서 `Thread.sleep` 을 쓴다.** 같은 스레드의 다른 코루틴이 전부 선다((3)).
4. ★★ **`async` 의 예외를 `await` 에서 잡았으니 끝났다고 본다.** 부모 scope 는 이미 취소됐다((4) · 53번 주제).
5. ★★ **`forEach { }` 안에서는 되는데 `Sequence.map { }` 안에서는 왜 안 되나 헤맨다.** `inline` 여부다((2)).
6. ★ **이미 코루틴 안에서 `runBlocking` 을 또 쓴다.** 그 스레드를 막는다((4)).
7. ★ **「코루틴은 가볍다」를 근거 없이 적는다.** 이 문서가 잰 것은 **스레드 수**뿐이다((3)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `suspend` 는 코루틴·`suspend` 함수 안에서만 호출 | ★★★ **언어 규칙**(컴파일 에러) | (2) |
| `suspend` 함수가 `Continuation` 을 더 받고 `Object` 를 돌려준다 | ★★ **JVM 백엔드의 변환**(CPS) — 논지는 [`언어-특성`](../../언어-특성/README.md) §6 | (1) |
| 상태 기계 클래스의 이름·필드 이름(`$twice$1` · `I$0` · `label`) | ★ **컴파일러 구현** — 이 판의 관찰 | (1) |
| `COROUTINE_SUSPENDED` 가 「중단됐다」 표지 | ★★ **stdlib 계약(KDoc)** | (5) |
| `launch`·`async`·`runBlocking`·`delay`·`yield` 의 동작 | ★★ **kotlinx-coroutines 1.11.0 의 계약** — 언어가 아니다 | (3)(4) |
| `runBlocking` 이 부른 스레드 하나에서 돈다 · 로그 순서 | ★ **이 판의 관찰**(라이브러리 구현) | (3)(4) |
| 「코루틴은 가볍다」 | **재지 않았다** | — |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 기다림이 있는 함수(I/O·타이머) | `suspend fun` | (1) — 기다리는 동안 스레드를 놓는다 |
| 여러 개를 동시에 받아 합친다 | `coroutineScope { async { } … await() }` | 형태 블록 |
| 결과 없이 따로 돌린다 | `launch { }` | (4) |
| `main`·테스트에서 코루틴 세계로 들어간다 | `runBlocking { }` | (4) — 스레드를 막는다 |
| 이미 코루틴 안 | `runBlocking` 대신 **`suspend` 그대로** | (4) |
| 블로킹 API(JDBC 등)를 불러야 한다 | 디스패처를 바꾼다 | [목록의 **54번 주제**](../54-coroutine-context-dispatchers-and-withcontext/) · [`언어-특성`](../../언어-특성/README.md) §6 |

## 핵심 문장

1. **`suspend` 는 컴파일러 변환이다** — `f(x: Int): Int` 가 JVM 에서 **`f(int, Continuation): Object`** 가 되고, 중단점이 있으면 **`label` 과 지역 변수 필드를 가진 상태 기계 클래스**가 생긴다.
2. 반환이 `Object` 인 까닭은 **`COROUTINE_SUSPENDED`** 표지를 돌려줄 수 있어야 해서다.
3. **`suspend` 는 코루틴이나 다른 `suspend` 함수 안에서만** 부른다 — 람다는 `inline` 이거나 `suspend` 여야 한다(이 격자에서 9 중 5 가 막혔다).
4. **코루틴 10만 개가 스레드 1개에서 돌았다** — `delay` 는 스레드를 놓고, `Thread.sleep` 은 붙잡는다.
5. **`async` 의 예외는 `await` 에서 나오지만, 부모 scope 는 이미 취소됐다.**

## 관련 자료

- [`../../언어-특성/README.md`](../../언어-특성/README.md) §6 — ★★★ 「코루틴 — 스레드가 아니라 컴파일러 변환이다」. **논지·가상 스레드 대비·블로킹 스택에서 안 쓰는 이유**는 거기다. 여기는 **그 변환을 `javap` 로 본 것**과 **호출 규칙**.
- [`cs/foundations/process-thread/`](../../../../process-thread/) — 스레드·프로세스 개념. 그쪽은 **OS 가 무엇을 스케줄하나**, 여기는 **그 위에서 코루틴이 스레드를 놓는 자리**.
- [10번 주제](../10-lambdas-and-higher-order-functions/) — ★ **선행.** 람다가 JVM 에서 무엇이 되나 · `inline` 이 람다를 펼치는 것 — (2)의 「`forEach` 안은 된다」가 거기서 온다.
- [34번 주제](../34-exceptions-nothing-and-try-expression/) — ★ **선행.** 검사 예외 없음 — `suspend` 함수의 예외도 서명에 안 적힌다.
- [37번 주제](../37-lambdas-with-receiver-and-type-safe-builders/) — `coroutineScope { }`·`launch { }` 의 `this` 가 수신자 람다다.
- [53번 주제](../53-structured-concurrency-job-cancellation-exceptions/) — 자식 하나가 실패·취소되면 형제와 부모가 어떻게 되나.
- [Python 51번](../../../python/syntax/51-asyncio-coroutine-basics/) — 부르기만 하면 **몸통 0줄**인 코루틴. Kotlin 은 부르는 쪽이 `suspend` 가 아니면 **컴파일이 안 된다.**
- [목록의 **54번 주제**](../54-coroutine-context-dispatchers-and-withcontext/) — `CoroutineContext`·디스패처·`withContext`.

## 용어 풀이

> **`suspend` 함수** — 실행 도중 **멈췄다가(중단) 나중에 이어서** 돌 수 있는 함수. 멈춘 동안 스레드를 놓는다.\
> 예: `suspend fun twice(x: Int): Int { delay(1); … }`.

> **중단점(suspension point)** — `suspend` 함수 안에서 **다른 `suspend` 함수를 부르는 자리**. 멈출 **수 있는** 자리다(반드시 멈추지는 않는다).

> **`Continuation`** — 「이 다음에 할 일」을 담은 객체. `suspend` 함수에 컴파일러가 몰래 넘기는 마지막 인자.

> **CPS(continuation-passing style)** — 결과를 돌려주는 대신 **「이어서 할 일」을 인자로 받아** 그리로 넘기는 꼴.

> **상태 기계(state machine)** — 「지금 몇 번째 단계인가(`label`)」를 기억해 두고, 다시 불리면 그 단계부터 이어 가는 구조.

> **`COROUTINE_SUSPENDED`** — `suspend` 함수가 「나는 지금 멈췄다 — 결과는 나중에」를 알리려고 돌려주는 특별한 값.

> **코루틴 빌더** — `launch`·`async`·`runBlocking` 처럼 **새 코루틴을 여는** 함수. kotlinx-coroutines 의 것이다.

> **`Job` / `Deferred<T>`** — `launch` 가 돌려주는 「작업 손잡이」 / `async` 가 돌려주는 「나중에 값이 올 손잡이」(`await()`).

## 더 들어가면

- **`invokeSuspend` 안** — 상태 기계의 나머지 절반(이어 들어올 때 `label` 을 올리고 `twice` 를 다시 부르는 쪽)은 `Cps52Kt$twice$1` 의 `javap -c` 에 있다. 이 문서는 서명과 필드까지만 실었다.
- **`suspendCoroutine` / `suspendCancellableCoroutine`** — 콜백 API 를 `suspend` 로 감싸는 다리. 돌리지 않았다.
- **`-Xdebug` 와 「was optimized out」** — 디버거에서 지역 변수가 사라지는 비용은 [`언어-특성`](../../언어-특성/README.md) §6 이 원고째 적는다. 이 문서는 확인하지 않았다.
