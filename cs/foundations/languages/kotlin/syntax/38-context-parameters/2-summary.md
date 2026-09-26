# kotlin/syntax/38 — context parameters — 2.2 실험 → 2.4.0 Stable — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Context parameters](https://kotlinlang.org/docs/context-parameters.html)(「Context parameters replace an older experimental feature called context receivers」 · 선언은 「`name: Type`」 꼴, 「You can use `_` as a context parameter name」 · 「To access its value explicitly, use `contextOf<T>()`」 · 「Kotlin resolves context parameters at the call site by searching for matching context values in the current scope. Kotlin matches them by their type. If multiple compatible values exist at the same scope level, the compiler reports an ambiguity.」) · [언어 기능·제안 상태표](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html)(context parameters — 「Available since 2.2.0, Stable since 2.4.0」 · context receivers — 「Revoked」).
> ★ 같은 문서의 「Experimental」 표시는 **명시 전달**(`-Xexplicit-context-arguments`) 한 절에만 붙어 있다 — 기능 전체가 아니다(열어서 확인).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 격자 24회 + 단독 10회(컴파일 실패 4벌) · `javac` 1회 · `java` 5회 · `javap` 1회 · stdlib 소스 jar 에서 `contextOf` 선언 1곳.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **판 격자의 「통과 N / M」은 스크립트가 스스로 센 것**이다.
> **버전** — context parameters 는 **2.2.0 에 실험으로 들어와 2.4.0 에 Stable**(상태표). 그 전신 context receivers 는 **1.6.20 실험 → 폐기**(문서가 1.6.20 의 what's new 로 링크한다).\
> ★★ **이 판에서 「2.2 실험」은 잴 수 없었다** — 그것은 **컴파일러 2.2.0 이 나왔을 때의 성질**이고, 이 머신의 컴파일러는 2.4.20 하나다. `-language-version` 을 낮춰도 **2.4.20 컴파일러가 그 판을 흉내 낼 뿐**이다((1)).
> **경계** — ★★★ **수신자 람다가 `Function1` 의 첫 인자로 내려가는 것**은 [37번 주제](../37-lambdas-with-receiver-and-type-safe-builders/) (4)가 이미 쟀다 — 여기서는 **context parameter 가 같은 자리에 앉는가**만 더한다((3)).\
> 확장 함수의 수신자는 [13번 주제](../13-extension-functions-and-properties/), `with`/`run` 이 암묵 수신자를 여는 것은 [14번 주제](../14-scope-functions/)가 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**판 격자 — `-language-version` × 플래그 × 두 문법의 컴파일 결과**」. 이 주제의 질문 「언제부터 되나 · 옛 문법은 어떻게 되나」는 **실행 결과가 아니라 컴파일러의 거부 여부**로만 답해진다. 둘째 창(에러 전문)이 「**수신자와 무엇이 다른가**」를 답한다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장** | 명세·공식 문서가 약속한 것 | ★★★ context parameter 는 **이름으로만** 쓴다 — 암묵 수신자가 **아니다** · 호출 자리에서 **타입으로** 찾는다 · 같은 층에 둘이면 **모호성 에러** · `_` 와 `contextOf<T>()` · context receivers 는 **폐기** |
| **구현(JVM 백엔드)** | kotlinc 가 JVM 으로 내리는 방식 | ★★ context parameter 가 **맨 앞 매개변수** · 확장 수신자보다 **더 앞** · 확장 함수와 **디스크립터가 같다** |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | ★ 판 격자의 진단 문구 · ★ `-Xcontext-parameters` 도움말이 아직 「experimental」이라 적는 것 · ★ **`-language-version 2.1` 에서도 플래그로 켜지는 것** |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 해시코드·주소·시간을 찍지 않았다 — 어느 `Logger` 인지는 **`tag` 문자열**로 가렸다 |
| 안 흔들린다 | 판 격자 24칸 · 통과 수 | 같은 컴파일러·같은 소스면 결정적이다 |
| 안 흔들린다 | `javap` 출력 · 진단 문구·`파일:줄:칸` · 모든 종료 코드 | 결정적이다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 바이트 단위로 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**context parameter 는 「이 일은 로거가 옆에 있을 때만 한다」는 출입 조건이다.** 함수를 부르는 사람이 로거를 **손에 쥐고 있으면**(`with(Logger(…)) { … }`) 컴파일러가 **알아서 건네준다.** 인자 목록에 적지 않아도 된다.
★ 그런데 건네받은 로거는 **이름표를 단 채로** 들어온다 — 안에서 `log.log(…)` 처럼 **이름을 불러야** 쓴다. 수신자 람다([37번 주제](../37-lambdas-with-receiver-and-type-safe-builders/))처럼 **방 자체가 로거가 되지는 않는다** — `log(…)` 만 쓰면 「그런 것 없다」다.
옛 형태(context receivers)는 **이름표 없이 방이 되는 쪽**이었고, 그래서 폐기됐다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 출입 조건 — 로거가 옆에 있을 것 | `context(log: Logger) fun work()` | (1)(2) |
| 손에 쥐고 있으면 알아서 건넨다 | 호출 자리에서 **타입으로** 찾는다 | (2) |
| 이름표를 달고 들어온다 | **이름으로만** 쓴다 — 암묵 수신자가 아니다 | (4) ★ |
| 이름표 없이 방이 되는 옛 형태 | context receivers(`context(Logger)`) — 폐기 | (1) |
| 누가 건넸는지 모르면 | 「`no context argument … found`」 · 둘이면 「`multiple potential …`」 | (4) |
| 건네받는 실체 | JVM 에서 **맨 앞 매개변수** | (3) |

```text
   context(log: Logger)                  호출 자리                          JVM
   fun work(x: Int): Int                 with(Logger("A")) {                work(Logger, int)
     |                                     work(3)   ─── 컴파일러가 ───>      ^^^^^^ 맨 앞 매개변수
     | 몸통 안에서                           }        「Logger 타입이           invokestatic work(logger, 3)
     |   log.log("…")   OK  (이름으로)                  스코프에 있나?」
     |   log("…")       에러 (수신자 아님)               있으면 그것을 넘긴다
     |   this           에러 (this 없음)                 없으면 에러 · 같은 층에 둘이면 에러

   수신자(37번 주제)                     context parameter
   fun Logger.work(x)                    context(log: Logger) fun work(x)
     this = Logger, 멤버를 이름만으로       this 없음, 이름(log)으로만
     JVM: work(Logger, int)               JVM: work(Logger, int)      ← 디스크립터가 같다
```

## 이 주제가 답하려는 질문

1. context parameters 는 **어느 판부터** 플래그 없이 되나 — 옛 context receivers 는 지금 어떻게 되나.
2. context parameter 는 **수신자와 무엇이 다른가** — 몸통 안에서, 호출 자리에서.
3. JVM 에서 context parameter 는 **어디에** 앉나 — 수신자와 같은 자리인가.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **판 격자 — 컴파일 통과 수** | `-language-version` 2.1\~2.4 × 플래그 셋 × 두 문법((1)) | ★ **본체 창** |
| ★★ **컴파일 에러 전문** | 옛 문법의 거부 · 이름으로만 쓰는 것 · 호출 자리에 context 가 없을 때((1)(4)) | 이 갈래의 기본 창 |
| ★★ **`javap -s`** | context parameter 의 자리 · 확장 함수와 디스크립터 대조((3)) | [37번 주제](../37-lambdas-with-receiver-and-type-safe-builders/) (4)와 같은 창 |
| ★ **실행 로그** | 어느 `Logger` 가 건네졌나(`tag`) — 중첩 `with` 에서((2)) | — |
| ★ **Java 에서 던지기** | Java 는 그것을 **평범한 첫 인자**로 넘긴다((3)) | [36번 주제](../36-function-types-fun-interface-and-sam-conversion/)의 창 |
| **제5의 상태 — 「2.2 실험」** | 컴파일러 2.2.0 이 **없어** 그 판의 실험 표시를 직접 못 본다 → **2.4.20 의 `-language-version 2.2` 와 도움말 문구**로 물었다((1)) | ★ 바꾼 창은 「2.2.0 컴파일러가 무엇을 경고했나」를 **못 본다** |
| **부적용 — 실행 시간·할당** | context 전달은 **인자 하나**다((3)) — 잴 비용이 따로 없다. 「느리다/빠르다」는 재지 않았다 | — |

### (1) ★★★ 판 격자 — 두 문법 × `-language-version` × 플래그

**언제 쓰나** — 빌드의 `languageVersion` 이 2.4 가 아닐 때, 또는 옛 코드에 `context(Logger)` 가 남아 있을 때.

두 파일은 **한 줄만** 다르다 — 새 문법 `context(log: Logger)` 과 옛 문법 `context(Logger)`, 그리고 몸통이 `log.log(…)` 인가 `log(…)` 인가.

```kotlin
// ctxp.kt
class Logger(val tag: String) { fun log(m: String) = println("[$tag] $m") }

context(log: Logger)
fun work(x: Int): Int { log.log("work $x"); return x * 2 }

fun main() {
    with(Logger("A")) { println(work(3)) }
}
```

```kotlin
// ctxr.kt
class Logger(val tag: String) { fun log(m: String) = println("[$tag] $m") }

context(Logger)
fun work(x: Int): Int { log("work $x"); return x * 2 }

fun main() {
    with(Logger("A")) { println(work(3)) }
}
```

격자를 도는 스크립트 — 칸마다 `kotlinc` 를 새로 부르고 종료 코드와 `error:` 줄을 모은다.

```python
# grid38.py
import re
import subprocess

FILES = ["ctxp.kt", "ctxr.kt"]
LVS = ["2.1", "2.2", "2.3", "2.4"]
FLAGS = ["", "-Xcontext-parameters", "-Xcontext-receivers"]
DIAG = re.compile(r"^(?:\S+:\d+:\d+: )?(error|warning): (.*)$")

print("file\tlv\tflag\texit\twarnings\terrors")
ok = total = 0
for f in FILES:
    for lv in LVS:
        for fl in FLAGS:
            out_dir = "o38g-" + f[:-3] + "-" + lv + "-" + (fl.lstrip("-X") or "none")
            cmd = ["kotlinc", "-language-version", lv] + ([fl] if fl else []) + [f, "-d", out_dir]
            p = subprocess.run(cmd, capture_output=True, text=True)
            errs, warns = [], 0
            for line in (p.stdout + p.stderr).splitlines():
                m = DIAG.match(line)
                if m and m.group(1) == "error":
                    errs.append(m.group(2))
                elif m:
                    warns += 1
            row = [f, lv, fl or "(none)", str(p.returncode), str(warns), " + ".join(errs) or "-"]
            if len(row) != 6 or any("\t" in c for c in row):
                raise SystemExit("cell count mismatch: " + repr(row))
            print("\t".join(row))
            total += 1
            if p.returncode == 0:
                ok += 1
print(f"cells that compiled: {ok} / {total}")
```

```text
===== python3 grid38.py =====
file	lv	flag	exit	warnings	errors
ctxp.kt	2.1	(none)	1	1	the feature "context parameters" is only available since language version 2.4 + to call contextual declarations, specify the '-Xcontext-parameters' compiler option.
ctxp.kt	2.1	-Xcontext-parameters	0	1	-
ctxp.kt	2.1	-Xcontext-receivers	1	1	experimental context receivers are superseded by context parameters.
ctxp.kt	2.2	(none)	1	0	the feature "context parameters" is only available since language version 2.4 + to call contextual declarations, specify the '-Xcontext-parameters' compiler option.
ctxp.kt	2.2	-Xcontext-parameters	0	0	-
ctxp.kt	2.2	-Xcontext-receivers	1	0	experimental context receivers are superseded by context parameters.
ctxp.kt	2.3	(none)	1	0	the feature "context parameters" is only available since language version 2.4 + to call contextual declarations, specify the '-Xcontext-parameters' compiler option.
ctxp.kt	2.3	-Xcontext-parameters	0	0	-
ctxp.kt	2.3	-Xcontext-receivers	1	0	experimental context receivers are superseded by context parameters.
ctxp.kt	2.4	(none)	0	0	-
ctxp.kt	2.4	-Xcontext-parameters	0	1	-
ctxp.kt	2.4	-Xcontext-receivers	1	0	experimental context receivers are superseded by context parameters.
ctxr.kt	2.1	(none)	1	1	experimental context receivers are superseded by context parameters. + the feature "context parameters" is only available since language version 2.4 + unresolved reference 'log'. + to call contextual declarations, specify the '-Xcontext-parameters' compiler option.
ctxr.kt	2.1	-Xcontext-parameters	1	1	context parameters must be named. Use '_' to declare an anonymous context parameter. + unresolved reference 'log'.
ctxr.kt	2.1	-Xcontext-receivers	1	1	experimental context receivers are superseded by context parameters. + experimental context receivers are superseded by context parameters. + unresolved reference 'log'.
ctxr.kt	2.2	(none)	1	0	experimental context receivers are superseded by context parameters. + the feature "context parameters" is only available since language version 2.4 + unresolved reference 'log'. + to call contextual declarations, specify the '-Xcontext-parameters' compiler option.
ctxr.kt	2.2	-Xcontext-parameters	1	0	context parameters must be named. Use '_' to declare an anonymous context parameter. + unresolved reference 'log'.
ctxr.kt	2.2	-Xcontext-receivers	1	0	experimental context receivers are superseded by context parameters. + experimental context receivers are superseded by context parameters. + unresolved reference 'log'.
ctxr.kt	2.3	(none)	1	0	experimental context receivers are superseded by context parameters. + the feature "context parameters" is only available since language version 2.4 + unresolved reference 'log'. + to call contextual declarations, specify the '-Xcontext-parameters' compiler option.
ctxr.kt	2.3	-Xcontext-parameters	1	0	context parameters must be named. Use '_' to declare an anonymous context parameter. + unresolved reference 'log'.
ctxr.kt	2.3	-Xcontext-receivers	1	0	experimental context receivers are superseded by context parameters. + experimental context receivers are superseded by context parameters. + unresolved reference 'log'.
ctxr.kt	2.4	(none)	1	0	context parameters must be named. Use '_' to declare an anonymous context parameter. + unresolved reference 'log'.
ctxr.kt	2.4	-Xcontext-parameters	1	1	context parameters must be named. Use '_' to declare an anonymous context parameter. + unresolved reference 'log'.
ctxr.kt	2.4	-Xcontext-receivers	1	0	experimental context receivers are superseded by context parameters. + context parameters must be named. Use '_' to declare an anonymous context parameter. + unresolved reference 'log'.
cells that compiled: 5 / 24
(exit 0)
```

- ★★★ **통과는 24칸 중 5칸**이고 **전부 새 문법(`ctxp.kt`)** 이다 — 2.1·2.2·2.3 은 **`-Xcontext-parameters` 가 있을 때만**, **2.4 는 플래그 없이도** 통과한다. 플래그 없는 2.1\~2.3 은 「`the feature "context parameters" is only available since language version 2.4`」 — **컴파일러 스스로 경계를 2.4 라고 말한다.**
- ★★★ **옛 문법(`ctxr.kt`)은 12칸 전부 실패**다. 2.4 에서 옛 문법을 새 문법으로 읽어 「`context parameters must be named. Use '_' to declare an anonymous context parameter.`」가 되고, 플래그 없는 2.1\~2.3 은 「`experimental context receivers are superseded by context parameters.`」가 먼저 나온다.
- ★★ **`-Xcontext-receivers` 는 어느 판에서도 통과시키지 않는다** — 새 문법 파일에 줘도 실패다(「`superseded`」). 플래그 자체가 거부된다.
- ★★ **2.4 + `-Xcontext-parameters` 는 경고 1** — 「`the argument '-Xcontext-parameters' is redundant for the current language version 2.4.`」(아래 블록). 2.1 은 모든 칸에 경고 1 — 판 자체가 deprecated 라는 경고다(격자는 경고를 **개수로만** 셌다).
- ★ **2.1 에서도 플래그로 켜진다** — 「2.2 에 실험으로 들어왔다」는 **컴파일러 판**의 이야기이고, `-language-version` 은 **2.4.20 컴파일러가 흉내 내는 언어 판**이라 둘이 같은 축이 아니다. 격자로 「2.2 실험」을 **확인하지는 못했다**(제5의 상태 — (0)).

대표 칸의 전문 — 새 문법은 2.4 기본 · 2.4 플래그 있음 · 2.3 플래그 없음 · 2.3 플래그 있음, 옛 문법은 2.4 기본 · `-Xcontext-receivers`.

```text
===== kotlinc ctxp.kt -d o38p =====
(exit 0)
===== java -cp o38p:kotlin-stdlib.jar CtxpKt =====
[A] work 3
6
(exit 0)
===== kotlinc -Xcontext-parameters ctxp.kt -d o38p2 =====
warning: the argument '-Xcontext-parameters' is redundant for the current language version 2.4.
(exit 0)
===== kotlinc -language-version 2.3 ctxp.kt -d o38p3 =====
ctxp.kt:3:1: error: the feature "context parameters" is only available since language version 2.4
context(log: Logger)
^^^^^^^^^^^^^^^^^^^^
ctxp.kt:7:33: error: to call contextual declarations, specify the '-Xcontext-parameters' compiler option.
    with(Logger("A")) { println(work(3)) }
                                ^^^^
(exit 1)
===== kotlinc -language-version 2.3 -Xcontext-parameters ctxp.kt -d o38p4 =====
(exit 0)
```

```text
===== kotlinc ctxr.kt -d o38r =====
ctxr.kt:3:9: error: context parameters must be named. Use '_' to declare an anonymous context parameter.
context(Logger)
        ^^^^^^
ctxr.kt:4:25: error: unresolved reference 'log'.
fun work(x: Int): Int { log("work $x"); return x * 2 }
                        ^^^
(exit 1)
===== kotlinc -Xcontext-receivers ctxr.kt -d o38r2 =====
error: experimental context receivers are superseded by context parameters.
Remove the '-Xcontext-receivers' compiler argument and migrate to the new syntax.

See the context parameters proposal for more details: https://kotl.in/context-parameters
ctxr.kt:3:9: error: context parameters must be named. Use '_' to declare an anonymous context parameter.
context(Logger)
        ^^^^^^
ctxr.kt:4:25: error: unresolved reference 'log'.
fun work(x: Int): Int { log("work $x"); return x * 2 }
                        ^^^
(exit 1)
```

```text
===== kotlinc -X | grep -E '^  -X(context-parameters|context-receivers|explicit-context-arguments) ' =====
  -Xcontext-parameters       Enable experimental context parameters.
  -Xcontext-receivers        Enable experimental context receivers.
  -Xexplicit-context-arguments Enable explicit passing of context arguments using named argument syntax.
(exit 0)
```

- ★★ **`-Xcontext-receivers` 의 전문은 이주 안내까지 한다** — 「`Remove the '-Xcontext-receivers' compiler argument and migrate to the new syntax.`」.
- ★ **도움말은 아직 「`Enable experimental context parameters.`」** 라고 적는다 — 2.4 에서 Stable 인데도. 도움말 문구는 상태표보다 느리다(**이 판의 관찰**).
- ★ `-Xexplicit-context-arguments`(이름 붙인 인자로 **명시 전달**)가 따로 있다 — 문서가 「Experimental」이라 적은 것은 이쪽이다. 이 문서는 **던지지 않았다**.

### (2) ★★ 호출 자리 — 타입으로 찾고, 안쪽이 이긴다

```kotlin
// ctxsig.kt
class Logger(val tag: String) { fun log(m: String) = println("[$tag] $m") }
class Tx(val id: Int)

context(lg: Logger)
fun ctx1(x: Int): Int { lg.log("ctx1 $x"); return x }

fun Logger.ext1(x: Int): Int { log("ext1 $x"); return x }

context(lg: Logger, tx: Tx)
fun String.both(n: Int): String = "$this$n tag=${lg.tag} tx=${tx.id}"

context(_: Logger)
fun anon(): String = contextOf<Logger>().tag

fun main() {
    with(Logger("A")) {
        println(ctx1(1))
        println(ext1(2))
        with(Tx(7)) { println("s".both(3)) }
        println(anon())
        with(Logger("B")) { println(ctx1(4)) }
    }
}
```

```text
===== kotlinc ctxsig.kt -d o38s =====
(exit 0)
===== java -cp o38s:kotlin-stdlib.jar CtxsigKt =====
[A] ctx1 1
1
[A] ext1 2
2
s3 tag=A tx=7
A
[B] ctx1 4
4
(exit 0)
```

- ★★★ **`with(Logger("A")) { ctx1(1) }` 가 `[A] ctx1 1`** — `ctx1` 의 인자 목록에는 `x` 하나뿐인데 `Logger` 가 건네졌다. `with` 가 연 **암묵 수신자**(`Logger("A")`)를 컴파일러가 **타입으로** 골랐다.
- ★★ **중첩 `with` 에서는 안쪽이 이긴다** — `with(Logger("B")) { ctx1(4) }` 가 `[B] ctx1 4`. 문서의 「**같은 층에** 둘이면 모호성」은 **다른 층**이면 가까운 쪽을 고른다는 뜻이다.
- ★★ **context 가 둘 + 확장 수신자** — `"s".both(3)` 이 `s3 tag=A tx=7`. `Logger` 는 바깥 `with` 에서, `Tx` 는 안쪽 `with` 에서 왔다. **타입마다 따로** 찾는다.
- ★ **`_` + `contextOf<Logger>()`** — 이름 없이 받아 두고 필요할 때 **타입으로 꺼낸다**(`A`).

### (3) ★★ JVM 에서 — 맨 앞 매개변수, 확장 수신자와 같은 자리

```text
===== javap -s -p o38s/CtxsigKt.class =====
Compiled from "ctxsig.kt"
public final class CtxsigKt {
  public static final int ctx1(Logger, int);
    descriptor: (LLogger;I)I

  public static final int ext1(Logger, int);
    descriptor: (LLogger;I)I

  public static final java.lang.String both(Logger, Tx, java.lang.String, int);
    descriptor: (LLogger;LTx;Ljava/lang/String;I)Ljava/lang/String;

  public static final java.lang.String anon(Logger);
    descriptor: (LLogger;)Ljava/lang/String;

  public static final void main();
    descriptor: ()V

  public static void main(java.lang.String[]);
    descriptor: ([Ljava/lang/String;)V
}
(exit 0)
```

```java
// JCtx.java
public class JCtx {
    public static void main(String[] args) {
        Logger j = new Logger("J");
        System.out.println(CtxsigKt.ctx1(j, 5));
        System.out.println(CtxsigKt.ext1(j, 6));
        System.out.println(CtxsigKt.both(j, new Tx(8), "s", 9));
    }
}
```

```text
===== javac -cp o38s -d o38s JCtx.java =====
(exit 0)
===== java -cp o38s:kotlin-stdlib.jar JCtx =====
[J] ctx1 5
5
[J] ext1 6
6
s9 tag=J tx=8
(exit 0)
```

```text
   Kotlin 선언                                    JVM 디스크립터
   context(lg: Logger) fun ctx1(x: Int)     ───>  ctx1(LLogger;I)I
   fun Logger.ext1(x: Int)                  ───>  ext1(LLogger;I)I              ← 한 글자도 같은 모양
   context(lg: Logger, tx: Tx)
   fun String.both(n: Int)                  ───>  both(LLogger;LTx;Ljava/lang/String;I)
                                                        ^^^^^^^^^^^ ^^^^^^^^^^^^^^^^
                                                        context 둘   그다음이 확장 수신자
   context(_: Logger) fun anon()            ───>  anon(LLogger;)                ← 이름 없어도 자리는 있다
```

- ★★★ **context parameter 는 맨 앞 매개변수**다 — `ctx1(Logger, int)`. 그리고 **확장 함수 `ext1(Logger, int)` 과 디스크립터가 같다.** [37번 주제](../37-lambdas-with-receiver-and-type-safe-builders/) (4)가 수신자 람다에서 본 「수신자 = 첫 인자」와 **같은 모양**이다.
- ★★ **둘을 가르는 것은 JVM 이 아니라 Kotlin 컴파일러**다 — 몸통 안에서 `this` 가 되느냐((4))는 **메타데이터**가 정하고, 바이트코드 서명에는 흔적이 없다(37 (4)의 `ExtensionFunctionType` 과 같은 결론을 **이 판에서 다시 재지는 않았다** — 여기서 본 것은 디스크립터가 같다는 것까지다).
- ★★ **context 가 확장 수신자보다 앞**이다 — `both(Logger, Tx, String, int)`. 선언 순서(`context(…)` → `String.` → `(n)`)가 그대로 매개변수 순서다.
- ★ **Java 는 그냥 넘긴다** — `CtxsigKt.ctx1(j, 5)`. Java 에게는 **「암묵으로 건넨다」가 없다.**

### (4) ★★★ 수신자와의 차이 — 이름으로만 쓴다

첫 함수 `r1` 은 **확장 함수**(수신자)라 대조로 둔 것이다. 나머지가 context parameter 다.

```kotlin
// ctxbad.kt
class Logger(val tag: String) { fun log(m: String) = println("[$tag] $m") }

fun Logger.r1() { log("r1"); println(tag); println(this.tag) }

context(lg: Logger)
fun c1() { log("c1") }

context(lg: Logger)
fun c2() { println(tag) }

context(lg: Logger)
fun c3() { println(this.tag) }

context(lg: Logger)
fun c4(): String = lg.tag

fun g1(): String = c4()

context(a: Logger, b: Logger)
fun g2(): String = c4()

fun g3(): Logger = contextOf<Logger>()
```

```text
===== kotlinc ctxbad.kt -d o38b =====
ctxbad.kt:6:12: error: unresolved reference 'log'.
fun c1() { log("c1") }
           ^^^
ctxbad.kt:9:20: error: unresolved reference 'tag'.
fun c2() { println(tag) }
                   ^^^
ctxbad.kt:12:20: error: 'this' is not defined in this context.
fun c3() { println(this.tag) }
                   ^^^^
ctxbad.kt:12:25: error: unresolved reference 'tag'.
fun c3() { println(this.tag) }
                        ^^^
ctxbad.kt:17:20: error: no context argument for 'lg: Logger' found.
fun g1(): String = c4()
                   ^^
ctxbad.kt:20:20: error: multiple potential context arguments for 'lg: Logger' in scope.
fun g2(): String = c4()
                   ^^
ctxbad.kt:22:20: error: no context argument for 'context: A' found.
fun g3(): Logger = contextOf<Logger>()
                   ^^^^^^^^^
(exit 1)
```

- ★★★ **`r1`(3번째 줄)은 에러가 없다** — 확장 함수 안에서는 `log(…)`·`tag`·`this.tag` 가 전부 된다. **수신자는 암묵 수신자**다.
- ★★★ **같은 세 가지가 context parameter 에서는 전부 막힌다** —
  `log("c1")` → 「`unresolved reference 'log'.`」 · `tag` → 「`unresolved reference 'tag'.`」 · `this.tag` → 「`'this' is not defined in this context.`」.
  **context parameter 는 몸통 안에서 암묵 수신자가 되지 않는다** — `lg.log(…)` 처럼 **이름으로만** 쓴다.
- ★★ **옛 문법(context receivers)은 바로 이 자리가 달랐다** — `context(Logger)` 는 `Logger` 를 **암묵 수신자로** 열어 `log(…)` 를 이름 없이 부르게 했다((1)의 `ctxr.kt` 몸통). 새 문법은 그것을 **버렸다** — 2.4 가 옛 파일에서 「`unresolved reference 'log'.`」를 내는 것이 그 흔적이다.
- ★★ **호출 자리에 없으면** 「`no context argument for 'lg: Logger' found.`」(17번째 줄) · **같은 층에 둘이면** 「`multiple potential context arguments for 'lg: Logger' in scope.`」(20번째 줄 — `a`·`b` 가 둘 다 `Logger`).
- ★ **`contextOf<Logger>()` 도 context 가 있어야** 한다 — 없는 자리에서는 「`no context argument for 'context: A' found.`」(22번째 줄). 문구의 `context: A` 는 **`contextOf` 자신의 context parameter** 다 — stdlib 소스를 열면 그렇게 선언돼 있다.

```text
===== unzip -o -q kotlin-stdlib-sources.jar commonMain/kotlin/contextParameters/ContextOf.kt =====
(exit 0)
===== grep -n -B2 'fun <A> contextOf' commonMain/kotlin/contextParameters/ContextOf.kt =====
27-@SinceKotlin("2.2")
28-context(context: @NoInfer A)
29:public inline fun <A> contextOf(): @NoInfer A = context
(exit 0)
```

- ★★ **`contextOf` 는 그 자체가 context parameter 하나를 받아 그대로 돌려주는 `inline` 함수**다 — `context(context: @NoInfer A)` · `= context`. 특별한 언어 장치가 아니라 **같은 규칙을 쓰는 평범한 함수**다. `@SinceKotlin("2.2")` — 상태표의 「2.2.0 도입」과 맞는다.

## 문법 — 형태와 규칙

**형태** — context 둘을 받는 함수 하나와 그것을 여는 호출 자리.

```kotlin
// form38.kt
class Logger(val tag: String) { fun log(m: String) = println("[$tag] $m") }
class Clock(val now: Long)

context(lg: Logger, clock: Clock)
fun audit(event: String) = lg.log("$event at ${clock.now}")

fun main() {
    with(Logger("app")) {
        with(Clock(100L)) {
            audit("start")
            audit("stop")
        }
    }
}
```

```text
===== kotlinc form38.kt -d o38z =====
(exit 0)
===== java -cp o38z:kotlin-stdlib.jar Form38Kt =====
[app] start at 100
[app] stop at 100
(exit 0)
```

**규칙 불릿**

- 선언 — **`context(이름: 타입, …) fun f(…)`** · 이름이 필요 없으면 **`_`**((2)).
- 몸통 — **이름으로만** 쓴다. `this` 도 멤버의 암묵 호출도 없다((4)).
- 호출 — 인자 목록에 **안 적는다.** 호출 자리의 스코프(암묵 수신자·다른 context parameter)에서 **타입으로** 찾는다((2)).
- 가까운 층이 이긴다 · **같은 층에 같은 타입 둘**이면 모호성 에러((2)(4)).
- **`contextOf<T>()`** — 이름 없이 받은 것을 꺼낸다((2)).
- **2.4 부터 플래그 없이** — 그 전 `-language-version` 은 `-Xcontext-parameters` 가 필요하다((1)).
- 옛 **`context(Type)`**(context receivers)은 **어느 판에서도 통과하지 않는다**((1)).

## 어디서 틀리나

1. ★★★ **context parameter 를 수신자처럼 쓴다.** `log(…)`·`tag`·`this` 가 전부 에러다((4)) — **이름으로** 부른다.
2. ★★★ **옛 `context(Logger)` 코드를 이름만 붙이면 된다고 믿는다.** 이름을 붙이면 몸통의 `log(…)` 가 **unresolved** 로 바뀐다((1)(4)) — 몸통까지 고쳐야 한다.
3. ★★ **`-Xcontext-receivers` 로 옛 코드를 살리려 한다.** 이 판은 그 플래그 자체를 거부한다((1)).
4. ★★ **`languageVersion` 을 낮춘 모듈에서 플래그를 빠뜨린다.** 2.3 이하는 「`only available since language version 2.4`」((1)).
5. ★★ **같은 타입 두 개를 context 로 받는다.** 그 안에서 그 타입을 요구하는 함수를 부르면 **모호성 에러**다((4)).
6. ★ **Java 에서도 알아서 건네질 거라 믿는다.** Java 는 **첫 인자로 직접** 넘긴다((3)).
7. ★ **「2.2 에서 실험」을 `-language-version 2.2` 로 확인했다고 적는다.** 그 격자는 **2.4.20 컴파일러**의 동작이다((1)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| 이름으로만 쓴다 · 암묵 수신자가 아니다 | ★★★ **언어 보장** | 문서 · (4) |
| 호출 자리에서 **타입으로** 찾는다 · 같은 층 둘이면 모호성 | ★★★ **언어 보장** | 문서 · (2)(4) |
| 가까운 층이 이긴다 | **언어 보장**(해소 규칙 — 「same scope level」의 뜻) · 이 판에서 확인 | (2) |
| `_` · `contextOf<T>()` | **언어 보장** | 문서 · (2) |
| context receivers 폐기 | **언어의 결정**(상태표 「Revoked」) | (1) |
| 2.4.0 Stable · 2.2.0 도입 | **언어 판의 사실**(상태표) — ★ 2.2 쪽은 **이 판에서 못 쟀다** | (1) |
| context parameter → **맨 앞 매개변수** · 확장 수신자보다 앞 | ★★ **JVM 백엔드의 구현** | (3) |
| 확장 함수와 디스크립터가 같다 | ★ **JVM 백엔드의 구현** | (3) |
| `-language-version 2.1` 에서 플래그로 켜지는 것 · 도움말의 「experimental」 | **이 판(2.4.20)의 관찰** | (1) |
| 진단 문구 | **이 판의 산출물** | (1)(4) |

★★ **가장 조심할 자리** — 「context parameter 는 JVM 에서 첫 인자다」는 **구현**이다. 문서가 약속하는 것은 **소스 쪽 규칙**(이름·타입 해소·모호성)이고, 매개변수 순서를 약속하지 않는다. Java 에서 부르는 코드를 짤 때 기대는 것은 **이 판의 `javap`** 다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 로거·트랜잭션·클럭처럼 **여러 함수를 가로질러** 흐르는 의존성 | ★ context parameter | (2) — 인자 목록이 조용해진다 |
| 그 객체의 **멤버를 이름만으로** 부르는 블록(DSL) | 수신자 람다 | [37번 주제](../37-lambdas-with-receiver-and-type-safe-builders/) — context parameter 는 암묵 수신자가 아니다((4)) |
| 수신자가 **둘 이상** 필요하다 | ★ context parameter | 수신자는 하나뿐이다 · context 는 여럿(`both` — (2)) |
| 같은 타입을 둘 받아야 한다 | 명시 인자 | 모호성 에러((4)) |
| Java 도 부를 공개 API | 명시 인자 또는 context — Java 는 **첫 인자로** 넘긴다 | (3) |
| `languageVersion` 이 2.4 미만인 모듈 | `-Xcontext-parameters` 또는 명시 인자 | (1) |
| 옛 `context(Type)` 코드 | **이름을 붙이고 몸통도 고친다** | (1)(4) |

## 핵심 문장

1. context parameters 는 **2.4 에서 플래그 없이** 되고, 그 아래 `-language-version` 은 `-Xcontext-parameters` 가 있어야 한다 — 옛 context receivers 는 **어느 판에서도** 안 된다(격자 5 / 24).
2. context parameter 는 **이름으로만** 쓴다 — 몸통 안에서 `this` 도, 멤버의 암묵 호출도 없다. **그것이 수신자와의 차이**다.
3. 호출 자리에서 컴파일러가 **타입으로** 찾아 건넨다 — 가까운 층이 이기고, 같은 층에 둘이면 에러다.
4. JVM 에서 context parameter 는 **맨 앞 매개변수**이고, 확장 함수와 **디스크립터가 같다** — 둘을 가르는 것은 Kotlin 컴파일러뿐이다.

## 관련 자료

- [37번 주제](../37-lambdas-with-receiver-and-type-safe-builders/) — ★★ **선행.** 수신자 람다 · 수신자가 `Function1` 의 첫 인자. 그쪽은 「**수신자가 하나일 때 무엇이 헷갈리나**」까지, 여기는 「**암묵 인자를 타입으로 넘기되 수신자로는 안 여는 것**」부터.
- [13번 주제](../13-extension-functions-and-properties/) — 확장 함수. (3)의 `ext1` 이 그것이다.
- [14번 주제](../14-scope-functions/) — `with` 가 암묵 수신자를 연다 — (2)에서 context 를 공급한 장치.
- [36번 주제](../36-function-types-fun-interface-and-sam-conversion/) — Java 쪽에서 Kotlin 함수를 부르는 창.
- [39번 주제](../39-java-interop-annotations/) — Java 에서 부를 API 의 모양을 바꾸는 애너테이션들.

## 용어 풀이

> **context parameter** — `context(이름: 타입)` 으로 선언하는 매개변수. 호출 자리에서 **타입으로 찾아** 암묵으로 건네진다.\
> 예: `context(log: Logger) fun work(x: Int)`.

> **context receivers** — context parameters 의 전신(1.6.20 실험). `context(Logger)` 처럼 **이름 없이** 받아 **암묵 수신자로** 열었다. 폐기됐다.

> **context argument** — 호출 자리에서 context parameter 에 건네지는 **값**. 이 판의 진단 문구가 쓰는 말이다.

> **`contextOf<T>()`** — 이름 없이(`_`) 받은 context 를 **타입으로** 꺼내는 stdlib 함수.

> **암묵 수신자(implicit receiver)** — `this.` 를 안 적어도 멤버를 찾아 주는 수신자. `with`·수신자 람다·확장 함수가 연다. **context parameter 는 이것이 아니다.**

> **`-language-version`** — 컴파일러가 **어느 언어 판처럼** 굴지 고르는 옵션. 컴파일러 판 자체를 바꾸지는 않는다.

## 더 들어가면

- **왜 이름을 강제하나** — 설계 문서가 옛 형태와의 차이를 요약한다고 공식 문서가 링크한다(KEEP 의 「summary of changes」). 이 문서는 그 문서를 **열어 확인하지 않았다** — (4)에서 보인 것은 「이름 없이 멤버를 부르는 것이 **막힌다**」는 결과까지다.
- **명시 전달** — `-Xexplicit-context-arguments` 로 context 를 **이름 붙인 인자처럼** 넘길 수 있다고 도움말이 적는다((1)). 실험 기능이라 **던지지 않았다.**
- **context 를 받는 함수 타입** — 람다에 context 를 요구하는 꼴이다. 한 벌만 던졌다 — 함수 타입 쪽은 **이름 없이 타입만** 적고, 람다 안에서는 `contextOf` 로 꺼낸다.

```kotlin
// ctxfn.kt
class Logger(val tag: String)
fun run1(block: context(Logger) () -> String): String = with(Logger("L")) { block() }
fun main() { println(run1 { contextOf<Logger>().tag }) }
```

```text
===== kotlinc ctxfn.kt -d o38f =====
(exit 0)
===== java -cp o38f:kotlin-stdlib.jar CtxfnKt =====
L
(exit 0)
```

  이것이 JVM 에서 무엇이 되는지(`Function1` 인가), 수신자 람다와 무엇이 갈리는지는 **재지 않았다** — [37번 주제](../37-lambdas-with-receiver-and-type-safe-builders/) (4)와 나란히 재 볼 다음 자리다.
