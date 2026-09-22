# java/syntax/28 — `Comparable`/`Comparator`: 전순서 계약과 조합 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·예외·컴파일 에러는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 실행 프로그램 다섯을 **17.0.13 · 25.0.1** 에서도 돌려 **출력이 한 글자도 다르지 않았다**\
> (관찰이다 — 보장은 javadoc 인용으로만 적었다).\
> 계약 조항은 `lib/src.zip` 의 javadoc 원문을, 임계 상수는 `TimSort.java` 소스를 그대로 인용했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 계약의 조항은 몇 개이고 각각 무엇인가

**"must ensure" 로 요구하는 조항은 셋이다** (`java.base/java/lang/Comparable.java` javadoc 원문)

> The implementor must ensure {@link Integer#signum signum}`(x.compareTo(y)) == -signum(y.compareTo(x))` for
> all `x` and `y`.  (This implies that `x.compareTo(y)` must throw an exception if and only if
> `y.compareTo(x)` throws an exception.)
>
> The implementor must also ensure that the relation is transitive:
> `(x.compareTo(y) > 0 && y.compareTo(z) > 0)` implies `x.compareTo(z) > 0`.
>
> Finally, the implementor must ensure that `x.compareTo(y)==0` implies that `signum(x.compareTo(z))
> == signum(y.compareTo(z))`, for all `z`.

```text
  ① 대칭성        signum(c(x,y)) == -signum(c(y,x))
  ② 추이성        c(x,y)>0 이고 c(y,z)>0 이면 c(x,z)>0
  ③ 동치의 일관성  c(x,y)==0 이면 모든 z 에 대해 signum(c(x,z))==signum(c(y,z))
```

**네 번째 조항과 강제 수준의 차이**

같은 파일의 `@apiNote` 다.

> It is strongly recommended, but *not* strictly required that `(x.compareTo(y)==0) == (x.equals(y))`.
> Generally speaking, any class that implements the `Comparable` interface and violates this condition
> should clearly indicate this fact.

| | ①②③ | ④ |
|---|---|---|
| 문구 | **"must ensure"** | **"strongly recommended, but *not* strictly required"** |
| 어기면 | 정렬 결과가 틀리거나 `IllegalArgumentException` | 정렬은 멀쩡하다. **`TreeSet`/`TreeMap` 이 달라진다** |
| JDK 안의 위반 사례 | 없다(있으면 버그다) | **`BigDecimal`** — javadoc 에 명시해 두었다(6번) |

**`Comparator.compare` 와의 차이**

- **강제 조항 셋은 문장까지 같다.** `x`·`y`·`z` 를 인자 자리로 옮겼을 뿐이다.
- 다른 것은 `null` 취급 하나뿐이다. `Comparator` 인터페이스 javadoc 원문:

> Unlike `Comparable`, a comparator may optionally permit comparison of null arguments, while maintaining
> the requirements for an equivalence relation.

**반사성이 왜 조항으로 없나**

- ①에서 **따라 나오기 때문**이다. `x` 와 `x` 를 넣으면 `signum(v) == -signum(v)` 가 되고, 이것을 만족하는 `v` 는 `0` 뿐이다.
- `equals` 계약은 반사성을 **따로 적는다**(다섯 조항). 두 계약의 구성이 다르다는 것이 이 차이로 드러난다.\
  `equals` 쪽 정본은 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/).

> **`signum`** — 값의 부호만 남긴 것(`-1`/`0`/`1`). `compareTo` 의 반환값은 **크기가 아니라 부호만** 의미가 있다.\
> 예: `-5` 를 돌려주든 `-1` 을 돌려주든 계약상 같은 뜻이다.

### 2. 이 비교자는 계약의 어느 조항을 어기는가

**출력** (`Ex.java (28-a)`, JDK 21.0.5 — 17·25 동일)

```text
--- FUZZY 가 추이성을 어기는 구체적 세 값 ---
FUZZY(0, 10)  = 0   (같다고 한다)
FUZZY(10, 20) = 0   (같다고 한다)
FUZZY(0, 20)  = -1  (그런데 다르다고 한다)
```

**세 호출의 결과**

- `compare(0, 10)` -> **`0`**
- `compare(10, 20)` -> **`0`**
- `compare(0, 20)` -> **`-1`**

**어느 조항을 어기나**

- ★ **③ 동치의 일관성**을 정면으로 어긴다.\
  `c(0,10)==0` 이므로 모든 `z` 에 대해 `signum(c(0,z)) == signum(c(10,z))` 여야 하는데,
  `z=20` 에서 `signum(c(0,20)) = -1`, `signum(c(10,20)) = 0` 이라 다르다.
