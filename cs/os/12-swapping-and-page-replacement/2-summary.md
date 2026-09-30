# os/12-swapping-and-page-replacement — 메모리가 모자랄 때 누구를 내보내나: 스왑·교체 정책·작업 집합·스래싱 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

원고 [memory-management §10·§11·§14](../../foundations/memory-management/README.md)는 요구 페이징, 페이지 폴트, 희생 페이지(victim page)를 짧게 소개한다.\
이 노트는 그다음 질문을 다룬다. **물리 메모리가 꽉 찼을 때 어느 페이지를 내보내고, 그 선택이 틀리면 무슨 일이 생기나.**

프로세스들이 쓰려는 메모리의 합은 물리 메모리보다 클 수 있다.\
가상 메모리는 "당장 쓰는 페이지만 RAM에 두고 나머지는 디스크에 둔다"로 이 착각을 유지한다.

```text
  가상 주소 공간 합계  >  물리 메모리
  +---------------------------+
  | 프로세스 A (2GB)           |      RAM (예시 4GB)          디스크
  | 프로세스 B (3GB)           | -->  [자주 쓰는 페이지들]  <-> [스왑 영역 / 원본 파일]
  | 프로세스 C (1GB)           |
  +---------------------------+
```

그러려면 두 가지가 필요하다.
- **자리를 비우는 메커니즘**: 페이지를 디스크로 내보내고, 다시 필요할 때 읽어 온다(스왑).
- **누구를 내보낼지 고르는 정책**: 곧 다시 쓸 페이지를 내보내면 바로 다시 읽어 와야 한다.

쉬운 예: 책상(RAM)과 책장(디스크)이다.
- 책상에는 책을 몇 권만 펼쳐 둘 수 있다. 새 책을 펴려면 한 권을 책장에 꽂아야 한다.
- 오래 안 본 책을 꽂으면 괜찮다. 방금 보던 책을 꽂으면 곧 다시 꺼내야 한다.
- 지금 공부에 필요한 책(작업 집합)이 책상보다 많으면, 꽂고 꺼내기만 하다 공부를 못 한다. 이것이 **스래싱**이다.

똑같은 구조다.\
커널은 메모리가 모자라면 "최근에 덜 쓴" 페이지를 골라 내보낸다. 모두가 쓰는 페이지의 합이 RAM보다 크면 디스크 I/O만 하게 된다.

실무 예:
- 배치 작업이 돌자 서버 전체가 "멈춘 듯" 느려진다. SSH 입력도 몇 초씩 늦다. CPU 사용률은 낮다.
- 큰 로그 파일을 한 번 `cat`하거나 백업이 파일을 훑은 뒤 DB 응답이 느려진다. 자주 쓰던 캐시가 밀려났다.

## 동작·원리

### 1. 메커니즘 — 스왑 아웃과 스왑 인

```text
  페이지 테이블 엔트리(PTE)
  +---------+---------+------------------------------+
  | present | 기타    | present=1: 물리 프레임 번호      |
  |   bit   | 비트    | present=0: 스왑 위치(디스크 주소) |
  +---------+---------+------------------------------+

  접근 → present=0 → 페이지 폴트 → 커널:
     1) 빈 프레임을 구한다 (없으면 교체 정책으로 희생 페이지를 고른다)
     2) 희생 페이지가 dirty면 디스크에 쓴다
     3) 필요한 페이지를 디스크에서 읽어 온다   ← 이 동안 프로세스는 잠든다 (major fault)
     4) PTE를 present=1로 고치고 명령을 다시 실행한다
```

