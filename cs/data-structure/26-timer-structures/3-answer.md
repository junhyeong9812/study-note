# data-structure/26-timer-structures — 정답

## 정답

### 1. 등록·취소가 더 중요한 이유

- 타임아웃 타이머는 대부분 만료되지 않는다. 응답이 오면 취소된다.
- 리눅스 `kernel/time/timer.c` 주석: "The vast majority of timeout timers (networking, disk I/O ...) are canceled before expiry."
- 그래서 타이머 하나의 일생에서 거의 매번 일어나는 연산은 등록과 취소다. 만료 처리는 드물다. 등록·취소가 O(1)인 구조(휠)가 유리해지는 근거다.

### 2. 힙의 비용과 취소

```text
         [105]           등록: 끝에 넣고 위로    O(log n)
        /     \          만료: 루트 빼고 아래로  O(log n)
     [230]   [150]       취소: 위치를 알면 O(log n), 모르면 찾느라 O(n)
```

- `PriorityQueue.remove(Object)`는 배열을 처음부터 훑어 원소를 찾는다. Javadoc이 "linear time"이라고 적는다.
- `ScheduledThreadPoolExecutor`의 `DelayedWorkQueue`는 작업마다 힙 안 위치(`heapIndex`)를 기록하고 sift 때마다 갱신한다. 찾기가 필요 없으므로 제거가 O(log n)이다(소스 주석 "down from O(n) to O(log n)").
- 실험(`TimerBench.java` B): `remove(Object)`로 전부 취소하는 시간이 N 두 배마다 약 2.5~3.8배 — O(n²) 모양. 휠 취소는 µs 단위.

### 3. 지연 취소의 흔적

- 실험(`CancelLeak.java`, OpenJDK 21.0.12)
  - 기본(`removeOnCancel=false`): `getQueue().size()=100000`
  - `setRemoveOnCancelPolicy(true)`: `getQueue().size()=0`
- 기본값은 취소 표시만 하고 만료 시각(여기서는 1시간 뒤)까지 힙에 둔다.
- 운영 문제: 타임아웃이 길고 요청이 많으면 취소된 작업 객체가 쌓인다(OpenJDK 21은 취소 때 `callable`을 null로 만들어 람다가 잡은 요청 객체는 보통 풀린다). 남는 수는 대략 `초당 취소 수 × 타임아웃 길이`까지 오르고, 그 규모가 가용 힙을 넘으면 `OutOfMemoryError`. 큐가 커지면 등록·만료의 log n도 커진다.

### 4. 해시 휠의 칸과 rounds

- 만료 틱 = 2 + 21 = 23. 칸 = 23 % 8 = 7. rounds = (21 − 1) / 8 = 2.
- 바늘이 7번 칸에 오는 시각: 7(rounds 2 → 1), 15(1 → 0), 23(rounds 0 → 만료). 세 번째 방문에서 만료된다.
- Netty `HashedWheelTimer`의 `remainingRounds = (calculated - tick) / wheel.length`가 같은 계산이다. Netty의 `tick`은 다음에 처리할 틱(= now + 1 = 3)이라 (23 − 3) / 8 = 2로 같다.

### 5. 힙 vs 휠 두 가지

- 실험(`TimerBench.java` A, N=100만, 집필 3회 + 사실 점검 1회): 131072칸 휠 200~293 ms < 힙 1740~1904 ms < 512칸 휠 3809~20862 ms. 512칸 휠은 실행마다 크게 흔들렸지만 4회 모두 가장 느렸다.
- 이유
  - Scheme 6(해시 휠)은 매 틱 그 칸의 타이머를 전부 훑으며 rounds를 줄인다. 논문: n개 타이머면 틱당 평균 n/TableSize 일.
  - 512칸: 평균 만료가 약 5만 틱 뒤라 타이머 하나가 약 100번(5만 / 512) 훑인다. 등록이 O(1)이어도 틱 비용이 힙의 log n을 넘었다.
  - 131072칸: 만료 범위(10만 틱)보다 칸이 많아 rounds가 0이다. 타이머마다 등록 1번, 만료 1번만 만진다.
