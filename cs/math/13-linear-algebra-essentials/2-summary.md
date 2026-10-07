# math/13-linear-algebra-essentials — 벡터·행렬·내적·노름·코사인 유사도 — 정리 (힌트)

## 해결하는 문제

"이 문서와 비슷한 문서"를 찾으려면 **비슷함을 숫자 하나로** 바꿔야 한다.\
그 숫자를 계산하는 도구가 벡터와 내적이다.

쉬운 예: 두 사람의 영화 취향 비교.

```text
          액션  로맨스  공포
  나      [ 1,    1,    0 ]
  친구A   [ 1,    1,    0 ]     ← 영화를 2편 봤고 취향이 나와 똑같다
  친구B   [ 6,    2,    5 ]     ← 영화를 13편 봤고 취향은 반쯤 겹친다
```

- 장르별 편수를 곱해서 더하면(내적) 친구B가 8점, 친구A가 2점이다. "많이 본 사람"이 이긴다.
- 편수를 각자의 총량으로 나눠 **방향만** 비교하면(코사인) 친구A가 1.0, 친구B가 약 0.70이다. "취향이 같은 사람"이 이긴다.

똑같은 구조다.\
실무 예:
- 임베딩 검색에서 긴 문서·자주 등장하는 상품이 질의와 무관하게 상위를 차지한다. 노름(길이)이 점수에 섞였기 때문이다.
- 행렬로 된 배치 계산(점수표 집계, 행렬곱)이 루프 순서 하나 때문에 10배 느리다. 행렬이 메모리에 놓인 방향과 순회 방향이 어긋났기 때문이다.

이 노트는 두 질문에 답한다.
1. 어떤 "비슷함"을 계산하고 있나 → 내적·노름·코사인
2. 같은 계산이 왜 10배 느린가 → 행렬의 메모리 배치

## 동작·원리

### 1. 벡터와 내적

```text
  y 축
   │    ↗ y = (1, 2)     ← 더 가파르다(기울기 2)
   │   ／  θ
   │  ／      ↗ x = (3, 1)  (기울기 1/3)
   │ ／  ／
   │／／
   └──────────── x 축

  x·y = 3×1 + 1×2 = 5
  |x| = √(3² + 1²) = √10 ≈ 3.16     |y| = √(1² + 2²) = √5 ≈ 2.24
  cos θ = x·y / (|x|·|y|) = 5 / 7.07 ≈ 0.71
```

- *벡터*: 숫자 d개를 순서대로 묶은 것. 임베딩은 문서·문장·상품을 d차원 벡터로 바꾼 결과다.
  - *차원(d)*: 벡터에 든 숫자의 개수.
- *내적(dot product)*: `x·y = x₁y₁ + x₂y₂ + … + x_d·y_d`.
  - 같은 위치끼리 곱해서 모두 더한다.
- *노름(L2 노름, 길이)*: `|x| = √(x·x)`. 원점에서 화살표 끝까지의 거리다.
- *코사인 유사도*: `cos θ = x·y / (|x|·|y|)`. 두 화살표 사이 각도 θ의 코사인이다.
  - 1이면 같은 방향, 0이면 직각(무관), −1이면 반대 방향.
  - 흔한 오해: "내적이 크면 비슷하다." 내적은 방향과 **길이의 곱**이다. 길이가 다르면 내적만으로 비슷함을 비교할 수 없다.
- 왜 `x·y = |x||y|cos θ`인가: 코사인 법칙 `|x−y|² = |x|² + |y|² − 2|x||y|cos θ`와 전개식 `|x−y|² = |x|² + |y|² − 2x·y`를 맞대면 나온다(MIT 18.06, Strang 『Introduction to Linear Algebra』 1장 [?]).
- *코시–슈바르츠 부등식*: `|x·y| ≤ |x|·|y|`. 그래서 코사인은 항상 −1~1 범위다(0벡터는 정의되지 않는다 — 나눗셈 분모가 0).

### 2. 노름이 순위를 비트는 이유

```text
  질의 q = [1, 1, 0]

  문서         벡터          |v|     q·v    cos
  A 짧은 문서  [1, 1, 0]     1.41    2.0   1.000   ← 주제가 정확히 같다
  B 긴 문서    [6, 2, 5]     8.06    8.0   0.702
  C 아주 긴    [2, 0, 12]   12.17    2.0   0.116   ← 딴 주제

  내적 순위:   B(8.0) > A(2.0) = C(2.0)
  코사인 순위: A(1.000) > B(0.702) > C(0.116)
```

