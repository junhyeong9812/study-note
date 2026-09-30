# os/11-heap-allocation — malloc 뒤에서 일어나는 일: free list·단편화·buddy·slab — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

기초는 원고 [memory-management §4·§11·§14](../../foundations/memory-management/README.md)다.\
§4는 가상 주소 공간의 힙 세그먼트, §11은 "다이나믹 힙", §14는 자바·파이썬 힙 구조를 다룬다.\
이 노트는 그 힙 안에서 **누가 어떻게 자리를 떼어 주고 돌려받는지**를 다룬다.

프로그램은 크기를 미리 모르는 메모리를 실행 중에 달라고 한다.\
커널은 메모리를 **페이지(보통 4KiB) 단위**로만 준다.\
32바이트짜리 노드를 만들 때마다 커널에 한 페이지씩 달라고 하면 두 가지가 망가진다.

```text
  요청                     커널에 직접 달라고 하면
  malloc(32) x 100만 번     시스템 콜 100만 번 (느림)
                           페이지 100만 개 = 약 4GB (32MB면 될 것을)
```

그래서 사용자 공간에 **할당자(allocator)**가 있다.\
커널에서 큰 덩어리를 받아 두고, 작은 요청은 그 안에서 잘라 준다.

  - *할당자*: 큰 메모리 덩어리를 들고, 요청마다 조각을 떼어 주고, 돌려받은 조각을 다시 쓰는 관리자다. C에서는 `malloc`/`free`를 구현한 라이브러리(glibc의 ptmalloc 등)다.

쉬운 예: 도매로 떼 온 원단을 손님 주문 크기대로 잘라 파는 가게다.
- 원단 한 롤(페이지 여러 장)을 도매상(커널)에서 받는다.
- 손님(`malloc`)마다 필요한 길이만 잘라 준다.
- 돌려받은 자투리(`free`)는 다음 손님에게 다시 판다. 옆 자투리와 붙어 있으면 이어 붙인다.

똑같은 구조다.\
커널은 도매상, glibc `malloc`은 가게, 프로그램은 손님이다.\
커널 안에도 같은 구조가 한 번 더 있다. 물리 페이지를 나누는 **buddy 할당자**와, 커널 객체를 나누는 **slab 할당자**다.

실무 예:
- 자바 서버에서 큰 요청을 처리한 뒤 힙 사용량은 줄었는데 프로세스 RSS가 안 줄어든다.
- C 서비스가 가끔 `free(): double free detected in tcache 2`를 찍고 죽는다(exit 134).
- 커널 로그에 `page allocation failure: order:4`가 찍힌다. 빈 메모리 총량은 넉넉한데도 그렇다.

## 동작·원리

### 1. 세 층의 할당자

```text
  +---------------------------------------------------+
  | 애플리케이션: new / malloc(32) / free(p)             |
  +---------------------------------------------------+
         |  작은 요청          | 큰 요청 (>= mmap 문턱, 기본 128KiB)
         v                    v
  +---------------------------+   +-------------------+
  | glibc malloc (ptmalloc2)  |   | mmap(익명) 직접    |
  |  arena 안의 free list·bin |   | free하면 munmap    |
  +---------------------------+   +-------------------+
         | main arena는 brk/sbrk로 늘림, 끝이 비면 줄임 (스레드용 arena는 mmap한 heap)
         v
  ============= 시스템 콜 경계 =============================
  +---------------------------------------------------+
  | 커널: 페이지 폴트 때 물리 페이지를 붙임                |
  |   buddy 할당자 — 2^order 페이지 단위 (order 0~10)   |
  |   slab(SLUB) — 커널 객체(inode, dentry, task...)용   |
  +---------------------------------------------------+
```

- 작은 `malloc`은 arena의 힙에서 잘라 준다.
  - main arena: 프로그램 브레이크 아래 영역이다. 모자라면 `brk`로 늘린다. `brk`가 실패하면 `mmap`으로 대신 받는다(malloc/malloc.c `sysmalloc`).
  - 스레드용 arena: `mmap`으로 만든 heap에서 잘라 준다. `brk`와 무관하다(아래 적용 1).
