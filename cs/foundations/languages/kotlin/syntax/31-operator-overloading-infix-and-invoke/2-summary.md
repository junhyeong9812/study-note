# kotlin/syntax/31 — 연산자 오버로딩·중위 함수·`invoke` 규약 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Operator overloading](https://kotlinlang.org/docs/operator-overloading.html)(`operator` 수식어 · `+=` 의 모호성 규칙 · `==` 는 오버로드가 아니라 `equals` 재정의 · `..<` → `rangeUntil`) · [Functions — Infix notation](https://kotlinlang.org/docs/functions.html#infix-notation).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> `kotlinc` 6회(컴파일 실패 2벌) · `java` 4회 · `javap` 4회(하나는 `python3` 격자 스크립트로 셌다).\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. 소스 펜스의 첫 줄 배너도 캡처가 찍었다.
> **버전** — `operator` 규약·`infix`·`invoke` 는 1.0. ★ **`..<`(`rangeUntil`)는 1.7.20 도입 · 1.8.0 Stable** 이다([07번 주제](../07-loops-ranges-and-labels/) 머리말) — **이 판은 `-language-version 1.9` 이하를 거부하므로 그 경계를 재지 못했다**(07번이 같은 이유로 못 잰 것을 인용한다).
> **경계** — `infix` 라는 **호출 형태와 우선순위**(`1 shl 2 + 3` 이 `32`)는 [09번 주제](../09-varargs-spread-local-and-infix-functions/) (9)가 **이미 재 둔 정본**이다 — 여기서 다시 재지 않는다.\
> **확장 함수 일반**은 [13번 주제](../13-extension-functions-and-properties/), `componentN` 은 [30번 주제](../30-destructuring-declarations-and-componentn/), `getValue`/`setValue` 는 [17번 주제](../17-delegated-properties/), `iterator()` 는 [07번 주제](../07-loops-ranges-and-labels/) (5), **`==`·`equals` 는 [32번 주제](../32-equality-and-equals-contract/)** 가 정본이다.
> **대비** — Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **30번**([`30-operator-overloading-std-ops-index-and-deref/`](../../../rust/syntax/30-operator-overloading-std-ops-index-and-deref/)) — 연산자가 **트레이트**이고 `a + b` 가 **`a` 를 옮긴다.** C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **22번**·**23번**(연산자 오버로딩·`<=>`)은 아직 폴더가 없다.
> 이 본문은 Claude 작성이다(원고 없음).

★ **본체는 첫째 창이다** — 「**`javap -c` 가 기호 자리에 박은 메서드 호출**」. 기호가 **어느 이름으로 풀리는지**는 외우는 표가 아니라 바이트코드에 적혀 있다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장** | 명세·공식 문서가 약속한 것 | ★★★ 기호 → 이름 대응표 · **`operator` 수식어가 있어야** 참가 · `+=` 의 **모호성 규칙** · `==` 는 오버로드 대상이 **아니다** |
| **구현(JVM 백엔드)** | kotlinc 가 JVM 으로 내리는 방식 | 기호가 **`invokevirtual` 하나**로 내려가는 것 · `!in`·`<` 뒤에 붙는 **비교 명령** · 확장 연산자가 **`invokestatic`** 인 것 |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | 진단 문구 · ★ `MutableList` 의 `+=` 가 **모호하지 않은 것**((3)) |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 해시코드·주소·시간을 **하나도 안 찍었다** |
| 안 흔들린다 | ★★★ 격자 출력 — `sNN → 호출` 과 마지막 줄 「풀린 칸 N / M」 | 같은 `javap` 출력이면 스크립트가 같은 답을 낸다 |
| 안 흔들린다 | `javap` 출력 — 명령·오프셋·서명 | 같은 소스·같은 판이면 같다. 상수 풀 **번호**는 근거로 쓰지 않는다 |
| 안 흔들린다 | 컴파일 진단의 **문구·`파일:줄:칸`·캐럿** · 모든 **종료 코드** | 결정적이다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 바이트 단위로 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**연산자 오버로딩은 「기호를 정해진 이름의 함수 호출로 바꿔 읽는 번역표」다.** `a + b` 라고 쓰면 컴파일러는 그것을 **`a.plus(b)`** 로 읽는다. 그 이상은 아무것도 없다.

그래서 할 수 있는 것과 없는 것이 **번역표 한 장**으로 정해진다 — 표에 있는 이름(`plus`·`get`·`invoke`…)만 기호가 되고, 표에 없는 기호(`===`·`&&`)는 **못 만든다.** 이름이 맞아도 **`operator` 도장**이 없으면 번역하지 않는다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 번역표 | 기호 → 이름 대응(`+` → `plus`, `a[i]` → `get`, `a()` → `invoke`) | (1) |
| 번역 결과 | `invokevirtual V.plus` — **이름으로 부른 것과 같은 호출** | (1) |
| 도장 | **`operator` 수식어** | (4) |
| 번역이 두 갈래 | `+=` 가 `plusAssign` 인가 `a = a + b` 인가 | (3) |
| 번역표에 없는 칸 | `==` — `equals` **재정의**로만 | (5) |
| 남의 물건에 번역표 붙이기 | 확장 연산자(`operator fun String.times`) | (6) |
| 괄호 없는 호출 | `infix` — [09번 주제](../09-varargs-spread-local-and-infix-functions/) | (7) |

