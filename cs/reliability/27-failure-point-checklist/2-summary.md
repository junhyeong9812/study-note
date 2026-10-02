# reliability/27-failure-point-checklist — 설계 시 실패 지점 점검 절차 — 정리 (힌트)

## 해결하는 문제

실패 모드를 알고 있어도 출시 전에 **묻지 않으면** 같은 사고가 다시 난다.
지식이 모자라서가 아니라, 경로의 한 칸만 보고 나머지 칸을 빼먹어서다.
"메시지 유실을 어떻게 막나?"에 발행 쪽(아웃박스)만 답하고 소비 쪽을 비우는 식이다.

쉬운 예: 비행기 이륙 전 점검표다.
- 숙련 조종사도 점검표를 읽는다. 아는 것을 몰라서가 아니라, 바쁠 때 한 줄을 건너뛰기 때문이다.

똑같은 구조다.\
실무 예: 새 기능 출시 전 리뷰에서 요청 경로의 경계마다 정해진 질문(느리면? 실패하면? 결과를 모르면? 두 번 오면?)을 순서대로 묻는다. 빈칸은 "막음" 또는 "이유가 있어 열어 둠"으로 기록한다.
Google SRE 27장도 같은 이유로 출시 점검표(launch checklist)를 쓴다. 항공 비행 전 점검표·수술 점검표를 예로 들며, 점검표는 실패를 줄이고 일관성·완전성을 준다고 적는다.

기초(메시지 파이프라인 5칸 — 발행 전·발행 중·브로커·소비 중·소비 후, 답하기 전 "어느 칸인가" 되짚기, 다른 질문에의 일반화)는 원본 [engineering/failure-point-checklist](../../engineering/failure-point-checklist/2-summary.md) 「되짚기 습관」·「5칸 체크리스트」·「같은 절차의 다른 적용」에 있다. 이 노트는 그 절차를 **요청 경로 전반의 경계별 점검**으로 넓히고, 질문마다 [04 카탈로그](../04-failure-modes-catalog/2-summary.md) 번호를 붙여 "알려진 실패 모드"와 잇는다. 메시지 파이프라인 두 칸(발행 전·소비 중)은 크래시 주입 시뮬레이션으로 보인다.

## 동작·원리

### 1. 점검의 단위 — 경계

```text
 사용자 ─①─> 게이트웨이 ─②─> 서비스 A ─③─> DB
                               │
                               ├─④─> 서비스 B (동기 호출)
                               ├─⑤─> 브로커 ─⑥─> 소비자 ─⑦─> 하위 저장소
                               └─⑧─> 외부 PG (돈이 움직임)
 번호 = 경계(호출·쓰기·발행이 일어나는 곳). 실패는 경계에서 생긴다.
```

- *경계(boundary)*: 프로세스·네트워크·트랜잭션이 바뀌는 지점. 한쪽의 고장이 다른 쪽의 결함이 되는 곳이다([01](../01-fault-error-failure-availability/2-summary.md)의 결함→오류→고장 사슬).
- 점검은 경계를 **빠짐없이 나열하는 것**에서 시작한다. 빠진 경계는 질문도 받지 않는다.

### 2. 경계마다 묻는 질문 — 여섯 줄

| # | 질문 | 막는 장치(예) | 카탈로그 |
|---|---|---|---|
| Q1 느림 | 상대가 느리면 얼마나 기다리나? 바깥 타임아웃보다 짧은가? 포기하면 하위 작업도 멈추나? | 계층별 타임아웃, 데드라인 전파, 취소 | F-16 |
| Q2 실패 | 실패하면 재시도하나? 몇 층에서? 상한·지터·예산은? | 재시도 예산, 서킷 브레이커 | F-09 |
| Q3 모름 | 응답을 못 받으면 상대가 처리했는지 아나? 그 상태를 무엇이라 부르나? | 멱등 키, 조회 API, "모름" 상태 + 대사 | F-20·F-10 |
| Q4 중복·순서 | 같은 요청·이벤트가 두 번 오면? 순서가 바뀌면? | 유니크 제약, 파티션 키 | F-11·F-12 |
| Q5 용량·편중 | 이 경계가 받는 최대량은? 한 키에 몰리면? 앞단을 늘리면 뒷단은? | 상한·셰딩, 커넥션 총량 계산 | F-03·F-19 |
| Q6 알기 | 이 경계가 조용히 틀리면 누가 언제 아나? | 지표·대사·불변식 검사, 그 검사의 감시 | F-25·F-21 |

