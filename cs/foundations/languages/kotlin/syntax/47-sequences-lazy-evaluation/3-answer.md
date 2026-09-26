# kotlin/syntax/47 — `Sequence` — 지연 평가, 언제 `List` 보다 싼가 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`·`javap` 에서 실제로 얻었다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **8 / 10** — 끝이 `first`·`take3` 인 사슬은 `Sequence` 가 **입력 크기와 무관하게** 줄였고, **`map>filter>toList` 두 칸만 호출 수가 같다** · `Sequence` 열은 전부 `coll=0`

**출력**

```text
===== kotlinc grid47.kt -d o47g =====
(exit 0)
===== java -cp o47g:kotlin-stdlib.jar Grid47Kt =====
chain	n	List	Sequence
map>filter>first	10	map=10 filter=10 coll=2	map=4 filter=4 coll=0
map>filter>first	1000	map=1000 filter=1000 coll=2	map=4 filter=4 coll=0
map>filter>toList	10	map=10 filter=10 coll=2	map=10 filter=10 coll=0
map>filter>toList	1000	map=1000 filter=1000 coll=2	map=1000 filter=1000 coll=0
map>sorted>filter>first	10	map=10 filter=10 coll=3	map=10 filter=4 coll=0
map>sorted>filter>first	1000	map=1000 filter=1000 coll=3	map=1000 filter=4 coll=0
map>distinct>filter>first	10	map=10 filter=10 coll=3	map=4 filter=4 coll=0
map>distinct>filter>first	1000	map=1000 filter=1000 coll=3	map=4 filter=4 coll=0
map>filter>take3>toList	10	map=10 filter=10 coll=3	map=6 filter=6 coll=0
map>filter>take3>toList	1000	map=1000 filter=1000 coll=3	map=6 filter=6 coll=0
cells where the Sequence column made fewer lambda calls: 8 / 10
(exit 0)
```

**왜 그런가**

- ★★★ `Sequence` 는 끝 연산이 원소를 **하나씩** 당긴다 — `first` 는 첫 합격(`6`, 네 번째 원소)에서, `take3` 은 세 번째 합격(여섯 번째 원소)에서 멈춘다. 그래서 크기 10 과 1000 이 **같은 수**다.
- ★★★ `toList` 는 **전부**를 당긴다 — 모든 원소가 `map`·`filter` 를 지나 `List` 와 같다.
- ★★ `sorted` 는 앞쪽(`map`)을 **전부** 당긴 뒤 원소별로 내보낸다(`map=1000 filter=4`). `distinct` 는 당기지 않는다(`map=4`).
- ★★ `List` 열의 `coll` 은 **단계마다 새 리스트**(`map`·`filter`·`sorted`·`distinct`·`take`)다. `Sequence` 열의 단계 출력은 전부 래퍼라 0 — 단, 단계 **안에** 숨은 컬렉션은 이 칸이 못 센다(2-summary (3)).

### 2. ★★★ `A` 는 **`map` 셋 → `filter` 셋** · `B` 는 **`map`/`filter` 가 번갈아** · `C` 는 **`map` 셋 뒤 `filter` 둘** · `D` 는 **`map` 셋(그중 하나는 `filter` 없이)** · `E`\~`F` 사이는 **아무것도 없다**

**출력**

```text
===== kotlinc order47.kt -d o47o =====
(exit 0)
===== java -cp o47o:kotlin-stdlib.jar Order47Kt =====
-- A
  map 3
  map 1
  map 2
  filter 30
  filter 10
  filter 20
  result [30, 20]
-- B
  map 3
  filter 30
  map 1
  filter 10
  map 2
  filter 20
  result [30, 20]
-- C
  map 3
  map 1
  map 2
  filter 10
  filter 20
  result 20
-- D
  map 3
  filter 30
  map 3
  map 1
  filter 10
  result 10
-- E
-- F
  kotlin.sequences.TransformingSequence
(exit 0)
```

**왜 그런가**

- ★★★ `List` 연산은 **즉시** — `map` 이 리스트를 다 만든 뒤 `filter` 가 돈다. `Sequence` 는 **원소별** — 원소 하나가 `map`·`filter` 를 다 지난 뒤 다음 원소가 올라온다.
- ★★★ `C` 의 `sorted` 는 정렬하려고 `map 3·1·2` 를 **먼저 다** 당기고, 정렬된 `10`·`20` 을 차례로 `filter` 에 흘린다 — `20` 에서 `first` 가 멈춘다.
- ★★ `D` 의 `distinct` 는 두 번째 `3`(→`30`)을 **이미 봤으므로 버린다** — 그래서 `map 3` 뒤에 `filter` 가 없다. `1`(→`10`)이 합격해 멈춘다. `2` 는 **`map` 조차 안 불렸다.**
- ★★ 끝 연산이 없는 `pending` 은 람다를 한 번도 안 불렀다 — `E` 와 `F` 사이가 비었다는 것이 그 증거다.

