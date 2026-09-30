# os/22-file-system-implementation — 블록 배열 위에 세운 inode·비트맵·디렉터리 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

디스크가 주는 것은 "번호 붙은 블록의 배열"뿐이다.\
"블록 5번에 4 KB를 써라", "블록 9번을 읽어라"만 할 수 있다.

그런데 사람은 `/home/jun/report.txt` 같은 **이름**으로, **크기가 제각각인** 파일을 다룬다.\
파일 시스템은 그 사이를 잇는다. 그러려면 네 가지를 디스크 위에 적어 둬야 한다.

```text
  무엇을 기억하나                         디스크 위 구조
  이 파일은 어느 블록들로 이루어졌나         inode (블록 포인터·extent)
  이 이름은 어느 파일인가                   디렉터리 (이름 -> inode 번호)
  어느 블록·inode가 비어 있나               비트맵
  전체 크기·구조가 어디 있나                 슈퍼블록
```

쉬운 예: 창고다.
- 창고 칸(블록)에는 번호만 있다.
- 물품 대장(inode)에 "이 물건은 3번·4번·9번 칸"이라고 적는다.
- 안내판(디렉터리)에는 "겨울옷 → 대장 12번"이라고 적는다.
- 빈 칸 현황판(비트맵)으로 새 칸을 찾는다.
- 대장 페이지 수는 창고를 지을 때 정한다. 칸이 남아도 대장이 꽉 차면 새 물건을 못 받는다.

똑같은 구조다.\
ext4는 inode 수를 포맷할 때 정한다. 그래서 `df`에 공간이 남아도 inode가 떨어지면 `No space left on device`가 난다.

실무 예:
- 작은 캐시 파일·세션 파일이 수백만 개 쌓인 서버에서 `df -h`는 40% 사용인데 파일 생성이 실패한다.
- 한 디렉터리에 파일 수천만 개를 넣다가 커널 로그에 `index full` 경고와 함께 `ENOSPC`가 난다.

## 동작·원리

### 디스크 배치 — 아주 작은 파일 시스템(vsfs)

OSTEP 40장의 예다. 4 KB 블록 64개짜리 파티션이다.

```text
  블록:  0    1    2    3 ... 7      8 ............................ 63
        [S]  [i]  [d]  [I I I I I]  [D D D D D D D D ... D D D D D]
         |    |    |    |            |
         |    |    |    |            데이터 영역 (56블록)
         |    |    |    inode 테이블 (5블록, inode 256 B -> 블록당 16개 -> 80개)
         |    |    데이터 비트맵 (블록마다 1비트: 0 빈칸, 1 사용)
         |    inode 비트맵
         슈퍼블록 (inode 수·데이터 블록 수·inode 테이블 시작 위치·매직 넘버)
```

- inode 테이블 크기가 곧 **만들 수 있는 파일 수의 상한**이다(여기서는 80개, OSTEP 40.2).
- 비트맵 한 블록(4 KB = 32768비트)이면 3만 2천여 개 객체를 추적한다.
  - *슈퍼블록*: 파일 시스템 전체 정보를 담은 블록이다. 마운트할 때 가장 먼저 읽는다.
  - *비트맵*: 객체 하나에 비트 하나를 대응시킨 표다. 0이면 빈칸, 1이면 사용 중이다.

### inode — 파일의 블록을 어떻게 가리키나

```text
  (a) 다단계 인덱스 (ext2/3, vsfs)                  (b) extent (ext4)
  inode                                          inode.i_block (60바이트)
  [직접 0] -> D                                   [헤더][ (논리 0, 길이 354, 물리 78679097) ]
  [직접 1] -> D                                         [ 빈 ] [ 빈 ] [ 빈 ]
  ...                                            -> extent 4개까지는 inode 안에 바로
  [직접 11] -> D                                 -> 더 많으면 트리(인덱스 노드 -> 잎 노드)
  [간접]   -> [포인터 1024개] -> D ...
  [이중 간접] -> [포인터 1024개] -> [포인터 1024개] -> D ...
```

