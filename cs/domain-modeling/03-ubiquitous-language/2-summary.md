# domain-modeling/03-ubiquitous-language — 코드·대화·문서의 단일 언어 — 정리 (힌트)

## 해결하는 문제

같은 단어를 사람마다 다른 뜻으로 쓰면, 요구는 맞게 전달됐다고 믿는데 구현은 다른 것을 만든다. 아무도 틀렸다고 느끼지 못한다는 것이 문제다.

쉬운 예: 이사 날 "짐 다 뺐어요".

```text
  이삿짐 센터:  "다 뺐다" = 트럭에 다 실었다
  집주인:       "다 뺐다" = 집이 비어 청소까지 끝났다
  세입자:       "다 뺐다" = 내 물건은 다 나갔다(냉장고는 다음 주)
        │
        ▼  보증금 반환 조건 "짐을 다 빼면 돌려준다"
  각자 조건이 충족됐다고 생각 → 분쟁
```

똑같은 구조다.\
결제팀은 "주문 완료"를 "결제가 끝났다"로, 물류팀은 "배송이 끝났다"로 쓴다. 코드에는 `OrderStatus.COMPLETED` 하나가 있고 두 흐름이 모두 그것을 켠다. CS팀 정책 "완료된 주문은 환불 대신 반품"이 코드에 들어가면, 배송 전 주문까지 환불이 거절된다. 아래 실험에서 주문 6건 중 3건이 그렇게 잘못 거절됐다.

- *보편 언어(ubiquitous language)*: Evans가 『DDD』 2장에서 쓴 말. 개발자와 도메인 전문가가 대화·문서·그림·**코드**에서 함께 쓰는, 도메인 모델에 바탕을 둔 하나의 언어.
- *도메인 전문가(domain expert)*: 그 업무를 깊이 아는 사람(정산 담당자, 물류 관리자 등).

## 동작·원리

### 1. 언어가 갈라진 프로젝트 — 번역이 곳곳에 낀다

```text
  도메인 전문가 ──"완료"──▶ [기획자: 번역] ──"status=COMPLETED"──▶ 개발자 ──▶ 코드
       ▲                                                                 │
       └──────────── [개발자: 역번역] ◀── "COMPLETED가 켜진 주문" ◀──────┘
  번역 지점마다 뜻이 조금씩 바뀌고, 바뀐 줄 아무도 모른다
```

- Evans 2장(2003 최종 원고 대조)
  - 공통 언어가 없으면 개발자는 전문가를 위해, 전문가는 개발자와 다른 전문가 사이에서 번역해야 한다. 번역은 부정확하고 이해의 단절을 숨긴다.
  - 몇몇이 양쪽 말을 다 하게 되지만 정보 흐름의 병목이 되고 번역도 정확하지 않다.
  - 서로 다른 사람이 같은 용어를 다르게 쓰면서 그 사실을 모르는 균열(schism)이 생기고, 맞물리지 않는 소프트웨어가 된다.
  - "Translation blunts communication and makes knowledge crunching anemic."

### 2. 보편 언어 — 모델이 언어의 뼈대

```text
            도메인 전문가의 용어          개발자의 기술 용어
                 ┌─────────┐          ┌─────────┐
                 │ 업무 은어 │          │ 설계 기술 │
                 │    ┌────┼──────────┼────┐    │
                 └────┼────┘ 보편 언어  └────┼────┘
                      │ 모델의 클래스·연산 이름│
                      │ 규칙, 패턴 이름        │
                      │ 바운디드 컨텍스트 이름 │
                      └──────────────────────┘
```

- Evans 2장 그림 "UBIQUITOUS LANGUAGE is Cultivated in the Intersection of Jargons"를 단순화했다.
- 어휘: 클래스와 주요 연산의 이름, 모델에 명시된 규칙, 팀이 쓰는 패턴 이름, 컨텍스트 맵 같은 큰 구조의 이름(Evans 2장).
- 처방(DDD Reference 2015 「Ubiquitous Language」의 "Therefore")
  - 모델을 언어의 뼈대로 쓴다. 팀 안의 모든 소통과 **코드**에서 그 언어를 끈질기게 쓴다.
  - 바운디드 컨텍스트 안에서 그림·글·특히 말에 같은 언어를 쓴다.
  - "Recognize that a change in the language is a change to the model." — 용어가 바뀌면 모델이 바뀐 것이다. 클래스·메서드·모듈 이름을 새 모델에 맞게 리팩터링한다.
