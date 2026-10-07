# architecture/13-latency-numbers — 지연 자릿수 감각과 AMAT — 정리 (힌트)

## 해결하는 문제

코드를 쓰기 전에 "이게 대략 얼마 걸릴까"를 어림하지 못하면, 반복문 안에 원격 호출을 넣는 실수를 리뷰에서 못 잡는다.

```text
  for (Order o : orders) {                 // 1000건
      Customer c = customerApi.get(o.cid); // 원격 호출 한 번 = 수십 µs ~ 수 ms
      ...                                  // 나머지 계산 = 원소당 ns 단위
  }
  → 시간의 거의 전부가 "왕복 대기"다. 계산을 아무리 빠르게 해도 안 줄어든다.
```

- 필요한 것은 정확한 숫자가 아니라 **자릿수**(ns·µs·ms 중 어디인가)와 **비율**(몇 배 차이인가)이다.
- 그리고 캐시처럼 "대부분 빠르고 가끔 느린" 경로의 평균을 계산하는 식(AMAT)이 필요하다.
  - *AMAT(Average Memory Access Time, 평균 메모리 접근 시간)*: 히트 시간 + 미스율 × 미스 페널티. 캐시 성능을 한 숫자로 보는 식.

쉬운 예: 장보기다.
- 냉장고에서 꺼내기 10초, 동네 마트 10분, 대형 마트 1시간.
- 저녁 재료 20가지를 하나씩 대형 마트에 다녀오면 20시간이다. 한 번에 사 오면 1시간이다.

똑같은 구조다.\
냉장고 = CPU 캐시, 마트 = 메모리·디스크, 대형 마트 왕복 = 네트워크 왕복이다. "하나씩 다녀오기"가 N+1이다.

실무 예:
- 이 호스트 실험(아래 실험 2)에서 루프백으로 id 1000개를 하나씩 조회하면 59~142ms, 한 번에 모아 조회하면 3.3~9.3ms, 같은 HashMap을 프로세스 안에서 조회하면 0.15~0.25ms였다.
- 같은 1000건 조회가 방법에 따라 두 자릿수 이상 갈린다. 같은 데이터센터 안의 실제 네트워크는 왕복이 루프백보다 길어, N+1이 왕복 대기에 쓰는 시간(건수 × 왕복)은 더 커진다. 다만 실제 DB에서는 단건 조회와 묶음 조회의 실행 비용이 달라 배율은 따로 재야 한다.

## 동작·원리

### 1. 자릿수 막대 — 널리 인용되는 표

```text
  "Latency Comparison Numbers (~2012)" (jboner gist — 아래 출처 성격 참고), 로그 눈금
  0.5 ns   L1 캐시 참조                     |
    5 ns   분기 예측 실패                    |#
    7 ns   L2 캐시 참조                     |#
   25 ns   뮤텍스 잠금/해제                  |##
  100 ns   메인 메모리 참조                  |###
    3 µs   1KB 압축(Zippy)                 |#####
   10 µs   1Gbps로 1KB 전송                 |######
  150 µs   SSD 4KB 무작위 읽기               |#######
  250 µs   메모리에서 1MB 순차 읽기           |#######
  500 µs   같은 데이터센터 안 왕복            |########
    1 ms   SSD에서 1MB 순차 읽기             |########
   10 ms   디스크 탐색                       |#########
   20 ms   디스크에서 1MB 순차 읽기           |##########
  150 ms   캘리포니아 → 네덜란드 → 캘리포니아  |###########
           (막대 1칸 ≈ 대략 3~10배)
```

- **출처 성격**: 이 표는 1차 측정 자료가 아니라 2차 정리다.
  - 원형은 Peter Norvig의 글 "Teach Yourself Programming in Ten Years"의 "Approximate timing for various operations on a typical PC" 표다(L1 0.5ns, 분기 예측 실패 5ns, L2 7ns, 뮤텍스 25ns, 메인 메모리 100ns, 디스크 탐색 8ms 등).
  - jboner gist는 제목에 "~2012"를 달고 "By Jeff Dean", "Originally by Peter Norvig"라고 적는다. 2026년 기준으로는 LLM 토큰 생성 같은 줄이 덧붙어 있다.
  - Norvig 판과 gist 판도 줄마다 다르다(예: 디스크 탐색 8ms vs 10ms, 전송은 2KB 20µs vs 1KB 10µs).
