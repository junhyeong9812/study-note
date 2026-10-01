# distributed/20-data-ownership-and-cross-service-queries — 질문

## 질문

1. (비교) Shared Database와 Database per Service를 microservices.io의 정의로 설명하고, Shared Database의 결합 두 종류(개발 시점·런타임)를 예로 들어라.
2. (예측) 한 PostgreSQL에 `customer`·`ordering` 스키마가 있고 주문 서비스가 고객 표를 직접 조인한다. 고객 팀이 `full_name` 열을 `name`으로 바꾸면 (a) 고객 팀의 `ALTER`는 성공하나 (b) 주문 서비스의 조회는 어떻게 되나? 이런 구조를 무엇이라 부르나?
3. (적용) Database per Service를 DB 서버 하나로도 할 수 있나? microservices.io가 권하는 "장벽"은 무엇이고, 실험에서 그 장벽은 어떤 오류로 나타났나?
4. (예측) 주문 20건짜리 목록을 API Composition으로 만든다. 주문마다 고객·상품을 하나씩 부르는 방식과, ID를 모아 배치·병렬로 부르는 방식의 페이지당 호출 수는? 실험에서 p50은 각각 얼마였나?
5. (계산) 상품 서비스 호출의 5%가 100ms 걸린다. 한 페이지에서 상품을 20번 부르면 느린 호출을 하나도 안 만날 확률은? 실험에서 naive의 p50이 왜 p99가 아니라 p50부터 올랐는지 설명하라.
6. (경계) Command-side Replica와 Materialized View는 각각 누구의 어떤 필요를 채우나? 둘이 공통으로 감수하는 것은?
7. (예측) 이벤트로 유지하는 `order_view`에서 주문 직후 곧바로 조회하면 평소에도 보이나? 프로젝터가 3초 멈추면? 사용자 화면에서 이 문제를 어떻게 피하나?
8. (장애 진단) 특정 고객 이름이 목록 화면에서만 몇 주째 옛 이름이다. 컨슈머 LAG는 0이다. 원인 후보 두 가지와 대처는?
9. (연결) Index Table의 세 가지 구성과, 원천과 색인을 같은 트랜잭션으로 갱신할 수 없을 때 Azure 문서가 권하는 방법은? 이것이 16번과 어떻게 이어지나?
10. (연결) API Composer의 메모리 조인과 뷰 프로젝터는 각각 어떤 알고리즘·자료구조인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