- 2003년 책은 "보편 언어는 하나의 모델을 전제한다"고 쓰고 여러 모델의 공존은 14장(Maintaining Model Integrity)으로 넘긴다. 2015 Reference는 처방 자체에 "Within a bounded context"를 넣었다. 한 단어가 컨텍스트마다 다른 뜻을 갖는 경우는 16번(바운디드 컨텍스트)이 다룬다.

### 3. 소리 내어 모델링하기 — 문장이 매끄러워질 때까지

- Evans 2장 「Modeling Out Loud」의 예(화물 경로 탐색)

```text
  1. Routing Service에 출발지·도착지·도착 시각을 주면 기항지를 찾아서… 음… DB에 넣는다.
  2. 출발지, 도착지 같은 것들이 Routing Service로 들어가고, 필요한 게 다 든 Itinerary가 나온다.
  3. A Routing Service finds an Itinerary that satisfies a Route Specification.
```

- 1번은 기술 절차(DB에 넣는다), 2번은 뭉뚱그린 데이터, 3번은 모델의 요소(서비스·일정·경로 명세)와 관계로 말한다. 3번이 보편 언어로 한 문장이다.
- 거친 곳은 말로 하면 잘 들린다(Evans). 전문가는 어색하거나 부족한 용어에 반대하고, 개발자는 설계를 넘어뜨릴 모호함·불일치를 찾는다(DDD Reference 2015, Fowler bliki "UbiquitousLanguage" 2006-10-31 인용).

### 실험: 한 단어 두 뜻, 단위 없는 숫자, 용어집 검사

- 환경: JDK 21(`eclipse-temurin:21-jdk`, openjdk 21.0.12, `--cpus=2`, 네트워크 없음), 2026-10-03.

**A. "완료" 한 단어를 두 흐름이 쓴 코드 vs 용어집대로 나눈 코드**

```java
// Overloaded: 결제팀·물류팀이 같은 COMPLETED를 켠다
static Status statusOf(Order o) {
    Status s = Status.CREATED;
    if (o.paid()) s = Status.COMPLETED;          // 결제팀: "결제 끝 = 완료"
    if (o.delivered()) s = Status.COMPLETED;     // 물류팀: "배송 끝 = 완료"
    return s;
}
// CS 정책 "완료(= 배송까지 끝난) 주문은 환불 대신 반품"을 코드로 옮김
static boolean refundAllowed(Order o) { return statusOf(o) != Status.COMPLETED; }

// Explicit: 용어집 — 결제됨(PAID)·배송 완료(DELIVERED)
enum Status { PLACED, PAID, DELIVERED }
boolean refundAllowed() { return status() == Status.PAID; }
```

- 데이터: 주문 6건 — 결제·배송 끝 2건, 결제만 끝 3건, 아무것도 안 됨 1건.

(실험, JDK 21 temurin, 2026-10-03)

```text
COMPLETED 주문 수(대시보드)  = 5
결제팀이 기대한 '결제된 주문' = 5
물류팀이 기대한 '배송 끝 주문' = 2
배송 전인데 환불 거절된 주문 = 3  (CS 정책 의도: 배송 끝난 주문만 환불 대신 반품)
---
PAID 이상(결제됨) = 5
DELIVERED       = 2
환불 가능(PAID)  = 3
```

- 관찰: 대시보드의 "완료 5건"은 결제팀 숫자와 같다(이 데이터에서 배송된 주문은 모두 결제된 주문이라 COMPLETED = 결제된 주문이 된다). 물류팀이 기대한 2건과는 다르다. 정책 코드는 배송 전 3건을 환불 거절했다. 용어를 나눈 코드에서는 같은 3건이 환불 가능이다.

**B. 단위가 이름·타입에 없는 숫자**

```java
static long retryAtMillis(long now, long delay) { return now + delay; }          // delay의 단위는?
static long retryAt(long nowMillis, Duration delay) { return nowMillis + delay.toMillis(); }
```

(실험, JDK 21 temurin, 2026-10-03)

```text
delay=5 (호출자 의도 5초) → 5 ms 뒤 재시도
Duration.ofSeconds(5)    → 5000 ms 뒤 재시도
```

(실험, JDK 21 temurin, 2026-10-03) `Duration`을 받는 메서드에 `5`를 넘기면 `javac`

```text
UnitsBad.java:4: error: incompatible types: int cannot be converted to Duration
    public static void main(String[] a) { System.out.println(retryAt(0, 5)); }   // 단위 없는 숫자를 넘김
                                                                        ^
```

- 관찰: 단위가 빠진 `long`은 1000배 어긋나도 컴파일·실행이 모두 된다. 단위를 타입으로 묶으면 같은 실수가 컴파일 오류가 된다.

