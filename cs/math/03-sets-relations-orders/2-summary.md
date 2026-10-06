# math/03-sets-relations-orders — 집합·함수·관계: 동치관계와 순서가 `equals`·`compare`의 계약이 되는 이유 — 정리 (힌트)

## 해결하는 문제

`HashSet`은 "같다"가 동치관계라고 믿는다. 정렬은 "작다"가 순서라고 믿는다. 그 믿음이 깨져도 컴파일러는 모른다.

```text
  equals 가 대칭이 아니면                     비교자가 추이적이지 않으면
  ───────────────────────────────            ──────────────────────────────────────
  set.add(p); set.add(cp);  → 크기 2         list.sort(cmp)
  set.add(cp); set.add(p);  → 크기 1           → (이 노트 실험에서는) 대개 예외 없이 틀린 순서
  (넣는 순서가 결과를 바꾼다)                   → 가끔 IllegalArgumentException:
                                                Comparison method violates its general contract!
```

쉬운 예: 반 친구들을 "같은 동네 사는 사람"끼리 묶는다. 이 "같다"는 나와 나도 같고(반사), A가 B와 같은 동네면 B도 A와 같은 동네이며(대칭), A=B·B=C면 A=C다(추이). 그래서 동네별 묶음이 깔끔하게 나뉜다.\
"집이 500m 안인 사람"으로 묶으면 다르다. A–B 400m, B–C 400m인데 A–C는 800m일 수 있다. 묶음이 겹치거나, 사슬로 이어져 동네 전체가 한 묶음이 된다.

똑같은 구조다.\
`equals`는 "같은 동네" 같은 동치관계여야 하고, `compare == 0`도 그래야 한다. "가까우면 같다"는 동치관계가 아니다.

실무 예:
- 하위 클래스가 `equals`를 재정의해 `HashSet`·`stream().distinct()`의 중복 제거 결과가 입력 순서에 따라 달라진다.
- `BigDecimal("1.0")`과 `BigDecimal("1.00")`이 `HashSet`에서는 둘, `TreeSet`에서는 하나다.
- 금액을 "0.5 이내면 같다"로 비교하는 비교자로 정렬하자 결과가 뒤죽박죽이고, 데이터에 따라 정렬 예외가 난다.

## 동작·원리

### 1. 집합과 함수 — 화살표로 본다

```text
  관계 R: A → B   (화살표 묶음)

   A          B         함수:     A의 원소마다 나가는 화살표가 많아야 1개 (≤1 out, 전체 함수면 =1)
   1 ───────> a         단사:     B의 원소마다 들어오는 화살표 ≤ 1
   2 ───┬───> b         전사:     B의 원소마다 들어오는 화살표 ≥ 1
   3 ───┘     c         전단사:   나가는 것 = 1, 들어오는 것 = 1  (일대일 대응)

   위 그림: 함수 O, 단사 X (b에 2개), 전사 X (c에 0개)
```

- *집합(set)*: 원소의 모임. 순서와 중복이 없다. `Set`이 "중복 없음"을 지키려면 "같은 원소"의 정의(동치관계)가 필요하다.
- *이항 관계(binary relation)*: 정의역 A, 공역 B, 그리고 화살표(순서쌍)들의 묶음(MCS 정의 4.4.1). 집합 A 위의 관계(A → A)는 방향 그래프와 같다(MCS 10.11).
- *함수(function)*: 원소마다 나가는 화살표가 많아야 1개인 관계. 정확히 1개면 *전체 함수(total)*(MCS 정의 4.4.2).
- *단사(injective)·전사(surjective)·전단사(bijective)*: 들어오는 화살표가 각각 ≤1·≥1·=1이다. 전단사는 여기에 나가는 화살표도 =1이어야 한다(MCS 정의 4.4.2).
- 실무 대응:
  - `hashCode()`는 객체 → `int` 함수다. 객체는 `int`보다 많을 수 있어 단사일 수 없다 → 충돌은 정상이고, 버킷 안에서 `equals`로 최종 확인한다([data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)).
  - 공개 ID ↔ 내부 키 매핑에서 발급된 공개 ID로 내부 키를 하나로 찾으려면(역조회) 단사면 된다. 전단사는 공역 전체(아직 안 쓴 공개 ID까지)에 역함수를 둘 때 필요하다(MCS 문제 4.16: R이 단사 ⇔ 역관계가 함수). 단사가 아니면 두 행이 같은 공개 ID를 갖는다.

