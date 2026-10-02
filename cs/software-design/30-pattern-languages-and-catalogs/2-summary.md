# software-design/30-pattern-languages-and-catalogs — 패턴의 형식·카탈로그 지형·패턴 언어 (허브) — 정리 (힌트)

## 해결하는 문제

패턴 이름은 대화를 짧게 해 준다("여긴 Strategy로"). 그런데 이름만 주고받으면 두 가지가 깨진다.

```text
 (1) 힘을 안 본다                         (2) 같은 이름, 다른 뜻
 "결제 수수료? Strategy로!"                A: "Repository 만들자"  (머릿속: 테이블마다 CRUD 클래스)
   → 인터페이스 + 구현 1개 + 팩토리         B: "Repository 만들자"  (머릿속: 애그리게이트 루트별 컬렉션)
   → 변형은 끝내 안 옴                      → 리뷰에서 서로 다른 것을 말한다
   → 간접 계층만 남음
```

- *패턴(pattern)*: 특정 맥락에서 반복되는 문제와, 그 문제를 이루는 힘들의 균형을 잡는 해법의 짝. 이름이 붙어 어휘가 된다.
- *힘(forces)*: 해법이 맞춰야 하는 서로 당기는 조건들(성능 vs 단순함, 유연성 vs 읽기 쉬움 등). Fowler는 패턴 작가들이 힘을 말하는 이유를 "그 패턴을 쓸 때와 쓰지 말 때(indications and contra-indications)를 탐색하는 방법"이라고 쓴다(「Writing Software Patterns」, 2006).

쉬운 예: 약 이름만 알고 먹는 것과 같다. "두통엔 이 약"만 외우고 금기(위장 질환이면 피할 것)를 안 보면 탈이 난다. 같은 상품명이 나라마다 다른 성분인 경우도 있다.\
똑같은 구조다.\
실무 예: 패턴 카탈로그의 "적용 조건·결과(consequences)" 칸을 건너뛰고 구조 그림만 베끼는 것. "Gateway"가 Fowler의 객체 패턴인지, API Gateway 서버인지 확인하지 않고 설계 리뷰를 하는 것.

이 노트는 **허브**다. 패턴의 형식과 카탈로그 지형을 정리하고, 카탈로그별로 이 저장소의 어느 노트가 그 패턴을 다루는지 역링크 표를 둔다. GoF 23개 자체는 [27-design-patterns-gof](../27-design-patterns-gof/2-summary.md)와 기존 [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md)(「우선순위」 표)에 있다.

## 동작·원리

### 1. 패턴의 형식 — 맥락·문제·힘·해법·결과

```text
 ┌ 이름 ─────────── 어휘가 된다 (명사구가 좋다 — Fowler)
 ├ 맥락(context) ── 어떤 상황에서
 ├ 문제(problem) ── 무엇이 어려운가
 ├ 힘(forces) ───── 서로 당기는 조건들   ← 건너뛰면 "문제 없는 곳에 패턴"
 ├ 해법(solution) ─ 힘의 균형을 잡는 구조
 └ 결과(consequences / resulting context) ─ 얻는 것과 잃는 것, 다음에 필요한 패턴
```

형식은 저자마다 다르다. Fowler는 저자마다 대개 자기 형식을 만든다고 쓰고, 널리 알려진 형식으로 Alexandrian·GOF·Portland·Coplien·POSA·P of EAA를 든다(「Writing Software Patterns」).

| 형식 | 칸(출처) |
|---|---|
| Alexandrian | 그림 → 맥락 문단 → ◆◆◆ → 굵은 문제 헤드라인 → 본문(근거) → 굵은 해법(지시문 형태) → 도식 → ◆◆◆ → 더 작은 패턴과의 연결 (Fowler가 『A Pattern Language』 서문을 인용. 인용문 자체에는 "Therefore"라는 말이 없다 — Fowler는 강조된 "therefore"를 Portland 형식의 특징으로 적는다) |
| GoF | Name·Intent·Also Known As·Motivation·Applicability·Structure·Participants·Collaborations·Consequences·Implementation·Sample Code·Known Uses·Related Patterns (Wikipedia 「Software design pattern」. Fowler의 GOF Form 목록은 Intent부터 Related Patterns까지 11칸 — 책 본문 미열람) |
| Coplien(canonical) | Problem·Context·Forces·Solution 등 머리 칸 + 추가 칸 (Fowler) |
| POSA | summary·example·context·problem·solution·structure·dynamics·implementation·example resolved·variants·known uses·consequences·see also (Fowler) |
| PoEAA | how it works·when to use it·examples (Fowler) |
| microservices.io | Context·Problem·Forces·Solution·Resulting context·Related patterns (API Gateway 페이지에서 확인) |