- 결론: 해시 휠의 O(1)은 등록·취소 이야기다. 칸 수 × 틱을 타임아웃 범위에 맞춰야 틱 비용도 작다.

### 6. 틱보다 짧은 타임아웃

- 휠은 틱 경계에서만 만료를 확인한다. 등록 시점이 틱 사이 어디냐에 따라 늦어지는 양이 다르다.
- 대략 `요청 ≤ 실제 < 요청 + 틱 (+ 스케줄링 지연)`. 틱 100 ms에서 10 ms 요청은 10~110 ms 사이.
- 실험(`WheelLatency.java`, 각 20개 × 2회): 휠 10 ms 요청 → 실제 10~108 ms(평균 59·62), 150 ms 요청 → 160~250 ms. STPE(힙)는 10~16 ms, 150 ms.

### 7. 계층형 휠

- 시계판 비유: 초·분·시·일 바퀴를 따로 둔다. Varghese–Lauck 예는 100 + 24 + 60 + 60 = 244칸으로 100일을 덮는다(평평하게 하면 864만 칸).
- 원래 계층형 휠(Scheme 7): 위 단계 칸에 있던 타이머를, 바늘이 오면 아래 단계로 옮겨 담는다. 정확한 시각을 지키는 대가로 옮기는 비용이 든다.
- 리눅스 4.8+: 먼 타이머를 거친 레벨 칸에 넣고 **아래로 옮기지 않는다.** 그 칸에서 그대로 만료된다(timer.c 주석 "We don't have cascading anymore").
- 포기한 것: 먼 타이머의 정밀도. HZ=1000에서 4~32초 구간은 512 ms 단위로 묶인다. 근거는 "대부분 만료 전 취소, 만료됐다면 이미 비정상이니 조금 늦어도 된다". 마지막 레벨보다 긴 타이머는 그 최대값에서 강제 만료된다.

### 8. 취소 타이머 누적 OOM

- 원인: `ScheduledThreadPoolExecutor` 기본 `removeOnCancel=false`. 응답 뒤 `cancel()`한 타임아웃 작업이 만료 시각까지 힙에 남는다. 타임아웃 길이 동안 쌓여 대략 `초당 취소 수 × 타임아웃 길이`에서 멈추는데, 그 규모가 힙을 넘었다. OpenJDK 21에서는 취소 때 `callable = null`(FutureTask `finishCompletion`)이라 작업 객체 자체가 주로 남는다.
- 확인
  - `jcmd <pid> GC.class_histogram`에서 `ScheduledThreadPoolExecutor$ScheduledFutureTask` 개수가 진행 중 요청 수보다 몇 자릿수 크다.
  - 앱에서 `executor.getQueue().size()`를 지표로 내보내 진행 중 요청 수와 비교한다.
  - 힙 덤프에서 `DelayedWorkQueue.queue` 배열이 지배적인 보유자인지 본다.
- 대처: `setRemoveOnCancelPolicy(true)`. 타임아웃이 매우 많으면 휠로 옮긴다. 직접 만든 지연 취소는 쓰레기 비율 기준 정리를 넣는다.

### 9. Netty 두 보고

- "50 ms가 100 ms 넘어서 끊긴다": 휠 해상도. Netty `HashedWheelTimer` 기본 틱은 100 ms다. 휠이 제때 돌면 실제 지연은 요청 + 0~1틱이다(워커가 밀리면 더 늦을 수 있다). 생성자의 `tickDuration`을 본다. 정밀해야 하는 타임아웃만 틱이 작은 별도 타이머로 분리한다.
- "타이머 스레드 CPU가 높다": 두 가지를 본다.
  - 칸 수(`ticksPerWheel`, 기본 512)가 타이머 수·타임아웃 길이에 비해 작아 틱마다 같은 타이머를 여러 번 훑는다(5번 답).
  - 인스턴스를 연결마다 만들어 워커 스레드가 여러 개 돈다. Netty는 인스턴스가 64개를 넘으면 "You are creating too many HashedWheelTimer instances" 오류 로그를 남긴다. 인스턴스는 하나를 공유한다.
- 틱을 줄여 첫 문제를 풀면 빈 칸을 도는 횟수가 늘어 두 번째 문제가 커질 수 있다. 둘은 트레이드오프다.