- **128KiB 이상**이고 free list로 채울 수 없는 요청은 `mmap`으로 따로 받는다(mallopt(3) `M_MMAP_THRESHOLD`, 기본 128*1024).
- 이 문턱은 기본 상태에서 **동적**이다. 문턱보다 큰(최대 64비트에서 32MiB) mmap 블록을 free하면 문턱이 그 크기로 올라간다(mallopt(3)).
  - `M_TRIM_THRESHOLD`·`M_TOP_PAD`·`M_MMAP_THRESHOLD`·`M_MMAP_MAX` 중 하나라도 설정하면 동적 조정이 꺼져 문턱이 고정된다. 같은 이름의 `MALLOC_*_` 환경 변수로 설정해도 같다(mallopt(3) Note, malloc.c `no_dyn_threshold`).
- `brk`나 `mmap`으로 받은 것은 **가상 주소 예약**이다. 물리 페이지는 처음 건드릴 때 페이지 폴트로 붙는다(10번 페이징).

  - *프로그램 브레이크(program break)*: 데이터 세그먼트의 끝 주소다. `brk`/`sbrk`로 이 끝을 밀어 올리거나 내려 힙 크기를 바꾼다.
  - *arena*: 자기 뮤텍스를 가진 힙 하나다. 스레드가 많으면 glibc가 경합을 줄이려 arena를 더 만든다.

로컬 재현(예시, 리눅스 7.0 · glibc 2.39): `malloc(100)`과 `malloc(200*1024)`을 `strace`로 보면 이렇다.

```text
brk(NULL)                               = 0x5e728af02000
brk(0x5e728af23000)                     = 0x5e728af23000      <- 작은 요청: 힙을 132KiB 늘림
mmap(NULL, 208896, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0) = 0x73c0ea39d000   <- 큰 요청
munmap(0x73c0ea39d000, 208896)          = 0                    <- free하면 바로 커널에 반납
```

- 힙을 요청보다 크게(0x21000 = 132KiB) 늘렸다. `M_TOP_PAD`(기본 128KiB)만큼 여유를 더 받기 때문이다(mallopt(3)). glibc 빌드에서 이 기본값은 `sysdeps/generic/malloc-machine.h`의 `DEFAULT_TOP_PAD 131072`다(`malloc/malloc.c`의 `(0)`은 그것이 없을 때의 대체값).

### 2. 힙 안의 모습 — 청크와 free list

```text
  힙 (주소 증가 →)
  +--------+--------+--------+--------+--------+-----------------+
  | 사용 A | 빈 32  | 사용 B | 빈 64  | 사용 C |   top (미사용)    |
  +--------+--------+--------+--------+--------+-----------------+
               |                  |                    ^ 브레이크
               +---- free list ---+
  각 청크 앞에 크기 헤더가 있다 → free(p)는 p 바로 앞 헤더를 보고 크기를 안다
```

- 할당자는 빈 청크들을 **free list**로 연결해 둔다. 빈 청크 자신의 공간에 다음 포인터를 적는다.
- `malloc(n)`: free list에서 맞는 청크를 찾는다. 크면 **분할(split)**한다.
- `free(p)`: 청크를 free list에 돌려놓는다. 옆 청크도 비었으면 **병합(coalesce)**한다.
- 어떤 청크를 고를지가 **배치 정책**이다(OSTEP 17).

| 정책 | 방법 | 대가 |
|---|---|---|
| best fit | 요청에 가장 가까운 크기 | 전체를 훑는다. 아주 작은 자투리가 남는다 |
| worst fit | 가장 큰 청크 | 전체를 훑는다. 연구상 단편화가 심하다 |
| first fit | 처음 맞는 청크 | 빠르다. 목록 앞쪽에 작은 조각이 쌓인다 |
| next fit | 지난번 멈춘 곳부터 first fit | 앞쪽 쏠림을 줄인다 |

glibc는 목록 하나가 아니라 **크기별 여러 목록(bin)**을 쓴다(malloc/malloc.c).

```text
  free(p) 가 들어가는 곳 (glibc 2.39, 64비트, 대략)
  tcache    스레드별, 크기별 64개 목록, 목록당 7개까지, 약 1KiB 이하 — 락 없이 가장 빠름
  fastbin   작은 크기(기본 128바이트 이하), 병합하지 않음
  unsorted  나머지가 먼저 들어가는 임시 목록
  small bin  bin마다 한 크기(64비트 1KiB 미만) — 정렬 불필요
  large bin  크기 구간별 목록, 크기순 정렬 — 병합된 큰 청크를 찾는다
```

