# distributed/36-distributed-incidents — 실사건: GitHub 43초 분할(2018) · Cloudflare 윤초 RRDNS(2017) · AWS EBS 재미러링 폭풍(2011) · metastable failure — 정리 (힌트)

## 해결하는 문제

leaf 노트는 메커니즘을 **하나씩** 설명한다.\
부분 실패는 03번, 비동기 페일오버는 06번, 단조 시계는 04번, 재시도 증폭은 03번 장애 3이다.\
실제 장애에서는 메커니즘 여러 개가 **한 줄로 이어진다.** 짧은 방아쇠 하나가 긴 복구로 바뀐다.

```text
  leaf 노트:  [분할] [합의 선출] [비동기 복제] [PACELC] [단조 시계] [재시도] [용량] [제어 평면]  <- 각각 따로
  실사건:
    GitHub      43초 분할 -> 정족수가 서부로 승격 -> 양쪽에 서로 없는 쓰기 -> 24시간 11분 저하
    Cloudflare  윤초에 시간이 1초 뒤로 -> 음수 RTT -> 평활값 음수 -> rand.Int63n panic
    AWS EBS     잘못된 트래픽 전환 -> 대량 고립 -> 재미러링 폭풍 -> 용량 고갈·제어 평면 고갈 -> 며칠
    metastable  방아쇠는 사라졌는데 지속 효과(재시도 등)가 시스템을 나쁜 상태에 붙잡는다
```

쉬운 예: 고속도로 정체다.\
사고 차량은 10분 만에 치웠다. 그런데 정체는 두 시간 간다.\
사고(방아쇠)는 사라졌지만, 이미 쌓인 차량과 끼어들기(지속 효과)가 정체를 붙잡고 있다.

똑같은 구조다.\
GitHub의 네트워크 단절은 43초였고 서비스 저하는 24시간 11분이었다.\
AWS EBS의 네트워크 잘못은 곧 되돌렸지만, 그 뒤에 시작된 재미러링 폭풍이 며칠짜리 복구를 만들었다.

이 노트는 당사자가 쓴 1차 출처로 사건을 복원하고, 각 고리를 이 영역 leaf에 붙인다.
- **GitHub(2018-10-21)**: DB 관점(타임라인 전체, 백업 복원, binlog 대조)은 [database/57-db-incidents](../../database/57-db-incidents/2-summary.md) 사건 3이 정본이다. 여기서는 **분할·정족수·페일오버 정책·복제 지연·적체 처리**를 본다.
- **Cloudflare(2017-01-01)**: 윤초에 경과 시간이 음수가 되어 DNS 일부가 실패했다.
- **AWS EBS(2011-04-21~)**: 한 가용 영역의 EBS 노드들이 고립됐다 돌아오며 새 복제본을 동시에 찾아 클러스터 용량이 바닥났다.
- **metastable failure**: Bronson 외(HotOS 2021)가 이름 붙이고, Huang 외(OSDI 2022)가 공개 사고 보고서에서 사례를 모은 장애 유형이다. Huang 외는 AWS 2011 사건을 그 사례 중 하나(AWS1)로 분류했다.

  - *사후 분석(postmortem)*: 장애 뒤 당사자가 타임라인·원인·재발 방지를 정리한 글이다. 이 노트의 시각·수치는 원문에서만 가져왔다. 원문에 없는 연결은 "해석"이라고 적는다.

## 동작·원리

### 사건 1 — GitHub: 43초 분할과 리전을 넘는 승격 (2018-10-21)

출처: Jason Warner, "October 21 post-incident analysis", GitHub 블로그 2018-10-30.

#### 무엇이 어디에 있었나

```text
            미 동부 네트워크 허브 ──X── 미 동부 주 데이터센터            미 서부 데이터센터
               (22:52 UTC, 43초 단절)   [MySQL 주 서버들]               [MySQL 복제본들]
                                       [Orchestrator 노드]             [Orchestrator 노드]
                                                                      
                                       미 동부 퍼블릭 클라우드
                                       [Orchestrator 노드]

  단절 동안: 서부 + 동부 클라우드의 Orchestrator 노드들이 정족수를 이룸(Raft)
          → 클러스터들의 쓰기를 서부로 보내도록 페일오버, 서부 토폴로지 재구성
  연결 복구: 애플리케이션 계층이 곧바로 서부의 새 주 서버로 쓰기를 보냄
  남은 것: 동부 DB에 서부로 복제되지 않은 짧은 구간의 쓰기
          → 양쪽에 서로 없는 쓰기가 있어 동부로 안전하게 되돌릴 수 없음
```

- 원문: Orchestrator는 MySQL 토폴로지 관리·자동 페일오버 도구이고 "Raft 위에 만들어져" 합의를 한다. 원문은 이렇게도 적는다: Orchestrator는 애플리케이션이 감당하지 못하는 토폴로지를 만들 수 있으므로 설정을 애플리케이션 기대와 맞춰야 한다.
- 해석: 정족수 쪽은 자기 모델 안에서 "옳은" 결정을 했다. 동부 주 데이터센터의 노드가 소수 쪽에 갇혔고, 다수 쪽이 진행했다([11](../11-consensus-raft/2-summary.md) · [10 §1](../10-leader-election/2-summary.md)). 문제는 결정의 **대가**였다. 하나는 승격 직전 비동기 복제의 틈([06 §3](../06-replication-strategies/2-summary.md))이고, 다른 하나는 리전 간 왕복 지연([08 §4](../08-cap-and-pacelc/2-summary.md))이다.

#### 분산 관점의 타임라인 (UTC, 원문)

