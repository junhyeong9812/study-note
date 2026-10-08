# reliability/53-reliability-incidents — 실사건: AWS S3 입력 오류(2017) · Slack 연휴 뒤 복귀 트래픽(2021) · Roblox Consul 73시간(2021) · CrowdStrike 채널 파일 291(2024) — 정리 (힌트)

## 해결하는 문제

leaf 노트는 신뢰성 장치를 **하나씩** 설명한다.\
운영 도구의 속도 제한은 49번, 셀은 51번, 오토스케일은 41번, 감시 시스템의 감시는 43번, 단계적 배포는 23번이다.\
실제 장애에서는 장치 여러 개가 **한꺼번에 빠져 있었다는 것**이 드러난다. 그리고 복구 경로가 평소와 전혀 다른 길이었다는 것도 드러난다.

```text
  leaf 노트:  [도구 Governor] [셀·폭발 반경] [오토스케일 신호] [감시 경로 독립] [단계적 배포] [콜드 스타트]  <- 각각 따로
  실사건:
    AWS S3 2017     명령 입력 오류 -> 큰 용량 제거 -> 색인 서브시스템 전체 재시작 -> 수년 안 해 본 재시작이 오래 걸림
    Slack 2021      연휴 뒤 트래픽 급증 -> TGW 패킷 유실 -> 웹 계층 포화 -> 오토스케일·프로비저닝이 오히려 막힘
    Roblox 2021     새 기능(streaming) + 부하 -> Consul 경합 -> 서비스 디스커버리·스케줄러·비밀 저장소 동시 정지 -> 73시간
    CrowdStrike     설정 콘텐츠 한 번 배포 -> 커널 드라이버 범위 밖 읽기 -> Windows 크래시 -> 수동 복구(문서·스크립트)
```

쉬운 예: 큰 건물 정전이다.\
차단기 하나를 잘못 내린 것(방아쇠)은 몇 초 일이다.\
그런데 비상 발전기를 몇 년간 한 번도 돌려 본 적이 없었고, 비상구 안내등도 같은 전원에 물려 있었다. 그래서 복구가 몇 시간이 된다.

똑같은 구조다.\
S3의 방아쇠는 명령 입력 하나였다. 복구를 길게 만든 것은 "수년 동안 완전히 재시작해 본 적 없는" 서브시스템이었다.\
Slack과 Roblox는 장애 중에 대시보드·경보가 **장애 난 그 시스템에 기대고** 있어 진단이 늦었다.

이 노트는 당사자가 쓴 1차 출처로 네 사건을 복원하고, 각 고리를 이 영역 leaf에 붙인다.
- 시각·수치는 원문 그대로 옮긴다. 원문에 없는 연결과 계산은 "해석"·"계산"이라고 적는다.
- 다른 영역 사건 노트와 겹치는 주제: 준안정(metastable) 고장과 AWS EBS 2011은 [distributed/36](../../distributed/36-distributed-incidents/2-summary.md), 백업·복제·페일오버 사고(GitLab 2017, GitHub 2018)는 [database/57](../../database/57-db-incidents/2-summary.md)이 정본이다.

  - *사후 분석(postmortem)*: 장애 뒤 당사자가 타임라인·원인·재발 방지를 정리한 글. 이 노트의 네 출처가 모두 이것이다.
  - *방아쇠(trigger)와 확대 요인*: 방아쇠는 장애를 시작한 사건, 확대 요인은 그 장애를 크게·길게 만든 조건이다. 이 노트에서 둘을 나누는 것은 해석이다.

## 동작·원리

### 사건 1 — AWS S3 us-east-1: 입력 하나 잘못된 용량 제거 명령 (2017-02-28)

출처: AWS, "Summary of the Amazon S3 Service Disruption in the Northern Virginia (US-EAST-1) Region" <https://aws.amazon.com/message/41926/>. 시각은 원문대로 PST.

#### 무엇이 어디에 있었나

```text
   S3 팀원이 기존 플레이북으로 명령 실행
   의도: 과금(billing) 처리에 쓰는 서브시스템의 서버 "소수" 제거
   실제: 입력 하나가 잘못 → 훨씬 많은 서버 제거
                     |
       +-------------+--------------------+
       v                                  v
  [색인(index) 서브시스템]           [배치(placement) 서브시스템]
   리전 모든 객체의 메타데이터·위치       새 저장 공간 할당(PUT에 사용)
   GET·LIST·PUT·DELETE 모두에 필요       색인이 정상이어야 동작
       |                                  |
       +------ 둘 다 "전체 재시작" 필요 ------+
                     |
       재시작 동안 S3가 요청을 처리 못 함
       → S3에 기대는 서비스도 영향: S3 콘솔, EC2 새 인스턴스 시작,
         EBS(S3 스냅숏에서 데이터가 필요한 볼륨), Lambda
```

#### 타임라인 (PST, 원문)

| 시각 | 사건 | 이어지는 leaf |
|---|---|---|
| 09:37 | 권한 있는 S3 팀원이 확립된 플레이북으로 명령 실행, 입력 하나가 잘못돼 의도보다 큰 서버 집합 제거. 색인·배치 서브시스템이 전체 재시작 필요 | 도구 Governor [49-5](../49-steady-state-fail-fast-and-supervision/2-summary.md) · 런북 [44-2](../44-runbooks-and-operational-readiness/2-summary.md) |
| (재시작 중) | 큰 리전에서 색인·배치 서브시스템을 "수년간" 완전히 재시작한 적이 없었다. 그사이 크게 성장해, 재시작과 메타데이터 무결성 안전 점검이 예상보다 오래 걸림 | 해 보지 않은 복구 경로 [45-4](../45-chaos-and-resilience-testing/2-summary.md) · [46-1](../46-disaster-recovery/2-summary.md) |
| ~11:37 | 이때까지 AWS Service Health Dashboard(SHD)의 서비스별 상태를 못 바꿈 — SHD 관리 콘솔이 S3에 의존. 트위터 @AWSCloud와 SHD 배너 글로 대신 알림 | 감시·알림 경로의 독립 [43-5](../43-alerting-and-on-call/2-summary.md) |
| 12:26 | 색인 서브시스템이 GET·LIST·DELETE를 처리할 만큼 용량 활성화 | — |
| 13:18 | 색인 완전 복구, GET·LIST·DELETE 정상 | — |
| 13:54 | 배치 서브시스템 복구 완료(색인이 동작한 뒤 시작), S3 정상. 다른 서비스는 그동안 쌓인 적체를 처리하느라 더 걸림 | 적체 [30-5](../30-scheduler-and-cron-ha/2-summary.md) · [12-2](../12-backpressure-and-load-shedding/2-summary.md) |

