# architecture/21-simd-and-gpu — 데이터 병렬의 모양: 한 명령으로 여러 값을, 그리고 분기가 비싼 이유 — 정리 (힌트)

## 해결하는 문제

같은 연산을 많은 값에 되풀이하는 일이 있다. 배열 더하기, 합계, 필터, 행렬곱, 이미지 처리, 임베딩 내적이 그렇다. 값마다 명령 하나씩 쓰면 명령 처리(가져오기·해석·스케줄)가 값 수만큼 든다.

```text
  스칼라:  a[0]=b[0]+c[0]   a[1]=b[1]+c[1]   ...   a[7]=b[7]+c[7]     덧셈 명령 8개 (+ 읽기·쓰기도 8번씩)
  SIMD:    a[0..7] = b[0..7] + c[0..7]                                  덧셈 명령 1개 (256비트 = int 8개, 읽기·쓰기도 8칸씩 한 번)
```

- 이것이 없으면 계산 위주 루프가 하드웨어가 낼 수 있는 속도의 일부만 쓴다.

쉬운 예: 도장 찍기.
- 서류 8장에 한 장씩 도장을 찍는다(스칼라).
- 도장 8개를 붙인 막대로 한 번에 8장을 찍는다(SIMD). 단, 서류가 나란히 놓여 있어야 하고, 8장 모두 같은 도장이어야 한다.
- 어떤 서류는 "승인", 어떤 서류는 "반려"면? 막대를 두 번 찍고, 각 서류에 맞는 쪽만 남긴다. 두 번 찍는 비용은 그대로 낸다(분기와 마스크).

똑같은 구조다.\
CPU의 SIMD(SSE·AVX)와 GPU의 워프(32개 스레드가 한 명령을 함께 실행)가 이 막대다.

실무 예:
- DB의 컬럼 저장 엔진이 "행 묶음 단위 벡터화 실행"으로 집계를 몇 배 빠르게 한다([database/54](../../database/54-query-execution-models/2-summary.md)).
- 같은 Java 코드가 JIT 옵션 하나로 4~5배 빨라지거나 느려진다.
- 분기가 많은 규칙 엔진을 GPU로 옮겼더니 기대만큼 빨라지지 않는다.

## 동작·원리

### 1. SIMD 레지스터 — 넓은 칸 하나에 값 여러 개

```text
  xmm (128비트, SSE)   | int | int | int | int |                       int 4개
  ymm (256비트, AVX2)  | int | int | int | int | int | int | int | int | int 8개 / float 8개 / double 4개
  zmm (512비트, AVX-512)                                               int 16개 (이 CPU는 지원 안 함)

  vpaddd ymm0, ymm1, ymm2   →  8칸을 한 명령으로 각각 더한다 (칸끼리만, 칸 사이는 섞지 않음)
```

- *SIMD(Single Instruction, Multiple Data)*: 명령 하나가 여러 데이터 칸에 같은 연산을 하는 방식.
  - *레인(lane)*: 벡터 레지스터 안의 칸 하나.
- 이 호스트(i7-13700HX)의 `lscpu` 플래그: `sse4_2 avx avx2 fma avx_vnni`가 있고 `avx512f`는 없다. JDK 21도 `UseAVX = 2`, `MaxVectorSize = 32`(바이트 = 256비트)로 잡았다(`-XX:+PrintFlagsFinal`).
- ARM64는 NEON(128비트)·SVE를 쓴다. 칸 수가 달라도 생각은 같다.

### 2. 자동 벡터화 — 컴파일러가 루프를 바꿔 준다

컴파일러는 루프가 아래 조건을 만족하면 SIMD 명령으로 바꾼다(GCC 문서의 `-ftree-vectorize` 계열, 개념은 CS:APP 5장 `[?]`·P&H 6장 `[?]`).

