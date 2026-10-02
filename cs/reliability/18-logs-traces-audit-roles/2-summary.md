# reliability/18-logs-traces-audit-roles — 운영 로그·지표·추적·감사/업무 기록의 역할 구분 — 정리 (힌트)

## 해결하는 문제

"관리자 admin7이 주문 1042를 39,000원 환불했다." 이 사건 하나를 어디에 남겨야 할까?\
운영 로그에만 남기면 14일 뒤 보존 기한과 함께 사라진다. 장애 중 로그 레벨을 올리면 그 자리에서 버려진다. 트레이스에만 남기면 샘플링으로 빠진다.\
반대로 디버깅용 줄까지 감사 저장소에 넣으면 비용이 커지고, 정말 봐야 할 기록이 묻힌다.

```text
 같은 사건, 네 가지 기록
 ┌ 운영 로그   "refund approved id=1042 ..."      → 디버깅용. 버려도 된다(샘플링·레벨·14일 보존)
 ├ 지표        refunds_total{result="ok"} += 1    → 개수·비율. 개별 사건은 없다
 ├ 추적        span "POST /refunds" 1.2s          → 이 요청의 경로·지연. 샘플링된다
 └ 감사·업무   audit_log(seq, at, actor, action, detail, prev_hash)
                                                  → 버리면 안 된다. 보존 기한·변경 금지·접근 통제
```

- 기록마다 **버려도 되는가**가 다르다. 그 성질에 맞는 저장 경로를 골라야 한다.
- *감사 기록(audit trail)*: 누가, 언제, 무엇을, 어떤 대상에 했는지의 기록. 나중에 책임·규정 준수·분쟁을 확인하는 근거다.
- *업무 기록*: 업무 상태 자체의 기록. 원장, 주문 상태 이력, 환불 내역. 시스템이 맞게 동작하려면 있어야 하는 데이터다.

쉬운 예: 가게다. CCTV(운영 로그)는 30일마다 덮어쓴다. 계산대 위 "오늘 손님 수" 판(지표)은 숫자만 있다. 영수증 원장(업무 기록)과 금고 열람 장부(감사 기록)는 법이 정한 기간 동안 보관하고 고쳐 쓰지 않는다.\
똑같은 구조다.\
실무 예: 결제 서비스. 디버깅 로그는 샘플링하고 짧게 보관한다. 환불 승인은 환불 행과 **같은 DB 트랜잭션**으로 감사 테이블에 쓰고, 그 테이블은 앱이 고치거나 지울 수 없게 한다.

## 동작·원리

### 1. 네 기록의 성질 비교

| | 운영 로그 | 지표 | 추적(트레이스) | 감사·업무 기록 |
|---|---|---|---|---|
| 답하는 질문 | 무슨 일이 있었나(맥락) | 얼마나 자주·얼마나 오래 | 이 요청은 어디를 거쳐 어디서 느렸나 | 누가 무엇을 했나 / 업무 상태는 무엇인가 |
| 단위 | 사건 줄 | 집계된 숫자 | 요청 하나의 스팬 트리 | 업무 사건 하나 |
| 버려도 되나 | 된다(샘플링·레벨·드롭) | 개별 사건이 원래 없다 | 된다(대부분 샘플링) | **안 된다** |
| 보존 | 짧다(예: 7~30일, 예시) | 해상도를 낮춰 길게 | 짧다(예시: 며칠) | 규정·계약이 정한 기간 |
| 변경 | 신경 쓰지 않음 | — | — | 추가만. 고침·삭제는 탐지되거나 막혀야 |
| 쓰기 경로 | 비동기·유실 허용 가능(15) | 메모리 카운터 | SDK → 수집기(드롭 가능) | 동기, 업무 트랜잭션과 함께 |
| 읽는 사람 | 개발·운영 | 운영·경보 | 개발·운영 | 감사·법무·고객 지원·회계 |

