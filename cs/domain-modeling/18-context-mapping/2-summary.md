# domain-modeling/18-context-mapping — 컨텍스트 매핑: 컨텍스트 사이 관계 9가지 — 정리 (힌트)

## 해결하는 문제

바운디드 컨텍스트(16번)를 나눴다. 이제 그 컨텍스트들이 서로 데이터를 주고받아야 한다.

```text
  카탈로그팀 ──상품 정보──> 주문팀 ──주문 정보──> 배송팀
      │
      └──상품 정보──> 검색팀

  질문: 카탈로그팀이 응답 필드 이름을 바꾸면 누가 알아야 하나?
        누가 누구에게 맞추나? 깨지면 누구 책임인가?
```

- 이 질문에 답이 없으면 상류 변경이 하류를 예고 없이 깨뜨린다(⚠ 커리큘럼).
- 기술(REST·Kafka)을 정해도 답은 안 나온다. 답은 **팀 사이의 힘 관계와 번역 방식**에 있다.

쉬운 예: 강을 낀 두 도시.
- 위쪽 도시가 강을 더럽히면 아래쪽 도시가 피해를 본다. 아래쪽이 뭘 하든 위쪽은 거의 영향이 없다.
- 아래쪽 도시가 고를 수 있는 것: 위쪽과 협정을 맺는다, 그냥 그 물을 쓴다, 정수장을 짓는다, 다른 수원을 찾는다.
- DDD Reference의 상류·하류 정의가 정확히 이 예를 든다.

똑같은 구조다.\
**컨텍스트마다 "누가 상류인가"와 "하류가 어떻게 받아들이나"를 정하고, 그 관계를 지도로 그린다.** 이것이 컨텍스트 맵이다.

- *상류-하류(upstream-downstream)*: 상류 그룹의 행동은 하류 프로젝트의 성패에 영향을 주지만, 하류의 행동은 상류에 큰 영향을 주지 않는 관계. 상류는 하류의 운명과 무관하게 성공할 수 있다(DDD Reference 2015 IV부 정의).
- *상호 의존(mutually dependent)*: 두 컨텍스트의 프로젝트가 **둘 다** 전달돼야 어느 쪽이든 성공으로 치는 상황(같은 곳).
- *자유(free)*: 다른 컨텍스트의 개발 방향·성패가 이쪽 전달에 거의 영향이 없는 상황(같은 곳).

## 동작·원리

### 1. 컨텍스트 맵 — 먼저 있는 그대로 그린다

Reference "Context Map"의 처방:
- 프로젝트에 있는 모델을 모두 찾아 각각의 바운디드 컨텍스트를 정한다. 객체지향이 아닌 하위 시스템의 암묵적 모델도 포함한다.
- 컨텍스트마다 이름을 붙이고, 그 이름을 유비쿼터스 언어의 일부로 만든다.
- 모델 사이 접점을 적는다. 통신마다 명시적 번역, 공유하는 것, 격리 장치, 영향력의 수준을 드러낸다.
- **지금 지형을 그린다. 바꾸는 것은 나중에 한다.**

```text
  컨텍스트 맵 표기 예 (U = upstream, D = downstream)

   ┌──────────┐ U          D ┌──────────┐ U   PL/OHS   D ┌──────────┐
   │ Catalog  │──────ACL────>│ Ordering │──────────────>│ Shipping │
   └──────────┘              └──────────┘               └────┬─────┘
        │ U                        │ U    PL/OHS              │ SK(공유 커널)
        │ CF(순응자)                └──────────> Invoicing      │
        ▼ D                                                ┌──┴───────┐
   ┌──────────┐                                            │ Tracking │
   │  Search  │                                            └──────────┘
   └──────────┘
```

- 선 하나 = 두 컨텍스트 사이 관계 하나. 선 위의 표시가 관계 패턴이다.
- 표기는 표준이 정해져 있지 않다. 위의 U/D·약어 표기는 흔히 쓰이는 관례(DDD Crew "Context Mapping" 시트 등)를 따랐다.

### 2. 관계 패턴 9가지 (DDD Reference 2015 IV부)

