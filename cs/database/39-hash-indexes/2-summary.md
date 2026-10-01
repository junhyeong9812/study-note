# database/39-hash-indexes — 해시 인덱스: 정적·확장·선형 해싱 — 정리 (힌트)

## 해결하는 문제

B+Tree는 키 하나를 찾을 때 루트에서 리프까지 내려간다. 트리 높이만큼 페이지를 읽는다.\
"이 키와 **같은** 행"만 찾는다면 순서는 필요 없다. 키를 해시해서 바로 그 버킷 페이지로 가면 된다.

그런데 디스크 위의 해시 테이블에는 메모리 해시맵에 없던 문제가 있다.
- 메모리 해시맵은 꽉 차면 전체를 두 배 크기로 다시 만든다(리해시).
- 디스크 인덱스가 수 GB라면 전체 리해시는 그동안 인덱스를 못 쓰게 만든다.
- 그래서 **조금씩 커지는** 해시가 필요하다. 그것이 확장 해싱과 선형 해싱이다.

쉬운 예: 사물함이다.
- 학번 끝 두 자리로 사물함 100칸을 정했다. 학생 이름을 몰라도 번호만 알면 바로 연다.
- "학번 20~30번 학생 전부"는 사물함 배치로는 못 찾는다. 번호가 칸에 흩어져 있다.
- 학생이 늘어 칸이 모자라면, 사물함 전체를 새로 짜는 대신 **넘치는 칸 하나만** 둘로 나누고 싶다.

똑같은 구조다.\
해시 인덱스는 등호 조회만 빠르다. 성장은 "버킷 하나씩 분할"로 한다.

실무 예:
- 긴 URL·UUID 컬럼의 등호 조회만 있는 테이블. PostgreSQL 해시 인덱스는 값 대신 4바이트 해시만 저장해 B-tree보다 훨씬 작을 수 있다.
- MySQL InnoDB에서 `USING HASH`로 만들었는데 실제로는 B-tree였다.

## 동작·원리

### 1. 정적 해싱 — 버킷 수가 고정이다

```text
  bucket = h(key) mod 4

  [0] → 페이지 ─→ 오버플로 페이지 ─→ 오버플로 페이지     한 버킷에 몰리면 체인이 길어진다
  [1] → 페이지
  [2] → 페이지 ─→ 오버플로 페이지
  [3] → 페이지

  버킷 수를 늘리려면: 새 크기(보통 2배)로 전체를 다시 만든다
```

- 원소 수를 미리 알아야 한다. 모자라면 전체 재구성이 필요하다. 보통 두 배로 다시 만든다(CMU 15-445 L7).
  - *오버플로 페이지*: 버킷의 첫 페이지가 꽉 찼을 때 뒤에 사슬로 잇는 추가 페이지.
- 조회는 버킷의 모든 오버플로 페이지를 훑어야 한다. 체인이 길면 B-tree보다 느려질 수 있다.

### 2. 확장 해싱 (Extendible Hashing) — 디렉터리만 두 배로

```text
  전역 깊이(global depth) 2 = 해시의 2비트로 디렉터리 칸을 고른다
  버킷마다 지역 깊이(local depth) = 그 버킷이 실제로 구분하는 비트 수
  버킷 용량 2 (예시, 해시 하위 비트 사용)

  디렉터리          버킷
  00 ──────────> A (지역 2) [4, 8]
  01 ──┐
       ├──────> B (지역 1) [1, 3]       01과 11이 버킷 B를 함께 가리킨다
  11 ──┘
  10 ──────────> C (지역 2) [2, 6]
```

```text
  (1) 5를 넣는다 (101 → 하위 2비트 01) → B가 꽉 참
      B의 지역 깊이 1 < 전역 깊이 2 → 디렉터리는 그대로, B만 둘로 나눈다
      01 → B  (지역 2) [1, 5]
      11 → B' (지역 2) [3]

  (2) 12를 넣는다 (1100 → 00) → A가 꽉 참
      A의 지역 깊이 2 = 전역 깊이 2 → 디렉터리를 두 배로 (전역 깊이 3, 칸 8개)
      A를 3비트로 나눈다:  8(000) → 칸 000,  4(100)·12(100) → 칸 100
      나머지 칸은 기존 버킷을 두 칸씩 함께 가리킨다
```

