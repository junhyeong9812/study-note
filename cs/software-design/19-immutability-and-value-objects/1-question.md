# software-design/19-immutability-and-value-objects — 질문

## 질문

1. (왜) 값 객체를 여러 곳이 공유할 때 가변이면 무엇이 일어나나? Fowler가 붙인 이름은?
2. (예측) 요금 캐시가 가변 `Money(3000)`을 돌려주고, 요청 A가 `add(500)`(자기를 바꾸고 `this` 반환), 요청 B가 같은 키를 조회한다. A·B·캐시 값은? 불변 `Money`라면?
3. (그림) `HashSet`에 `Key("A")`를 넣고 필드를 "B"로 바꾼 뒤 `contains(k)`·`contains(new Key("A"))`·`remove(k)`가 어떻게 되는지 버킷 그림으로 설명하라.
4. (경계) Java record는 어디까지 불변인가? `List` 구성 요소를 가진 record를 진짜 불변으로 만드는 방법과, `Collections.unmodifiableList`가 그 답이 아닌 이유는?
5. (예측) 스레드 4개가 각 5만 번 공유 `long[]`을 증가시키는 것과 `AtomicReference<Money>`를 `updateAndGet(m -> m.add(1))`하는 것의 결과는? 정확성을 만든 것은 불변인가?
6. (경계) 불변의 비용은 무엇이고, 큰 컬렉션에서 그 비용을 줄이는 구조는? 실험의 `v2.tail()==v1`이 보여 주는 것은?
7. (예측) `BigDecimal total = new BigDecimal("100"); total.add(new BigDecimal("5"));` 뒤 `total`은? `new BigDecimal("2.0")`과 `"2.00"`을 담은 record `Money` 둘은 `equals`인가?
8. (연결) 무엇을 불변으로 만들고, 무엇은 가변으로 둘 수 있나? 그때 가변 쪽이 지킬 규칙은?
9. (장애 진단) 어느 순간부터 모든 고객 요금에 할증이 붙고, 재시작하면 잠시 정상이다. 에러 로그는 없다. 무엇을 의심하고 어떻게 확인·수정하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