- 스왑 영역은 페이지 단위로 읽고 쓰는 디스크 공간이다(OSTEP 21.1).
- 파일에서 읽어 온 페이지(코드, 페이지 캐시)는 스왑이 필요 없다. 깨끗하면 버리고, 필요하면 원본 파일에서 다시 읽는다(14번).
- 스왑이 필요한 것은 **익명 페이지**(힙·스택처럼 파일 원본이 없는 페이지)다.
- 예외: shmem/tmpfs 페이지(`/dev/shm`, tmpfs 파일, SysV 공유 메모리, `MAP_SHARED|MAP_ANONYMOUS`)는 페이지 캐시에 있지만 뒤에 디스크 원본이 없다. 그래서 스왑으로 나간다. 커널도 이들을 익명 쪽 LRU에 둔다(include/linux/mm_inline.h `folio_is_file_lru` 주석, tmpfs(5)).

  - *major fault*: 디스크 I/O가 필요한 페이지 폴트다. 마이크로초가 아니라 밀리초가 걸릴 수 있다.
  - *minor fault*: 페이지가 이미 메모리 어딘가에 있어 PTE만 고치면 되는 폴트다.
  - *dirty 페이지*: 메모리에 올라온 뒤 수정된 페이지다. 내보내기 전에 디스크에 써야 한다.

**미리 비워 둔다.** 폴트가 날 때마다 교체하면 느리다. 리눅스는 워터마크를 두고 백그라운드 스레드가 미리 회수한다.

```text
  빈 메모리
    ^
    |  high  ------------ kswapd가 여기까지 채우면 잠든다
    |  low   ------------ 여기 밑으로 내려가면 kswapd를 깨운다
    |  min   ------------ 여기 밑이면 할당하는 스레드가 직접 회수 (direct reclaim) → 할당 지연
    +------------------------------------------------> 시간
```

- 워터마크 간격은 `vm.watermark_scale_factor`(기본 10 = 0.1%)로 정한다(kernel.org sysctl/vm).
- direct reclaim이 잦으면(`allocstall`) kswapd가 버스트를 못 따라가는 것이다(같은 문서).

### 2. 정책 — 누구를 내보내나

| 정책 | 내보내는 페이지 | 특징 |
|---|---|---|
| OPT (Belady) | 가장 먼 미래에 쓸 페이지 | 최적. 미래를 알아야 해서 실제로는 못 쓴다. 비교 기준용 |
| FIFO | 가장 먼저 들어온 페이지 | 간단. Belady 이상 현상이 있다 |
| Random | 무작위 | 최악의 패턴이 없다 |
| LRU | 가장 오래 안 쓴 페이지 | 지역성을 잘 따른다. 정확히 하려면 접근마다 기록해야 해서 비싸다 |
| CLOCK | 원형으로 돌며 use 비트 0인 페이지 | LRU의 근사. 하드웨어 use 비트 하나로 동작 |

**CLOCK — LRU의 근사.**

```text
        hand → [P1 use=1]              (시계 방향: P1 → P2 → ... → P6 → P1)
     [P6 use=0]      [P2 use=0]   <- P1을 0으로 지우고 넘어와 여기서 멈춘다. P2를 내보낸다
     [P5 use=1]      [P3 use=1]
            [P4 use=0]

  hand가 가리키는 페이지:
    use=1 → 0으로 지우고 다음으로 (한 번 더 기회)
    use=0 → 이 페이지를 내보낸다
```

- 페이지에 접근하면 하드웨어가 use 비트(reference 비트, x86의 accessed 비트)를 1로 켠다(OSTEP 22).
- 한 바퀴 도는 동안 다시 안 쓰인 페이지가 나간다. "최근에 안 쓴" 것을 싸게 고르는 방법이다.
- dirty 비트도 함께 보면 깨끗한 페이지를 먼저 내보낼 수 있다. 쓰기 I/O가 없어 싸다(OSTEP 22).

**Belady 이상 현상 — 프레임을 늘렸는데 폴트가 늘어난다.**\
참조열 `1,2,3,4,1,2,5,1,2,3,4,5`로 로컬 시뮬레이션(예시):

```text
          프레임 3   프레임 4
  FIFO    폴트 9     폴트 10   ← 늘렸는데 더 나빠짐
  CLOCK   폴트 9     폴트 10   ← 이 참조열에서는 CLOCK도 같다
  LRU     폴트 10    폴트 8
  OPT     폴트 7     폴트 6
```

- LRU와 OPT는 **스택 성질**이 있다. 크기 N+1 캐시의 내용이 크기 N 캐시의 내용을 항상 포함한다. 그래서 프레임을 늘려 나빠지는 일이 없다(OSTEP 22).
- FIFO는 스택 성질이 없다. 이 시뮬레이션에서는 CLOCK도 같은 이상을 보였다.

