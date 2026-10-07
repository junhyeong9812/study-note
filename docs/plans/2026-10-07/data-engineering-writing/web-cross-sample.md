# 웹 독립 교차 표본 — 데이터 공학 17편

- 일시: 2026-10-07
- 대상: `cs/data-engineering/01`~`17`의 `2-summary.md`. 사실 점검·판정·정합이 끝난 현재 본문 기준이며 노트는 수정하지 않았다.
- 방법: 편마다 URL이나 1차 출처가 붙은 주장을 2~4개 골랐다. log와 사실 점검 브리핑에 나온 기존 웹 표본(DDIA 목차, CIDR 1절 인용, Kimball grain·additive·conformed·drill-across·late-arriving·Type 0~7·DT#152, EXCLUDE·tstzrange, Debezium 'Possible duplicates', binlog 30일, Kreps HDFS 인용, Confluent 호환성 표·defaultToGlobal, dbt severity, GX, GDPR 조문, EDPB 02/2025, hashdiff 정의, Delta vacuum 7일, Iceberg operation, ODPS apiVersion, PHE 날짜 축, Unity 두 문제, Equifax 날짜·test code)은 피해서 다른 문장을 골랐다. 출처는 curl로 받았다(GET만, 일반 브라우저 UA). HTML은 텍스트로 추출했고 소스는 raw.githubusercontent.com에서 받았다(PostgreSQL `REL_17_STABLE`, Kafka `4.1`, CloudEvents `v1.0.2`, dbt-adapters `main`, Delta `master`). 원 페이지가 403이면 Internet Archive 사본을 열었다(Medium, SEC EDGAR).
- 결과: **59건** — 일치 58 · 불일치 1(출처 귀속, 경미) · 확인 불가 0.
- 비고: 불일치 1건은 사실 오류가 아니다. 주장(뷰 규칙 이름 `_RETURN`)은 맞지만, 붙인 링크(`pg_rewrite` 카탈로그 페이지)에는 그 문장이 없다. 관찰 1건(Micrometer 게이지 재등록 표현)은 일치로 판정했다.

| # | 노트 (:줄) | 주장 | 출처 | 원문 인용 | 판정 |
|---|---|---|---|---|---|
| 1 | 01 :105 | `A EXCEPT B`는 A에만 있는 행만 보인다 | PG 17 문서 7.4 queries-union | "EXCEPT returns all rows that are in the result of query1 but not in the result of query2." | 일치 |
| 2 | 01 :106 | `EXCEPT`는 중복 행을 없앤다. `EXCEPT ALL`로 중복 유지 | PG 17 문서 7.4 | "Again, duplicates are eliminated unless EXCEPT ALL is used." | 일치 |
| 3 | 02 :212 | `max_standby_streaming_delay` 기본 30초까지 기다린 뒤 조회 취소 | PG 17 문서 19.6 runtime-config-replication | "how long the standby server should wait before canceling standby queries that conflict … The default is 30 seconds." | 일치 |
| 4 | 02 :89 | 공유 버퍼 128MB(기본) | PG 17 문서 19.4 runtime-config-resource | "The default is typically 128 megabytes (128MB)" | 일치 |
| 5 | 02 :79 | `pgbench -l` 트랜잭션 로그로 분위수 계산 | PG 17 pgbench 문서 | "-l --log Write information about each transaction to a log file." | 일치 |
| 6 | 03 :64 | Kimball은 헤더 팩트를 상세 줄에 배분하는 쪽을 우선 권하고, 헤더 수준 팩트 테이블은 성능 이점이 있을 때만 | Kimball "Allocated Facts" | "You should strive to allocate the header facts down to the line level … you can avoid creating a header-level fact table, unless this aggregation delivers query performance advantages." | 일치 |
| 7 | 03 :134 | 팩트 외래 키에 NULL을 두지 않고 차원의 unknown/not applicable 기본 행·대리 키를 가리킨다 | Kimball "Nulls in Fact Tables" | "nulls must be avoided in the fact table's foreign keys … the associated dimension table must have a default row (and surrogate key) representing the unknown or not applicable condition." | 일치 |
| 8 | 03 :135 | 차원 속성 NULL은 "Unknown" 같은 문자열로. DB마다 그룹·필터 처리가 달라서 | Kimball "Null Attributes in Dimensions" | "substituting a descriptive string, such as Unknown or Not Applicable … different databases handle grouping and constraining on nulls inconsistently." | 일치 |
| 9 | 04 :76 | 퇴사 후 재입사로 사번(자연 키)이 바뀌어도 같은 내구 키 | Kimball "Natural, Durable, and Supernatural Keys" | "an employee number (natural key) may be changed if the employee resigns and then is rehired … a new durable key must be created that is persistent and does not change" | 일치 |
| 10 | 04 :101 | 부분 유일 인덱스는 술어를 만족하는 행 사이의 유일성만 건다(PG 17 문서 11.8) | PG 17 문서 11.8 indexes-partial | "This enforces uniqueness among the rows that satisfy the index predicate, without constraining those that do not." | 일치 |
| 11 | 04 :133 | 자연 키가 바뀌는 원천은 옛 키·새 키를 같은 내구 키로 잇는 매핑을 둔다(Design Tip #147) | Kimball Design Tip #147 "Durable 'Super-Natural' Keys"(2012-07) | "a table with the old account number, the new account number, and the effective date. The ETL system must then create a new row … and a separate durable key column that ties the old and new accounts together." | 일치 |
| 12 | 05 :52 | 슬롯은 소비자 상태를 모른다(원문 인용) | PG 17 문서 47.2.2 logicaldecoding-explanation | "A logical replication slot knows nothing about the state of the receiver(s)." | 일치 |
| 13 | 05 :154 | `incremental.snapshot.chunk.size` 기본 1,024 | Debezium 블로그 2021-10-07 · PG 커넥터 문서(stable) | 블로그 "The default chunk size is 1,024." · 커넥터 속성표 `incremental.snapshot.chunk.size` / `1024` | 일치 |
| 14 | 05 :177 | `tombstones.on.delete` 기본 true면 delete 뒤 tombstone 하나 더 | Debezium PG 커넥터 문서(stable) | `tombstones.on.delete` / `true` / "Controls whether a delete event is followed by a tombstone event." | 일치 |
| 15 | 05 :334 | `op` 값 c·u·d·r·t·m | Debezium PG 커넥터 문서(stable) | "Valid values are: c create, u update, d delete, r read (applies to only snapshots), t truncate, m message" | 일치 |
| 16 | 06 :42 | CloudEvents `time` = 발생 시각. 모르면 다른 시각(현재 시각 등) 허용 | CloudEvents spec v1.0.2 `time` | "Timestamp of when the occurrence happened. If the time of the occurrence cannot be determined then this attribute MAY be set to some other time (such as the current time) by the CloudEvents producer" | 일치 |
| 17 | 06 :144 | `message.timestamp.after.max.ms` 기본 3600000, CreateTime이면 초과 레코드 거부. `before.max.ms` 기본 사실상 무제한 | Kafka 4.1 Topic Configs | "If message.timestamp.type=CreateTime, the message will be rejected if the difference in timestamps exceeds this specified threshold." Default 3600000 (1 hour) · before.max.ms Default 9223372036854775807 | 일치 |
| 18 | 06 :295 | CloudEvents는 `source` + `id` 유일성을 생산자에게 요구 | CloudEvents spec v1.0.2 `id` | "Producers MUST ensure that `source` + `id` is unique for each distinct event." | 일치 |
| 19 | 07 :15 | Kreps 2014: "Code will always change." | Kreps, O'Reilly Radar(2014-07-02) | "This is a completely obvious but often ignored requirement. Code will always change." | 일치 |
| 20 | 07 :65 | Kappa 1단계 인용(30일 재처리 → 보존 30일) | Kreps 2014 | "For example, if you want to reprocess up to 30 days of data, set your retention in Kafka to 30 days." | 일치 |
| 21 | 07 :96 | `retention.ms` 기본 604800000(7일), 보존은 "an SLA on how soon consumers must read their data" | Kafka 4.1 Topic Configs | "This represents an SLA on how soon consumers must read their data." Default 604800000 (7 days) | 일치 |
| 22 | 07 :135 | `local.retention.ms`·`local.retention.bytes` 기본 -2 = `retention.*`를 따름 | Kafka 4.1 Topic Configs | "Default value is -2, it represents `retention.ms` value is to be used." (bytes 동일) | 일치 |
| 23 | 08 :43 | 순수 태스크는 결정적·멱등, 같은 입력이면 이전 출력을 덮어쓴다("forcing an overwrite approach") | Beauchemin, Medium 2018-01-08(IA 2024 사본) | "A pure task should be deterministic and idempotent … This requires forcing an overwrite approach, meaning re-executing a pure task with the same input parameters should overwrite any previous output" | 일치 |
| 24 | 08 :46 | 원본은 "persistent and immutable staging area"에, 웨어하우스 전체를 처음부터 재계산 가능 | Beauchemin(IA) | "Given a persistent immutable staging area and pure tasks, in theory it's possible to recompute the state of the entire warehouse from scratch" | 일치 |
| 25 | 08 :106 | past dependencies: 3년치 일별 스냅샷이면 그래프 깊이 천 이상, 몇 달 전을 고치면 수백 파티션을 병렬 없이 | Beauchemin(IA) | "the table has 3 years of history with daily snapshot, the depth of the resulting graph grows beyond a thousand … we may need to reprocess hundreds of partition using a DAG that cannot be parallelized." | 일치 |
| 26 | 08 :76 | PG 기본 격리 READ COMMITTED. 두 번째 DELETE는 먼저 커밋된 변경을 기다렸다 지워진 행을 건너뜀 | PG 17 문서 13.2.1 transaction-iso | "Read Committed is the default isolation level in PostgreSQL." · "they will only find target rows that were committed as of the command start time … the would-be updater will wait for the first updating transaction … If the first updater commits, the second updater will ignore the row if the first updater deleted it" | 일치 |
| 27 | 09 :49 | ODCS SLA 속성 `latency`·`frequency`·`retention`·`timeOfAvailability` | Bitol ODCS latest "Service-Level Agreement" | 예제 `property: latency` · `property: retention` · `property: frequency` · `property: timeOfAvailability` | 일치 |
| 28 | 09 :95 | Confluent Platform 8.1.1부터 16바이트 GUID를 헤더에 싣는 형식 선택 가능 | Confluent "Formats, Serializers, and Deserializers" | "As of Confluent Platform 8.1.1, you can change the wire format to not emit the schema ID in the payload prefix … the metadata for the schema be placed in the message header … 16-byte schema GUID instead of the 4-byte schema ID." | 일치 |
| 29 | 09 :186 | Avro aliases는 구현이 "may optionally" 쓴다 | Avro 1.12.0 Specification(Aliases) | "An implementation may optionally use aliases to map a writer's schema to the reader's." | 일치 |
| 30 | 10 :39 | Barr Moses가 2019년에 "data observability"라는 말을 만들었다고 적음 | Monte Carlo 블로그(현재판) | "I coined the term data observability in 2019." | 일치 |
| 31 | 10 :59 | dbt `unique`는 `IS NOT NULL`로 NULL을 빼고 센다 | dbt-adapters `generic_test_sql/unique.sql`(main) | `where {{ column_name }} is not null group by {{ column_name }} having count(*) > 1` | 일치 |
| 32 | 10 :77 | 테스트 실패 시 `dbt build`는 하류를 SKIP할 뿐 | dbt `build` 문서 | "a test failure will cause those downstream resources to skip entirely. E.g. If model_b depends on model_a, and a unique test on model_a fails, then model_b will SKIP." | 일치 |
| 33 | 10 :232 | Micrometer: 같은 이름·태그 게이지 재등록 → 기존 것 유지, 첫 값에 고정. 관측 대상은 약한 참조 | Micrometer "Gauges" | "the registry maintains only one meter for each unique combination of name and tags" · "WARNING: This Gauge has been already registered … the registration will be ignored." · "maintain only a weak reference to the object being observed" | 일치(관찰 — 아래) |
| 34 | 11 :42 | Run 상태 6종, 끝 상태 COMPLETE·ABORT·FAIL | OpenLineage "The Run Cycle" | "START … RUNNING … COMPLETE … ABORT … FAIL … OTHER" · "COMPLETE, ABORT and FAIL are terminal events." | 일치 |
| 35 | 11 :69~72 | columnLineage 분류 DIRECT(IDENTITY·TRANSFORMATION·AGGREGATION), INDIRECT(JOIN·FILTER·GROUP_BY·SORT·WINDOW·CONDITIONAL), `masking` 불리언 | OpenLineage "Column Level Lineage Dataset Facet" | "Direct: IDENTITY … TRANSFORMATION … AGGREGATION · Indirect: JOIN … GROUP_BY … FILTER … SORT … WINDOW … CONDITIONAL - input value is used in IF, CASE WHEN or COALESCE" · "Masking: Boolean value indicating if the input value was obfuscated" | 일치 |
| 36 | 11 :57 | 출력 facet 묶음 `outputFacets`, `outputStatistics.rowCount` | OpenLineage "Output Statistics" facet | `"outputFacets": { "outputStatistics": { … "rowCount": 123,` | 일치 |
| 37 | 11 :280 | `pg_rewrite` 문서 링크에 "뷰 정의 규칙 `_RETURN`"을 근거로 붙임 | PG 17 문서 51.44 catalog-pg-rewrite · 39.2 rules-views | pg_rewrite 페이지: "The catalog pg_rewrite stores rewrite rules for tables and views." (`_RETURN` 언급 없음) · 39.2: "Conventionally, that rule is named _RETURN." | **불일치(출처 귀속)** |
| 38 | 12 :107~108 | `delete.retention.ms`(기본 24시간) 안에 끝까지 읽어야 삭제 표시를 본다 | Kafka 4.1 `docs/design/design.md` | "all delete markers for deleted records will be seen, provided the consumer reaches the head of the log in a time period less than the topic's `delete.retention.ms` setting (the default is 24 hours)." | 일치 |
| 39 | 12 :109 | active segment는 compaction 대상 아님, `max.compaction.lag.ms`는 엄격한 보장 아님 | Kafka 4.1 design.md | "The active segment will not be compacted even if all of its messages are older than the minimum compaction time lag." · "this compaction deadline is not a hard guarantee" | 일치 |
| 40 | 12 :111 | `deleteRecords`는 주어진 오프셋보다 작은 레코드를 지운다 | Kafka 4.1 `Admin.java` | "Delete records whose offset is smaller than the given offset of the corresponding partition." | 일치 |
| 41 | 12 :306~307 | Dudycz 글(2023-11-26)의 "For GDPR, it's 30 days" | event-driven.io | "For GDPR, it's 30 days." · `article:published_time` 2023-11-26 | 일치 |
| 42 | 13 :17 | Linstedt가 2000년에 공개(Wikipedia, 2차) | Wikipedia "Data vault modeling" | "originally conceived by Dan Linstedt in the 1990s and was released in 2000 as a public domain modeling method." | 일치 |
| 43 | 13 :105 | AutomateDV: `EFFECTIVE_FROM`은 선택 컬럼, DV 2.0 표준 밖 | AutomateDV "Satellites" 튜토리얼 | "The EFFECTIVE_FROM field is not part of the Data Vault 2.0 standard, and as such it is an optional field" | 일치 |
| 44 | 13 :195 | AutomateDV는 hashdiff 컬럼을 알파벳순으로 정렬 | AutomateDV "Hashing" | "If you provide the is_hashdiff: true flag … AutomateDV will automatically sort the provided columns alphabetically. Columns will be sorted by their alias." | 일치 |
| 45 | 13 :184 | PG 17 기본 `join_collapse_limit = 8`, `geqo_threshold = 12` | PG 17 문서 19.7 runtime-config-query | geqo_threshold "The default is 12." · join_collapse_limit "By default, this variable is set the same as from_collapse_limit" · from_collapse_limit "The default is eight." | 일치 |
| 46 | 14 :79 | Iceberg `commit.retry.num-retries`=4, `min-wait-ms`=100, `max-wait-ms`=60000, `total-timeout-ms`=1800000 | Iceberg 1.12.0 Configuration | 표: `commit.retry.num-retries 4` · `min-wait-ms 100` · `max-wait-ms 60000 (1 min)` · `total-timeout-ms 1800000 (30 min)` | 일치 |
| 47 | 14 :262 | `write.target-file-size-bytes` 기본 512MB | Iceberg 1.12.0 Configuration | `write.target-file-size-bytes 536870912 (512 MB)` | 일치 |
| 48 | 14 :242·290 | 고아 파일 삭제 보존 간격 기본 3일 | Iceberg 1.12.0 Spark Procedures `remove_orphan_files` | "older_than … Remove orphan files created before this timestamp (Defaults to 3 days ago)" | 일치 |
| 49 | 14 :84 | Delta 프로토콜: "Delta's transactions are implemented using multi-version concurrency…" | Delta PROTOCOL.md(master) | "Delta's transactions are implemented using multi-version concurrency control (MVCC)." | 일치 |
| 50 | 15 :19 | 실패 모드 3: "의미 있고 정확한 데이터를 줄 동기가 없는 팀" | Dehghani 2019, martinfowler.com | "They need to consume data from teams who have no incentive in providing meaningful, truthful and correct data." | 일치 |
| 51 | 15 :51 | 네 원칙이 "함께 필요하고 충분하도록" 의도 | Dehghani 2020, martinfowler.com | "I have intended for the four principles to be collectively necessary and sufficient" | 일치 |
| 52 | 15 :56~64 | 데이터 제품 조건 6가지(Discoverable·Addressable·Trustworthy and truthful·Self-describing·Inter-operable·Secure) | Dehghani 2019 | "Discoverable / Addressable / Trustworthy and truthful / Self-describing semantics and syntax / Inter-operable and governed by global standards / Secure and governed by a global access control" | 일치 |
| 53 | 15 :190 | `last_seq_scan`은 16부터(15판 문서에 없음). 정상 종료 시 통계 보존, 비정상 종료 뒤 초기화 | PG 17·15 문서 monitoring-stats | 17판에 `last_seq_scan timestamp with time zone` 있음 / 15판 0회 · "When a server … shuts down cleanly, a permanent copy of the statistics data is stored … when starting from an unclean shutdown (e.g., after an immediate shutdown, a server crash, starting from a base backup…" | 일치 |
| 54 | 16 :241 | `pg_replication_slots`의 `inactive_since`, `wal_status=extended` | PG 17 문서 52.19 view-pg-replication-slots | "inactive_since timestamptz The time when the slot became inactive." · "extended means that max_wal_size is exceeded but the files are still retained, either by the replication slot or by wal_keep_size." | 일치 |
| 55 | 16 :250 | `wal_status=lost`, `invalidation_reason=wal_removed`, 서버 로그 `invalidating obsolete replication slot`, 커넥터 쪽 `can no longer get changes from replication slot` | PG 17 문서 52.19 · `REL_17_STABLE` `slot.c`·`logical.c` | "wal_removed means that the required WAL has been removed." · slot.c:1592 `errmsg("invalidating obsolete replication slot \"%s\""` · logical.c:625 `errmsg("can no longer get changes from replication slot \"%s\"" … "This slot has been invalidated because it exceeded the maximum reserved size."` | 일치 |
| 56 | 16 :253 | 상한을 넘은 슬롯은 체크포인트 때 무효화될 수 있다 | `REL_17_STABLE` `xlog.c` · 52.19 | `CreateCheckPoint()`·`CreateRestartPoint()` 안에서 `InvalidateObsoleteReplicationSlots(RS_INVAL_WAL_REMOVED, …)` 호출 · "unreserved … some of them are to be removed at the next checkpoint" | 일치 |
| 57 | 17 :62 | 발표문 "over 75% (11,968) relate to cases that should have been reported between 30 September and 2 October" | GOV.UK PHE 발표 | "Of these, over 75% (11,968) relate to cases that should have been reported between 30 September and 2 October." | 일치 |
| 58 | 17 :144 | Q1 2022 매출 $320.1M(36%↑), Operate $184.0M(26%↑), 연간 가이던스 하향, 2022년 매출 $1,350M~$1,425M | Unity 8-K Ex. 99.1(IA 사본) | "revenue of $320.1 million, which is up 36%" · "Operate Solutions revenue was $184.0 million, an increase of 26%" · "lowering guidance for the full year ending December 31, 2022" · "$1,350 — $1,425" | 일치 |
| 59 | 17 :190 | FY2024 10-K: 2025년 1월 CFPB 동의 명령으로 USIS 이의 처리·코딩 문제 조사 함께 종결, 민사 제재금 $15M, 업무 관행 변경 | Equifax 10-K FY2024(IA 사본) | "In January 2025, we entered into a consent order with the CFPB to settle the investigation into our consumer disputes process at our USIS business unit and the investigation into our previously-disclosed coding issue … civil money penalty of $15 million … agreed to modify certain business practices." | 일치 |

## 불일치 상세

### 1. 11 :280 — `_RETURN` 근거 링크가 그 문장이 없는 페이지를 가리킨다 (경미, 출처 귀속)

- 노트 문구(:280): "PostgreSQL 17 `pg_rewrite`(뷰 정의 규칙 `_RETURN`) <https://www.postgresql.org/docs/17/catalog-pg-rewrite.html>"
- 원문: `catalog-pg-rewrite` 페이지에는 "The catalog pg_rewrite stores rewrite rules for tables and views."와 컬럼 정의(`rulename name` — "Rule name")만 있고 `_RETURN`은 나오지 않는다. `_RETURN`은 39.2 "Views and the Rule System"에 있다: "A view is basically an empty table (having no actual storage) with an ON SELECT DO INSTEAD rule. Conventionally, that rule is named _RETURN."
- 본문 주장(:188·:194·:212 — 뷰 정의 규칙은 `_RETURN`, `pg_rewrite`에는 일반 테이블 규칙도 들어감)은 사실이다. 고칠 것은 근거 표기뿐이다.
- 제안 문구: "PostgreSQL 17 `pg_rewrite`(테이블·뷰의 재작성 규칙 카탈로그) <https://www.postgresql.org/docs/17/catalog-pg-rewrite.html> · 39.2 Views and the Rule System(뷰 = `ON SELECT DO INSTEAD` 규칙, 관례상 이름 `_RETURN`) <https://www.postgresql.org/docs/17/rules-views.html>"

## 확인 불가·관찰 상세

- 확인 불가: 0건.
- 관찰(10 :232, 일치로 판정): 노트는 "같은 이름·태그의 게이지를 다시 등록하면 기존 것을 돌려준다"고 적는다. Micrometer 문서는 "the registry maintains only one meter for each unique combination of name and tags"이고, 다시 등록하면 경고("This Gauge has been already registered … the registration will be ignored")를 남긴다고 적는다. "기존 것을 돌려준다"는 반환값을 말하는 문서 문장은 이 페이지에 없다. 결론(새 람다는 반영되지 않고 처음 등록한 관측 대상이 유지된다)은 같다. 원하면 "다시 등록하면 경고만 남기고 무시된다(레지스트리는 이름·태그 조합마다 미터 하나)"로 바꿀 수 있다.
- 관찰(02 :89, 일치): 문서는 `shared_buffers` 기본값을 "typically 128MB"(커널 설정에 따라 더 작을 수 있음)라고 적는다. 실험 컨테이너 값으로는 문제없다.
- 관찰(13 :184, 일치): 문서상 `join_collapse_limit`의 기본은 숫자가 아니라 "`from_collapse_limit`과 같게"이고, `from_collapse_limit`의 기본이 8이다. 노트는 `SHOW` 실행 결과를 적었으므로 맞다.
- 원 주소 403 → Internet Archive 사본으로 읽은 것: Beauchemin Medium 글(IA 2024), Unity 8-K Ex. 99.1(IA 2024), Equifax 10-K FY2024(IA 2025). SEC EDGAR 직접 요청은 403이었다(연락처가 든 User-Agent를 요구한다). 요청에 개인 식별 정보를 넣지 않으려고 IA 사본을 썼다.

## 실제 읽은 출처 (scratchpad `de/web/src/`)

- PostgreSQL 17 문서: queries-union, runtime-config-replication, runtime-config-resource, pgbench, indexes-partial, logicaldecoding-explanation, transaction-iso, catalog-pg-rewrite, rules-views, runtime-config-query, monitoring-stats(17·15), view-pg-replication-slots, hot-standby. 소스 `REL_17_STABLE`: `slot.c`, `logical.c`, `xlog.c`
- Kimball: Allocated Facts, Nulls in Fact Tables, Null Attributes in Dimensions, Natural/Durable/Supernatural Keys, Design Tip #147
- Debezium PostgreSQL connector(stable), Debezium 블로그 2021-10-07
- CloudEvents spec v1.0.2(raw)
- Kafka 4.1: Topic Configs 페이지, `TopicConfig.java`, `LogConfig.java`, `docs/design/design.md`, `Admin.java`
- Kreps 2014(O'Reilly Radar), Beauchemin 2018(IA)
- Avro 1.12.0 명세, Confluent serdes 문서, ODCS SLA 페이지
- Monte Carlo 블로그, dbt-adapters `unique.sql`, Micrometer Gauges, dbt build
- OpenLineage Run Cycle, Column Lineage facet, Output Statistics facet
- event-driven.io(Dudycz)
- AutomateDV Satellites·Hashing, Wikipedia Data vault modeling
- Iceberg 1.12.0 Configuration·Spark Procedures·Table Spec, Delta PROTOCOL.md
- martinfowler.com Dehghani 2019·2020
- GOV.UK PHE 발표, Unity 8-K Ex. 99.1(IA), Equifax 10-K FY2024(IA)

## 실패한 출처

- 열지 못해 판정을 못 한 출처는 없다.
- 직접 요청이 403이었던 것: `maximebeauchemin.medium.com`, `www.sec.gov`(Unity 8-K, Equifax 10-K) → 모두 Internet Archive 사본으로 대체했다.
