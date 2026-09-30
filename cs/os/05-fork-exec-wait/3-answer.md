# os/05-fork-exec-wait — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. `ls > out.txt`

```text
  셸 (부모)                         자식
  fork() ------------------------> 셸의 복제본
                                   open("out.txt") -> fd 3
                                   dup2(3, 1)   표준 출력 = out.txt
                                   close(3)
                                   execvp("ls")  -> ls로 바뀜 (PID 그대로, fd 1은 유지)
  waitpid(자식) ... 잠듦             ls가 fd 1(= out.txt)에 쓰고 exit(0)
  <------------ 종료 상태 --------
  다음 프롬프트
```

- 리다이렉트는 **fork 뒤, exec 전에 자식이** 한다. exec는 열린 fd를 유지하므로 `ls`는 자기가 파일에 쓴다는 것도 모른 채 fd 1에 쓴다.
- 나눈 이유: 이 "사이"가 있어서 셸이 `ls` 코드를 고치지 않고도 입출력·환경을 바꿔 줄 수 있다(OSTEP 5.4).

### 2. 반환값과 `_exit`

- `fork()`: 부모에게 **자식 PID**, 자식에게 **0**, 실패하면 부모에게 **-1**.
- `execvp()` 다음 줄이 실행됨 = **exec 실패**(파일 없음, 권한 없음 등). 성공하면 돌아오지 않는다.
- `_exit`를 쓰는 이유: `exit`는 stdio 버퍼를 비우고 `atexit` 핸들러를 돈다. 자식의 버퍼는 부모에게서 복사된 것이라, 부모 몫의 출력이 **한 번 더** 나가거나 부모의 정리 작업이 두 번 돈다.

### 3. "hello" 몇 번?

- **두 번**이다. 로컬 재현: `hello child` / `hello parent`.
- "hello "에는 줄바꿈이 없어서 fork 시점에 아직 stdio 버퍼에 있다. 출력이 파이프면 stdio는 블록 단위로 버퍼링하므로 더욱 그렇다(터미널이어도 줄바꿈 전이라 버퍼에 남는다).
- fork가 그 **버퍼(메모리)** 까지 복제한다. 부모와 자식이 각자 끝날 때 각자의 버퍼를 비우니 두 번 나온다.
- 대처: fork 전에 `fflush(stdout)`.

### 4. 256MB 프로세스의 fork

- fork 순간 복사되는 것: **페이지 테이블**(과 태스크 구조). private 매핑의 페이지 내용은 복사하지 않고, 양쪽 매핑을 읽기 전용으로 표시한다(copy-on-write). (`MAP_SHARED`는 계속 공유, pin된 익명 페이지는 즉시 복사하는 예외가 있다.)
  - 로컬 재현: fork 자체 7~10ms.
- 자식이 **읽기만**: 페이지 폴트가 거의 없다(로컬 3번). 공유 페이지를 그대로 읽는다.
- 자식이 **쓰기**: 256MB / 4KB = **65536** 페이지마다 쓰기 폴트 → 복사. 로컬 재현 65555번, 189~230ms.

### 5. 물려받는 것 / 안 받는 것

- 물려받는다: 주소 공간 내용(COW), 열린 fd(표 복사), 시그널 처리 방식(핸들러), 작업 디렉터리, 환경 변수, 자원 한도.
- 안 받는다: 대기 중인 시그널(비어서 시작), 메모리 락(`mlock`), 타이머(`alarm`·`setitimer`·`timer_create`), 프로세스에 딸린 `fcntl` 레코드 락(OFD 락·`flock` 락은 물려받는다). 그리고 **다른 스레드**(fork를 부른 스레드 하나만 있다)(fork(2)).
- 같은 fd로 `read`: 두 fd가 같은 "열린 파일 설명"을 가리켜 **오프셋을 공유**한다. 한쪽이 100바이트 읽으면 다른 쪽은 그 뒤부터 읽는다.

### 6. exec 뒤

- 남는 것: PID·PPID, CLOEXEC 없는 열린 fd, 무시·기본으로 둔 시그널 처리, 실 UID·GID, 작업 디렉터리.
- 사라지는 것: 코드·데이터·힙·스택(새 프로그램으로 교체), 메모리 매핑, 다른 스레드, 잡던 시그널의 핸들러(기본 동작으로 초기화), `atexit` 핸들러, CLOEXEC fd.
- 열린 fd는 **기본으로 유지**된다(execve(2)). 닫히게 하려면 `O_CLOEXEC`·`FD_CLOEXEC`.

