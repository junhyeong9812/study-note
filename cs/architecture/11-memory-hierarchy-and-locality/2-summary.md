# architecture/11-memory-hierarchy-and-locality — 메모리 계층과 지역성: 같은 O(n)이 수십 배 갈리는 이유 — 정리 (힌트)

## 해결하는 문제

CPU는 사이클마다 일을 하려 한다. 그런데 DRAM에서 값 하나를 가져오는 데는 그보다 훨씬 오래 걸린다.

```text
  이 호스트(i7-13700HX P코어)에서 잰 "값 하나를 기다리는 시간" (아래 실험 1)
  L1 캐시     ~5 사이클   |#
  L2 캐시    ~15 사이클   |###
  256MB 무작위 사슬 ~170~195 사이클 |####################################  (DRAM + TLB 미스 등이 섞인 값)
```

- 모든 읽기가 DRAM까지 가면 CPU는 대부분의 시간을 기다리며 보낸다.
- 해법: 작고 빠른 저장소를 CPU 가까이 여러 층으로 두고, **곧 쓸 데이터**를 거기에 미리 올려 둔다. 이것이 메모리 계층이다.
  - *메모리 계층(memory hierarchy)*: 레지스터 → L1 → L2 → L3 → DRAM → SSD/HDD 순으로, 위로 갈수록 작고 빠르고 비싼 저장소를 쌓은 구조.
- 계층이 통하는 이유는 프로그램이 **지역성**을 갖기 때문이다(CS:APP 3판 6.2 "Locality").
  - *지역성(locality)*: 최근에 쓴 데이터나 그 근처 데이터를 곧 다시 쓰는 경향.

쉬운 예: 공부하는 책상이다.
- 지금 펼친 책은 책상 위(레지스터·L1), 이번 주에 볼 책은 옆 책장(L2·L3), 나머지는 도서관 서고(DRAM)에 있다.
- 서고에 한 번 갈 때 필요한 책 한 권만이 아니라 같은 칸의 책을 한 묶음 들고 온다.

똑같은 구조다.\
책상 = 캐시, "한 묶음" = 캐시 라인(이 호스트 64바이트), "같은 칸의 옆 책" = 공간 지역성이다.

실무 예:
- 같은 합계 루프(O(n))가 `int[]`에서는 원소당 약 0.5ns, 섞인 `ArrayList<Integer>`에서는 약 17~20ns였다(아래 실험 3, Java 21).
- 2차원 배열을 열 방향으로 돌면 행 방향보다 최대 9~16배 느렸다(아래 실험 2, C — 행렬이 캐시를 넘고 행 길이가 2의 거듭제곱이거나 61MB 이상일 때. 1000×1000은 약 2.5배).
- 원인은 알고리즘이 아니라 **데이터가 메모리에 놓인 모양**이다.

## 동작·원리

기초는 원고 [foundations/memory-management](../../foundations/memory-management/README.md) §1(메모리 계층)·§2(캐시와 지역성)·§14.5(레이턴시 비교)에 있다. 여기서는 이 호스트에서 잰 숫자와 장애 쪽을 채운다.

### 1. 계층 그림 — 이 호스트의 실제 크기

```text
  i7-13700HX (lscpu -C, /sys/devices/system/cpu/cpuN/cache/)
                     P코어(cpu0~15, 2 스레드/코어)        E코어(cpu16~23)
  레지스터            수십 개 × 8바이트
  L1d                48 KB, 12-way, 코어 전용           32 KB, 8-way, 코어 전용
  L2                 1.25 MB, 10-way, 코어 전용         2 MB, 16-way, E코어 4개 공유
  L3                 30 MB, 12-way, 24개 논리 CPU 전체 공유
  DRAM               36 GB (free -g)
  SSD(NVMe)          수백 GB
        위로 갈수록: 작다 · 빠르다 · 비싸다     아래로 갈수록: 크다 · 느리다 · 싸다
  캐시 라인 = 64 B (coherency_line_size, 모든 층 동일)
```

