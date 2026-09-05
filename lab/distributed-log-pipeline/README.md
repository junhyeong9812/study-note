# distributed-log-pipeline — k3s 3노드에서 PostgreSQL vs HDFS+Spark 쓰기·읽기·부하 실측

- 원본: `/home/jun/project/distributed-log-pipeline` · 기간: 2026-01-11 ~ 2026-01-14 (git 커밋 기준) · 스택: k3s v1.34.3(3노드), Kafka 3.7.0, Spark 3.3.0(PySpark 3.5.0), Hadoop 3.2.1, PostgreSQL 15, Spring Boot(수집)·FastAPI(조회), k6, Prometheus+Grafana
- 상태: **완료** (쓰기 Phase 1~2·1.2억건 적재·Compaction·부하 Phase 6~7까지 측정. 10억건 적재 중 디스크 임계로 클러스터 다운 — 그 자체가 결론의 일부)

## 무엇을 알고 싶었나 — 질문·가설

- 핵심 질문: **"대용량 로그 데이터 처리에서 분산 시스템(HDFS+Spark)이 단일 DB(PostgreSQL)보다 효율적인가?"**
- 가설: 소량에서는 PostgreSQL이 빠르지만, 대용량에서는 Spark/HDFS가 우세할 것 (소량=PostgreSQL 압승 / 10만~100만 교차 / 100만+ Spark 우세 예상).
- 부수 질문: 쓰기 파이프라인(Kafka→Spark Streaming→HDFS)은 어디까지 버티는가, 동시 사용자 부하는 얼마나 받는가.

## 실험 환경과 방법

| 노드 | CPU / RAM | 역할 |
|------|-----------|------|
| Master (192.168.55.114) | 8코어 / 16GB | K8s Master, PostgreSQL, Kafka, NameNode, Spark Master |
| Worker 1 (192.168.55.158) | 6코어 / 16GB | DataNode, Spark Worker, k6 |
| Worker 2 (192.168.55.9) | 8코어 / 16GB | DataNode, Spark Worker |

데이터 흐름: `Generator(Python) → Backend(Spring Boot) → Kafka → Spark Streaming → HDFS(Parquet)`, Backend가 PostgreSQL에도 동시 적재. 조회는 FastAPI Query API(내장 PySpark)로 양쪽 비교.

## 결과 1 — 쓰기 성능

### Phase 1 (JPA 단건 INSERT): 목표 90만건/분의 22%에서 병목

| Phase | 목표 | 실제 | 결과 |
|-------|------|------|------|
| 1 (기본) | 9,000건/분 | 9,000건/분 | 둘 다 안정 |
| 2 (중간) | 90,000건/분 | 90,000건/분 | 둘 다 안정 |
| 3 (고부하) | 900,000건/분 | ~200,000건/분 | Backend 병목 (달성률 22%) |

출처: `/home/jun/project/distributed-log-pipeline/docs/BENCHMARK_WRITE_RESULT.md`

병목은 저장소가 아니라 **Backend** — JPA `saveAll()`이 IDENTITY 전략 때문에 단건 INSERT 반복(5,000건 = 5,000회 왕복)으로 동작.

### Phase 2 (JDBC Batch 전환): 9배 향상, HDFS 한계 발견

| 부하 | PostgreSQL | HDFS/Spark |
|------|------------|------------|
| 90만건/분 | 안정 | 안정 |
| 180만건/분 | 안정 (쿼리 345ms) | 안정 (쿼리 3,665ms) |
| 360만건/분 | **계속 동작** (514만건 저장) | **사망** (DataNode excluded) |

출처: `/home/jun/project/distributed-log-pipeline/docs/BENCHMARK_WRITE_PHASE2.md` (§Phase 2 테스트 결과)

최대 처리량 **20만건/분 → 180만건/분+ (9배)**. HDFS는 DataNode가 쓰기 속도를 못 따라가 excluded 처리 → Spark Streaming 사망.

## 결과 2 — 읽기 성능 (데이터 규모별)

### ~2만건: PostgreSQL 최대 354배

| 쿼리 | PostgreSQL | HDFS/Spark | 배수 |
|------|------------|------------|------|
| COUNT | 13.67ms | 1,851.70ms | 135x |
| 조건 조회 (level=ERROR) | 16.68ms | 5,899.03ms | 354x |
| GROUP BY level | 8.84ms | 2,313.51ms | 262x |

출처: `/home/jun/project/distributed-log-pipeline/docs/BENCHMARK_readPerformance.md`

### ~557만건: PostgreSQL 10~90배, 단 안정성은 HDFS

