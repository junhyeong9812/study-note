# reliability/25-high-availability-topology — 고가용성 토폴로지: 이중화 모델·페일오버·split-brain·다중 AZ/리전 — 정리 (힌트)

## 해결하는 문제

서버 한 대는 언젠가 죽는다. 한 대가 죽어도 서비스가 계속되게 하려고 같은 역할을 여러 대에 둔다. 이것이 이중화다.\
그런데 이중화는 공짜로 가용성을 올려 주지 않는다. 세 가지가 새로 생긴다.

```text
 1. 언제 "죽었다"고 볼 것인가     너무 빨리 → 멀쩡한 주 노드를 강등(오탐 페일오버)
                                 너무 늦게 → 죽은 동안 계속 실패
 2. 둘이 다 "내가 주인"이면?       split-brain → 데이터가 갈라진다
 3. 둘이 같이 죽으면?              같은 랙·같은 AZ·같은 설정 → 이중화가 한 번에 무너진다
```

- *이중화(redundancy)*: 같은 역할을 하는 구성 요소를 둘 이상 두는 것.
- *페일오버(failover)*: 주 구성 요소가 고장 났다고 판단하고, 대기 구성 요소로 역할을 넘기는 것.
- *split-brain*: 네트워크가 갈리거나 판정이 틀려 주(primary)가 둘이 되고, 양쪽이 각자 쓰기를 받는 상태.

쉬운 예: 병원 당직이다.
- 당직 의사(주)가 호출에 답이 없으면 대기 의사(부)가 맡는다.
- 화장실에 간 것(잠깐 멈춤)을 퇴근(죽음)으로 착각하면 두 의사가 같은 환자에게 다른 처방을 낸다.
- 두 의사가 같은 차를 타고 출근하면(같은 AZ), 그 차가 막히는 날 둘 다 없다.

똑같은 구조다.\
실무 예: DB 주-복제 자동 승격(Orchestrator·Patroni 같은 도구), 로드 밸런서 뒤의 앱 서버, 다중 AZ 배치, 다중 리전.\
기초(가용성 숫자 표·Active-Active 용량 규칙·쿼럼과 펜싱 표·다중 리전 모델)는 원본 [systems/server-design/05-ha-topology.md](../../systems/server-design/05-ha-topology.md) §1~§5에 있다. 가용성 합성 계산은 [01-fault-error-failure-availability](../01-fault-error-failure-availability/2-summary.md) 「동작·원리」 5절. 이 노트는 **헬스 판정 상태 기계**를 실험으로 보고, 오탐 페일오버·같은 AZ 이중화·split-brain을 사고 사례와 함께 채운다.

## 동작·원리

### 1. 이중화 모델 세 가지

```text
 Active-Passive          Active-Active               N+1
 [주 ●] ← 트래픽          [A ●] [B ●] ← 트래픽 나눠      [● ● ● ●] + [○ 여분 1]
 [부 ○] 대기(복제만 받음)   한 대 죽으면 남은 쪽이 다 받음   N대가 필요, 1대 여유
 전환 시간이 있다           용량을 (N−1)/N 이하로 써야      비용과 여유의 절충
```

- Active-Active는 전환 시간이 거의 없지만, 각 노드 사용률이 (N−1)/N를 넘으면 한 대가 죽을 때 남은 노드가 넘친다(원본 §2 "Active-Active의 함정").
- Active-Passive는 대기 노드가 실제로 일을 해 본 적이 없다. 전환을 정기적으로 해 보지 않으면 대기 노드가 동작하는지 모른다(원본 §2).

### 2. 페일오버의 세 단계

```text
 ① 탐지            ② 결정                       ③ 전환
 헬스체크 실패 누적 → "주가 죽었다"에 합의(쿼럼) → 새 주 승격 + 옛 주 차단(펜싱) + 클라이언트 경로 변경(VIP·DNS·프록시)
 (이 노트의 실험)     (distributed/10·11)          (distributed/12, 이 노트 5절)
```

