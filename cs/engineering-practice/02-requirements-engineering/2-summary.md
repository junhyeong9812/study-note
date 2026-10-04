# engineering-practice/02-requirements-engineering — 요구 도출·명세·검증·추적 — 정리 (힌트)

## 해결하는 문제

"검색이 빨라야 한다"는 요구를 받았다고 하자. 개발자는 1초를 떠올리고, 기획자는 0.2초를 떠올린다.\
둘 다 "빠르게"에 동의했으므로 아무도 어긋남을 모른다. 출시 뒤에야 안다.

```text
  요구 문장          머릿속 해석                결과
  "빨라야 한다" ──┬─▶ 개발자: 1초면 빠르지      구현 → 출시 → "느린데요?"
                 └─▶ 기획자: 0.2초는 돼야지    → 재작업 (설계부터 다시)
```

- *요구(requirement)*: ISO/IEC/IEEE 29148:2018 3.1.19의 정의는 "필요와 그에 딸린 제약·조건을 옮겨 표현한 진술"이다. 같은 항목의 주석은 요구를 "매우 구체적이고 정확하며 모호하지 않게" 표현한 것이라고 쓴다.
- *요구공학(requirements engineering)*: 같은 표준 3.1.21은 획득자와 공급자 사이를 잇는 학제 간 기능으로, 시스템이 충족할 요구를 세우고 유지하는 일이라고 정의한다. 같은 항목 주석은 요구의 발견·도출·개발·분석·검증·확인·소통·문서화·관리를 다룬다고 쓴다.

쉬운 예: 집 리모델링에서 "거실을 밝게 해 주세요"다.
- 시공자는 조명을 바꾸고, 집주인은 창을 넓히는 것을 생각했다. 공사가 끝난 뒤에야 다르다는 것을 안다.
- "저녁 8시에 거실 바닥 조도 300lx 이상"이라고 쓰면, 공사 전에 조도계로 확인할 수 있는 약속이 된다(수치는 예시).

똑같은 구조다.\
요구를 **확인할 수 있는 문장**으로 바꾸는 일이 이 주제의 중심이다.

실무 예:
- 커리큘럼 ⚠: 모호 요구("빠르게") → 구현 후 재작업.
- 커리큘럼 ⚠: 비기능 요구 누락. 기능은 다 됐는데 출시 직전 부하 테스트에서 응답이 몇 초씩 걸린다. 가용성·보관 기한·감사 로그 요구가 처음부터 없었다.
- 요구가 바뀌었는데 어떤 테스트를 고쳐야 하는지 아무도 모른다. 요구와 테스트 사이의 연결(추적)이 없다.

## 동작·원리

### 1. 요구공학의 활동 흐름

```text
  이해관계자 ─▶ 도출 ─▶ 분석 ─▶ 명세 ─▶ 검증·확인 ─▶ 기준선
  (누가 원하나)  (끌어내기) (충돌·우선순위) (문장으로)  (잘 썼나·맞는 것인가)
                   ▲                                            │
                   └──────────── 변경 요청·추적 (관리) ◀──────────┘
```

- *이해관계자(stakeholder)*: 시스템에 권리·몫·이해가 있는 사람이나 조직(29148 3.1.28). 최종 사용자만이 아니다. 운영자·유지보수자·규제 기관도 들어간다(같은 항목 주석).
- *도출(elicitation)*: 시제품·구조화된 설문 같은 체계적 기법으로 고객·최종 사용자의 필요를 찾아 적는 일(3.1.20).
- *요구 관리(requirements management)*: 수명 주기 내내 요구를 식별·문서화·유지·소통·추적하는 활동(3.1.22).
- SWEBOK v4는 이 흐름을 1장 Software Requirements에서 다룬다(장 번호는 IEEE CS의 장별 웨비나 목록으로 확인). 장 안의 절 이름은 원문을 열지 못해 `[?]`.
- 흐름은 한 번에 끝나지 않는다. 29148 목차의 5.3 "Practical considerations"는 반복(iteration)과 재귀(recursion) 적용을 따로 다룬다. 반복형 개발(01번)에서는 스프린트마다 이 흐름이 작게 돈다.

