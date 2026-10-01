# 집필 브리핑 — 커리큘럼 leaf 새 노트 (분산 시스템, 2026-10-01)

> 명세: 같은 폴더 `requirement-spec.md`. 문서 규칙 정본: `cs/README.md` 「작성 규칙」(2026-10-01 머리말 정리 반영판).
> 형식 참고(내용 복사 금지): `cs/database/16-mvcc/`, `cs/os/19-deadlock/`, `cs/network/15-tcp-handshake-and-backlog/`

## 1. 입력

- **커리큘럼 행**: `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §10 분산 시스템 표에서 담당 slug를 찾는다. 요지·선행·⚠ 깨지면·🔧·📚 칸은 **모두 다뤄야 할 요구사항**이다. §10 머리 문단(뼈대: DDIA 1판 5·8·9·10·11장, MIT 6.5840 Spring 2026)도 읽는다.
- **영역 표**: `cs/distributed/README.md` — 번호·선행·다른 영역 노트 링크 대상.
- **근거**: DDIA 1판, MIT 6.5840 강의 노트·논문 목록(pdos.csail.mit.edu/6.824), 원논문(Lamport 1978 "Time, Clocks…", Lamport 2001 "Paxos Made Simple", FLP 1985, Ongaro–Ousterhout 2014 Raft, Gilbert–Lynch 2002, Abadi 2012, DeCandia 2007 Dynamo, Corbett 2012 Spanner, Kulkarni 2014 HLC, Shapiro 2011 CRDT, van Renesse–Schneider 2004, Hunt 2010 ZooKeeper, Castro–Liskov 1999, Nishtala 2013, Garcia-Molina–Salem 1987 등), 제품 문서·소스(etcd·ZooKeeper·Kafka·Redis·Debezium 등), 사고 보고서 원문(GitHub 2018-10-30, Cloudflare 2017-01-01 윤초, AWS 2011-04 EBS 등), Kleppmann 2016 "How to do distributed locking".
- WebSearch·WebFetch·curl이나 **실험(§5)** 으로 **실제 확인**한 것만 사실로 쓴다.

## 2. 출력 — `cs/distributed/<NN-slug>/`의 4파일

- **새 형식(2026-10-01)**: 제목 다음 줄부터 바로 본문이다. **제목 아래 `>` 머리말·복습 안내·"Claude 초안" 표식 줄을 두지 않는다.** 진행 단계는 같은 폴더 `metadata.md`에 둔다.

### metadata.md (그대로)

```
# metadata

| 항목 | 값 |
|---|---|
| 단계 | 초안 |
| 초안 | 2026-10-01 (Claude) |
| 검수 | — |
| 학습 | — |
```

### 2-summary.md

```
# distributed/<NN-slug> — <한 줄 제목> — 정리 (힌트)

## 해결하는 문제
## 동작·원리
## 쓰이는 자료구조·알고리즘
## 적용 — 풀어나가는 법
## 장애 시나리오와 대처
## 핵심 문장
## 관련 주제·근거
```

- 최상위 `## ` 헤딩은 이 7개만, 이 순서로 둔다(하위는 `###`). 실험 절은 `## 동작·원리`나 `## 적용` 안의 `### 실험: …`로 둔다.
- **해결하는 문제**: 이것이 없으면 무엇이 안 되나. 쉬운 예 → "똑같은 구조다" → 실무 예.
- **동작·원리**: 중심. ASCII 그림 먼저(노드·메시지 시퀀스 다이어그램, 시간축, 로그·term, 정족수 교집합), 글은 그 해설.
- **쓰이는 자료구조·알고리즘**: 예) 복제 로그, 벡터 시계, Merkle 트리, 일관 해싱, CRDT 반격자, 상태 기계, 오프셋 인덱스. cs 노트가 있으면 링크.
- **적용 — 풀어나가는 법**: 실무 순서. 코드(Java·JS·TS)와 진단 명령(`etcdctl endpoint status`, `kafka-topics --describe`(ISR), `kafka-consumer-groups --describe`(lag), `redis-cli` 등).
- **장애 시나리오와 대처**: 3~5개. **현상 → 보이는 형태(에러·로그·지표) → 원인 → 대처**, ⚠ 칸 포함.
- **핵심 문장**: 3~6문장.
- **관련 주제·근거**: 선행·후속 링크(새 노트 `../NN-slug/2-summary.md`, 아직 없는 distributed 주제는 `../README.md` + "미작성", 다른 영역은 실제 경로 확인 — 특히 `../../database/32-…`, `33-…`, `55-…`, `../../network/…`, `../../os/…`), 논문·문서 URL·소스 경로·교재 장, **실험 목록**(무엇을 어떤 환경에서 돌렸나).

### 1-question.md / 3-answer.md

