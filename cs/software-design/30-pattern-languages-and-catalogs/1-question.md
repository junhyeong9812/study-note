# software-design/30-pattern-languages-and-catalogs — 질문

## 질문

1. (왜) 패턴 이름만 주고받을 때 깨지는 두 가지는 무엇인가? Fowler는 패턴 작가들이 "힘(forces)"을 적는 이유를 무엇이라고 했나?
2. (그림) 패턴 하나를 이루는 칸(맥락·문제·힘·해법·결과)을 그려라. GoF 형식과 microservices.io 형식은 어떤 칸을 두나?
3. (연결) "패턴 언어"란 무엇인가? Alexander·EIP·microservices.io·Azure에서 패턴 사이의 관계는 각각 어떻게 드러나나?
4. (경계) PoEAA의 Repository와 DDD의 Repository는 무엇이 같고 무엇이 다른가? PoEAA Gateway와 API Gateway는?
5. (예측) 구현 하나짜리 `ShippingFeePolicy` + 팩토리 판과 정적 메서드 판에 "무게 할증(입력 추가)"을 반영하면 각각 몇 파일이 바뀌나? "회원 무료배송(두 번째 정책)"에서는 기존 규칙 파일을 누가 고치나?
6. (예측) 위 실험에서 마지막으로 "할증 2000→2500"을 반영하면 두 판의 수정 파일 수는? 패턴 판이 더 많다면 원인은 무엇인가?
7. (그림) 선행(requires)·조합(combines)·대안(alternative) 간선으로 패턴 관계 그래프를 만들 때 어떤 자료구조·알고리즘을 쓰나? 위상 정렬로 무엇을 얻나?
8. (장애 진단) 리뷰에서 "Repository를 두자"에 합의했는데 PR마다 Repository의 모양이 다르다. 또 다른 PR은 구현 하나짜리 인터페이스와 팩토리를 계속 추가한다. 각각 무엇을 묻고 어떻게 바로잡나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