- tcache 상수: `TCACHE_MAX_BINS 64`, `TCACHE_FILL_COUNT 7`(malloc/malloc.c).
- fastbin 상한 `M_MXFAST` 기본은 `64*sizeof(size_t)/4`, 64비트에서 128바이트다(mallopt(3)).

### 3. 단편화 — 비었는데 못 준다

```text
  외부 단편화: 빈 총합은 96인데 64짜리를 못 준다
  +------+ 빈32 +------+ 빈32 +------+ 빈32 +
  | 사용 |      | 사용 |      | 사용 |      |
  +------+------+------+------+------+------+

  내부 단편화: 33바이트 요청에 48바이트 청크 → 15바이트는 아무도 못 쓴다
  +----------------------+-------+
  | 요청 33              | 낭비15 |
  +----------------------+-------+
```

- **외부 단편화**: 빈 공간이 잘게 흩어져 큰 요청을 못 채운다.
- **내부 단편화**: 정렬·크기 등급 때문에 청크 안쪽이 남는다.

RSS가 안 줄어드는 이유는 외부 단편화의 사용자 공간 판이다.

```text
  brk 힙은 "끝(top)"에서만 줄일 수 있다
  +------+------+------+------+------+------+------+
  | 빈   | 빈   | 빈   | 빈   | 빈   | 빈   | 사용 |  <- 마지막 하나가 살아 있으면
  +------+------+------+------+------+------+------+     브레이크를 못 내린다
```

- glibc는 힙 **꼭대기**의 연속 빈 공간이 `M_TRIM_THRESHOLD`(기본 128KiB)를 넘을 때만 `brk`를 내린다(mallopt(3)). 동적 mmap 문턱이 올라가면 trim 문턱도 그 2배로 함께 올라간다(같은 문서, 동적 조정이 켜진 기본 상태에서만).
- `malloc_trim()`은 glibc 2.8부터 모든 arena의 **페이지 전체가 빈** 청크까지 `madvise`로 돌려준다(malloc_trim(3)).
- 페이지마다 살아 있는 청크가 하나라도 있으면 그 페이지는 못 돌려준다.

로컬 재현(예시, 리눅스 7.0 · glibc 2.39): 256바이트를 10만 번 할당한 뒤 두 방식으로 해제했다. `after trim`은 `malloc_trim(0)` 직후다.

```text
  [A] 마지막 하나만 남기고 전부 free        [B] 짝수 번째만 free (체크무늬)
  start          RSS=1340 kB               start          RSS=1340 kB
  after malloc   RSS=29000 kB              after malloc   RSS=29000 kB
  after free     RSS=29000 kB   <- 그대로  after free     RSS=29000 kB
  after trim      RSS=2444 kB    <- 반납    after trim     RSS=29000 kB  <- 반납 못 함
```

- [A]는 top 아래가 통째로 비었다. `free`만으로는 안 줄었지만 `malloc_trim(0)`이 돌려줬다.
- [B]는 절반이 비었는데 모든 페이지에 산 청크가 섞여 있다. trim도 못 돌려준다.

### 4. 커널 쪽 — buddy와 slab

**buddy 할당자**는 물리 페이지를 2의 거듭제곱 묶음으로 관리한다.

```text
  order:   0     1     2     3    ...   10
  크기:   4KiB  8KiB 16KiB 32KiB  ...  4MiB   (4KiB 페이지 기준)

  16KiB 요청, order-2 목록이 비었다 →
  [        32KiB (order 3)        ]
  [ 16KiB (준다) ][ 16KiB (buddy) ]  → buddy는 order-2 목록으로

  해제할 때: 내 buddy도 비었으면 합쳐서 order 3으로 되돌린다
  buddy 주소 = 내 주소 XOR (블록 크기)  ← 계산으로 바로 찾는다
```

- 가장 큰 order는 `MAX_PAGE_ORDER`, 기본 10이다(include/linux/mmzone.h). 그래서 `/proc/buddyinfo`에 열이 11개다.
- 병합 상대를 주소 계산으로 찾으니 병합이 싸다. 대신 2의 거듭제곱으로 올림하니 내부 단편화가 생긴다(OSTEP 17).

