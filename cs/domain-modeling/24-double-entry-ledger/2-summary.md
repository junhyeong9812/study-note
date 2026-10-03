# domain-modeling/24-double-entry-ledger — 복식부기 원장: 차대 합 0, 잔액은 파생값, 정정은 역분개 — 정리 (힌트)

## 해결하는 문제

잔액을 `balance` 열 하나로 들고 `UPDATE`로만 바꾸면, 지금 숫자는 보이지만 그 숫자가 **왜** 그렇게 됐는지는 남지 않는다.

```text
  잔액 열만 있는 계좌                      원장(분개 목록)이 있는 계좌
  ┌─────────────┐                         ┌────┬──────────────┬────────┐
  │ alice 9,000 │  ← 왜 9,000인가?         │ #1 │ 충전          │ +10,000│
  └─────────────┘    어제는 얼마였나?      │ #4 │ #1 역분개     │ -10,000│
                     누가 언제 고쳤나?     │ #5 │ 충전(정정)    │  +9,000│
                     → 답할 자료가 없다    └────┴──────────────┴────────┘
                                            잔액 9,000 = 세 줄의 합 → 근거가 남는다
```

- 잔액이 틀렸다는 민원이 오면, 잔액 열만 있는 시스템은 "지금 값"밖에 보여줄 수 없다.
- 정정을 `UPDATE`·`DELETE`로 하면 틀렸던 값과 고친 흔적이 함께 사라진다.

쉬운 예: 가계부를 쓰지 않고 지갑만 세는 사람이다.
- 지갑에 9,000원이 있다는 건 안다. 하지만 어제 10,000원이 있었는지, 1,000원을 어디에 썼는지는 모른다.
- 가계부(들어온 것·나간 것의 목록)가 있으면 지갑 금액은 목록을 더해서 **다시 만들 수 있다.**

똑같은 구조다: 원장은 돈의 이동을 한 줄씩 쌓는 가계부다. 잔액은 그 줄들의 합으로 **계산되는 값**이다.

실무 예:
- 간편결제 지갑·포인트·선불 충전금 — 고객이 "내 잔액이 왜 이거냐"고 묻는다.
- 판매자 정산 — 매출·수수료·환불·지급이 한 판매자의 지급 예정액을 만든다([api-design/04-settlement-report](../../api-design/25-case-settlement-report/2-summary.md)).
- 부분 환불 — 환불이 원 결제를 고치는 게 아니라 새 이동으로 쌓인다([api-design/06-refund](../../api-design/27-case-refund/2-summary.md)).
- Square는 이 문제를 풀려고 "Books"라는 불변(immutable) 복식부기 원장 서비스를 만들었다(Square 개발자 블로그, 2019-10-16).

## 동작·원리

### 1. 이동 한 건 = 차변과 대변의 쌍

```text
  전표(journal entry) #1 "alice 충전 10,000원"
  ┌────────────────┬──────────┬──────────┐
  │ 계정(account)   │ 차변(Dr) │ 대변(Cr) │
  ├────────────────┼──────────┼──────────┤
  │ cash(현금)      │  10,000  │          │   ← 회사가 가진 돈이 늘었다
  │ wallet:alice    │          │  10,000  │   ← 회사가 alice에게 줄 돈(부채)이 늘었다
  ├────────────────┼──────────┼──────────┤
  │ 합             │  10,000  │  10,000  │   차변 합 = 대변 합
  └────────────────┴──────────┴──────────┘

  부호로 저장하면 (+ = 차변, − = 대변)
    posting(cash, +10000), posting(wallet:alice, −10000)   → 합 = 0
```

- 돈은 어디선가 나와서 어딘가로 간다. 그래서 한 이동은 **두 군데 이상**에 기록된다.
  - *전표(journal entry)*: 한 번의 업무 사건(충전·이체·환불)을 묶는 단위.
  - *분개(posting, entry line)*: 전표 안의 한 줄. 어느 계정에 얼마가 차변 또는 대변으로 붙는지.
  - *차변(debit)·대변(credit)*: 분개의 두 방향. "더하기·빼기"가 아니라 "왼쪽 칸·오른쪽 칸"이다.
- **불변식**: 전표마다 차변 합 = 대변 합. 부호 규약(+차변/−대변)으로 저장하면 **분개 합 = 0**이다.
  - Fowler는 Accounting Transaction 패턴을 "거래 안 모든 분개의 합이 0이 되게 둘 이상의 분개를 묶는다"고 정의한다(martinfowler.com, 2005-01-22).
  - Square Books 글도 "모든 전표는 0으로 균형이 맞아야 한다"를 기본 불변식으로 든다.
- Fowler는 전표 *모델*을 둘로 나눈다. 분개를 항상 정확히 두 개로 고정한 모델이 two-legged, 분개 수를 제한하지 않는 모델이 multi-legged다(multi-legged 모델로 두 줄짜리 전표도 담을 수 있다). 수수료가 붙은 결제(회사 장부, +차변/−대변: 고객 지갑 +10,000 / 판매자 미정산 −9,700 / 수수료 수익 −300)처럼 세 줄이 필요하면 multi-legged 모델이 있어야 한다(금액은 예시).

