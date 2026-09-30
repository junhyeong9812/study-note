# os/30-ipc — 주소 공간이 갈라진 프로세스끼리 말을 주고받는 네 가지 길 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

프로세스는 각자 주소 공간을 가진다(09번). A의 변수 주소를 B에 알려 줘도 B에게는 아무 의미가 없다.\
보호를 위해 일부러 갈라 놓은 것이다. 그런데 협력하려면 데이터를 건네야 한다.

```text
   프로세스 A                     프로세스 B
   +-----------+                 +-----------+
   | 0x1000: 42|    직접은 못 봄    | 0x1000: ? |   같은 주소라도 다른 물리 메모리
   +-----------+                 +-----------+
          \                          /
           \---- 커널을 거쳐야 한다 ---/
```

**IPC(프로세스 간 통신)**는 커널이 만들어 주는 "둘 다 닿을 수 있는 자리"다.

쉬운 예: 벽으로 나뉜 두 사무실이다.
- 우편함 구멍(파이프): 한쪽이 넣고 다른 쪽이 꺼낸다. 구멍이 차면 넣는 사람이 기다린다.
- 인터폰(유닉스 소켓): 양쪽이 말하고 듣는다. 서류(파일 디스크립터)도 건넬 수 있다.
- 공용 화이트보드(공유 메모리): 가장 빠르다. 대신 둘이 동시에 쓰면 글씨가 겹친다.
- 번호표 서류함(메시지 큐): 한 장씩, 급한 것부터 꺼낸다.

똑같은 구조다.\
셸의 `ps | grep java`, Java의 `ProcessBuilder`, Node의 `child_process.spawn`, Docker CLI와 `dockerd`(유닉스 소켓), PostgreSQL 백엔드들의 공유 버퍼가 모두 이 네 가지 중 하나다.

## 동작·원리

### 1. 네 가지 길 한눈에

```text
  방식              방향     경계       복사 횟수(데이터 1번 전달)      이름·수명
  파이프 / FIFO     한 방향   바이트 흐름  2번 (A->커널 버퍼->B)         fd / 경로(FIFO). 모두 닫으면 끝
  유닉스 소켓        양방향   흐름·메시지  2번                          경로·추상 이름·socketpair
  공유 메모리        양방향   없음       0번 (설정 후 같은 페이지를 봄)   /dev/shm/이름. shm_unlink까지 남는다
  POSIX 메시지 큐   한 방향*  메시지     2번                          /이름. mq_unlink까지 남는다
  (* 여러 프로세스가 같은 큐를 열어 보내고 받을 수 있다)
```

- 파이프·소켓·메시지 큐는 데이터를 **커널 버퍼로 복사**했다가 다시 **받는 쪽으로 복사**한다. 커널이 중개하니 동기화가 공짜다(버퍼가 비면 읽는 쪽이, 차면 쓰는 쪽이 잔다).
- 공유 메모리는 같은 물리 페이지를 두 프로세스의 주소 공간에 매핑한다. 복사가 없다. 대신 **동기화는 직접** 해야 한다(15·18번).

### 2. 파이프 — 커널 안의 링 버퍼

```text
   pipe(fds)  -> fds[1] (쓰기 끝)                           fds[0] (읽기 끝)
                   |                                          ^
                   v                                          |
   커널 pipe_inode_info:  [슬롯0][슬롯1][슬롯2] ... [슬롯15]   (슬롯 = 페이지 1개를 가리킴)
                             ^tail(읽을 곳)       ^head(쓸 곳)
   기본 용량 = 16 페이지 = 65,536 바이트 (페이지 4 KiB일 때)

   버퍼가 가득 차면 write()가 잠든다  (O_NONBLOCK이면 EAGAIN)
   버퍼가 비면     read()가 잠든다   (O_NONBLOCK이면 EAGAIN)
   단, 쓰기 끝이 모두 닫힌 빈 파이프는 잠들지 않고 read()가 0(EOF)
```

