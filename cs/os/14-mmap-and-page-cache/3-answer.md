# os/14-mmap-and-page-cache — 정답

## 정답

### 1. read vs mmap 경로

```text
  read                                   mmap + 포인터 읽기
  buf (사용자) <-- 복사 -- [페이지 캐시]     p (사용자) ==PTE==> [페이지 캐시]
                              ^                                    ^
                         없으면 디스크                          없으면 페이지 폴트 → 디스크
```

- `read`: 시스템 콜마다 페이지 캐시 → 사용자 버퍼로 **복사**한다.
- `mmap`: 페이지 테이블이 캐시 페이지를 직접 가리킨다. 복사가 없다. 대신 처음 접근 때 페이지 폴트가 난다.
- 캐시에 없으면 둘 다 디스크에서 읽어 캐시를 채운다.

### 2. SHARED vs PRIVATE 쓰기

- `MAP_SHARED`: 캐시 페이지 자체를 고친다. 같은 파일의 다른 매핑·`read`에 보이고, 나중에 원본 파일에 기록된다(mmap(2)).
- `MAP_PRIVATE`: 처음 쓰는 순간 그 페이지를 복사(copy-on-write)하고 사본만 고친다. 다른 프로세스와 원본 파일에는 안 보인다.
- 수정된 private 사본은 원본 파일이 없는 **익명 페이지**다. 메모리가 모자라면 스왑으로 간다(12번). 스왑이 없으면 내보낼 수 없다.

### 3. 캐시 조회 자료구조

- 파일(inode)마다 `address_space`가 있고, 그 `i_pages`가 **XArray**(기수 트리)다(include/linux/fs.h). 키는 파일 안 페이지 번호(1MiB / 4KiB = 256)다.
- 잘 맞는 이유
  - 키가 작은 정수(페이지 번호)라 비트를 잘라 내려가는 기수 트리가 자연스럽다.
  - 파일은 일부만 캐시되는 경우가 많다(희소). 빈 구간은 노드가 없어 메모리를 안 쓴다.
  - 순서가 있어 "이 범위의 dirty 페이지 전부" 같은 범위 순회가 쉽다(fsync, truncate에 필요). 해시는 범위 순회가 어렵다.

### 4. write 직후 전원 장애

- `write` 성공은 페이지 캐시에 쓰고 dirty로 표시했다는 뜻이다. 기록 전이면 그 데이터는 **사라진다**.
- dirty가 디스크로 가는 계기(작성 환경 기본값, kernel.org sysctl/vm 의미)
  - 시간: flusher가 `dirty_writeback_centisecs`(500 = 5초)마다 깨서 `dirty_expire_centisecs`(3000 = 30초)보다 오래된 dirty를 쓴다.
  - 양: dirty가 `dirty_background_ratio`(10%)를 넘으면 백그라운드 기록 시작. 더 쌓여 `dirty_ratio`(20%) 쪽으로 가면 쓰는 프로세스가 막힌다. 문서는 "직접 기록을 시작한다"고 적고, 현재 구현은 두 값의 중간부터 쓰는 프로세스를 재워 속도를 맞춘다(mm/page-writeback.c `balance_dirty_pages`).
  - 명시적: `fsync`/`fdatasync`/`msync(MS_SYNC)` — 기록이 끝날 때까지 기다린다(24번).

### 5. 절단된 매핑 접근

- `p[200]`: 파일 끝(100바이트)이 걸친 **첫 페이지** 안이다. 끝 뒤의 바이트는 **0**으로 보인다(mmap(2) NOTES).
- `p[4096]`: 파일 끝을 **완전히 넘은 페이지**다. **SIGBUS**(mmap(2)).
- 종료 코드 128 + 7 = **135**. 로컬 재현에서 `p[200]=0`, 이어서 "버스 오류", exit 135였다(예시, 리눅스 7.0).

### 6. free 읽는 법

