# engineering-practice/20-practice-incidents — 실사건: Knight Capital(2012-08-01) · Cloudflare WAF 규칙 전역 배포(2019-07-02) — 배포 절차·플래그·설정 검증 관점 — 정리 (힌트)

## 해결하는 문제

leaf 노트는 실천 장치를 **하나씩** 설명한다.\
배포 자동화와 검증은 06번, 플래그 부채는 04번, 리뷰는 05번, 런북은 11번, 부채(죽은 코드)는 10번이다.\
실제 사고에서는 장치 여러 개가 **한꺼번에 빠져 있었다는 것**이 드러난다.\
그리고 "우리는 그 장치가 있다"고 믿던 곳에 예외 경로가 있었다는 것도 드러난다.

```text
  leaf 노트:  [배포 검증] [플래그 수명] [죽은 코드 삭제] [설정도 리뷰·테스트] [단계 배포] [런북·긴급 경로]  <- 각각 따로
  실사건:
    Knight 2012      죽은 코드 9년 방치 -> 옛 플래그를 새 기능에 재사용 -> 8대 중 1대 복사 누락(확인 절차 없음)
                     -> 그 1대에서 옛 코드가 깨어남 -> "되돌리기"로 7대도 옛 코드 -> 약 45분
    Cloudflare 2019  PR 승인·CI 초록·변경 요청서까지 정상 -> 그런데 규칙 배포 절차는 단계 배포 없이 전역
                     -> 수 초 만에 전 세계 -> 정규식 하나가 HTTP 처리 CPU를 소진 -> 27분
```

쉬운 예: 건물 소방 점검이다.\
Knight는 **점검표 자체가 없던** 건물이다. 비상구 하나가 잠긴 줄 아무도 몰랐다.\
Cloudflare는 **점검표를 다 채운** 건물이다. 그런데 점검표에 "가스 배관 공사는 점검 생략 가능"이라는 예외 칸이 있었고, 그날 공사가 가스 배관이었다.

똑같은 구조다.\
Knight에서 빠진 것은 배포가 끝난 뒤 "8대가 같은가"를 묻는 단계였다.\
Cloudflare에서는 소프트웨어 배포의 단계 배포(DOG → PIG → 카나리 → 전역)가 있었다. 하지만 WAF 규칙 변경은 "빠른 위협 대응"을 이유로 그 절차 밖에 있었다.

이 노트는 공개 1차 문서로 두 사건을 복원하고, **엔지니어링 실천**(배포 절차·플래그·설정의 리뷰와 테스트·단계 배포)의 빈틈만 본다.
- **Knight Capital(2012-08-01)**: 1차 출처는 미 SEC 행정 명령 Release No. 34-70694(2013-10-16)와 Knight의 2012-08-02 보도자료.
- **Cloudflare(2019-07-02)**: 1차 출처는 Cloudflare 블로그 사후 보고서 두 편(2019-07-02 당일 글, 2019-07-12 상세 글).
- 다른 관점은 다른 노트가 정본이다. 정규식 백트래킹 알고리즘은 algorithm/43 alg-incidents(미작성, [algorithm 영역 표](../../algorithm/curriculum.md))와 [algorithm/13-backtracking](../../algorithm/13-backtracking/2-summary.md). 운영 관점의 Knight는 [reliability/24-feature-flag-lifecycle](../../reliability/24-feature-flag-lifecycle/2-summary.md) 장애 1, [reliability/23-deployment-strategies](../../reliability/23-deployment-strategies/2-summary.md) 장애 3·롤백, [reliability/04-failure-modes-catalog](../../reliability/04-failure-modes-catalog/2-summary.md) F-17. 운영 사건 모음 [reliability/53-reliability-incidents](../../reliability/53-reliability-incidents/2-summary.md)는 두 사건을 다루지 않는다. 이 노트는 겹치는 사실을 짧게만 쓴다.

  - *사후 보고서(postmortem)·행정 명령*: Cloudflare 글은 당사자가 쓴 사후 보고서다. SEC 명령은 규제 당국이 회사의 합의 제안을 받아들여 낸 명령이고, 회사는 사실 인정·부인 없이 합의했다("without admitting or denying the findings"). 둘 다 1차 출처지만 쓴 목적이 다르다.
  - *사실과 해석*: 원문에 있는 사실은 출처·문단 번호와 함께 쓴다. 원문이 말하지 않는 연결은 "해석"이라고 표시한다.

## 동작·원리

### 사건 1 — Knight Capital: 재사용된 플래그와 복사가 빠진 서버 (2012-08-01)

출처
- SEC, Administrative Proceeding File No. 3-15570, Release No. 34-70694, "In the Matter of Knight Capital Americas LLC", 2013-10-16 <https://www.sec.gov/litigation/admin/2013/34-70694.pdf>. sec.gov는 연락처가 든 User-Agent 없는 요청을 거부한다(2026-10-05 요청에 HTTP 403). 그래서 Internet Archive 사본(2015-01-15 캡처, PDF 18쪽, 98,373바이트) <https://web.archive.org/web/20150115011139/http://www.sec.gov/litigation/admin/2013/34-70694.pdf>을 읽었다. 아래 `¶`는 명령의 문단 번호다.
- Knight Capital Group 보도자료, 2012-08-02(SEC EDGAR 8-K 첨부 99.1, Internet Archive 사본으로 확인) <https://web.archive.org/web/20150413204538/http://www.sec.gov/Archives/edgar/data/1060749/000119312512332176/d391111dex991.htm>.

#### 사실 — 타임라인 (원문)

| 시점 | 사건 | 출처 |
|---|---|---|
| 2003 | Power Peg 기능 사용 중단. 코드는 SMARS에 남음("remained present and callable") | ¶13·¶14 |
| 2005 | Power Peg 코드의 누적 수량(cumulative quantity) 확인 기능을 코드 앞쪽으로 옮김. 옮긴 뒤 Power Peg를 다시 시험하지 않음 | ¶14 |
| 2012-07-27부터 | NYSE RLP(Retail Liquidity Program, 8월 1일 시작) 대응 새 코드를 SMARS에 며칠에 걸쳐 단계적으로 배포. 기술자 한 명이 8대 중 1대에 새 코드를 복사하지 않음 | ¶12·¶15 |
| 08-01 08:01 ET께부터 | 내부 시스템이 "Power Peg disabled"를 담은 자동 메일("BNET rejects")을 보냄. 09:30 개장 전까지 97통. 경보로 설계된 메일이 아니었고 대개 읽지 않음 | ¶19 |
| 08-01, 약 45분 동안 | 개장 때 고위 직원이 33 계좌에 큰 포지션이 쌓이는 것을 봄(¶25). 부모 주문 212건으로 자식 주문 수백만 건. 154개 종목에서 400만 건 넘게 체결, 3억 9,700만 주 초과 | ¶1·¶17 |
| 같은 날 | 문제를 고치려고 정상 배포된 7대에서 새 RLP 코드를 **제거**. 7대에서도 Power Peg가 켜져 악화 | ¶27 |
| 결과 | 80개 종목 순매수 약 35억 달러, 74개 종목 순매도 약 31.5억 달러 포지션. 손실 4억 6천만 달러("over $460 million" ¶1, "realized a $460 million loss" ¶17) | ¶1·¶17 |
| 2012-08-02 | 회사 보도자료: 포지션을 모두 정리했고 "realized pre-tax loss of approximately $440 million" | 보도자료 |
| 2013-10-16 | SEC 명령. 열흘 안에 민사 제재금 1,200만 달러 납부 | 명령 표지·IV절 |