- DDD 레퍼런스(Evans, 2015)의 Repositories 항도 문제 서술 뒤 "Therefore:"로 해법을 여는 Alexandrian 형식이다.

### 2. 패턴 언어 — 패턴이 서로를 부른다

```text
 큰 패턴 ───(완성하려면 필요)───> 작은 패턴들
 API Gateway ──requires──> Microservice Architecture (이 패턴이 필요를 만든다)
             ──requires──> Service Discovery (client-side 또는 server-side)
             ──combines──> Circuit Breaker
 Saga ──builds on──> Compensating Transaction
```

- *패턴 언어(pattern language)*: 패턴들이 서로 선행·조합·대안 관계로 엮여, 한 패턴의 결과가 다음 패턴의 맥락이 되는 체계. Alexander 외 『A Pattern Language』(1977)가 253개 패턴으로 이 개념을 보였다("All 253 patterns together form a language" — 서문, Wikipedia 인용).
- Alexander는 패턴을 확정된 정답이 아닌 **가설**로 보았다(같은 책 서문 — Wikipedia 인용).
- Hohpe·Woolf 『Enterprise Integration Patterns』(2003)는 65개 패턴을 패턴 언어로 엮었다(enterpriseintegrationpatterns.com).
- microservices.io는 스스로를 "A pattern language for microservices"라고 부르고, 각 패턴 끝에 Related patterns를 둔다.
- Azure Architecture Center 「Cloud design patterns」에는 「Combine patterns」 절이 있다: Retry + Circuit Breaker, Queue-Based Load Leveling + Competing Consumers, Gateway Routing·Aggregation·Offloading을 한 게이트웨이 뒤에, Saga를 Compensating Transaction 위에.

### 3. 카탈로그 지형

```text
 1977 Alexander 『A Pattern Language』 (건축, 253)
   │
 1994 GoF 『Design Patterns』 (객체 설계 23)
   ├─ 1996 POSA1 Buschmann 외 (아키텍처·설계 패턴 시스템) … POSA5 2007 "On Patterns and Pattern Languages"
   ├─ 2002 Fowler 『PoEAA』 (엔터프라이즈 앱: 도메인 로직·데이터 소스·웹 표현·분산)
   ├─ 2003 Hohpe·Woolf 『EIP』 (메시징 통합 65)
   ├─ 2003 Evans 『DDD』 (도메인 모델 빌딩 블록: Entity·Value Object·Aggregate·Repository …)
   ├─ microservices.io Richardson (마이크로서비스 패턴 언어)
   └─ Azure Architecture Center (클라우드 설계 패턴, Well-Architected 기둥별 분류)
```

- POSA 1~5권의 연도(1996·2000·2004·2007·2007)는 Wikipedia 「Pattern-Oriented Software Architecture」. 5권 부제가 "On Patterns and Pattern Languages"다. 1권의 패턴 목록은 출판사 목차를 열지 못해 확인하지 못했다 [?].
- PoEAA는 2002년 Addison-Wesley 출간(Wikipedia 「Martin Fowler」 저서 목록). martinfowler.com 카탈로그 페이지에는 2003-03-05가 찍혀 있다(Gateway 페이지 하단). DDD 책 출간은 2003년(Wikipedia 「Domain-driven design」).

### 4. 같은 이름, 다른 뜻