### 7. SIGTERM으로 죽은 자식

- `waitpid` status: `WIFSIGNALED(st)`가 참, `WTERMSIG(st)` = **15**. `WIFEXITED`는 거짓이다. 로컬 raw status 0xf.
- bash `$?`: **143**(128 + 15). 셸의 관례다(ksh93은 256 + 15 = 271).
- Java `waitFor()`: **143**. OpenJDK가 "0x80 + 시그널"을 돌려준다(`WTERMSIG_RETURN`).
- Node `'exit'`: `code = null`, `signal = 'SIGTERM'`(로컬 재현).
- `exit(256)`: 하위 8비트만 전달돼 **0**으로 보인다. 실패가 성공으로 둔갑한다.

### 8. PID 1 Node와 `<defunct>`

- 원인
  - `sh -c`가 띄운 자손이 `sh`보다 늦게 끝나면 고아가 된다. PID 네임스페이스의 고아는 (중간에 subreaper가 없으면) **PID 1(= Node 앱)** 에 입양된다(pid_namespaces(7)).
  - Node는 자기가 만든 자식은 회수하지만, 입양된 모르는 자식은 `wait`하지 않는다. 끝나면 좀비로 남는다.
  - 쌓이면 `pids.max`에 닿아 `fork`가 `EAGAIN`으로 실패한다(04번).
- 고치는 법
  - PID 1에 최소 init을 둔다: `docker run --init` 또는 `ENTRYPOINT ["/tini", "--", "node", "server.js"]`. tini가 좀비를 회수하고 시그널을 전달한다.
  - 로컬 흉내(subreaper) 재현: 회수 안 하면 좀비 6개, `SIGCHLD`에서 `waitpid(-1, 0, WNOHANG)` 루프를 돌리면 0개.

### 9. 포트를 잡은 헬퍼

- 원인
  - 서버가 listen 소켓을 CLOEXEC 없이 열었다. 헬퍼를 fork+exec할 때 fd가 **복사되고 exec 뒤에도 유지**됐다.
  - 소켓(열린 파일 설명)은 모든 fd가 닫혀야 풀린다. 서버가 죽어도 헬퍼가 소켓을 살려 둔다.
  - 로컬 재현: `sleep`이 fd 3으로 LISTEN을 잡고 있었고, 새 bind는 `Address already in use`. `SOCK_CLOEXEC`로 열자 성공.
- 대처
  - `socket(..., SOCK_STREAM | SOCK_CLOEXEC, 0)`, `open(..., O_CLOEXEC)`, `accept4(..., SOCK_CLOEXEC)`.
  - 자식에서 exec 전에 `close_range(3, ~0U, CLOSE_RANGE_CLOEXEC)`로 일괄 표시.
- 파이프의 경우: 자식이 쓰기 쪽 사본을 쥐고 있으면, 부모가 쓰기 쪽을 닫아도 읽는 쪽이 **EOF를 영원히 못 받는다**(pipe(7): 쓰기 쪽 fd가 모두 닫혀야 EOF). 읽는 프로세스가 끝나지 않고 멈춘다.

### 10. 스레드 많은 서비스의 외부 명령

- `posix_spawn`(또는 그것을 쓰는 런타임 API: Java `ProcessBuilder` — 현재 OpenJDK 리눅스 기본이 `POSIX_SPAWN`)을 쓴다.
- 이유
  1. **락 문제**: fork한 자식에는 스레드가 하나뿐이다. 다른 스레드가 쥐고 있던 락(앱·라이브러리의 mutex 등)이 자식에서 안 풀려, exec 전에 그 락을 쓰는 함수를 부르면 멈춘다(fork(2)). glibc는 malloc·stdio 내부 락만은 fork 때 챙긴다(posix/fork.c).
  2. **비용**: fork는 큰 주소 공간의 페이지 테이블을 복사하고 COW를 준비한다. `posix_spawn`은 glibc에서 `CLONE_VM|CLONE_VFORK`로 부모 메모리를 공유한 채 바로 exec해 이 복사가 없다(로컬 strace `clone3`).
