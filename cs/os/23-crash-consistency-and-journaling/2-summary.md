# os/23-crash-consistency-and-journaling — 블록 세 개를 고치는 도중 전원이 나가면 — 정리 (힌트)

## 해결하는 문제

파일 끝에 4 KB 한 블록을 덧붙이는 일조차 디스크의 **세 곳**을 고친다(22번의 구조).

```text
  고칠 것                  이유
  inode       I[v1]->I[v2]  새 블록 위치와 늘어난 크기를 적는다
  데이터 비트맵 B[v1]->B[v2]  새 블록을 "사용 중"으로 표시한다
  데이터 블록  Db             실제 내용을 쓴다
```

디스크는 한 번에 한 블록씩 쓴다.\
세 번 쓰는 사이 언제든 전원이 나가거나 커널이 멈출 수 있다.\
그러면 디스크에는 "일부만 바뀐" 상태가 남는다. 이것이 **크래시 일관성** 문제다.

  - *크래시 일관성(crash consistency)*: 갱신 도중 크래시가 나도 디스크 위 자료구조가 서로 모순되지 않게 하는 성질이다.

쉬운 예: 은행 이체다.
- A 계좌에서 빼고 B 계좌에 넣는다. 빼고 나서 넣기 전에 정전이 나면 돈이 사라진다.
- 은행은 먼저 "A→B 10만 원 이체"를 **장부에 적고**, 그다음 두 계좌를 고친다.
- 정전 뒤에는 장부를 보고 끝나지 않은 이체를 마저 한다.

똑같은 구조다.\
파일 시스템도 고칠 내용을 먼저 **저널(장부)**에 적고, 그다음 제자리를 고친다.

실무 예:
- 정전 뒤 부팅하니 편집하던 설정 파일이 **0바이트**다(ext4 지연 할당, 2009).
- DB 페이지 8 KB를 쓰는 도중 크래시 → 앞 절반은 새것, 뒤 절반은 옛것인 **찢어진 쓰기(torn write)**.
- 큰 디스크에서 fsck가 몇 시간 걸려 서비스가 못 올라온다.

## 동작·원리

### 크래시 시나리오 — 세 번의 쓰기 중 일부만 성공

OSTEP 42.1의 예다.

```text
  디스크에 남은 것          결과
  Db만                     문제없음 (아무도 안 가리키는 블록 = 쓰기가 없었던 것과 같음)
  I[v2]만                  inode가 쓰레기 블록을 가리킴 + 비트맵은 "빈칸" -> 불일치
  B[v2]만                  비트맵은 "사용 중"인데 아무도 안 가리킴 -> 공간 누수(불일치)
  I[v2] + B[v2]            메타데이터는 일관적, 그러나 블록 5번엔 쓰레기 데이터
  I[v2] + Db               inode는 올바른 데이터를 가리키지만 비트맵과 불일치
  B[v2] + Db               비트맵은 사용 중, 어느 inode 것인지 모름 -> 불일치
```

- 두 종류의 문제가 섞여 있다.
  - **메타데이터 불일치**: inode와 비트맵이 서로 다른 말을 한다.
  - **쓰레기 데이터**: 메타데이터는 맞는데 가리키는 블록 내용이 옛것·쓰레기다.

### 해법 1 — fsck: 크래시 뒤에 전부 검사한다

```text
  e2fsck
  Pass 1: inode·블록 검사        (모든 inode를 읽고 쓰는 블록 목록 작성)
  Pass 2: 디렉터리 구조
  Pass 3: 디렉터리 연결성        (어디에도 안 매달린 디렉터리 -> lost+found)
  Pass 4: 참조 수(링크 수)
  Pass 5: 그룹 요약·비트맵       (Pass 1 결과와 비트맵 비교)
```

- 비트맵과 inode가 다르면 **inode를 믿고** 비트맵을 고친다(OSTEP 42.2).
- 로컬 재현(예시): 16 MiB ext4 이미지에서 파일이 쓰는 블록 1291을 debugfs `freeb`로 비트맵에서 지웠다. `e2fsck -fn`이 Pass 5에서 `Block bitmap differences: +1291`을 보고했다.
- 한계 두 가지
  - **느리다**: 디스크 전체를 읽는다. 디스크가 커질수록 몇 분·몇 시간이 걸린다(OSTEP 42.2).
  - **쓰레기 데이터는 못 고친다**: I[v2] + B[v2] 경우는 메타데이터가 일관적이라 fsck 눈에는 정상이다.

