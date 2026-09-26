# kotlin/syntax/43 — 필터·검색 — `filter`/`find`/`first`/`any`/`all`/`none` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`·`javap` 에서 실제로 얻었다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **던진 칸 13 / 68** — 빈 입력에서 8칸(`first()`·`first{}`·`last()`·`single()`·`single{}`·`elementAt(0)`·`max()`·`random`), 비지 않은 입력에서 5칸(`first{}`·`single()`·`single{}`)

**출력**

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

**왜 그런가**

- ★★★ 던지는 연산의 클래스는 **셋뿐**이다 — 「없다」는 **`NoSuchElementException`**, 「너무 많다」는 **`IllegalArgumentException`**(`single`·`single{}`), 「그 인덱스가 없다」는 **`IndexOutOfBoundsException`**(`elementAt`).
- ★★ `…OrNull`·`find{}` 는 **한 칸도 안 던졌다** — 반환 타입의 `?` 가 그 약속이다.
- ★★ `filter{}`·`any`·`all{}`·`none{}` 은 **정해진 값**을 준다 — 예외도 `null` 도 아니다.
- ★ `max()` 의 빈 입력 칸은 **메시지가 `null`** 이다(`NoSuchElementException: null`) — 인자 없이 던지기 때문이다.

### 2. ★★★ **`all{}` → `true` · `any{}` → `false` · `none{}` → `true`** — `all{}` 과 `none{}` 이 같은 `true` 다

**출력** — 1번 격자의 `all{}`·`any{}`·`none{}` 행, `empty` 열.

**왜 그런가**

- ★★★ `all` 은 「어기는 원소가 **하나라도** 있나」를 찾는다 — 원소가 없으니 **못 찾고**, 그래서 `true`(6번).
- ★★ `none{}` 은 「맞는 원소가 **하나라도** 있나」의 부정 — 없으니 `true`. `any{}` 는 그 긍정이라 `false`.
- ★ 비지 않은 입력에서는 `all{}` 과 `none{}` 이 **동시에 `true` 일 수 없다**(어느 원소든 둘 중 하나를 어긴다) — 격자에서도 빈 입력 한 칸뿐이다.

### 3. ★★ `single()` 은 `no-match`·`two-match` 둘 다 **`IllegalArgumentException: List has more than one element.`**(빈 입력의 `NoSuchElementException` 과 **다른 클래스**) · `singleOrNull()` 은 둘 다 **`null`**

**출력** — 1번 격자의 `single()`·`singleOrNull()` 행.

**왜 그런가**

- ★★★ `single()` 은 **술어를 안 받는다** — `[1, 2]` 도 `[6, 8]` 도 「원소 둘」일 뿐이다. 소스가 `when (size)` 의 `else` 로 `IllegalArgumentException` 을 던진다(2-summary (3)).
- ★★ 그래서 `single()` 은 「없음」과 「너무 많음」을 **예외 클래스로 가른다.** `singleOrNull()` 은 그 둘을 **같은 `null`** 로 합친다(7번).
- ★ 술어를 받는 `single{}` 은 `no-match` 에서 `NoSuchElementException`, `two-match` 에서 `IllegalArgumentException` — **술어 기준으로** 센다.

### 4. ★★ **클래스는 두 가지뿐**(`first()` 넷은 `java.util.NoSuchElementException`, `elementAt`·`[0]` 다섯은 `java.lang.IndexOutOfBoundsException`) · **메시지가 줄마다 달라진다** — `List`·`Set`·`Sequence` 가 세 문장, `listOf()` 와 `mutableListOf()` 가 두 문장

**출력**

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

**왜 그런가**

- ★★★ `first()` 는 **받는 쪽 타입에 맞는 확장**이 골라진다 — `List.first()` 는 `List is empty.`, `Iterable.first()` 는 `Collection is empty.`, `Sequence.first()` 는 `Sequence is empty.`. 셋 다 **같은 클래스**다.
- ★★★ `elementAt(0)` 과 `[0]` 은 **객체의 `get`** 까지 내려간다 — `listOf()` 는 stdlib 의 `EmptyList` 라 `Empty list doesn't contain element at index 0.`, `mutableListOf()` 는 JDK 의 `ArrayList` 라 **`Index 0 out of bounds for length 0`** 이다. **같은 `List<Int>` 타입**인데 문장이 다르다.
- ★ 그래서 근거는 **클래스**다(8번).

### 5. **`CollectionsKt.maxOrThrow`** 를 부른다(출력은 `3`) · 빈 리스트였다면 **`NoSuchElementException`**(메시지 `null`)

**출력**

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

**왜 그런가**

- ★★ 새 `max()` 선언에 **`@kotlin.jvm.JvmName("maxOrThrow")`** 가 붙어 있다 — Kotlin 에서는 `max`, JVM 에서는 `maxOrThrow` 다.
- ★★ JVM stdlib 에는 **옛 `max`**(반환이 `java.lang.Comparable` 인 것)도 아직 있다 — 소스의 `jvmMain/…/_CollectionsJvm.kt` 82행이 그것이고 `hiddenSince = "1.6"` 이라 **새 코드에서는 부를 수 없다.**
- ★ 빈 입력 칸은 1번 격자의 `max()` 행(`! NoSuchElementException: null`)이다.

### 6. **KDoc 계약이다** — 「``Note that if the collection contains no elements, the function returns `true` …``」 · 논리의 이름은 **공허한 참(vacuous truth)**

**왜 그런가**

- ★★★ 2-summary (3)의 발췌 — `all` 의 KDoc 이 그 문장과 위키백과 「Vacuous truth」 링크를 싣고, 구현 첫 줄이 `if (this is Collection && isEmpty()) return true` 다.
- ★ 계약이므로 판이 올라도 바뀌지 않을 것으로 **기대해도 된다** — 반대로 「빈 목록이면 거부」가 필요하면 **부르는 쪽이** `isNotEmpty()` 를 붙인다.

