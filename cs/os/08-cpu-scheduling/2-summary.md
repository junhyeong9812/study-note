# os/08-cpu-scheduling — 다음에 누구를 돌릴까: FIFO에서 CFS·EEVDF, 그리고 CPU quota까지 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

기초는 원고 [foundations/process-thread](../../foundations/process-thread/README.md) §3(선점형·비선점형)·§4(우선순위·RR·FCFS·SJF)에 있다.\
요약: 실행 가능한 task가 CPU보다 많으면 누군가는 기다려야 한다. 그 순서를 정하는 것이 스케줄링이다.

이 노트는 세 가지를 더한다.
- 무엇을 좋게 만들려는지(지표)에 따라 정답이 달라진다.
- 리눅스는 실제로 무엇을 쓰나(CFS → 6.6부터 EEVDF, 실시간 정책, 멀티코어).
- 컨테이너 CPU 제한이 만드는 새 장애(throttling).

쉬운 예: 은행 창구 하나에 손님 셋이다.
- 30분짜리 대출 상담 손님이 먼저 오면, 1분짜리 입금 손님 둘은 30분을 기다린다.
- 짧은 일을 먼저 하면 평균 대기가 확 준다.
- 하지만 짧은 일만 계속 오면 대출 상담 손님은 영영 차례가 오지 않는다(기아).

똑같은 구조다.\
스케줄러는 평균 대기, 응답성, 공정성 사이에서 무엇을 우선할지 고른다.

실무 예:
- 배치 작업이 웹 서버와 같은 노드에서 돌며 요청 지연이 늘어난다. `nice`로 배치를 낮췄는데도 효과가 작다.
- 쿠버네티스 CPU limit을 건 파드에서 평균 CPU는 40%인데 p99 지연이 100 ms씩 튄다.

## 동작·원리

### 지표 — 무엇을 줄이려 하나

```text
  도착 ----대기----> 첫 실행 ------실행·대기 반복------> 완료
  |<-- 응답 시간 --->|
  |<--------------------- 반환 시간(turnaround) ----------->|
```

  - *반환 시간(turnaround time)*: 완료 시각 − 도착 시각. 배치 작업에 중요하다.
  - *응답 시간(response time)*: 처음 실행된 시각 − 도착 시각. 대화형 작업에 중요하다(OSTEP 7).

### 고전 알고리즘 — 한 예로 비교

OSTEP 7장의 예다. A(100초)·B(10초)·C(10초)가 0초에 거의 동시에 도착한다.

```text
  FIFO  |A..........................................|B....|C....|
        0                                          100   110   120   평균 반환 = (100+110+120)/3 = 110
  SJF   |B....|C....|A..........................................|
        0     10    20                                         120   평균 반환 = (10+20+120)/3 = 50
```

- **FIFO**: 먼저 온 순서. 긴 작업 뒤에 짧은 작업이 줄 서면 평균이 나빠진다. 이것을 호위 효과(convoy effect)라 부른다.
- **SJF**: 짧은 작업 먼저. 모두 동시에 도착하면 평균 반환 시간이 최소다. 실행 시간을 미리 알아야 한다는 가정이 비현실적이다.
- **STCF(SRTF)**: 새 작업이 오면 남은 시간이 가장 짧은 작업으로 **선점**한다. A가 0초에, B·C가 10초에 오면 FIFO·SJF는 평균 반환 103.33초지만 STCF는 50초다(OSTEP 7: ((120−0) + (20−10) + (30−10))/3).
- **RR**: 타임 슬라이스마다 돌아가며 실행한다. 응답 시간이 좋다.

RR의 응답 시간 예(OSTEP 7): 5초짜리 작업 셋, 슬라이스 1초.

```text
  SJF  |A....|B....|C....|     응답 시간 평균 = (0+5+10)/3 = 5
  RR   |A|B|C|A|B|C|...        응답 시간 평균 = (0+1+2)/3 = 1   (대신 반환 시간은 나빠진다)
```

- 슬라이스가 짧을수록 응답이 좋다. 대신 스위칭 비용 비율이 커진다. 슬라이스 10 ms, 스위치 1 ms면 약 10%가 스위칭에 쓰인다(OSTEP 7 "amortization" 예시).

### MLFQ — 실행 시간을 몰라도 짧은 작업을 우대하기