### 2. 차변이 늘리는 계정, 대변이 늘리는 계정

```text
  계정 종류            정상 잔액(normal balance)   늘어날 때
  자산(현금·미수금)       차변                       차변
  비용                   차변                       차변
  부채(고객 예치금·지갑)   대변                       대변
  자본·수익(수수료 수익)   대변                       대변
```

- Modern Treasury "Accounting for Developers" 1부는 이것을 debit normal / credit normal 계정으로 나눈다.
  - *debit normal*: 가진 것·쓴 것(자산·비용). 차변으로 늘고 대변으로 준다.
  - *credit normal*: 빚진 것·돈의 출처(부채·자본·수익). 대변으로 늘고 차변으로 준다.
- 그래서 alice 지갑(회사 입장에서 부채)의 잔액은 `−(분개 합)`으로 읽는다. 위 표에서 wallet:alice 분개 합은 −10,000이고, 잔액은 10,000이다.
- 이 표는 회사 장부 기준이다. 고객 입장에서 지갑은 자산이다. **누구의 장부인지**를 먼저 정해야 부호가 정해진다.

### 3. 잔액 = 분개의 합(폴드), 정정 = 역분개

```text
  시간 ─────────────────────────────────────────────────►
  #1 충전 +10,000 (cash Dr / alice Cr)
                     #4 역분개: #1의 부호만 뒤집음 (cash Cr / alice Dr)
                                    #5 재분개: 실제 금액 9,000
  alice 잔액:  10,000 ──────────── 0 ──────────── 9,000
              (어느 시점이든 그때까지의 분개를 더하면 그 시점 잔액)
```

- *폴드(fold)*: 목록을 앞에서부터 하나씩 누적해 값 하나로 접는 연산. 잔액 = 분개 금액의 누적 합.
- 잔액이 파생값이면 **어느 과거 시점의 잔액**도 그때까지의 분개만 더해 다시 만들 수 있다.
  - Modern Treasury 글은 "불변 거래를 저장하고 잔액은 항상 거래에서 계산하라"고 권한다.
- 정정은 원래 줄을 고치지 않는다. 반대 부호의 새 전표를 쌓는다.
  - *역분개(reversal)*: 틀린 전표와 부호만 반대인 전표. 둘을 더하면 0이 되어 효과가 상쇄된다.
  - Fowler의 Reversal Adjustment가 이것이다: "틀린 거래는 그대로 두고, 각각에 반대 분개를 붙여 상쇄한다". Fowler는 차이만 붙이는 Difference Adjustment, 지우고 다시 쓰는 Replacement Adjustment도 함께 든다. Replacement는 회계 틀 안의 이력이 사라진다고 적는다(Parallel Model로 재구성은 되지만 덜 직접적이라고 덧붙인다). Reversal의 단점으로는 서로 상쇄될 뿐인 분개가 많이 쌓인다는 점을 든다(AccountingNarrative).
- 결과: "언제 무엇을 틀렸고 언제 어떻게 고쳤나"가 원장 자체에 남는다. 로그를 grep할 필요가 없다([reliability/18-logs-traces-audit-roles](../../reliability/18-logs-traces-audit-roles/2-summary.md) — 로그는 운영 신호, 원장은 업무 기록).

### 4. 멱등 전표와 잔액 스냅샷

```text
  멱등 전표                                  잔액 스냅샷
  요청 dep-001 ──► INSERT entry(idem_key)    분개 #1 … #39,000 ──► snapshot(cash, upto=#39,000, 2,0xx,xxx)
  재전송 dep-001 ─► UNIQUE 충돌 → 0행         잔액 = snapshot.balance + Σ(#39,001 … 끝)
                    (기록은 1번)               (전체를 다시 더한 값과 같아야 한다)
```

- *멱등 전표(idempotent entry)*: 같은 업무 요청이 두 번 와도 전표가 한 번만 생기게 하는 것. 요청마다 키(`idem_key`)를 붙이고 UNIQUE 제약을 건다([reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md)).
- *잔액 스냅샷*: 어느 분개 번호까지의 합을 저장해 둔 값. 매번 전체를 더하지 않으려고 둔다.
  - 스냅샷은 **캐시**다. 정본은 분개다. 스냅샷 + 이후 분개 = 전체 합이 성립하는지 주기적으로 대조한다.
- 차대 합 0은 **전표 하나 안의 균형**만 보장한다. 같은 전표가 두 번 들어오거나 하나가 빠져도 두 전표 모두 각자 균형이다. 그래서 멱등 키와 대사([25-reconciliation](../25-reconciliation/2-summary.md))가 따로 필요하다(reliability/04 카탈로그 F-23 "전표 누락·중복").

### 실험: PostgreSQL 17 원장 — 불균형 거절, append-only, 역분개, 멱등

스키마 핵심(전문은 실험 목록의 `ledger_schema.sql`).

