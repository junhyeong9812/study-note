# os/28-containers-namespaces-cgroups — 컨테이너는 "보이는 것을 줄이고(namespace) 쓰는 양을 묶은(cgroup)" 보통 프로세스다 — 정리 (힌트)

## 해결하는 문제

한 서버에 서비스 여러 개를 올리면 세 가지가 부딪친다.

```text
  부딪치는 것          예
  무엇이 보이나        A가 쓰는 8080 포트를 B도 쓰고 싶다. A의 /etc/hosts를 B가 바꿔 버린다
  얼마나 쓰나          B의 메모리 누수가 호스트 전체를 OOM으로 끌고 간다
  어떤 파일로 도나      A는 glibc 2.39, B는 2.31이 필요하다
```

VM(35번)은 커널까지 통째로 따로 둬서 이 문제를 푼다. 대신 무겁다.\
컨테이너는 **커널은 하나 그대로 공유**하고, 프로세스마다 세 가지만 바꾼다.

```text
  컨테이너 = 보통 리눅스 프로세스
             + namespace   : 보이는 것을 바꾼다 (PID·네트워크·마운트·호스트명 ...)
             + cgroup      : 쓰는 양을 묶는다   (CPU·메모리·PID 수 ...)
             + 이미지 레이어 : 루트 파일시스템을 바꾼다 (overlayfs)
```

쉬운 예: 공유 오피스다.
- 건물(커널)과 전기·수도(CPU·메모리)는 하나다.
- 칸막이(namespace)가 있어 옆 팀 책상이 안 보인다.
- 전기 차단기(cgroup)가 팀마다 달려 있어 한 팀이 과열되면 그 팀만 내려간다.
- 각 팀은 자기 짐(이미지)을 들고 들어온다.

똑같은 구조다.\
`docker run`이나 쿠버네티스 파드는 결국 커널에 "이 프로세스는 새 namespace에서, 이 cgroup 안에서, 이 루트로 돌려라"를 요청하는 것이다.

실무 예:
- 호스트는 24코어인데 컨테이너 CPU는 2개로 묶였다. 앱이 24를 보고 스레드를 24개 만들면 CPU 제한에 걸려 지연이 튄다.
- `docker stop`이 늘 10초 걸리고 exit code 137로 끝난다. PID 1이 SIGTERM을 못 받았다.

## 동작·원리

### 1. 커널 하나, 보이는 세계 여러 개 — namespace

```text
                     리눅스 커널 (하나)
   +-----------------------------------------------------------+
   |  PID ns (호스트)            PID ns (컨테이너 A)              |
   |  pid 1 systemd              pid 1 java   <- 호스트에서는 pid 48213
   |  pid 812 sshd               pid 27 java 자식                |
   |  ...                                                       |
   |  net ns (호스트)            net ns (A)                      |
   |  eth0 10.0.0.5              eth0 172.17.0.2  :8080          |
   |  mnt ns (호스트)            mnt ns (A)                      |
   |  / = 호스트 디스크           / = overlayfs(이미지 레이어)      |
   +-----------------------------------------------------------+
```

- namespace는 전역 자원을 "이 namespace 안의 프로세스에게만 보이는 사본"처럼 감싼다(namespaces(7)).
- 같은 프로세스가 namespace마다 다른 이름을 가질 수 있다. 위 그림의 java는 컨테이너 안에서 pid 1, 호스트에서 pid 48213(예시)이다.

  - *namespace*: 전역 자원(PID 번호표, 네트워크 스택, 마운트 목록 등)을 격리해 보이는 범위를 나누는 커널 기능이다.

리눅스의 namespace 종류(namespaces(7) 표):

