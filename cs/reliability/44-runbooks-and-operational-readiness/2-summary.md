# reliability/44-runbooks-and-operational-readiness — 런북·경보 연결·출시 전 운영 준비도 점검(PRR)·온콜 인수인계 — 정리 (힌트)

## 해결하는 문제

새벽 3시에 경보가 울린다. 받은 사람이 그 서비스를 처음 본다면, 무엇을 확인하고 무엇을 해야 하는지 모른다. 아는 사람을 깨우는 데만 30분이 간다.

```text
 런북 없음                                    런북 있음
 03:00 경보 "PostgresReplicationLagHigh"       03:00 경보 → 링크 클릭 → 런북
 03:05 대시보드 뒤지기                          03:02 확인 명령 3개 실행 → 증상 분기
 03:20 담당자 연락처 찾기                       03:05 완화: 읽기를 주 서버로(플래그)
 03:35 담당자 기상, 원격 접속                    03:20 지연 안 줄면 → 에스컬레이션 표의 2차 호출
```

- *런북(runbook)*: 경보 하나(또는 증상 하나)에 대해 **확인 → 완화 → 에스컬레이션**을 적은 문서. Google SRE 책은 *플레이북(playbook)* 이라 부른다.
- *운영 준비도 점검(PRR, Production Readiness Review)*: 서비스가 운영에 들어가기 전에(또는 SRE가 넘겨받기 전에) 운영 기준을 만족하는지 보는 점검(SRE 32장).

쉬운 예: 비행기 조종석의 비상 체크리스트다.
- 엔진 화재 경고가 뜨면 조종사는 기억에 기대지 않고 체크리스트를 순서대로 읽는다.
- 체크리스트는 그 기종의 것이어야 한다. 다른 기종 체크리스트를 따르면 더 위험하다.

똑같은 구조다.\
실무 예: DB 복제 지연, 디스크 90%, 큐 적체, 인증서 만료 임박 경보마다 런북. 새 서비스를 출시하기 전 대시보드·경보·롤백 절차 점검.

## 동작·원리

### 1. 경보 → 런북 → 행동의 연결

```text
 경보 규칙 (Prometheus)                     런북 (문서)                      행동
 - alert: PostgresReplicationLagHigh  ──▶  ## 증상     사용자에게 보이는 것    
   annotations:                            ## 확인     명령 → 결과 분기 ──┐
     runbook_url: runbooks/pg-lag.md       ## 완화     먼저 할 일          ├─▶ 완화
                                           ## 에스컬레이션 누구를, 언제     └─▶ 호출
```

- SRE 책 1장: 사람이 개입해야 할 때 모범 사례를 미리 적은 플레이북은 "즉흥(winging it)"보다 MTTR을 대략 **3배** 개선한다.
- SRE Workbook 8장: SRE에서는 경보를 만들 때 보통 대응하는 플레이북 항목도 만든다. 새 경보도 코드처럼 리뷰하고, 경보마다 플레이북 항목이 있어야 한다.
- 경보 → 런북 링크는 경보 정의 안에 둔다. Prometheus 규칙에서는 `annotations.runbook_url`이 관례다(예: kube-prometheus의 `kubernetesControlPlane-prometheusRule.yaml`이 경보마다 `runbook_url`을 단다). annotation은 경보 데이터에 실릴 뿐이고, 수신자가 보는 본문은 Alertmanager 알림 템플릿이 정한다(예: 기본 Slack 본문 템플릿 `slack.default.text`는 비어 있다 — alertmanager `template/default.tmpl`). 그래서 수신 채널 템플릿이 `runbook_url`을 표시하게 설정하고, 실제 알림에 링크가 보이는지 확인한다.

### 2. 런북의 구조 = 증상 분기 결정 트리