```text
  팀 관계               패턴                       하류가 하는 일
  ────────────────     ─────────────────────       ──────────────────────────────
  상호 의존            Partnership                 함께 계획·함께 통합
                      Shared Kernel               작은 공유 모델을 같이 소유
  상류 → 하류          Customer/Supplier           하류 우선순위를 상류 계획에 반영
                      Conformist                  상류 모델을 그대로 따른다
                      Anticorruption Layer        번역 계층으로 자기 모델을 지킨다
                      Open-host Service           (상류가) 여러 하류용 공개 프로토콜 제공
                      Published Language          문서화된 공통 교환 언어
  자유                 Separate Ways               연결하지 않는다
  (경계 없음)          Big Ball of Mud             엉킨 영역 전체에 선을 긋고 격리
```

- 이 표의 "팀 관계" 묶음은 Reference의 세 정의(상호 의존·상류-하류·자유)에 패턴을 배치한 정리다(Reference는 패턴을 관계별로 묶지 않는다). DDD Crew 시트도 "세 팀 관계 + 9개 패턴"을 함께 정리하지만, 패턴을 관계 아래에 나눠 넣지는 않는다. Khononov 『Learning DDD』 4장은 협력(Partnership·Shared Kernel)·고객-공급자(Conformist·ACL·OHS)·Separate Ways로 묶는다(2차 정리로 확인).
- Reference 목차에는 Partnership·Big Ball of Mud(그리고 Domain Events)에 `*` 표시가 있다. 목차 끝 각주가 그 뜻을 "New term introduced since the 2004 book"(2004년 책 이후 새로 도입된 용어)이라고 적는다. 즉 이 둘은 『DDD』 원서에 패턴으로 없던 이름이다.

패턴별 요지(Reference 원문의 "Therefore" 처방 요약):

| 패턴 | 처방 | 비용·위험 |
|---|---|---|
| **Partnership** | 한쪽 실패가 양쪽 전달 실패가 되는 두 팀이 파트너십을 맺는다. 계획을 함께 세우고 통합을 함께 관리한다. 서로 의존하는 기능은 같은 릴리스에 맞춘다 | 조율 비용. 상대 모델을 자세히 알 필요는 대개 없지만 계획은 맞춰야 한다 |
| **Shared Kernel** | 두 팀이 공유하기로 합의한 모델 일부를 명시적 경계로 지정한다. **작게 유지**한다. 그 부분의 코드·DB 설계도 포함한다. 상대 팀과 상의 없이 바꾸지 않는다 | 매우 밀접한 의존. 커지면 공유 모델 문제(16번)로 돌아간다 |
| **Customer/Supplier** | 하류의 우선순위를 상류 계획에 반영한다. 하류 요구를 협상해 일정에 넣는다. 함께 만든 자동 인수 테스트를 상류 CI에 넣어, 상류가 하류 부작용 걱정 없이 바꿀 수 있게 한다 | 상류가 실제로 협조해야 성립 |
| **Conformist** | 상류가 하류를 도울 동기가 없을 때, 상류 모델을 그대로 따라 번역 복잡도를 없앤다 | 하류 설계가 상류에 묶인다. 상류 변경이 그대로 번진다 |
| **Anticorruption Layer** | 하류가 상류 기능을 자기 도메인 모델 언어로 쓰게 하는 격리 계층을 만든다. 상류의 기존 인터페이스를 쓰고, 안에서 양방향으로 번역한다 | 번역 계층 유지 비용(19번) |
| **Open-host Service** | 많은 하류와 통합해야 하는 상류가 하위 시스템을 서비스 집합으로 여는 프로토콜을 정의·공개한다. 한 팀만의 특이 요구는 일회용 번역기로 처리해 공용 프로토콜을 단순하게 둔다 | 제공자가 상류가 된다. 하류는 일부는 순응, 일부는 ACL을 둔다 |
| **Published Language** | 필요한 도메인 정보를 표현할 수 있는, 잘 문서화된 공유 언어를 교환 매체로 쓴다. 기존 모델을 직접 교환 언어로 쓰면 그 모델이 얼어붙는다 | 언어 자체의 버전 관리. OHS와 자주 함께 쓴다 |
| **Separate Ways** | 두 기능 묶음 사이에 의미 있는 관계가 없으면 완전히 떼어 낸다. 통합은 늘 비싸고, 이득이 작을 때가 있다 | 기능 중복이 생길 수 있다 |
| **Big Ball of Mud** | 경계가 없는 엉킨 영역 전체에 선을 긋고 "진흙 덩어리"로 지정한다. 그 안에서 정교한 모델링을 시도하지 않는다. 다른 컨텍스트로 번지는 것을 경계한다 | 그 안은 포기. 밖으로 새지 않게 막는 것이 목표 |