```text
  ✔ 연속 메모리를 차례로 읽는다              a[i], b[i]
  ✔ 반복끼리 의존이 없다(또는 축약 가능)       a[i] = b[i] + c[i]
  ✔ 포인터가 겹치지 않음을 안다(restrict 등)
  ✔ 분기는 "양쪽 계산 후 고르기"로 바꿀 수 있다
  ✘ 포인터 따라가기 (p = p->next)
  ✘ 부동소수 덧셈 순서를 바꿔야 하는 축약 — 언어가 순서 변경을 금지하면 안 된다
```

- GCC 13.3에서 `-O2`도 루프 벡터화를 켠다. 단 비용 모형이 `very-cheap`이라, 남는 반복 처리(에필로그)가 필요 없는 루프만 바꾼다(`gcc -Q -O2 --help=optimizers` → `-fvect-cost-model=very-cheap`, `-O3`는 `dynamic`; GCC 13.3 문서 Optimize-Options).
- 그래서 반복 수를 컴파일 때 모르는 루프는 `-O2`에서 안 바뀌고 `-O3`에서 바뀌었다(아래 실험의 `-fopt-info-vec`).

#### 실험: 같은 루프를 네 단계로 컴파일 (`simd.c`)

```c
void add(int *restrict a, const int *restrict b, const int *restrict c, int n) {
    for (int i = 0; i < n; i++) a[i] = b[i] + c[i];
}
void branchy(int *restrict a, const int *restrict b, int n) {
    for (int i = 0; i < n; i++) { if (b[i] > 0) a[i] = b[i] * 3; else a[i] = -b[i]; }   // 실험 입력은 -100~99라 넘침 없음
}
float fsum(const float *x, int n) { float s = 0; for (int i = 0; i < n; i++) s += x[i]; return s; }
long  isum(const int *x, int n)   { long s = 0;  for (int i = 0; i < n; i++) s += x[i]; return s; }
```

환경: i7-13700HX, gcc 13.3, `taskset -c 4`(P코어), 배열 4,096개(16KiB, L1d 48KiB 안)를 20만 번 반복, 큰 배열은 int 16M개(배열당 64MiB — `add`는 `a`·`b`·`c` 세 개라 합 192MiB, L3 30MiB 밖). 원소당 ns. 3회 중 1·2회(3회째는 호스트 부하로 값이 대체로 약 2배 느려졌다 — 아래 괄호).

```text
                    -O0          -O2 -fno-tree-vectorize   -O3          -O3 -march=native   -O3 -march=native -ffast-math
  add (L1)          6.3~9.5      1.06~1.09                 0.31~0.55    0.21~0.28           0.21
  branchy (L1)      6.6~7.7      2.16~2.19                 0.67~0.68    0.35~0.36           0.35~0.37
  fsum (L1)         9.4~12.4     2.15~2.33                 2.15~2.25    2.16~2.17           0.24~0.25
  isum (L1)         8.0~8.9      1.10~1.25                 0.56~0.58    0.40~0.43           0.45
  add (64MiB)       4.9~6.1      1.77~2.03                 1.52~1.65    1.53~1.56           1.53~1.62
  fsum 결과         2.919377e+05 (나머지 판)                                                 2.919381e+05
  (3회째)           add 5.4 · O2nv 1.10 · O3n 0.47 · fsum O3n 4.29 → O3nf 0.50  ← fsum 비율(약 9배)은 같음, add 비율은 약 2.3배로 작아짐
```

- 관찰 1(add, L1 안): 벡터화 없이 1.06~1.09 → AVX2(`-march=native`) 0.21~0.28ns. 약 4~5배다(점검 재실행 1회: 1.29 → 0.23ns, 약 5.7배).
- 관찰 2(add, 64MiB): 1.77~2.03 → 1.53~1.56ns. 약 1.1~1.3배뿐이다. 해석: 메모리 쪽(대역폭·지연)이 병목이면 계산을 8배 빨리 해도 기다리는 시간은 같다([11번](../11-memory-hierarchy-and-locality/2-summary.md)). 시간만 쟀으므로(perf 불가) 대역폭·지연·저장 정체 가운데 무엇인지는 가르지 못했다.
- 관찰 3(fsum): `-O3 -march=native`에서도 2.16~2.17ns로 벡터화 전과 같았다. `-ffast-math`를 주자 0.24~0.25ns(약 9배)가 됐고 **결과가 바뀌었다**(2.919377e+05 → 2.919381e+05).
- 관찰 4(isum): 정수 합은 순서를 바꿔도 결과가 같아 `-O3`에서 바로 빨라졌다.
- `-O0`은 값을 매번 스택에 쓰고 읽는 코드라 따로 느리다. 비교의 기준선은 `-O2 -fno-tree-vectorize`다.