```text
  Q_high  [ 대화형 task들 ]    <- 새 작업은 여기서 시작 (규칙 3)
  Q_mid   [ ... ]              <- 할당량을 다 쓰면 한 단계 내려감 (규칙 4)
  Q_low   [ CPU 위주 task들 ]
           주기 S마다 모두 Q_high로 끌어올림 (규칙 5, priority boost)
```

OSTEP 8장의 규칙이다.
1. 우선순위가 높은 큐의 작업이 먼저 돈다.
2. 같은 큐 안에서는 RR로 돈다.
3. 새 작업은 가장 높은 큐에서 시작한다.
4. 한 단계에서 할당량을 다 쓰면(몇 번 나눠 썼든) 한 단계 내려간다.
5. 주기 S마다 모든 작업을 가장 높은 큐로 올린다.

- 규칙 4의 "몇 번 나눠 썼든"은 **게임 방지**다. 할당량 직전에 I/O를 내며 높은 큐에 머무는 꼼수를 막는다.
- 규칙 5는 **기아 방지**다. 낮은 큐의 작업도 주기마다 기회를 얻는다.

### 비례 배분 — CFS와 EEVDF

리눅스의 일반 task(`SCHED_OTHER`)는 기본 fair 클래스에서 우선순위 큐 여러 개가 아니라 **CPU 시간을 가중치대로 나누는** 방식을 쓴다. (6.12+에서 `sched_ext` BPF 스케줄러를 올리면 일반 정책 task도 그쪽이 처리할 수 있다 — Documentation/scheduler/sched-ext.rst)

```text
  가중치(nice → weight, kernel/sched/core.c sched_prio_to_weight)
  nice -5: 3121   nice 0: 1024   nice 1: 820   nice 5: 335   nice 19: 15

  vruntime 증가 속도 ∝ 1 / weight   (가중치가 크면 가상 시간이 천천히 간다 -> 더 자주 뽑힌다)
```

- nice 한 단계는 CPU 몫 약 10% 차이다. 인접 단계 가중치 비율이 약 1.25다(kernel/sched/core.c 주석 "10% effect").
- 로컬 재현(예시, 리눅스 7.0): CPU 하나에 고정한 무한 루프 둘을 nice 0과 nice 5로 돌렸다. `%CPU`가 75.3 / 24.4였다. 가중치 계산 1024/(1024+335) = 75.3%와 맞는다.

**CFS(리눅스 2.6.23 ~)**
- 각 task의 가상 실행 시간(`vruntime`)을 나노초로 센다.
- 실행 가능한 task를 `vruntime` 순서의 레드블랙 트리에 넣고, **가장 왼쪽(가장 적게 돈) task**를 고른다(Documentation/scheduler/sched-design-CFS.rst).
- 돌린 시간만큼 `vruntime`이 늘어 오른쪽으로 밀려난다. 결국 모두가 차례로 가장 왼쪽이 된다.

**EEVDF(리눅스 6.6 ~)**
- 커널은 6.6부터 CFS를 EEVDF(Earliest Eligible Virtual Deadline First)로 바꿨다(Documentation/scheduler/sched-eevdf.rst). 작성 환경 커널 7.0도 EEVDF다.
- 두 기준으로 고른다(kernel/sched/fair.c 주석).
  1. **자격(eligible)**: 받을 몫보다 덜 받은 task(lag ≥ 0)만 후보다.
  2. 후보 중 **가상 데드라인이 가장 이른** task를 고른다.
- 가상 데드라인은 대략 "지금 가상 시간 + 요청한 슬라이스/가중치"다. 슬라이스를 짧게 요청한 task는 데드라인이 일러 먼저 뽑힌다. 리눅스 6.12부터 `sched_setattr()`의 `sched_runtime`으로 슬라이스를 요청할 수 있다(sched-eevdf.rst, v6.12 kernel/sched/syscalls.c `custom_slice`).
- 트리는 여전히 레드블랙 트리다. 리눅스 6.8부터는 **데드라인 순으로 정렬**하고, 각 노드가 서브트리의 최소 `vruntime`을 함께 들고 있어 자격 없는 가지를 잘라낸다(fair.c "augmented RB-tree … sorted on deadline, but also functions as a heap based on the vruntime"). 선택은 O(log n)이다.
  - 6.6·6.7은 반대였다: `vruntime` 순 정렬 + 서브트리 최소 `deadline`(v6.7 fair.c `entity_before()`·`min_deadline`).
