# os/14-mmap-and-page-cache — 파일을 메모리처럼: mmap·페이지 캐시·dirty writeback — 정리 (힌트)

## 해결하는 문제

디스크는 메모리보다 수만 배 이상 느리다(원고 [memory-management §14](../../foundations/memory-management/README.md)의 지연 표).\
같은 파일을 여러 번, 여러 프로세스가 읽는다면 매번 디스크까지 가면 안 된다.\
쓰기도 매번 디스크까지 기다리면 느리다.

```text
  없으면                                   있으면 (페이지 캐시)
  read  → 매번 디스크                       read  → 메모리에 있으면 복사만 (디스크 안 감)
  write → 디스크에 쓸 때까지 기다림           write → 메모리에 쓰고 바로 리턴, 디스크는 나중에
  프로세스 A·B가 같은 파일 → 사본 두 개        A·B가 같은 페이지를 공유
```

커널은 파일 내용을 페이지 단위로 메모리에 들고 있다. 이것이 **페이지 캐시**다.\
그리고 그 페이지를 프로세스 주소 공간에 직접 붙여 주는 것이 **`mmap`**이다.

  - *페이지 캐시*: 파일 내용을 담은 물리 페이지들의 캐시다. `read`/`write`도, `mmap`도 모두 이 페이지를 거친다(예외: `O_DIRECT`는 캐시 효과를 되도록 줄이려 한다 — open(2)).
  - *mmap(memory map)*: 파일(또는 익명 메모리)을 가상 주소 범위에 매핑하는 시스템 콜이다. 매핑한 뒤에는 포인터로 읽고 쓰면 된다.

쉬운 예: 도서관 열람실의 공용 책장이다.
- 누가 책을 요청하면 사서가 서고(디스크)에서 꺼내 열람실 책장(페이지 캐시)에 꽂는다. 다음 사람은 책장에서 바로 본다.
- 책에 메모를 하면(write) 책장에 있는 책이 바뀐다. 서고의 원본은 사서가 나중에 한꺼번에 고친다(writeback).
- `read`는 책장에서 복사본을 떠 가는 것이고, `mmap`은 책장 앞에 앉아 그 책을 직접 보는 것이다.

똑같은 구조다.\
Kafka가 자기 캐시를 두지 않고 OS 페이지 캐시에 맡기는 이유도 이것이다([systems/kafka-why-fast](../../systems/kafka-why-fast/2-summary.md) ②).

실무 예:
- `free`를 보니 "used"가 크거나 `free`가 거의 0이다. 메모리 누수라고 착각한다. 대부분 캐시다.
- 매핑해 둔 로그 파일을 다른 프로세스가 잘라(truncate) 내자 서비스가 `SIGBUS`(버스 오류)로 죽었다.

## 동작·원리

### 1. read/write와 mmap — 같은 페이지 캐시, 다른 길

```text
  read(fd, buf, n)                            mmap(NULL, n, PROT_READ, MAP_SHARED, fd, 0)

  사용자 버퍼 buf  <-- 복사 --+                 사용자 주소 p ----+  (페이지 테이블이 직접 가리킴)
                             |                                 |
  커널   +-------------------+-----+           +---------------v-----+
         |   페이지 캐시 (파일 페이지)   |   ←같은 것→   |   페이지 캐시        |
         +-------------------+-----+           +---------------------+
                             | 없으면 디스크에서 읽어 채움 (major fault / 블록 I/O)
                             v
                          디스크
```

- `read`는 페이지 캐시에서 사용자 버퍼로 **복사**한다. 시스템 콜 한 번마다 복사가 있다.
- `mmap`은 복사하지 않는다. 페이지 테이블이 캐시 페이지를 직접 가리킨다. 처음 접근할 때 페이지 폴트로 연결한다(요구 페이징, 10번).
- 둘 다 같은 캐시를 본다. 한 프로세스가 `write`한 내용은 다른 프로세스의 `MAP_SHARED` 매핑에서 보인다.

**MAP_SHARED vs MAP_PRIVATE**

