# os/24-fsync-and-durability — write가 돌아왔다고 디스크에 있는 게 아니다 — 정리 (힌트)

## 해결하는 문제

`write()`가 성공을 돌려주면 데이터는 어디에 있을까?\
대개 **커널 메모리(페이지 캐시)**에 있다. 디스크에는 몇 초에서 수십 초 뒤에 간다.

그 사이 전원이 나가면 사라진다.\
평소에는 이 지연이 이득이다. 쓰기를 모아 한 번에 내고, 금방 지워질 임시 파일은 아예 디스크에 안 쓴다.

그러나 "커밋되었습니다"라고 답한 DB, "저장했습니다"라고 알린 앱은 거짓말을 한 셈이 된다.\
**내구성(durability)**을 약속하려면 "지금 이 데이터를 디스크까지 내려보내고, 끝나면 알려 달라"는 수단이 필요하다. 그것이 `fsync`다.

  - *내구성*: 성공을 알린 데이터가 크래시·전원 차단 뒤에도 남아 있는 성질이다.

쉬운 예: 편지 부치기다.
- 우체통에 넣은 순간(`write`) 편지는 아직 우체통 안이다. 수거 차(flusher)가 몇 시간마다 온다.
- 등기로 보내고 "배달 완료" 확인을 받을 때까지 기다리면(`fsync`) 확실하다. 대신 느리다.
- 편지를 넣었다고 받는 사람 **주소록**(디렉터리)에 새 주소가 적힌 것은 아니다. 주소록도 따로 확인해야 한다.

똑같은 구조다.\
`fsync(file)`은 파일 내용과 inode를, `fsync(dir)`은 디렉터리 항목(이름)을 디스크에 보낸다.

실무 예:
- 설정 파일을 "임시 파일에 쓰고 rename"으로 원자적으로 바꿨는데, 크래시 뒤 **옛 파일이 돌아와** 있다(디렉터리 fsync 누락).
- 스토리지 오류로 `fsync`가 `EIO`를 냈다. 재시도하니 성공했다. 그런데 데이터는 이미 사라졌다(fsyncgate, 2018).

## 동작·원리

### 쓰기가 거치는 층

```text
  앱 버퍼          BufferedOutputStream / stdio FILE* / Node Writable 내부 버퍼
     | flush() / fflush()           <- 여기까지는 아직 프로세스 메모리
     v
  페이지 캐시       write() 성공 = 여기 도착 ("dirty" 페이지)
     | 백그라운드 writeback (dirty_expire_centisecs, 기본 30초) 또는 fsync()
     v
  장치 쓰기 캐시    디스크·SSD 내부 휘발성 캐시 ("write back"이면 완료 신호가 매체보다 먼저)
     | 캐시 flush 명령(REQ_PREFLUSH) / FUA 쓰기
     v
  비휘발성 매체     여기까지 와야 전원 차단을 견딘다
```

- `flush()`·`fflush()`는 앱 버퍼를 커널로 넘길 뿐이다. 디스크 보장이 아니다.
- `write()` 성공은 페이지 캐시 도착이다. 커널은 더러운 페이지를 나중에 내보낸다.
  - 작성 환경: `dirty_expire_centisecs=3000`(30초), `dirty_writeback_centisecs=500`(5초)(예시, `/proc/sys/vm`).
- 많은 저장 장치는 **휘발성 쓰기 캐시**를 가진다. 데이터가 매체에 닿기 전에 완료를 알린다. 그래서 OS는 fsync·sync·unmount 때 장치 캐시를 비우라고 명령한다(block/writeback_cache_control.rst).
  - `/sys/block/<dev>/queue/write_cache`가 `write back`이면 장치가 휘발성 캐시를 쓴다고 커널이 본다. 이 값을 `write through`로 바꾸면 커널이 flush를 안 보내게 되어 위험할 수 있다(ABI sysfs-block). 작성 환경 NVMe는 `write back`이었다(예시).