```text
$ cat /proc/buddyinfo        (예시, 리눅스 7.0)
Node 0, zone   Normal 676081 316703  58795   9756   1532    580    134     14      0      0      0
                      ^order0                                                      ^order8~10 이 0
```

- 높은 order 칸이 0이면 큰 연속 물리 메모리를 바로 줄 수 없다(proc_buddyinfo(5)). 커널은 이때 회수·압축(compaction)을 시도한다.

**slab 할당자**는 같은 크기의 커널 객체를 모아 둔 캐시다.

```text
  kmem_cache "dentry"  (객체 192바이트라고 하면 — 예시)
  slab = 페이지 1개 이상
  +------+------+------+------+------+------+
  | obj  | obj  | free | obj  | free | free |   ← slab 안의 free 목록
  +------+------+------+------+------+------+
  객체 크기가 전부 같다 → 외부 단편화가 없다, 해제된 자리를 그대로 재사용
```

- 자주 만들고 버리는 커널 객체(inode, dentry, task_struct 등)를 크기별로 분리한다(OSTEP 17, Bonwick의 slab).
- 현재 리눅스 소스의 slab 구현은 SLUB 하나다(mm/Kconfig `config SLUB`이 `def_bool y`, `SLUB_TINY`는 그 최소 메모리 설정 옵션).
- `/proc/meminfo`의 `Slab`·`SReclaimable`·`SUnreclaim`으로 크기를 본다. `/proc/slabinfo`와 `slabtop`은 root만 읽을 수 있다(작성 환경에서 `/proc/slabinfo`는 모드 `0400 root`).

> 참고: 원고 §11의 "LinkedList 10만 건 → 페이지 폴트 수백 번, ArrayList 수십 번, 10배 이상"은 출처가 없는 수치다. 이미 메모리에 올라온(상주) 힙을 순회할 때 늘어나는 것은 주로 **캐시·TLB 미스**다. 페이지 폴트는 처음 건드리거나 스왑에서 읽어 올 때 생긴다(10번, 12번).

## 쓰이는 자료구조·알고리즘

- **free list(연결 리스트)** — 빈 청크를 연결한다. 빈 청크의 본문 자리에 포인터를 적어 추가 메모리가 들지 않는다. [data-structure/02-linked-list](../../data-structure/02-linked-list/2-summary.md)
- **크기별 분리 목록(segregated list)** — glibc bin, tcache, 커널 slab이 모두 이 방식이다. 크기 등급으로 목록을 바로 고른다.
- **buddy 시스템** — 2의 거듭제곱 분할·병합. buddy 주소를 XOR로 계산한다. 구현 연습은 [data-structure/35-allocator](../../data-structure/35-allocator/2-summary.md)에 있다.
- **범프 포인터(bump pointer)** — 포인터를 밀기만 하는 할당. HotSpot의 TLAB(스레드별 할당 버퍼)가 이 방식이다(HotSpot Glossary). 해제는 GC가 영역 단위로 한다.
- **경계 태그(boundary tag)** — 청크 앞(과 뒤)에 크기를 적어, 이웃 청크를 O(1)로 찾아 병합한다.

## 적용 — 풀어나가는 법

### 1. "메모리가 안 줄어든다" — 어느 층인지 먼저 가른다

```text
  RSS 큼
   ├─ 자바 힙이 큰가?      → jstat / GC 로그 (language/10·11)
   ├─ 힙 밖(native)인가?  → 13번 NMT, pmap
   │    └─ glibc arena가 많은가? → pmap에서 64MiB 근처 anon 영역 여러 개
   └─ free했는데 RSS 그대로? → 단편화 / trim 문턱 (malloc_trim, M_TRIM_THRESHOLD)
```

```bash
# 프로세스 메모리 영역 — [heap]과 큰 anon 영역을 본다
pmap -x <pid> | sort -k3 -n | tail
grep -E 'VmRSS|RssAnon|RssFile' /proc/<pid>/status

# brk/mmap 호출을 직접 본다
strace -f -e trace=brk,mmap,munmap,madvise -p <pid>

# 커널 쪽: 연속 물리 메모리 여유, slab 크기
cat /proc/buddyinfo
grep -E 'Slab|SReclaimable|SUnreclaim' /proc/meminfo
```