### 7. **말할 수 없다** — `null` 은 「없음」**또는** 「둘 이상」이다

**왜 그런가**

- ★★ 3번의 `singleOrNull()` 행 — `empty` 도 `two-match` 도 `null` 이다.
- ★ 둘을 가르려면 `single()` 의 **예외 클래스**(3번)를 쓰거나, `filter{}` 결과의 **크기**를 본다.

### 8. **받는 쪽이 바뀌는 순간 깨진다** — `Set` 이면 `Collection is empty.`, `Sequence` 면 `Sequence is empty.`, `elementAt` 이면 `mutableListOf` 와 `listOf` 가 다르다

**왜 그런가**

- ★★★ 4번이 보였다 — **클래스는 한 번도 안 바뀌고 메시지만 바뀌었다.** 메시지는 stdlib·JDK 의 **구현 문장**이다.
- ★ 이 문서가 본 것은 **한 판**(2.4.20 · JDK 21.0.5)이다 — 판이 오르면 문장 자체가 바뀔 수도 있다. 그것은 **재지 않았다.**

### 9. 1.4 이전에는 **`null`**(반환 `T?`) · 1.4 **경고** → 1.5 **에러** → 1.6 **숨김** → 1.7 **던지는 새 `max()`** · 확인은 **stdlib 소스의 애너테이션**으로 했고, **그 판에서 컴파일해 보는 것은 못 했다**

**왜 그런가**

- ★★ 5번의 `grep` — 옛 선언에 `@DeprecatedSinceKotlin(warningSince = "1.4", errorSince = "1.5", hiddenSince = "1.6")`, 새 선언에 `@SinceKotlin("1.7")`.
- ★★ **못 한 것** — `kotlinc -api-version 1.6` 이 거부됐다:

```text
===== kotlinc -api-version 1.6 mx43.kt -d o43x =====
error: API version 1.6 is no longer supported; use version 2.0 or greater instead.
(exit 1)
```

- ★ 그래서 「1.5 에서 정말 컴파일 에러였나」는 **애너테이션이 그렇게 적혀 있다**까지다 — 실행 관찰이 아니다(2-summary (0)의 제5의 상태).

### 10. **`Optional.empty`** 를 돌려준다 — Kotlin 의 **`firstOrNull()`·`maxOrNull()`** 자리다(`null` 대신 `Optional`)

**왜 그런가**

- ★★ [Java 46번](../../../java/syntax/46-terminal-operations/)이 실측했다 — `빈 findFirst : Optional.empty` · `빈 min : Optional.empty`. 이 문서는 Java 쪽을 **다시 돌리지 않았다.**
- ★ Java 46번의 종단 연산 표에서 `min`·`max`·`findFirst`·`findAny` 는 전부 `Optional` 을 돌려준다 — 던지려면 **부르는 쪽이** `Optional` 을 푼다. Kotlin 은 던지는 이름(`first`)과 `null` 을 주는 이름(`firstOrNull`)을 **나란히** 둔다.

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
===== javap -version =====
21.0.5
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — `random` 은 `Random(42)` 로 고정했다 | 격자 17행 × 4열 · 던진 칸 수 · 예외 클래스 |
| | 예외 메시지(이 판에서) · `javap` 출력 · stdlib 소스 발췌 |
| | 진단 문구 · 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 60개 · 동일 59 · 흔들린 칸 1 · ★고칠 것 0**(42\~45 네 주제를 한 캡처로 받았다). 흔들린 1블록은 44번의 Rust 패닉 블록(`a44-rs`)이고, 원문 차이는 **패닉 첫 줄의 스레드 id** 하나였다 — 기본 정규화 규칙(스레드 id)이 그것을 지웠다.\
> ★ 추가한 정규화 규칙은 **없다**.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `empty43.kt` · `grid43.py` | ★★★ 빈 입력 격자 — 17연산 × 4입력 | `kotlinc` → 스크립트가 `java` |
| `msg43.kt` | ★★ 같은 연산 · 다른 받는 쪽의 클래스와 메시지 | `kotlinc` → `java` |
| `_Collections.kt`(stdlib 소스 jar) | `all` 의 KDoc · `List.single()` | `unzip` → `sed -n` |
| `_Collections.kt` · `_CollectionsJvm.kt` · stdlib jar | `max()` 의 옛·새 선언 · JVM 메서드 이름 | `grep` · `javap` |
| `mx43.kt` | `max()` 가 `maxOrThrow` 로 컴파일된다 · `-api-version 1.6` 거부 | `kotlinc` → `java` · `javap -c` · `kotlinc -api-version 1.6`(실패가 결과) |
| `form43.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — 예외 **메시지 문구** 전부 · `single()` 이 `IllegalArgumentException` 인 것 · `max()` 의 JVM 이름 `maxOrThrow` 와 옛 `max` 의 잔존 — 이 stdlib·JDK 판의 산출물이다.\
반면 **`…OrNull` 의 `null`**(반환 타입) · **`all` 의 공허한 참**(KDoc) 은 **API 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **같은 `elementAt(0)` 이 `listOf()` 와 `mutableListOf()` 에서 다른 문장을 냈다** — 타입이 같아도 **런타임 클래스가 문장을 고른다**(4번).
2. ★★ **`max()` 의 빈 입력 예외에 메시지가 없었다**(`null`) — 다른 연산은 전부 문장을 달았다(1번).
3. ★ **옛 판 `max()` 를 직접 컴파일해 볼 수 없었다** — kotlinc 2.4.20 이 `-api-version` 2.0 미만을 거부했다(9번).
