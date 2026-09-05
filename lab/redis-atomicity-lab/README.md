# redis-atomicity-lab — "Lua Script 없이는 원자성이 보장되지 않는다"를 수치로 증명하려는 설계

- 원본: `/home/jun/project/redis-atomicity-lab` · 기간: 2026-01-21 (git 커밋 기준, 단일 세션) · 스택: Java 21 + Spring Boot 3.5.0, Spring Data Redis, Redisson, Nginx, Docker Compose, k6
- 상태: **설계 완료 · 실험 미실행** — 개념 문서 5편 + 시나리오 설계 4편 + 구현 코드(서비스 4종·k6 스크립트 4종)는 존재하지만, `docs/results/` 는 **비어 있고 실측 결과 문서가 없다**. 아래 수치는 전부 **예상값**이다.

## 무엇을 알고 싶었나 — 질문·가설

Redis 는 단일 명령은 원자적이지만, **여러 명령의 조합(GET 후 SET)은 원자적이지 않다.** 다중 API 서버가 하나의 Redis 를 공유할 때 이 틈에서 동시성 사고가 실제로 얼마나 나는지, 그리고 INCR / WATCH+MULTI / Lua Script / Redisson Lock 이 각각 무엇을 얼마의 비용으로 막아주는지를 k6 부하로 측정하려는 설계.

측정하려던 지표: Lost Update Rate · Race Condition Rate · Data Inconsistency Rate (정합성) / TPS · p50/p95/p99 · Retry Rate (성능).

## 실험 환경과 방법 (설계)

```
┌─────────┐     ┌─────────┐
│ API 서버1│     │ API 서버2│
└────┬────┘     └────┬────┘
     └───────┬───────┘
      ┌──────┴──────┐
      │    Nginx    │  (Load Balancer)
      └──────┬──────┘
      ┌──────┴──────┐
      │    Redis    │  (Single Instance)
      └─────────────┘
```

- API 서버 2대 + Nginx LB + 단일 Redis (Docker Compose) — 서버 2대여야 요청이 진짜로 인터리빙된다.
- 방식별 구현이 서비스 클래스로 분리됨: `NonAtomicService`(GET→SET) / `AtomicCommandService`(INCR·DECR) / `LuaScriptService` / `RedissonLockService`.
- 절차: 초기값 설정 → 동시 N개 요청(k6) → 최종값을 기대값과 비교 → 오류율 = (기대값−실제값)/기대값.

## 시나리오 설계 4종과 예상값 (⚠️ 전부 예상 — 실측 아님)

### 시나리오 1 — Read-Modify-Write (증가 연산, 재고 차감·좋아요 수)

동시 1,000회 증가 요청 시 **예상**:

| 방식 | 기대값 | 예상 실제값 | 예상 오류율 |
|------|--------|------------|------------|
| Non-Atomic (GET→SET) | 1000 | 847 (153개 유실) | 15.30% |
| INCR | 1000 | 1000 | 0.00% |
| Lua Script | 1000 | 1000 | 0.00% |

출처(예상값): `/home/jun/project/redis-atomicity-lab/docs/scenarios/01-read-modify-write.md` §예상 결과

### 시나리오 2 — Check-Then-Act (조건부 차감)

초기 재고 100 · 요청 200 시 **예상**: Non-Atomic → 최종 재고 **−23 (음수 재고)** / Lua Script → 0 (정상, 한도에서 정확히 멈춤).

출처(예상값): `docs/scenarios/02-check-then-act.md` §예상 결과

### 시나리오 3 — 복합 연산 (송금: A 차감 + B 증가)

기대 A=0, B=10000, 총합 10000 에 대해 **예상**: Non-Atomic → A=2300, B=5400, **총합 7700 (2,300원 증발)** / Lua Script → 총합 10000 정확.

출처(예상값): `docs/scenarios/03-multi-key-transaction.md` §예상 결과

### 시나리오 4 — 분산 락 (Double Booking, 좌석 예약)

100명 동시 예약 시도 시 **예상**: Redisson Lock → 정확히 1명만 성공. Lua Script vs Redisson 비교 축(속도·재진입·Watch Dog)도 설계에 포함.

출처(예상값): `docs/scenarios/04-distributed-lock.md` §예상 결과

## 종합 결론 (설계 시점의 예상 결론 — 실측 검증 안 됨)

원본 README 의 "결론 예상" 그대로:

- 단일 키 단순 연산 → INCR/DECR 로 충분
- 조건부 연산 → Lua Script 필수
- 복합 연산 → Lua Script 필수
- 분산 락 → Redisson 또는 Lua Script

설계 자체에서 얻은 것:

- 동시성 사고 4대 패턴(Lost Update / Check-Then-Act / 다중 키 불일치 / Double Booking)을 각각 재현 가능한 시나리오로 분해한 프레임.
- 방식별 트레이드오프 정리 — WATCH+MULTI 는 "낮은 오류율 + 재시도 필요"(△), MULTI/EXEC 는 트랜잭션 내 원자성만, SETNX 는 락 해제 문제.

## 한계·남은 질문

- **실험이 실행되지 않았다.** 위 수치("847", "−23", "총합 7700" 등)는 시나리오 문서에 적힌 예상 시나리오이며 실측이 아니다. 오류율 15.30% 같은 구체 수치도 예시로 만든 값.
- Non-Atomic 의 실제 오류율이 예상 범위(10~30%)에 들어오는지, 부하·서버 수에 따라 어떻게 변하는지 미확인.
- WATCH+MULTI 의 Retry Rate, Redisson 의 락 오버헤드(TPS·지연) — 측정 지표로 설계만 되고 값 없음.
- `docs/results/` 디렉토리는 존재하나 비어 있음.

## 원본 문서 지도

| 문서 | 내용 |
|------|------|
| `README.md` | 실험 목표·구성도·시나리오 요약·예상 결과 |
| `docs/concepts/01-redis-basics.md` | Redis 기초 (싱글 스레드 모델 등) |
| `docs/concepts/02-atomicity-and-concurrency.md` | 원자성·동시성 이론 |
| `docs/concepts/03-lua-script.md` | Lua Script 가이드 |
| `docs/concepts/04-distributed-lock.md` | 분산 락 이론 |
| `docs/concepts/05-redisson.md` | Redisson (tryLock·Watch Dog) |
| `docs/scenarios/01~04-*.md` | 시나리오 설계 4편 — 문제 상황·테스트 방법·**예상** 결과 |
| `docs/results/` | (비어 있음 — 실측 결과 없음) |
| `src/.../service/*.java` · `k6/scripts/*.js` | 방식별 구현 4종 + 시나리오별 부하 스크립트 4종 (실행 준비 상태) |