- **다단계 인덱스**: 작은 파일은 직접 포인터만 쓴다. 커지면 간접 블록을 붙인다.
  - 4 KB 블록, 4바이트 주소면 간접 블록 하나에 포인터 1024개가 들어간다.
  - 직접 12개 + 간접 1개 → (12 + 1024) × 4 KB = 4144 KB(OSTEP 40.3).
  - 이중 간접까지 → (12 + 1024 + 1024²) × 4 KB ≈ 4 GB 조금 넘게(OSTEP 40.3).
  - 대부분 파일이 작다는 관찰에 맞춘 **비대칭 트리**다.
- **extent**: "시작 블록 + 길이" 한 쌍으로 연속 구간을 가리킨다.
  - 블록 1000개가 연속이면 extent 하나(`ee_len = 1000`)로 끝난다. 블록 맵이면 포인터 1000개가 든다(ext4 문서 ifork).
  - `inode.i_block` 60바이트에 헤더 + extent 4개가 들어간다. 넘치면 extent 트리가 된다.
  - 초기화된 extent 하나의 최대 길이는 32768블록이다(4 KB 블록이면 128 MiB, ext4 문서 ifork).
  - 로컬 재현: `filefrag -v /usr/bin/bash` → `1 extent found`, 354블록이 한 extent였다(예시, ext4, 리눅스 7.0).

  - *extent*: (파일 안 논리 블록 번호, 길이, 디스크 물리 블록 번호)의 묶음이다.

### 디렉터리 — 이름을 inode 번호로 바꾸는 표

```text
  디렉터리 "/foo"의 데이터 블록 (선형 방식)
  inode번호  이름길이  이름
  44         1         .
  2          2         ..
  47         3         bar
  51         8         notes.md
```

- 디렉터리도 파일이다. 내용이 "(이름, inode 번호)" 목록일 뿐이다(OSTEP 40.4).
- 선형 목록은 항목이 많아지면 찾기가 느리다(처음부터 훑는다).
- ext4는 `dir_index` 기능으로 **해시 트리(htree)**를 쓴다.
  - 이름의 해시를 키로 한 균형 트리다. 조회는 해시로 잎 블록을 찾는 B-트리 조회와 같다(ext4 문서 directory "Hash Tree Directories").
  - 트리 깊이 상한은 `large_dir` 기능이 없으면 2, 있으면 3이다(ext4 문서 `dx_root_info.indirect_levels`).
  - 로컬 확인: `lsattr -d /usr/bin`에 `I`(인덱스된 디렉터리) 플래그가 보였다(예시).

### 경로 한 번 여는 데 드는 I/O

```text
  open("/foo/bar")  (캐시가 비어 있을 때)
    루트 inode(2번) 읽기 -> 루트 디렉터리 데이터 읽기 ("foo" -> 44)
    -> foo inode 읽기 -> foo 디렉터리 데이터 읽기 ("bar" -> 47)
    -> bar inode 읽기                                         (여기까지 open)
  read() 블록마다: bar inode 읽기 -> 데이터 읽기 -> inode 쓰기(접근 시각)
```

- 경로의 **단계 수에 비례**해 I/O가 늘어난다. 루트 inode 번호는 약속된 값이다. 대부분 유닉스 파일 시스템에서 2다(OSTEP 40.6).
- 새 파일 `/foo/bar`를 만들면 약 10번의 I/O가 든다. 블록을 새로 할당하는 write는 한 번에 5번이다: 데이터 비트맵 읽기·쓰기, inode 읽기·쓰기, 데이터 쓰기(OSTEP 40.6 Figure 40.4).
- 그래서 **캐시**가 필수다. 리눅스는 페이지 캐시와 dentry 캐시(dcache)로 이 I/O 대부분을 없앤다(14번, vfs.rst).

### VFS — 여러 파일 시스템을 한 인터페이스로

```text
  open / read / write / stat           (시스템 콜)
            |
           VFS  --- dcache(경로 -> dentry), inode 캐시, struct file
            |
   +--------+--------+---------+
  ext4     XFS     btrfs     proc/tmpfs ...   (각자 lookup·read·write 구현을 등록)
```