#### 기계어로 확인 (`objdump -d`)

```text
  add, -O2 -fno-tree-vectorize        add, -O3 -march=native
   mov    (%rdx,%rax,1),%ecx           vmovdqu (%rsi,%rax,1),%ymm1
   add    (%rsi,%rax,1),%ecx           vpaddd  (%rdx,%rax,1),%ymm1,%ymm0     ← int 8개 한 번에
   mov    %ecx,(%rdi,%rax,1)           vmovdqu %ymm0,(%rdi,%rax,1)
   add    $0x4,%rax                    (-O3만: movdqu/paddd xmm — SSE2 128비트, int 4개)

  fsum, -O3 -march=native             fsum, + -ffast-math
   vaddss (%rax),%xmm0,%xmm0           vaddps (%rax),%ymm1,%ymm1             ← float 8개 한 번에
   vaddss -0x1c(%rax),%xmm0,%xmm0      ... 끝에서 vextractf128·vaddps로 8칸을 합침
   vaddss -0x18(%rax),%xmm0,%xmm0
   ... (8번 연속, 한 칸씩 차례로)
```

- `fsum`은 `-fopt-info-vec`이 fsum 루프 위치(`simd.c:16:36`)에 "loop vectorized using 32 byte vectors"라고 보고했다. 그런데 기계어는 `vaddss`(메모리에서 32비트 값 하나를 읽어 1칸 더함) 8개가 **순서대로** 한 레지스터에 쌓인다. 루프는 8개 단위로 돌지만, 읽기도 덧셈도 한 칸씩이고 덧셈 순서는 원래대로다(순서 보존 축약 — 해석).
  - 해석: 8칸에 따로 더하고 마지막에 합치려면 덧셈을 재결합해야 한다. GCC 13.3 문서는 `-fassociative-math`(`-ffast-math`가 켬)가 "계산 결과를 바꿀 수 있어 ISO C·C++ 표준을 어긴다"고 적는다. 그래서 이 옵션 없이는 순서를 지킨다.
  - 흔한 오해: "`-fopt-info-vec`에 vectorized라고 나오면 빨라진다." — 이 루프는 보고는 vectorized였지만 시간은 그대로였다. 기계어(`vaddss` 대 `vaddps`)와 시간으로 확인한다.
- 부동소수 합이 순서에 따라 달라지는 이유와 병렬 합의 결과 차이는 [math/15-numerical-stability](../../math/15-numerical-stability/2-summary.md)에 있다.

### 3. Java — C2 JIT의 SuperWord

#### 실험: 같은 루프, `-XX:+UseSuperWord`(기본) vs `-XX:-UseSuperWord` (`SimdJava.java`)

```java
static void add(int[] a, int[] b, int[] c) { for (int i = 0; i < a.length; i++) a[i] = b[i] + c[i]; }
static float fsum(float[] x) { float s = 0; for (int i = 0; i < x.length; i++) s += x[i]; return s; }
static long isum(int[] x) { long s = 0; for (int i = 0; i < x.length; i++) s += x[i]; return s; }
```

환경: Docker `eclipse-temurin:21-jdk`(21.0.12) `--cpuset-cpus=4 --network none`, 배열 4,096개 × 10만 번, 워밍업 2라운드 뒤 3라운드째, JVM 2회씩.

```text
                     add          fsum         isum        (ns/elem)
  +UseSuperWord      0.369~0.373  2.148~2.181  0.295~0.307
  -UseSuperWord      1.666~1.859  2.192~2.411  1.095~1.131
```