- OpenTelemetry는 수집 대상 신호(signal)로 Traces·Metrics·Logs·Baggage를 둔다(Profiles·Events는 개발·제안 단계, OTel 문서 "Signals" 2026-10-01 열람). **감사 기록은 이 목록에 없다.** 텔레메트리 파이프라인은 운영 관측용이고, 감사의 보존·변경 금지 요구를 기본으로 주지 않는다.
- Log4j 2 문서("Asynchronous loggers" Trade-offs)도 같은 판단이다: 로깅이 업무 로직의 일부라면(예: 감사 로깅) 그 메시지는 **동기로** 기록하라고 권한다.
- OWASP Logging Cheat Sheet는 로그 용도 목록에 감사 추적·업무 과정 모니터링을 함께 넣는다. 그러면서 보호 요구를 따로 적는다: 변조 탐지를 넣어 기록이 고쳐지거나 지워진 것을 알 수 있게 하고, 보존 기한 전에 파기하지 말며 기한을 넘겨 두지도 말라.

### 2. 판정 — "이 사건은 어디에 남겨야 하나"

```text
 이 사건을 잃으면 돈·법·분쟁·보안 조사에 문제가 생기나?
   ├ 예 → 감사·업무 기록
   │      업무 트랜잭션과 같이 커밋 (또는 같은 트랜잭션의 outbox)
   │      추가만 허용 · 변조 탐지 · 보존 기한 · 접근 통제 · 샘플링 금지
   └ 아니오
        ├ 개수·비율·분포만 필요한가? → 지표 (16)
        ├ 요청 하나의 경로·지연·인과가 필요한가? → 추적 (17)
        └ 디버깅 맥락(입력값·분기·예외)이 필요한가? → 운영 로그 (15)
 한 사건이 여러 곳에 갈 수 있다: 환불 승인 = 감사 기록 1행 + refunds_total +1 + 스팬 속성 + (선택) 로그 1줄
```

- 핵심은 **잃어도 되는 경로와 잃으면 안 되는 경로를 섞지 않는 것**이다. 같은 로거·같은 수집 파이프라인에 섞으면, 운영 쪽의 정상적인 조치(레벨 상향·샘플링·보존 단축·큐 포화 시 드롭)가 업무 기록을 지운다.

### 3. 실험: 로그 레벨을 올리자 업무 사건이 사라진다

- 같은 "환불 승인" 사건 100건을 운영 로거(`com.shop.refund`, INFO)와 별도 감사 로거(`AUDIT`, additivity false)에 각각 남겼다.
- 장애 중 "로그가 너무 많다"는 이유로 운영 로거를 WARN으로 올리는 상황을 흉내 냈다.

(실험, JDK 21.0.12 temurin + Logback 1.5.18 `ListAppender`, `--cpus=2`, 2026-10-01)

```text
앱 로거 레벨 INFO → 운영 로그에 남은 환불 승인 100/100, 감사 채널 100/100, 운영 로그 전체 104줄
앱 로거 레벨 WARN → 운영 로그에 남은 환불 승인   0/100, 감사 채널 100/100, 운영 로그 전체 4줄
```

- 관찰: 레벨을 올리자 운영 로그의 환불 기록은 0건이 됐다. 경고도 없다. 별도 채널은 영향을 받지 않았다.
- 이 실험의 감사 "채널"도 결국 로거다. 레벨 조정에서는 분리됐지만, 같은 프로세스의 비동기 큐·수집기를 지나면 15의 실험처럼 드롭될 수 있다. 그래서 아래 §4처럼 **DB 트랜잭션 안**에 쓰는 편이 감사·업무 기록에 맞다.

### 4. 실험: 감사 테이블 — 같은 트랜잭션, 추가만 허용, 그 한계