- 계산: 09:37 → 13:54는 4시간 17분이다(원문에 이 합계는 없다).
- 원문의 재발 방지
  - 도구가 "너무 많은 용량을 너무 빨리" 뺄 수 있었다 → 더 천천히 빼도록 고침. 어떤 서브시스템도 **최소 필요 용량 아래로** 내려가지 않게 안전장치 추가. 다른 운영 도구도 같은 점검을 하는지 감사.
  - 핵심 서브시스템의 복구 시간 개선. 서비스를 셀(cell)이라는 작은 파티션으로 나누는 작업을 해 왔고, 색인 서브시스템의 추가 분할을 그해 뒤로 계획했다가 즉시 시작으로 앞당김.
  - SHD 관리 콘솔을 여러 리전에서 돌게 바꿈.

#### 신뢰성 관점으로 다시 보기 (해석)

- 사람의 입력 실수는 막을 수 없다고 보고 **도구가 받는 범위**를 막았다. 원문의 두 조치(제거 속도 제한, 최소 용량 하한)가 49번의 Governor 두 축(창당 상한, 남는 몫 하한)과 같다([49-5](../49-steady-state-fail-fast-and-supervision/2-summary.md)). 적용 3에 코드로 옮겼다.
- 방아쇠는 몇 초짜리 명령이었다. 시간을 결정한 것은 **평소에 안 쓰는 복구 경로**(전체 재시작)였다. 정기 훈련으로 경로를 살려 두는 이유다([45-4](../45-chaos-and-resilience-testing/2-summary.md) · [46-1](../46-disaster-recovery/2-summary.md)).
- 셀 분할은 폭발 반경과 함께 **복구 단위**를 줄인다. 원문은 셀을 "가장 큰 서비스·서브시스템의 복구 절차까지 평가·시험할 수 있게" 하는 수단으로 설명한다([51](../51-cells-stamps-and-blast-radius/2-summary.md)).
- 상태 페이지가 장애 대상에 기대면 고객 소통 경로까지 같이 끊긴다. 감시·알림 경로는 감시 대상과 다른 장애 도메인에 둔다([43-5](../43-alerting-and-on-call/2-summary.md)).

### 사건 2 — Slack: 연휴 뒤 첫 업무일 (2021-01-04)

출처: Laura Nolan, "Slack's Outage on January 4th 2021", Slack Engineering <https://slack.engineering/slacks-outage-on-january-4th-2021/>. 시각은 원문대로 PST.

#### 무엇이 어디에 있었나

```text
   클라이언트 (연휴 뒤 캐시가 차가움 → 첫 연결에서 평소보다 많은 데이터)
        |
   [로드 밸런서] ── 헬스체크 실패가 많으면 "panic mode": 모든 인스턴스로 분산
        |
   [웹 계층 (Apache 워커)] ── 오토스케일 신호: CPU 이용률 + 워커 스레드 이용률
        |                      provision-service가 새 인스턴스 구성·시험
        |
   [AWS Transit Gateway (TGW)] ── VPC들을 잇는 허브. AWS가 관리, 투명하게 확장되도록 설계
        |
   [백엔드 VPC들]        [대시보드·경보 서비스] ← DB와 다른 VPC에 있어 TGW에 의존
```

#### 타임라인 (PST, 원문)

| 시각 | 사건 | 이어지는 leaf |
|---|---|---|
| (미주 오전) | 외부 감시 서비스가 page — 에러율 상승. 사고 절차 시작. 조사 초기에 대시보드·경보 서비스가 불능. 그날 배포한 변경을 몇 개 롤백(원인 아니었음) | 감시 경로 [43-5](../43-alerting-and-on-call/2-summary.md) · 먼저 롤백 [26-1](../26-incident-response-and-postmortem/2-summary.md) |
| 06:57 | 메시지 전송 성공률 99%(평소 99.999% 초과) | SLI [02](../02-slo-sli-error-budget/2-summary.md) |
| 07:00 | 매시 정각·30분의 작은 피크(리마인더·외부 cron) + 네트워크 문제 → 웹 계층 포화. 패킷 유실 증가 → 백엔드 호출 지연 증가 → 웹 계층 자원 포화. Slack 불능 | Dogpile [48-4](../48-performance-and-stability-antipatterns-in-code/2-summary.md) |
| (같은 무렵) | 백엔드에 닿지 못하는 인스턴스를 자동화가 unhealthy로 표시해 교체 시도. 오토스케일이 웹 계층을 **축소** — 스레드가 기다리느라 CPU가 떨어짐. 조사 중이던 SSH 세션이 끊김. 축소를 끔 | 신호 혼동 [41-4](../41-autoscaling/2-summary.md) · 헬스체크 [12-4](../12-backpressure-and-load-shedding/2-summary.md) |
| 07:01~07:15 | 네트워크 악화로 워커 스레드 이용률이 오르자 급격히 **확장** — 웹 계층에 1,200대 추가 시도 | 확장 반응 [41-1](../41-autoscaling/2-summary.md) |
| (그 뒤) | provision-service가 같은 나쁜 네트워크 위에서 동시 대량 프로비저닝 → 두 자원 한도에 걸림: 가장 큰 것은 리눅스 open files 한도, 그리고 AWS 할당량. 덜 구성된 인스턴스가 많아 오토스케일 그룹 최대 크기에 걸림. 대시보드 인스턴스도 새로 못 띄움 | 준비 안 된 인스턴스 [41-5](../41-autoscaling/2-summary.md) · 자원 한도 [49-1](../49-steady-state-fail-fast-and-supervision/2-summary.md) |
| ~08:15 | provision-service 복구, 건강한 인스턴스가 서비스에 들어오며 개선 | — |
| ~09:15 | 웹 계층에 충분한 호스트. LB의 헬스체크 실패율은 여전히 매우 높았지만 panic mode + 재시도 + 서킷 브레이킹으로 서빙 재개 — "down이 아니라 degraded". 오류율을 낮출 만큼 프로비저닝하는 데 한 시간 더(네트워크가 덜 나아 평소보다 많은 인스턴스가 필요했고, 프로비저닝도 느렸음) | 헬스체크 오독 [47-2](../47-server-design-antipatterns/2-summary.md) · 서킷 [10](../10-circuit-breaker/2-summary.md) |
| ~10:40 | AWS가 자체 감시로 패킷 드롭을 보고 TGW 용량을 **수동으로** 늘림. 모든 AZ에 반영, 네트워크·오류율·지연 정상 | — |