| 시각 | 사건 | 이어지는 leaf |
|---|---|---|
| 10-21 22:52 | 100G 광장비 교체 작업 중 동부 허브 ↔ 동부 주 DC 연결 끊김. 43초 만에 복구. 그 사이 Orchestrator 리더 재선출, 서부로 페일오버 | 분할·정족수 [10 §1](../10-leader-election/2-summary.md) · 오탐 페일오버 [03 §2](../03-partial-failure-and-timeouts/2-summary.md) |
| 22:54 | 내부 모니터링 경보 다수 | — |
| 23:02 | Orchestrator API 조회 결과 토폴로지에 서부 서버만 있음 | — |
| 23:13 | 서부는 애플리케이션 쓰기를 "거의 40분" 받은 상태, 동부엔 복제 안 된 몇 초의 쓰기. 같은 원문의 다음 문단은 "30+ minutes of data written"이라 적는다 | 양쪽 분기 [06 §3](../06-replication-strategies/2-summary.md) |
| (판단) | 서부 데이터를 지키려 "fail-forward"를 택함. 대가: 동부 앱이 대부분의 DB 호출에서 대륙 횡단 왕복 → 많은 사용자에게 사용 불가 | 평시 L vs C [08 §4](../08-cap-and-pacelc/2-summary.md) |
| 23:19 | 푸시 등 메타데이터를 쓰는 작업 중단: 웹훅 전달·Pages 빌드 일시 정지 | 적체 시작 [19 §4](../19-message-types-channels-and-endpoints/2-summary.md) |
| 10-22 06:51 | 일부 클러스터가 동부에서 백업 복원을 마치고 서부에서 복제 시작. 상태 페이지에 "2시간" 복구 예상 — 복제 원격 측정에서 **선형 보간**한 값 | — |
| 11:12 | 모든 주 서버가 다시 동부. 그러나 읽기 복제본 수십 대가 주 서버보다 몇 시간 뒤처짐 → 요청마다 다른(오래된) 데이터. 복제 따라잡기는 선형이 아니라 "power decay"를 따름. 유럽·미국 업무 시작으로 쓰기 부하 증가 | 오래된 읽기 [07 §3](../07-consistency-models/2-summary.md) · [06 §4](../06-replication-strategies/2-summary.md) |
| 13:15 | 피크 부하 접근, 복제 지연이 줄지 않고 늘어남. 동부 퍼블릭 클라우드에 미리 준비하던 읽기 복제본을 투입해 읽기를 분산 → 복제가 따라잡음 | — |
| 16:24 | 복제본 동기화 완료, 원래 토폴로지로 페일오버. 적체 처리를 위해 상태는 빨강 유지 | — |
| 16:45 | 대기 중: 웹훅 이벤트 5백만 건 이상, Pages 빌드 8만 건. 내부 TTL을 넘긴 웹훅 페이로드 약 20만 건이 버려짐 → 처리 일시 중지, TTL 상향 | 만료 [19 §4](../19-message-types-channels-and-endpoints/2-summary.md) · 적체 [18](../18-consumer-failure-handling/2-summary.md) |
| 23:03 | 대기 작업 모두 처리, 녹색. 총 24시간 11분 저하 | — |

- 원문의 원인 진술: Orchestrator는 "설정된 대로" 동작했다. 애플리케이션 계층은 이 토폴로지 변경을 감당하지 못했다. "리전 안의 리더 선출은 대체로 안전하지만, 갑작스러운 대륙 횡단 지연이 주요 원인 중 하나였다." 이런 규모의 내부 분할을 본 적이 없어 생긴 "창발적 동작"이었다.
- 원문의 후속 조치(분산 관련): 리전 경계를 넘는 주 서버 승격을 막도록 Orchestrator 설정 조정. 한 데이터센터 전체 장애를 견디는 active/active/active 설계 가속. 장애 주입·카오스 엔지니어링 도구 투자.
- 원문: 사용자 데이터 유실은 없었다. 동부에만 남은 쓰기는 binlog로 뽑았고, 가장 바쁜 클러스터 하나의 영향 구간 쓰기는 954건이었다(대조 절차는 [database/57](../../database/57-db-incidents/2-summary.md) 사건 3).

#### 분산 관점으로 다시 보기 (해석)

```text
  ① 분할(43초)         ② 정족수 결정          ③ 결정의 대가                      ④ 복구의 꼬리
  ─────────────        ─────────────          ──────────────────────────         ─────────────────────
  동부 DC 고립    →    서부+클라우드가 과반  →  비동기 복제 틈: 동부에만 몇 초 쓰기  →  백업 복원·복제 따라잡기
                      → 서부 승격               리전 간 왕복: 앱 쓰기가 느려짐          읽기 복제본 몇 시간 지연
                                                                                    적체 5백만+ · TTL로 20만 버림
```

- ①→② 해석: 43초는 사람에게 짧지만 자동 페일오버에는 충분히 길었다. 탐지 문턱만의 문제가 아니라 "승격이 **어디로** 일어나도 되나"의 문제였다. 원문도 탐지 시간이 짧았다고 하지 않고, 리전 간 승격을 막는 설정을 조치로 든다([03 §2](../03-partial-failure-and-timeouts/2-summary.md)과 같은 읽기).
- ②→③ 해석: 정족수 기반 선출은 리더가 둘이 되는 것을 막는다. 그러나 **비동기 복제의 미전송분**까지 지켜 주지는 않는다. 선출의 안전성([11](../11-consensus-raft/2-summary.md))과 데이터 복제의 내구성([06 §3](../06-replication-strategies/2-summary.md))은 다른 층이다.
- ③ 해석: 서부 주 서버로 일관성을 지키는 대신 동부 앱의 지연이 대륙 횡단 왕복이 됐다. 평시에도 L(지연)과 C(일관성) 사이의 선택이 있다는 PACELC의 E 쪽이 사고 중에 드러난 모양이다([08 §4](../08-cap-and-pacelc/2-summary.md)).
- ④ 해석
  - 읽기를 큰 복제본 풀에 퍼뜨린 구조라, 요청마다 지연이 다른 복제본에 닿아 "시간이 거꾸로 가는" 읽기(monotonic reads 위반)가 됐다([07 §3](../07-consistency-models/2-summary.md)).
  - 복제 따라잡기 속도 = 적용 속도 − 새 쓰기 속도다. 아침 부하로 새 쓰기가 늘자 따라잡기가 급감했다. 복제본을 늘려 복제본당 읽기 부하를 낮추자 따라잡았다(원문 13:15). 선형 보간 예측이 빗나간 이유다.
  - 적체를 다시 흘릴 때 내부 TTL이 정상 작업 약 20만 건을 버렸다. 만료는 "낡은 명령을 버리는" 장치인데([19 §4](../19-message-types-channels-and-endpoints/2-summary.md)), 복구 적체에서는 **유효한 작업**을 버리는 장치가 됐다. 복구 절차에 만료 정책을 함께 넣어야 한다.

### 사건 2 — Cloudflare: 윤초와 음수 RTT (2017-01-01)

출처: John Graham-Cumming, "How and why the leap second affected Cloudflare DNS", Cloudflare 블로그 2017-01-01.

#### 코드 경로

```text
  CNAME 조회 → RRDNS가 내부 리졸버 중 하나를 고름(가중 선택) → 질의 → RTT 측정
                                                                 │
     start := time.Now()   ... 질의 ...   rtt := time.Now().Sub(start)
                                                                 │
     윤초 순간 시간이 1초 뒤로 → 수 ms짜리 질의의 rtt가 음수
                                                                 │
     측정값을 여러 번 평활(smoothing) → 몇 번 뒤 평활값 자체가 음수
                                                                 │
     가중 선택이 업스트림 시간 값을 rand.Int63n()에 넣음 → 인자가 음수면 panic
     (Go recover로 잡힘) → 그 CNAME 해석 실패
```

- 원문의 근본 원인: "시간은 뒤로 갈 수 없다"는 믿음. 코드는 두 시각의 차이가 최악이어도 0이라고 가정했다.
- 원문: RRDNS는 Go로 썼고 `time.Now()`는 단조성을 보장하지 않는다. 당시 Go에는 단조 시간 소스가 없었다(Go issue 12914).
  - 이후 사실: Go 1.9가 "Transparent Monotonic Time support"를 넣었다. `time.Now()`가 단조 시계 값을 함께 담고, 두 `Time` 모두 그 값이 있으면 `t.Sub(u)`는 단조 값만 쓴다(Go 1.9 릴리스 노트, `src/time/time.go` 주석).
