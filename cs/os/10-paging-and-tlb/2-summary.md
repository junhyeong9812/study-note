# os/10-paging-and-tlb — 주소를 4 KB 조각으로 번역하는 표와 그 표의 캐시 — 정리 (힌트)

## 해결하는 문제

기초는 원고 [foundations/memory-management](../../foundations/memory-management/README.md) §8(페이지와 오프셋)·§9(페이지 테이블)·§10(요구 페이징)·§11(페이지 폴트)·§12(TLB)·§14.3~14.4(TLB·CAM)에 있다.\
요약: 가상 주소를 고정 크기 **페이지**로 쪼개고, 페이지 번호를 **페이지 테이블**로 물리 프레임 번호로 바꾼다. 그 번역 결과를 **TLB**에 캐시한다.

세그먼테이션(09번)은 크기가 제각각이라 외부 단편화가 남았다. 페이징은 모든 조각을 같은 크기로 만들어 이 문제를 없앤다. 대신 새 문제가 둘 생긴다.

```text
  문제                                     이 노트의 답
  페이지 테이블이 너무 크다                     다단계 페이지 테이블 (x86-64 4단계)
  메모리 접근 1번에 테이블 조회가 여러 번 붙는다   TLB (번역 결과 캐시), 큰 페이지로 TLB 범위 넓히기
```

쉬운 예: 전화번호부다.
- 한 권에 모든 번호를 넣으면 책이 너무 두껍다. 대부분 빈 줄이다.
- 그래서 "지역 → 동 → 번지" 순서로 얇은 책 여러 권으로 나눈다. 사람이 안 사는 동은 책을 만들지 않는다.
- 자주 거는 번호는 휴대폰 즐겨찾기(TLB)에 둔다. 즐겨찾기에 없으면 책 여러 권을 넘겨야 한다.

똑같은 구조다.\
페이지 테이블은 여러 단계의 표이고, TLB는 그 결과를 담은 작은 즐겨찾기다.

실무 예:
- 수십 GB 힙에서 해시맵을 무작위로 조회하는 서비스가, 계산량에 비해 느리다. 원인 중 하나가 TLB 미스다.
- Redis 문서는 THP(투명 대형 페이지)를 끄라고 권한다. 문서가 드는 이유는 fork 뒤 쓰기 때 큰 페이지 단위로 복사가 일어나 지연과 메모리가 는다는 것이다. 이 2 MB 복사는 리눅스 5.8 이전 커널의 동작이다(아래 장애 2).

## 동작·원리

### 주소 한 개의 분해 — x86-64 4단계

```text
  48비트 가상 주소 (4단계 페이지 테이블, 4 KB 페이지)

   47      39 38      30 29      21 20      12 11         0
  +----------+----------+----------+----------+------------+
  | PGD 인덱스 | PUD 인덱스 | PMD 인덱스 | PTE 인덱스 |  오프셋      |
  |  9비트     |  9비트     |  9비트     |  9비트     |  12비트      |
  +----------+----------+----------+----------+------------+
      512개      512개      512개      512개      4096바이트

  CR3 --> [PGD 표] --> [PUD 표] --> [PMD 표] --> [PTE 표] --> 물리 프레임 + 오프셋
          (4 KB)       (4 KB)       (4 KB)       (4 KB)
```

- 각 단계의 표는 512칸이고 칸 하나가 8바이트다. 표 하나가 정확히 4 KB, 즉 페이지 하나다.
- 리눅스 x86-64 상수: `PTRS_PER_PGD/PUD/PMD = 512`, `PUD_SHIFT 30`, `PMD_SHIFT 21`, `P4D_SHIFT 39`(arch/x86/include/asm/pgtable_64_types.h).
- 리눅스는 5단계 계층(PGD → P4D → PUD → PMD → PTE)을 정의한다. 하드웨어가 4단계면 P4D는 접혀(folded) 건너뛴다(Documentation/mm/page_tables.rst).
- 표의 이름 "PTE"는 원래 "항목 하나"였지만 지금은 **맨 아래 표 전체**를 가리킨다(page_tables.rst).
- 프로세스마다 자기 PGD가 있다. `task_struct → mm_struct → pgd`로 이어진다(page_tables.rst). CR3가 현재 프로세스의 PGD를 가리킨다.

  - *PFN(page frame number)*: 물리 주소를 페이지 크기로 나눈 번호다. 4 KB 페이지면 물리 주소의 12번 비트 위쪽이다(page_tables.rst).

