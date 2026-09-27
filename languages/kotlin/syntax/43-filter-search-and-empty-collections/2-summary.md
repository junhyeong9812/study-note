# kotlin/syntax/43 — 필터·검색 — `filter`/`find`/`first`/`any`/`all`/`none` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Filtering collections](https://kotlinlang.org/docs/collection-filtering.html)(`filter` · 검사 술어 `any`·`none`·`all`) · [Retrieve single elements](https://kotlinlang.org/docs/collection-elements.html)(`first`·`last`·`elementAt`·`find`·`random`·`…OrNull`) — 이 문서는 그 페이지들의 **목록**을 따르되, 문장은 인용하지 않고 **이 판의 stdlib 소스 jar**(`kotlin-stdlib-sources.jar` 2.4.20)의 KDoc 과 구현을 근거로 삼는다((3)(4)).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 5회(컴파일 실패 1벌 — `-api-version 1.6` 거부) · `java` 3회 + 격자 스크립트 안에서 1회 · `javap` 2회 · stdlib 소스 jar 에서 3곳.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「던진 칸 N / M」은 스크립트가 스스로 센 것**이다.
> **버전** — `first`·`single`·`find`·`any`·`all`·`none`·`filter`·`elementAt` 은 **1.0** — 이 판의 소스에서 선언 위에 `@SinceKotlin` 이 **없다**(확인만 했고 발췌하지 않았다). ★★ **`max()` 는 판에 따라 뜻이 바뀌었다** — stdlib 소스에 옛 `max(): T?` 가 **`warningSince = "1.4", errorSince = "1.5", hiddenSince = "1.6"`**, 새 `max(): T` 가 **`@SinceKotlin("1.7")`** 로 남아 있다((4)). 그 판들에서 **직접 컴파일해 보는 것은 못 했다**(아래).
> **경계** — `emptyList()` 가 **싱글턴 `EmptyList`** 라는 것은 [41번 주제](../41-collection-creation-and-copying/) (4)가 정본이다 — 여기서는 그 객체가 **던지는 메시지**만 본다. `?:` 와 `firstOrNull` 을 잇는 null 안전 연산자는 [03번 주제](../03-null-safe-types/)다. 예외 계층·`Nothing` 은 [34번 주제](../34-exceptions-nothing-and-try-expression/)다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**빈 입력 격자 — 연산 × (빈 · 하나 · 맞는 것 없음 · 둘 이상 맞음) → 값 / 던진 예외**」. 어느 연산이 던지는지는 **타입에 안 나온다** — `first()` 도 `firstOrNull()` 도 컴파일은 똑같이 된다. **빈 것을 넣어 봐야** 보인다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장 / API 계약** | 서명·KDoc 이 약속한 것 | ★★★ **반환 타입의 `?`** 가 「없으면 `null`」을 약속한다(`firstOrNull`·`find`·`singleOrNull`·`maxOrNull`) · ★★★ `all` 의 KDoc — 빈 컬렉션이면 **`true`**(공허한 참) · `@throws NoSuchElementException` |
| **구현(stdlib)** | 이 판의 stdlib 가 실제로 하는 것 | ★★ **예외 메시지 문구**(`List is empty.` · `Collection is empty.` · `Empty list doesn't contain element at index 0.`) — 받는 쪽 **타입과 런타임 클래스에 따라 갈린다**((2)) · `single()` 이 둘 이상에서 **`IllegalArgumentException`** |
| **이 판의 관찰** | kotlinc 2.4.20 · stdlib 2.4.20 에서 본 것 | ★ `max()` 호출이 **`maxOrThrow`** 로 컴파일된다 · JVM stdlib 에 옛 `max` 가 **아직 있다**((4)) |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | ★ `random()` 은 **`Random(42)` 로 씨앗을 고정**했다 — 매 호출마다 새 `Random(42)` 라 칸마다 같은 순서를 받는다 |
| 안 흔들린다 | 격자 17행 × 4열 · 던진 칸 수 · 예외 **클래스 이름** | 결정적이다 |
| 안 흔들린다 | 예외 **메시지** | 이 판에서는 결정적 — ★ 그러나 **판이 오르면 바뀔 수 있는 칸**이다(규칙 27 — 근거는 클래스) |
| 안 흔들린다 | stdlib 소스 발췌 · `javap` 출력 · 진단 · 종료 코드 | jar·컴파일러가 같으면 같다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**빈 상자에 손을 넣었을 때 연산은 세 부류로 갈린다 — 「없다」고 소리치는 쪽(예외), 「없음」 쪽지를 주는 쪽(`null`), 원래 답이 정해진 쪽(`true`·`false`·`[]`).** `first()` 는 소리치고, `firstOrNull()` 은 쪽지를 주고, `filter` 는 빈 상자를 그대로 돌려준다.
★ 그리고 「**전부 조건을 만족하나**(`all`)」는 빈 상자에서 **`true`** 다 — 어기는 것이 **하나도 없으니까**. 반 학생이 0명이면 「전원 출석」은 참이다. 이것을 **공허한 참**(vacuous truth)이라 한다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 없다고 소리친다 | `first()`·`last()`·`single()`·`elementAt(0)`·`max()`·`random()` → 예외 | (1) |
| 「없음」 쪽지를 준다 | `firstOrNull()`·`find{}`·`singleOrNull()`·`maxOrNull()` → `null` | (1) |
| 답이 정해져 있다 | `any` → `false` · `all` → **`true`** · `none` → `true` · `filter` → `[]` | (1) ★ |
| 「딱 하나」 검사관 — 둘이어도 소리친다 | `single()` → 둘 이상에서 `IllegalArgumentException` | (1)(3) ★ |
| 같은 고함, 다른 사투리 | 예외 클래스는 같은데 **메시지가 받는 쪽마다 다르다** | (2) ★ |

