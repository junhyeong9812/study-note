# os/37-os-symptom-index — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. 증상 이름만으로 원인을 적으면 안 되는 이유

증상은 아래층 사건이 위층 이름으로 **번역**된 것이다. 번역하면서 정보가 줄어든다.\
그래서 한 이름에 원인 후보가 여럿이다.
- `exit 137`은 "SIGKILL로 죽었다"까지만 말한다. OOM killer, 유예 후 강제 종료, 사람의 `kill -9`가 모두 137이다.
- `EAGAIN`은 호출에 따라 "지금 데이터 없음"(논블로킹 I/O)도, "프로세스·스레드 한도"(`fork`)도 된다.

함께 확보할 것:
- **원문**: 예외 타입·메시지 끝의 strerror 문자열, errno 이름과 **어느 호출**이었나, 종료 코드와 시그널을 따로, 커널 로그 줄.
- **모양**: 즉시인가·서서히인가·주기적인가, 한 코어인가·전체인가, CPU 100%인가·0%인가.

### 2. 128+N 규칙

- 커널의 wait 상태는 "정상 종료 + 코드(0~255)" 또는 "시그널로 죽음 + 시그널 번호"를 **따로** 담는다(`WIFEXITED`·`WEXITSTATUS`, `WIFSIGNALED`·`WTERMSIG`, wait(2)).
- 셸(bash)은 시그널 N으로 죽은 명령을 **128 + N**으로 보여 준다(bash(1)). 커널 상태에는 "128+"가 없다. 셸의 관례다.

| 코드 | 시그널 | 셸 메시지(`LC_ALL=C`) |
|---|---|---|
| 132 | SIGILL(4) | `Illegal instruction` |
| 134 | SIGABRT(6) | `Aborted` |
| 135 | SIGBUS(7) | `Bus error` |
| 137 | SIGKILL(9) | `Killed` |
| 139 | SIGSEGV(11) | `Segmentation fault` |
| 141 | SIGPIPE(13) | (출력 없음) |
| 143 | SIGTERM(15) | `Terminated` |

- 이 노트 작성 환경(bash 5.2)에서 `bash -c 'kill -<SIG> $$'`로 확인했다.

### 3. 같은 143, 다른 wait 상태

- JVM: SIGTERM을 받으면 셧다운 훅을 돌리고 **스스로** `exit(128 + 15)`를 한다(OpenJDK `Terminator.java`). wait 상태는 `WIFEXITED`, 코드 143이다. bash는 `Exit 143`으로 적는다(작성 환경 JDK 21 재현).
- 핸들러 없는 C 프로그램: 시그널로 **죽는다**. wait 상태는 `WIFSIGNALED`, `WTERMSIG` = 15다. 셸이 128 + 15 = 143으로 바꿔 보여 준다(`Terminated`).
- Node의 자식 프로세스: `'exit'` 이벤트가 `(code, signal)`을 따로 준다. SIGKILL이면 `(null, 'SIGKILL')`이다. 숫자 137로 오지 않는다(작성 환경 Node 18 재현).
- Java의 `Process.waitFor()`는 시그널 종료를 `0x80 + 시그널`로 돌려준다(OpenJDK `WTERMSIG_RETURN`). SIGKILL이면 137이다.

### 4. 137의 발신자 가르기

| 후보 | 확인 |
|---|---|
| cgroup(또는 노드 전체) OOM killer | `kubectl describe pod`의 `Reason: OOMKilled`, cgroup `memory.events`의 `oom_kill` 증가, 커널 로그 `Memory cgroup out of memory: Killed process ...`(13·28번) |
| 유예 시간 뒤 강제 종료 | 종료에 늘 유예 시간(쿠버네티스 기본 30초, Docker 기본 10초)이 꽉 걸림. SIGTERM이 앱에 안 닿는 원인(셸 형식 CMD, PID 1에 핸들러 없음)을 확인(06·28번) |
| 사람·스크립트의 `kill -9` | 위 둘의 흔적이 없음. 운영 기록·감사 로그 |

- 앱 로그가 중간에 끊긴 이유: SIGKILL은 잡을 수 없어 앱이 로그를 남길 기회가 없다. **앱이 스스로 크래시한 것이 아니다.**

### 5. `EAGAIN`의 세 얼굴

- `read`(논블로킹 fd): 지금 읽을 데이터가 없다. 정상 흐름이다(25번).
- `fork`·`pthread_create`: 프로세스·스레드 한도(`RLIMIT_NPROC`, `threads-max`, `pid_max`, cgroup `pids.max`)에 닿았다(fork(2), pthread_create(3), 04·07번).
- `sem_trywait`: 지금 permit이 없다(18번).

논블로킹 `read`의 `EAGAIN`을 잘못 다루는 방식:
- **바로 재호출(무시)**: 준비 알림을 기다리지 않고 루프를 돈다 → 트래픽이 없는데 한 코어 100%, `strace`에 `EAGAIN`이 끝없이 찍힌다(25번 시나리오 1).
- **에러로 처리**: `-1`이면 모두 에러로 보고 `close()` → 부하가 조금 오르면 멀쩡한 연결이 끊긴다(25번 시나리오 2).
- 올바른 처리: epoll·Selector에 관심을 등록하고 잠든다.

### 6. `df`는 여유인데 `ENOSPC`