- 내적 = `|q|·|v|·cos θ`다. 문서 쪽 길이 `|v|`가 클수록 점수가 커진다.
  - 단어 수를 센 벡터라면 긴 문서가, 상호작용 수를 실은 벡터라면 인기 상품이 길이가 길다.
- 질의 쪽 길이 `|q|`는 모든 문서 점수에 똑같이 곱해진다. 그래서 **순위는 문서 쪽 노름만 비튼다.**
- 해결은 문서 벡터를 **저장할 때 길이 1로 나눠 두는 것**(정규화)이다.

```text
  정규화:  u = v / |v|      → |u| = 1

  길이가 모두 1이면
    u·w            = cos θ                      (내적 = 코사인)
    |u − w|²       = |u|² + |w|² − 2u·w = 2 − 2cos θ   (유클리드 거리도 코사인의 단조 함수)
  → 내적·코사인·L2 거리 세 기준이 같은 순위를 낸다
```

- pgvector README도 같은 말을 한다. 연산자는 `<->`(L2 거리), `<#>`(음의 내적), `<=>`(코사인 거리)다. "벡터가 길이 1로 정규화돼 있으면(OpenAI 임베딩처럼) 최고 성능을 위해 내적을 쓰라"고 적는다.
- 길이에 의미를 일부러 실은 모델도 있다(예: 크기에 인기도를 반영한 추천 점수). 그때는 내적이 의도다. **모델 문서가 어느 거리를 전제로 학습했는지** 먼저 확인한다.

#### 실험: 내적 순위 vs 코사인 순위

- 3차원 예(위 그림) + 무작위 20,000개 × 64차원. 무작위 쪽은 벡터마다 길이 배율을 로그정규 분포(`exp(N(0,1))`)로 곱해 노름을 제각각으로 만들었다.
- 코드 핵심(`LinAlg.java`):

```java
static double dot(double[] x, double[] y) { double s = 0; for (int i = 0; i < x.length; i++) s += x[i] * y[i]; return s; }
static double norm(double[] x) { return Math.sqrt(dot(x, x)); }
static double cos(double[] x, double[] y) { return dot(x, y) / (norm(x) * norm(y)); }

// 노름이 제각각인 벡터
for (int i = 0; i < N; i++) { double scale = Math.exp(rnd.nextGaussian());
    for (int k = 0; k < d; k++) V[i][k] = rnd.nextGaussian() * scale; }
```

(실험, OpenJDK 21.0.12 temurin, Docker `--cpus=2`, 2026-10-07 — 시드 고정이라 4회 모두 같은 출력)

```text
A 짧은 문서(주제 일치)   v=[1.0, 1.0, 0.0]  |v|=  1.41  q·v=  2.0  cos=1.000
B 긴 문서(주제 반쯤)    v=[6.0, 2.0, 5.0]  |v|=  8.06  q·v=  8.0  cos=0.702
C 아주 긴 문서(딴 주제)  v=[2.0, 0.0, 12.0]  |v|= 12.17  q·v=  2.0  cos=0.116
무작위 N=20000 d=64 (노름 = 로그정규 배율): top-10 겹침 0/10, 평균 노름 전체 13.2 / 내적 top 178.2 / 코사인 top 5.7
저장 시 정규화한 뒤 내적 top-10 == 코사인 top-10 ? true
```

- 관찰 1: 무작위 데이터에서 내적 top-10과 코사인 top-10이 **하나도 겹치지 않았다.** 내적 top-10의 평균 노름은 178.2로 전체 평균 13.2의 약 13배다. 내적은 사실상 "길이가 긴 벡터"를 뽑았다.
- 관찰 2: 코사인 top-10의 평균 노름 5.7은 길이와 무관하게 뽑힌 10개의 우연한 값이다(해석 — 코사인 식에 길이가 들어가지 않는다).
- 관찰 3: 미리 정규화해 두면 내적 top-10이 코사인 top-10과 정확히 같다. 위 상자의 등식대로다.

### 3. 행렬과 메모리 배치

