# distributed/30-batch-and-stream-processing — 배치와 스트림 처리: MapReduce·셔플·윈도·워터마크 — 정리 (힌트)

## 해결하는 문제

데이터가 한 대의 메모리·디스크·시간 예산을 넘으면 두 가지 질문이 생긴다.

```text
  배치:   "어제 로그 10TB에서 사용자별 클릭 수"     ← 입력이 끝이 있다(bounded). 다 모인 뒤 한 번에
  스트림: "지금 이 순간까지 1분마다 페이지별 클릭 수" ← 입력이 끝이 없다(unbounded). 오는 대로 계속
```

- 배치는 일을 여러 대에 나누고, 같은 키를 한곳에 모아(셔플) 합친다. 문제는 **일이 고르게 나뉘지 않는 것**(스큐)과 **중간에 죽는 기계**다.
- 스트림은 끝이 없으니 "언제 1분 집계를 확정할까"를 정해야 한다. 이벤트는 늦게, 순서가 뒤바뀌어 도착한다. 문제는 **늦게 온 이벤트**다.

쉬운 예: 전국 투표 개표다.
- 배치: 투표가 끝난 뒤 투표함을 지역별로 나눠 세고, 후보별로 모아 더한다. 한 지역에 표가 몰리면 그 지역 개표소만 늦게 끝난다.
- 스트림: 투표 중에 실시간 집계를 낸다. 산간 지역 투표함이 늦게 도착하면 "12시 집계"를 언제 확정할지 정해야 한다.

똑같은 구조다.\
배치의 핵심은 "키로 나누고 모으기", 스트림의 핵심은 "이벤트가 일어난 시각 기준으로 묶고, 어디까지 기다릴지 정하기"다.

실무 예:
- 일 배치 Spark 작업이 99% 태스크는 2분에 끝나는데 마지막 1개가 40분 걸린다.
- 모바일 앱 이벤트가 오프라인 뒤 몰려 들어와 "시간대별 활성 사용자" 그래프가 다음 날 다시 계산하면 달라진다.

## 동작·원리

### 1. MapReduce — 나누고, 키로 모으고, 합친다

```text
  입력 분할(M개)      map 태스크                 셔플                       reduce 태스크(R개)
  split 0 ──> map ──> (k,v) ──┐ hash(k) mod R   ┌─> reduce 0: 정렬 → 같은 k끼리 → reduce(k, [v..]) → out-0
  split 1 ──> map ──> (k,v) ──┼─────────────────┼─> reduce 1: ...                                → out-1
  split 2 ──> map ──> (k,v) ──┘ map 쪽 로컬 디스크 └─> reduce 2: ...                                → out-2
                               R개 파일로 나눠 씀    reduce가 원격으로 당겨 와 키로 정렬(필요하면 외부 정렬)
```

- Dean–Ghemawat 2004 §3.1
  - 중간 키 공간을 분할 함수(예: `hash(key) mod R`)로 R조각으로 나눈다. R과 분할 함수는 사용자가 정한다.
  - reduce 워커는 중간 데이터를 다 읽은 뒤 **키로 정렬**해 같은 키를 붙인다. 메모리에 안 들어가면 외부 정렬을 쓴다.
  - 정렬된 데이터를 훑으며 키마다 reduce 함수를 부른다.
- 규모(논문 §3.5의 예): M = 200,000, R = 5,000, 워커 2,000대.
- *셔플*: map 출력을 키로 다시 나눠 reduce로 보내고 정렬하는 단계. 네트워크·디스크 비용이 가장 큰 곳이다.
- *combiner*(§4.3): map 쪽에서 미리 부분 합을 내 셔플로 보낼 양을 줄인다. reduce 함수가 교환·결합 법칙을 만족할 때 쓴다(단어 세기의 `<the, 1>` 수천 개 → `<the, 3842>` 하나).

#### 장애 처리 — 재실행과 원자적 이름 바꾸기 (논문 §3.3)