- Go `math/rand`의 `Int63n`은 인자가 0 이하이면 `panic("invalid argument to Int63n")`을 낸다(Go 소스 `src/math/rand/rand.go`).
- 실행 재현은 [04](../04-physical-clocks-and-ntp/2-summary.md)의 실험 A(Java로 같은 모양: 음수 bound → `IllegalArgumentException: bound must be positive`)에 있다.

#### 영향과 타임라인 (UTC, 원문)

| 시각 | 사건 |
|---|---|
| 2017-01-01 00:00 | 영향 시작 |
| 00:10 | 엔지니어에게 에스컬레이션 |
| 00:34 | 문제 확인 |
| 00:55 | 완화책을 카나리 노드 하나에 배포·확인 |
| 01:03 | 카나리 데이터센터에 배포·확인 |
| 01:23 | 가장 영향이 큰 데이터센터에 수정 배포 |
| 01:45 | 주요 데이터센터에 배포 중 |
| 01:48 | 전체에 배포 중 |
| 02:50 | 영향받은 데이터센터 대부분에 배포 완료 |
| 06:45 | 영향 종료 |

- 범위(원문): CNAME 레코드를 쓰는 고객만 영향. Cloudflare 102개 데이터센터의 적은 수의 머신. 정점에 Cloudflare DNS 질의의 약 0.2%, 전체 HTTP 요청의 1% 미만이 오류. 가장 영향이 큰 머신은 90분 안에 패치.
- 수정(원문): 시간이 뒤로 가면 업스트림 성능 기록을 잊고 다시 쌓게 했다. 음수 값이 서버 선택 코드로 새지 않게 했다. 이후 모든 RRDNS 서버를 재시작해 재발을 막았다.

#### 분산 관점으로 다시 보기 (해석)

- 벽시계 차이로 경과 시간을 잰 단 한 곳이, 평활(상태 누적)을 거쳐 **나중에, 다른 코드에서** 터졌다. 음수 값이 측정 순간이 아니라 몇 번 뒤의 평활값에서 나왔다는 점이 원인 추적을 어렵게 한다.
- 원문은 시간이 왜 1초 뒤로 갔는지(커널의 윤초 처리 방식 등)를 적지 않는다. 양의 윤초에서 벽시계가 1초를 되감는 일반 메커니즘과 smear 방식은 [04](../04-physical-clocks-and-ntp/2-summary.md) 「윤초」 절, 노드마다 윤초 처리가 다를 때의 문제는 [26 §5](../26-hybrid-clocks-and-truetime/2-summary.md)에 있다.
- 2012 윤초(Linux hrtimer)는 같은 "벽시계 되감기"가 다른 경로(시간 제한 대기)로 터진 사건이다 — [os/38-os-incidents](../../os/38-os-incidents/2-summary.md).
- 분산 시스템과의 연결: 이 버그는 **서버 선택**(어느 리졸버로 보낼까)의 가중치에 있었다. 지연 측정으로 상대를 고르는 로직(로드밸런싱·장애 탐지·φ accrual, [02](../02-system-and-failure-models/2-summary.md))은 모두 경과 시간 측정에 기대므로 같은 위험을 가진다.

### 사건 3 — AWS EBS: 재미러링 폭풍 (2011-04-21~24)

출처: Amazon, "Summary of the Amazon EC2 and Amazon RDS Service Disruption in the US East Region", 2011-04-29. 시각은 원문 그대로 **PDT**다.

#### EBS 구조 (원문)

```text
   EBS 클러스터(가용 영역 하나 안)                         EBS 제어 평면(리전 단위)
   ┌──────────────────────────────────────────┐          ┌────────────────────────────┐
   │ EBS 노드 ── 주 네트워크(고대역) ── EBS 노드 │◀────────▶│ 사용자 요청 조정, 복제본 중   │
   │    └──── 보조 네트워크(복제용, 저용량) ───┘ │          │ "쓰기 가능한 하나" 정하기     │
   │ 볼륨 데이터는 여러 노드에 복제               │          │ 리전 공용 스레드 풀           │
   └──────────────────────────────────────────┘          └────────────────────────────┘

   복제 상대와 연결을 잃은 노드 → 상대가 죽었다고 가정 → 새 노드를 찾아 데이터 복제(재미러링)
   재미러링 중 그 볼륨 접근은 막힘(새 주 복제본이 정해질 때까지) → EC2 쪽에선 볼륨이 "stuck"
```

- 원문: 각 EBS 노드는 사본 하나가 어긋나거나 사라지면 **공격적으로** 새 복제본을 만드는 P2P 빠른 장애 조치 전략을 쓴다. 정상 클러스터에서 새 복제본 자리 찾기는 밀리초 단위다.
- 원문: 재미러링 중에는 데이터 사본을 가진 모든 노드가, 다른 노드가 넘겨받았음을 확인할 때까지 데이터를 붙든다. 새 주(쓰기 가능) 복제본을 정하는 협상에는 EC2 인스턴스·EBS 노드·EBS 제어 평면(권한자 역할)이 참여하고, 사본 하나만 주 복제본으로 지정된다. 원문은 새 주 복제본이 정해질 때까지 볼륨 접근을 막는 것이 "모든 장애 모드에서" EBS 볼륨 일관성을 위해 필요하다고 쓴다.

#### 타임라인 (PDT, 원문)

