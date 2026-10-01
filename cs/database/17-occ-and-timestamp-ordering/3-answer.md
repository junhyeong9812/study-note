# database/17-occ-and-timestamp-ordering — 정답

## 정답

### 1. 비관적 vs 낙관적

- 비관적 락: "충돌할 것이다" → 접근 전에 잠근다. 충돌이 없어도 락 비용과 대기가 든다.
- OCC: "충돌은 드물다" → 잠그지 않고 진행하고 끝에 검증한다(Kung·Robinson 1981, CMU L18).
- 충돌이 드물면 OCC는 락 관리·대기가 없어 싸다. 전부 읽기이거나 서로 다른 데이터를 만지는 작업이 그렇다(CMU L18).
- 중단이 비싼 이유: OCC는 트랜잭션을 **끝까지 실행한 뒤** 검증에서 중단한다. 한 일 전체를 버린다. 락 방식은 충돌 지점에서 기다렸다가 이어서 한다.

### 2. OCC 세 단계와 검증 조건

```text
  읽기 단계(쓰기는 개인 작업 공간) → 검증(TS 부여, 충돌 검사) → 쓰기(전역 반영)
                                         └ 실패 → 중단·재시작
```

- 읽기 단계의 쓰기는 **로컬 사본**에만 간다. 다른 트랜잭션은 볼 수 없다.
- TS(Ti) < TS(Tj)이면 하나가 성립해야 한다.
  1. Ti가 쓰기 단계까지 마친 뒤 Tj가 읽기 단계를 시작했다.
  2. Ti가 Tj의 쓰기 단계 시작 전에 쓰기를 마쳤고, WS(Ti) ∩ RS(Tj) = ∅.
  3. Ti가 Tj보다 읽기 단계를 먼저 마쳤고, WS(Ti) ∩ RS(Tj) = ∅ 이고 WS(Ti) ∩ WS(Tj) = ∅.

### 3. Basic T/O 판정 (`R-TS=20`, `W-TS=15`)

| 연산 | 검사 | 결과 |
|---|---|---|
| TS 10 읽기 | 10 < W-TS 15 | 중단 — "미래"에 쓰인 값을 읽으려 함 |
| TS 18 쓰기 | 18 < R-TS 20 | 중단 — TS 20이 이미 옛 값을 읽었으니 그 앞에 끼어 쓸 수 없음 |
| TS 25 쓰기 | 25 ≥ 20, 25 ≥ 15 | 허용, W-TS = 25 |

- 토머스 쓰기 규칙은 `R-TS` 검사를 통과했지만 `TS(Ti) < W-TS(X)`인 쓰기를 중단 대신 **무시**한다. 이미 더 새 값이 있으니 그 쓰기를 읽을 트랜잭션이 없기 때문이다.
  - TS 18 쓰기는 `R-TS` 조건(18 < 20)에 걸리므로 여전히 중단이다.
  - 규칙이 효과를 보는 것은 `R-TS ≤ TS(Ti) < W-TS`인 경우다. 이 예는 R-TS(20) > W-TS(15)라 그런 TS가 없다. 따라서 이 X에서는 토머스 규칙이 있어도 결과가 같다.
- 근거: CMU 15-445 Fall 2023 L17 노트.

### 4. 교착이 없는 이유와 대가

- T/O에서는 아무도 기다리지 않는다. 순서를 어기면 즉시 중단·재시작한다. 기다림이 없으니 wait-for 그래프에 사이클이 생길 수 없다.
- 대가: 긴 트랜잭션은 새 트랜잭션이 쓴 값을 만날 확률이 높아 반복해서 중단된다(기아). 커밋 순서 제약이 없으면 회복 불가능한 스케줄도 허용한다(CMU Fall 2023 L17).

### 5. PostgreSQL RC에서 버전 조건 UPDATE 두 개

1. 세션 A가 행을 찾아 잠그고 `version = 8`로 고친다.
2. 세션 B도 같은 행(명령 시작 시점의 커밋된 버전 `version = 7`)을 찾는다. 행이 잠겨 있어 A의 커밋·롤백을 기다린다.
3. A가 커밋한다. B는 **갱신된 버전**(`version = 8`)에 WHERE를 다시 평가한다(13.2.1).
4. `version = 7`이 거짓 → B는 **0행**을 고친다. 앱은 이것을 충돌로 처리한다.

- A가 롤백했다면 B는 원래 행을 그대로 고쳐 1행이다.

### 6. `@Version`

