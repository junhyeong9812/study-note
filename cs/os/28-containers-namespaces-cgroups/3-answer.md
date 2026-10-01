# os/28-containers-namespaces-cgroups — 정답

## 정답

### 1. 세 요소와 공유하는 것

- **namespace** — 보이는 것을 바꾼다. PID 번호표, 네트워크 스택, 마운트 목록, 호스트명 등을 프로세스 묶음마다 따로 보이게 한다(namespaces(7)).
- **cgroup** — 쓰는 양을 묶는다. CPU 시간·메모리·태스크 수 한도를 걸고 사용량을 센다.
- **이미지 레이어(overlayfs)** — 루트 파일시스템을 바꾼다. 읽기 전용 레이어 위에 컨테이너 전용 쓰기 층을 얹는다.
- VM과 달리 **커널을 공유**한다. 컨테이너 안의 시스템 콜은 호스트 커널이 그대로 처리한다. 그래서 가볍지만, 커널 버그·커널 설정은 모든 컨테이너가 같이 겪는다.

### 2. PID namespace 중첩

```text
  루트 PID ns (호스트)
    pid 1 systemd
    pid 48213 java  ----+   같은 프로세스
                        |
    +-- 자식 PID ns (컨테이너)
          pid 1 java ----+
          pid 27 (java의 자식)   = 호스트에서는 또 다른 번호
```

- 한 프로세스는 자기 namespace부터 루트까지 층마다 PID를 하나씩 가진다. `getpid()`는 자기가 만들어진 namespace의 번호를 돌려준다(pid_namespaces(7)).
- 부모 namespace는 자식 namespace의 프로세스를 볼 수 있다. 반대는 안 된다.
- 확인: `ls -l /proc/<pid>/ns/pid`의 `pid:[번호]`를 비교한다. 같으면 같은 namespace다. `readlink`로 봐도 된다.

### 3. 셸 형식 ENTRYPOINT와 `docker stop`

- 셸 형식은 `/bin/sh -c "java -jar app.jar"`로 실행된다. 셸이 단일 명령을 exec로 갈아 끼우지 않는 구현(예: 작성 환경의 dash)이면 pid 1은 셸이고 java는 그 자식이다.
- `docker stop`은 pid 1에 SIGTERM을 보낸다. Docker 문서대로 이 셸은 시그널을 넘기지 않는다. pid 1인 셸에 SIGTERM 핸들러가 없으면 커널이 전달조차 하지 않는다.
- 아무 일도 일어나지 않다가 유예 시간(리눅스 기본 10초) 뒤 SIGKILL → exit **137**(128 + 9). 셧다운 훅은 돌지 않는다.
- exec 형식(`["java","-jar","app.jar"]`)이면 java가 pid 1이다. JVM은 SIGTERM 핸들러를 걸기 때문에(java(1) `-Xrs` 설명) 셧다운 훅을 돌고 곧 끝난다. SIGTERM으로 끝난 JVM의 exit code는 작성 환경에서 143(128 + 15)이었다(로컬 재현).

### 4. pid 1의 두 가지 차이

1. **고아 입양·회수**: namespace 안에서 부모를 잃은 프로세스는 pid 1의 자식이 된다. pid 1이 `wait`하지 않으면 좀비가 쌓인다.
2. **시그널 제한**: 같은 namespace의 프로세스든 조상 namespace의 프로세스든, pid 1이 핸들러를 등록한 시그널만 보낼 수 있다.

- 예외: SIGKILL·SIGSTOP을 **조상 namespace**에서 보내면 강제로 전달된다. 이 둘은 잡을 수 없으니 기본 동작(종료·정지)이 일어난다(pid_namespaces(7)). 그래서 호스트의 `kill -9`는 통한다.
- 덧붙여, pid 1이 끝나면 커널이 그 namespace의 나머지 프로세스를 모두 SIGKILL로 끝낸다.

### 5. 쿼터 계산

- `200000 100000` = 100ms마다 CPU 시간 200ms.
- 스레드 8개가 동시에 돌면 8 × 25ms = 200ms. 기간 시작 후 약 25ms 만에 쿼터를 다 쓴다.
- 나머지 약 75ms 동안 이 cgroup의 스레드는 모두 멈춘다(throttled). 다음 기간에 쿼터가 다시 채워진다(sched-bwc).
- 1초 평균으로 보면 "2 CPU만큼 썼다"로 한도와 맞아 보인다. 멈춤은 100ms 안에서 일어나니 평균 그래프에 안 보인다. `cpu.stat`의 `nr_throttled`·`throttled_usec`나 지연 분포로 봐야 한다.
- (수치는 예시다. 실제로는 slice 단위 배분과 스케줄링 때문에 정확히 25ms에 끊기지는 않는다.)

### 6. 런타임이 보는 CPU 수

- Node `os.cpus().length`는 호스트 CPU 목록을 센다. 작성 환경에서 `taskset -c 0,1`로 묶어도 24였다(로컬 재현). `--cpus=2`에서도 24를 볼 가능성이 크다. Node 문서도 이 값으로 병렬도를 정하지 말라고 한다.
- 최신 JVM(JDK 15+, 11.0.16+, OpenJDK 8u372+)은 cgroup v2의 `cpu.max`를 읽어 2를 돌려준다. 구형 JVM(특히 cgroup v2 지원 이전)은 24를 볼 수 있다.
- shares/weight가 빠진 이유(JDK-8281181): shares는 경쟁할 때의 **상대 비율**이지 한도가 아니다. 이것을 "1024 = 1 CPU"처럼 절대 CPU 수로 바꾸자 여유 CPU가 있어도 못 쓰는 저활용이 생겼다.

### 7. overlayfs의 읽기·수정·삭제

- (a) 읽기: 위층(upperdir)부터 아래로 이름을 찾아 처음 나온 파일을 보여 준다. 아래층 파일은 복사 없이 그대로 읽는다.
- (b) 수정: 아래층 파일을 쓰기로 열면 **copy_up** — 파일 전체(메타데이터·xattr 포함)를 위층으로 복사한 뒤 위층 사본을 고친다. 이후 접근은 위층 사본으로 간다.
- (c) 삭제: 아래층은 읽기 전용이라 못 지운다. 위층에 **whiteout**(0/0 장치 번호의 문자 장치, 또는 xattr 표시 파일)을 둬서 아래층 이름을 가린다(커널 문서 overlayfs).
- 그래서 큰 파일을 조금 고쳐도 통째로 복사되고, 아래층에서 "지운" 파일도 이미지 크기에서는 줄지 않는다.

### 8. exit 137 가려내기

- 137 = 128 + 9(SIGKILL)다. 누가 SIGKILL을 보냈는지는 exit code만으로 모른다.
- OOM kill의 흔적
  - cgroup의 `memory.events`에서 `oom_kill`이 올랐다.
  - 호스트 커널 로그에 `Memory cgroup out of memory: Killed process <pid> (...)`(mm/oom_kill.c).
  - 쿠버네티스는 `reason: OOMKilled`로 표시한다.
- `docker stop`·파드 종료의 흔적
  - 종료 직전에 SIGTERM이 먼저 왔고, 유예 시간(10초 등)이 지난 뒤 끝났다.
  - 종료를 요청한 이벤트(배포·스케일 다운·`docker stop` 기록)가 있다.
- 둘 다 아니면 다른 주체(헬스 체크 실패 후 재시작 등)를 찾는다.
