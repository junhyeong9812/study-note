# os/06-signals — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. 생성 → 대기 → 전달

```text
  생성: kill(2), Ctrl+C, CPU 예외, 파이프 끊김
    |
    v
  대기(pending): 대상의 pending 비트를 켠다. 막혀 있으면 풀릴 때까지 여기 머문다
    |
    v
  전달: 커널 모드 -> 유저 모드로 돌아가는 순간, pending이면서 막히지 않은 시그널 처리
        (기본 동작 / 무시 / 핸들러)
```

- 확인 시점은 커널에서 유저로 돌아갈 때마다다. 시스템 콜 복귀, 스레드가 CPU에 다시 올라갈 때가 그 예다(signal(7) "Execution of signal handlers").
- 그래서 핸들러·기본 동작은 "보내는 즉시"가 아니라 대상이 다음에 유저 모드로 돌아갈 때 실행된다.
- 예외적으로 생성 시점에 일어나는 효과도 있다. SIGCONT의 정지 해제, 막히지 않은 무시 시그널 버리기가 그렇다(`kernel/signal.c` `prepare_signal()`·`sig_ignored()`).

### 2. 세 번 보낸 SIGUSR1

- 핸들러는 **1번** 돈다. 표준 시그널은 막혀 있는 동안 여러 번 와도 한 번만 pending으로 표시된다(signal(7) "Standard signals do not queue").
- 실시간 시그널이면 **3번** 돈다. 실시간 시그널은 인스턴스마다 큐에 쌓인다. 단 세 인스턴스가 모두 큐에 들어갔을 때다 — 큐 한도에 걸리면 `sigqueue`는 `EAGAIN`, `kill`은 정보를 잃을 수 있다(`__send_signal_locked()`).
- 차이의 출처: 커널의 `struct sigpending`은 `sigset_t signal`(비트마스크)과 `list`(siginfo 큐)를 가진다(include/linux/signal_types.h). 리스트가 있어도 커널은 같은 표준 시그널이 이미 pending이면 새로 넣지 않는다(`kernel/signal.c` `legacy_queue()`). 실시간 시그널은 올 때마다 리스트에 하나씩 넣는다.
- 로컬 재현(예시, 리눅스 7.0): 세 번 보낸 뒤 `ShdPnd: …0200`(비트 9 = SIGUSR1), 풀고 나서 "handler ran 1 time(s)".

### 3. 블록 vs 무시

- **블록**: 전달을 **미룬다**. 시그널은 pending으로 남고, 막기를 풀면 전달된다. 스레드별 마스크로 정한다.
- **무시**: **버린다**. 막혀 있지 않으면 리눅스는 생성 시점에 바로 버린다(`sig_ignored()`). 나중에 되살릴 수 없다. 프로세스 단위 처리 방식이다.
- SIGKILL(9)과 SIGSTOP(19)은 **잡기·막기·무시 모두 불가**다(signal(7)). 그래서 SIGKILL을 받으면 정리 코드(셧다운 훅 등)가 돌 기회가 없다.

### 4. 핸들러 호출과 복귀

1. 커널이 대기 집합에서 그 시그널을 지운다.
2. 현재 PC·레지스터·시그널 마스크를 유저 스택의 시그널 프레임에 저장한다(`SA_ONSTACK`이면 대체 스택).
3. `sa_mask`의 시그널과 그 시그널 자신을 마스크에 더한다(`SA_NODEFER` 제외).
4. PC를 핸들러 첫 명령으로, 복귀 주소를 **시그널 트램펄린**으로 설정하고 유저 모드로 돌아간다.
5. 핸들러가 return하면 트램펄린이 `sigreturn(2)`을 부른다.
6. 커널이 프레임에서 레지스터·마스크를 복원한다. 끊겼던 명령부터 다시 실행된다.

(signal(7) 단계 (1)~(5))

### 5. 핸들러 안 `malloc`·`printf`

```text
  메인:   malloc() -> arena 락 획득 -> _int_malloc 실행 중 ... [SIGALRM]
  핸들러: malloc() -> 같은 arena 락 요청 -> 대기
          락 주인 = 메인 흐름 = 핸들러가 끝나야 재개됨  -> 영원히 대기
```

- 시그널은 메인 흐름의 아무 명령 사이에나 끼어든다. 메인이 락을 잡았거나 자료구조를 반쯤 고친 상태일 수 있다.
- `malloc`은 데드락, `printf`는 stdio 버퍼 손상 위험이 있다. 둘 다 async-signal-safe 목록에 없다(signal-safety(7)).
- 로컬 재현(예시, 리눅스 7.0 · glibc 2.39): 스레드가 있던 프로세스에서 즉시 멈췄다. 백트레이스는 `futex_wait(main_arena)` ← `malloc` ← 핸들러 ← `<signal handler called>` ← `_int_malloc` ← `main`.
- 단일 스레드에서 안 멈춘 것은 **안전의 증거가 아니다**. glibc 2.39는 단일 스레드면 락 없이 `_int_malloc`을 부른다(`malloc.c`의 `SINGLE_THREAD_P` 분기). 락이 없으니 데드락 대신 힙 자료구조를 이중으로 고치는 손상 위험이 남는다.
- 해법: 핸들러는 `volatile sig_atomic_t` 플래그 대입이나 self-pipe `write`만 한다.

