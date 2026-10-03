# domain-modeling/19-anti-corruption-layer — 부패 방지 계층(ACL): 외부 모델 번역 계층 — 정리 (힌트)

## 해결하는 문제

우리 결제 도메인이 외부 PG(결제 대행사) SDK를 쓴다. PG 응답은 이렇게 생겼다.

```text
  PG 응답 (우리가 못 고친다)
  { resCd: "0000", amt: "12,000", tid: "T1" }
     │        │          └ 거래 ID
     │        └ 금액이 쉼표 붙은 문자열
     └ "0000" = 성공, 그 밖은 실패 코드

  ACL이 없으면 우리 코드 곳곳이 이렇게 된다
  PaymentService : if ("0000".equals(r.resCd)) ...
  RefundService  : if ("0000".equals(p.raw.resCd)) ...
  Settlement     : Long.parseLong(p.raw.amt.replace(",", "")) ...
```

- 외부 모델의 이름(`resCd`)·코드값(`"0000"`)·형식(쉼표 문자열)이 우리 도메인 코드에 퍼진다.
- 그러면 PG가 형식을 바꿀 때 우리 코드 여러 곳이 같이 바뀐다. 한 곳을 놓치면 조용히 틀린다(아래 실험).
- DDD Reference는 이렇게 적는다. 상류 시스템과의 큰 인터페이스는 결국 하류 모델의 의도를 압도해, 하류 모델이 상류 모델을 닮도록 즉흥적으로 고쳐지게 만든다("Anticorruption Layer").

쉬운 예: 해외 여행의 통역사.
- 내가 현지 말을 몇 마디씩 섞어 쓰기 시작하면, 내 말이 이상해지고 현지 말이 바뀔 때마다 나도 바꿔야 한다.
- 통역사 한 명을 두면 나는 내 말만 쓴다. 현지 말이 바뀌면 통역사만 새로 배운다.

똑같은 구조다.\
**외부 모델과 우리 모델 사이에 번역 계층 하나를 두고, 외부의 말은 그 안에서만 쓴다.**

- *부패 방지 계층(Anticorruption Layer, ACL)*: 하류 클라이언트가 상류 시스템의 기능을 **자기 도메인 모델의 말로** 쓸 수 있게 해 주는 격리 계층. 상류의 기존 인터페이스를 그대로 쓰고(상류 수정은 거의 없다), 안에서 필요한 방향으로 두 모델 사이를 번역한다(DDD Reference 2015 "Anticorruption Layer").

실무 예:
- 레거시 ERP·외부 PG·택배사 API·공공 데이터 API와의 통합.
- 단계적 이전(스트랭글러 피그) 중 신·구 시스템이 서로 부를 때. 이 경우는 [software-design/50](../../software-design/50-legacy-migration-strangler-fig/2-summary.md) §5에 기초가 있다(Azure 문서 근거). 이 노트는 그 위에 내부 구조·실패 처리·실험을 더한다.

## 동작·원리

### 1. 위치 — 하류가 만들고, 하류 안에 둔다

```text
 ┌──────────── 우리 컨텍스트(하류) ───────────────────────┐
 │                                                        │      ┌──── 외부(상류) ────┐
 │  도메인 모델                     ACL                    │      │                    │
 │  Payment{approved, amount}  ◄─[번역기]◄─[어댑터]◄─[퍼사드]─────│  PG SDK / API      │
 │  PaymentGateway(포트)  ─────►                          ──────►│  resCd, amt, tid   │
 │      ↑ 우리 말만 쓴다          ↑ 외부 말은 여기 안에서만      │      │                    │
 └────────────────────────────────────────────────────────┘      └────────────────────┘
```

- ACL은 **하류의 책임**이다. Reference는 "하류 클라이언트로서" 만들라고 적는다. 상류 수정은 거의 또는 전혀 요구하지 않는다.
- 번역은 한 방향이나 양방향이다. 요청(우리 → 외부)과 응답(외부 → 우리)을 모두 번역할 수 있다.
- Azure 아키텍처 센터 설명도 같다. 하위 시스템 A와 ACL 사이 통신은 늘 A의 데이터 모델을 쓰고, ACL에서 B로 가는 호출은 B의 모델을 따른다. ACL은 애플리케이션 안의 구성 요소로도, 독립 서비스로도 둘 수 있다.

### 2. 안쪽 구조 — 퍼사드·어댑터·번역기