### 3. 관계를 고르는 흐름

```text
  두 컨텍스트가 통합해야 하나? ──아니오──> Separate Ways
          │ 예
  둘 다 성공해야 성공인가(상호 의존)? ──예──> Partnership (공유가 필요하면 작은 Shared Kernel)
          │ 아니오 (상류-하류)
  상류가 하류 요구를 들어주나? ──예──> Customer/Supplier (+ 계약 테스트를 상류 CI에)
          │ 아니오
  상류 모델이 쓸 만하고 우리 핵심과 충돌이 적나? ──예──> Conformist
          │ 아니오
                                         Anticorruption Layer
  (상류 쪽에서 하류가 많다면) ──> Open-host Service + Published Language
```

- 이 흐름은 Reference 각 패턴의 "When ..." 조건을 이어 붙인 정리다. Reference가 직접 순서도를 주지는 않는다.
- 하류 컨텍스트가 핵심 서브도메인(17번)이면 순응자 선택을 특히 경계한다. 상류 모델이 핵심 모델을 결정하게 된다.

### 실험: 관계가 파급을 정한다 — 컨텍스트 그래프와 계약 테스트

두 가지를 돌렸다.
1. 맵을 그래프로 두고 "Catalog 모델 변경이 어디까지 번지나"를 너비 우선 탐색으로 센다. 규칙(이 실험의 가정): 순응·공유 커널 선은 모델 변경을 그대로 넘기고, ACL·공개 언어 선은 번역 지점에서 멈춘다.
2. 상류가 `price → unitPrice`로 필드 이름을 바꿨을 때, 계약이 없는 순응자 하류와 Customer/Supplier 계약 테스트를 비교한다.

```java
static boolean propagates(Rel r){ return r==Rel.CONFORMIST || r==Rel.SHARED_KERNEL; }
// BFS: 순응·공유 커널이면 하류도 "모델 변경" → 그 하류의 하류로 계속, ACL·PL이면 "번역 계층만 수정"에서 멈춤
// 하류 Ordering(순응자): 상류 JSON을 그대로 읽는다
long total = ((Number)resp.getOrDefault("price",0)).longValue() * 3;
// Customer/Supplier: 하류가 쓴 계약(필요 필드)을 상류 CI에서 돈다
List<String> contract=List.of("sku","price");
```

(실험, JDK 21.0.12 temurin `--cpus=2`, 2026-10-03 — `Map18.java`)

```text
[1] Catalog 모델 변경의 파급
  모두 순응(관계 미정의): {Ordering=모델 변경(CONFORMIST), Search=모델 변경(CONFORMIST), Shipping=모델 변경(CONFORMIST), Invoicing=모델 변경(CONFORMIST), Tracking=모델 변경(CONFORMIST)}
  관계를 고른 맵        : {Ordering=번역 계층만 수정(ACL), Search=모델 변경(CONFORMIST)}
  관계를 고른 맵, Shipping 변경: {Tracking=모델 변경(SHARED_KERNEL)}
[2] 상류 Catalog v2가 price → unitPrice로 이름을 바꿨다
  하류 주문 합계(수량 3) = 36000  ← 응답 [sku, price]
  하류 주문 합계(수량 3) = 0  ← 응답 [sku, unitPrice]
  상류 CI 계약 테스트 v1: PASS
  상류 CI 계약 테스트 v2: FAIL missing=[price]
```