- 비동기 네트워크에서는 "죽음"과 "느림"을 구별할 수 없다([distributed/02-system-and-failure-models](../../distributed/02-system-and-failure-models/2-summary.md)). 그래서 ①은 추정이다. 추정의 두 오류가 오탐(멀쩡한데 죽었다고 봄)과 미탐·지연(죽었는데 늦게 봄)이다.
- ②를 한 노드가 혼자 하면 그 노드의 시야가 곧 진실이 된다. 쿼럼(과반)으로 하는 이유는 [distributed/10-leader-election](../../distributed/10-leader-election/2-summary.md) 「동작·원리」.

### 3. 헬스 판정 상태 기계

```text
                 실패 1회
   ┌─────────┐ ───────────> ┌─────────┐  연속 실패 ≥ failureThreshold  ┌──────┐
   │ HEALTHY │              │ SUSPECT │ ─────────────────────────────> │ DOWN │ ★ 페일오버 결정
   └─────────┘ <─────────── └─────────┘                                └──────┘
        ▲        성공 1회                                                 │
        └──────────────────── 연속 성공 ≥ successThreshold ───────────────┘
                              (돌아와도 이미 강등됐다 — 되돌리기는 별도 결정)
```

- *failureThreshold*: 연속 몇 번 실패해야 DOWN으로 보나. 클수록 오탐이 줄고 탐지가 늦다.
- *successThreshold*: DOWN에서 연속 몇 번 성공해야 다시 HEALTHY로 보나. 진동(flapping)을 막는다(→ [33-hysteresis-and-flapping](../33-hysteresis-and-flapping/2-summary.md)).
- 탐지 시간은 대략 `검사 간격 × failureThreshold`(+ 마지막 검사의 타임아웃)다.
- Kubernetes probe 기본값(Kubernetes 문서 "Liveness, Readiness, and Startup Probes", 2026-10-01 열람): `periodSeconds` 10, `timeoutSeconds` 1, `failureThreshold` 3, `successThreshold` 1. 기본값 그대로면, 프로세스는 살아 있는데 응답하지 않는 컨테이너를 liveness 프로브가 약 20~30초(+타임아웃 1초) 뒤에야 실패로 본다 — 멈춘 시각부터 첫 실패 검사까지 0~10초, 그 뒤 검사 두 번이 더 실패해야 한다. 프로세스가 아예 종료하면 프로브를 기다리지 않고 `restartPolicy`대로 처리된다(Pod 생명주기 문서).

### 4. 실험: 멈춤(GC 흉내) 두 번과 진짜 죽음 한 번 — 임계값 1·3·6

- 주 노드: Node HTTP 서버 컨테이너. `docker pause`로 프로세스를 얼려 GC 멈춤·짧은 네트워크 단절을 흉내 낸다.
- 판정기: Java 판정기 하나가 0.5초마다 검사(타임아웃 0.3초)하고, 같은 결과를 임계값 1·3·6짜리 상태 기계 셋에 넣는다(successThreshold 2).
- 순서: 1.2초 멈춤 → 2.5초 멈춤 → `docker kill`(진짜 죽음).

```java
String observe(boolean ok) {                      // HealthFsm.Detector 핵심
    if (ok) { fails = 0; oks++; } else { oks = 0; fails++; }
    State before = state;
    switch (state) {
        case HEALTHY -> { if (!ok) state = fails >= failureThreshold ? State.DOWN : State.SUSPECT; }
        case SUSPECT -> { if (ok) state = State.HEALTHY; else if (fails >= failureThreshold) state = State.DOWN; }
        case DOWN    -> { if (oks >= successThreshold) state = State.HEALTHY; }
    }
    if (before != state && state == State.DOWN) failovers++;
    return before == state ? null : before + "→" + state;
}
```

(실험, JDK 21.0.12 + Node 22.23.2, 각 컨테이너 `--cpus=1`, 검사 0.5초·타임아웃 0.3초, 2026-10-01 — 구동 스크립트(`##`)와 판정기 출력을 시각순으로 합쳤다)