- glibc의 스레드용 arena는 heap 여러 개를 이어 붙여 만든다. heap 하나는 최대 `HEAP_MAX_SIZE`(64비트에서 64MiB)로 `mmap`된다(malloc/arena.c). heap이 차면 `new_heap`으로 새 heap을 만들어 `heap->prev`로 잇는다(malloc/malloc.c `sysmalloc`). arena 전체 크기에는 이런 상한이 없다.
- 그래서 pmap에 64MiB 근처 영역이 여럿 보이면 arena를 의심한다. 여러 arena일 수도, 한 arena의 여러 heap일 수도 있다. (glibc 2.35+ hugetlb 튜너블을 쓰면 heap 크기가 `hp_pagesize × 4`로 바뀐다 — arena.c `heap_max_size`.)
- arena 개수 상한은 기본 **CPU 수 × 8**(64비트)이다(malloc/malloc.c `NARENAS_FROM_NCORES`). `MALLOC_ARENA_MAX` 환경 변수로 줄일 수 있다(mallopt(3)). 줄이면 메모리는 덜 쓰고 락 경합은 늘어난다.

### 2. 자바에서 보이는 모습

```java
// 자바 객체: JVM 힙 안에서 TLAB 범프 포인터로 할당 — malloc을 거치지 않는다
byte[] a = new byte[1024];

// direct buffer: JDK 구현에서 Unsafe.allocateMemory → HotSpot os::malloc → glibc malloc
ByteBuffer d = ByteBuffer.allocateDirect(1 << 20);
```

- OpenJDK 소스에서 direct buffer는 `UNSAFE.allocateMemory`로 받고(`Direct-X-Buffer.java.template`), HotSpot의 `Unsafe_AllocateMemory0`은 `os::malloc`을 부른다(`unsafe.cpp`).
- 그래서 direct buffer·스레드가 많은 자바 프로세스는 glibc arena 문제를 그대로 겪는다. 힙 크기로는 설명되지 않는 RSS가 여기서 나온다(13번).

### 3. C에서 메모리 오류를 잡는다

```c
char *p = malloc(32);
free(p);
free(p);                 /* double free */
/* glibc 2.39: "free(): double free detected in tcache 2" → abort() → SIGABRT */

int *q = malloc(16);
free(q);
printf("%d\n", q[0]);    /* use-after-free — 평소엔 조용히 쓰레기 값을 읽는다 */
```

로컬 재현(예시, 리눅스 7.0 · glibc 2.39 · gcc 13.3):

```text
$ ./dfree
free(): double free detected in tcache 2
중지됨 (코어 덤프됨)          exit=134  (128 + SIGABRT 6)

$ ./uaf_plain                 # 그냥 컴파일
-1961939471                   exit=0    ← 아무 에러 없이 쓰레기 값

$ gcc -g -fsanitize=address uaf.c && ./a.out
ERROR: AddressSanitizer: heap-use-after-free on address 0x502000000010 ...
READ of size 4 ... in main uaf.c:3
freed by thread T0 here: ...  exit=1
```

- glibc는 알아챈 힙 손상을 `malloc_printerr`로 알리고 `abort`한다(malloc/malloc.c). 메시지 종류: `double free detected in tcache 2`, `double free or corruption (fasttop)`, `(top)`, `(out)`, `(!prev)` 등.
- **알아채지 못한** 손상은 조용히 지나간다. 한참 뒤 무관한 `malloc` 안에서 SIGSEGV로 터질 수 있다. 그래서 테스트·CI에서 AddressSanitizer를 켠다.

## 장애 시나리오와 대처

### 1. 단편화로 RSS가 안 줄어듦

- **현상**: 트래픽 피크 뒤 한가해졌는데 프로세스 RSS가 피크 수준에 머문다. 컨테이너 메모리 그래프가 계단식으로만 오른다.
- **보이는 형태**
  - 애플리케이션이 센 사용량(자바 힙 used, 캐시 크기)은 줄었는데 `VmRSS`는 그대로다.
  - `pmap -x`에 `[heap]`이나 64MiB 근처 anon 영역이 여럿 크게 남아 있다.