### 2. 검증(verification)과 확인(validation)

```text
                 잘 썼나?                       맞는 것을 쓰고 있나?
  요구 문장 ──▶ [요구 검증 verification] ──▶ [요구 확인 validation] ──▶ 기준선
               모호어·단일성·측정 기준         이해관계자가 의도한 시스템인가
               (문서만 보고 판정 가능)          (시제품·리뷰·인수 테스트)
```

- *요구 검증(requirements verification)*: 요구가 잘 형성됐는지 검토로 확인하는 것(29148 3.1.26).
- *요구 확인(requirements validation)*: 요구가 이해관계자가 의도한 **올바른 시스템**을 정의하는지 확인하는 것(3.1.25).
    - 흔한 오해: 둘은 같은 말이다. 29148은 정의를 나눈다. 잘 쓴 문장(검증 통과)도 틀린 시스템을 가리킬 수 있다(확인 실패).

### 3. 좋은 요구 문장의 특성

- 29148 5.2.5는 개별 요구의 특성 9가지를 든다: 필요(necessary)·적절(appropriate)·모호하지 않음(unambiguous)·완전(complete)·단일(singular)·실현 가능(feasible)·검증 가능(verifiable)·정확(correct)·준수(conforming). 5.2.6은 요구 집합의 특성을 따로 든다(완전·일관·실현 가능·이해 가능·확인 가능). 절 번호는 표준 견본의 목차로 확인했다. 5.2.5 목록 중 8개는 2차 출처로 확인했고, 준수(conforming)는 그 출처에 이름이 없어 `[?]`다(표준 본문은 유료라 열지 못함).
- 5.2.7 "requirement language criteria"는 피해야 할 표현을 다룬다(절 제목은 견본 목차로 확인, 범주 목록은 표준 본문을 못 열어 `[?]`). 이 기준을 바탕으로 만든 *요구 냄새(requirement smells)* 목록이 있다. Femmer 외가 29148:2011을 바탕으로 사전을 만들었고, arXiv 2403.17479 표 3이 이를 정리했다: 주관적 표현(user friendly), 모호한 부사·형용사(almost), 검증 불가 용어(빠져나갈 구멍·열린 표현을 합침 — sufficient·as far as possible), 최상급(highest), 비교 표현(more exact), 부정문(must not), 모호한 대명사. 같은 표에는 저자들이 새로 더한 다의어·불확실한 동사(may·can)도 있다.

```text
  모호                                  검증 가능
  "검색은 빨라야 한다."            ─▶   "상품 검색 API는 상품 100000건, 초당 50요청에서
                                         p95 응답 시간이 300ms 이하여야 한다."   (수치는 예시)
   └ 무엇이? 어떤 조건에서? 얼마나?        └ 대상·부하 조건·지표·임계값이 다 있다
```

- *단일(singular)*: 한 요구가 한 가지만 말한다. "취소할 수 있고, 환불은 3일 안에 된다"는 둘로 쪼갠다. 테스트·추적 단위가 요구 하나와 맞아야 하기 때문이다.

### 4. 기능 요구와 비기능 요구

| | 기능 요구 | 비기능 요구(품질 요구·제약) |
|---|---|---|
| 묻는 것 | 무엇을 하나 | 얼마나 잘·어떤 조건에서 하나 |
| 예 | 주문을 취소한다 | p95 300ms, 월 가용성 99.9%, 개인정보 보관 기한 |
| 확인 수단 | 단위·인수 테스트 | 부하 테스트·SLO 모니터링·감사·리뷰 |
| 흔한 실패 | 경계 조건 누락 | **아예 안 적음** |

- *비기능 요구(nonfunctional requirement)*: 시스템이 하는 일이 아니라 그 일의 품질 속성이나 제약을 정하는 요구. 품질 속성 자체는 [software-design/46-quality-attributes-and-tradeoffs](../../software-design/46-quality-attributes-and-tradeoffs/2-summary.md) 참고.
- 비기능 요구는 단위 테스트로 확인되지 않는 것이 많다. 그래서 매트릭스에서 "연결된 테스트 없음"으로 남기 쉽다. 가용성 같은 요구는 운영 지표(SLO)로 확인한다([reliability/02-slo-sli-error-budget](../../reliability/02-slo-sli-error-budget/2-summary.md)).