- *캐시 라인(cache line)*: 캐시가 메모리와 주고받는 최소 단위. 1바이트를 읽어도 그 바이트가 든 64바이트 전체가 올라온다.
- *히트 / 미스(hit / miss)*: 찾는 라인이 그 층에 있으면 히트, 없으면 미스. 미스면 한 층 아래에서 라인을 가져온다.
- *작업 집합(working set)*: 일정 시간 동안 프로그램이 실제로 만지는 데이터의 크기. 작업 집합이 어느 층에 들어가느냐가 속도를 정한다.
- 하이브리드 CPU라 **같은 기계에서도 코어마다 L1·L2 크기가 다르다.** 아래 실험에서 그 차이가 그대로 보인다.
  - 흔한 오해: `getconf LEVEL1_DCACHE_SIZE`가 "이 기계의 L1 크기"다. 이 호스트에서 `taskset -c 2`로 돌리면 49152(48KB), `taskset -c 18`로 돌리면 32768(32KB)이 나왔다. 돌린 코어의 값이다.

### 2. 지역성 두 가지

```text
  시간 지역성: 같은 것을 곧 다시           공간 지역성: 근처 것을 곧
  sum += a[i]  ← sum은 매 반복 다시 씀     a[0] a[1] a[2] ... a[15]  ← 한 라인(64B)에 int 16개
                                          └── 배열이 라인 경계에 맞으면 한 번의 미스로 16개가 함께 올라온다 ──┘
```

- *시간 지역성(temporal locality)*: 방금 쓴 데이터를 곧 또 쓴다. 루프 변수, 자주 부르는 함수의 코드.
- *공간 지역성(spatial locality)*: 방금 쓴 주소 근처를 곧 쓴다. 배열 순차 순회.
- 공간 지역성이 깨지는 대표 모양 두 가지가 ⚠ 칸의 두 증상이다.

```text
  (가) 2차원 배열 열 우선 순회 (C는 행 우선 배치)
       메모리:  [r0: c0 c1 c2 ... cN-1][r1: c0 c1 ...][r2: ...]
       열 우선: r0c0 → r1c0 → r2c0 ...   매 접근이 행 길이(N×4B)만큼 건너뛴다
                → 라인 하나에서 4바이트만 쓰고 다음 라인으로. 나머지 60바이트는 나중에 쓸 때쯤 이미 밀려남

  (나) 포인터 추적 (연결 리스트)
       node A ──next──> node F ──next──> node B ──next──> ...   (주소가 흩어짐)
       다음 주소는 지금 읽는 값 안에 있다 → 앞 읽기가 끝나야 다음 읽기 시작 (의존 읽기)
```

- (나)가 특히 나쁜 이유: 다음 주소를 모르니 CPU가 미리 여러 개를 동시에 가져올 수 없다. 미스 하나하나의 지연이 그대로 더해진다.
- 박싱 객체 리스트(`ArrayList<Integer>`)는 모양이 조금 다르다. 참조 배열은 연속이고, 그 참조로 흩어진 객체를 한 번씩 간접 참조한다. 다음 주소가 객체 안이 아니라 배열 다음 칸에 있어 의존 사슬은 아니다. 그래서 미스를 겹칠 수 있어 `LinkedList`보다 덜 나쁘다(실험 3).
  - *의존 읽기(dependent load)*: 앞 읽기의 결과가 다음 읽기의 주소인 읽기. 겹쳐 실행할 수 없다.
  - *하드웨어 프리페처(hardware prefetcher)*: 순차·일정 간격 접근을 알아채고 다음 라인을 미리 가져오는 회로(Drepper 2007 §6.3.1). 일반적인 순차·간격 프리페처는 흩어진 포인터를 예측하기 어렵다. 일부 최신 Intel Core에는 메모리 속 포인터 값을 보고 그 주소를 미리 가져오는 데이터 의존 프리페처(DDP)도 있다. 하지만 가져온 곳을 다시 따라가지는 않는다(Intel "Data Dependent Prefetcher" 문서). 이 호스트에서 그것이 동작했는지는 확인하지 않았다.

### 실험 1: 작업 집합 크기별 "한 번 기다리는 시간" (C, 포인터 추적)