### 해법 2 — 저널링(WAL): 먼저 적고, 그다음 고친다

```text
  디스크:  [ 슈퍼블록 | 저널 (원형 로그) | 그룹 0 | 그룹 1 | ... ]

  1) 저널 쓰기     저널: [TxB id=1][I v2][B v2][Db]          (완료 대기)
  2) 저널 커밋     저널: [TxB id=1][I v2][B v2][Db][TxE id=1]  (TxE 쓰기 완료 = 커밋)
  3) 체크포인트    I v2, B v2, Db 를 제자리에 쓴다
  4) 해제          저널 슈퍼블록에서 트랜잭션 1을 "끝남"으로 표시 -> 공간 재사용
```

- **커밋 지점은 TxE 기록**이다. OSTEP은 디스크가 512바이트 쓰기의 원자성을 보장한다고 가정한다. 그래서 TxE를 512바이트 한 블록으로 만든다(OSTEP 42.3).
- TxE를 따로 늦게 쓰는 이유: 여러 블록을 한꺼번에 내면 디스크가 순서를 바꿔 쓸 수 있다. TxE만 먼저 도착하고 중간 블록이 빠진 채 크래시가 나면, 복구가 쓰레기를 "커밋됨"으로 재생한다.
  - 트랜잭션 **체크섬**을 넣으면 이 대기를 없앨 수 있다. 복구 때 체크섬이 안 맞으면 그 트랜잭션을 버린다(OSTEP 42.3). ext4에서는 `journal_async_commit` 마운트 옵션이 커밋 블록을 앞선 descriptor 블록의 완료를 기다리지 않고 쓰게 하며, 내부적으로 `journal_checksum`을 켠다. `journal_checksum`만으로는 트랜잭션 체크섬으로 손상을 감지하게 할 뿐이다(ext4 admin guide).
    - 단 기본 모드 `data=ordered`와는 함께 쓸 수 없다. 마운트는 실패하고 리마운트는 `EINVAL`이며, 커널 로그에 "can't mount with journal_async_commit in data=ordered mode"가 남는다(`fs/ext4/super.c`). `data=journal`·`data=writeback`에서만 쓴다.

**복구(redo)**

```text
  크래시 시점                 부팅 후 복구
  TxE 쓰기 전               -> 그 트랜잭션은 없던 일 (건너뜀)
  TxE 쓴 뒤 ~ 체크포인트 중   -> 저널의 블록을 제자리에 다시 쓴다 (몇 번 써도 결과 같음)
```

- 커밋된 트랜잭션만 재생한다. 재생은 같은 블록을 같은 내용으로 덮는 일이라 여러 번 해도 된다.
- 복구 시간은 디스크 크기가 아니라 **저널 크기**에 비례한다.
- 저널은 **원형**으로 재사용한다. 그래서 체크포인트 뒤 "해제" 단계가 있다(OSTEP 42.3).
- 블록을 지웠다가 다른 용도로 재사용한 경우를 위해 **revoke 레코드**를 둔다. 재생할 때 revoke된 블록은 다시 쓰지 않는다(OSTEP 42.3).

  - *WAL(write-ahead logging)*: 실제 자리를 고치기 **전에** 무엇을 할지 로그에 먼저 적는 규칙이다. DB의 WAL과 같은 발상이다.
  - *체크포인트*: 저널에 적힌 변경을 제자리에 반영하는 단계다.

### 데이터까지 저널에 쓸까 — 세 가지 모드 (ext4)

```text
  data=journal    데이터+메타데이터 모두 저널에   -> 데이터를 두 번 씀. 가장 느림(보통)
  data=ordered(*) 데이터를 제자리에 먼저 쓰고,     -> 쓰레기 데이터 없음
                  그다음 메타데이터 저널 커밋
  data=writeback  데이터 순서 보장 없음            -> 크래시 뒤 최근 파일에 옛 데이터가 보일 수 있음
  (*) 기본값
```