### 5. 추적 — 위로, 아래로

```text
  필요(이해관계자)           "주문 실수를 되돌리고 싶다"
        ▲ 위로: 이 요구는 왜 있나 (부모)
        │
  시스템·소프트웨어 요구      REQ-2 "결제 후 24시간 이내·배송 전이면 취소 가능"
        │ 아래로: 무엇이 이 요구를 구현·확인하나 (자식)
        ▼
  설계·코드·테스트            OrderCancelTest.cancel_at_24h01m_after_payment_is_rejected
```

- *요구 추적(requirements traceability)*: 요구의 위쪽 도출 경로와 아래쪽 할당 경로를 식별·문서화하는 것(29148 3.1.23).
- *추적 매트릭스(requirements traceability matrix)*: 요구를 상위 요구·필요나 하위 구현에 잇는 구조화된 정보(3.1.24). 커리큘럼의 🔧 칸이다.
- 추적이 있으면 두 질문에 답할 수 있다.
  - 요구가 바뀌면 어떤 테스트·코드를 봐야 하나(영향 분석).
  - 이 테스트는 왜 있나. 없는 요구를 가리키면 죽은 코드일 수 있다.

### 실험: 모호 요구를 고쳐 쓴 전후의 추적 매트릭스

같은 기능을 v1(모호한 요구 3개)과 v2(고쳐 쓴 요구 5개, 비기능 2개 포함)로 적었다. 테스트 소스의 `@Req("REQ-n")` 표식을 읽어 매트릭스를 만들고, 모호어와 수치 기준을 검사했다.

```java
// Trace.java 핵심 — 테스트 소스에서 @Req 표식을 모아 요구 → 테스트 역색인을 만든다
static final Pattern REQ_REF = Pattern.compile("@Req\\(\"(REQ-\\d+)\"\\)\\s*@Test\\s+void\\s+(\\w+)");
// 요구 냄새 범주(주관어·모호 부사·빠져나갈 구멍 등)를 한국어로 옮긴 예시 목록(전부가 아니다)
static final List<String> VAGUE = List.of("빠르", "빨라", "신속", "쉽게", "편리", "사용자 친화", "최대한",
        "최적", "적절히", "가능하면", "필요 시", "충분히", "최소화", "등을", "등의");
...
Matcher m = REQ_REF.matcher(Files.readString(f));
while (m.find()) testsByReq.computeIfAbsent(m.group(1), k -> new ArrayList<>()).add(m.group(2));
...
testsByReq.keySet().stream().filter(k -> !ids.contains(k))      // 고아 테스트 = 테스트 쪽 키 - 요구 ID
    .forEach(k -> System.out.println(k + " <- " + testsByReq.get(k)));
```

입력(v1 → v2)

```text
v1  REQ-1 | F | 검색은 빨라야 한다.
    REQ-2 | F | 사용자는 주문을 취소할 수 있다.
    REQ-3 | F | 결제가 실패하면 가능하면 사용자에게 적절히 알린다.
v2  REQ-1 | N | 상품 검색 API는 상품 100000건, 초당 50요청에서 p95 응답 시간이 300ms 이하여야 한다.
    REQ-2 | F | 사용자는 결제 완료 후 24시간 이내이고 배송 시작 전인 주문을 취소할 수 있다.
    REQ-3 | F | 배송이 시작된 주문의 취소 요청은 거절하고 오류 코드 ORDER_ALREADY_SHIPPED를 돌려준다.
    REQ-4 | F | 결제 승인이 실패하면 3초 이내에 실패 사유 코드와 재시도 버튼을 화면에 보여 준다.
    REQ-5 | N | 주문 API의 월간 가용성은 99.9% 이상이어야 한다.
    (v2 테스트 폴더에는 일부러 없는 요구 REQ-9를 가리키는 테스트 하나를 넣었다)
```

