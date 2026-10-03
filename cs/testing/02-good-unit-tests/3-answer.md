# testing/02-good-unit-tests — 정답

## 정답

### 1. 해가 되는 테스트

- SWE@G 12장: brittle test는 "fails in the face of an unrelated change to production code that does not introduce any real bugs".
- 버그를 잡더라도, 버그 아닌 변경에 자주 빨개지면 고치는 비용이 들고 리팩터링을 피하게 만든다.
- 화재경보기가 토스트에도 울리면 사람들은 경보를 무시한다. 테스트도 거짓 경보가 잦으면 진짜 실패까지 무시된다.

### 2. 네 기둥과 2×2

- 회귀 방지 · 리팩터링 내성 · 빠른 피드백 · 유지보수성(Khorikov 4장).

```text
                 버그 있음               버그 없음
  빨강   │ 참 양성                 │ 거짓 양성 ← 리팩터링 내성
  초록   │ 거짓 음성 ← 회귀 방지    │ 참 음성
```

- Khorikov 블로그: 거짓 양성 = "a false alarm, aka false failure", 회귀 방지 = "Lack of false negatives".
- 가치 = 네 점수의 곱(2차 출처 요약) → 한 기둥이 0이면 가치 0.

### 3. 관찰 가능 vs 구현 세부

| 사실 | 분류 | 이유 |
|---|---|---|
| 저장소에 할인된 총액으로 저장된 주문 | 관찰 가능 | 호출자의 목표(주문 기록)와 바로 이어진 결과 |
| `calc.total`이 한 번 호출됨 | 구현 세부 | 결과를 **어떻게** 만들었나. 계산을 다른 곳으로 옮겨도 동작은 같다 |
| 고객에게 보낸 알림 | 관찰 가능 | 프로세스 밖으로 나가는 부수효과. 외부가 본다 |

### 4. `subtotal()` 인라인(R1)

(실험, JDK 21.0.12 · JUnit Platform 1.13.4 · Mockito 5.18.0, 2026-10-03)

```text
R1 D 전체=6 통과=4 실패=0 |  PriceCalculatorDetailTest[컴파일 실패 2개: cannot find symbol]
R1 C 전체=6 통과=6 실패=0 |
```

- 도우미를 직접 부르는 테스트 파일은 **컴파일조차 안 된다.** 도우미를 부르지 않는 같은 파일의 다른 테스트까지 합쳐 2개가 함께 못 돈다.
- `total()` 결과만 보는 테스트는 그대로 초록이다.

### 5. `apply`로 위임(R2)

```text
R2 D  소계로_discountRate를_한번_묻는다() ✘
        Wanted but not invoked:
        -> at shop.DiscountPolicy.discountRate(DiscountPolicy.java:4)
R2 C  전체=6 통과=6 실패=0
```

- 버그가 아니다. 계산이 `apply` 안으로 옮겨 `discountRate`를 mock에 직접 묻지 않게 됐을 뿐이다(진짜 `apply`는 안에서 `discountRate`를 부르지만, mock의 `apply`는 아무것도 하지 않는다). 거짓 양성이다.

### 6. 단위 불일치(B4)

```text
B4 D 통과=6 실패=0 |
B4 C 통과=3 실패=3 | OrderServiceTest:주문이_할인된_총액으로_저장된다()  OrderServiceTest:고객에게_총액이_통지된다()  PriceCalculatorTest:경계에서_할인이_적용된다()
        expected: 90000L
         but was: 0L
```

- mock 묶음(D)은 전부 초록이다. 계산기 테스트는 "정책이 10을 준다"는 가정을 stub으로 새겨 두어 실제 정책이 100을 줘도 모른다.
- 진짜 정책을 쓴 묶음(C)은 3개가 빨개졌다. 10만 원 주문의 총액은 `100,000 − 100,000 × 100 / 100 = 0`원이다.

### 7. 변경 네 종류

| 변경 | 기존 테스트 수정 |
|---|---|
| 순수 리팩터링 | 없어야 한다 |
| 새 기능 | 없다. 새 테스트 추가 |
| 버그 수정 | 대개 없다. 빠진 케이스 추가 |
| 동작 변경 | 있다(유일한 경우) |

- 리팩터링에서 테스트를 고쳐야 했다면, 사실은 동작이 바뀌었거나 테스트가 부적절한 추상 수준(구현 세부)에 묶였다는 신호다(SWE@G 12장).

### 8. AAA

- Arrange(준비) → Act(실행 한 번) → Assert(확인).
- Meszaros Four-Phase Test(setup → exercise → verify → teardown)에서 teardown을 뺀 것과 같고, BDD의 Given-When-Then과도 같다. SWE@G 12장 각주도 같은 세 부분을 "arrange," "act," "assert"라고 부른다.
- Act가 두 번이면 한 테스트에 동작 여러 개를 섞은 것이다(Eager Test). 첫 Act의 단언이 실패하면 두 번째 동작은 검증되지 않는다. 동작마다 테스트를 나눈다.

### 9. `Wanted but not invoked` 대량 실패

- 원인: 테스트가 내부 협력 객체 호출(구현 세부)을 `verify`·`inOrder`로 고정했다. 리팩터링으로 호출 경로가 바뀌면 동작이 같아도 깨진다.
- 순서
  1. 실패한 테스트를 "동작이 바뀌었나?"로 분류한다. 리팩터링 PR이면 대부분 거짓 양성이다.
  2. 단언을 관찰 가능한 결과(반환값·저장 상태)로 옮긴다. 같은 프로세스의 도메인 객체는 mock 대신 진짜를 쓴다.
  3. `verify`는 꼭 필요한 호출에만 남긴다. SWE@G 13장 기준은 상태를 바꾸는 함수("Prefer to perform interaction testing only for state-changing functions"), Khorikov 기준은 관리하지 않는 프로세스 밖 의존으로 나가는 명령(메일·외부 API 호출)이다. 값만 돌려주는 조회 호출의 `verify`는 둘 다 뺀다.
  4. 다음 리팩터링 PR에서 테스트 파일 변경 수를 다시 세어 효과를 확인한다.
