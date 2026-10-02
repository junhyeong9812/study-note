# reliability/41-autoscaling — 지표 기반 확장·반응 지연·쿨다운(안정화 창) — 정리 (힌트)

## 해결하는 문제

트래픽은 하루에도 몇 배씩 출렁인다. 피크에 맞춰 늘 켜 두면 돈이 들고, 평균에 맞추면 피크에 넘친다.\
오토스케일링은 지표를 보고 인스턴스 수를 자동으로 맞춘다. 그런데 **늦게 반응하고**, **출렁이면 같이 출렁인다**.

쉬운 예: 버스 회사의 배차다.
- 정류장 줄이 길어지면 버스를 더 보낸다(스케일 아웃). 하지만 차고지에서 정류장까지 20분 걸린다(인스턴스 준비 시간).
- 줄이 갑자기 몇 배가 되면 버스가 오기 전 20분 동안 사람들이 기다리다 떠난다(타임아웃).
- 줄이 잠깐 짧아졌다고 버스를 바로 회수하면, 다음 파도 때 다시 20분을 기다린다(플래핑).

똑같은 구조다.\
실무 예: Kubernetes HPA, 클라우드 VM 오토스케일링 그룹, 서버리스 동시성 확장, 큐 적체 기반 워커 확장.

원본 [server-design/09-capacity-slo](../../systems/server-design/09-capacity-slo.md) §4(지표 선택 표, 함정 표, 스케일링이 답이 아닌 경우)가 기초다. 이 노트는 HPA의 실제 알고리즘과 기본값, 그리고 반응 지연·플래핑을 시뮬레이션으로 보인다.

## 동작·원리

### 1. 제어 루프

```text
          ┌──────────────────────── 15초마다(기본) ─────────────────────────┐
          ▼                                                                  │
   [지표 읽기] ──> [desired 계산] ──> [허용 오차·안정화·정책으로 다듬기] ──> [replicas 변경]
   파드별 CPU 사용률                                                             │
   (요청 대비 %)                                                                 ▼
          ▲                                                          [새 파드: 스케줄 → 이미지 pull
          │                                                           → 시작 → 준비(readiness)]
          └────────────── 준비된 파드만 지표에 의미 있게 들어온다 ◀───────────────┘
```

- *제어 루프(control loop)*: 측정 → 비교 → 조정을 주기적으로 반복하는 구조. HPA는 연속 과정이 아니라 **간헐적으로** 도는 루프다. 주기는 `--horizontal-pod-autoscaler-sync-period`, 기본 15초(Kubernetes 문서 v1.37 기준, 이하 같음).
- 핵심 식:

```text
 desiredReplicas = ceil( currentReplicas × currentMetricValue / desiredMetricValue )
 예: 현재 3대, 평균 CPU 140%, 목표 70% → ceil(3 × 2.0) = 6
```

- 비율이 1.0에 충분히 가까우면(허용 오차 기본 0.1 — 즉 ±10%) 아무것도 하지 않는다.
- CPU 사용률은 파드의 **리소스 요청(request)** 대비 %다. 요청이 없는 컨테이너가 있으면 그 지표로는 스케일하지 않는다(예외: `PodLevelResources` 기능이 켜져 있고 파드 수준 request가 있으면 그것으로 계산한다 — Kubernetes v1.37 `replica_calculator.go`).
- 지표가 여럿이면 지표마다 desired를 계산해 **가장 큰 값**을 쓴다. 단 일부 지표를 계산하지 못했는데 나머지가 축소를 가리키면 스케일을 건너뛴다(확장은 여전히 한다 — HPA 문서).

### 2. 준비 안 된 파드와 시작 직후 CPU — 보수적으로 다룬다

- CPU 기준일 때, 아직 준비되지 않은 파드나 마지막 지표가 준비 전에 찍힌 파드는 **따로 빼 둔다**.
- 스케일 업 계산에서는 빼 둔 준비 안 된 파드를 **0% 사용**으로 쳐서 비율을 다시 계산한다. 다시 계산한 비율이 방향을 뒤집거나 허용 오차 안이면 스케일하지 않는다.
  - 뜻: 새 파드가 준비되는 동안에는 추가 확장이 **억제된다**. 아래 실험에서 계단 모양으로 늘어난 이유다.