- 분할 때 **넘친 버킷 하나의 항목만** 옮긴다. 다른 버킷은 그대로다(CMU L7).
- 디렉터리를 두 배로 늘리는 일은 있다. 하지만 디렉터리는 포인터 배열이라 데이터 전체보다 훨씬 작다.
- CMU 노트는 디렉터리 칸을 해시의 **상위 비트**로 고른다고 설명한다. 교재·구현에 따라 하위 비트를 쓰기도 한다. 원리는 같다.

### 3. 선형 해싱 (Linear Hashing) — 분할 포인터가 차례로 나눈다

```text
  분할 포인터 next가 가리키는 버킷을, 넘친 버킷이 어디든 상관없이, 차례대로 나눈다

  버킷:  [0][1][2][3]            next = 0
  어느 버킷이 넘침 → 버킷 0을 나눔 → [0][1][2][3][4]      next = 1
  또 넘침         → 버킷 1을 나눔 → [0][1][2][3][4][5]   next = 2
  ...
  한 바퀴(원래 4개)를 다 나누면 → 버킷 8개, next = 0 으로 돌아간다

  위치 계산: b = h mod 8 (새 함수); 그 버킷이 아직 없으면 b = h mod 4 (옛 함수)
```

- 넘친 버킷은 당장은 오버플로 페이지로 버틴다. 차례가 오면 나뉜다(CMU L7).
- 디렉터리가 없다. 버킷 번호 계산만으로 위치를 찾는다.
- 버킷 수가 한 번에 두 배가 되지 않고 **하나씩** 는다. 그래서 확장 비용이 고르게 퍼진다.

### 4. PostgreSQL 17 해시 인덱스 — 선형 해싱의 한 형태

PostgreSQL 해시 인덱스는 "버킷 하나를 더할 때 기존 버킷 **정확히 하나**를 나눈다"(access/hash/README). 버킷 번호는 이렇게 구한다.

```c
/* src/backend/access/hash/hashutil.c  _hash_hashkey2bucket */
bucket = hashkey & highmask;
if (bucket > maxbucket)
    bucket = bucket & lowmask;
```

```text
  로컬 재현 (예시, PostgreSQL 17.11, pageinspect hash_metapage_info)
  행 3000개일 때:  maxbucket = 9, highmask = 15, lowmask = 7   → 버킷 0~9, 10개

  h = 13 (…1101):  13 & 15 = 13 > 9  → 13 & 7 = 5    (버킷 13은 아직 없다 → 옛 규칙)
  h =  9 (…1001):   9 & 15 = 9 ≤ 9   → 버킷 9        (버킷 1에서 이미 나뉘어 나온 버킷)

  다음 분할: new_bucket = maxbucket + 1 = 10,  old_bucket = 10 & lowmask = 2
             → 버킷 2의 항목 중 h & 15 = 10 인 것을 버킷 10으로 옮긴다      (hashpage.c _hash_expandtable)
```

- 분할 시점: 삽입이 끝날 때 `ntuples > ffactor × (maxbucket + 1)`이면 분할을 시도한다(hashinsert.c). 로컬 재현에서 `ffactor`는 307이었다. 3000행에서 버킷이 10개(307 × 10 = 3070), 10만 행에서 326개(maxbucket 325)였다.
  - *ffactor*: 버킷 하나에 평균 몇 개의 항목을 둘지 정한 목표값. `fillfactor`(기본 75)와 항목 크기로 계산한다.
- 항목은 **값이 아니라 4바이트 해시값**만 저장한다. 그래서 긴 값에서 B-tree보다 훨씬 작을 수 있다(문서: "may be much smaller"). 단, 같은 긴 값이 많이 반복되면 B-tree는 중복 제거(deduplication)로 키를 한 번만 저장하니 실제 크기를 재 본다(64.1.4.3). 모든 해시 인덱스 스캔은 손실(lossy)이라 힙에서 값을 다시 확인한다(PostgreSQL 17 64.6).
- 한 페이지 안의 항목은 해시값으로 정렬해 이진 탐색한다. 버킷 안 여러 페이지 사이의 순서는 없다(README).
- 제약(PostgreSQL 17 64.6)
  - 단일 컬럼만, 유일성 검사 불가(`UNIQUE` 불가), `=` 연산자만.
  - 인덱스는 줄어들지 않는다. 버킷 수를 줄이는 기능도 없다. 줄이려면 `REINDEX`.
  - **확장은 포그라운드에서 일어난다.** 삽입한 세션이 분할 비용을 낸다. 그래서 행 수가 빠르게 느는 테이블에는 맞지 않을 수 있다.