| 시각 | 사건 | 이어지는 leaf |
|---|---|---|
| 04-21 12:47 AM | 한 가용 영역의 주 네트워크 용량 업그레이드 작업. 트래픽을 다른 주 라우터로 옮겨야 했는데 **저용량 보조(복제) 네트워크**로 잘못 보냄 → 일부 노드는 주·보조 네트워크를 동시에 잃고 서로 완전히 고립 | 분할 [01](../01-why-distributed-and-fallacies/2-summary.md) · [02](../02-system-and-failure-models/2-summary.md) |
| (직후) | 잘못된 전환을 되돌려 연결 복구 → 대량의 노드가 동시에 재미러링 공간을 찾음 → 클러스터 여유 용량 고갈 → 노드들이 공간을 찾는 루프에 갇힘("re-mirroring storm"). 그 영역 볼륨의 약 13%가 stuck | 느림·고립을 죽음으로 [02 §1](../02-system-and-failure-models/2-summary.md) · 오탐 페일오버 [03 §2](../03-partial-failure-and-timeouts/2-summary.md) |
| (직후) | 고갈된 클러스터가 "create volume" API를 처리 못 함. 제어 평면의 긴 타임아웃 때문에 느린 호출이 쌓여 **리전 공용 스레드 풀**이 고갈 → 다른 가용 영역의 API까지 실패 | 타임아웃·스레드 고갈 [01 §1](../01-why-distributed-and-fallacies/2-summary.md) · [03 §4](../03-partial-failure-and-timeouts/2-summary.md) |
| 2:40 AM | 해당 영역의 새 Create Volume 요청을 모두 끔 | 부하 차단 |
| 2:50 AM | 다른 EBS API의 지연·오류율 회복 | — |
| (초기) | 악화 요인 둘: ① 공간을 못 찾은 노드가 충분히 공격적으로 **물러서지(back off) 않고** 반복 탐색 ② 복제 요청을 대량으로 동시에 닫을 때 낮은 확률로 노드가 죽는 경쟁 조건 — 폭풍 중 연결 시도가 극도로 많아 자주 터짐 → 더 많은 볼륨이 재미러링 필요 | 재시도 증폭 [03 §3](../03-partial-failure-and-timeouts/2-summary.md) |
| 5:30 AM | 리전 전체 EBS API 오류·지연 다시 증가: 주 복제본 협상이 늘어 제어 평면 brown-out | — |
| 8:20 AM | 고장 난 클러스터와 제어 평면 사이 통신을 끊기 시작 → 다른 영역 정상화(그 영역 API는 전부 불가) | 격리(벌크헤드) |
| 11:30 AM | 노드끼리의 헛된 공간 찾기 통신만 막는 변경 → 클러스터 악화 멈춤. 이 변경 전까지 경쟁 조건으로 추가 5%가 stuck, 한편 일부는 풀려 순 stuck은 13% | — |
| 12:04 PM | 장애가 한 가용 영역으로 갇힘. 약 13% stuck 유지 | — |
| 04-22 약 2:00 AM | 대량의 새 용량 투입 시작(다른 곳 서버를 물리적으로 옮겨 설치) | — |
| 04-22 12:30 PM | 해당 영역 볼륨 중 약 2.2%를 빼고 복원 | — |
| 04-23 11:30 AM 직후 | 전용 제어 평면 + 더 세밀한 스로틀로 적체 처리 시작 | — |
| 04-23 3:35 PM | 해당 영역의 제어 평면 접근 활성화 완료 | — |
| 04-23 6:15 PM | 해당 영역 EBS API 접근 복구 | — |
| 04-24 12:30 PM | 스냅숏으로 복원 가능한 것까지 마쳐, 영향 볼륨 중 1.04%를 빼고 복구 | — |
| (최종) | 해당 영역 볼륨의 0.07%는 일관된 상태로 복원하지 못함 | — |

- 원문: 실패한 노드는 그 노드의 모든 복제본 재미러링이 끝날 때까지 재사용하지 않는다. 데이터 복구 여지를 남기려는 의도적 결정이다. 그래서 새 용량을 따로 들여와야 했다.
- 원문(RDS): 단일 AZ 인스턴스는 정점에 해당 영역의 45%가 stuck I/O. 다중 AZ 인스턴스 중 2.5%는 자동 페일오버하지 못했다. 주 복제본과 보조 복제본을 갈라 놓은 네트워크 단절과 주 복제본의 stuck I/O가 빠르게 이어져 이전에 없던 버그가 드러났고, 그 버그는 주 복제본을 "데이터 유실 위험 없이 자동 페일오버하기에 안전하지 않은" 고립 상태로 남겼다.
- 원문의 재발 방지(분산 관련): 큰 복구 사건에 필요한 여유 용량을 확보. 큰 중단 때 재시도 로직이 **더 공격적으로 물러서고**, 새 노드를 헛되이 찾기보다 **이전 복제본과의 연결 회복**에 집중하도록 변경. 경쟁 조건 수정. 제어 평면을 가용 영역 사이에서 더 격리.

#### 분산 관점으로 다시 보기 (해석)

```text
  방아쇠              증폭기(되먹임)                                       마지막 방어선이 넘친 이유
  ────────────        ──────────────────────────────────────────           ──────────────────────────
  잘못된 트래픽   →   고립된 노드들: "상대 죽음" 가정 → 동시에 재미러링    →  여유 용량이 동시 대량 복구를
  전환(곧 되돌림)       공간 없음 → 물러서지 않고 반복 탐색 ─┐                  가정하지 않음
                      연결 폭증 → 경쟁 조건 crash ──────────┤               제어 평면 스레드 풀이 리전 공용
                      → 재미러링 필요 볼륨 증가 ◀────────────┘               + 긴 타임아웃
```

- 느림·고립과 죽음을 구분하지 못한다([02 §1](../02-system-and-failure-models/2-summary.md)). 각 노드는 국소적으로 옳게("상대가 죽었으니 새 사본을 만든다") 행동했다. 그러나 **모두가 동시에** 그렇게 하자 공유 자원(여유 공간)이 고갈됐다. 원문의 조치 "이전 복제본과의 연결 회복에 집중"은 "죽었다고 단정하지 말고 돌아오는지 먼저 보라"는 뜻으로 읽힌다.
- 물러서지 않는 재시도([03 §3](../03-partial-failure-and-timeouts/2-summary.md) · [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md)). 공간이 없을 때의 반복 탐색이 부하를 키웠다.
- 긴 타임아웃 + 공용 스레드 풀([01 §1](../01-why-distributed-and-fallacies/2-summary.md) · [ops-patterns/03-bulkhead](../../ops-patterns/03-bulkhead/2-summary.md)). 한 영역의 느린 호출이 리전 공용 풀을 채워 다른 영역까지 번졌다. 조치(호출 차단, 전용 제어 평면)는 벌크헤드를 사후에 세운 모양이다.
- 일관성 우선([08](../08-cap-and-pacelc/2-summary.md)). 새 주 복제본이 정해질 때까지 볼륨 접근을 막았다. 사본 하나만 쓰기 가능하게 하는 협상은 리더 선출·펜싱과 같은 역할이다([10](../10-leader-election/2-summary.md) · [12](../12-coordination-and-fencing/2-summary.md)). 그 대가가 stuck 볼륨(가용성 저하)이었다.
- RDS 다중 AZ 2.5%: 분할 직후 주 복제본이 고립되자 자동 페일오버가 "유실 위험" 판단으로 멈췄다. 리더 둘([10 §1](../10-leader-election/2-summary.md))과 비동기 유실([06 §3](../06-replication-strategies/2-summary.md))을 피하려는 쪽을 택한 결과로 읽을 수 있다.
- metastable 관점: Huang 외(OSDI 2022) 표 1은 이 사건을 AWS1(2011-04-21, 66.7시간, 방아쇠: 네트워크 설정 변경, 지속 효과: 재시도, 완화: 부하 차단·용량 증설)로 분류했다. 방아쇠(잘못된 전환)를 되돌린 뒤에도 재미러링 재시도가 나쁜 상태를 유지했다는 점이 그 정의에 맞는다.

### metastable failure — 방아쇠가 사라져도 남는 장애

출처: Bronson·Aghayev·Charapko·Zhu, "Metastable Failures in Distributed Systems", HotOS '21. Huang 외, "Metastable Failures in the Wild", OSDI '22.

#### 세 상태 (Bronson 외 그림 1)

```text
                 부하 증가(문턱은 보이지 않음)
     ┌────────┐ ─────────────────────────────▶ ┌──────────┐
     │ 안정    │                                │ 취약      │   취약 상태도 건강하다.
     │ stable │                                │vulnerable│   몇 달·몇 년 이 상태로 돌기도 한다
     └────────┘                                └──────────┘
          ▲                                        │ 방아쇠(trigger)
          │ 복구 = 강한 교정(재부팅·부하 대폭 감소)   ▼
          │                                   ┌──────────────┐
          └────────────────────────────────── │ metastable    │ ◀─┐ 지속 효과
                                              │ (goodput 바닥) │ ──┘ (되먹임)
                                              └──────────────┘
```