- 원문의 원인 진술: TGW 하나가 과부하됐다. Slack의 연간 트래픽 패턴 — 연휴엔 낮고, 복귀 첫 월요일엔 클라이언트 캐시가 차가워 첫 연결에서 데이터를 더 받는다. "한 해 가장 조용한 때에서 가장 바쁜 날 중 하루로, 말 그대로 하룻밤 사이에" 간다. 자기 서빙 시스템은 빨리 확장했지만 TGW가 충분히 빨리 확장되지 않았다.
- 원문의 후속 조치: AWS가 큰 초당 패킷 수 증가에 대한 TGW 확장 알고리즘 검토. 다음 연휴 끝에 TGW 선제 확장을 요청하도록 알림 설정. 대시보드 서비스를 DB와 같은 VPC로 옮겨 TGW 의존 제거. provision-service 정기 부하 테스트. 헬스체크·오토스케일 설정 재평가.

#### 신뢰성 관점으로 다시 보기 (해석)

- **예측 가능한 급증**이었다. 같은 일이 해마다 오고, 원문의 조치도 "다음 연휴 끝에 선제 확장 요청"이다. 반응형 확장(여기서는 공급자가 관리하는 TGW의 확장)이 급증보다 느리면 사전 확장으로 덮는다([41-1](../41-autoscaling/2-summary.md) · [22-5](../22-capacity-and-load-testing/2-summary.md)).
- 오토스케일 신호가 한 번은 반대로 움직였다. 네트워크 대기로 CPU가 떨어지자 **축소**했고, 곧 스레드 이용률로 **확장**했다. CPU는 "일이 많다"와 "막혀 있다"를 가르지 못한다([41-4](../41-autoscaling/2-summary.md) · [16-5](../16-metrics-and-golden-signals/2-summary.md)).
- 복구 수단(인스턴스 교체·대량 확장)이 **자기 의존성**(provision-service, 같은 네트워크, 파일 한도·할당량)에 막혔다. 복구 경로도 부하 테스트 대상이다. 원문의 조치가 그것이다.
- 헬스체크 실패를 "죽음"으로 읽었다면 LB가 대부분을 뺐을 것이다. panic mode는 "많이 실패하면 차라리 전부에 나눈다"는, 헬스체크 오독을 막는 장치로 동작했다([47-2](../47-server-design-antipatterns/2-summary.md) · [52 §11](../52-reliability-symptom-index/2-summary.md)).
- 대시보드·경보가 장애 난 네트워크에 기댔다. 원문은 감시 도구를 인프라에서 "가능한 한 독립적으로" 두려 했지만 VPC 배치가 TGW 의존을 만들었다고 적는다([43-5](../43-alerting-and-on-call/2-summary.md)).
- 준안정 고장과의 비교: 확장·교체가 부하를 키운 되먹임은 있었다. 그러나 방아쇠(TGW 포화)는 10:40 수동 확장 전까지 남아 있었으므로, "방아쇠를 없애도 남는 장애"라는 Bronson 외의 정의에 그대로 들어맞는지는 원문만으로 판단하기 어렵다([distributed/36](../../distributed/36-distributed-incidents/2-summary.md)의 metastable 절).

### 사건 3 — Roblox: Consul 73시간 (2021-10-28~31)

출처: Daniel Sturman 외(Roblox·HashiCorp), "Roblox Return to Service 10/28-10/31 2021", Roblox 블로그 2022-01-20 <https://about.roblox.com/newsroom/2022/01/roblox-return-to-service-10-28-10-31-2021>(옛 주소 blog.roblox.com에서 넘어옴). 원문 각주: 모든 날짜·시각은 PST.

#### 무엇이 어디에 있었나

```text
   18,000대 이상 서버, 170,000 컨테이너 (자체 데이터센터)
                         
   [Nomad] 스케줄링 ─┐
   [Vault] 비밀값   ─┼──> [Consul 클러스터 하나]  ── voter 5 + non-voter 5, Raft 리더 하나
   [서비스들]       ─┘     서비스 디스커버리 · 헬스체크 · 세션 락 · KV
                            |
                            └ Raft 로그는 BoltDB 파일에 저장
   감시(텔레메트리) 시스템도 Consul에 기댐 → 순환 의존
```

- 원문: Consul이 건강하지 않으면 서비스끼리 서로를 찾지 못하고, Nomad·Vault도 Consul에 기대므로 새 컨테이너를 못 띄우고 운영 비밀값을 못 가져온다. "Consul이 단일 장애점이었다."

#### 타임라인 (PST, 원문)

| 시각 | 사건 | 이어지는 leaf |
|---|---|---|
| 10-27 14:00 | (하루 전) 트래픽 라우팅 백엔드 서비스에 Consul streaming 기능을 켬. 연말 트래픽 대비로 라우팅 노드도 50% 늘림. streaming은 몇 달 전 1.9 → 1.10 업그레이드로 들여와 일부 서비스에 점진 적용 중이었음 | 변경 [23-5](../23-deployment-strategies/2-summary.md) |
| 10-28 13:37 | Vault 성능 저하, Consul 서버 하나의 CPU 높음. 아직 플레이어 영향 없음. KV 쓰기 p50이 평소 300ms 미만 → 2초 | 지연 SLI [02](../02-slo-sli-error-budget/2-summary.md) |
| (진단 1) | 하드웨어 저하를 의심해 노드 하나 교체 — 효과 없음 | 추측 진단 [20-2](../20-performance-method-and-amdahl/2-summary.md) |
| 16:35 | 온라인 플레이어가 평소의 50%로 떨어짐, 결국 전면 장애 | — |
| (진단 2) ~19:00 | 트래픽 한계를 의심해 전 노드를 128코어(2배)·NVMe 새 장비로 교체. 대부분 옮겼지만 여전히 비정상, KV 쓰기 p50 약 2초 | 증설로 덮기 [21-1](../21-scaling-principles/2-summary.md) |
| 10-29 02:00~04:00 | 복귀 시도 1: 리더가 다른 voter와 자주 어긋남. 장애 시작 무렵의 스냅숏으로 클러스터 상태를 되돌림(설정 데이터 일부 유실 감수, 사용자 데이터 아님). 내부 서비스 부하를 막으려 iptables로 차단 후 해제 → 다시 악화. "14시간 넘게" 지나도록 원인 모름 | 부하 차단 후 점진 복귀 [12-2](../12-backpressure-and-load-shedding/2-summary.md) |
| 10-29 04:00~10-30 02:00 | 복귀 시도 2 (진단 3): 비필수 Consul 사용을 끄고 서비스를 한 자릿수 인스턴스로 축소, 헬스체크 주기 60초 → 10분. 16:00(24시간 넘게) 재개 → 02:00 다시 비정상, 부하가 훨씬 적은데도 | — |
| 10-30 02:00~12:00 | 디버그 로그·OS 지표에서 KV 쓰기가 오래 막히는 "경합" 확인. 128코어가 악화시켰을 수 있다고 보고 64코어로 되돌림 — 효과 없음(진단 4) | 프로파일링 [36](../36-profiling/2-summary.md) |
| 10-30 12:00~20:00 | perf 보고서·플레임 그래프에서 streaming 코드 경로가 경합의 원인임을 확인. 모든 Consul에서 streaming 끔. 15:51 설정 전파 완료, KV 쓰기 p50 300ms로. 일부 리더가 여전히 느림 → 그 서버가 리더로 남지 않게 막는 우회 | 플레임 그래프 [36-1](../36-profiling/2-summary.md) |
| 10-30 20:00~10-31 05:00 | "54시간". 캐시 시스템(평소 초당 10억 요청) 재배포 중 문제 셋: 스냅숏 리셋 탓으로 보이는 잘못된 스케줄링 KV 데이터, 비정상 노드를 비어 있다고 본 스케줄러, 무에서 큰 클러스터를 띄우는 데 맞지 않는 배포 도구. 05:00("61시간") Consul·캐시 정상 | 콜드 스타트 [42-5](../42-cold-start-and-scale-from-zero/2-summary.md) · 해 보지 않은 경로 [45-4](../45-chaos-and-resilience-testing/2-summary.md) |
| 10-31 05:00~16:45 | 서비스들을 맞는 용량으로 재시작, 10:00 플레이어 받을 준비. 콜드 캐시라 DNS steering으로 무작위 일부만 들이고 나머지는 정적 점검 페이지로. 약 10%씩 올리며 DB 부하·캐시·안정성 확인. 16:45(일요일, "73시간") 100% | 점진 투입 [22-5](../22-capacity-and-load-testing/2-summary.md) · [29-3](../29-cache-stampede/2-summary.md) |