```text
  논리적 행렬 (3×4)                 메모리 (행 우선, row-major — 평평한 배열 a[i*n + j])
  ┌ a00 a01 a02 a03 ┐               │a00│a01│a02│a03│a10│a11│a12│a13│a20│a21│a22│a23│
  │ a10 a11 a12 a13 │                └──── 캐시 라인 64 B = double 8개 ────┘
  └ a20 a21 a22 a23 ┘

  행 우선 순회 (j가 안쪽)   a00 → a01 → a02 …  주소가 8 B씩 증가 → 한 번 가져온 캐시 라인을 끝까지 씀
  열 우선 순회 (i가 안쪽)   a00 → a10 → a20 …  주소가 n×8 B씩 점프 → 거의 매번 새 캐시 라인
```

- *행렬*: 숫자를 행과 열로 배치한 표. m×n 행렬은 m행 n열이다.
- *행 우선(row-major)*: 같은 행의 원소가 메모리에 붙어 있는 배치. C 배열과 위 평평한 배열 `a[i*n + j]`가 이렇다.
  - Java `double[][]`은 "행 배열의 배열"이다. 행 하나는 연속이지만 행끼리는 따로 할당된 객체다. 그래서 열 방향 순회는 행마다 다른 객체로 뛴다.
- *캐시 라인*: CPU가 메모리에서 한 번에 가져오는 단위. 이 실험 호스트는 64바이트(`getconf LEVEL1_DCACHE_LINESIZE` = 64)다.
- 열 우선 순회는 라인 하나에서 8바이트만 쓰고 넘어간다. 다음 열에서 그 라인을 다시 쓰려면 행마다 라인 하나씩(행 수 × 64 B)을 캐시에 붙잡아 두어야 한다. 행이 많아 그 묶음이 캐시를 넘으면 다음에 그 라인이 필요할 때 이미 밀려나 있다(행렬 전체 크기만으로 정해지지는 않는다).
- 메모리 계층과 캐시 동작은 architecture 영역([11 메모리 계층](../../architecture/11-memory-hierarchy-and-locality/2-summary.md)·[12 캐시 구성](../../architecture/12-cache-organization/2-summary.md))과 원고 [foundations/memory-management](../../foundations/memory-management/README.md) "행렬 순회 방향" 항목, 페이지 단위 번역 캐시는 [os/10-paging-and-tlb](../../os/10-paging-and-tlb/2-summary.md)에 있다.

### 4. 행렬곱과 루프 순서

```text
  C = A × B          c_ij = Σ_k a_ik · b_kj      (n×n이면 곱셈 n³번)

  ijk 순서 (k가 안쪽)                          ikj 순서 (j가 안쪽)
  for i: for j: for k:                         for i: for k: (a = A[i][k])  for j:
     s += A[i][k] * B[k][j]                        C[i][j] += a * B[k][j]
           ─────→     ↓ B를 열 방향으로 읽음              ─────→ B·C 모두 행 방향
```

- 덧셈·곱셈 횟수는 같다(n³). 다른 것은 **B를 읽는 방향** 하나다.
- ikj 순서에서 원소 `C[i][j]`에 더해지는 순서는 k = 0, 1, …, n−1로 ijk와 같다. 그래서 결과가 비트 단위로 같다(아래 실험의 최대 차이 0). 덧셈 순서를 바꾸면 부동소수 결과가 달라질 수 있다([15-numerical-stability](../15-numerical-stability/2-summary.md)).

#### 실험: 순회 방향과 루프 순서

- 코드 핵심(`LinAlg.java`):

```java
static double sumRow(double[] a, int n) { double s = 0; for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) s += a[i * n + j]; return s; }
static double sumCol(double[] a, int n) { double s = 0; for (int j = 0; j < n; j++) for (int i = 0; i < n; i++) s += a[i * n + j]; return s; }

static void mulIKJ(double[] A, double[] B, double[] C, int n) {
    Arrays.fill(C, 0);
    for (int i = 0; i < n; i++) for (int k = 0; k < n; k++) { double a = A[i*n+k]; for (int j = 0; j < n; j++) C[i*n+j] += a * B[k*n+j]; }
}
```

(실험, OpenJDK 21.0.12 temurin, Docker `--cpus=2`, 호스트 L2 14 MiB·L3 30 MiB, 2026-10-07 — 순회는 5회 중 최소, 행렬곱은 3회 중 최소. 첫 실행 출력, 4회 실행 범위는 아래 관찰)

