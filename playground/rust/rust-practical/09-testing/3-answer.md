# rust/rust-practical/09 — 테스트 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `"-1.50 USD"` 와 `"0.50 USD"` — 두 번째 줄은 음수 부호를 잃는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
-1.50 USD
0.50 USD
```

`"usd"` 는 `new` 에서 `"USD"` 로 바뀐다.
`-150` 은 `-150 / 100 = -1`, `-150 % 100 = -50`, `.abs()` 로 `50` → `"-1.50 USD"` 다.
`-50` 은 `-50 / 100 = 0`, `-50 % 100 = -50`, `.abs()` 로 `50` → `"0.50 USD"` 다.
두 번째 줄은 -0.50 달러를 +0.50 달러처럼 보여 준다.

**왜 그런가**

정수 나눗셈은 0 쪽으로 버리므로 정수부가 0 인 음수는 정수부에 부호가 남지 않는다.
소수부는 `.abs()` 로 부호를 지우므로 부호가 어디에도 남지 않는다.
근거: 2-summary 「어디서 틀리나 7」, 「동작 방식 (3)」.

### 2. `1` — 검증에 걸린 결제는 게이트웨이까지 가지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

첫 호출은 금액 0 이라 「양수」 검사에서 `Err` 로 돌아가고, `charge` 는 불리지 않는다.
둘째 호출은 5000 USD, 카드 `"card"` 로 두 검사를 통과해 `charge` 가 불리고 `(5000, "card")` 가 기록된다.
셋째 호출은 카드가 빈 문자열이라 `"카드 정보 필요"` 로 돌아가고, `charge` 는 불리지 않는다.
기록은 하나뿐이라 `1` 이 찍힌다.

**왜 그런가**

`process_payment` 는 검증을 모두 통과한 뒤에만 `gateway.charge` 를 부른다.
Mock 의 기록은 `charge` 안에서만 쌓인다.
근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (5)」.

### 3. 「총 결과: 11 성공, 0 실패」 — 열한 검사가 모두 통과한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
총 결과: 11 성공, 0 실패
```

`Money` 검사 7개와 `PaymentService` 검사 5개, 모두 11개다.
하나씩 읽으면 전부 통과한다 — `"KRW"` 그대로, `"K"` 는 「3자리」 에러, `"usd"` → `"USD"`, 1000 + 2000 = 3000, USD + EUR 은 `Err`, 999 × 3 = 2997, 1050 → `"10.50 USD"`, 성공 Mock 은 `"tx_mock_123"`, 0원은 「양수」 에러, 빈 카드는 `Err`, 실패 Mock 은 「카드 거절」, 결제 한 번이면 기록 1개.

**왜 그런가**

어느 `assert` 도 어긋나지 않아 패닉이 없고, `catch_unwind` 는 매번 `Ok` 를 돌려 `passed` 만 오른다.
근거: 2-summary 「동작 방식 (2)」의 판정 규칙과 (3) · (5)의 테스트 표.

### 4. 부동소수점 오차를 피해 정확한 정수 계산을 하려고

`f64` 는 십진 소수를 정확히 담지 못해, 더하고 곱할 때 작은 오차가 쌓인다.
돈은 한 푼도 어긋나면 안 되므로 센트 단위 정수로 두어 덧셈 · 곱셈을 정확하게 한다.
`1050` 이 10달러 50센트이고, 표시할 때만 `/ 100` 과 `% 100` 으로 나눈다.
근거: 2-summary 「동작 방식 (3)」.

### 5. 트레이트가 `charge` 를 `&self` 로 정해 두어서

`PaymentGateway::charge` 는 `&self`(공유 참조)를 받는다.
공유 참조로는 평범한 `Vec` 필드에 `push` 할 수 없다.
`RefCell` 은 빌림 검사를 실행 중으로 미뤄, `&self` 에서도 `borrow_mut()` 으로 안쪽 `Vec` 을 바꾸게 해 준다(내부 가변성).
그래서 트레이트의 꼴을 바꾸지 않고도 Mock 이 호출을 기록할 수 있다.
근거: 2-summary 「동작 방식 (5)」, 「어디서 틀리나 6」.

### 6. 첫 실패에서 프로그램 전체가 멈춘다