- ② 추이성도 같이 깨진다 — "같다"가 동치 관계가 아니기 때문이다.

```text
  0 ─(같다)─ 10 ─(같다)─ 20
  │                      │
  └────── 다르다 ─────────┘     "같다"가 묶음을 만들지 못한다
```

**원했던 것과 계약을 지키며 하는 법**

- 원한 것은 **"비슷한 것끼리 묶고 싶다"** 이지 "순서를 정하고 싶다"가 아니었다.
- 묶는 것은 **비교자가 아니라 그룹핑**이 한다. 값을 구간으로 정규화한 뒤 그 키로 묶는다.

```java
// 비교자로 하지 않는다
map = list.stream().collect(Collectors.groupingBy(v -> v / 10));   // 10 단위 구간이 키
```

- 정규화된 키는 동치 관계를 만든다(같은 구간이면 같고, 다르면 다르다). 그래서 계약이 깨지지 않는다.
- 그룹핑의 정본은 [`../48-collectors-grouping/`](../48-collectors-grouping/).

### 3. ★ 이 비교자로 정렬하면 무슨 일이 일어나는가 — 원소 수별로

**출력** (`Ex.java (28-a2)`, 값 0\~999, 씨앗 42, JDK 21.0.5 — 17·25 동일)

```text
--- A. 비추이 비교자 FUZZY (값 0~999, seed 42) ---
  n=4      통과 — 결과도 오름차순
  n=8      통과 — 결과도 오름차순
  n=16     통과 — 그러나 결과가 오름차순이 아니다  ★조용한 오답
  n=32     통과 — 그러나 결과가 오름차순이 아니다  ★조용한 오답
  n=64     통과 — 그러나 결과가 오름차순이 아니다  ★조용한 오답
  n=1000   통과 — 그러나 결과가 오름차순이 아니다  ★조용한 오답
  n=2000   IllegalArgumentException: Comparison method violates its general contract!
  n=4000   IllegalArgumentException: Comparison method violates its general contract!
  n=8000   IllegalArgumentException: Comparison method violates its general contract!
  n=10000  IllegalArgumentException: Comparison method violates its general contract!
```

**네 경우의 답**

| `n` | 결과 | 오름차순인가 |
|---|---|---|
| 4 | 정상 종료 | **그렇다** (운이 좋았다) |
| 16 | 정상 종료 | **아니다** ★ |
| 1000 | 정상 종료 | **아니다** ★ |
| 2000 | **`IllegalArgumentException`** | — |

**예외 타입과 메시지**

```text
java.lang.IllegalArgumentException: Comparison method violates its general contract!
```

`TimSort` 소스의 문자열 리터럴 그대로다.

```java
// JDK 21.0.5  java.base/java/util/TimSort.java  780~782행 — 실제 소스 그대로
} else if (len1 == 0) {
    throw new IllegalArgumentException(
        "Comparison method violates its general contract!");
}
```

구체적으로 8원소 하나를 눈으로 보면 이렇다(같은 프로그램 C절, 값 0\~99, 씨앗 7).

```text
  n=8 정렬 전 : [36, 64, 85, 44, 80, 54, 68, 49]
  n=8 정렬 후 : [36, 44, 64, 54, 49, 68, 85, 80]
                              ^^^^^^^^        ^^
                      64 다음에 54 가 온다   85 다음에 80
```

**가장 위험한 것**

```text
  정상 + 정답                정상 + 오답 ★              예외
  +-----------------+       +-----------------------+   +--------------------+
  | 문제가 없어 보임 |       | 문제가 없어 보임        |   | 즉시 눈에 띈다     |
  | 실제로도 맞았다  |       | 결과가 조용히 틀렸다    |   | 스택 트레이스가     |
  |                 |       | 이진 탐색·상위 N개가    |   | 원인을 가리킨다     |
  |                 |       | 전부 따라 틀린다        |   |                    |
  +-----------------+       +-----------------------+   +--------------------+
      운이 좋았을 뿐            ★ 가장 위험하다              가장 덜 위험하다
```

- ★ **"정상 + 오답"이 가장 위험하다.** 예외도 경고도 로그도 없다.
- 그 결과를 이진 탐색(`Collections.binarySearch`)·페이지네이션·상위 N개 추출이 이어받으면 **전부 조용히 틀린다.**
- 예외는 오히려 **다행**이다 — 그 자리에서 멈추고 원인을 알려 준다.

### 4. ★ 왜 원소가 적으면 안 터지는가

**소스의 상수**