| 종류 | clone 플래그 | 격리하는 것 |
|---|---|---|
| Cgroup | `CLONE_NEWCGROUP` | cgroup 루트 디렉터리 |
| IPC | `CLONE_NEWIPC` | System V IPC, POSIX 메시지 큐 |
| Network | `CLONE_NEWNET` | 네트워크 장치·스택·포트 |
| Mount | `CLONE_NEWNS` | 마운트 지점 |
| PID | `CLONE_NEWPID` | 프로세스 ID |
| Time | `CLONE_NEWTIME` | boot·monotonic 시계 |
| User | `CLONE_NEWUSER` | 사용자·그룹 ID |
| UTS | `CLONE_NEWUTS` | 호스트명, NIS 도메인명 |

- 만드는 법은 시스템 콜 세 개다.
  - `clone(2)` + `CLONE_NEW*`: 새 namespace에서 자식을 만든다.
  - `unshare(2)`: 호출한 프로세스를 새 namespace로 옮긴다. 단 PID와 Time은 예외다. 호출자는 그대로 있고 다음 자식부터 새 namespace에 들어간다(`/proc/<pid>/ns/pid_for_children`·`time_for_children`, unshare(2)).
  - `setns(2)`: 이미 있는 namespace에 들어간다. `docker exec`·`nsenter`가 이것이다.
- 어느 namespace에 속했는지는 `/proc/<pid>/ns/`의 링크 번호로 본다. 번호가 같으면 같은 namespace다.

```text
$ ls -l /proc/self/ns            (예시, 리눅스 7.0, 호스트 셸)
cgroup -> cgroup:[4026531835]
mnt    -> mnt:[4026531832]
net    -> net:[4026531833]
pid    -> pid:[4026531836]
...
```

### 2. PID namespace의 1번 — 특별한 두 가지 의무

```text
   컨테이너 PID ns
   pid 1 (앱 or init)
     |-- pid 7  (앱이 띄운 자식)
     |     `-- pid 9  (손자) -- 부모 pid 7이 죽으면 --> pid 1의 자식이 된다(고아 입양)
     |
   시그널: 같은 ns 안에서 pid 1에 보낸 시그널은
           pid 1이 "핸들러를 등록한 시그널"만 전달된다
           (조상 ns가 보낸 SIGKILL·SIGSTOP은 예외 - 강제 전달)
   pid 1이 죽으면: 커널이 ns 안 모든 프로세스에 SIGKILL
```

- 새 PID namespace의 첫 프로세스가 pid 1, 그 namespace의 "init"이다(pid_namespaces(7)).
- **의무 1 — 고아 입양**: namespace 안에서 부모를 잃은 프로세스는 pid 1의 자식이 된다. pid 1이 `wait`로 회수하지 않으면 좀비가 쌓인다(05번).
- **의무 2 — 시그널**: namespace 안의 다른 프로세스는 pid 1이 핸들러를 등록한 시그널만 보낼 수 있다. 조상 namespace(호스트)에서 보낸 시그널도 같다. 단 SIGKILL·SIGSTOP은 조상 namespace에서 보내면 강제로 전달된다(pid_namespaces(7)).
- 그래서 **핸들러가 없는 프로그램이 pid 1이면 `docker stop`의 SIGTERM이 효과가 없다.** 보통 프로세스라면 SIGTERM의 기본 동작(종료)이 일어났을 것이다.
- pid 1이 끝나면 커널이 그 namespace의 나머지를 SIGKILL로 모두 끝낸다(pid_namespaces(7)). 컨테이너의 수명 = pid 1의 수명이다.

### 3. 쓰는 양을 묶는 트리 — cgroup v2

```text
  /sys/fs/cgroup                         (루트, cgroup2 파일시스템)
   |-- system.slice
   |     `-- docker-<id>.scope           cpu.max    = "200000 100000"  (2 CPU)
   |            cgroup.procs: 48213 ...   memory.max = 536870912        (512 MiB)
   |                                      pids.max   = 256
   `-- user.slice
         `-- user-1000.slice ...
  규칙: 자식은 부모 한도를 넘을 수 없다 (자원은 위에서 아래로 나눠진다)
```

