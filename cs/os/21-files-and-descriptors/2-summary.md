# os/21-files-and-descriptors — 번호 하나 뒤의 세 겹 테이블, 이름과 inode는 따로 산다 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

프로그램이 파일을 읽을 때마다 경로 문자열을 넘긴다고 해 보자.\
커널은 매번 경로를 풀고, 권한을 검사하고, "어디까지 읽었는지"를 따로 기억해야 한다.\
게다가 파일만 있는 게 아니다. 소켓·파이프·터미널도 읽고 쓴다.

그래서 유닉스는 한 번 `open()`하면 **작은 정수 하나**를 돌려준다. 이것이 **파일 디스크립터(fd)**다.\
이후 `read`·`write`·`close`는 이 번호만 쓴다.

  - *파일 디스크립터(fd)*: 프로세스의 "열린 파일 표"에서 칸 번호다. 음이 아닌 작은 정수다(open(2)).

쉬운 예: 코트 보관소다.
- 코트를 맡기면 번호표(fd)를 받는다.
- 보관소 장부(열린 파일 기록)에는 "몇 번 옷걸이, 누가 맡겼나"가 적혀 있다.
- 옷 자체(inode)는 옷걸이에 걸려 있다. 옷에 붙은 이름표(파일 이름)는 떼어도 옷은 남는다.
- 번호표를 돌려줘야(close) 다음 손님이 그 번호를 쓴다. 번호표를 안 돌려주는 손님이 많으면 번호표가 동난다.

똑같은 구조다.\
fd → 열린 파일 기록 → inode의 세 겹이다. 이름(디렉터리 항목)은 inode를 가리키는 또 다른 끈일 뿐이다.

실무 예:
- 커넥션·파일을 닫지 않는 코드가 몇 시간 돌면 `Too many open files`(`EMFILE`)로 새 연결을 못 받는다.
- 디스크가 꽉 차서 큰 로그를 `rm`했는데 `df`가 줄지 않는다. 로그를 쓰던 프로세스가 아직 fd를 쥐고 있다.

## 동작·원리

### 세 겹 테이블

```text
  프로세스 A                    커널 전체                         파일 시스템
  fd 테이블                     열린 파일 기록(OFD)                inode
  +----+                       +---------------------+          +-----------------+
  | 0  |-----> (터미널)          |                     |          |                 |
  | 1  |-----> (터미널)          |                     |          |                 |
  | 3  |---------------------> | offset=5, O_RDWR    |--------> | inode 4342804   |
  | 5  |-----(dup)-----------> | ref=2               |    +---> | 크기·권한·블록 위치 |
  | 4  |---------------------> | offset=0, O_RDONLY  |----+     | nlink=1         |
  +----+                       +---------------------+          +-----------------+
                                                                    ^
  디렉터리 "."의 항목:  "f.txt" -> inode 4342804  ------------------+
```

- **fd 테이블**: 프로세스마다 하나다. 칸 번호가 fd다. 칸에는 OFD를 가리키는 포인터가 있다.
- **열린 파일 기록(OFD)**: `open()` 한 번마다 새로 하나 생긴다. **파일 오프셋**과 **상태 플래그**(`O_APPEND`·`O_NONBLOCK` 등)를 담는다(open(2)).
- **inode**: 파일 그 자체다. 크기·권한·데이터 블록 위치·링크 수를 담는다. 이름은 inode 안에 없다.
- 디렉터리 항목이 "이름 → inode 번호"를 잇는다(22번).

  - *열린 파일 기록(open file description, OFD)*: POSIX 용어다. 커널 코드에서는 `struct file`이다(open(2) NOTES). 오프셋(`f_pos`)·플래그(`f_flags`)·참조 수(`f_ref`)·inode 포인터(`f_inode`)를 가진다(include/linux/fs.h).
  - *inode*: 파일 하나의 메타데이터와 데이터 위치를 담은 구조다. 파일 시스템 안에서 번호로 식별된다.