```text
   소스              컴파일러가 읽는 것                javap -c
   ---------------   -----------------------------   ------------------------------
   a + b             a.plus(b)                       invokevirtual V.plus
   a[1] = 5          a.set(1, 5)                     invokevirtual V.set
   a(3)              a.invoke(3)                     invokevirtual V.invoke
   4 !in a           !a.contains(4)                  invokevirtual V.contains + ifne
   a < b             a.compareTo(b) < 0              invokevirtual V.compareTo + ifge
   a == b            a?.equals(b) ?: (b === null)    invokestatic Intrinsics.areEqual  <- V 가 아니다
```

## 이 주제가 답하려는 질문

1. 어떤 기호가 **어떤 이름**으로 풀리나 — 그리고 풀린 결과는 **이름으로 부른 것과 무엇이 다른가**.
2. `+=` 는 **언제 모호**하고 언제 한쪽으로 정해지나.
3. 언제 쓰면 **안 되나** — 컴파일러가 막지 않는 실패는 무엇인가.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **`javap -c` 격자** | 기호 18칸이 **각각 어느 메서드 호출**이 됐나 — 스크립트가 세어 「풀린 칸 N / M」을 찍는다((1)) | ★ **본체 창** |
| ★★ **실행 출력** | 번역된 호출이 **실제로 무엇을 돌려주나**((1)·(3)·(6)) | 이 갈래의 기본 창 |
| ★★ **컴파일 진단** | `+=` 모호성 · `operator` 누락 · `equals` 에 `operator` 를 붙이면((3)(4)(5)) | 이 갈래의 기본 창 |
| ★ **참조 동일성 `===`** | `+=` 가 **같은 객체를 고쳤나, 새 객체를 만들었나**((3)) — 출력만으로는 안 갈린다 | ★ 이 주제의 고유 창 |
| **부적용 — 실행 시간** | ★★★ **잴 것이 없다.** 기호 `a + b` 와 이름 `a.plus(b)` 는 **바이트코드가 한 글자도 같다**((1)의 `s01`·`s19`) — 비교할 두 대상이 **애초에 하나**다 | — |

★★ **제4의 상태 — 「잴 것이 없다」.** 「연산자 오버로딩은 비용이 없다」는 **잰 결론이 아니다.** 이 문서가 보인 것은 **「기호는 같은 이름의 메서드 호출 하나로 번역된다」** 뿐이다 — 그 메서드 **본문의 비용**은 기호와 무관하게 그 메서드의 것이다.\
★ 그래서 시간을 **안 쟀고**, 호출 **개수**만 셌다.

### (1) ★★★ 이름 → 기호 전수 격자 — `javap` 가 답한다

**언제 쓰나** — 「`!in` 은 무엇으로 풀리지?」「`<` 는?」을 외우지 말고 세어 볼 때.

`V` 에 `operator` 함수 15개, `Acc` 에 `plusAssign` 하나를 달고, **기호 하나당 함수 하나**(`s01`\~`s18`)로 썼다. `s19` 는 **기호 없이 이름으로** 부른 대조군이다.

```kotlin
// opgrid.kt
class V(val n: Int) {
    operator fun plus(o: V) = V(n + o.n)
    operator fun minus(o: V) = V(n - o.n)
    operator fun times(o: V) = V(n * o.n)
    operator fun div(o: V) = V(n / o.n)
    operator fun rem(o: V) = V(n % o.n)
    operator fun unaryMinus() = V(-n)
    operator fun not() = V(n.inv())
    operator fun inc() = V(n + 1)
    operator fun get(i: Int) = n + i
    operator fun set(i: Int, v: Int) { println("set $i $v") }
    operator fun invoke(x: Int) = n * x
    operator fun contains(x: Int) = x == n
    operator fun rangeTo(o: V) = n..o.n
    operator fun rangeUntil(o: V) = n..<o.n
    operator fun compareTo(o: V) = n.compareTo(o.n)
}

class Acc(var n: Int) {
    operator fun plusAssign(o: Int) { n += o }
}

fun s01(a: V, b: V) = a + b
fun s02(a: V, b: V) = a - b
fun s03(a: V, b: V) = a * b
fun s04(a: V, b: V) = a / b
fun s05(a: V, b: V) = a % b
fun s06(a: V) = -a
fun s07(a: V) = !a
fun s08(a: V): V { var x = a; x++; return x }
fun s09(a: V) = a[2]
fun s10(a: V) { a[1] = 5 }
fun s11(a: V) = a(3)
fun s12(a: V) = 4 in a
fun s13(a: V) = 4 !in a
fun s14(a: V, b: V) = a..b
fun s15(a: V, b: V) = a..<b
fun s16(a: V, b: V) = a < b
fun s17(a: Acc) { a += 2 }
fun s18(a: V, b: V) = a == b
fun s19(a: V, b: V) = a.plus(b)

fun main() {
    val a = V(6); val b = V(4)
    println("${s01(a, b).n} ${s02(a, b).n} ${s03(a, b).n} ${s04(a, b).n} ${s05(a, b).n}")
    println("${s06(a).n} ${s07(a).n} ${s08(a).n} ${s09(a)} ${s11(a)}")
    s10(a)
    println("${s12(a)} ${s13(a)} ${s14(a, b)} ${s15(b, a)} ${s16(a, b)} ${s18(a, b)}")
    val acc = Acc(1); s17(acc); println(acc.n)
}
```

