# data-engineering/16-de-symptom-index — 정답

## 정답

### 1. 에러 대신 어긋남의 모양

- 이 영역의 장애는 크래시로 보이지 않는다. 잡은 끝나고, 로그는 깨끗하고, 숫자만 틀린다(파이프라인은 초록인데 숫자가 틀린 모양).
- 잡 "성공"이 보장하는 것: SQL·코드가 오류 없이 끝났다.
- 보장하지 않는 것: 입력이 왔다, 다 실렸다, 한 번만 실렸다, 의미가 그대로다. 0행 `INSERT`도 성공이다([10-1](../10-data-quality-and-data-observability/2-summary.md) 실험 `INSERT 0 0`, `exit=0`).
- 그래서 첫 단서는 원천과 적재본의 파티션별 행 수·합계 대조이고, 그 차이의 모양(0·정수배·약간 적음·평평함·날짜 경계·비율)이 원인 후보를 고른다.

### 2. `Reconcile.java`의 분류

- 10-02: `MULTIPLE x2`. 원천 1,000행·250,000 → 적재 2,000행·500,000. 행 수와 합계가 같은 정수배다 → append 재실행·grain 혼합 후보.
- 10-05·10-06: `PLATEAU`. 원천이 80,000 → 90,000으로 늘었는데 적재본은 둘 다 65,535행·16,383,750. 늘어나는 입력에 같은 값에서 평평한 출력 → 고정 한도에서 잘림 후보.
- 10-08: `VALUE`. 행 수 1,000으로 같고 합계만 250,000 → 227,273(÷1.1, 예시). 행 수 검사로는 안 보이고 합계·분포로만 보인다 → 의미·규칙 변경 후보.
- 놓치는 것(하나 고르면 됨)
  - grain 혼합([03-1](../03-dimensional-modeling/2-summary.md))은 합계 줄 수가 상세 줄 수와 같지 않으면 행 수가 정확한 배수가 아니라 `EXTRA`로 분류될 수 있다(03번 실험 데이터면 1,200 + 600 = 1,800행, 1.5배 — 계산).
  - 정수배 규칙은 append 재실행과 이력 테이블 조인 곱([13-3](../13-data-vault/2-summary.md))을 가르지 못한다.
  - 행 수·합계가 모두 같고 분포(지역별)만 바뀐 SCD Type 1 덮어쓰기([04-1](../04-slowly-changing-dimensions/2-summary.md))는 `OK`로 나온다.
- 규칙은 후보를 고를 뿐이다. 확정은 leaf의 확인 쿼리로 한다.

### 3. 합계 2배의 다섯 후보 가르기

| 후보 | 배수의 모양 | 확인 |
|---|---|---|
| append 재실행 [08-1](../08-idempotent-pipelines-and-backfill/2-summary.md) | 그 파티션의 모든 지표가 정확히 2배(재시도 횟수 배), 다른 날짜는 정상 | `GROUP BY ds HAVING count(*) > 1`, 스케줄러 재시도 기록 |
| grain 혼합 [03-1](../03-dimensional-modeling/2-summary.md) | 그 팩트의 합계 지표가 모든 날짜에서 2배 근처, 행 유형이 섞임 | `line_no = 0` 같은 합계 줄, grain 문장 대조 |
| 팩트–팩트 직접 조인 [03-2](../03-dimensional-modeling/2-summary.md) | 주문 grain 지표(배송비)만 부풀고 상세 grain 지표(상품 매출)는 맞음. 상세 줄 많은 곳일수록 더 | 리포트 SQL의 팩트 간 조인 |
| Satellite 이력 조인 [13-3](../13-data-vault/2-summary.md) | 키당 행이 여럿(이력 행 수의 곱), 마트에서만 | 마트 "키당 1행" 검사, PIT 사용 여부 |
| 재처리 잡의 운영 출력 쓰기 [07-3](../07-batch-stream-architectures/2-summary.md) | 재처리 구간만 거의 2배 | 재처리 잡의 출력 대상·반영 방식 |

