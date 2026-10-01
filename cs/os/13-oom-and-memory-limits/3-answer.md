# os/13-oom-and-memory-limits — 정답

## 정답

### 1. malloc 성공 뒤의 OOM kill

- `malloc(1GB)`는 **가상 주소**를 약속할 뿐이다. 물리 페이지는 처음 건드릴 때 페이지 폴트로 붙는다.
- 기본 모드(0)는 뻔한 초과만 거절하므로, 여러 프로세스의 약속 합(`Committed_AS`)이 실제 RAM + 스왑보다 커질 수 있다.
- 모두가 약속을 실제로 쓰려 하면 물리 메모리가 모자란다. 이미 성공한 `malloc`을 실패로 되돌릴 방법이 없다. 커널은 회수(캐시 버리기, 스왑)를 해 보고, 안 되면 OOM killer로 프로세스를 죽여 메모리를 만든다(malloc(3) NOTES).

### 2. overcommit 모드

| 값 | 거절하는 것 |
|---|---|
| 0 | 뻔한 초과. 현재 커널 코드에서는 한 번의 요청이 RAM + 스왑 총량보다 클 때(mm/util.c) |
| 1 | 거절하지 않는다 |
| 2 | 약속 총량이 `CommitLimit`을 넘게 하는 요청 |

- `CommitLimit = (RAM - 거대 페이지) × overcommit_ratio / 100 + 스왑`(proc_sys_vm(5)).
- 계산: 38.7 × 0.5 + 8.4 = 19.35 + 8.4 ≈ **27.7GB**. 작성 환경의 `/proc/meminfo` 값 27729884 kB와 맞는다(예시, 리눅스 7.0).

### 3. ENOMEM vs SIGKILL

- 할당 시점 `ENOMEM`
  - `ulimit -v`(RLIMIT_AS)를 넘는 요청 — 로컬 재현: 1GiB 한도에서 `malloc(2GiB)` → NULL, `Cannot allocate memory`.
  - 모드 2에서 `CommitLimit` 초과, 또는 모드 0에서 RAM + 스왑보다 큰 단일 요청.
- 사용 중 SIGKILL
  - 전체 시스템 메모리가 바닥나 OOM killer가 나를 골랐다.
  - 내가 속한 cgroup이 `memory.max`에 닿아 그 cgroup 안에서 OOM killer가 나를 골랐다.

### 4. 희생자 선택

```text
  회수 실패 → 후보 집합 (전체 OOM: 모든 프로세스 / cgroup OOM: 그 cgroup 안)
     → 각 후보 점수 = RSS + 스왑 엔트리 + 페이지 테이블 페이지
                    + oom_score_adj × (허용 메모리 페이지 / 1000)
     → 최댓값 프로세스에 SIGKILL, 커널 로그 "Killed process ..."
```

- 기본 점수는 메모리 사용량이다(mm/oom_kill.c `oom_badness`).
- `oom_score_adj`는 허용 메모리의 천분율 단위로 더해진다. +500은 대략 허용 메모리의 50%를 더 쓴 것처럼 친다(proc_pid_oom_score_adj(5)).
- -1000(`OOM_SCORE_ADJ_MIN`)이면 후보에서 빠진다(`oom_badness`가 `LONG_MIN`을 돌려준다). OOM killer의 희생자가 되지 않는다. `memory.oom.group`의 그룹 kill에서도 예외다(kernel.org cgroup-v2). 다른 경로의 SIGKILL까지 막는 것은 아니다.

### 5. `oom_score` 계산

- `fs/proc/base.c`의 `proc_oom_score`: `oom_score = (1000 + badness × 1000 / (RAM + 스왑)) × 2 / 3`.
- 메모리 사용이 거의 0이면 badness ≈ 100 × (총량/1000)이고, 1000분율로 바꾸면 100이다.
- (1000 + 100) × 2 / 3 ≈ **733**. 작성 환경 셸에서 실제로 733이었다(예시, 리눅스 7.0).
- 참고: man은 "root는 3% 보너스"를 적지만 현재 소스의 `oom_badness`에는 없다.

### 6. `memory.high` vs `memory.max`