| 쿼리 | PostgreSQL | HDFS | 배수 |
|------|------------|------|------|
| COUNT(*) | 376ms | 4,396ms | 11.7x |
| GROUP BY | 584ms | 8,410ms | 14.4x |
| ORDER BY | 229ms | 20,969ms | 91.5x |

출처: `/home/jun/project/distributed-log-pipeline/docs/BENCHMARK_WRITE_PHASE3_RESULT.md`

동시 부하에서 PostgreSQL은 timeout 발생·편차 큼, HDFS는 느리지만 timeout 없이 일정 — "500만건은 대용량이 아님"이 원본 결론.

### 1.2억건 (Compaction 전, Parquet 30,803개): PostgreSQL 12~17배

| 쿼리 | PostgreSQL | HDFS+Spark | 배수 |
|------|-----------|------------|------|
| COUNT(*) | 6.7초 | 112초 | PostgreSQL 17x |
| GROUP BY service | 15.6초 | 245초 | PostgreSQL 16x |
| WHERE + GROUP BY | 20.5초 | 236초 | PostgreSQL 12x |

출처: `/home/jun/project/distributed-log-pipeline/docs/BENCHMARK_WRITE_PHASE4_RESULT.md`

원인 진단: **Small File Problem** — Streaming이 60초 배치마다 파일을 만들어 30,803개의 소형 파일(파일당 ~200KB, 권장 100MB~1GB) → 파일당 Task 1개 = 30,000+ Task.

## 결과 3 — Parquet Compaction (30,803개 → 100개)

| 항목 | Before | After |
|------|--------|-------|
| 파일 수 | 30,803개 | 100개 (99.7% 감소) |
| 파일당 크기 | ~200KB | ~58MB |
| 레코드 수 | 121,619,878 | 121,619,878 (무결성 확인) |

| 쿼리 | HDFS Before | HDFS After | 개선 | vs PostgreSQL |
|------|-------------|------------|------|---------------|
| COUNT(*) | 112초 | 12초 | 9.4x | PostgreSQL 승 (6.7초, 1.8x) |
| GROUP BY service | 245초 | 12초 | 20.3x | **HDFS 승 (1.3x)** |
| WHERE + GROUP BY | 236초 | 8.6초 | **27.4x** | **HDFS 승 (2.4x)** |

출처: `/home/jun/project/distributed-log-pipeline/docs/BENCHMARK_WRITE_PHASE5_RESULT.md`

Compaction 하나로 HDFS가 조건부 집계에서 PostgreSQL을 역전 — **HDFS 최대 병목은 Small File Problem**.

## 결과 4 — k6 부하 테스트 (1.2억건 위에서)

### Phase 6 (과부하): 전부 FAIL

| 테스트 | VU | 에러율 | 결과 |
|--------|-----|--------|------|
| PG 단순 조회 | 50 | 45.88% | FAIL |
| PG 집계 | 20 | 62.96% | FAIL |
| HDFS 단순 조회 | 10 | 완료 0건 | FAIL |

출처: `/home/jun/project/distributed-log-pipeline/docs/BENCHMARK_WRITE_PHASE6_RESULT.md`

### Phase 7 (리소스 기반 적정 VU 재계산): 전부 PASS

| 테스트 | VU | 에러율 | 평균 응답 |
|--------|-----|--------|-----------|
| PG 단순 조회 | 5 | 0% | 4,186ms |
| PG 집계 | 3 | 0% | 18,785ms |
| HDFS 집계 | 2 | 0% | **7,966ms** |
| HDFS 로그 조회 (ORDER BY+LIMIT) | 2 | 0% | 156,830ms (2분 37초) |

출처: `/home/jun/project/distributed-log-pipeline/docs/BENCHMARK_WRITE_PHASE7_RESULT.md`

집계는 HDFS가 2.4배 빠르고(7.9초 vs 18.8초), 정렬 조회는 PostgreSQL이 37배 빠름(4.2초 vs 157초) — 1.2억건 전체 정렬은 분산해도 최종 병합이 단일 노드라 분산처리가 오히려 불리.

### 번외 — 10억건 적재 시도: 디스크 임계로 클러스터 다운

PostgreSQL PVC가 326GB까지 차오르며 노드 DiskPressure → Spark Master 등 Pod 대량 Evicted. 원본 결론: 수억건 로그 = 수백GB, 단일 노드 디스크는 유한하므로 분산 저장이 필요하고, HDD 환경(순차 스캔·Columnar)에 강한 HDFS+Spark가 로그(통계성 워크로드)에 적합. (출처: `README.md` "분산 시스템을 써야되는 이유" — 총 10억건 수집 완료 스크린샷 포함)

## 종합 결론