```text
== 1. 순회 방향 (double, 평평한 배열 a[i*n+j], 5회 중 최소 ms)
n=  512 (   2 MB)  행 우선     1.68 ms   열 우선     2.71 ms   비율 1.6x
n= 2048 (  33 MB)  행 우선     9.15 ms   열 우선    63.29 ms   비율 6.9x
n= 4096 ( 134 MB)  행 우선    34.82 ms   열 우선   330.64 ms   비율 9.5x
== 2. 행렬곱 루프 순서 (n=1024, 3회 중 최소 ms)
ijk  13769.3 ms   ikj   1788.1 ms   비율 7.7x   두 결과 최대 차이 0.000e+00
```

- 관찰 1: 행렬이 캐시에 들어가는 크기(2 MB)에서는 1.5~1.8배 차이다. 캐시보다 훨씬 큰 134 MB에서는 5회(집필 4회 + 사실 점검 재실행 1회) 모두 9.3~10.8배다. 커리큘럼 ⚠ 칸의 "10배"가 이 구간이다.
- 관찰 2: n = 2048(33 MB)은 실행마다 1.9~7.1배로 흔들렸다(사실 점검 재실행은 행 우선 29.53 ms·열 우선 56.29 ms로 1.9배). L3(30 MiB) 경계 근처라 다른 프로세스의 캐시 사용에 민감한 것으로 본다(해석).
- 관찰 3: 행렬곱은 루프 순서만 바꿔 5회 모두 7.7~8.1배 빨라졌다(사실 점검 재실행 ijk 13,052.6 ms·ikj 1,641.8 ms, 8.0배). 결과는 비트 단위로 같다.
- 이 수치는 2코어 제한 컨테이너의 값이다. 비율은 CPU 캐시 크기·하드웨어 프리페처에 따라 달라진다.

### 5. 최근접 탐색 — 무차별과 근사(ANN)

```text
  질의 1건 = N개 벡터 × d차원 곱셈 = N·d 번          (정확한 top-k, 재현율 100%)

  N = 10만, d = 128  →  1,280만 번
  N = 40만, d = 128  →  5,120만 번      ← 데이터가 4배면 시간도 대략 4배
```

- *최근접 탐색(nearest neighbor)*: 질의와 가장 비슷한 벡터 k개를 찾는 것.
- *무차별 탐색(brute force)*: 모든 벡터와 점수를 계산한다. 정확하지만 비용이 N에 비례한다.
- *ANN(approximate nearest neighbor)*: 일부만 보고 "거의" 최근접을 찾는 인덱스. HNSW(근접 그래프를 따라 이동)·IVFFlat(군집으로 나눠 가까운 군집만 탐색)이 대표다.
  - pgvector README: 기본은 정확한 최근접 탐색(완벽한 재현율)이다. 근사 인덱스를 추가하면 "재현율 일부를 속도와 맞바꾸고", 인덱스 추가 뒤 질의 결과가 달라질 수 있다.
  - *재현율(recall)*: 진짜 top-k 중 결과에 들어온 비율.
- 저차원 공간 인덱스(KD 트리 등)가 수십 차원 이상에서 무너지는 이유(차원의 저주)는 [data-structure/25-spatial-index](../../data-structure/25-spatial-index/2-summary.md)에 있다.
- 이 노트는 ANN 인덱스의 **원리만** 다룬다. 제품·파라미터 선택은 정하지 않는다(결정 보류).

#### 실험: 무차별 최근접 1건의 시간

- 길이 1로 정규화한 `float` 벡터를 평평한 배열에 두고, 질의마다 전부 내적을 계산한다(코드는 `LinAlg.java` 4절).

(실험, OpenJDK 21.0.12 temurin, Docker `--cpus=2`, 2026-10-07 — 5회 중 최소. 첫 실행 출력, 4회 실행 범위는 아래)

```text
N=  10000 d=128     9.60 ms/질의 (곱셈 1백만 회)  최근접 id=6394
N= 100000 d=128    33.62 ms/질의 (곱셈 12백만 회)  최근접 id=50986
N= 400000 d=128   128.23 ms/질의 (곱셈 51백만 회)  최근접 id=352764
```

- 출력의 "곱셈 N백만 회"는 코드가 `N·d / 1_000_000`을 정수 나눗셈으로 버린 값이다. 정확히는 128만·1,280만·5,120만 회다.

- 4회 범위: N=10만 14.3~35.3 ms, N=40만 60.8~147.0 ms. 같은 입력이라 최근접 id는 4회 모두 같다.
- 관찰: N을 4배로 늘리면 시간이 실행별로 약 3.6~5.0배 늘었다. 비용이 N·d에 비례한다는 식과 맞는다(편차는 공유 호스트의 잡음 — 해석).

