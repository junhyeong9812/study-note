# domain-modeling/11-state-machines-in-domain — 정답

## 정답

### 1. 차단 목록 if문이 새는 이유

- 차단 목록은 "안 된다고 적은 것만 막는다." 적지 않은 상태는 기본이 통과다.
- 정상 경로 테스트는 허용 칸만 시험한다. 허용 칸은 if문도 맞게 통과시키므로 테스트가 초록이다. 새는 곳은 거부해야 할 칸인데, 그 칸을 시험하는 테스트가 없다.
- 허용 목록(전이 표)은 적힌 칸만 되고 나머지는 거부다. 기본값이 닫혀 있다.

### 2. 전이도

```text
  PLACED ─PAY→ PAID ─PREPARE→ PREPARING ─SHIP→ SHIPPED ─DELIVER→ DELIVERED ─REQUEST_RETURN→ RETURN_REQUESTED ─REFUND→ REFUNDED
    └─CANCEL─┐   └─CANCEL─┐        └─CANCEL─┐
             └──────────────┴────────────────┴→ CANCELLED
```

- 취소는 PLACED·PAID·PREPARING에서만. SHIPPED부터는 반품 경로다.

### 3. if문 예시의 불법 통과

- 56칸 중 19칸을 명세에 없는데 통과시켰다(허용 9칸은 다 맞힘).
- "환불된 주문 배송" = `REFUNDED--SHIP-->SHIPPED`.
- ON_HOLD 추가 후 72칸 중 21칸(`ON_HOLD--SHIP`, `ON_HOLD--REFUND`가 더해짐). 전이 표는 두 경우 모두 0.

### 4. 거부의 두 종류

- 표에 칸 없음: 그런 전이는 존재하지 않는다. 호출 코드·연동 오류일 가능성이 크다 → 오류로 기록·경보.
- 가드 거짓: 전이는 있지만 지금 조건이 안 된다(예: 주소 미검증). 정상 업무 흐름이다 → 이유를 사용자에게 돌려준다.
- 구분하지 않으면 정상 거부가 경보를 울리거나, 코드 오류가 사용자 메시지로 묻힌다.

### 5. statechart

- 계층(hierarchy), 동시성(concurrency, 직교 영역), 통신(communication)(Harel 1987, *Science of Computer Programming* 8(3)).
- 계층: 여러 상태에 공통인 전이(배송 전 언제든 취소)를 바깥 상자에 한 번 적는다 → 화살표 중복이 준다.
- 직교 영역: 처리 상태와 결제 상태처럼 독립적인 축을 따로 둔다 → 상태가 곱으로 불어나지 않는다.

### 6. 동시 전이 실험

- READ COMMITTED 읽고-검사-쓰기: 200/200건이 둘 다 성공. 두 번째 UPDATE는 행 잠금을 기다렸다가 상태 조건이 없으니 그대로 덮어쓴다.
- 조건부 UPDATE: 둘 다 성공 0, 한쪽만 200.
- REPEATABLE READ: 둘 다 성공 0, 진 쪽 200건이 40001(`could not serialize access due to concurrent update`)을 받았다.
- 최종 CANCELLED/SHIPPED 비율은 실행마다 다르다.

### 7. 조건부 UPDATE

```sql
UPDATE orders SET status = 'CANCELLED', version = version + 1
 WHERE id = :id AND status = 'PREPARING' AND version = :version;
```

- 영향 행 0 = 그 사이 누가 먼저 바꿨다. 다시 읽고, 새 상태에서 이 이벤트가 허용되는지 전이 표로 재판단한다(예: 이미 SHIPPED면 취소 대신 반품 안내). 맹목적으로 같은 UPDATE를 재시도하지 않는다.

### 8. enum 순서와 과거 데이터

- JPA `@Enumerated`의 기본값 `EnumType.ORDINAL`로 저장 중인지 의심한다. 순서 번호가 저장돼 있어 중간 삽입이 기존 숫자의 뜻을 밀었다.
- 예방: `EnumType.STRING`. 이미 꼬였으면 배포 전후 enum 순서로 매핑표를 만들어 보정한다(백업 후, 개별 확인).

### 9. 상태 곱 폭발

- 원인: 독립적인 두 축(처리 진행, 보류 여부 또는 결제 상태)을 한 enum에 곱했다.
- 방향: 축마다 상태 기계를 따로 둔다(직교 영역). 축 사이 제약은 가드로 표현한다(예: 결제 CAPTURED 전에는 SHIP 불가).

### 10. 불법 전이·모순 찾기

- 전이 이력과 허용 전이 표를 `(from, event, to)`로 LEFT JOIN해 표에 없는 이력을 찾는다.
- 끝난 상태(REFUNDED·CANCELLED)인데 출고 행이 있는 주문을 JOIN으로 찾는다.
- 같은 주문에서 같은 출발 상태의 전이가 둘 이상인 이력도 동시 전이 경합의 흔적이다.