```text
   빈 입력 []              연산                       결과
   ─────────────────────────────────────────────────────────────────────────────
   예외를 던진다    first()  last()  single()      NoSuchElementException 「List is empty.」
                   first{}  single{}             NoSuchElementException 「… no element matching the predicate.」
                   elementAt(0)                  IndexOutOfBoundsException 「Empty list doesn't contain …」
                   max()                         NoSuchElementException (메시지 없음 — null)
                   random(seed)                  NoSuchElementException 「Collection is empty.」
   null 을 준다     firstOrNull()  find{}  singleOrNull()  maxOrNull()
   답이 정해졌다    any() → false   any{} → false   all{} → true ★   none{} → true   filter{} → []

   둘 이상 맞음 [6, 8]  single()  → IllegalArgumentException 「List has more than one element.」
                       single{}  → IllegalArgumentException 「Collection contains more than one matching element.」
                       singleOrNull() → null  (「없음」과 「너무 많음」이 같은 null 이다)
```

## 이 주제가 답하려는 질문

1. 빈 컬렉션(과 「맞는 것 없음」·「둘 이상 맞음」)에서 **어느 연산이 던지고, 어느 것이 `null`·정해진 값을 주나**.
2. 던질 때 **무엇을 근거로** 잡아야 하나 — 클래스인가, 메시지인가.
3. `all{}` 이 빈 입력에서 `true` 인 것은 **계약인가**.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **빈 입력 격자(실행 + `try`)** | 17연산 × 4입력 → 값 / 예외 클래스·메시지((1)) | ★ **본체 창** |
| ★★ **같은 연산 · 다른 받는 쪽** | 예외 클래스는 같고 메시지가 갈린다((2)) | — |
| ★★ **stdlib 소스 jar 발췌** | `all` 의 공허한 참이 **KDoc 계약**인가 · `single` 의 두 예외((3)) | [41번 주제](../41-collection-creation-and-copying/) (2)와 같은 창 |
| ★ **`javap` — stdlib 와 호출 자리** | `max()` 가 **무엇으로** 컴파일되나 · 옛 `max` 가 남았나((4)) | [40번 주제](../40-read-only-collections-and-runtime-types/) (1)의 `javap` 창 |
| ★ **제5의 상태 — 창을 바꿔 물었다** | 「1.4\~1.6 판에서 `max()` 는 무엇이었나」를 **옛 판 컴파일**로 못 물었다(`-api-version 1.6` 거부) — **stdlib 소스의 애너테이션 + `javap`** 로 물었다((4)) | 바꾼 창은 **「그 판에서 경고였나 에러였나」를 직접 보여 주지 못한다** — 애너테이션이 **그렇게 적혀 있다**는 것까지다 |
| **인용 — 다시 안 잰다** | `emptyList()` 가 싱글턴 `EmptyList` | [41번 주제](../41-collection-creation-and-copying/) (4) |
| **부적용 — 실행 시간** | 「`find` 가 `filter().first()` 보다 싸다」는 **재지 않았다** | — |

### (1) ★★★ 빈 입력 격자 — 무엇이 던지고 무엇이 `null` 을 주나

**언제 쓰나** — 입력이 비어 있을 **수도** 있는 자리에서 검색 연산을 고를 때.

