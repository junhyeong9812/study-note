# architecture/12-cache-organization — 캐시 구성: 라인·집합·연관도·쓰기·교체, 그리고 false sharing — 정리 (힌트)

## 해결하는 문제

11번에서 "캐시에 있으면 빠르다"를 봤다. 그런데 캐시는 작다. 수십 GB 메모리 중 어느 라인을 48KB 안의 **어느 자리**에 둘지, 찾을 때 **어디를 볼지**, 꽉 차면 **무엇을 버릴지**, 쓰기는 **언제 메모리에 반영할지**를 정해야 한다.

```text
  메모리 주소 0x7f3a_1234_5678 의 라인을 찾는다
  모든 칸을 다 뒤진다?      → 비교기가 수천 개 필요 (느리고 비쌈)
  주소로 칸 하나를 정한다?   → 같은 칸에 몰리는 주소끼리 서로 쫓아낸다
  주소로 "구역"을 정하고 구역 안 몇 칸만 뒤진다 → 지금 CPU들의 방식 (집합 연관)
```

쉬운 예: 큰 주차장이다.
- 번호판 끝 두 자리로 구역을 정한다. 구역마다 12칸이 있다.
- 차를 찾을 때는 그 구역 12칸만 본다. 구역이 꽉 차면 그 구역에서 오래 안 움직인 차를 뺀다.
- 끝 두 자리가 같은 차만 계속 오면, 다른 구역이 텅 비어 있어도 그 구역에서만 계속 차를 뺀다.

똑같은 구조다.\
번호판 끝자리 = 주소의 인덱스 비트, 구역 = 집합(set), 12칸 = 12-way다. "끝자리 같은 차만 온다" = **4096B처럼 큰 2의 거듭제곱 간격 접근의 충돌 미스**다.

캐시 라인이 단위라는 사실은 또 하나의 함정을 만든다.
- 두 스레드가 **서로 다른 변수**를 쓰는데, 두 변수가 같은 64바이트 라인에 있으면 하드웨어는 같은 것을 다투는 것처럼 움직인다.
- 이것이 ⚠ 칸의 **false sharing**이다. 이 호스트에서 스레드 2개 카운터가 스레드 1개보다 3~6배 느렸다(아래 실험 3).

## 동작·원리

### 1. 주소를 세 조각으로 — 태그·인덱스·오프셋

이 호스트 P코어 L1d: 48KB, 12-way, 64B 라인 → 집합 수 = 48KB ÷ (12 × 64B) = **64** (`number_of_sets`로 확인).

```text
  가상 주소 (하위 비트만)
   bit: 47 ............................ 12 | 11 ........ 6 | 5 ...... 0
        [            태그(tag)               ][ 인덱스 6비트 ][ 오프셋 6비트 ]
                                               64개 집합 중 하나   라인 안 64바이트 중 위치

  찾는 순서
   1) 인덱스로 집합 하나를 고른다
   2) 그 집합의 12개 칸의 태그를 동시에 비교한다
   3) 같은 태그가 있으면 히트 → 오프셋 위치의 바이트를 돌려준다
      없으면 미스 → 아래 층에서 라인을 가져와 12칸 중 하나를 비우고 넣는다
```

- *오프셋(offset)*: 라인 안에서의 바이트 위치. 64B 라인이면 6비트.
- *인덱스(index)*: 몇 번째 집합인지. 집합이 64개면 6비트.
- *태그(tag)*: 같은 집합에 올 수 있는 수많은 라인 중 "누구인지"를 가리는 나머지 상위 비트.
- *집합(set)*: 인덱스가 같은 라인들이 들어갈 수 있는 칸 묶음.
- *연관도(associativity, N-way)*: 집합 하나의 칸 수. 같은 인덱스의 라인을 동시에 몇 개까지 둘 수 있나.
- 이 L1에서는 인덱스+오프셋이 12비트다. 4KB 페이지 안의 오프셋(12비트)과 같아서, 가상 주소로 골라도 물리 주소로 고른 것과 같은 집합이 된다. 그래서 아래 L1 실험은 가상 주소만으로 집합을 정확히 겨냥할 수 있다.
  - 더 큰 캐시의 인덱스는 페이지 오프셋을 넘는 비트를 쓴다. 물리 주소로 인덱싱하는 캐시라면 사용자 프로그램은 어느 집합에 들어갈지 정할 수 없다(Drepper 2007 §3.3.5).

