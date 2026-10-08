# testing/13-contract-testing — 소비자 주도 계약 테스트 — 정리 (힌트)

## 해결하는 문제

서비스 A(소비자)가 서비스 B(제공자)의 HTTP API를 부른다. 각 팀은 자기 테스트를 다 통과시킨다. 그런데 배포하면 A가 깨진다.

```text
  order-service(소비자) 테스트         user-service(제공자) 테스트
   └ user-service를 mock으로 대체        └ 자기 API를 자기 기대대로 검증
       {id, name}을 준다고 가정             name → fullName으로 바꾸고 테스트도 고침
           ✅ 초록                               ✅ 초록
                       배포 ▼
   order-service 운영: IllegalStateException: name missing  ❌
```

- 소비자의 mock은 제공자가 바뀌어도 그대로 남는다. 제공자 테스트는 "누가 무엇을 쓰는지" 모른다.
- 둘을 함께 띄운 E2E 테스트로 잡을 수는 있다. 대신 느리고, 서비스가 많아지면 조합이 폭발한다([18-e2e-and-ui-testing](../18-e2e-and-ui-testing/2-summary.md)).

쉬운 예: 집 열쇠를 복사해 줬다.

- 집주인이 자물쇠를 바꾸면, 열쇠를 가진 사람들은 집 앞에 와서야 안다.
- 열쇠를 가진 사람마다 "내 열쇠 본"을 집주인에게 맡겨 두면, 집주인은 자물쇠를 바꾸기 전에 그 본들로 시험해 볼 수 있다.

똑같은 구조다.\
"열쇠 본" = 소비자가 기대하는 요청·응답 예제 묶음(계약). 제공자는 바꾸기 전에 그 예제를 재생해 본다.

실무 예:

- 응답 필드 이름 변경(`name` → `fullName`), 타입 변경(`id` 숫자 → 문자열), 필수 필드 삭제 — 제공자 쪽 테스트는 초록이고 소비자만 운영에서 깨진다(커리큘럼 ⚠ 칸).

## 동작·원리

### 1. 두 갈래 테스트와 계약 파일

```text
  ① 소비자 테스트                         ② 제공자 검증
  ┌─────────────┐   요청    ┌───────────┐       ┌───────────┐ 재생 요청 ┌──────────────┐
  │ 소비자 코드  │ ───────▶ │ Pact 모의 │       │ Pact 검증기 │ ───────▶ │ 실제 제공자    │
  │ (UserClient)│ ◀─────── │ 제공자     │       │            │ ◀─────── │ (user-service)│
  └─────────────┘  예제 응답 └─────┬─────┘       └─────┬──────┘ 실제 응답 └──────────────┘
                                  │ 계약 파일 생성         ▲ 응답이 계약의 규칙과 맞나 비교
                                  ▼                      │
                      order-service-user-service.json ───┘ (파일 공유·또는 Pact Broker)
```

- Pact 문서("How Pact works")의 설명
  - 소비자 테스트: "제공자가 기대한 응답을 준다고 가정할 때, 소비자 코드가 요청을 올바르게 만들고 응답을 올바르게 처리하나?"를 상호작용마다 확인한다. 끝나면 상호작용을 기술한 **pact 파일**을 만든다.
  - 제공자 검증: 각 요청을 제공자에게 보내고, 실제 응답을 소비자 테스트가 기술한 **최소 기대 응답**과 비교한다.
  - 둘을 짝지으면 서비스를 함께 띄우지 않고 계약 전체를 시험한다.
- *제공자 상태(provider state)*: 상호작용의 전제(예: "user 1 exists"). 제공자 검증 전에 그 데이터를 준비하는 훅을 부른다.

### 2. 소비자 주도 — 계약의 출처

- Ian Robinson "Consumer-Driven Contracts: A Service Evolution Pattern"(2006)의 구분
  - *제공자 계약*: 제공자가 내보내는 전체 기능(스키마·인터페이스 등).
  - *소비자 계약*: 소비자 하나가 제공자 계약에 거는 기대 — **부분집합**이다.
  - *소비자 주도 계약*: 현재 소비자들의 기대를 모은 것이 곧 제공자가 지켜야 할 범위다.