`assert` 가 어긋나면 패닉한다.
`catch_unwind` 가 없으면 그 패닉이 `run_tests` 와 `main` 까지 번져 프로그램이 끝난다.
뒤의 테스트는 돌지 못하고, `✗` 줄도 「총 결과」 줄도 찍히지 않는다.
`catch_unwind` 는 패닉을 `Err` 로 바꿔 `failed` 를 올리고 다음 테스트로 넘어가게 한다 — 테스트를 하나씩 돌려 성적을 모으는 `cargo test` 의 동작을 흉내 낸 것이다.
근거: 2-summary 「동작 방식 (2)」.

### 7. `Ok` 를 돌려준다 — 길이 검사가 바이트를 세기 때문

`currency.len()` 은 글자 수가 아니라 UTF-8 바이트 수다.
한글 「원」 한 음절은 3바이트라서 `len() != 3` 검사를 통과한다.
`to_uppercase()` 는 한글을 바꾸지 않으므로 통화가 `"원"` 인 `Money` 가 만들어진다.
「영문 세 글자 통화 코드」라는 의도는 이 검사로 지켜지지 않는다.
근거: 2-summary 「어디서 틀리나 8」.

### 8. 통째 비교는 컴파일되지 않고, `amount` 비교는 그대로 된다

`assert_eq!` 는 비교할 타입에 `PartialEq` 와 `Debug` 를 둘 다 요구한다 — 실패할 때 두 값을 찍어야 하기 때문이다.
`Debug` 가 빠진 `Money` 를 넣으면 이 요구를 채우지 못해 컴파일 에러가 난다.
`money.amount` 는 `i64` 라 두 트레이트를 이미 갖고 있으므로 영향이 없다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 3」.

### 9. 트레이트로 의존성을 추상화하고 제네릭 서비스에 주입하는 짜임

`PaymentService<G: PaymentGateway>` 는 구체 타입이 아니라 「`PaymentGateway` 를 구현한 아무 타입」을 받는다.
`StripeGateway` 와 `MockGateway` 는 둘 다 그 트레이트를 구현한다.
게이트웨이는 바깥에서 만들어 `new` 로 넣으므로(의존성 주입), 서비스 코드를 고치지 않고 진짜와 가짜를 바꿔 꽂는다.
서비스가 구체 구현이 아니라 추상에 기대므로 원본 주석은 이를 「의존성 역전」이라 부른다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 5」.

### 10. `#[cfg(test)] mod tests` 안의 `#[test]` 함수들로, 통합 흐름은 `tests/` 로

각 `test!("이름", { … })` 블록은 `#[test]` 를 붙인 함수 하나가 된다.
그 함수들은 대상 코드와 같은 파일의 `#[cfg(test)] mod tests` 안에 두어, 일반 빌드에 섞이지 않게 한다.
패닉을 잡고 개수를 세는 일은 `cargo test` 가 맡으므로 `test!` 매크로와 `passed` · `failed` 계수는 필요 없어진다.
crate 를 바깥에서 쓰는 흐름의 시험은 `tests/` 디렉토리에 통합 테스트로 둔다.
테스트 안 `println!` 을 보려면 `cargo test -- --nocapture` 로 돌린다.
근거: 2-summary 「동작 방식 (6)」, 「문법 — 형태와 규칙」, 「어디서 틀리나 10」.

## 실습 정답

