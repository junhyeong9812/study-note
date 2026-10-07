# data-engineering/14-lakehouse-table-formats — 레이크하우스 테이블 포맷: 메타데이터 트리, 스냅샷 격리, time travel, 만료·compaction — 정리 (힌트)

## 해결하는 문제

데이터 레이크는 여러 형식의 데이터를 값싼 저장소에 쌓아 둔 것이다. 흔한 모양은 객체 저장소(S3 같은 곳)에 Parquet 파일을 쌓는 것이다(HDFS·다른 형식도 쓴다).\
"테이블"은 디렉터리 하나일 뿐이다. 그러면 DB가 해 주던 일이 사라진다.

```text
  디렉터리 = 테이블일 때
  s3://lake/orders/day=2026-10-01/part-000.parquet ... part-199.parquet

  쓰기 잡이 200개 중 120개를 쓰고 죽었다   → 읽는 쪽은 120개를 본다 (반쯤 쓴 테이블)
  두 잡이 같은 파티션을 동시에 덮어쓴다     → 누가 이겼는지 모른다
  "지금 테이블에 어떤 파일이 있나?"         → 디렉터리를 나열(list)해야 한다. 파티션 수만큼 느리다
```

- Iceberg 문서 "Reliability"의 진단: Hive 테이블은 파티션은 메타스토어에, 파일은 파일 시스템에 따로 추적한다. 그래서 테이블 내용을 원자적으로 바꿀 수 없고, 계획에 파티션 수 n에 비례하는 느린 나열 호출이 든다.
- 해법: 파일 목록 자체를 **메타데이터로** 관리하고, "현재 상태"를 원자적으로 한 번에 바꾼다. Iceberg는 현재 메타데이터를 가리키는 포인터 하나를 바꾸고, Delta는 다음 번호 로그 파일을, Hudi는 타임라인 완료 파일을 만든다(5절).
  - *테이블 포맷(table format)*: 객체 저장소의 불변 파일 묶음을 테이블처럼 쓰게 해 주는 메타데이터 규약. Apache Iceberg, Delta Lake, Apache Hudi가 대표다.
  - *레이크하우스(Lakehouse)*: 값싸고 직접 접근 가능한 저장소 위에 ACID 트랜잭션·버전 관리·감사·인덱스 같은 분석 DBMS 기능을 얹은 시스템(Armbrust 외, CIDR 2021의 정의).

쉬운 예: 도서관 서가와 목록 카드다.
- 서가를 한 칸씩 돌며 "지금 무슨 책이 있나" 세는 대신, 목록 카드 묶음을 본다.
- 새 책을 들이면 새 카드 묶음을 만들고, 안내 데스크의 "현재 카드 묶음" 표지판만 바꿔 단다.
- 표지판을 바꾸기 전에는 아무도 새 책을 못 본다. 바꾼 뒤에는 한꺼번에 본다.

똑같은 구조다.\
옛 카드 묶음을 버리지 않으면 "지난주의 서가"도 볼 수 있다. 이것이 time travel이다.\
대신 옛 묶음과 거기만 걸린 책을 언젠가 치워야 한다. 이것이 스냅샷 만료다.

실무 예:
- 스트리밍 적재가 1분마다 작은 파일을 만들어, 쿼리 계획 단계만 몇 초가 걸린다.
- 스냅샷 만료를 안 돌려 저장 비용이 매달 는다.
- 감사 요청으로 "지난달 말 테이블"을 time travel로 읽으려 했더니 그 스냅샷은 이미 만료되었다.

## 동작·원리

### 1. Iceberg 메타데이터 트리

```text
  카탈로그 ──포인터──> metadata v3.json           (스키마, 파티션 규칙, 스냅샷 목록, current-snapshot-id)
                        │ snapshots: S1, S2, S3
                        ▼ S3.manifest-list
                      snap-S3 manifest list        (매니페스트마다: 경로, 파티션 요약 lower/upper, 파일 수)
                        ├── manifest A  ───────>  data-001.parquet (day=10-01, 행 수, 컬럼 min/max)
                        │   (S1·S2·S3가 공유)        data-002.parquet ...
                        └── manifest B (S3에서 추가) ─> data-101.parquet (day=10-02 ...)
```