```java
// JDK 21.0.5  java.base/java/util/TimSort.java  80행 — 실제 소스 그대로
private static final int MIN_MERGE = 32;

// 219행
if (nRemaining < MIN_MERGE) {
```

- **`MIN_MERGE`, 값은 `32`** 다.
- 그 아래에서는 **이진 삽입 정렬(`binarySort`) 한 번**으로 끝난다. 병합 단계에 들어가지 않는다.
- `throw` 가 있는 곳은 `TimSort.java` 의 `mergeLo`(782행)·`mergeHi`(904행), `ComparableTimSort.java` 의 749·871행 — **전부 병합 안**이다.\
  즉 **31개 이하에는 던질 코드 자체가 실행 경로에 없다.**

```text
  sort(a, lo, hi, c) 에 들어온 원소 수 nRemaining
                  |
        +---------+---------+
        |                   |
   nRemaining < 32     nRemaining >= 32
        |                   |
        v                   v
  이진 삽입 정렬 한 번    run 을 만들고 스택에 쌓는다
        |                    |
        v                    v
   그냥 끝난다           merge — 여기에만 throw 가 있다
   ★ 던질 코드가 없다
```

**6만 번 실측** (`Ex.java (28-a4)`, 값 0\~99, 씨앗 0\~1999, JDK 21.0.5 — 17·25 동일)

```text
n = 2~31, seed 0~1999 -> 시도 60000회
  IllegalArgumentException 이 난 횟수 : 0
  예외 없이 오름차순이 아닌 결과가 난 횟수 : 54097
n = 32~61, seed 0~1999 -> 시도 60000회
  IllegalArgumentException 이 난 횟수 : 3012
  예외 없이 오름차순이 아닌 결과가 난 횟수 : 56988
```

| 구간 | 예외 | 조용한 오답 |
|---|---|---|
| 2\~31 | **0회** | 54,097회 |
| 32\~61 | 3,012회 (5.0%) | 56,988회 |

**"예외가 안 났으니 계약을 지켰다"가 틀린 이유**

- 31개 이하에서는 **위반이 있어도 절대 안 던진다.** 6만 번 중 0회다.
- 32개 이상에서도 던지는 비율은 **5%** 다. 95%는 여전히 조용히 틀린다.
- ★ **javadoc 자신이 그렇게 적었다.** `Arrays.sort(T[], Comparator)` 의 `@throws` 절이다.

> `@throws IllegalArgumentException` **(optional)** `if the comparator is found to violate the {@link Comparator} contract`

- `List.sort` 의 javadoc 에도 같은 자리에 `(optional)` 이 붙어 있다.
- 결론: **`IllegalArgumentException` 은 안전망이지 검사기가 아니다.** 계약은 사람이 보증해야 한다.

> **조용한 실패(silent failure)** — 에러 없이 정상처럼 끝나는데 결과만 틀린 것.\
> 예: 계약을 깬 비교자로 정렬한 8원소 리스트. 예외도 경고도 없고 오름차순만 아니다.

### 5. ★ `compareTo` 와 `equals` 가 어긋나면 무엇이 달라지는가

**출력** (`Ex.java (28-b)`, JDK 21.0.5 — 17·25 동일)

```text
--- 1. compareTo 와 equals 가 어긋날 때 ---
a.equals(b)    : false
a.compareTo(b) : 0
HashSet  size  : 2  [Emp[name=김, dept=영업], Emp[name=김, dept=개발]]
TreeSet  size  : 1  [Emp[name=김, dept=영업]]
TreeSet.contains(b) : true   (b 는 없는데 true)
TreeSet 에 남은 것이 a 인가 : true
```

**세 결과**

| 호출 | 결과 |
|---|---|
| `new HashSet<>(List.of(a, b)).size()` | **2** |
| `new TreeSet<>(List.of(a, b)).size()` | **1** ★ 원소가 사라졌다 |
| `new TreeSet<>(List.of(a, b)).contains(b)` | **`true`** ★ 없는데 있다고 한다 |

**남은 것은 `a` 다**

- 먼저 들어간 쪽이 남는다. `add(b)` 가 "이미 있다"로 판정돼 **아무 일도 안 했기 때문**이다.
- `Comparable` 의 인터페이스 javadoc 원문이 이 동작을 직접 적어 두었다.

> For example, if one adds two keys `a` and `b` such that `(!a.equals(b) && a.compareTo(b) == 0)`
> to a sorted set that does not use an explicit comparator, the second `add`
> operation returns false (and the size of the sorted set does not increase)
> because `a` and `b` are equivalent from the sorted set's perspective.

**`contains(b)` 가 `true` 인 이유**

