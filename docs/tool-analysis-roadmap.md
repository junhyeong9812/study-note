# 도구 동작 구조 분석 로드맵

이 문서는 인프라·데이터 도구의 동작 구조를 소스 기준으로 정리하기 위한 전체 후보 목록이다. 도구마다 `opensource/elasticsearch/architecture/`와 같은 모양(기준 커밋 고정, 구조 + 흐름 + API 역인덱스)으로 정리하고, 도구끼리 묶이는 자리는 개념 교차표와 E2E 시나리오라는 별도 층에서 다룬다. 목록은 2026-09-24 대화에서 추출했고, 진행하면서 상태 칸을 갱신한다.

## 1. 진행 순서

첫 묶음은 PostgreSQL(+pgvector), Redis, Nginx, Keycloak 넷이다. 앞의 셋은 C로 쓰였고 코드가 읽기 좋은 편이며, 저장 엔진·이벤트 루프·프록시라는 서로 다른 축을 하나씩 맡는다. Keycloak은 로컬 클론(26.6.2)과 공식 가이드 한국어 완역(`keycloak-analyze`)이 이미 있어 바로 소스 대조를 시작할 수 있다.

| 순서 | 도구 | 상태 |
|---|---|---|
| 0 | Elasticsearch | 완료 - 구조 6편 + 흐름 10편, 85문서 |
| 1 | PostgreSQL (+pgvector) | 폴더 구조화 - 기준 태그 REL_18_6, db-engine 대조편 |
| 1 | MySQL (InnoDB) | 폴더 구조화 - 기준 태그 mysql-9.7.2, db-engine 대조편 |
| 1 | Redis | 폴더 구조화 |
| 1 | Nginx | 폴더 구조화 |
| 1 | Keycloak | 폴더 구조화 - 기준 태그 26.6.2 |
| 2 | Kafka | `cs/systems/kafka-*` 이관과 함께 |
| 3 | Debezium | DB와 메시징을 잇는 첫 연결 사례 |
| 4 | Kubernetes + etcd | 제어 루프와 Raft |
| 5 | 이후 | 아래 목록에서 E2E 시나리오 경로에 걸리는 것부터 |

## 2. 정리 방식

도구마다 같은 틀을 쓴다. 문서 수가 ES처럼 불어나지 않도록 흐름은 도구당 5~7개로 제한하고, 개념 교차표의 칸을 채우는 흐름부터 고른다.

```text
opensource/<tool>/
  README.md        이 도구를 왜 보는가, 기준 커밋, 읽는 순서
  index.md         갈래 목록
  architecture/
    README.md      탑다운 지도 (구조 N편, 흐름 N편)
    api-index.md   API/명령/설정 이름 -> 흐름 문서 역인덱스
    structure/     무엇이 있는가 (자리)
    flows/         무엇이 일어나는가 (요청 하나의 길, 폴더 하나 = 메서드 하나)
  concepts/        개념 문서
```

공식 문서(영문)는 **지도로 쓰고, 주장은 소스로 확인한다.** 공식 문서의 설명을 그대로 옮기지 않고, 흐름을 고르는 출발점과 용어의 기준으로 삼는다. 인용할 때는 출처 링크를 단다.

## 3. 개념 교차표 (도구를 묶는 축)

같은 원리를 서로 다르게 구현한 자리를 한 행에 모은다. 각 칸은 채워지면 해당 흐름 문서로 링크한다.

| 축 | 비교 대상 |
|---|---|
| 저장 엔진 | B-Tree(InnoDB, PostgreSQL, SQLite, WiredTiger) / LSM(RocksDB, Cassandra) / 불변 세그먼트(Lucene, Kafka 로그) |
| 로그와 내구성 | redo/undo, WAL, AOF, translog, commit log, oplog |
| 복제 | 리더-팔로워, ISR, quorum, 동기/비동기 |
| 합의와 멤버십 | Raft(etcd, KRaft, Consul 서버), ZAB(ZooKeeper), gossip(Cassandra, Consul 에이전트) |
| 요청 처리 모델 | 이벤트 루프(Redis, Nginx, Netty) / 스레드풀(Java 계열) / goroutine(Go 계열) / 프로세스(PostgreSQL) |
| 제어 루프 | reconcile(Kubernetes, Argo CD, ES 샤드 할당, Terraform plan) |
| 색인 | 역색인(Lucene) / 라벨 색인(Loki) / 벡터 색인(pgvector HNSW·IVFFlat) |

## 4. E2E 시나리오 (도구가 시스템에서 묶이는 경로)

시나리오 문서는 구간마다 도구별 흐름 문서를 가리킨다. 도메인은 jun-bank를 쓴다.

| 시나리오 | 경로 |
|---|---|
| 요청 경로 | Nginx -> Spring Cloud Gateway -> Netty -> HikariCP -> MySQL/PostgreSQL |
| 로그 경로 | Beats -> Logstash -> Elasticsearch -> Kibana |
| 데이터 전파 경로 | MySQL -> Debezium -> Kafka -> Elasticsearch / Redis |
| 장애 대응 경로 | Resilience4j -> Actuator -> Kubernetes probe |