```text
===== kotlinc opgrid.kt -d o31g =====
(exit 0)
===== java -cp o31g:kotlin-stdlib.jar OpgridKt =====
10 2 24 1 2
-6 -7 7 8 18
set 1 5
false true 6..4 4..5 false false
3
(exit 0)
```

**격자** — `javap -c -p` 출력을 스크립트가 읽어 **함수마다 불린 메서드**를 뽑는다(`checkNotNullParameter` 는 뺀다).

```python
# grid31.py
import re
import sys

src = open(sys.argv[1], encoding="utf-8").read().splitlines()
expr = {}
for line in src:
    m = re.match(r"fun (s\d\d)\((.*?)\)(?:: \w+)? *(?:=|\{) *(.*?) *\}?$", line)
    if m:
        expr[m.group(1)] = m.group(3)

calls = {}
cur = None
for line in sys.stdin:
    m = re.search(r" (s\d\d)\(", line)
    if m and "static" in line:
        cur = m.group(1)
        calls[cur] = []
        continue
    if cur and line.strip() == "":
        cur = None
        continue
    if cur:
        m = re.search(r"invoke\w+ +#\d+(?:, +\d+)? +// (?:Interface)?Method ([\w/$]+)\.(\w+)", line)
        if m and m.group(2) != "checkNotNullParameter":
            calls[cur].append(m.group(1).split("/")[-1] + "." + m.group(2))

hit = 0
for k in sorted(calls):
    own = [c for c in calls[k] if c.split(".")[0] in ("V", "Acc")]
    if own:
        hit += 1
    print("%s  %-22s -> %s" % (k, expr.get(k, "?"), ", ".join(calls[k]) or "(호출 없음)"))
print("V·Acc 의 메서드 호출로 풀린 칸 %d / %d" % (hit, len(calls)))
```

```text
===== javap -c -p o31g/OpgridKt.class | python3 grid31.py opgrid.kt =====
s01  a + b                  -> V.plus
s02  a - b                  -> V.minus
s03  a * b                  -> V.times
s04  a / b                  -> V.div
s05  a % b                  -> V.rem
s06  -a                     -> V.unaryMinus
s07  !a                     -> V.not
s08  var x = a; x++; return x -> V.inc
s09  a[2]                   -> V.get
s10  a[1] = 5               -> V.set
s11  a(3)                   -> V.invoke
s12  4 in a                 -> V.contains
s13  4 !in a                -> V.contains
s14  a..b                   -> V.rangeTo
s15  a..<b                  -> V.rangeUntil
s16  a < b                  -> V.compareTo
s17  a += 2                 -> Acc.plusAssign
s18  a == b                 -> Intrinsics.areEqual
s19  a.plus(b)              -> V.plus
V·Acc 의 메서드 호출로 풀린 칸 18 / 19
(exit 0)
```

- ★★★ **`V·Acc 의 메서드 호출로 풀린 칸 18 / 19`** — 기호 17칸과 대조군 1칸이 전부 **`V`/`Acc` 의 메서드 호출 하나**로 내려갔다. **풀리지 않은 한 칸이 `s18 a == b`** 다 — `V.equals` 가 아니라 **`Intrinsics.areEqual`** 이다((5)).
- ★★ **`s13 4 !in a` 와 `s12 4 in a` 가 같은 `V.contains`** 를 부른다 — 부정은 **호출 뒤의 비교 명령**이 한다. `s16 a < b` 도 `V.compareTo` 하나다 — `<`·`>`·`<=`·`>=` 넷이 **한 메서드**를 쓴다.
- ★ `s08 x++` 는 `V.inc` — **`inc` 는 수신자를 고치지 않고 새 값을 돌려준다**(`x = x.inc()` 로 번역된다). 출력 둘째 줄의 `7` 이 그 결과다.
- ★ `s15 a..<b` → `V.rangeUntil`, `s14 a..b` → `V.rangeTo` — 내 타입에도 `..<` 를 열 수 있다. 표준 `Int` 의 `..<` 가 `until` 과 **명령이 같다**는 것은 [07번 주제](../07-loops-ranges-and-labels/) (3)이 정본이다.

**호출 뒤에 무엇이 붙나** — 네 칸을 통째로 본다.

```text
===== javap -c -p o31g/OpgridKt.class | awk '/ s(01|13|16|18|19)\(/,/^$/' =====
  public static final V s01(V, V);
    Code:
       0: aload_0
       1: ldc           #9                  // String a
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_1
       7: ldc           #17                 // String b
       9: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
      12: aload_0
      13: aload_1
      14: invokevirtual #23                 // Method V.plus:(LV;)LV;
      17: areturn

  public static final boolean s13(V);
    Code:
       0: aload_0
       1: ldc           #9                  // String a
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: iconst_4
       8: invokevirtual #76                 // Method V.contains:(I)Z
      11: ifne          18
      14: iconst_1
      15: goto          19
      18: iconst_0
      19: ireturn

  public static final boolean s16(V, V);
    Code:
       0: aload_0
       1: ldc           #9                  // String a
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_1
       7: ldc           #17                 // String b
       9: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
      12: aload_0
      13: aload_1
      14: invokevirtual #92                 // Method V.compareTo:(LV;)I
      17: ifge          24
      20: iconst_1
      21: goto          25
      24: iconst_0
      25: ireturn

  public static final boolean s18(V, V);
    Code:
       0: aload_0
       1: ldc           #9                  // String a
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_1
       7: ldc           #17                 // String b
       9: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
      12: aload_0
      13: aload_1
      14: invokestatic  #106                // Method kotlin/jvm/internal/Intrinsics.areEqual:(Ljava/lang/Object;Ljava/lang/Object;)Z
      17: ireturn

  public static final V s19(V, V);
    Code:
       0: aload_0
       1: ldc           #9                  // String a
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_1
       7: ldc           #17                 // String b
       9: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
      12: aload_0
      13: aload_1
      14: invokevirtual #23                 // Method V.plus:(LV;)LV;
      17: areturn
(exit 0)
```