| 부품 | 하는 일 |
|---|---|
| 퍼사드(Facade) | 외부 시스템의 큰 인터페이스를 우리가 쓰는 부분만으로 좁혀 감싼다. 외부 말을 쓴다 |
| 어댑터(Adapter) | 우리 쪽 인터페이스(포트)를 구현하고, 호출을 퍼사드로 넘긴다 |
| 번역기(Translator) | 외부 객체·코드값 ↔ 우리 도메인 객체. 순수 함수로 두기 좋다 |

- Evans 『DDD』 14장은 ACL을 "퍼사드·어댑터(둘 다 GoF)와 번역기(translators)의 조합"으로 짜는 것을 한 가지 방식("One way of organizing")으로 제시한다(원문 문장 "a combination of FACADES, ADAPTERS ..., and translators"는 Stack Overflow 답변 등의 인용으로 확인 — 원서는 열지 못했다). 퍼사드는 상류 쪽 말로 외부 복잡성을 감추고, 어댑터는 퍼사드의 말과 ACL 인터페이스(하류의 말) 사이를 잇는다(2차 정리, Software Architecture wiki). 위 표의 번역기는 그 translators 자리다.
- 작은 통합이면 셋을 클래스 하나로 합쳐도 된다. 아래 실험의 `PgTranslator`가 그렇다.

### 3. 번역할 때 지킬 것

```text
  외부 값                    번역 결과
  ───────────────           ─────────────────────────────
  resCd "0000"           →  approved = true
  resCd "9999"           →  approved = false (알려진 거절)
  resCd "00" (처음 봄)    →  예외: UNKNOWN_PG_CODE   ← 모르면 조용히 넘기지 않는다
  amt "12,000"           →  amount = 12000 (원)
```

1. **모르는 값은 실패로 드러낸다.** `default -> 실패`로 덮으면 새 성공 코드가 "실패"로 분류된다(실험 1단계).
2. **업무 규칙을 넣지 않는다.** Azure 문서: 의미 차이를 번역하는 데 집중하고, 비즈니스 규칙이나 오케스트레이션을 ACL에 넣지 말라.
3. **신뢰 경계로 다룬다.** Azure 문서: 신뢰 수준이 다른 시스템 사이이므로 입력 검증·정제를 이 경계에서 고려하라.
4. **관측 가능하게 한다.** Azure 문서: 번역 실패를 진단할 수 있게 상관 ID·구조화 로그를 계획하라.

### 4. 비용 — ACL이 손해인 경우

Azure 문서가 드는 고려점:
- 두 시스템 사이 호출에 지연이 더해진다.
- 관리·유지할 서비스가 하나 는다(독립 서비스로 둘 때).
- 확장 방식을 따로 생각해야 한다.
- 이전 전략의 일부라면, 영구로 둘지 이전이 끝나면 걷어 낼지 정한다.
- 패턴이 맞지 않는 경우: 두 시스템 사이에 의미 차이가 크지 않을 때.

### 실험: PG 응답 형식 변경 — ACL 없음 vs ACL

같은 결제·환불·정산 기능을 두 설계로 짰다.
- ACL 없음: `Payment`가 외부 응답(`raw`)을 들고 있고, 세 서비스가 `resCd`·`amt`를 직접 읽는다.
- ACL: `PgTranslator` 하나가 외부 응답을 `Payment{approved, amount, pgTxId}`로 바꾼다. 나머지는 도메인 필드만 읽는다.

외부 변경(PG v2): 성공 코드 `"0000"` → `"00"`, 금액 `"12,000"` → `"12000"`.

```java
// ACL 쪽 번역기 — 모르는 코드는 예외
switch (r.resCd) {
  case "0000" -> { p.approved = true; p.amount = Long.parseLong(r.amt.replace(",", "")); }
  case "9999" -> p.approved = false;
  default -> throw new IllegalStateException("UNKNOWN_PG_CODE resCd=" + r.resCd + " tid=" + r.tid);
}
// ACL 없음 쪽 — 세 파일에 흩어진 같은 해석
p.approved = "0000".equals(r.resCd);                       // PaymentService
return "0000".equals(p.raw.resCd);                         // RefundService
if ("0000".equals(p.raw.resCd)) s += Long.parseLong(...);  // Settlement
```

테스트 4개: 결제 승인, 승인 금액 12000, 환불 가능, 정산 합계 24000.

(실험, JDK 21.0.12 temurin `--cpus=2`, git 2.43.0, 2026-10-03 — `run.sh`, 출력 발췌)

