# java/syntax/28 — `Comparable`/`Comparator`: 전순서 계약과 조합 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — JDK 21.0.5 표준 라이브러리 소스 `java.base/java/lang/Comparable.java` · `java.base/java/util/Comparator.java` 의 **javadoc 원문**(`lib/src.zip` 에서 직접 인용) · `java.base/java/util/TimSort.java` · `java.base/java/util/ComparableTimSort.java`
> **실행 검증** — 이 문서의 모든 출력·예외는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 실행 프로그램 다섯(`Ex.java (28-a2)`·`(28-a3)`·`(28-a4)`·`(28-b)`·`(28-c)`)을 **17.0.13 · 21.0.5 · 25.0.1** 세 곳에서 돌려 **출력이 한 글자도 다르지 않았다**.\
> 계약 위반의 임계 원소 수(731·89)까지 세 JDK 에서 같았다. 다만 **"세 곳에서 같았다"는 관찰이지 보장이 아니다** —
> 보장은 javadoc 인용으로만 적었고, **임계값은 데이터·씨앗에 따라 달라진다**(아래 실측 조건 명시).
> **버전** — `Comparable` 은 **Java 1.2**, `Comparator` 도 **1.2**.\
> `comparing`·`thenComparing`·`reversed`·`nullsFirst`·`naturalOrder` 등 조합 메서드는 전부 **Java 8**(`@since 1.8`, src.zip 확인).
> **범위** — 정렬 **알고리즘**(병합·삽입·TimSort 의 run·gallop)은 이 문서가 다루지 않는다.\
> 그쪽은 [`../../../../../algorithm/01-elementary-sort/`](../../../../../algorithm/01-elementary-sort/) 와 `cs/algorithm/` 이 정본이다.\
> 여기는 **「비교자의 계약과 그것을 어겼을 때 관측되는 증상」**만 다룬다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**비교자는 "키 재는 자"다. 자가 흔들리면 줄 세우기가 조용히 망가진다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 키 재는 자 | `compareTo` 또는 `Comparator.compare` |
| 재서 나오는 값 | 음수 / `0` / 양수 |
| "둘을 재면 어느 쪽이든 결과가 뒤집힌다" | **대칭성** — `signum(c(x,y)) == -signum(c(y,x))` |
| "A가 B보다 크고 B가 C보다 크면 A가 C보다 크다" | **추이성** |
| "키가 같다고 잰 둘은 제3자와도 똑같이 재진다" | **동치의 일관성** |
| 키가 같으면 **같은 사람으로 친다** | **`equals` 와의 일관성**(권고) |
| 줄 세우는 사람 | `List.sort` / `Arrays.sort` / `TreeSet` / `TreeMap` |
| 자가 흔들리는 것을 줄 세우다 들킨 순간 | `IllegalArgumentException: Comparison method violates its general contract!` |

- 줄 세우기는 **자를 믿고** 한다. 자를 매번 다시 검사하지 않는다 — 그러면 정렬이 느려진다.
- 그래서 **자가 흔들려도 대개는 아무 말 없이 끝난다.** 줄이 엉켜 있을 뿐이다.
- 사람이 많아지면(원소가 많아지면) **부분 줄을 합치다가 아귀가 안 맞는 순간**이 오고, 그때 비로소 예외가 난다.
- ★ 끔찍한 점: **적은 인원에서는 절대 안 터진다.** 테스트는 통과하고 운영에서 터진다.

```text
  원소가 적을 때 (n < 32)                    원소가 많을 때
  +-------------------------------+          +-------------------------------+
  | 이진 삽입 정렬 하나로 끝난다   |          | 부분 줄(run)을 만들어 합친다   |
  | 합치는 단계가 없다             |          | 합치다 아귀가 안 맞으면 감지   |
  | -> 예외가 날 자리가 없다       |          | -> IllegalArgumentException    |
  | -> 조용히 틀린 줄이 남는다 ★   |          |    (다만 항상은 아니다)        |
  +-------------------------------+          +-------------------------------+
```

**똑같은 구조로** Java 가 동작한다: 자 = 비교자, 줄 세우기 = `sort`, 아귀가 안 맞는 순간 = `TimSort` 의 병합 단계.

실무에서 이게 터지는 자리는 **"대략 같으면 같다고 치자"는 비교자**다.\
`Math.abs(a - b) <= 임계값 ? 0 : ...`, 점수를 반올림해서 비교, 우선순위를 뺄셈으로 계산 —
셋 다 계약을 깨고, 셋 다 **작은 테스트 데이터로는 통과한다.**

> **전순서(total order)** — 어떤 두 원소를 집어도 대소가 정해지고, 그 관계가 대칭·추이를 만족하는 순서.\
> 예: 정수의 `<=` 는 전순서다. "키가 5cm 이내면 같다"는 추이성이 깨져 전순서가 아니다.

> **계약(contract)** — 컴파일러가 강제하지 못하지만 **어기면 표준 라이브러리가 오동작하는 약속**.\
> 예: 추이성을 깬 비교자는 컴파일이 되고, 작은 리스트에서는 정렬도 되지만, 결과가 오름차순이 아니다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. javadoc 이 요구하는 **조항이 정확히 몇 개**이고 각각 무엇인가.
2. 조항을 어기면 **언제 예외가 나고 언제 조용히 틀리는가** — 그 경계는 무엇이 정하는가.
3. `compareTo` 와 `equals` 가 어긋나면 **어느 컬렉션이 어떻게 달라지는가.**

## 동작 방식

### (1) `compareTo` 계약 — javadoc 이 요구하는 세 조항 + 권고 하나

**언제 쓰나** — `Comparable` 을 구현하거나 리뷰할 때.

JDK 21.0.5 `java.base/java/lang/Comparable.java` 의 `compareTo` javadoc 원문이다.

