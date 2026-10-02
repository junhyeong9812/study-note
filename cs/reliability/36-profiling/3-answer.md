# reliability/36-profiling — 정답

## 정답

### 1. 측정이 먼저

- 먼저 "얼마나 느린가"를 잰다: 지연 분포(p50·p99)와 처리량, 언제부터인지(19).
- 프로파일이 답하는 것: 시간을(또는 할당을) **어느 함수·호출 경로**에서 쓰나.
- 답하지 않는 것: 사용자 지연이 얼마인가, 개선이 충분한가. 그건 다시 측정해야 안다.

### 2. 한 스레드의 1초

```text
 ┌ CPU 실행 ┬── 락 대기 ──┬ CPU 실행 ┬── I/O 대기 ──┐
   ▲ CPU 프로파일: CPU 실행 구간만
   ▲ wall-clock: 전 구간(상태 무관, 일정 간격)
```

### 3. 실험 예측

(실험, async-profiler 4.5, JDK 21.0.12, `--cpus=2`, 6초)

- CPU: `cpu-worker: heavy 434`, `light 156` → 약 2.8:1(설계 3:1). `waiter`는 0샘플 — CPU를 거의 안 쓴다.
- wall: `waiter: 락 대기(monitor) 564`, `sleep 37`(재실행: 592, 8 — 실행마다 다르다). 시간 대부분이 `ObjectMonitor::enter`에서 `lock-holder`의 락을 기다리는 데 찍혔다.

### 4. 축과 해석

- x축: 스택 표본 모음을 알파벳순으로 정렬해 합친 것(시간 아님). y축: 스택 깊이(아래가 호출자). 너비 = 그 프레임이 나타난 표본 비율(Gregg).
- 플레임 차트(Chrome 개발자 도구)는 x축이 시간이다.
- "왼쪽이 먼저"는 틀렸다. 플레임 그래프에서 좌우 위치는 이름 순서일 뿐이다.

### 5. 세이프포인트 편향

- 세이프포인트에서만 스택을 찍는 샘플러는, 실제로 시간을 쓴 곳 대신 **다음 세이프포인트**(메서드 반환, 루프 검사 지점)에 표본을 몰아준다.
- 검사를 끈 실험(`-XX:-UseCountedLoopSafepoints -XX:LoopStripMiningIter=0`): 순진한 샘플러는 맨 위 프레임을 `mix`가 아닌 `heavy`/`light`로 보고했고, 비율을 355:72 ≈ 4.9:1로 부풀렸다(다른 실행 359:71, 362:46, 재실행 430:85, 407:48, 441:52 — 4.9~8.5:1). 같은 실행의 async-profiler는 351:131 ≈ 2.7:1, 맨 위 `Hot.mix`.
- 기본 설정: JDK 21은 `UseCountedLoopSafepoints=true`, `LoopStripMiningIter=1000`이라 긴 루프 안에도 검사가 있다. 그래서 순진한 샘플러도 `mix <- heavy` 338~411 : `mix <- light` 102~154(5회)로 비슷하게 맞혔다. 편향의 크기는 JIT 설정과 코드 모양에 달렸다.

### 6. 트라이

- 스택을 루트(아래)부터 읽은 경로로 보고 같은 접두사를 합친 트리(트라이). 노드 너비 = 그 접두사를 가진 표본 수.
- collapsed 한 줄 `a;b;c N` = 루트에서 잎까지 경로 하나와 그 경로로 끝난 표본 수. 트라이에 경로를 N번 넣은 것과 같다.

### 7. CPU 한가, p99 높음

- 전체 CPU가 한가하면 스레드가 기다리고 있을 가능성이 크다. 다만 단일 스레드·한 코어만 포화돼도 전체 평균은 낮게 보이므로 코어별·스레드별 CPU 사용률(`top -H`, `mpstat -P ALL`)도 확인한다. 순서: wall-clock(스레드별) → 락이 보이면 lock → I/O 대기면 하류(DB·HTTP) 쪽 지연 측정.

```bash
asprof -e wall -t -i 50ms -d 30 -f /tmp/wall.html <pid>
asprof -e lock -d 30 -f /tmp/lock.html <pid>
jcmd <pid> Thread.print     # 스냅숏으로 대기 지점 교차 확인
```

### 8. 커널 프레임이 없다

- Docker 기본 seccomp가 `perf_event_open`을 막는다. async-profiler는 `cpu`를 자동으로 `ctimer`로 내린다. `ctimer`는 커널 스택을 못 모은다(CpuSamplingEngines 문서). 실험에서도 `event=cpu-clock`이 `Perf events unavailable`로 실패했다.
- 선택지: seccomp 완화(+`SYS_ADMIN`), `--fdtransfer`, 호스트에서 특권으로 붙이기. 커널 시간이 필요 없으면 `ctimer` 결과로 사용자 공간만 해석한다.

### 9. 깨끗한 프로파일

- 문제 구간이 지난 뒤 떴다. 프로파일은 그 시간의 표본만 담는다.
- 다음에는: 지속 프로파일링(async-profiler `--loop`, JFR 상시 기록)으로 장애 시각의 표본을 남긴다. 사고 중에는 완화 전에 30초라도 떠 둔다(26의 증거 보존).