**스캔 오염 — LRU의 약점.**

```text
  캐시 49칸, 페이지 0~49를 순서대로 반복 접근 (looping sequential)
  LRU/FIFO/CLOCK: 매번 "곧 다시 쓸" 가장 오래된 페이지를 내보낸다 → 적중률 0%
  OPT:             97.5% (로컬 시뮬레이션, 예시)
```

- OSTEP 22도 "캐시 49, 50페이지 반복이면 LRU 적중률 0%"를 최악의 예로 든다.
- 한 번만 읽고 말 대량 데이터(백업, 로그 `cat`, 풀 스캔)가 들어와도 같다. 한 번 쓴 페이지가 "가장 최근"이 되어 자주 쓰던 페이지를 밀어낸다.
- 그래서 현대 알고리즘은 **스캔 저항성**을 넣는다. 예: ARC(OSTEP 22 요약절), 2Q와 리눅스의 변형 2Q 두 목록(OSTEP 23.2).

### 3. 리눅스의 실제 — 두 개의 CLOCK 목록

```text
  처음 폴트 --------------------+
                                v
                 +--------------+          +-------------+
  회수 <-------- |   inactive   | <-- 강등 -|   active    | <--+
  (꼬리부터)      +--------------+          +-------------+    |
                        |                                     |
                        +-------- 두 번째 접근 = 승격 ---------+
```

- 새 페이지는 **inactive** 목록 머리에 들어간다. 회수는 inactive 꼬리부터 한다.
- inactive에 있는 동안 **또 접근되면** active로 승격된다. active가 너무 커지면 꼬리를 inactive로 강등한다(mm/workingset.c 주석 "Double CLOCK lists").
- 한 번만 쓰고 마는 스캔 페이지는 inactive에서 바로 나간다. 두 번 이상 쓴 페이지는 active에서 보호된다.

로컬 장난감 시뮬레이션(예시): 캐시 40칸, 자주 쓰는 20페이지를 5번 돌린 뒤 한 번짜리 1000페이지 스캔을 넣었다.

```text
  스캔 직후 자주 쓰던 20페이지 적중: LRU 0/20, 두 목록 20/20
```

- **refault 거리**: 내보낸 페이지가 곧 다시 폴트되면, 커널은 "내보냈다가 다시 읽기까지의 접근 수"를 잰다. 이 값이 메모리에 들어갈 수 있는 크기면 그 페이지를 바로 active로 올린다(mm/workingset.c). `/proc/vmstat`의 `workingset_refault_*`가 이 횟수다.
- 리눅스 6.1에서 대안 구현 **Multi-Gen LRU(MGLRU)**가 선택 기능으로 들어왔다(kernelnewbies Linux 6.1). 빌드 설정에 따라 기본으로 켜진다(`CONFIG_LRU_GEN_ENABLED`, `/sys/kernel/mm/lru_gen/enabled`, kernel.org multigen_lru). 작성 환경(Ubuntu 24.04, 리눅스 7.0)은 `0x0007`(전부 켜짐)이었다.
- MGLRU가 켜진 커널은 위의 두 목록 대신 페이지를 **여러 세대(generation)**로 나눠 회수한다(kernel.org mm/multigen_lru "Evictable pages are divided into multiple generations"). 그래서 작성 환경에서 실제로 도는 것은 MGLRU 쪽이다. "한 번 쓴 페이지를 자주 쓴 페이지와 구분한다"는 발상은 같다.
- 익명 페이지(스왑 대상)와 파일 페이지(버리기만 하면 됨) 중 어느 쪽을 더 회수할지는 `vm.swappiness`가 정한다. 0~200, 기본 60이다. 100이면 두 I/O 비용을 같다고 본다(kernel.org sysctl/vm).

### 4. 작업 집합과 스래싱

