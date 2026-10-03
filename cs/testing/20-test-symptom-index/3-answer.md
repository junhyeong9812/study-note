# testing/20-test-symptom-index — 정답

## 정답

### 1. 네 칸과 다섯 증상

| | 제품 동작이 맞다 | 제품 동작이 틀렸다 |
|---|---|---|
| 테스트 빨강 | **거짓 경보(거짓 양성)** — CI 가끔 실패, 리팩터링마다 대량 실패 | 제대로 잡음 |
| 테스트 초록 | 정상 | **놓침(거짓 음성)** — 초록인데 운영 장애, 커버리지 높은데 버그 |

- "테스트 느림"은 칸 밖의 비용이다. 느린 테스트는 덜 돌고, 덜 돌면 두 칸의 증상이 모두 늦게 드러난다.
- 용어는 Khorikov 4장을 따른다(02 노트).
- 처방이 반대인 이유
  - 거짓 경보는 테스트가 구현 세부·시간·순서에 **너무 묶여서** 생긴다. 처방은 관찰 가능한 결과로 옮기고, 숨은 입력을 고정하는 것이다.
  - 놓침은 테스트가 실제 실행 경로와 **너무 떨어져서** 생긴다. 처방은 실제 의존·인수 테스트·음성 테스트·경계값으로 현실에 붙이는 것이다.
  - 거짓 경보를 줄이려고 mock을 늘리면 놓침이 커지고([04-3](../04-classical-vs-london/2-summary.md)), 놓침을 줄이려고 E2E를 늘리면 느림과 불안정이 커진다([01-1](../01-why-test-and-pyramid/2-summary.md)).

### 2. "가끔 빨강"을 가르는 질문

| 질문 (싼 것부터) | 답이 "예"이면 | leaf |
|---|---|---|
| 단독 실행은 초록이고 전체 실행만 빨강인가? | 순서 의존 — 공유 정적 상태·픽스처·DB 행 | [09-3](../09-flaky-tests/2-summary.md) · [11-1](../11-test-data-and-fixtures/2-summary.md) · [11-5](../11-test-data-and-fixtures/2-summary.md) |
| 실패가 바쁜 러너·혼잡 시간대에 몰리나? | 고정 sleep·짧은 타임아웃 | [09-4](../09-flaky-tests/2-summary.md) · [10-1](../10-testing-time-and-concurrency/2-summary.md) · [18-3](../18-e2e-and-ui-testing/2-summary.md) |
| 실패가 특정 날짜·시각(말일·자정·DST)에 몰리나? | 시스템 시계 직접 읽기, 기대값을 `now()`로 재계산 | [10-2](../10-testing-time-and-concurrency/2-summary.md) |
| 병렬 실행을 켠 뒤부터인가? | 포트·파일·DB 행 같은 외부 자원 공유 | [09-5](../09-flaky-tests/2-summary.md) |

- 위 넷이 모두 아니면 무작위 입력([14-3](../14-property-based-testing/2-summary.md)), 공유 환경([18-4](../18-e2e-and-ui-testing/2-summary.md)), 그리고 **제품 코드의 경쟁 조건**([09-1](../09-flaky-tests/2-summary.md), [10-4](../10-testing-time-and-concurrency/2-summary.md))을 본다.
- 어느 경우든 재시도로 덮지 않는다.

### 3. 반복 실행 확률

- 20번 모두 초록일 확률 = (1 − 0.05)^20 ≈ **0.358**. 20번 초록이어도 셋 중 하나꼴로 결함이 숨어 있다.
- 95% 확률로 최소 한 번 실패를 보려면 (1 − p)^n ≤ 0.05 → n ≥ ln 0.05 / ln 0.99 ≈ 298.1 → **299번**.
- 같은 식으로 p = 10%면 29번, 5%면 59번이다.
- 그래서 "몇 번 돌려 봤는데 괜찮다"는 실패 확률이 클 때만 증거가 된다.

### 4. `Flakes: 1`인데 `BUILD SUCCESS`