```text
  워커 사망
   ├─ 끝난 map 태스크도 다시 실행   ← 출력이 그 기계의 로컬 디스크에 있어 못 읽는다
   ├─ 진행 중 태스크 다시 실행
   └─ 끝난 reduce는 그대로          ← 출력이 전역 파일 시스템(GFS)에 있다
  reduce 출력: 임시 파일에 쓰고 → 끝나면 최종 이름으로 원자적 rename
               같은 태스크가 두 번 돌아도 최종 파일은 한 번의 결과만 남는다
```

- 이 보장에는 전제가 있다: map·reduce 함수가 입력에 대해 **결정적**이어야 장애 없는 순차 실행과 같은 결과가 나온다(§3.3).
- *straggler*: 마지막 몇 태스크를 유난히 오래 붙잡는 기계. 논문은 끝날 무렵 남은 태스크의 *백업 태스크*를 다른 기계에 하나 더 띄우고 먼저 끝난 쪽을 쓴다. 이 기능을 끄면 정렬 프로그램이 44% 더 오래 걸렸다(§3.6). 기계 탓 straggler는 [systems/straggler](../../systems/straggler/2-summary.md).
- 백업 태스크는 **기계가 느린 것**을 고친다. **데이터가 한 키에 몰린 것**(스큐)은 고치지 못한다. 어느 기계에서 돌려도 그 키는 한 reduce가 다 받는다.

#### 실험: 스큐 키 하나가 리듀서 하나를 잡아먹는다 — 그리고 솔팅

- 클릭 10만 건(예시 분포): 절반이 `user-42`, 나머지는 `user-0..999` 고르게. 리듀서 4개, `hashCode() mod 4`로 분할, 리듀서 쪽 정렬 후 합산.
- 솔팅: `user-42`만 `user-42#0..#3`으로 쪼개 1단계 집계 → 소금(`#n`)을 떼고 2단계 집계.

```java
static int partition(String key) { return Math.floorMod(key.hashCode(), R); }
...
List<KV> salted = clicks.stream()
    .map(u -> new KV(u.equals("user-42") ? u + "#" + rnd.nextInt(4) : u, 1)).toList();
Map<String, Long> partial = run(salted, load1);                       // 1단계
List<KV> stage2 = partial.entrySet().stream()
    .map(e -> new KV(e.getKey().replaceAll("#\\d+$", ""), e.getValue())).toList();
Map<String, Long> res2 = run(stage2, load2);                          // 2단계
```

```text
(실험, eclipse-temurin 21 JDK, 단일 JVM 시뮬레이션, 2026-10-01)
[skew] 리듀서별 입력 건수 = [62469, 12468, 12460, 12603], user-42 → 리듀서 0, count=50126
[salt] 1단계 리듀서별 입력 = [24807, 24925, 25066, 25202], 2단계 입력 = [252, 249, 251, 251], user-42 count=50126
[check] 두 방법 결과 같음 = true
```

- 관찰
  - 그냥 집계하면 리듀서 0이 나머지의 약 5배를 받는다. 전체 작업 시간은 가장 늦은 리듀서가 정한다.
  - 솔팅 1단계는 네 리듀서가 고르게 약 2만 5천 건씩 받았다. 2단계는 부분 합 약 250건씩이라 가볍다.
  - 결과는 같다. 합(count)이 결합 법칙을 만족해 두 단계로 나눠도 되기 때문이다.
- 해석: 스큐 대처의 핵심은 "뜨거운 키를 여러 조각으로 쪼개 부분 집계 → 합치기"다. 중앙값처럼 부분 결과로 합칠 수 없는 집계에는 그대로 못 쓴다.

### 2. 배치에서 스트림으로 — 시간이 두 개다

