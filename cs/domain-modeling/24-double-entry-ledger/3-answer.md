# domain-modeling/24-double-entry-ledger — 정답

## 정답

### 1. 잔액 열만 있으면 답하지 못하는 질문

- 답하지 못하는 질문: "왜 이 금액인가", "어제(과거 시점) 잔액은 얼마였나", "누가 언제 무엇을 바꿨나", "틀렸던 값은 무엇이었고 언제 고쳤나".
- `UPDATE`는 결과만 남기고 근거를 덮어쓴다.
- 원장은 이동을 분개로 쌓는다. 잔액은 분개의 합(폴드)이다.
  - 과거 잔액 = 그 시점까지의 분개 합.
  - 근거 = 분개를 묶은 전표(사건·메모·멱등키·역분개 대상).

### 2. 충전 전표

```text
  계정            차변(Dr)   대변(Cr)
  cash             10,000              ← 자산(debit normal) 증가
  wallet:alice                10,000   ← 부채(credit normal) 증가
  저장: posting(cash, +10000), posting(wallet:alice, −10000)  → 합 0
```

- 회사 장부에서 고객 지갑은 회사가 갚아야 할 돈(부채)이다. credit normal 계정이다.
- 그래서 wallet:alice 잔액 = −(분개 합) = −(−10,000) = 10,000으로 읽는다.
- 고객 장부라면 지갑은 자산이다. 장부의 주인을 먼저 정해야 부호가 정해진다.

### 3. 검사 시점

- 분개를 한 줄씩 넣으면 첫 줄을 넣은 직후 합은 +10,000이다. 문장마다 검사하면 정상 전표도 첫 줄에서 거절된다.
- 그래서 트랜잭션 끝(커밋 시점)에 검사한다.
- PostgreSQL 17: `CREATE CONSTRAINT TRIGGER … AFTER INSERT ON posting DEFERRABLE INITIALLY DEFERRED FOR EACH ROW`.
  - 문서(CREATE TRIGGER): 제약 트리거는 `AFTER ROW`여야 하고, 트랜잭션 끝에 실행하면 deferred라 부른다.
- 트리거 함수에는 `SET search_path`를 명시한다. 실험에서 빠뜨리자 다른 search_path 세션의 커밋이 전부 실패했다.

### 4. id가 1, 4, 5인 이유

- 불균형 전표(2)는 커밋에서 거절되어 롤백됐다. 재전송(3)은 `ON CONFLICT DO NOTHING`으로 버려졌다.
- 두 경우 모두 `nextval`이 이미 값을 가져갔다. PostgreSQL 문서(9.17)는 `nextval`이 롤백되지 않는다고 적는다.
- 빈 번호는 정상 동작의 흔적이다. 번호 연속성으로 누락을 판단하면 안 된다.
- 누락은 원천 사건과의 대조(대사)로 찾는다.

### 5. 동시 이체 세 경우 (PostgreSQL 17.11 실험)

| 경우 | 결과 | 잔액 |
|---|---|---|
| ① 잠금 없음 | 둘 다 9,000을 보고 둘 다 OK | −3,000 |
| ② FOR UPDATE + READ COMMITTED | 하나 OK, 하나 REJECTED (balance 3000) | 3,000 |
| ③ FOR UPDATE + REPEATABLE READ | 둘 다 OK (saw balance 9000) | −3,000 |

- ②: 뒤 요청이 잠금을 기다린다. READ COMMITTED는 명령마다 새 스냅샷이라, 다음 SELECT가 앞 요청의 커밋된 분개를 본다(13.2.1).
- ③: REPEATABLE READ는 트랜잭션 첫 문장 시점의 스냅샷을 끝까지 쓴다(13.2.2). 잠금을 얻은 뒤에도 앞 요청의 분개가 안 보인다.
  - 잠근 account 행은 아무도 고치지 않았다. 그래서 직렬화 오류도 나지 않는다.