- 의심: 테스트가 불안정한 것이 아니라 **제품 코드가 불안정**하다. 동기화 없는 공유 상태(경쟁 조건)가 가장 먼저 의심된다([09-1](../09-flaky-tests/2-summary.md)).
- 09 실험 C(Maven 3.9.16 · surefire 3.5.3 · JUnit 5.13.4, 동기화 없는 카운터)
  - 재시도 없이 12번 중 9번 실패했다(`expected: <2000> but was: <1607>`, `<1401>` — 실패 값이 매번 다르다).
  - `-Dsurefire.rerunFailingTestsCount=3`을 붙이자 6번 모두 `BUILD SUCCESS`, 그중 4번이 `Flakes: 1`이었다(사실 점검 재실행에서는 6번 모두 `Flakes: 1` — 실행마다 다르다).
- 문제를 키운 이유: 재시도는 빨강을 경고로 낮춘다. 운영의 합계 불일치라는 진짜 결함의 유일한 신호가 사라졌다.
- 대처: `Flakes`를 실패처럼 수집하고, `failOnFlakeCount`(surefire 3.0.0-M6+)로 상한을 건다. 재시도 없이 반복 실행해 실패 비율을 잰다.

### 5. 대량 실패 — 호출 단언 vs 값 단언

- (가) `Wanted but not invoked`: 테스트가 내부 협력 객체 호출에 묶였다 — **거짓 경보**일 가능성이 크다([02-1](../02-good-unit-tests/2-summary.md), [04-1](../04-classical-vs-london/2-summary.md)). 02 실험에서 세부 검증 판은 동작 보존 리팩터링 R1에서 컴파일 실패 2개, R2에서 실패 1개였고, 결과 검증 판은 둘 다 0개였다.
  - 처방: 단언을 관찰 가능한 결과로 옮긴다. mock은 프로세스 밖 명령에만 남긴다.
- (나) 여러 모듈의 값 단언이 동시에: 그 테스트들이 함께 실행하는 공용 객체에 **진짜 회귀**가 있을 수 있다([04-3](../04-classical-vs-london/2-summary.md)).
  - 단, `0L`이 stub하지 않은 mock 메서드의 기본값이라면 (가) 쪽이다(04 실험 R2: 위임만 바꿨는데 런던파 테스트 2개가 `expected: 90000L but was: 0L`). 실패 테스트의 SUT가 mock을 거쳐 값을 받는지 확인한다.
- (나)를 거짓 경보로 처리해 기대값을 새 출력에 맞추면, 회귀를 정답으로 고정하고 배포한다(장애 시나리오 2, 같은 구조: [05-1](../05-tdd/2-summary.md)).

### 6. `25P02` — 테스트는 H2

- 08 실험(H2 2.5.252 PostgreSQL 모드 vs PostgreSQL 17.11): 중복 키 오류를 잡고 같은 트랜잭션을 계속 쓰는 코드가 H2에서는 `committed [1, 2]`로 성공했다. PostgreSQL에서는 `SQLException 25P02: ERROR: current transaction is aborted, commands ignored until end of transaction block`이었다.
- 첫 질문: **테스트 DB 엔진이 운영과 같은가?**
- 처방
  - 리포지토리·트랜잭션 테스트를 운영과 같은 엔진(Testcontainers)으로 옮긴다([08-1](../08-integration-tests-real-dependencies/2-summary.md)).
  - 오류를 삼키고 계속하는 코드를 `ON CONFLICT DO NOTHING`·세이브포인트로 바꾼다.
- 같은 갈래: 락 실패 코드가 H2 `HYT00`, PostgreSQL `55P03`으로 달라 재시도 분기가 운영에서만 다른 길을 탄다([08-2](../08-integration-tests-real-dependencies/2-summary.md)).

### 7. "초록인데 운영 장애"의 갈래

| 갈래 | 대표 leaf |
|---|---|
| 대역이 실제와 다르게 답함(stub 계약 불일치) | [03-2](../03-test-doubles/2-summary.md) |
| 실제 조립이 한 번도 안 돎 | [06-1](../06-outside-in-tdd-and-acceptance-tests/2-summary.md) |
| 테스트 DB·환경이 운영과 다름 | [08-1](../08-integration-tests-real-dependencies/2-summary.md) |
| 서비스 사이 약속 변경 | [13-1](../13-contract-testing/2-summary.md) |
| 정답을 구현에서 베낌 | [05-1](../05-tdd/2-summary.md) |
| 단언이 실행되지 않음·실패를 삼킴 | [12-3](../12-test-smells-and-xunit-patterns/2-summary.md) · [06-4](../06-outside-in-tdd-and-acceptance-tests/2-summary.md) |
| 입력이 버그 영역에 닿지 않음(경계·금지 전이·분포) | [07-1](../07-test-design-techniques/2-summary.md) · [07-3](../07-test-design-techniques/2-summary.md) · [14-1](../14-property-based-testing/2-summary.md) |
| 운영에서만 보이는 것(설정·트래픽) | [19-1](../19-testing-in-production/2-summary.md) |