- ★★★ **`s01`(`a + b`)과 `s19`(`a.plus(b)`)는 한 글자도 같다** — 오프셋·명령·상수 풀 번호까지. 기호는 **이름 호출의 다른 표기**다((0)의 「잴 것이 없다」가 이 근거다).
- ★★ `s13` — `V.contains` 뒤에 **`ifne`**(참이면 0 으로 간다). `!in` 이라는 메서드는 **없다.**
- ★★ `s16` — `V.compareTo` 뒤에 **`ifge`**(0 이상이면 거짓). `<` 는 「`compareTo(b) < 0`」이다.
- ★ `s18` — `==` 만 **`invokestatic Intrinsics.areEqual`** 이다. 기호가 `V` 로 가지 않는 유일한 칸이다.

### (2) ★ 규약 이름 표 — 격자가 확인한 것

| 기호 | 이름 | 격자 | 반환 규칙 |
|---|---|---|---|
| `a + b` · `-` · `*` · `/` · `%` | `plus` · `minus` · `times` · `div` · `rem` | `s01`\~`s05` | 자유 |
| `-a` · `!a` | `unaryMinus` · `not` | `s06` · `s07` | 자유 |
| `a++` · `++a` | `inc` | `s08` | ★ **수신자 타입의 하위 타입** — 새 값을 돌려준다 |
| `a[i]` · `a[i] = v` | `get` · `set` | `s09` · `s10` | 자유 |
| `a(x)` | `invoke` | `s11` | 자유 |
| `x in a` · `x !in a` | `contains` | `s12` · `s13` | `Boolean` |
| `a..b` · `a..<b` | `rangeTo` · `rangeUntil` | `s14` · `s15` | 자유 |
| `a < b` 등 넷 | `compareTo` | `s16` | ★ **`Int`** — 0 과 비교된다 |
| `a += b` | `plusAssign`(또는 `a = a + b`) | `s17` | `plusAssign` 은 **`Unit`** |
| `a == b` | ★ **없다** — `equals` 재정의 | `s18` | — |

### (3) ★★ `+=` — 두 갈래가 동시에 서면 **모호하다**

**언제 쓰나** — `plus` 와 `plusAssign` 을 **둘 다** 가진 타입에 `+=` 를 쓸 때. 문서의 규칙은 이렇다 — **둘 다 있고, 좌변이 `var` 이고, `plus` 의 반환이 좌변 타입에 들어가면 모호성 에러.**

```kotlin
// assignbad.kt
class Both(val n: Int) {
    operator fun plus(o: Int) = Both(n + o)
    operator fun plusAssign(o: Int) { println("plusAssign $o") }
}

class Bare(val n: Int) {
    fun plus(o: Int) = Bare(n + o)
}

fun main() {
    var a = Both(1)
    a += 2
    val c = Bare(1) + 4
}
```

```text
===== kotlinc assignbad.kt -d o31b =====
assignbad.kt:12:7: error: ambiguity between assign operator candidates:
fun plus(o: Int): Both
fun plusAssign(o: Int): Unit
    a += 2
      ^^
assignbad.kt:13:21: error: 'operator' modifier is required on 'fun plus(o: Int): Bare' defined in 'Bare'.
    val c = Bare(1) + 4
                    ^
(exit 1)
```

- ★★★ **「`ambiguity between assign operator candidates:`」** — 후보 둘(`fun plus(o: Int): Both` · `fun plusAssign(o: Int): Unit`)을 **전문으로** 댄다. 컴파일러는 **고르지 않는다.**
- ★ 13번째 줄 — `Bare.plus` 에 `operator` 가 없어 「`'operator' modifier is required`」((4)).

```text
   a += b
     |
     +-- 갈래 1  a.plusAssign(b)          plusAssign 이 있나 ?
     +-- 갈래 2  a = a.plus(b)             plus 가 있고 · a 가 var 이고 · 반환이 a 의 타입에 들어가나 ?
     |
     둘 다 선다   -> 모호성 에러 (고르지 않는다)
     하나만 선다  -> 그 갈래
     둘 다 없다   -> 해석 실패
```

**한쪽 갈래가 무너지면 정해진다**

```kotlin
// assignok.kt
class Both(val n: Int) {
    operator fun plus(o: Int) = Both(n + o)
    operator fun plusAssign(o: Int) { println("A plusAssign $o") }
}

fun main() {
    val b = Both(1)
    b += 3
    var ml = mutableListOf(1)
    val m0 = ml
    ml += 2
    println("B $ml $m0 ${ml === m0}")
    var rl: List<Int> = listOf(1)
    val r0 = rl
    rl += 2
    println("C $rl $r0 ${rl === r0}")
}
```