### 실습 1. 결제 서비스와 Mock 게이트웨이, 그리고 직접 만든 테스트 실행기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `Money` 필드와 파생 | `#[derive(Debug, Clone, PartialEq)] struct Money { amount, currency }` |
| 2. 검증하는 생성자 | `Money::new` — `currency.len() != 3`, `currency.to_uppercase()` |
| 3. 통화 일치 덧셈 | `Money::add` — `self.currency != other.currency`, `format!("통화 불일치: …")` |
| 4. 정수배 곱셈 | `Money::multiply` — `self.amount * factor` |
| 5. 표시 형식 | `Money::display` — `amount / 100`, `(amount % 100).abs()`, `"{}.{:02} {}"` |
| 6. 게이트웨이 트레이트 | `trait PaymentGateway { fn charge …; fn refund …; }` |
| 7. 진짜 구현 | `impl PaymentGateway for StripeGateway` — `format!("ch_{}", card.len())`, `Ok(true)` |
| 8. Mock 의 필드 | `struct MockGateway { charge_result, refund_result, charge_calls: RefCell<Vec<(i64, String)>> }` |
| 9. 성공 · 실패 Mock | `MockGateway::succeeding`, `MockGateway::failing` |
| 10. 호출 횟수 | `charge_call_count` — `self.charge_calls.borrow().len()` |
| 11. 기록 후 결과 복사 | `impl PaymentGateway for MockGateway` — `borrow_mut().push(..)`, `charge_result.clone()`, `refund_result.clone()` |
| 12. 제네릭 서비스와 주입 | `struct PaymentService<G: PaymentGateway>`, `PaymentService::new` |
| 13. 검증 후 위임 | `process_payment` — `amount.amount <= 0`, `card.is_empty()`, `self.gateway.charge(..)` |
| 14. 패닉을 잡는 실행기 | `run_tests` 의 `macro_rules! test` — `catch_unwind(AssertUnwindSafe(|| $body))`, `passed += 1` / `failed += 1` |
| 15. `Money` 검사 7개 | `test!("유효한 Money 생성", …)` ~ `test!("표시 형식", …)` |
| 16. 서비스 검사 5개 | `test!("결제 성공", …)` ~ `test!("Mock 호출 횟수 검증", …)` |
| 17. 총 결과와 가이드 | `println!("\n총 결과: …")`, `main` 의 가이드 `println!` 들 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-practical/reference/testing.rs`

```rust
// [실전 Rust] 테스트
// 설명: #[test] 속성, assert 매크로, 단위/통합 테스트, mock 패턴, 테스트 구조화
// 팁: 단위 테스트는 같은 파일의 #[cfg(test)] mod tests 안에 작성한다. 통합 테스트는 tests/ 디렉토리에 둔다. 트레이트로 의존성을 추상화하면 Mock을 주입할 수 있다. assert_eq!는 PartialEq + Debug가 필요하다. cargo test -- --nocapture로 println! 출력을 볼 수 있다.

// === Rust 테스트 패턴 ===

// ===== 1. 테스트 대상 코드 =====

// 금액 - 부동소수점 오차 회피 위해 정수(센트 단위)로 저장
#[derive(Debug, Clone, PartialEq)]
struct Money {
    amount: i64,     // 센트 단위 저장 (부동소수점 회피)
    currency: String,
}

impl Money {
    // 스마트 생성자 - 통화 코드 검증 (ISO 4217은 3자리)
    fn new(amount: i64, currency: &str) -> Result<Self, String> {
        if currency.len() != 3 {
            return Err("통화 코드는 3자리여야 합니다".to_string());
        }
        Ok(Money {
            amount,
            // 대문자 정규화 (USD/usd 일치)
            currency: currency.to_uppercase(),
        })
    }

    // 덧셈 - 통화 일치 검사
    fn add(&self, other: &Money) -> Result<Money, String> {
        if self.currency != other.currency {
            return Err(format!("통화 불일치: {} != {}", self.currency, other.currency));
        }
        Ok(Money {
            amount: self.amount + other.amount,
            currency: self.currency.clone(),
        })
    }

    // 정수배 곱셈
    fn multiply(&self, factor: i64) -> Money {
        Money {
            amount: self.amount * factor,
            currency: self.currency.clone(),
        }
    }

    // 표시 형식: 정수.소수 형태
    fn display(&self) -> String {
        let whole = self.amount / 100;
        // 소수점 두 자리는 항상 양수로
        let cents = (self.amount % 100).abs();
        format!("{}.{:02} {}", whole, cents, self.currency)
    }
}

// ===== 2. 트레이트 기반 Mock 패턴 =====

// 결제 게이트웨이 추상화 - 실제 구현과 Mock을 모두 만족하는 트레이트
trait PaymentGateway {
    // 결제 처리 - 트랜잭션 ID 반환
    fn charge(&self, amount: &Money, card: &str) -> Result<String, String>;
    // 환불 - 성공 여부 반환
    fn refund(&self, transaction_id: &str) -> Result<bool, String>;
}

// 실제 구현 - 운영 환경에서 사용
struct StripeGateway;