- 공통 처방 금지: `DISTINCT`로 덮지 않는다. 원인은 남고 진짜로 같은 내용의 다른 사건까지 지운다.

### 4. 지난달 지역별 매출이 바뀌었다

- 총합 그대로, 분포만 이동
  - 후보: 지역 속성을 SCD Type 1로 덮어써 이력이 사라졌다([04-1](../04-slowly-changing-dimensions/2-summary.md) 실험: 8월 seoul 300 → 행 없음, busan 700 → 1,000).
  - 확인: 리포트가 쓰는 차원 속성의 SCD 유형, 차원의 최근 `updated_at`.
  - 늦게 온 팩트가 현재 행에 붙은 경우([04-5](../04-slowly-changing-dimensions/2-summary.md))도 분포만 움직인다. 팩트 사건 시각과 붙은 차원 행의 유효 기간을 대조한다.
- 총합도 바뀜
  - 후보: 백필이 현재 규칙으로 과거를 계산([08-2](../08-idempotent-pipelines-and-backfill/2-summary.md) 실험 90,000 → 75,000), 처리 시각으로 날짜를 잘라 재처리 때 날짜가 옮겨 감([06-1](../06-event-data-modeling/2-summary.md)).
  - 확인: 백필 전 스냅샷과 파티션별 비교, 집계의 날짜 컬럼.
- 다시 뽑으려면: 그때의 상태가 있어야 한다. 마감 리포트 스냅샷 테이블, Type 2 이력, 레이크하우스 태그([14-3](../14-lakehouse-table-formats/2-summary.md) — 만료된 스냅샷으로는 못 뽑는다). 이미 Type 1로 지운 이력은 원천 변경 이력(감사 로그·CDC)이 있어야 복원된다.

### 5. 두 대시보드의 차이

- (가) 이른 아침 매출이 전날로
  - 후보: 시간대 불일치 — 한쪽은 UTC 자정, 다른 쪽은 KST 자정([06-5](../06-event-data-modeling/2-summary.md), 실험: KST 00~09시 375건이 전날로).
  - 확인: 각 도구의 세션 시간대, 저장 타입(`timestamp` vs `timestamptz`), 업무 일자 계산 위치.
- (나) 매일 1~3% 들쭉날쭉, 오늘 본 숫자가 내일 바뀜
  - 후보: 실시간 경로와 배치 경로가 같은 지표를 다른 규칙(처리 시각·중복 미제거 vs 이벤트 시각·중복 제거)으로 계산([07-1](../07-batch-stream-architectures/2-summary.md), 실험 23:59 99,000 → 다음 날 100,000). 처리 시각 집계([06-1](../06-event-data-modeling/2-summary.md))도 같은 모양을 낸다.
  - 확인: 두 경로의 날짜 기준·중복 제거 규칙, 날짜별 대조.
- (가)는 **시각 축**(시간대) 차이가 후보다. (나)는 시각 축(처리 시각 vs 이벤트 시각)에 **중복 처리 규칙** 차이가 함께 있다. 둘 다 정의([15-2](../15-data-mesh-and-data-products/2-summary.md))·원천([01-1](../01-system-of-record-and-derived-data/2-summary.md)) 차이와는 모양이 다르다. 정의가 다를 때는 차이가 날짜 경계와 상관없이 날 수 있다([15-2](../15-data-mesh-and-data-products/2-summary.md) 실험: 같은 로그로 118~580).

### 6. 디스크가 며칠째 오른다

- 첫 쿼리: `pg_replication_slots`에서 `active`, `inactive_since`, `wal_status`, `pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)`(retained), `safe_wal_size`. 그리고 `pg_ls_waldir()` 합계.
- 읽는 법([05](../05-change-data-capture/2-summary.md) 적용 §2)
  - `active=f` + 오래된 `inactive_since` → 죽었거나 버려진 슬롯.
  - `retained`가 계속 오르고 `wal_status=extended` → 디스크를 먹는 중([05-1](../05-change-data-capture/2-summary.md), 실험 48 MB → 160 MB).
  - `unreserved` → 다음 체크포인트에 필요한 WAL이 지워질 수 있다. `lost` → 이미 끊겼다.