- 대부분 쓰기는 데이터다. 데이터를 저널에 두 번 쓰면 I/O가 크게 는다. 그래서 흔한 방식은 **메타데이터만 저널링(ordered)**이다(OSTEP 42.3).
- ordered의 핵심 규칙: "가리켜지는 것을 가리키는 것보다 먼저 쓴다". 데이터 블록이 먼저 디스크에 있어야 inode가 쓰레기를 가리키지 않는다(OSTEP 42.3).
  - `data=ordered`: 모든 데이터를 제자리에 먼저 내보낸 뒤 메타데이터를 저널에 커밋한다(ext4 admin guide).
  - `data=writeback`: 크래시 뒤 최근에 쓴 파일에 옛(다른 파일의) 데이터가 드러날 수 있다. 보안 문제가 될 수 있다(ext4 admin guide).
  - `data=journal`: 지연 할당과 `O_DIRECT`를 끈다(ext4 admin guide).
- `commit=`(기본 5초): 진행 중 트랜잭션의 최대 나이다. 정전 때 최대 약 5초의 메타데이터 변경을 잃을 수 있지만 파일 시스템은 망가지지 않는다(ext4 admin guide).
- 저널 커밋의 순서가 실제 매체에 지켜지려면 디스크 쓰기 캐시를 비우는 **barrier(flush)**가 필요하다. ext4 기본값은 켜짐이다(ext4 admin guide `barrier=1`).

### 0바이트 파일 — 지연 할당과 "fsync 없는 교체"

```text
  앱:  fd = open("conf.new", O_TRUNC); write(fd, ...); close(fd); rename("conf.new", "conf")
       (fsync 없음)

  ext3 ordered                            ext4 지연 할당(delalloc)
  데이터 블록이 5초 커밋 전에 먼저 나감        블록을 아직 할당 안 함 -> 저널 커밋이 데이터를 기다리지 않음
  -> 크래시해도 대개 새 내용                  rename(메타데이터)만 먼저 커밋
                                          -> 크래시 뒤 "conf"는 새 inode, 크기 0
```

- 2009년 ext4 초기 사용자가 크래시 뒤 최근에 쓴 파일이 대부분 0바이트가 되는 문제를 보고했다(LWN 322823).
- 원인: 지연 할당은 블록 할당을 최대한 늦춘다. 할당되지 않은 블록은 다음 저널 커밋에 딸려 나가지 않는다. 데이터가 나가기까지 기본 설정으로 1분 가까이 걸릴 수 있다(LWN 322823). `dirty_expire_centisecs` 기본은 30초다(작성 환경 3000, 예시).
- ext3가 "5초 안에 데이터도 거의 디스크에" 있게 해 준 것은 설계의 부산물이었다. POSIX는 이를 요구하지 않는다(LWN 322823).
- 완화: ext4 `auto_da_alloc`(기본 켜짐)은 rename·truncate로 교체하는 패턴을 알아채고 새 파일 데이터를 rename 커밋 전에 내보낸다(ext4 admin guide).
- 근본 해법은 **앱이 fsync를 부르는 것**이다(24번).

### 찢어진 쓰기(torn write)

```text
  DB 페이지 8 KB = 섹터 16개
  크래시 시점:  [새 새 새 새 새 새 새 새 | 옛 옛 옛 옛 옛 옛 옛 옛]
                → 어느 버전도 아닌 페이지
```

- 파일 시스템 저널은 **파일 시스템 메타데이터**를 지킨다. ordered 모드는 앱 데이터 페이지의 원자적 기록을 약속하지 않는다.
- 그래서 DB가 스스로 막는다.
  - PostgreSQL `full_page_writes`: 체크포인트 뒤 처음 고치는 페이지는 페이지 전체를 WAL에 쓴다. 끄면 복구 불가 또는 조용한 손상이 생길 수 있다(PostgreSQL 문서).
  - InnoDB **doublewrite buffer**: 페이지를 제자리에 쓰기 전에 doublewrite 영역에 먼저 쓴다. 중간에 끊기면 거기서 온전한 사본을 찾는다(MySQL 문서).
- 페이지에 체크섬이 있으면 찢어진 페이지를 **알아챌** 수는 있다(33번). 고치려면 사본이 필요하다.

### 해법 3 — 제자리에 쓰지 않는다: COW와 LFS

```text
  COW (ZFS·btrfs)                          LFS
  옛 블록은 그대로 두고 새 위치에 씀           모든 변경을 메모리 세그먼트에 모아 한 번에 순차 기록
  새 블록 -> 새 부모 -> ... -> 새 루트        [D][I][imap][D][I][imap] ... (로그 끝에 계속)
  마지막에 루트 포인터 하나를 바꿈             체크포인트 영역(CR) 2개가 최신 imap 위치를 가리킴
  -> 루트 교체 전 크래시 = 옛 트리 그대로        CR을 번갈아 쓰고 앞뒤 타임스탬프로 온전한 것 선택
```