- 역사: PostgreSQL 9.6까지 해시 인덱스는 WAL에 기록되지 않았다. 크래시 후 `REINDEX`가 필요할 수 있었고 복제본에 반영되지 않아 사용이 권장되지 않았다. 10에서 WAL 기록이 추가됐다(9.6 문서 11.2, 10 릴리스 노트).

### 5. MySQL 8.4 — 해시 인덱스는 어디에 있나

```text
  InnoDB   CREATE INDEX … USING HASH  → Note 3502 "does not support the HASH index algorithm,
                                         storage engine default was used instead"  → BTREE
  MEMORY   USING HASH                  → 진짜 해시 (기본값도 HASH)
  InnoDB   적응형 해시 인덱스(AHI)       → B-tree 위에 자동으로 만드는 메모리 해시.
                                         8.4 기본 OFF (8.0 기본 ON)
```

- 로컬 재현(예시, MySQL 8.4.10): InnoDB 테이블에 `USING HASH`를 주자 Note 3502가 나오고 `information_schema.STATISTICS`의 `INDEX_TYPE`이 `BTREE`였다.
- MEMORY 엔진 해시 인덱스는 `=`·`<=>`만 쓴다. 범위 조회와 `ORDER BY`에 쓰이지 않는다. 두 값 사이에 몇 행이 있는지 추정할 수도 없다(MySQL 8.4 10.3.9). 로컬 재현에서 `k > 'a'`는 `Table scan`, `ORDER BY k`는 `Sort`였다.
- AHI는 자주 조회되는 인덱스 페이지에 대해 키 접두어로 해시를 **요청 시** 만든다. 문서는 부하가 높으면 AHI 접근 자체가 경합 지점이 될 수 있고, 워크로드마다 켜고 끈 벤치마크로 판단하라고 적는다(17.5.3). 8.4 기본값은 OFF다(17.14 `innodb_adaptive_hash_index`).

## 쓰이는 자료구조·알고리즘

- **해시 함수와 버킷 체인** — 충돌한 항목은 같은 버킷에 모이고, 넘치면 오버플로 페이지로 잇는다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **확장 해싱** — 디렉터리(2^전역깊이 칸) + 버킷별 지역 깊이. 넘친 버킷만 나누고, 필요할 때만 디렉터리를 두 배로.
- **선형 해싱** — 분할 포인터가 버킷을 차례로 나눈다. 두 해시 함수(`mod 2^i`, `mod 2^(i+1)`)를 섞어 쓴다. PostgreSQL은 `highmask`·`lowmask`로 같은 일을 한다.
- **열린 주소법(선형 탐사)·쿠쿠 해싱** — 정적 해시 테이블의 다른 충돌 처리. DB에서는 주로 조인·집계용 메모리 해시 테이블에 쓴다(CMU L7). [data-structure/29-open-addressing](../../data-structure/29-open-addressing/2-summary.md)
- **비트 마스크** — `h & (2^k − 1)` = `h mod 2^k`. 버킷 수가 2의 거듭제곱일 때 나머지 연산을 대신한다. [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md)의 "버킷 수가 바뀌면 키가 이동한다" 문제와 비교해 볼 만하다.

## 적용 — 풀어나가는 법

### 1. 해시 인덱스를 고를지 판단한다

```text
  조건                                          판단
  쿼리가 전부 =  (범위·정렬·LIKE 접두어 없음)          후보
  값이 길다 (URL, 긴 문자열)                        해시가 더 작을 수 있다 → 후보 (실제 크기 비교)
  UNIQUE·복합 키·ORDER BY 가 필요하다               B-tree
  같은 값이 매우 많다 (중복 키)                      해시는 한 버킷 체인이 길어진다 → B-tree
  행 수가 빠르게 는다                               분할이 포그라운드 → 신중
```

### 2. SQL과 진단

```sql
-- PostgreSQL 17
CREATE INDEX urls_hash ON urls USING hash (url);
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM urls WHERE url = 'https://…';

-- 버킷·오버플로 상태 (pgstattuple 확장)
SELECT bucket_pages, overflow_pages, live_items, free_percent FROM pgstathashindex('urls_hash');
-- 메타 페이지 (pageinspect 확장)
SELECT maxbucket, highmask, lowmask, ffactor, ntuples
FROM hash_metapage_info(get_raw_page('urls_hash', 0));
```

```sql
-- MySQL 8.4: 만든 인덱스가 실제로 무엇인지 확인
SHOW WARNINGS;   -- CREATE 직후 Note 3502 여부
SELECT INDEX_NAME, INDEX_TYPE FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'app' AND TABLE_NAME = 't';
SHOW ENGINE INNODB STATUS\G   -- AHI를 켰다면 INSERT BUFFER AND ADAPTIVE HASH INDEX 절, SEMAPHORES 절
```