```sql
CREATE TABLE journal_entry (id bigserial PRIMARY KEY, idem_key text NOT NULL UNIQUE,
  memo text, reverses bigint REFERENCES journal_entry(id), posted_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE posting (id bigserial PRIMARY KEY, entry_id bigint NOT NULL REFERENCES journal_entry(id),
  account_id text NOT NULL REFERENCES account(id), amount bigint NOT NULL CHECK (amount <> 0));
-- 불변식 1: 전표마다 분개 합 = 0 — 커밋 시점에 검사(지연 제약 트리거)
CREATE FUNCTION check_balanced() RETURNS trigger LANGUAGE plpgsql SET search_path = led AS $$
DECLARE s bigint;
BEGIN
  SELECT coalesce(sum(amount),0) INTO s FROM posting WHERE entry_id = NEW.entry_id;
  IF s <> 0 THEN RAISE EXCEPTION 'unbalanced journal entry %: sum=%', NEW.entry_id, s; END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER posting_balanced AFTER INSERT ON posting
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_balanced();
-- 불변식 2: append-only — UPDATE·DELETE 거절
CREATE TRIGGER posting_append_only BEFORE UPDATE OR DELETE ON posting
  FOR EACH ROW EXECUTE FUNCTION forbid_change();
CREATE VIEW balance AS SELECT a.id, coalesce(sum(p.amount),0) AS debit_minus_credit
  FROM account a LEFT JOIN posting p ON p.account_id = a.id GROUP BY a.id;
```

- 검사를 **지연(DEFERRED)** 하는 이유: 분개 두 줄을 넣는 사이에는 합이 0이 아니다. 문장마다 검사하면 첫 줄에서 거절된다. PostgreSQL 17 문서(CREATE TRIGGER)는 제약 트리거가 `AFTER ROW`여야 하고, 문장 끝이나 트랜잭션 끝에 실행할 수 있으며 후자를 deferred라 부른다고 적는다.

(실험, PostgreSQL 17.11 일회용 컨테이너, 2026-10-03) — 출력 발췌.

```text
--- (2) 불균형 전표: 차변 10000, 대변 9999
psql:/tmp/ledger_exp1.sql:11: ERROR:  unbalanced journal entry 2: sum=1
 entries_after_bad
-------------------
                 1
--- (3) 같은 멱등키로 재전송
 id
----
(0 rows)
INSERT 0 0
--- (4) 정정을 UPDATE로 시도
psql:/tmp/ledger_exp1.sql:16: ERROR:  UPDATE on posting is forbidden (append-only ledger)
psql:/tmp/ledger_exp1.sql:17: ERROR:  DELETE on posting is forbidden (append-only ledger)
--- (5) 정정은 역분개 + 재분개 (실제는 9000원이었다)
 id |  idem_key   | reverses |            postings
----+-------------+----------+---------------------------------
  1 | dep-001     |          | cash:10000, wallet:alice:-10000
  4 | rev-dep-001 |        1 | cash:-10000, wallet:alice:10000
  5 | dep-001-fix |          | cash:9000, wallet:alice:-9000
      id      | debit_minus_credit
--------------+--------------------
 cash         |               9000
 wallet:alice |              -9000
--- (6) 시산표: 전체 분개 합 / 불균형 전표 수
 total_sum | unbalanced_entries
-----------+--------------------
         0 |                  0
```

- 관찰 1: 1원 어긋난 전표는 **COMMIT에서** 거절되고, 전표 수는 1로 남는다(전표 행까지 롤백).
- 관찰 2: 전표 id가 1 → 4 → 5로 건너뛴다. 롤백된 전표(2)와 `ON CONFLICT DO NOTHING`으로 버려진 시도(3)가 시퀀스 값을 소비했기 때문이다. PostgreSQL 문서(9.17 시퀀스 함수)는 `nextval`이 롤백되지 않는다고 적는다. **전표 번호의 빈칸은 누락의 증거가 아니다** — 누락 검사는 번호 연속성이 아니라 대사로 한다.
- 관찰 3: wallet:alice의 `debit_minus_credit`은 −9,000이다. credit normal 계정이라 잔액은 9,000으로 읽는다.
- 관찰 4(실험 중 실제로 겪은 함정): 트리거 함수에 `SET search_path = led`를 빠뜨리자, 다른 search_path로 접속한 세션의 이체가 `relation "posting" does not exist`로 **커밋 시점에** 전부 실패했다. 검사가 실패하면 쓰기도 실패하는 쪽(fail-closed)이라 원장은 안전했지만, 트리거 함수는 스키마를 명시해야 한다.

### 실험: 검사가 막지 못하는 것 — TRUNCATE와 빈 전표

(실험, PostgreSQL 17.11, 2026-10-03)

```text
-- 실행: TRUNCATE led.posting CASCADE
TRUNCATE TABLE
 count
-------
     0

-- 실행: CREATE TRIGGER posting_no_truncate BEFORE TRUNCATE ON led.posting FOR EACH STATEMENT EXECUTE FUNCTION led.forbid_change()
-- 실행: TRUNCATE led.posting CASCADE
CREATE TRIGGER
ERROR:  TRUNCATE on posting is forbidden (append-only ledger)

--- (a) 분개 없는 빈 전표는 행 트리거가 못 본다
 id | idem_key | postings
----+----------+----------
  6 | empty-1  |        0
```