```text
  MAP_SHARED                         MAP_PRIVATE
  쓰기 → 캐시 페이지를 직접 수정        쓰기 → 그 페이지를 복사(copy-on-write) → 내 사본만 수정
       → 다른 매핑에도 보임                 → 다른 프로세스·원본 파일에 안 보임
       → 나중에 파일에 기록                  → 사본은 익명 페이지(스왑 대상, 12번)
```

- `MAP_SHARED`의 수정은 원본 파일로 전달된다. 정확한 시점을 정하려면 `msync(2)`를 쓴다(mmap(2)).
- `MAP_PRIVATE`는 copy-on-write 매핑이다. 수정은 원본 파일에 가지 않는다(mmap(2)). 실행 파일과 공유 라이브러리의 데이터 영역이 이렇게 매핑된다.

### 2. 페이지 캐시 안에서 페이지 찾기

```text
  파일 (inode)
    └─ address_space
         └─ i_pages : XArray (기수 트리)
               키 = 파일 안 페이지 번호 (offset / 4096)
               값 = 캐시된 페이지 (folio)

        [ 루트 ]
        /   |   \        오프셋의 비트를 몇 개씩 잘라 단계별로 내려간다
     [ ]   [ ]   [ ]     → 파일이 아무리 커도 몇 단계면 찾는다
     / \         / \     → 비어 있는 구간은 노드가 없어 메모리를 안 쓴다
    p0  p1     p900 p901
```

- 파일마다 `address_space`가 있고, 그 안의 `i_pages`가 `struct xarray`다(include/linux/fs.h).
- XArray는 "아주 큰 포인터 배열처럼 동작하는" 추상 자료형이다(kernel.org core-api/xarray). 구현은 노드당 64칸(`XA_CHUNK_SHIFT` 6)의 기수 트리다(include/linux/xarray.h `struct xa_node`).
- 리눅스 4.20에서 XArray가 들어오고 페이지 캐시가 그쪽으로 옮겨졌다(kernelnewbies 4.20 "XArray"). 지금 radix tree API는 XArray 위의 이름이다(include/linux/radix-tree.h `#define radix_tree_root xarray`).
- OSTEP 23은 페이지 캐시를 "해시 테이블"로 설명한다. 교재의 단순화이고, 현재 리눅스는 파일별 XArray다.

### 3. 쓰기 — dirty와 writeback

```text
  write() / MAP_SHARED 쓰기
        |
        v
  캐시 페이지 수정 → dirty 표시 → 호출은 바로 리턴 (디스크는 아직)
        |
        |  flusher 스레드가 깨는 조건
        |   (a) 주기: dirty_writeback_centisecs (기본 500 = 5초)마다 깨서
        |        dirty_expire_centisecs (기본 3000 = 30초)보다 오래된 dirty를 쓴다
        |   (b) 양: dirty가 dirty_background_ratio (기본 10%)를 넘으면 백그라운드로 쓴다
        |   (c) 양: dirty가 늘면 write하는 프로세스를 재워 속도를 늦춘다 → write가 막힌다
        |        ((background+dirty_ratio)/2부터 점점, dirty_ratio (기본 20%)에 가까울수록 강하게)
        v
  디스크에 기록 → clean
  (fsync/fdatasync/msync(MS_SYNC)를 부르면 그 파일은 지금 기록하고 끝날 때까지 기다린다 — 24번)
```

- 비율의 기준은 전체 RAM이 아니라 "빈 페이지 + 회수 가능한 페이지"다(kernel.org sysctl/vm).
- sysctl 문서는 (c)를 "쓰는 프로세스가 직접 기록을 시작한다"고 적는다. 현재 구현의 `balance_dirty_pages`는 쓰는 프로세스를 `(background_thresh + dirty_thresh) / 2`를 넘으면 기다리게 하고, 기록 자체는 flusher에 맡긴다(mm/page-writeback.c 주석).
- 기본값 10·20·500·3000은 작성 환경(리눅스 7.0)의 `/proc/sys/vm/dirty_*` 값과 같았다. 문서는 각 값의 의미를 적는다(kernel.org sysctl/vm).
- 그래서 `write` 성공은 "디스크에 있다"가 아니다. 전원이 나가면 dirty 페이지는 사라진다(24번 fsync).

### 4. 파일 끝 너머를 건드리면 — SIGBUS

