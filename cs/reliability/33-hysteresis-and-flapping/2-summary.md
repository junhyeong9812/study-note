# reliability/33-hysteresis-and-flapping — 방향별 임계값 분리로 진동 방지 — 정리 (힌트)

## 해결하는 문제

자동 제어는 "값이 기준을 넘으면 A, 아니면 B"로 시작한다.\
그런데 측정값은 늘 흔들린다. 기준 근처에서 흔들리면 상태가 A↔B를 계속 오간다.\
오갈 때마다 비용이 든다. 인스턴스 기동, 알림 발송, 서킷 개폐, 라우팅 변경.

```text
 CPU%  71 69 72 68 71 70.5 69 ...   기준 70 하나
 판정  +1 −1 +1 −1 +1 +1  −1 ...   → 스케일 아웃·인을 매 표본마다 (flapping)

 기준을 방향별로 둘: 올릴 때 75, 내릴 때 45
 판정  ·  ·  ·  ·  ·  ·   ·  ...   → 45~75 사이에서는 지금 상태 유지
```

쉬운 예: 에어컨 온도 조절기다.
- "26도 넘으면 켜고 26도 아래면 끈다"면 26도 근처에서 몇 초마다 켜졌다 꺼진다.
- 그래서 "27도에 켜고 25도에 끈다". 25~27도에서는 지금 상태를 유지한다.

똑같은 구조다.\
실무 예: 오토스케일러의 스케일 아웃·인, 경보의 발화·해소, 서킷 브레이커의 열림·닫힘, 헬스체크의 대상 제외·복귀, 동적 배열의 확장·축소.

- 기초(동적 배열 16/4 예, CPU 팬 80/70 예, 물리학 이름의 유래, thrashing과의 구분, 슈미트 트리거, 오토스케일·서킷·헬스체크의 자리)는 원본 [systems/Hysteresis](../../systems/Hysteresis/2-summary.md)에 있다.
- 이 노트는 운영 시스템의 세 자리(**오토스케일·알람·서킷**)에서 flapping이 어떻게 생기고, 밴드·시간 창·연속 횟수로 어떻게 줄이는지 실험으로 보인다.

## 동작·원리

### 1. 히스테리시스 = 상태에 메모리 1비트

```text
 단일 임계:  상태 = f(입력)                       입력만 보면 답이 나온다
 히스테리시스: 상태 = f(입력, 이전 상태)

       상태
   ON  │        ┌────────────────
       │        │      ▲
       │   ◀────┼──────┘           밴드 안(45~75)에서는 이전 상태를 유지
   OFF │────────┘
       └────────┼──────┼────────▶ 입력
               45     75
            내릴 때  올릴 때
```

- *hysteresis band(히스테리시스 밴드)*: 올리는 임계와 내리는 임계 사이의 구간. 이 안에서는 상태를 바꾸지 않는다.
- *flapping(진동)*: 상태가 짧은 간격으로 계속 바뀌는 현상. Kubernetes HPA 문서는 레플리카 수가 자주 요동치는 것을 thrashing 또는 flapping이라 부르고 "cybernetics의 hysteresis 개념과 비슷하다"고 적는다.

### 2. 진동을 막는 세 축

```text
 ① 값의 축   — 밴드: 올림 임계 ≠ 내림 임계               (오토스케일 75/45, 경보 발화·해소 임계)
 ② 시간의 축 — 지속 조건·쿨다운·안정화 창                (Prometheus for / keep_firing_for, HPA 축소 안정화 창)
 ③ 횟수의 축 — 연속 N번이어야 전환                       (K8s probe failureThreshold 3 / successThreshold 1)
```

- 셋 다 "한 번 흔들린 값으로는 바꾸지 않는다"는 같은 생각이다. 실무에서는 섞어 쓴다.
- 대가도 같다. 반응이 늦어진다. 밴드가 넓을수록, 창이 길수록 진짜 변화에도 늦게 반응한다.

### 3. 밴드는 "내 행동이 만드는 변화"보다 넓어야 한다

```text
 레플리카 4개, CPU 50%   → 하나 줄이면  50 × 4/3 = 66.7%
 레플리카 3개, CPU 66.7% → 하나 늘리면  66.7 × 3/4 = 50%
 내림 임계 55, 올림 임계 65 이면?  50 → 줄임 → 66.7 → 늘림 → 50 → …   행동 한 번에 밴드(55~65)를 통째로 건너뛰어 진동
```