- *스냅샷(snapshot)*: 어느 시점의 테이블 상태. 그때의 데이터 파일 전체 집합이다(Iceberg Spec "Terms").
- *매니페스트(manifest)*: 데이터 파일(또는 삭제 파일) 목록. 파일마다 파티션 값과 통계(행 수, 컬럼 상·하한)를 담은 불변 Avro 파일이다(Spec "Manifests").
- *매니페스트 리스트(manifest list)*: 스냅샷 하나를 이루는 매니페스트들의 목록. 스냅샷마다 하나다(Spec "Terms").
- 매니페스트는 스냅샷 사이에 **재사용**된다. 새 커밋은 바뀐 부분의 매니페스트만 새로 쓴다(Spec "Overview"). Iceberg 문서 "Reliability"는 이것을 "persistent tree structure"라고 부른다.
- Iceberg Spec의 목표: 스캔 계획에 테이블 크기에 비례하지 않는 O(1)번의 원격 호출(Spec "Goals").

### 2. 커밋 = 포인터 하나의 원자적 교체 (낙관적 동시성)

```text
  writer A: base = v3 ─ 파일·매니페스트 작성 ─ v4-A.json 작성 ─ CAS(v3 → v4-A) ✔ 성공
  writer B: base = v3 ─ 파일·매니페스트 작성 ─ v4-B.json 작성 ─ CAS(v3 → v4-B) ✘ 이미 v4-A
            └─ 재시도: base = v4-A로 다시 읽고, 조건을 확인한 뒤 매니페스트 리스트·메타데이터만 다시 써서 CAS
```

- *낙관적 동시성(optimistic concurrency)*: 잠그지 않고 진행한 뒤, 커밋 때 "내 기준 버전이 아직 현재인가"를 확인한다. 아니면 다시 한다. → [database/17-occ-and-timestamp-ordering](../../database/17-occ-and-timestamp-ordering/2-summary.md)
- *CAS(compare-and-swap) / check-and-put*: "값이 아직 X이면 Y로 바꾼다"를 한 번에 하는 연산.
- 원자적 교체를 어떻게 하느냐는 명세가 정하지 않는다(Spec "Table Metadata"). 예시 두 가지
  - 메타스토어 테이블: 메타스토어·DB에 포인터를 두고 check-and-put으로 바꾼다(Spec "Metastore Tables").
  - 파일 시스템 테이블: `v<V+1>.metadata.json`으로의 원자적 rename. 명세는 이 방식을 **폐기 예정**(deprecated)으로 표시하고 "객체 저장소와 로컬 파일 시스템에서 안전하지 않다", "명세 v4에서 제거된다"고 적는다(Spec "File System Tables").
- 재시도할 때 무엇을 확인하나(Spec "Commit Conflict Resolution and Retry")

| 작업 | 다른 커밋이 먼저 끝났을 때 |
|---|---|
| append(파일 추가) | 조건 없음 — 그대로 다시 적용(명세: "can always be applied") |
| replace(compaction·포맷 변환) | 지울 파일들이 **아직 테이블에 있는지** 확인 |
| 파일 지정 delete | 지울 파일들이 아직 있는지 확인 |
| 식 기반 delete(`timestamp < X`) | 다시 적용 가능 |
| 스키마·파티션 규칙 변경 | 기준 버전과 현재 버전 사이에 스키마가 안 바뀌었는지 확인 |

- Iceberg 기본 재시도 설정(Iceberg 1.12 문서 "Configuration"): `commit.retry.num-retries`=4, `commit.retry.min-wait-ms`=100, `commit.retry.max-wait-ms`=60000, `commit.retry.total-timeout-ms`=1800000(30분).

### 3. 스냅샷 격리와 time travel

- 읽는 쪽은 테이블 메타데이터를 읽을 때의 스냅샷을 쓴다. 새로 고치기 전까지 다른 커밋의 영향을 받지 않는다. 읽는 쪽은 잠그지 않는다(Spec "Optimistic Concurrency", "Goals").
  - [database/16-mvcc](../../database/16-mvcc/2-summary.md)와 같은 발상이다. 옛 버전(옛 파일)을 남겨 두고 읽는 쪽이 자기 버전을 고른다. Delta 프로토콜도 "Delta's transactions are implemented using multi-version concurrency control (MVCC)"라고 적는다.
- *time travel*: 과거 스냅샷을 지정해 읽기. Iceberg Spark 문서의 문법

```sql
SELECT * FROM prod.db.orders TIMESTAMP AS OF '2026-09-30 23:59:59';
SELECT * FROM prod.db.orders VERSION AS OF 10963874102873;      -- 스냅샷 ID, 또는 브랜치·태그 이름
```

- 시각 기준 조회는 `snapshot-log`로 그 시각 직전 스냅샷을 찾는다. 해당 스냅샷이 없으면 "정보가 부족하다는 오류를 내야 한다"(Spec Appendix F "Point in Time Reads").
- 태그·브랜치로 참조된 스냅샷은 만료되지 않는다. 브랜치·태그 자체도 기본으로 만료되지 않는다 — `history.expire.max-ref-age-ms`(기본 `Long.MAX_VALUE`)를 줄이면 main 외의 참조도 만료될 수 있다(Iceberg Spark Procedures `expire_snapshots`, Configuration).

