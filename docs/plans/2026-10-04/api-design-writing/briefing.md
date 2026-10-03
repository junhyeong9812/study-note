# 집필 브리핑 — 커리큘럼 leaf 새 노트 (API 설계, 2026-10-04)

> 명세: 같은 폴더 `requirement-spec.md`. 문서 규칙 정본: `cs/README.md` 「작성 규칙」(2026-10-01 머리말 정리 반영판).
> 형식 참고(내용 복사 금지): `cs/database/16-mvcc/`, `cs/os/19-deadlock/`, `cs/network/15-tcp-handshake-and-backlog/`

## 1. 입력

- **커리큘럼 행**: `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §15 API 설계 표에서 담당 slug를 찾는다. 요지·선행·⚠ 깨지면·🔧·📚 칸은 **모두 다뤄야 할 요구사항**이다. §15 머리 문단(HTTP 프로토콜 본문은 network/33~35 — 여기선 **설계 판단**만, 뼈대: Fielding 5장·RFC 9110·9457·Google AIP·DDIA 4장·Stripe)도 읽는다.
- **영역 표**: `cs/api-design/curriculum.md`(생성 문서). 기존 사례 6편은 `cs/api-design/22-case-order-point` ~ `27-case-refund`(옛 형식 — **읽기만**, 링크 대상).
- **근거**: Fielding 2000 5장(ics.uci.edu), RFC 9110·9111·9457·8594·9745·8259·6585·7231(역사), IETF httpapi draft(Idempotency-Key·RateLimit 헤더 — 판 번호·만료 확인), Google AIP(aip.dev 각 번호), DDIA 4장, Stripe API 문서, Hyrum's Law(hyrumslaw.com·SWE@G 1장), Fowler "Richardson Maturity Model", Winand use-the-index-luke(페이지), Protobuf(protobuf.dev)·Avro 명세, Standard Webhooks 명세, gRPC 문서(deadlines·status codes·keepalive·load balancing), GraphQL 명세(spec.graphql.org)·graphql/dataloader, OpenAPI 3.1, AMQP 0-9-1·MQTT 5·Kafka 프로토콜 문서, Azure 아키텍처 패턴(Gateway Routing/Aggregation/Offloading·BFF·Valet Key·Gatekeeper), 사고 원문. 책 본문을 못 열면 목차·출판사 발췌로 확인한 범위만 단정, 나머지는 장 단위·`[?]`.
- WebSearch·WebFetch·curl이나 **실험(§5)** 으로 **실제 확인**한 것만 사실로 쓴다.

## 2. 출력 — `cs/api-design/<NN-slug>/`의 4파일

- **새 형식(2026-10-01)**: 제목 다음 줄부터 바로 본문이다. **제목 아래 `>` 머리말·복습 안내·"Claude 초안" 표식 줄을 두지 않는다.** 진행 단계는 같은 폴더 `metadata.md`에 둔다.

### metadata.md (그대로)

```
# metadata

