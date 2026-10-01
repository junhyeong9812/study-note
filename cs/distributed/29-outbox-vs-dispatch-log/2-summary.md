# distributed/29-outbox-vs-dispatch-log — outbox와 dispatch log의 경계: 저장 시점이 닫는 실패 — 정리 (힌트)

## 해결하는 문제

DB 커밋과 브로커 발행은 원자적으로 묶이지 않는다(16). 이때 "발행 기록 표"를 두는 방법이 둘 있다. 표 모양은 비슷한데 **기록하는 시점**이 다르다.

```text
  outbox:        BEGIN  업무 변경 + outbox INSERT  COMMIT  →  (릴레이) 발행 → 표시
                         └─────── 같은 트랜잭션 ───────┘
  dispatch log:  BEGIN  업무 변경  COMMIT  →  발행  →  dispatch_log INSERT
                                        † 여기서 죽으면 흔적이 없다
```

- *dispatch log(발송 로그)*: 브로커에 보낸 **뒤** "보냈음"을 기록하는 표. 사후 추적·대조용이다.
- outbox는 "보낼 것"을 업무 변경과 **함께** 기록해 유실을 닫는다. dispatch log는 "보낸 것"을 **나중에** 기록해서 커밋과 발행 사이의 유실 창이 열려 있다.
- 두 표를 같은 것으로 착각하면 사고가 난다. dispatch log를 outbox처럼 믿으면 **누락**이 남고, outbox 릴레이를 dispatch log처럼 느슨하게 만들면 **재발행 폭주**가 난다(커리큘럼 ⚠).

쉬운 예: 가게가 택배를 부친다.
- outbox: 판매 장부의 같은 줄에 "택배 보낼 것"을 함께 적는다. 직원이 그 목록을 보고 부친다. 판매가 남았으면 지시도 남는다.
- dispatch log: 먼저 택배를 부치고, "부쳤음"을 나중에 적는다. 부치러 가다 쓰러지면 그 건은 흔적이 없다.

똑같은 구조다. 실무 예: 주문 상태 변경 이벤트, 포인트 적립 사건, 검색 인덱스 동기화, 외부 파트너 웹훅.

기초(두 패턴 비교표, 상태형·사건형 구분, outbox를 다른 저장소에 두면 안 되는 이유, 폴링 vs CDC)는 원본 [systems/outbox-vs-dispatch-log](../../systems/outbox-vs-dispatch-log/2-summary.md)에 있다. 이 노트는 실제 실험으로 "대조 배치가 메우는 것과 못 메우는 것"을 보이고, 역할 혼동의 두 장애를 정리한다.

## 동작·원리

### 1. 어느 실패를 닫나

```text
  실패 지점                         outbox                     dispatch log
  ① 업무 커밋 전 죽음                둘 다 없음 (무해)            둘 다 없음 (무해)
  ② 업무 커밋 후, 발행 전 죽음        outbox 행이 남음 → 릴레이 발행  발행 없음·로그 없음 → 유실
  ③ 발행 후, 표시/로그 전 죽음        다시 발행 → 중복              로그 없음 → 대조 배치가 재발행 → 중복
```

- outbox: ②를 닫는다. ③에서 중복이 남는다(at-least-once).
- dispatch log: ②가 열려 있다. 실시간 경로는 best-effort다. ③도 중복이 된다.
  - *best-effort*: 되도록 전달하지만 유실이 없다고 약속하지 않는 등급.

### 2. 대조 배치 — dispatch log의 유실 창을 메우는 방법과 그 조건

```text
  실시간 경로:  원천 변경 → 발행 시도 → dispatch_log 기록      (유실 가능)
  보정 경로:    배치 → 원천의 "현재 상태" 전량 스캔 → 로그와 대조 → 없는 것 재발행 + 기록
```

- *대조 배치(reconciliation batch)*: 원천의 현재 상태와 발행 기록을 비교해, 나갔어야 하는데 안 나간 것을 다시 내보내는 주기 작업.
- 원본이 정리한 성립 조건 두 가지
  1. 이벤트를 **원천의 현재 상태에서 다시 만들 수 있어야** 한다(*상태형* 이벤트: "주문 상태 = SHIPPED").
  2. 배치 주기만큼의 지연을 허용해야 한다.
- *사건형* 이벤트("주문이 승인됨" 같은 일어난 사실)는 다시 만들 수 없다. `PENDING → APPROVED → SHIPPED`가 빠르게 지나가면 배치는 `SHIPPED`만 본다. `APPROVED`가 있었다는 사실이 원천에 남지 않는다.

