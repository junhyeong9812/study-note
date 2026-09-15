# issue6 — 배포 창 락: 남의 락을 풀 수 없게

- 원본 PR: infra #16 · devlog: `jun-bank/infra/docs/devlog/pr-16-window-lock.md`

## 1. 무엇이 문제였나

DB에는 락 전이 프로시저(S0에서 세운 일곱 전이)가 있는데, Go에서 부르는 코드가 없었다 — 공백 메우기 작업이었다.

> **배포 창 락(window lock)** — 한 시점에 한 주체만 배포 창을 점유하게 하는 잠금.\
> 예: lease(임차 기간)가 만료되기 전까지 점유자만 배포를 진행하고, 점유자가 바뀔 때마다 fencing token을 하나 올려 "옛 점유자의 지연된 명령"을 무효로 만든다.

락의 계약은 "조회가 아니라 획득"이다.\
점유자가 없거나 lease가 만료됐을 때만 내 식별자·새 fencing token·새 lease로 바꾸는 조건부 UPDATE 하나이고, 영향 행 1이면 획득, 0이면 거절이다.

배선의 기술적 난점은 MySQL OUT 파라미터였다.\
세션 변수로 받아야 하는데 세션 변수는 커넥션 로컬이라, 커넥션 풀 위에서 CALL과 SELECT가 다른 커넥션으로 흩어지면 값이 조용히 어긋난다 — `callProc` 헬퍼가 두 문장을 하나의 고정 커넥션에 묶는다.

초기 배선을 실 MySQL에 익스플로잇해 검증하자, "획득"이어야 할 계약이 코드에서 서 있지 않은 세 자리가 드러났다.\
반대 계정이 남의 락을 release할 수 있었고, 0초·음수 lease가 즉시 만료된 무보호 락을 "획득 성공"으로 냈으며, 미지 kind·NONE kind로 유령 락이 생겼다.

## 2. 무엇을 고민했나

- **kind를 인자로 받는 공유 프로시저에 각 계정이 EXECUTE를 가질까, 역할별 wrapper로 나눌까.** — wrapper/impl 분리를 택했다.\
  공유 프로시저에 EXECUTE를 주면, 커트오프 계정이 kind 인자만 바꿔 AGENT 락을 release할 수 있다.\
  로직은 kind를 인자로 받는 무권한 impl에 두되 어느 계정에도 impl EXECUTE를 주지 않고, 각 계정은 kind가 리터럴로 박힌 자기 wrapper만 갖는다 — 상대 kind로는 애초에 호출할 프로시저가 없다.

이 방침은 착수 시 load-bearing 가정 하나를 달고 있었다.\
"DEFINER 하에서 wrapper의 중첩 CALL이 impl EXECUTE 없이 성립한다" — 착수 직후 통합 스모크로 실증했다.

## 3. 그래서 이렇게

각 계정은 kind가 박힌 자기 wrapper만 실행하고, 세 방어선(NULL·미지 kind·최소 미만 lease)을 impl의 한 IF에 모았다.

```text
AGENT 계정             BATCH_CUTOFF 계정
    ↓                       ↓
sp_acquire_agent       sp_acquire_cutoff      ← kind가 리터럴로 박힌 wrapper
    ↓                       ↓
      sp_acquire_impl(kind, lease)            ← 무권한 impl · 아무도 EXECUTE 없음
        ↓
   NULL · 미지 kind · lease<1 ?  ── 예 ──> p_ok=0 (fail-closed 거절)
        ↓ 아니오
   조건부 UPDATE (점유자 NONE 또는 lease 만료일 때만)
        ↓
   영향 행 1 = 획득 · fencing_token +1
   영향 행 0 = 거절
```

## 4. 코드 — 실제 커밋에서

```sql
-- deploy/schema/02_procedures.sql:72-96 (발췌) — 세 방어선을 한 IF에
IF p_holder_kind IS NULL OR p_lease_seconds IS NULL
   OR p_holder_kind NOT IN ('AGENT', 'BATCH_CUTOFF') OR p_lease_seconds < 1 THEN
  -- NULL 입력 · 미지 kind(유령 락) · 최소 미만 lease(무보호 락) = fail-closed 거절.
  SET p_ok = 0;
ELSE
  UPDATE `deploy_window_lock`
     SET ... `fencing_token` = `fencing_token` + 1, ...
   WHERE `lock_id` = 1
     AND (`holder_kind` = 'NONE' OR `lease_expires_at` < NOW(6));
  IF ROW_COUNT() = 1 THEN
```

## 5. 구현 중 마주친 문제

재점검이 두 겹을 더했다.

첫째, 이미 프로비저닝된 DB에 구 취약 프로시저가 남아 있으면, 새 wrapper를 배선해도 구판으로 구멍이 계속 열려 있다.\
그래서 DROP 정리를 넣었다 — MySQL은 DROP 시 그 프로시저의 EXECUTE 권한도 함께 제거한다.

둘째, NULL 입력이 `NOT IN` 검사를 UNKNOWN으로 우회해 만료 없는 무보호 락을 만드는 fail-open이었다.

> **UNKNOWN(3값 논리)** — SQL에서 NULL과 비교하면 참도 거짓도 아닌 UNKNOWN이 나오는 것.\
> 예: `NULL NOT IN ('AGENT', ...)`는 거짓이 아니라 UNKNOWN이라, IF 조건을 통과하지 못하고 ELSE(획득)로 새어 나간다 — 그래서 `IS NULL` 검사를 앞에 둔다.

검증은 red-first의 교과서적 사례였다 — 미수정 스키마에서 프로브 테스트로 세 결함을 재현 통과시켜(RED 증거) 실재를 먼저 증명하고, 수정 후 정식 회귀 테스트(교차 계정 거부·lease 하한·kind 거절·24-goroutine 동시 획득)로 바꿨다.

## 6. 결론

오케스트레이션에 노출된 프리미티브는 셋이다 — 획득(`AcquireWindow`), 불가역 단계 직전 보유 재확인(`Confirm`), 해제.\
그런데 `Confirm`은 이 PR에서 노출만 되고 실제로 호출되지 않았다 — 그 갭은 다음 PR(#18 = issue7)이 잡는다.

긴급 롤백 인계(override 핸드셰이크)는 인터페이스만 확정하고 스텁으로 남았다.\
이 락이 "실행을 지키는" 이야기 — lease가 dispatch 전체를 덮는가 — 는 PR #22에서 이어진다.