- 측정 잡음만이 아니라 **제어 행동 자체가 측정값을 움직인다.** 레플리카 n개에서 하나를 빼면 평균 CPU가 n/(n−1)배가 된다.
- 그래서 밴드 폭(비율)이 그 배율보다 커야 한다. 아래 실험의 75/45는 n=4 → 3에서 45 × 4/3 = 60 < 75라 행동 한 번으로 반대 임계를 넘지 않는다.
- 레플리카가 적을수록 배율이 크다(2 → 1이면 2배). 작은 서비스일수록 넓은 밴드나 긴 축소 창이 필요하다.

### 4. Kubernetes HPA의 장치

```text
 desiredReplicas = ceil(currentReplicas × currentMetric / targetMetric)
 ① 허용 오차: |currentMetric / targetMetric − 1| ≤ 0.1 이면 아무것도 안 한다(기본 10%)
 ② 축소 안정화 창: 축소할 때 지난 300초(기본)의 권고 중 **최댓값**을 쓴다(rolling max)
    확대에는 기본 창이 없다(0초) — 늘릴 때는 빠르게, 줄일 때는 천천히
```

- 출처: Kubernetes 문서 "Horizontal Pod Autoscaling"(2026-10-01 열람) — 알고리즘, Stability of workload scale, Stabilization window, Tolerance.
  - 허용 오차 기본값은 kube-controller-manager의 `--horizontal-pod-autoscaler-tolerance`로 바꾼다. HPA 객체별 `tolerance` 필드는 기능 게이트 `HPAConfigurableTolerance`(알파 1.33, 베타 1.35 — 기본 꺼짐, GA 1.37) 뒤에 있다.
  - 축소 안정화 기본값은 `--horizontal-pod-autoscaler-downscale-stabilization`(5분) 또는 `behavior.scaleDown.stabilizationWindowSeconds`.
- ①은 값의 축(대칭 밴드), ②는 시간의 축이다. 둘을 함께 쓴다.

### 5. 경보와 서킷의 장치

- **Prometheus 경보 규칙**(Prometheus 문서 "Alerting rules", 3.x)
  - `for`: 조건이 처음 참이 된 뒤 이 시간 동안 **매 평가마다** 계속 참이어야 firing이 된다. 그 전은 pending이다.
  - `keep_firing_for`: 조건이 마지막으로 참이었던 뒤에도 이 시간 동안 firing을 유지한다. 문서는 용도를 flapping 경보와 데이터 공백으로 인한 거짓 해소 방지로 적는다.
  - 발화(for)와 해소(keep_firing_for)를 따로 늦추므로 시간 축의 히스테리시스다.
  - 임계값 자체를 방향별로 다르게 하려면 표현식이 **이전 경보 상태**를 봐야 한다. 규칙을 둘로 나누기만 하면 각 규칙이 자기 식으로 따로 발화·해소할 뿐이다. Prometheus는 pending·firing 경보를 `ALERTS{alertname=…, alertstate=…}` 시계열로 저장하므로, 예컨대 "2% 초과, 또는 이미 firing이면 1% 초과"처럼 그 시계열을 식에 넣어 상태를 만든다(개념 예).
- **서킷 브레이커**(Resilience4j 2.4.0 `CircuitBreakerConfig` 기본값)
  - 열림: 슬라이딩 창(기본 100콜, 최소 100콜) 실패율이 50% 이상이면 OPEN.
  - 열림 유지: `waitDurationInOpenState` 기본 60초 — 시간 축.
  - 닫힘: HALF_OPEN에서 허용 콜 10개(`permittedNumberOfCallsInHalfOpenState`)의 결과로 판정 — 횟수 축. 성공 한 번으로 닫지 않는다.
  - 상태 기계 자세한 동작은 [10-circuit-breaker](../10-circuit-breaker/2-summary.md).
- **Kubernetes 프로브**(core/v1 `Probe` 필드 주석): `failureThreshold` 기본 3(연속 실패 3번이어야 실패), `successThreshold` 기본 1(liveness·startup은 1이어야 한다).

### 실험: 같은 잡음, 다른 제어 규칙