- 손실 수치가 둘이다. 4.4억 달러는 사건 다음 날 회사가 밝힌 **세전 실현 손실**이고, 4.6억 달러는 1년 뒤 SEC 명령의 수치다. 커리큘럼 요지의 "4.4억 달러"는 앞의 것이다. 어느 쪽을 쓰든 출처를 붙인다.
- 45분은 원문 표현 "over a 45-minute period"(¶1), "approximately 45 minutes"(¶17)다. 시작·정지 시각을 분 단위로 적은 문단은 명령에 없다. 212건은 개장 전에 받아 개장 경매에 참여시키려던 주문이었다(¶21).

#### 무엇이 어디에 있었나

```text
   부모 주문(RLP 플래그 = "yes")
          │  라운드 로빈 등으로 8대에 나뉨 (배정 방식은 원문에 없음)
          ▼
   ┌────┬────┬────┬────┬────┬────┬────┬────┐
   │ 1  │ 2  │ 3  │ 4  │ 5  │ 6  │ 7  │ 8  │   SMARS 서버
   │RLP │RLP │RLP │RLP │RLP │RLP │RLP │옛  │   1~7: 새 코드(플래그 = RLP)
   └────┴────┴────┴────┴────┴────┴────┴─┬──┘   8: 복사 누락 → 같은 플래그 = Power Peg
                                         │
                                         ▼
                 Power Peg: 자식 주문을 내다가 "다 체결됐으면 멈춤"이 있어야 하는데
                 그 확인은 2005년에 다른 곳으로 옮겨져 있었다 → 멈추지 않음(¶14·¶16)

   "되돌리기"(¶27): 1~7에서 새 코드를 제거 → 1~7도 옛 코드 + 같은 플래그 → 8대 모두 Power Peg
```

#### 실천 관점의 고리 — SEC 원문과 leaf

| 고리 | SEC 원문 | 빠진 실천 장치 | leaf |
|---|---|---|---|
| 죽은 코드 9년 | 2003년 이후 안 쓰는 Power Peg가 "present and callable"(¶13). 2003년에 서버에 남기기로 함(¶41) | 다 쓴 기능·플래그는 분기 코드부터 지운다 | [10](../10-technical-debt/2-summary.md) · [04-4](../04-branching-strategies/2-summary.md) · [software-design/54](../../software-design/54-designing-for-deletion/2-summary.md) |
| 옛 코드를 건드리고 재시험 안 함 | 2005년 이동 뒤 Power Peg를 재시험하지 않음(¶14). 쓰지 않는 코드 접근 뒤 시험을 요구하는 서면 규칙 없음(¶26) | 영향받는 경로의 회귀 테스트, 아니면 그 경로 삭제 | [14](../14-quality-standards/2-summary.md) · [testing/01](../../testing/01-why-test-and-pyramid/2-summary.md) |
| 플래그 재사용 | 새 RLP 코드가 Power Peg를 켜던 플래그를 "repurposed"(¶13) | 플래그 이름 재사용 금지 | [04-4](../04-branching-strategies/2-summary.md) · [reliability/24](../../reliability/24-feature-flag-lifecycle/2-summary.md) |
| 수동 배포·확인 없음 | 1대에 복사 누락, 두 번째 기술자 검토 없음, 그런 검토를 요구하는 서면 절차 없음(¶15). SMARS에는 서면 코드 개발·배포 절차가 없었음(다른 그룹에는 있었음)(¶26) | 인벤토리 기반 자동 배포 + 배포 후 판 일치 검증 | [06-3](../06-ci-cd-pipelines/2-summary.md) |
| 경보가 아닌 신호 | "Power Peg disabled" 메일 97통이 개장 전에 왔으나 경보로 설계되지 않음(¶19) | 이상 신호를 경보·대시보드로, 형식 표준 | [16](../16-operational-standards/2-summary.md) · [reliability/43](../../reliability/43-alerting-and-on-call/2-summary.md) |
| 사고 대응 절차 없음 | 사고 대응 감독 절차 없음, 운영 중 시스템에서 기술팀이 원인 찾기, 7대 제거로 악화(¶27). 오작동 시스템을 시장에서 끊을 시점 지침 없음(¶42) | 런북, 킬 스위치, "되돌리기도 변경"이라는 판단 | [11-1](../11-documentation-practices/2-summary.md) · [reliability/23](../../reliability/23-deployment-strategies/2-summary.md) · [reliability/26](../../reliability/26-incident-response-and-postmortem/2-summary.md) |
| 출력 쪽 안전장치 없음 | SMARS에 나가는 주문과 들어온 주문을 비교하는 통제 없음, 스스로의 이상 활동에 SMARS를 멈추는 절차 없음(¶21) | 출력 상한·자동 정지(이 노트 범위 밖 — 위험 관리) | [reliability/04](../../reliability/04-failure-modes-catalog/2-summary.md) |

- SEC는 이렇게 적었다(¶41): RLP 코드 배포를 "간단히 다시 확인하는(simple double-check)" 서면 절차가 있었다면 빠진 서버를 찾아 8월 1일의 사건을 막을 수 있었다. BNET 메시지를 감시에 통합하는 절차도 같은 역할을 할 수 있었다.
- 해석: 일곱 고리 중 **하나만 있었어도** 사건이 작아졌을 가능성이 크다. 죽은 코드를 지웠다면 플래그를 재사용해도 깨어날 코드가 없다. 플래그 이름을 새로 지었다면 누락된 서버는 새 플래그를 모르고 무시한다(아래 실험 A의 B2). 배포 후 검증이 있었다면 개장 전에 누락을 안다. 이 판단은 SEC가 아니라 이 노트의 해석이다.

### 사건 2 — Cloudflare: "올바르게" 거친 규칙이 전역으로 수 초 만에 (2019-07-02)