- 리눅스 2.6.11부터 기본 용량은 16페이지, 즉 4 KiB 페이지에서 65,536바이트다. 2.6.35부터 `fcntl(F_GETPIPE_SZ/F_SETPIPE_SZ)`로 보고 바꿀 수 있다. 비특권 사용자의 상한은 `/proc/sys/fs/pipe-max-size`(기본 1 MiB)다(pipe(7)).
- 예외: 비특권 사용자가 가진 파이프 페이지 합계가 `/proc/sys/fs/pipe-user-pages-soft`(4.5+, 기본 16384)에 닿으면, 새 파이프는 최소 크기로 만들어지고 `F_SETPIPE_SZ`로 늘리기도 거부된다(pipe(7)). 최소 크기는 pipe(7)이 1페이지로 적지만 현재 커널 소스는 `PIPE_MIN_DEF_BUFFERS` = 2페이지다(fs/pipe.c `alloc_pipe_info`). 이때는 §3의 교착이 훨씬 작은 출력에서도 난다.
- 커널 구조체는 16칸(`PIPE_DEF_BUFFERS`)짜리 `pipe_buffer` 배열과 head/tail 인덱스를 가진 링이다(include/linux/pipe_fs_i.h).
- 작성 환경에서 논블로킹으로 1바이트씩 쓰자 정확히 65,536바이트 뒤 `EAGAIN`이 났다(로컬 재현).

  - *파이프*: 한쪽 끝에 쓴 바이트를 다른 쪽 끝에서 순서대로 읽는 커널 버퍼다. `pipe(2)`로 만들고, 보통 `fork` 뒤 부모·자식이 한쪽씩 쓴다.
  - *FIFO(이름 있는 파이프)*: 파일시스템 경로를 가진 파이프다. 부모·자식 관계가 없어도 경로로 연다. 입출력 의미는 파이프와 같다(fifo(7)).

**파이프의 세 가지 규칙(pipe(7)).**

```text
  (1) EOF    : 쓰기 끝을 가리키는 fd가 **모두** 닫혀야 read()가 0(EOF)을 돌려준다
  (2) SIGPIPE: 읽기 끝이 모두 닫힌 뒤 write()하면 SIGPIPE
               (무시·블록하거나 핸들러로 잡으면 write()는 EPIPE)
  (3) 원자성  : PIPE_BUF(리눅스 4096) 이하 write는 다른 writer와 섞이지 않는다
                그보다 크면 섞일 수 있다
```

- 규칙 (1) 때문에 `fork` 뒤 **안 쓰는 끝은 반드시 닫는다**. 부모가 자기 쓰기 끝을 안 닫으면 자식이 끝나도 부모의 `read`는 EOF를 못 본다. 쓰기 끝이 하나 더 살아 있기 때문이다.
- 규칙 (2)의 SIGPIPE 기본 동작은 종료다. 셸에서 `yes | head -1`의 `yes`가 exit 141(128 + 13)로 끝나는 이유다(로컬 재현: `PIPESTATUS=141 0`).
- 규칙 (3): POSIX는 PIPE_BUF가 최소 512바이트이기만 요구한다(pipe(7)). 여러 프로세스가 한 파이프에 로그를 쓴다면 한 줄을 PIPE_BUF 이하로 한 번에 써야 줄이 안 섞인다.
- 파이프는 **바이트 흐름**이다. 메시지 경계가 없다. `write` 두 번이 `read` 한 번에 붙어 나올 수 있다.

### 3. 부모·자식 파이프 교착 — 가장 흔한 사고

```text
   부모                                  자식
   pipe(); fork();                      stdout = 파이프 쓰기 끝
   waitpid(자식)  <---- 잠듦 ---+        write(70,000바이트) ...
                                |          65,536바이트까지 쓰고 버퍼 가득
   (끝나면 읽을 생각)             |          write() 에서 잠듦  <----+
                                +-- 자식이 끝나야 깨어남          |
                                   자식은 부모가 읽어야 깨어남 ---+   => 서로 기다림 (교착)
```

- 작성 환경 재현(로컬): 자식 출력 60,000바이트면 정상 종료, 70,000바이트면 멈췄다.
  - 멈춘 동안 부모는 `S do_wait`, 자식은 `S anon_pipe_write`(커널 7.0의 대기 지점 이름)였다.
- CPU 사용률은 0에 가깝다. 에러도, 로그도 없다. 그래서 "가끔 멈춘다"로만 보인다.
- 출력이 작을 때(개발 환경)는 버퍼에 다 들어가서 문제없다가, 운영 데이터로 출력이 커지면 멈춘다.