- 기본 슬라이스의 기준값은 0.7 ms다(kernel/sched/fair.c `normalized_sysctl_sched_base_slice = 700000ULL`). 실제 값은 CPU 수로 늘린다. 기본 스케일링(`SCHED_TUNABLESCALING_LOG`)의 배수는 `1 + ilog2(min(온라인 CPU 수, 8))`이다(fair.c `get_update_sysctl_factor()`). 그래서 CPU 8개 이상이면 0.7 × 4 = 2.8 ms다.

> 참고: 원고 §4는 우선순위·RR·FCFS·SJF를 소개한다. 리눅스 일반 task는 이 중 어느 것도 그대로 쓰지 않는다. 가중치 비례 배분(CFS → EEVDF)이다. 고정 우선순위 + FIFO/RR은 아래 실시간 정책에서만 쓴다(sched(7)).

### 리눅스 정책의 층 — 실시간이 먼저

```text
  높음  SCHED_DEADLINE        사용자가 줄 수 있는 가장 높은 우선순위 (sched(7))
        SCHED_FIFO / SCHED_RR  정적 우선순위 1~99. 준비되면 보통 일반 task를 곧바로 선점
  낮음  SCHED_OTHER / BATCH / IDLE   정적 우선순위 0. 가중치로 나눔 (EEVDF). OTHER·BATCH는 nice로 가중치, IDLE은 nice 무관 고정 최소 가중치
```

- 실시간 task는 원칙적으로 일반 task보다 먼저다. 예외는 바로 아래의 보호 장치다(그 몫만큼은 일반 task가 먼저 돌 수 있다). `SCHED_FIFO` task는 블록되거나, 더 높은 우선순위에 선점되거나, `sched_yield`할 때까지 계속 돈다(sched(7)).
- 폭주한 실시간 task가 일반 task를 굶기지 않게 하는 장치가 있다. 커널 버전에 따라 방식이 다르다.
  - sched(7)(man-pages 6.7)의 설명(리눅스 6.11까지의 기본 동작): 1초(`sched_rt_period_us` 1,000,000) 중 0.95초(`sched_rt_runtime_us` 950,000)만 실시간·데드라인 task에 주고, 0.05초를 일반 task에 남긴다.
  - 현재 커널 소스: CPU마다 일반 task용 **fair 데드라인 서버**를 두고 1초당 50 ms를 보장한다(kernel/sched/deadline.c `sched_init_dl_servers`: runtime 50 ms, period 1000 ms). `CONFIG_RT_GROUP_SCHED`가 없으면 `sched_rt_runtime_us`는 데드라인 task 승인 제어에만 쓰인다(Documentation/scheduler/sched-rt-group.rst). 이 방식은 리눅스 6.12부터다(v6.11 `kernel/sched/rt.c`에는 `def_rt_bandwidth` 스로틀이 있고 `fair_server`가 없다. v6.12 `fair.c`부터 `fair_server`가 있다).
  - 어느 쪽이든 "1초 중 약 5%는 일반 task 몫"이다.

### 멀티코어 — CPU마다 큐, 그리고 이주

```text
  단일 큐(SQMS)                     CPU별 큐(MQMS) — 리눅스 방식
  [ A B C D E ] <- 모든 CPU가 락 경쟁   CPU0 [A C]   CPU1 [B D]   CPU2 [E]
                                        \_________ 부하 균형: 과부하 큐에서 이주 _________/
```

- 단일 큐는 락 경합이 있고, task가 CPU를 옮겨 다녀 캐시를 잃는다(OSTEP 10).
- CPU별 큐는 캐시 친화도(cache affinity)가 좋다. 대신 큐 사이 불균형이 생긴다. 그래서 task를 옮기는 **이주(migration)**가 필요하다. 한 방법이 한가한 큐가 바쁜 큐에서 가져오는 **작업 훔치기(work stealing)**다(OSTEP 10).
- `taskset`·`sched_setaffinity(2)`로 task가 돌 CPU를 제한할 수 있다.

### cgroup CPU 대역폭 — quota와 throttling

