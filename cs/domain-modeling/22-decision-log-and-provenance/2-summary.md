# domain-modeling/22-decision-log-and-provenance — 결정 기록과 출처: "왜 이 값인가"를 데이터로 남긴다 — 정리 (힌트)

## 해결하는 문제

고객이 묻는다. "지난달 주문 3번, 왜 9,270원이에요?"

```text
  남아 있는 것                       답하려면 필요한 것
  orders: id=3, final=9270           그때 고객 등급은?        ← customer 테이블은 지금 값만 있다
  customer_id=3, rule='member-discount'  그때 할인율은?         ← discount_rule은 덮어써졌다
                                     중간 계산(할인액)은?      ← 어디에도 없다
  앱 로그: 30일 보관                  로그로 재구성?            ← 보존 기한이 지났다
```

- 결과만 저장하면 결과의 **근거**가 사라진다. 참조 데이터(등급·요율)가 바뀌면 다시 계산해도 다른 값이 나온다.
- 해법: 결정 하나마다 **입력·규칙·중간 산출·결과·시각**을 한 레코드로 남긴다. 이 레코드는 고치지 않는다.
  - *결정 기록(decision log)*: 도메인 계산(가격·한도·심사·정산)의 결과와 그 근거를 함께 담은 불변 레코드.
  - *출처(provenance)*: W3C PROV-DM(2013-04-30 Recommendation)의 정의로 "어떤 데이터나 사물의 생산·영향·전달에 관여한 사람·기관·개체·활동을 기술하는 기록".
  - *재현 가능성 테스트*: 결정 기록만 가지고 다시 계산하면 저장된 결과와 같은지 확인하는 테스트.

쉬운 예: 수학 시험 답안지다.
- 답만 적으면 맞았는지 틀렸는지만 안다. 풀이를 적으면 어디서 틀렸는지 안다.
- 문제지(입력)가 나중에 바뀌어도, 답안지에 문제를 옮겨 적어 두었으면 다시 채점할 수 있다.

똑같은 구조다. 문제 = 입력 스냅샷, 공식 = 규칙 ID·버전, 풀이 = 중간 산출, 답 = 결과다.

실무 예: 가격·할인 계산, 대출 심사 점수, 보험료 산정, 정산 수수료, 추천 결과의 노출 이유. 고객 분쟁·감사·규제 대응에서 "그때 왜"를 답해야 하는 곳.

로그와 감사 기록의 역할 구분(로그는 버려도 되는 운영 신호, 감사·업무 기록은 같은 트랜잭션·추가만·보존)과 해시 체인 변조 탐지의 기초 실험은 [reliability/18-logs-traces-audit-roles](../../reliability/18-logs-traces-audit-roles/2-summary.md) 4·5절에 있다. 이 노트는 그 위에 **도메인 계산의 재현성**을 다룬다.

## 동작·원리

### 1. 결정 레코드의 모양

```text
  decision_log (추가만)
  ┌──────────┬─────────────────────┬─────────────────────────────────────────────┐
  │ seq      │ 40                  │ 체인 순서                                    │
  │ order_id │ 3                   │ 무엇에 대한 결정인가                          │
  │ decided_at│ 2026-10-03 09:03+09│ 결정 시각 (언제 기준으로 계산했나)             │
  │ input    │ {grade: GOLD,       │ 입력 스냅샷 — 참조가 아니라 "그때 값"을 복사    │
  │          │  amount: 10300}     │                                             │
  │ rule_id  │ member-discount     │ 어떤 규칙                                    │
  │ rule_ver │ 1                   │ 규칙의 어느 버전                              │
  │ intermediate│ {rate: 0.10,     │ 중간 산출 — 사람이 읽고 검산할 수 있게          │
  │          │  discount: 1030}    │                                             │
  │ final    │ 9270                │ 결과                                         │
  │ prev_hash, hash │ ...          │ 변조 탐지 (선택)                              │
  └──────────┴─────────────────────┴─────────────────────────────────────────────┘
```

