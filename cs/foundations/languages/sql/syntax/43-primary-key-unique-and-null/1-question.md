# sql/43-기본키·UNIQUE 제약과 NULL — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

대상은 **PostgreSQL 18.6** 과 **MySQL 8.4.10** 두 서버다. 「두 엔진에서」라고 물으면 **각각** 답한다.

이 편이 쓴 표는 전부 직접 만들었다가 지운 것이다. `emp`·`dept` 는 읽지 않는다.

```text
t43_pk (id int PRIMARY KEY, code varchar(10) UNIQUE, name varchar(10))
        -> 처음에 (1,'A','ann') 한 행이 들어 있다

t43_comp (a int, b int, UNIQUE (a,b))       -> 비어 있다
t43_addpk (id int, v varchar(5))            -> (1,'a') 와 (NULL,'b') 가 들어 있다
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `PRIMARY KEY` 한 단어가 만드는 것 (경계)

- `id int PRIMARY KEY` 라고만 썼을 때 엔진이 만드는 것 **세 가지**는 무엇인가?

### 2. 세 가지 위반의 에러가 다른가 (예측)

```sql
INSERT INTO t43_pk VALUES (NULL,'B','bob');   -- (a)
INSERT INTO t43_pk VALUES (1,'C','cho');      -- (b)
INSERT INTO t43_pk VALUES (2,'A','dan');      -- (c)
```

- 두 엔진에서 세 문이 각각 어떤 에러를 내는가?

### 3. ★ `UNIQUE` 열에 `NULL` 을 두 번 넣으면 (예측)

```sql
INSERT INTO t43_pk VALUES (3,NULL,'eve');
INSERT INTO t43_pk VALUES (4,NULL,'fay');
```

- 두 엔진에서 각각 어떻게 되는가?

### 4. ★ 왜 그렇게 되나 (왜)

- 3번의 결과를 [04 의 3값 논리](../04-null-three-valued-logic/)로 설명하면 어떤 한 줄인가?

### 5. ★ 「빈칸도 하나만」 을 원하면 (예측)

```sql
CREATE TABLE t43_nnd (code varchar(10) UNIQUE NULLS NOT DISTINCT);
INSERT INTO t43_nnd VALUES (NULL);
INSERT INTO t43_nnd VALUES (NULL);
```

- 두 엔진에서 각각 어떻게 되고, **MySQL 쪽 출력이 무엇의 근거가 되고 무엇의 근거가 못 되는가**?

### 6. ★ 복합 `UNIQUE` 에서 한 칸만 `NULL` 이면 (예측)

```sql
-- t43_comp 는 UNIQUE (a,b)
INSERT INTO t43_comp VALUES (1,NULL);   -- 두 번
INSERT INTO t43_comp VALUES (1,2);      -- 두 번
```

- 네 번의 `INSERT` 중 무엇이 막히고 무엇이 통과하는가?

### 7. 이미 `NULL` 이 든 열에 PK 를 붙이면 (예측)

```sql
-- t43_addpk 에는 id 가 NULL 인 행이 있다
ALTER TABLE t43_addpk ADD PRIMARY KEY (id);
```

- 두 엔진에서 각각 어떻게 되는가?

### 8. 42번과 무엇이 다른가 (연결)

- 7번에서 MySQL 이 거부했는데, [42번의 `ADD COLUMN ... NOT NULL`](../42-create-alter-drop-table/) 은 통과시켰다 — 그 차이의 이유는 무엇인가?

### 9. PK 를 두 개 (예측)

```sql
CREATE TABLE t43_two (a int PRIMARY KEY, b int PRIMARY KEY);
```

- 두 엔진에서 각각 무엇이 나오고, 원래 하려던 것은 어떻게 써야 하는가?

### 10. `NOT NULL UNIQUE` 와 `PRIMARY KEY` (경계)

- 이 둘은 값의 성질에서 무엇이 같고 무엇이 다른가?

### 11. 제약 이름은 누가 짓나 (연결)

- 이름을 안 주면 두 엔진이 각각 어떤 이름을 짓고, 그것이 운영에서 왜 문제가 되는가?

### 12. 그래서 어떻게 설계하나 (연결)

- 「이 열은 하나만 있어야 한다」를 스키마로 옮기는 방법을 두 엔진 각각에서 무엇으로 고르겠는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