| 이름 | 출처 A | 출처 B | 차이 |
|---|---|---|---|
| Repository | PoEAA: 도메인과 데이터 매핑 계층 사이를 중재하는, 컬렉션 같은 인터페이스. 데이터 매퍼 위에 질의 구성 코드를 모으는 층(martinfowler.com) | DDD 레퍼런스: **전역 접근이 필요한 애그리게이트 타입마다** 루트 객체 전체의 메모리 컬렉션 같은 환상을 주는 서비스. **직접 접근이 필요한 애그리게이트 루트에만** 둔다 | DDD는 단위(애그리게이트 루트)와 개수(필요한 것만)를 제한한다. Fowler 페이지도 DDD에 좋은 설명이 있다고 연결한다 — 같은 뿌리, 다른 강조 |
| Gateway | PoEAA: 외부 시스템·자원 접근을 감싸는 **객체**. 특수 API를 평범한 메서드 호출로 번역 | microservices.io API Gateway: 클라이언트 전체의 단일 진입점("the single entry point for all clients")인 **서버**. 라우팅·여러 서비스로 팬아웃·클라이언트별 API | 하나는 코드 안의 클래스, 하나는 배포 단위. Azure는 다시 Gateway Routing·Aggregation·Offloading 셋으로 나눈다 |

- 해석: 리뷰에서 패턴 이름이 나오면 "어느 카탈로그의 그것인가"를 한 번 묻는 것으로 오해 대부분을 줄일 수 있다.

### 실험 A: 힘 없이 빌린 패턴 vs 직접 쓴 코드 — 같은 변경 세 번

배송비(5만 원 이상 무료, 아니면 3천 원)를 두 판으로 만들었다.

- direct: `ShippingFee.of(...)` 정적 메서드 + `Checkout` + `Order`(3파일).
- patterned: "나중에 정책이 바뀔 수 있으니" `ShippingFeePolicy` 인터페이스 + `DefaultShippingFeePolicy` + `ShippingFeePolicyFactory` + `Checkout` + `Order`(5파일). 구현은 하나뿐이다.

그다음 같은 요구 세 개를 차례로 반영하고 `git diff --stat`을 쟀다.

```java
// patterned v0
interface ShippingFeePolicy { int fee(int amount); }
class DefaultShippingFeePolicy implements ShippingFeePolicy {
    public int fee(int amount) { return amount >= 50_000 ? 0 : 3_000; }
}
final class ShippingFeePolicyFactory {
    static ShippingFeePolicy create() { return new DefaultShippingFeePolicy(); }
}
// direct v0
final class ShippingFee {
    static int of(int amount) { return amount >= 50_000 ? 0 : 3_000; }
}
```

(실험, git 2.43.0 `LC_ALL=C`, 실행 확인 JDK 21.0.12 temurin `--cpus=2`, 2026-10-02 — `scratchpad/sd/30/e30/direct`, `.../patterned`)

```text
== v0 크기
  direct: 파일 3, 타입 3, 줄 11
  patterned: 파일 5, 타입 5, 줄 18
== 변경 1 (무게 할증)
  direct:  3 files changed, 7 insertions(+), 4 deletions(-) | 파일: Checkout.java Order.java ShippingFee.java 
  patterned:  4 files changed, 8 insertions(+), 5 deletions(-) | 파일: Checkout.java DefaultShippingFeePolicy.java Order.java ShippingFeePolicy.java 
== 변경 2 (회원 무료배송)
  direct:  3 files changed, 6 insertions(+), 5 deletions(-) | 수정: Checkout.java Order.java ShippingFee.java | 추가: 
    기존 규칙 파일(ShippingFee/DefaultShippingFeePolicy) 수정 여부: 1
  patterned:  4 files changed, 10 insertions(+), 5 deletions(-) | 수정: Checkout.java Order.java ShippingFeePolicyFactory.java | 추가: MemberShippingFeePolicy.java 
    기존 규칙 파일(ShippingFee/DefaultShippingFeePolicy) 수정 여부: 0
  direct 변경 3 (할증 2000→2500):  1 file changed, 1 insertion(+), 1 deletion(-) | ShippingFee.java 
  patterned 변경 3 (할증 2000→2500):  2 files changed, 2 insertions(+), 2 deletions(-) | DefaultShippingFeePolicy.java MemberShippingFeePolicy.java 
  direct: total(10000)=15500 total(60000)=60000 member(10000)=10000
  patterned: total(10000)=15500 total(60000)=60000 member(10000)=10000
```

