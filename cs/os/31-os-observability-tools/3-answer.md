# os/31-os-observability-tools — 정답

## 정답

### 1. load average의 정체

- **R 상태(실행 중 + 실행 대기) 수 + D 상태(중단 불가 대기) 수**를 5초마다 표본으로 잡아 1·5·15분 지수 감쇠 평균을 낸 값이다(proc_loadavg(5), kernel/sched/loadavg.c).

```text
  8코어, load 20
  CPU 부족:  R R R R R R R R | R R R R R R R R R R R R      <- 8개 실행, 12개 줄 섬. CPU 100%
  CPU 아님:  R R | D D D D D D D D D D D D D D D D D D      <- 2개 실행, 18개가 I/O·락 대기. CPU 25% 남짓
```

- 리눅스 load는 "CPU 부하"가 아니라 "시스템 부하"다(Gregg).

### 2. CPU 한가한데 load 30

- D 상태 태스크가 많을 가능성이 크다. 디스크 I/O 대기, NFS 응답 대기, 중단 불가 락 대기 등이다.
- 확인
  - `ps -eLo stat,pid,tid,wchan:25,comm | awk '$1 ~ /^D/'` — D 스레드와 대기 지점(wchan).
  - `iostat -xz 1` — await·aqu-sz가 큰 장치.
  - `cat /proc/pressure/io` — I/O 때문에 멈춘 시간 비율.
- 진짜 원인(느린 디스크, NFS 서버, 파일시스템 락)을 찾아야 한다. CPU를 늘려도 안 줄어든다.

### 3. `b`=0인데 D가 있다

- `vmstat`의 `b`는 `/proc/stat`의 `procs_blocked`다. 커널은 이 값을 `nr_iowait()`로 낸다(fs/proc/stat.c). **I/O 완료를 기다리는** 태스크만 센다.
- D 상태에는 I/O가 아닌 대기도 있다. 작성 환경에서 `vfork` 부모 4개가 `D kernel_clone`이었는데 `b`는 0이었다(로컬 재현).
- load average는 D를 I/O 여부와 상관없이 센다(`TASK_NOLOAD`·얼어 있는 태스크만 빠진다, kernel/sched/core.c). 그래서 load에는 보이고 `b`에는 안 보이는 D가 있을 수 있다.

### 4. 첫 줄의 함정

- `vmstat`의 첫 보고는 **부팅 이후 평균**이다(vmstat(8)). 방금 생긴 I/O 대기는 몇 주 치 평균에 묻힌다. procs·메모리 칸만 순간값이다.
- `iostat`도 첫 보고는 부팅 이후 통계다. `-y`로 첫 보고를 생략할 수 있다(iostat(1)).
- `vmstat 1 5`처럼 여러 번 찍고 둘째 줄부터 본다.

### 5. USE

- **Utilization(사용률)**: 자원이 일을 처리하느라 바빴던 평균 시간.
- **Saturation(포화)**: 처리하지 못한 일이 쌓인 정도. 대개 대기열.
- **Errors(에러)**: 에러 이벤트 수.
- 포화 지표 예
  - CPU: `vmstat`의 `r`이 CPU 수보다 계속 큼, PSI cpu의 `some`(시스템 수준 cpu `full`은 5.13+에서 늘 0).
  - 메모리: 스왑 입출력(`si`·`so`), 익명 페이지 스왑, PSI memory.
  - 디스크: `iostat`의 `aqu-sz`·`await` 증가, PSI io.
- 사용률 100%만으로는 느리지 않을 수 있다. 일이 **줄을 서기 시작해야** 기다림(지연)이 생긴다. 포화는 그 줄을 직접 잰다.

### 6. `%util` 100%

- 결론 내리면 안 된다. `%util`은 "요청이 하나라도 처리 중이던 시간 비율"이다.
- 직렬로 처리하는 장치에서는 100%가 포화다. RAID·최신 SSD처럼 병렬로 처리하는 장치에서는 100%여도 한계가 아니다(iostat(1)).
- 더 볼 것: `await`(요청당 시간)가 오르는지, `aqu-sz`(평균 큐 길이)가 커지는지, 실제 IOPS·처리량이 장치 사양에 가까운지.

### 7. `strace`의 비용

- ptrace 방식이라 시스템 콜마다 대상을 멈추고 strace 프로세스로 문맥 교환한다. 시스템 콜이 많은 서버일수록 크게 느려져 타임아웃이 날 수 있다.
  - 작성 환경의 극단 예: `dd bs=1 count=200000`이 약 0.07초 → strace 아래 약 8초(로컬 재현).
- 쓸 때: 짧게 붙였다 뗀다. `-e trace=`·`-c`는 출력만 줄이고 시스템 콜마다의 정지는 그대로다. 정지를 줄이는 `--seccomp-bpf`는 `-f`와 함께 새로 띄운 프로세스에만 되고 `-p` 부착에는 안 된다(strace(1)).
- `perf`는 샘플링이다. 일정 간격으로 인터럽트가 걸려 그 순간의 위치(스택)만 링 버퍼에 기록한다. 대상을 시스템 콜마다 멈추지 않으니 비용이 샘플 빈도에 비례한다. 대신 권한(`perf_event_paranoid`)이 필요하다.

### 8. 컨테이너 안 `top`

- `top`이 읽는 `/proc/stat`·`/proc/loadavg`는 namespace로 가상화되지 않는 **호스트 전체** 값이다. load 계산도 커널 전역 변수다(kernel/sched/loadavg.c).
- 그래서 호스트가 한가하면 컨테이너 안 `top`도 한가해 보인다. 그 사이 컨테이너는 자기 cgroup 한도(`cpu.max`)에 걸려 throttling될 수 있다.
- 볼 것: 컨테이너 cgroup의 `cpu.stat`(`nr_throttled`, `throttled_usec`), `cpu.pressure`, `memory.events`(28번).

### 9. JVM 뜨거운 스레드 찾기

1. `top` 또는 `pidstat 1`로 CPU를 쓰는 **프로세스**(pid)를 찾는다.
2. `top -H -p <pid>`(또는 `pidstat -t -p <pid> 1`)로 CPU를 쓰는 **스레드 ID(TID)**를 찾는다.
3. JDK 17 이하라면 `printf '%x\n' <tid>`로 16진수로 바꾼다. JDK 18부터는 `nid`가 10진수라 바꾸지 않는다(JDK-8268425).
4. `jstack <pid>`의 스레드 덤프에서 `nid=`가 그 값인 스레드를 찾는다. 스택을 몇 번 떠서 같은 곳에 있는지 본다. (nid 표기는 HotSpot 구현이다.)
5. GC 스레드라면 메모리 쪽(힙·할당률)을, 애플리케이션 스레드라면 그 코드 경로를 본다.