```text
  이벤트 시간(event time) = 일이 일어난 시각 (기기가 기록)
  처리 시간(processing time) = 시스템이 그 이벤트를 처리하는 시각 (서버 벽시계)

  이벤트:   e@1s   e@3s   e@12s   e@4s   e@20s   e@5s   e@13s     ← 도착 순서
  이벤트 시간 축:  0 ──── 5 ──── 10 ──── 15 ──── 20 ──── 25
                  └─ 윈도 [0,10) ─┘└─ 윈도 [10,20) ─┘└─ [20,30)
  e@4s, e@5s, e@13s는 더 늦은 시각의 이벤트 뒤에 도착했다 = 순서 뒤바뀜(out-of-order)
```

- Flink 문서(Timely Stream Processing)
  - 처리 시간: 연산을 실행하는 기계의 시스템 시계. 결과가 도착 속도·장애에 따라 달라진다.
  - 이벤트 시간: 이벤트가 생산 기기에서 일어난 시각. 진행이 벽시계가 아니라 데이터에 달려 있다.
- *윈도*: 끝없는 스트림을 유한한 묶음으로 자르는 단위.
  - 텀블링: 겹치지 않는 고정 크기([0,10), [10,20)…).
  - 호핑: 고정 크기가 일정 간격으로 겹친다.
  - 세션: 활동 사이 빈 시간(gap)으로 끊는다.
  - Kafka Streams `TimeWindows`는 epoch에 정렬된다 — 첫 윈도가 타임스탬프 0에서 시작한다(4.1 소스 javadoc).
- *워터마크*: "이벤트 시간이 t에 도달했다, 이제 t 이하의 이벤트는 더 오지 않을 것이다"라는 선언. 데이터와 함께 흐른다(Flink 문서 "Watermark(t)").
  - 여러 입력을 받는 연산자의 이벤트 시간은 **입력들의 이벤트 시간 중 최솟값**이다(Flink 문서 "Watermarks in Parallel Streams").
  - 워터마크 뒤에 도착한 더 이른 이벤트가 *늦은 이벤트(late element)*다.
- Kafka Streams는 별도 워터마크 대신 *stream time*을 쓴다. 지금까지 본 레코드 타임스탬프로 정해지고, 새 레코드가 와야만 전진한다(Kafka Streams Core Concepts).
  - *grace period*: 윈도 끝 뒤에 늦은 레코드를 얼마나 더 받을지. **stream time > 윈도 끝 + grace**면 그 윈도의 레코드는 버린다(Core Concepts "Windowing").
  - 경계값은 소스가 더 엄격하다. 4.1.0 `KStreamWindowAggregate`는 `윈도 끝 > stream time − grace`일 때만 받으므로, stream time이 윈도 끝 + grace와 **같아도** 버린다.
  - 4.1의 `TimeWindows.ofSizeWithNoGrace`는 grace를 0으로 둔다 — 윈도 끝 뒤에 온 순서 뒤바뀐 레코드는 버린다(소스 javadoc의 CAUTION).

#### 실험: 10초 텀블링 윈도 + grace 5초 (Kafka Streams 4.1)

- 위 그림의 도착 순서대로 레코드 타임스탬프를 이벤트 시간으로 넣어 발행했다. 키는 모두 `page-1`.

```java
b.stream(IN, Consumed.with(Serdes.String(), Serdes.String()))
 .groupByKey()
 .windowedBy(TimeWindows.ofSizeAndGrace(Duration.ofSeconds(10), Duration.ofSeconds(5)))
 .count(Materialized.as(Stores.inMemoryWindowStore("w17-counts", Duration.ofMinutes(1), Duration.ofSeconds(10), false)))
 .toStream()
 .foreach((wk, c) -> out.add(...));
```

```text
(실험, Kafka 4.1.0 KRaft 단일 노드 + kafka-streams 4.1.0, 캐시 0, 2026-10-01)
  입력 t=1s
    → 윈도 [0s,10s) count=1
  입력 t=3s
    → 윈도 [0s,10s) count=2
  입력 t=12s
    → 윈도 [10s,20s) count=1
  입력 t=4s
    → 윈도 [0s,10s) count=3
  입력 t=20s
    → 윈도 [20s,30s) count=1
  입력 t=5s
  입력 t=13s
    → 윈도 [10s,20s) count=2
[metric] dropped-records-total task=0_0 = 1.0
```