- 모의(시드 고정 — 실행마다 같다): 15초마다 표본, 2시간(480표본).
- 부하 L(t) = 240 + 30·sin(2πt/1시간) + 잡음 N(0, 15). 레플리카 1개 = 100. CPU% = L / 레플리카 수. 시작 3개.
- 오토스케일 규칙 6가지. 경보: 오류율 = 0.95% + N(0, 0.15%), 임계 1%.
  - 경보는 Prometheus 평가 규칙(`rules/alerting.go`)을 흉내 냈다. 15초 평가에서 `for: 1m`은 첫 참 평가 뒤 60초가 지난 **5번째** 연속 참 평가에서 firing이 된다. `keep_firing_for: 5m`은 첫 거짓 평가 뒤 300초가 지나면 해소된다.
  - 세는 것은 **발화(firing 진입) 횟수**다. 실제로 사람에게 가는 알림 수는 Alertmanager의 그룹화·`group_wait`(기본 30초)·`repeat_interval`(기본 4시간)에 따라 달라지고, 그 전에 해소되면 안 갈 수도 있다.

핵심 코드(전체: 실험 목록의 `Hysteresis.java`):

```java
sim("단일 임계 70%",        (n, c, s) -> c > 70 ? n + 1 : c < 70 ? n - 1 : n, L);
sim("밴드 75/45",           (n, c, s) -> c > 75 ? n + 1 : c < 45 ? n - 1 : n, L);
// HPA 식: 허용 오차 안이면 그대로, 축소는 지난 창의 최대 권고
int desired = Math.abs(ratio - 1.0) <= tol ? n : (int) Math.ceil(n * ratio);
if (desired < n) desired = Math.min(n, maxOfRecentRecommendations);
// 경보: for = 연속 k평가 참이어야 발화(for 1분 = 15초 간격 5평가), keep = 거짓이 keep표본 넘게 이어져야 해소
if (!firing && pending >= Math.max(1, forSteps)) { firing = true; notifications++; }
else if (firing && !cond && sinceFalse > keepSteps) firing = false;
```

(실험, JDK 21 eclipse-temurin, 모의 시간, 2026-10-01 — 시드 1·2·3 중 시드 1 출력. 시드 2·3의 범위는 아래 관찰에. 경보 부분은 2026-10-02에 `for` 1분 = 5평가로 고쳐 다시 돌렸다)

```text
시드 1 — 오토스케일링(시작 레플리카 3)
  단일 임계 70% (>70 +1, <70 -1)         스케일 변경 480회 · 방향 반전 411회 · 평균 레플리카 3.43 · CPU>90% 표본  58
  밴드 75/45 (>75 +1, <45 -1)          스케일 변경   7회 · 방향 반전   4회 · 평균 레플리카 4.11 · CPU>90% 표본   0
  밴드 75/45 + 축소 쿨다운 5분               스케일 변경   5회 · 방향 반전   2회 · 평균 레플리카 4.12 · CPU>90% 표본   0
  HPA식 target 60%, 허용오차 0, 창 0       스케일 변경 120회 · 방향 반전 114회 · 평균 레플리카 4.48 · CPU>90% 표본   0
  HPA식 target 60%, 허용오차 0.1, 창 0     스케일 변경  40회 · 방향 반전  38회 · 평균 레플리카 4.31 · CPU>90% 표본   0
  HPA식 target 60%, 허용오차 0.1, 축소창 5분  스케일 변경   4회 · 방향 반전   3회 · 평균 레플리카 4.67 · CPU>90% 표본   0
시드 1 — 알람(오류율 > 1%, 평균 0.95% · 표준편차 0.15%)
  for 없음, keep 없음                    발화 113회 · firing 표본 186
  for 1분(연속 5평가)                     발화   2회 · firing 표본   3
  for 1분 + keep_firing_for 5분        발화   1회 · firing 표본 373
```