- v1의 REQ-1 "빨라야 한다"는 속도, 곧 품질을 묻는 요구다. 아래 4절 표 기준으로는 비기능 요구다. v1 입력은 이것을 F(기능)로 잘못 분류해 두었다. 그래서 출력의 "비기능 0"은 비기능 요구가 없다는 뜻이 아니라, 비기능 요구를 비기능으로 적지 않았다는 뜻이다. v2는 같은 요구를 N으로 고쳐 적었다.

(실험, JDK 21 temurin 21.0.12, `java Trace.java v1` / `v2`, 2026-10-05)

```text
######## v1
== 1. 요구 문장 검사 (모호어 / 측정 기준)
REQ-1  F  모호어=[빨라]  수치기준=없음
REQ-2  F  모호어=[]  수치기준=없음
REQ-3  F  모호어=[적절히, 가능하면]  수치기준=없음
== 2. 추적 매트릭스 (요구 -> 테스트)
REQ-1  테스트 0개 <-- 검증 수단 없음
REQ-2  테스트 1개 [cancelOrder]
REQ-3  테스트 0개 <-- 검증 수단 없음
== 3. 고아 테스트 (없는 요구를 가리킴)
== 요약: 요구 3개(비기능 0) · 테스트 1개 · 요구 커버 1/3
######## v2
== 1. 요구 문장 검사 (모호어 / 측정 기준)
REQ-1  N  모호어=[]  수치기준=있음
REQ-2  F  모호어=[]  수치기준=있음
REQ-3  F  모호어=[]  수치기준=없음
REQ-4  F  모호어=[]  수치기준=있음
REQ-5  N  모호어=[]  수치기준=있음
== 2. 추적 매트릭스 (요구 -> 테스트)
REQ-1  테스트 1개 [p95_under_300ms_at_50rps_with_100k_products]
REQ-2  테스트 3개 [cancel_at_23h59m_after_payment_succeeds, cancel_at_24h00m_after_payment_succeeds, cancel_at_24h01m_after_payment_is_rejected]
REQ-3  테스트 1개 [cancel_after_shipping_started_returns_ORDER_ALREADY_SHIPPED]
REQ-4  테스트 1개 [declined_card_shows_reason_code_and_retry_within_3s]
REQ-5  테스트 0개 <-- 검증 수단 없음
== 3. 고아 테스트 (없는 요구를 가리킴)
REQ-9 <- [old_coupon_rule]
== 요약: 요구 5개(비기능 2) · 테스트 7개 · 요구 커버 4/5
```

- 관찰
  - 출력의 "검증 수단 없음"은 이 도구가 붙인 이름이다. 뜻은 "`@Req` 표식으로 연결된 테스트가 없음"이다. 리뷰·모니터링 같은 다른 확인 수단이 있는지는 이 도구가 모른다.
  - v1은 테스트가 1개다. 모호한 REQ-1·REQ-3에는 쓸 테스트가 없다. "빨라야"를 통과·실패로 가를 기준이 없기 때문이다.
  - v2의 REQ-2는 "24시간"이라는 경계가 생겨 경계값 테스트 3개(23:59·24:00·24:01)가 나왔다. 경계값 기법은 [testing/07-test-design-techniques](../../testing/07-test-design-techniques/2-summary.md).
  - 비기능 요구 REQ-5(가용성)는 테스트가 0개로 드러났다. 단위 테스트가 아니라 SLO 모니터링으로 확인할 요구다. 매트릭스에 "모니터링 링크" 칸을 따로 두는 이유다.
  - 없는 요구 ID(REQ-9)를 가리키는 고아 테스트가 잡혔다. 이 실험에서는 일부러 넣었다. 실무에서는 요구가 지워졌는데 테스트만 남았거나 ID를 잘못 적었을 때 이렇게 보인다. 요약의 "테스트 7개"는 이 고아 1개를 포함한 수다.
- 도구의 한계(이것도 관찰이다)
  - v1 REQ-2는 모호어가 없다. 그런데 "언제까지·어떤 상태에서" 취소할 수 있는지 빠져 있다(불완전). 단어 검사로는 못 잡는다. 리뷰와 질문으로 잡는다.
  - v2 REQ-3은 수치가 없지만 검증 가능하다(오류 코드 비교). "수치 기준 없음 ≠ 검증 불가"다.
  - 그래서 이런 검사기는 리뷰를 돕는 보조 장치다. 판정은 사람이 한다.