### 누가 무엇을 공유하나

```text
  (a) 같은 파일을 두 번 open         (b) dup(fd) / fork()
  fd3 -> OFD#1(offset) -+          fd3 --+
                        +-> inode        +--> OFD#1(offset) -> inode
  fd4 -> OFD#2(offset) -+          fd5 --+   (fork면 자식의 fd3도 여기)
  오프셋 따로 움직인다                 오프셋을 함께 쓴다
```

- 두 번 `open()`하면 OFD가 둘이다. 한쪽을 읽어도 다른 쪽 오프셋은 그대로다.
- `dup()`과 `fork()`는 **같은 OFD**를 가리키는 fd를 만든다. 오프셋과 상태 플래그를 공유한다(open(2)).
- 로컬 재현(예시, 리눅스 7.0):

```text
fds a=3 b=4 c=5                                  # c = dup(a), b = 따로 open
read via c after lseek(a,0): 'hello' ; offset a=5 b=0
parent offset of a after child lseek(6): 6       # fork한 자식이 옮긴 오프셋이 부모에게 보인다
```

- 그래서 fork 뒤 부모·자식이 같은 fd로 쓰면 한 오프셋을 함께 민다. 리눅스 3.14부터 일반 파일의 `write`는 이 공유 오프셋 갱신이 원자적이라 서로 덮어쓰지 않는다(write(2) BUGS). 3.14 전에는 겹칠 수 있었다.
- 덮어쓰기가 나는 것은 **각자 따로 `open()`해 OFD가 둘**일 때다. 오프셋이 따로 놀아 같은 자리에 쓴다. 로그를 여러 프로세스가 함께 쓰려면 `O_APPEND`를 쓴다.
  - `O_APPEND`: 매 `write` 전에 오프셋을 파일 끝으로 옮긴다. 옮기기와 쓰기가 한 원자적 단계다(open(2)). 단 NFS에서는 이 보장이 깨질 수 있다(open(2)).

### open — 가장 작은 빈 번호

```text
  fd 테이블:  [0 사용][1 사용][2 사용][3 빈칸][4 사용] ...
  open() -> 3   (지금 비어 있는 가장 작은 번호)
```

- 성공한 `open()`은 **지금 열려 있지 않은 가장 작은 fd**를 돌려준다(open(2)).
- 로컬 재현: `close(0)` 뒤 `open()`하면 0이 나왔다(예시, 리눅스 7.0).
- 이 규칙 때문에 fd 번호는 **곧바로 재사용**된다. 한 스레드가 닫은 번호를 다른 스레드가 새 파일로 받을 수 있다.
- 기본값으로 fd는 `execve()` 뒤에도 열려 있다. `O_CLOEXEC`를 주면 exec 때 닫힌다(open(2)). fork·exec 뒤 상속되는 fd는 05번에서 다룬다.

### close — 번호를 돌려준다, 데이터를 디스크에 쓰는 게 아니다

```text
  close(fd)
    1. fd 테이블 칸을 비운다            (번호는 즉시 재사용 가능)
    2. OFD 참조 수 -1  -> 0이면 OFD 해제
    3. inode 링크 수가 0이고 열린 곳도 없으면 -> 파일 삭제, 공간 반환
```

- 마지막 fd가 닫히면 OFD가 해제된다. 그 파일이 이미 `unlink`된 상태였다면 이때 파일이 삭제된다(close(2)).
  - 단 fd만 OFD를 쥐는 것은 아니다. `mmap` 매핑은 fd를 닫아도 살아 있고(mmap(2)), 매핑이 풀릴 때(`munmap`·프로세스 종료)까지 파일을 붙잡는다. 이런 파일은 `lsof`에서 FD 열이 번호 대신 `mem`으로 보이고, 지워진 매핑이면 `DEL` 표시가 붙는다(lsof(8)).