- 관찰 1 — 단일 임계는 480표본 **전부**에서 레플리카를 바꿨다(시드 1·2·3 모두 480회). 그러고도 CPU>90% 표본이 57~65개다. 진동하느라 부하를 따라가지 못했다.
- 관찰 2 — 밴드 75/45는 변경 7~11회, CPU>90% 0. 축소 쿨다운 5분을 더하면 5~9회.
- 관찰 3 — HPA 식에서 허용 오차 0.1만 켜면 변경이 120 → 40회(시드 1)로 줄지만 여전히 반전이 대부분이다. 축소 안정화 창 5분을 더하자 4~5회로 줄었다. 대가로 평균 레플리카가 4.30~4.36(창 0) → 4.65~4.75(창 5분)로 늘었다. 안정의 값은 자원이다.
- 관찰 4 — 경보: `for` 없이는 2시간에 발화 110~115회다. `for` 1분으로 1~5회. 여기에 `keep_firing_for` 5분을 더하면 발화는 1회지만 **480표본 중 266~429표본 동안 firing인 채**였다. 평균 0.95%가 임계 1% 바로 아래인 신호에서는 해소가 계속 미뤄진다. keep을 길게 잡으면 "해소됨"이 안 보인다.
- 해석: 임계값을 신호의 평균 바로 옆에 둔 것이 근본 문제다. 시간 축 장치는 증상을 줄이지만, 신호와 임계의 거리가 잡음에 비해 가까우면 어떤 설정도 "자주 울림"과 "계속 울림" 사이에서 고를 뿐이다.

## 쓰이는 자료구조·알고리즘

- **2상태 기계 + 메모리 1비트** — 히스테리시스의 본체. 서킷 브레이커는 3상태(CLOSED·OPEN·HALF_OPEN) 기계다.
- **슬라이딩 창 최댓값(rolling max)** — HPA 축소 안정화. 창 안 권고들의 최댓값을 쓴다. 단조 덱으로 O(1) 갱신이 가능하다(덱은 [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)).
- **연속 카운터** — `for`(연속 참 시간), 프로브 `failureThreshold`(연속 실패 수). 한 번 끊기면 0으로 돌아간다.
- **링 버퍼 슬라이딩 창** — Resilience4j의 개수 기반 창(최근 N콜의 실패율). [11-rate-limiter](../11-rate-limiter/2-summary.md)의 창 카운터와 같은 재료다.
- **지수 이동 평균(EWMA)** — 입력 자체를 평활해 경계 근처 흔들림을 줄인다. 평활은 지연을 더한다.

## 적용 — 풀어나가는 법

### 1. 순서

1. **잡음의 크기를 잰다** — 지표의 표준편차·분위수. 임계가 평균에서 잡음 몇 배 떨어져 있나.
2. **행동이 지표를 얼마나 바꾸나** — 레플리카 하나를 빼면 CPU가 n/(n−1)배. 밴드는 그보다 넓게.
3. **방향별 비용이 다르면 비대칭으로** — 늘리기는 빠르게(창 0), 줄이기는 천천히(창 5분). 과부하가 과잉 자원보다 비싸기 때문이다.
4. **시간 축을 더한다** — 경보 `for`, 축소 안정화 창, 서킷의 열림 유지 시간.
5. **flapping 자체를 지표로** — 상태 전환 횟수를 세고 경보를 건다(시간당 스케일 이벤트 수, 경보 해소·재발 횟수).

### 2. 히스테리시스 판정기 (Java)

```java
/** 올림 임계 > 내림 임계. 밴드 안에서는 이전 상태를 유지한다. */
final class Hysteresis {
    private final double up, down; private boolean high;
    Hysteresis(double up, double down) {
        if (up <= down) throw new IllegalArgumentException("up must be > down");
        this.up = up; this.down = down;
    }
    boolean update(double x) {
        if (!high && x > up) high = true;
        else if (high && x < down) high = false;
        return high;                      // up과 down 사이면 바뀌지 않는다
    }
}
```

### 3. 설정 예

```yaml
# Kubernetes HPA (autoscaling/v2) — 늘리기는 즉시, 줄이기는 5분 창
behavior:
  scaleUp:
    stabilizationWindowSeconds: 0
  scaleDown:
    stabilizationWindowSeconds: 300
---
# Prometheus 경보 — 발화는 5분 지속, 해소는 2분 유지 (값은 예시)
- alert: HighErrorRate
  expr: sum(rate(http_requests_total{code=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.02
  for: 5m
  keep_firing_for: 2m
```

### 4. 진단

```bash
# HPA가 얼마나 자주 바꾸나 — 이벤트의 "New size" 줄을 본다
# 같은 이벤트가 반복되면 한 줄로 합쳐지고 "(x3 over 10m)"처럼 횟수가 붙는다 → 줄 수(grep -c)는 하한일 뿐, 횟수 칸도 더한다
kubectl describe hpa api | grep 'New size'
kubectl get events --field-selector involvedObject.kind=HorizontalPodAutoscaler --sort-by=.lastTimestamp | tail
```