```text
  작업 집합 W(t, Δ) = 최근 Δ 시간 동안 참조한 페이지들의 집합

  모든 프로세스의 작업 집합 합  ≤  RAM   → 폴트는 가끔, 정상
  모든 프로세스의 작업 집합 합  >  RAM   → 내보낸 페이지를 곧 다시 부른다
                                         → 폴트 → 디스크 대기 → CPU 놀고 → ... (스래싱)
```

- 작업 집합은 Denning(1968)의 모델이다. "지금 실제로 쓰고 있는 페이지들"이다.
- 스래싱은 메모리가 과하게 요구되어 **계속 페이징만 하는** 상태다(OSTEP 22.11).
- 옛 시스템은 **진입 제어(admission control)**로 대처했다. 일부 프로세스를 잠시 멈춰 나머지의 작업 집합이 들어가게 한다. 리눅스는 대신 OOM killer로 프로세스를 죽여 압력을 줄인다(OSTEP 22.11, 13번).

  - *스래싱(용어 대비)*: [systems/thrashing](../../systems/thrashing/2-summary.md)은 동적 배열이 늘었다 줄었다를 반복하는 **자료구조 재할당**의 스래싱이다. 이름은 같고, "경계 근처에서 비싼 일을 반복한다"는 모양도 같다. 대상은 다르다.

## 쓰이는 자료구조·알고리즘

- **CLOCK(원형 리스트 + 참조 비트)** — LRU의 근사. 접근마다 목록을 고치지 않고, 하드웨어가 켠 비트만 훑는다.
- **LRU 리스트** — 정확한 LRU는 해시 맵 + 이중 연결 리스트로 O(1)이다. 사용자 공간 캐시는 이렇게 만든다. [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md) 커널은 접근마다 목록을 고칠 수 없어 CLOCK·두 목록으로 근사한다.
- **두 목록(inactive/active) = 2Q 계열의 스캔 저항** — 한 번 본 것과 두 번 본 것을 나눈다.
- **작업 집합(슬라이딩 윈도)** — 최근 Δ 동안의 참조 집합.
- **OPT(Belady)** — 미래를 아는 오프라인 최적. 정책을 평가하는 기준선이다.

## 적용 — 풀어나가는 법

### 1. "서버가 멈춘 듯 느리다" — 스래싱인지 먼저 확인한다

```bash
# si/so: 초당 스왑 인/아웃. 둘 다 계속 0이 아니면 스왑이 돌고 있다. b: I/O 대기로 막힌 프로세스
vmstat 1

# 누적 카운터 — 두 번 찍어 차이를 본다
grep -E '^(pswpin|pswpout|pgmajfault|workingset_refault_anon|workingset_refault_file|allocstall_normal|pgscan_direct) ' /proc/vmstat

# 메모리 압력: full = idle이 아닌 모든 태스크가 메모리 때문에 동시에 멈춘 시간 비율
cat /proc/pressure/memory

# 어느 프로세스가 스왑으로 밀려났나 / major fault가 많은가
grep VmSwap /proc/<pid>/status
ps -o pid,maj_flt,min_flt,rss,comm -p <pid>
```

작성 환경에서 찍은 값(예시, 리눅스 7.0 — 스왑 8GB 중 7.9GB 사용 중이던 데스크톱):

```text
procs -----------memory---------- ---swap-- -----io---- -system-- -------cpu-------
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st gu
 6  0 8373656 1172936 2534760 9697996   12 35176    12 40424 134351 539054 15 10 75  1  0  0

/proc/pressure/memory
some avg10=0.02 avg60=0.19 avg300=0.09 total=825075596
full avg10=0.01 avg60=0.15 avg300=0.08 total=765472724
```

- `so`가 튀면 무언가를 스왑으로 내보내는 중이다. `si`가 계속 높으면 내보낸 것을 다시 읽는 중이다. 스왑을 통한 스래싱은 `si`와 `so`가 **둘 다 계속** 높은 모습이다.
- 스왑이 없어도 스래싱은 난다. 코드·파일 페이지를 버렸다가 곧 다시 읽는 경우다. 이때 `si`/`so`는 0이고, `bi`·`pgmajfault`·`workingset_refault_file`이 계속 높다.
- PSI의 `full`이 커질수록 스래싱에 가깝다. 문서는 `full`에 오래 머무는 워크로드를 스래싱으로 본다(kernel.org psi).
- PSI는 `/proc/pressure/`에 있다. cgroup v2에서는 cgroup마다 `memory.pressure`로도 본다(kernel.org psi).