- 방법: 크기 S의 버퍼를 64B 라인으로 나누고, 라인들을 **무작위 순서의 원형 사슬**로 잇는다. `p = *p`를 500만 번 반복해 접근 1회 시간을 잰다. 크기마다 5회 중 최소값.
- 사이클 환산: 같은 프로그램 안에서 레지스터끼리의 의존 `add` 사슬(1사이클/개)로 실제 클록을 잰 값을 곱했다.

```c
for (size_t i = 0; i < n; i++)                       // perm = 라인 번호를 무작위로 섞은 배열
    *(void **)(buf + perm[i]*64) = buf + perm[(i+1) % n]*64;
void **p = (void **)(buf + perm[0]*64);
for (long i = 0; i < iters; i++) p = *p;              // 의존 읽기 사슬
```

환경: i7-13700HX, Linux 7.0.0-34, gcc 13.3.0 `-O2`, `taskset -c 2`(P코어)·`-c 18`(E코어). **측정 중 코어 클록이 약 0.8~0.93GHz로 낮게 묶여 있었다**(`scaling_cur_freq` 0.8~0.9GHz, `add` 사슬 추정과 일치 — P코어 `cpuinfo_max_freq` 4.8~5.0GHz보다 훨씬 낮다). 그래서 ns 절대값은 크고, 사이클 수가 덜 흔들린다. 다른 작업이 돌던 호스트라 여러 번 돌린 범위로 적는다(사실 점검 재실행 1회 포함).

```text
  작업 집합    P코어 cpu2 (4회 범위)                 E코어 cpu18 (첫 실행 1회)
     16 KB    4.8~6.1 ns  ≈ 4.6~5.2 사이클           3.6 ns ≈  3.0 사이클
     32 KB    5.7~6.2 ns  ≈ 5.0~5.2                  3.5 ns ≈  2.9
     40 KB    5.6~7.2 ns  ≈ 5.0~6.2   ← P: 아직 L1   24.5 ns ≈ 20.5   ← E: L1(32KB) 넘음
     64 KB   15.7~17.0 ns ≈ 14.5~15.8 ← P: L2        25.2 ns ≈ 20.6
    512 KB   17.3~21.0 ns ≈ 16.1~18.2                38.8 ns ≈ 31.2
      1 MB   31.0~37.6 ns ≈ 27.5~33.6                78.0 ns ≈ 64.3
      2 MB   72.7~78.7 ns ≈ 62.3~69.3 ← P: L2(1.25MB) 넘음   93.3 ns ≈ 81.0
      8 MB    160~183 ns  ≈ 135~152                  137 ns ≈ 114
     64 MB    197~206 ns  ≈ 168~176                  247 ns ≈ 211
    256 MB    220~233 ns  ≈ 182~195                  286 ns ≈ 245

  E코어 재실행(cpu18, 사실 점검): 16KB 2.9 · 40KB 18.5 · 2MB 72.3 · 256MB 222.7 사이클 — 꺾이는 자리는 같고 큰 크기 값은 실행마다 흔들렸다

  같은 크기, 순차 사슬(라인을 주소 순으로 이음, P코어): 16KB~512KB ≈ 5 사이클, 256MB ≈ 8 사이클
```