- *metastable failure*: 제어되지 않은 부하원이 있는 열린 시스템에서, 방아쇠가 나쁜 상태를 만들고 **방아쇠를 없애도** 그 상태가 남는 장애다. goodput(쓸모 있는 일의 처리량)이 바닥이고, 지속 효과(sustaining effect)가 상태를 붙잡는다(Bronson 외 1절).
  - *goodput*: 처리량 중 실제로 쓸모 있는 몫. 시간 초과로 버려질 응답은 처리해도 goodput이 아니다.
  - *지속 효과*: 대개 일의 증폭(work amplification)이나 효율 저하. 재시도, 캐시 비움, 느린 오류 처리 경로 등.
- 방아쇠가 사라지면 낫는 장애(DoS 공격, limplock, livelock)는 metastable이 아니라고 Bronson 외는 구분한다.
- Bronson 외의 근본 원인 관점: 근본 원인은 방아쇠가 아니라 **지속되는 되먹임 고리**다. 같은 상태로 가는 방아쇠는 많기 때문이다.
- 역설: 지속 효과는 평시의 효율·신뢰성을 높이는 기능(재시도, 캐시, 장애 조치)에서 나오는 경우가 많다.

#### 재시도 예 (Bronson 외 2.1절의 수치)

- DB는 300 QPS 미만이면 100 ms 안에 답하고, 그보다 많으면 지연이 10배 수준으로 나빠진다.
- 웹 앱은 요청마다 DB 질의 1회, 1초 안에 답이 없으면 재시도 1회.
- 280 QPS로 정상 운영 중 10초 네트워크 단절 → 복구 순간 단절 중 보낸 요청·재시도가 한꺼번에 재전송 → DB 과부하 → 지연이 높은 동안 재시도 때문에 560 QPS가 계속 들어옴 → goodput 0.
- 150 QPS 아래면 안정 상태다(재시도로 두 배가 돼도 300 아래). 그 위는 취약 상태다. 회복하려면 부하를 150 QPS 아래로 줄이거나 재시도를 20 QPS 미만으로 제한해야 한다.

#### Huang 외가 넓힌 것 (OSDI 2022)

- 공개 사고 보고서 수백 건을 훑어 metastable 장애를 모았다. 초록은 "11개 조직의 22건"이라 쓰고, 2절은 공개 보고서에서 21건(표 1)을 찾았다고 쓴다. 4절은 Twitter 내부 사례(GC가 증폭기)다.
  - 해석: 21(표 1) + 1(Twitter 내부) = 22로 읽힌다.
- "지난 10년 AWS의 주요 장애 15건 중 최소 4건"이 metastable 장애였다(초록).
- 표 1 요약(원문 수치)
  - 장애 시간은 1.5~73.53시간, 보고된 것 중 4~10시간이 가장 흔했다(35%).
  - 방아쇠: 약 45%가 엔지니어 실수(잘못된 설정·코드 배포)와 잠복 버그, 약 35%가 부하 급증. 45%는 방아쇠가 둘 이상.
  - 지속 효과: 재시도가 50% 넘는 사건에 관여해 가장 흔했다.
  - 완화: 직접 부하 차단(throttling, 요청 버리기 등)이 55% 넘는 사건에 쓰였다.
- 모델 확장
  - 방아쇠 두 종류: **부하 급증형**(organic load가 늘어남)과 **용량 감소형**(랙 장애·비효율 코드 배포 등으로 용량이 줄어듦).
  - 증폭 두 종류: **작업 부하 증폭**(재시도 등으로 부하가 늘어남)과 **용량 저하 증폭**(GC 같은 배경 작업이 방아쇠 뒤에도 용량을 깎음).
  - 취약 상태는 예·아니오가 아니다. 취약도·방아쇠 크기·지속 시간이 함께 갇힐지를 정한다.

#### Bronson 외가 정리한 대응

| 대응 | 내용 | 이어지는 leaf·노트 |
|---|---|---|
| 방아쇠가 아니라 고리를 고친다 | 같은 상태로 가는 방아쇠는 많다 | — |
| 과부하 때 정책 바꾸기 | 장애 조치·재시도 끄기, 재시도 예산, LIFO, 내부 큐 줄이기, 우선순위, 부하 차단, 서킷 브레이커 | [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md) · [ops-patterns/02-circuit-breaker](../../ops-patterns/02-circuit-breaker/2-summary.md) · [ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md) |
| 지속 과부하와 순간 급증 가르기 | 슬라이딩 윈도 안 **최소** 대기 지연(CoDel처럼)이 크면 지속 과부하 | — |
| 우선순위 | 재시도 질의를 낮은 우선순위로. look-aside 캐시는 "캐시 채우기 우선"을 강제하기 어렵고, read-through 캐시는 쉽다 | [32](../32-distributed-cache-consistency/2-summary.md) |
| 빠른 오류 경로 | 실패 기록은 크기 제한 큐로 넘기고 넘치면 카운터만, 스택 트레이스는 표본만 | — |
| 특성 지표(characteristic metric) | 방아쇠에 튀고 장애가 끝나야 돌아오는 지표(대기 지연, 요청 지연, 타임아웃률, 캐시 적중률 …)로 경보 | — |
| 숨은 용량 | 광고 용량과 별개로 "스스로 회복하는 한계". look-aside 캐시 예: 광고 3,000 QPS, 숨은 용량 300 QPS | [32 §4](../32-distributed-cache-consistency/2-summary.md) |

### 실험: 재시도 예를 단순 유체 모델로 돌려 보기

논문 수치를 가정으로 삼아, 이 노트가 만든 단순 모델로 "방아쇠가 끝나도 회복하지 않는" 모양을 확인했다. **논문의 코드나 측정이 아니다.**

```js
// DB: 초당 300건 FIFO 처리, 대기열 상한 없음, 클라이언트가 포기한 요청도 처리(헛일)
// 클라이언트: 시도 후 1초 안에 응답이 없으면 1회 재시도. 재시도도 1초 넘으면 실패
// 트리거: t=10~20초 네트워크 단절. 그 사이 보낸 시도는 복구 순간 한꺼번에 도착(재전송)
const DT = 0.1, CAP = 300, TIMEOUT = 1.0;
function run(load, retries, outage = [10, 20], T = 400) {
  const q = [], pendingFirst = [], held = [];
  const good = new Array(Math.ceil(T / 20)).fill(0), sentPerBin = new Array(Math.ceil(T / 20)).fill(0);
  for (let step = 0; step < Math.round(T / DT); step++) {
    const t = +(step * DT).toFixed(1);
    const down = t >= outage[0] && t < outage[1];
    const send = (b) => { sentPerBin[Math.floor(t / 20)] += b.n; (down ? held : q).push(b); };
    const b = { sent: t, n: load * DT, retry: false, done: 0 };
    send(b); pendingFirst.push(b);
    if (!down && held.length) { q.push(...held.splice(0)); }              // 단절 끝: 보관분 도착
    while (pendingFirst.length && t - pendingFirst[0].sent >= TIMEOUT - 1e-9) {
      const f = pendingFirst.shift(), left = f.n - f.done;               // 1초 지난 첫 시도의 미완료분
      if (retries && left > 1e-9) send({ sent: t, n: left, retry: true, done: 0 });
    }
    let budget = CAP * DT;                                               // DB 처리
    while (budget > 1e-9 && q.length) {
      const h = q[0], take = Math.min(budget, h.n - h.done);
      h.done += take; budget -= take;
      if (t - h.sent <= TIMEOUT + 1e-9) good[Math.floor(t / 20)] += take; // 1초 안 응답만 goodput
      if (h.n - h.done <= 1e-9) q.shift();
    }
  }
  return { good: good.map(x => Math.round(x / 20)), sent: sentPerBin.map(x => Math.round(x / 20)) };
}
```