### 왜 여러 단계인가 — 크기 계산

```text
  단일(선형) 페이지 테이블
    32비트, 4 KB 페이지:  2^20 항목 × 4 B = 4 MB   (프로세스마다! OSTEP 20)
    48비트, 4 KB 페이지:  2^36 항목 × 8 B = 512 GB (불가능)

  다단계 페이지 테이블 (작은 프로그램: 코드 한 곳, 힙 한 곳, 스택 한 곳)
    PGD 1장 + 쓰는 곳마다 PUD·PMD·PTE 몇 장 = 수십 KB 수준 (예시)
```

- 가상 주소 공간은 대부분 비어 있다. 다단계 표는 **빈 구간을 윗단계에서 "없음" 한 칸으로 표시**하고 아래 표를 만들지 않는다(page_tables.rst, OSTEP 20).
- 대가: 번역 한 번에 표를 여러 번 읽는다. 4단계면 TLB 미스 한 번에 메모리 읽기가 최대 4번 붙는다. 그래서 TLB가 필수다.

### 페이지 테이블 항목(PTE)에 든 것

```text
  63   62 ...        12  11..9   8     7     6     5     4    3    2    1    0
  +----+--------------+-------+-----+-----+-----+-----+----+----+----+----+----+
  | NX |     PFN      | SW    | G   |PSE* | D   | A   |PCD |PWT | U  | RW | P  |
  +----+--------------+-------+-----+-----+-----+-----+----+----+----+----+----+
  (* 4 KB PTE 칸에서는 비트 7 = PAT. PFN은 비트 51..12이고, 52..62는 소프트웨어·보호 키(PKEY) 등 다른 용도)
```

| 비트 | 이름 | 뜻 (arch/x86/include/asm/pgtable_types.h) |
|---|---|---|
| 0 | Present | 물리 프레임이 있다. 0이면 접근 시 페이지 폴트 |
| 1 | RW | 쓰기 가능 |
| 2 | User | 유저 모드 접근 가능. 0이면 커널 전용 |
| 5 | Accessed | CPU가 접근하면 켠다. 교체 정책(12번)이 쓴다 |
| 6 | Dirty | CPU가 쓰면 켠다. 내보낼 때 디스크에 써야 하는지 판단 |
| 7 | PSE | PMD·PUD 칸에서: 이 칸이 아래 표가 아니라 **큰 페이지**를 직접 가리킨다(PMD면 2 MB, PUD면 1 GB). 맨 아래 PTE(4 KB) 칸에서는 같은 비트가 PAT(메모리 타입)다(`_PAGE_BIT_PAT 7 /* on 4KB pages */`) |
| 8 | Global | 모든 주소 공간에서 유효한 TLB 항목(커널 매핑) |
| 63 | NX | 실행 금지 |

- Present가 0이라는 것은 "디스크에 있다"만 뜻하지 않는다. 아직 한 번도 안 건드린 페이지(요구 페이징), 스왑으로 나간 페이지, 파일에서 읽어 올 페이지 모두 0이다. 커널은 VMA(09번)와 PTE의 나머지 비트로 구분한다.

> 참고: 원고 §9의 "유효 비트는 프레임 위치가 하드인지 메모리인지 나타낸다"는 한 경우만 말한다. Present=0은 위처럼 "아직 할당 전"일 수도 있다.\
> 참고: 원고 §8의 "페이지 크기는 보통 1~8KB"는 아키텍처마다 다르다. x86-64 기본 페이지는 4 KB이고 큰 페이지 2 MB·1 GB가 있다. ARM64 리눅스는 빌드 때 4 KB·16 KB·64 KB 중 고른다(arch/arm64/Kconfig `ARM64_4K/16K/64K_PAGES`).

### 요구 페이징 — 건드려야 생긴다

로컬 재현(예시, 리눅스 7.0). 64 MB를 `mmap`한 뒤 절반만 썼다. `/proc/self/pagemap`의 Present 비트(63번)를 셌다.