```text
===== kotlinc assignok.kt -d o31a =====
(exit 0)
===== java -cp o31a:kotlin-stdlib.jar AssignokKt =====
A plusAssign 3
B [1, 2] [1, 2] true
C [1, 2] [1] false
(exit 0)
```

```text
===== javap -c -p o31a/AssignokKt.class | grep -E 'Both\.plus|Collection\.add|CollectionsKt\.plus' =====
      11: invokevirtual #15                 // Method Both.plusAssign:(I)V
      41: invokeinterface #33,  2           // InterfaceMethod java/util/Collection.add:(Ljava/lang/Object;)Z
     119: invokestatic  #76                 // Method kotlin/collections/CollectionsKt.plus:(Ljava/util/Collection;Ljava/lang/Object;)Ljava/util/List;
(exit 0)
```

| 좌변 | 서는 갈래 | 호출 | `===` 옛 참조 |
|---|---|---|---|
| `val b: Both` | `plusAssign` 만(재대입 불가) | `Both.plusAssign` | — (`A plusAssign 3`) |
| `var ml: MutableList<Int>` | ★ `plusAssign` 만 — `plus` 는 **`List`** 를 돌려줘 `MutableList` 에 **못 들어간다** | `Collection.add`(인라인) | ★ **`true`** — 같은 객체를 고쳤다 |
| `var rl: List<Int>` | `plus` 만 — `List` 에는 `plusAssign` 이 없다 | `CollectionsKt.plus` | ★ **`false`** — 새 리스트 |

- ★★★ **같은 `+=` 가 좌변의 선언 타입에 따라 「제자리 수정」과 「새 객체 재대입」으로 갈린다.** 출력만 보면 `B [1, 2]`·`C [1, 2]` 로 **같아 보인다** — `===` 로 옛 참조를 물어야 갈린다((0)의 고유 창).
- ★★ **예상과 달랐다** — 「`var` 인 `MutableList` 의 `+=` 는 모호하다」는 흔한 설명이 **이 판에서는 틀렸다.** 에러 없이 `plusAssign` 으로 정해졌다. 문서 규칙의 셋째 조건(「`plus` 의 반환이 좌변 타입의 하위 타입」)이 **거짓**이기 때문이다 — `List<Int>` 는 `MutableList<Int>` 가 아니다. 그 규칙에 **그대로 맞는 `Both`** 만 모호했다.

### (4) ★ `operator` 도장 — 이름이 맞아도 없으면 번역하지 않는다

(3)의 `Bare` 가 그 실측이다 — `fun plus` 가 **있는데도** `Bare(1) + 4` 가 막혔다. [30번 주제](../30-destructuring-declarations-and-componentn/) (4)의 `component1` 도 같은 문구로 막혔다.

- ★★ 도장이 필요한 이유 — `plus`·`get`·`contains` 는 **흔한 이름**이다. 도장 없이 번역하면 **기호로 쓰일 줄 모르고 지은 메서드**가 기호가 된다. `operator` 는 「이 함수는 이 기호의 뜻을 따른다」는 **선언**이다.

### (5) ★★ `equals` 는 연산자로 오버로드하는 것이 **아니다** — 재정의다

```kotlin
// eqop.kt
class Q(val n: Int) {
    operator fun equals(other: Q): Boolean = n == other.n
}

operator fun Q.equals(other: Any?): Boolean = true
```

```text
===== kotlinc eqop.kt -d o31q =====
eqop.kt:2:5: error: 'operator' modifier is not applicable to function: must override 'equals()' in Any.
    operator fun equals(other: Q): Boolean = n == other.n
    ^^^^^^^^
eqop.kt:5:1: error: 'operator' modifier is not applicable to function: must be a member function.
operator fun Q.equals(other: Any?): Boolean = true
^^^^^^^^
(exit 1)
```

- ★★★ **`operator fun equals(other: Q)`** — 「`'operator' modifier is not applicable to function: must override 'equals()' in Any.`」 `==` 에 참가하는 유일한 길은 **`override fun equals(other: Any?)`** 다.
- ★★ **확장으로도 안 된다** — 「`must be a member function.`」 남의 타입의 `==` 는 **바꿀 수 없다**(멤버가 이긴다는 [13번 주제](../13-extension-functions-and-properties/) (3)과 같은 방향이다).
- ★ 그래서 (1)의 `s18` 이 `V.equals` 가 아니라 **`Intrinsics.areEqual`** 이었다 — `==` 의 번역과 `null` 처리는 [32번 주제](../32-equality-and-equals-contract/)가 정본이다.

### (6) ★★ 확장 연산자 · `invoke` · 그리고 **쓰면 안 되는** 모양

```kotlin
// ext31.kt
operator fun String.times(k: Int): String = repeat(k)
operator fun StringBuilder.plusAssign(s: String) { append(s) }

class Money(val cents: Long) {
    operator fun plus(o: Money) = Money(cents + o.cents)
    override fun toString() = "Money($cents)"
}

class Bag(val items: MutableList<String>) {
    operator fun plus(s: String): Bag { items.add(s); return this }
    override fun toString() = "Bag$items"
}

fun main() {
    println("A " + "ab" * 3)
    val sb = StringBuilder("x"); sb += "y"; println("B $sb")
    val a = Bag(mutableListOf("p"))
    val b = a + "q"
    println("C a=$a b=$b ${a === b}")
    val price = Money(100)
    val total = price + Money(50)
    println("D price=$price total=$total")
    more()
}

class Check(private val min: Int) {
    operator fun invoke(s: String) = s.length >= min
}

fun more() {
    val longEnough = Check(3)
    println("E ${longEnough("ab")} ${longEnough("abc")} ${listOf("a", "abcd").filter(longEnough::invoke)}")
}
```