- `BEFORE UPDATE OR DELETE` 행 트리거는 `TRUNCATE`에 실행되지 않는다. PostgreSQL 17 문서는 TRUNCATE 트리거를 따로 두며 `FOR EACH STATEMENT`로만 만들 수 있다고 적는다. 트리거를 추가하자 막혔다.
- 분개 합 검사는 **분개가 들어올 때** 실행된다. 분개가 0줄인 전표는 검사를 통과한다. "전표마다 분개 2줄 이상"은 별도 점검 쿼리(시산표)나 애플리케이션 생성 경로(아래 Java)에서 막는다.
- 트리거는 테이블 소유자·슈퍼유저가 끌 수 있다(`ALTER TABLE … DISABLE TRIGGER`). 운영에서는 애플리케이션 역할에서 UPDATE·DELETE·TRUNCATE 권한을 빼는 것(`REVOKE`)을 함께 쓴다. 이 권한 분리는 이번 실험에서 재현하지 않았다.

### 실험: 동시 이체 — 잔액 확인과 기록 사이의 틈

같은 alice 지갑(잔액 9,000)에서 6,000원 이체 두 건을 동시에 보낸다. 함수는 "분개 합으로 잔액 확인 → 0.5초 대기 → 분개 기록" 순서다.

```sql
CREATE FUNCTION transfer(k text, src text, dst text, amt bigint, use_lock boolean)
RETURNS text LANGUAGE plpgsql SET search_path = led AS $$
DECLARE bal bigint; eid bigint;
BEGIN
  IF use_lock THEN PERFORM 1 FROM account WHERE id = src FOR UPDATE; END IF;
  SELECT -coalesce(sum(amount),0) INTO bal FROM posting WHERE account_id = src;
  PERFORM pg_sleep(0.5);
  IF bal < amt THEN RETURN k||': REJECTED (balance '||bal||')'; END IF;
  INSERT INTO journal_entry(idem_key,memo) VALUES (k, src||'->'||dst) RETURNING id INTO eid;
  INSERT INTO posting(entry_id,account_id,amount) VALUES (eid, src, amt), (eid, dst, -amt);
  RETURN k||': OK (saw balance '||bal||')';
END $$;
```

(실험, PostgreSQL 17.11, 2026-10-03, 각 조건 2~3회 — 회차마다 먼저 끝나는 요청(t1/t2)만 달랐고 잔액 결과는 같았다. 출력 발췌)

```text
# run_exp2.sh false (READ COMMITTED)
== use_lock=false (alice 잔액 9000, 6000원 이체 2건 동시)
t1: OK (saw balance 9000)
t2: OK (saw balance 9000)
wallet:alice|-3000
wallet:bob|12000

# run_exp2.sh true (READ COMMITTED)
== use_lock=true (alice 잔액 9000, 6000원 이체 2건 동시)
t2: OK (saw balance 9000)
t1: REJECTED (balance 3000)
wallet:alice|3000

# run_exp2_rr.sh true (BEGIN ISOLATION LEVEL REPEATABLE READ)
== use_lock=true (alice 잔액 9000, 6000원 이체 2건 동시)
t2: OK (saw balance 9000)
t1: OK (saw balance 9000)
wallet:alice|-3000
```

- 잠금 없이: 두 요청이 모두 9,000을 보고 둘 다 기록했다. **두 전표 모두 차대 합 0**이다. 불균형 검사는 이 사고를 못 본다.
- 출금 계좌 행을 `FOR UPDATE`로 잠그면 READ COMMITTED에서는 막힌다. 뒤 요청은 잠금을 기다린 뒤 다음 문장에서 **새 스냅샷**으로 3,000을 본다(PostgreSQL 17 문서 13.2.1: Read Committed는 명령마다 새 스냅샷).
- 같은 코드를 REPEATABLE READ로 돌리면 다시 음수가 됐다. 스냅샷이 트랜잭션의 첫 문장 시점에 고정되어(13.2.2), 잠금을 얻은 뒤에도 커밋 전 분개를 못 본다. 잠근 행(account)은 아무도 고치지 않았으니 직렬화 오류도 나지 않는다(13.2.2: 직렬화 오류는 앞 트랜잭션이 행을 "실제로 갱신·삭제했을 때이지 잠그기만 했을 때가 아니다").
- **잠금으로 지키는 불변식은 격리 수준에 기대고 있다.** 격리 수준이 바뀌면 조용히 깨진다.

### 실험: 잔액 캐시 열 + 조건부 UPDATE

계정 행에 `cached_balance`를 두고, 원장 기록과 **같은 트랜잭션**에서 `UPDATE … WHERE cached_balance >= amt`로 확인과 차감을 한 문장에 넣었다([database/18](../../database/18-app-level-concurrency-patterns/2-summary.md)의 조건부 UPDATE).

```sql
UPDATE account SET cached_balance = cached_balance - amt
 WHERE id = src AND cached_balance >= amt;      -- 영향 행 0이면 거절
```

(실험, PostgreSQL 17.11, 2026-10-03, 각 1회 — 출력 발췌, 마지막 줄 열은 `계정|원장 합 잔액|캐시 잔액`)