- **close 성공 ≠ 디스크 기록**. 커널은 버퍼 캐시로 쓰기를 미룬다. 파일 시스템은 보통 close 때 버퍼를 비우지 않는다. 디스크까지 보장하려면 `fsync`(24번)를 쓴다(close(2) NOTES).
- close의 반환값은 확인한다. 앞선 `write`의 오류가 마지막 close에서야 보고될 수 있다. NFS·디스크 쿼터에서 특히 그렇다(close(2)).
- 그러나 **close를 재시도하지 않는다**. 리눅스는 close 초반에 fd를 먼저 풀어 준다. 오류는 그 뒤 단계에서 난다. 재시도하면 다른 스레드가 새로 받은 같은 번호를 닫을 수 있다(close(2)).
  - `EINTR`도 리눅스에서는 fd가 이미 닫힌 상태다. POSIX.1-2008은 이때 fd 상태를 unspecified로 두었다. man-pages 6.19는 POSIX.1-2024가 HP-UX 방식(`EINTR`이면 fd가 열린 채 남음)을 표준화해 리눅스가 비준수가 되었고, 리눅스는 바꿀 계획이 없다고 적는다(close(2), man7.org).

### 이름 · 하드 링크 · 심볼릭 링크 · unlink

```text
  디렉터리 항목들                     inode 4342804 (nlink=2)
  "f.txt" ------------------------->  데이터 블록들
  "g.txt" ------------------------->  (같은 파일)

  "link.txt" (심볼릭 링크 inode)  내용 = 문자열 "f.txt"  --(경로로 다시 찾기)--> ...
```

- **하드 링크**: 같은 inode를 가리키는 이름을 하나 더 만든다. inode의 링크 수(`st_nlink`)가 1 오른다.
  - 로컬 재현: `link("f.txt","g.txt")` 뒤 `st_nlink`가 2였다(예시, 리눅스 7.0).
  - 디렉터리에는 보통 만들 수 없다(순환 방지). 다른 파일 시스템에도 만들 수 없다. inode 번호는 파일 시스템 안에서만 고유하다(OSTEP 39.15).
- **심볼릭 링크**: 경로 문자열을 내용으로 가진 별도 파일이다. 가리키는 대상이 지워지면 끊긴 링크(dangling)가 된다(OSTEP 39.15).
- **unlink**: 이름 하나를 지운다. 마지막 이름이고 아무도 열고 있지 않을 때만 파일이 삭제되고 공간이 돌아온다. 누가 열고 있으면 마지막 fd가 닫힐 때까지 파일이 남는다(unlink(2)). 그래서 `rm`이 쓰는 시스템 콜이 `unlink` 계열이다. GNU coreutils `rm`은 `unlinkat(2)`를 부르므로 strace는 `-e trace=unlink,unlinkat`으로 잡는다(로컬 재현, coreutils 9.4: `unlinkat(AT_FDCWD, "zz", 0) = 0`).
- `rename`: 이름을 바꾼다. 다른 하드 링크와 열린 fd에는 영향이 없다(rename(2)). 크래시 원자성은 24번에서 다룬다.

### 열린 채 지운 파일 — 공간이 안 돌아오는 이유

```text
  rm big.log           -> 디렉터리 항목만 사라짐 (nlink 1 -> 0)
  로거는 fd 3을 계속 쥠   -> OFD 살아 있음 -> inode·블록 살아 있음
  df "사용량"            -> 그대로
  로거 재시작 / fd close   -> 그제서야 블록 반환 (mmap 매핑도 없을 때)
```

- 로컬 재현(예시, 리눅스 7.0): 64 MiB 파일을 `sleep` 프로세스가 연 채로 `rm`했다.
  - `df` 사용량은 `rm` 전후 같았다(440852204 KB → 440852204 KB).
  - `lsof +L1`에 `big.log (deleted)`가 보였다. `/proc/<pid>/fd/3`도 `... (deleted)`를 가리켰다.
  - `: > /proc/<pid>/fd/3`로 내용을 비우자 사용량이 65528 KB 줄었다.