```text
===== kotlinc ext31.kt -d o31e =====
(exit 0)
===== java -cp o31e:kotlin-stdlib.jar Ext31Kt =====
A ababab
B xy
C a=Bag[p, q] b=Bag[p, q] true
D price=Money(100) total=Money(150)
E false true [abcd]
(exit 0)
```

```text
===== javap -c -p o31e/Ext31Kt.class | grep -E 'Method (times|plusAssign|Bag\.plus|Money\.plus|Check\.invoke)' =====
      15: invokestatic  #50                 // Method times:(Ljava/lang/String;I)Ljava/lang/String;
      44: invokestatic  #75                 // Method plusAssign:(Ljava/lang/StringBuilder;Ljava/lang/String;)V
      98: invokevirtual #101                // Method Bag.plus:(Ljava/lang/String;)LBag;
     177: invokevirtual #123                // Method Money.plus:(LMoney;)LMoney;
      24: invokevirtual #148                // Method Check.invoke:(Ljava/lang/String;)Z
      38: invokevirtual #148                // Method Check.invoke:(Ljava/lang/String;)Z
     133: invokevirtual #148                // Method Check.invoke:(Ljava/lang/String;)Z
(exit 0)
```

- `A ababab` — **남의 타입**(`String`)에 `*` 를 달았다. 바이트코드는 **`invokestatic times(String, int)`** — 확장이므로 **정적 호출**이다([13번 주제](../13-extension-functions-and-properties/) (1)).
- `B xy` — `StringBuilder` 에 `+=` 를 확장으로 달았다(`invokestatic plusAssign`).
- `E false true [abcd]` — `invoke` 로 객체를 **함수처럼** 부른다. `longEnough::invoke` 로 **함수 참조**로도 넘어간다.
- ★★★ **`C a=Bag[p, q] b=Bag[p, q] true`** — `Bag.plus` 가 **수신자를 고치고 자기를 돌려준다.** `val b = a + "q"` 가 **`a` 까지 바꿨다**(`a === b` 가 `true`). **컴파일러는 아무 말도 안 했다** — 규약이 요구하는 것은 **이름과 `operator`** 뿐이고 「`+` 는 피연산자를 안 고친다」는 **사람의 약속**이다.
- ★ `D` 줄의 `Money.plus` 는 **새 객체**를 돌려준다(`price` 는 그대로 `Money(100)`). 두 `plus` 는 **바이트코드 모양이 같다**(`invokevirtual … .plus`) — 차이는 **본문에만** 있다.

**언제 쓰면 안 되나 — 판단 기준을 실패 사례로**

| 실패 사례 | 무엇이 깨지나 | 기준 |
|---|---|---|
| `Bag.plus` 가 수신자를 고친다 | `val b = a + x` 가 **`a` 를 바꾼다**(`C` 줄) | ★★ **`plus` 는 새 값, 고치려면 `plusAssign`** |
| `plus` 와 `plusAssign` 을 **둘 다** 주고 `var` 로 쓴다 | `+=` 가 **모호성 에러**((3)) | 가변 타입엔 `plusAssign` 만, 불변 타입엔 `plus` 만 |
| `+=` 가 좌변 타입에 따라 제자리/재대입으로 갈린다 | 옛 참조를 든 쪽이 **다른 것을 본다**((3)) | 공유되는 컬렉션이면 `add` 를 **이름으로** 쓴다 |
| 기호의 뜻이 도메인에서 **자명하지 않다**(`Order * Order`) | 읽는 사람이 **정의를 찾아가야** 한다 | 수학·컬렉션처럼 **뜻이 이미 합의된** 자리에서만 |
| `==` 를 바꾸고 싶다 | `operator` 로는 **못 한다**((5)) | `equals` 재정의 + 규약([32번 주제](../32-equality-and-equals-contract/)) |

### (7) ★ `infix` — 이 문서는 **다시 재지 않는다**

`infix` 는 **괄호 없는 호출 형태**이지 기호 번역표가 아니다. 조건(멤버 또는 확장 · 매개변수 1개)과 우선순위(★ **산술보다 낮고 비교보다 높다** — `1 shl 2 + 3` 이 `32`)는 [09번 주제](../09-varargs-spread-local-and-infix-functions/) (8)·(9)가 **실행으로 재 둔 정본**이다.
여기서는 형태 예제((아래) `a dot b`)에서 **한 번 쓰기만** 한다.

### (8) ★ Rust 와 — 같은 번역표, 다른 대가

