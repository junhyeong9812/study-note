# kotlin/syntax/04 — 스마트 캐스트와 그것이 깨지는 자리 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Type checks and casts — Smart casts](https://kotlinlang.org/docs/typecasts.html#smart-casts) · [Null safety](https://kotlinlang.org/docs/null-safety.html) · [What's new in Kotlin 2.0.0 — Smart cast improvements](https://kotlinlang.org/docs/whatsnew20.html).
> **실행 검증** — 모든 에러·출력은 **kotlinc 2.4.20 (JRE 21.0.5)** 에서 실제로 얻었다.\
> 「깨지는 자리」는 **아홉 가지를 따로 던져** 에러 메시지를 받은 것이고, 동시성 실험은 20만 회 × 5판을 돌렸다.
> **버전** — 스마트 캐스트는 1.0. 이 문서의 **에러 문구와 통과 범위는 K2**(2.0 이후 기본) 기준이다.\
> ★ **K1 과 비교하지 못했다** — 이 컴파일러는 `-language-version 1.9` 를 거부한다(아래 「실행 검증」).
> **경계** — [03번 주제](../03-null-safe-types/)는 **`?`·`?.`·`?:`·`!!` 라는 문법**이 정본이다.\
> 여기는 **「그 문법을 안 써도 되게 해 주는 것과, 그것이 안 되는 조건」** 만 다룬다.\
> `is`/`as`/`as?` 라는 **연산자 자체**의 정본은 목록의 **33번 주제**다.\
> Java 의 `instanceof` 패턴은 [`../../../java/syntax/22-instanceof-type-patterns/`](../../../java/syntax/22-instanceof-type-patterns/) 가 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**스마트 캐스트는 "컴파일러가 방금 읽은 검사를 기억해 주는 것" 이다.**\
**그래서 깨지는 조건은 하나다 — 「검사한 그 값이 다음 줄에서도 같다고 보장할 수 없을 때」.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 신분증을 확인하고 통과시킨 경비 | `if (x != null)` 검사 |
| "방금 확인했으니 안에서는 안 물어본다" | 스마트 캐스트 |
| 그 사람이 안에서 다른 사람으로 바뀔 수 있는 문 | `var` 프로퍼티·커스텀 getter·위임 |
| 확인한 순간 사진을 찍어 두기 | 로컬 `val` 로 받기 |
| 옆 건물이 관리하는 명부 | 다른 모듈의 `val` |
| 볼 때마다 다시 계산하는 명부 | 커스텀 getter |

```text
  스마트 캐스트가 되는 경우                스마트 캐스트가 깨지는 경우

  val s: String? = …                      class C { var s: String? = … }
  if (s != null) {                        if (c.s != null) {
      s.length      ← String 으로 좁혀짐       c.s.length   ← ERROR
  }                                       }
                                            이유: 두 c.s 가 같은 값이라는 보장이 없다
```

**똑같은 구조로** Kotlin 이 동작한다 — 컴파일러는 **"같은 값을 두 번 읽는다" 를 증명할 수 있을 때만** 좁힌다.

실무에서 이게 터지는 자리는 **`!!` 를 붙여 우회하는 순간**이다.\
컴파일러가 거부한 것은 잔소리가 아니라 **실제로 재현되는 경쟁 조건**이다 — 아래 (7)에서 20만 회 중 수백 번 터졌다.

> **스마트 캐스트(smart cast)** — `is`/`!= null` 검사를 통과한 뒤 컴파일러가 그 변수를 **좁은 타입으로 자동 취급**하는 것.\
> 예: `if (x is String) { x.length }` — `x` 를 `String` 으로 다시 캐스트하지 않아도 된다.

> **안정 값(stable value)** — 두 번 읽어도 같은 값이라고 컴파일러가 **증명할 수 있는** 것.\
> 예: 로컬 `val` 은 안정이고, `var` 프로퍼티는 안정이 아니다.

## 이 주제가 답하려는 질문