## 5. 전체 후보 목록

우선 칸의 "우선"은 먼저 볼 가치가 큰 것이다. 기준은 이미 정한 도구와 같은 원리를 다르게 구현했는가, Java/Spring 쪽과 가까운가, 레포 규모가 감당할 만한가 셋이다.

### 5.1 처음 정한 도구

| 도구 | 언어 | 우선 | 핵심 볼거리 |
|---|---|---|---|
| Elasticsearch | Java | 완료 | 샤드, 색인·검색 페이즈, 클러스터 상태 |
| MySQL | C++ | 우선 | InnoDB만 떼어 본다. redo/undo, MVCC read view, buffer pool, binlog와 2PC |
| PostgreSQL | C | 우선 | heap + WAL, MVCC(xmin/xmax), vacuum, 플래너, 프로세스 모델 |
| Oracle | 비공개 | - | 소스가 없어 소스 기준 정리 불가. 공식 Concepts 문서 기준 비교 절로 MySQL·PostgreSQL 문서 안에 흡수 |
| Redis | C | 우선 | 단일 스레드 이벤트 루프, RDB/AOF, 복제, Cluster 슬롯 |
| RabbitMQ | Erlang | | Kafka 대비 용도로 범위 축소. push vs pull, 큐 vs 로그 |
| Kafka | Java/Scala | 우선 | 로그 세그먼트, ISR, KRaft, 컨슈머 그룹 리밸런스 |

### 5.2 운영·연결 도구

| 도구 | 언어 | 우선 | 핵심 볼거리 |
|---|---|---|---|
| Kubernetes | Go | 우선 | 제어 루프, informer, 스케줄러 |
| etcd | Go | 우선 | Raft 실구현. KRaft와 비교 |
| Debezium | Java | 우선 | binlog/WAL을 Kafka로. DB와 메시징의 접착제, outbox 노트와 연결 |
| Neo4j | Java | 우선 | 그래프 DB. index-free adjacency, Cypher 플래너 |
| Apache AGE | C | | PostgreSQL 확장형 그래프 DB. PostgreSQL 문서와 붙여 읽기 |
| Nginx | C | 우선 | 리버스 프록시, 이벤트 루프, upstream 로드밸런싱 |
| Envoy | C++ | | L7 프록시, xDS 동적 설정 |
| Prometheus | Go | 우선 | pull 스크랩, TSDB(head block -> 압축 블록) |
| Cassandra | Java | | LSM, gossip, consistent hashing, hinted handoff |
| Jenkins | Java | | remoting(controller-agent), Pipeline CPS 실행 |
| Argo CD | Go | | GitOps reconcile. Jenkins와 대비 |
| Flink | Java | | 체크포인트(Chandy-Lamport), exactly-once |
| Temporal | Go | | durable execution. saga/orchestration 노트와 연결 |
| ZooKeeper | Java | | ZAB. KRaft 이전 구조 비교용 |
| ClickHouse | C++ | | MergeTree. 기존 `cs/systems/clickhouse-mergetree`와 연결 |
| MinIO | Go | | 오브젝트 스토리지, erasure coding |
| containerd / runc | Go | | namespace, cgroup |
| MongoDB | C++ | 우선 | WiredTiger(B-Tree + 저널), replica set 선출, oplog, 샤딩(mongos, config server) |

### 5.3 로그·관측성

| 도구 | 언어 | 우선 | 핵심 볼거리 |
|---|---|---|---|
| Logstash | Java/JRuby | 우선 | input -> filter -> output 파이프라인, persistent queue, 배압 |
| Beats / Elastic Agent | Go | 우선 | 파일 tail과 오프셋(registry), at-least-once 전송 |
| Kibana | TypeScript | | 쿼리 DSL 생성, 서버 플러그인 구조 |
| Fluent Bit | C | 우선 | 경량 수집기, 버퍼링과 재시도 |
| Vector | Rust | | 수집·변환 파이프라인, 디스크 버퍼 |
| Grafana Loki | Go | 우선 | 라벨만 색인. ES와 정반대 설계 |
| OpenTelemetry Collector | Go | 우선 | receiver -> processor -> exporter, 신호 통합 표준 |
| Jaeger / Tempo | Go | | 분산 트레이싱, span 저장과 샘플링 |
| Datadog Agent | Go | | check 스케줄링, DogStatsD 집계 |
| Grafana | Go/TS | | 데이터소스 플러그인, 알림 평가 루프 |
| Zabbix | C | | 전통적 push/pull 혼합 모니터링, 비교용 |

### 5.4 헬스체크·회복성 (watchdog 계열)