- 변경 1(규칙 하나에 입력 추가): 인터페이스가 시그니처를 하나 더 들고 있어 patterned가 파일 하나를 더 고쳤다. 이 실험에서는 변형이 오기 전의 간접 계층이 비용만 더했다. 테스트 대역·의존 방향 역전 같은 다른 힘이 있으면 다르다(아래 적용 절).
- 변경 2(두 번째 정책 — 처음으로 "변형"이 왔다): patterned는 기존 규칙 클래스를 건드리지 않고 새 클래스를 더했다. direct는 기존 규칙 함수 안에 조건을 넣었다. 여기서 처음으로 패턴의 이점(기존 규칙 수정 0)이 보였다.
- 변경 3(공통 규칙 수정): patterned는 무게 할증 규칙이 두 전략 클래스에 **복제**돼 두 파일을 고쳤다. 축(회원 여부)과 공통 규칙(할증)을 구분하지 않고 전략으로 통째로 나눈 결과다. 공통 부분을 합성(데코레이터나 공용 함수)으로 뺐다면 한 곳이었을 것이다(해석).
- 두 판의 최종 결과값은 같았다(마지막 두 줄).
- 정리: 패턴의 값어치는 패턴이 다루는 **힘(이 경우 "정책 변형이 늘어난다")이 실제로 있을 때** 생긴다. 힘이 오기 전에 만든 구조는 변경 1처럼 비용이고, 힘의 모양을 잘못 짚으면 변경 3처럼 지식이 흩어진다. 판단 기준(두 번째 요구가 올 때 확장점을 만든다)은 [12-simple-design-and-yagni](../12-simple-design-and-yagni/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **패턴 관계 그래프** — 노드 = 패턴, 간선 = 선행(requires)·조합(combines)·대안(alternative). 선행은 방향 그래프, 조합·대안은 무방향으로 본다.
- **위상 정렬** — 선행 간선만으로 위상 정렬하면 "먼저 이해·도입할 패턴" 순서 후보가 나온다(Kahn 알고리즘: 들어오는 간선 0인 노드부터 꺼낸다).
- **이웃 조회** — "이 패턴을 쓰면 함께 보게 되는 것"은 한 노드의 인접 리스트다.
- **역색인(카탈로그 → 노트)** — 아래 「카탈로그 → leaf 역링크 표」가 그것이다.

### 실험 B: 출처가 있는 간선만으로 만든 작은 관계 그래프

Azure 「Combine patterns」, microservices.io API Gateway의 Related patterns, PoEAA Repository 페이지, 기존 GoF 노트의 「헷갈리는 쌍」에서 간선 13개를 옮겨 그래프를 만들고 질의했다.

```java
record Edge(String from, Rel rel, String to, String src) {}
static final List<Edge> E = List.of(
    new Edge("Retry", Rel.COMBINES, "Circuit Breaker", "Azure Combine patterns"),
    new Edge("Saga", Rel.REQUIRES, "Compensating Transaction", "Azure Combine patterns"),
    new Edge("API Gateway", Rel.REQUIRES, "Microservice Architecture", "microservices.io API gateway"),
    new Edge("Repository", Rel.REQUIRES, "Data Mapper", "PoEAA Repository"),
    new Edge("Strategy", Rel.ALTERNATIVE, "Template Method", "GoF (합성 vs 상속)"),
    /* ... 13개 */ );
```

(실험, JDK 21.0.12 temurin `--cpus=2`, 2026-10-02 — `scratchpad/sd/30/e30graph/PatternGraph.java`)

```text
== Circuit Breaker
  COMBINES    → Retry                    [Azure Combine patterns]
  COMBINES    → API Gateway              [microservices.io API gateway]
== API Gateway
  REQUIRES    → Microservice Architecture [microservices.io API gateway]
  REQUIRES    → Service Discovery        [microservices.io API gateway]
  COMBINES    → Circuit Breaker          [microservices.io API gateway]
== Strategy
  ALTERNATIVE → Template Method          [GoF (합성 vs 상속)]
  ALTERNATIVE → State                    [GoF (같은 구조, 누가 바꾸나)]
== 선행 관계 위상 정렬 (REQUIRES 간선만)
  노드 21개, Compensating Transaction(2) < Saga(18), Microservice Architecture(9) < API Gateway(20)
```

- 간선마다 출처를 달아 두면 "왜 이 둘이 같이 나오나"에 답할 수 있다.
- 위상 정렬 결과에서 선행 패턴이 앞에 왔다. 이 그래프는 시연용으로 작다 — 패턴 언어 전체가 아니다.

## 적용 — 풀어나가는 법

### 1. 패턴을 고를 때의 순서

1. **문제를 먼저 쓴다.** "어떤 변경이 어떤 이유로 얼마나 자주 오나"([04-decompose-by-change](../04-decompose-by-change/2-summary.md)). 문제 문장이 없으면 패턴을 고르지 않는다.
2. **힘을 적는다.** 카탈로그의 Applicability·Forces·Consequences 칸을 읽고, 우리 상황에서 그 힘이 실제로 있는지 표시한다.
3. **어느 카탈로그의 그 이름인지 적는다.** 설계 문서·PR에 "Repository (DDD, 애그리게이트 루트당)"처럼 출처를 붙인다.
4. **관계를 본다.** 이 패턴이 요구하는 선행 패턴, 함께 쓰는 패턴, 대안을 확인한다(실험 B처럼). 대안이 없다고 느껴지면 Fowler의 조언대로 "언제 이 패턴을 안 쓸까"를 생각해 본다.
5. **결과를 기록한다.** 고른 패턴과 거절한 대안을 ADR에 남긴다([47-architecture-decision-records](../47-architecture-decision-records/2-summary.md)).

### 2. 리뷰에서 쓰는 질문

```text
 □ 이 패턴이 해결하는 변경이 지금 있나, 예상인가?      (없으면: 인라인 후보)
 □ 구현이 하나뿐인 인터페이스·팩토리인가?              (Speculative Generality 신호)
 □ "Repository/Gateway/Service/Manager"가 어느 뜻인가?
 □ 공통 규칙이 여러 전략·하위 클래스에 복제됐나?        (실험 A 변경 3)
```

### 3. 진단

- 구현이 하나뿐인 인터페이스 찾기(Java, 대략 — 실험 A의 patterned v0 파일로 돌려 `ShippingFeePolicy`가 나오고, 두 번째 구현을 넣으면 안 나오는 것을 확인했다):

```bash
# 인터페이스 이름마다 "implements 이름" 등장 수를 세서 1인 것
for i in $(grep -rhoE 'interface [A-Z][A-Za-z0-9]+' src/main/java | awk '{print $2}' | sort -u); do
  n=$(grep -rlE "implements ([A-Za-z0-9, ]*\b)?$i\b" src/main/java | wc -l); [ "$n" -eq 1 ] && echo "$i"
done
```

- 테스트 대역(목)을 위해 둔 인터페이스는 구현이 하나여도 이유가 있다. 목록은 후보일 뿐이다.

## 장애 시나리오와 대처

### 1. 힘을 검토하지 않고 이름만 빌림 → 문제 없는 곳에 간접 계층 (⚠ 커리큘럼)

- 현상: 규칙 하나를 바꾸는데 인터페이스·구현·팩토리를 함께 고친다. 새로 온 사람이 규칙 위치를 찾는 데 오래 걸린다.
- 보이는 형태: 구현이 하나뿐인 인터페이스, `~Factory`가 한 종류만 만든다. 실험 A 변경 1에서 patterned가 파일 하나를 더 고쳤다(3 vs 4).
- 원인: 카탈로그의 Applicability·Forces를 보지 않고 구조 그림만 옮겼다.
- 대처: 인라인한다(구현 하나짜리 인터페이스·팩토리 제거). 변형이 실제로 두 번째 오면 그때 추출한다.

### 2. 같은 이름 다른 뜻 → 리뷰에서 서로 다른 것을 말함 (⚠ 커리큘럼)

- 현상: "Repository를 두자"에 합의했는데 한 사람은 테이블마다 CRUD 클래스를, 다른 사람은 애그리게이트 루트당 하나를 만든다. "Gateway"를 두고 한쪽은 클래스, 한쪽은 프록시 서버를 생각한다.
- 보이는 형태: 같은 이름의 클래스가 패키지마다 다른 책임을 가진다. 리뷰 코멘트가 엇갈린다.
- 원인: 패턴 이름은 카탈로그마다 정의가 다르다(4절 표).
- 대처: 설계 문서·코드 주석에 출처 카탈로그를 붙인다. 팀 용어집에 "우리 코드의 Repository = …"를 적는다.

### 3. 패턴으로 나눴는데 공통 지식이 복제됨

- 현상: 정책 하나를 고치면 전략 클래스 여러 개를 함께 고쳐야 한다.
- 보이는 형태: 실험 A 변경 3 — 같은 할증 숫자가 두 전략 클래스에 있어 두 파일 수정.
- 원인: 변하는 축(회원 여부)과 공통 규칙(할증)을 구분하지 않고 통째로 나눴다.
- 대처: 공통 규칙은 한 곳(공용 함수·데코레이터)으로 모으고, 전략에는 변하는 부분만 둔다.

### 4. 카탈로그를 정답집으로 씀

- 현상: "Azure 패턴에 있으니 넣자"로 Circuit Breaker·Retry·Bulkhead가 호출마다 겹겹이 붙는다.
- 보이는 형태: 설정값을 근거 없이 기본값으로 둔 회복 패턴이 여러 겹. 장애 때 재시도가 서로 곱해진다.
- 원인: Alexander가 말한 대로 패턴은 가설이다. 카탈로그는 후보를 줄 뿐 우리 맥락을 모른다.
- 대처: 패턴마다 해결할 실패 모드를 적고, 측정으로 설정을 정한다([reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md), [reliability/10-circuit-breaker](../../reliability/10-circuit-breaker/2-summary.md)).

## 핵심 문장

- 패턴은 맥락·문제·힘·해법·결과의 묶음이다. 힘(쓸 때와 쓰지 말 때)을 건너뛰면 문제 없는 곳에 간접 계층이 생긴다.
- 실험에서 구현 하나짜리 전략 + 팩토리는 첫 변경에서 파일을 하나 더 고치게 했고, 두 번째 정책이 왔을 때에야 기존 규칙 수정 0이라는 이점을 냈다.
- 같은 이름이 카탈로그마다 다른 뜻이다. PoEAA Repository와 DDD Repository, PoEAA Gateway와 API Gateway는 출처를 붙여 말한다.
- 패턴 언어는 패턴들이 선행·조합·대안으로 엮인 체계다. Alexander 253개, EIP 65개, microservices.io·Azure의 Related/Combine 절이 그 관계를 적는다.
- 카탈로그는 가설의 목록이다. 우리 맥락의 힘을 확인한 뒤에 고른다.

## 관련 주제·근거

### 카탈로그 → leaf 역링크 표

| 카탈로그 | 대표 패턴 | 이 저장소의 노트 |
|---|---|---|
| GoF (1994) | Strategy·State·Adapter·Chain of Responsibility·Proxy·Template Method | [27-design-patterns-gof](../27-design-patterns-gof/2-summary.md) · [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md) · [32 IoC(Template Method)](../32-inversion-of-control-and-framework-flow/2-summary.md) · [33 AOP(Proxy)](../33-aop-and-proxies/2-summary.md) · [34 체인(CoR)](../34-middleware-filter-interceptor-chains/2-summary.md) |
| POSA | Layers 등 아키텍처 패턴 [?] | [systems/architecture-styles](../../systems/architecture-styles/2-summary.md) · [37-architecture-styles](../37-architecture-styles/2-summary.md) · [42-ui-architecture-patterns](../42-ui-architecture-patterns/2-summary.md)(MVC 계보) |
| PoEAA (Fowler) | Data Mapper·Active Record·Repository·Gateway·Remote Facade·DTO·Separated Interface·Plugin | [database/25-data-source-patterns](../../database/25-data-source-patterns/2-summary.md) · [43-data-across-boundaries](../43-data-across-boundaries/2-summary.md) · [36-extension-points-and-plugins](../36-extension-points-and-plugins/2-summary.md) |
| EIP (Hohpe·Woolf) | 메시지 채널·라우터·변환기 | [distributed/19-message-types-channels-and-endpoints](../../distributed/19-message-types-channels-and-endpoints/2-summary.md) · [distributed/34-message-routing-and-transformation](../../distributed/34-message-routing-and-transformation/2-summary.md) |
| DDD (Evans) | Entity·Value Object·Aggregate·Repository | [19-immutability-and-value-objects](../19-immutability-and-value-objects/2-summary.md) · domain-modeling 커리큘럼 [repositories-and-factories](../../domain-modeling/curriculum.md) |
| microservices.io (Richardson) | Saga·Transactional outbox·API Gateway·Strangler Application | [distributed/15-saga](../../distributed/15-saga/2-summary.md) · [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md) · [45-monolith-vs-microservices](../45-monolith-vs-microservices/2-summary.md) · [50-legacy-migration-strangler-fig](../50-legacy-migration-strangler-fig/2-summary.md) |
| Azure Cloud Design Patterns | Retry·Circuit Breaker·Bulkhead·Event Sourcing·Sidecar·Deployment Stamps | [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md) · [reliability/10-circuit-breaker](../../reliability/10-circuit-breaker/2-summary.md) · [reliability/28-bulkhead](../../reliability/28-bulkhead/2-summary.md) · [distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md) · [reliability/50-sidecar-ambassador-and-service-mesh](../../reliability/50-sidecar-ambassador-and-service-mesh/2-summary.md) · [reliability/51-cells-stamps-and-blast-radius](../../reliability/51-cells-stamps-and-blast-radius/2-summary.md) |
| 안티패턴 | God Object·Big Ball of Mud | [31-antipatterns](../31-antipatterns/2-summary.md) |

- 선행: [27-design-patterns-gof](../27-design-patterns-gof/2-summary.md)
- 후속: [29-refactoring-to-patterns](../29-refactoring-to-patterns/2-summary.md) — 스멜에서 패턴 쪽으로, 패턴에서 멀어지기 · [12-simple-design-and-yagni](../12-simple-design-and-yagni/2-summary.md) — 확장점은 두 번째 요구가 올 때 · [47-architecture-decision-records](../47-architecture-decision-records/2-summary.md) — 고른 패턴과 거절한 대안 기록
- 글·문서
  - Martin Fowler, "Writing Software Patterns", 2006-08-01 — 형식(Alexandrian·Coplien·POSA·PoEAA), 힘의 역할 <https://martinfowler.com/articles/writingPatterns.html>
  - Christopher Alexander 외, 『A Pattern Language』, 1977 — 253 패턴, 패턴은 가설(Wikipedia 「A Pattern Language」 인용, 책 미열람) <https://en.wikipedia.org/wiki/A_Pattern_Language>
  - Wikipedia 「Software design pattern」(GoF 문서화 형식 칸) <https://en.wikipedia.org/wiki/Software_design_pattern> · 「Pattern-Oriented Software Architecture」(POSA 1~5권 연도) <https://en.wikipedia.org/wiki/Pattern-Oriented_Software_Architecture>
  - Martin Fowler, PoEAA 카탈로그 Repository·Gateway <https://martinfowler.com/eaaCatalog/repository.html> · <https://martinfowler.com/eaaCatalog/gateway.html>
  - Eric Evans, 『Domain-Driven Design Reference』(2015-03) Repositories <https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf>
  - Chris Richardson, microservices.io 「Pattern: API Gateway」·패턴 목록 <https://microservices.io/patterns/apigateway.html>
  - Gregor Hohpe·Bobby Woolf, Enterprise Integration Patterns 사이트(65 패턴) <https://www.enterpriseintegrationpatterns.com/>
  - Azure Architecture Center 「Cloud design patterns」의 「Combine patterns」 <https://learn.microsoft.com/en-us/azure/architecture/patterns/>
- 실험 목록
  - A 구현 하나짜리 Strategy + Factory vs 직접 코드, 같은 변경 3회의 `git diff --stat` — `scratchpad/sd/30/e30/` (git 2.43.0, 실행 확인 JDK 21.0.12 temurin `--cpus=2`)
  - B 출처 달린 패턴 관계 그래프·위상 정렬 — `scratchpad/sd/30/e30graph/PatternGraph.java` (JDK 21.0.12)