## 쓰이는 자료구조·알고리즘

- **역색인(inverted index)**: 테스트 → 요구 표식을 뒤집어 요구 → 테스트 목록(`Map<String, List<String>>`)을 만든다. 검색 엔진의 단어 → 문서 역색인과 같은 구조다([data-structure/32-inverted-index](../../data-structure/32-inverted-index/)).
- **이분 그래프와 집합 차**: 추적 매트릭스는 요구 집합과 산출물 집합 사이의 이분 그래프다. "테스트 연결이 없는 요구" = 요구 ID 집합 − 테스트가 가리키는 ID 집합, "고아 테스트" = 그 반대 차집합이다. 그래프 표현은 [data-structure/08-graph](../../data-structure/08-graph/).
- **트리(요구 분해)**: 이해관계자 필요 → 시스템 요구 → 소프트웨어 요구는 부모·자식 관계다(29148 3.1.23 주석의 parent·child requirement). 위로 추적 = 부모 따라가기, 아래로 추적 = 자식 펼치기.
- **결정 테이블**: 조건이 여러 개인 요구(결제 상태 × 배송 상태 × 경과 시간)는 조건 조합 표로 펼쳐 빠진 조합을 찾는다([testing/07-test-design-techniques](../../testing/07-test-design-techniques/2-summary.md)).
- **용어 사전(유비쿼터스 언어)**: "취소"·"환불"·"반품"이 문장마다 다른 뜻이면 요구 집합의 일관성이 깨진다. 같은 단어를 한 뜻으로만 쓰는 사전을 둔다([domain-modeling/03-ubiquitous-language](../../domain-modeling/03-ubiquitous-language/)).

## 적용 — 풀어나가는 법

### 1. 실무 순서

1. **이해관계자 목록**: 사용자뿐 아니라 운영·보안·법무·고객지원을 적는다. 비기능 요구는 대개 이쪽에서 나온다.
2. **도출 질문**: 요구 문장마다 "누가·언제·어떤 조건에서·얼마나·실패하면?"을 묻는다.
3. **문장 고쳐 쓰기**: 모호어를 지우고, 한 문장에 한 요구만 둔다. 측정 대상·조건·임계값을 넣는다.
4. **수용 기준**: Given-When-Then으로 쓴다. 인수 테스트와 바로 이어진다([testing/06-outside-in-tdd-and-acceptance-tests](../../testing/06-outside-in-tdd-and-acceptance-tests/2-summary.md)).
5. **ID와 추적**: 요구에 ID를 붙이고, 테스트·모니터링·설계 결정(ADR)에 그 ID를 단다.
6. **확인**: 시제품이나 데모로 이해관계자에게 "이게 맞나"를 묻는다(validation).
7. **변경 관리**: 요구가 바뀌면 매트릭스에서 영향받는 테스트를 찾아 함께 고친다.

### 2. 수용 기준 예

```text
  REQ-2 사용자는 결제 완료 후 24시간 이내이고 배송 시작 전인 주문을 취소할 수 있다.

  Given 결제가 2026-10-05 10:00에 완료되고 배송이 시작되지 않은 주문
  When  2026-10-06 10:01에 취소를 요청하면
  Then  요청은 거절되고, 주문 상태는 PAID로 남는다
```

- 이 기준을 쓰다 보면 질문이 생긴다. "24시간 정각은 포함인가?" 이 질문이 요구 문장을 다시 고치게 한다(v2 테스트 이름 `cancel_at_24h00m_after_payment_succeeds`가 그 답이다).

### 3. 테스트에 요구 ID 달기 (JUnit 5)

```java
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

class OrderCancelTest {
    @Test
    @Tag("REQ-2")   // JUnit 5의 태그: 빌드 도구에서 이 태그만 골라 실행할 수 있다
    void cancel_at_24h01m_after_payment_is_rejected() {
        // ...
    }
}
```