| 도구 | 언어 | 우선 | 핵심 볼거리 |
|---|---|---|---|
| Resilience4j | Java | 우선 | circuit breaker 상태 머신, bulkhead, retry |
| systemd | C | | watchdog(`WatchdogSec`), 재시작 정책, cgroup |
| Kubernetes probe (kubelet) | Go | | liveness/readiness/startup probe 루프 |
| Spring Boot Actuator | Java | | HealthIndicator 집계, 가용성 상태 전이 |
| Sentinel (Alibaba) | Java | | 유량 제어, 슬라이딩 윈도우 통계 |

### 5.5 DB·저장소

| 도구 | 언어 | 우선 | 핵심 볼거리 |
|---|---|---|---|
| pgvector | C | 우선 | PostgreSQL 확장. HNSW, IVFFlat, 거리 연산자와 인덱스 접근 메서드 |
| SQLite | C | 우선 | B-Tree 페이지, VDBE 바이트코드, WAL 모드. DB 내부 입문 |
| RocksDB | C++ | 우선 | LSM 엔진 표준 구현, 여러 DB와 Kafka Streams의 하부 |
| TiDB / TiKV | Go / Rust | | 분산 SQL, Raft 멀티 그룹, Percolator 트랜잭션 |
| CockroachDB | Go | | 분산 SQL, range 분할, HLC 시계 |
| Vitess | Go | 우선 | MySQL 샤딩 미들웨어, 쿼리 라우팅, 리샤딩 |
| DuckDB | C++ | | 벡터화 실행 OLAP. ClickHouse와 대비 |
| Memcached | C | | slab 할당자, LRU. Redis와 대비 |
| ScyllaDB | C++ | | Cassandra 재구현, shard-per-core(Seastar) |
| HBase + HDFS | Java | | region, NameNode. 하둡 계열 원형 |
| Milvus | Go | | 벡터 DB. pgvector와 대비 |
| InfluxDB / TimescaleDB | Go·Rust / C | | 시계열 DB. Prometheus TSDB와 비교 |
| Ceph | C++ | | 분산 스토리지, CRUSH 배치 |

### 5.6 메시징·스트리밍

| 도구 | 언어 | 우선 | 핵심 볼거리 |
|---|---|---|---|
| Apache Pulsar | Java | 우선 | 브로커와 저장소(BookKeeper) 분리. Kafka와 대비 |
| NATS / JetStream | Go | | 경량 pub/sub + 영속 스트림 |
| Redpanda | C++ | | Kafka 호환 재구현, Raft, thread-per-core |
| ActiveMQ Artemis | Java | | JMS 브로커. messaging-jms 노트와 연결 |
| Apache Spark | Scala | | DAG 스케줄러, shuffle |

### 5.7 게이트웨이·서비스 메시·디스커버리

| 도구 | 언어 | 우선 | 핵심 볼거리 |
|---|---|---|---|
| Spring Cloud Gateway | Java | 우선 | WebFlux 기반 필터 체인. webflux 노트와 연결 |
| Consul | Go | 우선 | Raft(서버) + gossip(에이전트), 서비스 디스커버리 |
| Istio | Go | | Envoy를 제어하는 control plane(xDS) |
| Kong | Lua(OpenResty) | | Nginx 위의 플러그인 게이트웨이 |
| Traefik / HAProxy | Go / C | | 동적 라우팅 / L4·L7 로드밸런싱 |
| Eureka / Nacos | Java | | Spring Cloud 계열 레지스트리, AP 설계 |

### 5.8 보안·인증

| 도구 | 언어 | 우선 | 핵심 볼거리 |
|---|---|---|---|
| Keycloak | Java | 진행 | OIDC/OAuth2 인가 서버. spring-security resource-server 노트의 반대편 |
| HashiCorp Vault | Go | | seal/unseal(Shamir), 동적 시크릿, lease |

### 5.9 인프라·컨테이너·배포

| 도구 | 언어 | 우선 | 핵심 볼거리 |
|---|---|---|---|
| Terraform | Go | 우선 | plan(의존 그래프 diff), state, provider 플러그인(gRPC) |
| Docker(moby) | Go | | 이미지 레이어(overlayfs), 데몬 구조 |
| BuildKit | Go | | 빌드 DAG, 레이어 캐시 |
| Helm | Go | | 템플릿 렌더링, 릴리스 이력 |
| Ansible | Python | | push형 멱등 구성 관리 |
| GitLab Runner / Tekton | Go | | CI 실행기. Jenkins와 비교 |

### 5.10 런타임·미들웨어 (Java)

| 도구 | 언어 | 우선 | 핵심 볼거리 |
|---|---|---|---|
| Netty | Java | 우선 | 이벤트 루프, ChannelPipeline, ByteBuf 풀링 |
| HikariCP | Java | 우선 | 커넥션 풀 동시성(ConcurrentBag) |
| Tomcat | Java | | 커넥터, 스레드 모델, NIO poller |
| gRPC-java | Java | | HTTP/2 스트림, 데드라인 전파 |
| Spring Batch | Java | 우선 | chunk 처리, JobRepository 재시작 의미론 |
| Quartz / ShedLock | Java | | 분산 스케줄링과 락 |
| Seata | Java | | 분산 트랜잭션(AT 모드). saga 노트와 비교 |