```text
== READ COMMITTED (alice 잔액 9000, 6000원 이체 2건 동시)
t2: OK
t1: REJECTED (insufficient)
wallet:alice|3000|3000
== REPEATABLE READ (alice 잔액 9000, 6000원 이체 2건 동시)
ERROR:  could not serialize access due to concurrent update
t1: OK
wallet:alice|3000|3000
```

- READ COMMITTED: 뒤 요청이 행 잠금을 기다린 뒤 **갱신된 행으로 WHERE를 다시 평가**해(13.2.1) 0행 → 거절.
- REPEATABLE READ: 뒤 요청이 직렬화 오류로 실패한다. 실패는 재시도 대상이다. 두 격리 수준 모두 음수가 되지 않았다.
- 원장 합과 캐시가 같다(3,000 = 3,000). 캐시는 원장과 같은 트랜잭션에서만 바뀌므로 어긋나지 않는다. 그래도 캐시는 파생값이다 — 대조 쿼리로 주기적으로 확인한다(적용 §3).

## 쓰이는 자료구조·알고리즘

- **append-only 로그** — 분개는 추가만 한다. 정정도 추가(역분개)다. 이벤트 소싱의 이벤트 로그와 같은 모양이다([distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md)). 원장은 그중 "금액 합 0" 불변식이 붙은 특수한 경우다.
- **폴드(누적 합)** — 잔액 = Σ 분개 금액. 시점 잔액 = 그 시점까지의 Σ. 누적합 배열([algorithm/10-prefix-sum](../../algorithm/10-prefix-sum/2-summary.md))과 같은 원리로 스냅샷을 둔다.
- **스냅샷 + 증분** — `잔액 = 스냅샷 + Σ(이후 분개)`. 실험에서 2만 전표(4만 분개) 기준 전체 합 10.0~11.8ms, 스냅샷 + 증분 1.45~1.46ms였다(아래 적용 §3, 2회 측정 — 실행마다 다르다).
- **유일 키 집합(멱등)** — `idem_key UNIQUE`. 해시 집합의 "이미 있나" 검사를 DB 제약으로 옮긴 것.
- **고정 소수점 정수** — 금액을 원 단위(통화의 최소 단위) `bigint`로 저장한다. 소수점 금액·반올림·배분은 [14-money-arithmetic-rounding-allocation](../14-money-arithmetic-rounding-allocation/2-summary.md), 통화·단위 값 객체는 [12-time-money-and-units](../12-time-money-and-units/2-summary.md).
- **group-by 합 검사(시산표)** — `GROUP BY entry_id HAVING sum(amount) <> 0` = 불균형 전표 목록. 전체 `sum(amount) = 0`은 원장 전체의 균형.

## 적용 — 풀어나가는 법

### 1. 순서

1. **장부의 주인을 정한다** — 회사 장부인가, 고객 장부인가. 이것이 계정 종류(자산·부채)와 부호를 정한다.
2. **계정 목록을 만든다** — 현금, 고객별 지갑(부채), 수수료 수익, 미정산금(판매자에게 줄 돈) 등. 계정마다 정상 잔액 방향(debit/credit normal)과 음수 허용 여부를 적는다.
3. **업무 사건마다 전표 모양을 정한다** — "충전 = 현금 Dr / 지갑 Cr", "결제 = 지갑 Dr / 판매자 미정산 Cr + 수수료 수익 Cr" 같은 표. Fowler 『Analysis Patterns』(1996) 6장 "Inventory and Accounting"의 목차에 Posting Rules·Posting Rule Execution·Posting Rules for Many Accounts 절이 있다(InformIT 목차로 확인, 책 본문은 열지 못했다). martinfowler.com/eaaDev의 회계 패턴 목록(Account·Accounting Entry·Accounting Transaction·세 Adjustment)에는 Posting Rule이 없다.
4. **불변식을 DB와 코드 두 곳에 둔다** — 코드(생성 시 합 0 검사)는 빠른 피드백, DB(지연 제약 트리거·UNIQUE·권한)는 코드가 틀려도 막는 마지막 선.
5. **정정 절차를 정한다** — 역분개 + 재분개. 역분개는 원 전표를 `reverses`로 가리킨다.
6. **잔액 확인 방식을 정한다** — 캐시 열 + 조건부 UPDATE, 또는 계정 행 잠금 + 격리 수준 고정. 격리 수준을 바꾸면 다시 시험한다(위 실험).
7. **대조를 예약한다** — 시산표(전체 합 0), 캐시 vs 원장 합, 스냅샷 vs 전체 합, 외부와의 대사([25](../25-reconciliation/2-summary.md)).

### 2. 도메인 코드 — 불균형 전표는 객체로 존재할 수 없게