- 계단이 캐시 크기에서 꺾인다. P코어는 48KB와 1.25MB 근처, E코어는 32KB 근처에서 꺾였다. lscpu 값과 맞는다.
- 같은 40KB가 P코어에서는 L1 히트, E코어에서는 L1 미스였다. **같은 코드가 어느 코어에 배정되느냐로 몇 배 달라질 수 있다.**
- 1MB 이후 구간에는 TLB 미스(페이지 표 걷기)가 섞인다는 해석이다. 4KB 페이지에서 8MB는 2048페이지다(이 호스트 THP는 `madvise` 모드이고 실험 코드는 madvise를 하지 않아 4KB 페이지로 본다). TLB 효과의 분리 측정은 [os/10-paging-and-tlb](../../os/10-paging-and-tlb/2-summary.md)에 있다.
- 8MB(L3 안)와 256MB(DRAM)의 차이가 생각보다 작았다(약 150 vs 190 사이클). 낮은 클록 상태의 L3 지연과 TLB 미스가 함께 든 값이라는 해석이다. perf 카운터를 쓸 수 없는 환경(`perf_event_paranoid=4`)이라 미스 종류를 직접 세지 못했다.
- **순차 사슬은 256MB에서도 약 8사이클**이었다. 데이터가 DRAM에 있어도 주소가 예측되면 프리페처가 미리 가져와 지연을 숨긴다. 같은 크기, 같은 접근 횟수인데 접근 **순서**만으로 20배 넘게 갈렸다.
- 참고: 원고 §14.5의 표(L1 4·L2 12·L3 40·RAM 100+ 사이클)는 출처 없는 대략치다. 이 호스트의 L1·L2 사이클은 같은 자릿수였지만, 클록이 낮은 상태의 L3·DRAM은 150~195사이클로 표와 달랐다. DRAM 지연은 ns 단위로 거의 고정이라 **코어 클록이 높을수록 사이클 수는 커진다.**
- 참고: 원고 §2의 "실제 캐시에 필요한 데이터가 존재할 확률은 90% 이상"은 출처가 없고 워크로드마다 다르다. 위 256MB 무작위 사슬은 거의 모든 접근이 미스인 경우다.

### 실험 2: 행 우선 vs 열 우선 (C)

```c
for (int i = 0; i < N; i++) for (int j = 0; j < N; j++) s += a[(size_t)i*N + j];   // 행 우선
for (int j = 0; j < N; j++) for (int i = 0; i < N; i++) s += a[(size_t)i*N + j];   // 열 우선
```

`gcc -O2 -fno-tree-vectorize`, `taskset -c 2`, 크기마다 3회 중 최소, 전체를 4번 돌린 범위(사실 점검 재실행 1회 포함):

```text
     N   행렬 크기   행 우선 ns/원소   열 우선 ns/원소   열/행
    64     16 KB      1.8~2.3          1.7~2.9          0.9~1.4x   ← 전부 L1 안: 순서 무관
   256    256 KB      1.3~1.8          2.8~3.6          2.0~2.2x
  1000    3.8 MB      1.5             3.4~3.7          2.3~2.5x
  1024    4.0 MB      1.5             13.6~14.9         9.3~10.2x  ← 2의 거듭제곱 행 길이
  2000   15.3 MB      1.3~1.5          6.5~7.1          4.6~5.0x
  2048   16.0 MB      1.3~1.5         13.6~14.1         9.0~11.3x
  4000   61.0 MB      1.1~1.3         12.7~14.6        10.7~13.1x
  4096   64.0 MB      1.1~1.5         17.2~18.9        12.2~16.1x
```

- 행 우선은 크기와 거의 무관하게 원소당 약 1.1~1.5ns(약 1사이클)다. 순차 접근이라 프리페처가 따라온다.
- 열 우선은 행렬이 캐시를 넘는 순간 크게 느려진다. 4000×4000(61MB)에서 약 11~13배다.
- **N=1000과 N=1024는 크기가 거의 같은데 2.3~2.5배 vs 9~10배로 갈렸다.** 행 길이가 4096바이트(2의 거듭제곱)면 한 열의 원소들이 캐시의 같은 칸(집합)에 몰린다. 이것은 지역성이 아니라 **캐시 구성**의 문제라 [12-cache-organization](../12-cache-organization/2-summary.md)에서 다룬다.

### 실험 3: 같은 합, 네 가지 배치 (Java 21)

```java
int[] arr;                               // 값이 연속으로
ArrayList<Integer> ordered;              // 참조 배열 + Integer 객체(할당 순서대로 놓였을 가능성 — 주소는 확인 안 함)
ArrayList<Integer> shuffled;             // 같은 객체들, 참조 순서만 Collections.shuffle
LinkedList<Integer> linked;              // shuffled 순서로 만든 연결 리스트
for (Integer x : list) s += x;           // 모두 같은 합계 루프
```

`eclipse-temurin:21-jdk`(JDK 21.0.12), `--cpus=2 --cpuset-cpus=2,4`, n = 400만, JIT 예열 5회 후 7회 중 최소, 4번 실행 범위(사실 점검 재실행 1회 포함):