- SQL 모양(Hibernate 6.6 가이드 11.1): `update ... set ..., version = 1 where id = 1 and version = 0`.
- 영향받은 행이 0이면
  - Hibernate: `StaleObjectStateException`(네이티브) 또는 Jakarta Persistence `OptimisticLockException` 계열
  - Spring: `ObjectOptimisticLockingFailureException`(Hibernate 예외 번역) 또는 `JpaOptimisticLockingFailureException`(JPA 예외 번역). 둘 다 `OptimisticLockingFailureException`의 하위다.
- 허용 타입: Jakarta Persistence 기준 `int`·`short`·`long`(래퍼 포함)·`java.sql.Timestamp`. Hibernate는 `Instant` 등도 허용한다.
- 타임스탬프 버전은 가이드가 "버전 번호보다 덜 믿을 만하다"고 적는다. 같은 시각 해상도 안의 두 갱신을 구분하지 못할 수 있기 때문이다 [?] — 이유는 가이드에 명시되지 않았다.

### 7. 경합 높은 행의 OCC 재시도 폭증

- 한 행에 N명이 동시에 쓰면 라운드마다 1명만 이기고 나머지는 전부 다시 읽고 다시 계산한다.
- 로컬 재현(예시, PostgreSQL 17.11): 한 행을 8세션이 각 200번 차감.
  - 버전 조건 UPDATE: 1600 성공, 재시도 6605(성공당 약 4번), 세션당 17.4 s
  - 원자 조건부 UPDATE: 1600 성공, 재시도 0, 세션당 4.1 s
- 대처
  - 몰리는 행은 `UPDATE stock SET qty = qty - ? WHERE id = ? AND qty >= ?`처럼 DB가 계산하게 한다(18번).
  - 순서가 필요하면 `SELECT ... FOR UPDATE`.
  - OCC를 유지해야 하면 재시도 상한 + 지터 백오프 + 재시도율 지표.

### 8. 조용한 lost update

- 두 요청이 같은 값(예: 100)을 읽고 각각 99를 쓴다. 두 번 차감했는데 한 번만 반영된다. 검증이 없으니 에러도 없다.
- 로컬 재현(예시, PostgreSQL 17.11): 8세션 × 200번 "성공"했는데 실제 차감은 202.
- MySQL 8.4 RR이 막지 못하는 이유: RR 스냅샷은 `SELECT`에만 적용되고, `UPDATE`는 최신 커밋 버전을 그냥 덮어쓴다(17.7.2.3). 앱이 계산한 상수로 덮어쓰면 그사이의 변경이 사라진다.
  - PostgreSQL RR이었다면 두 번째 UPDATE가 40001로 실패했을 것이다(16번).
- 대처: 버전 컬럼, 또는 `SET qty = qty - 1`.

### 9. `@Version`이 있는데 덮어쓰기

- 흔한 서버 코드

```java
@Transactional
public void update(Long id, ProductForm form) {
    Product p = repo.findById(id).orElseThrow();   // 지금 최신 버전을 읽음
    p.setName(form.name());                         // 화면이 본 버전과 비교하지 않음
}
```

- 새로 읽은 엔티티는 항상 최신 버전이다. 검증할 "옛 버전"이 없다.
- 고치기: 화면이 받은 `version`을 요청에 싣고 비교한다.

```java
if (p.getVersion() != form.version()) throw new ConflictException();  // 409, 또는 ETag/If-Match → 412
```

### 10. 여러 행에 걸친 불변식

- 버전은 **행마다** 검사한다. 두 사용자가 **다른 자식 행**을 추가하면 서로의 버전을 건드리지 않아 충돌로 안 보인다.
  - 예: 주문 총액 한도 100, 현재 80. A가 15짜리 항목, B가 15짜리 항목을 동시에 추가 → 둘 다 성공, 총액 110.
- 이것은 write skew와 같은 구조다([14번](../14-isolation-levels-and-anomalies/2-summary.md)).
- 대처
  - 자식을 바꿀 때 루트(주문) 버전을 함께 올린다 — `LockModeType.OPTIMISTIC_FORCE_INCREMENT`로 루트를 잠근다. 그러면 두 번째 커밋이 루트 버전 충돌로 실패한다.
  - 또는 루트 행을 `FOR UPDATE`로 잠근 뒤 합계를 검사한다.
  - aggregate 단위 버전은 [52번 offline-concurrency-patterns](../52-offline-concurrency-patterns/2-summary.md).