`cs/database/16-mvcc/`와 같은 틀(머리말 없음). 질문 6~10개(왜 / 예측 / 경계 / 연결 / 장애 진단), 정답은 번호·개수 일치. 예측형 질문은 실험 출력으로 답을 확인할 수 있게 쓴다.

## 3. 쓰는 방식 (사용자와 합의된 기준)

1. **그림 먼저, 글은 그림 해설.** 단순한 그림 여러 개 > 복잡한 그림 하나.
2. **용어는 처음 나오는 자리 바로 아래에서 푼다.** 형식 `  - *용어*: 설명`.
3. 한 문장에 한 개념. 용어가 셋 넘게 든 문장은 쪼갠다.
4. **코드**: Java(기본)·JS·TS. 셸은 진단·실험 구동에만.
5. **사실 규칙**: 수치·기본값·버전은 출처나 실험으로 확인했을 때만. 확인 못 하면 `[?]`. **지어내지 않는다.** 예시 수치는 "(예시)".

## 3-1. 앞 영역에서 나온 주의 (2차 리뷰 수백 건의 유형)

- **`[?]`는 확인 못 한 것에만.** 확인했으면 근거(절·URL·소스 경로·실험)를 쓴다.
- **"항상·모든·반드시·절대" 금지** — 예외가 있으면 조건. (가장 많은 지적 유형)
- **노트 안 모순 금지**: 그림과 글, 요약과 정답, 정답 N과 M. 다 쓰고 스스로 대조.
- **제품·버전 한정**: "etcd 3.6에서는", "Kafka 4.1 KRaft에서는", "Redis 7.4에서는". 논문의 모델과 제품 구현을 구분한다(예: Raft 논문 vs etcd raft 구현, Dynamo 논문 vs Cassandra).
- **모델·가정 명시**: 동기/부분동기/비동기, crash-stop/crash-recovery/비잔틴 — 주장마다 어떤 모델에서 성립하는지.
- **보장의 범위를 정확히**: "exactly-once"·"선형화"·"원자적" 같은 말은 어느 범위(단일 파티션·단일 키·트랜잭션 프로듀서)에서의 보장인지 한정한다.
- **계층을 섞지 않는다**: 프로토콜 보장 vs 클라이언트 라이브러리 기본값 vs 애플리케이션 책임.
- **기본값은 해당 버전 문서·소스로 확인**(예: Kafka `acks` 기본값은 3.0부터 `all`, `min.insync.replicas` 기본 1 — 반드시 문서로 재확인).
- **사고 보고서의 시각·수치는 원문 그대로**, 해석은 "해석"이라고 표시.

## 4. 기존 노트 이어받기 (보강 17편 담당자)

- 원본은 **수정하지 않는다.** 담당 주제의 원본: 명세 §1 보강 목록.
- 원본을 먼저 **읽는다.** 이미 설명한 것은 길게 되풀이하지 않고 "기초는 원본 §N" 링크 + 한두 줄 요약.
- 빈 곳을 채운다: 커리큘럼 ⚠ 장애, 자료구조, 실험, 적용(코드·진단), 질문·정답.
- 원본에 틀린 내용이 있으면 새 leaf에 올바르게 쓰고 `참고: 원본 §N의 "…"는 …(근거)` 한 줄로 짚는다(인용문 `>`가 아닌 일반 문장).

## 5. 실험 근거 (명세 I7 — 사용자 요청, 필수)

- **편마다 실행으로 보일 수 있는 핵심 주장 1개 이상을 작은 실험으로 보인다**(종합 35·36 제외). 예:
  - 04: `System.currentTimeMillis()` vs `System.nanoTime()` — 벽시계를 뒤로 돌릴 수 없으면 두 시계의 정의·단조성 차이를 코드로 보이고, 음수 duration이 생기는 계산을 재현(시계 조작은 컨테이너 안 `faketime` 류가 없으면 시뮬레이션 클래스로, 그렇게 했다고 명시).
  - 05: 램포트·벡터 시계 구현과 메시지 교환 시뮬레이션 → 동시 이벤트 판정 출력.
  - 09: N=3 복제 시뮬레이터에서 R·W 조합별 오래된 읽기 비율.
  - 10·11·12: etcd 3노드에서 리더 컨테이너 정지 → 재선출까지 시간·term 증가(`etcdctl endpoint status`), lease 만료, fencing token(revision) 없는 락의 이중 쓰기 vs 있는 락.
  - 17·18·21: Kafka `acks`·리더 교체·오프셋 커밋 순서별 유실/중복 개수, 컨슈머 리밸런스.
  - 14: 2PC 코디네이터를 prepare 뒤 멈춰 참가자가 락을 쥐고 기다리는 모습(PostgreSQL `PREPARE TRANSACTION`은 `sn-dbw-pg`가 아니라 **자기 전용 일회용 PG 컨테이너**로).
  - 24: G-Counter·OR-Set 병합 결과, LWW 유실 재현.