```text
## 06:13:10.685 주 노드 1.2초 멈춤 시작 (docker pause — GC 멈춤 흉내)
06:13:11.140 임계값 1: HEALTHY→DOWN  ★페일오버 결정
06:13:11.140 임계값 3: HEALTHY→SUSPECT
06:13:11.140 임계값 6: HEALTHY→SUSPECT
06:13:12.019 임계값 3: SUSPECT→HEALTHY
06:13:12.019 임계값 6: SUSPECT→HEALTHY
## 06:13:12.040 멈춤 끝
06:13:12.339 임계값 1: DOWN→HEALTHY
## 06:13:15.053 주 노드 2.5초 멈춤 시작
06:13:15.636 임계값 1: HEALTHY→DOWN  ★페일오버 결정
06:13:15.636 임계값 3: HEALTHY→SUSPECT
06:13:15.636 임계값 6: HEALTHY→SUSPECT
06:13:16.637 임계값 3: SUSPECT→DOWN  ★페일오버 결정
06:13:17.881 임계값 6: SUSPECT→HEALTHY
## 06:13:17.903 멈춤 끝
06:13:18.341 임계값 1: DOWN→HEALTHY
06:13:18.341 임계값 3: DOWN→HEALTHY
## 06:13:21.910 주 노드 실제로 죽음 (docker kill)
06:13:22.637 임계값 1: HEALTHY→DOWN  ★페일오버 결정
06:13:22.637 임계값 3: HEALTHY→SUSPECT
06:13:22.637 임계값 6: HEALTHY→SUSPECT
06:13:23.639 임계값 3: SUSPECT→DOWN  ★페일오버 결정
06:13:25.139 임계값 6: SUSPECT→DOWN  ★페일오버 결정
임계값 1 (검사 0.5초·타임아웃 0.3초): 페일오버 결정 3번
임계값 3 (검사 0.5초·타임아웃 0.3초): 페일오버 결정 2번
임계값 6 (검사 0.5초·타임아웃 0.3초): 페일오버 결정 1번
```

| 임계값 | 1.2초 멈춤 | 2.5초 멈춤 | 진짜 죽음 탐지(kill → DOWN) | 정당한 페일오버 / 전체 |
|---|---|---|---|---|
| 1 | 오탐 | 오탐 | 0.73초 | 1 / 3 |
| 3 | 넘김 | 오탐 | 1.73초 | 1 / 2 |
| 6 | 넘김 | 넘김 | 3.23초 | 1 / 1 |

- 관찰 1: 멈춤이 끝나자 주 노드는 바로 다시 응답했다(DOWN→HEALTHY). 멀쩡한 노드였다. 임계값 1은 두 번의 멈춤 모두에서 페일오버를 결정했다. 실제 시스템이었다면 멀쩡한 주 노드를 두 번 강등했다.
- 관찰 2: 임계값이 커질수록 오탐이 줄고 진짜 죽음의 탐지가 늦어진다. 공짜인 쪽이 없다. 다른 실행들(집필 2회 + 점검 재실행 3회)에서 탐지 시간은 0.27~0.85초 · 1.56~1.85초 · 3.06~3.35초였다. 죽은 시각과 다음 검사 시각의 위상에 따라 최대 검사 간격(0.5초)만큼 흔들린다.
- 관찰 3: 비결정적이다. 임계값 3은 이 실행에서는 1.2초 멈춤을 넘겼지만, 첫 실행에서는 같은 1.2초 멈춤에도 페일오버를 결정했다(멈춤이 검사 3번에 걸쳤다). 멈춤 길이와 검사 간격이 비슷하면 결과가 검사 시각의 위상에 달린다.
- 관찰 4: 또 다른 실행에서는 멈춤을 주기 **전에** 임계값 1이 DOWN이 됐다. 판정기 JVM이 막 떠서 첫 연결이 0.3초 타임아웃을 넘긴 것으로 보인다(해석). 점검 재실행 3회 중 1회에서도 같은 일이 났다(그 실행은 임계값 1 페일오버 결정 4번). 판정기 자신의 느림도 오탐 원인이다.

### 5. split-brain을 막는 두 장치

```text
 네트워크 분할                       쿼럼만 있을 때                       쿼럼 + 펜싱
 [주 A] ╳ [B] [C]                   B·C가 과반 → B 승격                 B 승격 + 임기 번호 증가
 A는 자기가 아직 주라고 믿는다          A가 클라이언트 쓰기를 계속 받을 수 있다   저장소·스위치가 옛 임기의 A를 거절
```