impl PaymentGateway for StripeGateway {
    fn charge(&self, amount: &Money, card: &str) -> Result<String, String> {
        // 실제로는 Stripe API 호출
        Ok(format!("ch_{}", card.len()))
    }
    fn refund(&self, transaction_id: &str) -> Result<bool, String> {
        Ok(true)
    }
}

// Mock 구현 - 테스트용 - 결과를 미리 설정 + 호출 기록
struct MockGateway {
    // 미리 설정된 charge 결과
    charge_result: Result<String, String>,
    // 미리 설정된 refund 결과
    refund_result: Result<bool, String>,
    // 호출 기록 - RefCell로 &self에서도 변경 가능
    charge_calls: std::cell::RefCell<Vec<(i64, String)>>,
}

impl MockGateway {
    // 항상 성공하는 mock
    fn succeeding() -> Self {
        MockGateway {
            charge_result: Ok("tx_mock_123".to_string()),
            refund_result: Ok(true),
            charge_calls: std::cell::RefCell::new(Vec::new()),
        }
    }

    // 항상 실패하는 mock - 에러 메시지 지정
    fn failing(error: &str) -> Self {
        MockGateway {
            charge_result: Err(error.to_string()),
            refund_result: Err(error.to_string()),
            charge_calls: std::cell::RefCell::new(Vec::new()),
        }
    }

    // 호출 검증 - 호출 횟수 확인
    fn charge_call_count(&self) -> usize {
        self.charge_calls.borrow().len()
    }
}

impl PaymentGateway for MockGateway {
    fn charge(&self, amount: &Money, card: &str) -> Result<String, String> {
        // 호출 시 기록 후 미리 설정된 결과 반환
        self.charge_calls.borrow_mut().push((amount.amount, card.to_string()));
        self.charge_result.clone()
    }
    fn refund(&self, _transaction_id: &str) -> Result<bool, String> {
        self.refund_result.clone()
    }
}

// PaymentGateway를 사용하는 서비스 - 의존성 역전
struct PaymentService<G: PaymentGateway> {
    gateway: G,
}

impl<G: PaymentGateway> PaymentService<G> {
    // 게이트웨이 주입
    fn new(gateway: G) -> Self {
        PaymentService { gateway }
    }

    // 결제 처리 - 입력 검증 후 게이트웨이 호출
    fn process_payment(&self, amount: &Money, card: &str) -> Result<String, String> {
        // 0 이하 금액 거부
        if amount.amount <= 0 {
            return Err("금액은 양수여야 합니다".to_string());
        }
        // 카드 정보 필수
        if card.is_empty() {
            return Err("카드 정보 필요".to_string());
        }
        self.gateway.charge(amount, card)
    }
}

// ===== 3. 테스트 모듈 =====

// 실제로는 #[cfg(test)] mod tests { ... } 안에 위치
// 여기서는 main에서 직접 호출하기 위해 일반 함수로 작성