로컬 재현(예시, 리눅스 7.0, ext4 on NVMe):

```text
write 32MiB: 10.2 ms | fsync: 12.8 ms | Dirty kB: before=16584 afterWrite=49352 afterFsync=16704
200 small writes: 0.09 ms | 200 writes+fdatasync: 1075.8 ms
```

- write 직후 `/proc/meminfo`의 `Dirty`가 약 32 MiB 늘었다. fsync 뒤 원래대로 줄었다.
- 17바이트 write 200번은 0.09 ms, 매번 `fdatasync`를 붙이면 약 1초였다(한 번에 약 5 ms). 내구성의 값이다.

### fsync와 fdatasync

```text
  fsync(fd)       파일 데이터 + 메타데이터(inode: 크기·mtime·블록 위치 ...) + 장치 캐시 flush
                  장치가 완료를 보고할 때까지 블록
  fdatasync(fd)   데이터 + "다음 읽기에 필요한" 메타데이터만 (크기·블록 위치 O, mtime·atime X)
```

- `fsync`는 수정된 데이터를 저장 장치로 보내고, 장치 캐시가 있으면 비우거나 통과시킨다. 장치가 완료를 보고할 때까지 기다린다(fsync(2)).
- `fdatasync`는 읽기에 필요 없는 메타데이터(`st_mtime` 등)는 내보내지 않는다. 파일 크기 변경은 필요하므로 내보낸다(fsync(2)).
  - 그래서 **덮어쓰기**만 하는 미리 할당된 로그 파일에서 `fdatasync`가 이득이다. 크기가 늘어나는 append는 어차피 메타데이터를 쓴다.
  - 단 "미리 할당"은 **실제로 0 등을 한 번 써 둔** 파일이어야 한다. `fallocate`만 한 영역은 ext4에서 unwritten extent다. 첫 쓰기 때 written으로 바꾸는 변경이 "읽기에 필요한 메타데이터"라서 `fdatasync`도 저널 커밋을 기다린다(`fs/ext4/extents.c`).
    - *unwritten extent*: 블록은 잡혀 있지만 "아직 안 씀 — 읽으면 0"으로 표시된 구간.
  - 로컬 재현(예시, 리눅스 7.0, ext4): 4 KB 덮어쓰기+`fdatasync` 200번이 `fallocate`만 한 파일에서 1556 ms, 0을 써 둔 파일에서 492 ms였다. 두 번째 덮어쓰기부터는 둘 다 약 495 ms로 같았다.
- 오래된 커널이나 일부 파일 시스템의 fsync는 장치 캐시를 비우지 못할 수 있다. 그때는 장치 캐시를 꺼야 안전하다(fsync(2) HISTORY).
- 비슷해 보이지만 보장이 아닌 것
  - `O_DIRECT`: 페이지 캐시를 건너뛰려 할 뿐, `O_SYNC` 같은 보장은 없다(open(2)).
  - `sync_file_range`: 메타데이터를 안 쓰고 장치 캐시도 안 비운다. man은 "extremely dangerous"라고 경고한다(sync_file_range(2)).
- 대신 쓸 수 있는 것: `O_DSYNC`(매 write가 fdatasync처럼), `O_SYNC`(매 write가 fsync처럼)(open(2)).

### 파일 fsync는 이름을 보장하지 않는다 — 디렉터리 fsync

```text
  새 파일 "a.dat" 만들기
    디렉터리 "/data" 블록:  [ ... | "a.dat" -> inode 77 ]   <- 디렉터리의 데이터
    inode 77:              크기·블록 위치                  <- 파일의 메타데이터
    데이터 블록:             내용                          <- 파일의 데이터

  fsync(fd_a)     -> inode 77 + 데이터   (디렉터리 항목은 "반드시"는 아님)
  fsync(fd_dir)   -> "/data" 디렉터리 항목
```

