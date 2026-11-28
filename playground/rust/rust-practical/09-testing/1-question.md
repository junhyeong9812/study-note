# rust/rust-practical/09 — 테스트 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 음수 금액을 `display()` 하면 (예측)

```rust
// 질문용 발췌
let a = Money::new(-150, "usd").unwrap();
let b = Money::new(-50, "USD").unwrap();
println!("{}", a.display());
println!("{}", b.display());
```

- 두 줄에 각각 어떤 문자열이 찍히나?
- 둘 중 금액의 뜻을 제대로 담지 못하는 줄은 어느 것인가?

### 2. 검증에 걸린 결제와 Mock 의 호출 기록 (예측)

```rust
// 질문용 발췌
let service = PaymentService::new(MockGateway::succeeding());
let zero = Money::new(0, "USD").unwrap();
let five = Money::new(5000, "USD").unwrap();
let _ = service.process_payment(&zero, "card");
let _ = service.process_payment(&five, "card");
let _ = service.process_payment(&five, "");
println!("{}", service.gateway.charge_call_count());
```

- 마지막 줄이 찍는 수는 무엇인가?

### 3. `run_tests` 의 마지막 줄 (예측)

- 예제의 `run_tests` 를 끝까지 돌리면 「총 결과」 줄에 어떤 두 수가 찍히나?

### 4. 금액을 `i64` 센트로 저장하는 까닭 (왜)

- `Money` 가 금액을 `f64` 달러가 아니라 `i64` 센트로 저장하는 까닭은 무엇인가?

### 5. Mock 이 호출 기록을 `RefCell` 에 담는 까닭 (왜)

- `MockGateway` 가 `charge_calls` 를 그냥 `Vec` 이 아니라 `RefCell<Vec<…>>` 로 두는 까닭은 무엇인가?

### 6. `test!` 매크로가 `catch_unwind` 를 쓰는 까닭 (왜)

- `test!` 매크로가 테스트 본문을 `catch_unwind` 로 감싸지 않으면 무엇이 달라지나?

### 7. 통화 코드 검사는 어디까지 막나 (경계)

- `Money::new(100, "원")` 은 `Ok` 와 `Err` 중 무엇을 돌려주나?

### 8. `assert_eq!` 가 요구하는 것 (경계)

- `Money` 의 `derive` 에서 `Debug` 를 빼면, `Money` 두 값을 통째로 `assert_eq!` 하는 테스트와 `money.amount` 만 비교하는 테스트는 각각 어떻게 되나?

### 9. 같은 서비스에 진짜와 가짜를 꽂는 구조 (연결)

- 운영에서는 `StripeGateway`, 테스트에서는 `MockGateway` 를 `PaymentService` 에 넣을 수 있게 해 주는 짜임은 무엇인가?

### 10. `run_tests` 를 `cargo test` 체계로 옮기면 (연결)

- 예제의 `test!` 블록들을 실제 `cargo test` 로 돌리는 테스트로 옮기면 코드의 꼴과 파일 배치는 어떻게 바뀌나?

## 실습

### 실습 1. 결제 서비스와 Mock 게이트웨이, 그리고 직접 만든 테스트 실행기

**만들 것** — 정수 센트로 금액을 다루는 `Money`, 결제 게이트웨이 트레이트와 그 진짜 · 가짜 구현, 게이트웨이를 주입받는 결제 서비스를 짓는다.
그리고 패닉을 잡아 성공 · 실패를 세는 작은 테스트 실행기로 12개 검사를 돌린다.

**요구 조건**

1단계 — `Money`

1. `Money` 구조체는 `amount: i64`(센트 단위)와 `currency: String` 을 갖고, `Debug` · `Clone` · `PartialEq` 를 파생한다.
2. `Money::new(amount, currency)` 는 `Result<Self, String>` 을 돌려준다 — 통화 코드 길이가 3이 아니면 「3자리」가 든 에러, 아니면 통화를 대문자로 바꾼 `Money` 를 돌려준다.
3. `add(&self, other)` 는 통화가 다르면 `"통화 불일치: A != B"` 꼴의 에러를, 같으면 금액을 더한 새 `Money` 를 돌려준다.
4. `multiply(&self, factor)` 는 금액에 정수를 곱한 새 `Money` 를 돌려준다.
5. `display(&self)` 는 `정수부.두자리소수 통화` 꼴의 문자열을 돌려준다 — 소수부는 절댓값을 두 자리로 맞춘다.

2단계 — 게이트웨이

6. `PaymentGateway` 트레이트는 `charge(&self, &Money, &str) -> Result<String, String>` 과 `refund(&self, &str) -> Result<bool, String>` 을 정한다.
7. `StripeGateway` 는 `charge` 에서 `"ch_"` 뒤에 카드 문자열 길이를 붙인 `Ok` 를, `refund` 에서 `Ok(true)` 를 돌려준다.
8. `MockGateway` 는 미리 정한 `charge` 결과 · `refund` 결과와, `(금액, 카드)` 짝을 쌓는 `RefCell` 호출 기록을 갖는다.
9. `MockGateway::succeeding()` 은 `charge` 가 `Ok("tx_mock_123")`, `refund` 가 `Ok(true)` 인 Mock 을, `failing(error)` 는 둘 다 그 에러를 돌려주는 Mock 을 만든다.
10. `charge_call_count()` 는 쌓인 호출 기록의 개수를 돌려준다.
11. `MockGateway` 의 `charge` 는 호출을 기록한 뒤 미리 정한 결과의 복사본을, `refund` 는 미리 정한 결과의 복사본을 돌려준다.

