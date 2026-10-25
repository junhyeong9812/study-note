# issue/cross-cutting/database/ddl-lock-held-to-transaction-end — 정답

태그: `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **열 추가의 `ACCESS EXCLUSIVE`가 인덱스 생성이 끝날 때까지 유지되어, 그 동안 읽기까지 막힌다.**\
   PostgreSQL의 테이블 락은 문장이 끝날 때가 아니라 **트랜잭션이 끝날 때** 풀린다.\
   파일 하나를 트랜잭션 하나로 돌리면 첫 문장 `ALTER TABLE`이 잡은 `ACCESS EXCLUSIVE`(모든 락 모드와 충돌 — `SELECT`의 `ACCESS SHARE`도)가 뒤의 `CREATE INDEX`가 끝나고 `COMMIT`할 때까지 남는다.\
   문장별로 보면 `CREATE INDEX`는 `SHARE`(쓰기만 막음)라 "인덱스 생성 동안 쓰기가 막힌다"로 읽기 쉽지만, 실제로는 **읽기·쓰기 모두**가 인덱스 생성 시간만큼 멈춘다.\
   이 사례는 설계 검토에서 이 차이를 찾았고, 측정에서 인덱스 빌드 단계의 0.2초 락 표본마다 그 테이블의 `AccessExclusiveLock`이 쥐어져 있음을 확인했다.
   > **ACCESS EXCLUSIVE** — PostgreSQL의 가장 센 테이블 락. 같은 테이블의 다른 모든 락(읽기 포함)과 충돌한다. 대부분의 `ALTER TABLE`이 기본으로 잡는다.

2. **기다리는 동안 뒤의 모든 접근이 그 뒤에 줄을 선다 — `lock_timeout`과 재시도로 묶는다.**\
   `ACCESS EXCLUSIVE` 요청은 앞의 열린 트랜잭션이 끝나기를 기다리고, 락 대기열은 대체로 순서대로 처리되므로 그 뒤에 온 평범한 `SELECT`도 열 추가 뒤에 줄을 선다.\
   업무 요청은 커넥션 풀에서 대기하다 요청 시한으로 번질 수 있다 — 문장 자체가 순간이어도 "기다린 시간"이 멈춤이 된다.\
   그래서 짧은 단계는 `SET LOCAL lock_timeout = '2s'`로 줄 서는 시간을 시도당 2초로 묶고, 걸리면 1초 쉬고 다시(최대 30번) 하게 했다 — 시도마다 대기 시간·결과를 기록한다.
   > **lock_timeout** — 락 획득을 기다리는 최대 시간. 넘으면 그 문장이 오류로 끝난다(문장 실행 시간 상한인 `statement_timeout`과 다르다).

3. **일반은 `SHARE`(쓰기 막음), CONCURRENTLY는 `SHARE UPDATE EXCLUSIVE`(쓰기 허용) — 대신 트랜잭션 밖에서만 돌고, 끊기면 INVALID가 남는다.**\
   CONCURRENTLY는 테이블을 두 번 훑고, 단계 사이마다 그 시점에 열려 있던 트랜잭션들이 끝나기를 기다린다 — 그래서 더 느리고 트랜잭션 블록 안에서 실행할 수 없다.\
   중간에 실패하면 인덱스가 **INVALID**로 남는다 — 질의에는 쓰이지 않지만 갱신마다 유지 비용은 든다. 지우고(`DROP INDEX CONCURRENTLY`) 다시 만들어야 한다.

4. **CONCURRENTLY의 기다림이 2초에 끊겨 INVALID 인덱스가 남는다.**\
   CONCURRENTLY가 앞 트랜잭션을 기다리는 것도 **락 대기**라 세션의 `lock_timeout`이 그대로 적용된다 — 고부하에서 2초 안에 앞 트랜잭션이 다 끝나지 않으면 끊긴다.\
   `SET LOCAL`은 시한을 그 트랜잭션 안에만 두어 다음 단계로 새지 않게 하고, CONCURRENTLY 단계 앞에서는 `RESET lock_timeout`으로 지운 뒤 대신 `statement_timeout`으로 전체 실행 시간에 상한(실측 시간의 3배 · 최소 600초)을 둔다 — 무한 대기도, 짧은 시한으로 인한 INVALID도 막는다.\
   이 사례에서 이 결함은 설계 검토에서 발견해 적용 전에 막았다 — 측정 중 `lock_timeout`이 실제로 걸린 일은 0번이라 이 장치의 효과 자체는 재지 못했다.

5. **원래 파일은 그대로 두고, 같은 객체를 도구 밖에서 만든 뒤 동치를 확인하고 "실행 없이 적용됨"으로 기록한다.**\
   같은 버전 번호로 비트랜잭션 판 파일을 다른 위치에 두는 방법은 그 DB의 이력 체크섬이 원래 파일과 달라져, 원래 위치를 쓰는 앱이 그 DB에서 영원히 검증에 실패한다(설정이 DB 이력에 묶인다) — 선택하지 않은 방법.\
   그래서 원래 파일과 같은 문장을 단계별로(열 → 트리거 → 인덱스) 따로 실행하고, 카탈로그(열 정의·기본값 식·인덱스 정의·유효 여부·함수·트리거 정의·활성 상태)를 **같은 파일을 빈 DB에 적용한 결과**와 비교해 같을 때만 도구의 "실행 없이 이력만 기록" 기능으로 기록했다(Flyway 커뮤니티판 11.7.2에서 동작 확인).\
   기록할 때 이미 적용된 버전들의 위치까지 **전부** 줘야 한다 — 그 파일만 든 위치를 주면 도구가 "적용됐는데 위치에 없는 버전"으로 검증에 실패한다.\
   비교에서는 적용 시각·물리 배치에 따라 달라지는 값(빠른 기본값·OID·통계 등)을 뺀다.\
   순서를 열 → 트리거 → 인덱스로 둔 이유는 트리거가 먼저 서야 옛 앱의 쓰기도 일찍부터 변경 표시를 남기기 때문이다(인덱스는 속도, 트리거는 탐지 범위).
   > **체크섬 검증** — 마이그레이션 도구가 이미 적용된 버전의 파일 체크섬을 이력과 비교해, 적용 뒤 파일이 바뀌었으면 기동을 거부하는 동작.

6. **`indisvalid AND indisready`로 확인하고, 아니면 지우고 다시 — 그래도 아니면 기록하지 않고 멈춘다.**\
   CONCURRENTLY가 끝나면 `pg_index`의 두 플래그를 본다 — 아니면(시한 끊김 포함) `DROP INDEX CONCURRENTLY` 뒤 다시(최대 2번), 그래도 아니면 이력을 기록하지 않고 멈춘다.\
   `pg_indexes`에서 이름만 찾는 기동 검사는 INVALID 인덱스도 "있음"으로 통과시킨다 — 그러면 이 인덱스를 전제로 한 조회가 매번 순차 읽기가 된다. 그래서 기동 검사에 유효 여부를 더했다(→ [catalog-presence-vs-enabled](../catalog-presence-vs-enabled/) 5번과 같은 원리).

7. **"이 규모에서는 막힘이 마이그레이션 시간만큼, 1초 안팎이었다"까지만 말할 수 있다.**\
   약 615만 행 테이블에서 트랜잭션 안 적용은 0.81~0.82초, 업무 대기 최대 0.79초였다 — 그 앞에 오래 열린 트랜잭션이 없던 조건이다.\
   도구 밖 단계 적용은 쓰기를 막지 않았지만 전체 10초 남짓(인덱스 단계 약 2.4초)과 절차 단계 수가 들었고, 막힘 1초 안팎에서는 다운타임 이점이 드러나지 않아 단순한 트랜잭션 안 경로를 골랐다.\
   "막힘의 상한 = 마이그레이션 시간"은 일반형으로는 가설이다 — 앞에 긴 트랜잭션이 있으면 대기열이 더해지고, 인덱스 생성이 긴 테이블(디스크·훨씬 큰 표)에서는 막힘도 길어진다. 그런 DB에서는 운영 크기 사본에서 먼저 재고, 길면 단계 적용을 쓴다.

## 문제 구조 (추상화 코드)

### 변형 A — 한 파일 = 한 트랜잭션 안의 열 추가 + 인덱스 생성
① 문제 코드
```sql
-- V9__add_change_marker.sql  (도구가 BEGIN … COMMIT으로 감싼다)
ALTER TABLE items ADD COLUMN updated_at timestamptz NOT NULL DEFAULT now();   -- ACCESS EXCLUSIVE 획득
CREATE FUNCTION touch() RETURNS trigger AS $$ BEGIN NEW.updated_at := now(); RETURN NEW; END $$ LANGUAGE plpgsql;
CREATE TRIGGER items_touch BEFORE UPDATE ON items FOR EACH ROW EXECUTE FUNCTION touch();
CREATE INDEX idx_items_updated_at ON items (updated_at);                       -- 이 동안에도 ACCESS EXCLUSIVE 유지
-- COMMIT에서야 모든 락 해제 → 인덱스 생성 시간만큼 SELECT까지 멈춤
```
② 고친 코드 (도구 밖 단계 적용 — 원래 파일은 무변경)
```sql
-- 1 열 (실패하면 1초 쉬고 재시도, 최대 30번)
BEGIN; SET LOCAL lock_timeout = '2s';
ALTER TABLE items ADD COLUMN updated_at timestamptz NOT NULL DEFAULT now();
COMMIT;
-- 2 함수·트리거 (같은 재시도)
BEGIN; SET LOCAL lock_timeout = '2s';
CREATE FUNCTION touch() …; CREATE TRIGGER items_touch …;
COMMIT;
-- 3 인덱스 (자동 커밋 — 트랜잭션 밖)
RESET lock_timeout;
SET statement_timeout = '600s';                    -- 실측의 3배 · 최소 600초
CREATE INDEX CONCURRENTLY idx_items_updated_at ON items (updated_at);
SELECT indisvalid AND indisready FROM pg_index WHERE indexrelid = 'idx_items_updated_at'::regclass;
-- false → DROP INDEX CONCURRENTLY … 후 재시도(최대 2번) → 그래도 false면 멈춤(이력 기록 안 함)
```
```bash
# 4 동치 확인 뒤에만 이력 기록 — 실행 없이, 이미 적용된 버전의 위치까지 전부
same_catalog "$DB" "$REFERENCE_DB" || exit 1
migrate-tool migrate -target=9 -skipExecutingMigrations=true -locations="$ALL_LOCATIONS"
```
무엇이 깨졌나: 문장별 락 모드로 영향을 예상했지만, 락의 수명은 문장이 아니라 트랜잭션(= 파일)이 정했다.

### 변형 B — 짧은 단계용 시한이 세션에 남아 CONCURRENTLY를 끊음
① 문제 코드
```sql
SET lock_timeout = '2s';                           -- 세션 전체에 남는다
ALTER TABLE items ADD COLUMN …;
CREATE TRIGGER …;
CREATE INDEX CONCURRENTLY idx_items_updated_at ON items (updated_at);
-- 앞 트랜잭션 대기(락 대기)가 2초에 끊김 → ERROR · INVALID 인덱스 잔존
```
② 고친 코드
```sql
BEGIN; SET LOCAL lock_timeout = '2s'; ALTER TABLE …; COMMIT;   -- 시한은 이 트랜잭션 안에만
RESET lock_timeout; SET statement_timeout = '600s';             -- CONCURRENTLY 앞에서 지우고 전체 상한으로 대신
CREATE INDEX CONCURRENTLY …;
```
무엇이 깨졌나: "짧게 기다려라"는 의도가 세션 설정으로 남아, 오래 기다려야 정상인 다음 문장에 적용됐다.

## 검증 기록
- 2026-10-26: 사건 기록 대조·추상화(Claude 초안) — 변형 A의 락 범위는 설계 검토에서 발견하고 측정의 락 표본으로 확인, 변형 B는 설계 검토에서 발견해 적용 전에 막음(`lock_timeout` 발동 0 — 효과 미측정). 수치는 측정 기록(트랜잭션 안 0.81~0.82초 · 단계 적용 전체 10초 남짓)에서 옮김.

## 방안 비교

같은 원리(락 수명 = 트랜잭션)에 대한 세 방안.

### 방안 1 — 그대로 트랜잭션 안 적용 (이 사례의 최종 선택)
```sql
-- 파일 하나: ALTER + TRIGGER + CREATE INDEX — 막힘 = 파일 실행 시간(+ 앞 트랜잭션 대기)
```

### 방안 2 — 도구 밖 단계 적용 + 실행 없이 이력 기록 (측정한 대안)
```sql
-- 1 열(lock_timeout + 재시도) → 2 트리거 → 3 CONCURRENTLY(RESET lock_timeout) → 4 동치 확인 → 이력 기록
```

### 방안 3 — 같은 버전의 비트랜잭션 판 파일을 다른 위치에 (선택하지 않은 방법)
```properties
# V9__…sql.conf
executeInTransaction=false      # 그 DB의 이력 체크섬 ≠ 원래 파일 → 원래 위치의 앱은 그 DB에서 영원히 검증 실패
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 1. 트랜잭션 안 | 인덱스 생성이 짧고, 앞에 오래 열린 트랜잭션이 없다 | 단계 1개 | 인덱스 생성 시간만큼 읽기·쓰기 모두 멈춤 · 긴 트랜잭션 뒤에서는 대기열이 더해짐 | 운영 크기 사본에서 잰 막힘이 허용선 안일 때 |
| 2. 단계 적용 + 이력 기록 | 도구가 "실행 없이 기록"을 지원하고, 카탈로그 동치 비교를 만들 수 있다 | 단계 4개 · 동치 비교 코드 · CONCURRENTLY의 두 번 훑기 | 세션 시한이 새면 INVALID · 동치 확인 없이 기록하면 이력과 실제가 어긋남 | 인덱스 생성이 길어 막힘이 허용선을 넘을 때 |
| 3. 다른 위치의 비트랜잭션 판 | 그 DB에는 늘 다른 위치를 준다 | 파일 2벌 | 설정이 DB 이력에 묶여, 기본 위치 앱이 그 DB에서 기동하지 못함 | (권하지 않음) |