- 시작 직후 CPU 급증(예: JVM 워밍업)을 오판하지 않으려고 두 옵션이 있다.
  - `--horizontal-pod-autoscaler-cpu-initialization-period`(기본 5분): 이 시간 안에는 준비 상태이고 샘플이 전부 준비 뒤에 찍힌 경우만 CPU를 센다.
  - `--horizontal-pod-autoscaler-initial-readiness-delay`(기본 30초): 이 시간 안의 준비 안 됨은 "아직 초기화 중"으로 본다.
  - 문서 권고: CPU 급증이 끝날 때까지 통과하지 않는 startupProbe, 또는 급증 뒤에야 Ready를 알리는 readinessProbe.

### 3. 반응 지연의 합

```text
 트래픽 급증 ──┬─ 지표 수집·평균 창 ─┬─ 다음 동기화(최대 15초) ─┬─ 스케줄 ─┬─ 이미지 pull ─┬─ 런타임 시작·워밍업 ─┬─ readiness 통과 ─> 용량 증가
              │      수 초~수십 초     │                        │   수 초    │   수 초~수 분  │     수 초~수십 초      │
              └──────────────────────────── 합계: 수십 초 ~ 수 분 (구성마다 다름) ─────────────────────────────────┘
 급증 자체는 수 초에 일어난다 → 그 사이의 초과분은 대기열·타임아웃으로 간다
```

- 각 구간의 길이는 환경마다 다르다. 위 수치 범위는 설명용(예시)이다. 이미지 pull·워밍업은 [42-cold-start-and-scale-from-zero](../42-cold-start-and-scale-from-zero/2-summary.md).
- 또 하나의 상한: CPU 사용률은 포화되면 더 오르지 못한다. 사용률은 request 대비 %이므로, 그 천장은 CPU limit(없으면 노드에서 쓸 수 있는 CPU)을 request로 나눈 값이다. limit = request이면 천장이 100% 근처다(앞 예의 140%는 limit이 request보다 큰 경우다).
  - limit = request, 목표 70%라면 한 번의 계산으로 늘릴 수 있는 배수가 약 100/70 ≈ 1.43배에 묶인다(아래 실험의 5 → 7 → 10 → 15 → 22 — 실험은 파드 한 대의 천장을 100%로 뒀다). 실제 수요가 4배라도 지표는 그만큼을 보여 주지 못한다.
- SRE Workbook 11장: 새 인스턴스는 즉시 생기지 않는다. 인스턴스가 바로 서빙하지 못하면 오토스케일러에 반응할 시간이 필요하고, 사용자 대면 서비스는 과부하 보호와 이중화를 위한 여유 용량을 남기라고 권한다.

### 4. 비대칭: 늘리기는 빠르게, 줄이기는 천천히

HPA `behavior` 기본값(문서의 "Default behavior"):

```yaml
behavior:
  scaleDown:
    stabilizationWindowSeconds: 300       # 지난 5분 추천값 중 최댓값으로만 줄인다
    policies:
    - type: Percent
      value: 100
      periodSeconds: 15
  scaleUp:
    stabilizationWindowSeconds: 0         # 바로 늘린다
    policies:
    - type: Percent
      value: 100                          # 15초에 100%(두 배)까지
      periodSeconds: 15
    - type: Pods
      value: 4                            # 또는 15초에 4개까지
      periodSeconds: 15
    selectPolicy: Max                     # 둘 중 큰 쪽
```

- *안정화 창(stabilization window)*: 지난 창 안의 추천값들을 기억해, 줄일 때는 그중 **최댓값**을 쓴다. 문서는 이것을 "rolling maximum의 근사"라고 하고, 파드를 지웠다가 곧 다시 만드는 일을 막는다고 적는다. 흔히 쓰는 말로 *쿨다운*이다.
  - 커맨드라인 기본값 `--horizontal-pod-autoscaler-downscale-stabilization`도 5분이다.
- 허용 오차는 v1.33에 처음 들어와 v1.37에서 안정(stable)이 된 `behavior.scaleUp/scaleDown.tolerance` 필드로 방향별로 정할 수 있다. 정하지 않으면 클러스터 전역 10%다.
- SRE Workbook 11장도 같은 비대칭을 권한다. 확장 실패는 과부하·유실로 이어지므로 스케일 업이 더 중요하고 덜 위험하다. 대부분의 오토스케일러는 급증에 민감하고 감소에는 보수적으로 설계됐다.
- 히스테리시스(방향별 임계 분리)와 같은 생각이다 — [33-hysteresis-and-flapping](../33-hysteresis-and-flapping/2-summary.md).

### 5. 실험: HPA 알고리즘 시뮬레이션 — 급증과 출렁임