| 축 | Kotlin | Rust([30번](../../../rust/syntax/30-operator-overloading-std-ops-index-and-deref/)) |
|---|---|---|
| 참가 표식 | 이름 + **`operator` 수식어** | **트레이트 구현**(`impl Add for T`) |
| `a + b` 뒤의 `a` | ★ **그대로 쓸 수 있다** — 참조를 넘긴다((6)의 `price`) | ★ **옮겨진다**(Rust 30번 (1)) — `Copy` 가 아니면 다시 못 쓴다 |
| `+=` | `plusAssign` 또는 `a = a + b` — **모호성 규칙**((3)) | `AddAssign` — **별개 트레이트**, 모호성 없음 |
| 비교 | `compareTo` 하나가 `<` 넷 · `==` 는 `equals` 재정의 | `PartialOrd`·`PartialEq` — **`std::ops` 밖** |
| 남의 타입에 달기 | ★ **확장 연산자**로 된다((6)의 `String.times`) | **고아 규칙**이 막는 경우가 있다 |

- ★ 이 표의 Rust 칸은 **그 갈래 문서를 읽고** 옮긴 것이다 — 여기서 `rustc` 를 던지지 않았다.

## 문법 — 형태와 규칙

**형태** — `operator` 셋과 `infix` 하나가 한 프로그램에서 도는 최소 예제다.

```kotlin
// form31.kt
data class Vec(val x: Int, val y: Int) {
    operator fun plus(o: Vec) = Vec(x + o.x, y + o.y)
    operator fun unaryMinus() = Vec(-x, -y)
    operator fun get(i: Int) = if (i == 0) x else y
}

infix fun Vec.dot(o: Vec) = x * o.x + y * o.y

fun main() {
    val a = Vec(1, 2)
    val b = Vec(3, 4)
    println("Z ${a + b} ${-a} ${a[1]} ${a dot b}")
}
```

```text
===== kotlinc form31.kt -d o31z =====
(exit 0)
===== java -cp o31z:kotlin-stdlib.jar Form31Kt =====
Z Vec(x=4, y=6) Vec(x=-1, y=-2) 2 11
(exit 0)
```

**규칙 불릿**

- 기호는 **정해진 이름의 함수 호출**로 번역된다 — `+` → `plus`, `a[i]` → `get`, `a()` → `invoke`, `in` → `contains`, `<` → `compareTo`, `..<` → `rangeUntil`((1)(2)).
- 그 함수에는 **`operator`** 가 있어야 한다((4)). 멤버·확장 모두 된다((6)).
- `!in`·`<` 는 **별도 함수가 없다** — 같은 함수 뒤에 비교 명령이 붙는다((1)).
- `inc`/`dec` 는 **새 값을 돌려준다**(수신자를 고치지 않는다).
- `+=` — `plusAssign` 과 `plus` 가 **둘 다 서면 모호성 에러**, 한쪽만 서면 그쪽((3)).
- `==` 는 오버로드가 아니라 **`override fun equals(other: Any?)`**((5)). `===`·`&&`·`||` 는 **못 만든다.**
- `infix` 는 기호가 아니라 **호출 형태** — [09번 주제](../09-varargs-spread-local-and-infix-functions/).

## 어디서 틀리나