### 4. 만료·고아 파일·compaction — MVCC의 VACUUM에 해당

```text
  쓰기마다 스냅샷 +1 ──> 옛 스냅샷이 옛 파일을 붙잡는다 ──> 저장 비용 ↑
                                │
  expire_snapshots ── 스냅샷을 메타데이터에서 지우고, 남은 스냅샷 어디에도 안 걸린 파일을 지운다
  remove_orphan_files ── 어떤 메타데이터에도 없는 파일(실패한 잡의 잔해)을 지운다
  rewrite_data_files ── 작은 파일 여러 개 → 큰 파일 몇 개 (새 스냅샷: replace)
  rewrite_manifests  ── 매니페스트를 재배치해 계획을 빠르게
```

| Iceberg 1.12 설정·인자 | 기본값 | 출처 |
|---|---|---|
| `history.expire.max-snapshot-age-ms` | 432000000 (5일) | Configuration |
| `history.expire.min-snapshots-to-keep` | 1 | Configuration |
| `expire_snapshots` `older_than` / `retain_last` | 5일 전 / 1 | Spark Procedures |
| 고아 파일 삭제의 보존 간격 | 3일 | Maintenance |
| `write.target-file-size-bytes` | 536870912 (512 MB) | Configuration |
| `write.metadata.delete-after-commit.enabled` / `previous-versions-max` | false / 100 | Maintenance |

- 만료한 스냅샷은 time travel로 읽을 수 없다(Maintenance "Expire Snapshots").
- 고아 파일 삭제 간격을 쓰기 시간보다 짧게 잡으면, 진행 중인 쓰기의 파일을 고아로 보고 지워 테이블을 망가뜨릴 수 있다(Maintenance "Delete orphan files").
- "small data files causes an unnecessary amount of metadata and less efficient queries from file open costs"(Maintenance "Compact data files").
- 이것은 [database/16-mvcc](../../database/16-mvcc/2-summary.md)의 VACUUM, [database/38-lsm-storage-engine](../../database/38-lsm-storage-engine/2-summary.md)·[database/45-clickhouse-mergetree](../../database/45-clickhouse-mergetree/2-summary.md)의 병합과 같은 자리의 일이다. 쓰기를 싸게 하려고 남긴 조각을 뒤에서 정리한다.

### 5. 세 포맷 — 같은 문제, 다른 메타데이터 모양

```text
  Iceberg   metadata.json ─> manifest list ─> manifests(Avro) ─> data files     커밋: 카탈로그 포인터 CAS
  Delta     _delta_log/00000000000000000000.json, ...01.json, ... + checkpoint   커밋: 다음 번호 로그 파일 생성(덮어쓰기 금지)
  Hudi      .hoodie/ timeline: <요청 instant>.<action>.<state>, 완료는 <요청 instant>_<완료 instant>.<action>   커밋: 타임라인 상태 전이 + 락
```

- **Delta Lake**(PROTOCOL.md)
  - 테이블은 연속 정수 버전의 직렬 이력이다. 버전 v의 로그 파일은 20자리 0 채움 번호의 JSON이다(`_delta_log/00000000000000000000.json`).
  - 로그 파일 하나가 원자성의 단위다. 그 안의 `add`·`remove` 액션을 앞 상태에 적용하면 v번째 스냅샷이 된다.
  - 쓰는 쪽은 기존 로그 항목을 **덮어쓰면 안 된다**. 가능하면 저장소의 원자적 기본 연산으로 동시 작성자가 서로 덮어쓰지 않게 한다("Creation of New Log Entries"). 카탈로그 관리 테이블 절은 PUT-if-absent를 예로 든다.
  - 체크포인트는 그 버전까지의 액션을 다시 정리한 파일이다. 읽는 쪽이 로그 전체를 재생하지 않게 한다.
  - `remove` 액션은 만료될 때까지 *툼스톤*(tombstone)으로 남아 VACUUM이 실제 파일을 지울 때 쓴다. 더 이상 최신 버전에 없는 파일은 사용자 지정 보존 기간(기본 7일) 뒤 vacuum 명령이 지울 수 있다("Overview").
    - 7일은 Overview 문단이 vacuum 명령의 기본값으로 언급한 것이다. 프로토콜 본문은 툼스톤 만료를 "`remove` 타임스탬프 + 만료 임계값"으로만 정하고 일수를 요구하지 않는다("Add File and Remove File"). 구현 기본값으로 읽는다(해석).