```text
  파일 8KiB를 MAP_SHARED로 매핑 (2페이지)
  +-----------+-----------+
  |  page 0   |  page 1   |
  +-----------+-----------+
  다른 프로세스가 파일을 100바이트로 truncate
  +-----------+-----------+
  |0..99| 0...|  파일 밖   |   ← page 0: 100바이트 뒤는 0으로 보인다
  +-----------+-----------+     page 1: 파일 끝을 완전히 넘은 페이지 → 접근하면 SIGBUS
```

- mmap(2): 매핑된 파일의 **끝을 넘은 페이지**에 접근하면 `SIGBUS`다. 쓰기 금지 영역에 쓰면 `SIGSEGV`다.
- 파일 끝이 걸친 마지막 페이지의 나머지 바이트는 0으로 보인다(mmap(2) NOTES).

로컬 재현(예시, 리눅스 7.0):

```text
before truncate: p[0]=A p[4096]=B
after truncate:  p[0]=A p[200]=0
touch p[4096] ...
버스 오류 (코어 덤프됨)          exit=135  (128 + SIGBUS 7)
```

## 쓰이는 자료구조·알고리즘

- **기수 트리(XArray)** — 파일 오프셋 → 캐시 페이지. 오프셋 비트를 잘라 단계별로 내려간다. 희소한 파일도 빈 구간 노드가 없다. [data-structure/20-radix-trie](../../data-structure/20-radix-trie/2-summary.md)
- **두 목록(active/inactive) 교체** — 페이지 캐시 회수는 12번의 두 CLOCK 목록을 쓴다. OSTEP 23은 이것을 "변형된 2Q"라고 부른다. MGLRU가 켜진 커널은 대신 여러 세대 목록을 쓴다(12번).
- **copy-on-write** — `MAP_PRIVATE` 쓰기, `fork` 뒤 쓰기에서 페이지를 처음 쓸 때 복사한다(05번).
- **미리 읽기(readahead)** — 순차 읽기를 감지하면 요청보다 더 읽어 둔다. 로컬 재현에서 4MiB(1024페이지)를 읽자 1056페이지가 캐시에 올랐다(예시, 리눅스 7.0 — 32페이지를 더 읽음).

## 적용 — 풀어나가는 법

### 1. "메모리가 없다"를 캐시와 구분한다

```text
$ free -m                     (예시, 리눅스 7.0 · procps-ng 4.0.4)
               total        used        free      shared  buff/cache   available
Mem:           37775       34609        1797        8448       10355        3166
```

- `buff/cache`: 버퍼 + 페이지 캐시 + 회수 가능한 slab이다(free(1)).
- `available`: 스왑 없이 새 프로그램에 줄 수 있다고 **추정한** 양이다. 버릴 수 있는 캐시를 포함한다. `/proc/meminfo`의 `MemAvailable`이고 리눅스 3.14부터 있다(free(1)).
- `used`의 정의는 도구 버전마다 다르다. procps-ng 4.0.1부터 free의 used는 `total - available`이다(procps NEWS).
- 대시보드가 `MemTotal - MemFree`를 "사용량"으로 그리면 캐시까지 사용 중으로 보인다. 판단은 `available`로 한다.

```bash
grep -E '^(MemTotal|MemFree|MemAvailable|Cached|Dirty|Writeback):' /proc/meminfo
cat /sys/fs/cgroup/<경로>/memory.stat | grep -E '^(anon|file|file_dirty|file_writeback) '   # cgroup 안
```

- cgroup의 `memory.current`에도 페이지 캐시가 들어간다(13번). 컨테이너 메모리 그래프가 limit에 붙어 있어도 `file`이 크면 대개 회수 가능한 캐시다.

### 2. 파일이 캐시에 있나 확인한다

```c
/* mincore: 매핑한 범위의 각 페이지가 메모리에 있는지 */
void *m = mmap(NULL, size, PROT_READ, MAP_SHARED, fd, 0);
unsigned char vec[(size + 4095) / 4096];
mincore(m, size, vec);         /* vec[i] & 1 == 1 이면 캐시에 있음 */
```