### 한도 — 몇 개까지 열 수 있나

```text
  프로세스 한도   RLIMIT_NOFILE (soft ≤ hard)     넘으면 EMFILE  "Too many open files"
  커널 상한       /proc/sys/fs/nr_open            hard 한도를 이 위로 못 올림 (소스 기본 1024*1024)
  시스템 전체     /proc/sys/fs/file-max           넘으면 ENFILE  (열린 OFD 전체 수)
```

- `RLIMIT_NOFILE`은 "열 수 있는 최대 fd 번호 + 1"이다. 넘으면 `open`·`pipe`·`dup` 등이 `EMFILE`로 실패한다(getrlimit(2)).
- 시스템 전체 한도는 `file-max`다. 넘으면 `ENFILE`이다. `/proc/sys/fs/file-nr`은 할당된 OFD 수, 0, 최대값을 보여 준다(proc_sys_fs(5)).
- `nr_open`의 커널 소스 기본값은 `1024*1024`다(fs/file.c `sysctl_nr_open`).
- systemd 서비스의 기본 한도는 배포판·버전마다 다르다. 작성 환경(systemd 255)에서 `DefaultLimitNOFILESoft=1024`, 시스템 `DefaultLimitNOFILE=524288`이었다(예시, `systemctl show`).
- 로컬 재현: `setrlimit(RLIMIT_NOFILE, 16)` 뒤 `/dev/null`을 계속 열자 10개를 더 열고 `errno=24 (Too many open files)`가 났다(예시, 리눅스 7.0).

## 쓰이는 자료구조·알고리즘

- **동적 배열(fd 테이블)** — `struct fdtable`의 `fd`는 `struct file *` 배열이다. 모자라면 2의 거듭제곱 크기로 새 배열을 만들어 옮긴다(fs/file.c `alloc_fdtable`의 `roundup_pow_of_two`). 첫 크기는 `BITS_PER_LONG`(64비트에서 64칸)이다(`NR_OPEN_DEFAULT`). [data-structure/01-dynamic-array](../../data-structure/01-dynamic-array/2-summary.md)
- **비트맵(가장 작은 빈 번호 찾기)** — `open_fds` 비트맵에서 0인 비트를 찾는다(fs/file.c `find_next_fd` → `find_next_zero_bit`). `full_fds_bits`는 "한 워드가 꽉 찼나"를 한 비트로 요약해 건너뛰게 한다. [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)
- **참조 수 세기** — OFD는 `f_ref`로, inode는 링크 수(`i_nlink`)와 열린 참조로 수명을 정한다. 둘 다 0이 되어야 실제로 해제된다.
- **이름 → 번호 매핑(디렉터리)** — 디렉터리는 "이름 → inode 번호" 표다. ext4는 큰 디렉터리를 해시 트리(htree)로 찾는다(22번).
- **close-on-exec 비트맵** — `close_on_exec` 비트맵이 fd마다 `FD_CLOEXEC`를 기억한다(include/linux/fdtable.h).

## 적용 — 풀어나가는 법

### 1. 여는 코드는 닫는 코드와 짝을 짓는다

Java — try-with-resources가 예외 경로에서도 닫는다.

```java
try (var in = new FileInputStream(path);                 // fd 1개
     var out = Files.newOutputStream(target)) {          // fd 1개
    in.transferTo(out);
}   // 여기서 둘 다 close — 예외가 나도
```

Node.js — `fs.promises`의 `FileHandle`은 `finally`에서 닫는다.

```js
const fh = await fs.promises.open(path, 'r');
try {
  const { bytesRead } = await fh.read(Buffer.alloc(4096), 0, 4096, 0);
} finally {
  await fh.close();          // 빠뜨리면 fd 누수
}
```