술어는 전부 `it > 5` 다. 입력 넷 — `empty=[]` · `one=[7]` · `no-match=[1, 2]` · `two-match=[6, 8]`. 칸마다 `try` 로 감싸 **값(`= …`)** 이나 **예외(`! 클래스: 메시지`)** 를 적는다.

```kotlin
// empty43.kt
import kotlin.random.Random

val inputs = listOf(
    "empty" to listOf<Int>(),
    "one" to listOf(7),
    "no-match" to listOf(1, 2),
    "two-match" to listOf(6, 8),
)

val ops: List<Pair<String, (List<Int>) -> Any?>> = listOf(
    "first()" to { xs -> xs.first() },
    "first{}" to { xs -> xs.first { it > 5 } },
    "firstOrNull()" to { xs -> xs.firstOrNull() },
    "last()" to { xs -> xs.last() },
    "single()" to { xs -> xs.single() },
    "single{}" to { xs -> xs.single { it > 5 } },
    "singleOrNull()" to { xs -> xs.singleOrNull() },
    "find{}" to { xs -> xs.find { it > 5 } },
    "any()" to { xs -> xs.any() },
    "any{}" to { xs -> xs.any { it > 5 } },
    "all{}" to { xs -> xs.all { it > 5 } },
    "none{}" to { xs -> xs.none { it > 5 } },
    "filter{}" to { xs -> xs.filter { it > 5 } },
    "elementAt(0)" to { xs -> xs.elementAt(0) },
    "max()" to { xs -> xs.max() },
    "maxOrNull()" to { xs -> xs.maxOrNull() },
    "random(seed)" to { xs -> xs.random(Random(42)) },
)

fun main() {
    for ((opName, op) in ops) {
        for ((inName, xs) in inputs) {
            val cell = try {
                "= " + op(xs)
            } catch (e: Exception) {
                "! " + e::class.java.simpleName + ": " + e.message
            }
            println(listOf(opName, inName, cell).joinToString("\t"))
        }
    }
}
```

```python
# grid43.py
import subprocess
import sys

d = sys.argv[1]
out = subprocess.run(["java", "-cp", d + ":kotlin-stdlib.jar", "Empty43Kt"],
                     capture_output=True, text=True, check=True).stdout
cols = ["empty", "one", "no-match", "two-match"]
rows = {}
order = []
for line in out.splitlines():
    cells = line.split("\t")
    if len(cells) != 3:
        raise SystemExit("cell count mismatch: " + line)
    op, inp, cell = cells
    if op not in rows:
        rows[op] = {}
        order.append(op)
    rows[op][inp] = cell
print("predicate: it > 5 | inputs: empty=[] one=[7] no-match=[1, 2] two-match=[6, 8]")
print("\t".join(["op"] + cols))
threw = total = 0
for op in order:
    if sorted(rows[op]) != sorted(cols):
        raise SystemExit("missing column: " + op)
    print("\t".join([op] + [rows[op][c] for c in cols]))
    for c in cols:
        total += 1
        if rows[op][c].startswith("! "):
            threw += 1
print("cells that threw: %d / %d" % (threw, total))
```

```text
===== kotlinc empty43.kt -d o43e =====
(exit 0)
```

```text
===== python3 grid43.py o43e =====
predicate: it > 5 | inputs: empty=[] one=[7] no-match=[1, 2] two-match=[6, 8]
op	empty	one	no-match	two-match
first()	! NoSuchElementException: List is empty.	= 7	= 1	= 6
first{}	! NoSuchElementException: Collection contains no element matching the predicate.	= 7	! NoSuchElementException: Collection contains no element matching the predicate.	= 6
firstOrNull()	= null	= 7	= 1	= 6
last()	! NoSuchElementException: List is empty.	= 7	= 2	= 8
single()	! NoSuchElementException: List is empty.	= 7	! IllegalArgumentException: List has more than one element.	! IllegalArgumentException: List has more than one element.
single{}	! NoSuchElementException: Collection contains no element matching the predicate.	= 7	! NoSuchElementException: Collection contains no element matching the predicate.	! IllegalArgumentException: Collection contains more than one matching element.
singleOrNull()	= null	= 7	= null	= null
find{}	= null	= 7	= null	= 6
any()	= false	= true	= true	= true
any{}	= false	= true	= false	= true
all{}	= true	= true	= false	= true
none{}	= true	= false	= true	= false
filter{}	= []	= [7]	= []	= [6, 8]
elementAt(0)	! IndexOutOfBoundsException: Empty list doesn't contain element at index 0.	= 7	= 1	= 6
max()	! NoSuchElementException: null	= 7	= 2	= 8
maxOrNull()	= null	= 7	= 2	= 8
random(seed)	! NoSuchElementException: Collection is empty.	= 7	= 1	= 6
cells that threw: 13 / 68
(exit 0)
```