- 로컬 재현(예시, PostgreSQL 17.11, 20만 행, URL 약 95자)

```text
  urls 테이블 26 MB
  B-tree (url) 24 MB      hash (url) 12 MB
  WHERE url = '…'  → Index Scan using urls_hash   Buffers: shared hit=3
```

## 장애 시나리오와 대처

### 1. 범위 조회에 해시 인덱스 → 인덱스 미사용

- **현상**: `id` 해시 인덱스를 만들었는데 `BETWEEN` 조회와 페이지네이션이 느리다.
- **보이는 형태**: 로컬 재현(예시, PostgreSQL 17.11)에서 `id = 42`는 `Index Scan using urls_id_hash`, `id BETWEEN 42 AND 50`은 `Parallel Seq Scan`이었다. MySQL MEMORY 엔진에서도 `k > 'a'`는 `Table scan`이었다.
- **원인**: 해시는 값의 순서를 버린다. 인접한 키가 흩어진 버킷에 있다. 해시 인덱스는 `=`만 지원한다(PostgreSQL 17 64.6, MySQL 8.4 10.3.9).
- **대처**: 범위·정렬이 하나라도 있으면 B-tree를 쓴다. 등호 전용이라고 확신할 때만 해시를 고른다.

### 2. 버킷 분할 중 삽입 지연

- **현상**: 해시 인덱스가 있는 테이블에서 대부분의 `INSERT`는 빠른데, 가끔 한 건이 튄다. 행 수가 빨리 늘 때 심하다.
- **보이는 형태**: 삽입 지연의 꼬리(p99)가 길다. 원인 추적에서 해당 인덱스가 드러난다.
- **원인**
  - 목표 적재율을 넘기면 삽입을 마친 세션이 **그 자리에서** 버킷을 나눈다. 옮길 항목을 읽고 쓰고 WAL을 남긴다. 문서도 "확장은 포그라운드에서 일어나 사용자 삽입의 실행 시간을 늘릴 수 있다"고 적는다(PostgreSQL 17 64.6).
  - 분할은 옛 버킷과 새 버킷의 **클린업 락**(배타 락 + 다른 핀 없음)이 필요하다. 그 버킷을 스캔 중인 세션이 있으면 분할을 포기한다(hashpage.c 주석: "if there is any pending scan, the split will give up"). 그동안 버킷은 오버플로 체인으로 버틴다.
- **대처**
  - 데이터를 적재한 뒤 인덱스를 만든다. 생성 시에는 필요한 크기를 추정해 버킷을 미리 잡는다(README). 로컬 재현에서 20만 행 뒤에 만든 인덱스는 바로 `maxbucket = 767`이었다.
  - 행 수가 빠르게 는다면 B-tree를 쓴다.

### 3. 중복 키가 많음 → 한 버킷의 오버플로 체인이 길다

- **현상**: 특정 값의 등호 조회가 느리다.
- **보이는 형태**: 로컬 재현(예시): 5만 행 중 4만 5천 행이 `k = 7`이었다. `pgstathashindex`에 `overflow_pages = 110`이 나오고, `k = 7` 조회가 인덱스 페이지 111개를 읽었다.
- **원인**: 같은 값은 같은 해시, 같은 버킷이다. 분할해도 그 항목들은 한 버킷을 떠나지 않는다. 문서도 "균형이 깨진 해시 인덱스는 B-tree보다 블록을 더 읽을 수 있다"고 적는다(64.6).
- **대처**: 흔한 값을 부분 인덱스 조건으로 빼거나(64.6), B-tree를 쓴다. 중복이 많은 컬럼은 애초에 해시 인덱스 후보가 아니다.

### 4. MySQL에서 `USING HASH`가 조용히 B-tree가 됨

- **현상**: 해시 인덱스를 만들었다고 생각했는데 성능 특성이 B-tree다. 설계 문서와 실제 스키마가 다르다.
- **보이는 형태**: `CREATE` 직후 `SHOW WARNINGS`에 Note 3502. `INDEX_TYPE = BTREE`.
- **원인**: InnoDB는 사용자 정의 해시 인덱스를 지원하지 않는다. 에러가 아니라 Note로 알리고 기본 알고리즘을 쓴다.
- **대처**: 스키마 리뷰에서 `information_schema.STATISTICS`로 실제 타입을 확인한다. InnoDB에서 해시 효과가 필요하면 AHI를 켜고 벤치마크로 판단한다. 경합이 보이면 `innodb_adaptive_hash_index_parts`(기본 8)를 늘리거나 끈다(17.5.3).