- **원인**
  - 해제된 청크가 살아 있는 청크 사이사이에 흩어져 페이지를 통째로 비우지 못한다(외부 단편화).
  - brk 힙은 꼭대기에서만 줄어든다. 꼭대기에 오래 사는 청크가 하나 있으면 아래가 비어도 못 줄인다.
  - 스레드가 많아 arena가 CPU×8개까지 늘었고, arena마다 여유 공간을 쥐고 있다.
- **대처**
  - `MALLOC_ARENA_MAX`를 2~4 정도로 줄여 본다(값은 예시 — 측정하며 정한다).
  - 긴 수명 객체와 짧은 수명 객체를 다른 풀·arena로 나눈다. 원고 §11의 "다이나믹 힙"이 이 발상이다.
  - 주기적으로 `malloc_trim(0)`을 부르거나, jemalloc·tcmalloc으로 바꿔 비교한다.
  - 새는 게 아닌지(누수) 먼저 확인한다. 단편화는 일정 수준에서 멈추고, 누수는 계속 오른다.

### 2. double free → `SIGABRT`(exit 134)

- **현상**: 특정 에러 경로에서만 프로세스가 죽는다.
- **보이는 형태**: stderr에 `free(): double free detected in tcache 2` 또는 `double free or corruption (...)`. 종료 코드 134, 코어 덤프.
- **원인**: 같은 포인터를 두 번 `free`했다. 흔한 예는 에러 처리 경로와 정상 정리 경로가 둘 다 `free`하는 경우다.
- **대처**
  - `free(p); p = NULL;`로 두 번째 `free`를 무해하게 만든다(`free(NULL)`은 아무 일도 안 한다 — malloc(3)).
  - 소유권을 한 곳으로 정한다(누가 해제하는가).
  - ASan으로 재현하면 첫 `free`와 두 번째 `free`의 스택이 함께 나온다.

### 3. use-after-free → 한참 뒤 엉뚱한 곳에서 `SIGSEGV`(exit 139)

- **현상**: 크래시 스택이 매번 다르고, 대개 `malloc`·`free` 내부다.
- **보이는 형태**: exit 139, 또는 `malloc(): corrupted top size` 같은 glibc 메시지 뒤 abort.
- **원인**: 해제된 청크에 계속 쓰면 free list 포인터(청크 본문에 적혀 있다)를 덮는다. 다음 할당이 망가진 포인터를 따라간다. 크래시 위치는 원인과 멀다.
- **대처**
  - `-fsanitize=address`로 재현한다. 첫 잘못된 접근에서 멈춘다.
  - 운영 코어 덤프만 있으면 크래시 지점보다 "그 청크를 누가 마지막으로 free했나"를 추적한다.
  - `MALLOC_PERTURB_`(mallopt(3) `M_PERTURB`)로 해제된 메모리를 특정 값으로 채워 증상을 앞당긴다.

### 4. 커널 고차(high-order) 할당 실패

- **현상**: 빈 메모리는 넉넉한데 드라이버·네트워크 쪽에서 할당 실패가 난다.
- **보이는 형태**: `dmesg`에 `page allocation failure: order:N` 경고. `/proc/buddyinfo`의 높은 order 칸이 0이다.
- **원인**: 물리 메모리가 order 0·1 조각으로 흩어져 2^N 연속 페이지가 없다(buddy의 외부 단편화).
- **대처**: 고차 연속 할당을 요구하는 설정(큰 버퍼·점보 프레임 등)을 줄인다. 커널의 회수·압축에 맡기되, 반복되면 커널 문서와 벤더 가이드를 본다.

## 핵심 문장

- 커널은 페이지 단위로만 준다. `malloc`은 그 위에서 작은 조각을 잘라 주고 돌려받는 사용자 공간 할당자다.
- glibc는 작은 요청은 arena 힙(main arena는 `brk`, 스레드용 arena는 `mmap`한 heap)에서, 128KiB 이상(기본 상태에서 동적 문턱)은 `mmap`으로 따로 받는다. mmap 블록은 `free`하면 바로 반납된다.
- 해제는 free list에 돌려놓는 것이지 커널에 돌려주는 것이 아니다. brk 힙은 꼭대기에서만 줄고, 페이지마다 산 청크가 섞이면 `malloc_trim`도 못 돌려준다.
- 커널 안에는 buddy(2^order 페이지, XOR로 짝 찾기)와 slab(같은 크기 객체 캐시)이 한 층 더 있다.
- double free는 glibc가 알아채면 `SIGABRT`(134)로 죽는다. 알아채지 못한 손상은 조용히 지나가 나중에 엉뚱한 곳에서 터진다. ASan으로 잡는다.