- 관찰: `add`는 약 4.5~5배, `isum`은 약 3.6~3.8배 차이. `fsum`은 거의 같다. 점검 재실행(각 1회, 3라운드째)도 `add` 0.345 → 1.683(약 4.9배), `isum` 0.279 → 1.149(약 4.1배), `fsum` 2.183 → 2.177로 같은 모양이었다.
- 해석: JLS §15.7.3은 Java 구현이 결합법칙 같은 대수 항등식으로 식을 바꿔 쓰지 못하게 한다(값이 같다고 증명되는 경우만 예외). 그래서 JIT은 `float` 합의 순서를 바꾸지 않는다([math/15](../../math/15-numerical-stability/2-summary.md)). C의 `-ffast-math` 같은 탈출구가 없다.
  - 순서를 바꾼 합이 필요하면 코드에서 직접 칸을 나눠 더하거나(결과가 달라짐을 받아들이고), `jdk.incubator.vector`(Vector API, 인큐베이터 모듈) 같은 명시적 SIMD를 쓴다.
- 기계어 확인(`-XX:+PrintAssembly`)은 hsdis 플러그인이 있어야 해 이번에는 시간 비교로 대신했다.

### 4. 분기는 마스크가 된다 — SIMD와 GPU 워프의 공통점

```text
  if (x > 0) A(x) else B(x)   를 8칸에 한 번에

  레인:       0   1   2   3   4   5   6   7
  x>0 ?      [1] [0] [1] [1] [0] [0] [1] [0]   ← 비교 결과 = 마스크 (vpcmpgtd)
  A 계산:     ✓   ✓   ✓   ✓   ✓   ✓   ✓   ✓    ← 8칸 모두 계산
  B 계산:     ✓   ✓   ✓   ✓   ✓   ✓   ✓   ✓    ← 8칸 모두 계산
  고르기:     A   B   A   A   B   B   A   B    ← 마스크로 칸마다 하나를 남김 (vpblendvb)
  비용 = A + B  (데이터가 어떻든)
```

- `branchy`의 `-O3 -march=native` 기계어가 이 모양이다: `vpcmpgtd`로 마스크, 양쪽 값을 다 계산하고 `vpblendvb`로 고른다.
  - *if-conversion*: 분기를 "양쪽 계산 + 선택"으로 바꾸는 변환. 분기 예측 실패가 없어지는 대신 양쪽 비용을 낸다. 스칼라 쪽의 브랜치리스 기법은 [18-pipelining-and-branch-prediction](../18-pipelining-and-branch-prediction/2-summary.md)에 있다.
- GPU도 같다. CUDA 프로그래밍 가이드(v13.4.2) §1.2.2.2 "Warps and SIMT": 스레드 블록 안의 스레드는 **32개씩 워프**로 묶이고, 워프의 스레드는 같은 명령을 동시에 실행한다. 일부 스레드만 분기를 따르면 나머지는 **마스크로 꺼진 채** 기다린다. 이를 warp divergence라 하며, 워프의 스레드가 같은 경로를 따를 때 GPU 활용도가 가장 높다.
  - *워프(warp)*: NVIDIA GPU에서 한 명령을 함께 실행하는 스레드 32개 묶음.
  - *SIMT(Single Instruction, Multiple Threads)*: 스레드마다 코드를 따로 쓰는 것처럼 보이지만, 하드웨어는 워프 단위로 한 명령씩 실행하는 모델.
- GPU 메모리도 "이웃 스레드가 이웃 주소"일 때 효율이 좋다. 같은 워프의 요청을 32바이트 트랜잭션으로 묶는다(coalescing). 연속 4바이트 접근이고 시작 주소가 32바이트 경계에 맞으면 128바이트를 트랜잭션 4개로 가져와 100% 쓴다(경계에서 어긋나면 128바이트가 세그먼트 5개에 걸쳐 5개가 든다). 32바이트 이상씩 떨어진 접근이면 1,024바이트를 가져와 12.5%만 쓴다(가이드 §2.3.4.1 "Coalesced Global Memory Access").