- **분산처리 ≠ 만능**: 단순 조회·정렬+LIMIT은 PostgreSQL 압승(부하 테스트 기준 37배) — 인덱스·단일노드 정렬의 힘.
- **집계는 분산이 이긴다**: Compaction 후 GROUP BY 계열에서 HDFS+Spark가 1.3~2.4배 우위 — 부분 집계 후 병합이라 데이터가 줄어드는 연산.
- **Small File Problem이 HDFS 성능의 제1병목**: 파일 30,803→100개로 최대 27.4배 개선. Streaming 적재에는 정기 Compaction 필수.
- **병목은 저장소보다 앞단에서 먼저 온다**: JPA IDENTITY 단건 INSERT가 원인 — JDBC Batch로 9배(20만→180만건/분). 극한 쓰기(360만건/분)에선 오히려 HDFS가 먼저 죽고 PostgreSQL이 버팀.
- **디스크는 유한하다**: 10억건 적재에서 물리적 한계(용량·비용)가 아키텍처 선택(분산 저장 + HDD + Columnar)의 실질 근거임을 체감.

## 한계·남은 질문

- HDFS의 쓰기 안정성 가설은 완전 검증 안 됨 — 360만건/분에서 오히려 HDFS가 먼저 사망 (worker 2대·리소스 제한 환경의 결과일 수 있음).
- Phase 7에서 Spark Worker가 거의 미사용 — Query API의 PySpark가 local[*] 모드로 동작해 진짜 분산 조회가 아님(원본이 스스로 지적).
- Delta Lake/Iceberg 인덱싱, 파티션 프루닝, Elasticsearch 하이브리드는 계획으로만 남음.
- `docs/BENCHMARK_WRITE_PHASE3.md`는 **0바이트 빈 파일** — Phase 3(리소스 확장) 설계 문서 부재. 결과는 `BENCHMARK_WRITE_PHASE3_RESULT.md`(내용은 500만건 읽기 벤치마크)에 있음.
- 루트 README "성능 개선 히스토리"의 `20,000건/분 → 180,000건/분`은 Phase 2 문서의 실측(`20만건/분 → 180만건/분`)과 단위가 어긋남 — 정본은 `BENCHMARK_WRITE_PHASE2.md`.

## 원본 문서 지도

| 문서 | 내용 |
|------|------|
| `README.md` (26KB) | 종합 보고서 — 전체 결과 요약, 10억건 장애 기록, 아키텍처 |
| `docs/ARCHITECTURE.md` (22KB) | 시스템 아키텍처 상세 (**정본** — 루트 ARCHITECTURE.md 7.6KB보다 상세) |
| `docs/WHY_HDFS_SPARK.md` (50KB) | PostgreSQL 분산 옵션 한계·HDFS 선택 이유·I/O 패턴 이론 |
| `docs/BENCHMARK_WRITE_PERFORMANCE.md` / `_RESULT.md` | 쓰기 Phase 1~3 설계·결과 (JPA 병목 발견) |
| `docs/BENCHMARK_WRITE_PHASE2.md` | JDBC Batch 원리(IDENTITY 함정)+Phase 2 실측 (9배·HDFS 사망) |
| `docs/BENCHMARK_WRITE_PHASE3.md` | ⚠️ 0바이트 빈 파일 |
| `docs/BENCHMARK_WRITE_PHASE3_RESULT.md` | 500만건 규모 읽기 벤치마크 |
| `docs/BENCHMARK_WRITE_PHASE4.md` / `_RESULT.md` | 1.2억건 적재·조회 + Small File Problem 발견 |
| `docs/BENCHMARK_WRITE_PHASE5.md` / `_RESULT.md` | Parquet Compaction 실행·재측정 (27.4x) |
| `docs/BENCHMARK_WRITE_PHASE6.md` / `_RESULT.md` | k6 과부하 실패 분석 |
| `docs/BENCHMARK_WRITE_PHASE7.md` / `_RESULT.md` | 적정 VU 계산·재테스트 성공 |
| `docs/BENCHMARK_readPerformance.md` | 최초 소량(2만건) 읽기 비교 (354x) |
| `docs/HDFS_COMPACTION.md` | Compaction 원리·coalesce vs repartition·자동화 가이드 |
| `docs/HDDvsSSD.md` | HDD 순차 I/O vs Random I/O, Columnar가 로그 통계에 강한 이유 |
| `docs/TROUBLESHOOTING*.md` | DataNode excluded, Spark Streaming 이슈 등 |
| `docs/SETUP_MASTER.md` / `SETUP_WORKER.md` / `HDFS_SETTING.md` | 클러스터 구축 가이드 |