### 3. ★★ `List` 는 **`ArrayList` 셋**, `Sequence` 는 **래퍼 셋(익명 · `TransformingSequence` · `FilteringSequence`) 뒤에 `ArrayList` 하나** · `sorted` 는 익명 객체 · `distinct` 는 `DistinctSequence`

**출력**

```text
===== kotlinc kinds47.kt -d o47k =====
(exit 0)
===== java -cp o47k:kotlin-stdlib.jar Kinds47Kt =====
List      java.util.ArrayList > java.util.ArrayList > java.util.ArrayList
Sequence  kotlin.collections.CollectionsKt___CollectionsKt$asSequence$$inlined$Sequence$1 > kotlin.sequences.TransformingSequence > kotlin.sequences.FilteringSequence > java.util.ArrayList
sorted    kotlin.sequences.SequencesKt___SequencesKt$sorted$1
distinct  kotlin.sequences.DistinctSequence
(exit 0)
```

**왜 그런가**

- ★★ `List` 쪽은 원본·`map` 결과·`filter` 결과가 **각각 리스트**다 — 중간 리스트는 `a1` 하나다.
- ★★ `Sequence` 쪽은 **리스트가 끝(`toList`)에만** 있다 — 대신 단계 수만큼 래퍼가 있다. `sorted`·`distinct` 도 **아직 모으지 않은 래퍼**다.

### 4. ★★ **`4`(씨앗 없는 `generateSequence`)와 `6`(`Iterator.asSequence()`)만 두 번째에 `IllegalStateException`** · `block starts` 는 **두 번**

**출력**

```kotlin
// once47.kt
fun twice(label: String, s: Sequence<Int>) {
    for (round in 1..2) {
        try {
            println("$label  round $round -> ${s.toList()}")
        } catch (e: IllegalStateException) {
            println("$label  round $round -> ${e::class.simpleName}: ${e.message}")
        }
    }
}

fun main() {
    twice("1 sequenceOf              ", sequenceOf(1, 2, 3))
    twice("2 List.asSequence()       ", listOf(1, 2, 3).asSequence())
    twice("3 generateSequence(seed)  ", generateSequence(1) { if (it < 3) it + 1 else null })
    var i = 0
    twice("4 generateSequence { }    ", generateSequence { if (i < 3) ++i else null })
    twice("5 sequence { }            ", sequence { println("   block starts"); yield(1); yield(2) })
    twice("6 Iterator.asSequence()   ", listOf(1, 2, 3).iterator().asSequence())
    twice("7 Sequence { iterator }   ", Sequence { listOf(1, 2).iterator() })
}
```

```text
===== kotlinc once47.kt -d o47n =====
(exit 0)
===== java -cp o47n:kotlin-stdlib.jar Once47Kt =====
1 sequenceOf                round 1 -> [1, 2, 3]
1 sequenceOf                round 2 -> [1, 2, 3]
2 List.asSequence()         round 1 -> [1, 2, 3]
2 List.asSequence()         round 2 -> [1, 2, 3]
3 generateSequence(seed)    round 1 -> [1, 2, 3]
3 generateSequence(seed)    round 2 -> [1, 2, 3]
4 generateSequence { }      round 1 -> [1, 2, 3]
4 generateSequence { }      round 2 -> IllegalStateException: This sequence can be consumed only once.
   block starts
5 sequence { }              round 1 -> [1, 2]
   block starts
5 sequence { }              round 2 -> [1, 2]
6 Iterator.asSequence()     round 1 -> [1, 2, 3]
6 Iterator.asSequence()     round 2 -> IllegalStateException: This sequence can be consumed only once.
7 Sequence { iterator }     round 1 -> [1, 2]
7 Sequence { iterator }     round 2 -> [1, 2]
(exit 0)
```

**왜 그런가**

- ★★★ 두 번 돌 수 있는 것이 **기본**이고, 한 번 제한은 KDoc 에 「`only once`」가 적힌 만드는 함수에만 있다 — 씨앗 없는 `generateSequence` 와 `Iterator.asSequence`(반복자는 한 번 쓰면 끝이다).
- ★★★ `sequence { }` 는 반복할 때마다 **블록을 새로 실행**한다 — 두 번 돌고 **두 번 계산**한다.
- ★ 같은 이름 `generateSequence` 인데 씨앗 있는 꼴(`3`)은 두 번 돈다 — 매번 씨앗에서 다시 시작한다.

### 5. ★★ `viaList` 에 **두 번**(`map`·`filter`), `viaSequence` 에 **0번** — 대신 **`SequencesKt.map`·`filter`·`first` 호출**이 있다