- **Apache Hudi**(문서 "Timeline", "Concurrency Control")
  - 테이블 변경을 *타임라인*의 액션으로 기록한다. 액션은 REQUESTED → INFLIGHT → COMPLETED로 전이한다. 전이마다 파일 하나가 생긴다 — REQUESTED·INFLIGHT는 `<requested instant>.<action>.<state>`, COMPLETED는 `<requested instant>_<completed instant>.<action>`(문서 "Timeline" "State Transitions").
  - 액션 종류에 COMMIT·DELTA_COMMIT·REPLACE_COMMIT·CLEANS·COMPACTION·CLUSTERING 등이 있다. 정리·병합을 "테이블 서비스"로 따로 부른다.
  - 쓰기 사이에는 OCC를, 쓰기와 테이블 서비스 사이에는 MVCC를 쓴다고 적는다. 다중 작성자는 분산 락 제공자가 전제다.
  - 시점 차이: CIDR 2021 논문은 "Hudi는 동시 작성자를 지원하지 않는다"고 적었다. 2026-10 현재 Hudi 문서는 OCC·NBCC 다중 작성을 설명한다. 논문 서술은 2021년 기준이다.
- CIDR 2021의 공통 한계 지적: Delta Lake·Iceberg·Hudi는 한 번에 테이블 하나에 대한 트랜잭션만 지원한다(논문 3.2절 "Metadata Layers for Data Management"의 Future Directions 문단).

### 6. 행 단위 삭제 (Iceberg)

- 데이터 파일은 불변이다. 행 몇 개를 지우려면 두 가지 길이 있다.
  - 파일을 새로 써서 바꾼다(copy-on-write). 테이블 데이터가 바뀌므로 스냅샷 operation은 `overwrite`·`delete`다. `replace`는 데이터가 그대로인 재작성(compaction·포맷 변환)을 뜻한다(Spec 스냅샷 `operation` 값).
  - *삭제 파일*을 따로 적는다(Spec v2 "Row-level Deletes"). 위치 삭제(파일 경로 + 행 위치)와 동등 삭제(`id = 5` 같은 값)가 있다. v3는 위치 삭제를 바이너리 *삭제 벡터*(deletion vector)로 담는다.
- 삭제 파일은 읽을 때 데이터 파일에 적용된다. 쌓일수록 읽기가 느려지므로 compaction 대상이다(Maintenance "Rewrite position delete files").
- 명세 v4(개발 중, 미채택)에서는 동등 삭제를 새로 쓰는 것이 허용되지 않는다(Spec "Version 4").

### 실험: 테이블 포맷 모형 — CAS 커밋, compaction 검증, 만료, 작은 파일

- **모형이다.** Iceberg 라이브러리가 아니라, 명세의 구조(불변 객체 + 포인터 CAS + 메타데이터 → 매니페스트 리스트 → 매니페스트 → 데이터 파일)를 Java로 흉내 냈다. 실제 도구 동작은 위 1차 문서로 뒷받침한다.
- 환경: `eclipse-temurin:21-jdk`(JDK 21.0.12), `--network none --cpus=2`, i7-13700HX 호스트. 프로그램을 5번 실행(집필 2번 + 점검 3번 — 실험 A는 실행마다 3회라 15회).

```java
// 카탈로그 포인터 = AtomicReference<String>. 커밋 = 기준 메타데이터 경로에서 새 경로로 CAS
boolean commit(String basePath, TableMetadata base, List<ManifestEntry> newList, String op) {
    String mlPath = store.put("manifest-list", List.copyOf(newList));     // 시도마다 새 매니페스트 리스트
    Snapshot ns = new Snapshot(snapIds.incrementAndGet(), cur.id, cur.seq + 1, now, mlPath, op);
    String newPath = store.put("metadata", new TableMetadata(snaps, ns.id, base.version + 1));
    if (useCas) return pointer.compareAndSet(basePath, newPath);
    pointer.set(newPath); return true;                                    // 잘못된 구현: 그냥 덮어쓴다
}
// append: 매니페스트는 한 번만 쓰고 재시도 때 재사용
// compaction: 재시도 전에 "원본 파일이 아직 다 살아 있나" 검증 (validate 플래그)
```

출력(5번 실행의 범위):