### 2. 스캔 오염을 피한다

한 번만 읽을 대량 파일은 캐시에 남기지 않는다고 커널에 알린다.

```c
/* 다 읽은 구간은 캐시에서 버려도 된다고 알림 */
posix_fadvise(fd, 0, 0, POSIX_FADV_DONTNEED);
/* 순차로 읽을 것이라 알림 (미리 읽기 확대) */
posix_fadvise(fd, 0, 0, POSIX_FADV_SEQUENTIAL);
```

- `POSIX_FADV_DONTNEED`는 권고다. 리눅스는 그 구간의 캐시 페이지를 버리려 **시도**한다. 페이지 일부만 걸친 구간은 무시한다(posix_fadvise(2)).
- DB는 자기 버퍼 풀에 스캔 저항을 넣는다. 예: MySQL InnoDB는 버퍼 풀 LRU를 new/old 구역으로 나누고 새 페이지를 중간 지점(midpoint)에 넣는다. 기본으로 3/8이 old 구역이다(MySQL 8.4 문서 "Buffer Pool").

### 3. 스왑을 설계에 넣는다

- 지연이 중요한 서비스는 작업 집합이 RAM에 들어가도록 **용량을 잡는다**. 스왑은 느린 대체물이지 추가 메모리가 아니다.
- 꼭 상주해야 하는 영역은 `mlock(2)`/`mlockall(2)`로 스왑에서 뺄 수 있다. 권한·`RLIMIT_MEMLOCK` 제한이 있다(mlock(2)).
- `vm.swappiness`는 "스왑을 쓸지 말지" 스위치가 아니다. 익명 페이지와 파일 페이지 사이의 **상대 비용**이다.
  - 전통적인 두 목록 LRU의 전역 회수에서는, 0이어도 빈 페이지와 파일 페이지가 high 워터마크 아래로 떨어지면 스왑한다(kernel.org sysctl/vm).
  - 예외 1: MGLRU가 켜진 커널에서 0이면 파일 페이지만 회수한다(mm/vmscan.c `min_type`/`max_type`, `get_type_to_scan`). 작성 환경이 여기에 해당한다.
  - 예외 2: cgroup 한도 회수(`memory.max`·`memory.high` 등)에서 0이면 파일 페이지만 훑는다(mm/vmscan.c `get_scan_count`의 `cgroup_reclaim(sc) && !swappiness` → `SCAN_FILE`).
  - 두 예외 모두 익명 페이지를 스왑하지 않는 대신, 파일 페이지만 회수하다 OOM으로 갈 수 있다.
- 자바처럼 GC가 힙 전체를 훑는 런타임은 힙 일부가 스왑으로 나가면 GC가 그 페이지를 다시 읽느라 일시 정지가 길어진다. 힙은 RAM에 들어가게 잡는다.

## 장애 시나리오와 대처

### 1. 스왑 폭주 → 시스템 전체가 멈춘 듯(스래싱)

- **현상**: 모든 서비스가 동시에 느려진다. SSH 타이핑도 지연된다. 시간이 지나도 스스로 회복하지 않는다.
- **보이는 형태**
  - `vmstat`의 `si`·`so`가 계속 높다. `b`(I/O 대기 프로세스)가 늘고 `wa`가 오른다. CPU `us`는 낮다.
  - `/proc/pressure/memory`의 `full avg10`이 크다.
  - `pgmajfault`가 빠르게 는다. 애플리케이션 p99 지연이 초 단위로 뛴다.
- **원인**: 실행 중인 프로세스들의 작업 집합 합이 RAM을 넘었다. 새로 뜬 배치, 메모리 누수, 캐시 설정 과다가 흔하다.
- **대처**
  - 가장 많이 쓰는 프로세스를 줄이거나 멈춘다(진입 제어의 수동판).
  - 컨테이너라면 cgroup 메모리 limit으로 한 서비스가 전체를 스래싱시키지 않게 막는다(13번).
  - PSI 기반 조기 종료(systemd-oomd 등)를 검토한다. OOM killer는 메모리가 완전히 바닥나야 움직여, 그 전의 긴 스래싱을 막지 못할 수 있다.

