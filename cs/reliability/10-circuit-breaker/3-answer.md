# reliability/10-circuit-breaker — 정답

## 정답

### 1. 브레이커가 없을 때의 손해

- 사용자: 타임아웃 × 시도 수만큼 기다린 뒤 실패한다.
- 우리: 그동안 스레드·커넥션이 묶여 무관한 요청까지 느려진다(장애가 번진다).
- 하류: 회복하려는 중에 계속 요청을 맞아 회복이 늦어진다.
- 브레이커가 정하지 않는 것: **열렸을 때 무엇을 줄지(폴백)**. 정하지 않으면 빠른 에러가 될 뿐이다.

### 2. 상태와 특수 상태

```text
 CLOSED ──(실패율 또는 느린 비율 ≥ 임계, 기록 ≥ 최소)──> OPEN
 OPEN ──(대기 경과)──> HALF_OPEN
 HALF_OPEN ──(허용 N건의 비율 < 임계)──> CLOSED
 HALF_OPEN ──(허용 N건의 비율 ≥ 임계)──> OPEN
```

- `METRICS_ONLY`: 기록만 하고 열지 않는다(새 브레이커를 관찰만 할 때).
- `DISABLED`: 항상 통과, 기록 없음.
- `FORCED_OPEN`: 항상 차단(폴백 경로 시험, 하류 점검 중 수동 차단).
- 이 셋에서 나오려면 전이를 명시적으로 일으키거나 reset해야 한다(Resilience4j 문서).

### 3. 최소 표본과 ≥

(실험 A, Resilience4j 2.4.0, 2026-10-01)

```text
t=  194ms 호출9(X)     실패      state=CLOSED
          ** 전이 State transition from CLOSED to OPEN
t=  205ms 호출10       성공      state=OPEN
```

- 9건째: CLOSED. 기록이 최소 10에 못 미쳐 비율을 계산하지 않는다.
- 10건째(성공): 5/10 = 50%. 비교가 ≥라 **열린다**. 그 호출 자체는 이미 실행돼 성공했다.

### 4. OPEN → HALF_OPEN은 호출이 일으킨다

- 대기가 지나도 `getState()`는 **OPEN**이다(실험 출력 "(550ms 대기 …) state=OPEN").
- 다음 호출이 허가를 요청할 때 HALF_OPEN으로 바뀐다. `automaticTransitionFromOpenToHalfOpenEnabled=true`면 감시 스레드가 대기 끝에 전이시킨다(문서).

### 5. 반열림 판정

(실험 A, 2026-10-01)

```text
  → 반열림 4건 중 실패 1건(25%) < 50%: CLOSED
  → 반열림 4건 중 실패 2건(50%) >= 50%: OPEN
```

- 1건 실패: **닫힌다**. 2건: **다시 연다**. 허용 4건이 다 끝난 뒤 비율로 판정한다.
- 원본 직접 구현은 "하나라도 실패하면 즉시 OPEN"이다. 더 보수적이다. Resilience4j는 반열림 표본에도 같은 임계(비율)를 쓴다.

### 6. 기본값

(실험, `CircuitBreakerConfig.ofDefaults()`, Resilience4j 2.4.0)

```text
failureRateThreshold=50.0 slowCallRateThreshold=100.0 slowCallDurationThreshold=PT1M slidingWindowType=COUNT_BASED slidingWindowSize=100 minimumNumberOfCalls=100 permittedNumberOfCallsInHalfOpenState=10 waitDurationInOpenState=60000ms automaticTransition=false maxWaitDurationInHalfOpenState=PT0S
```

- 개수 창 100, 최소 100, 실패율 50%, 대기 60초, 반열림 10건.
- 느린 호출: 60초 넘어야 느림, 그 비율이 100%여야 열림. **기본으로는 느린 하류를 사실상 못 끊는다**.
- 실험 B처럼 `slowCallDurationThreshold(100ms)`·`slowCallRateThreshold(50)`로 낮추면 실패율 0%에서도 열린다.

### 7. 400류를 세나

(실험 C, 2026-10-01)

```text
  ignore=false state=OPEN 기록된 호출=10 실패=10
  ignore=true  state=CLOSED 기록된 호출=0 실패=0
```

- 기본: 모든 예외를 실패로 세서 **열린다**.
- `ignoreExceptions(IllegalArgumentException.class)`: 기록조차 안 해 CLOSED.

### 8. 플래핑

(실험 D, 2026-10-01, 실행마다 다르다 — 집필 3회·점검 3회에서 창 4는 OPEN 전이 53~54회, 하류 호출 251~314)

```text
  창=4 최소=2 반열림허용=1 → OPEN 전이 53회, 하류로 간 호출 314, 차단 2174
  창=100 최소=50 반열림허용=10 → OPEN 전이 0회, 하류로 간 호출 2604, 차단 0
```

- 의심: 작은 창, 작은 최소 표본, 반열림 허용 1건, 짧은 대기.
- 창 4: 3초에 53~54번 열렸고, 70%가 성공할 요청인데 대부분(2174건) 차단됐다.
- 창 100: 표본이 커서 실패율이 30% 근처에 머물고 임계 50%에 닿지 않았다.
- 대처: 창·최소·반열림 허용을 키우고, 여는 조건과 닫는 조건을 분리한다(히스테리시스).

### 9. Envoy circuit breaking

- Envoy의 것은 클러스터별 **동시성 상한**이다: 최대 연결·대기 요청·요청·재시도 수(기본 1024·1024·1024·3). 넘치면 해당 `*_overflow` 통계가 오르고, 결과는 한도마다 다르다(Envoy circuit breaking 문서).
  - 대기 요청·요청 한도 초과: 그 요청을 버린다(HTTP면 응답에 `x-envoy-overloaded` — 라우터 필터 문서).
  - 연결 한도 초과: 새 연결을 안 만들 뿐, 요청은 대기 요청 목록에서 빈 연결을 기다릴 수 있다.
  - 재시도 한도 초과: 원래 요청이 아니라 **재시도**를 하지 않는다.
- 실패율로 여닫는 상태 기계가 아니다. 이름만 같다. 오히려 벌크헤드(28)에 가깝다.
- 실패가 잦은 호스트를 일정 시간 빼는 기능은 **outlier detection**이다.

### 10. AWS의 반론

- 브레이커는 시스템에 modal behavior를 들여와 **시험하기 어렵다**.
- 회복에 **상당한 시간을 더할 수 있다**(열림 대기 동안 하류가 회복해도 차단).
- 대신: 로컬 **토큰 버킷으로 재시도를 묶는다**. 토큰이 있으면 모두 재시도하고, 바닥나면 고정 속도로만 재시도한다. AWS SDK에 2016년 추가(Builders' Library).