- 관찰
  - `t=4s`는 stream time 12초에 도착했다. 12 < 10 + 5라 [0,10) 윈도에 들어갔다(count=3).
  - `t=5s`는 stream time 20초에 도착했다. 20 > 10 + 5라 버려졌다. 출력이 없고 `dropped-records-total`이 1이 됐다.
  - `t=13s`는 stream time 20초에 도착했지만 [10,20) 윈도는 stream time이 20 + 5 = 25에 닿기 전까지 열려 있어 들어갔다.
- 해석: 버려진 `t=5s`는 ERROR 없이 사라진다. 남는 흔적은 지표와 WARN 로그 한 줄뿐이다. [0,10) 윈도의 최종 count는 실제(4건)보다 1 적다.
  - 사실 점검 때 같은 토폴로지를 log4j 출력을 켜고 다시 돌리니 같은 결과에 `[log WARN] Skipping record for expired window. topic=[w30-fc-in] partition=[0] offset=[5] ... expiration=[…] streamTime=[…]`가 찍혔다(4.1.0 `AbstractKStreamTimeWindowAggregateProcessor`의 `log.warn`). 집필 때 출력에 이 줄이 없던 것은 로깅 바인딩 없이(slf4j NOP) 돌렸기 때문이다.

### 3. 스트림의 장애 처리 — 범위를 정확히

- 스트림 처리기는 상태(윈도 카운트 등)를 들고 있다. 장애 뒤 이어서 하려면 입력 위치와 상태를 같이 복구해야 한다.
- Kafka Streams의 `processing.guarantee` 기본값은 `at_least_once`다. `exactly_once_v2`로 바꾸면(브로커 2.5 이상) 입력 토픽 오프셋 커밋, 상태 저장소 갱신, 출력 토픽 쓰기를 원자적으로 완료한다. Kafka를 부작용 있는 외부 시스템이 아니라 저장소로 묶어 다루기 때문이다(Core Concepts "Processing Guarantees").
- 이 보장은 **Kafka 안**(입력 토픽 → 상태 → 출력 토픽)까지다. 처리 중 외부 DB·API를 부르면 그 호출은 재처리 때 다시 일어날 수 있다(17번 §4).
- 배치는 같은 문제를 "입력 불변 + 결정적 함수 + 출력 원자적 교체"로 푼다(MapReduce §3.3). 스트림은 입력이 계속 오므로 체크포인트·트랜잭션으로 같은 효과를 낸다.

## 쓰이는 자료구조·알고리즘

- **셔플 = 해시 분할 + 외부 정렬** — `hash(key) mod R`로 나누고, reduce 쪽에서 키로 정렬해 같은 키를 붙인다. 메모리를 넘으면 정렬된 런을 디스크에 쓰고 k-way 병합한다. [database/41-sorting-and-aggregation](../../database/41-sorting-and-aggregation/2-summary.md) · [algorithm/02-merge-sort](../../algorithm/02-merge-sort/2-summary.md) · [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)(k-way 병합의 최소 힙)
- **해시 집계** — 정렬 대신 키 → 누적값 해시 맵으로 합치는 방법. combiner·Kafka Streams의 윈도 상태가 이 모양이다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **결합·교환 법칙(모노이드)** — 부분 합을 어떤 순서·묶음으로 합쳐도 같다. combiner와 솔팅 2단계 집계가 성립하는 조건이다.
- **윈도 상태 = (키, 윈도 시작) → 집계값** — 시간 버킷 맵. 보존 기간이 지난 윈도는 지운다(실험의 `inMemoryWindowStore` 보존 1분).
- **워터마크 = 입력들의 최솟값** — 여러 파티션·소스의 이벤트 시간 중 가장 느린 쪽을 따른다. 입력 하나가 멈추면 전체가 멈춘다.