### 2. 배치 방식 세 가지

```text
  직접 사상(direct-mapped)      집합 연관(set-associative)       완전 연관(fully associative)
  집합마다 1칸                   집합마다 N칸                      집합 1개, 모든 칸
  ┌──┐ set0                     ┌──┬──┬──┬──┐ set0              ┌──┬──┬──┬──┬──┬──┬──┬──┐
  ├──┤ set1                     ├──┼──┼──┼──┤ set1              └──┴──┴──┴──┴──┴──┴──┴──┘
  ├──┤ set2                     └──┴──┴──┴──┘ ...               태그를 전부 동시에 비교
  비교기 1개, 충돌에 약함         비교기 N개 (이 호스트 L1 12개)     비교기 = 칸 수 (작은 TLB 등)
```

- Drepper 2007 §3.3.1(그림 3.5~3.7)이 세 방식을 그림으로 비교한다. 직접 사상은 주소가 인덱스 비트에 고르게 퍼지지 않으면 일부 칸만 계속 쓰인다고 적는다.
- 연관도를 키우면 충돌은 줄지만 동시에 비교할 태그가 늘어 회로가 커진다.

### 3. 쓰기 정책

```text
  write-through: 캐시에 쓰면서 바로 아래 층에도 쓴다     → 단순, 매 쓰기가 아래 층 트래픽
  write-back:    캐시에만 쓰고 "더러움(dirty)" 표시      → 매 쓰기마다 내려 쓰지 않는다. 주로 쫓겨날 때 내려 쓴다

  write-back 라인의 일생
   [읽어 옴, 깨끗] --쓰기--> [dirty] --또 쓰기(트래픽 없음)--> [dirty] --쫓겨남--> 아래 층에 한 번 기록
```

- *write-back*: 수정 사항을 캐시에 모았다가 주로 라인이 나갈 때 기록. 그 전에도 내려갈 수 있다 — 다른 코어가 그 라인을 읽을 때(Drepper §3.3.4 MESI 설명: 메모리 컨트롤러가 그 내용을 메모리에 저장), `clflush`·`clwb` 같은 명령으로. Drepper 2007 §3.3.3은 성능이 좋아 대부분의 메모리가 이 방식으로 캐시된다고 적는다.
- *write-allocate*: 캐시에 없는 주소에 쓰면 그 라인을 먼저 읽어 와서 쓴다. write-back과 짝을 이루는 경우가 많다(CS:APP 6.4.5 "Issues with Writes" — 절 제목은 목차로 확인, 본문 미확인 [?]).
- write-back 캐시가 여러 코어에 따로 있으면 "다른 코어의 dirty 라인을 어떻게 보나"가 문제가 된다. 그 답이 일관성 프로토콜(MESI)이고 14번에서 다룬다.

### 4. 교체 — LRU와 의사 LRU

- *LRU(Least Recently Used)*: 집합 안에서 가장 오래 안 쓴 칸을 버린다. Drepper 2007 §3.3.5는 대부분의 캐시가 LRU를 쓰지만, 연관도가 커지면 LRU 목록 유지가 비싸져 다른 전략이 쓰일 수 있다고 적는다.
- *의사 LRU(pseudo-LRU, tree-PLRU)*: 정확한 순서 대신 이진 트리의 비트 몇 개로 "대략 오래된 쪽"을 고른다.

```text
  4-way 집합, 비트 3개 (b0 b1 b2)            접근할 때: 지나온 길의 반대쪽을 가리키게 비트를 바꾼다
              b0                             버릴 때:   비트가 가리키는 쪽으로 내려간다
            /    \
          b1      b2                         예) 칸 A에 접근 → b0=오른쪽, b1=오른쪽(B쪽)
         /  \    /  \                            다음 희생자 찾기: b0 → 오른쪽 → b2가 가리키는 C 또는 D
        A    B  C    D
```