### 6. 128+N

| 종료 코드 | N | 시그널 |
|---|---|---|
| 137 | 9 | SIGKILL |
| 143 | 15 | SIGTERM |
| 139 | 11 | SIGSEGV |
| 141 | 13 | SIGPIPE |

- 커널의 `wait` 상태는 "시그널로 종료 + 번호"를 따로 담는다(`WIFSIGNALED`, `WTERMSIG`). 128+N은 **bash·컨테이너 런타임의 관례**다(bash(1) "128+N"). POSIX는 "128보다 큰 값"만 요구한다(XCU §2.8.2).
- 그래서 숫자만으로 시그널 사망을 확정하지 못한다. `exit(137)`도 137이다.
- 예외: JDK는 기본 설정(`-Xrs` 없음)에서 SIGTERM을 **잡아서** 셧다운 훅을 돌린 뒤 스스로 `exit(128+15)`한다(OpenJDK `Terminator.java`). 이때 143은 시그널 사망이 아니라 정상 `exit(143)`이다.

### 7. 30초 뒤 137

- 흐름: kubelet이 컨테이너 런타임을 통해 SIGTERM(또는 이미지 `STOPSIGNAL`)을 보냄 → 유예(기본 30초) → 남은 프로세스에 SIGKILL → 137(k8s Pod Lifecycle 문서).
- 원인 후보
  1. **앱이 PID 1이 아니다.** `CMD` 셸 형식이라 `sh -c`가 PID 1이고, 셸이 SIGTERM을 자식에게 전하지 않을 수 있다. 확인: 컨테이너 안에서 `ps -o pid,cmd` 또는 `cat /proc/1/cmdline`.
  2. **앱이 PID 1인데 핸들러가 없다.** PID 네임스페이스의 init은 다른 프로세스가 보낸 시그널 중 핸들러를 설치한 것만 받는다. 기본 동작(종료)도 일어나지 않는다(pid_namespaces(7)). 조상 네임스페이스의 SIGKILL·SIGSTOP은 예외다. 확인: `grep SigCgt /proc/1/status`에서 비트 14(SIGTERM)가 켜져 있는지.
  - 그 밖: 핸들러는 있지만 정리가 30초를 넘는다(드레이닝 대기, 멈춘 스레드).
- 대처: exec 형식 CMD, `tini` 같은 init, 핸들러에서 정리 후 종료, 필요하면 `terminationGracePeriodSeconds` 조정.

### 8. 141로 조용히 사라지는 C 도구

- 원인: 읽는 쪽이 닫힌 파이프에 `write`했거나, 소켓 쓰기가 `EPIPE` 조건(연결이 이미 끊김)에 걸렸다. 상대가 막 닫은 직후의 첫 `write`는 성공할 수 있다. 커널이 SIGPIPE를 보내고, 기본 동작이 종료라 로그가 없다(pipe(7), send(2)).
- 대처
  - 프로세스 전체: `signal(SIGPIPE, SIG_IGN)` 또는 `sigaction`으로 무시. 이후 `write`는 `-1/EPIPE`를 돌려주니 에러로 처리한다.
  - 호출 단위: `send(..., MSG_NOSIGNAL)`. 다른 스레드·라이브러리의 동작을 바꾸지 않는다(send(2)).
- Java: HotSpot이 SIGPIPE에 아무것도 안 하는 핸들러를 걸어 두므로(무시와 같은 효과) 프로세스는 살고 `IOException: Broken pipe`가 난다(`signals_posix.cpp`).
- Node: 시작 시 SIGPIPE를 `SIG_IGN`으로 두므로 쓰기가 `EPIPE`로 실패하면 에러 이벤트가 된다(`src/node.cc`). 상황에 따라 `ECONNRESET`으로 보일 수도 있다.

### 9. fork·exec 상속

| 항목 | fork 후 자식 | execve 후 |
|---|---|---|
| 처리 방식 | 복사 | 핸들러 → 기본 동작, 무시 → 유지 |
| 마스크 | 복사 | 유지 |
| 대기 집합 | 비움 | 유지 |

(signal(7))

- 핸들러는 함수 주소다. `execve`로 새 프로그램이 올라오면 그 주소에 그 함수가 없으니 되돌린다.
- 무시(`SIG_IGN`)는 주소가 아니라 표시라 새 프로그램에서도 의미가 있어 유지된다. 그래서 부모가 무시하던 시그널을 자식 프로그램도 무시한 채 시작할 수 있다.

### 10. SIGCHLD 한 번에 `waitpid` 한 번

- 자식 다섯이 거의 동시에 끝나면 SIGCHLD는 한 번(또는 몇 번)만 pending된다. 표준 시그널은 쌓이지 않는다.
- 핸들러가 `waitpid`를 한 번만 부르면 한 자식만 회수되고 나머지는 **좀비**로 남는다.
- 고침: `while (waitpid(-1, &st, WNOHANG) > 0) ;`로 끝난 자식을 전부 회수한다. `waitpid`는 async-signal-safe다(signal-safety(7) 목록).
- 핸들러 안에서 `errno`를 바꾸므로 들어올 때 저장하고 나갈 때 복원한다.