- ★★★ **68칸 중 13칸이 던졌다** — 빈 입력 열에서 8칸(`first()`·`first{}`·`last()`·`single()`·`single{}`·`elementAt(0)`·`max()`·`random(seed)`), 나머지 5칸은 **비어 있지 않은** 입력이다(`first{}`·`single()`·`single{}` 의 「맞는 것 없음」·「둘 이상」).
- ★★★ **`all{}` 은 빈 입력에서 `true`**, `any{}` 는 `false`, `none{}` 은 `true` — 셋이 **예외도 `null` 도 아닌 정해진 값**을 준다. `all{}` 과 `none{}` 이 **동시에 `true`** 인 것은 빈 입력 한 칸뿐이다.
- ★★★ **`single()` 은 둘 이상에서도 던진다** — `no-match=[1, 2]`·`two-match=[6, 8]` 둘 다 원소가 둘이라 **`IllegalArgumentException: List has more than one element.`** 이다. 빈 입력은 **`NoSuchElementException`** — **클래스가 다르다.** 「없음」과 「너무 많음」을 예외 종류로 가른다.
- ★★ **`singleOrNull()` 은 그 둘을 합친다** — 빈 입력도, 둘 이상도 **같은 `null`** 이다. `null` 을 받으면 **없었는지 많았는지 모른다.**
- ★★ **`first{}` 는 「맞는 것 없음」에서도 던진다** — 빈 입력과 **같은 메시지**(`Collection contains no element matching the predicate.`). 입력이 비어서인지 **다 걸러져서인지** 예외로는 못 가른다.
- ★★ **`first()` 는 `NoSuchElementException`, `elementAt(0)` 은 `IndexOutOfBoundsException`** — 같은 「0번째가 없다」인데 **종류가 다르다.** `elementAt` 은 **인덱스 연산**으로 취급된다.
- ★ **`max()` 는 빈 입력에서 메시지 없이(`null`) 던진다** — `NoSuchElementException: null`. 소스가 `throw NoSuchElementException()` 로 **인자 없이** 던진다((4)).
- ★ **`random(seed)` 도 빈 입력에서 던진다** — `Collection is empty.`. 비어 있을 수 있으면 `randomOrNull`.

### (2) ★★ 같은 예외, 다른 메시지 — 근거는 클래스다

```kotlin
// msg43.kt
fun probe(label: String, f: () -> Any?) {
    val r = try {
        "= " + f()
    } catch (e: Exception) {
        "! " + e::class.java.name + " | " + e.message
    }
    println("$label  $r")
}

fun main() {
    val ro: List<Int> = listOf()
    val ml: List<Int> = mutableListOf()
    val st: Set<Int> = setOf()
    val sq: Sequence<Int> = emptySequence()
    probe("1 listOf().first()       ") { ro.first() }
    probe("2 mutableListOf().first()") { ml.first() }
    probe("3 setOf().first()        ") { st.first() }
    probe("4 emptySequence().first()") { sq.first() }
    probe("5 listOf().elementAt(0)       ") { ro.elementAt(0) }
    probe("6 mutableListOf().elementAt(0)") { ml.elementAt(0) }
    probe("7 setOf().elementAt(0)        ") { st.elementAt(0) }
    probe("8 listOf()[0]                 ") { ro[0] }
    probe("9 mutableListOf()[0]          ") { ml[0] }
}
```

```text
===== kotlinc msg43.kt -d o43m =====
(exit 0)
===== java -cp o43m:kotlin-stdlib.jar Msg43Kt =====
1 listOf().first()         ! java.util.NoSuchElementException | List is empty.
2 mutableListOf().first()  ! java.util.NoSuchElementException | List is empty.
3 setOf().first()          ! java.util.NoSuchElementException | Collection is empty.
4 emptySequence().first()  ! java.util.NoSuchElementException | Sequence is empty.
5 listOf().elementAt(0)         ! java.lang.IndexOutOfBoundsException | Empty list doesn't contain element at index 0.
6 mutableListOf().elementAt(0)  ! java.lang.IndexOutOfBoundsException | Index 0 out of bounds for length 0
7 setOf().elementAt(0)          ! java.lang.IndexOutOfBoundsException | Collection doesn't contain element at index 0.
8 listOf()[0]                   ! java.lang.IndexOutOfBoundsException | Empty list doesn't contain element at index 0.
9 mutableListOf()[0]            ! java.lang.IndexOutOfBoundsException | Index 0 out of bounds for length 0
(exit 0)
```

