# domain-modeling-basic/18-shipping-fee — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

⚠️ 질문 목록은 Claude 초안(2026-09-15) — 원본 요구사항·생각해볼 것 이관 + 파생 질문. 본인 검토 후 이 줄 삭제

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄. 옆으로 묶지 않고 아래로 늘어놓는다.
     문제(A)는 원문 요구사항/javadoc/TODO 를 코드블록으로 먼저 두고 그 아래에 질문을 단다.
     도메인 모델링의 핵심 질문형: "이 한 줄 요구사항에 안 들어 있는 결정은 무엇인가" -->

### A. 과제 (Shipping 의 TODO 1~4)

#### 1. 챕터 지문 — 말로 된 요구사항

```text
"5 만원 이상 무료 배송" 은 한 줄이다. 그 한 줄에 안 적힌 것이 넷이다.

  1. 5 만원이 할인 전인가 할인 후인가
  2. 도서산간 추가비도 무료가 되나
  3. 판매자가 여럿이면 각각인가 합쳐서인가
  4. 일부를 취소해서 5 만원 아래가 되면 배송비를 다시 받나
```

- 이 한 줄에서 "5만원"과 "이상"과 "무료"가 각각 무엇을 안 정하고 있는가?
- 넷 말고 이 지문이 침묵하는 것이 더 있는가(전부 취소하면? 기준이 없으면?)?
- 이 챕터는 그 침묵들을 어디에 모아 두었는가?
- `ShippingPolicy` 필드 여섯 개를 결정 번호와 짝지을 수 있는가?

#### 2. TODO 1 — thresholdAmount (무료 기준에 쓰는 금액)

```java
/** 무료 기준에 쓰는 금액. 취소된 줄은 안 센다. */
public static int thresholdAmount(List<OrderLine> lines, ShippingPolicy policy) {
    throw new UnsupportedOperationException("TODO 1");
}
```

- 이 함수가 정책에서 보는 필드는 무엇 하나인가?
- 할인 후 기준이면 줄마다 무엇을 더하고, 할인 전 기준이면 무엇을 더하는가?
- 정가 60,000·할인 15,000 한 줄에서 두 기준의 값은 각각 얼마인가?
- 취소된 줄을 빼먹고 세면 손님이 어떤 길을 찾아내는가?
- 배송비 판정에 쓰는 금액과 실제 결제 금액이 달라도 되는가?

#### 3. TODO 3 — feeForGroup (한 묶음의 배송비, 순서가 계약)

```java
/** 한 묶음의 배송비. */
private static int feeForGroup(List<OrderLine> lines, ShippingPolicy policy, boolean remote) {
    throw new UnsupportedOperationException("TODO 3");
}
// javadoc(feeFor): 순서가 계약이다. 무료 여부를 먼저 보고 도서산간을 붙인다.
//                  반대로 하면 무료 배송인데 도서산간만 남는 경우를 표현할 수 없다.
```

- 이 메서드가 가장 먼저 걸러야 하는 경우 둘은 무엇인가?
- 빈 목록과 전부 취소를 0원으로 처리하지 않으면 어떤 손님이 무엇을 내는가?
- 무료 판정식에서 `freeThreshold() > 0` 을 앞에 둔 이유는 무엇인가?
- 기준 0을 "0원 이상이면 무료"로 읽으면 어떤 일이 벌어지는가?
- 기준 비교는 `>=` 인가 `>` 인가, 틀리면 어떤 손님이 가장 많이 걸리는가?
- 도서산간 추가비를 붙이는 조건을 한 줄로 쓰면 무엇인가?
- "무료 여부 먼저, 도서산간 나중"의 순서를 뒤집으면 표현할 수 없게 되는 경우는 무엇인가?
- STANDARD 정책에서 6만원짜리 주문을 도서산간으로 보내면 배송비는 얼마인가?

#### 4. TODO 2 — feeFor (판매자별로 나눌지는 정책이 정한다)

```java
public static int feeFor(List<OrderLine> lines, ShippingPolicy policy, boolean remote) {
    throw new UnsupportedOperationException("TODO 2");
}
```

- `perSeller` 가 거짓이면 이 메서드는 무엇을 하는가?
- 참이면 줄들을 무엇으로 묶고, 묶음마다 무엇을 부르는가?
- 묶을 때 `HashMap` 이 아니라 `LinkedHashMap` 을 쓴 이유는 무엇인가?
- 판매자별 판정은 "전체를 보고 한 번에" 하는가 "묶음마다 따로" 하는가?
- S1 60,000 + S2 10,000 을 판매자별로 계산하면 얼마인가?
- 도서산간 추가비는 판매자별이면 몇 번 붙는가, 그게 맞는가?

#### 5. TODO 4 · feeDeltaAfterCancel