- 권한 조건(리눅스 5.2+): 파일 매핑은 호출자가 파일 소유자이거나 쓰기 권한이 있을 때만 실제 상주 여부가 나온다. 그 밖의 파일(시스템 라이브러리, 남의 파일)은 모든 페이지가 1로 보고된다(mm/mincore.c `can_do_mincore`·`memset(vec, 1, pages)`, 커밋 134fca9063ad "mm/mincore.c: make mincore() more conservative" — 사이드 채널 방지). mincore(2) man에는 이 조건이 없다. 아래 재현은 직접 만든 파일이라 영향이 없다.

로컬 재현(예시, 리눅스 7.0 — 16MiB 파일, 4096페이지):

```text
after write (dirty)          cached pages 4096 / 4096
after fsync                  cached pages 4096 / 4096
after FADV_DONTNEED          cached pages 0 / 4096       ← fsync 뒤라 clean → 전부 버려짐
after reading first 4MiB     cached pages 1056 / 4096    ← 1024 + readahead 32

(fsync 없이 바로 FADV_DONTNEED)
after FADV_DONTNEED          cached pages 2048 / 4096    ← dirty 페이지는 바로 못 버린다
```

- `util-linux`의 `fincore` 명령이 있으면 파일 단위로 같은 정보를 보여 준다.

### 3. mmap을 쓸 때의 규칙

- 매핑 중인 파일을 다른 곳에서 줄이지 않게 한다. 로그 회전은 truncate 대신 새 파일로 교체(rename)한다.
- `SIGBUS`를 피할 수 없으면 파일 크기를 먼저 확인하고, 필요하면 `fallocate`로 공간을 미리 잡는다.
- `MAP_SHARED`의 수정을 디스크에 확정하려면 `msync(MS_SYNC)`를 부른다. msync 없이는 `munmap` 전에 기록된다는 보장이 없다(msync(2)). `munmap`도 기록을 기다려 주지 않는다.

자바에서의 모습:

```java
try (FileChannel ch = FileChannel.open(path, READ, WRITE)) {
    MappedByteBuffer buf = ch.map(FileChannel.MapMode.READ_WRITE, 0, ch.size()); // mmap(MAP_SHARED)
    buf.put(0, (byte) 1);   // 페이지 캐시를 직접 수정
    buf.force();            // msync에 해당 — 디스크 기록을 요청
}
```

- Java SE 문서는 매핑이 "버퍼 자체가 GC될 때까지 유효하다"고 적는다(`MappedByteBuffer`). 파일을 닫아도 매핑은 GC 전까지 남는다.
- 매핑된 파일이 잘린 뒤 접근하면, HotSpot 구현에서는 SIGBUS를 `java.lang.InternalError: a fault occurred in an unsafe memory access operation`으로 바꿔 던질 수 있다(OpenJDK `handshake.cpp`).

## 장애 시나리오와 대처

### 1. `free`가 "사용 중"으로 보여 메모리 누수 오판

- **현상**: 서버 메모리 그래프가 며칠째 우상향하다 90% 이상에서 멈춘다. 누수를 의심해 재시작한다. 재시작 뒤 또 오른다.
- **보이는 형태**: `free`의 `free`가 작고 `buff/cache`가 크다. `available`은 넉넉하다. 스왑·OOM 없음.
- **원인**: 파일을 읽고 쓸수록 페이지 캐시가 빈 메모리를 채운다. 비어 있는 메모리는 쓸모가 없으니 커널은 캐시로 쓴다. 필요하면 회수한다.
- **대처**
  - 판단 지표를 `MemAvailable`로 바꾼다. 컨테이너면 `memory.stat`의 `anon`과 `file`을 나눠 본다.
  - `echo 3 > /proc/sys/vm/drop_caches`로 "치우는" 것은 진단 실험일 뿐 해결책이 아니다(root 필요). 치운 뒤 디스크 읽기가 늘어난다.

### 2. 매핑 중인 파일 절단 → `SIGBUS`