- `fsync()`가 파일을 담은 디렉터리의 항목까지 디스크에 보낸다는 보장은 없다. 그러려면 디렉터리 fd에도 `fsync()`해야 한다(fsync(2)).
- 이름은 **디렉터리의 데이터**이기 때문이다. 새로 만든 파일, `rename`한 파일, `unlink`한 파일은 모두 디렉터리를 바꾼다.
- 실제로 파일 fsync만으로 디렉터리 항목이 따라 나가는 파일 시스템도 있다. 그러나 파일 시스템마다 다르다. 이런 "지속성 속성"은 리눅스 파일 시스템 여섯 개 사이에서 크게 달랐다(Pillai 외, OSDI 2014).

### rename으로 원자적 교체 — 네 단계

```text
  1. fd = open("cfg.tmp", O_WRONLY|O_CREAT|O_TRUNC)
  2. write(fd, 새 내용);  fsync(fd);  close(fd)        <- 새 내용이 디스크에
  3. rename("cfg.tmp", "cfg")                        <- 이름을 원자적으로 바꿈
  4. dfd = open(".", O_RDONLY|O_DIRECTORY); fsync(dfd) <- 이름 바꿈이 디스크에

  크래시 시점별 결과
  2 전        : cfg = 옛 내용 (tmp는 반쯤 쓰였을 수 있음 -> 무시·삭제)
  2~3 사이    : cfg = 옛 내용
  3~4 사이    : cfg = 옛 내용 또는 새 내용 (둘 중 하나. 섞이지 않음)
  4 뒤        : cfg = 새 내용
```

- `rename`은 `newpath`가 있으면 **원자적으로 교체**한다. 다른 프로세스가 `newpath`가 없는 순간을 보지 않는다(rename(2)). 이것은 **실행 중 다른 프로세스에 대한** 원자성이다.
- 크래시에 대해서도 rename은 대개 원자적으로 구현된다. 옛 이름 또는 새 이름 중 하나로 남는다(OSTEP 39.8 "usually").
- 2번의 `fsync(fd)`가 빠지면: rename(메타데이터)이 데이터보다 먼저 디스크에 갈 수 있다. 크래시 뒤 `cfg`가 **빈 파일**일 수 있다(23번, ext4 지연 할당).
- 4번의 `fsync(dir)`가 빠지면: 크래시 뒤 rename 자체가 사라져 **옛 파일이 돌아올** 수 있다.
- 로컬 재현: Java와 Node 모두 아래 코드가 `fsync(파일) → rename → fsync(디렉터리)`로 나가는 것을 `strace`로 확인했다(예시, 리눅스 7.0).

### fsync가 실패하면 — fsyncgate

```text
  시간 ->
  write(A)  write(B)   [백그라운드 writeback: B 블록 쓰기 실패 EIO]
                        커널: B 페이지를 "clean"으로 표시, 오류를 파일에 기록(errseq)
  fsync() -> EIO        (오류를 한 번 보고)
  fsync() -> 0 (성공!)   재시도는 "성공". 그런데 B 데이터는 메모리에도 디스크에도 없다
```