- VFS는 시스템 콜과 실제 파일 시스템 사이의 층이다. 여러 구현이 공존하게 한다(vfs.rst).
- 핵심 객체는 넷이다: 슈퍼블록(마운트된 파일 시스템), inode, dentry(경로 요소), file(= 21번의 OFD).
- dentry는 RAM에만 있다. 디스크에 저장하지 않는다. 성능만을 위한 것이다(vfs.rst).
- 하나의 inode를 여러 dentry가 가리킬 수 있다. 하드 링크가 그 예다(vfs.rst).

### FFS와 블록 그룹 — "관련된 것은 가까이"

```text
  디스크 = 블록 그룹 여러 개
  [그룹 0: SB | 그룹 디스크립터 | 블록 비트맵 | inode 비트맵 | inode 테이블 | 데이터 ...]
  [그룹 1: (SB 사본) | ...      | 블록 비트맵 | inode 비트맵 | inode 테이블 | 데이터 ...]
  ...
  정책: 파일 데이터는 그 inode와 같은 그룹에 / 같은 디렉터리의 파일은 디렉터리와 같은 그룹에
       새 디렉터리는 디렉터리가 적고 빈 inode가 많은 그룹에
```

- 초기 유닉스 파일 시스템은 디스크를 랜덤 메모리처럼 다뤘다. 성능이 디스크 대역폭의 2%까지 떨어졌다(OSTEP 41.1).
- FFS(BSD Fast File System)는 디스크를 **실린더 그룹**으로 나눴다. 관련된 것은 같은 그룹에, 무관한 것은 다른 그룹에 둔다(OSTEP 41.3~41.4).
- 큰 파일은 한 그룹을 다 채우지 않게 덩어리(chunk)로 나눠 여러 그룹에 흩는다(large-file exception, OSTEP 41.6).
- ext4의 **블록 그룹**이 이 설계의 후손이다. 슈퍼블록·그룹 디스크립터 사본을 일부 그룹에 둬 디스크 앞부분이 망가져도 복구할 수 있게 한다(ext4 문서 blockgroup).
- 로컬 재현(16 MiB 이미지, `mke2fs -t ext4 -N 64`, 예시):

```text
Group 0: (Blocks 0-4095)
  Primary superblock at 0, Group descriptors at 1-1
  Block bitmap at 3 (+3)
  Inode bitmap at 19 (+19)
  Inode table at 35-38 (+35)
  3057 free blocks, 53 free inodes, 2 directories
```

### inode 수는 포맷할 때 정해진다 (ext4)

```text
  mke2fs 기본:  inode 1개 / 16384바이트 (inode_ratio, /etc/mke2fs.conf — 512 MB~4 TB 볼륨)
  500 GB 파티션 -> 약 3천만 inode
  작은 파일 평균 < 16 KB 가 계속 쌓이면 -> 블록보다 inode가 먼저 바닥
```

- `mke2fs -i`(bytes-per-inode)로 비율을 정한다. **만든 뒤에는 비율을 바꿀 수 없다**. 크기를 늘리면 비율에 맞춰 inode 수도 늘어난다(mke2fs(8)).
- `-T`를 안 주면 mke2fs가 크기로 usage type을 고르고, 그 type의 `inode_ratio`가 기본값을 덮어쓴다(mke2fs(8) `-T`, `/etc/mke2fs.conf` e2fsprogs 1.47.0).
  - 3 MB 미만 `floppy` 8192 · 512 MB 미만 `small` 4096 · 4 TB 이상 `big` 32768 · 16 TB 이상 `huge` 65536. 그 사이(보통 볼륨)가 `[defaults]`의 16384다.
  - 그래서 "작은 파일"의 기준도 볼륨 크기에 따라 4 KB~64 KB로 달라진다.