- *쿼럼(quorum)*: 과반의 동의. 과반은 둘이 될 수 없으므로 "결정"은 한 쪽에서만 난다.
- *펜싱(fencing)*: 옛 주를 강제로 막는 것. 전원 차단(STONITH), 스토리지 접근 차단, 단조 증가 토큰 검사([distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md)).
- 쿼럼은 "누가 새 주인가"를 하나로 만든다. 펜싱은 "옛 주가 아직 쓰는 것"을 막는다. 둘 다 필요하다.

### 6. 실제 사례: 43초의 분할이 24시간 11분이 되다 (GitHub 2018-10-21)

GitHub 사후 분석(2018-10-30, Jason Warner) 원문 요지:

- 22:52 UTC, 광 장비 교체 작업으로 미국 동부 네트워크 허브와 동부 주 데이터센터의 연결이 끊겼다. 연결은 43초 만에 복구됐다.
- 그 사이 Orchestrator(MySQL 토폴로지·자동 페일오버 도구, Raft 기반)의 서부 데이터센터 노드와 동부 퍼블릭 클라우드 노드가 쿼럼을 이뤄, 쓰기를 **서부** 데이터센터로 넘기는 페일오버를 시작했다.
- 동부 DB에는 서부로 복제되지 않은 짧은 구간의 쓰기가 있었다. 가장 바쁜 클러스터 하나에서 영향 구간의 쓰기가 954건이었다.
- 서부에 이미 30분 넘는 쓰기가 쌓이자, 동부로 그냥 되돌릴 수 없어 "앞으로 고치기"를 택했다. 동부 앱은 대륙을 가로지르는 왕복 지연을 견디지 못했다. 서비스 저하는 24시간 11분 이어졌다.
- 후속 조치 중 하나: 리전 경계를 넘는 주 DB 승격을 막도록 Orchestrator 설정을 바꾼다. 원문: "Orchestrator's actions behaved as configured, despite our application tier being unable to support this topology change."

해석: 탐지·결정 자체는 쿼럼으로 "옳게" 됐다. 문제는 (1) 43초짜리 단절에 리전 간 페일오버라는 큰 조치를 걸었고 (2) 새 토폴로지를 애플리케이션이 감당하지 못했으며 (3) 비동기 복제라 양쪽 데이터가 갈렸다는 점이다. 자동 페일오버는 "언제 하나"와 함께 "어디로까지 하나"를 제한해야 한다.

### 7. 장애 도메인 — 같이 죽는 것들

```text
 같은 AZ에 둘                          AZ 둘에 하나씩
 AZ-a [주][부]                         AZ-a [주]      AZ-b [부]
 AZ-a 정전·네트워크 장애 → 둘 다 없음       AZ-a 장애 → 부가 이어받음(*)
```

- (*) 단, 승격 결정에 쿼럼이 있어야 한다(5절). 주·부 두 대만 투표하면 남은 한 표는 과반이 아니다. 제3 위치의 투표자 등으로 쿼럼을 유지하고 펜싱·경로 전환까지 갖춰야 부가 이어받는다.
- *장애 도메인(failure domain)*: 하나의 원인으로 같이 고장 나는 범위. 프로세스 < 호스트 < 랙 < AZ < 리전.
- *AZ(가용 영역)*: AWS 문서는 AZ를 "한 리전 안의 여러 격리된 위치"라고 정의한다(EC2 사용자 안내서 "Regions and Zones").
- 독립 가정이 깨지면 병렬 합성 공식(1 − (1−A)²)이 틀린다. 공통 원인이 있으면 두 복제의 가용성은 그 공통 원인의 가용성보다 높아질 수 없다(01의 몬테카를로 실험).
- 같은 이미지·같은 설정·같은 배포도 장애 도메인이다. 나쁜 설정을 두 AZ에 동시에 밀면 AZ 분리가 소용없다(→ [51-cells-stamps-and-blast-radius](../51-cells-stamps-and-blast-radius/2-summary.md)).

### 8. 다중 리전