- ★★★ **`first()` 의 예외 클래스는 넷 다 `java.util.NoSuchElementException`, 메시지는 셋으로 갈린다** — `List is empty.`(정적 타입이 `List`) · `Collection is empty.`(`Set`) · `Sequence is empty.`(`Sequence`). **어느 `first` 확장이 골라졌느냐**가 메시지를 정한다.
- ★★★ **`elementAt(0)` 의 메시지는 런타임 클래스가 정한다** — 같은 `List<Int>` 타입인데 `listOf()` 는 `Empty list doesn't contain element at index 0.`(stdlib 의 `EmptyList`), `mutableListOf()` 는 **`Index 0 out of bounds for length 0`**(JDK 의 `ArrayList`)다. 앞은 Kotlin stdlib 문장, 뒤는 **JDK 문장**이다.
- ★★ `[0]`(`get`)도 같다(`8`·`9`) — `elementAt` 은 `List` 에서 **`get` 으로 내려간다**는 것이 메시지로 보인다.
- ★ 그래서 **메시지 문자열을 `catch` 의 근거로 쓰면 안 된다** — 받는 쪽이 `listOf` 에서 `mutableListOf` 로 바뀌기만 해도 문장이 바뀐다. **예외 클래스**(와 애초에 `…OrNull` 을 쓰는 것)가 근거다.

### (3) ★★ 공허한 참과 `single` — stdlib 소스

```text
===== unzip -o -q kotlin-stdlib-sources.jar commonMain/generated/_Collections.kt commonMain/generated/_Maps.kt commonMain/kotlin/collections/Maps.kt commonMain/kotlin/collections/SlidingWindow.kt jvmMain/generated/_CollectionsJvm.kt =====
(exit 0)
```

```text
===== sed -n '1935,1948p' commonMain/generated/_Collections.kt =====
/**
 * Returns `true` if all elements match the given [predicate].
 * 
 * Note that if the collection contains no elements, the function returns `true`
 * because there are no elements in it that _do not_ match the predicate.
 * See a more detailed explanation of this logic concept in ["Vacuous truth"](https://en.wikipedia.org/wiki/Vacuous_truth) article.
 * 
 * @sample samples.collections.Collections.Aggregates.all
 */
public inline fun <T> Iterable<T>.all(predicate: (T) -> Boolean): Boolean {
    if (this is Collection && isEmpty()) return true
    for (element in this) if (!predicate(element)) return false
    return true
}
(exit 0)
```

```text
===== sed -n '617,623p' commonMain/generated/_Collections.kt =====
public fun <T> List<T>.single(): T {
    return when (size) {
        0 -> throw NoSuchElementException("List is empty.")
        1 -> this[0]
        else -> throw IllegalArgumentException("List has more than one element.")
    }
}
(exit 0)
```

- ★★★ **`all` 의 공허한 참은 KDoc 계약이다** — 「``Note that if the collection contains no elements, the function returns `true` because there are no elements in it that _do not_ match the predicate.``」 — 위키백과 「Vacuous truth」 링크까지 달려 있다. 구현 첫 줄도 `if (this is Collection && isEmpty()) return true`.
- ★★ **`List.single()` 은 `when (size)` 세 갈래** — `0` 이면 `NoSuchElementException("List is empty.")`, `1` 이면 원소, **그 밖이면 `IllegalArgumentException("List has more than one element.")`**. 격자의 두 예외가 이 세 줄이다.
- ★ 이 메시지 문구들은 **구현**이다 — KDoc 이 약속하는 것은 「예외를 던진다」와 (`first` 의) `@throws NoSuchElementException` 까지다.

### (4) ★ `max()` — 판에 따라 뜻이 바뀐 이름

```kotlin
// mx43.kt
fun main() {
    println(listOf(3, 1, 2).max())
}
```