```text
  pages=16384 present=0        after mmap 64MB:     VmRSS  1616 kB
  pages=16384 present=8192     after touching 32MB: VmRSS 34384 kB
  pagemap entry of first page: 0x8180000000000000   <- 비트 63(present)·56(exclusive)·55(soft-dirty), PFN=0
```

- `mmap`은 VMA만 만든다. 페이지 테이블 칸은 처음 건드릴 때 페이지 폴트로 채워진다.
- PFN이 0으로 나온 것은 권한 때문이다. 리눅스 4.2부터 `CAP_SYS_ADMIN`이 없으면 pagemap의 PFN을 0으로 가린다. 이유는 Rowhammer 공격 방지다(Documentation/admin-guide/mm/pagemap.rst).

### TLB — 번역 결과의 캐시

```text
  가상 주소 --> [ TLB ] -- 히트 --> 물리 주소 (추가 메모리 읽기 없음)
                  |
                 미스
                  v
          페이지 테이블 워크 (x86: 하드웨어가 CR3부터 4단계를 읽음)
                  |
                  +-- Present=1 --> TLB에 채움 --> 명령 재실행
                  +-- Present=0 --> 페이지 폴트 --> 커널 처리 --> 명령 재실행
```

- x86은 TLB 미스를 **하드웨어가** 처리한다(hardware-managed). MIPS 같은 RISC는 트랩으로 OS가 처리한다(software-managed, OSTEP 19).
- TLB는 몇십~몇천 칸짜리 연관 캐시다. 가상 페이지 번호를 여러 칸과 동시에 비교한다(원고 §14.4 CAM 그림).

  - *TLB 도달 범위(reach)*: TLB 항목 수 × 페이지 크기. 이 범위 안의 메모리는 번역 비용 없이 접근한다.
  - 예) 2,048칸(예시) × 4 KB = 8 MB, 같은 칸 수 × 2 MB = 4 GB.

**문맥 전환과 TLB.** TLB 항목은 "어느 주소 공간의" 번역인지 구분해야 한다.
- 방법 1: 전환마다 TLB를 비운다(flush). 단순하지만 전환 직후 미스가 쏟아진다.
- 방법 2: 항목에 주소 공간 ID(ASID, x86은 PCID)를 붙인다(OSTEP 19). x86 리눅스는 CPU마다 최근 주소 공간 6개까지 PCID로 구분한다(arch/x86/include/asm/tlbflush.h `TLB_NR_DYN_ASIDS 6`).

**TLB 슛다운.** 한 스레드가 `munmap`·`mprotect`로 매핑을 바꾸면, 같은 주소 공간을 쓰는 **다른 CPU의 TLB**에도 옛 번역이 남아 있을 수 있다. 커널은 그 CPU들에 인터럽트(IPI)를 보내 비우게 한다(arch/x86/mm/tlb.c `flush_tlb_multi`).

로컬 재현(예시, 리눅스 7.0). 메인 스레드가 4 KB를 `mmap` → 쓰기 → `munmap`을 2만 번 반복했다. 같은 프로세스에서 다른 CPU에 올라가 도는 스레드 수만 바꿨다.

```text
  돌고 있는 다른 스레드 0개:  TLB shootdown 인터럽트 +142      (시스템 전체)   3.86 µs/회
  돌고 있는 다른 스레드 4개:  TLB shootdown 인터럽트 +80,134                  5.32 µs/회
  돌고 있는 다른 스레드 8개:  TLB shootdown 인터럽트 +159,675                 11.15 µs/회
```

- 슛다운 수가 "munmap 횟수 × 다른 CPU의 스레드 수"에 가깝게 늘었다. 한 번의 `munmap` 비용도 3배 가까이 늘었다.
- `/proc/interrupts`의 `TLB:` 줄("TLB shootdowns")로 볼 수 있다.

### 큰 페이지 — TLB 도달 범위를 512배로

```text
  4 KB 페이지:  PGD -> PUD -> PMD -> PTE -> 4 KB 프레임      (TLB 1칸 = 4 KB)
  2 MB 페이지:  PGD -> PUD -> PMD(PSE=1) -> 2 MB 프레임       (TLB 1칸 = 2 MB, 단계 하나 적음)
  1 GB 페이지:  PGD -> PUD(PSE=1) -> 1 GB 프레임
```