- **노트에 싣는 것**: 실험 코드(핵심 부분), 실행 환경(제품·버전·노드 수), **실제 출력**(손으로 만들지 않는다), 관찰과 해석. 출력 블록 앞에 `(실험, etcd 3.6.5 3노드, 2026-10-01)`처럼 환경을 적는다. 비결정적 값(시간·ID)은 "실행마다 다르다"고 적고 경향을 말한다.
- **실험으로 보일 수 없는 주장**(대규모 수치·불가능성 증명)은 1차 출처로 대신하고 그 사실을 적는다.
- **packet에 실험 목록**을 낸다: 주장 · 코드 파일(scratchpad 경로) · 실행 명령 · 환경 · 출력 요지. 사실 점검 워커가 다시 돌린다.

## 6. 실행 환경과 안전 규칙

- **공용 컨테이너**(메인이 띄움, 스모크 완료 — 쓰기·읽기만, 정지·재시작·네트워크 조작 금지):
  - etcd 3.6.5 3노드: `sn-dw-etcd1·2·3`(네트워크 `sn-dw-net`). 명령: `docker exec sn-dw-etcd1 etcdctl --endpoints=http://sn-dw-etcd1:2379,http://sn-dw-etcd2:2379,http://sn-dw-etcd3:2379 …`. 키는 `/w<NN>/` 접두사만.
  - Kafka 4.1.0 KRaft 단일 노드: `sn-dw-kafka`. 명령: `docker exec sn-dw-kafka /opt/kafka/bin/kafka-*.sh --bootstrap-server localhost:9092 …`. 토픽 이름은 `w<NN>-*`만, 끝나면 삭제.
  - Redis 7.4.9: `sn-dw-redis`. 명령: `docker exec sn-dw-redis redis-cli …`. 키는 `w<NN>:` 접두사만, 끝나면 삭제. `FLUSHALL`·`CONFIG SET` 금지.
- **파괴 실험**(노드 kill·재시작·네트워크 분할·브로커 여러 대·PG 2PC)은 **자기 전용 일회용 컨테이너**로: 이름 `sn-dw-w<NN>-*`, 네트워크 `sn-dw-w<NN>-net`, 포트는 열지 않거나 127.0.0.1만. 이미지는 이미 받은 것만(`quay.io/coreos/etcd:v3.6.5`, `apache/kafka:4.1.0`, `redis:7-alpine`, `postgres:17`, `eclipse-temurin:21-jdk`). 끝나면 `docker rm -f` + `docker network rm`, 그리고 `docker ps -a --filter name=sn-dw-w<NN>`가 비었는지 확인.
- **Java 실행**: 호스트 java는 8이라 단일 파일 실행이 안 된다. `docker run --rm -v <scratchpad 절대경로>:/w -w /w eclipse-temurin:21-jdk java X.java`(같은 네트워크가 필요하면 `--network sn-dw-net`). **Node**: 호스트 node 18 (`node x.js`), TS는 `tsc`.
- **부하 상한**: 노드 몇 개, 메시지 수천 건, 실행 수십 초 이내. CPU 여러 코어를 오래 채우지 않는다.
- **파일 위치**: 모든 파일은 `/tmp/claude-1000/-home-jun-project-study-note/16696510-853f-4d10-82ba-64d9eb37bcc8/scratchpad/dist/<담당 첫 번호>/`에만(절대 경로). **저장소 루트·노트 폴더에 파일을 만들지 않는다.**
- **금지**: `sn-dbw-*`(DB 작업 컨테이너), `payment-codex-*` 등 이 작업이 만들지 않은 컨테이너·볼륨은 건드리지 않는다.

## 7. 하지 말 것

- 담당 폴더 밖 파일(원고·다른 영역·커리큘럼·README 등)을 수정하지 않는다. git은 조회만.
- 리프 폴더에는 md만(1-question·2-summary·3-answer·metadata).
- 하위 에이전트·fork 금지.

## 8. 자기 검증

- `python3 docs/plans/2026-09-30/network-writing/check_new.py <담당 폴더들>` → 전부 PASS(머리말 금지·metadata 검사 포함).
- §3-1 노트 안 모순 자기 대조. 실험 출력과 본문·정답의 수치가 같은지 대조.

## 9. 반환 packet

- 폴더 목록과 check 결과
- 편별 주요 근거(논문·문서 URL·소스 경로·교재 장)
- **실험 목록**(주장 · 코드 경로 · 명령 · 환경 · 출력 요지) + 전용 컨테이너·토픽·키를 지웠는지
- `[?]` 목록, 커리큘럼 ⚠ 칸 커버 여부, 미완료 항목