### 실험: dispatch log + 대조 배치 vs outbox

- 환경: 전용 일회용 PostgreSQL 17.11 + Kafka 4.1.0(KRaft 단일 노드, 파티션 1), Java 21. 2026-10-01.
- 주문 100건이 각각 `PENDING → APPROVED → SHIPPED`로 전이한다. 전이마다 업무 트랜잭션 하나.
- 크래시 주입: 같은 JVM 안에서 그 줄 이후 동작을 건너뛰어, 그 지점에서 프로세스가 죽은 것과 같은 결과를 만든다(16번 실험은 진짜 프로세스 종료로 같은 지점을 보였다).
  - id 끝자리 0의 `APPROVED`: 커밋 후·발행 전(중간 전이 유실)
  - id 끝자리 3의 `SHIPPED`: 커밋 후·발행 전(마지막 전이 유실)
  - id 끝자리 5의 `SHIPPED`: 발행 후·로그 전
- 소비자 두 종류로 토픽을 읽는다.
  - 상태형 소비자: 주문별 마지막 상태를 유지한다(검색 인덱스·조회 뷰). 원천과 다른 주문 수를 센다.
  - 사건형 소비자: `APPROVED` 사건마다 무언가를 한다(승인 알림·포인트 적립). 받은 `APPROVED` 수를 센다.

```java
// dispatch log 쪽 실시간 경로
c.commit();                                                         // 업무 커밋
if (id % 10 == 0 && s.equals("APPROVED")) continue;                // †커밋 후 발행 전 (중간 전이)
if (id % 10 == 3 && s.equals("SHIPPED")) continue;                 // †커밋 후 발행 전 (마지막 전이)
pr.send(new ProducerRecord<>(topic, "" + id, id + ":" + s)).get();  // 발행
if (id % 10 == 5 && s.equals("SHIPPED")) continue;                 // †발행 후 로그 전
st.executeUpdate("insert into dispatch_log(order_id, status) values (" + id + ", '" + s + "')");

// 대조 배치: 현재 상태에 해당하는 로그가 없으면 재발행 + 기록
"select o.id, o.status from orders29 o where not exists " +
"(select 1 from dispatch_log d where d.order_id=o.id and d.status=o.status)"
```

(실험, PostgreSQL 17.11 + Kafka 4.1.0, 2026-10-01)

```text
=== dispatch log (발행 후 기록) + 대조 배치 2회
[실시간 경로 직후] 메시지 280(서로 다른 280) | 상태형 소비자: 원천과 다른 주문 10/100 | 사건형 소비자: APPROVED 사건 90/100
대조 배치 1회차: 재발행 20건
[대조 배치 1회차 뒤] 메시지 300(서로 다른 290) | 상태형 소비자: 원천과 다른 주문 0/100 | 사건형 소비자: APPROVED 사건 90/100
대조 배치 2회차: 재발행 0건
[대조 배치 2회차 뒤] 메시지 300(서로 다른 290) | 상태형 소비자: 원천과 다른 주문 0/100 | 사건형 소비자: APPROVED 사건 90/100
=== outbox (같은 트랜잭션에 기록 → 릴레이)
[실시간 경로 직후] 메시지 300(서로 다른 300) | 상태형 소비자: 원천과 다른 주문 0/100 | 사건형 소비자: APPROVED 사건 100/100
```

- 실시간 경로 직후: 메시지 20건이 빠졌다(280). 상태형 소비자는 10건이 틀렸다(끝자리 3 — 마지막 전이 유실). 끝자리 0은 `APPROVED`가 빠졌지만 `SHIPPED`가 나가서 상태형 소비자에게는 맞아 보인다.
- 대조 배치 1회차: 20건을 재발행했다.
  - 끝자리 3의 `SHIPPED` 10건 → 상태형 소비자 0/100으로 **복구**.
  - 끝자리 5의 `SHIPPED` 10건 → 이미 나간 것을 또 보냈다. 메시지 300, 서로 다른 290 = **중복 10**.
- 사건형 소비자는 끝까지 90/100이다. 배치는 현재 상태(`SHIPPED`)만 보므로 끝자리 0의 `APPROVED` 10건을 **알아챌 방법이 없다.**
- 2회차 재발행 0: 배치가 재발행하면서 로그도 썼기 때문에 수렴했다.
- outbox: 300건 전부, `APPROVED` 100/100. 같은 크래시 지점에서도 outbox 행이 남아 있으니 릴레이가 보낸다(16번 실험 A·B).

### 3. 역할 혼동의 두 방향