- 해법(실험): 잔액 캐시 열을 `UPDATE … WHERE cached_balance >= amt`로 갱신한다. RC에서는 WHERE 재평가로 거절, RR에서는 `could not serialize access due to concurrent update`로 실패 → 재시도.

### 6. 균형이 맞은 채로 생기는 사고

| 사고 | 왜 균형 검사가 못 보나 | 막는 것 |
|---|---|---|
| 같은 요청이 전표 두 개 | 두 전표 각각 합 0 | 멱등키 UNIQUE |
| 전표 누락(사건은 있었는데 기록 없음) | 없는 전표는 검사 대상이 아니다 | 원천·외부와의 대사, 아웃박스(reliability/04 F-23) |
| 잔액 음수(초과 출금) | 두 이체 전표 모두 합 0 | 잔액 조건부 UPDATE·CHECK 제약 |

- 빈 전표(분개 0줄)도 행 트리거를 통과한다. "분개 2줄 이상"은 생성 코드나 점검 쿼리로 막는다.

### 7. 정정 전표

- 두 개를 넣는다.
  1. 역분개: 원 전표와 부호만 반대(cash −10,000 / wallet:alice +10,000), `reverses = 1`.
  2. 재분개: 올바른 금액(cash +9,000 / wallet:alice −9,000).
- 이것은 Fowler의 Reversal Adjustment다 — 틀린 거래는 그대로 두고 반대 분개로 상쇄한다.
- Difference Adjustment: 차이(−1,000)만 한 전표로 넣는다. 전표 수는 적지만 "원래 맞는 값"이 한 전표에 드러나지 않는다.
- Replacement Adjustment: 틀린 거래를 지우고 다시 쓴다. Fowler는 회계 틀 안의 이력이 사라진다고 적는다(Parallel Model로 재구성은 되지만 덜 직접적). append-only 원장에서는 쓰지 않는다.

### 8. 원장이 비었다

- `TRUNCATE`는 행 단위 DELETE 트리거를 실행하지 않는다. 실험에서 `TRUNCATE led.posting CASCADE`가 그대로 성공해 0행이 됐다.
- 더할 것: `BEFORE TRUNCATE … FOR EACH STATEMENT` 트리거(PostgreSQL 17 문서: TRUNCATE 트리거는 statement 단위만). 추가 후 실험에서 거절됐다.
- 함께 둘 방어선:
  - 애플리케이션 역할에서 UPDATE·DELETE·TRUNCATE 권한 회수(`REVOKE`). 소유자·슈퍼유저는 트리거를 끌 수 있다.
  - 백업·복제, 그리고 시산표·외부 대사로 이상을 빨리 안다.

### 9. COMMIT이 느릴 때

- 지연 트리거는 분개 한 줄마다 "그 전표의 분개 합"을 조회한다. 먼저 `posting(entry_id)` 인덱스가 있는지 본다.
- 실험(`--cpus=2`, 3회): 인덱스 없음 — 전표 2,000개 커밋 2,412~3,472ms, 4,000개 14,307~19,536ms(회차마다 약 5.5~5.9배). 인덱스 있음 — 92~174ms, 157~309ms.
- 줄마다 테이블 전체를 읽어 대략 제곱으로 자란다(해석). 수치는 제한 환경의 값이다.

### 10. 파생값 대조

- 주기적으로 대조할 것:
  - 시산표: 전체 `sum(amount) = 0`, 불균형 전표 0건, 분개 2줄 미만 전표 0건.
  - 캐시 잔액 = 원장 합(계정별).
  - 스냅샷 + 이후 분개 = 전체 합(실험: 2,068,997 = 2,068,997).
- 캐시·스냅샷이 원장과 다르면 원장을 믿고 캐시를 다시 만든다. 원장을 캐시에 맞추지 않는다.
- 외부(PG·은행) 기록과의 대조는 [25-reconciliation](../25-reconciliation/2-summary.md)이다. 원장은 내부 일관성을, 대사는 바깥 세계와의 일치를 본다.