| 모델 | 대략의 RTO·RPO | 비고 |
|---|---|---|
| 백업 복원 | 시간 | 리전 재해 대비의 최소형 |
| 파일럿 라이트 | 수십 분 | 데이터는 복제, 앱은 꺼 둠 |
| 웜 스탠바이 | 분 | 작은 규모로 상시 가동 |
| 다중 사이트 액티브-액티브 | 실시간에 가까움 | 쓰기 충돌·지연 비용 |

- 수치 출처: AWS 백서 "Disaster Recovery of Workloads on AWS" 그림 6. 상세는 [46-disaster-recovery](../46-disaster-recovery/2-summary.md).
- 리전 사이 왕복 지연이 길어서 동기 복제는 쓰기 지연을 크게 늘린다. 비동기 복제면 페일오버 때 마지막 쓰기를 잃을 수 있다(위 GitHub 사례, [database/32-replication-leader-follower](../../database/32-replication-leader-follower/2-summary.md) 「동작·원리」 6절).

## 쓰이는 자료구조·알고리즘

- **헬스 판정 상태 기계** — HEALTHY/SUSPECT/DOWN + 연속 실패·성공 카운터(위 실험). 슬라이딩 윈도("최근 10번 중 6번 실패")로 바꾸면 성공 한 번에 카운터가 초기화되지 않아, 연속이 아닌 간헐 실패도 창 안에 쌓이면 DOWN으로 잡는다.
- **과반 쿼럼** — N대 중 ⌊N/2⌋+1. 두 과반은 한 대 이상 겹친다는 산술 성질을 이용한다. 짝수 대수는 1:1 분할에서 아무도 과반이 못 된다([distributed/09-quorums](../../distributed/09-quorums/2-summary.md)).
- **임기·에포크 번호, 펜싱 토큰** — 단조 증가 번호로 옛 주를 거절([distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md)).
- **리스(lease)** — 기한이 있는 주인 자격. 갱신을 못 하면 스스로 내려온다.
- **위상 분산 제약** — 복제본을 장애 도메인(존 레이블)에 고르게 흩는 스케줄링 규칙. Kubernetes `topologySpreadConstraints`(`maxSkew`·`topologyKey: topology.kubernetes.io/zone`).

## 적용 — 풀어나가는 법

### 1. 순서

1. 목표를 정한다(몇 9, RTO·RPO). 이것이 모델(Active-Passive/Active-Active/N+1)과 범위(다중 AZ/리전)를 정한다.
2. 계층마다 "이게 죽으면?"을 묻는다. LB·앱·DB·캐시·큐·DNS·설정 저장소·비밀 저장소.
3. 장애 도메인을 나눈다. 복제본은 다른 AZ에, 배포·설정 변경은 AZ를 하나씩.
4. 상태 저장 구성 요소는 쿼럼(홀수 대)과 펜싱을 갖춘 도구로 승격한다.
5. 헬스 판정을 설계한다. 검사 간격·타임아웃·임계값을 "허용할 오탐" vs "허용할 탐지 시간"으로 고른다. 판정은 한 관찰자가 아니라 여러 위치에서 본 결과를 합친다.
6. 페일오버 범위를 제한한다. 리전 경계를 넘는 자동 승격은 사람 승인이나 별도 조건으로 묶는다(GitHub 후속 조치).
7. 전환을 정기적으로 실제로 해 본다(계획된 페일오버 훈련).

### 2. 헬스 판정 설계 — 숫자 고르기 (예시)

```text
 목표: 주 DB 고장 탐지 10초 이내, GC 멈춤(관측 최대 2초)으로는 승격하지 않음
 검사 간격 1초, 타임아웃 0.5초
 failureThreshold = 5  → 탐지 ≈ 5초(+0.5초), 연속 5번 실패 = 4초 넘는 무응답이 있어야 DOWN
 successThreshold = 3  → 돌아온 노드가 1~2번 응답하고 또 끊기는 진동을 걸러 냄
 관찰자 3곳(다른 AZ) 중 2곳 이상이 DOWN이어야 승격
```

### 3. Kubernetes 예