- 효과: 제공자는 "아무도 안 쓰는 필드"는 자유롭게 바꾸고, "누군가 쓰는 필드"를 바꿀 때만 막힌다.

### 3. 계약 = 예제 집합 + 매칭 규칙

실험의 소비자 테스트(Pact JVM 4.7.5, V3 형식)가 만든 파일 발췌:

```json
"response": {
  "body": { "id": 1, "name": "Kim" },
  "matchingRules": {
    "body": {
      "$.id":   { "combine": "AND", "matchers": [ { "match": "integer" } ] },
      "$.name": { "combine": "AND", "matchers": [ { "match": "type" } ] }
    }
  },
  "status": 200
}
```

- 계약은 스키마 전체가 아니라 **예제 하나 + 규칙**이다. `"id": 1`이라는 값이 아니라 "정수면 된다", `"name": "Kim"`이 아니라 "문자열이면 된다".
  - *매처(matcher)*: 값이 아니라 모양을 비교하는 규칙. 값을 그대로 비교하면 제공자의 테스트 데이터가 조금만 달라도 깨진다.
- Pact 매칭 문서는 Postel의 법칙을 따른다고 적는다.
  - 응답: "예상하지 않은" JSON 필드는 무시한다(다른 소비자가 쓰는 필드일 수 있다).
  - 요청: 본문·쿼리에 예상하지 않은 값이 있으면 허용하지 않는다(헤더는 예외).

### 4. 실험: 제공자 변경 네 가지

제공자를 JDK `HttpServer`로 흉내 내고, 판(variant)만 바꿔 같은 계약 파일로 검증했다.

```java
String body = switch (variant) {
  case "add"      -> "{\"id\":1,\"name\":\"Kim\",\"email\":\"kim@example.com\"}"; // 필드 추가
  case "rename"   -> "{\"id\":1,\"fullName\":\"Kim\"}";                            // 이름 변경
  case "idstring" -> "{\"id\":\"1\",\"name\":\"Kim\"}";                            // 타입 변경
  default         -> "{\"id\":1,\"name\":\"Kim\"}";                                // v1
};
```

(실험, JDK 21 temurin · Pact JVM 4.7.5(consumer·provider junit5) · JUnit 5.13.4, 네트워크 차단 컨테이너, 2026-10-03)

v1·필드 추가 — 통과:

```text
Verifying a pact between order-service and user-service
  [Using File target/pacts/order-service-user-service.json]
  Given user 1 exists
  GET /users/1
    returns a response which
      has status code 200 (OK)
      has a matching body (OK)
```

이름 변경 — 실패:

```text
    returns a response which
      has status code 200 (OK)
      has a matching body (FAILED)

Failures:

1) Verifying a pact between order-service and user-service - GET /users/1 has a matching body

    1.1) body: $ Actual map is missing the following keys: name

        {
        -  "id": 1,
        -  "name": "Kim"
        +  "fullName": "Kim",
        +  "id": 1
        }
```

타입 변경 — 실패:

```text
    1.1) body: $.id Expected '1' (String) to be an integer
```

계약 없이 그대로 배포했다면 소비자에게 보였을 모습(같은 클라이언트를 rename 제공자에 직접 연결):

```text
consumer at runtime: java.lang.IllegalStateException: name missing: {"id":1,"fullName":"Kim"}
```

| 제공자 변경 | 계약 검증 | 소비자 운영 |
|---|---|---|
| v1 | 통과 | 정상 |
| 필드 추가(`email`) | 통과 — 응답의 추가 필드는 무시 | 정상(소비자가 모르는 필드 무시하게 짰음) |
| 이름 변경(`name`→`fullName`) | **실패**: missing keys: name | 실패 |
| 타입 변경(`id` 문자열) | **실패**: Expected '1' (String) to be an integer | (실험 안 함) |