(실험, Node.js 18.19.1, 2026-10-01 — 결정적 모델이라 실행마다 같다. 열 하나 = 20초 구간의 초당 평균, 첫 구간 0~20초에 단절 10~20초가 들어 있다)

```text
load=140 retries=on   goodput/s per 20s: 70 1 0 0 0 0 36 143 140 140 140 140 140 140 140 140 140 140 140 140
                          attempts/s per 20s: 203 279 280 280 280 280 271 140 140 140 140 140 140 140 140 140 140 140 140 140
load=280 retries=on   goodput/s per 20s: 140 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
                          attempts/s per 20s: 406 559 560 560 560 560 560 560 560 560 560 560 560 560 560 560 560 560 560 560
load=280 retries=off  goodput/s per 20s: 140 1 0 0 0 0 0 221 280 280 280 280 280 280 280 280 280 280 280 280
                          attempts/s per 20s: 280 280 280 280 280 280 280 280 280 280 280 280 280 280 280 280 280 280 280 280
```

- 관찰
  - 280 QPS + 재시도: 단절(10초)이 끝난 뒤 400초까지 goodput이 0 근처다(20~40초 구간 평균 1, 그 뒤 0). 시도는 초당 560으로, 논문 2.1절의 "560 QPS"와 같다. 560 > 300이라 대기열이 줄지 않는다.
  - 140 QPS + 재시도: 단절 직후엔 똑같이 goodput 0이지만, 시도가 280 < 300이라 대기열이 초당 약 20건씩 줄어 120~140초 구간부터 회복한다.
  - 280 QPS + 재시도 끔: 같은 부하·같은 방아쇠인데 140~160초 구간부터 회복한다. 지속 효과(재시도)를 없애면 빠져나온다.
- 해석
  - 같은 방아쇠(10초 단절)에 대해 부하가 안정 구간(< 150)이면 저절로 회복하고, 취약 구간이면 갇힌다. Bronson 외의 "취약 상태는 건강해 보이지만 방아쇠 하나로 갇힌다"의 모양이다.
  - 이 모델은 DB가 포기된 요청까지 처리한다고 두었다(헛일). DB가 기한 지난 요청을 버리면([03 §4](../03-partial-failure-and-timeouts/2-summary.md)의 데드라인 전파) 모양이 달라진다. 실제 시스템의 회복 시간은 이 숫자와 다르다.

## 쓰이는 자료구조·알고리즘

- **Raft 정족수 선출** — GitHub의 Orchestrator. 정족수는 리더 둘을 막지만 복제 미전송분과 리전 간 지연까지 판단하지는 않는다([11](../11-consensus-raft/2-summary.md) · [10](../10-leader-election/2-summary.md)).
- **비동기 복제 로그(binlog)** — 미전송분이 양쪽 분기를 만들고, 같은 로그가 대조의 재료가 된다([06](../06-replication-strategies/2-summary.md) · [database/57](../../database/57-db-incidents/2-summary.md)).
- **평활(smoothing)된 측정값 + 가중 무작위 선택** — Cloudflare RRDNS. 원문은 평활 방식(이동 평균의 종류)을 밝히지 않는다. 음수 측정이 상태에 누적되어 나중에 선택 함수로 새는 경로가 핵심이다. 경과 시간 측정은 **단조 시계**([04](../04-physical-clocks-and-ntp/2-summary.md)).
- **복제본 배치 탐색(재미러링)** — EBS 노드가 여유 공간 있는 노드를 찾아 새 사본을 만든다. 이것이 동시에, 물러섬 없이 일어난 것이 폭풍이다. 체인·정족수 복제본 교체와 같은 계열([27](../27-chain-replication-and-striping/2-summary.md)).
- **유한 스레드 풀 + 타임아웃** — EBS 제어 평면. 긴 타임아웃은 스레드 점유 시간을 늘려 풀 고갈을 앞당긴다([01](../01-why-distributed-and-fallacies/2-summary.md)).
- **되먹임 고리 모델(부하 L, 용량 C, 증폭 α)** — Huang 외 3절. 부하와 용량을 같은 단위(초당 자원 단위)로 재고, 과부하가 아닌 조건을 `L_sys(t) < C_sys(t)`로 둔다. 증폭은 방아쇠 뒤에도 `L_sys`를 키우거나 `C_sys`를 깎는다. 위 실험의 유체 모델은 그 가장 단순한 판이다(해석).
- **지수 백오프·재시도 예산** — 재시도를 시간에 흩고 비율에 상한을 둔다([03](../03-partial-failure-and-timeouts/2-summary.md) · [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md)).

```text
  네 사건을 같은 틀로: 방아쇠 -> 증폭기(지속 효과) -> 마지막 방어선 -> 그것도 넘친 이유

  GitHub      43초 분할       -> 리전 간 자동 승격·비동기 틈 -> fail-forward + 백업 복원 -> 복제 따라잡기가 아침 부하에 밀림
  Cloudflare  윤초(-1초)      -> 평활값에 음수 누적          -> Go recover로 panic 격리   -> CNAME 해석은 실패
  AWS EBS     잘못된 전환     -> 동시 재미러링·무백오프 재시도 -> 클러스터 여유 용량        -> 동시 대량 복구를 가정 안 함
  metastable  일시 과부하     -> 재시도·캐시 비움 등 증폭     -> (없음)                   -> 숨은 용량 < 실제 부하
```

## 적용 — 풀어나가는 법

### 1. 사고 보고서를 분산 관점으로 읽는 순서

1. **방아쇠와 지속 시간의 비**를 본다. 43초 → 24시간 11분처럼 비가 크면, 방아쇠 뒤에 증폭기나 되돌릴 수 없는 결정이 있다.
2. **되돌릴 수 없는 자동 동작**을 찾는다. 페일오버·승격·재미러링·데이터 이동. 그것이 언제, 어떤 문턱으로, 어디까지 일어나게 되어 있었나.
3. **지속 효과**를 찾는다. 방아쇠를 없앤 뒤에도 무엇이 부하를 유지했나(재시도, 적체, 복제 따라잡기).
4. **공유 자원**을 찾는다. 여유 용량, 리전 공용 스레드 풀, 읽기 복제본 풀처럼 사고를 경계 밖으로 번지게 한 것.
5. 각 고리를 leaf에 붙이고(위 표들), 원문 수치와 해석을 나눠 적는다. 원문 안에서 수치가 어긋나면(GitHub의 "거의 40분"과 "30+ minutes") 둘 다 적는다.