| 항목 | 값 |
|---|---|
| 단계 | 초안 |
| 초안 | 2026-10-04 (Claude) |
| 검수 | — |
| 학습 | — |
```

### 2-summary.md

```
# api-design/<NN-slug> — <한 줄 제목> — 정리 (힌트)

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
- **동작·원리**: 중심. ASCII 그림 먼저(요청·응답 시퀀스, 재시도 시간축, 클라이언트-서버-저장소 상자 그림, 상태 기계, 버전 호환 매트릭스, 페이지 경계 그림, 웹훅 재전송 흐름, 게이트웨이 경로), 글은 그 해설.
- **쓰이는 자료구조·알고리즘**: 예) 멱등 키-결과 저장소(TTL), keyset = B+Tree 범위 스캔, 커서 인코딩, 버전 비교(ETag), 토큰 버킷·슬라이딩 윈도, varint·zigzag, HMAC, 재시도 큐·지수 백오프, 작업 상태 기계, DataLoader(배치+캐시), 트리(자원 계층). cs 노트가 있으면 링크.
- **적용 — 풀어나가는 법**: 실무 순서. 코드(Java 기본 — `com.sun.net.httpserver`·JDK `HttpClient`·Jackson, 필요 시 Spring Boot·TS/Node)와 진단(curl -i로 헤더 확인, 로그·지표로 재시도·중복 탐지, EXPLAIN 등).
- **장애 시나리오와 대처**: 3~5개. **현상 → 보이는 형태(에러·로그·지표) → 원인 → 대처**, ⚠ 칸 포함.
- **핵심 문장**: 3~6문장.
- **관련 주제·근거**: 선행·후속 링크(새 노트 `../NN-slug/2-summary.md`, 아직 없는 api-design 주제는 `../curriculum.md`, 다른 영역은 그 영역 README + "미작성", 다른 영역은 실제 경로 확인 — 특히 `../../network/…`(33 http-semantics·34 caching·35 connection·36 http2·38 websocket·46 load balancers), `../../database/…`(08 btree·17 OCC·18 app-level concurrency), `../../distributed/…`(15 saga·16 outbox·17 queues), `../../reliability/…`(05 timeouts·06 retry·11 rate limiter·13 idempotency), `../../security/…`(있는 것만), `../../software-design/…`(23 DbC), `../../testing/…`(13 contract testing), 사례 `../22-case-order-point/…`~`../27-case-refund/…`), 논문·문서 URL·소스 경로·교재 장, **실험 목록**(무엇을 어떤 환경에서 돌렸나).

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
- **제품·버전 한정**: "RFC 9110 기준", "Jackson 2.x 기본값", "gRPC-Java 1.x에서는", "Spring Boot 3.x/4.x에서는", "draft-ietf-httpapi-…-0N 기준(초안)". 책의 원칙(저자 주장)과 사실(측정·문서)을 구분하고, 저자마다 다른 정의(예: Fielding의 REST 제약 vs 업계의 'REST API', RFC 9110의 멱등 정의 vs Stripe 멱등 키 의미, AIP 권고 vs 다른 회사 관례)는 출처별로 나눠 쓴다.
- **원칙은 주장으로, 측정은 측정으로**: "좋은 설계"는 단정하지 않는다 — 어떤 변경에서 비용이 줄었는지 실험(diff 크기·영향 파일 수)으로 보이고, 반대 상황(그 추상이 손해인 변경)도 함께 보인다(APOSD·YAGNI 균형).
- **라이브러리·표준 동작은 버전·조건과 함께**: 예) Jackson `FAIL_ON_UNKNOWN_PROPERTIES`(기본 true)·enum 역직렬화 실패, JS `Number.MAX_SAFE_INTEGER`, Protobuf 알 수 없는 필드 보존(proto3 3.5+), HTTP 클라이언트별 자동 재시도(어느 메서드·상태에서), 429·503의 `Retry-After`, `412`/`428`, gRPC 상태 코드와 HTTP 매핑, GraphQL 오류 형식 — 문서·소스·실행으로 확인. **표준(RFC) vs 초안(draft) vs 회사 관례(Stripe·AIP)를 구분해 쓴다.**
- **계층을 섞지 않는다**: 프로토콜 보장 vs 클라이언트 라이브러리 기본값 vs 애플리케이션 책임.
- **도구 기본값·지표 정의는 문서·소스로 확인**(예: Jackson 기본 Feature 값, gRPC 기본 keepalive·deadline 없음, nginx `limit_req` 동작).
- **사고 보고서의 시각·수치는 원문 그대로**, 해석은 "해석"이라고 표시.

## 4. 기존 노트

- 신규 leaf 23편(01~21·28·29). 기존 사례 6편(22~27, 옛 형식 질문 A./B. 절)은 **읽기만** — 사례와 겹치는 원리는 사례로 링크하고 원리만 쓴다. HTTP 프로토콜 세부는 network 33~38 노트로 링크하고 설계 판단만 쓴다. reliability 13(멱등)·11(rate limiter), testing 13(계약 테스트)과 겹치는 부분도 링크.

## 5. 실험 근거 (명세 I7 — 사용자 요청, 필수)