- 원문의 근본 원인 둘
  - streaming: 전체로는 더 효율적이지만 롱 폴링보다 동시성 제어 요소(Go 채널)를 적게 썼다. 읽기·쓰기 부하가 모두 매우 높으면 Go 채널 하나에 경합이 몰려 쓰기가 막혔다. 128코어 장비는 이중 소켓 NUMA라 공유 자원 경합이 더 나빴다.
  - BoltDB freelist: 장애 뒤 HashiCorp가 밝혔다. 4.2GB 로그 저장소에 실제 데이터는 489MB, 3.8GB가 빈 공간이었다. freelist는 빈 페이지 ID 거의 100만 개로 7.8MB였다. Raft 쓰기(배치 뒤) 하나마다, 붙이는 데이터는 16kB 이하인데 7.8MB freelist를 디스크에 새로 썼다. 이 쓰기의 역압이 TCP 버퍼를 가득 채워, 비정상 리더의 2~3초 쓰기 시간에 기여했다. 기존 BoltDB 도구로 압축(compact)해 해결했다.
- 원문의 후속 조치: 텔레메트리와 Consul의 순환 의존 제거. 지리적으로 다른 데이터센터·다중 AZ. 핵심 서비스를 전용 Consul 클러스터로 분리, Consul KV를 저장소로 쓰던 데이터 이전, 낡은 KV 삭제(성능 개선). freelist 무한 증가 문제가 없는 bbolt로 교체(연말 피크를 피해 Q1). 캐시 배포 메커니즘을 "정지 상태에서 빠르게 띄우기"에 맞게 재설계. streaming은 새 구현을 규모에서 시험한 뒤 재도입.
- 계산: 원문의 경과 시간은 한 기준점으로 모두 맞지는 않는다. 10-28 13:37을 기준으로 하면 "14시간 넘게"(04:00, 14.4시간)·"24시간 넘게"(16:00, 26.4시간)·"54시간"(20:00, 54.4시간)은 맞지만, 10-31 05:00은 약 63.4시간(원문 61), 16:45는 약 75.1시간(원문 73)이다. 16:35(플레이어 50% 하락)를 기준으로 하면 16:45가 약 72.2시간이다. 원문은 기준 시각을 밝히지 않는다.

#### 신뢰성 관점으로 다시 보기 (해석)

- **공유 구성 요소 하나**(Consul 클러스터)가 디스커버리·스케줄링·비밀값·감시를 모두 받쳤다. 셀로 나누지 않은 전역 공유 요소의 장애는 전 서비스 동시 중단이 된다([51-1](../51-cells-stamps-and-blast-radius/2-summary.md)). 원문의 조치(전용 클러스터 분리, 다중 데이터센터)가 그 방향이다.
- 진단이 네 번 빗나갔다(하드웨어 → 트래픽 → 재연결 폭주 → 코어 수). 원인을 찾은 것은 측정(perf·플레임 그래프)이었다. 추측으로 장비를 바꾸고 늘린 것은 병목이 아닌 곳을 고친 셈이다([36-1](../36-profiling/2-summary.md) · [20-2](../20-performance-method-and-amdahl/2-summary.md)).
- 방아쇠가 된 변경(streaming 확대 적용)과 증상 사이에 **하루**가 있었다. 변경 직후가 아니라 부하 조건이 맞을 때 터졌으므로 "언제부터"만으로는 바로 연결되지 않았다. 카나리·단계 배포에서 "시간대·부하"를 단계 기준에 넣는 이유다([23-5](../23-deployment-strategies/2-summary.md)).
- BoltDB freelist는 **쌓이기만 하는 자원**의 문제다. 지운 로그의 페이지가 줄지 않고 빈 페이지 목록이 커졌다. 정리·압축이 정상 운영에 들어 있어야 한다([49-1](../49-steady-state-fail-fast-and-supervision/2-summary.md)).
- 복귀는 콜드 스타트 문제였다. 캐시를 다시 띄우고, 들어올 사용자 비율을 DNS로 10%씩 올렸다. 이것은 입장 제어(로드 셰딩의 반대 방향)다([42-5](../42-cold-start-and-scale-from-zero/2-summary.md) · [12](../12-backpressure-and-load-shedding/2-summary.md)).
- 텔레메트리의 순환 의존은 Slack의 대시보드 VPC 문제와 같은 모양이다. 감시는 감시 대상에 기대지 않아야 한다([43-5](../43-alerting-and-on-call/2-summary.md)).

### 사건 4 — CrowdStrike: 채널 파일 291 (2024-07-19)

출처: CrowdStrike, "Falcon Content Update Preliminary Post Incident Report"(예비 PIR, 2024-07-25 1900 UTC 갱신판) <https://www.crowdstrike.com/en-us/blog/falcon-content-update-preliminary-post-incident-report/>, "External Technical Root Cause Analysis — Channel File 291"(RCA, 2024-08-06) <https://www.crowdstrike.com/wp-content/uploads/2024/08/Channel-File-291-Incident-Root-Cause-Analysis-08.06.2024.pdf>. 영향 규모는 Microsoft 블로그(David Weston, 2024-07-20) <https://blogs.microsoft.com/blog/2024/07/20/helping-our-customers-through-the-crowdstrike-outage/>.