- **현상**: 서비스가 로그 회전·파일 교체 시점에 죽는다.
- **보이는 형태**: 종료 코드 135(128 + 7), 셸 메시지 "버스 오류(Bus error)". 자바면 `InternalError: a fault occurred in an unsafe memory access operation`.
- **원인**: 프로세스가 `mmap`한 파일을 다른 프로세스가 `truncate`했다. 파일 끝을 넘은 페이지에 접근하면 커널이 `SIGBUS`를 보낸다(mmap(2)). 디스크가 꽉 차 sparse 파일의 구멍에 쓸 블록을 못 받을 때도 SIGBUS가 난다. ext4의 `page_mkwrite`가 `ENOSPC`를 받으면 `vmf_fs_error`가 `VM_FAULT_SIGBUS`로 바꾼다(include/linux/mm.h, fs/ext4/inode.c).
- **대처**
  - 매핑 중인 파일은 제자리에서 줄이지 않는다. 새 파일에 쓰고 `rename`으로 교체한다.
  - 파일 크기를 미리 확정(`fallocate`)하고 매핑 범위를 그 안으로 제한한다.
  - 공유 파일을 매핑해야 하면 파일 잠금 등으로 절단과 접근을 조율한다.

### 3. dirty 페이지 누적 → write가 갑자기 멈춤

- **현상**: 평소 빠르던 로그 쓰기·파일 업로드가 가끔 수 초씩 멈춘다.
- **보이는 형태**: `/proc/meminfo`의 `Dirty`·`Writeback`이 크다. `vmstat`의 `bo`가 튀고 `wa`가 오른다.
- **원인**: 쓰는 속도가 디스크 속도보다 빨라 dirty가 한도 근처까지 쌓였다. 그러면 커널의 `balance_dirty_pages`가 쓰는 프로세스를 재워 쓰기 속도를 디스크 속도에 맞춘다. `(background + dirty_ratio)/2`를 넘으면 시작하고 `dirty_ratio`에 가까울수록 오래 막힌다(mm/page-writeback.c, kernel.org sysctl/vm).
- **대처**
  - `dirty_background_ratio`(또는 `_bytes`)를 낮춰 더 일찍, 조금씩 쓰게 한다.
  - 큰 파일은 중간중간 `fdatasync`나 `sync_file_range`로 나눠 기록한다.
  - 근본은 디스크 대역폭과 쓰기량의 균형이다.

### 4. 페이지 캐시에만 있던 데이터 유실

- **현상**: 전원 장애·커널 패닉 뒤 방금 "저장 성공"한 데이터가 없다.
- **보이는 형태**: 파일 끝부분이 비었거나 0바이트다. 애플리케이션 로그에는 쓰기 성공이 남아 있다.
- **원인**: `write`는 페이지 캐시에 쓰고 리턴한다. dirty 페이지가 기록되기 전(기본 최대 약 30초 + 주기)에 전원이 나갔다.
- **대처**: 지속성이 필요한 지점에서 `fsync`/`fdatasync`를 부른다. 새 파일은 디렉터리까지 fsync한다(24번). Kafka처럼 복제로 대신하는 설계도 있다.

## 핵심 문장

- 페이지 캐시는 파일 내용을 담은 커널 메모리다. `read`/`write`는 거기서 복사하고, `mmap`은 그 페이지를 주소 공간에 직접 붙인다.
- `MAP_SHARED` 쓰기는 캐시 페이지를 고쳐 파일로 전달되고, `MAP_PRIVATE` 쓰기는 copy-on-write 사본만 고친다.
- `write` 성공은 "dirty 페이지가 됐다"는 뜻이다. flusher가 시간(30초 지난 것)·양(background 10%) 기준으로 나중에 기록하고, dirty가 20% 쪽으로 쌓이면 쓰는 쪽이 막힌다.
- 페이지 캐시는 빈 메모리를 채운다. "free가 적다"는 누수가 아니다. `available`로 판단한다.
- 매핑한 파일의 끝을 넘은 페이지를 건드리면 `SIGBUS`(135)다. 매핑 중인 파일은 truncate하지 말고 rename으로 교체한다.

## 관련 주제·근거