1. ★★★ **`plus` 가 수신자를 고친다.** `val b = a + x` 가 **`a` 를 바꾼다** — 컴파일러는 침묵한다((6)의 `C`).
2. ★★★ **`plus` 와 `plusAssign` 을 둘 다 준다.** `var` 에서 `+=` 가 **모호성 에러**((3)).
3. ★★ **`+=` 가 항상 제자리 수정이라고 믿는다.** `var rl: List` 는 **새 리스트를 재대입**한다 — 옛 참조는 옛 값이다((3)).
4. ★★ **「`var MutableList` 의 `+=` 는 모호하다」로 외운다.** 이 판에서는 **모호하지 않다** — `plus` 의 반환 `List` 가 좌변에 안 들어간다((3)).
5. ★ **`operator` 를 빠뜨린다.** 「`'operator' modifier is required`」((4)).
6. ★ **`operator fun equals(other: MyType)` 을 쓴다.** 막힌다 — `==` 는 **`equals(Any?)` 재정의**뿐이다((5)).
7. ★ **`!in`·`>` 를 따로 구현하려 한다.** `contains`·`compareTo` 하나로 끝난다((1)).
8. ★ **「연산자 오버로딩은 비용이 없다」를 잰 결론으로 쓴다.** 보인 것은 **이름 호출과 바이트코드가 같다**까지다((0)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| 기호 → 이름 **대응표** | ★★★ **언어 보장** | (1)(2) |
| `operator` 수식어 **요구** | **언어 보장** | (4) |
| `+=` 의 **모호성 규칙** | **언어 보장**(문서가 세 조건으로 명시) | (3) |
| `==` 가 오버로드 대상이 **아닌** 것 | **언어 보장** | (5) |
| `inc` 가 **새 값을 돌려주는** 것 · `compareTo` 가 `Int` | **언어 보장** | (1)(2) |
| 기호가 **`invokevirtual` 하나** · 뒤에 `ifne`/`ifge` | **JVM 백엔드의 구현** | (1) |
| 확장 연산자가 **`invokestatic`** | **JVM 백엔드의 구현** | (6) |
| `MutableList` 의 `+=` 가 **`Collection.add` 로 인라인** | **표준 라이브러리의 구현**(`inline` 확장) | (3) |
| 진단 **문구 그 자체** | **이 판의 산출물** | 전부 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 수·벡터·행렬·돈 — **뜻이 합의된** 산술 | `operator fun plus` 등 | (1) — 읽는 사람이 정의를 안 찾아가도 된다 |
| 컨테이너의 접근 | `get`/`set`/`contains` | `a[i]`·`x in a` 가 자연스럽다 |
| 가변 누산기 | ★ **`plusAssign` 만** | (3) — `plus` 를 같이 주면 모호해진다 |
| 불변 값 | ★ **`plus` 만** | (3)(6) — 새 값을 돌려준다 |
| 「함수 같은 객체」(검사기·핸들러) | `invoke` | (6)의 `Check` — 함수 참조로도 넘어간다 |
| 남의 타입에 기호 | 확장 연산자 | (6) — 단 **그 기호의 뜻을 바꾸지 마라** |
| 도메인 동사(`place`·`merge`) | ★ **이름 있는 함수**(필요하면 `infix`) | 기호의 뜻이 **자명하지 않다** |
| 동등성 | `equals` 재정의 | (5) — 연산자가 아니다 |

## 핵심 문장

1. 연산자 오버로딩은 **기호를 정해진 이름의 함수 호출로 번역하는 것**이다 — `a + b` 와 `a.plus(b)` 는 **바이트코드가 같다.**
2. 참가하려면 **`operator`** 가 필요하다. `!in`·`<` 는 **별도 함수가 없고** `contains`·`compareTo` 뒤에 비교 명령이 붙는다.
3. `+=` 는 `plusAssign` 과 `a = a + b` 가 **둘 다 서면 모호성 에러**다 — 한쪽만 서면 그쪽이고, 그래서 **좌변 타입이 제자리/재대입을 가른다.**
4. `==` 는 오버로드가 아니라 **`equals(Any?)` 재정의**이고, 확장으로도 못 바꾼다.
5. 규약이 검사하는 것은 **이름과 수식어**뿐이다 — 「`+` 는 피연산자를 안 고친다」는 **사람의 약속**이다.

## 관련 자료

- [09번 주제](../09-varargs-spread-local-and-infix-functions/) — ★ **`infix` 의 정본.** 조건과 우선순위(`1 shl 2 + 3`)를 실측으로 둔 곳.
- [07번 주제](../07-loops-ranges-and-labels/) — `..<` 의 판 경계와 `iterator()` 규약.
- [13번 주제](../13-extension-functions-and-properties/) — 확장 함수. 확장 연산자가 **정적 호출**인 이유.
- [17번 주제](../17-delegated-properties/) — `getValue`/`setValue`, 또 하나의 `operator` 규약.
- [30번 주제](../30-destructuring-declarations-and-componentn/) — `componentN`, 또 하나의 `operator` 규약.
- [32번 주제](../32-equality-and-equals-contract/) — ★ **`==` 의 정본.** (5)에서 넘긴 것.
- [`../../../rust/syntax/30-operator-overloading-std-ops-index-and-deref/`](../../../rust/syntax/30-operator-overloading-std-ops-index-and-deref/) — Rust `std::ops`. **소유권이 움직이는** 쪽의 대비.

## 용어 풀이

> **연산자 오버로딩(operator overloading)** — 기호의 뜻을 내 타입에 정해 주는 것. Kotlin 에서는 **정해진 이름의 `operator` 함수**를 쓰는 것이다.\
> 예: `operator fun plus(o: V) = …` → `a + b`.

> **`operator` 수식어** — 「이 함수가 기호 규약에 참가한다」는 선언. 없으면 이름이 맞아도 번역되지 않는다.

> **복합 대입(augmented assignment)** — `+=`·`-=` 따위. `plusAssign` 이나 `a = a + b` 로 풀린다.

> **`invoke` 규약** — `a(x)` 를 `a.invoke(x)` 로 읽는 규약. 객체를 함수처럼 부르게 한다.

> **`infix`** — `a f b` 처럼 **괄호와 점 없이** 부르는 호출 형태. 기호 번역표와는 **다른 기능**이다.

> **`Intrinsics.areEqual`** — Kotlin `==` 가 참조 타입에서 번역되는 정적 메서드. `null` 을 먼저 처리하고 `equals` 를 부른다([32번 주제](../32-equality-and-equals-contract/)).

## 더 들어가면

- **왜 이름 기반 번역표인가** — Kotlin 은 C++ 처럼 `operator+` 라는 **기호 이름의 함수**를 두지 않고 **평범한 식별자**(`plus`)에 도장을 찍는다. 그래서 기호 호출과 이름 호출이 **같은 메서드**가 되고((1)의 `s01`·`s19`), 클래스 파일에는 **`plus` 라는 평범한 메서드**만 남는다(`javap` 가 `V.plus` 로 보였다) — JVM 에는 기호 이름의 메서드가 없으니 이 설계가 번역을 단순하게 만든다(이 문서는 **Java 에서 부르는 데까지는 안 던졌다**).
- **왜 `==` 만 빠졌나** — `==` 는 `null` 을 **먼저 처리**해야 하고(`a?.equals(b) ?: (b === null)`), `equals(Any?)` 는 **`Any` 가 이미 가진 계약**(반사·대칭·추이)이 걸려 있다. 타입별 오버로드(`equals(Q)`)를 허용하면 **`Any?` 로 받은 자리와 `Q` 로 받은 자리에서 답이 갈린다** — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **27번**([`27-equals-hashcode-contract/`](../../../java/syntax/27-equals-hashcode-contract/))이 「`equals(내타입)` 은 재정의가 아니라 오버로딩」 사고로 적은 그 자리다. Kotlin 은 그 문을 **문법으로 닫았다**((5)).