```text
  A. 동시 append 8 writer × 50 commit (커밋당 파일 1개·100행, 기대 400파일·40000행)
     CAS       : live 파일 400, 행 40000 (15회 모두)  CAS 실패 971~1447, 총 시도 1371~1847
     덮어쓰기   : live 파일 59~96, 행 5900~9600        CAS 실패 0 (오류 없음)
  B. compaction(10-01의 작은 파일 4개 → 1개) 도중 그 파일 하나를 지우는 커밋이 먼저 끝남 (정답 500행)
     검증 O: ABORT: 원본 파일 중 일부가 이미 지워짐 → 커밋 포기   최종 500행
     검증 X: COMMITTED (attempt 2)                                최종 600행  ← 지운 100행 부활
  C. 스냅샷 6개(create, append×4, replace) → 최근 1개만 남기고 만료
     data 객체 13 → 10 (지운 파일 3 = compaction 전 작은 파일)
     time travel AS OF snapshot 3 → 실패: 메타데이터에 없는 스냅샷
  D. 하루 1,000,000행을 파일 N개로, 10일치. id 10개 범위 질의 계획(7회 중앙값)
     N=     10: 훑은 항목      10, 열 파일 1(읽을 행 100,000), 계획 0.02 ~ 0.06 ms
     N=  1,000: 훑은 항목   1,000, 열 파일 1(읽을 행   1,000), 계획 1.12 ~ 2.37 ms
     N= 10,000: 훑은 항목  10,000, 열 파일 1(읽을 행     100), 계획 14.46 ~ 18.14 ms
     N=100,000: 훑은 항목 100,000, 열 파일 1(읽을 행      10), 계획 63.08 ~ 81.18 ms
```

- 관찰 A: 검사 없는 덮어쓰기는 예외 하나 없이 커밋의 약 76~85%를 잃었다. CAS는 실패한 만큼 다시 해서 하나도 잃지 않았다. 대신 CAS 실패가 커밋 수(400)의 약 2.4~3.6배(971~1447번)였다. 유실·실패 수는 스레드 경합에 따라 실행마다 달라진다.
- 관찰 B: 재시도는 "다시 적용해도 되는가" 검증과 짝이다. 검증 없이 다시 적용하면 오류 없이 지운 행이 되살아난다. 명세가 replace에 파일 존재 확인을 요구하는 이유다.
- 관찰 D: 매니페스트 리스트의 파티션 요약 덕분에 다른 날짜의 매니페스트는 건너뛰었다. 같은 날짜 안에서는 파일 수만큼 항목을 훑었다. 파일이 작을수록 읽을 행은 줄었지만 계획 시간은 파일 수에 비례해 늘었다.
- 한계: 모형의 계획은 메모리 안 파싱이다. 실제로는 매니페스트 읽기가 원격 GET이고, 파일 열기 비용이 따로 든다(Maintenance 문서). 그 비용은 측정하지 않았다.

## 쓰이는 자료구조·알고리즘

