# os/24-fsync-and-durability — 정답

## 정답

### 1. 쓰기의 층

```text
  앱 버퍼  --flush()-->  페이지 캐시  --writeback / fsync-->  장치 쓰기 캐시  --flush·FUA-->  매체
```

- `flush()`·`fflush()`: 앱 버퍼 → 커널. 아직 페이지 캐시다.
- `write()` 성공: 페이지 캐시 도착(dirty). 백그라운드 writeback이 나중에 내보낸다.
- `fsync()` 성공: 데이터·메타데이터를 장치로 보내고 장치 캐시까지 비운 뒤 반환한다(fsync(2)). 여기서 비로소 "디스크에 있다".

### 2. fsync vs fdatasync

- `fsync`: 데이터 + 모든 수정된 메타데이터(mtime 등).
- `fdatasync`: 데이터 + **다음 읽기에 필요한** 메타데이터만. `st_mtime`·`st_atime`은 건너뛴다(fsync(2)).
- append로 **크기**가 늘면 크기는 읽기에 필요한 메타데이터라서 `fdatasync`도 내보낸다. 이득이 큰 곳은 미리 0을 써서 할당해 두고 덮어쓰기만 하는 파일이다. `fallocate`만 한 영역은 ext4에서 첫 쓰기 때 unwritten→written 변환을 커밋해야 해서 이득이 없다(`fs/ext4/extents.c`).

### 3. O_DIRECT·sync_file_range

- 보장되지 않는다.
  - `O_DIRECT`는 캐시를 건너뛰려 할 뿐 `O_SYNC`의 보장이 없다. 보장하려면 `O_SYNC`를 함께 쓴다(open(2)).
  - `sync_file_range`는 메타데이터를 안 쓰고 장치 캐시도 안 비운다. man이 "extremely dangerous"라고 한다.
- 대신: `fsync`/`fdatasync`, 또는 `O_SYNC`/`O_DSYNC`.

### 4. fsync했는데 파일이 없다

- 파일 **이름**은 부모 디렉터리의 데이터다. `fsync(file)`은 디렉터리 항목까지 디스크에 보낸다고 보장하지 않는다(fsync(2)).
- 부모 디렉터리를 `open(dir, O_RDONLY|O_DIRECTORY)`로 열어 `fsync(dirfd)`한다.

### 5. 원자적 교체 네 단계

```text
  1. tmp 열기·쓰기    2. fsync(tmp), close    3. rename(tmp, cfg)    4. fsync(dir)

  크래시 위치      cfg 내용
  2 전            옛 내용
  2~3 사이        옛 내용
  3~4 사이        옛 또는 새 (섞이지 않음)
  4 뒤            새 내용
```

- rename은 다른 프로세스가 `cfg`가 없는 순간을 보지 않게 교체한다(rename(2)). 크래시에 대해서도 대개 원자적이다(OSTEP 39.8).

### 6. 단계를 빼면

- (a) 임시 파일 fsync 누락: rename이 데이터보다 먼저 커밋될 수 있다. 크래시 뒤 `cfg`가 **0바이트**·일부만 쓰인 파일일 수 있다(23번 지연 할당).
- (b) 디렉터리 fsync 누락: rename 자체가 디스크에 안 갔을 수 있다. 크래시 뒤 **옛 파일이 돌아온다**. 에러는 없다.

### 7. EIO 뒤 재시도 성공

- 안전하지 않다. 버퍼 쓰기 실패 시 많은 파일 시스템이 그 페이지를 **clean으로 표시**하고 데이터를 버린다. 두 번째 fsync는 보낼 더러운 페이지가 없어 성공한다(LWN 752063, Rebello 외 2020).
- 커널이 페이지를 계속 쥐지 않는 이유: 흔한 오류(USB 분리)에서 더러운 페이지가 메모리를 다 먹을 수 있다(Ts'o).
- PostgreSQL은 flush 실패 뒤 상태를 믿을 수 없으므로 **PANIC → WAL로 복구**를 택했다. `data_sync_retry` 기본 off(PostgreSQL 문서).

### 8. 4.13과 4.17

- 4.13: `errseq_t` 도입. writeback 오류를 그 데이터를 썼을 수 있는 **모든 fd**(대부분 로컬 FS에서는 오류 시점에 열려 있던 모든 fd)에 보고한다.
- 그런데 오류 **뒤에 연** fd는 오류를 못 봤다. PostgreSQL checkpointer는 fsync 직전에 파일을 여는 경우가 많아 오류를 놓칠 수 있었다(LWN 752063).
- 4.17(stable 백포트): 아직 어떤 fd에도 보고되지 않은 오류는 그 뒤에 연 fd에도 한 번 보고한다(commit b4678df184b3).

### 9. 요청마다 fdatasync

- 한 스레드가 순서대로 하면 초당 약 200건(1000 ms / 5 ms)이 한계다. 2000건을 받으려면 약 10개가 동시에 fsync를 기다려야 하고, 장치가 그만큼 병렬로 처리하지 못하면 대기열이 쌓여 p99가 급등한다(수치는 로컬 예시, 장치마다 다르다).
- 푸는 법
  - **group commit**: 여러 요청의 쓰기를 모아 fsync 한 번으로 커밋하고, 그 뒤에 모두에게 응답한다.
  - 미리 0을 써 둔 덮어쓰기 로그 + `fdatasync`.
  - 전원 손실 보호(PLP)가 있는 장치.
- fsync를 끄는 것은 해법이 아니라 내구성 포기다.

### 10. Java·Node

- OpenJDK `FileChannel.force(false)` → `fdatasync`, `force(true)` → `fsync`(UnixFileDispatcherImpl.c `force0`).
- Node `fs.writeFileSync`는 기본으로 fsync를 하지 않는다(v21.0.0·v20.10.0부터 `flush: true`면 `fs.fsyncSync()` 호출). 내구성이 필요하면 `fs.fsyncSync(fd)`를 직접 부르고, rename 뒤 디렉터리도 fsync한다. libuv는 리눅스에서 `fsync`, macOS에서 `F_FULLFSYNC`를 쓴다.