```sql
CREATE TABLE audit_log(
  seq bigserial PRIMARY KEY, at timestamptz NOT NULL DEFAULT now(),
  actor text NOT NULL, action text NOT NULL, detail jsonb NOT NULL);
CREATE FUNCTION audit_no_change() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'audit_log is append-only (% blocked)', TG_OP; END $$;
CREATE TRIGGER audit_append_only BEFORE UPDATE OR DELETE ON audit_log
  FOR EACH ROW EXECUTE FUNCTION audit_no_change();
GRANT INSERT, SELECT ON audit_log TO app;          -- 앱 역할에는 UPDATE·DELETE 권한이 없다
GRANT USAGE ON SEQUENCE audit_log_seq_seq TO app;  -- bigserial 기본값(nextval)에 필요
```

(실험, PostgreSQL 17.11 일회용 컨테이너 `--cpus=1`, 2026-10-01 — ① 환불+감사 커밋 ② 환불+감사 후 `1/0`으로 실패해 롤백 ③ 앱 역할로 UPDATE·DELETE ④ 소유자(슈퍼유저)로 UPDATE·TRUNCATE)

```text
== 1. 환불과 감사 기록을 한 트랜잭션에 — 커밋
== 2. 같은 묶음 — 도중 실패로 롤백되면 감사 기록도 없다
ERROR:  division by zero
 seq | actor  | action |                    detail                     
-----+--------+--------+-----------------------------------------------
   1 | admin7 | REFUND | {"order": 1042, "amount": 39000, "refund": 1}
(1 row)

 id |  status  
----+----------
  1 | APPROVED
(1 row)

== 3. 앱 역할로 고치기·지우기
ERROR:  permission denied for table audit_log
ERROR:  permission denied for table audit_log
== 4. 소유자(슈퍼유저)로 UPDATE, 그리고 TRUNCATE
ERROR:  audit_log is append-only (UPDATE blocked)
CONTEXT:  PL/pgSQL function audit_no_change() line 2 at RAISE
 rows_after_truncate 
---------------------
                   0
(1 row)
```

- 관찰 1: 환불과 감사 행이 같이 커밋되고, 같이 롤백됐다. "환불은 됐는데 감사 기록이 없다"와 "감사 기록은 있는데 환불은 없다"가 둘 다 생기지 않는다.
- 관찰 2: 앱 역할은 권한에서 막혔다. 소유자의 UPDATE는 트리거가 막았다.
- 관찰 3: 그러나 **TRUNCATE는 통과해 0행이 됐다.** 행 단위 `ON DELETE` 트리거는 TRUNCATE에서 실행되지 않는다(PostgreSQL 17 문서 TRUNCATE: "will not fire any ON DELETE triggers ... But it will fire ON TRUNCATE triggers"). 소유자는 트리거를 끌 수도 있다(`ALTER TABLE ... DISABLE TRIGGER`).
- 정리: DB 권한·트리거는 **앱 계정의 실수·오용**을 막는다. 관리자 권한을 가진 쪽의 변경까지 막지는 못한다. 그것은 탐지(§5 해시 체인 + 밖에 둔 고정점)와 저장소 분리(별도 계정·WORM 저장소)로 다룬다.

### 5. 실험: 해시 체인 — 변조 탐지와 그 한계

```text
 seq1 ─hash1─▶ seq2(prev=hash1) ─hash2─▶ seq3(prev=hash2) ─hash3─▶ seq4(prev=hash3) ─hash4  ← 머리 해시
 hash_n = SHA-256(seq | at | actor | action | detail | prev)
 머리 해시를 주기적으로 "다른 곳"(별도 계정의 저장소, WORM, 외부)에 적어 둔다 = 고정점
```

- *해시 체인*: 기록마다 직전 기록의 해시를 넣고 자기 해시를 계산한다. 중간 하나의 내용만 고치면 그 행의 저장된 해시와 다시 계산한 해시가 어긋난다(아래 실험 1). 그 행 해시까지 다시 계산해 저장하면 다음 행의 `prev`가 어긋나므로, 들키지 않으려면 뒤 행을 전부 다시 계산해야 한다.
- *고정점(anchor)*: 체인 밖에 따로 둔 머리 해시. 저장소 쓰기 권한을 가진 사람이 체인을 통째로 다시 계산해도, 고정점과 비교하면 드러난다.