- 원고: [foundations/memory-management](../../foundations/memory-management/README.md) — §10 요구 페이징, §14 메모리 계층 지연
- 선행: [10-paging-and-tlb](../10-paging-and-tlb/2-summary.md) · [09-address-space](../09-address-space/2-summary.md) — 주소 공간의 매핑 영역
- 후속·연결
  - [12-swapping-and-page-replacement](../12-swapping-and-page-replacement/2-summary.md) — 파일 페이지 회수, 두 목록
  - [13-oom-and-memory-limits](../13-oom-and-memory-limits/2-summary.md) — cgroup 사용량의 `file` 몫
  - [06-signals](../06-signals/2-summary.md) — SIGBUS·SIGSEGV
  - [24-fsync-and-durability](../24-fsync-and-durability/2-summary.md) — write ≠ 디스크, fsync
  - [34-zero-copy-and-io-uring](../34-zero-copy-and-io-uring/2-summary.md) — sendfile·mmap
  - [05-fork-exec-wait](../05-fork-exec-wait/2-summary.md)(copy-on-write)
  - [systems/kafka-why-fast](../../systems/kafka-why-fast/2-summary.md) — 페이지 캐시에 맡기는 설계, sendfile
  - Apache Kafka 문서 Design "Persistence" — 페이지 캐시는 서비스 재시작 뒤에도 따뜻하다 <https://kafka.apache.org/41/design/design/>
  - 같은 문서 "Efficiency" — SSL이 켜지면 sendfile을 쓰지 않는다(사용자 공간 암호화)
  - [data-structure/20-radix-trie](../../data-structure/20-radix-trie/2-summary.md) — 기수 트리
- 교재
  - OSTEP 23 "Complete Virtual Memory Systems" — 23.2 Linux의 통합 페이지 캐시, dirty 백그라운드 기록, 변형 2Q <https://pages.cs.wisc.edu/~remzi/OSTEP/vm-complete.pdf>
  - CS:APP 3판 9.8 "Memory Mapping"
- man
  - mmap(2) — `MAP_SHARED`·`MAP_PRIVATE`, SIGBUS(파일 끝 너머)·SIGSEGV, 끝 페이지 0 채움 <https://man7.org/linux/man-pages/man2/mmap.2.html>
  - msync(2), mincore(2), posix_fadvise(2)
  - free(1) — buff/cache, available(`MemAvailable`, 3.14+) <https://man7.org/linux/man-pages/man1/free.1.html>
  - proc_meminfo(5) — `Cached`, `Dirty`, `Writeback`, `MemAvailable`
- 커널 문서·소스
  - mm/mincore.c(v7.0) `can_do_mincore` — 소유자·쓰기 권한 없는 파일 매핑은 전부 1. 커밋 134fca9063ad(v5.2에 포함, GitHub compare로 확인) <https://raw.githubusercontent.com/torvalds/linux/v7.0/mm/mincore.c>
  - sysctl/vm — `dirty_background_ratio`, `dirty_ratio`, `dirty_expire_centisecs`, `dirty_writeback_centisecs`, `drop_caches` <https://docs.kernel.org/admin-guide/sysctl/vm.html>
  - XArray <https://docs.kernel.org/core-api/xarray.html> · `include/linux/fs.h` `struct address_space`의 `i_pages`
  - kernelnewbies Linux 4.20 — XArray 전환 <https://kernelnewbies.org/Linux_4.20>
- procps-ng NEWS — 4.0.1 "Used memory is Total - Available" <https://gitlab.com/procps-ng/procps/-/blob/master/NEWS>
- OpenJDK `src/hotspot/share/runtime/handshake.cpp` — "a fault occurred in an unsafe memory access operation"
- Java SE 21 `MappedByteBuffer` — 매핑은 버퍼가 GC될 때까지 유효 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/MappedByteBuffer.html>
- `mm/page-writeback.c` `balance_dirty_pages` — "(background_thresh + dirty_thresh) / 2"를 넘으면 쓰는 쪽을 기다리게 함, 기본값 `dirty_background_ratio = 10`·`vm_dirty_ratio = 20`·`dirty_writeback_interval = 5 * 100`·`dirty_expire_interval = 30 * 100`
- `include/linux/mm.h` `vmf_fs_error` — `-ENOSPC` 등 → `VM_FAULT_SIGBUS` · `include/linux/xarray.h`·`radix-tree.h`
- 로컬 재현(리눅스 7.0): 매핑 파일 truncate → SIGBUS(exit 135)와 끝 페이지 0 채움, `mincore`로 쓰기·fsync·`POSIX_FADV_DONTNEED`·readahead 뒤 캐시 페이지 수, `free -m`·`/proc/meminfo`·`/proc/sys/vm/dirty_*` 읽기