- PromQL 개념 예: `changes(kube_horizontalpodautoscaler_status_desired_replicas{horizontalpodautoscaler="api"}[1h])` — 한 시간 동안 **수집된 표본에서 관측된** 원하는 레플리카 수의 변경 횟수(kube-state-metrics 지표). 두 스크레이프 사이에 바뀌었다 돌아온 것은 세지 못한다. 경보 쪽은 Alertmanager로 나간 알림 수(FIRING·RESOLVED 교대 횟수)를 경보 이름별로 센다.

## 장애 시나리오와 대처

### 1. 오토스케일 flapping (⚠)

- 현상: 파드 수가 몇 분마다 늘었다 줄었다 한다. 새 파드가 준비되기 전에 다시 줄어든다. 그 사이 지연이 튄다.
- 보이는 형태: HPA 이벤트에 `New size`가 짧은 간격으로 교대로. 실험의 단일 임계처럼 방향 반전이 대부분.
- 원인: 올림·내림 기준이 같거나 너무 가깝다. 행동 자체가 지표를 반대 임계 너머로 민다(n/(n−1)). 축소 안정화 창을 0으로 줄였다.
- 대처: 밴드를 행동 배율보다 넓게, 축소 안정화 창(기본 300초) 유지, 허용 오차(기본 10%). 줄이는 쪽만 느리게.

### 2. 경보 flapping (⚠)

- 현상: 같은 경보가 한 시간에 수십 번 울렸다 꺼진다. 온콜이 경보를 무시하기 시작한다.
- 보이는 형태: 알림 채널에 FIRING·RESOLVED가 교대로. 지표가 임계 바로 근처에서 흔들린다(실험: 2시간 발화 110~115회).
- 원인: `for`가 없거나 짧다. 임계가 평소 값의 잡음 범위 안에 있다.
- 대처: `for`로 발화를 늦추고(실험: `for` 1분이면 1~5회), Alertmanager 그룹화로 전송을 묶고, 필요하면 `keep_firing_for`로 해소를 늦춘다. 그보다 먼저 임계를 평소 분포에서 떼어 놓는다(SLO 번 레이트 경보처럼 기준 자체를 바꾼다 — [43-alerting-and-on-call](../43-alerting-and-on-call/2-summary.md)).

### 3. 해소 지연을 너무 길게 → 경보가 안 꺼진다

- 현상: 장애가 끝났는데 경보가 몇 시간째 firing이다. 다음 장애가 와도 새 알림이 오지 않는다.
- 보이는 형태: 실험의 `keep_firing_for` 5분 — 발화 1회, 480표본 중 266~429표본 firing.
- 원인: 신호가 임계 근처를 계속 오가는데 해소 유지 시간이 흔들림 주기보다 길다.
- 대처: keep을 짧게 하거나 해소 임계를 따로 둔다(발화 > 2%, 해소 < 1% 같은 밴드 — 식이 `ALERTS` 시계열로 이전 firing 상태를 참조해야 한다). 오래 firing인 경보 자체를 점검 대상으로 삼는다.

### 4. 서킷 브레이커 flapping (⚠)

- 현상: 하류가 반쯤 아픈 동안 서킷이 OPEN ↔ HALF_OPEN ↔ CLOSED를 계속 돈다. 닫힐 때마다 몰린 요청이 하류를 다시 넘어뜨린다.
- 보이는 형태: 상태 전이 이벤트가 열림 유지 시간 주기로 반복. 닫힌 직후마다 오류율 스파이크.
- 원인: 반열림 시험이 너무 적은 콜로 판정하거나(성공 한 번에 닫기), 열림 유지 시간이 하류 회복 시간보다 짧다. 닫힌 직후 전체 트래픽이 한꺼번에 돌아간다.
- 대처: 반열림 허용 콜 수를 충분히(Resilience4j 기본 10), 열림 유지 시간을 하류 회복 특성에 맞게(기본 60초), 닫힌 뒤 트래픽을 점진적으로 늘린다. 재시도 예산으로 몰림을 줄인다([06](../06-retry-backoff-jitter/2-summary.md)).

### 5. 헬스체크 flapping으로 대상이 들락날락

