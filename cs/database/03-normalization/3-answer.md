# database/03-normalization — 정답

## 정답

### 1. 세 가지 이상과 원인 FD

- 원인 FD: `customer_id → customer_email`. 결정자 `customer_id`가 이 테이블의 슈퍼키가 아니다.
- 갱신 이상: 고객 7의 이메일을 주문 2에서만 고치면 같은 고객에 이메일이 둘이 된다(로컬 재현: `{kim@new.com,kim@old.com}`).
- 삽입 이상: 아직 주문이 없는 고객의 이메일을 저장할 행이 없다. 주문 칸을 NULL로 채운 가짜 행이 필요하다.
- 삭제 이상: 고객 8의 유일한 주문을 지우면 고객 8의 이메일도 사라진다.

### 2. 속성 폐포

```text
  result = {A, G}
  A→B, A→C  → {A, B, C, G}
  CG→H      → {A, B, C, G, H}
  CG→I      → {A, B, C, G, H, I} = R
  B→H       → 변화 없음 → 종료
```

- (AG)+ = R 이므로 AG는 **슈퍼키**다.
- 후보 키 판정: 진부분집합이 슈퍼키인지 본다. A+ = {A, B, C, H}, G+ = {G}. 둘 다 R이 아니다 → AG는 **후보 키**(최소)다.

### 3. 정규형 정의와 위반 예

- 2NF: 키가 아닌 속성이 후보 키의 일부에만 종속하지 않는다(부분 종속 없음).
  - 위반: `order_item(order_id, product_id, qty, product_name)` — `product_id → product_name`.
- 3NF: 모든 α → β가 자명이거나, α가 슈퍼키이거나, β − α의 각 속성이 어떤 후보 키에 들어 있다.
  - 위반: `orders_flat`의 `customer_id → customer_email`(키 → customer_id → email 이행 종속).
- BCNF: 모든 α → β가 자명이거나 α가 슈퍼키다. "결정자는 모두 슈퍼키".
  - 위반(3NF지만): 5번의 `dept_advisor`.

### 4. BCNF 분해와 손실 없음

- 위반 FD α → β = `customer_id → customer_email`. 분해: (α ∪ β) = `customer(customer_id, customer_email)`, (R − (β − α)) = `orders(order_id, customer_id, amount)`.
- 손실 없음 조건: R1 ∩ R2 → R1 또는 R1 ∩ R2 → R2가 F+에 있으면 된다. R1 ∩ R2 = {customer_id}이고 `customer_id → customer_email`이므로 `customer_id → customer`(R1 전체)가 성립한다.
- 잘못 분해하면(예: 공통 속성이 어느 쪽의 키도 아님) 다시 조인할 때 원래 없던 조합이 생긴다. 무엇이 원래 사실인지 알 수 없게 된다(손실 분해).

### 5. dept_advisor

- 후보 키: {s_ID, dept_name}, {s_ID, i_ID}.
- BCNF가 **아니다**. `i_ID → dept_name`에서 i_ID가 슈퍼키가 아니다.
- 3NF**다**. `dept_name`이 후보 키 {s_ID, dept_name}에 들어 있으므로 3NF의 세 번째 조건을 만족한다.
- BCNF로 쪼개면(예: (i_ID, dept_name), (s_ID, i_ID)) `(s_ID, dept_name) → i_ID`를 한 테이블 안에서 검사할 수 없다. **종속 보존**을 잃는다. 학생이 한 학과에 지도교수 두 명을 두는 것을 조인 없이 막을 수 없다.

### 6. 반정규화 선택지

- 선택지 1: 반정규화한 테이블을 둔다. 조회는 빠르다. 공간·갱신 시간이 더 들고, 동기화 코드를 사람이 짜야 해서 오류 가능성이 있다.
- 선택지 2: 구체화 뷰. 장단점은 같지만 동기화 코드를 사람이 짜지 않는다. PostgreSQL은 `REFRESH` 전까지 옛 값이다.
- `unit_price`는 반정규화가 **아니다**. "주문 시점 가격"은 상품의 현재 가격과 다른 사실이다. `(order_id, product_id) → unit_price`라는 별도 FD를 가진다. 상품 테이블로 옮기면 가격 변경이 과거 주문을 바꾼다.

### 7. 고객 이메일 불일치

```sql
SELECT customer_id, count(DISTINCT customer_email) AS emails
FROM orders_flat GROUP BY customer_id
HAVING count(DISTINCT customer_email) > 1;
```

- 원인: 고객 → 이메일 종속을 주문 테이블에 복제했다. 이메일 변경 경로가 복사본 일부만 고쳤다(갱신 이상).
- 근본 대처: `customer(customer_id PK, email)`로 분리하고 주문은 `customer_id` FK만 둔다. 이관 때 어느 값을 채택할지는 데이터가 아니라 원천(고객 마스터)·업무 규칙으로 정한다. 앱 전환 후 복제 열을 지운다.

### 8. 12개 조인

- 확인할 설정(PostgreSQL 17 19.7): `join_collapse_limit`·`from_collapse_limit`(기본 8)은 이보다 큰 조인 목록을 한 번에 재배열하지 않게 막는다. `geqo`(기본 on)가 켜져 있고 플래너가 한 번에 다루는 FROM 항목(collapse 한도로 묶인 뒤의 수)이 `geqo_threshold`(기본 12) 이상이면 유전 알고리즘 플래너가 쓰여 최적이 아닌 계획이 나올 수 있다.
- 계획 신호: `EXPLAIN (ANALYZE, BUFFERS)`에서 조인 단계를 거칠수록 추정 `rows`와 `actual rows`가 크게 벌어지는지, 큰 중간 결과에 중첩 루프가 붙었는지 본다.
- 설계 대처
  - 함께 읽고 함께 바뀌는 값까지 쪼갠 과정규화인지 본다. FD가 없는 분리는 되돌린다.
  - 읽기 화면용 조회 테이블·구체화 뷰로 조인을 미리 해 둔다(동기화 방법과 함께).
- 참고: 로컬 재현에서 14개 사슬 조인의 계획 시간은 1~2ms였다. 조인 수만으로 느려진다고 단정하지 말고, 계획 시간(`Planning Time`)과 실행 시간을 나눠 본다.