- 그래서 **개별 숫자는 하드웨어 세대마다 바뀐다.** 오래 가는 것은 층 사이의 비율과 자릿수다.

### 2. 이 호스트에서 잰 같은 사다리

환경: i7-13700HX, Linux 7.0.0-34, gcc 13.3.0. **측정 중 코어 클록이 약 0.8~0.93GHz로 낮게 묶여 있었다**(11번 참고). CPU 안쪽 숫자는 클록에 비례해 커졌다.

```text
                                     이 호스트 (5회 범위)            표(~2012)
  L1 히트 (포인터 사슬 16KB)          4.8~6.1 ns  (≈5 사이클)        0.5 ns
  함수 호출 (noinline)                1.5~1.8 ns                     —
  L2 히트 (64~256KB)                  15.7~17.0 ns (≈15 사이클)       7 ns
  DRAM 무작위 (256MB 사슬)            220~233 ns                     100 ns
  시스템 콜 getppid                   326~345 ns                     —
  루프백 TCP 왕복 (64B, Nagle 끔)      34.1~41.9 µs                   (같은 DC 왕복 500 µs)
  SSD 4KB 무작위 읽기 (O_DIRECT)       90~109 µs                      150 µs
  4KB 쓰기 + fdatasync (ext4, NVMe)    2.63~2.89 ms                   —
```

- 측정 방법(`lat.c`): 함수 호출·시스템 콜은 1천만·1백만 번 반복의 평균. 루프백은 두 스레드 사이 64B 핑퐁 2만 번(`taskset -c 2,4`로 프로세스만 묶었고 스레드별 CPU 고정은 하지 않았다). 5회 중 2회는 사실 점검 재실행이고, 루프백 값은 재실행(41.4~41.9µs)이 처음 3회(34.1~34.6µs)보다 컸다. L1·L2·DRAM 행은 11번 실험 1(4회 범위)이다. SSD는 64MB 파일을 만든 뒤 `O_DIRECT`로 페이지 캐시를 우회해 4KB 무작위 `pread` 2천 번. 쓰기는 4KB `pwrite` + `fdatasync` 200번.
- CPU 안쪽(L1·L2·함수 호출·시스템 콜)은 클록이 낮아 표보다 몇 배 크다. 장치 쪽(SSD)은 표와 같은 자릿수였다.
- 시스템 콜 값은 [os/02-system-calls](../../os/02-system-calls/2-summary.md)의 같은 호스트 측정(약 109ns)보다 3배쯤 크다. 측정 시점의 클록 차이로 본다(해석).
- 루프백 왕복 34~42µs는 NIC를 거치지 않는데도 DRAM 무작위 접근(220~233ns)의 약 150~190배다. 커널 TCP 스택을 두 번 지나고, 잠든 상대 스레드를 깨우는 비용이 들어 있다는 해석이다([os/07-threads-and-context-switch](../../os/07-threads-and-context-switch/2-summary.md)).

### 3. 비율로 기억한다

```text
  기준: 캐시 안 연속 처리 원소 1개 ≈ 1 ns  (11번 실험 2의 행 우선 합: 원소당 1.2~1.5 ns)

  DRAM 무작위 1회        ≈ 100~230 ns   →   약 100~200배
  시스템 콜 1회          ≈ 0.1~0.3 µs   →   약 100~300배
  루프백 왕복 1회        ≈ 34~42 µs     →   약 3~4만 배
  같은 DC 왕복 1회(표)   ≈ 500 µs       →   약 50만 배   ← ⚠ 칸의 "메모리 접근 수십만 회"
  fsync 1회             ≈ 2.6~2.9 ms   →   약 3백만 배
  대륙 간 왕복(표)       ≈ 150 ms       →   약 1.5억 배
```

- ⚠ 칸의 "네트워크 1회 ≈ 메모리 접근 수십만 회"는 **캐시에 맞는 연속 접근(원소당 약 1ns)** 기준이다. DRAM 무작위 접근(100ns) 기준이면 약 5천 배다. 어느 쪽이든 루프 안 원격 호출 한 번이 그 루프의 계산 전부를 압도한다.

### 4. AMAT — 평균을 계산하는 식

```text
  AMAT = 히트 시간 + 미스율 × 미스 페널티

  두 층이면 페널티 자리에 다시 AMAT을 넣는다
  AMAT = T_L1 + m_L1 × ( ΔT_L2 + m_L2 × ΔT_mem )
         ΔT = 그 층까지 가는 데 추가로 드는 시간
```