```text
  cpu.max = "100000 100000"  (period 100 ms 동안 100 ms = CPU 1개 분량)
  스레드 4개가 동시에 CPU를 씀 (예시)

  시간(ms)  0        25                                   100       125 ...
  CPU 사용  |████████|                                     |████████|
  (4코어)   |████████|        throttled: 아무것도 못 돔      |████████|
            |████████|        (이 사이 도착한 요청은 대기)   |████████|
            |████████|                                     |████████|
            quota 100 ms 소진 ^                    다음 period에 재충전 ^
```

- 그룹은 period마다 quota만큼 CPU 시간을 쓸 수 있다. 다 쓰면 다음 period까지 **throttle**되어 아무 스레드도 돌지 못한다(Documentation/scheduler/sched-bwc.rst).
- cgroup v2 파일은 `cpu.max`(`$MAX $PERIOD`, 기본 `max 100000` = 제한 없음)이고, 일반(fair) 클래스 task에 적용된다. 최신 문서는 `cgroup_set_bandwidth` 콜백을 구현한 BPF 스케줄러(sched_ext)도 적용 대상으로 적는다(cgroup-v2 문서).
- 위 예시에서 quota는 25 ms 만에 바닥났다. 나머지 75 ms 동안 그룹 전체가 멈춘다. 1분 평균 CPU 사용률은 낮게 보여도 요청 하나는 최대 75 ms를 더 기다린다.
- `cpu.stat`의 `nr_periods`·`nr_throttled`·`throttled_usec`로 확인한다. 이 값은 cpu 컨트롤러가 켜진 그룹에만 나온다(cgroup-v2 문서).
- 쿠버네티스 CPU limit은 cgroup을 통한 커널의 CPU throttling으로 강제된다. CPU request는 경합 시의 가중치다(k8s 문서 "Resource Management for Pods and Containers").
  - cgroup v2 노드에서 limit이 정확히 `cpu.max`의 어떤 값으로 적히는지는 런타임 문서로 확인하지 못했다 [?].

## 쓰이는 자료구조·알고리즘