출처
- John Graham-Cumming, "Details of the Cloudflare outage on July 2, 2019", Cloudflare 블로그, 2019-07-12 <https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/>(2026-10-05 열람).
- "Cloudflare outage caused by bad software deploy (updated)", Cloudflare 블로그, 2019-07-02(20:09 UTC 갱신 포함) <https://blog.cloudflare.com/cloudflare-outage/>.
- 시각은 원문대로 UTC다.

#### 사실 — 타임라인 (UTC, 원문)

| 시각 | 사건 |
|---|---|
| 13:31 | 승인된 PR(WAF 관리 규칙 변경)을 병합 |
| 13:37 | TeamCity가 규칙을 빌드하고 테스트 — 초록 |
| 13:42 | 테스트 통과 뒤 TeamCity가 자동으로 배포 시작. 방화벽 팀 엔지니어가 XSS 탐지 규칙의 "minor change"를 자동 프로세스로 배포했고 변경 요청(Jira) 티켓이 생성됨 |
| 13:45께 | "Three minutes later" 첫 PagerDuty 호출(WAF를 바깥에서 확인하는 합성 테스트). 이어서 종단 간 테스트 실패, 전역 트래픽 감소 경보, 광범위한 502, 각 PoP의 CPU 소진 보고 |
| 14:00 | WAF가 원인 구성 요소로 지목됨. 공격 가능성 배제 |
| 14:02 | 'global terminate'(구성 요소 하나를 전 세계에서 끄는 장치) 사용 제안 |
| 14:07 | 전역 WAF 종료 실행. 그 전에 자사 Access 서비스가 내려가 내부 제어판 인증이 막혀 잘 안 쓰던 우회 경로를 써야 했음 |
| 14:09 | 전 세계 트래픽·CPU가 예상 수준으로 복귀 |
| 14:52 | 원인과 수정 확인 뒤 WAF 전역 재활성화. 그 전에 유료 고객 트래픽을 뺀 한 도시에서 음성·양성 테스트 |

- 영향(원문): HTTP/HTTPS를 처리하는 CPU 코어가 전 세계에서 거의 100%. 방문자는 Cloudflare 도메인에서 502를 봤다. 상세 글은 서비스 중단을 "27 minutes"라고 쓴다. 원문이 27분의 시작·끝 시각을 직접 짚지는 않는다 — 13:42(배포 시작)부터 14:09(복귀)까지를 빼면 27분이다(계산). 트래픽 감소는 상세 글에서 "lost 80% of our traffic"(당시 들은 보고), 당일 글에서 "At its worst traffic dropped by 82%"다.
- 규모(원문): 최근 60일 WAF 관리 규칙 변경 요청 476건(평균 3시간에 1건). Quicksilver는 평균 초당 약 350건 변경을 배포하고, 전 세계 모든 기계까지 p99 2.29초. 180개가 넘는 도시에 복제.
- 원문은 6년 동안 전역 장애가 없었다고 적는다.

#### 두 배포 경로 — 같은 회사, 다른 절차

```text
  소프트웨어 배포 (SOP)                                    WAF 규칙 배포 (SOP, 당시)
  ─────────────────────                                    ──────────────────────────
  PR → TeamCity 빌드 → 리뷰어 승인 → 빌드·테스트 재실행          PR → 승인 → 병합(13:31)
     → 변경 요청서(관리자 또는 기술 리드 승인)                    → TeamCity 빌드·테스트 초록(13:37)
     → DOG  (직원만 지나는 PoP)                                  → 변경 요청서(배포·롤백 계획, SOP 링크)
     → PIG  (무료 고객 일부 트래픽)                               → Quicksilver로 전역 (13:42, p99 2.29초)
     → Canary (전 세계 3곳, 유료·무료)                             
     → 전역        "몇 시간~며칠"                                  "수 초"
```

- 원문: 규칙 변경 SOP는 전역 배포를 "specifically allows" 했다. 소프트웨어 배포와 달리 WAF는 "by design" 이 단계 절차를 쓰지 않았다. 이유는 새 위협에 빠르게 대응해야 해서다(예: 5월 SharePoint 취약점 규칙).
- 원문: 그 규칙은 "simulate" 모드(실제 트래픽을 통과시키되 막지 않고 오탐·미탐률을 잼)로 배포될 예정이었다. 그래도 규칙은 **실행**되어야 하므로 CPU를 썼다.
- 원문: 배포 전까지는 모두 "correctly" 진행됐다 — PR, 승인, CI/CD 빌드·테스트, 롤아웃·롤백이 적힌 변경 요청서, 롤아웃 실행.

#### 원문이 든 열한 가지 취약점과 실천 장치

원문은 "단일 근본 원인"을 찾는 것이 현실을 가릴 수 있다고 쓰고 여러 원인을 나열했다.

| # | 원문(요약) | 실천 관점 | leaf |
|---|---|---|---|
| 1 | 엔지니어가 크게 백트래킹할 수 있는 정규식을 씀 | 알고리즘 관점 — 이 노트 범위 밖 | algorithm/43(미작성) · [algorithm/13](../../algorithm/13-backtracking/2-summary.md) |
| 2 | 정규식 과다 CPU를 막던 보호 장치가 몇 주 전 WAF 리팩터링(CPU를 덜 쓰게 하려던 작업)에서 실수로 제거됨 | 리팩터링이 안전장치를 지움 — 그 장치를 확인하는 테스트가 없었다(해석) | [05](../05-code-review/2-summary.md) · [14](../14-quality-standards/2-summary.md) |
| 3 | 정규식 엔진에 복잡도 보장이 없음 | 의존성·엔진 선택(도입 판단) | [13](../13-build-vs-buy-and-adoption/2-summary.md) |
| 4 | 테스트 묶음에 과다 CPU 사용을 식별할 방법이 없음. 이전 빌드 로그에서도 테스트 실행 시간 증가가 관찰되지 않음 | CI에 성능 예산 테스트 | [06](../06-ci-cd-pipelines/2-summary.md) · 실험 C |
| 5 | SOP가 비긴급 규칙 변경을 단계 배포 없이 전역에 허용 | 설정·규칙도 단계 배포. 긴급 경로는 따로 | [06](../06-ci-cd-pipelines/2-summary.md) · [reliability/23](../../reliability/23-deployment-strategies/2-summary.md) |
| 6 | 롤백 계획이 WAF 전체 빌드를 두 번 돌려야 해 너무 오래 걸림 | 롤백도 빠른 경로가 필요(이전 산출물 재지정) | [06-4](../06-ci-cd-pipelines/2-summary.md) · [07](../07-build-systems-and-reproducibility/2-summary.md) |
| 7 | 전역 트래픽 감소 첫 경보가 너무 늦게 울림 | 경보 설계 | [reliability/43](../../reliability/43-alerting-and-on-call/2-summary.md) |
| 8 | 상태 페이지를 충분히 빨리 갱신하지 못함 | 사고 소통 | [reliability/26](../../reliability/26-incident-response-and-postmortem/2-summary.md) |
| 9 | 장애 때문에 자사 시스템 접근이 어려웠고 우회 절차가 훈련되지 않음 | 런북·긴급 경로 리허설 | [11-1](../11-documentation-practices/2-summary.md) · [reliability/44](../../reliability/44-runbooks-and-operational-readiness/2-summary.md) |
| 10 | 일부 SRE가 보안 정책(자주 안 쓰면 자격 증명 비활성화)으로 접근 권한을 잃음 | 비상 접근 경로의 정기 점검 | [reliability/44](../../reliability/44-runbooks-and-operational-readiness/2-summary.md) |
| 11 | 고객 대시보드·API도 Cloudflare 엣지를 거쳐 접근 불가 | 제어 경로가 장애 난 데이터 경로에 의존 | [reliability/51](../../reliability/51-cells-stamps-and-blast-radius/2-summary.md) |

