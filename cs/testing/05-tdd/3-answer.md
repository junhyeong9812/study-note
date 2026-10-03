# testing/05-tdd — 정답

## 정답

### 1. 구현 먼저의 문제와 TDD

- 한 번에 크게 짜서, 틀렸을 때 원인을 찾는 범위가 넓다.
- 테스트가 이미 있는 코드 모양을 따라가, 코드에서 빠진 경우는 테스트에서도 빠진다.
- 기대값을 실행 결과에서 베껴 버그가 정답으로 굳는다.
- TDD는 실패하는 테스트 하나를 먼저 쓰고(빨강), 그것을 통과시키는 코드를 쓰고(초록), 초록에서 구조를 정리한다(리팩터링).

### 2. 다섯 단계

```text
   ┌─▶ 1. 테스트 목록
   │   2. 하나를 실행 가능한 테스트로 → 빨강
   │   3. 이 테스트 + 이전 테스트 전부 통과 → 초록
   │   4. (선택) 리팩터링 → 계속 초록
   └── 5. 목록이 빌 때까지 2로
```

- "& all previous tests pass": 새 동작을 넣다가 이전 결정을 깨면 바로 알아야 한다. 이전 테스트 묶음이 회귀 방지 장치다.

### 3. 두 설계 결정

- 인터페이스 설계("How a particular piece of behavior is invoked"): 2단계, 테스트를 쓸 때 정한다. 실험에서 첫 테스트가 `new Cart().total()`을 정했다.
- 구현 설계("How the system implements that behavior"): 3·4단계에서 정한다.
- 목록 단계에서 구현을 정하면, 아직 배우지 않은 것을 미리 확정하게 된다. Beck: "Mistake: mixing in implementation design decisions. Chill."

### 4. 초록으로 가는 세 전략

- Fake It: 상수를 돌려줘 일단 초록. 실험의 `return 0;`.
- Triangulate: 서로 다른 예제가 둘 이상 생기면 상수로는 다 못 통과하니 일반화한다.
- Obvious Implementation: 구현이 뻔하면 바로 쓴다. 실험의 `sum += unitPrice * quantity`.
- TDD의 Fake It은 **제품 코드의 임시 구현**이다. 테스트 더블 Fake는 **테스트에서 DOC를 대신하는 가벼운 구현**(HashMap 저장소 등)이다.

### 5. 첫 빨강과 처음부터 초록

- 첫 빨강은 컴파일 오류였다: `COMPILATION ERROR` — `CartTest.java:[6,24] cannot find symbol`. `Cart` 클래스가 아직 없다.
- "여러 품목" 테스트는 `Tests run: 3, Failures: 0`으로 처음부터 초록이었다. 이미 있는 구현(누적 합)이 그 경우를 덮는다는 정보다. 새 코드는 필요 없었고, 테스트는 회귀 방지로 남는다.

### 6. 손 계산 vs 붙여 넣기

- 손 계산: 9,005 × 0.9 = 8,104.5 → HALF_UP 8,105. 정수 연산 구현은 8,104라 빨강(`expected: 8105L but was: 8104L`). 버그가 드러난다.
- 붙여 넣기: 실행 출력 `ACTUAL=8104`를 기대값에 넣으면 `Tests run: 5, Failures: 0`, 초록. 버그가 정답으로 고정된다.
- 붙여 넣은 테스트를 둔 채 구현을 HALF_UP으로 고치면 `expected: 8104L but was: 8105L`, 빨강. 테스트가 수정에 저항한다.

### 7. 독립된 근거와 골든 마스터

- 기대값이 구현에서 오면 테스트는 구현을 복사할 뿐 검사하지 않는다. 손 계산·명세·다른 계산 경로처럼 구현과 독립된 근거가 필요하다.
- Evident Data: 입력과 기대값의 관계가 테스트 안에서 보이게 쓴다(`9_005 × 0.9 = 8_104.5 → 8_105`). 읽는 사람이 근거를 확인할 수 있다.
- 골든 마스터는 "현재 동작"을 일부러 고정하는 도구다. 목적이 정답 검증이 아니라 변화 감지이고, 레거시 리팩터링의 안전망으로 쓴다(17번). 새 기능의 기대값을 출력에서 베끼는 것과는 쓰임이 다르다.

### 8. 리팩터링 생략

- 4단계를 계속 건너뛰어 중복과 긴 조건문이 쌓였다. 구현 설계가 나빠질수록 다음 테스트를 통과시키는 비용이 커진다.
- 바로잡기: 초록마다 중복·이름·구조를 점검하고 그 사이클에서 고친다. 커밋을 refactor로 나눠 남긴다.
- 반대 방향 실수: "refactoring further than necessary for this session", "abstracting too soon. Duplication is a hint, not a command". 이번 사이클에 필요한 만큼만 고친다.

### 9. 목록 전체를 테스트로

- Canon TDD의 실수 "convert all the items on the Test List into concrete tests, then make them pass one at a time".
- 첫 구현에서 배운 것(인터페이스 변경)이 아직 통과시키지 않은 테스트 전부에 번진다.
- 목록은 글로 두고, 한 번에 하나만 테스트로 바꿨어야 한다.

### 10. 빨강을 안 본 테스트, 단언 없는 테스트

- 빨강을 보지 않은 테스트는 실패할 수 있는지 모른다. 잘못 쓴 단언·잘못된 대상 호출로 항상 초록일 수 있다.
- 단언 없는 테스트는 코드를 실행만 해서 커버리지를 올리지만 아무것도 검사하지 않는다(Canon TDD의 "write tests without assertions just to get code coverage").
- 드러내는 도구: 변이 테스트(15번). 코드에 작은 변이를 넣어도 테스트가 실패하지 않으면, 그 테스트의 판별력이 없다는 뜻이다.