- **최소 힙(우선순위 큐)** — SJF·STCF는 "남은 시간이 가장 짧은 작업"을 반복해서 꺼낸다. [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)
- **다중 FIFO 큐** — MLFQ는 우선순위별 큐 여러 개와 강등·승격 규칙이다. 리눅스 실시간 정책도 우선순위(1~99)별 대기 목록이다(sched(7)). [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **레드블랙 트리** — CFS는 `vruntime` 순, EEVDF(6.8+)는 데드라인 순으로 정렬한 레드블랙 트리를 쓴다. 가장 왼쪽 노드는 캐시해 둔다(`rb_root_cached`). [data-structure/16-red-black-tree](../../data-structure/16-red-black-tree/2-summary.md)
- **증강 트리(augmented tree)** — EEVDF 트리(6.8+)의 각 노드는 서브트리의 최소 `vruntime`을 함께 저장한다. 그래서 "자격 있는 task 중 데드라인 최소"를 한 번 내려가며 찾는다. 구간 트리와 같은 발상이다. [data-structure/30-interval-tree](../../data-structure/30-interval-tree/2-summary.md)
- **토큰 버킷과 닮은 quota** — `cpu.max`는 period마다 채워지는 CPU 시간 예산이다. 레이트 리미터와 같은 구조다. [ops-patterns/04-rate-limiter](../../ops-patterns/04-rate-limiter/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 우선순위 조정 — nice, 정책, 친화도

```bash
nice -n 10 ./batch-job              # 새로 띄울 때 현재 nice에 +10 (셸이 0이면 10)
renice -n 10 -p <pid>               # 실행 중인 프로세스
chrt -b 0 ./batch-job               # SCHED_BATCH: 깨어날 때 조금 불리하게 (sched(7))
chrt -i 0 ./housekeeping            # SCHED_IDLE: nice 19보다도 약함
taskset -c 0-3 ./app                # CPU 0~3에서만 실행
chrt -m                             # 정책별 우선순위 범위
```

- **autogroup 주의**: `sched_autogroup_enabled`가 1이고(이 환경 1) 프로세스가 루트 CPU cgroup에 있으면 터미널 세션마다 그룹이 생기고, CPU는 먼저 그룹끼리 나눈다. 그래서 다른 세션의 프로세스와는 nice 값이 직접 비교되지 않는다(sched(7) "The autogroup feature", "The nice value and group scheduling"). 루트가 아닌 CPU cgroup에 넣으면 autogroup은 무시되고, 같은 cgroup 안이면 세션이 달라도 nice가 비교된다(sched(7)).
- 실시간 정책(`chrt -f`)은 권한이 필요하고, 폭주하면 일반 task를 굶긴다. 일반 서버에는 쓰지 않는다.

### 2. 컨테이너 CPU — 제한과 런타임의 시각을 맞춘다

```bash
cat /sys/fs/cgroup/<그룹>/cpu.max       # 예: "200000 100000" = CPU 2개 분량
cat /sys/fs/cgroup/<그룹>/cpu.stat      # nr_periods / nr_throttled / throttled_usec
cat /sys/fs/cgroup/<그룹>/cpu.pressure  # 그룹 단위 CPU 대기 압력
```

- JVM(HotSpot)은 cgroup CPU quota를 읽어 사용 가능 CPU 수를 정한다(`UseContainerSupport`, 기본 켜짐). GC·JIT 스레드 수도 이 값을 따른다. 필요하면 `-XX:ActiveProcessorCount=N`으로 명시한다.
- Node는 이벤트 루프가 스레드 하나라 quota가 CPU 1개 이상이면 루프 혼자서는 소진하기 어렵다. quota가 1개 미만(예: `cpu.max = "50000 100000"`)이면 루프 하나로도 period마다 소진해 throttle된다. `UV_THREADPOOL_SIZE`나 `worker_threads`를 늘리면 순간 병렬도가 quota를 넘을 수 있다.

### 3. 진단 명령

```bash
# 실행 대기(run queue) 압력: some = 적어도 하나의 task가 CPU를 기다린 시간 비율
cat /proc/pressure/cpu
#   some avg10=1.60 avg60=1.64 avg300=3.39 total=13241976904     (예시, 리눅스 7.0)

# 코어별 사용률: 평균은 낮은데 한 코어만 100%인지
mpstat -P ALL 1

# 프로세스의 스케줄링 통계 (vruntime, 스위치 수, 정책·prio)
grep -E 'se.vruntime|nr_switches|nr_involuntary|policy|prio' /proc/<pid>/sched

# 실행 가능 task 수(r)와 시스템 전체 CPU 비율(코어별 분포는 위 mpstat)
vmstat 1

# 스레드별 CPU와 어느 CPU에서 도는지(PSR = 마지막으로 실행한 CPU, ps(1))
ps -eLo pid,tid,psr,ni,cls,pcpu,comm --sort=-pcpu | head
```

- `/proc/<pid>/sched`는 이 환경에서 일반 사용자로 읽을 수 있었다. 리눅스 6.14까지는 `CONFIG_SCHED_DEBUG`가 켜진 커널에만 있다. 6.15부터는 조건 없이 있다(fs/proc/base.c `REG("sched", …)` 주변의 `#ifdef CONFIG_SCHED_DEBUG`가 v6.15에서 사라짐).
- PSI의 `some`은 "적어도 일부 task가 자원을 기다린 시간 비율"이다(Documentation/accounting/psi.rst). 시스템 수준 CPU `full`은 정의되지 않아 0으로 보고한다(psi.rst).

## 장애 시나리오와 대처

### 1. 기아 — 낮은 우선순위가 끝나지 않는다

- **현상**: 백그라운드 정리 작업이나 로그 전송이 몇 시간째 진척이 없다. 또는 한 스레드가 폭주한 뒤 시스템 전체가 굳는다.
- **보이는 형태**
  - `ps -eLo …,cls,ni`에서 굶는 task가 `SCHED_IDLE`(IDL)이거나 높은 nice다.
  - 실시간 task(FF/RR) 폭주라면 일반 task가 거의 돌지 못한다. 보호 장치 덕에 1초 중 약 5%(50 ms)만 남는다(위 「리눅스 정책의 층」).
- **원인**
  - 엄격한 우선순위 스케줄링은 높은 쪽이 계속 준비 상태면 낮은 쪽을 굶긴다. MLFQ가 priority boost(규칙 5)를 두는 이유다.
  - 리눅스 일반 task끼리는 가중치 비례라 완전히 굶지는 않는다. 하지만 `SCHED_IDLE`·nice 19는 몫이 매우 작다(nice 19 가중치 15 vs nice 0 1024).
  - 실시간 정책은 선점이 절대적이라 폭주가 곧 기아다.
- **대처**
  - 일반 서버 작업에 실시간 정책을 쓰지 않는다.
  - 중요한 백그라운드 작업은 nice 대신 cgroup `cpu.weight`로 최소 몫을 준다.
  - 락을 쥔 낮은 우선순위 task가 굶어 높은 task까지 막히는 경우는 우선순위 역전이다(20번).

### 2. CPU quota throttling → 평균 CPU는 낮은데 p99 급등

- **현상**: 대시보드의 CPU 사용률은 limit의 40%인데, 응답 지연 p99가 주기적으로 100 ms 가까이 튄다.
- **보이는 형태**
  - `cpu.stat`의 `nr_throttled`가 `nr_periods`에 비해 크게 늘고, `throttled_usec`가 쌓인다.
  - 지연 스파이크가 period(기본 100 ms) 단위로 나타난다.
- **원인**
  - 멀티스레드 앱(GC 병렬 스레드, 요청 버스트)이 여러 코어를 동시에 써 quota를 period 초반에 소진한다. 남은 시간 동안 그룹 전체가 멈춘다(sched-bwc.rst).
  - 평균 사용률은 긴 창의 평균이라 짧은 소진을 숨긴다.
- **대처**
  - 병렬도를 quota에 맞춘다. JVM `-XX:ActiveProcessorCount`, GC 스레드 수, 풀 크기를 limit에 맞춘다.
  - limit을 늘리거나, 지연 민감 서비스는 CPU limit 대신 request(가중치)만 거는 정책을 검토한다.
  - `cpu.max.burst`로 짧은 초과를 허용한다(cgroup-v2 문서, 기본 0).

### 3. 한 코어만 100% — 평균에 숨은 병목

- **현상**: 16코어 서버의 CPU 평균은 10%인데 처리량이 더 늘지 않는다.
- **보이는 형태**: `mpstat -P ALL 1`에서 한 코어만 100%. `ps -eLo … pcpu`에서 특정 스레드 하나가 99%.
- **원인**: 단일 스레드 구조(이벤트 루프, 단일 accept 스레드, 전역 락 안의 작업)가 한 코어에 묶였다.
- **대처**: 작업을 여러 스레드·프로세스로 나눈다(Node `cluster`, 다중 리액터). 스케줄러가 해결할 수 있는 문제가 아니다.

### 4. `nice`를 줬는데 효과가 없다

- **현상**: 배치를 nice 19로 낮췄는데 웹 서버 지연이 그대로다.
- **보이는 형태**: `ps`의 NI 값은 19인데 배치의 `%CPU`가 여전히 높다.
- **원인**
  - 두 프로세스가 **다른 autogroup·cgroup**에 있다. CPU는 먼저 그룹끼리 나누고, nice는 그룹 안에서만 비교된다(sched(7)).
  - CPU가 남아 있으면 nice는 아무것도 빼앗지 않는다. nice는 경쟁할 때의 몫이다. 이때 지연 원인은 CPU가 아니라 캐시·메모리 대역폭·I/O일 수 있다.
- **대처**: cgroup `cpu.weight`로 그룹 단위 몫을 정한다. `/proc/pressure/cpu`로 CPU 대기가 실제로 있는지 먼저 확인한다.

## 핵심 문장

- 스케줄링의 정답은 지표에 달렸다. 반환 시간은 SJF·STCF, 응답 시간은 RR이 좋다.
- MLFQ는 실행 시간을 몰라도 관찰로 짧은 작업을 우대한다. 할당량 누적(게임 방지)과 주기적 부스트(기아 방지)가 핵심 규칙이다.
- 리눅스 일반 task는 가중치 비례 배분이다. CFS는 `vruntime`이 가장 작은 task를, 6.6+의 EEVDF는 자격 있는 task 중 가상 데드라인이 가장 이른 task를 레드블랙 트리에서 고른다.
- 실시간 정책은 원칙적으로 일반 task보다 먼저다. 기본 설정은 1초 중 약 5%(50 ms)를 일반 task 몫으로 남긴다.
- cgroup CPU quota는 period 안에서 소진되면 그룹 전체를 멈춘다. 평균 CPU가 낮아도 p99가 튄다. `cpu.stat`의 `nr_throttled`로 확인한다.

## 관련 주제·근거

- 선행: [07-threads-and-context-switch](../07-threads-and-context-switch/2-summary.md) — 스위칭 비용과 실행 큐.
- 후속·연결
  - [28-containers-namespaces-cgroups](../28-containers-namespaces-cgroups/2-summary.md) — cgroup `cpu.max`·`cpu.weight`.
  - [31-os-observability-tools](../31-os-observability-tools/2-summary.md) — PSI·USE 방법론.
  - [35-virtualization-hypervisor](../35-virtualization-hypervisor/2-summary.md) — steal time.
  - [20-concurrency-bugs](../20-concurrency-bugs/2-summary.md)(우선순위 역전·기아).
  - [ops-patterns/03-bulkhead](../../ops-patterns/03-bulkhead/2-summary.md) — 스레드 풀 격리와 병렬도 상한.
  - [reliability/README](../../reliability/README.md) — 꼬리 지연·골든 시그널.
- Kernel 문서·소스
  - Documentation/scheduler/sched-design-CFS.rst — vruntime, 시간순 rbtree, 가장 왼쪽 선택 <https://docs.kernel.org/scheduler/sched-design-CFS.html>
  - Documentation/scheduler/sched-eevdf.rst — 6.6부터 EEVDF, lag·eligible·virtual deadline, `sched_setattr` 슬라이스 <https://docs.kernel.org/scheduler/sched-eevdf.html>
  - kernel/sched/fair.c — `pick_eevdf()` 주석(augmented RB-tree, deadline 정렬 + min_vruntime), `entity_before()`(deadline 비교), `normalized_sysctl_sched_base_slice = 700000ULL`, `get_update_sysctl_factor()`(1 + ilog2(min(CPU, 8)))
  - kernel/sched/core.c — `sched_prio_to_weight[40]`, "10% effect"·1.25 배 주석
  - kernel/sched/deadline.c `sched_init_dl_servers()` — fair 서버 50 ms / 1000 ms(v6.12부터 `fair_server`) · fs/proc/base.c — `/proc/<pid>/sched`의 `CONFIG_SCHED_DEBUG` 조건(v6.14까지) · Documentation/scheduler/sched-rt-group.rst — `sched_rt_runtime_us`의 현재 의미, fair dl_server 몫 보존
  - Documentation/scheduler/sched-bwc.rst — quota·period, throttle, `nr_throttled` <https://docs.kernel.org/scheduler/sched-bwc.html>
  - Documentation/admin-guide/cgroup-v2.rst — `cpu.max`(기본 `max 100000`), `cpu.max.burst`, `cpu.stat`(nr_periods·nr_throttled·throttled_usec) <https://docs.kernel.org/admin-guide/cgroup-v2.html>
  - Documentation/accounting/psi.rst — `/proc/pressure/cpu` some/full <https://docs.kernel.org/accounting/psi.html>
- Documentation/scheduler/sched-ext.rst(v6.12+) — BPF 스케줄러가 켜지면 일반 정책 task도 처리(`SCX_OPS_SWITCH_PARTIAL` 제외) · nice(1) `-n` = 현재 nice에 더하는 증분
- Linux man-pages 6.7(로컬): sched(7) — SCHED_IDLE은 nice 무관, 비루트 CPU cgroup이 autogroup을 무시, 정책·정적 우선순위 1~99, SCHED_FIFO 동작, SCHED_DEADLINE 최상위, `sched_rt_period_us`·`sched_rt_runtime_us`, autogroup
- Kubernetes 문서 "Resource Management for Pods and Containers" — CPU limit = 커널 throttling, request = 가중치 <https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/>
- OpenJDK `src/hotspot/os/linux/globals_linux.hpp`(`UseContainerSupport`) · `cgroupSubsystem_linux.cpp`(quota/period로 CPU 수 계산)
- 교재: OSTEP 7 "Scheduling: Introduction"(FIFO 110초 → SJF 50초, RR 응답 1초 vs 5초), 8 "MLFQ"(규칙 1~5), 9 "Proportional Share"(9.7 CFS), 10 "Multiprocessor Scheduling"(SQMS·MQMS·migration·work stealing)
- 로컬 재현(리눅스 7.0): 같은 CPU의 nice 0 vs nice 5 → 75.3% / 24.4%, `/proc/<pid>/sched`·`/proc/pressure/cpu`·`chrt -m` 출력, 세션 cgroup의 `cpu.max`(`user.slice`는 `max 100000`)