### 2. 내 시스템으로 옮길 점검 목록

- **GitHub 형 — 자동 승격의 범위**
  - 승격 도구가 리전·데이터센터 경계를 넘을 수 있나? Orchestrator 문서에는 `PreventCrossDataCenterMasterFailover`·`PreventCrossRegionMasterFailover`(기본 `false`) 설정이 있다(openark/orchestrator `docs/configuration-recovery.md`). GitHub가 어떤 설정으로 바꿨는지는 보고서에 없다.
  - 승격 뒤 옛 주 서버의 미전송분을 뽑는 절차(binlog·WAL)가 있나([06 §3](../06-replication-strategies/2-summary.md)).
  - 읽기 복제본 지연을 요청 경로에서 거르나(최대 허용 지연 이상인 복제본 제외, [07 §3](../07-consistency-models/2-summary.md)).
  - 복구 때 적체를 다시 흘리면 만료·TTL이 정상 작업을 버리지 않나([19 §4](../19-message-types-channels-and-endpoints/2-summary.md)).
- **Cloudflare 형 — 경과 시간**
  - 경과 시간·지연 측정이 단조 시계를 쓰나. Java는 `System.nanoTime()`, Go 1.9 이상은 `time.Now()`끼리의 `Sub`.
  - 시간 차이를 받는 함수(난수 범위, 배열 크기, sleep)에 음수 방어가 있나.
- **AWS 형 — 동시 복구와 재시도**
  - "상대가 죽었다"고 판단한 뒤의 복구 동작이 **동시에 대량으로** 일어나면 감당되나. 복구 동작의 동시성 상한·속도 제한이 있나.
  - 복구 재시도에 지수 백오프·지터·예산이 있나.
  - 제어 평면 호출에 짧은 타임아웃과 영역별 격리(벌크헤드)가 있나.
- **metastable 형 — 숨은 용량**
  - 캐시가 다 비면 원천이 감당하나(숨은 용량). 캐시 적중률 개선으로 원천을 줄였다면 숨은 용량도 줄었다.
  - 특성 지표(대기 지연·타임아웃률)에 경보가 있나.

### 3. 코드 — 단조 시계와 물러서는 재시도 (Java 21)

```java
import java.util.concurrent.ThreadLocalRandom;

final class IncidentGuards {
    /** Cloudflare 형 방어: 경과 시간은 단조 시계로, 그래도 음수면 버린다 */
    static long elapsedMillis(long startNanos) {
        long d = System.nanoTime() - startNanos;        // nanoTime은 벽시계 조정의 영향을 받지 않는다
        return d < 0 ? 0 : d / 1_000_000;               // 방어선 하나 더: 음수가 상태로 새지 않게
    }

    /** AWS·metastable 형 방어: 지수 백오프 + 전체 지터 + 재시도 예산 */
    static final class RetryBudget {
        private final double ratio;          // 첫 시도 대비 허용 재시도 비율(예: 0.1)
        private double attempts, retries;
        RetryBudget(double ratio) { this.ratio = ratio; }
        synchronized void onFirstAttempt() { attempts++; }
        synchronized boolean tryAcquireRetry() {
            if (retries + 1 > attempts * ratio) return false;   // 예산 초과면 재시도하지 않는다
            retries++; return true;
        }
    }

    static long backoffMillis(int retry, long baseMs, long capMs) {
        long exp = Math.min(capMs, baseMs << Math.min(retry, 20));
        return ThreadLocalRandom.current().nextLong(exp + 1);   // 0..exp 균등(전체 지터)
    }
}
```

- 재시도 예산은 Bronson 외가 과부하 때 정책으로 든 것 중 하나다(retry budget). 예산의 비율(예시 0.1)은 시스템마다 측정으로 정한다. 실제 구현은 시간 창으로 세어야 오래된 시도가 예산을 부풀리지 않는다(예시 코드는 누적).

## 장애 시나리오와 대처

### 1. 짧은 분할에 리전을 넘는 자동 승격 (GitHub 형)

- **현상**: 1분도 안 되는 네트워크 단절 뒤, 쓰기 주 서버가 다른 리전에 가 있다. 앱이 느리고, 옛 주 서버에는 새 주 서버에 없는 쓰기가 있다.
- **보이는 형태**: 승격 도구 API의 토폴로지에 다른 리전 서버만 있음. DB 호출 지연 = 리전 간 왕복. 양쪽 binlog·GTID 집합이 서로를 포함하지 않음.
- **원인**: 정족수 선출은 설계대로 동작했지만, 승격 범위가 앱이 감당하는 토폴로지를 넘었다. 비동기 복제의 미전송분이 남았다.
- **대처**: 승격 범위를 리전 안으로 제한한다. 옛 주 서버는 펜싱한다([12](../12-coordination-and-fencing/2-summary.md)). 미전송분은 로그로 뽑아 대조한다. 복구 방향(되돌리기 vs fail-forward)과 그 대가를 미리 정해 둔다([08 §4](../08-cap-and-pacelc/2-summary.md)).

### 2. 벽시계 되감기로 경과 시간이 음수 (Cloudflare 형)

- **현상**: 윤초·NTP step 순간부터 일부 요청이 실패한다. 측정 직후가 아니라 조금 뒤에 터진다.
- **보이는 형태**: Go `panic: invalid argument to Int63n`, Java `IllegalArgumentException: bound must be positive` 같은 "범위가 음수" 예외. 시각이 윤초(UTC 자정)·시간 동기 이벤트와 겹친다.
- **원인**: 벽시계 차이로 경과 시간을 쟀고, 음수가 평활값 같은 상태에 누적됐다.
- **대처**: 경과 시간은 단조 시계로 잰다. 시간 차이를 받는 곳에 음수 방어. 누적 상태는 시간이 뒤로 가면 버리고 다시 쌓는다(Cloudflare의 수정). 상세는 [04 §1](../04-physical-clocks-and-ntp/2-summary.md).

### 3. 동시 복구가 공유 용량을 고갈시킨다 (AWS 형)

- **현상**: 네트워크 문제를 되돌렸는데 저장 계층이 오히려 더 나빠진다. 다른 영역의 API까지 실패한다.
- **보이는 형태**: 복구(재미러링·재복제) 요청 급증, 클러스터 여유 용량 0, 제어 평면 스레드 풀 포화와 지연 증가.
- **원인**: 많은 노드가 동시에 "상대가 죽었다"고 판단하고 새 복제본을 찾았다. 공간이 없는데도 물러서지 않았다. 긴 타임아웃이 공용 스레드를 묶었다.
- **대처**: 복구 동작의 동시성 상한·속도 제한, 지수 백오프, "이전 복제본과의 재연결 먼저". 여유 용량을 대량 복구 기준으로 잡는다. 제어 평면을 영역별로 격리하고 타임아웃을 짧게 둔다.