```text
=== noacl: PG v2, 우리 코드 그대로
FAIL 결제 승인
FAIL 승인 금액 12000
FAIL 환불 가능
FAIL 정산 합계 24000
failures=4
=== noacl: 맞춘 뒤 diff(우리 코드)
 src/payment/PaymentService.java | 2 +-
 src/payment/RefundService.java  | 2 +-
 src/payment/Settlement.java     | 2 +-
 3 files changed, 3 insertions(+), 3 deletions(-)
...
failures=0
=== acl: PG v2, 우리 코드 그대로
Exception in thread "main" java.lang.IllegalStateException: UNKNOWN_PG_CODE resCd=00 tid=T1
	at payment.PgTranslator.toDomain(PgTranslator.java:9)
	at payment.PaymentService.approve(PaymentService.java:2)
=== acl: 맞춘 뒤 diff(우리 코드)
 src/payment/PgTranslator.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
...
failures=0
=== 외부 모델 참조 위치 수(import/필드 접근)
noacl: 4 files -> PaymentService.java Payment.java RefundService.java Settlement.java 
acl: 1 files -> PgTranslator.java 
=== ACL 비용: 번역기 줄 수
11
```

관찰:
1. ACL 없음: PG v2 뒤 우리 코드를 안 바꾸면 테스트 4개가 모두 실패했다. 운영이라면 **PG는 승인했는데 우리는 실패로 기록**한다. 예외도 로그도 없다. `"0000".equals(...)`가 새 성공 코드를 실패로 분류했기 때문이다.
2. ACL 없음에서 바로잡는 데 3파일을 고쳤다. 외부 모델을 아는 파일이 4개였다.
3. ACL: 같은 외부 변경이 `UNKNOWN_PG_CODE resCd=00` 예외로 **바로 드러났다.** 바로잡는 데 번역기 1파일(1줄)만 고쳤다. 단, 예외로 드러난다는 것은 고칠 때까지 결제 요청이 모두 오류가 된다는 뜻이기도 하다. 그 사이 PG가 승인한 건은 대사·취소 처리가 여전히 필요하다(해석 — 실험은 단위 테스트까지만 돌렸다).
4. ACL의 비용은 이 규모에서 번역기 11줄과 `Payment`의 도메인 필드다.
5. 금액 형식 변경(`"12,000"` → `"12000"`)은 두 설계 모두 `replace(",", "")`가 흡수해 영향이 없었다. 실패 원인은 성공 코드 하나다.

해석: ACL의 이득은 "외부 말을 아는 곳이 한 곳"이라는 데서 나온다(4파일 → 1파일). 이득의 크기는 외부 모델을 읽는 지점 수에 비례한다. 읽는 곳이 한 곳뿐이고 외부 모델이 우리 말과 거의 같다면, 번역기는 그만큼의 코드만 더하는 비용이다(Azure: 의미 차이가 크지 않으면 맞지 않는다).

## 쓰이는 자료구조·알고리즘