- **편마다 실행으로 보일 수 있는 핵심 주장 1개 이상을 작은 실험으로 보인다**(28·29 종합은 선택). 예:
  - 01: 문서에 없는 동작(응답 필드 순서·목록 정렬·에러 문구)에 의존한 클라이언트가 서버의 "무해한" 변경에 깨지는 재현(Hyrum).
  - 02·03·04: 동사형 URL + 모든 것을 POST로 했을 때 캐시·재시도 안전성 차이(JDK HttpClient·curl), 200+에러 바디 vs 4xx/5xx에서 클라이언트 재시도·모니터링 집계 차이, RFC 9457 `application/problem+json` 응답과 스택 트레이스 노출 사례.
  - 05: Idempotency-Key 없는 재시도로 이중 결제 → 키-결과 저장소로 1회, 같은 키 다른 본문 422, 동시 같은 키 409(PG 17 유일 제약).
  - 06·12: offset vs keyset(PG 17, 행 수 키우며 EXPLAIN ANALYZE 시간·rows), 페이지 사이 삽입에 따른 중복·누락 재현, 인덱스 없는 정렬 허용 시 Sort 노드.
  - 07·08: 필드 추가·enum 값 추가에 Jackson 엄격 역직렬화 실패(`UnrecognizedPropertyException`, enum `InvalidFormatException`), JS에서 2^53+1 ID 손실, Protobuf 필드 번호 재사용으로 조용한 오역(protoc/maven).
  - 09·10: 웹훅 HMAC 서명 검증(위조·재전송·타임스탬프 창), 순서 역전·중복 전달에서 상태 역행 재현과 버전/이벤트 시각 비교로 해결, 발송 파이프라인의 멱등 발송 키.
  - 11·13·14: ETag/If-Match 없이 동시 편집 lost update → 412, 동기 처리 LB 타임아웃 vs 202+작업 자원 폴링, 429+Retry-After 준수 클라이언트 vs 무시 클라이언트(nginx `limit_req` 또는 자체 토큰 버킷).
  - 15·16: gRPC 데드라인 미설정 시 무한 대기 vs 설정(grpc-java maven), 스트리밍 흐름 제어·취소.
  - 17: GraphQL 리졸버 N+1 쿼리 수 vs DataLoader 배치(graphql-js 또는 graphql-java), 깊이 제한 없는 쿼리 비용.
  - 18~21: 공개 조회를 GraphQL POST로 할 때 HTTP 캐시 미적중(nginx 캐시), MQTT QoS·Kafka ack 모델(apache/kafka:4.1.0 일회용), 게이트웨이 오프로딩, OpenAPI 명세-구현 불일치를 검증 도구로 검출.
- 실험 코드는 scratchpad에 둔다(저장소 루트·노트 폴더 금지). 결과 표에는 실제 명령 출력만 싣는다.
- **노트에 싣는 것**: 실험 코드(핵심 부분), 실행 환경(제품·버전), **실제 출력**(손으로 만들지 않는다), 관찰과 해석. 출력 블록 앞에 `(실험, JDK 21 temurin, 2026-10-04)`처럼 환경을 적는다. 비결정적 값은 "실행마다 다르다"고 적고 여러 번 돌린 범위를 쓴다.
- **실험으로 보일 수 없는 주장**은 1차 출처로 대신하고 그 사실을 적는다.
- **packet에 실험 목록**: 주장 · 코드 파일(scratchpad 경로) · 실행 명령 · 환경 · 출력 요지. 사실 점검 워커가 다시 돌린다.
- **재부팅 대비**: 실험 코드의 핵심은 노트에 싣는다(/tmp는 재부팅 때 사라진다).

## 6. 실행 환경과 안전 규칙