### 2. 교체 정책이 스캔에 오염 → 캐시가 식는다

- **현상**: 야간 백업·로그 압축·풀 스캔 쿼리 직후 서비스 지연이 오른다. 시간이 지나면 서서히 회복한다.
- **보이는 형태**
  - 스캔 직후 `workingset_refault_file`과 디스크 읽기(`bi`)가 튄다.
  - 애플리케이션 캐시 적중률(버퍼 풀 hit ratio)이 떨어진다.
- **원인**: 한 번 쓸 대량 페이지가 "최근 사용"이 되어 자주 쓰던 페이지를 밀어냈다. LRU·FIFO·CLOCK의 공통 약점이다(looping/scan 패턴).
- **대처**
  - 스캔 작업에 `POSIX_FADV_DONTNEED`·`O_DIRECT`를 쓰거나, 캐시를 덜 쓰는 도구 옵션을 쓴다.
  - 스캔 작업을 전용 cgroup에 넣어 메모리를 제한한다.
  - 애플리케이션 캐시는 스캔 저항이 있는 정책(2Q·ARC·TinyLFU 류)을 쓴다.

### 3. direct reclaim으로 할당 지연

- **현상**: 평균은 괜찮은데 가끔 요청 하나가 수십~수백 ms 멈춘다.
- **보이는 형태**: `/proc/vmstat`의 `allocstall_*`, `pgscan_direct`가 는다.
- **원인**: 버스트 할당이 kswapd보다 빨라 빈 메모리가 min 워터마크 밑으로 내려갔다. 할당하는 스레드가 직접 회수한다.
- **대처**: `vm.watermark_scale_factor`로 kswapd를 더 일찍 깨운다(kernel.org sysctl/vm). 근본은 여유 메모리를 늘리거나 버스트 할당을 줄이는 것이다.

### 4. 스왑된 JVM 힙 → 긴 GC 정지

- **현상**: 한동안 한가하던 자바 서비스가 첫 요청 무렵이나 Full GC 때 수 초씩 멈춘다.
- **보이는 형태**: `/proc/<pid>/status`의 `VmSwap`이 크다. GC 로그의 일시 정지 시간이 평소보다 훨씬 길다. 그동안 `si`가 튄다.
- **원인**: 안 쓰이던 힙 페이지가 스왑으로 나갔다. GC가 살아 있는 객체를 따라가며 그 페이지를 major fault로 하나씩 읽어 온다.
- **대처**: 힙과 native 메모리의 합이 RAM(또는 cgroup limit)에 넉넉히 들어가게 잡는다. 스왑을 끄거나 해당 cgroup의 스왑을 0(`memory.swap.max`)으로 두는 선택을 비교한다.

## 핵심 문장

- 스왑은 익명 페이지(와 shmem/tmpfs 페이지)를 디스크로 내보내 가상 메모리의 합이 RAM보다 커도 돌아가게 하는 메커니즘이다. 일반 파일 페이지는 원본 파일이 있어 버리기만 하면 된다(dirty면 먼저 쓴다).
- 교체 정책의 기준선은 OPT(가장 먼 미래)다. 실제로는 LRU를 쓰고 싶지만 비싸서, 참조 비트 하나로 도는 CLOCK으로 근사한다.
- FIFO는 프레임을 늘려도 폴트가 늘 수 있다(Belady 이상). LRU·OPT는 스택 성질이 있어 그렇지 않다.
- LRU 계열은 한 번 쓰고 마는 스캔에 오염된다. 전통적인 리눅스 LRU는 inactive/active 두 목록으로 "두 번 쓴 페이지"만 보호한다. MGLRU(6.1+)가 켜진 커널은 여러 세대로 같은 구분을 한다.
- 작업 집합의 합이 RAM을 넘으면 스래싱이다. 스왑을 쓰면 `si`·`so`가 함께 높고(파일 페이지 스래싱은 `bi`·refault), CPU는 놀며, PSI `full`이 오른다. 해법은 정책이 아니라 메모리 수요를 줄이는 것이다.