- 원문의 후속 조치: WAF 릴리스 작업을 전면 중단. 제거된 CPU 보호 장치 복구(완료). WAF 관리 규칙 3,868개 전부를 손으로 점검(점검 완료). 테스트 묶음에 규칙별 성능 프로파일링 도입(ETA 7월 19일). re2 또는 Rust regex 엔진으로 전환(ETA 7월 31일). 규칙도 다른 소프트웨어처럼 단계 배포로 바꾸되, 실제 공격 대응용 긴급 전역 배포 능력은 유지. 대시보드·API를 엣지 밖으로 뺄 비상 수단. 상태 페이지 갱신 자동화.

### 두 사건을 나란히 (해석)

| | Knight 2012 | Cloudflare 2019 |
|---|---|---|
| 배포 방식 | 사람이 서버마다 복사, 며칠에 걸쳐 | 자동(CI 통과 뒤 TeamCity), 수 초 만에 전역 |
| 리뷰·테스트 | 두 번째 기술자 검토 없음, 2005년 이후 재시험 없음 | PR 승인, CI 초록 — 그런데 CPU를 재는 테스트가 없음 |
| 단계 배포 | 며칠에 걸친 단계 배포는 있었음 — 다만 끝난 뒤 "다 같은가"를 확인하지 않음 | 소프트웨어엔 있었음 — 규칙엔 SOP 예외 |
| 폭발 반경 | 1대(누락)에서 시작, 되돌리기로 8대 | 처음부터 전 세계 |
| 빨리 멈추는 장치 | 시장에서 끊을 시점 지침 없음(¶42) | global terminate가 있었음 — 접근 경로가 막혀 늦음 |
| 남은 "옛 것" | 9년 된 죽은 코드 + 재사용 플래그 | 리팩터링에서 사라진 보호 장치 |

- 해석: 두 사건의 교훈은 "자동화하라"가 아니다. Cloudflare는 자동화돼 있었고, 자동화가 결함을 **더 빨리** 퍼뜨렸다. 공통으로 빠진 것은 두 가지다.
  1. **배포된 것이 의도한 것과 같고 안전한지 확인하는 단계** — Knight는 판 일치, Cloudflare는 자원 사용량.
  2. **처음 노출 범위를 제한하는 것** — Knight는 확인 전에 개장했고, Cloudflare는 규칙이 단계 배포 밖이었다.
- 해석: "설정·규칙·플래그는 코드가 아니다"라는 생각이 두 사건 모두에 있다. Knight의 플래그 값, Cloudflare의 규칙은 코드처럼 실행되는 입력이었다. 같은 구조가 2024년 CrowdStrike 채널 파일 사건에도 있다 — [testing/21-test-incidents](../../testing/21-test-incidents/2-summary.md) 장애 4, [reliability/53](../../reliability/53-reliability-incidents/2-summary.md) 사건 4.

### 실험 A: 재사용 플래그 + 배포 누락 + "되돌리기" 모형 (시뮬레이션)

실제 SMARS를 재현한 것이 아니다. 서버 8대, 부모 주문 212건(SEC ¶17의 수만 빌려 옴)을 라운드 로빈으로 나누는 모형이다. 옛 판(OLD)은 `power_peg` 플래그를 Power Peg로 해석하고, 누적 수량 확인이 없어 모형의 상한(1,000)까지 자식 주문을 낸다. 새 판(NEW)은 필요한 만큼(300주 ÷ 100주 = 3건)만 낸다.

```java
static int handle(Build b, Order o, String rlpFlagName) {
    boolean on = o.flags().getOrDefault(rlpFlagName, false);
    if (b == Build.NEW) {
        return on ? (o.qty() + FILL_PER_CHILD - 1) / FILL_PER_CHILD : 0; // RLP: 필요한 만큼만
    }
    // OLD 판: 옛 코드는 "power_peg" 플래그를 Power Peg로 해석한다.
    // 누적 수량 확인이 다른 곳으로 옮겨진 뒤라(2005) 체결이 다 돼도 멈추지 않는다.
    boolean powerPeg = o.flags().getOrDefault("power_peg", false);
    if (!powerPeg) return 0;
    int sent = 0;
    while (sent < CHILD_CAP) sent++;      // 멈출 조건이 없다 -> 상한까지
    return sent;
}
```

(실험, eclipse-temurin:21-jdk OpenJDK 21.0.12, `java FlagSim.java`, `--network none --cpus=1`, 2026-10-05 — 결정적 계산, 실행마다 같음)

```text
== A. 플래그 이름 재사용(power_peg를 RLP용으로)
A1 8대 모두 새 판                       판=[N, N, N, N, N, N, N, N]
   서버별 자식 주문=[81, 81, 81, 81, 78, 78, 78, 78] 합계=636 (정상 기대 636)
A2 1대 누락                           판=[N, N, N, N, N, N, N, O]
   서버별 자식 주문=[81, 81, 81, 81, 78, 78, 78, 26000] 합계=26558 (정상 기대 636)
A3 7대도 옛 판으로 되돌림                   판=[O, O, O, O, O, O, O, O]
   서버별 자식 주문=[27000, 27000, 27000, 27000, 26000, 26000, 26000, 26000] 합계=212000 (정상 기대 636)
== B. 새 이름(rlp_enabled)을 쓴 경우
B2 1대 누락                           판=[N, N, N, N, N, N, N, O]
   서버별 자식 주문=[81, 81, 81, 81, 78, 78, 78, 0] 합계=558 (정상 기대 636)
B3 7대도 옛 판으로 되돌림                   판=[O, O, O, O, O, O, O, O]
   서버별 자식 주문=[0, 0, 0, 0, 0, 0, 0, 0] 합계=0 (정상 기대 636)
== C. 배포 검증 단계(판 일치)
   8대 모두 새 판: verify=true
   1대 누락:      verify=false
```