- 여섯 줄을 고른 기준: 03 노트의 네 양상과 04 카탈로그에서 **경계 하나에서 판정할 수 있는** 질문만 남겼다. 이 묶음은 이 노트의 구성이고, 표준 목록이 아니다.
- 답은 원본 판정 규칙대로 **장치 이름**이어야 한다. "조심한다"는 빈칸이다.

### 3. 메시지 파이프라인은 다섯 칸으로 다시 쪼갠다

위 그림의 ⑤⑥⑦은 원본의 5칸과 같다.

```text
 발행 전 ──> 발행 중 ──> 브로커 ──> 소비 중 ──> 소비 후
 (DB↔이벤트)  (앱→브로커)  (저장·복제)  (poll→처리→커밋)  (하위 반영)
   아웃박스     acks=all    복제·min.insync  처리 후 커밋+멱등  멱등 upsert·대사
```

- Kafka 4.1 기준 기본값(공식 설정 문서): 프로듀서 `acks=all`, `enable.idempotence`는 충돌하는 설정이 없으면 켜짐. 브로커·토픽 `min.insync.replicas=1`, `unclean.leader.election.enable=false`, `retention.ms=604800000`(7일). 소비자 `enable.auto.commit=true`.
  - `min.insync.replicas` 기본 1은 `acks=all`이어도 복제본 하나만 남아 있으면 쓰기를 받는다는 뜻이다. 3번 칸에서 이 값을 명시적으로 묻는다.
- 자동 커밋에 관해 KafkaConsumer Javadoc(4.1)은 이렇게 적는다: 자동 커밋도 at-least-once가 될 수 있지만, 각 `poll()`이 돌려준 데이터를 다음 `poll()`(또는 close) 전에 다 소비해야 한다. 그러지 않으면 커밋된 오프셋이 소비 위치를 앞질러 레코드를 놓칠 수 있다.
  - 참고: 원본 [Claude 추가] 절의 "poll한 오프셋을 처리 전에 커밋하면(auto-commit 기본값의 함정)"은 조건이 빠졌다. 자동 커밋 자체가 처리 전 커밋은 아니고, 처리를 다른 스레드로 넘기는 등 다음 `poll()` 전에 처리를 끝내지 않을 때 앞질러진다(위 Javadoc).

### 실험: 발행 전·소비 중 칸에 크래시를 넣으면

- 메시지 1만 건. 단계마다 1% 확률로 프로세스가 죽고 재시작한다(예시 확률, seed 고정 시뮬레이션 — 실제 브로커가 아니다).
- 칸 1: 이중 쓰기(DB 커밋 → 발행) vs 아웃박스(같은 트랜잭션에 outbox 행 → 릴레이가 발행 → sent 표시).
- 칸 4: 처리 전 커밋 vs 처리 후 커밋 vs 처리 후 커밋 + 멱등(이벤트 ID 집합).

```java
// 핵심 부분 (전체: scratchpad/rel/01/e27/Pipeline.java)
case "처리 전 커밋" -> {
    committedOffset = pos + 1;                                     // 먼저 커밋
    if (r.nextDouble() < CRASH) { crashed = true; break; }         // 처리 전에 죽음 → 이 메시지는 다시 안 온다
    applied[pos]++;
}
case "처리 후 커밋", "처리 후 커밋 + 멱등" -> {
    if (mode.endsWith("멱등")) { if (inbox.add(pos)) applied[pos]++; }   // 유니크 제약 흉내
    else applied[pos]++;
    if (r.nextDouble() < CRASH) { crashed = true; break; }         // 커밋 전에 죽음 → 다시 와서 또 처리
    committedOffset = pos + 1;
}
```

(실험, JDK 21 eclipse-temurin, `--cpus=2`, 2026-10-01)

```text
메시지 10000건, 단계마다 크래시 확률 1% (seed 고정)

-- 칸 1 발행 전
이중 쓰기     : DB 커밋 10000, 브로커 도착 9913 → 유실 87
아웃박스      : 업무 커밋 10000, 브로커 도착 10089(서로 다른 10000건) → 유실 0, 중복 89

-- 칸 4 소비 중
처리 전 커밋         : 반영 누락  88건, 중복 반영   0건
처리 후 커밋         : 반영 누락   0건, 중복 반영  88건
처리 후 커밋 + 멱등    : 반영 누락   0건, 중복 반영   0건
```