- cgroup v2는 모든 컨트롤러가 **하나의 트리**(unified hierarchy)에 붙는다. 리눅스 4.5에서 정식이 됐다(cgroups(7)).
- 프로세스는 트리의 한 노드에 속한다. `/proc/<pid>/cgroup`의 `0::/경로`가 그 노드다.
- 자원은 위에서 아래로 나눈다(top-down constraint, 커널 문서 cgroup-v2).

  - *cgroup(control group)*: 프로세스 묶음에 CPU·메모리·I/O·PID 수 같은 자원 한도를 걸고 사용량을 세는 커널 기능이다.
  - *컨트롤러*: cgroup의 자원 종류 하나를 맡는 모듈이다. `cpu`, `memory`, `pids`, `io`, `cpuset` 등.

주요 파일(커널 문서 cgroup-v2):

| 파일 | 형식·기본값 | 뜻 |
|---|---|---|
| `cpu.max` | `$MAX $PERIOD`, 기본 `max 100000` | 기간(µs)마다 쓸 수 있는 CPU 시간(µs). `max`는 무제한 |
| `cpu.weight` | 1~10000, 기본 100 | 경쟁할 때의 **상대** 비율(한도 아님) |
| `cpu.stat` | `nr_periods`, `nr_throttled`, `throttled_usec` ... | 제한에 걸린 횟수·시간 |
| `memory.max` | 기본 `max` | 하드 한도. 회수로도 못 줄이면 cgroup 안에서 OOM killer |
| `memory.high` | 기본 `max` | 넘으면 강한 회수·지연. OOM killer는 부르지 않는다 |
| `memory.events` | `max`, `oom`, `oom_kill` ... | 한도 도달·OOM kill 횟수 |
| `pids.max` | 기본 `max` | 태스크 수 한도. 여기서 PID는 TID라 스레드도 센다 |

### 4. CPU 한도(쿼터)는 "코어 수"가 아니라 "기간당 시간"이다

`cpu.max = 200000 100000`은 "100ms마다 CPU 시간 200ms"다. 흔히 "CPU 2개"라고 부른다.\
하지만 코어 2개에 묶는 것이 아니다. 스레드가 많으면 여러 코어에서 동시에 쿼터를 빨리 써 버린다.

```text
  cpu.max = 200000 100000,  바쁜 스레드 8개가 코어 8개에서 동시에 돈다 (예시)

  시간(ms) 0        25                                    100       125
           |========|-------------------------------------|========|------
  8스레드   8 x 25ms = 200ms 소진       -> 나머지 75ms 동안 전부 정지(throttled)
                                                            새 기간, 쿼터 다시 채움

  평균 사용량은 "2 CPU"로 맞지만, 요청 하나가 운 나쁘게 걸리면 최대 75ms가 더 붙는다
```

- 쿼터는 전역으로 관리되고, 스레드가 돌 때 CPU별로 조각(slice)씩 나눠 준다. 다 쓰면 스레드는 다음 기간까지 못 돈다(커널 문서 sched-bwc).
- `cpu.stat`의 `nr_throttled`·`throttled_usec`가 오르면 이 일이 일어난 것이다.
- `cpu.weight`는 다르다. CPU가 남으면 제한이 없다. 경쟁할 때만 비율로 나눈다.

### 5. 이미지 = 읽기 전용 층 + 쓰기 층 — overlayfs

```text
   컨테이너가 보는 /  (merged)
   +------------------------------------------+
   | upperdir  (컨테이너 전용, 쓰기 가능)          |  <- 새 파일, 수정된 파일, 삭제 표시(whiteout)
   +------------------------------------------+
   | lowerdir 3 (앱 jar 레이어, 읽기 전용)         |
   | lowerdir 2 (JRE 레이어, 읽기 전용)           |  <- 이미지 레이어. 여러 컨테이너가 공유
   | lowerdir 1 (베이스 OS 레이어, 읽기 전용)       |
   +------------------------------------------+
   읽기: 위에서부터 찾아 처음 나온 것을 보여 준다
   쓰기: 아래층 파일을 처음 쓰려 하면 위층으로 통째 복사(copy_up) 후 수정
   삭제: 아래층은 못 지우니 위층에 whiteout(0/0 문자 장치 등)을 둔다
```