- **COW(copy-on-write)**: 파일·디렉터리를 제자리에 덮어쓰지 않는다. 새 위치에 쓰고, 여러 갱신 뒤 루트 구조를 새 것으로 바꾼다(OSTEP 42.4).
- **LFS(log-structured file system)**: 디스크 전체를 로그로 쓴다(OSTEP 43).
  - inode 위치가 계속 바뀌므로 **inode 맵(imap)**으로 "inode 번호 → 현재 위치"를 찾는다.
  - 체크포인트 영역(CR)은 약 30초마다 갱신한다. CR 두 개를 번갈아 쓰고, 머리·꼬리 타임스탬프가 맞는 최신 CR을 쓴다(OSTEP 43.12).
  - 마지막 CR 이후의 세그먼트는 **롤 포워드**로 살린다(OSTEP 43.12).
  - 대가: 옛 버전이 쓰레기로 남는다. **청소(cleaning)**로 세그먼트를 모아 비워야 한다. 자주 덮이는 hot 세그먼트는 늦게, cold는 일찍 청소한다(OSTEP 43.11).
- 그 밖에: Soft Updates(쓰기 순서를 세밀히 정렬, 구현이 복잡), backpointer 기반 일관성, optimistic crash consistency(OSTEP 42.4).

## 쓰이는 자료구조·알고리즘

