# rust/rust-project-structures/10 — 테스트 패턴 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 이름 필터를 준 `cargo test` (예측)

```text
// 질문용 발췌 — tests 모듈 안 테스트 이름
test_money_add_same_currency
test_money_add_different_currency
test_money_multiply
test_money_multiply_zero
test_add_panics_on_different_currency
test_calculate_total
test_calculate_total_unknown_item
test_add_is_commutative
test_multiply_by_one_is_identity
```

- `cargo test test_money_add` 를 돌리면 위 목록에서 어느 테스트가 실행되는가?

### 2. `main` 의 덧셈 두 줄 (예측)

```rust
// 질문용 발췌
let a = Money::new(1000, "KRW");
let b = Money::new(2000, "KRW");
println!("add: {:?}", a.add(&b));
let c = Money::new(10, "USD");
println!("다른 통화: {:?}", a.add(&c));
```

- 두 `println!` 은 각각 어떤 줄을 찍는가?

### 3. `expected` 가 붙은 패닉 테스트의 판정 (예측)

```rust
// 질문용 발췌
#[test]
#[should_panic(expected = "통화 불일치")]
fn test_add_panics_on_different_currency() {
    let a = Money::new(100, "KRW");
    let b = Money::new(100, "USD");
    a.add(&b).unwrap();
}
```

- 이 테스트는 통과하는가, 실패하는가?
- 두 통화를 모두 `"KRW"` 로 바꾸면 판정은 어떻게 되는가?

### 4. 테스트 모듈을 `#[cfg(test)]` 로 감싸는 까닭 (왜)

- 테스트 모듈에 `#[cfg(test)]` 를 붙이면 배포 빌드에서 무엇이 달라지는가?
- 예제의 `main` 이 `MockPriceRepo` 를 쓰지 않고 `TestRepo` 를 따로 만든 까닭은 무엇인가?

### 5. `Money` 가 `Debug` · `PartialEq` · `Clone` 을 derive 한 까닭 (왜)

- 세 derive 는 이 예제에서 각각 어떤 호출 때문에 필요한가?

### 6. `PriceService` 를 제네릭 `R: PriceRepository` 로 만든 까닭 (왜)

- 이 구조가 없으면 `calculate_total` 을 테스트할 때 무엇이 곤란한가?

### 7. 통합 테스트가 닿는 범위 (경계)

- `tests/integration.rs` 에서 이 예제의 `Money::new` 를 부를 수 있는가?

### 8. 수동 프로퍼티 테스트가 잡지 못하는 것 (경계)

- `test_add_is_commutative` 와 `test_multiply_by_one_is_identity` 가 `proptest` 로 쓴 테스트보다 놓치는 것은 무엇인가?

### 9. 손으로 쓴 Mock 과 `#[automock]` (연결)

- `mockall` 의 `#[automock]` 은 예제의 어느 부분을 대신해 주며, 그래도 남는 설계 조건은 무엇인가?

## 실습

### 실습 1. 금액 계산 코드와 테스트 묶음 만들기

**만들 것** — 통화가 있는 금액 타입 `Money` 와 가격 저장소에 기대는 `PriceService` 를 만들고, 단위 · 패닉 · Mock · 수동 프로퍼티 테스트를 한 파일에 갖춘다. `main` 은 같은 호출을 `println!` 으로 보여 주는 시뮬레이션이다.

**준비물** — Rust 툴체인(`cargo`). 외부 크레이트는 쓰지 않는다 — 프로퍼티 테스트는 `proptest` 를 값 목록 반복으로 흉내 낸 것이고, `mockall` · `proptest` · `rstest` · `test-case` 는 `main` 에서 이름만 소개한다.

**요구 조건**

1단계 — 테스트 대상 코드
1. `Money` 는 `amount: i64`(센트 단위)와 `currency: String` 을 갖고 `Debug` · `PartialEq` · `Clone` 을 derive 한다.
2. `Money::new(amount, &str)` 가 값을 만든다.
3. `add(&self, &Money) -> Result<Money, String>` 은 통화가 다르면 `"통화 불일치: {} vs {}"` 꼴의 `Err` 를, 같으면 합을 `Ok` 로 돌려준다.
4. `multiply(&self, i64) -> Money` 는 정수배를, `is_positive(&self) -> bool` 은 금액이 0 보다 큰지를 돌려준다.
5. `PriceRepository` trait 에 `get_price(&self, &str) -> Option<Money>` 를 정의한다.
6. `PriceService<R: PriceRepository>` 는 `repo: R` 을 갖고 `new(repo)` 로 만든다.
7. `calculate_total(&self, &[(&str, i64)]) -> Result<Money, String>` 은 0 KRW 에서 시작해, 항목마다 가격을 찾아(없으면 `"가격 없음: {}"` 에러) 수량만큼 곱해 더한다.

2단계 — 단위 테스트 (`#[cfg(test)] mod tests`, `use super::*`)
8. 같은 통화 1000 + 2000 = 3000 KRW 를 `assert_eq!` 로 확인한다.
9. KRW + USD 덧셈이 에러인지 `assert!` 로 확인한다.
10. 500 × 3 = 1500, 500 × 0 = 0 을 각각 확인한다.
11. KRW + USD 를 `unwrap()` 하면 「통화 불일치」로 패닉해야 통과하는 테스트를 둔다.