## 관련 주제·근거

- 원고: [foundations/memory-management](../../foundations/memory-management/README.md) — §10 요구 페이징, §11 페이지 폴트와 희생 페이지, §14 Page Table·TLB·스왑
- 선행: [10-paging-and-tlb](../10-paging-and-tlb/2-summary.md)
- 후속·연결
  - [11-heap-allocation](../11-heap-allocation/2-summary.md) — 스왑 대상인 익명 메모리가 생기는 곳
  - [13-oom-and-memory-limits](../13-oom-and-memory-limits/2-summary.md) — 회수로도 안 되면 OOM killer
  - [14-mmap-and-page-cache](../14-mmap-and-page-cache/2-summary.md) — 파일 페이지와 페이지 캐시 회수
  - [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md) — 정확한 LRU 구현
  - [systems/thrashing](../../systems/thrashing/2-summary.md) — 동적 배열 재할당 스래싱(용어 대비)
- 교재
  - OSTEP 21 "Beyond Physical Memory: Mechanisms"(스왑 영역, present 비트, 워터마크) <https://pages.cs.wisc.edu/~remzi/OSTEP/vm-beyondphys.pdf>
  - OSTEP 22 "Beyond Physical Memory: Policies"(OPT, FIFO, LRU, CLOCK, Belady 이상, looping-sequential 0%, 22.11 스래싱, 스캔 저항·ARC) <https://pages.cs.wisc.edu/~remzi/OSTEP/vm-beyondphys-policy.pdf>
  - Belady, Nelson, Shedler, "An Anomaly in Space-time Characteristics of Certain Programs Running in a Paging Machine", CACM 12(6), 1969 (OSTEP 22 인용)
  - Denning, "The Working Set Model for Program Behavior", CACM 11(5), 1968
- 커널 문서·소스
  - sysctl/vm — `swappiness`(0~200, 기본 60), `watermark_scale_factor`(기본 10), `min_free_kbytes` <https://docs.kernel.org/admin-guide/sysctl/vm.html>
  - Multi-Gen LRU — `/sys/kernel/mm/lru_gen/enabled`, `min_ttl_ms` <https://docs.kernel.org/admin-guide/mm/multigen_lru.html> · 설계 문서(세대 구조) <https://docs.kernel.org/mm/multigen_lru.html>
  - PSI — `/proc/pressure/memory`의 some/full <https://docs.kernel.org/accounting/psi.html>
  - `mm/workingset.c` 머리 주석 — Double CLOCK lists, refault distance <https://github.com/torvalds/linux/blob/master/mm/workingset.c>
  - `mm/vmscan.c`(v7.0) — `get_scan_count`의 `cgroup_reclaim(sc) && !swappiness`, MGLRU `min_type`/`max_type`·`get_type_to_scan` <https://raw.githubusercontent.com/torvalds/linux/v7.0/mm/vmscan.c>
  - `include/linux/mm_inline.h` `folio_is_file_lru` 주석 — tmpfs·swap-backed 페이지는 익명 LRU · tmpfs(5) "pages ... can be swapped out"
- man: vmstat(8) si/so, posix_fadvise(2), mlock(2)(`RLIMIT_MEMLOCK`, `CAP_IPC_LOCK`), proc_pid_status(5) `VmSwap`
- MySQL 8.4 Reference Manual, "Buffer Pool"(midpoint insertion, old 3/8) <https://dev.mysql.com/doc/refman/8.4/en/innodb-buffer-pool.html>
- kernelnewbies, Linux 6.1(MGLRU) <https://kernelnewbies.org/Linux_6.1>
- 로컬 재현: FIFO/LRU/CLOCK/OPT 시뮬레이터(Belady 참조열, looping 50페이지·캐시 49), LRU vs 두 목록 스캔 오염 장난감 시뮬레이션, `vmstat`·`/proc/vmstat`·`/proc/pressure/memory` 읽기(리눅스 7.0)