- 한도에 닿으면 이렇게 보인다(로컬 재현, `ulimit -n 64`, 예시).
  - Java(JDK 21): `java.io.FileNotFoundException: /etc/hostname (Too many open files)`
  - Node 18: `EMFILE: too many open files, open '/etc/hostname'` (`err.code === 'EMFILE'`)

C — 반환값을 확인하되 close는 재시도하지 않는다.

```c
int fd = open(path, O_RDONLY | O_CLOEXEC);   /* exec로 새지 않게 */
if (fd < 0) { perror("open"); return -1; }   /* EMFILE, ENFILE, ENOENT ... */
/* ... read ... */
if (close(fd) < 0) perror("close");          /* 기록만 한다. 다시 close하지 않는다 */
```

### 2. 진단 명령

```bash
ls /proc/<pid>/fd | wc -l                 # 지금 연 fd 수
ls -l /proc/<pid>/fd                      # fd -> 대상 (파일 경로, socket:[inode], pipe:[...])
grep 'open files' /proc/<pid>/limits      # soft / hard 한도
lsof -p <pid> | awk '{print $5}' | sort | uniq -c | sort -rn   # 종류별(REG, IPv4, unix...) 개수
lsof -nP +L1                              # 링크 수 < 1 = 지웠는데 열려 있는 파일
cat /proc/sys/fs/file-nr                  # 시스템 전체: 할당 OFD, 0, file-max
ulimit -n                                 # 현재 셸의 soft 한도
```

- `lsof +L1`: 링크 수가 1보다 작은(= 지워진) 열린 파일만 보인다(lsof(8) `+L`).
- fd 수를 시간에 따라 찍어 **계단식으로 오르기만 하면** 누수다. 부하에 따라 오르내리면 정상 사용이다.

### 3. 한도를 올리기 전에 누수를 먼저 본다

- 한도를 올리는 것은 누수를 늦출 뿐이다.
- 그래도 연결이 많은 서버(웹소켓·프록시)는 한도가 실제로 부족하다. systemd 서비스는 `LimitNOFILE=`, 컨테이너는 런타임의 ulimit 설정으로 올린다.

## 장애 시나리오와 대처

### 1. fd 누수 → `EMFILE: Too many open files`

- **현상**: 서비스가 몇 시간·며칠 잘 돌다가 새 연결·새 파일 열기가 모두 실패한다. 재시작하면 한동안 괜찮다.
- **보이는 형태**
  - Java `java.io.FileNotFoundException: ... (Too many open files)`(로컬 재현, JDK 21). 괄호 안은 errno의 strerror 문자열이다.
  - Node `Error: EMFILE: too many open files`.
  - `ls /proc/<pid>/fd | wc -l`이 `grep 'open files' /proc/<pid>/limits`의 soft 값에 붙어 있다.
- **원인**
  - 예외 경로에서 스트림·소켓·HTTP 응답 본문을 닫지 않는다.
  - 커넥션 풀 없이 요청마다 새 클라이언트를 만든다.
  - 기본 soft 한도가 작다(작성 환경 systemd 기본 soft 1024, 예시).
- **대처**
  - `lsof -p`로 어떤 종류(REG·TCP·pipe)가 쌓이는지 본다. 같은 경로·같은 원격 주소가 반복되면 그 코드가 범인이다.
  - try-with-resources·`finally`로 닫는다. HTTP 클라이언트는 응답 본문까지 소비·close한다.
  - 원인을 고친 뒤 필요하면 `LimitNOFILE`을 올린다.

### 2. 지운 로그가 공간을 안 돌려준다