3단계 — Mock 테스트
12. 테스트 모듈 안에 `HashMap` 을 가진 `MockPriceRepo` 를 두고 coffee 4500 KRW, bread 3000 KRW 로 초기화한다.
13. `MockPriceRepo` 가 `PriceRepository` 를 구현해 맵에서 복제본을 돌려준다.
14. coffee 2개 + bread 1개 = 12000 KRW 임을 확인한다.
15. 없는 항목 `"unknown"` 은 에러이고 메시지에 「가격 없음」이 들어 있음을 확인한다.

4단계 — 수동 프로퍼티 테스트
16. `a_val ∈ [0, 100, -50, i64::MAX / 2]`, `b_val ∈ [0, 200, -100, 1]` 모든 쌍에서 `a + b == b + a` 를 확인하고, 실패 메시지에 두 값을 넣는다.
17. `[0, 100, -50, 999999]` 각 값에서 `m.multiply(1) == m` 을 확인한다.

5단계 — `main` 시뮬레이션
18. 1000 KRW + 2000 KRW 와 1000 KRW + 10 USD 의 결과를 `{:?}` 로 찍는다.
19. `main` 안에 `"apple"` 만 1000 KRW 로 알려 주는 `TestRepo` 를 만들고, 사과 2개와 없는 상품 `"????"` 1개의 합계를 찍는다.
20. 테스트 실행 방법 · 테스트 구조 · 유용한 크레이트 안내 줄을 찍는다(시작 코드에 채워져 있다).

**시작 코드**

```rust
// === 테스트 대상 코드 ===
// TODO: Debug, PartialEq, Clone 을 derive 한다
struct Money {
    amount: i64,   // 센트 단위
    currency: String,
}

impl Money {
    fn new(amount: i64, currency: &str) -> Self {
        // TODO
    }

    fn add(&self, other: &Money) -> Result<Money, String> {
        // TODO: 통화가 다르면 Err("통화 불일치: … vs …")
    }

    fn multiply(&self, factor: i64) -> Money {
        // TODO
    }

    fn is_positive(&self) -> bool {
        // TODO
    }
}

// TODO: trait PriceRepository { get_price }

// TODO: struct PriceService<R: PriceRepository> { repo: R }

// TODO: impl PriceService — new, calculate_total(0 KRW 에서 시작, 가격 없으면 "가격 없음: …")

// === 테스트 모듈 ===
// TODO: 테스트 빌드에서만 컴파일되게 표시
mod tests {
    // TODO: 부모 모듈 항목 가져오기

    // --- 단위 테스트 ---
    // TODO: 같은 통화 덧셈 / 다른 통화 덧셈 / 곱셈 / 0배 곱셈

    // TODO: 「통화 불일치」로 패닉해야 통과하는 테스트

    // --- Mock 테스트 ---
    // TODO: struct MockPriceRepo { prices: HashMap<String, Money> }
    //       coffee 4500 KRW, bread 3000 KRW
    // TODO: impl PriceRepository for MockPriceRepo
    // TODO: 합계 12000 KRW 테스트 / 없는 항목 에러 테스트

    // --- 프로퍼티 기반 테스트 (수동) ---
    // TODO: 교환법칙 / 1배 항등법칙
}

// === main에서 테스트 결과 시뮬레이션 ===
fn main() {
    println!("=== Rust 테스트 패턴 ===");

    // TODO: 1000 KRW + 2000 KRW, 1000 KRW + 10 USD 를 "add: {:?}", "다른 통화: {:?}" 로 찍기

    println!("\n--- Mock 서비스 ---");
    // TODO: struct TestRepo; apple → 1000 KRW, 나머지 None
    // TODO: "사과 2개: {:?}", "없는 상품: {:?}" 찍기

    println!("\n=== 테스트 실행 방법 ===");
    println!("cargo test                    # 전체 테스트");
    println!("cargo test test_money_add     # 이름 매칭");
    println!("cargo test -- --nocapture     # println! 출력");
    println!("cargo test -- --test-threads=1 # 직렬 실행");

    println!("\n=== 테스트 구조 ===");
    println!("tests/          # 통합 테스트 디렉토리");
    println!("  integration.rs # 각 파일이 독립 바이너리");
    println!("src/");
    println!("  lib.rs        # #[cfg(test)] mod tests {{ }}");

    println!("\n=== 유용한 크레이트 ===");
    println!("mockall:    자동 Mock 생성 (#[automock])");
    println!("proptest:   프로퍼티 기반 테스트");
    println!("rstest:     매개변수화 테스트 (#[rstest])");
    println!("test-case:  테이블 기반 테스트");
}
```

**확인 방법** — `cargo new` 로 만든 프로젝트의 `src/main.rs` 에 넣고 `cargo test` 를 돌려 테스트 9개가 모두 `ok` 인지 본다. `cargo run` 으로 `main` 의 시뮬레이션 줄을 확인하고, `cargo test test_money_add` 로 이름 필터도 시험한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