- `memory.high`를 넘으면: 그 cgroup의 프로세스가 스로틀되고 강한 회수를 받는다. **OOM killer는 부르지 않는다.** 극단적인 경우 잠깐 넘을 수 있다(kernel.org cgroup-v2).
- `memory.max`에 닿으면: 회수를 해 보고, 못 줄이면 **그 cgroup 안에서** OOM killer가 돈다.
- 페이지 캐시가 중요한 이유
  - 그 cgroup이 읽고 쓴 파일의 캐시도 `memory.current`에 들어간다. 파일을 많이 다루는 서비스는 사용량이 limit 근처로 보이기 쉽다.
  - 캐시는 회수할 수 있어 대개 OOM으로 가지 않는다. 그래서 `memory.current`만 보고 "곧 죽는다"고 판단하면 틀릴 수 있다. 익명 메모리(`memory.stat`의 `anon`)를 따로 본다.

### 7. exit 137 = OOM?

- 아니다. 137은 128 + 9, 즉 **SIGKILL로 죽었다**는 뜻일 뿐이다.
- SIGKILL의 다른 출처: 쿠버네티스 종료 유예 시간(SIGTERM 뒤) 초과, 사람의 `kill -9`, 헬스 체크 실패 뒤 강제 종료.
- 확정하는 법
  - 쿠버네티스 `lastState.terminated.reason: OOMKilled`.
  - cgroup `memory.events`의 `oom_kill` 증가.
  - 노드 커널 로그의 `Memory cgroup out of memory: Killed process <pid> (...)`.

### 8. 힙 밖 JVM 메모리

- 메타스페이스(클래스 메타데이터 — 기본 상한 없음)
- 스레드 스택(스레드 수 × `-Xss`)
- 코드 캐시(JIT 결과)
- direct buffer(NIO, Netty — 기본 상한은 최대 힙 크기, OpenJDK `VM.java`)
- GC 자료구조(카드 테이블, 마킹 비트맵 등)
- JNI·native 라이브러리의 `malloc`, glibc arena 여유 공간(11번)
- 나눠 보는 도구
  - JVM을 `-XX:NativeMemoryTracking=summary`로 띄우고 `jcmd <pid> VM.native_memory summary`로 영역별 사용량을 본다.
  - `/proc/<pid>/status`의 `VmRSS`와 NMT 합계를 비교한다. 차이는 JVM 밖 native 사용량이다. `pmap -x`로 큰 영역을 찾는다.

### 9. 두 종류의 OOM

| | `OutOfMemoryError: Java heap space` | 커널 OOM kill |
|---|---|---|
| 누가 | JVM이 자기 힙 한도(-Xmx)에서 판단 | 커널이 물리 메모리·cgroup 한도에서 판단 |
| 모습 | 예외. 스택 트레이스·로그·힙 덤프를 남길 수 있다 | SIGKILL. 아무것도 못 남기고 즉시 종료(137) |
| 프로세스 | 살아 있을 수도 있다 | 죽는다 |

- `MaxMetaspaceSize`를 걸고 `MaxDirectMemorySize`를 limit에 맞게 작게 잡으면, 그 영역이 넘칠 때 커널 SIGKILL 대신 JVM의 `OutOfMemoryError`(메타스페이스는 `OutOfMemoryError: Metaspace`)로 바뀐다.
  - direct buffer는 옵션을 안 줘도 상한(= 최대 힙 크기)이 있어 넘으면 `OutOfMemoryError`가 난다(OpenJDK `VM.java`, `Bits.java`). 다만 힙 + 같은 크기의 direct buffer가 limit을 넘으면 그 전에 커널 OOM kill이 먼저 올 수 있다. 원인이 로그에 남아 진단이 쉬워진다.

### 10. 엉뚱한 DB가 죽는 이유

- OOM killer는 "원인 제공자"가 아니라 **점수가 가장 큰(메모리를 가장 많이 쓰는)** 프로세스를 고른다. 큰 버퍼 풀을 가진 DB가 1순위가 되기 쉽다.
- 재발 방지
  - 서비스마다 cgroup `memory.max`를 둔다. 배치가 넘치면 전체 OOM 대신 배치 cgroup 안에서만 OOM kill이 난다.
  - DB처럼 중요한 프로세스는 `oom_score_adj`를 낮추고(하한 아래로 낮추려면 `CAP_SYS_RESOURCE`), 버려도 되는 워커는 올린다.
  - (추가) 엄격 모드(2)로 "죽는 대신 할당 실패"를 택할 수도 있다. 모든 프로그램이 `ENOMEM`을 처리해야 하는 대가가 있다.