- PROV-DM 용어로 읽으면
  - *Entity*: 결정 결과(9,270원), 입력 스냅샷, 규칙 v1.
  - *Activity*: "할인 계산" 실행(시작·끝 시각).
  - *Agent*: 계산을 책임진 주체(서비스·담당자).
  - 관계: 결과 `wasGeneratedBy` 계산, 계산 `used` 입력·규칙 v1, 결과 `wasDerivedFrom` 입력. PROV-DM 정의는 W3C 원문 확인.
- 입력을 **참조 + 버전**으로 둘 수도 있다(`customer_snapshot_id=…`, `price_table_version=7`). 조건: 참조 대상이 추가만 하는 버전 테이블이어서 그 버전이 영원히 같은 값을 돌려줘야 한다. 그러면 복사 비용을 줄이면서 재현성을 지킨다.

### 2. 참조만 남기면 왜 재현이 깨지나

```text
  결정 시점 t0                      재계산 시점 t1
  customer(3).grade = GOLD          customer(3).grade = GOLD    (그대로)
  discount_rule(GOLD) = 0.10        discount_rule(GOLD) = 0.12  (덮어씀)
  final = 10300 × 0.90 = 9270       recompute = 10300 × 0.88 = 9064   ≠ 9270
```

- 참조(ID)는 "지금의 그것"을 가리킨다. 지금이 바뀌면 같은 ID가 다른 값을 낸다.
- 커리큘럼 ⚠ "규칙 ID만 남기고 입력을 참조로만 뒀다 → 참조 데이터가 바뀌어 재계산 결과가 다르다"가 이것이다.

### 실험: 참조만 남긴 기록 vs 스냅샷 + 규칙 버전 — 참조 데이터가 바뀐 뒤 재계산

- 환경: 전용 일회용 컨테이너 PostgreSQL 17.11(`psql`), 2026-10-03.
- 고객 100명(등급 GOLD·SILVER·BASIC), 주문 100건(금액 10000 + 주문번호×100, 예시). 할인 규칙 v1: GOLD 0.10, SILVER 0.05, BASIC 0.
- A: `decision_ref(order_id, customer_id, rule_id, amount, final)` — 참조만.
- B: `decision_log` — 입력 스냅샷(jsonb) + 규칙 ID·버전 + 중간 산출 + 결과 + 결정 시각 + 해시 체인. 규칙은 `rule_version`(추가만)에서 읽는다.
- 그다음 시간이 흐른다: 고객 10명의 등급을 GOLD로 올리고, `discount_rule`의 GOLD 요율을 0.12로 덮어쓴다(버전 테이블에는 v2를 추가).

```sql
-- 재현 테스트: 같은 주문을 다시 계산하면 같은가
SELECT 'A 참조만', count(*) FILTER (WHERE d.final <> round(d.amount * (1 - r.rate))), count(*)
FROM decision_ref d JOIN customer c ON c.id = d.customer_id JOIN discount_rule r ON r.grade = c.grade
UNION ALL
SELECT 'B 스냅샷+버전',
       count(*) FILTER (WHERE l.final <> (l.input->>'amount')::int - round((l.input->>'amount')::int * v.rate)), count(*)
FROM decision_log l
JOIN rule_version v ON v.rule_id = l.rule_id AND v.version = l.rule_version AND v.grade = l.input->>'grade';
```

(실험, PostgreSQL 17.11, 2026-10-03)

```text
     방식      | 불일치 | 전체 
---------------+--------+------
 A 참조만      |     40 |  100
 B 스냅샷+버전 |      0 |  100
```

- A: 100건 중 40건이 다른 값을 냈다. 요율이 바뀐 GOLD 33건 + 새로 GOLD가 된 7건(등급을 올린 10명 중 3명은 원래 GOLD)이다.
- B: 0건. 스냅샷과 규칙 버전이 그때 값을 고정한다.
- "왜 이 금액인가"에 대한 B의 답은 한 행이다.