```text
===== grep -n -B4 -E '^public fun <T : Comparable<T>> Iterable<T>\.max\(\)' commonMain/generated/_Collections.kt jvmMain/generated/_CollectionsJvm.kt =====
commonMain/generated/_Collections.kt-2266- */
commonMain/generated/_Collections.kt-2267-@SinceKotlin("1.7")
commonMain/generated/_Collections.kt-2268-@kotlin.jvm.JvmName("maxOrThrow")
commonMain/generated/_Collections.kt-2269-@Suppress("CONFLICTING_OVERLOADS")
commonMain/generated/_Collections.kt:2270:public fun <T : Comparable<T>> Iterable<T>.max(): T {
--
jvmMain/generated/_CollectionsJvm.kt-78-
jvmMain/generated/_CollectionsJvm.kt-79-@Deprecated("Use maxOrNull instead.", ReplaceWith("this.maxOrNull()"))
jvmMain/generated/_CollectionsJvm.kt-80-@DeprecatedSinceKotlin(warningSince = "1.4", errorSince = "1.5", hiddenSince = "1.6")
jvmMain/generated/_CollectionsJvm.kt-81-@Suppress("CONFLICTING_OVERLOADS")
jvmMain/generated/_CollectionsJvm.kt:82:public fun <T : Comparable<T>> Iterable<T>.max(): T? {
(exit 0)
===== javap -cp kotlin-stdlib.jar kotlin.collections.CollectionsKt___CollectionsKt kotlin.collections.CollectionsKt___CollectionsJvmKt | grep -E ' (max|maxOrThrow|maxOrNull)\(' =====
  public static final double maxOrThrow(java.lang.Iterable<java.lang.Double>);
  public static final float maxOrThrow(java.lang.Iterable<java.lang.Float>);
  public static final <T extends java.lang.Comparable<? super T>> T maxOrThrow(java.lang.Iterable<? extends T>);
  public static final java.lang.Double maxOrNull(java.lang.Iterable<java.lang.Double>);
  public static final java.lang.Float maxOrNull(java.lang.Iterable<java.lang.Float>);
  public static final <T extends java.lang.Comparable<? super T>> T maxOrNull(java.lang.Iterable<? extends T>);
  public static final java.lang.Double max(java.lang.Iterable);
  public static final java.lang.Float max(java.lang.Iterable);
  public static final java.lang.Comparable max(java.lang.Iterable);
(exit 0)
===== kotlinc mx43.kt -d o43n =====
(exit 0)
===== java -cp o43n:kotlin-stdlib.jar Mx43Kt =====
3
(exit 0)
===== javap -c -p o43n/Mx43Kt.class | grep -E 'CollectionsKt\.max' =====
      33: invokestatic  #24                 // Method kotlin/collections/CollectionsKt.maxOrThrow:(Ljava/lang/Iterable;)Ljava/lang/Comparable;
(exit 0)
```

```text
===== kotlinc -api-version 1.6 mx43.kt -d o43x =====
error: API version 1.6 is no longer supported; use version 2.0 or greater instead.
(exit 1)
```

```text
   판      Iterable<T>.max()                             근거(위 grep)
   ─────────────────────────────────────────────────────────────────────────
   1.4 전  max(): T?   빈 입력이면 null (반환 타입의 ?)  옛 선언 — 경고가 붙기 전
   1.4     max(): T?   경고 「Use maxOrNull instead.」   warningSince = "1.4"
   1.5     max(): T?   에러                              errorSince   = "1.5"
   1.6     max(): T?   숨김(부를 수 없다)                hiddenSince  = "1.6"
   1.7~    max(): T    빈 입력이면 NoSuchElementException   @SinceKotlin("1.7") · JvmName("maxOrThrow")
```

- ★★★ **같은 `xs.max()` 가 1.3 까지는 `null` 을 돌려주고, 1.7 부터는 던진다** — 옛 선언은 반환 타입이 **`T?`**, 새 선언은 **`T`** 다. 그 사이 세 판(1.4 경고 → 1.5 에러 → 1.6 숨김)은 **이름을 비워 두는 기간**이었다 — 소스 애너테이션이 그렇게 적는다.
- ★★ **새 `max()` 는 JVM 에서 `maxOrThrow` 라는 이름이다** — `mx43.kt` 의 `listOf(3, 1, 2).max()` 가 `CollectionsKt.maxOrThrow` 를 부르도록 컴파일됐다(`javap -c`). **옛 `max` 는 JVM stdlib 에 아직 있다**(`java.lang.Comparable max(java.lang.Iterable)` — 왜 남겼는지는 확인하지 않았다. 옛 판으로 컴파일된 바이너리를 위한 것으로 **보인다**). 이름이 같아 보여도 **바이트코드에서는 다른 메서드**다.
- ★★ **옛 판에서 직접 컴파일해 보는 것은 못 했다** — `-api-version 1.6` 을 주자 kotlinc 2.4.20 이 「`API version 1.6 is no longer supported; use version 2.0 or greater instead.`」로 거부했다. 그래서 위 표의 1.4\~1.6 칸은 **실행 관찰이 아니라 애너테이션을 읽은 것**이다(제5의 상태 — (0)).

## 문법 — 형태와 규칙

**형태** — 비어 있을 수 있는 목록에서 찾기·걸러내기·검사.