```yaml
readinessProbe:                # 트래픽에서 빼는 판정 — 의존성 검사 여부는 /ready 구현이 정한다(여기서는 보지 않게 구현한다고 가정, 원본 §7 깊은 헬스체크)
  httpGet: { path: /ready, port: 8080 }
  periodSeconds: 5
  timeoutSeconds: 1
  failureThreshold: 3
topologySpreadConstraints:     # 복제본을 존마다 고르게
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector: { matchLabels: { app: api } }
```

```bash
# 복제본이 실제로 어느 존·노드에 있나
kubectl get pods -l app=api -o wide
kubectl get nodes -L topology.kubernetes.io/zone
```

## 장애 시나리오와 대처

### 1. ⚠ 페일오버 자동화가 오탐으로 멀쩡한 주 노드를 강등

- 현상: GC 멈춤·짧은 네트워크 단절 뒤 주가 바뀌어 있다. 옛 주는 멀쩡하다.
- 보이는 형태: 실험처럼 DOWN 직후 DOWN→HEALTHY. 승격 로그와 같은 시각에 GC 로그의 긴 멈춤이나 짧은 링크 장애. 승격 후 비동기 복제의 마지막 쓰기 유실, 커넥션 재수립 폭주.
- 원인: 임계값이 멈춤 길이보다 짧다(실험: 임계값 1은 1.2초 멈춤에도 승격). 한 관찰자의 시야만으로 결정한다. 판정기 자신이 느리다.
- 대처: 임계값을 관측된 최대 멈춤보다 길게, 여러 위치의 관찰자 합의로 결정. 승격 범위(리전 경계) 제한. 승격 뒤 옛 주는 펜싱으로 막는다. 탐지 시간 증가는 RTO 예산에 넣는다.

### 2. ⚠ 같은 AZ 이중화 → 동시 장애

- 현상: 주·부를 다 두었는데 AZ 하나의 장애로 서비스가 통째로 멈췄다.
- 보이는 형태: 두 인스턴스가 같은 시각에 사라진다. `kubectl get pods -o wide`·클라우드 콘솔에서 같은 존 레이블.
- 원인: 스케줄러가 남는 자리에 몰아 놓았거나, 비용 때문에 같은 AZ에 두었다. 병렬 합성의 독립 가정이 깨졌다.
- 대처: 존 단위 분산 제약, 다른 AZ의 복제본. LB·NAT·캐시처럼 잊기 쉬운 계층도 AZ마다. 설정·배포도 AZ를 하나씩.

### 3. split-brain — 주가 둘

- 현상: 분할이 풀린 뒤 같은 키에 서로 다른 값이 있다. 주문·잔액이 맞지 않는다.
- 보이는 형태: 두 노드가 같은 시간대에 쓰기를 받은 로그. 복제 재연결 때 타임라인 분기 오류.
- 원인: 쿼럼 없이 승격했거나(2대 구성), 펜싱 없이 옛 주가 쓰기를 계속 받았다.
- 대처: 홀수 대 쿼럼 + 펜싱(STONITH·토큰). 분할된 소수 쪽은 쓰기를 멈춘다. 이미 갈렸다면 사람 판단으로 대사(reconciliation)한다.

### 4. 리전 간 자동 페일오버가 앱이 감당 못 하는 토폴로지를 만든다 (GitHub 2018)

- 현상: 짧은 단절 뒤 쓰기가 먼 리전으로 넘어가 페이지가 느려지고, 되돌릴 수도 없다.
- 보이는 형태: 쓰기 지연이 대륙 간 왕복만큼 오른다. 옛 리전에 복제 안 된 쓰기(GitHub: 바쁜 클러스터 하나에서 954건)가 남는다.
- 원인: 페일오버 범위 제한이 없었다. 도구는 설정대로 동작했다.
- 대처: 자동 승격은 리전 안으로 한정, 리전 간은 사람 결정. 옛 주의 미복제 쓰기를 보관했다가 대사한다.

### 5. 대기 노드·여분 용량이 실제로는 없다