- **코드 사상 표(lookup table)** — `외부 코드 → 도메인 값`. `switch`나 `Map<String, Outcome>`. 핵심은 **기본값 없는 전수 매핑**이다. 표에 없는 키는 예외로 보낸다.
- **양방향 매퍼** — 요청용(도메인 → 외부)과 응답용(외부 → 도메인) 함수 쌍. 왕복 테스트(`toDomain(toExternal(x)) == x`)로 검증할 수 있는 부분은 검증한다.
- **포트·어댑터(헥사고날)** — 도메인이 정의한 인터페이스(포트)를 ACL이 구현한다. 의존 방향이 도메인 쪽을 향한다. [software-design/38-layered-hexagonal-clean](../../software-design/38-layered-hexagonal-clean/2-summary.md).
- **메시지 번역기(Message Translator)** — 비동기 통합에서 ACL은 메시지 변환기가 된다. EIP의 Message Translator는 [distributed/34-message-routing-and-transformation](../../distributed/34-message-routing-and-transformation/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. **우리 말로 포트를 먼저 정한다.** "PG가 주는 것"이 아니라 "우리 도메인이 결제에서 알아야 하는 것"으로. 예: `approved`, `amount`, `pgTxId`.
2. **외부 모델을 아는 곳을 한 패키지로 모은다.** 퍼사드·어댑터·번역기. 도메인 패키지는 외부 SDK를 import하지 않는다.
3. **매핑 표를 전수로 쓴다.** 알려진 성공·실패 코드만 명시하고, 나머지는 예외.
4. **경계에서 검증한다.** 금액 음수·통화 불일치·필수 필드 누락은 번역 단계에서 거절한다.
5. **번역 실패를 관측한다.** 상관 ID(거래 ID)를 예외 메시지·로그에 넣는다.
6. **규칙은 넣지 않는다.** "승인 금액이 주문 금액과 다르면 취소" 같은 판단은 도메인(또는 애플리케이션 서비스)에서.

### 2. 코드 (Java)

```java
// 도메인 쪽 포트 — 우리 말만 있다
package payment.domain;
public interface PaymentGateway {
    PaymentResult pay(OrderId order, Money amount);
}
public sealed interface PaymentResult {
    record Approved(String pgTxId, Money amount) implements PaymentResult {}
    record Declined(String reason) implements PaymentResult {}
}

// ACL — 외부 SDK는 이 패키지만 안다
package payment.acl;
final class PgGatewayAdapter implements payment.domain.PaymentGateway {
    private final LegacyPgClient pg;                         // 퍼사드 역할(외부 SDK를 좁혀 감쌈)
    public PaymentResult pay(OrderId order, Money amount) {
        LegacyPgResponse r = pg.pay(order.value(), amount.value().toPlainString());   // 우리 → 외부
        return PgTranslator.toDomain(r, amount.currency());                   // 외부 → 우리
    }
}
final class PgTranslator {
    static PaymentResult toDomain(LegacyPgResponse r, Currency cur) {
        return switch (r.resCd) {
            case "0000" -> new PaymentResult.Approved(r.tid, Money.of(new BigDecimal(r.amt.replace(",", "")), cur));
            case "9999", "9001" -> new PaymentResult.Declined(r.resCd);
            default -> throw new UnknownExternalCode("PG", r.resCd, r.tid);  // 조용히 실패로 분류하지 않는다
        };
    }
}
```

- `sealed` 인터페이스의 결과를 패턴 `switch`(JDK 21, JEP 441)로 다루면, 도메인 쪽에서 결과 종류를 빠뜨렸을 때 컴파일러가 잡는다. `if (r instanceof ...)` 사슬로 다루면 잡지 못한다.
- 외부 코드 `default`를 "실패"로 두지 않는다. 새 성공 코드가 실패로 분류되는 사고(실험 관찰 1)가 바로 그 경로다.

### 3. 진단 — 외부 모델이 어디까지 새어 들어왔나

```bash
# 도메인 패키지가 외부 SDK 타입·필드명을 쓰는지 — 결과가 ACL 패키지 밖에 있으면 누수
grep -rlE 'LegacyPgResponse|resCd|\.raw\.' src/payment | grep -v '/acl/'
```

- 실험의 "외부 모델 참조 위치 수"가 같은 진단이다(ACL 없음 4파일, ACL 1파일).
- 아키텍처 테스트(ArchUnit 등)로 "domain 패키지는 legacy 패키지에 의존하지 않는다"를 CI에서 강제할 수 있다([software-design/41-architecture-fitness-rules](../../software-design/41-architecture-fitness-rules/2-summary.md)).

## 장애 시나리오와 대처

### 1. ACL 부재 → 외부 모델이 핵심 도메인을 오염 (⚠ 커리큘럼)

- 현상: 외부 PG가 응답 형식을 바꾼 날부터 결제가 "실패"로 쌓인다. 고객 카드에서는 돈이 빠져나갔다.
- 보이는 형태: 에러 로그가 없다. 결제 실패율 지표가 급등하고, 대사(25번)에서 "외부 승인·내부 실패" 불일치가 쏟아진다.
- 원인: 외부 코드값 `"0000"` 해석이 도메인 여러 곳에 흩어져 있었다. 새 코드 `"00"`이 모두 실패로 분류됐다(실험: 테스트 4개 전부 FAIL).
- 대처
  - 당장: 외부 코드를 해석하는 모든 곳을 찾아 고친다(실험: 3파일). 이미 실패로 기록된 건은 대사로 찾아 바로잡는다.
  - 근본: ACL로 외부 말을 한 곳에 모은다. 모르는 코드는 예외로 드러낸다(실험: 1파일·즉시 예외).

### 2. ACL이 "기본값으로 덮는" 번역을 한다

- 현상: ACL을 뒀는데도 외부 변경 뒤 금액이 0원, 상태가 "알 수 없음"으로 저장된다.
- 보이는 형태: 도메인 데이터에 0원·NULL·UNKNOWN 상태 행이 늘어난다. 에러는 없다.
- 원인: 번역기가 없는 필드·모르는 코드를 기본값으로 바꿨다. 오염이 번역기를 통과해 들어왔다.
- 대처: 기본값 없는 전수 매핑으로 바꾼다. 실패는 예외 + 상관 ID 로그 + 지표(번역 실패 수)로 드러낸다. 18번 실험의 `getOrDefault` → "합계 0"과 같은 원인이다.

### 3. ACL에 업무 규칙이 쌓였다

- 현상: "PG 번역기"에 할인 재계산·주문 취소 판단·재시도 오케스트레이션이 들어 있다.
- 보이는 형태: 업무 규칙 변경인데 ACL 파일을 고친다. 같은 규칙이 도메인과 ACL에 두 벌 있다.
- 원인: 번역과 결정을 구분하지 않았다.
- 대처: ACL은 번역만 한다(Azure: 비즈니스 규칙·오케스트레이션을 넣지 말 것). 결정은 도메인·애플리케이션 서비스로 옮긴다.

### 4. 독립 ACL 서비스가 병목·장애점이 됐다

- 현상: 레거시 앞에 둔 ACL 서비스가 느려지거나 내려가 신 시스템 전체가 멈춘다.
- 보이는 형태: ACL 서비스의 지연 백분위 상승, 타임아웃 에러, 신 시스템의 연쇄 실패.
- 원인: Azure 문서가 고려하라고 한 지연·확장·운영(모니터링·배포) 계획을 빠뜨렸다.
- 대처: ACL을 다른 서비스처럼 확장·모니터링·배포 대상으로 관리한다. 요청 경로에 둘 필요가 없으면 애플리케이션 안의 구성 요소로 두거나 비동기 메시지 번역으로 바꾼다. 타임아웃·재시도 정책은 [distributed/03-partial-failure-and-timeouts](../../distributed/03-partial-failure-and-timeouts/2-summary.md).

## 핵심 문장

1. ACL은 하류가 상류 기능을 자기 모델의 말로 쓰게 해 주는 번역·격리 계층이며, 하류가 만들고 하류 안에 둔다.
2. ACL의 이득은 "외부 말을 아는 곳이 한 곳"이라는 데서 나온다 — 실험에서 외부 변경 대응이 3파일에서 1파일로 줄었다.
3. 번역기는 모르는 외부 값을 기본값으로 덮지 말고 예외로 드러내야 한다. 덮으면 오염이 조용히 통과한다.
4. ACL은 번역만 한다. 업무 규칙·오케스트레이션은 넣지 않는다.
5. 두 모델의 의미 차이가 작고 외부 모델을 읽는 곳이 하나뿐이면, ACL은 코드와 지연만 더하는 비용이다.

## 관련 주제·근거

- 선행
  - [18-context-mapping](../18-context-mapping/2-summary.md) — ACL을 고르는 관계(협조 없는 상류)
- 후속·연결
  - [16-bounded-contexts](../16-bounded-contexts/2-summary.md) — 지킬 모델 경계
  - [17-subdomains](../17-subdomains/2-summary.md) — 구매한 일반 서브도메인을 감싸기
  - [25-reconciliation](../25-reconciliation/2-summary.md) — 외부 승인·내부 실패 불일치 찾기
  - [software-design/50-legacy-migration-strangler-fig](../../software-design/50-legacy-migration-strangler-fig/2-summary.md) §5 — 이전 중 ACL(기초)
  - [software-design/38-layered-hexagonal-clean](../../software-design/38-layered-hexagonal-clean/2-summary.md) — 포트·어댑터
  - [software-design/43-data-across-boundaries](../../software-design/43-data-across-boundaries/2-summary.md) — 경계를 넘는 데이터와 매핑
  - [distributed/34-message-routing-and-transformation](../../distributed/34-message-routing-and-transformation/2-summary.md) — 메시지 번역기
- 글·문서
  - Eric Evans, 『Domain-Driven Design Reference』(2015) "Anticorruption Layer" <https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf>
  - Eric Evans, 『Domain-Driven Design』 14장 — ACL 내부(퍼사드·어댑터·번역기)는 2차 정리·원문 인용으로 확인, 원문 쪽 [?] <https://synchronium.github.io/software-architecture-wiki/patterns/anti-corruption-layer.html>, 원문 문장 인용 <https://stackoverflow.com/a/909287>
  - Microsoft, Azure Architecture Center "Anti-Corruption Layer pattern"(2026-05-28판) — 문제·해법·고려점(지연·추가 서비스·확장·은퇴·입력 검증·관측)·사용하지 말 때 <https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer>
  - AWS Prescriptive Guidance "Anti-corruption layer pattern" <https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/acl.html>
- 실험 목록
  - PG 응답 변경(성공 코드 `0000`→`00`, 금액 형식) — ACL 없음 vs ACL의 테스트 결과·`git diff --stat`·외부 모델 참조 파일 수·번역기 줄 수 — `scratchpad/dm/16/e19/run.sh`, JDK 21.0.12 temurin `--cpus=2 --network none`, git 2.43.0