### 4. 유닉스 도메인 소켓 — 같은 호스트용 소켓

```text
   서버: socket(AF_UNIX) -> bind("/run/app.sock") -> listen -> accept
   클라: socket(AF_UNIX) -> connect("/run/app.sock")
         |<----------- 양방향, 네트워크 스택(IP·TCP) 없이 커널 안에서 복사 ----------->|
   추가 기능: SCM_RIGHTS  = 열린 파일(fd)을 상대 프로세스에 건넨다
             SO_PEERCRED = 상대 프로세스의 pid·uid·gid를 커널이 알려 준다
```

- `SOCK_STREAM`(바이트 흐름), `SOCK_DGRAM`(메시지 경계 보존), `SOCK_SEQPACKET`을 지원한다(unix(7)).
  - 작성 환경: DGRAM으로 10바이트·3바이트를 보내면 `recv`가 10, 3으로 나눠 받았다. STREAM은 13바이트가 한 번에 왔다(로컬 재현).
- `SCM_RIGHTS`로 보내는 것은 정확히는 **열린 파일 설명(open file description)에 대한 참조**다. 받는 쪽 fd 번호는 다를 수 있다. 의미는 `dup`과 같다(unix(7)).
- `SO_PEERCRED`로 "누가 연결했나"를 커널이 보증한다. 돌려주는 값은 상대가 `connect`·`listen`·`socketpair`를 부른 시점의 자격 증명이다(unix(7)).
  - 예: PostgreSQL의 peer 인증은 `getpeereid()`나 `SO_PEERCRED` 같은 기능이 있는 OS에서만 된다(PostgreSQL 문서 "Peer Authentication").
- 경로 소켓은 파일시스템에 **파일로 남는다**. 닫아도 안 지워지니 `unlink`는 호출자 몫이다(unix(7)). 남은 파일에 다시 `bind`하면 `EADDRINUSE`다.
- 리눅스는 경로 대신 첫 바이트가 NUL인 **추상 이름**도 지원한다. 참조가 모두 닫히면 자동으로 사라진다. 비표준 확장이다(unix(7)).

### 5. 공유 메모리 — 복사 없는 대신 동기화는 내 몫

```text
   shm_open("/demo") -> /dev/shm/demo (tmpfs 파일)
   ftruncate(fd, size)
   mmap(MAP_SHARED)
        프로세스 A 가상주소 0x7f..a000 ─┐
                                        ├──> 같은 물리 페이지
        프로세스 B 가상주소 0x7f..c000 ─┘     (주소는 달라도 된다)
```

- POSIX 공유 메모리 객체는 리눅스에서 tmpfs(보통 `/dev/shm`)에 만들어진다. 모두 unmap하고 `shm_unlink`하거나 시스템이 꺼질 때까지 남는다(shm_overview(7), 커널 지속성).
- 가장 빠르지만 커널이 순서를 잡아 주지 않는다.
  - 작성 환경: 자식 4개가 공유 카운터를 100만 번씩 올리자 보통 `long`은 2,812,951, `atomic_fetch_add`는 4,000,000이었다(기대 4,000,000, `-O0`, 로컬 재현. 보통 변수 값은 실행마다 다르다).
- 공유 메모리 안에 둔 뮤텍스·세마포어(`pthread_mutexattr_setpshared`, `sem_init(pshared=1)`)나 원자 연산으로 동기화한다.

### 6. POSIX 메시지 큐 — 경계와 우선순위가 있는 우편함

```text
   mq_open("/jobs", O_CREAT, attr{maxmsg=10, msgsize=64})
   mq_send(q, "low-1", prio 1)
   mq_send(q, "high",  prio 9)          큐 내부:  [high(9)] [low-1(1)] [low-2(1)]
   mq_send(q, "low-2", prio 1)          mq_receive는 높은 우선순위부터, 같은 우선순위는 먼저 온 순
```