- 4-way에 비트 3개, N-way에 N−1개로 끝난다. 정확한 LRU의 순서 정보보다 훨씬 작다.
- 근사라서 틀릴 때가 있다. 위키백과 "Pseudo-LRU"의 예: 칸 배치가 (A, C | B, D)일 때 접근 순서 C, B, D, A 뒤에 가장 오래된 C 대신 B를 버린다(A와 C가 같은 절반이라 A 접근이 C 쪽 절반을 피하게 만든다). 위 그림의 (A, B | C, D) 배치에서는 같은 순서라도 C를 버려 우연히 맞는다.
- Intel이 이 CPU의 각 층에 어떤 교체 정책을 쓰는지는 공개 문서로 확인하지 못했다 [?]. 아래 실험 1에서 "13개 라인을 12칸에 돌리는" 경우의 지연이 정확한 LRU라면 나와야 할 값(매번 미스, L2 약 15사이클)보다 낮은 약 8~9사이클이었다. 교체 정책이 정확한 LRU가 아니어서 일부가 히트했을 수도 있고, 간격이 일정(4096B)해 하드웨어 프리페처가 다음 라인을 미리 가져왔을 수도 있다(Drepper §6.3.1: 일정 stride도 프리페치 대상). 카운터 없이 둘을 가르지 못했다 — 해석이 아니라 미결로 둔다.

### 실험 1: 2의 거듭제곱 stride 충돌 (C)

- 방법: K개 라인을 `stride` 바이트 간격으로 두고 원형 포인터 사슬로 돈다. 접근 1회 지연을 잰다(5회 중 최소, 3번 실행 — 1번은 사실 점검 재실행).
- stride 4096 = 2^12. 인덱스 비트(6~11)가 모든 라인에서 같다 → **전부 L1의 같은 집합 하나**에 몰린다.
- stride 4160 = 4096 + 64. 라인마다 인덱스가 1씩 달라 → 집합이 흩어진다.

```c
for (int i = 0; i < K; i++)
    *(void **)(buf + (size_t)i*stride) = buf + (size_t)((i+1) % K)*stride;
for (long i = 0; i < it; i++) p = *p;
```

환경: P코어 `taskset -c 2`, gcc 13.3.0 `-O2`, 측정 중 클록 약 0.81~0.87GHz.

```text
    K    stride 4096 (같은 집합)     stride 4160 (흩어짐)
    4     5.6~6.0 ns ≈ 4.9~5.0 사이클    5.6~5.8 ns ≈ 4.9~5.0
   12     5.5~5.8 ns ≈ 4.6~5.1          5.2~5.9 ns ≈ 4.6~5.0
   13     9.3~9.9 ns ≈ 8.3~8.8   ←      5.2~5.6 ns ≈ 4.6~5.1
   14    13.3~14.6 ns ≈ 11.7~12.4        5.5~5.8 ns ≈ 4.9
   16~64  10.5~11.7 ns ≈ 9.2~11.0        4.6~6.7 ns ≈ 4.5~5.5
```

- **K=12까지는 히트, K=13에서 꺾였다.** 12-way라는 `lscpu -C` 값이 실험으로 그대로 보인다.
- 64개 라인(4KB어치)밖에 안 되는데 미스가 난다. 캐시 용량(48KB)은 남아 있다. 이것이 *충돌 미스(conflict miss)*다.
  - *충돌 미스*: 캐시 전체에는 자리가 있는데, 한 집합에 몰려서 생기는 미스.
  - 흔한 오해: "데이터가 캐시 크기보다 작으면 미스가 안 난다." 용량이 아니라 집합별 칸 수가 한계일 수 있다.
- 같은 64개 라인을 64B만 어긋나게(stride 4160) 두면 전부 히트다.

### 실험 2: 실무 모양 — 행 길이가 2의 거듭제곱인 행렬의 열 방향 합

```c
for (int j = 0; j < 1024; j++) for (int i = 0; i < 1024; i++) s += m[(size_t)i*C + j];   // C = 1024 또는 1040
```

```text
  행 길이 1024 int (= 4096 B)   11.8~13.5 ns/원소
  행 길이 1040 int (= 4160 B)    1.9~2.9 ns/원소        (3번 실행 범위, 4.7~6.4배 차이)
```