- 관찰: 계약 검증은 **제공자 쪽 빌드**에서 실패했다. 소비자가 운영에서 깨지기 전, 바꾼 쪽에서 원인 필드를 짚었다.
- 필드 추가가 통과한 것은 두 가지가 맞물려서다. Pact가 응답의 추가 필드를 무시하고, 소비자 클라이언트도 모르는 필드를 무시하게 설정했다(`FAIL_ON_UNKNOWN_PROPERTIES=false`). 소비자 쪽 역직렬화가 엄격하면 계약은 통과해도 운영에서 깨질 수 있다 — 그 경우는 소비자 테스트가 잡아야 한다.

## 쓰이는 자료구조·알고리즘

- **계약 = 예제 집합** — 상호작용(요청 → 응답) 목록. 각 응답은 JSON 트리 + JSONPath 키(`$.id`)로 가리키는 매처 표다.
- **트리 비교(부분 일치)** — 기대 트리의 각 경로가 실제 트리에 있고 규칙을 만족하는지 본다. 실제 쪽의 추가 경로는 응답에서는 무시한다. 결과 메시지 `Actual map is missing the following keys`가 이 비교의 산물이다.
- **검증 행렬(matrix)** — Pact Broker는 "소비자 판 × 제공자 판 → 검증 결과" 표를 둔다. `can-i-deploy`는 배포하려는 판과 대상 환경에 이미 있는 상대 판들 사이에 성공한 검증이 있는지 이 표에서 찾는다(Pact 문서).
- 스키마 호환성 검사(데이터 계약)와의 차이: 스키마 레지스트리는 포맷(Avro·Protobuf·JSON Schema)마다 다른 **해석·호환 규칙**으로, 호환 모드가 정한 방향(새 스키마로 옛 데이터를 읽나 등)을 판정한다(Confluent "Schema Evolution and Compatibility"). 소비자 주도 계약은 **실제로 쓰는 예제**만 본다. 데이터 쪽은 [data-engineering/09-data-contracts-and-schema-registry](../../data-engineering/09-data-contracts-and-schema-registry/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. 소비자 팀: 실제로 쓰는 필드만 담아 소비자 테스트를 쓴다. 값 대신 매처(`integerType`·`stringType`)를 쓴다.
2. 계약 파일을 공유한다 — 작은 팀은 파일, 여럿이면 Pact Broker(PactFlow 등)에 게시.
3. 제공자 팀: 제공자 검증을 빌드에 넣고, 제공자 상태 훅으로 테스트 데이터를 준비한다.
4. 배포 전 `can-i-deploy`로 "지금 운영에 있는 상대 판과 검증됐나"를 확인한다. 배포 뒤 `record-deployment`로 어느 판이 어느 환경에 있는지 기록한다.

```bash
pact-broker can-i-deploy --pacticipant Foo --version 23 --to-environment production   # Pact 문서 예시
```

### 2. 소비자 테스트 (Java, Pact JVM 4.7.5)

```java
@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(providerName = "user-service", pactVersion = PactSpecVersion.V3)
class UserClientPactTest {
  @Pact(consumer = "order-service")
  public RequestResponsePact userById(PactDslWithProvider builder) {
    return builder
      .given("user 1 exists")
      .uponReceiving("GET /users/1")
        .path("/users/1").method("GET")
      .willRespondWith()
        .status(200)
        .body(new PactDslJsonBody()
          .integerType("id", 1)      // 타입만 맞으면 된다
          .stringType("name", "Kim"))
      .toPact();
  }

  @Test
  void readsUser(MockServer mockServer) throws Exception {
    UserClient.User u = new UserClient(mockServer.getUrl()).find(1);
    assertEquals("Kim", u.name());
  }
}
```

- Pact JVM 4.7.5에서는 `pactVersion`을 지정하지 않으면 V4 형식을 기본으로 쓴다. 위처럼 `RequestResponsePact`를 반환하는 메서드에 V3를 지정하지 않았더니 `Method userById does not conform required method signature 'public au.com.dius.pact.core.model.V4Pact xxx(PactBuilder builder)'`로 실패했다(실험).

### 3. 제공자 검증 (Java)

```java
@Provider("user-service")
@PactFolder("target/pacts")            // Broker를 쓰면 @PactBroker
class UserProviderPactTest {
  @BeforeEach void target(PactVerificationContext ctx) {
    ctx.setTarget(new HttpTestTarget("127.0.0.1", server.getAddress().getPort()));
  }
  @TestTemplate @ExtendWith(PactVerificationInvocationContextProvider.class)
  void verify(PactVerificationContext ctx) { ctx.verifyInteraction(); }

  @State("user 1 exists") void user1() { /* 테스트 데이터 준비 */ }
}
```

### 4. 계약 테스트가 맞지 않는 곳 (Pact 문서 "What is Pact good for")

- 소비자를 하나하나 알 수 없는 **공개 API** — 계약을 모을 소비자가 없다. 이 경우는 버저닝·하위 호환 규칙([api-design/07-versioning-and-compatibility](../../api-design/07-versioning-and-compatibility/2-summary.md))으로 간다.
- 제공자 **기능** 테스트 — 그것은 제공자 자신의 테스트 몫이다. 계약은 "모양과 의미의 최소 약속"만 본다.
- 요청을 검증 없이 하류로 넘기는 pass-through API, 성능·부하 테스트.

### 5. Fowler의 "ContractTest"(2011)와의 관계

- Fowler의 계약 테스트는 "테스트 더블이 외부 서비스와 같은 결과를 주는지" 주기적으로 확인하는 테스트다. 일반 빌드 파이프라인이 아니라 외부 서비스의 변경 주기에 맞춰(하루 한 번이면 충분한 경우가 많다고 적는다) 돌리고, 실패하면 빌드를 깨기보다 맞추는 작업을 일으키라고 한다.
- Pact식 소비자 주도 계약은 같은 문제(더블이 낡는다)를, 소비자의 더블에서 계약을 뽑아 제공자 빌드에서 재생하는 방식으로 푼다. 두 정의는 출처별로 구분해서 쓴다.

## 장애 시나리오와 대처

### 1. ⚠ 제공자 필드 변경 → 소비자만 운영에서 파손

- 현상: 제공자 배포 직후 소비자의 특정 화면·배치만 실패.
- 보이는 형태: 소비자 로그 `IllegalStateException: name missing` 류, 역직렬화 오류, NPE.
- 원인: 소비자의 mock이 옛 응답을 흉내 내고 있었다. 제공자 테스트는 소비자의 사용을 몰랐다.
- 대처: 소비자 계약을 제공자 빌드에서 검증한다(실험: `missing the following keys: name`). 필드를 바꿔야 하면 확장 → 소비자 이전 → 수축 순으로 나눈다([reliability/23-deployment-strategies](../../reliability/23-deployment-strategies/2-summary.md)의 확장 배포).

### 2. 계약이 너무 엄격해 제공자 변경마다 깨진다

- 현상: 제공자가 무해한 값(이름 철자, 날짜)만 바꿔도 검증 실패.
- 원인: 소비자 테스트가 매처 없이 정확한 값을 박았다. 또는 소비자가 쓰지 않는 필드까지 계약에 넣었다.
- 대처: 쓰는 필드만, 값 대신 타입·정규식 매처로 쓴다.

### 3. 계약은 통과했는데 의미가 바뀌었다

- 현상: 검증 초록. 그런데 소비자 집계가 틀어졌다.
- 원인: `amount`의 단위가 원 → 천 원으로 바뀌는 식의 **의미 변경**. 타입 매처로는 못 잡는다.
- 대처: 의미가 걸린 필드는 제공자 상태로 데이터를 고정하고 값(또는 범위) 규칙을 쓴다. 의미 변경은 새 필드로 낸다.

### 4. 소비자의 새 계약이 제공자 빌드를 막는다

- 현상: 소비자가 아직 없는 엔드포인트를 기대하는 계약을 올리자 제공자 main 빌드가 빨강.
- 원인: 소비자가 앞서 나가는 개발(새 기능)을 계약에 넣었다.
- 대처: Pact Broker의 **pending pacts** — 제공자 검증 설정에서 `enablePending`(언어별 같은 옵션)을 켜야 동작한다. 새 계약 내용은 그 제공자 브랜치에서 처음 성공한 검증이 게시될 때까지 "보류" 상태이고, 보류 중 불일치는 검증 작업 전체를 실패시키지 않는다(Pact 문서). 기능을 끈 기본 흐름에서는 검증 작업이 오류로 끝난다.

### 5. 배포 순서가 꼬였다

- 현상: 제공자를 먼저 배포했더니 운영에 있는 **옛 소비자 판**과 맞지 않았다.
- 원인: 최신 소비자 계약만 검증했다.
- 대처: `can-i-deploy`로 대상 환경의 실제 판들과의 검증 결과를 확인하고, 배포 뒤 `record-deployment`로 기록한다.

## 핵심 문장

- 소비자 주도 계약은 "소비자가 실제로 쓰는 요청·응답 예제"를 계약으로 삼아, 제공자 빌드에서 재생해 본다.
- 계약은 예제 + 매처다. 값이 아니라 모양(정수·문자열)을 비교하고, 응답의 추가 필드는 무시한다.
- 실험에서 필드 추가는 통과, 이름 변경은 `missing the following keys: name`, 타입 변경은 `Expected '1' (String) to be an integer`로 제공자 쪽에서 실패했다.
- 계약 테스트는 두 서비스를 함께 띄우지 않으므로 E2E보다 빠르고 원인 필드를 직접 짚는다. 대신 공개 API·제공자 기능·의미 변경은 다른 수단이 필요하다.
- `can-i-deploy`는 배포하려는 판과 대상 환경에 이미 있는 판들 사이의 검증 기록을 확인한다.

## 관련 주제·근거

- 선행
  - [08-integration-tests-real-dependencies](../08-integration-tests-real-dependencies/2-summary.md) — 실제 의존 하나와의 통합.
  - [api-design/07-versioning-and-compatibility](../../api-design/07-versioning-and-compatibility/2-summary.md).
  - [03-test-doubles](../03-test-doubles/2-summary.md). 더블이 낡는 문제.
- 후속·연결
  - [18-e2e-and-ui-testing](../18-e2e-and-ui-testing/2-summary.md) — 계약으로 줄이는 E2E.
  - [19-testing-in-production](../19-testing-in-production/2-summary.md) — 배포 뒤 검증.
  - [reliability/23-deployment-strategies](../../reliability/23-deployment-strategies/2-summary.md) — 신·구 공존 구간과 확장 배포.
  - [data-engineering/09-data-contracts-and-schema-registry](../../data-engineering/09-data-contracts-and-schema-registry/2-summary.md).
- 문서·글
  - Pact 문서 — How Pact works <https://docs.pact.io/getting_started/how_pact_works>, What is Pact good for <https://docs.pact.io/getting_started/what_is_pact_good_for>, Matching(Postel의 법칙) <https://docs.pact.io/getting_started/matching>, Can I Deploy <https://docs.pact.io/pact_broker/can_i_deploy>, Pending pacts <https://docs.pact.io/pact_broker/advanced_topics/pending_pacts>
  - Ian Robinson, "Consumer-Driven Contracts: A Service Evolution Pattern", 2006-06-12 <https://martinfowler.com/articles/consumerDrivenContracts.html>
  - Martin Fowler, "ContractTest", 2011-01-12 <https://martinfowler.com/bliki/ContractTest.html>
  - Pact JVM 4.7.5 — `au.com.dius.pact.consumer:junit5`, `au.com.dius.pact.provider:junit5`(Maven Central)
- 실험 목록
  - UserClientPactTest(소비자) → `target/pacts/order-service-user-service.json` 생성(V3, matchingRules `integer`·`type`).
  - UserProviderPactTest(제공자) — `-Dvariant=v1|add|rename|idstring`, 결과 OK·OK·missing keys: name·Expected '1' (String) to be an integer.
  - RuntimeBreakTest — 계약 없이 rename 제공자에 붙였을 때 `IllegalStateException: name missing`.
  - 환경: maven:3.9-eclipse-temurin-21 컨테이너(`--network none`, `pact_do_not_track=true`), JDK 21, JUnit 5.13.4, 2026-10-03.