- 관찰
  - A2: 1대 누락만으로 자식 주문이 636 → 26,558(약 42배). 늘어난 것은 전부 8번 서버다.
  - A3: "되돌리기"로 7대를 옛 판으로 돌리자 212,000. 되돌린 판이 **옛 의미의 플래그**를 읽기 때문이다. SEC ¶27의 "악화"와 같은 방향이다(모형이므로 배수 자체는 의미가 없다).
  - B2·B3: 플래그 이름을 새로 지으면 옛 판은 그 플래그를 모른다. 누락된 서버는 RLP 주문을 **처리하지 않을** 뿐이다(558, 0). 이것도 결함이지만 조용히 덜 하는 쪽이고 폭주하지 않는다.
  - C: 판 일치 검증은 1대 누락을 `false`로 잡는다. 사람이 "끝났다"고 보고한 뒤에도 잡는다.
- 한계: 체결 수량·가격·시장 영향은 모형에 없다. 자식 주문 수의 **방향**만 본다.

### 실험 B: 백트래킹 정규식의 시간 — JDK 21 java.util.regex vs RE2J (선택 실험)

알고리즘 설명은 algorithm/43(미작성)에 맡기고, 여기서는 "테스트 입력이 작으면 안 보이고 입력이 조금만 길어져도 CPU를 태운다"는 **테스트 설계** 관점만 본다. 같은 패턴을 백트래킹 엔진(java.util.regex)과 선형 시간을 보장하는 엔진(RE2J 1.8)으로 `find()` 하고 시간(3회 중앙값)을 쟀다. 입력은 모두 **매칭에 실패하는** 문자열이다.

```java
// Cloudflare 2019-07-12 보고서의 정규식을 Java 문자열로 옮김({} 는 Java에서 \{\} 로 이스케이프)
static final String CF = "(?:(?:\\\"|'|\\]|\\}|\\\\|\\d|(?:nan|infinity|true|false|null|undefined|symbol|math)|`|\\-|\\+)+[)]*;?((?:\\s|-|~|!|\\{\\}|\\|\\||\\+)*.*(?:.*=.*)))";
...
long j = medianMicros(s -> jp.matcher(s).find(), in);   // java.util.regex
long r = medianMicros(s -> rp.matcher(s).find(), in);   // com.google.re2j
```

(실험, eclipse-temurin:21-jdk OpenJDK 21.0.12 + RE2J 1.8, `--network none --cpus=1 -Xmx256m`, 2026-10-05 — 시간은 실행마다 다르다. 두 번 돌린 값)

```text
== .*.*=.*   입력 = "x" 뒤에 x를 n개
  n=  250  java.util.regex    922,654 us   re2j   1,529 us   matched=false/false
  n=  500  java.util.regex    329,749 us   re2j   1,129 us   matched=false/false
  n= 1000  java.util.regex  2,658,116 us   re2j   1,092 us   matched=false/false
  n= 2000  java.util.regex 19,545,277 us   re2j   1,865 us   matched=false/false
== .*.*=.*;   입력 = "x=x" 뒤에 x를 n개
  n=  250  java.util.regex     50,984 us   re2j   1,004 us   matched=false/false
  n=  500  java.util.regex    340,243 us   re2j     592 us   matched=false/false
  n= 1000  java.util.regex  2,700,345 us   re2j     857 us   matched=false/false
  n= 2000  java.util.regex 21,025,179 us   re2j   1,741 us   matched=false/false
== Cloudflare 원본   입력 = ""x" 뒤에 x를 n개
  n=  250  java.util.regex      1,519 us   re2j   1,991 us   matched=false/false
  n=  500  java.util.regex      3,684 us   re2j     935 us   matched=false/false
  n= 1000  java.util.regex     14,871 us   re2j   1,819 us   matched=false/false
  n= 2000  java.util.regex     45,273 us   re2j   2,897 us   matched=false/false
```

두 번째 실행(같은 명령): `.*.*=.*`는 n=1000에서 2,369,126us, n=2000에서 19,181,490us. `.*.*=.*;`는 n=2000에서 21,013,662us. Cloudflare 원본(`"x…`)은 n=2000에서 91,049us.

사실 점검 재실행(같은 코드·같은 명령, 네 경우를 한 번에, 2026-10-05): `.*.*=.*`는 n=1000 2,486,511us · n=2000 19,129,149us, `.*.*=.*;`는 n=2000 20,720,936us, 원본 `"x…`는 n=2000 76,443us, 원본 `1…`는 n=1000 6,106,904us · n=2000 48,789,891us. RE2J는 모든 줄에서 3.5ms 이하였다. 절대값은 실행마다 크게 달랐지만(원본 `1…` n=2000: 28초 vs 49초) 두 배 길이에 약 8배라는 비율은 같았다.

같은 원본 정규식에 첫 그룹의 `\d`에 걸리는 문자만 이어 붙인 입력(`java RegexTime.java digits`, 같은 환경):

```text
== Cloudflare 원본   입력 = 숫자 1을 n+1개
  n=  250  java.util.regex    146,320 us   re2j   2,811 us   matched=false/false
  n=  500  java.util.regex    450,881 us   re2j     982 us   matched=false/false
  n= 1000  java.util.regex  3,502,881 us   re2j   1,867 us   matched=false/false
  n= 2000  java.util.regex 27,966,308 us   re2j   3,385 us   matched=false/false
```

- 관찰
  - java.util.regex는 n을 1000 → 2000으로 두 배 하면 시간이 약 7~8배(2.66s → 19.5s, 3.50s → 27.97s, 재실행 2.49s → 19.1s, 6.11s → 48.8s)로 늘었다. 입력 2,000자짜리 요청 하나가 CPU 1개로 제한한 컨테이너(`--cpus=1`)에서 패턴·실행에 따라 끝나기까지 약 19~49초 걸렸다(`System.nanoTime()`으로 잰 경과 시간 — CPU 사용 시간을 따로 재지는 않았다).
  - RE2J는 같은 입력에서 수 ms 이하로 머물렀다.
  - n=250이 n=500보다 느린 줄(922,654us)은 JIT 워밍업 등 측정 잡음으로 보인다(해석). 작은 n의 값은 비교에 쓰지 않는다.
  - **같은 정규식도 입력에 따라** 수십 ms(`"x…`, n=2000에서 45~91ms)와 수십 초(`1…`, n=2000에서 28~49초)로 갈렸다. 원본 패턴의 첫 그룹에 걸리는 시작 위치가 많을수록 백트래킹이 반복된다(해석).
- 테스트 설계 관점: 정상 요청·공격 요청 모음으로 "막아야 할 것을 막고, 통과시킬 것을 통과시키는가"만 보면 위 입력은 그냥 "통과(매칭 실패)"로 끝난다. 원문 4번 취약점처럼 **시간**을 재지 않으면 이 결함은 테스트에서 보이지 않는다.