- *미스율(miss rate)*: 접근 중 미스 비율.
- *미스 페널티(miss penalty)*: 미스 한 번에 추가로 드는 시간.
- 이 호스트 숫자(사이클)로 계산: T_L1 = 5, ΔT_L2 = 15 − 5 = 10, ΔT_mem = 190 − 15 = 175.
  - L1 미스율 5%, L1 미스 중 L2 미스 20%(예시): AMAT = 5 + 0.05 × (10 + 0.2 × 175) = 5 + 0.05 × 45 = **7.25 사이클**.
  - L1 미스율만 10%로 늘면(예시): 5 + 0.10 × 45 = **9.5 사이클**. 미스율 5%p가 평균을 31% 늘린다.
- 같은 식이 애플리케이션 캐시에도 그대로 맞는다.
  - 캐시 히트 0.1ms, DB 조회 5ms(예시). 히트율 99%: 0.1 + 0.01 × 5 = 0.15ms. 히트율 95%: 0.1 + 0.05 × 5 = 0.35ms.
  - **히트율이 4%p 떨어졌는데 평균 지연은 2.3배**다. 미스 페널티가 히트 시간보다 수십 배 크면 미스율이 평균을 지배한다.
- AMAT은 기댓값이다. 평균만 보고 꼬리(p99)를 놓치면 안 된다. 어느 백분위수가 움직이는지는 미스율에 달렸다 — 미스율이 1%를 넘으면 p99가 히트 지연에서 미스 지연으로 뛰고(위 예: 0.1ms → 5ms), 1% 미만이면 p99는 그대로이고 p99.9 같은 더 먼 꼬리가 움직인다. [math/08-expectation-variance-tails](../../math/08-expectation-variance-tails/2-summary.md) · [reliability/34-tail-latency-and-stragglers](../../reliability/34-tail-latency-and-stragglers/2-summary.md)
- 출처: 식 자체는 컴퓨터 구조 교재의 표준 식이다. Hennessy·Patterson 『Computer Architecture: A Quantitative Approach』 부록 B [?] (장·절 미확인). CS:APP 3판 6.4.7 "Performance Impact of Cache Parameters"가 미스율·히트 시간·미스 페널티를 다루는 절이다(절 제목은 목차로 확인, 본문 미확인).

### 5. 지연과 처리량은 다르다

```text
  지연(latency): 한 건이 끝나는 데 걸리는 시간
  처리량(throughput): 단위 시간당 끝나는 건수

  동시에 하나씩:  [===요청1===][===요청2===][===요청3===]      처리량 = 1 / 지연
  겹쳐서 여러 개:  [===요청1===]
                    [===요청2===]                              처리량 = 평균 동시 건수 / 평균 지연
                      [===요청3===]                            (Little의 법칙 — 안정 상태의 장기 평균)
```

- 11번 실험에서 256MB 순차 사슬은 접근당 약 8사이클이었다. DRAM 지연(약 190사이클)이 줄어든 게 아니라, 프리페처가 여러 라인을 **겹쳐서·미리** 가져와 처리량이 오른 것으로 본다(해석 — 시간만 쟀고 프리페치 카운터는 못 봤다. 결과가 프리페치 설명과 맞는다는 데까지가 측정).
- 네트워크도 같다. 배치·파이프라이닝은 왕복 한 번의 지연을 줄이지 않고, 한 왕복에 실을 일을 늘린다. 그래서 여러 건을 다 받는 **전체 시간**은 줄어든다(실험 2). [math/10-queueing-and-littles-law](../../math/10-queueing-and-littles-law/2-summary.md) · [network/03-latency-bandwidth-bdp](../../network/03-latency-bandwidth-bdp/2-summary.md)

### 실험 2: N+1 vs 배치 vs 로컬 (Java 21, 루프백)

```java
// 서버: 한 줄에 쉼표로 묶인 id들을 받아 HashMap에서 찾아 한 줄로 돌려준다 (같은 JVM의 다른 스레드)
for (int id : ids) { out.println(id); out.flush(); sum += parse(in.readLine()); }   // N+1: id마다 왕복
out.println(String.join(",", idsAsStrings)); out.flush(); parseAll(in.readLine());    // 배치: 왕복 1번
for (int id : ids) sum3 += store.get(id);                                             // 로컬 조회
```

`eclipse-temurin:21-jdk`(21.0.12), `--network none --cpus=2 --cpuset-cpus=2,4`, id 1000개, 한 번 실행에 5회 중 JIT 예열 전인 첫 회 제외, 2번 실행(1번은 사실 점검 재실행) 범위:

```text
  N+1 (1000번 왕복)   59~142 ms      ← 왕복 1회 ≈ 60~142 µs
  배치 (1번 왕복)      3.3~9.3 ms     ← 왕복 1회 + 1000개 문자열 처리
  로컬 HashMap        0.15~0.25 ms
  (첫 회: 236~295 ms / 9.4~16.6 ms / 0.46~0.55 ms — JIT 전)
```

- N+1은 같은 회차의 배치보다 14~25배, 로컬보다 수백 배 느렸다. HashMap 조회 자체는 셋 모두 같다(N+1·배치는 서버 스레드에서, 로컬은 호출 스레드에서). 차이는 거의 전부 왕복 횟수다.
- 이것은 같은 기계 안 루프백이다. 실제 DB·다른 서버라면 왕복 1회가 수백 µs~ms라 N+1의 왕복 대기 손해는 더 커진다(표의 같은 DC 왕복 500µs면 1000번 = 0.5초).

## 쓰이는 자료구조·알고리즘

- **AMAT 계산**(🔧): 층별 히트 시간·미스율·페널티로 기댓값을 낸다. 기댓값의 선형성 [math/08-expectation-variance-tails](../../math/08-expectation-variance-tails/2-summary.md).
- **Little의 법칙**: 동시 처리 수 = 처리량 × 지연. 지연을 못 줄이면 겹치는 수를 늘린다. [math/10-queueing-and-littles-law](../../math/10-queueing-and-littles-law/2-summary.md)
- **배칭·파이프라이닝**: 왕복당 일을 늘린다. 크기·시간 트리거 버퍼 [reliability/40-batching-and-round-trips](../../reliability/40-batching-and-round-trips/2-summary.md) · [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md)
- **캐시 계층(애플리케이션)**: 느린 층 앞에 빠른 층을 둔다. AMAT이 그대로 적용된다. [database/30-caching-with-databases](../../database/30-caching-with-databases/2-summary.md) · [database/49-multi-level-caching](../../database/49-multi-level-caching/2-summary.md)
- **B-tree의 높은 팬아웃**: 느린 층(디스크) 접근 횟수 = 트리 높이. 한 번의 느린 접근으로 많은 키를 본다. [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md)

## 적용 — 풀어나가는 법

1. **봉투 뒷면 계산부터.** 요청 하나가 하는 느린 일(왕복·디스크·fsync)의 **횟수**를 세고, 자릿수를 곱한다.
   - 예: 주문 목록 API가 주문 100건마다 고객 조회 1번(같은 DC DB 왕복 0.5ms 가정, 예시) → 50ms. 응답 목표가 100ms면 이미 절반이다.
2. **횟수를 실제로 센다.**

```bash
strace -c -f -p <pid>                 # 시스템 콜 종류별 횟수·시간 (짧게, 운영 부하에 주의)
ss -tin dst <db-ip>                    # rtt:<평균>/<편차> = 커널의 TCP 왕복 추정치(ms, ss(8)). 쿼리 처리 시간은 안 든다
```

   - DB 요청 하나의 시간(왕복 + 쿼리 처리)은 트레이스의 DB 스팬으로 따로 본다.
   - DB 쪽: `pg_stat_statements`의 `calls`가 요청 수보다 수십 배 많은 짧은 쿼리가 N+1의 흔적이다([database/23-orm-and-n-plus-one](../../database/23-orm-and-n-plus-one/2-summary.md)).
   - 애플리케이션: 요청 하나의 쿼리 수·원격 호출 수를 지표로 남기고 테스트에서 단언한다.
3. **고친다** — 왕복 횟수를 줄인다.

```java
// 전: N+1
for (Order o : orders) o.setCustomer(customerRepo.findById(o.getCustomerId()));

// 후: 한 번에 모아 조회 (IN 절, fetch join, 배치 API)
Set<Long> ids = orders.stream().map(Order::getCustomerId).collect(toSet());
Map<Long, Customer> byId = customerRepo.findAllById(ids).stream().collect(toMap(Customer::getId, c -> c));
orders.forEach(o -> o.setCustomer(byId.get(o.getCustomerId())));
```

