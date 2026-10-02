# software-design/12-simple-design-and-yagni — 단순 설계 4규칙과 YAGNI의 비용 4종 — 정리 (힌트)

## 해결하는 문제

"나중에 필요할 테니 지금 유연하게 만들자"는 판단은 두 번 틀릴 수 있다. 그 기능이 안 올 수도 있고, 와도 생각한 모양과 다를 수 있다.

```text
 지금 요구: "1만원 이상이면 1천원 할인"

 추측한 확장점 (SPEC)                               지금 요구만 (SIMPLE)
 Pricing ─> DiscountPolicyFactory ─> DiscountRegistry      Pricing (5줄)
              │                        │ Map<type, 생성자>
              v                        v
            Config ─> app.properties (키 8개, 5개는 아무도 안 읽음)
            DiscountPolicy (interface) <── FixedAmountDiscount
 7파일 51줄                                                  1파일 5줄

 6개월 뒤 실제로 온 요구: "VIP는 5% 추가 할인"  ← 할인이 '고객 등급'을 알아야 한다
 SPEC: 미리 만든 인터페이스가 등급을 모른다 → 7파일 수정
 SIMPLE: 이제 확장점을 만든다 → 2파일 수정
```

- *YAGNI(You Aren't Gonna Need It)*: 미래에 필요할 것으로 추정한 기능을 지금 만들지 말라는 XP의 원칙.
- *추정 기능(presumptive feature)*: 아직 쓰이지 않는 기능을 지원하려고 지금 넣은 코드(Fowler "Yagni"의 용어).
- *확장점(extension point)*: 새 변형을 기존 코드 수정 없이 끼울 수 있게 미리 뚫어 둔 자리(인터페이스·레지스트리·설정 키 등).

쉬운 예: 아이가 크면 쓸 거라며 방 크기의 2층 침대를 미리 샀다. 쓰지도 않는 침대를 피해 다니고(유지 비용), 막상 아이가 크니 책상이 필요했다(모양이 틀림).\
똑같은 구조다.\
실무 예: "할인 종류가 늘 것"이라며 전략 인터페이스·팩토리·레지스트리·설정 키를 미리 만들었다. 실제로 온 요구는 인터페이스가 모르는 정보(고객 등급)가 필요했다.

## 동작·원리

### 1. Beck의 단순 설계 4규칙

```text
  우선순위 높음
   1. 테스트를 통과한다 (Passes the tests)          ← 무엇보다 먼저: 의도대로 동작
   2. 의도를 드러낸다   (Reveals intention)         ← 읽는 사람이 목적을 안다
   3. 중복이 없다       (No duplication)            ← Once and Only Once
   4. 요소가 가장 적다  (Fewest elements)           ← 위 셋에 기여 안 하는 것은 지운다
  우선순위 낮음
```

- 위 표현은 Martin Fowler "BeckDesignRules"(2015-03-02)의 것이다. Fowler는 Beck이 1990년대 후반 XP를 만들며 정했고, 저자마다 표현이 조금씩 다르다고 쓴다.
- 권위 있는 원문은 『Extreme Programming Explained』 1판(White Book) p.57이라고 Fowler가 안내한다. 그 판의 순서는 "테스트 실행 → 중복 로직 없음 → 의도 표현 → 클래스·메서드 최소"다(Fowler가 인용, 원서 직접 확인 못 함 [?]).
- "우선순위 순"은 1번이 가장 중요하다는 뜻이다. Fowler는 2번(의도)과 3번(중복)의 순서는 중요하지 않다고 본다. 둘이 서로를 다듬기 때문이다. Beck은 드물게 충돌하면 "empathy wins"라고 답했다(같은 글 각주).
- 4번 규칙이 YAGNI와 이어진다. Fowler: 당시 미래 요구에 대비해 요소를 더하라는 조언이 많았는데, 그 추가 복잡도가 대개 시스템을 오히려 고치기 어렵게 만들었다.

### 2. YAGNI의 비용 4종

```text
 추정 기능을 지금 만든다
     │
     ├─ 결국 필요 없었다 ─────────────> build 비용 (분석·코딩·테스트가 헛수고)
     │                                 + carry 비용 (지울 때까지 모든 기능이 그 복잡도를 지고 간다)
     │
     ├─ 필요했고 맞게 만들었다 ───────> delay 비용 (그동안 다른 가치 있는 기능을 못 냈다)
     │                                 + carry 비용 (쓰이기 전까지 다른 기능 개발을 느리게 한다)
     │
     └─ 필요했지만 틀린 모양이었다 ───> repair 비용 (고치거나, 우회하며 계속 비용을 낸다)
```

- *build 비용*: 만드는 데 든 노력 자체.
- *delay 비용(cost of delay)*: 그 노력을 다른 기능에 썼다면 더 일찍 냈을 가치.
- *carry 비용(cost of carry)*: 추가된 복잡도 때문에 다른 기능의 수정·디버깅이 느려지는 비용.
- *repair 비용(cost of repair)*: 맞는 기능을 틀리게 만들어 나중에 고치거나 우회하는 비용.
- 출처: Fowler "Yagni"(2015-05-26). 추정 기능을 세 부류(실패·성공·맞는 기능을 틀리게)로 나누고, 거기서 비용 네 종류가 나온다고 쓴다.
- 같은 글: Kohavi 등의 Microsoft 분석에서 신중한 사전 분석을 거친 기능도 의도한 지표를 개선한 것은 ⅓뿐이었다. 그래서 추정 기능이 불필요할 확률을 "적어도 ⅔"로 본다.

### 3. YAGNI가 아닌 것

- 리팩터링·자체 테스트 코드(SelfTestingCode)·지속적 전달은 YAGNI 위반이 아니다. 코드를 **고치기 쉽게** 만드는 노력이기 때문이다(Fowler "Yagni").
- YAGNI는 코드가 고치기 쉬울 때만 성립한다. Fowler: "Yagni requires (and enables) malleable code." 테스트·리팩터링을 건너뛰는 핑계가 아니다.
- 지금 하기 쉽고 복잡도를 거의 늘리지 않으면서 나중 비용을 크게 줄이는 일은 해 둘 만하다(Fowler — "나중 리팩터링을 상상해 보기"의 또 다른 결과로 든다). Fowler의 예: 에러 메시지를 인라인 문자열 대신 조회 테이블에 두면 나중 번역이 쉬워진다.
- 판별 질문(Fowler의 방법): "나중에 필요해지면 어떤 리팩터링을 하게 될까?"를 상상해 본다. 그 비용이 지금 만드는 비용보다 크게 비싸지 않으면 미룬다.

### 4. 확장점은 두 번째 요구가 올 때

```text
 요구 1 ──> 직접 구현 (확장점 없음)
 요구 2 ──> 두 사례를 보고, 실제로 달라지는 축(여기서는 "고객 등급")에 맞춰 확장점을 만든다
 요구 3 ──> 확장점에 끼운다
```

- 둘째 요구가 오면 변하는 축이 실제 데이터로 드러난다. 첫 요구만 보고 축을 추측하면 틀릴 수 있다(Fowler: 지금 생각한 추상화가 실제로 필요할 때 배운 것과 맞지 않을 수 있다).
- 같은 이유로 셋째 사례 규칙([11-when-to-abstract](../11-when-to-abstract/2-summary.md))과 이어진다. 확장점도 추상화다.

### 실험: 추측한 확장점 vs 지금 요구만

같은 테스트(`Tests.java`)로 두 설계를 확인했다.

```java
// SIMPLE v1 — 지금 요구만
static long total(long subtotal, String grade) {
  return subtotal >= 10_000 ? subtotal - 1_000 : subtotal;
}
// SPEC v1 — 미리 만든 확장점: 금액만 받는 인터페이스, 설정의 discount.type 하나로 고른다
interface DiscountPolicy { long discount(long subtotal); }
// SIMPLE v2 — 두 번째 요구(VIP)가 온 뒤, 실제로 달라진 축(등급)을 받는 확장점을 만든다
interface Discount { long apply(long amount, String grade); }
private static final List<Discount> CHAIN = List.of(
    (amount, grade) -> amount >= 10_000 ? amount - 1_000 : amount,
    (amount, grade) -> grade.equals("VIP") ? amount - amount * 5 / 100 : amount);
```

(실험, JDK 21.0.12 temurin `--cpus=2`, git 2.43.0, `scratchpad/sd/11/e12/`, 2026-10-02)

```text
=== v1 만들기 (build 비용): 테스트 커밋 대비 ===
--- simple-v1
 1 file changed, 5 insertions(+)
--- spec-v1
 7 files changed, 51 insertions(+)
=== 두 번째 요구(VIP 5%) ===
--- simple-v1 → simple-v2
 Discount.java | 3 +++
 Pricing.java  | 8 +++++++-
 2 files changed, 10 insertions(+), 1 deletion(-)
--- spec-v1 → spec-v2
 DiscountPolicy.java        | 2 +-
 DiscountPolicyFactory.java | 7 +++++--
 DiscountRegistry.java      | 1 +
 FixedAmountDiscount.java   | 2 +-
 Pricing.java               | 7 +++++--
 VipRateDiscount.java       | 5 +++++
 app.properties             | 4 ++--
 7 files changed, 20 insertions(+), 8 deletions(-)
=== 설정 키: 정의됐지만 코드가 읽지 않는 키 ===
spec-v1: 키 8개, 미사용: discount.rate.percent discount.stackable discount.max.cap discount.plugin.dir discount.currency
spec-v2: 키 8개, 미사용: discount.stackable discount.max.cap discount.plugin.dir discount.currency
=== 대조: 추측이 맞은 두 번째 요구(2만원 이상 3%) ===
--- simple-v1 → simple-hit
 2 files changed, 10 insertions(+), 1 deletion(-)
--- spec-v1 → spec-hit
 5 files changed, 18 insertions(+), 6 deletions(-)
```

- 테스트는 네 브랜치(v1·v2 각 두 설계)와 대조 브랜치 둘에서 모두 `ALL PASS`였다(VIP 20,000원 → 18,050원, 대조 30,000원 → 28,130원).
- 관찰 1(build) — 같은 동작에 SIMPLE 1파일 5줄, SPEC 7파일 51줄. 가격 계산 경로를 이해하려고 읽을 코드도 같은 비율이다.
- 관찰 2(repair) — 실제 둘째 요구는 할인이 등급을 알아야 했다. SPEC은 미리 만든 인터페이스·구현·팩토리·조합 규칙을 고쳐 7파일이었다. SIMPLE은 그때 확장점을 만들어 2파일이었다.
- 관찰 3(대조) — 둘째 요구가 미리 만든 모양(금액만 보는 할인)에 맞았는데도 SPEC은 5파일이었다. 추측한 구조는 "할인 하나를 고른다"였고, 실제 요구는 "할인 둘을 차례로 적용"이었다.
- 관찰 4(carry) — SPEC v1의 설정 키 8개 중 5개는 코드가 읽지 않았다. 둘째 요구 뒤에도 4개가 남았다.
- 반대 사례(실행하지 않고 코드 구조로 판단): 할인 금액만 바꾸는 요구(1천원 → 2천원)는 SPEC에서 `app.properties` 한 줄로 끝나 코드 수정·재컴파일 없이 바꿀 수 있다. 다만 이 실험의 `Config`는 클래스 초기화 때 파일을 한 번 읽으므로(`static final POLICY`) 값을 바꾸려면 재시작이 필요하다. 운영 중 값 변경이 실제 요구라면 그 확장점은 값어치를 한다. 그 요구가 **이미 있을 때** 만드는 것이다.
- 해석: 이 실험은 작은 예제 하나다. "추측이 틀렸을 때 비싸다"를 보였을 뿐, 모든 확장점이 손해라는 뜻은 아니다.

## 쓰이는 자료구조·알고리즘

- **디스패치 테이블(레지스트리)**: `Map<String, Function<Config, DiscountPolicy>>`로 문자열 → 생성자를 찾는다. 확장점의 흔한 구현이다. 키가 하나뿐이면 테이블 조회가 `if` 하나보다 읽기 어렵다. 조건문 도구 선택은 [28-taming-conditionals](../28-taming-conditionals/2-summary.md).
- **체인(리스트 순회)**: 둘째 요구 뒤 SIMPLE의 `List<Discount>`는 할인을 순서대로 적용하는 파이프라인이다. 순서가 결과를 바꾼다(1천원 먼저, 5% 나중 → 18,050원).
- **집합 차집합으로 미사용 설정 찾기**: (정의된 키 집합) − (코드가 참조하는 키 집합) = 아무도 안 읽는 키. 실험의 `measure.sh`가 이 방식이다.
- **설정 조합 수**: 독립 불리언 설정 n개는 조합 2^n개를 만든다. 키 40개 중 불리언이 20개면 조합 2^20 = 1,048,576개라 전수 테스트가 불가능하다(계산). 테스트 설계 쪽의 쌍 조합은 testing 영역 07 test-design-techniques([testing/README](../../testing/README.md), 미작성).
- **호출 그래프 도달성**: 진입점에서 닿지 않는 클래스·메서드 = 지금 아무도 쓰지 않는 코드. 지우기 쉬운 코드는 [54-designing-for-deletion](../54-designing-for-deletion/2-summary.md).

## 적용 — 풀어나가는 법

1. **설계 리뷰 질문 세 개**: 이 요소는 지금 어떤 테스트·요구가 쓰나? 없다면 나중에 필요할 때 넣는 리팩터링은 얼마나 비싼가? 지금 넣으면 지금 코드를 읽기 어려워지나?
2. **4규칙을 순서대로 적용한다.** 테스트 통과 → 이름·구조로 의도 드러내기 → 중복 제거 → 기여하지 않는 클래스·메서드·설정 삭제.
3. **둘째 요구가 오면 그때 확장점을 만든다.** 두 사례에서 실제로 달라지는 입력(실험: 고객 등급)을 인터페이스에 반영한다.

```java
// 요구 1: 직접
static long total(long subtotal, String grade) {
  return subtotal >= 10_000 ? subtotal - 1_000 : subtotal;
}
// 요구 2: 두 사례가 드러낸 축(등급)으로 확장점
interface Discount { long apply(long amount, String grade); }
```

4. **미사용 설정 키를 주기적으로 찾는다.**

```bash
# 정의된 키 중 코드가 문자열로 참조하지 않는 키
for k in $(grep -oE '^[a-z0-9.-]+' src/main/resources/application.properties); do
  grep -rqF "\"$k\"" src/main/java || grep -rqF "{$k}" src/main/java || echo "미사용? $k"
done
```

- Spring Boot `@ConfigurationProperties`로 묶은 키는 문자열 참조 없이 바인딩되므로 위 grep이 놓친다. 그런 키는 바인딩 클래스의 필드 사용처를 본다(해석, 실행하지 않음).

5. **YAGNI를 테스트·리팩터링 생략의 핑계로 쓰지 않는다.** 미루는 전략은 나중에 쉽게 고칠 수 있을 때만 싸다.

## 장애 시나리오와 대처

### 1. 안 쓰는 인터페이스·팩토리·플러그인 구조 — 기능마다 5계층 수정 (⚠ 커리큘럼, carry 비용)

- 현상: 할인 하나 추가에 인터페이스·구현·팩토리·레지스트리·설정을 다 건드린다.
- 보이는 형태: 작은 기능 PR의 `git diff --stat`이 5~7파일. 리뷰어가 "이 계층은 뭐 하는 거냐"고 묻는다. 실험 SPEC v2는 7파일 +20/−8.
- 원인: 쓰이지 않는 일반화가 모든 변경에 세금을 매긴다(carry).
- 대처: 구현이 하나뿐인 인터페이스·팩토리는 인라인해서 줄인다(Inline Class·Collapse Hierarchy 계열). 실제로 둘째 변형이 생기면 다시 만든다.

### 2. "나중에 필요할" 설정 키 40개 중 38개 미사용 — 조합 테스트 불가 (⚠ 커리큘럼)

- 현상: 설정 파일에 키가 많지만 실제로 읽히는 것은 일부다. 어떤 조합이 안전한지 아무도 모른다.
- 보이는 형태: 미사용 키 탐지에서 대량 검출(실험: 8개 중 5개). 운영자가 "있는 키"를 바꿨는데 아무 일도 안 일어난다.
- 원인: 추정 기능의 설정만 먼저 만들었다. 불리언 n개는 2^n 조합이라 테스트로 덮을 수 없다.
- 대처: 읽히지 않는 키를 지운다. 남은 키는 유효 조합을 문서·검증 코드로 제한한다(시작 시 잘못된 조합이면 기동 실패).

### 3. 추측한 확장점이 실제 요구 모양과 달라 결국 우회 (⚠ 커리큘럼, repair 비용)

- 현상: 미리 만든 `DiscountPolicy.discount(subtotal)`에 고객 등급을 넘길 자리가 없다. ThreadLocal·전역 변수로 등급을 몰래 넘기는 우회가 생긴다.
- 보이는 형태: 확장점 시그니처를 바꾸는 PR이 모든 구현체를 건드린다(실험 SPEC v2). 또는 우회 코드와 숨은 입력이 늘어난다.
- 원인: 첫 요구만 보고 변하는 축을 추측했다.
- 대처: 우회하지 말고 시그니처를 실제 축에 맞게 바꾼다. 다음부터는 둘째 요구에서 축을 확인하고 확장점을 만든다.

### 4. 반대 실패 — YAGNI를 핑계로 테스트·리팩터링을 미뤄 코드가 굳는다

- 현상: "지금 필요 없다"며 정리·테스트를 건너뛰었다. 몇 달 뒤 작은 요구에도 손대기 무섭다.
- 보이는 형태: 변경마다 회귀 버그, 리팩터링 PR이 거절된다("동작이 바뀔까 봐").
- 원인: YAGNI는 고치기 쉬운 코드를 전제로 한다(Fowler). 그 전제를 무너뜨렸다.
- 대처: 리팩터링·테스트는 YAGNI 대상이 아니라는 점을 팀 규칙으로 둔다. 리팩터링 절차는 [13-refactoring](../13-refactoring/2-summary.md).

## 핵심 문장

- Beck의 단순 설계 4규칙은 테스트 통과 → 의도 드러냄 → 중복 없음 → 요소 최소다. 앞의 셋에 기여하지 않는 요소는 지운다.
- YAGNI를 어긴 비용은 build·delay·carry·repair 네 가지다(Fowler 2015). 추정 기능이 맞았을 때도 delay·carry는 낸다.
- YAGNI는 리팩터링·테스트를 생략하라는 뜻이 아니다. 고치기 쉬운 코드가 있어야 미루는 전략이 싸다.
- 확장점은 둘째 요구가 실제로 올 때 만든다. 그때 변하는 축이 데이터로 드러난다.
- 실험에서 미리 만든 확장점은 7파일 51줄이었고, 실제 둘째 요구에 7파일을 다시 고쳤다. 지금 요구만 만든 쪽은 5줄로 시작해 둘째 요구에 2파일을 고쳤다.

## 관련 주제·근거

- 선행
  - [11-when-to-abstract](../11-when-to-abstract/2-summary.md) — 추상화 시점, 셋째 사례 규칙, 잘못된 추상화
- 후속·연결
  - [10-code-smells](../10-code-smells/2-summary.md) — Speculative Generality 스멜
  - [13-refactoring](../13-refactoring/2-summary.md) — YAGNI를 가능하게 하는 습관
  - [28-taming-conditionals](../28-taming-conditionals/2-summary.md) — 테이블·전략을 언제 쓰나
  - [36-extension-points-and-plugins](../36-extension-points-and-plugins/2-summary.md) — 확장점을 실제로 둘 때의 설계
  - [54-designing-for-deletion](../54-designing-for-deletion/2-summary.md) — 미사용 코드·설정 걷어내기
  - [reliability/24-feature-flag-lifecycle](../../reliability/24-feature-flag-lifecycle/2-summary.md) — 끝난 플래그가 남기는 carry 비용
- 글·문서
  - Martin Fowler, "BeckDesignRules", 2015-03-02 <https://martinfowler.com/bliki/BeckDesignRules.html>
  - Martin Fowler, "Yagni", 2015-05-26 — 추정 기능 3부류·비용 4종, Kohavi ⅓, 리팩터링은 YAGNI 위반 아님 <https://martinfowler.com/bliki/Yagni.html>
  - Kent Beck, 『Extreme Programming Explained』 1판(1999) p.57 Simple Design — Fowler의 인용으로만 확인 [?]. 2판은 incremental design으로 부른다(Fowler "Yagni")
- 실험 목록 (코드: scratchpad `sd/11/e12/build.sh`·`build-hit.sh`·`measure.sh`, JDK 21.0.12 temurin `--cpus=2`, git 2.43.0)
  - SIMPLE vs SPEC: v1 build 크기, 둘째 요구(VIP, 등급 필요) diff, 추측이 맞은 둘째 요구(2만원 이상 3%) diff, 미사용 설정 키, 테스트
