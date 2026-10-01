# database/45-clickhouse-mergetree — 정답

## 정답

### 1. MergeTree가 좋아지는 것과 잃는 것

- 읽기: 컬럼별로 나눠 저장해 필요한 컬럼만 읽는다(`Wide` 파트는 컬럼마다 파일, 작은 `Compact` 파트는 파일 하나). 정렬 덕분에 비슷한 값이 붙어 압축이 잘 된다. 희소 인덱스로 그래뉼 단위로 건너뛴다.
- 쓰기: INSERT 블록을 정렬해 파트 하나로 한 번에 쓴다. 행 단위 무작위 쓰기가 없다.
- 잃는 것
  - 행 하나를 고치거나 지우기가 비싸다. mutation은 파트를 다시 쓴다.
  - 작은 INSERT가 잦으면 파트가 쌓인다(`Too many parts`).
  - PRIMARY KEY가 유일성을 보장하지 않는다. 일반 `MergeTree`는 병합해도 같은 키 행을 그대로 둔다. 병합 때 중복을 지우는 것은 `ReplacingMergeTree` 같은 변형 엔진이다.

### 2. 두 파티션에 걸친 INSERT

- 파트가 **두 개** 생긴다. 파티션 키로 행을 나눠 파티션마다 파트를 만든다.
- 이름은 `202609_N_N_0`, `202610_M_M_0` 꼴이다. 블록 번호 최솟값과 최댓값이 같고, 레벨은 0(병합 전)이다.
- 행 수가 `max_insert_block_size`를 넘으면 더 쪼개질 수 있다.
- "INSERT 한 번 = 파트 하나"는 한 파티션에만 들어가는 작은 INSERT에서만 맞다.

### 3. 파트 수 임계

- 2000개: `parts_to_delay_insert`(1000)를 넘었다. INSERT는 성공하지만 지연된다.
  - 식(23.1 이후): `max(10, 1000 × (2000 − 1000 + 1) / (3000 − 1000))` ≈ 500ms.
- 3001개: `parts_to_throw_insert`(3000)를 넘었다. `Too many parts (3001 with average size of …) in table '…'. Merges are processing significantly slower than inserts` 예외로 거부된다.
  - 26.8 코드는 `>=`로 비교한다. 정확히 3000개여도 이미 거부된다.
- 두 임계는 **파티션 하나**의 활성 파트 수 기준이다. 테이블 전체 기준은 `max_parts_in_total`(100000)이다.
- 파티션의 평균 파트 크기가 `max_avg_part_size_for_too_many_parts`(1 GiB)보다 크면 두 검사는 적용되지 않는다.

### 4. 둘째 키 컬럼만으로 거르기

- 첫 컬럼(tenant_id) 조건이 없으므로 이진 탐색은 못 쓴다. ClickHouse는 generic exclusion search로 마크 구간을 배제한다.
- tenant_id 카디널리티가 **낮으면**: 같은 tenant_id가 여러 그래뉼에 이어진다. 그 안에서 metric이 정렬돼 있어 'cpu'가 없는 그래뉼을 꽤 건너뛴다.
- tenant_id 카디널리티가 **높으면**: 그래뉼마다 tenant_id가 바뀐다. 마크만 보고는 'cpu'가 있을지 판단할 수 없어 거의 다 읽는다.
- 그래서 가이드는 카디널리티 차이가 크면 키를 카디널리티 오름차순으로 두라고 권한다. 늘 metric만으로 거른다면 metric을 앞에 두거나 projection·스키핑 인덱스를 검토한다.

### 5. BRIN과 희소 인덱스

- 같은 점
  - 행마다가 아니라 묶음(BRIN은 블록 범위, ClickHouse는 그래뉼)마다 항목 하나를 둔다. 그래서 작다.
  - 범위 단위로 읽어서 여분 행을 읽고 버린다.
  - 데이터가 키 순서로 놓여 있어야 효과가 있다.
- 다른 점
  - PG 힙은 정렬을 보장하지 않는다. BRIN은 삽입 순서가 키와 상관돼 있기를 기대할 뿐이다.
  - MergeTree 파트는 항상 ORDER BY 순서로 쓰인다.
  - 이 예의 BRIN(기본 `minmax` 연산자 클래스)은 min/max 요약이다. PostgreSQL 17 BRIN에는 `minmax-multi`·`inclusion`·`bloom` 클래스도 있다. 기본 인덱스는 그래뉼 첫 행의 키 값이다.
- 로컬 재현(예시, PostgreSQL 17.11): 600행을 찾으려고 128블록(lossy)을 읽었다. `Rows Removed by Index Recheck: 19496`이었다. 인덱스는 24 kB였다. 같은 컬럼의 B-tree는 6600 kB였다.

### 6. 배치인데도 Too many parts

- 확인
  ```sql
  SELECT partition_id, count() FROM system.parts
  WHERE active AND table = 'events'
  GROUP BY partition_id ORDER BY count() DESC LIMIT 20;
  SELECT uniqExact(partition_id) FROM system.parts WHERE active AND table = 'events';
  ```
  - 파티션이 (테넌트 수 × 날짜 수)만큼 있다. 1만 행 배치 하나가 테넌트 수만큼 파트를 만든다.
- 원인: 병합은 파티션을 넘지 않는다. 같은 파티션 안 파트끼리는 합쳐지지만, 파티션이 수천 개면 파티션마다 최소 한 파트씩 남아 파트 수가 줄지 않는다.
- 대처: `PARTITION BY toYYYYMM(ts)`(또는 파티션 없음)로 바꾸고 `tenant_id`는 ORDER BY 첫 컬럼으로 옮긴다. 새 테이블을 만들어 옮겨 담는다. 문서도 고객 ID로 파티션하지 말고 ORDER BY 앞에 두라고 한다.

### 7. wait_for_async_insert 1 vs 0

| | 1 (기본) | 0 |
|---|---|---|
| 응답 시점 | 버퍼가 디스크로 flush된 뒤 | 버퍼에 넣자마자 |
| 에러 | 클라이언트가 받는다 | 서버 로그·`system.asynchronous_insert_log`(로깅을 켠 경우)에만 남는다 |
| 유실 | flush 실패를 클라이언트가 안다 | 문서: 저장된다는 보장이 없다 |
| 백프레셔 | 서버가 느려지면 클라이언트도 느려진다 | 클라이언트가 계속 빨리 써서 과부하를 키울 수 있다 |

- 26.8 기본값: `async_insert = true`(26.2부터), `wait_for_async_insert = true`.
- 문서는 async insert를 쓴다면 `async_insert=1, wait_for_async_insert=1`을 강하게 권한다.

### 8. ReplacingMergeTree 중복과 OPTIMIZE FINAL

- 원인: 중복 제거는 병합 때만 일어난다. 병합 시점은 정할 수 없다. 다른 파티션에 들어간 같은 키는 합쳐지지 않는다.
- `OPTIMIZE ... FINAL` 크론의 문제
  - 파티션마다 활성 파트를 하나로 합친다(파티션 지정이 없으면 전체 파티션). 큰 파트도 압축을 풀고 다시 써서 CPU·I/O를 크게 쓴다.
  - 끝난 직후 새 INSERT가 다시 파트를 만든다. 크론 사이에는 여전히 중복이 보인다.
- 대신
  - 조회 시 `SELECT ... FROM orders FINAL`을 쓴다. 필터가 기본 키 컬럼과 같으면 부담이 적다.
  - 또는 `argMax(col, version)`·`GROUP BY` 집계로 최신 행만 고른다.
  - 같은 키가 같은 파티션에 들어가도록 파티션 키를 잡는다.