- 판단은 **`available`**로 한다. 스왑 없이 새 프로그램에 줄 수 있다고 추정한 양이고, 버릴 수 있는 캐시를 포함한다(`MemAvailable`, 3.14+).
- `buff/cache`: 버퍼 + 페이지 캐시 + 회수 가능한 slab이다(free(1)). 메모리가 필요하면 커널이 회수한다.
- `free` 칸이 작은 것은 정상이다. 빈 메모리를 캐시로 쓰고 있을 뿐이다.
- `used`의 정의는 도구 버전마다 다르다. procps-ng 4.0.1부터 `total - available`이다(procps NEWS). 대시보드가 `MemTotal - MemFree`를 쓰면 캐시까지 "사용"으로 보인다.

### 7. FADV_DONTNEED와 readahead

- (a) fsync 뒤: 페이지가 모두 clean이다. 4096 → **0**으로 전부 버려졌다.
- (b) fsync 없이: dirty 페이지는 바로 버릴 수 없다. 로컬 재현에서 4096 → **2048**만 빠졌다. 기록이 끝난 일부만 버려진 것이다(예시, 리눅스 7.0).
- 앞 4MiB(1024페이지)를 순차로 읽자 **1056**페이지가 캐시에 있었다. 커널이 순차 읽기를 감지해 요청보다 앞을 미리 읽었다(readahead, 여기서는 32페이지 더).
- (모두 로컬 재현, 16MiB 파일)

### 8. write가 멈추는 원인

- 볼 것: `/proc/meminfo`의 `Dirty`와 `Writeback`. 업로드 중 `Dirty`가 크게 쌓여 있으면 원인 후보다. `vmstat`의 `bo`·`wa`도 함께 본다.
- 원인: 쓰는 속도가 디스크 속도보다 빨라 dirty가 한도 근처까지 쌓였다. 그러면 `balance_dirty_pages`가 쓰는 프로세스를 재워 속도를 디스크에 맞추느라 `write`가 막힌다. `(background + dirty_ratio)/2`부터 시작하고 `dirty_ratio`에 가까울수록 길어진다.
- 조정: `vm.dirty_background_ratio`(또는 `dirty_background_bytes`)를 낮춰 더 일찍 조금씩 쓰게 한다. 큰 파일은 중간중간 `fdatasync`·`sync_file_range`로 나눠 기록한다.

### 9. Kafka와 페이지 캐시

- 장점
  - 자기 캐시(JVM 힙)를 안 두니 GC 부담이 없고, 같은 데이터가 힙과 캐시에 두 번 있지 않다.
  - 프로듀서가 쓴 바이트가 페이지 캐시에 있고 컨슈머가 바로 뒤따라오면, 디스크를 거치지 않고 캐시에서 읽힌다. 평문 리스너에서는 sendfile로 소켓까지 보낸다. SSL이 켜져 있으면 sendfile을 쓰지 않고 사용자 공간으로 복사해 암호화한다(Kafka 문서 Design "Efficiency").
  - 브로커 프로세스를 재시작해도 캐시는 커널에 남아 따뜻하다(Kafka 문서 Design "Persistence").
- 대가
  - `write`는 dirty 페이지일 뿐이라 전원 장애 때 유실될 수 있다. Kafka는 fsync 대신 복제로 막는다.
  - 뒤처진 컨슈머의 데이터는 캐시에서 밀려나 있어 실제 디스크 읽기가 생긴다. 이것이 다른 컨슈머의 캐시까지 밀어낼 수 있다(12번 스캔 오염).
- ([systems/kafka-why-fast](../../systems/kafka-why-fast/2-summary.md) ②)

### 10. 매핑 파일의 교체

- 제자리 truncate를 하지 않는다. 새 파일에 다 쓴 뒤 `rename`으로 이름을 바꾼다. 이미 매핑한 프로세스는 옛 inode를 계속 안전하게 본다.
- 크기가 늘어날 파일은 `fallocate`로 미리 크기를 확정하고, 매핑 범위를 그 안으로 제한한다.
- 자바 `MappedByteBuffer`
  - 매핑은 버퍼가 GC될 때까지 유효하다(Java SE 문서). 채널을 닫아도 매핑과 파일 참조가 남는다.
  - 잘린 파일에 접근하면 HotSpot 구현에서는 SIGBUS가 `InternalError: a fault occurred in an unsafe memory access operation`으로 바뀔 수 있다(OpenJDK `handshake.cpp`).
  - 디스크 확정은 `force()`로 한다(msync에 해당).