(실험, JDK 21.0.12 temurin, `--cpus=2`, 2026-10-01 — 해시는 보기 쉽게 SHA-256 앞 12자만 썼다)

```text
seq=1 admin7 REFUND     prev=GENESIS hash=1b4df0288a98
seq=2 admin7 ROLE_GRANT prev=1b4df0288a98 hash=00e0ac473aae
seq=3 kim EXPORT     prev=00e0ac473aae hash=aec0f1922a7b
seq=4 admin2 REFUND     prev=aec0f1922a7b hash=f4b35a1d76d4
원본 검증: OK (머리 해시 f4b35a1d76d4)
1) seq2 내용만 고침: seq 2: 해시 불일치(내용 변경)
2) seq3 삭제: 순번 끊김: 위치 3에 seq=4
3) seq3 삭제 후 전부 재계산, 고정점 없이: OK (머리 해시 1b8fe4d58851)
3) 같은 체인, 밖에 둔 고정점과 대조: 체인은 자체 일관 — 그러나 머리 해시 1b8fe4d58851 ≠ 밖에 둔 고정점 f4b35a1d76d4
```

- 관찰 1·2: 내용 변경과 중간 삭제는 체인만으로 드러났다.
- 관찰 3: 공격자가 kim의 대량 EXPORT(seq3)를 지우고 뒤를 전부 다시 계산하면 **체인 자체는 OK**다. 밖에 둔 고정점과 비교해야 드러났다.
- 해시 체인은 **막지 않고 탐지한다**. 그리고 탐지의 힘은 고정점을 얼마나 다른 신뢰 영역에 두느냐에 달려 있다.

### 6. 개인정보와 보존 — 로그에 남긴 것이 삭제 범위가 된다

- 운영 로그에 이름·이메일·주민번호를 남기면, 개인정보 삭제 요청(예: GDPR 17조 삭제권)이 왔을 때 로그 저장소·백업까지 처리 범위에 든다. 삭제권에는 법정 보존 의무 같은 예외가 있다(17조 3항). 적용되면 운영 저장소는 지우고, 바로 못 지우는 백업은 쓰지 못하게 묶어 두었다가 정해진 주기에 덮어쓰는 식으로 처리한다(영국 ICO 삭제권 지침의 백업 항목). 로그는 그런 선택적 삭제에 맞게 설계되지 않았다.
- 대처 방향
  - 운영 로그·트레이스에는 내부 ID(가명)만 남긴다. OWASP "Data to exclude" 목록을 기준으로 한다.
  - 감사 기록에 필요한 개인정보는 최소로 두고, 보존 기한이 끝나면 파기한다(OWASP: 기한 전 파기 금지, 기한 후 보관 금지).

## 쓰이는 자료구조·알고리즘