#### 무엇이 어디에 있었나

```text
   [센서 릴리스 (코드)]                         [Rapid Response Content (설정 데이터)]
   Template Type = 코드, 센서에 컴파일          Template Instance = 정규식 매칭 조건
   단계적 롤아웃 + 고객이 N/N-1/N-2 선택        Content Validator가 검사 → Channel File로 배포
             |                                              |
             +--------------> [Falcon 센서 (Windows 커널 드라이버, 부팅 초기에 로드)]
                              Content Interpreter가 Channel File을 읽어 매칭
```

```text
  IPC Template Type (센서 7.11)
    정의(Template Type Definitions): 입력 필드 21개
    센서 통합 코드가 실제로 넘기는 입력:  20개
                                         ┌─ 21번째 조건이 와일드카드 → 21번째를 안 읽음 → 문제 없음 (3월~4월 배포, 시험)
    Template Instance의 21번째 필드 ─────┤
                                         └─ 21번째 조건이 와일드카드가 아님 → 21번째를 읽음 → 입력 배열 범위 밖 읽기 → 크래시 (7-19)
```

#### 타임라인 (원문)

| 날짜·시각 | 사건 | 이어지는 leaf |
|---|---|---|
| 2024-02-28 | 센서 7.11 정식 배포. 이름 있는 파이프 등 IPC 남용을 탐지할 새 IPC Template Type 도입 | — |
| 03-05 | 스테이징에서 IPC Template Type 스트레스 시험 통과. 같은 날 IPC Template Instance 운영 배포 | — |
| 04-08~04-24 | IPC Template Instance 세 개 추가 배포, 운영에서 정상 | — |
| 07-19 04:09 UTC | Windows 센서용 콘텐츠 설정 업데이트(IPC Template Instance 둘) 배포. Content Validator의 버그로 하나가 문제 있는 콘텐츠를 담고도 검증 통과. 받은 센서에서 범위 밖 메모리 읽기 → 예외를 처리하지 못해 Windows 크래시(BSOD) | 단계적 배포 부재 [23-5](../23-deployment-strategies/2-summary.md) · 플래그·설정 [24-2](../24-feature-flag-lifecycle/2-summary.md) |
| 07-19 05:27 UTC | 결함 있는 콘텐츠 되돌림. 이후 켜지거나 그 사이 연결하지 않은 시스템은 영향 없음 | — |
| 07-20 | Microsoft: 영향 Windows 기기 850만 대 추정, 전체 Windows의 1% 미만. 수동 복구 문서·스크립트 게시 | — |
| 07-19~07-27 | 센서 콘텐츠 컴파일러가 Template Type 입력 수를 검사하는 패치: 7-19 개발, 7-27 운영 투입 | — |
| 07-25 | Content Interpreter의 입력 문자열 조회 함수에 범위 검사 추가, 입력 배열 크기 = 기대 입력 수 검사 추가 | Fail Fast [49-2](../49-steady-state-fail-fast-and-supervision/2-summary.md) |
| 07-25 (발표) | CEO LinkedIn 게시: 7-25 기준 Windows 센서 97% 넘게 온라인. 회복이 빨라진 이유로 "자동 복구 기법(automatic recovery techniques)" 개발을 듦(원 게시물은 못 열었고 TechTarget 7-26 보도의 인용) | — |
| 07-29 17:00 PT 기준 | 주간 비교로 Windows 센서의 약 99%가 업데이트 전 대비 온라인(주간 변동은 보통 약 1%). 8-06자 RCA 서문이 든 시점 스냅숏이다 | — |
| 08-09 / 08-19 | 7.11 이상 모든 Windows 센서에 핫픽스(입력 수 21 수정·범위 검사) 정식 배포 예정 / Content Validator 새 검사 운영 투입 예정 | — |

- 원문의 원인 진술(RCA): 세 가지가 겹쳤다 — (1) Content Validator가 검증한 입력 21개와 Content Interpreter에 실제로 주어진 20개의 불일치, (2) Content Interpreter의 잠복한 범위 밖 읽기, (3) 21번째 필드에 와일드카드가 아닌 조건을 쓰는 시험의 부재. 자동 시험은 정적 시험 사례 12개였고, 시험용 채널 파일의 21번째 필드가 모두 와일드카드였다.
- 원문의 재발 방지(배포 쪽): Rapid Response Content도 카나리부터 점점 큰 링으로 단계 배포하고, 링마다 bake 시간 동안 원격 측정을 보고 다음 링으로 올리거나 되돌린다. 고객이 콘텐츠 업데이트를 어디에·언제 받을지 고를 수 있게 한다.
- 계산: 04:09 → 05:27은 78분이다. 원문은 이 창에 온라인이던 센서가 영향 범위라고 적는다.

#### 신뢰성 관점으로 다시 보기 (해석)

- **설정도 변경이다.** 센서 코드는 단계 롤아웃과 N-1·N-2 선택을 거쳤지만, Rapid Response Content는 "코드가 아니라 설정 데이터"로 분류돼 전 대상에 한 번에 나갔다. 원문의 조치가 바로 콘텐츠에도 카나리·링을 두는 것이다. 메시 설정 오류가 전 서비스 장애가 되는 것([50-4](../50-sidecar-ambassador-and-service-mesh/2-summary.md))과 같은 모양이다.
- 폭발 반경을 정한 것은 **배포 방식**이었다. 78분 창에 온라인이었고 업데이트를 받은 7.11 이상 Windows 호스트 전부였다(PIR). 웨이브·셀 단위 배포는 결함이 같아도 반경을 줄인다([51](../51-cells-stamps-and-blast-radius/2-summary.md) · [23-5](../23-deployment-strategies/2-summary.md)).
- **되돌림이 복구가 아니었다.** 05:27에 콘텐츠를 되돌렸지만 이미 크래시한 호스트는 그대로였다. 원문 사실은 셋이다: 채널 파일은 호스트 디스크에 쓰이고(PIR), 커널 드라이버는 부팅 초기에 올라오며(RCA), Microsoft는 수동 복구 문서·스크립트를 냈다. 해석: 재부팅한 호스트가 새 콘텐츠를 받기 전에 디스크의 옛 파일을 다시 읽으면 같은 크래시가 되풀이될 수 있다. CrowdStrike는 7-25에 97% 넘게 온라인이라고 밝히며 자동 복구 기법을 들었다. 8-06자 RCA는 "7-29 17:00 PT 기준" 주간 비교로 약 99%(평소 주간 변동 약 1%)라고 적는다. 99%에 처음 닿은 시각은 원문에 없다. 해석: 초기에는 호스트마다 수동 조치가 필요했고, 평소 변동 범위 근처까지 돌아오는 데 며칠 단위가 걸렸다. "롤백 가능"은 롤백 명령이 닿는 대상에서만 성립한다([23-2](../23-deployment-strategies/2-summary.md)).
- 검증기(Content Validator)를 믿고 배포했다. 원문은 이전 성공 배포와 검증기에 대한 신뢰를 배포 근거로 든다. 검증기도 결함이 있을 수 있으므로 단계 배포가 마지막 방어선이다. 시험 관점은 [testing/21-test-incidents](../../testing/21-test-incidents/2-summary.md)로 넘긴다.
- 입력 개수 불일치를 런타임에 검사하지 않았다. 범위 검사는 손상된 입력을 끝까지 들고 가지 않는 Fail Fast다. 커널 안에서는 실패가 곧 OS 크래시라 비용이 크다([49-2](../49-steady-state-fail-fast-and-supervision/2-summary.md) · [49-3](../49-steady-state-fail-fast-and-supervision/2-summary.md)).