1. 컴파일러는 **무엇을 근거로** 타입을 좁히는가 — 그리고 그 근거가 언제 무너지는가.
2. 깨지는 자리는 **몇 가지이고 각각 에러 메시지가 무엇인가** — 메시지가 이유를 말해 주는가.
3. 깨졌을 때 **무엇으로 푸는가** — 그리고 `!!` 로 우회하면 실제로 무슨 일이 일어나는가.

## 동작 방식

### (1) 되는 경우 — 컴파일러가 좁혀 준다

**언제 쓰나** — null 검사나 타입 검사를 한 직후.

```kotlin
fun e(x: String?) {
    val v = x ?: return
    println(v.length)          // v 는 String
}
fun f(x: Any?) = when (x) {
    is String -> x.length      // x 는 String
    is Int -> x + 1            // x 는 Int
    null -> -1
    else -> 0
}
fun g(x: Any) {
    require(x is String)
    println(x.length)          // contract 로 좁혀진다
}
```

**출력** (`k2.kt` — 좁혀지는 형태 11가지를 한 프로그램에 몰아 넣었다. 전부 컴파일되고 실행된다)

```text
a (boolean val 이 검사를 들고 있음) -> 2
b (|| 오른쪽에서 좁혀짐)        -> 2
c (&& 오른쪽에서 좁혀짐)        -> 마
e (엘비스 조기 반환)            -> 3
g (require 의 contract)         -> 3
h (?.let 의 it)                 -> 2
i (좁혀진 값을 람다가 잡음)     -> 1
j (람다가 읽기만 하는 var)      -> 1, reader()=1
k (인라인 람다 안)              -> 1
l (제네릭 val)                  -> 1
f (when 의 가지) -> f("x")=1, f(1)=2, f(null)=-1, f(1.0)=0
```

```text
   x: Any?
     │
     ├─ if (x is String) ──> 이 블록 안에서 x: String
     ├─ if (x != null)   ──> 이 블록 안에서 x: Any
     └─ val v = x ?: return ──> 이 아래 전부에서 v: Any
```

- `is`·`!= null`·`require`·`?: return` 이 전부 근거가 된다.
- ★ **`?: return` 은 블록이 아니라 「그 아래 전부」를 좁힌다** — 검사에 실패한 경로가 이미 떠났기 때문이다.\
  이것이 나중에 (8)의 해법이 된다.
- `when` 의 각 가지 안에서도 좁혀진다.

비용 — 0. 스마트 캐스트는 **바이트코드에 `checkcast` 하나를 넣거나 아예 아무것도 안 넣는다.**

### (2) ★★ 깨지는 자리 아홉 — 전수를 던져서 받은 에러

**언제 쓰나** — `if` 로 검사했는데도 컴파일러가 거부할 때.

**출력** (`kotlinc break.kt` — 한 파일에 몰아 넣고 한 번에 던졌다)

```text
break.kt:10:47: error: smart cast to 'String' is impossible, because 's' is a mutable property that could be mutated concurrently.
fun f1(o: VarProp) { if (o.s != null) println(o.s.length) }          // var 프로퍼티
                                              ^^^
break.kt:12:52: error: smart cast to 'String' is impossible, because 's' is a property that has an open or custom getter.
fun f3(o: CustomGetter) { if (o.s != null) println(o.s.length) }     // 커스텀 getter
                                                   ^^^
break.kt:13:45: error: smart cast to 'String' is impossible, because 's' is a property that has an open or custom getter.
fun f4(o: Iface) { if (o.s != null) println(o.s.length) }            // 인터페이스 프로퍼티
                                            ^^^
break.kt:18:29: error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
    if (v != null) println(v.length)
                            ^
break.kt:28:42: error: smart cast to 'String' is impossible, because 'topLevel' is a mutable property that could be mutated concurrently.
fun f7() { if (topLevel != null) println(topLevel.length) }          // 최상위 var
                                         ^^^^^^^^
break.kt:31:49: error: smart cast to 'String' is impossible, because 's' is a delegated property.
fun f8(o: Delegated) { if (o.s != null) println(o.s.length) }        // 위임 프로퍼티
                                                ^^^
```