- 열 하나를 내려갈 때 1024개 라인을 만진다. 다음 열은 같은 라인들의 다음 4바이트다. 1024개 라인이 캐시에 남아 있으면 다음 열은 히트다.
- 행 길이 4096B면 그 1024개 라인이 L1에서는 집합 1개(12칸), L2에서도 일부 집합에 몰린다(P코어 L2는 집합 2048개라 인덱스가 비트 6~16이다. 4096B 간격이면 비트 6~11은 페이지 오프셋이라 모두 같고, 비트 12~16의 5비트만 달라질 수 있어 최대 32개 집합만 쓴다 — 단순 비트 인덱싱을 가정한 계산 [?]. L2는 물리 주소로 인덱싱돼 32개 중 실제로 몇 개에 몰리는지는 물리 페이지 배치에 달려 있다). 그러면 L1은 물론 L2의 최대 32개 집합 × 10칸 = 320칸에도 1024개 라인이 다 못 남는다는 계산이다.
- 행 길이를 16개(64B)만 늘리면 L1에서는 집합당 16개라 여전히 12칸을 넘는다. 하지만 L2에서는 집합이 흩어져 1024개 라인(64KB)이 넉넉히 남는다는 계산이다. 두 판의 차이는 주로 L2에서 살아남느냐로 본다(해석 — 시간만 쟀고 층별 미스 카운터는 못 썼다). 11번 실험 2의 N=1000 vs 1024 차이가 같은 원인이라는 해석이다.

### 5. 인덱스 비트 해싱 — 몰림을 피하는 하드웨어·소프트웨어의 같은 발상

```text
  하위 비트만으로 인덱스:  addr[11:6]                    → 2^12 간격 주소가 전부 한 집합
  상위 비트를 섞어 고르기:  f(addr 상위, addr[11:6])          → 같은 간격이어도 고르는 칸이 흩어짐 (발상)
```

- Intel의 공유 L3는 여러 조각(slice)으로 나뉘고, 주소를 문서화되지 않은 함수("complex addressing")로 해시해 조각을 고른다는 역공학 결과가 있다(Maurice 외, "Reverse Engineering Intel Last-Level Cache Complex Addressing Using Performance Counters" — 저자 PDF 초록: Sandy Bridge·Ivy Bridge·Haswell 대상). 이 해시는 **조각을 고르는 것**이고, 조각 안의 집합은 주소 비트로 직접 정해진다(같은 논문 §2.1·그림 2: "Contrary to the slices, the sets are directly addressed"). 집합 인덱스 해싱의 근거는 아니지만, 상위 비트를 섞어 몰림을 줄이는 발상은 같다. 이 CPU(Raptor Lake)의 해시 함수 자체는 공개 문서로 확인하지 못했다 [?].
- 소프트웨어 판이 Java `HashMap.hash()`다. OpenJDK 21 소스 주석: 표가 2의 거듭제곱 마스킹을 쓰므로 "마스크 위 비트만 다른 해시들은 항상 충돌한다". 그래서 `h ^ (h >>> 16)`으로 상위 비트를 내려 섞는다. 캐시 인덱스 몰림과 같은 문제, 같은 처방이다.

### 6. false sharing — 라인이 "공유 단위"라서 생기는 일

```text
  64바이트 라인 하나
  ┌──────── counterA (8B) ────────┬──────── counterB (8B) ────────┬───── 나머지 ─────┐
  └───────────────────────────────┴───────────────────────────────┴──────────────────┘
     코어 0만 씀                       코어 1만 씀

  코어 0: A++  → 라인을 "내 것(수정 중)"으로 가져와야 함 → 코어 1의 사본 무효화
  코어 1: B++  → 라인을 다시 가져와야 함               → 코어 0의 사본 무효화
  → 라인이 두 코어 사이를 계속 오간다. 논리적으로는 아무것도 공유하지 않는데.

  패딩 후:  [counterA][..56B 패딩..] | [counterB][..56B 패딩..]   라인이 다르다 → 각자 자기 캐시에서 끝
```

- *false sharing(거짓 공유)*: 서로 다른 변수인데 같은 캐시 라인에 있어서, 한 코어의 쓰기가 다른 코어의 라인을 무효화하는 현상(Drepper 2007 §6.4.1). 라인을 오가게 하는 일관성 메시지(RFO)는 14번.
- Drepper 2007 §6.4.1 그림 6.10: 프로세서 4개(P4) 기계에서 스레드마다 5억 번 증가, 한 라인 공유 시간 ÷ 라인 분리 시간으로 잰 오버헤드가 390%·734%·1,147%였다(본문은 "respectively"로만 적는다 — 스레드 2·3·4개로 읽는 것은 그림 기준 해석). 같은 절 그림 6.11의 단일 프로세서 쿼드코어(Core 2 QX6700, L2 두 개)에서는 약간의 오버헤드만 있고 코어 수에 따라 늘지 않았다. **어떤 캐시를 공유하느냐에 따라 효과가 달라진다**는 점이 아래 실험에서도 보인다.

### 실험 3: false sharing — C, 원자적 증가