### 네 사건을 나란히 (해석)

| | 방아쇠 | 확대 요인 | 복구를 늦춘 것 | 감시·소통 | 원문의 핵심 조치 |
|---|---|---|---|---|---|
| AWS S3 2017 | 명령 입력 오류 | 도구에 제거 속도·최소 용량 제한 없음 | 수년간 안 해 본 전체 재시작 | SHD가 S3에 의존 | 도구 Governor, 셀 분할 가속, SHD 다중 리전 |
| Slack 2021 | 연휴 뒤 트래픽 급증 + TGW 확장 지연 | 오토스케일 축소·대량 확장, 헬스체크 기반 교체 | provision-service의 파일 한도·할당량 | 대시보드가 TGW에 의존 | 선제 확장, 대시보드 VPC 이동, provision-service 부하 시험 |
| Roblox 2021 | streaming 확대 + 높은 부하 | Consul 단일 클러스터에 모든 것이 기댐, BoltDB freelist | 오진 네 번, 콜드 캐시·도구 부적합 | 텔레메트리가 Consul에 의존 | 순환 의존 제거, 클러스터 분리, bbolt, 다중 데이터센터 |
| CrowdStrike 2024 | 검증기를 통과한 문제 콘텐츠 | 전 대상 동시 배포 | 크래시한 호스트는 원격 되돌림이 안 닿음 | — | 콘텐츠 링 배포, 고객 제어, 입력 수·범위 검사 |

- 공통 1: **방아쇠는 작았고 길이를 정한 것은 복구 경로**였다. 평소에 안 쓰는 경로(전체 재시작, 무에서 띄우기, 수동 복구)가 가장 느렸다.
- 공통 2: 셋에서 **감시·알림이 장애 대상에 기댔다.** 장애 때 진단 속도를 떨어뜨린 공통 원인이다.
- 공통 3: 원문 조치의 대부분이 "잘못을 막자"가 아니라 **"잘못이 퍼지는 범위와 속도를 줄이자"**다(속도 제한, 하한, 셀, 링, 분리).

### 실행 확인: S3형 운영 도구 앞의 Governor

S3 원문의 두 조치(천천히 빼기, 최소 용량 아래로 못 내리기)를 49번의 Governor 모양으로 옮겼다. 입력 오타(4 → 400)를 넣어 본다.

```java
/** 운영 도구의 "용량 제거" 명령 앞에 두는 Governor: 최소 용량 하한 + 창당 제거 상한. */
synchronized String remove(int requested, Instant now) {
    while (!removals.isEmpty() && removals.peekFirst().isBefore(now.minus(window))) removals.pollFirst();
    int byFloor = capacity - minCapacity;                       // 하한까지 남은 여유
    int byRate = maxRemovePerWindow - removals.size();          // 이번 창에 남은 몫
    int allowed = Math.max(0, Math.min(requested, Math.min(byFloor, byRate)));
    for (int i = 0; i < allowed; i++) removals.addLast(now);
    capacity -= allowed;
    ...
}
// new Governor(용량 1000, 하한 800, 창당 20대, 창 10분)
```

(실행 확인, eclipse-temurin:21-jdk 컨테이너 — OpenJDK 21.0.12, `--cpus=2`, 2026-10-01. 결정적 출력)

```text
요청    4 → 제거  4, 남은 용량  996  [전부 허용]
요청  400 → 제거 16, 남은 용량  980  [창당 상한(20/10분)]
요청   10 → 제거  0, 남은 용량  980  [창당 상한(20/10분)]
요청   30 → 제거  4, 남은 용량  976  [창당 상한(20/10분)]
요청   20 → 제거  0, 남은 용량  800  [최소 용량 하한(800)]
```

- 오타 400은 창당 상한에 걸려 16대(20 − 앞서 뺀 4)만 빠졌다. 사람이 이상을 알아챌 시간을 번다.
- 11분 뒤 요청 30은 4대만 허용됐다. 0분에 뺀 4대는 창 밖으로 나갔지만 1분에 뺀 16대는 아직 창 안이다.
- 반복 요청으로 800에 닿은 뒤에는 하한이 막는다. S3 원문의 "최소 필요 용량 아래로 내려가지 않게"에 해당한다.
- 한계(해석): 하한 값이 맞아야 한다. 서브시스템의 최소 필요 용량을 모르면 Governor는 숫자만 지킨다. S3도 "다른 운영 도구도 같은 점검을 하는지 감사"를 조치에 넣었다.

## 쓰이는 자료구조·알고리즘

- **의존 그래프와 순환 탐지**: "감시 → 감시 대상"을 간선으로 그리면 Slack(대시보드 → TGW), Roblox(텔레메트리 → Consul), S3(SHD 콘솔 → S3)는 감시 경로가 감시 대상에 닿는다. 그래프에서 사이클·공유 노드를 찾는 것이 점검이다(DFS).
- **슬라이딩 윈도 카운터**: Governor의 창당 제거 상한(실행 확인). 레이트 리미터와 같은 구조다([11](../11-rate-limiter/2-summary.md)).
- **링(ring) 단계 배포**: 대상 집합을 카나리 ⊂ 링1 ⊂ 링2 …로 나누고 단계마다 bake 시간과 판정을 둔다. CrowdStrike의 조치다. 비율 기반 입장 제어(Roblox의 DNS steering 10% 단계)와 같은 "점진 확대" 알고리즘이다.
- **Raft 로그 + 빈 페이지 목록(freelist)**: BoltDB는 지운 페이지를 freelist에 모아 재사용한다. 목록이 커지면 쓰기마다 목록 전체를 다시 쓰는 비용이 생겼다(Roblox). 합의 로그는 [distributed/11](../../distributed/11-consensus-raft/2-summary.md).
- **배열 범위 검사**: 입력 개수(20)와 기대 개수(21)의 불일치를 런타임에 거르는 가장 단순한 불변식 검사(CrowdStrike RCA의 조치).