- **현상**: 디스크 사용률 100%. 큰 로그를 `rm`했는데 `df`가 그대로다. `du`로 합쳐 보면 `df`보다 훨씬 작다.
- **보이는 형태**: `lsof -nP +L1`에 `(deleted)` 파일이 크게 보인다. 쓰기는 `ENOSPC`(`No space left on device`)로 계속 실패한다.
- **원인**: 로그를 쓰던 프로세스가 fd를 쥐고 있다. `rm`(unlink)은 이름만 지웠고, 링크 수 0 + 열린 참조가 남아 inode·블록이 살아 있다(unlink(2)).
- **대처**
  - 그 프로세스를 재시작하거나 로그 파일을 다시 열게 한다(많은 데몬이 `SIGHUP`·`SIGUSR1`로 로그 재오픈).
  - 급하면 `: > /proc/<pid>/fd/<n>`로 내용을 비운다(로컬 재현에서 공간이 즉시 돌아왔다).
  - 예방: 로그 회전은 "이름 바꾸고 재오픈 신호" 방식으로 한다. 재오픈을 못 하는 프로그램이면 logrotate `copytruncate`를 쓴다. 단 복사와 비우기 사이에 쓴 로그는 잃을 수 있다(logrotate(8)).

### 3. 여러 프로세스가 같은 로그 파일에 쓰다 내용이 겹친다

- **현상**: 부모·자식(또는 여러 워커)이 같은 로그에 쓰는데 줄이 서로 덮이거나 끊긴다.
- **보이는 형태**: 로그 줄이 중간에 끊기거나 다른 프로세스의 줄로 덮여 있다. 줄 수가 쓴 줄 수보다 적다.
- **원인**
  - 각 프로세스가 **따로 `open()`**해 OFD(오프셋)가 둘이다. `O_APPEND` 없이 쓰면 두 프로세스가 같은 위치에 쓴다.
  - fork로 **같은 OFD를 공유**하면 리눅스 3.14부터 일반 파일의 오프셋 갱신이 원자적이라 덮어쓰지 않는다(write(2) BUGS). 다만 한 줄을 여러 번의 `write`로 나눠 내면 줄 중간에 다른 프로세스의 쓰기가 끼어 끊긴다.
  - 로컬 재현(예시, 리눅스 7.0): 부모·자식이 각 20000줄을 쓰자, fork 전에 연 fd 공유는 40000줄, 각자 `open()`은 20000줄만 남았다.
- **대처**: 로그 파일은 `O_APPEND`로 연다. 한 줄은 한 번의 `write`로 낸다. 여러 프로세스가 NFS의 한 파일에 append하는 설계는 피한다(open(2)).

### 4. 닫은 fd 번호를 다른 스레드가 재사용 → 엉뚱한 파일·소켓을 건드린다

- **현상**: 드물게 엉뚱한 연결로 데이터가 가거나, 멀쩡한 연결이 갑자기 끊긴다.
- **보이는 형태**: 재현이 어렵다. `strace -f`에 같은 번호의 `close`가 두 번 보인다.
- **원인**
  - close 실패 후 **재시도**했다. 그사이 다른 스레드가 같은 번호를 받았다(close(2)).
  - 또는 다른 스레드가 쓰는 중인 fd를 닫았다. 리눅스에서는 이미 진행 중인 시스템 콜이 OFD를 붙잡고 있어 끝까지 성공할 수 있다(close(2)).
- **대처**: close는 한 번만 부른다. fd의 소유자를 한 곳으로 정한다. 언어 런타임의 소켓·스트림 객체를 쓰고 raw fd를 공유하지 않는다.

## 핵심 문장

- fd는 프로세스 fd 테이블의 칸 번호다. 그 칸은 OFD(오프셋·플래그)를 가리키고, OFD는 inode를 가리킨다.
- `open()`마다 새 OFD가 생긴다. `dup()`·`fork()`는 같은 OFD를 공유해 오프셋도 함께 움직인다.
- `open()`은 가장 작은 빈 번호를 준다. 그래서 fd 번호는 곧바로 재사용되고, close 재시도는 위험하다.
- 이름은 inode를 가리키는 끈이다. 파일은 링크 수 0 **그리고** 열린 참조 0일 때 사라진다. 열린 채 지운 로그가 공간을 안 돌려주는 이유다.
- close 성공은 디스크 기록을 뜻하지 않는다. 내구성은 `fsync`의 일이다.
- `EMFILE`은 프로세스 한도, `ENFILE`은 시스템 한도다. 한도를 올리기 전에 누수를 찾는다.