```text
  dispatch log를 outbox로 착각  → "로그가 있으니 유실은 없다"   → 사건형 이벤트 누락 (위 실험: APPROVED 10건)
  outbox 릴레이를 느슨하게      → 표시를 배치 끝에 몰아서, 같은 지점에서 반복 크래시
                                → 같은 앞부분만 계속 재발행    → 재발행 폭주 (16번 실험: 658건 중 서로 다른 7건)
  대조 배치가 로그를 안 쓰면    → 매 회차 같은 건을 재발행      → 주기마다 중복 폭주
```

- 마지막 줄은 위 실험의 반대 조건이다. 실험의 배치는 재발행과 함께 로그를 써서 2회차에 0건이 됐다. 로그 쓰기가 실패하거나 빠지면 매 회차가 같은 건을 다시 보낸다.

## 쓰이는 자료구조·알고리즘

- **append-only 기록 표 두 종류** — outbox(보낼 것, 업무 트랜잭션과 함께)와 dispatch log(보낸 것, 발행 뒤). 모양은 같고 쓰는 시점이 다르다.
- **집합 차(anti-join)** — 대조 배치의 핵심. "원천 현재 상태 − 발행 기록"을 `NOT EXISTS`로 구한다. 원천이 커지면 전량 스캔이라 비용이 커진다.
- **상태 vs 이벤트 로그** — 상태형 이벤트는 현재 상태의 함수라 다시 계산할 수 있다. 사건형 이벤트는 상태 변화의 기록이라, 이벤트 로그(outbox·이벤트 소싱)에만 남는다. [ops-patterns/16-event-sourcing](../../ops-patterns/16-event-sourcing/2-summary.md)
- **멱등 소비(이벤트 id 집합)** — 두 방식 모두 중복을 남기므로 소비자 쪽에 필요하다. [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 어느 쪽을 고르나

```text
  이벤트가 "일어난 사실"(승인됨·사용됨·차감됨)인가? ── 예 ──> outbox (필수)
          │ 아니오 (상태 동기화: 검색 인덱스, 조회 뷰, 캐시)
  배치 주기만큼의 지연을 허용하나? ──────────────── 아니오 ──> outbox
          │ 예
  dispatch log + 대조 배치 (단, 배치는 재발행과 기록을 함께, 소비자는 멱등)
```

- 두 질문의 답을 파이프라인 설계 근거로 남긴다(원본 「현장에서 만나는 상황」).
- 한 서비스 안에서도 이벤트마다 다를 수 있다. "주문 상태 동기화"는 dispatch log로 충분해도 "포인트 적립 사건"은 outbox가 필요하다.

### 2. 진단 질의

```sql
-- dispatch log 쪽: 원천 현재 상태 중 발행 기록이 없는 것 (대조 배치가 볼 것)
SELECT o.id, o.status FROM orders o
WHERE NOT EXISTS (SELECT 1 FROM dispatch_log d WHERE d.order_id = o.id AND d.status = o.status);

-- 같은 (주문, 상태)가 여러 번 기록됐나 = 중복 재발행
SELECT order_id, status, count(*) FROM dispatch_log GROUP BY 1, 2 HAVING count(*) > 1;

-- outbox 쪽: 진행이 멈췄나
SELECT count(*), now() - min(created_at) FROM outbox WHERE published_at IS NULL;
```

- 대조 배치 결과(회차별 재발행 건수)를 지표로 남긴다. 평소 0에 가깝다가 튀면 실시간 경로가 깨진 것이다. 매 회차 같은 수가 반복되면 배치의 기록 쓰기가 깨진 것이다.

## 장애 시나리오와 대처

### 1. dispatch log를 믿어 사건형 이벤트가 누락된다 (커리큘럼 ⚠ — 누락)

- **현상**: 일부 고객에게 승인 알림이 오지 않았고 포인트도 적립되지 않았다. 주문 상태는 정상(`SHIPPED`)이다.
- **보이는 형태**: 대조 배치는 "재발행 0건"을 보고한다. 사건형 소비자의 처리 건수가 원천의 승인 건수보다 적다(실험: 90/100).
- **원인**: 커밋 후 발행 전 유실. 대조 배치는 현재 상태만 보므로 지나간 중간 전이(`APPROVED`)를 찾지 못한다.
- **대처**: 사건형 이벤트는 outbox로 옮긴다. 이미 빠진 건은 감사 로그·DB 이력 표 등 다른 원천에서 찾아 수동 보정한다(원천에 흔적이 없으면 복구할 수 없다).

### 2. 릴레이·배치가 같은 건을 계속 재발행한다 (커리큘럼 ⚠ — 재발행 폭주)

- **현상**: 토픽 메시지 수가 급증하고 소비자 부하가 오른다. 실제 새 이벤트는 거의 없다.
- **보이는 형태**: 같은 페이로드가 반복된다. 16번 실험: 릴레이 94회 재시작에 658건, 서로 다른 것은 7건. 대조 배치라면 회차마다 같은 재발행 건수.
- **원인**
  - outbox 릴레이가 표시를 큰 배치 끝에 몰아서 커밋하고, 배치 중간 같은 지점에서 반복해 죽는다.
  - 대조 배치가 재발행 후 기록을 남기지 않는다(쓰기 실패, 다른 키로 기록 등).
- **대처**: 표시·기록을 작은 단위로 커밋한다. 반복 실패 건을 격리한다. 재발행 건수가 회차마다 같으면 알람.

### 3. 대조 배치의 재발행이 중복을 만든다

- **현상**: 배치가 돈 직후 같은 상태 이벤트가 두 번 처리된다.
- **보이는 형태**: 실험 1회차에서 메시지 300건 중 서로 다른 것 290 — 이미 나간 `SHIPPED` 10건이 다시 나갔다.
- **원인**: "발행 후 로그 전" 크래시. 로그가 없으니 배치는 안 나간 것으로 본다.
- **대처**: 소비자 멱등. 상태형이면 "같은 상태를 다시 적용해도 결과가 같게"(상태 덮어쓰기 + 버전 비교) 만든다.

### 4. 원천이 커져 대조 배치가 주기 안에 끝나지 않는다

- **현상**: 배치가 겹쳐 돌고 DB 부하가 오른다. 복구 지연(배치 주기)이 계속 늘어난다.
- **보이는 형태**: 배치 실행 시간 > 배치 주기. 대조 질의가 원천 전량 스캔.
- **원인**: 원본이 짚은 비용 — 대조 배치는 원천 전량 스캔이라 데이터가 커질수록 무거워진다.
- **대처**: 변경 시각 인덱스로 최근 변경분만 대조한다. 그래도 커지면 outbox(또는 CDC)로 옮긴다.

## 핵심 문장

- 기록하는 시점이 닫는 실패를 정한다. 업무 변경과 함께 쓰면(outbox) 유실이 닫히고, 보낸 뒤 쓰면(dispatch log) 유실 창이 남는다.
- 대조 배치는 원천의 현재 상태에서 다시 만들 수 있는 상태형 이벤트만 메운다. 지나간 중간 전이 같은 사건형 이벤트는 못 메운다.
- 두 방식 모두 중복을 남긴다. 소비자 멱등은 어느 쪽을 골라도 필요하다.
- 역할을 혼동하면 dispatch log에서는 누락이, 느슨한 릴레이·배치에서는 재발행 폭주가 생긴다.

## 관련 주제·근거

- 선행
  - [16-outbox-and-dual-write](../16-outbox-and-dual-write/2-summary.md) — 이중 쓰기, outbox, 릴레이 크래시·재발행 폭주 실험
  - 원본 [systems/outbox-vs-dispatch-log](../../systems/outbox-vs-dispatch-log/2-summary.md) — 비교표, 상태형·사건형, 성립 조건 두 가지, outbox를 다른 저장소에 두면 안 되는 이유
- 연결
  - [ops-patterns/07-outbox](../../ops-patterns/07-outbox/2-summary.md) · [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md) · [ops-patterns/16-event-sourcing](../../ops-patterns/16-event-sourcing/2-summary.md)
  - [22-event-sourcing](../22-event-sourcing/2-summary.md) — 사건을 원천으로 두는 방식
- 근거
  - 원고: `jun-bank/docs/study/notes/06-outbox-vs-dispatch-log.md`(원본 노트 출처 표기 그대로)
  - microservices.io "Pattern: Transactional outbox" — 커밋될 때만 발행, 릴레이 중복 <https://microservices.io/patterns/data/transactional-outbox.html>
- 실험 목록
  - `DispatchExp.java` + `exp29.sh` — 전용 PostgreSQL 17.11 + Kafka 4.1.0, Java 21. 주문 100건 × 전이 3개, 크래시 주입 3종. dispatch log: 실시간 280건·상태 틀림 10·APPROVED 90 → 배치 1회차 재발행 20(상태 0 틀림, 중복 10, APPROVED 여전히 90) → 2회차 0. outbox: 300건, APPROVED 100.