- **공용 컨테이너 없음** — 필요한 것은 워커가 **자기 전용 일회용 컨테이너**로 띄운다: 이름 `sn-ad-w<NN>-*`, 네트워크 `sn-ad-w<NN>-net`, 포트는 열지 않거나 127.0.0.1만. **이미 있는 이미지만** 쓴다(`eclipse-temurin:21-jdk`, `maven:3.9-eclipse-temurin-21`, `postgres:17`, `redis:7-alpine`, `node:22-alpine`·`node:22-bookworm-slim`, `grafana/k6:1.2.3`, `nginx:alpine`, `apache/kafka:4.1.0`, `testcontainers/ryuk:0.12.0`·`0.14.0`) — **새 이미지 받기 금지**. 끝나면 자기 컨테이너만 `docker rm -fv <이름>` + `docker network rm <자기 네트워크>`. **`docker volume prune`·`system prune`·`image prune` 등 일괄 삭제 금지**(남의 볼륨까지 지울 수 있다), `docker ps -a --filter name=sn-ad-w<NN>`가 비었는지 확인.
- **Testcontainers(필요할 때만)**: maven 컨테이너에 `-v /var/run/docker.sock:/var/run/docker.sock`을 붙이고, 이미지 이름을 이미 있는 태그로 고정한다(`postgres:17`, `TESTCONTAINERS_RYUK_CONTAINER_IMAGE=testcontainers/ryuk:0.14.0` 또는 0.12.0). 컨테이너 안에서 호스트 접근은 `TESTCONTAINERS_HOST_OVERRIDE`·`--add-host=host.docker.internal:host-gateway` 등 문서 방식으로. 실행 전후 `docker ps -a --filter label=org.testcontainers=true`를 기록하고 끝나면 0이어야 한다(남으면 그 라벨 컨테이너 중 **자기가 만든 것만** 지운다). 새 이미지가 필요해지면 받지 말고 멈춰 packet에 보고.
- **파일 소유권**: 컨테이너는 `-u $(id -u):$(id -g) -e HOME=/tmp`로 돌린다(root로 돌리면 scratchpad에 root 소유 파일이 남는다). maven은 `-Dmaven.repo.local=/m2`에 `-v <scratchpad>/ts/m2:/m2`를 붙여 공용 로컬 저장소를 쓴다(스모크 확인: JUnit 5.13.4·surefire 3.5.3 받아 통과).
- **사용 통계 끄기(2026-10-03 w08)**: Pact는 `pact_do_not_track=true`, 의존성을 다 받은 뒤 실행은 `--network none`. Testcontainers는 매핑 포트를 0.0.0.0에 잠깐 연다(문서 동작) — 실행 시간을 짧게.
- **라이선스·사용 조항 존중(2026-10-03 w07)**: jqwik 1.10 User Guide에 AI 코딩 에이전트 사용을 원치 않는다는 "Anti-AI Usage Clause"가 있다 — jqwik은 실행하지 않는다(문서 인용·코드 모양만, 실험은 fast-check 등). 다른 도구도 비슷한 조항이 있으면 따르고 packet에 보고.
- **Java 실행**: 호스트 java는 8이다. `docker run --rm -v <scratchpad 절대경로>:/w -w /w eclipse-temurin:21-jdk java X.java`. 라이브러리(JUnit 5·Mockito·AssertJ·jqwik·PIT·JaCoCo·Pact·H2 등)는 maven 이미지로 받아 쓴다 — 소규모 `pom.xml` 프로젝트 + `mvn -q test`, 로컬 저장소는 scratchpad 안(`-Dmaven.repo.local=/w/.m2`, 담당 폴더끼리 공유하려면 `scratchpad/ts/m2`). **Node**: 호스트 node 18, TS는 `tsc`.
- **부하 상한**: 실행 수십 초 이내, `--cpus=2` 이하로 제한, 호스트를 포화시키는 부하 테스트·메모리를 크게 먹는 실험(힙 1GB 초과) 금지. 측정 수치는 이 제한 환경의 값이라고 적는다.
- **파일 위치**: 모든 파일은 `/tmp/claude-1000/-home-jun-project-study-note/16696510-853f-4d10-82ba-64d9eb37bcc8/scratchpad/ad/<담당 첫 번호>/`에만(절대 경로). **저장소 루트·노트 폴더에 파일을 만들지 않는다.**
- **이미지(2026-10-01 사고)**: 이 작업은 이미지를 받지도 지우지도 않는다(`docker pull`·`docker rmi` 금지).
- **개인정보 금지(2026-10-01 사고)**: HTTP 요청(User-Agent·헤더·쿼리)·파일·노트 어디에도 사용자의 이메일·이름 등 개인 식별 정보를 넣지 않는다. SEC처럼 연락처 User-Agent를 요구하는 사이트는 열지 말고 다른 출처(언론·미러)를 쓰거나 `[?]`.
- **금지**: `sn-ts-*`·`sn-dm-*`·`sn-sd-*`·`sn-rl-*`·`sn-dw-*`·`payment-codex-*`·`jun-bank-*` 등 이 작업이 만들지 않은 컨테이너·볼륨·이미지는 건드리지 않는다.

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