관찰:
1. 모두 순응이면 Catalog 변경이 5개 하류 컨텍스트 전부에 번진다. 관계를 고른 맵에서는 2개(Ordering은 번역기만, Search는 순응이라 모델까지)에서 멈췄다.
2. 같은 맵에서 Shipping을 바꾸면 공유 커널로 묶인 Tracking만 영향을 받는다. 공유 커널은 "작게 유지"해야 하는 이유가 여기 있다.
3. 관계 미정의 하류는 필드 이름 변경 뒤 **에러 없이 합계 0**을 냈다. 기본값(`getOrDefault`)이 실패를 숨겼다.
4. 같은 변경을 하류 계약 테스트가 상류 CI에서 `FAIL missing=[price]`로 잡았다. 릴리스 전에 상류가 안다.
5. 응답의 키 출력 순서(`[sku, price]`)는 `Map.of`의 반복 순서라 실행마다 달라질 수 있다. 결론에는 영향이 없다.

해석: [1]은 가정한 규칙 위의 계산이다. "ACL이면 번역기만 고친다"는 19번 실험에서 실제 diff로 보인다. [2]는 Reference "Customer/Supplier"의 "함께 만든 자동 인수 테스트를 상류 CI에" 처방이 무엇을 막는지 보인다.

## 쓰이는 자료구조·알고리즘

- **방향 그래프(컨텍스트 그래프)** — 노드 = 컨텍스트, 간선 = 상류→하류 + 관계 라벨. 🔧 커리큘럼의 "컨텍스트 그래프"다.
- **너비 우선 탐색(BFS)으로 영향 범위 계산** — 변경된 노드에서 시작해 "번지는" 간선만 따라간다. 시간 O(V+E). 실험 [1]의 `impact`.
- **계약 = 필요 필드 집합** — 하류 계약은 "내가 읽는 필드" 집합이고, 검사는 응답 키 집합과의 차집합(`contract − response.keys`)이다. 실험 [2]의 `missing`. 실무 도구(Pact 등)는 형식·값 예시까지 검사한다.
- **버전 붙은 공개 언어(스키마)** — Published Language는 실무에서 스키마 + 버전 + 호환 규칙(예: 필드 추가만 허용)으로 운영된다. 경계 번역기와 공용 모델 범위는 [distributed/34-message-routing-and-transformation](../../distributed/34-message-routing-and-transformation/2-summary.md), 하위 호환 규칙은 api-design `07-versioning-and-compatibility`(미작성, [api-design/curriculum](../../api-design/curriculum.md)).

## 적용 — 풀어나가는 법

### 1. 순서

1. **있는 그대로 그린다.** 컨텍스트와 연결을 모두 적는다. 레거시·외부 SaaS도 컨텍스트다(Reference: 비객체지향 하위 시스템의 암묵적 모델도 포함).
2. **선마다 방향을 적는다.** 누가 상류인가. 상호 의존이면 표시한다.
3. **선마다 현재 패턴을 적는다.** 대개 "아무도 안 정함 = 사실상 순응"이 많다.
4. **위험한 선을 찾는다.** 핵심 컨텍스트가 순응하는 선, 계약 없는 상류-하류 선, 커지는 공유 커널.
5. **바꿀 선을 고른다.** 고객/공급자 협상, ACL 도입, OHS+PL로 승격.
6. **맵을 저장소에 둔다.** 그림 + 표(상류, 하류, 패턴, 계약 위치, 담당자).

### 2. 코드 — 하류 계약을 상류 CI에서 돈다 (Java, JUnit 5)

```java
// 하류(Ordering)가 작성해 상류(Catalog) 저장소에 넣는 계약 테스트 — Customer/Supplier
class OrderingContractTest {
    // 하류가 실제로 읽는 필드만 적는다. 나머지 필드는 상류가 자유롭게 바꿔도 된다
    static final Set<String> REQUIRED = Set.of("sku", "price", "currency");

    @Test void productResponseHasFieldsOrderingReads() throws Exception {
        JsonNode body = new ObjectMapper().readTree(catalogApi.get("/products/A-1"));
        Set<String> missing = new TreeSet<>(REQUIRED);
        body.fieldNames().forEachRemaining(missing::remove);
        assertTrue(missing.isEmpty(), "Ordering이 읽는 필드가 사라짐: " + missing);
    }
}
```