- **WAL(저널) = 원형 로그** — 앞에서 쓰고 체크포인트가 끝난 꼬리를 해제한다. DB WAL과 같은 규칙이다.
- **redo 복구** — 커밋된 트랜잭션을 다시 적용한다. 재적용해도 결과가 같다(멱등).
- **커밋 레코드 + 체크섬** — "여기까지 온전히 썼다"를 한 블록의 원자적 쓰기나 체크섬으로 판정한다.
- **로그 구조 + 인덱스(imap)** — 추가만 하는 로그에 위치 색인을 얹는다. LSM 트리와 같은 발상이다. [data-structure/24-lsm-tree](../../data-structure/24-lsm-tree/2-summary.md)
- **COW 트리(섀도 페이징)** — 잎에서 루트까지 새 경로를 만들고 루트 포인터만 원자적으로 바꾼다. [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md)
- **가비지 컬렉션(청소)** — 살아 있는 블록을 옮기고 세그먼트를 비운다. SSD의 FTL도 같은 문제를 안고 있다. [systems/nand-flash](../../systems/nand-flash/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 내 파일 시스템의 저널 설정을 안다

```bash
findmnt -no FSTYPE,OPTIONS /data           # data=ordered 등 (기본값은 표시 안 될 수 있음)
cat /proc/fs/ext4/<dev>/options | grep -E 'data=|commit=|barrier|auto_da_alloc'
dumpe2fs -h /dev/<dev> | grep -iE 'features|journal'   # has_journal, 저널 크기
cat /proc/sys/vm/dirty_expire_centisecs    # 더러운 페이지가 기다리는 최대 시간(1/100초)
```

### 2. 앱의 파일 교체는 "임시 파일 + fsync + rename + 디렉터리 fsync"로

- 크래시 일관성은 파일 시스템 **메타데이터**를 지킨다. 앱 파일 내용의 원자적 교체는 앱이 fsync와 rename으로 만든다.
- 코드는 24번 「적용」에 있다. 여기서는 규칙만 적는다.

```text
  write(tmp) -> fsync(tmp) -> rename(tmp, real) -> fsync(dir)
      |             |               |                   |
    내용 준비     내용을 디스크에    이름을 원자적으로     이름 변경을 디스크에
```

### 3. 크래시 뒤 점검

```bash
dmesg | grep -iE 'EXT4-fs|recovery|journal'     # "recovery complete" 등 저널 재생 흔적
tune2fs -l /dev/<dev> | grep -iE 'state|mount count|last checked'
e2fsck -fn /dev/<dev>    # 언마운트(또는 읽기 전용) 상태에서 검사만, 고치지 않음
```

- 마운트된 파일 시스템에 쓰기 모드로 e2fsck를 돌리지 않는다. 먼저 `-n`으로 본다.

### 4. 연습 — 루트 없이 이미지로 fsck 보기

```bash
truncate -s 16M j.img && mke2fs -q -t ext4 j.img
echo hi > a && debugfs -w -R 'write a a' j.img
debugfs -R 'bmap a 0' j.img            # 파일의 첫 블록 번호
debugfs -w -R 'freeb <그 번호>' j.img   # 비트맵만 "빈칸"으로 = I[v2]+Db, B[v1] 상황 흉내
e2fsck -fn j.img                       # Pass 5: Block bitmap differences
```

## 장애 시나리오와 대처

### 1. 정전 뒤 설정 파일이 0바이트

- **현상**: 재부팅 뒤 앱이 설정·상태 파일을 못 읽고 기본값으로 뜨거나 죽는다.
- **보이는 형태**: `ls -l`에 크기 0. JSON 파서 `Unexpected end of JSON input`, Java `EOFException` 류.
- **원인**
  - 앱이 `open(O_TRUNC)`→`write`→`close` 또는 `write(new)`→`rename`을 **fsync 없이** 했다.
  - 지연 할당으로 데이터 블록이 아직 할당·기록되지 않았는데 메타데이터(크기 0·rename)가 먼저 커밋되었다(LWN 322823).
- **대처**
  - 쓰기 패턴을 24번의 "임시 파일 + fsync + rename + 디렉터리 fsync"로 바꾼다.
  - `auto_da_alloc`(기본 켜짐)이 흔한 패턴을 완화하지만 보장은 아니다. `O_TRUNC` 뒤 덮어쓰기는 여전히 위험하다.
  - 읽을 때 빈 파일·파싱 실패를 감지하고 백업 사본으로 되돌리는 경로를 둔다.

### 2. 찢어진 DB 페이지 (torn write)

- **현상**: 크래시 뒤 DB가 특정 페이지를 못 읽는다.
- **보이는 형태**: PostgreSQL `invalid page in block N of relation "..."`(bufmgr.c), 데이터 체크섬이 켜져 있으면 `page verification failed, calculated checksum ... but expected ...`(bufpage.c). InnoDB는 로그에 페이지 손상 메시지를 남긴다.
- **원인**: 페이지(8 KB·16 KB)가 섹터 몇 개만 새것으로 쓰인 채 크래시가 났다. 파일 시스템 저널은 앱 데이터 페이지를 원자적으로 쓰지 않는다.
- **대처**
  - `full_page_writes`(PostgreSQL)·doublewrite(InnoDB)를 끄지 않는다. 쓰기량을 줄이려고 끄면 조용한 손상 위험을 산다.
  - PostgreSQL 문서는 `full_page_writes`를 `fsync`를 끌 때와 같은 조건(DB 전체를 외부 데이터로 쉽게 다시 만들 수 있을 때)에서만 끄라고 한다. InnoDB는 원자적 쓰기를 지원하는 Fusion-io 장치(NVMFS)에서만 doublewrite를 자동으로 끈다(MySQL 8.4 문서).

### 3. 크래시 뒤 부팅이 fsck에서 멈춘다

- **현상**: 재부팅이 몇 십 분·몇 시간 끝나지 않는다. 콘솔에 fsck 진행률이 보인다.
- **보이는 형태**: e2fsck의 `... contains a file system with errors, check forced.`(e2fsck/unix.c), systemd `systemd-fsck@...` 서비스가 오래 걸림.
- **원인**
  - 저널 재생으로 해결되지 않는 오류가 기록되어 전체 검사가 강제되었다.
  - 또는 저널이 없는 파일 시스템(ext2 등)이라 매번 전체 검사를 한다. 전체 검사는 디스크 크기에 비례한다.
- **대처**: 큰 볼륨은 저널링 파일 시스템을 쓴다. 전체 fsck 시간을 복구 계획(RTO)에 넣는다. 반복되면 디스크 자체를 의심한다(33번 SMART·스크럽).

### 4. 저널 오류로 읽기 전용 재마운트

- **현상**: 운영 중 갑자기 모든 쓰기가 실패한다.
- **보이는 형태**: `EROFS`(`Read-only file system`). `dmesg`에 `EXT4-fs error ...`, `Aborting journal on device ...`(fs/jbd2/journal.c), `Remounting filesystem read-only`(fs/ext4/super.c).
- **원인**: 디스크 I/O 오류나 메타데이터 손상을 감지했다. `errors=remount-ro`면 더 망가지지 않게 읽기 전용으로 바꾼다(ext4 admin guide `errors=`).
- **대처**: 쓰기를 강제로 되살리지 않는다. 앱을 멈추고, 디스크 상태(`smartctl`)를 보고, 언마운트 뒤 `e2fsck`한다. 하드웨어 문제면 교체 후 복구한다.

## 핵심 문장

- 한 번의 논리적 갱신이 여러 블록을 고친다. 그 사이 크래시가 나면 inode·비트맵이 모순되거나 쓰레기 데이터를 가리킨다.
- fsck는 크래시 뒤 전체를 검사해 메타데이터를 맞춘다. 느리고, 쓰레기 데이터는 못 고친다.
- 저널링은 먼저 저널에 적고(TxB…TxE) 커밋한 뒤 제자리에 쓴다. 복구는 커밋된 트랜잭션만 재생하므로 저널 크기에 비례한다.
- ext4 기본 `data=ordered`는 데이터를 먼저 쓰고 메타데이터를 커밋해 쓰레기 데이터를 막는다. 데이터 자체를 원자적으로 쓰지는 않는다.
- 크래시 뒤 0바이트 파일은 지연 할당 + fsync 없는 교체의 결과다. 앱 파일의 원자적 교체는 앱이 fsync와 rename으로 만든다.
- COW·LFS는 제자리에 덮어쓰지 않고 루트(또는 체크포인트) 포인터만 바꿔 일관성을 얻는다. 대가는 청소다.

## 관련 주제·근거

- 선행: [22-file-system-implementation](../22-file-system-implementation/2-summary.md) — inode·비트맵·블록 그룹
- 후속·연결
  - [24-fsync-and-durability](../24-fsync-and-durability/2-summary.md) — 앱이 크래시 일관성을 만드는 법
  - [33-data-integrity-checksums](../33-data-integrity-checksums/2-summary.md) — 찢어진 페이지·손상 감지
  - [32-raid](../32-raid/2-summary.md) — RAID의 같은 문제(consistent-update, write hole)
  - [database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md)(WAL 규칙·group commit)
  - [38-os-incidents](../38-os-incidents/2-summary.md)(ext4 0바이트 파일 2009)
- 교재
  - OSTEP 42장 "Crash Consistency: FSCK and Journaling" — 42.1 시나리오, 42.2 fsck, 42.3 데이터·메타데이터 저널링·512바이트 원자성·revoke, 42.4 Soft Updates·COW·BBC <https://pages.cs.wisc.edu/~remzi/OSTEP/file-journaling.pdf>
  - OSTEP 43장 "Log-structured File Systems" — 43.5 imap, 43.6 CR, 43.11 청소 정책, 43.12 크래시 복구·롤 포워드 <https://pages.cs.wisc.edu/~remzi/OSTEP/file-lfs.pdf>
- 커널 문서
  - Documentation/admin-guide/ext4.rst — `data=journal|ordered|writeback`, `commit=`(5초), `barrier`, `journal_checksum`·`journal_async_commit`, `auto_da_alloc`, `delalloc`, `errors=` <https://docs.kernel.org/admin-guide/ext4.html>
  - Documentation/filesystems/ext4/journal.rst — jbd2 저널 형식
  - `fs/ext4/super.c` `ext4_load_and_init_journal()`·`__ext4_remount()` — `journal_async_commit` + `data=ordered` 거부. `fs/jbd2/commit.c` — async commit이면 커밋 레코드를 저널 버퍼 완료 대기 전에 제출 <https://github.com/torvalds/linux/blob/master/fs/ext4/super.c>
- LWN, Jonathan Corbet, "ext4 and data loss"(2009-03-11) <https://lwn.net/Articles/322823/>
- DB 문서
  - PostgreSQL `full_page_writes` <https://www.postgresql.org/docs/current/runtime-config-wal.html>
  - MySQL 8.4 InnoDB Doublewrite Buffer <https://dev.mysql.com/doc/refman/8.4/en/innodb-doublewrite-buffer.html>
- 로컬 재현(리눅스 7.0, e2fsprogs 1.47.0): ext4 이미지에서 debugfs `freeb`로 비트맵 불일치를 만들고 `e2fsck -fn` Pass 5 보고 확인, `dumpe2fs -h`로 저널 크기(1024블록) 확인, `dirty_expire_centisecs` 3000 확인