### 4. 방아쇠를 근본 원인으로 적고 닫는다 (metastable 형)

- **현상**: "네트워크 단절이 원인, 네트워크 팀 조치 완료"로 사후 분석을 닫았다. 몇 달 뒤 다른 방아쇠(배포·캐시 재시작)로 같은 모양의 장애가 난다.
- **보이는 형태**: 방아쇠를 없앤 뒤에도 타임아웃률·대기 지연이 높게 유지됐다. 부하를 크게 줄이거나 재시작해야 풀렸다.
- **원인**: 근본 원인은 방아쇠가 아니라 지속 효과(재시도·캐시 비움 등)의 되먹임 고리다(Bronson 외 3절).
- **대처**: 사후 분석에 "방아쇠 제거 뒤에도 무엇이 상태를 유지했나"를 필수 질문으로 둔다. 재시도 예산·과부하 시 정책 변경·특성 지표 경보. 숨은 용량을 부하 시험(방아쇠 주입 후 스스로 회복하나)으로 잰다.

### 5. 복구 적체를 다시 흘리다 TTL이 정상 작업을 버린다 (GitHub 형)

- **현상**: 장애가 끝나고 밀린 웹훅·작업을 처리하는데, 일부가 처리되지 않고 사라진다.
- **보이는 형태**: 적체 처리 중 "TTL 초과로 버림" 건수가 급증(GitHub: 약 20만 건). 하위 파트너에게 알림 폭주 위험.
- **원인**: 만료(TTL)는 평시의 "낡은 메시지 버리기"용으로 정했는데, 복구 적체의 대기 시간이 그것을 넘었다.
- **대처**: 복구 런북에 만료 정책을 넣는다(적체 처리 중 상향 또는 업무 기준 만료로 전환). 버린 건수를 지표로 내고 처리를 멈출 수 있게 한다(GitHub는 발견 즉시 처리를 멈추고 TTL을 올렸다). 하위로의 속도는 조절한다([19 §4](../19-message-types-channels-and-endpoints/2-summary.md)).

## 핵심 문장

- 실사건은 짧은 방아쇠가 증폭기나 되돌릴 수 없는 자동 동작을 만나 긴 복구로 바뀐 것이다. GitHub는 43초 분할이 24시간 11분 저하가 됐다.
- 정족수 선출은 리더 둘을 막을 뿐, 비동기 복제의 미전송분과 리전 간 지연까지 판단하지 않는다. 자동 승격의 범위는 앱이 감당하는 토폴로지와 맞아야 한다.
- Cloudflare: 벽시계 차이로 잰 경과 시간이 윤초에 음수가 됐고, 평활 상태를 거쳐 `rand.Int63n`에서 panic이 났다. 경과 시간은 단조 시계로 잰다.
- AWS EBS: 고립됐다 돌아온 노드들이 동시에, 물러섬 없이 재미러링을 시도해 여유 용량과 제어 평면 스레드를 고갈시켰다. 국소적으로 옳은 복구도 동시에 일어나면 공유 자원을 무너뜨린다.
- metastable 장애에서 근본 원인은 방아쇠가 아니라 지속 효과(재시도 등)의 되먹임 고리다. 취약 상태는 평시에 건강해 보인다.

## 관련 주제·근거

- 선행: [35](../35-distributed-symptom-index/2-summary.md) — 증상 사전(이 사건들의 증상이 색인의 어디에 있나)
- 메커니즘 leaf
  - 분할·부분 실패·모델: [01](../01-why-distributed-and-fallacies/2-summary.md) · [02](../02-system-and-failure-models/2-summary.md) · [03](../03-partial-failure-and-timeouts/2-summary.md)
  - 시간: [04](../04-physical-clocks-and-ntp/2-summary.md) · [26](../26-hybrid-clocks-and-truetime/2-summary.md)
  - 복제·일관성: [06](../06-replication-strategies/2-summary.md) · [07](../07-consistency-models/2-summary.md) · [08](../08-cap-and-pacelc/2-summary.md) · [27](../27-chain-replication-and-striping/2-summary.md)
  - 합의·조정: [10](../10-leader-election/2-summary.md) · [11](../11-consensus-raft/2-summary.md) · [12](../12-coordination-and-fencing/2-summary.md)
  - 메시징·적체: [18](../18-consumer-failure-handling/2-summary.md) · [19](../19-message-types-channels-and-endpoints/2-summary.md)
  - 캐시(숨은 용량): [32](../32-distributed-cache-consistency/2-summary.md)
- 다른 영역
  - [database/57-db-incidents](../../database/57-db-incidents/2-summary.md) 사건 3 — GitHub 2018의 DB 관점(전체 타임라인·백업 복원·binlog 954건)
  - [os/38-os-incidents](../../os/38-os-incidents/2-summary.md) — 2012 윤초(Linux hrtimer)
  - [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md) · [ops-patterns/02-circuit-breaker](../../ops-patterns/02-circuit-breaker/2-summary.md) · [ops-patterns/03-bulkhead](../../ops-patterns/03-bulkhead/2-summary.md) · [ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md) · [ops-patterns/failure-at-scale](../../ops-patterns/failure-at-scale/2-summary.md)(양상 2 재시도 증폭)
- 1차 출처
  - Jason Warner(GitHub), "October 21 post-incident analysis", 2018-10-30 <https://github.blog/2018-10-30-oct21-post-incident-analysis/>
  - John Graham-Cumming(Cloudflare), "How and why the leap second affected Cloudflare DNS", 2017-01-01 <https://blog.cloudflare.com/how-and-why-the-leap-second-affected-cloudflare-dns/>
  - Amazon, "Summary of the Amazon EC2 and Amazon RDS Service Disruption in the US East Region", 2011-04-29 <https://aws.amazon.com/message/65648/>
  - Bronson, Aghayev, Charapko, Zhu, "Metastable Failures in Distributed Systems", HotOS '21 <https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf>
  - Huang, Magnusson, Muralikrishna, Estyak, Isaacs, Aghayev, Zhu, Charapko, "Metastable Failures in the Wild", OSDI '22 <https://www.usenix.org/system/files/osdi22-huang-lexiang.pdf>
- 보조 출처
  - Go 1.9 릴리스 노트 "Transparent Monotonic Time support" <https://go.dev/doc/go1.9> · Go `src/time/time.go`(go1.9) 주석 · `src/math/rand/rand.go`(`invalid argument to Int63n`)
  - openark/orchestrator `docs/configuration-recovery.md`(master) — `PreventCrossDataCenterMasterFailover`·`PreventCrossRegionMasterFailover`
- 실험 목록
  - `retry-meta.js` — Bronson 외 2.1절 재시도 예의 수치(DB 300 QPS, 1초 타임아웃 + 재시도 1회, 10초 단절)를 가정한 단순 유체 모델. 부하 140·280, 재시도 켬·끔 세 경우. Node.js 18.19.1, 결정적.