- overlay 마운트는 `lowerdir`(여러 개, 읽기 전용)과 `upperdir`(쓰기)를 합친 디렉터리를 만든다(커널 문서 overlayfs).
- 아래층 파일을 쓰기로 열면 먼저 위층으로 복사한다(copy_up). 큰 파일 한 바이트를 고쳐도 파일 전체가 복사된다.
- 이미지 레이어는 내용의 해시(digest)로 식별된다(OCI image-spec descriptor). 같은 레이어는 한 번만 받아 여러 이미지가 공유한다.

## 쓰이는 자료구조·알고리즘

- **계층형 트리(cgroup)** — 노드 = cgroup, 자식은 부모 한도 안에서 나눈다. 사용량은 조상으로 합산된다(`memory.events`는 계층 합산, `.local`은 자기만). 트리 순회 기초는 [data-structure/08-graph](../../data-structure/08-graph/2-summary.md).
- **namespace = 자원 테이블의 여러 사본** — PID namespace는 트리로 중첩되고(리눅스 3.7부터 깊이 32 제한), 한 프로세스는 자기 namespace부터 루트까지 **층마다 PID를 하나씩** 가진다(pid_namespaces(7)).
- **토큰 버킷에 가까운 쿼터 회계(CFS bandwidth)** — 기간마다 쿼터를 채우고, 쓰면 깎고, 0이면 멈춘다. `cpu.max.burst`는 안 쓴 몫을 조금 저축해 두는 버킷 깊이다(sched-bwc).
- **유니온 파일시스템 = 층 쌓기 조회** — 이름을 위층부터 찾아 첫 번째를 쓴다(스택·섀도잉). 삭제는 tombstone(whiteout)으로 표시한다. LSM 트리의 삭제 표시와 같은 발상이다 → [data-structure/24-lsm-tree](../../data-structure/24-lsm-tree/2-summary.md).
- **콘텐츠 주소(해시)** — 레이어 이름 = 내용의 sha256. 같으면 같은 것이니 한 번만 저장·전송한다 → [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 지금 내가 어느 namespace·cgroup에 있나

```bash
ls -l /proc/self/ns                     # namespace 번호 (호스트 셸과 비교)
cat /proc/self/cgroup                   # 0::/<cgroup 경로>  (v2면 한 줄)
stat -fc %T /sys/fs/cgroup              # cgroup2fs 이면 v2
CG=/sys/fs/cgroup$(cut -d: -f3 /proc/self/cgroup)
cat "$CG/cpu.max" "$CG/memory.max" "$CG/pids.max" 2>/dev/null
```

- 파일이 없으면 그 컨트롤러가 이 노드에서 켜져 있지 않은 것이다. 작성 환경(리눅스 7.0)의 데스크톱 세션 scope에는 `cpu.max`가 없었고 `memory.max`는 `max`였다(예시).
- 컨테이너가 자기 cgroup namespace를 가지면 자기 cgroup이 루트처럼 보여 경로가 `0::/`로 나온다(cgroup_namespaces(7)).

### 2. 앱이 보는 CPU 수를 확인한다 — 호스트 코어 수 vs 컨테이너 한도

```text
(예시, 리눅스 7.0, 24 CPU 호스트 — taskset으로 CPU 2개에 고정해 비교. 로컬 재현)
                                    그냥 실행    taskset -c 0,1
nproc                                  24            2
Node os.cpus().length                  24           24     <- 고정해도 호스트 전체를 센다
Node os.availableParallelism()         24            2
Java 8u504 "Effective CPU Count"       24            2     (java -XshowSettings:system)
```

- CPU 수를 줄이는 방법은 두 가지다. 위 실험은 **affinity(cpuset)**이고, `docker run --cpus`는 **쿼터(cpu.max)**다. `--cpus=1.5`는 `--cpu-period=100000 --cpu-quota=150000`과 같다(Docker 문서).
- **JVM**
  - JDK 10(JDK-8146115)부터 cgroup 한도를 읽는다. 8u191로 백포트됐다.
  - cgroup v2 지원은 JDK 15(JDK-8230305)이고, 11.0.16·OpenJDK 8u372로 백포트됐다. 그 이전 JVM은 v2 호스트에서 한도를 못 읽는다.
  - JDK 19부터 CPU shares(`cpu.weight`)는 CPU 수 계산에 쓰지 않는다(JDK-8281181). 쿼터와 affinity만 본다.
  - 최대 힙 기본값도 컨테이너 메모리 한도의 비율이다(`MaxRAMPercentage` 기본 25%. 작성 환경 8u504에서 확인). 한도가 약 250MiB 미만이면 `MinRAMPercentage`(기본 50%)를 쓴다(13번).
- **Node**: `os.cpus().length`로 스레드 수를 정하지 말라고 Node 문서가 직접 적는다. `os.availableParallelism()`(v18.14·v19.4+)은 libuv `uv_available_parallelism()`을 쓴다.
  - libuv 문서는 리눅스에서 affinity를 본다고만 적는다.
  - 소스는 다르다. libuv **1.49.0**(2024-09)부터 리눅스에서 cgroup의 `cpu.max` 쿼터도 반영한다(ChangeLog "linux: fix uv_available_parallelism using cgroup", src/unix/linux.c `uv__get_constrained_cpu`). 그 이전 libuv는 affinity만 본다.
  - 그래서 결과는 Node에 번들된 libuv 판에 달렸다. `node -p process.versions.uv`로 확인한다(작성 환경 Node 18.19.1은 libuv 1.48.0).

```java
// 스레드 풀 크기는 availableProcessors()로. 하드코딩한 코어 수·호스트 값 금지
int n = Runtime.getRuntime().availableProcessors();   // 컨테이너 인식 JVM이면 쿼터·affinity 반영
ExecutorService pool = Executors.newFixedThreadPool(n);
```

### 3. CPU throttling을 본다

```bash
CG=/sys/fs/cgroup$(cut -d: -f3 /proc/self/cgroup)
cat "$CG/cpu.max"        # 200000 100000 이면 2 CPU 쿼터
cat "$CG/cpu.stat"       # nr_periods, nr_throttled, throttled_usec (cpu 컨트롤러가 켜졌을 때)
```

- `nr_throttled / nr_periods` 비율과 `throttled_usec` 증가를 본다.
- 평균 CPU 사용률이 한도보다 낮아도 throttling은 난다. 짧은 순간에 스레드 여럿이 쿼터를 몰아 쓰기 때문이다(4절 그림).

### 4. PID 1을 제대로 세운다

```dockerfile
# 나쁨: 셸 형식. /bin/sh -c 아래에서 앱이 돈다 -> 셸이 pid 1이면 SIGTERM이 앱에 안 간다
ENTRYPOINT java -jar app.jar

# 좋음: exec 형식. 앱이 바로 pid 1
ENTRYPOINT ["java", "-jar", "app.jar"]

# 앱이 자식을 띄우거나 핸들러가 없으면: 작은 init을 pid 1로 (시그널 전달 + 좀비 회수)
#   docker run --init ...      (docker-run(1): "Run an init inside the container that forwards signals and reaps processes")
```

- Docker 문서: 셸 형식은 `/bin/sh -c`의 하위 명령으로 실행되고, 이 셸은 시그널을 넘기지 않는다. 그래서 앱이 pid 1이 아니고 `docker stop`의 SIGTERM을 못 받는다.
  - 참고: 셸이 단일 명령을 `exec`로 갈아 끼우는지는 셸 구현마다 다르다. 작성 환경에서 `sh -c 'sleep 3'`은 dash가 남았고 `bash -c 'sleep 3'`은 sleep으로 바뀌었다(예시, 로컬 재현). 셸 동작에 기대지 말고 exec 형식을 쓴다.
- JVM은 SIGTERM에 핸들러를 건다(셧다운 훅용, java(1) `-Xrs` 설명). 그래서 JVM이 pid 1이면 SIGTERM을 받는다.
- 직접 만든 C·Go·Node 프로그램은 SIGTERM 핸들러를 명시적으로 등록한다.

```c
static volatile sig_atomic_t stop = 0;
static void on_term(int s) { (void)s; stop = 1; }
int main(void) {
    struct sigaction sa = { .sa_handler = on_term };
    sigaction(SIGTERM, &sa, NULL);       /* pid 1이어도 이제 SIGTERM이 전달된다 */
    while (!stop) { /* 일 */ }
    /* 정리 후 종료 */
}
```

### 5. 메모리 한도와 OOM을 본다

```bash
cat "$CG/memory.max" "$CG/memory.current" "$CG/memory.peak"
grep -E 'oom|max' "$CG/memory.events"        # oom_kill 이 오르면 cgroup 안에서 OOM kill이 있었다
dmesg | grep -i 'killed process'             # 권한이 있으면 커널 로그에서 희생자 확인
```

## 장애 시나리오와 대처

### 1. 컨테이너가 호스트 코어 수를 보고 스레드 풀을 과하게 만든다

- **현상**: `--cpus=2` 컨테이너인데 스레드가 수십 개다. 부하가 오면 p99 지연이 튄다.
- **보이는 형태**
  - 앱 로그에 "workers=24"(호스트 코어 수) 같은 값이 찍힌다.
  - `cpu.stat`의 `nr_throttled`가 빠르게 오른다.
  - GC 스레드·ForkJoinPool 병렬도가 호스트 기준이다.
- **원인**
  - 앱이 CPU 수를 호스트 값으로 읽었다. 예: Node `os.cpus().length`, 컨테이너 인식 이전 JVM(8u191 이전), cgroup v2 호스트의 8u372·11.0.16 이전 JVM.
  - 스레드가 많으면 쿼터를 짧은 순간에 다 써서 throttling이 커진다(4절).
- **대처**
  - JVM을 올리거나 `-XX:ActiveProcessorCount=N`으로 명시한다.
  - Node는 `os.availableParallelism()`을 쓴다. 번들 libuv가 1.49.0 이전이면 쿼터를 반영하지 않으니 환경 변수로 워커 수를 명시한다.
  - `java -XshowSettings:system -version`(JDK 11+, JDK-8204107. 작성 환경 OpenJDK 8u504에도 있었다)으로 JVM이 본 한도를 확인한다.

### 2. CPU throttling — 평균 CPU는 낮은데 지연이 튄다

- **현상**: CPU 사용률 그래프는 한도의 50%(예시)인데 요청 지연이 수십 ms씩 튄다.
- **보이는 형태**: `cpu.stat`의 `throttled_usec`·`nr_throttled` 증가. 지연 분포가 기간(100ms) 단위로 끊긴 모양.
- **원인**: 기간 안의 앞부분에서 여러 스레드가 쿼터를 다 써서 나머지 동안 멈췄다. 평균은 1초 단위로 보니 안 보인다.
- **대처**
  - 스레드 수를 한도에 맞춘다(시나리오 1).
  - 한도를 올리거나 `cpu.max.burst`(기본 0)로 짧은 초과를 허용한다.
  - 지연에 민감하면 CPU 쿼터 대신 요청(가중치)만 두는 운영 정책도 쓴다. 이때 이웃의 영향(noisy neighbor)을 대신 받는다.

### 3. PID 1이 SIGTERM을 못 받는다 → 10초 뒤 강제 종료

- **현상**: `docker stop`·파드 종료가 늘 유예 시간을 다 채운다. 진행 중 요청이 끊기고 정리 로직이 안 돈다.
- **보이는 형태**
  - 종료에 정확히 10초(Docker 리눅스 기본) 또는 `terminationGracePeriodSeconds`가 걸린다.
  - exit code **137**(128 + SIGKILL 9). 정상적으로 SIGTERM에 끝났다면 보통 143(128 + 15)이다(작성 환경에서 JVM·핸들러 없는 C 프로그램 모두 SIGTERM에 143, 로컬 재현).
- **원인**
  - 셸 형식 ENTRYPOINT라서 셸이 pid 1이고, 셸이 시그널을 앱에 넘기지 않는다.
  - 또는 앱이 pid 1인데 SIGTERM 핸들러가 없다. pid 1에는 핸들러 없는 시그널이 전달되지 않는다(pid_namespaces(7)).
  - `docker stop`은 SIGTERM을 보내고 유예 시간 뒤 SIGKILL을 보낸다(Docker 문서).
- **대처**
  - exec 형식 ENTRYPOINT, 셸 스크립트라면 마지막에 `exec java ...`.
  - `docker run --init`처럼 시그널을 넘기고 좀비를 회수하는 작은 init을 pid 1로 둔다.
  - 앱에 SIGTERM 핸들러를 둔다.
- **같은 뿌리의 다른 증상**: pid 1이 `wait`를 안 해서 고아가 된 자식이 좀비(`<defunct>`)로 쌓이고, `pids.max`에 닿으면 `fork: Resource temporarily unavailable`이 난다(05번).

### 4. 메모리 한도 → `OOMKilled`, exit 137

- **현상**: 컨테이너가 부하 중 갑자기 재시작한다. 앱 로그는 중간에 끊긴다.
- **보이는 형태**
  - exit code 137. 쿠버네티스는 `reason: OOMKilled`, `exitCode: 137`로 표시한다(쿠버네티스 문서 "Assign Memory Resources").
  - `memory.events`의 `oom_kill` 증가. 호스트 커널 로그에 `Memory cgroup out of memory: Killed process <pid> (<이름>) ...` 형태로 남는다(mm/oom_kill.c).
- **원인**
  - cgroup 사용량이 `memory.max`에 닿고 회수로도 못 줄여 cgroup 안에서 OOM killer가 돌았다(커널 문서 cgroup-v2).
  - JVM이라면 힙만 보고 한도를 잡은 경우가 흔하다. 메타스페이스·스레드 스택·다이렉트 버퍼·페이지 캐시도 cgroup 사용량에 들어간다.
- **대처**
  - 힙은 한도의 비율로(`-XX:MaxRAMPercentage`), 나머지 몫을 남긴다.
  - `memory.high`로 먼저 느려지게 해 경고 신호를 받는다.
  - 자세한 OOM 동작은 13번.

## 핵심 문장

- 컨테이너는 VM이 아니다. **커널을 공유하는 보통 프로세스**에 namespace(보이는 것)·cgroup(쓰는 양)·overlayfs(루트 파일)를 붙인 것이다.
- PID namespace의 pid 1은 고아를 입양해 회수해야 하고, **핸들러를 건 시그널만** 받는다. 그래서 셸 형식 ENTRYPOINT나 핸들러 없는 앱은 SIGTERM을 놓치고 137로 끝난다.
- `cpu.max`는 코어 수가 아니라 **기간당 CPU 시간**이다. 스레드가 많으면 기간 앞부분에 쿼터를 다 쓰고 멈춘다(throttling).
- 앱이 보는 CPU 수는 런타임마다 다르다. 호스트 코어 수(`os.cpus().length`)로 풀 크기를 정하면 throttling을 부른다.
- 이미지는 읽기 전용 레이어의 스택이다. 쓰면 copy_up, 지우면 whiteout이다.

## 관련 주제·근거

- 선행
  - [13-oom-and-memory-limits](../13-oom-and-memory-limits/2-summary.md) — cgroup 메모리·OOM killer
  - [08-cpu-scheduling](../08-cpu-scheduling/2-summary.md) — CFS와 대역폭 제어의 바탕. 원고는 [foundations/process-thread](../../foundations/process-thread/README.md)
- 연결
  - [05-fork-exec-wait](../05-fork-exec-wait/2-summary.md) — 좀비 회수, 컨테이너 PID 1(tini)
  - [06-signals](../06-signals/2-summary.md) — 시그널 기본 동작·핸들러
  - [35-virtualization-hypervisor](../35-virtualization-hypervisor/2-summary.md) — 커널까지 나누는 격리와의 비교
  - [31-os-observability-tools](../31-os-observability-tools/2-summary.md) — 컨테이너 안에서 `top`이 보여 주는 것과 한계
  - [29-linking-and-loading](../29-linking-and-loading/2-summary.md) — alpine(musl) 이미지에서 glibc 바이너리가 안 도는 이유
  - [engineering-practice/08-container-image-optimization](../../engineering-practice/08-container-image-optimization/2-summary.md)
- Linux man-pages
  - namespaces(7) — 종류 표, `/proc/<pid>/ns` <https://man7.org/linux/man-pages/man7/namespaces.7.html>
  - pid_namespaces(7) — init의 고아 입양, 핸들러 있는 시그널만, 조상의 SIGKILL/SIGSTOP 강제 전달, init 종료 시 SIGKILL, 중첩 깊이 32(3.7+) <https://man7.org/linux/man-pages/man7/pid_namespaces.7.html>
  - cgroups(7) — v1/v2, v2 정식화(4.5) · cgroup_namespaces(7)
  - clone(2) · unshare(2) · setns(2)
- 커널 문서
  - Control Group v2 — `cpu.max`(기본 `max 100000`), `cpu.weight`(기본 100), `cpu.stat`, `memory.max`/`memory.high`/`memory.events`, `pids.max`, top-down 제약 <https://docs.kernel.org/admin-guide/cgroup-v2.html>
  - CFS Bandwidth Control — 쿼터·기간·slice·throttle·burst <https://docs.kernel.org/scheduler/sched-bwc.html>
  - Overlay Filesystem — lowerdir/upperdir/workdir, copy_up, whiteout <https://docs.kernel.org/filesystems/overlayfs.html>
- OCI image-spec — descriptor의 `digest` <https://github.com/opencontainers/image-spec/blob/main/descriptor.md>
- Docker 문서
  - Dockerfile reference ENTRYPOINT — 셸 형식은 `/bin/sh -c`, 시그널 미전달 <https://docs.docker.com/reference/dockerfile/>
  - docker container stop — SIGTERM, 리눅스 기본 10초 뒤 SIGKILL <https://docs.docker.com/reference/cli/docker/container/stop/>
  - Resource constraints — `--cpus` = period 100000 + quota <https://docs.docker.com/engine/containers/resource_constraints/>
  - docker-run(1) `--init`
- OpenJDK — JDK-8146115(컨테이너 인식, JDK 10, 8u191) · JDK-8230305(cgroup v2, JDK 15, 11.0.16·openjdk8u372) · JDK-8281181(CPU shares 미사용, JDK 19) · JDK-8204107(`-XshowSettings:system`, JDK 11) <https://bugs.openjdk.org/browse/JDK-8230305>
- Node.js `os.availableParallelism()`·`os.cpus()` <https://nodejs.org/api/os.html> · libuv `uv_available_parallelism` <https://docs.libuv.org/en/v1.x/misc.html> · libuv 소스 src/unix/core.c·linux.c(`uv__get_constrained_cpu`)와 ChangeLog 1.49.0 <https://github.com/libuv/libuv/blob/v1.x/ChangeLog>
- 쿠버네티스 "Assign Memory Resources to Containers and Pods" — `OOMKilled`, exit 137 <https://kubernetes.io/docs/tasks/configure-pod-container/assign-memory-resource/>
- 커널 소스 mm/oom_kill.c — `"Memory cgroup out of memory"`, `"%s: Killed process ..."` <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/mm/oom_kill.c>
- 로컬 재현(리눅스 7.0, Ubuntu 24.04): `/proc/self/ns`·`/proc/self/cgroup` 조회, `taskset`으로 nproc·Node·JVM CPU 수 비교, `sh -c`/`bash -c` exec 차이, SIGTERM exit 143