- 메시지는 우선순위 내림차순으로, 같은 우선순위는 먼저 온 순서로 놓인다(mq_send(3)). 작성 환경에서 `high(9) low-1(1) low-2(1)` 순서로 나왔다(로컬 재현).
- 큐가 차면 `mq_send`가 잠들고, `O_NONBLOCK`이면 `EAGAIN`이다. 작성 환경에서 `maxmsg=10` 큐에 10개 뒤 `EAGAIN`(로컬 재현).
- 비특권 사용자의 `mq_maxmsg` 상한 `/proc/sys/fs/mqueue/msg_max` 기본값은 10, 메시지 크기 상한 `msgsize_max`는 8192바이트다(mq_overview(7)).
- `mq_unlink`하지 않으면 시스템이 꺼질 때까지 남는다(커널 지속성, mq_overview(7)).
- System V IPC(`msgget`·`shmget`·`semget`)는 같은 일을 하는 옛 API다(sysvipc(7)). `ipcs`로 본다.

## 쓰이는 자료구조·알고리즘

- **링 버퍼(파이프)** — 16칸 `pipe_buffer` 배열 + head/tail 인덱스. 칸마다 페이지를 가리킨다. 생산자·소비자 큐의 전형이다 → [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md).
- **대기 큐(wait queue)** — 파이프는 읽는 쪽·쓰는 쪽 대기 큐(`rd_wait`, `wr_wait`)를 따로 둔다. 버퍼 상태가 바뀌면 반대편을 깨운다. 조건 변수와 같은 구조다(17번).
- **우선순위 큐(메시지 큐)** — 리눅스 POSIX mq는 우선순위별 노드를 레드블랙 트리(`msg_tree`)에 둔다(ipc/mqueue.c `posix_msg_tree_node`) → [data-structure/16-red-black-tree](../../data-structure/16-red-black-tree/2-summary.md).
- **참조 카운트** — 파이프의 EOF·SIGPIPE는 읽기 끝·쓰기 끝을 가리키는 fd 수(`readers`, `writers`)로 판정한다. 0이 되는 순간이 신호다.
- **생산자·소비자 문제** — 공유 메모리 위 큐는 세마포어 두 개(빈 칸·찬 칸)로 푸는 고전 문제다 → 원고 [systems/semaphore](../../systems/semaphore/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 어떤 IPC를 고르나

```text
  부모가 자식 출력을 받는다              -> 파이프 (stdio 연결)
  같은 호스트의 데몬과 요청/응답          -> 유닉스 소켓 (권한 = 파일 권한, 상대 신원 확인)
  큰 데이터를 여러 프로세스가 같이 읽고 씀 -> 공유 메모리 + 동기화
  작은 작업 메시지를 경계·우선순위와 함께  -> 메시지 큐 (또는 소켓 DGRAM)
  다른 호스트                          -> TCP (network/23)
```

### 2. 자식 프로세스 출력은 "기다리기 전에" 끝까지 읽는다

Java — `Process` 문서: 일부 플랫폼은 표준 입출력 버퍼가 작아서 "입력에 제때 쓰지 않거나 출력을 제때 읽지 않으면 자식이 막히거나 교착할 수 있다".

```java
ProcessBuilder pb = new ProcessBuilder("some-tool", "--dump");
pb.redirectErrorStream(true);                 // stderr를 stdout에 합쳐 파이프 하나만 읽는다
Process p = pb.start();
byte[] out = p.getInputStream().readAllBytes();   // 먼저 끝까지 읽고 (JDK 9+)
int code = p.waitFor();                           // 그다음 기다린다
// stdout·stderr를 따로 받아야 하면 두 스트림을 서로 다른 스레드로 동시에 읽는다
// 출력이 필요 없으면 pb.redirectOutput(ProcessBuilder.Redirect.DISCARD)  (JDK 9+)
```

Node — 문서: stdio 파이프 용량은 제한돼 있고, 자식이 그 이상 쓰면 버퍼가 빌 때까지 막힌다. 출력을 안 쓸 거면 `{ stdio: 'ignore' }`.

```js
const { spawn } = require('node:child_process');
const child = spawn('some-tool', ['--dump']);
child.stdout.on('data', (chunk) => { /* 계속 소비 */ });
child.stderr.on('data', (chunk) => { /* stderr도 소비. 안 읽으면 stderr 쪽에서 막힌다 */ });
child.on('close', (code) => console.log('exit', code));
// exec()는 출력을 모아 주지만 maxBuffer(기본 1024*1024) 초과 시 자식을 종료하고 출력을 자른다
```

### 3. fork 뒤 안 쓰는 끝을 닫는다

```c
int p[2]; pipe(p);
if (fork() == 0) {            /* 자식: 쓰기만 */
    close(p[0]);
    dup2(p[1], STDOUT_FILENO); close(p[1]);
    execlp("some-tool", "some-tool", (char *)NULL);
    _exit(127);
}
close(p[1]);                  /* 부모: 읽기만. 이걸 빼면 read가 EOF를 영영 못 본다 */
char buf[4096]; ssize_t n;
while ((n = read(p[0], buf, sizeof buf)) > 0) { /* 처리 */ }
waitpid(-1, NULL, 0);         /* 다 읽은 뒤 기다린다 */
```

- 작성 환경 재현(로컬): 부모가 `close(p[1])`을 안 하면 `timeout 2`에 걸려 끝났다(exit 124). 닫으면 즉시 EOF.
- 다른 자식에게 fd가 새지 않게 `pipe2(p, O_CLOEXEC)`를 쓴다(05번의 fd 상속 문제).

### 4. 진단 명령

```bash
ls -l /proc/<pid>/fd                    # pipe:[번호], socket:[번호] — 같은 번호면 같은 파이프·소켓
cat /proc/<pid>/wchan; echo             # anon_pipe_write(파이프 가득), do_wait(자식 대기) 등 (예시, 7.0)
ps -o pid,stat,wchan:20,cmd -p <pid>
lsof -p <pid> | grep -E 'FIFO|unix'     # 파이프·유닉스 소켓 목록
ss -xp                                  # 유닉스 소켓과 소유 프로세스
ls -l /dev/shm /dev/mqueue              # 남아 있는 공유 메모리·메시지 큐 (/dev/mqueue는 마운트돼 있을 때)
ipcs -a                                 # System V IPC 자원
cat /proc/sys/fs/pipe-max-size /proc/sys/fs/mqueue/msg_max
```

## 장애 시나리오와 대처

### 1. 자식 stdout을 안 읽음 → 파이프 가득 → 부모·자식 교착

- **현상**: 외부 명령을 부르는 배치가 "가끔" 멈춘다. 입력이 크면 늘 멈춘다. CPU는 0%다.
- **보이는 형태**
  - 부모 스레드 덤프가 `Process.waitFor()`(Java)나 `waitpid`에 서 있다.
  - 자식의 `wchan`이 파이프 쓰기 대기다(작성 환경 7.0에서 `anon_pipe_write`).
  - 타임아웃을 걸었다면 타임아웃 에러, 안 걸었다면 무한 대기.
- **원인**
  - 부모가 자식 종료를 먼저 기다리고 출력은 나중에 읽는다.
  - 자식 출력이 파이프 용량(기본 64 KiB, `pipe-user-pages-soft`에 닿은 사용자는 더 작음)을 넘는 순간 자식은 `write`에서, 부모는 `wait`에서 서로를 기다린다.
  - stderr를 안 읽어도 똑같다. 파이프가 두 개면 둘 다 소비해야 한다.
- **대처**
  - 읽기를 끝낸 뒤 기다린다. stdout·stderr를 동시에 소비하거나 합친다.
  - 안 쓸 출력은 버리거나(`Redirect.DISCARD`, `stdio: 'ignore'`) 파일로 보낸다.
  - 파이프 용량을 키우는 것(`F_SETPIPE_SZ`)은 한계를 뒤로 미룰 뿐이다.

### 2. EOF가 안 온다 — 쓰기 끝이 어딘가 살아 있다

- **현상**: 자식이 끝났는데 부모의 읽기 루프가 안 끝난다.
- **보이는 형태**: 부모가 `read`에서 잠들어 있다. `ls -l /proc/*/fd`에서 같은 `pipe:[번호]`를 쥔 프로세스가 더 있다.
- **원인**: 부모 자신이 쓰기 끝을 안 닫았거나, 그 fd가 다른 자식(손자 데몬 등)에게 상속됐다. 쓰기 끝이 하나라도 열려 있으면 EOF가 아니다(pipe(7)).
- **대처**: `fork` 직후 안 쓰는 끝을 닫는다. `O_CLOEXEC`로 exec 때 자동으로 닫히게 한다.

### 3. 읽는 쪽이 먼저 끝남 → SIGPIPE, exit 141

- **현상**: 파이프라인의 앞 명령이 에러 메시지 없이 죽는다. 서버가 응답을 쓰다 갑자기 사라진다.
- **보이는 형태**: exit code 141(128 + SIGPIPE 13). SIGPIPE를 무시·블록하거나 핸들러로 잡아 뒀다면 `write`가 `EPIPE`(`Broken pipe`)를 돌려준다(write(2)).
- **원인**: 읽기 끝이 모두 닫힌 파이프(또는 상대가 닫은 소켓)에 썼다.
- **대처**
  - 셸 파이프라인(`… | head`)에서는 정상 동작일 수 있다. `set -o pipefail`과 함께 쓰면 141을 실패로 오해하지 않게 처리한다.
  - 서버는 SIGPIPE를 무시(`signal(SIGPIPE, SIG_IGN)`)하거나 소켓에 `MSG_NOSIGNAL`을 쓰고 `EPIPE`를 에러로 처리한다. `MSG_NOSIGNAL`은 SIGPIPE만 막고 `EPIPE`는 그대로 돌려준다(send(2)).
  - 런타임은 이미 막아 둔다. Node는 시작할 때 SIGPIPE를 `SIG_IGN`으로 둔다(src/node.cc `ResetSignalHandlers`). HotSpot JVM은 SIGPIPE 핸들러를 걸고 무시한다(src/hotspot/os/posix/signals_posix.cpp "Ignore SIGPIPE and SIGXFSZ"). 그래서 이 런타임들에서는 프로세스가 죽지 않고 쓰기 에러(EPIPE)로 올라온다.

### 4. 공유 메모리 경쟁·잔여물

- **현상**: 공유 메모리 카운터·큐가 가끔 틀린 값을 낸다. 재시작 뒤 이상한 옛 값이 보인다.
- **보이는 형태**: 합계 불일치(작성 환경 재현: 기대 4,000,000 vs 2,812,951). `/dev/shm`에 이전 실행의 객체가 남아 있다.
- **원인**
  - 동기화 없이 read-modify-write를 했다(15번 경쟁 조건).
  - 공유 메모리·메시지 큐는 커널 지속성이다. 프로세스가 죽어도 `unlink` 전까지 남는다.
- **대처**: 원자 연산이나 공유 뮤텍스·세마포어를 쓴다. 시작 시 옛 객체를 정리하고, 종료 경로에서 `shm_unlink`·`mq_unlink`한다.

### 5. 유닉스 소켓 파일이 남아 재시작 실패

- **현상**: 데몬이 비정상 종료 뒤 다시 안 뜬다.
- **보이는 형태**: `bind: Address already in use`(`EADDRINUSE`). 남은 소켓 파일에 클라이언트가 붙으면 `Connection refused`(작성 환경 재현: 소켓 닫은 뒤 파일 존재, 재 bind 98 `EADDRINUSE`, connect 111 `ECONNREFUSED`).
- **원인**: 경로 소켓은 닫아도 파일이 남는다. 지우는 것은 호출자 몫이다(unix(7)).
- **대처**: 시작할 때 옛 소켓 파일을 `unlink`하고 bind한다(다른 인스턴스가 살아 있지 않은지 먼저 확인). 리눅스 전용이면 추상 이름을 쓴다.

## 핵심 문장

- 프로세스는 주소 공간이 갈라져 있어서, 데이터는 **커널을 거쳐**(파이프·소켓·큐) 가거나 **같은 물리 페이지를 나눠 매핑**(공유 메모리)해서 건넨다.
- 파이프는 기본 64 KiB 링 버퍼다. 차면 쓰는 쪽이 잔다. 그래서 **자식 출력을 읽기 전에 자식 종료를 기다리면 교착**한다.
- 파이프의 EOF는 쓰기 끝 fd가 **모두** 닫혀야 온다. fork 뒤 안 쓰는 끝은 닫고, fd 상속은 `O_CLOEXEC`로 막는다.
- 유닉스 소켓은 양방향이고 fd·자격 증명을 건넬 수 있다. 경로 소켓 파일은 닫아도 남는다.
- 공유 메모리는 복사가 없는 대신 동기화가 내 몫이고, 공유 메모리·메시지 큐는 `unlink` 전까지 남는다.

## 관련 주제·근거

- 선행: [21-files-and-descriptors](../21-files-and-descriptors/2-summary.md) — fd·열린 파일 설명·상속
- 연결
  - [05-fork-exec-wait](../05-fork-exec-wait/2-summary.md) — fork 뒤 fd 상속, `wait`
  - [06-signals](../06-signals/2-summary.md) — SIGPIPE 기본 동작
  - [15-race-conditions](../15-race-conditions/2-summary.md) · [18-semaphores](../18-semaphores/2-summary.md) — 공유 메모리 동기화
  - [14-mmap-and-page-cache](../14-mmap-and-page-cache/2-summary.md) — `MAP_SHARED`
  - [34-zero-copy-and-io-uring](../34-zero-copy-and-io-uring/2-summary.md) — `splice`·`vmsplice`로 파이프 복사 줄이기
  - [28-containers-namespaces-cgroups](../28-containers-namespaces-cgroups/2-summary.md) — IPC namespace가 System V IPC·POSIX mq를 격리한다
  - [network/23-socket-api](../../network/23-socket-api/2-summary.md) — 소켓 API 공통 부분
- 교재: CS:APP 3판 10장(10.8 파일 공유, 10.9 I/O 리다이렉션) · 11장(11.4 소켓 인터페이스) · 12.5 세마포어. CS:APP에 IPC 전용 장은 없다
- Linux man-pages
  - pipe(7) — 용량(2.6.11+ 16페이지), `F_GETPIPE_SZ`(2.6.35+), `pipe-max-size` 기본 1 MiB, EOF·SIGPIPE·EPIPE, PIPE_BUF 4096, `pipe-user-pages-soft`(4.5+) <https://man7.org/linux/man-pages/man7/pipe.7.html>
  - write(2) — EPIPE는 SIGPIPE를 잡거나·블록하거나·무시할 때만 보인다
  - pipe(2) · fifo(7)
  - unix(7) — STREAM/DGRAM/SEQPACKET, 추상 이름, `SO_PEERCRED`, `SCM_RIGHTS`, unlink는 호출자 몫, `EADDRINUSE` <https://man7.org/linux/man-pages/man7/unix.7.html>
  - shm_overview(7) — `/dev/shm` tmpfs, 커널 지속성 <https://man7.org/linux/man-pages/man7/shm_overview.7.html>
  - mq_overview(7) — `msg_max` 10, `msgsize_max` 8192, 커널 지속성 · mq_send(3) — 우선순위 순서 <https://man7.org/linux/man-pages/man7/mq_overview.7.html>
  - sysvipc(7) · send(2) — `MSG_NOSIGNAL`(SIGPIPE 없이 `EPIPE`)
- PostgreSQL "Peer Authentication" — `getpeereid()`·`SO_PEERCRED` <https://www.postgresql.org/docs/current/auth-peer.html>
- Node.js src/node.cc `ResetSignalHandlers`(SIGPIPE → `SIG_IGN`) · OpenJDK src/hotspot/os/posix/signals_posix.cpp(SIGPIPE 무시)
- 커널 소스
  - include/linux/pipe_fs_i.h — `pipe_inode_info`(링, `rd_wait`/`wr_wait`, `readers`/`writers`), `PIPE_DEF_BUFFERS 16` <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/include/linux/pipe_fs_i.h>
  - fs/pipe.c — `alloc_pipe_info()`: soft 한도 초과 비특권 사용자는 `PIPE_MIN_DEF_BUFFERS`(2) <https://raw.githubusercontent.com/torvalds/linux/master/fs/pipe.c>
  - ipc/mqueue.c — `posix_msg_tree_node`, `msg_tree`(rbtree)
- Java SE `Process` — 제한된 버퍼, 교착 경고 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Process.html>
- Node.js `child_process` — 파이프 용량, `stdio: 'ignore'`, `exec`의 `maxBuffer` 기본 1024*1024 <https://nodejs.org/api/child_process.html>
- 로컬 재현(리눅스 7.0, gcc 13.3): 파이프 용량 65,536(`F_GETPIPE_SZ`·논블로킹 채우기), 60,000/70,000바이트 교착과 `wchan`, 쓰기 끝 미close 시 EOF 미도착, `yes | head` 141, 유닉스 소켓 DGRAM/STREAM 경계·잔여 소켓 파일, 공유 메모리 카운터 경쟁, POSIX mq 우선순위·가득 참 `EAGAIN`