### 실험 C: 규칙 배포 전 CI의 시간 예산 검사

원문 후속 조치 "테스트 묶음에 규칙별 성능 프로파일링"을 가장 작은 형태로 만든 것이다. 규칙마다 적대적 입력(1,000자)에 돌리고 50ms를 넘으면 중단·거부한다. java.util.regex는 매칭 도중 끊을 API가 없어서, `charAt`마다 마감 시각을 확인하는 `CharSequence`로 감쌌다.

```java
static final class Deadline implements CharSequence {
    final CharSequence s; final long deadline;
    Deadline(CharSequence s, long deadline) { this.s = s; this.deadline = deadline; }
    public char charAt(int i) {
        if (System.nanoTime() > deadline) throw new IllegalStateException("budget exceeded");
        return s.charAt(i);
    }
    public int length() { return s.length(); }
    public CharSequence subSequence(int a, int b) { return new Deadline(s.subSequence(a, b), deadline); }
    public String toString() { return s.toString(); }
}
...
try { p.matcher(new Deadline(in, t0 + budgetMs * 1_000_000)).find(); }
catch (IllegalStateException e) { verdict = "FAIL (" + budgetMs + "ms 초과에서 중단)"; }
```

(실험, eclipse-temurin:21-jdk OpenJDK 21.0.12, `java RuleBudget.java`, `--network none --cpus=1`, 2026-10-05)

```text
xss-1            최악    0 ms  PASS
sqli-1           최악    0 ms  PASS
xss-2 (2019형)    최악  100 ms  FAIL (50ms 초과에서 중단)
rules: REJECTED
exit=1
```

- 관찰: 2019형 패턴은 배포 전에 종료 코드 1로 막힌다. 실제 중단은 예산(50ms)보다 늦었다: `--cpus=1`에서 94~101ms(사실 점검 재실행 포함 4회), 같은 코드를 `--cpus=2`로 돌리면 58~61ms(2회). 매칭 중에는 `charAt`이 계속 불리므로 늦어짐의 주된 원인은 확인 간격보다 컨테이너 CPU 제한(CFS 할당량을 JIT·GC 스레드와 나눠 씀)으로 보인다(해석). 마감 시각이 지나도 그 스레드가 CPU를 다시 받을 때까지 확인이 일어나지 않는다.
- 한계: 적대적 입력을 사람이 골랐다. 입력 생성(속성 기반·퍼징)과 엔진 교체(RE2J처럼 선형 보장)가 근본 대책이고, 시간 예산 검사는 그물 하나다.

## 쓰이는 자료구조·알고리즘

