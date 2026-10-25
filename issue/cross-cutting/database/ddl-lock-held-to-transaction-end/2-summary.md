# issue/cross-cutting/database/ddl-lock-held-to-transaction-end — 정리 (힌트)

## 전체 흐름

```text
[트랜잭션 하나로 도는 마이그레이션 파일]
  BEGIN
   ALTER TABLE items ADD COLUMN …      ACCESS EXCLUSIVE  ← 읽기·쓰기 모두와 충돌
   CREATE TRIGGER …                    SHARE ROW EXCLUSIVE
   CREATE INDEX … ON items (…)         SHARE  (이 문장만 보면 "쓰기만 막음")
  COMMIT                               ← 모든 락은 여기서야 풀린다
  ─────────────────────────────────────────────────────────────
  실제 효과: ACCESS EXCLUSIVE가 인덱스 생성이 끝날 때까지 유지 → 그 동안 SELECT도 멈춤

[락 대기 줄]  ALTER가 앞의 긴 트랜잭션을 기다리는 동안
  뒤의 SELECT ─▶ ALTER 뒤에 줄 섬 ─▶ 커넥션 풀 대기 ─▶ 요청 시한
  묶기: SET LOCAL lock_timeout = '2s' + 짧게 쉬고 재시도(최대 n번)

[도구 밖 단계 적용]
  1 열      BEGIN; SET LOCAL lock_timeout; ALTER …; COMMIT      (재시도)
  2 트리거  BEGIN; SET LOCAL lock_timeout; CREATE TRIGGER …; COMMIT
  3 인덱스  RESET lock_timeout; SET statement_timeout = 상한
            CREATE INDEX CONCURRENTLY …   (자동 커밋 — 트랜잭션 밖)
            └─ 확인 indisvalid AND indisready → 아니면 DROP INDEX CONCURRENTLY 뒤 재시도 → 그래도 아니면 멈춤
  4 동치 확인(카탈로그) → 같으면 도구 이력에 "적용됨" 기록(실행 없이) — 다르면 기록하지 않음

[lock_timeout을 세션에 남기면]
  CONCURRENTLY는 단계 사이 "앞 트랜잭션이 끝나기"를 락 대기로 기다림
  → 2초에 끊김 → INVALID 인덱스 잔존(질의엔 안 쓰이고 갱신 비용만)
```

## 핵심 문장

- 락은 문장이 아니라 **트랜잭션**이 끝날 때 풀린다 — 한 트랜잭션 안에서는 가장 센 락이 가장 긴 문장 동안 유지된다.
- 파일 하나 = 트랜잭션 하나인 마이그레이션 도구에서는 **파일 구성**이 락 범위를 정한다.
- `ACCESS EXCLUSIVE`는 순간이어도 위험하다 — 기다리는 동안 뒤의 읽기가 줄을 선다. `lock_timeout` + 재시도로 묶는다.
- CONCURRENTLY는 트랜잭션 밖에서만 돌고, 끊기면 INVALID 인덱스를 남긴다 — 짧은 단계의 시한은 `SET LOCAL`로 그 트랜잭션에 가둔다.
- 도구 밖에서 만든 객체는 **동치를 확인한 뒤에만** 이력에 기록한다 — 원래 파일은 바꾸지 않는다(체크섬 보존).
- 막힘의 크기는 인덱스 생성 시간에 비례한다 — 작은 규모의 "1초 안팎"은 큰 규모의 근거가 아니다.