- 스레드마다 자기 카운터만 `__atomic_fetch_add`로 2천만 번 증가한다(`objdump`로 `lock addq $0x1,(%rax)` 확인). 두 카운터 간격만 8·64·128바이트로 바꾼다. 코어 쌍을 바꿔 고정한다.

```text
  (ms, 각 줄 2~5번 실행 범위)          스레드 1개   간격 8B       간격 64B     간격 128B
  P코어 2개 (cpu2·cpu4, 다른 코어)      390~498     1437~2341     398~455      387~447 (한 번 829)
  E코어 2개 (cpu16·cpu20, 다른 클러스터) 412~472     1708~2457     418~477      417~464
  P코어+E코어 (cpu2·cpu16)              408~437     1552~1898     431~445      435~448
  같은 P코어의 두 하드웨어 스레드(cpu2·3) 414~465     897~905      1035~1056    1035~1045
```

- 다른 코어끼리면 **간격 8B(같은 라인)일 때 스레드 2개가 스레드 1개보다 3~6배 느렸다.** 64B로 떼면 스레드 1개와 같은 시간에 2배의 일을 한다. ⚠ 칸의 "멀티스레드 카운터가 단일보다 느림"이다.
- 이 호스트에서는 64B와 128B의 차이가 노이즈 범위였다(128B 한 번의 829ms는 다른 실행과 동떨어진 값).
- **같은 코어의 두 하드웨어 스레드(SMT)에서는 false sharing 효과가 없었다.** 둘이 L1을 공유해 라인이 오갈 곳이 없다. 대신 한 코어의 실행 자원을 나눠 써서 간격과 무관하게 약 2배 걸렸다. 벤치마크를 어떤 CPU 쌍에서 돌렸는지가 결론을 뒤집을 수 있다.
- 비원자적 `volatile long` 증가(`(*c)++`, 1억 번)로 같은 실험을 하면, 다른 코어끼리는 간격과 무관하게 109~173ms로 뚜렷한 차이가 없었다. 반대로 같은 코어의 두 하드웨어 스레드에서는 8B가 1746~1757ms, 64B가 181~184ms로 약 10배 차이가 났다.
  - 해석(미확인): 일반 저장은 저장 버퍼에 들어가고 같은 스레드의 다음 읽기는 저장 버퍼에서 값을 받는다(store-to-load forwarding). 그래서 라인 소유권을 기다리는 일이 드물었다는 해석이다. 같은 코어 안의 10배는 원인을 이 실험으로 가리지 못했다 [?].
  - 결론은 좁게 적는다: **원자적 갱신(lock 접두 명령) — Java `AtomicLong`·`LongAdder` 칸·락 변수 — 에서는 다른 코어 간 false sharing이 크게 보였다.**

### 실험 4: false sharing — Java 21

```java
AtomicLongArray arr = new AtomicLongArray(64);
// 스레드1: arr.incrementAndGet(0)  스레드2: arr.incrementAndGet(1)   → 8바이트 간격
// 스레드1: arr.incrementAndGet(16) 스레드2: arr.incrementAndGet(32)  → 128바이트 간격
static class Two  { volatile long a; volatile long b; }                     // 필드가 붙어 있다
static class TwoC { @jdk.internal.vm.annotation.Contended volatile long a;
                    @jdk.internal.vm.annotation.Contended volatile long b; }   // 필드마다 패딩
```

`eclipse-temurin:21-jdk`(21.0.12), `--cpus=2 --cpuset-cpus=2,4`, `-XX:-RestrictContended --add-exports java.base/jdk.internal.vm.annotation=ALL-UNNAMED`, 각 2천만 번, 6회(3회는 사실 점검 재실행):

```text
  스레드 1개                414~477 ms
  배열 간격 8B   1292~3272 ms  |  간격 128B   424~556 ms (한 번 877)
  필드 붙음      1561~2352 ms  |  @Contended  410~596 ms

  필드 오프셋(sun.misc.Unsafe.objectFieldOffset)
  Two   a@16  b@24     ← 8바이트 차이, 같은 라인
  TwoC  a@144 b@280    ← 136바이트 차이, @Contended가 앞뒤로 패딩을 넣었다
  (-XX:-RestrictContended 없이 돌리면 TwoC도 a@16 b@24 — 애노테이션이 무시됐다)
```