- 태그를 쓰면 "REQ-2가 바뀌었으니 REQ-2 테스트만 먼저 돌린다"가 가능하다. Maven Surefire는 `-Dgroups=REQ-2`로 태그를 고른다.
- 실험의 `@Req`는 이를 흉내 낸 단순 표식이다. 실제 프로젝트에서는 `@Tag`나 자체 애너테이션 + 리포트 생성기를 쓴다.

### 4. 진단 — 매트릭스 읽기

| 매트릭스에서 보이는 것 | 뜻 | 할 일 |
|---|---|---|
| 테스트 0개인 기능 요구 | 테스트가 아직 없음 또는 모호 | 문장 고치기 → 테스트 |
| 테스트 0개인 비기능 요구 | 단위 테스트 밖의 확인 수단이 필요하거나 아직 없음 | 배포 전 부하·성능 테스트, 운영 SLO·대시보드 중 맞는 것을 정해 링크 |
| 고아 테스트 | 요구 삭제 후 남은 테스트, 또는 ID 오타 | 지우거나 요구 복원 |
| 한 요구에 테스트가 아주 많음 | 요구가 단일하지 않음 | 요구 쪼개기 |

## 장애 시나리오와 대처

### 1. 모호 요구 → 구현 후 재작업 (⚠)

- 현상: 출시 데모에서 "이건 우리가 말한 게 아닌데요".
- 보이는 형태: 요구 문서에 "빠르게·쉽게·적절히"가 남아 있다. 해당 요구의 테스트가 없다. 같은 기능의 재작업 티켓이 생긴다.
- 원인: 요구가 검증 가능한 문장이 아니어서, 각자 다른 해석으로 진행했다.
- 대처: 문장을 측정 대상·조건·임계값이 있는 형태로 고친다. 수용 기준(Given-When-Then)을 개발 전에 합의한다. 모호어 검사를 리뷰 체크리스트에 넣는다.

### 2. 비기능 요구 누락 (⚠)

- 현상: 기능 테스트는 다 통과했는데, 출시 직전 부하 테스트에서 응답이 크게 느리다. 또는 감사에서 개인정보 보관 기한 위반이 나온다.
- 보이는 형태: 요구 목록에 비기능 항목이 0개다. 또는 실험 v1처럼 속도 요구를 기능 요구로 잘못 적어 "비기능 0"으로 보인다. 아키텍처 결정에 성능·가용성 근거가 없다.
- 원인: 도출 단계에서 사용자 기능만 물었다. 운영·보안·법무 이해관계자를 빼먹었다.
- 대처: 이해관계자 목록에 운영·보안·법무를 넣는다. 품질 속성 체크리스트(성능·가용성·보안·보관 기한·관측성)로 도출한다. 비기능 요구에는 테스트 대신 부하 테스트·SLO·감사 절차를 추적 매트릭스에 잇는다.

### 3. 추적이 끊겨 변경 영향을 모름

- 현상: 정책이 "24시간 → 48시간"으로 바뀌었는데 일부 화면·배치는 옛 기준으로 동작한다.
- 보이는 형태: 같은 규칙의 상수가 여러 곳에 있다. 요구 ID로 검색해도 아무것도 안 나온다.
- 원인: 요구와 코드·테스트 사이에 연결이 없어 영향 범위를 찾지 못했다.
- 대처: 요구 ID를 테스트 태그·커밋 메시지·설정 키에 단다. 규칙 값을 한 곳에 모은다. 변경 시 매트릭스로 영향 테스트를 찾는다.

### 4. 범위 크리프·골드 플레이팅

- 현상: 일정이 계속 밀리는데 요구 목록은 계속 길어진다. 또는 아무도 요청하지 않은 기능이 들어간다.
- 보이는 형태: 추적 매트릭스에서 위쪽(이해관계자 필요)에 연결되지 않는 요구·코드가 있다.
- 원인: 요구 변경이 기준선·변경 관리 없이 들어온다. 개발자가 필요하리라 짐작한 것을 넣는다.
- 대처: 요구마다 "왜(부모 필요)"를 적게 한다. 변경은 우선순위와 일정 영향을 함께 보고 받는다(12번 추정과 연결).

