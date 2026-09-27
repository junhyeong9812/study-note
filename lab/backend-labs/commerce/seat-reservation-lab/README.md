# 01. Seat Reservation Lab

동시접속 20만 명, 10,000석 환경에서 발생하는
좌석 경합 / 선점 만료 / 트래픽 폭주 / 조회-예약 불일치를 다룬 실험 프로젝트

## Load Baseline (근거)

| 사례 | 관찰된 수치 | 출처 |
|------|-----------|------|
| 소형 공연 (1,500석) | 예매 시작 5분 내 전석 매진 | [뉴스핌](https://www.newspim.com/news/view/20260922000268) |
| 스타디움 3회차 공연 | 순간 동접 21만 명 이상, 일반 예매 22분 만에 매진 | [TV리포트](https://v.daum.net/v/20260626124216017) |
| 초대형 내한공연 | 최대 동접 약 130만 명, 35분 만에 매진 | [뉴스1](https://m.news.nate.com/view/20260521n29892) |
| 글로벌 최대 사례 | 하루 35억 건 요청, 이전 피크의 4배 | [Ticketmaster](https://business.ticketmaster.com/press-release/taylor-swift-the-eras-tour-onsale-explained/) |

> 동접 수치는 대기열 대기 인원을 포함한 접속자 수이며, 초당 요청 수가 아니다.
> 국내 예매사는 측정 방식을 공개하지 않으므로 규모감 참고용으로만 사용한다.

**채택 기준 (스타디움 사례 모델)**: 좌석 10,000석, 피크 동접 200,000명, 경쟁률 약 20:1, 20분 내 매진

## Questions

1. 같은 좌석을 1,000명이 동시에 눌렀다면?
2. 2연석 중 1석만 선점에 성공했다면?
3. 좌석을 선점해놓고 결제 없이 떠났다면?
4. 오픈 정각에 20만 명이 동시에 들어왔다면?
5. 화면엔 빈자리였는데 누르니 이미 팔렸다면?
6. 결제는 성공했는데 그 사이 선점이 만료됐다면?
7. 테스트가 끝났을 때 좌석 상태는 정말 정확한가?

## Architecture

```
Client
  ↓
Queue Server (Redis Sorted Set)
  ↓ 입장 토큰 (초당 N명)
Reservation API
 ├── Seat Map Query ── Cache
 └── Seat Hold ─────── Redis SET NX EX / DB Lock
        ↓
      Hold Expiry ── 만료 시 좌석 반환
        ↓
Payment (→ 02. Payment Consistency Lab)
  ↓
Reservation Confirm

Verification Batch → Seat state consistency check
```

## Load Profile

| 항목 | 값 |
|------|---|
| 좌석 | 10,000석, 1인 최대 2매 (예상 주문 약 5,000~6,000건) |
| 피크 동접 | 200,000명 |
| 대기열 입장 속도 | 100 / 300 / 1,000 명/s (변수) |
| 선점 TTL | 5분 |
| 결제 이탈률 | 0% / 20% / 50% (변수) |
| 좌석 선호 분포 | 균등 vs 앞 20% 구역에 요청 70% 집중 (핫스팟) |
| 연석 비율 | 1석 60% / 2연석 40% |

**트래픽 구간**

| 구간 | 시간 | 특징 |
|------|------|------|
| 오픈 스파이크 | 0~2분 | 대기열 진입 폭주, 좌석 경합 최대 |
| 소진 구간 | 2~20분 | 선점 경쟁 + 이탈 좌석 재경쟁 |
| 잔여석 구간 | 20~30분 | 만료·취소로 풀린 좌석을 노리는 롱테일 |

## Results

| # | Question | 시도한 방식 | 측정 결과 | 최종 선택 | 선택 이유 / 감수한 단점 |
|---|----------|------------|----------|----------|----------------------|
| 1 | 동일 좌석 1,000명 동시 요청 | | | | |
| 2 | 연석 부분 선점 | | | | |
| 3 | 선점 후 결제 이탈 | | | | |
| 4 | 오픈 정각 20만 명 유입 | | | | |
| 5 | 좌석맵 조회 ↔ 실제 상태 불일치 | | | | |
| 6 | 결제 성공 + 선점 만료 | | | | |
| 7 | 종료 후 좌석 상태 정합성 | | | | |

## Load Test Results

| 락 방식 | 입장 속도(명/s) | 이탈률 | TPS | p99 | 에러율 | 매진 시간 | 중복 예약 |
|--------|---------------|-------|-----|-----|-------|---------|---------|
| | | | | | | | |
| | | | | | | | |

## Consistency Checks

| 검증 항목 | 기대값 | 실제값 | 통과 |
|----------|-------|-------|-----|
| RESERVED 좌석 수 | 10,000 | | |
| 동일 좌석 중복 예약 | 0 | | |
| 만료됐는데 HELD로 남은 좌석 | 0 | | |
| 결제 성공 건수 = 예약 확정 건수 | 일치 | | |

## Decisions (ADR)

- ADR-001:
- ADR-002:

---

## 작업 기록

### 2026-09-27 — ADR-000 기준선: 좌석 선점·확정·만료 (DDD 애그리거트, 동시성 제어 없음)
- 대응 질문: Q1 · Q3 · Q6 의 토대 (동시성 문제는 의도적으로 미해결 — 이후 ADR에서 관측·해결)
- 코드: seat-reservation-lab @ `add5330` (코드) · `ec80736` (ADR-000 + 가설 ADR-001~009 문서) — 브랜치 `feat/adr-000-baseline`
- 한 것:
  - 진행 방식 전환: 해법(락·조건부 쿼리)을 먼저 정한 ADR 초안을 버리고, **평범한 기준선 → k6로 문제 관측 → ADR마다 선택지 실험·실측**으로 바꿨다. 가설 ADR-001~009(판정 하네스·Q1~Q7·1인 2매·보상)를 미측정 상태로 먼저 깔아 둠.
  - 도메인: 상품 > 회차 > 좌석 + 홀드 + 예약(결제 uid). 판매 단위는 **회차의 좌석**. 좌석에 `AVAILABLE/HELD/RESERVED` 저장, 만료는 `@Scheduled` 배치(sweep) — 직관 모델로 시작해 만료 지연 문제를 ADR-004에서 관측하기로 함.
  - 애그리거트: Product · Schedule · **Seat(⊃ SeatHold)** · Reservation. 좌석 상태와 홀드는 항상 함께 바뀌므로 한 경계. 회차는 좌석을 품지 않음(품으면 모든 선점이 회차 하나를 두고 경합).
  - 애그리거트 하나로 못 지키는 규칙 2개: 확정(좌석 RESERVED + 예약 생성)은 **같은 트랜잭션**(RESERVED 수 = CONFIRMED 수를 원자적으로) — "트랜잭션당 애그리거트 1개"의 의도된 예외. 1인 2매는 도메인 서비스 `HoldLimitPolicy`(조회 후 비교).
  - 스키마(Flyway V1)는 PK/FK만 — 유니크·CHECK·인덱스를 두면 문제가 재현되지 않으므로 해결책 후보로 남김.
  - API: `POST /api/schedules/{id}/seats/{id}/hold`(201) · `POST /api/holds/{id}/confirm`(200, 결제 성공 후 호출) · 에러 409/404/403.
- 도식:

```
애그리거트 경계                                  상태 전이 (좌석)
┌─────────┐ ┌──────────┐ ┌─────────────────┐ ┌─────────────┐      선점              확정
│ Product │◀│ Schedule │◀│ Seat (루트)      │◀│ Reservation │   AVAILABLE ──▶ HELD ──────▶ RESERVED
└─────────┘ └──────────┘ │  status         │ │  paymentUid │       ▲         │  + 홀드 제거
                         │  └ SeatHold 0..1│ │  CONFIRMED/ │       └─────────┘  + 예약 CONFIRMED
                         │    user, 만료시각│ │  CANCELED   │     만료 배치(sweep)
                         └─────────────────┘ └─────────────┘     + 홀드 제거
    ◀ = 다른 애그리거트 루트를 ID로 참조

선점:  좌석 로드 → seat.assertHoldable() → HoldLimitPolicy(홀드+확정 < 2) → seat.hold() → flush
확정:  홀드 id로 좌석 로드 → seat.confirm() [내 홀드? 만료 전? 좌석 HELD?] → Reservation 저장 (같은 트랜잭션)
       ※ 모든 검사는 읽어 온 스냅샷 위의 비교(check-then-act) — 동시 요청에서 깨지는지는 ADR-002·003·005
```

- 확인:
  - 테스트 22개 green (Testcontainers PostgreSQL 통합 17 + 좌석 애그리거트 단위 5) — 단일 요청 기준 선점·확정·만료의 성공/거절과 거절 시 DB 불변.
  - 뮤테이션 점검: 선점 가능 검사 제거 → 5 red, 만료 경계(`isAfter`→`isBefore`) → 3 red, 에러 우선순위 뒤집기 → 1 red. 테스트가 실제로 계약을 잡는지 확인.
  - 실경로 스모크(`bootTestRun`, TTL 20s): 선점 201 → 다른 사용자 409 → 확정 200(좌석 RESERVED, 예약 CONFIRMED) / 선점 후 만료 3초 뒤 배치가 AVAILABLE로 복귀.
  - 부하·동시성: **미측정** (ADR-001 하네스부터).
- 막힌 것 / 틀렸던 가정:
  - 처음엔 "레이어드 + usecase가 리포지토리 직접 호출"을 DDD라고 여겼는데 실제로는 트랜잭션 스크립트 + 빈약한 도메인 모델이었다. 애그리거트 경계를 ADR-000에 먼저 명시하고, 특성테스트를 DB 수준으로 옮겨 green을 고정한 뒤 리팩토링.
  - 애그리거트가 규칙을 가져도 동시성은 해결되지 않는다 — 검사는 스냅샷 위에서 일어난다. 애그리거트는 "무엇이 일관돼야 하나", 락은 "동시에 어떻게 지키나".
  - Testcontainers 1.21.3이 Docker 29에서 연결 실패(API 1.32 vs 최소 1.44) → BOM 프로퍼티로 1.21.4.
  - 영속 좌석에 `saveAndFlush` → merge가 새 홀드의 복사본을 영속화해 원본 홀드 id가 null → `flush()`로 해결.
- cs/ 추출 후보:
  - [issue/cross-cutting/infra/client-api-version-floor](../../../../issue/cross-cutting/infra/client-api-version-floor/) (작성함)
  - [issue/kotlin/spring/jpa-save-merge-copy](../../../../issue/kotlin/spring/jpa-save-merge-copy/) (작성함)
  - 애그리거트 경계 = 트랜잭션·락 경계 (회차가 좌석을 품으면 경합 단위가 커진다) → domain-modeling 애그리거트 챕터