```text
 [경보: 복제 지연 > 30초]
   │
   ├─ 확인1: pg_stat_replication에 복제본이 보이나?
   │     ├─ 아니오 → 복제 연결 끊김 → "재연결" 절 → 안 되면 DB 온콜
   │     └─ 예
   ├─ 확인2: 주 서버에 오래 열린 트랜잭션·대량 쓰기가 있나?
   │     ├─ 예 → 쓰기 배치 일시 중지(플래그) → 지연 감소 확인
   │     └─ 아니오
   └─ 완화: 읽기를 주 서버로(read-from-primary) → 15분 안에 줄지 않으면 에스컬레이션
```

- *결정 트리*: 확인 결과마다 다음 단계가 갈리는 트리. 잎은 "완화 조치" 또는 "에스컬레이션".
- 확인 명령은 **읽기 전용**이 먼저다. 쓰기·재시작 같은 조치는 확인이 끝난 가지에만 둔다.
- SRE Workbook 8장의 논쟁: 플레이북을 일반적으로(예: "RPC 오류 높음" 하나 + 아키텍처 그림) 둘지, 단계별로 둘지 팀마다 갈린다. 권고: 최소 구조(필수 칸)만 합의하라. 그리고 **매번 같은 명령 목록을 실행하는 플레이북이면 자동화하라.**

### 3. 런북은 썩는다

- SRE Workbook 8장: 플레이북의 세부는 운영 환경이 바뀌는 속도로 낡는다. 매일 배포하면 매일 고쳐야 할 수도 있다.
- 가장 위험한 낡음: **확인·완화 명령이 지금 인프라와 안 맞는 것**. 새벽에 그대로 실행하면 2차 사고가 난다.

### 4. 실험: 런북 점검기 — 경보 링크, 필수 절, 확인 SQL을 지금 DB에서 실행

- 입력: Prometheus 형식 경보 규칙 3개, 런북 2개.
  - `pg-replication-lag.md`의 확인 SQL 중 둘은 **PostgreSQL 9.6 시절** 이름(`replay_location`, `pg_current_xlog_location()`)으로 썼다. PostgreSQL 10에서 `xlog`는 `wal`로, `location`은 `lsn`으로 이름이 바뀌었다(PostgreSQL 10 릴리스 노트).
- 점검: (1) 경보마다 `runbook_url`이 있나 (2) 런북에 `## 증상/확인/완화/에스컬레이션`이 있나 (3) ```sql 블록의 질의를 일회용 PostgreSQL 17 컨테이너에서 `ON_ERROR_STOP`으로 실행. 아래 구현은 블록을 **한 줄씩** 읽어 줄마다 `psql -c`로 보내므로, 질의가 한 줄에 하나씩 있는 런북만 검사한다(실험 런북은 그렇게 썼다). 여러 줄 질의를 검사하려면 블록 전체를 모아 한 번에 실행해야 한다.

```bash
# 3) 런북의 확인 SQL을 지금 버전의 DB에서 돌려 본다 (읽기 전용 질의만, 한 줄에 질의 하나라는 것이 전제)
awk '/^```sql/{f=1;next} /^```/{f=0} f' "$f" | while IFS= read -r q; do
  if out=$(docker exec $PG psql -U postgres -v ON_ERROR_STOP=1 -Atc "$q" 2>&1); then echo "  OK   ${q:0:60}"
  else echo "  실패 ${q:0:60}"; echo "       → $(echo "$out" | head -1)"; fi
done
```

(실험, PostgreSQL 17.11 `postgres:17` 일회용 컨테이너, bash + awk + psql, 2026-10-01)

```text
== 1. 경보 → 런북 링크
OK  PostgresReplicationLagHigh -> runbooks/pg-replication-lag.md
없음 PostgresTooManyConnections
OK  PostgresLongRunningTx -> runbooks/pg-long-tx.md
== 2. runbooks/pg-long-tx.md 필수 절
  OK  ## 증상
  OK  ## 확인
  OK  ## 완화
  빠짐 ## 에스컬레이션