### 5. 잘 쓴 요구가 틀린 시스템을 가리킴

- 현상: 요구대로 정확히 만들었는데 사용자가 쓰지 않는다.
- 보이는 형태: 요구 검증(문장 품질)은 통과했다. 시제품이나 데모 없이 바로 구현했다.
- 원인: verification만 하고 validation을 안 했다.
- 대처: 작은 시제품·데모로 이해관계자 확인을 일찍 받는다. 반복형 수명 주기([01번](../01-lifecycle-and-agile/2-summary.md))의 스프린트 리뷰가 이 자리다.

## 핵심 문장

- 요구는 필요와 제약을 확인할 수 있는 문장으로 옮긴 것이다. 확인할 수 없으면 아직 요구가 아니라 바람이다.
- 모호어("빠르게·적절히·가능하면")를 지우고 대상·조건·임계값을 넣으면, 경계값 테스트가 생긴다.
- 검증(잘 썼나)과 확인(맞는 것인가)은 다르다. 둘 다 해야 한다.
- 비기능 요구는 가장 자주 빠지고, 단위 테스트가 아니라 부하 테스트·SLO로 확인하는 경우가 많다.
- 추적 매트릭스는 요구 → 테스트 역색인이다. 테스트 연결이 없는 요구와 고아 테스트를 집합 차로 찾는다.

## 관련 주제·근거

- 선행: [01-lifecycle-and-agile](../01-lifecycle-and-agile/2-summary.md).
- 후속: [12-estimation-and-planning](../12-estimation-and-planning/2-summary.md) · [11-documentation-practices](../11-documentation-practices/2-summary.md).
- 연결: [testing/06-outside-in-tdd-and-acceptance-tests](../../testing/06-outside-in-tdd-and-acceptance-tests/2-summary.md) · [testing/07-test-design-techniques](../../testing/07-test-design-techniques/2-summary.md) · [software-design/46-quality-attributes-and-tradeoffs](../../software-design/46-quality-attributes-and-tradeoffs/2-summary.md) · [reliability/02-slo-sli-error-budget](../../reliability/02-slo-sli-error-budget/2-summary.md) · [domain-modeling/03-ubiquitous-language](../../domain-modeling/03-ubiquitous-language/) · [software-design/47-architecture-decision-records](../../software-design/47-architecture-decision-records/2-summary.md).
- 근거
  - ISO/IEC/IEEE 29148:2018 — 3장 정의(3.1.19 requirement, 3.1.20 elicitation, 3.1.21 requirements engineering, 3.1.22 management, 3.1.23 traceability, 3.1.24 traceability matrix, 3.1.25 validation, 3.1.26 verification, 3.1.28 stakeholder)와 목차(5.2.5~5.2.8, 5.3)는 iTeh 공개 견본 PDF로 확인: https://standards.iteh.ai/catalog/standards/iso/8cf2bc2b-8b5e-4907-a82a-d1c5676c9e85/iso-iec-ieee-29148-2018
  - 5.2.5 특성 9가지·5.2.6 집합 특성: 2차 출처로 확인 — https://www.modernrequirements.com/blogs/iso-29148-explained/ . 요구 냄새 범주: arXiv 2403.17479 "Natural Language Requirements Testability Measurement Based on Requirement Smells" 표 3(Femmer 외의 목록, 29148:2011 기반) — https://arxiv.org/abs/2403.17479
  - SWEBOK v4 1장 Software Requirements(장 번호는 https://www.computer.org/education/bodies-of-knowledge/software-engineering 의 장별 웨비나 목록으로 확인, 절 이름 `[?]`).
  - JUnit 5 `@Tag`·Maven Surefire `groups`: JUnit 5 User Guide "Tagging and Filtering", Maven Surefire "Using JUnit 5 Platform" 문서.
- 실험 목록
  - 요구 고쳐 쓰기 전후 추적 매트릭스·모호어 검사: `Trace.java` + 입력 `v1/`·`v2/`(requirements.txt, tests/*.java), `docker run eclipse-temurin:21-jdk java Trace.java v1|v2`, JDK 21.0.12(temurin), `--network none`.
