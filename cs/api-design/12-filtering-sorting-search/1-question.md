# api-design/12-filtering-sorting-search — 질문

## 질문

1. (왜) 목록 API에 필터·정렬 파라미터를 여는 것이 "클라이언트에게 쿼리 모양을 고르게 하는 것"인 이유는? 도서관 사서 비유로 설명하라.
2. (경계) Google AIP-132·AIP-160과 JSON:API 1.1은 정렬·필터 파라미터의 모양과 "지원하지 않는 요청"의 처리를 각각 어떻게 정하나?
3. (예측) 100만 행 테이블에서 `ORDER BY created_at DESC, id DESC LIMIT 20`(인덱스 있음)과 `ORDER BY name, id LIMIT 20`(인덱스 없음)의 계획은 어떻게 다른가? 두 번째에 `OFFSET 200000`을 붙이면 `Sort Method`는 무엇으로 바뀌나?
4. (예측) 인덱스 없는 정렬 쿼리 4개가 동시에 도는 동안, 인덱스를 타는 정상 목록 요청의 평균 지연과 처리량은 어떻게 되나?
5. (예측) PostgreSQL에서 `PREPARE p(text) AS SELECT id FROM product WHERE id < 5 ORDER BY $1 LIMIT 4; EXECUTE p('id DESC');`의 결과 순서는? 왜 에러가 안 나나?
6. (설계) 정렬·필터 필드를 SQL에 넣을 때 식별자와 값은 각각 어떻게 다뤄야 하나? 허용 목록이 막는 두 가지 위험은?
7. (연결) `filter=category=7&order_by=price`가 빠르려면 어떤 인덱스가 필요하고, 왜 열 순서가 중요한가? `filter=price=12345&order_by=created_at desc`가 느렸던 이유는?
8. (예측) `name ILIKE '%abc12%'` 검색은 B+Tree 인덱스로 왜 안 되나? pg_trgm GIN을 만들면 계획과 시간이 어떻게 바뀌나? 트라이그램 인덱스가 소용없어지는 패턴은?
9. (연결) 정렬을 바꿀 수 있는 목록 API에서 커서 페이지네이션의 토큰에는 무엇이 들어가야 하나?
10. (장애 진단) 관리자 화면에 "아무 열이나 클릭 정렬"을 추가한 다음 날 DB CPU가 포화됐다. 무엇을 보고 어떻게 대처하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