```java
record Posting(String account, long amount) {          // +차변 / -대변, 원 단위
    Posting { if (amount == 0) throw new IllegalArgumentException("0원 분개"); }
    Posting negate() { return new Posting(account, -amount); }
}
record JournalEntry(String idemKey, List<Posting> postings, String reverses) {
    JournalEntry {
        postings = List.copyOf(postings);                // 불변 복사
        if (postings.size() < 2) throw new IllegalArgumentException("분개는 2줄 이상");
        long sum = postings.stream().mapToLong(Posting::amount).sum();
        if (sum != 0) throw new IllegalArgumentException("불균형 전표 " + idemKey + ": sum=" + sum);
    }
    JournalEntry reversal(String key) {                  // 역분개 = 부호만 뒤집은 새 전표
        return new JournalEntry(key, postings.stream().map(Posting::negate).toList(), idemKey);
    }
}
```

- 전표가 애그리거트 루트다. 분개는 전표를 통해서만 만들어진다. "분개 합 0"은 이 애그리거트의 불변식이다([05-aggregates-and-invariants](../05-aggregates-and-invariants/2-summary.md)).
- 잔액은 전표 애그리거트 밖이다. 계정 잔액 한도(음수 금지)는 여러 전표에 걸친 불변식이라 전표 하나로는 못 지킨다 — 위 동시 이체 실험이 그 증거다. 그래서 계정 행(캐시 열)의 조건부 UPDATE나 잠금이 따로 필요하다.

(실험, JDK 21.0.12 temurin 일회용 컨테이너, 2026-10-03) — 위 코드 + `putIfAbsent` 멱등 저장 + 폴드 잔액.

```text
post dep-001       -> true
post dep-001 again -> false
rejected: 불균형 전표 dep-002: sum=1
post reversal      -> true
post fix 9000      -> true
entries=3 cash=9000 wallet:alice=-9000
```

- JPA로 매핑할 때: 분개를 `@ElementCollection`이나 `@OneToMany(cascade = ALL)`로 두면 컬렉션 교체 시 DELETE + INSERT가 나갈 수 있다 [?] — Hibernate 버전별 동작은 이 노트에서 확인하지 않았다. append-only 테이블에 DELETE가 나가면 위 트리거가 거절하므로, 분개를 별도 엔티티로 두고 INSERT만 하는 저장 경로를 쓰는 편이 안전하다.

### 3. 진단 쿼리

```sql
-- 시산표: 원장 전체 합과 불균형 전표 수
SELECT sum(amount) AS total_sum,
  (SELECT count(*) FROM (SELECT entry_id FROM posting GROUP BY entry_id HAVING sum(amount) <> 0) x) AS unbalanced
FROM posting;
-- 분개 2줄 미만 전표(빈 전표 포함)
SELECT e.id FROM journal_entry e LEFT JOIN posting p ON p.entry_id = e.id GROUP BY e.id HAVING count(p.id) < 2;
-- 캐시 잔액 vs 원장 합
SELECT a.id, a.cached_balance, -coalesce(sum(p.amount),0) AS ledger
FROM account a LEFT JOIN posting p ON p.account_id = a.id WHERE a.normal = 'CREDIT'
GROUP BY a.id HAVING a.cached_balance <> -coalesce(sum(p.amount),0);
```

스냅샷이 전체 합과 같은지(실험, PostgreSQL 17.11, `posting(account_id, id)` 인덱스, 2026-10-03 — 아래는 첫 실행 출력. 재실행에서는 같은 합 2,068,997에 9.975ms / 1.450ms).

```text
--- (b) 잔액 스냅샷: 2만 전표 적재 후 스냅샷 + 이후 분개 = 전체 합
 full_sum
----------
  2068997
Time: 11.770 ms
 snap_plus_delta
-----------------
         2068997
Time: 1.464 ms
```

### 4. 검사 트리거의 비용 — 인덱스가 없으면 커밋이 느려진다

지연 트리거는 분개 한 줄마다 "그 전표의 합"을 조회한다. `posting(entry_id)` 인덱스가 없으면 조회마다 테이블 전체를 읽는다.

(실험, PostgreSQL 17.11 `--cpus=2`, 2026-10-03, 3회 측정 범위 — COMMIT 시간)

| 한 트랜잭션에 넣은 전표 수(분개 수) | entry_id 인덱스 없음 | 인덱스 있음 |
|---|---|---|
| 2,000 (4,000) | 2,412~3,472 ms | 92~174 ms |
| 4,000 (8,000) | 14,307~19,536 ms | 157~309 ms |
| 20,000 (40,000) | (측정 안 함 — 첫 시도 20만 전표는 2분 넘게 끝나지 않아 취소) | 830~1,384 ms |

- 인덱스 없이 전표 수를 2배로 늘리자 커밋 시간이 회차마다 약 5.5~5.9배 늘었다. 줄마다 테이블 전체를 읽으므로 대략 제곱으로 자란다(해석).
- 이 표는 2 CPU로 제한한 일회용 컨테이너의 값이다. 수치보다 "검사 쿼리가 쓰는 열에 인덱스"라는 결론을 가져간다.

## 장애 시나리오와 대처

### 1. 잔액 열만 UPDATE한다 → 잔액이 틀려도 원인을 못 찾는다 (⚠)