**출력**

```text
===== kotlinc code47.kt -d o47c =====
(exit 0)
===== java -cp o47c:kotlin-stdlib.jar Code47Kt =====
6 6
(exit 0)
===== javap -c -p o47c/Code47Kt.class | grep -E 'public static final int|new .*ArrayList|SequencesKt|CollectionsKt' =====
  public static final int viaList(java.util.List<java.lang.Integer>);
      15: new           #20                 // class java/util/ArrayList
      22: invokestatic  #26                 // Method kotlin/collections/CollectionsKt.collectionSizeOrDefault:(Ljava/lang/Iterable;I)I
     114: new           #20                 // class java/util/ArrayList
     202: invokestatic  #71                 // Method kotlin/collections/CollectionsKt.first:(Ljava/util/List;)Ljava/lang/Object;
  public static final int viaSequence(java.util.List<java.lang.Integer>);
      10: invokestatic  #95                 // Method kotlin/collections/CollectionsKt.asSequence:(Ljava/lang/Iterable;)Lkotlin/sequences/Sequence;
      18: invokestatic  #121                // Method kotlin/sequences/SequencesKt.map:(Lkotlin/sequences/Sequence;Lkotlin/jvm/functions/Function1;)Lkotlin/sequences/Sequence;
      26: invokestatic  #132                // Method kotlin/sequences/SequencesKt.filter:(Lkotlin/sequences/Sequence;Lkotlin/jvm/functions/Function1;)Lkotlin/sequences/Sequence;
      29: invokestatic  #135                // Method kotlin/sequences/SequencesKt.first:(Lkotlin/sequences/Sequence;)Ljava/lang/Object;
      41: invokestatic  #143                // Method kotlin/collections/CollectionsKt.listOf:([Ljava/lang/Object;)Ljava/util/List;
      89: invokestatic  #143                // Method kotlin/collections/CollectionsKt.listOf:([Ljava/lang/Object;)Ljava/util/List;
(exit 0)
```

**왜 그런가**

- ★★ `Iterable.map`·`filter` 는 `inline` 이라 그 본문(`ArrayList` 를 만들고 채우는 고리)이 **호출한 함수 안에 풀린다** — 중간 리스트가 바이트코드에 **글자로** 보인다.
- ★ `Sequence.map`·`filter` 는 `inline` 이 아니다 — 래퍼를 만드는 **함수 호출** 한 번씩이고, 원소를 나르는 일은 래퍼의 반복자가 나중에 한다.

### 6. ★ `powers [1, 2, 4, 8, 16, 32, 64]` · `keys [a, b]` · `fib [0, 1, 1, 2, 3, 5, 8, 13]`

**출력**

```text
===== kotlinc form47.kt -d o47z =====
(exit 0)
===== java -cp o47z:kotlin-stdlib.jar Form47Kt =====
powers  [1, 2, 4, 8, 16, 32, 64]
keys    [a, b]
fib     [0, 1, 1, 2, 3, 5, 8, 13]
(exit 0)
```

**왜 그런가**

- ★ `generateSequence(1) { it * 2 }` 와 `sequence { while (true) … }` 는 **무한**하다 — `takeWhile`·`take` 가 끝을 정해 준다. `List` 로는 만들 수 없는 모양이다.
- ★ `keys` 는 `take(2)` 에서 멈춘다 — `c=3`·`d=4` 는 `filter` 도 `map` 도 **안 지났다.**

### 7. `sorted` 는 **`toMutableList()` 로 전부 모아 정렬**하고, `distinct` 는 **본 키의 `HashSet` 하나만 쥐고 원소별로** 내보낸다

**왜 그런가**

- ★★★ 2-summary (3)의 발췌 — `Sequence.sorted` 의 `iterator()` 가 `this@sorted.toMutableList()` → `sort()` 를 한다. `DistinctIterator` 는 `observed = HashSet<K>()` 에 `add` 가 참일 때만 `setNext(next)` 하고 **바로 돌아온다.**
- ★★ KDoc 분류는 둘 다 「`_intermediate_ and _stateful_`」 — **분류가 같아도 당기는 양은 다르다.** 정렬은 마지막 원소를 봐야 첫 원소를 알 수 있고, 중복 검사는 **지금까지 본 것**만 알면 된다.

### 8. **`map>filter>toList`** — 호출 수가 같고, `Sequence` 는 **래퍼 셋과 그 반복자**를 더 만든다(중간 리스트 하나를 아끼는 대신) · 시간은 **N판 판 격자 없이 한 판으로 말할 수 없어서** 재지 않았다

**왜 그런가**