- Java에서도 같은 라인이면 3~7배 느렸다. `@Contended`를 붙이자 스레드 1개 수준으로 돌아왔다.
- `@Contended`는 JDK 내부 애노테이션이다. HotSpot 플래그 `RestrictContended`(기본 true)가 켜져 있으면 신뢰된 클래스 밖에서는 무시된다. 패딩 폭은 `ContendedPaddingWidth`(기본 128바이트)다(OpenJDK 21 `src/hotspot/share/runtime/globals.hpp`).
- JDK 자신은 `LongAdder`의 칸(`Striped64.Cell`)에 `@Contended`를 붙여 둔다(OpenJDK 21 `Striped64.java`). 사용자 코드는 보통 플래그를 바꾸기보다 `LongAdder`를 쓰거나 스레드별로 따로 센다.

## 쓰이는 자료구조·알고리즘

- **의사 LRU(tree-PLRU)**(🔧): 집합 안 교체를 N−1비트 트리로 근사. 정확한 LRU의 구현은 [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)(해시맵 + 이중 연결 리스트) — 연관도가 큰 하드웨어 캐시는 그 비용 때문에 근사를 쓰기도 한다(Drepper §3.3.5).
- **인덱스 비트 해싱**(🔧): 상위 비트를 섞어 집합·버킷 몰림을 피한다. [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md) · [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) · [data-structure/29-open-addressing](../../data-structure/29-open-addressing/2-summary.md)(2의 거듭제곱 표 + 마스크)
- **비트 연산으로 주소 분해**: 인덱스 = `(addr >> 6) & (sets-1)`. [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md)
- **캐시 라인 패딩**: Disruptor 링 버퍼의 시퀀스 패딩 [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md), `LongAdder`·`ConcurrentHashMap`의 카운터 칸 [data-structure/29-concurrent-data-structures](../../data-structure/29-concurrent-data-structures/2-summary.md), MCS 락이 캐시 라인 핑퐁을 피하는 법 [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md)

## 적용 — 풀어나가는 법

1. **증상 A — 스레드를 늘렸더니 더 느리다.**
   - 스레드별로 따로 쓰는 필드·배열 칸이 메모리에서 붙어 있는지 본다. 후보: 스레드별 통계 카운터 배열 `long[] perThread`, 한 객체 안의 여러 `volatile long` 필드, 연달아 만든 `AtomicLong` 객체들(필드는 참조일 뿐이고 증가하는 `value`는 각 객체 안에 있다 — 객체끼리 가까이 놓였는지는 주소를 확인해야 한다), 워커마다의 진행 위치.
   - 확인: 같은 작업을 스레드 1개 vs 2개로 돌려 총 처리량을 비교한다. 칸 간격을 64B 이상으로 벌린 판과 비교한다(실험 3·4).
   - 측정 CPU를 고정한다. 같은 코어의 하드웨어 스레드 쌍(이 호스트 cpu2·cpu3)에서는 false sharing이 안 보인다.

```bash
lscpu -e=CPU,CORE,CACHE         # 어떤 CPU 번호가 같은 코어(=L1 공유)인지
cat /sys/devices/system/cpu/cpu2/cache/index0/shared_cpu_list    # 0-1처럼 나오면 그 둘이 L1 공유
```

2. **고친다.**

```java
// 전: 스레드 i가 counts[i]를 증가 → 8개 칸이 한 라인
AtomicLongArray counts = new AtomicLongArray(nThreads);

// 후 1: 공유 합계가 목적이면 LongAdder (칸 분산 + @Contended)
LongAdder total = new LongAdder();

// 후 2: 스레드 로컬로 세고 끝에 합친다 — 공유 쓰기 자체를 없앤다
long local = 0; for (...) local++; total.add(local);

// 후 3: 배열을 쓴다면 칸 간격을 벌린다 (128B = long 16개)
AtomicLongArray padded = new AtomicLongArray(nThreads * 16);  // 스레드 i는 i*16 칸
```

3. **증상 B — 특정 크기(1024·2048·4096…)에서만 갑자기 느리다.**
   - 행 길이·구조체 크기·버퍼 정렬이 4KB 등 2의 거듭제곱 배수인지 본다.
   - 확인: 크기를 조금(64B) 바꿔 다시 잰다. 크게 빨라지면 충돌 미스를 강하게 의심한다(실험 1·2 — 시간만으로는 어느 층의 미스인지 확정하지 못한다).
   - 고친다: 행 길이에 패딩(1024 → 1040), 여러 배열을 같은 4KB 경계에 정렬하지 않기, 블록 단위 처리.