```text
  HashSet (equals · hashCode 로 판정)       TreeSet (compareTo 로만 판정)
  +---------------------------------+       +---------------------------------+
  | add(a) -> 들어간다               |       | add(a) -> 들어간다               |
  | add(b) -> equals 가 false        |       | add(b) -> compareTo 가 0         |
  |          -> 다른 것으로 본다      |       |          -> 같은 것으로 본다      |
  | size = 2                        |       | size = 1  ★ b 가 사라졌다        |
  | contains(b) -> equals 로 찾는다  |       | contains(b) -> compareTo 로 찾는다|
  |             -> true             |       |             -> true ★ 없는데     |
  +---------------------------------+       +---------------------------------+
```

- ★ **`TreeSet` 은 `equals` 를 부르지 않는다.** 트리를 내려가며 `compareTo` 가 `0` 이 되는 노드를 찾을 뿐이다.
- `a` 에서 `0` 이 나오므로 "찾았다"가 된다. 그 노드가 `b` 인지 `a` 인지는 **묻지 않는다.**
- javadoc 은 이것을 "violates the general contract for set (or map), which is defined in terms of the `equals` method" 라고 부른다.

**`TreeMap` 으로 만들면**

```text
HashMap : {1.0=첫째, 1.00=둘째}
TreeMap : {1.0=둘째}   ★ 키는 1.0 인데 값은 둘째다
```

- `put(y, "둘째")` 가 **새 엔트리를 만들지 않고 기존 키의 값만 덮었다.**
- 그래서 **키는 처음 것, 값은 나중 것**이 남는다. 둘이 어긋난 상태로 살아 있다.
- 로그에 키를 찍으면 `1.0` 이 나오는데 값은 `1.00` 으로 넣은 것이라, 추적이 거의 불가능하다.

### 6. JDK 안에서 이 계약을 깨 놓은 대표 클래스는 무엇인가

**출력** (`Ex.java (28-b)`)

```text
--- 2. BigDecimal — JDK 안의 대표 사례 ---
x.equals(y)    : false
x.compareTo(y) : 0
HashSet  size  : 2
TreeSet  size  : 1  [1.0]
HashMap : {1.0=첫째, 1.00=둘째}
TreeMap : {1.0=둘째}   ★ 키는 1.0 인데 값은 둘째다
```

**`BigDecimal` 이다.**

| 호출 | 결과 | 왜 |
|---|---|---|
| `new BigDecimal("1.0").equals(new BigDecimal("1.00"))` | **`false`** | `equals` 는 **스케일까지** 본다 |
| `new BigDecimal("1.0").compareTo(new BigDecimal("1.00"))` | **`0`** | `compareTo` 는 **값만** 본다 |
| `HashSet` 크기 | **2** | `equals`/`hashCode` 판정 |
| `TreeSet` 크기 | **1** | `compareTo` 판정 |

**문제가 안 되는 이유**

- ★ **javadoc 이 요구한 "clearly indicate this fact" 를 실제로 했기 때문**이다.
- `Comparable` 인터페이스 javadoc 이 `BigDecimal` 을 **유일한 예외로 직접 호명**한다.