```text
  int[]                          0.48~0.51 ns/원소
  ArrayList<Integer> 할당 순서    5.6~6.2
  ArrayList<Integer> 섞은 순서   17.2~20.3
  LinkedList<Integer>(섞은 값)   41.5~43.3
  int[2048][2048] 행 우선 0.49~1.20, 열 우선 17.0~18.2 ns/원소 (14.7~35.4배)
```

```text
  int[]:            [7][1][3][0][5] ...                 값이 바로 붙어 있다
  ArrayList<Integer>: [ref][ref][ref] ...                참조를 따라가면
                        │    │    └──> Integer{hdr, 3}   객체 헤더 + 값 (객체당 16B [?])
                        │    └───────> Integer{hdr, 1}
                        └────────────> Integer{hdr, 7}   섞으면 이 화살표들이 힙 곳곳으로 흩어진다
```

- 할당 순서 그대로면 `Integer` 객체들이 힙에 차례로 놓였을 가능성이 높다는 해석이다(HotSpot은 스레드별 버퍼에서 차례로 떼어 할당한다. JVM 명세는 배치를 보장하지 않고, 이 실험은 주소를 확인하지 않았다). 그러면 참조를 따라가도 대체로 순차다. 그래도 `int[]`보다 10배 남짓 느리다(간접 참조 + 언박싱 + 더 큰 메모리).
- 참조 순서만 섞으면 같은 객체, 같은 개수인데 다시 약 3배 느려진다. 참조 배열은 여전히 연속이지만 객체를 흩어진 순서로 간접 참조해 라인마다 미스가 난다는 해석이다.
- `LinkedList`는 노드 객체를 하나 더 거치고, 다음 노드 주소가 지금 노드 안에 있는 의존 사슬이다.
- GC가 객체를 옮기면 배치가 바뀔 수 있다. 이 실험에서는 측정 구간의 GC를 따로 통제하지 않았다.

### 계층은 캐시에서 끝나지 않는다

```text
  CPU 캐시 ── 미스 ──> DRAM(페이지 캐시 포함) ── 페이지가 DRAM에 없음 ──> SSD/HDD(파일·스왑)
  (이 노트)            (os/10 TLB, os/14 페이지 캐시)                       (architecture 16)
  단위: 64B 라인        4KB 페이지                                          블록
```

- 페이지 캐시는 DRAM 안에 둔 파일 데이터 캐시다(Linux 커널 문서 admin-guide/mm/concepts "Page cache"). 모든 페이지 폴트가 디스크로 가지는 않는다. 익명 메모리의 첫 읽기는 0으로 채운 페이지로 처리된다(같은 문서 "Anonymous Memory").
- 같은 원리(작고 빠른 층에 곧 쓸 것을 둔다)가 OS 페이지 캐시, DB 버퍼 풀, 애플리케이션 캐시까지 반복된다. 층마다 단위만 커진다.

## 쓰이는 자료구조·알고리즘

- **배열 vs 연결 리스트 선택 근거**(🔧): 순회가 많으면 연속 배열. 삽입·삭제 위치의 노드·반복자를 이미 쥔 채 중간 삽입·삭제가 대부분이고 순회가 드물 때만 연결 리스트가 이긴다(인덱스로 위치를 찾으면 그 순회 비용이 든다). [data-structure/01-dynamic-array](../../data-structure/01-dynamic-array/2-summary.md) · [data-structure/02-linked-list](../../data-structure/02-linked-list/2-summary.md)
- **B-tree 노드 크기**: 노드 하나를 디스크 페이지·캐시 라인 묶음에 맞춰 한 번의 미스로 많은 키를 본다. [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md)
- **열 저장(column store)**: 집계에 필요한 열만 연속으로 두어 공간 지역성을 얻는다. [database/37-row-vs-column-storage](../../database/37-row-vs-column-storage/2-summary.md)
- **LRU 교체**: 시간 지역성을 가정한 정책. 버퍼 풀·애플리케이션 캐시가 쓴다. [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md) · [database/07-buffer-pool](../../database/07-buffer-pool/2-summary.md)
- **루프 순서 바꾸기·블록 단위 처리(tiling)**: 행렬 곱에서 안쪽 루프가 연속 주소를 돌도록 순서를 바꾼다(CS:APP 6.6.2 "Rearranging Loops to Increase Spatial Locality" — 절 제목은 목차로 확인). [math/13-linear-algebra-essentials](../../math/13-linear-algebra-essentials/2-summary.md)