- 상한을 걸면: 디스크 풀 대신 슬롯 무효화(`wal_status=lost`, `invalidation_reason=wal_removed`)가 된다. 하류는 어느 시점부터 멈추고, 커넥터가 슬롯을 읽으려 하면 `can no longer get changes from replication slot` 오류가 난다([05-5](../05-change-data-capture/2-summary.md) 실험 E). 이 오류를 경보로 받지 않으면 대시보드에는 "멈춤"으로만 보인다.
- 함께 둘 것: `safe_wal_size`·`retained`·`inactive_since` 경보, 무효화 시 재스냅샷 절차. 디스크가 이미 찼을 때의 처리와 `pg_wal` 수동 삭제 금지는 database/19 장애 2가 정본이다.

### 7. 원천 `count(*) = 0`의 함정

- 원천 0행은 원천만 지웠다는 뜻이다. 사본(웨어하우스·검색 인덱스·이벤트 로그·백업·내보내기)은 별도 경로라 원천 삭제가 자동으로 전파되지 않는다([12-1](../12-data-retention-and-erasure/2-summary.md) 실험: 원천 0행, 파생 다섯 테이블 잔존).
- 잔존 경로(셋을 고르면 됨)
  - 사본 목록·경로별 삭제 절차 없음([12-1](../12-data-retention-and-erasure/2-summary.md)).
  - CDC 소비자가 `op=d`·tombstone을 무시([05-4](../05-change-data-capture/2-summary.md)).
  - `SELECT *` 내보내기가 계보에 "미상"으로 남아 삭제 대상에서 빠짐([11-3](../11-data-lineage/2-summary.md)).
  - 불변 로그의 평문 PII([12-2](../12-data-retention-and-erasure/2-summary.md)), 남은 키 사본으로 복호 가능([12-5](../12-data-retention-and-erasure/2-summary.md)).
- 반대 방향: 검색 인덱스(파생본)에서 직접 숨긴 상품이 재색인 뒤 다시 나타난다([01-2](../01-system-of-record-and-derived-data/2-summary.md)). 재구축은 원천을 다시 접으므로 수정은 원천에 기록해야 한다.
- 완료의 증거: 계보로 만든 사본 목록 전체에 대한 확인 검색 결과와 사본별 ack.

### 8. 재처리 불가의 공통 원인

- 공통 원인: 다시 읽을 원본이 없거나, 원본의 보존 기간이 재처리 요구 기간보다 짧다.
  - [07-2](../07-batch-stream-architectures/2-summary.md) 로그 보존 < 재처리 구간(실험: 30일 재처리가 9일·880건만, 재실행에서는 10일·906~995건 — 실행마다 다름, 에러 없음).
  - [01-4](../01-system-of-record-and-derived-data/2-summary.md) 원천 이벤트 보존 기간이 재구축 요구보다 짧거나 원천이 현재 상태뿐.
  - [02-4](../02-oltp-olap-and-warehouse/2-summary.md) 변환 전 원본을 남기지 않은 ETL.
  - [05-2](../05-change-data-capture/2-summary.md) binlog 보존 만료로 커넥터가 위치를 잃음.
  - [14-3](../14-lakehouse-table-formats/2-summary.md) 스냅샷 만료가 재현 요구보다 짧음.
- 성격이 다른 것: [07-4](../07-batch-stream-architectures/2-summary.md). 원본은 있는데 재처리 속도가 따라잡지 못한다(파티션 수가 병렬도 상한, 출력 DB의 대량 쓰기 한계). 보존이 아니라 처리량 문제다.
- 예방 한 문장: 얼마나 과거까지 다시 돌려야 하는지(재처리 요구 기간)를 먼저 정하고, 로그 보존·raw 층·아카이브·스냅샷 태그를 그 기간 이상으로 맞춘다.