fn run_tests() {
    let mut passed = 0;
    let mut failed = 0;

    // 테스트 매크로 - 각 케이스를 패닉 캐치 후 카운트 - cargo test의 동작 모방
    macro_rules! test {
        ($name:expr, $body:block) => {{
            // catch_unwind로 패닉을 잡아 다음 테스트로 진행
            match std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| $body)) {
                Ok(_) => {
                    println!("  ✓ {}", $name);
                    passed += 1;
                }
                Err(_) => {
                    println!("  ✗ {}", $name);
                    failed += 1;
                }
            }
        }};
    }

    println!("=== Money 테스트 ===");

    // 정상 생성
    test!("유효한 Money 생성", {
        let money = Money::new(1000, "KRW").unwrap();
        assert_eq!(money.amount, 1000);
        assert_eq!(money.currency, "KRW");
    });

    // 통화 검증 실패
    test!("잘못된 통화 코드", {
        let result = Money::new(1000, "K");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("3자리"));
    });

    // 대문자 변환 검증
    test!("소문자 통화 코드 대문자 변환", {
        let money = Money::new(1000, "usd").unwrap();
        assert_eq!(money.currency, "USD");
    });

    // 덧셈 정상 동작
    test!("같은 통화 덧셈", {
        let a = Money::new(1000, "USD").unwrap();
        let b = Money::new(2000, "USD").unwrap();
        let sum = a.add(&b).unwrap();
        assert_eq!(sum.amount, 3000);
        assert_eq!(sum.currency, "USD");
    });

    // 통화 불일치 시 실패
    test!("다른 통화 덧셈 실패", {
        let usd = Money::new(1000, "USD").unwrap();
        let eur = Money::new(2000, "EUR").unwrap();
        assert!(usd.add(&eur).is_err());
    });

    // 곱셈
    test!("곱셈", {
        let price = Money::new(999, "USD").unwrap();
        let total = price.multiply(3);
        assert_eq!(total.amount, 2997);
    });

    // 표시 형식
    test!("표시 형식", {
        let money = Money::new(1050, "USD").unwrap();
        assert_eq!(money.display(), "10.50 USD");
    });

    println!("\n=== PaymentService 테스트 (Mock) ===");

    // 정상 결제 흐름
    test!("결제 성공", {
        let gateway = MockGateway::succeeding();
        let service = PaymentService::new(gateway);
        let amount = Money::new(5000, "USD").unwrap();
        let result = service.process_payment(&amount, "4111111111111111");
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), "tx_mock_123");
    });

    // 입력 검증 - 0원
    test!("결제 금액 0 이하 거부", {
        let gateway = MockGateway::succeeding();
        let service = PaymentService::new(gateway);
        let amount = Money::new(0, "USD").unwrap();
        let result = service.process_payment(&amount, "card");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("양수"));
    });

    // 입력 검증 - 카드 누락
    test!("카드 정보 없으면 거부", {
        let gateway = MockGateway::succeeding();
        let service = PaymentService::new(gateway);
        let amount = Money::new(5000, "USD").unwrap();
        let result = service.process_payment(&amount, "");
        assert!(result.is_err());
    });

    // 게이트웨이 에러 전파
    test!("게이트웨이 실패 전파", {
        let gateway = MockGateway::failing("카드 거절");
        let service = PaymentService::new(gateway);
        let amount = Money::new(5000, "USD").unwrap();
        let result = service.process_payment(&amount, "card");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("카드 거절"));
    });

    // Mock 호출 횟수 검증 - mockall의 .times()와 유사
    test!("Mock 호출 횟수 검증", {
        let gateway = MockGateway::succeeding();
        let service = PaymentService::new(gateway);
        let amount = Money::new(5000, "USD").unwrap();
        service.process_payment(&amount, "card1").unwrap();
        assert_eq!(service.gateway.charge_call_count(), 1);
    });

    println!("\n총 결과: {} 성공, {} 실패", passed, failed);
}

fn main() {
    run_tests();

    // 표준 테스트 도구 정리
    println!("\n=== 테스트 구조 가이드 ===");
    println!("#[cfg(test)]           -> 테스트 코드 조건부 컴파일");
    println!("#[test]                -> 테스트 함수 표시");
    println!("#[should_panic]        -> 패닉 예상 테스트");
    println!("#[ignore]              -> 기본 제외, --ignored로 실행");
    println!("assert!(expr)          -> 참 검증");
    println!("assert_eq!(a, b)       -> 동등 검증");
    println!("assert_ne!(a, b)       -> 부등 검증");
    println!("tests/ 디렉토리         -> 통합 테스트");
    println!("트레이트 + Mock 구조체  -> 의존성 모킹");
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**

- 판정은 오직 패닉 여부다 — `assert` 가 어긋나면 패닉하고, `catch_unwind` 가 그것을 `Err` 로 받아 `✗` 로 센다.
- `Money::new` 가 검증과 대문자 정규화를 맡아, 이후 코드는 「통화는 대문자 세 칸」이라고 믿고 비교할 수 있다(단 길이는 바이트 기준이다).
- `PaymentService` 는 `G: PaymentGateway` 에만 기대므로 테스트에서 `MockGateway` 를 꽂아 결제 API 없이 모든 갈래(성공 · 0원 · 빈 카드 · 게이트웨이 실패)를 시험한다.
- Mock 은 `charge_result.clone()` 으로 정해 둔 답을 내놓고, `RefCell` 로 `&self` 에서도 호출을 기록해 「몇 번 불렸나」까지 확인하게 한다.
- 실제 프로젝트에서는 각 `test!` 블록을 `#[cfg(test)] mod tests` 안의 `#[test]` 함수로 옮기고, 세는 일은 `cargo test` 에 맡긴다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