```text
 order_id |       decided_at       |                        input                         |     rule_id     | rule_version |           intermediate           | final 
----------+------------------------+------------------------------------------------------+-----------------+--------------+----------------------------------+-------
        3 | 2026-10-03 00:03:00+00 | {"grade": "GOLD", "amount": 10300, "customer_id": 3} | member-discount |            1 | {"rate": 0.10, "discount": 1030} |  9270
```

### 3. 변조 탐지 — 해시 체인과 그 함정

```text
  행 n:  hash_n = SHA-256(prev_hash || 정규화한 내용_n)
  검증:  저장된 hash_n == 다시 계산한 값?   prev_hash_n == hash_(n-1)?
  고정점: 머리 해시를 체인 밖(별도 권한·외부 저장소)에 주기적으로 적는다
```

- 해시 체인의 원리·고정점의 필요성 실험(Java)은 [reliability/18](../../reliability/18-logs-traces-audit-roles/2-summary.md) 5절에 있다. 같은 것을 SQL로 확인하고, 새 함정 하나를 더 본다.
- DDIA 1판 12장 "Trust, but Verify" 안의 "Designing for auditability"는 트랜잭션 로그의 삽입·갱신·삭제만으로는 **왜** 그 변경이 일어났는지 알기 어렵다고 적고, 입력을 불변 이벤트로 두고 상태를 결정적으로 파생하는 방식이 감사에 유리하다고 한다(발췌로 확인, 본문 전체는 미열람).

### 실험: SQL 해시 체인 — 변조, 체인 재계산, 그리고 세션 시간대

(실험, PostgreSQL 17.11, 2026-10-03 — 위 `decision_log` 100행, `sha256()` 내장 함수)

```text
== 해시 체인 검증 (변조 전)
 깨진_행 
---------
       0

== 누군가 주문 40의 결과를 UPDATE로 고친다
 seq | order_id | link_ok | hash_ok 
-----+----------+---------+---------
  40 |       40 | t       | f

== 공격자가 40부터 끝까지 해시를 다시 계산해 덮는다
 깨진_행 
---------
       0

== 외부에 보관한 머리 해시와 비교
before=d556aba3830551c73258781b303e33ae62c94ea77fdfbff5f740151912562ad5
after=469b6286f5ae1c685c0eb588e06d5c5691fd31c7064bb95245c5b44721a49fb8
다름
```

- 내용만 고치면 그 행의 `hash_ok`가 거짓이 됐다. 뒤를 전부 다시 계산하면 체인 자체는 0건 — 밖에 둔 머리 해시와 비교해야 드러났다. reliability/18의 Java 실험과 같은 결론이다.
- 새 함정: 해시 입력에 `decided_at::text`를 넣었다. `timestamptz`의 텍스트 표현은 세션 `TimeZone`을 따른다. 같은 데이터를 다른 세션 설정으로 검증했다.

(실험, 같은 환경)

```text
 TimeZone 
----------
 Etc/UTC
SET                                       ← set timezone='Asia/Seoul'
 깨진_행 | count 
---------+-------
     100 |   100
```

- 변조가 없는데 **100행 전부** 깨진 것으로 나왔다. 해시는 바이트를 비교하므로, 같은 시각이라도 `00:03:00+00`과 `09:03:00+09`는 다른 입력이다.
- 대처: 해시 입력을 **정규화(canonicalize)** 한다. 시각은 UTC ISO 문자열이나 epoch 정수로, 숫자는 고정 스케일로, JSON은 키 순서를 고정해 직렬화한다. PostgreSQL 17 `jsonb`는 입력의 키 순서·공백을 보존하지 않고 중복 키는 마지막 값만 남긴다(문서 8.14). 이 실험에서는 `jsonb::text`를 해시 입력으로 써도 같은 세션 설정에서 재검증이 일치했다(변조 전 0행). 앱에서 해시를 만들면 앱 쪽 직렬화 규칙을 따로 정해야 한다.