### 2. 관계의 성질 — 그래프 모양으로

```text
  성질           정의                                  그래프로 보면
  ─────────────  ───────────────────────────────────  ─────────────────────────────
  반사           x R x  (x 각각)                       꼭짓점마다 자기 고리
  비반사         x R x 인 x가 없다                       자기 고리 없음
  대칭           x R y ⇒ y R x                         간선이 있으면 반대 간선도
  비대칭         x R y ⇒ NOT y R x                     두 점 사이 간선 ≤ 1, 자기 고리 없음
  반대칭         x R y ∧ y R x ⇒ x = y                 서로 다른 두 점 사이 간선 ≤ 1
  추이           x R y ∧ y R z ⇒ x R z                 경로가 있으면 지름길 간선도
```

- 정의와 그림 설명은 MCS 10.11 "Summary of Relational Properties"를 따랐다.
  - 흔한 오해: "비대칭(asymmetric)과 반대칭(antisymmetric)은 같다." — 반대칭은 자기 고리(x R x)를 허용하고, 비대칭은 허용하지 않는다(MCS 10.11). `≤`는 반대칭이고 `<`는 비대칭이다.
- 성질의 조합이 이름을 갖는다:

| 이름 | 성질 | 예 | Java에서 기대하는 곳 |
|---|---|---|---|
| 동치관계 | 반사·대칭·추이 | `=`, mod n 합동 | `equals`, `compare == 0` |
| 약한 부분순서 | 반사·반대칭·추이 | `⊆`, `≤` | — |
| 엄격한 부분순서 | 비반사·추이(→ 비대칭) | `⊂`, 선행 과목, 의존성 | 위상정렬 입력 |
| 선형(전)순서 | 부분순서 + 서로 다른 두 원소가 비교 가능 | 정수의 `<`·`≤` | `Comparable` 자연 순서 |

- 엄격한 부분순서 = 비반사 + 추이(MCS 정의 10.6.7). 약한 부분순서 = 추이 + 반사 + 반대칭(MCS 정의 10.6.13). 선형순서 = 서로 다른 두 원소가 비교 가능한 부분순서(MCS 정의 10.8.1).

### 3. 동치관계 = "같은 라벨" = 분할

```text
  f(x) = x mod 3            동치류 (분할의 블록)
   0 3 6 9  → 라벨 0        [0] = {0, 3, 6, 9}
   1 4 7    → 라벨 1        [1] = {1, 4, 7}
   2 5 8    → 라벨 2        [2] = {2, 5, 8}
  블록끼리 겹치지 않고, 합치면 전체
```

- *동치관계(equivalence relation)*: 반사·대칭·추이인 관계(MCS 정의 10.10.1).
- *동치류(equivalence class)* `[a]`: a와 관계가 있는 원소 전체(MCS 정의 10.10.3).
- *분할(partition)*: 겹치지 않는 비어 있지 않은 블록들로 집합을 나눈 것. 동치관계의 동치류들은 분할의 블록이 된다(MCS 정리 10.10.4).
- 핵심 정리: 관계가 동치관계인 것은, 어떤 전체 함수 f에 대해 "f(a) = f(b)"와 같은 관계인 것과 같다(MCS 10.10, 문제 10.58).
  - 실무로 읽으면: `equals`를 "어떤 키 함수의 값이 같다"로 쓰면 동치관계가 저절로 된다. `record`의 `equals`는 같은 record 클래스의 컴포넌트 값이 같은지로 비교한다(`java.lang.Record` Javadoc).
- `Object.equals` Javadoc(OpenJDK 21)은 null이 아닌 참조에서 반사·대칭·추이·일관성, `x.equals(null) == false`를 요구하고, "equals는 동치관계를 구현한다"고 적는다.
- `hashCode` 계약은 "equals로 같으면 hashCode도 같다" — 동치류가 하나의 해시값 안에 들어가야 한다는 뜻이다.