**결론**: 막힘은 인덱스 생성 시간에 비례하므로 먼저 운영 크기 사본에서 트랜잭션 안 적용 시간을 잰다 — 짧으면 단순한 방안 1이 단계 수에서 이긴다(이 사례: 약 615만 행에서 0.8초).\
길면 방안 2가 맞고, 그때는 짧은 단계의 시한을 `SET LOCAL`로 가두고 CONCURRENTLY 결과의 유효 여부를 확인한 뒤에만 이력을 기록한다.\
방안 1이 "긴 경우"에도 괜찮다는 것과, 어느 길이부터 방안 2로 넘어가야 하는지는 이 사례에서 재지 않았다(가설).\
검증 기록: 2026-10-26 사건 기록 대조·추상화(Claude 초안) — 방안 1·2는 측정, 방안 3은 설계 검토 근거(미측정).

## 관련 카드
- [migration-discipline](../migration-discipline/) — 적용된 마이그레이션은 불변 이력이다 — 이 카드가 원래 파일을 바꾸지 않고 도구 밖 적용 + 이력 기록을 고른 이유.
- [catalog-presence-vs-enabled](../catalog-presence-vs-enabled/) — 이름으로 존재만 세는 검사는 INVALID 인덱스도 통과시킨다.
- [transaction-boundary-scope](../transaction-boundary-scope/) — 트랜잭션 경계가 원자성 단위다 — 이 카드는 같은 경계가 락 수명도 정한다는 쪽.
- [add-column-default-shared-value](../add-column-default-shared-value/) — 같은 열 추가 문장이 기존 행에 남기는 값과 그 비용.