## 장애 시나리오와 대처

### 1. 멀티스레드 통계 카운터가 단일 스레드보다 느리다

- **현상**: 요청 수·바이트 수를 워커 스레드별로 세도록 바꿨는데 처리량이 오히려 떨어졌다.
- **보이는 형태**: CPU 사용률은 올랐는데 초당 처리량은 그대로이거나 감소. 스레드 덤프에는 락 대기가 없다(`RUNNABLE`).
- **원인**: 스레드별 칸(`AtomicLongArray`의 인접 칸, 한 객체의 인접 `volatile long` 필드, 가까이 놓인 `AtomicLong` 객체들의 `value`)이 같은 64B 라인에 있다. 원자적 증가마다 라인이 코어 사이를 오간다. 이 호스트에서 3~6배(C), 3~7배(Java) 느려졌다.
- **대처**: `LongAdder`, 스레드 로컬 누적 후 합산, 칸 간격 128B. 고친 뒤 스레드 수별 처리량 곡선으로 확인한다.

### 2. 행렬·이미지 크기가 1024일 때만 유난히 느리다

- **현상**: 1000×1000 처리는 빠른데 1024×1024에서 몇 배 느리다. 크기는 2.4%밖에 안 늘었다.
- **보이는 형태**: 크기별 처리 시간 그래프에 2의 거듭제곱 지점마다 뾰족한 봉우리.
- **원인**: 행 길이 4096B → 열 방향 접근이 한두 집합에 몰리는 충돌 미스(실험 2에서 4.7~6.4배, 11번 실험 2에서 N=1000 2.3배 vs N=1024 9~10배).
- **대처**: 행 길이에 64B 패딩, 루프를 행 방향으로, 블록 단위 처리.

### 3. 벤치마크 결론이 다른 기계에서 뒤집혔다

- **현상**: 개발 PC에서 "패딩은 효과 없다"고 결론 냈는데, 운영 서버에서는 패딩 판이 몇 배 빨랐다.
- **보이는 형태**: 같은 JMH·자체 벤치마크인데 기계마다 결론이 다르다.
- **원인**: 스레드 두 개가 같은 물리 코어의 하드웨어 스레드에 배정되면 L1을 공유해 false sharing이 안 보인다(실험 3: cpu2·cpu3에서 8B가 64B보다 오히려 빨랐다). 다른 코어에 배정되면 크게 보인다.
- **대처**: 코어 배치를 고정하고 "다른 코어 쌍", "같은 코어 쌍"을 따로 잰다. 결과에 CPU 번호와 토폴로지를 적는다.

### 4. "패딩을 넣었는데 효과가 없다"

- **현상**: 필드 사이에 `long p1..p7`을 넣었지만 여전히 느리다.
- **보이는 형태**: 패딩 전후 처리량이 같다.
- **원인**: 필드 배치는 JVM 재량이다(JLS는 필드 순서를 메모리 순서로 보장하지 않는다 [?]). 실제 오프셋을 보지 않고 소스 순서를 믿었다.
- **대처**: 오프셋을 확인한다(실험 4처럼 `Unsafe.objectFieldOffset`, 또는 JOL 같은 도구). 배열 칸 간격·`LongAdder`처럼 배치가 확실한 방법을 쓴다.

## 핵심 문장

- 캐시는 주소를 태그·인덱스·오프셋으로 나눈다. 인덱스로 집합을 고르고, 그 집합의 N칸만 동시에 비교한다.
- 집합 연관 캐시에서는 용량이 남아도 한 집합의 칸 수를 넘으면 미스가 난다. 이 호스트 L1(12-way)에서 4096B 간격 라인은 12개까지 히트, 13개부터 미스였다.
- 2의 거듭제곱 간격 중 인덱스 비트를 바꾸지 않는 큰 간격(이 L1에서는 4096B의 배수)은 한 집합에 몰린다. 64B 간격처럼 인덱스 비트를 바꾸는 간격은 집합을 차례로 돈다. 64B만 어긋나게 해도 풀린다. 상위 비트를 섞는 해싱이 같은 처방이다.
- write-back 캐시는 쓰기를 모았다가 주로 라인이 나갈 때 기록한다. 교체 정책은 구현마다 다르다 — 연관도가 크면 정확한 LRU 대신 의사 LRU 같은 근사가 쓰일 수 있고(Drepper §3.3.5), 이 CPU의 정책은 확인하지 못했다.
- 캐시 라인은 코어 간 공유의 단위다. 서로 다른 변수라도 같은 라인을 다른 코어가 원자적으로 갱신하면 라인이 오가 3~7배 느려졌다(이 호스트).
- false sharing은 L1을 공유하는 같은 코어의 하드웨어 스레드끼리는 보이지 않는다. 측정할 때 CPU 배치를 적는다.