## 적용 — 풀어나가는 법

1. **증상**: 데이터가 늘어난 비율보다 처리 시간이 훨씬 더 늘었다. 또는 같은 O(n) 두 구현의 속도가 몇 배 차이 난다.
2. **계산 문제인가 메모리 문제인가**를 가른다.
   - 작은 입력(캐시 안)에서는 빠르고, 어떤 크기를 넘는 순간 원소당 시간이 계단처럼 뛰면 메모리 계층 문제다(실험 1·2의 꺾임).
   - 그 크기를 이 기계의 캐시 크기와 비교한다.

```bash
lscpu -C                                            # 층별 크기·연관도·집합 수 (CPU0 기준 표)
cat /sys/devices/system/cpu/cpu*/cache/index0/size | sort | uniq -c   # 하이브리드면 코어별로 다르다
cat /sys/devices/system/cpu/cpu0/cache/index0/coherency_line_size     # 라인 크기 (이 호스트 64)
```

3. **배치를 확인한다.** 박싱 컬렉션·연결 리스트·객체 그래프 순회가 핫 루프에 있는지 본다.

```bash
jcmd <pid> GC.class_histogram | head      # java.lang.Long·Integer, LinkedList$Node 인스턴스 수가 수백만이면 의심
```

4. **고친다** — 데이터 모양을 바꾸는 것이 먼저다.

```java
// 전: 박싱 리스트, 흩어진 객체 간접 참조
List<Long> amounts = loadAmounts();
long total = 0; for (Long a : amounts) total += a;

// 후: 원시 배열, 연속 순회
long[] amounts = loadAmountsAsArray();
long total = 0; for (long a : amounts) total += a;

// 2차원: 안쪽 루프가 마지막 인덱스를 돌게
for (int i = 0; i < rows; i++) for (int j = 0; j < cols; j++) sum += grid[i][j];
```

   - 객체 배열 대신 필드별 원시 배열(AoS → SoA)로 바꾸면 필요한 필드만 연속으로 읽는다.
   - *AoS / SoA*: Array of Structures(객체의 배열) / Structure of Arrays(필드마다 배열).
5. **같은 기계·같은 코어 종류에서 운영 크기로 다시 잰다.** 작은 입력의 마이크로벤치마크는 L1 안의 숫자다(실험 1의 16KB 행).

## 장애 시나리오와 대처

### 1. 데이터 10배에 배치 시간 30배

- **현상**: 정산 배치가 거래 100만 건일 때 2분, 1000만 건에서 1시간 넘게 걸린다. 알고리즘은 O(n)이다.
- **보이는 형태**: CPU 사용률은 100%인데 처리량(건/초)이 크기에 따라 떨어진다. GC 로그는 평범하다.
- **원인(가설)**: 작업 집합이 L3(이 호스트 30MB)를 넘었다. 박싱 객체·해시맵 엔트리를 무작위 순서로 따라가며 많은 접근이 DRAM까지 간다(실험 1에서 L1 대비 30배 넘는 지연). 자주 쓰는 부분은 캐시에 남을 수 있어, 확정하려면 LLC 미스 카운터(perf 등)나 크기별 원소당 시간 곡선으로 확인한다.
- **대처**: 원시 배열·정렬된 순회로 바꾼다. 키 순서로 정렬한 뒤 순차 처리(머지 조인처럼)하면 무작위 접근이 순차 접근이 된다. 원소당 시간을 크기별로 그려 꺾이는 크기를 찾는다.

### 2. 행렬·이미지·표 데이터를 열 방향으로 돈다

