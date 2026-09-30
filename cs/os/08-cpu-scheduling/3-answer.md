# os/08-cpu-scheduling — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. FIFO vs SJF 반환 시간

```text
  FIFO  |A(100)|B(10)|C(10)|   완료 100, 110, 120  -> 평균 110초
  SJF   |B(10)|C(10)|A(100)|   완료 10, 20, 120    -> 평균 50초
```

- 긴 작업 뒤에 짧은 작업이 줄 서서 평균이 나빠지는 현상을 **호위 효과(convoy effect)**라 부른다(OSTEP 7).
- SJF는 모두 동시에 도착할 때 평균 반환 시간이 최소다. 실행 시간을 미리 알아야 한다는 가정이 약점이다.

### 2. SJF vs RR 응답 시간

- SJF: A, B, C가 0, 5, 10초에 처음 실행 → 평균 응답 (0+5+10)/3 = **5초**.
- RR(1초): A, B, C가 0, 1, 2초에 처음 실행 → 평균 응답 (0+1+2)/3 = **1초**(OSTEP 7).
- 희생: **반환 시간**. 스위칭 비용을 빼면 SJF는 5·10·15초에, RR은 13·14·15초에 끝난다. 평균 반환이 10초 → 14초로 나빠진다(마지막 C는 같다). 슬라이스가 짧을수록 스위칭 비용 비율도 커진다(슬라이스 10 ms, 스위치 1 ms면 약 10%).

### 3. MLFQ

```text
  Q_high [ ... ]  <- 새 작업 시작
  Q_mid  [ ... ]  <- 할당량 소진 시 강등
  Q_low  [ ... ]
         주기 S마다 전부 Q_high로
```

1. 우선순위 높은 큐가 먼저.
2. 같은 큐는 RR.
3. 새 작업은 최상위 큐.
4. 한 단계에서 할당량을 다 쓰면(몇 번 나눠 썼든) 강등.
5. 주기 S마다 모두 최상위로 부스트.

- 규칙 4는 **게임**을 막는다. 할당량 직전에 I/O를 내서 높은 큐에 머무는 꼼수가 통하지 않는다.
- 규칙 5는 **기아**를 막고, CPU 위주였다가 대화형으로 바뀐 작업을 다시 우대한다(OSTEP 8).

### 4. nice 0 vs nice 5

- nice 0 몫 = 1024 / (1024 + 335) ≈ **75.3%**, nice 5 몫 ≈ **24.7%**.
- 로컬 재현(예시, 리눅스 7.0): `%CPU` 75.3 / 24.4.
- nice 한 단계 ≈ CPU 몫 **10%** 차이. 인접 가중치 비율이 약 1.25다(kernel/sched/core.c 주석 "10% effect").

### 5. CFS와 EEVDF

```text
                 [vruntime 50]
                /             \
        [vruntime 20]      [vruntime 80]
        /
  [vruntime 10]  <- 가장 왼쪽 = 가장 적게 돈 task -> 선택 (CFS)
```

- CFS: 실행 가능 task를 `vruntime` 순서 레드블랙 트리에 두고 **가장 왼쪽**을 고른다. 돈 만큼 `vruntime`이 늘어 오른쪽으로 간다. 가중치가 크면 `vruntime`이 천천히 는다(sched-design-CFS.rst).
- EEVDF(6.6+): 몫보다 덜 받은(lag ≥ 0, **eligible**) task 중 **가상 데드라인이 가장 이른** task를 고른다(sched-eevdf.rst).
- EEVDF 트리는 리눅스 6.8부터 **데드라인 순으로 정렬**하고, 노드마다 서브트리 최소 `vruntime`을 함께 저장해 자격 없는 가지를 잘라낸다. O(log n)이다(kernel/sched/fair.c `pick_eevdf` 주석). 6.6·6.7은 `vruntime` 순 정렬 + 최소 `deadline` 저장이었다.

### 6. SCHED_FIFO vs SCHED_OTHER