## 쓰이는 자료구조·알고리즘

- **연속 배열(평평한 배열)** — 행렬을 `a[i*n + j]` 하나로 두면 행 순회가 연속 접근이다. [data-structure/01-dynamic-array](../../data-structure/01-dynamic-array/2-summary.md)(커리큘럼 03 — 연속 메모리의 캐시 이점).
- **행렬곱·행렬 거듭제곱** — 점화식을 행렬로 쓰고 빠른 거듭제곱으로 행렬 곱셈 O(log n)번에 푼다. 행렬 크기 d가 고정이면 O(log n), d×d 행렬을 보통 방식으로 곱하면 O(d³ log n)이다. [algorithm/24-divide-conquer](../../algorithm/24-divide-conquer/2-summary.md).
- **인접 행렬** — 그래프를 n×n 행렬로 둔다. [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)(커리큘럼 11).
- **top-k = 힙** — 점수 N개 중 상위 k개를 크기 k 최소 힙으로 고른다. [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)(커리큘럼 10).
- **공간 인덱스·근사 최근접(ANN)** — KD 트리·R-tree는 저차원, 고차원은 HNSW·IVF 같은 근사. [data-structure/25-spatial-index](../../data-structure/25-spatial-index/2-summary.md)(커리큘럼 39).
- **역색인** — 단어 수 벡터(희소 벡터)의 내적을 문서 목록으로 빠르게 계산한다. [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)(커리큘럼 24).

## 적용 — 풀어나가는 법

### 1. 유사도 검색 순위가 이상할 때

1. **증상**: 질의와 무관한 몇 개(긴 문서·인기 상품)가 거의 모든 질의의 상위에 뜬다.
2. **수식으로 어림**: 점수 = `|q|·|v|·cos θ`. 상위 결과의 `|v|`가 전체 평균보다 훨씬 크면 노름이 순위를 만들고 있다.
3. **코드로 확인**: 저장된 벡터 노름 분포를 본다. 전부 1 근처면 정규화돼 있다.
4. **고친다**: 저장할 때 정규화하고, 모델이 전제한 거리(코사인·내적·L2)와 인덱스 연산자를 맞춘다.

```java
/** 저장 직전에 길이 1로. 0벡터는 방향이 없으니 거부한다(코사인 분모 0). */
static float[] normalize(float[] v) {
    double s = 0;
    for (float x : v) s += (double) x * x;
    if (s == 0) throw new IllegalArgumentException("zero vector");
    double inv = 1 / Math.sqrt(s);   // double로 둔다: 아주 작은 벡터면 float 변환 시 Infinity
    float[] u = new float[v.length];
    for (int i = 0; i < v.length; i++) u[i] = (float) (v[i] * inv);
    return u;
}

/** 정규화된 벡터끼리는 내적 = 코사인. 상위 k개를 크기 k 최소 힙으로 고른다. */
static int[] topK(float[][] db, float[] q, int k) {
    PriorityQueue<double[]> heap = new PriorityQueue<>(Comparator.comparingDouble(e -> e[0]));
    for (int i = 0; i < db.length; i++) {
        double s = 0;
        for (int j = 0; j < q.length; j++) s += db[i][j] * q[j];
        heap.offer(new double[]{s, i});
        if (heap.size() > k) heap.poll();          // 가장 낮은 점수를 버린다
    }
    return heap.stream().sorted((a, b) -> Double.compare(b[0], a[0])).mapToInt(e -> (int) e[1]).toArray();
}
```

```sql
-- pgvector: 노름 분포 확인(vector_norm은 pgvector 함수). 정규화돼 있으면 min·max가 1 근처
SELECT min(vector_norm(embedding)), avg(vector_norm(embedding)), max(vector_norm(embedding)) FROM items;
-- 정규화는 l2_normalize(vector) (pgvector README 함수 표)
```

### 2. 행렬 계산이 느릴 때

