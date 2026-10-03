# testing/04-classical-vs-london — 정답

## 정답

### 1. 격리를 어떻게 읽나

| | 고전파 | 런던파 |
|---|---|---|
| 격리 대상 | 테스트끼리 | 단위(SUT)를 협력 객체에서 |
| 단위 | 동작 단위(클래스 여럿 가능) | 클래스 하나 |
| 대역 | 공유 의존(DB·파일 시스템 등) | 변경 가능한 의존 전부 |

- Khorikov 2.1의 단위 테스트 속성 "does it in an isolated manner"를 고전파는 "테스트가 서로 영향을 주지 않는다"로, 런던파는 "SUT를 협력 객체에서 떼어 낸다"로 읽는다.

### 2. 정의와 이름

- 상태 검증: 실행 뒤 SUT·협력 객체의 상태를 본다. 행위 검증: SUT가 협력 객체를 올바르게 호출했는지 본다(Fowler).
- 고전파: "use real objects if possible and a double if it's awkward to use the real thing."
- mockist: "will always use a mock for any object with interesting behavior."
- 이름: XP가 Detroit의 C3 프로젝트에서 시작돼 고전파 = Detroit, mockist 스타일이 London의 초기 XP 실천가에게서 나와 London.

### 3. 무엇이 진짜인가

```text
  고전파 OrderServiceTest                 런던파 OrderServiceLondonTest
  OrderService (진짜)                     OrderService (진짜)
    ├─ PriceCalculator (진짜)               ├─ PriceCalculator (mock: total → 90,000 stub)
    │    └─ DiscountPolicy (진짜)           ├─ OrderRepository (mock: save verify)
    ├─ OrderRepository (인메모리 Fake)      └─ Notifier (mock: orderPlaced verify)
    └─ Notifier (기록용 대역)
  확인: Fake에 저장된 총액, 보낸 알림       확인: save·orderPlaced 호출 인자
```

### 4. 경계 결함 B1

(실험, JDK 21.0.12 · JUnit Platform 1.13.4 · Mockito 5.18.0, 2026-10-03)

```text
B1 L 전체=6 통과=5 실패=1 | DiscountPolicyTest:소계_100000부터_10퍼센트()
B1 C 전체=6 통과=2 실패=4 | OrderServiceTest:주문이_할인된_총액으로_저장된다() OrderServiceTest:고객에게_총액이_통지된다() PriceCalculatorTest:경계에서_할인이_적용된다() DiscountPolicyTest:소계_100000부터_10퍼센트()
```

- 런던파 1개, 고전파 4개. 런던파는 결함 클래스의 테스트 하나만 빨개져 원인을 바로 가리킨다.
- 고전파도 4개가 공통으로 실행하는 `DiscountPolicy`를 따라가면 같은 곳에 닿는다. 가장 작은 범위의 실패(`DiscountPolicyTest`)부터 보면 된다.

### 5. `apply` 위임 뒤 런던파 실패

```text
할인율을_적용한다() ✘   expected: 90000L  but was: 0L
수량을_곱한다() ✘       expected: 60000L  but was: 0L
```

- 0은 stub하지 않은 `apply`가 돌려준 값이다. Mockito 5.18의 기본 응답 `ReturnsEmptyValues`는 원시 타입 반환 메서드에 기본 원시값(long이면 0)을 준다.
- 동작은 그대로인 리팩터링이므로 거짓 양성이다. 고전파 묶음은 6개 모두 초록이었다.

### 6. 단위 불일치 B4

```text
B4 L 통과=6 실패=0 |
B4 C 통과=3 실패=3 | OrderServiceTest:… ×2  PriceCalculatorTest:경계에서_할인이_적용된다()   (expected: 90000L but was: 0L)
```

- 런던파는 전부 초록이다. 계산기 테스트의 stub이 "정책은 10을 준다"는 옛 약속을 기억하고 있어서다.
- 고전파는 10만 원 주문이 0원이 되는 것을 잡았다.
- 약점: 클래스 사이 계약이 stub 반환값으로 테스트에 새겨져, 실제 클래스가 약속을 바꿔도 모른다. 런던파는 이 틈을 인수 테스트(바깥 루프)로 메운다.

### 7. 논쟁의 축과 저자 입장

| 축 | 런던파 | 고전파 |
|---|---|---|
| TDD 진행 | 바깥부터 안으로(outside-in, need-driven) | 도메인부터(middle-out) |
| 픽스처 | 협력 객체를 만들 필요가 적다 | 진짜 객체 그래프 필요(Object Mother 등) |
| 실패 격리 | 결함 클래스 테스트만 빨강 | 파급. 대신 자주 돌리면 방금 고친 곳이 원인 |
| 구현 결합 | 협력 객체 호출 방식이 바뀌면 깨진다 | 최종 상태만 보므로 리팩터링에 강하다 |

- Fowler: 스스로 "old fashioned classic TDDer".
- SWE@G 13장: mockist는 Google에서 "difficult to scale", "Prefer Realism Over Isolation".
- Khorikov: 고전파. mock은 관리하지 않는 프로세스 밖 의존에만.

### 8. mock을 쓰는 곳

- 쓴다: 프로세스 밖으로 나가는 **명령**(메일·결제 요청·메시지 발행) — 외부가 관찰하는 결과라서 호출 자체가 검증 대상이다. 아직 없는 협력 객체의 인터페이스를 바깥에서 설계할 때(outside-in).
- 쓰지 않는다: 같은 프로세스의 도메인 객체, 값을 돌려주는 조회 호출의 `verify`, 남이 만든 라이브러리 타입(원칙으로서. 실제 라이브러리로 일으키기 어려운 동작을 흉내 낼 때 같은 예외를 GOOS가 두는지는 본문을 확인하지 못했다 [?]).
- 조회는 stub, 명령만 verify: 조회의 결과는 SUT의 반환값·상태에 이미 반영되므로 다시 확인할 필요가 없다. 확인하면 구현 경로에 묶인다.
- 자기가 소유한 타입만 mock(GOOS 8장 "Building on Third-Party Code"): 외부 타입의 동작을 추측해 stub에 적으면 실제와 어긋난다. 어댑터로 감싸고 어댑터를 mock하거나, 어댑터는 실제 의존으로 테스트한다.

### 9. 고전파의 파급 대처

- 실패한 테스트들이 공통으로 실행하는 클래스를 찾는다(의존 그래프의 역방향 도달성). 그 클래스 자체의 테스트 실패부터 본다.
- 테스트를 자주 돌리면 직전 변경이 원인 후보다. 그래도 어렵다면 `git bisect`로 좁힌다.
- mock을 늘리면: 리팩터링 내성(내부 호출 방식에 묶임)과 클래스 사이 계약 불일치 검출(B4 같은 결함)을 잃는다.