- THP(투명 대형 페이지)의 이점은 두 가지다(Documentation/admin-guide/mm/transhuge.rst).
  - 2 MB 구간마다 페이지 폴트가 한 번뿐이다. 커널 진입이 512분의 1로 준다.
  - TLB 한 칸이 훨씬 넓은 메모리를 덮어 미스가 줄고, 미스 자체도 한 단계 짧아 빨라진다.
- 대가: 페이지 폴트 때 비울(0으로 채울) 크기가 커진다(transhuge.rst). 5.8 이전 커널은 fork 뒤 쓰기 때 복사할 크기도 2 MB였다. 2 MB 연속 물리 메모리를 구하려고 압축(compaction)하며 멈출 수 있다(`defrag` 설정).
- THP 모드는 `/sys/kernel/mm/transparent_hugepage/enabled`의 `always`·`madvise`·`never`다. 이 환경은 `madvise`였다. 이때는 `madvise(MADV_HUGEPAGE)`를 준 영역만 큰 페이지를 쓴다.

로컬 측정(예시, 리눅스 7.0 · i7-13700HX, CPU 3 고정). 캐시 라인 하나씩 무작위로 2천만 번 읽었다. 앞 읽기 값이 다음 주소에 섞여 들어가 읽기가 하나씩 차례로 일어난다.

```text
   256 MB  4 KB 페이지   167.4 ns/접근   touch 때 minor fault 65,536   AnonHugePages      0 kB
   256 MB  THP(2 MB)     136.9 ns/접근   touch 때 minor fault    128   AnonHugePages 262144 kB
     4 MB  4 KB 페이지    75.0 ns/접근
     4 MB  THP            64.7 ns/접근
```

- 256 MB 전체가 큰 페이지로 잡힌 실행에서 접근당 약 18% 빨랐다. 폴트 수는 65,536 → 128로 정확히 512분의 1이었다.
- 같은 실험의 다른 실행과 1 GB 실행에서는 일부만 큰 페이지로 잡혔다(`AnonHugePages`가 전체보다 작음). 2 MB 연속 물리 메모리를 매번 얻지는 못한다.
- 이 수치에는 캐시 미스 비용이 함께 들어 있다. TLB 효과는 두 줄의 **차이**로만 읽는다. perf가 막힌 환경(`perf_event_paranoid=4`)이라 dTLB 미스를 직접 세지는 못했다.

## 쓰이는 자료구조·알고리즘