## 적용 — 풀어나가는 법

### 1. 사고 보고서를 신뢰성 관점으로 읽는 순서

1. **방아쇠**와 **확대 요인**을 나눈다. 방아쇠만 적고 닫으면 같은 확대 요인이 다른 방아쇠로 다시 온다(metastable 관점 — [distributed/36](../../distributed/36-distributed-incidents/2-summary.md)).
2. 시간이 어디서 길어졌나를 본다. 탐지·진단·완화·복구 중 어느 구간인가. 네 사건 모두 복구 구간이 길었다.
3. 감시·소통 경로가 장애 대상에 기댔나를 본다.
4. 원문 조치를 "실수 방지"와 "반경·속도 제한"으로 나눈다. 내 시스템에는 뒤쪽이 더 잘 옮겨진다.
5. 원문의 시각·수치와 내 해석을 섞지 않는다. 경과 시간 같은 계산은 계산이라고 적는다(Roblox의 "73시간"처럼 원문 안에서도 기준이 흔들릴 수 있다).

### 2. 내 시스템으로 옮길 점검 목록

| 사건 | 질문 | leaf |
|---|---|---|
| S3 | 용량을 빼거나 지우는 운영 도구에 창당 상한·최소 용량 하한·dry-run이 있나? | [49-5](../49-steady-state-fail-fast-and-supervision/2-summary.md) |
| S3 | 가장 큰 서브시스템을 **완전히** 재시작해 본 게 언제인가? 걸린 시간을 아는가? | [45-4](../45-chaos-and-resilience-testing/2-summary.md) · [46-1](../46-disaster-recovery/2-summary.md) |
| S3·Slack·Roblox | 상태 페이지·대시보드·경보가 감시 대상과 다른 장애 도메인에 있나? | [43-5](../43-alerting-and-on-call/2-summary.md) |
| Slack | 해마다 오는 급증(연휴 뒤·연말·이벤트)에 사전 확장 일정이 있나? 공급자 관리 구성 요소(게이트웨이·NAT·LB)도 포함했나? | [41-1](../41-autoscaling/2-summary.md) · [22-5](../22-capacity-and-load-testing/2-summary.md) |
| Slack | 오토스케일 신호가 "막혀 있다"를 "한가하다"로 읽을 수 있나? 장애 중 축소를 끄는 스위치가 있나? | [41-4](../41-autoscaling/2-summary.md) |
| Slack | 복구 수단(프로비저닝)도 부하 시험했나? 파일 한도·할당량은? | [22](../22-capacity-and-load-testing/2-summary.md) |
| Roblox | 디스커버리·스케줄러·비밀값이 같은 클러스터 하나에 기대나? | [51-1](../51-cells-stamps-and-blast-radius/2-summary.md) |
| Roblox | 무에서 전체를 띄우는(bootstrapping) 절차와 점진 입장 장치(비율 기반 입장)가 있나? | [42-5](../42-cold-start-and-scale-from-zero/2-summary.md) · [12](../12-backpressure-and-load-shedding/2-summary.md) |
| CrowdStrike | 설정·콘텐츠·플래그 배포도 코드처럼 카나리·링·bake를 거치나? | [23-5](../23-deployment-strategies/2-summary.md) · [24](../24-feature-flag-lifecycle/2-summary.md) · [50-4](../50-sidecar-ambassador-and-service-mesh/2-summary.md) |
| CrowdStrike | 롤백 명령이 닿지 않는 상태(부팅 불가·연결 끊김)에서의 복구 절차가 있나? | [44](../44-runbooks-and-operational-readiness/2-summary.md) |

### 3. 사고 문서에 남길 것

- 타임라인은 원 시각대로(UTC·PST 표기 포함), 출처 시스템과 함께 적는다.
- "처음 인지" 시각과 "선언" 시각을 나눠 적는다([26-4](../26-incident-response-and-postmortem/2-summary.md)).
- 진단 가설과 그 가설을 버린 근거를 적는다. Roblox는 네 번의 진단 시도를 번호를 매겨 기록했다.

## 장애 시나리오와 대처

이 절은 사건을 **잘못 읽고 잘못 옮기는 것**을 다룬다.

### 1. "사람 실수"로 닫는다 — S3형

- **현상**: 운영자가 잘못된 대상을 지워 장애가 났다. 포스트모템 조치가 "교육·주의"다. 몇 달 뒤 다른 도구에서 같은 모양이 난다.
- **보이는 형태**: 조치 항목에 도구 변경이 없다. 같은 도구로 같은 크기의 명령이 여전히 가능하다.
- **원인**: 방아쇠를 근본 원인으로 적었다. S3 원문은 사람이 아니라 도구가 "너무 많이, 너무 빨리" 뺄 수 있었던 것을 고쳤다.
- **대처**: 도구에 창당 상한·최소 하한·dry-run(적용 2). 다른 도구도 감사한다. 비난 없는 포스트모템([26-2](../26-incident-response-and-postmortem/2-summary.md)).

### 2. 장애 중 대시보드가 같이 죽는다 — Slack·Roblox형

- **현상**: 에러율이 오르기 시작한 직후 대시보드·경보가 사라졌다. 엔지니어들이 지표 백엔드에 직접 쿼리하며 진단한다.
- **보이는 형태**: 감시 서비스의 오류가 장애 대상(네트워크 허브·디스커버리)의 오류와 같은 시각에 시작.
- **원인**: 감시 경로가 감시 대상에 기댔다(VPC 배치, 텔레메트리 → Consul).
- **대처**: 감시 의존 그래프를 그려 공유 노드를 없앤다. 외부 블랙박스 감시와 dead man's switch를 둔다([43-5](../43-alerting-and-on-call/2-summary.md)).

### 3. 오토스케일이 장애 중에 반대로 움직인다 — Slack형

- **현상**: 하류 네트워크가 느려진 순간 레플리카가 **줄었다가** 곧 대량으로 늘었다. 늘린 인스턴스 대부분이 준비되지 못했다.
- **보이는 형태**: CPU 하락 → 축소 이벤트, 워커 스레드 이용률 상승 → 확장 이벤트, 준비 안 된 인스턴스가 그룹 최대 크기를 채움.
- **원인**: CPU가 대기를 한가함으로 읽었다. 대량 확장이 프로비저닝 경로의 한도(open files·할당량)에 걸렸다.
- **대처**: 장애 중 축소를 끄는 스위치, 확장 속도 상한, 프로비저닝 경로 부하 시험. 예측 가능한 급증은 사전 확장([41-4](../41-autoscaling/2-summary.md) · [41-5](../41-autoscaling/2-summary.md)).

### 4. 추측으로 장비를 바꾸며 시간을 쓴다 — Roblox형