4. **캐시를 넣었다면 AMAT으로 기대 효과와 한계를 계산한다.** 히트율이 몇 %p 떨어질 때 평균·p99가 어떻게 변하는지 미리 안다.
5. **숫자는 자기 환경에서 다시 잰다.** 표의 숫자는 2012년 무렵 정리이고, 이 호스트의 CPU 안쪽 숫자는 클록 상태에 따라 몇 배 달랐다.

## 장애 시나리오와 대처

### 1. 루프 안 원격 호출 (N+1)

- **현상**: 목록 API가 데이터 건수에 비례해 느려진다. 개발 환경(로컬 DB)에서는 괜찮았다.
- **보이는 형태**: 응답 시간 ≈ 건수 × 왕복 시간. DB CPU는 한가한데 쿼리 수(`calls`)가 폭증. APM 트레이스에 짧은 DB 스팬이 수백 개 줄지어 있다.
- **원인**: 왕복 한 번(같은 DC 수백 µs~ms)이 캐시 안 계산의 수십만 배인데, 그것을 건수만큼 반복했다. 로컬 DB는 왕복이 짧아 문제가 숨었다(실험 2: 루프백에서도 배치의 14~25배).
- **대처**: IN 절·fetch join·배치 API로 왕복 1~몇 번으로 줄인다. 쿼리 수를 테스트로 단언한다.

### 2. 캐시 히트율 몇 %p 하락에 지연이 몇 배

- **현상**: 배포 직후나 캐시 키 형식 변경 후 p50·p99가 함께 뛴다. 캐시 히트율 지표는 "99% → 95%"로 조금 내려갔을 뿐이다.
- **보이는 형태**: DB QPS가 몇 배로 오른다. 응답 지연이 히트율 하락 폭보다 훨씬 크게 늘어난다.
- **원인**: AMAT = 히트 시간 + 미스율 × 페널티. 페널티(DB 5ms, 예시)가 히트(0.1ms, 예시)의 50배면, 미스율 1% → 5%가 평균을 0.15ms → 0.35ms로 2.3배 키운다. DB 부하가 늘어 페널티 자체도 커진다.
- **대처**: 히트율이 아니라 **미스 수(초당)**와 미스 페널티를 함께 본다. 배포 전 캐시 예열, 키 변경 시 이중 읽기. [database/31-cache-key-versioning-and-serialization](../../database/31-cache-key-versioning-and-serialization/2-summary.md)

### 3. 한 건씩 커밋

- **현상**: 10만 건 적재가 몇 분 걸린다. 디스크 대역폭은 한가하다.
- **보이는 형태**: 행당 수 ms로 일정. `iostat`의 쓰기 대역폭은 낮은데 쓰기 요청 수가 많다.
- **원인**: 커밋마다 로그를 디스크에 내리고(fsync) 기다린다. 이 호스트의 4KB 쓰기 + `fdatasync`가 2.6~2.9ms였다. 10만 번이면 4~5분이다.
- **대처**: 배치 커밋, 다중 VALUES·`COPY`. [reliability/40-batching-and-round-trips](../../reliability/40-batching-and-round-trips/2-summary.md) · [os/24-fsync-and-durability](../../os/24-fsync-and-durability/2-summary.md)

### 4. 요청 경로의 대륙 간 호출

- **현상**: 특정 리전 사용자만 응답이 수백 ms 느리다.
- **보이는 형태**: 트레이스에서 외부 API 호출 하나가 150ms 안팎으로 일정. 재시도가 붙으면 그 배수.
- **원인**: 대륙 간 왕복은 표 기준 150ms다(오래된 표의 근사 예시). 그중 전파 지연은 두 지점의 거리와 매체(광섬유) 속도가 정하는 하한이라 코드로 줄일 수 없다. 실제 RTT는 경로 우회·장비 처리가 더해져 그 하한보다 크다. 이것을 요청마다, 또는 순차로 여러 번 했다.
- **대처**: 같은 리전 사본·캐시, 비동기화(요청 경로 밖으로), 여러 호출을 병렬로. [network/03-latency-bandwidth-bdp](../../network/03-latency-bandwidth-bdp/2-summary.md)

## 핵심 문장