- ★★ 1번의 두 칸(`map=10 filter=10` · `map=1000 filter=1000`)과 3번의 클래스 줄.
- ★★ 「객체 몇 개를 더 만들고 리스트 하나를 아꼈다」는 **세는 것**이라 결정적이지만, 그것이 **시간으로** 어느 쪽인지는 JIT·크기·원소 타입에 달린다 — 규칙 24 대로 판 격자 없이 적지 않는다.

### 9. KDoc — 「**두 번 돌 수 있다**, 다만 일부 구현은 스스로 **한 번으로 제한하고 그 사실을 문서에 적는다**」 · 구현은 **`AtomicReference.getAndSet(null)`**

**왜 그런가**

- ★★★ 2-summary (5)의 발췌 — `Sequence.kt` 「`Sequences can be iterated multiple times, however some sequence implementations might constrain themselves to be iterated only once. That is mentioned specifically in their documentation`」.
- ★★ `ConstrainedOnceSequence.iterator()` 는 원본 참조를 **꺼내며 `null` 로 바꾸고**, 두 번째 호출은 `null` 을 받아 `IllegalStateException("This sequence can be consumed only once.")` 를 던진다.

### 10. **원소별로 흐르고 `sorted` 에서 전부 모인다** — 같은 모양이다 · Kotlin 은 컬렉션 연산이 **기본 즉시**라 `asSequence()` 로 **명시적으로** 넘어가고, Java 는 `stream()` 이 곧 지연이다

**왜 그런가**

- ★★ [Java 45번](../../../java/syntax/45-intermediate-operations/)이 「작업대별이 아니라 원소별」과 「`sorted` 앞까지는 원소별로 흐르다가 전부 모일 때까지 막힌다」를 쟀다 — 2번의 `B`·`C` 와 같은 순서다. 이 문서는 Java 를 **다시 돌리지 않았다.**
- ★ 차이는 타입이다 — Java 는 컬렉션에 `map` 이 **없어서** 지연(`Stream`)이 유일한 길이고, Kotlin 은 `List.map`(즉시)과 `Sequence.map`(지연)이 **같은 이름으로 둘 다** 있다. 그래서 Kotlin 에서는 **어느 쪽인지 타입을 봐야** 안다.

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

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 실행 시간을 찍지 않았다 | 격자 10행 · 호출 수 · 컬렉션 수 · 줄인 칸 수 |
| | 순서 로그 · 두 번 돌기 · 런타임 클래스 이름 |
| | stdlib 소스 발췌(줄 번호째) · `javap` 의 명령·상수 풀 번호 · 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 71개 · 동일 71 · 흔들린 칸 0 · ★고칠 것 0**(46\~49 네 주제를 한 캡처로 받았다). 추가한 정규화 규칙은 **없다**.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `grid47.kt` | ★★★ 호출 수 격자 — 사슬 5 × 모양 2 × 크기 2 | `kotlinc` → `java` (칸 수 검사·줄인 칸 수는 프로그램이 센다) |
| `order47.kt` | ★★ 단계별 대 원소별 · `sorted`·`distinct` · 끝 연산 없음 | `kotlinc` → `java` (한 흐름 — 표준 출력만) |
| `kinds47.kt` | ★ 단계마다의 런타임 클래스 | `kotlinc` → `java` |
| `once47.kt` | ★★ 두 번 돌기 일곱 가지 | `kotlinc` → `java` |
| `code47.kt` | ★★ `new java/util/ArrayList` 개수 | `kotlinc` → `java` → `javap -c -p`(전부 받은 뒤 `grep`) |
| `_Sequences.kt` · `_Collections.kt` · `Sequence.kt` · `Sequences.kt` · `SequencesJVM.kt` · `SequenceBuilder.kt`(stdlib 소스 jar) | 분류 KDoc · 중간 컬렉션을 만드는 줄 · 한 번 제한 | `unzip` → `sed -n` |
| `form47.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — 래퍼 클래스 이름 · `sorted` 의 `toMutableList` · `distinct` 의 `HashSet` · 한 번 제한의 `AtomicReference` 와 메시지 — 이 stdlib 판의 산출물이다.\
반면 **지연·원소별 처리**(중간 연산 분류) · **상태 있음 분류** · **두 번 돌기 가능 여부(KDoc)** 는 **API 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 두 건**

1. ★★★ **`distinct` 는 첫 원소 전에 전부 끌어오지 않았다** — `sorted` 와 같은 「상태 있음」인데 원소별로 흘렀다(2번 `D`). 「상태 있음 = 전부 모은다」는 `sorted` 에만 맞다.
2. ★★ **`sequence { }` 는 「한 번만」이 아니라 「두 번 돌고 두 번 계산한다」였다** — 한 번 제한은 씨앗 없는 `generateSequence` 와 `Iterator.asSequence` 에 있었다.