## 쓰이는 자료구조·알고리즘

- **불변 레코드(append-only)** — 결정은 고치지 않는다. 정정은 새 결정(정정 사유·이전 결정 참조)으로 남긴다. 원장의 역분개와 같은 생각이다([24-double-entry-ledger](../24-double-entry-ledger/2-summary.md)).
- **해시 체인** — 각 행이 직전 행의 해시를 담는 연결 리스트. 중간 변경·삭제를 탐지한다. 고정점(체인 밖 머리 해시)이 있어야 전체 재계산을 탐지한다. 더 나아가면 머클 트리(Certificate Transparency 등)로 부분 증명을 한다.
- **버전 테이블 + 구간 조회** — 규칙·참조 데이터를 `(id, version)` 또는 유효 기간으로 추가만 한다. 시각으로 버전을 찾는 것은 [23-versioned-rules-and-effective-dating](../23-versioned-rules-and-effective-dating/2-summary.md) · [database/50-temporal-and-bitemporal-tables](../../database/50-temporal-and-bitemporal-tables/2-summary.md).
- **결정적 함수** — 재현은 계산 `f(입력, 규칙 버전)`이 순수할 때만 성립한다. 현재 시각·난수·외부 조회를 입력으로 끌어올려 스냅샷에 넣는다. [software-design/26-functional-core-imperative-shell](../../software-design/26-functional-core-imperative-shell/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 순서

1. "그때 왜"를 물을 결정을 고른다. 돈·권리·분쟁이 걸린 계산부터(가격, 심사, 정산).
2. 계산을 순수 함수로 만든다: `Decision decide(Input in, RuleSet rules)`. 시각은 `Clock`에서 받아 입력에 넣는다.
3. 입력 스냅샷의 범위를 정한다. 계산이 **읽은 값 전부**다. 참조 + 버전으로 둘 것은 그 버전이 추가만 하는 테이블일 때만.
4. 규칙에 ID와 버전을 붙인다. 코드로 된 규칙이면 규칙 버전 = 배포 버전(또는 규칙 모듈 버전)을 기록한다.
5. 결정 레코드를 업무 데이터와 **같은 트랜잭션**에 쓴다. 로그에 쓰지 않는다.
6. 재현 가능성 테스트를 둔다: 표본 결정을 다시 계산해 같은지. 배포 전후로 돌린다.
7. 보존 기한·개인정보 범위를 정한다. 스냅샷은 개인정보를 복사하므로 삭제 요청 범위에 들어간다(reliability/18 6절).
8. 필요하면 해시 체인 + 외부 고정점. 해시 입력은 정규화한다.

### 2. 코드 모양 (Java)

```java
public record DiscountInput(long customerId, String grade, BigDecimal amount, Instant at) {}
public record DiscountTrace(BigDecimal rate, BigDecimal discount) {}
public record DiscountDecision(DiscountInput input, String ruleId, int ruleVersion,
                               DiscountTrace trace, BigDecimal result) {}

public final class MemberDiscountV1 {             // 규칙 = 순수 함수 + ID·버전
    public static final String ID = "member-discount"; public static final int VERSION = 1;
    private static final Map<String, BigDecimal> RATE = Map.of("GOLD", new BigDecimal("0.10"),
            "SILVER", new BigDecimal("0.05"), "BASIC", BigDecimal.ZERO);

    public static DiscountDecision decide(DiscountInput in) {
        BigDecimal rate = RATE.get(in.grade());
        BigDecimal discount = in.amount().multiply(rate).setScale(0, RoundingMode.HALF_UP);
        return new DiscountDecision(in, ID, VERSION, new DiscountTrace(rate, discount), in.amount().subtract(discount));
    }
}

// 재현 가능성 테스트
@Test void recorded_decisions_reproduce() {
    for (DiscountDecision d : decisionRepo.sample(1000)) {
        DiscountDecision again = rules.byIdAndVersion(d.ruleId(), d.ruleVersion()).decide(d.input());
        assertThat(again.result()).isEqualByComparingTo(d.result());   // BigDecimal은 compareTo로 비교(스케일 차이)
    }
}
```

- 규칙 버전별 클래스를 지우지 않는다. 옛 결정을 재현하려면 옛 규칙이 실행 가능해야 한다. 요율만 다른 규칙이면 코드는 하나, 요율표를 버전 테이블로 둔다.

### 3. 진단

```sql
-- 재현 실패 표본: 스냅샷 + 규칙 버전으로 재계산한 값과 저장 값이 다른 결정
SELECT l.order_id, l.final, (l.input->>'amount')::int - round((l.input->>'amount')::int * v.rate) AS recomputed
FROM decision_log l
JOIN rule_version v ON v.rule_id = l.rule_id AND v.version = l.rule_version AND v.grade = l.input->>'grade'
WHERE l.final <> (l.input->>'amount')::int - round((l.input->>'amount')::int * v.rate);

-- 결정 기록이 없는 업무 행 (같은 트랜잭션에 쓰지 않은 흔적)
SELECT o.id FROM orders o LEFT JOIN decision_log l ON l.order_id = o.id WHERE l.order_id IS NULL;

-- 해시 검증은 고정된 세션 설정에서: SET TimeZone = 'UTC';
```

## 장애 시나리오와 대처

### 1. "왜 이 금액인가"를 재현할 수 없다 (커리큘럼 ⚠)

- 현상: 고객 분쟁에서 금액 근거를 설명하지 못한다. 지금 다시 계산하면 다른 값이 나온다.
- 보이는 형태: 주문 행에는 결과와 규칙 ID뿐이다. 실험 A처럼 재계산 불일치(100건 중 40건).
- 원인: 입력을 참조로만 남겼고, 참조 데이터(등급·요율)가 덮어써졌다.
- 대처: 입력 스냅샷 + 규칙 버전을 결정 레코드로. 이미 지난 건은 DB 백업·PITR 시점 조회로 그때 값을 찾는다(보존 범위 안일 때만).

### 2. 로그로 재구성하려 했는데 보존 기한이 지났다 (커리큘럼 ⚠)

- 현상: 6개월 전 결정을 조사하는데 앱 로그는 30일(예시)만 남아 있다.
- 원인: 업무 근거를 운영 로그에 맡겼다. 로그는 샘플링·레벨 조정·보존 기한으로 버려지는 신호다(reliability/18 실험: 레벨 WARN에서 환불 로그 0/100).
- 대처: 결정 근거는 업무 데이터로, 업무 트랜잭션 안에. 보존 기한은 업무·법 요구로 정한다.

### 3. 규칙 ID만 남기고 입력은 참조로 → 참조 데이터 변경 후 결과가 다르다 (커리큘럼 ⚠)

- 현상: 정산 재계산 배치가 과거 달 금액을 다르게 낸다. 회계 마감 숫자와 안 맞는다.
- 원인: 참조 대상(요율표·고객 등급)이 버전 없이 덮어써지는 테이블이었다.
- 대처: 참조 대상을 추가만 하는 버전 테이블로 바꾸고 결정에 버전을 남긴다. 또는 스냅샷 복사. 규칙 변경 = 새 버전 추가, 덮어쓰기 금지([23](../23-versioned-rules-and-effective-dating/2-summary.md)).

### 4. 변조가 없는데 해시 검증이 전부 실패한다

- 현상: 감사 점검 배치가 어느 날부터 전체 행을 "변조"로 보고한다.
- 보이는 형태: 깨진 행 = 전체 행. 배치 서버나 DB 세션 설정이 바뀐 시점과 겹친다.
- 원인: 해시 입력이 세션 설정(시간대·로캘·숫자 표기)에 따라 달라지는 텍스트였다. 실험에서 `TimeZone`만 바꿔도 100/100.
- 대처: 해시 입력 정규화(UTC·고정 스케일·고정 키 순서). 검증 절차가 세션 설정을 명시한다.

### 5. 결정 기록이 빠진 거래가 있다

- 현상: 일부 주문에 결정 레코드가 없다.
- 원인: 결정 기록을 비동기(로그·메시지)로 썼거나, 주문과 다른 트랜잭션에서 썼다.
- 대처: 같은 트랜잭션에 쓴다. 위 "결정 기록이 없는 업무 행" 쿼리를 정기 점검으로 둔다.

## 핵심 문장

- 결정 기록 = 입력 스냅샷(또는 불변 참조 + 버전) + 규칙 ID·버전 + 중간 산출 + 결과 + 결정 시각, 한 레코드, 고치지 않음.
- 참조만 남기면 참조 데이터가 바뀌는 순간 재현이 깨진다 — 실험에서 100건 중 40건이 다른 값을 냈고, 스냅샷 + 버전은 0건.
- "왜 이 값인가"는 로그를 grep해서 답하는 것이 아니라, 업무 트랜잭션 안에 남긴 근거 한 행으로 답한다.
- 재현 가능성 테스트("같은 입력으로 다시 계산하면 같은가")를 배포 전후로 돌린다. 재현은 계산이 순수 함수일 때만 성립한다.
- 해시 체인은 고정점 없이는 전체 재계산을 못 잡고, 입력을 정규화하지 않으면 변조 없이도 깨진다(세션 시간대만 바꿔도 100/100).

## 관련 주제·근거

- 선행: [08-domain-services-and-policies](../08-domain-services-and-policies/2-summary.md) · [09-domain-events](../09-domain-events/2-summary.md) · [distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md)(입력을 불변 이벤트로)
- 함께: [reliability/18-logs-traces-audit-roles](../../reliability/18-logs-traces-audit-roles/2-summary.md)(로그 vs 감사, 해시 체인 기초 실험) · [11-state-machines-in-domain](../11-state-machines-in-domain/2-summary.md)(전이 이력) · [21-cqrs](../21-cqrs/2-summary.md)(결정적 폴드·재구축) · [software-design/47-architecture-decision-records](../../software-design/47-architecture-decision-records/2-summary.md)(이름은 비슷하지만 **설계** 결정의 문서다. 이 노트는 **도메인 계산** 결정의 데이터다)
- 후속: [23-versioned-rules-and-effective-dating](../23-versioned-rules-and-effective-dating/2-summary.md) · [24-double-entry-ledger](../24-double-entry-ledger/2-summary.md) · [25-reconciliation](../25-reconciliation/2-summary.md)
- 근거
  - W3C, "PROV-DM: The PROV Data Model", W3C Recommendation 2013-04-30 — https://www.w3.org/TR/prov-dm/ (provenance·Entity·Activity·Agent·관계 정의 원문 확인)
  - Kleppmann, 『Designing Data-Intensive Applications』 1판(2017) 12장 "The Future of Data Systems" > "Trust, but Verify" > "Designing for auditability" — 요지는 발췌(ebrary 등)로 확인, 본문 전체 미열람
  - PostgreSQL 17 문서 9.5 Binary String Functions(`sha256`) · 8.14 JSON Types(`jsonb`는 키 순서·중복 키를 보존하지 않음) · 8.5.1.3 Time Stamps(`timestamptz` 출력은 세션 `TimeZone` 기준)
- 실험 목록
  - 참조만 vs 스냅샷 + 규칙 버전, 참조 데이터 변경 후 재계산 불일치 수: PostgreSQL 17.11 `psql`, 일회용 컨테이너
  - SQL 해시 체인: 단일 행 변조 탐지, 전체 재계산 후 체인 OK, 외부 머리 해시 비교: 같은 환경
  - 세션 `TimeZone` 변경 시 해시 검증 100/100 실패: 같은 환경