- 지연 표의 개별 숫자는 세대마다 바뀐다. 오래 가는 것은 ns·µs·ms 자릿수와 층 사이의 비율이다.
- 캐시 안 연속 처리 원소 하나가 약 1ns라면, 같은 DC 왕복 한 번(표 500µs)은 약 50만 개 처리와 맞먹는다. 루프 안 원격 호출 한 번이 루프의 계산 전부를 압도한다.
- AMAT = 히트 시간 + 미스율 × 미스 페널티. 페널티가 히트보다 수십 배 크면 미스율 몇 %p가 평균을 몇 배로 바꾼다.
- 배치·파이프라이닝·프리페치는 왕복·DRAM 접근 한 번의 지연을 줄이지 않는다. 대기를 겹치거나 앞당겨 처리량을 올리고, 그래서 전체 완료 시간과 작업이 겪는 대기(프리페치는 나중 접근을 히트로 바꾼다)는 줄어든다.
- 숫자는 자기 환경에서 다시 잰다. 이 호스트에서는 클록 상태 때문에 CPU 안쪽 지연이 표보다 몇 배 컸고, SSD는 표와 같은 자릿수였다.

## 관련 주제·근거

- 선행: [11-memory-hierarchy-and-locality](../11-memory-hierarchy-and-locality/2-summary.md)(층별 지연 측정) · [12-cache-organization](../12-cache-organization/2-summary.md)
- 후속: [14-cache-coherence-and-memory-ordering](../14-cache-coherence-and-memory-ordering/2-summary.md) · [15-io-devices-interrupts-dma](../15-io-devices-interrupts-dma/2-summary.md) · [16-storage-media-workload](../16-storage-media-workload/2-summary.md)
- 다른 영역
  - [os/02-system-calls](../../os/02-system-calls/2-summary.md) · [os/07-threads-and-context-switch](../../os/07-threads-and-context-switch/2-summary.md) · [os/24-fsync-and-durability](../../os/24-fsync-and-durability/2-summary.md)
  - [network/03-latency-bandwidth-bdp](../../network/03-latency-bandwidth-bdp/2-summary.md) · [network/22-nagle-and-delayed-ack](../../network/22-nagle-and-delayed-ack/2-summary.md)
  - [database/23-orm-and-n-plus-one](../../database/23-orm-and-n-plus-one/2-summary.md) · [database/30-caching-with-databases](../../database/30-caching-with-databases/2-summary.md) · [database/49-multi-level-caching](../../database/49-multi-level-caching/2-summary.md) · [database/31-cache-key-versioning-and-serialization](../../database/31-cache-key-versioning-and-serialization/2-summary.md)
  - [reliability/40-batching-and-round-trips](../../reliability/40-batching-and-round-trips/2-summary.md) · [reliability/34-tail-latency-and-stragglers](../../reliability/34-tail-latency-and-stragglers/2-summary.md)
  - [math/08-expectation-variance-tails](../../math/08-expectation-variance-tails/2-summary.md) · [math/10-queueing-and-littles-law](../../math/10-queueing-and-littles-law/2-summary.md)
- 출처
  - jboner, "Latency Numbers Every Programmer Should Know" gist — "Latency Comparison Numbers (~2012)", Credit: Jeff Dean, Originally by Peter Norvig <https://gist.github.com/jboner/2841832> (2차 정리)
  - P. Norvig, "Teach Yourself Programming in Ten Years" — "Approximate timing for various operations on a typical PC" <http://norvig.com/21-days.html#answers>
  - CS:APP 3판 6.1 Storage Technologies · 6.4.7 Performance Impact of Cache Parameters — 절 제목은 목차 PDF로 확인, 본문 미확인
  - Hennessy·Patterson, 『Computer Architecture: A Quantitative Approach』 — AMAT 식, 부록 B [?]
  - Drepper 2007 §3.3.2 그림 3.10·3.11(작업 집합별 접근 시간), §6.3(프리페치) <https://people.freebsd.org/~lstewart/articles/cpumemory.pdf>
- 실험 목록(환경: i7-13700HX, Linux 7.0.0-34-generic, gcc 13.3.0 `-O2`, JDK 21.0.12, 측정 중 클록 약 0.8~0.93GHz, ext4 on NVMe)
  - 실험 1 `lat.c`: 함수 호출·`getppid` 시스템 콜·루프백 TCP 64B 왕복·4KB `O_DIRECT` 무작위 읽기(64MB 임시 파일, 끝나면 삭제)·4KB `pwrite`+`fdatasync`, `taskset -c 2,4`, 5회(2회는 사실 점검 재실행)
  - 실험 2 `NPlusOne.java`: id 1000개 N+1 vs 배치 vs 로컬 HashMap, 컨테이너 `--network none --cpus=2 --cpuset-cpus=2,4`, 5회 × 2번 실행
  - L1·L2·DRAM 값은 11번 실험 1(`chase.c`)