## 적용 — 풀어나가는 법

### 1. 배치냐 스트림이냐

- 결과가 하루 뒤에 필요하고 입력이 정해져 있으면 배치가 단순하다. 다시 돌리면 같은 결과가 나온다(결정적 함수일 때).
- 결과가 분 단위로 필요하면 스트림이다. 이때는 시간 정의(이벤트 시간), 윈도, 늦은 이벤트 정책을 **먼저** 정한다.
- 흔한 절충: 스트림으로 빠른 근사치를 내고, 배치로 늦게 온 것까지 넣어 확정치를 다시 계산한다.

### 2. 스큐 진단과 대처

```text
  증상: 태스크 소요 시간 분포에서 한두 개만 수십 배
  확인: 그 태스크 입력 건수 → 키 빈도 상위 N개 (top-k)
  대처: ① map 쪽 combiner로 뜨거운 키를 미리 줄인다
        ② 뜨거운 키만 솔팅(키#0..#k-1) → 부분 집계 → 합치기 (실험)
        ③ 조인이면 작은 쪽을 브로드캐스트해 셔플을 없앤다
```

- 키 빈도 확인(예: SQL로 표본)

```sql
SELECT user_id, count(*) FROM clicks_sample GROUP BY user_id ORDER BY 2 DESC LIMIT 20;
```

### 3. 늦은 이벤트 정책 (Kafka Streams 4.1)

```java
// 이벤트 시간: 레코드 타임스탬프에 이벤트 발생 시각을 넣어 발행하거나 TimestampExtractor로 꺼낸다
KTable<Windowed<String>, Long> counts = clicks
    .groupByKey()
    .windowedBy(TimeWindows.ofSizeAndGrace(Duration.ofMinutes(1), Duration.ofMinutes(10)))  // 늦음 10분까지 허용
    .count();
counts.suppress(Suppressed.untilWindowCloses(Suppressed.BufferConfig.unbounded()))       // 윈도가 닫힐 때 한 번만 내보낸다
      .toStream().to("clicks-per-minute");
```

- grace를 늘리면 늦은 이벤트를 더 받지만 결과 확정이 늦어지고 상태를 오래 들고 있다.
- 버려진 레코드는 `dropped-records-total`(task 단위 지표)과 WARN 로그 `Skipping record for expired window`로만 보인다. 이 지표에 경보를 건다.
- 확정 뒤에도 고쳐야 하는 업무(정산)라면 늦은 이벤트를 별도 토픽으로 보내 배치로 보정한다.

## 장애 시나리오와 대처

### 1. 늦게 온 이벤트 → 윈도 집계 누락 (⚠)

- **현상**: 실시간 대시보드의 시간대별 합계가 다음 날 배치 결과보다 작다. 모바일 트래픽이 많은 시간대일수록 차이가 크다.
- **보이는 형태**: ERROR 로그 없음. WARN `Skipping record for expired window. ... expiration=[…] streamTime=[…]`가 찍히고 Kafka Streams `dropped-records-total`이 오른다. 실험에서 `t=5s` 레코드가 출력 없이 사라지고 지표가 1이 됐다.
- **원인**: stream time(또는 워터마크)이 윈도 끝 + grace를 넘은 뒤 그 윈도의 이벤트가 도착했다. 오프라인 기기·재시도·상류 지연이 흔한 출처다.
- **대처**: 실제 지연 분포(이벤트 시간과 도착 시간의 차이 p99)를 재고 grace를 정한다. 버려지는 비율에 경보를 건다. 늦은 이벤트를 배치로 보정한다.

### 2. 스큐된 키 → 한 태스크만 느림 (⚠)