- 현상: 고객이 "충전한 10,000원 중 1,000원이 사라졌다"고 문의한다.
- 보이는 형태: `balance` 열은 9,000. 감사 로그가 없거나, 애플리케이션 로그는 보존 기한이 지났다. 어느 요청이 바꿨는지 재구성할 수 없다.
- 원인: 이동의 근거가 데이터에 남지 않고 결과값만 남았다.
- 대처: 분개 원장을 정본으로 두고 잔액은 파생(뷰·캐시)으로 바꾼다. 이행 기간에는 "현재 잔액 = 이월 전표(opening balance) 1건"으로 시작해 이후 이동부터 분개로 남긴다. 과거 이력은 복원할 수 없음을 인정하고 이월 시점을 기록한다.

### 2. 정정을 UPDATE·DELETE로 한다 → 감사 흔적이 사라진다 (⚠)

- 현상: 운영자가 잘못 들어간 전표 금액을 SQL로 고쳤다. 다음 달 정산 보고서가 이미 보낸 보고서와 다르다.
- 보이는 형태: 같은 기간을 다시 조회했는데 합계가 바뀌었다. 무엇이 언제 바뀌었는지 원장에 흔적이 없다.
- 원인: 원장을 수정 가능한 표로 다뤘다. 과거 보고서가 근거로 삼았던 행이 사라졌다.
- 대처: UPDATE·DELETE·TRUNCATE를 트리거와 권한(REVOKE)으로 막는다(실험: TRUNCATE는 행 트리거로 안 막힌다). 정정은 역분개 + 재분개. 이미 마감한 기간의 정정은 **정정한 날짜의 전표**로 넣고 원 전표를 가리킨다.

### 3. 차변 합 ≠ 대변 합인데 알람이 없다 (⚠)

- 현상: 월말 시산표에서 원장 전체 합이 0이 아니다. 언제부터인지 모른다.
- 보이는 형태: `sum(amount)`가 0이 아닌 값. 불균형 전표 목록 쿼리에 몇 건이 나온다.
- 원인: 합 검사가 애플리케이션 코드 한 곳에만 있었고, 배치·수기 SQL·이관 스크립트 경로가 그 코드를 거치지 않았다. 또는 분개를 여러 트랜잭션에 나눠 넣었다.
- 대처: 전표와 분개를 **한 트랜잭션**으로 넣고, DB에 지연 제약 트리거를 둔다. 시산표 쿼리를 매일 돌려 0이 아니면 경보를 낸다. 경보는 "검사가 돌았는지"도 함께 본다(검사 배치가 멈추면 경보도 없다).

### 4. 동시 이체에서 잔액이 음수가 된다 (⚠)

- 현상: 잔액 9,000원 지갑에서 6,000원 결제가 두 번 승인됐다.
- 보이는 형태: 잔액 −3,000. 두 전표 모두 차대 합 0이라 시산표는 정상이다(실험).
- 원인: "잔액 확인"과 "분개 기록" 사이에 다른 트랜잭션이 끼었다. 계정 행을 잠갔더라도 REPEATABLE READ에서는 고정된 스냅샷 때문에 막히지 않았다(실험).
- 대처: 확인과 차감을 한 문장으로(캐시 열 조건부 UPDATE) 하거나, 같은 행을 갱신해 격리 수준이 충돌을 잡게 한다. 직렬화 오류는 재시도한다. 격리 수준을 바꾸는 배포 전에 동시 이체 테스트를 다시 돌린다. DB 제약으로 `CHECK (cached_balance >= 0)`을 더하면 코드가 틀려도 거절된다.

### 5. 같은 업무 요청이 전표 두 개가 된다

- 현상: 네트워크 재시도로 충전이 두 번 기록됐다.
- 보이는 형태: 같은 금액·같은 시각대의 전표 두 건. 둘 다 균형이라 시산표는 정상이다.
- 원인: 멱등 키가 없거나, 키를 요청마다 새로 만들었다(재시도도 새 키).
- 대처: 업무 요청 단위(주문 ID + 사건 종류 등)로 키를 정하고 `UNIQUE`로 막는다. 이미 들어간 중복은 지우지 않고 역분개한다. 외부 기록과 맞춰보는 대사가 마지막 안전망이다([25](../25-reconciliation/2-summary.md)).

## 핵심 문장

- 잔액은 저장하는 값이 아니라 **분개를 더해 만드는 값**이다 — 캐시를 두더라도 정본은 분개다.
- 전표마다 분개 합 = 0이 원장의 불변식이고, 두 줄 사이에는 합이 0이 아니므로 검사는 **커밋 시점**(지연 제약)에 한다.
- 정정은 고치는 것이 아니라 **반대 부호 전표를 쌓는 것**이다 — 그래야 틀린 값과 고친 흔적이 함께 남는다.
- 차대 합 0은 전표 하나의 균형만 보장한다 — 중복 전표·누락 전표·음수 잔액은 균형이 맞은 채로 생긴다(실험). 멱등 키·잔액 조건부 갱신·대사가 따로 필요하다.
- 잠금으로 지키는 잔액 검사는 격리 수준에 기댄다 — 같은 코드가 READ COMMITTED에서는 막고 REPEATABLE READ에서는 뚫렸다(PostgreSQL 17.11 실험).

## 관련 주제·근거

### 선행·후속