- **백트래킹 vs Thompson NFA 시뮬레이션** — java.util.regex·PCRE는 백트래킹이라 최악에 입력 길이에 대해 다항(패턴에 따라 지수) 시간이 걸린다. RE2·RE2J·Rust regex는 상태 집합을 한 글자씩 옮기는 방식으로 입력 길이에 선형인 시간을 보장한다(Cloudflare 보고서 부록이 Thompson 1968을 들어 설명). 알고리즘 본문은 algorithm/43(미작성)과 [algorithm/13-backtracking](../../algorithm/13-backtracking/2-summary.md).
- **콘텐츠 해시로 판 일치 확인** — 서버마다 실행 중인 산출물의 해시를 모아 종류 수를 센다(실험 A의 C, [06-3](../06-ci-cd-pipelines/2-summary.md)). git 객체 모델과 같은 원리다 — [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md).
- **플래그 = 이름 → 동작의 사상(map)** — 같은 키를 다른 판의 코드가 다른 의미로 해석하면 사상이 판마다 달라진다. 키를 재사용하지 않으면 모르는 키는 기본값(꺼짐)으로 떨어진다(실험 A의 B).
- **전역 복제 KV 저장소(Quicksilver)** — 쓰기 하나가 전 세계 기계로 수 초 안에 복제된다(원문: p99 2.29초). 전파 속도 자체가 폭발 반경을 정한다.
- **단계 배포 = 표본 검사** — DOG → PIG → Canary는 노출을 작은 표본에서 큰 표본으로 늘리는 순서다. 판정 방법은 [reliability/23](../../reliability/23-deployment-strategies/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 사고 보고서를 실천 관점으로 읽는 순서

```text
  ① 타임라인: 변경이 언제 만들어지고(커밋·병합), 언제 어디까지 퍼졌나(배포 시작·범위·속도)
  ② 경로: 그 변경은 어느 배포 경로를 탔나. 그 경로는 다른 변경의 경로와 같은 단계를 거치나
  ③ 확인: 배포 뒤 무엇이 "같은가·안전한가"를 확인했나. 누가, 무엇으로
  ④ 남은 것: 옛 코드·옛 플래그·사라진 안전장치처럼 "지금은 안 쓰는" 것이 관여했나
  ⑤ 멈춤: 멈추는 장치(킬 스위치·롤백)가 있었나. 그 장치까지 가는 길이 장애에 막혔나
  ⑥ 내 시스템: ①~⑤를 내 배포 경로에 그대로 물어 본다
```

### 2. 내 시스템으로 옮길 점검 목록

| 질문 | 두 사건에서 | 장치 | leaf |
|---|---|---|---|
| 배포 뒤 전 인스턴스의 판이 같은지 자동으로 확인하나? 응답 없는 인스턴스를 "다름"으로 세나? | Knight ¶15 | 해시 대조, 버전 혼재 경보 | [06-3](../06-ci-cd-pipelines/2-summary.md) · [19 적용 3](../19-practice-symptom-index/2-summary.md) |
| 다 쓴 플래그 이름을 새 기능에 쓰는 일을 막나? | Knight ¶13 | 플래그 등록부, 이름 재사용 금지, 만료 테스트 | [04-4](../04-branching-strategies/2-summary.md) · [reliability/24](../../reliability/24-feature-flag-lifecycle/2-summary.md) |
| 안 쓰는 코드가 운영 서버에 "켤 수 있는 상태로" 남아 있나? | Knight ¶13·¶41 | 분기 코드부터 삭제 | [10](../10-technical-debt/2-summary.md) · [software-design/54](../../software-design/54-designing-for-deletion/2-summary.md) |
| 설정·규칙·플래그 값이 코드와 같은 단계 배포를 거치나? 예외 경로가 있다면 "긴급"에만 쓰이나? | Cloudflare 취약점 5 | 단계 배포, 긴급 경로 분리·기록 | [06](../06-ci-cd-pipelines/2-summary.md) · [reliability/23](../../reliability/23-deployment-strategies/2-summary.md) |
| CI가 정확성만 보나, 자원 사용(시간·CPU·메모리)도 보나? | Cloudflare 취약점 4 | 성능 예산 테스트(실험 C) | [06](../06-ci-cd-pipelines/2-summary.md) |
| 안전장치(타임아웃·상한·보호 코드)를 지우는 리팩터링을 테스트가 막나? | Cloudflare 취약점 2 | 안전장치마다 그것을 확인하는 테스트 | [05](../05-code-review/2-summary.md) · [14](../14-quality-standards/2-summary.md) |
| 롤백이 "이전 산출물 재지정"인가, "다시 빌드"인가? 롤백 대상 판이 지금 플래그·데이터를 안전하게 읽나? | Cloudflare 취약점 6 · Knight ¶27 | 한 번 빌드·해시 지정, 롤백 리허설 | [06-4](../06-ci-cd-pipelines/2-summary.md) · [reliability/23](../../reliability/23-deployment-strategies/2-summary.md) |
| 킬 스위치·제어판까지 가는 길이 장애 난 시스템을 거치나? 우회 경로를 훈련하나? | Cloudflare 취약점 9·10·11 | 비상 접근 경로, 정기 훈련 | [11-1](../11-documentation-practices/2-summary.md) · [reliability/44](../../reliability/44-runbooks-and-operational-readiness/2-summary.md) |
| "경보처럼 생긴" 자동 메일·로그를 누가 보나? | Knight ¶19 | 경보로 승격하거나 없앤다 | [16](../16-operational-standards/2-summary.md) · [reliability/43](../../reliability/43-alerting-and-on-call/2-summary.md) |

### 3. 규칙·설정 변경의 배포 파이프라인 — 단계와 긴급 경로를 나눈 예

```yaml
# 예시(가상의 CI 설정) — 규칙 변경도 코드처럼 단계를 거치고, 긴급 경로는 따로 기록한다
stages: [test, perf-budget, stage-internal, stage-canary, global]

perf-budget:
  script: java RuleBudget.java          # 실험 C — 예산 초과 규칙이 있으면 종료 코드 1

stage-internal:                          # 직원 트래픽만
  script: deploy-rules --target=internal && watch-cpu --max=70% --for=10m

stage-canary:                            # 소수 지역·소수 고객
  script: deploy-rules --target=canary && watch-cpu --max=70% --for=30m

global:
  script: deploy-rules --target=all
  rules:
    - if: $EMERGENCY == "true"           # 실제 공격 대응만 — 위 단계를 건너뛰되
      when: manual                       #   사람 승인 + 사유를 사고 기록에 남긴다
```

- `deploy-rules`·`watch-cpu`는 이름만 지은 가상의 명령이다. 핵심은 구조다: 긴급 경로가 일반 경로의 "기본값"이 되지 않게 한다. Cloudflare의 후속 조치도 이 모양(단계 배포 + 긴급 전역 배포 능력 유지)이다.
- 대기 시간(10분·30분)·CPU 기준(70%)은 예시 값이다.

## 장애 시나리오와 대처

### 1. 일부 서버만 옛 판 + 재사용한 플래그 (Knight형)

- **현상**: 새 기능을 켠 순간 서버 한 대가 전혀 다른, 폭주하는 동작을 한다.
- **보이는 형태**: 인스턴스별 판이 하나만 다르다(실험 A2: 8번 서버만 26,000). 개장(트래픽 시작) 전부터 옛 기능 이름이 든 로그·메일이 나온다(Knight ¶19: "Power Peg disabled" 97통).
- **원인**: 수동 복사 누락 + 확인 절차 없음(¶15·¶26) + 옛 의미를 가진 플래그 재사용(¶13) + 지우지 않은 죽은 코드(¶13·¶41).
- **대처**: 배포 후 판 일치 검증(응답 없는 인스턴스 = 다름). 플래그 이름 재사용 금지. 다 쓴 기능은 분기 코드부터 지운다. 트래픽 시작 전에 이상 신호를 경보로 본다.

### 2. "되돌리기"가 사고를 키운다

- **현상**: 문제를 고치려고 최근 배포를 되돌렸는데 이상 동작이 더 많은 서버로 번진다.
- **보이는 형태**: 되돌린 뒤 이상 인스턴스 수가 늘어난다(실험 A3: 8대 모두, 212,000). Knight는 정상 배포된 7대에서 새 코드를 제거해 악화됐다(¶27).
- **원인**: 되돌린 판이 **지금의 플래그·데이터**를 옛 의미로 읽는다. 코드만 롤백하면 따로 관리되는 설정·데이터는 되돌아가지 않는다.
- **대처**: 롤백 전에 "옛 판이 지금 상태를 어떻게 읽나"를 묻는다. 먼저 플래그·킬 스위치로 기능을 끄고, 코드 롤백은 그다음이다. 롤백을 정기적으로 리허설한다([reliability/23](../../reliability/23-deployment-strategies/2-summary.md) 롤백 절).

### 3. "설정·규칙이라서" 단계 배포를 건너뜀 (Cloudflare형)

- **현상**: 코드 배포는 카나리를 거치는데, 설정·규칙·플래그 변경 하나가 수 초 만에 전 세계를 멈춘다.
- **보이는 형태**: 변경 직후 전역에서 동시에 CPU·오류율이 뛴다. 지역별 차이가 없다(Cloudflare: 13:42 배포, 약 3분 뒤 첫 호출, 전 세계 502).
- **원인**: 설정 배포 경로가 소프트웨어 배포 경로의 단계를 건너뛰도록 SOP가 허용했다(취약점 5). 빠른 전파 인프라(Quicksilver p99 2.29초)가 결함도 빠르게 퍼뜨렸다.
- **대처**: 설정·규칙도 단계 배포를 기본으로 한다. 전역 즉시 배포는 긴급 경로로 분리하고 사람 승인·사유 기록을 붙인다. 같은 구조의 다른 사건은 [testing/21](../../testing/21-test-incidents/2-summary.md) 장애 4(CrowdStrike 2024).

### 4. 리팩터링이 안전장치를 조용히 지움

- **현상**: 몇 주 전 성능 개선 리팩터링은 테스트를 다 통과했다. 오늘 들어온 규칙 하나가 CPU를 다 쓴다.
- **보이는 형태**: 보호 장치(타임아웃·상한·실행 한도)가 코드에서 사라졌는데 어떤 테스트도 빨개지지 않았다(Cloudflare 취약점 2). 테스트 실행 시간에도 변화가 없었다(취약점 4).
- **원인**: 안전장치를 "작동하는지" 확인하는 테스트가 없었다. 정확성 테스트는 안전장치가 없어도 통과한다(해석).
- **대처**: 안전장치마다 그것이 작동해야 하는 입력(느린 규칙·큰 입력)으로 테스트를 둔다. CI에 자원 예산 검사를 둔다(실험 C). 리팩터링 리뷰에서 지워진 줄에 상한·타임아웃이 있는지 따로 본다([05](../05-code-review/2-summary.md)).

### 5. 멈추는 장치까지 가는 길이 막힘

- **현상**: 원인을 14:00에 알았고 끄는 장치(global terminate)도 있었는데, 실행은 14:07이었다.
- **보이는 형태**: 내부 제어판 인증이 장애 난 자사 서비스(Access)를 거쳐 막혔다. 잘 안 쓰던 우회 경로를 써야 했고, 일부 SRE는 자격 증명이 비활성화돼 있었다(Cloudflare 취약점 9·10). Knight는 오작동 시스템을 언제 시장에서 끊을지 지침 자체가 없었다(¶42).
- **원인**: 복구 경로가 장애 경로에 의존했다. 비상 경로를 훈련하지 않았다.
- **대처**: 킬 스위치·제어판의 접근 경로를 데이터 경로와 분리한다. 런북에 우회 경로를 적고 정기적으로 실제로 써 본다([11-1](../11-documentation-practices/2-summary.md), [reliability/44](../../reliability/44-runbooks-and-operational-readiness/2-summary.md)). "언제 끊는가"를 미리 정한다.

## 핵심 문장

- Knight(2012)는 수동 배포에서 8대 중 1대가 빠졌고, 재사용한 플래그가 그 서버에서 2003년 이후 안 쓰던 Power Peg 코드를 깨웠다. SEC는 두 번째 기술자 검토와 서면 배포 절차가 없었다고 지적했다.
- Knight의 손실은 출처마다 다르다. 회사 보도자료(2012-08-02)는 세전 약 4.4억 달러, SEC 명령(2013)은 4.6억 달러다.
- Cloudflare(2019)는 PR 승인·CI 초록·변경 요청서를 다 거쳤지만, 규칙 배포 절차가 단계 배포 없이 전역 배포를 허용해 정규식 하나가 수 초 만에 전 세계 HTTP 처리 CPU를 소진시켰다(27분).
- 두 사건에 공통으로 빠진 것은 "배포된 것이 의도한 것과 같고 안전한지 확인하는 단계"와 "처음 노출 범위의 제한"이다. 자동화만으로는 둘 다 생기지 않는다.
- 설정·규칙·플래그는 코드처럼 실행되는 입력이다. 리뷰·테스트(자원 사용 포함)·단계 배포를 코드와 같이 거치게 하고, 긴급 경로는 따로 둔다.
- 롤백도 변경이다. 옛 판이 지금의 플래그·데이터를 어떻게 읽는지 확인하지 않은 롤백은 사고를 키울 수 있다.

## 관련 주제·근거

- 선행: [19-practice-symptom-index](../19-practice-symptom-index/2-summary.md)(3절 "배포 공포") · [06-ci-cd-pipelines](../06-ci-cd-pipelines/2-summary.md)(장애 3 수동 배포, 배포 누락 모형) · [04-branching-strategies](../04-branching-strategies/2-summary.md)(장애 4 플래그 부채) · [10-technical-debt](../10-technical-debt/2-summary.md) · [05-code-review](../05-code-review/2-summary.md) · [11-documentation-practices](../11-documentation-practices/2-summary.md)
- 다른 관점(정본)
  - 알고리즘: algorithm/43 alg-incidents — 미작성([algorithm 영역 표](../../algorithm/curriculum.md)) · [algorithm/13-backtracking](../../algorithm/13-backtracking/2-summary.md)
  - 운영: [reliability/24-feature-flag-lifecycle](../../reliability/24-feature-flag-lifecycle/2-summary.md) 장애 1 · [reliability/23-deployment-strategies](../../reliability/23-deployment-strategies/2-summary.md) 장애 3·롤백 · [reliability/04-failure-modes-catalog](../../reliability/04-failure-modes-catalog/2-summary.md) F-17 · [reliability/26-incident-response-and-postmortem](../../reliability/26-incident-response-and-postmortem/2-summary.md)
  - 같은 구조의 다른 사건: [testing/21-test-incidents](../../testing/21-test-incidents/2-summary.md)(CrowdStrike 2024 — 설정 콘텐츠의 시험·단계 배포) · [reliability/53-reliability-incidents](../../reliability/53-reliability-incidents/2-summary.md)
- 1차 출처
  - SEC Release No. 34-70694, Administrative Proceeding File No. 3-15570, "In the Matter of Knight Capital Americas LLC", 2013-10-16 — ¶1·¶9·¶12~¶19·¶21·¶26·¶27·¶41·¶42, IV절(제재금) <https://www.sec.gov/litigation/admin/2013/34-70694.pdf>. sec.gov가 연락처 없는 요청을 거부해 Internet Archive 사본으로 읽음 <https://web.archive.org/web/20150115011139/http://www.sec.gov/litigation/admin/2013/34-70694.pdf>
  - Knight Capital Group, "Knight Capital Group Provides Update Regarding August 1st Disruption to Routing in NYSE-listed Securities", 2012-08-02(EDGAR 8-K 첨부 99.1, Internet Archive 사본) <https://web.archive.org/web/20150413204538/http://www.sec.gov/Archives/edgar/data/1060749/000119312512332176/d391111dex991.htm>
  - John Graham-Cumming, "Details of the Cloudflare outage on July 2, 2019", 2019-07-12 — UTC 타임라인, 소프트웨어 배포 SOP(DOG·PIG·Canary), WAF 규칙 SOP, Quicksilver(p99 2.29초·초당 약 350건), 11가지 취약점, 후속 조치, 부록(백트래킹·Thompson) <https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/>
  - Cloudflare, "Cloudflare outage caused by bad software deploy (updated)", 2019-07-02 — 최악 82% 트래픽 감소, 14:02 판단·14:09 복구·14:52 재활성화 <https://blog.cloudflare.com/cloudflare-outage/>
  - RE2J — Maven Central `com.google.re2j:re2j:1.8` <https://github.com/google/re2j>
- 실험 목록
  - A. 재사용 플래그 + 배포 누락 + 되돌리기 모형(시뮬레이션): `scratchpad/ep/19/e20a/FlagSim.java`, `docker run --rm --network none --cpus=1 eclipse-temurin:21-jdk java FlagSim.java`, OpenJDK 21.0.12. 출력은 결정적이다.
  - B. 백트래킹 정규식 시간: `scratchpad/ep/19/e20b/RegexTime.java` + RE2J 1.8(공용 maven 저장소에서 받음), `java -Xmx256m -cp re2j-1.8.jar RegexTime.java`(두 번) · `… RegexTime.java digits`(한 번), `--network none --cpus=1`. 시간은 실행마다 다르다.
  - C. 규칙 시간 예산 검사: `scratchpad/ep/19/e20b/RuleBudget.java`, `java RuleBudget.java`, 종료 코드 1 확인.