- **현상**: 전체 작업의 대부분 태스크가 끝났는데 한 태스크가 수십 배 오래 걸린다. 그 태스크만 메모리 부족·디스크 스필이 난다.
- **보이는 형태**: 태스크별 입력 건수 분포가 한쪽으로 치우친다. 실험에서 리듀서 0이 62,469건, 나머지가 약 12,500건씩.
- **원인**: 해시 분할은 같은 키를 한 곳에 보낸다. 한 키가 데이터의 절반이면 그 리듀서가 절반을 받는다. 기계를 바꾸거나 백업 태스크를 띄워도 줄지 않는다.
- **대처**: combiner, 뜨거운 키 솔팅 + 2단계 집계(실험에서 1단계 입력이 약 2만 5천 건씩으로 고르게), 조인은 브로드캐스트. 부분 결과로 합칠 수 없는 집계(정확한 중앙값 등)는 근사 알고리즘을 검토한다.

### 3. 유휴 파티션 하나가 워터마크를 붙잡는다

- **현상**: 어떤 윈도 결과도 나오지 않는다. 입력 트래픽은 정상이다.
- **보이는 형태**: 연산자의 현재 이벤트 시간(워터마크)이 몇 시간 전에 멈춰 있다. 입력 파티션 하나에 새 이벤트가 없다.
- **원인**: 여러 입력을 받는 연산자의 이벤트 시간은 입력들의 최솟값이다(Flink 문서). 입력 하나가 조용하면 최솟값이 전진하지 않는다. Kafka Streams의 stream time도 새 레코드가 와야 전진한다.
- **대처**: 유휴 입력을 워터마크 계산에서 빼는 설정(Flink의 idleness 설정)을 쓰거나, 주기적인 하트비트 이벤트를 넣는다. 테스트 환경처럼 트래픽이 적은 곳에서 특히 드러난다.

### 4. 처리 시간 윈도를 써서 재처리 결과가 달라진다

- **현상**: 장애 뒤 같은 입력을 다시 돌렸더니 시간대별 집계가 처음과 다르다.
- **보이는 형태**: 재처리 구간이 "재처리한 시각"의 윈도에 몰려 있다.
- **원인**: 처리 시간 윈도는 서버 벽시계로 묶는다. 결과가 도착 속도·장애에 따라 달라진다(Flink 문서 "Processing time").
- **대처**: 업무 의미가 있는 집계는 이벤트 시간으로 묶는다. 이벤트 시간은 기기 시계를 믿는 것이므로 미래·과거로 크게 벗어난 타임스탬프를 거른다(04번 시계).

### 5. 비결정적 map 함수 → 재실행 결과가 달라진다

- **현상**: 같은 배치를 다시 돌렸더니 출력 건수가 미세하게 다르다. 일부 태스크가 실패 후 재실행된 날에만 그렇다.
- **보이는 형태**: 출력 파티션 사이에 중복 또는 누락된 레코드.
- **원인**: map·reduce에서 현재 시각·난수·외부 조회를 썼다. MapReduce의 "장애 없는 순차 실행과 같은 결과" 보장은 함수가 결정적일 때만 성립한다(§3.3). 재실행된 태스크가 다른 결과를 내면 한 출력은 첫 실행, 다른 출력은 재실행 결과를 본다.
- **대처**: 난수는 입력에서 유도한 시드를 쓰고, 시각·외부 값은 입력에 미리 담는다. 출력은 임시 경로에 쓰고 원자적으로 교체한다.

## 핵심 문장

- MapReduce는 키로 해시 분할해 셔플하고, reduce 쪽에서 키로 정렬해 같은 키를 붙인다. 셔플이 가장 비싸고 combiner가 그 양을 줄인다.
- 장애는 결정적 함수 + 재실행 + 출력의 원자적 rename으로 견딘다. 결정적이지 않으면 재실행이 다른 답을 낸다.
- 해시 분할은 한 키를 한 곳에 보내므로 뜨거운 키 하나가 작업 전체 시간을 정한다. 솔팅 + 2단계 집계로 고르게 나눈다(실험: 62,469 vs 약 12,500 → 약 25,000씩).
- 스트림은 이벤트 시간으로 묶고, 워터마크·stream time과 grace로 "어디까지 기다릴지"를 정한다. 그 뒤에 온 이벤트는 ERROR 없이 버려진다(실험: `dropped-records-total` 1, WARN 로그 한 줄).
- 스트림의 exactly-once는 Kafka 안(입력 오프셋·상태·출력)까지다.

