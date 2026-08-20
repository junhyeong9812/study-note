# cs/straggler — Straggler와 Tail Latency — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다.
> 원고는 내가 직접 쓴 `Straggler.md`를 골격만 다듬은 것이다(2026-08-20).

## 전체 흐름

```text
정의    여러 대에 일을 나눠줬을 때 유독 느리게 끝나는 한 대. 전부 기다리는 설계라면 전체 응답 시간 = 가장 느린 한 대
원인    고장이 아니라 평범한 시스템의 상시 현상 — SSD GC, JVM GC, noisy neighbor, 네트워크 큐잉, 백그라운드 작업, data skew
규모    노드 하나가 1%만 느려도 N=100이면 63%의 요청이 걸린다 (1 - 0.99^N). 평균은 의미가 없고 꼬리(p99, p999)가 지배한다
대응    기다리지 않기(quorum) · 미리 한 번 더 보내기(hedged) · 중복 실행(speculative) · tied request · 애초에 안 만들기
연결    앞서 다룬 주제들(SSD GC, JVM GC, 뒤처진 컨슈머)이 표면에 드러나는 방식이 straggler다
```

## 1. 정의 — 전체 응답 시간 = 가장 느린 한 대

```text
작업을 10대에 분산, 응답을 전부 기다려야 함
  Node 1  ██ 10ms
  Node 2  ██ 12ms
  ...
  Node 10 ████████████████████ 800ms   ← straggler
  전체 완료 시간 = 800ms
```

9대가 아무리 빨라도 전체 = 가장 느린 한 대. 이걸 **tail latency** 문제라 부른다.

## 2. 왜 하필 그 한 대가 느려지는가

특별한 고장이 아니라 평범한 시스템에서 상시로 일어난다.

```text
SSD GC          하필 그 순간 그 디스크가 가비지 컬렉션 중
JVM GC          Full GC로 수백 ms 정지
CPU 경합        같은 머신의 다른 프로세스, 컨테이너 이웃 (noisy neighbor)
네트워크        스위치 큐잉, 재전송, 일시적 혼잡
백그라운드 작업  로그 로테이션, 백업, 인덱스 재구축, 모니터링 에이전트
하드웨어 열화    발열 스로틀링, 디스크 재할당 섹터 증가
데이터 편중      그 노드에만 유독 큰 파티션 (data skew)
```

## 3. 왜 규모가 커질수록 심각해지는가 — 여기가 핵심

개별 노드가 아주 가끔만 느려도, 노드 수가 많으면 거의 매번 걸린다. 노드 하나가 느릴 확률이 1%(p99)라면:

```text
전부 빠를 확률 = 0.99^N
N=1      99%      느릴 확률 1%
N=10     90%      느릴 확률 10%
N=100    37%      느릴 확률 63%
N=1000   0.004%   느릴 확률 사실상 100%
```

100대에 요청을 뿌리면 3분의 2의 확률로 매번 straggler를 만난다 — 각 노드가 99% 건강한데도. Jeff Dean의 "The Tail at Scale"이 이 문제를 정리한 논문이다. 요지: **규모가 커지면 평균은 의미가 없고 꼬리(p99, p999)가 사용자 경험을 지배한다.**

## 4. 대응 방법

### ① Quorum — 전부 기다리지 않기

BookKeeper의 Qa가 정확히 이것이다(→ [striping](../striping/)).

```text
Qw=3에 쓰고 Qa=2만 기다림
  B1 ██ 5ms ✓
  B2 ██ 6ms ✓          ← 2개 도착, 즉시 성공
  B3 ████████ 200ms    (계속 쓰긴 하지만 안 기다림)
  응답 시간 = 6ms
```

"다수만 응답하면 된다"는 규칙 하나로 straggler를 구조적으로 무력화한다. 반면 Kafka의 `acks=all`은 ISR 전원을 기다리므로 팔로워 한 대가 GC에 걸리면 프로듀서 응답 시간이 그대로 튄다.

### ② Hedged / Speculative Request — 미리 한 번 더 보내기

요청 전송 → p95 시간(예: 50ms) 지나도 응답 없음 → 다른 노드에 같은 요청을 하나 더 → 둘 중 먼저 오는 것 채택, 나머지 취소. 여분 부하는 5%쯤만 늘면서 tail latency를 크게 줄인다. Cassandra, gRPC 등에서 사용.

### ③ Speculative Execution — 배치 작업에서

MapReduce/Spark 방식. 태스크가 유독 느리면 같은 태스크를 다른 노드에서 중복 실행하고 먼저 끝난 쪽을 채택.

### ④ Backup / Tied Request

두 노드에 동시에 보내되 "다른 쪽에서 시작했으면 취소하라"는 정보를 함께 넘겨 중복 작업을 최소화.

### ⑤ 애초에 안 만들기

- 부하 분산을 정교하게 (data skew 제거)
- 백그라운드 작업 스케줄을 노드마다 어긋나게
- 읽기/쓰기 디스크 분리 ← BookKeeper의 journal/ledger 분리
- JVM GC 튜닝, 또는 힙 밖으로 데이터 빼기 ← Kafka가 페이지 캐시를 쓰는 이유 중 하나

## 5. 앞서 다룬 주제들이 표면에 드러나는 방식

```text
SSD GC로 그 디스크만 잠깐 느려짐 / JVM Full GC로 그 브로커만 멈춤 / 뒤처진 컨슈머의 랜덤 읽기가 쓰기 디스크를 점유
        ↓  그 노드가 straggler가 됨
        ↓  전부 기다리는 설계라면 → 전체 p99 latency 폭증
```

세 시스템의 선택을 straggler 관점에서 보면:

- **Kafka** — JVM 힙을 안 써서 GC straggler를 예방. 하지만 `acks=all`은 전원 대기라 발생하면 그대로 노출.
- **BookKeeper** — Qa 정족수로 회피, 디스크 분리로 읽기-쓰기 간섭도 예방.
- **Redpanda** — JVM 자체를 제거하고 thread-per-core로 스케줄링 지터를 예방.

## 핵심 문장

- 전부 기다리는 설계에서 전체 응답 시간은 가장 느린 한 대다.
- straggler는 고장이 아니라 상시 현상이고, 1 - 0.99^N 때문에 규모가 커지면 매번 만난다.
- 평균은 의미가 없다 — 꼬리가 사용자 경험을 지배한다.
- 대응은 둘로 나뉜다: 기다리지 않거나(quorum, hedged, speculative), 애초에 안 만들거나(skew 제거, 디스크 분리, 힙 밖으로).
- 앞 주제들(SSD GC, JVM GC, 읽기-쓰기 간섭)은 전부 straggler의 원인 목록에 다시 등장한다.

## 관련 자료

- 따라 친 원본 노트(직접 작성): `/home/jun/project/db-engine-lab/docs/study/Straggler.md`
- Jeff Dean, Luiz André Barroso, "The Tail at Scale", CACM 2013
- 연결: [striping](../striping/) (Qa) · [nand-flash](../nand-flash/) (SSD GC 스파이크) · [kafka-why-fast](../kafka-why-fast/) (페이지 캐시, acks=all)