**C. 용어집 금지어 검사 — 용어집을 테스트로**

```text
# glossary.txt — 주문 컨텍스트: 금지어=권장어
complete=PAID 또는 DELIVERED 중 하나로
done=PAID 또는 DELIVERED 중 하나로
finish=markDelivered
```

(실험, JDK 21 temurin, 2026-10-03) `GlossaryCheck`가 도메인 소스 줄마다 금지어(대소문자 무시)를 찾는다

```text
  domain_before/Order.java:2 'complete' → PAID 또는 DELIVERED 중 하나로
  domain_before/Order.java:2 'done' → PAID 또는 DELIVERED 중 하나로
  domain_before/Order.java:3 'complete' → PAID 또는 DELIVERED 중 하나로
  domain_before/Order.java:4 'finish' → markDelivered
  domain_before 금지어 4건 → FAIL
  domain_after 금지어 0건 → PASS
```

- 관찰: 금지어 검사는 부분 문자열 일치라 `COMPLETED`도 `complete`로 잡는다. 반대로 `completedAt`처럼 허용하고 싶은 이름도 잡히므로 예외 목록이 필요하다. 이 검사는 "용어를 바꾸기로 했다"는 합의를 코드에서 되돌아가지 않게 막는 장치이지, 언어를 만들어 주지는 않는다.

## 쓰이는 자료구조·알고리즘