#### 실험: 양쪽 갈래가 모두 무거운 분기 (`diverge.c`)

```c
int x = b[i];
if (x > 0) { for (int k = 0; k < 8; k++) x = x * 3 + 7; }      // 갈래 A
else       { for (int k = 0; k < 8; k++) x = x * 5 - 11; }     // 갈래 B
a[i] = x;
```

입력 두 가지: 전부 양수(all-same, 모두 A) / 부호 무작위(mixed, 반반). 값은 ±1~100이라 8번 곱해도(최대 약 3,900만) `int` 범위 안이다. 범위를 넘는 입력이면 C에서 부호 있는 정수 넘침은 정의되지 않은 동작이니 정의역을 제한해야 한다. `taskset -c 6`, 4,096개 × 10만 번, 3회.

```text
                                    all-same          mixed
  스칼라 (-O2 -fno-tree-vectorize)   7.80~7.94 ns      20.31~21.49 ns    ← 분기 예측 실패
  벡터 (-O3 -march=native)          2.68~2.95 ns       2.73~2.79 ns     ← 데이터와 무관
```

- 관찰 1: 벡터 판은 입력이 어떻든 같은 시간이다. 마스크로 A와 B를 **둘 다** 계산하기 때문이다(기계어에 `vpcmpgtd`·`vpblendvb`).
- 관찰 2: 그래도 8칸 병렬이라 이 경우는 스칼라보다 빠르다. 모두 같은 갈래(all-same)인데도 벡터는 B까지 계산해 일을 2배 하고 있다. 갈래가 4개, 8개로 늘면 그만큼 곱해진다.
- 관찰 3: 스칼라는 예측 가능한 입력에서 7.8~7.9ns, 무작위 입력에서 20~21ns. 이 빌드의 기계어에는 `x > 0` 조건 분기(`jle`)가 있고 `cmov`는 없다. 분기 예측 실패 비용과 부합한다(해석 — 오예측 횟수는 perf를 못 써 재지 못했다, 18번).
- 해석(GPU로 옮기면): 워프 32개 스레드가 갈래를 나눠 타면 그 워프는 갈래들을 차례로 실행한다. 워프 안 스레드가 모두 같은 갈래를 타면 다른 갈래는 실행하지 않는다 — 언제나 양쪽을 계산한 이 CPU 벡터 판과 다른 점이다. 이 GPU 실험은 이 호스트에서 NVIDIA 드라이버가 로드되지 않아(`nvidia-smi` 실패) 돌리지 못했다. CUDA 가이드의 설명과 CPU SIMD 실험으로 대신한다.

## 쓰이는 자료구조·알고리즘