- 관찰 1: 이중 쓰기는 커밋과 발행 사이 크래시만큼(87건) 잃었다. 아웃박스는 유실 0이지만 **중복 89건**을 만들었다. 칸 1을 닫으면 칸 4의 짐(중복 흡수)이 늘어난다 — 칸은 서로 이어져 있다.
- 관찰 2: 커밋 위치는 유실과 중복을 맞바꾼다(누락 88 ↔ 중복 88). 멱등을 더해야 둘 다 0이다.
- 숫자는 seed에 따라 달라진다. seed 1~5로 다시 돌리면 이중 쓰기 유실 84~107, 아웃박스 중복 90~107, 처리 전 커밋 누락·처리 후 커밋 중복 87~104였다. 누락과 중복이 같은 수(88 ↔ 88)로 나온 것은 두 모드에 같은 난수 순서를 줬기 때문이다. 0인 칸(아웃박스 유실, 처리 후 커밋 + 멱등의 누락·중복)은 다섯 번 모두 0이었다.
- 관찰 3: 한 칸만 점검했다면 "아웃박스로 유실 0, 끝"이라고 답했을 것이다. 소비 쪽 89건 중복은 칸 4를 물어야 보인다. 원본이 말한 "반쪽 답"이 숫자로 보인다.

### 4. 점검표를 키우고 다듬는 규칙

SRE 27장(LCE 팀)의 출시 점검표 운영 규칙이다.

- 질문마다 **할 일(action item)**과 방법 링크를 붙인다. 예: "영속 데이터를 저장하나? → 백업을 구현하라, 방법은 여기."
- **질문의 중요성은 근거로 입증한다. 이상적으로는 과거 출시 사고로.** 할 일은 구체적이고 개발자가 할 수 있어야 한다.
- 점검표는 무한히 길어지기 쉽다. 한때 Google은 새 질문 추가에 부사장 승인을 요구했다. 1년에 한두 번 전체를 다시 보고 낡은 항목을 지운다.
- 공용 인프라로 수렴시키면 점검표가 짧아진다. 긴 레이트 리밋 요구 항목이 "시스템 X로 레이트 리밋을 구현하라" 한 줄이 됐다.

이것이 ⚠ 칸("점검 없이 출시 → 알려진 실패 모드 재발")과 이어지는 고리다. 사고 → 카탈로그 항목 → 점검 질문 → 할 일 → 공용 장치.

## 쓰이는 자료구조·알고리즘