**출력** (`kotlinc modB/use.kt -cp outA` — **모듈을 따로 컴파일**해서 던졌다)

```text
modB/use.kt:3:43: error: smart cast to 'String' is impossible, because 's' is a public API property declared in different module.
fun g1(b: Box) { if (b.s != null) println(b.s.length) }
                                          ^^^
modB/use.kt:4:47: error: smart cast to 'String' is impossible, because 's' is a property that has an open or custom getter.
fun g2(b: OpenBox) { if (b.s != null) println(b.s.length) }
                                              ^^^
```

**출력** (`kotlinc more.kt` — `@Volatile` 과 함수 호출 결과)

```text
more.kt:3:40: error: smart cast to 'String' is impossible, because 's' is a mutable property that could be mutated concurrently.
fun a(o: V) { if (o.s != null) println(o.s.length) }       // @Volatile var
                                       ^^^
more.kt:4:39: error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
fun b() { if (f() != null) println(f().length) }            // 함수 호출 결과
                                      ^
```

정리하면 이렇다.

| # | 깨지는 자리 | 에러 메시지 |
|---|---|---|
| 1 | **`var` 멤버 프로퍼티** | `… is a mutable property that could be mutated concurrently.` |
| 2 | **최상위 `var`** | 같은 문구 |
| 3 | **`@Volatile var`** ★ | 같은 문구 — **volatile 로도 안 풀린다** |
| 4 | **커스텀 getter 가 있는 `val`** | `… is a property that has an open or custom getter.` |
| 5 | **`open val`** | 같은 문구 |
| 6 | **인터페이스가 선언한 `val`** | 같은 문구 |
| 7 | **위임 프로퍼티(`by lazy` 등)** | `… is a delegated property.` |
| 8 | **다른 모듈의 public `val`** | `… is a public API property declared in different module.` |
| 9 | **람다가 고쳐 쓰는 지역 `var`** ★ | **`only safe (?.) or non-null asserted (!!.) calls are allowed…`** |
| (9') | **함수 호출 결과** | 같은 문구 |

★ **9와 9' 만 메시지가 다르다.** 앞의 여덟은 "스마트 캐스트가 불가능한 이유" 를 말해 주는데,\
9·9' 는 [03번](../03-null-safe-types/)의 1번과 **똑같은 일반 문구**다 — **왜 안 되는지가 안 적혀 있다.**\
이유는 이렇게 읽는다 — 앞의 여덟은 **"이 값이 있긴 한데 안정적이지 않다"** 이고,\
9·9' 는 **애초에 「그 값」이라고 부를 대상이 없다**(매번 새로 계산되거나 언제든 덮어써진다).

**통과하는 경우도 같이 확인해야 한다.**

| 자리 | 결과 |
|---|---|
| 같은 모듈의 `val` 프로퍼티 (getter 없음) | **통과** |
| 지역 `var` (람다가 안 고침) | **통과** |
| 람다가 **읽기만** 하는 지역 `var` | **통과** |
| 인라인 람다(`run { }`) 안 | **통과** |
| 제네릭 `val` (`G<String?>` 의 `t`) | **통과** |

비용 — 0. 되는 쪽도 안 되는 쪽도 런타임 비용은 없다. **전부 컴파일 타임 판정이다.**

### (3) 세 문구를 한 그림으로 — 컴파일러가 묻는 것은 하나다

**언제 쓰나** — 아홉 가지를 외우기 전에.

```text
                    "이 식을 두 번 읽으면 같은 값인가?"
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
      예 → 좁힌다          아니오 → 왜?        모르겠다 → 일반 거부
          │                   │                   │
    로컬 val             ┌────┴────┐          람다가 고치는 var
    같은 모듈 val        │         │          함수 호출 결과
    지역 var(안 고침)    │         │
                     누가 고칠     읽을 때마다
                     수 있다       계산된다
                        │            │
                   var / 다른 모듈   커스텀 getter
                   (mutated          open val
                    concurrently)    위임 (delegated)
```

- **세 메시지는 「아니오」의 세 가지 이유**다 — 누가 고칠 수 있거나(1\~3, 8), 읽을 때마다 계산되거나(4\~7), 아예 안정 개념이 없거나(9).
- 8번(다른 모듈)이 처음 보면 이상한데, **그 모듈이 나중에 `var` 로 바뀌어도 내 코드는 재컴파일되지 않을 수 있다.**\
  즉 컴파일러가 **지금 본 것을 미래에도 믿을 수 없다.**
- 3번(`@Volatile`)이 결정적이다 — **volatile 은 가시성을 보장하지 그 값이 안 바뀌는 것을 보장하지 않는다.**

### (4) 커스텀 getter 는 부를 때마다 값이 다를 수 있다 — 실증

**언제 쓰나** — "getter 가 있다고 뭐가 다른가" 를 물을 때.

```kotlin
class Flaky {
    private var n = 0
    val s: String?
        get() { n++; return if (n % 2 == 1) "가" else null }
}
```

**출력** (`why.kt`)

```text
--- 커스텀 getter 는 부를 때마다 값이 다를 수 있다 ---
1회: 가   2회: null   3회: 가   4회: null
-> if (f.s != null) 로 통과해도 다음 f.s 는 null 일 수 있다
--- 그래서 !! 로 우회하면 실제로 터진다 ---
g.s!! -> java.lang.NullPointerException (message=null)
```

```text
   if (g.s != null) {      ← 1회 호출: "가"  → 조건 통과
       g.s!!.length        ← 2회 호출: null  → NPE
   }
```

- **`if` 의 `g.s` 와 본문의 `g.s` 는 서로 다른 호출이다.** 소스에서는 같은 글자인데 실행은 둘이다.
- 그래서 **`!!` 로 우회하면 스레드가 하나여도 터진다.** 동시성이 필요 없다.
- 이것이 "getter 가 있으면 거부" 라는 규칙의 이유다 — **컴파일러는 getter 안을 안 본다.**

비용 — getter 호출 횟수만큼.

### (5) ★★ `var` 프로퍼티는 실제로 경쟁한다 — 20만 회 실측

**언제 쓰나** — "`mutated concurrently` 는 이론상 얘기 아닌가" 라고 물을 때.

```kotlin
class Mutable { var s: String? = "가" }

val t = Thread { repeat(200000) { m.s = if (it % 2 == 0) null else "가" } }
t.start()
repeat(200000) {
    try { if (m.s != null) m.s!!.length } catch (e: Throwable) { crashed++ }
}
```

**출력** (`why.kt` — **5판**)

```text
20만 회 중 !! 가 터진 횟수 = 242
20만 회 중 !! 가 터진 횟수 = 96
20만 회 중 !! 가 터진 횟수 = 252
20만 회 중 !! 가 터진 횟수 = 492
20만 회 중 !! 가 터진 횟수 = 256
```

- ★ **다섯 판 전부 0이 아니다.** 컴파일러의 거부는 이론이 아니라 **재현되는 실패**다.
- **횟수 자체는 한 판의 결과**다(96 \~ 492 로 흔들린다). 재현되는 것은 **"0이 아니다" 뿐**이다.\
  이 수치로 확률을 말하면 안 된다 — 스케줄링·JIT 상태에 달렸다.
- 같은 실험에서 **로컬 `val` 로 스냅샷을 뜨면** 이렇게 된다.

```kotlin
val snap = m2.s
if (snap != null) snap.length
```

```text
20만 회 중 터진 횟수 = 0
20만 회 중 터진 횟수 = 0
20만 회 중 터진 횟수 = 0
20만 회 중 터진 횟수 = 0
20만 회 중 터진 횟수 = 0
```

- ★ **이 0은 "안 터졌다" 가 아니라 구조적으로 터질 수 없다는 뜻**이다 —\
  `snap` 은 **지역 변수**라 다른 스레드가 닿을 방법이 없다. 관찰이 아니라 **논증**이 근거다.\
  (동시성 주제에서 "통과한 실행" 은 대개 가장 약한 근거지만, 여기서는 **그 값이 공유되지 않는다는 사실**이 근거다.)

비용 — 필드 읽기 한 번이 지역 변수 한 칸으로 옮겨 가는 것뿐이다.

### (6) 푸는 법 — 전부 "안정 값 하나를 만들어라"

**언제 쓰나** — (2)의 아홉 중 하나에 걸렸을 때.

```kotlin
// 1. 로컬 val 로 받는다 (가장 흔함)
val s = o.s
if (s != null) println(s.length)

// 2. 엘비스 조기 반환 — 그 아래 전부가 좁혀진다
val s = o.s ?: return
println(s.length)

// 3. ?.let — 블록 인자가 곧 안정 값이다
o.s?.let { println(it.length) }

// 4. 안 되면 ?. 를 그냥 쓴다
println(o.s?.length ?: 0)
```

```text
   깨진 자리                        고친 자리
   +--------------------------+     +---------------------------+
   | if (o.s != null)         |     | val s = o.s               |
   |     o.s.length   ERROR   |     | if (s != null)            |
   +--------------------------+     |     s.length     OK       |
                                    +---------------------------+
      두 번 읽는다                      한 번 읽어 고정한다
```

- **네 해법이 전부 같은 일을 한다** — **읽는 횟수를 하나로 줄이고 그것을 `val` 에 묶는다.**
- ★ **`!!` 는 해법이 아니다.** (4)·(5)가 보여 준 그대로 **실제로 터진다.**
- `?.let { }` 의 `it` 은 **람다 파라미터**라서 로컬 `val` 과 같다 — 그래서 자동으로 풀린다.

비용 — 없다. 오히려 프로퍼티 읽기가 줄어든다.

### (7) K2 가 좁혀 주는 범위 — 데이터 흐름 분석

**언제 쓰나** — "이것도 될까" 싶은 형태를 만났을 때.

```kotlin
fun a(x: Any) {
    val isStr = x is String
    if (isStr) println(x.length)              // ★ boolean val 이 검사를 들고 있어도 좁혀진다
}
fun b(x: Any?) {
    if (x !is String || x.length == 0) return // ★ || 의 오른쪽에서 좁혀진다
    println(x.length)
}
fun c(x: Any?) {
    if (x is String && x.length > 0) println(x.uppercase())
}
fun i(x: Any?) {
    if (x is String) {
        val lam = { x.length }                // ★ 좁혀진 값을 람다가 잡는다
        println(lam())
    }
}
```

**출력** — 위 (1)과 **같은 프로그램의 같은 실행**이다. 경고는 한 건도 없었다.

```text
a (boolean val 이 검사를 들고 있음) -> 2
b (|| 오른쪽에서 좁혀짐)        -> 2
c (&& 오른쪽에서 좁혀짐)        -> 마
e (엘비스 조기 반환)            -> 3
g (require 의 contract)         -> 3
h (?.let 의 it)                 -> 2
i (좁혀진 값을 람다가 잡음)     -> 1
j (람다가 읽기만 하는 var)      -> 1, reader()=1
k (인라인 람다 안)              -> 1
l (제네릭 val)                  -> 1
f (when 의 가지) -> f("x")=1, f(1)=2, f(null)=-1, f(1.0)=0
```

- ★ **`val isStr = x is String` 을 거쳐도 좁혀진다.** 검사 결과를 변수에 담아 두어도 컴파일러가 따라간다.\
  이것이 K2(2.0+)의 데이터 흐름 분석이 하는 일이다.
- `||`·`&&` 안에서도, 람다가 **읽기만** 하면 람다 안에서도 좁혀진다.
- ★ **K1 에서 무엇이 안 됐는지는 이 문서가 확인하지 못했다** — 이 컴파일러가 K1 을 안 돌린다(아래 「구현…」).

비용 — 0. 컴파일 시간만 쓴다.

## 문법 — 형태와 규칙

```kotlin
// 근거가 되는 검사들
if (x != null) { … }          // null 검사
if (x is String) { … }        // 타입 검사
if (x !is String) return      // 부정 + 조기 이탈
when (x) { is String -> … }   // when 의 가지
require(x is String)          // contract 를 가진 stdlib 함수
val v = x ?: return           // 엘비스 조기 반환

// 좁혀진 타입은 그 범위 안에서만 유효하다
if (x is String) {
    x.length                  // OK
}
x.length                      // ERROR — 밖에서는 다시 Any
```

규칙 불릿.

- 좁힘의 범위는 「**검사가 참인 것이 보장되는 구간**」이다. `if` 블록 안, `&&` 의 오른쪽, `||` 뒤의 `return` 아래.
- **`is` 로 좁힌 것과 `!= null` 로 좁힌 것은 같은 메커니즘**이다 — `!= null` 은 `is T` 의 특수한 경우로 읽는다.
- `require`·`checkNotNull` 이 좁혀 주는 것은 **contract** 덕분이다. 내가 만든 함수도 contract 를 달면 된다(목록의 **51번 주제**).
- **안 되면 메시지가 이유를 말해 준다** — 세 문구 중 하나다((2)).

## 어디서 틀리나

| 틀리는 형태 | 무슨 일이 일어나나 | 고치는 법 |
|---|---|---|
| 거부당해서 `!!` 를 붙임 | 커스텀 getter 면 **단일 스레드에서도** 터진다 | 로컬 `val` 로 받는다 |
| `var` 프로퍼티에 `!!` | 20만 회 중 수백 번 터진다(실측) | 로컬 `val` 스냅샷 |
| `@Volatile` 을 붙이면 될 거라 기대 | **안 된다.** 같은 에러 | volatile 은 가시성이지 불변이 아니다 |
| 다른 모듈의 `val` 이라 거부 | "같은 모듈에서는 됐는데" | 모듈 경계를 의심한다 — 메시지에 적혀 있다 |
| `by lazy` 프로퍼티에서 거부 | `delegated property` | 로컬 `val` |
| 인터페이스 프로퍼티에서 거부 | `open or custom getter` — 구현이 getter 일 수 있다 | 로컬 `val` |
| 람다가 고치는 `var` 에서 거부 | 메시지가 **일반 문구**라 이유가 안 보인다 | 람다가 고치는지 찾아본다 |
| 함수 호출 결과에 검사 | 두 호출이 다른 값일 수 있다 | 결과를 `val` 에 담는다 |
| `?.let { }` 안에서 `it` 대신 원본을 씀 | 다시 거부당한다 | `it` 을 쓴다 |

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 로컬 `val` 은 검사 뒤 좁혀진다 | **언어** | 명세 + 실측 |
| `var` 프로퍼티는 좁혀지지 않는다 | **언어** | 명세(안정 값 조건) + 에러 |
| 다른 모듈의 `val` 은 좁혀지지 않는다 | **언어** | 명세 + 에러 |
| 위임 프로퍼티는 좁혀지지 않는다 | **언어** | 명세 + 에러 |
| **에러 문구 자체** | **구현**(이 컴파일러 버전) | 실측 — 버전마다 바뀔 수 있다 |
| **K2 가 `val isStr = x is String` 을 따라가는 것** | **구현**(K2 데이터 흐름 분석) ★ | 실측 — 명세가 아니라 컴파일러 능력이다 |
| **9·9' 만 일반 문구가 나오는 것** | **구현** | 실측 |
| **20만 회 중 터진 횟수** | **한 판의 관찰** ★ | 96 \~ 492 로 흔들린다 |
| "0이 아니다" | **재현됨** | 5판 전부 0이 아니었다 |
| 스냅샷 판의 0 | **구조적 논증** | 지역 변수는 공유되지 않는다 |

★ **가장 조심할 구분** — **"스마트 캐스트가 되는 범위" 는 컴파일러 능력이다.**\
명세는 "안정 값이면 좁힌다" 를 정하고, **무엇을 안정이라고 증명할 수 있는지는 컴파일러가 얼마나 똑똑한가**에 달렸다.\
그래서 K2 에서 새로 되는 것들이 생겼고, **앞으로도 늘어날 수 있다.**\
뒤집으면 — **"이건 안 되니까 원래 안 되는 거다" 라고 외우면 안 된다.** 버전을 확인한다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 지역 변수의 null 검사 | 그냥 `if` | 스마트 캐스트가 알아서 해 준다 |
| 프로퍼티를 한 번만 쓸 때 | `o.s?.length ?: 0` | `val` 을 만들 것도 없다 |
| 프로퍼티를 여러 번 쓸 때 | 로컬 `val` 로 받는다 | 좁혀지고, 읽기 횟수도 준다 |
| 없으면 함수를 끝낼 때 | `val s = o.s ?: return` | 그 아래 전부가 좁혀진다 |
| 있을 때만 블록을 돌릴 때 | `o.s?.let { }` | `it` 이 곧 안정 값 |
| 동시에 바뀌는 상태 | **반드시 스냅샷** | (5)에서 실제로 터졌다 |
| **`!!` 로 우회** | **안 한다** | 컴파일러가 거부한 것은 재현되는 실패다 |

판단 규칙 두 줄.

- **거부당하면 "어떻게 통과시킬까" 가 아니라 "이 값을 몇 번 읽고 있나" 를 먼저 센다.** 답은 거의 항상 "두 번" 이다.
- **`!!` 는 우회가 아니라 그 경쟁 조건을 런타임으로 미루는 것이다.**

## 핵심 문장

- 스마트 캐스트의 조건은 하나다 — **같은 식을 두 번 읽어도 같은 값임을 컴파일러가 증명할 수 있는가.**
- 깨지는 자리는 **세 무리**다 — 누가 고칠 수 있는 것(`var`·다른 모듈), 읽을 때마다 계산되는 것(getter·`open`·위임), 안정 개념이 없는 것(람다가 고치는 `var`·함수 호출).
- **`@Volatile` 로는 안 풀린다.** volatile 은 가시성이지 불변이 아니다.
- **람다가 고치는 `var` 와 함수 호출 결과만 메시지가 일반 문구다** — 이유가 안 적혀 있으니 직접 찾아야 한다.
- 커스텀 getter 에 `!!` 를 붙이면 **단일 스레드에서도 터진다.** `var` 프로퍼티는 20만 회 중 수백 번 터졌다.
- 해법 넷은 전부 같은 일이다 — **읽기를 한 번으로 줄여 `val` 에 묶는다.**
- **무엇이 좁혀지는지는 컴파일러 능력이라 버전에 따라 늘어난다.** 안 되는 것을 규칙으로 외우지 않는다.

## 관련 자료

- [`../README.md`](../README.md) — Kotlin 문법·API 주제 목록(이 주제는 04번)
- [03번 주제](../03-null-safe-types/) — **`?`·`?.`·`?:`·`!!` 문법의 정본.** 이 문서의 9번 에러 문구가 거기 1번과 같다
- [05번 주제](../05-platform-types/) — Java 경계. **플랫폼 타입에는 스마트 캐스트가 필요 없다**(이미 non-null 처럼 쓸 수 있다) — 그래서 더 위험하다
- [01번 주제](../01-val-var-and-basic-types/) — `val` 이 **재대입만** 막는다는 것. 이 주제의 "안정 값" 개념이 거기서 출발한다
- [`../../../java/syntax/22-instanceof-type-patterns/`](../../../java/syntax/22-instanceof-type-patterns/) — **Java 의 `instanceof` 패턴 정본.** Java 는 **변수를 새로 선언**해서 같은 문제를 피했다 — Kotlin 은 기존 변수를 좁힌다
- [`../../../java/syntax/23-switch-pattern-matching/`](../../../java/syntax/23-switch-pattern-matching/) — `when (x) { is … }` 의 Java 쪽 대응
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — 「왜 이 언어인가」. 문법이 아니라 선택 논증
- 목록의 **33번 주제**(`is`/`as`/`as?`) — 캐스트 연산자 자체의 정본
- 목록의 **51번 주제**(`require`/`check`) — contract 가 스마트 캐스트를 만드는 방법
- 목록의 **23번 주제**(`sealed` + `when` 완결성) — `when` 의 가지에서 좁혀지는 것의 다음 단계

## 용어 풀이

- **스마트 캐스트** — 검사 뒤 컴파일러가 변수를 좁은 타입으로 자동 취급하는 것. 캐스트를 손으로 안 적어도 된다.
- **안정 값(stable value)** — 두 번 읽어도 같다고 컴파일러가 증명할 수 있는 식. 로컬 `val`·같은 모듈 `val`(getter 없음).
- **데이터 흐름 분석(data-flow analysis)** — 코드의 실행 경로를 따라가며 각 지점에서 무엇이 참인지 추적하는 것. K2 의 스마트 캐스트가 이것 위에 있다.
- **커스텀 getter** — `val x: T get() = …` 처럼 읽을 때 계산하는 프로퍼티. **값이 아니라 함수다.**
- **위임 프로퍼티(delegated property)** — `by lazy`·`by observable` 처럼 읽기·쓰기를 다른 객체에 맡긴 프로퍼티.
- **`@Volatile`** — 필드 쓰기가 다른 스레드에 즉시 보이게 하는 표시. **값이 안 바뀐다는 뜻이 아니다.**
- **contract** — stdlib 함수가 "이 함수가 정상 반환하면 이 조건이 참이다" 를 컴파일러에 알려 주는 선언. `require` 가 좁혀 주는 이유.
- **K1 / K2** — 옛 프런트엔드 / 2.0 부터의 새 프런트엔드. 스마트 캐스트 범위가 달라진 지점이다.
- **경쟁 조건(race condition)** — 두 스레드의 실행 순서에 따라 결과가 달라지는 상태. (5)에서 실제로 재현했다.

---

## 더 들어가면

- 8번(다른 모듈)은 **컴파일 단위의 문제**다. 같은 파일·같은 모듈이면 컴파일러가 선언을 직접 보지만,\
  다른 모듈의 `.class` 는 **나중에 교체될 수 있다.** 그 모듈이 `val` 을 `var` 로 바꿔 다시 배포해도\
  내 코드는 재컴파일되지 않을 수 있으므로 **바이너리 호환 관점의 거부**다.
- `?.let { }` 이 스마트 캐스트 문제를 함께 푸는 것은 우연이 아니다 —\
  `let` 의 시그니처가 `inline fun <T, R> T.let(block: (T) -> R): R` 이라 **수신자를 파라미터로 한 번 넘긴다.**\
  그 파라미터가 곧 로컬 `val` 이다. **(6)의 1번과 같은 일을 문법으로 포장한 것**이다.
- Java 21 의 `if (o instanceof String s)` 는 **새 변수 `s` 를 선언**해서 같은 문제를 아예 안 만든다.\
  Kotlin 은 **기존 이름을 좁히는** 쪽을 골랐고, 그 대가가 이 문서의 아홉 가지다.\
  어느 쪽이 나은지는 취향이 아니라 **"어떤 실수를 막고 싶은가" 의 차이**다 — 정본은 [`../../../java/syntax/22-instanceof-type-patterns/`](../../../java/syntax/22-instanceof-type-patterns/).
- 제네릭 프로퍼티(`class G<T>(val t: T)` 의 `g.t`)는 **좁혀진다**(실측). `T` 가 `String?` 으로 실체화돼도\
  `val` 이고 getter 가 없으므로 안정 값이기 때문이다.