- 작성 환경의 `/etc/mke2fs.conf` 기본 `inode_ratio = 16384`였다. `df -i /`는 31195136 inode였다(예시, 약 500 GB 파티션 — `df -B1` 기준 501.8 GB).
- XFS는 inode를 필요할 때 할당한다. 대신 inode가 쓸 수 있는 공간 비율 상한(`maxpct`)을 둔다. 기본은 1 TB 미만 25%다(mkfs.xfs(8)).

## 쓰이는 자료구조·알고리즘

- **비트맵** — 빈 inode·빈 블록을 비트 하나로 표시한다. 연속된 0을 찾으면 연속 공간이 된다. [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)
- **다단계 인덱스(비대칭 트리)** — 직접·간접·이중 간접 포인터. 다단계 페이지 테이블(10번)과 같은 발상이다.
- **extent 트리** — 연속 구간을 (시작, 길이)로 압축하고 넘치면 B-트리처럼 인덱스 노드를 둔다(ext4 `eh_depth`). [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md)
- **해시 B-트리(htree)** — 이름 해시로 디렉터리 항목을 찾는다. 선형 스캔 O(n)을 트리 깊이 몇 단계로 줄인다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **dcache(해시 테이블 + LRU)** — 경로 요소를 메모리에 캐시해 디스크 조회를 없앤다. 조회는 `dentry_hashtable`, 회수 후보는 `d_lru` 목록이다(fs/dcache.c). [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)
- **지역성 기반 배치(블록 그룹)** — 관련 객체를 가까이 둬 탐색 거리를 줄인다(FFS).
- 트리 모양 파일 시스템을 직접 구현해 보는 연습: [data-structure/33-filesystem](../../data-structure/33-filesystem/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 공간과 inode를 함께 본다

```bash
df -h /data          # 블록 사용량
df -i /data          # inode 사용량 (IUsed, IFree, IUse%)
stat -f /data        # statfs: 블록 전체/여유/가용, 아이노드 전체/여유
```

- 로컬 예(예시): `stat -f /` → `블록: 전체 122512118 여유 12246780 가용 6005129`.
  - "여유"와 "가용"의 차이(약 5%)는 root용 **예약 블록**이다. `mke2fs -m`의 기본은 5%다(mke2fs(8)).

C — 코드에서 inode 여유를 확인한다.

```c
#include <sys/statvfs.h>
struct statvfs s;
if (statvfs("/data", &s) == 0) {
    printf("inodes free %lu / %lu\n", s.f_ffree, s.f_files);          /* inode */
    printf("blocks avail %lu (non-root)\n", s.f_bavail);              /* 예약분 제외 */
}
```

- Java의 `FileStore.getUsableSpace()`는 바이트만 준다. inode는 `df -i`나 statvfs로 따로 감시한다.

### 2. 누가 inode를 먹는지 찾는다

```bash
# 디렉터리별 파일 수 상위 (현재 파일 시스템만)
find /data -xdev -type f | awk -F/ '{print $2"/"$3}' | sort | uniq -c | sort -rn | head
# 또는 GNU du의 inode 모드
du --inodes -x -d 2 /data | sort -rn | head
```

### 3. 구조를 들여다본다 (루트 없이 이미지로 연습)

```bash
truncate -s 16M img && mke2fs -q -t ext4 -N 64 img   # inode 64개짜리 작은 ext4
dumpe2fs -h img | grep -E 'Inode count|Free inodes|Free blocks'
debugfs -R 'stat <파일>' img          # inode 내용·EXTENTS
debugfs -R 'ls -l /' img              # 디렉터리 항목: inode 번호 + 이름
filefrag -v <파일>                    # 실제 파일의 extent 목록
```

### 4. 설계로 피한다

- 작은 파일 수백만 개 대신 묶는다: 로그는 회전·압축, 캐시는 KV 저장소·단일 파일 DB(SQLite), 객체는 오브젝트 스토리지.
- 한 디렉터리에 몰지 않는다: `ab/cd/abcdef...`처럼 해시 앞 글자로 하위 디렉터리를 나눈다.
- 작은 파일이 많을 볼륨이면 포맷 때 `-i`를 작게 잡거나, inode를 동적으로 할당하는 파일 시스템을 쓴다.

## 장애 시나리오와 대처

### 1. inode 고갈 — `df`는 여유인데 `No space left on device`

- **현상**: 파일 생성·임시 파일 쓰기가 실패한다. 기존 파일에 덧붙이기는 되기도 한다.
- **보이는 형태**
  - `ENOSPC` — Java는 파일을 여는 단계면 `java.io.FileNotFoundException: <경로> (No space left on device)`, 쓰는 단계면 `java.io.IOException: No space left on device`다(JDK `FileOutputStream` 구현). Node `ENOSPC: no space left on device`.
  - `df -h`는 여유, `df -i`는 `IUse% 100%`.
- **원인**: ext4는 inode 수가 포맷 때 고정이다. 작은 파일(세션·캐시·메일 큐·빌드 산출물)이 쌓여 inode가 먼저 떨어졌다. ext4 inode 할당 함수는 빈 inode가 없으면 `-ENOSPC`를 돌려준다(fs/ext4/ialloc.c).
- **로컬 재현(예시)**: inode 64개짜리 16 MiB 이미지에 debugfs로 작은 파일 60개를 쓰자 `Could not allocate inode`가 났다. 그때 `Free inodes: 0`, `Free blocks: 3004`(4096 중)였다.
- **대처**
  - 당장: `du --inodes`로 범인 디렉터리를 찾아 오래된 작은 파일을 지운다.
  - 근본: 작은 파일을 만들지 않는 설계로 바꾸거나, 볼륨을 `-i`를 작게 해 다시 만든다(비율은 나중에 못 바꾼다).
  - 감시: 블록 사용률과 함께 inode 사용률에 경보를 건다.

### 2. 거대 디렉터리 — 느린 조회, 그리고 `index full`

- **현상**: 한 디렉터리의 `ls`·`find`가 매우 느리다. 결국 새 파일 생성이 `ENOSPC`로 실패한다. `df -i`는 여유다.
- **보이는 형태**: 커널 로그에 `Directory (ino: N) index full, reach max htree level :2`, 이어서 `Large directory feature is not enabled on this filesystem`(fs/ext4/namei.c `ext4_dx_add_entry`).
- **원인**: htree 깊이 상한(`large_dir` 없으면 2)에 닿았다. 또는 `max_dir_size_kb` 마운트 제한에 걸렸다(fs/ext4/namei.c).
- **대처**: 파일을 해시 접두어 하위 디렉터리로 나눈다. 필요하면 `large_dir` 기능을 켠다. `ls`는 정렬하느라 더 느리므로 정렬 없는 `ls -f`나 `find -maxdepth 1`로 본다.

### 3. 일반 사용자만 `ENOSPC` — 예약 블록

- **현상**: 앱(일반 사용자)은 쓰기 실패인데 root 작업은 된다. `df`의 Use%가 100% 근처다.
- **보이는 형태**: `stat -f`에서 "여유"는 남았는데 "가용"은 0에 가깝다.
- **원인**: ext4는 기본으로 블록의 5%를 root용으로 예약한다. 단편화를 줄이고 시스템 데몬이 계속 돌게 하려는 것이다(mke2fs(8) `-m`).
- **대처**: 공간을 비우는 것이 먼저다. 데이터 전용 큰 볼륨이면 `tune2fs -m`으로 예약 비율을 낮출 수 있다(tune2fs(8)). 루트 파일 시스템의 예약은 남겨 둔다.

### 4. 파일 수가 많은 트리의 `stat` 폭주 — 캐시가 식었을 때

- **현상**: 재부팅·캐시 비움 직후 빌드·백업·`find`가 몇 배 느리다.
- **보이는 형태**: `iostat`에 작은 랜덤 읽기가 많다. 같은 작업의 두 번째 실행은 빠르다.
- **원인**: 경로 해석마다 디렉터리·inode 블록을 읽는다(OSTEP 40.6). dcache·inode 캐시·페이지 캐시가 비면 이 I/O가 전부 디스크로 간다.
- **대처**: 파일 수를 줄이는 설계(묶음·아카이브)가 근본이다. 메모리 압박으로 캐시가 밀리지 않게 한다(12·14번).

## 핵심 문장

- 파일 시스템은 블록 배열 위에 슈퍼블록·비트맵·inode 테이블·데이터 영역을 얹은 자료구조다.
- inode는 파일의 블록 위치를 담는다. ext2/3은 직접·간접 포인터, ext4는 (시작, 길이) extent 트리를 쓴다.
- 디렉터리는 "이름 → inode 번호" 표다. ext4는 큰 디렉터리를 해시 트리로 찾는다.
- 경로 한 단계마다 디렉터리·inode를 읽어야 해서 캐시(dcache·페이지 캐시)가 성능을 좌우한다.
- FFS·ext4 블록 그룹은 관련된 inode와 데이터를 가까이 둬 탐색을 줄인다.
- ext4의 inode 수는 포맷 때 고정이다. 그래서 `df` 여유와 `ENOSPC`가 함께 나올 수 있다. `df -i`를 같이 본다.

## 관련 주제·근거

- 선행: [21-files-and-descriptors](../21-files-and-descriptors/2-summary.md) — fd·inode·링크, [data-structure/33-filesystem](../../data-structure/33-filesystem/2-summary.md) — 트리 파일 시스템 구현 연습
- 후속·연결
  - [23-crash-consistency-and-journaling](../23-crash-consistency-and-journaling/2-summary.md) — 여러 블록을 고치는 도중 전원이 나가면
  - [24-fsync-and-durability](../24-fsync-and-durability/2-summary.md) — 디렉터리 항목까지 디스크에 남기기
  - [architecture/16-storage-media-workload](../../systems/storage-media-workload/2-summary.md) — HDD 탐색 비용이 FFS 설계의 이유
  - [10-paging-and-tlb](../10-paging-and-tlb/2-summary.md) — 다단계 페이지 테이블(다단계 인덱스와 같은 발상)
  - [14-mmap-and-page-cache](../14-mmap-and-page-cache/2-summary.md) — 페이지 캐시
- 교재
  - OSTEP 40장 "File System Implementation" — 40.2 vsfs 배치, 40.3 inode·다단계 인덱스·extent, 40.4 디렉터리, 40.6 접근 경로(Figure 40.3·40.4), 40.7 캐시 <https://pages.cs.wisc.edu/~remzi/OSTEP/file-implementation.pdf>
  - OSTEP 41장 "Fast File System (FFS)" — 41.1 대역폭 2%, 41.3 실린더 그룹, 41.4 배치 정책, 41.6 large-file exception <https://pages.cs.wisc.edu/~remzi/OSTEP/file-ffs.pdf>
- 커널 문서·소스
  - Documentation/filesystems/ext4/ — blockgroup.rst(블록 그룹·사본), ifork.rst(`i_block` 60바이트·extent 4개·`ee_len` 32768), directory.rst(htree·`indirect_levels` 2/3) <https://docs.kernel.org/filesystems/ext4/>
  - Documentation/filesystems/vfs.rst — dcache·inode·file 객체 <https://docs.kernel.org/filesystems/vfs.html>
  - fs/ext4/namei.c `ext4_dx_add_entry`(index full → `-ENOSPC`), fs/ext4/ialloc.c(inode 할당 실패 `-ENOSPC`)
- man: mke2fs(8) `-i`·`-N`·`-m`·`-T`, tune2fs(8) `-m`, mkfs.xfs(8) `maxpct`, df(1) `-i`, statvfs(3), filefrag(8), debugfs(8), dumpe2fs(8)
- 로컬 재현(리눅스 7.0, e2fsprogs 1.47.0): 16 MiB ext4 이미지로 블록 그룹 배치 확인·inode 고갈(debugfs), `filefrag`로 extent 확인, `lsattr -d`로 인덱스 디렉터리 확인, `stat -f`로 예약 블록 확인