### 4. 순서 — 부분순서·DAG·전순서·비교자

```text
  부분순서 (의존성)                 전순서 (정수의 ≤)           전전순서 (비교자: 나이순)
     A ──> C                        1 < 2 < 3 < 4              {kim:20, lee:20} < {park:31}
     B ──> C ──> D                  어느 두 개든 비교 가능        같은 나이끼리는 compare = 0
   A와 B는 비교 불가 (순서 없음)                                   (= 동치류를 한 칸으로 본 전순서)
   → 위상정렬: A B C D 또는 B A C D
```

- 엄격한 부분순서의 그래프는 사이클이 없는 방향 그래프(DAG)이고, 유한 DAG는 위상정렬을 갖는다(MCS 10.5–10.6, 정리 10.5.4). 그래프 쪽 성질은 [math 04 graph-theory-basics](../04-graph-theory-basics/2-summary.md), 구현은 [data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md).
- *비교 가능(comparable)*: a R b 또는 b R a(MCS 정의 10.8.1). 부분순서에서는 비교 불가능한 쌍이 있다. 정렬은 비교 불가능한 쌍을 허용하지 않는다.
- *전전순서(total preorder)*: 반사·추이이고 어느 두 원소든 비교 가능한 관계. `compare(x, y) <= 0`이 이것이다. 그 안의 `compare == 0`이 동치관계가 되고, 동치류끼리는 전순서다.
- `Comparator` 계약의 세 조건(부호 반대칭·추이·0의 일관성)과 TimSort가 위반을 만났을 때의 예외, 크기 32 경계는 [algorithm/09-sorting-in-practice](../../algorithm/09-sorting-in-practice/2-summary.md) §2·§3. 여기서는 수학 쪽 의미만 본다.
  - 세 번째 조건 "compare(x, y) == 0이면 z 각각에 대해 sgn(compare(x, z)) == sgn(compare(y, z))"가 `compare == 0`을 동치관계로 만든다(추이성 포함).
- *equals와 일관된(consistent with equals)*: `compare(e1, e2) == 0`과 `e1.equals(e2)`가 같은 값인 것(`Comparator` Javadoc). 일관되지 않으면 `TreeSet`·`TreeMap`은 `Set`·`Map` 일반 계약을 어긴다 — 같은 원소 집합에 동치관계 두 개가 걸린 것이다.

### 실험: 대칭이 깨진 `equals`, 서로 다른 두 동치관계, 추이성 없는 "같음"

코드 핵심(`Rel.java`):

```java
static class Point {                          // 하위 타입도 "같다"고 본다
    public boolean equals(Object o) { return o instanceof Point p && p.x == x && p.y == y; }
    public int hashCode() { return 31 * x + y; }
}
static class ColorPoint extends Point {       // ColorPoint 끼리만 "같다"고 본다
    public boolean equals(Object o) { return o instanceof ColorPoint cp && super.equals(cp) && cp.color.equals(color); }
}
static final Comparator<Double> NEAR = (a, b) -> Math.abs(a - b) <= 0.5 ? 0 : Double.compare(a, b);
```

(실험, OpenJDK 21.0.12 Temurin, docker `--cpus=2 --network none`, `java Rel.java`, 2026-10-07 — 3)의 뒤에 붙는 `NEAR` 정렬 반복 5줄(n=31~10000, 각 200회 예외 0회)은 생략, 정렬 결과는 아래 `Near.java`)

```text
== 1) equals 대칭 위반
p.equals(cp)=true  cp.equals(p)=false
add(p) 후 add(cp): size=2 [P(1,2), CP(1,2,red)]
add(cp) 후 add(p): size=1 [CP(1,2,red)]
{p}.contains(cp)=false  {cp}.contains(p)=true
List.of(p, cp).stream().distinct().count()=2  List.of(cp, p)...=1
== 2) 서로 다른 두 동치관계: BigDecimal equals vs compareTo
equals=false compareTo=0
HashSet size=2  TreeSet size=1  stripTrailingZeros 후 HashSet size=1
== 3) '가까우면 같다' 비교자 — 추이성 없는 '같음'
NEAR(1.0,1.4)=0 NEAR(1.4,1.8)=0 NEAR(1.0,1.8)=-1
TreeSet 넣는 순서 [1.0,1.4,1.8] → [1.0, 1.8] / [1.4,1.0,1.8] → [1.4]
== 4) union-find = 관계의 추이 폐포 → 동치류
값 [1.0, 1.4, 1.8, 2.2, 5.0, 5.3], |a-b|<=0.5 를 union → 동치류 [[1.0, 1.4, 1.8, 2.2], [5.0, 5.3]]
|1.0-2.2|=1.2000000000000002 인데 같은 동치류
```