- 선행: [05-aggregates-and-invariants](../05-aggregates-and-invariants/2-summary.md) · [12-time-money-and-units](../12-time-money-and-units/2-summary.md) · [14-money-arithmetic-rounding-allocation](../14-money-arithmetic-rounding-allocation/2-summary.md) · [database/18-app-level-concurrency-patterns](../../database/18-app-level-concurrency-patterns/2-summary.md)
- 후속: [25-reconciliation](../25-reconciliation/2-summary.md) · [22-decision-log-and-provenance](../22-decision-log-and-provenance/2-summary.md) · [23-versioned-rules-and-effective-dating](../23-versioned-rules-and-effective-dating/2-summary.md)
- 다른 영역: [database/13-transactions-acid](../../database/13-transactions-acid/2-summary.md) · [database/16-mvcc](../../database/16-mvcc/2-summary.md)(스냅샷) · [database/17-occ-and-timestamp-ordering](../../database/17-occ-and-timestamp-ordering/2-summary.md) · [distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md) · [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md) · [reliability/18-logs-traces-audit-roles](../../reliability/18-logs-traces-audit-roles/2-summary.md) · [reliability/04-failure-modes-catalog](../../reliability/04-failure-modes-catalog/2-summary.md)(F-22 초과 승인·F-23 전표 누락·중복)
- 연결 사례(커리큘럼 `api-design/25-case-settlement-report`·`27-case-refund`): [api-design/04-settlement-report](../../api-design/25-case-settlement-report/2-summary.md)(상쇄 엔트리 추가로 정정) · [api-design/06-refund](../../api-design/27-case-refund/2-summary.md)(누적 환불 상한 조건부 UPDATE)
- 연습 문제: [basic/14-points](../basic/14-points/2-summary.md)(잔액 = 덩어리의 파생값, 사용 장부) · [basic/10-payment](../basic/10-payment/2-summary.md)(멱등키·파생 상태) · [advanced/16-audit-replay](../advanced/16-audit-replay/2-summary.md)(로그 재생·REVERSE) · [advanced/14-mileage-expiry](../advanced/14-mileage-expiry/2-summary.md)(사건 재생으로 잔액·소멸 계산)

### 근거

- Square, Łukasz Strzałkowski, "Books, an immutable double-entry accounting database service", 2019-10-16 — https://developer.squareup.com/blog/books-an-immutable-double-entry-accounting-database-service/ (전표 합 0, append-only, 정정은 새 전표, 책별 단조 증가 버전)
- Martin Fowler, "Accounting Transaction", 2005-01-22 — https://martinfowler.com/eaaDev/AccountingTransaction.html (분개 합 0, two-legged·multi-legged)
- Martin Fowler, "Accounting Patterns" 개요 — https://martinfowler.com/eaaDev/AccountingNarrative.html (잔액 = 분개 합, Reversal·Difference·Replacement Adjustment). eaaDev 글은 Fowler가 2000년대 중반 쓴 "Further Enterprise Application Architecture" 원고다(각 글 머리말). 같은 영역은 『Analysis Patterns』(1996) 6장 "Inventory and Accounting"이 다룬다 — https://www.informit.com/store/analysis-patterns-reusable-object-models-9780201895421 (목차)
- Modern Treasury, "Accounting for Developers, Part I", 2022-08-17(2025-08-13 갱신) — https://www.moderntreasury.com/journal/accounting-for-developers-part-i (debit/credit normal, 불변 거래에서 잔액 계산)
- PostgreSQL 17 문서 — CREATE TRIGGER(제약 트리거 `AFTER ROW`·deferred, TRUNCATE 트리거는 `FOR EACH STATEMENT`만) https://www.postgresql.org/docs/17/sql-createtrigger.html · 13.2 Transaction Isolation(13.2.1 Read Committed 명령별 스냅샷·WHERE 재평가, 13.2.2 Repeatable Read 첫 문장 스냅샷·`could not serialize access due to concurrent update`) https://www.postgresql.org/docs/17/transaction-iso.html · 9.17 Sequence Manipulation Functions(nextval 비롤백)

### 실험 목록

- 원장 불변식(불균형 거절·멱등·UPDATE/DELETE 거절·역분개·시산표) — PostgreSQL 17.11 일회용 컨테이너, `ledger_schema.sql` + `ledger_exp1.sql`
- TRUNCATE 우회와 statement 트리거, 빈 전표 — 같은 환경, `ledger_exp4.sql`(a)
- 동시 이체(잠금 없음·FOR UPDATE·RC/RR) — 같은 환경, `ledger_exp2.sql` + `run_exp2.sh`, `run_exp2_rr.sh`
- 잔액 캐시 조건부 UPDATE(RC/RR) — 같은 환경, `ledger_exp3.sql` + `run_exp3.sh`
- 스냅샷 + 증분 = 전체 합 — 같은 환경, `ledger_exp4.sql`(b)
- 지연 트리거 비용(entry_id 인덱스 유무) — 같은 환경 `--cpus=2`, `ledger_exp5.sql`
- Java 도메인 모델(전표 생성 시 합 0, 역분개, 멱등 저장, 폴드 잔액) — JDK 21.0.12 temurin, `Ledger.java`