- 공통 첫 질문: **"그 경로를 진짜로 실행한 테스트가 있었나?"** 대역·H2·테스트 설정이 실행한 것은 운영이 실행한 것이 아니다.

### 8. 같은 커버리지, 다른 변이 점수

- 다를 수 있다. 15·16 실험(JUnit 5.13.4 · JaCoCo 0.8.14 · PIT 1.20.4)에서 NoAssertTest와 StrongTest는 둘 다 JaCoCo 라인 4/4·분기 8/8이었다.
  - NoAssertTest: `>> Generated 14 mutations Killed 1 (7%)`.
  - StrongTest: `>> Generated 14 mutations Killed 14 (100%)`.
- 커버리지는 코드가 **실행됐나**를 잰다. 단언이 없어도 실행만 하면 오른다.
- 변이 점수는 코드를 일부러 틀리게 바꿨을 때 테스트가 **알아채나**(판별력)를 잰다.
- 그래서 "커버리지 높은데 버그"의 첫 진단은 변이 테스트와 단언 없는 테스트 검색이다([15-1](../15-mutation-testing/2-summary.md), [16-1](../16-coverage-and-its-limits/2-summary.md)).

### 9. 지표를 게이트로 걸었을 때

| 게이트 | 생기는 증상 | 근거 |
|---|---|---|
| 커버리지 80% | 단언 없는·`assertNotNull`뿐인 테스트 양산. 수치는 오르는데 결함 유출은 그대로 | [16-1](../16-coverage-and-its-limits/2-summary.md) — 실험 NoAssertTest: 커버리지 100%, 변이 7% |
| 변이 점수 100% | 등가 변이체는 어떤 테스트로도 못 죽인다 → 몇 달째 통과 못 하거나 억지 테스트 | [15-3](../15-mutation-testing/2-summary.md) — 실험 `abs`: 5개 중 4개 Killed, 80%에서 멈춤 |
| 카나리 오류율 > 기준 | 같은 판끼리도 우연한 차이로 "실패" → 팀이 판정을 건너뜀 | [19-3](../19-testing-in-production/2-summary.md) — 실험: 같은 판에서 순진 규칙 40~53% 실패, 통계 판정은 4.7~6.5% |

- 공통 원인: 측정이 목표가 되면 측정을 맞추는 행동이 나온다(굿하트). 지표는 "어디를 볼지" 정하는 데 쓰고, 게이트는 변경분·사람 검토·통계 판정처럼 우연을 거르는 형태로 건다(장애 시나리오 5).

### 10. 실패 위치 ≠ 원인 위치

- 착각: 실패한 `nothingReservedYet`은 **피해자**다. 원인은 앞서 실행된 `reserveFour`·`reserveFive`가 남긴 공유 상태(**오염자**)다([11-1](../11-test-data-and-fixtures/2-summary.md), [09-3](../09-flaky-tests/2-summary.md)).
- 11 실험 A(JUnit 5.13.4): 공유 픽스처 판은 무작위 순서 20회 중 12회 실패했고, `nothingReservedYet`이 맨 앞일 때(8회)만 통과했다. 테스트마다 새 픽스처를 만든 판은 0회 실패.
- 순서
  1. 단독 실행(초록)과 전체 실행(빨강)을 비교해 순서 의존임을 확인한다.
  2. 무작위 순서 + 시드 고정(`junit.jupiter.execution.order.random.seed`)으로 실패를 재현한다.
  3. 피해자 앞에 돈 테스트 집합을 반으로 나눠 이분 탐색으로 오염자를 찾는다.
  4. 공유 가변 상태를 테스트마다 새로 만들거나(`@BeforeEach`) 불변으로 만든다. 같은 재현 명령으로 실패 0을 확인한다.