- **현상**: 열 단위 통계(엑셀식 "열마다 합계")나 이미지 세로 필터가 가로 필터보다 몇 배 느리다.
- **보이는 형태**: 같은 원소 수인데 방향만 바꾸면 수~십수 배(실험 2·3: C에서 캐시를 넘는 크기 2~16배, Java `int[2048][2048]`에서 15~35배).
- **원인**: 행 우선 배치에서 열 방향은 매 접근이 다른 캐시 라인이다. 행 길이가 2의 거듭제곱이면 충돌 미스까지 겹친다(12번).
- **대처**: 루프 순서를 바꾸거나, 전치해 둔 사본을 한 번 만들고 그 위에서 돈다. 열 단위 처리가 주 용도면 저장을 열 기준으로 한다.

### 3. `List<Long>`·`Map<Long, …>` 대량 적재

- **현상**: 1천만 건 ID 목록을 `List<Long>`으로 들고 집계하니 느리고 힙도 크다.
- **보이는 형태**: `GC.class_histogram`에 `java.lang.Long` 수백만 개. 순회 시간이 `long[]`의 10~40배(실험 3의 `Integer` 결과와 같은 모양).
- **원인**: 원소마다 객체 헤더가 붙고, 참조를 한 번 더 따라가는 간접 참조가 된다(객체가 흩어져 있으면 라인마다 미스). 객체 배치 세부는 language 영역 "객체 레이아웃과 할당 줄이기"([language/12-object-layout-and-allocation-reduction](../../language/12-object-layout-and-allocation-reduction/2-summary.md))에서 다룬다.
- **대처**: `long[]`, 원시형 특화 컬렉션, 정렬된 원시 배열 + 이진 탐색으로 바꾼다.

### 4. 같은 서비스, 인스턴스마다 다른 지연 (하이브리드 CPU)

- **현상**: 같은 이미지·같은 요청인데 어떤 때는 빠르고 어떤 때는 몇 배 느리다. 데스크톱·노트북급 하이브리드 CPU에서 돌린 테스트 환경에서 특히 보인다.
- **보이는 형태**: 지연 분포가 두 봉우리. 스레드를 특정 코어에 고정하면 한쪽으로 모인다.
- **원인**: P코어와 E코어의 캐시 크기가 다르다(이 호스트 L1 48KB vs 32KB). 작업 집합 40KB가 P코어에서는 L1 히트(약 5사이클), E코어에서는 L2(약 20사이클)였다(실험 1).
- **대처**: 벤치마크는 코어를 고정해 따로 잰다(`taskset -c`). 운영 판단은 운영과 같은 CPU 종류에서 한다. 코어 배치 정책은 [20-multicore-and-numa](../20-multicore-and-numa/2-summary.md)에서 다룬다.

## 핵심 문장

- 메모리 계층은 "곧 쓸 데이터를 작고 빠른 층에 둔다"는 장치이고, 지역성이 있어야 통한다.
- 캐시는 64바이트 라인 단위로 움직인다. 1바이트를 읽어도 라인 전체가 오고, 그 나머지를 쓰느냐가 공간 지역성이다.
- 같은 O(n)도 접근 순서가 순차냐 무작위냐에 따라 수십 배 갈린다. 이 호스트에서 256MB 순차 사슬은 약 8사이클, 무작위 사슬은 약 190사이클이었다.
- 포인터 추적은 다음 주소를 미리 알 수 없어 미스 지연이 하나씩 그대로 쌓인다. 연결 리스트가 그 모양이고, 박싱 컬렉션은 흩어진 객체를 간접 참조해 그다음으로 나쁘다(실험 3).
- 캐시 크기는 기계마다, 하이브리드 CPU에서는 코어마다 다르다. 원소당 시간이 꺾이는 크기를 재고 `lscpu -C`와 대조한다.

## 관련 주제·근거