- **영속(persistent) 트리 — 구조 공유** — 새 스냅샷은 바뀐 매니페스트만 새로 쓰고 나머지를 공유한다. [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md)
- **Merkle 트리와 닮은 점·다른 점** — 루트(메타데이터)에서 잎(데이터 파일)까지 내려가는 불변 트리이고 부분을 공유한다는 점이 닮았다. 다만 Iceberg 매니페스트 리스트 항목에는 자식 매니페스트의 경로·길이·통계가 있고 내용 해시는 없다(Spec "Manifest Lists" 필드 표). 그래서 해시로 위변조를 검증하는 Merkle 트리는 아니다. [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md)
- **CAS와 낙관적 재시도** — 포인터 하나의 compare-and-swap으로 직렬 이력을 만든다. 재시도 전 전제 조건 검증이 짝이다. [database/17-occ-and-timestamp-ordering](../../database/17-occ-and-timestamp-ordering/2-summary.md), [distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md)
- **min/max 통계로 가지치기(zone map)** — 매니페스트 리스트의 파티션 상·하한, 매니페스트의 컬럼 상·하한으로 볼 필요 없는 매니페스트·파일을 건너뛴다. PostgreSQL BRIN·ClickHouse 그래뉼과 같은 발상이다([database/45-clickhouse-mergetree](../../database/45-clickhouse-mergetree/2-summary.md)).
- **MVCC + 가비지 수집** — 옛 스냅샷 = 옛 버전, 스냅샷 만료·고아 파일 삭제 = VACUUM. [database/16-mvcc](../../database/16-mvcc/2-summary.md)
- **병합(compaction)** — 작은 파일을 묶어 큰 파일로. LSM의 병합과 같은 "쓰기 증폭 vs 읽기 비용" 거래다. [data-structure/24-lsm-tree](../../data-structure/24-lsm-tree/2-summary.md)
- **컬럼 저장 파일 포맷** — 데이터 파일은 보통 Parquet·ORC 같은 컬럼 포맷이다. Iceberg 명세는 행 지향인 Avro 데이터 파일도 허용한다(Spec "Version 1": Parquet, Avro, ORC). [database/37-row-vs-column-storage](../../database/37-row-vs-column-storage/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 증상 → 원인 → 확인 순서

| 증상 | 원인 후보 | 확인 |
|---|---|---|
| 쿼리 실행은 1초인데 전체가 10초, 엔진 로그에 계획 단계가 길다 | 작은 파일 폭증·매니페스트 난립 | `files`·`partitions`·`manifests` 메타데이터 테이블 |
| 테이블 데이터는 그대로인데 저장 비용이 매달 는다 | 스냅샷 만료·고아 파일 삭제를 안 돌림 | `snapshots` 개수·가장 오래된 `committed_at` |
| time travel 쿼리가 "스냅샷 없음"으로 실패 | 만료 정책이 감사 요구보다 짧다 | `history`·`snapshots`, 테이블 속성 |
| 동시 쓰기 잡이 가끔 실패·재시도 폭증 | 같은 파티션을 동시에 replace·delete | 엔진 로그의 커밋 충돌 예외, 재시도 횟수 |
| 지운 행이 다시 나타났다 | 검증 없이 재적용한 커스텀 커밋 코드(모형 실험 B) | 스냅샷별 `operation`·`summary` 비교 |

### 2. 진단 쿼리 (Iceberg Spark 메타데이터 테이블 — Iceberg 1.12 문서 "Spark Queries — Inspecting tables")

```sql
-- 파티션별 파일 수와 평균 파일 크기: 작은 파일 후보
SELECT partition, file_count, record_count,
       total_data_file_size_in_bytes / file_count AS avg_file_bytes
FROM prod.db.orders.partitions
ORDER BY file_count DESC LIMIT 20;

-- 스냅샷이 몇 개 쌓였나, 가장 오래된 것은 언제인가
SELECT count(*), min(committed_at), max(committed_at) FROM prod.db.orders.snapshots;

-- 커밋 종류와 요약(추가·삭제 파일 수)
SELECT committed_at, snapshot_id, operation, summary FROM prod.db.orders.snapshots ORDER BY committed_at DESC LIMIT 20;

-- 매니페스트 수와 크기
SELECT count(*), sum(length) FROM prod.db.orders.manifests;
```

### 3. 유지보수 작업 (Iceberg Spark 프로시저)

```sql
-- 5일보다 오래된 스냅샷 만료, 최근 100개는 유지 (값은 예시)
CALL prod.system.expire_snapshots(table => 'db.orders', older_than => TIMESTAMP '2026-10-02 00:00:00', retain_last => 100);
-- 작은 파일 병합 (기본 binpack)
CALL prod.system.rewrite_data_files(table => 'db.orders');
-- 매니페스트 재배치
CALL prod.system.rewrite_manifests('db.orders');
-- 고아 파일 삭제: 보존 간격을 가장 긴 쓰기 잡보다 길게 (기본 3일)
CALL prod.system.remove_orphan_files(table => 'db.orders');
```

- 순서: compaction → 만료(옛 작은 파일이 이제 어느 스냅샷에도 안 걸린다) → 고아 파일 삭제.
- 감사·재처리에 필요한 시점은 **태그**로 고정한다. 태그가 가리키는 스냅샷은 만료되지 않는다(참조 보존 기간 `history.expire.max-ref-age-ms`를 기본 무기한으로 둘 때).

### 4. 쓰기 설계

- 스트리밍 적재는 커밋 간격을 너무 짧게 잡지 않는다. 커밋마다 스냅샷·매니페스트 리스트·메타데이터 파일이 생긴다.
- 같은 파티션을 여러 잡이 덮어쓰거나(overwrite) 재작성(replace)하지 않게 파티션 소유를 나눈다. 충돌하면 재시도하는데, 재시도는 계산을 다시 하는 비용이다.
- 앱 코드가 메타데이터를 직접 고치지 않는다. 엔진·라이브러리의 커밋 API를 쓴다. 모형 실험 A의 "덮어쓰기"처럼 직접 구현한 커밋은 조용히 데이터를 잃을 수 있다.

## 장애 시나리오와 대처

### 1. 작은 파일 폭증 → 계획 시간이 실행 시간보다 길다

- **현상**: 쿼리 하나가 실행보다 계획에서 더 오래 걸린다. 스트리밍 적재를 시작한 뒤 점점 심해진다.
- **보이는 형태**: `partitions`의 `file_count`가 파티션당 수만, 평균 파일 크기가 수 MB 이하(예시). 모형 실험 D에서 파일이 10개 → 100,000개로 늘자 같은 질의의 계획 시간이 0.02~0.06ms → 63~81ms(중앙값)로 늘었다.
- **원인**: 커밋마다 작은 파일과 매니페스트 항목이 생긴다. 계획은 항목 수에 비례하고, 실행은 파일 열기 비용을 파일 수만큼 낸다(Maintenance 문서).
- **대처**: `rewrite_data_files`로 병합하고 `rewrite_manifests`로 매니페스트를 정리한다. 적재 커밋 간격을 늘리거나 쓰기 전에 모은다. 목표 파일 크기(`write.target-file-size-bytes`, 기본 512MB)를 확인한다.

### 2. 스냅샷을 만료시키지 않는다 → 저장 비용이 계속 는다

- **현상**: 행 수는 그대로인데 버킷 용량과 비용이 매달 오른다.
- **보이는 형태**: `snapshots`가 수만 개, 가장 오래된 `committed_at`이 몇 달 전. compaction을 돌렸는데도 용량이 안 준다.
- **원인**: 옛 스냅샷이 옛 파일을 붙잡는다. compaction은 새 파일을 쓰고 옛 파일을 "현재"에서만 뺀다. 만료 전에는 지우지 않는다. 모형 실험 C에서 만료 전 data 객체 13, 만료 후 10이었다.
- **대처**: `expire_snapshots`를 정기 작업으로 돌린다. 이어서 `remove_orphan_files`로 실패한 잡의 잔해를 지운다.

### 3. 만료 후 time travel 쿼리 실패

- **현상**: "9월 말 기준으로 다시 뽑아 달라"는 감사 요청에 `TIMESTAMP AS OF` 쿼리가 실패한다.
- **보이는 형태**: 스냅샷이 없다는 오류. 모형 실험 C의 "메타데이터에 없는 스냅샷". 명세는 해당 시각 이전 스냅샷이 없으면 정보가 부족하다는 오류를 내라고 한다.
- **원인**: 만료 정책(예: 5일)이 업무의 재현 요구(월말 마감)보다 짧다.
- **대처**: 재현해야 하는 시점은 태그로 고정한다(브랜치·태그는 기본으로 만료되지 않는다). 장기 보존이 필요한 숫자는 time travel에 기대지 말고 별도 스냅샷 테이블로 남긴다([database/50-temporal-and-bitemporal-tables](../../database/50-temporal-and-bitemporal-tables/2-summary.md)).

### 4. 동시 커밋 충돌 → 쓰기 재시도·실패

- **현상**: 같은 테이블에 쓰는 잡 둘이 가끔 실패한다. 실패하지 않아도 지연이 커진다.
- **보이는 형태**: 엔진 로그의 커밋 충돌 예외(구체 예외 이름은 엔진마다 다르다 `[?]`), 재시도 횟수 증가. 모형 실험 A에서 8개 작성자가 경합하자 400커밋에 시도 1371~1847번이 들었다.
- **원인**: 낙관적 동시성이다. 같은 기준 버전에서 출발한 커밋은 하나만 성공한다. append는 다시 적용되지만, 같은 파일을 건드리는 replace·delete는 검증에 실패하면 포기해야 한다.
- **대처**: 파티션별로 잡의 소유를 나눈다. compaction은 적재가 덜 붐비는 시간에 파티션 단위로 돌린다. 재시도 설정(`commit.retry.*`)은 증상 완화일 뿐이다.

### 5. 고아 파일 삭제가 진행 중인 쓰기를 지운다

- **현상**: 정리 작업 직후 일부 쿼리가 "파일 없음"으로 실패한다.
- **보이는 형태**: 커밋된 매니페스트가 가리키는 데이터 파일이 객체 저장소에 없다.
- **원인**: 보존 간격을 쓰기 잡 시간보다 짧게 잡아, 아직 커밋 전인 파일을 고아로 보고 지웠다(Maintenance 문서의 경고). 경로 표기가 바뀐 경우(HDFS authority 변경 등)도 같은 문서가 데이터 손실 위험으로 든다.
- **대처**: 보존 간격을 가장 긴 쓰기 잡보다 넉넉히 둔다(기본 3일). 경로 표기를 바꾼 뒤에는 실행 전에 메타데이터의 경로와 실제 나열 결과를 대조한다.

## 핵심 문장

- 테이블 포맷은 "디렉터리 = 테이블"을 "메타데이터 = 테이블"로 바꾼다. 커밋은 현재 상태의 원자적 교체다 — Iceberg는 포인터 하나의 교체, Delta는 다음 번호 로그 파일, Hudi는 타임라인 완료 파일.
- 읽는 쪽은 자기가 읽은 스냅샷을 끝까지 본다. 옛 스냅샷이 남아 있어 time travel이 되고, 그 대가로 만료·고아 파일 정리가 필요하다.
- 동시 커밋은 낙관적으로 처리한다. 재시도는 "다시 적용해도 되나" 검증과 짝이고, 검증 없는 재적용은 지운 행을 되살릴 수 있다.
- 작은 파일은 메타데이터 항목과 파일 열기를 늘려 계획·실행 비용을 키운다. 심하면 계획 시간이 실행 시간보다 길어질 수 있다(모형 실험 D는 계획 시간만 쟀다). compaction과 매니페스트 재작성이 해법이다.
- Iceberg·Delta·Hudi는 같은 문제를 다른 메타데이터 모양(매니페스트 트리·번호 로그·타임라인)으로 푼다. 동작은 도구 문서로 확인한다.

## 관련 주제·근거

- 선행
  - [02 oltp-olap-and-warehouse](../02-oltp-olap-and-warehouse/2-summary.md) — 분석 저장소의 자리
  - [database/16-mvcc](../../database/16-mvcc/2-summary.md) — 스냅샷·옛 버전·가비지 수집
- 연결
  - [database/17-occ-and-timestamp-ordering](../../database/17-occ-and-timestamp-ordering/2-summary.md) · [database/37-row-vs-column-storage](../../database/37-row-vs-column-storage/2-summary.md) · [database/38-lsm-storage-engine](../../database/38-lsm-storage-engine/2-summary.md) · [database/45-clickhouse-mergetree](../../database/45-clickhouse-mergetree/2-summary.md)
  - [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md) · [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md) · [data-structure/24-lsm-tree](../../data-structure/24-lsm-tree/2-summary.md)
  - [distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md) — CAS로 하는 조정
  - [13-data-vault](../13-data-vault/2-summary.md) — 볼트 테이블을 레이크하우스에 둘 때 insert-only 패턴과 잘 맞는다(해석)
  - [08 idempotent-pipelines-and-backfill](../08-idempotent-pipelines-and-backfill/2-summary.md) — 파티션 덮어쓰기는 Iceberg에서 `overwrite` 스냅샷(파일을 빼고 더하는 논리적 덮어쓰기)이다. `replace`는 데이터를 바꾸지 않는 재작성(compaction 등)에만 쓴다(Spec 스냅샷 `operation` 값)
- 근거
  - Armbrust, Ghodsi, Xin, Zaharia, "Lakehouse: A New Generation of Open Platforms that Unify Data Warehousing and Advanced Analytics", CIDR 2021 <https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf> — 3절 정의, 3.2절 메타데이터 계층(Delta·Iceberg·Hudi, 한 테이블 트랜잭션 한계, 당시 Hudi 단일 작성자).
  - Apache Iceberg Table Spec <https://iceberg.apache.org/spec/> — Format Versioning(v1~v3 채택, v4 개발 중), Goals, Overview, Optimistic Concurrency, Manifests, Manifest Lists, Snapshot Retention Policy, Table Metadata, Commit Conflict Resolution and Retry, File System Tables(폐기 예정), Metastore Tables, Appendix F Point in Time Reads. (2026-10-07 열람)
  - Apache Iceberg 1.12 문서(2026-10-07 기준 최신 릴리스 1.12.0) — Reliability, Maintenance, Configuration(`commit.retry.*`, `history.expire.*`, `write.target-file-size-bytes`, format-version 기본 2), Spark Queries(time travel·메타데이터 테이블), Spark Procedures(`expire_snapshots`·`remove_orphan_files`·`rewrite_data_files`·`rewrite_manifests`) <https://iceberg.apache.org/docs/latest/>
  - Delta Transaction Log Protocol <https://raw.githubusercontent.com/delta-io/delta/master/PROTOCOL.md> — Overview(MVCC, vacuum 명령의 기본 보존 7일 언급), Delta Log Entries, Checkpoints, Add File and Remove File(툼스톤), Creation of New Log Entries. (master 브랜치, 2026-10-07 열람)
  - Apache Hudi 문서 "Timeline" <https://hudi.apache.org/docs/timeline>, "Concurrency Control" <https://hudi.apache.org/docs/concurrency_control> (2026-10-07 열람)
- 실험 목록(2026-10-07, Java 21 모형 `eclipse-temurin:21-jdk` JDK 21.0.12, `--network none --cpus=2`, 5번 실행)
  - A: 8 작성자 × 50 append — CAS vs 검사 없는 덮어쓰기(파일·행 유실 수, CAS 실패 수).
  - B: compaction 도중 원본 파일 삭제 커밋 — 검증 O(ABORT, 500행) vs 검증 X(600행).
  - C: 스냅샷 6개 → 최근 1개만 남기고 만료 → 지운 파일 수, 옛 스냅샷 time travel 실패.
  - D: 파일 수 10~100,000 × 10일 — 매니페스트 가지치기 후 훑은 항목 수·계획 시간.