- **현상**: 공유 구성 요소가 느려 하드웨어를 바꾸고, 더 큰 장비로 바꾸고, 다시 작은 장비로 바꿨다. 매번 효과가 없다.
- **보이는 형태**: 같은 지표(KV 쓰기 p50 2초)가 장비 교체 뒤에도 그대로.
- **원인**: 가설을 측정으로 가르지 않았다. 원인은 소프트웨어 경합과 자료 구조(freelist) 문제였다.
- **대처**: 바쁜 프로세스의 플레임 그래프·perf를 먼저 뜬다. 바꾼 것 하나마다 재측정한다([36-1](../36-profiling/2-summary.md) · [20-2](../20-performance-method-and-amdahl/2-summary.md)). 진단 시도와 기각 근거를 사고 문서에 남긴다.

### 5. "설정이라서" 한 번에 내보낸다 — CrowdStrike형

- **현상**: 코드 배포는 단계적인데, 탐지 규칙·플래그·라우팅 설정은 전 대상에 즉시 나간다. 설정 하나로 전체가 동시에 멈춘다.
- **보이는 형태**: 무관해 보이는 대상들이 같은 시각에 함께 실패. 시각이 설정 배포와 일치.
- **원인**: 실행 동작을 바꾸는 데이터를 코드와 다른 위험 등급으로 분류했다. 검증기 통과를 안전의 근거로 삼았다.
- **대처**: 설정·콘텐츠도 카나리 → 링 → bake → 판정. 받는 쪽은 형식·개수·범위를 런타임에 검사하고, 실패하면 직전 정상본으로 돌아간다. 롤백이 닿지 않는 상태의 복구 절차를 런북에 둔다([50-4](../50-sidecar-ambassador-and-service-mesh/2-summary.md) · [24-2](../24-feature-flag-lifecycle/2-summary.md) · [44](../44-runbooks-and-operational-readiness/2-summary.md)).

## 핵심 문장

- 네 사건 모두 방아쇠는 작았다(명령 입력 하나, 연휴 뒤 출근, 기능 하나 켜기, 콘텐츠 파일 하나). 장애의 길이를 정한 것은 평소에 안 쓰던 복구 경로였다.
- S3 원문은 사람을 고치지 않고 도구를 고쳤다. 제거 속도 제한과 최소 용량 하한은 Governor의 두 축이다.
- 감시·상태 페이지가 장애 대상에 기대면 진단과 소통이 함께 끊긴다(S3의 SHD, Slack의 대시보드, Roblox의 텔레메트리).
- 공유 구성 요소 하나(Consul 클러스터, TGW)가 여러 기능을 받치면 그 하나의 장애가 전부의 장애가 된다.
- 설정·콘텐츠도 실행 동작을 바꾸는 변경이다. CrowdStrike 원문의 조치는 콘텐츠에도 카나리와 링을 두는 것이었다.
- 사고 보고서의 시각·수치는 원문 그대로 옮기고, 계산과 해석은 따로 표시한다.

## 관련 주제·근거

- 선행: [52-reliability-symptom-index](../52-reliability-symptom-index/2-summary.md) — 증상 단위 색인. 이 노트는 사건 단위
- 이 노트가 이은 leaf: [12](../12-backpressure-and-load-shedding/2-summary.md) · [22](../22-capacity-and-load-testing/2-summary.md) · [23](../23-deployment-strategies/2-summary.md) · [24](../24-feature-flag-lifecycle/2-summary.md) · [26](../26-incident-response-and-postmortem/2-summary.md) · [36](../36-profiling/2-summary.md) · [41](../41-autoscaling/2-summary.md) · [42](../42-cold-start-and-scale-from-zero/2-summary.md) · [43](../43-alerting-and-on-call/2-summary.md) · [44](../44-runbooks-and-operational-readiness/2-summary.md) · [45](../45-chaos-and-resilience-testing/2-summary.md) · [46](../46-disaster-recovery/2-summary.md) · [49](../49-steady-state-fail-fast-and-supervision/2-summary.md) · [50](../50-sidecar-ambassador-and-service-mesh/2-summary.md) · [51](../51-cells-stamps-and-blast-radius/2-summary.md)
- 다른 영역 사건 노트: [distributed/36](../../distributed/36-distributed-incidents/2-summary.md)(GitHub 2018 분산 관점, Cloudflare 2017, AWS EBS 2011, metastable failure) · [database/57](../../database/57-db-incidents/2-summary.md)(GitLab 2017, Sentry 2015, GitHub 2018 DB 관점) · [os/38](../../os/38-os-incidents/2-summary.md) · [testing/21-test-incidents](../../testing/21-test-incidents/2-summary.md)(CrowdStrike 시험 관점)
- 후속(AI 엔지니어링): [ai-engineering/26-ai-incidents](../../ai-engineering/26-ai-incidents/2-summary.md) — LLM 운영 실사건(Anthropic 2025-09 사후 분석 등)
- 1차 출처
  - AWS, "Summary of the Amazon S3 Service Disruption in the Northern Virginia (US-EAST-1) Region"(2017) <https://aws.amazon.com/message/41926/>
  - Laura Nolan, "Slack's Outage on January 4th 2021", Slack Engineering <https://slack.engineering/slacks-outage-on-january-4th-2021/>
  - Daniel Sturman 외, "Roblox Return to Service 10/28-10/31 2021", 2022-01-20 <https://about.roblox.com/newsroom/2022/01/roblox-return-to-service-10-28-10-31-2021>
  - CrowdStrike, "Falcon Content Update Preliminary Post Incident Report"(2024-07-25 1900 UTC 갱신) <https://www.crowdstrike.com/en-us/blog/falcon-content-update-preliminary-post-incident-report/>
  - CrowdStrike, "External Technical Root Cause Analysis — Channel File 291"(2024-08-06) <https://www.crowdstrike.com/wp-content/uploads/2024/08/Channel-File-291-Incident-Root-Cause-Analysis-08.06.2024.pdf>
  - David Weston(Microsoft), "Helping our customers through the CrowdStrike outage", 2024-07-20 <https://blogs.microsoft.com/blog/2024/07/20/helping-our-customers-through-the-crowdstrike-outage/>
  - TechTarget(Dark Reading), "CrowdStrike: 97% of Windows sensors back online after outage", 2024-07-26 — CEO LinkedIn 게시(7-25) 인용 <https://www.techtarget.com/searchsecurity/news/366599094/CrowdStrike-97-of-Windows-sensors-back-online-after-outage>
- 실행 확인(실험 의무는 면제된 종합 편): eclipse-temurin:21-jdk(OpenJDK 21.0.12), `--cpus=2`, 일회용 컨테이너 `sn-rl-w52-gov` — `Governor.java`. 경과 시간 계산은 Python `datetime`으로 원문 시각 사이를 뺐다.