## 관련 주제·근거

- 선행: [05-fork-exec-wait](../05-fork-exec-wait/2-summary.md) — fork의 fd 상속, `O_CLOEXEC`
- 후속·연결
  - [22-file-system-implementation](../22-file-system-implementation/2-summary.md) — inode·디렉터리가 디스크에 놓이는 방식
  - [24-fsync-and-durability](../24-fsync-and-durability/2-summary.md) — close ≠ 디스크, rename 원자성
  - [network/23-socket-api](../../network/23-socket-api/2-summary.md) — 소켓도 fd다
  - [26-io-multiplexing-epoll](../26-io-multiplexing-epoll/2-summary.md) — fd로 다루는 I/O 대기
  - [30-ipc](../30-ipc/2-summary.md) — 파이프·유닉스 소켓도 fd
  - [37-os-symptom-index](../37-os-symptom-index/2-summary.md)(`EMFILE`·`ENOSPC`)
- Linux man-pages
  - open(2) — 가장 작은 fd, OFD, `O_APPEND` 원자성, `O_CLOEXEC`, `EMFILE`/`ENFILE` <https://man7.org/linux/man-pages/man2/open.2.html>
  - close(2) — 마지막 참조·unlink된 파일 삭제, 재시도 금지, `EINTR`, POSIX.1-2024 주석(man-pages 6.19) <https://man7.org/linux/man-pages/man2/close.2.html>
  - unlink(2)·`unlinkat`, mmap(2)(fd를 닫아도 매핑 유지), link(2), rename(2), dup(2), getrlimit(2) `RLIMIT_NOFILE`, proc_sys_fs(5) `file-max`·`file-nr`·`nr_open`, lsof(8) `+L`·`mem`·`DEL`, logrotate(8) `copytruncate`
- 커널
  - include/linux/fdtable.h — `struct fdtable`(`fd`, `open_fds`, `close_on_exec`, `full_fds_bits`), `NR_OPEN_DEFAULT` <https://github.com/torvalds/linux/blob/master/include/linux/fdtable.h>
  - fs/file.c — `sysctl_nr_open = 1024*1024`, `alloc_fdtable`(2의 거듭제곱), `find_next_fd` <https://github.com/torvalds/linux/blob/master/fs/file.c>
  - include/linux/fs.h — `struct file`(`f_pos`, `f_flags`, `f_ref`, `f_inode`)
  - Documentation/filesystems/vfs.rst — dentry·inode·file 객체
- 교재
  - OSTEP 39장 "Interlude: Files and Directories" — 39.5~39.6 open file table·fork/dup 공유, 39.14~39.15 하드·심볼릭 링크 <https://pages.cs.wisc.edu/~remzi/OSTEP/file-intro.pdf>
  - CS:APP 3판 10장 "System-Level I/O" — 파일 공유·I/O 리다이렉션 절(절 번호 [?])
- write(2) BUGS — 공유 OFD의 오프셋 갱신 원자성은 리눅스 3.14부터 <https://man7.org/linux/man-pages/man2/write.2.html>
- 로컬 재현(리눅스 7.0, glibc/gcc 13.3): 공유 OFD vs 따로 open 동시 쓰기, fd 번호·dup/fork 오프셋 공유·링크 수·열린 채 unlink·`EMFILE`(C), 열린 채 `rm` 후 `df`·`lsof +L1`, Java 21·Node 18의 `EMFILE` 메시지