- 1) `HashMap`은 새로 넣는 키를 기준으로 `key.equals(k)`(k = 이미 있는 키)를 부른다(OpenJDK 21 `HashMap.putVal`·`getNode`). 그래서 대칭이 깨지면 **넣는 순서**와 **누가 묻느냐**가 결과를 바꾼다. `distinct()`도 같은 결과였다.
- 2) `BigDecimal.equals`는 값과 스케일을 같이 보고, `compareTo`는 값만 본다. Javadoc이 "natural ordering이 equals와 일관되지 않다"고 적는다. 같은 원소에 동치관계가 둘이라 `HashSet`과 `TreeSet`이 다른 크기를 낸다.
- 3) `NEAR`의 "0"은 추이적이지 않다(1.0≈1.4, 1.4≈1.8인데 1.0<1.8). `TreeSet`의 결과가 넣는 순서에 따라 원소 2개·1개로 달라졌다.
- 4) union-find는 "가깝다" 관계의 **추이 폐포**(사슬로 이어진 것을 전부 같다고 봄)를 계산한다. 그래서 1.2만큼 떨어진 1.0과 2.2가 한 동치류가 된다. 추이적이지 않은 관계로 묶으면 사슬이 길어질수록 묶음이 커진다.

`NEAR`로 정렬하면 어떻게 되나(`Near.java`, 같은 환경). 값을 [0, 범위·n)에서 균등하게 뽑아 200회(시드 0~199). "역전" = 정렬 결과에서 i < j인데 xs[i] − xs[j] > 0.5인 쌍이 있음(비교자 자신의 기준으로도 틀린 순서):

```text
범위=[0, 0.60·n) n=31    예외   0회, 예외 없이 '|차이|>0.5 역전'  88회 (200회 중), 최대 역전 1.10
범위=[0, 0.60·n) n=32    예외   0회, 예외 없이 '|차이|>0.5 역전'  88회 (200회 중), 최대 역전 1.04
범위=[0, 0.60·n) n=1000  예외   0회, 예외 없이 '|차이|>0.5 역전' 200회 (200회 중), 최대 역전 1.41
범위=[0, 0.60·n) n=10000 예외   0회, 예외 없이 '|차이|>0.5 역전' 200회 (200회 중), 최대 역전 1.84
범위=[0, 0.10·n) n=31    예외   0회, 예외 없이 '|차이|>0.5 역전' 200회 (200회 중), 최대 역전 2.16
범위=[0, 0.10·n) n=32    예외   5회, 예외 없이 '|차이|>0.5 역전' 194회 (200회 중), 최대 역전 2.10
범위=[0, 0.10·n) n=1000  예외   1회, 예외 없이 '|차이|>0.5 역전' 199회 (200회 중), 최대 역전 2.22
범위=[0, 0.10·n) n=10000 예외   0회, 예외 없이 '|차이|>0.5 역전' 200회 (200회 중), 최대 역전 2.35
범위=[0, 0.02·n) n=31    예외   0회, 예외 없이 '|차이|>0.5 역전' 185회 (200회 중), 최대 역전 0.61
범위=[0, 0.02·n) n=32    예외   3회, 예외 없이 '|차이|>0.5 역전' 190회 (200회 중), 최대 역전 0.64
범위=[0, 0.02·n) n=1000  예외 174회, 예외 없이 '|차이|>0.5 역전'  26회 (200회 중), 최대 역전 3.33
범위=[0, 0.02·n) n=10000 예외 170회, 예외 없이 '|차이|>0.5 역전'  30회 (200회 중), 최대 역전 3.63
```