- 현상: 페일오버는 됐는데 새 주가 부하를 못 버티고 같이 쓰러진다.
- 보이는 형태: 승격 직후 CPU·커넥션 포화, 연쇄 실패. Active-Active인데 평소 사용률이 50%를 넘던 2대 구성.
- 원인: 대기 노드가 작거나 설정이 다르다. (N−1)/N 규칙 위반.
- 대처: 대기 노드를 같은 사양으로, 정기 전환 훈련으로 검증. 사용률 경보 기준을 (N−1)/N 아래로.

## 핵심 문장

- 이중화는 탐지·결정·전환의 세 단계가 다 맞아야 가용성을 올린다. 하나라도 틀리면 이중화가 장애 원인이 된다.
- 헬스 판정 임계값은 오탐과 탐지 시간을 맞바꾼다. 실험에서 임계값 1은 1.2초 멈춤에도 멀쩡한 노드를 강등했고, 임계값 6은 멈춤을 다 넘겼지만 진짜 죽음을 3.2초 뒤에야 잡았다.
- 쿼럼은 새 주를 하나로 만들고, 펜싱은 옛 주의 쓰기를 막는다. split-brain에는 둘 다 필요하다.
- 같은 AZ·같은 설정·같은 배포에 묶인 복제본은 같이 죽는다. 장애 도메인을 나눠야 병렬 합성이 성립한다.
- 자동 페일오버는 "언제"와 함께 "어디까지"를 제한한다. GitHub 2018에서는 43초 단절이 리전 간 승격으로 이어져 24시간 11분 저하가 됐다.

## 관련 주제·근거

- 선행
  - [01-fault-error-failure-availability](../01-fault-error-failure-availability/2-summary.md) — 가용성 합성, 공통 원인
  - [distributed/10-leader-election](../../distributed/10-leader-election/2-summary.md) — 장애 탐지·리스·임기
  - 원본 [systems/server-design/05-ha-topology.md](../../systems/server-design/05-ha-topology.md) §2 이중화 토폴로지, §3 리더-팔로워 Failover·Split-Brain, §4 다중 AZ/리전, §5 무상태 vs 상태, §7 헬스체크 설계. 참고: 원본 §3의 "쿼럼·펜싱 표"에서 쿼럼은 리더 둘의 **선출**을 막고, 옛 리더가 쓰기를 계속하는 것은 펜싱이 막는다 — 둘은 대체 관계가 아니라 함께 쓰는 관계다(distributed/12 실험).
- 후속·연결
  - [46-disaster-recovery](../46-disaster-recovery/2-summary.md) — RPO·RTO, 리전 전환 훈련
  - [51-cells-stamps-and-blast-radius](../51-cells-stamps-and-blast-radius/2-summary.md) — 장애 반경을 구조로 제한
  - [distributed/11-consensus-raft](../../distributed/11-consensus-raft/2-summary.md), [distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md), [distributed/09-quorums](../../distributed/09-quorums/2-summary.md)
  - [database/32-replication-leader-follower](../../database/32-replication-leader-follower/2-summary.md) — 페일오버 때 잃는 쓰기
  - [33-hysteresis-and-flapping](../33-hysteresis-and-flapping/2-summary.md) — 방향별 임계값으로 진동 막기
- 문서·글
  - GitHub, "October 21 post-incident analysis", 2018-10-30 <https://github.blog/news-insights/company-news/oct21-post-incident-analysis/>
  - Kubernetes 문서 "Liveness, Readiness, and Startup Probes"(probe 기본값) <https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/>, "Pod Topology Spread Constraints" <https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/>
  - AWS EC2 사용자 안내서 "Regions and Zones"(AZ = 리전 안의 격리된 위치) <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html>
  - AWS 백서 "Disaster Recovery of Workloads on AWS"(그림 6 전략별 RPO/RTO, "Detection" 절: 깊은 헬스체크·불필요한 페일오버의 위험) <https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html>
- 실험 목록
  - E25: Node 주 노드 + Java 판정기(0.5초 간격·0.3초 타임아웃, 임계값 1·3·6) — `docker pause` 1.2초·2.5초, `docker kill`. 3회 실행. 코드 scratchpad `rel/23/e25/{health.js,HealthFsm.java,run25.sh}`, 일회용 컨테이너 `sn-rl-w23-{primary,checker}`