```kotlin
// form43.kt
data class User(val name: String, val age: Int)

fun main() {
    val users = listOf(User("kim", 31), User("lee", 17))
    val none = emptyList<User>()
    println("1 ${users.firstOrNull { it.age >= 18 }?.name ?: "(none)"}")
    println("2 ${none.firstOrNull { it.age >= 18 }?.name ?: "(none)"}")
    println("3 ${users.filter { it.age >= 18 }.map { it.name }}")
    println("4 all adults? ${users.all { it.age >= 18 }}  empty: ${none.all { it.age >= 18 }}")
    println("5 ${none.isNotEmpty() && none.all { it.age >= 18 }}")
}
```

```text
===== kotlinc form43.kt -d o43z =====
(exit 0)
===== java -cp o43z:kotlin-stdlib.jar Form43Kt =====
1 kim
2 (none)
3 [kim]
4 all adults? false  empty: true
5 false
(exit 0)
```

**규칙 불릿**

- **비어 있을 수 있으면 `…OrNull` 또는 `find`** — `?:` 로 기본값을 붙인다(`1`·`2`).
- **`first()`·`last()`·`single()`·`elementAt()`·`max()`·`random()` 은 빈 입력에서 던진다**((1)).
- **`single()` 은 「정확히 하나」** — 둘 이상에서도 던진다((1)(3)).
- **`all{}` 은 빈 입력에서 `true`** — 「원소가 있고 전부 만족」이 필요하면 `isNotEmpty() && all { }`(`4`·`5`).
- **`filter` 는 절대 던지지 않는다** — 없으면 `[]`((1)).
- 예외를 잡을 때는 **클래스로** 잡는다 — 메시지는 받는 쪽마다 다르다((2)).

## 어디서 틀리나