- 실시간 정책(정적 우선순위 1~99)은 일반 정책(정적 우선순위 0)보다 원칙적으로 먼저다. FIFO task가 준비되면 일반 task를 선점한다(sched(7)). 예외는 아래 5% 보호 장치다.
- FIFO task는 블록되거나, 더 높은 우선순위에 선점되거나, `sched_yield`할 때까지 계속 돈다.
- 무한 루프여도 기본 설정에서는 일반 task가 **완전히 0은 아니다**. 1초 중 약 5%(50 ms)가 일반 task에 남는다.
  - sched(7)의 설명: 실시간·데드라인 task는 1초(`sched_rt_period_us`) 중 0.95초(`sched_rt_runtime_us`)까지만 쓴다.
  - 리눅스 6.12+ 커널 소스: CPU마다 fair 데드라인 서버가 일반 task에 1초당 50 ms를 보장한다(kernel/sched/deadline.c `sched_init_dl_servers`).
- 그래도 5%로는 서버가 사실상 멈춘 것과 같다. 일반 서비스에 실시간 정책을 쓰지 않는다.

### 7. CPU별 큐

- 장점: 공용 큐 하나에 몰리던 락 경합이 크게 준다(이주·부하 균형 때는 두 CPU의 큐를 함께 잠근다 — kernel/sched/sched.h `double_rq_lock()`), task가 같은 CPU에 머물러 **캐시 친화도**가 좋다.
- 문제: 큐 사이 **부하 불균형**. 한 CPU는 쉬고 다른 CPU는 밀린다.
- 해법: task **이주(migration)**와 **작업 훔치기(work stealing)** — 한가한 큐가 바쁜 큐를 들여다보고 task를 가져온다(OSTEP 10).

### 8. 평균 40%인데 p99 100 ms 주기 스파이크

- 의심: **cgroup CPU quota throttling**. 멀티스레드가 period(기본 100 ms) 초반에 quota를 다 쓰고, 나머지 동안 그룹 전체가 멈춘다(sched-bwc.rst).
- 확인: `/sys/fs/cgroup/<그룹>/cpu.stat`의 `nr_throttled`(`nr_periods` 대비 비율)와 `throttled_usec` 증가. `cpu.max`로 quota/period를 본다.
- 대처
  1. 병렬도를 limit에 맞춘다: JVM `-XX:ActiveProcessorCount`, GC 스레드 수, 풀 크기.
  2. limit을 늘리거나, 지연 민감 서비스는 limit 없이 request(가중치)만 두는 정책을 검토한다.
  3. `cpu.max.burst`로 짧은 초과를 허용한다(기본 0).

### 9. nice 19가 효과 없을 때

- 이유 1: 두 프로세스가 **다른 autogroup·cgroup**에 있다. CPU는 그룹끼리 먼저 나누고 nice는 그룹 안에서만 비교된다(sched(7)).
- 이유 2: CPU가 **경쟁 상태가 아니다**. nice는 경쟁할 때의 몫일 뿐이다. 지연 원인이 메모리 대역폭·캐시·I/O일 수 있다.
- 확인: `cat /proc/pressure/cpu`의 `some`이 의미 있게 높은지, `vmstat 1`의 `r`이 코어 수를 넘는지 본다. 둘 다 낮으면 CPU 스케줄링 문제일 가능성이 낮다. 다만 전체 평균이라 특정 cgroup의 throttling(`cpu.stat`·`cpu.pressure`), 허용 CPU 제한(`taskset`), 짧은 스파이크는 가릴 수 있으니 따로 본다(psi.rst).
- 대처: 그룹 단위 몫은 cgroup `cpu.weight`로 정한다.

### 10. 평균 10%, 처리량 정체

- 스케줄러로 해결할 수 없다. 한 스레드가 한 코어를 100% 쓰는 **직렬 병목**일 가능성이 크다. 16코어 중 한 코어가 100%면 평균은 약 6%다.
- 확인: `mpstat -P ALL 1`(코어별), `ps -eLo pid,tid,psr,pcpu,comm --sort=-pcpu | head`(스레드별).
- 대처: 작업을 여러 스레드·프로세스로 나눈다(Node `cluster`, 다중 리액터, 락 범위 축소).