- **그래프 순회** — 요청 경로를 노드(서비스·저장소)와 간선(호출·쓰기·발행)의 그래프로 두고 간선을 하나씩 방문한다. 점검 = 모든 간선 × 질문 6개의 표 채우기.
- **2차원 표(경계 × 질문)** — 빈칸이 곧 미점검 항목이다. 칸마다 상태(막음·열어 둠·해당 없음)를 둔다.
- **오프셋(단조 증가 위치)** — 소비 위치 기록. 커밋이 처리보다 앞서면 유실, 뒤면 중복(실험).
- **집합 기반 중복 제거** — 처리한 이벤트 ID 집합(DB에서는 유니크 인덱스). [database/08-btree-indexes](../../database/08-btree-indexes/2-summary.md).
- **아웃박스 = 같은 트랜잭션 안의 큐 테이블** — [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md), [distributed/29-outbox-vs-dispatch-log](../../distributed/29-outbox-vs-dispatch-log/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 출시 전 점검 순서

1. 질문을 받거나 리뷰를 시작하면 먼저 범위를 한 문장으로 되짚는다: "어느 경계(칸) 이야기인가, 전 구간인가?"(원본 되짚기 습관)
2. 경로 그림을 그리고 경계에 번호를 붙인다.
3. 경계 × Q1~Q6 표를 만든다. 칸마다 장치 이름 + 위치(코드·스키마·설정 파일)를 적는다.
4. 장치가 실제로 있는지 확인한다(설정값 조회, 스키마 제약 조회, 테스트).
5. 열어 두는 칸은 이유와 감수하는 결과를 적는다("알림 중복은 사용자 영향이 작아 허용").
6. 사고가 나면 회고에서 빠졌던 질문을 점검표에 추가하고, 근거로 그 사고를 링크한다(SRE 27장 규칙).

### 2. 점검 결과를 코드로 남기기 (Java)

```java
/** 경계 × 질문 점검표. 빈칸(UNCHECKED)이 남으면 출시 검사에서 실패시킨다. */
enum Q { SLOW, FAIL, UNKNOWN, DUP_ORDER, CAPACITY, DETECT }
enum Status { GUARDED, ACCEPTED_OPEN, NOT_APPLICABLE, UNCHECKED }
record Cell(String boundary, Q question, Status status, String guardOrReason) {}

static List<Cell> gaps(List<Cell> table) {
    return table.stream()
        .filter(c -> c.status() == Status.UNCHECKED
                  || (c.status() == Status.GUARDED && c.guardOrReason().isBlank()))   // 장치 이름 없는 "막음"은 빈칸
        .toList();
}
```

### 3. 칸별 확인 명령 (예)

```bash
# 칸 3: 토픽의 복제·ISR 설정 확인 (Kafka CLI)
kafka-configs.sh --bootstrap-server localhost:9092 --entity-type topics --entity-name orders --describe --all \
  | grep -E 'min.insync.replicas|unclean.leader.election.enable|retention.ms'
# 칸 4: 소비자 그룹 지연
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group point-consumer
```

```sql
-- 칸 4·5: 처리 기록 테이블에 유니크 제약이 있는가 (PostgreSQL)
SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'inbox'::regclass;
```

## 장애 시나리오와 대처

### 1. 점검 없이 출시 → 알려진 실패 모드 재발 (⚠ 커리큘럼)

- 현상: 작년에 회고까지 쓴 사고(예: 소비자 재시작 뒤 중복 지급)가 새 기능에서 똑같이 난다.
- 보이는 형태: 회고 문서에는 원인과 대책이 있다. 새 기능 설계 문서에는 그 질문이 없다.
- 원인: 회고의 교훈이 점검 절차로 옮겨지지 않았다. 사람의 기억에 기댔다.
- 대처: 사고 → 카탈로그 항목 → 점검 질문 + 할 일로 옮긴다. 질문의 근거로 사고를 링크한다(SRE 27장). 출시 검사에서 빈칸을 막는다(위 코드).

### 2. 한 칸만 닫고 "해결"이라고 보고

- 현상: "아웃박스를 넣어 유실을 막았다" 뒤 중복 지급 사고.
- 보이는 형태: 발행 쪽 유실은 0, 소비 쪽 중복 처리 로그가 있다. 실험: 아웃박스 유실 0·중복 89.
- 원인: 칸 1을 닫으며 생긴 중복을 칸 4가 흡수하지 않았다.
- 대처: 5칸을 끝까지 훑는다. 칸 1에 아웃박스를 두면 칸 4에 멱등을 함께 둔다.

### 3. 커밋 위치를 잘못 잡아 조용히 누락

- 현상: 하루에 몇 건씩 적립이 빠진다. 에러 로그 없음.
- 보이는 형태: 소비자 재시작·리밸런스 시각에 누락이 몰린다. 처리를 별도 스레드 풀로 넘기는 구조.
- 원인: 처리 완료 전에 오프셋이 커밋됐다(수동 처리 전 커밋, 또는 자동 커밋 + 비동기 처리 — Kafka Javadoc의 조건). 실험: 처리 전 커밋 누락 88건.
- 대처: 처리 후 커밋 + 멱등(이벤트 ID 기록과 적립을 같은 DB 트랜잭션으로 커밋한 뒤 오프셋 커밋). 비동기 처리라면 처리 완료된 오프셋까지만 수동 커밋.

### 4. 기본값을 확인하지 않은 칸

- 현상: 브로커 한 대 장애 뒤 일부 메시지가 사라졌다.
- 보이는 형태: 해당 파티션이 복제본 하나로 쓰기를 받고 있었다. `min.insync.replicas`가 1.
- 원인: Kafka 4.1 기본값 `min.insync.replicas=1`. `acks=all`만 보고 칸 3을 닫았다고 판단했다. Kafka 설계 문서의 예처럼, 복제본 하나만 ISR에 남은 상태에서 받은 쓰기는 그 마지막 복제본마저 고장 나면 사라질 수 있다("these writes could be lost if the remaining replica also fails"). 기본값 `unclean.leader.election.enable=false`에서는 그 복제본이 일시 장애일 때 유실 대신 파티션이 멈추고, 디스크를 잃는 등 영구 고장이면 (다른 복제본이 받아 두지 않은 범위가) 유실될 수 있다.
- 대처: 칸 3 질문에 "min.insync.replicas는 몇인가(복제 수와 함께)"를 넣고, 설정 조회 명령 결과를 점검 기록에 붙인다.

### 5. 점검표가 너무 길어 아무도 안 읽는다

- 현상: 질문 200개짜리 점검표를 형식적으로 "예"만 체크한다.
- 보이는 형태: 모든 칸이 체크됐는데 장치 이름·위치 칸이 비어 있다.
- 원인: 근거 없는 질문이 쌓였고, 할 일이 구체적이지 않다. SRE 27장은 부담이 큰 절차는 우회된다고 적는다.
- 대처: 질문마다 근거(사고)를 요구하고, 낡은 질문을 주기적으로 지운다. 공용 장치로 여러 질문을 한 줄로 바꾼다.

## 핵심 문장

- 실패는 경계에서 생긴다. 점검은 경계를 빠짐없이 나열하는 데서 시작한다.
- 경계마다 느림·실패·모름·중복과 순서·용량·알기 여섯 질문을 묻고, 답은 장치 이름으로 받는다.
- 칸은 서로 이어져 있다. 실험에서 아웃박스는 유실 0을 주는 대신 중복 89를 만들었고, 그 짐은 소비 쪽 멱등이 받아야 했다.
- 커밋 위치는 유실과 중복을 맞바꾼다(누락 88 ↔ 중복 88). 멱등을 더해야 둘 다 0이다.
- 점검표 질문은 사고로 근거를 대고, 할 일은 구체적으로 쓰며, 주기적으로 줄인다(SRE 27장).

## 관련 주제·근거

- 선행
  - [04-failure-modes-catalog](../04-failure-modes-catalog/2-summary.md) — 질문의 근거가 되는 실패 목록
  - 원본 [engineering/failure-point-checklist](../../engineering/failure-point-checklist/2-summary.md) — 5칸 표와 되짚기 습관
- 후속·연결
  - [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md), [distributed/17-queues-logs-and-delivery-semantics](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md), [distributed/18-consumer-failure-handling](../../distributed/18-consumer-failure-handling/2-summary.md), [distributed/21-kafka-internals](../../distributed/21-kafka-internals/2-summary.md) — 칸 1~5의 원리
  - [distributed/03-partial-failure-and-timeouts](../../distributed/03-partial-failure-and-timeouts/2-summary.md) — Q1·Q3
  - [44-runbooks-and-operational-readiness](../44-runbooks-and-operational-readiness/2-summary.md) — 출시 준비도 점검
- 책·문서
  - Google 『Site Reliability Engineering』 27장 "Reliable Product Launches at Scale" — LCE, The Launch Checklist(질문 + 할 일, 근거는 과거 출시 사고, 부사장 승인, 공용 인프라로 수렴) <https://sre.google/sre-book/reliable-product-launches/>, 부록 E "Launch Coordination Checklist"(2005년경 원본 요약 — 장애 시 무슨 일이 생기나, 백엔드별 타임아웃·재시도·오류 처리) <https://sre.google/sre-book/launch-checklist/>
  - Apache Kafka 4.1 Configuration — Producer(`acks` 기본 all, `enable.idempotence`), Topic(`min.insync.replicas` 기본 1, `unclean.leader.election.enable` 기본 false, `retention.ms` 기본 604800000), Consumer(`enable.auto.commit` 기본 true) <https://kafka.apache.org/41/configuration/>
  - Apache Kafka `clients/src/main/java/org/apache/kafka/clients/consumer/KafkaConsumer.java`(4.1 브랜치) Javadoc — 자동 커밋과 at-least-once의 조건
  - Apache Kafka 문서 Design 「Availability and Durability Guarantees」(4.1 브랜치 `docs/design/design.md`) — 복제본 하나만 남은 상태의 `acks=all` 쓰기, unclean 선출 금지와 최소 ISR의 맞바꿈 <https://kafka.apache.org/41/design/design/>
- 실험 목록
  - e27 발행 전(이중 쓰기 vs 아웃박스)·소비 중(처리 전/후 커밋, 멱등) 크래시 주입 시뮬레이션 — JDK 21, `scratchpad/rel/01/e27/Pipeline.java`(실제 브로커 아님)
