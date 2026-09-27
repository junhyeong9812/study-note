# sql/18-USING 과 NATURAL JOIN — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

예시 테이블은 이 폴더의 SQL 주제들이 공유한다.

```text
emp (사원)                          dept (부서)
+----+------+---------+--------+    +----+-------+
| id | name | dept_id | salary |    | id | name  |
+----+------+---------+--------+    +----+-------+
|  1 | ann  |      10 |    300 |    | 10 | sales |
|  2 | bob  |      10 |    500 |    | 20 | dev   |
|  3 | cho  |      20 |   NULL |    | 30 | hr    |
|  4 | dan  |    NULL |    400 |    +----+-------+
+----+------+---------+--------+
```

★ **이 두 표의 열 이름을 먼저 본다.**

```text
 emp  : id   name   dept_id   salary
 dept : id   name
        ↑     ↑
  겹치는 이름은 둘인데, 정작 붙여야 할 짝(emp.dept_id ↔ dept.id)은 이름이 다르다
```

`USING` 이 도는 모습을 보는 문항에서는 `dept` 를 파생 테이블로 감싸 이름만 바꿔 쓴다 — `dept` 자체는 안 바꾼다.

```text
d = (SELECT id AS dept_id, name AS dept_name FROM dept)     열: dept_id, dept_name
```

10번에서만 표 하나(`deptx`)를 더 쓴다. **기존 `dept` 에서 만들어 롤백**했고, 만드는 문은 정답 파일에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `ON` 과 `USING` 의 결과 (예측)

```sql
-- (A)
SELECT * FROM emp e JOIN (SELECT id AS dept_id, name AS dept_name FROM dept) d ON e.dept_id = d.dept_id;
-- (B)
SELECT * FROM emp e JOIN (SELECT id AS dept_id, name AS dept_name FROM dept) d USING (dept_id);
```

- 두 질의의 **행 수**와 **열 목록**은 각각 어떻게 다른가?

### 2. 한정자 없이 공통 열 부르기 (예측)

```sql
SELECT dept_id FROM emp e JOIN (SELECT id AS dept_id, name AS dept_name FROM dept) d ON e.dept_id = d.dept_id;
```

- 이 질의는 통과하는가? `ON` 을 `USING (dept_id)` 로 바꾸면 달라지는가?

### 3. 외부 조인에서 합쳐진 열 (예측)

```sql
SELECT dept_id, e.dept_id AS from_e, d.dept_id AS from_d
FROM emp e RIGHT JOIN (SELECT id AS dept_id, name AS dept_name FROM dept) d USING (dept_id);
```

- `hr`(30번) 행에서 `dept_id`·`from_e`·`from_d` 세 칸에는 각각 무엇이 들어가는가?

### 4. 그것이 왜 문제인가 (왜)

- 3번의 결과 때문에, 외부 조인 + `USING` 에서 **짝이 없었다는 사실**을 어떻게 확인해야 하는가?

### 5. `USING` 에 없는 열을 적으면 (경계)

```sql
SELECT * FROM emp e JOIN dept d USING (dept_id);
```

- 이 질의는 어떻게 되는가?

### 6. `NATURAL JOIN` 의 0행 (왜)

```sql
SELECT COUNT(*) FROM emp NATURAL JOIN dept;
```

- [13번](../13-inner-join/)에서 본 이 결과가 **왜** 0 인지, 엔진이 만든 조인 조건을 그대로 쓸 수 있는가?

### 7. `NATURAL LEFT JOIN` (예측)

```sql
SELECT * FROM emp NATURAL LEFT JOIN dept;
```

- 결과 행 수와 열 목록은 무엇이고, 그 결과가 **무엇과 구분되지 않는가**?

### 8. 공통 열이 하나도 없으면 (예측)

```sql
SELECT COUNT(*) FROM emp NATURAL JOIN (SELECT id AS d_id, name AS d_name FROM dept) x;
```

- 결과는 몇이고, 두 엔진 중 어느 쪽이 이것을 막아 주는가?

### 9. 조건 없는 조인의 세 경로 (연결)

- 카티션곱이 **의도치 않게** 나오는 경로 셋을 들고, 그중 어느 것이 가장 조용한지 말할 수 있는가?

### 10. 열 하나를 추가하면 (예측)

```sql
-- deptx 의 열 = dept_id, dept_name 일 때
SELECT COUNT(*) FROM emp NATURAL JOIN deptx;
-- ALTER TABLE deptx ADD COLUMN name …;  뒤에 같은 문을 다시
SELECT COUNT(*) FROM emp NATURAL JOIN deptx;
```

- 두 결과는 각각 몇이고, 이 사고가 코드 리뷰로 잡히지 않는 이유는 무엇인가?

### 11. `USING` 이었다면 (연결)

- 10번을 `USING (dept_id)` 로 썼다면 각각 어떻게 됐겠는가?

### 12. `USING` 도 조용할 수 있나 (경계)

```sql
SELECT * FROM emp e JOIN dept d USING (id, name);
```

- 이 질의의 결과는 무엇이고, `USING` 의 안전이 정확히 **무엇을** 보장하는지 한 줄로 말할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