## 핵심 문장

- 해시 인덱스는 등호 조회만 빠르다. 값의 순서를 버리므로 범위·정렬·접두어 검색에는 쓰이지 않는다.
- 정적 해싱은 버킷 수가 고정이라 커지면 전체를 다시 만든다. 확장 해싱과 선형 해싱은 버킷 하나씩 나눠 조금씩 자란다.
- 확장 해싱은 디렉터리와 지역 깊이로 넘친 버킷만 나눈다. 선형 해싱은 분할 포인터가 차례대로 나눈다.
- PostgreSQL 해시 인덱스는 선형 해싱 방식이다. 4바이트 해시만 저장해 긴 값에서 B-tree보다 작을 수 있고, 분할은 삽입 세션이 포그라운드에서 한다.
- MySQL InnoDB는 `USING HASH`를 B-tree로 바꾼다. 사용자가 만드는 해시 인덱스는 MEMORY·NDB 엔진에 있고, InnoDB에는 내부용 적응형 해시 인덱스(8.4 기본 OFF)가 있다.

## 관련 주제·근거

- 선행: [07-buffer-pool](../07-buffer-pool/2-summary.md) · [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- 연결
  - [08-btree-indexes](../08-btree-indexes/2-summary.md) — 해시와 비교할 기본 인덱스
  - [09-index-design](../09-index-design/2-summary.md) — 등호·범위 조건과 인덱스 선택
  - [11-join-algorithms](../11-join-algorithms/2-summary.md) — 해시 조인의 메모리 해시 테이블
  - [53-index-concurrency-control](../53-index-concurrency-control/2-summary.md) — 해시 테이블 래치(페이지 래치·슬롯 래치)
  - [data-structure/29-open-addressing](../../data-structure/29-open-addressing/2-summary.md) · [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md)
- 강의·문서·소스
  - CMU 15-445 Fall 2024 L7 "Hash Tables"(정적 해싱·선형 탐사·쿠쿠, 체인·확장·선형 해싱) <https://15445.courses.cs.cmu.edu/fall2024/notes/07-hashtables.pdf>
  - PostgreSQL 17: 64.6 Hash Indexes(단일 컬럼·`=`만·UNIQUE 불가·4바이트 해시·오버플로·포그라운드 확장·축소 불가) <https://www.postgresql.org/docs/17/hash-index.html> · 64.1.4.3 B-Tree Deduplication <https://www.postgresql.org/docs/17/btree.html> · F.23 pageinspect(`hash_metapage_info`) · F.31 pgstattuple(`pgstathashindex`)
  - PostgreSQL 소스 REL_17_STABLE: `src/backend/access/hash/README`(분할·락·메타페이지 캐시) · `hashutil.c` `_hash_hashkey2bucket` · `hashinsert.c`(분할 조건) · `hashpage.c` `_hash_expandtable` · `src/include/access/hash.h`(`HASH_DEFAULT_FILLFACTOR` 75) <https://github.com/postgres/postgres/tree/REL_17_STABLE/src/backend/access/hash>
  - PostgreSQL 9.6 문서 11.2(해시 인덱스 WAL 미기록 경고) · PostgreSQL 10 릴리스 노트("Add write-ahead logging support to hash indexes")
  - MySQL 8.4: 10.3.9 Comparison of B-Tree and Hash Indexes · 17.5.3 Adaptive Hash Index · 17.14 `innodb_adaptive_hash_index`(8.4 기본 OFF; 8.0 문서 기본 ON) · 18.3 The MEMORY Storage Engine <https://dev.mysql.com/doc/refman/8.4/en/index-btree-hash.html> · 15.1.15 CREATE INDEX(표 15.1 엔진별 인덱스 유형: MEMORY·NDB = HASH, BTREE) <https://dev.mysql.com/doc/refman/8.4/en/create-index.html>
  - W. Litwin, "Linear Hashing: A New Tool for File and Table Addressing", VLDB 1980 · R. Fagin 외, "Extendible Hashing", ACM TODS 1979 — 원문 미열람 [?]
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): 해시 인덱스 성장(행 수별 maxbucket·highmask·lowmask), 범위 조회 미사용, URL 해시 vs B-tree 크기, 중복 키 오버플로 체인, InnoDB `USING HASH` → BTREE(Note 3502), MEMORY 해시의 범위·정렬 미사용, AHI 기본값
