# cs/issue/database/transaction-boundary-scope — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
트랜잭션 경계 = "함께 성공하거나 함께 실패하는" 범위

[너무 넓다]  BEGIN ─ nodes×224 ─ edge#1 ✗ ─ rollback ─ edge#2..(FK ✗) ─ COMMIT(빈 트랜잭션)
             → 한 건 실패가 이미 넣은 전부를 되돌림, 에러 없이 0건

[쪼갰다]     주문 tx ──▶ [queue] ──▶ 결제 tx ✓ ──▶ 후속 tx ✗
             → 부분 성공(결제만 완료) 상태가 남음

[밖에 있다]  BEGIN ─ save ─ cache.clear() ─ ... ─ COMMIT(프록시 반환 시)
                                ↑ 커밋 전 무효화: 동시 요청이 옛 DB 로 재적재 / 롤백 시 캐시만 비워짐
             BEGIN ─ file.write ─ insert ─ COMMIT ✗   → 메서드 내 보상은 이미 지나감 → 고아 파일
             token.consume(외부 저장소) ─ BEGIN ─ findUser ✗ ─ ROLLBACK  → 토큰만 소실
             db.insert ─ publish ✗ (또는 반대)         → 둘 중 하나만 성공

[교정]
 넓다   → 실패 격리 단위로 경계를 좁힘(문장 단위) + 쓰기 전 정규화 + 마지막에 count 재조회
 쪼갰다 → 한 비즈니스 단위를 한 소비자 트랜잭션으로(202 즉시 응답 + 결과 통지)
 밖     → rollbackFor 명시 · 부수효과는 커밋 이후(afterCommit) · 외부 소비는 뒤로
          발행은 outbox: DB insert(pending) 를 같은 트랜잭션에 → 워커가 읽어 발행 → published
```

## 핵심 문장

- **제약 위반의 비용은 트랜잭션 경계가 정한다.** 넓은 경계에서의 rollback 은 이미 넣은 전부를 되돌린다.
- "에러 없이 commit" ≠ "데이터 적재" — 마지막에 **count 재조회**로 확인한다.
- 한 비즈니스 단위를 메시지 경계로 쪼개면 각 조각이 **별도 트랜잭션**이 되어 부분 성공이 가능해진다.
- (Spring) 선언적 트랜잭션은 기본적으로 **unchecked 예외(RuntimeException·Error)만** 롤백하고, 커밋은 **메서드 반환 후** 프록시에서 일어난다.
- 트랜잭션 밖 부수효과(캐시·파일·외부 저장소·발행)는 커밋 결과와 **자동으로 동기화되지 않는다** → 커밋 후 실행 또는 outbox.
- 저장 없는 Pub/Sub(이 사례: Redis Pub/Sub)은 그 순간의 구독자에게만 전달한다 — 구독자가 없던 동안의 메시지는 사라진다(보존형 Pub/Sub 제품도 있음).