| 원인 | 확인 |
|---|---|
| inode 고갈 | `df -i`의 `IUse%` 100%, `du --inodes`로 범인 디렉터리 |
| 한 디렉터리의 htree 한도(`large_dir` 없음) | 커널 로그 `Directory (ino: N) index full, reach max htree level :2` |
| 디렉터리 크기 제한(`max_dir_size_kb` 마운트 옵션) | `findmnt -o OPTIONS <마운트>`에 `max_dir_size_kb`, 문제 디렉터리 자체의 크기(`ls -ld`) |

- 모두 22번 노트가 다루는 원인이다(`max_dir_size_kb`는 fs/ext4/namei.c `ext4_append`의 `-ENOSPC`).
- 예약 블록은 여기에 들지 않는다. 일반 사용자만 막히는 경우지만, 그때는 일반 사용자 기준 가용 공간이 0이라 `df`의 Use%가 100% 근처다(22번 시나리오 3). "`df` 여유 40%"와 맞지 않는다.
- 반대로 `df`가 가득인데 `du` 합계가 작다면: 지운 파일을 어떤 프로세스가 아직 열고 있다. `rm`은 이름만 지웠고 inode·블록은 살아 있다. `lsof -nP +L1`로 `(deleted)` 파일을 찾고, 그 프로세스가 파일을 다시 열게 하거나 재시작한다(21번).

### 7. load 30, CPU 한가

- 의심: **D 상태 누적**이다. 리눅스 load는 R과 D의 수다(proc_loadavg(5)). 느린 디스크·끊긴 NFS·major fault 폭주가 D를 쌓는다.
- 확인
  - `vmstat 1 5`의 `r`(작음)과 `b`, `wa`.
  - `ps -eo stat,wchan:30,comm | awk '$1 ~ /^D/'`로 D와 잠든 커널 함수.
  - `iostat -x`의 `await`, PSI io, 커널 로그의 `blocked for more than 120 seconds`.
  - `vmstat`의 `b`는 I/O 대기 D만 센다. `b`가 0이어도 D가 없다는 뜻이 아니다(04·31번).
- 교착으로 멈춘 서비스: 스레드들이 futex 대기 `S` 상태다. `S`는 load에 들어가지 않는다. 그래서 load는 **낮게** 보이고 CPU도 0%다(19번). "load가 낮으니 멀쩡하다"는 성립하지 않는다.

### 8. 상태와 load, 좀비

- load에 들어가는 것: **R과 D**. S·T·Z는 들어가지 않는다(I 상태 커널 스레드도 제외).
- 좀비에 `kill -9`가 소용없는 이유: 좀비는 이미 끝난 프로세스다. 남은 것은 PID·종료 상태 같은 기록뿐이고, 부모가 `wait`로 회수해야 사라진다.
- 대처
  - `ps -o ppid`로 좀비의 **부모**를 찾는다.
  - 부모 코드를 고친다: `SIGCHLD` 핸들러나 메인 루프에서 `while (waitpid(-1, &st, WNOHANG) > 0);`(06번: SIGCHLD는 여러 번 와도 한 번만 pending될 수 있다).
  - 급하면 부모를 끝낸다. 좀비는 init·subreaper에 입양되어 회수된다.
  - 컨테이너 PID 1이 앱이면 `docker run --init`·tini를 둔다(05·28번).

### 9. `unable to create native thread`

- 출처: `pthread_create`의 `EAGAIN`이다(pthread_create(3), 07번).
- 힙과 무관한 이유: 막힌 것은 **스레드 개수 한도**나 스레드 스택 같은 native 자원이다. `-Xmx`는 Java 힙만 정한다. "OutOfMemoryError"라는 클래스 이름이 오해를 부른다.
- 스택 메모리를 못 받은 경우도 glibc는 `ENOMEM`을 `EAGAIN`으로 바꿔 돌려준다(glibc `nptl/pthread_create.c`, 13번). 그래서 errno만으로는 개수 한도와 메모리 부족을 가를 수 없다.
- 확인할 한도
  - `RLIMIT_NPROC`(`ulimit -u`) — 실사용자 ID 단위라 같은 사용자의 다른 프로세스 스레드까지 합산된다.
  - `/proc/sys/kernel/threads-max`
  - `/proc/sys/kernel/pid_max`
  - cgroup `pids.max`(컨테이너)
- 그다음 `jstack`으로 스레드 수·이름을 세어 누수 풀을 찾는다. 좀비가 PID를 쥐고 있지 않은지도 본다.

### 10. 조용한 실패 넷

| 증상 | leaf | 첫 확인 |
|---|---|---|
| 카운터 합계가 로그보다 적음, 재고 음수 | [15](../15-race-conditions/2-summary.md) · [20](../20-concurrency-bugs/2-summary.md) | 동시성 테스트(많은 스레드·동시 출발), TSan |
| 재부팅 뒤 설정 파일이 0바이트 | [23](../23-crash-consistency-and-journaling/2-summary.md) · [24](../24-fsync-and-durability/2-summary.md) | `strace -e trace=openat,write,fsync,rename`으로 쓰기 순서 |
| 스토리지 장애 뒤 며칠 지나 데이터가 없음, 당시 fsync 실패 1회 뒤 재시도 성공 | [24](../24-fsync-and-durability/2-summary.md) | 당시 커널 로그의 블록 장치 오류 |
| 해제 후 사용인데 안 죽음, 한참 뒤 엉뚱한 곳에서 크래시 | [09](../09-address-space/2-summary.md) · [11](../11-heap-allocation/2-summary.md) | ASan(`-fsanitize=address`) |

- 이 밖에: 복제·백업까지 같은 비트 부패(33번), RAID5 write hole(32번), 짧은 쓰기 무시(02·34번).