> Virtually all Java core classes that implement `Comparable` have natural orderings that are consistent with equals.
> One exception is {@link java.math.BigDecimal}, whose {@linkplain java.math.BigDecimal#compareTo natural ordering}
> equates `BigDecimal` objects with equal numerical values and different representations (such as 4.0 and 4.00).

- 그리고 `BigDecimal.compareTo` 자신의 javadoc 에 권고 문구가 그대로 들어 있다 —
  "Note: this class has a natural ordering that is inconsistent with equals."
- **권고 ④ 를 깨는 것 자체는 허용된다. 다만 밝혀야 한다** — 이것이 계약의 실제 요구다.
- `BigDecimal` 의 스케일·반올림·`equals` 함정 자체는 [`../53-bigdecimal/`](../53-bigdecimal/) 가 정본이다.

### 7. 뺄셈으로 비교하면 무엇이 틀리는가

**출력** (`Ex.java (28-b)`, JDK 21.0.5 — 17·25 동일)

```text
--- 3. 뺄셈 비교자와 오버플로 ---
big - neg              = -2147483639   (음수! 오버플로)
(a, b) -> a - b        : [2147483647, -10, 0]   ★ 틀렸다
Integer::compare       : [-10, 0, 2147483647]
```

**`Integer.MAX_VALUE - (-10)`**

- **`-2147483639`** 다. 참값 `2147483657` 은 `int` 범위를 넘어 음수로 돌았다.

**정렬 결과**

- **`[2147483647, -10, 0]`** — 가장 큰 값이 맨 앞에 왔다.
- 비교자가 "`MAX_VALUE` 가 `-10` 보다 작다"고 말했기 때문이다.

```text
  a - b 의 부호가 곧 답이라고 믿는다
        |
        v
  MAX_VALUE - (-10) = 2147483657  <- int 로 표현 불가
        |
        v
  실제 저장되는 값 = -2147483639  <- 부호가 뒤집혔다
        |
        v
  "MAX_VALUE < -10" 이라고 답한다
```

**오래 살아남는 이유**

- **값이 전부 양수이고 범위가 좁으면 절대 안 터진다.** 나이·개수·길이 같은 필드에서는 평생 문제가 없다.
- 터지는 조건은 **음수가 섞이고 값의 폭이 `int` 범위의 절반을 넘을 때**뿐이다.
- 그래서 ID·타임스탬프·해시값처럼 폭이 큰 값을 다루기 시작하는 날 갑자기 틀린다.
- 게다가 **예외가 아니라 조용한 오답**이다.

**무엇으로 바꾸나**

```java
Comparator<Integer> safe = Integer::compare;        // 또는 Comparator.comparingInt(...)
// long 이면 Long.compare, double 이면 Double.compare
```

- `Integer.compare` 는 내부에서 `x < y ? -1 : (x == y ? 0 : 1)` 를 하므로 뺄셈이 없다.
- 오버플로 자체의 정본은 [`../02-numeric-operations/`](../02-numeric-operations/).

### 8. `compareTo(null)` 은 어떻게 되어야 하는가

**출력** (`Ex.java (28-b)`)

```text
--- 4. compareTo(null) ---
a.compareTo(null) -> java.lang.NullPointerException: Cannot read field "name" because "o" is null
a.equals(null)    -> false
```

**각각 무엇을 해야 하나**

| 호출 | 해야 할 것 | 근거 |
|---|---|---|
| `e.compareTo(null)` | **`NullPointerException` 을 던진다** | `Comparable` 인터페이스 javadoc |
| `e.equals(null)` | **`false` 를 돌려준다** | `Object.equals` javadoc 다섯째 조항 |

`Comparable` javadoc 원문이 둘을 나란히 적어 두었다.

> Note that `null` is not an instance of any class, and `e.compareTo(null)` should
> throw a `NullPointerException` even though `e.equals(null)` returns `false`.

**정반대인 이유**

- `equals` 는 **"같은가?"** 를 묻는다. `null` 과는 같지 않으므로 답은 `false` 다. 답할 수 있는 질문이다.
- `compareTo` 는 **"어느 쪽이 먼저인가?"** 를 묻는다. `null` 은 어떤 클래스의 인스턴스도 아니므로 **순서를 정할 근거가 없다.**\
  "모르겠다"를 돌려줄 값이 없으니 던질 수밖에 없다.
- 위 NPE 는 **일부러 던진 것이 아니라 `o.name` 을 읽다가 난 것**이다. 결과적으로 계약에는 맞는다.\
  의도를 드러내려면 `Objects.requireNonNull(o)` 로 먼저 막는 편이 낫다([**60번 주제**](../60-null-handling/)).

**`Comparator` 는**

- **`null` 을 받아도 된다.** javadoc 이 "may optionally permit comparison of null arguments" 라고 허용했다.
- 그래서 `nullsFirst`/`nullsLast` 가 표준으로 제공된다(10번).

### 9. `reversed()` 를 붙이는 자리가 결과를 바꾸는가

**출력** (`Ex.java (28-c)`, JDK 21.0.5 — 17·25 동일)

```text
--- 2. reversed() 는 앞의 조합 전체를 뒤집는다 ---
(dept then name).reversed() : [영업/이/25, 영업/김/25, 개발/박/30, 개발/김/40]
dept.reversed() then name   : [영업/김/25, 영업/이/25, 개발/김/40, 개발/박/30]
```

**같은가 다른가**

- **다르다.**

| 식 | 뜻 | 결과 |
|---|---|---|
| (A) `comparing(dept).thenComparing(name).reversed()` | dept **내림** + name **내림** | `영업/이 → 영업/김 → 개발/박 → 개발/김` |
| (B) `comparing(dept).reversed().thenComparing(name)` | dept **내림** + name **오름** | `영업/김 → 영업/이 → 개발/김 → 개발/박` |

```text
  (A) .reversed() 가 맨 끝                       (B) .reversed() 가 중간
  +------------------------------------+         +------------------------------------+
  | 1. "dept 오름, 같으면 name 오름"    |         | 1. "dept 오름" 을 만든다            |
  |    이라는 비교자 하나를 조립        |         | 2. 그것을 뒤집어 "dept 내림"        |
  | 2. 그 하나를 통째로 뒤집는다        |         | 3. 거기에 "name 오름" 을 이어 붙인다 |
  | -> 두 키가 모두 내림                |         | -> dept 만 내림                     |
  +------------------------------------+         +------------------------------------+
```

- `reversed()` 는 **그 시점까지 조립된 비교자 하나**에 걸린다. 메서드 체인의 순서가 곧 괄호다.

**한 키만 내림차순으로**

```java
list.sort(comparing(P::dept).thenComparing(P::age, reverseOrder()));
```

- **그 키에 비교자를 직접 준다.** `thenComparing(키추출, 비교자)` 오버로드가 이 자리를 위한 것이다.
- 실행으로 확인했다(`Ex.java (28-c)` 1절) — `개발/김/40` 이 `개발/박/30` 보다 앞에 온다.

```text
dept, age 내림차순 : [개발/김/40, 개발/박/30, 영업/김/25, 영업/이/25]
```

- 읽기 헷갈리면 중간 변수로 끊는다 — `var byDeptDesc = comparing(P::dept).reversed();`

### 10. `null` 이 섞인 정렬은 어떻게 다루는가

**출력** (`Ex.java (28-c)`, JDK 21.0.5 — 17·25 동일)

```text
--- 4. null 이 섞이면 ---
comparing(P::age)            -> java.lang.NullPointerException: Cannot invoke "java.lang.Comparable.compareTo(Object)" because the return value of "java.util.function.Function.apply(Object)" is null
nullsFirst(naturalOrder())   : [개발/최/null, 영업/김/25, 영업/이/25, 개발/박/30, 개발/김/40]
nullsLast(naturalOrder())    : [영업/김/25, 영업/이/25, 개발/박/30, 개발/김/40, 개발/최/null]

--- 5. 리스트 자체에 null 원소가 섞이면 ---
naturalOrder -> java.lang.NullPointerException: Cannot invoke "java.lang.Comparable.compareTo(Object)" because "c1" is null
nullsFirst(naturalOrder()) : [null, a, b]
```

**두 NPE 메시지가 다르다**

| 상황 | 메시지 | 읽는 법 |
|---|---|---|
| 키 추출 함수가 `null` 을 돌려줌 | `... because the return value of "java.util.function.Function.apply(Object)" is null` | **원소는 멀쩡하고 키가 `null`** 이다 |
| 원소 자체가 `null` | `... because "c1" is null` | **리스트 안에 `null` 원소**가 있다 |

- ★ **메시지 한 줄로 어느 층이 문제인지 갈린다.** 이것이 helpful NPE 의 값어치다([`../05-arrays/`](../05-arrays/)).

**`nullsFirst`/`nullsLast` 를 감싸는 층**

```text
  원소가 null 일 수 있다                     추출한 키가 null 일 수 있다
  +--------------------------------+        +----------------------------------------+
  | nullsFirst(naturalOrder())     |        | comparing(P::age, nullsFirst(          |
  |   <- 바깥에 감싼다              |        |            naturalOrder()))            |
  |                                |        |   <- 키 비교자 자리에 감싼다            |
  | list.sort(그것)                 |        |                                        |
  +--------------------------------+        +----------------------------------------+
```

- `nullsFirst(cmp)` 는 **`null` 을 먼저 처리하고, 둘 다 `null` 이 아닐 때만 `cmp` 에 넘긴다.**\
  그래서 안쪽 비교자는 `null` 을 절대 못 본다.
- 잘못 감싸면(바깥에 감싸야 할 것을 키 자리에 감싸면) 여전히 NPE 가 난다. **어느 층의 `null` 인지 먼저 정한다.**

**`list.sort(null)`**

```text
--- 6. Collections.sort 와 List.sort(null) ---
list.sort(null) -> 자연 순서 : [a, b, c]
```

- **"자연 순서를 쓰라"** 는 뜻이다. `List.sort` javadoc: "A `null` value indicates that the elements' natural ordering should be used."
- `NullPointerException` 이 아니다. 소스에서도 `Arrays.sort(a, (Comparator) c)` 로 넘기고, 거기서 `c == null` 이면 `sort(a)` 를 부른다.

### 11. 이 체인은 왜 컴파일되지 않는가

**출력** (`Ex.java (28-d)`, JDK 21.0.5 — 17·25 문구 동일)

```text
Ex.java:7: error: cannot find symbol
        l.sort(comparing(p -> p.dept()).thenComparing(p -> p.name()));
                               ^
  symbol:   method dept()
  location: variable p of type Object
Ex.java:7: error: cannot find symbol
        l.sort(comparing(p -> p.dept()).thenComparing(p -> p.name()));
                                                            ^
  symbol:   method name()
  location: variable p of type Object
2 errors
```

**어디를 가리키나**

- **두 람다의 `p.dept()`·`p.name()` 호출 자리**다. `location: variable p of type Object` 가 핵심이다.

**원인**

```text
  l.sort( comparing(p -> p.dept()) .thenComparing(p -> p.name()) )
          \_____________________/
           이 부분의 타입이 먼저 정해져야
           .thenComparing 을 찾을 수 있다
                    |
                    v
          그런데 comparing 의 T 는
          l.sort(...) 의 대상 타입에서 와야 한다
                    |
                    v
          메서드 체인 중간이라 그 정보가 안 흐른다
                    |
                    v
          T 가 Object 로 떨어진다 -> p.dept() 를 못 찾는다
```

- 제네릭 메서드의 타입 인자는 **대상 타입**에서 온다. 그런데 `.thenComparing` 을 이어 붙이면
  `comparing(...)` 의 결과가 **수신자(receiver)** 가 되어 버려, 대상 타입 정보가 거기까지 흐르지 않는다.
- 04번의 `var list = new ArrayList<>()` 가 `ArrayList<Object>` 가 되는 것과 **같은 원리**다 —
  대상 타입이 끊기면 경계인 `Object` 로 떨어진다([`../04-var-type-inference/`](../04-var-type-inference/)).

**고치는 방법 둘**

```java
// 1. 메서드 참조로 바꾼다 — 참조가 자기 타입을 알려 준다
l.sort(comparing(P::dept).thenComparing(P::name));

// 2. 타입 인자를 명시한다
l.sort(Comparator.<P, String>comparing(p -> p.dept()).thenComparing(p -> p.name()));
```

둘 다 컴파일됨을 확인했다(`Ex.java (28-d2)`).

```text
둘 다 컴파일된다
```

- 실무에서는 **1번**을 쓴다. 짧고 이 함정을 원천적으로 피한다.

### 12. `Comparable` 과 `Comparator` 중 무엇을 고르나

**둘을 가르는 실제 기준**

> **그 타입에 "당연한 하나"의 순서가 있으면 `Comparable`, 관점이 여럿이면 `Comparator`.**

| | `Comparable` | `Comparator` |
|---|---|---|
| 어디에 있나 | 타입 자신이 구현 | 밖에서 넘긴다 |
| 몇 개 | **하나**(자연 순서) | **필요한 만큼** |
| 남의 타입에 | 못 붙인다 | **붙일 수 있다** |
| `null` | NPE 를 던져야 한다 | 허용해도 된다 |
| 패키지 | `java.lang` | `java.util` |

- 숫자·날짜·ID 는 `Comparable`. "가격순"·"인기순"·"거리순"은 `Comparator`.
- **남의 라이브러리 타입**을 정렬해야 하면 선택지가 `Comparator` 뿐이다.

**여러 키로 정렬할 때**

```java
// if 를 쌓지 않는다
Comparator<P> ORDER = comparing(P::dept).thenComparing(P::name).thenComparingInt(P::age);
```

- `if (c != 0) return c;` 를 손으로 쌓으면 **한 줄만 빠뜨려도 조용히 틀린다.**
- 조합으로 쓰면 각 키가 한 줄이고, 순서가 눈에 보인다.

**`comparingInt` 를 쓰는 이유**

- `comparing(P::age)` 는 `Function<P, Integer>` 를 받는다 — **비교할 때마다 박싱**이 생긴다.
- `comparingInt(P::age)` 는 `ToIntFunction<P>` 를 받아 **`int` 그대로** 비교한다.
- 정렬은 원소당 `O(log n)` 번 비교하므로, 큰 리스트에서는 박싱 객체가 그만큼 쌓인다.
- 박싱 자체의 정본은 [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/).

### 13. 다른 주제와 잇기

**27번의 `equals` 계약과 만나는 자리·갈라지는 자리**

```text
  27번 — 동치 계약                     28번 — 순서 계약
  +--------------------------------+   +--------------------------------+
  | equals 다섯 조항                |   | compareTo 세 조항               |
  |   반사·대칭·추이·일관·null      |   |   대칭·추이·동치 일관성         |
  | hashCode 세 조항                |   | + 권고 ④ (equals 와의 일관성)   |
  | 영향 받는 것: HashMap/HashSet   |   | 영향 받는 것: sort/TreeSet/TreeMap|
  +--------------------------------+   +--------------------------------+
              |                                     |
              +------------- 만나는 자리 ------------+
                       권고 ④ 하나뿐이다
              (c(x,y)==0) == x.equals(y) 가 성립하는가
```

- **만나는 곳은 ④ 하나**다. 나머지는 서로 독립이다.
- ④ 를 깨면 **`HashSet` 과 `TreeSet` 의 `size()` 가 갈린다**(5번). 이것이 두 주제가 이어지는 유일한 실무 증상이다.
- ④ 는 27번에서는 조항이 아니고, 28번에서만 **권고**로 등장한다.

**원소가 사라지는 두 경우의 원인 차이**

| | `HashSet` 에서 사라짐 | `TreeSet` 에서 사라짐 |
|---|---|---|
| 언제 | `equals` 는 같다는데 `hashCode` 가 다를 때 | `equals` 는 다르다는데 `compareTo` 가 `0` 일 때 |
| 증상 | **넣은 것을 못 찾는다**(`get` 이 `null`) | **넣은 것이 안 들어간다**(`size` 가 안 는다) |
| `size()` | 오히려 **늘어난다**(중복이 안 걸러짐) | **안 는다** |
| `contains` | `false` (있는데 못 찾음) | `true` (없는데 찾음) |
| 정본 | [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) | 이 문서 (5) |

- ★ **증상이 정반대다.** 해시 쪽은 "있는데 못 찾는다", 트리 쪽은 "없는데 있다고 한다".

**`Arrays.sort(int[])` 에서도 나는가**

- **안 난다.** 기본형 배열에는 비교자가 없어 `DualPivotQuicksort.sort` 로 간다(`Arrays.java` 100·176행 등).
- 계약 위반이라는 개념 자체가 성립하지 않는다.
- 이 주제의 함정은 **객체 배열·컬렉션에서만** 나온다 — `Arrays.sort(T[], Comparator)`·`List.sort`·`Collections.sort`·`TreeSet`·`TreeMap`·`Stream.sorted`.

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java (28-a)` | `FUZZY` 의 추이성 위반 세 값, 원소 수 10구간별 정렬 결과 | 21 |
| `Ex.java (28-a2)` | `FUZZY`·`NEVER_ZERO` 를 n=4\~10000 에서 — 통과/조용한 오답/예외 세 구간, 8·31·32 원소의 실제 정렬 결과 | 17 · 21 · 25 (출력 동일) |
| `Ex.java (28-a3)` | 처음 던지는 n(731 · 89), `Arrays.sort`·`Arrays.parallelSort` 도 같은 경계 | 17 · 21 · 25 (출력 동일) |
| `Ex.java (28-a3)` `-Djava.util.Arrays.useLegacyMergeSort=true` | 옛 병합 정렬에서는 n=3000까지 한 번도 안 던짐(`-1`) | 21 |
| `Ex.java (28-a4)` | n=2\~31 씨앗 0\~1999 (6만 회) -> 예외 0회·오답 54,097회 / n=32\~61 -> 예외 3,012회·오답 56,988회 | 17 · 21 · 25 (출력 동일) |
| `Ex.java (28-b)` | `compareTo`/`equals` 불일치의 `HashSet`·`TreeSet`·`TreeMap` 차이, `BigDecimal`, 뺄셈 오버플로, `compareTo(null)` | 17 · 21 · 25 (출력 동일) |
| `Ex.java (28-c)` | `comparing`·`thenComparing`·`reversed` 위치, `comparingInt`, `nullsFirst`/`nullsLast`, `sort(null)` | 17 · 21 · 25 (출력 동일) |
| `Ex.java (28-d)` `javac` | `comparing(람다).thenComparing(람다)` -> `cannot find symbol ... variable p of type Object` | 17 · 21 · 25 (문구 동일) |
| `Ex.java (28-d2)` | 메서드 참조 / 타입 인자 명시 두 형태가 모두 컴파일됨 | 21 |

**구현 의존 항목** — `MIN_MERGE == 32`, 처음 던지는 원소 수(731·89), 예외 메시지 문구,
6만 회 실측의 정확한 횟수(54,097·3,012·56,988), `ComparableTimSort`/`TimSort` 의 행 번호 —
전부 **JDK 구현 세부이고 데이터·씨앗에 의존**한다. 버전이 올라 달라질 수 있으므로 그때 다시 돌린다.\
반면 계약 세 조항·권고 ④·`compareTo(null)` 이 NPE 여야 한다는 것·`IllegalArgumentException` 이 **optional** 이라는 것은
**javadoc 이 보장**한다.

★ **세 JDK 에서 같았다는 것은 관찰이지 보장이 아니다.** 임계값에 의존하는 코드·테스트를 쓰면 안 된다.