- 버퍼 쓰기가 하드웨어 오류로 실패하면, 많은 파일 시스템은 그 페이지의 데이터를 버리고 **clean으로 표시**한다(LWN 752063).
  - 이유: 가장 흔한 I/O 오류는 USB를 잘못 뽑은 경우다. 더러운 페이지를 계속 쥐면 메모리가 고갈된다(Ts'o, LWN 752063).
- 그래서 **fsync를 재시도해 성공해도** 데이터가 디스크에 있다는 뜻이 아니다. 연구가 살핀 ext4·XFS·Btrfs는 모두 실패 후 페이지를 clean으로 표시했다(Rebello 외, USENIX ATC 2020).
- 오류 보고 방식의 변화
  - 리눅스 4.13부터 `errseq_t`로 writeback 오류를 그 데이터를 썼을 수 있는 **모든 fd**에 보고한다(fsync(2) `EIO`, PostgreSQL wiki).
  - 그래도 오류가 난 **뒤에 연** fd는 오류를 못 봤다. PostgreSQL의 checkpointer가 바로 그렇게 파일을 연다(LWN 752063).
  - 리눅스 4.17(stable 백포트)부터 "아직 아무 fd에도 보고되지 않은 오류"는 그 뒤에 연 fd에도 한 번 보고한다(commit b4678df184b3 "errseq: Always report a writeback error once").
- PostgreSQL의 대응: 데이터 파일 flush 실패 시 **PANIC**으로 죽고 WAL로 복구한다. `data_sync_retry`(기본 off)(PostgreSQL 문서, PostgreSQL 12 커밋이 9.4까지 백포트 — PostgreSQL wiki).

## 쓰이는 자료구조·알고리즘

- **더러운 페이지 추적(페이지 캐시)** — 어떤 페이지가 디스크와 다른지 표시하고 나중에 모아 쓴다(14번).
- **오류 시퀀스 카운터(`errseq_t`)** — 32비트 하나에 오류 코드(하위 비트) + 카운터(상위 비트) + "표본을 떴나" 플래그 1비트를 담는다. 구독자(fd)는 값을 표본으로 떠 두었다가 바뀌었는지로 새 오류를 안다(lib/errseq.c 주석).
- **group commit** — 여러 트랜잭션의 커밋을 fsync 한 번으로 묶어 fsync당 비용을 나눈다. 내구성 비용(로컬 재현에서 한 번 약 5 ms)을 줄이는 표준 기법이다. [database/README](../../database/README.md) `19-wal-and-logging`(미작성)
- **임시 파일 + rename = 섀도 복사** — 새 버전을 옆에 완성하고 포인터(이름) 하나를 원자적으로 바꾼다. COW 트리의 루트 교체와 같은 발상이다(23번).

## 적용 — 풀어나가는 법

### 1. 원자적 파일 교체 (C)

```c
int atomic_replace(const char *dir, const char *tmp, const char *dst,
                   const void *buf, size_t n) {
    int fd = open(tmp, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0644);
    if (fd < 0) return -1;
    if (write_all(fd, buf, n) < 0 ||      /* short write까지 처리한 헬퍼(가정) */
        fsync(fd) < 0) {                  /* EIO면 재시도하지 말고 실패로 */
        close(fd); unlink(tmp); return -1;
    }
    if (close(fd) < 0) { unlink(tmp); return -1; }
    if (rename(tmp, dst) < 0) { unlink(tmp); return -1; }
    int dfd = open(dir, O_RDONLY | O_DIRECTORY | O_CLOEXEC);
    if (dfd < 0) return -1;
    int r = fsync(dfd);                   /* rename을 디스크에 */
    close(dfd);
    return r;
}
```

### 2. Java

```java
Path dir = Paths.get("/data"), tmp = dir.resolve("cfg.tmp"), dst = dir.resolve("cfg.json");
try (FileChannel ch = FileChannel.open(tmp, CREATE, WRITE, TRUNCATE_EXISTING)) {
    ch.write(ByteBuffer.wrap(bytes));
    ch.force(true);                                   // fsync (false면 fdatasync)
}
Files.move(tmp, dst, StandardCopyOption.ATOMIC_MOVE); // rename
try (FileChannel d = FileChannel.open(dir, READ)) {
    d.force(true);                                    // 디렉터리 fsync (리눅스에서 동작 확인)
}
```

- OpenJDK의 `FileChannel.force(metaData)`는 `metaData=false`면 `fdatasync`, `true`면 `fsync`를 부른다(UnixFileDispatcherImpl.c `force0`).
- 디렉터리를 `FileChannel.open(dir, READ)`로 여는 방법은 리눅스 JDK 21에서 `fsync(dirfd)`로 나가는 것을 확인했다(로컬 재현). 다른 OS에서는 동작이 다를 수 있다 [?].
- `BufferedOutputStream.flush()`만으로는 페이지 캐시까지다.

### 3. Node.js

```js
const fs = require('node:fs');
const fd = fs.openSync('cfg.tmp', 'w');
fs.writeSync(fd, JSON.stringify(cfg));
fs.fsyncSync(fd);                 // 리눅스: fsync
fs.closeSync(fd);
fs.renameSync('cfg.tmp', 'cfg.json');
const dfd = fs.openSync('.', 'r');
fs.fsyncSync(dfd);                // 디렉터리 fsync
fs.closeSync(dfd);
```

- libuv의 `uv_fs_fsync`는 리눅스에서 `fsync`, macOS에서는 `F_FULLFSYNC`를 먼저 시도한다. macOS의 `fsync`는 드라이브 캐시를 비우지 않기 때문이다(libuv src/unix/fs.c 주석).
- `fs.writeFileSync`는 기본으로 fsync를 하지 않는다(로컬 재현: Node 18에서 strace에 fsync 0회). v21.0.0·v20.10.0부터 `flush: true` 옵션을 주면 쓰기 뒤 `fs.fsyncSync()`를 부른다(Node `fs` 문서). 그래도 rename 뒤 디렉터리 fsync는 직접 한다.

### 4. 진단

```bash
strace -f -e trace=write,fsync,fdatasync,rename,renameat2,openat -p <pid>   # fsync·rename 순서 확인
grep -E '^(Dirty|Writeback):' /proc/meminfo                                  # 내보낼 더러운 페이지 양
sysctl vm.dirty_expire_centisecs vm.dirty_writeback_centisecs vm.dirty_background_ratio vm.dirty_ratio
cat /sys/block/<dev>/queue/write_cache                                       # write back / write through
iostat -x 1          # w_await 가 fsync 지연을 반영
dmesg -T | grep -iE 'I/O error|blk_update_request|EXT4-fs (error|warning)'   # writeback 오류 흔적
```

## 장애 시나리오와 대처

### 1. fsync `EIO` 후 재시도 "성공" → 조용한 유실 (fsyncgate)

- **현상**: 스토리지 순간 장애 뒤 DB가 계속 돌았다. 며칠 뒤 일부 데이터가 없거나 옛 값이다.
- **보이는 형태**
  - 장애 시점 `dmesg`에 블록 장치 I/O 오류.
  - 앱 로그에 fsync 실패 1회 뒤 재시도 성공. 이후 오류 없음.
  - PostgreSQL(12 커밋과 백포트 버전)은 대신 `could not fsync file "...": Input/output error`를 PANIC 수준으로 내고 죽는다. 기본 `data_sync_retry=off`에서 `data_sync_elevel(ERROR)`가 PANIC이 된다(src/backend/storage/sync/sync.c, PostgreSQL 문서).
- **원인**
  - 실패한 페이지는 clean으로 표시되어 버려졌다. 두 번째 fsync는 보낼 더러운 페이지가 없어 성공한다(LWN 752063, Rebello 외 2020).
  - 오류 전에 연 fd가 없으면 오류를 아예 못 볼 수도 있었다(4.17 이전).
- **대처**
  - fsync 실패를 **재시도로 덮지 않는다**. 그 파일의 최근 쓰기는 잃었다고 보고, 로그(WAL)·복제본에서 다시 만든다. PostgreSQL처럼 PANIC 뒤 복구가 가장 단순하다.
  - `data_sync_retry=on` 같은 설정은 OS의 동작을 확인한 뒤에만 켠다(PostgreSQL 문서).
  - 장기적으로는 Direct I/O로 어떤 쓰기가 실패했는지 직접 아는 설계가 권해졌다(LWN 752063).

### 2. 디렉터리 fsync 누락 → rename이 사라짐

- **현상**: 전원 차단 뒤 설정·상태 파일이 **예전 버전**으로 돌아왔다. 또는 새로 만든 파일이 통째로 없다. 파일 내용 자체는 멀쩡하다.
- **보이는 형태**: 에러는 없다. 앱이 오래된 설정·오래된 오프셋으로 뜬다. 메시지 큐 소비자가 이미 처리한 메시지를 다시 처리한다.
- **원인**: 새 파일 생성·rename은 디렉터리를 바꾼다. 파일 fsync만 하고 디렉터리 fsync를 안 했다. 디렉터리 항목이 디스크에 가기 전에 크래시가 났다(fsync(2), OSTEP 39.7).
- **대처**: rename·create 뒤에 부모 디렉터리를 fsync한다. 여러 파일이면 모두 끝낸 뒤 디렉터리 fsync 한 번으로 묶는다. 크래시 테스트 도구(ALICE류)나 전원 차단 테스트로 검증한다(Pillai 외 2014).

### 3. fsync 없는 교체 → 크래시 뒤 0바이트 파일

- **현상**: 23번 장애 1과 같다.
- **보이는 형태**: 크기 0 파일, 파싱 오류.
- **원인**: write 뒤 fsync 없이 rename했다. rename(메타데이터)이 데이터보다 먼저 커밋되었다.
- **대처**: 위 네 단계에서 2번(`fsync(tmp)`)을 넣는다.

### 4. 요청마다 fsync → 지연과 처리량 급락

- **현상**: 내구성을 켜자 쓰기 API p99가 몇 ms에서 수십 ms로 오르고 처리량이 떨어진다.
- **보이는 형태**: `iostat`의 `w_await` 상승, 스레드 덤프에 `FileChannel.force`·`fsync`에서 대기하는 스레드가 많다.
- **원인**: fsync 한 번은 장치 캐시 flush까지 기다린다(로컬 재현에서 약 5 ms, 장치마다 다르다). 요청마다 부르면 그 비용을 요청 수만큼 낸다.
- **대처**: **group commit**으로 여러 요청의 fsync를 한 번에 묶는다. 미리 0을 써 둔 덮어쓰기 로그는 `fdatasync`를 쓴다(`fallocate`만 한 파일은 첫 쓰기 때 이득이 없다). 전원 손실 보호(PLP)가 있는 장치를 쓴다. "fsync를 끈다"는 해법이 아니라 내구성 포기다.

### 5. 내구성 설정을 꺼 둔 채 운영

- **현상**: 크래시·정전 뒤 커밋했다고 응답한 트랜잭션이 사라졌다.
- **보이는 형태**: 복구 뒤 마지막 몇 초~몇 분의 데이터가 없다. 에러는 없다.
- **원인**: PostgreSQL `fsync=off`, Redis의 느슨한 `appendfsync` 설정, 파일 시스템 `nobarrier`, 장치 캐시 flush를 무시하는 구성 등. 페이지 캐시·장치 캐시에 있던 데이터가 사라졌다. 설정별 유실 창은 각 제품 문서로 확인한다.
- **대처**: 각 설정이 약속하는 유실 창을 문서화하고, 그 창이 요구 사항(RPO)에 맞는지 확인한다. 장치가 flush를 정직하게 처리하는지 전원 차단 테스트로 본다.

## 핵심 문장

- `write()` 성공은 페이지 캐시 도착이다. 디스크 도착은 `fsync`·`fdatasync`가 성공해야 말할 수 있다.
- `fsync`는 데이터·메타데이터를 내보내고 장치 쓰기 캐시까지 비운다. `fdatasync`는 읽기에 필요 없는 메타데이터를 건너뛴다.
- 이름은 디렉터리의 데이터다. 새 파일·rename을 남기려면 디렉터리도 fsync한다.
- 원자적 교체는 "임시 파일 write → fsync → rename → 디렉터리 fsync" 네 단계다.
- fsync가 `EIO`를 내면 데이터는 이미 버려졌을 수 있다. 재시도 성공을 믿지 말고 로그·복제본에서 복구한다.
- 내구성의 비용은 fsync 지연이다. 끄지 말고 group commit으로 나눈다.

## 관련 주제·근거

- 선행: [23-crash-consistency-and-journaling](../23-crash-consistency-and-journaling/2-summary.md) — 저널·지연 할당·0바이트 파일
- 연결
  - [21-files-and-descriptors](../21-files-and-descriptors/2-summary.md) — close ≠ 디스크, OFD
  - [22-file-system-implementation](../22-file-system-implementation/2-summary.md) — 디렉터리 = 이름 → inode 표
  - [33-data-integrity-checksums](../33-data-integrity-checksums/2-summary.md) — lost write·조용한 손상
  - [database/README](../../database/README.md) — `19-wal-and-logging`(WAL·group commit). 미작성
  - [14-mmap-and-page-cache](../14-mmap-and-page-cache/2-summary.md) — 페이지 캐시·dirty writeback
  - [38-os-incidents](../38-os-incidents/2-summary.md)(fsyncgate 2018)
- Linux man-pages
  - fsync(2) — 장치 캐시 flush, 디렉터리 fsync 필요, `EIO`와 4.13 이후 보고 범위 <https://man7.org/linux/man-pages/man2/fsync.2.html>
  - rename(2) — 원자적 교체(다른 프로세스 관점) <https://man7.org/linux/man-pages/man2/rename.2.html>
  - open(2) `O_SYNC`·`O_DSYNC`·`O_DIRECT`, sync_file_range(2) Warning, close(2) NOTES
- 커널
  - Documentation/block/writeback_cache_control.rst — 휘발성 쓰기 캐시, `REQ_PREFLUSH`, FUA <https://docs.kernel.org/block/writeback_cache_control.html>
  - Documentation/ABI/stable/sysfs-block — `queue/write_cache`
  - `fs/ext4/extents.c` — unwritten→written 변환 뒤 `ext4_update_inode_fsync_trans(handle, inode, 1)`, unwritten 할당 때는 `datasync=0`. `fs/ext4/ext4_jbd2.h` — datasync일 때만 `i_datasync_tid` 갱신 <https://github.com/torvalds/linux/blob/master/fs/ext4/extents.c>
  - lib/errseq.c, commit b4678df184b3 "errseq: Always report a writeback error once"(v4.17 포함) <https://github.com/torvalds/linux/commit/b4678df184b3>
- LWN, Jonathan Corbet, "PostgreSQL's fsync() surprise"(2018-04-18) <https://lwn.net/Articles/752063/>
- 논문
  - Pillai 외, "All File Systems Are Not Created Equal: On the Complexity of Crafting Crash-Consistent Applications", OSDI 2014 — 지속성 속성, 11개 앱에서 취약점 60개 <https://www.usenix.org/conference/osdi14/technical-sessions/presentation/pillai>
  - Rebello 외, "Can Applications Recover from fsync Failures?", USENIX ATC 2020 — ext4·XFS·Btrfs가 실패 페이지를 clean으로 표시 <https://www.usenix.org/conference/atc20/presentation/rebello>
- PostgreSQL
  - 문서 `data_sync_retry`(기본 off → PANIC) <https://www.postgresql.org/docs/current/runtime-config-error-handling.html>
  - wiki "Fsync Errors" <https://wiki.postgresql.org/wiki/Fsync_Errors>
- 교재: OSTEP 39장 39.7 fsync·디렉터리 fsync, 39.8 rename 원자적 교체 <https://pages.cs.wisc.edu/~remzi/OSTEP/file-intro.pdf>
- 런타임 소스: OpenJDK `src/java.base/unix/native/libnio/ch/UnixFileDispatcherImpl.c`(`force0`), libuv `src/unix/fs.c`(`uv__fs_fsync`)
- 로컬 재현(리눅스 7.0, ext4 on NVMe): write vs fsync 시간·`Dirty` 변화, 작은 write 200번 vs write+fdatasync 200번, `fallocate`만 한 파일 vs 0을 써 둔 파일의 덮어쓰기+fdatasync, `fsync(dirfd)`, Java 21·Node 18의 원자적 교체를 strace로 확인(`fsync → rename → fsync(dir)`)