- 위 1~4절의 식·기본값을 1초 단위로 흉내 낸 시뮬레이터다(실제 Kubernetes가 아니다).
  - 15초마다 준비된 파드의 최근 15초 평균 CPU → desired, 허용 오차 0.1, 준비 안 된 파드는 0%로 재계산, 스케일 업 한도 15초에 max(+100%, +4), 스케일 다운은 안정화 창의 최댓값.
  - 파드 1개 = 초당 100건 = CPU 100%. 넘치면 대기열, 10초 넘게 기다릴 몫은 클라이언트 타임아웃으로 버린다.
  - 파드 준비 시간(스케줄~readiness)은 설정값이다(예시: 90초·20초·60초).
  - `maxReplicas`는 30이다. `minReplicas`는 급증 5(세 번째 설정은 8), 출렁임 3이다. 스케일 다운 속도 정책(기본 15초에 100%)은 사실상 제한이 없어 따로 흉내 내지 않았다.

```java
if (t % 15 == 14) {                                   // HPA 동기화 주기 15초
    double ratio = util / target;
    int desired = total;
    if (Math.abs(ratio - 1) > 0.1) {
        if (ratio > 1 && total > ready) {             // 준비 안 된 파드는 0%로 보고 다시 계산
            double r2 = util * ready / (target * total);
            if (r2 > 1.1) desired = (int) Math.ceil(total * r2);
        } else desired = (int) Math.ceil(ready * ratio);
    }
    ...
    if (desired < total) desired = Math.max(desired, maxOfRecommendationsInWindow);       // 안정화 창
    if (desired > total) desired = Math.min(desired, Math.max(total * 2, total + 4));     // 스케일 업 정책
}
```

(실험, JDK 21.0.12 temurin 컨테이너에서 실행한 결정적 시뮬레이션, 2026-10-01 — 난수 없음, 실행마다 같다(사실 점검 재실행 출력이 글자 단위로 같음). 30초 간격 표 일부)

```text
== 급증, 파드 준비 90초 (최소 5, 목표 CPU 70%, 파드 준비 90s, 다운 안정화 300s)
   t(s)  유입/s  준비/전체 파드  사용률  대기열  대기 예상
     60     300     5 /   5         60%       0     0.0s
     90    1200     5 /   7        100%    5000    10.0s
    180    1200     7 /  10        100%    7000    10.0s
    270    1200    10 /  15        100%   10000    10.0s
    360    1200    15 /  22        100%    5200     3.5s
    390    1200    15 /  22         83%       0     0.0s
    450    1200    22 /  25         55%       0     0.0s
    540    1200    25 /  25         48%       0     0.0s
    780    1200    20 /  20         60%       0     0.0s
    900    1200    18 /  18         67%       0     0.0s

== 급증 요약 (총 요청 1021050)
  설정                                 최대 대기열  타임아웃 건수  최대 파드  파드·분
  준비 90초, 목표 70%, 최소 5                10000        121180        25      267
  준비 20초, 목표 70%, 최소 5                10000         30180        22      266
  준비 90초, 목표 50%, 최소 8                 8000         30300        30      379

== 출렁임 요약 (평균 600/s ±250/s, 주기 120초, 30분, 파드 준비 60초)
  다운 안정화 창   스케일 변경 횟수  최대 대기열  타임아웃 건수  파드·분
       0초                58        6000         73127      257
     300초                 5        3591         27569      357
```

- 관찰 1 — 반응 지연: 300 → 1,200/s 급증이 10초 만에 왔는데, 용량이 수요를 따라잡은 것은 약 5분 뒤(t≈360~390초)다. 그동안 대기열이 10초치로 가득 차 약 12만 건(전체의 약 12%)이 타임아웃됐다.
- 관찰 2 — 계단: 5 → 7 → 10 → 15 → 22. 사용률이 천장 100%(실험 설정)에 묶여 한 번에 약 1.43배까지만 늘고, 새 파드가 준비될 때까지(90초) 추가 확장이 억제됐다(준비 안 된 파드 0% 처리).
- 관찰 3 — 과확장 뒤 축소: 25대까지 늘었다가(사용률 48%) 안정화 창 5분이 지난 뒤에야 20 → 18대로 줄었다. 1,200/s ÷ 70 = 17.1 → 18대가 맞는 값이다.
- 관찰 4 — 무엇이 도움이 되나: 준비 시간을 90 → 20초로 줄이면 타임아웃이 12만 → 3만 건. 여유 용량(목표 50%·최소 8대)도 3만 건으로 줄지만 파드·분(비용)이 267 → 379로 늘었다. 이 설정의 최대 파드 30은 `maxReplicas` 30에 닿은 값이다.
- 관찰 5 — 플래핑: 2분 주기 출렁임에서 안정화 창 0초는 30분 동안 58번 바꿨고, 줄였다가 다시 늘리는 사이 준비 시간 60초 동안 넘쳐 타임아웃이 7.3만 건이었다. 300초 창은 5번 바꾸고 2.8만 건, 대신 파드·분이 257 → 357로 늘었다.
- 해석: 이 모델은 단순화다(대기열 상한·즉시 반영되는 지표·같은 성능의 파드). 숫자 자체보다 **모양**(지연 동안의 초과분, 계단, 비대칭의 대가)을 본다.