> The implementor must ensure {@link Integer#signum signum}`(x.compareTo(y)) == -signum(y.compareTo(x))` for
> all `x` and `y`.  (This implies that `x.compareTo(y)` must throw an exception if and only if
> `y.compareTo(x)` throws an exception.)
>
> The implementor must also ensure that the relation is transitive:
> `(x.compareTo(y) > 0 && y.compareTo(z) > 0)` implies `x.compareTo(z) > 0`.
>
> Finally, the implementor must ensure that `x.compareTo(y)==0` implies that `signum(x.compareTo(z))
> == signum(y.compareTo(z))`, for all `z`.

그리고 `@apiNote` 에 권고가 하나 더 있다.

> It is strongly recommended, but *not* strictly required that `(x.compareTo(y)==0) == (x.equals(y))`.
> Generally speaking, any class that implements the `Comparable` interface and violates this condition
> should clearly indicate this fact.

```text
  ① 대칭성   signum(c(x,y)) == -signum(c(y,x))     -> 한쪽만 0 이거나 부호가 같으면 위반
  ② 추이성   c(x,y)>0 이고 c(y,z)>0 이면            -> c(x,z)>0 이어야 한다
  ③ 동치의 일관성  c(x,y)==0 이면                   -> 모든 z 에 대해 signum(c(x,z))==signum(c(y,z))
  --------------------------------------------------------------------------
  ④ equals 와의 일관성  (c(x,y)==0) == x.equals(y)  -> ★ 권고(strongly recommended)이지 강제가 아니다
```

그림 해설 (한 단계씩):

- ★ **①~③ 은 "must ensure"(강제), ④ 는 "strongly recommended … not strictly required"(권고)** 다.\
  이 구분이 이 주제의 절반이다 — ④ 를 어겨도 정렬은 안 터지지만 **`TreeSet`/`TreeMap` 이 달라진다**((5)).
- 앞의 셋을 만족하면 **전순서**가 된다. javadoc 의 표현으로는 "the natural ordering is a *total order* on C".
- ①의 괄호가 중요하다 — **예외도 대칭이어야 한다.** `x.compareTo(y)` 가 던지면 `y.compareTo(x)` 도 던져야 한다.
- 반사성은 ①에서 따라 나온다(`x` 와 `x` 를 넣으면 `signum(v) == -signum(v)` 이므로 `v == 0`).\
  그래서 javadoc 은 반사성을 따로 적지 않는다 — **`equals` 의 다섯 조항과 구성이 다르다**([`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/)).

비용 — 없다. 판단 규칙이다.

> **`signum`** — 값의 부호만 남긴 것. 음수면 `-1`, `0` 이면 `0`, 양수면 `1`.\
> 예: `compareTo` 가 `-5` 를 돌려주든 `-1` 을 돌려주든 계약상 같은 뜻이다. **크기는 의미가 없다.**

### (2) `Comparator.compare` 계약 — 문장이 거의 같다

**언제 쓰나** — 람다로 비교자를 쓸 때. **람다라고 계약이 느슨해지지 않는다.**

`java.base/java/util/Comparator.java` 의 `compare` javadoc 원문이다.

> The implementor must ensure that {@link Integer#signum signum}`(compare(x, y)) == -signum(compare(y, x))` for
> all `x` and `y`.  (This implies that `compare(x, y)` must throw an exception if and only if
> `compare(y, x)` throws an exception.)
>
> The implementor must also ensure that the relation is transitive:
> `((compare(x, y)>0) && (compare(y, z)>0))` implies `compare(x, z)>0`.
>
> Finally, the implementor must ensure that `compare(x, y)==0` implies that `signum(compare(x,
> z))==signum(compare(y, z))` for all `z`.

차이는 딱 하나, 인터페이스 javadoc 에 이렇게 적혀 있다.

> Unlike `Comparable`, a comparator may optionally permit comparison of null arguments, while maintaining
> the requirements for an equivalence relation.

```text
  Comparable.compareTo                     Comparator.compare
  +--------------------------------+       +--------------------------------+
  | 타입 자신이 가진 "자연 순서"    |       | 밖에서 주는 자. 여러 개 가능    |
  | e.compareTo(null) 은 NPE 여야   |       | null 을 받아도 된다(선택)       |
  | 조항 ①②③ + 권고 ④              |       | 조항 ①②③ + 권고 ④ (문장 동일)  |
  +--------------------------------+       +--------------------------------+
```

그림 해설 (한 단계씩):

- **강제 조항 세 개는 문장까지 같다.** 외울 것은 하나다.
- 다른 것은 **`null` 취급**뿐이다 — `Comparable` 은 NPE 를 요구하고, `Comparator` 는 허용할 수 있다.\
  그래서 `Comparator.nullsFirst`/`nullsLast` 가 존재한다((6)).
- `Comparable` 은 **타입에 하나**, `Comparator` 는 **필요한 만큼** 만들 수 있다. 이것이 둘을 가르는 실제 기준이다.

비용 — 없다.

### (3) ★ 계약을 어기면 무엇이 터지나 — 원소 수가 답을 바꾼다

**언제 쓰나** — "이 비교자 괜찮나?"를 판정할 때. **이 절이 이 주제의 값어치 전부다.**

계약을 어기는 비교자 둘을 만들었다.

```java
// A. 추이성 위반 — "값 차이가 10 이하면 같다"
Comparator<Integer> FUZZY = (x, y) -> Math.abs(x - y) <= 10 ? 0 : Integer.compare(x, y);

// B. 대칭성 위반 — 같은 값에 대해 양쪽 다 1 을 돌려준다
Comparator<Integer> NEVER_ZERO = (x, y) -> x < y ? -1 : 1;
```

`FUZZY` 가 추이성을 어긴다는 것부터 실행으로 못 박는다(`Ex.java (28-a)`).

**출력** (JDK 21.0.5 — 17·25 동일)

```text
--- FUZZY 가 추이성을 어기는 구체적 세 값 ---
FUZZY(0, 10)  = 0   (같다고 한다)
FUZZY(10, 20) = 0   (같다고 한다)
FUZZY(0, 20)  = -1  (그런데 다르다고 한다)
```

이 자를 들고 원소 수만 바꿔 가며 `List.sort` 를 돌렸다(`Ex.java (28-a2)`, 씨앗 42 고정).

**출력**

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

--- B. 대칭성 위반 비교자 NEVER_ZERO (값 0~9 라 중복이 많다, seed 42) ---
  n=4      통과 — 결과도 오름차순
  n=8      통과 — 결과도 오름차순
  n=16     통과 — 결과도 오름차순
  n=32     통과 — 결과도 오름차순
  n=64     통과 — 결과도 오름차순
  n=1000   IllegalArgumentException: Comparison method violates its general contract!
  n=10000  IllegalArgumentException: Comparison method violates its general contract!
```

★ **세 구간으로 갈린다.**

```text
  n 작다            n 중간                        n 크다
  +-------------+   +-------------------------+   +---------------------------+
  | 예외 없음    |   | 예외 없음                |   | IllegalArgumentException  |
  | 결과도 맞다  |   | ★ 결과가 조용히 틀렸다    |   | 여기서만 시끄럽다          |
  | (운이 좋았다)|   | 아무도 모른다            |   |                           |
  +-------------+   +-------------------------+   +---------------------------+
      테스트 통과        테스트 통과(assert 없으면)      운영에서 터진다
```

**임계 원소 수**를 처음 던지는 지점까지 훑어 보았다(`Ex.java (28-a3)`).

```text
FUZZY (0~999, seed 42) 가 처음 던진 n = 731
NEVER_ZERO (0~9, seed 42) 가 처음 던진 n = 89
```

- ★ **이 숫자는 자·데이터·씨앗에 달렸다.** "731개부터 터진다"가 아니라 **"같은 자여도 데이터에 따라 언제 터질지 모른다"** 가 결론이다.
- 세 JDK(17·21·25)에서 이 두 숫자까지 같았다 — **관찰이다.** javadoc 은 임계값을 아무것도 보장하지 않는다.

`Arrays.sort`·`Arrays.parallelSort` 도 같은 계열이다(같은 프로그램).

```text
Arrays.sort n=8 : 통과
Arrays.sort n=32 : 통과
Arrays.sort n=1000 : 통과
Arrays.sort n=2000 : Comparison method violates its general contract!

Arrays.parallelSort n=1000 : 통과
Arrays.parallelSort n=2000 : Comparison method violates its general contract!
Arrays.parallelSort n=10000 : Comparison method violates its general contract!
```

그림 해설 (한 단계씩):

- **예외는 "감지했을 때만" 난다.** 정렬은 자를 검증하지 않는다 — 검증하면 O(n²) 이 든다.
- ★ **javadoc 자신이 그렇게 적어 두었다.** `Arrays.sort(T[], Comparator)` 의 `@throws` 절이다.

> `@throws IllegalArgumentException` **(optional)** `if the comparator is found to violate the {@link Comparator} contract`

  `List.sort` 도 같은 자리에 `(optional)` 이 붙어 있다.\
  **"던질 수도 있다"이지 "던진다"가 아니다** — 이 한 단어가 이 절의 모든 실측을 예고한다.
- 감지되는 자리는 **병합 단계**다. `TimSort` 소스에 그대로 있다.

```java
// JDK 21.0.5  java.base/java/util/TimSort.java  780~782행 — 실제 소스 그대로
} else if (len1 == 0) {
    throw new IllegalArgumentException(
        "Comparison method violates its general contract!");
}
```

- `TimSort.java` 에 이 `throw` 가 **두 곳**(`mergeLo` 782행 · `mergeHi` 904행), `ComparableTimSort.java` 에도 **두 곳**(749·871행) 있다.\
  전부 **병합 안**이다. 병합을 안 하면 던질 길이 없다.

비용 — 계약을 지키면 정렬은 평균 O(n log n).\
어기면 비용이 아니라 **답이 틀리거나 예외가 난다** — 그리고 **어느 쪽일지 예측할 수 없다.**

### (4) ★ 왜 원소가 적으면 안 터지나 — `MIN_MERGE` 가 답이다

**언제 쓰나** — "작은 데이터로 테스트했는데 왜 운영에서 터지나"를 설명할 때.

```java
// JDK 21.0.5  java.base/java/util/TimSort.java  80행 — 실제 소스 그대로
private static final int MIN_MERGE = 32;

// 219행
if (nRemaining < MIN_MERGE) {
```

```text
  sort(a, lo, hi, c) 에 들어온 원소 수 nRemaining
                  |
        +---------+---------+
        |                   |
   nRemaining < 32     nRemaining >= 32
        |                   |
        v                   v
  이진 삽입 정렬 한 번    run 을 만들고 스택에 쌓는다
  (binarySort)               |
        |                    v
        |              merge 단계 — 여기에만 throw 가 있다
        v                    |
   그냥 끝난다           아귀가 안 맞으면 IllegalArgumentException
   ★ 던질 코드 자체가 없다
```

실측으로 확인했다(`Ex.java (28-a4)`, 값 0~99, 씨앗 0~1999).

**출력** (JDK 21.0.5 — 17·25 동일)

```text
n = 2~31, seed 0~1999 -> 시도 60000회
  IllegalArgumentException 이 난 횟수 : 0
  예외 없이 오름차순이 아닌 결과가 난 횟수 : 54097
n = 32~61, seed 0~1999 -> 시도 60000회
  IllegalArgumentException 이 난 횟수 : 3012
  예외 없이 오름차순이 아닌 결과가 난 횟수 : 56988
```

그림 해설 (한 단계씩):

- ★ **31개 이하에서는 6만 번을 돌려도 한 번도 안 던졌다.** 병합 코드에 도달조차 안 하기 때문이다.
- 그런데 **같은 6만 번 중 54,097번이 오름차순이 아니었다.** 조용히 틀린 것이다.
- 32개부터 던지기 시작하지만 **던지는 비율은 5%(3,012/60,000)** 다. **대부분은 여전히 조용히 틀린다.**
- 결론: **`IllegalArgumentException` 은 계약 위반의 "일부"만 잡는 안전망**이지 검사기가 아니다.

구체적으로 8개짜리 하나를 눈으로 보면 이렇다(`Ex.java (28-a2)` C절, 값 0~99, 씨앗 7).

```text
  n=8 정렬 전 : [36, 64, 85, 44, 80, 54, 68, 49]
  n=8 정렬 후 : [36, 44, 64, 54, 49, 68, 85, 80]
                              ^^^^^^^^        ^^
                      64 다음에 54 가 온다   85 다음에 80
```

- 예외 없음. 반환값도 정상. **오름차순만 아니다.**
- 이 결과를 쓰는 코드(이진 탐색·페이지네이션·상위 N개)는 **전부 조용히 틀린다.**

비용 — 없다. 판별 규칙이다.

> **`MIN_MERGE`** — `TimSort` 가 "이 아래로는 굳이 병합 정렬을 쓰지 않는다"고 정한 경계. JDK 21.0.5 기준 `32` 다.\
> 예: 원소가 31개면 이진 삽입 정렬 한 번으로 끝나고 병합이 없다.

> **조용한 실패(silent failure)** — 에러 없이 정상처럼 끝나는데 결과만 틀린 것.\
> 예: 계약을 깬 비교자로 정렬한 8원소 리스트. 예외도 경고도 없고 오름차순만 아니다.

### (5) ★ `compareTo` 와 `equals` 가 어긋날 때 — `TreeSet` 에서 원소가 사라진다

**언제 쓰나** — 같은 객체 묶음을 `HashSet` 과 `TreeSet` 에 넣었는데 `size()` 가 다를 때.

`Comparable` 의 인터페이스 javadoc 이 이 상황을 직접 설명한다.

> For example, if one adds two keys `a` and `b` such that `(!a.equals(b) && a.compareTo(b) == 0)`
> to a sorted set that does not use an explicit comparator, the second `add`
> operation returns false (and the size of the sorted set does not increase)
> because `a` and `b` are equivalent from the sorted set's perspective.

직접 만들어 확인했다(`Ex.java (28-b)`).

```java
record Emp(String name, String dept) implements Comparable<Emp> {
    public int compareTo(Emp o) { return name.compareTo(o.name); }   // 이름만 본다
}
// record 의 equals 는 name 과 dept 를 둘 다 본다
```

**출력** (JDK 21.0.5 — 17·25 동일)

```text
--- 1. compareTo 와 equals 가 어긋날 때 ---
a.equals(b)    : false
a.compareTo(b) : 0
HashSet  size  : 2  [Emp[name=김, dept=영업], Emp[name=김, dept=개발]]
TreeSet  size  : 1  [Emp[name=김, dept=영업]]
TreeSet.contains(b) : true   (b 는 없는데 true)
TreeSet 에 남은 것이 a 인가 : true
```

```text
  HashSet (equals · hashCode 로 판정)       TreeSet (compareTo 로만 판정)
  +---------------------------------+       +---------------------------------+
  | add(a) -> 들어간다               |       | add(a) -> 들어간다               |
  | add(b) -> equals 가 false        |       | add(b) -> compareTo 가 0         |
  |          -> 다른 것으로 본다      |       |          -> 같은 것으로 본다      |
  | size = 2                        |       | size = 1  ★ b 가 사라졌다        |
  | contains(b) = true              |       | contains(b) = true ★ 없는데 true |
  +---------------------------------+       +---------------------------------+
```

그림 해설 (한 단계씩):

- ★ **`TreeSet`/`TreeMap` 은 `equals` 를 부르지 않는다.** `compareTo`(또는 `Comparator`)의 결과가 `0` 인지만 본다.
- 그래서 `equals` 가 다르다고 말해도 **원소가 조용히 버려진다.** 예외도 경고도 없다.
- 더 나쁜 것은 `contains(b)` 가 **`true` 를 돌려준다**는 것이다 — 집합 안에 `b` 는 없는데 있다고 한다.
- 이것은 `Set` 계약 위반이다. javadoc 이 "violates the general contract for set (or map), which is defined in terms of the `equals` method" 라고 적어 두었다.

`TreeMap` 에서는 **키와 값이 어긋난다.**

```text
HashMap : {1.0=첫째, 1.00=둘째}
TreeMap : {1.0=둘째}   ★ 키는 1.0 인데 값은 둘째다
```

- `put(y, "둘째")` 가 **새 엔트리를 만들지 않고 기존 키의 값만 덮었다.** 키는 처음 것이 남는다.

비용 — 없다. **정확성 문제**다.

### (6) `Comparator` 조합 — `comparing`·`thenComparing`·`reversed`·`nullsFirst`

**언제 쓰나** — 두 개 이상의 기준으로 정렬할 때. 손으로 `if` 를 쌓지 않는다.

```java
import static java.util.Comparator.*;

list.sort(comparing(P::dept).thenComparing(P::name));
list.sort(comparing(P::dept).thenComparing(P::age, reverseOrder()));
list.sort(comparing(P::age, nullsFirst(naturalOrder())));
```

**출력** (`Ex.java (28-c)`, JDK 21.0.5 — 17·25 동일)

```text
--- 1. comparing / thenComparing ---
dept, name        : [개발/김/40, 개발/박/30, 영업/김/25, 영업/이/25]
dept, age 내림차순 : [개발/김/40, 개발/박/30, 영업/김/25, 영업/이/25]
```

★ **`reversed()` 는 앞의 조합 전체를 뒤집는다.** 이것이 가장 흔한 실수다.

```text
--- 2. reversed() 는 앞의 조합 전체를 뒤집는다 ---
(dept then name).reversed() : [영업/이/25, 영업/김/25, 개발/박/30, 개발/김/40]
dept.reversed() then name   : [영업/김/25, 영업/이/25, 개발/김/40, 개발/박/30]
```

```text
  comparing(dept).thenComparing(name).reversed()     comparing(dept).reversed().thenComparing(name)
  +------------------------------------------+       +------------------------------------------+
  | "dept 오름, 같으면 name 오름" 을          |       | "dept 내림" 을 만들고                     |
  |  통째로 뒤집는다                          |       |  거기에 "name 오름" 을 붙인다             |
  | -> dept 내림 + name 내림                  |       | -> dept 내림 + name 오름                  |
  | 영업/이 -> 영업/김 -> 개발/박 -> 개발/김   |       | 영업/김 -> 영업/이 -> 개발/김 -> 개발/박   |
  +------------------------------------------+       +------------------------------------------+
```

그림 해설 (한 단계씩):

- `reversed()` 는 **그 시점까지 조립된 비교자 하나**를 뒤집는다. 메서드 체인의 순서가 곧 괄호다.
- 한 키만 뒤집고 싶으면 **그 키에 붙인다** — `thenComparing(P::age, reverseOrder())`.
- 읽기 헷갈리면 중간 변수로 끊는다. `var byDept = comparing(P::dept).reversed();`

`null` 이 섞이면 이렇게 갈린다(같은 프로그램).

```text
--- 4. null 이 섞이면 ---
comparing(P::age)            -> java.lang.NullPointerException: Cannot invoke "java.lang.Comparable.compareTo(Object)" because the return value of "java.util.function.Function.apply(Object)" is null
nullsFirst(naturalOrder())   : [개발/최/null, 영업/김/25, 영업/이/25, 개발/박/30, 개발/김/40]
nullsLast(naturalOrder())    : [영업/김/25, 영업/이/25, 개발/박/30, 개발/김/40, 개발/최/null]

--- 5. 리스트 자체에 null 원소가 섞이면 ---
naturalOrder -> java.lang.NullPointerException: Cannot invoke "java.lang.Comparable.compareTo(Object)" because "c1" is null
nullsFirst(naturalOrder()) : [null, a, b]
```

- ★ **NPE 메시지가 어느 `null` 인지 구분해 준다** — 앞은 "추출한 키가 null", 뒤는 "원소 자체가 null".
- `nullsFirst`/`nullsLast` 는 **감싸는 비교자**다. 안쪽 비교자는 `null` 을 절대 못 본다.

비용 — 조합 하나당 람다 한 겹. 핫 루프에서 `comparing(P::age)` 는 **박싱**이 생기므로 `comparingInt` 를 쓴다.

> **`naturalOrder()`** — `Comparable` 의 `compareTo` 를 그대로 쓰는 비교자(`@since 1.8`).\
> 예: `nullsFirst(naturalOrder())` 는 "null 을 앞에, 나머지는 자연 순서로".

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### 둘을 가르는 기준

| | `Comparable` | `Comparator` |
|---|---|---|
| 어디에 있나 | 타입 자신이 구현 | 밖에서 넘긴다 |
| 몇 개 | **하나**(자연 순서) | **필요한 만큼** |
| 메서드 | `int compareTo(T o)` | `int compare(T a, T b)` |
| `null` | `e.compareTo(null)` 은 NPE 여야 한다 | 허용해도 된다 |
| 패키지 | `java.lang` | `java.util` |
| 버전 | 1.2 | 1.2 (조합 메서드는 8) |

- **그 타입에 "당연한 하나"가 있으면 `Comparable`** — 숫자·날짜·문자열.
- **관점이 여럿이면 `Comparator`** — "가격순"·"인기순"·"거리순".
- `List.sort(null)` 은 `Comparator` 자리에 `null` 을 주는 것이고, **자연 순서를 쓰라는 뜻**이다.

```text
list.sort(null) -> 자연 순서 : [a, b, c]
```

### 조합 메서드 지도 (전부 `@since 1.8` — src.zip 확인)

| 만드는 것 | 호출 |
|---|---|
| 키 하나로 | `comparing(P::name)` · `comparingInt/Long/Double(P::age)` |
| 키 + 그 키의 비교자 | `comparing(P::age, reverseOrder())` |
| 2차 기준 | `.thenComparing(P::name)` · `.thenComparingInt(P::age)` |
| 뒤집기 | `.reversed()` · `reverseOrder()` |
| 자연 순서 | `naturalOrder()` |
| `null` 처리 | `nullsFirst(cmp)` · `nullsLast(cmp)` |

### 구현의 표준 형태

```java
// 1. 뺄셈을 쓰지 않는다
public int compareTo(P o) { return Integer.compare(age, o.age); }     // O
public int compareTo(P o) { return age - o.age; }                      // X 오버플로

// 2. 여러 키는 조합으로
static final Comparator<P> ORDER =
    Comparator.comparing(P::dept).thenComparing(P::name).thenComparingInt(P::age);
public int compareTo(P o) { return ORDER.compare(this, o); }

// 3. equals 와 같은 필드를 쓴다 (권고 ④)
```

### 람다·메서드 참조의 타입 추론이 끊기는 자리

```java
l.sort(comparing(p -> p.dept()).thenComparing(p -> p.name()));   // 컴파일 에러
```

```text
Ex.java:7: error: cannot find symbol
        l.sort(comparing(p -> p.dept()).thenComparing(p -> p.name()));
                               ^
  symbol:   method dept()
  location: variable p of type Object
2 errors
```

- `comparing` 의 결과에 `.thenComparing` 을 이어 붙이면 **람다의 타입을 추론할 근거가 끊긴다.**
- 고치는 법 둘 — **메서드 참조로 바꾸거나**(`comparing(P::dept)`), **타입 인자를 명시**한다(`Comparator.<P, String>comparing(...)`).\
  둘 다 컴파일됨을 확인했다(`Ex.java (28-d2)`).

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. **다섯 중 넷이 예외 없이 조용히 틀린다.**

### 1. ★ "대략 같으면 같다고 치자" 비교자를 쓴다

```java
Comparator<Integer> FUZZY = (x, y) -> Math.abs(x - y) <= 10 ? 0 : Integer.compare(x, y);
```

- 추이성이 깨진다 — `0~10` 은 같고 `10~20` 은 같은데 `0~20` 은 다르다((3)에서 실행으로 확인).
- 작은 데이터에서는 **터지지도 않고 결과가 맞아 보이기도 한다.** 그래서 리뷰를 통과한다.
- 같은 모양의 실무 코드들.
  - 점수를 반올림해 비교 — `(int) Math.round(a.score) - (int) Math.round(b.score)`
  - 날짜를 "같은 날이면 같다"로 비교하면서 시각도 보는 경우
  - 문자열을 `trim()` 해서 비교하다가 어떤 경로만 안 하는 경우
- 방어: **`0` 을 돌려주는 조건이 진짜 동치 관계인지** 확인한다. "가깝다"는 동치가 아니다.

### 2. 뺄셈으로 비교해 오버플로를 만든다

```java
Comparator<Integer> minus = (a, b) -> a - b;
```

**출력** (`Ex.java (28-b)`)

```text
--- 3. 뺄셈 비교자와 오버플로 ---
big - neg              = -2147483639   (음수! 오버플로)
(a, b) -> a - b        : [2147483647, -10, 0]   ★ 틀렸다
Integer::compare       : [-10, 0, 2147483647]
```

- `Integer.MAX_VALUE - (-10)` 은 `int` 범위를 넘어 **음수로 돈다.** 그래서 "가장 큰 값이 가장 작다"고 나온다.
- 값 범위가 좁으면 평생 안 터진다 — **음수가 섞이는 순간**부터 틀린다.
- 방어: **`Integer.compare(a, b)`·`Long.compare`·`Double.compare` 를 쓴다.** 뺄셈은 쓰지 않는다.
- 오버플로 자체의 정본은 [`../02-numeric-operations/`](../02-numeric-operations/).

### 3. ★ `compareTo` 와 `equals` 를 다른 필드로 쓴다

(5)에서 본 그대로다. **`HashSet` 과 `TreeSet` 의 `size()` 가 갈린다.**

JDK 안의 대표 사례가 `BigDecimal` 이다(`Ex.java (28-b)`).

```text
--- 2. BigDecimal — JDK 안의 대표 사례 ---
x.equals(y)    : false
x.compareTo(y) : 0
HashSet  size  : 2
TreeSet  size  : 1  [1.0]
HashMap : {1.0=첫째, 1.00=둘째}
TreeMap : {1.0=둘째}   ★ 키는 1.0 인데 값은 둘째다
```

- `new BigDecimal("1.0")` 과 `new BigDecimal("1.00")` 은 **값은 같고 스케일이 다르다.**
- `compareTo` 는 값만 보고, `equals` 는 스케일까지 본다. **`BigDecimal` 의 javadoc 이 그렇게 적어 두었다** —
  "Note: this class has a natural ordering that is inconsistent with equals."
- ★ 이것이 javadoc 이 요구한 **"clearly indicate this fact"** 의 실제 모습이다. 권고 ④ 를 깨려면 이렇게 밝혀야 한다.
- `BigDecimal` 의 스케일·반올림 자체는 [`../53-bigdecimal/`](../53-bigdecimal/) 가 정본이다.\
  여기서는 **"계약 ④ 를 깨면 컬렉션이 어떻게 갈리나"** 라는 관점만 쓴다.

### 4. `compareTo(null)` 이 `false` 를 돌려줄 거라 기대한다

```text
--- 4. compareTo(null) ---
a.compareTo(null) -> java.lang.NullPointerException: Cannot read field "name" because "o" is null
a.equals(null)    -> false
```

- **`equals` 와 정반대다.** `equals(null)` 은 `false` 를 돌려줘야 하고, `compareTo(null)` 은 **NPE 를 던져야 한다.**
- `Comparable` 의 javadoc 원문: "`e.compareTo(null)` should throw a `NullPointerException` even though `e.equals(null)` returns `false`."
- 위 NPE 는 **일부러 던진 것이 아니라 필드를 읽다가 난 것**이다 — 결과적으로 계약에 맞지만, 의도를 밝히려면
  `Objects.requireNonNull(o)` 로 먼저 막는 편이 낫다([**60번 주제**](../60-null-handling/)).

### 5. `reversed()` 를 체인 끝에 붙여 놓고 한 키만 뒤집힌 줄 안다

(6)에서 본 그대로다. `comparing(A).thenComparing(B).reversed()` 는 **A 와 B 둘 다** 내림차순이 된다.

- 한 키만 뒤집으려면 **그 키에 붙인다** — `thenComparing(P::age, reverseOrder())`.
- 이건 예외가 안 나고 **순서만 틀린다.** 페이지네이션·상위 N개에서 조용히 틀린 결과가 나간다.

## 구현 세부사항 대 언어 보장

이 절은 **"어디까지 믿어도 되나"**를 가른다.

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| 대칭·추이·동치 일관성 세 조항 | **javadoc (계약)** | `Comparable.compareTo` · `Comparator.compare` javadoc |
| `equals` 와의 일관성 | **권고만** | "strongly recommended, but *not* strictly required" |
| `e.compareTo(null)` 이 NPE | **javadoc (계약)** | `Comparable` 인터페이스 javadoc |
| `TreeSet`/`TreeMap` 이 `compareTo` 로 같음을 판정 | **javadoc (계약)** | `SortedSet`/`SortedMap` 의 정의. `Comparable` javadoc 이 결과까지 설명 |
| 계약을 어기면 `IllegalArgumentException` 이 **난다** | **아니다 — 보장 없음** | 감지됐을 때만 던진다. 안 나는 경우가 훨씬 많다(실측 (4)) |
| `MIN_MERGE == 32` | **구현 세부** | `TimSort.java` 80행. 버전이 바뀌면 달라질 수 있다 |
| 처음 던지는 원소 수 731 · 89 | **구현 세부 + 데이터 의존** | 씨앗 42 고정, JDK 17·21·25 에서 같았다 — **관찰이다** |
| 예외 메시지 문구 | **구현 세부** | `TimSort.java` 의 문자열 리터럴. 17·21·25 에서 같았다 |
| `List.sort(null)` 이 자연 순서 | **javadoc (계약)** | `List.sort` javadoc — `null` 이면 자연 순서 |

**경계 한 줄** — `IllegalArgumentException` 은 **안전망이지 검사기가 아니다.**\
"안 터졌으니 계약을 지켰다"는 결론은 실측으로 반증됐다(31개 이하 6만 번 중 던진 횟수 0, 틀린 결과 54,097).\
외울 것은 임계값이 아니라 **"계약 위반은 대개 조용히 틀린다"** 는 성질이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 판단 |
|---|---|
| 그 타입에 "당연한 하나"의 순서가 있다 | **`Comparable`** — 숫자·날짜·ID |
| 관점이 여럿이거나 남의 타입이다 | **`Comparator`** — `comparing(...)` 으로 조립 |
| 두 개 이상의 키 | `thenComparing` 으로 잇는다. `if` 를 쌓지 않는다 |
| 기본형 키 | `comparingInt`/`comparingLong`/`comparingDouble` — 박싱이 없다 |
| 한 키만 내림차순 | `thenComparing(key, reverseOrder())` — `.reversed()` 를 끝에 붙이지 않는다 |
| 키가 `null` 일 수 있다 | `nullsFirst`/`nullsLast` 로 감싼다. 안쪽에서 `null` 을 다루지 않는다 |
| `TreeSet`/`TreeMap` 에 넣을 타입 | **④ 를 반드시 지킨다.** 못 지키면 javadoc 처럼 명시하고, 중복을 잃어도 되는지 확인한다 |
| "가까우면 같다"는 비교 | **비교자로 만들지 않는다.** 그룹핑([`../48-collectors-grouping/`](../48-collectors-grouping/))으로 푼다 |
| 두 수의 대소 | `Integer.compare` 등. **뺄셈 금지** |

판단 규칙 세 줄.

- **`0` 을 돌려주는 조건이 동치 관계인가**를 먼저 묻는다. "가깝다"는 동치가 아니다.
- **`equals` 와 같은 필드를 쓴다.** 못 쓰면 그 사실을 javadoc 에 적는다(`BigDecimal` 처럼).
- **뺄셈으로 비교하지 않는다.** `Integer.compare` 하나로 끝난다.

## 핵심 문장

- 계약은 **강제 세 조항(대칭·추이·동치 일관성) + 권고 하나(`equals` 와의 일관성)** 이고, `Comparable` 과 `Comparator` 의 문장이 사실상 같다.
- ★ **계약 위반은 대개 예외가 아니라 조용한 오답으로 나타난다** — 원소 31개 이하 6만 번 중 예외는 0번, 틀린 결과는 54,097번이었다(JDK 21.0.5 실측).
- `IllegalArgumentException: Comparison method violates its general contract!` 는 **병합 단계에서만** 난다. `MIN_MERGE`(21.0.5 기준 32) 미만이면 던질 코드에 도달조차 안 한다.
- ★ **`TreeSet`/`TreeMap` 은 `equals` 를 안 쓴다.** `compareTo` 가 `0` 이면 같은 것으로 보고 **원소를 버린다** — 그런데 `contains` 는 `true` 를 돌려준다.
- `BigDecimal` 이 JDK 안의 대표 사례다. javadoc 이 스스로 "natural ordering that is inconsistent with equals" 라고 밝혀 두었다.
- **뺄셈으로 비교하면 오버플로**로 순서가 뒤집힌다. `Integer.compare` 를 쓴다.
- `.reversed()` 는 **그때까지 조립된 비교자 전체**를 뒤집는다. 한 키만 뒤집으려면 그 키에 `reverseOrder()` 를 준다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 28번)
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — **그쪽은 동치 계약(`equals` 다섯 조항 + `hashCode` 세 조항)까지, 여기는 순서 계약(대칭·추이·동치 일관성)부터.**\
  두 계약이 만나는 자리는 권고 ④ 하나뿐이고, 그 접점은 이 문서의 (5)가 다룬다
- [`../../../../../algorithm/01-elementary-sort/`](../../../../../algorithm/01-elementary-sort/) — **그쪽은 정렬 알고리즘 자체(삽입·병합·비교 횟수)까지, 여기는 그 알고리즘에 넘기는 비교자의 계약부터.**\
  `TimSort` 가 왜 run 을 쌓고 병합하는지는 `cs/algorithm/` 이 정본이고, 이 문서는 **병합 단계에만 `throw` 가 있다**는 사실만 쓴다
- [`../53-bigdecimal/`](../53-bigdecimal/) — **`BigDecimal` 의 스케일·반올림·`equals` 함정의 정본.**\
  여기서는 그것을 "권고 ④ 를 깬 JDK 안의 사례"로만 인용한다
- [`../02-numeric-operations/`](../02-numeric-operations/) — 뺄셈 비교자가 터지는 이유(정수 오버플로)의 정본
- [`../14-records/`](../14-records/) — `record` 가 자동 생성하는 `equals` 와 손으로 쓴 `compareTo` 가 어긋나는 자리
- [`../46-terminal-operations/`](../46-terminal-operations/) — `min`/`max`/`sorted` 가 비교자를 받는 자리
- [`../48-collectors-grouping/`](../48-collectors-grouping/) — "가까우면 같다"를 비교자 대신 그룹핑으로 푸는 법
- [`../49-parallel-streams/`](../49-parallel-streams/) — `Arrays.parallelSort` 도 같은 예외를 던진다는 것
- 목록의 **39번 주제**(컬렉션 지도) — `TreeSet`/`TreeMap` 을 언제 고르나
- [**60번 주제**](../60-null-handling/)(`null` 다루기) — `compareTo(null)` 을 `Objects.requireNonNull` 로 명시적으로 막는 법

## 용어 풀이

- **`Comparable`** — 타입 자신이 가진 하나의 순서(자연 순서)를 정의하는 인터페이스(`java.lang`, 1.2).
- **`Comparator`** — 밖에서 주는 비교 규칙. 한 타입에 여러 개를 만들 수 있다(`java.util`, 1.2).
- **자연 순서(natural ordering)** — `Comparable.compareTo` 가 정의하는 그 타입의 기본 순서.
- **전순서(total order)** — 어떤 두 원소든 대소가 정해지고 대칭·추이가 성립하는 순서.
- **대칭성(antisymmetry)** — `signum(c(x,y)) == -signum(c(y,x))`. 한쪽만 `0` 이면 위반.
- **추이성(transitivity)** — `c(x,y)>0` 이고 `c(y,z)>0` 이면 `c(x,z)>0`.
- **동치의 일관성** — `c(x,y)==0` 이면 모든 `z` 에 대해 `signum(c(x,z))==signum(c(y,z))`.
- **`equals` 와의 일관성(consistent with equals)** — `(c(x,y)==0) == x.equals(y)`. **강제가 아니라 권고**다.
- **`signum`** — 값의 부호만 남긴 것(`-1`/`0`/`1`). `compareTo` 의 반환값은 크기가 아니라 부호만 의미가 있다.
- **`TimSort`** — JDK 의 객체 배열 정렬 알고리즘. 병합 단계에서 계약 위반을 감지하면 `IllegalArgumentException` 을 던진다.
- **`MIN_MERGE`** — `TimSort` 가 병합 정렬로 갈지 이진 삽입 정렬로 끝낼지 가르는 경계. JDK 21.0.5 기준 32.
- **조용한 실패(silent failure)** — 에러 없이 정상처럼 끝나는데 결과만 틀린 것.

---

## 더 들어가면

- **`ComparableTimSort` 와 `TimSort` 는 다른 클래스다.**\
  `Arrays.sort(Object[])` 는 `ComparableTimSort.sort` 로(소스 1042행), `Arrays.sort(T[], Comparator)` 는 `TimSort.sort` 로(1234행) 간다.\
  둘 다 같은 문자열의 `IllegalArgumentException` 을 던지고(`ComparableTimSort.java` 749·871행, `TimSort.java` 782·904행),
  `MIN_MERGE` 도 둘 다 32다. 그래서 `Comparable` 을 잘못 구현해도 증상이 같다.
- **`List.sort` 는 `Arrays.sort` 를 부른다.**\
  소스가 세 줄이다 — `Object[] a = this.toArray(); Arrays.sort(a, (Comparator) c); ...`(`List.java` 507~509행).\
  그래서 이 문서의 결론이 `List.sort`·`Arrays.sort`·`Collections.sort` 에 그대로 적용된다.
- **`Arrays.sort(int[])` 는 이 예외를 절대 안 던진다.**\
  기본형 배열은 비교자가 없어 `DualPivotQuicksort.sort` 로 간다(소스 100·176행 등). 계약 위반이라는 개념 자체가 없다.\
  이 주제의 함정은 **객체 배열·컬렉션에서만** 나온다.
- **`-Djava.util.Arrays.useLegacyMergeSort=true` 로 옛 병합 정렬을 켤 수 있다** — 그러면 **아예 안 던진다.**\
  `Arrays.java` 988~993행의 `LegacyMergeSort.userRequested` 가 이 시스템 속성을 읽는다.\
  같은 프로그램(`Ex.java (28-a3)`)을 이 플래그로 다시 돌리니 n 을 3000까지 올려도 임계값을 못 찾았다(`-1`).

```text
$ java Ex
FUZZY (0~999, seed 42) 가 처음 던진 n = 731
NEVER_ZERO (0~9, seed 42) 가 처음 던진 n = 89

$ java -Djava.util.Arrays.useLegacyMergeSort=true Ex
FUZZY (0~999, seed 42) 가 처음 던진 n = -1
NEVER_ZERO (0~9, seed 42) 가 처음 던진 n = -1
```

  즉 **"예외가 나느냐"는 계약이 아니라 그날 쓰이는 정렬 구현에 달렸다.**\
  이 플래그의 javadoc 주석은 `To be removed in a future release` 라고 적혀 있다.
- **`Comparator` 는 `Serializable` 을 구현하는 편이 좋다.**\
  `Comparator` 의 javadoc 이 직접 권한다 — `TreeSet`/`TreeMap` 을 직렬화할 때 비교자가 함께 직렬화돼야 하기 때문이다.\
  람다로 만든 비교자는 `Serializable` 이 아니다.
- **`thenComparing` 은 오버로드가 셋이라 모호해질 수 있다.**\
  `Comparator<T>` 를 받는 것, 키 추출 함수를 받는 것, 키 추출 함수 + 비교자를 받는 것.\
  람다를 넘기면 어느 것인지 추론이 안 돼 컴파일 에러가 나기도 한다 — **메서드 참조를 쓰면 대개 풀린다.**