- **기수 트리(radix tree) = 다단계 페이지 테이블** — 주소 비트를 9비트씩 끊어 각 단계의 인덱스로 쓴다. 비교 없이 비트로 길을 찾는 트라이다. 빈 서브트리는 만들지 않아 희소한 키 공간에 맞다. [data-structure/20-radix-trie](../../data-structure/20-radix-trie/2-summary.md) · [data-structure/09-trie](../../data-structure/09-trie/2-summary.md)
- **연관 캐시(TLB)** — 가상 페이지 번호를 키로 여러 칸을 동시에 비교하는 하드웨어 캐시다. 캐시 조직(집합 연관·교체)은 [architecture/README](../../architecture/README.md)의 `12-cache-organization`(미작성)에서 다룬다.
- **LRU 근사** — TLB·페이지 교체 모두 "최근에 안 쓴 것"을 내보내려 한다. PTE의 Accessed 비트가 근사 LRU의 재료다(12번). [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)
- **해시 테이블(역 페이지 테이블)** — 물리 프레임마다 한 칸을 두고 (프로세스, 가상 페이지)로 해시 검색하는 방식도 있다(OSTEP 20 "Inverted Page Tables"). [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 큰 메모리를 쓰는 프로세스는 큰 페이지를 검토한다

```c
#include <sys/mman.h>
size_t sz = 256UL << 20;                                   /* 256 MB (예시) */
void *p = mmap(NULL, sz, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
madvise(p, sz, MADV_HUGEPAGE);        /* THP=madvise 모드에서 이 구간만 큰 페이지 후보 */
```

- JVM: `-XX:+UseTransparentHugePages`는 힙에 `MADV_HUGEPAGE`를 준다(OpenJDK `globals_linux.hpp` "Use MADV_HUGEPAGE for large pages"). `-XX:+AlwaysPreTouch`는 시작 때 힙을 미리 건드려 운영 중 폴트를 없앤다.
- PostgreSQL: 공유 버퍼가 크면 huge pages로 오버헤드가 준다(PostgreSQL 문서 "Managing Kernel Resources", `huge_pages`).
- Redis: fork(RDB·AOF 재작성)를 쓰므로 THP를 끄라고 권한다(Redis 문서 "Diagnosing latency issues").
- 같은 기술이 워크로드에 따라 득도 실도 된다. 측정한 뒤 켠다.

### 2. 접근 패턴을 바꾼다

- 무작위 조회가 많은 큰 자료구조는 자주 쓰는 부분을 모은다(핫 데이터 분리, 작은 캐시 앞단).
- 포인터를 따라가는 구조(연결 리스트, 객체 그래프) 대신 연속 배열을 쓰면 캐시와 TLB가 함께 좋아진다.

### 3. 진단 명령

```bash
# THP 설정과 사용량
cat /sys/kernel/mm/transparent_hugepage/enabled /sys/kernel/mm/transparent_hugepage/defrag
grep -E 'AnonHugePages|PageTables|HugePages_' /proc/meminfo
grep AnonHugePages /proc/<pid>/smaps_rollup

# 페이지 폴트 누적 (minor = 디스크 없이 처리, major = 디스크 읽기)
ps -o pid,min_flt,maj_flt,rss,cmd -p <pid>
/usr/bin/time -v ./app 2>&1 | grep -E 'page faults'

# TLB 슛다운 인터럽트 (CPU별 누적)
grep TLB /proc/interrupts

# 페이지 단위 상태 (Present·swap 비트. PFN은 CAP_SYS_ADMIN 필요)
#   /proc/<pid>/pagemap : 가상 페이지마다 64비트 항목

# 하드웨어 카운터 (권한이 되면)
perf stat -e dTLB-load-misses,dTLB-loads ./app
```

- `perf`는 `perf_event_paranoid` 설정에 따라 일반 사용자에게 막힐 수 있다. 이 환경은 4라 막혀 있었다.

## 장애 시나리오와 대처

### 1. TLB 미스 폭증 → 큰 힙 무작위 접근이 느리다

- **현상**: 수십 GB 힙에서 해시 조회·그래프 탐색을 하는 서비스가 CPU는 바쁜데 처리량이 기대보다 낮다. 데이터가 커질수록 급격히 느려진다.
- **보이는 형태**
  - `perf stat`의 `dTLB-load-misses` 비율이 높다(권한이 될 때).
  - `AnonHugePages`가 0이다(THP 미사용).
  - 로컬 측정처럼 같은 작업이 4 KB 페이지에서 THP보다 느리다(256 MB에서 약 18%, 예시).
- **원인**: 작업 집합이 TLB 도달 범위(수 MB)보다 훨씬 크다. 접근마다 TLB 미스와 4단계 테이블 워크가 붙는다.
- **대처**
  - 큰 페이지: THP `madvise` + JVM `-XX:+UseTransparentHugePages`, 또는 hugetlbfs(명시 예약).
  - 접근 지역성을 높인다(연속 배열, 핫 데이터 분리).
  - 효과는 반드시 지연 분포로 측정한다. 아래 2번의 부작용이 있다.

### 2. THP 때문에 지연 스파이크·메모리 증가

- **현상**: THP를 `always`로 켠 뒤 가끔 수십~수백 ms 멈춤이 생긴다. 또는 fork 뒤 메모리가 크게 는다.
- **보이는 형태**
  - `defrag`가 `always`면 큰 페이지를 못 구할 때 **직접 회수·압축하며 멈춘다**(transhuge.rst "will stall on allocation failure").
  - Redis: `BGSAVE` 직후 지연 급등과 RSS 증가. 리눅스 5.8 이전 커널에서는 fork 뒤 몇 번의 쓰기가 큰 페이지 단위 복사를 일으켜 거의 전체 메모리를 복사한다(Redis 문서).
- **원인**: 큰 페이지는 할당 단위가 512배다. 연속 물리 메모리가 부족하면 확보 비용이 크다.
  - 5.8 이전: 공유된 THP에 쓰면 2 MB를 통째로 복사했다.
  - 5.8부터: PMD를 쪼개고 4 KB 한 장만 복사한다(커밋 3917c80280c9 "thp: change CoW semantics for anon-THP", mm/huge_memory.c `do_huge_pmd_wp_page`의 `__split_huge_pmd` → `VM_FAULT_FALLBACK`). 05번과 같은 내용이다. 대신 쪼갠 구간은 THP 이점을 잃는다.
  - 그래서 최신 커널에서 THP가 Redis에 주는 부담은 주로 할당·압축 멈춤과 메모리 부풀림 쪽이다(`always`는 "may end up allocating more memory resources", transhuge.rst).
- **대처**
  - `enabled=madvise`로 필요한 프로그램만 쓰게 한다.
  - `defrag`를 `defer`·`madvise`로 둬 직접 압축 멈춤을 피한다.
  - fork를 쓰는 저장소(Redis)는 문서 권고대로 THP를 끈다.

### 3. TLB 슛다운 폭주 → 멀티스레드 프로그램의 커널 시간 급증

- **현상**: 스레드가 많은 서버에서 `sy`(커널 시간)가 높고, 특정 할당·해제가 느리다.
- **보이는 형태**
  - `grep TLB /proc/interrupts`의 값이 초당 크게 증가한다.
  - `strace -c -f`에서 `munmap`·`madvise`·`mprotect` 호출이 많다.
  - 로컬 재현: 다른 CPU에서 도는 스레드가 8개일 때 `munmap` 2만 번에 슛다운 인터럽트 약 16만 번, 한 번 비용 3.86 → 11.15 µs(예시).
- **원인**: 주소 공간을 공유하는 모든 CPU의 TLB를 비워야 매핑 변경이 안전하다. 할당기가 메모리를 자주 반환하거나(`MADV_DONTNEED`), JIT·GC가 권한을 자주 바꾸면 IPI가 쏟아진다.
- **대처**
  - 할당기의 반환 빈도를 낮춘다(glibc `M_TRIM_THRESHOLD`·`M_MMAP_THRESHOLD` — 설정하면 동적 문턱이 꺼져 고정된다(11번), jemalloc·tcmalloc의 decay 설정).
  - 짧게 쓰고 버리는 큰 버퍼는 재사용 풀로 바꾼다.

### 4. 페이지 테이블 자체가 메모리를 먹는다

- **현상**: 프로세스 수백 개가 큰 공유 메모리를 매핑한 DB 서버에서, 사용자 메모리 합보다 가용 메모리가 훨씬 적다.
- **보이는 형태**: `/proc/meminfo`의 `PageTables`가 수 GB다.
- **원인**: 공유 메모리라도 프로세스마다 자기 페이지 테이블을 가진다. 4 KB 페이지로 N GB를 매핑하면 프로세스마다 약 N × 2 MB의 PTE 표가 필요하다(4 KB 페이지 512개를 PTE 표 한 장(4 KB)이 덮으므로 매핑 크기의 1/512).
- **대처**: 큰 페이지(hugetlbfs)를 쓰면 PMD 한 칸이 2 MB를 덮어 PTE 표가 필요 없다. PostgreSQL 문서가 큰 `shared_buffers`에 huge pages를 권하는 이유다.

## 핵심 문장

- 페이징은 주소를 고정 크기 페이지로 쪼개 외부 단편화를 없앤다. 대가는 큰 페이지 테이블과 번역 비용이다.
- x86-64는 48비트 주소를 9·9·9·9·12비트로 나눠 4단계 표를 걷는다. 각 표는 512칸 × 8 B = 4 KB이고, 빈 구간은 윗단계에서 잘라 메모리를 아낀다. 다단계 페이지 테이블은 기수 트리다.
- PTE의 Present=0은 "디스크에 있음"만이 아니다. 아직 안 건드린 페이지도 0이다. 매핑은 처음 건드릴 때 페이지 폴트로 채워진다.
- TLB는 번역 결과의 연관 캐시다. 도달 범위 = 칸 수 × 페이지 크기라서 큰 페이지(2 MB)가 범위를 512배로 넓힌다.
- 매핑을 바꾸면 다른 CPU의 TLB를 IPI로 비워야 한다(슛다운). 멀티스레드에서 잦은 `munmap`은 비싸다.
- THP는 TLB 미스와 폴트를 줄이지만, 압축 멈춤이라는 부작용이 있다. 리눅스 5.8 이전 커널은 fork 뒤 2 MB 단위 복사도 일어났다. 측정 후 켠다.

## 관련 주제·근거

- 선행: [09-address-space](../09-address-space/2-summary.md) — VMA와 SIGSEGV 판정. [architecture/README](../../architecture/README.md) — `12-cache-organization`(연관 캐시), 미작성.
- 후속·연결
  - [07-threads-and-context-switch](../07-threads-and-context-switch/2-summary.md) — CR3 교체와 PCID.
  - [03-interrupts-traps-faults](../03-interrupts-traps-faults/2-summary.md) — 페이지 폴트 경로(minor·major).
  - [11-heap-allocation](../11-heap-allocation/2-summary.md) — 할당기의 메모리 반환과 슛다운.
  - [12-swapping-and-page-replacement](../12-swapping-and-page-replacement/2-summary.md) — Accessed 비트와 교체 정책.
  - [14-mmap-and-page-cache](../14-mmap-and-page-cache/2-summary.md) — 파일 매핑.
  - [35-virtualization-hypervisor](../35-virtualization-hypervisor/2-summary.md) — 중첩 페이지 테이블.
  - [systems/thrashing](../../systems/thrashing/2-summary.md) — 작업 집합이 메모리를 넘을 때.
- Kernel 문서·소스
  - Documentation/mm/page_tables.rst — PGD·P4D·PUD·PMD·PTE, 접기(folding), PFN, 다단계의 이유 <https://docs.kernel.org/mm/page_tables.html>
  - arch/x86/include/asm/pgtable_types.h — `_PAGE_BIT_PRESENT 0` … `_PAGE_BIT_GLOBAL 8`, `_PAGE_BIT_NX 63`
  - arch/x86/include/asm/pgtable_64_types.h — `PTRS_PER_* 512`, `P4D_SHIFT 39`, `PUD_SHIFT 30`, `PMD_SHIFT 21`
  - arch/x86/include/asm/tlbflush.h `TLB_NR_DYN_ASIDS 6` · arch/x86/mm/tlb.c `flush_tlb_multi`(슛다운 IPI)
  - mm/huge_memory.c `do_huge_pmd_wp_page()` — 공유 THP 쓰기 폴트의 `fallback:` 경로(`__split_huge_pmd` 후 `VM_FAULT_FALLBACK`, v7.0 소스). 커밋 3917c80280c9 "thp: change CoW semantics for anon-THP"(v5.8에 포함, GitHub compare로 확인)
  - Documentation/admin-guide/mm/transhuge.rst — THP 이점 두 가지, `enabled`·`defrag` 모드, khugepaged <https://docs.kernel.org/admin-guide/mm/transhuge.html>
  - Documentation/admin-guide/mm/pagemap.rst — 비트 63 present, 4.2+ 비특권 PFN 0 <https://docs.kernel.org/admin-guide/mm/pagemap.html>
  - arch/arm64/Kconfig — `ARM64_4K_PAGES`·`ARM64_16K_PAGES`·`ARM64_64K_PAGES`
- OpenJDK `src/hotspot/os/linux/globals_linux.hpp` — `UseTransparentHugePages`("Use MADV_HUGEPAGE for large pages")
- Redis 문서 "Diagnosing latency issues — Latency induced by transparent huge pages" <https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/>
- PostgreSQL 문서 "Managing Kernel Resources — Linux Huge Pages" <https://www.postgresql.org/docs/current/kernel-resources.html>
- 교재: OSTEP 18 "Introduction to Paging", 19 "Translation Lookaside Buffers"(hardware/software-managed, ASID), 20 "Advanced Page Tables"(선형 4 MB, 다단계, 역 페이지 테이블) · CS:APP 3판 9.6 Address Translation(9.6.2 TLB, 9.6.3 Multi-Level Page Tables), 9.7.1 Core i7 Address Translation
- 로컬 재현(리눅스 7.0 · i7-13700HX): pagemap으로 본 요구 페이징(present 0 → 8192), 4 KB vs THP 무작위 접근과 폴트 수, 멀티스레드 `munmap`의 TLB 슛다운 수