## 쓰이는 자료구조·알고리즘

- **제어 루프(비례 제어)** — desired ∝ 현재 × 측정/목표. 오차에 비례해 조정하는 P 제어와 닮았다. 지연이 긴 루프에 큰 이득을 주면 진동한다.
- **이동 평균** — 지표를 일정 창으로 평균해 순간 잡음을 거른다. 실험은 15초 평균.
- **슬라이딩 윈도 최댓값(rolling max)** — 안정화 창. 지난 W초 추천값 중 최댓값. 덱(deque)으로 O(1) 갱신이 가능하다(실험은 단순 순회). [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md).
- **히스테리시스** — 올릴 때와 내릴 때의 기준·속도를 다르게. [33-hysteresis-and-flapping](../33-hysteresis-and-flapping/2-summary.md).
- **토큰식 속도 제한** — 스케일 정책("15초에 최대 4개")은 변경 속도의 상한이다. 레이트 리미터와 같은 발상([11-rate-limiter](../11-rate-limiter/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 설계 순서

1. **지표를 고른다.** 원본 §4 표: CPU는 CPU 바운드에, RPS·동시 요청 수는 웹 서버에, 큐 적체·소비 지연은 비동기 워커에. I/O 바운드 서비스는 CPU가 낮은 채로 스레드가 고갈될 수 있어 CPU 기준이 동작하지 않는다.
2. **반응 시간을 잰다.** 스케일 결정부터 새 파드가 트래픽을 받기까지 걸리는 시간(스케줄·pull·시작·워밍업·readiness). 이 시간 동안의 최악 급증을 **여유 용량**으로 흡수해야 한다.
3. **여유를 정한다.** 목표 사용률(예: 50~70%), `minReplicas`. "반응 시간 × 그동안 늘 수 있는 트래픽"이 여유 안에 들어오게 한다.
4. **상한을 정한다.** `maxReplicas`는 하류(DB 커넥션 총량·외부 API 한도·쿼터)에서 역산한다. SRE Workbook 11장: 최소·최대 한도를 두고, 그 한도까지 쿼터가 있는지 확인한다.
5. **비대칭으로 둔다.** 업은 빠르게, 다운은 안정화 창으로 천천히. 다운할 때는 graceful shutdown·드레이닝([14-graceful-shutdown](../14-graceful-shutdown/2-summary.md)).
6. **readiness를 정직하게.** 워밍업이 끝나야 Ready. 아니면 덜 데워진 파드가 트래픽을 받고, HPA는 시작 직후 CPU를 오판한다.
7. **예측 가능한 급증은 미리.** 정해진 시각의 이벤트·푸시는 그 전에 `minReplicas`를 올린다(일정 기반). 반응형 확장만으로는 수 초 급증을 못 따라간다.
8. **킬 스위치.** 오토스케일링을 끄고 수동으로 정하는 법을 온콜이 알아야 한다(SRE Workbook 11장).

### 2. HPA 예 (autoscaling/v2)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 8                      # 반응 시간 동안의 급증을 흡수할 바닥(측정해서 정한다)
  maxReplicas: 40                     # DB 커넥션 총량 = 40 × 인스턴스당 풀 ≤ DB 한도
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60        # 컨테이너 resources.requests.cpu 대비
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10                     # 1분에 10%씩만 줄인다(문서의 예)
        periodSeconds: 60
```

### 3. 진단 명령

```bash
kubectl get hpa api -w                       # 현재/목표 지표, replicas 변화
kubectl describe hpa api                     # Conditions(AbleToScale·ScalingActive·ScalingLimited)와 Events(스케일 사유)
kubectl get pods -l app=api -o wide          # 준비 안 된 파드 수
kubectl get events --field-selector involvedObject.kind=Pod | grep -i pull   # 이미지 pull 시간
```

```text
# PromQL 예: 스케일 결정 대비 실제 Ready 수의 차이(kube-state-metrics 지표 이름 예)
# 두 지표의 라벨(horizontalpodautoscaler·deployment)이 달라 on(namespace)로 짝을 지정한다
kube_horizontalpodautoscaler_status_desired_replicas{horizontalpodautoscaler="api"}
  - on(namespace) kube_deployment_status_replicas_ready{deployment="api"}
```

- `_replicas_available`은 Ready가 아니라 `minReadySeconds` 동안 Ready를 유지한 수다(Deployment API). 두 지표 모두 kube-state-metrics 문서(main 브랜치 `docs/metrics/workload/`)에 STABLE로 올라 있다. `describe hpa`의 세 Condition(AbleToScale·ScalingActive·ScalingLimited)은 Kubernetes "HorizontalPodAutoscaler Walkthrough"에 나온다.

## 장애 시나리오와 대처

### 1. 확장보다 급증이 빨라 확장 전에 무너졌다 (⚠)

- 현상: 푸시 발송 직후 트래픽이 수 초 만에 4배가 됐다. 오토스케일은 동작했지만 몇 분간 타임아웃이 쏟아졌다.
- 보이는 형태: HPA 이벤트에 스케일 업 기록이 여러 번, 그 사이 준비 안 된 파드 다수, 대기열 포화, 5xx·타임아웃 급증 후 몇 분 뒤 회복. 실험 관찰 1·2의 모양.
- 원인: 반응 시간(동기화 주기 + 파드 준비 시간)이 급증보다 길다. CPU 지표가 포화 천장(limit = request이면 100%)에 묶여 한 번에 늘 수 있는 배수가 제한되고, 준비 안 된 파드 처리로 추가 확장이 억제된다.
- 대처: 여유 용량(`minReplicas`·낮은 목표 사용률), 예정된 급증은 미리 확장, 파드 준비 시간 단축(이미지 크기·시작 시간 — 42번), 넘치는 몫은 빠르게 거절(로드 셰딩 — [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md)). SRE Workbook 11장: 로드 셰딩보다 오토스케일이 먼저 동작하도록 임계를 정하라.

### 2. 늘렸다 줄였다를 반복한다 (⚠ 쿨다운 없음 → 플래핑)

- 현상: 레플리카 수가 몇 분마다 오르내린다. 줄인 직후 다음 파도에 지연이 튄다.
- 보이는 형태: HPA 이벤트에 스케일 업·다운이 번갈아, 실험의 안정화 창 0초(30분에 58번).
- 원인: 스케일 다운 안정화 창이 없거나 너무 짧고, 지표가 주기적으로 출렁인다. 줄였다가 다시 늘리면 준비 시간 동안 넘친다.
- 대처: `scaleDown.stabilizationWindowSeconds`(기본 300초)를 출렁임 주기보다 길게, 다운 정책을 느리게(분당 10% 등). 대가는 더 많은 파드·분(실험 257 → 357).

### 3. 앱 오토스케일이 DB를 죽였다

- 현상: 피크에 앱이 50대로 늘자 DB 연결이 바닥나 전체가 장애.
- 보이는 형태: DB 커넥션 수가 앱 수에 비례해 상승, `too many connections`류 오류, 커넥션 획득 타임아웃.
- 원인: `maxReplicas` × 인스턴스당 풀 크기가 DB 한도를 넘었다. 병목이 앱에서 DB로 옮겨 갔다([21-scaling-principles](../21-scaling-principles/2-summary.md)).
- 대처: `maxReplicas`를 DB 한도에서 역산, 커넥션 풀러(PgBouncer 등), 인스턴스당 풀 축소. SRE Workbook 11장 "Avoiding Overloading Backends": 오토스케일러를 켜기 전에 하류 의존성을 분석하라.

### 4. 하류 장애에 오토스케일러가 계속 늘린다

- 현상: 의존 서비스가 느려지자 요청이 서버에 붙잡혀 CPU·동시 요청 지표가 올라가고, 오토스케일러가 계속 확장해 의존 서비스를 더 누른다.
- 보이는 형태: 레플리카가 `maxReplicas`까지 상승, 처리량은 오르지 않음, 하류 오류율 상승.
- 원인: 지표가 "일이 많다"와 "막혀 있다"를 구분하지 못한다(SRE Workbook 11장의 사례와 같은 모양). 버그로 CPU를 헛쓰는 새 버전도 같은 일을 만든다.
- 대처: 하류 호출 데드라인(타임아웃)·서킷 브레이커로 막힌 요청을 빨리 끊는다. `maxReplicas`·쿼터로 상한. 오토스케일 킬 스위치.

### 5. 새 파드가 많은데도 확장이 안 된다 (준비 상태 문제)

- 현상: 트래픽이 높은데 HPA가 더 늘리지 않는다.
- 보이는 형태: 준비 안 된 파드(Ready 0/1)가 오래 남아 있다. `kubectl describe hpa`의 지표가 실제보다 낮다.
- 원인: 준비 안 된 파드는 스케일 업 계산에서 0%로 쳐진다. 파드가 준비에 실패하거나(헬스 체크 설정 오류, 의존성 대기) 오래 걸리면 확장이 억제된다. SRE Workbook 11장: 서빙하지 않는 인스턴스가 평균에 들어가면 오토스케일이 일어나지 않을 수 있다.
- 대처: readiness 실패 원인 수리, 준비 시간 단축, 로드밸런서가 본 용량 지표로 스케일(건강하지 않은 인스턴스를 자동으로 뺌 — 같은 장).

## 핵심 문장

- HPA는 15초(기본)마다 desired = ceil(현재 × 측정/목표)를 계산하고, ±10%(기본) 안이면 그대로 둔다.
- 반응 지연 = 지표 창 + 동기화 주기 + 파드 준비 시간이다. 그 사이의 급증은 여유 용량이 흡수해야 한다. 시뮬레이션에서 10초 급증을 따라잡는 데 약 5분이 걸렸고 약 12%가 타임아웃됐다.
- CPU 사용률은 포화 천장(limit = request이면 100%)에 묶여 한 번에 늘 수 있는 배수를 제한하고, 준비 안 된 파드는 0%로 쳐져 추가 확장을 억제한다. 그래서 확장이 계단으로 온다.
- 늘리기는 빠르게(기본 안정화 0초), 줄이기는 천천히(기본 300초 창의 최댓값). 창이 없으면 플래핑으로 오히려 더 넘친다.
- 최대치는 하류에서 역산한다. 앱 오토스케일이 DB를 죽이는 일이 흔하다.

## 관련 주제·근거

- 선행
  - [22-capacity-and-load-testing](../22-capacity-and-load-testing/2-summary.md) — 대당 한계·헤드룸
  - [33-hysteresis-and-flapping](../33-hysteresis-and-flapping/2-summary.md) — 방향별 임계로 진동 막기
  - 원본 [server-design/09-capacity-slo](../../systems/server-design/09-capacity-slo.md) §4 — 지표 선택 표, 함정 표(반응 지연·콜드 스타트·플래핑·스케일인·하위 시스템 압사·상한)
- 후속·연결
  - [42-cold-start-and-scale-from-zero](../42-cold-start-and-scale-from-zero/2-summary.md) — 파드 준비 시간 줄이기
  - [21-scaling-principles](../21-scaling-principles/2-summary.md) — 병목 이동
  - [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md) · [14-graceful-shutdown](../14-graceful-shutdown/2-summary.md)
  - [os/28-containers-namespaces-cgroups](../../os/28-containers-namespaces-cgroups/2-summary.md) — CPU request·limit의 실체
- 문서
  - Kubernetes "Horizontal Pod Autoscaling"(v1.37 문서, 2026-10-01 열람) — 제어 루프·sync-period 15초, 알고리즘 식, 허용 오차 0.1, 준비 안 된 파드·누락 지표의 보수적 처리, cpu-initialization-period 5분·initial-readiness-delay 30초, 다중 지표 최댓값, downscale-stabilization 5분, Default behavior, tolerance 필드(v1.33 도입·v1.37 안정) <https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/>
  - Google SRE Workbook 11장 "Managing Load" — Autoscaling 절(Handling Unhealthy Machines, Configuring Conservatively, Setting Constraints, Kill Switches, Avoiding Overloading Backends), Case Study 2(로드 셰딩과 부하 분산의 되먹임) <https://sre.google/workbook/managing-load/>
- 실험 목록
  - E41 `HpaSim.java`: HPA 식·기본값 1초 단위 결정적 시뮬레이션 — 급증(300 → 1,200/s, 준비 90/20초, 목표 70/50%) 3설정, 출렁임(600±250/s, 주기 120초, 안정화 0/300초) 2설정. JDK 21.0.12 temurin 컨테이너, 1회(결정적)
