# database/01-relational-model-and-algebra — 질문

## 질문

1. (왜) Codd가 관계 모델로 없애려 한 "데이터 종속"은 무엇인가? 파일에 직접 데이터를 두는 방식과 비교해 데이터 독립성이 무엇을 바꾸는지 설명하라.
2. (경계) Codd의 릴레이션과 SQL 테이블은 중복 행·행 순서·NULL에서 어떻게 다른가? 대수의 π와 SQL의 `SELECT`는 같은가?
3. (그림) `σ_{b_id=102}(R ⋈ S)`와 `R ⋈ σ_{b_id=102}(S)`를 연산자 트리로 그려라. 둘의 결과는 같은가? 어느 쪽이 왜 빠른가? SQL을 쓰는 사람은 이 선택을 누가 한다고 생각해야 하나?
4. (예측) PostgreSQL에서 id 1~5를 넣고 `SELECT id FROM item;`을 한 뒤 `UPDATE item SET name='x' WHERE id=2;`를 하고 같은 SELECT를 다시 하면 순서는 어떻게 되나? 이유를 ctid로 설명하라.
5. (예측) MySQL InnoDB 테이블 `item(id PK, name, cat, KEY(name))`에서 `SELECT id FROM item`과 `SELECT id, cat FROM item`의 결과 순서가 다를 수 있는 이유는?
6. (설계) 게시글 목록을 `ORDER BY created_at DESC LIMIT 20 OFFSET 20`으로 넘기는데 행이 중복·누락된다. 원인과 수정한 쿼리를 써라.
7. (연결) `UNION`과 `UNION ALL`의 차이는? 두 쿼리 결과에 각각 NULL이 있을 때 `UNION`은 NULL 행을 몇 개 남기나? `=` 비교의 NULL 규칙과 무엇이 다른가?
8. (장애 진단) 적재 오류로 기본 키 없는 테이블에 완전히 같은 행이 두 번 들어갔다. `DELETE … WHERE`로 하나만 지우려 했는데 `DELETE 2`가 나왔다. 왜 그런가? 어떻게 복구하고 재발을 막나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