## 관련 주제·근거

- 선행
  - [17-queues-logs-and-delivery-semantics](../17-queues-logs-and-delivery-semantics/2-summary.md) — 로그·파티션·전달 보장
  - [21-kafka-internals](../21-kafka-internals/2-summary.md) — 파티션과 보존
- 연결
  - [database/41-sorting-and-aggregation](../../database/41-sorting-and-aggregation/2-summary.md) — 외부 정렬·해시 집계·디스크 스필
  - [database/33-partitioning-and-sharding](../../database/33-partitioning-and-sharding/2-summary.md) — 해시 분할과 핫 키
  - [database/37-row-vs-column-storage](../../database/37-row-vs-column-storage/2-summary.md) — 배치 분석의 저장 형식
  - [systems/straggler](../../systems/straggler/2-summary.md) — 느린 기계와 백업 태스크
  - [04-physical-clocks-and-ntp](../04-physical-clocks-and-ntp/2-summary.md) — 이벤트 시간은 기기 시계를 믿는다
  - [16-outbox-and-dual-write](../16-outbox-and-dual-write/2-summary.md) — 스트림의 원천이 되는 CDC
- 교재·강의·논문
  - DDIA 1판 10장 Batch Processing(MapReduce, 셔플, 조인, 스큐), 11장 Stream Processing(이벤트 시간 vs 처리 시간, 윈도, 늦은 이벤트, 장애 허용)
  - MIT 6.5840 Spring 2026 L1 Introduction — 준비 읽기 MapReduce(2004), Lab 1 MapReduce <https://pdos.csail.mit.edu/6.824/schedule.html>
  - Dean·Ghemawat, "MapReduce: Simplified Data Processing on Large Clusters", OSDI 2004 — §3.1 실행 흐름(`hash(key) mod R`, 정렬·외부 정렬), §3.3 장애 시 의미론(결정적 함수, 원자적 rename), §3.5 M·R 규모, §3.6 백업 태스크(44%), §4.3 combiner <https://pdos.csail.mit.edu/6.824/papers/mapreduce.pdf>
- 제품 문서
  - Apache Flink "Timely Stream Processing" — 처리 시간·이벤트 시간, Watermark(t), 병렬 스트림의 최솟값, lateness <https://nightlies.apache.org/flink/flink-docs-release-2.1/docs/concepts/time/>
  - Kafka Streams 4.1 Core Concepts — stream time, windowing·grace period("stream time > window end + grace → discarded"), `processing.guarantee`(기본 `at_least_once`, `exactly_once_v2`) (소스 `docs/streams/core-concepts.html` @ 4.1.0)
  - Kafka Streams 4.1 `TimeWindows.java` javadoc — epoch 정렬, `ofSizeWithNoGrace`의 grace 0 경고 (소스 `streams/src/main/java/org/apache/kafka/streams/kstream/TimeWindows.java` @ 4.1.0)
- 실험 목록
  - `MapReduce30.java`(eclipse-temurin 21 JDK, 단일 JVM): 10만 건·리듀서 4, 스큐 [62469, 12468, 12460, 12603] → 솔팅 1단계 [24807, 24925, 25066, 25202]·2단계 [252, 249, 251, 251], 결과 동일
  - `Streams30.java`(공용 `sn-dw-kafka` Kafka 4.1.0 + kafka-streams 4.1.0, `--network container:sn-dw-kafka`): 10초 텀블링·grace 5초, 도착 순서 1·3·12·4·20·5·13초 → `t=5s`만 버려짐, `dropped-records-total`=1