== 3. runbooks/pg-long-tx.md 확인 SQL 실행 (PostgreSQL 17.11)
  OK   SELECT pid, now() - xact_start AS age, state, left(query, 40
== 2. runbooks/pg-replication-lag.md 필수 절
  OK  ## 증상
  OK  ## 확인
  OK  ## 완화
  OK  ## 에스컬레이션
== 3. runbooks/pg-replication-lag.md 확인 SQL 실행 (PostgreSQL 17.11)
  실패 SELECT client_addr, state, replay_location FROM pg_stat_repl
       → ERROR:  column "replay_location" does not exist
  실패 SELECT pg_current_xlog_location();
       → ERROR:  function pg_current_xlog_location() does not exist
  OK   SELECT pid, state, wait_event_type, now() - xact_start AS ag
```

- 관찰 1: 페이지 경보 하나(`PostgresTooManyConnections`)에 런북 링크가 없다. 새벽에 받은 사람은 빈손이다.
- 관찰 2: 런북 하나에 에스컬레이션 절이 없다. 확인·완화가 안 통하면 다음이 없다.
- 관찰 3: 문법은 멀쩡한 SQL 둘이 **지금 버전에서** 실패했다. 사람이 문서만 읽어서는 이 낡음을 알기 어렵다. 점검기를 CI나 주기 작업으로 돌리면 사고 전에 드러난다.
- 해석: 이번에는 확인 명령이라 "실패"로 끝났다. 완화 명령이 낡았다면 엉뚱한 대상을 바꾸는 2차 사고가 될 수 있다. 그래서 완화 명령은 `--dry-run`류나 대상 재확인 단계를 같이 적는다.

### 5. PRR — 운영 기준을 체크리스트로 본다

SRE 32장의 Simple PRR 모델은 보통 **이미 출시된 서비스**를 SRE 팀이 넘겨받기 전에 적용한다. 출시 전부터 참여하는 것은 아래의 Early Engagement 모델이다. Simple PRR 모델 단계:

```text
 Engagement ─▶ Analysis ─▶ Improvements & Refactoring ─▶ Training ─▶ Onboarding ─▶ Continuous Improvement
 (SLO 합의,    (체크리스트로    (우선순위대로 함께 고침)      (설계·요청 흐름·    (운영 책임을      (변경을 리뷰하며
  일정)         결함 찾기)                                   실습)              단계적으로 이전)   기준 유지)
```

- SRE가 보는 "운영(production)"의 축(32장): 시스템 아키텍처와 서비스 간 의존, 계측·지표·모니터링, 비상 대응, 용량 계획, 변경 관리, 성능(가용성·지연·효율).
- 32장의 체크리스트 예(원문 요지):
  - 업데이트가 시스템의 지나치게 큰 비율에 한 번에 영향을 주나?
  - 의존 서비스의 올바른 인스턴스(배치용이 아닌 서빙용)에 붙나?
  - 오류를 중앙 로깅에 보고하나? 사용자에게 저하·실패를 낳는 모든 예외 상황을 보고하나?
  - 사용자에게 보이는 요청 실패가 모두 계측·모니터링되고, 알맞은 경보가 있나?
- 32장의 한계 지적: 이미 출시된 서비스에 늦게 하는 PRR은 고칠 기회가 적다. 그래서 설계 단계부터 참여하는 Early Engagement, 공통 프레임워크로 기준을 기본값으로 만드는 Frameworks 모델로 진화했다.
- 출시 체크리스트의 예: SRE 부록 E "Launch Coordination Checklist"(항목 예: 기계·랙·클러스터가 죽으면 어떻게 되나, 백엔드가 죽은 것을 어떻게 감지하고 무엇을 하나, "Monitoring the monitoring", 카나리·단계적 출시), 원본 [server-design/08 「운영 준비 체크리스트」](../../systems/server-design/08-deployment-ops.md).

### 6. 온콜 인수인계

- SRE Workbook 8장 사례: 교대 시작에 이전 교대의 인수인계를 읽고, 교대 끝에 다음 담당에게 인수인계 메일을 보낸다.
- 인수인계에 담을 것(예시): 진행 중인 사고·완화 상태, 이번 교대의 경보와 조치, 낡았다고 발견한 런북, 다음 교대가 지켜볼 것(배포 예정, 용량 임박).
- 새 팀의 진입 순서(Workbook 8장 사례): 두 달 뒤 경험자 셋(팀장 Sara, 다른 SRE 팀에서 온 Mike, SRE 전입자)이 기존 팀의 온콜을 **그림자(shadow)** 로 따라가고, 석 달째에 주 담당이 되며 기존 팀은 백업(에스컬레이션 대상)으로 남았다. 신입 넷은 그다음에 이 경험자들을 shadow한 뒤 로테이션에 합류했다.
- 사고 지휘권 인계는 말로 명시한다 → [26-incident-response-and-postmortem](../26-incident-response-and-postmortem/2-summary.md) 5절.

## 쓰이는 자료구조·알고리즘

- **결정 트리** — 런북의 확인 단계. 내부 노드 = 확인 명령과 그 결과 조건, 잎 = 완화 또는 에스컬레이션. 깊이가 얕을수록(확인 2~3번 안에 잎) 새벽에 쓰기 쉽다.
- **맵(경보 이름 → 런북)** — 실험의 점검 1은 경보 집합과 런북 링크 맵의 차집합을 구한 것이다(링크 없는 경보).
- **상태 기계** — PRR 단계(Engagement → … → Continuous Improvement), 런북 항목의 상태(작성 → 검증됨 → 낡음 의심).
- **에스컬레이션 정책 = 시간 조건이 붙은 큐** — 1차가 N분 안에 확인하지 않으면 2차로(온콜 도구의 정책).

## 적용 — 풀어나가는 법

### 1. 런북 템플릿

```text
# <경보 이름>
## 증상        사용자에게 무엇이 보이나, 영향 범위, 심각도
## 대시보드    링크 1~2개 (경보가 가리키는 그래프)
## 확인        읽기 전용 명령과 "이 결과면 → 이 절로"
## 완화        먼저 할 일(되돌릴 수 있는 것부터), 확인 방법
## 에스컬레이션  누구를(역할), 언제(N분 뒤 / 조건), 어떻게(호출 경로)
## 마지막 검증  날짜, 검증한 버전 (점검기가 갱신)
```

### 2. 경보 규칙에 런북을 붙인다

```yaml
- alert: PostgresReplicationLagHigh
  expr: pg_replication_lag_seconds > 30
  for: 5m
  labels: {severity: page}
  annotations:
    summary: "복제 지연 30초 초과"
    runbook_url: "https://wiki.example.com/runbooks/pg-replication-lag"
```

- 경보 리뷰 규칙: `severity: page`인데 `runbook_url`이 없으면 병합을 막는다(실험의 점검 1을 CI에).
- 런북 명령 점검(실험의 점검 3)을 스테이징 DB에서 주기적으로 돌린다. 버전 업그레이드 PR에도 붙인다.

### 3. 자동화로 옮기는 기준

- 같은 경보에 매번 같은 명령을 같은 순서로 친다 → 그 런북은 스크립트가 되어야 한다(Workbook 8장).
- 판단이 필요한 가지만 사람에게 남긴다. 자동화된 완화에는 속도 제한을 둔다(사람보다 빨리 많은 것을 망가뜨릴 수 있다 — 26의 diskerase 사례).

### 4. 출시 전 PRR 점검표 (요지)

| 축 | 질문 | 증거 |
|---|---|---|
| SLO | SLI·SLO가 합의됐나 | 대시보드 링크 |
| 관측 | 사용자에게 보이는 실패가 모두 지표·경보로 잡히나 | 경보 규칙, 런북 링크 |
| 변경 | 롤백 절차를 실제로 해 봤나, 한 번에 전체를 바꾸지 않나 | 리허설 기록, 카나리 설정 |
| 용량 | 피크 부하 시험, 한 대가 빠져도 버티나 | 부하 시험 결과 |
| 의존 | 의존 서비스가 죽으면 어떻게 되나, 타임아웃이 있나 | 장애 주입 결과(45) |
| 비상 | 온콜 담당이 정해졌고 런북이 있나, 호출이 실제로 도착하나 | 테스트 호출 기록 |

## 장애 시나리오와 대처

### 1. ⚠ 새벽 경보에 런북이 없어 담당자 호출까지 30분

- 현상: 경보는 제때 울렸는데 완화가 한참 늦었다. 타임라인에 "담당자 찾기"가 길다.
- 보이는 형태: 경보 메시지에 링크가 없다. 사고 채널에 "이거 누가 알아요?"가 반복된다. 실험의 `없음 PostgresTooManyConnections`.
- 원인: 경보를 만들 때 런북을 의무로 하지 않았다.
- 대처: 페이지 경보는 `runbook_url` 필수(CI 점검). 런북에 에스컬레이션 표(역할·호출 경로)를 둔다. 경보 수가 많아 런북을 못 쓰겠다면 경보가 너무 많은 것이다(43).

### 2. ⚠ 런북 명령이 구 인프라 기준이라 실행 시 2차 사고

- 현상: 런북대로 명령을 쳤는데 실패하거나, 엉뚱한 대상이 바뀌었다.
- 보이는 형태: 실험처럼 `ERROR: function pg_current_xlog_location() does not exist`, `column "replay_location" does not exist`. 더 나쁜 경우는 옛 호스트 이름·옛 클러스터를 가리키는 완화 명령이 성공하는 것이다.
- 원인: 런북은 운영 환경이 바뀌는 속도로 낡는다(Workbook 8장). 버전 업그레이드·이전이 런북 갱신과 묶여 있지 않다.
- 대처: 런북 명령을 주기적으로 실행해 보는 점검기(읽기 전용 명령), 업그레이드 체크리스트에 "런북 점검" 추가, 완화 명령에는 대상 확인 단계(`SELECT current_setting('cluster_name')` 같은)와 dry-run을 적는다. 온콜이 런북 오류를 발견하면 그 교대 안에 고친다.

### 3. ⚠ 출시 후 대시보드·경보가 없어 고객 문의로 장애 인지

- 현상: 새 기능이 하루 동안 절반 실패했는데, 지원팀 문의로 처음 알았다.
- 보이는 형태: 사고 타임라인의 "탐지"가 고객 문의. 포스트모템 기준 중 "모니터링 실패(사람이 직접 발견)"에 해당(SRE 15장).
- 원인: 출시 기준에 관측이 없었다. PRR 없이 출시.
- 대처: 출시 체크리스트에 "사용자에게 보이는 실패가 모두 계측·경보되나"(SRE 32장 체크리스트 항목)를 넣는다. 출시 전에 테스트 경보를 실제로 울려 호출이 도착하는지 본다.

### 4. 인수인계 누락 — 진행 중이던 완화가 다음 교대에서 풀렸다

- 현상: 밤 교대가 임시로 꺼 둔 기능 플래그를 아침 교대가 "이상한 설정"으로 보고 되돌렸다. 같은 장애가 재발했다.
- 보이는 형태: 같은 경보가 교대 시각 직후 다시 울린다. 인수인계 기록이 없거나 한 줄이다.
- 원인: 진행 중인 완화와 그 이유가 전달되지 않았다.
- 대처: 인수인계 템플릿에 "진행 중인 완화와 되돌릴 조건"을 필수로. 임시 완화에는 만료·담당이 붙은 표식(플래그 설명란, 티켓 번호)을 남긴다.

## 핵심 문장

- 런북은 경보 하나에 대한 증상 → 확인 → 완화 → 에스컬레이션이다. 경보 정의 안에 링크해서 알림과 함께 오게 한다.
- SRE 책은 플레이북이 즉흥 대응보다 MTTR을 대략 3배 개선한다고 적는다. 매번 같은 명령 목록이면 자동화가 답이다.
- 런북은 운영 환경이 바뀌는 속도로 낡는다. 실험에서 PostgreSQL 9.6 시절의 확인 SQL 둘이 PostgreSQL 17에서 실패했다 — 명령을 주기적으로 실행해 보는 점검이 필요하다.
- PRR은 출시·인수 전에 SLO, 관측, 변경, 용량, 의존, 비상 대응을 체크리스트로 보는 과정이다. 늦을수록 고칠 기회가 적다.
- 인수인계에는 진행 중인 완화와 그 이유를 적는다. 모르는 사람은 완화를 "이상한 설정"으로 되돌린다.

## 관련 주제·근거

- 선행
  - [26-incident-response-and-postmortem](../26-incident-response-and-postmortem/2-summary.md) — 사고 지휘, 지휘권 인계, 포스트모템 기준
  - [43-alerting-and-on-call](../43-alerting-and-on-call/2-summary.md) — 증상 기반 경보, 온콜
- 후속·연결
  - [45-chaos-and-resilience-testing](../45-chaos-and-resilience-testing/2-summary.md) — 런북을 게임 데이에서 실제로 써 본다
  - engineering-practice/11 `documentation-practices` — 문서 신선도 (영역 표 [../../engineering-practice/README.md](../../engineering-practice/README.md)에서 "미작성")
  - 원본 [systems/server-design/08-deployment-ops.md](../../systems/server-design/08-deployment-ops.md) — 운영 준비 체크리스트(런북 항목 포함)
  - [engineering/development-standards/operational-standards](../../engineering/development-standards/operational-standards/2-summary.md) 5절 — "새벽 3시에 그대로 따라 할 수 있는" 런북
  - [database/32-replication-leader-follower](../../database/32-replication-leader-follower/2-summary.md) — 실험 런북이 다룬 복제 지연
- 교재·문서
  - Google SRE 책 1장 "Introduction"(플레이북 → MTTR 대략 3배 개선) <https://sre.google/sre-book/introduction/>
  - Google SRE 책 32장 "The Evolving SRE Engagement Model"(PRR 목표·단계, 운영 축, 체크리스트 예, Early Engagement·Frameworks) <https://sre.google/sre-book/evolving-sre-engagement-model/>
  - Google SRE 책 부록 E "Launch Coordination Checklist" <https://sre.google/sre-book/launch-checklist/>
  - SRE Workbook 8장 "On-Call"(플레이북 유지, 일반형 vs 단계형 논쟁, 경보마다 플레이북 항목, 인수인계, shadow 온콜) <https://sre.google/workbook/on-call/>
  - PagerDuty Incident Response 문서(심각도·역할·호출) <https://response.pagerduty.com/>
  - kube-prometheus `manifests/kubernetesControlPlane-prometheusRule.yaml`(경보마다 `runbook_url` 주석) <https://github.com/prometheus-operator/kube-prometheus>
  - PostgreSQL 10 릴리스 노트 — "xlog"→"wal", "location"→"lsn" 이름 변경 <https://www.postgresql.org/docs/release/10.0/>
- 실험 목록
  - 런북 점검기: `rules.yml`(경보 3개) + `runbooks/*.md` 2개 + `runbook-lint.sh`(bash·awk). 링크 누락, 필수 절 누락, 확인 SQL을 PostgreSQL 17.11 일회용 컨테이너(`postgres:17`)에서 `ON_ERROR_STOP`으로 실행. 결과: 링크 없음 1, 에스컬레이션 절 없음 1, 구 버전 SQL 2건 실패