- 선행: [09-isa-and-machine-code](../09-isa-and-machine-code/2-summary.md) — 읽기·쓰기 명령이 메모리를 만지는 단위
- 원고: [foundations/memory-management](../../foundations/memory-management/README.md) §1·§2·§14.5
- 후속
  - [12-cache-organization](../12-cache-organization/2-summary.md) — 라인이 어느 칸에 들어가나, 2의 거듭제곱 stride 충돌, false sharing
  - [13-latency-numbers](../13-latency-numbers/2-summary.md) — 층별 지연 자릿수와 AMAT
  - [14-cache-coherence-and-memory-ordering](../14-cache-coherence-and-memory-ordering/2-summary.md) — 코어마다 캐시가 따로일 때
  - 같은 영역: [15-io-devices-interrupts-dma](../15-io-devices-interrupts-dma/2-summary.md) · [16-storage-media-workload](../16-storage-media-workload/2-summary.md) · [20-multicore-and-numa](../20-multicore-and-numa/2-summary.md)
- 다른 영역
  - [os/10-paging-and-tlb](../../os/10-paging-and-tlb/2-summary.md) — TLB·huge page(같은 호스트 측정)
  - [os/14-mmap-and-page-cache](../../os/14-mmap-and-page-cache/2-summary.md) — 디스크 위의 캐시 층
  - [os/07-threads-and-context-switch](../../os/07-threads-and-context-switch/2-summary.md) — 문맥 교환 뒤 캐시가 식는 간접 비용
  - [data-structure/01-dynamic-array](../../data-structure/01-dynamic-array/2-summary.md) · [02-linked-list](../../data-structure/02-linked-list/2-summary.md) · [15-b-tree](../../data-structure/15-b-tree/2-summary.md) · [10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)
  - [database/07-buffer-pool](../../database/07-buffer-pool/2-summary.md) · [database/37-row-vs-column-storage](../../database/37-row-vs-column-storage/2-summary.md)
  - [math/13-linear-algebra-essentials](../../math/13-linear-algebra-essentials/2-summary.md) — 행렬 순회
- 후속(AI 엔지니어링): [ai-engineering/08-kv-cache-and-inference-memory](../../ai-engineering/08-kv-cache-and-inference-memory/2-summary.md) — KV 캐시와 추론 메모리
- 교재·문서
  - CS:APP 3판 6.1 Storage Technologies · 6.2 Locality · 6.3 The Memory Hierarchy · 6.5 Writing Cache-Friendly Code · 6.6 Putting It Together: The Impact of Caches on Program Performance(6.6.1 Memory Mountain, 6.6.2 Rearranging Loops) — 절 번호·제목은 저자 사이트 목차 PDF로 확인 <https://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf>, 본문은 열지 못했다
  - U. Drepper, "What Every Programmer Should Know About Memory", 2007 — §3.3.2 Measurements of Cache Effects(순차·무작위 접근 그래프, 그림 3.10·3.11·3.15), §6.3.1 Hardware Prefetching <https://people.freebsd.org/~lstewart/articles/cpumemory.pdf>
  - Intel, "Data Dependent Prefetcher" (Software Security Guidance) <https://www.intel.com/content/www/us/en/developer/articles/technical/software-security-guidance/technical-documentation/data-dependent-prefetcher.html> — 2026-10-07 intel.com 403, Internet Archive 사본으로 열람
  - Linux sysfs 캐시 정보 `/sys/devices/system/cpu/cpuN/cache/indexM/{size,ways_of_associativity,number_of_sets,coherency_line_size,shared_cpu_list}` (이 호스트에서 읽음)
- 실험 목록(환경: i7-13700HX, Linux 7.0.0-34-generic, gcc 13.3.0, eclipse-temurin:21-jdk = JDK 21.0.12, 측정 중 코어 클록 약 0.8~0.93GHz, 다른 작업이 돌던 호스트)
  - 실험 1 `chase.c`: 작업 집합 16KB~256MB 무작위·순차 포인터 사슬, P코어 cpu2 4회·E코어 cpu18 2회(각 1회는 사실 점검 재실행)
  - 실험 2 `rowcol.c`: N=64~4096 행 우선 vs 열 우선, `-O2 -fno-tree-vectorize`, 4회
  - 실험 3 `Locality.java`: `int[]`·`ArrayList<Integer>`(할당 순서·섞은 순서)·`LinkedList`, `int[2048][2048]` 행·열, 컨테이너 `--cpus=2`, 4회
  - 클록 추정: 레지스터 의존 `add` 사슬과 `imul` 사슬(둘 다 약 0.8GHz)