1. **증상**: 데이터 크기를 2배로 했는데 시간이 4배보다 훨씬 더 늘거나, 같은 연산량의 다른 구현보다 수 배 느리다.
2. **어림**: 안쪽 루프가 메모리를 몇 바이트 간격으로 읽는지 본다. 간격 = 원소 크기면 연속, 간격 = 행 길이 × 원소 크기면 열 방향 점프다.
3. **확인**: 루프 두 개를 바꿔(ijk → ikj) 시간을 잰다. JMH로 정밀하게 재는 법은 [reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md).
4. **고친다**: 안쪽 루프가 연속 메모리를 따라가게 순서를 바꾼다. `double[][]` 대신 평평한 `double[]`을 쓴다. 큰 행렬곱은 직접 짜기보다 검증된 수치 라이브러리(BLAS 계열)에 맡긴다.

### 3. 무차별 탐색의 비용 어림

- 질의 1건 비용 ≈ N·d 곱셈. 이 실험 환경에서 N = 40만, d = 128이 1건에 약 60~150 ms였다.
- 목표 QPS × 질의당 시간 = 필요한 CPU 초. 이것이 코어 수를 넘으면 무차별은 불가능하다. 그때 ANN을 검토한다(재현율 측정을 함께).

## 장애 시나리오와 대처

### 1. 정규화 누락 → 유사도 검색 순위 왜곡 (⚠)

- 현상: 어떤 질의를 넣어도 같은 긴 문서 몇 개가 상위를 차지한다.
- 보이는 형태: 클릭률·만족도 하락, "검색 결과가 다 비슷하다"는 사용자 신고. 오류 로그는 없다. 상위 결과의 벡터 노름이 평균보다 크다(위 실험: 13배).
- 원인: 정규화하지 않은 벡터에 내적(`<#>`)을 썼다. 점수에 문서 길이가 곱해진다.
- 대처: 저장 시 정규화하거나 코사인 거리(`<=>`)를 쓴다. 노름 분포를 지표로 남긴다. 순위 회귀 테스트(고정 질의의 기대 top-k)를 둔다.

### 2. 임베딩 모델 교체 중 두 모델의 벡터가 섞임

- 현상: 모델 교체 배포 뒤 일부 질의의 결과가 엉뚱하다.
- 보이는 형태: 차원이 같으면 오류 없이 낮은 점수·무관한 결과만 나온다. 새 모델과 옛 모델 벡터의 코사인이 무작위 쌍 수준으로 낮다.
- 원인: 따로 학습한 두 모델은 보통 서로 다른 좌표계다. 같은 차원이라도 i번째 축의 뜻이 다르다(같은 공간에 맞추도록 학습한 경우 — 예: Sentence Transformers의 교사·학생 증류 — 는 예외라 모델 조합마다 확인한다). 내적은 같은 좌표계 안에서만 의미가 있다.
- 대처: 벡터에 모델 버전을 함께 저장하고, 질의와 같은 버전끼리만 비교한다. 전체 재색인 뒤 한 번에 전환한다.

### 3. 열 우선 순회 → 캐시 미스로 10배 느림 (⚠)

- 현상: 정산·추천 배치가 데이터가 커지자 예상보다 훨씬 느려졌다.
- 보이는 형태: 배치 시간이 데이터 크기 대비 비선형으로 늘어난다. 프로파일러에서 CPU는 바쁜데 IPC(사이클당 명령 수)가 낮다. `perf stat -e cache-misses`의 미스가 크다.
- 원인: 안쪽 루프가 행렬을 열 방향(행 길이만큼 점프)으로 읽는다. 위 실험의 134 MB 행렬에서 9.3~10.8배 차이였다.
- 대처: 루프 순서를 바꾸거나 저장 배치를 바꾼다(열 단위로 자주 읽으면 전치해서 저장). 프로파일링 방법은 [reliability/36-profiling](../../reliability/36-profiling/2-summary.md).

### 4. 데이터 증가로 무차별 탐색 지연이 선형 증가 → ANN 도입 후 결과가 바뀜

- 현상: 벡터 수가 늘면서 검색 p99가 계속 오른다. ANN 인덱스를 붙이자 빨라졌지만 "있어야 할 결과가 빠진다"는 신고가 온다.
- 보이는 형태: 질의 지연이 N에 비례해 증가(위 실험: N 4배 → 약 3.6~5.0배). 인덱스 추가 뒤 같은 질의의 결과 집합이 달라진다(pgvector README가 명시).
- 원인: 무차별은 O(N·d)다. ANN은 재현율을 속도와 맞바꾼다.
- 대처: 정확 탐색 결과를 기준으로 고정 질의 세트의 재현율을 재고, 인덱스 파라미터를 그 수치로 정한다. 재현율이 계약인 기능(중복 탐지 등)은 후보를 ANN으로 넓게 뽑고 정확 점수로 재정렬한다.