- **용어집 = 사전(맵)** — `용어 → {정의, 코드 이름, 금지 동의어, 담당 컨텍스트, 예시}`. 컨텍스트가 여럿이면 키는 `(컨텍스트, 용어)` 쌍이다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **금지어 검색 = 문자열 매칭** — 실험 C는 금지어마다 정규식으로 줄을 훑는다(금지어 k개 × 줄 n개). 금지어가 많으면 여러 패턴을 한 번에 찾는 Aho–Corasick을 쓴다. [algorithm/26-aho-corasick](../../algorithm/26-aho-corasick/2-summary.md)
- **용어 사용처 = 역색인** — "이 용어가 어느 파일·문서에 나오나"는 용어 → 위치 목록의 역색인으로 답한다(IDE 검색·`grep -rn`). [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)
- **단위 = 타입 태그** — `Duration`·`Money`처럼 값에 단위·통화를 붙여 컴파일러가 섞임을 막는다. [software-design/24-types-as-invariants](../../software-design/24-types-as-invariants/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 용어를 모으고 모호한 것에 표시한다

- 요구 회의·CS 문의·운영 매뉴얼에서 명사(주문, 결제, 정산)와 동사(완료하다, 취소하다)를 모은다.
- 같은 단어를 팀마다 어떻게 쓰는지 묻는다. "완료는 정확히 언제 참이 되나요?"처럼 **참이 되는 시점·조건**으로 묻는다.

### 2. 용어집을 짧게 만든다

| 용어 | 정의(참이 되는 조건) | 코드 이름 | 쓰지 않는 말 | 컨텍스트 |
|---|---|---|---|---|
| 결제됨 | PG 승인 응답을 받고 결제 기록이 저장됐다 | `OrderStatus.PAID`, `Order.pay()` | 완료, done | 주문 |
| 배송 완료 | 택배사가 수령 확인 이벤트를 보냈다 | `OrderStatus.DELIVERED`, `markDelivered()` | 완료, finish | 주문 |
| 주문 금액 | 할인 뒤, 배송비 전, 원 단위 정수 | `Order.itemsTotal(): Money` | amount, price | 주문 |

- 정의에는 단위·기준 시각·포함/제외를 넣는다("할인 뒤, 배송비 전, 원 단위").
- 용어집은 코드 저장소 안(예: `docs/glossary.md`)이나 위키에 두고, 코드 이름 칸이 실제 식별자와 맞는지 리뷰 때 본다.

### 3. 코드 이름을 용어에 맞춘다

```java
/** 결제됨: PG 승인 응답을 받고 결제 기록이 저장됐다. 배송 여부와 무관하다. */
public enum OrderStatus { PLACED, PAID, DELIVERED, CANCELLED }

public class Order {
    public void pay(PaymentApproval approval) { … }      // "결제하다"
    public void markDelivered(Instant at) { … }           // "배송 완료 처리"
    public Money itemsTotal() { … }                       // "주문 금액" — 단위는 Money가 들고 다닌다
}
```

- 용어가 바뀌면 이름을 바꾼다. Evans는 이를 "언어의 변화 = 모델의 변화"로 본다. 이름만 그대로 두면 다음 사람이 옛 뜻으로 읽는다.
- DB 컬럼·이벤트 이름처럼 바꾸기 비싼 외부 계약은 매핑 계층에서 번역하고, 용어집에 "외부 이름" 칸을 둔다.

### 4. 테스트 이름과 시나리오도 같은 언어로

```java
@Test void 결제됨_주문은_배송_전이면_환불할_수_있다() { … }
@Test void 배송_완료_주문은_환불_대신_반품_절차로_간다() { … }
```

- Evans는 전문가가 모델의 언어로 유스케이스를 쓰고 인수 테스트를 명세할 수 있다고 적는다. 테스트 이름을 전문가가 읽고 "맞다/틀리다"를 말할 수 있어야 한다.

### 5. 되돌아가지 않게 검사한다

- 실험 C처럼 금지어 검사를 CI에 건다. 예외 목록(허용 식별자)을 함께 관리한다.

## 장애 시나리오와 대처

### 1. 같은 단어 다른 뜻 — 요구와 구현 불일치 (⚠ 커리큘럼 "주문 완료")

- **현상**: 정책이 의도와 다른 주문에 적용된다. 팀마다 대시보드 숫자가 다르다.
- **보이는 형태**: "완료 주문 수"가 결제팀 집계와 맞고 물류팀 집계와 다르다(실험 A: 5 vs 2). CS 문의 "배송도 안 됐는데 환불이 안 된다"(실험 A: 3건).
- **원인**: 하나의 상태 값이 두 뜻을 겸했다. 정책 문장의 "완료"와 코드의 `COMPLETED`가 서로 다른 것을 가리켰다.
- **대처**: 정의를 "참이 되는 조건"으로 합의해 용어를 나눈다(`PAID`·`DELIVERED`). 기존 데이터는 원천 기록(결제·배송 이벤트)으로 다시 분류한다. 두 팀이 정말 다른 모델을 쓴다면 컨텍스트를 나누고 경계에서 번역한다(16번).

### 2. 단위 누락 (⚠ 커리큘럼)

- **현상**: 값이 몇 배·몇천 배 어긋나는데 오류가 나지 않는다. 재시도가 너무 빨라 외부 API를 두들기거나, 금액이 100배 청구된다.
- **보이는 형태**: 설정 `retry.delay=5`가 5 ms로 동작(실험 B). 로그의 숫자에 단위가 없다.
- **원인**: 단위가 이름·타입·용어집 어디에도 없었다. 만든 쪽과 쓰는 쪽이 서로 다른 단위를 가정했다.
- **대처**: 단위를 타입(`Duration`·`Money`)이나 이름(`delayMillis`)에 넣는다. 설정은 단위 접미사를 받는 형식(예: `5s`)을 쓴다. 용어집 정의에 단위를 적는다.
- 실사건: Mars Climate Orbiter(1999-09-23 소실). NASA 사고조사위원회 1단계 보고서(1999-11-10)는 근본 원인을 지상 소프트웨어 파일 "Small Forces"가 미터 단위를 쓰지 않은 것으로 판정했다. 인터페이스 명세는 뉴턴·초(N-s)를 요구했는데 데이터는 파운드힘·초(lbf-s)로 전달됐고, 받는 쪽은 미터 단위로 가정해 추력 효과를 4.45배 작게 잡았다. 상세는 [28-dm-incidents](../28-dm-incidents/2-summary.md).

### 3. 사람 번역기가 병목

- **현상**: 특정 한 사람이 회의마다 "그러니까 개발 쪽 말로는…"을 한다. 그 사람이 휴가 가면 요구 해석이 멈춘다.
- **보이는 형태**: 요구 문서와 티켓·코드의 용어가 다르다. 같은 질문이 반복된다.
- **원인**: 팀에 언어가 둘이다. Evans가 말한 "양쪽 말을 다 하는 몇 명이 병목이 되고 번역이 부정확한" 상태.
- **대처**: 전문가와 개발자가 함께 쓰는 용어집을 만들고, 회의·티켓·코드에서 같은 말을 쓴다. 시나리오를 모델 요소로 소리 내어 따라가 본다(Modeling Out Loud).

### 4. 말은 바뀌었는데 코드 이름은 그대로

- **현상**: 회의에서는 "예약"이라고 하는데 코드는 `Hold`, DB는 `reservation_tmp`. 신규 인원이 셋이 같은 것인지 모른다.
- **보이는 형태**: 용어집 "코드 이름" 칸과 실제 식별자가 다르다. 주석 "Hold = 예약(옛 이름)".
- **원인**: 용어 변경을 모델 변경으로 보지 않고 대화에서만 바꿨다.
- **대처**: 용어를 바꾸기로 하면 이름 변경 리팩터링을 같은 작업 단위에 넣는다. 외부 계약(테이블·이벤트)은 번역 계층에서 옛 이름을 받고, 금지어 검사로 새 코드에 옛 이름이 들어오지 않게 한다.

### 5. 전사 단일 용어를 강요

- **현상**: "고객"의 정의를 회사 전체에서 하나로 맞추려다 합의가 끝나지 않는다. 합의된 정의는 누구의 업무에도 정확히 맞지 않는다.
- **보이는 형태**: `Customer` 클래스에 필드가 수십 개, 팀마다 쓰는 필드가 다르다.
- **원인**: 보편 언어의 범위를 바운디드 컨텍스트가 아니라 조직 전체로 잡았다. DDD Reference 2015는 처방에 "Within a bounded context"를 명시한다.
- **대처**: 컨텍스트마다 언어를 따로 두고, 컨텍스트 사이 번역을 명시한다(16·18·19번).

## 핵심 문장

- 보편 언어는 모델을 뼈대로 한, 대화·문서·코드에 공통인 하나의 언어다. 범위는 바운디드 컨텍스트 하나다(DDD Reference 2015).
- 번역은 뜻을 흐리고 이해의 단절을 숨긴다(Evans 2장). 단절은 오류 없이 엉뚱한 결과로 드러난다.
- 실험에서 "완료" 한 상태가 결제·배송 두 뜻을 겸하자, 주문 6건 중 배송 전인 결제 주문 3건이 환불 거절됐다. 용어를 나눈 코드에서는 같은 3건이 환불 가능이었다.
- 단위가 빠진 숫자는 1000배 어긋나도 컴파일·실행된다. 단위를 타입에 넣으면 같은 실수가 컴파일 오류가 된다.
- 용어가 바뀌면 모델이 바뀐 것이다. 이름 변경 리팩터링까지 해야 끝난다.

## 관련 주제·근거

- 선행: [01-domain-vs-application-logic](../01-domain-vs-application-logic/2-summary.md)
- 연결
  - [04-entities-and-value-objects](../04-entities-and-value-objects/2-summary.md)(값 객체로 단위를 들고 다니기) · [12-time-money-and-units](../12-time-money-and-units/2-summary.md) · [16-bounded-contexts](../16-bounded-contexts/2-summary.md) · [18-context-mapping](../18-context-mapping/2-summary.md) · [19-anti-corruption-layer](../19-anti-corruption-layer/2-summary.md) · [20-event-storming](../20-event-storming/2-summary.md)(용어를 끌어내는 워크숍) · [28-dm-incidents](../28-dm-incidents/2-summary.md)(Mars Climate Orbiter)
  - [software-design/07-naming](../../software-design/07-naming/2-summary.md) — 이름이 추상화의 첫 표현
  - [software-design/24-types-as-invariants](../../software-design/24-types-as-invariants/2-summary.md) — 원시 타입 집착 제거
  - [languages/java/syntax/52-duration-period-formatter](../../../languages/java/syntax/52-duration-period-formatter/2-summary.md)
  - 원본 [domain-vs-application-logic](../domain-vs-application-logic/2-summary.md) 「값 객체에 넣는 규칙」 — "타입이 곧 문서"
- 근거
  - Evans 『Domain-Driven Design』(2003) 2장 Communication and the Use of Language(UBIQUITOUS LANGUAGE, Modeling Out Loud, One Team One Language, Documents and Diagrams) — 2003-04-15 최종 원고 PDF 대조, 장 구성은 <https://www.dddcommunity.org/uncategorized/toc/>
  - Evans 『DDD Reference』(2015) 「Ubiquitous Language」 3~4쪽(처방 "Therefore"는 4쪽) <https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf>
  - Fowler bliki "UbiquitousLanguage"(2006-10-31) <https://martinfowler.com/bliki/UbiquitousLanguage.html>
  - NASA Mars Climate Orbiter Mishap Investigation Board Phase I Report(1999-11-10) <https://llis.nasa.gov/llis_lib/pdf/1009464main1_0641-mr.pdf>
- 실험 목록
  - A. "완료" 단일 상태 vs `PAID`·`DELIVERED` — 주문 6건 집계(5 / 5 / 2)와 정책 오적용 3건
  - B. 단위 없는 `long` delay(5 ms) vs `Duration.ofSeconds(5)`(5000 ms), `Duration` 인자에 `int` 전달 시 `javac` 오류
  - C. 용어집 금지어 검사 — 이전 4건 FAIL, 이후 0건 PASS
  - 공통: JDK 21.0.12(temurin), `--cpus=2`·네트워크 없음