1. ★★★ **`all{}` 이 빈 입력에서 `false` 라고 믿는다.** `true` 다((1)(3)) — 「모든 권한이 허용됐나」를 빈 권한 목록에 물으면 **허용**이 나온다.
2. ★★★ **`single()` 을 「첫 번째 것」으로 쓴다.** 둘 이상이면 `IllegalArgumentException` 이다((1)).
3. ★★ **`singleOrNull()` 의 `null` 을 「없다」로 읽는다.** 「너무 많다」도 `null` 이다((1)).
4. ★★ **`first{}` 가 「맞는 것 없음」에서는 `null` 을 준다고 본다.** 던진다 — `firstOrNull{}` 이나 `find{}` 를 쓴다((1)).
5. ★★ **예외 메시지 문자열로 분기한다.** 같은 `first()` 가 `List`·`Set`·`Sequence` 에서 **세 문장**, 같은 `elementAt(0)` 이 `listOf`·`mutableListOf` 에서 **두 문장**이다((2)).
6. ★ **`elementAt(0)` 이 `NoSuchElementException` 을 던진다고 본다.** `IndexOutOfBoundsException` 이다((1)).
7. ★ **옛 코드의 `max()` 가 `null` 을 돌려주던 기억으로 새 코드를 읽는다.** 1.7 부터는 던진다((4)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `…OrNull`·`find`·`maxOrNull` 이 `null` 을 준다 | ★★★ **API 계약(반환 타입 `T?`)** | (1) |
| `all{}` 이 빈 입력에서 `true` | ★★★ **API 계약(KDoc)** | (3) |
| `first()`·`max()` 가 빈 입력에서 `NoSuchElementException` | ★★ **API 계약(KDoc `@throws`)** — 이 문서는 `max()` 의 `@throws` 를 발췌하지 않았고 `first()` 쪽 KDoc 도 싣지 않았다 | (1) · 2-summary 에 실은 것은 **실행 결과** |
| `single()` 이 둘 이상에서 `IllegalArgumentException` | ★ **stdlib 구현** — KDoc 은 「throws an exception」까지 | (3) |
| 예외 **메시지 문구** 전부 | ★★ **stdlib·JDK 구현** — 받는 쪽 타입·클래스에 따라 갈린다 | (2) |
| `max()` 가 JVM 에서 `maxOrThrow` · 옛 `max` 가 남아 있다 | ★ **JVM stdlib 구현** — 남긴 이유는 **확인 안 함** | (4) |
| 1.4\~1.6 의 경고·에러·숨김 | **stdlib 소스의 애너테이션** — 그 판에서 **컴파일해 보지 못했다** | (4) |

★★ **가장 조심할 자리** — **예외 클래스는 격자에서 안 흔들렸지만 메시지는 받는 쪽 하나로 바뀌었다**((2)). 「이 판에서 결정적」과 「언제나 같은 문장」은 다르다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 없을 수도 있는 첫 원소 | `firstOrNull()` · `firstOrNull{}` · `find{}` | (1) — `null` |
| 반드시 있어야 한다(없으면 버그) | `first()` · `first{}` | (1) — 던져서 드러낸다 |
| 정확히 하나여야 한다 | `single()` · `single{}` | (1)(3) — 없음·많음을 **클래스로** 가른다 |
| 하나이거나 없다(많음도 「없음」 취급) | `singleOrNull()` | (1) — ★ 많음과 없음이 섞인다 |
| 「원소가 있고 전부」 | `isNotEmpty() && all { }` | (1) — `all` 만으로는 빈 입력이 참 |
| 조건에 맞는 것 전부 | `filter{}` | (1) — 절대 안 던진다 |
| 최댓값(빈 입력 가능) | `maxOrNull()` | (1)(4) |

## 핵심 문장

1. 빈 입력에서 **`first()`·`last()`·`single()`·`elementAt()`·`max()`·`random()` 은 던지고**, `…OrNull`·`find` 는 `null`, `any`·`all`·`none`·`filter` 는 정해진 값을 준다 — 격자 68칸 중 **13칸이 던졌다.**
2. **`all{}` 은 빈 입력에서 `true`**(공허한 참)다 — KDoc 이 약속한다.
3. **`single()` 은 둘 이상에서도 던지고**, 그 예외는 빈 입력과 **클래스가 다르다**(`IllegalArgumentException` 대 `NoSuchElementException`).
4. 예외 **메시지는 받는 쪽마다 다르다** — 근거로 쓸 것은 **클래스**다.
5. `max()` 는 **1.7 부터 던지는 쪽**으로 뜻이 바뀌었고, JVM 에서는 **`maxOrThrow`** 다.

## 관련 자료

- [41번 주제](../41-collection-creation-and-copying/) — ★★★ **선행.** `emptyList()` 는 싱글턴 `EmptyList` — 그 객체가 (2)의 `Empty list doesn't contain …` 문장을 낸다.
- [03번 주제](../03-null-safe-types/) — `?:` 로 `…OrNull` 결과에 기본값.
- [34번 주제](../34-exceptions-nothing-and-try-expression/) — `try` 가 식이다(격자의 `val cell = try { … }`).
- [40번 주제](../40-read-only-collections-and-runtime-types/) — `javap` 창.
- [Java 46번](../../../java/syntax/46-terminal-operations/) — Java 스트림은 `findFirst`·`max` 가 **`Optional`** 을 돌려준다(여기 `…OrNull` 과 같은 자리). 이 문서는 Java 쪽을 다시 돌리지 않았다.
- [42번 주제](../42-transformations-map-flatmap-associate-zip/) — 변환 연산. [44번 주제](../44-aggregation-grouping-fold-reduce/) — 집계(`reduce` 도 빈 입력에서 던진다).

## 용어 풀이

> **공허한 참(vacuous truth)** — 「모든 X 가 P 다」에서 X 가 **하나도 없으면** 참이 되는 것. 어기는 X 가 없기 때문이다.\
> 예: `emptyList<Int>().all { it > 5 }` → `true`.

> **술어(predicate)** — 원소를 받아 `Boolean` 을 돌려주는 람다. 이 문서에서는 `{ it > 5 }`.

> **`NoSuchElementException`** — 「찾는 원소가 없다」. Kotlin 에서는 `java.util.NoSuchElementException` 의 별칭이다.

> **`IllegalArgumentException`** — 「받은 입력이 조건에 안 맞는다」. `single()` 은 원소가 둘 이상인 것을 이것으로 알린다.

> **`@JvmName`** — Kotlin 선언을 JVM 에서 **다른 이름**으로 내보내는 애너테이션. 새 `max()` 가 `maxOrThrow` 가 된 것.

> **`-api-version`** — 「이 판의 stdlib API 까지만 쓰겠다」고 컴파일러에게 알리는 옵션. kotlinc 2.4.20 은 **2.0 미만을 거부**했다.

## 더 들어가면

- **`last{}`·`lastOrNull{}`·`findLast{}`** — 격자에 넣지 않았다. `first` 쪽과 같은 모양일 것으로 보이지만 **던지지 않았다.**
- **`Sequence` 의 `single()`** — (2)에서 `Sequence.first()` 가 `Sequence is empty.` 였다. `single()` 의 「둘 이상」 문구가 무엇인지는 **던지지 않았다.**
- **`randomOrNull`** — 이름만 적었다. 돌리지 않았다.