## 핵심 문장

- 내적은 `|x|·|y|·cos θ`다. 길이가 다른 벡터를 내적으로 비교하면 비슷함(방향)에 길이가 섞여, 길이가 순위를 좌우할 수 있다.
- 순위를 비트는 것은 문서 쪽 노름이다. 질의 노름은 모든 점수에 같은 배율이라 순위를 바꾸지 않는다.
- 모든 벡터를 길이 1로 저장하면 내적·코사인·L2 거리가 같은 순위를 낸다.
- 행렬은 메모리에 한 방향으로 놓인다. 그 방향을 거슬러 순회하면 연산량이 같아도 캐시 미스 때문에 수 배~10배 느려진다.
- 무차별 최근접은 정확하지만 O(N·d)다. ANN은 재현율을 속도와 맞바꾸므로 재현율을 재서 쓴다.

## 관련 주제·근거

- 선행·같은 영역
  - [06-recurrences-and-asymptotics](../06-recurrences-and-asymptotics/2-summary.md) — 비용을 N·d, n³로 세는 법
  - [15-numerical-stability](../15-numerical-stability/2-summary.md) — 덧셈 순서와 부동소수 오차(내적도 합이다)
  - [14-information-theory-basics](../14-information-theory-basics/2-summary.md) — 해밍 거리(이진 벡터의 거리)
- 다른 영역
  - [data-structure/25-spatial-index](../../data-structure/25-spatial-index/2-summary.md) — 차원의 저주, LSH·HNSW로 가는 이유
  - [data-structure/07-heap](../../data-structure/07-heap/2-summary.md) — top-k
  - [algorithm/24-divide-conquer](../../algorithm/24-divide-conquer/2-summary.md) — 행렬 거듭제곱
  - [os/10-paging-and-tlb](../../os/10-paging-and-tlb/2-summary.md) — 큰 배열 접근과 TLB
  - architecture — [메모리 계층](../../architecture/11-memory-hierarchy-and-locality/2-summary.md)·[캐시](../../architecture/12-cache-organization/2-summary.md), 원고 [foundations/memory-management](../../foundations/memory-management/README.md)
  - [reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md) · [reliability/36-profiling](../../reliability/36-profiling/2-summary.md)
- 근거
  - MIT OCW 18.06 Linear Algebra(Spring 2010, Gilbert Strang) <https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/> — 벡터·내적·행렬곱. 교재 『Introduction to Linear Algebra』의 장 번호는 확인하지 못했다 `[?]`
  - pgvector README — 거리 연산자 `<->`·`<#>`·`<=>`, 정규화된 벡터는 내적 권장, 기본 정확 탐색과 근사 인덱스(HNSW·IVFFlat)의 재현율 트레이드오프 <https://github.com/pgvector/pgvector>
  - Sentence Transformers, Multilingual Models — 교사 모델의 벡터 공간을 학생 모델이 따라 하도록 학습(서로 다른 모델이 같은 공간을 쓰는 예) <https://sbert.net/examples/sentence_transformer/training/multilingual/README.html>
  - Java SE 21 `Float.MIN_VALUE`·JLS §5.1.3(double → float 축소 변환에서 너무 큰 값은 무한대) — `normalize`의 역수를 double로 두는 이유. 확인 실험 `Norm.java`: 옛 코드 `[Float.MIN_VALUE, 0]` → `[Infinity, NaN]`, 고친 코드 → `[1.0, 0.0]`(OpenJDK 21 temurin, 2026-10-07)
- 실험 목록
  - `LinAlg.java` — (1) 행 우선 vs 열 우선 합(n = 512·2048·4096), (2) 행렬곱 ijk vs ikj(n = 1024), (3) 내적 vs 코사인 순위(3차원 예 + 무작위 20,000×64, 시드 7), (4) 무차별 최근접(N = 1만·10만·40만, d = 128). OpenJDK 21.0.12 temurin, Docker `--cpus=2 --network none`, `-Xmx1g`, 2026-10-07, 4회 실행 + 사실 점검 재실행 1회(3절 출력·최근접 id는 같았고, 시간은 위 범위 안 — n = 2048 순회 비율만 1.9배로 범위를 넓혔다). 호스트 캐시 라인 64 B, L2 14 MiB, L3 30 MiB(`lscpu`).