- **해시 체인** — 앞 기록의 해시를 다음 기록에 넣는 연결 리스트. 변경·삭제 탐지. 여러 기록을 한 번에 증명하려면 머클 트리로 확장한다(Certificate Transparency 로그가 그 예). [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md).
- **추가 전용 로그(append-only log)** — 감사 테이블, WAL. [database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md)(DB의 "로그"는 복구용 기록으로 운영 로그와 다르다).
- **링 버퍼·유계 큐** — 운영 로그 경로. 가득 차면 버린다(15). 감사 경로에는 두지 않는다.
- **outbox 테이블** — 업무 트랜잭션과 같이 커밋한 뒤 별도로 내보낸다. [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md).
- **보존 기한별 파티션** — 기한이 지난 파티션을 통째로 지운다. [database/29-soft-delete-and-data-lifecycle](../../database/29-soft-delete-and-data-lifecycle/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. 사건 목록을 만든다: 로그인·권한 변경·환불·데이터 내보내기·설정 변경 등. 각각에 "잃으면 무엇이 문제인가"를 적는다.
2. §2의 판정으로 저장 경로를 정한다. 감사·업무 기록은 보존 기한·접근 권한·담당자를 함께 정한다.
3. 감사 기록은 업무 트랜잭션 안에서 쓴다. 다른 시스템(SIEM 등)으로 보내야 하면 outbox로 내보낸다.
4. 앱 계정에는 INSERT(와 SELECT·시퀀스 USAGE)만 준다. UPDATE·DELETE는 주지 않는다. 해시 체인 + 주기적 고정점(별도 계정·저장소)을 둔다.
5. 운영 로그·트레이스에는 가명 ID만 남기고, 샘플링·레벨·보존을 자유롭게 조정한다.

### 2. 환불과 감사를 한 트랜잭션에 (Java, Spring + JDBC)

```java
@Transactional
public void approveRefund(long orderId, long amount, String actor) {
    long refundId = refundRepo.insert(orderId, amount, "APPROVED");
    auditRepo.lockChainHead();      // SELECT pg_advisory_xact_lock(<체인 키>) — 커밋·롤백까지 추가를 한 줄로 세운다
    String prev = auditRepo.lastHash();                       // 잠금을 얻은 뒤 머리를 읽는다
    String detail = json(Map.of("refund", refundId, "order", orderId, "amount", amount));
    Instant at = Instant.now();
    // seq(bigserial)는 INSERT 뒤에 정해지므로 이 예에서는 해시에서 빼고, 순서는 prev 연결로 묶는다(§5 그림·실험은 seq 포함)
    String hash = sha256(String.join("|", at.toString(), actor, "REFUND", detail, prev));
    auditRepo.insert(at, actor, "REFUND", detail, prev, hash);   // 실패하면 환불도 롤백
    meterRegistry.counter("refunds_total", "result", "ok").increment(); // 지표: 개수만. 커밋 전이라 롤백돼도 줄지 않는다
    log.info("refund approved refundId={}", refundId);           // 운영 로그: 버려져도 된다
}
```

- 머리 잠금을 "마지막 행 `SELECT … FOR UPDATE`"로 하면 안 된다. 기본 READ COMMITTED에서 기다리던 쪽이 풀린 뒤에도 같은 옛 머리를 읽어 둘 다 같은 `prev`로 추가한다(점검 실험, PostgreSQL 17.11: 대기 후 읽은 머리가 옛 값 그대로, 자문 잠금(advisory lock)으로는 새 머리). 첫 행일 때는 잠글 행도 없다. 또 `FOR UPDATE`는 테이블 UPDATE 권한까지 요구해 INSERT·SELECT만 받은 앱 역할로는 실행되지 않는다(실험: permission denied). 그래서 자문 잠금(또는 늘 있는 잠금 행 하나)을 쓴다.
  - *자문 잠금(advisory lock)*: 행이 아니라 앱이 정한 숫자 키에 거는 잠금. `pg_advisory_xact_lock`은 트랜잭션이 끝날 때 풀린다.
- 지표 카운터는 트랜잭션과 묶이지 않는다. "커밋된 환불 수"가 필요하면 커밋 후 콜백(Spring `TransactionSynchronization.afterCommit`)에서 올리거나 DB 기준으로 센다.
- 체인 머리를 잠그는 부분은 동시 추가가 많으면 병목이 된다. 묶음 단위 체인(구간마다 머리 해시)이나 머클 트리로 바꿀 수 있다.
- `Span.current().setAttribute("refund.id", refundId)`로 트레이스에서도 찾게 한다. 그러나 근거로는 감사 테이블만 쓴다.

### 3. 점검 명령

```sql
-- 앱 계정 권한이 INSERT·SELECT뿐인지
SELECT grantee, privilege_type FROM information_schema.role_table_grants WHERE table_name = 'audit_log';
-- 순번 구멍(삭제 흔적) — bigserial은 롤백으로도 구멍이 생기므로 해시 체인과 함께 본다
SELECT seq + 1 AS gap_start FROM audit_log a WHERE NOT EXISTS (SELECT 1 FROM audit_log b WHERE b.seq = a.seq + 1)
  AND seq < (SELECT max(seq) FROM audit_log);
```

## 장애 시나리오와 대처

### 1. 감사가 필요한 사건을 앱 로그에만 남겼다 → 보존 기한 뒤 증거가 없다

- 현상: 석 달 전 환불 분쟁이 들어왔는데, 누가 승인했는지 찾을 수 없다.
- 보이는 형태: 로그 저장소의 보존이 14일이라 해당 기간 데이터가 없다. DB의 환불 행에는 승인자 칸이 없다.
- 원인: 감사 사건을 운영 로그 경로(짧은 보존·드롭 허용)에 맡겼다.
- 대처: 감사 테이블(또는 감사 전용 저장소)로 옮기고, 보존 기한을 규정에서 정한다. 업무 행에도 최소한의 행위자·시각 칸을 둔다.

### 2. 로그 샘플링·레벨 조정이 업무 이벤트까지 버린다

- 현상: 장애 대응 중 로그 레벨을 올린 사이의 환불 기록이 없다. 정산 대사에서 건수가 맞지 않는다.
- 보이는 형태: 위 실험처럼 WARN으로 올리자 환불 승인 0/100. 경고·오류 없음.
- 원인: 업무 사건을 디버깅 로그와 같은 로거·같은 정책 아래 두었다.
- 대처: 업무·감사 사건을 운영 로그 경로에서 분리한다(DB 트랜잭션, 최소한 별도 로거 + 동기 + 드롭 없는 경로). 운영 로그는 자유롭게 줄일 수 있게 된다.

### 3. 트레이스를 감사 근거로 썼다 → head 샘플링으로 해당 요청이 없다

- 현상: "이 사용자가 이 API를 불렀나"를 트레이스에서 찾으니 없다. 그런데 DB에는 결과가 있다.
- 보이는 형태: 트레이스 비율 10% 설정(17의 실험: 에러 트레이스 212개 중 25개만 보존 — 실행마다 20~26개). 트레이스 보존 며칠.
- 원인: 트레이스는 샘플링되고 짧게 보존되는 운영 신호다.
- 대처: 감사 근거는 감사 기록에서만 찾는다. 트레이스에는 감사 행의 ID를 속성으로 달아 서로 찾아가게만 한다.

### 4. 로그에 개인정보를 남겼다 → 삭제 요청 범위가 로그까지 번진다

- 현상: 고객의 개인정보 삭제 요청(삭제권이 적용되는 경우)을 처리하려니 로그 저장소·백업·수집 파이프라인의 버퍼까지 찾아야 한다.
- 보이는 형태: 로그 줄에 이메일·전화번호·요청 본문 원문.
- 원인: 디버깅 편의로 요청 본문을 통째로 로깅했다. 객체 `toString()`에 개인정보 필드.
- 대처: 운영 로그·트레이스에는 가명 ID만(15 장애 5와 같은 마스킹 규칙). 감사 기록의 개인정보는 최소화하고 보존 기한 뒤 파기한다.

### 5. 감사 기록을 트랜잭션 밖에서 썼다 → 있어야 할 기록이 없거나, 없던 일이 기록됐다

- 현상: 환불 행은 있는데 감사 기록이 없다. 또는 감사 기록은 있는데 환불은 롤백돼 없다.
- 보이는 형태: 두 테이블(또는 DB와 외부 감사 시스템) 건수 대사 불일치. 커밋 직후 감사 전송 단계의 타임아웃 로그.
- 원인: 이중 쓰기 — 업무 커밋과 감사 쓰기가 원자적이지 않다(커밋 후 감사 전송 실패, 또는 감사 먼저 쓰고 업무 롤백).
- 대처: 같은 DB 트랜잭션에 쓴다(위 실험 ①②). 외부 시스템으로 보내야 하면 outbox로 같은 트랜잭션에 넣고 따로 전달한다.

## 핵심 문장

- 기록은 "버려도 되는가"로 나눈다. 운영 로그·지표·추적은 버려지고 샘플링되는 운영 신호이고, 감사·업무 기록은 버리면 안 된다.
- 잃어도 되는 경로와 잃으면 안 되는 경로를 섞으면, 레벨 상향·샘플링·보존 단축 같은 정상적인 운영 조치가 업무 기록을 지운다(실험: WARN 상향으로 환불 승인 0/100).
- 감사·업무 기록은 업무 트랜잭션과 같이 커밋한다. 그래야 "했는데 기록 없음"과 "안 했는데 기록 있음"이 함께 사라진다.
- DB 권한·트리거는 앱 계정의 변경을 막지만 관리자의 TRUNCATE는 막지 못했다(실험). 그 너머는 해시 체인과 밖에 둔 고정점으로 탐지한다.
- 트레이스는 감사 근거가 아니다. 로그·트레이스에는 가명 ID만 남겨 삭제 요청의 범위를 좁힌다.

## 관련 주제·근거

- 선행
  - [15-logging](../15-logging/2-summary.md) — 운영 로그의 드롭·샘플링·비동기 큐
  - [17-distributed-tracing](../17-distributed-tracing/2-summary.md) — head 샘플링
  - security/26-security-logging-and-audit — [security 영역 표](../../security/README.md)(미작성)
- 후속·연결
  - [16-metrics-and-golden-signals](../16-metrics-and-golden-signals/2-summary.md)
  - [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md) · [database/13-transactions-acid](../../database/13-transactions-acid/2-summary.md) · [database/50-temporal-and-bitemporal-tables](../../database/50-temporal-and-bitemporal-tables/2-summary.md)(변경 이력 보존)
  - [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md)
  - [26-incident-response-and-postmortem](../26-incident-response-and-postmortem/2-summary.md)
- 문서
  - OpenTelemetry "Signals"(Traces·Metrics·Logs·Baggage, Events·Profiles는 개발·제안) <https://opentelemetry.io/docs/concepts/signals/>
  - OWASP Logging Cheat Sheet — 용도(Audit trails·Business process monitoring), Data to exclude, 변조 탐지, 보존 기한 <https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html>
  - Apache Log4j 2 "Asynchronous loggers" — 감사 로깅은 동기로 권고 <https://logging.apache.org/log4j/2.x/manual/async.html>
  - PostgreSQL 17 문서 TRUNCATE(ON DELETE 트리거 미실행) <https://www.postgresql.org/docs/17/sql-truncate.html>
- 실험 목록
  - A: Logback 1.5.18 `ListAppender` — 운영 로거 INFO→WARN 상향 시 업무 사건 보존 수 vs 별도 감사 로거(JDK 21.0.12, scratchpad `rel/15/Audit18.java`)
  - B: 해시 체인 4건 — 내용 변경·삭제·전부 재계산 + 고정점 대조(같은 파일)
  - C: PostgreSQL 17.11 일회용 컨테이너 — 같은 트랜잭션 커밋/롤백, 앱 역할 권한 거부, 소유자 UPDATE 트리거 거부, TRUNCATE 통과(scratchpad `rel/15/audit18.sql`)
  - D(점검, 2026-10-02): PostgreSQL 17.11 — INSERT·SELECT만 받은 역할의 `FOR UPDATE`·시퀀스 없는 INSERT 거부, 두 트랜잭션이 마지막 행 `FOR UPDATE`로 경쟁하면 기다린 쪽이 옛 머리를 읽음 vs `pg_advisory_xact_lock`이면 새 머리를 읽음
