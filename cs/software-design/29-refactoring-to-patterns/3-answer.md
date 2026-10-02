# software-design/29-refactoring-to-patterns — 정답

## 정답

### 1. 두 실패와 대안

- 처음부터 설계: 축을 잘못 짚어 Speculative Generality(쓰지 않는 일반화, 구현 하나뿐인 인터페이스).
- 방치: 같은 `switch`가 여러 곳 → 새 타입마다 N곳 수정(Shotgun Surgery), 한 곳 누락.
- 대안(Kerievsky 2004): 스멜이 보일 때 작은 리팩터링 단계로 패턴에 도달하고, 필요 없어지면 걷어낸다.

### 2. 카탈로그의 문제

- Replace Type Code With Class: `String`·`int` 같은 필드 타입이 잘못된 대입과 비교를 막지 못한다.
- Replace Conditional Logic With Strategy: 메서드 안 조건문이 계산의 어느 변형을 실행할지 정한다.
- Introduce Null Object: null 필드·변수를 다루는 로직이 곳곳에 중복된다.
- Inline Singleton: 객체에 접근해야 하지만 전역 접근점은 필요 없다 — **패턴에서 멀어지는** 리팩터링.

### 3. 단계

```text
 v0  String type + switch ×3            tests 6 pass
 1단계 String → enum, switch 식          tests 6 pass  (테스트 파일 무변경)
 2단계 enum 상수별 interest/fee/label    tests 6 pass  (테스트 파일 무변경)
```

- 장치: 공개 생성자 `Account(String, long)`를 남기고 내부에서 `AccountType.valueOf`로 바꿨다. 옛 입구를 유지한 채 내부만 옮긴 것(parallel change의 작은 형태).

### 4. BUSINESS 추가

(실험 A, 2026-10-02)

```text
  [add-business-on-v0]  1 file changed, 3 insertions(+), 1 deletion(-)
  [add-business-after-refactor]  1 file changed, 4 insertions(+)
== 실행 [add-business-on-v0] …
  tests: 6 pass, 0 fail
  BUSINESS interest=1000 fee=5000 label=?
== 실행 [add-business-after-refactor] …
  tests: 6 pass, 0 fail
  BUSINESS interest=1000 fee=5000 label=사업자
```

- diff는 둘 다 4줄이지만 v0 쪽은 라벨을 빠뜨린 불완전한 변경이다(다 채우면 `Statement.java`까지 2파일 — 재지 않음). 둘 다 테스트 초록. 차이는 v0이 라벨을 `?`로 조용히 내보낸 것.

### 5. 구현 누락

```text
error: <anonymous AccountType$4> is not abstract and does not override abstract method interest(long) in AccountType
```

- 컴파일이 막힌다. 라벨도 생성자 인자라 빠뜨릴 수 없다.
- 산 것: 다음 변경의 크기가 아니라 "한 곳을 잊을 수 없게" 하는 것. 비용은 두 단계 약 80줄의 diff와, 이자 규칙 전체를 보려면 enum 상수를 훑어야 한다는 점.

### 6. 테스트 순서

(실험 B)

```text
  [before] 순서 [defaultTest, promoTest] → defaultTest=PASS promoTest=PASS
  [before] 순서 [promoTest, defaultTest] → promoTest=PASS defaultTest=FAIL
  [after] 순서 [defaultTest, promoTest] → defaultTest=PASS promoTest=PASS
  [after] 순서 [promoTest, defaultTest] → promoTest=PASS defaultTest=PASS
```

- 싱글턴 판은 `promoTest`가 바꾼 전역 `promoBp`가 남아 뒤 순서의 `defaultTest`가 깨졌다. 인스턴스를 넘긴 판은 두 순서 모두 초록.

### 7. Null Object

(실험 C)

```text
  null 반환판   bob → java.lang.NullPointerException: Cannot invoke "NullObj$Discount.apply(long)" because "<local3>" is null
  Null Object판 bob → 10000
```

- null 반환판은 NPE, Null Object판은 원가 10,000원(할인 없음 = 아무것도 안 바꾸는 원소).
- `<local3>`: `-g`(디버그 정보) 없이 컴파일해 지역 변수 이름이 클래스 파일에 없어서 슬롯 번호로 표시됐다.

### 8. 화석화된 패턴

- 원인: 패턴 도입은 쉽지만 제거에는 호출부 전수 확인과 테스트 안전망이 필요하다. 그것이 없으면 아무도 손대지 않는다.
- 절차: 호출부를 IDE 호출 계층·grep으로 전수 확인 → 특성 테스트로 현재 동작 고정 → 팩토리를 인라인해 구현을 직접 생성 → 인터페이스를 인라인 → 단계마다 테스트 초록·커밋. Inline Singleton처럼 "멀어지는" 리팩터링도 정식 절차다.

### 9. 커밋 확인

- 약한 신호: 리팩터링 커밋에서 테스트 파일이 바뀌지 않았다(`git diff --stat HEAD~1 HEAD -- '*Test.java'`가 비어 있음). 실험 A의 두 단계가 그랬다. 테스트를 같이 고쳤다면 동작이 바뀌었을 수 있다.
- 나누는 이유: 리팩터링 커밋은 "동작이 같다"만 검토하면 되고, 기능 커밋은 "무엇이 바뀌었나"만 보면 된다. 섞이면 둘 다 검토하기 어렵고 되돌리기도 함께 되돌려진다(14 tidy-first).