## 관련 주제·근거

- 선행: [11-memory-hierarchy-and-locality](../11-memory-hierarchy-and-locality/2-summary.md)
- 후속: [13-latency-numbers](../13-latency-numbers/2-summary.md) · [14-cache-coherence-and-memory-ordering](../14-cache-coherence-and-memory-ordering/2-summary.md)(MESI·RFO — false sharing의 메커니즘) · [20-multicore-and-numa](../20-multicore-and-numa/2-summary.md)
- 다른 영역
  - [os/10-paging-and-tlb](../../os/10-paging-and-tlb/2-summary.md) — TLB도 연관 캐시다
  - [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md) — 캐시 라인 핑퐁, MCS 락
  - [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md) · [29-concurrent-data-structures](../../data-structure/29-concurrent-data-structures/2-summary.md) · [10-lru-cache](../../data-structure/10-lru-cache/2-summary.md) · [05-hashmap](../../data-structure/05-hashmap/2-summary.md)
  - [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md) · [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md)
- 교재·문서·소스
  - CS:APP 3판 6.4 Cache Memories(6.4.1 Generic Cache Memory Organization, 6.4.2 Direct-Mapped, 6.4.3 Set Associative, 6.4.4 Fully Associative, 6.4.5 Issues with Writes, 6.4.6 Anatomy of a Real Cache Hierarchy, 6.4.7 Performance Impact of Cache Parameters) · 6.5 · 6.6 — 절 제목은 목차 PDF로 확인 <https://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf>, 본문 미확인
  - Drepper 2007 — §3.3.1 Associativity(그림 3.5~3.7, 표 3.1), §3.3.3 Write Behavior(write-through·write-back), §3.3.5 Other Details(가상·물리 주소, LRU), §6.4.1 Concurrency Optimizations(false sharing, 그림 6.10·6.11, 변수 분리 권고) <https://people.freebsd.org/~lstewart/articles/cpumemory.pdf>
  - Wikipedia "Pseudo-LRU"(tree-PLRU·bit-PLRU, 근사가 틀리는 예) <https://en.wikipedia.org/wiki/Pseudo-LRU>
  - C. Maurice, N. Le Scouarnec, C. Neumann, O. Heen, A. Francillon, "Reverse Engineering Intel Last-Level Cache Complex Addressing Using Performance Counters" <https://cmaurice.fr/pdf/raid15_maurice.pdf> (저자 PDF로 확인, 학회명 RAID 2015는 PDF 본문에 표기 없음 [?])
  - OpenJDK 21: `java/util/HashMap.java` `hash()` 주석 · `java/util/concurrent/atomic/Striped64.java`(`@Contended` Cell) · `src/hotspot/share/runtime/globals.hpp`(`ContendedPaddingWidth` 128, `EnableContended`, `RestrictContended` true) <https://github.com/openjdk/jdk21u>
- 실험 목록(환경: i7-13700HX, Linux 7.0.0-34, gcc 13.3.0 `-O2`, JDK 21.0.12 컨테이너 `--cpus=2 --cpuset-cpus=2,4`, 측정 중 클록 약 0.8~0.9GHz)
  - 실험 1 `stride.c` (1): K=4~64, stride 4096 vs 4160 포인터 사슬, cpu2, 3회
  - 실험 2 `stride.c` (2): 1024행 열 방향 합, 행 길이 1024 vs 1040 int, 3회
  - 실험 3 `fshare_atomic.c`(원자적 `lock addq`, 2천만 번) · `fshare.c`(비원자 `volatile`, 1억 번): 간격 8·64·128B, 코어 쌍 4종, 2~5회(+사실 점검 재실행: 원자적 cpu2·4 2회, cpu2·3 1회, cpu16·20 1회)
  - 실험 4 `FalseSharing.java` · `Offsets.java`: `AtomicLongArray` 간격, 인접 필드 vs `@Contended`, 필드 오프셋(플래그 유무), 6회