3단계 — 서비스

12. `PaymentService<G: PaymentGateway>` 는 게이트웨이를 필드로 갖고 `new(gateway)` 로 주입받는다.
13. `process_payment` 는 금액이 0 이하면 「양수」가 든 에러, 카드가 빈 문자열이면 `"카드 정보 필요"` 에러를 돌려주고, 둘 다 통과하면 게이트웨이의 `charge` 결과를 그대로 돌려준다.

4단계 — 테스트 실행기

14. `run_tests` 는 성공 · 실패 개수를 세고, `test!(이름, { 본문 })` 매크로로 본문을 패닉을 잡으며 돌려 성공이면 `✓ 이름`, 실패면 `✗ 이름` 을 찍는다.
15. `Money` 검사 7개를 돌린다 — 유효한 생성, 잘못된 통화 코드, 소문자 대문자 변환, 같은 통화 덧셈, 다른 통화 덧셈 실패, 곱셈(999 × 3), 표시 형식(1050).
16. `PaymentService` 검사 5개를 Mock 으로 돌린다 — 결제 성공, 금액 0 거부, 빈 카드 거부, 게이트웨이 실패 전파, Mock 호출 횟수 1.
17. 끝에 `총 결과: N 성공, M 실패` 를 찍고, `main` 은 `run_tests` 뒤에 테스트 구조 가이드를 찍는다.

**시작 코드**

```rust
// === Rust 테스트 패턴 ===

// ===== 1. 테스트 대상 코드 =====

// TODO: derive 세 가지
struct Money {
    // TODO: 센트 단위 금액, 통화 코드
}

impl Money {
    fn new(amount: i64, currency: &str) -> Result<Self, String> {
        // TODO: 길이 검사 → 에러 "통화 코드는 3자리여야 합니다"
        // TODO: 대문자 정규화해 Ok
        todo!()
    }

    fn add(&self, other: &Money) -> Result<Money, String> {
        // TODO: 통화 불일치 검사, 합 돌려주기
        todo!()
    }

    fn multiply(&self, factor: i64) -> Money {
        // TODO
        todo!()
    }

    fn display(&self) -> String {
        // TODO: 정수부, 소수부(절댓값), "{}.{:02} {}"
        todo!()
    }
}

// ===== 2. 트레이트 기반 Mock 패턴 =====

trait PaymentGateway {
    // TODO: charge, refund
}

struct StripeGateway;

// TODO: impl PaymentGateway for StripeGateway

struct MockGateway {
    // TODO: charge_result, refund_result, charge_calls (RefCell)
}

impl MockGateway {
    fn succeeding() -> Self { todo!() }
    fn failing(error: &str) -> Self { todo!() }
    fn charge_call_count(&self) -> usize { todo!() }
}

// TODO: impl PaymentGateway for MockGateway (기록 후 결과 복사본)

// TODO: struct PaymentService<G: PaymentGateway>

// TODO: impl — new, process_payment
//   금액 0 이하 → "금액은 양수여야 합니다"
//   빈 카드     → "카드 정보 필요"

// ===== 3. 테스트 모듈 =====

fn run_tests() {
    let mut passed = 0;
    let mut failed = 0;

    macro_rules! test {
        ($name:expr, $body:block) => {{
            // TODO: catch_unwind + AssertUnwindSafe 로 본문을 돌려
            //       "  ✓ {}" / "  ✗ {}" 를 찍고 passed / failed 를 올린다
        }};
    }

    println!("=== Money 테스트 ===");
    // TODO: test!("유효한 Money 생성", { ... });
    // TODO: test!("잘못된 통화 코드", { ... });
    // TODO: test!("소문자 통화 코드 대문자 변환", { ... });
    // TODO: test!("같은 통화 덧셈", { ... });
    // TODO: test!("다른 통화 덧셈 실패", { ... });
    // TODO: test!("곱셈", { ... });
    // TODO: test!("표시 형식", { ... });

    println!("\n=== PaymentService 테스트 (Mock) ===");
    // TODO: test!("결제 성공", { ... });
    // TODO: test!("결제 금액 0 이하 거부", { ... });
    // TODO: test!("카드 정보 없으면 거부", { ... });
    // TODO: test!("게이트웨이 실패 전파", { ... });
    // TODO: test!("Mock 호출 횟수 검증", { ... });

    println!("\n총 결과: {} 성공, {} 실패", passed, failed);
}

fn main() {
    run_tests();

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

**확인 방법** — `rustc testing.rs && ./testing` 으로 돌려, 12개 검사가 모두 `✓` 로 찍히고 「총 결과」 줄의 실패 수가 0 인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