- Ian Robinson의 "Consumer-Driven Contracts"(2006)가 이 방식의 원형이다. 제공자 계약이 소비자 기대에서 나오고, 제공자는 경계 밖에서 온 의무를 진다.
- 하류 코드에서 `getOrDefault(..., 0)`처럼 **없는 필드를 기본값으로 덮는 코드를 금지**한다. 실험 [2]의 "합계 0"이 그 결과다. 없으면 예외로 드러낸다.

### 3. 진단 — 맵에 없는 의존 찾기

```bash
# 우리 컨텍스트 코드가 다른 컨텍스트의 내부 패키지를 import하는지 — 맵에 없는 순응 관계의 흔적
grep -rn "^import com\.example\.\(catalog\|billing\)\.internal\." src/ordering/ | head
```

- 다른 컨텍스트 내부 패키지를 import하면 사실상 순응자다. 맵에 그 선이 있는지, 의도한 관계인지 확인한다.

## 장애 시나리오와 대처

### 1. 관계 미정의 → 상류 변경이 하류를 예고 없이 파손 (⚠ 커리큘럼)

- 현상: 상류 팀이 응답 필드 이름을 바꿔 배포했다. 하류 주문 합계가 0원으로 찍힌다.
- 보이는 형태: 에러 로그가 없다. 지표상 주문 금액 합계·결제 금액이 급락한다. 고객 문의로 처음 안다(실험 [2]의 `합계 = 0`).
- 원인: 두 컨텍스트 사이 관계를 아무도 정하지 않았다. 하류는 사실상 순응자인데 상류는 그것을 모른다. 하류는 없는 필드를 기본값으로 덮었다.
- 대처
  - 당장: 상류가 옛 필드를 되살리거나(두 필드 병행), 하류가 새 필드를 읽게 고친다.
  - 근본: 관계를 정한다. 고객/공급자라면 하류 계약 테스트를 상류 CI에 넣는다(실험 [2]의 `FAIL missing=[price]`). 협조가 안 되면 하류가 ACL을 두고 번역 실패를 예외로 드러낸다(19번).

### 2. 공유 커널이 커져 공유 모델이 됐다

- 현상: "작은 공통 모듈"에 클래스가 계속 늘어, 두 팀의 거의 모든 변경이 서로의 승인을 기다린다.
- 보이는 형태: 공유 모듈의 PR 리드타임이 길다. 변경마다 양 팀 테스트가 깨진다.
- 원인: Reference의 "Keep this kernel small"을 지키지 않았다.
- 대처: 공유 커널에 들어갈 기준(정말 두 팀이 같은 뜻으로 쓰는가)을 정하고, 한쪽만 쓰는 것은 각자 컨텍스트로 돌려보낸다. 공유 커널 변경은 상대 팀과 상의 후에만 한다.

### 3. 핵심 컨텍스트가 순응자다

- 현상: 핵심 업무 규칙 이름·구조가 외부 ERP·PG의 필드 이름을 그대로 닮아 있다.
- 보이는 형태: 도메인 코드에 `resCd`, `trdDt` 같은 외부 약어가 퍼져 있다. 외부 버전 업그레이드 때 핵심 코드가 대량으로 바뀐다.
- 원인: 상류가 협조하지 않는 상황에서 번역 비용을 아끼려고 순응을 골랐다(또는 고른 적 없이 그렇게 됐다).
- 대처: ACL을 도입한다(19번). Reference도 레거시 상류 모델은 대개 약해서 순응하기 어렵다고 적는다.

### 4. 상호 의존인데 따로 계획한다