- 이 실험에서 예외는 값이 빽빽할 때(범위 0.02·n, n ≥ 1000) 주로 났다. 나머지 대부분은 **예외 없이 틀린 순서**였다. 예외는 위반을 우연히 발견했을 때만 난다([algorithm/09](../../algorithm/09-sorting-in-practice/2-summary.md)의 결론과 같다).
- n = 31에서는 예외가 0회였다. 32 미만은 병합 없이 이진 삽입 정렬로 끝나기 때문이다(09번 노트의 `MIN_MERGE = 32`).
- 같은 비교자라도 데이터 분포에 따라 예외가 나기도 안 나기도 한다. "특정 고객 데이터에서만 터지는" 이유다.

## 쓰이는 자료구조·알고리즘

- **해시 집합·해시 맵** — `equals`(동치관계)와 `hashCode`(동치류 → 정수 함수) → [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **union-find** — 간선을 하나씩 넣으며 동치류(추이 폐포)를 유지 → [data-structure/14-union-find](../../data-structure/14-union-find/2-summary.md)
- **위상정렬** — 엄격한 부분순서(DAG)를 전순서 하나로 펼침 → [data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md), 그래프 성질은 [math 04](../04-graph-theory-basics/2-summary.md)
- **정렬·정렬 컬렉션** — 전전순서(비교자), equals와의 일관성 → [algorithm/09-sorting-in-practice](../../algorithm/09-sorting-in-practice/2-summary.md), [data-structure/06-binary-search-tree](../../data-structure/06-binary-search-tree/2-summary.md)
- **집합 연산** — 합집합·교집합·차집합 = OR·AND·AND NOT([01-propositional-logic](../01-propositional-logic/2-summary.md)). 비트셋으로 구현 → [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 증상 → 어느 성질이 깨졌나

| 증상 | 의심할 성질 | 확인 |
|---|---|---|
| `Set` 크기·`distinct()` 결과가 넣는 순서에 따라 다름 | `equals` 대칭 | `a.equals(b) == b.equals(a)`를 하위 타입 섞어 검사 |
| `HashSet`에는 둘, `TreeSet`에는 하나 | 동치관계 두 개(equals vs compare) | `compare == 0`인데 `!equals`인 쌍 |
| 정렬 결과가 뒤죽박죽, 가끔 `Comparison method violates...` | 비교자 추이성·0의 일관성 | "가까우면 0", 뺄셈 비교, 무작위 비교 |
| 중복 제거하니 서로 먼 값이 한 묶음 | 추이성 없는 관계를 union-find·그룹화에 사용 | 묶음 안 최대 거리 |
| 위상정렬 실패 | 순서가 아니라 사이클 | 의존 그래프 사이클 탐지 |

### 2. 계약을 테스트로 고정한다

```java
// 세 원소 조합 전부에 대해 동치관계 공리를 검사 (표본은 하위 타입·경계값 섞어서)
static <T> void assertEquivalence(List<T> xs) {
    for (T a : xs) {
        assertTrue(a.equals(a));                                         // 반사
        for (T b : xs) {
            assertEquals(a.equals(b), b.equals(a));                      // 대칭
            if (a.equals(b)) assertEquals(a.hashCode(), b.hashCode());   // hashCode 계약
            for (T c : xs)
                if (a.equals(b) && b.equals(c)) assertTrue(a.equals(c)); // 추이
        }
    }
}
```

- 비교자도 같은 모양으로 부호 반대칭·추이·0의 일관성을 검사한다. 값은 무작위로 뽑는다([testing/14](../../testing/14-property-based-testing/2-summary.md)).

### 3. 고치는 법

- `equals`는 "키 함수의 값이 같다"로 만든다(§3 정리). 값 객체는 `record`로 쓴다.
- 상속 계층에서 필드를 더하는 하위 클래스는 상위 `equals`와 대칭을 지키기 어렵다. 상속 대신 조합(`ColorPoint`가 `Point`를 필드로 가짐)을 쓴다(Bloch, *Effective Java* 3판 Item 10 — 장 단위 인용).
- "가까우면 같다"가 필요하면 비교자에 넣지 말고, 값을 먼저 **양자화**(예: 센트 단위 반올림, 시간 버킷)한 뒤 그 키로 비교한다. 양자화 함수 f가 있으면 "f 값이 같다"는 동치관계다.
- `BigDecimal`을 해시 키로 쓰면 `stripTrailingZeros()`나 `setScale(...)`로 스케일을 통일한다(실험 2).

## 장애 시나리오와 대처

### 1. `equals` 비대칭 → `HashSet` 중복 원소 (⚠ 커리큘럼)

- **현상**: 중복 제거한 목록에 같은 좌표·같은 주문이 두 번 나온다. 배포마다, 요청마다 결과가 다르다.
- **보이는 형태**: 예외 없음. `set.size()`가 기대보다 크고, `set.contains(x)`가 넣은 객체와 "같은" 객체에 `false`를 낸다(실험 1).
- **원인**: 상위 클래스는 `instanceof`로 하위 타입도 같다고 보고, 하위 클래스는 자기 타입만 같다고 본다. `HashMap`은 새 키의 `equals`를 부르므로 넣는 순서가 결과를 정한다.
- **대처**: 대칭을 지키도록 `getClass()` 비교나 조합으로 다시 설계한다. 동치 공리 테스트(적용 §2)를 하위 타입을 섞어 돌린다.

### 2. 비교자 추이성 위반 → `Comparison method violates its general contract!` (⚠ 커리큘럼)

- **현상**: 특정 데이터로 목록을 정렬할 때만 500이 난다. 같은 코드가 다른 날엔 정상이다.
- **보이는 형태**: `java.lang.IllegalArgumentException: Comparison method violates its general contract!`, 스택에 `TimSort.mergeHi`/`mergeLo`. 더 흔하게는 예외 없이 순서가 틀린 결과(실험 `Near.java`).
- **원인**: "차이가 ε 이하면 0" 같은 비교자는 `compare == 0`을 추이적이지 않게 만든다. 뺄셈 비교의 오버플로 등 다른 원인은 [algorithm/09](../../algorithm/09-sorting-in-practice/2-summary.md) §2.
- **대처**: 비교자를 전전순서로 고친다(양자화한 키, `Double.compare`, `Comparator.comparing(...).thenComparing(...)`). `-Djava.util.Arrays.useLegacyMergeSort=true`는 예외만 숨기므로 쓰지 않는다.

### 3. `TreeSet`·`TreeMap`에서 원소가 사라지거나 두 컬렉션 크기가 다르다

- **현상**: 같은 금액 목록을 `HashSet`과 `TreeSet`에 넣었는데 크기가 다르다. 또는 정렬 맵에서 키 하나가 사라진다.
- **보이는 형태**: 예외 없음. `1.0`과 `1.00`이 한쪽에서만 합쳐진다(실험 2).
- **원인**: 비교자(또는 `compareTo`)가 equals와 일관되지 않다. 정렬 컬렉션은 `compare == 0`을 "같은 원소"로 쓴다(`Comparator` Javadoc의 "inconsistent with equals" 경고).
- **대처**: 정렬 컬렉션의 비교자에 동점 해소 키(유일 ID)를 붙이거나, 해시 쪽 키를 정규화(`stripTrailingZeros`)해 두 동치관계를 맞춘다.

### 4. "비슷한 것끼리 묶기"가 전체를 한 덩어리로 만든다

- **현상**: 근접 중복 제거(가격·좌표·시각이 가까운 레코드 병합) 뒤 서로 먼 레코드가 하나로 합쳐졌다.
- **보이는 형태**: 묶음 하나의 최소·최대 차이가 임계값의 몇 배다(실험 4: 임계 0.5인데 1.0과 2.2가 한 묶음).
- **원인**: 추이적이지 않은 관계로 union-find·그룹화를 하면 추이 폐포가 계산되어 사슬이 이어진다.
- **대처**: 고정 격자로 양자화해 동치관계로 바꾸거나, 묶음 지름(최대 거리)에 상한을 두는 군집화를 쓴다. 어느 쪽이든 "같다"의 정의를 문서로 남긴다.

## 핵심 문장

- `equals`와 `compare == 0`은 동치관계(반사·대칭·추이)여야 하고, 그래야 원소들이 겹치지 않는 동치류로 나뉜다.
- 동치관계는 "어떤 키 함수의 값이 같다"와 같은 것이다. `equals`는 키 함수로 정의하면 계약을 지키기 쉽다.
- 대칭이 깨진 `equals`는 `HashSet`의 결과를 넣는 순서에 따라 바꾼다.
- "가까우면 같다"는 추이적이지 않다. 비교자에 넣으면 이 노트 실험에서는 대개 조용히 틀린 순서, 가끔 정렬 예외가 났다(빈도는 입력 분포에 달렸다).
- 엄격한 부분순서(의존성)의 그래프는 DAG이고(MCS 정리 10.6.8) 위상정렬로 전순서 하나로 펼친다. 정렬 비교자는 어느 두 원소든 비교 가능해야 한다.
- 같은 원소에 동치관계가 둘(equals와 compareTo)이면, 해시 컬렉션과 정렬 컬렉션이 다른 답을 낸다.

## 관련 주제·근거

- 선행: [01-propositional-logic](../01-propositional-logic/2-summary.md) — 성질의 정의는 술어 논리식이다
- 함께: [02-induction-and-invariants](../02-induction-and-invariants/2-summary.md) — 정렬 컬렉션·힙의 불변식
- 후속: [04-graph-theory-basics](../04-graph-theory-basics/2-summary.md)(DAG·사이클), [05-counting-and-birthday-bound](../05-counting-and-birthday-bound/2-summary.md)(함수가 단사일 수 없는 비둘기집)
- 연결
  - [algorithm/09-sorting-in-practice](../../algorithm/09-sorting-in-practice/2-summary.md) — 비교자 계약, TimSort 예외와 32 경계, `TreeSet` 원소 소실
  - [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) · [data-structure/14-union-find](../../data-structure/14-union-find/2-summary.md) · [data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md) · [data-structure/06-binary-search-tree](../../data-structure/06-binary-search-tree/2-summary.md) · [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)
  - [testing/14-property-based-testing](../../testing/14-property-based-testing/2-summary.md)
- 교재
  - MCS(2018-06-06 개정판 PDF <https://courses.csail.mit.edu/6.042/spring18/mcs.pdf>) — 4.1 집합, 4.3 함수, 4.4 이항 관계(정의 4.4.1·4.4.2 함수·전사·전체·단사·전단사), 10.5 DAG와 위상정렬(정리 10.5.4), 10.6 부분순서(정의 10.6.1·10.6.7·10.6.9·10.6.12·10.6.13), 10.8 선형순서(정의 10.8.1), 10.10 동치관계(정의 10.10.1–10.10.3, 정리 10.10.4, "f 값이 같다"와의 동치 — 문제 10.58), 10.11 관계 성질 요약. 장 번호는 이 PDF의 목차 기준.
  - Joshua Bloch, *Effective Java* 3판 Item 10 "Obey the general contract when overriding equals" — `Point`/`ColorPoint` 대칭·추이 위반 예와 "조합을 쓰라"(장 단위 인용, 본문 미대조)
- 소스·문서(OpenJDK 21, jdk21u 소스)
  - `java/lang/Object.java` — `equals`의 반사·대칭·추이·일관성·null, "equivalence relation partitions ... into equivalence classes"
  - `java/util/Comparator.java` — 세 조건, "consistent with equals" 정의와 정렬 컬렉션 경고
  - `java/util/HashMap.java` — `getNode`·`putVal`의 `key.equals(k)` 호출 방향
  - `java/math/BigDecimal.java` — `equals`는 스케일까지 비교(2.0 ≠ 2.00), "natural ordering that is inconsistent with equals"
  - `java.lang.Record` Javadoc — 컴포넌트 기반 `equals`
- 실험 목록(이 노트)
  - `Rel.java` — `Point`/`ColorPoint` 대칭 위반의 `HashSet`·`distinct()` 순서 의존, `BigDecimal` 두 동치관계, `NEAR` 비교자와 `TreeSet`, union-find 추이 폐포. OpenJDK 21.0.12 Temurin, docker(`--cpus=2 --network none`), 2026-10-07.
  - `Near.java` — `NEAR` 비교자 정렬, 값 밀도 3단계 × n 4단계 × 200회(시드 0~199)의 예외·역전 빈도. 같은 환경.