- 현상: 로드 밸런서가 한 인스턴스를 뺐다 넣었다 반복한다. 넣을 때마다 그 인스턴스로 몰린 요청이 실패한다.
- 보이는 형태: 대상 상태 변경 로그가 짧은 간격으로 교대. 인스턴스는 GC·부하로 가끔 늦게 응답한다.
- 원인: 실패 1번에 빼고 성공 1번에 넣는다(횟수 축 히스테리시스 없음). 또는 프로브 타임아웃이 평소 지연 분포의 꼬리 안에 있다.
- 대처: 빼기는 연속 실패 N번(K8s `failureThreshold` 기본 3), 넣기는 연속 성공 M번(readiness는 `successThreshold`를 1보다 크게 둘 수 있다). 프로브 타임아웃을 평소 p99보다 넉넉하게.

## 핵심 문장

- 히스테리시스는 상태에 메모리 1비트를 더해, 밴드 안에서는 이전 상태를 유지하게 하는 것이다.
- 진동을 막는 축은 셋이다 — 값(밴드), 시간(지속·창·쿨다운), 횟수(연속 N번).
- 밴드는 잡음보다, 그리고 내 행동이 지표를 바꾸는 폭(레플리카 n → n−1이면 n/(n−1)배)보다 넓어야 한다.
- 안정의 값은 반응 속도와 자원이다. 실험에서 축소 창 5분은 변경을 40 → 4회로 줄였지만 평균 레플리카를 늘렸다.
- 임계가 평소 값의 잡음 범위 안에 있으면 시간 장치는 "자주 울림"과 "계속 울림" 사이에서 고를 뿐이다. 임계와 신호의 거리부터 본다.

## 관련 주제·근거

- 선행
  - [10-circuit-breaker](../10-circuit-breaker/2-summary.md) — 3상태 기계, 반열림 시험
  - 원본 [systems/Hysteresis](../../systems/Hysteresis/2-summary.md) — 동적 배열·CPU 팬 예, 슈미트 트리거, 오토스케일·서킷·헬스체크의 자리, debounce·smoothing·cooldown
- 후속·연결
  - [41-autoscaling](../41-autoscaling/2-summary.md) — 지표 기반 확장·반응 지연·쿨다운
  - [43-alerting-and-on-call](../43-alerting-and-on-call/2-summary.md) — 증상 기반·번 레이트 경보
  - [02-slo-sli-error-budget](../02-slo-sli-error-budget/2-summary.md) — 경보 기준을 SLO로
  - [data-structure/01-dynamic-array](../../data-structure/01-dynamic-array/2-summary.md) — 확장·축소 임계 분리의 원형
  - [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md) — 셰딩 진입·해제에도 같은 문제
- 근거
  - Kubernetes 문서 "Horizontal Pod Autoscaling"(알고리즘 식, tolerance 0.1, 축소 안정화 300초, 확대 창 0, flapping·hysteresis 언급) <https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/> · 기능 게이트 `HPAConfigurableTolerance`(website 저장소 feature-gates 문서)
  - Prometheus 문서 "Alerting rules"(`for`, `keep_firing_for` — flapping 방지 용도, `ALERTS` 시계열) <https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/> · 평가 코드 `rules/alerting.go`(`ts.Sub(a.ActiveAt) >= holdDuration`이면 firing, `ts.Sub(a.KeepFiringSince) < keepFiringFor` 동안 유지) <https://github.com/prometheus/prometheus/blob/main/rules/alerting.go>
  - Alertmanager 문서 "Configuration"(`group_wait` 기본 30s, `repeat_interval` 기본 4h) <https://prometheus.io/docs/alerting/latest/configuration/> · Prometheus `changes()` 문서
  - Resilience4j v2.4.0 `CircuitBreakerConfig.java` 기본값(실패율 50, 열림 60초, 반열림 10콜, 최소 100콜, 창 100) <https://github.com/resilience4j/resilience4j>
  - Kubernetes API `core/v1` `Probe` 필드 주석(failureThreshold 기본 3, successThreshold 기본 1) <https://github.com/kubernetes/api/blob/master/core/v1/types.go>
- 실험 목록
  - 오토스케일 규칙 6가지 + 경보 규칙 3가지 — `Hysteresis.java`(scratchpad `rel/12/`, 경보를 `for` 1분 = 5평가로 고친 판은 `rel/fa-28/h33/`), JDK 21 temurin, 모의 시간, 시드 1·2·3(결정적 — 두 번 돌려 출력 동일)