- **SoA(Structure of Arrays) vs AoS** — 같은 필드를 연속 배열로 두면(SoA) 벡터 load 한 번에 칸이 찬다. 객체 배열(AoS)은 필드가 흩어진다. 컬럼 저장이 SoA다([database/37](../../database/37-row-vs-column-storage/2-summary.md)).
- **벡터화 루프 / 축약(reduction)** — 합·최대·내적은 칸별 부분합 → 마지막에 합치기. 정수는 순서 무관, 부동소수는 결과가 바뀐다([math/15](../../math/15-numerical-stability/2-summary.md)).
- **비트셋·비트맵** — 64비트 워드 하나가 원소 64개. 그 자체가 SIMD 같은 데이터 병렬이고, AVX로 더 넓게 처리한다. [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)
- **내적·행렬곱** — 임베딩 유사도, 신경망. 루프 순서와 연속 접근이 벡터화를 정한다. [math/13-linear-algebra-essentials](../../math/13-linear-algebra-essentials/2-summary.md)
- **문자열 검색·해시** — 여러 바이트를 한 번에 비교하는 SIMD 구현이 있다([algorithm/25-string-matching](../../algorithm/25-string-matching/2-summary.md)).
- **벡터화 실행 엔진** — 행 묶음 단위 처리. [database/54-query-execution-models](../../database/54-query-execution-models/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 이 루프가 SIMD를 쓰나 확인한다

```bash
grep -o -w -E 'sse4_2|avx2|avx512f|fma' /proc/cpuinfo | sort -u     # 어떤 SIMD가 있나
gcc -O3 -march=native -fopt-info-vec-optimized -c x.c                # 벡터화된 루프 보고
gcc -O3 -march=native -fopt-info-vec-missed -c x.c                   # 못 한 이유
objdump -d --no-show-raw-insn x.o | grep -E 'ymm|zmm'                # 넓은 레지스터를 쓰나
#  vaddps/vpaddd = 여러 칸(packed),  vaddss/vaddsd = 한 칸(scalar)
java -XX:+PrintFlagsFinal -version | grep -E 'UseAVX|MaxVectorSize|UseSuperWord'
```

### 2. 벡터화되게 쓰는 법 (Java 21)

```java
// 좋음: 원시 배열, 연속 인덱스, 루프 안 분기·호출 없음
for (int i = 0; i < n; i++) out[i] = a[i] * k + b[i];

// 나쁨: 박싱된 리스트 — 원소가 흩어진 객체라 연속 load가 안 된다
long s = 0; for (Integer v : list) s += v;

// 분기는 값 선택으로 (JIT이 조건 이동·블렌드로 바꾸기 쉬워진다)
for (int i = 0; i < n; i++) out[i] = Math.max(a[i], 0);
```

- 먼저 병목이 계산인지 메모리인지 본다. 64MiB 실험처럼 데이터가 캐시 밖이면 벡터화 이득이 작을 수 있다(메모리 대역폭·지연 쪽이 병목으로 해석).
- 부동소수 합은 Java가 순서를 지키므로 자동 벡터화로 빨라지지 않는다. 정확도·재현성 요구를 먼저 정하고, 순서를 바꿔도 되면 칸을 나눠 더한다.

### 3. GPU로 옮길지 판단할 때

- 데이터 병렬인가(같은 연산 × 수많은 원소) → 예.
- 원소마다 분기 경로가 크게 갈리나 → 갈리면 워프 분기로 효율이 떨어진다. 데이터를 경로별로 먼저 나누거나(정렬·분할), 분기 없는 식으로 바꾼다.
- 이웃 원소가 이웃 메모리에 있나 → 아니면 coalescing이 깨진다.
- 계산량 대비 전송량이 큰가 → GPU 메모리로 옮기는 시간이 계산 이득을 넘으면 CPU SIMD가 낫다 `[?]`(PCIe 대역폭은 [16번](../16-storage-media-workload/2-summary.md) 원고의 PCIe 표 참고).

## 장애 시나리오와 대처

### 1. 분기 많은 코드를 GPU로 → 워프 분기로 느림 (⚠)

- **현상**: 규칙 엔진·파서처럼 원소마다 다른 길을 타는 코드를 GPU로 옮겼는데 이득이 작거나 CPU보다 느리다.
- **보이는 형태**: GPU 사용률 지표는 높은데 처리량이 낮다. 프로파일러(Nsight Compute 등)에서 활성 스레드 비율·워프 실행 효율이 낮게 나온다 `[?]`.
- **원인**: 워프 32개 스레드가 다른 갈래를 타면 갈래마다 차례로 실행하고 나머지는 마스크로 꺼진다(CUDA 가이드 §1.2.2.2). CPU 실험에서도 벡터 판은 입력과 무관하게 양쪽 갈래 비용(2.7~2.9ns)을 냈다.
- **대처**: 같은 경로를 탈 원소끼리 모아(정렬·버킷) 워프 안의 분기를 줄인다. 분기를 산술 선택으로 바꾼다. 경로가 너무 다양하면 CPU에 남긴다.

### 2. 최적화 플래그 차이로 합계가 달라짐

- **현상**: 같은 소스인데 빌드 설정이나 CPU에 따라 집계 결과의 끝자리가 다르다.
- **보이는 형태**: 실험: `fsum`이 `-ffast-math` 유무로 2.919377e+05 ↔ 2.919381e+05. 테스트의 정확 일치 비교가 특정 빌드에서만 실패한다.
- **원인**: 벡터화된 축약은 칸별 부분합을 따로 쌓아 덧셈 순서가 바뀐다. `-ffast-math`·`-fassociative-math`는 이를 허용한다(GCC 13.3 문서: 결과를 바꿀 수 있음).
- **대처**: 돈·재현이 중요한 계산은 `-ffast-math`를 쓰지 않거나 정수·`BigDecimal`로 한다. 테스트는 허용 오차로 비교한다. 정밀 합이 필요하면 Kahan 합([math/15](../../math/15-numerical-stability/2-summary.md)).

### 3. `-march=native`로 빌드한 바이너리가 다른 서버에서 `SIGILL`

- **현상**: 빌드 서버에서는 잘 돌던 프로그램이 일부 운영 서버에서 바로 죽는다.
- **보이는 형태**: `Illegal instruction (core dumped)`, 종료 코드 132(128+4, SIGILL).
- **원인**: `-march=native`는 빌드한 CPU의 명령(예: AVX2, AVX-512)을 쓴다. 그 명령이 없는 CPU에서 실행하면 정의되지 않은 명령이다([os/03](../../os/03-interrupts-traps-faults/2-summary.md)의 #UD → SIGILL).
- **대처**: 배포용은 운영 CPU의 최소 공통 수준으로 빌드한다(예: `-march=x86-64-v3`로 AVX2·FMA까지 — gcc 13.3에서 이 옵션이 `__AVX2__`·`__FMA__`를 정의하는 것을 `gcc -march=x86-64-v3 -dM -E`로 확인). 또는 실행 시 CPU 기능을 검사해 경로를 고르는 라이브러리를 쓴다. JVM은 실행 시 CPU를 보고 JIT이 고른다(`UseAVX`).

### 4. "벡터화했는데 안 빨라짐" — 메모리 병목

- **현상**: SIMD 최적화 뒤 마이크로벤치마크는 4배 빨라졌는데 실제 대용량 처리는 거의 그대로다.
- **보이는 형태**: 실험: L1 안 배열은 1.06 → 0.21~0.28ns, 64MiB 배열은 1.77~2.03 → 1.53~1.56ns.
- **원인**: 데이터가 캐시 밖이면 메모리에서 가져오는 속도(대역폭·지연)가 상한이 되기 쉽다. 계산을 빨리 해도 load를 기다린다(해석 — 실험은 시간만 쟀다).
- **대처**: 먼저 데이터를 줄인다(압축·작은 타입·필요한 컬럼만), 한 번 읽을 때 여러 연산을 몰아 한다(루프 융합), 캐시 크기 단위로 쪼갠다(블로킹, [11번](../11-memory-hierarchy-and-locality/2-summary.md)).

## 핵심 문장

- SIMD는 명령 하나로 레지스터의 여러 칸(AVX2 256비트 = int 8개)에 같은 연산을 한다. GPU 워프는 스레드 32개가 한 명령을 함께 실행한다.
- 컴파일러·JIT은 연속 접근·의존 없음·분기 없음인 루프를 자동 벡터화한다. 이 호스트에서 정수 배열 덧셈이 약 4~5배 빨라졌다.
- 부동소수 합은 순서를 바꿔야 벡터화되므로, C는 재결합을 허용하는 옵션(`-ffast-math`, 또는 `-fassociative-math`를 켜는 `-funsafe-math-optimizations` 등)이 있어야 하고 결과가 바뀔 수 있다. Java는 JLS가 순서 변경을 막아 자동으로 빨라지지 않는다.
- 분기는 마스크가 된다. CPU SIMD의 if-conversion은 갈래를 모두 계산하고 고른다. 워프는 스레드들이 탄 갈래들을 차례로 실행한다(모두 같은 갈래면 그 갈래만). 경로가 갈릴수록 일을 버린다.
- 데이터가 캐시 밖이면 SIMD 이득은 작다. 먼저 병목이 계산인지 메모리인지 본다.

## 관련 주제·근거

- 선행
  - architecture [20-multicore-and-numa](../20-multicore-and-numa/2-summary.md) — 코어 사이 병렬(이 노트는 코어 안 데이터 병렬)
- 연결
  - architecture [09-isa-and-machine-code](../09-isa-and-machine-code/2-summary.md) — 명령어 인코딩, `objdump`
  - architecture [11-memory-hierarchy-and-locality](../11-memory-hierarchy-and-locality/2-summary.md) — 메모리 병목
  - architecture [18-pipelining-and-branch-prediction](../18-pipelining-and-branch-prediction/2-summary.md) — 분기 예측 실패, 브랜치리스
  - math [15-numerical-stability](../../math/15-numerical-stability/2-summary.md) — 덧셈 순서와 결과, JLS §15.7.3 · [13-linear-algebra-essentials](../../math/13-linear-algebra-essentials/2-summary.md) — 내적·행렬곱
  - database [54-query-execution-models](../../database/54-query-execution-models/2-summary.md) · [37-row-vs-column-storage](../../database/37-row-vs-column-storage/2-summary.md) — 벡터화 실행, 컬럼 저장
  - os [03-interrupts-traps-faults](../../os/03-interrupts-traps-faults/2-summary.md) — 정의되지 않은 명령 → SIGILL
  - data-structure [18-bitset](../../data-structure/18-bitset/2-summary.md)
- 교재·문서
  - P&H 『Computer Organization and Design』 6장(병렬 프로세서, SIMD·GPU) `[?]` — 장 번호는 커리큘럼 표기, 이번에 목차를 열지 못했다
  - CS:APP 3판 5장 Optimizing Program Performance(5.9 Enhancing Parallelism 등 — 3판 목차로 절 번호 확인, SIMD 관련 내용 위치는 `[?]`) <https://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf>
  - NVIDIA CUDA Programming Guide v13.4.2 — §1.2.2.2 Warps and SIMT(32스레드 워프, 마스크, warp divergence) <https://docs.nvidia.com/cuda/cuda-programming-guide/01-introduction/programming-model.html>, §2.3 Writing SIMT Kernels — §2.3.4.1 Coalesced Global Memory Access(32바이트 트랜잭션·12.5%) <https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/writing-cuda-kernels.html>
  - GCC 13.3 Optimize-Options — `-ftree-loop-vectorize`(-O2에서 켜짐), `-fvect-cost-model`(very-cheap 설명), `-fassociative-math`(결과를 바꿀 수 있음) <https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Optimize-Options.html>
  - JLS SE 21 §15.7.3 — 평가 순서와 대수 항등식 금지 <https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.7.3>
- 실험 목록(i7-13700HX, Linux 7.0.0-34, 2026-10-07)
  - `simd.c` — gcc 13.3 `-O0` / `-O2 -fno-tree-vectorize` / `-O3` / `-O3 -march=native` / `+ -ffast-math`, `taskset -c 4`, 3회. `-fopt-info-vec-optimized`·`-fopt-info-vec-all`, `objdump -d`로 `add`·`fsum`·`branchy` 기계어 확인, `gcc -Q --help=optimizers`로 비용 모형 확인
  - `diverge.c` — 양쪽이 무거운 분기, 스칼라 vs AVX2, 입력 all-same/mixed, `taskset -c 6`, 3회
  - `SimdJava.java` — Docker `eclipse-temurin:21-jdk`(21.0.12) `--cpuset-cpus=4 --network none`, `±UseSuperWord` 각 2회, `-XX:+PrintFlagsFinal`(`UseAVX=2`, `MaxVectorSize=32`)
  - GPU: `lspci`에 GeForce RTX 4060 Mobile이 보이나 `nvidia-smi`가 드라이버와 통신하지 못해 실행하지 않음