```java
/** 무료 배송인가. */
public static boolean isFree(List<OrderLine> lines, ShippingPolicy policy) {
    throw new UnsupportedOperationException("TODO 4");
}

/** 일부를 취소한 뒤의 배송비 차액. 양수면 더 받아야 한다. (주어짐) */
public static int feeDeltaAfterCancel(
        List<OrderLine> before, List<OrderLine> after, ShippingPolicy policy, boolean remote) {
    return feeFor(after, policy, remote) - feeFor(before, policy, remote);
}
```

- `isFree` 는 `feeFor` 가 0인지 보는 것과 같은가 다른가?
- 도서산간 주문에서 `isFree` 가 참인데 배송비가 0이 아닐 수 있는가?
- `feeDeltaAfterCancel` 이 양수라는 것은 무슨 뜻인가?
- 이 차액을 청구할지 말지를 이 함수가 정하는가?
- "계산도 안 하면 정할 수가 없다"는 말이 설계에 주는 지침은 무엇인가?

#### 6. 계약으로 주어진 OrderLine·ShippingPolicy

```java
public record OrderLine(String seller, int listPrice, int discount, boolean cancelled) {
    // discount > listPrice 면 예외. payable() = listPrice - discount. cancel() 은 새 객체를 만든다.
}
public static ShippingPolicy standard() {
    return new ShippingPolicy(3_000, 50_000, 3_000, false, true, false);
}
```

- `cancel()` 이 필드를 바꾸지 않고 새 객체를 돌려주는 설계의 이점은 무엇인가?
- 할인이 정가를 넘는 줄을 생성자에서 막으면 배송비 계산에서 무엇이 보장되는가?
- `standard()` 의 여섯 값을 말로 풀면 어떤 정책인가?
- 표준 정책이 `freeAppliesToSurcharge = false` 인 것은 무엇을 뜻하고, 그러면 화면에 무엇을 써야 하는가?

### B. 개념

#### 7. 측정 하나 — 기준 금액을 할인 후로 보면

- 할인 후 기준과 할인 전 기준의 무료 배송 건수·배송비 합계는 각각 얼마인가?
- 2,000건 중 갈리는 건수는 몇 건이고, 왜 그것뿐인가?
- 그 231건은 어떤 손님인가?
- "갈리는 비율이 낮은 것과 문제가 작은 것은 다르다"를 이 수치로 설명하면?

#### 8. 측정 둘 — 판매자별로 나누면

- 주문 전체 기준과 판매자별 기준의 배송비 합계는 각각 얼마이고 몇 배인가?
- 2,000건 중 몇 건이 갈리는가?
- 네 결정 중 금액이 가장 큰 것은 무엇인가?
- 판매자별이 "손님이 가장 이해하기 어려운" 이유는 무엇인가?

#### 9. 측정 셋 — 도서산간

- 추가비를 받는 정책과 안 받는 정책의 합계 차이는 얼마이고 몇 건이 갈리는가?
- 건당 차이는 얼마인가?
- 금액이 작은데 항의가 큰 이유는 무엇인가?
- 그래서 화면에 뭐라고 써야 하는가?

#### 10. 측정 넷 — 부분 취소

- 두 줄 이상인 주문 1,495건에서 한 줄을 취소하면 몇 건이 무료에서 떨어지는가?
- 그때 추가로 생기는 배송비는 얼마인가?
- 이 돈을 안 받으면 어떤 길이 남고, 받으면 무슨 일이 생기는가?
- 이 챕터가 "어느 쪽이 맞다"고 말하지 않고 무엇만 요구하는가?

#### 11. 측정 다섯 — 할인이 없으면 결정 하나가 사라진다

- 모든 줄의 할인이 0이면 2,000건이 왜 전부 같은 답을 내는가?
- "개발할 때 만드는 주문은 대개 할인이 없다"는 문장이 테스트 설계에 주는 경고는 무엇인가?
- 17번의 "할인이 하나면 세 결정이 사라진다"와 같은 구조인가?

#### 12. 생각해볼 것 (원본 README 이관)

- 17번의 할인 순서가 여기 기준 금액에 그대로 흘러든다 — 두 박스가 한 줄로 이어져 있는가?
- 판매자별 배송비를 손님 화면에 어떻게 보여주는가, 줄마다인가 합계인가?
- 반품 배송비는 여기 계산에 들어가는가 별도인가?
- 무료 배송 기준을 넘기려고 담은 상품만 취소하는 것을 어떻게 볼 것인가?

#### 13. 연결

- 15번 쿠폰의 "최소 금액"과 여기 "기준은 이상이다"는 왜 같은 자리인가?
- 16·17·18 세 챕터가 공통으로 가르치는 한 문장은 무엇인가?
- 무료 배송을 17번의 할인 종류로 모델링하면 무엇이 꼬이는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