## 관련 주제·근거

- 원고: [foundations/memory-management](../../foundations/memory-management/README.md) — §4 가상 주소 공간, §11 페이지 폴트와 다이나믹 힙, §14 자바·파이썬 힙
- 선행
  - [09-address-space](../09-address-space/2-summary.md) — 힙 세그먼트와 프로그램 브레이크의 자리
  - [10-paging-and-tlb](../10-paging-and-tlb/2-summary.md)
  - [data-structure/35-allocator](../../data-structure/35-allocator/2-summary.md) — free list·buddy·bump를 직접 구현
- 후속·연결
  - [12-swapping-and-page-replacement](../12-swapping-and-page-replacement/2-summary.md) — 할당된 페이지가 메모리에서 밀려날 때
  - [13-oom-and-memory-limits](../13-oom-and-memory-limits/2-summary.md) — native 메모리·arena 때문에 컨테이너 limit을 넘을 때
  - [language/README](../../language/README.md) — `09-memory-management-models`(원고 있음), `10-garbage-collection`(미작성)
  - [reliability/README](../../reliability/README.md) — `37-memory-leak-and-heap-analysis`(RSS vs 힙). 미작성
- 교재
  - OSTEP 14 "Interlude: Memory API", 17 "Free-Space Management"(분할·병합, best/worst/first/next fit, segregated list, slab, buddy) <https://pages.cs.wisc.edu/~remzi/OSTEP/vm-freespace.pdf>
  - CS:APP 3판 9.9 "Dynamic Memory Allocation"
- man
  - malloc(3) — 기본 128KiB 문턱, arena, `free(NULL)` <https://man7.org/linux/man-pages/man3/malloc.3.html>
  - mallopt(3) — `M_MMAP_THRESHOLD`(128*1024, 동적, 상한 `4*1024*1024*sizeof(long)`), `M_TRIM_THRESHOLD`, `M_TOP_PAD`, `M_MXFAST`, `M_ARENA_MAX`, `M_PERTURB`, `M_CHECK_ACTION` <https://man7.org/linux/man-pages/man3/mallopt.3.html>
  - malloc_trim(3) — glibc 2.8부터 모든 arena의 빈 페이지 반납 <https://man7.org/linux/man-pages/man3/malloc_trim.3.html>
  - proc_buddyinfo(5) — order별 빈 블록 수 <https://man7.org/linux/man-pages/man5/proc_buddyinfo.5.html>
- 소스
  - glibc 2.39 `malloc/malloc.c` — `TCACHE_MAX_BINS 64`, `TCACHE_FILL_COUNT 7`, `NARENAS_FROM_NCORES`, `malloc_printerr` 메시지, `sysmalloc`(스레드 arena의 `new_heap`·`heap->prev`, `brk` 실패 시 `mmap` 대체), 1537행 small bin 설명·"maintain large bins in sorted order", `no_dyn_threshold` <https://sourceware.org/git/?p=glibc.git;a=blob;f=malloc/malloc.c;hb=refs/tags/glibc-2.39>
  - glibc 2.39 `malloc/arena.c` — `HEAP_MAX_SIZE`(= 2 × `DEFAULT_MMAP_THRESHOLD_MAX`), arena 상한 계산 · `sysdeps/generic/malloc-machine.h` — `DEFAULT_TOP_PAD 131072`
  - Linux `include/linux/mmzone.h` — `MAX_PAGE_ORDER 10` · `mm/Kconfig` — SLUB <https://github.com/torvalds/linux/blob/master/include/linux/mmzone.h>
  - OpenJDK `java/nio/Direct-X-Buffer.java.template`(`UNSAFE.allocateMemory`) · `hotspot/share/prims/unsafe.cpp`(`os::malloc`)
- HotSpot Glossary — TLAB <https://openjdk.org/groups/hotspot/docs/HotSpotGlossary.html>
- 로컬 재현(리눅스 7.0 · glibc 2.39 · gcc 13.3): brk vs mmap strace, 해제 방식별 RSS와 `malloc_trim`, double free 메시지·exit 134, ASan use-after-free