- 현상: 두 팀이 서로의 기능이 있어야 출시할 수 있는데 일정을 따로 잡는다. 통합 직전에 인터페이스가 안 맞는다.
- 보이는 형태: 출시가 한쪽 일정에 끌려 밀린다. 통합 단계에서 큰 재작업.
- 원인: 상호 의존 관계를 상류-하류처럼 다뤘다.
- 대처: Partnership으로 바꾼다. 계획을 함께 세우고, 서로 의존하는 기능을 같은 릴리스에 맞추며, 인터페이스 테스트를 상대 CI에 넣는다(Reference "Partnership").

## 핵심 문장

1. 컨텍스트 맵은 컨텍스트들과 그 사이 관계(누가 상류인가, 하류가 어떻게 받나)를 있는 그대로 그린 지도다.
2. 관계는 기술이 아니라 팀 사이의 힘과 협조에서 정해진다 — 상호 의존, 상류-하류, 자유.
3. 순응은 번역 비용을 없애는 대신 상류 변경을 그대로 받는다. ACL·공개 언어는 번역 지점에서 파급을 멈춘다.
4. 고객/공급자 관계라면 하류 계약 테스트를 상류 CI에 넣는다. 그러면 필드 이름 변경이 릴리스 전에 잡힌다(실험).
5. 없는 필드를 기본값으로 덮는 하류 코드는 계약 파손을 "합계 0" 같은 조용한 데이터 오류로 바꾼다.

## 관련 주제·근거

- 선행
  - [16-bounded-contexts](../16-bounded-contexts/2-summary.md) — 매핑할 대상
- 후속·연결
  - [17-subdomains](../17-subdomains/2-summary.md) — 핵심 컨텍스트의 순응을 경계하는 이유
  - [19-anti-corruption-layer](../19-anti-corruption-layer/2-summary.md) — ACL 구현과 실험
  - [20-event-storming](../20-event-storming/2-summary.md) — 맵의 재료(경계 후보) 찾기
  - [09-domain-events](../09-domain-events/2-summary.md) — 공개 언어로서의 이벤트
  - [distributed/19-message-types-channels-and-endpoints](../../distributed/19-message-types-channels-and-endpoints/2-summary.md) — 메시지 채널(OHS·PL의 전달 수단)
  - [distributed/34-message-routing-and-transformation](../../distributed/34-message-routing-and-transformation/2-summary.md) — 메시지 번역기
  - [software-design/45-monolith-vs-microservices](../../software-design/45-monolith-vs-microservices/2-summary.md) — 계약 변경의 배포 비용
  - [systems/architecture-styles](../../systems/architecture-styles/2-summary.md) — 콘웨이 법칙(팀 구조와 시스템 구조)
- 글·문서
  - Eric Evans, 『Domain-Driven Design Reference』(2015) IV부 Context Mapping for Strategic Design — 정의(upstream-downstream, mutually dependent, free), "Context Map"과 패턴 9개 <https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf>
  - Eric Evans, 『Domain-Driven Design』 14장 Maintaining Model Integrity — 장 제목은 2차 목차로 확인
  - Vaughn Vernon, 『Implementing Domain-Driven Design』 3장 Context Maps — 목차로 확인
  - Vlad Khononov, 『Learning Domain-Driven Design』 4장 Integrating Bounded Contexts — 장 제목·묶음은 검색 요약·2차 정리로 확인 [?]
  - DDD Crew, "Context Mapping"(라이선스 표기가 둘이다 — README는 CC BY 4.0, 저장소 `LICENCE.md` 파일은 CC BY-SA 4.0. 2026-10-03 확인) <https://github.com/ddd-crew/context-mapping>
  - Ian Robinson, "Consumer-Driven Contracts: A Service Evolution Pattern", 2006-06-12 <https://martinfowler.com/articles/consumerDrivenContracts.html>
  - Melvin Conway, "How Do Committees Invent?", Datamation 1968-04 <https://www.melconway.com/Home/Conways_Law.html>
- 실험 목록
  - 컨텍스트 그래프 BFS(관계 라벨별 파급 규칙 가정) + 필드 이름 변경 시 순응 하류의 합계 0 vs 계약 테스트 FAIL — `scratchpad/dm/16/e18/Map18.java`, JDK 21.0.12 temurin `--cpus=2 --network none`
